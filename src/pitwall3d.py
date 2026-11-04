"""Pit Wall 3D: the race replay plus the strategist on screen
(team radio for the driver you follow, strategist panel, planned-stop badges and the verdict).
With `game`, it becomes Be the Race Engineer: you make the pit calls for one driver."""
import json

import streamlit.components.v1 as components

from track3d import THREE_URL


def pit_wall_view(data, track, strategy=None, dark=True, height=720, game=None):
    payload = dict(data, dark=dark, strategy=strategy, game=game,
                   points=track[["x", "y", "z"]].round(1).values.tolist())
    page = TEMPLATE.replace("__DATA__", json.dumps(payload)).replace("__THREE__", THREE_URL)
    components.html(page, height=height)


TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body { margin: 0; overflow: hidden; font-family: Inter, system-ui, sans-serif; }
  #app { display: grid; grid-template-columns: 1fr 300px; gap: 10px; height: 700px; }
  #left { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
  #stage { position: relative; flex: 1; border-radius: 16px; overflow: hidden; min-height: 300px; }
  #stage canvas { display: block; }
  .label { position: absolute; transform: translate(-50%, -150%); padding: 2px 7px; border-radius: 999px;
           font-size: 10px; font-weight: 700; white-space: nowrap; pointer-events: none;
           background: var(--panel); color: var(--text); border: 1px solid var(--border); }
  #hud { position: absolute; left: 12px; top: 12px; padding: 10px 12px; border-radius: 12px;
         background: var(--panel); border: 1px solid var(--border); color: var(--text); font-size: 12px; }
  #lap { font: 800 24px 'Saira Condensed', Inter, sans-serif; }
  #status { position: absolute; left: 50%; top: 12px; transform: translateX(-50%); padding: 6px 14px; border-radius: 999px;
            font: 800 13px 'Saira Condensed', Inter, sans-serif; letter-spacing: 1px; display: none; z-index: 3; }
  #ticker { position: absolute; left: 12px; bottom: 12px; padding: 8px 12px; border-radius: 10px; font-size: 12px;
            background: var(--panel); border: 1px solid var(--border); color: var(--text); display: none; }
  #views { position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
  button, select { font: 600 12px Inter, system-ui, sans-serif; padding: 9px 14px; border-radius: 999px; cursor: pointer;
                   border: 1px solid var(--border); background: var(--panel); color: var(--text); }
  button.on, #play { background: #e10600; border-color: #e10600; color: #fff; }
  #controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  #scrub { flex: 1; min-width: 140px; accent-color: #e10600; }

  /* leaderboard */
  #board { border-radius: 16px; background: var(--panel2); border: 1px solid var(--border); overflow-y: auto; color: var(--text); }
  .row { display: grid; grid-template-columns: 24px 5px 1fr 62px 22px 24px 20px; gap: 7px; align-items: center;
         padding: 7px 10px; font-size: 12px; border-bottom: 1px solid var(--border); cursor: pointer; }
  .row.head { font-size: 10px; color: var(--muted); cursor: default; position: sticky; top: 0; background: var(--panel2); z-index: 1; }
  .row.sel { background: rgba(225,6,0,.14); }
  .row .pos { font-weight: 800; text-align: center; }
  .row .bar { height: 18px; border-radius: 3px; }
  .row .code { font-weight: 700; white-space: nowrap; }
  .row .gap { color: var(--muted); text-align: right; font-variant-numeric: tabular-nums; }
  .row .tyre { width: 20px; height: 20px; border-radius: 50%; font-size: 10px; font-weight: 800; color: #111;
               display: flex; align-items: center; justify-content: center; }
  .row .age, .row .stops { color: var(--muted); text-align: center; font-variant-numeric: tabular-nums; }
  .pit { color: #e10600 !important; font-weight: 800; }
  .badge { font-size: 9px; font-weight: 700; padding: 1px 5px; border-radius: 4px; margin-left: 5px;
           border: 1px solid var(--border); color: var(--muted); }
  .badge.box { background: #e10600; border-color: #e10600; color: #fff; }

  /* team radio: small glass cards, newest at the bottom */
  #radio { position: absolute; left: 50%; top: 50px; transform: translateX(-50%); width: min(330px, 62%);
           display: flex; flex-direction: column; gap: 6px; pointer-events: none; z-index: 4; }
  .card { border: 1.5px solid var(--team); border-left-width: 5px; border-radius: 12px; padding: 7px 11px 8px;
          background: var(--glass); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
          color: var(--text); box-shadow: 0 6px 22px rgba(0,0,0,.18);
          opacity: 0; transform: translateY(-6px); transition: opacity .35s ease, transform .35s ease; }
  .card.show { opacity: 1; transform: none; }
  .card .top { display: flex; align-items: center; gap: 6px; font-size: 10px; font-weight: 700; letter-spacing: .6px; }
  .card .who { color: var(--muted); }
  .card .lapTag { margin-left: auto; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--border); color: var(--text); }
  .card .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--team); }
  .card .msg { margin-top: 3px; font-size: 14px; font-weight: 600; line-height: 1.3; }
  .card.box .msg { font: 800 18px 'Saira Condensed', Inter, sans-serif; letter-spacing: .5px; }
  .card.box .dot { background: #e10600; }
  .card.done .dot { background: #2ecc71; }
  .card.missed .dot { background: #f2a71b; }
  #hint { padding: 6px 12px; border-radius: 999px; font-size: 11px; text-align: center; color: var(--muted);
          background: var(--glass); border: 1px solid var(--border); backdrop-filter: blur(8px); align-self: center; }

  /* strategist panel */
  #strat { position: absolute; right: 12px; bottom: 12px; width: 250px; padding: 10px 12px; border-radius: 12px;
           background: var(--panel); border: 1px solid var(--border); color: var(--text); font-size: 11px; display: none; }
  #strat h4 { margin: 0 0 6px; font: 800 13px 'Saira Condensed', Inter, sans-serif; letter-spacing: .5px; }
  #strat .plan { font-size: 13px; font-weight: 700; }
  #strat .count { margin-top: 2px; font-weight: 700; }
  #strat .count.now { color: #e10600; }
  #strat .muted { color: var(--muted); }
  #strat .log { margin-top: 8px; border-top: 1px solid var(--border); padding-top: 6px; display: grid; gap: 3px; }
  #strat .log div { display: grid; grid-template-columns: 30px 1fr; gap: 4px; }
  #strat .log b { color: var(--muted); font-weight: 700; }

  /* verdict */
  #verdict { position: absolute; inset: 0; background: var(--panel2); color: var(--text); padding: 18px 20px; overflow: auto;
             display: none; z-index: 6; font-size: 13px; }
  #verdict h3 { margin: 0; font: 800 30px 'Saira Condensed', Inter, sans-serif; }
  #verdict h3 span { color: #e10600; }
  #verdict .sub { color: var(--muted); margin: 2px 0 10px; }
  #verdict p { margin: 4px 0; }
  #verdict .note { color: var(--muted); }
  #verdict .chips { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0 4px; }
  .chip { padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }
  .chip.v-matched { background: rgba(46,204,113,.18); color: #22a85a; }
  .chip.v-close { background: rgba(242,194,27,.2); color: #b38900; }
  .chip.v-different, .chip.v-stayed_out { background: rgba(225,6,0,.15); color: #e10600; }
  .chip.v-unplanned { background: rgba(140,140,150,.18); color: var(--muted); }
  #verdict table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }
  #verdict th, #verdict td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); }
  #verdict th { color: var(--muted); font-weight: 600; }
  #verdict .close { position: absolute; top: 14px; right: 14px; }
  #verdict .legend { margin-top: 12px; display: flex; gap: 10px; flex-wrap: wrap; color: var(--muted); font-size: 12px; }
  #verdict #toggleMissed { margin-top: 10px; }
  #verdict .knew { margin: 10px 0 4px; padding: 10px 12px; border-radius: 12px; border: 1px solid var(--border);
                   background: rgba(127,127,140,.08); }
  #verdict .knew b { display: block; margin-bottom: 4px; }
  #verdict .knew ul { margin: 0; padding-left: 18px; }
  #verdict .knew li { margin: 2px 0; }

  /* Be the Race Engineer */
  #gameBar { display: none; align-items: center; gap: 8px; flex-wrap: wrap; }
  #boxBtn { font: 900 16px 'Saira Condensed', Inter, sans-serif; letter-spacing: 2px; padding: 10px 26px;
            background: #e10600; border-color: #e10600; color: #fff; transform: skewX(-8deg); }
  #boxBtn.cancel { background: transparent; color: #e10600; }
  .tyreBtn { width: 38px; height: 38px; padding: 0; border-radius: 50%; font-weight: 900; color: #111;
             border: 3px solid transparent; }
  .tyreBtn.on { border-color: var(--text); box-shadow: 0 0 0 2px var(--panel2); }
  #gameBar .lbl { font-size: 12px; color: var(--muted); }
  #intro { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; z-index: 7;
           background: rgba(0,0,0,.45); }
  #intro .box { max-width: 440px; margin: 16px; padding: 18px 20px; border-radius: 16px; background: var(--panel2);
                color: var(--text); border: 1px solid var(--border); font-size: 13px; line-height: 1.5; }
  #intro h3 { margin: 0 0 8px; font: 800 24px 'Saira Condensed', Inter, sans-serif; }
  #intro ul { margin: 6px 0 14px; padding-left: 18px; }
  #intro button { background: #e10600; border-color: #e10600; color: #fff; }
  .row.you { background: rgba(225,6,0,.16); }
  #verdict .result { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 12px 0; }
  #verdict .result div { padding: 10px; border-radius: 12px; border: 1px solid var(--border); text-align: center; }
  #verdict .result b { display: block; font: 800 26px 'Saira Condensed', Inter, sans-serif; }
  #verdict .result span { color: var(--muted); font-size: 12px; }
  #verdict .result .me { border-color: #e10600; }
  #verdict .big2 { font: 800 20px 'Saira Condensed', Inter, sans-serif; margin: 8px 0 2px; }
  .chip.v-good { background: rgba(46,204,113,.18); color: #22a85a; }
  .chip.v-early, .chip.v-late { background: rgba(242,194,27,.2); color: #b38900; }
  .sim { display: inline-block; margin-left: 8px; padding: 2px 8px; border-radius: 999px; font-size: 11px;
         font-weight: 700; border: 1px solid var(--border); color: var(--muted); vertical-align: middle; }

  @media (max-width: 760px) {
    #app { grid-template-columns: 1fr; height: auto; }
    #stage { height: 420px; flex: none; }
    #board { height: 260px; }
    #views { left: 8px; right: 8px; top: 8px; justify-content: flex-start; gap: 6px; }
    #views button { padding: 6px 10px; font-size: 11px; }
    #hud { top: 46px; left: 8px; padding: 6px 10px; }
    #lap { font-size: 18px; }
    #status { top: 48px; left: auto; right: 8px; transform: none; }
    #radio { width: calc(100% - 16px); top: 104px; }
    .card .msg { font-size: 13px; }
    .card.box .msg { font-size: 16px; }
    #strat { left: 8px; right: 8px; bottom: 8px; width: auto; padding: 8px 10px; }
    #strat .log { display: none; }
    #ticker { display: none !important; }
    #verdict .result { grid-template-columns: 1fr; }
  }
</style>
<script type="importmap">
  { "imports": { "three": "__THREE__/build/three.module.js",
                 "three/addons/": "__THREE__/examples/jsm/" } }
</script>
</head>
<body>
<div id="app">
  <div id="left">
    <div id="stage">
      <div id="hud"><div id="lap">Lap 1</div><div id="clock">0:00</div></div>
      <div id="status"></div>
      <div id="views">
        <button id="overview" class="on">Overview</button><button id="follow">Follow</button>
        <button id="verdictBtn">Strategist verdict</button>
      </div>
      <div id="radio"><div id="hint">Tap a driver to hear their team radio</div></div>
      <div id="ticker"></div>
      <div id="strat"></div>
      <div id="verdict"></div>
      <div id="intro"></div>
    </div>
    <div id="controls">
      <button id="play">Play</button>
      <select id="speed" aria-label="Replay speed">
        <option value="1">1×</option><option value="5">5×</option><option value="10" selected>10×</option>
        <option value="30">30×</option><option value="60">60×</option>
      </select>
      <select id="jump" aria-label="Jump to lap"></select>
      <input id="scrub" type="range" min="0" max="1000" value="0" aria-label="Position in the race">
      <div id="gameBar">
        <button id="boxBtn" aria-label="Call your driver into the pits">BOX</button>
        <span class="lbl">Tyres:</span>
        <button class="tyreBtn" data-t="SOFT" style="background:#e10600" aria-label="Softs">S</button>
        <button class="tyreBtn" data-t="MEDIUM" style="background:#f2c21b" aria-label="Mediums">M</button>
        <button class="tyreBtn" data-t="HARD" style="background:#e8e8e8" aria-label="Hards">H</button>
      </div>
    </div>
  </div>
  <div id="board" aria-label="Live leaderboard"></div>
</div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const D = __DATA__;
const PLANS = D.strategy ? D.strategy.calls : null;
const RADIO = D.strategy ? D.strategy.radio : {};

// ---------- theme ----------
const T = D.dark
  ? { bg: "#0b0b10", panel: "rgba(21,21,30,.9)", panel2: "#15151e", border: "#2c2c3a", text: "#f5f5f7",
      muted: "#a3a3b2", ground: "#111118", grid: "#23232f", curtain: "#ffffff", track: "#3a3a4a",
      glass: "rgba(21,21,30,.55)" }
  : { bg: "#f6f6f3", panel: "rgba(255,255,255,.94)", panel2: "#ffffff", border: "#d9d9d4", text: "#15151e",
      muted: "#55556a", ground: "#ececea", grid: "#d6d6cf", curtain: "#15151e", track: "#c4c4cc",
      glass: "rgba(255,255,255,.6)" };
const STATUS = { SC: { text: "SAFETY CAR", bg: "#f2c21b", fg: "#111", track: "#8a7414" },
                 VSC: { text: "VIRTUAL SAFETY CAR", bg: "#f2c21b", fg: "#111", track: "#8a7414" },
                 RED: { text: "RED FLAG", bg: "#e10600", fg: "#fff", track: "#7a1d1d" } };
const TYRES = { SOFT: ["S", "#e10600"], MEDIUM: ["M", "#f2c21b"], HARD: ["H", "#e8e8e8"],
                INTERMEDIATE: ["I", "#2ecc71"], WET: ["W", "#2b6cff"] };
const app = document.getElementById("app"), stage = document.getElementById("stage");
for (const [k, v] of Object.entries({ "--panel": T.panel, "--panel2": T.panel2, "--border": T.border,
                                      "--text": T.text, "--muted": T.muted, "--glass": T.glass }))
  app.style.setProperty(k, v);
document.body.style.background = T.bg;

// ---------- the track ----------
const P = D.points, n = P.length;
const cx = P.reduce((a, p) => a + p[0], 0) / n, cy = P.reduce((a, p) => a + p[1], 0) / n;
const zMin = Math.min(...P.map(p => p[2]));
const extent = Math.max(...P.map(p => Math.max(Math.abs(p[0] - cx), Math.abs(p[1] - cy))));
const S = 50 / extent, LIFT = 4;
const pts = P.map(p => new THREE.Vector3((p[0] - cx) * S, (p[2] - zMin) * S * LIFT + 0.5, -(p[1] - cy) * S));
const curve = new THREE.CatmullRomCurve3(pts, true, "centripetal");
const K = 8, N = n * K, samples = curve.getPoints(N);

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
const pos = [], idx = [], leftEdge = [], rightEdge = [], cPos = [];
for (let j = 0; j < samples.length; j++) {
  const p = samples[j];
  const side = new THREE.Vector3().crossVectors(curve.getTangent(j / N), up).normalize().multiplyScalar(W);
  pos.push(p.x + side.x, p.y, p.z + side.z, p.x - side.x, p.y, p.z - side.z);
  leftEdge.push(new THREE.Vector3(p.x + side.x, p.y + 0.02, p.z + side.z));
  rightEdge.push(new THREE.Vector3(p.x - side.x, p.y + 0.02, p.z - side.z));
  cPos.push(p.x, p.y - 0.05, p.z, p.x, 0, p.z);
  if (j < samples.length - 1) { const a = 2 * j; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
}
const ribbonGeo = new THREE.BufferGeometry();
ribbonGeo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
ribbonGeo.setIndex(idx);
const ribbonMat = new THREE.MeshBasicMaterial({ color: T.track, side: THREE.DoubleSide });
scene.add(new THREE.Mesh(ribbonGeo, ribbonMat));
const edgeMat = new THREE.LineBasicMaterial({ color: T.text, transparent: true, opacity: 0.35 });
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(leftEdge), edgeMat));
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(rightEdge), edgeMat));
const curtain = new THREE.BufferGeometry();
curtain.setAttribute("position", new THREE.Float32BufferAttribute(cPos, 3));
curtain.setIndex(idx);
scene.add(new THREE.Mesh(curtain, new THREE.MeshBasicMaterial({
  color: T.curtain, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false })));
const startLine = new THREE.Mesh(new THREE.BoxGeometry(W * 2.3, 0.25, 0.6), new THREE.MeshBasicMaterial({ color: "#ffffff" }));
startLine.position.copy(samples[0]);
startLine.lookAt(samples[0].clone().add(curve.getTangent(0)));
scene.add(startLine);

// ---------- labels ----------
function makeLabel(text) {
  const el = document.createElement("div");
  el.className = "label";
  el.textContent = text;
  stage.appendChild(el);
  return el;
}
function placeLabel(el, p, visible) {
  const v = p.clone().project(camera);
  el.style.display = visible && v.z <= 1 ? "block" : "none";
  el.style.left = ((v.x * 0.5 + 0.5) * stage.clientWidth) + "px";
  el.style.top = ((-v.y * 0.5 + 0.5) * stage.clientHeight) + "px";
}

// ---------- the cars ----------
const cars = D.cars.map(c => {
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(0.9, 20, 14), new THREE.MeshBasicMaterial({ color: c.colour }));
  const halo = new THREE.Mesh(new THREE.SphereGeometry(1.9, 20, 14),
    new THREE.MeshBasicMaterial({ color: c.colour, transparent: true, opacity: 0, depthWrite: false }));
  mesh.add(halo);
  scene.add(mesh);
  // each radio message gets its replay time: the start of the lap it is heard on, plus any seconds into it
  const radio = (RADIO[c.number] || []).map(m => {
    const start = c.lapStarts[m.lap - 1];
    return { ...m, t: start === undefined || start < 0 ? null : start + (m.at || 0) };
  }).filter(m => m.t !== null);
  return { ...c, mesh, halo, radio, el: makeLabel(c.code), p: 0, showLabel: false, boxNow: false };
});
let selected = null;

const last = arr => arr[arr.length - 1];
function progAt(c, time) {
  const i = Math.min(Math.floor(time), c.prog.length - 1), j = Math.min(i + 1, c.prog.length - 1);
  return c.prog[i] + (c.prog[j] - c.prog[i]) * (time - Math.floor(time));
}
function lastIndexAtOrBefore(arr, x) {
  let lo = 0, hi = arr.length - 1, ans = -1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (arr[mid] <= x) { ans = mid; lo = mid + 1; } else hi = mid - 1; }
  return ans;
}
function firstIndexAtOrAbove(arr, x) {
  let lo = 0, hi = arr.length - 1, ans = arr.length - 1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (arr[mid] >= x) { ans = mid; hi = mid - 1; } else lo = mid + 1; }
  return ans;
}
const isOut = (c, time) => c.out !== null && time >= c.out;

// The strategist's plan for a car right now: the one made at the end of its last completed lap
function planFor(c, time) {
  if (!PLANS || !PLANS[c.number]) return null;
  const completed = lastIndexAtOrBefore(c.lapStarts, time);     // index i = on lap i+1 = i laps done
  if (completed < 1) return null;
  const plan = PLANS[c.number][String(completed)];
  return plan ? { onLap: completed + 1, ...plan } : null;
}

// ---------- camera ----------
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.minDistance = 12;
controls.maxDistance = 220;
controls.maxPolarAngle = Math.PI * 0.48;
let follow = false;
const overviewBtn = document.getElementById("overview"), followBtn = document.getElementById("follow");
function resetView() { camera.position.set(0, 70, 95); controls.target.set(0, 0, 0); controls.update(); }
let order = cars.slice();
const focusCar = () => selected || order[0];
overviewBtn.onclick = () => { follow = false; overviewBtn.classList.add("on"); followBtn.classList.remove("on"); resetView(); };
followBtn.onclick = () => {
  follow = true; followBtn.classList.add("on"); overviewBtn.classList.remove("on");
  const p = focusCar().mesh.position;
  controls.target.copy(p);
  camera.position.copy(p.clone().add(new THREE.Vector3(0, 22, 30)));
};
resetView();

// ---------- playback ----------
let END = D.duration;
const playBtn = document.getElementById("play"), speedSel = document.getElementById("speed"),
      jumpSel = document.getElementById("jump"), scrub = document.getElementById("scrub");
let time = 0, playing = false, lastFrame = performance.now(), verdictShown = false;
jumpSel.innerHTML = "<option value=''>Jump to lap</option>" +
  D.lapTimes.map((t, k) => `<option value="${t}">Lap ${k + 1}</option>`).join("");
function setPlaying(on) { playing = on; playBtn.textContent = on ? "Pause" : (time >= END ? "Replay" : "Play"); }
playBtn.onclick = () => { if (time >= END) { time = 0; verdictShown = false; } setPlaying(!playing); };
scrub.oninput = () => { time = scrub.value / 1000 * END; };
jumpSel.onchange = () => { if (jumpSel.value !== "") time = Number(jumpSel.value); jumpSel.value = ""; };

// ---------- HUD: lap, clock, status, ticker ----------
const lapEl = document.getElementById("lap"), clockEl = document.getElementById("clock"),
      statusEl = document.getElementById("status"), tickerEl = document.getElementById("ticker");
tickerEl.style.right = PLANS || D.game ? "274px" : "12px";
const fmtClock = s => { s = Math.max(0, Math.floor(s)); const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60;
  return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(s % 60).padStart(2, "0"); };
let currentStatus = null;
function updateHud() {
  const leader = order[0];
  lapEl.textContent = `Lap ${Math.min(D.laps, Math.max(1, Math.floor(leader.p) + 1))} / ${D.laps}`;
  clockEl.textContent = fmtClock(time);
  const s = D.status.find(s => time >= s.start && time < s.end);
  const kind = s ? s.kind : null;
  if (kind !== currentStatus) {
    currentStatus = kind;
    if (kind) {
      statusEl.textContent = STATUS[kind].text;
      statusEl.style.background = STATUS[kind].bg; statusEl.style.color = STATUS[kind].fg;
      statusEl.style.display = "block";
      ribbonMat.color.set(STATUS[kind].track);
    } else {
      statusEl.style.display = "none";
      ribbonMat.color.set(T.track);
    }
  }
  const recent = D.events.filter(e => e.t <= time && time - e.t < 10);
  if (recent.length) { tickerEl.textContent = "Race control: " + last(recent).text; tickerEl.style.display = "block"; }
  else tickerEl.style.display = "none";
}

// ---------- team radio cards ----------
const radioEl = document.getElementById("radio"), hintEl = document.getElementById("hint");
const CARD_LIFE = 4500;                                   // milliseconds on screen
function maxCards() { return parseFloat(speedSel.value) >= 30 ? 2 : 3; }
function removeCard(card) {
  card.classList.remove("show");
  setTimeout(() => card.remove(), 350);
}
function showCard(c, m) {
  const card = document.createElement("div");
  card.className = "card " + m.kind;
  card.style.setProperty("--team", c.colour);
  card.innerHTML = `<div class="top"><span class="dot"></span><span class="who">RADIO · ${c.code}</span>` +
                   `<span class="lapTag">L${m.lap}</span></div><div class="msg"></div>`;
  card.querySelector(".msg").textContent = m.text;
  radioEl.appendChild(card);
  requestAnimationFrame(() => card.classList.add("show"));
  const cards = [...radioEl.querySelectorAll(".card")].filter(k => !k.dataset.leaving);
  while (cards.length > maxCards()) { const old = cards.shift(); old.dataset.leaving = "1"; removeCard(old); }
  setTimeout(() => { card.dataset.leaving = "1"; removeCard(card); }, CARD_LIFE);
}
function clearCards() { radioEl.querySelectorAll(".card").forEach(k => k.remove()); }
let radioTime = 0;
function checkRadio() {
  const from = radioTime;
  radioTime = time;
  if (!selected || !playing || time < from || time - from > 20) return;   // no flood after a jump
  for (const m of selected.radio) if (m.t > from && m.t <= time) showCard(selected, m);
}

// ---------- strategist panel ----------
const stratEl = document.getElementById("strat");
const esc = s => String(s).replace(/[&<>]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[ch]));
const finishText = p => `Finish P${Math.round(p.finish)}` + (p.best !== p.worst ? ` (likely P${p.best}–P${p.worst})` : "");
function updateStrat() {
  if (D.game) { updateGamePanel(); return; }
  if (!PLANS) return;
  const c = focusCar();
  const plan = isOut(c, time) ? null : planFor(c, time);
  stratEl.style.display = "block";
  let html = `<h4>STRATEGIST · ${c.code}</h4>`;
  if (!plan) {
    html += "<div class='muted'>No plan right now (opening laps, a pit stop, wet tyres or a red flag).</div>";
  } else if (plan.pit === null) {
    html += `<div class="plan">No more stops</div><div class="muted">${finishText(plan)}</div>`;
  } else {
    const toGo = plan.pit - plan.onLap;
    const count = toGo <= 0 ? "Box this lap" : `Box in ${toGo} lap${toGo > 1 ? "s" : ""}`;
    html += `<div class="plan">Plan: box lap ${plan.pit} → ${plan.tyre}</div>` +
            `<div class="count${toGo <= 0 ? " now" : ""}">${count}</div>` +
            `<div class="muted">${plan.rejoin ? `Out in ~P${plan.rejoin} · ` : ""}${finishText(plan)}</div>`;
  }
  const heard = c.radio.filter(m => m.t <= time).slice(-4);
  if (heard.length)
    html += "<div class='log'>" + heard.map(m => `<div><b>L${m.lap}</b><span>${esc(m.text)}</span></div>`).join("") + "</div>";
  if (!selected) html += "<div class='muted' style='margin-top:6px'>Showing the leader. Tap a driver to follow their radio.</div>";
  stratEl.innerHTML = html;
}

// ---------- leaderboard ----------
const board = document.getElementById("board");
board.onpointerdown = e => {     // on press, so a redraw mid-click never loses it
  if (D.game) return;                                    // in the game you always follow your own car
  const row = e.target.closest(".row[data-n]");
  if (!row) return;
  const car = cars.find(c => c.number === Number(row.dataset.n));
  selected = selected === car ? null : car;
  clearCards();
  hintEl.style.display = selected ? "none" : "block";
  radioTime = time;
  updateBoard();
  updateStrat();
};
function gapText(c, leader) {
  if (c === leader) return "Leader";
  const behind = leader.p - c.p;
  if (behind >= 1) { const lapsDown = Math.floor(behind); return `+${lapsDown} lap${lapsDown > 1 ? "s" : ""}`; }
  const k = firstIndexAtOrAbove(leader.prog, c.p);
  return "+" + Math.max(0, time - k).toFixed(1);
}
function updateBoard() {
  // on track: by progress; after the flag: the finishing order (laps, then who crossed the line first)
  const score = c => { const f = finishOf(c); return f && time >= f.end ? f.laps + 1 - f.end / 1e7 : c.p; };
  const running = cars.filter(c => !isOut(c, time) && !c.isReal).sort((a, b) => score(b) - score(a));
  const retired = cars.filter(c => isOut(c, time) && !c.isReal);
  order = running.concat(retired);
  const leader = order[0];
  let html = "<div class='row head'><span>POS</span><span></span><span>CAR</span><span style='text-align:right'>GAP</span>" +
             "<span>TYRE</span><span>AGE</span><span>PIT</span></div>";
  order.forEach((c, i) => {
    const k = lastIndexAtOrBefore(c.lapStarts, time);
    const tyre = TYRES[k >= 0 ? c.compound[k] : ""] || ["?", "#8a8a96"];
    const age = k >= 0 ? c.age[k] : "";
    const stops = c.pits.filter(t => t <= time).length;
    const inPit = c.pits.some(t => time >= t && time - t < 25);
    const out = isOut(c, time);
    let gap = out ? "OUT" : inPit ? "<span class='pit'>PIT</span>" : gapText(c, leader);
    const f = finishOf(c), lf = finishOf(leader);
    if (!out && f && lf && time >= f.end)                 // after the flag: the real finishing gaps
      gap = c === leader ? "Leader" : f.laps < lf.laps ? `+${lf.laps - f.laps} lap${lf.laps - f.laps > 1 ? "s" : ""}`
                                                       : "+" + (f.end - lf.end).toFixed(1);
    const plan = out ? null : c.isYou ? yourPlan() : D.game ? null : planFor(c, time);
    c.boxNow = !!plan && plan.pit !== null && plan.pit === plan.onLap && !inPit;
    const badge = !plan || plan.pit === null ? ""
      : c.boxNow ? "<span class='badge box' title='Box this lap'>BOX</span>"
      : `<span class='badge' title='Planned stop'>L${plan.pit}</span>`;
    c.showLabel = i < 3 || c === selected;
    html += `<div class="row${c.isYou ? " you" : c === selected ? " sel" : ""}" data-n="${c.number}">` +
      `<span class="pos">${out ? "-" : i + 1}</span><span class="bar" style="background:${c.colour}"></span>` +
      `<span class="code">${c.code}${badge}</span><span class="gap">${gap}</span>` +
      `<span class="tyre" style="background:${tyre[1]}">${tyre[0]}</span><span class="age">${age}</span>` +
      `<span class="stops">${stops}</span></div>`;
  });
  board.innerHTML = html;
}

// ---------- verdict: the strategist vs the real teams ----------
const verdictEl = document.getElementById("verdict"), verdictBtn = document.getElementById("verdictBtn");
if (!D.strategy) verdictBtn.style.display = "none";
const VERDICT = {
  matched: ["✓ Matched", "The team pitted within 2 laps of the lap our strategist planned"],
  close: ["≈ Close", "The team pitted 3 to 5 laps away from our strategist's plan"],
  different: ["✗ Different", "The team pitted 6 or more laps away from our plan, or when we planned no stop"],
  stayed_out: ["✗ Team stayed out", "Our strategist said box, but the team kept going"],
  unplanned: ["Not counted", "A stop in the first 3 laps is usually damage, which no strategist can plan"],
};
function diffText(r) {
  if (r.verdict === "stayed_out") return "–";
  if (r.diff === null) return r.verdict === "unplanned" ? "Unplanned (damage?)" : "–";
  if (r.diff === 0) return "Same lap";
  const n = Math.abs(r.diff);
  return `Team ${n} lap${n > 1 ? "s" : ""} ${r.diff < 0 ? "earlier" : "later"}`;
}
function knewText(k) {
  if (!k) return "";
  const vs = (x, more, less) => x >= 1.1 ? `${x.toFixed(1)}× ${more} than an average circuit`
                              : x <= 0.9 ? `${x.toFixed(1)}× (${less} than an average circuit)` : "about average";
  const items = [];
  if (k.source === "typical values") items.push("Nothing yet: no earlier races to learn from, so it used typical values.");
  else {
    items.push(`Tyre wear here: ${vs(k.wear, "higher", "gentler")}.`);
    items.push(`How long teams run a set of tyres here: ${vs(k.stints, "longer", "shorter")}.`);
    items.push(`Teams usually make their first stop about ${Math.round(k.first_stop * 100)}% into the race ` +
               `(around lap ${Math.round(k.first_stop * D.laps)}). A stop costs about ${Math.round(k.pit_loss)} s.`);
    items.push(`Learned from ${k.source}.`);
  }
  items.push(k.timing ? `Its pit-timing model learned when real teams stop from ${k.timing}.`
                      : "No pit-timing model yet (it needs a full earlier season).");
  return `<div class="knew"><b>What our strategist knew before the race</b><ul>${items.map(i => `<li>${i}</li>`).join("")}</ul></div>`;
}
function showVerdict() {
  const v = D.strategy.verdict;
  const row = r => `<tr><td><b>${r.code}</b></td>` +
    `<td>${r.planned !== null ? "Lap " + r.planned : "No stop planned"}</td>` +
    `<td>${r.real !== null ? "Lap " + r.real : "Stayed out"}</td><td>${diffText(r)}</td>` +
    `<td><span class="chip v-${r.verdict}" title="${VERDICT[r.verdict][1]}">${VERDICT[r.verdict][0]}</span></td></tr>`;
  const stops = v.table.filter(r => r.verdict !== "stayed_out");
  const missed = v.table.filter(r => r.verdict === "stayed_out");
  const head = "<tr><th>Driver</th><th>Our strategist planned</th><th>Team actually pitted</th><th>Difference</th><th>Verdict</th></tr>";
  const notes = [];
  if (v.red_laps.length)
    notes.push(`Red flag on lap ${v.red_laps.join(", ")}: tyre changes during the stoppage aren't counted.`);
  if (v.unplanned) notes.push("Stops in the first 3 laps (usually damage) aren't counted.");
  verdictEl.innerHTML = `<button class="close" id="closeVerdict">Close</button>` +
    `<h3><span>${v.matched} of ${v.stops}</span> pit stops matched</h3>` +
    `<div class="sub">All drivers in this race combined</div>` +
    `<p><b>Matched</b> means the real team pitted within 2 laps of the lap our strategist planned.</p>` +
    notes.map(t => `<p class="note">${t}</p>`).join("") +
    `<p class="note">Our strategist only knew what had happened up to each lap. Real teams also have tyre sensors ` +
    `and team radio, so matching every stop isn't expected.</p>` + knewText(D.strategy.knew) +
    `<div class="chips"><span class="chip v-matched">✓ Matched ${v.matched}</span><span class="chip v-close">≈ Close ${v.close}</span>` +
    `<span class="chip v-different">✗ Different ${v.different}</span>` +
    `<span class="chip v-stayed_out">✗ Team stayed out ${v.stayed_out}</span></div>` +
    `<table>${head}${stops.map(row).join("")}</table>` +
    (missed.length ? `<button id="toggleMissed">Show the ${missed.length} BOX calls the team didn't follow</button>` +
                     `<table id="missedTable" style="display:none">${head}${missed.map(row).join("")}</table>` : "") +
    `<div class="legend"><span><b>✓ Matched</b> within 2 laps</span><span><b>≈ Close</b> 3–5 laps apart</span>` +
    `<span><b>✗ Different</b> 6+ laps apart</span><span><b>Not counted</b> damage or red flag</span></div>`;
  verdictEl.style.display = "block";
  document.getElementById("closeVerdict").onclick = () => { verdictEl.style.display = "none"; };
  const toggle = document.getElementById("toggleMissed");
  if (toggle) toggle.onclick = () => {
    const t = document.getElementById("missedTable"), open = t.style.display === "none";
    t.style.display = open ? "table" : "none";
    toggle.textContent = (open ? "Hide" : "Show") + ` the ${missed.length} BOX calls the team didn't follow`;
  };
}
verdictBtn.onclick = showVerdict;

// ---------- Be the Race Engineer (only in game mode) ----------
let yourPlan = () => null, gameTick = () => {}, updateGamePanel = () => {}, finishOf = () => null;
if (D.game) {
  const G = D.game, GD = G.drivers[G.driver], TY = G.tyres, nLaps = GD.laps, hard = G.mode === "hard";
  const SHORT = { SOFT: "Softs", MEDIUM: "Mediums", HARD: "Hards" };
  const me = cars.find(c => c.number === Number(G.driver));

  // the real car: faded (normal mode) or hidden (hard mode); it no longer races in the leaderboard
  me.isReal = true;
  me.hidden = hard;
  me.mesh.material.transparent = true;
  me.mesh.material.opacity = 0.35;
  me.el.textContent = "REAL " + me.code;
  me.showLabel = !hard;

  // your car: the team colour with a white ring
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1.0, 20, 14), new THREE.MeshBasicMaterial({ color: me.colour }));
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.22, 8, 28), new THREE.MeshBasicMaterial({ color: "#ffffff" }));
  ring.rotation.x = Math.PI / 2;
  mesh.add(ring);
  const halo = new THREE.Mesh(new THREE.SphereGeometry(2.1, 20, 14),
    new THREE.MeshBasicMaterial({ color: me.colour, transparent: true, opacity: 0, depthWrite: false }));
  mesh.add(halo);
  scene.add(mesh);
  const you = { number: -1, code: "YOU", name: "You", colour: me.colour, mesh, halo, el: makeLabel("YOU"),
                radio: [], prog: [], lapStarts: [], compound: [], age: [], pits: [], out: null,
                isYou: true, p: 0, showLabel: true, boxNow: false, log: [] };
  cars.push(you);
  selected = you;
  hintEl.style.display = "none";
  verdictBtn.style.display = "none";
  jumpSel.style.display = "none";                 // in the game, the race only runs forward
  scrub.disabled = true;
  document.getElementById("gameBar").style.display = "flex";

  // ---- the simulation: the real driver's pace + what YOUR tyres cost + your pit stops ----
  const lapCost = (comp, age) => TY.offset[comp] + TY.wear[comp] * age
    + TY.cliffRate * Math.max(0, age - TY.cliffStart * TY.life[comp]);
  function simulate(plan) {
    const byLap = {};
    plan.forEach(s => { byLap[s.lap] = s; });
    let comp = GD.startTyre, age = GD.startAge, t = GD.start, carry = 0;
    const cal = (GD.calibration || 0) / nLaps;      // copying the real stops = the real result
    const starts = [], comps = [], ages = [], pits = [];
    for (let k = 1; k <= nLaps; k++) {
      starts.push(t); comps.push(comp); ages.push(Math.round(age));
      let lap = GD.pace[k - 1] + lapCost(comp, age) + carry + cal;
      carry = 0;
      const s = byLap[k];
      if (s) {
        const loss = s.free ? 0 : G.pitLoss * (G.scFactor[GD.neutral[k - 1]] || 1);
        lap += 0.4 * loss;
        carry = 0.6 * loss;
        if (!s.free) pits.push(t + lap - 2);
        comp = s.tyre; age = s.age || 0;                 // a real team sometimes fits a used set
      } else {
        age += 1;
      }
      t += lap;
    }
    return { starts, comps, ages, pits, finish: t };
  }

  // how the real car covers one lap over time, to move your car smoothly round the track
  let lapIdx = 2, best = Infinity;
  const durations = [];
  for (let i = 2; i < Math.min(nLaps - 2, me.lapStarts.length - 1); i++) {
    if (me.lapStarts[i] >= 0 && me.lapStarts[i + 1] > me.lapStarts[i]) durations.push([i, me.lapStarts[i + 1] - me.lapStarts[i]]);
  }
  const median = durations.map(d => d[1]).sort((a, b) => a - b)[Math.floor(durations.length / 2)] || 90;
  for (const [i, d] of durations) if (Math.abs(d - median) < best) { best = Math.abs(d - median); lapIdx = i; }
  const s0 = me.lapStarts[lapIdx], d0 = me.lapStarts[lapIdx + 1] - s0;
  const p0 = progAt(me, s0), span = (progAt(me, s0 + d0) - p0) || 1;
  const profile = Array.from({ length: 101 }, (_, j) => Math.min(1, Math.max(0, (progAt(me, s0 + d0 * j / 100) - p0) / span)));
  for (let j = 1; j <= 100; j++) profile[j] = Math.max(profile[j], profile[j - 1]);
  // where on the track (in laps) lap 1 begins: measured on laps 2-6, where every start is on the line
  const offsets = [];
  for (let i = 1; i <= 5 && i < me.lapStarts.length; i++) if (me.lapStarts[i] >= 0) offsets.push(progAt(me, me.lapStarts[i]) - i);
  const startProg = offsets.length ? offsets.sort((a, b) => a - b)[Math.floor(offsets.length / 2)] : 0;
  const realEnd = (G.finish.find(f => f.number === me.number) || {}).end;
  const doneProg = realEnd !== undefined ? progAt(me, realEnd) : startProg + nLaps;   // where a finished car sits

  let stops = [];                                        // your stops: {lap, tyre, free}
  let tyreChoice = GD.startTyre === "HARD" ? "MEDIUM" : "HARD";
  function rebuild() {
    const sim = simulate(stops);
    you.sim = sim;
    you.lapStarts = sim.starts.slice();
    you.compound = sim.comps;
    you.age = sim.ages;
    you.pits = sim.pits;
    END = Math.max(D.duration, Math.ceil(sim.finish + 25));
    const len = END + 2, prog = new Array(len);
    for (let t = 0; t < len; t++) {
      if (t < sim.starts[0]) { prog[t] = progAt(me, t); continue; }
      if (t >= sim.finish) { prog[t] = doneProg + (t - sim.finish) * 0.002; continue; }
      const j = lastIndexAtOrBefore(sim.starts, t);
      const end = j + 1 < nLaps ? sim.starts[j + 1] : sim.finish;
      const x = (t - sim.starts[j]) / (end - sim.starts[j]) * 100, a = Math.floor(x), b = Math.min(100, a + 1);
      prog[t] = startProg + j + profile[a] + (profile[b] - profile[a]) * (x - a);
    }
    you.prog = prog;
  }
  rebuild();

  finishOf = c => c.isYou ? { laps: nLaps, end: you.sim.finish } : G.finish.find(f => f.number === c.number);
  const curLap = () => lastIndexAtOrBefore(you.lapStarts, time) + 1;          // 0 before the start
  const lapEnd = k => k < nLaps ? you.lapStarts[k] : you.sim.finish;          // end of lap k
  const pending = () => stops.find(s => s.lap >= curLap());
  yourPlan = () => {
    const s = pending(), k = curLap();
    return s ? { pit: s.lap, onLap: k } : null;
  };
  function say(kind, text, lap) {
    const m = { lap: lap || Math.max(1, curLap()), kind, text, t: time };
    you.log.push(m);
    showCard(you, m);
  }
  function position() {
    const running = order.filter(c => !isOut(c, time));
    return running.indexOf(you) + 1;
  }
  function rejoin(lap) {                                  // expected position at the end of your out-lap
    const mine = lapEnd(lap + 1);
    let pos = 1;
    for (const c of cars) {
      if (c.isYou || c.isReal) continue;
      const e = c.lapStarts[lap + 1];
      if (e !== undefined && e >= 0 && e < mine) pos++;
    }
    return pos;
  }
  const used = plan => new Set([GD.startTyre, ...plan.map(s => s.tyre)]).size >= 2;

  // ---- the controls ----
  const boxBtn = document.getElementById("boxBtn"), tyreBtns = [...document.querySelectorAll(".tyreBtn")];
  function updateControls() {
    tyreBtns.forEach(b => b.classList.toggle("on", b.dataset.t === tyreChoice));
    const s = pending();
    boxBtn.textContent = s ? `CANCEL (L${s.lap})` : "BOX";
    boxBtn.classList.toggle("cancel", !!s);
  }
  tyreBtns.forEach(b => b.onclick = () => {
    tyreChoice = b.dataset.t;
    const s = pending();
    if (s && s.lap > curLap() - 1) { s.tyre = tyreChoice; rebuild(); }
    updateControls();
  });
  let started = false;
  boxBtn.onclick = () => {
    if (!started) return startRace();
    const k = curLap();
    if (k < 1 || time >= you.sim.finish) return;
    const s = pending();
    if (s) {
      stops = stops.filter(x => x !== s);
      rebuild(); updateControls();
      return say("missed", `Stay out, stay out. Stop on lap ${s.lap} cancelled.`);
    }
    const frac = (time - you.lapStarts[k - 1]) / (lapEnd(k) - you.lapStarts[k - 1]);
    const lap = frac < 0.85 ? k : k + 1;                  // too close to the pit entry: next lap
    if (lap > nLaps - 1) return say("missed", "Too late to stop now. Bring it home.");
    const free = GD.redLap !== null && lap === GD.redLap;
    stops.push({ lap, tyre: tyreChoice, free });
    stops.sort((a, b) => a.lap - b.lap);
    rebuild(); updateControls();
    if (free) say("box", `Red flag: free change to ${SHORT[tyreChoice]}.`);
    else say("box", `Box… box… ${SHORT[tyreChoice]}${lap > k ? " next lap" : ""} · out in ~P${rejoin(lap)}`);
  };

  // ---- the start screen ----
  const intro = document.getElementById("intro");
  intro.innerHTML = `<div class="box"><h3>You are ${me.name || me.code}'s race engineer</h3>` +
    `<div>${G.raceName} · ${nLaps} laps · starting on ${SHORT[GD.startTyre]}</div><ul>` +
    `<li>Pick the tyres, then press <b>BOX</b> to call your driver in. Press it again to cancel.</li>` +
    `<li>Your car is the dot with the <b>white ring</b>.</li>` +
    (hard ? "<li><b>Hard mode:</b> no hints, and the real car is hidden.</li>"
          : "<li>The faded dot is what really happened. Our strategist will give you hints.</li>") +
    `<li>Dry races need two different tyre types. A red flag gives you a free change.</li>` +
    `<li>Everyone else races exactly as they did in reality. Your result is <b>simulated</b>.</li></ul>` +
    `<button id="startBtn">Start the race</button></div>`;
  intro.style.display = "flex";
  function startRace() {
    started = true;
    intro.style.display = "none";
    setPlaying(true);
  }
  document.getElementById("startBtn").onclick = startRace;
  playBtn.onclick = () => { if (!started) return startRace(); if (time >= END) return; setPlaying(!playing); };
  updateControls();

  // ---- what happens as the race goes on ----
  const said = new Set();
  const once = (key, fn) => { if (!said.has(key)) { said.add(key); fn(); } };
  const nearest = (plan, lap) => plan.filter(s => !s.free).reduce((b, s) => b === null || Math.abs(s.lap - lap) < Math.abs(b - lap) ? s.lap : b, null);
  const red = (D.status || []).find(s => s.kind === "RED");
  let reported = false;
  gameTick = () => {
    if (!started || reported) return;
    const k = curLap();
    for (const s of stops) {                              // a stop has finished: how did it go?
      if (time >= lapEnd(s.lap + 1)) once("done" + s.lap, () => {
        if (s.free) return say("done", `Fresh ${SHORT[s.tyre]} fitted under the red flag.`, s.lap + 2);
        const realLap = nearest(GD.real, s.lap), stratLap = nearest(GD.strategist, s.lap);
        say("done", `Done ✓ ${SHORT[s.tyre]} fitted · rejoined P${position()}.` +
            (realLap ? ` The real team stopped on lap ${realLap}` : " The real team didn't stop around here") +
            (stratLap ? `; our strategist on lap ${stratLap}.` : "."), s.lap + 2);
      });
    }
    if (red && time >= red.start && time < red.end) once("red", () =>
      say("box", "Red flag! The race is stopped. Free tyre change: pick tyres and press BOX."));
    const n = GD.neutral[k - 1];
    const lastStop = Math.max(0, ...stops.filter(s => s.lap < k).map(s => s.lap));
    if (!hard && (n === "SC" || n === "VSC") && !pending() && k - lastStop > 8 && k < nLaps - 3)
      once("sc" + (GD.neutral.slice(0, k).lastIndexOf(null)), () =>
        say("box", `${n === "SC" ? "Safety car" : "Virtual safety car"}! A stop now costs about ` +
                   `${Math.round(G.pitLoss * G.scFactor[n])} s instead of ${Math.round(G.pitLoss)} s.`));
    if (!hard) for (const s of GD.strategist) {
      if (s.free) continue;
      if (k === s.lap - 2) once("h2" + s.lap, () => say("plan", `Strategist: box in 2 laps for ${SHORT[s.tyre]}.`));
      if (k === s.lap && !pending()) once("h0" + s.lap, () => say("plan", `Strategist: I'd box this lap for ${SHORT[s.tyre]}.`));
    }
    if (k === nLaps - 12 && !used(stops)) once("rule", () =>
      say("missed", "Remember: you must use two different dry tyre types before the flag."));
    if (time >= you.sim.finish + 1) { reported = true; setPlaying(false); showReport(); }
    updateControls();
  };

  // ---- your panel ----
  updateGamePanel = () => {
    stratEl.style.display = "block";
    const k = Math.min(nLaps, Math.max(1, curLap())), comp = you.compound[k - 1], age = you.age[k - 1];
    const done = Math.min(nLaps, lastIndexAtOrBefore(you.lapStarts, time));
    let vs = "";
    if (done >= 1) {
      const mine = lapEnd(done);
      const real = done < nLaps ? me.lapStarts[done] : (G.finish.find(f => f.number === me.number) || {}).end;
      if (real !== undefined && real >= 0) {
        const d = real - mine;
        vs = `<div class="count${d < 0 ? " now" : ""}">${Math.abs(d).toFixed(1)} s ${d >= 0 ? "ahead of" : "behind"} the real team</div>`;
      }
    }
    const s = pending();
    const next = GD.strategist.find(x => !x.free && x.lap >= k);
    let html = `<h4>YOU · ${me.code}'S RACE ENGINEER</h4>` +
      `<div class="plan">P${position()} · ${SHORT[comp] || comp}, ${age} lap${age === 1 ? "" : "s"} old</div>` + vs +
      `<div class="muted">${s ? `Stop planned: lap ${s.lap} → ${SHORT[s.tyre]}` : "No stop planned"}` +
      (used(stops) ? " · two tyre types ✓" : " · still need a second tyre type") + `</div>`;
    if (!hard && next) html += `<div class="muted">Strategist would box: lap ${next.lap} → ${SHORT[next.tyre]}</div>`;
    const heard = you.log.slice(-4);
    if (heard.length) html += "<div class='log'>" + heard.map(m => `<div><b>L${m.lap}</b><span>${esc(m.text)}</span></div>`).join("") + "</div>";
    stratEl.innerHTML = html;
  };

  // ---- the report card ----
  function finishPos(T) {
    let pos = 1;
    for (const f of G.finish) if (f.number !== me.number && (f.laps > nLaps || (f.laps === nLaps && f.end < T))) pos++;
    return pos;
  }
  function judgeStop(s, i) {
    const lo = Math.max(2, (stops[i - 1] ? stops[i - 1].lap + 2 : 2)), hi = Math.min(nLaps - 1, stops[i + 1] ? stops[i + 1].lap - 2 : nLaps - 1);
    const base = simulate(stops).finish;
    let bestLap = s.lap, bestT = base;
    for (let L = Math.max(lo, s.lap - 10); L <= Math.min(hi, s.lap + 10); L++) {
      if (L === s.lap || (GD.redLap !== null && L === GD.redLap)) continue;
      const T = simulate(stops.map(x => x === s ? { ...x, lap: L } : x)).finish;
      if (T < bestT) { bestT = T; bestLap = L; }
    }
    const gain = base - bestT, worn = SHORT[you.compound[s.lap - 1]] || "tyres";
    if (gain < 1.0) return { v: "good", label: "✓ Good call", why: "Within a second of the best lap for this stop." };
    const sc = GD.neutral[bestLap - 1] && !GD.neutral[s.lap - 1];
    const why = sc ? `A ${GD.neutral[bestLap - 1] === "SC" ? "safety car" : "virtual safety car"} on lap ${bestLap} made stopping then much cheaper: it would have saved ${gain.toFixed(1)} s.`
      : bestLap > s.lap ? `Your ${worn} still had pace left: stopping on lap ${bestLap} would have saved ${gain.toFixed(1)} s.`
      : `Your ${worn} were fading: stopping on lap ${bestLap} would have saved ${gain.toFixed(1)} s.`;
    return bestLap > s.lap ? { v: "early", label: "≈ Too early", why } : { v: "late", label: "≈ Too late", why };
  }
  const planText = plan => plan.length ? plan.map(s => `L${s.lap} → ${SHORT[s.tyre]}${s.free ? " (red flag)" : ""}`).join(", ") : "No stops";
  function showReport() {
    const T = { you: you.sim.finish, real: simulate(GD.real).finish, strat: simulate(GD.strategist).finish };
    const ok = { you: used(stops), real: true, strat: used(GD.strategist) };
    const pos = { you: ok.you ? finishPos(T.you) : null, real: finishPos(T.real), strat: finishPos(T.strat) };
    const gain = T.real - T.you, places = pos.you === null ? 0 : pos.real - pos.you;
    let headline;
    if (!ok.you) headline = "Rule broken: you never used a second dry tyre type. In a real race, that means disqualification.";
    else if (places > 0) headline = `You beat the real team by ${places} place${places > 1 ? "s" : ""} (${gain.toFixed(1)} s faster).`;
    else if (places < 0) headline = `The real team did better: they finished ${-places} place${places < -1 ? "s" : ""} higher (${(-gain).toFixed(1)} s faster).`;
    else headline = gain >= 0 ? `Same place as the real team, and ${gain.toFixed(1)} s faster.`
                              : `Same place as the real team, but ${(-gain).toFixed(1)} s slower.`;
    const key = `pp-engineer-${G.folder}-${G.driver}`;
    let bestNote = "";
    try {
      const prev = parseFloat(localStorage.getItem(key));
      if (ok.you && (isNaN(prev) || gain > prev)) { localStorage.setItem(key, String(gain)); bestNote = "New personal best on this race!"; }
      else if (!isNaN(prev)) bestNote = `Your best here: ${Math.abs(prev).toFixed(1)} s ${prev >= 0 ? "faster" : "slower"} than the real team.`;
    } catch (e) { /* storage blocked: no personal best */ }
    const rows = stops.filter(s => !s.free).map(s => {
      const j = judgeStop(s, stops.indexOf(s));
      return `<tr><td>Lap ${s.lap}</td><td>${SHORT[s.tyre]}</td><td><span class="chip v-${j.v}">${j.label}</span></td><td>${j.why}</td></tr>`;
    }).join("");
    const card = (who, cls, p, t, plan) => `<div class="${cls}"><span>${who}</span><b>${p === null ? "DSQ" : "P" + p}</b>` +
      `<span>${t}</span><br><span>${planText(plan)}</span></div>`;
    const vsReal = x => Math.abs(x) < 0.05 ? "the real result" : `${Math.abs(x).toFixed(1)} s ${x > 0 ? "faster" : "slower"} than the real team`;
    verdictEl.innerHTML = `<button class="close" id="closeVerdict">Close</button>` +
      `<h3>Race report <span class="sim">Simulated</span></h3>` +
      `<div class="sub">${G.raceName} · you were ${me.code}'s race engineer${hard ? " · hard mode" : ""}</div>` +
      `<div class="big2">${headline}</div>${bestNote ? `<p class="note">${bestNote}</p>` : ""}` +
      `<div class="result">${card("You", "me", pos.you, vsReal(gain), stops)}` +
      `${card("Real team", "", pos.real, "what really happened", GD.real)}` +
      `${card("Our strategist", "", ok.strat ? pos.strat : null, vsReal(T.real - T.strat), GD.strategist)}</div>` +
      (rows ? `<table><tr><th>Your stop</th><th>Tyres</th><th>Verdict</th><th>Why</th></tr>${rows}</table>`
            : `<p>You didn't make a pit stop.</p>`) +
      `<p class="note">How it works: your car does the real driver's lap times with the tyre effect taken out, ` +
      `plus what your tyres cost and your pit stops. Everyone else races exactly as they did, so traffic and ` +
      `battles aren't simulated. If you copy the real team's stops, you get exactly the real result.</p>` +
      `<button id="againBtn">Play again</button>`;
    verdictEl.style.display = "block";
    document.getElementById("closeVerdict").onclick = () => { verdictEl.style.display = "none"; };
    document.getElementById("againBtn").onclick = () => {
      stops = []; said.clear(); you.log = []; reported = false; time = 0; radioTime = 0;
      clearCards(); rebuild(); updateControls();
      verdictEl.style.display = "none";
      setPlaying(true);
    };
  }
}

// ---------- sizing and the main loop ----------
function resize() {
  renderer.setSize(stage.clientWidth, stage.clientHeight);
  camera.aspect = stage.clientWidth / stage.clientHeight;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(stage);
resize();

let lastBoard = 0;
(function frame() {
  const now = performance.now(), dt = (now - lastFrame) / 1000;
  lastFrame = now;
  if (playing) {
    time = Math.min(END, time + dt * parseFloat(speedSel.value));
    if (time >= END) {
      setPlaying(false);
      if (D.strategy && !D.game && !verdictShown) { verdictShown = true; showVerdict(); }
    }
    scrub.value = time / END * 1000;
  }
  checkRadio();
  gameTick();
  const pulse = 1 + 0.4 * (0.5 + 0.5 * Math.sin(now / 160));
  for (const c of cars) {
    c.p = progAt(c, time);
    const f = ((c.p % 1) + 1) % 1;
    const pt = curve.getPointAt(f);
    c.mesh.position.set(pt.x, pt.y + 0.6, pt.z);
    if (c.boxNow) { c.halo.scale.setScalar(pulse); c.halo.material.opacity = 0.4; }
    else { c.halo.scale.setScalar(1); c.halo.material.opacity = c === selected ? 0.3 : 0; }
    c.mesh.visible = (!isOut(c, time) || time - c.out < 30) && !c.hidden;
  }
  if (now - lastBoard > 200) { updateBoard(); updateHud(); updateStrat(); lastBoard = now; }
  if (follow) {
    const move = focusCar().mesh.position.clone().sub(controls.target).multiplyScalar(0.12);
    controls.target.add(move);
    camera.position.add(move);
  }
  controls.update();
  renderer.render(scene, camera);
  for (const c of cars) placeLabel(c.el, c.mesh.position.clone().add(new THREE.Vector3(0, 2.2, 0)), c.showLabel && c.mesh.visible);
  requestAnimationFrame(frame);
})();
</script>
</body></html>
"""
