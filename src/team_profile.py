"""One team's own page, painted in the team's colour.

It opens when a card is tapped on the Team Cards page, so it is not in the menu.
Five tabs: who they are, what they have won, every driver, season by season, and where
they are based.
"""
import pandas as pd
import streamlit as st

from app_garage import (get_constructor_progress, get_constructor_table, get_entries,
                        get_team_drivers, get_team_history, get_teammate_battles)
from cards import (accent, cards_css, crest, figures, glass, head_to_head, key_values,
                   note, ordinal, photo_url, team_theme, timeline)
from charts import season_line, season_positions
from predictor import clean_name
from style import empty_note, team_info
from teaminfo import family, photo_credits, team_meta



def season_story(row):
    """One line about a season, written from the numbers."""
    place = ordinal(row["position"])
    bits = []
    if row["wins"]:
        bits.append(f'{int(row["wins"])} win{"s" if row["wins"] != 1 else ""}')
    if row["podiums"]:
        bits.append(f'{int(row["podiums"])} podium{"s" if row["podiums"] != 1 else ""}')
    if row["poles"]:
        bits.append(f'{int(row["poles"])} pole{"s" if row["poles"] != 1 else ""}')
    tail = ", ".join(bits) if bits else "no podiums"
    if row["position"] == 1:
        return f'Constructors\' champions with {row["points"]:.0f} points, {tail}.'
    return (f'Finished {place} of {int(row["teams_that_season"])} with '
            f'{row["points"]:.0f} points, {tail}.')


def show(team_id, season):
    """Draw the whole profile for one team."""
    name, colour = team_info(team_id)
    meta = team_meta(team_id)
    dark = st.session_state.get("dark", True)
    cards_css()
    shot = team_theme(colour, photo_url(team_id))

    fam = family(team_id)
    history = get_team_history(team_id, tuple(fam))
    drivers = get_team_drivers(tuple(fam))
    table = get_constructor_table(season)
    this_season = table[table["constructor"] == team_id]

    line_up = get_entries(season)
    line_up = line_up[line_up["constructor"] == team_id]
    names = [clean_name(d) for d in line_up["driver"]]

    pills = [meta["engine"] and f'Engine: {meta["engine"]}',
             meta["base"] and f'Based in {meta["base"]}',
             meta["principal"] and f'Run by {meta["principal"]}',
             not this_season.empty and
             f'{ordinal(this_season.iloc[0]["position"])} in {season}']
    crest(f"{season} season" if not this_season.empty else "Team profile",
          name, meta["blurb"], pills, colour, shot)

    if not this_season.empty:
        row = this_season.iloc[0]
        figures([(f'{row["points"]:.0f}', f"{season} points"),
                 (int(row["wins"]), "Wins"),
                 (int(row["podiums"]), "Podiums"),
                 (int(row["poles"]), "Poles"),
                 (int(row["dnfs"]), "DNFs"),
                 (ordinal(row["position"]), "Championship")])

    tabs = st.tabs(["Overview", "Achievements", "Drivers", "Season by season", "Facilities"])

    # ---------- 1. overview ----------
    with tabs[0]:
        glass("The facts", key_values([
            ("Founded", meta["founded"]),
            ("First F1 season", meta["entered_f1"]),
            ("Full entry name", meta["full_name"]),
            ("Base", f'{meta["base"]}, {meta["country"]}' if meta["base"] else ""),
            ("Team principal", meta["principal"]),
            ("Power unit", meta["engine"]),
            ("Raced as", ", ".join(team_info(f)[0] for f in fam)),
        ]))

        if names:
            glass(f"{season} drivers", key_values(
                [(n, f'{int(r)} race{"s" if r != 1 else ""} this season')
                 for n, r in zip(names, line_up["races"])]))

        if not drivers.empty:
            best = drivers.head(5)
            rows = []
            for d in best.itertuples():
                years = (f"{int(d.first_season)}" if d.first_season == d.last_season
                         else f"{int(d.first_season)}–{int(d.last_season)}")
                bits = [f"{int(d.races)} races"]
                if d.wins:
                    bits.append(f"{int(d.wins)} wins")
                if d.podiums:
                    bits.append(f"{int(d.podiums)} podiums")
                rows.append((clean_name(d.driver), f'{years} · {", ".join(bits)}'))
            glass("Drivers who did the most here", key_values(rows))
            note("Only the seasons in our data (2016 onwards) are counted, so a long career "
                 "before that is not included.")

        if not history.empty:
            totals = history[["wins", "podiums", "poles", "points"]].sum()
            titles = int((history["position"] == 1).sum())
            figures([(titles, "Titles since 2016"),
                     (int(totals["wins"]), "Race wins"),
                     (int(totals["podiums"]), "Podiums"),
                     (int(totals["poles"]), "Poles"),
                     (f'{totals["points"]:.0f}', "Points"),
                     (len(history), "Seasons")])

    # ---------- 2. achievements ----------
    with tabs[1]:
        if history.empty:
            empty_note("No seasons for this team in our data yet.")
        else:
            st.subheader("Season by season, in words")
            note("Written from the results themselves. Our data starts in 2016, so anything "
                 "older is not listed here.")
            timeline([(int(r["season"]), season_story(r))
                      for _, r in history.sort_values("season", ascending=False).iterrows()])

            best = history.loc[history["points"].idxmax()]
            most_wins = history.loc[history["wins"].idxmax()]
            glass("Records in our data", key_values([
                ("Best season by points", f'{int(best["season"])} · {best["points"]:.0f} points'),
                ("Most wins in a season",
                 f'{int(most_wins["season"])} · {int(most_wins["wins"])} wins'),
                ("Best championship finish",
                 f'{ordinal(history["position"].min())} '
                 f'({int(history.loc[history["position"].idxmin(), "season"])})'),
                ("Seasons raced", f'{int(history["season"].min())} to {int(history["season"].max())}'),
            ]))

    # ---------- 3. drivers ----------
    with tabs[2]:
        if drivers.empty:
            empty_note("No drivers for this team in our data.")
        else:
            st.subheader("Everyone who has raced for this team")
            show_me = drivers.copy()
            show_me["Driver"] = show_me["driver"].map(clean_name)
            show_me["Seasons"] = [
                f"{int(a)}" if a == b else f"{int(a)}–{int(b)}"
                for a, b in zip(show_me["first_season"], show_me["last_season"])]
            st.dataframe(
                show_me[["Driver", "Seasons", "races", "wins", "podiums", "poles",
                         "points", "best_finish"]]
                .rename(columns={"races": "Races", "wins": "Wins", "podiums": "Podiums",
                                 "poles": "Poles", "points": "Points",
                                 "best_finish": "Best finish"}),
                hide_index=True, width="stretch")

            battles = get_teammate_battles(season)
            mine = battles[battles["constructor"] == team_id] if not battles.empty else battles
            if not mine.empty:
                st.subheader(f"Inside the garage in {season}")
                blocks = []
                for b in mine.itertuples():
                    a_name, b_name = clean_name(b.driver_a), clean_name(b.driver_b)
                    left = accent(colour, dark)
                    right = "#8a8a96"
                    blocks.append(head_to_head(
                        "Qualifying", f"{b.races_together} races together",
                        a_name, b_name, b.quali_a, b.quali_b, left, right))
                    blocks.append(head_to_head(
                        "Finished ahead", "both cars classified",
                        a_name, b_name, b.race_a, b.race_b, left, right))
                    blocks.append(head_to_head(
                        "Points", "this season so far",
                        a_name, b_name, int(b.points_a), int(b.points_b), left, right))
                st.markdown(f'<div class="pp-h2h">{"".join(blocks)}</div>',
                            unsafe_allow_html=True)

    # ---------- 4. season by season ----------
    with tabs[3]:
        if history.empty:
            empty_note("No seasons for this team in our data yet.")
        else:
            st.subheader("Championship place by season")
            st.altair_chart(season_positions(history, accent(colour, dark)),
                            width="stretch", theme=None)
            st.subheader("Points by season")
            note("Points are not comparable across the years: the scoring system and the "
                 "number of races have both changed.")
            st.altair_chart(season_line(history, "points", "Points", accent(colour, dark)),
                            width="stretch", theme=None)
            st.subheader("Wins and podiums by season")
            st.altair_chart(season_line(history, "podiums", "Podiums", accent(colour, dark)),
                            width="stretch", theme=None)

            progress = get_constructor_progress(season)
            mine = progress[progress["constructor"] == team_id]
            if not mine.empty:
                st.subheader(f"{season}, race by race")
                st.dataframe(
                    mine[["round", "race_name", "points", "cum_points", "position"]]
                    .rename(columns={"round": "Round", "race_name": "Race",
                                     "points": "Points", "cum_points": "Running total",
                                     "position": "Place"}),
                    hide_index=True, width="stretch")

    # ---------- 5. facilities ----------
    with tabs[4]:
        glass("Where the cars are built", key_values([
            ("Factory", meta["base"]),
            ("Country", meta["country"]),
            ("Founded", meta["founded"]),
            ("First F1 season", meta["entered_f1"]),
        ]))
        if meta["latitude"] and meta["longitude"]:
            st.map(pd.DataFrame({"lat": [float(meta["latitude"])],
                                 "lon": [float(meta["longitude"])]}), zoom=5)
            note("The pin marks the town, not the exact building.")
        else:
            note("No location has been filled in for this team in data/teams.csv yet.")

        credits = photo_credits()
        mine = credits[credits["team_id"] == team_id] if not credits.empty else credits
        if not mine.empty:
            row = mine.iloc[0]
            note(f'Photo: {row.get("credit", "")} · {row.get("licence", "")} · '
                 f'{row.get("source", "")}')
