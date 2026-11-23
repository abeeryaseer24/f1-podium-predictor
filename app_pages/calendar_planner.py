"""Calendar Planner: how far the F1 circus travels in a season, and a shorter order for the same races."""
import altair as alt
import pandas as pd
import streamlit as st

import calendar_plan as C
from charts import dress, theme
from style import stat_strip
from ui_kit import GOOD, POOR, board, section

WORLD = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"


@st.cache_data(ttl=86400)
def seasons():
    r = pd.read_csv(C.RACES)
    counts = r.groupby("season").size()
    return sorted(counts[counts >= 8].index.tolist(), reverse=True)


@st.cache_data(ttl=86400, max_entries=60)
def solve(year, fixed, shift, base, factors):
    s = C.season(year)
    pts = list(zip(s["latitude"], s["longitude"]))
    return C.optimise(pts, set(fixed), shift, dict(factors), base=base)


years = seasons()
c1, c2 = st.columns([1, 2])
year = c1.selectbox("Season", years, index=1 if len(years) > 1 else 0, key="cal_year",
                    help="The newest season may still be running, so the one before is picked first.")
s = C.season(year)
names = [f"{r.round}. {r.locality}" for r in s.itertuples()]
default_fixed = [0, len(s) - 1] + [i for i, n in enumerate(s["race_name"]) if "Monaco" in n]
fixed = c2.multiselect("Races that keep their date", list(range(len(s))), default=sorted(set(default_fixed)),
                       format_func=lambda i: names[i], key=f"cal_fixed_{year}")
c3, c4 = st.columns(2)
shift = c3.slider("How far any other race may move (places)", 0, max(1, len(s) - 1), min(4, len(s) - 1), key="cal_shift",
                  help="Weather, holidays and contracts tie races to their dates. 0 keeps the real calendar.")
base = c4.toggle("Start and end the season at a European base", True, key="cal_base")
with st.expander("The carbon estimate"):
    e1, e2, e3 = st.columns(3)
    tonnes = e1.number_input("Freight moved per race (tonnes)", 200, 3000, int(C.DEFAULTS["tonnes"]), step=100)
    air = e2.number_input("Air freight (kg CO₂ per tonne-km)", 0.2, 1.5, C.DEFAULTS["air"], step=0.05)
    road = e3.number_input("Trucks (kg CO₂ per tonne-km)", 0.02, 0.4, C.DEFAULTS["road"], step=0.01)
factors = {"tonnes": float(tonnes), "air": float(air), "road": float(road)}

pts = list(zip(s["latitude"], s["longitude"]))
real = list(range(len(s)))
best = solve(year, tuple(sorted(fixed)), shift, base, tuple(sorted(factors.items())))
legs_r, km_r, kg_r = C.route(pts, real, factors, base)
legs_b, km_b, kg_b = C.route(pts, best, factors, base)
stat_strip([
    ("Real calendar", f"{km_r:,.0f} km", f"about {kg_r / 1e6:,.0f} thousand tonnes of CO₂", True),
    ("Shorter order", f"{km_b:,.0f} km", f"about {kg_b / 1e6:,.0f} thousand tonnes", False),
    ("Saved", f"{1 - kg_b / kg_r:.0%}", f"{km_r - km_b:,.0f} km less travel", False),
    ("Air legs", f"{sum(l['mode'] == 'air' for l in legs_r)} → {sum(l['mode'] == 'air' for l in legs_b)}",
     "flights between races", False),
])

# ---------- the map ----------
section("Both seasons on the map", "Red: the real order. Green: the shorter one.")
text, grid, muted = theme()


def path(order, label):
    stops = ([("Base", *C.BASE)] if base else []) + [(names[i], *pts[i]) for i in order] + ([("Base", *C.BASE)] if base else [])
    return pd.DataFrame([{"stop": n, "lat": a, "lon": b, "step": k, "calendar": label} for k, (n, a, b) in enumerate(stops)])


df = pd.concat([path(real, "Real"), path(best, "Shorter")])
world = alt.Chart(alt.topo_feature(WORLD, "countries")).mark_geoshape(fill=grid, stroke=muted, strokeWidth=0.3)
lines = alt.Chart(df).mark_line(strokeWidth=1.6, opacity=.85).encode(
    longitude="lon:Q", latitude="lat:Q", order="step:Q",
    color=alt.Color("calendar:N", scale=alt.Scale(domain=["Real", "Shorter"], range=["#e4544a", "#1fd6a0"]),
                    legend=alt.Legend(orient="top", title=None)))
dots = alt.Chart(df[df["calendar"] == "Real"]).mark_circle(size=40, color=text).encode(
    longitude="lon:Q", latitude="lat:Q", tooltip=["stop"])
st.altair_chart(dress((world + lines + dots).project("equalEarth")).properties(height=420), use_container_width=True)

# ---------- the shorter calendar ----------
section("The shorter calendar", "Each race's new slot, and the trip to get there.")
rows = []
for slot, i in enumerate(best):
    into = legs_b[slot] if base else (legs_b[slot - 1] if slot else None)
    moved = slot - i
    rows.append({"colour": GOOD if moved == 0 else ("#e8b33a" if abs(moved) <= 2 else POOR),
                 "cells": [(names[i], "kept its date" if i in fixed else s.loc[i, "race_name"]),
                           (moved, "same slot" if moved == 0 else f"{moved:+d} places"),
                           f"{into['km']:,.0f} km by {'road' if into['mode'] == 'road' else 'air'}" if into else "–"]})
board([("Race", "label"), ("Moved", "delta"), ("Trip to get there", "text")], rows, ranked=True)

st.caption("Distances are great-circle distances between the circuits (road legs stretched by a quarter for real roads). "
           "Legs between two European circuits go by truck, the rest by air. The carbon figure is an estimate built "
           "from round numbers you can change above: real F1 freight mixes air, sea and road and teams don't publish "
           "leg-by-leg figures. Sea freight for the long-haul kit and people's own travel are left out. The search is "
           "simulated annealing; it finds a good order, not always the very best.")
