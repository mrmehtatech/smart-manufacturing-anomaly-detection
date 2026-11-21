"""Authenticated Streamlit dashboard with admin-managed signup approval."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
from config import SETTINGS
from src.pipeline import run_pipeline
from src.analysis import calculate_kpis, evaluate_simulated_labels
from dashboard.authentication import require_login, render_admin_approval_panel

st.set_page_config(page_title="Smart Manufacturing Monitor", layout="wide")
user = require_login()

st.title("Smart Manufacturing | Anomaly Monitoring")
st.caption("Synthetic demonstration data • Decision support only • No physical machine control")

with st.sidebar:
    st.header("Controls")
    st.caption(f"Signed in as: {user.get('full_name', user['user_id'])} ({user['role']})")
    if st.button("Logout", use_container_width=True):
        st.session_state.pop("auth_user", None)
        st.rerun()
    if user["role"] == "admin":
        st.divider()
        render_admin_approval_panel(user["user_id"])
    st.divider()
    if st.button("Generate / refresh simulation", use_container_width=True):
        st.cache_data.clear()
        data, _ = run_pipeline()
        st.success(f"Generated {len(data)} observations.")
    st.caption("For a fresh run, execute the pipeline or use the refresh button.")

@st.cache_data(ttl=15)
def load_or_run():
    if SETTINGS.processed_path.exists():
        return pd.read_csv(SETTINGS.processed_path, parse_dates=["timestamp"])
    frame, _ = run_pipeline()
    return frame

try:
    data = load_or_run()
except Exception as exc:
    st.error(f"Could not load dashboard data: {exc}")
    st.info("Run `python main.py` from the project root, then refresh this page.")
    st.stop()

if data.empty:
    st.warning("No observations are available.")
    st.stop()

data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
kpis = calculate_kpis(data)
cols = st.columns(5)
cols[0].metric("Observations", f"{kpis['records']:,}")
cols[1].metric("Machines", kpis["machines"])
cols[2].metric("Units produced", f"{kpis['total_units']:,}")
cols[3].metric("Anomaly flags", f"{kpis['anomaly_count']:,}")
cols[4].metric("Defect rate", f"{kpis['defect_rate']:.1%}" if kpis["defect_rate"] is not None else "N/A")

machine_options = ["All"] + sorted(data["machine_id"].dropna().unique().tolist())
selected_machine = st.selectbox("Machine", machine_options)
view = data if selected_machine == "All" else data[data["machine_id"] == selected_machine]

left, right = st.columns(2)
with left:
    fig = px.line(view, x="timestamp", y="temperature_c", color="machine_id", title="Machine temperature over time")
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.line(view, x="timestamp", y="vibration_mm_s", color="machine_id", title="Machine vibration over time")
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    fig = px.scatter(view, x="cycle_time_sec", y="throughput_units", color="is_anomaly", symbol="is_anomaly", title="Cycle time vs throughput")
    st.plotly_chart(fig, use_container_width=True)
with right:
    counts = view["is_anomaly"].value_counts().rename_axis("is_anomaly").reset_index(name="count")
    fig = px.bar(counts, x="is_anomaly", y="count", title="Normal vs flagged observations")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Anomaly events")
events = view[view["is_anomaly"]].sort_values("timestamp", ascending=False)
display_cols = [c for c in ["timestamp", "machine_id", "temperature_c", "vibration_mm_s", "cycle_time_sec", "spc_flag", "iforest_flag", "iforest_decision_score"] if c in events.columns]
st.dataframe(events[display_cols], use_container_width=True, hide_index=True)

st.subheader("Evaluation against simulator labels")
metrics = evaluate_simulated_labels(view)
if metrics:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Precision", f"{metrics['precision']:.3f}")
    metric_cols[1].metric("Recall", f"{metrics['recall']:.3f}")
    metric_cols[2].metric("F1-score", f"{metrics['f1_score']:.3f}")
    metric_cols[3].metric("False-positive rate", f"{metrics['false_positive_rate']:.3f}")
    st.caption("These metrics use the simulator's hidden event labels for evaluation only; labels are not model inputs.")
else:
    st.info("No evaluation labels are available in this dataset.")

st.download_button("Download processed data", data=view.to_csv(index=False).encode("utf-8"), file_name="processed_manufacturing_readings.csv", mime="text/csv")
