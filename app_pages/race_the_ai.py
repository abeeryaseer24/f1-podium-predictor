"""Race the AI Driver: drive the calibrated car round a real circuit against a driver learned from real laps."""
import json

import numpy as np
import streamlit as st

import ai_driver as AD
import app_sim as A
from drive_game import drive, game_data
from style import stat_strip
from ui_kit import section


@st.cache_data(ttl=86400)
def report():
    return json.loads(AD.REPORT_FILE.read_text(encoding="utf-8"))


@st.cache_data(ttl=86400, max_entries=40)
def ai_lap(folder):
    path = AD.LAPS_DIR / f"{folder}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


folder = A.pick_race("race_ai")
lap = ai_lap(folder)
if lap is None:
    st.info("The AI driver hasn't driven this circuit yet. Pick another, or come back after the next update.")
    st.stop()
track = A.get_track(folder)
car = A.calibrated(folder)

stat_strip([
    ("AI driver", A.lap_str(lap["ai_lap"]), "learned from real laps, never trained here", True),
    ("Real fastest lap", A.lap_str(lap["real_lap"]), "of the race", False),
    ("Perfect physics", A.lap_str(lap["sim_lap"]), "the simulator on the tyres' exact limit", False),
])

drive(game_data(track, car, lap, []), dark=st.session_state.dark)
st.caption("Teal is the AI driver and gold the real fastest lap, both as ghosts. Same car for everyone: the "
           "simulator's car calibrated to this race. The braking guide turns the road amber, then red, where "
           "at your current speed you'd already need to be braking for what's ahead. Overcook a corner and you "
           "run wide and lose speed. Tap the page first if the keys don't respond.")

# ---------- how the AI driver drives this circuit ----------
section("How the AI driver drives here", "Its speed all the way round, against the real lap and the simulator "
        "driving on the exact limit. This circuit was left out when it learned.")
s = np.asarray(lap["s"])
st.altair_chart(A.speed_chart([("Real lap", "#e8b33a", s, np.asarray(lap["real_kmh"])),
                               ("AI driver", "#27f4d2", s, np.asarray(lap["ai_kmh"])),
                               ("Perfect physics", "#8a8a96", s, np.asarray(lap["sim_kmh"]))],
                              marks=A.corner_marks(folder, track)), use_container_width=True)

r = report()
section("How good is the AI driver, honestly?", f"Each of {r['circuits']} circuits was driven by a version trained "
        f"without it ({r['races']} races in all).")
stat_strip([
    ("Closer to the real lap", f"{r['closer_share']:.0%}", "of races, than the simulator's own trace", True),
    ("Speed trace off by", f"{r['ai_rmse']:.1f} km/h", f"typical gap to the real lap (simulator {r['sim_rmse']:.1f})", False),
    ("Lap time", f"{r['ai_gap']:+.2f} s", "typical gap to the real lap", False),
])
st.caption("How it learned: at every 4 m of each race's fastest lap it saw the situation (the simulator's speed, "
           "the tyres' limit, how far to the next braking zone, the corners coming up) and the speed the real driver "
           "chose. A gradient-boosted tree model copies that choice (behaviour cloning), and the simulator's physics "
           "turn it into a lap the car can actually drive. What it can't do: it learned from one lap per race, from "
           "position data four times a second, on a point-mass car with no tyre wear or traffic, so it copies "
           "the typical driver of that lap, not any one driver's style.")
