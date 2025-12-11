from pathlib import Path

import pandas as pd
from sqlalchemy import text
from joblib import dump
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from src.db.connection import get_engine
from src.config.settings import print_settings_summary


def load_daily_aggregates() -> pd.DataFrame:
    """
    Load daily aggregates from the database.

    Expected columns:
      - location_id
      - date
      - max_aqi
    """
    engine = get_engine()
    sql = text(
        """
        SELECT location_id, date, max_aqi
        FROM daily_aggregates
        ORDER BY location_id, date;
        """
    )

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, parse_dates=["date"])

    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create lag and rolling features for modeling.

    For each location_id, we create:
      - lag1: max_aqi(t-1)
      - lag2: max_aqi(t-2)
      - lag3: max_aqi(t-3)
      - roll3: rolling mean over last 3 days
      - roll7: rolling mean over last 7 days

    Target:
      - target = max_aqi(t+1)  (next day's max AQI)
    """
    if df.empty:
        return df

    df = df.sort_values(["location_id", "date"]).copy()

    # Group by location for time-based features
    grouped = df.groupby("location_id", group_keys=False)

    df["lag1"] = grouped["max_aqi"].shift(1)
    df["lag2"] = grouped["max_aqi"].shift(2)
    df["lag3"] = grouped["max_aqi"].shift(3)
    df["roll3"] = grouped["max_aqi"].rolling(3).mean().reset_index(level=0, drop=True)
    df["roll7"] = grouped["max_aqi"].rolling(7).mean().reset_index(level=0, drop=True)

    # Target: next day's max_aqi
    df["target"] = grouped["max_aqi"].shift(-1)

    # Drop rows where we don't have full feature history or target
    feature_cols = ["lag1", "lag2", "lag3", "roll3", "roll7", "target"]
    df = df.dropna(subset=feature_cols).reset_index(drop=True)

    return df


def train_random_forest(df_feat: pd.DataFrame, model_path: Path) -> None:
    """
    Train a RandomForestRegressor on the feature dataframe and save the model.

    Also prints simple evaluation metrics and baseline comparison.
    """
    if df_feat.empty:
        print("⚠️ No feature rows available for training. Collect more data first.")
        return

    feature_columns = ["lag1", "lag2", "lag3", "roll3", "roll7"]
    X = df_feat[feature_columns]
    y = df_feat["target"]

    n_rows = len(df_feat)
    print(f"Feature rows available for modeling: {n_rows}")

    if n_rows < 20:
        print("⚠️ Very few rows for training. Training on all data without train/test split.")
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    # Baseline: persistence (target ≈ lag1)
    y_baseline = X_test["lag1"]
    baseline_mae = mean_absolute_error(y_test, y_baseline)
    print(f"Baseline (persistence) MAE on test set: {baseline_mae:.3f}")

    # Random Forest model
    rf = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, y_pred)
    print(f"RandomForest MAE on test set: {rf_mae:.3f}")

    # Save the model
    model_path.parent.mkdir(parents=True, exist_ok=True)
    dump(rf, model_path)
    print(f"✅ Saved RandomForest model to: {model_path}")


def main() -> None:
    print_settings_summary()
    print("\nLoading daily_aggregates for ML training...")

    df = load_daily_aggregates()

    if df.empty:
        print("⚠️ daily_aggregates is empty. Run ingestion + build_features first.")
        return

    print(f"Loaded {len(df)} daily_aggregates row(s). Building features...")

    df_feat = build_features(df)
    print(f"After feature engineering, {len(df_feat)} row(s) remain.")

    # Path to save the ML model
    base_dir = Path(__file__).resolve().parents[2]
    model_file = base_dir / "models" / "aqi_rf_model.joblib"

    train_random_forest(df_feat, model_file)


if __name__ == "__main__":
    main()
