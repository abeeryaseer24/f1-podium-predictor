"""Race history for the strategist to learn from (OpenF1, 2023 onwards).

A light copy of every race: laps with tyres, pit stops and race control messages,
without the 3D track positions. About 30 KB per race, so the whole history stays small.

For one race it saves data/history/<season>_<round>/ with:
  laps.parquet          every lap: time, tyre compound, tyre age, pit out lap
  pits.parquet          pit stops (lap and time in the pit lane)
  race_control.parquet  flags, safety cars and other messages
  meta.json             race name, circuit, number of laps (written last = "this race is done")

Races that already have a full folder in data/races are skipped: the strategist reads those directly.

Usage:
  python src/history.py                  every race that is missing (takes 10-15 minutes the first time)
  python src/history.py --missing --limit 5   up to 5 missing races (what the robot runs)
"""
import argparse
import json

import pandas as pd

from predictor import RACES_DIR, RESULTS_CSV
from prepare_race import FIRST_SEASON, add_tyres, find_session, get, text, timed, to_dt

HISTORY_DIR = RACES_DIR.parent / "history"
LAP_COLUMNS = ["driver_number", "lap_number", "t_start", "lap_duration",
               "is_pit_out_lap", "compound", "tyre_age"]


def download(season, rnd):
    race_name, session = find_session(season, rnd)
    key = int(session["session_key"])
    t0 = to_dt(pd.Series([session["date_start"]])).iloc[0]

    laps = pd.DataFrame(get("laps", {"session_key": key}))
    if laps.empty:
        raise RuntimeError("OpenF1 has no laps for this race yet.")
    laps["t_start"] = (to_dt(laps["date_start"]) - t0).dt.total_seconds()
    laps = add_tyres(laps, pd.DataFrame(get("stints", {"session_key": key})))
    pits = timed(get("pit", {"session_key": key}), t0)
    control = timed(get("race_control", {"session_key": key}), t0)

    out = HISTORY_DIR / f"{season}_{rnd:02d}"
    out.mkdir(parents=True, exist_ok=True)
    laps[[c for c in LAP_COLUMNS if c in laps.columns]].to_parquet(out / "laps.parquet", index=False)
    pits.to_parquet(out / "pits.parquet", index=False)
    control.to_parquet(out / "race_control.parquet", index=False)
    meta = {"season": int(season), "round": int(rnd), "race_name": race_name,
            "location": text(session.get("location")), "country": text(session.get("country_name")),
            "laps": int(laps["lap_number"].max())}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"  Saved {out.name}: {race_name}, {meta['laps']} laps, {len(pits)} pit records")


def missing():
    """Races from 2023 onwards with neither a full race folder nor a history folder, newest first."""
    results = pd.read_csv(RESULTS_CSV, usecols=["season", "round"]).drop_duplicates()
    results = results[results["season"] >= FIRST_SEASON]
    have = {p.name for p in RACES_DIR.glob("*_*") if (p / "info.json").exists()}
    have |= {p.name for p in HISTORY_DIR.glob("*_*") if (p / "meta.json").exists()}
    todo = [(int(s), int(r)) for s, r in results.itertuples(index=False) if f"{s}_{r:02d}" not in have]
    return sorted(todo, reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Download race history for the strategist")
    parser.add_argument("--missing", action="store_true", help="only a few missing races (for the robot)")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    todo = missing()
    if args.missing:
        todo = todo[:args.limit]
    print(f"{len(todo)} races to download.")
    for i, (season, rnd) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {season} round {rnd}")
        try:
            download(season, rnd)
        except Exception as error:                  # not ready yet, or OpenF1 is busy: try again later
            print(f"  Skipped {season} round {rnd}: {error}")


if __name__ == "__main__":
    main()
