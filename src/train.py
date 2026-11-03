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

FEATURES = [
    "grid", "quali_position",
    "driver_podium_rate", "driver_avg_finish", "driver_dnf_rate",
    "driver_races", "driver_circuit_podium_rate",
    "constructor_podium_rate", "constructor_circuit_podium_rate",
    "constructor_season_podium_rate", "driver_season_podium_rate",
    "driver_season_avg_finish", "grid_gap_to_pole", "team_rank_in_race",
    "driver_avg_gain", "constructor_avg_gain",
]


def top3_hits(data, score_col):
    """Per race: take the 3 highest scores, count real podium finishers, average."""
    hits = [race.nlargest(3, score_col)["podium"].sum()
            for _, race in data.groupby(["season", "round"])]
    return np.mean(hits)


def main():
    df = pd.read_csv("data/processed/features.csv")
    train = df[df["season"] <= 2024]
    test = df[df["season"] == 2025].copy()

    # Imputer + model in one pipeline, so the saved file handles blanks itself
    model = make_pipeline(
        SimpleImputer(strategy="mean"),
        RandomForestClassifier(n_estimators=300, max_depth=6,
                               min_samples_leaf=20, random_state=42, n_jobs=-1),
    )
    model.fit(train[FEATURES], train["podium"])

    # Final, one-time test on 2025
    test["score"] = model.predict_proba(test[FEATURES])[:, 1]
    test["grid_score"] = -test["grid"]
    print("2025 test | model top-3 hits:", round(top3_hits(test, "score"), 2))
    print("2025 test | grid baseline:   ", round(top3_hits(test, "grid_score"), 2))
    print("2025 test | ROC-AUC:", round(roc_auc_score(test["podium"], test["score"]), 3))

        # Save the 2025 backtest: the model above never saw any 2025 race
    rows = []
    for (season, rnd), race in test.groupby(["season", "round"]):
        top3 = race.nlargest(3, "score")
        row = {"season": season, "round": rnd, "race_name": race["race_name"].iloc[0]}
        for i, (_, r) in enumerate(top3.iterrows(), start=1):
            row[f"p{i}"] = r["driver"]
            row[f"p{i}_team"] = r["constructor"]
            row[f"p{i}_chance"] = round(r["score"] * 100, 1)
        rows.append(row)
    Path("data/predictions").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv("data/predictions/backtest_2025.csv", index=False)
    print("Backtest saved to data/predictions/backtest_2025.csv")

       # Final model: retrain on every season (2016 to latest) before saving
    model.fit(df[FEATURES], df["podium"])
    # Save the model
    Path("models").mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES}, "models/podium_model.joblib")
    print("Model saved to models/podium_model.joblib")

        # Model card: when it was trained, on what, and how it scored on 2025
    last = df.sort_values(["season", "round"]).iloc[-1]
    info = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trained_on_rows": int(len(df)),
        "last_race": {
            "season": int(last["season"]),
            "round": int(last["round"]),
            "race_name": last["race_name"],
        },
        "features": FEATURES,
        "test_2025": {
            "model_top3_hits": round(float(top3_hits(test, "score")), 2),
            "grid_top3_hits": round(float(top3_hits(test, "grid_score")), 2),
            "roc_auc": round(float(roc_auc_score(test["podium"], test["score"])), 3),
        },
    }
    Path("models/model_info.json").write_text(json.dumps(info, indent=2))
    print("Model info saved to models/model_info.json")

    # Feature importance chart for the README
    rf = model.named_steps["randomforestclassifier"]
    importance = pd.Series(rf.feature_importances_, index=FEATURES).sort_values()
    plt.figure(figsize=(8, 6))
    importance.plot(kind="barh", color="#e10600")
    plt.title("What the model relies on most")
    plt.xlabel("Importance")
    plt.tight_layout()
    Path("reports/figures").mkdir(parents=True, exist_ok=True)
    plt.savefig("reports/figures/feature_importance.png", dpi=150)
    print("Chart saved to reports/figures/feature_importance.png")


if __name__ == "__main__":
    main()