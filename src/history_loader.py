"""Download the whole history of Formula 1, 1950 to now, from the Jolpica-F1 API.

The prediction model only needs recent seasons, so data/processed/results.csv starts in
2016. The History pages need everything, which is what this script fetches:

  data/processed/history_results.csv    every race result ever, one row per driver per race
  data/processed/history_drivers.csv    the final drivers' table for every season
  data/processed/history_teams.csv      the final constructors' table (1958 onwards)
  data/processed/history_races.csv      every race: circuit, country and where it is

It is kind to the free API and it can be stopped and restarted. Seasons already saved are
skipped, so if it stops on a rate limit, just run it again and it carries on:

  python src/history_loader.py                  # fill in whatever is missing
  python src/history_loader.py --from 1950 --to 1979
  python src/history_loader.py --refresh        # re-download the current season
  python src/history_loader.py --full           # start again from scratch

The official standings are downloaded rather than added up, because the rules before 1991
only counted a driver's best few results, so adding up every race gives the wrong champion.
"""
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
FIRST_SEASON = 1950
LIMIT = 100
PAUSE = 0.6                  # seconds between calls, to stay inside the free limits

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS_FILE = PROCESSED / "history_results.csv"
DRIVERS_FILE = PROCESSED / "history_drivers.csv"
TEAMS_FILE = PROCESSED / "history_teams.csv"
RACES_FILE = PROCESSED / "history_races.csv"


def get_json(url, params):
    """Call the API. If it says we are going too fast, wait longer each time and retry."""
    for attempt in range(6):
        resp = requests.get(url, params=params, timeout=40)
        if resp.status_code == 429:
            wait = 10 * (attempt + 1)
            print(f"    rate limited, waiting {wait}s...", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"API kept refusing: {url}")


def full_name(driver):
    return f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip()


# ---------- one season at a time ----------

def fetch_results(season):
    """Every race result of one season, plus a row per race for the calendar file."""
    rows, races, offset = [], {}, 0
    while True:
        data = get_json(f"{BASE_URL}/{season}/results.json",
                        {"limit": LIMIT, "offset": offset})["MRData"]
        for race in data["RaceTable"]["Races"]:
            circuit = race.get("Circuit", {})
            place = circuit.get("Location", {})
            races[int(race["round"])] = {
                "season": int(race["season"]),
                "round": int(race["round"]),
                "race_name": race["raceName"],
                "date": race.get("date", ""),
                "circuit": circuit.get("circuitId", ""),
                "circuit_name": circuit.get("circuitName", ""),
                "locality": place.get("locality", ""),
                "country": place.get("country", ""),
                "latitude": place.get("lat", ""),
                "longitude": place.get("long", ""),
            }
            for r in race["Results"]:
                fastest = r.get("FastestLap") or {}
                rows.append({
                    "season": int(race["season"]),
                    "round": int(race["round"]),
                    "race_name": race["raceName"],
                    "circuit": circuit.get("circuitId", ""),
                    "date": race.get("date", ""),
                    "driver": r["Driver"]["driverId"],
                    "driver_name": full_name(r["Driver"]),
                    "nationality": r["Driver"].get("nationality", ""),
                    "constructor": r["Constructor"]["constructorId"],
                    "constructor_name": r["Constructor"].get("name", ""),
                    "grid": int(r.get("grid", 0)),
                    "finish_position": int(r["position"]),
                    "position_text": r.get("positionText", ""),
                    "laps": int(r.get("laps", 0)),
                    "status": r.get("status", ""),
                    "points": float(r.get("points", 0)),
                    "fastest_lap_rank": int(fastest["rank"]) if fastest.get("rank") else 0,
                })
        total = int(data["total"])
        offset += LIMIT
        if offset >= total or total == 0:
            break
        time.sleep(PAUSE)
    return rows, list(races.values())


def fetch_driver_standings(season):
    """The official final drivers' table for one season."""
    data = get_json(f"{BASE_URL}/{season}/driverstandings.json", {"limit": LIMIT})["MRData"]
    lists = data["StandingsTable"]["StandingsLists"]
    if not lists:
        return []
    return [{
        "season": season,
        # drivers who scored no points have no championship position; leave it blank
        "position": int(s["position"]) if s.get("position") else "",
        "driver": s["Driver"]["driverId"],
        "driver_name": full_name(s["Driver"]),
        "nationality": s["Driver"].get("nationality", ""),
        "constructor": ", ".join(c["constructorId"] for c in s.get("Constructors", [])),
        "constructor_name": ", ".join(c.get("name", "") for c in s.get("Constructors", [])),
        "points": float(s["points"]),
        "wins": int(s["wins"]),
    } for s in lists[0]["DriverStandings"]]


def fetch_team_standings(season):
    """The official final constructors' table for one season (there is none before 1958)."""
    data = get_json(f"{BASE_URL}/{season}/constructorstandings.json", {"limit": LIMIT})["MRData"]
    lists = data["StandingsTable"]["StandingsLists"]
    if not lists:
        return []
    return [{
        "season": season,
        "position": int(s["position"]) if s.get("position") else "",
        "constructor": s["Constructor"]["constructorId"],
        "constructor_name": s["Constructor"].get("name", ""),
        "nationality": s["Constructor"].get("nationality", ""),
        "points": float(s["points"]),
        "wins": int(s["wins"]),
    } for s in lists[0]["ConstructorStandings"]]


# ---------- saving ----------

def read_existing(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def merge_season(old, new_rows, season, columns):
    """Replace this season's rows with the freshly downloaded ones."""
    new = pd.DataFrame(new_rows, columns=columns)
    if old.empty:
        return new
    kept = old[old["season"] != season]
    return pd.concat([kept, new], ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description="Download the full history of F1")
    parser.add_argument("--from", dest="start", type=int, default=FIRST_SEASON)
    parser.add_argument("--to", dest="end", type=int, default=None)
    parser.add_argument("--full", action="store_true", help="start again from scratch")
    parser.add_argument("--refresh", action="store_true",
                        help="also re-download seasons that are already saved")
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    this_year = datetime.now(timezone.utc).year
    end = args.end or this_year

    results = pd.DataFrame() if args.full else read_existing(RESULTS_FILE)
    drivers = pd.DataFrame() if args.full else read_existing(DRIVERS_FILE)
    teams = pd.DataFrame() if args.full else read_existing(TEAMS_FILE)
    races = pd.DataFrame() if args.full else read_existing(RACES_FILE)

    have_results = set(results["season"].unique()) if not results.empty else set()
    have_standings = set(drivers["season"].unique()) if not drivers.empty else set()
    # the newest season is always refreshed, because it is still being raced
    newest = max(have_results) if have_results else None

    def needs(season, have):
        return args.full or args.refresh or season == newest or season not in have

    todo = [s for s in range(args.start, end + 1)
            if needs(s, have_results) or needs(s, have_standings)]
    if not todo:
        print("Everything is already downloaded. Use --refresh to do it again.")
        return

    print(f"{len(todo)} season(s) to fetch: {todo[0]} to {todo[-1]}")
    for season in todo:
        print(f"  {season}...", flush=True)

        if needs(season, have_results):
            try:
                season_rows, season_races = fetch_results(season)
            except Exception as problem:
                print(f"  stopped at {season}: {problem}")
                print("  What has been downloaded so far is saved. "
                      "Run the script again to carry on.")
                break
            if not season_rows:
                print(f"  {season}: no races yet, skipping")
                continue
            results = merge_season(results, season_rows, season, list(season_rows[0]))
            races = merge_season(races, season_races, season, list(season_races[0]))
            time.sleep(PAUSE)

        # Standings are fetched whenever they are missing, even if the results are
        # already saved, so a season that failed half way is put right on the next run.
        if needs(season, have_standings):
            try:
                ds = fetch_driver_standings(season)
                time.sleep(PAUSE)
                ts = fetch_team_standings(season)
                time.sleep(PAUSE)
            except Exception as problem:
                print(f"  standings for {season} failed: {problem} "
                      "(run the script again later to fill them in)")
                ds, ts = [], []
            if ds:
                drivers = merge_season(drivers, ds, season, list(ds[0]))
            if ts:
                teams = merge_season(teams, ts, season, list(ts[0]))

        # Save after every season, so a stopped run never loses what it already has.
        results.sort_values(["season", "round", "finish_position"]).to_csv(RESULTS_FILE, index=False)
        races.sort_values(["season", "round"]).to_csv(RACES_FILE, index=False)
        if not drivers.empty:
            drivers.sort_values(["season", "position"]).to_csv(DRIVERS_FILE, index=False)
        if not teams.empty:
            teams.sort_values(["season", "position"]).to_csv(TEAMS_FILE, index=False)

    print(f"\nDone. {len(results)} results across "
          f"{results['season'].nunique() if not results.empty else 0} seasons.")
    print(f"Saved to {RESULTS_FILE.name}, {DRIVERS_FILE.name}, {TEAMS_FILE.name} "
          f"and {RACES_FILE.name}")


if __name__ == "__main__":
    main()
