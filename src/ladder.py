"""The Ladder: results archive for the feeder series below Formula 1.

THE SOURCE. There is no free results API for F2, F3 or F1 Academy like Jolpica is for F1, and the series'
own sites don't allow automated copying. Wikipedia's season articles carry the full championship tables
(every race's result for every driver, and the teams' table) under CC BY-SA 4.0, so this reads them through
the free MediaWiki API, once per season, politely (one request a second), and keeps the raw pages in
cache/ladder/ (not committed). Pages that carry Wikipedia content credit it.

THE SERIES, newest name first:
  F2   FIA Formula 2 (2017-) and its predecessor GP2 (2005-2016)
  F3   FIA Formula 3 (2019-) and GP3 (2010-2018)
  F1A  F1 Academy (2023-)

SAVED (data/ladder/):
  standings.csv  series, season, pos, driver, team, points, races, wins, podiums
  results.csv    series, season, race (e.g. "BHR SR"), driver, result ("1", "Ret", ...), finish (number or blank)
  teams.csv      series, season, pos, team, points
  superlicence.csv  series, p1 ... p10: FIA Super Licence points by championship position (from Wikipedia's
                    "FIA Super Licence" article, which cites the FIA's Supplement 1)

  python src/ladder.py            fetch anything missing, then parse everything
  python src/ladder.py --parse    parse the cached pages only
  python src/ladder.py --refresh  also re-read the current season's pages
"""
import argparse
import io
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "ladder"
OUT = ROOT / "data" / "ladder"
API = "https://en.wikipedia.org/w/api.php"
HEAD = {"User-Agent": "F1PodiumPredictor/1.0 (open-source educational project)"}
LAST = __import__("datetime").date.today().year      # the season running now

SEASONS = (
    [("F2", y, f"{y} GP2 Series", "GP2") for y in range(2005, 2017)]
    + [("F2", y, f"{y} FIA Formula 2 Championship", "F2") for y in range(2017, LAST + 1)]
    + [("F3", y, f"{y} GP3 Series", "GP3") for y in range(2010, 2019)]
    + [("F3", y, f"{y} FIA Formula 3 Championship", "F3") for y in range(2019, LAST + 1)]
    + [("F1A", y, f"{y} F1 Academy season", "F1 Academy") for y in range(2023, LAST + 1)]
)
SERIES_NAMES = {"F2": "Formula 2", "F3": "Formula 3", "F1A": "F1 Academy"}


# ---------- fetching ----------

def fetch(title, refresh=False):
    path = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", title) + ".html")
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    params = {"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": 2, "redirects": 1}
    for attempt in range(5):
        try:
            r = requests.get(API, params=params, headers=HEAD, timeout=60)
            if r.status_code == 200:
                j = r.json()
                if "error" in j:
                    return None
                html = j["parse"]["text"]
                CACHE.mkdir(parents=True, exist_ok=True)
                path.write_text(html, encoding="utf-8")
                time.sleep(1.0)
                return html
        except requests.RequestException:
            pass
        time.sleep(3 * (attempt + 1))
    return None


# ---------- parsing ----------

def tables(html):
    html = re.sub(r'(rowspan|colspan)="(\d+)[^"]*"', r'\1="\2"', html)     # a few pages have rowspan="2,"
    html = re.sub(r"<sup[^>]*>.*?</sup>", "", html, flags=re.S)            # footnote markers
    try:
        return pd.read_html(io.StringIO(html))
    except ValueError:
        return []


def flat(columns):
    out = []
    for c in columns:
        if isinstance(c, tuple):
            parts = [str(p) for p in c if str(p) and not str(p).startswith("Unnamed")]
            uniq = list(dict.fromkeys(parts))
            out.append(" ".join(uniq))
        else:
            out.append(str(c))
    return out


def clean_name(text):
    text = re.sub(r"\[.*?\]", "", str(text))
    text = re.sub(r"[†‡*]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def name_key(name):
    """The same person however a page writes them: 'Zhou Guanyu' and 'Guanyu Zhou', accents or not."""
    import unicodedata
    plain = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    return " ".join(sorted(re.findall(r"[a-z]+", plain)))


def finish(cell):
    m = re.match(r"\s*(\d+)", str(cell))
    return int(m.group(1)) if m else None


def number(cell):
    m = re.search(r"-?\d+(?:\.\d+)?", str(cell).replace(",", "."))
    return float(m.group(0)) if m else 0.0


def championship(tabs, who):
    """The drivers' (who="Driver") or teams' (who="Team") table: Pos., name, one column per race, Points.
    Returns (table, race columns, points column). Some pages end the table with empty columns, put the
    points elsewhere, or add a car-number column to the teams' table."""
    for t in tabs:
        cols = flat(t.columns)
        if len(cols) < 4 or not cols[0].startswith("Pos") or not cols[1].startswith(who):
            continue
        t = t.copy()
        t.columns = [f"{c}#{i}" for i, c in enumerate(cols)]          # names can repeat
        names = dict(zip(t.columns, cols))
        while len(t.columns) > 3 and (t[t.columns[-1]].isna().all() or not names[t.columns[-1]].strip()
                                      and t[t.columns[-1]].astype(str).str.strip().isin(["", "nan"]).all()):
            t = t.drop(columns=t.columns[-1])
        pts = [c for c in t.columns if names[c].lower().startswith(("point", "pts"))]
        points = pts[-1] if pts else t.columns[-1]
        races = [c for c in t.columns[2:] if c != points and t.columns.get_loc(c) < t.columns.get_loc(points)
                 and not re.match(r"(car )?no\.?$", names[c].strip().lower())]
        renamed = {c: names[c] for c in races}
        return t, races, points, renamed
    return None


def entries(tabs):
    """driver -> team from the entry list (the last team a driver raced for, if they moved)."""
    out = {}
    for t in tabs:
        cols = flat(t.columns)
        lower = [c.lower() for c in cols]
        dcol = next((c for c, l in zip(cols, lower) if "driver" in l), None)
        tcol = next((c for c, l in zip(cols, lower) if l.startswith(("entrant", "team"))), None)
        if dcol and tcol and len(t) >= 6:
            t = t.copy()
            t.columns = cols
            for _, r in t.iterrows():
                d, tm = clean_name(r[dcol]), clean_name(r[tcol])
                if d and tm and d.lower() != "nan" and tm.lower() != "nan" and len(d) < 40:
                    out[name_key(d)] = tm
            if out:
                return out
    return out


def parse(series, season, html):
    tabs = tables(html)
    found = championship(tabs, "Driver")
    if found is None:
        return None
    drv, race_cols, pcol, label = found
    team_of = entries(tabs)
    rows, res = [], []
    for _, r in drv.iterrows():
        name = clean_name(r.iloc[1])
        pos = finish(r.iloc[0])
        if not name or pos is None or name.lower().startswith(("pos", "driver")):
            continue
        fins = [finish(r[c]) for c in race_cols]
        started = [str(r[c]).strip() for c in race_cols]
        raced = [x for x in started if x and x.lower() != "nan" and x != "—"]
        rows.append({"series": series, "season": season, "pos": pos, "driver": name,
                     "team": team_of.get(name_key(name), ""), "points": number(r[pcol]), "races": len(raced),
                     "wins": sum(f == 1 for f in fins if f), "podiums": sum(f <= 3 for f in fins if f)})
        for c, x, f in zip(race_cols, started, fins):
            if x and x.lower() != "nan":
                res.append({"series": series, "season": season, "race": label[c], "driver": name,
                            "result": x, "finish": f})
    found = championship(tabs, "Team")
    trows = []
    if found is not None:
        teams, _, tp, _ = found
        for _, r in teams.iterrows():
            pos, name = finish(r.iloc[0]), clean_name(r.iloc[1])
            if pos is not None and name and not name.lower().startswith("team"):
                trows.append({"series": series, "season": season, "pos": pos, "team": name, "points": number(r[tp])})
    st = pd.DataFrame(rows).drop_duplicates(["driver"]) if rows else pd.DataFrame()
    return st, pd.DataFrame(res), pd.DataFrame(trows).drop_duplicates(["team"]) if trows else pd.DataFrame()


def superlicence_table():
    html = fetch("FIA Super Licence")
    t = tables(html)[0] if html else None
    if t is None:
        return pd.DataFrame()
    t = t.copy()
    t.columns = ["series"] + [f"p{i}" for i in range(1, len(t.columns))]
    t = t[~t["series"].astype(str).str.startswith("Source")]
    for c in t.columns[1:]:
        t[c] = pd.to_numeric(t[c], errors="coerce").fillna(0)
    return t


# ---------- for the pages ----------

# Which row of the Super Licence table each of our series uses (GP2 and GP3 counted as F2 and F3)
SL_ROW = {"F2": "FIA Formula 2 Championship", "F3": "FIA Formula 3 Championship", "F1A": "F1 Academy"}
SL_NEEDED = 40          # points over the previous three seasons


def load():
    st = pd.read_csv(OUT / "standings.csv")
    st["key"] = st["driver"].map(name_key)
    return st, pd.read_csv(OUT / "teams.csv"), pd.read_csv(OUT / "superlicence.csv")


def sl_points(table, series, pos):
    row = table[table["series"] == SL_ROW.get(series, series)]
    if row.empty or not 1 <= int(pos) <= 10:
        return 0.0
    return float(row.iloc[0][f"p{int(pos)}"])


def f1_careers():
    """name_key -> first F1 season, starts, wins, podiums and best championship place, from our F1 archive."""
    res = pd.read_csv(ROOT / "data" / "processed" / "history_results.csv",
                      usecols=["season", "driver_name", "finish_position"])
    drv = pd.read_csv(ROOT / "data" / "processed" / "history_drivers.csv", usecols=["season", "driver_name", "position"])
    res["key"] = res["driver_name"].map(name_key)
    drv["key"] = drv["driver_name"].map(name_key)
    fin = pd.to_numeric(res["finish_position"], errors="coerce")
    g = res.assign(win=fin.eq(1), pod=fin.le(3)).groupby("key")
    out = pd.DataFrame({"first_f1": g["season"].min(), "starts": g.size(), "f1_wins": g["win"].sum(),
                        "f1_podiums": g["pod"].sum()})
    best = drv[drv["position"] > 0].groupby("key")["position"].min()
    out["best_f1"] = best
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parse", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="re-read this season's pages, which change as it runs")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    S, R, T = [], [], []
    for series, season, title, label in SEASONS:
        html = None
        if args.parse:
            path = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", title) + ".html")
            html = path.read_text(encoding="utf-8") if path.exists() else None
        else:
            html = fetch(title, refresh=args.refresh and season == LAST)
        if not html:
            print(f"{label} {season}: no page")
            continue
        out = parse(series, season, html)
        if out is None or out[0].empty:
            print(f"{label} {season}: no championship table")
            continue
        st, res, tm = out
        st["name"] = label
        S.append(st), R.append(res), T.append(tm)
        champ = st.sort_values("pos").iloc[0]
        print(f"{label} {season}: {len(st)} drivers, champion {champ['driver']} ({champ['points']:g})")
    OUT.mkdir(parents=True, exist_ok=True)
    pd.concat(S).to_csv(OUT / "standings.csv", index=False)
    pd.concat(R).to_csv(OUT / "results.csv", index=False)
    pd.concat([t for t in T if not t.empty]).to_csv(OUT / "teams.csv", index=False)
    sl = superlicence_table()
    if not sl.empty:
        sl.to_csv(OUT / "superlicence.csv", index=False)
        print(f"Super Licence table: {len(sl)} championships")


if __name__ == "__main__":
    main()
