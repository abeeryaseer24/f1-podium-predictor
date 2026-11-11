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


def dress(chart):
    """Give a chart the app's colours and strip the clutter Altair adds by default."""
    text, grid, muted = theme()
    return (chart.properties(height=HEIGHT)
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=muted, titleColor=muted, gridColor=grid,
                            domainColor=grid, tickColor=grid, labelFontSize=11,
                            titleFontSize=12)
            .configure_legend(labelColor=text, titleColor=muted, labelFontSize=12,
                              symbolType="stroke", symbolStrokeWidth=4)
            .configure_title(color=text))


def team_scale(team_ids):
    """An Altair colour scale that paints each team in its own colour."""
    names, colours = [], []
    for team_id in team_ids:
        name, colour = team_info(team_id)
        names.append(name)
        colours.append(colour)
    return alt.Scale(domain=names, range=colours)


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


def points_per_race(progress):
    """How many points each team scored at each race, as stacked bars."""
    data = with_team_names(progress)
    scale = team_scale(sorted(progress["constructor"].unique()))
    chart = (alt.Chart(data[data["points"] > 0]).mark_bar()
             .encode(x=alt.X("round:O", title="Round"),
                     y=alt.Y("points:Q", title="Points that race"),
                     color=alt.Color("Team:N", scale=scale, title=None),
                     tooltip=["Team", alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip("points:Q", title="Points")]))
    return dress(chart)


def points_heatmap(progress):
    """A grid of teams against races, shaded by how many points were scored."""
    data = with_team_names(progress)
    order = (data.groupby("Team")["points"].sum().sort_values(ascending=False).index.tolist())
    chart = (alt.Chart(data).mark_rect(stroke=None)
             .encode(x=alt.X("round:O", title="Round"),
                     y=alt.Y("Team:N", sort=order, title=None),
                     color=alt.Color("points:Q", title="Points",
                                     scale=alt.Scale(scheme="reds")),
                     tooltip=["Team", alt.Tooltip("race_name:N", title="Race"),
                              alt.Tooltip("points:Q", title="Points")]))
    return dress(chart).properties(height=max(220, 26 * len(order)))


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
