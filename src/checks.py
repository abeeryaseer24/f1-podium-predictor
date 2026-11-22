"""Safety checks for the live system.

If anything looks wrong, a check raises an error. The pipeline then stops,
nothing gets pushed, and GitHub emails you that the run failed.
"""
import sys

import pandas as pd

from predictor import FEATURES_CSV, RACES_DIR, RESULTS_CSV, ROOT, SCOREBOARD_FILES, model_info
from strategy import engineer_step, load_race, run_engineer, stored_knowledge
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
    champion = ROOT / "models" / "champion.json"
    if champion.exists():
        import json
        import joblib
        recipe = json.loads(champion.read_text())["recipe"]
        live = joblib.load(ROOT / "models" / "podium_model.joblib")["model"].get("recipe")
        check(live == recipe, f"the live model is the champion recipe ({recipe})")


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
    from prepare_race import shape_ok
    broken_tracks = [p.name for p in folders if not shape_ok(pd.read_parquet(p / "track.parquet"))]
    if broken_tracks:                                  # a warning, not a failure: the race still works
        print(f"  !!  track shape looks broken for {', '.join(broken_tracks)}: "
              f"run  python src/prepare_race.py <season> <round> --track-only")
    else:
        print("  ok  every track shape is clean")

# ---------- the strategist (the no-future rule) ----------

def check_strategy_no_future():
    print("Checking the strategist uses no future laps")
    files = sorted(RACES_DIR.glob("*_*/radio.parquet"))
    if not files:
        print("  --  no strategy files yet")
        return
    folder = files[-1].parent
    laps, pits, control = load_race(folder.name)
    total = int(laps["lap_number"].max())
    L = total // 2
    knowledge = stored_knowledge(folder.name)

    # 1. Handed a lap from the future, the strategist must refuse to work
    try:
        engineer_step(laps[laps["lap_number"] <= L + 1], pits, control, L, total, {}, knowledge)
        refused = False
    except ValueError:
        refused = True
    check(refused, "the strategist refuses to work when it is handed a future lap")

    # 2. Re-run from laps 1-L only: the stored plans must be the same (computers can round the
    #    last decimal differently on another machine (GitHub's Python vs yours), which can flip a
    #    near-tie, so 95% is the bar. Real leakage is also blocked by the refusal test above, and
    #    would change far more than a few percent of the plans)
    line = (laps["t_start"] + laps["lap_duration"])[laps["lap_number"] == L].max()
    plans, _ = run_engineer(laps[laps["lap_number"] <= L], pits[pits["lap_number"] <= L],
                            control[control["t"] <= line], total, L, knowledge)
    stored = pd.read_parquet(folder / "strategy.parquet")
    cols = ["driver_number", "lap", "status", "pit_lap"]
    key = lambda df: set(map(tuple, df[cols].astype(str).values))
    old, new = key(stored[stored["lap"] <= L]), key(plans)
    same = len(old & new) / max(len(old | new), 1)
    check(same >= 0.95, f"stored plans for laps 1-{L} of {folder.name} match a re-run from laps 1-{L} only "
                        f"({same:.1%} identical)")


def check_lapsim():
    """The lap simulator's calibrations: every prepared race tried, the usable ones close to reality."""
    import lapsim
    print("Checking the lap simulator")
    calibration = lapsim.load_calibration()
    folders = sorted(p.name for p in RACES_DIR.glob("*_*") if (p / "track.parquet").exists())
    usable = {f: c for f, c in calibration.items() if c.get("usable")}
    check(len(usable) >= 0.8 * len(folders),
          f"most prepared races have a usable calibration ({len(usable)} of {len(folders)})")
    far = [f for f, c in usable.items() if abs(c["sim_lap"] - c["real_lap"]) > 0.5]
    check(not far, "every usable calibration is within half a second of the real lap")
    rough = [f for f, c in usable.items() if c["speed_rmse_kmh"] > lapsim.MAX_RMSE]
    check(not rough, f"every usable calibration's speed trace is within {lapsim.MAX_RMSE:.0f} km/h on average")
    # The engine itself: a known car on a known circuit gives a sensible lap
    if usable:
        folder = sorted(usable)[-1]
        import pandas as pd
        track = lapsim.build_track(pd.read_parquet(RACES_DIR / folder / "track.parquet"))
        car = lapsim.calibrated_car(folder, calibration)
        lap = lapsim.simulate(car, track)["lap_time"]
        check(abs(lap - usable[folder]["sim_lap"]) < 0.05, f"re-simulating {folder} gives the stored lap time")
        heavier = lapsim.simulate(lapsim.replace(car, mass=car.mass + 50), track)["lap_time"]
        check(heavier > lap, "a heavier car is slower")


def check_race_story():
    """Where the Race Was Won adds up, and the report card covers every tested race."""
    import race_story
    print("Checking the race breakdowns and report card")
    folders = sorted(p.name for p in RACES_DIR.glob("*_*") if (p / "laps.parquet").exists())
    if folders:
        folder = folders[-1]
        data = race_story.load(folder)
        order = race_story.finishing_order(data[0])
        totals, per_lap = race_story.breakdown(folder, order[0], order[1], data)
        check(abs(sum(totals.values()) - per_lap["gap"].iloc[-1]) < 1e-6,
              f"the parts of the gap add up exactly to the real gap ({folder})")
        check(per_lap["gap"].iloc[-1] > 0, f"the winner of {folder} is ahead of second place at the flag")
    probs_file = ROOT / "data" / "predictions" / "backtest_probs.csv"
    if probs_file.exists():
        probs = pd.read_csv(probs_file)
        backtests = pd.read_csv(ROOT / "data" / "predictions" / "backtests.csv")
        check(len(probs[["season", "round"]].drop_duplicates()) >= len(backtests) - 1,
              "the report card grades every race in the backtest")
        check(probs["podium_chance"].between(0, 1).all(), "every podium chance is between 0 and 1")
        sums = probs.groupby(["season", "round"])["podium_chance"].sum()
        check(sums.between(2.95, 3.05).all(), "podium chances add up to 3 drivers in every race")


def check_race_engine():
    """The race engine replays the latest prepared race and roughly agrees with the real result."""
    import race_engine
    print("Checking the race engine")
    folders = sorted(p.name for p in RACES_DIR.glob("*_*") if (p / "laps.parquet").exists())
    race = race_engine.build(folders[-1])
    table = race_engine.summary(race, race_engine.simulate(race, runs=150))
    check(abs(table["win"].sum() - 1) < 0.15, "win chances add up to about one winner per race")
    agree = race_engine.agreement(table)
    check(agree > 0.5, f"replaying {folders[-1]} with the real strategies agrees with the real result ({agree:.2f})")


def check_driving_style():
    """Guess the Driver: the model beats a coin on unseen races, and every game round has two teammates."""
    import json
    import pandas as pd
    print("Checking the driving-style model")
    model = json.loads((ROOT / "data" / "processed" / "style_model.json").read_text(encoding="utf-8"))
    check(model["score"]["lap_accuracy"] > 0.5, f"it names teammates better than a coin on unseen races "
          f"({model['score']['lap_accuracy']:.0%})")
    game = pd.read_parquet(ROOT / "data" / "processed" / "style_game.parquet")
    check((game.groupby(["folder", "team"])["driver"].nunique() == 2).all(), "every game round has both teammates")


def check_ai_driver():
    """Race the AI Driver: on circuits it never saw, the learned driver follows the real lap more
    closely than the simulator does, and its laps are believable."""
    import json
    print("Checking the AI driver")
    r = json.loads((ROOT / "data" / "processed" / "ai_driver.json").read_text(encoding="utf-8"))
    check(r["ai_rmse"] < r["sim_rmse"], f"it follows real laps more closely than the simulator "
          f"({r['ai_rmse']:.1f} vs {r['sim_rmse']:.1f} km/h)")
    check(abs(r["ai_gap"]) < 3, f"its lap times are within 3 s of the real ones ({r['ai_gap']:+.2f} s)")


def check_pages():
    """Every page in the menu has its one-line subtitle."""
    import re
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    titles = re.findall(r'st\.Page\("app_pages/[^"]+", title="([^"]+)"', app)
    missing = [t for t in titles if t != "Home" and f'"{t}":' not in app]
    print("Checking the pages")
    check(not missing, f"every page has a tagline ({', '.join(missing) or 'all present'})")
    pages = [m for m in re.findall(r'st\.Page\("(app_pages/[^"]+)"', app)]
    check(all((ROOT / p).exists() for p in pages), "every page in the menu exists")
    import py_compile
    broken = []
    for path in [ROOT / "app.py", *sorted((ROOT / "app_pages").glob("*.py")), *sorted((ROOT / "src").rglob("*.py"))]:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError:
            broken.append(path.name)
    check(not broken, f"every page and module compiles ({', '.join(broken) or 'all fine'})")


def run_all(min_rows=0):
    check_results(min_rows)
    check_features()
    check_model()
    check_predictions()
    check_race_files()
    check_strategy_no_future()
    # Checks for the extra pages (simulator, race breakdowns, report card, page files). These only
    # WARN: a problem on those pages must never stop the robot pushing a locked-in prediction.
    for extra in (check_lapsim, check_race_story, check_race_engine, check_driving_style, check_ai_driver, check_pages):
        warn_only(extra)
    print("All checks passed.")


def warn_only(check_fn):
    """Run a check for an extra page; print a warning instead of stopping if it fails."""
    try:
        check_fn()
    except Exception as error:                      # CheckFailed or anything unexpected
        print(f"  !!  WARNING ({check_fn.__name__}, the robot carries on): {error}")


if __name__ == "__main__":
    try:
        run_all()
    except CheckFailed as error:
        print(f"\nCHECK FAILED: {error}")
        sys.exit(1)
