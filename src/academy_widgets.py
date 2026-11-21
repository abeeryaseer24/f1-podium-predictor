"""Live demos for the Engineering Academy. Each one runs on the real engines (lapsim.py)
or the real race data, never on made-up numbers, unless it says so on the screen."""
from dataclasses import replace

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import app_sim as A
import lapsim
from app_data import get_race_file, get_race_info
from charts import dress, theme
from style import stat_strip
from ui_kit import FAIR, GOOD, POOR, heat, sheet

# Circuits used to compare tracks, from fast to twisty. The latest calibrated race at each wins.
SHOWCASE = ["Monza", "Spa-Francorchamps", "Silverstone", "Suzuka", "Barcelona", "Marina Bay",
            "Budapest", "Monaco"]


# Comparisons between circuits use one season so every car follows the same rules. 2025 is
# the last full season before 2026's movable wings, which the simulator doesn't model.
COMPARE_SEASON = 2025


@st.cache_data(ttl=600)
def latest_at(location, season=None):
    """The newest usable race folder at a location (in `season` if one is given), or None."""
    for folder in A.usable_races()["folder"]:
        if get_race_info(folder)["location"] == location and (season is None or A.season_of(folder) == season):
            return folder
    return latest_at(location) if season is not None else None


def circuit_picker(key, default="Monza"):
    races = A.usable_races()
    names = {r.folder: f"{r.race_name} {r.season}" for r in races.itertuples()}
    folders = list(names)
    start = latest_at(default)
    return st.selectbox("Circuit", folders, index=folders.index(start) if start in folders else 0,
                        format_func=names.get, key=key)


# ---------- 0.2 the physics you need ----------

def downforce_calculator():
    left, right = st.columns(2)
    speed = left.slider("Speed (km/h)", 0, 350, 250, step=5, key="w_df_speed")
    cza = left.slider("Downforce coefficient × area, CzA (m²)", 2.0, 6.0, 4.4, step=0.1, key="w_df_cza",
                      help="Modern cars are roughly 3–6 m² depending on the wing level.")
    mass = right.slider("Car + driver mass (kg)", 700, 900, 800, step=5, key="w_df_mass")
    place = right.radio("Air", ["Sea level (1.225 kg/m³)", "Mexico City, 2,240 m (0.94 kg/m³)"], key="w_df_air")
    rho = 1.225 if place.startswith("Sea") else 0.94
    v = speed / 3.6
    downforce = 0.5 * rho * cza * v * v
    weight = mass * lapsim.G
    v_equal = np.sqrt(weight / (0.5 * rho * cza)) * 3.6
    stat_strip([
        ("Downforce", f"{downforce / 1000:.1f} kN", f"like {downforce / lapsim.G:.0f} kg pressing down", True),
        ("Compared with weight", f"{downforce / weight:.2f}×", f"weight is {weight / 1000:.1f} kN", False),
        ("Downforce = weight at", f"{v_equal:.0f} km/h", "above this it could, in theory, drive upside down", False),
    ])
    speeds = np.arange(0, 361, 5)
    data = pd.DataFrame({"Speed (km/h)": np.r_[speeds, speeds],
                         "Force (kN)": np.r_[0.5 * rho * cza * (speeds / 3.6) ** 2 / 1000,
                                             np.full(len(speeds), weight / 1000)],
                         "Force": ["Downforce"] * len(speeds) + ["Weight"] * len(speeds)})
    chart = alt.Chart(data).mark_line(strokeWidth=2.5).encode(
        x="Speed (km/h):Q", y="Force (kN):Q",
        color=alt.Color("Force:N", scale=alt.Scale(domain=["Downforce", "Weight"], range=["#e10600", "#8a8a96"]),
                        legend=alt.Legend(orient="top", title=None)))
    dot = alt.Chart(pd.DataFrame({"Speed (km/h)": [speed], "Force (kN)": [downforce / 1000]})).mark_point(
        size=120, filled=True, color="#e10600").encode(x="Speed (km/h):Q", y="Force (kN):Q")
    st.altair_chart(dress(chart + dot).properties(height=280), use_container_width=True)
    st.caption("Downforce grows with the square of speed: twice as fast means four times the downforce. "
               "The weight line stays flat.")


# ---------- 0.3 what makes a car fast ----------

def lap_equation():
    folder = circuit_picker("w_lap_circuit")
    track = A.get_track(folder)
    sim = A.run_car(folder, A.car_key(A.calibrated(folder)))
    ds = sim["s"][1] - sim["s"][0]
    piece = ds / sim["speed"]
    shares = {m: float(piece[sim["mode"] == m].sum()) for m in A.MODE_COLOURS}
    stat_strip([
        ("Lap time", A.lap_str(sim["lap_time"]), f"{len(sim['s'])} pieces of {ds:.1f} m added up", True),
        ("Full throttle", f"{shares['throttle']:.1f}s", "limited by power and drag", False),
        ("Cornering", f"{shares['corner']:.1f}s", "limited by grip and downforce", False),
        ("Braking", f"{shares['brake']:.1f}s", "limited by grip, helped by drag", False),
    ])
    step = max(1, len(sim["s"]) // 700)
    data = pd.DataFrame({"Distance (m)": sim["s"][::step], "Speed (km/h)": sim["speed_kmh"][::step],
                         "Limited by": pd.Series(sim["mode"][::step]).map(
                             {"throttle": "Power and drag", "corner": "Grip in the corner", "brake": "Braking grip"})})
    chart = alt.Chart(data).mark_circle(size=14).encode(
        x=alt.X("Distance (m):Q", scale=alt.Scale(nice=False)), y=alt.Y("Speed (km/h):Q"),
        color=alt.Color("Limited by:N", scale=alt.Scale(
            domain=["Power and drag", "Grip in the corner", "Braking grip"], range=[GOOD, FAIR, POOR]),
            legend=alt.Legend(orient="top", title=None)))
    st.altair_chart(dress(chart).properties(height=280), use_container_width=True)
    st.caption(f"The simulated lap at {get_race_info(folder)['race_name']} ({track.length / 1000:.2f} km), "
               "coloured by what limits the car at each point. See it in 3D on the Lap Simulator page.")


# ---------- 0.4 reading telemetry ----------

def telemetry_reader():
    folder = circuit_picker("w_tel_circuit", default="Silverstone")
    track = A.get_track(folder)
    df = get_race_file(folder, "track")
    real = lapsim.real_trace(df, track)
    s = track.s
    step = max(1, len(s) // 700)
    rows = []
    for channel, values, unit in (("Speed", real["speed_kmh"], "km/h"), ("Throttle", real["throttle"], "%"),
                                  ("Brake", np.clip(real["brake"], 0, 100), "%")):
        rows.append(pd.DataFrame({"Distance (m)": s[::step], "Value": np.round(values[::step], 1),
                                  "Channel": f"{channel} ({unit})"}))
    data = pd.concat(rows)
    text, grid, muted = theme()
    base = alt.Chart(data).mark_line(strokeWidth=1.8, color="#e10600").encode(
        x=alt.X("Distance (m):Q", scale=alt.Scale(nice=False)), y=alt.Y("Value:Q", title=None))
    chart = base.properties(height=120).facet(row=alt.Row("Channel:N", title=None,
                                                          header=alt.Header(labelColor=text, labelAngle=0,
                                                                            labelAlign="left", labelFontSize=12)))
    chart = chart.resolve_scale(y="independent").configure_view(strokeWidth=0).configure_axis(
        labelColor=muted, titleColor=muted, gridColor=grid, domainColor=grid, tickColor=grid)
    st.altair_chart(chart, use_container_width=True)

    braking = np.flatnonzero(np.diff((real["brake"] > 50).astype(int)) == 1)
    slow = int(np.argmin(real["speed_kmh"]))
    full = float((real["throttle"] >= 98).mean())
    stat_strip([
        ("Top speed", A.kmh(real["speed_kmh"].max()), "end of the longest straight", False),
        ("Slowest point", A.kmh(real["speed_kmh"][slow]), f"{s[slow]:.0f} m from the line", False),
        ("Full throttle", f"{full:.0%}", "of the distance", False),
        ("Braking zones", f"{len(braking)}", "times the brake goes past half", False),
    ])
    st.caption(f"The real fastest lap of the {get_race_info(folder)['race_name']} {get_race_info(folder)['season']}, "
               "from OpenF1. The brake channel is close to on/off in this data, which is why it looks like steps.")


# ---------- 1.1 anatomy ----------

ANATOMY = [
    ("1", "Front wing", "The first part to meet the air: makes front downforce and steers the airflow round the front wheels."),
    ("2", "Nose and front crash structure", "Absorbs a frontal impact. Its shape feeds air under the car."),
    ("3", "Front suspension", "Carbon wishbones and a push rod or pull rod to springs and dampers inside the car."),
    ("4", "Halo", "The titanium hoop that protects the driver's head."),
    ("5", "Cockpit and survival cell", "The carbon monocoque: the driver's safety cell and the car's backbone."),
    ("6", "Airbox and roll hoop", "Feeds air to the engine; the hoop protects the driver if the car turns over."),
    ("7", "Sidepods and radiators", "House the radiators that cool the engine, battery and gearbox."),
    ("8", "Power unit", "A 1.6-litre V6 turbo with an electric motor (MGU-K) and battery, bolted to the back of the monocoque."),
    ("9", "Floor and underbody tunnels", "Since 2022 the biggest source of downforce: ground effect."),
    ("10", "Gearbox and rear suspension", "Eight forward gears, and the rear suspension mounts directly on the gearbox casing."),
    ("11", "Diffuser", "The upswept rear of the floor, where the underbody air slows and pressure recovers."),
    ("12", "Rear wing and beam wing", "Rear downforce, and the flap that opens for less drag on the straights."),
]


def car_anatomy():
    """A side view of a generic, unbranded modern car with numbered parts."""
    text, grid, muted = theme()
    body, accent = ("#3a3a48" if st.session_state.get("dark", True) else "#c8c8d0"), "#e10600"
    tags = {
        "1": (72, 186), "2": (150, 150), "3": (218, 128), "4": (395, 72), "5": (370, 128),
        "6": (470, 52), "7": (520, 118), "8": (585, 92), "9": (520, 196), "10": (735, 120),
        "11": (790, 182), "12": (838, 60),
    }
    circles = "".join(
        f'<g><circle cx="{x}" cy="{y}" r="13" fill="{accent}"/>'
        f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-size="13" font-weight="800" fill="#fff" '
        f'font-family="Saira Condensed, Inter, sans-serif">{n}</text></g>' for n, (x, y) in tags.items())
    svg = f"""
<svg viewBox="0 0 920 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side view of a Formula 1 car with numbered parts" style="width:100%;height:auto">
  <line x1="10" y1="226" x2="910" y2="226" stroke="{grid}" stroke-width="2"/>
  <!-- floor -->
  <path d="M120 200 L800 200 L830 178 L860 178 L860 192 L812 212 L130 212 Z" fill="{body}" opacity=".85"/>
  <!-- front wing -->
  <path d="M30 196 L150 192 L150 206 L30 210 Z" fill="{body}"/>
  <rect x="26" y="168" width="10" height="44" fill="{body}"/>
  <!-- nose + monocoque -->
  <path d="M110 186 C170 170 250 150 320 138 L330 182 L118 200 Z" fill="{body}"/>
  <!-- cockpit / engine cover / airbox -->
  <path d="M320 138 L360 122 L430 118 L455 64 L500 62 L520 110 L700 140 L740 160 L740 200 L330 200 Z" fill="{body}"/>
  <!-- halo -->
  <path d="M352 122 Q380 74 438 92" fill="none" stroke="{text}" stroke-width="6" stroke-linecap="round"/>
  <!-- sidepod line -->
  <path d="M440 150 Q520 140 600 170 L700 186" fill="none" stroke="{muted}" stroke-width="2" opacity=".7"/>
  <!-- power unit (inside, dashed) -->
  <rect x="540" y="128" width="110" height="56" rx="8" fill="none" stroke="{accent}" stroke-width="2" stroke-dasharray="6 5"/>
  <!-- gearbox -->
  <rect x="660" y="150" width="90" height="34" rx="6" fill="none" stroke="{muted}" stroke-width="2" stroke-dasharray="4 4"/>
  <!-- rear wing + endplate + beam wing -->
  <rect x="800" y="44" width="80" height="14" rx="3" fill="{body}"/>
  <rect x="806" y="62" width="70" height="9" rx="3" fill="{body}"/>
  <rect x="868" y="40" width="10" height="130" fill="{body}"/>
  <rect x="812" y="150" width="54" height="8" rx="3" fill="{body}"/>
  <rect x="790" y="70" width="12" height="100" fill="{body}" opacity=".8"/>
  <!-- wheels -->
  <circle cx="220" cy="190" r="36" fill="#15151e" stroke="{muted}" stroke-width="3"/>
  <circle cx="220" cy="190" r="14" fill="{accent}"/>
  <circle cx="740" cy="188" r="38" fill="#15151e" stroke="{muted}" stroke-width="3"/>
  <circle cx="740" cy="188" r="15" fill="{accent}"/>
  <!-- suspension -->
  <path d="M220 190 L330 160 M220 190 L330 178" stroke="{muted}" stroke-width="2.5"/>
  <path d="M740 188 L690 168 M740 188 L690 182" stroke="{muted}" stroke-width="2.5"/>
  {circles}
</svg>"""
    st.markdown(f'<div class="ac-figure">{svg}</div>', unsafe_allow_html=True)
    st.caption("Our own simplified drawing of a generic modern car, not any team's. A 3D version you can "
               "take apart is coming to the Academy.")
    st.markdown("".join(f'<div class="ac-term"><b>{n} · {name}</b><span>{what}</span></div>'
                        for n, name, what in ANATOMY), unsafe_allow_html=True)


# ---------- 1.2 the 2026 rules on the simulator ----------

def regulation_change():
    folder = circuit_picker("w_reg_circuit", default="Silverstone")
    base = A.calibrated(folder)
    st.caption("Start from a calibrated car, then apply a rule change. The 2026 preset uses the targets "
               "the FIA published when the rules were announced in June 2024; the cars that raced have moved on from them.")
    presets = {"No change": (0, 0, 0), "2026 targets": (-30, -55, -30), "Only lighter (−30 kg)": (0, 0, -30),
               "Only less downforce (−30%)": (-30, 0, 0)}
    choice = st.radio("Preset", list(presets), horizontal=True, key="w_reg_preset")
    d0, x0, m0 = presets[choice]
    c1, c2, c3 = st.columns(3)
    down = c1.slider("Downforce change (%)", -60, 30, d0, key=f"w_reg_down_{choice}")
    drag = c2.slider("Drag change (%)", -60, 30, x0, key=f"w_reg_drag_{choice}")
    mass = c3.slider("Mass change (kg)", -60, 30, m0, key=f"w_reg_mass_{choice}")
    changed = replace(base, downforce_scale=1 + down / 100, drag_scale=1 + drag / 100, mass=base.mass + mass)
    a = A.run_car(folder, A.car_key(base))
    b = A.run_car(folder, A.car_key(changed))
    stat_strip([
        ("Lap time change", f"{b['lap_time'] - a['lap_time']:+.2f}s", f"{A.lap_str(a['lap_time'])} → {A.lap_str(b['lap_time'])}", True),
        ("Top speed", A.kmh(b["speed_kmh"].max()), f"{b['speed_kmh'].max() - a['speed_kmh'].max():+.0f} km/h", False),
        ("Slowest corner", A.kmh(b["speed_kmh"].min()), f"{b['speed_kmh'].min() - a['speed_kmh'].min():+.0f} km/h", False),
        ("Fastest corner, peak lateral g", f"{b['lat_g'].max():.1f} g", f"was {a['lat_g'].max():.1f} g", False),
    ])
    st.altair_chart(A.speed_chart([("New rules", "#e10600", b["s"], b["speed_kmh"]),
                                   ("Calibrated car", "#8a8a96", a["s"], a["speed_kmh"])], height=260),
                    use_container_width=True)
    st.caption("Same power in both. The real 2026 power units also change how power is delivered, "
               "which this simple model leaves out.")


# ---------- 1.3 sensitivities on every circuit ----------

@st.cache_data(ttl=3600)
def sensitivity_table():
    changes = {
        "−10 kg": lambda c: replace(c, mass=c.mass - 10),
        "+10 kW": lambda c: replace(c, power_kw=c.power_kw + 10),
        "+5% downforce": lambda c: replace(c, downforce_scale=c.downforce_scale * 1.05),
        "−5% drag": lambda c: replace(c, drag_scale=c.drag_scale * 0.95),
        "+1% grip": lambda c: replace(c, grip=c.grip * 1.01),
    }
    rows = {}
    for location in SHOWCASE:
        folder = latest_at(location, COMPARE_SEASON)
        if not folder:
            continue
        car = A.calibrated(folder)
        t0 = A.run_car(folder, A.car_key(car))["lap_time"]
        rows[location] = {name: A.run_car(folder, A.car_key(f(car)))["lap_time"] - t0 for name, f in changes.items()}
    return rows, list(changes)


def sensitivity_map():
    rows, columns = sensitivity_table()
    if not rows:
        st.info("No circuits calibrated yet.")
        return
    cells = {}
    for col in columns:
        gains = [-rows[r][col] for r in rows]
        lo, hi = min(gains), max(gains)
        for r in rows:
            gain = -rows[r][col]
            cells[(r, col)] = (f"{gain:.3f}s", (gain - lo) / ((hi - lo) or 1))
    heat(list(rows), columns, cells, legend=("Worth least here", "Worth most here"))
    st.caption(f"Time gained per lap for each change, on each circuit's own calibrated {COMPARE_SEASON} car. "
               "Read down a column: the same upgrade is worth very different amounts on different tracks.")


# ---------- 1.4 the design compromise ----------

@st.cache_data(ttl=3600)
def wing_sweep(folders):
    out = []
    for folder in folders:
        car = A.calibrated(folder)
        times = [A.run_car(folder, A.car_key(replace(car, wing=w)))["lap_time"] for w in np.linspace(0, 1, 11)]
        best = min(times)
        name = get_race_info(folder)["location"]
        out += [{"Wing level": round(w, 1), "Lap time lost (s)": t - best, "Circuit": name}
                for w, t in zip(np.linspace(0, 1, 11), times)]
    return pd.DataFrame(out)


def compromise():
    folders = tuple(f for f in (latest_at("Monza", COMPARE_SEASON), latest_at("Silverstone", COMPARE_SEASON),
                                latest_at("Monaco", COMPARE_SEASON)) if f)
    if len(folders) < 2:
        st.info("This needs Monza and Monaco calibrated.")
        return
    data = wing_sweep(folders)
    colours = ["#e10600", "#e8b33a", "#27f4d2"][:len(folders)]
    chart = alt.Chart(data).mark_line(point=True, strokeWidth=2.5).encode(
        x="Wing level:Q", y=alt.Y("Lap time lost (s):Q", title="Lap time lost against the best wing (s)"),
        color=alt.Color("Circuit:N", scale=alt.Scale(range=colours), legend=alt.Legend(orient="top", title=None)),
        tooltip=["Circuit", "Wing level", alt.Tooltip("Lap time lost (s):Q", format=".3f")])
    st.altair_chart(dress(chart).properties(height=300), use_container_width=True)
    best = data.loc[data.groupby("Circuit")["Lap time lost (s)"].idxmin()]
    st.caption(f"Every point is a full simulated lap of a {COMPARE_SEASON} car with a different wing level, "
               "everything else the same. "
               + " · ".join(f"Best at {r['Circuit']}: wing {r['Wing level']:.1f}" for _, r in best.iterrows()) + ".")
