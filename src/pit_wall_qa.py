"""Ask the Pit Wall: plain-English questions about F1 history, answered from our own archive (1950 to today).

No language model and no paid service. The question is read in three steps:

1. YEARS     "in 2021", "since 2010", "between 2000 and 2009", "2000s"
2. NAMES     every word and two- or three-word phrase is matched against drivers, teams and circuits, with
             difflib's fuzzy matching so "verstapen" or "silverston" still work
3. WHAT      keywords decide the statistic (wins, poles, podiums, titles, points, starts, retirements,
             fastest laps) and the shape of the answer (one driver's record, a head-to-head, a leaderboard,
             or who won a particular race)

The answer always says how the question was read, so a wrong guess is easy to spot and rephrase.
"""
import difflib
import html
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"

STATS = {   # key: (label, keywords)
    "titles": ("World titles", ("title", "titles", "championship", "championships", "champion", "champions", "wdc")),
    "poles": ("Pole positions", ("pole", "poles", "polesitter")),
    "podiums": ("Podiums", ("podium", "podiums", "top three", "top 3")),
    "fastest": ("Fastest laps", ("fastest lap", "fastest laps")),
    "dnfs": ("Retirements", ("dnf", "dnfs", "retire", "retired", "retirement", "retirements")),
    "points": ("Points", ("point", "points")),
    "starts": ("Starts", ("start", "starts", "races", "raced", "entries", "appearances")),
    "wins": ("Wins", ("win", "wins", "won", "victory", "victories", "winner", "winners")),
}
VERSUS = ("vs", "versus", "against", "beat", "beaten", "compare", "compared", "or")
NICKNAMES = {"max": "max_verstappen", "lewis": "hamilton", "seb": "vettel", "schumi": "michael_schumacher",
             "kimi": "raikkonen", "nando": "alonso", "checo": "perez", "lando": "norris", "charles": "leclerc",
             "senna": "senna", "ayrton": "senna", "prost": "prost", "fangio": "fangio", "clark": "clark",
             "mansell": "mansell", "lauda": "lauda", "piastri": "piastri", "oscar": "piastri", "carlos": "sainz",
             "russell": "russell", "george": "russell", "nico": "rosberg", "hakkinen": "hakkinen", "mika": "hakkinen"}
TEAM_ALIASES = {"red bull": "red_bull", "redbull": "red_bull", "rbr": "red_bull", "merc": "mercedes",
                "scuderia": "ferrari", "prancing horse": "ferrari", "aston": "aston_martin", "macca": "mclaren"}
STOP = {"who", "what", "how", "many", "much", "the", "most", "has", "have", "had", "did", "does", "do", "in", "at",
        "of", "a", "an", "is", "was", "were", "for", "and", "with", "to", "since", "between", "from", "until",
        "ever", "all", "time", "alltime", "grand", "prix", "gp", "race", "driver", "drivers", "team", "teams",
        "career", "best", "more", "than", "which", "by", "on", "their", "his", "her", "show", "me", "list", "top",
        "record", "records", "season", "seasons", "year", "years", "get", "got", "scored", "score", "f1",
        "formula", "one", "constructor", "constructors", "first", "last", "each", "every", "number", "count"}


def plain(text):
    return re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower())


@lru_cache(maxsize=1)
def tables():
    res = pd.read_csv(DATA / "history_results.csv")
    res["finish_position"] = pd.to_numeric(res["finish_position"], errors="coerce")
    res["grid"] = pd.to_numeric(res["grid"], errors="coerce")
    drv = pd.read_csv(DATA / "history_drivers.csv")
    teams = pd.read_csv(DATA / "history_teams.csv")
    races = pd.read_csv(DATA / "history_races.csv")
    for t in (res, drv, teams):                            # "Brabham-Repco", "Lotus-Climax": one team, whatever the engine
        t["constructor"] = t["constructor"].astype(str).str.split("-").str[0]
        t["constructor_name"] = t["constructor_name"].astype(str).map(html.unescape).str.split("-").str[0]
        t.loc[t["constructor"] == "team_lotus", ["constructor", "constructor_name"]] = ["lotus", "Lotus"]
        t.loc[t["constructor"] == "lotus_racing", "constructor_name"] = "Lotus Racing"
    for t in (res, drv):
        t["driver_name"] = t["driver_name"].astype(str).map(html.unescape)
    return res, drv, teams, races


SHARED = {}   # names that are both a team and a driver -> the driver


@lru_cache(maxsize=1)
def lexicon():
    """phrase -> (kind, id). Surnames that several drivers share go to the one with the most starts."""
    res, _, _, races = tables()
    words = {}
    starts = res.groupby("driver").size()
    names = res.drop_duplicates("driver").set_index("driver")["driver_name"]
    for d in starts.sort_values().index:                    # most starts last, so they win shared surnames
        full = plain(names[d]).strip()
        words[full] = ("driver", d)
        words[full.split()[-1]] = ("driver", d)
    for alias, d in NICKNAMES.items():
        if d in names.index:
            words[alias] = ("driver", d)
    for c, n in res.drop_duplicates("constructor")[["constructor", "constructor_name"]].itertuples(index=False):
        key = plain(n).strip()
        if words.get(key, ("",))[0] == "driver":            # Prost, Brabham, McLaren: team and driver
            SHARED[key] = words[key]
        words[key] = ("team", c)
    for alias, c in TEAM_ALIASES.items():
        words[alias] = ("team", c)
    for r in races.drop_duplicates("circuit").itertuples():
        for phrase in (r.circuit_name, r.locality, r.circuit.replace("_", " ")):
            p = plain(phrase).strip()
            if p and p not in words:
                words[p] = ("circuit", r.circuit)
    for r in races.drop_duplicates("race_name").itertuples():   # "British Grand Prix" -> every circuit it used
        p = plain(r.race_name.replace("Grand Prix", "")).strip()
        if p and p not in words:
            words[p] = ("race", r.race_name)
    return words


def years(q):
    now = int(tables()[0]["season"].max())
    m = re.search(r"between (\d{4}) and (\d{4})|(\d{4})\s*(?:-|to|until)\s*(\d{4})", q)
    if m:
        a, b = [int(x) for x in m.groups() if x]
        return min(a, b), max(a, b)
    m = re.search(r"(?:since|after|from) (\d{4})", q)
    if m:
        return int(m.group(1)), now
    m = re.search(r"(?:before|until) (\d{4})", q)
    if m:
        return 1950, int(m.group(1)) - 1
    m = re.search(r"\b(19[5-9]0|20[0-2]0)s\b", q)
    if m:
        return int(m.group(1)), int(m.group(1)) + 9
    m = re.search(r"\b(19[5-9]\d|20[0-4]\d)\b", q)
    if m:
        return int(m.group(1)), int(m.group(1))
    return None


def parse(question):
    q = plain(question)
    q = re.sub(r"\s+", " ", q).strip()
    span = years(q)
    stat = next((k for k, (_, keys) in STATS.items() if any(re.search(rf"\b{re.escape(w)}\b", q) for w in keys)), None)
    toks = [t for t in q.split() if not t.isdigit()]
    lex = lexicon()
    keys = list(lex)
    found, used, phrases = [], set(), {}
    for n in (3, 2, 1):                                     # longest phrases first
        for i in range(len(toks) - n + 1):
            if any(j in used for j in range(i, i + n)):
                continue
            phrase = " ".join(toks[i:i + n])
            if n == 1 and (phrase in STOP or len(phrase) < 3 or phrase in VERSUS
                           or any(phrase in keys_ for _, keys_ in STATS.values())):
                continue
            hit = lex.get(phrase)
            if hit is None and len(phrase) >= 5:
                close = difflib.get_close_matches(phrase, keys, n=1, cutoff=0.86 if n == 1 else 0.9)
                hit = lex[close[0]] if close else None
            if hit and hit not in found:
                found.append(hit)
                phrases[hit] = phrase
                used.update(range(i, i + n))
    # "Prost vs Senna" means the driver Prost; "Ferrari vs McLaren" means the team McLaren
    if any(f" {v} " in f" {q} " for v in VERSUS[:5]):
        shared = [h for h in found if h[0] == "team" and phrases[h] in SHARED]
        if len(shared) == 1 and sum(h[0] == "team" for h in found) == 1 and any(h[0] == "driver" for h in found):
            found = [SHARED[phrases[h]] if h == shared[0] else h for h in found]
    drivers = [i for k, i in found if k == "driver"]
    teams = [i for k, i in found if k == "team"]
    circuits = [i for k, i in found if k == "circuit"]
    race_names = [i for k, i in found if k == "race"]
    shape = ("versus" if len(drivers) >= 2 or len(teams) >= 2 else
             "record" if drivers or (teams and not re.search(r"\bwho\b|\bwhich\b|\bmost\b", q)) else
             "race" if span and span[0] == span[1] and (circuits or race_names) else
             "leaders")
    return {"question": question, "stat": stat or "wins", "stat_guessed": stat is None, "years": span,
            "drivers": drivers, "teams": teams, "circuits": circuits, "race_names": race_names, "shape": shape}


def _filter(res, p):
    out = res
    if p["years"]:
        out = out[out["season"].between(*p["years"])]
    if p["circuits"]:
        out = out[out["circuit"].isin(p["circuits"])]
    if p["race_names"]:
        out = out[out["race_name"].isin(p["race_names"])]
    return out


def _value(rows, stat, who_col):
    """One number per driver or team for a statistic."""
    if stat == "wins":
        return rows[rows["finish_position"] == 1].groupby(who_col).size()
    if stat == "podiums":
        return rows[rows["finish_position"] <= 3].groupby(who_col).size()
    if stat == "poles":
        return rows[rows["grid"] == 1].groupby(who_col).size()
    if stat == "fastest":
        return rows[rows["fastest_lap_rank"] == 1].groupby(who_col).size()
    if stat == "points":
        return rows.groupby(who_col)["points"].sum()
    if stat == "starts":
        return rows.drop_duplicates(["season", "round", who_col]).groupby(who_col).size() if who_col == "constructor" \
            else rows.groupby(who_col).size()
    if stat == "dnfs":
        fin = rows["status"].str.match(r"Finished|\+\d+ Laps?|Lapped", na=False)
        return rows[~fin].groupby(who_col).size()
    raise KeyError(stat)


def _titles(p, who_col):
    _, drv, teams, _ = tables()
    table = drv if who_col == "driver" else teams
    champs = table[table["position"] == 1]
    if p["years"]:
        champs = champs[champs["season"].between(*p["years"])]
    return champs.groupby(who_col).size(), champs


def stat_of(p, who_col, rows):
    if p["stat"] == "titles":
        return _titles(p, who_col)[0]
    return _value(rows, p["stat"], who_col)


def count(v, word):
    """'1 podium', '3 podiums', '7.5 points'."""
    return f"{v:g} {word[:-1] if v == 1 and word.endswith('s') else word}"


def names():
    res = tables()[0]
    return (res.drop_duplicates("driver").set_index("driver")["driver_name"].to_dict(),
            res.drop_duplicates("constructor").set_index("constructor")["constructor_name"].to_dict())


def answer(p):
    """{"headline", "rows": [(name, value, sub, team)], "versus": ..., "note"} for the page to draw."""
    res = tables()[0]
    rows = _filter(res, p)
    dn, tn = names()
    label = STATS[p["stat"]][0]
    when = ""
    if p["years"]:
        a, b = p["years"]
        when = f" in {a}" if a == b else f" from {a} to {b}"
    where = ""
    if p["circuits"] or p["race_names"]:
        where = " at the " + ", ".join(p["race_names"] or sorted(set(res.loc[res["circuit"].isin(p["circuits"]), "race_name"].mode())))
    if rows.empty and p["stat"] != "titles":
        return {"headline": f"No races in our archive match that{when}{where}.", "rows": [], "note": ""}

    def team_of(driver):
        sub = rows[rows["driver"] == driver]
        return sub["constructor_name"].mode().iloc[0] if len(sub) else ""

    if p["shape"] == "race":
        race = rows.sort_values("finish_position")
        top = race[race["finish_position"].notna()].head(10)
        if top.empty:
            return {"headline": "No result in our archive for that race.", "rows": [], "note": ""}
        w = top.iloc[0]
        return {"headline": f"{w['driver_name']} won the {w['season']} {w['race_name']} for {w['constructor_name']}, " +
                            (f"from P{int(w['grid'])} on the grid." if pd.notna(w['grid']) and w['grid'] > 0 else "from the pit lane."),
                "rows": [(r.driver_name, int(r.finish_position), f"grid {int(r.grid) if r.grid > 0 else 'pit lane'} · {r.status}",
                          r.constructor_name) for r in top.itertuples()], "value_label": "Finished", "note": ""}

    if p["shape"] == "versus":
        if len(p["drivers"]) >= 2:
            a, b = p["drivers"][:2]
            both = rows[rows["driver"].isin([a, b])]
            shared = both.groupby(["season", "round"]).filter(lambda g: g["driver"].nunique() == 2)
            ahead = {a: 0, b: 0}
            for _, g in shared.groupby(["season", "round"]):
                pa = g.loc[g["driver"] == a, "finish_position"].fillna(99).min()
                pb = g.loc[g["driver"] == b, "finish_position"].fillna(99).min()
                if pa != pb and min(pa, pb) < 99:
                    ahead[a if pa < pb else b] += 1
            stats = []
            for key in ("wins", "podiums", "poles", "points", "starts"):
                v = _value(rows[rows["driver"].isin([a, b])], key, "driver")
                stats.append((STATS[key][0], float(v.get(a, 0)), float(v.get(b, 0))))
            t = _titles(p, "driver")[0]
            stats.insert(0, ("World titles", float(t.get(a, 0)), float(t.get(b, 0))))
            n = ahead[a] + ahead[b]
            lead = a if ahead[a] > ahead[b] else b
            head = (f"In the {n} races they both started{when}{where}, {dn[lead]} finished ahead {ahead[lead]} times "
                    f"to {ahead[a if lead == b else b]}." if n else f"{dn[a]} and {dn[b]} never raced each other{when}{where}.")
            return {"headline": head, "versus": (dn[a], dn[b], team_of(a), team_of(b), stats,
                                                 ("Finished ahead", float(ahead[a]), float(ahead[b]))), "rows": [], "note":
                    "Head-to-head counts only races both started; a retirement counts as finishing behind."}
        a, b = p["teams"][:2]
        stats = []
        for key in ("wins", "podiums", "poles", "points", "starts"):
            v = _value(rows[rows["constructor"].isin([a, b])], key, "constructor")
            stats.append((STATS[key][0], float(v.get(a, 0)), float(v.get(b, 0))))
        t = _titles(p, "constructor")[0]
        stats.insert(0, ("Constructors' titles", float(t.get(a, 0)), float(t.get(b, 0))))
        w = dict((s[0], (s[1], s[2])) for s in stats)["Wins"]
        lead, other = (a, b) if w[0] >= w[1] else (b, a)
        return {"headline": f"{tn[lead]} have won {int(max(w))} races to {tn[other]}'s {int(min(w))}{when}{where}.",
                "versus": (tn[a], tn[b], tn[a], tn[b], stats, None), "rows": [], "note": ""}

    if p["shape"] == "record":
        if p["drivers"]:
            d = p["drivers"][0]
            mine = rows[rows["driver"] == d]
            v = stat_of(p, "driver", rows).get(d, 0)
            extra = ""
            if p["stat"] == "titles":
                seasons = _titles(p, "driver")[1]
                seasons = seasons.loc[seasons["driver"] == d, "season"].tolist()
                extra = f" ({', '.join(map(str, seasons))})" if seasons else ""
            if p["teams"]:
                mine = mine[mine["constructor"] == p["teams"][0]]
                v = stat_of(p, "driver", rows[rows["constructor"] == p["teams"][0]]).get(d, 0)
                where += f" with {tn[p['teams'][0]]}"
            head = f"{dn[d]}: {count(v, label.lower())}{when}{where}{extra}."
            by = []
            if p["stat"] != "titles" and len(mine):
                per = _value(mine, p["stat"], "season")
                starts = mine.groupby("season").size()
                team = mine.groupby("season")["constructor_name"].agg(lambda s: s.mode().iloc[0])
                by = [(str(s), float(per.get(s, 0)), f"{int(starts[s])} starts", team[s]) for s in starts.index]
            return {"headline": head, "rows": by, "value_label": label, "by": "Season", "note": ""}
        c = p["teams"][0]
        mine = rows[rows["constructor"] == c]
        v = stat_of(p, "constructor", rows).get(c, 0)
        kind = "constructors' titles" if p["stat"] == "titles" else label.lower()
        head = f"{tn[c]}: {count(v, kind)}{when}{where}."
        lead = _value(mine, p["stat"], "driver").sort_values(ascending=False).head(10) if p["stat"] != "titles" else pd.Series(dtype=float)
        return {"headline": head, "rows": [(dn[d], float(x), "", tn[c]) for d, x in lead.items() if x > 0],
                "value_label": f"{label} for {tn[c]}", "by": "Driver", "note": ""}

    # leaderboard
    if p["stat"] == "titles" and p["years"] and p["years"][0] == p["years"][1]:
        _, champs = _titles(p, "driver")
        _, team_champs = _titles(p, "constructor")
        if len(champs):
            c = champs.iloc[0]
            head = f"{c['driver_name']} was world champion in {c['season']} with {c['constructor_name']}, {c['points']:g} points."
            if len(team_champs):
                head += f" {team_champs.iloc[0]['constructor_name']} won the constructors' title."
            return {"headline": head, "rows": [], "note": ""}
    who_col = "constructor" if re.search(r"\bteams?\b|\bconstructors?\b", plain(p["question"])) else "driver"
    if who_col == "constructor" and p["stat"] == "titles":
        label = "Constructors' titles"
    s = stat_of(p, who_col, rows).sort_values(ascending=False)
    s = s[s > 0].head(10)
    if s.empty:
        return {"headline": f"Nobody has any {label.lower()}{when}{where} in our archive.", "rows": [], "note": ""}
    nm = dn if who_col == "driver" else tn
    top = s.index[0]
    tied = (s == s.iloc[0]).sum()
    head = (f"{nm[top]} leads with {count(s.iloc[0], label.lower())}{when}{where}." if tied == 1 else
            f"{tied} share the lead with {count(s.iloc[0], label.lower())}{when}{where}.")
    out = [(nm[i], float(x), "", team_of(i) if who_col == "driver" else nm[i]) for i, x in s.items()]
    note = "Fastest-lap records in our archive start in 2004." if p["stat"] == "fastest" else ""
    return {"headline": head, "rows": out, "value_label": label, "by": "Driver" if who_col == "driver" else "Team",
            "note": note}


def reading(p):
    """How the question was understood, as short chips."""
    dn, tn = names()
    out = [(STATS[p["stat"]][0] + (" (guessed)" if p["stat_guessed"] else ""), "#e10600")]
    out += [(dn.get(d, d), "#27f4d2") for d in p["drivers"]]
    out += [(tn.get(t, t), "#ff8000") for t in p["teams"]]
    races = tables()[3]
    cn = races.drop_duplicates("circuit").set_index("circuit")["circuit_name"].to_dict()
    out += [(cn.get(c, c), "#64c4ff") for c in p["circuits"]]
    out += [(r, "#64c4ff") for r in p["race_names"]]
    if p["years"]:
        a, b = p["years"]
        out.append((str(a) if a == b else f"{a}–{b}", "#e8b33a"))
    out.append(({"versus": "head-to-head", "record": "one record", "race": "one race", "leaders": "leaderboard"}[p["shape"]],
                "#8a8a96"))
    return out


if __name__ == "__main__":
    import sys
    for q in sys.argv[1:] or ["Who has the most wins at Monaco?", "Hamilton vs Verstappen", "Senna poles",
                              "Who won the 2008 British Grand Prix?", "Ferrari titles since 2000",
                              "most podiums 2010s", "Verstapen wins in 2023", "Red Bull vs Mercedes",
                              "which team has the most points since 2014", "Alonso retirements with McLaren"]:
        p = parse(q)
        a = answer(p)
        print(f"{q!r:55} -> {[t for t, _ in reading(p)]}\n    {a['headline']}")
