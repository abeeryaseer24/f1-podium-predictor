"""Module 4: Aerodynamics."""
import academy_widgets as W1
import academy_widgets_m3 as W3
import academy_widgets_m4 as W

SOURCES = ["Katz, J. (2006). Race Car Aerodynamics. Bentley Publishers.",
           "Anderson, J. D. (2016). Fundamentals of Aerodynamics, 6th ed. McGraw-Hill.",
           "Toet, W. (2013). Aerodynamics and aerodynamic research in Formula 1. The Aeronautical Journal 117(1187)."]


def ch(id, title, summary, basics, engineer, deep, quiz, widget=None, blurb="", data=None, terms=None, sources=None):
    return {"id": id, "title": title, "summary": summary, "basics": basics, "engineer": engineer, "deep": deep,
            "widget": widget, "widget_blurb": blurb, "data": data or [], "terms": terms or [],
            "quiz": quiz, "sources": sources or SOURCES}


CHAPTERS = [
    ch("4.1", "Pressure and Bernoulli", "Why fast-moving air pushes less, and how a car turns that into downforce.",
       """
Air is always pushing on everything with about one atmosphere of pressure, roughly 10 tonnes on every
square metre. A racing car doesn't create force from nothing: it creates a small **difference** in
pressure between its top and bottom surfaces.

The key idea is **Bernoulli's principle**: where air speeds up, its pressure drops. Shape a surface
so the air underneath moves faster than the air on top, and the car is pushed down. Wings do it with
their curved shape; the floor does it by squeezing the air through a narrow gap above the track.

The pressure differences involved are tiny compared with the atmosphere (a few per cent), but spread
over a whole car at 300 km/h they add up to more than the car's own weight.
""",
       """
**Bernoulli's equation** along a streamline (incompressible, no losses):

$$p + \\tfrac12\\rho v^2 = \\text{constant}$$

So if the air under the floor moves at $k$ times the car's speed $v$, the pressure there drops by

$$\\Delta p = \\tfrac12\\rho v^2 (k^2 - 1)$$

At 250 km/h with $k = 1.35$, that's about 2.4 kPa (2.4 % of an atmosphere). Over 2.5 m² of floor:
roughly 6 kN of downforce. The **pressure coefficient** $C_p = (p - p_\\infty)/(\\tfrac12\\rho v^2)$
describes a shape independently of speed, which is why downforce scales with $v^2$.
""",
       """
**Where Bernoulli applies.** It holds along streamlines outside boundary layers, where viscosity can
be ignored. It doesn't explain *why* the air speeds up: that comes from the shape forcing the flow to
turn (pressure gradients and continuity). In practice engineers use Bernoulli to read results and CFD
or wind tunnels to get them.

**Compressibility.** At 300 km/h the Mach number is about 0.25, so air density changes by only a few
per cent around the car: incompressible methods work well, a big simplification compared with aircraft.
""",
       [("Where air speeds up, its pressure…", ["rises", "drops", "stays the same", "doubles"], 1, "Bernoulli."),
        ("Downforce comes from…", ["a pressure difference between top and bottom", "heavy wings", "engine thrust", "magnets"], 0,
         "A small difference over a large area."),
        ("Atmospheric pressure is roughly…", ["10 kg per m²", "10 tonnes per m²", "1 tonne per m²", "100 tonnes per m²"], 1,
         "About 101 kPa."),
        ("Why does downforce scale with v²?", ["Bernoulli's ½ρv² term", "Tyres heat up", "Engine power", "Gravity"], 0,
         "Pressure differences scale with dynamic pressure."),
        ("At 300 km/h F1 air flow is…", ["supersonic", "nearly incompressible", "turbulent only", "a vacuum"], 1,
         "Mach about 0.25.")],
       widget=W.bernoulli_floor, blurb="Pressure drop and downforce from air speeding up under a floor.",
       data=[("Lap Simulator", "Downforce at 250 km/h for every calibrated circuit.")], terms=["downforce"]),

    ch("4.2", "Boundary layers and the Reynolds number", "The thin layer of air that sticks to the car decides drag and separation.",
       """
Right at the car's surface the air is stuck to it, not moving at all. A few millimetres away it's
moving at full speed. That thin region in between is the **boundary layer**, and most of an F1 car's
aerodynamic problems happen there.

If the boundary layer runs into rising pressure (for example on the back of a wing or in a diffuser)
it can slow down so much that it **separates**: it lifts off the surface, the flow breaks into
eddies, downforce is lost and drag rises. Keeping flow attached is half of aerodynamic design.

The **Reynolds number** says whether a flow behaves more like honey (smooth, viscous) or like a
river in flood (turbulent). F1 cars live firmly in the turbulent world.
""",
       """
$$Re = \\frac{\\rho v L}{\\mu}$$

with $L$ a length (a wing's chord, the car's length) and $\\mu$ the air's viscosity. A front-wing
element at 250 km/h has $Re$ around 1.4 million; the whole car about 20 million. Boundary layers
usually turn turbulent around $Re \\approx 5\\times10^5$.

**Turbulent vs laminar.** A laminar boundary layer has less skin friction but separates easily. A
turbulent one has more friction but mixes energy from the outer flow down to the wall, so it resists
separation better. Vortex generators and slots deliberately energise boundary layers.

**Wind tunnels.** F1 tunnels use models up to 60 % scale at up to 50 m/s, so their Reynolds numbers
are lower than the real car's. Correlating tunnel results to the track is a constant problem.
""",
       """
**Adverse pressure gradient.** Separation happens where pressure rises along the flow faster than the
boundary layer's momentum can overcome. Diffusers, wing trailing edges and the rear of sidepods are all
adverse-gradient regions; their shapes are limited by how much pressure recovery the boundary layer
tolerates.

**Slotted wings.** Multi-element wings let fresh high-energy air through the slot between elements,
restarting the boundary layer on each element. That's why F1 wings have several elements, and why the
rules limit how many.
""",
       [("The boundary layer is…", ["the edge of the track", "the thin layer of air slowed by the surface", "the floor", "a rule"], 1,
         "Air at the surface doesn't move relative to it."),
        ("Flow separation causes…", ["more downforce", "lost downforce and more drag", "nothing", "cooler tyres"], 1,
         "The flow lifts off the surface."),
        ("The Reynolds number compares…", ["inertia with viscosity", "lift with drag", "speed with power", "mass with grip"], 0,
         "ρvL/μ."),
        ("Why do wings have several elements?", ["Looks", "The slots re-energise the boundary layer", "Weight", "Cost"], 1,
         "Each element restarts its boundary layer."),
        ("F1 wind-tunnel models may be at most…", ["10 % scale", "60 % scale", "full size only", "200 %"], 1,
         "At up to 50 m/s.")],
       widget=W.reynolds_calc, blurb="Reynolds number for any part at any speed."),

    ch("4.3", "Lift, drag and efficiency", "Every wing makes downforce and drag together. Efficiency is the ratio.",
       """
Anything that makes downforce also makes **drag**. Angle a wing more steeply and it pushes harder,
but it also holds the car back more, and past a certain angle the flow separates and the wing
**stalls**: downforce collapses while drag keeps rising.

**Aerodynamic efficiency** is downforce divided by drag (often written L/D). An efficient car gets a
lot of downforce for little drag, which makes it fast everywhere. Teams chase efficiency more than
raw downforce, because extra downforce bought with lots of drag only helps in corners.
""",
       """
**Thin-aerofoil theory** gives the lift slope $C_L \\approx 2\\pi\\alpha$ for small angles. A real,
finite wing loses some of that to tip vortices, and pays **induced drag**:

$$C_D = C_{D0} + \\frac{C_L^2}{\\pi e\\,AR}$$

$C_{D0}$ is drag at zero lift, $e$ an efficiency factor, $AR$ the aspect ratio (span²/area). Induced
drag grows with the **square** of lift, which is why each extra step of wing costs more drag than the
last, the same shape our lap simulator uses for its wing level.

**Car-level numbers** (typical published estimates): $C_zA$ about 3–6 m², $C_xA$ about 1–1.9 m²,
so whole-car efficiency of roughly 3–4.
""",
       """
**Low aspect ratio.** F1 wings are short and wide in chord, constrained by the rules, so they have low
aspect ratios and large tip vortices. Endplates and the shape of the wing tips control those vortices,
and the vortices themselves are used to steer airflow (4.8).

**Stall and hysteresis.** Once a wing stalls, the angle must drop well below the stall angle before the
flow reattaches. The same behaviour in the floor is what drives porpoising (4.11).
""",
       [("Downforce and drag…", ["can be separated freely", "come together", "cancel out", "are unrelated"], 1,
         "Any lifting surface makes both."),
        ("Aerodynamic efficiency is…", ["drag ÷ downforce", "downforce ÷ drag", "speed ÷ power", "weight ÷ area"], 1, "L/D."),
        ("Induced drag grows with…", ["lift", "lift squared", "the square root of lift", "nothing"], 1, "C_L² / (π e AR)."),
        ("A stalled wing…", ["makes more downforce", "loses downforce while drag rises", "has no drag", "cools down"], 1,
         "Flow separates."),
        ("Whole-car efficiency for an F1 car is roughly…", ["0.5", "3–4", "20", "100"], 1, "Downforce a few times the drag.")],
       widget=W.wing_polar, blurb="A wing's lift and drag against angle of attack."),

    ch("4.4", "The front wing", "The first thing the air meets: front downforce, and steering the airflow for the rest of the car.",
       """
The front wing makes downforce on the front axle, which is essential for the car to turn in. But its
bigger job is **conditioning the airflow** for everything behind it. The front tyres are huge, spinning,
messy obstacles: the front wing's shape and its endplates direct air around them (*outwash*) or under
them, and set up the flow for the floor.

Because downforce on the front wing changes the car's balance, teams can adjust the wing's flap angle
at pit stops to fine-tune understeer and oversteer.
""",
       """
**Ground effect on the wing.** The front wing runs close to the ground, so it's itself partly a
ground-effect device: closer to the track means more downforce, until it stalls. Its height changes
with pitch under braking, so its downforce shifts during the lap.

**Rules since 2022** simplified the wing (fewer elements, a nose connection and endplates designed to
send air *inwards*, not out around the car) to make the wake less disruptive for following cars.

**Y250 vortex.** Before 2022, a strong vortex shed from the inner end of the wing, about 250 mm from the
car's centreline, was steered along the car to seal and energise the floor. The 2022 rules removed it.
""",
       """
**Aeroelasticity.** Wings bend under load. The FIA's deflection tests load the wing statically, but
under real aerodynamic load a cleverly laid-up wing can flex in ways that reduce drag at speed. This is
a recurring grey area, policed with stricter tests and on-car camera checks.

**Sensitivity to the car in front.** The front wing is the first to suffer in dirty air, which is a big
reason following cars understeer (4.10).
""",
       [("The front wing's biggest job is…", ["holding the nose cone", "conditioning airflow for the rest of the car", "cooling",
                                             "advertising"], 1, "Downforce plus flow control."),
        ("Outwash means…", ["sending air outwards around the front tyres", "washing the car", "air under the car", "drag"], 0,
         "The 2022 rules restricted it."),
        ("Adjusting the front flap at a stop changes…", ["engine power", "the car's balance", "tyre pressure", "fuel"], 1,
         "More front downforce reduces understeer."),
        ("The Y250 vortex came from…", ["the rear wing", "the inner end of the front wing", "the diffuser", "the halo"], 1,
         "About 250 mm from the centreline."),
        ("Why does a following car often understeer?", ["The front wing loses the most in dirty air", "Rules",
                                                         "Tyres", "Brakes"], 0, "It meets the wake first.")],
       widget=W.wing_polar, blurb="The same lift and drag trade-off applies to every front-wing element.",
       data=[("Dirty Air Lab", "How much downforce a following car loses.")], terms=["downforce"]),

    ch("4.5", "Rear wing, beam wing and DRS", "Rear downforce, the drag it costs, and the flap that opened on straights.",
       """
The **rear wing** makes downforce on the rear axle, balancing the front, and works with the
**beam wing** (a lower element, reintroduced in 2022) to help pull air out of the diffuser underneath.

Rear wings make a lot of drag. From 2011 to 2025, a driver within one second of the car ahead at a
detection point could open a flap in the rear wing on certain straights: **DRS**, the Drag Reduction
System, worth roughly 10–15 km/h. In 2026 DRS was replaced by **active aero**, where both front and
rear wings change between a low-drag straight mode and a high-downforce corner mode for every car.
""",
       """
**Wing levels.** Teams bring several rear-wing designs: almost flat for Monza and Las Vegas, steep for
Monaco and Hungary, and medium for most tracks. The best one for a circuit is where the time gained in
corners equals the time lost on straights (Module 1.4).

**Upwash and the diffuser.** The rear wing's low-pressure underside draws flow upwards from the diffuser
exit, helping the diffuser work harder. The beam wing strengthens that coupling.

**DRS effect.** Opening the flap stalls the upper element, cutting both drag and rear downforce, which is
why it was only allowed on straights.
""",
       """
**2026 active aero.** With less downforce and more electric power, drag had to fall sharply on
straights for the cars to reach sensible speeds with the battery available (see the Energy Lab). Both
wings move together, under strict rules on when each mode may be used.

**Flexing wings.** Rear wings that bend back at speed to shed drag (2021's "bendy wing" debate) led to
new load tests and camera checks.
""",
       [("The beam wing helps…", ["the front wing", "the diffuser pull air out", "the engine", "steering"], 1,
         "It strengthens the diffuser's flow."),
        ("DRS was worth roughly…", ["1 km/h", "10–15 km/h", "100 km/h", "nothing"], 1, "On the straights where it was allowed."),
        ("What replaced DRS in 2026?", ["Nothing", "Active aero for every car", "Bigger wings", "Push-to-pass only"], 1,
         "Straight mode and corner mode."),
        ("Opening the DRS flap…", ["stalls the upper element, cutting drag and downforce", "adds downforce", "adds power",
                                   "cools the brakes"], 0, "Only allowed on straights."),
        ("Which circuit uses the flattest rear wings?", ["Monaco", "Hungary", "Monza", "Singapore"], 2, "Long straights.")],
       widget=W1.compromise, blurb="Lap time against wing level on three circuits (from Module 1.4).",
       data=[("Energy Lab", "Active aero and the battery on 2026 cars.")], terms=["drs", "active aero", "wing level"]),

    ch("4.6", "The floor and ground effect", "Since 2022, most of the downforce comes from underneath the car.",
       """
Underneath a modern F1 car are two large **tunnels** (called Venturi tunnels) that narrow and then
widen again. Air entering at the front speeds up through the narrowest point, the *throat*, which
lowers its pressure and sucks the car towards the track. This is **ground effect**.

Ground effect is efficient: lots of downforce for little drag, and it leaves a cleaner wake for
following cars than big wings do. That's why the 2022 rules brought it back, 40 years after it was
first banned.

The catch: the floor's downforce depends strongly on how high it runs. Too low and the flow stalls.
""",
       """
**Venturi effect.** By continuity, $A_1 v_1 = A_2 v_2$: halving the area between floor and track
doubles the air speed there, and by Bernoulli the pressure falls by $\\tfrac12\\rho v^2(k^2 - 1)$.

**Ride-height sensitivity.** As the gap closes, downforce rises steeply until the boundary layers on
the floor and on the track grow together and the throat chokes: the floor stalls. Cars run as low as
the stall, the plank-wear rules and porpoising allow (Module 3.6).

**Edges.** The floor's edges must stop high-pressure air from the sides leaking in. Edge wings and
vortices form an "air skirt" since physical skirts are banned.
""",
       """
**History.** Lotus's 78 and 79 (1977–78) used shaped floors with sliding skirts sealing the sides.
Cornering speeds rose so fast that skirts were banned and, from 1983, flat floors were mandatory. The
2022 rules allowed tunnels again, under strict geometry rules and a minimum ride-height regime policed
by plank wear.

**2026.** The floor was flattened further and its edges simplified, cutting peak downforce and making the
cars less sensitive to ride height.
""",
       [("Ground effect works by…", ["air speeding up under the car, lowering pressure", "heavy floors", "fans", "magnets"], 0,
         "The Venturi effect."),
        ("The narrowest part of a Venturi tunnel is the…", ["throat", "diffuser", "plank", "skirt"], 0, "Where air is fastest."),
        ("Why did the 2022 rules bring back ground effect?", ["Cheaper", "Efficient downforce with a cleaner wake", "Louder cars",
                                                              "Lighter cars"], 1, "Better for following."),
        ("When were flat floors made mandatory?", ["1950", "1983", "2009", "2022"], 1, "After the first ground-effect era."),
        ("Too low a ride height makes the floor…", ["grip more forever", "stall", "lighter", "cooler"], 1, "And causes porpoising.")],
       widget=W3.ride_height_demo, blurb="An illustrative floor's downforce against ride height, with its lap time.",
       data=[("Porpoising Lab", "What happens when the floor stalls at speed.")], terms=["ground effect", "downforce"]),

    ch("4.7", "Diffuser and floor edges", "Slowing the air back down without losing it, and sealing the sides.",
       """
At the back of the floor the tunnels sweep upwards into the **diffuser**. Its job is to slow the fast
underbody air back down to normal speed gradually, so it can leave the car smoothly. The better the
diffuser recovers that pressure, the faster the air can run under the rest of the floor, and the more
downforce the whole floor makes.

Along the sides, the **floor edges** stop air from the sides leaking in and filling the low-pressure
region underneath. Without physical skirts, designers use carefully shaped edges and vortices as an
invisible seal.
""",
       """
**Pressure recovery.** A diffuser is an expanding channel with rising pressure along it, an adverse
gradient (4.2). Expand too quickly and the boundary layer separates; too slowly and the diffuser is too
long. The *expansion ratio* and angle are limited by both the rules and separation.

**Coupling with the rear wing.** The rear wing's low-pressure underside and the beam wing pull flow up out
of the diffuser exit, letting it expand more aggressively without separating.
""",
       """
**The 2009 double diffuser.** Brawn GP, Toyota and Williams found that the rules allowed a second deck
of diffuser above the first through holes in the floor's step. It was legal, Brawn won the title, and
the trick was banned from 2011.

**Exhaust-blown diffusers (2010–2013).** Teams aimed hot exhaust gas into the diffuser's edges to seal
and energise it, even mapping the engine to keep blowing off the throttle. The rules then fixed the
exhaust position.
""",
       [("A diffuser's job is to…", ["speed air up", "slow underbody air down smoothly", "cool brakes", "steer"], 1,
         "Pressure recovery."),
        ("Expanding a diffuser too quickly causes…", ["more downforce", "separation", "more power", "noise"], 1,
         "An adverse gradient the boundary layer can't handle."),
        ("Floor edges act as…", ["skirts made of air", "brakes", "radiators", "mirrors"], 0, "Physical skirts are banned."),
        ("Which team won the 2009 title with a double diffuser?", ["Ferrari", "McLaren", "Brawn GP", "Red Bull"], 2,
         "Banned from 2011."),
        ("Exhaust-blown diffusers used…", ["fans", "hot exhaust gas", "water", "batteries"], 1, "2010–2013.")],
       data=[("Car DNA", "Fast-corner speed reflects how well a car's floor works.")], terms=["diffuser", "ground effect"]),

    ch("4.8", "Vortices as tools", "Spinning air that seals, steers and energises the flow.",
       """
A **vortex** is a tube of air spinning like a tornado. Every wing tip makes one, because high-pressure
air wraps around from one side to the other. On an F1 car, vortices aren't just a by-product: they're
tools.

A vortex can act as an invisible wall, keeping air from leaking under the floor. It can carry energy
into a tired boundary layer so it stays attached. And because it holds together for a long way
downstream, it can steer air precisely to where the designers want it.
""",
       """
**How they form.** Any surface making lift has a pressure difference across it; at its ends air flows
from high to low pressure, rolling into a vortex. Their strength scales with the lift being made.

**Uses on an F1 car:** floor-edge vortices sealing the underbody; vortices from the front wing and the
floor's leading edge steering flow around the front tyres; small vortex generators energising boundary
layers ahead of separation-prone regions.

**Vortex breakdown.** Under strong adverse pressure a vortex can suddenly burst into turbulence, losing
its usefulness, a key reason underbody designs are so sensitive.
""",
       """
**Ride height and yaw.** A vortex's path moves with the car's attitude. When the car pitches, rolls or
yaws, the vortices move, and the seal they provide can be lost suddenly, one reason the 2022–2025 cars
were so sensitive to setup.

**The 2022 philosophy.** The rules tried to reduce the dependence on strong, fragile vortices so the
cars would lose less downforce in another car's wake.
""",
       [("A vortex is…", ["a type of tyre", "spinning tube of air", "a pressure sensor", "a radiator"], 1, "Like a small tornado."),
        ("Wing-tip vortices form because…", ["air flows from high to low pressure around the tip", "engines blow", "tyres spin",
                                             "rules require them"], 0, "Pressure difference across the wing."),
        ("A floor-edge vortex can…", ["seal the underbody", "heat the brakes", "add power", "nothing"], 0, "An air skirt."),
        ("Vortex breakdown means…", ["the vortex strengthens", "it bursts into turbulence", "it cools", "it disappears safely"], 1,
         "Under strong adverse pressure."),
        ("Vortex generators help by…", ["energising boundary layers", "adding weight", "making noise", "cooling"], 0,
         "Delaying separation.")],
       terms=["downforce"]),

    ch("4.9", "Sidepods and cooling inlets", "Where the radiators breathe, and how the bodywork guides air to the floor and rear.",
       """
The **sidepods** hold the radiators that cool the engine, battery and gearbox. Their inlets must take
in enough air to cool everything, and their shape guides the air flowing along the car towards the
rear wing, the beam wing and the top of the diffuser.

Teams have tried very different ideas since 2022: tiny "zero" sidepods, deep scooped "downwash" pods,
and wide "bathtub" pods. Each changes how air reaches the floor edges and the rear of the car. The
compromise is always between cooling and aerodynamics: more cooling means bigger openings and more drag.
""",
       """
**Cooling drag.** Air passing through a radiator loses momentum, and that loss is drag. Teams open or
close louvres on the bodywork per circuit: maximum cooling for hot races like Singapore, minimum for
cool, fast tracks.

**Downwash concept.** Sidepods that slope steeply downwards guide air towards the beam wing and diffuser
top, helping the rear of the car. **Outwash and the floor edge.** Undercut sidepods leave room for air
to flow along the floor edge, strengthening the edge vortices that seal the underbody.
""",
       """
**Heat rejection.** A power unit at about 50 % efficiency turns roughly as much fuel energy into heat as
into work. Much of that goes out of the exhaust, but hundreds of kilowatts still have to pass through
the radiators, which is why the 2026 power units, with more electric power and batteries needing
cooling, changed sidepod design again (Module 9).
""",
       [("Sidepods mainly hold…", ["fuel", "radiators", "the driver", "tyres"], 1, "Cooling for engine, battery and gearbox."),
        ("More cooling usually means…", ["less drag", "more drag", "more downforce", "no change"], 1, "Bigger openings."),
        ("Louvres on the bodywork are opened for…", ["cold races", "hot races", "qualifying", "rain"], 1, "More cooling."),
        ("A 'downwash' sidepod guides air towards…", ["the front wing", "the beam wing and diffuser", "the halo", "the tyres only"], 1,
         "Helping the rear."),
        ("Why does a radiator create drag?", ["The air loses momentum passing through it", "It's heavy", "Rules", "It doesn't"], 0,
         "Cooling drag.")],
       data=[("Lap Simulator", "Drag at 300 km/h for the calibrated car at every circuit.")]),

    ch("4.10", "Dirty air", "Why following another car is hard, and how the 2022 rules tried to fix it.",
       """
Behind a racing car is a messy, swirling **wake**. A car following through it gets slower, more
turbulent air with less energy. Its wings and floor make less downforce, it slides more, its tyres
overheat, and it can't stay close enough through corners to attempt a pass.

On straights the wake helps: less drag (the **tow** or slipstream) means more speed. So a following car
loses out in corners and gains on straights.

The 2022 rules were designed around this: ground-effect floors and simpler wings that throw the wake
upwards, so the car behind keeps much more downforce.
""",
       """
**FIA figures.** When the 2022 rules were launched, the FIA said a 2021 car kept about 65 % of its
downforce three car-lengths (about 20 m) behind another, and 53 % at one length (about 10 m). The new
cars were designed to keep about 96 % and 82 %.

**Why the old cars suffered.** Their downforce relied on delicate vortices and outwash around the
front wing, which the incoming turbulence wrecked. The 2022 cars send the wake upwards in a narrower
plume, and depend more on the floor.

The demo uses the FIA's figures; the Dirty Air Lab turns them into lap time.
""",
       """
**After 2022.** Teams gradually clawed back outwash and more complex flow structures, and the
following problem returned partly by 2024–25. The FIA aimed to protect following performance again in
the 2026 rules.

**Tyres in the wake.** Losing downforce means more sliding, so a following car's tyres heat up faster,
which can end an overtaking attempt even if the aero loss is small.
""",
       [("Behind another car, a car loses…", ["drag in corners", "downforce", "power", "weight"], 1,
         "Its wings and floor work less well."),
        ("The tow on straights gives…", ["more drag", "less drag and more speed", "more downforce", "nothing"], 1, "The slipstream."),
        ("A 2021 car one car-length behind kept about…", ["90 %", "53 %", "20 %", "100 %"], 1, "FIA figure."),
        ("The 2022 cars aimed to keep about … at one car-length", ["53 %", "82 %", "30 %", "100 %"], 1, "FIA design target."),
        ("Why do tyres overheat when following?", ["Less downforce means more sliding", "Exhaust heat", "Brakes", "Rain"], 0,
         "Sliding heats rubber.")],
       widget=W.dirty_air_mini, blurb="Downforce kept at any distance behind another car, 2017–21 vs 2022+.",
       data=[("Dirty Air Lab", "The lap time a following car loses at every gap.")], terms=["downforce", "drag"]),

    ch("4.11", "Porpoising", "Why the 2022 cars bounced down the straights.",
       """
When ground-effect cars returned in 2022, many of them bounced violently down the straights:
**porpoising**, named after the way porpoises leap through waves.

Here's the cycle: as speed rises, downforce pushes the car down. The floor gets closer to the track
and makes even more downforce, pulling it lower still. At some point the floor gets too close, the air
underneath **stalls**, and downforce suddenly drops. The car springs up, the flow reattaches, the
downforce returns and pulls it down again, several times a second.

It's not just uncomfortable: drivers complained of back pain and blurred vision, and the FIA stepped in
for safety.
""",
       """
**A self-excited oscillation.** The car is a mass on springs pushed by a force that depends on ride
height. Normally downforce rising as height falls is a negative stiffness, reducing the effective
spring. When the floor stalls and recovers with a time lag and hysteresis (stalling at one height,
reattaching at a higher one), each cycle can put energy *into* the motion. Damping removes energy; if
the floor adds more than the dampers remove, the bounce grows until the plank hits the track.

**Fixes:** stiffer springs (less compression), higher ride height (stay above the stall), more
damping, and floors designed to stall more gently, each costing some downforce.
""",
       """
**Bouncing vs porpoising.** Engineers distinguish aerodynamic porpoising (the floor stalling) from
mechanical bouncing (stiff cars hitting bumps), though they mix in practice.

**The FIA's response.** A 2022 technical directive (TD039) introduced a vertical-oscillation metric that
cars had to stay within, and the 2023 rules raised the floor edges and stiffened the floor to reduce
the problem.
""",
       [("Porpoising is caused by…", ["the floor stalling and recovering", "soft tyres", "engine vibration", "wind"], 0,
         "A self-excited aero oscillation."),
        ("Raising the ride height…", ["makes porpoising worse", "can stop it, at a cost in downforce", "has no effect",
                                     "adds power"], 1, "Stay above the stall."),
        ("Damping helps because it…", ["adds downforce", "removes energy from the motion", "lowers the car", "cools the floor"], 1,
         "If it removes more than the floor adds, the bounce dies."),
        ("Hysteresis here means…", ["the floor stalls and reattaches at different heights", "the tyres wear", "drag rises",
                                    "nothing"], 0, "Part of what keeps the cycle going."),
        ("The FIA's response in 2022 was…", ["banning floors", "a vertical-oscillation limit", "slower cars", "nothing"], 1,
         "TD039.")],
       widget=W.porpoise_mini, blurb="Ride height down a straight: when does the floor start bouncing?",
       data=[("Porpoising Lab", "The full version: springs, damping, the floor and five setups.")], terms=["ground effect"]),

    ch("4.12", "Aero maps", "Downforce, drag and balance as the car pitches, rolls, yaws and moves up and down.",
       """
A car's downforce isn't one number. It changes with **ride height** at the front and rear, with
**roll** in corners, with **yaw** (the car pointing slightly sideways to the airflow when it slides or
in a crosswind), and with **steering** (the front wheels turning disturbs the flow).

An **aero map** is a big table of downforce, drag and balance for every combination. Engineers use it
to understand how the car behaves through every part of a corner: braking (nose down), turn-in
(rolling and yawing), mid-corner and exit (nose up under acceleration).
""",
       """
**Balance migration.** As the car pitches under braking, the front gets closer to the ground and the
aero balance moves forward; under acceleration it moves back. A car whose balance moves a lot through
a corner is hard to drive, even if its peak downforce is high. Teams design for a **stable platform**
as much as for peak numbers.

**Yaw sensitivity.** In slow corners cars run large yaw angles and their downforce can drop sharply,
one reason some cars are strong in fast corners and weak in slow ones (see Car DNA).
""",
       """
**Building the map.** Wind tunnels move the model through ride heights, yaw and roll on a motion
system while a rolling road simulates the track. CFD fills in conditions the tunnel can't reach, like
dirty air. The map then feeds the vehicle model and the driver-in-the-loop simulator.

**Using it in setup.** Engineers choose springs and ride heights to keep the car in the best region of
the map at every phase of the lap, the link between Module 3's suspension and Module 4's aerodynamics.
""",
       [("An aero map shows…", ["the track layout", "downforce, drag and balance against the car's attitude", "fuel use",
                                "the team's factory"], 1, "Ride heights, roll, yaw and steer."),
        ("Yaw means…", ["the car pointing slightly sideways to the airflow", "pitching forward", "rolling", "bouncing"], 0,
         "Sliding or crosswind."),
        ("Under braking the aero balance usually moves…", ["forward", "backward", "nowhere", "up"], 0, "The nose dives."),
        ("A 'stable platform' means…", ["a stiff chassis", "aero balance that doesn't move much through a corner", "a big wing",
                                        "low fuel"], 1, "Easier to drive at the limit."),
        ("Why are some cars strong in fast corners but weak in slow ones?", ["Yaw and ride-height sensitivity of their aero",
                                                                              "Engine power", "Tyres", "Fuel"], 0,
         "Slow corners mean big yaw angles.")],
       data=[("Car DNA", "Slow-, medium- and fast-corner speeds for every car.")]),

    ch("4.13", "CFD and the wind tunnel", "How teams test aerodynamics, and why the rules limit how much they can.",
       """
Teams develop aerodynamics two ways. **Wind tunnels** blow air over a scale model on a moving road,
measuring forces precisely. **CFD** (computational fluid dynamics) simulates the airflow on
supercomputers, showing every detail of the flow that a tunnel can't see.

Both are expensive, so the rules limit them. Since 2021 the **Aerodynamic Testing Restrictions**
(ATR) give teams a sliding scale: the team that finished last in the championship gets the most wind
tunnel time and CFD, the champions the least. It's a handicap system to help close up the field.
""",
       """
**Tunnel limits.** Models up to 60 % scale, wind speed up to 50 m/s, and a set number of "runs" and
hours per testing period. **CFD limits** are measured in computing units.

**Correlation.** Neither tool is the real car. The tunnel's lower Reynolds number, rolling-road
imperfections, tyre models and CFD's turbulence models all introduce errors. Teams measure the real car
with pressure taps, flow-visualisation paint and rakes of sensors to check their tools agree:
*correlation*. Poor correlation is behind many teams' failed upgrades.
""",
       """
**Turbulence models.** Practical CFD solves the Reynolds-averaged equations (RANS) with turbulence
models, or uses more expensive scale-resolving methods (DES/LES) for wakes. The choice is a trade
between accuracy and how many design variations a team can test within its allocation.

**The cost cap connection.** With spending capped (Module 14), teams also choose whether to spend on
tunnel upgrades, CFD hardware, or manufacturing parts. Aero testing restrictions and the cap together
shape the whole development race.
""",
       [("CFD stands for…", ["Car Force Data", "Computational Fluid Dynamics", "Central Floor Design", "Cooling Flow Duct"], 1,
         "Simulating airflow on computers."),
        ("Under the ATR, the team that finished last gets…", ["the least testing", "the most testing", "no testing", "the same"], 1,
         "A sliding scale."),
        ("Wind-tunnel models may be up to…", ["10 % scale", "60 % scale", "100 %", "200 %"], 1, "At up to 50 m/s."),
        ("Correlation means…", ["drivers agreeing", "the simulation and the real car agreeing", "two teams merging", "fuel matching"], 1,
         "Checking the tools against the track."),
        ("Why might an upgrade fail on track?", ["Poor correlation between tools and reality", "Paint colour", "Rules", "Weather only"], 0,
         "The tunnel or CFD didn't match the car.")],
       sources=SOURCES + ["FIA Formula 1 Sporting Regulations, Appendix on Aerodynamic Testing Restrictions, fia.com"]),

    ch("4.14", "2026 active aero", "Wings that move: a low-drag straight mode and a high-downforce corner mode.",
       """
From 2026, every car's front and rear wings move. On straights, the wings flatten into a
**low-drag straight mode**; before corners they return to a **high-downforce corner mode**. It
replaces DRS, which only one car at a time could use and only to attack.

The reason is energy. The 2026 power units get about half their power from a battery that can't
deploy at full power for a whole lap. With less drag on the straights, the cars don't burn through
their electrical energy as fast and don't run out of speed before the braking zone.
""",
       """
**The trade-off.** Cutting drag on straights raises top speed and saves battery energy for the same
lap. In corner mode the car keeps the downforce it needs for grip. The Energy Lab shows the effect
with the battery modelled: try it on a power circuit like Monza with active aero on and off.

**Why both wings.** Flattening only the rear wing (as DRS did) shifts the car's aero balance forward,
destabilising it. Moving front and rear together keeps the balance closer to constant.
""",
       """
**Control and safety.** The FIA defines where each mode may be used and when the wings must return to
corner mode, with fail-safes if an actuator fails. The design challenge is making the switch fast and
reliable, and keeping the car stable in the transition at high speed.

**Overtaking in 2026.** With active aero for everyone, overtaking help comes from an extra electrical
"overtake mode" for a car close behind, a power boost rather than a drag cut.
""",
       [("2026 active aero replaced…", ["the halo", "DRS", "ground effect", "the beam wing"], 1, "For every car, every lap."),
        ("Straight mode…", ["adds downforce", "cuts drag", "adds weight", "cools brakes"], 1, "Wings flatten."),
        ("Why did 2026 cars need less drag on straights?", ["Battery energy runs out at full deploy", "Rules for noise",
                                                            "Tyres", "Cost"], 0, "Half the power is electric."),
        ("Why move both wings, not just the rear?", ["To keep the aero balance steady", "Cost", "Looks", "Weight"], 0,
         "Rear-only shifts balance forward."),
        ("Overtaking help in 2026 comes mainly from…", ["DRS", "an electrical overtake mode", "a bigger wing", "fans"], 1,
         "A power boost when close behind.")],
       widget=W.active_aero_demo, blurb="Lap time with less drag on the straights.",
       data=[("Energy Lab", "Active aero with the battery modelled.")], terms=["active aero", "drs"]),
]
