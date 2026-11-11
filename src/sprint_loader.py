"""Download sprint race results from the Jolpica-F1 API.

Sprint points are not part of the normal race results, so without this file the
championship tables are short by up to 8 points per driver on a sprint weekend.
Run it once, then let the pipeline keep it up to date:

  python src/sprint_loader.py          # refresh the newest season we have
  python src/sprint_loader.py --full   # rebuild every season from 2016

It writes data/processed/sprint.csv. Sprint races began in 2021, so the seasons
before that simply come back empty, which is correct.
"""
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
FIRST_SEASON = 2016
LIMIT = 100

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "data" / "processed" / "sprint.csv"
COLUMNS = ["season", "round", "driver", "constructor", "sprint_position",
           "sprint_grid", "sprint_status", "sprint_points"]


def get_json(url, params):
    """Call the API, waiting and trying again if it says we are going too fast."""
    for attempt in range(5):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(5 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"API kept refusing: {url}")


def fetch_sprint(season):
    """Every sprint result for one season, one row per driver per sprint."""
    rows, offset = [], 0
    while True:
        data = get_json(f"{BASE_URL}/{season}/sprint.json",
                        {"limit": LIMIT, "offset": offset})["MRData"]
        for race in data["RaceTable"]["Races"]:
            results = race.get("SprintResults") or race.get("Results") or []
            for r in results:
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "driver": r["Driver"]["driverId"],
                    "constructor": r["Constructor"]["constructorId"],
                    "sprint_position": int(r["position"]),
                    "sprint_grid": int(r.get("grid", 0)),
                    "sprint_status": r.get("status", ""),
                    "sprint_points": float(r["points"]),
                })
        total = int(data["total"])
        offset += LIMIT
        if offset >= total or total == 0:
            break
        time.sleep(0.5)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Download F1 sprint race results")
    parser.add_argument("--full", action="store_true",
                        help="re-download every season from scratch")
    args = parser.parse_args()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    old = None
    if OUT_FILE.exists() and not args.full:
        old = pd.read_csv(OUT_FILE)
        first = int(old["season"].max()) if len(old) else FIRST_SEASON
    else:
        first = FIRST_SEASON
    seasons = range(first, datetime.now(timezone.utc).year + 1)

    rows = []
    for season in seasons:
        print(f"Downloading sprint results for {season}...")
        rows += fetch_sprint(season)
        time.sleep(0.5)

    new = pd.DataFrame(rows, columns=COLUMNS)
    if old is not None and len(old):
        new = pd.concat([old[old["season"] < first], new], ignore_index=True)

    new = new.sort_values(["season", "round", "sprint_position"]).reset_index(drop=True)
    new.to_csv(OUT_FILE, index=False)
    print(f"Done. {len(new)} sprint results saved to {OUT_FILE}")


if __name__ == "__main__":
    main()
