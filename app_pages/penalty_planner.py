"""Engine Penalty Planner: where to fit new power units for the cheapest grid penalties."""
import streamlit as st

import penalties as P
from app_data import get_calendar
from predictor import current_season
from style import stat_strip
from ui_kit import board, section


@st.cache_data(ttl=86400)
def costs():
    return P.place_costs()


@st.cache_data(ttl=86400)
def calendar(season):
    return [{"round": r["round"], "race_name": r["race_name"], "circuit_id": r["circuit_id"]} for r in get_calendar(season)]


season = current_season()
races = calendar(season)
pc = costs()
c1, c2 = st.columns(2)
allowance = c1.slider("Power units allowed in the season", 2, 6, 3, key="pp_allow")
life = c2.slider("Races a unit lasts", 3, 12, 7, key="pp_life",
                 help="How many race weekends one unit can do before it must be replaced.")
cost = [pc.get(r["circuit_id"], P.DEFAULT_SLOPE) for r in races]
best_picks, best_cost = P.plan(cost, allowance, life)
simple_picks, simple_cost = P.naive(cost, allowance, life)
pen = P.penalty_places(best_picks, allowance)

needed = len(best_picks)
stat_strip([
    ("Units needed", f"{needed}", f"{max(0, needed - allowance)} beyond the allowance of {allowance}", True),
    ("Smart plan", f"{best_cost:.1f}", "finishing places lost to penalties", False),
    ("Change only when worn out", f"{simple_cost:.1f}", "finishing places lost", False),
    ("Saved by planning", f"{simple_cost - best_cost:.1f}", "places at the flag over the season", False),
])

section(f"The {season} calendar, planned", "Where the smart plan fits each new unit, and what a grid place costs at "
        "every circuit (how far a driver's finish moves for each place on the grid).")
rows = []
for k, (r, c) in enumerate(zip(races, cost)):
    fresh = k in best_picks
    places = pen.get(k, 0)
    rows.append({"colour": "#e10600" if places else ("#1fd6a0" if fresh else "#8a8a96"),
                 "cells": [(f"Round {r['round']}", r["race_name"]),
                           ("#1fd6a0" if fresh else "#3a3a48", "New unit" if fresh else "–"),
                           (-places, f"−{places} places" if places else "no penalty") if fresh else None,
                           (c, f"{c:.2f}"),
                           (-(places * c), f"{places * c:.1f}") if places else None]})
board([("Race", "label"), ("Power unit", "tag"), ("Grid penalty", "delta"), ("Cost of a grid place", "scale_low"),
       ("Places lost at the flag", "delta")], rows)
st.caption("Simplified: one power-unit set, no failures, and the rule's shape of 10 places for the first extra unit and "
           "5 for each one after. Grid-place costs are measured from every race since 2016.")
left, right = st.columns([3, 2], vertical_alignment="center")
left.caption("Real teams also plan around failures, part-by-part allowances and taking several parts at once.")
right.page_link("app_pages/academy_m5.py", label="Learn it: Academy 5.10 Reliability and penalties",
                icon=":material/school:", query_params={"ch": "5.10"})
