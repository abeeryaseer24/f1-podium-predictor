"""The 3D circuit viewer: a small Three.js web page embedded in Streamlit.

circuit_view(track, colour_by, dark, labels) draws one circuit:
  track   = the fastest lap's points (x, y, z, speed, n_gear) from track.parquet
  labels  = text pinned to the track, e.g. [{"text": "START / FINISH", "i": 0, "kind": "start"}]
            (i = which point of the track the label sits on)
"""
import json

import numpy as np

import streamlit.components.v1 as components

THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.160.0"


def circuit_view(track, colour_by="speed", dark=True, labels=None, height=540):
    column = "speed" if colour_by == "speed" else "n_gear"
    data = {
        "points": track[["x", "y", "z"]].round(1).values.tolist(),
        "values": track[column].fillna(0).round(1).tolist(),
        "mode": colour_by,
        "dark": dark,
        "labels": labels or [{"text": "START / FINISH", "i": 0, "kind": "start"}],
    }
    page = TEMPLATE.replace("__DATA__", json.dumps(data)).replace("__THREE__", THREE_URL)
    components.html(page, height=height)


TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; font-family: Inter, system-ui, sans-serif; }
  #wrap { position: relative; width: 100%; height: 100%; border-radius: 16px; overflow: hidden; }
  canvas { display: block; }
  .label { position: absolute; transform: translate(-50%, -140%); padding: 3px 8px; border-radius: 999px;
           font-size: 11px; font-weight: 700; letter-spacing: .4px; white-space: nowrap; pointer-events: none;
           background: var(--panel); color: var(--text); border: 1px solid var(--border); }
  .label.start { background: #e10600; color: #fff; border-color: #e10600; }
  .label.corner { font-size: 10px; padding: 2px 6px; font-weight: 600; }
  #ui { position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; }
  #ui button { font: 600 12px Inter, system-ui, sans-serif; padding: 9px 14px; border-radius: 999px; cursor: pointer;
               border: 1px solid var(--border); background: var(--panel); color: var(--text); }
  #ui button:hover { border-color: #e10600; color: #e10600; }
  #legend { position: absolute; left: 12px; bottom: 12px; padding: 10px 12px; border-radius: 12px; font-size: 11px;
            background: var(--panel); border: 1px solid var(--border); color: var(--text); }
  #legend .bar { width: 180px; height: 10px; border-radius: 5px; margin: 6px 0 4px; }
  #legend .ends { display: flex; justify-content: space-between; color: var(--muted); }
  #legend .gears { display: flex; gap: 4px; margin-top: 6px; }
  #legend .gears span { width: 20px; height: 20px; border-radius: 5px; display: flex; align-items: center;
                        justify-content: center; font-weight: 700; color: #111; }
  #hint { position: absolute; left: 50%; bottom: 14px; transform: translateX(-50%); font-size: 11px;
          color: var(--muted); pointer-events: none; }
</style>
<script type="importmap">
  { "imports": { "three": "__THREE__/build/three.module.js",
                 "three/addons/": "__THREE__/examples/jsm/" } }
</script>
</head>
<body>
<div id="wrap">
  <div id="ui"><button id="spin">Pause spin</button><button id="reset">Reset view</button></div>
  <div id="legend"></div>
  <div id="hint">Drag to rotate · scroll or pinch to zoom</div>
</div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const D = __DATA__;

// ---------- theme ----------
const T = D.dark
  ? { bg: "#0b0b10", panel: "rgba(21,21,30,.88)", border: "#2c2c3a", text: "#f5f5f7", muted: "#a3a3b2",
      ground: "#111118", grid: "#23232f", curtain: "#ffffff" }
  : { bg: "#f6f6f3", panel: "rgba(255,255,255,.92)", border: "#d9d9d4", text: "#15151e", muted: "#55556a",
      ground: "#ececea", grid: "#d6d6cf", curtain: "#15151e" };
const wrap = document.getElementById("wrap");
for (const [k, v] of Object.entries({ "--panel": T.panel, "--border": T.border, "--text": T.text, "--muted": T.muted }))
  wrap.style.setProperty(k, v);
document.body.style.background = T.bg;

// ---------- colours: slow/low = blue -> teal -> yellow -> red = fast/high ----------
const RAMP = ["#2b6cff", "#19c3a6", "#ffd23f", "#ff3b2f"];
const ramp = RAMP.map(c => new THREE.Color(c));
function rampColour(f) {
  f = Math.min(1, Math.max(0, f));
  const s = f * (ramp.length - 1), i = Math.min(ramp.length - 2, Math.floor(s));
  return ramp[i].clone().lerp(ramp[i + 1], s - i);
}

// ---------- the track points, centred and scaled to fit ----------
const P = D.points, V = D.values, n = P.length;
const cx = P.reduce((a, p) => a + p[0], 0) / n, cy = P.reduce((a, p) => a + p[1], 0) / n;
const zMin = Math.min(...P.map(p => p[2]));
const extent = Math.max(...P.map(p => Math.max(Math.abs(p[0] - cx), Math.abs(p[1] - cy))));
const S = 50 / extent;        // the whole circuit fits in about 100 units
const LIFT = 4;               // hills shown 4x higher so they are visible
const pts = P.map(p => new THREE.Vector3((p[0] - cx) * S, (p[2] - zMin) * S * LIFT + 0.5, -(p[1] - cy) * S));

// Smooth curve through the points, sampled K times between each pair
const curve = new THREE.CatmullRomCurve3(pts, true, "centripetal");
const K = 8, N = n * K;
const samples = curve.getPoints(N);

const isGear = D.mode === "gear";
const vMin = isGear ? 1 : Math.min(...V), vMax = isGear ? 8 : Math.max(...V);
function valueAt(j) {
  const i = Math.floor(j / K) % n, f = (j % K) / K, a = V[i], b = V[(i + 1) % n];
  return isGear ? (f < 0.5 ? a : b) : a + (b - a) * f;
}
function colourAt(j) { return rampColour((valueAt(j) - vMin) / ((vMax - vMin) || 1)); }

// ---------- scene ----------
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true });
} catch (e) {
  wrap.innerHTML = "<p style='padding:24px;color:" + T.text + "'>3D isn't available in this browser.</p>";
  throw e;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
wrap.insertBefore(renderer.domElement, wrap.firstChild);

const scene = new THREE.Scene();
scene.background = new THREE.Color(T.bg);
scene.fog = new THREE.Fog(T.bg, 150, 280);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);

// Ground and grid
const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshBasicMaterial({ color: T.ground }));
ground.rotation.x = -Math.PI / 2;
scene.add(ground);
const grid = new THREE.GridHelper(160, 32, T.grid, T.grid);
grid.position.y = 0.01;
scene.add(grid);

// The track ribbon (coloured), its edges and the elevation curtain
const W = 1.4, up = new THREE.Vector3(0, 1, 0);
const pos = [], col = [], idx = [], leftEdge = [], rightEdge = [], cPos = [];
for (let j = 0; j < samples.length; j++) {
  const p = samples[j];
  const side = new THREE.Vector3().crossVectors(curve.getTangent(j / N), up).normalize().multiplyScalar(W);
  pos.push(p.x + side.x, p.y, p.z + side.z, p.x - side.x, p.y, p.z - side.z);
  leftEdge.push(new THREE.Vector3(p.x + side.x, p.y + 0.02, p.z + side.z));
  rightEdge.push(new THREE.Vector3(p.x - side.x, p.y + 0.02, p.z - side.z));
  const c = colourAt(j);
  col.push(c.r, c.g, c.b, c.r, c.g, c.b);
  cPos.push(p.x, p.y - 0.05, p.z, p.x, 0, p.z);
  if (j < samples.length - 1) { const a = 2 * j; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
}
const ribbon = new THREE.BufferGeometry();
ribbon.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
ribbon.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
ribbon.setIndex(idx);
scene.add(new THREE.Mesh(ribbon, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide })));

const edgeMat = new THREE.LineBasicMaterial({ color: T.text, transparent: true, opacity: 0.35 });
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(leftEdge), edgeMat));
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(rightEdge), edgeMat));

const curtain = new THREE.BufferGeometry();
curtain.setAttribute("position", new THREE.Float32BufferAttribute(cPos, 3));
curtain.setIndex(idx);
scene.add(new THREE.Mesh(curtain, new THREE.MeshBasicMaterial({
  color: T.curtain, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false })));

// Start / finish line
const line = new THREE.Mesh(new THREE.BoxGeometry(W * 2.3, 0.25, 0.6), new THREE.MeshBasicMaterial({ color: "#ffffff" }));
line.position.copy(samples[0]);
line.lookAt(samples[0].clone().add(curve.getTangent(0)));
scene.add(line);

// ---------- labels pinned to the track ----------
const labels = (D.labels || []).map(l => {
  const el = document.createElement("div");
    el.className = "label" + (l.kind ? " " + l.kind : "");
  el.textContent = l.text;
  wrap.appendChild(el);
  return { el, pos: pts[Math.min(l.i, n - 1)].clone().add(new THREE.Vector3(0, 1.5, 0)) };
});
function placeLabels() {
  const w = wrap.clientWidth, h = wrap.clientHeight;
  for (const L of labels) {
    const v = L.pos.clone().project(camera);
    L.el.style.display = v.z > 1 ? "none" : "block";
    L.el.style.left = ((v.x * 0.5 + 0.5) * w) + "px";
    L.el.style.top = ((-v.y * 0.5 + 0.5) * h) + "px";
  }
}

// ---------- legend ----------
const legend = document.getElementById("legend");
if (isGear) {
  legend.innerHTML = "<b>Gear</b><div class='gears'>" +
    [1, 2, 3, 4, 5, 6, 7, 8].map(g => `<span style='background:${rampColour((g - 1) / 7).getStyle()}'>${g}</span>`).join("") + "</div>";
} else {
  legend.innerHTML = `<b>Speed (km/h)</b><div class='bar' style='background:linear-gradient(90deg,${RAMP.join(",")})'></div>` +
    `<div class='ends'><span>${Math.round(vMin)}</span><span>${Math.round(vMax)}</span></div>`;
}

// ---------- camera controls ----------
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 25;
controls.maxDistance = 220;
controls.maxPolarAngle = Math.PI * 0.48;      // never go under the ground
controls.autoRotate = true;
controls.autoRotateSpeed = 0.6;

function resetView() { camera.position.set(0, 70, 95); controls.target.set(0, 0, 0); controls.update(); }
resetView();

const spinBtn = document.getElementById("spin");
function setSpin(on) { controls.autoRotate = on; spinBtn.textContent = on ? "Pause spin" : "Spin"; }
spinBtn.onclick = () => setSpin(!controls.autoRotate);
document.getElementById("reset").onclick = resetView;
controls.addEventListener("start", () => { setSpin(false); document.getElementById("hint").style.display = "none"; });

function resize() {
  const w = wrap.clientWidth, h = wrap.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(wrap);
resize();

(function frame() {
  controls.update();
  renderer.render(scene, camera);
  placeLabels();
  requestAnimationFrame(frame);
})();
</script>
</body></html>
"""

# ======================= Ghost Lap Duel =======================

def duel_view(track, duel, driver_a, driver_b, dark=True, height=780):
    """Two laps racing on the 3D track, with synced speed/throttle/brake charts below."""
    colour_a = driver_a.get("colour") or "#e10600"
    colour_b = driver_b.get("colour") or "#2b6cff"
    if colour_b.lower() == colour_a.lower():                  # teammates: make B stand out
        colour_b = "#ffffff" if dark else "#15151e"

    # Colour every track point by who is faster in that mini-sector
    step = (track[["x", "y"]].diff().pow(2).sum(axis=1) ** 0.5).fillna(0)
    frac = (step.cumsum() / step.sum()).to_numpy()
    segments = duel["segments"]
    k = np.minimum((frac * len(segments)).astype(int), len(segments) - 1)
    winners = segments["winner"].to_numpy()[k]
    colours = [colour_a if w == "a" else colour_b for w in winners]

    def pack(trace, driver, colour, lap):
        cols = ["t", "frac", "x", "y", "z", "speed", "throttle", "brake"]
        data = {c: trace[c].fillna(0).round(4).tolist() for c in cols}
        data.update({"code": driver.get("code") or "?", "colour": colour, "lap": lap})
        return data

    data = {
        "dark": dark,
        "points": track[["x", "y", "z"]].round(1).values.tolist(),
        "colours": colours,
        "a": pack(duel["trace_a"], driver_a, colour_a, duel["lap_a"]),
        "b": pack(duel["trace_b"], driver_b, colour_b, duel["lap_b"]),
        "grid": np.round(duel["grid"], 4).tolist(),
        "delta": np.round(duel["delta"], 4).tolist(),
        "corners": [{"label": label, "frac": round(f, 4)} for label, f in duel["corners"]],
    }
    page = DUEL_TEMPLATE.replace("__DATA__", json.dumps(data)).replace("__THREE__", THREE_URL)
    components.html(page, height=height)


DUEL_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body { margin: 0; overflow: hidden; font-family: Inter, system-ui, sans-serif; }
  #app { display: flex; flex-direction: column; gap: 10px; }
  #stage { position: relative; height: 440px; border-radius: 16px; overflow: hidden; }
  #stage canvas { display: block; }
  .label { position: absolute; transform: translate(-50%, -150%); padding: 3px 8px; border-radius: 999px;
           font-size: 11px; font-weight: 700; white-space: nowrap; pointer-events: none;
           background: var(--panel); color: var(--text); border: 1px solid var(--border); }
  .label.start { background: #e10600; color: #fff; border-color: #e10600; }
  #hud { position: absolute; left: 12px; top: 12px; padding: 10px 12px; border-radius: 12px; min-width: 170px;
         background: var(--panel); border: 1px solid var(--border); color: var(--text); font-size: 12px; }
  #clock { font: 800 24px 'Saira Condensed', Inter, sans-serif; }
  #gap { margin-top: 2px; font-weight: 600; }
  #views { position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; }
  #key { position: absolute; left: 12px; bottom: 12px; padding: 10px 12px; border-radius: 12px; font-size: 11px;
         background: var(--panel); border: 1px solid var(--border); color: var(--text); }
  #key .chips { display: flex; gap: 10px; margin-top: 6px; }
  #key .chips span { display: flex; align-items: center; gap: 6px; font-weight: 700; }
  #key .chips i { width: 14px; height: 14px; border-radius: 4px; display: inline-block; border: 1px solid var(--border); }
  button, select { font: 600 12px Inter, system-ui, sans-serif; padding: 9px 14px; border-radius: 999px; cursor: pointer;
                   border: 1px solid var(--border); background: var(--panel); color: var(--text); }
  button.on, #play { background: #e10600; border-color: #e10600; color: #fff; }
  #controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  #scrub { flex: 1; min-width: 160px; accent-color: #e10600; }
  #charts { width: 100%; height: 240px; border-radius: 12px; background: var(--panel2); cursor: pointer; display: block; }
</style>
<script type="importmap">
  { "imports": { "three": "__THREE__/build/three.module.js",
                 "three/addons/": "__THREE__/examples/jsm/" } }
</script>
</head>
<body>
<div id="app">
  <div id="stage">
    <div id="hud"><div id="clock">0:00.000</div><div id="gap">Press Play</div></div>
    <div id="views"><button id="overview" class="on">Overview</button><button id="follow">Follow</button></div>
    <div id="key"></div>
  </div>
  <div id="controls">
    <button id="play">Play</button>
    <select id="speed" aria-label="Playback speed">
      <option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option>
    </select>
    <input id="scrub" type="range" min="0" max="1000" value="0" aria-label="Position in the lap">
  </div>
  <canvas id="charts" aria-label="Speed, throttle and brake for both drivers"></canvas>
</div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const D = __DATA__;

// ---------- theme ----------
const T = D.dark
  ? { bg: "#0b0b10", panel: "rgba(21,21,30,.88)", panel2: "#15151e", border: "#2c2c3a", text: "#f5f5f7",
      muted: "#a3a3b2", ground: "#111118", grid: "#23232f", curtain: "#ffffff" }
  : { bg: "#f6f6f3", panel: "rgba(255,255,255,.92)", panel2: "#ffffff", border: "#d9d9d4", text: "#15151e",
      muted: "#55556a", ground: "#ececea", grid: "#d6d6cf", curtain: "#15151e" };
const app = document.getElementById("app"), stage = document.getElementById("stage");
for (const [k, v] of Object.entries({ "--panel": T.panel, "--panel2": T.panel2, "--border": T.border,
                                      "--text": T.text, "--muted": T.muted }))
  app.style.setProperty(k, v);
document.body.style.background = T.bg;

// ---------- track, centred and scaled (same as the Circuit Explorer) ----------
const P = D.points, n = P.length;
const cx = P.reduce((a, p) => a + p[0], 0) / n, cy = P.reduce((a, p) => a + p[1], 0) / n;
const zMin = Math.min(...P.map(p => p[2]));
const extent = Math.max(...P.map(p => Math.max(Math.abs(p[0] - cx), Math.abs(p[1] - cy))));
const S = 50 / extent, LIFT = 4;
const toScene = (x, y, z) => new THREE.Vector3((x - cx) * S, (z - zMin) * S * LIFT + 0.5, -(y - cy) * S);
const pts = P.map(p => toScene(p[0], p[1], p[2]));
const curve = new THREE.CatmullRomCurve3(pts, true, "centripetal");
const K = 8, N = n * K, samples = curve.getPoints(N);
const colourAt = j => new THREE.Color(D.colours[Math.floor(j / K) % n]);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
stage.insertBefore(renderer.domElement, stage.firstChild);
const scene = new THREE.Scene();
scene.background = new THREE.Color(T.bg);
scene.fog = new THREE.Fog(T.bg, 150, 280);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);

const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshBasicMaterial({ color: T.ground }));
ground.rotation.x = -Math.PI / 2;
scene.add(ground);
const grid = new THREE.GridHelper(160, 32, T.grid, T.grid);
grid.position.y = 0.01;
scene.add(grid);

const W = 1.4, up = new THREE.Vector3(0, 1, 0);
const pos = [], col = [], idx = [], leftEdge = [], rightEdge = [], cPos = [];
for (let j = 0; j < samples.length; j++) {
  const p = samples[j];
  const side = new THREE.Vector3().crossVectors(curve.getTangent(j / N), up).normalize().multiplyScalar(W);
  pos.push(p.x + side.x, p.y, p.z + side.z, p.x - side.x, p.y, p.z - side.z);
  leftEdge.push(new THREE.Vector3(p.x + side.x, p.y + 0.02, p.z + side.z));
  rightEdge.push(new THREE.Vector3(p.x - side.x, p.y + 0.02, p.z - side.z));
  const c = colourAt(j);
  col.push(c.r, c.g, c.b, c.r, c.g, c.b);
  cPos.push(p.x, p.y - 0.05, p.z, p.x, 0, p.z);
  if (j < samples.length - 1) { const a = 2 * j; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
}
const ribbon = new THREE.BufferGeometry();
ribbon.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
ribbon.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
ribbon.setIndex(idx);
scene.add(new THREE.Mesh(ribbon, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide,
                                                                transparent: true, opacity: 0.85 })));
const edgeMat = new THREE.LineBasicMaterial({ color: T.text, transparent: true, opacity: 0.35 });
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(leftEdge), edgeMat));
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(rightEdge), edgeMat));
const curtain = new THREE.BufferGeometry();
curtain.setAttribute("position", new THREE.Float32BufferAttribute(cPos, 3));
curtain.setIndex(idx);
scene.add(new THREE.Mesh(curtain, new THREE.MeshBasicMaterial({
  color: T.curtain, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false })));
const line = new THREE.Mesh(new THREE.BoxGeometry(W * 2.3, 0.25, 0.6), new THREE.MeshBasicMaterial({ color: "#ffffff" }));
line.position.copy(samples[0]);
line.lookAt(samples[0].clone().add(curve.getTangent(0)));
scene.add(line);

// ---------- labels pinned in 3D ----------
function makeLabel(html, cls) {
  const el = document.createElement("div");
  el.className = "label" + (cls ? " " + cls : "");
  el.innerHTML = html;
  stage.appendChild(el);
  return el;
}
function placeLabel(el, p) {
  const v = p.clone().project(camera);
  el.style.display = v.z > 1 ? "none" : "block";
  el.style.left = ((v.x * 0.5 + 0.5) * stage.clientWidth) + "px";
  el.style.top = ((-v.y * 0.5 + 0.5) * stage.clientHeight) + "px";
}
const startLabel = makeLabel("START / FINISH", "start");
const startPos = pts[0].clone().add(new THREE.Vector3(0, 1.5, 0));

// ---------- the two cars ----------
const cars = [D.a, D.b].map(c => {
  const path = c.t.map((_, k) => toScene(c.x[k], c.y[k], c.z[k]).add(new THREE.Vector3(0, 0.7, 0)));
  const dot = new THREE.Mesh(new THREE.SphereGeometry(1.1, 24, 16), new THREE.MeshBasicMaterial({ color: c.colour }));
  dot.add(new THREE.Mesh(new THREE.SphereGeometry(2.2, 24, 16),
    new THREE.MeshBasicMaterial({ color: c.colour, transparent: true, opacity: 0.22, depthWrite: false })));
  scene.add(dot);
  const trailGeo = new THREE.BufferGeometry();
  scene.add(new THREE.Line(trailGeo, new THREE.LineBasicMaterial({ color: c.colour, transparent: true, opacity: 0.6 })));
  const el = makeLabel(`<span style="color:${c.colour}">&#9679;</span> ${c.code}`);
  return { ...c, path, dot, trailGeo, trail: [], el, f: 0 };
});
dot0: {
  // place both cars on the line before playing
}

function stateAt(c, time) {
  const t = c.t, last = t.length - 1;
  if (time <= t[0]) return { p: c.path[0], f: c.frac[0] };
  if (time >= t[last]) return { p: c.path[last], f: c.frac[last] };
  let lo = 0, hi = last;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (t[mid] <= time) lo = mid; else hi = mid; }
  const u = (time - t[lo]) / (t[hi] - t[lo]);
  return { p: c.path[lo].clone().lerp(c.path[hi], u), f: c.frac[lo] + (c.frac[hi] - c.frac[lo]) * u };
}
function interp(x, xs, ys) {
  if (x <= xs[0]) return ys[0];
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
  let lo = 0, hi = xs.length - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] <= x) lo = mid; else hi = mid; }
  return ys[lo] + (ys[hi] - ys[lo]) * (x - xs[lo]) / (xs[hi] - xs[lo]);
}

document.getElementById("key").innerHTML = "<b>Track colour</b> = faster driver in that section" +
  "<div class='chips'>" + cars.map(c => `<span><i style="background:${c.colour}"></i>${c.code}</span>`).join("") + "</div>";

// ---------- camera ----------
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 12;
controls.maxDistance = 220;
controls.maxPolarAngle = Math.PI * 0.48;
let follow = false;
const overviewBtn = document.getElementById("overview"), followBtn = document.getElementById("follow");
function resetView() { camera.position.set(0, 70, 95); controls.target.set(0, 0, 0); controls.update(); }
function leader() { return cars[0].f >= cars[1].f ? cars[0] : cars[1]; }
overviewBtn.onclick = () => { follow = false; overviewBtn.classList.add("on"); followBtn.classList.remove("on"); resetView(); };
followBtn.onclick = () => {
  follow = true; followBtn.classList.add("on"); overviewBtn.classList.remove("on");
  const p = leader().dot.position;
  controls.target.copy(p);
  camera.position.copy(p.clone().add(new THREE.Vector3(0, 22, 30)));
};
resetView();

// ---------- playback ----------
const END = Math.max(D.a.lap, D.b.lap);
const playBtn = document.getElementById("play"), speedSel = document.getElementById("speed"),
      scrub = document.getElementById("scrub"), clock = document.getElementById("clock"),
      gapText = document.getElementById("gap");
let time = 0, playing = false, lastFrame = performance.now();
const fmt = s => { const m = Math.floor(s / 60); return m + ":" + (s - m * 60).toFixed(3).padStart(6, "0"); };
function setPlaying(on) { playing = on; playBtn.textContent = on ? "Pause" : (time >= END ? "Replay" : "Play"); }
playBtn.onclick = () => { if (time >= END) { time = 0; cars.forEach(c => c.trail = []); } setPlaying(!playing); };
scrub.oninput = () => { time = scrub.value / 1000 * END; setPlaying(false); cars.forEach(c => c.trail = []); };

function updateHud() {
  clock.textContent = fmt(Math.min(time, END));
  const a = cars[0], b = cars[1];
  if (time >= END) {
    const faster = a.lap <= b.lap ? a : b;
    gapText.innerHTML = `<span style="color:${faster.colour}">&#9679;</span> ${faster.code} faster by ${Math.abs(a.lap - b.lap).toFixed(3)} s`;
    return;
  }
  if (time === 0) { gapText.textContent = "Press Play"; return; }
  const d = interp(Math.max(a.f, b.f), D.grid, D.delta);      // A's time minus B's time at this point
  const ahead = d <= 0 ? a : b;
  gapText.innerHTML = `<span style="color:${ahead.colour}">&#9679;</span> ${ahead.code} ahead by ${Math.abs(d).toFixed(3)} s`;
}

// ---------- synced charts: speed, throttle, brake ----------
const chart = document.getElementById("charts"), ctx = chart.getContext("2d");
const ROWS = [{ key: "speed", name: "Speed" }, { key: "throttle", name: "Throttle", max: 100 },
              { key: "brake", name: "Brake", max: 100 }];
const PAD_L = 70, PAD_R = 12, TOP = 20;
let base = null;
function drawBase() {
  const w = chart.clientWidth, h = chart.clientHeight, r = Math.min(window.devicePixelRatio, 2);
  chart.width = w * r; chart.height = h * r;
  base = document.createElement("canvas");
  base.width = chart.width; base.height = chart.height;
  const g = base.getContext("2d");
  g.scale(r, r);
  const plotW = w - PAD_L - PAD_R, rowH = (h - TOP - 6) / ROWS.length;
  const topSpeed = Math.max(...D.a.speed, ...D.b.speed) || 1;
  g.font = "600 10px Inter, system-ui, sans-serif";
  for (const c of D.corners) {
    const x = PAD_L + c.frac * plotW;
    g.strokeStyle = T.grid; g.lineWidth = 1;
    g.beginPath(); g.moveTo(x, TOP); g.lineTo(x, h - 6); g.stroke();
    g.fillStyle = T.muted; g.textAlign = "center"; g.fillText(c.label, x, 13);
  }
  ROWS.forEach((row, ri) => {
    const y0 = TOP + ri * rowH, max = row.max || topSpeed;
    g.textAlign = "left"; g.fillStyle = T.muted; g.fillText(row.name, 10, y0 + rowH / 2 + 4);
    g.strokeStyle = T.grid; g.beginPath(); g.moveTo(PAD_L, y0 + rowH - 4); g.lineTo(w - PAD_R, y0 + rowH - 4); g.stroke();
    for (const c of cars) {
      g.strokeStyle = c.colour; g.lineWidth = 1.5; g.beginPath();
      c.frac.forEach((f, k) => {
        const x = PAD_L + f * plotW, y = y0 + rowH - 6 - (Math.min(c[row.key][k], max) / max) * (rowH - 12);
        k ? g.lineTo(x, y) : g.moveTo(x, y);
      });
      g.stroke();
    }
  });
}
function drawCharts() {
  if (!base) return;
  const w = chart.clientWidth, h = chart.clientHeight, r = Math.min(window.devicePixelRatio, 2);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, chart.width, chart.height);
  ctx.drawImage(base, 0, 0);
  ctx.setTransform(r, 0, 0, r, 0, 0);
  const x = PAD_L + Math.max(cars[0].f, cars[1].f) * (w - PAD_L - PAD_R);
  ctx.strokeStyle = "#e10600"; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(x, TOP - 4); ctx.lineTo(x, h - 4); ctx.stroke();
}
chart.onclick = e => {           // click a chart to jump to that point of the lap
  const rect = chart.getBoundingClientRect();
  const f = Math.min(1, Math.max(0, (e.clientX - rect.left - PAD_L) / (rect.width - PAD_L - PAD_R)));
  time = interp(f, D.a.frac, D.a.t);
  setPlaying(false); cars.forEach(c => c.trail = []);
};

// ---------- sizing and the main loop ----------
function resize() {
  renderer.setSize(stage.clientWidth, stage.clientHeight);
  camera.aspect = stage.clientWidth / stage.clientHeight;
  camera.updateProjectionMatrix();
  drawBase();
}
new ResizeObserver(resize).observe(app);
resize();

(function frame() {
  const now = performance.now(), dt = (now - lastFrame) / 1000;
  lastFrame = now;
  if (playing) {
    time = Math.min(END, time + dt * parseFloat(speedSel.value));
    if (time >= END) setPlaying(false);
    scrub.value = time / END * 1000;
  }
  for (const c of cars) {
    const s = stateAt(c, Math.min(time, c.lap));
    c.dot.position.copy(s.p);
    c.f = s.f;
    c.trail.push(s.p.clone());
    if (c.trail.length > 45) c.trail.shift();
    c.trailGeo.setFromPoints(c.trail);
    placeLabel(c.el, s.p.clone().add(new THREE.Vector3(0, 2.4, 0)));
  }
  if (follow) {
    const move = leader().dot.position.clone().sub(controls.target).multiplyScalar(0.12);
    controls.target.add(move);
    camera.position.add(move);
  }
  controls.update();
  renderer.render(scene, camera);
  placeLabel(startLabel, startPos);
  updateHud();
  drawCharts();
  requestAnimationFrame(frame);
})();
</script>
</body></html>
"""
