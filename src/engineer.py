"""Be the Race Engineer: everything the game needs for one race.

The game rebuilds your car's race lap by lap:
  your lap time = the real driver's pace on that lap (tyres taken out) + what YOUR tyres cost
plus the pit stop time when you box (less under a safety car, free under a red flag).
Everyone else races exactly as they did in reality. It is a simulation, and the page says so.

To compare fairly, three strategies go through the same simulation:
  you, the real team (their real stops), and our strategist (if the team had listened to it).

Test from the terminal:
  python src/engineer.py 2026 19
"""
import json
import sys

import numpy as np
import pandas as pd

from predictor import RACES_DIR
from replay import race_start
from strategy import (CLIFF_RATE, CLIFF_START, DRY, EARLIEST_STOP, FIRST_PLAN_LAP, MIN_STINT, REPLAN_FAR,
                      REPLAN_GAIN, SC_FACTOR, best_plan, default_knowledge, load_race, neutralised,
                      plan_cost, stored_knowledge, tyre_model)
from tyre_book import neutral_laps, real_pits

MAX_LAPS_DOWN = 2               # a driver must have finished within this many laps of the winner


def lap_tyre_cost(model, comp, age):
    """Seconds one lap costs on `comp` at `age` (same tyre model as the strategist)."""
    life = model["life"][comp]
    cliff = CLIFF_RATE * np.maximum(0.0, np.asarray(age, dtype=float) - CLIFF_START * life)
    return model["offset"][comp] + model["wear"][comp] * np.asarray(age, dtype=float) + cliff


def real_laps(mine):
    """The driver's laps 1..n with no gaps: real lap time, tyre and tyre age on every lap."""
    laps = mine.drop_duplicates("lap_number").set_index("lap_number")
    n = int(laps.index.max())
    # a lap's real time = when the next lap started minus when this one did (OpenF1 sometimes
    # leaves lap_duration blank, e.g. on a red-flag lap); the last lap uses its own duration
    starts = laps["t_start"].reindex(range(1, n + 2)).astype(float).interpolate(limit_area="inside")
    real = (starts.shift(-1) - starts).iloc[:n].fillna(laps["lap_duration"].reindex(range(1, n + 1)).astype(float))
    comp = laps["compound"].reindex(range(1, n + 1)).ffill().bfill().tolist()
    age = laps["tyre_age"].reindex(range(1, n + 1)).astype(float).interpolate(limit_area="inside").ffill().bfill().tolist()
    return n, real.to_numpy(), comp, age


def tyre_changes(comp, age, red_lap, paid):
    """Every real tyre change, read from the laps: a new compound, or the tyre age going back.
    A change next to a red flag with no real pit stop recorded is the free red-flag change."""
    out = []
    for k in range(1, len(comp)):                             # change at the end of lap k
        if comp[k] != comp[k - 1] or age[k] < age[k - 1] + 0.5:
            free = k not in paid and red_lap is not None and abs(k - red_lap) <= 1
            out.append({"lap": k, "tyre": comp[k], "age": round(float(age[k]), 1), "free": bool(free)})
    return out


def clean_pace(real, comp, age, changes, model, neutral, pit_loss):
    """The driver's real lap times with the tyre effect and the pit stop time taken out.
    The game adds back exactly the same amounts, so copying the real stops gives the real race."""
    pace = real - np.array([float(lap_tyre_cost(model, c, a)) if c in DRY else 0.0 for c, a in zip(comp, age)])
    for s in changes:
        if s["free"]:
            continue
        loss = pit_loss * (SC_FACTOR.get(neutral[s["lap"] - 1]) or 1.0)
        pace[s["lap"] - 1] -= 0.4 * loss                       # in-lap
        if s["lap"] < len(pace):
            pace[s["lap"]] -= 0.6 * loss                       # out-lap
    return pd.Series(pace).interpolate(limit_direction="both").to_numpy()


def strategist_stops(d, laps, pits, control, total, models, knowledge, start_comp, start_age, red_lap):
    """What our strategist would have done if the team had followed every call:
    its own virtual car, with its own tyres, re-planned at the end of every lap."""
    comp, age, used, stops, plan, out = start_comp, start_age, {start_comp} & set(DRY), 0, None, []
    earliest = max(round(EARLIEST_STOP * total), FIRST_PLAN_LAP + 1)
    ends = (laps["t_start"] + laps["lap_duration"]).where(laps["driver_number"] == d)
    ends = ends.groupby(laps["lap_number"]).max()
    for L in range(1, total - 2):
        if red_lap is not None and L == red_lap:              # red flag: a free fresh set
            new = comp if len(used) >= 2 else min(c for c in DRY if c != comp)
            out.append({"lap": L, "tyre": new, "free": True})
            comp, age, plan = new, -1, None
            used.add(new)
        elif plan and plan[0] == L:                           # the virtual car pits now
            out.append({"lap": L, "tyre": plan[1], "free": False})
            comp, age, plan, stops = plan[1], -1, None, stops + 1
            used.add(comp)
        elif L >= FIRST_PLAN_LAP and L in models:
            model = models[L]
            status = neutralised(control, ends.get(L, np.inf))
            st = {"compound": comp, "age": float(age), "used": set(used), "stops": stops,
                  "neutral": status in ("SC", "VSC")}
            target = best_plan(st, model, L, total, max(earliest, L + 3), model["pit_loss"])
            current = plan_cost(st, model, L, total, plan[0], plan[1], model["pit_loss"]) if plan else np.inf
            new_plan = (target[0], target[1]) if target else plan
            if status in ("SC", "VSC") and age >= MIN_STINT:
                loss = model["pit_loss"] * SC_FACTOR[status]
                c, cost = min(((c, plan_cost(st, model, L, total, L + 1, c, loss)) for c in DRY), key=lambda o: o[1])
                if cost < min(current, target[2] if target else np.inf) - 1.0:
                    new_plan = (L + 1, c)
            elif plan is not None and target is not None:
                away = plan[0] - (L + 1) if plan[0] is not None else 99
                gain = REPLAN_FAR if away >= 6 else REPLAN_GAIN
                if away <= 1 or target[2] > current - gain:
                    new_plan = plan
            plan = new_plan
        age += 1
    return out


def game_pack(folder):
    """Everything the game page needs for one race, or None if the race can't be played."""
    path = RACES_DIR / folder
    info = json.loads((path / "info.json").read_text())
    laps, pits, control = load_race(folder)
    total = int(laps["lap_number"].max())
    knowledge = stored_knowledge(folder) or default_knowledge()
    base = float(np.ceil(race_start(laps)))                  # replay time 0, same as the replay
    stops = real_pits(pits, laps)
    sc_laps, red_laps = neutral_laps(laps, control)
    if laps["compound"].isin(["INTERMEDIATE", "WET"]).any():
        return None                                          # rain: not in the game (yet)
    full = tyre_model(laps, knowledge)                       # the race is over: use all of it
    models = {L: tyre_model(laps[laps["lap_number"] <= L], knowledge)
              for L in range(FIRST_PLAN_LAP, total - 2)}

    finish, drivers = [], {}
    for d, mine in laps.sort_values("lap_number").groupby("driver_number"):
        mine = mine.dropna(subset=["t_start"])
        if mine.empty:
            continue
        n = int(mine["lap_number"].max())
        last = mine[mine["lap_number"] == n].iloc[0]
        if pd.isna(last["lap_duration"]):                    # the last lap was never completed
            n, end = n - 1, last["t_start"]
            mine = mine[mine["lap_number"] <= n]
        else:
            end = last["t_start"] + last["lap_duration"]
        if n < 1:
            continue
        finish.append({"number": int(d), "laps": n, "end": round(float(end - base), 1)})

        wet = mine["compound"].isin(["INTERMEDIATE", "WET"]).any()
        if n < total - MAX_LAPS_DOWN or wet or mine["compound"].dropna().iloc[0] not in DRY:
            continue
        red = sorted(L for dd, L in red_laps if dd == d)
        red_lap = red[0] if red else None
        n, real, comp, age = real_laps(mine)
        ends = (mine.set_index("lap_number")["t_start"] + mine.set_index("lap_number")["lap_duration"])
        neutral = [neutralised(control, float(x)) for x in ends.reindex(range(1, n + 1)).ffill().bfill()]
        neutral = [s if s in ("SC", "VSC") else None for s in neutral]
        changes = tyre_changes(comp, age, red_lap, set(stops.loc[stops["driver_number"] == d, "lap"]))
        pace = clean_pace(real, comp, age, changes, full, neutral, full["pit_loss"])
        start = mine.iloc[0]
        drivers[str(int(d))] = {
            "laps": n, "start": round(float(start["t_start"] - base), 1),
            "pace": np.round(pace, 3).tolist(),
            "startTyre": comp[0], "startAge": float(age[0]),
            "neutral": neutral, "redLap": red_lap,
            "real": changes,
            "strategist": strategist_stops(d, laps, pits, control, total, models, knowledge,
                                           comp[0], float(age[0]), red_lap),
        }
    if not drivers:
        return None
    pack = {"laps": total, "pitLoss": round(float(full["pit_loss"]), 2), "scFactor": SC_FACTOR,
            "tyres": {"offset": full["offset"], "wear": full["wear"], "life": full["life"],
                      "cliffStart": CLIFF_START, "cliffRate": CLIFF_RATE}, "drivers": drivers}
    # Calibration: copying the real team's stops must give exactly the real finishing time
    real_end = {str(f["number"]): f["end"] for f in finish}
    for num, d in drivers.items():
        d["calibration"] = round(real_end[num] - simulate(pack, num, d["real"], calibrated=False), 2)
    return {"laps": total, "pitLoss": round(float(full["pit_loss"]), 2), "scFactor": SC_FACTOR,
            "tyres": {"offset": full["offset"], "wear": full["wear"], "life": full["life"],
                      "cliffStart": CLIFF_START, "cliffRate": CLIFF_RATE},
            "finish": finish, "drivers": drivers}


def simulate(pack, number, plan, calibrated=True):
    """Total race time for one driver with a list of stops (the same maths as the page)."""
    d, t = pack["drivers"][str(number)], pack["tyres"]
    comp, age, total = d["startTyre"], d["startAge"], d["start"]
    stops = {s["lap"]: s for s in plan}
    out_lap_loss = 0.0
    for k in range(1, d["laps"] + 1):
        life = t["life"][comp]
        lap = d["pace"][k - 1] + t["offset"][comp] + t["wear"][comp] * age \
            + t["cliffRate"] * max(0.0, age - t["cliffStart"] * life) + out_lap_loss
        out_lap_loss = 0.0
        s = stops.get(k)
        if s:
            loss = 0.0 if s["free"] else pack["pitLoss"] * (pack["scFactor"].get(d["neutral"][k - 1]) or 1.0)
            lap += 0.4 * loss
            out_lap_loss = 0.6 * loss
            comp, age = s["tyre"], s.get("age", 0)
        else:
            age += 1
        total += lap
    return total + (d.get("calibration", 0.0) if calibrated else 0.0)


def main():
    season, rnd = int(sys.argv[1]), int(sys.argv[2])
    folder = f"{season}_{rnd:02d}"
    pack = game_pack(folder)
    if pack is None:
        print("This race can't be played (rain, or no finishers with clean data).")
        return
    info = json.loads((RACES_DIR / folder / "info.json").read_text())
    codes = {d["number"]: d["code"] for d in info["drivers"]}
    real_end = {f["number"]: f["end"] for f in pack["finish"]}
    print(f"{info['race_name']}: {len(pack['drivers'])} drivers playable")
    for num, d in pack["drivers"].items():
        real = simulate(pack, num, d["real"])
        strat = simulate(pack, num, d["strategist"])
        print(f"  {codes.get(int(num), num):>4}: real stops {[s['lap'] for s in d['real']]}, "
              f"strategist {[s['lap'] for s in d['strategist']]}  | simulated real {real:.0f}s "
              f"vs actual {real_end[int(num)]:.0f}s (diff {real - real_end[int(num)]:+.1f}s), "
              f"strategist {strat - real:+.1f}s")


if __name__ == "__main__":
    main()
