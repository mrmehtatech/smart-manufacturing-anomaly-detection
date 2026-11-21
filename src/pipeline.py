"""End-to-end analytics pipeline."""
import logging
import pandas as pd
from config import SETTINGS
from src.data_simulator import generate_manufacturing_data
from src.data_loader import validate_frame
from src.preprocessing import preprocess_readings
from src.anomaly_detection import add_spc_flags, detect_isolation_forest
from src.optimization import generate_recommendations

LOGGER = logging.getLogger(__name__)

def run_pipeline() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate, process, detect anomalies and write outputs."""
    SETTINGS.csv_path.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.processed_path.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.events_path.parent.mkdir(parents=True, exist_ok=True)

    raw = generate_manufacturing_data(
        SETTINGS.machine_count,
        SETTINGS.records_per_machine,
        SETTINGS.anomaly_fraction,
        SETTINGS.random_state,
    )
    raw.to_csv(SETTINGS.csv_path, index=False)
    LOGGER.info("Generated %s raw observations.", len(raw))

    clean = validate_frame(raw)
    processed = preprocess_readings(clean, SETTINGS.rolling_window)
    processed = add_spc_flags(processed)
    detected, _ = detect_isolation_forest(
        processed,
        SETTINGS.iforest_estimators,
        SETTINGS.iforest_contamination,
        SETTINGS.random_state,
    )
    recommendations = generate_recommendations(detected)
    detected.to_csv(SETTINGS.processed_path, index=False)
    recommendations.to_csv(SETTINGS.events_path, index=False)
    LOGGER.info("Processed %s observations; flagged %s.", len(detected), int(detected["is_anomaly"].sum()))
    return detected, recommendations
