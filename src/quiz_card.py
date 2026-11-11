"""The share card for the F1 Quiz: a picture drawn in the visitor's browser, with a
download button. Separate from share_card.py so the Beat the AI card is left alone.
"""
import json

import streamlit.components.v1 as components

APP_URL = "f1-podium-predictor1.streamlit.app"


def quiz_card(score, total, era, marks, verdict, height=520):
    """marks = a list of True/False, one per question, in the order they were answered."""
    data = {"score": score, "total": total, "era": era, "marks": list(marks),
            "verdict": verdict, "url": APP_URL}
    components.html(PAGE.replace("__DATA__", json.dumps(data)), height=height)


PAGE = r"""<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600;800&family=Inter:wght@500;700&display=swap" rel="stylesheet">
<style>
body{margin:0;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;gap:10px;background:transparent}
canvas{width:min(100%,360px);height:auto;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.35)}
a{display:inline-block;padding:9px 20px;border-radius:999px;background:#e10600;color:#fff;font-weight:700;font-size:14px;text-decoration:none}
</style></head><body>
<canvas id="c" width="1080" height="1080"></canvas>
<a id="dl" download="my-f1-quiz-score.png" href="#">Download image</a>
<script>
const D = __DATA__;
const W = 1080, H = 1080, RED = "#e10600";
const cv = document.getElementById("c"), g = cv.getContext("2d");
const F = (w, s, fam) => `${w} ${s}px ${fam === "i" ? "Inter, system-ui, sans-serif" : "'Saira Condensed', 'Arial Narrow', sans-serif"}`;

function rr(x, y, w, h, r, fill) { g.beginPath(); g.roundRect(x, y, w, h, r); g.fillStyle = fill; g.fill(); }
function fit(text, max, weight, size, fam) {
  let s = size; g.font = F(weight, s, fam);
  while (g.measureText(text).width > max && s > 16) { s -= 2; g.font = F(weight, s, fam); }
}

// background
g.fillStyle = "#0b0b10"; g.fillRect(0, 0, W, H);
const glow = g.createRadialGradient(140, 120, 20, 140, 120, 620);
glow.addColorStop(0, "rgba(225,6,0,.30)"); glow.addColorStop(1, "rgba(225,6,0,0)");
g.fillStyle = glow; g.fillRect(0, 0, W, H);
// chequered corner
g.globalAlpha = .07;
for (let y = 0; y < 220; y += 44) for (let x = W - 440; x < W; x += 44) {
  g.fillStyle = ((x + y) / 44) % 2 === 0 ? "#fff" : "transparent"; g.fillRect(x, y, 44, 44);
}
g.globalAlpha = 1;

// title
g.textAlign = "left";
g.font = F(800, 34, "s"); g.fillStyle = RED;
g.fillText("PODIUM PREDICTOR", 80, 110);
g.font = F(800, 78, "s"); g.fillStyle = "#f5f5f7";
g.fillText("F1 QUIZ", 80, 196);

// the score
rr(80, 250, W - 160, 300, 28, "#15151e");
g.textAlign = "center";
g.font = F(800, 190, "s"); g.fillStyle = RED;
g.fillText(`${D.score}/${D.total}`, W / 2, 430);
g.font = F(500, 34, "i"); g.fillStyle = "#a3a3b2";
g.fillText("questions right", W / 2, 490);

// verdict
fit(D.verdict, W - 200, 800, 54, "s");
g.fillStyle = "#f5f5f7";
g.fillText(D.verdict, W / 2, 630);

// one dot per question
const n = D.marks.length, gap = 18, size = Math.min(62, (W - 200 - gap * (n - 1)) / Math.max(n, 1));
let x = (W - (size * n + gap * (n - 1))) / 2;
for (const hit of D.marks) {
  rr(x, 690, size, size, 14, hit ? "#1fa855" : "#3a2126");
  g.font = F(700, size * 0.6, "i");
  g.fillStyle = hit ? "#fff" : "#f0443a";
  g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(hit ? "✓" : "✗", x + size / 2, 690 + size / 2 + 2);
  g.textBaseline = "alphabetic";
  x += size + gap;
}

// era and footer
g.textAlign = "center";
g.font = F(500, 32, "i"); g.fillStyle = "#a3a3b2";
g.fillText(D.era, W / 2, 840);
rr(80, 900, W - 160, 2, 1, "#2c2c3a");
g.font = F(700, 34, "i"); g.fillStyle = "#f5f5f7";
g.fillText("Think you can beat it?", W / 2, 968);
g.font = F(500, 30, "i"); g.fillStyle = RED;
g.fillText(D.url, W / 2, 1016);

document.getElementById("dl").href = cv.toDataURL("image/png");
</script></body></html>"""
