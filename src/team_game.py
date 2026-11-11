"""Beat the AI: Constructors. Working out which teams scored the most at a race, both
from a predicted finishing order and from the real result.

A team's haul is simply the points its two cars scored. Our model predicts the whole
finishing order, so turning that into a team order is just a matter of adding up. The
real answer comes from the points actually awarded, which also takes care of
disqualifications and any other oddity.
"""
from odds import POINTS

PLACES = 3          # visitors pick the top three teams of the race


def points_for(position):
    """Points for one finishing position in a Grand Prix."""
    position = int(position)
    return POINTS[position - 1] if 1 <= position <= len(POINTS) else 0


def teams_from_order(order, team_of):
    """Turn a predicted driver order into a team order, best first.

    order    list of driver ids, first to last
    team_of  {driver id: team id}
    Returns [(team id, points, best finishing position), ...]
    """
    totals, best = {}, {}
    for position, driver in enumerate(order, start=1):
        team = team_of.get(driver)
        if not team:
            continue
        totals[team] = totals.get(team, 0) + points_for(position)
        best[team] = min(best.get(team, 99), position)
    rows = [(team, totals[team], best[team]) for team in totals]
    return sorted(rows, key=lambda r: (-r[1], r[2]))


def teams_from_results(race):
    """The real team order of a finished race, from the points actually awarded.

    race = the rows of data/processed/results.csv for one race.
    Returns [(team id, points, best finishing position), ...]
    """
    rows = []
    for team, group in race.groupby("constructor"):
        rows.append((team, float(group["points"].sum()),
                     int(group["finish_position"].min())))
    return sorted(rows, key=lambda r: (-r[1], r[2]))


def top_teams(rows, places=PLACES):
    """Just the team ids of the leading few."""
    return [team for team, _, _ in rows[:places]]


def score(pick, actual):
    """3 points for a team in the exact spot, 1 for a team in the wrong spot."""
    return sum(3 if p == a else (1 if p in actual else 0)
               for p, a in zip(pick, actual))


def verdict(you, model, actual):
    """'win', 'lose' or 'tie' for the visitor against our model."""
    if not model:
        return None
    yours, ours = score(you, actual), score(model, actual)
    if yours == ours:
        return "tie"
    return "win" if yours > ours else "lose"
