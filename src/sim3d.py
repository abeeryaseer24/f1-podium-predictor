"""The shared 3D kit for the simulator and Academy pages.

Every new 3D page uses this file, so they all look and behave the same: the same theme
colours as style.py, the same Three.js version as track3d.py, the same buttons and the
same camera.

lap_view(track, cars, ...) draws a circuit and races cars round it:
  track  = {"x", "y", "z"} in metres, evenly spaced points round the lap (a closed loop),
           plus "colours" (one CSS colour per point) and a "legend" [(label, colour), ...]
  cars   = [{"name", "colour", "t": [...seconds], "s": [...metres along the track]}]
           each car moves by looking up how far round the lap it is at each moment
  labels = [{"text", "i", "kind"}] pinned to track points (i = index into the track arrays)
"""
import json

import numpy as np
import streamlit.components.v1 as components

THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.160.0"


def lap_view(track, cars, labels=None, dark=True, height=560, lift=4, note=""):
    """A 3D lap with cars, play controls, a follow camera and a live timing box."""
    data = {
        "dark": dark,
        "x": np.round(track["x"], 1).tolist(),
        "y": np.round(track["y"], 1).tolist(),
        "z": np.round(track["z"], 1).tolist(),
        "colours": list(track["colours"]),
        "legend": [list(item) for item in track.get("legend", [])],
        "length": float(track["length"]),
        "cars": [{"name": c["name"], "colour": c["colour"],
                  "t": np.round(c["t"], 3).tolist(), "s": np.round(c["s"], 1).tolist()}
                 for c in cars],
        "labels": labels or [],
        "lift": lift,
        "note": note,
    }
    page = LAP_TEMPLATE.replace("__DATA__", json.dumps(data)).replace("__THREE__", THREE_URL)
    components.html(page, height=height)


def thin(values, every):
    """Every n-th value of an array (keeps payloads small)."""
    return np.asarray(values)[::every]


# The theme below must stay in step with THEMES in style.py.
LAP_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; font-family: Inter, system-ui, sans-serif; }
  #app { display: flex; flex-direction: column; gap: 10px; height: 100%; }
  #stage { position: relative; flex: 1; min-height: 300px; border-radius: 16px; overflow: hidden;
           border: 1px solid var(--border); }
  #stage canvas { display: block; }
  .label { position: absolute; transform: translate(-50%, -150%); padding: 3px 8px; border-radius: 999px;
           font-size: 11px; font-weight: 700; white-space: nowrap; pointer-events: none;
           background: var(--panel); color: var(--text); border: 1px solid var(--border); }
  .label.start { background: #e10600; color: #fff; border-color: #e10600; }
  .label.corner { font-size: 10px; padding: 2px 6px; font-weight: 600; }
  .carlabel { position: absolute; transform: translate(-50%, -190%); padding: 2px 7px; border-radius: 6px;
              font: 800 11px 'Saira Condensed', Inter, sans-serif; letter-spacing: .5px; color: #fff;
              pointer-events: none; white-space: nowrap; }
  #hud { position: absolute; left: 12px; top: 12px; padding: 10px 12px; border-radius: 12px; min-width: 190px;
         background: var(--panel); border: 1px solid var(--border); color: var(--text); font-size: 12px; }
  #clock { font: 800 24px 'Saira Condensed', Inter, sans-serif; letter-spacing: .5px; }
  #rows div { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
  #rows i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
  #rows b { flex: 1; }
  #rows span { font-variant-numeric: tabular-nums; color: var(--muted); }
  #views { position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; }
  #legend { position: absolute; left: 12px; bottom: 12px; padding: 8px 10px; border-radius: 12px; font-size: 11px;
            background: var(--panel); border: 1px solid var(--border); color: var(--text);
            display: flex; gap: 10px; flex-wrap: wrap; max-width: 75%; }
  #legend span { display: flex; align-items: center; gap: 5px; font-weight: 600; }
  #legend i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  #note { position: absolute; right: 12px; bottom: 12px; font-size: 11px; color: var(--muted); max-width: 40%;
          text-align: right; pointer-events: none; }
  button, select { font: 600 12px Inter, system-ui, sans-serif; padding: 9px 14px; border-radius: 999px; cursor: pointer;
                   border: 1px solid var(--border); background: var(--panel); color: var(--text); }
  button:hover { border-color: #e10600; color: #e10600; }
  button.on, #play { background: #e10600; border-color: #e10600; color: #fff; }
  #controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  #scrub { flex: 1; min-width: 160px; accent-color: #e10600; }
  @media (max-width: 560px) { #note { display: none; } #legend { max-width: 92%; } #hud { min-width: 150px; } }
</style>
<script type="importmap">
  { "imports": { "three": "__THREE__/build/three.module.js",
                 "three/addons/": "__THREE__/examples/jsm/" } }
</script>
</head>
<body>
<div id="app">
  <div id="stage">
    <div id="hud"><div id="clock">0:00.000</div><div id="rows"></div></div>
    <div id="views"><button id="overview" class="on">Overview</button><button id="follow">Follow</button></div>
    <div id="legend"></div>
    <div id="note"></div>
  </div>
  <div id="controls">
    <button id="play">Play</button>
    <select id="speed" aria-label="Playback speed">
      <option value="0.25">0.25×</option><option value="0.5">0.5×</option>
      <option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option>
    </select>
    <input id="scrub" type="range" min="0" max="1000" value="0" aria-label="Position in the lap">
  </div>
</div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const D = __DATA__;

// ---------- theme (same values as style.py) ----------
const T = D.dark
  ? { bg: "#0b0b10", panel: "rgba(21,21,30,.88)", border: "#2c2c3a", text: "#f5f5f7", muted: "#a3a3b2",
      ground: "#111118", grid: "#23232f", curtain: "#ffffff" }
  : { bg: "#f6f6f3", panel: "rgba(255,255,255,.92)", border: "#d9d9d4", text: "#15151e", muted: "#55556a",
      ground: "#ececea", grid: "#d6d6cf", curtain: "#15151e" };
const root = document.getElementById("app");
for (const [k, v] of Object.entries({ "--panel": T.panel, "--border": T.border, "--text": T.text, "--muted": T.muted }))
  root.style.setProperty(k, v);
document.body.style.background = "transparent";
const stage = document.getElementById("stage");

// ---------- track points, centred and scaled to about 100 units ----------
const n = D.x.length;
const cx = D.x.reduce((a, b) => a + b, 0) / n, cy = D.y.reduce((a, b) => a + b, 0) / n;
const zMin = Math.min(...D.z);
let extent = 1;
for (let i = 0; i < n; i++) extent = Math.max(extent, Math.abs(D.x[i] - cx), Math.abs(D.y[i] - cy));
const S = 50 / extent;
const pts = [];
for (let i = 0; i < n; i++) pts.push(new THREE.Vector3((D.x[i] - cx) * S, (D.z[i] - zMin) * S * D.lift + 0.5, -(D.y[i] - cy) * S));

// ---------- scene ----------
let renderer;
try { renderer = new THREE.WebGLRenderer({ antialias: true }); }
catch (e) { stage.innerHTML = "<p style='padding:24px;color:" + T.text + "'>3D isn't available in this browser.</p>"; throw e; }
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
stage.insertBefore(renderer.domElement, stage.firstChild);
const scene = new THREE.Scene();
scene.background = new THREE.Color(T.bg);
scene.fog = new THREE.Fog(T.bg, 200, 600);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshBasicMaterial({ color: T.ground }));
ground.rotation.x = -Math.PI / 2;
scene.add(ground);
const gridHelper = new THREE.GridHelper(160, 32, T.grid, T.grid);
gridHelper.position.y = 0.01;
scene.add(gridHelper);

// ---------- the track ribbon, coloured point by point ----------
const W = 1.3, up = new THREE.Vector3(0, 1, 0);
const pos = [], col = [], idx = [], cPos = [], left = [], right = [];
for (let i = 0; i <= n; i++) {
  const p = pts[i % n], a = pts[(i + n - 1) % n], b = pts[(i + 1) % n];
  const tangent = b.clone().sub(a).normalize();
  const side = new THREE.Vector3().crossVectors(tangent, up).normalize().multiplyScalar(W);
  pos.push(p.x + side.x, p.y, p.z + side.z, p.x - side.x, p.y, p.z - side.z);
  left.push(new THREE.Vector3(p.x + side.x, p.y + 0.02, p.z + side.z));
  right.push(new THREE.Vector3(p.x - side.x, p.y + 0.02, p.z - side.z));
  const c = new THREE.Color(D.colours[i % n]);
  col.push(c.r, c.g, c.b, c.r, c.g, c.b);
  cPos.push(p.x, p.y - 0.05, p.z, p.x, 0, p.z);
  if (i < n) { const k = 2 * i; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
}
const ribbon = new THREE.BufferGeometry();
ribbon.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
ribbon.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
ribbon.setIndex(idx);
scene.add(new THREE.Mesh(ribbon, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide })));
const edgeMat = new THREE.LineBasicMaterial({ color: T.text, transparent: true, opacity: 0.35 });
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(left), edgeMat));
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(right), edgeMat));
const curtain = new THREE.BufferGeometry();
curtain.setAttribute("position", new THREE.Float32BufferAttribute(cPos, 3));
curtain.setIndex(idx);
scene.add(new THREE.Mesh(curtain, new THREE.MeshBasicMaterial({
  color: T.curtain, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false })));
const startLine = new THREE.Mesh(new THREE.BoxGeometry(W * 2.3, 0.25, 0.6), new THREE.MeshBasicMaterial({ color: "#ffffff" }));
startLine.position.copy(pts[0]);
startLine.lookAt(pts[1]);
scene.add(startLine);

// ---------- legend and note ----------
document.getElementById("legend").innerHTML =
  D.legend.map(([t, c]) => `<span><i style="background:${c}"></i>${t}</span>`).join("");
if (!D.legend.length) document.getElementById("legend").style.display = "none";
document.getElementById("note").textContent = D.note || "";

// ---------- labels ----------
const labels = D.labels.map(l => {
  const el = document.createElement("div");
  el.className = "label" + (l.kind ? " " + l.kind : "");
  el.textContent = l.text;
  stage.appendChild(el);
  return { el, pos: pts[Math.min(l.i, n - 1)].clone().add(new THREE.Vector3(0, 1.5, 0)) };
});

// ---------- cars ----------
const step = D.length / n;
function pointAt(s) {           // a position on the track, s metres from the line
  s = ((s % D.length) + D.length) % D.length;
  const f = s / step, i = Math.floor(f) % n, k = f - Math.floor(f);
  return pts[i].clone().lerp(pts[(i + 1) % n], k);
}
function sAt(car, t) {          // how far round the car is at time t (binary search)
  const T_ = car.t, S_ = car.s;
  if (t <= T_[0]) return S_[0];
  if (t >= T_[T_.length - 1]) return S_[S_.length - 1];
  let lo = 0, hi = T_.length - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (T_[mid] <= t) lo = mid; else hi = mid; }
  const k = (t - T_[lo]) / (T_[hi] - T_[lo]);
  return S_[lo] + (S_[hi] - S_[lo]) * k;
}
function speedAt(car, t) {      // km/h, from the slope of distance over time
  const t0 = Math.max(car.t[0], t - 0.1), t1 = Math.min(car.t[car.t.length - 1], t + 0.1);
  return t1 > t0 ? Math.max(0, (sAt(car, t1) - sAt(car, t0)) / (t1 - t0) * 3.6) : 0;
}
const cars = D.cars.map(c => {
  const group = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.6, 0.8), new THREE.MeshBasicMaterial({ color: c.colour }));
  body.position.y = 0.35;
  group.add(body);
  const halo = new THREE.Mesh(new THREE.RingGeometry(1.1, 1.5, 24), new THREE.MeshBasicMaterial({
    color: c.colour, transparent: true, opacity: .45, side: THREE.DoubleSide }));
  halo.rotation.x = -Math.PI / 2; halo.position.y = 0.05;
  group.add(halo);
  scene.add(group);
  const tag = document.createElement("div");
  tag.className = "carlabel"; tag.textContent = c.name; tag.style.background = c.colour;
  const rgb = new THREE.Color(c.colour);          // dark text on light car colours
  tag.style.color = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) > 0.6 ? "#15151e" : "#fff";
  stage.appendChild(tag);
  return { ...c, group, tag, end: c.t[c.t.length - 1] };
});
const lapEnd = Math.max(...cars.map(c => c.end), 1);
document.getElementById("rows").innerHTML = cars.map((c, i) =>
  `<div><i style="background:${c.colour}"></i><b>${c.name}</b><span id="v${i}">0 km/h</span></div>`).join("");

// ---------- camera ----------
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 8;
controls.maxDistance = 420;
controls.maxPolarAngle = Math.PI * 0.48;
let follow = false;
function overview() {          // pull back on narrow screens so the whole circuit fits
  const f = Math.max(1, 1.2 / Math.max(camera.aspect, 0.3));
  camera.position.set(0, 70 * f, 95 * f); controls.target.set(0, 0, 0); controls.update();
}
const btnO = document.getElementById("overview"), btnF = document.getElementById("follow");
btnO.onclick = () => { follow = false; btnO.classList.add("on"); btnF.classList.remove("on"); overview(); };
btnF.onclick = () => { follow = true; btnF.classList.add("on"); btnO.classList.remove("on"); };

// ---------- playback ----------
let clock = 0, playing = false, last = null;
const playBtn = document.getElementById("play"), scrub = document.getElementById("scrub"), speedSel = document.getElementById("speed");
playBtn.onclick = () => {
  if (!playing && clock >= lapEnd) clock = 0;
  playing = !playing; playBtn.textContent = playing ? "Pause" : "Play"; last = null;
};
scrub.oninput = () => { clock = scrub.value / 1000 * lapEnd; };
function fmt(t) { const m = Math.floor(t / 60), s = t - 60 * m; return m + ":" + s.toFixed(3).padStart(6, "0"); }

function place(el, v3) {
  const v = v3.clone().project(camera), w = stage.clientWidth, h = stage.clientHeight;
  el.style.display = v.z > 1 ? "none" : "block";
  el.style.left = ((v.x * 0.5 + 0.5) * w) + "px";
  el.style.top = ((-v.y * 0.5 + 0.5) * h) + "px";
}

let moved = false;               // once the visitor moves the camera, resizing leaves it alone
controls.addEventListener("start", () => { moved = true; });
function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
  if (!moved && !follow) overview();
}
new ResizeObserver(resize).observe(stage);
resize();

(function frame(now) {
  if (playing && last !== null) {
    clock += (now - last) / 1000 * parseFloat(speedSel.value);
    if (clock >= lapEnd) { clock = lapEnd; playing = false; playBtn.textContent = "Play again"; }
  }
  last = now;
  if (playing) scrub.value = Math.round(clock / lapEnd * 1000);
  document.getElementById("clock").textContent = fmt(clock);
  cars.forEach((c, i) => {
    const t = Math.min(clock, c.end), s = sAt(c, t);
    const p = pointAt(s), ahead = pointAt(s + step * 2);
    c.group.position.copy(p);
    c.group.lookAt(ahead.x, p.y, ahead.z);
    c.group.rotateY(Math.PI / 2);
    place(c.tag, p.clone().add(new THREE.Vector3(0, 0.8, 0)));
    const done = clock >= c.end;
    document.getElementById("v" + i).textContent = done ? "Lap " + fmt(c.end) : Math.round(speedAt(c, t)) + " km/h";
  });
  if (follow && cars.length) {
    const c = cars[0], s = sAt(c, Math.min(clock, c.end));
    const p = pointAt(s), behind = pointAt(s - step * 12);
    const want = behind.clone().add(new THREE.Vector3(0, 6, 0));
    camera.position.lerp(want, 0.12);
    controls.target.lerp(p, 0.2);
  }
  controls.update();
  renderer.render(scene, camera);
  labels.forEach(L => place(L.el, L.pos));
  requestAnimationFrame(frame);
})(performance.now());
</script>
</body></html>
"""
