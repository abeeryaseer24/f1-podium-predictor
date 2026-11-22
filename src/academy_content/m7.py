"""Module 7: Brakes."""
import academy_widgets_m4 as W
from academy_content.m4 import ch

SOURCES = ["Brembo, public F1 brake material and circuit braking guides, brembo.com",
           "Limpert, R. (2011). Brake Design and Safety, 3rd ed. SAE International.",
           "FIA Formula 1 Technical Regulations, brake articles, fia.com"]

CHAPTERS = [
    ch("7.1", "Carbon-carbon brakes", "Discs and pads of carbon fibre, glowing at hundreds of degrees.",
       """
F1 brakes use discs and pads made of **carbon-carbon**: carbon fibres in a carbon matrix. They're
very light, keep working at temperatures that would destroy steel, and grip harder as they heat up.
The catch: they only work well when hot. Cold carbon brakes barely grip, which is why drivers weave and
brake hard on the formation lap.

Each disc is drilled with well over a thousand tiny cooling holes, and the brakes can glow orange in
heavy braking zones at night races.
""",
       """
**Temperature window.** Carbon-carbon works best roughly between 400 and 1,000 °C. Above that it oxidises
and wears quickly; below it, friction drops. Teams choose duct sizes per circuit to keep the brakes in
the window (7.4).

**Why carbon.** High specific heat and thermal conductivity let the disc soak up a braking zone's energy
(several megajoules, 7.5) and shed it before the next one, at a fraction of steel's weight.
""",
       """
**Manufacturing** takes months: carbon fibre preforms are densified with carbon by chemical vapour
infiltration in furnaces, then machined, including the cooling holes. Brake suppliers develop discs by
circuit severity, with designs for heavy-braking tracks like Montréal and Monza.
""",
       [("F1 brake discs are made of…", ["steel", "carbon-carbon", "aluminium", "ceramic tiles"], 1, "Carbon fibres in a carbon matrix."),
        ("Carbon brakes work best when…", ["cold", "hot, roughly 400–1,000 °C", "wet", "new only"], 1, "They need heat."),
        ("Why do drivers brake hard on the formation lap?", ["To warm the brakes and tyres", "Rules", "To save fuel", "To test radio"], 0,
         "Cold carbon barely grips."),
        ("Each disc has…", ["no holes", "well over a thousand cooling holes", "one big hole", "fins only"], 1, "For cooling."),
        ("Too hot carbon brakes…", ["grip more forever", "oxidise and wear quickly", "freeze", "turn to steel"], 1, "Above the window.")],
       sources=SOURCES),

    ch("7.2", "Brake-by-wire", "The rear brakes share their job with the energy-recovery motor.",
       """
Since 2014 the rear brakes are **brake-by-wire**. When the driver presses the pedal, a computer decides
how much braking the rear axle needs and splits it between the friction brakes and the **MGU-K**, which
brakes the car while harvesting energy (Module 5.5).

The driver just feels a consistent pedal. Behind it, the system is constantly blending the two so the
total rear braking stays the same, however much the MGU-K is harvesting.
""",
       """
**Why it's needed.** The MGU-K's braking torque varies with how much energy it can store and how fast
the car is going. Without blending, the rear braking would change from corner to corner and lap to lap,
locking the rears one moment and under-braking the next.

**Failure mode.** If brake-by-wire fails, the car falls back to a conventional hydraulic rear circuit,
but the balance changes and the driver must adapt, often with a big moment at the next corner.
""",
       """
**2026.** With a 350 kW MGU-K harvesting much more under braking, rear-axle braking from the motor is a far
larger share of the total, making brake-by-wire calibration and rear stability even more important.
""",
       [("Brake-by-wire controls…", ["the front brakes", "the rear braking split between friction brakes and the MGU-K", "the clutch",
                                     "the steering"], 1, "Since 2014."),
        ("What does the driver feel?", ["A changing pedal", "A consistent pedal", "No pedal", "Vibration only"], 1, "The computer blends."),
        ("Why is blending needed?", ["The MGU-K's braking varies", "Rules", "Weight", "Noise"], 0, "Keep total rear braking steady."),
        ("If brake-by-wire fails…", ["the car stops", "it falls back to a hydraulic rear circuit", "the brakes lock", "nothing changes"], 1,
         "With a different balance."),
        ("Why does 2026 make it more important?", ["The MGU-K harvests far more under braking", "Fewer brakes", "Bigger discs", "No reason"], 0,
         "A bigger share of rear braking.")],
       terms=["MGU-K"], sources=SOURCES),

    ch("7.3", "Brake bias", "How braking is split between front and rear, and why drivers change it every lap.",
       """
**Brake bias** is the share of braking force on the front axle. Under heavy braking, load transfers to
the front (Module 3.1), so the front tyres can take more braking than the rear: bias is typically well
over half to the front.

Drivers adjust it from the steering wheel, often several times a lap: more to the front for a corner
where the rears lock, more to the rear to help the car rotate into a slow hairpin, and steadily as fuel
burns off and the balance changes.
""",
       """
**Locking.** If one axle reaches its grip limit first, its wheels lock: front locking makes the car run
straight on and flat-spots the tyres; rear locking makes it unstable. The ideal bias puts both axles at
their limit together, which changes with speed (downforce), fuel load and grip.

**Bias migration.** Modern systems can shift bias automatically through the braking zone as speed and
downforce fall, set up by the driver and engineers in advance.
""",
       """
**Interaction with harvesting.** Because the MGU-K brakes only the rear, the effective bias changes with
the harvest level. Brake-by-wire compensates, but drivers still tune bias with energy settings in mind.
""",
       [("Brake bias is…", ["brake temperature", "the share of braking on the front axle", "pedal travel", "a penalty"], 1,
         "Typically more than half at the front."),
        ("Why is bias usually forward?", ["Load transfers to the front under braking", "Rules", "Bigger front tyres", "Cooling"], 0,
         "Weight transfer."),
        ("Front locking makes the car…", ["spin", "run straight on", "faster", "lighter"], 1, "And flat-spots tyres."),
        ("Why do drivers change bias during a race?", ["Fuel burns off and grip changes", "Boredom", "Rules", "Radio"], 0,
         "The balance moves."),
        ("Bias migration means…", ["bias changes through the braking zone", "moving teams", "tyre wear", "a gearbox"], 0,
         "As downforce falls.")],
       sources=SOURCES),

    ch("7.4", "Brake cooling", "Ducts sized for every circuit, balancing cooling against drag.",
       """
Brakes must stay inside their temperature window. **Brake ducts**, shaped scoops inside the wheels,
feed cooling air to the discs and calipers. Bigger ducts cool more but add drag, so teams choose duct
sizes for each circuit: large for heavy-braking tracks, small for flowing ones.

The heat doesn't only go into the air. Some soaks into the wheel rim and the tyre, which affects tyre
temperature and pressure (Module 2.6). Brake cooling is part of tyre management.
""",
       """
**Circuit severity.** Tracks with many big stops from high speed (Montréal, Monza, Bahrain, Mexico City's
thin air) are the hardest on brakes. Brake suppliers publish a severity scale per circuit.

**Thin air.** At altitude there's less air to cool the brakes and engine, so teams run their biggest
ducts and openings there.
""",
       """
**Aero coupling.** The ducts also shape the airflow around the front and rear wheels, so the duct design is
negotiated between the brake and aerodynamics engineers. Rules restrict their geometry to stop them being
used as aerodynamic devices.
""",
       [("Brake ducts…", ["add downforce only", "feed cooling air to the brakes", "store fuel", "steer"], 1, "Inside the wheels."),
        ("Bigger ducts mean…", ["less cooling", "more cooling and more drag", "no drag", "more power"], 1, "A trade-off."),
        ("Brake heat also flows into…", ["the engine", "the wheel rim and tyre", "the battery", "the driver"], 1,
         "Affecting tyre temperature."),
        ("Why run big ducts in Mexico City?", ["Thin air cools less", "It's cold", "Rules", "Rain"], 0, "Altitude."),
        ("Which track is hard on brakes?", ["Montréal", "A flat-out oval", "A straight line", "None"], 0, "Many big stops.")],
       sources=SOURCES),

    ch("7.5", "Braking in the data", "Losing 200 km/h in under three seconds: the numbers behind a braking zone.",
       """
An F1 car can brake from over 300 km/h to under 100 km/h in about 100 metres and under three seconds.
The driver presses the pedal with well over 100 kg of force, and their body takes up to 5–6 g.

All that energy of motion has to go somewhere. Most becomes heat in the brakes; some goes into the
battery through the MGU-K. The demo works out how much, for any braking zone.
""",
       """
**Energy and power.** Braking from $v_1$ to $v_2$ removes $\\tfrac12 m (v_1^2 - v_2^2)$. From 320 to
90 km/h for an 820 kg car that's about 3 MJ, in roughly 1.5–2 seconds: an average of well over a
megawatt, mostly as heat.

**Why braking is so strong.** Downforce adds load at the start of the braking zone when speed is highest,
and drag helps too. As the car slows, downforce falls, so drivers ease off the pedal through the zone
to avoid locking (trail braking, Module 2.4).

**In the data.** The braking zones show as steep falls on the speed trace; the Ghost Lap Duel and Tyre
Physics' g-g diagram show them from real laps.
""",
       """
**Measuring braking from public data.** OpenF1's brake channel is nearly on/off, so deceleration has to
come from the speed trace. At about 4 samples a second the peaks are smoothed, so public data
underestimates peak braking g; team data at hundreds of hertz shows the full 5–6 g.
""",
       [("An F1 car braking from 300+ km/h reaches about…", ["1 g", "5–6 g", "20 g", "0.5 g"], 1, "Helped by downforce."),
        ("Braking from 320 to 90 km/h removes about…", ["30 kJ", "300 kJ", "3 MJ", "30 MJ"], 2, "For an 820 kg car."),
        ("Why do drivers ease off the brake through a zone?", ["Downforce falls as speed falls", "To save pads", "Rules", "Noise"], 0,
         "To avoid locking."),
        ("Where does braking energy go?", ["Mostly heat, some to the battery", "Sound only", "Nowhere", "The tyres only"], 0,
         "Brakes and MGU-K."),
        ("Why does public data underestimate peak braking?", ["Low sample rate smooths the peaks", "Rules", "Wrong units", "It doesn't"], 0,
         "About 4 samples a second.")],
       widget=W.braking_energy, blurb="Energy, time and power for any braking zone.",
       data=[("Ghost Lap Duel", "Two drivers' braking points overlaid."), ("Tyre Physics", "Real braking g on the g-g diagram.")],
       terms=["kinetic energy", "longitudinal g"], sources=SOURCES),
]
