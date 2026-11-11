"""One driver's own page, painted in their team's colour.

It opens when a card is tapped on the Driver Cards page, so it is not in the menu.
The History pages use the same five tabs for drivers of the past.
"""
import altair as alt
import streamlit as st

from app_garage import (get_driver_history, get_driver_pace, get_driver_races,
                        get_driver_teammates, get_driver_totals)
from cards import (accent, cards_css, crest, figures, glass, head_to_head, key_values,
                   note, team_theme, timeline)
from charts import dress, season_line, season_positions
from predictor import clean_name
from style import empty_note, team_info


def ordinal(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def season_story(row):
    """One line about a driver's season, written from the numbers."""
    bits = []
    if row["wins"]:
        bits.append(f'{int(row["wins"])} win{"s" if row["wins"] != 1 else ""}')
    if row["podiums"]:
        bits.append(f'{int(row["podiums"])} podium{"s" if row["podiums"] != 1 else ""}')
    if row["poles"]:
        bits.append(f'{int(row["poles"])} pole{"s" if row["poles"] != 1 else ""}')
    tail = ", ".join(bits) if bits else f'best finish P{int(row["best_finish"])}'
    team = team_info(row["constructor"])[0]
    place = "Champion" if row["position"] == 1 else f'{ordinal(row["position"])} overall'
    return f'{team} · {place} with {row["points"]:.0f} points, {tail}.'


def show(driver_id, season=None, team_id=None):
    """Draw the whole profile for one driver."""
    name = clean_name(driver_id)
    history = get_driver_history(driver_id)
    totals = get_driver_totals(driver_id)
    races = get_driver_races(driver_id)

    if not totals:
        empty_note(f"We have no races for {name}.")
        return

    if team_id is None:
        team_id = (history.iloc[-1]["constructor"] if not history.empty
                   else races.iloc[-1]["constructor"])
    team_name, colour = team_info(team_id)
    dark = st.session_state.get("dark", True)
    cards_css()
    team_theme(colour)

    seasons_text = (f'{totals["first_season"]}' if totals["first_season"] == totals["last_season"]
                    else f'{totals["first_season"]}–{totals["last_season"]}')
    pills = [team_name, f'{seasons_text} in our data',
             f'{totals["races"]} races', f'{len(totals["teams"])} teams']
    crest("Driver", name,
          f'{totals["wins"]} wins and {totals["podiums"]} podiums from '
          f'{totals["races"]} starts since {totals["first_season"]}.',
          pills, colour)

    figures([(totals["wins"], "Wins"), (totals["podiums"], "Podiums"),
             (totals["poles"], "Poles"), (f'{totals["points"]:.0f}', "Points"),
             (totals["dnfs"], "DNFs"), (f'P{totals["best_finish"]}', "Best finish")])

    tabs = st.tabs(["Overview", "Career", "Season by season", "Teammates", "Race craft"])

    # ---------- 1. overview ----------
    with tabs[0]:
        best_season = history.loc[history["points"].idxmax()] if not history.empty else None
        glass("At a glance", key_values([
            ("Current team", team_name),
            ("Seasons in our data", seasons_text),
            ("Races started", totals["races"]),
            ("Teams raced for", ", ".join(team_info(t)[0] for t in totals["teams"])),
            ("Best season",
             f'{int(best_season["season"])} · {best_season["points"]:.0f} points, '
             f'{ordinal(best_season["position"])}' if best_season is not None else ""),
            ("Win rate", f'{100 * totals["wins"] / totals["races"]:.1f}%'),
            ("Podium rate", f'{100 * totals["podiums"] / totals["races"]:.1f}%'),
            ("Finished", f'{100 * (1 - totals["dnfs"] / totals["races"]):.1f}% of starts'),
        ]))
        note("Everything on this page comes from the races in our data, which start in "
             "2016. A career that began before then is longer than the numbers here.")

    # ---------- 2. career ----------
    with tabs[1]:
        if history.empty:
            empty_note("No seasons to show.")
        else:
            st.subheader("Season by season, in words")
            timeline([(int(r["season"]), season_story(r))
                      for _, r in history.sort_values("season", ascending=False).iterrows()])

            firsts = []
            first_win = races[races["win"] == 1].head(1)
            first_podium = races[races["podium"] == 1].head(1)
            first_pole = races[races["pole"] == 1].head(1)
            debut = races.head(1)
            for label, frame in (("Debut", debut), ("First podium", first_podium),
                                 ("First pole", first_pole), ("First win", first_win)):
                if not frame.empty:
                    row = frame.iloc[0]
                    firsts.append((label, f'{int(row["season"])} {row["race_name"]} '
                                          f'({team_info(row["constructor"])[0]})'))
            if firsts:
                glass("Milestones", key_values(firsts))

    # ---------- 3. season by season ----------
    with tabs[2]:
        if history.empty:
            empty_note("No seasons to show.")
        else:
            st.subheader("Championship place by season")
            st.altair_chart(season_positions(history, accent(colour, dark)),
                            width="stretch", theme=None)
            st.subheader("Points by season")
            st.altair_chart(season_line(history, "points", "Points", accent(colour, dark)),
                            width="stretch", theme=None)
            st.dataframe(
                history[["season", "constructor", "position", "points", "wins",
                         "podiums", "poles", "races", "dnfs"]]
                .assign(constructor=history["constructor"].map(lambda t: team_info(t)[0]))
                .rename(columns={"season": "Season", "constructor": "Team",
                                 "position": "Place", "points": "Points", "wins": "Wins",
                                 "podiums": "Podiums", "poles": "Poles", "races": "Races",
                                 "dnfs": "DNFs"})
                .sort_values("Season", ascending=False),
                hide_index=True, width="stretch")

    # ---------- 4. teammates ----------
    with tabs[3]:
        mates = get_driver_teammates(driver_id)
        if mates.empty:
            empty_note("No teammates found in our data.")
        else:
            note("The fairest test there is: the same car, the same weekend. Only races "
                 "where both drivers took part are counted, and the race column only "
                 "counts races where both were classified at the end.")
            blocks = []
            left = accent(colour, dark)
            for m in mates.itertuples():
                mate = clean_name(m.teammate)
                blocks.append(head_to_head(
                    f"Qualifying against {mate}", f"{m.races_together} races · {m.seasons}",
                    name, mate, m.quali_me, m.quali_them, left, "#8a8a96"))
                blocks.append(head_to_head(
                    f"Finished ahead of {mate}", "both classified",
                    name, mate, m.race_me, m.race_them, left, "#8a8a96"))
                blocks.append(head_to_head(
                    f"Points against {mate}", "while they were teammates",
                    name, mate, int(m.points_me), int(m.points_them), left, "#8a8a96"))
            st.markdown(f'<div class="pp-h2h">{"".join(blocks)}</div>', unsafe_allow_html=True)

    # ---------- 5. race craft ----------
    with tabs[4]:
        if races.empty:
            empty_note("No races to show.")
        else:
            gained = (races["grid"] - races["finish_position"])
            glass("Starting and finishing", key_values([
                ("Average grid slot", f'{races["grid"].mean():.1f}'),
                ("Average finish", f'{races["finish_position"].mean():.1f}'),
                ("Places gained per race", f'{gained.mean():+.1f}'),
                ("Best recovery",
                 f'P{int(races.loc[gained.idxmax(), "grid"])} to '
                 f'P{int(races.loc[gained.idxmax(), "finish_position"])} at the '
                 f'{races.loc[gained.idxmax(), "race_name"]}'),
            ]))
            st.subheader("Where they started against where they finished")
            note("Each dot is one race. Below the line means places gained.")
            data = races.assign(Season=races["season"].astype(str))
            chart = (alt.Chart(data).mark_circle(size=70, opacity=.7, color=accent(colour, dark))
                     .encode(x=alt.X("grid:Q", title="Started"),
                             y=alt.Y("finish_position:Q", title="Finished",
                                     scale=alt.Scale(reverse=True)),
                             tooltip=["Season", alt.Tooltip("race_name:N", title="Race"),
                                      alt.Tooltip("grid:Q", title="Started"),
                                      alt.Tooltip("finish_position:Q", title="Finished")]))
            st.altair_chart(dress(chart), width="stretch", theme=None)

            if season is not None:
                pace = get_driver_pace(season, True)
                mine = pace[pace["driver"] == driver_id] if not pace.empty else pace
                if not mine.empty:
                    st.subheader(f"Lap time pace in {season}")
                    note("Per cent off the fastest car of the weekend, smoothed over three "
                         "races. Lower is faster. This includes the car, not just the driver.")
                    chart = (alt.Chart(mine).mark_line(strokeWidth=3, point=True,
                                                       color=accent(colour, dark))
                             .encode(x=alt.X("round:Q", title="Round",
                                             axis=alt.Axis(tickMinStep=1, format="d")),
                                     y=alt.Y("smoothed:Q", title="Per cent off the fastest car",
                                             scale=alt.Scale(reverse=True)),
                                     tooltip=[alt.Tooltip("race_name:N", title="Race"),
                                              alt.Tooltip("pct_off:Q", title="That race",
                                                          format=".2f")]))
                    st.altair_chart(dress(chart), width="stretch", theme=None)
