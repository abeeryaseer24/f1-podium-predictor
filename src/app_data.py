"""Cached data helpers shared by every page, so slow work isn't repeated on every click.
ttl = how many seconds a result is kept before it's loaded fresh."""
import json

import pandas as pd
import streamlit as st

from duel import fastest_laps, run_duel, session_key
from tyres import analyse as analyse_tyres
from replay import build_replay
from strategy import replay_payload
from engineer import game_pack

from predictor import (RACES_DIR, full_order, reasons, load_model, model_info, past_races, predict_past,
                       predict_upcoming, race_calendar, scoreboard, upcoming_races)


@st.cache_data(ttl=600)
def get_past_races():
    return past_races()


@st.cache_data(ttl=3600)
def get_upcoming(season):
    return upcoming_races(season)


@st.cache_data(ttl=600)
def run_past(season, rnd):
    return predict_past(season, rnd)


@st.cache_data(ttl=3600)
def run_upcoming(season, rnd):
    return predict_upcoming(season, rnd)


@st.cache_data(ttl=60)
def _scoreboard(kind):
    return scoreboard(kind)


def get_scoreboard(kind):
    """Saved predictions next to the real results. For the live scoreboard, this also locks
    the next race the moment its lock time passes (see lock_if_due)."""
    if kind == "live":
        try:
            if lock_if_due(_scoreboard("live")):
                _scoreboard.clear()
        except Exception:
            pass                            # never break a page over this; the robot locks it later
    return _scoreboard(kind)


def lock_if_due(live):
    """Lock the next race if its lock time has passed and nobody has locked it yet.
    The prediction is saved once in the database (the first save wins), so every visitor sees the same
    locked pick, and the robot later copies it into predictions.csv. Returns True if a lock was saved."""
    from datetime import datetime, timedelta, timezone
    from locks import save_lock
    from log_prediction import LOCK_HOURS, build_lock
    from predictor import RESULTS_CSV, current_season

    now = datetime.now(timezone.utc)
    season = current_season()
    results = pd.read_csv(RESULTS_CSV, usecols=["season", "round"])
    finished = set(zip(results["season"], results["round"]))
    race = next((r for r in get_calendar(season) if (season, r["round"]) not in finished), None)
    if race is None or not (race["race_start"] - timedelta(hours=LOCK_HOURS) <= now < race["race_start"]):
        return False
    if not live.empty and ((live["season"] == season) & (live["round"] == race["round"])).any():
        return False                        # already locked
    row, _ = build_lock(season, race["round"], race["race_start"], now)
    return row is not None and save_lock(row) is not None


@st.cache_data(ttl=600)
def get_model_info():
    return model_info()


@st.cache_data(ttl=3600)
def get_calendar(season):
    return race_calendar(season)


@st.cache_data(ttl=600)
def get_backtests():
    """Every backtested race (each season by a model that never saw it), or an empty table."""
    path = RACES_DIR.parent / "predictions" / "backtests.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


@st.cache_data(ttl=600)
def get_reasons(kind, season, rnd):
    """'Why this pick?' for the podium of a past or upcoming race."""
    result = run_past(season, rnd) if kind == "past" else run_upcoming(season, rnd)
    model, _ = load_model()
    return reasons(result["table"], model)


@st.cache_data(ttl=600)
def get_full_order(season, rnd, order):
    return full_order(season, rnd, order)


@st.cache_data(ttl=600)
def get_model_weights():
    """How much each input moves a driver's strength in the live model (one row per input)."""
    model, features = load_model()
    return pd.DataFrame({"feature": features, "weight": [model["weights"][f] for f in features]})


# ---------- prepared race files (for the 3D pages) ----------

@st.cache_data(ttl=600)
def get_prepared_races():
    """Every race that has a complete folder: season, round, race_name, folder."""
    rows = []
    for folder in sorted(RACES_DIR.glob("*_*")):
        info_file = folder / "info.json"
        if info_file.exists():
            info = json.loads(info_file.read_text())
            rows.append({"season": info["season"], "round": info["round"],
                         "race_name": info["race_name"], "folder": folder.name})
    return pd.DataFrame(rows)


@st.cache_data(ttl=600)
def get_race_file(folder, name):
    """One prepared table, e.g. get_race_file("2026_19", "track")."""
    return pd.read_parquet(RACES_DIR / folder / f"{name}.parquet")


@st.cache_data(ttl=600)
def get_race_info(folder):
    return json.loads((RACES_DIR / folder / "info.json").read_text())

@st.cache_data(ttl=600)
def get_corners(folder):
    """Corner labels for a race, or [] if they haven't been made yet."""
    path = RACES_DIR / folder / "corners.json"
    return json.loads(path.read_text()) if path.exists() else []

# ---------- Ghost Lap Duel (live from OpenF1, kept for a day) ----------

@st.cache_data(ttl=86400)
def get_fastest_laps(folder, session_name):
    return fastest_laps(session_key(folder, session_name))


@st.cache_data(ttl=86400)
def get_duel(folder, session_name, num_a, num_b):
    return run_duel(folder, session_name, num_a, num_b)

# ---------- Tyre Lab ----------

@st.cache_data(ttl=600)
def get_tyres(folder):
    return analyse_tyres(folder)

# ---------- Pit Wall ----------

@st.cache_data(ttl=600)
def get_replay(folder):
    return build_replay(folder)



@st.cache_data(ttl=600)
def get_strategy(folder):
    return replay_payload(folder)


@st.cache_data(ttl=86400)
def get_game(folder):
    return game_pack(folder)


@st.cache_data(ttl=600)
def get_model_history():
    """Every champion-vs-challenger decision (newest last), or an empty list."""
    path = RACES_DIR.parent.parent / "models" / "history.json"
    return json.loads(path.read_text()) if path.exists() else []
