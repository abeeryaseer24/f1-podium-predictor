"""Circuit Designer: draw a circuit and watch the lap simulator drive it, live in the browser.

The visitor drags points to shape a closed track (a smooth spline through them). Every time it
changes, the page runs the same three passes as lapsim.py on it, in JavaScript:
  1. the corner limit at every 4 m, from the tyres' grip plus downforce against the curvature
  2. a forward pass: as hard on the power as the engine and the rear tyres allow
  3. a backward pass: braking as late as the tyres allow
It reports the lap time, length, top speed, the slowest corner, the share at full throttle, the
corners (each braking zone) and the overtaking spots (a long straight into a heavy stop), and colours
the track by full throttle, cornering on the limit and braking, like the Lap Simulator.

The car is the median of every calibrated car of the season, so lap times are comparable with the real
circuits. The wing slider moves downforce and drag together, as in lapsim.py.

designer(car, dark) draws it; the car is a dict of lapsim.Car fields.
"""
import json

import streamlit.components.v1 as components

import lapsim


def designer(car, dark=True, height=760):
    data = {"dark": dark, "car": {"m": car.mass, "p": car.power_kw * 1000, "wing": car.wing, "grip": car.grip,
                                  "ls": car.load_sensitivity, "rear": car.rear_share, "roll": car.rolling},
            "cza": [lapsim.CZA_LOW, lapsim.CZA_HIGH], "cxa": [lapsim.CXA_LOW, lapsim.CXA_HIGH],
            "drag_curve": lapsim.DRAG_CURVE}
    components.html(PAGE.replace("__DATA__", json.dumps(data)), height=height)


# The theme below must stay in step with THEMES in style.py.
PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; font-family: Inter, system-ui, sans-serif; color: var(--text); -webkit-user-select: none; user-select: none; }
  #app { display: flex; flex-direction: column; gap: 10px; }
  #tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .tile { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 8px 12px; }
  .tile small { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .5px; }
  .tile b { display: block; font: 800 26px 'Saira Condensed', Inter, sans-serif; }
  .tile b.red { color: #e10600; }
  #stage { position: relative; height: 430px; border-radius: 16px; overflow: hidden; border: 1px solid var(--border);
           background: var(--bg); touch-action: none; }
  canvas { display: block; width: 100%; height: 100%; }
  #legend { position: absolute; left: 10px; bottom: 10px; display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px;
            padding: 6px 10px; border-radius: 10px; background: var(--panel); border: 1px solid var(--border); }
  #legend span { display: flex; align-items: center; gap: 5px; font-weight: 600; }
  #legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  #hint { position: absolute; right: 10px; top: 10px; font-size: 11px; color: var(--muted); max-width: 45%; text-align: right; }
  #controls { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  button { font: 600 12px Inter, system-ui, sans-serif; padding: 8px 13px; border-radius: 999px; cursor: pointer;
           border: 1px solid var(--border); background: var(--panel); color: var(--text); }
  button:hover { border-color: #e10600; color: #e10600; }
  label { font-size: 12px; display: flex; align-items: center; gap: 6px; }
  input[type=range] { accent-color: #e10600; width: 140px; }
  #trace { height: 150px; border-radius: 12px; border: 1px solid var(--border); background: var(--panel); }
  #notes { font-size: 12px; color: var(--muted); }
  @media (max-width: 560px) { #tiles { grid-template-columns: repeat(2, 1fr); } #stage { height: 360px; } #hint { display: none; } }
</style></head>
<body>
<div id="app">
  <div id="tiles">
    <div class="tile"><small>Lap time</small><b class="red" id="lap">–</b></div>
    <div class="tile"><small>Length</small><b id="len">–</b></div>
    <div class="tile"><small>Top speed / slowest</small><b id="spd">–</b></div>
    <div class="tile"><small>Full throttle</small><b id="full">–</b></div>
  </div>
  <div id="stage"><canvas id="map"></canvas>
    <div id="legend"><span><i style="background:#1fd6a0"></i>Full throttle</span><span><i style="background:#e8b33a"></i>Cornering on the limit</span><span><i style="background:#e4544a"></i>Braking</span><span><i style="background:#ffffff;border:2px solid #e10600"></i>Overtaking spot</span></div>
    <div id="hint">Drag a point to move it · tap the track to add one · double-tap a point to remove it</div>
  </div>
  <div id="controls">
    <button data-preset="flowing">Fast and flowing</button>
    <button data-preset="stop">Stop and go</button>
    <button data-preset="street">Street circuit</button>
    <button data-preset="oval">Oval</button>
    <label>Wing <input type="range" id="wing" min="0" max="1" step="0.01"> <span id="wingv"></span></label>
  </div>
  <canvas id="trace"></canvas>
  <div id="notes"></div>
</div>
<script>
const D = __DATA__;
const T = D.dark
  ? { bg: "#0b0b10", panel: "#15151e", border: "#2c2c3a", text: "#f5f5f7", muted: "#a3a3b2", grid: "#1b1b25", road: "#2a2a36" }
  : { bg: "#f6f6f3", panel: "#ffffff", border: "#d9d9d4", text: "#15151e", muted: "#55556a", grid: "#e6e6e1", road: "#cfcfd6" };
for (const [k, v] of Object.entries(T)) document.documentElement.style.setProperty("--" + k, v);
const G = 9.81, RHO = 1.2, STEP = 4, WORLD = { w: 2600, h: 1700 };     // metres shown on the map
const MODE = { throttle: "#1fd6a0", corner: "#e8b33a", brake: "#e4544a" };

// ---------- presets: our own shapes, in metres ----------
// Each corner is [x, y, d]: the corner of a polygon, rounded by two control points d metres either
// side of it. A small d makes a tight hairpin, a large one a fast sweeper.
const SHAPES = {
  flowing: [[300,300,110],[1500,200,170],[2300,380,60],[2250,900,28],[1750,820,22],[1450,1300,55],[750,1450,90],[300,1050,35]],
  stop:    [[300,250,50],[2300,250,45],[2300,700,42],[1400,700,36],[1400,1000,38],[2300,1050,45],[2300,1450,50],[300,1450,50],[300,950,38],[850,850,60],[300,650,38]],
  street:  [[450,350,22],[1300,350,20],[1300,650,18],[1750,650,18],[1750,350,20],[2250,350,25],[2250,1300,30],[1500,1300,18],[1500,1000,16],[950,1000,16],[950,1350,20],[450,1350,22],[450,900,18],[750,900,16],[750,600,18],[450,600,18]],
  oval:    [[450,400,420],[2150,400,420],[2150,1300,420],[450,1300,420]],
};
function rounded(shape) {
  const out = [], n = shape.length;
  for (let i = 0; i < n; i++) {
    const [x, y, d] = shape[i], a = shape[(i - 1 + n) % n], b = shape[(i + 1) % n];
    const la = Math.hypot(a[0] - x, a[1] - y), lb = Math.hypot(b[0] - x, b[1] - y);
    const da = Math.min(d, la * 0.45), db = Math.min(d, lb * 0.45);
    out.push([x + (a[0] - x) / la * da, y + (a[1] - y) / la * da], [x + (b[0] - x) / lb * db, y + (b[1] - y) / lb * db]);
  }
  return out;
}
// every preset is scaled to a realistic length (the oval to a short-track 4 km)
const LENGTHS = { flowing: 5300, stop: 5000, street: 4800, oval: 4000 };
function scaled(points, target) {
  const L = resample(spline(points)).L, f = target / L;
  const cx = points.reduce((a, p) => a + p[0], 0) / points.length, cy = points.reduce((a, p) => a + p[1], 0) / points.length;
  return points.map(([x, y]) => [WORLD.w / 2 + (x - cx) * f, WORLD.h / 2 + (y - cy) * f]);
}
const PRESETS = {};
function preset(name) {
  if (!PRESETS[name]) PRESETS[name] = scaled(rounded(SHAPES[name]), LENGTHS[name]);
  return PRESETS[name].map(p => p.slice());
}
let ctrl = null;
let wing = D.car.wing;

// ---------- the track from the control points ----------
function spline(points, per = 40) {            // closed centripetal Catmull-Rom: no loops or overshoot
  const out = [], n = points.length;
  const tj = (ti, a, b) => ti + Math.sqrt(Math.max(Math.hypot(b[0] - a[0], b[1] - a[1]), 1e-6));
  for (let i = 0; i < n; i++) {
    const p0 = points[(i - 1 + n) % n], p1 = points[i], p2 = points[(i + 1) % n], p3 = points[(i + 2) % n];
    const t0 = 0, t1 = tj(t0, p0, p1), t2 = tj(t1, p1, p2), t3 = tj(t2, p2, p3);
    for (let k = 0; k < per; k++) {
      const t = t1 + (t2 - t1) * k / per, pt = [];
      for (let c = 0; c < 2; c++) {
        const a1 = (t1 - t) / (t1 - t0) * p0[c] + (t - t0) / (t1 - t0) * p1[c];
        const a2 = (t2 - t) / (t2 - t1) * p1[c] + (t - t1) / (t2 - t1) * p2[c];
        const a3 = (t3 - t) / (t3 - t2) * p2[c] + (t - t2) / (t3 - t2) * p3[c];
        const b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2;
        const b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3;
        pt.push((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2);
      }
      out.push(pt);
    }
  }
  return out;
}
function resample(pts) {                       // evenly every STEP metres round the loop
  const n = pts.length, cum = [0];
  for (let i = 1; i <= n; i++) { const a = pts[i - 1], b = pts[i % n]; cum.push(cum[i - 1] + Math.hypot(b[0] - a[0], b[1] - a[1])); }
  const L = cum[n], m = Math.max(50, Math.round(L / STEP)), out = [];
  let j = 0;
  for (let k = 0; k < m; k++) {
    const s = k * L / m;
    while (cum[j + 1] < s) j++;
    const w = (s - cum[j]) / Math.max(cum[j + 1] - cum[j], 1e-9), a = pts[j], b = pts[(j + 1) % n];
    out.push([a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w]);
  }
  return { pts: out, L };
}
function curvature(pts, ds) {                  // signed 1/m from the change of heading, lightly smoothed
  const n = pts.length, h = [], k = new Array(n);
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[(i + 1) % n]; h.push(Math.atan2(b[1] - a[1], b[0] - a[0])); }
  for (let i = 0; i < n; i++) { let d = h[i] - h[(i - 1 + n) % n]; d = Math.atan2(Math.sin(d), Math.cos(d)); k[i] = d / ds; }
  const sig = Math.max(1, Math.round(6 / ds)), r = 3 * sig, w = [];
  for (let j = -r; j <= r; j++) w.push(Math.exp(-0.5 * (j / sig) ** 2));
  const ws = w.reduce((a, b) => a + b, 0), out = new Array(n);
  for (let i = 0; i < n; i++) { let s = 0; for (let j = -r; j <= r; j++) s += w[j + r] * k[(i + j + n) % n]; out[i] = s / ws; }
  return out;
}

// ---------- the lap simulator (the same passes as lapsim.py) ----------
function simulate(pts, L) {
  const n = pts.length, ds = L / n, C = D.car, m = C.m;
  const cza = (D.cza[0] + wing * (D.cza[1] - D.cza[0])), cxa = (D.cxa[0] + Math.pow(wing, D.drag_curve) * (D.cxa[1] - D.cxa[0]));
  const qd = 0.5 * RHO * cza, qx = 0.5 * RHO * cxa, n0 = Math.pow(m * G, C.ls);
  const kap = curvature(pts, ds).map(Math.abs);
  const grip = N => C.grip * n0 * Math.pow(N, 1 - C.ls);
  const vc = kap.map(k => { let lo = 5, hi = 150;
    for (let it = 0; it < 40; it++) { const v = (lo + hi) / 2; if (grip(m * G + qd * v * v) >= m * v * v * k) lo = v; else hi = v; }
    return lo; });
  const longGrip = (v, i) => { const N = m * G + qd * v * v, g = grip(N), left = 1 - (m * v * v * kap[i] / g) ** 2;
    return [left > 0 ? g * Math.sqrt(left) : 0, N]; };
  let start = 0; for (let i = 1; i < n; i++) if (vc[i] < vc[start]) start = i;
  const fwd = new Array(n), bwd = new Array(n);
  let v = vc[start];
  for (let s = 0; s < n; s++) { const i = (start + s) % n; v = Math.min(v, vc[i]); fwd[i] = v;
    const [g, N] = longGrip(v, i); const a = (Math.min(C.p / Math.max(v, 1), g * C.rear) - qx * v * v - C.roll * N) / m;
    v = Math.sqrt(Math.max(v * v + 2 * a * ds, 1)); }
  v = vc[start];
  for (let s = 0; s < n; s++) { const i = (start - s + n) % n; v = Math.min(v, vc[i], fwd[i]); bwd[i] = v;
    const [g, N] = longGrip(v, i); const d = (g + qx * v * v + C.roll * N) / m;
    v = Math.sqrt(Math.max(v * v + 2 * Math.max(d, 0) * ds, 1)); }
  const speed = fwd.map((f, i) => Math.min(f, bwd[i]));
  let t = 0; for (let i = 0; i < n; i++) t += 2 * ds / (speed[i] + speed[(i + 1) % n]);
  const mode = speed.map((sp, i) => bwd[i] < fwd[i] - 1e-6 ? "brake" : sp >= vc[i] - 1e-6 ? "corner" : "throttle");
  return { speed, mode, lap: t, ds, kap };
}

// corners = braking zones; an overtaking spot = a stop from above 270 km/h to below 160 km/h after 500 m of straight
function analyse(sim) {
  const n = sim.speed.length, zones = [];
  for (let i = 0; i < n; i++) if (sim.mode[i] === "brake" && sim.mode[(i - 1 + n) % n] !== "brake") {
    let j = i; while (sim.mode[j % n] === "brake" && j < i + n) j++;
    let straight = 0, k = (i - 1 + n) % n; while (sim.mode[k] === "throttle" && straight < n) { straight++; k = (k - 1 + n) % n; }
    const vin = sim.speed[i] * 3.6, vout = sim.speed[(j - 1) % n] * 3.6;
    zones.push({ i, vin, vout, straight: straight * sim.ds, pass: vin > 270 && vout < 160 && straight * sim.ds > 500 });
  }
  return zones;
}

// ---------- drawing ----------
const map = document.getElementById("map"), mx = map.getContext("2d");
const tr = document.getElementById("trace"), tx = tr.getContext("2d");
function fit(c) { const r = c.getBoundingClientRect(), d = devicePixelRatio || 1;
  if (c.width !== Math.round(r.width * d) || c.height !== Math.round(r.height * d)) { c.width = Math.round(r.width * d); c.height = Math.round(r.height * d); } return d; }
let view = { s: 1, ox: 0, oy: 0 };
function toScreen(p) { return [view.ox + p[0] * view.s, view.oy + p[1] * view.s]; }
function toWorld(x, y) { return [(x - view.ox) / view.s, (y - view.oy) / view.s]; }

let track = null, sim = null, zones = [];
function rebuild() {
  track = resample(spline(ctrl));
  sim = simulate(track.pts, track.L);
  zones = analyse(sim);
  const fmt = t => Math.floor(t / 60) + ":" + (t % 60).toFixed(3).padStart(6, "0");
  const sp = sim.speed.map(v => v * 3.6);
  document.getElementById("lap").textContent = fmt(sim.lap);
  document.getElementById("len").textContent = (track.L / 1000).toFixed(2) + " km";
  document.getElementById("spd").textContent = Math.round(Math.max(...sp)) + " / " + Math.round(Math.min(...sp));
  document.getElementById("full").textContent = Math.round(100 * sim.mode.filter(m => m === "throttle").length / sim.mode.length) + "%";
  const tight = Math.max(...sim.kap) > 1 / 10;
  const passes = zones.filter(z => z.pass).length;
  document.getElementById("notes").innerHTML =
    `${zones.length} corners that need the brakes · ${passes} overtaking spot${passes === 1 ? "" : "s"} · average ${(track.L / sim.lap * 3.6).toFixed(0)} km/h` +
    (track.L < 3000 ? " · <b>shorter than any current circuit</b> (the rules ask for at least 3.5 km)" : "") +
    (track.L > 7000 ? " · <b>longer than any current circuit</b>" : "") +
    (tight ? " · <b>one corner is under 10 m radius</b>, very tight for an F1 car" : "");
  draw();
}

function draw() {
  const d = fit(map), w = map.width, h = map.height;
  view.s = Math.min(w / WORLD.w, h / WORLD.h); view.ox = (w - WORLD.w * view.s) / 2; view.oy = (h - WORLD.h * view.s) / 2;
  mx.fillStyle = T.bg; mx.fillRect(0, 0, w, h);
  mx.strokeStyle = T.grid; mx.lineWidth = 1;
  for (let x = 0; x <= WORLD.w; x += 100) { const [a] = toScreen([x, 0]); mx.beginPath(); mx.moveTo(a, view.oy); mx.lineTo(a, view.oy + WORLD.h * view.s); mx.stroke(); }
  for (let y = 0; y <= WORLD.h; y += 100) { const [, b] = toScreen([0, y]); mx.beginPath(); mx.moveTo(view.ox, b); mx.lineTo(view.ox + WORLD.w * view.s, b); mx.stroke(); }
  const P = track.pts, n = P.length;
  mx.lineCap = "round"; mx.lineJoin = "round";
  mx.strokeStyle = T.road; mx.lineWidth = 14 * d; mx.beginPath();
  P.forEach((p, i) => { const [x, y] = toScreen(p); i ? mx.lineTo(x, y) : mx.moveTo(x, y); }); mx.closePath(); mx.stroke();
  mx.lineWidth = 6 * d;
  for (let i = 0; i < n; i++) { const a = toScreen(P[i]), b = toScreen(P[(i + 1) % n]);
    mx.strokeStyle = MODE[sim.mode[i]]; mx.beginPath(); mx.moveTo(a[0], a[1]); mx.lineTo(b[0], b[1]); mx.stroke(); }
  for (const z of zones) if (z.pass) { const [x, y] = toScreen(P[z.i]);
    mx.fillStyle = "#ffffff"; mx.strokeStyle = "#e10600"; mx.lineWidth = 3 * d; mx.beginPath(); mx.arc(x, y, 7 * d, 0, 7); mx.fill(); mx.stroke(); }
  const [sx, sy] = toScreen(P[0]), [nx, ny] = toScreen(P[3]);
  const ang = Math.atan2(ny - sy, nx - sx);
  mx.save(); mx.translate(sx, sy); mx.rotate(ang); mx.fillStyle = T.text; mx.fillRect(-2 * d, -11 * d, 4 * d, 22 * d); mx.restore();
  ctrl.forEach((p, i) => { const [x, y] = toScreen(p);
    mx.fillStyle = i === drag ? "#e10600" : T.panel; mx.strokeStyle = "#e10600"; mx.lineWidth = 2.5 * d;
    mx.beginPath(); mx.arc(x, y, 8 * d, 0, 7); mx.fill(); mx.stroke(); });
  mx.fillStyle = T.muted; mx.font = `${11 * d}px Inter`; mx.fillText("grid squares are 100 m", 10 * d, 18 * d);
  drawTrace();
}
function drawTrace() {
  const d = fit(tr), w = tr.width, h = tr.height, pad = 8 * d, sp = sim.speed.map(v => v * 3.6), n = sp.length;
  tx.clearRect(0, 0, w, h);
  tx.fillStyle = T.muted; tx.font = `${10 * d}px Inter`;
  for (const k of [100, 200, 300]) { const y = h - pad - k / 360 * (h - 2 * pad);
    tx.strokeStyle = T.border; tx.lineWidth = 1; tx.beginPath(); tx.moveTo(30 * d, y); tx.lineTo(w - pad, y); tx.stroke(); tx.fillText(k, 4 * d, y + 3 * d); }
  tx.lineWidth = 2 * d;
  for (let i = 0; i < n - 1; i++) {
    const x0 = 30 * d + i / n * (w - 30 * d - pad), x1 = 30 * d + (i + 1) / n * (w - 30 * d - pad);
    tx.strokeStyle = MODE[sim.mode[i]]; tx.beginPath();
    tx.moveTo(x0, h - pad - sp[i] / 360 * (h - 2 * pad)); tx.lineTo(x1, h - pad - sp[i + 1] / 360 * (h - 2 * pad)); tx.stroke();
  }
  tx.fillStyle = T.muted; tx.fillText("speed round the lap (km/h)", w - 170 * d, 14 * d);
}

// ---------- editing ----------
let drag = -1, lastTap = { t: 0, i: -1 };
function nearestPoint(wx, wy) { let best = -1, bd = 1e9;
  ctrl.forEach((p, i) => { const dd = Math.hypot(p[0] - wx, p[1] - wy); if (dd < bd) { bd = dd; best = i; } });
  return [best, bd]; }
map.addEventListener("pointerdown", e => {
  const r = map.getBoundingClientRect(), d = devicePixelRatio || 1;
  const [wx, wy] = toWorld((e.clientX - r.left) * d, (e.clientY - r.top) * d);
  const [i, dist] = nearestPoint(wx, wy), grab = 22 * d / view.s;
  if (dist < grab) {
    const now = performance.now();
    if (lastTap.i === i && now - lastTap.t < 350 && ctrl.length > 4) { ctrl.splice(i, 1); rebuild(); lastTap = { t: 0, i: -1 }; return; }
    lastTap = { t: now, i }; drag = i; try { map.setPointerCapture(e.pointerId); } catch (err) {} draw(); return;
  }
  // tap near the track: add a point in the spline segment that was tapped
  const raw = spline(ctrl); let bi = 0, bd = 1e9;
  raw.forEach((p, k) => { const dd = Math.hypot(p[0] - wx, p[1] - wy); if (dd < bd) { bd = dd; bi = k; } });
  if (bd < 90) {
    const seg = Math.floor(bi / 40);              // spline() makes 40 points per segment
    ctrl.splice(seg + 1, 0, [wx, wy]); drag = seg + 1; try { map.setPointerCapture(e.pointerId); } catch (err) {} rebuild();
  }
});
map.addEventListener("pointermove", e => {
  if (drag < 0) return;
  const r = map.getBoundingClientRect(), d = devicePixelRatio || 1;
  let [wx, wy] = toWorld((e.clientX - r.left) * d, (e.clientY - r.top) * d);
  ctrl[drag] = [Math.min(Math.max(wx, 20), WORLD.w - 20), Math.min(Math.max(wy, 20), WORLD.h - 20)];
  rebuild();
});
for (const ev of ["pointerup", "pointercancel"]) map.addEventListener(ev, () => { drag = -1; draw(); });
document.querySelectorAll("[data-preset]").forEach(b => b.onclick = () => { ctrl = preset(b.dataset.preset); rebuild(); });
const wingEl = document.getElementById("wing"), wingV = document.getElementById("wingv");
wingEl.value = wing; wingV.textContent = wing.toFixed(2);
wingEl.oninput = () => { wing = parseFloat(wingEl.value); wingV.textContent = wing.toFixed(2); rebuild(); };
new ResizeObserver(() => { if (track) draw(); }).observe(document.getElementById("stage"));
ctrl = preset("flowing");
rebuild();
</script></body></html>
"""
