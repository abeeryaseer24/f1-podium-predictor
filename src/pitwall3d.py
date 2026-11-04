"""Pit Wall 3D: the race replay plus the strategist on screen
(team radio for the driver you follow, strategist panel, planned-stop badges and the verdict)."""
import json

import streamlit.components.v1 as components

from track3d import THREE_URL


def pit_wall_view(data, track, strategy=None, dark=True, height=720):
    payload = dict(data, dark=dark, strategy=strategy,
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
    </div>
    <div id="controls">
      <button id="play">Play</button>
      <select id="speed" aria-label="Replay speed">
        <option value="1">1×</option><option value="5">5×</option><option value="10" selected>10×</option>
        <option value="30">30×</option><option value="60">60×</option>
      </select>
      <select id="jump" aria-label="Jump to lap"></select>
      <input id="scrub" type="range" min="0" max="1000" value="0" aria-label="Position in the race">
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
const END = D.duration;
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
tickerEl.style.right = PLANS ? "274px" : "12px";
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
  const running = cars.filter(c => !isOut(c, time)).sort((a, b) => b.p - a.p);
  const retired = cars.filter(c => isOut(c, time));
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
    const gap = out ? "OUT" : inPit ? "<span class='pit'>PIT</span>" : gapText(c, leader);
    const plan = out ? null : planFor(c, time);
    c.boxNow = !!plan && plan.pit !== null && plan.pit === plan.onLap && !inPit;
    const badge = !plan || plan.pit === null ? ""
      : c.boxNow ? "<span class='badge box' title='Box this lap'>BOX</span>"
      : `<span class='badge' title='Planned stop'>L${plan.pit}</span>`;
    c.showLabel = i < 3 || c === selected;
    html += `<div class="row${c === selected ? " sel" : ""}" data-n="${c.number}">` +
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
    `and team radio, so matching every stop isn't expected.</p>` +
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
      if (D.strategy && !verdictShown) { verdictShown = true; showVerdict(); }
    }
    scrub.value = time / END * 1000;
  }
  checkRadio();
  const pulse = 1 + 0.4 * (0.5 + 0.5 * Math.sin(now / 160));
  for (const c of cars) {
    c.p = progAt(c, time);
    const f = ((c.p % 1) + 1) % 1;
    const pt = curve.getPointAt(f);
    c.mesh.position.set(pt.x, pt.y + 0.6, pt.z);
    if (c.boxNow) { c.halo.scale.setScalar(pulse); c.halo.material.opacity = 0.4; }
    else { c.halo.scale.setScalar(1); c.halo.material.opacity = c === selected ? 0.3 : 0; }
    c.mesh.visible = !isOut(c, time) || time - c.out < 30;
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
