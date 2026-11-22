"""Module 6: Transmission and drivetrain."""
import academy_widgets_m4 as W
from academy_content.m4 import ch

SOURCES = ["Wright, P. (2001). Formula 1 Technology, ch. on transmissions. SAE International.",
           "FIA Formula 1 Technical Regulations, transmission articles, fia.com"]

CHAPTERS = [
    ch("6.1", "The seamless-shift gearbox", "Eight gears, changed in milliseconds without a gap in drive.",
       """
An F1 gearbox has eight forward gears and one reverse. The driver changes gear with paddles behind the
steering wheel; there's no clutch pedal once the car is moving. The gearbox is **seamless-shift**: the
next gear engages a fraction of a millisecond before the current one disengages, so the drive to the
wheels never stops.

The gearbox casing is also part of the car's structure: the rear suspension and the rear crash
structure bolt directly to it.
""",
       """
**How seamless works.** Two gears are briefly engaged at once on separate selector mechanisms, and the
engine's torque is controlled for a few milliseconds while the old gear releases. The result is a change
with essentially no interruption in torque, worth hundredths per lap compared with a conventional shift.

**Materials.** Casings are carbon fibre or titanium for stiffness and low weight; gears are small and
narrow, run hot, and must survive several race weekends (gearboxes have their own allocation rules).
""",
       """
**Hydraulics and control.** Shifts are made by hydraulic actuators commanded by the standard ECU, with
strict rules preventing automatic shifting: the driver must request each change.

**Fixed ratios.** Since 2014 each team nominates one set of gear ratios for the whole season, so ratios
can't be tailored to each track. Choosing them is a calendar-wide compromise (next chapter).
""",
       [("How many forward gears does an F1 car have?", ["5", "6", "8", "10"], 2, "Plus reverse."),
        ("Seamless shift means…", ["no gearbox", "no gap in drive during a change", "automatic shifting", "a clutch pedal"], 1,
         "The next gear engages before the last releases."),
        ("The gearbox casing also carries…", ["the front wing", "the rear suspension", "the radiators", "the driver"], 1,
         "It's structural."),
        ("Can F1 cars shift gears automatically?", ["Yes", "No, the driver must request each change", "Only in the wet", "Only in qualifying"], 1,
         "Driver-requested."),
        ("Since 2014 gear ratios are…", ["changed every race", "fixed for the whole season", "unlimited", "chosen by Pirelli"], 1,
         "One nominated set.")],
       sources=SOURCES),

    ch("6.2", "Choosing gear ratios", "One set of ratios for every circuit: a season-long compromise.",
       """
Gear ratios decide how fast the car can go in each gear. Too short a top gear and the car hits the
rev limiter on long straights; too long and it accelerates slowly and never uses the top of the rev
range. Close spacing keeps the engine in its best rev band; wide spacing covers more speed range.

Because teams must pick one set for the whole season, they pick ratios that work acceptably everywhere,
from Monaco's 50 km/h hairpin to Monza's 350 km/h straights. Top speed at each track is then tuned with
wing level instead.
""",
       """
**Spacing.** Roughly geometric spacing (each gear a fixed percentage taller than the last) keeps the
engine's revs dropping by the same amount at every shift. The demo builds eight evenly spaced gears and
checks whether the circuit's fastest point fits.

**Gearing and the energy era.** With turbo hybrids the engine's useful rev range is narrower and the
MGU-K adds torque low down, which changes the ideal spacing compared with the V10 era.
""",
       """
**First gear and starts.** First gear is set by the race start and the slowest hairpins; too tall and
starts suffer, too short and the driver changes up almost immediately. **Eighth gear** is set by the
fastest circuits in the tow, with the slipstream and DRS (or 2026 active aero) adding speed.
""",
       [("Too short a top gear means…", ["more top speed", "hitting the rev limiter on straights", "better starts only", "nothing"], 1,
         "No more speed available."),
        ("Why can't teams change ratios for each track?", ["One set per season is nominated", "Gearboxes are sealed", "Cost only",
                                                           "They can"], 0, "Since 2014."),
        ("What tunes top speed per track instead?", ["Tyres", "Wing level", "Fuel", "Brakes"], 1, "Drag sets the speed."),
        ("Geometric spacing means…", ["each gear a fixed percentage taller", "equal speed steps", "random", "two gears only"], 0,
         "Even rev drops."),
        ("First gear is mainly set by…", ["the start and slowest hairpins", "top speed", "fuel", "weather"], 0, "Monaco's hairpin.")],
       widget=W.gear_ratios, blurb="Eight evenly spaced gears: does the circuit's fastest point fit?", sources=SOURCES),

    ch("6.3", "Clutch and launch", "The race start: the one time the driver uses a clutch.",
       """
The clutch is only used to get the car moving: at the start, after a pit stop, and out of the garage.
It's a small, multi-plate carbon clutch operated by a paddle on the steering wheel.

A **race start** is a test of grip and control: the driver holds the revs, finds the clutch's bite
point, and releases it when the lights go out, without wheelspin or bogging down. Traction control is
banned, so it's all in the driver's hands, helped by settings the team prepares from practice starts.
""",
       """
**Bite point.** Engineers find the clutch position where it starts to transmit torque and set paddle
maps so the driver can release from there. Too much torque and the rear tyres spin; too little and the
engine bogs down. Track temperature, tyre temperature and the grid surface all change the right setting.

**Lap One** in this app shows what happens next: places gained and lost by the end of lap 1, which a good
launch strongly affects.
""",
       """
**Rules against launch control.** Electronic launch control and traction control have been banned since
2008, with the standard ECU policing it. Clutch maps must respond directly to the driver's paddle, so
small differences in skill and practice show up in the start.
""",
       [("When is the clutch used?", ["Every gear change", "Only to get the car moving", "Under braking", "Never"], 1,
         "Starts, pit stops, garage."),
        ("The bite point is…", ["a corner", "where the clutch starts to transmit torque", "a tyre mark", "a rule"], 1, "Found in practice."),
        ("Too much torque at the start causes…", ["wheelspin", "a stall", "a penalty", "nothing"], 0, "Rear tyres spin."),
        ("Launch control in F1 is…", ["mandatory", "banned", "optional", "only in the wet"], 1, "Since 2008."),
        ("Which page shows lap-one gains?", ["Lap One", "Tyre Lab", "Engine Room", "Quiz"], 0, "Places gained on lap 1.")],
       data=[("Lap One", "Places gained and lost by the end of the first lap.")], sources=SOURCES),

    ch("6.4", "Driveshafts, uprights and hubs", "Taking the torque to the wheels and holding them in place.",
       """
From the gearbox, **driveshafts** carry the torque out to the rear wheels, flexing with the suspension
through constant-velocity joints. Each wheel spins on a **hub** inside an **upright**, the part that
holds the bearings, the brakes and the suspension mounts.

The uprights take every force the tyre makes: braking, cornering and the weight and downforce of the
car. They're machined from metal or made of carbon composite, light but extremely stiff, because any
flex changes the tyre's angles.
""",
       """
**Stiffness matters.** Under several tonnes of load, flex in uprights and bearings changes camber and
toe (Module 3.4's compliance), which the tyre feels. Teams design and test uprights on rigs to control it.

**Brake ducts** are mounted on the uprights, and their shape is also aerodynamic: they guide air around
the wheel and affect the floor, so the corner assembly is a joint mechanical and aero design.
""",
       """
**Wheel nuts and pit stops.** A single centre-locking nut holds each wheel, with retention devices that
stop a wheel coming off if the nut isn't tight. The whole corner design must allow a wheel change in about
two seconds.
""",
       [("Driveshafts carry torque from…", ["the engine to the front wheels", "the gearbox to the rear wheels", "the battery to the wing",
                                            "the steering to the wheels"], 1, "Through CV joints."),
        ("An upright holds…", ["the driver", "bearings, brakes and suspension mounts", "the engine", "the fuel"], 1, "The wheel's carrier."),
        ("Why must uprights be stiff?", ["Flex changes the tyre's angles", "Looks", "Noise", "Rules only"], 0, "Compliance."),
        ("Brake ducts also matter for…", ["aerodynamics", "fuel", "radio", "steering"], 0, "They guide air around the wheel."),
        ("How many nuts hold each wheel?", ["One centre nut", "Four", "Five", "None"], 0, "For fast pit stops.")],
       data=[("Pit and Strategy", "How quick each team is in the pit box.")], sources=SOURCES),
]
