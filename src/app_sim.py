"""What the Simulator pages need from the lap simulator, cached for the app.

Nothing here does physics: it loads tracks and calibrations, runs lapsim.py, and shapes
the results for the 3D view and the charts.
"""
import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import lapsim
from app_data import get_corners, get_prepared_races, get_race_file
from charts import dress, theme
from ui_kit import FAIR, GOOD, POOR

MODE_COLOURS = {"throttle": GOOD, "corner": FAIR, "brake": POOR}
MODE_LEGEND = [("Full throttle", GOOD), ("Cornering on the limit", FAIR), ("Braking", POOR)]
SIM_COLOUR = "#e10600"
THREE_EVERY = 2                  # every 2nd simulated point (8 m apart) goes to the 3D view

# Minimum car + driver weight by season, from the FIA technical regulations
MIN_MASS = {2022: 798, 2023: 798, 2024: 798, 2025: 800, 2026: 768}


@st.cache_data(ttl=600)
def get_calibration():
    return lapsim.load_calibration()


@st.cache_data(ttl=600)
def usable_races():
    """Prepared races whose lap could be calibrated, newest first, with a label for each."""
    races = get_prepared_races()
    cal = get_calibration()
    if races.empty:
        return races
    races = races[races["folder"].map(lambda f: bool(cal.get(f, {}).get("usable")))]
    return races.sort_values(["season", "round"], ascending=False)


@st.cache_data(ttl=3600)
def get_track(folder):
    return lapsim.build_track(get_race_file(folder, "track"))


@st.cache_data(ttl=3600, max_entries=200)
def run_car(folder, car_fields):
    """Simulate one lap. car_fields is a tuple of (name, value) so it can be cached."""
    car = lapsim.Car(**dict(car_fields))
    return lapsim.simulate(car, get_track(folder))


def car_key(car):
    return tuple(sorted(lapsim.asdict(car).items()))


def calibrated(folder):
    return lapsim.calibrated_car(folder, get_calibration())


def pick_race(key):
    """Season + circuit dropdowns. Returns the chosen folder (or stops the page)."""
    races = usable_races()
    if races.empty:
        st.info("No circuits are ready for the simulator yet. The robot adds them after each race.")
        st.stop()
    seasons = sorted(races["season"].unique().tolist(), reverse=True)
    left, right = st.columns(2)
    season = left.selectbox("Season", seasons, key=f"{key}_season")
    in_season = races[races["season"] == season].sort_values("round")
    names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
    return right.selectbox("Circuit", list(names), index=len(names) - 1, format_func=names.get,
                           key=f"{key}_race")


def season_of(folder):
    return int(folder.split("_")[0])


def three_track(track, colours, legend):
    """The track arrays the 3D view needs, thinned to keep the page light."""
    k = THREE_EVERY
    return {"x": track.x[::k], "y": track.y[::k], "z": track.z[::k],
            "colours": list(np.asarray(colours)[::k]), "legend": legend, "length": track.length}


def sim_car(sim, name, colour):
    """A simulated lap as a car for the 3D view."""
    return {"name": name, "colour": colour,
            "t": np.r_[sim["time"], sim["lap_time"]],
            "s": np.r_[sim["s"], sim["s"][-1] + (sim["s"][1] - sim["s"][0])]}


def corner_labels(folder, track):
    """Corner labels positioned on the thinned 3D track."""
    out = [{"text": "START / FINISH", "i": 0, "kind": "start"}]
    for c in get_corners(folder):
        s = track.source_s[c["i"]] if c["i"] < len(track.source_s) else np.nan
        if np.isnan(s):
            continue
        out.append({"text": c["label"], "i": int(s / track.length * len(track.s)) // THREE_EVERY,
                    "kind": "corner"})
    return out


def corner_marks(folder, track):
    """(label, metres from the line) for every corner, in lap order."""
    marks = []
    for c in get_corners(folder):
        if c["i"] < len(track.source_s) and not np.isnan(track.source_s[c["i"]]):
            marks.append((c["label"], float(track.source_s[c["i"]]) % track.length))
    return sorted(marks, key=lambda m: m[1])


def speed_chart(series, marks=None, height=300):
    """Speed against distance for several laps. series = [(name, colour, s, speed_kmh)]."""
    text, grid, muted = theme()
    rows = []
    for name, colour, s, v in series:
        step = max(1, len(s) // 600)
        rows.append(pd.DataFrame({"Distance (m)": np.asarray(s)[::step],
                                  "Speed (km/h)": np.round(np.asarray(v)[::step], 1), "Lap": name}))
    data = pd.concat(rows)
    scale = alt.Scale(domain=[n for n, *_ in series], range=[c for _, c, *_ in series])
    lines = alt.Chart(data).mark_line(strokeWidth=2).encode(
        x=alt.X("Distance (m):Q", scale=alt.Scale(nice=False)),
        y=alt.Y("Speed (km/h):Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Lap:N", scale=scale, legend=alt.Legend(orient="top", title=None)),
        tooltip=["Lap", "Distance (m)", "Speed (km/h)"])
    layers = [lines]
    if marks:
        m = pd.DataFrame({"Distance (m)": [s for _, s in marks], "Corner": [l for l, _ in marks]})
        layers.append(alt.Chart(m).mark_rule(strokeDash=[2, 4], color=muted, opacity=.5)
                      .encode(x="Distance (m):Q"))
        layers.append(alt.Chart(m).mark_text(dy=-6, fontSize=10, color=muted, baseline="bottom")
                      .encode(x="Distance (m):Q", y=alt.value(0), text="Corner:N"))
    return dress(alt.layer(*layers)).properties(height=height)


def kmh(v):
    return f"{v:.0f} km/h"


def lap_str(seconds):
    minutes, secs = divmod(float(seconds), 60)
    return f"{int(minutes)}:{secs:06.3f}"


def car_facts(car, rho=1.2):
    """Plain-words numbers about a car: power in hp, downforce at 250 km/h, drag at 300."""
    v250, v300 = 250 / 3.6, 300 / 3.6
    downforce = 0.5 * rho * car.cza * v250 ** 2
    drag = 0.5 * rho * car.cxa * v300 ** 2
    return {
        "hp": car.power_kw * 1.341,
        "downforce_kn": downforce / 1000,
        "downforce_x_weight": downforce / (car.mass * lapsim.G),
        "drag_kn": drag / 1000,
        "lat_g_slow": car.grip,
    }


def calibration_json(folder):
    return json.dumps(get_calibration().get(folder, {}), indent=1)
