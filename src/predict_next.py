import argparse
import sys

import joblib
import numpy as np
import pandas as pd
import requests

from features import (TEAM_MAP, add_driver_features, add_team_features,
                      add_season_features, add_gain_features)

BASE_URL = "https://api.jolpi.ca/ergast/f1"


def get_race_info(season, rnd):
    """Race name and circuit from the calendar (works for future races too)."""
    data = requests.get(f"{BASE_URL}/{season}/{rnd}.json", timeout=30).json()
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        sys.exit(f"No round {rnd} in the {season} calendar.")
    return races[0]["raceName"], races[0]["Circuit"]["circuitId"], races[0]["date"]


def get_qualifying(season, rnd):
    """Real qualifying results, or None if qualifying hasn't happened yet."""
    data = requests.get(f"{BASE_URL}/{season}/{rnd}/qualifying.json", timeout=30).json()
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        return None
    return pd.DataFrame([{
        "driver": q["Driver"]["driverId"],
        "constructor": q["Constructor"]["constructorId"],
        "quali_position": int(q["position"]),
    } for q in races[0]["QualifyingResults"]])


def estimate_grid(history, season):
    """No qualifying yet: rank drivers by their average qualifying this season."""
    this_season = history[history["season"] == season]
    last_round = this_season["round"].max()
    entry = this_season[this_season["round"] == last_round][["driver", "constructor"]].copy()
    avg_q = this_season.groupby("driver")["quali_position"].mean()
    entry["quali_position"] = entry["driver"].map(avg_q).rank(method="first").astype(int)
    return entry


def prepare(df):
    """Same cleaning as features.py, then all the feature functions."""
    df = df.sort_values(["season", "round"]).reset_index(drop=True)
    df["constructor"] = df["constructor"].replace(TEAM_MAP)
    df["podium"] = (df["finish_position"] <= 3).astype(int)
    finished = (df["status"].eq("Finished")
                | df["status"].str.startswith("+")
                | df["status"].eq("Lapped"))
    df["dnf"] = (~finished).astype(int)
    df["grid"] = df["grid"].replace(0, 20)
    df["quali_position"] = df["quali_position"].fillna(df["grid"])
    df = add_driver_features(df)
    df = add_team_features(df)
    df = add_season_features(df)
    df = add_gain_features(df)
    return df


def main():
    parser = argparse.ArgumentParser(description="Predict the podium for an upcoming race")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()

    history = pd.read_csv("data/processed/results.csv")
    done = (history["season"] == args.season) & (history["round"] == args.round)
    if done.any():
        sys.exit("That race already happened. Use src/predict.py for past races.")

    race_name, circuit, date = get_race_info(args.season, args.round)
    quali = get_qualifying(args.season, args.round)
    mode = "real qualifying results"
    if quali is None:
        quali = estimate_grid(history, args.season)
        mode = "ESTIMATED grid (qualifying hasn't happened yet)"

    # Rows for the upcoming race: no result yet, so finish/points are blank
    new_rows = quali.assign(
        season=args.season, round=args.round, race_name=race_name,
        circuit=circuit, date=date, grid=quali["quali_position"],
        finish_position=np.nan, status="Upcoming", points=np.nan)

    df = prepare(pd.concat([history, new_rows], ignore_index=True))
    race = df[(df["season"] == args.season) & (df["round"] == args.round)].copy()

    bundle = joblib.load("models/podium_model.joblib")
    race["podium_chance_%"] = (
        bundle["model"].predict_proba(race[bundle["features"]])[:, 1] * 100).round(1)
    race = race.sort_values("podium_chance_%", ascending=False)

    print(f"\n{race_name} {args.season}  (using {mode})\n")
    print(race[["driver", "constructor", "grid", "podium_chance_%"]]
          .head(10).to_string(index=False))
    print("\nPredicted podium:", ", ".join(race.head(3)["driver"]))


if __name__ == "__main__":
    main()