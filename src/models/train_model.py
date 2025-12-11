from pathlib import Path

import pandas as pd
from sqlalchemy import text
from joblib import dump

from src.db.connection import get_engine
from src.config.settings import print_settings_summary
from src.models.baseline_model import NaiveAQIForecastModel


def load_training_data() -> pd.DataFrame:
    """
    Load historical daily aggregates from the database.

    Returns a DataFrame with columns:
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


def train_and_save(model_path: Path) -> None:
    """
    Train the baseline model and save it to disk as a joblib file.
    """
    print_settings_summary()
    print("\nLoading training data from daily_aggregates...")

    df = load_training_data()

    if df.empty:
        print("⚠️ No data in daily_aggregates. Run ingestion + aggregation first.")
        return

    print(f"Loaded {len(df)} daily aggregate row(s).")

    # For now, use a persistence baseline model:
    model = NaiveAQIForecastModel(strategy="persistence")
    model.fit(df)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    dump(model, model_path)

    print(f"✅ Saved baseline model to: {model_path}")


if __name__ == "__main__":
    # Project root: src/models/train_model.py → parents[2]
    base_dir = Path(__file__).resolve().parents[2]
    model_file = base_dir / "models" / "aqi_baseline_model.joblib"
    train_and_save(model_file)
