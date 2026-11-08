"""Lock in the prediction for the next race (the podium and the whole order) on race day.
It first copies any lock the app already saved in the database (src/locks.py), so both always match.

Rules that keep the scoreboard fair:
- only races that haven't started yet
- only with the real qualifying grid (never the estimated one)
- once a race is saved, it is never changed
"""
import argparse
import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from locks import get_locks, save_lock
from predictor import (ROOT, current_season, get_race_start, load_model, model_version,
                       predict_upcoming, reasons, upcoming_races)

LOG_FILE = ROOT / "data" / "predictions" / "predictions.csv"


LOCK_HOURS = 8           # lock on race day, this many hours before lights out (grid penalties are known by then)


def load_log():
    """All predictions saved so far (empty table if there are none yet)."""
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame()


def next_race(season, now):
    """The first race in the calendar that hasn't started yet."""
    upcoming = upcoming_races(season)
    if upcoming.empty:
        return None, None
    for rnd in sorted(upcoming["round"]):
        start = get_race_start(season, int(rnd))
        if start > now:
            return int(rnd), start
    return None, None


def build_lock(season, rnd, start, now):
    """The locked prediction row for one race, or (None, reason) if it can't be locked yet."""
    if now < start - timedelta(hours=LOCK_HOURS):
        return None, (f"Not locked yet: predictions are locked on race day, from {LOCK_HOURS} hours before "
                      f"lights out ({start - timedelta(hours=LOCK_HOURS):%Y-%m-%d %H:%M} UTC), so late grid "
                      "penalties are included (read from OpenF1's official starting grid).")
    if now >= start:
        return None, "The race has already started, so it's too late to lock it."
    result = predict_upcoming(season, rnd)
    if not result["real_quali"]:
        return None, "Qualifying results aren't online yet, so nothing was locked in."
    top3 = result["table"].head(3)
    row = {
        "season": int(season),
        "round": int(rnd),
        "race_name": result["race_name"],
        "race_start": start.isoformat(),
        "predicted_at": now.isoformat(timespec="seconds"),
        "model_version": model_version(),
    }
    for i, (_, r) in enumerate(top3.iterrows(), start=1):
        row[f"p{i}"] = r["driver"]
        row[f"p{i}_team"] = r["constructor"]
        row[f"p{i}_chance"] = float(r["podium_chance"])
    row["order"] = json.dumps(result["table"]["driver"].tolist())        # the whole predicted order, 1-22
    row["why"] = json.dumps(reasons(result["table"], load_model()[0]))   # "Why this pick?", saved with it
    row["penalties"] = json.dumps(result["penalties"])                   # grid penalties it knew about
    print("Grid used:", result.get("grid_source"))
    if result["penalties"]:
        print("Grid penalties applied:", ", ".join(f"{p['name']} ({p['note']})" for p in result["penalties"]))
    return row, "ok"


def append_to_log(rows):
    log = load_log()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([log, pd.DataFrame(rows)], ignore_index=True).to_csv(LOG_FILE, index=False)


def is_logged(log, season, rnd):
    return not log.empty and ((log["season"] == season) & (log["round"] == rnd)).any()


def main():
    parser = argparse.ArgumentParser(description="Lock in the next race's podium prediction")
    parser.add_argument("--season", type=int, default=current_season())
    args = parser.parse_args()
    now = datetime.now(timezone.utc)

    # 1. Copy any locks the app already saved in the database (exactly as they were saved).
    try:
        saved = get_locks(args.season)
    except Exception as error:
        print(f"Couldn't read the locks database ({error}); carrying on without it.")
        saved = []
    log = load_log()
    new = [r for r in saved if not is_logged(log, int(r["season"]), int(r["round"]))]
    if new:
        append_to_log(new)
        print("Copied from the locks database:", ", ".join(f"round {r['round']}" for r in new))

    # 2. Lock the next race ourselves if it's due and nobody has locked it yet.
    rnd, start = next_race(args.season, now)
    if rnd is None:
        print("No races left to predict this season. Nothing to do.")
        return
    if is_logged(load_log(), args.season, rnd):
        print(f"Round {rnd} is already locked in. Nothing to do.")
        return
    print(f"Next race: round {rnd}, starts {start:%Y-%m-%d %H:%M} UTC")
    row, why = build_lock(args.season, rnd, start, now)
    if row is None:
        print(why)
        return
    try:
        row = save_lock(row) or row          # if the app saved one first, use the app's
    except Exception as error:
        print(f"Couldn't save to the locks database ({error}); saving to the file only.")
    append_to_log([row])
    print(f"Locked in round {rnd}: {row['p1']}, {row['p2']}, {row['p3']}. Saved to predictions.csv.")


if __name__ == "__main__":
    main()
