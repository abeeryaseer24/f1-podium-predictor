"""One page layout for a series' championships: Feeder Series (F2, F3, F1 Academy) and Other Series (Formula E,
IndyCar). Standings, teams, every champion, and each driver's Formula 1 story from our F1 archive."""
import pandas as pd
import streamlit as st

import ladder as L
from style import stat_strip
from ui_kit import GOLD, banner, board, section

COLOURS = {"F2": "#3a7bd5", "F3": "#c0392b", "F1A": "#d63384", "FE": "#1fd6a0", "INDY": "#e8b33a"}
TEAM_COLOURS = ["#e10600", "#27f4d2", "#e8b33a", "#3a7bd5", "#9b59b6", "#1fd6a0", "#ff8c42", "#8a8a96"]
NOTES = {"F2": "Before 2017 the series was called GP2.", "F3": "Before 2019 the series was called GP3.",
         "F1A": "The all-female series began in 2023.", "FE": "Seasons are listed by the year they ended.",
         "INDY": "Since 2010."}


@st.cache_data(ttl=86400)
def data():
    st_, teams, _ = L.load()
    return st_.join(L.f1_careers(), on="key"), teams


def ordinal(n):
    n = int(n)
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"


def show(names, key, after_only=True):
    """after_only=True: the F1 column counts only careers that began after the season (the feeder question).
    False: any F1 career, before or after (Formula E and IndyCar have many former F1 drivers)."""
    standings, teams = data()
    c1, c2 = st.columns(2)
    series = c1.segmented_control("Series", list(names), default=list(names)[0], format_func=names.get,
                                  key=f"{key}_series") or list(names)[0]
    seasons = sorted(standings.loc[standings["series"] == series, "season"].unique(), reverse=True)
    if not seasons:
        st.info("No seasons for this series yet.")
        return
    season = c2.selectbox("Season", seasons, key=f"{key}_season_{series}")
    table = standings[(standings["series"] == series) & (standings["season"] == season)].sort_values("pos")
    label, colour = table["name"].iloc[0], COLOURS.get(series, "#e10600")

    def in_f1(r, season_):
        return pd.notna(r["first_f1"]) and (r["first_f1"] >= season_ if after_only else True)

    champ = table.iloc[0]
    runner = table.iloc[1] if len(table) > 1 else None
    gap = champ["points"] - runner["points"] if runner is not None else 0
    if pd.notna(champ["first_f1"]):
        f1_note = (f"Reached F1 in {int(champ['first_f1'])}." if champ["first_f1"] >= season
                   else f"A former F1 driver: {int(champ['starts'])} Grands Prix.")
    else:
        f1_note = "Hasn't started an F1 race."
    banner("🏆", f"{season} {label} champion: {champ['driver']}",
           f"{champ['team'] or 'team unknown'} · {champ['points']:g} points, {gap:g} ahead of "
           f"{runner['driver'] if runner is not None else '–'} · {champ['wins']} wins. {f1_note}", colour)
    f1_count = sum(in_f1(r, season) for _, r in table.iterrows())
    stat_strip([
        ("Drivers", f"{len(table)}", "scored or started this season", True),
        ("Races", f"{int(table['races'].max())}", "counted in the table", False),
        ("Went on to F1" if after_only else "Have raced in F1", f"{f1_count}",
         "started a Grand Prix after this season" if after_only else "started a Grand Prix at some point", False),
    ])

    section("Drivers' championship", "A gold edge: " + ("went on to start a Formula 1 race." if after_only
                                                        else "has started a Formula 1 race."))
    team_list = list(dict.fromkeys(table["team"].fillna("")))
    rows = []
    for _, r in table.iterrows():
        f1 = in_f1(r, season)
        sub = r["team"] if isinstance(r["team"], str) and r["team"] else "team not listed"
        f1_text = (f"F1 {int(r['first_f1'])}" if after_only else f"{int(r['starts'])} F1 starts") if f1 else "–"
        rows.append({"colour": GOLD if f1 else TEAM_COLOURS[team_list.index(r["team"] if isinstance(r["team"], str) else "")
                                                             % len(TEAM_COLOURS)],
                     "cells": [(r["driver"], sub), (r["points"], f"{r['points']:g}"), f"{r['wins']}", f"{r['podiums']}", f1_text]})
    board([("Driver", "label"), ("Points", "bar"), ("Wins", "num"), ("Podiums", "num"), ("Formula 1", "text")], rows, ranked=True)

    tt = teams[(teams["series"] == series) & (teams["season"] == season)].sort_values("pos")
    if len(tt):
        section("Teams' championship")
        board([("Team", "label"), ("Points", "bar")],
              [{"colour": TEAM_COLOURS[i % len(TEAM_COLOURS)], "cells": [(r["team"], ""), (r["points"], f"{r['points']:g}")]}
               for i, (_, r) in enumerate(tt.iterrows())], ranked=True)

    section(f"Every {names[series]} champion", "And their Formula 1 story. " + NOTES.get(series, ""))
    champs = standings[(standings["series"] == series) & (standings["pos"] == 1)].sort_values("season", ascending=False)
    rows, went_count = [], 0
    for _, r in champs.iterrows():
        went = pd.notna(r["first_f1"]) and (r["first_f1"] >= r["season"] - 1 if after_only else True)
        went_count += went
        if went:
            best = f", best {ordinal(r['best_f1'])} in the championship" if pd.notna(r["best_f1"]) else ""
            career = f"{int(r['starts'])} starts, {int(r['f1_wins'])} wins{best}"
        else:
            career = "not in F1 (yet)" if after_only else "never raced in F1"
        rows.append({"colour": GOLD if went else colour,
                     "cells": [(r["driver"], f"{r['season']} · {r['name']}"), r["team"] if isinstance(r["team"], str) else "",
                               (r["points"], f"{r['points']:g}"), career]})
    board([("Champion", "label"), ("Team", "text"), ("Points", "bar"), ("In Formula 1", "text")], rows)
    st.caption(f"{went_count / max(len(champs), 1):.0%} of these champions have started a Grand Prix. Results from "
               "Wikipedia's season articles (CC BY-SA 4.0); F1 careers from our own archive.")
