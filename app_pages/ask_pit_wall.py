"""Ask the Pit Wall: type a question about F1 history, get the answer from our own archive."""
import streamlit as st

import pit_wall_qa as PW
from classic import colour_for
from ui_kit import banner, board, chips, esc, section, versus

EXAMPLES = ["Most wins at Monaco", "Hamilton vs Verstappen", "Champion in 1988", "Senna poles",
            "Ferrari vs McLaren", "Podiums in the 2010s", "2008 British GP", "Team points since 2014"]


def ask(q):
    st.session_state["pw_q"] = q


q = st.text_input("Your question", key="pw_q", placeholder="e.g. Alonso podiums with Ferrari, or Prost vs Senna")
cols = st.columns(4)
for i, e in enumerate(EXAMPLES):
    cols[i % 4].button(e, key=f"pw_ex{i}", on_click=ask, args=(e,), use_container_width=True)

if not q.strip():
    st.caption("Ask about wins, poles, podiums, titles, points, starts, retirements or fastest laps, for any driver, "
               "team, circuit or year since 1950. Two names make a head-to-head.")
    st.stop()

p = PW.parse(q)
a = PW.answer(p)
chips([("How I read it", "#8a8a96")] + PW.reading(p))
banner("📻", a["headline"], esc(a.get("note") or "From our archive of every Grand Prix since 1950."))

if a.get("versus"):
    left, right, team_l, team_r, stats, ahead = a["versus"]
    cl, cr = colour_for(team_l), colour_for(team_r)
    if cl == cr:
        cr = "#27f4d2" if cl != "#27f4d2" else "#ff8000"
    rows = ([(ahead[0], ahead[1], ahead[2], f"{ahead[1]:g}", f"{ahead[2]:g}")] if ahead else []) + \
        [(lab, l, r, f"{l:g}", f"{r:g}") for lab, l, r in stats]
    versus(left, right, rows, left_colour=cl, right_colour=cr)
elif a["rows"]:
    by = a.get("by", "Driver")
    shape = p["shape"]
    if shape == "race":
        section("The top ten", "")
        board([("Driver", "label"), ("Grid and status", "text")],
              [{"colour": colour_for(team), "cells": [(name, team), sub]} for name, _, sub, team in a["rows"]], ranked=True)
    elif shape == "record" and by == "Season":
        section("Season by season", "")
        board([("Season", "label"), (a["value_label"], "bar")],
              [{"colour": colour_for(team), "cells": [(season, f"{team} · {sub}"), (v, f"{v:g}")]}
               for season, v, sub, team in reversed(a["rows"])])
    else:
        section("The leaderboard" if shape == "leaders" else f"By {by.lower()}", "")
        board([(by, "label"), (a["value_label"], "bar")],
              [{"colour": colour_for(team), "cells": [(name, team if by == "Driver" else ""), (v, f"{v:g}")]}
               for name, v, _, team in a["rows"]], ranked=True)

st.caption("No AI model reads your question: it's matched word by word against every driver, team and circuit, with "
           "spelling mistakes forgiven. If the chips above show the wrong reading, try naming things more plainly.")
