"""Live demos for Academy Modules 11-12 (race engineering and strategy)."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import race_engine as RE
from academy_widgets import circuit_picker
from charts import dress
from style import stat_strip

COMP = {"Soft": (0.0, 0.10), "Medium": (0.45, 0.06), "Hard": (0.85, 0.035)}   # offset s, wear s/lap (illustrative)


def _stint(comp, n, deg_scale):
    off, wear = COMP[comp]
    ages = np.arange(n)
    return float((off + wear * deg_scale * ages).sum())


def stop_calculator():
    c1, c2, c3 = st.columns(3)
    laps = c1.slider("Race laps", 44, 78, 57, key="w12_laps")
    loss = c2.slider("Pit loss (s)", 15, 32, 22, key="w12_loss")
    deg = c3.slider("How hard the track is on tyres (×)", 0.5, 2.5, 1.0, step=0.1, key="w12_deg")
    best = {}
    one = []
    for k in range(8, laps - 7):
        for a, b in (("Medium", "Hard"), ("Hard", "Medium"), ("Soft", "Hard")):
            t = _stint(a, k, deg) + _stint(b, laps - k, deg) + loss
            one.append({"Stop lap": k, "Plan": "One stop", "Time lost (s)": t, "Tyres": f"{a}–{b}"})
    two = []
    for k1 in range(6, laps - 12, 2):
        for k2 in range(k1 + 6, laps - 5, 2):
            for seq in (("Medium", "Hard", "Medium"), ("Soft", "Hard", "Soft"), ("Medium", "Medium", "Soft")):
                t = _stint(seq[0], k1, deg) + _stint(seq[1], k2 - k1, deg) + _stint(seq[2], laps - k2, deg) + 2 * loss
                two.append({"Stop lap": k1, "Plan": "Two stops", "Time lost (s)": t, "Tyres": "–".join(seq), "k2": k2})
    o, t2 = pd.DataFrame(one), pd.DataFrame(two)
    bo, bt = o.loc[o["Time lost (s)"].idxmin()], t2.loc[t2["Time lost (s)"].idxmin()]
    winner = "One stop" if bo["Time lost (s)"] <= bt["Time lost (s)"] else "Two stops"
    stat_strip([("Fastest plan", winner, f"by {abs(bo['Time lost (s)'] - bt['Time lost (s)']):.1f} s", True),
                ("Best one-stop", f"lap {int(bo['Stop lap'])}", bo["Tyres"], False),
                ("Best two-stop", f"laps {int(bt['Stop lap'])} and {int(bt['k2'])}", bt["Tyres"], False)])
    curve = o.groupby("Stop lap")["Time lost (s)"].min().reset_index()
    st.altair_chart(dress(alt.Chart(curve).mark_line(color="#e10600", strokeWidth=3).encode(
        x="Stop lap:Q", y=alt.Y("Time lost (s):Q", title="Time lost to tyres + stop (s)", scale=alt.Scale(zero=False))
    )).properties(height=220), use_container_width=True)
    st.caption("One-stop race time against the lap of the stop (best tyre order at each lap). Illustrative compound "
               "speeds and wear; harder-wearing tracks push towards more stops.")


def undercut():
    c1, c2, c3 = st.columns(3)
    gap = c1.slider("Gap to the car ahead (s)", 0.5, 4.0, 1.8, step=0.1, key="w123_gap")
    fresh = c2.slider("New tyres faster than old by (s/lap)", 0.5, 3.0, 1.5, step=0.1, key="w123_fresh")
    outlap = c3.slider("Out-lap time lost on cold tyres (s)", 0.0, 1.5, 0.6, step=0.1, key="w123_out")
    # You stop on lap 0; the rival stops one lap later. You gain `fresh` on your out-lap (minus warm-up),
    # then the rival loses its own out-lap warm-up after its stop.
    gain = fresh - outlap + outlap * 0.5          # your fresh-tyre lap, and the rival's cold out-lap
    left = gap - gain
    stat_strip([("Time gained by stopping first", f"{gain:.1f} s", "one lap on fresh tyres", True),
                ("Gap after both stops", f"{left:+.1f} s", "negative: you're ahead", False),
                ("Undercut", "works" if left < 0 else "fails", "if pit stops are equal", False)])
    st.caption("A simplified one-lap undercut. Real undercuts also depend on traffic, the pit-stop times, and how "
               "quickly each car's tyres warm up.")


def sc_saving():
    loss = st.slider("Normal pit loss (s)", 15, 32, 22, key="w124_loss")
    stat_strip([("Pit loss under a safety car", f"{loss * 0.55:.1f} s", "the field is slow, so you lose less", True),
                ("Saving", f"{loss * 0.45:.1f} s", "a 'cheap' stop", False),
                ("Under a VSC", f"{loss * 0.7:.1f} s", "a smaller saving", False)])
    st.caption("Using the same factors as our strategist and race engine (55 % of a normal stop under a safety car, "
               "70 % under a virtual safety car).")


def monte_carlo():
    folder = circuit_picker("w126_circuit", default="Silverstone")
    runs = st.select_slider("Number of simulated races", [10, 25, 50, 100, 200, 400, 800], value=50, key="w126_runs")
    race = RE.build(folder)
    rows = []
    for seed in range(3):
        table = RE.summary(race, RE.simulate(race, runs=runs, seed=seed))
        for _, r in table.head(4).iterrows():
            rows.append({"Driver": r["code"], "Win chance": r["win"], "Repeat": f"Run {seed + 1}"})
    df = pd.DataFrame(rows)
    st.altair_chart(dress(alt.Chart(df).mark_bar(cornerRadius=3).encode(
        x=alt.X("Driver:N", axis=alt.Axis(labelAngle=0)), y=alt.Y("Win chance:Q", axis=alt.Axis(format="%")),
        xOffset="Repeat:N", color=alt.Color("Repeat:N", scale=alt.Scale(range=["#e10600", "#e8b33a", "#27c2f4"]),
                                            legend=alt.Legend(orient="top", title=None)))).properties(height=240),
        use_container_width=True)
    st.caption("The same race simulated three times with different random numbers. With few races the answers disagree; "
               "with hundreds they settle. That's how Monte Carlo strategy tools turn randomness into odds.")


def long_run():
    c1, c2 = st.columns(2)
    laps = c1.slider("Long-run length (laps)", 8, 25, 15, key="w112_laps")
    fuel_kg = c2.slider("Fuel at the start of the run (kg)", 20, 110, 80, key="w112_fuel")
    burn = 1.7
    effect = 0.03
    t = np.arange(laps)
    fuel = fuel_kg - burn * t
    raw = 92 + effect * fuel + 0.06 * t
    corrected = raw - effect * fuel
    df = pd.DataFrame({"Lap": np.r_[t, t] + 1, "Lap time (s)": np.r_[raw, corrected + effect * fuel_kg],
                       "Times": ["As driven"] * laps + ["With fuel taken out"] * laps})
    st.altair_chart(dress(alt.Chart(df).mark_line(point=True, strokeWidth=2.5).encode(
        x="Lap:Q", y=alt.Y("Lap time (s):Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Times:N", scale=alt.Scale(range=["#8a8a96", "#e10600"]), legend=alt.Legend(orient="top", title=None))
    )).properties(height=220), use_container_width=True)
    st.caption(f"Burning {burn} kg a lap at about {effect} s per kg hides tyre wear: the driven times look flatter "
               "than the tyre really is. Engineers take the fuel out to see the true degradation.")
