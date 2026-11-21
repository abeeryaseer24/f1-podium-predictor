"""Car DNA: what each car was good at, measured from its fastest race lap."""
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from charts import dress
from style import stat_strip
from ui_kit import heat, section, versus

FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "car_dna.csv"
# trait: (column, label, unit, higher is better, from the model?)
TRAITS = [
    ("top_speed", "Top speed", "km/h", True, False),
    ("slow_kmh", "Slow corners", "km/h", True, False),
    ("medium_kmh", "Medium corners", "km/h", True, False),
    ("fast_kmh", "Fast corners", "km/h", True, False),
    ("traction_g", "Traction", "g", True, False),
    ("downforce_kn", "Downforce", "kN", True, True),
    ("drag_kn", "Drag", "kN", False, True),
    ("power_kw", "Power", "kW", True, True),
]


@st.cache_data(ttl=600)
def load():
    if not FILE.exists():
        return pd.DataFrame()
    d = pd.read_csv(FILE)
    d[["season", "round"]] = d[["season", "round"]].astype(int)
    return d


dna = load()
if dna.empty:
    st.info("Car DNA is measured after each race. Nothing has been measured yet.")
    st.stop()

seasons = sorted(dna["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons)
races = dna[dna["season"] == season][["round", "race_name", "folder"]].drop_duplicates().sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in races.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get)
race = dna[dna["folder"] == folder].sort_values("lap_time").reset_index(drop=True)
traits = [t for t in TRAITS if race[t[0]].notna().any()]

best = race.iloc[0]
first = lambda col, hi: race.loc[race[col].idxmax() if hi else race[col].idxmin()]
stat_strip([
    ("Fastest lap", best["team"], f"{best['driver']} · {best['lap_time']:.3f}s", True),
    ("Highest top speed", first("top_speed", True)["team"], f"{race['top_speed'].max():.0f} km/h", False),
    ("Best in slow corners", first("slow_kmh", True)["team"] if race["slow_kmh"].notna().any() else "–",
     f"{race['slow_kmh'].max():.0f} km/h at the apex" if race["slow_kmh"].notna().any() else "", False),
    ("Most downforce (model)", first("downforce_kn", True)["team"], f"{race['downforce_kn'].max():.1f} kN at 250 km/h", False),
])

# ---------- the grid ----------
section("Every car, every trait", "Each cell is that car's number; the colour ranks it within this race "
        "(green best, red worst). Teams are in order of their fastest lap.")
cells = {}
for col, label, unit, higher, _ in traits:
    values = race[col]
    lo, hi = values.min(), values.max()
    for _, r in race.iterrows():
        if pd.isna(r[col]):
            continue
        score = (r[col] - lo) / ((hi - lo) or 1)
        text = f"{r[col]:.2f}" if unit == "g" else f"{r[col]:.1f}" if unit == "kN" else f"{r[col]:.0f}"
        cells[(r["team"], label)] = (text, score if higher else 1 - score)
heat(race["team"].tolist(), [t[1] for t in traits], cells, legend=("Worst here", "Best here"),
     row_colours=dict(zip(race["team"], race["colour"])),
     column_titles={label: f"{label} ({unit}){' · from the lap simulator' if model else ''}"
                    for _, label, unit, _, model in traits})
counts = race.iloc[0]
st.caption(f"This circuit has {int(counts['corners_slow'])} slow, {int(counts['corners_medium'])} medium and "
           f"{int(counts['corners_fast'])} fast corners by apex speed (slow under 130 km/h, fast over 210). "
           "Downforce, drag and power come from fitting the lap simulator to each car's lap; the rest is straight from the data.")

# ---------- two cars ----------
section("Two cars side by side")
teams = race["team"].tolist()
c3, c4 = st.columns(2)
left = c3.selectbox("Car", teams, index=0, key=f"dna_l_{folder}")
right = c4.selectbox("Against", [t for t in teams if t != left], index=0, key=f"dna_r_{folder}")
L, R = race[race["team"] == left].iloc[0], race[race["team"] == right].iloc[0]
rows = []
for col, label, unit, higher, _ in traits:
    if pd.isna(L[col]) or pd.isna(R[col]):
        continue
    fmt = (lambda v: f"{v:.2f} {unit}") if unit == "g" else (lambda v: f"{v:.1f} {unit}") if unit == "kN" \
        else (lambda v: f"{v:.0f} {unit}")
    lv, rv = (L[col], R[col]) if higher else (1 / L[col], 1 / R[col])     # longer bar = better
    rows.append((label + ("" if higher else " (less is better)"), lv, rv, fmt(L[col]), fmt(R[col])))
versus(left, right, rows, left_colour=L["colour"], right_colour=R["colour"] if R["colour"] != L["colour"] else "#8a8a96")

# ---------- through the season ----------
section("Through the season", "Each car against the best car at every race, so tracks with very different "
        "speeds can sit on one chart. Zero is the best car that weekend.")
pick = st.selectbox("Trait", [t[1] for t in traits if not t[4]], key="dna_trend")
col, label, unit, higher, _ = next(t for t in TRAITS if t[1] == pick)
season_rows = dna[dna["season"] == season].copy()
ref = season_rows.groupby("folder")[col].transform("max" if higher else "min")
season_rows["gap"] = (season_rows[col] - ref) if higher else (ref - season_rows[col])
team_colours = season_rows.groupby("team")["colour"].last()
chart = alt.Chart(season_rows.dropna(subset=["gap"])).mark_line(point=True, strokeWidth=2).encode(
    x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1)),
    y=alt.Y("gap:Q", title=f"Behind the best car ({unit})"),
    color=alt.Color("team:N", scale=alt.Scale(domain=list(team_colours.index), range=list(team_colours.values)),
                    legend=alt.Legend(orient="bottom", title=None, columns=5)),
    tooltip=["race_name", "team", "driver", alt.Tooltip(f"{col}:Q", format=".2f", title=label),
             alt.Tooltip("gap:Q", format=".2f", title="Behind the best")])
st.altair_chart(dress(chart).properties(height=340), use_container_width=True)

with st.expander("How Car DNA is measured, and what it can't tell you"):
    st.markdown("""
- **One lap per team per race:** the team's fastest race lap, from whichever driver set it, with full
  telemetry from OpenF1. It's usually set late in the race on light fuel, but tyres, traffic and DRS
  still vary from car to car.
- **Corners are found once per race** on the reference lap and sorted by apex speed, so every car is
  measured at the same places.
- **Traction** is the average acceleration out of slow corners up to 200 km/h.
- **Downforce, drag and power** come from fitting the lap simulator (a point-mass model) to each lap. They
  trade off against each other in the fit, so read them as a consistent comparison between cars in the same
  race, not as wind-tunnel numbers.
- **Across circuits,** compare positions against the best car, not raw numbers: every track has its own speeds
  and wing levels.
""")
