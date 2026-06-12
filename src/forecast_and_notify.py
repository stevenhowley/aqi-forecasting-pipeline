from datetime import timedelta, datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy import text
from joblib import load

from src.db.connection import get_engine
from src.config.settings import print_settings_summary
from src.alerts import send_alert_email, send_all_clear_email

MODEL_NAME = "random_forest_v1"
ALERT_THRESHOLD = 100  # AQI level for alerts
FEATURE_COLS = ["lag1", "lag2", "lag3", "roll3", "roll7"]

# Log file paths
BASE_DIR = Path(__file__).resolve().parents[1]  # project root
LOGS_DIR = BASE_DIR / "logs"
ALERTS_LOG_PATH = LOGS_DIR / "alerts.log"


def log_alert(message: str) -> None:
    """
    Append a timestamped alert message to logs/alerts.log.

    This is a very lightweight logging helper.
    """
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    line = f"[{timestamp} UTC] {message}\n"
    with ALERTS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def load_model():
    """
    Load the saved baseline model from the models/ directory.
    """
    model_path = BASE_DIR / "models" / "aqi_rf_model.joblib"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    model = load(model_path)
    return model, model_path


def load_recent_daily_aggregates(days: int = 10) -> pd.DataFrame:
    """
    Load the most recent N real (non-interpolated) rows per location.

    Fetches enough history to compute lag and rolling features for prediction.
    """
    engine = get_engine()

    sql = text(
        """
        SELECT location_id, date, max_aqi
        FROM daily_aggregates
        WHERE is_interpolated = FALSE
        ORDER BY location_id, date;
        """
    )

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, parse_dates=["date"])

    return df.groupby("location_id").tail(days).reset_index(drop=True)


def build_forecast_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build lag and rolling features, then return the most recent row per location.

    The most recent row has features computed from the preceding days and is
    the input used to predict tomorrow's AQI.
    """
    df = df.sort_values(["location_id", "date"]).copy()
    grp = df.groupby("location_id", group_keys=False)

    df["lag1"] = grp["max_aqi"].shift(1)
    df["lag2"] = grp["max_aqi"].shift(2)
    df["lag3"] = grp["max_aqi"].shift(3)
    df["roll3"] = grp["max_aqi"].rolling(3).mean().reset_index(level=0, drop=True)
    df["roll7"] = grp["max_aqi"].rolling(7).mean().reset_index(level=0, drop=True)

    return df.groupby("location_id").last().reset_index()


def ensure_alert_state_table() -> None:
    with get_engine().begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alert_state (
                location_id INTEGER PRIMARY KEY REFERENCES locations(id),
                in_alert BOOLEAN NOT NULL DEFAULT FALSE,
                alert_started_at TIMESTAMPTZ,
                last_forecast_aqi INTEGER
            )
        """))


def load_location_names() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text("SELECT id AS location_id, name FROM locations"), conn)


def process_alert_state(df: pd.DataFrame) -> None:
    engine = get_engine()

    with engine.connect() as conn:
        state_rows = conn.execute(text(
            "SELECT location_id, in_alert FROM alert_state"
        )).mappings().all()

    state_map = {row["location_id"]: row["in_alert"] for row in state_rows}
    now = datetime.utcnow()

    for row in df.itertuples():
        loc_id = int(row.location_id)
        loc_name = row.name
        forecast_aqi = int(row.forecast_aqi)
        target_date = row.target_date.date()
        currently_alerting = state_map.get(loc_id, False)
        over_threshold = forecast_aqi >= ALERT_THRESHOLD

        if over_threshold and not currently_alerting:
            send_alert_email(loc_name, forecast_aqi, target_date, ALERT_THRESHOLD)
            log_alert(f"Alert email sent for {loc_name}: AQI {forecast_aqi}")
            new_in_alert = True
            new_started_at = now
        elif not over_threshold and currently_alerting:
            send_all_clear_email(loc_name, forecast_aqi, target_date, ALERT_THRESHOLD)
            log_alert(f"All-clear email sent for {loc_name}: AQI {forecast_aqi}")
            new_in_alert = False
            new_started_at = None
        else:
            new_in_alert = currently_alerting
            new_started_at = now if currently_alerting else None

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO alert_state (location_id, in_alert, alert_started_at, last_forecast_aqi)
                VALUES (:loc_id, :in_alert, :started_at, :last_aqi)
                ON CONFLICT (location_id) DO UPDATE
                SET in_alert = EXCLUDED.in_alert,
                    alert_started_at = CASE
                        WHEN EXCLUDED.in_alert AND alert_state.alert_started_at IS NOT NULL
                            THEN alert_state.alert_started_at
                        ELSE EXCLUDED.alert_started_at
                    END,
                    last_forecast_aqi = EXCLUDED.last_forecast_aqi
            """), {
                "loc_id": loc_id,
                "in_alert": new_in_alert,
                "started_at": new_started_at,
                "last_aqi": forecast_aqi,
            })


def insert_forecasts(records: List[Dict[str, Any]]) -> None:
    """
    Insert forecast records into the forecasts table.

    Uses ON CONFLICT to upsert (update) existing rows for the same
    (location_id, target_date, model_name).
    """
    if not records:
        print("No forecast records to insert.")
        return

    engine = get_engine()

    sql = text(
        """
        INSERT INTO forecasts (
            location_id,
            target_date,
            forecast_aqi,
            model_name
        )
        VALUES (
            :location_id,
            :target_date,
            :forecast_aqi,
            :model_name
        )
        ON CONFLICT (location_id, target_date, model_name) DO UPDATE
        SET forecast_aqi = EXCLUDED.forecast_aqi;
        """
    )

    with engine.begin() as conn:
        conn.execute(sql, records)

    print(f"✅ Inserted/updated {len(records)} forecast row(s) in the database.")
    log_alert(f"Inserted/updated {len(records)} forecast row(s) in the database.")


def run_forecast_and_notify() -> None:
    """
    Main entry point:
      - load model
      - load latest daily aggregates
      - forecast next-day AQI
      - write forecasts to DB
      - log + print alerts for high AQI forecasts
    """
    print_settings_summary()
    print("\nRunning forecast and notify...")
    log_alert("Starting forecast_and_notify run")
    ensure_alert_state_table()

    model, model_path = load_model()
    msg = f"Using model from: {model_path}"
    print(msg)
    log_alert(msg)

    df_recent = load_recent_daily_aggregates()

    if df_recent.empty:
        msg = "No daily aggregates found. Run ingestion + aggregation first."
        print(f"⚠️ {msg}")
        log_alert(f"⚠️ {msg}")
        return

    # Warn if the most recent aggregate is more than 48 hours old
    most_recent = df_recent["date"].max()
    age_hours = (datetime.utcnow().date() - most_recent.date()).days * 24
    if age_hours > 48:
        msg = f"⚠️ Most recent daily aggregate is {age_hours}h old ({most_recent.date()}). Forecasts may be stale."
        print(msg)
        log_alert(msg)

    df = build_forecast_features(df_recent)
    df = df.merge(load_location_names(), on="location_id")
    print(f"Loaded {len(df)} latest daily aggregate row(s).")
    log_alert(f"Loaded {len(df)} latest daily aggregate row(s).")

    # Predict next-day AQI
    df["forecast_aqi"] = model.predict(df[FEATURE_COLS]).round().astype(int)
    df["target_date"] = df["date"] + pd.to_timedelta(1, unit="D")

    # Build records for insertion
    records: List[Dict[str, Any]] = []
    for row in df.itertuples():
        records.append(
            {
                "location_id": int(row.location_id),
                "target_date": row.target_date.date(),  # convert to Python date
                "forecast_aqi": int(row.forecast_aqi),
                "model_name": MODEL_NAME,
            }
        )

    insert_forecasts(records)

    # Log summary
    high_forecasts = df[df["forecast_aqi"] >= ALERT_THRESHOLD]
    if high_forecasts.empty:
        msg = (
            f"No locations exceed AQI threshold {ALERT_THRESHOLD}. "
            f"Max forecast AQI = {df['forecast_aqi'].max()}"
        )
        print(msg)
        log_alert(msg)
    else:
        for row in high_forecasts.itertuples():
            msg = f"⚠️ {row.name}: forecast AQI {row.forecast_aqi} on {row.target_date.date()}"
            print(msg)
            log_alert(msg)

    process_alert_state(df)


if __name__ == "__main__":
    run_forecast_and_notify()
