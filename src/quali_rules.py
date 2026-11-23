"""Qualifying Game rules: Q1, Q2 and Q3 against the real laps of a real session.

You take the place of a team's quicker driver. Your car's potential at minute m of the session is the
team's best real lap carried to that minute with the session's measured track evolution (the track gets
faster as rubber goes down). Each segment you choose:
  when to run   early (clear track, slower surface), late (faster surface, but traffic and yellow flags),
                or both (two new sets of tyres)
  the tow       a slipstream down the straights: worth more where the lap is mostly full throttle, but
                you may be badly placed
  how hard      a safe lap, or on the limit (quicker on average, but a mistake or a deleted lap)
Your best time goes up against the real drivers' real best laps in that segment, and the real cut lines
decide who goes through.

The game numbers (risks and gains) are illustrative; the lap times, cut lines and evolution are real.
"""
import json
import random
from pathlib import Path

import quali_game as Q

DATA = {r["folder"]: r for r in json.loads(Q.OUT.read_text(encoding="utf-8"))} if Q.OUT.exists() else {}
TOURS = Path(__file__).resolve().parent.parent / "data" / "processed" / "circuit_tours.json"
FULL = {}
if TOURS.exists():
    for t in json.loads(TOURS.read_text(encoding="utf-8")):
        FULL[t["race_name"]] = t["full_throttle"]

WINDOW = {1: (4.0, 15.5), 2: (28.0, 37.5), 3: (51.0, 57.5)}       # minute of an early and a late run
NEW_SETS = 4
USED_TYRE = 0.35          # s slower on a used set
SIGMA = {"safe": 0.07, "limit": 0.09}
LIMIT_GAIN = 0.08
MISTAKE = 0.6
CARRY = 12.0              # minutes a lap may be carried along the track evolution


def teams(race):
    out = {}
    for d in race["drivers"]:
        out.setdefault(d["team"], []).append(d)
    return out


def potential(race, team, minute):
    """The team's best real lap, carried to `minute` with the session's track evolution."""
    best = None
    for d in teams(race)[team]:
        for b in d["best"].values():
            # the fitted evolution holds over minutes, not a whole session: carry a lap at most CARRY minutes
            t = b["time"] + race["evolution"] * max(-CARRY, min(CARRY, minute - b["min"]))
            best = t if best is None else min(best, t)
    return best


def replaced(race, team):
    """The team's quicker driver (best lap of the session): the one you stand in for."""
    return min(teams(race)[team], key=lambda d: min(b["time"] for b in d["best"].values()))


def new_game(folder, team, seed=None):
    race = DATA[folder]
    rng = random.Random(seed)
    return {"folder": folder, "team": team, "seg": 1, "sets": NEW_SETS, "best": {}, "log": [], "over": False,
            "seed": rng.randrange(10 ** 9), "you_for": replaced(race, team)["code"]}


def field(race, g, seg):
    """The real rivals in this segment: everyone but the driver you replace, with a lap in this segment.
    If you reached a segment your driver didn't, the slowest real qualifier for it makes way."""
    key = str(seg)                                 # segment keys are strings once saved as JSON
    rivals = [d for d in race["drivers"] if d["code"] != g["you_for"] and key in d["best"]]
    t = lambda d: d["best"][key]["time"]
    rivals.sort(key=t)
    limit = {1: len(race["drivers"]), 2: race["q2"], 3: race["q3"]}[seg] - 1
    return [(d, t(d)) for d in rivals[:limit]]


def run_segment(g, plan, tow, push):
    race = DATA[g["folder"]]
    rng = random.Random(g["seed"] + g["seg"])
    seg = g["seg"]
    early, late = WINDOW[seg]
    runs = {"early": [early], "late": [late], "both": [early, late]}[plan]
    laps, notes = [], []
    tow_gain = 0.04 + 0.2 * FULL.get(race["race_name"], 0.6) ** 2      # about 0.1-0.2 s, most at power circuits
    for minute in runs:
        new = g["sets"] > 0
        if new:
            g["sets"] -= 1
        t = potential(race, g["team"], minute) + (0 if new else USED_TYRE)
        if not new:
            notes.append("no new tyres left: a used set (+0.35 s)")
        if tow:
            if rng.random() < 0.7:
                t -= tow_gain
                notes.append(f"a good tow (−{tow_gain:.2f} s)")
            else:
                t += 0.3
                notes.append("badly placed for the tow (+0.30 s)")
        if push == "limit":
            t -= LIMIT_GAIN
            r = rng.random()
            if r < 0.07:
                notes.append("track limits: lap deleted")
                continue
            if r < 0.22:
                t += MISTAKE
                notes.append("a lock-up at the hairpin (+0.6 s)")
        t += rng.gauss(0, SIGMA[push])
        if minute == late:
            r = rng.random()
            if r < 0.10:
                notes.append("yellow flag on your last lap: abandoned")
                continue
            if r < 0.30:
                t += 0.25
                notes.append("traffic in the final sector (+0.25 s)")
        laps.append(round(t, 3))
    best = min(laps) if laps else None
    rivals = field(race, g, seg)
    order = sorted([(d["code"], d["team"], d["colour"], tm) for d, tm in rivals] + [("YOU", g["team"], "#e10600", best if best else 999.0)],
                   key=lambda x: x[3])
    pos = [o[0] for o in order].index("YOU") + 1
    through = {1: race["q2"], 2: race["q3"], 3: 99}[seg]
    entry = {"seg": seg, "laps": laps, "best": best, "pos": pos, "of": len(order), "notes": notes,
             "cut": order[through - 1][3] if seg < 3 and len(order) >= through else None, "order": order,
             "plan": plan, "tow": tow, "push": push}
    g["log"].append(entry)
    if seg == 3 or pos > through or best is None:
        g["over"] = True
        g["grid"] = pos                            # out in this segment: your place in it is your grid slot
    else:
        g["seg"] += 1
    return g


def real_result(race, g):
    d = next(x for x in race["drivers"] if x["code"] == g["you_for"])
    segs = sorted(int(k) for k in d["best"])
    return d, segs[-1]
