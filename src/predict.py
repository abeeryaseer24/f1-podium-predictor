import argparse

from predictor import predict_past


def main():
    parser = argparse.ArgumentParser(description="Predict the podium for a past F1 race")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()

    result = predict_past(args.season, args.round)
    print(f"\n{result['race_name']} {args.season}\n")
    print(result["table"][["name", "constructor", "grid", "podium_chance"]]
          .head(10).to_string(index=False))
    print("\nPredicted podium:", ", ".join(result["predicted"]))
    print("Actual podium:   ", ", ".join(result["actual"]))
    print(f"Correct: {result['correct']} of 3")


if __name__ == "__main__":
    main()