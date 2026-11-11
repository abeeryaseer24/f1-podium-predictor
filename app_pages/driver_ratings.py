"""Driver Ratings: how each driver's form moved through the season, measured two ways.

One is raw lap time pace, which includes the car. The other compares a driver only with
their own teammate, which is the closest thing to a fair test of the driver alone.
"""
import altair as alt
import pandas as pd
import streamlit as st

from app_garage import default_season, get_driver_pace, get_seasons, pace_available
from cards import cards_css, note
from charts import dress, team_scale
from predictor import clean_name
from style import empty_note, stat_strip, team_info

cards_css()

seasons = get_seasons()
season = st.selectbox("Season", seasons, index=seasons.index(default_season()))

if not pace_available():
    empty_note("The pace files have not been built yet.")
    note("Run <code>python src/pace.py</code> once. It reads the race files already in "
         "<code>data/races/</code> and needs no downloading.")
    st.stop()

pace = get_driver_pace(season, True)
if pace.empty:
    empty_note(f"No lap data for {season}. Lap times only go back to 2023.")
    st.stop()

pace = pace.copy()
pace["Driver"] = pace["driver"].map(clean_name)
pace["Team"] = pace["team_id"].map(lambda t: team_info(t)[0] if isinstance(t, str) else "Unknown")

# ---------- the driver against their own teammate ----------

pairs = []
for (season_id, rnd), group in pace.groupby(["season", "round"]):
    for team, mates in group.groupby("team_id"):
        if len(mates) != 2:
            continue
        a, b = mates.iloc[0], mates.iloc[1]
        pairs.append({"round": rnd, "race_name": a["race_name"], "driver": a["driver"],
                      "team_id": team, "gap": round(a["pace"] / b["pace"] * 100 - 100, 3)})
        pairs.append({"round": rnd, "race_name": b["race_name"], "driver": b["driver"],
                      "team_id": team, "gap": round(b["pace"] / a["pace"] * 100 - 100, 3)})
mates_table = pd.DataFrame(pairs)

best_pace = pace.groupby("Driver", as_index=False)["pct_off"].mean().round(3).sort_values("pct_off")
stat_strip([
    ("Quickest on raw pace", best_pace.iloc[0]["Driver"],
     f'{best_pace.iloc[0]["pct_off"]:.2f}% off the fastest car', True),
    ("Races measured", str(pace["round"].nunique()), "dry races only", False),
    ("Drivers measured", str(pace["driver"].nunique()), f"in {season}", False),
])

note("Raw pace includes the car, so a driver in the quickest car will always look good. "
     "The teammate chart underneath takes the car out of it as far as anything can.")

# ---------- chart 1: raw pace ----------

st.subheader("Raw pace through the season")
note("Per cent off the fastest car of the weekend, smoothed over three races. "
     "Lower is faster. Two drivers in the same team share a colour.")
teams_present = sorted(pace["team_id"].dropna().unique())
scale = team_scale(teams_present)
base = alt.Chart(pace.dropna(subset=["team_id"])).encode(
    x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1, format="d")),
    color=alt.Color("Team:N", scale=scale, title=None),
    detail="Driver:N",
    tooltip=["Driver", "Team", alt.Tooltip("race_name:N", title="Race"),
             alt.Tooltip("smoothed:Q", title="Smoothed", format=".2f"),
             alt.Tooltip("pct_off:Q", title="That race", format=".2f")])
st.altair_chart(
    dress(base.mark_line(strokeWidth=3, interpolate="monotone")
          .encode(y=alt.Y("smoothed:Q", title="Per cent off the fastest car",
                          scale=alt.Scale(reverse=True)))),
    width="stretch", theme=None)

# ---------- chart 2: against the teammate ----------

if mates_table.empty:
    note("No race this season had both cars of a team with enough clean laps, so the "
         "teammate comparison cannot be drawn.")
else:
    mates_table["Driver"] = mates_table["driver"].map(clean_name)
    mates_table["Team"] = mates_table["team_id"].map(lambda t: team_info(t)[0])
    mates_table = mates_table.sort_values(["driver", "round"])
    mates_table["smoothed"] = (mates_table.groupby("driver")["gap"]
                               .transform(lambda s: s.rolling(3, min_periods=1).mean())
                               .round(3))

    st.subheader("Against their own teammate")
    note("How much slower or faster each driver's pace was than the other car in the same "
         "garage, as a percentage of lap time. Below zero means faster than the teammate. "
         "This is the fairest comparison there is, but it only says who was better in that "
         "garage, not who is better overall.")
    mate_base = alt.Chart(mates_table).encode(
        x=alt.X("round:Q", title="Round", axis=alt.Axis(tickMinStep=1, format="d")),
        color=alt.Color("Team:N", scale=team_scale(sorted(mates_table["team_id"].unique())),
                        title=None),
        detail="Driver:N",
        tooltip=["Driver", "Team", alt.Tooltip("race_name:N", title="Race"),
                 alt.Tooltip("gap:Q", title="Against teammate", format="+.2f")])
    st.altair_chart(
        dress(mate_base.mark_line(strokeWidth=3, interpolate="monotone")
              .encode(y=alt.Y("smoothed:Q", title="Per cent against the teammate",
                              scale=alt.Scale(reverse=True)))),
        width="stretch", theme=None)

    st.subheader("The season in one number each")
    season_gap = (mates_table.groupby(["Driver", "Team"], as_index=False)["gap"]
                  .mean().round(3).sort_values("gap"))
    bars = (alt.Chart(season_gap).mark_bar(cornerRadiusEnd=4)
            .encode(x=alt.X("gap:Q", title="Average per cent against the teammate"),
                    y=alt.Y("Driver:N", sort=season_gap["Driver"].tolist(), title=None),
                    color=alt.Color("Team:N",
                                    scale=team_scale(sorted(mates_table["team_id"].unique())),
                                    legend=None),
                    tooltip=["Driver", "Team",
                             alt.Tooltip("gap:Q", title="Average", format="+.2f")]))
    st.altair_chart(dress(bars).properties(height=max(240, 26 * len(season_gap))),
                    width="stretch", theme=None)

note("<b>Worth knowing.</b> With two cars per team and twenty-odd races, a single weekend "
     "tells you almost nothing, which is why everything here is smoothed. A crash, a "
     "damaged floor, a bad set of tyres or a long stint in traffic all move the number. "
     "The ratings describe what happened; they do not explain it.")
