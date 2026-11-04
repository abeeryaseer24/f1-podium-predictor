"""Safety checks for the live system.

If anything looks wrong, a check raises an error. The pipeline then stops,
nothing gets pushed, and GitHub emails you that the run failed.
"""
import sys

import pandas as pd

from predictor import FEATURES_CSV, RACES_DIR, RESULTS_CSV, SCOREBOARD_FILES, model_info
from strategy import calls_for_lap
FIRST_SEASON = 2016


class CheckFailed(Exception):
    pass


def check(condition, message):
    """Stop with an error if the condition is false; print 'ok' if it's true."""
    if not condition:
        raise CheckFailed(message)
    print(f"  ok  {message}")


# ---------- the data ----------

def check_results(min_rows=0):
    df = pd.read_csv(RESULTS_CSV)
    print("Checking results.csv")

    needed = {"season", "round", "driver", "constructor", "grid", "finish_position", "status"}
    check(needed.issubset(df.columns), "all needed columns are present")
    check(len(df) >= min_rows, f"no rows were lost ({len(df)} rows now, {min_rows} before)")
    check(not df.duplicated(["season", "round", "driver"]).any(),
          "no driver appears twice in one race")
    check(df[["season", "round", "driver", "finish_position"]].notna().all().all(),
          "no missing seasons, rounds, drivers or finishing positions")

    seasons = sorted(df["season"].unique())
    check(seasons == list(range(FIRST_SEASON, seasons[-1] + 1)), "no season is missing")

    gaps = [s for s, g in df.groupby("season")
            if sorted(g["round"].unique()) != list(range(1, g["round"].max() + 1))]
    check(not gaps, "no round is missing inside a season")

    sizes = df.groupby(["season", "round"]).size()
    check(sizes.between(18, 24).all(), "every race has between 18 and 24 drivers")

    podiums = (df[df["finish_position"] <= 3]
               .groupby(["season", "round"])["finish_position"]
               .apply(lambda s: sorted(s.tolist()) == [1, 2, 3]))
    check(len(podiums) == len(sizes) and podiums.all(),
          "every race has exactly one P1, P2 and P3")


def check_features():
    df = pd.read_csv(FEATURES_CSV)
    results = pd.read_csv(RESULTS_CSV)
    print("Checking features.csv")
    check(len(df) == len(results), "features.csv has one row per race result")
    check(df["grid"].notna().all() and df["quali_position"].notna().all(),
          "grid and qualifying positions are filled in")
    check((df.groupby(["season", "round"])["podium"].sum() == 3).all(),
          "every race has exactly 3 podium finishers")


# ---------- the model ----------

def check_model():
    info = model_info()
    print("Checking the model")
    check(info is not None, "model_info.json exists")
    test = info["test_2025"]
    check(test["model_top3_hits"] >= 2.0,
          f"2025 test score is healthy ({test['model_top3_hits']} of 3 per race)")
    check(test["roc_auc"] >= 0.85, f"ROC-AUC is healthy ({test['roc_auc']})")


# ---------- the locked predictions (fairness) ----------

def snapshot_log():
    """The locked predictions as they are right now (empty if none yet)."""
    file = SCOREBOARD_FILES["live"]
    return pd.read_csv(file) if file.exists() else pd.DataFrame()


def check_predictions():
    print("Checking the locked predictions")
    log = snapshot_log()
    if log.empty:
        print("  --  no locked predictions yet")
        return
    check(not log.duplicated(["season", "round"]).any(), "each race was locked in only once")
    saved = pd.to_datetime(log["predicted_at"], utc=True)
    start = pd.to_datetime(log["race_start"], utc=True)
    check((saved < start).all(), "every prediction was saved before its race started")


def check_log_unchanged(before):
    """Old locked predictions must be exactly as they were before this run."""
    print("Checking that earlier predictions were not changed")
    if before.empty:
        print("  --  nothing to compare yet")
        return
    after = snapshot_log()
    old_part = after.head(len(before)).astype(str).reset_index(drop=True)
    check(len(after) >= len(before)
          and old_part.equals(before.astype(str).reset_index(drop=True)),
          "earlier locked predictions are exactly as they were")

# ---------- the prepared race files ----------

def check_race_files():
    print("Checking the prepared race files")
    folders = [p for p in RACES_DIR.glob("*_*") if (p / "info.json").exists()]
    if not folders:
        print("  --  no race files yet")
        return
    needed = ["track.parquet", "positions.parquet", "laps.parquet",
              "pits.parquet", "race_control.parquet", "weather.parquet"]
    broken = [p.name for p in folders if not all((p / f).exists() for f in needed)]
    check(not broken, f"every prepared race has all its files ({len(folders)} races)")
    few_cars = [p.name for p in folders
                if pd.read_parquet(p / "positions.parquet", columns=["driver_number"])
                ["driver_number"].nunique() < 15]
    check(not few_cars, "every prepared race has positions for at least 15 cars")
    too_big = [p.name for p in folders if sum(f.stat().st_size for f in p.iterdir()) > 15e6]
    check(not too_big, "every race folder is under 15 MB")

# ---------- the strategist (the no-future rule) ----------

def check_strategy_no_future():
    print("Checking the strategist uses no future laps")
    files = sorted(RACES_DIR.glob("*_*/strategy.parquet"))
    if not files:
        print("  --  no strategy files yet")
        return
    folder = files[0].parent
    laps = pd.read_parquet(folder / "laps.parquet")
    total = int(laps["lap_number"].max())
    L = total // 2
    fresh = calls_for_lap(laps[laps["lap_number"] <= L], L, total)
    stored = pd.read_parquet(files[0])
    stored = stored[stored["lap"] == L]
    cols = ["driver_number", "plan", "exp_position", "call"]
    tidy = lambda df: df[cols].sort_values(cols[:2]).reset_index(drop=True)
    check(tidy(stored).equals(tidy(fresh)),
          f"stored calls for lap {L} of {folder.name} match a recomputation from laps 1-{L} only")




def run_all(min_rows=0):
    check_results(min_rows)
    check_features()
    check_model()
    check_predictions()
    check_race_files()
    check_strategy_no_future()
    print("All checks passed.")


if __name__ == "__main__":
    try:
        run_all()
    except CheckFailed as error:
        print(f"\nCHECK FAILED: {error}")
        sys.exit(1)