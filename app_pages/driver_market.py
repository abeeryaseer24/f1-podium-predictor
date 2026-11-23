"""Driver Market: who is likely to keep their seat, change team or leave F1 next season, and why."""
import json
from pathlib import Path

import streamlit as st

from style import stat_strip, team_info
from ui_kit import board, section

FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "driver_market.json"
OUTCOME = {"stay": ("Stays", "#1fd6a0"), "move": ("Moves team", "#f5a623"), "out": ("Leaves F1", "#e4544a")}
TEAM_IDS = {"Red Bull": "red_bull", "Racing Bulls": "rb", "RB F1 Team": "rb", "Aston Martin": "aston_martin",
            "Haas F1 Team": "haas", "Cadillac F1 Team": "cadillac", "Sauber": "sauber"}

if not FILE.exists():
    st.info("The driver market model hasn't been built yet.")
    st.stop()
data = json.loads(FILE.read_text(encoding="utf-8"))
tests = data["tests"]
n = sum(t["n"] for t in tests)
ll = sum(t["log_loss"] * t["n"] for t in tests) / n
base = sum(t["base_log_loss"] * t["n"] for t in tests) / n


def colour(team_name, team_id=None):
    return team_info(team_id or TEAM_IDS.get(team_name, team_name.lower().replace(" ", "_")))[1]


def why_text(why):
    out = [w["feature"] for w in why if w["push"] > 0]
    stay = [w["feature"] for w in why if w["push"] <= 0]
    return " · ".join(x for x in ((f"Against: {', '.join(out)}" if out else ""),
                                  (f"For: {', '.join(stay)}" if stay else "")) if x)


stat_strip([
    ("Next season", f"{data['season'] + 1}", f"from the {data['season']} season so far", True),
    ("Most at risk", data["live"][0]["name"].split()[-1], f"{1 - data['live'][0]['stay']:.0%} chance of losing the seat", False),
    ("Tested on", f"{n} seats", f"{tests[0]['season']}–{tests[-1]['season']}, each year out of sample", False),
    ("Better than base rates", f"{1 - ll / base:.0%}", f"log loss {ll:.2f} vs {base:.2f}", False),
])

section(f"The {data['season'] + 1} market", "Each driver's chance of staying, moving team or leaving F1, and the three biggest reasons.")
board([("Driver", "label"), ("Stays", "scale"), ("Moves team", "scale_low"), ("Leaves F1", "scale_low"), ("Why", "text")],
      [{"colour": colour(r["team_name"], r["team"]),
        "cells": [(r["name"], f"{r['team_name']} · {r['age']:.0f} years old"), (r["stay"], f"{r['stay']:.0%}"),
                  (r["move"], f"{r['move']:.0%}"), (r["out"], f"{r['out']:.0%}"), why_text(r["why"])]}
       for r in data["live"]])

section("How it did before", "Pick a season: what the model said that winter, before anyone knew, and what happened.")
years = [t["season"] for t in tests]
y = st.select_slider("Season", years, value=years[-1], key="dm_year")
t = next(t for t in tests if t["season"] == y)
stat_strip([
    ("Right call", f"{t['accuracy']:.0%}", f"always guessing 'stays' was {t['base_accuracy']:.0%}", True),
    ("Log loss", f"{t['log_loss']:.2f}", f"base rates {t['base_log_loss']:.2f} (lower is better)", False),
    ("Seats changed", f"{sum(d['actual'] != 'stay' for d in t['drivers'])}", f"of {t['n']}", False),
])
rows = []
for d in sorted(t["drivers"], key=lambda d: d["stay"]):
    label, col = OUTCOME[d["actual"]]
    guess = max(OUTCOME, key=lambda k: d[k])
    rows.append({"colour": col, "cells": [(d["name"], d["team"]), (d["stay"], f"{d['stay']:.0%}"), (d["move"], f"{d['move']:.0%}"),
                                          (d["out"], f"{d['out']:.0%}"), (col, label),
                                          "✓" if guess == d["actual"] else ""]})
board([("Driver", "label"), ("Stays", "scale"), ("Moves team", "scale_low"), ("Leaves F1", "scale_low"),
       ("What happened", "tag"), ("Called it", "text")], rows)

st.caption("Every driver-season since 1980, a multinomial logistic regression on age, experience, form, the teammate "
           "battle and the team's results; a renamed team counts as the same team. It doesn't know contracts (there's "
           "no free source), who owns the team or who is sponsoring whom, so read it as what the results alone say.")
