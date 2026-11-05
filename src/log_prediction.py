"""Lock in the prediction for the next race (the podium and the whole order), once its qualifying is done.

Rules that keep the scoreboard fair:
- only races that haven't started yet
- only with the real qualifying grid (never the estimated one)
- once a race is saved, it is never changed
"""
import argparse
import json
from datetime import datetime, timezone

import pandas as pd

from predictor import (ROOT, current_season, get_race_start, load_model, model_version,
                       predict_upcoming, reasons, upcoming_races)

LOG_FILE = ROOT / "data" / "predictions" / "predictions.csv"


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


def main():
    parser = argparse.ArgumentParser(description="Lock in the next race's podium prediction")
    parser.add_argument("--season", type=int, default=current_season())
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would be saved, without saving anything")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    rnd, start = next_race(args.season, now)
    if rnd is None:
        print("No races left to predict this season. Nothing to do.")
        return

    log = load_log()
    if not log.empty and ((log["season"] == args.season) & (log["round"] == rnd)).any():
        print(f"Round {rnd} is already locked in. Nothing to do.")
        return

    result = predict_upcoming(args.season, rnd)
    top3 = result["table"].head(3)

    print(f"\nNext race: {result['race_name']} {args.season} (round {rnd})")
    print(f"Race starts: {start:%Y-%m-%d %H:%M} UTC")
    print("Grid used:", "real qualifying" if result["real_quali"] else "ESTIMATED")
    for i, (_, r) in enumerate(top3.iterrows(), start=1):
        print(f"  P{i}: {r['name']} ({r['podium_chance']:.1f}%)")

    if args.dry_run:
        print("\nDry run: nothing was saved.")
        return
    if not result["real_quali"]:
        print("\nQualifying hasn't happened yet, so nothing was locked in. "
              "Run this again after qualifying.")
        return

    row = {
        "season": args.season,
        "round": rnd,
        "race_name": result["race_name"],
        "race_start": start.isoformat(),
        "predicted_at": now.isoformat(timespec="seconds"),
        "model_version": model_version(),
    }
    for i, (_, r) in enumerate(top3.iterrows(), start=1):
        row[f"p{i}"] = r["driver"]
        row[f"p{i}_team"] = r["constructor"]
        row[f"p{i}_chance"] = r["podium_chance"]
    row["order"] = json.dumps(result["table"]["driver"].tolist())        # the whole predicted order, 1-22
    row["why"] = json.dumps(reasons(result["table"], load_model()[0]))   # "Why this pick?", saved with it

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([log, pd.DataFrame([row])], ignore_index=True).to_csv(LOG_FILE, index=False)
    print(f"\nLocked in! Saved to {LOG_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
