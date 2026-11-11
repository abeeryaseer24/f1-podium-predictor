"""The telemetry charts under the Ghost Lap Duel: where the time went, and what the two
drivers were doing with the car to make it happen.

The numbers are already worked out by duel.py, which returns both laps as traces of
speed, throttle, brake and gear against how far round the lap the car is. Nothing here
fetches anything; it only draws.
"""
import altair as alt
import pandas as pd

from charts import dress

POINTS = 400          # how many points of each trace to draw; more is slower, not clearer


def thin(trace, columns):
    """Cut a trace down to a readable number of points."""
    keep = [c for c in columns if c in trace.columns]
    step = max(1, len(trace) // POINTS)
    return trace.iloc[::step][["frac"] + keep].copy()


def both(duel, code_a, code_b, columns):
    """The two traces stacked into one long table, ready for Altair."""
    frames = []
    for trace, code in ((duel["trace_a"], code_a), (duel["trace_b"], code_b)):
        part = thin(trace, columns)
        part["driver"] = code
        frames.append(part)
    return pd.concat(frames, ignore_index=True)


def corner_rules(duel, height=None):
    """Thin vertical lines where the corners are, with their names along the top."""
    corners = duel.get("corners") or []
    if not corners:
        return None
    table = pd.DataFrame([{"name": str(name), "frac": float(frac)}
                          for name, frac in corners])
    rules = (alt.Chart(table).mark_rule(color="#8a8a96", opacity=.35, strokeDash=[3, 3])
             .encode(x=alt.X("frac:Q"),
                     tooltip=[alt.Tooltip("name:N", title="Corner")]))
    return rules


def axis(title):
    return alt.X("frac:Q", title=title, axis=alt.Axis(format="%"),
                 scale=alt.Scale(domain=[0, 1], nice=False))


def delta_chart(duel, code_a, code_b, colour_a, colour_b):
    """How the gap between the two laps builds up round the lap. Above the line means
    the first driver is losing time."""
    table = pd.DataFrame({"frac": duel["grid"], "delta": duel["delta"]})
    area = (alt.Chart(table).mark_area(opacity=.25, color="#e10600")
            .encode(x=axis("Round the lap"),
                    y=alt.Y("delta:Q", title=f"{code_a} behind {code_b} (seconds)")))
    line = (alt.Chart(table).mark_line(strokeWidth=2.5, color="#e10600")
            .encode(x=axis("Round the lap"), y=alt.Y("delta:Q"),
                    tooltip=[alt.Tooltip("frac:Q", title="Round the lap", format=".0%"),
                             alt.Tooltip("delta:Q", title="Gap", format="+.3f")]))
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#8a8a96").encode(y="y:Q")
    layers = [area, line, zero]
    rules = corner_rules(duel)
    if rules is not None:
        layers.insert(0, rules)
    return dress(alt.layer(*layers)).properties(height=260)


def speed_chart(duel, code_a, code_b, colour_a, colour_b):
    """Both drivers' speed all the way round the lap."""
    data = both(duel, code_a, code_b, ["speed"])
    scale = alt.Scale(domain=[code_a, code_b], range=[colour_a, colour_b])
    line = (alt.Chart(data).mark_line(strokeWidth=2)
            .encode(x=axis("Round the lap"),
                    y=alt.Y("speed:Q", title="Speed (km/h)", scale=alt.Scale(zero=False)),
                    color=alt.Color("driver:N", scale=scale, title=None),
                    tooltip=[alt.Tooltip("driver:N", title="Driver"),
                             alt.Tooltip("speed:Q", title="km/h"),
                             alt.Tooltip("frac:Q", title="Round the lap", format=".0%")]))
    rules = corner_rules(duel)
    chart = alt.layer(rules, line) if rules is not None else line
    return dress(chart).properties(height=300)


def pedals_chart(duel, code_a, code_b, colour_a, colour_b):
    """Throttle and braking. Throttle is a percentage; brake is on or off."""
    data = both(duel, code_a, code_b, ["throttle", "brake"])
    scale = alt.Scale(domain=[code_a, code_b], range=[colour_a, colour_b])
    throttle = (alt.Chart(data).mark_line(strokeWidth=1.8)
                .encode(x=axis("Round the lap"),
                        y=alt.Y("throttle:Q", title="Throttle (%)",
                                scale=alt.Scale(domain=[0, 100])),
                        color=alt.Color("driver:N", scale=scale, title=None),
                        tooltip=[alt.Tooltip("driver:N", title="Driver"),
                                 alt.Tooltip("throttle:Q", title="Throttle %")]))
    braking = data[data["brake"] > 0] if "brake" in data.columns else data.iloc[0:0]
    if braking.empty:
        return dress(throttle).properties(height=260)
    marks = (alt.Chart(braking).mark_tick(thickness=2, size=14, opacity=.7)
             .encode(x=axis("Round the lap"),
                     y=alt.Y("driver:N", title=None),
                     color=alt.Color("driver:N", scale=scale, legend=None),
                     tooltip=[alt.Tooltip("driver:N", title="Braking")]))
    return (dress(throttle).properties(height=240),
            dress(marks).properties(height=90))


def gear_chart(duel, code_a, code_b, colour_a, colour_b):
    """Which gear each driver was in, round the lap."""
    data = both(duel, code_a, code_b, ["n_gear"])
    if "n_gear" not in data.columns:
        return None
    scale = alt.Scale(domain=[code_a, code_b], range=[colour_a, colour_b])
    line = (alt.Chart(data).mark_line(strokeWidth=1.8, interpolate="step-after")
            .encode(x=axis("Round the lap"),
                    y=alt.Y("n_gear:Q", title="Gear",
                            axis=alt.Axis(tickMinStep=1, format="d")),
                    color=alt.Color("driver:N", scale=scale, title=None),
                    tooltip=[alt.Tooltip("driver:N", title="Driver"),
                             alt.Tooltip("n_gear:Q", title="Gear")]))
    return dress(line).properties(height=220)


def top_speeds(duel, code_a, code_b):
    """The highest speed each driver reached on their lap."""
    out = {}
    for trace, code in ((duel["trace_a"], code_a), (duel["trace_b"], code_b)):
        if "speed" in trace.columns and len(trace):
            out[code] = float(pd.to_numeric(trace["speed"], errors="coerce").max())
    return out
