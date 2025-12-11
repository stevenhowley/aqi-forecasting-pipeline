import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests


# Read the API key from the environment (.env loaded earlier by settings.py)
AIRNOW_API_KEY = os.getenv("AIRNOW_API_KEY")

# Base URL for current observations by latitude/longitude
# You may tweak this if AirNow changes their endpoints.
BASE_URL = "https://www.airnowapi.org/aq/observation/latLong/current/"


class AirNowConfigError(RuntimeError):
    """Raised when the AirNow API configuration is invalid."""


def ensure_api_key() -> None:
    """
    Ensure we have an API key before making requests.
    """
    if not AIRNOW_API_KEY or AIRNOW_API_KEY in ("YOUR_AIRNOW_API_KEY_HERE", "REPLACE_ME"):
        raise AirNowConfigError(
            "AIRNOW_API_KEY is not set or is a placeholder. "
            "Set it in your .env file."
        )


def fetch_current_observations(
    latitude: float,
    longitude: float,
    distance_miles: int = 25,
    pollutants: Optional[List[str]] = None,
    timeout: int = 20,
) -> List[Dict[str, Any]]:
    """
    Fetch current air quality observations from the AirNow API for a given lat/lon.

    Parameters
    ----------
    latitude : float
        Latitude in decimal degrees.
    longitude : float
        Longitude in decimal degrees.
    distance_miles : int
        Search radius in miles for nearby monitoring sites.
    pollutants : list of str, optional
        If provided, filter to only these pollutant names (e.g. ["PM2.5", "OZONE"]).
    timeout : int
        HTTP request timeout in seconds.

    Returns
    -------
    List[Dict[str, Any]]
        Raw JSON records from the API (one per pollutant / site).
    """
    ensure_api_key()

    params = {
        "format": "application/json",
        "latitude": latitude,
        "longitude": longitude,
        "distance": distance_miles,
        "API_KEY": AIRNOW_API_KEY,
    }

    response = requests.get(BASE_URL, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        # AirNow usually returns a list; if not, wrap it for consistency
        data = [data]

    if pollutants:
        pollutants_upper = {p.upper() for p in pollutants}
        data = [
            d
            for d in data
            if str(d.get("ParameterName", "")).upper() in pollutants_upper
        ]

    return data


def normalize_observations(
    location_id: int,
    api_records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform AirNow API records into rows matching the observations table schema.

    observations columns:
        location_id, timestamp_utc, aqi, category, pollutant, raw_json
    """
    normalized: List[Dict[str, Any]] = []

    for rec in api_records:
        aqi = rec.get("AQI")
        pollutant = rec.get("ParameterName")
        category_obj = rec.get("Category") or {}
        category_name = category_obj.get("Name")

        date_str = rec.get("DateObserved")  # e.g. "2025-12-10"
        hour = rec.get("HourObserved")      # e.g. 14 (local hour)

        if date_str is None or hour is None:
            # Skip malformed records
            continue

        # Build a naive datetime. AirNow also provides LocalTimeZone,
        # but for this project we'll treat this as UTC or adjust later.
        try:
            hour_int = int(hour)
            dt = datetime.strptime(f"{date_str} {hour_int:02d}", "%Y-%m-%d %H")
        except Exception:
            # Skip if we can't parse
            continue

        normalized.append(
            {
                "location_id": location_id,
                "timestamp_utc": dt,
                "aqi": aqi,
                "category": category_name,
                "pollutant": pollutant,
                "raw_json": rec,
            }
        )

    return normalized
