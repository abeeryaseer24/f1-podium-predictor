"""Is it time to lock in the next race's prediction? A quick check for the race-day lock robot.

It answers "yes" only when the next race's lock time has passed (8 hours before lights out)
and that race isn't locked in yet. Most runs answer "no" and finish in a few seconds,
so the robot only installs everything and predicts when there's real work to do.
Uses plain Python only (no extra libraries needed).
"""
import csv
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "data" / "predictions" / "predictions.csv"
BASE_URL = "https://api.jolpi.ca/ergast/f1"
LOCK_HOURS = 8           # keep the same as LOCK_HOURS in log_prediction.py


def answer(run, why):
    print(why)
    print("Run the lock:", "yes" if run else "no")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"run={'true' if run else 'false'}\n")


def race_start(race):
    time = race.get("time", "12:00:00Z").replace("Z", "+00:00")
    return datetime.fromisoformat(f"{race['date']}T{time}")


def already_locked(season, rnd):
    if not LOG_FILE.exists():
        return False
    with open(LOG_FILE, newline="", encoding="utf-8") as f:
        return any(int(r["season"]) == season and int(r["round"]) == rnd for r in csv.DictReader(f))


def main():
    now = datetime.now(timezone.utc)
    season = now.year
    try:
        with urllib.request.urlopen(f"{BASE_URL}/{season}.json", timeout=30) as reply:
            races = json.load(reply)["MRData"]["RaceTable"]["Races"]
    except Exception as error:
        return answer(False, f"Couldn't read the race calendar ({error}). Trying again next run.")

    upcoming = [r for r in races if race_start(r) > now]
    if not upcoming:
        return answer(False, "No races left this season.")
    race = upcoming[0]
    rnd, start = int(race["round"]), race_start(race)
    lock_at = start - timedelta(hours=LOCK_HOURS)
    print(f"Next race: {race['raceName']} (round {rnd}), lights out {start:%a %d %b %H:%M} UTC, "
          f"lock time {lock_at:%a %d %b %H:%M} UTC")

    if now < lock_at:
        return answer(False, "Not lock time yet.")
    if already_locked(season, rnd):
        return answer(False, "Already locked in.")
    return answer(True, "Lock time has passed and it isn't locked yet.")


if __name__ == "__main__":
    main()
