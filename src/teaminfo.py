"""Who each team is: the facts no free API publishes, and the family tree that joins a
team to its earlier names (Force India to Racing Point to Aston Martin).

The facts live in data/teams.csv so they can be corrected without touching any code.
Colours and short names stay in style.py, which every other page already uses.
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TEAMS_CSV = ROOT / "data" / "teams.csv"
PHOTOS_DIR = ROOT / "data" / "team_photos"

# Earlier names of today's teams, oldest first. Only names that appear in our
# results (2016 onwards) matter here; the history pages add the older ones later.
LINEAGE = {
    "ferrari": ["ferrari"],
    "mercedes": ["mercedes"],
    "red_bull": ["red_bull"],
    "mclaren": ["mclaren"],
    "williams": ["williams"],
    "haas": ["haas"],
    "aston_martin": ["force_india", "racing_point", "aston_martin"],
    "rb": ["toro_rosso", "alphatauri", "rb"],
    "alpine": ["renault", "lotus_f1", "alpine"],
    "audi": ["sauber", "alfa", "audi"],
    "cadillac": ["cadillac"],
    "manor": ["manor", "marussia"],
}

# Which of today's teams an old name belongs to ("force_india" -> "aston_martin")
PARENT = {old: new for new, olds in LINEAGE.items() for old in olds}

# OpenF1 writes team names out in full; this turns them into our ids (used by pace.py)
OPENF1_TEAMS = {
    "mercedes": "mercedes",
    "ferrari": "ferrari",
    "scuderia ferrari": "ferrari",
    "red bull racing": "red_bull",
    "mclaren": "mclaren",
    "aston martin": "aston_martin",
    "alpine": "alpine",
    "bwt alpine": "alpine",
    "williams": "williams",
    "rb": "rb",
    "racing bulls": "rb",
    "visa cash app rb": "rb",
    "alphatauri": "rb",
    "haas f1 team": "haas",
    "haas": "haas",
    "kick sauber": "audi",
    "sauber": "audi",
    "alfa romeo": "audi",
    "audi": "audi",
    "cadillac": "cadillac",
}

# Shown when data/teams.csv has no row for a team
BLANK = {"name": "", "full_name": "", "founded": "", "entered_f1": "", "base": "",
         "country": "", "latitude": None, "longitude": None, "principal": "",
         "engine": "", "blurb": ""}


@lru_cache(maxsize=1)
def _read(modified_time):
    df = pd.read_csv(TEAMS_CSV)
    return df.set_index("team_id")


def team_meta_table():
    """Everything in data/teams.csv, one row per team, indexed by team id."""
    if not TEAMS_CSV.exists():
        return pd.DataFrame(columns=list(BLANK)).rename_axis("team_id")
    return _read(TEAMS_CSV.stat().st_mtime)


def team_meta(team_id):
    """The hand-kept facts for one team, as a plain dict. Missing values come back blank,
    so a page never breaks just because a row has not been filled in yet."""
    table = team_meta_table()
    out = dict(BLANK)
    if team_id in table.index:
        row = table.loc[team_id]
        for key in BLANK:
            value = row.get(key)
            out[key] = None if pd.isna(value) else value
    return out


def parent_team(constructor_id):
    """Today's name for an old constructor id. Unknown ids are left alone."""
    return PARENT.get(constructor_id, constructor_id)


def family(team_id):
    """Every constructor id this team has raced under, oldest first."""
    return LINEAGE.get(team_id, [team_id])


def openf1_team_id(name):
    """'Red Bull Racing' -> 'red_bull'. Returns None for a name we don't know."""
    if not isinstance(name, str):
        return None
    return OPENF1_TEAMS.get(name.strip().lower())


def photo_path(team_id):
    """The team's background photo, if the owner has added one to data/team_photos/."""
    for suffix in (".jpg", ".jpeg", ".png", ".webp"):
        path = PHOTOS_DIR / f"{team_id}{suffix}"
        if path.exists():
            return path
    return None


def photo_credits():
    """Who took each photo, from data/team_photos/credits.csv. Empty if there is no file."""
    path = PHOTOS_DIR / "credits.csv"
    if not path.exists():
        return pd.DataFrame(columns=["team_id", "credit", "licence", "source"])
    return pd.read_csv(path)
