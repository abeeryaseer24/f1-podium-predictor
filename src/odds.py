"""Championship odds: who can still win the title, and how likely it is.

The model already works out a strength for every driver in the next race (see ranker.py).
This replays the rest of the season thousands of times using those strengths: each race is
drawn from the same Plackett-Luce model the predictions use, drivers retire at roughly the
rate they have this season, points are awarded the normal way, and at the end we count how
often each driver and each team finished on top.

It assumes the rest of the season looks like the next race. A big upgrade, a wet weekend or
a driver change will not be in it, which is the honest limit of doing it this way.
"""
import numpy as np
import pandas as pd

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]      # a Grand Prix, P1 to P10
SPRINT_POINTS = [8, 7, 6, 5, 4, 3, 2, 1]          # a sprint race, P1 to P8
SIMULATIONS = 5000
SPRINT_DNF_SHARE = 0.5     # a sprint is about a third the distance, so fewer cars break
PRIOR_RACES = 10           # how strongly a driver's retirement rate is pulled to the average


def points_array(n_drivers, scheme):
    """Points by finishing place, as an array long enough for the whole field."""
    table = np.zeros(n_drivers)
    take = min(len(scheme), n_drivers)
    table[:take] = scheme[:take]
    return table


def dnf_rates(season_rows, drivers):
    """How often each driver has failed to finish this season, smoothed towards the field
    average so a driver with two races does not look either bulletproof or doomed."""
    field = season_rows["dnf"].mean() if len(season_rows) else 0.1
    counts = season_rows.groupby("driver")["dnf"].agg(["sum", "count"])
    out = []
    for driver in drivers:
        if driver in counts.index:
            stops, races = counts.loc[driver, "sum"], counts.loc[driver, "count"]
        else:
            stops, races = 0, 0
        out.append((stops + field * PRIOR_RACES) / (races + PRIOR_RACES))
    return np.clip(np.array(out, dtype=float), 0.0, 0.6)


def simulate(drivers, strength, dnf_rate, driver_points_now, team_of, team_points_now,
             races_left, sprints_left, luck=1.0, simulations=SIMULATIONS, seed=0):
    """Replay the rest of the season. Returns one table for drivers and one for teams.

    drivers            list of driver ids, in the same order as strength and dnf_rate
    strength           the model's strength for each driver (higher is better)
    driver_points_now  points each driver already has
    team_of            team id for each driver
    team_points_now    {team id: points already scored}
    """
    rng = np.random.default_rng(seed)
    n = len(drivers)
    if n == 0:
        return pd.DataFrame(), pd.DataFrame()

    race_points = points_array(n, POINTS)
    sprint_points = points_array(n, SPRINT_POINTS)

    gained = np.zeros((simulations, n))
    rounds = ([(race_points, dnf_rate)] * races_left +
              [(sprint_points, dnf_rate * SPRINT_DNF_SHARE)] * sprints_left)
    for scheme, stop_rate in rounds:
        noise = strength[None, :] / luck + rng.gumbel(size=(simulations, n))
        running = rng.random((simulations, n)) >= stop_rate[None, :]
        noise = np.where(running, noise, -np.inf)
        place = (-noise).argsort(axis=1).argsort(axis=1)      # 0 = winner
        gained += np.where(running, scheme[place], 0.0)

    # A tiny nudge splits exact ties at random. Real ties are settled by a countback on
    # wins, so a dead heat here is shown as a coin flip rather than pretending to know.
    totals = driver_points_now[None, :] + gained
    jitter = totals + rng.random((simulations, n)) * 1e-6
    champion = jitter.argmax(axis=1)
    top3 = (jitter.argsort(axis=1).argsort(axis=1) >= n - 3)

    driver_table = pd.DataFrame({
        "driver": drivers,
        "constructor": [team_of[d] for d in drivers],
        "points_now": driver_points_now,
        "expected_points": totals.mean(axis=0).round(1),
        "low_points": np.percentile(totals, 10, axis=0).round(0),
        "high_points": np.percentile(totals, 90, axis=0).round(0),
        "title_chance": 100 * np.bincount(champion, minlength=n) / simulations,
        "top3_chance": 100 * top3.mean(axis=0),
    }).sort_values(["title_chance", "expected_points"], ascending=False).reset_index(drop=True)

    # Teams: a driver's new points go to the team they are driving for now.
    teams = sorted(set(team_of[d] for d in drivers) | set(team_points_now))
    index = {team: i for i, team in enumerate(teams)}
    membership = np.zeros((n, len(teams)))
    for i, driver in enumerate(drivers):
        membership[i, index[team_of[driver]]] = 1.0
    start = np.array([team_points_now.get(team, 0.0) for team in teams])
    team_totals = start[None, :] + gained @ membership

    jitter = team_totals + rng.random((simulations, len(teams))) * 1e-6
    team_champion = jitter.argmax(axis=1)
    team_table = pd.DataFrame({
        "constructor": teams,
        "points_now": start,
        "expected_points": team_totals.mean(axis=0).round(1),
        "low_points": np.percentile(team_totals, 10, axis=0).round(0),
        "high_points": np.percentile(team_totals, 90, axis=0).round(0),
        "title_chance": 100 * np.bincount(team_champion, minlength=len(teams)) / simulations,
    }).sort_values(["title_chance", "expected_points"], ascending=False).reset_index(drop=True)

    return driver_table, team_table


def most_points_left(races_left, sprints_left, cars=1):
    """The most one entrant could still score.

    A driver can only win the race in front of them, so they take P1 and nothing else.
    A team scores with both of its cars, so a perfect weekend for a team is a one-two,
    which is 43 points and not 25. Getting this wrong makes every team look eliminated
    far earlier than it is.
    """
    race = sum(POINTS[:cars])
    sprint = sum(SPRINT_POINTS[:cars])
    return races_left * race + sprints_left * sprint


def still_alive(table, races_left, sprints_left, cars=1):
    """Add a column saying whether each driver or team can still catch the leader.
    This is arithmetic, not a guess: it is true whenever the gap is smaller than
    everything still on the table."""
    table = table.copy()
    best = table["points_now"].max()
    table["alive"] = (table["points_now"]
                      + most_points_left(races_left, sprints_left, cars) >= best)
    return table


def title_state(table, races_left, sprints_left, cars=1):
    """Whether the championship is still open, and if not, who has already won it.

    "Alive" counts the leader too, so a lone survivor means the title is settled: there
    is nobody left who could still catch them. Saying that plainly is far more use than
    printing the number 1.
    """
    if table.empty:
        return {}
    table = still_alive(table, races_left, sprints_left, cars)
    leader = table.sort_values("points_now", ascending=False).iloc[0]
    alive = table[table["alive"]]
    chasers = alive[alive.index != leader.name]
    on_offer = most_points_left(races_left, sprints_left, cars)
    second = (table.sort_values("points_now", ascending=False).iloc[1]
              if len(table) > 1 else None)
    return {
        "table": table,
        "alive": int(len(alive)),
        "settled": len(alive) <= 1,
        "leader": leader,
        "chasers": chasers,
        "on_offer": on_offer,
        "gap_to_second": (float(leader["points_now"]) - float(second["points_now"]))
                         if second is not None else 0.0,
        "runner_up": second,
    }
