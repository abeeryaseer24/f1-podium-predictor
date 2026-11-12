"""On This Day: what happened in Formula 1 on today's date, in every season since 1950.

The races come first and stay first, because that is the whole question the page
answers. Everything underneath is extra: the seasons that ended on this date, the
drivers who started their first Grand Prix on it, and the ones who won for the first
time.

The page is drawn as a race poster rather than in the app's usual red, and it keeps
that look in both themes on purpose: a poster is a picture, not a panel.
"""
import calendar
from datetime import date

import streamlit as st

from app_archive import require_history
from archive import on_this_day_full, race_dates
from cards import cards_css
from style import empty_note, team_info
from ui_kit import esc, fade, kit_css, section

cards_css()
kit_css()
require_history()

# A quieter palette than the rest of the app: midnight blue through violet, with amber
# for the things that matter. Easier on the eye than red on black for a page of reading.
INK = "#f3f1ea"
DIM = "#a7a3bd"
AMBER = "#f0b429"
ICE = "#6fd6e8"

POSTER_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
.otd{--ink:#f3f1ea;--dim:#a7a3bd;--amber:#f0b429;--ice:#6fd6e8;--edge:rgba(255,255,255,.12)}
.otd-hero{position:relative;overflow:hidden;border-radius:22px;padding:30px 28px 26px;
  margin:.2rem 0 1.3rem;border:1px solid rgba(255,255,255,.12);
  background:radial-gradient(900px 420px at 12% -20%,#3a2b63 0%,transparent 62%),
             radial-gradient(700px 400px at 95% 120%,#123b4d 0%,transparent 60%),
             linear-gradient(145deg,#141033 0%,#0c1226 55%,#090a16 100%)}
.otd-hero .grain{position:absolute;inset:0;opacity:.30;
  background-image:repeating-conic-gradient(rgba(255,255,255,.05) 0 25%,transparent 0 50%);
  background-size:22px 22px}
.otd-hero .streak{position:absolute;left:-10%;width:120%;height:2px;
  background:linear-gradient(90deg,transparent,rgba(240,180,41,.55),transparent);filter:blur(1px)}
.otd-hero .inner{position:relative;z-index:2}
.otd-hero .eyebrow{font-family:Inter,sans-serif;font-size:.74rem;font-weight:700;
  letter-spacing:3px;text-transform:uppercase;color:var(--amber);margin-bottom:.2rem}
.otd-hero h2{font-family:'Bebas Neue','Saira Condensed',sans-serif;font-weight:400;
  font-size:clamp(3rem,13vw,6.6rem);line-height:.88;letter-spacing:2px;margin:0;
  color:var(--ink);text-shadow:0 10px 40px rgba(0,0,0,.6)}
.otd-hero h2 span{color:var(--amber)}
.otd-hero .lead{margin:.7rem 0 0;color:var(--dim);font-size:1rem;line-height:1.55;max-width:60ch}
.otd-hero .tally{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
.otd-hero .tally div{padding:8px 14px;border-radius:12px;background:rgba(255,255,255,.06);
  border:1px solid var(--edge);min-width:92px}
.otd-hero .tally b{display:block;font-family:'Bebas Neue','Saira Condensed',sans-serif;
  font-size:1.9rem;line-height:1;color:var(--ink);letter-spacing:1px}
.otd-hero .tally small{color:var(--dim);font-size:.66rem;text-transform:uppercase;letter-spacing:1px}

.otd-races{display:flex;flex-direction:column;gap:14px;margin:.2rem 0 1.4rem}
.otd-race{position:relative;overflow:hidden;border-radius:18px;padding:18px 20px 16px;
  border:1px solid rgba(255,255,255,.11);
  background:linear-gradient(150deg,#161335 0%,#0d1124 60%,#0a0b16 100%)}
.otd-race .wash{position:absolute;inset:0;z-index:0}
.otd-race .yr{position:absolute;right:16px;top:-6px;z-index:0;
  font-family:'Bebas Neue','Saira Condensed',sans-serif;font-size:6rem;line-height:1;
  letter-spacing:2px;opacity:.11;color:#fff}
.otd-race > .body{position:relative;z-index:1}
.otd-race .top{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.otd-race .season{font-family:'Bebas Neue','Saira Condensed',sans-serif;font-size:2.3rem;
  line-height:1;letter-spacing:2px;color:var(--amber)}
.otd-race h4{font-family:'Bebas Neue','Saira Condensed',sans-serif;font-weight:400;
  font-size:1.75rem;letter-spacing:1.5px;margin:0;color:var(--ink);line-height:1.05}
.otd-race .where{color:var(--dim);font-size:.84rem;margin:.3rem 0 .85rem}
.otd-race .podium{display:flex;flex-direction:column;gap:7px}
.otd-race .slot{display:grid;grid-template-columns:1.5rem 4px minmax(0,1fr) auto;
  align-items:center;gap:10px;padding:7px 11px;border-radius:10px;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.07)}
.otd-race .slot.p1{background:linear-gradient(90deg,rgba(240,180,41,.16),rgba(240,180,41,.03));
  border-color:rgba(240,180,41,.40)}
.otd-race .slot .n{font-family:'Bebas Neue','Saira Condensed',sans-serif;font-size:1.2rem;
  text-align:center;color:var(--dim);letter-spacing:1px}
.otd-race .slot.p1 .n{color:var(--amber)}
.otd-race .slot .stripe{width:4px;height:22px;border-radius:2px}
.otd-race .slot .nm{min-width:0;display:flex;flex-direction:column}
.otd-race .slot .nm b{color:var(--ink);font-weight:600;font-size:.96rem;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.otd-race .slot .nm small{color:var(--dim);font-size:.76rem;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.otd-race .slot .tail{color:var(--dim);font-size:.72rem;text-transform:uppercase;
  letter-spacing:.8px;white-space:nowrap}
.otd-race .foot{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}
.otd-race .foot span{font-size:.72rem;letter-spacing:.5px;color:var(--dim);
  padding:3px 9px;border-radius:999px;border:1px solid rgba(255,255,255,.12)}

.otd-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;
  margin:.2rem 0 1.3rem}
.otd-item{display:grid;grid-template-columns:3.1rem 4px minmax(0,1fr);gap:10px;
  align-items:center;padding:11px 14px;border-radius:12px;background:var(--pp-panel);
  border:1px solid var(--pp-border)}
.otd-item .y{font-family:'Bebas Neue','Saira Condensed',sans-serif;font-size:1.35rem;
  color:var(--pp-red);letter-spacing:1px}
.otd-item .s{width:4px;height:26px;border-radius:2px}
.otd-item b{display:block;font-weight:600;color:var(--pp-text);font-size:.93rem;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.otd-item small{color:var(--pp-muted);font-size:.78rem;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}

@media (max-width:640px){
  .otd-hero{padding:22px 18px 20px;border-radius:18px}
  .otd-hero .tally div{min-width:74px;padding:7px 11px}
  .otd-hero .tally b{font-size:1.5rem}
  .otd-race{padding:15px 14px 13px}
  .otd-race .yr{font-size:3.4rem;right:8px;opacity:.07}
  .otd-race .season{font-size:1.8rem}
  .otd-race h4{font-size:1.3rem}
  .otd-race .slot{grid-template-columns:1.2rem 4px minmax(0,1fr) auto;gap:8px;padding:6px 9px}
  .otd-race .slot .tail{display:none}
}
</style>"""

st.markdown(POSTER_CSS, unsafe_allow_html=True)

# ---------- which date ----------

today = date.today()
if "otd_month" not in st.session_state:
    st.session_state.otd_month = today.month
    st.session_state.otd_day = today.day

month = int(st.session_state.otd_month)
day = int(st.session_state.otd_day)
pretty = f"{day} {calendar.month_name[month]}"

found = on_this_day_full(month, day)
races = found["races"]

# ---------- the poster ----------

streaks = "".join(f'<div class="streak" style="top:{top}%"></div>' for top in (26, 58, 81))
if races:
    newest, oldest = races[0], races[-1]
    span = (f'{oldest["season"]}' if oldest["season"] == newest["season"]
            else f'{oldest["season"]} to {newest["season"]}')
    many = len(races) != 1
    lead = (f'{len(races)} world championship Grand Prix{"es" if many else ""} '
            f'{"have" if many else "has"} been run on {esc(pretty)}'
            f'{", between " + span.replace(" to ", " and ") if " to " in span else ", in " + span}.')
    tally = [(len(races), "races"),
             (len({r["winner"] for r in races}), "winners"),
             (len({r["team"] for r in races}), "teams"),
             (newest["season"], "most recent")]
    if oldest["season"] != newest["season"]:
        tally.append((oldest["season"], "oldest"))
else:
    lead = (f'No Grand Prix has ever been run on {esc(pretty)}. There are only about '
            f'twenty-four race days in a year, so most dates are quiet ones.')
    tally = []

tally_html = "".join(f"<div><b>{v}</b><small>{esc(l)}</small></div>" for v, l in tally)
day_text, month_text = f"{day}", calendar.month_name[month].upper()
st.markdown(
    f'<div class="otd"><div class="otd-hero">{streaks}<div class="grain"></div>'
    f'<div class="inner"><div class="eyebrow">On this day in Formula 1</div>'
    f'<h2>{day_text} <span>{esc(month_text)}</span></h2>'
    f'<p class="lead">{lead}</p>'
    f'<div class="tally">{tally_html}</div></div></div></div>',
    unsafe_allow_html=True)

# ---------- the races themselves, first and always ----------


def place_line(race):
    """Where the race was held, in words rather than an id."""
    bits = [race.get("circuit_name") or "", race.get("locality") or "",
            race.get("country") or ""]
    seen, out = set(), []
    for bit in bits:
        if bit and bit not in seen:
            seen.add(bit)
            out.append(bit)
    return " · ".join(out)


if races:
    blocks = []
    for race in races:
        _, colour = team_info(race["team_id"])
        slots = []
        for place in race["podium"]:
            _, slot_colour = team_info(place["team_id"])
            tail = ""
            if place["position"] == 1 and race["from_grid"]:
                tail = f'<div class="tail">from P{race["from_grid"]}</div>'
            slots.append(
                f'<div class="slot p{place["position"]}">'
                f'<div class="n">{place["position"]}</div>'
                f'<div class="stripe" style="background:{slot_colour}"></div>'
                f'<div class="nm"><b>{esc(place["driver"])}</b>'
                f'<small>{esc(place["team"])}</small></div>{tail}</div>')
        foot = [f'Round {race["round"]}',
                f'{race["starters"]} starters',
                f'{race["finishers"]} finished']
        if race["finale"]:
            foot.append("Season finale")
        foot_html = "".join(f"<span>{esc(f)}</span>" for f in foot)
        wash = (f'background:linear-gradient(110deg,{fade(colour, .24)} 0%,'
                f'{fade(colour, .02)} 58%)')
        blocks.append(
            f'<div class="otd-race"><div class="wash" style="{wash}"></div>'
            f'<div class="yr">{race["season"]}</div><div class="body">'
            f'<div class="top"><div class="season">{race["season"]}</div>'
            f'<h4>{esc(race["race_name"])}</h4></div>'
            f'<div class="where">{esc(place_line(race))}</div>'
            f'<div class="podium">{"".join(slots)}</div>'
            f'<div class="foot">{foot_html}</div></div></div>')
    st.markdown(f'<div class="otd"><div class="otd-races">{"".join(blocks)}</div></div>',
                unsafe_allow_html=True)
else:
    # Rather than leaving the reader stuck, offer the nearest date that did hold a race.
    counts = race_dates()
    if counts:
        def distance(key):
            m, d = (int(part) for part in key.split("-"))
            gap = abs((date(2001, m, d) - date(2001, month, day)).days)
            return min(gap, 365 - gap)
        nearest = min(counts, key=distance)
        near_month, near_day = (int(part) for part in nearest.split("-"))
        empty_note(f'The nearest race date is {near_day} '
                   f'{calendar.month_name[near_month]}, with {counts[nearest]} '
                   f'Grand Prix{"es" if counts[nearest] != 1 else ""} on it.')
        if st.button(f"Show {near_day} {calendar.month_name[near_month]}",
                     type="primary"):
            st.session_state.otd_month, st.session_state.otd_day = near_month, near_day
            st.rerun()

# ---------- pick another date ----------

section("Another date",
        "Every day of the year is in here. Tap your way to a birthday, a wedding "
        "anniversary or a Sunday in the middle of a season.")
month_names = list(calendar.month_name)[1:]
left, middle, right = st.columns([2, 1, 1], vertical_alignment="bottom")
with left:
    chosen_month = st.selectbox("Month", month_names, index=month - 1, key="otd_month_pick")
with middle:
    days = calendar.monthrange(2024, month_names.index(chosen_month) + 1)[1]
    chosen_day = st.selectbox("Day", list(range(1, days + 1)),
                              index=min(day, days) - 1, key="otd_day_pick")
with right:
    back_to_today = st.button("Today", width="stretch")

new_month = month_names.index(chosen_month) + 1
if back_to_today:
    new_month, chosen_day = today.month, today.day
if (new_month, chosen_day) != (month, day):
    st.session_state.otd_month, st.session_state.otd_day = new_month, chosen_day
    st.rerun()

# ---------- the extras ----------


def small_list(items, title, blurb, line):
    if not items:
        return
    section(title, blurb)
    body = []
    for item in items:
        _, colour = team_info(item.get("team_id", ""))
        top, bottom = line(item)
        body.append(f'<div class="otd-item"><div class="y">{item["season"]}</div>'
                    f'<div class="s" style="background:{colour}"></div>'
                    f'<div><b>{esc(top)}</b><small>{esc(bottom)}</small></div></div>')
    st.markdown(f'<div class="otd"><div class="otd-list">{"".join(body)}</div></div>',
                unsafe_allow_html=True)


small_list(found["finales"], "Seasons that ended on this date",
           "The last round of the year. Whoever is named here was champion when the "
           "flag fell, whether it was settled that afternoon or weeks earlier.",
           lambda i: (i["champion"] or i["race_name"],
                      f'{i["race_name"]} · champion for {i["team"]}' if i["champion"]
                      else "Final round"))

small_list(found["first_wins"], "First career win on this date",
           "The afternoon these drivers won a Grand Prix for the first time.",
           lambda i: (i["driver"], f'{i["race_name"]} · {i["team"]}'))

small_list(found["debuts"], "First Grand Prix on this date",
           "Drivers who started their very first world championship race on this day.",
           lambda i: (i["driver"], f'{i["race_name"]} · {i["team"]}'))
