"""Team Principal: run a team for a real season. Budget cap, wind-tunnel time, upgrades, drivers, reliability.

THE GRID. Every other team's car follows its REAL pace through the season (pace_teams.csv: each race's
clean-lap pace as a % off the quickest team, smoothed over three races), so rivals develop exactly as they
did. Your car starts where your team really started (its first three races) and from then on only gets
faster through your decisions. The drivers' own pace is their gap to their teammates that season.

EACH TURN covers a block of races. You decide:
  development spend   from the cost cap's development budget. It buys development, scaled by your
                      wind-tunnel allowance, which (as in the real ATR rule) depends on your place in the
                      constructors' championship: 70% for the leader up to 115% for 10th
  the upgrade         the package built last turn can go straight on the car (it may not correlate with
                      the wind tunnel: then only part of it works) or be tested first (no risk, one turn later)
  engine mode         push (quicker, less reliable), normal, or save
Before the season you pick two drivers within a salary budget; a team that loses a driver to you runs a
reserve instead.

RACES. Each car's strength is its pace (car + driver + engine mode); a race is drawn the predictor's way
(strength plus Gumbel noise, Plackett-Luce) with retirements at each car's reliability rate, and points go
25-18-15-12-10-8-6-4-2-1. Money not spent on this year's car goes to next year's: the end screen says
what head start it buys. The game numbers (costs, gains, risks) are illustrative; the rivals' pace is real.
"""
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEAMS = ROOT / "data" / "processed" / "pace_teams.csv"
DRIVERS = ROOT / "data" / "processed" / "pace_drivers.csv"
POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
BLOCK = 4                       # races per turn
DEV_BUDGET = 90.0               # $M of the cap left for development after running the team
SALARY_BUDGET = 40.0            # $M for your two drivers
SIGMA = 0.28                    # % of lap time that one unit of race noise is worth
GAIN_PER_M = 0.0045             # % lap time per $M of development at a 100% wind-tunnel allowance
DIMINISH = 60.0                 # $M: a block's development gives less the more is spent at once
MISS = 0.18                     # chance a rushed package doesn't correlate
MISS_KEEPS = 0.35               # share of the gain a package that doesn't correlate keeps
RESERVE = 0.25                  # % a reserve driver is slower than the team's average
MODES = {"push": (-0.08, 0.11), "normal": (0.0, 0.055), "save": (0.06, 0.03)}   # (pace %, retirement chance)
NEXT_YEAR_PER_M = 0.006         # % head start next year per unspent $M (illustrative)


def atr(position):
    """Wind-tunnel allowance by constructors' position (2021+ sliding scale, simplified)."""
    return min(1.15, 0.70 + 0.05 * (position - 1))


def seasons():
    t = pd.read_csv(TEAMS)
    return sorted(t["season"].unique().tolist(), reverse=True)


def setup(season):
    """The season's races, every team's real pace trajectory, and the drivers with skills and salaries."""
    t = pd.read_csv(TEAMS)
    t = t[t["season"] == season]
    rounds = t[["round", "race_name"]].drop_duplicates().sort_values("round")
    pace = t.pivot_table(index="round", columns="constructor", values="pct_off").sort_index()
    pace = pace.rolling(3, min_periods=1, center=True).median().ffill().bfill()
    d = pd.read_csv(DRIVERS)
    d = d[d["season"] == season].copy()
    d["gap"] = d["pct_off"] - d.groupby(["round", "team_id"])["pct_off"].transform("mean")   # against the team's average
    starts = d.groupby(["driver", "team_id"]).size().rename("n").reset_index()
    main = starts.sort_values("n").groupby("driver").tail(1)
    skill = d.groupby("driver").agg(code=("code", "first"), gap=("gap", "median"), races=("round", "nunique"))
    drivers = []
    for r in main.itertuples():
        if r.n < 3:
            continue
        g = float(skill.loc[r.driver, "gap"])
        drivers.append({"driver": r.driver, "code": skill.loc[r.driver, "code"], "team": r.team_id,
                        "skill": round(-g, 3), "salary": float(np.clip(round(10 + 80 * -g), 2, 30))})
    lineup = {}
    for dr in sorted(drivers, key=lambda x: -x["skill"]):
        lineup.setdefault(dr["team"], [])
        if len(lineup[dr["team"]]) < 2:
            lineup[dr["team"]].append(dr["driver"])
    teams = [c for c in pace.columns if lineup.get(c)]
    for c in teams:                                         # a driver missing from the pace data: a reserve
        lineup[c] = (lineup[c] + ["RESERVE"])[:2]
    return {"season": season, "rounds": rounds.to_dict("records"), "pace": pace[teams].round(3).to_dict(),
            "drivers": {x["driver"]: x for x in drivers if x["team"] in teams}, "lineup": {k: lineup[k] for k in teams}}


def new_game(world, team, picks, seed=None):
    rng = random.Random(seed)
    rounds = [r["round"] for r in world["rounds"]]
    start = float(np.mean([world["pace"][team][r] for r in rounds[:3]]))
    return {"team": team, "drivers": list(picks), "car": start, "start": start, "spent": 0.0, "factory": 0.0,
            "testing": 0.0, "block": 0, "seed": rng.randrange(10 ** 9), "points": {}, "results": [], "log": [],
            "over": False}


def lineups(world, g):
    """Each team's two drivers this season, with your picks and reserves where you poached."""
    out = {t: list(v) for t, v in world["lineup"].items()}
    for t, v in out.items():
        out[t] = ["RESERVE" if ((d in g["drivers"] and t != g["team"]) or d not in world["drivers"]) else d for d in v]
    out[g["team"]] = list(g["drivers"])
    return out


def standings(g):
    return sorted(g["points"].items(), key=lambda x: -x[1])


def position(g):
    order = [t for t, _ in standings(g)]
    return order.index(g["team"]) + 1 if g["team"] in order else len(order) // 2 + 1


def play_block(world, g, spend, upgrade, mode):
    """One turn: fit or test the waiting package, develop the next, run BLOCK races."""
    rng = random.Random(g["seed"] + g["block"])
    nprng = np.random.default_rng(g["seed"] + g["block"])
    notes = []
    # 1. the package built last turn
    if g["factory"] > 0:
        if upgrade == "now":
            if rng.random() < MISS:
                gain = g["factory"] * MISS_KEEPS
                notes.append(f"The upgrade didn't correlate with the wind tunnel: only {gain:.2f}% of {g['factory']:.2f}% worked.")
            else:
                gain = g["factory"]
                notes.append(f"The upgrade works: {gain:.2f}% quicker.")
            g["car"] -= gain
        else:
            g["testing"] += g["factory"]
            notes.append(f"The {g['factory']:.2f}% package is in testing; it goes on the car next turn, guaranteed.")
        g["factory"] = 0.0
    elif g["testing"] > 0:
        pass
    if g["testing"] > 0 and upgrade != "test-again":
        if not any("is in testing" in n for n in notes):
            g["car"] -= g["testing"]
            notes.append(f"The tested package goes on: {g['testing']:.2f}% quicker.")
            g["testing"] = 0.0
    # 2. development this turn, scaled by the wind-tunnel allowance
    spend = float(min(spend, DEV_BUDGET - g["spent"]))
    allowance = atr(position(g)) if g["points"] else 1.0
    gain = GAIN_PER_M * DIMINISH * (1 - math.exp(-spend / DIMINISH)) * allowance
    g["spent"] += spend
    g["factory"] = gain
    if spend:
        notes.append(f"${spend:.0f}M of development at {allowance:.0%} wind-tunnel time: a {gain:.2f}% package for next turn.")
    # 3. the races
    rounds = world["rounds"][g["block"] * BLOCK:(g["block"] + 1) * BLOCK]
    line = lineups(world, g)
    for rr in rounds:
        cars = []
        for team, ds in line.items():
            base = g["car"] if team == g["team"] else world["pace"][team][rr["round"]]
            pm, dnf = MODES[mode] if team == g["team"] else MODES["normal"]
            team_avg = np.mean([world["drivers"][d]["skill"] for d in world["lineup"][team] if d in world["drivers"]])
            for d in ds:
                skill = -RESERVE if d == "RESERVE" else world["drivers"][d]["skill"] - (team_avg if team != g["team"] else 0)
                cars.append((team, d, base + pm - skill, dnf))
        strength = np.array([-c[2] / SIGMA for c in cars]) + nprng.gumbel(size=len(cars))
        out = nprng.random(len(cars)) < np.array([c[3] for c in cars])
        strength[out] = -1e9
        order = np.argsort(-strength)
        res = []
        for pos, i in enumerate(order, start=1):
            team, d, _, _ = cars[i]
            pts = POINTS[pos - 1] if pos <= 10 and not out[i] else 0
            g["points"][team] = g["points"].get(team, 0) + pts
            res.append({"pos": pos, "team": team, "driver": d, "dnf": bool(out[i]), "pts": pts})
        g["results"].append({"round": rr["round"], "race_name": rr["race_name"], "order": res})
    g["log"].append({"block": g["block"], "spend": spend, "upgrade": upgrade, "mode": mode, "notes": notes,
                     "car": round(g["car"], 3), "position": position(g)})
    g["block"] += 1
    if g["block"] * BLOCK >= len(world["rounds"]):
        g["over"] = True
    return g


SAME_TEAM = {"alfa": "audi", "sauber": "audi", "alphatauri": "rb"}      # results.csv ids -> pace file ids


def real_points(season):
    """The real constructors' points that season (Jolpica results), for the comparison at the end."""
    r = pd.read_csv(ROOT / "data" / "processed" / "results.csv")
    r = r[r["season"] == season].assign(constructor=lambda x: x["constructor"].replace(SAME_TEAM))
    return r.groupby("constructor")["points"].sum().sort_values(ascending=False).to_dict()


def next_year(g):
    return (DEV_BUDGET - g["spent"]) * NEXT_YEAR_PER_M
