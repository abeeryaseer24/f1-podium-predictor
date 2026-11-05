"""Share cards for Beat the AI: a picture drawn in the visitor's browser, with a download button.

  pick card:   my podium pick for the next race
  result card: my pick, our model's pick and the real podium, with who won
"""
import json

import streamlit.components.v1 as components

from style import team_info

APP_URL = "f1-podium-predictor1.streamlit.app"


def card_data(kind, race, nickname="", you=None, model=None, actual=None, result=None):
    """Everything the card needs. you/model/actual = lists of (name, team_id)."""
    people = lambda rows: [{"name": n, "color": team_info(t)[1]} for n, t in (rows or [])]
    return {"kind": kind, "race": race, "nickname": nickname, "url": APP_URL,
            "you": people(you), "model": people(model), "actual": people(actual), "result": result}


def share_card(data, height=560):
    components.html(PAGE.replace("__DATA__", json.dumps(data)), height=height)


PAGE = r"""<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@500;700&display=swap" rel="stylesheet">
<style>
body{margin:0;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;gap:10px;background:transparent}
canvas{width:min(100%,380px);height:auto;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.35)}
a{display:inline-block;padding:9px 20px;border-radius:999px;background:#e10600;color:#fff;font-weight:700;font-size:14px;text-decoration:none}
</style></head><body>
<canvas id="c" width="1080" height="1350"></canvas>
<a id="dl" download="my-podium-pick.png" href="#">Download image</a>
<script>
const D = __DATA__;
const W = 1080, H = 1350, RED = "#e10600";
const cv = document.getElementById("c"), g = cv.getContext("2d");
const F = (w, s, fam) => `${w} ${s}px ${fam === "i" ? "Inter, system-ui, sans-serif" : "'Saira Condensed', 'Arial Narrow', sans-serif"}`;

function fit(text, max, weight, size, fam) {           // shrink text until it fits
  let s = size; g.font = F(weight, s, fam);
  while (g.measureText(text).width > max && s > 18) { s -= 2; g.font = F(weight, s, fam); }
}
function rr(x, y, w, h, r, fill) { g.beginPath(); g.roundRect(x, y, w, h, r); g.fillStyle = fill; g.fill(); }

function frame() {
  const bg = g.createLinearGradient(0, 0, W, H); bg.addColorStop(0, "#15151e"); bg.addColorStop(1, "#0b0b10");
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  const glow = g.createRadialGradient(120, 80, 10, 120, 80, 620);
  glow.addColorStop(0, "rgba(225,6,0,.35)"); glow.addColorStop(1, "rgba(225,6,0,0)");
  g.fillStyle = glow; g.fillRect(0, 0, W, H);
  g.save(); g.globalAlpha = .07; g.fillStyle = "#fff";                 // chequered corner
  for (let i = 0; i < 9; i++) for (let j = 0; j < 5; j++) if ((i + j) % 2 === 0) g.fillRect(W - 360 + i * 40, j * 40, 40, 40);
  g.restore();
  g.fillStyle = RED; g.font = F(800, 34); g.fillText("PODIUM PREDICTOR", 72, 112);
  g.fillStyle = "rgba(255,255,255,.55)"; g.font = F(500, 26, "i"); g.fillText("Beat the AI", 72, 146);
  g.fillStyle = "rgba(255,255,255,.12)"; g.fillRect(72, H - 150, W - 144, 2);
  g.fillStyle = "#fff"; g.font = F(800, 40); g.fillText("THINK YOU CAN BEAT THE AI?", 72, H - 92);
  g.fillStyle = "rgba(255,255,255,.6)"; g.font = F(500, 28, "i"); g.fillText(D.url, 72, H - 52);
}

function pickCard() {
  g.fillStyle = "#fff"; fit("MY PODIUM PICK", W - 144, 800, 120); g.fillText("MY PODIUM PICK", 72, 300);
  g.fillStyle = "rgba(255,255,255,.75)"; fit(D.race, W - 144, 500, 40, "i"); g.fillText(D.race, 72, 362);
  // the podium: P2 left, P1 middle, P3 right, names above each block (like the app)
  const base = 1120, w = 290, gap = 20, x0 = (W - (3 * w + 2 * gap)) / 2;
  const spots = [{pos: 2, h: 380, fill: "#b9bcc4", ink: "#15151e"},
                 {pos: 1, h: 490, fill: "#e10600", ink: "#ffffff"},
                 {pos: 3, h: 300, fill: "#b5743c", ink: "#15151e"}];
  spots.forEach((sp, i) => {
    const p = D.you[sp.pos - 1]; if (!p) return;
    const x = x0 + i * (w + gap), top = base - sp.h;
    g.save(); g.beginPath(); g.roundRect(x, top, w, sp.h, [18, 18, 0, 0]); g.fillStyle = sp.fill; g.fill(); g.restore();
    rr(x, top, w, 14, [18, 18, 0, 0], p.color);
    g.fillStyle = sp.ink; g.font = F(800, 110); const t = `P${sp.pos}`;
    g.fillText(t, x + (w - g.measureText(t).width) / 2, top + 130);
    const parts = p.name.split(" "), last = parts.slice(-1)[0].toUpperCase(), first = parts.slice(0, -1).join(" ");
    g.fillStyle = "#fff"; fit(last, w - 10, 800, 64);
    g.fillText(last, x + (w - g.measureText(last).width) / 2, top - 30);
    if (first) { g.fillStyle = "rgba(255,255,255,.6)"; g.font = F(500, 26, "i");
      g.fillText(first, x + (w - g.measureText(first).width) / 2, top - 100); }
    rr(x + w / 2 - 30, top - 18 + 4, 60, 6, 3, p.color);
  });
  g.fillStyle = "rgba(255,255,255,.12)"; g.fillRect(72, base, W - 144, 2);
  if (D.nickname) { g.fillStyle = "rgba(255,255,255,.6)"; g.font = F(500, 30, "i");
    const t = `Picked by ${D.nickname}`; g.fillText(t, (W - g.measureText(t).width) / 2, base + 60); }
}

function column(x, w, title, rows, marks) {
  g.fillStyle = "rgba(255,255,255,.6)"; g.font = F(700, 26, "i"); g.fillText(title.toUpperCase(), x, 470);
  rows.forEach((p, i) => {
    const y = 500 + i * 150;
    rr(x, y, w, 130, 18, "rgba(255,255,255,.06)"); rr(x, y, 10, 130, 5, p.color);
    g.fillStyle = "rgba(255,255,255,.45)"; g.font = F(800, 44); g.fillText(`P${i + 1}`, x + 26, y + 58);
    g.fillStyle = "#fff"; fit(p.name.split(" ").slice(-1)[0].toUpperCase(), w - 40, 800, 54); g.fillText(p.name.split(" ").slice(-1)[0].toUpperCase(), x + 26, y + 112);
    if (marks) {
      const hit = marks[i]; g.fillStyle = hit ? "#1fa855" : "#f0443a"; g.font = F(800, 46);
      g.fillText(hit ? "✓" : "✗", x + w - 52, y + 58);
    }
  });
}

function resultCard() {
  const titles = {win: "I BEAT THE AI", lose: "THE AI WON THIS TIME", tie: "DEAD LEVEL WITH THE AI"};
  g.fillStyle = D.result === "win" ? "#fff" : "#fff"; fit(titles[D.result] || "MY RESULT", W - 144, 800, 110);
  g.fillText(titles[D.result] || "MY RESULT", 72, 300);
  g.fillStyle = "rgba(255,255,255,.75)"; fit(D.race, W - 144, 500, 40, "i"); g.fillText(D.race, 72, 362);
  const names = D.actual.map(p => p.name);
  const marks = rows => rows.map(p => names.includes(p.name));
  const w = (W - 144 - 2 * 24) / 3;
  column(72, w, D.nickname ? D.nickname : "Me", D.you, marks(D.you));
  column(72 + w + 24, w, "Our AI", D.model, marks(D.model));
  column(72 + 2 * (w + 24), w, "Real result", D.actual, null);
  if (D.result === "win") { rr(72, 980, W - 144, 90, 45, "rgba(31,168,85,.18)"); g.fillStyle = "#1fa855"; }
  else if (D.result === "lose") { rr(72, 980, W - 144, 90, 45, "rgba(225,6,0,.16)"); g.fillStyle = "#f0443a"; }
  else { rr(72, 980, W - 144, 90, 45, "rgba(255,255,255,.08)"); g.fillStyle = "#fff"; }
  const line = {win: "Beat the model on podium picks", lose: "The model was just better", tie: "Same score as the model"}[D.result] || "";
  g.font = F(800, 46); const tw = g.measureText(line).width; g.fillText(line, (W - tw) / 2, 1040);
}

function draw() {
  frame();
  D.kind === "result" ? resultCard() : pickCard();
  const a = document.getElementById("dl");
  a.href = cv.toDataURL("image/png");
  a.download = D.kind === "result" ? "my-result-vs-the-ai.png" : "my-podium-pick.png";
}
Promise.race([Promise.all([document.fonts.load(F(800, 40)), document.fonts.load(F(500, 20, "i"))]),
              new Promise(r => setTimeout(r, 1500))]).then(draw, draw);
</script></body></html>"""
