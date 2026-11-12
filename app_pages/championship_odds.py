"""Championship Odds: the rest of the season replayed thousands of times, to see who
still wins the drivers' and constructors' titles.

Two different questions get answered here and they are kept apart on purpose. The
simulation says how *likely* each outcome is. The arithmetic says what is still
*possible*, and that one is never wrong: if the points still on offer are smaller than
the gap, the championship is over whatever any model thinks.
"""
import altair as alt
import streamlit as st

from app_garage import default_season, get_championship_odds, get_seasons
from cards import cards_css, note
from charts import dress, team_scale
from predictor import clean_name
from style import empty_note, stat_strip, team_info
from ui_kit import GOLD, banner, chip, kit_css, league, section

cards_css()
kit_css()

seasons = get_seasons()
if not seasons:
    empty_note("No results have been downloaded yet.")
    st.stop()

season = default_season()
result = get_championship_odds(season)

if result.get("finished"):
    empty_note(f"The {season} season is over, so there is nothing left to simulate.")
    note("Open <b>Season Rewind</b> or <b>Driver Standings</b> to see how it finished.")
    st.stop()

if "error" in result:
    empty_note(f"The odds cannot be worked out right now: {result['error']}")
    note("This page needs the season calendar and the next race's grid, both of which "
         "come from the internet. Try again in a few minutes.")
    st.stop()

drivers = result["drivers"]
teams = result["teams"]
driver_state = result["driver_state"]
team_state = result["team_state"]
leader = driver_state["leader"]
team_leader = team_state["leader"]


def name_of(driver_id):
    return clean_name(driver_id)


# ---------- is it still a championship at all? ----------

races_left = result["races_left"]
sprints_left = result["sprints_left"]
left_text = (f'{races_left} race{"s" if races_left != 1 else ""} left'
             + (f' and {sprints_left} sprint{"s" if sprints_left != 1 else ""}'
                if sprints_left else ""))

if driver_state["settled"]:
    runner_up = driver_state["runner_up"]
    banner("🏆", f'{name_of(leader["driver"])} is the {season} world champion',
           f'With {left_text}, {int(driver_state["on_offer"])} points are still on offer '
           f'and {name_of(runner_up["driver"])} is {driver_state["gap_to_second"]:.0f} '
           f'behind. Nobody can catch {name_of(leader["driver"])} now, so the title is '
           f'settled whatever happens next.', GOLD)
else:
    chasers = driver_state["chasers"]
    who = ", ".join(name_of(d) for d in chasers["driver"].head(4))
    if len(chasers) > 4:
        who += f" and {len(chasers) - 4} others"
    banner("🔥", f'The drivers\' title is still open',
           f'{name_of(leader["driver"])} leads, but {len(chasers)} '
           f'driver{"s" if len(chasers) != 1 else ""} can still catch '
           f'{"them" if len(chasers) != 1 else "them"}: {who}. There are '
           f'{int(driver_state["on_offer"])} points left with {left_text}.')

stat_strip([
    ("Leads the drivers", name_of(leader["driver"]),
     f'{leader["points_now"]:.0f} points · '
     + ("champion already" if driver_state["settled"]
        else f'{driver_state["gap_to_second"]:.0f} clear'), True),
    ("Leads the teams", team_info(team_leader["constructor"])[0],
     f'{team_leader["points_now"]:.0f} points · '
     + ("title already won" if team_state["settled"]
        else f'{team_state["gap_to_second"]:.0f} clear'), False),
    ("Still to run", str(races_left),
     f'{sprints_left} sprint{"s" if sprints_left != 1 else ""}', False),
    ("Can still win the drivers' title", str(driver_state["alive"]),
     f'{int(driver_state["on_offer"])} points a driver could still score', False),
])

grid_note = ("the real starting grid for the next race"
             if result["grid_source"] != "estimated"
             else "an estimated grid, because qualifying has not happened yet")
note(f'The rest of the season was replayed <b>{result["simulations"]:,}</b> times, '
     f'starting from the {result["next_race"]} and using {grid_note}. The count above '
     f'includes the leader, so <b>1</b> means the championship is already decided.')

# ---------- drivers ----------

section("Who can still win the drivers' title",
        "Pure arithmetic, not the model: a driver is listed here whenever the points "
        "still available are more than the gap to the leader. The bar is how much of "
        "the leader's total they already have.")

top_points = max(float(drivers["points_now"].max()), 1.0)
rows = []
for place, row in enumerate(drivers.sort_values("points_now", ascending=False)
                            .itertuples(), start=1):
    if not row.alive and place > 1:
        continue
    behind = float(leader["points_now"]) - float(row.points_now)
    needs = (chip("champion", GOLD, solid=True) if driver_state["settled"] and place == 1
             else chip("leader", GOLD) if place == 1 else "")
    rows.append({
        "pos": place, "name": name_of(row.driver),
        "colour": team_info(row.constructor)[1], "tag": needs,
        "sub": (f'{team_info(row.constructor)[0]} · '
                + ("leads" if place == 1 else f'{behind:.0f} behind')),
        "bar": float(row.points_now) / top_points,
        "figures": [(f"{row.points_now:.0f}", "points"),
                    (f"{row.title_chance:.0f}%", "title chance"),
                    (f"{row.expected_points:.0f}", "expected")],
    })
if len(rows) == 1:
    note("Only the champion is left, so there is nothing to list against them.")
league(rows)

section("How often each driver won the simulated season",
        "The same seasons replayed thousands of times. This is a likelihood, not a "
        "certainty: it assumes the rest of the year looks like the next race.")
data = drivers[drivers["title_chance"] > 0.05].copy()
if data.empty:
    data = drivers.head(5).copy()
data["Driver"] = data["driver"].map(clean_name)
data["Team"] = data["constructor"].map(lambda t: team_info(t)[0])
scale = team_scale(sorted(data["constructor"].unique()))
chart = (alt.Chart(data).mark_bar(cornerRadiusEnd=4)
         .encode(x=alt.X("title_chance:Q", title="Chance of the title (%)"),
                 y=alt.Y("Driver:N", sort=data["Driver"].tolist(), title=None),
                 color=alt.Color("Team:N", scale=scale, legend=None),
                 tooltip=["Driver", "Team",
                          alt.Tooltip("title_chance:Q", title="Title chance %", format=".1f"),
                          alt.Tooltip("points_now:Q", title="Points now"),
                          alt.Tooltip("expected_points:Q", title="Expected final points")]))
st.altair_chart(dress(chart).properties(height=max(200, 30 * len(data))),
                width="stretch", theme=None)

section("Where everyone is expected to finish",
        "The whole field, in the order the simulations put them at the end of the "
        "season. The range is where they landed in the middle of those runs.")
league([{
    "pos": place,
    "name": name_of(row.driver),
    "colour": team_info(row.constructor)[1],
    "tag": "" if row.alive else chip("out of reach", "#8a8a96"),
    "sub": f'{team_info(row.constructor)[0]} · likely '
           f'{int(row.low_points)}–{int(row.high_points)} points by the end',
    "bar": float(row.expected_points) / max(float(drivers["expected_points"].max()), 1.0),
    "figures": [(f"{row.points_now:.0f}", "now"),
                (f"{row.expected_points:.0f}", "expected"),
                (f"{row.top3_chance:.0f}%", "top three")],
} for place, row in enumerate(drivers.itertuples(), start=1)])

# ---------- constructors ----------

if team_state["settled"]:
    banner("🏆", f'{team_info(team_leader["constructor"])[0]} have won the '
                 f'{season} constructors\' championship',
           f'A team scores with both cars, so the most one could still take from '
           f'{left_text} is {int(team_state["on_offer"])} points. The gap behind is '
           f'{team_state["gap_to_second"]:.0f}, so it cannot be closed.',
           team_info(team_leader["constructor"])[1])
else:
    section("The constructors' title", "")

section("Who can still win the constructors' title",
        "A team's best possible weekend is a one-two, which is 43 points and not 25, "
        "so teams stay in the fight longer than drivers do.")
top_team_points = max(float(teams["points_now"].max()), 1.0)
league([{
    "pos": place, "name": team_info(row.constructor)[0],
    "colour": team_info(row.constructor)[1],
    "tag": (chip("champion", GOLD, solid=True)
            if team_state["settled"] and place == 1 else
            chip("leader", GOLD) if place == 1 else
            "" if row.alive else chip("out of reach", "#8a8a96")),
    "sub": ("leads" if place == 1 else
            f'{float(team_leader["points_now"]) - float(row.points_now):.0f} behind'),
    "bar": float(row.points_now) / top_team_points,
    "figures": [(f"{row.points_now:.0f}", "points"),
                (f"{row.title_chance:.0f}%", "title chance"),
                (f'{int(row.low_points)}–{int(row.high_points)}', "likely final")],
} for place, row in enumerate(teams.sort_values("points_now", ascending=False)
                              .itertuples(), start=1)])

# ---------- how it works ----------

section("How these numbers are made",
        "Worth reading once, so you know which of the two numbers to trust.")
note("Every remaining race is drawn from the same model that makes our podium predictions: "
     "each driver has a strength, and the finishing order is drawn from those strengths with "
     "the right amount of luck mixed in. Drivers retire at roughly the rate they have this "
     "season. Points are awarded the normal way, sprints included, and the season is run "
     f'{result["simulations"]:,} times. The percentage is simply how often each driver or '
     "team came out on top.")
note("<b>What it cannot know.</b> It assumes the rest of the season looks like the next "
     "race, so an upgrade that has not landed yet, a wet weekend, a driver swap or a "
     "penalty are all missing. <b>Who can still win</b> is different: that is pure "
     "arithmetic, comparing the gap with the points still available, and it is always "
     "right even when the simulated chance rounds to zero.")
