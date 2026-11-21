"""Module 1: The car as a system."""
import academy_widgets as W

CHAPTERS = [
    {
        "id": "1.1",
        "title": "Anatomy of a Formula 1 car",
        "summary": "Twelve parts, what each one does, and how they depend on each other.",
        "basics": """
A Formula 1 car looks like a collection of parts, but every part is there to serve two jobs:
**keep the tyres pressed into the road** and **get the car through the air with as little
resistance as possible**, all inside a safety cell that protects the driver.

Start at the front and work back:

- The **front wing** is the first thing the air meets. It makes downforce on the front axle
  and steers the air round the front wheels, which are messy for airflow.
- The **monocoque** is a carbon-fibre tub. The driver sits in it, everything else bolts to it,
  and in a crash it's what keeps the driver alive. The **halo** above it protects the head.
- The **power unit** sits behind the driver: a small turbocharged V6 working with an electric
  motor and a battery. It's a *stressed member*, meaning it carries loads like part of the frame.
- The **gearbox** bolts to the back of the engine, and the rear suspension bolts to the gearbox.
- Under it all, the **floor** is the biggest source of downforce on today's cars. Tunnels
  underneath speed the air up, which lowers its pressure and sucks the car to the track.
- At the back, the **diffuser** and **rear wing** finish the job.
""",
        "engineer": """
**The load path.** Forces from the tyres travel through the uprights and suspension arms into
the monocoque at the front and into the gearbox casing at the rear. The engine block carries
those rear loads forward to the monocoque. That's why the engine, gearbox and tub must be
very stiff: if the chassis twists, the suspension stops controlling the tyres precisely.

**Where the downforce comes from.** Since the 2022 rules, the floor's underbody tunnels make
the largest share of the car's downforce, with the wings providing the rest. Floor downforce
costs less drag than wing downforce, and it disturbs the air behind the car less, which
helps following cars.

**Packaging.** Radiators must sit in the sidepods, where cooling air is available, but bigger
radiators mean bigger sidepods, which disturb airflow to the floor and rear. That trade-off
between cooling and aerodynamics shapes every car's bodywork.

**Typical numbers** (2022–2025 rules): minimum mass 798–800 kg with driver, no fuel. Maximum
wheelbase 3,600 mm, width 2,000 mm. 18-inch wheels. Around 1,000 hp from the power unit at
its peak.
""",
        "deep": """
**Stiffness.** Torsional stiffness of a modern F1 chassis is commonly quoted in the tens of
thousands of N·m per degree. What matters is that it's much higher than the suspension's roll
stiffness, so the springs, not the chassis, decide how the car's load moves between tyres.

**Suspension.** Double wishbones at both ends. Push-rod (rod runs from the bottom of the upright
up to the chassis) or pull-rod (from the top of the upright down to the chassis) layouts move
the springs and dampers inboard, out of the airflow. The choice is mostly about packaging and
centre of gravity: pull-rod puts the heavy parts lower.

**Aero platform.** Ground-effect floors are very sensitive to ride height and pitch, so the
suspension's main aerodynamic job is to hold the floor at the right height. That's why teams
run very stiff setups, and why porpoising appeared in 2022 when the floor got too close to the
track (Module 4).

**Systems you don't see:** hydraulics for the gearbox, clutch and steering; a fuel cell holding
up to about 110 kg (2022–2025); electronics running the FIA's standard ECU; cooling circuits
for the engine, battery, gearbox and electronics.
""",
        "widget": W.car_anatomy,
        "widget_blurb": "A generic modern car, part by part.",
        "data": [("Circuit Explorer", "How a car's speed changes round a lap tells you which parts matter most there."),
                 ("Team Performance", "How much each team's car differs, measured from lap times.")],
        "terms": ["monocoque", "halo", "power unit", "ground effect", "diffuser", "downforce"],
        "quiz": [
            ("What are almost all of a car's parts there to do?",
             ["Look good", "Keep the tyres loaded and cut drag, safely", "Save fuel only", "Carry sponsors"], 1,
             "Grip, low drag and safety drive everything."),
            ("Since 2022, the largest source of downforce is…",
             ["the rear wing", "the front wing", "the floor and its tunnels", "the halo"], 2,
             "Ground-effect floors make most of the downforce."),
            ("The rear suspension is mounted on…",
             ["the monocoque", "the gearbox casing", "the rear wing", "the floor"], 1,
             "The gearbox casing carries the rear suspension."),
            ("A 'stressed member' is a part that…",
             ["is under pressure from the team", "carries chassis loads as part of the frame", "breaks often",
              "is made of steel"], 1,
             "The engine carries rear-end loads forward to the tub."),
            ("Why do bigger radiators cost lap time?",
             ["They're heavy and need bigger sidepods that disturb airflow", "They use fuel", "They make noise",
              "They aren't allowed"], 0,
             "Cooling and aerodynamics fight for the same space."),
        ],
        "sources": ["FIA 2022–2025 Formula 1 Technical Regulations, fia.com",
                    "Wright, P. (2001). Formula 1 Technology. SAE International."],
    },
    {
        "id": "1.2",
        "title": "The regulations as a design box",
        "summary": "Rules define the space engineers can design in. In 2026 that space changed shape.",
        "basics": """
A Formula 1 car isn't designed from a blank sheet. The FIA's **technical regulations** run to
well over a hundred pages and fix the car's maximum size, its minimum weight, the shape of the
spaces where bodywork may go, what the engine must be, how much fuel energy it may use, and
much more.

Think of the rules as a **box**. Every team designs inside the same box, and the winner is the
team that uses its corners best. When the box changes, as it did in 2014 (hybrid engines),
2022 (ground-effect floors) and **2026**, everyone starts again, and the order can shuffle.

**2026 in short:** smaller, lighter cars; much more electric power and fully sustainable fuel;
and wings that move, switching between a low-drag setting for straights and a high-downforce
setting for corners.
""",
        "engineer": """
**Why rules exist:** safety (crash tests, the halo, speed limits through the rules), cost
(the budget cap, Module 14), close racing (cars that can follow each other), and relevance
(hybrid engines, sustainable fuel).

**2022–2025 vs 2026, the headline numbers** (from the FIA's published regulations; check the
current issue for later changes):

| | 2022–2025 | 2026 |
|---|---|---|
| Minimum mass (car + driver, no fuel) | 798 → 800 kg | 768 kg |
| Maximum wheelbase | 3,600 mm | 3,400 mm |
| Maximum width | 2,000 mm | 1,900 mm |
| Electric motor (MGU-K) power | 120 kW | 350 kW |
| MGU-H (turbo motor) | yes | removed |
| Fuel | E10 blend | 100 % sustainable |
| Straight-line drag aid | DRS (rear flap) | active front and rear wings |

**The FIA's stated targets** when the 2026 rules were announced (June 2024) were about 30 %
less downforce and 55 % less drag. The demo below applies changes like these to a calibrated
car on our simulator, so you can see what each one does on its own.
""",
        "deep": """
**Reading the rules like an engineer.** The technical regulations define bodywork as
*legality volumes*: 3D zones where bodywork is allowed, with rules on curvature, minimum radii
and how many sections a wing may have. Clever designs come from reading those definitions very
precisely. The double diffuser of 2009 and Mercedes' DAS steering in 2020 were both legal
readings of words that the rule makers hadn't expected to be read that way (Module 15).

**Sporting vs technical rules.** Technical regulations define the car. Sporting regulations
define the weekend: parc fermé, engine allocations, tyre rules, penalties. Financial
regulations set the cost cap. Many engineering decisions (how many power units to plan for,
how much to spend on upgrades) are really sporting or financial decisions.

**Why 2026 needed movable aero.** With less drag and much more of the power coming from a
battery that can't deploy at full power for a whole lap, cars risked running out of electrical
energy on long straights. Cutting drag on the straights (low-drag mode) and adding downforce in
corners (cornering mode) lets a lower-drag car still corner hard.
""",
        "widget": W.regulation_change,
        "widget_blurb": "Apply a rule change to a calibrated car and see what it does to the lap.",
        "data": [("Team Performance", "How the order between cars changed from 2025 to 2026."),
                 ("Lap Simulator", "Compare a 2025 and a 2026 lap at the same circuit.")],
        "terms": ["regulations", "minimum mass", "wheelbase", "MGU-K", "active aero", "drs"],
        "quiz": [
            ("The 2026 minimum mass is about…",
             ["900 kg", "800 kg", "768 kg", "700 kg"], 2,
             "768 kg with the driver, without fuel."),
            ("What happened to the MGU-H in 2026?",
             ["It doubled in power", "It was removed", "It moved to the front axle", "Nothing"], 1,
             "The turbo's motor-generator was dropped to simplify the power unit."),
            ("Why did the 2026 rules add movable wings?",
             ["To look exciting", "To cut drag on straights and keep downforce for corners", "To save weight",
              "For safety only"], 1,
             "Low drag on straights, high downforce in corners."),
            ("Bodywork rules are written as…",
             ["colours", "3D zones where bodywork may go", "a list of team names", "a single maximum weight"], 1,
             "They're called legality volumes."),
            ("Which regulations set the cost cap?",
             ["Technical", "Sporting", "Financial", "Safety"], 2,
             "The FIA's financial regulations."),
        ],
        "sources": ["FIA 2026 Formula 1 Technical Regulations, fia.com",
                    "FIA press release, 6 June 2024: 'FIA unveils Formula 1 regulations for 2026 and beyond'",
                    "FIA Formula 1 Financial Regulations, fia.com"],
    },
    {
        "id": "1.3",
        "title": "Lap-time sensitivities",
        "summary": "What 10 kg, 10 kW, 5 % more downforce or 5 % less drag are worth, track by track.",
        "basics": """
Engineers think in **sensitivities**: how much lap time one small change is worth. A
sensitivity turns arguments ("should we save weight or add downforce?") into numbers.

The same change is worth different amounts at different circuits:

- **Weight** costs everywhere, because the car must accelerate, brake and turn it. It's one of
  the few gains that's always worth having.
- **Power** and **low drag** are worth most where the car spends a long time flat out:
  Monza, Spa, Baku, Las Vegas.
- **Downforce** is worth most where the car spends a long time in fast and medium corners:
  Silverstone, Suzuka, Barcelona.

Teams keep big tables of these numbers for every circuit and use them to decide which upgrade
to bring where, and which wing level to run.
""",
        "engineer": """
**A sensitivity is a derivative.** For a car property $x$:

$$S_x = \\frac{\\partial t_{lap}}{\\partial x} \\approx \\frac{t_{lap}(x + \\Delta x) - t_{lap}(x)}{\\Delta x}$$

The demo below works these out with our simulator: each cell is one extra simulated lap with
one property changed.

**Rules of thumb you'll hear** (they vary with the car and the circuit):

- around **0.02–0.03 s per kg per lap**, which is why race fuel matters (a full tank is up
  to about 110 kg in 2022–2025). Our model gives 0.015–0.026 s per kg across the eight circuits below.
- **10 kW** is worth about 0.3 s a lap at Spa or Suzuka in our model, and under 0.1 s at Monaco
- **downforce and drag trade off**: adding a few per cent of downforce usually costs some drag,
  and the best wing level is where the two effects balance (next chapter)

**Why weight matters twice.** Mass appears in every equation: more mass needs more force to
accelerate and brake, and more sideways force to corner. Downforce doesn't scale with mass,
so a lighter car also gets more grip *per kilogram* from the same downforce.
""",
        "deep": """
**Linear only for small changes.** Sensitivities assume the lap time responds in a straight
line, which holds for small changes. Big changes (a whole new wing level) interact: more
downforce raises corner speeds, which changes how much time is spent on straights, which
changes what power is worth. That's why teams re-run full simulations for big decisions.

**Using sensitivities to choose upgrades.** If a new floor adds 2 % downforce and 0.5 % drag,
its value at a circuit is roughly $2 S_{down} + 0.5 S_{drag}$ (with the right signs). Summing
over the calendar, weighted by how many races are left, gives the upgrade's championship value.
Under the cost cap, teams rank upgrades by **lap time per dollar**.

**Our sensitivities vs real ones.** Our point-mass model leaves out tyre temperature, weight
transfer and energy limits, so its numbers are best read as the *pattern across circuits*.
Where real numbers have been made public, the magnitudes are similar.
""",
        "widget": W.sensitivity_map,
        "widget_blurb": "Time gained per lap from five small changes, on eight very different circuits.",
        "data": [("Setup Garage", "The same sensitivities for any circuit, from any setup you choose."),
                 ("Upgrades", "Where real upgrades showed up in the lap times.")],
        "terms": ["sensitivity", "power", "downforce", "drag", "minimum mass"],
        "quiz": [
            ("A lap-time sensitivity tells you…",
             ["how nervous the driver is", "how much lap time one small change is worth", "the tyre pressure",
              "the fuel used"], 1,
             "It's the change in lap time per unit of change."),
            ("Where is 10 kW of extra power worth the most?",
             ["Monaco", "Hungary", "Monza", "Singapore"], 2,
             "Monza has the most time at full throttle."),
            ("Why is saving weight worth time everywhere?",
             ["Mass appears in accelerating, braking and cornering", "It cools the brakes", "Rules reward it",
              "It doesn't"], 0,
             "Every phase of the lap has to move the mass."),
            ("A common rule of thumb for weight is about…",
             ["0.3 s per kg per lap", "0.03 s per kg per lap", "3 s per kg per lap", "nothing"], 1,
             "Around 0.03 s per kg per lap, varying by circuit."),
            ("Why aren't sensitivities enough for big changes?",
             ["They're secret", "Effects interact when changes are large", "Computers can't do them",
              "Rules forbid it"], 1,
             "They assume a straight-line response, which only holds for small changes."),
        ],
        "sources": ["Milliken, W. F. & Milliken, D. L. (1995). Race Car Vehicle Dynamics, ch. 2. SAE International.",
                    "Our own simulations: lapsim.py, calibrated on OpenF1 fastest laps."],
    },
    {
        "id": "1.4",
        "title": "Monaco or Monza: the design compromise",
        "summary": "Why every car runs a different wing at every track, and why no car is best everywhere.",
        "basics": """
Wings make downforce, and downforce costs drag. More wing means faster corners but slower
straights. So every circuit has a **best wing level**, where the time gained in the corners
equals the time lost on the straights:

- **Monza** is mostly straights. Teams bring special low-drag wings that look almost flat.
- **Monaco** is all slow corners and has no real straight. Teams run the biggest wings they have.
- Most circuits sit in between, and teams bring a few rear-wing designs to cover the range.

The same idea goes far beyond wings. A car designed around fast corners may struggle in slow
ones. A car that's kind to its tyres may be slow over one lap. Every design is a compromise,
and the calendar has 24 different circuits to compromise across.
""",
        "engineer": """
**Finding the best wing.** With wing level $w$ moving both downforce and drag, the lap time is
$t(w)$, and the best wing is where

$$\\frac{dt_{lap}}{dw} = 0$$

The demo sweeps $w$ from 0 to 1, simulating a full lap at each setting, for a power circuit, a
balanced circuit and Monaco. The curves bottom out at very different wing levels.

**Aerodynamic efficiency.** The ratio of downforce to drag, $C_z/C_x$ (also written L/D), says
how much downforce a design gets for its drag. Higher efficiency moves the whole trade-off
curve down. Low-drag wings are usually *less* efficient, but at Monza drag matters most, so
they still win.

**Not just the wing.** Ride height, rake, suspension stiffness and gear ratios are all chosen
per circuit, and they interact with the wing. The Setup Garage lets you try them on our model.
""",
        "deep": """
**Why the optimum is flat.** Near its minimum, $t(w)$ is close to a parabola, so being a little
off the best wing costs very little. Teams often run *more* wing than the lap-time optimum: in
the race it protects tyres (less sliding) and helps in traffic. Or they run less, if top speed
helps defend and overtake. The lap-time optimum is where the conversation starts, not where it ends.

**Car concept and the calendar.** Each design starts from a choice of concept (sidepod shape,
floor philosophy) that suits some kinds of circuit better than others. Teams estimate the
championship value of a concept by simulating the whole calendar, weighting each circuit
equally (every race scores the same points). A car that's very fast at half the circuits and
poor at the rest can still lose a title to one that's consistently second.

**Our model's version.** In the simulator, downforce rises in a straight line with the wing
level and drag rises with its square, the way a wing's *induced drag* grows with the square of
its lift. So the first steps of wing are cheap and the last ones expensive, which is what gives
each circuit its own best wing. Real wings each have their own curve, and the floor's downforce
depends strongly on ride height, so the real trade-off is a surface, not a line.
""",
        "widget": W.compromise,
        "widget_blurb": "Lap time against wing level, from lowest drag (0) to most downforce (1), on three circuits.",
        "data": [("Setup Garage", "Try Monaco's wing at Monza and see the corner-by-corner cost."),
                 ("Lap Simulator", "The 'car the simulator found' panel shows each circuit's fitted wing level.")],
        "terms": ["wing level", "downforce", "drag", "sensitivity"],
        "quiz": [
            ("At the best wing level…",
             ["drag is zero", "time gained in corners equals time lost on straights", "downforce is maximum",
              "the car is slowest"], 1,
             "That's where the lap time is lowest: dt/dw = 0."),
            ("Which circuit uses the lowest-drag wings?",
             ["Monaco", "Hungary", "Monza", "Singapore"], 2,
             "Monza's long straights reward low drag above all."),
            ("Aerodynamic efficiency is…",
             ["downforce ÷ drag", "drag ÷ weight", "speed ÷ power", "wing area"], 0,
             "How much downforce you get per unit of drag."),
            ("Why might a team run more wing than the lap-time optimum in a race?",
             ["To protect tyres and race in traffic", "It's required", "To save fuel", "To slow down"], 0,
             "More downforce means less sliding and better grip when following."),
            ("Why is being slightly off the best wing usually cheap?",
             ["The lap-time curve is flat near its minimum", "Wings don't matter", "Drivers adapt", "It isn't"], 0,
             "Near a minimum, small changes cost almost nothing."),
        ],
        "sources": ["Katz, J. (2006). Race Car Aerodynamics, ch. 1 and 6. Bentley Publishers.",
                    "Our own simulations: lapsim.py wing sweeps on calibrated circuits."],
    },
]
