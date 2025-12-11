from pathlib import Path

from sqlalchemy import text

from src.db.connection import get_engine
from src.config.settings import print_settings_summary


def get_seed_sql() -> str:
    """
    Load the SQL seed file from the sql/ directory at the project root.
    """
    base_dir = Path(__file__).resolve().parents[2]  # go up to project root
    seed_path = base_dir / "sql" / "seed_locations.sql"

    if not seed_path.exists():
        raise FileNotFoundError(f"Could not find seed_locations.sql at: {seed_path}")

    return seed_path.read_text(encoding="utf-8")


def seed_locations() -> None:
    """
    Insert initial locations into the locations table.
    """
    print_settings_summary()
    print("\nSeeding locations...")

    sql = get_seed_sql()
    engine = get_engine()

    with engine.begin() as conn:
        conn.exec_driver_sql(sql)

    print("✅ Locations seeded successfully.")


if __name__ == "__main__":
    seed_locations()
