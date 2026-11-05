"""Shared prediction engine, used by predict.py, predict_next.py and the web app.
The model ranks the whole field (see ranker.py): predicted position, win and podium chances."""
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests

import ranker
from features import (TEAM_MAP, add_driver_features, add_team_features,
                      add_season_features, add_gain_features, add_step9_features)

# Paths that work no matter which folder you run from
ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = ROOT / "data" / "processed" / "results.csv"
FEATURES_CSV = ROOT / "data" / "processed" / "features.csv"
MODEL_FILE = ROOT / "models" / "podium_model.joblib"
RACES_DIR = ROOT / "data" / "races"
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


# ---------- "Why this pick?": the biggest reasons behind a driver's strength ----------

REASON_GROUPS = {          # inputs that say the same thing are added up and shown as one reason
    "grid": ["log_grid", "log_quali", "grid_x_circuit", "quali_gap_teammate"],
    "car": ["log_team_best_q", "team_form_quali"],
    "form": ["driver_form_finish"],
    "team_form": ["team_form_finish"],
    "season": ["driver_season_avg_finish"],
    "team_season": ["constructor_season_podium_rate"],
    "career": ["driver_podium_rate", "driver_avg_finish"],
    "circuit": ["driver_circuit_podium_rate", "constructor_circuit_podium_rate"],
    "reliable": ["driver_form_dnf", "driver_dnf_rate"],
    "racecraft": ["driver_avg_gain", "constructor_avg_gain", "driver_beats_teammate"],
}


def _num(row, col):
    value = row.get(col)
    return None if value is None or value != value else float(value)


def reason_text(group, row):
    """One reason in plain words, using the driver's real numbers where we have them."""
    grid, quali = _num(row, "grid"), _num(row, "quali_position")
    if group == "grid":
        if grid and quali and int(quali) != int(grid):
            return f"Starts P{int(grid)} (qualified P{int(quali)})"
        return f"Starts P{int(grid)}" if grid else "Strong starting position"
    if group == "car":
        best = _num(row, "team_best_quali")
        if not best:
            return "Fast car this weekend"
        if best == 1:
            return "The fastest car in qualifying"
        if quali and best < quali:
            return f"Quick car: the teammate qualified P{int(best)}"
        return f"One of the quickest cars: P{int(best)} in qualifying"
    texts = {
        "form": ("driver_form_finish", "Averaging P{:.0f} in the last 5 races"),
        "team_form": ("team_form_finish", "The team is averaging P{:.0f} in the last 3 races"),
        "season": ("driver_season_avg_finish", "Averaging P{:.0f} this season"),
        "team_season": ("constructor_season_podium_rate", "The team is on the podium in {:.0%} of races this season"),
        "career": ("driver_podium_rate", "On the podium in {:.0%} of career races"),
        "circuit": ("driver_circuit_podium_rate", "On the podium in {:.0%} of past races here"),
    }
    if group in texts:
        col, text = texts[group]
        value = _num(row, col)
        if value is not None:
            return text.format(value)
    return {"reliable": "Rarely retires from races", "racecraft": "Usually gains places on race day",
            "team_season": "Strong team this season", "career": "Strong career record",
            "circuit": "Good record at this circuit"}.get(group, group)


def reasons(table, model, top=3):
    """The top reasons that helped each of the first three drivers in a predicted table:
    {driver_id: [{"text": ..., "size": 0-1}, ...]}. Only reasons that HELP are shown."""
    contrib = ranker.contributions(model, table)
    out = {}
    for i in table.index[:3]:
        row = table.loc[i]
        sums = {g: float(contrib.loc[i, [f for f in fs if f in contrib.columns]].sum())
                for g, fs in REASON_GROUPS.items()}
        best = sorted(((v, g) for g, v in sums.items() if v > 0.02), reverse=True)[:top]
        biggest = best[0][0] if best else 1.0
        out[row["driver"]] = [{"text": reason_text(g, row), "size": round(v / biggest, 2)} for v, g in best]
    return out


def score_race(race, model, features):
    """The predicted finishing order of one race, best first, with every driver's predicted
    position, win chance, podium chance and expected finish."""
    race = ranker.predict(model, ranker.add_model_columns(race))
    race["name"] = race["driver"].map(clean_name)
    return race


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
    race["places_off"] = race["finish_position"] - race["predicted_position"]
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
    df = add_step9_features(df)
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


# Time zone of each circuit, to show "at the track" times on the Home page
CIRCUIT_TZ = {
    "albert_park": "Australia/Melbourne", "shanghai": "Asia/Shanghai", "suzuka": "Asia/Tokyo",
    "bahrain": "Asia/Bahrain", "jeddah": "Asia/Riyadh", "miami": "America/New_York",
    "villeneuve": "America/Toronto", "monaco": "Europe/Monaco", "catalunya": "Europe/Madrid",
    "madring": "Europe/Madrid", "red_bull_ring": "Europe/Vienna", "silverstone": "Europe/London",
    "spa": "Europe/Brussels", "hungaroring": "Europe/Budapest", "zandvoort": "Europe/Amsterdam",
    "monza": "Europe/Rome", "imola": "Europe/Rome", "baku": "Asia/Baku", "marina_bay": "Asia/Singapore",
    "americas": "America/Chicago", "rodriguez": "America/Mexico_City", "interlagos": "America/Sao_Paulo",
    "vegas": "America/Los_Angeles", "losail": "Asia/Qatar", "yas_marina": "Asia/Dubai",
}
SESSIONS = [("FirstPractice", "Practice 1"), ("SecondPractice", "Practice 2"), ("ThirdPractice", "Practice 3"),
            ("SprintQualifying", "Sprint Qualifying"), ("SprintShootout", "Sprint Qualifying"),
            ("Sprint", "Sprint"), ("Qualifying", "Qualifying")]


def race_calendar(season):
    """Every race of a season: round, name, circuit, race start, qualifying start and every session
    (times in UTC; None if unknown)."""
    data = requests.get(f"{BASE_URL}/{season}.json", timeout=30).json()
    when = lambda d: datetime.fromisoformat(f"{d['date']}T{d.get('time', '12:00:00Z').replace('Z', '+00:00')}")
    races = []
    for r in data["MRData"]["RaceTable"]["Races"]:
        circuit = r.get("Circuit", {})
        sessions = sorted(((label, when(r[key])) for key, label in SESSIONS if key in r), key=lambda x: x[1])
        races.append({
            "round": int(r["round"]), "race_name": r["raceName"], "race_start": when(r),
            "quali_start": when(r["Qualifying"]) if "Qualifying" in r else None,
            "circuit_id": circuit.get("circuitId", ""), "circuit": circuit.get("circuitName", ""),
            "place": circuit.get("Location", {}).get("locality", ""),
            "track_tz": CIRCUIT_TZ.get(circuit.get("circuitId", "")),
            "sessions": sessions + [("Race", when(r))],
        })
    return races


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
    "backtests": PREDICTIONS_DIR / "backtests.csv",     # every season from 2022, each by a model that never saw it
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


def full_order(season, rnd, order):
    """A locked whole-order prediction next to the real result (once the race is done).
    Returns (rows, summary): one row per predicted position; summary is None before the result."""
    order = json.loads(order) if isinstance(order, str) else list(order)
    results = pd.read_csv(RESULTS_CSV)
    results["constructor"] = results["constructor"].replace(TEAM_MAP)
    race = results[(results["season"] == season) & (results["round"] == rnd)]
    last_team = results.sort_values(["season", "round"]).groupby("driver")["constructor"].last()
    real = dict(zip(race["driver"], race["finish_position"]))
    team = dict(zip(race["driver"], race["constructor"])) if not race.empty else {}

    rows = []
    for i, d in enumerate(order, start=1):
        pos = real.get(d)
        rows.append({"predicted": i, "driver": d, "name": clean_name(d),
                     "team": team.get(d, last_team.get(d, "")),
                     "real": int(pos) if pos == pos and pos is not None else None,
                     "off": None if pos is None or pos != pos else int(pos) - i})
    rows = pd.DataFrame(rows)
    if race.empty:
        return rows, None

    done = rows.dropna(subset=["real"])
    grid = race.assign(start=race["grid"].where(race["grid"] > 0, 99))
    grid_rank = grid["start"].rank(method="first")
    summary = {
        "model_off": round(float(done["off"].abs().mean()), 1),
        "grid_off": round(float((grid["finish_position"] - grid_rank).abs().mean()), 1),
        "spot_on": int((done["off"] == 0).sum()),
        "within_2": int((done["off"].abs() <= 2).sum()),
        "drivers": len(done),
    }
    return rows, summary


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
