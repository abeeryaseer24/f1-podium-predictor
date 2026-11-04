"""Ghost Lap Duel: two drivers' fastest laps, head to head."""
import streamlit as st

from app_data import get_duel, get_fastest_laps, get_prepared_races, get_race_info
from duel import lap_time


races = get_prepared_races()
if races.empty:
    st.info("No events prepared yet. The robot adds a few every 3 hours.")
    st.stop()

# ---------- pick the event and session ----------
c1, c2, c3 = st.columns(3)
season = c1.selectbox("Season", sorted(races["season"].unique().tolist(), reverse=True))
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Event", list(names), format_func=names.get)
session = c3.selectbox("Session", ["Qualifying", "Race"])

info = get_race_info(folder)
drivers = {d["number"]: d for d in info["drivers"]}

with st.spinner("Loading lap times..."):
    try:
        laps = get_fastest_laps(folder, session)
    except Exception as error:
        st.error(f"Couldn't load this session: {error}")
        st.stop()
if len(laps) < 2:
    st.info("Not enough laps in this session for a duel.")
    st.stop()

# ---------- pick the two drivers (fastest first) ----------
times = dict(zip(laps["driver_number"].astype(int), laps["lap_duration"]))


def label(number):
    d = drivers.get(number, {})
    name = (d.get("name") or "").title()
    return f"{d.get('code') or number} · {name} · {lap_time(times[number])}"


order = list(times)
left, right = st.columns(2)
num_a = left.selectbox("Driver 1", order, index=0, format_func=label)
num_b = right.selectbox("Driver 2", order, index=1, format_func=label)
if num_a == num_b:
    st.info("Pick two different drivers.")
    st.stop()

# ---------- the duel ----------
with st.spinner("Comparing the two laps..."):
    try:
        duel = get_duel(folder, session, num_a, num_b)
    except Exception as error:
        st.error(f"Couldn't compare these laps: {error}")
        st.stop()

code_a = drivers.get(num_a, {}).get("code") or str(num_a)
code_b = drivers.get(num_b, {}).get("code") or str(num_b)

m1, m2, m3 = st.columns(3)
m1.metric(f"{code_a} lap", lap_time(duel["lap_a"]))
m2.metric(f"{code_b} lap", lap_time(duel["lap_b"]))
m3.metric("Gap", f"{abs(duel['gap']):.3f} s")

st.markdown(f"**{duel['verdict']}**")
wins_a = int((duel["segments"]["winner"] == "a").sum())
total = len(duel["segments"])
st.caption(f"{code_a} was faster in {wins_a} of {total} mini-sectors, "
           f"{code_b} in the other {total - wins_a}.")