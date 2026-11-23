"""Scouting Report: which feeder records turned into Formula 1 careers, and who looks next."""
import json

import pandas as pd
import streamlit as st

import scouting as S
from style import stat_strip
from ui_kit import GOLD, GOOD, POOR, board, section


@st.cache_data(ttl=86400)
def data():
    return json.loads(S.OUT.read_text(encoding="utf-8"))


d = data()
hist = pd.DataFrame(d["history"])
r, e = d["reach"], d["established"]

stat_strip([
    ("Ranking skill", f"{r['auc']:.2f}", "area under the ROC curve on eras it never saw (0.5 is guessing)", True),
    ("Drivers tested", f"{r['drivers']}", f"F2/GP2 and F3/GP3 careers since 2005, {r['base']:.0%} reached F1", False),
    ("Lasting careers", f"{e['auc']:.2f}", f"telling who makes {e['starts']}+ starts, from only {e['drivers']} drivers", False),
])

# ---------- who looks next ----------
section("Who looks next", f"Drivers from the last two seasons without a Grand Prix start: the model's chance they "
        f"start one within {r['window']} seasons of leaving the ladder, and the past drivers whose records were closest.")
rows = []
for c in d["candidates"][:20]:
    alike = ", ".join(f"{s['driver']} ({'F1, ' + str(s['starts']) + ' starts' if s['reached'] else 'no F1'})"
                      for s in c["similar"])
    rows.append({"colour": GOOD if c["p_reach"] >= .5 else (GOLD if c["p_reach"] >= .25 else POOR),
                 "cells": [(c["driver"], c["path"]), (c["p_reach"], f"{c['p_reach']:.0%}"), alike]})
board([("Driver", "label"), ("Chance of reaching F1", "bar"), ("Closest past records", "text")], rows, ranked=True)
st.caption("A chance, not a verdict: seats also depend on money, a junior programme, timing and who retires.")

# ---------- what a record is worth ----------
section("What a feeder record is worth", "How often each kind of record led to Formula 1, from the drivers whose "
        "careers have had time to play out.")


def bucket(p):
    if p == 1:
        return "F2 champion"
    if p <= 3:
        return "2nd–3rd in F2"
    if p <= 6:
        return "4th–6th in F2"
    if p <= 10:
        return "7th–10th in F2"
    if p < S.NONE:
        return "Below 10th in F2"
    return "Never raced in F2"


order = ["F2 champion", "2nd–3rd in F2", "4th–6th in F2", "7th–10th in F2", "Below 10th in F2", "Never raced in F2"]
hist["bucket"] = hist["f2_best"].map(bucket)
g = hist.groupby("bucket").agg(n=("reached", "size"), rate=("reached", "mean"), starts=("starts", "median"))
rows = [{"colour": GOOD if g.loc[b, "rate"] >= .5 else (GOLD if g.loc[b, "rate"] >= .2 else POOR),
         "cells": [(b, f"{int(g.loc[b, 'n'])} drivers"), (g.loc[b, "rate"], f"{g.loc[b, 'rate']:.0%}")]}
        for b in order if b in g.index]
board([("Best F2/GP2 season", "label"), ("Reached Formula 1", "bar")], rows)

mates = hist.assign(side=hist["beat_teammate"].map(lambda v: "Usually beat their team-mate" if v > .5 else
                                                     ("Even with their team-mate" if v == .5 else "Usually lost to their team-mate")))
gm = mates.groupby("side")["reached"].agg(["size", "mean"])
board([("Against the team-mate, same car", "label"), ("Reached Formula 1", "bar")],
      [{"colour": GOOD if v["mean"] >= .2 else POOR, "cells": [(k, f"{int(v['size'])} drivers"), (v["mean"], f"{v['mean']:.0%}")]}
       for k, v in gm.sort_values("mean", ascending=False).iterrows()])

# ---------- surprises ----------
scored = hist.dropna(subset=["p_cv"])
left, right = st.columns(2)
with left:
    section("Strong records that never made it", "The highest chances, from the honest test, for drivers who never "
            "started a Grand Prix.")
    miss = scored[scored["reached"] == 0].sort_values("p_cv", ascending=False).head(8)
    board([("Driver", "label"), ("Chance", "bar")],
          [{"colour": POOR, "cells": [(x["driver"], x["path"]), (x["p_cv"], f"{x['p_cv']:.0%}")]} for _, x in miss.iterrows()])
with right:
    section("Made it against the odds", "The lowest chances for drivers who did reach Formula 1.")
    odds = scored[scored["reached"] == 1].sort_values("p_cv").head(8)
    board([("Driver", "label"), ("Chance", "bar")],
          [{"colour": GOOD, "cells": [(x["driver"], f"{x['path']} · {x['starts']} F1 starts"), (x["p_cv"], f"{x['p_cv']:.0%}")]}
           for _, x in odds.iterrows()])

# ---------- calibration ----------
section("Can its percentages be trusted?", "Drivers grouped by the chance the model gave them on eras it never saw, "
        "against how many really reached F1.")
bins = pd.cut(scored["p_cv"], [0, .05, .15, .3, .5, .75, 1.0], include_lowest=True)
cal = scored.groupby(bins, observed=True).agg(n=("reached", "size"), said=("p_cv", "mean"), real=("reached", "mean"))
board([("Model said", "label"), ("Really reached F1", "bar"), ("Drivers", "num")],
      [{"colour": GOOD if abs(v["said"] - v["real"]) < .12 else GOLD,
        "cells": [(f"{v['said']:.0%} on average", f"{max(iv.left, 0):.0%}–{iv.right:.0%}"), (v["real"], f"{v['real']:.0%}"), f"{int(v['n'])}"]}
       for iv, v in cal.iterrows()])

st.caption(f"How it works: each driver's F2/GP2 and F3/GP3 record (best championship places, share of the champion's "
           f"points, wins, podiums, beating the team-mate, Super Licence points) goes into a logistic regression, "
           f"trained only on careers that ended at least {r['window']} seasons ago and tested by leaving out whole groups "
           f"of seasons. What it can't see: money, junior programmes, age, other series (Formula Regional, IndyCar, "
           f"Japan) and the seats available each year. Results from Wikipedia's season articles (CC BY-SA 4.0).")
