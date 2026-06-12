"""
One-time backfill: linearly interpolate missing daily_aggregates rows.

Adds is_interpolated column if not present, then fills gaps up to
MAX_GAP_DAYS using linear interpolation between surrounding known values.
Gaps larger than MAX_GAP_DAYS are skipped as too uncertain to estimate.
"""
from datetime import timedelta

from sqlalchemy import text

from src.db.connection import get_engine
from src.config.settings import print_settings_summary

MAX_GAP_DAYS = 7


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def run_backfill() -> None:
    print_settings_summary()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE daily_aggregates
            ADD COLUMN IF NOT EXISTS is_interpolated BOOLEAN NOT NULL DEFAULT FALSE
        """))

        locations = conn.execute(text(
            "SELECT id, name FROM locations ORDER BY id"
        )).mappings().all()

        total_inserted = 0

        for loc in locations:
            loc_id = loc["id"]
            name = loc["name"]

            rows = conn.execute(text("""
                SELECT date, max_aqi, mean_aqi, min_aqi
                FROM daily_aggregates
                WHERE location_id = :loc_id
                  AND is_interpolated = FALSE
                ORDER BY date
            """), {"loc_id": loc_id}).mappings().all()

            if len(rows) < 2:
                print(f"⚠️  {name}: not enough data to interpolate, skipping.")
                continue

            inserted = 0

            for i in range(len(rows) - 1):
                before = rows[i]
                after = rows[i + 1]

                gap_start = before["date"] + timedelta(days=1)
                gap_end = after["date"]

                if gap_start >= gap_end:
                    continue

                gap_days = (gap_end - gap_start).days
                span_days = (after["date"] - before["date"]).days

                if gap_days > MAX_GAP_DAYS:
                    print(
                        f"  ⚠️  {name}: gap {gap_start} → {gap_end - timedelta(days=1)}"
                        f" ({gap_days}d) exceeds limit, skipping."
                    )
                    continue

                for d in range(gap_days):
                    missing_date = gap_start + timedelta(days=d)
                    t = (missing_date - before["date"]).days / span_days

                    conn.execute(text("""
                        INSERT INTO daily_aggregates
                            (location_id, date, max_aqi, mean_aqi, min_aqi, is_interpolated)
                        VALUES
                            (:loc_id, :date, :max_aqi, :mean_aqi, :min_aqi, TRUE)
                        ON CONFLICT (location_id, date) DO NOTHING
                    """), {
                        "loc_id": loc_id,
                        "date": missing_date,
                        "max_aqi": round(lerp(before["max_aqi"], after["max_aqi"], t)),
                        "mean_aqi": lerp(before["mean_aqi"], after["mean_aqi"], t),
                        "min_aqi": round(lerp(before["min_aqi"], after["min_aqi"], t)),
                    })
                    inserted += 1

            print(f"✅ {name}: interpolated {inserted} day(s).")
            total_inserted += inserted

    print(f"\nDone. Total interpolated rows inserted: {total_inserted}")


if __name__ == "__main__":
    run_backfill()
