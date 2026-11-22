"""Setup Garage: change the car and see what it does to the lap, corner by corner."""
from dataclasses import replace

import numpy as np
import streamlit as st

import app_sim as A
from sim3d import lap_view
from style import stat_strip
from ui_kit import diverge, section

folder = A.pick_race("garage")
track = A.get_track(folder)
base = A.calibrated(folder)
min_mass = A.MIN_MASS.get(A.season_of(folder), 798)
base_fuel = float(np.clip(round(base.mass - min_mass), 0, 110))
COMPOUNDS = {"Soft": 1.04, "Medium": 1.00, "Hard": 0.97}

# Widget keys include the circuit, so every circuit starts from its own calibrated car
k = lambda name: f"garage_{folder}_{name}"
DEFAULTS = {"wing": round(base.wing, 2), "power": int(round(base.power_kw)), "fuel": int(base_fuel),
            "compound": "Medium", "grip": round(base.grip, 2), "ls": base.load_sensitivity,
            "down": 100, "drag": 100}
for name, value in DEFAULTS.items():
    st.session_state.setdefault(k(name), value)

PRESETS = {
    "Calibrated car": {},
    "Lowest drag": {"wing": 0.0},
    "Most downforce": {"wing": 1.0},
    "Full tank": {"fuel": 110},
    "+10% aero upgrade": {"down": 110},
}
st.caption("Start from a preset, or move the sliders.")
cols = st.columns(len(PRESETS))
for col, (label, change) in zip(cols, PRESETS.items()):
    if col.button(label, key=k(f"preset_{label}"), use_container_width=True):
        for name, value in {**DEFAULTS, **change}.items():
            st.session_state[k(name)] = value
        st.rerun()

left, right = st.columns(2)
with left:
    wing = st.slider("Wing level", 0.0, 1.0, step=0.01, key=k("wing"),
                     help="0 is a Monza-style low-drag wing, 1 is Monaco-style maximum downforce. "
                          "More wing means more downforce AND more drag.")
    power = st.slider("Power at the wheels (kW)", 300, 1000, step=1, key=k("power"))
    fuel = st.slider("Fuel on board (kg)", 0, 110, step=1, key=k("fuel"),
                     help=f"The car and driver weigh at least {min_mass} kg in {A.season_of(folder)}.")
with right:
    compound = st.radio("Tyres", list(COMPOUNDS), horizontal=True, key=k("compound"),
                        help="Illustrative only: softer tyres grip more but wear faster. "
                             "The real gaps change from track to track.")
    with st.expander("Advanced"):
        grip = st.slider("Tyre grip (friction coefficient)", 1.0, 3.0, step=0.01, key=k("grip"))
        ls = st.slider("Load sensitivity", 0.0, 0.3, step=0.01, key=k("ls"),
                       help="How much less grip each extra newton of load adds. 0 means grip "
                            "grows in step with load.")
        down = st.slider("Downforce (% of the wing level's)", 70, 130, step=1, key=k("down"))
        drag = st.slider("Drag (% of the wing level's)", 70, 130, step=1, key=k("drag"))

def build(wing, power, fuel, compound, grip, ls, down, drag):
    if [wing, power, fuel, compound, grip, ls, down, drag] == list(DEFAULTS.values()):
        return base                     # untouched sliders: exactly the calibrated car
    return replace(base, wing=wing, power_kw=float(power), mass=float(min_mass + fuel),
                   grip=grip * COMPOUNDS[compound], load_sensitivity=ls,
                   downforce_scale=down / 100, drag_scale=drag / 100)


car = build(wing, power, fuel, compound, grip, ls, down, drag)
yours = A.run_car(folder, A.car_key(car))
# The reference is the car the sliders start at, so an untouched setup shows no difference
ref = A.run_car(folder, A.car_key(build(*DEFAULTS.values())))


def signed(x, unit):
    x = round(x)
    return f"{x:+d} {unit}" if x else f"±0 {unit}"


delta = yours["lap_time"] - ref["lap_time"]
tone = "faster" if delta < -0.0005 else "slower" if delta > 0.0005 else "the same"
stat_strip([
    ("Your lap", A.lap_str(yours["lap_time"]), f"{abs(delta):.3f}s {tone}" if tone != "the same" else "same as the calibrated car", True),
    ("Calibrated car", A.lap_str(ref["lap_time"]), "the starting point", False),
    ("Top speed", A.kmh(yours["speed_kmh"].max()), signed(yours['speed_kmh'].max() - ref['speed_kmh'].max(), "km/h"), False),
    ("Slowest corner", A.kmh(yours["speed_kmh"].min()), signed(yours['speed_kmh'].min() - ref['speed_kmh'].min(), "km/h"), False),
])

# ---------- 3D: your car against the calibrated one ----------
section("Your car against the calibrated car", "Both cars start together. The track is coloured "
        "by where your car is gaining (green) or losing (red) speed.")
diff = yours["speed_kmh"] - ref["speed_kmh"]
colours = np.where(diff > 1, "#1fd6a0", np.where(diff < -1, "#e4544a", "#8a8a96"))
ghost = "#f5f5f7" if st.session_state.dark else "#15151e"
lap_view(A.three_track(track, colours, [("You're faster", "#1fd6a0"), ("You're slower", "#e4544a"),
                                        ("About the same", "#8a8a96")]),
         [A.sim_car(yours, "YOU", A.SIM_COLOUR), A.sim_car(ref, "BASE", ghost)],
         labels=A.corner_labels(folder, track), dark=st.session_state.dark, height=520)

# ---------- corner by corner ----------
marks = A.corner_marks(folder, track)
if len(marks) >= 2:
    section("Corner by corner", "Time gained or lost on the way into each corner, in thousandths "
            "of a second.")
    edges = [m for _, m in marks] + [track.length]
    names = [f"Into {label}" for label, _ in marks] + ["To the line"]
    t_y = np.interp(edges, np.r_[yours["s"], track.length], np.r_[yours["time"], yours["lap_time"]])
    t_r = np.interp(edges, np.r_[ref["s"], track.length], np.r_[ref["time"], ref["lap_time"]])
    seg_y, seg_r = np.diff(np.r_[0, t_y]), np.diff(np.r_[0, t_r])
    rows = [{"name": name, "sub": "", "value": round((r - y) * 1000), "colour": "#1fd6a0" if r > y else "#e4544a"}
            for name, y, r in zip(names, seg_y, seg_r)]
    if any(r["value"] for r in rows):
        diverge(rows, left_label="Slower (ms)", right_label="Faster (ms)")
    else:
        st.caption("No difference yet: change something above.")

# ---------- speed trace ----------
section("Speed all the way round", "Your car against the calibrated car.")
st.altair_chart(A.speed_chart([("You", A.SIM_COLOUR, yours["s"], yours["speed_kmh"]),
                               ("Calibrated", "#8a8a96", ref["s"], ref["speed_kmh"])],
                              marks=marks), use_container_width=True)

# ---------- sensitivities ----------
section("What each change is worth here", "Lap time for one small change at a time, from the "
        "car you have set up. Every circuit values these differently.")
changes = [
    ("10 kg lighter", replace(car, mass=car.mass - 10)),
    ("10 kW more power", replace(car, power_kw=car.power_kw + 10)),
    ("5% more downforce", replace(car, downforce_scale=car.downforce_scale * 1.05)),
    ("5% less drag", replace(car, drag_scale=car.drag_scale * 0.95)),
    ("1% more tyre grip", replace(car, grip=car.grip * 1.01)),
    ("Wing level +0.1", replace(car, wing=min(1.0, car.wing + 0.1))),
]
rows = []
for label, changed in changes:
    t = A.run_car(folder, A.car_key(changed))["lap_time"]
    gain = t - yours["lap_time"]
    rows.append({"name": label, "sub": f"{gain:+.3f}s a lap", "value": round(-gain * 1000),
                 "colour": "#1fd6a0" if gain < 0 else "#e4544a"})
diverge(rows, left_label="Slower (ms per lap)", right_label="Faster (ms per lap)")
st.caption("Each row starts from your current setup, so the numbers change as you move the sliders. "
           "The wing row is the classic trade: more downforce in the corners, more drag on the straights.")
