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
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none; }}
[data-testid="stSidebar"] {{ background: var(--pp-panel); border-right: 1px solid var(--pp-border); }}
.block-container {{ position: relative; z-index: 1; max-width: 1100px; padding-top: 2.5rem; }}

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


def hero():
    st.markdown(
        '<div class="pp-hero"><h1>Podium <span>Predictor</span></h1></div>'
        '<p class="pp-sub">Pick a Formula 1 race and see who the model puts on the podium.</p>',
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