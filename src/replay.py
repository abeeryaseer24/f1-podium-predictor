"""Pit Wall replay data: turns a prepared race into what the 3D replay needs.

Each car's position is turned into 'progress': how far round the race it is, in laps
(12.5 = halfway round lap 13). The replay moves each dot along the real track curve by that
amount, so cars always stay on the track and move smoothly.

Times in the result are seconds from lights out (roughly), one value per second.
"""
import json
import re

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from predictor import RACES_DIR

TRACK_POINTS = 1500               # the track line is resampled to this many evenly spaced points
NOISY_FLAGS = {"BLUE", "CLEAR", "GREEN", "YELLOW", "DOUBLE YELLOW"}
RED_FLAG = re.compile(r"\bRED FLAG\b")      # careful: "CHEQUERED FLAG" also contains "RED FLAG"


def load(folder, name):
    return pd.read_parquet(RACES_DIR / folder / f"{name}.parquet")


def even_track(track):
    """The track line as evenly spaced points (a closed loop)."""
    xy = track[["x", "y"]].to_numpy(dtype=float)
    xy = np.vstack([xy, xy[:1]])
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    u = np.linspace(0, cum[-1], TRACK_POINTS, endpoint=False)
    return np.column_stack([np.interp(u, cum, xy[:, 0]), np.interp(u, cum, xy[:, 1])])


def race_start(laps):
    """Lights out: the first car to start lap 2, minus its lap 1 time."""
    lap2 = laps[laps["lap_number"] == 2].dropna(subset=["t_start"])
    first = lap2.nsmallest(1, "t_start").iloc[0]
    lap1 = laps[(laps["driver_number"] == first["driver_number"]) & (laps["lap_number"] == 1)]
    lap1_time = lap1["lap_duration"].iloc[0] if len(lap1) else None
    if lap1_time is None or pd.isna(lap1_time):
        lap1_time = 1.15 * laps["lap_duration"].median()      # lap 1 is slower (standing start)
    return float(first["t_start"] - lap1_time)


def car_progress(pos, ticks, tree, lap_starts=None):
    """How far round the race one car is (in laps), once per second.
    Where on the lap comes from the car's real position readings; WHICH lap comes from the
    official lap times, so a gap in the position data can never lose a lap. Gaps between
    readings (OpenF1 sometimes has none for 20-30 s) are filled smoothly along the track."""
    samples = pos.drop_duplicates("t").sort_values("t")
    _, idx = tree.query(samples[["x", "y"]].to_numpy(dtype=float))
    t_s = samples["t"].to_numpy(dtype=float)
    frac = idx / TRACK_POINTS                                 # 0..1 round the lap, at each reading
    starts = np.asarray([s for s in (lap_starts if lap_starts is not None else []) if np.isfinite(s)])
    if len(starts) >= 2:
        duration = starts[-1] - starts[-2]
        est = np.interp(t_s, np.r_[starts, starts[-1] + duration],
                        np.arange(len(starts) + 1, dtype=float))    # laps done, judged by the clock
        est = np.where(t_s < starts[0], 0.0, est)
        prog = frac + np.round(est - frac)                    # the lap from the clock, the spot from the position
        good = np.abs(prog - est) < 0.25                      # drop readings that disagree with the clock
        t_s, prog = t_s[good], prog[good]
    else:
        prog = np.unwrap(frac * 2 * np.pi) / (2 * np.pi)      # keeps counting past 1, 2, 3...
        if len(prog) and prog[0] > 0.5:                       # the grid is just before the line
            prog = prog - 1.0
    prog = np.maximum.accumulate(prog)                        # never slide backwards
    return np.interp(ticks, t_s, prog)


def is_event(r):
    """Race control messages worth showing in the ticker."""
    category, flag = r.get("category"), r.get("flag")
    if category == "SafetyCar" or category == "Other":
        return True
    if category == "Flag":
        return flag in ("RED", "CHEQUERED") or r.get("scope") == "Track" and flag not in NOISY_FLAGS
    return False


def race_events(control, base, end):
    """The ticker messages, and the safety car / VSC / red flag periods."""
    events, status = [], []
    open_kind, open_t = None, None
    if control.empty:
        return events, status
    for r in control.sort_values("t").to_dict("records"):
        t = r["t"] - base
        if t < -60 or t > end - base:
            continue
        msg = str(r.get("message") or "")
        up = msg.upper()
        new = None
        if "VIRTUAL SAFETY CAR DEPLOYED" in up or "VSC DEPLOYED" in up:
            new = "VSC"
        elif "SAFETY CAR DEPLOYED" in up:
            new = "SC"
        elif RED_FLAG.search(up) or r.get("flag") == "RED":
            new = "RED"
        closes = any(w in up for w in ("VIRTUAL SAFETY CAR ENDING", "VSC ENDING", "SAFETY CAR IN THIS LAP",
                                       "TRACK CLEAR", "RESUME")) or r.get("flag") == "CHEQUERED"
        if (new or closes) and open_kind:
            extra = 45 if open_kind == "SC" and "IN THIS LAP" in up else 0
            status.append({"kind": open_kind, "start": round(open_t, 1), "end": round(t + extra, 1)})
            open_kind = None
        if new:
            open_kind, open_t = new, t
        if is_event(r):
            events.append({"t": round(t, 1), "text": msg})
    if open_kind:
        status.append({"kind": open_kind, "start": round(open_t, 1), "end": round(end - base, 1)})
    return events, status


def build_replay(folder):
    info = json.loads((RACES_DIR / folder / "info.json").read_text())
    laps, pos, pits = load(folder, "laps"), load(folder, "positions"), load(folder, "pits")
    control, track = load(folder, "race_control"), load(folder, "track")

    start = race_start(laps)
    end = float((laps["t_start"] + laps["lap_duration"]).max()) + 20
    ticks = np.arange(int(np.ceil(start)), int(end) + 1)
    base = float(ticks[0])                                     # replay time 0
    tree = cKDTree(even_track(track))
    total_laps = int(laps["lap_number"].max())

    cars = []
    for d in info["drivers"]:
        number = d["number"]
        p = pos[pos["driver_number"] == number]
        if p.empty:
            continue
        mine = laps[laps["driver_number"] == number].sort_values("lap_number")
        if len(mine):                                      # OpenF1 sometimes skips a lap: fill the gap
            mine = (mine.drop_duplicates("lap_number").set_index("lap_number")
                    .reindex(range(1, int(mine["lap_number"].max()) + 1)))
            mine["t_start"] = mine["t_start"].interpolate(limit_area="inside")
            mine["tyre_age"] = mine["tyre_age"].interpolate(limit_area="inside")
            mine["compound"] = mine["compound"].ffill()
            mine = mine.rename_axis("lap_number").reset_index()
        last_lap = int(mine["lap_number"].max()) if len(mine) else 0
        last_end = (mine["t_start"] + mine["lap_duration"]).max()
        out = (round(float(last_end - base), 1)
               if last_lap < total_laps - 3 and pd.notna(last_end) else None)
        stops = pits.loc[pits["driver_number"] == number, "t"] if "t" in pits else []
        cars.append({
            "number": int(number),
            "code": d.get("code") or str(number),
            "name": (d.get("name") or "").title(),
            "colour": d.get("colour") or "#8a8a96",
            "prog": np.round(car_progress(p, ticks, tree, mine["t_start"].to_numpy(dtype=float)), 3).tolist(),
            "lapStarts": (mine["t_start"] - base).round(1).fillna(-1).tolist(),
            "compound": mine["compound"].fillna("").tolist(),
            "age": mine["tyre_age"].fillna(0).round().astype(int).tolist(),
            "pits": sorted(round(float(t - base), 1) for t in stops),
            "out": out,
        })

    leader = np.max([c["prog"] for c in cars], axis=0)
    lap_times = [int(np.argmax(leader >= k)) for k in range(total_laps)]
    events, status = race_events(control, base, end)
    return {"race_name": info["race_name"], "season": info["season"], "laps": total_laps,
            "duration": int(len(ticks) - 1), "lapTimes": lap_times, "cars": cars,
            "events": events, "status": status}
