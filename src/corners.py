"""Corner numbers for the 3D pages.

Official corners come from the MultiViewer circuit data (the same source FastF1 used).
If that isn't available, corners are estimated from the fastest lap: every place where
the car clearly slows down counts as a corner. Estimated numbers can differ from the
official ones, and the app says so.

Saves data/races/<folder>/corners.json:
  [{"label": "T1", "i": 123, "source": "official"}, ...]
  (i = the nearest point in track.parquet, where the label is drawn)

Usage:
  python src/corners.py 2026 19      one race (prints what it found)
  python src/corners.py --missing    every prepared race without corners.json
To redo a race, delete its corners.json and run again.
"""
import argparse
import json

import pandas as pd
import requests

from predictor import RACES_DIR
from prepare_race import get

MULTIVIEWER = "https://api.multiviewer.app/api/v1/circuits/{key}/{year}"
MAX_GAP = 400          # an official corner must lie within 40 m of our track line (units: 1/10 m)


# ---------- official corners ----------

def official_corners(circuit_key, year):
    """The official corner list for a circuit, or [] if it isn't available."""
    try:
        r = requests.get(MULTIVIEWER.format(key=circuit_key, year=year), timeout=30,
                         headers={"User-Agent": "f1-podium-predictor"})
        if r.status_code != 200:
            return []
        return r.json().get("corners", [])
    except (requests.RequestException, ValueError):
        return []


def nearest_index(track, x, y):
    """The track point closest to (x, y), and how far away it is."""
    dist = ((track["x"] - x) ** 2 + (track["y"] - y) ** 2) ** 0.5
    return int(dist.idxmin()), float(dist.min())


def from_official(track, corners):
    """Place each official corner on our track. If any doesn't line up, trust none."""
    placed = []
    for c in corners:
        spot = c.get("trackPosition") or {}
        if "x" not in spot or "y" not in spot:
            continue
        i, gap = nearest_index(track, spot["x"], spot["y"])
        if gap > MAX_GAP:
            return []
        placed.append({"label": f"T{c.get('number')}{c.get('letter') or ''}",
                       "i": i, "source": "official"})
    return placed


# ---------- estimated corners (backup) ----------

def estimated(track):
    """A corner = a point where the speed is lowest nearby, after a clear slow-down."""
    speed = track["speed"].rolling(5, center=True, min_periods=1).mean().to_numpy()
    found, last = [], -999
    for i in range(1, len(speed) - 1):
        nearby = speed[max(0, i - 8): i + 9]
        slowed_down = speed[max(0, i - 15): i].max() - speed[i] > 15      # km/h
        if speed[i] == nearby.min() and slowed_down and i - last > 10:
            found.append(i)
            last = i
    return [{"label": f"T{k}", "i": i, "source": "estimated"}
            for k, i in enumerate(found, start=1)]


# ---------- one race ----------

def make_corners(folder):
    info = json.loads((RACES_DIR / folder / "info.json").read_text())
    track = pd.read_parquet(RACES_DIR / folder / "track.parquet")

    session = get("sessions", {"session_key": info["openf1_session_key"]})
    circuit_key = session[0].get("circuit_key") if session else None

    corners = []
    if circuit_key:
        for year in (info["season"], info["season"] - 1):     # this year's map, else last year's
            corners = from_official(track, official_corners(circuit_key, year))
            if corners:
                break
    if not corners:
        corners = estimated(track)

    (RACES_DIR / folder / "corners.json").write_text(json.dumps(corners, indent=2))
    source = corners[0]["source"] if corners else "none found"
    print(f"  {folder} ({info['race_name']}): {len(corners)} corners, {source}")


def main():
    parser = argparse.ArgumentParser(description="Add corner numbers to prepared races")
    parser.add_argument("season", type=int, nargs="?")
    parser.add_argument("round", type=int, nargs="?")
    parser.add_argument("--missing", action="store_true",
                        help="every prepared race that doesn't have corners.json yet")
    args = parser.parse_args()

    if args.missing:
        folders = [p.name for p in sorted(RACES_DIR.glob("*_*"))
                   if (p / "info.json").exists() and not (p / "corners.json").exists()]
        print(f"{len(folders)} races need corner numbers.")
        for folder in folders:
            try:
                make_corners(folder)
            except Exception as error:
                print(f"  Skipped {folder}: {error}")
    elif args.season and args.round:
        make_corners(f"{args.season}_{args.round:02d}")
    else:
        parser.error("give a season and a round, or use --missing")


if __name__ == "__main__":
    main()