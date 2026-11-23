"""Fantasy Optimizer: the best budget-capped fantasy team from the model's predictions, by integer programming."""
import altair as alt
import pandas as pd
import streamlit as st

import fantasy as F
import predictor as P
from app_data import get_upcoming, run_upcoming
from charts import dress
from style import stat_strip, team_info
from ui_kit import GOLD, board, chips, section

CAPTAIN = GOLD


@st.cache_data(ttl=3600)
def past(season, rnd, budget):
    return F.past_race(season, rnd, budget)


@st.cache_data(ttl=3600)
def upcoming(season, rnd, budget):
    model, _ = P.load_model()
    return F.upcoming_race(run_upcoming(season, rnd)["table"], season, rnd, model.get("luck", 1.0), budget)


@st.cache_data(ttl=6 * 3600)
def backtest(season, budget):
    return F.season_backtest(season, budget)


@st.cache_data(ttl=6 * 3600)
def seasons_with_backtests():
    return sorted(pd.read_csv(F.BACKTEST, usecols=["season"])["season"].unique().tolist(), reverse=True)


def team_of(r):
    return dict(zip(r["race"]["driver"], r["race"]["constructor"]))


def team_board(r, pick, points=None, points_t=None):
    """The picked team: drivers then constructors, with price and expected (and real) points."""
    owner = team_of(r)
    rows = []
    for d in sorted(pick["drivers"], key=lambda d: -r["exp_d"][d]):
        cap = d == pick["captain"]
        e = r["exp_d"][d] * (2 if cap else 1)
        cells = [(F.name(d), team_info(owner[d])[0] + (" · captain, double points" if cap else "")),
                 f"{r['price_d'][d]:.1f}", (e, f"{e:.1f}")]
        if points is not None:
            v = points.get(d, 0) * (2 if cap else 1)
            cells.append((v, f"{v:+.0f}"))
        rows.append({"colour": team_info(owner[d])[1], "cells": cells})
    for t in sorted(pick["teams"], key=lambda t: -r["exp_t"][t]):
        cells = [(team_info(t)[0], "constructor"), f"{r['price_t'][t]:.1f}", (r["exp_t"][t], f"{r['exp_t'][t]:.1f}")]
        if points_t is not None:
            cells.append((points_t.get(t, 0), f"{points_t.get(t, 0):+.0f}"))
        rows.append({"colour": team_info(t)[1], "cells": cells})
    cols = [("Pick", "label"), ("Price", "num"), ("Expected points", "bar")]
    if points is not None:
        cols.append(("Scored", "delta"))
    board(cols, rows)


def price_list(r):
    owner = team_of(r)
    rows = sorted(({"colour": team_info(owner[d])[1],
                    "cells": [(F.name(d), team_info(owner[d])[0]), f"{r['price_d'][d]:.1f}", (r["exp_d"][d], f"{r['exp_d'][d]:.1f}"),
                              (r["exp_d"][d] / r["price_d"][d], f"{r['exp_d'][d] / r['price_d'][d]:.2f}")]}
                   for d in r["exp_d"].index if d in r["price_d"]), key=lambda x: -x["cells"][2][0])
    rows += sorted(({"colour": team_info(t)[1],
                     "cells": [(team_info(t)[0], "constructor"), f"{r['price_t'][t]:.1f}", (r["exp_t"][t], f"{r['exp_t'][t]:.1f}"),
                               (r["exp_t"][t] / r["price_t"][t], f"{r['exp_t'][t] / r['price_t'][t]:.2f}")]}
                    for t in r["exp_t"].index if t in r["price_t"]), key=lambda x: -x["cells"][2][0])
    board([("Driver or team", "label"), ("Price", "num"), ("Expected points", "bar"), ("Points per million", "scale")], rows)


mode = st.radio("Race", ["Next race", "A past race", "A whole season"], horizontal=True, key="fo_mode")
c1, c2 = st.columns([1, 2])
budget = c1.slider("Budget", 80.0, 120.0, F.BUDGET, 0.5, key="fo_budget")

# ---------- a whole season ----------
if mode == "A whole season":
    season = c2.selectbox("Season", seasons_with_backtests(), key="fo_season")
    bt = backtest(season, budget)
    if bt.empty:
        st.info("No races to replay for that season yet.")
        st.stop()
    stat_strip([
        ("Model's teams", f"{bt['model'].sum():,.0f}", f"points over {len(bt)} races", True),
        ("Best in hindsight", f"{bt['best'].sum():,.0f}", "knowing every result", False),
        ("A random team", f"{bt['random'].sum():,.0f}", "the average team that fits the budget", False),
        ("Expected", f"{bt['expected'].sum():,.0f}", "what the model said its teams would score", False),
    ])
    section("Points through the season", "Each race picked before it was run, by a model trained only on earlier seasons.")
    long = bt.assign(**{"Model's team": bt["model"].cumsum(), "Best in hindsight": bt["best"].cumsum(),
                        "A random team": bt["random"].cumsum()}).melt(
        id_vars=["round", "race_name"], value_vars=["Model's team", "Best in hindsight", "A random team"],
        var_name="Team", value_name="Points")
    chart = alt.Chart(long).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("round:Q", title="Round", scale=alt.Scale(zero=False, nice=False), axis=alt.Axis(tickMinStep=1)), y=alt.Y("Points:Q", title="Points so far"),
        color=alt.Color("Team:N", scale=alt.Scale(domain=["Model's team", "Best in hindsight", "A random team"],
                                                  range=["#e10600", GOLD, "#8a8a96"]), legend=alt.Legend(orient="top", title=None)),
        tooltip=["race_name", "Team", alt.Tooltip("Points:Q", format=",.0f")])
    st.altair_chart(dress(chart).properties(height=300), use_container_width=True)
    section("Race by race")
    board([("Race", "label"), ("Model's team", "bar"), ("Best in hindsight", "num"), ("Share of the best", "scale")],
          [{"colour": "#e10600", "cells": [(r.race_name.replace(" Grand Prix", ""), f"Round {r.round}"), (r.model, f"{r.model:.0f}"),
                                           f"{r.best:.0f}", (r.model / r.best if r.best else 0, f"{r.model / r.best:.0%}" if r.best else "")]}
           for r in bt.itertuples()])
    st.caption("Prices and rules are this page's own (see below). The model's teams use only what was known before each race.")
    st.stop()

# ---------- one race ----------
if mode == "Next race":
    try:
        up = get_upcoming(P.current_season())
    except Exception:
        up = pd.DataFrame()
    if up.empty:
        st.info("No races left this season. Pick a past race, or replay a whole season.")
        st.stop()
    season, rnd, race_name = P.current_season(), int(up["round"].iloc[0]), up["race_name"].iloc[0]
    c2.markdown(f"**Round {rnd} · {race_name}**")
    try:
        r = upcoming(season, rnd, budget)
    except Exception as error:
        st.warning(f"The prediction for this race isn't ready yet ({error}).")
        st.stop()
else:
    races = P.past_races()
    races = races[races["season"].isin(seasons_with_backtests())]
    cs, cr = c2.columns(2)
    season = cs.selectbox("Season", sorted(races["season"].unique(), reverse=True), key="fo_past_season")
    rs = races[races["season"] == season]
    names = dict(zip(rs["round"], rs["race_name"]))
    rnd = cr.selectbox("Race", list(names), index=len(names) - 1, format_func=lambda k: f"Round {k} · {names[k]}", key="fo_past_round")
    r = past(int(season), int(rnd), budget)
    if r is None:
        st.info("No out-of-sample prediction for that race.")
        st.stop()

# your own constraints
owner = team_of(r)
options = sorted(r["price_d"], key=lambda d: -r["price_d"][d]) + sorted(r["price_t"], key=lambda t: -r["price_t"][t])
label = lambda k: f"{F.name(k)} ({r['price_d'][k]:.1f})" if k in r["price_d"] else f"{team_info(k)[0]} ({r['price_t'][k]:.1f})"
m1, m2 = st.columns(2)
must = m1.multiselect("Must include", options, format_func=label, key="fo_must")
never = m2.multiselect("Leave out", [o for o in options if o not in must], format_func=label, key="fo_never")
pick = r["pick"] if not (must or never) else F.optimise(r["exp_d"], r["exp_t"], r["price_d"], r["price_t"], budget, must, never)
if pick is None:
    st.warning("No team fits those choices within the budget. Raise the budget or drop a must-include.")
    st.stop()

tiles = [("Expected points", f"{pick['expected']:.1f}", "the most any team within budget can expect", True),
         ("Cost", f"{pick['cost']:.1f}", f"of {budget:.1f}", False),
         ("Captain", F.name(pick["captain"]), "double points", False)]
if mode == "A past race":
    scored = F.team_score(pick, r["real_d"], r["real_t"])
    tiles.append(("It scored", f"{scored:.0f}", f"best in hindsight {r['best']:.0f}", False))
stat_strip(tiles)

section("The team", "Five drivers and two constructors: the integer program's answer.")
if mode == "A past race":
    team_board(r, pick, r["real_d"], r["real_t"])
    hs = r["hindsight"]
    if hs:
        section("The best team in hindsight", "The same budget, knowing every result.")
        same = set(pick["drivers"] + pick["teams"]) & set(hs["drivers"] + hs["teams"])
        st.caption(f"Green: also in the model's team ({len(same)} of 7).")
        chips([(F.name(k) if k in r["price_d"] else team_info(k)[0], "#1fd6a0" if k in same else "#8a8a96")
               for k in hs["drivers"] + hs["teams"]])
        team_board(r, hs, r["real_d"], r["real_t"])
else:
    team_board(r, pick)

with st.expander("Every price and expected score"):
    price_list(r)

st.caption("Our own rules, in the style of the usual F1 fantasy games: race points, ±1 a place against the grid (at most "
           "10), −20 for a retirement, a double-points captain, and constructors scoring their drivers' race points. "
           "Prices are ours as well, from recent race points; the official game's prices aren't public data. Expected "
           "points come from replaying the race 20,000 times on the predictor's strengths.")
