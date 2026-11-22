"""Rules Sandbox: every drivers' championship since 1950, recomputed under the rules you pick."""
import streamlit as st

import rules
from app_archive import require_history
from style import stat_strip
from ui_kit import GOOD, board, league, section

require_history()

PALETTE = ["#e10600", "#27f4d2", "#ff8000", "#3671c6", "#e8b33a", "#64c4ff", "#b6babd", "#229971",
           "#c04dff", "#ff87bc", "#52e252", "#2b4562"]


def colour_for(team):
    """The same colour for the same team name every time (historical teams have no official colour here)."""
    known = {"ferrari": "#e8002d", "mclaren": "#ff8000", "mercedes": "#27f4d2", "red bull": "#3671c6",
             "williams": "#64c4ff", "lotus": "#ffd23f", "brabham": "#229971", "renault": "#ffd800",
             "benetton": "#4dc94f", "tyrrell": "#2b4562", "brm": "#52e252", "cooper": "#2b6cff"}
    name = str(team).lower()
    for key, colour in known.items():
        if key in name:
            return colour
    return PALETTE[sum(map(ord, name)) % len(PALETTE)]


@st.cache_data(ttl=3600)
def run(points, fastest_lap, best_of, sprints):
    return rules.compare(list(points), fastest_lap, best_of, sprints)


left, right = st.columns([3, 2])
with left:
    name = st.selectbox("Points system", list(rules.SYSTEMS) + ["Make my own"])
    if name == "Make my own":
        text = st.text_input("Points for P1, P2, P3… separated by commas", "25, 18, 15, 12, 10, 8, 6, 4, 2, 1")
        try:
            points = [float(x) for x in text.replace(" ", "").split(",") if x != ""]
        except ValueError:
            st.error("Use numbers separated by commas, like 10, 6, 4, 3, 2, 1.")
            st.stop()
        if not points:
            st.stop()
    else:
        points = rules.SYSTEMS[name]
with right:
    fastest_lap = st.toggle("A point for the fastest lap", help="Only where the archive says who set it "
                                                               "(2004 onwards), and only for a top-10 finisher.")
    sprints = st.toggle("Add sprint race points (2021 onwards)")
    best_of = st.slider("Count only each driver's best results", 0, 24, 0,
                        help="0 counts every race. Until 1990 F1 often dropped a driver's worst results.")

out, tables = run(tuple(points), fastest_lap, best_of, sprints)
changed = out[out["changed"]]
counts = rules.title_counts(tables)
real_counts = out.groupby("real_name").size()
most = counts.index[0] if len(counts) else "–"
stat_strip([
    ("Titles that change hands", f"{len(changed)}", f"of {len(out)} seasons", True),
    ("Most titles under these rules", most, f"{int(counts.iloc[0])} titles" if len(counts) else "", False),
    ("Closest title", f"{out['margin'].min():g} pts" if out["margin"].notna().any() else "–",
     (str(out.loc[out["margin"].idxmin(), "season"])
      + (" · level on points, decided on countback" if out["margin"].min() == 0 else ""))
     if out["margin"].notna().any() else "", False),
])

if len(changed):
    section("Titles that change hands", "Seasons where these rules crown a different champion.")
    board([("Season", "label"), ("Real champion", "label"), ("Under these rules", "label"), ("Margin", "bar")],
          [{"colour": colour_for(r.new_team),
            "cells": [(str(r.season), "level, decided on countback" if not r.margin else f"won by {r.margin:g} pts"),
                      (r.real_name, r.real_team), (f"{r.new_name} ★", r.new_team),
                      (max(float(r.margin), 0.5), f"{r.margin:g} pts" if r.margin else "countback")]}
           for r in changed.itertuples()])
else:
    section("Titles that change hands")
    st.caption("None: every champion stays the same under these rules.")

section("All-time title count under these rules", "Change against the real count in brackets.")
rows = []
for driver, n in counts.head(15).items():
    real = int(real_counts.get(driver, 0))
    diff = n - real
    rows.append({"name": driver, "sub": f"real count: {real}" + (f" ({diff:+d})" if diff else ""),
                 "colour": GOOD if diff > 0 else "#e4544a" if diff < 0 else "#8a8a96",
                 "bar": n / max(counts.max(), 1), "figures": [(n, "titles")]})
league(rows)

section("Any season, both ways", "The full table under these rules next to the real champion.")
season = st.selectbox("Season", sorted(out["season"].tolist(), reverse=True))
table = tables[tables["season"] == season].head(10)
real_row = out[out["season"] == season].iloc[0]
st.caption(f"Real champion: **{real_row['real_name']}** ({real_row['real_team']}).")
board([("Driver", "label"), ("Wins", "num"), ("Points", "bar")],
      [{"colour": colour_for(r.team), "cells": [(r.driver_name + (" ★" if r.driver_name == real_row["real_name"] else ""), r.team),
                                                int(r.wins), (r.points, f"{r.points:g}")]}
       for r in table.itertuples()], ranked=True)
st.caption("★ marks the real champion.")

with st.expander("What this can't reproduce"):
    st.markdown("""
- **Shared drives.** In the 1950s two drivers could share a car and split its points. Here each
  driver scores their own result.
- **Historical dropped-results rules** were more complicated than "best N" (some years split the
  season in halves). The *real champion* column always comes from the official standings.
- **Half points** for shortened races aren't applied.
- **The fastest-lap point** can only be given from 2004, the first season our archive records who set it.
- Michael Schumacher's 1997 season is left out of the tables: he was excluded from that championship.
- The current season is still running, so its "champion" is today's leader.
""")
