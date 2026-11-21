
"""Automated tests for the synthetic manufacturing analytics pipeline."""

import pandas as pd
import pytest

from src.data_simulator import generate_manufacturing_data
from src.data_loader import validate_frame
from src.preprocessing import preprocess_readings
from src.anomaly_detection import add_spc_flags, detect_isolation_forest


def test_simulator_and_detection_pipeline():
    """Check that the complete synthetic detection pipeline runs."""
    raw = generate_manufacturing_data(
        machine_count=2,
        records_per_machine=60,
        anomaly_fraction=0.05,
        random_state=7,
    )

    clean = validate_frame(raw)
    processed = preprocess_readings(clean, rolling_window=5)
    processed = add_spc_flags(processed)

    detected, _ = detect_isolation_forest(
        processed,
        estimators=50,
        contamination=0.05,
        random_state=7,
    )

    assert len(detected) == 120
    assert "is_anomaly" in detected.columns
    assert detected["is_anomaly"].dtype == bool


def test_simulator_generates_correct_number_of_records():
    """Check the generated record count and machine IDs."""
    data = generate_manufacturing_data(
        machine_count=3,
        records_per_machine=40,
        anomaly_fraction=0.05,
        random_state=10,
    )

    assert len(data) == 120
    assert data["machine_id"].nunique() == 3
    assert set(data["machine_id"]) == {
        "MACHINE-01",
        "MACHINE-02",
        "MACHINE-03",
    }


def test_simulator_is_reproducible():
    """Check that the same random seed produces the same readings."""
    first = generate_manufacturing_data(
        machine_count=2,
        records_per_machine=60,
        anomaly_fraction=0.05,
        random_state=7,
    )

    second = generate_manufacturing_data(
        machine_count=2,
        records_per_machine=60,
        anomaly_fraction=0.05,
        random_state=7,
    )

    pd.testing.assert_frame_equal(
        first.drop(columns=["timestamp"]),
        second.drop(columns=["timestamp"]),
    )


def test_simulator_rejects_invalid_parameters():
    """Check that invalid simulator settings raise ValueError."""
    with pytest.raises(ValueError):
        generate_manufacturing_data(
            machine_count=0,
            records_per_machine=60,
            anomaly_fraction=0.05,
            random_state=7,
        )

    with pytest.raises(ValueError):
        generate_manufacturing_data(
            machine_count=2,
            records_per_machine=20,
            anomaly_fraction=0.05,
            random_state=7,
        )

    with pytest.raises(ValueError):
        generate_manufacturing_data(
            machine_count=2,
            records_per_machine=60,
            anomaly_fraction=0.6,
            random_state=7,
        )
