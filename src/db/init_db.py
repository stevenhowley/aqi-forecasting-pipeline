from pathlib import Path

from sqlalchemy import text

from src.db.connection import get_engine
from src.config.settings import print_settings_summary


def get_schema_sql() -> str:
    """
    Load the SQL schema file from the sql/ directory at the project root.
    """
    # This file lives in src/db/, so go up two levels to reach project root.
    base_dir = Path(__file__).resolve().parents[2]
    schema_path = base_dir / "sql" / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Could not find schema.sql at: {schema_path}")

    return schema_path.read_text(encoding="utf-8")


def init_db() -> None:
    """
    Initialize the database schema by executing schema.sql.
    """
    print_settings_summary()

    sql = get_schema_sql()
    engine = get_engine()

    print("\nInitializing database schema...")

    # Use exec_driver_sql so we can execute a multi-statement SQL script.
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)

    print("✅ Database schema initialized successfully.")


if __name__ == "__main__":
    init_db()
