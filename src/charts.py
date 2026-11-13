"""Chart building blocks shared by the Teams and Drivers pages.

Every chart is drawn in the real team colours and follows the app's dark or light
theme, so the pages look like one thing rather than a pile of default graphs.
"""
import altair as alt
import streamlit as st

from style import team_info

HEIGHT = 340


def theme():
    """Text and gridline colours for the theme the visitor is using."""
    dark = st.session_state.get("dark", True)
    return ("#f5f5f7", "#2c2c3a", "#a3a3b2") if dark else ("#15151e", "#d9d9d4", "#55556a")


def dress(chart, symbol="square"):
    """Give a chart the app's colours and strip the clutter Altair adds by default.

    `symbol` is the shape drawn beside each name in the legend, and the default is a
    square for every chart in the app on purpose. It used to be "stroke", a short
    line. A stroke symbol takes its colour from the mark's *stroke*, but a bar or a
    rectangle keeps its colour in its *fill* — so every bar chart in the app printed a
    legend of names with no colour at all beside them, and there was no way to tell
    which team was which. A square is drawn with both a fill and a thick outline, so
    it shows up whichever kind of mark the chart uses.
    """
    text, grid, muted = theme()
    if symbol == "stroke":
        legend = dict(symbolType="stroke", symbolStrokeWidth=4)
    else:
        legend = dict(symbolType="square", symbolSize=170, symbolStrokeWidth=3)
    return (chart.properties(height=HEIGHT)
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=muted, titleColor=muted, gridColor=grid,
                            domainColor=grid, tickColor=grid, labelFontSize=11,
                            titleFontSize=12)
            .configure_legend(labelColor=text, titleColor=muted, labelFontSize=12,
                              **legend)
            .configure_title(color=text))


def team_scale(team_ids):
    """An Altair colour scale that paints each team in its own colour."""
    names, colours = [], []
    for team_id in team_ids:
        name, colour = team_info(team_id)
        names.append(name)
        colours.append(colour)
    return alt.Scale(domain=names, range=colours)


# A spread of colours for teams from the past, which have no official colour of their own.
# They are picked in a fixed order, so the same team keeps the same colour every time.
ARCHIVE_COLOURS = [
    "#e10600", "#27f4d2", "#3671c6", "#ff8000", "#229971", "#ff87bc", "#64c4ff",
    "#b6babd", "#c9a227", "#9b5de5", "#f2c21b", "#4cc9a0", "#f4845f", "#7a8fa6",
]
KNOWN_BY_NAME = {
    "ferrari": "#e8002d", "mclaren": "#ff8000", "mercedes": "#27f4d2",
    "red bull": "#3671c6", "williams": "#64c4ff", "renault": "#f2c21b",
    "team lotus": "#00703c", "lotus": "#00703c", "brabham": "#1d4e89",
    "tyrrell": "#1f4ea1", "benetton": "#00a650", "brm": "#0b6623",
    "cooper": "#1e8a4c", "alpine": "#ff87bc", "aston martin": "#229971",
    "haas": "#b6babd", "audi": "#bb0a30", "sauber": "#52e252",
    "jordan": "#f2c21b", "brawn": "#b8fd6e", "matra": "#1f4ea1",
    "vanwall": "#0b6623", "maserati": "#c0392b", "alfa romeo": "#9b1b30",
}


def name_scale(names):
    """A colour scale for teams named in words (the History pages), using the real colour
    where we know it and a fixed spread of colours for the rest."""
    colours, spare = [], 0
    for name in names:
        key = str(name).lower()
        if key in KNOWN_BY_NAME:
            colours.append(KNOWN_BY_NAME[key])
        elif key == "everyone else":
            colours.append("#6b6b7a")
        else:
            colours.append(ARCHIVE_COLOURS[spare % len(ARCHIVE_COLOURS)])
            spare += 1
    return alt.Scale(domain=list(names), range=colours)


def with_team_names(table, column="constructor"):
    """Add a 'Team' column of readable names next to the team ids."""
    out = table.copy()
    out["Team"] = out[column].map(lambda t: team_info(t)[0])
    return out


# ---------- the charts ----------

def points_lines(progress, label="Points"):
    """Running championship points, one line per team, race by race."""
    data = with_team_names(progress)
    scale = team_scale(sorted(progress["constructor"].unique()))
    chart = (alt.Chart(data).mark_line(strokeWidth=3, interpolate="monotone")
             .encode(x=alt.X("round:Q", title="Round",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("cum_points:Q", title=label),
                     color=alt.Color("Team:N", scale=scale, title=None),
                     tooltip=["Team", alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip("cum_points:Q", title=label),
                              alt.Tooltip("position:Q", title="Place")]))
    return dress(chart)


def position_bumps(progress):
    """Championship place after every round. Lower on the chart is better."""
    data = with_team_names(progress)
    scale = team_scale(sorted(progress["constructor"].unique()))
    top = int(data["position"].max())
    base = alt.Chart(data).encode(
        x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1, format="d")),
        y=alt.Y("position:Q", title="Championship place",
                scale=alt.Scale(domain=[top + 0.5, 0.5]),
                axis=alt.Axis(tickMinStep=1, format="d")),
        color=alt.Color("Team:N", scale=scale, title=None),
        tooltip=["Team", alt.Tooltip("race_name:N", title="Race"),
                 alt.Tooltip("position:Q", title="Place"),
                 alt.Tooltip("cum_points:Q", title="Points")])
    return dress(base.mark_line(strokeWidth=3) + base.mark_circle(size=55))


def points_per_race(progress, row_field="Team", row_label="Driver"):
    """Points scored at each race: one small bar chart per team, or per driver.

    This was a single stacked bar chart and it was wrong. Stacking piles every team's
    score for a weekend into one bar, so the bar measured the *whole field's* haul —
    101 points at a normal Grand Prix, 137 when there is a sprint — and the chart
    appeared to show teams scoring 140 points in a race. No team can: the most on
    offer for one team is 43 at a normal weekend and 58 with a sprint. On top of that
    the legend was unreadable, because a bar's colour is its fill and the legend was
    drawing stroke symbols, so the names had no colour beside them at all.

    One row per team fixes both. Every row is drawn against the same scale, so bar
    heights can be compared straight down the column, and the name sits beside its own
    row, which means there is no legend to read.
    """
    text, grid, muted = theme()
    data = progress if "Team" in progress.columns else with_team_names(progress)
    data = data.copy()
    rows = (data.groupby(row_field, observed=True)["points"].sum()
            .sort_values(ascending=False))
    order = rows.index.tolist()
    ceiling = float(data["points"].max())
    if not ceiling > 0:                      # also catches an all-empty season (NaN)
        ceiling = 1.0
    scale = team_scale(sorted(data["constructor"].dropna().unique()))

    label = row_label if row_field != "Team" else "Team"
    panel = (alt.Chart(data).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
             .encode(x=alt.X("round:O", title="Round",
                             axis=alt.Axis(labelAngle=0, labelFontSize=9,
                                           labelOverlap=True)),
                     y=alt.Y("points:Q", title=None,
                             scale=alt.Scale(domain=[0, ceiling]),
                             axis=alt.Axis(values=[0, round(ceiling)], labelFontSize=9)),
                     color=alt.Color("Team:N", scale=scale, legend=None),
                     tooltip=[alt.Tooltip(f"{row_field}:N", title=label),
                              alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip("points:Q", title="Points that race")])
             .properties(width=alt.Step(16), height=34))

    chart = panel.facet(
        row=alt.Row(f"{row_field}:N", sort=order, title=None,
                    header=alt.Header(labelAngle=0, labelAlign="left",
                                      labelAnchor="middle", labelFontSize=11,
                                      labelColor=text, labelLimit=150)),
        spacing=3)
    return (chart.configure_view(strokeWidth=0)
            .configure_axis(labelColor=muted, titleColor=muted, gridColor=grid,
                            domainColor=grid, tickColor=grid, titleFontSize=12)
            .configure_title(color=text))


def gap_to_leader(progress):
    """How far each team is behind the championship leader after every round."""
    data = with_team_names(progress)
    scale = team_scale(sorted(progress["constructor"].unique()))
    chart = (alt.Chart(data).mark_line(strokeWidth=2.5, interpolate="monotone")
             .encode(x=alt.X("round:Q", title="Round",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("gap_to_leader:Q", title="Points behind the leader",
                             scale=alt.Scale(reverse=True)),
                     color=alt.Color("Team:N", scale=scale, title=None),
                     tooltip=["Team", alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip("gap_to_leader:Q", title="Behind by")]))
    return dress(chart)


def pace_lines(table, value="smoothed", label="Per cent off the fastest car"):
    """Car pace race by race. Lower is faster, so the axis runs the other way up."""
    data = with_team_names(table)
    scale = team_scale(sorted(table["constructor"].unique()))
    chart = (alt.Chart(data).mark_line(strokeWidth=3, interpolate="monotone", point=True)
             .encode(x=alt.X("round:Q", title="Round",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y(f"{value}:Q", title=label, scale=alt.Scale(reverse=True)),
                     color=alt.Color("Team:N", scale=scale, title=None),
                     tooltip=["Team", alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip(f"{value}:Q", title="Off the pace", format=".2f"),
                              alt.Tooltip("pct_off:Q", title="That race", format=".2f")]))
    return dress(chart)


def simple_bars(table, value, label, name_col="Team", colour_col="constructor",
                sort_ascending=False):
    """One bar per team, in team colours."""
    data = with_team_names(table, colour_col) if colour_col in table.columns else table.copy()
    order = data.sort_values(value, ascending=sort_ascending)[name_col].tolist()
    scale = team_scale(sorted(table[colour_col].unique())) if colour_col in table.columns else alt.Undefined
    chart = (alt.Chart(data).mark_bar(cornerRadiusEnd=4)
             .encode(x=alt.X(f"{value}:Q", title=label),
                     y=alt.Y(f"{name_col}:N", sort=order, title=None),
                     color=alt.Color(f"{name_col}:N", scale=scale, legend=None),
                     tooltip=[name_col, alt.Tooltip(f"{value}:Q", title=label)]))
    return dress(chart).properties(height=max(200, 28 * len(data)))


def cause_bars(causes):
    """Why cars stopped, stacked by reason, one bar per team."""
    data = with_team_names(causes)
    order = (data.groupby("Team")["count"].sum().sort_values(ascending=False).index.tolist())
    chart = (alt.Chart(data).mark_bar(cornerRadiusEnd=3)
             .encode(x=alt.X("count:Q", title="Cars that did not finish",
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     y=alt.Y("Team:N", sort=order, title=None),
                     color=alt.Color("cause:N", title="Reason",
                                     scale=alt.Scale(scheme="tableau10")),
                     tooltip=["Team", alt.Tooltip("cause:N", title="Reason"),
                              alt.Tooltip("count:Q", title="Cars")]))
    return dress(chart).properties(height=max(220, 30 * len(order)))


def season_line(history, value, label, colour):
    """One team or driver over the years, in their own colour."""
    chart = (alt.Chart(history).mark_line(strokeWidth=3, point=True, color=colour)
             .encode(x=alt.X("season:O", title=None),
                     y=alt.Y(f"{value}:Q", title=label),
                     tooltip=[alt.Tooltip("season:O", title="Season"),
                              alt.Tooltip(f"{value}:Q", title=label)]))
    return dress(chart).properties(height=260)


def season_positions(history, colour):
    """Championship place by season. Lower on the chart is better."""
    top = int(history["position"].max())
    chart = (alt.Chart(history).mark_line(strokeWidth=3, point=True, color=colour)
             .encode(x=alt.X("season:O", title=None),
                     y=alt.Y("position:Q", title="Championship place",
                             scale=alt.Scale(domain=[top + 0.5, 0.5]),
                             axis=alt.Axis(tickMinStep=1, format="d")),
                     tooltip=[alt.Tooltip("season:O", title="Season"),
                              alt.Tooltip("position:Q", title="Place"),
                              alt.Tooltip("points:Q", title="Points")]))
    return dress(chart).properties(height=260)
