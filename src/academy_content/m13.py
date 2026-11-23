"""Module 13: Circuits."""
import academy_widgets_m13 as W
from academy_content.m4 import ch

SOURCES = ["FIA International Sporting Code, Appendix O: circuit design and licensing, fia.com",
           "FIA Formula 1 Sporting Regulations: race distance, fia.com",
           "Milliken, W. & Milliken, D. (1995). Race Car Vehicle Dynamics. SAE. Chapter 2 on lap-time simulation.",
           "Our own data: every circuit's most recent race, lapsim.py and circuit_tours.py"]

CHAPTERS = [
    ch("13.1", "How circuits differ", "Power, downforce, braking and tyres: every circuit asks for a different car.",
       """
No two circuits ask the same thing of a car. At **Monza** the car is flat out for most of the lap, so
straight-line speed (power and low drag) is everything. At **Monaco** it is never flat out for long,
the corners are slow and close together, and downforce and traction win.

Most circuits sit between those two. Engineers describe a circuit by what it demands:

- **Power:** how much of the lap is spent at full throttle.
- **Downforce:** how many medium and fast corners there are.
- **Braking:** how many hard stops from high speed, which also decides where overtaking happens.
- **Tyre energy:** long fast corners and rough surfaces wear the tyres faster.

The chart below puts every circuit on two of those axes, using what our lap simulator says extra power
and extra downforce are each worth there.
""",
       """
**Sensitivities.** For a small change $\\Delta x$ in one property, the lap time changes by about
$\\frac{\\partial t}{\\partial x}\\,\\Delta x$. The simulator measures this directly: run the lap, change
one thing, run it again. The chart uses 10 kW more power and 5% more downforce.

**Why the ratio matters.** Extra downforce comes with extra drag (a wing's drag grows with its load), so
each circuit has its own best wing level. Where the downforce gain is large compared with the power gain,
the best wing is high; where it is small, the best wing is low. That's why teams bring special low-drag
wings to Monza, Spa and Las Vegas.

**Altitude.** Air density falls about 1% for every 85 m of height. In Mexico City (about 2,240 m) the air
is roughly a fifth thinner, so the car makes less downforce **and** less drag: teams run their biggest
wings and still reach high top speeds.
""",
       """
**From a dot to a design.** A team's season starts with exactly this kind of map. A car that is efficient
(high downforce for its drag) does well everywhere; a car that is "draggy" suffers on the right-hand side
of the chart and recovers on the left. Upgrade plans are often timed to the circuits where they pay most.

**The limits of the map.** It comes from a point-mass simulator with one calibrated car per race, so it
ignores kerbs, bumps, wind, temperature and the tyres' heat. It ranks circuits sensibly; it doesn't give
the exact numbers a team would use.
""",
       [("Which circuit is most about straight-line speed?", ["Monaco", "Monza", "Hungaroring", "Singapore"], 1,
         "Flat out for most of the lap."),
        ("Why can't you just add as much downforce as possible?", ["It's banned", "It comes with extra drag",
                                                                    "It wears the brakes", "It's too heavy"], 1,
         "The best wing level is a balance."),
        ("Mexico City's thin air means…", ["more downforce", "less downforce and less drag", "more drag only",
                                            "no difference"], 1, "About a fifth less air."),
        ("A 'sensitivity' is…", ["how fast the car is", "how much lap time one small change is worth",
                                  "a driver's feel", "a tyre compound"], 1, "Change one thing, rerun the lap."),
        ("Overtaking usually happens…", ["in fast corners", "into hard braking zones after straights",
                                          "on the grid", "in the pit lane"], 1, "Braking zones after long straights.")],
       widget=W.circuit_map, blurb="Every circuit on one chart: what power and downforce are each worth there.",
       data=[("Setup Garage", "The same sensitivities for any circuit, from the car you set up."),
             ("Car DNA", "Which real cars were strong on which kind of circuit.")],
       terms=["sensitivity", "wing level", "downforce", "drag", "air density"], sources=SOURCES),

    ch("13.2", "Circuit tours in 3D", "Ride a lap of any circuit, then go through it corner by corner.",
       """
Pick a circuit and press Play: the camera rides with the lap simulator's car round the real track, with
its real elevation (shown four times higher so the hills are easy to see). The real fastest lap of that
race runs alongside as a ghost.

Below the flyover, every corner is listed with:

- **Apex speed:** the slowest point of the corner, from the simulator and from the real lap.
- **Gear** at the apex.
- **Braking:** where the braking starts, and from what speed.
- **Braking g** and **cornering g:** how hard the car decelerates and how hard it turns.
- **Overtaking spots:** stops from above 270 km/h to below 160 km/h after a long straight.

Last comes the circuit's character: what each kind of upgrade is worth there.
""",
       """
**How a corner is measured.** The apex is the lowest simulated speed within 60 m of the official corner
marker. The braking point is found by walking back from the apex to the last moment the car was flat out
(short bursts of throttle inside a chicane count as the same complex), then forward to the first braking.
Braking g is the hardest deceleration between there and the apex:

$$a_{brake} = \\frac{F_{grip} + F_{drag} + F_{roll}}{m}$$

and at 300 km/h drag alone gives more than 1 g, which is why the hardest braking happens at the top of a
straight.

**Simulator against reality.** Where the real apex is faster than the simulator's, the real car has grip
the point-mass model doesn't (kerbs, a better line, a car balanced for that corner). Where it's slower,
the driver gave the corner a margin, or the real car slid. Module 3.9 builds the simulator step by step.
""",
       """
**Gears.** The gear shown is a display gear from evenly stepped ratios up to the car's top speed (see
Module 6.2); the real gearbox ratios are chosen per circuit.

**What's left out.** No track width or racing line (the car follows the centre line of the fastest lap),
no kerbs, no DRS or overtake mode, no traffic or tyre wear. Corners near each other share a braking zone,
so only the first of them shows the stop.
""",
       [("The apex of a corner is…", ["its fastest point", "its slowest point, near the inside", "the braking point",
                                       "the exit"], 1, "The slowest point."),
        ("Why is braking hardest at the top of a straight?", ["The driver is fresh", "Downforce and drag are largest at high speed",
                                                               "The brakes are cold", "Rules"], 1,
         "Both grow with speed squared."),
        ("An overtaking spot here means…", ["any corner", "a hard stop from high speed after a long straight",
                                             "a fast corner", "the start line"], 1, "Where passes happen."),
        ("If the real apex is faster than the simulator's…", ["the data is wrong", "the real car finds grip the model doesn't",
                                                               "the driver cut the track", "it's raining"], 1,
         "Kerbs, line, balance."),
        ("Elevation in the 3D view is…", ["exact", "shown four times higher", "removed", "random"], 1, "So hills are visible.")],
       widget=W.circuit_tour, blurb="Pick a circuit, press Play, then read it corner by corner.",
       data=[("Circuit Explorer", "Every circuit's shape and elevation, coloured by speed."),
             ("Lap Simulator", "The simulated lap against the real one, with the speed trace.")],
       terms=["apex", "lateral g", "longitudinal g", "lap simulator"], sources=SOURCES),

    ch("13.3", "Historic circuits", "Longer, faster and far more dangerous: how circuits changed.",
       """
The circuits of the 1950s–70s were very different. The **Nürburgring Nordschleife** was over 22 km of
public-road-style track through forests and villages. The original **Spa-Francorchamps** used 14 km of
ordinary roads. The old **Hockenheim** had long straights through a forest, broken by chicanes.

They were spectacular and deadly. After Niki Lauda's crash at the Nordschleife in 1976, F1 left it for
good; old Spa was replaced by today's 7 km layout in 1983; Hockenheim's forest section went in 2002.

Circuits changed for safety: shorter laps (so marshals and medical cars arrive faster), chicanes to slow
the fastest corners, wide run-off areas, gravel traps and energy-absorbing barriers. Many classic corners
survive inside modern layouts: Eau Rouge at Spa, the Parabolica at Monza, Copse at Silverstone.
""",
       """
**Why shorter laps.** A rescue vehicle covering 22 km is slow to reach an accident; a 5 km lap has
marshal posts and medical cover within sight of every point. Today's rules ask new circuits to be between
about 3.5 and 7 km long, with Monaco kept as a special case.

**Chicanes.** A chicane cuts the speed into a dangerous corner and adds a braking zone, which also creates
an overtaking chance. Monza added its chicanes in the 1970s for exactly this reason.

**Run-off.** Gravel slows a car quickly but can flip it; asphalt run-off lets a driver recover but can be
abused for time, which is why track-limits rules appeared.
""",
       """
**Rebuilding them.** There's no telemetry from the old days, but the roads are still mapped. The Historic
Circuits page rebuilds the Nordschleife, the old Hockenheim and the 14 km old Spa from OpenStreetMap with real elevation, and the
lap simulator drives a 1975, a 2001 and a 2026 car round them. Each older car has one tuned number (its tyre
grip), set so it matches a real pole lap of its era; everything else is the same physics as today's circuits.

**The trade-off.** Safety improvements made racing far less lethal; critics argue that wide asphalt run-off
also made mistakes cheaper. Circuit designers now mix gravel back in at key corners.
""",
       [("The Nordschleife was about…", ["5 km", "7 km", "22 km", "14 km"], 2, "Over 22 km."),
        ("F1 left the Nordschleife after…", ["1958", "1976", "1994", "2001"], 1, "Lauda's crash."),
        ("Why are modern laps shorter?", ["Cheaper tickets", "Rescue and marshals arrive faster", "Fuel rules", "TV only"], 1,
         "Safety coverage."),
        ("A chicane is added to…", ["make the lap longer", "slow a dangerous corner", "save fuel", "help pit stops"], 1,
         "Cuts speed, adds a braking zone."),
        ("A downside of asphalt run-off is…", ["it's expensive", "mistakes cost less time", "it's slippery", "nothing"], 1,
         "Track limits.")],
       data=[("Historic Circuits", "The Nordschleife, the old Hockenheim and the old Spa in 3D, with three eras of car racing round."),
             ("Circuit Profiles", "Every track that has held a Grand Prix, and who has won there."),
             ("Eras", "How the sport changed decade by decade.")],
       terms=["lap simulator"], sources=SOURCES),

    ch("13.4", "Designing a circuit", "Draw a track and see what kind of racing it makes.",
       """
Designing a circuit is a balance between speed, safety, overtaking and the land you have. Long straights
into slow corners make overtaking spots; fast sweepers test the cars' downforce but make following hard;
tight sections slow the average speed and favour traction.

Try it below: drag the points, add more by tapping the track, and watch the lap simulator drive your
circuit as you draw. It counts the braking zones and the overtaking spots, and warns you when the track is
outside the usual length range or a corner is extremely tight.
""",
       """
**A good overtaking spot** needs three things: a long full-throttle run (so the car behind can use the
tow, and DRS or overtake mode), a hard stop from high speed (so braking later gains a lot), and a slow
corner (so the cars arrive side by side). The designer marks a spot when the speed falls from above
270 km/h to below 160 km/h after 500 m of full throttle.

**Average speed** is a safety number as much as a racing one: the faster the corners, the more run-off
they need.
""",
       """
**The real process.** Circuit designers work to the FIA's Appendix O: track width, corner radii, run-off
dimensions, barrier types, pit lane, sight lines. They simulate the expected speeds (with tools like this
one, and full vehicle models), then check every corner's run-off against the speed and angle a car could
leave it at.
""",
       [("A good overtaking spot needs…", ["a fast corner", "a long straight into a hard stop for a slow corner",
                                            "a chicane on a straight", "a long pit lane"], 1, "Tow, braking, slow corner."),
        ("Faster corners need…", ["less run-off", "more run-off", "no barriers", "narrower track"], 1, "More energy to absorb."),
        ("The FIA rules for circuit design are in…", ["the Technical Regulations", "Appendix O", "the cost cap", "the Sporting Code only"], 1,
         "Appendix O."),
        ("Fast sweeping corners tend to make following…", ["easier", "harder", "the same", "illegal"], 1, "Dirty air."),
        ("Many tight corners favour cars with good…", ["top speed", "traction and downforce", "fuel economy", "brakes only"], 1,
         "Slow corners.")],
       widget=W.designer_widget, blurb="Drag the points. The lap simulator drives your circuit as you draw.",
       data=[("Circuit Designer", "The same tool on its own page, with a choice of season's car.")],
       terms=["lap simulator", "curvature"], sources=SOURCES),
]
