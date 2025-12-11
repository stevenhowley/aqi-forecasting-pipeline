import os
from dotenv import load_dotenv

# Always run commands from the project root so this finds .env there.
# e.g.:
#   cd C:\Users\steve\Documents\aqi-forecasting-pipeline
#   python -m src.db.connection

load_dotenv()  # Loads variables from .env into the environment

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ClamBone5")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "aqi_db")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def print_settings_summary() -> None:
    """Helper to quickly see which DB we're pointing at (hides password)."""
    print("Database settings:")
    print(f"  DB_USER = {DB_USER}")
    print(f"  DB_HOST = {DB_HOST}")
    print(f"  DB_PORT = {DB_PORT}")
    print(f"  DB_NAME = {DB_NAME}")
