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


def driver_rows(table, start=0, end=10, real=False):
    """Styled rows: predicted position, team stripe, driver, team, grid, podium and win chance.
    With real=True (past races), also where the driver really finished."""
    rows = []
    for i, r in table.iloc[start:end].iterrows():
        team_name, color = team_info(r["constructor"])
        top = " top" if i < 3 else ""
        extra = ""
        if real and r.get("finish_position") == r.get("finish_position"):
            off = int(r["finish_position"] - (i + 1))
            word = "spot on" if off == 0 else f"{abs(off)} place{'s' if abs(off) > 1 else ''} {'lower' if off > 0 else 'higher'}"
            extra = f' · <b>really finished P{int(r["finish_position"])}</b> ({word})'
        win = f'<small style="display:block;font-size:.75rem;font-weight:600;opacity:.7">win {r["win_chance"]:.0f}%</small>' \
            if "win_chance" in r else ""
        rows.append(
            f'<div class="pp-row{top}"><div class="pp-pos">{i + 1}</div>'
            f'<div class="pp-stripe" style="background:{color}"></div>'
            f'<div class="pp-who"><b>{html.escape(r["name"])}</b>'
            f'<small>{team_name} · Grid {int(r["grid"])}{extra}</small></div>'
            f'<div class="pp-pct" style="text-align:right">{r["podium_chance"]:.1f}%{win}</div></div>'
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
.pp-osum{padding:12px 14px;border-radius:12px;background:var(--pp-panel2);color:var(--pp-text);font-size:.92rem;line-height:1.5;margin-bottom:10px}
.pp-order{display:flex;flex-direction:column;gap:4px}
.pp-orow{display:grid;grid-template-columns:3rem 10px minmax(0,1fr) 3rem 9.5rem;align-items:center;gap:10px;padding:7px 12px;border-radius:10px;background:var(--pp-panel);border:1px solid var(--pp-border);font-size:.92rem;color:var(--pp-text)}
.pp-orow.nr{grid-template-columns:3rem 10px minmax(0,1fr)}
.pp-orow.head{background:none;border:none;padding-top:0;padding-bottom:0;color:var(--pp-muted);font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px}
.pp-orow.head *{color:var(--pp-muted);font-family:inherit;font-size:.72rem;font-weight:600}
.pp-opos{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.05rem;color:var(--pp-muted)}
.pp-oname{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pp-oreal{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.05rem}
.pp-ov{font-size:.82rem;font-weight:600;padding:3px 9px;border-radius:999px;justify-self:start;color:var(--pp-muted)}
.pp-ov.on{background:rgba(31,168,85,.18);color:#1fa855}
.pp-ov.near{background:rgba(242,194,27,.2);color:#c99a00}
.pp-ov.far{background:rgba(225,6,0,.15);color:#f0443a}
@media (max-width:640px){.pp-orow{grid-template-columns:2.4rem 8px minmax(0,1fr) 2.4rem 5.6rem;gap:7px;padding:6px 9px;font-size:.85rem}.pp-orow.nr{grid-template-columns:2.4rem 8px minmax(0,1fr)}.pp-ov{font-size:.74rem;padding:2px 7px}.pp-ov .w{display:none}
.pp-stats{grid-template-columns:repeat(3,1fr);gap:8px}.pp-stat{padding:10px 10px}.pp-stat .v{font-size:1.9rem}.pp-stat .k{font-size:.66rem;letter-spacing:.3px}.pp-stat .s{font-size:.72rem;line-height:1.3}}
.pp-banner{padding:14px 18px;border-radius:14px;border:1px solid var(--pp-border);background:var(--pp-panel);margin:.4rem 0 1.2rem;display:flex;flex-direction:column;gap:3px}
.pp-banner b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.6rem;letter-spacing:.5px;color:var(--pp-text)}
.pp-banner span{color:var(--pp-muted);font-size:.92rem}
.pp-banner.hammer{border-color:var(--pp-red);background:linear-gradient(90deg,rgba(225,6,0,.16),var(--pp-panel) 70%)}
.pp-banner.hammer b{color:var(--pp-red);text-transform:uppercase}
.pp-vs{display:grid;gap:10px;margin:.3rem 0 .6rem}
.pp-vsbox{background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:14px;padding:12px 14px;min-width:0}
.pp-vst{color:var(--pp-muted);font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px}
.pp-vsrow{display:flex;align-items:center;gap:8px;padding:5px 0;color:var(--pp-text);font-weight:600;font-size:.95rem}
.pp-vsp{font-family:'Saira Condensed',sans-serif;font-weight:800;color:var(--pp-muted);width:1.6rem}
.pp-vsn{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pp-vsn .short{display:none}
.pp-vsrow .mk{font-weight:800}.pp-vsrow .mk.hit{color:#1fa855}.pp-vsrow .mk.miss{color:#f0443a}
.pp-msg{padding:12px 16px;border-radius:12px;font-weight:700;margin:0 0 1.4rem;color:var(--pp-text);background:var(--pp-panel2)}
.pp-msg.win{background:rgba(31,168,85,.16);color:#1fa855}
.pp-msg.lose{background:rgba(225,6,0,.13);color:#f0443a}
@media (max-width:640px){.pp-vs{gap:6px}.pp-vsbox{padding:9px 8px}.pp-vsrow{font-size:.74rem;gap:4px}.pp-vsp{width:1rem}.pp-vsrow .pp-dot{width:4px;height:16px;border-radius:2px}.pp-vsn{overflow:visible;text-overflow:clip;letter-spacing:-.2px;min-width:auto}.pp-vsrow .mk{flex:none}.pp-vsbox{padding:9px 6px}.pp-vsn .full{display:none}.pp-vsn .short{display:inline}.pp-vst{font-size:.66rem}}
.pp-whys{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin:.2rem 0 .6rem}
.pp-whycard{background:var(--pp-panel);border:1px solid var(--pp-border);border-top:4px solid;border-radius:12px;padding:12px 14px}
.pp-whycard .h{font-weight:600;color:var(--pp-text);margin-bottom:8px;display:flex;align-items:baseline;gap:6px;flex-wrap:wrap}
.pp-whycard .h b{font-family:'Saira Condensed',sans-serif;font-weight:800;color:var(--pp-red);font-size:1.1rem}
.pp-whycard .h small{color:var(--pp-muted);font-weight:500}
.pp-why{margin:7px 0}
.pp-why .t{font-size:.88rem;color:var(--pp-text);line-height:1.3}
.pp-why .bar{height:5px;border-radius:3px;background:var(--pp-panel2);margin-top:4px;overflow:hidden}
.pp-why .bar span{display:block;height:100%;border-radius:3px}
.pp-strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:6px;margin:.4rem 0 .3rem}
.pp-rt{border-radius:10px;padding:8px 8px 7px;display:flex;flex-direction:column;gap:1px;border:1px solid var(--pp-border);min-width:0}
.pp-rt b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.5rem;line-height:1}
.pp-rt small{font-size:.68rem;font-weight:600;opacity:.75}
.pp-rt span{font-size:.72rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pp-rt.h3{background:#e10600;border-color:#e10600}.pp-rt.h3 *{color:#fff}
.pp-rt.h2{background:rgba(225,6,0,.45);border-color:transparent}.pp-rt.h2 *{color:#fff}
.pp-rt.h1{background:rgba(225,6,0,.16)}.pp-rt.h1 *{color:var(--pp-text)}
.pp-rt.h0{background:var(--pp-panel)}.pp-rt.h0 *{color:var(--pp-muted)}
.pp-legend{color:var(--pp-muted);font-size:.8rem;display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:0 0 1rem}
.pp-legend i{display:inline-block;width:12px;height:12px;border-radius:3px;border:1px solid var(--pp-border);margin-left:6px}
.pp-legend i.h3{background:#e10600}.pp-legend i.h2{background:rgba(225,6,0,.45)}.pp-legend i.h1{background:rgba(225,6,0,.16)}.pp-legend i.h0{background:var(--pp-panel)}
.pp-call{background:var(--pp-panel);border:1px solid var(--pp-border);border-left:4px solid;border-radius:12px;padding:12px 16px;margin-bottom:10px}
.pp-call.good{border-left-color:#1fa855}.pp-call.bad{border-left-color:#e10600}
.pp-call .k{color:var(--pp-muted);font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px}
.pp-call b{display:block;color:var(--pp-text);font-size:1.05rem;margin:2px 0}
.pp-call span{color:var(--pp-muted);font-size:.88rem}
@media (max-width:640px){.pp-stats.four{grid-template-columns:repeat(2,1fr)}.pp-strip{grid-template-columns:repeat(auto-fill,minmax(62px,1fr))}}
.pp-block.pp-ghost{background:var(--pp-panel2)!important;color:var(--pp-muted)!important;border-top-color:var(--pp-border)!important}
.pp-tease{text-align:center;color:var(--pp-muted);margin:-1.2rem 0 1rem}
.pp-band{padding:18px 20px;border-radius:16px;border:1px solid var(--pp-border);background:var(--pp-panel);margin:1.4rem 0 .4rem;display:flex;flex-direction:column;gap:4px}
.pp-band b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.7rem;letter-spacing:.5px;color:var(--pp-text);line-height:1.1}
.pp-band span{color:var(--pp-muted)}
.pp-band.hot{background:linear-gradient(100deg,#e10600,#9e0400);border-color:#e10600}
.pp-band.hot b,.pp-band.hot span{color:#fff}
.pp-band.hot b{text-transform:uppercase}
.pp-link{color:var(--pp-muted);font-size:.9rem;margin-top:1.4rem}
.pp-empty{padding:22px;border:1px dashed var(--pp-border);border-radius:14px;color:var(--pp-muted);text-align:center;margin:.5rem 0 1.5rem}
</style>"""


def stat_tiles(summary):
    """Three summary tiles (our model, the grid, races finished) and a one-line verdict."""
    races = summary.get("races", 0)
    if not races:
        return
    diff = summary["model_hits"] - summary["grid_hits"]
    plural = "s" if abs(diff) != 1 else ""
    if diff > 0:
        verdict = f"Our model is ahead of the grid by {diff} podium driver{plural}."
    elif diff < 0:
        verdict = f"The grid is ahead of our model by {-diff} podium driver{plural}."
    else:
        verdict = "Our model and the grid are level."
    waiting = summary.get("waiting", 0)
    tiles = [
        ("Our model", f'{summary["model_avg"]:.2f}',
         f'podium drivers per race · {summary["model_hits"]} of {3 * races}', " red"),
        ("The grid", f'{summary["grid_avg"]:.2f}',
         f'podium drivers per race · {summary["grid_hits"]} of {3 * races}', ""),
        ("Races finished", str(races), f"{waiting} waiting" if waiting else "all results in", ""),
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
        right = '<div class="pp-wait">WAITING</div>'
    else:
        right = (f'<div class="pp-sc model">Our model <b>{model_hits}/3</b></div>'
                 f'<div class="pp-sc">Grid <b>{grid_hits}/3</b></div>')
    return (f'<div class="pp-race"><div class="head"><div class="title">{html.escape(title)}</div>'
            f'<div class="meta">{meta}</div></div><div class="chips">{"".join(chips)}</div>'
            f'<div class="scores">{right}</div></div>')


def show_cards(cards):
    st.markdown("".join(cards), unsafe_allow_html=True)


def order_table(rows, summary):
    """The whole predicted order (one line per driver). After the race: where each driver really
    finished and a coloured verdict (green spot on, yellow 1-2 places off, red 3 or more)."""
    out = []
    if summary:
        out.append(f'<div class="pp-osum"><b>On average {summary["model_off"]:.1f} places off</b> · copying '
                   f'the grid would have been {summary["grid_off"]:.1f} places off<br>'
                   f'{summary["spot_on"]} driver{"s" if summary["spot_on"] != 1 else ""} spot on · '
                   f'{summary["within_2"]} within 2 places</div>')
    for r in rows.itertuples():
        _, color = team_info(r.team) if r.team else ("", "#8a8a96")
        if summary is None:
            right = ""
        elif r.real is None or r.real != r.real:
            right = '<span class="pp-oreal">—</span><span class="pp-ov">No result</span>'
        else:
            off = int(r.off)
            cls = "on" if off == 0 else ("near" if abs(off) <= 2 else "far")
            word = "✓ Spot on" if off == 0 else (
                f'{abs(off)}<span class="w"> place{"s" if abs(off) > 1 else ""}</span> '
                f'{"lower" if off > 0 else "higher"}')
            right = f'<span class="pp-oreal">P{int(r.real)}</span><span class="pp-ov {cls}">{word}</span>'
        out.append(f'<div class="pp-orow{"" if summary else " nr"}"><span class="pp-opos">P{r.predicted}</span>'
                   f'<span class="pp-dot" style="background:{color}"></span>'
                   f'<span class="pp-oname">{html.escape(r.name)}</span>{right}</div>')
    head = (f'<div class="pp-orow head{"" if summary else " nr"}"><span class="pp-opos">Ours</span><span></span><span class="pp-oname">'
            'Driver</span>' + ('<span class="pp-oreal">Real</span><span class="pp-ov">Verdict</span>'
                               if summary else '') + '</div>')
    st.markdown(f'<div class="pp-order">{head}{"".join(out)}</div>', unsafe_allow_html=True)


def vs_boxes(boxes):
    """Side-by-side boxes, e.g. You / Our model / Actual result.
    boxes = [(title, [(name, team, mark)])], mark True (on the podium), False, or None (no mark)."""
    cols = []
    for title, rows in boxes:
        lines = []
        for i, (name, team, mark) in enumerate(rows, start=1):
            _, color = team_info(team) if team else ("", "#8a8a96")
            tick = "" if mark is None else (f'<span class="mk {"hit" if mark else "miss"}">{"✓" if mark else "✗"}</span>')
            surname = html.escape(name.split(" ")[-1])
            lines.append(f'<div class="pp-vsrow"><span class="pp-vsp">P{i}</span>'
                         f'<span class="pp-dot" style="background:{color}"></span>'
                         f'<span class="pp-vsn"><span class="full">{html.escape(name)}</span>'
                         f'<span class="short">{surname}</span></span>{tick}</div>')
        cols.append(f'<div class="pp-vsbox"><div class="pp-vst">{html.escape(title)}</div>{"".join(lines)}</div>')
    st.markdown(f'<div class="pp-vs" style="grid-template-columns:repeat({len(boxes)},1fr)">{"".join(cols)}</div>',
                unsafe_allow_html=True)


def why_cards(table, why):
    """'Why this pick?': one small card per podium driver with the top reasons and a strength bar.
    table: rows with driver, name, constructor (first three are used); why: from predictor.reasons."""
    cards = []
    for pos, (_, r) in enumerate(table.head(3).iterrows(), start=1):
        team_name, color = team_info(r["constructor"])
        lines = "".join(
            f'<div class="pp-why"><div class="t">{html.escape(x["text"])}</div>'
            f'<div class="bar"><span style="width:{max(8, int(100 * x["size"]))}%;background:{color}"></span></div></div>'
            for x in why.get(r["driver"], []))
        cards.append(f'<div class="pp-whycard" style="border-top-color:{color}"><div class="h"><b>P{pos}</b> '
                     f'{html.escape(r["name"])}<small>{team_name}</small></div>{lines}</div>')
    st.markdown(f'<div class="pp-whys">{"".join(cards)}</div>', unsafe_allow_html=True)


def stat_strip(tiles):
    """A row of number tiles. tiles = [(label, value, small text, red?)]."""
    body = "".join(f'<div class="pp-stat"><div class="k">{k}</div><div class="v{" red" if red else ""}">{v}</div>'
                   f'<div class="s">{s}</div></div>' for k, v, s, red in tiles)
    st.markdown(f'<div class="pp-stats{" four" if len(tiles) == 4 else ""}">{body}</div>', unsafe_allow_html=True)


def teaser_podium(note):
    """A greyed-out podium with question marks, before our model has locked in its pick."""
    parts = []
    for pos, cls in ((2, "p2"), (1, "p1"), (3, "p3")):
        parts.append(f'<div class="pp-place"><div class="pp-info" style="opacity:1;animation:none">'
                     f'<div class="pp-name" style="color:var(--pp-muted)">?</div></div>'
                     f'<div class="pp-block {cls} pp-ghost" style="transform:none;animation:none">P{pos}</div></div>')
    st.markdown(f'<div class="pp-podium">{"".join(parts)}</div><p class="pp-tease">{html.escape(note)}</p>',
                unsafe_allow_html=True)


def empty_note(text):
    st.markdown(f'<div class="pp-empty">{text}</div>', unsafe_allow_html=True)
