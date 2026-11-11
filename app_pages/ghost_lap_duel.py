"""Ghost Lap Duel: two drivers' fastest laps, head to head, with the telemetry."""
import streamlit as st

from app_data import get_duel, get_fastest_laps, get_prepared_races, get_race_file, get_race_info
from duel import lap_time
from duel_charts import delta_chart, gear_chart, pedals_chart, speed_chart, top_speeds
from track3d import duel_view


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

# ---------- the 3D duel ----------
track = get_race_file(folder, "track")
driver_a = drivers.get(num_a, {"code": code_a})
driver_b = drivers.get(num_b, {"code": code_b})
duel_view(track, duel, driver_a, driver_b, dark=st.session_state.dark)
if driver_a.get("team") and driver_a.get("team") == driver_b.get("team"):
    shade = "white" if st.session_state.dark else "black"
    st.caption(f"Teammates share a team colour, so {code_b} is shown in {shade}.")

# ---------- the telemetry ----------

colour_a = driver_a.get("colour") or "#e10600"
colour_b = driver_b.get("colour") or "#27f4d2"
if colour_a.lower() == colour_b.lower():                 # teammates: tell them apart
    colour_b = "#f5f5f7" if st.session_state.dark else "#15151e"

st.subheader("Where the time went")
st.caption("The gap building up round the lap. Above the line means "
           f"{code_a} is losing time to {code_b}; below it means {code_a} is gaining. "
           "The dotted lines are the corners, and hovering one names it.")
st.altair_chart(delta_chart(duel, code_a, code_b, colour_a, colour_b),
                width="stretch", theme=None)

fastest = top_speeds(duel, code_a, code_b)
if fastest:
    row = st.columns(len(fastest))
    for column, (code, speed) in zip(row, fastest.items()):
        column.metric(f"{code} top speed", f"{speed:.0f} km/h")

st.subheader("Speed")
st.caption("Both laps, all the way round. The dips are the corners: a higher dip means "
           "more speed carried through, and a later dip means braking later.")
st.altair_chart(speed_chart(duel, code_a, code_b, colour_a, colour_b),
                width="stretch", theme=None)

st.subheader("Throttle and brake")
pedals = pedals_chart(duel, code_a, code_b, colour_a, colour_b)
if isinstance(pedals, tuple):
    throttle, braking = pedals
    st.caption("Throttle as a percentage. The marks underneath are every point on the "
               "lap where the brake was on, so you can see who braked earlier.")
    st.altair_chart(throttle, width="stretch", theme=None)
    st.altair_chart(braking, width="stretch", theme=None)
else:
    st.caption("Throttle as a percentage. No brake data was recorded for these laps.")
    st.altair_chart(pedals, width="stretch", theme=None)

gears = gear_chart(duel, code_a, code_b, colour_a, colour_b)
if gears is not None:
    st.subheader("Gear")
    st.caption("Which gear the car was in. A driver a gear higher through a corner is "
               "carrying more speed; a flat top-gear stretch is the straight.")
    st.altair_chart(gears, width="stretch", theme=None)

st.caption("Telemetry is recorded about four times a second, so very short inputs can "
           "fall between two readings. Both laps are lined up on the start/finish line, "
           "not on the clock, so the comparison is fair even if one driver started their "
           "lap earlier.")