"""Car DNA: what each car was good at, measured from its fastest race lap.

For every team in a prepared race, this takes the team's fastest race lap (whichever driver set
it), downloads its full telemetry from OpenF1 (the same lap traces the Ghost Lap Duel uses), and
measures it two ways:

1. STRAIGHT FROM THE DATA (no model):
   top speed; the speed at the apex of every slow (<130 km/h), medium (130-210) and fast (>210)
   corner; how quickly it accelerates out of slow corners (traction); share of the lap at full
   throttle. Corners are found once per race on the reference lap, so every team is measured at
   the same places.
2. THROUGH THE LAP SIMULATOR:
   the wing level, grip and power that make lapsim.py reproduce this team's speed trace on the
   real track, turned into downforce at 250 km/h, drag at 300 km/h and power.

Everything is compared within one race (same track, same day), never across circuits.

Writes data/processed/car_dna.csv, one row per team per race. The pipeline runs it after the
prediction is locked in.

Usage:
  python src/car_dna.py 2025 12            one race
  python src/car_dna.py --missing --limit 2   races not measured yet (what the robot runs)
"""
import argparse
import json
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import lapsim
from duel import fastest_laps, lap_trace, start_line
from predictor import RACES_DIR

OUT = RACES_DIR.parent / "processed" / "car_dna.csv"
SLOW, FAST = 130, 210              # km/h apex speeds that split slow / medium / fast corners
APEX_WINDOW = 60                   # m either side of a corner's apex to look for each car's minimum


def apexes(speed_kmh, s, min_drop=15):
    """Corner apexes on a reference lap: local speed minima with a real dip before and after."""
    v = lapsim._circular_smooth(np.asarray(speed_kmh, dtype=float), sigma_points=3)
    n, out = len(v), []
    span = max(1, int(150 / (s[1] - s[0])))            # look 150 m either side
    for i in range(n):
        window = v[[(i + k) % n for k in range(-span, span + 1)]]
        if v[i] == window.min() and window.max() - v[i] >= min_drop:
            if not out or s[i] - s[out[-1]] > 2 * APEX_WINDOW:
                out.append(i)
    return [float(s[i]) for i in out]


def measure(trace, track, apex_s, kind):
    """Data-only measurements for one lap trace, on our track's distance scale."""
    s = trace["frac"].to_numpy() * track.length
    speed = trace["speed"].to_numpy(dtype=float)
    on_track = np.interp(track.s, s, speed)
    mins = {}
    for a, k in zip(apex_s, kind):
        near = np.abs(((track.s - a + track.length / 2) % track.length) - track.length / 2) <= APEX_WINDOW
        mins.setdefault(k, []).append(on_track[near].min())
    # Traction: average acceleration from each slow apex while speed is under 200 km/h
    t = np.interp(track.s, s, trace["t"].to_numpy())
    gains = []
    for a, k in zip(apex_s, kind):
        if k != "slow":
            continue
        i = int(np.argmin(np.abs(track.s - a)))
        j = i
        while j < len(track.s) - 1 and on_track[j] < 200 and track.s[j] - track.s[i] < 700:
            j += 1
        if j > i and t[j] > t[i]:
            gains.append((on_track[j] - on_track[i]) / 3.6 / (t[j] - t[i]) / lapsim.G)
    return {
        "top_speed": float(speed.max()),
        "slow_kmh": float(np.mean(mins["slow"])) if mins.get("slow") else np.nan,
        "medium_kmh": float(np.mean(mins["medium"])) if mins.get("medium") else np.nan,
        "fast_kmh": float(np.mean(mins["fast"])) if mins.get("fast") else np.nan,
        "traction_g": float(np.mean(gains)) if gains else np.nan,
        "full_throttle": float((trace["throttle"].to_numpy() >= 98).mean()),
        "_on_track": on_track,
    }


def fit_car(track, on_track_kmh, lap_time, start):
    """Wing, grip and power that reproduce this speed trace (same idea as lapsim.fit)."""
    def make(p):
        return replace(start, wing=float(np.clip(p[0], 0, 1)), grip=float(np.clip(p[1], 0.8, 3.0)),
                       power_kw=float(np.clip(p[2], 300, 1200)))

    def cost(p):
        sim = lapsim.simulate(make(p), track)
        err = float(np.sqrt(np.mean((sim["speed_kmh"] - on_track_kmh) ** 2)))
        return err + 4.0 * ((sim["lap_time"] - lap_time) / lap_time * 100) ** 2

    p0 = [start.wing, start.grip, start.power_kw]
    res = minimize(cost, p0, method="Nelder-Mead",
                   options={"xatol": 1e-3, "fatol": 1e-3, "maxiter": 140,
                            "initial_simplex": [p0, [p0[0] + 0.2, p0[1], p0[2]], [p0[0], p0[1] + 0.2, p0[2]],
                                                [p0[0], p0[1], p0[2] + 80]]})
    car = make(res.x)
    sim = lapsim.simulate(car, track)
    return car, float(np.sqrt(np.mean((sim["speed_kmh"] - on_track_kmh) ** 2)))


def build(folder):
    info = json.loads((RACES_DIR / folder / "info.json").read_text())
    track_df = pd.read_parquet(RACES_DIR / folder / "track.parquet")
    track = lapsim.build_track(track_df)
    ref = lapsim.real_trace(track_df, track)
    apex_s = apexes(ref["speed_kmh"], track.s)
    ref_at = [float(np.interp(a, track.s, ref["speed_kmh"])) for a in apex_s]
    kind = ["slow" if v < SLOW else "fast" if v > FAST else "medium" for v in ref_at]
    start = lapsim.calibrated_car(folder)

    key = info["openf1_session_key"]
    laps = fastest_laps(key)
    who = {int(d["number"]): d for d in info.get("drivers", [])}
    line = start_line(folder)
    rows, seen = [], set()
    for _, lap in laps.iterrows():                       # fastest first: the first lap per team wins
        num = int(lap["driver_number"])
        team = who.get(num, {}).get("team")
        if not team or team in seen:
            continue
        seen.add(team)
        try:
            trace = lap_trace(key, num, lap, line)
        except Exception as error:                       # no telemetry for this lap: skip the team
            print(f"  {folder} {team}: skipped ({error})")
            continue
        if len(trace) < 100:
            continue
        m = measure(trace, track, apex_s, kind)
        car, rmse = fit_car(track, m.pop("_on_track"), float(lap["lap_duration"]), start)
        facts_down = 0.5 * track.rho * car.cza * (250 / 3.6) ** 2 / 1000
        facts_drag = 0.5 * track.rho * car.cxa * (300 / 3.6) ** 2 / 1000
        rows.append({"folder": folder, "season": info["season"], "round": info["round"],
                     "race_name": info["race_name"], "location": info.get("location", ""),
                     "team": team, "colour": who[num].get("colour") or "#8a8a96", "driver": who[num].get("code", ""),
                     "lap_time": float(lap["lap_duration"]), **m,
                     "wing": car.wing, "grip": car.grip, "power_kw": car.power_kw,
                     "downforce_kn": facts_down, "drag_kn": facts_drag, "fit_rmse": rmse,
                     "corners_slow": kind.count("slow"), "corners_medium": kind.count("medium"),
                     "corners_fast": kind.count("fast")})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("season", nargs="?", type=int)
    parser.add_argument("round", nargs="?", type=int)
    parser.add_argument("--missing", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    done = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=["folder"])
    calibration = lapsim.load_calibration()
    usable = [f for f, c in calibration.items() if c.get("usable")]
    if args.season and args.round:
        todo = [f"{args.season}_{args.round:02d}"]
    elif args.missing:
        todo = [f for f in sorted(usable, reverse=True) if f not in set(done["folder"])]
        if args.limit:
            todo = todo[:args.limit]
    else:
        print(__doc__)
        return
    for folder in todo:
        new = build(folder)
        if new.empty:
            print(f"{folder}: no telemetry")
            continue
        done = pd.concat([d for d in (done[done["folder"] != folder], new) if len(d)], ignore_index=True)
        done[["season", "round"]] = done[["season", "round"]].astype(int)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        done.sort_values(["season", "round", "lap_time"]).to_csv(OUT, index=False)
        best = new.sort_values("lap_time").iloc[0]
        print(f"{folder}: {len(new)} teams measured; fastest {best['team']} ({best['lap_time']:.3f}s)")


if __name__ == "__main__":
    main()
