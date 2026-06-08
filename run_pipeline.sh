#!/bin/bash
set -euo pipefail

PIPELINE_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$PIPELINE_DIR/.venv/bin/python"
LOG_DIR="$PIPELINE_DIR/logs"

mkdir -p "$LOG_DIR"

cd "$PIPELINE_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [1/3] Ingesting AirNow data..."
"$VENV_PYTHON" -m src.ingest.ingest_airnow

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [2/3] Building daily aggregates..."
"$VENV_PYTHON" -m src.features.build_features

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [3/3] Forecasting and notifying..."
"$VENV_PYTHON" -m src.forecast_and_notify

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline run complete."
