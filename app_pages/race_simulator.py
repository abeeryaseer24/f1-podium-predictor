"""Race Simulator: replay a real Grand Prix hundreds of times, then change it."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import race_engine as RE
from app_data import get_prepared_races
from charts import dress
from style import stat_strip
from ui_kit import board, section

RUNS = 400
COMPOUNDS = ["SOFT", "MEDIUM", "HARD"]


@st.cache_data(ttl=3600, max_entries=40)
def race_for(folder):
    return RE.build(folder)


@st.cache_data(ttl=3600, max_entries=200)
def run(folder, strategy_key, force_sc, sc_on, pace_key):
    race = race_for(folder)
    strategies = {d: list(s) for d, s in strategy_key} if strategy_key else None
    pos = RE.simulate(race, runs=RUNS, strategies=strategies, force_sc_lap=force_sc or None, sc_enabled=sc_on,
                      pace_offsets=dict(pace_key) if pace_key else None)
    return pos, RE.summary(race, pos)


races = get_prepared_races()
seasons = sorted(races["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons, key="rs_season")
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get, key="rs_race")
race = race_for(folder)
L = race["laps"]
label = lambda d: f"{race['who'][d].get('code', d)} · {str(race['who'][d].get('name', '')).title()}"

st.caption("Built from this race's own laps, so it replays the race rather than predicting it. Change something "
           "and see how the result could have gone.")
c3, c4, c5 = st.columns(3)
sc_on = c3.toggle("Random safety cars", value=True, key="rs_sc", help=f"About {race['sc_rate']:.1f} per race at this circuit, from the data.")
force = c4.slider("Force a safety car on lap", 0, L - 3, 0, key=f"rs_force_{folder}", help="0 = no forced safety car.")
who = c5.selectbox("Change a driver", race["drivers"], format_func=label, key=f"rs_who_{folder}")

real = race["strategies"][who]
with st.expander(f"{race['who'][who].get('code', who)}'s strategy and pace", expanded=True):
    real_stops = len(real) - 1
    options = sorted({real_stops, 1, 2, 3})
    stops = st.radio("Pit stops", options, index=options.index(real_stops), horizontal=True, key=f"rs_stops_{folder}_{who}",
                     format_func=lambda k: f"{k} stop{'s' if k != 1 else ''}" + (" (real)" if k == real_stops else ""))
    edit = st.toggle("Choose the laps and tyres", value=stops != real_stops, key=f"rs_edit_{folder}_{who}_{stops}")
    plan = list(real)
    if edit or stops != real_stops:
        cols = st.columns(stops + 1)
        plan = []
        edges = np.linspace(0, L, stops + 2)[1:].round().astype(int)
        for k in range(stops + 1):
            ref = real[min(k, len(real) - 1)]
            default_end = ref[1] if stops == real_stops else int(edges[k])
            comp = cols[k].selectbox(f"Stint {k + 1} tyre", COMPOUNDS,
                                     index=COMPOUNDS.index(ref[0]) if ref[0] in COMPOUNDS else 1,
                                     key=f"rs_c_{folder}_{who}_{stops}_{k}")
            end = L if k == stops else cols[k].number_input("Pit on lap", 2, L - 1, int(min(max(default_end, 2), L - 1)),
                                                            key=f"rs_l_{folder}_{who}_{stops}_{k}")
            plan.append((comp, int(end)))
    pace = st.slider("Pace change (seconds per lap, negative is faster)", -0.6, 0.6, 0.0, step=0.05, key=f"rs_pace_{folder}_{who}")
    st.caption("Real strategy: " + " → ".join(f"{c.title()} to lap {e}" for c, e in real))

changed = plan != list(real)
base_pos, base_table = run(folder, None, force, sc_on, None)
your_pos, your_table = run(folder, ((who, tuple(plan)),) if changed else None, force, sc_on,
                           ((who, pace),) if pace else None)
j = race["drivers"].index(who)
fav = your_table.iloc[0]
real_winner = next((d for d, p in race["real_pos"].items() if p == 1), None)
mine = your_table[your_table["driver_number"] == who].iloc[0]
before = base_table[base_table["driver_number"] == who].iloc[0]
stat_strip([
    ("Favourite", fav["code"], f"wins {fav['win']:.0%} of {RUNS} races", True),
    ("Real winner", race["who"].get(real_winner, {}).get("code", "–") if real_winner else "–", f"{race['info']['race_name']} {race['info']['season']}", False),
    (f"{mine['code']}: expected finish", f"P{mine['expected']:.1f}", f"was P{before['expected']:.1f} with the real plan" if (changed or pace) else "with the real plan", False),
    ("Engine vs reality", f"{RE.agreement(base_table):.2f}", "rank agreement with the real result, real strategies", False),
])

section("Every driver over 400 races", "Sorted by average finish. Pills run green to red down each column.")
rows = [{"colour": r.colour, "cells": [(f"{r.code} · {str(r['name']).title()}", r.team),
                                       f"P{int(r.grid)}" if pd.notna(r.grid) else "–",
                                       (r.expected, f"P{r.expected:.1f}"), (r.win, f"{r.win:.0%}"), (r.podium, f"{r.podium:.0%}"),
                                       (r.dnf, f"{r.dnf:.0%}"), f"P{int(r.real)}" if pd.notna(r.real) else "–"]}
        for _, r in your_table.iterrows()]
board([("Driver", "label"), ("Grid", "num"), ("Average finish", "scale_low"), ("Win", "bar"), ("Podium", "bar"),
       ("Retire", "scale_low"), ("Real result", "num")], rows, ranked=True)

section(f"Where {mine['code']} finishes", "Share of the 400 races ending in each position, with the real plan and with yours.")
def dist(pos, name):
    p = pos[:, j]
    counts = pd.Series(p[p > 0]).value_counts(normalize=False).reindex(range(1, len(race["drivers"]) + 1), fill_value=0) / len(p)
    return pd.DataFrame({"Position": counts.index, "Share": counts.values, "Plan": name})
df = pd.concat([dist(base_pos, "Real plan"), dist(your_pos, "Your change")]) if (changed or pace) else dist(base_pos, "Real plan")
colour = race["who"][who].get("colour") or "#e10600"
chart = alt.Chart(df).mark_bar(cornerRadius=3).encode(
    x=alt.X("Position:O", axis=alt.Axis(labelAngle=0)), y=alt.Y("Share:Q", axis=alt.Axis(format="%")),
    xOffset="Plan:N", color=alt.Color("Plan:N", scale=alt.Scale(domain=["Real plan", "Your change"], range=["#8a8a96", colour]),
                                      legend=alt.Legend(orient="top", title=None)),
    tooltip=["Plan", "Position", alt.Tooltip("Share:Q", format=".0%")])
st.altair_chart(dress(chart).properties(height=260), use_container_width=True)
st.caption(f"Overtaking difficulty here: {race['difficulty']:.2f} (from how much a grid place costs at this circuit) · "
           f"pit loss {race['pit_loss']:.1f} s · no weather or tyre temperatures in this model.")
