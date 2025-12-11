from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config.settings import DATABASE_URL, print_settings_summary


def get_engine() -> Engine:
    """
    Create and return a SQLAlchemy engine.

    We keep this in one place so the rest of the project can import it
    without worrying about connection details.
    """
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    return engine


def test_connection() -> None:
    """
    Try a simple SELECT 1 to verify that the database connection works.
    """
    print_settings_summary()
    print("\nTesting database connection...")

    engine = get_engine()

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar_one()
            print(f"Connection successful! SELECT 1 returned: {value}")
    except Exception as exc:
        print("Error connecting to the database:")
        print(exc)


if __name__ == "__main__":
    test_connection()
