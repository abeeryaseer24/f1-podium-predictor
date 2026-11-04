import pandas as pd
import numpy as np

# Same team, different names over the years -> one name
TEAM_MAP = {
    "force_india": "aston_martin",
    "racing_point": "aston_martin",
    "toro_rosso": "rb",
    "alphatauri": "rb",
    "renault": "alpine",
    "alfa": "audi",
    "sauber": "audi",
}


def load_and_clean():
    df = pd.read_csv("data/processed/results.csv")
    df = df.sort_values(["season", "round"]).reset_index(drop=True)

    df["constructor"] = df["constructor"].replace(TEAM_MAP)
    df["podium"] = (df["finish_position"] <= 3).astype(int)

    # DNF = anything that isn't "Finished", "+1 Lap", "+2 Laps" or "Lapped"
    finished = (
        df["status"].eq("Finished")
        | df["status"].str.startswith("+")
        | df["status"].eq("Lapped")
    )
    df["dnf"] = (~finished).astype(int)
    # grid 0 = pit lane start, treat as the back of the grid
    df["grid"] = df["grid"].replace(0, 20)
    # the 11 missing qualifying values: fall back to the grid slot
    df["quali_position"] = df["quali_position"].fillna(df["grid"])
    return df
def past_mean(df, keys, col):
    """Average of `col` over each group's EARLIER races only.
    shift(1) pushes everything down one row, so a race never sees itself."""
    return df.groupby(keys)[col].transform(
        lambda s: s.shift(1).expanding().mean()
    )


def add_driver_features(df):
    df["driver_podium_rate"] = past_mean(df, ["driver"], "podium")
    df["driver_avg_finish"] = past_mean(df, ["driver"], "finish_position")
    df["driver_dnf_rate"] = past_mean(df, ["driver"], "dnf")
    df["driver_races"] = df.groupby("driver").cumcount()
    df["driver_circuit_podium_rate"] = past_mean(df, ["driver", "circuit"], "podium")
    return df
def add_team_features(df):
    sets = [
        ("constructor_podium_rate", ["constructor"]),
        ("constructor_circuit_podium_rate", ["constructor", "circuit"]),
    ]
    for name, keys in sets:
        # one row per team per race
        race = df.groupby(keys + ["season", "round"], as_index=False).agg(
            podiums=("podium", "sum"), entries=("podium", "count")
        ).sort_values(["season", "round"])

        # running total minus the current race = earlier races only
        prev_pod = race.groupby(keys)["podiums"].cumsum() - race["podiums"]
        prev_ent = race.groupby(keys)["entries"].cumsum() - race["entries"]
        race[name] = prev_pod / prev_ent.replace(0, np.nan)

        df = df.merge(race[keys + ["season", "round", name]],
                      on=keys + ["season", "round"], how="left")
    return df
def add_season_features(df):
    # Team: podiums per entry in EARLIER races of the same season
    race = df.groupby(["constructor", "season", "round"], as_index=False).agg(
        podiums=("podium", "sum"), entries=("podium", "count")
    ).sort_values(["season", "round"])
    g = race.groupby(["constructor", "season"])
    prev_pod = g["podiums"].cumsum() - race["podiums"]
    prev_ent = g["entries"].cumsum() - race["entries"]
    race["constructor_season_podium_rate"] = prev_pod / prev_ent.replace(0, np.nan)
    df = df.merge(
        race[["constructor", "season", "round", "constructor_season_podium_rate"]],
        on=["constructor", "season", "round"], how="left")

    # Driver: season-to-date podium rate and average finish (earlier races only)
    df["driver_season_podium_rate"] = df.groupby(["driver", "season"])["podium"].transform(
        lambda s: s.shift(1).expanding().mean())
    df["driver_season_avg_finish"] = df.groupby(["driver", "season"])["finish_position"].transform(
        lambda s: s.shift(1).expanding().mean())

    # Compare each driver with the rest of the SAME race
    df["grid_gap_to_pole"] = df["grid"] - df.groupby(["season", "round"])["grid"].transform("min")
    df["team_rank_in_race"] = df.groupby(["season", "round"])["constructor_season_podium_rate"].rank(ascending=False)
    return df

def add_gain_features(df):
    # positive = moved up from the grid, negative = lost places
    df["gain"] = df["grid"] - df["finish_position"]

    # Driver: average gain over EARLIER races
    df["driver_avg_gain"] = past_mean(df, ["driver"], "gain")

    # Team: same idea, totalled per race first so teammates don't leak
    race = df.groupby(["constructor", "season", "round"], as_index=False).agg(
        gain_sum=("gain", "sum"), entries=("gain", "count")
    ).sort_values(["season", "round"])
    g = race.groupby("constructor")
    prev_sum = g["gain_sum"].cumsum() - race["gain_sum"]
    prev_ent = g["entries"].cumsum() - race["entries"]
    race["constructor_avg_gain"] = prev_sum / prev_ent.replace(0, np.nan)

    df = df.merge(
        race[["constructor", "season", "round", "constructor_avg_gain"]],
        on=["constructor", "season", "round"], how="left")
    return df
# ---------- Step 9: recent form, this weekend's car, teammates, circuit type ----------

def rolling_past(df, keys, col, window):
    """Average of `col` over each group's last `window` EARLIER races (never the race itself)."""
    return df.groupby(keys)[col].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())


def add_form_features(df):
    """Recent form: the last few races say more about this year's car than a whole season."""
    df["driver_form_finish"] = rolling_past(df, ["driver"], "finish_position", 5)
    df["driver_form_quali"] = rolling_past(df, ["driver"], "quali_position", 5)
    df["driver_form_dnf"] = rolling_past(df, ["driver"], "dnf", 10)

    # Team: both cars together, per race first, then the last 3 races
    race = (df.groupby(["constructor", "season", "round"], as_index=False)
              .agg(team_finish=("finish_position", "mean"), team_quali=("quali_position", "mean"))
              .sort_values(["season", "round"]))
    for col, name in (("team_finish", "team_form_finish"), ("team_quali", "team_form_quali")):
        race[name] = race.groupby("constructor")[col].transform(
            lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    return df.merge(race[["constructor", "season", "round", "team_form_finish", "team_form_quali"]],
                    on=["constructor", "season", "round"], how="left")


def add_weekend_features(df):
    """This weekend's qualifying, known before the race: how fast is the car right now?"""
    g = df.groupby(["season", "round", "constructor"])["quali_position"]
    df["team_best_quali"] = g.transform("min")
    team_sum, team_n = g.transform("sum"), g.transform("count")
    df["teammate_quali"] = ((team_sum - df["quali_position"]) / (team_n - 1)).where(team_n > 1)
    df["quali_gap_teammate"] = df["quali_position"] - df["teammate_quali"]
    df["field_size"] = df.groupby(["season", "round"])["driver"].transform("count")
    return df


def add_teammate_features(df):
    """How the driver usually does against their teammate (earlier races only)."""
    race = df.groupby(["season", "round", "constructor"])
    beat = (df["finish_position"] < (race["finish_position"].transform("sum") - df["finish_position"])
            / (race["finish_position"].transform("count") - 1))
    df["_beat_mate"] = beat.where(race["finish_position"].transform("count") > 1).astype(float)
    df["driver_beats_teammate"] = rolling_past(df, ["driver"], "_beat_mate", 10)
    df["driver_quali_gap_form"] = rolling_past(df, ["driver"], "quali_gap_teammate", 5)
    return df.drop(columns="_beat_mate")


def add_circuit_features(df):
    """Circuit type: how much the grid decides the result here (Monaco high, Spa lower),
    from earlier races at this circuit."""
    race = (df.groupby(["circuit", "season", "round"])
              .apply(lambda r: pd.Series({
                  "grid_finish_corr": r["grid"].corr(r["finish_position"], method="spearman"),
                  "places_changed": (r["grid"] - r["finish_position"]).abs().mean()}),
                  include_groups=False)
              .reset_index().sort_values(["season", "round"]))
    for col, name in (("grid_finish_corr", "circuit_grid_importance"),
                      ("places_changed", "circuit_places_changed")):
        race[name] = race.groupby("circuit")[col].transform(lambda s: s.shift(1).expanding().mean())
    return df.merge(race[["circuit", "season", "round", "circuit_grid_importance", "circuit_places_changed"]],
                    on=["circuit", "season", "round"], how="left")


def add_step9_features(df):
    df = add_weekend_features(df)
    df = add_form_features(df)
    df = add_teammate_features(df)
    df = add_circuit_features(df)
    return df


def main():
    df = load_and_clean()
    df = add_driver_features(df)
    df = add_team_features(df)
    df = add_season_features(df)
    df = add_gain_features(df)
    df = add_step9_features(df)
    df.to_csv("data/processed/features.csv", index=False)

    cols = ["grid", "quali_position", "driver_podium_rate", "driver_avg_finish",
            "driver_dnf_rate", "driver_races", "driver_circuit_podium_rate",
            "constructor_podium_rate", "constructor_circuit_podium_rate",
            "constructor_season_podium_rate", "driver_season_podium_rate",
            "driver_season_avg_finish", "grid_gap_to_pole", "team_rank_in_race", "team_rank_in_race", "driver_avg_gain", "constructor_avg_gain"]
    print("Saved:", df.shape)
    print("DNF rate:", round(df["dnf"].mean() * 100, 1), "%")
    print(df[cols].isna().sum())


if __name__ == "__main__":
    main()