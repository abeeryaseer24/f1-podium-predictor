"""Championship tables, reliability and head-to-head records, worked out from the race
results the project already downloads.

Nothing here calls the internet. Everything comes from data/processed/results.csv and,
when the file is there, data/processed/sprint.csv. Points are simply added up race by
race, which matches the official tables for every season in our data (2016 onwards).

Test from the terminal:
  python src/standings.py 2026
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = ROOT / "data" / "processed" / "results.csv"
SPRINT_CSV = ROOT / "data" / "processed" / "sprint.csv"

# How many places a countback looks at when two teams or drivers are level on points
COUNTBACK_DEPTH = 10


# ---------- loading ----------

def load_results():
    """Every race result, with two extra columns: finished and dnf."""
    df = pd.read_csv(RESULTS_CSV)
    status = df["status"].fillna("")
    finished = (status.eq("Finished") | status.str.startswith("+") | status.eq("Lapped"))
    df["finished"] = finished.astype(int)
    df["dnf"] = (~finished).astype(int)
    df["podium"] = (df["finish_position"] <= 3).astype(int)
    df["win"] = (df["finish_position"] == 1).astype(int)
    df["pole"] = (df["quali_position"] == 1).astype(int)
    return df


def load_sprint():
    """Sprint race points, or an empty table if src/sprint_loader.py has never been run.
    Without this file the standings are race points only, which is wrong on sprint
    weekends, so every page that uses it says whether the file was found."""
    columns = ["season", "round", "driver", "constructor", "sprint_position", "sprint_points"]
    if not SPRINT_CSV.exists():
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(SPRINT_CSV)
    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df[columns]


def has_sprint_data():
    return SPRINT_CSV.exists()


# ---------- points per driver per round ----------

def points_table(season=None):
    """One row per driver per round: race points, sprint points and the total."""
    results = load_results()
    if season is not None:
        results = results[results["season"] == season]
    keep = ["season", "round", "race_name", "date", "circuit", "driver", "constructor",
            "grid", "quali_position", "finish_position", "status", "points",
            "finished", "dnf", "podium", "win", "pole"]
    table = results[keep].copy()
    table = table.rename(columns={"points": "race_points"})

    sprint = load_sprint()
    if not sprint.empty:
        sprint = sprint.drop(columns=["constructor"])
        table = table.merge(sprint, on=["season", "round", "driver"], how="left")
    else:
        table["sprint_position"] = pd.NA
        table["sprint_points"] = pd.NA
    table["sprint_points"] = pd.to_numeric(table["sprint_points"], errors="coerce").fillna(0.0)
    table["total_points"] = table["race_points"] + table["sprint_points"]
    return table


# ---------- ranking ----------

def _countback(frame, group_col, finish_col="finish_position"):
    """How many P1s, P2s, P3s ... each team or driver has. Used to split teams that
    finish the season level on points, the way the rules do."""
    counts = {}
    for place in range(1, COUNTBACK_DEPTH + 1):
        at_place = frame[frame[finish_col] == place].groupby(group_col).size()
        counts[f"p{place}"] = at_place
    out = pd.DataFrame(counts).fillna(0).astype(int)
    return out.reindex(frame[group_col].unique(), fill_value=0)


def _rank(table, frame, group_col):
    """Add a 'position' column: most points first, then most wins, then most seconds..."""
    back = _countback(frame, group_col)
    merged = table.join(back, how="left").fillna({c: 0 for c in back.columns})
    order = ["points"] + list(back.columns)
    merged = merged.sort_values(order, ascending=False)
    merged["position"] = range(1, len(merged) + 1)
    return merged.drop(columns=list(back.columns))


# ---------- constructors ----------

def constructor_table(season):
    """The constructors' championship for one season: points, wins, podiums and more."""
    rows = points_table(season)
    if rows.empty:
        return rows
    grouped = rows.groupby("constructor")
    table = pd.DataFrame({
        "points": grouped["total_points"].sum().round(1),
        "race_points": grouped["race_points"].sum().round(1),
        "sprint_points": grouped["sprint_points"].sum().round(1),
        "wins": grouped["win"].sum(),
        "podiums": grouped["podium"].sum(),
        "poles": grouped["pole"].sum(),
        "entries": grouped.size(),
        "finishes": grouped["finished"].sum(),
        "dnfs": grouped["dnf"].sum(),
        "best_finish": grouped["finish_position"].min(),
        "avg_finish": grouped["finish_position"].mean().round(2),
    })
    table = _rank(table, rows, "constructor")
    table["drivers"] = [sorted(rows.loc[rows["constructor"] == c, "driver"].unique())
                        for c in table.index]
    return table.reset_index()


def constructor_progress(season):
    """How the constructors' table looked after every round: points that round, the
    running total and the championship position at that point in the season."""
    rows = points_table(season)
    if rows.empty:
        return rows
    per_round = (rows.groupby(["round", "race_name", "constructor"], as_index=False)
                 ["total_points"].sum().rename(columns={"total_points": "points"}))
    # Every team gets a row for every round, so the lines never break
    rounds = per_round[["round", "race_name"]].drop_duplicates().sort_values("round")
    teams = sorted(per_round["constructor"].unique())
    grid = rounds.merge(pd.DataFrame({"constructor": teams}), how="cross")
    out = grid.merge(per_round, on=["round", "race_name", "constructor"], how="left")
    out["points"] = out["points"].fillna(0.0)
    out = out.sort_values(["constructor", "round"])
    out["cum_points"] = out.groupby("constructor")["points"].cumsum()
    out["position"] = (out.groupby("round")["cum_points"]
                       .rank(method="min", ascending=False).astype(int))
    leader = out.groupby("round")["cum_points"].transform("max")
    out["gap_to_leader"] = (leader - out["cum_points"]).round(1)
    return out.sort_values(["round", "position"]).reset_index(drop=True)


# ---------- drivers ----------

def driver_table(season):
    """The drivers' championship for one season."""
    rows = points_table(season)
    if rows.empty:
        return rows
    grouped = rows.groupby("driver")
    table = pd.DataFrame({
        "points": grouped["total_points"].sum().round(1),
        "wins": grouped["win"].sum(),
        "podiums": grouped["podium"].sum(),
        "poles": grouped["pole"].sum(),
        "entries": grouped.size(),
        "finishes": grouped["finished"].sum(),
        "dnfs": grouped["dnf"].sum(),
        "best_finish": grouped["finish_position"].min(),
        "avg_finish": grouped["finish_position"].mean().round(2),
        "avg_grid": grouped["grid"].mean().round(2),
    })
    table = _rank(table, rows, "driver")
    last_team = rows.sort_values("round").groupby("driver")["constructor"].last()
    table["constructor"] = last_team
    return table.reset_index()


def driver_progress(season):
    """The drivers' table after every round."""
    rows = points_table(season)
    if rows.empty:
        return rows
    per_round = (rows.groupby(["round", "race_name", "driver"], as_index=False)
                 ["total_points"].sum().rename(columns={"total_points": "points"}))
    rounds = per_round[["round", "race_name"]].drop_duplicates().sort_values("round")
    drivers = sorted(per_round["driver"].unique())
    grid = rounds.merge(pd.DataFrame({"driver": drivers}), how="cross")
    out = grid.merge(per_round, on=["round", "race_name", "driver"], how="left")
    out["points"] = out["points"].fillna(0.0)
    out = out.sort_values(["driver", "round"])
    out["cum_points"] = out.groupby("driver")["points"].cumsum()
    out["position"] = (out.groupby("round")["cum_points"]
                       .rank(method="min", ascending=False).astype(int))
    teams = rows[["round", "driver", "constructor"]].drop_duplicates(["round", "driver"])
    out = out.merge(teams, on=["round", "driver"], how="left")
    out["constructor"] = out.groupby("driver")["constructor"].ffill().bfill()
    return out.sort_values(["round", "position"]).reset_index(drop=True)


# ---------- why cars stop ----------

def cause_group(status):
    """Turn the many status words the API uses into a handful of plain reasons."""
    s = str(status).lower()
    if s in ("finished", "lapped") or s.startswith("+"):
        return "Finished"
    if any(w in s for w in ("collision", "accident", "spun", "damage", "puncture")):
        return "Crash or damage"
    if any(w in s for w in ("engine", "power unit", "turbo", "ers", "exhaust", "overheat",
                            "water", "oil", "fuel", "battery", "cooling", "radiator",
                            "spark", "injection", "pneumatic")):
        return "Power unit"
    if any(w in s for w in ("gearbox", "transmission", "clutch", "driveshaft", "halfshaft",
                            "differential", "drivetrain")):
        return "Gearbox or drivetrain"
    if any(w in s for w in ("hydraulic", "brake", "suspension", "wheel", "steering",
                            "electr", "throttle", "chassis", "vibration", "wing",
                            "undertray", "drs", "handling", "mechanical", "technical",
                            "power loss", "seat", "debris", "tyre", "track rod", "axle")):
        return "Other mechanical"
    if any(w in s for w in ("disqualif", "excluded")):
        return "Disqualified"
    if any(w in s for w in ("withdrew", "did not", "injur", "illness", "fatal", "safety")):
        return "Did not start"
    if "retired" in s:
        return "Retired, no reason given"
    return "Other"


def dnf_grid(season):
    """One row per team per round: how many of its cars failed to finish.

    The results feed stopped recording *why* a car retired a few seasons ago, so a
    chart of causes is nearly empty for a recent year. Which races a team lost cars at
    is still real, and says more anyway: three in a row is a pattern, one is a shunt.
    """
    rows = points_table(season)
    if rows.empty:
        return rows
    grid = (rows.groupby(["round", "race_name", "constructor"], as_index=False)
            .agg(cars=("dnf", "size"), dnfs=("dnf", "sum")))
    grid["dnfs"] = grid["dnfs"].astype(int)
    return grid.sort_values(["round", "constructor"]).reset_index(drop=True)


def reasons_recorded(season):
    """How many different retirement reasons the feed actually gives for a season.

    Anything below about three means the data is generic ("Retired") rather than
    specific ("Gearbox"), and a chart of causes would be telling the reader nothing.
    """
    rows = points_table(season)
    if rows.empty:
        return 0
    stops = rows[rows["dnf"] == 1]
    if stops.empty:
        return 0
    named = stops["status"].map(cause_group)
    return int(named[~named.isin(["Retired, no reason given", "Other"])].nunique())


def reliability(season):
    """How often each team's cars reached the finish, and why the others stopped."""
    rows = points_table(season)
    if rows.empty:
        return rows, rows
    rows = rows.copy()
    rows["cause"] = rows["status"].map(cause_group)
    grouped = rows.groupby("constructor")
    summary = pd.DataFrame({
        "entries": grouped.size(),
        "finishes": grouped["finished"].sum(),
        "dnfs": grouped["dnf"].sum(),
    })
    summary["finish_rate"] = (100 * summary["finishes"] / summary["entries"]).round(1)
    summary = summary.sort_values("finish_rate", ascending=False).reset_index()

    stops = rows[rows["dnf"] == 1]
    causes = (stops.groupby(["constructor", "cause"], as_index=False).size()
              .rename(columns={"size": "count"})) if not stops.empty else \
        pd.DataFrame(columns=["constructor", "cause", "count"])
    return summary, causes


# ---------- teammates ----------

def teammate_battles(season):
    """Inside each garage: who out-qualified whom, who finished ahead, and the points.
    Only rounds where both drivers of a team have a result are counted, which is the
    fair way to do it. Teams that used more than two drivers get every pair that raced
    together."""
    rows = points_table(season)
    if rows.empty:
        return pd.DataFrame()
    out = []
    for team, group in rows.groupby("constructor"):
        drivers = sorted(group["driver"].unique())
        for i, a in enumerate(drivers):
            for b in drivers[i + 1:]:
                left = group[group["driver"] == a].set_index("round")
                right = group[group["driver"] == b].set_index("round")
                shared = left.index.intersection(right.index)
                if len(shared) == 0:
                    continue
                la, rb = left.loc[shared], right.loc[shared]
                quali = la["quali_position"].notna() & rb["quali_position"].notna()
                race = (la["finished"] == 1) & (rb["finished"] == 1)
                out.append({
                    "constructor": team,
                    "driver_a": a,
                    "driver_b": b,
                    "races_together": len(shared),
                    "quali_a": int((la["quali_position"][quali] < rb["quali_position"][quali]).sum()),
                    "quali_b": int((rb["quali_position"][quali] < la["quali_position"][quali]).sum()),
                    "race_a": int((la["finish_position"][race] < rb["finish_position"][race]).sum()),
                    "race_b": int((rb["finish_position"][race] < la["finish_position"][race]).sum()),
                    "points_a": round(float(la["total_points"].sum()), 1),
                    "points_b": round(float(rb["total_points"].sum()), 1),
                    "dnf_a": int(la["dnf"].sum()),
                    "dnf_b": int(rb["dnf"].sum()),
                })
    frame = pd.DataFrame(out)
    if not frame.empty:
        frame = frame.sort_values("races_together", ascending=False)
    return frame.reset_index(drop=True)


# ---------- one team, across the years ----------

def team_history(team_id, family_ids):
    """Every season this team has raced in our data, under any of its old names."""
    results = points_table()
    mine = results[results["constructor"].isin(family_ids)]
    if mine.empty:
        return pd.DataFrame()
    rows = []
    for season, group in mine.groupby("season"):
        table = constructor_table(int(season))
        here = table[table["constructor"].isin(family_ids)]
        if here.empty:
            continue
        row = here.iloc[0]
        rows.append({
            "season": int(season),
            "raced_as": row["constructor"],
            "position": int(row["position"]),
            "points": float(row["points"]),
            "wins": int(row["wins"]),
            "podiums": int(row["podiums"]),
            "poles": int(row["poles"]),
            "entries": int(row["entries"]),
            "teams_that_season": int(len(table)),
        })
    return pd.DataFrame(rows).sort_values("season").reset_index(drop=True)


def team_drivers(family_ids):
    """Every driver who has raced for this team in our data, best first."""
    results = points_table()
    mine = results[results["constructor"].isin(family_ids)]
    if mine.empty:
        return pd.DataFrame()
    grouped = mine.groupby("driver")
    table = pd.DataFrame({
        "races": grouped.size(),
        "wins": grouped["win"].sum(),
        "podiums": grouped["podium"].sum(),
        "poles": grouped["pole"].sum(),
        "points": grouped["total_points"].sum().round(1),
        "best_finish": grouped["finish_position"].min(),
        "first_season": grouped["season"].min(),
        "last_season": grouped["season"].max(),
    })
    return table.sort_values(["wins", "podiums", "points"], ascending=False).reset_index()


# ---------- one driver, across the years ----------

def driver_history(driver_id):
    """Season by season for one driver: team, points, championship position and more."""
    results = points_table()
    mine = results[results["driver"] == driver_id]
    if mine.empty:
        return pd.DataFrame()
    rows = []
    for season, group in mine.groupby("season"):
        table = driver_table(int(season))
        here = table[table["driver"] == driver_id]
        if here.empty:
            continue
        row = here.iloc[0]
        rows.append({
            "season": int(season),
            "constructor": group.sort_values("round")["constructor"].iloc[-1],
            "position": int(row["position"]),
            "points": float(row["points"]),
            "wins": int(row["wins"]),
            "podiums": int(row["podiums"]),
            "poles": int(row["poles"]),
            "races": int(row["entries"]),
            "best_finish": int(row["best_finish"]),
            "dnfs": int(row["dnfs"]),
        })
    return pd.DataFrame(rows).sort_values("season").reset_index(drop=True)


def driver_totals(driver_id):
    """A driver's career totals across everything in our data."""
    results = points_table()
    mine = results[results["driver"] == driver_id]
    if mine.empty:
        return {}
    return {
        "races": int(len(mine)),
        "wins": int(mine["win"].sum()),
        "podiums": int(mine["podium"].sum()),
        "poles": int(mine["pole"].sum()),
        "points": round(float(mine["total_points"].sum()), 1),
        "best_finish": int(mine["finish_position"].min()),
        "dnfs": int(mine["dnf"].sum()),
        "first_season": int(mine["season"].min()),
        "last_season": int(mine["season"].max()),
        "teams": sorted(mine["constructor"].unique()),
    }


def driver_teammate_record(driver_id):
    """This driver against every teammate they have had, over all seasons in our data."""
    results = points_table()
    mine = results[results["driver"] == driver_id]
    if mine.empty:
        return pd.DataFrame()
    pairs = results.merge(
        mine[["season", "round", "constructor"]].drop_duplicates(),
        on=["season", "round", "constructor"], how="inner")
    others = pairs[pairs["driver"] != driver_id]
    rows = []
    for mate, group in others.groupby("driver"):
        keys = ["season", "round"]
        left = mine.set_index(keys)
        right = group.set_index(keys)
        shared = left.index.intersection(right.index)
        if len(shared) == 0:
            continue
        la, rb = left.loc[shared], right.loc[shared]
        quali = la["quali_position"].notna() & rb["quali_position"].notna()
        race = (la["finished"] == 1) & (rb["finished"] == 1)
        rows.append({
            "teammate": mate,
            "races_together": len(shared),
            "quali_me": int((la["quali_position"][quali] < rb["quali_position"][quali]).sum()),
            "quali_them": int((rb["quali_position"][quali] < la["quali_position"][quali]).sum()),
            "race_me": int((la["finish_position"][race] < rb["finish_position"][race]).sum()),
            "race_them": int((rb["finish_position"][race] < la["finish_position"][race]).sum()),
            "points_me": round(float(la["total_points"].sum()), 1),
            "points_them": round(float(rb["total_points"].sum()), 1),
            "seasons": ", ".join(str(s) for s in sorted(la.index.get_level_values("season").unique())),
        })
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values("races_together", ascending=False)
    return frame.reset_index(drop=True)


# ---------- who is racing now ----------

def current_entries(season):
    """The drivers and teams of a season: one row per driver, with their team and number
    of races. Used by the card pages."""
    rows = points_table(season)
    if rows.empty:
        return rows
    last = rows.sort_values("round").groupby("driver").tail(1)
    counts = rows.groupby("driver").size().rename("races")
    out = last[["driver", "constructor", "round"]].merge(counts, on="driver")
    return out.sort_values(["constructor", "driver"]).reset_index(drop=True)


if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    print(f"Sprint file found: {has_sprint_data()}")
    print(f"\nConstructors {year}")
    print(constructor_table(year)[["position", "constructor", "points", "wins", "podiums",
                                   "dnfs"]].to_string(index=False))
    print(f"\nDrivers {year} (top 10)")
    print(driver_table(year).head(10)[["position", "driver", "constructor", "points",
                                       "wins"]].to_string(index=False))
