"""The Engineering Academy: the course engine.

A chapter is a plain dict (see academy_content/), so writing a new one never means touching
this file:

  {"id": "1.3", "title": "...", "summary": "one line",
   "basics": md, "engineer": md, "deep": md,     # the three depths; LaTeX works with $...$
   "widget": callable or None,                    # a live demo, from academy_widgets.py
   "data": [("Page title", "what to look for")],  # where to see it in the real app
   "terms": ["downforce", ...],                   # keys of GLOSSARY
   "quiz": [(question, [options], right_index, why)],
   "sources": ["..."]}

Every depth builds on the one before it: Engineer shows the Basics text and then adds to
it, Deep dive shows all three. So nobody misses the plain explanation.

Progress (chapters read, quiz scores) lives in st.session_state, so it lasts for the visit.
"""
import html

import streamlit as st

from ui_kit import chips, section

DEPTHS = ["Basics", "Engineer", "Deep dive"]
DEPTH_HELP = {
    "Basics": "No maths. What it is and why it matters.",
    "Engineer": "Adds the equations and real numbers.",
    "Deep dive": "Adds derivations, limits of the models and where to read more.",
}

# The whole course. Chapters with content are listed in academy_content; the rest show as
# coming soon on the Academy page, so visitors can see where the course is going.
CURRICULUM = [
    ("0", "Start here", ["How to use the Academy", "The physics you need", "What makes a car fast",
                         "Reading telemetry"]),
    ("1", "The car as a system", ["Anatomy of a Formula 1 car", "The regulations as a design box",
                                  "Lap-time sensitivities", "Monaco or Monza: the design compromise"]),
    ("2", "Tyres", ["How rubber grips", "Slip angle and slip ratio", "The magic formula",
                    "The friction circle and g-g diagrams", "Load sensitivity", "Temperature and pressure",
                    "Wear, graining and the cliff", "Compounds and construction", "Degradation in the data"]),
    ("3", "Vehicle dynamics", ["Weight transfer", "Balance: understeer and oversteer", "Suspension layouts",
                               "Kinematics", "Springs, dampers and heave", "Ride height and rake",
                               "Differentials and traction", "Steering", "Building a lap simulator"]),
    ("4", "Aerodynamics", ["Pressure and Bernoulli", "Boundary layers and the Reynolds number",
                           "Lift, drag and efficiency", "The front wing", "Rear wing, beam wing and DRS",
                           "The floor and ground effect", "Diffuser and floor edges", "Vortices as tools",
                           "Sidepods and cooling inlets", "Dirty air", "Porpoising", "Aero maps",
                           "CFD and the wind tunnel", "2026 active aero"]),
    ("5", "Power unit", ["Engine thermodynamics", "Combustion", "Turbocharging", "The fuel-flow limit",
                         "Energy recovery", "The battery", "Energy management over a lap",
                         "Sustainable fuels", "The 2026 power unit", "Reliability and penalties",
                         "Engines through history"]),
    ("6", "Transmission", ["The seamless-shift gearbox", "Choosing gear ratios", "Clutch and launch",
                           "Driveshafts, uprights and hubs"]),
    ("7", "Brakes", ["Carbon-carbon brakes", "Brake-by-wire", "Brake bias", "Brake cooling",
                     "Braking in the data"]),
    ("8", "Chassis, materials and safety", ["The carbon monocoque", "Weight and ballast",
                                            "Crash structures", "Halo, HANS and the survival cell",
                                            "Circuit safety", "What crashes taught engineering"]),
    ("9", "Cooling", ["The heat budget", "Radiators and sidepods", "Hot races", "Cooling the driver"]),
    ("10", "Electronics, data and simulation", ["The standard ECU and sensors", "Telemetry",
                                                "The steering wheel", "Data analysis like an engineer",
                                                "Driver-in-the-loop simulators", "Correlation"]),
    ("11", "Race engineering", ["The weekend from the engineer's chair", "Practice run plans",
                                "Setup work", "Parc fermé", "Qualifying preparation",
                                "Driver and engineer"]),
    ("12", "Strategy", ["The race as an optimisation", "Degradation, fuel and pit loss",
                        "Undercut and overcut", "Safety cars", "Game theory", "Monte Carlo strategy",
                        "Reinforcement learning", "Wet races and crossovers"]),
    ("13", "Circuits", ["How circuits differ", "Circuit tours in 3D", "Historic circuits",
                        "Designing a circuit"]),
    ("14", "Rules, money and the business", ["Technical and sporting rules", "The cost cap",
                                             "How a team is organised", "Testing limits",
                                             "Protests and grey areas"]),
    ("15", "History of F1 engineering", ["Front engine to mid engine", "Wings arrive",
                                         "Ground effect, 1978", "The turbo era", "Active suspension",
                                         "The V10 years", "Blown and double diffusers", "Clever loopholes",
                                         "The hybrid era", "Ground effect returns", "2026 and after"]),
    ("16", "Capstone: design your car", ["Design, simulate, race, debrief"]),
]

GLOSSARY = {
    "downforce": "Aerodynamic force pushing the car down onto the road. It adds tyre grip without adding mass.",
    "drag": "Aerodynamic force resisting the car's motion. It grows with the square of speed.",
    "grip": "How much force the tyres can pass to the road before they slide.",
    "friction coefficient": "Grip force divided by the load on the tyre (often written μ, 'mu').",
    "curvature": "How sharply the track bends: 1 divided by the corner radius.",
    "lateral g": "Sideways acceleration in a corner, measured in multiples of gravity (9.81 m/s²).",
    "longitudinal g": "Acceleration or braking along the car, in multiples of gravity.",
    "power": "How fast the engine does work. At a given speed, driving force = power ÷ speed.",
    "air density": "Mass of air per cubic metre, about 1.2 kg/m³ at sea level, less at altitude.",
    "telemetry": "Data sent from the car's sensors to the garage while it runs.",
    "throttle": "The accelerator pedal, recorded as 0–100 %.",
    "apex": "The point of a corner closest to the inside, usually near the slowest point.",
    "lap simulator": "A program that works out the fastest possible lap for a given car and track.",
    "friction circle": "The limit on combined grip: braking or accelerating hard leaves less grip for turning.",
    "load sensitivity": "Tyre grip grows more slowly than the load on the tyre, so doubling load gives less than double grip.",
    "power unit": "The engine together with its energy-recovery motor and battery.",
    "MGU-K": "Motor Generator Unit – Kinetic: the electric motor on the crankshaft that harvests under braking and deploys power.",
    "regulations": "The FIA's technical and sporting rules every car and team must follow.",
    "wheelbase": "The distance between the front and rear axles.",
    "minimum mass": "The lightest a car with its driver may weigh, without fuel.",
    "sensitivity": "How much the lap time changes for a small change in one car property.",
    "wing level": "How much downforce (and drag) the wings are set to make. Low for fast tracks, high for twisty ones.",
    "brake bias": "How the braking force is split between the front and rear axles.",
    "monocoque": "The carbon-fibre survival cell the driver sits in, also the car's main structure.",
    "diffuser": "The upswept rear of the floor that speeds up air under the car and adds downforce.",
    "halo": "The titanium hoop over the cockpit that protects the driver's head.",
    "drs": "Drag Reduction System: a flap in the rear wing that opens on straights (until 2025).",
    "active aero": "From 2026, front and rear wings that switch between a low-drag and a high-downforce setting.",
    "ground effect": "Downforce made by shaping the floor so air under the car speeds up and its pressure drops.",
    "quasi-steady-state": "Treating every point of the lap as if the car were in a steady state there, ignoring how it got there.",
    "kinetic energy": "Energy of motion: ½ × mass × speed².",
}


def progress():
    return st.session_state.setdefault("academy_progress", {"read": set(), "quiz": {}})


def depth_picker(key):
    depth = st.segmented_control("Depth", DEPTHS, default=st.session_state.get("academy_depth", "Engineer"),
                                 key=key, help=" · ".join(f"{d}: {h}" for d, h in DEPTH_HELP.items()))
    depth = depth or "Engineer"
    st.session_state["academy_depth"] = depth
    return depth


def render_module(module_id, chapters):
    """A module page: chapter picker, the chapter, then previous/next."""
    number, title, _ = next(m for m in CURRICULUM if m[0] == module_id)
    ids = [c["id"] for c in chapters]
    key = f"academy_ch_{module_id}"
    wanted = st.query_params.get("ch")
    if wanted in ids and st.session_state.get(f"{key}_from_url") != wanted:
        st.session_state[key] = wanted
        st.session_state[f"{key}_from_url"] = wanted
    st.session_state.setdefault(key, ids[0])

    names = {c["id"]: f"{c['id']}  {c['title']}" for c in chapters}
    top_left, top_right = st.columns([3, 2], vertical_alignment="bottom")
    with top_left:
        chosen = st.selectbox(f"Module {number}: {title}", ids, format_func=names.get, key=key)
    with top_right:
        depth = depth_picker(f"academy_depth_{module_id}")

    chapter = next(c for c in chapters if c["id"] == chosen)
    render_chapter(chapter, depth)

    i = ids.index(chosen)
    st.divider()
    prev_col, mid, next_col = st.columns([1, 2, 1])
    if i > 0 and prev_col.button(f"← {chapters[i - 1]['title']}", key=f"{key}_prev", use_container_width=True):
        st.session_state[key] = ids[i - 1]
        st.rerun()
    if i < len(ids) - 1 and next_col.button(f"{chapters[i + 1]['title']} →", key=f"{key}_next",
                                            type="primary", use_container_width=True):
        st.session_state[key] = ids[i + 1]
        st.rerun()
    done = progress()["read"]
    mid.caption(f"Chapter {i + 1} of {len(ids)} · {sum(c in done for c in ids)} read in this module")


def render_chapter(chapter, depth):
    progress()["read"].add(chapter["id"])
    st.markdown(f'<div class="ac-head"><span class="ac-num">{html.escape(chapter["id"])}</span>'
                f'<div><h2>{html.escape(chapter["title"])}</h2><p>{html.escape(chapter["summary"])}</p>'
                f'</div></div>', unsafe_allow_html=True)

    levels = DEPTHS[:DEPTHS.index(depth) + 1]
    for level in levels:
        text = chapter.get({"Basics": "basics", "Engineer": "engineer", "Deep dive": "deep"}[level])
        if not text:
            continue
        if level != "Basics":
            st.markdown(f'<div class="ac-level">{level}</div>', unsafe_allow_html=True)
        st.markdown(text, unsafe_allow_html=True)

    if chapter.get("widget"):
        section("Try it", chapter.get("widget_blurb", "Change the numbers and watch what happens."))
        chapter["widget"]()

    if chapter.get("data"):
        section("In the real data", "Where to see this in the rest of the app.")
        for page, note in chapter["data"]:
            st.markdown(f'<div class="ac-data"><b>{html.escape(page)}</b><span>{html.escape(note)}</span></div>',
                        unsafe_allow_html=True)

    if chapter.get("terms"):
        section("Key terms")
        st.markdown("".join(f'<div class="ac-term"><b>{html.escape(t)}</b><span>{html.escape(GLOSSARY[t])}</span></div>'
                            for t in chapter["terms"] if t in GLOSSARY), unsafe_allow_html=True)

    if chapter.get("quiz"):
        render_quiz(chapter)

    if chapter.get("sources") and depth == "Deep dive":
        section("Sources and further reading")
        st.markdown("\n".join(f"- {s}" for s in chapter["sources"]))


def render_quiz(chapter):
    section("Check yourself", "Pick an answer for each, then check.")
    key = f"academy_quiz_{chapter['id']}"
    answers = []
    for n, (question, options, _, _) in enumerate(chapter["quiz"]):
        answers.append(st.radio(f"**{n + 1}.** {question}", options, index=None, key=f"{key}_{n}"))
    if st.button("Check my answers", key=f"{key}_check"):
        st.session_state[f"{key}_shown"] = True
    if st.session_state.get(f"{key}_shown"):
        score = 0
        for n, ((question, options, right, why), given) in enumerate(zip(chapter["quiz"], answers)):
            ok = given == options[right]
            score += ok
            mark = "✅" if ok else ("❌" if given else "⚪")
            st.markdown(f"{mark} **{n + 1}.** {html.escape(options[right])}: {why}")
        progress()["quiz"][chapter["id"]] = (score, len(chapter["quiz"]))
        st.markdown(f"**{score} of {len(chapter['quiz'])}**")


def academy_css():
    st.markdown("""<style>
.ac-head { display:flex; gap:16px; align-items:flex-start; margin: 10px 0 6px; }
.ac-num { font-family:'Saira Condensed',sans-serif; font-weight:800; font-size:1.05rem; color:#fff;
  background:var(--pp-red); padding:6px 10px; border-radius:8px; transform:skewX(-8deg); white-space:nowrap; }
.ac-head h2 { margin:0 !important; padding:0 !important; font-size:1.9rem; line-height:1.1; }
.ac-head p { margin:4px 0 0; color:var(--pp-muted) !important; }
.ac-level { display:inline-block; margin:18px 0 4px; padding:3px 10px; border-radius:999px; font-size:.75rem;
  font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:var(--pp-red);
  border:1px solid var(--pp-red); }
.ac-data, .ac-term { display:flex; gap:12px; padding:10px 14px; margin:6px 0; border-radius:12px;
  background:var(--pp-panel); border:1px solid var(--pp-border); }
.ac-data b, .ac-term b { min-width:170px; color:var(--pp-text); }
.ac-data span, .ac-term span { color:var(--pp-muted); }
.ac-mod { padding:14px 16px; border-radius:14px; background:var(--pp-panel); border:1px solid var(--pp-border);
  height:100%; }
.ac-mod h4 { margin:0 0 4px; font-family:'Saira Condensed',sans-serif; font-weight:800; font-size:1.2rem;
  color:var(--pp-text); }
.ac-mod .tag { font-size:.7rem; font-weight:700; letter-spacing:.5px; text-transform:uppercase; }
.ac-mod ol { margin:6px 0 0; padding-left:18px; color:var(--pp-muted); font-size:.85rem; }
.ac-mod li { color:var(--pp-muted) !important; }
.ac-figure { padding:10px; border-radius:14px; background:var(--pp-panel); border:1px solid var(--pp-border); }
@media (max-width: 640px) { .ac-data, .ac-term { flex-direction:column; gap:2px; } .ac-data b, .ac-term b { min-width:0; } }
</style>""", unsafe_allow_html=True)


def term_chips(terms):
    chips([(t, "#8a8a96") for t in terms])
