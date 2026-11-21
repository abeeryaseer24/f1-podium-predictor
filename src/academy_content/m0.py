"""Module 0: Start here."""
import academy_widgets as W

CHAPTERS = [
    {
        "id": "0.1",
        "title": "How to use the Academy",
        "summary": "What the course covers, the three depths, and how the live demos work.",
        "basics": """
The Engineering Academy explains how a modern Formula 1 car works and how a race is engineered,
from the tyres up. It starts with school physics and builds to the level of a university
motorsport module.

**Three depths, one page.** The *Depth* switch at the top of every chapter changes how far it goes:

- **Basics**: no maths. What it is and why it matters.
- **Engineer**: everything in Basics, plus the equations and real numbers.
- **Deep dive**: everything above, plus derivations, the limits of each model, and where to read more.

You can switch at any time; the app remembers your choice while you're here.

**Everything is live.** Most chapters have a *Try it* panel. It isn't an animation: it runs
the same physics engines as the Simulator pages, on real circuits measured from real laps.
Change a number and the whole lap is simulated again.

**Everything links to real data.** *In the real data* tells you where to see each idea in the
rest of the app: Tyre Lab, Ghost Lap Duel, Pit Wall and the others.

**Check yourself.** Each chapter ends with five questions. Nobody sees your answers but you.
""",
        "engineer": """
**How the course is built.** Modules go from the contact patch outwards: tyres (Module 2),
then how the car moves on them (3), then the air around it (4), the power unit (5), and the
rest of the machine (6 to 10). Then come the people and decisions: race engineering (11),
strategy (12), circuits (13), the rules and money (14), and history (15). Module 16 is a
capstone where you design a car and race it.

**Units.** The course uses SI units throughout: metres, seconds, kilograms, newtons (N),
watts (W). Speeds are shown in km/h because that's what F1 uses, but every equation uses m/s.
Divide km/h by 3.6 to get m/s.
""",
        "deep": """
**About the models.** Every simulation in the Academy is a *teaching model*: simple enough to
explain fully, checked against real data, and honest about what it leaves out. Each one says
what it ignores. Real teams use far bigger models (multi-body vehicle dynamics, CFD with
billions of cells, tyre models fitted to rig data), but those are built on exactly the ideas
explained here.

**Sources.** Numbers come from the FIA's published regulations, from teams' and suppliers'
public technical material, from textbooks, and from our own measurements on OpenF1 data.
Estimates are marked as estimates. If something looks wrong, the About page says how to tell us.
""",
        "terms": ["telemetry", "lap simulator"],
        "quiz": [
            ("What does the Engineer depth add to Basics?",
             ["Nothing, it replaces it", "The equations and real numbers", "Only videos", "A harder quiz"], 1,
             "Each depth keeps everything from the one before and adds to it."),
            ("Where do the Try it demos get their results?",
             ["Pre-recorded animations", "The same physics engines as the Simulator pages",
              "Random numbers", "Team data"], 1,
             "The demos run lapsim.py, the same engine as Lap Simulator and Setup Garage."),
            ("To turn 288 km/h into m/s you…",
             ["multiply by 3.6", "divide by 3.6", "divide by 60", "multiply by 1,000"], 1,
             "1 m/s is 3.6 km/h, so 288 km/h is 80 m/s."),
            ("Which module covers the air around the car?",
             ["Module 2", "Module 4", "Module 7", "Module 12"], 1,
             "Module 4 is aerodynamics."),
            ("What does every Academy model tell you?",
             ["Its source code only", "What it leaves out", "Which team it copies", "Nothing"], 1,
             "Every simulation lists what it ignores, so you know how far to trust it."),
        ],
        "sources": ["FIA Formula 1 Technical Regulations (current issue), fia.com",
                    "OpenF1 API documentation, openf1.org"],
    },
    {
        "id": "0.2",
        "title": "The physics you need",
        "summary": "Force, mass, energy, power and pressure: the five ideas behind everything else.",
        "basics": """
You need only a handful of ideas to understand a racing car.

**Force makes things speed up, slow down or turn.** A car corners because its tyres push it
sideways. It brakes because the tyres push backwards. Without force, it would carry straight on.

**Mass resists change.** A heavier car needs more force to do the same thing. That's why teams
fight for every kilogram.

**Energy is what the engine spends and the brakes throw away.** Every time the car slows from
300 km/h to 100 km/h, most of its energy of motion turns into heat in the brakes. Since 2014 F1
cars have recovered some of it electrically.

**Power is how fast you can spend energy.** At high speed, power is what decides how hard the
car can still accelerate.

**Air pushes.** At speed, air pressure on the car's wings and floor is enormous. Shaped the right
way, it pushes the car into the road (*downforce*), which lets the tyres grip harder. The price
is *drag*, the air holding the car back.
""",
        "engineer": """
**Newton's second law** ties force, mass and acceleration together:

$$F = m\\,a$$

A 800 kg car braking at 5 g (5 × 9.81 m/s²) needs about **39 kN** of braking force.

**Cornering.** To follow a curve of radius $r$ at speed $v$, the car needs a sideways
acceleration of

$$a_{lat} = \\frac{v^2}{r} = v^2\\,\\kappa$$

where $\\kappa = 1/r$ is the *curvature*. At Copse (Silverstone), roughly 290 km/h (80 m/s)
through a radius of about 160 m, that's 40 m/s², **about 4 g**.

**Energy of motion** (kinetic energy):

$$E = \\tfrac{1}{2} m v^2$$

At 320 km/h (89 m/s) an 800 kg car carries about **3.2 MJ**. Braking to 80 km/h turns about
3 MJ into heat in under three seconds: more than a megawatt.

**Power and driving force.** At speed $v$, an engine of power $P$ can push with

$$F_{drive} = \\frac{P}{v}$$

so the same 700 kW gives 31 kN at 80 km/h but only 7.9 kN at 320 km/h. That's why
acceleration fades as speed rises.

**Downforce and drag** both grow with the square of speed:

$$F_{down} = \\tfrac{1}{2}\\rho\\,C_zA\\,v^2 \\qquad F_{drag} = \\tfrac{1}{2}\\rho\\,C_xA\\,v^2$$

$\\rho$ is the air density (about 1.2 kg/m³ at sea level), and $C_zA$ and $C_xA$ are the car's
downforce and drag coefficients multiplied by its frontal area. The demo below uses these.
""",
        "deep": """
**Why "the square of speed"?** In a time $t$ a car at speed $v$ hits a column of air with mass
$\\rho A v t$ and changes its momentum by an amount proportional to $v$. Force is the rate of
change of momentum, so it scales with $\\rho A v^2$. The coefficients $C_z$ and $C_x$ capture
everything about the shape. They're almost constant over the speeds a car runs at, which is
why this simple form works so well. (They do change with ride height and yaw, covered in
Module 4.)

**Where top speed comes from.** At top speed, all the power goes into beating drag and rolling
resistance:

$$P = \\tfrac{1}{2}\\rho\\,C_xA\\,v^3 + C_{rr}\\,N v$$

Because of the cube, 10 % more power gives only about 3 % more top speed.

**Thin air.** Air density falls roughly exponentially with altitude, with a scale height of
about 8.5 km. At Mexico City (2,240 m) it's about 23 % lower than at sea level: less downforce
and less drag for the same wing. Teams run their biggest wings there and still have less
downforce than at Monaco. Turbochargers make up most of the lost engine power.

**Units check.** $\\tfrac{1}{2}\\rho C_zA v^2$ has units kg/m³ × m² × m²/s² = kg·m/s² = N. ✓
""",
        "widget": W.downforce_calculator,
        "widget_blurb": "Downforce against speed. Find the speed where downforce equals the car's weight.",
        "data": [("Lap Simulator", "The 'car the simulator found' panel gives each circuit's downforce at 250 km/h."),
                 ("Circuit Explorer", "Mexico City's elevation: the whole circuit is over 2.2 km up.")],
        "terms": ["downforce", "drag", "power", "kinetic energy", "curvature", "lateral g", "air density"],
        "quiz": [
            ("If a car goes twice as fast, its downforce becomes about…",
             ["the same", "twice as big", "four times as big", "eight times as big"], 2,
             "Downforce grows with speed squared: 2² = 4."),
            ("The sideways acceleration needed in a corner is…",
             ["v × r", "v² ÷ r", "r ÷ v", "m × r"], 1,
             "a = v²/r, or v² times the curvature."),
            ("Why does acceleration fade at high speed even at full power?",
             ["The engine gets tired", "Driving force = power ÷ speed, and drag grows",
              "Tyres get colder", "The air gets thinner"], 1,
             "The same power gives less force at higher speed, while drag rises with v²."),
            ("Mexico City's thin air means, for the same wing…",
             ["more downforce", "less downforce and less drag", "more drag only", "no change"], 1,
             "Both forces are proportional to air density."),
            ("Kinetic energy at 320 km/h for an 800 kg car is roughly…",
             ["32 kJ", "320 kJ", "3.2 MJ", "32 MJ"], 2,
             "½ × 800 × 89² ≈ 3.2 million joules."),
        ],
        "sources": ["Katz, J. (2006). Race Car Aerodynamics. Bentley Publishers.",
                    "Milliken, W. F. & Milliken, D. L. (1995). Race Car Vehicle Dynamics. SAE International.",
                    "International Standard Atmosphere, ISO 2533:1975."],
    },
    {
        "id": "0.3",
        "title": "What makes a car fast",
        "summary": "A lap is thousands of tiny pieces. Each one is limited by power, grip or braking.",
        "basics": """
A lap time is just the track's length divided by the car's speed, piece by piece. Cut the
track into thousands of short pieces, work out how fast the car can go on each, and add up
the time.

On every piece, one of three things sets the limit:

1. **On the straights: power and drag.** The car is flat out, and how fast it gains speed
   depends on its engine against the air holding it back.
2. **In the corners: grip.** The tyres can only push so hard sideways. Downforce adds grip,
   so the faster the corner, the more the wings help.
3. **Into the corners: braking.** The car brakes as late as its tyres allow. Drag helps here.

That gives you the three ways to make a car faster: **more power or less drag**, **more grip**
(better tyres, more downforce, less weight), and **better braking**. Each circuit has a
different mix, which is why no car is best everywhere.
""",
        "engineer": """
**The lap-time integral.** If $v(s)$ is the speed at distance $s$ round a lap of length $L$:

$$t_{lap} = \\int_0^L \\frac{ds}{v(s)}$$

Slow sections count for more than you'd think, because time is distance *divided* by speed.
Gaining 1 km/h in a 70 km/h hairpin saves more time per metre than gaining 1 km/h at 300 km/h.

**The three limits**, for a car of mass $m$ with grip coefficient $\\mu$:

*Corner limit*: the tyres can supply $\\mu N$ sideways, where $N = mg + \\tfrac{1}{2}\\rho C_zA v^2$
is the vertical load. Setting that equal to $m v^2 \\kappa$:

$$m v^2 \\kappa = \\mu\\left(mg + \\tfrac{1}{2}\\rho C_zA v^2\\right)
\\;\\Rightarrow\\; v_{max} = \\sqrt{\\frac{\\mu m g}{m\\kappa - \\tfrac{1}{2}\\mu\\rho C_zA}}$$

If the bottom is zero or negative, downforce grows faster than the grip needed: in theory
that corner is flat out at any speed.

*Acceleration*: $m\\,a = \\min\\!\\left(\\frac{P}{v},\\; \\mu_{rear} N_{rear}\\right) - \\tfrac{1}{2}\\rho C_xA v^2 - C_{rr}N - mg\\sin\\theta$

*Braking*: $m\\,a_{brake} = \\mu N + \\tfrac{1}{2}\\rho C_xA v^2 + C_{rr}N + mg\\sin\\theta$

The car's speed is the lowest of the three limits at every point. That's exactly what the
Lap Simulator does, every 4 m.
""",
        "deep": """
**The friction circle.** A tyre has one budget of grip to share between turning and braking
or accelerating. With $a_{lat}$ used for cornering, what's left for braking is

$$a_{long} = a_{grip}\\sqrt{1 - \\left(\\frac{a_{lat}}{a_{grip}}\\right)^2}$$

so a driver braking into a corner is trading the two all the way to the apex. This is called
*trail braking*. Module 2 covers it properly.

**Quasi-steady-state.** Treating each point as if the car were in a steady state there ignores
how the car got there: no weight transfer, no yaw inertia, no suspension. It's surprisingly
good, typically within a few per cent of the real lap time once tuned, because most of a lap
is spent close to one of the three limits. Teams used this method as their main lap simulator
into the 1990s and still use it for quick studies.

**The forward–backward algorithm.** Find every corner's limit speed. Run forward from the
slowest corner, accelerating as hard as possible and capping at each corner limit. Run
backward from the same point, braking as hard as possible. The speed everywhere is the lower
of the two runs. That's a few thousand arithmetic steps, about 3 ms in Python.
""",
        "widget": W.lap_equation,
        "widget_blurb": "One simulated lap, coloured by what limits the car at each point.",
        "data": [("Lap Simulator", "The same three colours on the 3D track, with the real lap beside it."),
                 ("Setup Garage", "Change power, wing or grip and see which parts of the lap change.")],
        "terms": ["lap simulator", "quasi-steady-state", "friction circle", "grip", "friction coefficient"],
        "quiz": [
            ("Which limits the car in the middle of a long straight?",
             ["Tyre grip", "Power and drag", "Braking", "Steering"], 1,
             "Flat out, the engine is fighting the air."),
            ("Why do slow corners matter so much for lap time?",
             ["They're longer", "Time = distance ÷ speed, so slow sections cost more time per metre",
              "Drivers make more mistakes", "They use more fuel"], 1,
             "Each metre at 70 km/h takes over four times as long as a metre at 300 km/h."),
            ("Adding downforce raises the corner limit because…",
             ["it lowers the car's mass", "it adds vertical load on the tyres without adding mass",
              "it reduces drag", "it cools the tyres"], 1,
             "More load means more grip, and downforce gives load without mass."),
            ("The friction circle says that braking hard while turning…",
             ["gives more grip", "leaves less grip for turning", "has no effect", "only matters in the wet"], 1,
             "Grip is shared between the two directions."),
            ("A quasi-steady-state simulator ignores…",
             ["the track shape", "downforce", "weight transfer and suspension", "power"], 2,
             "It treats the car as a point with no suspension or yaw."),
        ],
        "sources": ["Siegler, B., Deakin, A. & Crolla, D. (2000). Lap time simulation: comparison of steady state, "
                    "quasi-static and transient racing car cornering strategies. SAE 2000-01-3563.",
                    "Brayshaw, D. (2004). The use of numerical optimisation to determine on-limit handling behaviour "
                    "of race cars. PhD thesis, Cranfield University."],
    },
    {
        "id": "0.4",
        "title": "Reading telemetry",
        "summary": "Speed, throttle and brake traces: how engineers read a lap at a glance.",
        "basics": """
Every F1 car carries around 300 sensors and sends their readings to the garage many times a
second. That's **telemetry**. Engineers spend hours a day looking at it, and the first three
channels they look at are almost always the same:

- **Speed.** The shape of the lap. Peaks are the ends of straights, dips are corners. The
  lowest dips are the slowest corners.
- **Throttle**, 0 to 100 %. Flat at the top means full throttle. Where it drops, the driver
  is lifting or braking. A smooth climb out of a corner shows the driver feeding in power
  without spinning the rear tyres.
- **Brake.** On and off. The length of each braking zone tells you how much speed the car is
  losing there.

Lay one driver's lap over another's and the differences jump out: who brakes later, who gets
on the throttle earlier, who carries more speed through the middle of the corner.
""",
        "engineer": """
**Reading the speed trace.** The *slope* of the speed trace is the car's acceleration. Steep
falls are braking: a modern car can lose 200 km/h in under 3 seconds, around 5 g. Gentle
climbs at high speed show power fading against drag. A flat bottom means a long, constant-radius
corner taken at the grip limit.

**Minimum speeds.** The lowest point of each corner sets how quickly the car can accelerate
away, so a few km/h at the *apex* is worth time all the way down the next straight.

**The delta.** Overlaying two laps on *distance* (not time) lines up the corners, and a
running time difference ("delta") shows exactly where the time is won and lost. The Ghost Lap
Duel page does this.

**Sampling.** OpenF1's car data comes at about 3.7 samples a second; team systems log key
channels at hundreds or thousands of hertz. At 300 km/h, 3.7 Hz is one sample every 22 m,
which is why the traces here look a little stepped.
""",
        "deep": """
**Brake channel quirks.** In public data the brake channel is close to binary (on/off), so
you can't read brake pressure or how the driver releases the brake. Teams see pressures,
temperatures and brake-by-wire torque for each axle.

**Deriving more channels.** From speed alone you can work out longitudinal acceleration
($dv/dt$). From position you can work out curvature, and from that lateral acceleration
$v^2\\kappa$. Plotting one against the other gives a *g-g diagram*, the shape of the car's
friction circle. Module 2 builds one from real data.

**Common traps.** Laps from different sessions aren't comparable without thinking about fuel
load (about 0.03 s per kg per lap), tyre age, track evolution (grip rises over a weekend as
rubber goes down), wind and traffic.
""",
        "widget": W.telemetry_reader,
        "widget_blurb": "A real fastest lap: speed, throttle and brake against distance.",
        "data": [("Ghost Lap Duel", "Two drivers' telemetry overlaid, with a running delta."),
                 ("Circuit Explorer", "The same lap's speed and gear painted on the 3D track.")],
        "terms": ["telemetry", "throttle", "apex", "longitudinal g"],
        "quiz": [
            ("On a speed trace, a steep fall means…",
             ["the car is accelerating", "the car is braking", "the car has stopped", "DRS is open"], 1,
             "Steep falls are braking zones."),
            ("Why compare two laps on distance rather than time?",
             ["It's shorter", "It lines up the corners", "Time isn't recorded", "Rules require it"], 1,
             "On distance, both laps are at the same corner at the same x position."),
            ("A higher minimum speed in a corner helps…",
             ["only in that corner", "all the way down the next straight", "only in qualifying", "nothing"], 1,
             "The car starts the next straight faster, so it's faster all along it."),
            ("At 300 km/h, data sampled 3.7 times a second has a point roughly every…",
             ["2 m", "22 m", "220 m", "1 km"], 1,
             "83 m/s ÷ 3.7 ≈ 22 m."),
            ("A g-g diagram plots…",
             ["speed against time", "lateral against longitudinal acceleration", "throttle against brake",
              "gear against speed"], 1,
             "Its outline shows the car's friction circle."),
        ],
        "sources": ["Segers, J. (2014). Analysis Techniques for Racecar Data Acquisition, 2nd ed. SAE International.",
                    "OpenF1 API documentation: car_data and location endpoints, openf1.org"],
    },
]
