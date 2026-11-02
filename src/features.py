import pandas as pd
import numpy as np

# Same team, different names over the years -> one name
TEAM_MAP = {
    "force_india": "aston_martin",
    "racing_point": "aston_martin",
    "toro_rosso": "rb",
    "alphatauri": "rb",
    "renault": "alpine",
    "alfa": "sauber",
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
def main():
    df = load_and_clean()
    df = add_driver_features(df)
    df = add_team_features(df)
    df = add_season_features(df)
    df = add_gain_features(df)
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