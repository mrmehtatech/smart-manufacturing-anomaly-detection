
"""Generate reproducible synthetic manufacturing observations."""

import numpy as np
import pandas as pd


def generate_manufacturing_data(
    machine_count: int,
    records_per_machine: int,
    anomaly_fraction: float,
    random_state: int,
) -> pd.DataFrame:
    """Generate synthetic machine readings and a separate evaluation label."""

    if machine_count < 1 or records_per_machine < 30:
        raise ValueError(
            "machine_count must be positive and records_per_machine >= 30."
        )

    if not 0 <= anomaly_fraction < 0.5:
        raise ValueError("anomaly_fraction must be between 0 and 0.5.")

    rng = np.random.default_rng(random_state)
    frames = []

    start = (
        pd.Timestamp.now(tz="UTC").floor("s")
        - pd.to_timedelta(int(records_per_machine), unit="min")
    )

    for machine_index in range(machine_count):
        machine_id = f"MACHINE-{machine_index + 1:02d}"

        timestamps = pd.date_range(
            start=start,
            periods=records_per_machine,
            freq="min",
        )

        temperature = rng.normal(68 + machine_index, 2.2, records_per_machine)
        vibration = rng.normal(2.2, 0.35, records_per_machine)
        cycle_time = rng.normal(42, 3.0, records_per_machine)

        throughput = (
            np.clip(
                rng.normal(18, 2.0, records_per_machine),
                1,
                None,
            )
            .round()
            .astype(int)
        )

        total_count = throughput.copy()
        defect_count = rng.binomial(total_count, 0.025)
        good_count = total_count - defect_count

        labels = np.zeros(records_per_machine, dtype=int)

        anomaly_count = max(
            1,
            int(records_per_machine * anomaly_fraction),
        )

        anomaly_indices = rng.choice(
            records_per_machine,
            size=anomaly_count,
            replace=False,
        )

        labels[anomaly_indices] = 1

        for idx in anomaly_indices:
            pattern = rng.integers(0, 4)

            if pattern == 0:
                temperature[idx] += rng.uniform(9, 16)

            elif pattern == 1:
                vibration[idx] += rng.uniform(2.0, 4.5)

            elif pattern == 2:
                cycle_time[idx] += rng.uniform(12, 24)

                throughput[idx] = max(
                    1,
                    throughput[idx] - rng.integers(5, 10),
                )

                total_count[idx] = throughput[idx]
                defect_count[idx] = min(
                    total_count[idx],
                    defect_count[idx] + 2,
                )
                good_count[idx] = total_count[idx] - defect_count[idx]

            else:
                defect_count[idx] = min(
                    total_count[idx],
                    defect_count[idx] + rng.integers(2, 5),
                )
                good_count[idx] = total_count[idx] - defect_count[idx]

        frames.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "machine_id": machine_id,
                    "temperature_c": temperature.round(3),
                    "vibration_mm_s": vibration.round(3),
                    "cycle_time_sec": cycle_time.round(3),
                    "throughput_units": throughput,
                    "total_count": total_count,
                    "good_count": good_count,
                    "defect_count": defect_count,
                    "machine_status": "RUNNING",
                    "ground_truth_anomaly": labels,
                }
            )
        )

    return pd.concat(
        frames,
        ignore_index=True,
    ).sort_values(
        ["machine_id", "timestamp"]
    ).reset_index(drop=True)
