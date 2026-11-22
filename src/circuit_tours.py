"""Circuit tours for Academy Module 13: every circuit measured corner by corner.

For each circuit (its most recent calibrated race) the lap simulator drives the calibrated car and
the real fastest lap is lined up with it. Then, for every official corner:
  apex       the slowest point within 60 m of the corner: simulated and real speed, and the gear
  braking    where the braking for it starts (metres before the apex), the speed at that point and
             the hardest deceleration in g
  cornering  the highest sideways g near the apex
  overtaking a stop from above 270 km/h to below 160 km/h after at least 500 m of full throttle,
             the kind of braking zone where most passes happen
and for the circuit as a whole: length, average and top speed, share at full throttle, the number
of braking zones, the calibrated wing level, how hard it is on tyres (tyre_book.csv) and what the
lap simulator says each change is worth here (10 kW more power, 5% more downforce, 5% less drag,
10 kg less mass).

Saves data/processed/circuit_tours.json.
  python src/circuit_tours.py
"""
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lapsim as L

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "circuit_tours.json"
TYRES = ROOT / "data" / "processed" / "tyre_book.csv"


def latest_per_circuit(calibration):
    by = {}
    for folder, c in sorted(calibration.items()):
        if not c.get("usable"):
            continue
        info = json.loads((L.RACES_DIR / folder / "info.json").read_text(encoding="utf-8"))
        by[info["race_name"]] = (folder, info)           # sorted, so the last one is the newest
    return by


def braking_zones(sim, ds):
    """(start index, end index) of every braking zone, wrapping round the lap."""
    brake = sim["mode"] == "brake"
    n = len(brake)
    starts = [i for i in range(n) if brake[i] and not brake[i - 1]]
    zones = []
    for s in starts:
        e = s
        while brake[e % n] and e < s + n:
            e += 1
        zones.append((s, e % n))
    return zones


def tour(folder, info, calibration, tyres):
    track_df = pd.read_parquet(L.RACES_DIR / folder / "track.parquet")
    track = L.build_track(track_df)
    car = L.calibrated_car(folder, calibration)
    sim = L.simulate(car, track)
    real = L.real_trace(track_df, track)
    n, ds = len(track.s), track.length / len(track.s)
    gear = L.gears(sim["speed_kmh"])
    zones = braking_zones(sim, ds)          # counted for the whole circuit
    mode = sim["mode"]
    path = L.RACES_DIR / folder / "corners.json"
    corners = json.loads(path.read_text()) if path.exists() else []

    out, used = [], set()
    for c in corners:
        if c["i"] >= len(track.source_s) or np.isnan(track.source_s[c["i"]]):
            continue
        at = int(round(track.source_s[c["i"]] / ds)) % n
        win = [(at + k) % n for k in range(-int(60 / ds), int(60 / ds) + 1)]
        apex = min(win, key=lambda i: sim["speed"][i])
        row = {"label": c["label"], "s": round(float(track.s[apex]), 1), "i": int(apex),
               "sim_kmh": round(float(sim["speed_kmh"][apex])), "real_kmh": round(float(real["speed_kmh"][apex])),
               "gear": int(gear[apex]), "lat_g": round(float(max(sim["lat_g"][i] for i in win)), 2),
               "brake_m": None, "brake_from_kmh": None, "brake_g": None, "overtaking": False}
        # walk back from the apex to the last moment the car was flat out: the braking for this corner
        # starts at the first braking point after that (so a chicane's two stops count as one)
        k, steps, limit = apex, 0, int(600 / ds)
        while steps < limit:
            while mode[k] != "throttle" and steps < limit:
                k, steps = (k - 1) % n, steps + 1
            run = 0                                   # a flat-out burst under 50 m is still the same complex
            while mode[(k - run) % n] == "throttle" and run * ds < 50:
                run += 1
            if run * ds >= 50 or steps + run >= limit:
                break
            k, steps = (k - run) % n, steps + run
        idx = [(k + j) % n for j in range(1, steps + 1)]
        first = next((i for i in idx if mode[i] == "brake"), None)
        if first is not None and first in used:
            first = None                              # the same stop as the corner before: count it once
        if first is not None:
            used.add(first)
            span = idx[idx.index(first):]
            row["brake_m"] = round(((apex - first) % n) * ds)
            row["brake_from_kmh"] = round(float(sim["speed_kmh"][first]))
            row["brake_g"] = round(float(-min(sim["long_g"][i] for i in span)), 2)
            straight, j = 0, k
            while mode[j] == "throttle" and straight < n:
                straight += 1
                j = (j - 1) % n
            row["overtaking"] = bool(row["brake_from_kmh"] > 270 and row["sim_kmh"] < 160 and straight * ds > 500)
        out.append(row)

    base = sim["lap_time"]

    def worth(changed):
        return round(L.simulate(changed, track)["lap_time"] - base, 3)

    sens = {"power": worth(replace(car, power_kw=car.power_kw + 10)),
            "downforce": worth(replace(car, downforce_scale=car.downforce_scale * 1.05)),
            "drag": worth(replace(car, drag_scale=car.drag_scale * 0.95)),
            "mass": worth(replace(car, mass=car.mass - 10))}
    tyre = tyres.get(folder, {})
    thin = slice(None, None, 2)
    return {
        "folder": folder, "race_name": info["race_name"], "location": info.get("location", ""),
        "season": info["season"], "length_km": round(track.length / 1000, 3),
        "lap": round(base, 3), "real_lap": round(real["lap_time"], 3),
        "avg_kmh": round(track.length / base * 3.6, 1), "top_kmh": round(float(sim["speed_kmh"].max())),
        "min_kmh": round(float(sim["speed_kmh"].min())),
        "full_throttle": round(float((mode == "throttle").mean()), 3), "braking_zones": len(zones),
        "wing": round(car.wing, 2), "altitude_m": round(float(np.mean(track.z))),
        "wear_factor": round(float(tyre["wear_factor"]), 2) if "wear_factor" in tyre else None,
        "pit_loss": round(float(tyre["pit_loss"]), 1) if "pit_loss" in tyre else None,
        "sensitivity": sens, "corners": out,
        "trace": {"s": np.round(track.s[thin], 1).tolist(), "sim": np.round(sim["speed_kmh"][thin]).tolist(),
                  "real": np.round(real["speed_kmh"][thin]).tolist()},
    }


def main():
    calibration = L.load_calibration()
    tyres = pd.read_csv(TYRES).set_index("folder").to_dict("index") if TYRES.exists() else {}
    tours = []
    for name, (folder, info) in sorted(latest_per_circuit(calibration).items()):
        try:
            tours.append(tour(folder, info, calibration, tyres))
            print(f"{folder} {name}: {len(tours[-1]['corners'])} corners")
        except Exception as error:
            print(f"{folder} {name}: skipped ({error})")
    OUT.write_text(json.dumps(tours), encoding="utf-8")
    print(f"{len(tours)} circuits")


if __name__ == "__main__":
    main()
