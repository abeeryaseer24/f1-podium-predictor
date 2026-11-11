"""The F1 quiz: questions written from the archive, so every answer is checkable.

Nothing here is hand-written trivia. Each question is built from the real results, the
wrong answers are real drivers, teams or numbers from the same context, and the
explanation says where the answer comes from. If the data cannot support a question,
the builder returns None and another one is tried.

Test from the terminal:
  python src/quiz.py
"""
import random

import pandas as pd

import archive

ERAS = {
    "Mixed": (1950, 3000),
    "Modern, 2010 onwards": (2010, 3000),
    "The classics, before 1990": (1950, 1989),
}
OPTIONS = 4


def bundle():
    """Everything the builders need, loaded once."""
    results = archive.results()
    if results.empty:
        return None
    wins = results[results["win"] == 1]
    return {
        "results": results,
        "wins": wins,
        "champions": archive.champions(),
        "titles": archive.title_counts("driver"),
        "careers": (results.groupby(["driver", "driver_name"])
                    .agg(wins=("win", "sum"), starts=("season", "size"),
                         first=("season", "min"), last=("season", "max"))
                    .reset_index()),
        "circuits": archive.circuit_index(),
    }


def _span(data, era):
    low, high = ERAS.get(era, ERAS["Mixed"])
    rows = data["results"]
    return rows[(rows["season"] >= low) & (rows["season"] <= high)]


def _careers_in(data, era):
    """Drivers who raced inside the chosen era."""
    low, high = ERAS.get(era, ERAS["Mixed"])
    careers = data["careers"]
    return careers[(careers["last"] >= low) & (careers["first"] <= high)]


def _circuits_in(data, era):
    """Circuits that held a race inside the chosen era."""
    low, high = ERAS.get(era, ERAS["Mixed"])
    circuits = data["circuits"]
    return circuits[(circuits["last_season"] >= low) & (circuits["first_season"] <= high)]


def _question(text, correct, wrong, explain, kind, rng):
    """Put one correct answer and three wrong ones in a random order."""
    wrong = [w for w in dict.fromkeys(wrong) if w != correct][:OPTIONS - 1]
    if len(wrong) < OPTIONS - 1:
        return None
    options = wrong + [correct]
    rng.shuffle(options)
    return {"question": text, "options": options, "answer": correct,
            "explain": explain, "kind": kind}


# ---------- the builders ----------

def race_winner(data, rng, era):
    rows = _span(data, era)
    winners = rows[rows["win"] == 1]
    if winners.empty:
        return None
    pick = winners.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    field = rows[(rows["season"] == pick["season"]) & (rows["round"] == pick["round"])]
    others = field[field["driver"] != pick["driver"]]["driver_name"].tolist()
    rng.shuffle(others)
    grid = int(pick["grid"])
    start = f"from pole" if grid == 1 else (f"from P{grid}" if grid > 0 else "")
    return _question(
        f'Who won the {int(pick["season"])} {pick["race_name"]}?',
        pick["driver_name"], others,
        f'{pick["driver_name"]} won for {pick["constructor_name"]} {start}.'.replace("  ", " "),
        "Race winners", rng)


def season_champion(data, rng, era):
    low, high = ERAS.get(era, ERAS["Mixed"])
    table = data["champions"]
    table = table[(table["season"] >= low) & (table["season"] <= high)]
    table = table[table["driver_name"] != ""]
    if table.empty:
        return None
    pick = table.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    season = int(pick["season"])
    standings = archive.ranked(archive.driver_standings())
    rivals = standings[(standings["season"] == season) & (standings["position"] > 1)]
    others = rivals.sort_values("position").head(6)["driver_name"].tolist()
    rng.shuffle(others)
    return _question(
        f"Who was the {season} drivers' champion?",
        pick["driver_name"], others,
        f'{pick["driver_name"]} took the {season} title with {pick["driver_team"]}, '
        f'{int(pick["driver_wins"])} win{"s" if pick["driver_wins"] != 1 else ""} '
        f'and {pick["driver_points"]:g} points.',
        "Champions", rng)


def team_champion(data, rng, era):
    low, high = ERAS.get(era, ERAS["Mixed"])
    table = data["champions"]
    table = table[(table["season"] >= max(low, 1958)) & (table["season"] <= high)]
    table = table[table["team_name"] != ""]
    if table.empty:
        return None
    pick = table.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    season = int(pick["season"])
    standings = archive.ranked(archive.team_standings())
    rivals = standings[(standings["season"] == season) & (standings["position"] > 1)]
    others = rivals.sort_values("position").head(6)["constructor_name"].tolist()
    rng.shuffle(others)
    return _question(
        f"Which team won the {season} constructors' championship?",
        pick["team_name"], others,
        f'{pick["team_name"]} won the {season} constructors\' title with '
        f'{pick["team_points"]:g} points.',
        "Champions", rng)


def season_most_wins(data, rng, era):
    rows = _span(data, era)
    seasons = rows["season"].unique()
    if not len(seasons):
        return None
    season = int(rng.choice(seasons))
    here = rows[rows["season"] == season]
    counts = here[here["win"] == 1].groupby("driver_name").size().sort_values(ascending=False)
    if len(counts) < 2 or counts.iloc[0] == counts.iloc[1]:
        return None                               # no clear answer, try another question
    others = here["driver_name"].unique().tolist()
    rng.shuffle(others)
    return _question(
        f"Who won the most races in {season}?",
        counts.index[0], others,
        f'{counts.index[0]} won {counts.iloc[0]} races that season, '
        f'ahead of {counts.index[1]} on {counts.iloc[1]}.',
        "Seasons", rng)


def wins_in_season(data, rng, era):
    rows = _span(data, era)
    winners = rows[rows["win"] == 1]
    if winners.empty:
        return None
    counts = winners.groupby(["season", "driver_name"]).size()
    counts = counts[counts >= 2]
    if counts.empty:
        return None
    (season, name), total = list(counts.items())[rng.randrange(len(counts))]
    total = int(total)
    wrong = [str(n) for n in {total - 2, total - 1, total + 1, total + 2, total + 3}
             if n >= 0 and n != total]
    rng.shuffle(wrong)
    return _question(
        f"How many races did {name} win in {int(season)}?",
        str(total), wrong,
        f'{name} won {total} races in {int(season)}.',
        "Seasons", rng)


def most_career_wins(data, rng, era):
    careers = _careers_in(data, era).nlargest(40, "wins")
    pool = careers.sample(min(OPTIONS, len(careers)), random_state=rng.randrange(10 ** 6))
    pool = pool.sort_values("wins", ascending=False)
    if len(pool) < OPTIONS or pool.iloc[0]["wins"] == pool.iloc[1]["wins"]:
        return None
    best = pool.iloc[0]
    return _question(
        "Which of these drivers has won the most races?",
        best["driver_name"], pool.iloc[1:]["driver_name"].tolist(),
        f'{best["driver_name"]} won {int(best["wins"])} races, against '
        f'{int(pool.iloc[1]["wins"])} for {pool.iloc[1]["driver_name"]}.',
        "Records", rng)


def how_many_titles(data, rng, era):
    low, high = ERAS.get(era, ERAS["Mixed"])
    titles = data["titles"]
    titles = titles[titles["titles"] >= 2].copy()
    won_in_era = titles["years"].map(
        lambda years: any(low <= int(y) <= high for y in years.split(", ")))
    titles = titles[won_in_era]
    if titles.empty:
        return None
    pick = titles.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    total = int(pick["titles"])
    wrong = [str(n) for n in {total - 2, total - 1, total + 1, total + 2}
             if n >= 1 and n != total]
    rng.shuffle(wrong)
    return _question(
        f'How many drivers\' championships did {pick["driver_name"]} win?',
        str(total), wrong,
        f'{pick["driver_name"]} won {total}: {pick["years"]}.',
        "Records", rng)


def circuit_king(data, rng, era):
    circuits = _circuits_in(data, era)
    circuits = circuits[circuits["races"] >= 10]
    if circuits.empty:
        return None
    pick = circuits.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    here = data["wins"][data["wins"]["circuit"] == pick["circuit"]]
    counts = here.groupby("driver_name").size().sort_values(ascending=False)
    if len(counts) < 2 or counts.iloc[0] == counts.iloc[1]:
        return None
    others = counts.index[1:].tolist()
    rng.shuffle(others)
    return _question(
        f'Who has won the most races at {pick["circuit_name"]}?',
        counts.index[0], others,
        f'{counts.index[0]} has won there {counts.iloc[0]} times, from '
        f'{int(pick["races"])} Grands Prix held at the circuit.',
        "Circuits", rng)


def busiest_circuit(data, rng, era):
    circuits = _circuits_in(data, era).nlargest(25, "races")
    pool = circuits.sample(min(OPTIONS, len(circuits)), random_state=rng.randrange(10 ** 6))
    pool = pool.sort_values("races", ascending=False)
    if len(pool) < OPTIONS or pool.iloc[0]["races"] == pool.iloc[1]["races"]:
        return None
    best = pool.iloc[0]
    return _question(
        "Which of these circuits has held the most Grands Prix?",
        best["circuit_name"], pool.iloc[1:]["circuit_name"].tolist(),
        f'{best["circuit_name"]} has held {int(best["races"])}, against '
        f'{int(pool.iloc[1]["races"])} at {pool.iloc[1]["circuit_name"]}.',
        "Circuits", rng)


def first_win(data, rng, era):
    low, high = ERAS.get(era, ERAS["Mixed"])
    careers = _careers_in(data, era)
    careers = careers[careers["wins"] >= 5]
    if careers.empty:
        return None
    pick = careers.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    theirs = data["wins"][data["wins"]["driver"] == pick["driver"]]
    if theirs.empty:
        return None
    first = int(theirs["season"].min())
    if not low <= first <= high:
        return None
    raced = data["results"]
    seasons = sorted(raced[raced["driver"] == pick["driver"]]["season"].unique())
    wrong = [str(int(s)) for s in seasons if s != first]
    rng.shuffle(wrong)
    row = theirs[theirs["season"] == first].sort_values("round").iloc[0]
    return _question(
        f'In which season did {pick["driver_name"]} score a first Grand Prix win?',
        str(first), wrong,
        f'The first came at the {first} {row["race_name"]}, driving for '
        f'{row["constructor_name"]}.',
        "Careers", rng)


def which_team(data, rng, era):
    rows = _span(data, era)
    if rows.empty:
        return None
    pick = rows.sample(1, random_state=rng.randrange(10 ** 6)).iloc[0]
    season = int(pick["season"])
    here = rows[rows["season"] == season]
    if here["constructor_name"].nunique() < OPTIONS:
        return None
    others = [t for t in here["constructor_name"].unique()
              if t != pick["constructor_name"]]
    rng.shuffle(others)
    return _question(
        f'Which team did {pick["driver_name"]} drive for in {season}?',
        pick["constructor_name"], others,
        f'{pick["driver_name"]} raced for {pick["constructor_name"]} in {season}.',
        "Careers", rng)


BUILDERS = [race_winner, season_champion, team_champion, season_most_wins, wins_in_season,
            most_career_wins, how_many_titles, circuit_king, busiest_circuit, first_win,
            which_team]


def build(count=10, era="Mixed", seed=None):
    """A fresh quiz. Returns a list of questions, each with four options."""
    data = bundle()
    if data is None:
        return []
    rng = random.Random(seed)
    questions, seen, tries = [], set(), 0
    while len(questions) < count and tries < count * 40:
        tries += 1
        made = rng.choice(BUILDERS)(data, rng, era)
        if made and made["question"] not in seen:
            seen.add(made["question"])
            questions.append(made)
    return questions


if __name__ == "__main__":
    if not archive.available():
        print("Run python src/history_loader.py first.")
    else:
        for i, q in enumerate(build(8, seed=1), start=1):
            print(f"\n{i}. [{q['kind']}] {q['question']}")
            for option in q["options"]:
                mark = "*" if option == q["answer"] else " "
                print(f"   {mark} {option}")
            print(f"   -> {q['explain']}")
