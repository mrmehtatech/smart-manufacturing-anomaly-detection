"""Optional MySQL persistence helpers."""
import os
import pandas as pd

def get_connection():
    """Create a MySQL connection from environment variables."""
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError("Install mysql-connector-python to enable MySQL support.") from exc
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_manufacturing"),
    )

def save_readings(frame: pd.DataFrame) -> int:
    """Persist readings using parameterized SQL statements."""
    connection = get_connection()
    cursor = connection.cursor()
    query = """
        INSERT INTO sensor_readings
        (machine_id, observed_at, temperature_c, vibration_mm_s, cycle_time_sec,
         throughput_units, total_count, good_count, defect_count, machine_status, source_type)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
        temperature_c=VALUES(temperature_c),
        vibration_mm_s=VALUES(vibration_mm_s),
        cycle_time_sec=VALUES(cycle_time_sec),
        throughput_units=VALUES(throughput_units),
        total_count=VALUES(total_count),
        good_count=VALUES(good_count),
        defect_count=VALUES(defect_count)
    """
    records = []
    for row in frame.itertuples():
        records.append((
            row.machine_id, row.timestamp.to_pydatetime().replace(tzinfo=None),
            float(row.temperature_c), float(row.vibration_mm_s), float(row.cycle_time_sec),
            int(row.throughput_units), int(row.total_count), int(row.good_count),
            int(row.defect_count), str(row.machine_status), "simulator"
        ))
    try:
        cursor.executemany(query, records)
        connection.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        connection.close()
