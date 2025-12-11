@echo off
cd /d C:\Users\steve\Documents\aqi-forecasting-pipeline
call .venv\Scripts\activate.bat

echo [1/3] Ingesting AirNow data...
python -m src.ingest.ingest_airnow

echo [2/3] Building daily aggregates...
python -m src.features.build_features

echo [3/3] Forecasting and notifying...
python -m src.forecast_and_notify

echo Pipeline run complete.
