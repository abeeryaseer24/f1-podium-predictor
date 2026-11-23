"""Superlicence Calculator: the FIA points every driver needs for Formula 1, and who on the ladder has them."""
import pandas as pd
import streamlit as st

import ladder as L
from style import stat_strip
from ui_kit import GOLD, GOOD, POOR, board, section


@st.cache_data(ttl=86400)
def data():
    st_, _, sl = L.load()
    return st_, sl, L.f1_careers()


standings, sl, f1 = data()
POSITIONS = ["Outside the top 10"] + [f"{i}{'st' if i == 1 else 'nd' if i == 2 else 'rd' if i == 3 else 'th'}" for i in range(1, 11)]

# ---------- your own path ----------
section("Plan a path to Formula 1", f"A driver needs at least {L.SL_NEEDED} points from their championship places "
        "over the three seasons before. Pick a series and a final position for each.")
series_list = sl["series"].tolist()
default = {0: "FIA Formula 3 Championship", 1: "FIA Formula 2 Championship", 2: "FIA Formula 2 Championship"}
default_pos = {0: 3, 1: 5, 2: 4}
total, parts = 0.0, []
cols = st.columns(3)
for k, col in enumerate(cols):
    with col:
        st.markdown(f"**Season {k + 1}**" + (" (the most recent)" if k == 2 else ""))
        ser = st.selectbox("Series", series_list, index=series_list.index(default[k]) if default[k] in series_list else 0,
                           key=f"sl_s{k}", label_visibility="collapsed")
        pos = st.selectbox("Position", POSITIONS, index=default_pos[k], key=f"sl_p{k}", label_visibility="collapsed")
        n = POSITIONS.index(pos)
        pts = float(sl.loc[sl["series"] == ser, f"p{n}"].iloc[0]) if n else 0.0
        total += pts
        parts.append((ser, pos, pts))
        st.caption(f"{pts:g} points")
ok = total >= L.SL_NEEDED
stat_strip([
    ("Your total", f"{total:g}", f"of the {L.SL_NEEDED} needed", True),
    ("Verdict", "Eligible" if ok else "Not yet", "for a Super Licence on points" if ok else
     f"{L.SL_NEEDED - total:g} points short", False),
])
st.caption("Points alone aren't everything: the FIA also sets an age limit, a driving test and minimum single-seater "
           "experience. Points from the FIA's Supplement 1, as listed in Wikipedia's FIA Super Licence article.")

# ---------- who has them ----------
last = int(standings["season"].max())
section(f"Who on the ladder has the points for {last + 1}", f"F2, F3 and F1 Academy results from {last - 2} to {last}, "
        "scored with today's table. Drivers already racing in Formula 1 are left out.")
recent = standings[standings["season"].between(last - 2, last)].copy()
recent["sl"] = [L.sl_points(sl, s, p) for s, p in zip(recent["series"], recent["pos"])]
# a driver in two series in one season: the better result counts here
best = recent.sort_values("sl", ascending=False).drop_duplicates(["key", "season"])
by = best.groupby("key")
summary = pd.DataFrame({"driver": by["driver"].first(), "points": by["sl"].sum(),
                        "path": by.apply(lambda g: " · ".join(f"{r.season} {r['name']} P{r.pos}"
                                                               for _, r in g.sort_values("season").iterrows()),
                                         include_groups=False)})
summary = summary.join(f1)
summary = summary[summary["starts"].isna() & (summary["points"] > 0)].sort_values("points", ascending=False)
eligible = summary[summary["points"] >= L.SL_NEEDED]
stat_strip([
    ("Eligible on points", f"{len(eligible)}", f"drivers with {L.SL_NEEDED}+ from these series", True),
    ("Close", f"{int(summary['points'].between(30, L.SL_NEEDED - 0.5).sum())}", "on 30 to 39 points", False),
])
rows = [{"colour": GOOD if r["points"] >= L.SL_NEEDED else (GOLD if r["points"] >= 30 else POOR),
         "cells": [(r["driver"], r["path"]), (r["points"], f"{r['points']:g}"),
                   "eligible" if r["points"] >= L.SL_NEEDED else f"{L.SL_NEEDED - r['points']:g} short"]}
        for _, r in summary.head(30).iterrows()]
board([("Driver", "label"), ("Super Licence points", "bar"), ("Status", "text")], rows, ranked=True)
st.caption("Only F2, F3 and F1 Academy are in our archive, so points from other series (Formula Regional, IndyCar, "
           "Super Formula and more) are missing: some drivers will have more than shown. Where someone raced two of "
           "these series in one season, only the better result is counted here. GP2 and GP3 count as F2 and F3. "
           "Results from Wikipedia's season articles (CC BY-SA 4.0).")
