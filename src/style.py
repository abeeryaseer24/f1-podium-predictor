"""Look and feel: colours, fonts and the animated background. No prediction logic here."""
from urllib.parse import quote

import streamlit as st

RED = "#e10600"

THEMES = {
    True: {   # dark
        "bg": "#0b0b10", "panel": "#15151e", "panel2": "#1e1e29", "text": "#f5f5f7",
        "muted": "#a3a3b2", "border": "#2c2c3a", "car": "#262632", "checker": "#ffffff",
    },
    False: {  # light
        "bg": "#f6f6f3", "panel": "#ffffff", "panel2": "#ececea", "text": "#15151e",
        "muted": "#55556a", "border": "#d9d9d4", "car": "#d3d3da", "checker": "#15151e",
    },
}

# Speed lines: (top in % of screen height, width in % of screen width,
#               seconds per pass, start delay, extra class)
LINES = [
    (12, 38, 2.6, 0.0, ""), (21, 22, 1.9, -1.2, ""), (30, 46, 3.2, -0.6, " thick"),
    (43, 18, 2.2, -2.1, ""), (55, 34, 2.9, -1.5, ""), (64, 52, 3.6, -0.3, " thick"),
    (76, 26, 2.1, -0.9, ""),
]


def car_image(color):
    """Our own simple race-car silhouette, turned into an image the CSS can use."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 610 160">'
        f'<g fill="{color}">'
        '<rect x="10" y="56" width="62" height="10"/>'
        '<rect x="22" y="60" width="12" height="60"/>'
        '<path d="M20 118 L120 112 L170 96 L260 88 L300 64 L340 60 L360 80 '
        'L470 86 L540 100 L590 124 L20 128 Z"/>'
        '<rect x="540" y="122" width="64" height="7"/>'
        '<circle cx="130" cy="118" r="34"/><circle cx="480" cy="120" r="30"/></g>'
        f'<path d="M300 64 Q330 40 362 66" stroke="{color}" stroke-width="8" fill="none"/>'
        f'<g fill="{RED}"><circle cx="130" cy="118" r="11"/><circle cx="480" cy="120" r="9"/>'
        '<rect x="380" y="92" width="120" height="6"/></g></svg>'
    )
    return "data:image/svg+xml;utf8," + quote(svg)


def apply_style(dark):
    """Inject the CSS and the animated background for the chosen theme."""
    t = THEMES[dark]
    css = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@400;500;600&display=swap');
:root {{
--pp-red: {RED}; --pp-bg: {t['bg']}; --pp-panel: {t['panel']}; --pp-panel2: {t['panel2']};
--pp-text: {t['text']}; --pp-muted: {t['muted']}; --pp-border: {t['border']}; --pp-checker: {t['checker']};
}}
.stApp {{ background: var(--pp-bg); font-family: Inter, system-ui, sans-serif; }}
.stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3 {{ color: var(--pp-text); }}
.stApp h2, .stApp h3 {{ font-family: 'Saira Condensed', sans-serif; font-weight: 800; letter-spacing: .5px; }}
[data-testid="stHeader"] {{ background: var(--pp-bg); border-bottom: 1px solid var(--pp-border); }}
[data-testid="stHeader"] a, [data-testid="stHeader"] span, [data-testid="stHeader"] p {{ color: var(--pp-text) !important; }}
[data-baseweb="popover"] a, [data-baseweb="popover"] span {{ color: var(--pp-text) !important; }}
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stDecoration"] {{ display: none; }}
[data-testid="stSidebar"] {{ background: var(--pp-panel); border-right: 1px solid var(--pp-border); }}
.block-container {{ position: relative; z-index: 1; max-width: 1100px; padding-top: 6rem; }}

/* dropdowns */
[data-baseweb="select"] > div {{ background: var(--pp-panel2) !important; border-color: var(--pp-border) !important; }}
[data-baseweb="select"] * {{ color: var(--pp-text) !important; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {{ background: var(--pp-panel) !important; }}
[data-baseweb="popover"] li {{ color: var(--pp-text) !important; }}

/* buttons */
.stButton > button {{ border-radius: 999px; padding: .6rem 1.5rem; font-weight: 600;
  background: var(--pp-panel); border: 1px solid var(--pp-border); color: var(--pp-text); }}
.stButton > button:hover {{ border-color: var(--pp-red); color: var(--pp-red); }}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {{
  background: var(--pp-red) !important; border-color: var(--pp-red) !important; }}
.stButton > button[kind="primary"] *, [data-testid="stBaseButton-primary"] * {{ color: #fff !important; }}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {{ background: #ff2a1a !important; }}

/* expander and score */
[data-testid="stExpander"] details {{ background: var(--pp-panel); border: 1px solid var(--pp-border); border-radius: 12px; }}
[data-testid="stMetricValue"] {{ font-family: 'Saira Condensed', sans-serif; font-weight: 800; color: var(--pp-red); }}

/* header and step pills */
.pp-hero {{ display: flex; align-items: center; gap: 14px; }}
.pp-hero .bar {{ width: 10px; height: 48px; background: var(--pp-red); transform: skewX(-12deg); }}
.pp-hero h1 {{ font-family: 'Saira Condensed', sans-serif; font-weight: 800; text-transform: uppercase;
  font-size: clamp(2.2rem, 5vw, 3.4rem); letter-spacing: 1px; line-height: 1; margin: 0; padding: 0; }}
.pp-hero h1 span {{ color: var(--pp-red); }}
.pp-sub {{ color: var(--pp-muted); margin: .5rem 0 1.6rem; font-size: 1.05rem; }}
.pp-steps {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 1.4rem; }}
.pp-step {{ padding: 6px 14px; border-radius: 999px; font-size: .85rem; font-weight: 600;
  background: var(--pp-panel); border: 1px solid var(--pp-border); color: var(--pp-muted); }}
.pp-step.on {{ background: var(--pp-red); border-color: var(--pp-red); color: #fff; }}

/* animated background */
.pp-bg {{ position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }}
.pp-glow {{ position: absolute; top: -180px; left: -180px; width: 560px; height: 560px; border-radius: 50%;
  background: radial-gradient(circle, rgba(225,6,0,.18), transparent 70%); }}
.pp-checker {{ position: absolute; background-image: repeating-conic-gradient(var(--pp-checker) 0 25%, transparent 0 50%);
  background-size: 40px 40px; opacity: .06; }}
.pp-checker.corner {{ top: -140px; right: -180px; width: 640px; height: 380px; transform: rotate(-18deg); }}
.pp-checker.band {{ bottom: 0; left: 0; width: 100%; height: 60px; opacity: .05; }}
.pp-line {{ position: absolute; left: 0; height: 2px; border-radius: 2px; opacity: .55;
  background: linear-gradient(90deg, transparent, var(--pp-red) 45%, #ff8a66 75%, transparent);
  box-shadow: 0 0 12px rgba(225,6,0,.55); animation: pp-streak 2.8s linear infinite; }}
.pp-line.thick {{ height: 4px; opacity: .35; }}
.pp-car {{ position: absolute; left: 0; bottom: 9vh; width: min(520px, 60vw); aspect-ratio: 610 / 160;
  background: url("{car_image(t['car'])}") no-repeat center / contain; animation: pp-drive 9s linear infinite; }}
.pp-car::before {{ content: ""; position: absolute; right: 97%; top: 64%; width: 70%; height: 6px;
  background: linear-gradient(90deg, transparent, var(--pp-red)); filter: blur(3px); opacity: .6; }}
@keyframes pp-streak {{ from {{ transform: translateX(110vw); }} to {{ transform: translateX(-60vw); }} }}
@keyframes pp-drive {{ from {{ transform: translateX(-70vw); }} to {{ transform: translateX(130vw); }} }}
@media (prefers-reduced-motion: reduce) {{ .pp-line, .pp-car {{ animation: none; }} }}
</style>"""

    lines = "".join(
        f'<div class="pp-line{cls}" style="top:{top}vh;width:{width}vw;'
        f'animation-duration:{secs}s;animation-delay:{delay}s"></div>'
        for top, width, secs, delay, cls in LINES
    )
    background = (
        '<div class="pp-bg" aria-hidden="true"><div class="pp-glow"></div>'
        '<div class="pp-checker corner"></div><div class="pp-checker band"></div>'
        f'{lines}<div class="pp-car"></div></div>'
    )
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(background, unsafe_allow_html=True)
    st.markdown(COMPONENT_CSS, unsafe_allow_html=True)
    st.markdown(SCOREBOARD_CSS, unsafe_allow_html=True)


BRAND = "Podium Predictor"


def hero(title, subtitle):
    """The big page title (last word in the second style), with the app name above it."""
    words = title.split()
    first, last = " ".join(words[:-1]), words[-1]
    brand = "" if title == BRAND else f'<div class="pp-brand">{BRAND}</div>'
    st.markdown(
        f'{brand}<div class="pp-hero"><h1>{first} <span>{last}</span></h1></div>'
        f'<p class="pp-sub">{subtitle}</p>',
        unsafe_allow_html=True,
    )


def steps(current, upcoming=False):
    """The step pills at the top of each screen."""
    labels = ["Pick a race", "Prediction"] if upcoming else ["Pick a race", "Prediction", "Reveal"]
    pills = "".join(
        f'<div class="pp-step{" on" if i == current else ""}">{i} · {label}</div>'
        for i, label in enumerate(labels, start=1)
    )
    st.markdown(f'<div class="pp-steps">{pills}</div>', unsafe_allow_html=True)

    # ================= Step 4: podium graphic and driver list =================
import html

TEAMS = {   # team id -> (display name, team colour)
    "mercedes": ("Mercedes", "#27f4d2"),
    "ferrari": ("Ferrari", "#e8002d"),
    "red_bull": ("Red Bull", "#3671c6"),
    "mclaren": ("McLaren", "#ff8000"),
    "aston_martin": ("Aston Martin", "#229971"),
    "alpine": ("Alpine", "#ff87bc"),
    "williams": ("Williams", "#64c4ff"),
    "rb": ("Racing Bulls", "#6692ff"),
    "haas": ("Haas", "#b6babd"),
    "audi": ("Audi", "#bb0a30"),
    "cadillac": ("Cadillac", "#c9a227"),
    "manor": ("Manor", "#7a1f2b"),
}


def team_info(team_id):
    """Display name and colour for a team (grey if we don't know it)."""
    return TEAMS.get(team_id, (team_id.replace("_", " ").title(), "#8a8a96"))


COMPONENT_CSS = """<style>
.pp-brand{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:.95rem;letter-spacing:2px;text-transform:uppercase;color:var(--pp-red);margin-bottom:.15rem}
.pp-podium{display:flex;align-items:flex-end;justify-content:center;gap:14px;margin:1.2rem 0 2rem}
.pp-place{flex:1;max-width:230px;display:flex;flex-direction:column;align-items:center;text-align:center}
.pp-info{margin-bottom:10px;opacity:0;animation:pp-fade .5s ease-out forwards}
.pp-name{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.6rem;line-height:1.1;color:var(--pp-text)}
.pp-team{display:flex;align-items:center;justify-content:center;gap:6px;color:var(--pp-muted);font-size:.9rem;margin-top:2px}
.pp-dot{width:10px;height:10px;border-radius:50%;flex:none}
.pp-note{margin-top:6px;font-weight:600;font-size:1.05rem;color:var(--pp-text)}
.pp-block{width:100%;border-top:6px solid;border-radius:8px 8px 0 0;display:flex;justify-content:center;padding-top:10px;box-sizing:border-box;font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:2.6rem;transform-origin:bottom;transform:scaleY(0);animation:pp-rise .6s cubic-bezier(.2,.8,.2,1) forwards}
.pp-block.p1{height:190px;background:#e10600;color:#fff}
.pp-block.p2{height:140px;background:#b9bcc4;color:#15151e}
.pp-block.p3{height:105px;background:#b5743c;color:#15151e}
@keyframes pp-rise{to{transform:scaleY(1)}}
@keyframes pp-fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.pp-tag{display:inline-block;padding:3px 10px;border-radius:999px;font-weight:600;font-size:.85rem;color:#fff}
.pp-tag.hit{background:#15803d}
.pp-tag.miss{background:#c40500}
.pp-rows{display:flex;flex-direction:column;gap:8px;margin:.5rem 0 1.5rem}
.pp-row{display:grid;grid-template-columns:2.2rem 6px 1fr auto;align-items:center;gap:14px;padding:12px 16px;background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:12px}
.pp-row.top{border-color:var(--pp-red)}
.pp-pos{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.3rem;color:var(--pp-muted);text-align:center}
.pp-row.top .pp-pos{color:var(--pp-red)}
.pp-stripe{width:6px;height:34px;border-radius:3px}
.pp-who{display:flex;flex-direction:column;min-width:0}
.pp-who b{font-weight:600;color:var(--pp-text)}
.pp-who small{color:var(--pp-muted);font-size:.85rem}
.pp-pct{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.5rem;color:var(--pp-text)}
.pp-score{text-align:center;margin:.5rem 0 1rem}
.pp-score .big{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:4.5rem;line-height:1;color:var(--pp-red)}
.pp-score .lbl{color:var(--pp-muted)}
.pp-picks{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:1.5rem}
.pp-pick{display:flex;align-items:center;gap:8px;padding:8px 14px;background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:999px;color:var(--pp-text);font-weight:600}
@media (prefers-reduced-motion: reduce){.pp-block,.pp-info{animation:none;transform:none;opacity:1}}
</style>"""


def tag(hit):
    """Green '✓ Predicted' or red '✗ Missed' label."""
    label = "✓ Predicted" if hit else "✗ Missed"
    return f'<div class="pp-tag {"hit" if hit else "miss"}">{label}</div>'


def podium(places):
    """places = [P1, P2, P3]; each a dict with 'name', 'team' and 'note'."""
    layout = [(2, "p2", 0.15), (1, "p1", 0.30), (3, "p3", 0.0)]   # left, middle, right
    parts = []
    for pos, cls, delay in layout:
        p = places[pos - 1]
        team_name, color = team_info(p["team"])
        parts.append(
            '<div class="pp-place">'
            f'<div class="pp-info" style="animation-delay:{delay + 0.45}s">'
            f'<div class="pp-name">{html.escape(p["name"])}</div>'
            f'<div class="pp-team"><div class="pp-dot" style="background:{color}"></div>{team_name}</div>'
            f'<div class="pp-note">{p["note"]}</div></div>'
            f'<div class="pp-block {cls}" style="border-top-color:{color};animation-delay:{delay}s">P{pos}</div>'
            '</div>'
        )
    st.markdown(f'<div class="pp-podium">{"".join(parts)}</div>', unsafe_allow_html=True)


def driver_rows(table, start=0, end=10):
    """Styled rows: position, team stripe, driver, team, grid, podium chance."""
    rows = []
    for i, r in table.iloc[start:end].iterrows():
        team_name, color = team_info(r["constructor"])
        top = " top" if i < 3 else ""
        rows.append(
            f'<div class="pp-row{top}"><div class="pp-pos">{i + 1}</div>'
            f'<div class="pp-stripe" style="background:{color}"></div>'
            f'<div class="pp-who"><b>{html.escape(r["name"])}</b>'
            f'<small>{team_name} · Grid {int(r["grid"])}</small></div>'
            f'<div class="pp-pct">{r["podium_chance"]:.1f}%</div></div>'
        )
    st.markdown(f'<div class="pp-rows">{"".join(rows)}</div>', unsafe_allow_html=True)


def score(correct):
    st.markdown(
        f'<div class="pp-score"><div class="big">{correct} / 3</div>'
        '<div class="lbl">podium drivers predicted correctly</div></div>',
        unsafe_allow_html=True,
    )


def picks(predicted, actual, team_of):
    """The model's three picks as pills, each marked ✓ or ✗."""
    pills = []
    for name in predicted:
        _, color = team_info(team_of[name])
        hit = name in actual
        pills.append(
            f'<div class="pp-pick"><div class="pp-dot" style="background:{color}"></div>'
            f'{html.escape(name)} <div class="pp-tag {"hit" if hit else "miss"}">'
            f'{"✓" if hit else "✗"}</div></div>'
        )
    st.markdown(f'<div class="pp-picks">{"".join(pills)}</div>', unsafe_allow_html=True)

    # ================= Scoreboard page =================
SCOREBOARD_CSS = """<style>
.pp-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:.5rem 0 .8rem}
.pp-stat{background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:14px;padding:16px 18px}
.pp-stat .k{color:var(--pp-muted);font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px}
.pp-stat .v{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:2.6rem;line-height:1.1;color:var(--pp-text)}
.pp-stat .v.red{color:var(--pp-red)}
.pp-stat .s{color:var(--pp-muted);font-size:.9rem}
.pp-verdict{font-weight:600;margin:0 0 1.2rem;color:var(--pp-text)}
.pp-race{display:flex;flex-wrap:wrap;align-items:center;gap:12px 20px;padding:14px 18px;background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:14px;margin-bottom:10px}
.pp-race .head{flex:1 1 220px;min-width:0}
.pp-race .title{font-weight:600;color:var(--pp-text)}
.pp-race .meta{color:var(--pp-muted);font-size:.85rem;margin-top:2px}
.pp-race .chips{display:flex;flex-wrap:wrap;gap:8px;flex:2 1 320px}
.pp-chip{display:flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;border:1px solid var(--pp-border);font-size:.9rem;font-weight:600;color:var(--pp-text)}
.pp-chip small{color:var(--pp-muted);font-weight:500}
.pp-chip.hit{border-color:#1fa855}
.pp-chip.miss{border-color:#c40500}
.pp-chip.hit .mk{color:#1fa855;font-weight:800}
.pp-chip.miss .mk{color:#e10600;font-weight:800}
.pp-race .scores{display:flex;gap:8px}
.pp-sc{padding:6px 12px;border-radius:10px;background:var(--pp-panel2);font-weight:600;font-size:.9rem;color:var(--pp-text);white-space:nowrap}
.pp-sc b{font-family:'Saira Condensed',sans-serif;font-size:1.25rem}
.pp-sc.model b{color:var(--pp-red)}
.pp-wait{padding:6px 12px;border-radius:10px;background:var(--pp-panel2);color:var(--pp-muted);font-weight:600;font-size:.9rem;white-space:nowrap}
.pp-empty{padding:22px;border:1px dashed var(--pp-border);border-radius:14px;color:var(--pp-muted);text-align:center;margin:.5rem 0 1.5rem}
</style>"""


def stat_tiles(summary):
    """Three summary tiles (model, grid, races) and a one-line verdict."""
    races = summary.get("races", 0)
    if not races:
        return
    diff = summary["model_hits"] - summary["grid_hits"]
    plural = "s" if abs(diff) != 1 else ""
    if diff > 0:
        verdict = f"The model is ahead of the grid by {diff} podium driver{plural}."
    elif diff < 0:
        verdict = f"The grid is ahead of the model by {-diff} podium driver{plural}."
    else:
        verdict = "The model and the grid are level."
    waiting = summary.get("waiting", 0)
    tiles = [
        ("Model", f'{summary["model_avg"]:.2f}',
         f'per race · {summary["model_hits"]} of {3 * races} podium drivers', " red"),
        ("Grid baseline", f'{summary["grid_avg"]:.2f}',
         f'per race · {summary["grid_hits"]} of {3 * races}', ""),
        ("Races scored", str(races),
         f"{waiting} waiting for result" if waiting else "all results in", ""),
    ]
    tiles_html = "".join(
        f'<div class="pp-stat"><div class="k">{k}</div><div class="v{c}">{v}</div>'
        f'<div class="s">{s}</div></div>'
        for k, v, s, c in tiles
    )
    st.markdown(f'<div class="pp-stats">{tiles_html}</div><p class="pp-verdict">{verdict}</p>',
                unsafe_allow_html=True)


def race_card(title, meta, picks, model_hits=None, grid_hits=None):
    """One race on the scoreboard. picks = list of dicts: name, team, mark ('hit'/'miss'/None), extra."""
    chips = []
    for p in picks:
        _, color = team_info(p["team"])
        mark = {"hit": '<span class="mk">✓</span>', "miss": '<span class="mk">✗</span>'}.get(p["mark"], "")
        cls = f' {p["mark"]}' if p["mark"] else ""
        extra = f' <small>{p["extra"]}</small>' if p.get("extra") else ""
        chips.append(f'<div class="pp-chip{cls}"><div class="pp-dot" style="background:{color}"></div>'
                     f'{html.escape(p["name"])}{extra}{mark}</div>')
    if model_hits is None:
        right = '<div class="pp-wait">Waiting for result</div>'
    else:
        right = (f'<div class="pp-sc model">Model <b>{model_hits}/3</b></div>'
                 f'<div class="pp-sc">Grid <b>{grid_hits}/3</b></div>')
    return (f'<div class="pp-race"><div class="head"><div class="title">{html.escape(title)}</div>'
            f'<div class="meta">{meta}</div></div><div class="chips">{"".join(chips)}</div>'
            f'<div class="scores">{right}</div></div>')


def show_cards(cards):
    st.markdown("".join(cards), unsafe_allow_html=True)


def empty_note(text):
    st.markdown(f'<div class="pp-empty">{text}</div>', unsafe_allow_html=True)