"""Replay Commentary (C4): event-driven commentary over the Pit Wall replay, with no AI service.

Every fifth of a second the replay compares the race with how it was a moment ago and turns what changed
into events: an overtake in the top ten (not a pit-stop swap), a new leader, a car into the pits, a
retirement, a safety car / VSC / red flag and the restart, a gap closing to under a second, the last lap,
the finish. Each event picks a line from a phrase bank (never the same one twice in a row), and a queue
with priorities and a cooldown keeps it from talking over itself or narrating stale news. Scrubbing the
replay resets it quietly. Lines show on screen and, if the visitor wants, the browser's own speech
(Web Speech API, free and offline in most browsers) reads them out.

COMMENTARY_JS is injected into the Pit Wall template (pitwall3d.py).
"""

COMMENTARY_BUTTON = '<button id="commBtn" title="Spoken commentary">🎙 Commentary</button>'
COMMENTARY_CSS = """
  #comm { position: absolute; left: 50%; bottom: 54px; transform: translateX(-50%); max-width: 78%; padding: 8px 14px;
          border-radius: 12px; background: var(--panel); border: 1px solid var(--border); color: var(--text);
          font: 600 14px Inter, system-ui, sans-serif; text-align: center; display: none; z-index: 4; }
"""
COMMENTARY_DIV = '<div id="comm"></div>'

COMMENTARY_JS = r"""
// ---------- replay commentary: events -> lines -> screen and voice ----------
const LINES = {
  start: ["And they're away!", "The race is on!", "Green light, and the field charges to turn one."],
  overtake: ["{a} is through on {b} for P{p}!", "Move made: {a} passes {b}, up to P{p}.",
             "{a} gets the job done on {b}. That's P{p}.", "And {a} is past {b}!", "{a} makes it stick on {b} for P{p}."],
  lead: ["{a} takes the lead from {b}!", "New leader: {a}!", "{a} is in front now, {b} has lost the lead!"],
  pit: ["{a} peels into the pit lane.", "{a} is in for fresh tyres.", "Box, box for {a}.", "{a} dives into the pits from P{p}."],
  out: ["{a} is out of the race.", "Trouble for {a}: that's a retirement.", "And that's the end of the race for {a}."],
  SC: ["Safety car! The gaps will be wiped out.", "The safety car is out on track.", "Safety car deployed: a chance for cheap pit stops."],
  VSC: ["Virtual safety car: everyone slows to a set pace.", "VSC deployed. Watch for anyone diving into the pits."],
  RED: ["Red flag! The race is stopped.", "Red flag: the cars head back to the pit lane."],
  green: ["And we're racing again!", "Green flag: back to full speed.", "Restart! Here we go again."],
  closing: ["{a} is closing on {b}, under a second now.", "{a} has {b} in their sights.", "Less than a second between {b} and {a}."],
  last: ["Final lap! {a} leads.", "One lap to go, and {a} is in front."],
  win: ["Chequered flag! {a} wins the {race}!", "{a} takes victory in the {race}!", "And it's {a} who wins it!"],
};
const PRIORITY = { win: 9, RED: 8, SC: 8, VSC: 7, lead: 7, out: 6, green: 6, last: 6, start: 6, overtake: 5, pit: 3, closing: 2 };
const commEl = document.getElementById("comm"), commBtn = document.getElementById("commBtn");
const canSpeak = "speechSynthesis" in window;
let commOn = false, lastLine = {}, queue = [], busyUntil = 0, prev = null, lastTime = 0, saidLast = false, saidWin = false;
let history = [], pairSaid = {};          // recent running orders, and when each pair of cars was last called
const HOLD = 4, PAIR_GAP = 90, SETTLE = 40;     // s of replay: a pass must hold; the same pair waits; the start settles
commBtn.onclick = () => {
  commOn = !commOn; commBtn.classList.toggle("on", commOn);
  if (!commOn) { if (canSpeak) speechSynthesis.cancel(); commEl.style.display = "none"; queue = []; }
  else say(canSpeak ? "Commentary on." : "Commentary on (this browser can't speak, so lines show here).", true);
};
const surname = c => (c.name || c.code).split(" ").slice(-1)[0] || c.code;
function line(kind, v) {
  const opts = LINES[kind];
  let i = Math.floor(Math.random() * opts.length);
  if (opts.length > 1 && i === lastLine[kind]) i = (i + 1) % opts.length;
  lastLine[kind] = i;
  return opts[i].replace("{a}", v.a || "").replace("{b}", v.b || "").replace("{p}", v.p || "").replace("{race}", D.race_name || "race");
}
function push(kind, v) { queue.push({ kind, text: line(kind, v), at: performance.now(), pr: PRIORITY[kind] || 1 }); }
function say(text, force) {
  commEl.textContent = text; commEl.style.display = "block";
  busyUntil = performance.now() + Math.max(2600, text.length * 65);
  if (canSpeak) {
    if (force) speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.08; u.pitch = 1.0;
    const en = speechSynthesis.getVoices().find(x => /^en(-|_)/i.test(x.lang));
    if (en) u.voice = en;
    speechSynthesis.speak(u);
  }
}
function snapshot() {
  const running = order.filter(c => !isOut(c, time));
  return { time, codes: running.map(c => c.code), pos: Object.fromEntries(running.map((c, i) => [c.code, i])),
           out: new Set(cars.filter(c => isOut(c, time)).map(c => c.code)),
           pits: Object.fromEntries(cars.map(c => [c.code, c.pits.filter(t => t <= time).length])),
           status: (D.status.find(s => time >= s.start && time < s.end) || {}).kind || null };
}
const inPitNow = c => c.pits.some(t => time >= t - 20 && time - t < 30);   // slowing for the pit lane counts too
function commentate() {
  if (!commOn) { prev = null; return; }
  const now = snapshot();
  if (!prev || Math.abs(time - lastTime) > 20 || time < lastTime) {   // first look, or the visitor scrubbed
    prev = now; lastTime = time; queue = []; history = []; pairSaid = {};
    saidLast = order[0] && order[0].p >= D.laps - 1; saidWin = order[0] && order[0].p >= D.laps;
    return;
  }
  lastTime = time;
  if (!playing) { prev = now; return; }
  const byCode = Object.fromEntries(cars.map(c => [c.code, c]));
  if (prev.time <= 2 && time > 2) push("start", {});
  if (now.status !== prev.status) {
    if (now.status) push(now.status, {});
    else if (prev.status) push("green", {});
  }
  for (const code of now.out) if (!saidWin && !prev.out.has(code)) push("out", { a: surname(byCode[code]) });
  for (const c of cars) if (!saidWin && (now.pits[c.code] || 0) > (prev.pits[c.code] || 0) && !now.out.has(c.code))
    push("pit", { a: surname(c), p: (now.pos[c.code] ?? 0) + 1 });
  // passes: the new order must have held for HOLD seconds (side-by-side cars and noisy positions flicker),
  // and neither car may be in the pits (a pit-stop swap isn't a pass)
  history.push({ t: time, pos: now.pos, lead: now.codes[0] });
  while (history.length && history[0].t < time - 3 * HOLD) history.shift();
  const then = history.find(h => h.t >= time - 2 * HOLD), mid = history.find(h => h.t >= time - HOLD);
  const quiet = now.status || time < SETTLE || saidWin || !order[0] || order[0].p < 1;   // lap 1 positions are unreliable
  if (!quiet && then && mid && then !== mid) {
    if (now.codes[0] && mid.lead === now.codes[0] && then.lead && then.lead !== now.codes[0]) {
      const a = byCode[now.codes[0]], b = byCode[then.lead], key = [a.code, b.code].sort().join();
      if (!inPitNow(a) && !inPitNow(b) && !(time - (pairSaid[key] ?? -1e9) < PAIR_GAP)) {
        pairSaid[key] = time; push("lead", { a: surname(a), b: surname(b) });
      }
    } else {
      for (let i = 1; i < Math.min(10, now.codes.length); i++) {
        const code = now.codes[i], a = byCode[code];
        for (const other of now.codes.slice(i + 1, 12)) {        // cars now behind a that were ahead of it before
          const b = byCode[other], key = [code, other].sort().join();
          if (then.pos[code] > then.pos[other] && mid.pos[code] < mid.pos[other] && !inPitNow(a) && !inPitNow(b)
              && !(time - (pairSaid[key] ?? -1e9) < PAIR_GAP)) {
            pairSaid[key] = time; push("overtake", { a: surname(a), b: surname(b), p: i + 1 });
            break;
          }
        }
      }
    }
  }
  // a gap closing to under a second (top ten, now and then)
  if (!quiet && Math.random() < 0.08) {
    for (let i = 1; i < Math.min(10, order.length); i++) {
      const a = order[i], b = order[i - 1];
      if (isOut(a, time) || isOut(b, time) || inPitNow(a) || inPitNow(b)) continue;
      const k = firstIndexAtOrAbove(b.prog, a.p), gap = time - k;
      if (gap > 0.2 && gap < 1.0) { push("closing", { a: surname(a), b: surname(b) }); break; }
    }
  }
  const leader = order[0];
  if (leader && !saidLast && leader.p >= D.laps - 1 && leader.p < D.laps) { saidLast = true; push("last", { a: surname(leader) }); }
  if (leader && !saidWin && leader.p >= D.laps - 0.002) { saidWin = true; push("win", { a: surname(leader) }); }
  prev = now;
  // speak the most important fresh line when free
  const t = performance.now();
  queue = queue.filter(q => t - q.at < 7000);
  if (t >= busyUntil && queue.length) {
    queue.sort((x, y) => y.pr - x.pr || x.at - y.at);
    say(queue.shift().text);
  } else if (t >= busyUntil + 2500) commEl.style.display = "none";
}
"""
