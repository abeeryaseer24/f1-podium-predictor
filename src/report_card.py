"""Model Report Card: how trustworthy are the model's percentages?

The backtest (train.py) keeps only the predicted podium. This replays the same honest test
for the live recipe and keeps EVERY driver's win and podium chance, so the chances themselves
can be graded:

  Brier score     the average squared gap between a chance and what happened (0 is perfect;
                  always saying 15% for a podium scores about 0.13)
  log loss        like Brier, but punishes confident mistakes much harder
  skill vs grid   how much better the Brier score is than a fair baseline: the podium rate
                  each grid slot has had in earlier seasons
  calibration     of all the times the model said "about 30%", did it happen about 30% of the time?
  finish ranges   for each predicted position, the range of real finishes that held 80% of
                  the time in the test (an empirical prediction interval)

Each season is predicted by a model trained only on the seasons before it, exactly as in
train.py, so nothing here has seen the races it is graded on.

Writes data/predictions/backtest_probs.csv. The pipeline runs it after retraining.

Usage:
  python src/report_card.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import ranker
from train import CHAMPION_FILE, FIRST_MODEL, FIRST_TEST, luck_for

OUT = Path("data/predictions/backtest_probs.csv")
EPS = 1e-4


def grid_rates(train):
    """Podium and win rate by grid slot, from earlier seasons (a fair baseline)."""
    g = train.assign(slot=train["grid"].clip(lower=1, upper=22).fillna(22).astype(int))
    rates = g.groupby("slot").agg(podium=("podium", "mean"), win=("finish_position", lambda s: (s == 1).mean()))
    return rates.reindex(range(1, 23)).ffill().fillna(0.0)


def build():
    df = ranker.add_model_columns(pd.read_csv("data/processed/features.csv"))
    recipe = ranker.DEFAULT_RECIPE
    if CHAMPION_FILE.exists():
        recipe = json.loads(CHAMPION_FILE.read_text()).get("recipe", recipe)
    last = int(df["season"].max())
    models = {s: ranker.fit_recipe(df[df["season"] < s], recipe) for s in range(FIRST_MODEL, last + 1)}
    for s in models:
        models[s]["luck"] = luck_for(s, models, df)

    rows = []
    for season in range(FIRST_TEST, last + 1):
        base = grid_rates(df[df["season"] < season])
        for rnd, race in df[df["season"] == season].groupby("round"):
            pred = ranker.predict(models[season], race)
            slot = pred["grid"].clip(lower=1, upper=22).fillna(22).astype(int)
            rows.append(pd.DataFrame({
                "season": season, "round": int(rnd), "race_name": pred["race_name"],
                "driver": pred["driver"], "constructor": pred["constructor"], "grid": pred["grid"],
                "predicted_position": pred["predicted_position"], "finish_position": pred["finish_position"],
                "podium": pred["podium"].astype(int), "win": (pred["finish_position"] == 1).astype(int),
                "podium_chance": pred["podium_chance"] / 100, "win_chance": pred["win_chance"] / 100,
                "grid_podium_chance": base.loc[slot, "podium"].to_numpy(),
                "grid_win_chance": base.loc[slot, "win"].to_numpy(),
            }))
    out = pd.concat(rows, ignore_index=True)
    out["recipe"] = recipe
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    return out


# ---------- scoring (used by the app too) ----------

def brier(p, y):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def log_loss(p, y):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    y = np.asarray(y)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def skill(p, base, y):
    """1 - Brier(model) / Brier(baseline): above 0 means better than the baseline."""
    b = brier(base, y)
    return 1 - brier(p, y) / b if b else 0.0


def calibration(p, y, bins=10):
    """Per bin of predicted chance: average prediction, how often it happened, how many."""
    d = pd.DataFrame({"p": p, "y": y})
    d["bin"] = np.minimum((d["p"] * bins).astype(int), bins - 1)
    return d.groupby("bin").agg(predicted=("p", "mean"), happened=("y", "mean"), n=("y", "size")).reset_index()


def finish_ranges(probs, coverage=0.8):
    """For each predicted position: the middle `coverage` share of real finishing positions."""
    lo, hi = (1 - coverage) / 2, 1 - (1 - coverage) / 2
    g = probs.groupby("predicted_position")["finish_position"]
    return pd.DataFrame({"low": g.quantile(lo).round(), "median": g.median(), "high": g.quantile(hi).round(),
                         "n": g.size()}).reset_index()


def by_season(probs):
    rows = []
    for season, d in probs.groupby("season"):
        rows.append({"season": int(season), "races": d["round"].nunique(),
                     "brier": brier(d["podium_chance"], d["podium"]),
                     "grid_brier": brier(d["grid_podium_chance"], d["podium"]),
                     "skill": skill(d["podium_chance"], d["grid_podium_chance"], d["podium"]),
                     "log_loss": log_loss(d["podium_chance"], d["podium"]),
                     "win_brier": brier(d["win_chance"], d["win"])})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    probs = build()
    print(f"Saved {len(probs)} driver predictions from {probs[['season', 'round']].drop_duplicates().shape[0]} races")
    print(by_season(probs).round(4).to_string(index=False))
