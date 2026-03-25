import streamlit as st
import pandas as pd
import random
import time

st.set_page_config(page_title="Welding Simulator", layout="wide")

# ---------- SESSION ----------
defaults = {
    "running": False,
    "paused": False,
    "data": [],
    "start_time": None,
    "elapsed": 0,
    "last_data_time": 0,
    "pause_start": 0,
    "total_pause": 0,
    "final_time": 0
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- UI ----------
st.title("🔥 Welding Simulator")

length = st.number_input("Joint Length (mm)", value=100)

c1, c2, c3 = st.columns(3)

# START
if c1.button("▶ Start"):
    st.session_state.running = True
    st.session_state.paused = False
    st.session_state.data = []
    st.session_state.start_time = time.time()
    st.session_state.total_pause = 0
    st.session_state.elapsed = 0
    st.session_state.last_data_time = 0

    # ✅ ADD FIRST ENTRY AT 0 sec
    st.session_state.data.append({
        "Time (sec)": 0,
        "Voltage (V)": round(random.uniform(25, 27), 2),
        "Current (A)": round(random.uniform(120, 130), 2)
    })

# PAUSE / RESUME
if c2.button("⏸ Pause / Resume"):
    if st.session_state.running:
        if not st.session_state.paused:
            st.session_state.paused = True
            st.session_state.pause_start = time.time()
        else:
            st.session_state.paused = False
            st.session_state.total_pause += time.time() - st.session_state.pause_start

# STOP
if c3.button("⏹ Stop"):
    st.session_state.running = False
    st.session_state.final_time = st.session_state.elapsed

# ---------- TIMER ----------
if st.session_state.running and not st.session_state.paused:
    st.session_state.elapsed = int(
        time.time() - st.session_state.start_time - st.session_state.total_pause
    )

st.metric("⏱ Stopwatch (sec)", st.session_state.elapsed)

# ---------- DATA GENERATION (FIXED) ----------
if st.session_state.running and not st.session_state.paused:

    # generate every 5 seconds using difference (NOT modulo)
    if st.session_state.elapsed - st.session_state.last_data_time >= 5:

        st.session_state.last_data_time = st.session_state.elapsed

        st.session_state.data.append({
            "Time (sec)": st.session_state.elapsed,
            "Voltage (V)": round(random.uniform(25, 27), 2),
            "Current (A)": round(random.uniform(120, 130), 2)
        })

# ---------- ALWAYS SHOW TABLE ----------
st.markdown("---")
st.subheader("📋 Welding Data")

if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No data yet")

# ---------- FINAL RESULT ----------
if not st.session_state.running and len(st.session_state.data) > 0:

    st.markdown("---")
    st.header("📊 Final Result")

    df = pd.DataFrame(st.session_state.data)

    total_time = st.session_state.final_time
    avg_v = df["Voltage (V)"].mean()
    avg_a = df["Current (A)"].mean()

    travel_speed = length / total_time if total_time != 0 else 1
    heat = (avg_v * avg_a * 60) / (travel_speed * 1000)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Time", total_time)
    c2.metric("Avg V", round(avg_v, 2))
    c3.metric("Avg A", round(avg_a, 2))
    c4.metric("🔥 Heat", round(heat, 2))

# ---------- AUTO REFRESH ----------
if st.session_state.running:
    time.sleep(1)
    st.rerun()