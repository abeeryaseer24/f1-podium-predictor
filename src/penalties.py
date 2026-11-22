"""Engine Penalty Planner: when to fit new power-unit parts for the cheapest grid penalties.

Each driver gets a fixed number of power units a season. A part lasts a certain number of races,
so over a long calendar a team may need more than the allowance, and every extra unit costs grid
places (simplified here to the rule's shape: 10 places for the first extra unit, 5 for each after).

THE COST OF A GRID PLACE depends on the circuit. From every race since 2016, this measures how much
a driver's finishing position moves with their grid position at each circuit (a regression slope):
at Monaco a place on the grid is worth nearly a place at the flag, at Spa or Monza much less, because
overtaking is easier.

THE PLAN. A dynamic programme goes through the calendar race by race and chooses where to fit new
units so the total cost (penalty places x that circuit's slope) is smallest, never running a unit
past its life. It's compared with the simple plan: fit a new unit only when the old one is worn out.

Simplified: one combined power-unit "set", no failures, no pooling of several units at once.
"""
import numpy as np
import pandas as pd

from predictor import RESULTS_CSV

FIRST_EXTRA, LATER_EXTRA = 10, 5
DEFAULT_SLOPE = 0.55             # a typical circuit, used where there's too little history


def place_costs(min_races=3):
    """circuit_id -> finishing places lost per grid place (finishers only, since 2016)."""
    df = pd.read_csv(RESULTS_CSV)
    status = df["status"].fillna("")
    fin = df[(status.eq("Finished") | status.str.startswith("+") | status.eq("Lapped")) & (df["grid"] > 0)]
    out = {}
    for circuit, d in fin.groupby("circuit"):
        if d[["season", "round"]].drop_duplicates().shape[0] < min_races:
            continue
        slope = np.polyfit(d["grid"], d["finish_position"], 1)[0]
        out[circuit] = float(np.clip(slope, 0.15, 1.0))
    return out


def plan(costs, allowance=4, life=6):
    """Cheapest plan. costs = per-race cost of one grid place. Returns (rounds with a new unit, total places lost)."""
    n = len(costs)
    INF = float("inf")
    # best[r][used][age] = cheapest cost before race r with `used` units so far and the current unit `age` races old
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def best(r, used, age):
        if r == n:
            return 0.0, ()
        options = []
        if age < life:                                          # keep the current unit
            cost, picks = best(r + 1, used, age + 1)
            options.append((cost, picks))
        new_used = used + 1                                     # fit a new one here
        extra = new_used - allowance
        places = 0 if extra <= 0 else (FIRST_EXTRA if extra == 1 else LATER_EXTRA)
        cost, picks = best(r + 1, new_used, 1)
        options.append((cost + places * costs[r], (r,) + picks))
        return min(options, key=lambda o: o[0]) if options else (INF, ())

    cost, picks = best(1, 1, 1) if n else (0.0, ())            # the first unit is fitted at race 1, free
    return [0] + list(picks), cost


def naive(costs, allowance=4, life=6):
    """Fit a new unit only when the old one reaches its life."""
    picks, cost, used, age = [0], 0.0, 1, 1
    for r in range(1, len(costs)):
        if age >= life:
            used += 1
            extra = used - allowance
            cost += (0 if extra <= 0 else (FIRST_EXTRA if extra == 1 else LATER_EXTRA)) * costs[r]
            picks.append(r)
            age = 1
        else:
            age += 1
    return picks, cost


def penalty_places(picks, allowance):
    """Grid places dropped at each pick."""
    out = {}
    for k, r in enumerate(picks, start=1):
        extra = k - allowance
        out[r] = 0 if extra <= 0 else (FIRST_EXTRA if extra == 1 else LATER_EXTRA)
    return out


if __name__ == "__main__":
    pc = place_costs()
    print({k: round(v, 2) for k, v in sorted(pc.items(), key=lambda kv: kv[1])[:5]}, "... cheapest")
    print({k: round(v, 2) for k, v in sorted(pc.items(), key=lambda kv: kv[1])[-5:]}, "... dearest")
    costs = [pc.get(c, DEFAULT_SLOPE) for c in sorted(pc)][:24]
    print(plan(costs, 4, 5), naive(costs, 4, 5))
