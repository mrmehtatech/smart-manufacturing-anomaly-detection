"""Statistical and machine-learning anomaly detection."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_FEATURES = [
    "temperature_c", "vibration_mm_s", "cycle_time_sec",
    "throughput_units", "defect_rate", "cycle_time_deviation"
]

def add_spc_flags(frame: pd.DataFrame, z_threshold: float = 3.0) -> pd.DataFrame:
    """Add baseline z-score flags per machine and feature."""
    result = frame.copy()
    flags = []
    for machine_id, group in result.groupby("machine_id", sort=False):
        machine_flags = pd.Series(False, index=group.index)
        for feature in ["temperature_c", "vibration_mm_s", "cycle_time_sec"]:
            mean = group[feature].mean()
            std = group[feature].std(ddof=1)
            if pd.notna(std) and std > 0:
                machine_flags |= ((group[feature] - mean).abs() / std) > z_threshold
        flags.append(machine_flags)
    combined = pd.concat(flags).sort_index() if flags else pd.Series(False, index=result.index)
    result["spc_flag"] = combined.astype(bool)
    return result

def detect_isolation_forest(
    frame: pd.DataFrame,
    estimators: int,
    contamination: float,
    random_state: int,
) -> tuple[pd.DataFrame, IsolationForest]:
    """Fit Isolation Forest and append its decision score and outlier label."""
    result = frame.copy()
    feature_frame = result[MODEL_FEATURES].replace([np.inf, -np.inf], np.nan)
    medians = feature_frame.median()
    feature_frame = feature_frame.fillna(medians).fillna(0.0)
    model = IsolationForest(
        n_estimators=estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    predictions = model.fit_predict(feature_frame)
    result["iforest_decision_score"] = model.decision_function(feature_frame)
    result["iforest_flag"] = predictions == -1
    result["is_anomaly"] = result["spc_flag"] | result["iforest_flag"]
    return result, model
