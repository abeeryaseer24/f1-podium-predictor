"""The 3D circuit viewer: a small Three.js web page embedded in Streamlit.

circuit_view(track, colour_by, dark, labels) draws one circuit:
  track   = the fastest lap's points (x, y, z, speed, n_gear) from track.parquet
  labels  = text pinned to the track, e.g. [{"text": "START / FINISH", "i": 0, "kind": "start"}]
            (i = which point of the track the label sits on)
"""
import json

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
  el.className = "label" + (l.kind === "start" ? " start" : "");
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