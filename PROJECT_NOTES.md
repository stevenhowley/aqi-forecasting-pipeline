\# Automated Air Quality Forecasting Pipeline – Project Instructions



These are instructions for ChatGPT to help Steven work on this project.



\## 1. System / Environment



\- OS: Windows (PowerShell and Command Prompt available)

\- Python: \*\*3.11.8\*\*, installed via official python.org installer

\- Project folder:  

&nbsp; `C:\\Users\\steve\\Documents\\aqi-forecasting-pipeline`

\- Virtual environment:

&nbsp; - Location: `.venv` in the project root

&nbsp; - Activation (preferred) is via \*\*Command Prompt\*\*, not PowerShell:

&nbsp;   ```bat

&nbsp;   cd C:\\Users\\steve\\Documents\\aqi-forecasting-pipeline

&nbsp;   .venv\\Scripts\\activate.bat

&nbsp;   ```

&nbsp; - Once activated, the prompt will look like:

&nbsp;   ```text

&nbsp;   (.venv) C:\\Users\\steve\\Documents\\aqi-forecasting-pipeline>

&nbsp;   ```

\- Package manager: `pip` inside the virtual environment

\- Other tools:

&nbsp; - PostgreSQL installed locally on Windows

&nbsp; - One PostgreSQL instance already existed on port `5432`

&nbsp; - A new PostgreSQL instance for this project is running on port \*\*5433\*\* (unless explicitly changed later)

&nbsp; - ChatGPT should assume:

&nbsp;   - Host: `localhost`

&nbsp;   - Port: `5433`

&nbsp;   - Database name: `aqi\_db` (placeholder)

&nbsp;   - User: `postgres` (placeholder)

&nbsp;   - Password: to be provided by Steven or left as an environment variable



If any credentials or ports are unclear, ChatGPT should use \*\*placeholders\*\* in code and `.env` files and tell Steven where to fill them in.



\## 2. High-Level Project Goal



Build an \*\*automated pipeline\*\* that:



1\. Ingests air quality data (e.g., PM2.5, ozone) for Oregon from trusted sources (such as EPA AQS or pre-downloaded CSVs).

2\. Cleans and stores the data in a \*\*PostgreSQL\*\* database.

3\. Trains forecasting models (e.g., for daily AQI / pollutant levels by county or station).

4\. Exposes forecasts through:

&nbsp;  - A Python API (e.g., FastAPI), and/or

&nbsp;  - Notebooks / scripts that generate plots and summaries.

5\. Is structured and documented enough to be showcased as a portfolio project.



\## 3. Tech Stack



\- Python 3.11

\- Virtualenv (`.venv`) in project root

\- Libraries (initial core set):

&nbsp; - `pandas`

&nbsp; - `numpy`

&nbsp; - `sqlalchemy`

&nbsp; - `psycopg2-binary` (for PostgreSQL)

&nbsp; - `python-dotenv`

&nbsp; - `fastapi`

&nbsp; - `uvicorn`

&nbsp; - Any modeling libraries we decide to use later (e.g., `scikit-learn`, `statsmodels`, `prophet` if compatible)

\- Database: PostgreSQL (local)

\- Optional: Jupyter Notebooks for exploration and visualizations



ChatGPT should always assume this environment when suggesting commands and code.



\## 4. Project Structure (Target / Recommended)



ChatGPT should help the user gradually move toward something like this:



```text

aqi-forecasting-pipeline/

├─ .venv/                     # Python virtual environment (do NOT commit)

├─ data/

│  ├─ raw/                    # Raw data dumps (CSV, JSON, etc.)

│  ├─ processed/              # Cleaned / transformed data

├─ notebooks/

│  ├─ 01\_exploration.ipynb

│  ├─ 02\_feature\_engineering.ipynb

│  └─ 03\_modeling.ipynb

├─ src/

│  ├─ \_\_init\_\_.py

│  ├─ config/                 # Config utilities (e.g., env loader)

│  │  └─ settings.py

│  ├─ db/                     # Database utilities

│  │  ├─ \_\_init\_\_.py

│  │  ├─ connection.py

│  │  └─ models.py

│  ├─ ingest/                 # Data ingestion scripts

│  │  └─ ingest\_epa\_aqs.py

│  ├─ features/               # Feature engineering logic

│  │  └─ build\_features.py

│  ├─ models/                 # Forecasting models training / inference

│  │  └─ train\_model.py

│  └─ api/                    # FastAPI app for serving forecasts

│     └─ main.py

├─ .env                       # Environment variables (not committed)

├─ requirements.txt           # Python dependencies

├─ README.md                  # Project overview

└─ PROJECT\_NOTES.md           # Optional: notes / instructions for ChatGPT



