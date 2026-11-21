"""Live demos for Academy Module 3 (vehicle dynamics). Simple, stated teaching models, plus
the real lap simulator for the last chapter."""
from dataclasses import replace

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
import tyre_physics as TP
from academy_widgets import circuit_picker
from charts import dress
from style import stat_strip

G = 9.81


def weight_transfer_calc():
    c1, c2, c3 = st.columns(3)
    mass = c1.slider("Mass with driver and fuel (kg)", 760, 920, 820, step=5, key="w31_m")
    h = c1.slider("Centre of gravity height (m)", 0.20, 0.45, 0.28, step=0.01, key="w31_h")
    track = c2.slider("Track width (m)", 1.40, 1.80, 1.60, step=0.01, key="w31_t")
    base = c2.slider("Wheelbase (m)", 3.0, 3.7, 3.6, step=0.05, key="w31_wb")
    lat = c3.slider("Cornering (g)", 0.0, 5.0, 3.0, step=0.1, key="w31_lat")
    lon = c3.slider("Braking (−) or accelerating (+) (g)", -5.0, 2.0, 0.0, step=0.1, key="w31_lon")
    front = 0.45
    W = mass * G
    d_lat = mass * lat * G * h / track            # total load moved to the outside wheels
    d_lon = mass * lon * G * h / base             # positive moves load to the rear
    fl = W * front / 2 - d_lat / 2 * front - d_lon / 2
    fr = W * front / 2 + d_lat / 2 * front - d_lon / 2
    rl = W * (1 - front) / 2 - d_lat / 2 * (1 - front) + d_lon / 2
    rr = W * (1 - front) / 2 + d_lat / 2 * (1 - front) + d_lon / 2
    loads = np.maximum([fl, fr, rl, rr], 0)
    even = W / 4
    grip_now = sum(TP.mu_at(l) * l for l in loads)
    grip_even = 4 * TP.mu_at(even) * even
    names = ["Front inside", "Front outside", "Rear inside", "Rear outside"]
    df = pd.DataFrame({"Wheel": names, "Load (N)": loads.round(0)})
    st.altair_chart(dress(alt.Chart(df).mark_bar(cornerRadius=4, color="#e10600").encode(
        x=alt.X("Wheel:N", sort=names, title=None, axis=alt.Axis(labelAngle=0)), y="Load (N):Q",
        tooltip=["Wheel", "Load (N)"])).properties(height=240), use_container_width=True)
    stat_strip([
        ("Load moved sideways", f"{d_lat:,.0f} N", f"{d_lat / W:.0%} of the car's weight", True),
        ("Load moved front to rear", f"{d_lon:+,.0f} N", "negative means onto the front", False),
        ("Grip lost to the transfer", f"{1 - grip_now / grip_even:.1%}", "from tyre load sensitivity", False),
    ])
    if loads.min() == 0:
        st.caption("A wheel has lifted: all its load is gone. Real cars have downforce too, which this leaves out.")
    else:
        st.caption("Without downforce, which adds load at speed. 45 % of the weight on the front axle.")


def understeer_demo():
    c1, c2 = st.columns(2)
    front = c1.slider("Weight on the front axle (%)", 35, 55, 45, key="w32_f") / 100
    cf = c1.slider("Front tyre cornering stiffness (kN/rad)", 100, 300, 200, step=5, key="w32_cf") * 1000
    cr = c2.slider("Rear tyre cornering stiffness (kN/rad)", 100, 300, 220, step=5, key="w32_cr") * 1000
    radius = c2.slider("Corner radius (m)", 30, 300, 100, step=5, key="w32_r")
    mass, wheelbase = 800, 3.6
    # Understeer gradient K (rad per m/s^2) of the bicycle model
    K = mass * ((1 - front) / cf - front / cr)
    speeds = np.linspace(10, 90, 81)
    delta = np.degrees(wheelbase / radius + K * speeds ** 2 / radius)
    df = pd.DataFrame({"Speed (km/h)": speeds * 3.6, "Steering needed (°)": delta,
                       "Neutral car": np.degrees(wheelbase / radius)})
    line = alt.Chart(df).mark_line(color="#e10600", strokeWidth=3).encode(x="Speed (km/h):Q", y="Steering needed (°):Q")
    neutral = alt.Chart(df).mark_line(color="#8a8a96", strokeDash=[5, 4]).encode(x="Speed (km/h):Q", y="Neutral car:Q")
    st.altair_chart(dress(line + neutral).properties(height=260), use_container_width=True)
    label = "understeers" if K > 1e-5 else "oversteers" if K < -1e-5 else "is neutral"
    extra = ""
    if K < 0:
        v_crit = np.sqrt(wheelbase / -K) * 3.6
        extra = f" It becomes unstable above about {v_crit:.0f} km/h."
    st.caption(f"This car {label}: as it goes faster round the same corner, the driver needs "
               f"{'more' if K > 0 else 'less'} steering than a neutral car (dashed).{extra}")


def camber_demo():
    c1, c2 = st.columns(2)
    static = c1.slider("Static camber (°, negative leans the top inwards)", -5.0, 1.0, -3.0, step=0.25, key="w34_c")
    roll = c2.slider("Body roll in the corner (°)", 0.0, 3.0, 1.0, step=0.1, key="w34_r")
    gain = 0.6                         # camber gained per degree of roll by the suspension geometry
    outside = static + roll * (1 - gain)
    camber = np.linspace(-6, 3, 181)
    grip = np.exp(-((camber + 2.5) / 3.0) ** 2)          # a tyre likes about -2.5° when loaded
    df = pd.DataFrame({"Camber (°)": camber, "Grip (share of best)": grip})
    curve = alt.Chart(df).mark_line(color="#8a8a96", strokeWidth=2).encode(x="Camber (°):Q", y="Grip (share of best):Q")
    dot = alt.Chart(pd.DataFrame({"Camber (°)": [outside], "Grip (share of best)": [float(np.exp(-((outside + 2.5) / 3.0) ** 2))]})).mark_point(
        filled=True, size=160, color="#e10600").encode(x="Camber (°):Q", y="Grip (share of best):Q")
    st.altair_chart(dress(curve + dot).properties(height=240), use_container_width=True)
    st.caption(f"The outside tyre, which does most of the work, runs at {outside:.1f}° in the corner: "
               f"{float(np.exp(-((outside + 2.5) / 3.0) ** 2)):.0%} of its best grip. Illustrative curve, not a real tyre.")


def quarter_car():
    c1, c2, c3 = st.columns(3)
    k = c1.slider("Spring (kN/m)", 50, 600, 250, step=10, key="w35_k") * 1000
    c = c2.slider("Damper (kN·s/m)", 1, 40, 8, step=1, key="w35_c") * 1000
    m = c3.slider("Mass on this corner (kg)", 150, 300, 200, step=5, key="w35_m")
    wn = np.sqrt(k / m)
    zeta = c / (2 * np.sqrt(k * m))
    t = np.linspace(0, 0.6, 600)
    # Response of the body to a 20 mm step (a kerb)
    if zeta < 1:
        wd = wn * np.sqrt(1 - zeta ** 2)
        x = 1 - np.exp(-zeta * wn * t) * (np.cos(wd * t) + zeta / np.sqrt(1 - zeta ** 2) * np.sin(wd * t))
    else:                                              # overdamped: no bounce, a slow creep
        r1 = -wn * (zeta - np.sqrt(max(zeta ** 2 - 1, 0.0)))
        x = 1 - np.exp(r1 * t)
    df = pd.DataFrame({"Time (s)": t, "Body movement (mm)": 20 * x})
    st.altair_chart(dress(alt.Chart(df).mark_line(color="#e10600", strokeWidth=3).encode(
        x="Time (s):Q", y="Body movement (mm):Q")).properties(height=240), use_container_width=True)
    stat_strip([
        ("Natural frequency", f"{wn / (2 * np.pi):.1f} Hz", "road cars about 1–1.5 Hz", True),
        ("Damping ratio", f"{zeta:.2f}", "0.6–0.8 settles fastest without bouncing", False),
        ("Overshoot", f"{max(0.0, x.max() - 1):.0%}", "how far past the bump it goes", False),
    ])


def ride_height_demo():
    folder = circuit_picker("w36_circuit", default="Silverstone")
    h = st.slider("Ride height (mm)", 10, 60, 35, step=1, key="w36_h",
                  help="An illustrative floor: downforce rises as it gets closer to the track, then stalls.")
    heights = np.arange(10, 61)
    # Illustrative aero map: more downforce closer to the ground, a stall below about 20 mm
    def factor(x):
        return 1.0 + 0.012 * (40 - x) - 0.35 * np.exp(-((x - 10) / 7.0) ** 2)
    df = pd.DataFrame({"Ride height (mm)": heights, "Downforce (× normal)": factor(heights)})
    curve = alt.Chart(df).mark_line(color="#8a8a96", strokeWidth=2).encode(x="Ride height (mm):Q", y="Downforce (× normal):Q")
    dot = alt.Chart(pd.DataFrame({"Ride height (mm)": [h], "Downforce (× normal)": [factor(h)]})).mark_point(
        filled=True, size=160, color="#e10600").encode(x="Ride height (mm):Q", y="Downforce (× normal):Q")
    st.altair_chart(dress(curve + dot).properties(height=220), use_container_width=True)
    base = A.calibrated(folder)
    t0 = A.run_car(folder, A.car_key(base))["lap_time"]
    t1 = A.run_car(folder, A.car_key(replace(base, downforce_scale=float(factor(h)) / float(factor(40)))))["lap_time"]
    stat_strip([("Downforce", f"{factor(h) / factor(40):.0%}", "of the car at 40 mm", True),
                ("Lap time change", f"{t1 - t0:+.3f}s", "on the lap simulator, everything else the same", False)])
    st.caption("Running lower adds downforce, until the floor stalls and the car starts to bounce. Teams run as "
               "low as the floor, the plank wear rules and the bouncing allow. The shape here is illustrative.")


def diff_demo():
    lat = st.slider("Cornering (g)", 0.0, 4.0, 2.0, step=0.1, key="w37_lat")
    lock = st.slider("Diff locking (0 = open, 1 = fully locked)", 0.0, 1.0, 0.5, step=0.05, key="w37_lock")
    rear_load = 800 * G * 0.55
    shift = min(rear_load, 800 * lat * G * 0.28 / 1.6 * 0.55)
    inner = max(0.0, (rear_load - shift) / 2)          # inside rear wheel
    outer = (rear_load + shift) / 2                    # outside rear wheel
    mu = 1.7
    open_drive = 2 * mu * inner                        # an open diff sends equal torque: the weak wheel limits
    locked_drive = mu * (inner + outer)
    drive = open_drive + lock * (locked_drive - open_drive)
    stat_strip([
        ("Open diff", f"{open_drive / 1000:.1f} kN", "limited by the inside wheel", False),
        ("Fully locked", f"{locked_drive / 1000:.1f} kN", "both wheels' grip, but it fights turning", False),
        ("Your setting", f"{drive / 1000:.1f} kN", "of drive force out of the corner", True),
    ])
    st.caption("Before tyre grip is shared with cornering. A locked diff gives more traction but pushes the car "
               "straight on, so F1 diffs vary the locking through the corner: open on entry, locked on exit.")


def ackermann_demo():
    c1, c2 = st.columns(2)
    radius = c1.slider("Corner radius (m)", 10, 200, 30, step=1, key="w38_r")
    pct = c2.slider("Ackermann (%)", -50, 100, 30, step=5, key="w38_p",
                    help="100% = perfect Ackermann (inside wheel turns more); 0% = parallel; below 0 = anti-Ackermann.")
    wb, tw = 3.6, 1.6
    inner_ack = np.degrees(np.arctan(wb / (radius - tw / 2)))
    outer = np.degrees(np.arctan(wb / (radius + tw / 2)))
    inner = outer + pct / 100 * (inner_ack - outer)
    stat_strip([("Outside wheel", f"{outer:.2f}°", "steering angle", False),
                ("Inside wheel", f"{inner:.2f}°", f"perfect Ackermann would be {inner_ack:.2f}°", True),
                ("Difference", f"{inner - outer:+.2f}°", "toe-out in the corner", False)])
    st.caption("At low speed, perfect Ackermann lets both wheels roll without scrubbing. At racing speeds the "
               "outside tyre does most of the work and both run at slip angles, so many F1 cars use little "
               "Ackermann or even anti-Ackermann.")


def build_lapsim():
    folder = circuit_picker("w39_circuit", default="Monaco")
    sim = A.run_car(folder, A.car_key(A.calibrated(folder)))
    step = st.radio("Show", ["1. Corner limit", "2. + Forward pass", "3. + Backward pass", "4. The lap"],
                    horizontal=True, key="w39_step")
    n = len(sim["s"])
    k = max(1, n // 700)
    s = sim["s"][::k]
    series = [("Corner limit", np.minimum(sim["corner_limit"] * 3.6, 400)[::k], "#2b6cff")]
    if step[0] >= "2":
        series.append(("Forward pass (accelerating)", sim["forward"][::k] * 3.6, "#1fd6a0"))
    if step[0] >= "3":
        series.append(("Backward pass (braking)", sim["backward"][::k] * 3.6, "#e8b33a"))
    if step[0] >= "4":
        series.append(("The lap: the lowest of all", sim["speed_kmh"][::k], "#e10600"))
    df = pd.concat([pd.DataFrame({"Distance (m)": s, "Speed (km/h)": v, "Curve": name}) for name, v, _ in series])
    st.altair_chart(dress(alt.Chart(df).mark_line(strokeWidth=2).encode(
        x=alt.X("Distance (m):Q", scale=alt.Scale(nice=False)), y=alt.Y("Speed (km/h):Q", scale=alt.Scale(domain=[0, 410])),
        color=alt.Color("Curve:N", scale=alt.Scale(domain=[n_ for n_, _, _ in series], range=[c for _, _, c in series]),
                        legend=alt.Legend(orient="top", title=None)))).properties(height=300), use_container_width=True)
    st.caption(f"Lap time {A.lap_str(sim['lap_time'])}. The corner limit is capped at 400 km/h on the chart: on "
               "straights it is effectively infinite.")
