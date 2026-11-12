"""The shared look of every leaderboard, grid and feed in the app.

Streamlit's own st.dataframe is a spreadsheet: grey, cramped, and it clips its last
column on a phone. Nothing here uses it. Everything is plain HTML and CSS built from
the same handful of shapes, so a table of lap times and a table of championships look
like they belong to the same sport:

  league()   a timing tower: position, team colour, name, a bar you can read at a
             glance and a few numbers on the right
  heat()     a grid of teams against races, coloured by value, with the first column
             pinned while the rest scrolls
  feed()     a race-control message feed, grouped by race
  versus()   two people or teams facing each other, one mirrored bar per statistic
  sheet()    a real table when a table is genuinely the right shape, but with a sticky
             header, team colours and no clipped columns
  tap_card() a card you open by tapping anywhere on it, not by a button underneath
  polish()   stops dropdowns swallowing the keyboard, and unsticks chart tooltips

Everything takes its colours from the variables style.py sets, so it follows the light
and dark themes without being told.
"""
import html
import inspect

import streamlit as st

# st.container(key=...) puts an "st-key-<key>" class on the container, which is how a
# card knows which CSS belongs to it. It arrived in Streamlit 1.42; if this app is ever
# run on something older, tap_card falls back to an ordinary button underneath.
CONTAINER_KEYS = "key" in inspect.signature(st.container).parameters

GOLD, SILVER, BRONZE = "#d8b45a", "#b9bcc4", "#b07a4a"
GOOD, FAIR, POOR = "#1fd6a0", "#e8b33a", "#e4544a"


def esc(value):
    return html.escape("" if value is None else str(value))


# ---------- colour helpers ----------

def _rgb(colour):
    colour = str(colour).lstrip("#")
    if len(colour) == 3:
        colour = "".join(c * 2 for c in colour)
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))


def fade(colour, alpha):
    r, g, b = _rgb(colour)
    return f"rgba({r},{g},{b},{alpha})"


def blend(colour_a, colour_b, amount):
    a, b = _rgb(colour_a), _rgb(colour_b)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def scale_colour(fraction, flip=False):
    """0 to 1 along a red → amber → green ramp. flip=True makes 0 the good end."""
    try:
        fraction = min(1.0, max(0.0, float(fraction)))
    except (TypeError, ValueError):
        return POOR
    if flip:
        fraction = 1 - fraction
    if fraction < 0.5:
        return blend(POOR, FAIR, fraction * 2)
    return blend(FAIR, GOOD, (fraction - 0.5) * 2)


# ---------- the stylesheet ----------

KIT_CSS = """<style>
/* ---------- section heading: every table and chart gets one ---------- */
.kt-sec{margin:1.6rem 0 .5rem}
.kt-sec h3{font-family:'Saira Condensed',sans-serif;font-weight:800;text-transform:uppercase;
  letter-spacing:.6px;font-size:1.5rem;margin:0;line-height:1.1;color:var(--pp-text)}
.kt-sec .rule{height:3px;width:52px;border-radius:2px;background:var(--pp-red);margin:.35rem 0 .5rem}
.kt-sec p{margin:0;color:var(--pp-muted);font-size:.92rem;line-height:1.5;max-width:76ch}

/* ---------- the timing tower ---------- */
.kt-lg{display:flex;flex-direction:column;gap:6px;margin:.2rem 0 1.2rem}
.kt-row{position:relative;display:grid;grid-template-columns:2.3rem minmax(0,1fr) auto;
  align-items:center;gap:12px;padding:10px 14px;border-radius:12px;overflow:hidden;
  background:var(--pp-panel);border:1px solid var(--pp-border)}
.kt-row .fill{position:absolute;left:0;top:0;bottom:0;z-index:0;border-radius:12px 0 0 12px}
.kt-row .edge{position:absolute;left:0;top:0;bottom:0;width:4px;z-index:1}
.kt-row > *{position:relative;z-index:2}
.kt-lg.wide .kt-row{grid-template-columns:3.7rem minmax(0,1fr) auto}
.kt-lg.wide .kt-row .pos{font-size:1.35rem;color:var(--pp-red)}
.kt-row .pos{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.2rem;
  text-align:center;color:var(--pp-muted);font-variant-numeric:tabular-nums}
.kt-row.p1 .pos{color:#d8b45a}.kt-row.p2 .pos{color:#b9bcc4}.kt-row.p3 .pos{color:#b07a4a}
.kt-row.p1{border-color:rgba(216,180,90,.55)}
.kt-row .who{min-width:0;display:flex;flex-direction:column;gap:1px}
.kt-row .who b{font-weight:600;font-size:1rem;color:var(--pp-text);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.kt-row .who small{color:var(--pp-muted);font-size:.8rem;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
.kt-row .figs{display:flex;gap:15px;text-align:right}
.kt-row .figs div{display:flex;flex-direction:column;align-items:flex-end}
.kt-row .figs b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.15rem;
  line-height:1.05;color:var(--pp-text);font-variant-numeric:tabular-nums;white-space:nowrap}
.kt-row .figs small{color:var(--pp-muted);font-size:.62rem;text-transform:uppercase;
  letter-spacing:.5px;white-space:nowrap}

/* ---------- chips ---------- */
.kt-chip{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;
  font-size:.72rem;font-weight:700;letter-spacing:.4px;text-transform:uppercase;white-space:nowrap}
.kt-chips{display:flex;flex-wrap:wrap;gap:6px;margin:.1rem 0 .3rem}

/* ---------- the heat grid ---------- */
.kt-heatwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--pp-border);
  border-radius:14px;background:var(--pp-panel);margin:.2rem 0 .5rem}
.kt-heat{border-collapse:separate;border-spacing:0;width:100%;font-size:.82rem}
.kt-heat th,.kt-heat td{padding:0;text-align:center}
.kt-heat thead th{position:sticky;top:0;z-index:3;background:var(--pp-panel2);
  color:var(--pp-muted);font-weight:600;font-size:.68rem;text-transform:uppercase;
  letter-spacing:.4px;padding:9px 6px;white-space:nowrap;border-bottom:1px solid var(--pp-border)}
.kt-heat tbody th{position:sticky;left:0;z-index:2;background:var(--pp-panel);
  text-align:left;padding:0 12px 0 0;white-space:nowrap;
  border-right:1px solid var(--pp-border)}
.kt-heat thead th:first-child{position:sticky;left:0;z-index:4;text-align:left;padding-left:14px}
.kt-heat tbody th .lbl{display:flex;align-items:center;gap:8px;padding:0 0 0 14px;height:34px}
.kt-heat tbody th .dot{width:4px;height:20px;border-radius:2px;flex:none}
.kt-heat tbody th b{font-weight:600;font-size:.86rem;color:var(--pp-text)}
.kt-heat .cell{display:flex;align-items:center;justify-content:center;height:30px;margin:2px;
  border-radius:6px;font-variant-numeric:tabular-nums;font-weight:600;font-size:.78rem}
.kt-heat .none{background:repeating-linear-gradient(45deg,transparent,transparent 4px,
  var(--pp-border) 4px,var(--pp-border) 5px);color:var(--pp-muted);font-size:.7rem}
.kt-key{display:flex;align-items:center;gap:10px;flex-wrap:wrap;color:var(--pp-muted);
  font-size:.78rem;margin:0 0 1.2rem}
.kt-key .ramp{height:9px;width:130px;border-radius:5px}
.kt-key .box{width:16px;height:9px;border-radius:3px;display:inline-block;
  background:repeating-linear-gradient(45deg,transparent,transparent 3px,
  var(--pp-border) 3px,var(--pp-border) 4px);border:1px solid var(--pp-border)}

/* ---------- gained and lost ---------- */
.kt-dv{display:flex;flex-direction:column;gap:5px;margin:.2rem 0 1.2rem}
.kt-dvhead{display:flex;justify-content:space-between;color:var(--pp-muted);font-size:.7rem;
  text-transform:uppercase;letter-spacing:1px;font-weight:600;padding:0 2px 3px}
.kt-dvr{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.5fr) 2.6rem;
  align-items:center;gap:12px;padding:7px 12px;border-radius:10px;
  background:var(--pp-panel);border:1px solid var(--pp-border)}
.kt-dvr .who{min-width:0;display:flex;flex-direction:column}
.kt-dvr .who b{font-weight:600;font-size:.92rem;color:var(--pp-text);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.kt-dvr .who small{color:var(--pp-muted);font-size:.74rem;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.kt-dvr .track{display:grid;grid-template-columns:1fr 2px 1fr;align-items:center;height:14px}
.kt-dvr .side{display:flex;height:100%}
.kt-dvr .side.l{justify-content:flex-end}
.kt-dvr .side i{display:block;height:100%;font-style:normal;border-radius:4px}
.kt-dvr .line{height:18px;background:var(--pp-border)}
.kt-dvr .val{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.1rem;
  text-align:right;font-variant-numeric:tabular-nums}

/* ---------- the message feed ---------- */
.kt-feed{display:flex;flex-direction:column;gap:14px;margin:.2rem 0 1.2rem}
.kt-grp{border:1px solid var(--pp-border);border-radius:14px;background:var(--pp-panel);
  overflow:hidden}
.kt-grp .head{display:flex;align-items:baseline;justify-content:space-between;gap:10px;
  padding:11px 16px;background:var(--pp-panel2);border-bottom:1px solid var(--pp-border)}
.kt-grp .head b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.05rem;
  letter-spacing:.5px;text-transform:uppercase;color:var(--pp-text)}
.kt-grp .head small{color:var(--pp-muted);font-size:.78rem;white-space:nowrap}
.kt-item{display:grid;grid-template-columns:3.4rem minmax(0,1fr);gap:12px;padding:10px 16px;
  border-top:1px solid var(--pp-border)}
.kt-item:first-of-type{border-top:0}
.kt-item .lap{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.05rem;
  color:var(--pp-muted);text-align:right;padding-top:1px;font-variant-numeric:tabular-nums}
.kt-item .lap small{display:block;font-size:.58rem;letter-spacing:.5px;text-transform:uppercase;
  font-family:Inter,sans-serif;font-weight:600;opacity:.75}
.kt-item .body{min-width:0}
.kt-item .line1{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:3px}
.kt-item .who{font-weight:600;color:var(--pp-text);font-size:.9rem}
.kt-item .msg{color:var(--pp-muted);font-size:.85rem;line-height:1.45;word-break:break-word}

/* ---------- head to head ---------- */
.kt-vs{border:1px solid var(--pp-border);border-radius:16px;background:var(--pp-panel);
  padding:16px 18px;margin:.2rem 0 1rem}
.kt-vs .names{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;
  margin-bottom:14px}
.kt-vs .names .n{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.3rem;
  text-transform:uppercase;letter-spacing:.5px;line-height:1.1}
.kt-vs .names .r{text-align:right}
.kt-vs .names .mid{font-size:.72rem;font-weight:700;letter-spacing:2px;color:var(--pp-muted)}
.kt-vsr{margin:0 0 11px}
.kt-vsr .lbl{display:grid;grid-template-columns:1fr auto 1fr;align-items:baseline;gap:8px;
  font-size:.8rem;margin-bottom:4px}
.kt-vsr .lbl b{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1.1rem;
  color:var(--pp-text);font-variant-numeric:tabular-nums}
.kt-vsr .lbl .r{text-align:right}
.kt-vsr .lbl .mid{color:var(--pp-muted);text-transform:uppercase;letter-spacing:.6px;
  font-size:.68rem;font-weight:600;text-align:center}
.kt-vsr .track{display:grid;grid-template-columns:1fr 1fr;gap:3px;height:12px}
.kt-vsr .side{display:flex;height:100%;background:var(--pp-panel2);border-radius:6px;overflow:hidden}
.kt-vsr .side.l{justify-content:flex-end}
.kt-vsr .side i{display:block;height:100%;font-style:normal}
.kt-vsr .side.l i{border-radius:6px 0 0 6px}
.kt-vsr .side.r i{border-radius:0 6px 6px 0}

/* ---------- a real table, done properly ---------- */
.kt-sheetwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--pp-border);
  border-radius:14px;background:var(--pp-panel);margin:.2rem 0 1.2rem}
.kt-sheet{border-collapse:separate;border-spacing:0;width:100%;font-size:.88rem}
.kt-sheet thead th{position:sticky;top:0;z-index:2;background:var(--pp-panel2);
  color:var(--pp-muted);font-weight:600;font-size:.7rem;text-transform:uppercase;
  letter-spacing:.5px;padding:10px 14px;text-align:left;white-space:nowrap;
  border-bottom:1px solid var(--pp-border)}
.kt-sheet thead th.num{text-align:right}
.kt-sheet td{padding:9px 14px;border-top:1px solid var(--pp-border);color:var(--pp-text);
  white-space:nowrap}
.kt-sheet td.num{text-align:right;font-variant-numeric:tabular-nums;
  font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:1rem}
.kt-sheet td.wrap{white-space:normal;min-width:200px;color:var(--pp-muted);line-height:1.45}
.kt-sheet tbody tr:nth-child(even) td{background:var(--pp-panel2)}
.kt-sheet .tag{display:inline-flex;align-items:center;gap:7px}
.kt-sheet .tag i{width:4px;height:16px;border-radius:2px;flex:none;display:block}

/* ---------- a headline state banner ---------- */
.kt-state{display:flex;align-items:center;gap:16px;border-radius:16px;padding:16px 20px;
  margin:.2rem 0 1.1rem;border:1px solid var(--pp-border);background:var(--pp-panel);
  position:relative;overflow:hidden}
.kt-state .glow{position:absolute;inset:0;z-index:0}
.kt-state > *{position:relative;z-index:1}
.kt-state .mark{font-size:2.1rem;line-height:1;flex:none}
.kt-state .txt b{display:block;font-family:'Saira Condensed',sans-serif;font-weight:800;
  font-size:1.45rem;text-transform:uppercase;letter-spacing:.5px;line-height:1.1;
  color:var(--pp-text)}
.kt-state .txt span{color:var(--pp-muted);font-size:.9rem;line-height:1.45}

/* ---------- tappable cards ---------- */
@supports selector(:has(*)){
  div[class*="st-key-pptap-"]{position:relative}
  div[class*="st-key-pptap-"] .stElementContainer:has(> .stButton),
  div[class*="st-key-pptap-"] .element-container:has(> .stButton){
    position:absolute!important;inset:0!important;width:100%!important;height:100%!important;
    margin:0!important;padding:0!important;z-index:5}
  div[class*="st-key-pptap-"] .stButton{height:100%;width:100%;margin:0}
  div[class*="st-key-pptap-"] .stButton > button{width:100%;height:100%;opacity:0;padding:0;
    min-height:0;border:0;background:transparent;cursor:pointer}
  div[class*="st-key-pptap-"] .pp-card{transition:transform .16s ease,box-shadow .16s ease,
    border-color .16s ease}
  div[class*="st-key-pptap-"]:hover .pp-card{transform:translateY(-3px);
    box-shadow:0 16px 34px rgba(0,0,0,.30)}
  div[class*="st-key-pptap-"]:active .pp-card{transform:translateY(-1px)}
}

/* ---------- chart tooltips: never wider than the phone ---------- */
#vg-tooltip-element{max-width:min(78vw,340px)!important;font-size:.8rem!important}

@media (max-width:640px){
  .kt-sec h3{font-size:1.25rem}
  .kt-row{grid-template-columns:1.8rem minmax(0,1fr) auto;gap:8px;padding:9px 10px}
  .kt-lg.wide .kt-row{grid-template-columns:2.9rem minmax(0,1fr) auto}
  .kt-lg.wide .kt-row .pos{font-size:1.1rem}
  .kt-row .figs{gap:10px}
  .kt-row .figs b{font-size:1rem}
  .kt-row .figs small{font-size:.55rem;letter-spacing:.2px}
  .kt-row .who b{font-size:.9rem}.kt-row .who small{font-size:.72rem}
  .kt-vs .names .n{font-size:1.05rem}
  .kt-vsr .lbl b{font-size:.98rem}
  .kt-item{grid-template-columns:2.8rem minmax(0,1fr);gap:9px;padding:9px 12px}
  .kt-dvr{grid-template-columns:minmax(0,1fr) minmax(0,1.1fr) 2.2rem;gap:8px;padding:6px 9px}
  .kt-dvr .who b{font-size:.84rem}.kt-dvr .who small{font-size:.68rem}
  .kt-dvr .val{font-size:.95rem}
  .kt-heat tbody th b{font-size:.78rem}
  .kt-heat .cell{height:26px;font-size:.7rem}
  .kt-state{gap:12px;padding:14px 15px}
  .kt-state .txt b{font-size:1.15rem}
  .kt-state .mark{font-size:1.7rem}
}
</style>"""


def kit_css():
    """Put the shared styles on the page. Safe to call more than once."""
    st.markdown(KIT_CSS, unsafe_allow_html=True)


# ---------- two fixes that need a little JavaScript ----------

POLISH_JS = """
<script>
(function () {
  var doc = window.parent && window.parent.document;
  if (!doc) { return; }

  /* 1. Dropdowns should be tapped, not typed into. Making the input read-only keeps the
        list working but stops the phone keyboard covering half the screen. Any select
        inside something marked data-pp-typing is left alone. */
  function lockSelects() {
    var inputs = doc.querySelectorAll('div[data-baseweb="select"] input');
    for (var i = 0; i < inputs.length; i++) {
      var box = inputs[i];
      if (box.dataset.ppLocked === '1') { continue; }
      if (box.closest('[data-pp-typing]')) { continue; }
      box.dataset.ppLocked = '1';
      box.readOnly = true;
      box.setAttribute('inputmode', 'none');
      box.setAttribute('autocomplete', 'off');
      box.style.caretColor = 'transparent';
      box.style.cursor = 'pointer';
    }
  }

  /* 2. A chart tooltip opened by a tap has no mouse to leave, so it used to sit there
        covering the page. Hide it when the finger goes anywhere else, when the page
        scrolls, and a couple of seconds after it was opened. */
  var timer = null;
  function hideTip() {
    var tip = doc.getElementById('vg-tooltip-element');
    if (tip) { tip.classList.remove('visible'); }
  }
  function armTip() {
    if (timer) { clearTimeout(timer); }
    timer = setTimeout(hideTip, 2600);
  }
  doc.addEventListener('touchstart', function (event) {
    var onChart = event.target && event.target.closest &&
                  event.target.closest('.vega-embed, [data-testid="stVegaLiteChart"]');
    if (onChart) { armTip(); } else { hideTip(); }
  }, true);
  doc.addEventListener('scroll', hideTip, true);

  lockSelects();
  new MutationObserver(lockSelects).observe(doc.body, { childList: true, subtree: true });
})();
</script>
"""


def polish():
    """Tap-only dropdowns and tooltips that let go. Called once, from app.py."""
    st.components.v1.html(POLISH_JS, height=0)


# ---------- headings ----------

def section(title, blurb=""):
    """A heading with a rule under it and one line saying what the thing below is for.
    Nothing in the app should appear without one."""
    text = f"<p>{blurb}</p>" if blurb else ""
    st.markdown(f'<div class="kt-sec"><h3>{esc(title)}</h3><div class="rule"></div>'
                f'{text}</div>', unsafe_allow_html=True)


def chip(text, colour="#8a8a96", solid=False):
    """A small coloured label."""
    if solid:
        style = f"background:{colour};color:#0b0b10"
    else:
        style = f"background:{fade(colour, .16)};color:{colour};box-shadow:inset 0 0 0 1px {fade(colour, .40)}"
    return f'<span class="kt-chip" style="{style}">{esc(text)}</span>'


def chips(items):
    """A row of chips. items = [(text, colour), ...]"""
    body = "".join(chip(t, c) for t, c in items)
    st.markdown(f'<div class="kt-chips">{body}</div>', unsafe_allow_html=True)


def banner(mark, title, text, colour="#e10600"):
    """One loud line of state, for things like a championship being settled."""
    glow = (f"background:linear-gradient(100deg,{fade(colour, .22)},"
            f"{fade(colour, .02)} 62%)")
    st.markdown(
        f'<div class="kt-state" style="border-color:{fade(colour, .5)}">'
        f'<div class="glow" style="{glow}"></div>'
        f'<div class="mark">{mark}</div>'
        f'<div class="txt"><b>{esc(title)}</b><span>{text}</span></div></div>',
        unsafe_allow_html=True)


# ---------- the timing tower ----------

def league(rows, show_position=True, wide_position=False):
    """A ranked list that reads like a timing screen.

    rows = [{"name", "sub", "colour", "bar" (0-1), "figures" [(value, label)],
             "pos", "tag" (html)}, ...]
    wide_position makes room for a year rather than a place.
    The bar is a share of the row's width, so the leader's bar is full and everyone
    else is measured against them without needing to read a single number.
    """
    out = []
    for index, row in enumerate(rows, start=1):
        position = row.get("pos", index)
        colour = row.get("colour") or "#8a8a96"
        share = max(0.0, min(1.0, float(row.get("bar") or 0)))
        medal = f" p{position}" if isinstance(position, int) and position <= 3 else ""
        figs = "".join(f"<div><b>{v}</b><small>{esc(l)}</small></div>"
                       for v, l in row.get("figures", ()))
        sub = f'<small>{esc(row.get("sub", ""))}</small>' if row.get("sub") else ""
        tag = row.get("tag", "")
        pos_cell = (f'<div class="pos">{esc(position)}</div>' if show_position
                    else '<div class="pos"></div>')
        fill = (f'<div class="fill" style="width:{share * 100:.1f}%;'
                f'background:linear-gradient(90deg,{fade(colour, .34)},{fade(colour, .07)})">'
                f'</div>') if share > 0 else ""
        out.append(
            f'<div class="kt-row{medal}">{fill}'
            f'<div class="edge" style="background:{colour}"></div>'
            f'{pos_cell}'
            f'<div class="who"><b>{esc(row["name"])} {tag}</b>{sub}</div>'
            f'<div class="figs">{figs}</div></div>')
    wide = " wide" if wide_position else ""
    st.markdown(f'<div class="kt-lg{wide}">{"".join(out)}</div>', unsafe_allow_html=True)


# ---------- the heat grid ----------

def heat(row_labels, column_labels, cells, legend=("Slower", "Faster"), row_colours=None,
         column_titles=None, missing_label="not measured"):
    """A grid of rows against columns, every cell coloured by how good its value is.

    cells[row][column] is either None, meaning no measurement, or a pair
    (text to print, 0-1 where 1 is the good end).
    """
    colours = row_colours or {}
    titles = column_titles or {}
    head = "".join(f'<th title="{esc(titles.get(c, c))}">{esc(c)}</th>'
                   for c in column_labels)
    missing = False
    body = []
    for label in row_labels:
        stripe = colours.get(label, "#8a8a96")
        line = [f'<th><div class="lbl"><span class="dot" style="background:{stripe}"></span>'
                f'<b>{esc(label)}</b></div></th>']
        for column in column_labels:
            value = cells.get((label, column))
            if value is None:
                missing = True
                line.append('<td><div class="cell none">·</div></td>')
                continue
            text, goodness = value
            tone = scale_colour(goodness)
            line.append(f'<td><div class="cell" style="background:{fade(tone, .20)};'
                        f'color:{tone}">{esc(text)}</div></td>')
        body.append(f"<tr>{''.join(line)}</tr>")
    ramp = f"linear-gradient(90deg,{POOR},{FAIR},{GOOD})"
    gaps = (f'<span style="margin-left:6px"><span class="box"></span> '
            f'{esc(missing_label)}</span>' if missing else "")
    st.markdown(
        f'<div class="kt-heatwrap"><table class="kt-heat"><thead><tr><th></th>{head}</tr>'
        f'</thead><tbody>{"".join(body)}</tbody></table></div>'
        f'<div class="kt-key"><span>{esc(legend[0])}</span>'
        f'<span class="ramp" style="background:{ramp}"></span>'
        f'<span>{esc(legend[1])}</span>{gaps}</div>',
        unsafe_allow_html=True)


# ---------- gained and lost, from a centre line ----------

def diverge(rows, left_label="Lost", right_label="Gained"):
    """Bars growing out of a centre line: losses to the left, gains to the right.

    rows = [{"name", "sub", "colour", "value" (signed), "note"}]
    The longest bar either way sets the scale, so the centre line stays in the middle
    and the two sides stay comparable.
    """
    top = max((abs(float(r["value"])) for r in rows), default=1) or 1
    body = []
    for row in rows:
        value = float(row["value"])
        share = 100 * abs(value) / top
        colour = row.get("colour") or "#8a8a96"
        left = (f'<i style="width:{share:.1f}%;background:{colour}"></i>'
                if value < 0 else "")
        right = (f'<i style="width:{share:.1f}%;background:{colour}"></i>'
                 if value > 0 else "")
        mark = "—" if value == 0 else f"{value:+.0f}"
        tone = ("#1fd6a0" if value > 0 else POOR if value < 0 else "#8a8a96")
        body.append(
            f'<div class="kt-dvr"><div class="who"><b>{esc(row["name"])}</b>'
            f'<small>{esc(row.get("sub", ""))}</small></div>'
            f'<div class="track"><div class="side l">{left}</div>'
            f'<div class="line"></div><div class="side r">{right}</div></div>'
            f'<div class="val" style="color:{tone}">{mark}</div></div>')
    st.markdown(
        f'<div class="kt-dv"><div class="kt-dvhead"><span>&#8592; {esc(left_label)}</span>'
        f'<span>{esc(right_label)} &#8594;</span></div>{"".join(body)}</div>',
        unsafe_allow_html=True)


# ---------- the message feed ----------

def feed(groups):
    """Messages grouped under the race they came from.

    groups = [{"title", "meta", "items": [{"lap", "lap_label", "chip", "colour",
               "who", "text"}]}]
    """
    blocks = []
    for group in groups:
        items = []
        for item in group["items"]:
            colour = item.get("colour", "#8a8a96")
            lap = item.get("lap")
            lap_html = (f'<div class="lap">{esc(lap)}'
                        f'<small>{esc(item.get("lap_label", "lap"))}</small></div>'
                        if lap not in (None, "") else '<div class="lap">—</div>')
            who = f'<span class="who">{esc(item["who"])}</span>' if item.get("who") else ""
            items.append(
                f'<div class="kt-item">{lap_html}<div class="body">'
                f'<div class="line1">{chip(item["chip"], colour)}{who}</div>'
                f'<div class="msg">{esc(item.get("text", ""))}</div></div></div>')
        blocks.append(
            f'<div class="kt-grp"><div class="head"><b>{esc(group["title"])}</b>'
            f'<small>{esc(group.get("meta", ""))}</small></div>{"".join(items)}</div>')
    st.markdown(f'<div class="kt-feed">{"".join(blocks)}</div>', unsafe_allow_html=True)


# ---------- head to head ----------

def versus(left_name, right_name, rows, left_colour="#e10600", right_colour="#27f4d2",
           middle="versus"):
    """Two people facing each other, one mirrored bar per statistic.

    rows = [(label, left value, right value, printed left, printed right)]
    Each bar is measured against the bigger of the two, so the leader's bar is always
    full and the gap is the thing you actually see.
    """
    body = []
    for label, left, right, left_text, right_text in rows:
        top = max(abs(float(left)), abs(float(right)), 1e-9)
        left_share, right_share = 100 * abs(float(left)) / top, 100 * abs(float(right)) / top
        lead_l = left_colour if float(left) >= float(right) else fade(left_colour, .45)
        lead_r = right_colour if float(right) >= float(left) else fade(right_colour, .45)
        body.append(
            f'<div class="kt-vsr"><div class="lbl"><b>{esc(left_text)}</b>'
            f'<span class="mid">{esc(label)}</span><b class="r">{esc(right_text)}</b></div>'
            f'<div class="track">'
            f'<div class="side l"><i style="width:{left_share:.1f}%;background:{lead_l}"></i></div>'
            f'<div class="side r"><i style="width:{right_share:.1f}%;background:{lead_r}"></i></div>'
            f'</div></div>')
    st.markdown(
        f'<div class="kt-vs"><div class="names">'
        f'<div class="n" style="color:{left_colour}">{esc(left_name)}</div>'
        f'<div class="mid">{esc(middle.upper())}</div>'
        f'<div class="n r" style="color:{right_colour}">{esc(right_name)}</div></div>'
        f'{"".join(body)}</div>', unsafe_allow_html=True)


# ---------- a table, when a table really is the right shape ----------

def sheet(columns, rows):
    """A readable table. columns = [(heading, kind)] where kind is "text", "num",
    "wrap" or "tag"; a "tag" cell is the pair (colour, text)."""
    head = "".join(f'<th class="{"num" if kind == "num" else ""}">{esc(name)}</th>'
                   for name, kind in columns)
    body = []
    for row in rows:
        cells = []
        for (_, kind), value in zip(columns, row):
            if kind == "tag":
                colour, text = value
                cells.append(f'<td><span class="tag"><i style="background:{colour}"></i>'
                             f'{esc(text)}</span></td>')
            else:
                cells.append(f'<td class="{kind if kind != "text" else ""}">{esc(value)}</td>')
        body.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(f'<div class="kt-sheetwrap"><table class="kt-sheet"><thead><tr>{head}</tr>'
                f'</thead><tbody>{"".join(body)}</tbody></table></div>',
                unsafe_allow_html=True)


# ---------- a card you open by tapping it ----------

def tap_card(card_html, key, label="Open"):
    """Draw a card and return True if it was tapped.

    The button is stretched over the whole card and made invisible, so the card itself
    is the thing you press. On a browser too old for :has(), the button simply shows
    underneath as an ordinary button and everything still works.
    """
    if CONTAINER_KEYS:
        with st.container(key=f"pptap-{key}"):
            st.markdown(card_html, unsafe_allow_html=True)
            return st.button(label, key=f"pptapb-{key}", width="stretch")
    st.markdown(card_html, unsafe_allow_html=True)
    return st.button(label, key=f"pptapb-{key}", width="stretch")
