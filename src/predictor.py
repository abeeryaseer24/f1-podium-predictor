"""Shared prediction engine, used by predict.py, predict_next.py and the web app."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests

from features import (TEAM_MAP, add_driver_features, add_team_features,
                      add_season_features, add_gain_features)

# Paths that work no matter which folder you run from
ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = ROOT / "data" / "processed" / "results.csv"
FEATURES_CSV = ROOT / "data" / "processed" / "features.csv"
MODEL_FILE = ROOT / "models" / "podium_model.joblib"
BASE_URL = "https://api.jolpi.ca/ergast/f1"


# ---------- small helpers ----------

def clean_name(driver_id):
    """'max_verstappen' -> 'Max Verstappen'"""
    return driver_id.replace("_", " ").title()


def load_model():
    bundle = joblib.load(MODEL_FILE)
    return bundle["model"], bundle["features"]


def score_race(race, model, features):
    """Give every driver a podium chance (%) and sort, best first."""
    race = race.copy()
    race["podium_chance"] = (model.predict_proba(race[features])[:, 1] * 100).round(1)
    race["name"] = race["driver"].map(clean_name)
    return race.sort_values("podium_chance", ascending=False).reset_index(drop=True)


# ---------- race lists (for the app's dropdowns) ----------

def past_races():
    """Every race we have results for: season, round, race_name."""
    df = pd.read_csv(RESULTS_CSV, usecols=["season", "round", "race_name"])
    return df.drop_duplicates(["season", "round"]).sort_values(["season", "round"])


def upcoming_races(season):
    """Races in the calendar that haven't happened yet."""
    data = requests.get(f"{BASE_URL}/{season}.json", timeout=30).json()
    races = data["MRData"]["RaceTable"]["Races"]
    results = pd.read_csv(RESULTS_CSV, usecols=["season", "round"])
    done = set(results.loc[results["season"] == season, "round"])
    return pd.DataFrame([
        {"round": int(r["round"]), "race_name": r["raceName"], "date": r["date"]}
        for r in races if int(r["round"]) not in done
    ])


# ---------- past races ----------

def predict_past(season, rnd):
    """Prediction for a race that already happened, plus the real podium."""
    model, features = load_model()
    df = pd.read_csv(FEATURES_CSV)
    race = df[(df["season"] == season) & (df["round"] == rnd)]
    if race.empty:
        raise ValueError(f"No results for season {season}, round {rnd}.")

    race = score_race(race, model, features)
    predicted = race.head(3)["name"].tolist()
    actual = race.sort_values("finish_position").head(3)["name"].tolist()
    return {
        "race_name": race["race_name"].iloc[0],
        "table": race,
        "predicted": predicted,
        "actual": actual,
        "correct": len(set(predicted) & set(actual)),
    }


# ---------- upcoming races ----------

def get_race_info(season, rnd):
    data = requests.get(f"{BASE_URL}/{season}/{rnd}.json", timeout=30).json()
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        raise ValueError(f"No round {rnd} in the {season} calendar.")
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


def predict_upcoming(season, rnd):
    """Prediction for a race that hasn't happened yet."""
    history = pd.read_csv(RESULTS_CSV)
    if ((history["season"] == season) & (history["round"] == rnd)).any():
        raise ValueError("That race already happened. Use predict_past instead.")

    race_name, circuit, date = get_race_info(season, rnd)
    quali = get_qualifying(season, rnd)
    real_quali = quali is not None
    if not real_quali:
        quali = estimate_grid(history, season)

    new_rows = quali.assign(
        season=season, round=rnd, race_name=race_name, circuit=circuit, date=date,
        grid=quali["quali_position"], finish_position=np.nan,
        status="Upcoming", points=np.nan)

    df = prepare(pd.concat([history, new_rows], ignore_index=True))
    race = df[(df["season"] == season) & (df["round"] == rnd)]

    model, features = load_model()
    race = score_race(race, model, features)
    return {
        "race_name": race_name,
        "date": date,
        "table": race,
        "predicted": race.head(3)["name"].tolist(),
        "real_quali": real_quali,
    }