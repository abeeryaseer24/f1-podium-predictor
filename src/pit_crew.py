"""Pit Crew: run a pit stop yourself, against every real stop's stationary time.

THE REAL STOPS: OpenF1's stop_duration for every pit stop in every prepared race (the stationary time
in the box, about 2-3 s), kept if it's under STOP_MAX (longer ones are repairs or penalties served).

THE GAME runs in the browser:
  1. the car stops: press GO and the jack goes up (your reaction counts)
  2. four crews change their wheels in 1.5-2.0 s; each wheel lights green when its nut is tight and you
     confirm it (tapping a wheel before it's green is a cross-threaded nut: 0.8 s to fix)
  3. release the car when all four are green and the lane is clear. Releasing into a passing car is an
     unsafe release: a 5 s penalty, as the stewards would give
Your stationary time is ranked against the real stops.

stats() gives the real numbers; game(stats, dark) draws it.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
RACES = ROOT / "data" / "races"
STOP_MAX = 6.0


def stats():
    rows = []
    for folder in sorted(RACES.glob("*_*")):
        pits, info = folder / "pits.parquet", folder / "info.json"
        if not pits.exists() or not info.exists():
            continue
        p = pd.read_parquet(pits)
        if "stop_duration" not in p.columns:
            continue
        meta = json.loads(info.read_text(encoding="utf-8"))
        team = {int(d["number"]): (d["team"], d.get("colour") or "#8a8a96", d["code"]) for d in meta.get("drivers", [])}
        p = p[p["stop_duration"].between(1.5, STOP_MAX)]
        for r in p.itertuples():
            t = team.get(int(r.driver_number))
            if t:
                rows.append({"season": meta["season"], "race": meta["race_name"], "team": t[0], "colour": t[1],
                             "driver": t[2], "stop": float(r.stop_duration)})
    df = pd.DataFrame(rows)
    last = int(df["season"].max())
    recent = df[df["season"] == last]
    teams = (recent.groupby("team").agg(median=("stop", "median"), best=("stop", "min"), stops=("stop", "size"),
                                        colour=("colour", "last")).sort_values("median"))
    fastest = df.loc[df["stop"].idxmin()]
    return {"season": last, "all": np.round(np.sort(df["stop"].to_numpy()), 2).tolist(),
            "teams": [{"team": t, **{k: (round(float(v), 2) if k in ("median", "best") else v) for k, v in r.items()}}
                      for t, r in teams.iterrows()],
            "fastest": {"stop": float(fastest["stop"]), "team": fastest["team"], "driver": fastest["driver"],
                        "race": f"{fastest['race']} {fastest['season']}"},
            "count": int(len(df))}


def game(data, dark=True, height=600):
    components.html(PAGE.replace("__DATA__", json.dumps({**data, "dark": dark})), height=height)


# The theme below must stay in step with THEMES in style.py.
PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; font-family: Inter, system-ui, sans-serif; color: var(--text); -webkit-user-select: none; user-select: none;
               touch-action: manipulation; }
  #app { display: flex; flex-direction: column; gap: 10px; }
  #box { position: relative; height: 380px; border-radius: 16px; border: 1px solid var(--border); background: var(--bg); overflow: hidden; }
  #lane { position: absolute; left: 0; right: 0; top: 18px; height: 54px; background: var(--road); border-bottom: 2px dashed var(--border); }
  #traffic { position: absolute; top: 26px; width: 76px; height: 38px; border-radius: 10px; background: #e4544a; display: none; }
  #traffic::after { content: "CAR"; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
                    font: 800 14px 'Saira Condensed', sans-serif; color: #fff; }
  #car { position: absolute; left: 50%; top: 150px; width: 170px; height: 86px; transform: translateX(-50%); border-radius: 30px;
         background: #e10600; transition: left .5s ease; }
  #car::before { content: ""; position: absolute; left: 62px; top: 28px; width: 46px; height: 30px; border-radius: 12px; background: #111; }
  .wheel { position: absolute; width: 58px; height: 40px; border-radius: 10px; background: #2a2a36; border: 3px solid #555;
           display: flex; align-items: center; justify-content: center; font: 800 13px 'Saira Condensed', sans-serif; color: #ddd;
           cursor: pointer; }
  .wheel.ready { background: #1fd6a0; border-color: #1fd6a0; color: #0b0b10; }
  .wheel.done { background: #3a7bd5; border-color: #3a7bd5; color: #fff; }
  #w0 { left: calc(50% - 125px); top: 112px; } #w1 { left: calc(50% + 67px); top: 112px; }
  #w2 { left: calc(50% - 125px); top: 236px; } #w3 { left: calc(50% + 67px); top: 236px; }
  #clock { position: absolute; left: 14px; bottom: 12px; font: 800 40px 'Saira Condensed', sans-serif; }
  #msg { position: absolute; right: 14px; bottom: 16px; max-width: 55%; text-align: right; font-size: 13px; color: var(--muted); }
  #controls { display: flex; gap: 10px; flex-wrap: wrap; }
  button { font: 800 16px 'Saira Condensed', Inter, sans-serif; letter-spacing: .5px; padding: 14px 22px; border-radius: 14px; cursor: pointer;
           border: 1px solid var(--border); background: var(--panel); color: var(--text); flex: 1; min-width: 120px; }
  button:disabled { opacity: .4; cursor: default; }
  #go { background: #e10600; border-color: #e10600; color: #fff; }
  #release { background: #1fd6a0; border-color: #1fd6a0; color: #0b0b10; }
  #result { padding: 12px 14px; border-radius: 14px; border: 1px solid var(--border); background: var(--panel); display: none; }
  #result b { font: 800 26px 'Saira Condensed', sans-serif; }
  .bar { position: relative; height: 26px; border-radius: 8px; background: var(--road); margin-top: 8px; }
  .bar i { position: absolute; top: -4px; width: 3px; height: 34px; background: #e10600; }
  .bar span { position: absolute; top: 4px; font-size: 11px; color: var(--muted); }
</style></head>
<body>
<div id="app">
  <div id="box">
    <div id="lane"></div><div id="traffic"></div>
    <div id="car"></div>
    <div class="wheel" id="w0">FL</div><div class="wheel" id="w1">FR</div><div class="wheel" id="w2">RL</div><div class="wheel" id="w3">RR</div>
    <div id="clock">0.00</div>
    <div id="msg">Press Start: the car comes in. Hit GO when it stops, confirm each wheel when it goes green, then release when the lane is clear.</div>
  </div>
  <div id="controls">
    <button id="start">Start</button><button id="go" disabled>GO</button><button id="release" disabled>RELEASE</button>
  </div>
  <div id="result"></div>
</div>
<script>
const D = __DATA__;
const T = D.dark ? { bg: "#0b0b10", panel: "#15151e", border: "#2c2c3a", text: "#f5f5f7", muted: "#a3a3b2", road: "#1d1d27" }
                 : { bg: "#f6f6f3", panel: "#ffffff", border: "#d9d9d4", text: "#15151e", muted: "#55556a", road: "#e3e3df" };
for (const [k, v] of Object.entries(T)) document.documentElement.style.setProperty("--" + k, v);
const $ = id => document.getElementById(id);
let S = null, raf = null;

function reset() {
  for (let i = 0; i < 4; i++) $("w" + i).className = "wheel";
  $("car").style.left = "-200px";
  $("result").style.display = "none";
}
function start() {
  reset();
  S = { phase: "arriving", stopAt: null, t0: null, penalty: 0, notes: [], wheels: [], traffic: [] };
  $("start").disabled = true; $("go").disabled = true; $("release").disabled = true;
  $("msg").textContent = "Here it comes…";
  requestAnimationFrame(() => { $("car").style.left = "50%"; });
  const wait = 900 + Math.random() * 1400;                 // the car arrives at a moment you can't predict
  setTimeout(() => { S.phase = "stopped"; S.stopAt = performance.now(); $("go").disabled = false; $("msg").textContent = "STOPPED: GO!"; tick(); }, 500 + wait);
}
function go() {
  if (!S || S.phase !== "stopped") return;
  S.phase = "wheels"; $("go").disabled = true;
  const jack = performance.now() + 250;                    // the jack takes a quarter of a second
  S.wheels = [0, 1, 2, 3].map(() => ({ ready: jack + 1500 + Math.random() * 500, done: false }));
  // sometimes a car passes in the lane during the stop: then you must wait for it
  if (Math.random() < 0.6) { const at = jack + 1300 + Math.random() * 1500; S.traffic.push([at, at + 450]); }
  $("msg").textContent = "Wheels: confirm each one when it goes green.";
}
function wheel(i) {
  if (!S || S.phase !== "wheels" || S.wheels[i].done) return;
  const now = performance.now();
  if (now < S.wheels[i].ready) {
    S.penalty += 800; S.notes.push("cross-threaded nut on " + ["FL", "FR", "RL", "RR"][i] + " (+0.8 s)");
    S.wheels[i].ready = Math.max(S.wheels[i].ready, now) + 800;
    return;
  }
  S.wheels[i].done = true; $("w" + i).className = "wheel done";
  if (S.wheels.every(w => w.done)) { S.phase = "release"; $("release").disabled = false; $("msg").textContent = "All four on. Release when the lane is clear!"; }
}
function laneBusy(now) { return S.traffic.some(([a, b]) => now >= a && now <= b); }
function release() {
  if (!S || S.phase !== "release") return;
  const now = performance.now();
  let stat = (now - S.stopAt + S.penalty) / 1000;
  if (laneBusy(now)) { S.notes.push("unsafe release into a passing car: 5 s penalty"); stat += 5; }
  S.phase = "done"; $("release").disabled = true; $("start").disabled = false; $("start").textContent = "Go again";
  $("car").style.left = "130%";
  cancelAnimationFrame(raf);
  $("traffic").style.display = "none";
  $("msg").textContent = S.notes.length ? "Released, with a penalty." : "Released clean.";
  $("clock").textContent = stat.toFixed(2);
  show(stat);
}
function tick() {
  const now = performance.now();
  if (S.phase !== "done") $("clock").textContent = ((now - S.stopAt + S.penalty) / 1000).toFixed(2);
  if (S.phase === "wheels") S.wheels.forEach((w, i) => { if (!w.done && now >= w.ready) $("w" + i).className = "wheel ready"; });
  const busy = S.phase !== "arriving" && laneBusy(now);
  const tr = $("traffic");
  const live = S.traffic.find(([a, b]) => now >= a - 300 && now <= b + 300);
  if (live) { tr.style.display = "block"; tr.style.left = ((now - live[0] + 300) / 1300 * 110 - 10) + "%"; } else tr.style.display = "none";
  if (S.phase === "release") $("msg").textContent = busy ? "WAIT: car in the lane!" : "Lane clear: RELEASE!";
  raf = requestAnimationFrame(tick);
}
function show(stat) {
  const all = D.all, rank = all.filter(x => x < stat).length;
  const pct = rank / all.length;
  const team = D.teams.find(t => stat <= t.median);
  const verdict = stat <= D.fastest.stop ? "Faster than any real stop in our data!" :
    team ? `Quicker than ${team.team}'s typical ${D.season} stop (${team.median.toFixed(2)} s).` : "Slower than every team's typical stop.";
  const lo = 1.8, hi = 5.0, pos = x => Math.min(100, Math.max(0, (x - lo) / (hi - lo) * 100));
  let marks = D.teams.slice(0, 10).map(t => `<span style="left:${pos(t.median)}%;top:30px;color:${t.colour}">▲</span>`).join("");
  $("result").innerHTML = `<b>${stat.toFixed(2)} s</b> stationary · faster than ${Math.round((1 - pct) * 100)}% of ${D.count.toLocaleString()} real stops.<br>` +
    `${verdict} ${S.notes.length ? "<br>Lost time: " + S.notes.join("; ") + "." : ""}` +
    `<div class="bar"><i style="left:${pos(stat)}%"></i><span style="left:0">1.8 s</span><span style="right:4px">5 s</span>${marks}</div>` +
    `<div style="font-size:11px;color:var(--muted);margin-top:22px">Red line: you. Triangles: each team's typical stop in ${D.season}. ` +
    `Fastest in our data: ${D.fastest.stop.toFixed(2)} s, ${D.fastest.team} (${D.fastest.driver}), ${D.fastest.race}.</div>`;
  $("result").style.display = "block";
}
$("start").onclick = start; $("go").onclick = go; $("release").onclick = release;
for (let i = 0; i < 4; i++) $("w" + i).onclick = () => wheel(i);
addEventListener("keydown", e => {
  if (e.key === " ") { e.preventDefault(); if (S && S.phase === "stopped") go(); else if (S && S.phase === "release") release(); else if (!S || S.phase === "done") start(); }
  const k = { "1": 0, "2": 1, "3": 2, "4": 3, q: 0, w: 1, a: 2, s: 3 }[e.key.toLowerCase()];
  if (k !== undefined) wheel(k);
});
reset();
</script></body></html>
"""
