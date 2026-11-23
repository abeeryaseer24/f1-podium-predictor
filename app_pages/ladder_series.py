"""Feeder Series: F2, F3 and F1 Academy standings, champions, and who made it to Formula 1."""
import pandas as pd
import streamlit as st

import ladder as L
from style import stat_strip
from ui_kit import GOLD, banner, board, chips, section

SERIES_COLOUR = {"F2": "#3a7bd5", "F3": "#c0392b", "F1A": "#d63384"}
TEAM_COLOURS = ["#e10600", "#27f4d2", "#e8b33a", "#3a7bd5", "#9b59b6", "#1fd6a0", "#ff8c42", "#8a8a96"]


@st.cache_data(ttl=86400)
def data():
    st_, teams, sl = L.load()
    return st_, teams, sl, L.f1_careers()


standings, teams, sl, f1 = data()
standings = standings.join(f1, on="key")

c1, c2 = st.columns(2)
series = c1.segmented_control("Series", list(L.SERIES_NAMES), default="F2", format_func=L.SERIES_NAMES.get,
                              key="lad_series") or "F2"
seasons = sorted(standings.loc[standings["series"] == series, "season"].unique(), reverse=True)
season = c2.selectbox("Season", seasons, key="lad_season")
table = standings[(standings["series"] == series) & (standings["season"] == season)].sort_values("pos")
label = table["name"].iloc[0]
colour = SERIES_COLOUR[series]

champ = table.iloc[0]
runner = table.iloc[1] if len(table) > 1 else None
gap = champ["points"] - runner["points"] if runner is not None else 0
f1_note = (f"Reached F1 in {int(champ['first_f1'])}." if pd.notna(champ["first_f1"]) else "Hasn't started an F1 race yet.")
banner("🏆", f"{season} {label} champion: {champ['driver']}",
       f"{champ['team'] or 'team unknown'} · {champ['points']:g} points, {gap:g} ahead of "
       f"{runner['driver'] if runner is not None else '–'} · {champ['wins']} wins. {f1_note}", colour)

reached = table["first_f1"].notna() & (table["first_f1"] >= season)
stat_strip([
    ("Drivers", f"{len(table)}", "scored or started this season", True),
    ("Races", f"{int(table['races'].max())}", "sprint and feature races counted", False),
    ("Went on to F1", f"{int(reached.sum())}", "started a Grand Prix after this season", False),
])

# ---------- drivers ----------
section("Drivers' championship", "Every driver's season. A gold edge: went on to start a Formula 1 race.")
team_list = list(dict.fromkeys(table["team"].fillna("")))
rows = []
for _, r in table.iterrows():
    in_f1 = pd.notna(r["first_f1"]) and r["first_f1"] >= season
    sub = r["team"] if isinstance(r["team"], str) and r["team"] else "team not listed"
    rows.append({"colour": GOLD if in_f1 else TEAM_COLOURS[team_list.index(r["team"] if isinstance(r["team"], str) else "") % len(TEAM_COLOURS)],
                 "cells": [(r["driver"], sub), (r["points"], f"{r['points']:g}"), f"{r['wins']}", f"{r['podiums']}",
                           (f"F1 {int(r['first_f1'])}" if in_f1 else "–")]})
board([("Driver", "label"), ("Points", "bar"), ("Wins", "num"), ("Podiums", "num"), ("Formula 1", "text")],
      rows, ranked=True)

# ---------- teams ----------
tt = teams[(teams["series"] == series) & (teams["season"] == season)].sort_values("pos")
if len(tt):
    section("Teams' championship")
    board([("Team", "label"), ("Points", "bar")],
          [{"colour": TEAM_COLOURS[i % len(TEAM_COLOURS)], "cells": [(r["team"], ""), (r["points"], f"{r['points']:g}")]}
           for i, (_, r) in enumerate(tt.iterrows())], ranked=True)

# ---------- champions ----------
section(f"Every {L.SERIES_NAMES[series]} champion", "And what they did next. "
        + {"F2": "Before 2017 the series was called GP2.", "F3": "Before 2019 the series was called GP3.",
           "F1A": "The all-female series began in 2023."}[series])
champs = standings[(standings["series"] == series) & (standings["pos"] == 1)].sort_values("season", ascending=False)
rows = []
for _, r in champs.iterrows():
    went = pd.notna(r["first_f1"]) and r["first_f1"] >= r["season"] - 1
    if went:
        best = f", best {int(r['best_f1'])}{'st' if int(r['best_f1']) == 1 else 'nd' if int(r['best_f1']) == 2 else 'rd' if int(r['best_f1']) == 3 else 'th'} in the championship" if pd.notna(r["best_f1"]) else ""
        career = f"{int(r['starts'])} starts, {int(r['f1_wins'])} wins{best}"
    else:
        career = "not in F1 (yet)"
    rows.append({"colour": GOLD if went else colour,
                 "cells": [(r["driver"], f"{r['season']} · {r['name']}"), r["team"] if isinstance(r["team"], str) else "",
                           (r["points"], f"{r['points']:g}"), career]})
board([("Champion", "label"), ("Team", "text"), ("Points", "bar"), ("In Formula 1", "text")], rows)
share = sum(1 for _, r in champs.iterrows() if pd.notna(r["first_f1"]) and r["first_f1"] >= r["season"] - 1) / max(len(champs), 1)
st.caption(f"{share:.0%} of these champions have started a Grand Prix. Results from Wikipedia's season articles "
           "(CC BY-SA 4.0); F1 careers from our own archive. Wins and podiums count sprint and feature races.")
