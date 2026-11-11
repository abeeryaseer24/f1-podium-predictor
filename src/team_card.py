"""The share card for Beat the AI: Constructors.

Separate from share_card.py because team names are two or three words long and that card
shows only a driver's surname, which would turn Red Bull into "BULL".
"""
import json

import streamlit.components.v1 as components

from style import team_info

APP_URL = "f1-podium-predictor1.streamlit.app"
TITLES = {"win": "I BEAT THE AI", "lose": "THE AI GOT ME", "tie": "DEAD LEVEL"}


def team_rows(team_ids, actual=None):
    """[(team id)] -> what the card needs, with a tick or cross when the result is known."""
    rows = []
    for team_id in team_ids or []:
        name, colour = team_info(team_id)
        hit = None if actual is None else (team_id in actual)
        rows.append({"name": name, "color": colour, "hit": hit})
    return rows


def team_card(kind, race, nickname="", you=None, model=None, actual=None, result=None,
              height=620):
    """kind = 'pick' before the race, 'result' after it. you/model/actual = team ids."""
    data = {"kind": kind, "race": race, "nickname": (nickname or "").strip(),
            "url": APP_URL, "result": result,
            "you": team_rows(you, actual if kind == "result" else None),
            "model": team_rows(model, actual if kind == "result" else None),
            "actual": team_rows(actual)}
    components.html(PAGE.replace("__DATA__", json.dumps(data)), height=height)


PAGE = r"""<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@500;700&display=swap" rel="stylesheet">
<style>
body{margin:0;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;gap:10px;background:transparent}
canvas{width:min(100%,380px);height:auto;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.35)}
a{display:inline-block;padding:9px 20px;border-radius:999px;background:#e10600;color:#fff;font-weight:700;font-size:14px;text-decoration:none}
</style></head><body>
<canvas id="c" width="1080" height="1350"></canvas>
<a id="dl" download="my-constructors-pick.png" href="#">Download image</a>
<script>
const D = __DATA__;
const W = 1080, H = 1350, RED = "#e10600";
const TITLES = {win: "I BEAT THE AI", lose: "THE AI GOT ME", tie: "DEAD LEVEL"};
const cv = document.getElementById("c"), g = cv.getContext("2d");
const F = (w, s, fam) => `${w} ${s}px ${fam === "i" ? "Inter, system-ui, sans-serif" : "'Saira Condensed', 'Arial Narrow', sans-serif"}`;

function fit(text, max, weight, size, fam) {
  let s = size; g.font = F(weight, s, fam);
  while (g.measureText(text).width > max && s > 16) { s -= 2; g.font = F(weight, s, fam); }
  return s;
}
function rr(x, y, w, h, r, fill) { g.beginPath(); g.roundRect(x, y, w, h, r); g.fillStyle = fill; g.fill(); }

// background
g.fillStyle = "#0b0b10"; g.fillRect(0, 0, W, H);
const glow = g.createRadialGradient(150, 130, 20, 150, 130, 700);
glow.addColorStop(0, "rgba(225,6,0,.30)"); glow.addColorStop(1, "rgba(225,6,0,0)");
g.fillStyle = glow; g.fillRect(0, 0, W, H);
g.globalAlpha = .07;
for (let y = 0; y < 230; y += 46) for (let x = W - 460; x < W; x += 46) {
  g.fillStyle = ((x + y) / 46) % 2 === 0 ? "#fff" : "transparent"; g.fillRect(x, y, 46, 46);
}
g.globalAlpha = 1;

// heading
g.textAlign = "left";
g.font = F(800, 34, "s"); g.fillStyle = RED; g.fillText("PODIUM PREDICTOR", 72, 112);
g.font = F(500, 26, "i"); g.fillStyle = "rgba(255,255,255,.55)";
g.fillText("Beat the AI · Constructors", 72, 150);

const head = D.kind === "pick" ? "MY TOP THREE TEAMS" : (TITLES[D.result] || "MY RESULT");
g.fillStyle = "#fff"; fit(head, W - 144, 800, 104, "s"); g.fillText(head, 72, 300);
g.font = F(500, 38, "i"); g.fillStyle = "rgba(255,255,255,.75)";
fit(D.race, W - 144, 500, 38, "i"); g.fillText(D.race, 72, 360);

// one column of three teams
function column(title, rows, x, w, top) {
  g.textAlign = "left";
  g.font = F(700, 26, "i"); g.fillStyle = "rgba(255,255,255,.6)";
  g.fillText(title.toUpperCase(), x, top);
  rows.slice(0, 3).forEach((p, i) => {
    const y = top + 24 + i * 112, h = 96;
    rr(x, y, w, h, 16, "#15151e");
    rr(x, y, 10, h, 5, p.color);
    g.fillStyle = "rgba(255,255,255,.45)"; g.font = F(800, 40, "s");
    g.fillText(`P${i + 1}`, x + 30, y + 60);
    g.fillStyle = "#fff";
    const name = p.name.toUpperCase();
    fit(name, w - 150, 800, 46, "s");
    g.fillText(name, x + 104, y + 62);
    if (p.hit !== null && p.hit !== undefined) {
      g.font = F(800, 42, "i"); g.fillStyle = p.hit ? "#1fa855" : "#f0443a";
      g.fillText(p.hit ? "✓" : "✗", x + w - 54, y + 62);
    }
  });
}

if (D.kind === "pick") {
  column("My pick", D.you, 72, W - 144, 470);
  if (D.nickname) {
    g.textAlign = "center"; g.font = F(500, 34, "i"); g.fillStyle = "rgba(255,255,255,.7)";
    g.fillText(`Picked by ${D.nickname}`, W / 2, 880);
  }
} else {
  const w = (W - 144 - 40) / 2;
  column("You", D.you, 72, w, 470);
  column(D.model.length ? "Our model" : "Actual", D.model.length ? D.model : D.actual,
         72 + w + 40, w, 470);
  if (D.actual.length && D.model.length) {
    column("Actual result", D.actual, 72, W - 144, 850);
  }
}

// footer
g.textAlign = "left";
g.fillStyle = "#fff"; g.font = F(800, 40, "s");
g.fillText("THINK YOU CAN BEAT THE AI?", 72, H - 92);
g.fillStyle = "rgba(255,255,255,.6)"; g.font = F(500, 28, "i");
g.fillText(D.url, 72, H - 52);

document.getElementById("dl").href = cv.toDataURL("image/png");
</script></body></html>"""
