"""The Home page's big race card: next race, a live countdown, the five start lights and the
weekend schedule. All times are worked out in the visitor's browser, so they show in their own time."""
import json

import streamlit.components.v1 as components


def race_hero(race, locked, dark=True, height=470):
    """race: one race from race_calendar(); locked: has our model locked its prediction?"""
    data = {
        "round": race["round"], "name": race["race_name"], "circuit": race["circuit"], "place": race["place"],
        "trackTz": race["track_tz"], "start": race["race_start"].isoformat(),
        "quali": race["quali_start"].isoformat() if race["quali_start"] else None,
        "sessions": [[label, t.isoformat()] for label, t in race["sessions"]],
        "locked": bool(locked), "dark": bool(dark),
    }
    components.html(PAGE.replace("__DATA__", json.dumps(data)), height=height)


PAGE = r"""<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--red:#e10600}
.dark{--panel:#15151e;--panel2:#1e1e29;--text:#f5f5f7;--muted:#a3a3b2;--border:#2c2c3a;--pod:#0a0a0e}
.light{--panel:#ffffff;--panel2:#ececea;--text:#15151e;--muted:#55556a;--border:#d9d9d4;--pod:#1b1b22}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:transparent;font-family:Inter,system-ui,sans-serif}
.card{height:100%;display:flex;flex-direction:column;gap:14px;padding:22px 24px;border-radius:18px;
  background:linear-gradient(135deg,rgba(225,6,0,.18),rgba(225,6,0,0) 45%),var(--panel);border:1px solid var(--border);color:var(--text);overflow:hidden;position:relative}
.top{display:flex;justify-content:space-between;align-items:center;gap:10px}
.rnd{font-family:'Saira Condensed',sans-serif;font-weight:800;letter-spacing:2px;color:var(--red);font-size:15px}
.pill{padding:5px 12px;border-radius:999px;font-size:12px;font-weight:700;background:var(--panel2);color:var(--text);white-space:nowrap}
.pill.hot{background:var(--red);color:#fff}
h1{font-family:'Saira Condensed',sans-serif;font-weight:800;text-transform:uppercase;font-size:clamp(28px,6vw,52px);line-height:.95;margin:0;letter-spacing:.5px}
.sub{color:var(--muted);font-size:14px;margin-top:-6px}
.row{display:flex;align-items:center;gap:28px;flex-wrap:wrap;flex:1}
.gantry{display:flex;gap:10px;padding:12px 14px;border-radius:14px;background:var(--pod);box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)}
.pod{display:flex;flex-direction:column;gap:8px;padding:8px;border-radius:10px;background:#000}
.bulb{width:30px;height:30px;border-radius:50%;background:#2a0b0b;box-shadow:inset 0 2px 4px rgba(0,0,0,.6);transition:background .08s,box-shadow .08s}
.bulb.dim{background:#141418}
.pod.on .bulb.r{background:radial-gradient(circle at 40% 35%,#ff6a5c,#e10600 55%,#8a0400);box-shadow:0 0 18px 4px rgba(225,6,0,.75)}
.cd .lbl{color:var(--muted);font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px}
.num{display:flex;gap:8px;margin-top:6px}
.unit{min-width:64px;padding:10px 8px 8px;border-radius:12px;background:var(--panel2);text-align:center;border:1px solid var(--border)}
.unit b{display:block;font-family:Inter,system-ui,sans-serif;font-weight:600;font-size:30px;line-height:1;font-variant-numeric:tabular-nums;color:var(--text)}
.unit span{display:block;margin-top:5px;font-size:10px;font-weight:600;letter-spacing:1.2px;color:var(--muted)}
.away{font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:34px;color:var(--red);letter-spacing:1px}
.when{color:var(--muted);font-size:13px;margin-top:4px}
.flash{position:absolute;right:24px;top:58px;font-family:'Saira Condensed',sans-serif;font-weight:800;font-size:18px;letter-spacing:2px;color:var(--red);opacity:0;transition:opacity .2s}
.flash.show{opacity:1}
.sched{display:flex;gap:8px;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}
.sched::-webkit-scrollbar{display:none}
.chip{flex:none;padding:7px 12px;border-radius:10px;background:var(--panel2);font-size:12px;color:var(--text);border:1px solid transparent}
.chip b{display:block;font-weight:700;font-size:12px}
.chip span{color:var(--muted)}
.chip.done{opacity:.55}
.chip.next{border-color:var(--red)}
.chip.next b{color:var(--red)}
@media (max-width:560px){.unit{min-width:54px;padding:8px 6px 7px}.unit b{font-size:24px}.card{padding:18px 16px;gap:11px}.row{gap:14px}.bulb{width:22px;height:22px}.gantry{gap:7px;padding:9px 10px}.pod{gap:6px;padding:6px}.flash{display:none}}
@media (prefers-reduced-motion:reduce){.bulb{transition:none}}
</style></head><body>
<div class="card" id="card">
  <div class="top"><span class="rnd" id="rnd"></span><span class="pill" id="pill"></span></div>
  <h1 id="name"></h1>
  <div class="sub" id="sub"></div>
  <div class="flash" id="flash">LIGHTS OUT AND AWAY WE GO</div>
  <div class="row">
    <div class="gantry" id="gantry"></div>
    <div class="cd"><div class="lbl" id="lbl">Lights out in</div><div class="num" id="num"></div><div class="when" id="when"></div></div>
  </div>
  <div class="sched" id="sched"></div>
</div>
<script>
const D = __DATA__;
document.body.className = D.dark ? "dark" : "light";
const $ = id => document.getElementById(id);
const start = new Date(D.start), quali = D.quali ? new Date(D.quali) : null;
$("rnd").textContent = `ROUND ${D.round}`;
$("name").textContent = D.name;
$("sub").textContent = [D.circuit, D.place].filter(Boolean).join(" · ");

const fmt = (d, tz) => d.toLocaleString(undefined, Object.assign({weekday: "short", day: "2-digit", month: "short",
  hour: "2-digit", minute: "2-digit"}, tz ? {timeZone: tz} : {}));
const clock = (d, tz) => d.toLocaleTimeString(undefined, Object.assign({hour: "2-digit", minute: "2-digit"}, tz ? {timeZone: tz} : {}));
$("when").textContent = `${fmt(start)} your time` + (D.trackTz ? ` · ${clock(start, D.trackTz)} at the track` : "");

// the five start lights: five pods, each with two dark bulbs on top and two red bulbs below
for (let i = 0; i < 5; i++) {
  const pod = document.createElement("div"); pod.className = "pod";
  pod.innerHTML = '<div class="bulb dim"></div><div class="bulb dim"></div><div class="bulb r"></div><div class="bulb r"></div>';
  $("gantry").appendChild(pod);
}
const pods = [...document.querySelectorAll(".pod")];
const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
function sequence() {                    // one light a second, a short random hold, then lights out
  if (still) { pods.forEach(p => p.classList.add("on")); return; }
  pods.forEach(p => p.classList.remove("on")); $("flash").classList.remove("show");
  pods.forEach((p, i) => setTimeout(() => p.classList.add("on"), 900 + i * 1000));
  const out = 900 + 4 * 1000 + 700 + Math.random() * 1800;
  setTimeout(() => { pods.forEach(p => p.classList.remove("on")); $("flash").classList.add("show"); }, out);
  setTimeout(() => $("flash").classList.remove("show"), out + 1800);
  setTimeout(sequence, out + 3200);
}
sequence();

// weekend schedule, in the visitor's own time
function schedule(now) {
  const next = D.sessions.findIndex(([, t]) => new Date(t) > now);
  $("sched").innerHTML = D.sessions.map(([label, t], i) => {
    const d = new Date(t), cls = d <= now ? "done" : (i === next ? "next" : "");
    return `<div class="chip ${cls}"><b>${d <= now ? "✓ " : ""}${label}</b><span>${fmt(d)}</span></div>`;
  }).join("");
}

// countdown and the status pill
const pad = n => String(n).padStart(2, "0");
function tick() {
  const now = new Date(), left = start - now;
  const upcoming = D.sessions.find(([, t]) => new Date(t) > now);
  let pill = upcoming && upcoming[0] !== "Race" ? `Next: ${upcoming[0]}` : "Race next", hot = false;
  if (left <= 0) {
    pill = now - start < 2.5 * 3600e3 ? "Race on now" : "Race done, results soon"; hot = true;
    $("lbl").textContent = "Lights went out"; $("num").innerHTML = '<span class="away">AND AWAY WE GO</span>';
  } else {
    if (quali && now >= quali) pill = D.locked ? "Prediction locked" : "Prediction locks on race day";
    if (left < 3600e3) { pill = "Lights out soon!"; hot = true; }
    const s = Math.floor(left / 1000), d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600),
          m = Math.floor(s % 3600 / 60), sec = s % 60;
    const unit = (v, label) => `<div class="unit"><b>${v}</b><span>${label}</span></div>`;
    $("num").innerHTML = (d ? unit(d, d === 1 ? "DAY" : "DAYS") : "") + unit(pad(h), "HRS") + unit(pad(m), "MIN") + unit(pad(sec), "SEC");
  }
  $("pill").textContent = pill; $("pill").className = "pill" + (hot ? " hot" : "");
  schedule(now);
}
tick(); setInterval(tick, 1000);
</script></body></html>"""
