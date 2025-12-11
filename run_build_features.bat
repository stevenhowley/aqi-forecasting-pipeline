@echo off
cd /d C:\Users\steve\Documents\aqi-forecasting-pipeline
call .venv\Scripts\activate.bat
python -m src.features.build_features
