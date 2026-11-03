"""The whole live system in one run. GitHub Actions runs this every 3 hours.

1. A race has finished and its results are online?   -> download data, rebuild features, retrain
2. Next race's qualifying is done, prediction not saved? -> lock it in (log_prediction.py)

Each step only acts when there is something new, so running this often is safe.
"""
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

from predictor import BASE_URL, RESULTS_CSV

SEASON = 2026


def run(script, *args):
    """Run one of our scripts. If it fails, the whole pipeline stops (nothing gets pushed)."""
    print(f"\n>>> python {script} {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, script, *args], check=True)


def race_start(race):
    """Start time of a race from the calendar, in UTC."""
    time = race.get("time", "12:00:00Z").replace("Z", "+00:00")
    return datetime.fromisoformat(f"{race['date']}T{time}")


def missing_results(season):
    """Rounds that have finished and have results online, but aren't in our data yet."""
    data = requests.get(f"{BASE_URL}/{season}.json", timeout=30).json()
    calendar = data["MRData"]["RaceTable"]["Races"]

    have = pd.read_csv(RESULTS_CSV, usecols=["season", "round"])
    have = set(have.loc[have["season"] == season, "round"])
    now = datetime.now(timezone.utc)

    missing = []
    for race in calendar:
        rnd = int(race["round"])
        if rnd in have or race_start(race) > now:
            continue
        res = requests.get(f"{BASE_URL}/{season}/{rnd}/results.json", timeout=30).json()
        if res["MRData"]["RaceTable"]["Races"]:
            missing.append(rnd)
    return missing


def main():
    print(f"Pipeline run at {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")

    # 1. New race results? Refresh everything and retrain.
    new = missing_results(SEASON)
    if new:
        print(f"New results for round(s) {new}: refreshing data and retraining.")
        run("src/data_loader.py")
        run("src/features.py")
        run("src/train.py")
    else:
        print("No new race results.")

    # 2. Lock in the next race's prediction if qualifying is done (the script checks the rules).
    run("src/log_prediction.py", "--season", str(SEASON))

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()