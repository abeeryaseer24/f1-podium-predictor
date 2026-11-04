"""Shared prediction engine, used by predict.py, predict_next.py and the web app."""
from datetime import datetime, timezone
from functools import lru_cache
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



def current_season():
    """The season we're in, based on today's date (2027 starts by itself)."""
    return datetime.now(timezone.utc).year


# ---------- small helpers ----------

def clean_name(driver_id):
    """'max_verstappen' -> 'Max Verstappen'"""
    return driver_id.replace("_", " ").title()


@lru_cache(maxsize=1)
def _load_model(modified_time):
    bundle = joblib.load(MODEL_FILE)
    return bundle["model"], bundle["features"]


def load_model():
    """The saved model, loaded once and kept in memory.
    It reloads by itself when the model file changes (after the robot retrains)."""
    return _load_model(MODEL_FILE.stat().st_mtime)


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
    if this_season.empty:   # first race of a new season: use last season's form
     this_season = history[history["season"] == history["season"].max()]
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

# ================= Live system helpers =================
import json
from datetime import datetime, timezone

MODEL_INFO = ROOT / "models" / "model_info.json"


def get_race_start(season, rnd):
    """When the race starts, in UTC. Uses noon UTC if the calendar has no time yet."""
    data = requests.get(f"{BASE_URL}/{season}/{rnd}.json", timeout=30).json()
    race = data["MRData"]["RaceTable"]["Races"][0]
    time = race.get("time", "12:00:00Z").replace("Z", "+00:00")
    return datetime.fromisoformat(f"{race['date']}T{time}")


def model_version():
    """Which model made a prediction: the time it was trained.
    (Step 4 adds model_info.json; until then we use the model file's save time.)"""
    if MODEL_INFO.exists():
        return json.loads(MODEL_INFO.read_text())["trained_at"]
    saved = datetime.fromtimestamp(MODEL_FILE.stat().st_mtime, timezone.utc)
    return saved.isoformat(timespec="seconds")

# ================= Scoreboard =================
PREDICTIONS_DIR = ROOT / "data" / "predictions"
SCOREBOARD_FILES = {
    "live": PREDICTIONS_DIR / "predictions.csv",        # 2026, locked before each race
    "backtest": PREDICTIONS_DIR / "backtest_2025.csv",  # 2025, model trained on 2016-2024
}


def scoreboard(kind):
    """Every saved prediction next to the real result.
    kind = "live" or "backtest". One row per race."""
    file = SCOREBOARD_FILES[kind]
    if not file.exists():
        return pd.DataFrame()

    preds = pd.read_csv(file)
    results = pd.read_csv(RESULTS_CSV)
    results["constructor"] = results["constructor"].replace(TEAM_MAP)

    rows = []
    for _, p in preds.iterrows():
        row = p.to_dict()
        row["predicted"] = [p["p1"], p["p2"], p["p3"]]
        race = results[(results["season"] == p["season"]) & (results["round"] == p["round"])]

        if race.empty:                      # no result yet
            row.update(status="waiting", actual=[], actual_teams=[],
                       model_hits=None, grid_hits=None)
        else:
            podium = race.sort_values("finish_position").head(3)
            front_row = race[race["grid"] > 0].sort_values("grid").head(3)["driver"].tolist()
            actual = podium["driver"].tolist()
            row.update(
                status="done",
                actual=actual,
                actual_teams=podium["constructor"].tolist(),
                model_hits=len(set(row["predicted"]) & set(actual)),
                grid_hits=len(set(front_row) & set(actual)),
            )
        rows.append(row)
    return pd.DataFrame(rows)


def season_summary(board):
    """Totals and averages for the finished races: the model vs the grid."""
    if board.empty:
        return {"races": 0, "waiting": 0}
    done = board[board["status"] == "done"]
    races = len(done)
    summary = {"races": races, "waiting": len(board) - races}
    if races:
        summary.update(
            model_hits=int(done["model_hits"].sum()),
            grid_hits=int(done["grid_hits"].sum()),
            model_avg=round(done["model_hits"].mean(), 2),
            grid_avg=round(done["grid_hits"].mean(), 2),
        )
    return summary

def model_info():
    """The model card written by train.py (None if it doesn't exist yet)."""
    if MODEL_INFO.exists():
        return json.loads(MODEL_INFO.read_text())
    return None