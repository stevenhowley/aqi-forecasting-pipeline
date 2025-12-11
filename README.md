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

&nbsp; - `max\_aqi`

&nbsp; - `mean\_aqi`

&nbsp; - `min\_aqi`



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

├── .venv/                     # Python virtual environment (excluded from Git)

├── data/

│   ├── raw/                   # Future raw data dumps (optional)

│   ├── processed/             # Future cleaned data (optional)

├── logs/

│   └── alerts.log             # Alert history (auto-created)

├── models/

│   └── aqi\_baseline\_model.joblib   # Saved forecasting model

├── sql/

│   ├── schema.sql             # Database schema

│   └── seed\_locations.sql     # Oregon location seeds

├── src/

│   ├── config/

│   │   └── settings.py        # Environment variable loading

│   ├── db/

│   │   ├── connection.py      # SQLAlchemy engine + DB config

│   │   ├── init\_db.py         # Create tables

│   │   └── seed\_locations.py  # Insert initial locations

│   ├── ingest/

│   │   ├── airnow\_client.py   # AirNow API client

│   │   └── ingest\_airnow.py   # Orchestrates ingestion → DB

│   ├── features/

│   │   └── build\_features.py  # Daily aggregation into daily\_aggregates

│   ├── models/

│   │   ├── baseline\_model.py  # Persistence baseline model

│   │   └── train\_model.py     # Trains + saves baseline model

│   └── forecast\_and\_notify.py # Forecasts + logs alerts

├── .env                       # Environment variables (NOT tracked by git)

├── requirements.txt

└── README.md

```



---



## Database Schema



**Database:** `aqi\_db`  

**Port:** `5433`



### `locations`

| column     | type               |

|------------|--------------------|

| id         | SERIAL PRIMARY KEY |

| name       | TEXT               |

| latitude   | DOUBLE PRECISION   |

| longitude  | DOUBLE PRECISION   |



### `observations`

Stores raw AirNow observations including pollutant, AQI, timestamp, and JSON metadata.



### `daily\_aggregates`

Daily summary statistics computed from `observations`.



### `forecasts`

Predicted next-day AQI per location, per model.



---



## Environment Variables



Create a `.env` file in the project root:



```

AIRNOW\_API\_KEY=REPLACE\_ME



DB\_USER=postgres

DB\_PASSWORD=REPLACE\_ME

DB\_HOST=localhost

DB\_PORT=5433

DB\_NAME=aqi\_db

```



Do **NOT** commit `.env` to Git.



---



## Running the Pipeline



Run all commands from Command Prompt with your venv activated:



```bat

cd C:\\Users\\steve\\Documents\\aqi-forecasting-pipeline

.venv\\Scripts\\activate.bat

```



---



### 1️⃣ Initialize the database schema



```bat

python -m src.db.init\_db

```



### 2️⃣ Seed Oregon locations



```bat

python -m src.db.seed\_locations

```



### 3️⃣ Ingest live AirNow data



```bat

python -m src.ingest.ingest\_airnow

```



### 4️⃣ Build daily aggregates



```bat

python -m src.features.build\_features

```



### 5️⃣ Train the baseline model



```bat

python -m src.models.train\_model

```



### 6️⃣ Run forecasting + alerts



```bat

python -m src.forecast\_and\_notify

```



Alerts are written to:



```

logs/alerts.log

```



---



## Baseline Model



The baseline model uses a simple **persistence strategy**:



```

forecast\_aqi(t+1) = observed\_max\_aqi(t)

```



This provides a reference point for determining whether future ML models outperform a trivial predictor.



---



## Alerting System



Alerts occur when:



```

forecast\_aqi >= 100

```



Alert examples written to `logs/alerts.log`:



```

\[2025-12-10T23:15:42 UTC] ALERT: location\_id=5, target\_date=2025-12-11, forecast\_aqi=135

```



---



## Scheduling (Future Work)



This pipeline can be fully automated via **Windows Task Scheduler**:



- **3:00 PM daily** → ingestion  

- **3:02 PM** → aggregation  

- **3:03 PM** → forecasting + alerts  



Instructions will be added in a future update.



---



## Future Enhancements



- Add lag features and ML regression models

- Train tree-based or time-series models (RF, XGBoost, Prophet, ARIMA)

- Serve forecasts via a FastAPI endpoint

- Build a dashboard to visualize predictions + trends

- Containerize with Docker

- Multi-day forecasting

- Deploy to cloud platforms



---



## Current Status



This pipeline now supports:



- ✔️ AirNow ingestion  

- ✔️ Observation storage  

- ✔️ Daily feature generation  

- ✔️ Baseline model training  

- ✔️ Forecast generation  

- ✔️ Logging + alerting  

- ✔️ Modular, extensible architecture  



---



## Notes



This project is part of a professional data engineering + ML portfolio.  

It is actively evolving toward a full MLOps pipeline with scheduling, advanced modeling, and cloud deployment.



Feel free to explore, run individual steps, or extend the system.



