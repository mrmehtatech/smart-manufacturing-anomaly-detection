"""Preprocessing and feature engineering for time-series readings."""
import pandas as pd

BASE_FEATURES = [
    "temperature_c", "vibration_mm_s", "cycle_time_sec",
    "throughput_units", "defect_rate"
]

def preprocess_readings(frame: pd.DataFrame, rolling_window: int) -> pd.DataFrame:
    """Create machine-wise rolling features without mixing machine histories."""
    if rolling_window < 2:
        raise ValueError("rolling_window must be at least 2.")
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data = data.sort_values(["machine_id", "timestamp"]).reset_index(drop=True)
    data["defect_rate"] = (
        data["defect_count"] / data["total_count"].replace(0, pd.NA)
    ).astype(float)
    data["defect_rate"] = data["defect_rate"].fillna(0.0)

    grouped = data.groupby("machine_id", group_keys=False)
    for column in ["temperature_c", "vibration_mm_s", "cycle_time_sec", "throughput_units"]:
        data[f"{column}_rolling_mean"] = grouped[column].transform(
            lambda values: values.rolling(rolling_window, min_periods=2).mean()
        )
        data[f"{column}_rolling_std"] = grouped[column].transform(
            lambda values: values.rolling(rolling_window, min_periods=2).std()
        )
    data["cycle_time_deviation"] = data["cycle_time_sec"] - data.groupby("machine_id")[
        "cycle_time_sec"
    ].transform("median")
    data = data.replace([float("inf"), float("-inf")], pd.NA)
    return data
