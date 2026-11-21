"""KPI and model evaluation calculations."""
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

def calculate_kpis(frame: pd.DataFrame) -> dict:
    """Calculate interval production and quality indicators."""
    total = int(frame["total_count"].sum())
    good = int(frame["good_count"].sum())
    defects = int(frame["defect_count"].sum())
    return {
        "records": int(len(frame)),
        "machines": int(frame["machine_id"].nunique()),
        "total_units": total,
        "good_units": good,
        "defect_units": defects,
        "defect_rate": (defects / total) if total else None,
        "anomaly_count": int(frame["is_anomaly"].sum()) if "is_anomaly" in frame else 0,
        "spc_alerts": int(frame["spc_flag"].sum()) if "spc_flag" in frame else 0,
        "iforest_alerts": int(frame["iforest_flag"].sum()) if "iforest_flag" in frame else 0,
    }

def evaluate_simulated_labels(frame: pd.DataFrame) -> dict:
    """Evaluate flags against simulator labels; labels are never model features."""
    if "ground_truth_anomaly" not in frame:
        return {}
    truth = frame["ground_truth_anomaly"].astype(int)
    pred = frame["is_anomaly"].astype(int)
    tn, fp, fn, tp = confusion_matrix(truth, pred, labels=[0, 1]).ravel()
    return {
        "precision": float(precision_score(truth, pred, zero_division=0)),
        "recall": float(recall_score(truth, pred, zero_division=0)),
        "f1_score": float(f1_score(truth, pred, zero_division=0)),
        "true_positive": int(tp), "false_positive": int(fp),
        "true_negative": int(tn), "false_negative": int(fn),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else None,
    }

def calculate_oee(frame: pd.DataFrame) -> dict:
    """Return OEE only if explicit time and ideal-cycle inputs are present."""
    required = {"planned_production_time_sec", "operating_time_sec", "ideal_cycle_time_sec"}
    if not required.issubset(frame.columns):
        return {"available": False, "reason": "Required time fields are not present in the dataset."}
    planned = float(frame["planned_production_time_sec"].sum())
    operating = float(frame["operating_time_sec"].sum())
    total = float(frame["total_count"].sum())
    good = float(frame["good_count"].sum())
    ideal = float(frame["ideal_cycle_time_sec"].dropna().iloc[0]) if frame["ideal_cycle_time_sec"].notna().any() else 0.0
    if planned <= 0 or operating <= 0 or total <= 0:
        return {"available": False, "reason": "A required OEE denominator is zero or unavailable."}
    availability = operating / planned
    performance = (ideal * total) / operating
    quality = good / total
    return {
        "available": True,
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": availability * performance * quality,
    }
