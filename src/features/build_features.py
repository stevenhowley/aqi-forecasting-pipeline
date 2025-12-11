from sqlalchemy import text

from src.db.connection import get_engine
from src.config.settings import print_settings_summary


def run_daily_aggregation() -> None:
    """
    Aggregate raw observations into daily_aggregates.

    For each (location_id, date), compute:
      - max_aqi
      - mean_aqi
      - min_aqi

    Only inserts rows that don't already exist, thanks to the UNIQUE constraint
    on (location_id, date) and ON CONFLICT DO NOTHING.
    """
    print_settings_summary()
    print("\nBuilding daily aggregates...")

    # This query:
    #   - derives a date from timestamp_utc
    #   - aggregates AQI metrics per location + date
    #   - inserts into daily_aggregates, skipping rows that already exist
    sql = text(
        """
        INSERT INTO daily_aggregates (
            location_id,
            date,
            max_aqi,
            mean_aqi,
            min_aqi
        )
        SELECT
            o.location_id,
            o.timestamp_utc::date AS date,
            MAX(o.aqi) AS max_aqi,
            AVG(o.aqi)::double precision AS mean_aqi,
            MIN(o.aqi) AS min_aqi
        FROM observations o
        LEFT JOIN daily_aggregates da
          ON da.location_id = o.location_id
         AND da.date = o.timestamp_utc::date
        WHERE da.id IS NULL
        GROUP BY
            o.location_id,
            o.timestamp_utc::date
        ON CONFLICT (location_id, date) DO NOTHING;
        """
    )

    engine = get_engine()

    with engine.begin() as conn:
        result = conn.execute(sql)
        # rowcount may be -1 for some dialects, but often indicates inserted rows
        inserted = result.rowcount

    print(f"✅ Daily aggregation complete. Rows inserted (if known): {inserted}")


if __name__ == "__main__":
    run_daily_aggregation()
