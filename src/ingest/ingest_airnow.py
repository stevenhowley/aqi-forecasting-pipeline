from typing import List, Dict, Any

from sqlalchemy import text
from psycopg2.extras import Json

from src.db.connection import get_engine
from src.config.settings import print_settings_summary
from src.ingest.airnow_client import (
    fetch_current_observations,
    normalize_observations,
    AirNowConfigError,
)


def get_locations() -> List[Dict[str, Any]]:
    """
    Load all locations from the locations table.
    """
    engine = get_engine()
    sql = text("SELECT id, name, latitude, longitude FROM locations")

    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    return [dict(row) for row in rows]


def insert_observations(records: List[Dict[str, Any]]) -> None:
    """
    Bulk insert observation records into the observations table.

    Uses ON CONFLICT DO NOTHING to avoid duplicates.
    """
    if not records:
        return

    # Prepare records so psycopg2 knows raw_json is JSON
    prepared: List[Dict[str, Any]] = []
    for rec in records:
        rec_copy = rec.copy()
        # Wrap the dict in psycopg2.extras.Json so it can be stored in JSONB
        rec_copy["raw_json"] = Json(rec_copy["raw_json"])
        prepared.append(rec_copy)

    engine = get_engine()

    insert_sql = text(
        """
        INSERT INTO observations (
            location_id,
            timestamp_utc,
            aqi,
            category,
            pollutant,
            raw_json
        )
        VALUES (
            :location_id,
            :timestamp_utc,
            :aqi,
            :category,
            :pollutant,
            :raw_json
        )
        ON CONFLICT (location_id, timestamp_utc, pollutant) DO NOTHING;
        """
    )

    with engine.begin() as conn:
        conn.execute(insert_sql, prepared)

def run_ingestion() -> None:
    """
    Main entry point: fetch current AirNow observations for each location
    and store them in the observations table.
    """
    print_settings_summary()
    print("\nStarting AirNow ingestion...")

    try:
        locations = get_locations()
    except Exception as exc:
        print("❌ Failed to load locations from the database:")
        print(exc)
        return

    if not locations:
        print("⚠️ No locations found in the locations table. Seed them first.")
        return

    total_inserted = 0

    for loc in locations:
        loc_id = loc["id"]
        name = loc["name"]
        lat = loc["latitude"]
        lon = loc["longitude"]

        print(f"\nFetching observations for {name} (id={loc_id}, lat={lat}, lon={lon})...")

        try:
            raw_records = fetch_current_observations(lat, lon, distance_miles=25)
        except AirNowConfigError as cfg_err:
            print("❌ Configuration error:", cfg_err)
            return
        except Exception as exc:
            print(f"❌ Error fetching AirNow data for {name}:")
            print(exc)
            continue

        if not raw_records:
            print(f"⚠️ No observations returned for {name}.")
            continue

        normalized = normalize_observations(loc_id, raw_records)

        if not normalized:
            print(f"⚠️ No valid normalized records for {name}.")
            continue

        try:
            insert_observations(normalized)
        except Exception as exc:
            print(f"❌ Error inserting observations for {name}:")
            print(exc)
            continue

        count = len(normalized)
        total_inserted += count
        print(f"✅ Inserted {count} observation(s) for {name}.")

    print(f"\nDone. Total observations inserted: {total_inserted}")


if __name__ == "__main__":
    run_ingestion()
