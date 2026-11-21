"""Rules Sandbox: recompute every drivers' championship since 1950 under different rules.

A points system is a list of points for P1, P2, P3... Options on top:
  fastest_lap  one extra point for the fastest lap (only where the data says who set it,
               which is 2004 onwards in our archive, and only for a top-10 finisher)
  best_of      count only each driver's best N scores of the season (0 = count them all)
  sprints      add the real sprint-race points (2021 onwards) as they were awarded

Only classified finishers score (Jolpica's position text is a number). Ties are broken
the official way: most wins, then most second places, and so on.

Michael Schumacher's 1997 season is left out of the tables: he was excluded from that
championship for causing a collision with Jacques Villeneuve.

What this does NOT reproduce: shared drives in the 1950s (points were split between the
drivers of one car), the exact dropped-results rules of each era, and half points for
shortened races. So the "real" column always comes from the official standings, not
from re-running the historical system.

Test from the terminal:
  python src/rules.py
"""
import numpy as np
import pandas as pd

from archive import champions, results

SYSTEMS = {
    "Today's (25-18-15-12-10-8-6-4-2-1)": [25, 18, 15, 12, 10, 8, 6, 4, 2, 1],
    "2003–2009 (10-8-6-5-4-3-2-1)": [10, 8, 6, 5, 4, 3, 2, 1],
    "1991–2002 (10-6-4-3-2-1)": [10, 6, 4, 3, 2, 1],
    "1961–1990 (9-6-4-3-2-1)": [9, 6, 4, 3, 2, 1],
    "1950s (8-6-4-3-2)": [8, 6, 4, 3, 2],
    "Winner takes all (1-0-0…)": [1],
    "Everyone scores (20 down to 1)": list(range(20, 0, -1)),
    "Most wins, then seconds (medals)": [1_000_000, 1_000, 1],
}


# Drivers thrown out of a championship after the fact: their results stand, but they can't
# be ranked in that season's table.
EXCLUDED = {(1997, "michael_schumacher")}


def scored(points, fastest_lap=False):
    """Every classified result with its points under one system."""
    df = results()
    out = df.apply(lambda r: (int(r["season"]), r["driver"]) in EXCLUDED, axis=1) if len(df) else []
    df = df[~out] if len(df) else df
    classified = pd.to_numeric(df["position_text"], errors="coerce")
    df = df.assign(pos=classified)
    table = np.zeros(int(df["pos"].max() or 1) + 2)
    table[1:len(points) + 1] = points
    df["new_points"] = np.where(df["pos"].notna(), table[df["pos"].fillna(0).astype(int).clip(0, len(table) - 1)], 0.0)
    if fastest_lap:
        df["new_points"] += ((df["fastest_lap_rank"] == 1) & (df["pos"] <= 10)).astype(float)
    return df


def season_tables(points, fastest_lap=False, best_of=0, sprints=False):
    """Final standings for every season: season, driver, driver_name, team, points, wins, rank."""
    df = scored(points, fastest_lap)
    keep = ["season", "round", "driver", "driver_name", "constructor_name", "pos", "new_points"]
    rows = df[keep]
    if best_of:
        rows = (rows.sort_values("new_points", ascending=False).groupby(["season", "driver"])
                .head(best_of))
    totals = rows.groupby(["season", "driver"])["new_points"].sum()
    if sprints:
        sp = _sprints()
        if not sp.empty:
            totals = totals.add(sp, fill_value=0)

    # Countback: wins, seconds, thirds... as a sortable key
    places = df[df["pos"].notna() & (df["pos"] <= 10)].pivot_table(
        index=["season", "driver"], columns="pos", values="round", aggfunc="count", fill_value=0)
    table = pd.DataFrame({"points": totals})
    table = table.join(places, how="left").fillna(0)
    info = df.sort_values("round").groupby(["season", "driver"]).agg(
        driver_name=("driver_name", "last"), team=("constructor_name", "last"))
    table = table.join(info)
    table["wins"] = table.get(1.0, 0)
    sort_cols = ["points"] + [c for c in sorted(places.columns)]
    table = table.reset_index().sort_values(["season"] + sort_cols, ascending=[True] + [False] * len(sort_cols))
    table["rank"] = table.groupby("season").cumcount() + 1
    return table[["season", "driver", "driver_name", "team", "points", "wins", "rank"]]


def _sprints():
    try:
        sp = pd.read_csv(_sprint_file())
    except (FileNotFoundError, OSError):
        return pd.Series(dtype=float)
    return sp.groupby(["season", "driver"])["sprint_points"].sum()


def _sprint_file():
    from archive import RESULTS_FILE
    return RESULTS_FILE.parent / "sprint.csv"


def compare(points, fastest_lap=False, best_of=0, sprints=False):
    """One row per season: the real champion and the champion under these rules."""
    new = season_tables(points, fastest_lap, best_of, sprints)
    real = champions()[["season", "driver", "driver_name", "driver_team"]].rename(
        columns={"driver": "real", "driver_name": "real_name", "driver_team": "real_team"})
    top = new[new["rank"] == 1].rename(columns={"driver": "new", "driver_name": "new_name", "team": "new_team",
                                                "points": "new_points"})
    second = new[new["rank"] == 2][["season", "points", "driver_name"]].rename(
        columns={"points": "second_points", "driver_name": "second_name"})
    out = real.merge(top[["season", "new", "new_name", "new_team", "new_points"]], on="season", how="left")
    out = out.merge(second, on="season", how="left")
    out["changed"] = out["real"] != out["new"]
    out["margin"] = out["new_points"] - out["second_points"]
    return out, new


def title_counts(table):
    """Titles per driver under one set of rules."""
    return table[table["rank"] == 1].groupby("driver_name").size().sort_values(ascending=False)


if __name__ == "__main__":
    out, _ = compare(SYSTEMS["Today's (25-18-15-12-10-8-6-4-2-1)"])
    changed = out[out["changed"]]
    print(f"Today's points for every season: {len(changed)} of {len(out)} titles change hands")
    for _, r in changed.iterrows():
        print(f"  {r['season']}: {r['real_name']} -> {r['new_name']}")
