"""Module 10: Electronics, data and simulation."""
import academy_widgets as W0
import academy_widgets_m8 as W
from academy_content.m4 import ch

SOURCES = ["FIA Formula 1 Technical Regulations, electronic systems and standard ECU articles, fia.com",
           "Segers, J. (2014). Analysis Techniques for Racecar Data Acquisition, 2nd ed. SAE International.",
           "OpenF1 API documentation (car data, laps, location), openf1.org"]

CHAPTERS = [
    ch("10.1", "The standard ECU and around 300 sensors", "One control box for every car, and a car full of sensors.",
       """
Every F1 car runs the same **ECU** (electronic control unit), supplied to all teams since 2008. It runs
the engine, the gearbox, the energy recovery and the data logging, with software the FIA can inspect.
That's how driver aids like traction control stay banned: nobody can hide them in their own electronics.

Around the car are **hundreds of sensors**: temperatures and pressures everywhere in the engine, tyres
and brakes; ride heights; suspension movement; steering angle; pedal positions; accelerations; and
pressure taps on the bodywork in testing.
""",
       """
**What the ECU controls.** Ignition and injection, the throttle (it's drive-by-wire: the pedal asks, the
ECU decides how), the seamless gearshifts (Module 6.1), the brake-by-wire blend (Module 7.2) and the
battery's deployment. Teams write the strategies within the FIA's rules; the hardware and the core software
are common.

**Logging.** Key channels are logged at hundreds of hertz or more; some (vibration, combustion) much
faster. A weekend generates a huge amount of data for every car.
""",
       """
**Why standardise?** In the early 2000s teams' own electronics made traction and launch control
impossible to police, so they were legalised in 2001 and banned again from 2008 together with the
standard ECU. A common ECU also cuts costs: no team needs its own control electronics programme.
""",
       [("Since 2008 every car uses…", ["its own ECU", "the same standard ECU", "no ECU", "two ECUs"], 1, "Supplied to all teams."),
        ("Why does a standard ECU help keep traction control banned?", ["The FIA can inspect the one common system", "It's cheaper", "Weight", "It doesn't"], 0,
         "Nowhere to hide it."),
        ("A modern F1 car carries about…", ["5 sensors", "hundreds of sensors", "no sensors", "a million sensors"], 1, "Temperatures, pressures, positions…"),
        ("The throttle is…", ["a cable", "drive-by-wire: the ECU decides", "manual only", "hydraulic"], 1, "The pedal asks."),
        ("Key channels are logged at…", ["once a lap", "hundreds of hertz or more", "once a minute", "not at all"], 1, "Very fast.")],
       terms=["telemetry"], sources=SOURCES),

    ch("10.2", "Telemetry and the garage", "Data flows from the car to engineers at the track and at the factory.",
       """
While the car runs, its data streams by radio to the garage (**telemetry**) and on to the factory, where
more engineers watch in an operations room. They see tyre temperatures, brake wear, engine health and the
battery's state as it happens, and talk to the race engineer, who talks to the driver.

It's one way only. Since 2003 teams may not send commands to the car: they can see everything, but any
change has to be made by the driver, from the steering wheel, after the engineer asks over the radio.
""",
       """
**What gets watched.** A performance engineer watches lap times and the driver's inputs; a power unit
engineer watches temperatures and energy; a strategist watches gaps and tyre wear. Alarms trigger when a
channel leaves its safe range, which is often the first warning of a failure.

**The car's own log.** Not everything fits down the radio, so the full log is downloaded when the car
returns to the garage.
""",
       """
**Public telemetry.** The data fans can see (OpenF1, from FIA timing) is a thin slice: speed, rpm, gear,
throttle, brake on/off and DRS at a few samples a second, and position from the timing system. The app's
Ghost Lap Duel and Guess the Driver use exactly this, which shows how much can be learned from very
little.
""",
       [("Telemetry flows…", ["from the car to the garage only", "both ways", "never", "from the garage to the car only"], 0,
         "One-way since 2003."),
        ("If an engineer wants a setting changed during a session…", ["they change it remotely", "the driver changes it from the wheel",
                                                                     "nobody can", "they pit"], 1, "After a radio call."),
        ("Factory engineers…", ["watch live data in an operations room", "never see data", "drive the car", "only read reports"], 0,
         "Remote support."),
        ("The full car log is…", ["downloaded when the car returns", "lost", "sent by email", "not kept"], 0, "Too big for the radio link."),
        ("Public data from OpenF1 is sampled at about…", ["a few samples a second", "1,000 Hz", "once a lap", "once a race"], 0,
         "A thin slice.")],
       data=[("Ghost Lap Duel", "Public telemetry overlaid for two drivers.")], terms=["telemetry"], sources=SOURCES),

    ch("10.3", "The steering wheel", "A computer with handles: every setting the driver can change.",
       """
An F1 steering wheel has a screen and dozens of buttons, rotary switches and paddles. From it the driver
changes the brake bias, the differential, engine and energy modes, the radio, the pit-lane speed limiter
and, in 2026, the overtake mode. Behind it are the gearshift paddles and the clutch paddles used at the
start.

Each wheel is made for its driver (the grips moulded to their hands, the buttons where they want them)
and costs about as much as a family car.
""",
       """
**Why so many switches?** The rules ban automatic systems that change the car's balance, so the driver
does it, sometimes several times a lap: brake bias forward for one corner, differential more open for
another, a different energy mode for a straight where they're defending.

**The display** shows lap delta, shift lights, warnings and pages the engineer asks the driver to check:
"go to strat mode 5", "brake bias plus one".
""",
       """
**Human factors.** Every control is a chance for a mistake at 300 km/h. Layout, colour coding, detents on
the rotaries and multi-function "toggles" that change meaning by context are designed with the driver,
tested in the simulator (10.5) and changed between seasons as drivers learn what they use most.
""",
       [("Brake bias is changed…", ["by the team remotely", "by the driver from the wheel", "automatically", "never"], 1, "Often several times a lap."),
        ("Why can't these settings change automatically?", ["Rules ban automatic balance-changing systems", "Too expensive", "Weight", "They can"], 0,
         "The driver does it."),
        ("The clutch paddles are used mainly…", ["at the start and in the pits", "every corner", "never", "for DRS"], 0, "Launches."),
        ("A steering wheel is…", ["standard for all drivers", "made for its driver", "borrowed", "made of wood"], 1, "Moulded grips, custom layout."),
        ("In 2026 the wheel also controls…", ["overtake mode", "the halo", "tyre pressures", "fuel type"], 0, "Replacing DRS.")],
       terms=["brake bias"], sources=SOURCES),

    ch("10.4", "Data analysis like an engineer", "Overlays, deltas and mini-sectors: where is the time?",
       """
The first question after every run is **where the time went**. Engineers overlay two laps (two drivers, or
the same driver before and after a change) on the same distance axis: speed, throttle, brake, gear and
steering. Where the lines separate is where the time is.

The **delta time** trace adds up the difference metre by metre; its slope shows where one lap gains
and where it loses. **Mini-sectors** split the lap into dozens of short pieces and colour each by who was
fastest.
""",
       """
**Reading an overlay.** A later braking point and a higher minimum speed in a corner is the classic gain;
an earlier throttle pick-up on exit is worth even more, because the speed is carried down the next
straight. Delta time: $\\Delta t(s) = t_A(s) - t_B(s)$; where it rises, lap A is losing.

**Sampling.** Public data at a few hertz smooths the peaks: the demo below shows how much a braking peak is
underestimated at low sample rates, which matters when you compare braking.
""",
       """
**Aligning laps.** Laps must be compared on distance, not time, and distance comes from integrating speed
or from position, both noisy. Engineers align laps on corner apexes or GPS markers before comparing, or
the traces drift apart and fake differences appear late in the lap.
""",
       [("Two laps are compared on…", ["distance", "time of day", "lap number", "temperature"], 0, "So corners line up."),
        ("Where the delta-time trace rises, lap A is…", ["gaining", "losing", "equal", "stopped"], 1, "Δt = t_A − t_B."),
        ("Mini-sectors are…", ["short pieces of the lap coloured by who was fastest", "tyre sizes", "radio channels", "fuel stops"], 0,
         "Dozens per lap."),
        ("Why does an earlier throttle pick-up matter so much?", ["The speed carries down the next straight", "It saves fuel", "Rules", "It doesn't"], 0,
         "Exit speed."),
        ("Low sample rates make braking peaks look…", ["bigger", "smaller", "the same", "negative"], 1, "Peaks are missed.")],
       widget=W.sampling, blurb="How sample rate hides the real braking peak.",
       data=[("Ghost Lap Duel", "Two drivers' laps overlaid, with the delta."), ("Guess the Driver", "One lap's traces say who drove it.")],
       sources=SOURCES),

    ch("10.5", "Driver-in-the-loop simulators", "Racing a circuit before arriving, and testing parts that don't exist yet.",
       """
Every top team has a **driver-in-the-loop simulator**: a real cockpit on a motion platform, surrounded by a
wrap-around screen, driven by a computer model of the car. Drivers use it to learn circuits and prepare
setups; engineers use it to try parts and setups before they're built.

Because testing is limited, the simulator is where a lot of the development happens, and reserve drivers
spend many days a year in it.
""",
       """
**The vehicle model.** At its core is a much richer version of the lap simulator in this app: a full
multi-body model with tyres, aero maps, suspension kinematics, the power unit and the driver's inputs,
running in real time. Latency matters: if the motion and picture lag the driver's inputs by more than a few
milliseconds, the car feels wrong and the results don't transfer.

**What it's used for.** Setup sweeps before a race weekend, practising procedures, and judging how a new
part changes the car's balance, which a lap time alone can't show.
""",
       """
**Offline versus online.** The quasi-steady lap simulator used here (Module 3.9) answers "how fast could the
car be?" in seconds. The driver-in-the-loop simulator answers "can a human drive it that fast, and does it
feel right?", which is why teams need both, and why the hardest part is making the model match the real
car (10.6).
""",
       [("A driver-in-the-loop simulator has…", ["a real cockpit and a car model", "only a screen", "a real engine", "no driver"], 0, "On a motion platform."),
        ("Why does latency matter?", ["Lag makes the car feel wrong", "It doesn't", "Rules", "Cost"], 0, "A few milliseconds."),
        ("Teams use simulators a lot because…", ["track testing is limited", "they're cheap", "drivers like games", "rules require it"], 0,
         "Development happens there."),
        ("The quasi-steady lap simulator answers…", ["how fast the car could be", "how it feels", "tyre colour", "nothing"], 0, "Offline."),
        ("Who spends many days in the simulator?", ["Reserve drivers", "Mechanics only", "Nobody", "Fans"], 0, "And race drivers.")],
       widget=W0.lap_equation, blurb="The lap-time equation at the heart of every simulator.",
       data=[("Lap Simulator", "The offline simulator, against the real pole lap.")], terms=["lap simulator"], sources=SOURCES),

    ch("10.6", "Correlation: simulation vs track", "Do the wind tunnel, CFD and simulator agree with the real car?",
       """
Teams design the car in **CFD** (computer airflow simulation), test scale models in the **wind tunnel**,
and drive it in the **simulator**. **Correlation** is the question of whether all of that matches the real
car on track.

When it doesn't, a team can spend months chasing the wrong direction: an upgrade that looked great in the
tunnel makes the car slower, or the balance the simulator promised never appears. Several teams have lost
whole seasons to correlation problems.
""",
       """
**Measuring it.** Teams fit aero rakes (grids of pressure sensors) and flow-visualisation paint to the car
in practice, then compare pressures and ride heights with the tunnel and CFD. Wind-tunnel models are
limited by the rules to 60% scale at up to 50 m/s, so the tunnel never matches the real car exactly:
Reynolds number, tyres and track surface all differ.

**This app does it too.** The lap simulator is calibrated circuit by circuit against the real fastest lap
and its speed trace; the Lap Simulator page shows where it agrees and where it doesn't.
""",
       """
**Why it's hard.** The real car's floor runs millimetres from a bumpy track at changing ride heights, with
tyres deforming and the car pitching under braking. The tunnel has a moving belt but rigid model tyres and
smooth flow. Getting the trends right (does this change help?) matters more than absolute numbers, and
teams invest heavily in tools that measure the real car's aero platform on track.
""",
       [("Correlation asks whether…", ["simulation and tunnel match the real car", "two drivers agree", "the radio works", "fans like it"], 0,
         "Model vs reality."),
        ("Wind-tunnel models are limited to…", ["60% scale, up to 50 m/s", "full size", "10% scale", "no limit"], 0, "By the rules."),
        ("Aero rakes measure…", ["pressures in the airflow", "tyre wear", "fuel", "brake heat"], 0, "Grids of sensors."),
        ("Why might an upgrade make a car slower?", ["Poor correlation", "Paint", "Rules", "It can't"], 0, "The tunnel was wrong."),
        ("What matters most in correlation?", ["Getting trends right", "Exact numbers only", "Colour", "Nothing"], 0, "Does a change help?")],
       data=[("Lap Simulator", "How well our simulator matches the real pole lap.")], sources=SOURCES),
]
