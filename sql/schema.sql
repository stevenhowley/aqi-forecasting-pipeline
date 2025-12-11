-- Schema for aqi_db database

-- Locations table: cities / areas we track
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- Raw observations ingested from AirNow / EPA AQS / other sources
CREATE TABLE IF NOT EXISTS observations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    timestamp_utc TIMESTAMPTZ NOT NULL,
    aqi INTEGER NOT NULL,
    category TEXT,
    pollutant TEXT,
    raw_json JSONB,
    CONSTRAINT uq_obs_location_time_pollutant UNIQUE (location_id, timestamp_utc, pollutant)
);

-- Daily aggregates per location
CREATE TABLE IF NOT EXISTS daily_aggregates (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    date DATE NOT NULL,
    max_aqi INTEGER,
    mean_aqi DOUBLE PRECISION,
    min_aqi INTEGER,
    CONSTRAINT uq_daily_location_date UNIQUE (location_id, date)
);

-- Forecasts (next-day or multi-day)
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    target_date DATE NOT NULL,
    forecast_aqi INTEGER NOT NULL,
    model_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_forecast_location_date_model UNIQUE (location_id, target_date, model_name)
);
