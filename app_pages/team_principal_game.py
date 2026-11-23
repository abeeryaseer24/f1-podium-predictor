"""Team Principal: run a team through a real season against the other teams' real pace."""
import altair as alt
import pandas as pd
import streamlit as st

import team_principal as T
from charts import dress
from style import stat_strip, team_info
from ui_kit import GOLD, GOOD, POOR, banner, board, section

KEY = "tp_game"
MODE_TEXT = {"push": "Push (−0.08%, 11% retirements)", "normal": "Normal (5.5% retirements)", "save": "Save (+0.06%, 3% retirements)"}


@st.cache_data(ttl=6 * 3600)
def world(season):
    return T.setup(season)


@st.cache_data(ttl=6 * 3600)
def real(season):
    return T.real_points(season)


def code(w, d):
    return "Reserve" if d == "RESERVE" else w["drivers"][d]["code"]


g = st.session_state.get(KEY)

# ---------- set up ----------
if g is None:
    c1, c2 = st.columns(2)
    season = c1.selectbox("Season", T.seasons(), key="tp_season")
    w = world(season)
    team = c2.selectbox("Your team", sorted(w["lineup"]), format_func=lambda t: team_info(t)[0], key=f"tp_team_{season}")
    section("Sign your drivers", f"Two drivers within ${T.SALARY_BUDGET:.0f}M. Skill is each driver's pace against their "
                                 "teammate that season; a team you sign from runs a reserve.")
    pool = sorted(w["drivers"].values(), key=lambda d: -d["skill"])
    default = [d for d in w["lineup"][team] if d in w["drivers"]]
    chosen = st.multiselect("Drivers", [d["driver"] for d in pool], default=default, max_selections=2,
                            format_func=lambda k: f"{w['drivers'][k]['code']} · {team_info(w['drivers'][k]['team'])[0]} · "
                                                  f"${w['drivers'][k]['salary']:.0f}M", key=f"tp_drivers_{season}_{team}")
    board([("Driver", "label"), ("Skill", "delta"), ("Salary", "num")],
          [{"colour": team_info(d["team"])[1], "cells": [(d["code"], team_info(d["team"])[0]),
                                                         (round(d["skill"] * 1000), f"{d['skill']:+.2f}%"), f"${d['salary']:.0f}M"]}
           for d in pool[:12]])
    cost = sum(w["drivers"][d]["salary"] for d in chosen)
    st.caption(f"Your two drivers cost ${cost:.0f}M of ${T.SALARY_BUDGET:.0f}M.")
    if st.button("Start the season", type="primary", disabled=len(chosen) != 2 or cost > T.SALARY_BUDGET):
        st.session_state[KEY] = T.new_game(w, team, chosen)
        st.session_state["tp_season_now"] = season
        st.rerun()
    if cost > T.SALARY_BUDGET:
        st.warning("Over the salary budget.")
    st.stop()

season = st.session_state["tp_season_now"]
w = world(season)
team_name, colour = team_info(g["team"])
n_blocks = -(-len(w["rounds"]) // T.BLOCK)
pos = T.position(g) if g["points"] else None
stat_strip([
    ("Team", team_name, f"{season} · {' & '.join(code(w, d) for d in g['drivers'])}", True),
    ("Constructors'", f"P{pos}" if pos else "—", f"{g['points'].get(g['team'], 0)} points", False),
    ("Car", f"{g['car']:.2f}% off", f"started {g['start']:.2f}%", False),
    ("Development left", f"${T.DEV_BUDGET - g['spent']:.0f}M", f"wind tunnel {T.atr(pos) if pos else 1:.0%}", False),
])

if g["log"]:
    for n in g["log"][-1]["notes"]:
        st.caption("• " + n)

# ---------- the turn ----------
if not g["over"]:
    rounds = w["rounds"][g["block"] * T.BLOCK:(g["block"] + 1) * T.BLOCK]
    section(f"Turn {g['block'] + 1} of {n_blocks}: {rounds[0]['race_name'].replace(' Grand Prix', '')} to "
            f"{rounds[-1]['race_name'].replace(' Grand Prix', '')}", "Your decisions for the next block of races.")
    c1, c2 = st.columns(2)
    left = T.DEV_BUDGET - g["spent"]
    spend = c1.slider("Development spend ($M)", 0.0, float(left), float(min(15.0, left)), 1.0, key=f"tp_spend_{g['block']}",
                      help="Builds a package for next turn. Spending a lot at once gives less per dollar.")
    mode = c2.radio("Engine mode", list(T.MODES), index=1, format_func=MODE_TEXT.get, key=f"tp_mode_{g['block']}")
    upgrade = "now"
    if g["factory"] > 0:
        upgrade = st.radio(f"The {g['factory']:.2f}% package from the factory",
                           ["now", "test"], horizontal=True, key=f"tp_upg_{g['block']}",
                           format_func={"now": f"Fit it now ({T.MISS:.0%} chance it doesn't correlate)",
                                        "test": "Test it first (safe, fitted next turn)"}.get)
    if st.button(f"Race the next {len(rounds)}", type="primary", key=f"tp_go_{g['block']}"):
        st.session_state[KEY] = T.play_block(w, dict(g), spend, upgrade, mode)
        st.rerun()
else:
    real_pts = real(season)
    real_pos = list(real_pts).index(g["team"]) + 1 if g["team"] in real_pts else None
    ahead = real_pos and pos < real_pos
    banner("🏆" if pos == 1 else "🏁", f"{team_name} finish P{pos} in the constructors' championship",
           f"with {g['points'][g['team']]} points. In reality they were P{real_pos} with {real_pts.get(g['team'], 0):.0f}."
           if real_pos else f"with {g['points'][g['team']]} points.",
           GOLD if pos == 1 else (GOOD if ahead or pos == real_pos else POOR))
    st.caption(f"${T.DEV_BUDGET - g['spent']:.0f}M unspent goes to next year's car: a head start of about "
               f"{T.next_year(g):.2f}% of lap time.")
    if st.button("New season", type="primary"):
        del st.session_state[KEY]
        st.rerun()

# ---------- what happened ----------
if g["results"]:
    last = g["results"][-T.BLOCK:]
    section("Your races", "Where your two cars finished.")
    rows = []
    for r in last:
        mine = [x for x in r["order"] if x["team"] == g["team"]]
        winner = r["order"][0]
        rows.append({"colour": colour, "cells": [(r["race_name"].replace(" Grand Prix", ""), f"Round {r['round']}")] +
                     [("DNF" if x["dnf"] else f"P{x['pos']}") + f" {code(w, x['driver'])}" for x in mine] +
                     [f"{code(w, winner['driver'])} ({team_info(winner['team'])[0]})", (sum(x["pts"] for x in mine), f"{sum(x['pts'] for x in mine)}")]})
    board([("Race", "label"), ("Car 1", "text"), ("Car 2", "text"), ("Winner", "text"), ("Points", "bar")], rows)

    c1, c2 = st.columns([1, 1])
    with c1:
        section("Constructors' championship")
        board([("Team", "label"), ("Points", "bar")],
              [{"colour": team_info(t)[1], "cells": [(team_info(t)[0], "you" if t == g["team"] else ""), (p, f"{p}")]}
               for t, p in T.standings(g)], ranked=True)
    with c2:
        section("Your car against the real one", "% off the quickest car, race by race (lower is quicker).")
        done = [r["round"] for r in g["results"]]
        cars, pace_by_block = [], {}
        for e in g["log"]:
            pace_by_block[e["block"]] = e["car"]
        for i, rr in enumerate(done):
            block = i // T.BLOCK
            cars += [{"Round": rr, "Car": "Yours", "Off": g["log"][block]["car"]},
                     {"Round": rr, "Car": f"The real {team_name}", "Off": w["pace"][g["team"]][rr]}]
        chart = alt.Chart(pd.DataFrame(cars)).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("Round:Q", scale=alt.Scale(zero=False, nice=False)), y=alt.Y("Off:Q", title="% off the quickest", scale=alt.Scale(zero=False)),
            color=alt.Color("Car:N", scale=alt.Scale(range=["#e10600", "#8a8a96"]), legend=alt.Legend(orient="top", title=None)))
        st.altair_chart(dress(chart).properties(height=300), use_container_width=True)

st.caption("The other teams' pace is real (their clean-lap pace in every race that season, smoothed). Costs, gains, "
           "correlation risk and reliability are illustrative game numbers.")
