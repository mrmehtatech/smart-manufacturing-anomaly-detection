"""Central configuration for the smart manufacturing prototype."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "outputs"
LOG_DIR = BASE_DIR / "logs"

@dataclass(frozen=True)
class Settings:
    random_state: int = int(os.getenv("RANDOM_STATE", "42"))
    records_per_machine: int = int(os.getenv("RECORDS_PER_MACHINE", "500"))
    machine_count: int = int(os.getenv("MACHINE_COUNT", "3"))
    anomaly_fraction: float = float(os.getenv("SIMULATED_ANOMALY_FRACTION", "0.04"))
    rolling_window: int = int(os.getenv("ROLLING_WINDOW", "10"))
    iforest_estimators: int = int(os.getenv("IFOREST_ESTIMATORS", "150"))
    iforest_contamination: float = float(os.getenv("IFOREST_CONTAMINATION", "0.04"))
    csv_path: Path = DATA_RAW_DIR / "manufacturing_readings.csv"
    processed_path: Path = DATA_PROCESSED_DIR / "processed_readings.csv"
    events_path: Path = OUTPUT_DIR / "anomaly_events.csv"

SETTINGS = Settings()

def ensure_directories() -> None:
    """Create runtime directories if they do not already exist."""
    for directory in (DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUT_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
