"""Career Mode rules: from F4 at 15 to Formula 1, one season at a time.

The page keeps a career (a plain dict) in the visitor's session and calls next_season() with their choices.

A SEASON is drawn from real seasons (career.json): drivers in the same series at the same kind of team.
Your hidden TALENT sets where in that pool you usually land, against a field that gets better at every step
(F2 drivers are better than F3 drivers, F1 drivers better still), plus a little for experience in that series
and plenty of luck. PUSHING moves the season up or down the pool with equal chances.

MONEY: junior seats cost money (front-running teams most), results bring sponsors, and a junior programme
pays most of the bill once you've won a lot. If you can't afford any seat, the career ends.

SUPER LICENCE points use the FIA's real table. Formula 1 teams look at your F3 and F2 record with the
Scouting Report's model (scouting.py): its chance becomes the chance of an offer after each F2 season,
provided you have the 40 Super Licence points.

In F1 you're paid instead of paying; strong seasons bring offers from better teams and two poor seasons at
the back end it. The ladder closes if you're 27 without an F1 seat.
"""
import json
import math
import random
from pathlib import Path

import ladder as L
import scouting as S

POOLS = json.loads((L.OUT / "career.json").read_text(encoding="utf-8"))
SCOUT = json.loads(S.OUT.read_text(encoding="utf-8"))["model"]
SL = L.load()[2]

SERIES = ["F4", "F3", "F2", "F1"]
NAMES = {"F4": "Formula 4", "F3": "Formula 3", "F2": "Formula 2", "F1": "Formula 1"}
SL_ROW = {"F4": "FIA Formula 4 Championships", "F3": "FIA Formula 3 Championship", "F2": "FIA Formula 2 Championship"}
COST = {"F4": {"front": 0.5, "mid": 0.35, "back": 0.2}, "F3": {"front": 1.4, "mid": 0.9, "back": 0.6},
        "F2": {"front": 2.6, "mid": 1.8, "back": 1.1}}                     # million a season
SPONSOR = {"F4": 0.45, "F3": 1.1, "F2": 2.0}                                  # best case, million
SALARY = {"front": 10.0, "mid": 3.0, "back": 1.0}
BACKING = {"Modest (0.8 million)": 0.8, "Solid (2 million)": 2.0, "Wealthy (5 million)": 5.0}
MAX_SEASONS = {"F4": 3, "F3": 4}                                           # nobody stays longer than this
TIERS = {"front": "Front-running team", "mid": "Midfield team", "back": "Back-of-the-grid team"}
F1_RACES = 22


def new_career(backing, seed=None):
    rng = random.Random(seed)
    return {"age": 15, "year": 2027, "budget": BACKING[backing], "talent": round(rng.betavariate(3, 3), 3),
            "series": "F4", "f1_tier": None, "academy": False, "history": [], "over": None, "offer": None,
            "seed": rng.randrange(10 ** 9), "poor_f1": 0}


def _rng(c):
    return random.Random(c["seed"] + len(c["history"]))


def seasons_in(c, series):
    return sum(h["series"] == series for h in c["history"])


def options(c):
    """What the visitor can choose for next season: [(series, tier, cost or salary)]."""
    if c["over"]:
        return []
    if c["series"] == "F1":
        return [("F1", c["f1_tier"], SALARY[c["f1_tier"]])]
    out = []
    here = SERIES.index(c["series"])
    for series in SERIES[here:here + 2]:
        if series == "F1" or (series == "F2" and c["series"] == "F4"):
            continue
        if seasons_in(c, series) >= MAX_SEASONS.get(series, 99):
            continue
        for tier in ("front", "mid", "back"):
            cost = COST[series][tier] * (0.3 if c["academy"] else 1.0)
            if cost <= c["budget"] + 1e-9:
                out.append((series, tier, round(cost, 2)))
    return out


def sl_window(c, upto=None):
    """Super Licence points over the last three seasons."""
    pts = {}
    for h in c["history"]:
        pts[h["year"]] = max(pts.get(h["year"], 0), h["sl"])
    last = upto or (c["year"] - 1)
    return sum(pts.get(y, 0) for y in (last - 2, last - 1, last))


def _sl(series, pos):
    if series not in SL_ROW or not 1 <= pos <= 10:
        return 0.0
    row = SL[SL["series"] == SL_ROW[series]]
    return float(row.iloc[0][f"p{pos}"]) if len(row) else 0.0


# Each step up, the field is better: your talent counts for less against it.
FIELD = {"F4": -0.12, "F3": 0.05, "F2": 0.2, "F1": 0.32}
SPREAD = 5.0            # how much a season varies around your level (a Beta distribution's concentration)


def draw(c, series, tier, push, rng):
    """Your season: a real season from the pool, at a percentile set by your level plus luck."""
    pool = sorted(POOLS["F3" if series == "F4" else series][tier], key=lambda r: r["place"])
    level = c["talent"] - FIELD[series] + 0.05 * min(seasons_in(c, series), 2)
    mean = min(max(1 - level, 0.03), 0.97)                 # where in the pool you'd usually land (0 = best)
    u = rng.betavariate(mean * SPREAD, (1 - mean) * SPREAD)
    note = ""
    if push:
        if rng.random() < 0.5:
            u, note = u * 0.65, "Pushing paid off."
        else:
            u, note = u + (1 - u) * 0.45, "Pushing cost you: too many incidents."
    return pool[min(int(u * len(pool)), len(pool) - 1)], note


def record(c):
    """The Scouting Report's numbers for this career's F3 and F2 seasons."""
    f3 = [h for h in c["history"] if h["series"] == "F3"]
    f2 = [h for h in c["history"] if h["series"] == "F2"]
    ahead = [h["ahead"] for h in f2 + f3 if h.get("ahead") is not None]
    years = sorted({h["year"] for h in c["history"]})
    return {"f3_best": min((h["pos"] for h in f3), default=S.NONE), "f2_best": min((h["pos"] for h in f2), default=S.NONE),
            "f2_rookie": f2[0]["pos"] if f2 else S.NONE, "f3_share": max((h["share"] for h in f3), default=0.0),
            "f2_share": max((h["share"] for h in f2), default=0.0), "f2_wins": sum(h["wins"] for h in f2),
            "f2_podiums": sum(h["podiums"] for h in f2),
            "beat_teammate": sum(ahead) / len(ahead) if ahead else 0.5,
            "sl_peak": max((sl_window(c, y) for y in years), default=0.0)}


def f1_chance(c):
    return float(S.chance(SCOUT, record(c)))


def next_season(c, series, tier, push):
    """Race one season. Returns the updated career (a new dict)."""
    c = json.loads(json.dumps(c))
    rng = _rng(c)
    r, note = draw(c, series, tier, push, rng)
    entry = {"year": c["year"], "age": c["age"], "series": series, "tier": tier, "pos": r["pos"],
             "points": r["points"], "wins": r["wins"], "podiums": r.get("podiums", 0), "share": r["share"],
             "ahead": r.get("ahead"), "like": f"{r['driver']} ({r['season']}, {r['team']})", "note": note,
             "sl": _sl(series, r["pos"]), "push": push}
    if series == "F1":
        c["budget"] += SALARY[tier]
        entry["money"] = SALARY[tier]
    else:
        cost = COST[series][tier] * (0.3 if c["academy"] else 1.0)
        income = round(SPONSOR[series] * (1 - r["place"]) ** 2, 2)
        c["budget"] = round(c["budget"] - cost + income, 2)
        entry["money"] = round(income - cost, 2)
    c["history"].append(entry)
    c["series"] = series
    c["year"] += 1
    c["age"] += 1
    c["offer"] = None

    if r["place"] <= (0.03 if series == "F4" else 0.1) and series != "F1" and not c["academy"]:
        c["academy"] = True
        entry["note"] += " An F1 team's junior programme signed you: it now pays most of your bills."
    if series == "F2" and sl_window(c) >= L.SL_NEEDED:
        p = f1_chance(c)
        per_season = 0.5 * p                     # teams decide one season at a time; seats are scarce
        if c["academy"]:
            per_season = min(0.9, per_season * 1.3)
        entry["f1_chance"] = round(p, 3)
        if rng.random() < per_season:
            c["offer"] = "mid" if p > 0.85 and rng.random() < 0.35 else "back"
    if series == "F1":
        if r["place"] <= 0.25 and tier != "front" and rng.random() < 0.6:
            c["f1_tier"] = "front" if tier == "mid" else "mid"
            entry["note"] += f" A {TIERS[c['f1_tier']].lower()} wants you next year."
        c["poor_f1"] = c["poor_f1"] + 1 if (tier == "back" and r["place"] >= 0.8) else 0
        if c["poor_f1"] >= 2:
            c["over"] = "Two poor seasons at the back: no team renewed your contract."
        elif c["age"] >= 38:
            c["over"] = "You retired from Formula 1."
    elif not c["offer"]:
        if c["age"] >= 27:
            c["over"] = "The ladder closed: 27 and no F1 seat."
        elif not options(c):
            c["over"] = "The money ran out: no seat you could afford."
    return c


def accept_offer(c):
    c = dict(c)
    c["series"], c["f1_tier"], c["offer"] = "F1", c["offer"], None
    return c


def summary(c):
    f1 = [h for h in c["history"] if h["series"] == "F1"]
    return {"f1_seasons": len(f1), "f1_starts": len(f1) * F1_RACES, "f1_wins": sum(h["wins"] for h in f1),
            "titles": sum(h["pos"] == 1 for h in f1), "junior_titles": sum(h["pos"] == 1 for h in c["history"] if h["series"] != "F1")}


def autoplay(backing="Solid (2 million)", seed=None, push_p=0.3):
    """A simple bot career, used to check the game's balance."""
    c = new_career(backing, seed)
    rng = random.Random(seed)
    while not c["over"] and len(c["history"]) < 30:
        if c["offer"]:
            c = accept_offer(c)
        opts = options(c)
        if not opts:
            break
        here = [o for o in opts if o[0] == c["series"]]
        up = [o for o in opts if o[0] != c["series"]]
        stay = seasons_in(c, c["series"]) < (1 if c["series"] == "F4" else 2)
        pool = here if (stay and here) else (up or here)
        choice = min(pool, key=lambda o: ["front", "mid", "back"].index(o[1]))
        c = next_season(c, choice[0], choice[1], rng.random() < push_p)
    return c
