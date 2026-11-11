"""The F1 archive: everything from 1950, read from the files src/history_loader.py writes.

Nothing here calls the internet. If the history files have not been downloaded yet, every
function returns an empty table and the pages say so rather than breaking.

Test from the terminal:
  python src/archive.py
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS_FILE = PROCESSED / "history_results.csv"
DRIVERS_FILE = PROCESSED / "history_drivers.csv"
TEAMS_FILE = PROCESSED / "history_teams.csv"
RACES_FILE = PROCESSED / "history_races.csv"

ACTIVE_WITHIN = 2        # a driver counts as active if they raced in the last two seasons
FASTEST_LAP_FROM = 2004  # the API only records fastest laps from this season on


def available():
    """True once the history has been downloaded."""
    return RESULTS_FILE.exists() and DRIVERS_FILE.exists()


@lru_cache(maxsize=8)
def _cached(path_text, modified_time):
    return pd.read_csv(path_text)


def _load(path):
    if not path.exists():
        return pd.DataFrame()
    return _cached(str(path), path.stat().st_mtime).copy()


def results():
    """Every race result since 1950, with finished / podium / win / pole worked out."""
    df = _load(RESULTS_FILE)
    if df.empty:
        return df
    status = df["status"].fillna("")
    df["finished"] = (status.eq("Finished") | status.str.startswith("+")
                      | status.eq("Lapped")).astype(int)
    df["win"] = (df["finish_position"] == 1).astype(int)
    df["podium"] = (df["finish_position"] <= 3).astype(int)
    df["pole"] = (df["grid"] == 1).astype(int)
    df["fastest_lap"] = (df["fastest_lap_rank"] == 1).astype(int)
    df["decade"] = (df["season"] // 10 * 10).astype(int)
    return df


def driver_standings():
    """The official final table for every season. Drivers who scored no points have no
    championship position in the records, which arrives as 0 or blank: those rows are
    kept, but `ranked()` is what to use when the order matters."""
    return _load(DRIVERS_FILE)


def team_standings():
    return _load(TEAMS_FILE)


def ranked(standings):
    """Only the rows that actually have a championship position."""
    if standings.empty:
        return standings
    places = pd.to_numeric(standings["position"], errors="coerce")
    return standings[places.notna() & (places > 0)]


def race_list():
    return _load(RACES_FILE)


def seasons():
    df = _load(RESULTS_FILE)
    return sorted(df["season"].unique().tolist()) if not df.empty else []


def latest_season():
    all_seasons = seasons()
    return all_seasons[-1] if all_seasons else None


# ---------- champions ----------

def champions():
    """One row per season: who won the drivers' title and who won the constructors'."""
    drivers, teams = driver_standings(), team_standings()
    if drivers.empty:
        return pd.DataFrame()
    best_driver = drivers[drivers["position"] == 1].set_index("season")
    best_team = teams[teams["position"] == 1].set_index("season") if not teams.empty \
        else pd.DataFrame()
    rows = []
    for season in sorted(drivers["season"].unique()):
        d = best_driver.loc[season] if season in best_driver.index else None
        t = best_team.loc[season] if (not best_team.empty and season in best_team.index) else None
        rows.append({
            "season": int(season),
            "driver": d["driver"] if d is not None else "",
            "driver_name": d["driver_name"] if d is not None else "",
            "driver_team": d["constructor_name"] if d is not None else "",
            "driver_points": float(d["points"]) if d is not None else 0.0,
            "driver_wins": int(d["wins"]) if d is not None else 0,
            "team": t["constructor"] if t is not None else "",
            "team_name": t["constructor_name"] if t is not None else "",
            "team_points": float(t["points"]) if t is not None else 0.0,
        })
    return pd.DataFrame(rows)


def title_counts(kind="driver"):
    """How many championships each driver, or each constructor, has won."""
    table = champions()
    if table.empty:
        return pd.DataFrame()
    if kind == "driver":
        counted = table[table["driver_name"] != ""]
        out = (counted.groupby(["driver", "driver_name"], as_index=False)
               .agg(titles=("season", "size"),
                    years=("season", lambda s: ", ".join(str(int(y)) for y in sorted(s)))))
        return out.sort_values("titles", ascending=False).reset_index(drop=True)
    counted = table[table["team_name"] != ""]
    out = (counted.groupby(["team", "team_name"], as_index=False)
           .agg(titles=("season", "size"),
                years=("season", lambda s: ", ".join(str(int(y)) for y in sorted(s)))))
    return out.sort_values("titles", ascending=False).reset_index(drop=True)


# ---------- eras ----------

# The same team written two ways in the records. "Lotus F1" is deliberately not here:
# that is the 2012-2015 team that bought the name, not Colin Chapman's Lotus.
CHASSIS_ALIASES = {"Team Lotus": "Lotus"}


def chassis_name(name):
    """Until the 1980s the records name a car by chassis and engine, so Colin Chapman's
    Lotus shows up as Lotus-Climax, Lotus-BRM and Lotus-Ford. For the era charts we keep
    the chassis, which is the team, and drop the engine."""
    chassis = str(name).split("-")[0].strip()
    return CHASSIS_ALIASES.get(chassis, chassis)


def notable_teams(top=12, per_decade=3):
    """The teams worth naming on a chart: the biggest winners of all time, plus the top
    few of every decade, so the 1950s do not collapse into one grey block."""
    df = results()
    if df.empty:
        return set()
    wins = df[df["win"] == 1].copy()
    wins["chassis"] = wins["constructor_name"].map(chassis_name)
    names = set(wins.groupby("chassis").size().nlargest(top).index)
    for _, group in wins.groupby("decade"):
        names |= set(group.groupby("chassis").size().nlargest(per_decade).index)
    return names


def wins_by_decade(top=12):
    """Race wins per constructor per decade."""
    df = results()
    if df.empty:
        return df
    wins = df[df["win"] == 1].copy()
    wins["chassis"] = wins["constructor_name"].map(chassis_name)
    best = notable_teams(top)
    table = (wins.groupby(["decade", "chassis"], as_index=False).size()
             .rename(columns={"size": "wins"}))
    table["team"] = table["chassis"].where(table["chassis"].isin(best), "Everyone else")
    return (table.groupby(["decade", "team"], as_index=False)["wins"].sum()
            .sort_values(["decade", "wins"], ascending=[True, False]))


def wins_by_season(top=12):
    """Race wins per constructor per season, using the same teams as the decade chart."""
    df = results()
    if df.empty:
        return df
    wins = df[df["win"] == 1].copy()
    wins["chassis"] = wins["constructor_name"].map(chassis_name)
    best = notable_teams(top)
    table = (wins.groupby(["season", "chassis"], as_index=False).size()
             .rename(columns={"size": "wins"}))
    table["team"] = table["chassis"].where(table["chassis"].isin(best), "Everyone else")
    return table.groupby(["season", "team"], as_index=False)["wins"].sum()


def season_shape():
    """One row per season: how many races, how many different winners, how many teams."""
    df = results()
    if df.empty:
        return df
    return (df.groupby("season")
            .agg(races=("round", "nunique"),
                 winners=("driver", lambda s: df.loc[s.index][df.loc[s.index, "win"] == 1]["driver"].nunique()),
                 teams=("constructor", "nunique"),
                 entries=("driver", "size"))
            .reset_index())


# ---------- records ----------

METRICS = {
    "wins": ("Race wins", "win"),
    "podiums": ("Podiums", "podium"),
    "poles": ("Pole positions", "pole"),
    "fastest_laps": ("Fastest laps", "fastest_lap"),
    "starts": ("Race starts", None),
    "points": ("Career points", "points"),
}


def driver_records(metric="wins", active_only=False, top=25):
    """A leaderboard of drivers for one measure."""
    df = results()
    if df.empty:
        return df
    if metric == "fastest_laps":
        df = df[df["season"] >= FASTEST_LAP_FROM]
    label, column = METRICS[metric]
    grouped = df.groupby(["driver", "driver_name"])
    value = grouped.size() if column is None else grouped[column].sum()
    table = pd.DataFrame({"value": value}).reset_index()
    span = (df.groupby("driver")
            .agg(first_season=("season", "min"), last_season=("season", "max"),
                 starts=("season", "size")).reset_index())
    table = table.merge(span, on="driver")
    if active_only:
        newest = df["season"].max()
        table = table[table["last_season"] >= newest - ACTIVE_WITHIN + 1]
    table = table.sort_values("value", ascending=False).head(top).reset_index(drop=True)
    table["label"] = label
    return table


def team_records(metric="wins", active_only=False, top=25):
    """The same leaderboard for constructors."""
    df = results()
    if df.empty:
        return df
    if metric == "fastest_laps":
        df = df[df["season"] >= FASTEST_LAP_FROM]
    label, column = METRICS[metric]
    grouped = df.groupby(["constructor", "constructor_name"])
    value = grouped.size() if column is None else grouped[column].sum()
    table = pd.DataFrame({"value": value}).reset_index()
    span = (df.groupby("constructor")
            .agg(first_season=("season", "min"), last_season=("season", "max"),
                 starts=("season", "size")).reset_index())
    table = table.merge(span, on="constructor")
    if active_only:
        newest = df["season"].max()
        table = table[table["last_season"] >= newest - ACTIVE_WITHIN + 1]
    table = table.sort_values("value", ascending=False).head(top).reset_index(drop=True)
    table["label"] = label
    return table


# ---------- great seasons ----------

def title_fights():
    """Every season by how close the drivers' title was at the end."""
    standings = ranked(driver_standings())
    if standings.empty:
        return pd.DataFrame()
    rows = []
    for season, group in standings.groupby("season"):
        group = group.sort_values("position")
        if len(group) < 2:
            continue
        first, second = group.iloc[0], group.iloc[1]
        rows.append({
            "season": int(season),
            "champion": first["driver_name"],
            "champion_team": first["constructor_name"],
            "runner_up": second["driver_name"],
            "points_first": float(first["points"]),
            "points_second": float(second["points"]),
            "gap": round(float(first["points"]) - float(second["points"]), 1),
            "wins_first": int(first["wins"]),
            "wins_second": int(second["wins"]),
        })
    table = pd.DataFrame(rows)
    return table.sort_values("gap").reset_index(drop=True)


def season_points_progress(season, top=6):
    """Points added up race by race for the leading drivers of one season.

    Before 1991 only a driver's best few results counted towards the title, so this line
    is the raw total and will not always match the official table of the time.
    """
    df = results()
    if df.empty:
        return df, []
    rows = df[df["season"] == season]
    if rows.empty:
        return pd.DataFrame(), []
    totals = rows.groupby(["driver", "driver_name"])["points"].sum().nlargest(top)
    names = [n for _, n in totals.index]
    chosen = rows[rows["driver_name"].isin(names)]
    per_round = (chosen.groupby(["round", "race_name", "driver_name"], as_index=False)["points"]
                 .sum())
    rounds = per_round[["round", "race_name"]].drop_duplicates().sort_values("round")
    grid = rounds.merge(pd.DataFrame({"driver_name": names}), how="cross")
    out = grid.merge(per_round, on=["round", "race_name", "driver_name"], how="left")
    out["points"] = out["points"].fillna(0.0)
    out = out.sort_values(["driver_name", "round"])
    out["cum_points"] = out.groupby("driver_name")["points"].cumsum()
    return out.reset_index(drop=True), names


def decided_in_the_last_race():
    """Seasons where the championship was still open going into the final round."""
    df = results()
    standings = driver_standings()
    if df.empty or standings.empty:
        return pd.DataFrame()
    rows = []
    for season, group in df.groupby("season"):
        last = group["round"].max()
        before = group[group["round"] < last]
        if before.empty:
            continue
        totals = before.groupby("driver_name")["points"].sum().sort_values(ascending=False)
        if len(totals) < 2:
            continue
        champion = standings[(standings["season"] == season) & (standings["position"] == 1)]
        gap = totals.iloc[0] - totals.iloc[1]
        best_final = group[group["round"] == last]["points"].max()
        if gap <= best_final:
            rows.append({
                "season": int(season),
                "leader_before": totals.index[0],
                "chaser": totals.index[1],
                "gap_before_final": round(float(gap), 1),
                "most_on_offer": round(float(best_final), 1),
                "champion": champion["driver_name"].iloc[0] if not champion.empty else "",
            })
    return pd.DataFrame(rows).sort_values("season", ascending=False).reset_index(drop=True)


# ---------- one driver ----------

def driver_index():
    """Every driver in the archive: name, seasons raced, starts and wins."""
    df = results()
    if df.empty:
        return df
    table = (df.groupby(["driver", "driver_name"])
             .agg(starts=("season", "size"), wins=("win", "sum"), podiums=("podium", "sum"),
                  points=("points", "sum"), first_season=("season", "min"),
                  last_season=("season", "max"), nationality=("nationality", "last"))
             .reset_index())
    return table.sort_values(["wins", "starts"], ascending=False).reset_index(drop=True)


def driver_career(driver_id):
    """A driver's totals across their whole career."""
    df = results()
    mine = df[df["driver"] == driver_id] if not df.empty else df
    if mine.empty:
        return {}
    titles = title_counts("driver")
    won = titles[titles["driver"] == driver_id]
    return {
        "name": mine["driver_name"].iloc[-1],
        "nationality": mine["nationality"].iloc[-1],
        "starts": int(len(mine)),
        "wins": int(mine["win"].sum()),
        "podiums": int(mine["podium"].sum()),
        "poles": int(mine["pole"].sum()),
        "points": round(float(mine["points"].sum()), 1),
        "best_finish": int(mine["finish_position"].min()),
        "first_season": int(mine["season"].min()),
        "last_season": int(mine["season"].max()),
        "teams": sorted(mine["constructor_name"].unique().tolist()),
        "titles": int(won["titles"].iloc[0]) if not won.empty else 0,
        "title_years": won["years"].iloc[0] if not won.empty else "",
    }


def driver_seasons(driver_id):
    """Season by season for one driver, with the official championship place."""
    df = results()
    standings = driver_standings()
    mine = df[df["driver"] == driver_id] if not df.empty else df
    if mine.empty:
        return pd.DataFrame()
    per_season = (mine.groupby("season")
                  .agg(team=("constructor_name", "last"), races=("round", "size"),
                       wins=("win", "sum"), podiums=("podium", "sum"), poles=("pole", "sum"),
                       points=("points", "sum"), best_finish=("finish_position", "min"))
                  .reset_index())
    standings = ranked(standings)
    if not standings.empty:
        places = (standings[standings["driver"] == driver_id][["season", "position"]]
                  .rename(columns={"position": "championship_place"}))
        per_season = per_season.merge(places, on="season", how="left")
    return per_season.sort_values("season").reset_index(drop=True)


# ---------- one circuit ----------

def circuit_index():
    """Every circuit in the archive, with how many races it has held."""
    races = race_list()
    if races.empty:
        return races
    table = (races.groupby(["circuit", "circuit_name"])
             .agg(races=("season", "size"), first_season=("season", "min"),
                  last_season=("season", "max"), country=("country", "last"),
                  locality=("locality", "last"), latitude=("latitude", "last"),
                  longitude=("longitude", "last")).reset_index())
    return table.sort_values("races", ascending=False).reset_index(drop=True)


def circuit_winners(circuit_id):
    """Everyone who has won at one circuit, most wins first."""
    df = results()
    if df.empty:
        return df, pd.DataFrame()
    here = df[(df["circuit"] == circuit_id) & (df["win"] == 1)]
    if here.empty:
        return pd.DataFrame(), pd.DataFrame()
    by_driver = (here.groupby(["driver", "driver_name"], as_index=False).size()
                 .rename(columns={"size": "wins"})
                 .sort_values("wins", ascending=False).reset_index(drop=True))
    by_team = (here.groupby(["constructor", "constructor_name"], as_index=False).size()
               .rename(columns={"size": "wins"})
               .sort_values("wins", ascending=False).reset_index(drop=True))
    return by_driver, by_team


def circuit_history(circuit_id):
    """Every race held at one circuit: the year, the winner and who they drove for."""
    df = results()
    if df.empty:
        return df
    here = df[(df["circuit"] == circuit_id) & (df["win"] == 1)]
    return (here[["season", "race_name", "driver_name", "constructor_name", "date"]]
            .sort_values("season", ascending=False).reset_index(drop=True))


# ---------- on this day ----------

def on_this_day(month, day):
    """Every race held on this date, whatever the year, with its winner."""
    df = results()
    if df.empty:
        return df
    dates = pd.to_datetime(df["date"], errors="coerce")
    match = df[(dates.dt.month == month) & (dates.dt.day == day) & (df["win"] == 1)]
    if match.empty:
        return pd.DataFrame()
    return (match[["season", "race_name", "circuit", "driver_name", "constructor_name", "date"]]
            .sort_values("season", ascending=False).reset_index(drop=True))


# ---------- two drivers, side by side ----------

def head_to_head(driver_a, driver_b):
    """Two drivers compared over every race they both took part in, plus career totals."""
    df = results()
    if df.empty:
        return {}
    left = df[df["driver"] == driver_a].set_index(["season", "round"])
    right = df[df["driver"] == driver_b].set_index(["season", "round"])
    shared = left.index.intersection(right.index)
    la, rb = left.loc[shared], right.loc[shared]
    both_finished = (la["finished"] == 1) & (rb["finished"] == 1)
    teammate_rounds = int((la["constructor"] == rb["constructor"]).sum()) if len(shared) else 0
    return {
        "a": driver_career(driver_a),
        "b": driver_career(driver_b),
        "races_together": int(len(shared)),
        "as_teammates": teammate_rounds,
        "ahead_a": int((la["finish_position"][both_finished] <
                        rb["finish_position"][both_finished]).sum()),
        "ahead_b": int((rb["finish_position"][both_finished] <
                        la["finish_position"][both_finished]).sum()),
        "grid_a": int((la["grid"].where(la["grid"] > 0) <
                       rb["grid"].where(rb["grid"] > 0)).sum()),
        "grid_b": int((rb["grid"].where(rb["grid"] > 0) <
                       la["grid"].where(la["grid"] > 0)).sum()),
        "seasons": sorted({int(s) for s, _ in shared}),
    }


if __name__ == "__main__":
    if not available():
        print("The history files are missing. Run: python src/history_loader.py")
    else:
        df = results()
        print(f"{len(df)} results, {df['season'].min()} to {df['season'].max()}")
        print(f"\nMost titles:\n{title_counts('driver').head(5).to_string(index=False)}")
        print(f"\nMost wins:\n{driver_records('wins').head(5).to_string(index=False)}")
        print(f"\nClosest titles:\n{title_fights().head(5).to_string(index=False)}")
