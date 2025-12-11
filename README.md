# Automated Air Quality Forecasting Pipeline (Oregon AQI)

This project implements an **automated end-to-end pipeline** for collecting air quality data in Oregon, storing it in PostgreSQL, transforming it into daily aggregates, generating forecasts using a baseline AQI model, and logging alerts when poor air quality is expected.

It is designed as a real-world MLOps-style workflow: modular, scheduled, reproducible, and easy to extend with more sophisticated models later.

---

## Overview

The pipeline performs the following tasks:

### 1. Ingestion
- Pulls real-time AQI observations from the **AirNow API**
- Stores raw hourly measurements in a PostgreSQL database (`observations` table)

### 2. Daily Aggregation
- Converts raw observations into daily metrics per location:
  - `max_aqi`
  - `mean_aqi`
  - `min_aqi`

### 3. Forecasting
- Uses a saved baseline model (`persistence` strategy)
- Predicts *next-day AQI* for each Oregon location
- Writes results into the `forecasts` table

### 4. Alerting + Logging
- Checks if forecasted AQI exceeds a threshold (default: **100**)
- Writes alerts to `logs/alerts.log`
- Prints alerts to the console when forecasting runs

### 5. Extensible Design
The project intentionally uses a modular folder structure so more advanced ML models, dashboards, and API layers can be added later.

---

## Project Structure

```
aqi-forecasting-pipeline/
├── .venv/                     # Virtual environment
├── data/
│   ├── raw/
│   ├── processed/
├── logs/
│   └── alerts.log
├── models/
│   └── aqi_baseline_model.joblib
├── sql/
│   ├── schema.sql
│   └── seed_locations.sql
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── init_db.py
│   │   └── seed_locations.py
│   ├── ingest/
│   │   ├── airnow_client.py
│   │   └── ingest_airnow.py
│   ├── features/
│   │   └── build_features.py
│   ├── models/
│   │   ├── baseline_model.py
│   │   └── train_model.py
│   └── forecast_and_notify.py
├── .env
├── requirements.txt
└── README.md
```

---

## Database Schema

**Database:** `aqi_db`  
**Port:** `5433`

### `locations`
| column   | type               |
|----------|--------------------|
| id       | SERIAL PRIMARY KEY |
| name     | TEXT               |
| latitude | DOUBLE PRECISION   |
| longitude| DOUBLE PRECISION   |

### `observations`
Raw AirNow observations including pollutant, AQI, timestamp, and JSON metadata.

### `daily_aggregates`
Daily summary statistics computed from observations.

### `forecasts`
Stored predictions for next-day AQI per location and model.

---

## Environment Variables

Create a `.env` file in the project root:

```
AIRNOW_API_KEY=REPLACE_ME

DB_USER=postgres
DB_PASSWORD=REPLACE_ME
DB_HOST=localhost
DB_PORT=5433
DB_NAME=aqi_db
```

Do **NOT** commit `.env` to Git.

---

## Running the Pipeline

Activate your virtual environment (example on Windows):

```
cd path\to\aqi-forecasting-pipeline
.venv\Scripts\activate.bat
```

### 1. Initialize the database schema

```
python -m src.db.init_db
```

### 2. Seed Oregon locations

```
python -m src.db.seed_locations
```

### 3. Ingest live AirNow data

```
python -m src.ingest.ingest_airnow
```

### 4. Build daily aggregates

```
python -m src.features.build_features
```

### 5. Train the baseline model

```
python -m src.models.train_model
```

### 6. Run forecasting + alerts

```
python -m src.forecast_and_notify
```

Alerts are written to:

```
logs/alerts.log
```

---

## Baseline Model

The baseline model uses a simple **persistence strategy**:

```
forecast_aqi(t+1) = observed_max_aqi(t)
```

This provides a reference benchmark before upgrading to more advanced ML models.

---

## Alerting System

Alerts trigger when:

```
forecast_aqi >= 100
```

Example:

```
[2025-12-10T23:15:42 UTC] ALERT: location_id=5, target_date=2025-12-11, forecast_aqi=135
```

---

## Scheduling (Future Work)

This pipeline can be fully automated using **Windows Task Scheduler**:

- 3:00 PM → ingestion  
- 3:02 PM → daily aggregation  
- 3:03 PM → forecasting + alerts  

Instructions will be added in a future update.

---

## Future Enhancements

- Add lag-based and rolling-window features  
- Train regression, random forest, gradient boosting, or time-series models  
- Add FastAPI endpoint to serve forecasts  
- Build a dashboard for observations + forecasts  
- Containerize with Docker  
- Multi-day forecasting  
- Deploy to cloud platforms  

---

## Current Status

The pipeline currently supports:

- ✔️ AirNow ingestion  
- ✔️ Observation storage  
- ✔️ Daily feature creation  
- ✔️ Baseline model training  
- ✔️ Forecast generation  
- ✔️ Alert logging  
- ✔️ Modular, extensible architecture  

---

## Notes

This project is part of a professional data engineering + ML portfolio.  
It will continue evolving toward a full MLOps deployment with automation, advanced modeling, and API support.

Feel free to explore, run individual steps, or extend the system!
