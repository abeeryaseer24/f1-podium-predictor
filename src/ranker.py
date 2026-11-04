"""The ranking model: predicts the WHOLE finishing order, 1 to 22.

It is a Plackett-Luce model, the classic model for races: every driver gets a strength
score, and the finishing order is "who comes out on top, then who is best of the rest..."
  - strength = a weighted sum of what we know before the race (grid, car pace, form...)
  - every input is compared with the rest of THIS race, so it learns who is better than whom
  - chances come from replaying the race thousands of times with the right amount of luck,
    so win chances add up to 100% and podium chances add up to exactly 3 drivers

It is linear, so every prediction can be explained exactly: each input adds or takes away
a known amount of strength (used by "Why this pick?").
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

TOP = 10                 # it learns from the first 10 finishers (the back of the field is mostly luck)
L2 = 1.0                 # keeps the weights small, so it doesn't over-learn
SIMULATIONS = 5000       # races replayed to turn strengths into chances

FEATURES = [
    "log_grid", "log_quali", "log_team_best_q", "quali_gap_teammate", "grid_x_circuit",
    "driver_form_finish", "team_form_finish", "team_form_quali", "driver_season_avg_finish",
    "constructor_season_podium_rate", "driver_podium_rate", "driver_avg_finish",
    "driver_form_dnf", "driver_dnf_rate", "driver_beats_teammate", "driver_avg_gain",
    "constructor_avg_gain", "driver_circuit_podium_rate", "constructor_circuit_podium_rate",
]

# Plain-words names, for the app
LABELS = {
    "log_grid": "Starting position", "log_quali": "Qualifying position",
    "log_team_best_q": "Car pace this weekend (team's best qualifying)",
    "quali_gap_teammate": "Qualifying vs teammate", "grid_x_circuit": "Grid matters more at this circuit",
    "driver_form_finish": "Driver's last 5 races", "team_form_finish": "Team's last 3 races",
    "team_form_quali": "Team's qualifying, last 3 races", "driver_season_avg_finish": "Driver's season so far",
    "constructor_season_podium_rate": "Team's podiums this season", "driver_podium_rate": "Driver's career podiums",
    "driver_avg_finish": "Driver's career average finish", "driver_form_dnf": "Recent retirements (bad luck, not pace)",
    "driver_dnf_rate": "Career retirements", "driver_beats_teammate": "Usually beats teammate",
    "driver_avg_gain": "Usually gains places in races", "constructor_avg_gain": "Team usually gains places",
    "driver_circuit_podium_rate": "Driver's podiums at this circuit",
    "constructor_circuit_podium_rate": "Team's podiums at this circuit",
}


def add_model_columns(df):
    """The model's inputs that are made from other columns."""
    df = df.copy()
    df["log_grid"] = np.log(df["grid"].clip(lower=1))
    df["log_quali"] = np.log(df["quali_position"].clip(lower=1))
    df["log_team_best_q"] = np.log(df["team_best_quali"].clip(lower=1))
    df["grid_x_circuit"] = df["log_grid"] * df["circuit_grid_importance"].fillna(0.62)
    return df


def race_matrix(d, fill=None, scale=None, features=None):
    """Inputs as numbers, each one compared with the average of its own race."""
    X = d[features or FEATURES].astype(float)
    fill = X.median() if fill is None else pd.Series(fill)
    X = X.fillna(fill)
    X = X - X.groupby([d["season"].to_numpy(), d["round"].to_numpy()]).transform("mean").to_numpy()
    scale = X.std().replace(0, 1) if scale is None else pd.Series(scale)
    return (X / scale).to_numpy(), fill, scale


def fit(train, top=TOP, l2=L2, features=None):
    """Learn the weights from past races (maximum likelihood of the real finishing orders).
    `top`: how many finishers it learns from; `l2`: how strongly the weights are kept small."""
    features = list(features or FEATURES)
    X, fill, scale = race_matrix(train, features=features)
    key = train["season"].astype(str).to_numpy() + "_" + train["round"].astype(str).to_numpy()
    finish = train["finish_position"].to_numpy()
    races = [idx[np.argsort(finish[idx])] for idx in pd.Series(range(len(train))).groupby(key).indices.values()]

    def loss(w):
        s_all, total, grad = X @ w, 0.0, np.zeros_like(w)
        for order in races:
            s, Xo = s_all[order], X[order]
            e = np.exp(s - s.max())
            tail = np.cumsum(e[::-1])[::-1]                 # everyone still to be placed
            tail_x = np.cumsum((e[:, None] * Xo)[::-1], axis=0)[::-1]
            k = min(top, len(order))
            total -= (s[:k] - s.max() - np.log(tail[:k])).sum()
            grad -= (Xo[:k] - tail_x[:k] / tail[:k, None]).sum(axis=0)
        return total + l2 * w @ w, grad + 2 * l2 * w

    w = minimize(loss, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B").x
    return {"weights": dict(zip(features, w.tolist())), "fill": fill.to_dict(), "scale": scale.to_dict(),
            "features": features, "luck": 1.0}


def strengths(model, d):
    features = model.get("features", FEATURES)
    X, _, _ = race_matrix(d, model["fill"], model["scale"], features)
    return X @ np.array([model["weights"][f] for f in features])


def contributions(model, d):
    """How much each input adds to or takes from each driver's strength (vs the race average)."""
    features = model.get("features", FEATURES)
    X, _, _ = race_matrix(d, model["fill"], model["scale"], features)
    return pd.DataFrame(X * np.array([model["weights"][f] for f in features]), columns=features, index=d.index)


def chances(s, luck=1.0, n=SIMULATIONS, seed=0):
    """Replay one race n times: win chance, podium chance and expected finish for every driver."""
    rng = np.random.default_rng(seed)
    g = (s / luck)[None, :] + rng.gumbel(size=(n, len(s)))
    place = (-g).argsort(axis=1).argsort(axis=1)            # 0 = winner
    return (place == 0).mean(axis=0), (place < 3).mean(axis=0), place.mean(axis=0) + 1


def predict(model, race):
    """One race: everyone's predicted position, win chance, podium chance and expected finish."""
    race = race.copy()
    race["strength"] = strengths(model, race)
    win, podium, expected = chances(race["strength"].to_numpy(), model.get("luck", 1.0))
    race["win_chance"] = (win * 100).round(1)
    race["podium_chance"] = (podium * 100).round(1)
    race["expected_position"] = expected.round(1)
    race = race.sort_values("strength", ascending=False).reset_index(drop=True)
    race["predicted_position"] = np.arange(1, len(race) + 1)
    return race


# ---------- the recipes that compete to be the live model (champion vs challengers) ----------

SHORT_TERM = [f for f in FEATURES if f not in (
    "driver_podium_rate", "driver_avg_finish", "driver_dnf_rate", "driver_avg_gain", "constructor_avg_gain",
    "driver_circuit_podium_rate", "constructor_circuit_podium_rate")]

RECIPES = {
    "top10": {"label": "Learns from the first 10 finishers", "top": 10, "l2": 1.0, "features": FEATURES},
    "top5": {"label": "Learns from the first 5 finishers", "top": 5, "l2": 1.0, "features": FEATURES},
    "top15-smooth": {"label": "First 15 finishers, stronger smoothing", "top": 15, "l2": 5.0, "features": FEATURES},
    "short-term": {"label": "Only this weekend and recent form (no career stats)", "top": 10, "l2": 1.0,
                   "features": SHORT_TERM},
}
DEFAULT_RECIPE = "top10"


def fit_recipe(train, name):
    r = RECIPES[name]
    model = fit(train, top=r["top"], l2=r["l2"], features=r["features"])
    model["recipe"] = name
    return model
