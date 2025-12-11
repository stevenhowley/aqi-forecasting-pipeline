from datetime import timedelta, datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy import text
from joblib import load

from src.db.connection import get_engine
from src.config.settings import print_settings_summary

MODEL_NAME = "baseline_persistence_v1"
ALERT_THRESHOLD = 100  # AQI level for alerts

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
    model_path = BASE_DIR / "models" / "aqi_baseline_model.joblib"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    model = load(model_path)
    return model, model_path


def load_latest_daily_aggregates() -> pd.DataFrame:
    """
    Load the most recent daily aggregate per location.

    Returns DataFrame with:
        - location_id
        - date
        - max_aqi
    """
    engine = get_engine()

    sql = text(
        """
        SELECT da.location_id, da.date, da.max_aqi
        FROM daily_aggregates da
        JOIN (
            SELECT location_id, MAX(date) AS max_date
            FROM daily_aggregates
            GROUP BY location_id
        ) latest
          ON da.location_id = latest.location_id
         AND da.date = latest.max_date
        ORDER BY da.location_id;
        """
    )

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, parse_dates=["date"])

    return df


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

    model, model_path = load_model()
    msg = f"Using model from: {model_path}"
    print(msg)
    log_alert(msg)

    df = load_latest_daily_aggregates()

    if df.empty:
        msg = "No daily aggregates found. Run ingestion + aggregation first."
        print(f"⚠️ {msg}")
        log_alert(f"⚠️ {msg}")
        return

    print(f"Loaded {len(df)} latest daily aggregate row(s).")
    log_alert(f"Loaded {len(df)} latest daily aggregate row(s).")

    # Predict next-day AQI
    df["forecast_aqi"] = model.predict(df).round().astype(int)
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

    # Simple alerting: log and print any forecasts above threshold
    high_forecasts = df[df["forecast_aqi"] >= ALERT_THRESHOLD]

    if high_forecasts.empty:
        msg = (
            f"No locations exceed AQI threshold {ALERT_THRESHOLD}. "
            f"Max forecast AQI = {df['forecast_aqi'].max()}"
        )
        print(msg)
        log_alert(msg)
    else:
        header = f"⚠️ ALERT: Locations with forecast AQI >= {ALERT_THRESHOLD}:"
        print("\n" + header)
        log_alert(header)

        for row in high_forecasts.itertuples():
            line = (
                f"location_id={row.location_id}, "
                f"target_date={row.target_date.date()}, "
                f"forecast_aqi={row.forecast_aqi}"
            )
            print(" - " + line)
            log_alert("ALERT: " + line)


if __name__ == "__main__":
    run_forecast_and_notify()
