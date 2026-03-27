import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
import pytz
from io import BytesIO


IST = pytz.timezone("Asia/Kolkata")

st.set_page_config(page_title="Welding Simulator", layout="wide")

# ---------- SESSION ----------
defaults = {
    "running": False,
    "paused": False,
    "data": [],
    "start_time": 0,
    "elapsed": 0,
    "last_data_time": 0,
    "pause_start": 0,
    "total_pause": 0,
    "final_time": 0,
    "joint_name": "Joint_1",
    "weld_type": "ROOT",
    "finished": False,
    "log": []
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- UI ----------
st.title("🔥 Welding Simulator")

col1, col2 = st.columns(2)

with col1:
    st.session_state.joint_name = st.text_input(
        "Joint Name",
        st.session_state.joint_name,
        disabled=st.session_state.running
    )

with col2:
    weld_options = ["ROOT", "HOT", "FILL", "CAP"]
    st.session_state.weld_type = st.selectbox(
        "Weld Type",
        weld_options,
        index=weld_options.index(st.session_state.weld_type),
        disabled=st.session_state.running
    )

length = st.number_input("Joint Length (mm)", value=100)

st.markdown(
    f"### 📍 Joint: `{st.session_state.joint_name}` | Weld Type: `{st.session_state.weld_type}`"
)

# ---------- BUTTONS ----------
c1, c2, c3, c4 = st.columns(4)

# START
if c1.button("▶ Start"):
    st.session_state.running = True
    st.session_state.paused = False
    st.session_state.finished = False
    st.session_state.data = []
    st.session_state.start_time = time.time()
    st.session_state.total_pause = 0
    st.session_state.elapsed = 0
    st.session_state.last_data_time = 0

    # reset log
    st.session_state.log = []
    st.session_state.log.append({
        "Event": "Start",
        "Time": datetime.now(IST).strftime("%H:%M:%S")
    })

    # first data at 0
    st.session_state.data.append({
        "Joint": st.session_state.joint_name,
        "Weld Type": st.session_state.weld_type,
        "Time (sec)": 0,
        "Voltage (V)": round(random.uniform(25, 27), 2),
        "Current (A)": round(random.uniform(120, 130), 2)
    })

# NEW JOINT
if c2.button("🔄 New Joint"):
    st.session_state.running = False
    st.session_state.paused = False
    st.session_state.data = []
    st.session_state.elapsed = 0
    st.session_state.final_time = 0
    st.session_state.finished = False
    st.session_state.log = []

# PAUSE / RESUME
if c3.button("⏸ Pause / Resume"):
    if st.session_state.running:
        if not st.session_state.paused:
            st.session_state.paused = True
            st.session_state.pause_start = time.time()

            st.session_state.log.append({
                "Event": "Pause",
                "Time": datetime.now(IST).strftime("%H:%M:%S")
            })

        else:
            st.session_state.paused = False
            st.session_state.total_pause += time.time() - st.session_state.pause_start

            st.session_state.log.append({
                "Event": "Resume",
                "Time": datetime.now(IST).strftime("%H:%M:%S")
            })

# FINISH
if c4.button("✅ Finish"):
    st.session_state.running = False
    st.session_state.final_time = st.session_state.elapsed
    st.session_state.finished = True

    st.session_state.log.append({
        "Event": "Finish",
        "Time": datetime.now(IST).strftime("%H:%M:%S")
    })
   

# ---------- STOPWATCH ----------
if st.session_state.running:
    if not st.session_state.paused:
        st.session_state.elapsed = int(
            time.time()
            - st.session_state.start_time
            - st.session_state.total_pause
        )

st.metric("⏱ Stopwatch (sec)", st.session_state.elapsed)

# ---------- DATA GENERATION ----------
if st.session_state.running and not st.session_state.paused:

    if st.session_state.elapsed - st.session_state.last_data_time >= 5:
        st.session_state.last_data_time = st.session_state.elapsed

        st.session_state.data.append({
            "Joint": st.session_state.joint_name,
            "Weld Type": st.session_state.weld_type,
            "Time (sec)": st.session_state.elapsed,
            "Voltage (V)": round(random.uniform(25, 27), 2),
            "Current (A)": round(random.uniform(120, 130), 2)
        })

# ---------- TABLE ----------
st.markdown("---")
st.subheader("📋 Welding Data")

if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(
        df[["Joint", "Weld Type", "Time (sec)", "Voltage (V)", "Current (A)"]],
        use_container_width=True
    )
else:
    st.info("No data yet")
# ---------- FINAL RESULT ----------
if st.session_state.finished and len(st.session_state.data) > 0:

    st.markdown("---")
    st.header(f"📊 Final Result - {st.session_state.joint_name}")

    df = pd.DataFrame(st.session_state.data)

    total_time = st.session_state.final_time
    avg_v = df["Voltage (V)"].mean()
    avg_a = df["Current (A)"].mean()

    travel_speed = length / total_time if total_time != 0 else 1
    heat = (avg_v * avg_a * 60) / (travel_speed * 1000)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Time", total_time)
    c2.metric("Avg Voltage", round(avg_v, 2))
    c3.metric("Avg Current", round(avg_a, 2))
    c4.metric("🔥 Heat Input (kJ/mm)", round(heat, 2))

    # ---------- TIMELINE ----------
    st.markdown("---")
    st.subheader("🕒 Welding Timeline")

    log_df = pd.DataFrame(st.session_state.log)
    st.dataframe(log_df, use_container_width=True)

    # ---------- EXCEL EXPORT ----------
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:

        # SUMMARY
        summary_df = pd.DataFrame({
            "Metric": [
                "Joint Name",
                "Weld Type",
                "Total Time (sec)",
                "Avg Voltage",
                "Avg Current",
                "Heat Input (kJ/mm)"
            ],
            "Value": [
                st.session_state.joint_name,
                st.session_state.weld_type,
                total_time,
                round(avg_v, 2),
                round(avg_a, 2),
                round(heat, 2)
            ]
        })

        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # DATA
        df[["Time (sec)", "Voltage (V)", "Current (A)"]].to_excel(
            writer, sheet_name="Welding Data", index=False
        )

        # TIMELINE
        if not log_df.empty:
            log_df.to_excel(writer, sheet_name="Timeline", index=False)
        else:
            pd.DataFrame({"Info": ["No timeline data"]}).to_excel(
                writer, sheet_name="Timeline", index=False
            )

    st.download_button(
        "⬇ Download Excel Report",
        buffer.getvalue(),
        file_name=f"{st.session_state.joint_name}_report.xlsx"
    )
# ---------- AUTO REFRESH ----------
if st.session_state.running:
    time.sleep(1)
    st.rerun()
