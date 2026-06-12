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

    Upserts so that existing rows are updated when new observations arrive
    for a date that was already aggregated (e.g. mid-day re-runs).
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
        WHERE o.timestamp_utc >= NOW() - INTERVAL '2 days'
        GROUP BY
            o.location_id,
            o.timestamp_utc::date
        ON CONFLICT (location_id, date) DO UPDATE
        SET
            max_aqi          = EXCLUDED.max_aqi,
            mean_aqi         = EXCLUDED.mean_aqi,
            min_aqi          = EXCLUDED.min_aqi,
            is_interpolated  = FALSE;
        """
    )

    engine = get_engine()

    with engine.begin() as conn:
        result = conn.execute(sql)
        # rowcount may be -1 for some dialects, but often indicates inserted rows
        inserted = result.rowcount

    print(f"✅ Daily aggregation complete. Rows upserted: {inserted}")


if __name__ == "__main__":
    run_daily_aggregation()
