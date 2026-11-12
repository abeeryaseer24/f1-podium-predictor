"""Upgrades: the step changes in car pace the lap times can see, next to the notes kept
by hand about what each team actually brought."""
import pandas as pd
import streamlit as st

from app_garage import default_season, get_seasons, get_team_pace, get_upgrades, pace_available
from cards import cards_css, note
from style import empty_note, stat_strip, team_info
from ui_kit import kit_css, league, section, sheet

JUMP = 0.25        # a gain this big (in per cent of lap time) counts as a step change
LOOKBACK = 3       # races averaged before and after the step

cards_css()
kit_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))

notes = get_upgrades()
notes = notes[notes["season"] == season] if not notes.empty else notes


def find_steps(pace):
    """Rounds where a team's pace improved by more than a quarter of a per cent against
    its own recent form. A jump is a hint that something new arrived, not proof."""
    rows = []
    for team, group in pace.sort_values("round").groupby("constructor"):
        values = group["pct_off"].tolist()
        rounds = group["round"].tolist()
        names = group["race_name"].tolist()
        for i in range(LOOKBACK, len(values)):
            before = sum(values[i - LOOKBACK:i]) / LOOKBACK
            after = sum(values[i:i + LOOKBACK]) / len(values[i:i + LOOKBACK])
            gain = before - after
            if gain >= JUMP:
                rows.append({"constructor": team, "round": rounds[i],
                             "race_name": names[i], "gain": round(gain, 2),
                             "before": round(before, 2), "after": round(after, 2)})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    # keep only the biggest jump in any run of three rounds, so one upgrade is not listed twice
    frame = frame.sort_values(["constructor", "round"])
    keep, last = [], {}
    for row in frame.itertuples():
        if row.constructor in last and row.round - last[row.constructor] < LOOKBACK:
            continue
        last[row.constructor] = row.round
        keep.append(row._asdict())
    return pd.DataFrame(keep).drop(columns=["Index"], errors="ignore")


steps = pd.DataFrame()
if pace_available():
    pace = get_team_pace(season, True)
    if not pace.empty:
        steps = find_steps(pace)

stat_strip([
    ("Steps the lap times show", str(len(steps)), "dry races only", True),
    ("Notes written by hand", str(len(notes)), f"in {season}", False),
    ("Biggest step",
     f'{steps["gain"].max():.2f}%' if not steps.empty else "—",
     team_info(steps.loc[steps["gain"].idxmax(), "constructor"])[0]
     if not steps.empty else "nothing found", False),
])

st.subheader("What this page can and cannot do")
note("Nobody publishes a free list of F1 upgrades, so there is no way to fetch them. "
     "What the lap times <i>can</i> show is a team suddenly going quicker than its own "
     "recent form. That is a strong hint an upgrade landed, but it could just as easily be "
     "a circuit that suits the car, a cooler weekend or a rival's bad race. The notes "
     "below are the only place the real answer lives, and they are written by hand.")

if steps.empty:
    if not pace_available():
        empty_note("The pace files have not been built yet, so no steps can be found.")
        note("Run <code>python src/pace.py</code> once to build them.")
    else:
        empty_note(f"No clear steps in car pace found in {season}.")
else:
    section("Where the car pace stepped up",
            "Every point in the season where a team's measured pace jumped, biggest "
            "step first. The bar is the size of the step.")
    steps = steps.sort_values("gain", ascending=False)
    biggest = max(float(steps["gain"].max()), 1e-9)
    league([{
        "pos": place, "name": team_info(row.constructor)[0],
        "colour": team_info(row.constructor)[1],
        "sub": f'from round {int(row.round)}, the {row.race_name} \u00b7 '
               f'{row.before:.2f}% off became {row.after:.2f}% off',
        "bar": float(row.gain) / biggest,
        "figures": [(f"{row.gain:.2f}%", "gained")],
    } for place, row in enumerate(steps.itertuples(), start=1)])

section("Upgrade notes",
        "What each team actually brought, written down by hand from the technical reports.")
if notes.empty:
    empty_note(f"Nothing has been written down for {season} yet.")
    note("Add a line to <code>data/upgrades.csv</code> for each package a team brings. "
         "The columns are "
         "<code>season, round, constructor, area, description, source</code>, where "
         "<code>area</code> is something like floor, front wing or sidepods, and "
         "<code>source</code> is where you read about it.")
else:
    show = notes.copy().sort_values("round", ascending=False)
    sheet([("Round", "num"), ("Team", "tag"), ("Area", "text"),
           ("What it was", "wrap"), ("Source", "text")],
          [[int(r.round), (team_info(r.constructor)[1], team_info(r.constructor)[0]),
            r.area, r.description, r.source] for r in show.itertuples()])
