"""Explainable advisory recommendations for anomaly events."""
import pandas as pd

def generate_recommendations(frame: pd.DataFrame) -> pd.DataFrame:
    """Create human-review recommendations based on flagged variables."""
    recommendations = []
    for row in frame.loc[frame["is_anomaly"]].itertuples():
        reasons = []
        if row.temperature_c > 78:
            reasons.append("Review the approved temperature operating range and inspect cooling conditions.")
        if row.vibration_mm_s > 3.5:
            reasons.append("Ask authorized maintenance personnel to inspect vibration trend and sensor mounting.")
        if row.cycle_time_sec > 50:
            reasons.append("Review cycle-time trend, machine loading and process interruptions.")
        if row.defect_rate > 0.08:
            reasons.append("Review recent quality checks and process conditions for the affected interval.")
        if not reasons:
            reasons.append("Review the observation and nearby machine history; detector output alone does not confirm a fault.")
        recommendations.append({
            "timestamp": row.timestamp,
            "machine_id": row.machine_id,
            "recommendation": " ".join(reasons),
            "review_status": "PENDING_HUMAN_REVIEW",
        })
    return pd.DataFrame(recommendations)
