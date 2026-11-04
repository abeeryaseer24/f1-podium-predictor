"""Download race and qualifying results from the Jolpica-F1 API.

Normal run:  only re-downloads the newest season we have (plus any newer one), then
             merges it into the existing data. Fast, and kind to the free API.
--full:      re-downloads every season from 2016 (use if the data ever looks broken).
"""
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
FIRST_SEASON = 2016
LIMIT = 100                   # rows per API call (the API's max)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUT_FILE = PROCESSED_DIR / "results.csv"


def get_json(url, params):
    """Call the API, and wait and retry if it says we're going too fast."""
    for attempt in range(5):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:          # "too many requests"
            time.sleep(5 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"API kept refusing: {url}")


def fetch_results(season):
    """All race results for one season, one row per driver per race."""
    rows, offset = [], 0
    while True:
        data = get_json(f"{BASE_URL}/{season}/results.json",
                        {"limit": LIMIT, "offset": offset})["MRData"]
        for race in data["RaceTable"]["Races"]:
            for r in race["Results"]:
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "race_name": race["raceName"],
                    "circuit": race["Circuit"]["circuitId"],
                    "date": race["date"],
                    "driver": r["Driver"]["driverId"],
                    "constructor": r["Constructor"]["constructorId"],
                    "grid": int(r["grid"]),
                    "finish_position": int(r["position"]),
                    "status": r["status"],
                    "points": float(r["points"]),
                })
        offset += LIMIT
        if offset >= int(data["total"]):
            break
        time.sleep(0.5)
    return rows


def fetch_qualifying(season):
    """Qualifying results for one season."""
    rows, offset = [], 0
    while True:
        data = get_json(f"{BASE_URL}/{season}/qualifying.json",
                        {"limit": LIMIT, "offset": offset})["MRData"]
        for race in data["RaceTable"]["Races"]:
            for q in race["QualifyingResults"]:
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "driver": q["Driver"]["driverId"],
                    "quali_position": int(q["position"]),
                })
        offset += LIMIT
        if offset >= int(data["total"]):
            break
        time.sleep(0.5)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Download F1 race and qualifying results")
    parser.add_argument("--full", action="store_true",
                        help="re-download every season from scratch")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Which seasons to download
    old = None
    if OUT_FILE.exists() and not args.full:
        old = pd.read_csv(OUT_FILE)
        first = int(old["season"].max())        # refresh the newest season we have
    else:
        first = FIRST_SEASON                     # full rebuild
    seasons = range(first, datetime.now(timezone.utc).year + 1)

    results, quali = [], []
    for season in seasons:
        print(f"Downloading {season}...")
        results += fetch_results(season)
        time.sleep(0.5)
        quali += fetch_qualifying(season)
        time.sleep(0.5)

    results_df = pd.DataFrame(results)
    quali_df = pd.DataFrame(quali)

    # Keep a copy of exactly what was downloaded this time
    results_df.to_csv(RAW_DIR / "results_raw.csv", index=False)
    quali_df.to_csv(RAW_DIR / "quali_raw.csv", index=False)

    # Combine into one table: one row per driver per race
    new = results_df.merge(quali_df, on=["season", "round", "driver"], how="left")

    # Keep the older seasons we already had, replace the ones we just downloaded
    if old is not None:
        new = pd.concat([old[old["season"] < first], new], ignore_index=True)

    new = new.sort_values(["season", "round", "finish_position"]).reset_index(drop=True)
    new.to_csv(OUT_FILE, index=False)
    print(f"Done. {len(new)} rows saved to {OUT_FILE}")


if __name__ == "__main__":
    main()