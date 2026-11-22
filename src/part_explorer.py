"""3D Part Explorer: rotate, explode and tap the parts of a Formula 1 car.

Every model is built here from simple shapes (boxes, cylinders, tubes, wing sections), to our own
generic design: no team's car, livery or branding. Each part has an explode direction, a colour, and
a short card (what it does, what it's made of, a fact, and the Academy chapter that explains it).

A part:  {"id", "name", "shape", "size", "pos", "rot", "colour", "explode", "info": {...}}
  shapes: box [w, h, d] · cyl [r_top, r_bottom, length] (along y; rotate to point it) ·
          foil [span, chord, thickness] (a wing section spanning x) · tube [x1,y1,z1, x2,y2,z2, r] ·
          torus [R, r] · disc [r, thickness] (along x)
  units are metres, x = across the car, y = up, z = forward
"""
import json

import streamlit.components.v1 as components

CARBON, CARBON2, RED, METAL, TITAN, GOLD, RUBBER = "#2a2a33", "#3a3a46", "#e10600", "#9aa0aa", "#b8b2a6", "#c9a24a", "#18181d"
COPPER, GREEN, BLUE = "#b87333", "#1fd6a0", "#2b6cff"


def P(id, name, shape, size, pos, colour=CARBON, rot=(0, 0, 0), explode=(0, 0, 0), what="", material="Carbon fibre composite",
      fact="", chapter=None):
    return {"id": id, "name": name, "shape": shape, "size": list(size), "pos": list(pos), "rot": list(rot),
            "colour": colour, "explode": list(explode),
            "info": {"what": what, "material": material, "fact": fact, "chapter": chapter}}


FRONT_WING = [
    P("nose", "Nose and front crash structure", "cyl", (0.06, 0.16, 0.9), (0, 0.32, 0.25), CARBON2, rot=(90, 0, 0), explode=(0, 0.35, 0.5),
      what="Absorbs a frontal impact and carries the wing. Its underside feeds air towards the floor.",
      fact="It must pass an FIA crash test, absorbing a heavy impact while keeping the driver's deceleration within limits.", chapter="8.3"),
    P("main", "Main plane", "foil", (1.70, 0.34, 0.035), (0, 0.10, 0.70), CARBON, rot=(-4, 0, 0), explode=(0, -0.12, 0.25),
      what="The largest element: makes front downforce and sets up the airflow for the rest of the car.",
      fact="Running close to the ground, it is partly a ground-effect device itself.", chapter="4.4"),
    P("flap1", "First flap", "foil", (1.60, 0.16, 0.02), (0, 0.17, 0.52), CARBON2, rot=(-16, 0, 0), explode=(0, 0.12, 0.0),
      what="Adds downforce. The slot between elements re-energises the airflow so the wing can work harder without stalling.",
      fact="Its angle is adjusted at pit stops to fine-tune the car's balance.", chapter="4.2"),
    P("flap2", "Upper flap", "foil", (1.50, 0.12, 0.018), (0, 0.25, 0.42), CARBON, rot=(-28, 0, 0), explode=(0, 0.26, -0.08),
      what="The most steeply angled element, where most of the wing's adjustment happens.",
      fact="The rules limit how many elements a front wing may have.", chapter="4.3"),
    P("ep_l", "Endplate (left)", "box", (0.02, 0.30, 0.55), (-0.86, 0.17, 0.58), CARBON2, explode=(-0.35, 0, 0),
      what="Controls the vortex at the wing tip and steers air around the front tyre.",
      fact="Since 2022 endplates are shaped to send air inwards, not outwards, to help following cars.", chapter="4.8"),
    P("ep_r", "Endplate (right)", "box", (0.02, 0.30, 0.55), (0.86, 0.17, 0.58), CARBON2, explode=(0.35, 0, 0),
      what="The mirror of the left endplate.", fact="Endplates hold the flaps rigid at their outer ends."),
    P("pylon_l", "Wing pylon (left)", "box", (0.03, 0.18, 0.18), (-0.12, 0.2, 0.62), METAL, explode=(-0.1, 0.18, 0.2),
      what="Connects the wing to the nose.", material="Titanium and carbon", fact="Wings must pass static load tests so they can't flex too much."),
    P("pylon_r", "Wing pylon (right)", "box", (0.03, 0.18, 0.18), (0.12, 0.2, 0.62), METAL, explode=(0.1, 0.18, 0.2),
      what="Connects the wing to the nose.", material="Titanium and carbon"),
]

REAR_WING = [
    P("rw_main", "Main plane", "foil", (1.0, 0.30, 0.03), (0, 0.92, -0.05), CARBON, rot=(14, 0, 0), explode=(0, 0.05, 0.25),
      what="Makes rear downforce to balance the front, and draws air up out of the diffuser.", chapter="4.5"),
    P("rw_flap", "Upper flap (moves in 2026)", "foil", (1.0, 0.16, 0.02), (0, 1.03, -0.22), CARBON2, rot=(32, 0, 0), explode=(0, 0.3, -0.2),
      what="Flattens on the straights for less drag and returns for corners: active aero from 2026 (DRS until 2025).",
      fact="Opening it cut drag enough for roughly 10–15 km/h more speed in the DRS era.", chapter="4.14"),
    P("beam", "Beam wing", "foil", (0.9, 0.16, 0.025), (0, 0.42, -0.12), CARBON2, rot=(10, 0, 0), explode=(0, -0.2, -0.2),
      what="A lower wing that strengthens the diffuser's pull on the air underneath.", fact="Reintroduced with the 2022 rules.", chapter="4.7"),
    P("rw_ep_l", "Endplate (left)", "box", (0.02, 0.75, 0.55), (-0.51, 0.72, -0.12), CARBON2, explode=(-0.35, 0, 0),
      what="Holds the wing elements and shapes the tip vortex.", chapter="4.8"),
    P("rw_ep_r", "Endplate (right)", "box", (0.02, 0.75, 0.55), (0.51, 0.72, -0.12), CARBON2, explode=(0.35, 0, 0),
      what="The mirror of the left endplate."),
    P("swan", "Swan-neck pylon", "box", (0.04, 0.42, 0.14), (0, 0.85, 0.12), METAL, explode=(0, 0.1, 0.35),
      what="Holds the wing from above, keeping the underside of the main plane clean for airflow.", material="Titanium"),
    P("actuator", "Wing actuator", "cyl", (0.025, 0.025, 0.16), (0, 1.0, -0.06), GOLD, rot=(60, 0, 0), explode=(0, 0.45, 0.1),
      what="Moves the flap between straight mode and corner mode.", material="Hydraulic actuator, metal",
      fact="It must fail safe, returning the wing to its corner position."),
    P("rainlight", "Rain light", "box", (0.08, 0.04, 0.02), (0, 0.3, -0.38), RED, explode=(0, -0.15, -0.3),
      what="Flashes in wet conditions, low speed or when the car is harvesting energy.", material="LED unit"),
]

POWER_UNIT = [
    P("block", "Engine block and crankcase", "box", (0.40, 0.22, 0.55), (0, 0.18, 0), METAL, explode=(0, -0.25, 0),
      what="The core of the 1.6-litre V6. It's also a stressed member: it carries loads between the chassis and gearbox.",
      material="Aluminium alloy", fact="The V6 banks sit at 90 degrees.", chapter="5.1"),
    P("bank_l", "Cylinder bank and head (left)", "box", (0.14, 0.22, 0.52), (-0.16, 0.38, 0), METAL, rot=(0, 0, 40), explode=(-0.35, 0.15, 0),
      what="Three cylinders with their valves and the pre-chamber combustion system.", material="Aluminium alloy, steel valves",
      fact="Combustion in a pre-chamber lets the engine burn a very lean mixture quickly.", chapter="5.2"),
    P("bank_r", "Cylinder bank and head (right)", "box", (0.14, 0.22, 0.52), (0.16, 0.38, 0), METAL, rot=(0, 0, -40), explode=(0.35, 0.15, 0),
      what="The other three cylinders.", material="Aluminium alloy", chapter="5.2"),
    P("crank", "Crankshaft", "cyl", (0.03, 0.03, 0.62), (0, 0.12, 0), TITAN, rot=(90, 0, 0), explode=(0, -0.45, 0),
      what="Turns the pistons' up-and-down motion into rotation, up to 15,000 rpm.", material="Steel alloy", chapter="5.1"),
    P("piston1", "Pistons (×6)", "cyl", (0.04, 0.04, 0.05), (-0.16, 0.36, 0.12), TITAN, explode=(-0.55, 0.4, 0.1),
      what="Pushed down by the burning gas; the stroke is short and the bore is fixed by the rules at 80 mm.",
      material="Aluminium or steel alloy", fact="At full revs each piston changes direction about 500 times a second."),
    P("turbo_c", "Turbo compressor", "cyl", (0.09, 0.09, 0.09), (0, 0.32, 0.36), METAL, rot=(90, 0, 0), explode=(0, 0.1, 0.45),
      what="Squeezes air into the engine so more fuel can burn.", material="Aluminium/titanium wheel", chapter="5.3"),
    P("turbo_t", "Turbo turbine", "cyl", (0.08, 0.08, 0.08), (0, 0.32, -0.36), COPPER, rot=(90, 0, 0), explode=(0, 0.1, -0.5),
      what="Spun by the exhaust, it drives the compressor on the same shaft.", material="Nickel superalloy",
      fact="It runs at well over 100,000 rpm and glows red-hot.", chapter="5.3"),
    P("turbo_shaft", "Turbo shaft (MGU-H until 2025)", "cyl", (0.02, 0.02, 0.72), (0, 0.32, 0), GOLD, rot=(90, 0, 0), explode=(0, 0.3, 0),
      what="Joins turbine and compressor. Until 2025 an electric motor (MGU-H) sat on it; it was removed for 2026.",
      material="Steel", chapter="5.3"),
    P("intercooler", "Intercooler", "box", (0.30, 0.12, 0.10), (0, 0.55, 0.36), "#5a6270", explode=(0, 0.45, 0.25),
      what="Cools the compressed air before it enters the engine: denser air and less knock.", material="Aluminium core", chapter="5.3"),
    P("mguk", "MGU-K", "cyl", (0.07, 0.07, 0.16), (0.24, 0.12, 0.25), BLUE, explode=(0.5, -0.1, 0.2),
      what="The electric motor-generator on the crankshaft: harvests under braking and deploys up to 350 kW in 2026.",
      material="Copper windings, rare-earth magnets", fact="It nearly tripled in power for 2026 (120 kW before).", chapter="5.5"),
    P("battery", "Energy store (battery)", "box", (0.40, 0.08, 0.30), (0, -0.04, 0.42), GREEN, explode=(0, -0.45, 0.35),
      what="Lithium-ion cells that charge and discharge at hundreds of kilowatts, many times a lap.",
      material="Lithium-ion cells", fact="It stores only a few megajoules: built for power, not range.", chapter="5.6"),
    P("ce", "Control electronics", "box", (0.18, 0.05, 0.14), (0, 0.02, -0.38), "#4a4a5a", explode=(0, -0.4, -0.35),
      what="Power electronics that convert and route energy between the battery and the motor.", material="Electronics in a cooled case"),
    P("exh_l", "Exhaust (left)", "tube", (-0.2, 0.45, -0.15, -0.05, 0.36, -0.42, 0.03), (0, 0, 0), COPPER, explode=(-0.3, 0.2, -0.3),
      what="Carries exhaust gas from the left bank to the turbine.", material="Inconel"),
    P("exh_r", "Exhaust (right)", "tube", (0.2, 0.45, -0.15, 0.05, 0.36, -0.42, 0.03), (0, 0, 0), COPPER, explode=(0.3, 0.2, -0.3),
      what="Carries exhaust gas from the right bank to the turbine.", material="Inconel"),
]

CORNER = [
    P("tyre", "Tyre", "torus", (0.30, 0.09), (0, 0.36, 0), RUBBER, rot=(0, 90, 0), explode=(0.55, 0, 0),
      what="The only contact with the road. 18-inch wheels since 2022, supplied by Pirelli to every team.",
      material="Rubber compound on a fabric carcass", fact="Its grip peaks at about 6° of slip angle.", chapter="2.1"),
    P("rim", "Wheel rim", "disc", (0.23, 0.30), (0, 0.36, 0), "#55555f", explode=(0.38, 0, 0),
      what="Holds the tyre, and carries brake heat that affects tyre temperature.", material="Magnesium alloy", chapter="2.6"),
    P("nut", "Wheel nut", "cyl", (0.045, 0.045, 0.06), (0.17, 0.36, 0), RED, rot=(0, 0, 90), explode=(0.75, 0, 0),
      what="A single centre-locking nut: off and on in about two seconds at a pit stop.", material="Aluminium/titanium", chapter="6.4"),
    P("disc", "Brake disc", "disc", (0.16, 0.032), (-0.05, 0.36, 0), "#3b3b44", explode=(0.12, 0, 0),
      what="Carbon-carbon disc with more than a thousand cooling holes, working between about 400 and 1,000 °C.",
      material="Carbon-carbon", fact="Braking from 320 to 90 km/h turns about 3 MJ into heat.", chapter="7.1"),
    P("caliper", "Brake caliper", "box", (0.06, 0.13, 0.08), (-0.05, 0.47, 0.11), RED, explode=(0.1, 0.25, 0.15),
      what="Squeezes the pads onto the disc.", material="Aluminium-lithium alloy", chapter="7.1"),
    P("upright", "Upright", "box", (0.06, 0.26, 0.10), (-0.11, 0.36, 0), TITAN, explode=(-0.05, 0, 0),
      what="Carries the wheel bearings, brakes and suspension mounts, and must be very stiff.", material="Titanium or metal-matrix composite",
      chapter="6.4"),
    P("duct", "Brake duct", "box", (0.06, 0.12, 0.16), (-0.13, 0.30, 0.15), CARBON2, explode=(-0.1, -0.15, 0.3),
      what="Feeds cooling air to the brakes; sized for each circuit, and shaped for aerodynamics too.", chapter="7.4"),
    P("uwb_f", "Upper wishbone", "tube", (-0.12, 0.48, 0, -0.62, 0.45, 0.22, 0.012), (0, 0, 0), CARBON2, explode=(-0.2, 0.25, 0),
      what="One of the two A-shaped arms that locate the wheel and set its camber change.", chapter="3.3"),
    P("uwb_r", "Upper wishbone (rear leg)", "tube", (-0.12, 0.48, 0, -0.62, 0.45, -0.22, 0.012), (0, 0, 0), CARBON2, explode=(-0.2, 0.25, 0),
      what="The rear leg of the upper wishbone.", chapter="3.3"),
    P("lwb_f", "Lower wishbone", "tube", (-0.12, 0.24, 0, -0.62, 0.20, 0.25, 0.014), (0, 0, 0), CARBON2, explode=(-0.2, -0.25, 0),
      what="The lower arm, which takes the largest loads.", chapter="3.3"),
    P("lwb_r", "Lower wishbone (rear leg)", "tube", (-0.12, 0.24, 0, -0.62, 0.20, -0.25, 0.014), (0, 0, 0), CARBON2, explode=(-0.2, -0.25, 0),
      what="The rear leg of the lower wishbone.", chapter="3.3"),
    P("pushrod", "Push rod", "tube", (-0.13, 0.26, 0.02, -0.58, 0.55, 0.02, 0.011), (0, 0, 0), METAL, explode=(-0.25, 0.4, 0),
      what="Pushes on a rocker inside the car as the wheel rises, working the springs and dampers out of the airflow.",
      material="Steel/titanium", chapter="3.3"),
    P("damper", "Spring and damper (inboard)", "cyl", (0.022, 0.022, 0.2), (-0.62, 0.58, 0), GOLD, rot=(0, 0, 90), explode=(-0.45, 0.45, 0),
      what="Inside the car: the spring holds it up, the damper controls how fast it moves.", material="Steel, aluminium", chapter="3.5"),
]

FLOOR = [
    P("floor", "Floor", "box", (1.40, 0.025, 2.6), (0, 0.06, 0), CARBON, explode=(0, -0.1, 0),
      what="Since 2022 the biggest source of downforce. Its underside is shaped into tunnels.", chapter="4.6"),
    P("tunnel_l", "Venturi tunnel (left)", "box", (0.32, 0.06, 2.2), (-0.38, 0.03, -0.1), "#1c1c26", explode=(-0.25, -0.35, 0),
      what="Narrows to a throat and widens again: air speeds up, pressure drops, and the car is sucked to the track.",
      fact="Downforce rises steeply as the floor gets closer to the track, until it stalls.", chapter="4.6"),
    P("tunnel_r", "Venturi tunnel (right)", "box", (0.32, 0.06, 2.2), (0.38, 0.03, -0.1), "#1c1c26", explode=(0.25, -0.35, 0),
      what="The mirror of the left tunnel.", chapter="4.6"),
    P("diffuser", "Diffuser", "box", (1.0, 0.025, 0.55), (0, 0.16, -1.45), CARBON2, rot=(-14, 0, 0), explode=(0, 0.1, -0.5),
      what="Slows the fast underbody air back down smoothly, letting the whole floor work harder.",
      fact="The 2009 'double diffuser' won Brawn GP the title before it was banned.", chapter="4.7"),
    P("plank", "Plank (skid block)", "box", (0.30, 0.012, 2.2), (0, 0.035, 0.0), "#c8a26a", explode=(0, -0.6, 0),
      what="A wooden-composite strip under the car. Too much wear means disqualification, which stops teams running too low.",
      material="Wood-fibre composite with titanium skids", fact="Excess wear disqualified two cars at the 2023 United States GP.", chapter="3.6"),
    P("edge_l", "Floor edge wing (left)", "foil", (0.08, 0.5, 0.012), (-0.72, 0.09, 0.2), CARBON2, rot=(0, 90, 0), explode=(-0.35, 0.1, 0),
      what="Shapes vortices along the floor's edge that act like an invisible skirt, sealing the low pressure underneath.", chapter="4.8"),
    P("edge_r", "Floor edge wing (right)", "foil", (0.08, 0.5, 0.012), (0.72, 0.09, 0.2), CARBON2, rot=(0, 90, 0), explode=(0.35, 0.1, 0),
      what="The mirror of the left edge wing.", chapter="4.8"),
    P("fence", "Floor fences", "box", (0.4, 0.12, 0.35), (0, 0.10, 1.05), CARBON2, explode=(0, 0.25, 0.35),
      what="Vanes at the floor's entry that split and steer the air into the tunnels.", chapter="4.6"),
]

CAR = [
    P("tub", "Monocoque (survival cell)", "box", (0.62, 0.55, 1.9), (0, 0.42, 0.55), CARBON, explode=(0, 0.25, 0.2),
      what="The carbon-fibre tub the driver sits in: the car's backbone and safety cell.",
      fact="It must pass a series of FIA crash and load tests.", chapter="8.1"),
    P("halo", "Halo", "torus", (0.32, 0.025), (0, 0.84, 0.38), TITAN, rot=(80, 0, 0), explode=(0, 0.55, 0.1),
      what="The titanium hoop over the cockpit that protects the driver's head.", material="Titanium",
      fact="It can carry loads equivalent to a large car resting on it.", chapter="8.4"),
    P("cover", "Engine cover and airbox", "box", (0.5, 0.42, 1.5), (0, 0.55, -0.95), CARBON2, explode=(0, 0.55, -0.2),
      what="Feeds air to the engine and guides the flow towards the rear wing."),
    P("pod_l", "Sidepod (left)", "box", (0.32, 0.36, 1.2), (-0.5, 0.33, -0.25), CARBON2, explode=(-0.5, 0.1, 0),
      what="Houses the radiators; its shape guides air to the floor edge and rear.", chapter="4.9"),
    P("pod_r", "Sidepod (right)", "box", (0.32, 0.36, 1.2), (0.5, 0.33, -0.25), CARBON2, explode=(0.5, 0.1, 0),
      what="Houses the radiators.", chapter="4.9"),
    P("c_floor", "Floor", "box", (1.40, 0.03, 3.4), (0, 0.06, -0.2), CARBON, explode=(0, -0.4, 0),
      what="The biggest source of downforce: tunnels underneath suck the car to the track.", chapter="4.6"),
    P("c_fw", "Front wing", "foil", (1.8, 0.4, 0.05), (0, 0.12, 2.25), CARBON, rot=(-8, 0, 0), explode=(0, 0, 0.6),
      what="Front downforce and airflow control for the whole car. Open the Front wing model to take it apart.", chapter="4.4"),
    P("c_nose", "Nose", "cyl", (0.06, 0.18, 0.8), (0, 0.33, 1.9), CARBON2, rot=(90, 0, 0), explode=(0, 0.15, 0.6),
      what="Crash structure carrying the front wing.", chapter="8.3"),
    P("c_rw", "Rear wing", "foil", (1.0, 0.4, 0.05), (0, 0.95, -2.05), CARBON, rot=(16, 0, 0), explode=(0, 0.45, -0.5),
      what="Rear downforce; moves for less drag on straights in 2026. Open the Rear wing model to take it apart.", chapter="4.5"),
    P("c_pu", "Power unit", "box", (0.45, 0.4, 0.75), (0, 0.42, -0.75), METAL, explode=(0, 1.1, -0.3),
      what="V6 turbo hybrid behind the driver. Open the Power unit model to take it apart.", material="Aluminium, steel, copper", chapter="5.9"),
    P("c_gb", "Gearbox", "box", (0.3, 0.25, 0.6), (0, 0.32, -1.45), TITAN, explode=(0, 0.2, -0.7),
      what="Eight-speed seamless-shift gearbox; the rear suspension mounts on its casing.", material="Carbon or titanium casing", chapter="6.1"),
    P("w_fl", "Front-left wheel", "torus", (0.30, 0.09), (-0.82, 0.36, 1.6), RUBBER, rot=(0, 90, 0), explode=(-0.7, 0, 0.2),
      what="18-inch wheel and Pirelli tyre. Open the Wheel corner model to take it apart.", material="Rubber, magnesium", chapter="2.1"),
    P("w_fr", "Front-right wheel", "torus", (0.30, 0.09), (0.82, 0.36, 1.6), RUBBER, rot=(0, 90, 0), explode=(0.7, 0, 0.2),
      what="18-inch wheel and Pirelli tyre.", material="Rubber, magnesium", chapter="2.1"),
    P("w_rl", "Rear-left wheel", "torus", (0.31, 0.10), (-0.80, 0.37, -1.6), RUBBER, rot=(0, 90, 0), explode=(-0.7, 0, -0.2),
      what="Rear tyres are wider and take the engine's power.", material="Rubber, magnesium", chapter="2.1"),
    P("w_rr", "Rear-right wheel", "torus", (0.31, 0.10), (0.80, 0.37, -1.6), RUBBER, rot=(0, 90, 0), explode=(0.7, 0, -0.2),
      what="Rear tyres are wider and take the engine's power.", material="Rubber, magnesium", chapter="2.1"),
]

ASSEMBLIES = {
    "Whole car": {"parts": CAR, "camera": 5.5, "blurb": "The car as six big systems. Explode it, then open each system on its own."},
    "Front wing": {"parts": FRONT_WING, "camera": 2.6, "blurb": "Main plane, flaps, endplates and the nose."},
    "Rear wing": {"parts": REAR_WING, "camera": 2.4, "blurb": "Main plane, the moving flap, beam wing and endplates."},
    "Power unit": {"parts": POWER_UNIT, "camera": 2.2, "blurb": "The V6, its turbo, the MGU-K, the battery and the electronics."},
    "Wheel corner": {"parts": CORNER, "camera": 2.2, "blurb": "Tyre, rim, brakes, upright and suspension."},
    "Floor and diffuser": {"parts": FLOOR, "camera": 3.6, "blurb": "Where most of today's downforce comes from."},
}


def explorer(name, dark=True, height=640):
    a = ASSEMBLIES[name]
    data = {"parts": a["parts"], "camera": a["camera"], "dark": dark}
    components.html(PAGE.replace("__DATA__", json.dumps(data)).replace("__THREE__", "https://cdn.jsdelivr.net/npm/three@0.160.0"),
                    height=height)


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
 html,body{margin:0;height:100%;overflow:hidden;font-family:Inter,system-ui,sans-serif}
 #wrap{position:relative;height:100%;border-radius:16px;overflow:hidden;border:1px solid var(--b)}
 canvas{display:block}
 #panel{position:absolute;right:12px;top:12px;width:300px;max-width:46%;background:var(--p);border:1px solid var(--b);border-radius:14px;
   padding:14px;color:var(--t);font-size:13px;line-height:1.45;display:none}
 #panel h3{margin:0 0 6px;font:800 20px 'Saira Condensed',Inter,sans-serif;letter-spacing:.3px;color:var(--t)}
 #panel .tag{display:inline-block;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#e10600;margin-bottom:6px}
 #panel p{margin:6px 0;color:var(--t)} #panel small{display:block;color:var(--m);margin-top:8px}
 #panel .fact{border-left:3px solid #e10600;padding-left:8px;color:var(--m)}
 #panel button{margin-top:10px}
 #list{position:absolute;left:12px;top:12px;max-height:calc(100% - 120px);overflow:auto;display:flex;flex-direction:column;gap:4px;width:200px}
 #list div{font-size:12px;font-weight:600;padding:6px 10px;border-radius:999px;background:var(--p);border:1px solid var(--b);color:var(--t);cursor:pointer;
   white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 #list div.on{border-color:#e10600;color:#e10600}
 #bar{position:absolute;left:12px;right:12px;bottom:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;
   background:var(--p);border:1px solid var(--b);border-radius:14px;padding:10px 12px;color:var(--t)}
 #bar label{font-size:12px;font-weight:600;display:flex;align-items:center;gap:8px;flex:1;min-width:200px}
 #explode{flex:1;accent-color:#e10600}
 button{font:600 12px Inter,system-ui,sans-serif;padding:8px 13px;border-radius:999px;cursor:pointer;border:1px solid var(--b);background:var(--p2);color:var(--t)}
 button.on{background:#e10600;border-color:#e10600;color:#fff}
 #hint{position:absolute;left:50%;top:12px;transform:translateX(-50%);font-size:11px;color:var(--m);pointer-events:none}
 @media(max-width:620px){#list{display:none}#panel{max-width:none;left:12px;right:12px;width:auto;top:auto;bottom:74px}}
</style><script type="importmap">{"imports":{"three":"__THREE__/build/three.module.js","three/addons/":"__THREE__/examples/jsm/"}}</script>
</head><body><div id="wrap"><div id="list"></div><div id="hint">Drag to rotate · scroll to zoom · tap a part</div>
<div id="panel"><span class="tag" id="ptag">Part</span><h3 id="pname"></h3><p id="pwhat"></p><p class="fact" id="pfact"></p>
<small id="pmat"></small><small id="pch"></small><button id="isolate">Isolate</button> <button id="close">Close</button></div>
<div id="bar"><label>Explode <input id="explode" type="range" min="0" max="100" value="0"></label>
<button id="spin">Spin</button><button id="showall">Show all</button><button id="reset">Reset view</button></div></div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
const D=__DATA__;
const T=D.dark?{bg:"#0b0b10",p:"rgba(21,21,30,.9)",p2:"#1e1e29",b:"#2c2c3a",t:"#f5f5f7",m:"#a3a3b2",ground:"#111118",grid:"#23232f"}
              :{bg:"#f6f6f3",p:"rgba(255,255,255,.93)",p2:"#ececea",b:"#d9d9d4",t:"#15151e",m:"#55556a",ground:"#e6e6e1",grid:"#d0d0c8"};
const wrap=document.getElementById("wrap");for(const[k,v]of Object.entries(T))wrap.style.setProperty("--"+k,v);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
wrap.insertBefore(renderer.domElement,wrap.firstChild);
const scene=new THREE.Scene();scene.background=new THREE.Color(T.bg);
const camera=new THREE.PerspectiveCamera(40,1,0.01,100);
scene.add(new THREE.HemisphereLight(0xffffff,0x303040,1.1));
const key=new THREE.DirectionalLight(0xffffff,1.6);key.position.set(3,5,4);scene.add(key);
const rim=new THREE.DirectionalLight(0xff4030,0.5);rim.position.set(-4,2,-3);scene.add(rim);
const grid=new THREE.GridHelper(12,48,T.grid,T.grid);grid.position.y=-0.02;scene.add(grid);

function foilShape(chord,t){const s=new THREE.Shape(),n=30;const pt=(x,up)=>{const yt=5*t*(0.2969*Math.sqrt(x)-0.126*x-0.3516*x*x+0.2843*x**3-0.1036*x**4);
  const yc=0.04*(x<0.4?(2*0.4*x-x*x)/0.16:((1-0.8)+0.8*x-x*x)/0.36);return [ (0.5-x)*chord, -(yc+(up?yt:-yt))*chord ]};
  for(let k=0;k<=n;k++){const x=(1-Math.cos(Math.PI*k/n))/2;const[a,b]=pt(x,true);k?s.lineTo(a,b):s.moveTo(a,b)}
  for(let k=n;k>=0;k--){const x=(1-Math.cos(Math.PI*k/n))/2;const[a,b]=pt(x,false);s.lineTo(a,b)}return s}
function geom(p){const s=p.size;
  if(p.shape==="box")return new THREE.BoxGeometry(s[0],s[1],s[2]);
  if(p.shape==="cyl")return new THREE.CylinderGeometry(s[0],s[1],s[2],32);
  if(p.shape==="torus")return new THREE.TorusGeometry(s[0],s[1],20,48);
  if(p.shape==="disc"){const g=new THREE.CylinderGeometry(s[0],s[0],s[1],40);g.rotateZ(Math.PI/2);return g}
  if(p.shape==="foil"){const g=new THREE.ExtrudeGeometry(foilShape(s[1],s[2]/s[1]),{depth:s[0],bevelEnabled:false});g.translate(0,0,-s[0]/2);g.rotateY(Math.PI/2);return g}
  if(p.shape==="tube"){const a=new THREE.Vector3(s[0],s[1],s[2]),b=new THREE.Vector3(s[3],s[4],s[5]);
    return new THREE.TubeGeometry(new THREE.LineCurve3(a,b),4,s[6],10,false)}
  return new THREE.BoxGeometry(.1,.1,.1)}
const meshes=[],byId={};
for(const p of D.parts){
  const mat=new THREE.MeshStandardMaterial({color:p.colour,roughness:p.colour==="#18181d"?0.9:0.45,metalness:["#9aa0aa","#b8b2a6","#c9a24a","#b87333"].includes(p.colour)?0.7:0.25});
  const m=new THREE.Mesh(geom(p),mat);
  if(p.shape!=="tube"){m.position.set(...p.pos);m.rotation.set(...p.rot.map(d=>d*Math.PI/180))}
  m.userData={p,home:m.position.clone(),dir:new THREE.Vector3(...p.explode)};
  scene.add(m);meshes.push(m);byId[p.id]=m}
// centre the model
const box=new THREE.Box3();meshes.forEach(m=>box.expandByObject(m));const centre=box.getCenter(new THREE.Vector3());
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.copy(centre);
function resetView(){camera.position.set(centre.x+D.camera*0.8,centre.y+D.camera*0.45,centre.z+D.camera*0.9);controls.target.copy(centre);controls.update()}
resetView();

// list
const list=document.getElementById("list");
meshes.forEach(m=>{const d=document.createElement("div");d.textContent=m.userData.p.name;d.onclick=()=>select(m);m.userData.row=d;list.appendChild(d)});
// selection
let selected=null,isolated=false;
const panel=document.getElementById("panel");
function paint(){meshes.forEach(m=>{const on=m===selected;m.material.emissive=new THREE.Color(on?"#e10600":"#000000");m.material.emissiveIntensity=on?0.45:0;
  m.visible=!isolated||on;m.userData.row.classList.toggle("on",on)})}
function select(m){selected=m;const p=m.userData.p,i=p.info;panel.style.display="block";
  document.getElementById("pname").textContent=p.name;document.getElementById("pwhat").textContent=i.what||"";
  const f=document.getElementById("pfact");f.textContent=i.fact||"";f.style.display=i.fact?"block":"none";
  document.getElementById("pmat").textContent="Material: "+(i.material||"");
  document.getElementById("pch").textContent=i.chapter?"Read more: Academy chapter "+i.chapter:"";
  isolated=false;document.getElementById("isolate").textContent="Isolate";paint();
  const c=new THREE.Box3().setFromObject(m).getCenter(new THREE.Vector3());controls.target.lerp(c,0.6)}
document.getElementById("close").onclick=()=>{selected=null;isolated=false;panel.style.display="none";paint();controls.target.copy(centre)};
document.getElementById("isolate").onclick=e=>{isolated=!isolated;e.target.textContent=isolated?"Show the rest":"Isolate";paint()};
document.getElementById("showall").onclick=()=>{isolated=false;paint()};
document.getElementById("reset").onclick=resetView;
let spin=false;document.getElementById("spin").onclick=e=>{spin=!spin;controls.autoRotate=spin;e.target.classList.toggle("on",spin)};
// tap to select (not when dragging)
const ray=new THREE.Raycaster(),ptr=new THREE.Vector2();let down=null;
renderer.domElement.addEventListener("pointerdown",e=>{down=[e.clientX,e.clientY];document.getElementById("hint").style.display="none"});
renderer.domElement.addEventListener("pointerup",e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>6)return;
  const r=renderer.domElement.getBoundingClientRect();ptr.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);
  ray.setFromCamera(ptr,camera);const hit=ray.intersectObjects(meshes.filter(m=>m.visible))[0];if(hit)select(hit.object)});
// explode
const ex=document.getElementById("explode");
function resize(){const w=wrap.clientWidth,h=wrap.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(resize).observe(wrap);resize();
let k=0;(function frame(){const target=ex.value/100;k+=(target-k)*0.15;
  meshes.forEach(m=>{const u=m.userData;if(m.userData.p.shape==="tube")m.position.copy(u.dir).multiplyScalar(k*1.6);
    else m.position.copy(u.home).addScaledVector(u.dir,k*1.6)});
  controls.update();renderer.render(scene,camera);requestAnimationFrame(frame)})();
</script></body></html>"""
