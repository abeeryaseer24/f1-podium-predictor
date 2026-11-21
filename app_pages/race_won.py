"""Where the Race Was Won: the gap between two drivers, split into the start, pit stops,
safety cars and racing laps."""
import altair as alt
import pandas as pd
import streamlit as st

import race_story as R
from app_data import get_prepared_races
from charts import dress, theme
from style import stat_strip
from ui_kit import section, sheet

BUCKET_COLOURS = {"Start (lap 1)": "#2b6cff", "Pit stops": "#e8b33a", "Safety car laps": "#a3a3b2",
                  "Racing laps": "#e10600"}


@st.cache_data(ttl=600)
def race_data(folder):
    return R.load(folder)


@st.cache_data(ttl=600)
def field(folder):
    return R.field_breakdown(folder, race_data(folder))


@st.cache_data(ttl=600)
def grid_slots(folder):
    return R.grid_for(race_data(folder)[3], pd.read_csv(R.RESULTS_CSV))


@st.cache_data(ttl=600)
def pair(folder, a, b):
    return R.breakdown(folder, a, b, race_data(folder))


races = get_prepared_races()
if races.empty:
    st.info("No races prepared yet.")
    st.stop()
seasons = sorted(races["season"].unique().tolist(), reverse=True)
c1, c2 = st.columns(2)
season = c1.selectbox("Season", seasons)
in_season = races[races["season"] == season].sort_values("round")
names = {r.folder: f"Round {r.round} · {r.race_name}" for r in in_season.itertuples()}
folder = c2.selectbox("Race", list(names), index=len(names) - 1, format_func=names.get)

laps, pits, control, info = race_data(folder)
who = R.drivers(info)
order = R.finishing_order(laps)
grid = grid_slots(folder)


def label(n):
    return f"P{order.index(n) + 1} · {str(who.get(n, {}).get('name', n)).title()}"

c3, c4 = st.columns(2)
a = c3.selectbox("Driver", order, index=0, format_func=label, key=f"won_a_{folder}")
b = c4.selectbox("Against", [n for n in order if n != a], index=0, format_func=label, key=f"won_b_{folder}")

totals, per_lap = pair(folder, a, b)
if per_lap.empty:
    st.info("These two drivers have no laps in common.")
    st.stop()
code_a, code_b = who.get(a, {}).get("code", str(a)), who.get(b, {}).get("code", str(b))
colour_a = who.get(a, {}).get("colour") or "#e10600"
colour_b = who.get(b, {}).get("colour") or "#8a8a96"
final = per_lap["gap"].iloc[-1]
biggest = max(totals, key=lambda k: abs(totals[k]))
last_common = int(per_lap["lap"].iloc[-1])
done = R.completed_laps(laps)
lapped = done.get(a, 0) != done.get(b, 0)
stat_strip([
    ("Gap at the flag" if last_common >= int(info.get("laps", last_common)) and not lapped
     else f"Gap after lap {last_common}", f"{abs(final):.1f}s",
     f"{code_a if final > 0 else code_b} ahead" + (" (one car was lapped)" if lapped else
                                                   "" if last_common >= int(info.get("laps", last_common))
                                                   else " (the timing data stops here)"), True),
    ("Biggest single factor", biggest, f"{abs(totals[biggest]):.1f}s to {code_a if totals[biggest] > 0 else code_b}", False),
    ("Grid", f"{code_a} P{grid.get(a, '?')} · {code_b} P{grid.get(b, '?')}", "where they started", False),
])

# ---------- waterfall ----------
section(f"How {code_a}'s gap to {code_b} was built",
        f"Each bar is time {code_a} gained (up) or lost (down) against {code_b}. They add up exactly to the gap at the flag.")
steps, running = [], 0.0
for bucket in R.BUCKETS:
    value = totals[bucket]
    steps.append({"Part": bucket, "start": running, "end": running + value, "value": value})
    running += value
steps.append({"Part": "Gap at the flag", "start": 0.0, "end": running, "value": running})
wf = pd.DataFrame(steps)
wf["label"] = wf["value"].map(lambda v: f"{v:+.1f}s")
wf["colour"] = [BUCKET_COLOURS.get(p, colour_a if running >= 0 else colour_b) for p in wf["Part"]]
text, grid, muted = theme()
bars = alt.Chart(wf).mark_bar(size=46, cornerRadius=4).encode(
    x=alt.X("Part:N", sort=list(wf["Part"]), title=None, axis=alt.Axis(labelAngle=0, labelLimit=140)),
    y=alt.Y("start:Q", title=f"Seconds ({code_a} ahead is up)"), y2="end:Q",
    color=alt.Color("colour:N", scale=None),
    tooltip=["Part", alt.Tooltip("value:Q", format="+.2f", title="Seconds")])
labels = alt.Chart(wf).mark_text(dy=-8, fontWeight="bold", color=text).encode(
    x=alt.X("Part:N", sort=list(wf["Part"])), y=alt.Y("hi:Q"), text="label:N").transform_calculate(
    hi="max(datum.start, datum.end)")
zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=muted).encode(y="y:Q")
st.altair_chart(dress(bars + labels + zero).properties(height=320), use_container_width=True)

# ---------- gap through the race ----------
section("The gap, lap by lap", f"Above zero, {code_a} is ahead. The colour shows which part each lap counts towards.")
gap_chart = alt.Chart(per_lap).mark_line(color=muted, strokeWidth=1.5).encode(
    x=alt.X("lap:Q", title="Lap"), y=alt.Y("gap:Q", title=f"{code_a} ahead by (s)"))
dots = alt.Chart(per_lap).mark_circle(size=55).encode(
    x="lap:Q", y="gap:Q",
    color=alt.Color("bucket:N", scale=alt.Scale(domain=list(BUCKET_COLOURS), range=list(BUCKET_COLOURS.values())),
                    legend=alt.Legend(orient="top", title=None)),
    tooltip=[alt.Tooltip("lap:Q", title="Lap"), alt.Tooltip("gap:Q", format="+.2f", title="Gap (s)"),
             alt.Tooltip("change:Q", format="+.2f", title="Change this lap"), alt.Tooltip("bucket:N", title="Counts as")])
st.altair_chart(dress(gap_chart + dots + zero).properties(height=300), use_container_width=True)

# ---------- the whole field ----------
winner, table = field(folder)
if len(table):
    section("The whole field against the winner",
            f"Where every lead-lap finisher lost time to {who.get(winner, {}).get('code', winner)}. "
            "Negative means time lost, positive time gained.")
    rows = []
    for _, r in table.iterrows():
        d = who.get(int(r["driver_number"]), {})
        rows.append([f"P{int(r['position'])}", (d.get("colour") or "#8a8a96", d.get("code", "?")),
                     *[f"{round(-r[k], 1) + 0.0:+.1f}" for k in R.BUCKETS], f"{round(-r['total'], 1) + 0.0:+.1f}"])
    sheet([("", "text"), ("Driver", "tag"), *[(k, "num") for k in R.BUCKETS], ("Total (s)", "num")], rows)

with st.expander("How this is worked out"):
    st.markdown(f"""
The gap between two cars at the flag is the sum of how much it changed on every lap. Each
lap's change goes into one part:

- **Start (lap 1)**: the first lap, which includes where each car started on the grid.
- **Pit stops**: either driver's in-lap or out-lap. That covers the time in the pit lane, any
  penalty served at the stop, and the saving from stopping under a safety car.
- **Safety car laps**: any other lap run under a safety car, a virtual safety car or a red flag.
- **Racing laps**: every other lap. Pure pace, tyres, fuel, traffic and mistakes all land here.

The parts are built from the real lap times (OpenF1), so they add up exactly to the real gap.
Time penalties added after the race aren't in the lap times, so they aren't here either. A
lapped driver is compared only over the laps both cars completed.
""")
