# Real-Time Anomaly Detection & Process Optimization in Smart Manufacturing

A modular Python prototype for synthetic manufacturing telemetry, SPC and Isolation Forest anomaly detection, advisory recommendations, and a Streamlit monitoring dashboard.

## Important scope statement
This project uses synthetic data by default. It is a student decision-support prototype, not a certified industrial control system. It does not send commands to physical equipment. Anomaly flags require human review.

## Requirements
- Python 3.10 or newer
- pip
- Optional: MySQL 8+ for persistence integration

## Setup (Windows PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Generate data and run analytics
```powershell
python main.py
```
The pipeline writes:
- `data/raw/manufacturing_readings.csv`
- `data/processed/processed_readings.csv`
- `outputs/anomaly_events.csv`
- `logs/application.log`

## Start the dashboard
```powershell
streamlit run dashboard/app.py
```

## Configuration
Settings are read from environment variables in `config.py`. Copy `.env.example` to `.env`. For local execution, load `.env` in your shell or add `load_dotenv()` at the application startup if desired. Never commit `.env` or real credentials.

## Architecture
- `src/data_simulator.py`: synthetic data generation
- `src/data_loader.py`: schema validation and CSV loading
- `src/preprocessing.py`: cleaning and rolling features
- `src/anomaly_detection.py`: SPC z-score screening and Isolation Forest
- `src/analysis.py`: KPIs and evaluation metrics
- `src/optimization.py`: transparent advisory recommendations
- `src/database.py`: optional MySQL persistence helpers
- `src/pipeline.py`: pipeline orchestration
- `dashboard/app.py`: Streamlit user interface

## Notes on interpretation
- The simulator's `ground_truth_anomaly` label is used only to evaluate detection performance. It is not passed to Isolation Forest.
- The current SPC screening uses a per-machine full-sample z-score as an initial prototype signal; for prospective real-time SPC, establish a baseline period and freeze control limits.
- OEE is not calculated unless planned production time, operating time and ideal cycle time are available. The sample simulator does not invent those fields.
- The Isolation Forest score is a model decision score, not a probability of equipment failure.
- MySQL schema is supplied separately in `smart_manufacturing_schema.sql`. The optional database helper requires a configured database and environment variables.

## Coding standards
Only `.py` source files are used. No Jupyter Notebook or Colab files are included. Business logic is separated from data loading, persistence and visualization.
