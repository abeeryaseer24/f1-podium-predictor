import argparse

import joblib
import pandas as pd


def predict_race(season, rnd):
    """Return every driver in one race, sorted by predicted podium chance."""
    bundle = joblib.load("models/podium_model.joblib")
    model, features = bundle["model"], bundle["features"]

    df = pd.read_csv("data/processed/features.csv")
    race = df[(df["season"] == season) & (df["round"] == rnd)].copy()
    if race.empty:
        raise SystemExit(f"No race found for season {season}, round {rnd}")

    race["podium_chance_%"] = (model.predict_proba(race[features])[:, 1] * 100).round(1)
    return race.sort_values("podium_chance_%", ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Predict the podium for one F1 race")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()

    race = predict_race(args.season, args.round)
    print(f"\n{race['race_name'].iloc[0]} {args.season}\n")
    print(race[["driver", "constructor", "grid", "podium_chance_%"]]
          .head(10).to_string(index=False))

    predicted = race.head(3)["driver"].tolist()
    actual = race.sort_values("finish_position").head(3)["driver"].tolist()
    correct = len(set(predicted) & set(actual))

    print("\nPredicted podium:", ", ".join(predicted))
    print("Actual podium:   ", ", ".join(actual))
    print(f"Correct: {correct} of 3")


if __name__ == "__main__":
    main()