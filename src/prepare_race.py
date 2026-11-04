"""Prepare ready-made race files for the 3D pages, from the free OpenF1 API (2023 onwards).

For one race it saves a folder data/races/<season>_<round>/ with:
  info.json             race name, date, drivers (names, codes, team colours)
  track.parquet         the circuit shape from the fastest lap: x, y, z, speed, gear
  positions.parquet     every car's position once per second: t, driver_number, x, y, z
  laps.parquet          every lap: time, tyre compound, tyre age, position, pit out lap
  pits.parquet          pit stops
  race_control.parquet  flags, safety cars and other messages
  weather.parquet       weather readings
  practice_laps.parquet practice lap times with tyres (for the smarter model later)

Times are in seconds from the start of the race session.

Usage:
  python src/prepare_race.py 2026 19               one race
  python src/prepare_race.py --missing --limit 3   up to 3 races that don't have files yet
"""
import argparse
import json
import time

import pandas as pd
import requests

from predictor import RACES_DIR, RESULTS_CSV

BASE = "https://api.openf1.org/v1"
FIRST_SEASON = 2023              # OpenF1's free history starts here
MIN_CARS = 15                    # a race needs positions for at least this many cars

LAP_COLUMNS = ["driver_number", "lap_number", "t_start", "lap_duration",
               "duration_sector_1", "duration_sector_2", "duration_sector_3",
               "is_pit_out_lap", "compound", "tyre_age", "position"]


# ---------- talking to OpenF1 ----------

def get(endpoint, params):
    """Rows from OpenF1. Keys ending in > or < are filters, e.g. {"date>": "2026-..."}."""
    parts = []
    for key, value in params.items():
        joiner = "" if key.endswith((">", "<")) else "="
        parts.append(f"{key}{joiner}{value}")
    url = f"{BASE}/{endpoint}?" + "&".join(parts).replace(" ", "%20")

    for attempt in range(5):
        r = requests.get(url, timeout=180)
        if r.status_code == 429:                 # too many requests: wait and retry
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 404:                 # no data for this query
            return []
        r.raise_for_status()
        time.sleep(0.4)                          # be polite to the free API
        data = r.json()
        return data if isinstance(data, list) else []
    raise RuntimeError(f"OpenF1 kept refusing: {url}")


def to_dt(values):
    """Read times and store them all at the same precision (nanoseconds),
    so time columns from different places can be matched with each other."""
    return pd.to_datetime(values, utc=True, format="ISO8601").dt.as_unit("ns")


def fmt(ts):
    """A timestamp in the format OpenF1 filters expect (UTC)."""
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%f")


def text(value):
    return value if isinstance(value, str) and value else None


# ---------- small helpers ----------

def find_session(season, rnd):
    """Match our race (from results.csv) to OpenF1's race session by date."""
    results = pd.read_csv(RESULTS_CSV, usecols=["season", "round", "race_name", "date"])
    row = results[(results["season"] == season) & (results["round"] == rnd)]
    if row.empty:
        raise ValueError(f"No results for {season} round {rnd} yet.")
    race_name = row["race_name"].iloc[0]
    race_day = pd.Timestamp(row["date"].iloc[0], tz="UTC")

    sessions = pd.DataFrame(get("sessions", {"year": season, "session_name": "Race"}))
    if sessions.empty:
        raise ValueError(f"OpenF1 has no races for {season}.")
    sessions["gap"] = (to_dt(sessions["date_start"]).dt.normalize() - race_day).abs()
    best = sessions.sort_values("gap").iloc[0]
    if best["gap"] > pd.Timedelta(days=1):
        raise ValueError(f"OpenF1 has no race close to {race_day.date()}.")
    return race_name, best


def add_tyres(laps, stints):
    """Add the tyre compound and tyre age to every lap, from the stints."""
    laps = laps.copy()
    laps["compound"] = None
    laps["tyre_age"] = float("nan")
    if laps.empty or stints.empty:
        return laps
    stints = stints.copy()
    stints["lap_end"] = stints["lap_end"].fillna(999)
    for s in stints.itertuples():
        mask = ((laps["driver_number"] == s.driver_number)
                & laps["lap_number"].between(s.lap_start, s.lap_end))
        laps.loc[mask, "compound"] = s.compound
        age_at_start = s.tyre_age_at_start if pd.notna(s.tyre_age_at_start) else 0
        laps.loc[mask, "tyre_age"] = age_at_start + laps.loc[mask, "lap_number"] - s.lap_start
    return laps


def timed(rows, t0):
    """Turn rows with a 'date' into a table with 't' = seconds from the session start."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["t"] = (to_dt(df["date"]) - t0).dt.total_seconds()
    return df.drop(columns=[c for c in ("date", "meeting_key", "session_key") if c in df.columns])


# ---------- preparing one race ----------

def prepare(season, rnd):
    race_name, session = find_session(season, rnd)
    key, meeting = int(session["session_key"]), int(session["meeting_key"])
    t0 = to_dt(pd.Series([session["date_start"]])).iloc[0]
    print(f"Preparing {season} round {rnd}: {race_name} (OpenF1 session {key})")

    drivers = pd.DataFrame(get("drivers", {"session_key": key}))
    laps = pd.DataFrame(get("laps", {"session_key": key}))
    if drivers.empty or laps.empty:
        raise RuntimeError("OpenF1 has no drivers or laps for this race yet.")

    # Laps: times, tyres, and position at the end of each lap
    laps["start"] = to_dt(laps["date_start"])
    laps["end"] = laps["start"] + pd.to_timedelta(laps["lap_duration"], unit="s")
    laps["t_start"] = (laps["start"] - t0).dt.total_seconds()
    laps = add_tyres(laps, pd.DataFrame(get("stints", {"session_key": key})))

    positions = pd.DataFrame(get("position", {"session_key": key}))
    if not positions.empty:
        positions["date"] = to_dt(positions["date"])
        ends = laps.dropna(subset=["end"]).sort_values("end")
        ends = pd.merge_asof(ends, positions.sort_values("date")[["date", "driver_number", "position"]],
                             left_on="end", right_on="date", by="driver_number",
                             direction="backward")
        laps = laps.merge(ends[["driver_number", "lap_number", "position"]],
                          on=["driver_number", "lap_number"], how="left")

    # Events
    pits = timed(get("pit", {"session_key": key}), t0)
    control = timed(get("race_control", {"session_key": key}), t0)
    weather = timed(get("weather", {"session_key": key}), t0)

    # Every car's position on track, once per second
    race_end = (laps["end"].max() - t0).total_seconds() + 120
    frames = []
    for number in drivers["driver_number"].astype(int):
        loc = pd.DataFrame(get("location", {"session_key": key, "driver_number": number}))
        if loc.empty:
            continue
        loc["t"] = (to_dt(loc["date"]) - t0).dt.total_seconds().round()
        loc = loc[(loc["t"] >= 0) & (loc["t"] <= race_end)]
        loc = loc.groupby("t", as_index=False)[["x", "y", "z"]].mean()
        loc["driver_number"] = number
        frames.append(loc)
    if len(frames) < MIN_CARS:
        raise RuntimeError(f"Only {len(frames)} cars have track positions so far.")
    track_positions = pd.concat(frames, ignore_index=True)
    track_positions["t"] = track_positions["t"].astype("int32")
    track_positions[["x", "y", "z"]] = track_positions[["x", "y", "z"]].round().astype("int32")

    # The circuit shape: the fastest lap, at full detail, with speed and gear
    clean = laps[laps["lap_duration"].notna()
                 & ~laps["is_pit_out_lap"].fillna(False).astype(bool)]
    fastest = clean.nsmallest(1, "lap_duration").iloc[0]
    window = {"session_key": key, "driver_number": int(fastest["driver_number"]),
              "date>": fmt(fastest["start"]), "date<": fmt(fastest["end"])}
    shape = pd.DataFrame(get("location", window))
    car = pd.DataFrame(get("car_data", window))
    if shape.empty or car.empty:
        raise RuntimeError("No detailed data for the fastest lap yet.")
    shape["date"], car["date"] = to_dt(shape["date"]), to_dt(car["date"])
    shape = pd.merge_asof(shape.sort_values("date"),
                          car.sort_values("date")[["date", "speed", "n_gear", "throttle", "brake"]],
                          on="date", direction="nearest")
    shape["s"] = (shape["date"] - shape["date"].iloc[0]).dt.total_seconds()
    shape = shape[["s", "x", "y", "z", "speed", "n_gear", "throttle", "brake"]]

    # Practice lap times (FP2, or FP1 on sprint weekends)
    practice_name, practice_laps = None, pd.DataFrame()
    for name in ("Practice 2", "Practice 1"):
        found = get("sessions", {"meeting_key": meeting, "session_name": name})
        if found:
            practice_key = found[0]["session_key"]
            practice_laps = add_tyres(pd.DataFrame(get("laps", {"session_key": practice_key})),
                                      pd.DataFrame(get("stints", {"session_key": practice_key})))
            practice_name = name
            break

    # Everything is complete: now write the files (info.json last = "this race is done")
    out = RACES_DIR / f"{season}_{rnd:02d}"
    out.mkdir(parents=True, exist_ok=True)
    laps[[c for c in LAP_COLUMNS if c in laps.columns]].to_parquet(out / "laps.parquet", index=False)
    track_positions.to_parquet(out / "positions.parquet", index=False)
    shape.to_parquet(out / "track.parquet", index=False)
    pits.to_parquet(out / "pits.parquet", index=False)
    control.to_parquet(out / "race_control.parquet", index=False)
    weather.to_parquet(out / "weather.parquet", index=False)
    if not practice_laps.empty:
        cols = [c for c in LAP_COLUMNS if c in practice_laps.columns and c != "position"]
        practice_laps[cols].to_parquet(out / "practice_laps.parquet", index=False)

    info = {
        "season": int(season),
        "round": int(rnd),
        "race_name": race_name,
        "location": text(session.get("location")),
        "country": text(session.get("country_name")),
        "openf1_session_key": key,
        "session_start": t0.isoformat(),
        "laps": int(laps["lap_number"].max()),
        "practice_session": practice_name,
        "drivers": [
            {"number": int(d["driver_number"]),
             "code": text(d.get("name_acronym")),
             "name": text(d.get("full_name")),
             "team": text(d.get("team_name")),
             "colour": f"#{d['team_colour']}" if text(d.get("team_colour")) else None}
            for d in drivers.to_dict("records")
        ],
    }
    (out / "info.json").write_text(json.dumps(info, indent=2))

    size_mb = sum(f.stat().st_size for f in out.iterdir()) / 1e6
    print(f"  Saved {out.name}: {len(frames)} cars, {info['laps']} laps, {size_mb:.1f} MB")


# ---------- which races still need files ----------

def missing_races():
    """Races from 2023 onwards without a finished folder, newest first."""
    results = pd.read_csv(RESULTS_CSV, usecols=["season", "round"]).drop_duplicates()
    results = results[results["season"] >= FIRST_SEASON]
    done = {p.name for p in RACES_DIR.glob("*_*") if (p / "info.json").exists()}
    todo = [(int(s), int(r)) for s, r in results.itertuples(index=False)
            if f"{s}_{r:02d}" not in done]
    return sorted(todo, reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Prepare race files for the 3D pages")
    parser.add_argument("season", type=int, nargs="?")
    parser.add_argument("round", type=int, nargs="?")
    parser.add_argument("--missing", action="store_true",
                        help="prepare races that don't have files yet")
    parser.add_argument("--limit", type=int, default=3,
                        help="with --missing: at most this many races per run")
    args = parser.parse_args()

    if args.missing:
        todo = missing_races()
        print(f"{len(todo)} races still need files; preparing up to {args.limit}.")
        for season, rnd in todo[:args.limit]:
            try:
                prepare(season, rnd)
            except Exception as error:           # not ready yet: try again next run
                print(f"  Skipped {season} round {rnd}: {error}")
    elif args.season and args.round:
        prepare(args.season, args.round)
    else:
        parser.error("give a season and a round, or use --missing")


if __name__ == "__main__":
    main()