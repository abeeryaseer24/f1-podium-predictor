"""Train the ranking model (the whole finishing order) and test it honestly.

The test: for every season from 2022 on, a model trained ONLY on the seasons before it
predicts that season. It is compared with two baselines:
  - the grid (finishing order = starting order), a very strong baseline in F1
  - the old podium model (a Random Forest that only answered "podium or not")
Then the final model is trained on every race and saved.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline

import ranker

FIRST_TEST = 2022                 # backtests from this season on
FIRST_MODEL = 2019                # the first season a model is trained for (needs 3 seasons of history)
OLD_FEATURES = [
    "grid", "quali_position",
    "driver_podium_rate", "driver_avg_finish", "driver_dnf_rate",
    "driver_races", "driver_circuit_podium_rate",
    "constructor_podium_rate", "constructor_circuit_podium_rate",
    "constructor_season_podium_rate", "driver_season_podium_rate",
    "driver_season_avg_finish", "grid_gap_to_pole", "team_rank_in_race",
    "driver_avg_gain", "constructor_avg_gain",
]


def race_scores(race, order):
    """How good one predicted order was: podium drivers, winner, whole order."""
    finish = race.set_index("driver")["finish_position"]
    actual = finish.loc[order].to_numpy()
    predicted = np.arange(1, len(order) + 1)
    return {"podium_hits": int((actual[:3] <= 3).sum()), "winner_right": bool(actual[0] == 1),
            "order_match": float(pd.Series(predicted).corr(pd.Series(actual), method="spearman")),
            "places_off": float(np.mean(np.abs(predicted - actual)))}


def luck_for(season, models, df):
    """The amount of luck for a season's chances, chosen on the 3 seasons before it
    (each predicted by a model that never saw it)."""
    earlier = [s for s in range(season - 3, season) if s in models and (df["season"] == s).any()]
    if not earlier:
        return 1.0
    options = [0.5, 0.6, 0.7, 0.8, 1.0, 1.2]
    errors = []
    for luck in options:
        err = []
        for s in earlier:
            for _, race in df[df["season"] == s].groupby("round"):
                _, podium, _ = ranker.chances(ranker.strengths(models[s], race), luck, n=2000)
                err.append(np.mean((podium - race["podium"].to_numpy()) ** 2))
        errors.append(np.mean(err))
    return options[int(np.argmin(errors))]


def main():
    df = ranker.add_model_columns(pd.read_csv("data/processed/features.csv"))
    last_season = int(df["season"].max())

    # One model per season, each trained only on the seasons before it
    models = {}
    for season in range(FIRST_MODEL, last_season + 2):
        models[season] = ranker.fit(df[df["season"] < season])
    for season in models:
        models[season]["luck"] = luck_for(season, models, df)

    # The backtest: every season from 2022, predicted by a model that never saw it
    races, summary = [], {}
    for season in range(FIRST_TEST, last_season + 1):
        test = df[df["season"] == season]
        old = make_pipeline(SimpleImputer(strategy="mean"),
                            RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=20,
                                                   random_state=42, n_jobs=-1))
        old.fit(df.loc[df["season"] < season, OLD_FEATURES], df.loc[df["season"] < season, "podium"])
        probs, labels = [], []
        for rnd, race in test.groupby("round"):
            pred = ranker.predict(models[season], race)
            order = pred["driver"].tolist()
            grid_order = race.sort_values("grid")["driver"].tolist()
            old_order = race.assign(p=old.predict_proba(race[OLD_FEATURES])[:, 1]).sort_values(
                "p", ascending=False)["driver"].tolist()
            m, g, o = race_scores(race, order), race_scores(race, grid_order), race_scores(race, old_order)
            row = {"season": season, "round": int(rnd), "race_name": race["race_name"].iloc[0], **m,
                   "grid_podium_hits": g["podium_hits"], "grid_winner_right": g["winner_right"],
                   "grid_order_match": g["order_match"], "grid_places_off": g["places_off"],
                   "old_podium_hits": o["podium_hits"], "order": json.dumps(order)}
            for i, r in pred.head(3).iterrows():
                row[f"p{i + 1}"], row[f"p{i + 1}_team"] = r["driver"], r["constructor"]
                row[f"p{i + 1}_chance"] = r["podium_chance"]
            races.append(row)
            probs += (pred["podium_chance"] / 100).tolist()
            labels += pred["podium"].tolist()
        season_rows = pd.DataFrame([r for r in races if r["season"] == season])
        summary[str(season)] = {
            "races": len(season_rows),
            "podium_hits": round(season_rows["podium_hits"].mean(), 2),
            "grid_podium_hits": round(season_rows["grid_podium_hits"].mean(), 2),
            "old_model_podium_hits": round(season_rows["old_podium_hits"].mean(), 2),
            "winner_right": round(season_rows["winner_right"].mean(), 3),
            "grid_winner_right": round(season_rows["grid_winner_right"].mean(), 3),
            "order_match": round(season_rows["order_match"].mean(), 3),
            "grid_order_match": round(season_rows["grid_order_match"].mean(), 3),
            "places_off": round(season_rows["places_off"].mean(), 2),
            "grid_places_off": round(season_rows["grid_places_off"].mean(), 2),
            "podium_auc": round(float(roc_auc_score(labels, probs)), 3),
        }
    table = pd.DataFrame(races)
    Path("data/predictions").mkdir(parents=True, exist_ok=True)
    table.to_csv("data/predictions/backtests.csv", index=False)
    cols = ["season", "round", "race_name", "p1", "p1_team", "p1_chance", "p2", "p2_team", "p2_chance",
            "p3", "p3_team", "p3_chance", "order"]
    table.loc[table["season"] == 2025, cols].to_csv("data/predictions/backtest_2025.csv", index=False)

    print("Backtest: each season predicted by a model trained only on the seasons before it")
    print(f"{'season':>6}  {'podium (model / grid / old)':>28}  {'winner (model / grid)':>22}  "
          f"{'order match (model / grid)':>27}  {'places off (model / grid)':>26}")
    for season, s in summary.items():
        print(f"{season:>6}  {s['podium_hits']:>12} / {s['grid_podium_hits']} / {s['old_model_podium_hits']:<5}"
              f"  {s['winner_right']:>12.0%} / {s['grid_winner_right']:.0%}  "
              f"{s['order_match']:>15} / {s['grid_order_match']:<7}  {s['places_off']:>14} / {s['grid_places_off']}")
    avg = {k: round(float(np.mean([s[k] for s in summary.values()])), 3)
           for k in ("podium_hits", "grid_podium_hits", "old_model_podium_hits", "winner_right",
                     "grid_winner_right", "order_match", "grid_order_match", "places_off", "grid_places_off")}
    print(f"   avg  {avg['podium_hits']:>12} / {avg['grid_podium_hits']} / {avg['old_model_podium_hits']}")

    # The final model: trained on every race, ready for the next one
    final = models[last_season + 1]
    Path("models").mkdir(exist_ok=True)
    joblib.dump({"kind": "plackett_luce", "model": final, "features": ranker.FEATURES},
                "models/podium_model.joblib")
    print(f"Model saved to models/podium_model.joblib (luck setting {final['luck']})")

    last = df.sort_values(["season", "round"]).iloc[-1]
    s25 = summary.get("2025", {})
    info = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trained_on_rows": int(len(df)),
        "model": "Plackett-Luce ranking model: predicts the whole finishing order",
        "last_race": {"season": int(last["season"]), "round": int(last["round"]),
                      "race_name": last["race_name"]},
        "features": ranker.FEATURES,
        "test_2025": {"model_top3_hits": s25.get("podium_hits"), "grid_top3_hits": s25.get("grid_podium_hits"),
                      "roc_auc": s25.get("podium_auc")},
        "backtests": summary,
        "backtest_average": avg,
    }
    Path("models/model_info.json").write_text(json.dumps(info, indent=2))
    print("Model info saved to models/model_info.json")

    # What the model relies on: the weight of every input
    weights = pd.Series(final["weights"]).rename(index=ranker.LABELS).sort_values()
    plt.figure(figsize=(9, 7))
    weights.plot(kind="barh", color=["#e10600" if w > 0 else "#4781d7" for w in weights])
    plt.title("Weight of each input (red: a higher value moves a driver up the order)")
    plt.xlabel("Weight (per typical difference between drivers in one race)")
    plt.tight_layout()
    Path("reports/figures").mkdir(parents=True, exist_ok=True)
    plt.savefig("reports/figures/feature_importance.png", dpi=150)
    print("Chart saved to reports/figures/feature_importance.png")


if __name__ == "__main__":
    main()
