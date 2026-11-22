"""Classic Races: famous Grands Prix since 1996. Take control of one car's strategy and try to beat history."""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import classic as C
import race_engine as RE
from charts import dress
from style import stat_strip
from ui_kit import banner, board, section

RUNS = 400


@st.cache_data(ttl=86400, max_entries=20)
def race_for(key):
    return C.build(key)


@st.cache_data(ttl=86400, max_entries=300)
def run(key, plan_key, real_sc, extra_sc):
    race = race_for(key)
    starts = [l for l in race["sc_laps"] if l - 1 not in race["sc_laps"]] if real_sc else []
    race = {**race, "sc_rate": 0.6 if extra_sc else 0.0}
    strategies = {d: list(p) for d, p in plan_key} if plan_key else None
    pos = RE.simulate(race, runs=RUNS, strategies=strategies, force_sc_lap=starts, sc_enabled=extra_sc)
    return pos, RE.summary(race, pos)


keys = C.saved()
if not keys:
    st.info("The classic races haven't been downloaded yet.")
    st.stop()
key = st.selectbox("Classic race", keys[::-1], format_func=lambda k: C.CLASSICS[k]["title"], key="cr_race")
race = race_for(key)
L = race["laps"]
banner("🏁", C.CLASSICS[key]["title"], C.CLASSICS[key]["story"])

c1, c2, c3 = st.columns(3)
winner = next(d for d, p in race["real_pos"].items() if p == 1)
order = race["drivers"]
who = c1.selectbox("Take control of", order, index=order.index(winner),
                   format_func=lambda d: f"{race['who'][d]['code']} · {race['who'][d]['name']} ({race['who'][d]['team']})",
                   key=f"cr_who_{key}")
real_sc = c2.toggle("Real safety cars", value=True, key=f"cr_sc_{key}",
                    help="On: safety cars where they really happened (found in the lap times).")
extra_sc = c3.toggle("Random extra safety cars", value=False, key=f"cr_extra_{key}")

real_plan = race["strategies"][who]
real_stops = len(real_plan) - 1
options = sorted({real_stops, 0, 1, 2, 3})
stops = st.radio("Pit stops", options, index=options.index(real_stops), horizontal=True, key=f"cr_stops_{key}_{who}",
                 format_func=lambda k: f"{k} stop{'s' if k != 1 else ''}" + (" (real)" if k == real_stops else ""))
plan = list(real_plan)
if stops != real_stops or st.toggle("Choose the laps", key=f"cr_edit_{key}_{who}"):
    cols = st.columns(max(stops, 1))
    edges = np.linspace(0, L, stops + 2)[1:-1].round().astype(int)
    plan = []
    for k in range(stops):
        default = real_plan[k][1] if stops == real_stops else int(edges[k])
        lap = cols[k].number_input(f"Stop {k + 1} on lap", 2, L - 1, int(min(max(default, 2), L - 1)), key=f"cr_l_{key}_{who}_{stops}_{k}")
        plan.append(("MEDIUM", int(lap)))
    plan = sorted(plan, key=lambda x: x[1]) + [("MEDIUM", L)]
changed = plan != list(real_plan)

base_pos, base = run(key, None, real_sc, extra_sc)
your_pos, yours = run(key, ((who, tuple(plan)),) if changed else None, real_sc, extra_sc)
me = yours[yours["driver_number"] == who].iloc[0]
was = base[base["driver_number"] == who].iloc[0]
real = race["real_pos"].get(who)
beat = real and me["expected"] < real - 0.3
stat_strip([
    ("History", f"P{real}" if real else "DNF", f"{race['who'][who]['code']}'s real result", False),
    ("Your plan", f"P{me['expected']:.1f}", f"average finish · wins {me['win']:.0%}", True),
    ("Real plan, replayed", f"P{was['expected']:.1f}", f"wins {was['win']:.0%}", False),
    ("Verdict", f"Wins {me['win']:.0%}" if real == 1 else
     ("You beat history" if beat else ("As history" if real and abs(me["expected"] - real) <= 0.3 else "History wins")),
     "they won for real: how often does your plan win?" if real == 1 else "against the real finishing position", False),
])

section("The field over 400 replays", "With your plan for the car you control. Pills run green to red down each column.")
rows = [{"colour": r.colour, "cells": [(f"{r.code} · {r['name']}", r.team), f"P{int(r.grid)}" if r.grid and r.grid < 99 else "pit lane",
                                       (r.expected, f"P{r.expected:.1f}"), (r.win, f"{r.win:.0%}"), (r.podium, f"{r.podium:.0%}"),
                                       f"P{int(r.real)}" if pd.notna(r.real) else "DNF"]}
        for _, r in yours.head(12).iterrows()]
board([("Driver", "label"), ("Grid", "num"), ("Average finish", "scale_low"), ("Win", "bar"), ("Podium", "bar"),
       ("Real result", "num")], rows, ranked=True)

j = order.index(who)
def dist(pos, name):
    p = pos[:, j]
    s = pd.Series(p[p > 0]).value_counts().reindex(range(1, 11), fill_value=0) / len(p)
    return pd.DataFrame({"Position": s.index, "Share": s.values, "Plan": name})
df = pd.concat([dist(base_pos, "Real plan"), dist(your_pos, "Your plan")]) if changed else dist(base_pos, "Real plan")
st.altair_chart(dress(alt.Chart(df).mark_bar(cornerRadius=3).encode(
    x=alt.X("Position:O", axis=alt.Axis(labelAngle=0)), y=alt.Y("Share:Q", axis=alt.Axis(format="%")), xOffset="Plan:N",
    color=alt.Color("Plan:N", scale=alt.Scale(domain=["Real plan", "Your plan"], range=["#8a8a96", race["who"][who]["colour"]]),
                    legend=alt.Legend(orient="top", title=None)))).properties(height=230), use_container_width=True)
st.caption(f"Rebuilt from Jolpica's lap times: pace, pit loss {race['pit_loss']:.1f} s, "
           f"{'refuelling-era fuel per stint' if race['refuel'] else 'fuel and tyre wear'} and safety cars on laps "
           f"{', '.join(map(str, race['sc_laps'][:8])) or 'none'}. No tyre compounds or weather in this data.")
