"""Race the AI Driver: you drive the lap simulator's car round a real circuit in the browser.

Python sends the circuit (every 8 m: position, the tyres' corner limit, curvature, slope), the
calibrated car, and two ghosts: the AI driver (ai_driver.py, a driver learned from real laps
and tested on circuits it never saw) and the real fastest lap. The page runs the same physics
as lapsim.py every frame, with your pedals instead of a perfect driver's:

  throttle   drive force = the engine's power / speed, capped by the rear tyres' grip left over
             after cornering (the friction circle), minus drag, rolling resistance and slope
  brake      all the grip left over after cornering, plus drag and slope
  neither    the car coasts on drag and rolling resistance

Go past the tyres' corner limit and the car runs wide: it drops to 55% of the limit and loses 0.3 s, so running wide always costs more than braking would have.

drive(folder_data, dark) draws it. The keyboard (up / down, or W / S, or space to brake) and two
big touch buttons both work.
"""
import json

import numpy as np
import streamlit.components.v1 as components

import lapsim


def braking_envelope(car, track, vc):
    """The fastest the car can be at every point and still make every corner after it: the lap
    simulator's braking pass on its own (no acceleration limit), run twice round to wrap."""
    n = len(track.s)
    ds = track.length / n
    m = car.mass
    q_down, q_drag = 0.5 * track.rho * car.cza, 0.5 * track.rho * car.cxa
    n0 = (m * lapsim.G) ** car.load_sensitivity
    kappa, slope = np.abs(track.curvature), track.slope
    env = vc.copy()
    start = int(np.argmin(vc))
    v = vc[start]
    for step in range(2 * n):
        i = (start - step) % n
        v = min(v, vc[i])
        env[i] = v
        normal = m * lapsim.G + q_down * v * v
        grip = car.grip * n0 * normal ** (1 - car.load_sensitivity)
        left = 1 - (m * v * v * kappa[i] / grip) ** 2
        g_long = grip * np.sqrt(left) if left > 0 else 0.0
        decel = (g_long + q_drag * v * v + car.rolling * normal + m * lapsim.G * slope[i]) / m
        v = float(np.sqrt(max(v * v + 2 * max(decel, 0.0) * ds, 1.0)))
    return env


def game_data(track, car, ai_lap, corners, every=1):
    """Everything the page needs. The physics uses every simulated point (4 m): thinning would
    smooth away the tightest corner limits and make the lap easier than the simulator's."""
    sl = slice(None, None, every)
    vc = np.minimum(lapsim.corner_limit(car, track), 120.0)
    real = np.asarray(ai_lap["real_kmh"]) / 3.6
    n = len(real)
    ds = track.length / n
    real_time = np.r_[0, np.cumsum(2 * ds / (real + np.roll(real, -1)))]
    return {
        "x": np.round(track.x[sl], 1).tolist(), "y": np.round(track.y[sl], 1).tolist(),
        "vc": np.round(vc[sl], 2).tolist(), "env": np.round(braking_envelope(car, track, vc)[sl], 2).tolist(), "kappa": np.round(np.abs(track.curvature[sl]), 5).tolist(),
        "slope": np.round(track.slope[sl], 4).tolist(), "length": float(track.length), "rho": float(track.rho),
        "car": {"m": car.mass, "p": car.power_kw * 1000, "cza": car.cza, "cxa": car.cxa, "grip": car.grip,
                "ls": car.load_sensitivity, "rear": car.rear_share, "roll": car.rolling},
        "ai_t": ai_lap["ai_time"] + [ai_lap["ai_lap"]], "ai_kmh": ai_lap["ai_kmh"], "ai_lap": ai_lap["ai_lap"],
        "real_t": np.round(real_time, 3).tolist(), "real_lap": ai_lap["real_lap"], "real_kmh": ai_lap["real_kmh"],
        "sim_lap": ai_lap["sim_lap"], "sim_kmh": ai_lap["sim_kmh"],
        "corners": corners,
    }


def drive(data, dark=True, height=620):
    components.html(PAGE.replace("__DATA__", json.dumps({**data, "dark": dark})), height=height)


# The theme below must stay in step with THEMES in style.py.
PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; font-family: Inter, system-ui, sans-serif;
               -webkit-user-select: none; user-select: none; touch-action: manipulation; }
  #app { display: flex; flex-direction: column; gap: 10px; height: 100%; }
  #stage { position: relative; flex: 1; min-height: 300px; border-radius: 16px; overflow: hidden;
           border: 1px solid var(--border); background: var(--bg); outline: none; }
  canvas { display: block; width: 100%; height: 100%; }
  #hud { position: absolute; left: 12px; top: 12px; padding: 10px 12px; border-radius: 12px; min-width: 170px;
         background: var(--panel); border: 1px solid var(--border); color: var(--text); font-size: 12px; }
  #clock { font: 800 26px 'Saira Condensed', Inter, sans-serif; letter-spacing: .5px; }
  #delta { font: 800 18px 'Saira Condensed', Inter, sans-serif; }
  #speed { position: absolute; right: 12px; top: 12px; padding: 8px 14px; border-radius: 12px; text-align: right;
           background: var(--panel); border: 1px solid var(--border); color: var(--text); }
  #speed b { font: 800 34px 'Saira Condensed', Inter, sans-serif; display: block; line-height: 1; }
  #speed span { font-size: 11px; color: var(--muted); }
  #msg { position: absolute; left: 50%; top: 38%; transform: translate(-50%, -50%); text-align: center;
         font: 800 44px 'Saira Condensed', Inter, sans-serif; color: var(--text); pointer-events: none;
         text-shadow: 0 2px 12px var(--bg); }
  #msg small { display: block; font: 600 14px Inter, sans-serif; color: var(--muted); margin-top: 6px; }
  #mini { position: absolute; right: 12px; bottom: 12px; width: 150px; height: 150px; border-radius: 12px;
          background: var(--panel); border: 1px solid var(--border); }
  #result { position: absolute; inset: 0; display: none; align-items: center; justify-content: center;
            background: var(--veil); }
  #card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 18px 20px;
          color: var(--text); width: min(440px, 88%); }
  #card h3 { margin: 0 0 10px; font: 800 26px 'Saira Condensed', Inter, sans-serif; text-transform: uppercase; }
  #card .row { display: flex; justify-content: space-between; padding: 6px 0; border-top: 1px solid var(--border);
               font-variant-numeric: tabular-nums; }
  #card .row b { font-weight: 700; }
  #card canvas { width: 100%; height: 110px; margin-top: 8px; }
  #controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  button { font: 600 12px Inter, system-ui, sans-serif; padding: 9px 14px; border-radius: 999px; cursor: pointer;
           border: 1px solid var(--border); background: var(--panel); color: var(--text); }
  button:hover { border-color: #e10600; color: #e10600; }
  #go { background: #e10600; border-color: #e10600; color: #fff; }
  label { font-size: 12px; color: var(--text); display: flex; align-items: center; gap: 6px; }
  #pedals { position: absolute; left: 0; right: 0; bottom: 12px; display: flex; justify-content: space-between;
            padding: 0 12px; pointer-events: none; }
  .pedal { pointer-events: auto; width: 120px; height: 84px; border-radius: 16px; display: flex; align-items: center;
           justify-content: center; font: 800 18px 'Saira Condensed', Inter, sans-serif; letter-spacing: 1px;
           color: #fff; opacity: .82; touch-action: none; }
  .pedal.on { opacity: 1; transform: scale(.97); }
  #brk { background: #e4544a; } #thr { background: #1fd6a0; color: #0b0b10; margin-right: 162px; }
  @media (max-width: 560px) { #mini { width: 100px; height: 100px; } #thr { margin-right: 112px; }
    .pedal { width: 96px; height: 76px; } #msg { font-size: 34px; } }
</style></head>
<body>
<div id="app">
  <div id="stage" tabindex="0">
    <canvas id="view"></canvas>
    <div id="hud"><div id="clock">0:00.000</div><div id="delta">±0.000</div>
      <div style="color:var(--muted)">against the AI driver</div></div>
    <div id="speed"><b id="kmh">0</b><span>km/h · gear <span id="gear">-</span></span></div>
    <canvas id="mini"></canvas>
    <div id="pedals"><div class="pedal" id="brk">BRAKE</div><div class="pedal" id="thr">THROTTLE</div></div>
    <div id="msg">Press Start<small>↑ / W throttle · ↓ / S / space brake · or the buttons</small></div>
    <div id="result"><div id="card"></div></div>
  </div>
  <div id="controls">
    <button id="go">Start</button>
    <label><input type="checkbox" id="guide" checked> Braking guide</label>
    <label><input type="checkbox" id="slow"> Half speed (learner)</label>
  </div>
</div>
<script>
const D = __DATA__;
const T = D.dark
  ? { bg: "#0b0b10", panel: "rgba(21,21,30,.9)", border: "#2c2c3a", text: "#f5f5f7", muted: "#a3a3b2",
      road: "#2a2a36", edge: "#4a4a5a", veil: "rgba(11,11,16,.6)" }
  : { bg: "#f6f6f3", panel: "rgba(255,255,255,.94)", border: "#d9d9d4", text: "#15151e", muted: "#55556a",
      road: "#d6d6dc", edge: "#b0b0ba", veil: "rgba(246,246,243,.6)" };
for (const [k, v] of Object.entries(T)) document.documentElement.style.setProperty("--" + k, v);

const N = D.x.length, L = D.length, DS = L / N, G = 9.81, C = D.car;
const qd = 0.5 * D.rho * C.cza, qx = 0.5 * D.rho * C.cxa, n0 = Math.pow(C.m * G, C.ls);
const RED = "#e10600", AI = "#27f4d2", REAL = "#e8b33a";

// ---------- physics: the same equations as lapsim.py ----------
function at(arr, s) {                      // linear interpolation round the lap
  const f = ((s % L) + L) % L / DS, i = Math.floor(f) % N, j = (i + 1) % N, w = f - Math.floor(f);
  return arr[i] * (1 - w) + arr[j] * w;
}
function grip(v, s) {
  const normal = C.m * G + qd * v * v;
  const g = C.grip * n0 * Math.pow(normal, 1 - C.ls);
  const lat = C.m * v * v * at(D.kappa, s);
  const left = 1 - (lat / g) * (lat / g);
  return [left > 0 ? g * Math.sqrt(left) : 0.1 * g, normal];
}
function accel(v, s, thr, brk) {
  const [g, normal] = grip(v, s);
  const resist = qx * v * v + C.roll * normal + C.m * G * at(D.slope, s);
  if (brk) return -(g + resist) / C.m;
  if (thr) return (Math.min(C.p / Math.max(v, 1), g * C.rear) - resist) / C.m;
  return -resist / C.m;
}
function maxDecel(v, s) { const [g, normal] = grip(v, s); return (g + qx * v * v + C.roll * normal) / C.m; }
function timeAt(ts, s) {                   // a ghost's lap time when it reaches distance s
  const f = Math.min(Math.max(s, 0), L) / L * (ts.length - 1), i = Math.floor(f), w = f - i;
  return i >= ts.length - 1 ? ts[ts.length - 1] : ts[i] * (1 - w) + ts[i + 1] * w;
}
function distAt(ts, t) {                   // where a ghost is at time t
  if (t >= ts[ts.length - 1]) return L;
  let lo = 0, hi = ts.length - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (ts[mid] <= t) lo = mid; else hi = mid; }
  return (lo + (t - ts[lo]) / Math.max(ts[hi] - ts[lo], 1e-6)) / (ts.length - 1) * L;
}
function gearOf(kmh) { const top = 350; for (let g = 1; g <= 8; g++) if (kmh <= top * Math.pow(0.30, (8 - g) / 7)) return g; return 8; }

// ---------- state ----------
let S = null, thr = false, brk = false;
const keys = new Set();
const stage = document.getElementById("stage");
function setPedals() {
  thr = keys.has("thr") || keys.has("ArrowUp") || keys.has("w") || keys.has("W");
  brk = keys.has("brk") || keys.has("ArrowDown") || keys.has("s") || keys.has("S") || keys.has(" ");
  document.getElementById("thr").classList.toggle("on", thr);
  document.getElementById("brk").classList.toggle("on", brk);
}
addEventListener("keydown", e => { if (["ArrowUp", "ArrowDown", " "].includes(e.key)) e.preventDefault(); keys.add(e.key); setPedals(); });
addEventListener("keyup", e => { keys.delete(e.key); setPedals(); });
for (const [id, k] of [["thr", "thr"], ["brk", "brk"]]) {
  const el = document.getElementById(id);
  el.addEventListener("pointerdown", e => { e.preventDefault(); el.setPointerCapture(e.pointerId); keys.add(k); setPedals(); });
  for (const ev of ["pointerup", "pointercancel", "pointerleave"]) el.addEventListener(ev, () => { keys.delete(k); setPedals(); });
}

function start() {
  S = { s: 0, v: D.ai_kmh[0] / 3.6, t: 0, countdown: 3, offs: 0, trace: [], done: false, msgUntil: 0 };
  document.getElementById("result").style.display = "none";
  stage.focus();
}
document.getElementById("go").onclick = start;

// ---------- drawing ----------
const view = document.getElementById("view"), vx = view.getContext("2d");
const mini = document.getElementById("mini"), mx = mini.getContext("2d");
function fit(c) { const r = c.getBoundingClientRect(), d = devicePixelRatio || 1;
  if (c.width !== Math.round(r.width * d)) { c.width = Math.round(r.width * d); c.height = Math.round(r.height * d); }
  return d; }
const minX = Math.min(...D.x), maxX = Math.max(...D.x), minY = Math.min(...D.y), maxY = Math.max(...D.y);

function drawMini(sYou, sAi, sReal) {
  const d = fit(mini), w = mini.width, h = mini.height, pad = 10 * d;
  const sc = Math.min((w - 2 * pad) / (maxX - minX), (h - 2 * pad) / (maxY - minY));
  const px = x => pad + (x - minX) * sc + (w - 2 * pad - (maxX - minX) * sc) / 2;
  const py = y => h - pad - (y - minY) * sc - (h - 2 * pad - (maxY - minY) * sc) / 2;
  mx.clearRect(0, 0, w, h); mx.lineWidth = 3 * d; mx.strokeStyle = T.edge; mx.beginPath();
  for (let i = 0; i <= N; i++) { const k = i % N; i ? mx.lineTo(px(D.x[k]), py(D.y[k])) : mx.moveTo(px(D.x[k]), py(D.y[k])); }
  mx.stroke();
  for (const [s, col] of [[sReal, REAL], [sAi, AI], [sYou, RED]]) {
    mx.fillStyle = col; mx.beginPath(); mx.arc(px(at(D.x, s)), py(at(D.y, s)), 4 * d, 0, 7); mx.fill();
  }
}

function drawView(sYou, sAi, sReal, v) {
  const d = fit(view), w = view.width, h = view.height;
  vx.fillStyle = T.bg; vx.fillRect(0, 0, w, h);
  const ahead = 6, cx = at(D.x, sYou), cy = at(D.y, sYou);
  const hx = at(D.x, sYou + ahead) - cx, hy = at(D.y, sYou + ahead) - cy;
  const ang = Math.atan2(hy, hx);
  const zoom = Math.min(w, h) / (170 + v * 1.4);            // zooms out with speed
  vx.save();
  vx.translate(w / 2, h * 0.66); vx.scale(zoom, -zoom); vx.rotate(Math.PI / 2 - ang); vx.translate(-cx, -cy);
  // road
  const from = sYou - 250, to = sYou + 900;
  const path = () => { vx.beginPath(); for (let s = from; s <= to; s += DS) { const x = at(D.x, s), y = at(D.y, s); s === from ? vx.moveTo(x, y) : vx.lineTo(x, y); } };
  vx.lineCap = "round"; vx.lineJoin = "round";
  path(); vx.strokeStyle = T.edge; vx.lineWidth = 16; vx.stroke();
  path(); vx.strokeStyle = T.road; vx.lineWidth = 13; vx.stroke();
  // braking guide: red where, at your speed now, you'd already need to be braking for what comes next
  if (document.getElementById("guide").checked) {
    // braking guide: amber, then red, on the road ahead where your speed now is above the fastest
    // you could be there and still make what follows (the braking envelope)
    for (let s = sYou; s < to; s += DS) {
      const share = v / Math.max(at(D.env, s), 1);
      if (share < 0.97) continue;
      vx.strokeStyle = share >= 1 ? "#e4544a" : "#e8b33a";
      vx.lineWidth = 4; vx.beginPath(); vx.moveTo(at(D.x, s), at(D.y, s)); vx.lineTo(at(D.x, s + DS), at(D.y, s + DS)); vx.stroke();
    }
  }
  // start line
  vx.strokeStyle = T.text; vx.lineWidth = 2;
  const nx = -(D.y[1] - D.y[0]), ny = D.x[1] - D.x[0], nl = Math.hypot(nx, ny);
  vx.beginPath(); vx.moveTo(D.x[0] + nx / nl * 8, D.y[0] + ny / nl * 8); vx.lineTo(D.x[0] - nx / nl * 8, D.y[0] - ny / nl * 8); vx.stroke();
  // cars: ghosts first, you on top
  const car = (s, col, alpha) => {
    const x = at(D.x, s), y = at(D.y, s), a = Math.atan2(at(D.y, s + 3) - y, at(D.x, s + 3) - x);
    vx.save(); vx.translate(x, y); vx.rotate(a); vx.globalAlpha = alpha; vx.fillStyle = col;
    vx.fillRect(-2.8, -1, 5.6, 2); vx.fillRect(1.6, -1.6, 1.4, 3.2); vx.fillRect(-2.8, -1.5, 1, 3); vx.restore();
  };
  car(sReal, REAL, 0.75); car(sAi, AI, 0.85); car(sYou, RED, 1);
  vx.restore();
}

function lapClock(t) { const m = Math.floor(t / 60), s = t - 60 * m; return m + ":" + (s < 10 ? "0" : "") + s.toFixed(3); }

function finish() {
  S.done = true;
  const you = S.t, rows = [["You", you, RED], ["AI driver", D.ai_lap, AI], ["Real fastest lap", D.real_lap, REAL],
                           ["Perfect physics (the simulator)", D.sim_lap, "#8a8a96"]];
  rows.sort((a, b) => a[1] - b[1]);
  const beatAi = you < D.ai_lap, beatReal = you < D.real_lap;
  const title = beatReal ? "Faster than the real lap!" : beatAi ? "You beat the AI driver" : "The AI driver wins this one";
  let html = `<h3>${title}</h3>`;
  for (const [name, t, col] of rows)
    html += `<div class="row"><span><i style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${col};margin-right:6px"></i>${name}</span><b>${lapClock(t)}</b></div>`;
  html += `<div class="row"><span>Times you ran wide</span><b>${S.offs}</b></div>`;
  html += `<canvas id="trace"></canvas><div style="font-size:11px;color:var(--muted)">Your speed (red) against the AI driver's (teal) all the way round.</div>`;
  document.getElementById("card").innerHTML = html;
  document.getElementById("result").style.display = "flex";
  const c = document.getElementById("trace"), d = fit(c), x = c.getContext("2d"), w = c.width, h = c.height;
  const sx = s => s / L * w, sy = k => h - k / 360 * h;
  x.lineWidth = 1.5 * d;
  x.strokeStyle = AI; x.beginPath(); D.ai_kmh.forEach((k, i) => { const X = i / D.ai_kmh.length * w; i ? x.lineTo(X, sy(k)) : x.moveTo(X, sy(k)); }); x.stroke();
  x.strokeStyle = RED; x.beginPath(); S.trace.forEach(([s, k], i) => i ? x.lineTo(sx(s), sy(k)) : x.moveTo(sx(s), sy(k))); x.stroke();
}

// ---------- the loop ----------
let last = performance.now();
function frame(now) {
  let dt = Math.min((now - last) / 1000, 1 / 20); last = now;
  if (document.getElementById("slow").checked) dt *= 0.5;
  const msg = document.getElementById("msg");
  if (S && !S.done) {
    if (S.countdown > 0) {
      S.countdown -= dt; msg.innerHTML = Math.ceil(Math.max(S.countdown, 0.01)) + "<small>get ready</small>";
    } else {
      // small sub-steps keep the physics stable at any frame rate
      const steps = Math.max(1, Math.ceil(dt / 0.005)), h = dt / steps;
      for (let k = 0; k < steps && !S.done; k++) {
        const a = accel(S.v, S.s, thr, brk);
        S.v = Math.max(S.v + a * h, 8);
        S.s += S.v * h; S.t += h;
        const lim = at(D.vc, S.s);
        if (S.v > lim * 1.005) {
          // over the tyres' limit: the car runs wide. Running wide must never be a shortcut, so it
          // costs more than braking would have.
          S.v = lim * 0.55; S.t += 0.3; S.offs += 1; S.msgUntil = S.t + 1.2;
        }
        if (S.trace.length === 0 || S.s - S.trace[S.trace.length - 1][0] > 8) S.trace.push([S.s, S.v * 3.6]);
        if (S.s >= L) { S.t -= (S.s - L) / S.v; S.s = L; finish(); }
      }
      msg.innerHTML = S.t < S.msgUntil ? "RAN WIDE<small>too fast for this corner</small>" : "";
    }
    const tAi = timeAt(D.ai_t, S.s), delta = S.t - tAi;
    document.getElementById("clock").textContent = lapClock(S.t);
    const del = document.getElementById("delta");
    del.textContent = (delta >= 0 ? "+" : "−") + Math.abs(delta).toFixed(3);
    del.style.color = delta <= 0 ? "#1fd6a0" : "#e4544a";
    document.getElementById("kmh").textContent = Math.round(S.v * 3.6);
    document.getElementById("gear").textContent = gearOf(S.v * 3.6);
  }
  const sYou = S ? S.s : 0, t = S ? S.t : 0;
  const sAi = S && S.countdown <= 0 ? distAt(D.ai_t, t) : 0, sReal = S && S.countdown <= 0 ? distAt(D.real_t, t) : 0;
  drawView(sYou, sAi, sReal, S ? S.v : D.ai_kmh[0] / 3.6);
  drawMini(sYou, sAi, sReal);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script></body></html>
"""
