"""Time of day and rain for the 3D views (sim3d.py lap views and the Pit Wall replay).

Python decides the starting conditions:
  time_of_day(race_name)   "night" for the races run after dark, "dusk" for Abu Dhabi, else "day"
  rain_timeline(folder)    [[seconds from the replay start, raining 0/1], ...] from the race's own
                           weather feed (OpenF1's rainfall flag, about once a minute)
and ENV_JS draws them inside the Three.js page:
  Day / Dusk / Night       the sky, fog and ground change colour; at night floodlights run along both
                           edges of the track
  Rain                     short streaks fall round the camera and a wet film covers the road
The visitor can change both from the buttons on the 3D view. Everything is drawn with unlit
materials like the rest of the 3D kit, so it costs almost nothing on a phone.
"""
import json
from pathlib import Path

import pandas as pd

RACES_DIR = Path(__file__).resolve().parent.parent / "data" / "races"

NIGHT = ("Bahrain", "Saudi", "Singapore", "Las Vegas", "Qatar")
DUSK = ("Abu Dhabi",)


def time_of_day(race_name):
    name = str(race_name)
    if any(k in name for k in NIGHT):
        return "night"
    if any(k in name for k in DUSK):
        return "dusk"
    return "day"


def rain_timeline(folder, base=0.0, start=None, end=None):
    """When it was raining, as [[t - base, 0 or 1], ...], only the changes. Empty if it stayed dry."""
    path = RACES_DIR / folder / "weather.parquet"
    if not path.exists():
        return []
    w = pd.read_parquet(path, columns=["t", "rainfall"]).sort_values("t")
    if start is not None:
        w = w[w["t"] >= start - 120]
    if end is not None:
        w = w[w["t"] <= end]
    wet = (w["rainfall"].fillna(0) > 0).astype(int)
    if not wet.any():
        return []
    changes = wet.ne(wet.shift())
    return [[round(float(t - base), 1), int(r)] for t, r in zip(w["t"][changes], wet[changes])]


def env_for(folder):
    """Starting conditions for a circuit's simulator views (the simulator is a dry-weather model)."""
    info = json.loads((RACES_DIR / folder / "info.json").read_text(encoding="utf-8"))
    return {"tod": time_of_day(info["race_name"]), "rain": False}


# The buttons the templates add to their #views bar.
ENV_BUTTONS = ('<select id="tod" aria-label="Time of day"><option value="day">Day</option>'
               '<option value="dusk">Dusk</option><option value="night">Night</option></select>'
               '<button id="rainBtn">Rain</button>')

# makeWeather({scene, ground, grid, edges: [leftPoints, rightPoints], road: geometry, T, target})
# returns { step(dt), setTod(name), setRain(on) }. `target` is a THREE.Vector3 the rain follows.
ENV_JS = r"""
function makeWeather(o) {
  const SKY = {
    day: { bg: o.T.bg, ground: o.T.ground, grid: o.T.grid },
    dusk: { bg: "#2b1d33", ground: "#1a1320", grid: "#2e2333" },
    night: { bg: "#04050a", ground: "#07080e", grid: "#12141d" },
  };
  // floodlights: a warm line along both edges and a row of lamps outside the track
  const lights = new THREE.Group();
  const glow = new THREE.LineBasicMaterial({ color: "#ffe2a0", transparent: true, opacity: 0.85 });
  for (const e of o.edges) lights.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(e), glow));
  const lamps = [], e0 = o.edges[0], every = Math.max(1, Math.round(e0.length / 90));
  for (let i = 0; i < e0.length; i += every) lamps.push(e0[i].clone().add(new THREE.Vector3(0, 1.4, 0)));
  lights.add(new THREE.Points(new THREE.BufferGeometry().setFromPoints(lamps),
    new THREE.PointsMaterial({ color: "#fff3c4", size: 0.3, sizeAttenuation: true })));
  lights.visible = false;
  o.scene.add(lights);
  // the wet film over the road
  const film = new THREE.Mesh(o.road, new THREE.MeshBasicMaterial({ color: "#6f86b0", transparent: true,
    opacity: 0.28, depthWrite: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2 }));
  film.visible = false;
  o.scene.add(film);
  // rain: short falling streaks in a box round the target
  const R = 1600, BOX = 70, H = 34, off = new Float32Array(R * 3), pos = new Float32Array(R * 6);
  for (let i = 0; i < R; i++) { off[3*i] = (Math.random() - .5) * BOX; off[3*i+1] = Math.random() * H; off[3*i+2] = (Math.random() - .5) * BOX; }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const rain = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: "#a9bddf", transparent: true, opacity: 0.5 }));
  rain.frustumCulled = false; rain.visible = false;
  o.scene.add(rain);
  let tod = "day", raining = false;
  function paint() {
    const sky = SKY[tod];
    o.scene.background = new THREE.Color(raining && tod === "day" ? (o.T.bg === "#0b0b10" ? "#141820" : "#dfe3ea") : sky.bg);
    if (o.scene.fog) { o.scene.fog.color = o.scene.background.clone(); }
    o.ground.material.color.set(sky.ground);
    const g = o.grid.material; (Array.isArray(g) ? g : [g]).forEach(m => m.color.set(sky.grid));
    lights.visible = tod === "night";
    film.visible = raining; rain.visible = raining;
  }
  return {
    setTod(name) { tod = name; paint(); },
    setRain(on) { raining = !!on; paint(); },
    get raining() { return raining; },
    step(dt) {
      if (!raining) return;
      const c = o.target(), fall = 38 * Math.min(dt, 0.05);
      for (let i = 0; i < R; i++) {
        off[3*i+1] -= fall;
        if (off[3*i+1] < 0) { off[3*i+1] += H; off[3*i] = (Math.random() - .5) * BOX; off[3*i+2] = (Math.random() - .5) * BOX; }
        const x = c.x + off[3*i], y = off[3*i+1] + Math.max(c.y - 4, 0), z = c.z + off[3*i+2];
        pos[6*i] = x; pos[6*i+1] = y; pos[6*i+2] = z;
        pos[6*i+3] = x + 0.12; pos[6*i+4] = y + 1.1; pos[6*i+5] = z;
      }
      geo.attributes.position.needsUpdate = true;
    },
  };
}
"""
