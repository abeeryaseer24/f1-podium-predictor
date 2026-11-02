import argparse

from predictor import predict_upcoming


def main():
    parser = argparse.ArgumentParser(description="Predict the podium for an upcoming F1 race")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()

    result = predict_upcoming(args.season, args.round)
    mode = ("real qualifying results" if result["real_quali"]
            else "ESTIMATED grid (qualifying hasn't happened yet)")
    print(f"\n{result['race_name']} {args.season}  (using {mode})\n")
    print(result["table"][["name", "constructor", "grid", "podium_chance"]]
          .head(10).to_string(index=False))
    print("\nPredicted podium:", ", ".join(result["predicted"]))


if __name__ == "__main__":
    main()