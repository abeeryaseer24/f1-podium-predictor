"""Pit Wall strategist: a race engineer for every driver.

At the end of every lap it looks at the race so far and keeps ONE plan per driver
("box on lap 24 for Hards"). It talks on the radio only when something happens:
  plan made or changed, "box in 2 laps", "Box... box...", missed call, safety car chance,
  undercut threat, pit stop done, no more stops needed.

It starts each race with what it learned from EARLIER races (tyre_book.py): how hard this circuit
is on tyres, how long teams run them here, the pit stop loss, and a pit-timing model of when
real teams tend to stop. The simulation says what is fastest; the pit-timing model keeps it realistic.

THE NO-FUTURE RULE: the plan at the end of lap L is made by engineer_step(), which only ever
receives laps, pit stops and race control messages up to lap L, plus knowledge from earlier
races. checks.py re-runs the first half of a race from truncated data and compares, to prove it.

Simple, stated assumptions:
- tyres lose time in a straight line with age, plus a "cliff" near the end of their life
- dry races must use two different dry compounds; wet laps get no plan
- a stop under a safety car costs 55% of a normal stop (70% under a virtual safety car)
- rivals run at their own pace; nobody else's plan reacts to ours

Usage:
  python src/strategy.py 2026 19               one race (prints how it compares with reality)
  python src/strategy.py --missing --limit 10  races that don't have a strategy file yet
  python src/strategy.py --all                 rebuild every race (after changing the strategist)
"""
import argparse
import json
import re

import numpy as np
import pandas as pd

from predictor import RACES_DIR
from tyre_book import book_for, features as timing_features, hazard, pit_model_for, real_pits
from tyres import MIN_LAPS, clean_laps, design, fit, pit_loss

DRY = ["SOFT", "MEDIUM", "HARD"]
SHORT = {"SOFT": "Softs", "MEDIUM": "Mediums", "HARD": "Hards"}

# Typical values, used until the race shows more
PRIOR_OFFSET = {"SOFT": -0.5, "MEDIUM": 0.0, "HARD": 0.4}
PRIOR_WEAR = {"SOFT": 0.09, "MEDIUM": 0.05, "HARD": 0.03}
PRIOR_FUEL = -0.045
PRIOR_PIT_LOSS = 22.0
PRIOR_WEIGHT = 80               # how many laps of evidence the typical values are worth
MIN_CLEAN = 150                 # clean laps needed before the race's own numbers are used
MIN_DRIVERS = 3                 # a compound needs laps from at least this many drivers
MIN_STOPPED = 8                 # cars that must have pitted before the race's own fuel effect is used
FUEL_TRUST = 20                 # ...and how many stopped cars before it is fully trusted
FUEL_RANGE = (-0.09, -0.02)      # sensible limits for the estimates (seconds)
OFFSET_RANGE = (-1.5, 1.5)
WEAR_RANGE = (0.0, 0.2)

# How long a set of tyres can last (until the tyre book knows better), and its cliff
TYRE_LIFE = {"SOFT": 35, "MEDIUM": 45, "HARD": 55}
TIMING_WEIGHT = 20.0            # seconds per unit of "how unusual would a real team find this stop"
CLIFF_START = 0.85              # the cliff starts at 85% of the tyre's life
CLIFF_RATE = 0.04               # extra seconds per lap, growing with every lap past it

# How the engineer behaves
FIRST_PLAN_LAP = 5              # quiet for the opening laps
EARLIEST_STOP = 0.2             # no planned stop before 20% of the race (unless a safety car)
MIN_STINT = 8                   # a new set of tyres runs at least this many laps
MISS_HOLD = 4                   # after a missed call, wait at least this many laps (more after each miss)
REPLAN_FAR = 2.5                # seconds better needed to move a stop that is 6+ laps away
REPLAN_GAIN = 4.0               # ...and one that is closer (never changed in the last 2 laps)
COVER_COST = 4.0                # covering an undercut is fine if it costs less than this
UNDERCUT_GAP = 2.5              # seconds: a car this close behind can undercut
SC_FACTOR = {"SC": 0.55, "VSC": 0.7}
RED_FLAG = re.compile(r"\bRED FLAG\b")   # careful: "CHEQUERED FLAG" also contains "RED FLAG"

LAP_NOISE = 0.6                 # seconds of random variation per lap (for finish ranges)
RUNS = 200


# ---------- what the race has shown so far ----------

def default_knowledge():
    """What the strategist assumes when it has no earlier races to learn from."""
    return {"book": {"offset": dict(PRIOR_OFFSET), "wear": dict(PRIOR_WEAR), "life": dict(TYRE_LIFE),
                     "pit_loss": PRIOR_PIT_LOSS, "first_stop": 0.4, "source": "typical values",
                     "wear_factor": 1.0, "stint_factor": 1.0},
            "pit_model": None}


def tyre_model(laps, knowledge=None):
    """Fuel, compound offsets and wear, from the laps so far, blended with what earlier races
    taught us (or typical values). Early in a race there is little data, so every estimate is
    kept inside sensible limits."""
    knowledge = knowledge or default_knowledge()
    book = knowledge["book"]
    prior_offset, prior_wear = book["offset"], book["wear"]
    model = {"fuel": PRIOR_FUEL, "offset": dict(prior_offset), "wear": dict(prior_wear),
             "pit_loss": pit_loss(laps) or book["pit_loss"], "life": dict(book["life"]),
             "book": book, "pit_model": knowledge.get("pit_model")}
    clean = clean_laps(laps)
    clean = clean[clean["compound"].isin(DRY)]
    drivers_on = clean.groupby("compound")["driver_number"].nunique()
    counts = clean["compound"].value_counts()
    comps = [c for c in DRY if counts.get(c, 0) >= MIN_LAPS and drivers_on.get(c, 0) >= MIN_DRIVERS]
    if not comps or len(clean) < MIN_CLEAN:
        return model

    data = clean[clean["compound"].isin(comps)]
    drivers = sorted(data["driver_number"].unique())
    nd, nc = len(drivers), len(comps)
    stopped = laps.loc[laps["is_pit_out_lap"].fillna(False).astype(bool)
                       & (laps["lap_number"] > 1), "driver_number"].nunique()
    fuel = PRIOR_FUEL                                         # first stint: fuel and wear can't be told apart
    if stopped >= MIN_STOPPED:                                # more stops: trust the race's own fuel effect, slowly
        fitted = float(np.clip(fit(data, drivers, comps)[nd], *FUEL_RANGE))
        fuel = PRIOR_FUEL + (fitted - PRIOR_FUEL) * min(1.0, stopped / FUEL_TRUST)
    X = np.delete(design(data, drivers, comps), nd, axis=1)
    y = data["lap_duration"].to_numpy(dtype=float) - fuel * data["lap_number"].to_numpy(dtype=float)
    coef = np.insert(np.linalg.lstsq(X, y, rcond=None)[0], nd, fuel)
    offsets = [0.0] + list(coef[nd + 1: nd + nc])
    wear = coef[nd + nc:]

    model["fuel"] = fuel
    shift = prior_offset[comps[0]]            # put the fitted offsets on the same scale as the priors
    for c, o, wr in zip(comps, offsets, wear):
        wc = counts[c] / (counts[c] + PRIOR_WEIGHT)
        o = float(np.clip(o + shift, *OFFSET_RANGE))
        wr = float(np.clip(wr, *WEAR_RANGE))
        model["offset"][c] = wc * o + (1 - wc) * prior_offset[c]
        model["wear"][c] = wc * wr + (1 - wc) * prior_wear[c]
    return model


def base_pace(laps, model):
    """Each driver's pace with fuel and tyres taken out (median of their last 5 clean laps)."""
    clean = clean_laps(laps)
    clean = clean[clean["compound"].isin(DRY)]
    if clean.empty:
        return {}, laps["lap_duration"].median()
    adj = (clean["lap_duration"] - model["fuel"] * clean["lap_number"]
           - clean["compound"].map(model["offset"])
           - clean["compound"].map(model["wear"]) * clean["tyre_age"])
    clean = clean.assign(adj=adj)
    recent = clean.sort_values("lap_number").groupby("driver_number").tail(5)
    return recent.groupby("driver_number")["adj"].median().to_dict(), float(adj.median())


def neutralised(control, when):
    """'SC', 'VSC', 'RED' or None: the race status at time `when` (from messages up to then)."""
    if control.empty:
        return None
    status = None
    for msg in control[control["t"] <= when].sort_values("t")["message"].fillna("").str.upper():
        if RED_FLAG.search(msg):
            status = "RED"
        elif "VSC DEPLOYED" in msg or "VIRTUAL SAFETY CAR DEPLOYED" in msg:
            status = "VSC"
        elif "SAFETY CAR DEPLOYED" in msg:
            status = "SC"
        elif any(w in msg for w in ("VSC ENDING", "VIRTUAL SAFETY CAR ENDING", "SAFETY CAR IN THIS LAP")):
            status = None
        elif status == "RED" and ("TRACK CLEAR" in msg or "RESUM" in msg):
            status = None                                      # the race is getting going again
    return status


# ---------- the cost of a plan ----------

def stint_cost(model, comp, age0, n):
    """Seconds lost to tyres over n laps on `comp`, starting at age `age0` (n can be an array)."""
    n = np.asarray(n, dtype=float)
    life = model["life"][comp]
    ages_end = age0 + n
    linear = n * model["offset"][comp] + model["wear"][comp] * (age0 * n + n * (n - 1) / 2)
    start = CLIFF_START * life                                  # cliff: sum of (age - start) past it
    over_end = np.maximum(0.0, ages_end - start)
    over_begin = max(0.0, age0 - start)
    cliff = CLIFF_RATE * (over_end * (over_end + 1) - over_begin * (over_begin + 1)) / 2
    return linear + cliff


def timing_cost(st, model, L, total):
    """How unusual each possible first-stop lap would look to a real team, in seconds:
    (stop on lap p) for p = L+1 .. total, and (no more stops). Zero without a pit-timing model,
    and after the first stop (tested: the model helps the first stop and hurts later ones)."""
    k = np.arange(L + 1, total + 1)
    if model["pit_model"] is None or TIMING_WEIGHT == 0 or st.get("stops", 0) > 0:
        return np.zeros(len(k)), 0.0                            # used for the first stop only: that is where it is strong
    neutral = np.where(k == L + 1, float(st.get("neutral", False)), 0.0)
    X = timing_features(st["age"] + (k - L), st["compound"], k, total, st.get("stops", 0),
                        float(len(st["used"]) < 2), neutral, model["book"])
    h = np.clip(hazard(model["pit_model"], X), 1e-4, 1 - 1e-4)
    stay = -np.log(1 - h)
    before = np.concatenate([[0.0], np.cumsum(stay)[:-1]])      # staying out on every lap before p
    stop = before - np.log(h)
    never = float(stay[: max(0, total - 2 - L)].sum())
    return TIMING_WEIGHT * stop, TIMING_WEIGHT * never


def best_plan(st, model, L, total, earliest, loss):
    """The fastest plan from the end of lap L: (pit_lap, compound, cost) with pit_lap None for
    'no more stops'. Up to two more stops are considered; new tyres can't go past their life."""
    N = total - L                                               # laps left
    used = st["used"]
    life = {c: int(round(v)) for c, v in model["life"].items()}
    realism, never = timing_cost(st, model, L, total)
    options = []

    if len(used) >= 2:                                          # no more stops
        options.append((None, None, float(stint_cost(model, st["compound"], st["age"], N)) + never))

    first = max(L + 1, earliest)
    last = total - 3
    if first <= last:
        p = np.arange(first, last + 1)                          # in-lap of the next stop
        n1 = p - L                                              # laps still on these tyres
        now_cost = stint_cost(model, st["compound"], st["age"], n1) + realism[p - (L + 1)]
        rest = total - p                                        # laps after the stop
        for c in DRY:
            if len(used | {c}) < 2:
                continue                                        # must use two compounds
            ok = (rest <= life[c]) & (rest >= MIN_STINT)
            one = np.where(ok, now_cost + loss + stint_cost(model, c, 0, rest), np.inf)
            k = int(np.argmin(one))
            if np.isfinite(one[k]):
                options.append((int(p[k]), c, float(one[k])))
            for c2 in DRY:                                      # two more stops
                m = np.arange(MIN_STINT, life[c] + 1)
                r2 = rest[:, None] - m[None, :]
                ok2 = (r2 >= MIN_STINT) & (r2 <= life[c2])
                two = (now_cost[:, None] + 2 * model["pit_loss"] + (loss - model["pit_loss"])
                       + stint_cost(model, c, 0, m)[None, :]
                       + stint_cost(model, c2, 0, np.maximum(r2, 0)))
                two = np.where(ok2, two, np.inf)
                i, j = np.unravel_index(np.argmin(two), two.shape)
                if np.isfinite(two[i, j]):
                    options.append((int(p[i]), c, float(two[i, j])))
    if not options:
        return None
    return min(options, key=lambda o: o[2])


def plan_cost(st, model, L, total, pit_lap, comp, loss):
    """Cost of keeping a given plan (stop on `pit_lap` for `comp`), best finish after it."""
    realism, never = timing_cost(st, model, L, total)
    life = {c: int(round(v)) for c, v in model["life"].items()}
    if pit_lap is None:
        if len(st["used"]) < 2:
            return np.inf
        return float(stint_cost(model, st["compound"], st["age"], total - L)) + never
    if pit_lap <= L or pit_lap > total - 3 or len(st["used"] | {comp}) < 2:
        return np.inf
    n1, rest = pit_lap - L, total - pit_lap
    cost = float(stint_cost(model, st["compound"], st["age"], n1)) + loss + float(realism[pit_lap - (L + 1)])
    if rest <= life[comp]:
        return cost + float(stint_cost(model, comp, 0, rest))
    m = np.arange(MIN_STINT, life[comp] + 1)
    r2 = rest - m
    best = np.inf
    for c2 in DRY:
        ok = (r2 >= MIN_STINT) & (r2 <= life[c2])
        two = stint_cost(model, comp, 0, m) + model["pit_loss"] + stint_cost(model, c2, 0, np.maximum(r2, 0))
        if ok.any():
            best = min(best, float(two[ok].min()))
    return cost + best


# ---------- one lap of the engineer ----------

def car_states(laps, L):
    """Each car at the end of lap L: tyre, age, when it crossed the line, compounds used."""
    states = {}
    for d, mine in laps.groupby("driver_number"):
        now = mine[mine["lap_number"] == L]
        if now.empty:
            continue
        r = now.iloc[0]
        if pd.isna(r["t_start"]) or pd.isna(r["lap_duration"]):
            continue
        out_lap = pd.notna(r["is_pit_out_lap"]) and bool(r["is_pit_out_lap"])
        states[d] = {"compound": r["compound"], "age": float(r["tyre_age"]) if pd.notna(r["tyre_age"]) else 0.0,
                     "start": float(r["t_start"]), "end": float(r["t_start"] + r["lap_duration"]),
                     "out_lap": out_lap,
                     "position": int(r["position"]) if pd.notna(r.get("position")) else None,
                     "used": set(mine["compound"].dropna()) & set(DRY)}
    return states


def lap_time(st, model, base, k, L):
    """Predicted time of future lap k on the current tyres."""
    age = st["age"] + (k - L)
    return base + model["fuel"] * k + model["offset"][st["compound"]] + model["wear"][st["compound"]] * age


def rejoin_position(d, states, model, bases, L, pit_lap, loss):
    """Where the car is expected to come out of the pit lane: everyone keeps their pace to the stop."""
    k = np.arange(L + 1, pit_lap + 1)
    at_stop = {r: s["end"] + float(lap_time(s, model, bases[r], k, L).sum())
               for r, s in states.items() if s["compound"] in DRY}
    if d not in at_stop:
        return None
    mine = at_stop[d] + loss
    return 1 + sum(t < mine for r, t in at_stop.items() if r != d)


def finish_range(d, states, model, bases, L, total, plan_cost_d, best_costs):
    """Expected finish (and a likely range) with the current plan, against everyone's best plan."""
    k = np.arange(L + 1, total + 1)
    fuel_base = lambda r: bases[r] * len(k) + model["fuel"] * k.sum()
    mine = states[d]["end"] + fuel_base(d) + plan_cost_d
    rivals = [r for r in best_costs if r != d]
    if not rivals:
        return 1, 1, 1
    times = np.array([states[r]["end"] + fuel_base(r) + best_costs[r] for r in rivals])
    rng = np.random.default_rng(int(d) * 1000 + L)                 # same draws every time
    spread = LAP_NOISE * np.sqrt(len(k))
    own = mine + rng.normal(0, spread, RUNS)
    others = times + rng.normal(0, spread, (RUNS, len(rivals)))
    finish = 1 + (others < own[:, None]).sum(axis=1)
    return (round(float(finish.mean()), 1), int(np.percentile(finish, 10)), int(np.percentile(finish, 90)))


def say(memory, d, L, kind, text, rejoin=None, lap=None, at=0.0):
    """One radio message. `lap` is the lap the driver hears it on (normally the next one),
    `at` how many seconds into that lap."""
    memory[d]["radio"].append({"L": L, "lap": lap or L + 1, "at": round(at, 1),
                               "kind": kind, "text": text, "rejoin": rejoin})


def deployed_during(control, start, end):
    """'SC' or 'VSC' and the time, if one was deployed between `start` and `end`."""
    if control.empty:
        return None, None
    window = control[(control["t"] > start) & (control["t"] <= end)].sort_values("t")
    for t, msg in zip(window["t"], window["message"].fillna("").str.upper()):
        if "VSC DEPLOYED" in msg or "VIRTUAL SAFETY CAR DEPLOYED" in msg:
            return "VSC", float(t)
        if "SAFETY CAR DEPLOYED" in msg:
            return "SC", float(t)
    return None, None


def engineer_step(laps, pits, control, L, total, memory, knowledge=None):
    """The engineer's work at the end of lap L. `laps`, `pits` and `control` must only contain
    laps 1..L: that is the no-future rule. `memory` carries each driver's plan between laps."""
    states = car_states(laps, L)
    line = max((s["end"] for s in states.values()), default=0)     # the last car over the line on lap L
    if laps["lap_number"].max() > L or (len(pits) and pits["lap_number"].max() > L) \
            or (len(control) and control["t"].max() > line):
        raise ValueError("engineer_step was given future laps")

    stops = real_pits(pits, laps)
    pitted_now = set(stops.loc[stops["lap"] == L, "driver_number"])
    model = tyre_model(laps, knowledge)
    model_loss = model["pit_loss"]
    made = stops.groupby("driver_number").size().to_dict()
    for d, st in states.items():
        st["stops"] = int(made.get(d, 0))
        st["neutral"] = neutralised(control, st["end"]) in ("SC", "VSC")
    bases, fallback = base_pace(laps, model)
    bases = {d: bases.get(d, fallback) for d in states}
    earliest = max(round(EARLIEST_STOP * total), FIRST_PLAN_LAP + 1)
    order = sorted(states, key=lambda d: states[d]["end"])

    # everyone's best plan, for finish positions and rivals
    best = {}
    for d, st in states.items():
        if st["compound"] in DRY and not st["out_lap"]:
            b = best_plan(st, model, L, total, earliest, model_loss)
            if b:
                best[d] = b
    best_costs = {d: b[2] for d, b in best.items()}

    rows = []
    for d, st in states.items():
        mem = memory.setdefault(d, {"plan": None, "radio": [], "said_final": False, "missed": False})
        plan = mem["plan"]                                         # (pit_lap, compound) or None
        status = neutralised(control, st["end"])                   # what race control said by now

        if status == "RED":
            mem["plan"] = None
            rows.append({"driver_number": int(d), "lap": L, "status": "red"})
            continue
        if st["compound"] not in DRY:                              # wet tyres: no plan
            mem["plan"] = None
            rows.append({"driver_number": int(d), "lap": L, "status": "wet"})
            continue

        # 1. did the car pit at the end of this lap?
        if d in pitted_now:
            kind, when = deployed_during(control, st["start"], st["end"])
            if kind and plan is not None and L >= FIRST_PLAN_LAP:     # would we have called it mid-lap?
                before = dict(st, age=max(0.0, st["age"] - 1))           # the car as it started this lap
                keep = plan_cost(before, model, L - 1, total, plan[0], plan[1], model_loss)
                cheap = min(((c, plan_cost(before, model, L - 1, total, L, c, model_loss * SC_FACTOR[kind]))
                             for c in DRY), key=lambda o: o[1])
                if cheap[1] < keep - 1.0:
                    name = "Safety car" if kind == "SC" else "Virtual safety car"
                    say(memory, d, L, "box", f"{name}! Box this lap for {SHORT[cheap[0]]}",
                        lap=L, at=when - st["start"])
            mem["plan"] = None
            mem["pending_done"] = True
            rows.append({"driver_number": int(d), "lap": L, "status": "pitting"})
            continue
        if st["out_lap"]:
            if mem.pop("pending_done", False):
                pos = st["position"]
                say(memory, d, L, "done", f"Done ✓ {SHORT.get(st['compound'], st['compound'].title())} fitted"
                    + (f" · rejoined P{pos}" if pos else ""), pos)
            mem["said_final"], mem["misses"], mem["hold_until"] = False, 0, 0
            rows.append({"driver_number": int(d), "lap": L, "status": "out_lap"})
            continue

        if L < FIRST_PLAN_LAP:
            rows.append({"driver_number": int(d), "lap": L, "status": "quiet"})
            continue

        loss = model_loss * SC_FACTOR.get(status, 1.0)

        # 2. a planned stop that didn't happen
        if plan and plan[0] is not None and plan[0] <= L:
            say(memory, d, L, "missed", "Missed. Recalculating…")
            mem["plan"], plan, mem["missed"] = None, None, True
            mem["misses"] = mem.get("misses", 0) + 1
            mem["hold_until"] = L + MISS_HOLD * mem["misses"]
            rows.append({"driver_number": int(d), "lap": L, "status": "missed"})
            continue

        hold = max(mem.get("hold_until", 0), L + 3)                # normal plans give at least 2 laps' warning
        target = best.get(d)
        if target is not None and target[0] is not None and target[0] < hold:
            target = best_plan(st, model, L, total, max(earliest, hold), model_loss)
        if target is None:
            rows.append({"driver_number": int(d), "lap": L, "status": "no_plan"})
            continue
        new_plan = (target[0], target[1])
        current = plan_cost(st, model, L, total, plan[0], plan[1], model_loss) if plan else np.inf
        reason = None

        # 3. safety car: a cheaper stop right now?
        if status in ("SC", "VSC") and st["age"] >= MIN_STINT:
            options = [(c, plan_cost(st, model, L, total, L + 1, c, loss)) for c in DRY]
            c, cost = min(options, key=lambda o: o[1])
            keep = min(current, target[2])
            if cost < keep - 1.0:
                new_plan, reason = (L + 1, c), (status,)

        # 4. undercut threat: the car just behind has pitted
        if reason is None and plan and plan[0] is not None and plan[0] > L + 1 \
                and mem.get("hold_until", 0) <= L + 1:
            i = order.index(d)
            behind = order[i + 1] if i + 1 < len(order) else None
            if behind is not None and behind in pitted_now \
                    and states[behind]["end"] - st["end"] < UNDERCUT_GAP:
                options = [(c, plan_cost(st, model, L, total, L + 1, c, model_loss)) for c in DRY]
                c, cost = min(options, key=lambda o: o[1])
                if cost - current < COVER_COST:
                    new_plan, reason = (L + 1, c), ("UC", behind)

        # 5. keep the plan unless the new one is clearly better (and never in the last 2 laps before a stop)
        if reason is None and plan is not None:
            away = plan[0] - (L + 1) if plan[0] is not None else 99
            gain = REPLAN_FAR if away >= 6 else REPLAN_GAIN
            if away <= 1 or target[2] > current - gain:
                new_plan = plan

        # 6. talk only when something changed (or the countdown says so)
        pit_lap, comp = new_plan
        rejoin = rejoin_position(d, states, model, bases, L, pit_lap, loss) if pit_lap else None
        to_go = pit_lap - (L + 1) if pit_lap else None
        tyre = SHORT.get(comp, "")
        out = f" · out in P{rejoin}" if rejoin else ""
        if reason and reason[0] in ("SC", "VSC"):
            name = "Safety car" if reason[0] == "SC" else "Virtual safety car"
            say(memory, d, L, "box", f"{name}! Box now for {tyre}{out}", rejoin)
        elif reason and reason[0] == "UC":
            say(memory, d, L, "box", f"Box… box… cover the undercut for {tyre}{out}", rejoin)
        elif new_plan != plan:
            if pit_lap is None:
                if not mem["said_final"]:
                    say(memory, d, L, "final", "No more stops. Bring it home.")
                    mem["said_final"] = True
            elif to_go == 0:
                say(memory, d, L, "box", f"Box… box… {tyre}{out}", rejoin)
            else:
                word = "Plan" if plan is None and not mem["missed"] else "Change of plan"
                laps_txt = f"{to_go} lap{'s' if to_go > 1 else ''}"
                say(memory, d, L, "plan", f"{word}: box in {laps_txt} (lap {pit_lap}) for {tyre}{out}", rejoin)
            mem["missed"] = False
        elif pit_lap is not None and to_go == 0:
            say(memory, d, L, "box", f"Box… box… {tyre}{out}", rejoin)
        elif pit_lap is not None and to_go == 2:
            say(memory, d, L, "countdown", f"Box in 2 laps{out}", rejoin)
        mem["plan"] = new_plan

        cost_now = plan_cost(st, model, L, total, pit_lap, comp, model_loss)
        if not np.isfinite(cost_now):
            cost_now = target[2]
        finish, best_pos, worst_pos = finish_range(d, states, model, bases, L, total, cost_now, best_costs)
        rows.append({"driver_number": int(d), "lap": L, "status": "plan",
                     "pit_lap": pit_lap, "compound": comp, "rejoin": rejoin,
                     "finish": finish, "best_position": best_pos, "worst_position": worst_pos})
    return rows


def run_engineer(laps, pits, control, total, upto, knowledge=None):
    """Run the engineer from lap 2 to `upto`, feeding it only the past at every lap
    (plus the knowledge from earlier races)."""
    memory, rows = {}, []
    ends = (laps["t_start"] + laps["lap_duration"]).groupby(laps["lap_number"]).max()
    for L in range(2, upto + 1):
        line = ends.get(L, np.inf)
        rows += engineer_step(laps[laps["lap_number"] <= L],
                              pits[pits["lap_number"] <= L] if len(pits) else pits,
                              control[control["t"] <= line] if len(control) else control,
                              L, total, memory, knowledge)
    radio = [dict(m, driver_number=int(d)) for d, mem in memory.items() for m in mem["radio"]]
    return pd.DataFrame(rows), pd.DataFrame(radio)


# ---------- whole races ----------

def load_race(folder):
    path = RACES_DIR / folder
    laps = pd.read_parquet(path / "laps.parquet")
    pits = pd.read_parquet(path / "pits.parquet")
    control = pd.read_parquet(path / "race_control.parquet")
    control = control.dropna(subset=["t"]) if len(control) else control
    return laps, pits, control


def race_knowledge(folder):
    """What the strategist knows before this race: only from earlier races."""
    info = json.loads((RACES_DIR / folder / "info.json").read_text())
    season, rnd = int(info["season"]), int(info["round"])
    return {"book": book_for(season, rnd, info.get("location")), "pit_model": pit_model_for(season)}


def stored_knowledge(folder):
    """The knowledge a stored strategy was built with (so checks can re-run it exactly)."""
    path = RACES_DIR / folder / "knowledge.json"
    return json.loads(path.read_text()) if path.exists() else None


def build_strategy(folder):
    laps, pits, control = load_race(folder)
    total = int(laps["lap_number"].max())
    knowledge = race_knowledge(folder)
    (RACES_DIR / folder / "knowledge.json").write_text(json.dumps(knowledge, indent=1))
    plans, radio = run_engineer(laps, pits, control, total, total - 2, knowledge)
    plans.to_parquet(RACES_DIR / folder / "strategy.parquet", index=False)
    radio.to_parquet(RACES_DIR / folder / "radio.parquet", index=False)
    return plans, radio


def judge(diff):
    if diff is None:
        return "different"
    if abs(diff) <= 2:
        return "matched"
    return "close" if abs(diff) <= 5 else "different"


def verdict(folder):
    """Every real stop next to what the strategist was planning at that moment."""
    laps, pits, control = load_race(folder)
    plans = pd.read_parquet(RACES_DIR / folder / "strategy.parquet")
    radio = pd.read_parquet(RACES_DIR / folder / "radio.parquet")
    return verdict_from(plans, radio, laps, pits, control)


def verdict_from(plans, radio, laps, pits, control):
    stops = real_pits(pits, laps)
    red_laps = sorted({int(l) for l, m in zip(control["lap_number"], control["message"].fillna(""))
                       if pd.notna(l) and RED_FLAG.search(m.upper())}) if len(control) else []

    rows = []
    for s in stops.itertuples():
        d, lap = int(s.driver_number), int(s.lap)
        if lap <= 3:
            rows.append({"driver_number": d, "planned": None, "real": lap, "diff": None, "verdict": "unplanned"})
            continue
        before = plans[(plans["driver_number"] == d) & (plans["lap"] < lap) & (plans["status"] == "plan")]
        planned = before.sort_values("lap")["pit_lap"].iloc[-1] if len(before) else None
        planned = int(planned) if planned is not None and pd.notna(planned) else None
        called = len(radio) and ((radio["driver_number"] == d) & (radio["kind"] == "box")
                                 & (radio["lap"] == lap)).any()
        if called:                                              # e.g. a mid-lap safety car call
            planned = lap
        diff = lap - planned if planned is not None else None
        rows.append({"driver_number": d, "planned": planned, "real": lap, "diff": diff, "verdict": judge(diff)})

    for m in radio[radio["kind"] == "missed"].itertuples() if len(radio) else []:
        rows.append({"driver_number": int(m.driver_number), "planned": int(m.L), "real": None,
                     "diff": None, "verdict": "stayed_out"})

    table = pd.DataFrame(rows, columns=["driver_number", "planned", "real", "diff", "verdict"])
    scored = table[table["verdict"].isin(["matched", "close", "different"])]
    counts = table["verdict"].value_counts().to_dict()
    return {"stops": int(len(scored)), "matched": int(counts.get("matched", 0)),
            "close": int(counts.get("close", 0)), "different": int(counts.get("different", 0)),
            "stayed_out": int(counts.get("stayed_out", 0)), "unplanned": int(counts.get("unplanned", 0)),
            "red_laps": red_laps, "table": table}


def summary(folder):
    v = verdict(folder)
    return {k: v[k] for k in ("stops", "matched", "close", "different", "stayed_out", "unplanned")}


def replay_payload(folder):
    """Everything the Pit Wall needs from the strategist: each car's plan per lap, its radio
    messages, and the verdict. None if this race has no strategy yet."""
    path = RACES_DIR / folder
    if not (path / "strategy.parquet").exists() or not (path / "radio.parquet").exists():
        return None
    plans = pd.read_parquet(path / "strategy.parquet")
    radio = pd.read_parquet(path / "radio.parquet")
    info = json.loads((path / "info.json").read_text())
    codes = {d["number"]: d.get("code") or str(d["number"]) for d in info["drivers"]}
    num = lambda x: None if x is None or pd.isna(x) else int(x)

    calls = {}
    for r in plans[plans["status"] == "plan"].itertuples():
        calls.setdefault(str(int(r.driver_number)), {})[str(int(r.lap))] = {
            "pit": num(r.pit_lap), "tyre": SHORT.get(r.compound) if isinstance(r.compound, str) else None,
            "rejoin": num(r.rejoin), "finish": float(r.finish),
            "best": num(r.best_position), "worst": num(r.worst_position)}

    messages = {}
    for m in radio.sort_values(["L"]).itertuples() if len(radio) else []:
        messages.setdefault(str(int(m.driver_number)), []).append(
            {"L": int(m.L), "lap": int(m.lap), "at": float(m.at), "kind": m.kind, "text": m.text})

    v = verdict(folder)
    table = [{"code": codes.get(r.driver_number, str(r.driver_number)), "planned": num(r.planned),
              "real": num(r.real), "diff": num(r.diff), "verdict": r.verdict}
             for r in v["table"].sort_values(["driver_number", "real"], na_position="last").itertuples()]
    v["table"] = table
    k = stored_knowledge(folder) or default_knowledge()
    b, m = k["book"], k.get("pit_model")
    knew = {"source": b.get("source"), "wear": round(float(b.get("wear_factor", 1.0)), 2),
            "stints": round(float(b.get("stint_factor", 1.0)), 2), "first_stop": round(float(b["first_stop"]), 2),
            "pit_loss": round(float(b["pit_loss"]), 1), "timing": m.get("trained_on") if m else None}
    return {"calls": calls, "radio": messages, "verdict": v, "knew": knew}


def main():
    parser = argparse.ArgumentParser(description="Run the Pit Wall strategist")
    parser.add_argument("season", type=int, nargs="?")
    parser.add_argument("round", type=int, nargs="?")
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    ready = [p.name for p in sorted(RACES_DIR.glob("*_*"), reverse=True) if (p / "info.json").exists()]
    if args.all:
        folders = ready
    elif args.missing:
        todo = [f for f in ready if not (RACES_DIR / f / "radio.parquet").exists()]
        print(f"{len(todo)} races need a strategy; doing up to {args.limit}.")
        folders = todo[:args.limit]
    elif args.season and args.round:
        folders = [f"{args.season}_{args.round:02d}"]
    else:
        parser.error("give a season and a round, or use --missing or --all")

    for folder in folders:
        try:
            build_strategy(folder)
            s = summary(folder)
            print(f"  {folder}: {s['matched']} of {s['stops']} stops matched (within 2 laps), "
                  f"{s['close']} close, {s['different']} different, "
                  f"{s['stayed_out']} BOX calls the team didn't follow")
        except Exception as error:
            print(f"  Skipped {folder}: {error}")


if __name__ == "__main__":
    main()
