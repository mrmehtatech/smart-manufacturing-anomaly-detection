"""Read and validate manufacturing datasets."""
from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {
    "timestamp", "machine_id", "temperature_c", "vibration_mm_s",
    "cycle_time_sec", "throughput_units", "total_count", "good_count", "defect_count"
}

def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file and fail clearly if required fields are absent."""
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {path}")
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    return frame

def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate schema and remove exact duplicate rows."""
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    result = frame.copy()
    result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce", utc=True)
    numeric = [
        "temperature_c", "vibration_mm_s", "cycle_time_sec",
        "throughput_units", "total_count", "good_count", "defect_count"
    ]
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(subset=["timestamp", "machine_id"] + numeric)
    result = result.drop_duplicates()
    result = result[
        (result["cycle_time_sec"] > 0)
        & (result["throughput_units"] >= 0)
        & (result["total_count"] >= 0)
        & (result["good_count"] >= 0)
        & (result["defect_count"] >= 0)
        & (result["good_count"] <= result["total_count"])
        & (result["defect_count"] <= result["total_count"])
    ]
    return result.sort_values(["machine_id", "timestamp"]).reset_index(drop=True)
