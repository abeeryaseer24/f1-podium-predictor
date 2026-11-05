"""The whole live system in one run. GitHub Actions runs this every 3 hours.

1. A race has finished and its results are online?   -> download, CHECK, rebuild features, retrain
2. Next race's qualifying is done, prediction not saved? -> lock it in (log_prediction.py)
3. Final safety checks on everything.

If any step or check fails, the run stops with an error and nothing gets pushed.
"""
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

from picks import ping
from checks import check_log_unchanged, check_results, run_all, snapshot_log
from predictor import BASE_URL, RESULTS_CSV, current_season

SEASON = current_season()


def run(script, *args):
    """Run one of our scripts. If it fails, the whole pipeline stops."""
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

    # Remember how things were before this run, to compare afterwards
    rows_before = len(pd.read_csv(RESULTS_CSV))
    log_before = snapshot_log()

    # 1. New race results? Download, check BEFORE using them, then rebuild and retrain.
    new = missing_results(SEASON)
    if new:
        print(f"New results for round(s) {new}: refreshing data and retraining.")
        run("src/data_loader.py")
        print()
        check_results(min_rows=rows_before)
        run("src/features.py")
        run("src/train.py")
    else:
        print("No new race results.")

    # Race files for the 3D pages: up to 3 missing races per run, newest first.
    run("src/prepare_race.py", "--missing", "--limit", "3")
    run("src/corners.py", "--missing")
    # The strategist's knowledge from earlier races, then strategies for races that need one.
    run("src/history.py", "--missing", "--limit", "5")
    run("src/tyre_book.py")
    run("src/strategy.py", "--missing", "--limit", "10")
   
    # 2. Lock in the next race's prediction if qualifying is done.
    run("src/log_prediction.py", "--season", str(SEASON))

    # 3. Final safety checks on everything.
    print("\nFinal safety checks")
    run_all(min_rows=rows_before)
    check_log_unchanged(log_before)

    # 4. Keep the Beat the AI database awake (free databases pause after a week without use)
    try:
        ping()
    except Exception as error:                     # never stop the robot for this
        print(f"Couldn't reach the picks database: {error}")

    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
