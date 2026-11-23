"""Calendar Planner (A12): how far the F1 circus travels in a season, and a shorter order for the same races.

TRAVEL. Each leg is the great-circle distance between two circuits (from our archive's coordinates).
Legs between two European circuits go by road (trucks), so their distance is stretched by ROAD_DETOUR
for the roads not being straight; every other leg is air freight. Optionally the season starts and ends at
a European base (most teams are in England and Italy).

CARBON is an estimate, and the page says so: freight tonnes moved per leg times a kg-CO2 per tonne-km
factor, one for air freight and one for trucks. The defaults are round published-scale figures, and the
visitor can change them.

THE OPTIMISER keeps the same races and searches for a shorter order by simulated annealing (swap two races,
keep the change if it's shorter, sometimes even if it's longer early on). Real calendars can't move freely:
races are tied to weather, holidays and contracts, so some races stay fixed and every other race may move
at most `max_shift` places from its real slot.

  python src/calendar_plan.py 2025      the real 2025 calendar against an optimised one
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RACES = ROOT / "data" / "processed" / "history_races.csv"
BASE = (52.07, -1.02)                 # a European base near Silverstone, where most teams are
ROAD_DETOUR = 1.25                    # roads are longer than the straight line
DEFAULTS = {"tonnes": 1200.0, "air": 0.6, "road": 0.1}    # t per move; kg CO2 per tonne-km (estimates)


def season(year):
    r = pd.read_csv(RACES)
    return r[r["season"] == year].sort_values("round").reset_index(drop=True)


def in_europe(lat, lon):
    return 35.0 <= lat <= 62.0 and -11.0 <= lon <= 30.0


def great_circle(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def leg(a, b, factors):
    """(km, mode, kg CO2) for one move between two places (lat, lon)."""
    road = in_europe(*a) and in_europe(*b)
    km = great_circle(a, b) * (ROAD_DETOUR if road else 1.0)
    kg = km * factors["tonnes"] * (factors["road"] if road else factors["air"])
    return km, "road" if road else "air", kg


def route(points, order, factors, base=True):
    """Every leg of a season in this order: list of dicts, and the totals."""
    stops = [points[i] for i in order]
    if base:
        stops = [BASE] + stops + [BASE]
    legs = []
    for a, b in zip(stops, stops[1:]):
        km, mode, kg = leg(a, b, factors)
        legs.append({"km": km, "mode": mode, "kg": kg})
    return legs, sum(x["km"] for x in legs), sum(x["kg"] for x in legs)


def optimise(points, fixed, max_shift, factors, base=True, iters=40_000, seed=7, objective="kg"):
    """A shorter order keeping `fixed` races in their slots and moving others at most max_shift places."""
    n = len(points)
    rng = random.Random(seed)
    order = list(range(n))
    movable = [i for i in range(n) if i not in fixed]
    cost = lambda o: route(points, o, factors, base)[2 if objective == "kg" else 1]
    cur, cur_c = order[:], cost(order)
    best, best_c = cur[:], cur_c
    t0 = cur_c * 0.02
    for k in range(iters):
        if len(movable) < 2:
            break
        i, j = rng.sample(movable, 2)
        a, b = cur[i], cur[j]                   # race a moves to slot j, race b to slot i
        if abs(j - a) > max_shift or abs(i - b) > max_shift:
            continue
        cur[i], cur[j] = b, a
        c = cost(cur)
        temp = t0 * (1 - k / iters) + 1e-9
        if c < cur_c or rng.random() < math.exp((cur_c - c) / temp):
            cur_c = c
            if c < best_c:
                best, best_c = cur[:], c
        else:
            cur[i], cur[j] = a, b
    return best


def main(args):
    year = int(args[0]) if args else 2025
    s = season(year)
    pts = list(zip(s["latitude"], s["longitude"]))
    fixed = {0, len(pts) - 1} | set(s.index[s["race_name"].str.contains("Monaco")])
    _, km, kg = route(pts, list(range(len(pts))), DEFAULTS)
    best = optimise(pts, fixed, 6, DEFAULTS)
    _, km2, kg2 = route(pts, best, DEFAULTS)
    print(f"{year}: real {km:,.0f} km, {kg / 1e6:,.0f} t CO2 · optimised {km2:,.0f} km, {kg2 / 1e6:,.0f} t CO2 "
          f"({(1 - kg2 / kg):.0%} less)")
    print(" → ".join(s.loc[i, "locality"] for i in best))


if __name__ == "__main__":
    main(sys.argv[1:])
