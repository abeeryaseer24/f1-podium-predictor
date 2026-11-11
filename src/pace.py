"""How fast each car really was, race by race.

A finishing position hides a lot: a quick car can be stuck behind a slow one, and a slow
car can inherit a good result. This measures pace from the lap times instead.

For every race we have prepared (2023 onwards, in data/races/), it takes each driver's
clean racing laps, averages their fastest quarter of them, and compares that with the
fastest car of the weekend. The answer is a percentage: 0.0% is the fastest car that
weekend, 1.2% means a lap and a bit over a second slower on a 90-second lap.

A team's pace is its better car, so one driver having a scrappy race does not drag the
team's number down.

Run it to build the files (the pipeline does this automatically):
  python src/pace.py

It writes data/processed/pace_teams.csv and data/processed/pace_drivers.csv.
"""
import json
from pathlib import Path

import pandas as pd

from teaminfo import openf1_team_id

ROOT = Path(__file__).resolve().parent.parent
RACES_DIR = ROOT / "data" / "races"
PROCESSED = ROOT / "data" / "processed"
TEAM_FILE = PROCESSED / "pace_teams.csv"
DRIVER_FILE = PROCESSED / "pace_drivers.csv"

SLOW_LIMIT = 1.07      # laps more than 7% slower than the driver's normal lap are thrown out
MIN_LAPS = 8           # a driver needs this many clean laps to get a pace number
FAST_SHARE = 0.25      # we average the fastest quarter of a driver's clean laps
WET_COMPOUNDS = ("INTERMEDIATE", "WET")


def clean_laps(laps):
    """Racing laps only: no lap 1, no pit in-lap or out-lap, no safety-car crawls."""
    laps = laps.sort_values(["driver_number", "lap_number"]).copy()
    out_lap = laps["is_pit_out_lap"].fillna(False).astype(bool)
    in_lap = (laps.groupby("driver_number")["is_pit_out_lap"].shift(-1)
              .fillna(False).astype(bool))
    keep = laps["lap_duration"].notna() & (laps["lap_number"] > 1) & ~out_lap & ~in_lap
    clean = laps[keep].copy()
    if clean.empty:
        return clean
    normal = clean.groupby("driver_number")["lap_duration"].transform("median")
    return clean[clean["lap_duration"] <= normal * SLOW_LIMIT]


def driver_pace(clean):
    """Each driver's representative pace: the average of their fastest quarter of laps."""
    rows = []
    for number, group in clean.groupby("driver_number"):
        times = group["lap_duration"].sort_values()
        if len(times) < MIN_LAPS:
            continue
        take = max(3, int(round(len(times) * FAST_SHARE)))
        rows.append({"driver_number": int(number),
                     "pace": float(times.head(take).mean()),
                     "laps_used": take,
                     "clean_laps": int(len(times))})
    return pd.DataFrame(rows)


def surname(name):
    """'Lando NORRIS' -> 'norris'. OpenF1 puts the family name in capitals."""
    parts = str(name).split()
    return parts[-1].lower() if parts else ""


def driver_ids_for(season, rnd, results):
    """Match this race's drivers to the driver ids the rest of the project uses,
    by family name. Returns {family name: driver id}."""
    race = results[(results["season"] == season) & (results["round"] == rnd)]
    return {d.split("_")[-1].lower(): d for d in race["driver"].unique()}


def race_pace(folder, results):
    """Pace for one prepared race, as two tables: by driver and by team."""
    info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    laps_file = folder / "laps.parquet"
    if not laps_file.exists():
        return None, None

    laps = pd.read_parquet(laps_file)
    clean = clean_laps(laps)
    if clean.empty:
        return None, None

    wet = False
    if "compound" in clean.columns:
        wet = bool(clean["compound"].isin(WET_COMPOUNDS).mean() > 0.2)

    pace = driver_pace(clean)
    if pace.empty:
        return None, None

    entries = pd.DataFrame(info.get("drivers", []))
    if entries.empty:
        return None, None
    entries["team_id"] = entries["team"].map(openf1_team_id)
    entries["surname"] = entries["name"].map(surname)

    lookup = driver_ids_for(info["season"], info["round"], results)
    entries["driver"] = entries["surname"].map(lookup)

    table = pace.merge(entries[["number", "driver", "team_id", "code"]],
                       left_on="driver_number", right_on="number", how="left")
    best = table["pace"].min()
    table["pct_off"] = (100 * (table["pace"] / best - 1)).round(3)
    for key, value in (("season", info["season"]), ("round", info["round"]),
                       ("race_name", info["race_name"]), ("wet", wet)):
        table[key] = value

    teams = (table.dropna(subset=["team_id"])
             .groupby("team_id", as_index=False)
             .agg(pace=("pace", "min"), clean_laps=("clean_laps", "sum")))
    teams["pct_off"] = (100 * (teams["pace"] / teams["pace"].min() - 1)).round(3)
    teams = teams.rename(columns={"team_id": "constructor"})
    for key, value in (("season", info["season"]), ("round", info["round"]),
                       ("race_name", info["race_name"]), ("wet", wet)):
        teams[key] = value

    cols = ["season", "round", "race_name", "wet", "driver", "code", "team_id",
            "driver_number", "pace", "pct_off", "clean_laps"]
    return table[cols], teams[["season", "round", "race_name", "wet", "constructor",
                               "pace", "pct_off", "clean_laps"]]


def build():
    """Walk every prepared race and write the two pace files."""
    results = pd.read_csv(PROCESSED / "results.csv", usecols=["season", "round", "driver"])
    driver_rows, team_rows = [], []
    for folder in sorted(RACES_DIR.glob("*_*")):
        if not (folder / "info.json").exists():
            continue
        try:
            drivers, teams = race_pace(folder, results)
        except Exception as error:                     # one bad race must not stop the rest
            print(f"  skipped {folder.name}: {error}")
            continue
        if drivers is None:
            continue
        driver_rows.append(drivers)
        team_rows.append(teams)
        print(f"  {folder.name}: {len(teams)} teams")

    if not team_rows:
        print("No prepared races with lap times were found.")
        return

    PROCESSED.mkdir(parents=True, exist_ok=True)
    pd.concat(driver_rows, ignore_index=True).to_csv(DRIVER_FILE, index=False)
    pd.concat(team_rows, ignore_index=True).to_csv(TEAM_FILE, index=False)
    print(f"Done. {len(team_rows)} races written to {TEAM_FILE.name} and {DRIVER_FILE.name}")


# ---------- reading the files back (used by the app) ----------

def team_pace(dry_only=False):
    """Team pace per race, or an empty table if src/pace.py has never been run."""
    if not TEAM_FILE.exists():
        return pd.DataFrame(columns=["season", "round", "race_name", "wet",
                                     "constructor", "pace", "pct_off", "clean_laps"])
    table = pd.read_csv(TEAM_FILE)
    return table[~table["wet"].astype(bool)] if dry_only else table


def driver_pace_table(dry_only=False):
    """Driver pace per race, or an empty table if the file has not been built."""
    if not DRIVER_FILE.exists():
        return pd.DataFrame(columns=["season", "round", "race_name", "wet", "driver",
                                     "code", "team_id", "driver_number", "pace",
                                     "pct_off", "clean_laps"])
    table = pd.read_csv(DRIVER_FILE)
    return table[~table["wet"].astype(bool)] if dry_only else table


def smooth(table, group_col, window=3):
    """A rolling average over the last few races, because one race on its own is noisy."""
    table = table.sort_values(["season", "round"]).copy()
    table["smoothed"] = (table.groupby(group_col)["pct_off"]
                         .transform(lambda s: s.rolling(window, min_periods=1).mean())
                         .round(3))
    return table


if __name__ == "__main__":
    build()
