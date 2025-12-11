\# Project Roadmap – Automated AQI Forecasting Pipeline



This roadmap tracks what has been done so far and what is planned for the future.



---



\## Completed Milestones



\- \[x] Set up Python virtual environment and basic project structure

\- \[x] Configure PostgreSQL database (`aqi\_db` on port 5433)

\- \[x] Create core tables: `locations`, `observations`, `daily\_aggregates`, `forecasts`

\- \[x] Seed Oregon locations into `locations`

\- \[x] Implement AirNow ingestion (`ingest\_airnow.py`) → `observations`

\- \[x] Implement daily aggregation (`build\_features.py`) → `daily\_aggregates`

\- \[x] Implement baseline persistence model (`NaiveAQIForecastModel`)

\- \[x] Train and save baseline model (`train\_model.py` → `models/aqi\_baseline\_model.joblib`)

\- \[x] Implement forecasting + alerting (`forecast\_and\_notify.py`) → `forecasts`, `logs/alerts.log`

\- \[x] Add logging of forecast runs and alerts to `logs/alerts.log`

\- \[x] Write initial README with architecture diagram and badges

\- \[x] Add MIT LICENSE file



---



\## Near-Term Goals



\### A. Repository Polish (now)

\- \[x] Add `ROADMAP.md` to describe project direction

\- \[ ] Keep README updated as the project evolves



\### B. Automation \& Scheduling

\- \[ ] Add simple `.bat` scripts to run:

&nbsp; - \[ ] Ingestion

&nbsp; - \[ ] Daily aggregation

&nbsp; - \[ ] Forecasting + alerts

\- \[ ] Document how to schedule these scripts using Windows Task Scheduler



\### C. Improved Modeling

\- \[ ] Add lag features (e.g., AQI(t-1), AQI(t-2), rolling means) to training data

\- \[ ] Implement a more advanced model (e.g., RandomForestRegressor)

\- \[ ] Compare performance against the baseline persistence model

\- \[ ] Save evaluation metrics (MAE/RMSE) in a small report (e.g., `model\_report.md`)



---



\## Medium-Term Enhancements



\### D. API Layer (FastAPI)

\- \[ ] Implement a FastAPI app that can:

&nbsp; - \[ ] Return the latest forecast per location

&nbsp; - \[ ] Return recent history for a given location

\- \[ ] Document API usage in the README



\### E. Visualization \& Notebooks

\- \[ ] Add Jupyter notebooks for:

&nbsp; - \[ ] Exploratory data analysis (EDA) of AQI data

&nbsp; - \[ ] Model performance visualization (forecasts vs. actuals)

\- \[ ] Optionally add a lightweight dashboard (e.g., Streamlit or Plotly Dash)



---



\## Longer-Term Ideas



\### F. MLOps \& Deployment

\- \[ ] Containerize the project using Docker

\- \[ ] Add GitHub Actions for:

&nbsp; - \[ ] Running tests (when tests are added)

&nbsp; - \[ ] Linting / code quality checks

\- \[ ] Deploy the API or pipeline to a cloud platform (Render, Railway, AWS, GCP, etc.)



\### G. Advanced Forecasting

\- \[ ] Add multi-day forecasting (e.g., AQI(t+1), AQI(t+2), AQI(t+3))

\- \[ ] Experiment with time-series models (Prophet, ARIMA)

\- \[ ] Explore deep learning approaches (e.g., sequence models) if data volume allows



---



\## Notes



This roadmap is meant to be a living document.  

As the project evolves, items can be checked off, refined, or reprioritized.



The main goal is to demonstrate:

\- Solid data engineering foundations

\- Clean and modular Python code

\- Sensible MLOps practices (version control, automation, monitoring)

\- Clear documentation that a hiring manager or teammate can follow.



