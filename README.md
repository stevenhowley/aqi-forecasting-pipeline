\# Automated Air Quality Forecasting Pipeline (Oregon AQI)



This project implements an \*\*automated end-to-end pipeline\*\* for collecting air quality data in Oregon, storing it in PostgreSQL, transforming it into daily aggregates, generating forecasts using a baseline AQI model, and logging alerts when poor air quality is expected.



It is designed as a real-world MLOps-style workflow: modular, scheduled, reproducible, and easy to extend with more sophisticated models later.



---



\## Overview



The pipeline performs the following tasks:



\### 1. Ingestion

\- Pulls real-time AQI observations from the \*\*AirNow API\*\*

\- Stores raw hourly measurements in a PostgreSQL database (`observations` table)



\### 2. Daily Aggregation

\- Converts raw observations into daily metrics per location:

&nbsp; - `max\_aqi`

&nbsp; - `mean\_aqi`

&nbsp; - `min\_aqi`



\### 3. Forecasting

\- Uses a saved baseline model (`persistence` strategy)

\- Predicts \*next-day AQI\* for each Oregon location

\- Writes results into the `forecasts` table



\### 4. Alerting + Logging

\- Checks if forecasted AQI exceeds a threshold (default: \*\*100\*\*)

\- Writes alerts to `logs/alerts.log`

\- Prints alerts to the console when forecasting runs



\### 5. Extensible Design

The project intentionally uses a modular folder structure so more advanced ML models, dashboards, and API layers can be added later.



---



\## Project Structure



```

aqi-forecasting-pipeline/

├── .venv/                     # Virtual environment

├── data/

│   ├── raw/

│   ├── processed/

├── logs/

│   └── alerts.log

├── models/

│   └── aqi\_baseline\_model.joblib

├── sql/

│   ├── schema.sql

│   └── seed\_locations.sql

├── src/

│   ├── config/

│   │   └── settings.py

│   ├── db/

│   │   ├── connection.py

│   │   ├── init\_db.py

│   │   └── seed\_locations.py

│   ├── ingest/

│   │   ├── airnow\_client.py

│   │   └── ingest\_airnow.py

│   ├── features/

│   │   └── build\_features.py

│   ├── models/

│   │   ├── baseline\_model.py

│   │   └── train\_model.py

│   └── forecast\_and\_notify.py

├── .env

├── requirements.txt

└── README.md

```



---



\## Database Schema



\*\*Database:\*\* `aqi\_db`  

\*\*Port:\*\* `5433`



\### `locations`

| column   | type               |

|----------|--------------------|

| id       | SERIAL PRIMARY KEY |

| name     | TEXT               |

| latitude | DOUBLE PRECISION   |

| longitude| DOUBLE PRECISION   |



\### `observations`

Raw AirNow observations including pollutant, AQI, timestamp, and JSON metadata.



\### `daily\_aggregates`

Daily summary statistics computed from observations.



\### `forecasts`

Stored predictions for next-day AQI per location and model.



---



\## Environment Variables



Create a `.env` file in the project root:



```

AIRNOW\_API\_KEY=REPLACE\_ME



DB\_USER=postgres

DB\_PASSWORD=REPLACE\_ME

DB\_HOST=localhost

DB\_PORT=5433

DB\_NAME=aqi\_db

```



Do \*\*NOT\*\* commit `.env` to Git.



---



\## Running the Pipeline



Activate your virtual environment (example on Windows):



```

cd path\\to\\aqi-forecasting-pipeline

.venv\\Scripts\\activate.bat

```



\### 1. Initialize the database schema



```

python -m src.db.init\_db

```



\### 2. Seed Oregon locations



```

python -m src.db.seed\_locations

```



\### 3. Ingest live AirNow data



```

python -m src.ingest.ingest\_airnow

```



\### 4. Build daily aggregates



```

python -m src.features.build\_features

```



\### 5. Train the baseline model



```

python -m src.models.train\_model

```



\### 6. Run forecasting + alerts



```

python -m src.forecast\_and\_notify

```



Alerts are written to:



```

logs/alerts.log

```



---



\## Baseline Model



The baseline model uses a simple \*\*persistence strategy\*\*:



```

forecast\_aqi(t+1) = observed\_max\_aqi(t)

```



This provides a reference benchmark before upgrading to more advanced ML models.



---



\## Alerting System



Alerts trigger when:



```

forecast\_aqi >= 100

```



Example:



```

\[2025-12-10T23:15:42 UTC] ALERT: location\_id=5, target\_date=2025-12-11, forecast\_aqi=135

```



---



\## Scheduling (Future Work)



This pipeline can be fully automated using \*\*Windows Task Scheduler\*\*:



\- 3:00 PM → ingestion  

\- 3:02 PM → daily aggregation  

\- 3:03 PM → forecasting + alerts  



Instructions will be added in a future update.



---



\## Future Enhancements



\- Add lag-based and rolling-window features  

\- Train regression, random forest, gradient boosting, or time-series models  

\- Add FastAPI endpoint to serve forecasts  

\- Build a dashboard for observations + forecasts  

\- Containerize with Docker  

\- Multi-day forecasting  

\- Deploy to cloud platforms  



---



\## Current Status



The pipeline currently supports:



\- ✔️ AirNow ingestion  

\- ✔️ Observation storage  

\- ✔️ Daily feature creation  

\- ✔️ Baseline model training  

\- ✔️ Forecast generation  

\- ✔️ Alert logging  

\- ✔️ Modular, extensible architecture  



---



\## Notes



This project is part of a professional data engineering + ML portfolio.  

It will continue evolving toward a full MLOps deployment with automation, advanced modeling, and API support.



Feel free to explore, run individual steps, or extend the system!



