from datetime import date
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from src.db.connection import get_engine
from src.config.settings import print_settings_summary

app = FastAPI(
    title="Oregon AQI Forecasting API",
    description="Serves air quality forecasts from the PostgreSQL database.",
    version="0.1.0",
)


class ForecastOut(BaseModel):
    location_id: int
    location_name: str
    target_date: date
    forecast_aqi: int
    model_name: str


@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}


@app.get("/forecasts/latest", response_model=List[ForecastOut])
def get_latest_forecasts():
    """
    Return the latest forecast per location from the database.

    For each location_id, we find the most recent target_date in the forecasts table.
    """
    engine = get_engine()

    sql = text(
        """
        SELECT
            f.location_id,
            l.name AS location_name,
            f.target_date,
            f.forecast_aqi,
            f.model_name
        FROM forecasts f
        JOIN (
            SELECT location_id, MAX(target_date) AS max_date
            FROM forecasts
            GROUP BY location_id
        ) latest
          ON f.location_id = latest.location_id
         AND f.target_date = latest.max_date
        JOIN locations l
          ON l.id = f.location_id
        ORDER BY f.location_id;
        """
    )

    with engine.connect() as conn:
        result = conn.execute(sql)
        rows = result.fetchall()

    forecasts: List[ForecastOut] = []
    for row in rows:
        forecasts.append(
            ForecastOut(
                location_id=row.location_id,
                location_name=row.location_name,
                target_date=row.target_date,
                forecast_aqi=row.forecast_aqi,
                model_name=row.model_name,
            )
        )

    return forecasts
