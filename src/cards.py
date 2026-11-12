"""The look of the Teams and Drivers pages: tappable cards, and a profile page painted
in the team's own colour.

The profile background is the team colour, not the usual app background. A photo can sit
behind it (data/team_photos/<team id>.jpg) and everything written on top sits on frosted
glass, so the words stay readable whatever the photo looks like.
"""
import base64
import html
from functools import lru_cache

import streamlit as st

from style import team_info
from teaminfo import photo_path

CARD_HEIGHT = 190


# ---------- small colour helpers ----------

def _rgb(colour):
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))


def mix(colour_a, colour_b, amount):
    """Blend two colours. amount = 0 gives the first, 1 gives the second."""
    a, b = _rgb(colour_a), _rgb(colour_b)
    out = tuple(round(x + (y - x) * amount) for x, y in zip(a, b))
    return "#%02x%02x%02x" % out


def rgba(colour, alpha):
    r, g, b = _rgb(colour)
    return f"rgba({r},{g},{b},{alpha})"


def brightness(colour):
    """0 (black) to 1 (white). Used to decide whether text on this colour should be dark."""
    r, g, b = _rgb(colour)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def ink(colour):
    """Black or white, whichever can be read on top of this colour."""
    return "#15151e" if brightness(colour) > 0.6 else "#ffffff"


def accent(colour, dark):
    """A version of the team colour that can be read as text on the page background."""
    if dark:
        return colour if brightness(colour) > 0.35 else mix(colour, "#ffffff", 0.35)
    return colour if brightness(colour) < 0.62 else mix(colour, "#000000", 0.38)


# ---------- the photo behind a team profile ----------

@lru_cache(maxsize=24)
def _photo_data(path_text, modified_time):
    data = base64.b64encode(open(path_text, "rb").read()).decode("ascii")
    suffix = path_text.rsplit(".", 1)[-1].lower()
    kind = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    return f"data:image/{kind};base64,{data}"


def photo_url(team_id):
    """The team's photo as something CSS can use, or None if there isn't one yet."""
    path = photo_path(team_id)
    if path is None:
        return None
    try:
        return _photo_data(str(path), path.stat().st_mtime)
    except Exception:
        return None


# ---------- CSS ----------

CARDS_CSS = """<style>
.pp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;margin:.4rem 0 .2rem}
.pp-card{position:relative;border-radius:16px;padding:16px 16px 14px;overflow:hidden;border:1px solid var(--pp-border);background:var(--pp-panel);min-height:150px;display:flex;flex-direction:column;justify-content:space-between}
.pp-card .wash{position:absolute;inset:0;z-index:0;background:var(--card-wash)}
/* The team name ghosted behind the card. It is centred on the right edge, so it bleeds
   off the side the way a watermark should instead of being sliced across the top, and
   it stays faint enough to read as texture rather than words. */
.pp-card .mark{position:absolute;right:-14px;top:50%;transform:translateY(-50%);z-index:0;font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:3.4rem;line-height:1;letter-spacing:-2px;opacity:.09;white-space:nowrap;text-transform:uppercase}
.pp-card .body{position:relative;z-index:1}
.pp-card .rank{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:.95rem;letter-spacing:1px;opacity:.75}
.pp-card h4{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.65rem;letter-spacing:.5px;margin:.1rem 0 .3rem;line-height:1.05;text-transform:uppercase}
.pp-card .line{color:var(--pp-muted);font-size:.86rem;line-height:1.4}
.pp-card .nums{position:relative;z-index:1;display:flex;gap:14px;margin-top:10px}
.pp-card .nums div{display:flex;flex-direction:column}
.pp-card .nums b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.4rem;line-height:1}
.pp-card .nums small{color:var(--pp-muted);font-size:.68rem;text-transform:uppercase;letter-spacing:.5px}
.pp-card .bar{position:absolute;left:0;top:0;bottom:0;width:6px;z-index:1}

/* frosted glass panels, used on the team profile */
.pp-glass{position:relative;z-index:1;border-radius:16px;padding:18px 20px;margin-bottom:14px;background:var(--glass-bg);border:1px solid var(--glass-line);backdrop-filter:blur(16px) saturate(130%);-webkit-backdrop-filter:blur(16px) saturate(130%);box-shadow:0 10px 30px rgba(0,0,0,.18)}
.pp-glass h4{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.1rem;letter-spacing:1px;text-transform:uppercase;margin:0 0 .6rem;color:var(--pp-muted)}
.pp-glass .kv{display:grid;grid-template-columns:minmax(120px,auto) 1fr;gap:6px 18px;font-size:.95rem}
.pp-glass .kv span{color:var(--pp-muted)}
.pp-glass .kv b{font-weight:600;color:var(--pp-text)}

/* the big header at the top of a team or driver profile */
.pp-crest{position:relative;z-index:1;border-radius:20px;overflow:hidden;margin:.2rem 0 1rem;border:1px solid var(--glass-line);min-height:170px;display:flex;align-items:flex-end;background:var(--crest-bg)}
.pp-crest .shot{position:absolute;inset:0;background-size:cover;background-position:center;filter:saturate(115%)}
/* The two generated layers that stand in for a photograph: a tinted CSS texture and
   the page's own data drawn as a line. Both sit under the veil, so the words on top
   stay readable whatever they look like. See backdrop.py. */
.pp-crest .pp-weave{position:absolute;inset:0;z-index:0}
.pp-crest .pp-trace{position:absolute;inset:0;width:100%;height:100%;z-index:0}
.pp-crest .pp-track{position:absolute;right:3%;top:6%;height:88%;width:auto;max-width:52%;z-index:0}
.pp-crest .pp-shade{position:absolute;inset:0;z-index:0}
.pp-crest .veil{position:absolute;inset:0;background:var(--crest-veil)}
.pp-crest .word{position:absolute;right:-10px;top:-18px;font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:7rem;line-height:1;opacity:.08;text-transform:uppercase;letter-spacing:-3px;white-space:nowrap}
.pp-crest .inner{position:relative;z-index:2;padding:22px 24px;width:100%}
.pp-crest .eyebrow{font-size:.8rem;font-weight:600;letter-spacing:2px;text-transform:uppercase;opacity:.85}
.pp-crest h2{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:clamp(2rem,5vw,3rem);text-transform:uppercase;letter-spacing:1px;margin:.1rem 0 .3rem;line-height:1;max-width:66%}
.pp-crest p{margin:0;font-size:.95rem;opacity:.9;max-width:62ch}
.pp-crest .pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.pp-crest .pill{padding:5px 12px;border-radius:999px;font-size:.82rem;font-weight:600;background:var(--pill-bg);border:1px solid var(--glass-line)}

/* a row of big numbers */
.pp-figs{position:relative;z-index:1;display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin:0 0 14px}
.pp-fig{border-radius:14px;padding:12px 14px;background:var(--glass-bg);border:1px solid var(--glass-line);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.pp-fig b{display:block;font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:2rem;line-height:1.05;color:var(--pp-text)}
.pp-fig small{color:var(--pp-muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.6px}

/* a simple timeline, used for a team's achievements */
.pp-time{position:relative;z-index:1;border-left:3px solid var(--time-line);margin:.2rem 0 .6rem;padding-left:18px}
.pp-time .item{position:relative;padding-bottom:16px}
.pp-time .item::before{content:"";position:absolute;left:-26px;top:5px;width:12px;height:12px;border-radius:50%;background:var(--time-dot);border:2px solid var(--pp-bg)}
.pp-time .yr{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.2rem;color:var(--pp-text)}
.pp-time .txt{color:var(--pp-muted);font-size:.92rem;line-height:1.45}

.pp-h2h{display:flex;flex-direction:column;gap:10px;margin:.3rem 0 1rem}
.pp-h2hrow{background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:14px;padding:12px 16px}
.pp-h2hrow .top{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:4px}
.pp-h2hrow .top b{font-weight:600;color:var(--pp-text)}
.pp-h2hrow .top small{color:var(--pp-muted)}
.pp-h2hbar{display:flex;height:16px;border-radius:8px;overflow:hidden;background:var(--pp-panel2);margin:6px 0 2px}
.pp-h2hbar i{display:block;height:100%;font-style:normal}
.pp-h2hlbl{display:flex;justify-content:space-between;font-size:.78rem;color:var(--pp-muted)}
.pp-note{color:var(--pp-muted);font-size:.86rem;line-height:1.5;margin:.2rem 0 1rem}
@media (max-width:640px){
.pp-crest .pp-track{right:-4%;max-width:56%;opacity:.8}
.pp-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.pp-card{padding:12px 12px 10px;min-height:128px}
.pp-card h4{font-size:1.2rem}.pp-card .mark{font-size:2.3rem;right:-10px}
.pp-card .nums{gap:9px}
.pp-card .nums b{font-size:1.1rem}
.pp-card .nums small{font-size:.58rem;letter-spacing:.2px}
.pp-crest .word{font-size:4rem}.pp-crest{min-height:140px}
.pp-crest h2{max-width:100%}
.pp-fig b{font-size:1.5rem}
}
</style>"""


def cards_css():
    """Put the card and profile styles on the page. Safe to call more than once."""
    st.markdown(CARDS_CSS, unsafe_allow_html=True)


# ---------- painting a page in a team's colour ----------

def team_theme(colour, photo=None):
    """Repaint the whole page in one team's colour, with their photo behind it if there
    is one. Everything written on top goes on frosted glass so it stays readable."""
    dark = st.session_state.get("dark", True)
    base = "#0b0b10" if dark else "#f6f6f3"
    panel = "#15151e" if dark else "#ffffff"
    tint_a = mix(base, colour, 0.26 if dark else 0.16)
    tint_b = mix(base, colour, 0.08 if dark else 0.05)
    glass = rgba("#000000", 0.42) if dark else rgba("#ffffff", 0.72)
    line = rgba("#ffffff", 0.16) if dark else rgba("#15151e", 0.10)
    veil = (f"linear-gradient(180deg,{rgba(mix(base, colour, .35), .55)} 0%,"
            f"{rgba(base, .88)} 100%)" if dark else
            f"linear-gradient(180deg,{rgba(mix('#ffffff', colour, .35), .55)} 0%,"
            f"{rgba('#ffffff', .86)} 100%)")
    shot = (f'<div class="shot" style="background-image:url(\'{photo}\')"></div>'
            if photo else "")
    css = f"""<style>
.stApp {{ background: linear-gradient(165deg,{tint_a} 0%,{tint_b} 48%,{base} 100%) fixed !important; }}
:root {{ --pp-red: {accent(colour, dark)};
  --glass-bg: {glass}; --glass-line: {line}; --pill-bg: {rgba(colour, .22)};
  --crest-bg: linear-gradient(120deg,{mix(base, colour, .55)},{mix(base, colour, .18)});
  --crest-veil: {veil}; --time-line: {rgba(colour, .45)}; --time-dot: {colour};
  --pp-panel: {rgba(panel, .66)}; }}
.pp-glow {{ background: radial-gradient(circle,{rgba(colour, .22)},transparent 70%) !important; }}
.pp-line {{ background: linear-gradient(90deg,transparent,{colour} 45%,transparent) !important;
  box-shadow: 0 0 12px {rgba(colour, .5)} !important; }}
</style>"""
    st.markdown(css, unsafe_allow_html=True)
    return shot


# ---------- cards ----------

def team_card(team_id, rank=None, lines=(), numbers=()):
    """One team's card. numbers = [(value, label), ...]"""
    name, colour = team_info(team_id)
    dark = st.session_state.get("dark", True)
    wash = f"linear-gradient(135deg,{rgba(colour, .30)},{rgba(colour, .04)} 65%)"
    rank_html = f'<div class="rank" style="color:{accent(colour, dark)}">P{rank}</div>' if rank else ""
    line_html = "".join(f'<div class="line">{html.escape(str(t))}</div>' for t in lines)
    nums = "".join(f'<div><b style="color:{accent(colour, dark)}">{v}</b>'
                   f'<small>{html.escape(str(l))}</small></div>' for v, l in numbers)
    return (f'<div class="pp-card" style="--card-wash:{wash};border-color:{rgba(colour, .5)}">'
            f'<div class="wash"></div>'
            f'<div class="mark" style="color:{colour}">{html.escape(name)}</div>'
            f'<div class="bar" style="background:{colour}"></div>'
            f'<div class="body">{rank_html}<h4>{html.escape(name)}</h4>{line_html}</div>'
            f'<div class="nums">{nums}</div></div>')


def driver_card(name, team_id, number=None, rank=None, lines=(), numbers=()):
    """One driver's card, in their team's colour, with their car number behind it."""
    team_name, colour = team_info(team_id)
    dark = st.session_state.get("dark", True)
    wash = f"linear-gradient(135deg,{rgba(colour, .28)},{rgba(colour, .03)} 65%)"
    rank_html = f'<div class="rank" style="color:{accent(colour, dark)}">P{rank}</div>' if rank else ""
    back = html.escape(str(number)) if number else html.escape(team_name)
    line_html = "".join(f'<div class="line">{html.escape(str(t))}</div>' for t in lines)
    nums = "".join(f'<div><b style="color:{accent(colour, dark)}">{v}</b>'
                   f'<small>{html.escape(str(l))}</small></div>' for v, l in numbers)
    return (f'<div class="pp-card" style="--card-wash:{wash};border-color:{rgba(colour, .5)}">'
            f'<div class="wash"></div><div class="mark" style="color:{colour}">{back}</div>'
            f'<div class="bar" style="background:{colour}"></div>'
            f'<div class="body">{rank_html}<h4>{html.escape(name)}</h4>'
            f'<div class="line">{html.escape(team_name)}</div>{line_html}</div>'
            f'<div class="nums">{nums}</div></div>')


def crest(eyebrow, title, blurb, pills, colour, shot=""):
    """The big header at the top of a profile page."""
    pill_html = "".join(f'<div class="pill">{html.escape(str(p))}</div>' for p in pills if p)
    st.markdown(
        f'<div class="pp-crest">{shot}<div class="veil"></div>'
        f'<div class="word" style="color:{colour}">{html.escape(title)}</div>'
        f'<div class="inner"><div class="eyebrow" style="color:{colour}">{html.escape(eyebrow)}</div>'
        f'<h2>{html.escape(title)}</h2>'
        f'<p>{html.escape(blurb or "")}</p>'
        f'<div class="pills">{pill_html}</div></div></div>',
        unsafe_allow_html=True)


def figures(items):
    """A row of big numbers. items = [(value, label), ...]"""
    body = "".join(f'<div class="pp-fig"><b>{v}</b><small>{html.escape(str(l))}</small></div>'
                   for v, l in items)
    st.markdown(f'<div class="pp-figs">{body}</div>', unsafe_allow_html=True)


def glass(title, inner_html):
    """A frosted panel with a heading."""
    head = f"<h4>{html.escape(title)}</h4>" if title else ""
    st.markdown(f'<div class="pp-glass">{head}{inner_html}</div>', unsafe_allow_html=True)


def key_values(pairs):
    """Rows of 'label: value' for inside a glass panel. Blank values are left out."""
    rows = "".join(f"<span>{html.escape(str(k))}</span><b>{html.escape(str(v))}</b>"
                   for k, v in pairs if v not in (None, "", "nan"))
    return f'<div class="kv">{rows}</div>'


def timeline(items):
    """items = [(year, text), ...] oldest first."""
    body = "".join(f'<div class="item"><div class="yr">{html.escape(str(y))}</div>'
                   f'<div class="txt">{html.escape(str(t))}</div></div>' for y, t in items)
    st.markdown(f'<div class="pp-time">{body}</div>', unsafe_allow_html=True)


def head_to_head(title, meta, left_name, right_name, left, right, colour_left, colour_right):
    """A bar split between two drivers, e.g. 12 - 7 in qualifying."""
    total = max(1, left + right)
    return (f'<div class="pp-h2hrow"><div class="top"><b>{html.escape(title)}</b>'
            f'<small>{html.escape(meta)}</small></div>'
            f'<div class="pp-h2hbar"><i style="width:{100 * left / total:.1f}%;background:{colour_left}"></i>'
            f'<i style="width:{100 * right / total:.1f}%;background:{colour_right}"></i></div>'
            f'<div class="pp-h2hlbl"><span>{html.escape(left_name)} {left}</span>'
            f'<span>{right} {html.escape(right_name)}</span></div></div>')


STANDINGS_CSS = """<style>
.pp-tbl{display:flex;flex-direction:column;gap:7px;margin:.4rem 0 1.4rem}
.pp-trow{display:grid;grid-template-columns:2.4rem 6px minmax(0,1fr) auto;align-items:center;gap:12px;padding:11px 16px;background:var(--pp-panel);border:1px solid var(--pp-border);border-radius:12px}
.pp-trow.lead{border-color:var(--pp-red)}
.pp-trow .pos{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.25rem;color:var(--pp-muted);text-align:center}
.pp-trow.lead .pos{color:var(--pp-red)}
.pp-trow .stripe{width:6px;height:34px;border-radius:3px}
.pp-trow .who{display:flex;flex-direction:column;min-width:0}
.pp-trow .who b{font-weight:600;color:var(--pp-text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pp-trow .who small{color:var(--pp-muted);font-size:.82rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pp-trow .figs{display:flex;gap:16px;text-align:right}
.pp-trow .figs div{display:flex;flex-direction:column}
.pp-trow .figs b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.2rem;color:var(--pp-text);line-height:1}
.pp-trow .figs small{color:var(--pp-muted);font-size:.66rem;text-transform:uppercase;letter-spacing:.5px}
@media (max-width:640px){.pp-trow{grid-template-columns:1.9rem 5px minmax(0,1fr) auto;gap:8px;padding:9px 10px}
.pp-trow .figs{gap:9px}.pp-trow .figs b{font-size:1rem}.pp-trow .figs small{font-size:.58rem}
.pp-trow .who b{font-size:.92rem}.pp-trow .who small{font-size:.72rem}}
</style>"""


def standings_rows(rows):
    """A championship table. rows = [(position, colour, title, subtitle, [(value, label)])]"""
    st.markdown(STANDINGS_CSS, unsafe_allow_html=True)
    out = []
    for position, colour, title, subtitle, figs in rows:
        lead = " lead" if position == 1 else ""
        nums = "".join(f"<div><b>{v}</b><small>{html.escape(str(l))}</small></div>"
                       for v, l in figs)
        out.append(f'<div class="pp-trow{lead}"><div class="pos">{position}</div>'
                   f'<div class="stripe" style="background:{colour}"></div>'
                   f'<div class="who"><b>{html.escape(str(title))}</b>'
                   f'<small>{html.escape(str(subtitle))}</small></div>'
                   f'<div class="figs">{nums}</div></div>')
    st.markdown(f'<div class="pp-tbl">{"".join(out)}</div>', unsafe_allow_html=True)


def ordinal(n):
    """1 -> 1st, 2 -> 2nd, 11 -> 11th."""
    n = int(n)
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def note(text):
    st.markdown(f'<p class="pp-note">{text}</p>', unsafe_allow_html=True)
