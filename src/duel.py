"""Ghost Lap Duel engine: two drivers' fastest laps, compared around the whole lap.

The laps come live from OpenF1 (2023 onwards). The app keeps the results for a day.

Test from the terminal:
  python src/duel.py 2026 19 Qualifying ANT RUS
"""
import json
import sys

import numpy as np
import pandas as pd

from predictor import RACES_DIR
from prepare_race import fmt, get, to_dt

MINI_SECTORS = 25


# ---------- small helpers ----------

def lap_time(seconds):
    """83.456 -> '1:23.456'"""
    minutes, secs = divmod(float(seconds), 60)
    return f"{int(minutes)}:{secs:06.3f}"


def race_info(folder):
    return json.loads((RACES_DIR / folder / "info.json").read_text())


# ---------- getting the laps ----------

def session_key(folder, session_name):
    """OpenF1's key for the race or qualifying session of this event."""
    race_key = race_info(folder)["openf1_session_key"]
    if session_name == "Race":
        return race_key
    race = get("sessions", {"session_key": race_key})
    found = get("sessions", {"meeting_key": race[0]["meeting_key"], "session_name": session_name})
    if not found:
        raise ValueError(f"No {session_name} session found for this event.")
    return found[0]["session_key"]


def fastest_laps(key):
    """Each driver's fastest valid lap in a session, fastest first."""
    laps = pd.DataFrame(get("laps", {"session_key": key}))
    if laps.empty:
        return laps
    laps = laps[laps["lap_duration"].notna()
                & ~laps["is_pit_out_lap"].fillna(False).astype(bool)]
    best = laps.loc[laps.groupby("driver_number")["lap_duration"].idxmin()]
    return best.sort_values("lap_duration").reset_index(drop=True)


def lap_trace(key, number, lap):
    """One lap at full detail: t (seconds into the lap), dist (metres), x, y, z,
    speed, throttle, brake, n_gear."""
    start = to_dt(pd.Series([lap["date_start"]])).iloc[0]
    duration = float(lap["lap_duration"])
    end = start + pd.Timedelta(seconds=duration)
    window = {"session_key": key, "driver_number": int(number),
              "date>": fmt(start - pd.Timedelta(seconds=1)),
              "date<": fmt(end + pd.Timedelta(seconds=1))}
    loc = pd.DataFrame(get("location", window))
    car = pd.DataFrame(get("car_data", window))
    if loc.empty or car.empty:
        raise ValueError("OpenF1 has no detailed data for this lap.")

    loc["date"], car["date"] = to_dt(loc["date"]), to_dt(car["date"])
    trace = pd.merge_asof(loc.sort_values("date"),
                          car.sort_values("date")[["date", "speed", "throttle", "brake", "n_gear"]],
                          on="date", direction="nearest")
    trace["t"] = (trace["date"] - start).dt.total_seconds()
    trace = trace[(trace["t"] >= 0) & (trace["t"] <= duration)].reset_index(drop=True)
    step = (trace[["x", "y"]].diff().pow(2).sum(axis=1) ** 0.5).fillna(0) / 10   # 1/10 m -> m
    trace["dist"] = step.cumsum()
    return trace[["t", "dist", "x", "y", "z", "speed", "throttle", "brake", "n_gear"]]


# ---------- comparing ----------

def compare(trace_a, trace_b, lap_a, lap_b):
    """Line both laps up by how far round the lap they are (0 = start, 1 = finish)."""
    grid = np.linspace(0, 1, 501)

    def times(trace, lap):
        frac = (trace["dist"] / trace["dist"].iloc[-1]).to_numpy()
        return np.interp(grid, np.r_[0, frac, 1], np.r_[0, trace["t"].to_numpy(), lap])

    ta, tb = times(trace_a, lap_a), times(trace_b, lap_b)
    edges = np.linspace(0, 1, MINI_SECTORS + 1)
    seg_a = np.diff(np.interp(edges, grid, ta))      # time spent in each mini-sector
    seg_b = np.diff(np.interp(edges, grid, tb))
    segments = pd.DataFrame({
        "start": edges[:-1], "end": edges[1:],
        "winner": np.where(seg_a <= seg_b, "a", "b"),
        "gain": np.abs(seg_a - seg_b),
    })
    return grid, ta - tb, segments


def corner_fractions(folder, trace):
    """Where each corner falls on this lap, as (label, fraction of the lap)."""
    path = RACES_DIR / folder / "corners.json"
    if not path.exists():
        return []
    corners = json.loads(path.read_text())
    track = pd.read_parquet(RACES_DIR / folder / "track.parquet")
    frac = trace["dist"] / trace["dist"].iloc[-1]
    found = []
    for c in corners:
        x, y = track.loc[c["i"], "x"], track.loc[c["i"], "y"]
        j = ((trace["x"] - x) ** 2 + (trace["y"] - y) ** 2).idxmin()
        found.append((c["label"], float(frac[j])))
    return sorted(found, key=lambda c: c[1])


def describe(start, end, corners, k):
    """Put a stretch of the lap into words using the corner numbers."""
    inside = [label for label, f in corners if start <= f <= end]
    if len(inside) == 1:
        return f"through {inside[0]}"
    if inside:
        return f"from {inside[0]} to {inside[-1]}"
    before = [label for label, f in corners if f < start]
    if before:
        return f"on the straight after {before[-1]}"
    return "on the run to the first corner" if corners else f"around mini-sector {k + 1}"


def best_stretch(segments, who, corners):
    """The run of consecutive mini-sectors where this driver gained the most."""
    best, current = None, None
    for k, s in segments.iterrows():
        if s["winner"] == who:
            if current is None:
                current = {"start": s["start"], "end": s["end"], "gain": 0.0, "k": k}
            current["end"] = s["end"]
            current["gain"] += s["gain"]
            if best is None or current["gain"] > best["gain"]:
                best = dict(current)
        else:
            current = None
    if best is None:
        return None
    return {"where": describe(best["start"], best["end"], corners, best["k"]), "gain": best["gain"]}


def verdict(code_a, code_b, gap, best_a, best_b):
    a_faster = gap < 0
    faster, slower = (code_a, code_b) if a_faster else (code_b, code_a)
    best_f, best_s = (best_a, best_b) if a_faster else (best_b, best_a)
    text = f"{faster} is faster by {abs(gap):.3f} s."
    if best_f:
        text += f" {faster} gains most {best_f['where']} ({best_f['gain']:.2f} s)"
        text += (f", while {slower} wins back {best_s['gain']:.2f} s {best_s['where']}."
                 if best_s else ".")
    return text


# ---------- the whole duel ----------

def run_duel(folder, session_name, num_a, num_b):
    info = race_info(folder)
    codes = {d["number"]: d.get("code") or str(d["number"]) for d in info["drivers"]}
    key = session_key(folder, session_name)
    laps = fastest_laps(key).set_index("driver_number")
    lap_a, lap_b = laps.loc[num_a], laps.loc[num_b]
    time_a, time_b = float(lap_a["lap_duration"]), float(lap_b["lap_duration"])

    trace_a = lap_trace(key, num_a, lap_a)
    trace_b = lap_trace(key, num_b, lap_b)
    grid, delta, segments = compare(trace_a, trace_b, time_a, time_b)
    corners = corner_fractions(folder, trace_a)
    gap = time_a - time_b

    return {
        "lap_a": time_a, "lap_b": time_b, "gap": gap,
        "trace_a": trace_a, "trace_b": trace_b,
        "grid": grid, "delta": delta, "segments": segments, "corners": corners,
        "verdict": verdict(codes.get(num_a, str(num_a)), codes.get(num_b, str(num_b)), gap,
                           best_stretch(segments, "a", corners),
                           best_stretch(segments, "b", corners)),
    }


if __name__ == "__main__":
    season, rnd, session_name, code_a, code_b = sys.argv[1:6]
    folder = f"{int(season)}_{int(rnd):02d}"
    numbers = {(d.get("code") or "").upper(): d["number"] for d in race_info(folder)["drivers"]}
    result = run_duel(folder, session_name, numbers[code_a.upper()], numbers[code_b.upper()])
    print(f"{code_a.upper()}: {lap_time(result['lap_a'])}   {code_b.upper()}: {lap_time(result['lap_b'])}")
    print(result["verdict"])