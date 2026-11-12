"""One circuit's own page: what it is, who has won there, and the track itself in 3D.

It opens when a card is tapped on the Circuit Profiles page, so it is not in the menu.

The 3D shape comes from the same prepared race files the Circuit Explorer uses, which
OpenF1 only has from 2023 onwards. A circuit that has not held a race since then still
gets everything else, and a map pin instead of the track.
"""
import pandas as pd
import streamlit as st

import backdrop

from app_archive import get_circuit_history, get_circuit_index, get_circuit_winners
from cards import cards_css, crest, figures, glass, key_values, note
from style import team_info
from ui_kit import GOLD, kit_css, league, section, sheet


@st.cache_data(ttl=3600)
def latest_race_folder(circuit_id):
    """The newest prepared race folder for this circuit, or None if there isn't one.

    Folders are named "<season>_<round>", and the archive knows which circuit each
    season and round was held at, so the two line up without needing anything new.
    """
    from app_data import get_prepared_races
    from archive import race_list

    races = get_prepared_races()
    tracks = race_list()
    if races.empty or tracks.empty:
        return None
    here = tracks[tracks["circuit"] == circuit_id][["season", "round"]]
    if here.empty:
        return None
    wanted = set(zip(here["season"].astype(int), here["round"].astype(int)))
    matches = [r.folder for r in races.itertuples()
               if (int(r.season), int(r.round)) in wanted]
    return sorted(matches)[-1] if matches else None


@st.cache_data(ttl=3600)
def track_outline(circuit_id, colour):
    """The circuit's real shape as a faint line for behind the header.

    It is the same position data the 3D view uses, thinned down to a few hundred
    points, so Monza's page is backed by Monza's actual outline rather than clip art.
    Circuits with no race since 2023 have no position data and simply get the texture.
    """
    folder = latest_race_folder(circuit_id)
    if folder is None:
        return ""
    try:
        from app_data import get_race_file
        track = get_race_file(folder, "track")
    except Exception:
        return ""
    if track is None or track.empty or "x" not in track.columns:
        return ""
    return backdrop.track_trace(backdrop.thin(track["x"].tolist()),
                                backdrop.thin(track["y"].tolist()), colour)


def track_in_3d(circuit_id):
    """Draw the circuit in its real shape and elevation, if we have the lap data."""
    folder = latest_race_folder(circuit_id)
    if folder is None:
        return False
    try:
        from app_data import get_corners, get_race_file
        from track3d import circuit_view
        track = get_race_file(folder, "track")
    except Exception:
        return False
    if track is None or track.empty:
        return False

    section("The lap itself",
            "The real shape of the circuit, drawn from a car's own position data, with "
            "the hills exaggerated so you can see them. Drag to spin it, pinch or "
            "scroll to zoom.")
    show_corners = st.toggle("Show corner numbers", value=True, key=f"cp_corners_{circuit_id}")
    colour_by = st.radio("Colour the track by", ["Speed", "Gear"], horizontal=True,
                         key=f"cp_colour_{circuit_id}")
    labels = [{"text": "START / FINISH", "i": 0, "kind": "start"}]
    corners = []
    if show_corners:
        try:
            corners = get_corners(folder)
        except Exception:
            corners = []
        labels += [{"text": c["label"], "i": c["i"], "kind": "corner"} for c in corners]
    circuit_view(track, colour_by=colour_by.lower(),
                 dark=st.session_state.get("dark", True), labels=labels)

    length_km = (track[["x", "y"]].diff().pow(2).sum(axis=1) ** 0.5).sum() / 10_000
    climb_m = (track["z"].max() - track["z"].min()) / 10
    figures([(f"{length_km:.2f} km", "Lap length"),
             (f"{climb_m:.0f} m", "Height difference"),
             (f'{track["speed"].max():.0f} km/h', "Top speed"),
             (len(corners) or "—", "Corners"),
             (folder.replace("_", " round "), "Measured at")])
    note("Measured from the car's own data on its fastest lap of that race, so the "
         "length is a few metres off the official figure and the top speed is whatever "
         "that car reached, not the record.")
    if corners and corners[0].get("source") == "estimated":
        note("Corner numbers here are worked out from where the car slows down, so they "
             "may not match the official numbering.")
    return True


def show(circuit_id):
    """Draw the whole profile for one circuit."""
    cards_css()
    kit_css()
    index = get_circuit_index()
    row = index[index["circuit"] == circuit_id]
    if row.empty:
        st.warning("That circuit is not in the archive.")
        return
    row = row.iloc[0]
    by_driver, by_team = get_circuit_winners(circuit_id)
    history = get_circuit_history(circuit_id)

    span = (f'{int(row["first_season"])}' if row["first_season"] == row["last_season"]
            else f'{int(row["first_season"])}–{int(row["last_season"])}')
    pills = [p for p in (row["country"], row["locality"], f'{span}',
                         f'{int(row["races"])} Grands Prix') if p and str(p) != "nan"]
    most = (f'{by_driver.iloc[0]["driver_name"]} has won here '
            f'{int(by_driver.iloc[0]["wins"])} times.' if not by_driver.empty else "")
    crest("Circuit", row["circuit_name"],
          f'{int(row["races"])} rounds of the world championship have been held here, '
          f'{span}. {most}', pills, "#e10600",
          backdrop.build("#e10600", key=circuit_id,
                         trace=track_outline(circuit_id, "#e10600"),
                         dark=st.session_state.get("dark", True)))

    figures([(int(row["races"]), "Races held"),
             (int(row["first_season"]), "First"),
             (int(row["last_season"]), "Most recent"),
             (len(by_driver) if not by_driver.empty else 0, "Different winners"),
             (len(by_team) if not by_team.empty else 0, "Winning teams")])

    # ---------- the track ----------
    drawn = track_in_3d(circuit_id)

    # ---------- where it is ----------
    section("Where it is", "The pin marks the circuit, not the exact start line.")
    glass("", key_values([
        ("Circuit", row["circuit_name"]),
        ("Town", row["locality"]),
        ("Country", row["country"]),
        ("In the championship", span),
    ]))
    try:
        st.map(pd.DataFrame({"lat": [float(row["latitude"])],
                             "lon": [float(row["longitude"])]}), zoom=9)
    except (TypeError, ValueError):
        note("No coordinates for this circuit in the archive.")
    if not drawn:
        note("There is no 3D lap for this circuit: the position data behind it starts in "
             "2023, and no championship round has been held here since.")

    # ---------- who wins here ----------
    if not by_driver.empty:
        best = int(by_driver["wins"].max())
        section("Masters of this circuit",
                "Drivers with more than one win here. The bar is measured against the "
                "most anyone has managed.")
        rows = [{"name": r.driver_name, "sub": "", "colour": GOLD,
                 "bar": r.wins / best,
                 "figures": [(int(r.wins), "wins")]}
                for r in by_driver.head(10).itertuples()]
        league(rows)

    if not by_team.empty:
        best = int(by_team["wins"].max())
        section("Teams that own this place",
                "The same thing for constructors, in each team's own colour.")
        rows = [{"name": r.constructor_name, "sub": "",
                 "colour": team_info(r.constructor)[1], "bar": r.wins / best,
                 "figures": [(int(r.wins), "wins")]}
                for r in by_team.head(10).itertuples()]
        league(rows)

    # ---------- every winner ----------
    if not history.empty:
        section("Every winner here",
                "One row per Grand Prix, newest first.")
        rows = []
        for r in history.itertuples():
            colour = "#8a8a96"
            match = by_team[by_team["constructor_name"] == r.constructor_name] \
                if not by_team.empty else None
            if match is not None and not match.empty:
                colour = team_info(match.iloc[0]["constructor"])[1]
            rows.append([int(r.season), r.race_name, r.driver_name,
                         (colour, r.constructor_name), r.date])
        sheet([("Season", "num"), ("Race", "text"), ("Winner", "text"),
               ("Team", "tag"), ("Date", "text")], rows)
