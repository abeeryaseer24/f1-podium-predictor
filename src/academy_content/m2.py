"""Module 2: Tyres."""
import academy_widgets_m2 as W

SOURCES = ["Pacejka, H. B. (2012). Tire and Vehicle Dynamics, 3rd ed. Butterworth-Heinemann.",
           "Milliken, W. F. & Milliken, D. L. (1995). Race Car Vehicle Dynamics, ch. 2. SAE International.",
           "Pirelli Motorsport, public F1 tyre guides and press material, pirelli.com"]

CHAPTERS = [
    {
        "id": "2.1",
        "title": "How rubber grips",
        "summary": "Four patches of rubber, each smaller than a sheet of paper, hold the car to the road.",
        "basics": """
Everything a Formula 1 car does (accelerate, brake, turn) happens through four **contact patches**:
the parts of the tyres actually touching the road. Each one is smaller than a sheet of paper.
Every engineering idea in the rest of this course is, in the end, a way to make those four patches
grip harder or more evenly.

Rubber grips in two main ways:

- **Adhesion.** Rubber molecules briefly stick to the stones in the road surface, then let go, over
  and over. It's like the stickiness of tape, and it's why clean, warm, rubbered-in tarmac grips best.
- **Hysteresis.** Soft rubber flows over the bumps of the road texture, and squeezing it in and out
  wastes energy. That lost energy shows up as a force resisting the slide. It's why tyres need
  some road texture to work, and why it works in the wet too.

A racing slick has no tread pattern because, on a dry road, more rubber touching the ground means
more grip. Grooves only help to pump water away in the wet.
""",
        "engineer": """
**Grip isn't simple friction.** For a block of wood on a table, friction force is roughly
$F = \\mu N$, with $\\mu$ fixed. Rubber breaks that rule in three ways, each covered in this module:

1. It depends on **how much the tyre slips** (2.2, 2.3).
2. It depends on **load**: $\\mu$ falls as the load rises (2.5).
3. It depends on **temperature** and pressure, often more than anything else (2.6).

**Typical numbers.** A racing slick reaches a friction coefficient of roughly 1.6–1.9 at its
own static load. Ordinary road tyres reach about 1.0. Downforce then multiplies the load, which is
how an F1 car sustains 4–5 g in fast corners even though the rubber "only" gives $\\mu \\approx 1.7$.

**The contact patch's job.** It has to pass forces in three directions at once: vertical (holding
up the car and its downforce), longitudinal (driving and braking) and lateral (cornering). The
patch deforms as it does so, and that deformation (slip) is what generates the force.
""",
        "deep": """
**Adhesion and hysteresis in more detail.** Adhesion depends on the true contact area at the
molecular scale and on the rubber's viscoelastic response at the sliding frequency. Hysteresis
depends on the road's texture wavelengths (macro-texture of millimetres, micro-texture of
micrometres) and on how lossy the rubber is at the frequencies those wavelengths excite. Both
peak at a particular combination of temperature and sliding speed, which is the physical origin
of the temperature window (2.6). The WLF (Williams–Landel–Ferry) shift links temperature and
frequency: warming the rubber has a similar effect to sliding it more slowly.

**Why tracks "rubber in".** Over a weekend, cars lay rubber on the racing line. Rubber-on-rubber
adhesion is higher than rubber-on-stone, so lap times fall by a second or more from Friday to
Sunday. That's *track evolution*, and it shows up in the degradation fits in 2.9 as laps getting
faster with tyre age.
""",
        "terms": ["grip", "friction coefficient", "downforce"],
        "quiz": [
            ("What is a contact patch?", ["The tyre's sidewall", "The part of the tyre touching the road",
                                          "A repair kit", "The wheel rim"], 1, "All forces pass through it."),
            ("Why do dry racing tyres have no tread?", ["To save weight", "More rubber on the road means more grip",
                                                        "Rules ban grooves", "They last longer"], 1,
             "Grooves only help to clear water."),
            ("Hysteresis grip comes from…", ["glue in the rubber", "energy lost as rubber flows over road texture",
                                              "the wheel's weight", "air pressure"], 1,
             "Deforming rubber in and out wastes energy, which resists sliding."),
            ("A racing slick's friction coefficient is roughly…", ["0.3", "1.0", "1.7", "5"], 2,
             "About 1.6–1.9; road tyres reach about 1.0."),
            ("Track evolution means…", ["the circuit gets longer", "grip rises as rubber is laid down",
                                        "the weather changes", "tyres get harder"], 1,
             "Rubber-on-rubber grips better than rubber-on-stone."),
        ],
        "sources": SOURCES + ["Persson, B. N. J. (2001). Theory of rubber friction and contact mechanics. "
                              "Journal of Chemical Physics 115, 3840."],
    },
    {
        "id": "2.2",
        "title": "Slip angle and slip ratio",
        "summary": "A tyre only makes force when it slips a little. Too much, and it slides.",
        "basics": """
It sounds wrong, but a tyre has to **slip** to grip.

- **Cornering:** the wheel points slightly more into the corner than the direction the car is really
  travelling. The difference is the **slip angle**, a few degrees. The tread twists as it rolls
  through the contact patch, and that twisting is what pushes the car sideways.
- **Braking and accelerating:** the tyre turns slightly slower (braking) or faster (driving) than
  the road passing under it. The difference is the **slip ratio**, a few per cent.

More slip gives more force, up to a peak. Beyond the peak the tyre is **sliding**: force drops,
the rubber overheats and wears, and the car feels like it's on ice. The best drivers keep their
tyres right at the peak, corner after corner.
""",
        "engineer": """
**Definitions.** For a wheel moving at velocity $V$ with its direction of travel at angle $\\alpha$
to where it points:

$$\\alpha = \\arctan\\frac{V_y}{V_x} \\qquad \\kappa = \\frac{\\omega R - V_x}{V_x}$$

$\\alpha$ is the slip angle, $\\kappa$ the slip ratio ($\\omega$ the wheel's spin rate, $R$ its
rolling radius). Positive $\\kappa$ is driving, negative is braking; $\\kappa = -1$ is a locked wheel.

**Typical peaks for racing slicks:** slip angle about 4–8°, slip ratio about 8–12 %. Below the
peak, force is almost proportional to slip; the slope is the **cornering stiffness** $C_\\alpha$
(newtons per degree).

**Why the curve falls.** At small slip, most of the contact patch is gripping and only the back
edge slides. As slip grows, the sliding region creeps forward. At the peak, nearly all of the
patch is sliding; after it, sliding friction is lower than gripping friction, so force falls.
""",
        "deep": """
**The brush model.** Picture the tread as bristles. Each bristle enters the contact patch
undeformed, is dragged sideways as it travels through (because the wheel is at an angle to its
path), and springs back when it leaves. Where the bristle's elastic force exceeds what friction
can hold, it slides. Integrating along the patch gives a force curve with exactly this shape:
linear, then saturating. The brush model is the physical root of empirical fits like the magic
formula (next chapter).

**Relaxation length.** A tyre doesn't build force instantly: it needs to roll a short distance
(roughly half a metre for a slick) before the deformation, and so the force, settles. That lag
matters for fast direction changes and is part of why steady-state models (like our lap
simulator) miss some of a car's transient behaviour.
""",
        "widget": W.slip_curves,
        "widget_blurb": "Cornering force against slip angle and braking/driving force against slip ratio.",
        "data": [("Tyre Physics", "Change the shape of the curve and the load on the tyre."),
                 ("Ghost Lap Duel", "Throttle and brake traces show drivers riding the slip peak out of corners.")],
        "terms": ["grip", "lateral g", "longitudinal g"],
        "quiz": [
            ("What is slip angle?", ["The angle of the track", "The gap between where the wheel points and where it goes",
                                     "Camber", "Steering lock"], 1, "A few degrees in a corner."),
            ("A locked wheel has a slip ratio of…", ["0", "+1", "−1", "10%"], 2, "It isn't turning at all."),
            ("Peak cornering force for a racing slick comes at roughly…", ["0.5°", "4–8°", "20°", "45°"], 1,
             "Our model peaks near 6°."),
            ("Past the peak, the tyre…", ["grips harder", "slides and loses force", "cools down", "stops rolling"], 1,
             "Sliding friction is lower than gripping friction."),
            ("Cornering stiffness is…", ["how stiff the sidewall is", "force per degree of slip at small slip",
                                         "the suspension spring", "maximum steering"], 1,
             "The slope of the curve near zero."),
        ],
        "sources": SOURCES,
    },
    {
        "id": "2.3",
        "title": "The magic formula",
        "summary": "Pacejka's equation: four numbers that describe almost any tyre.",
        "basics": """
Engineers need a tyre model they can put into a simulator: an equation that says how much force
the tyre makes for any amount of slip. The most famous is Hans Pacejka's **magic formula**. It's
called magic because nobody derived it from first principles; it simply fits measured tyre data
astonishingly well with just four numbers.

Each number changes one feature of the curve: how high it peaks, how quickly it rises, how sharp
the peak is, and how much force is left once the tyre slides. Teams fit those numbers to data from
tyre test rigs and from the car itself, then feed them into their vehicle models.
""",
        "engineer": """
$$F(x) = D\\,\\sin\\!\\Big(C\\,\\arctan\\big(Bx - E\\,(Bx - \\arctan Bx)\\big)\\Big)$$

- **D, peak:** the maximum force, $D = \\mu F_z$.
- **C, shape:** sets how far the force falls after the peak. About 1.3 for cornering, 1.65 for
  braking/driving in Pacejka's original fits.
- **B, stiffness factor:** with C and D it sets the initial slope, the cornering stiffness
  $C_\\alpha = BCD$.
- **E, curvature:** shapes the region around the peak, moving where it falls.

In practice each coefficient is itself a function of load, camber and pressure, so a full model
has dozens of parameters. The demo keeps $D = 1$ so you can see the shape alone.
""",
        "deep": """
**Where it came from.** Bakker, Nyborg and Pacejka published the formula in 1987 working with
Volvo, and it became the industry standard (variants are called MF-Tyre, now maintained as
MF-Swift). The sine of an arctangent naturally rises, saturates and falls, which is the shape of
the brush model's output with a falling friction coefficient.

**Combined slip in the magic formula.** For braking while cornering, the full model applies
weighting functions that reduce lateral force as longitudinal slip rises and vice versa: the
friction circle (next chapter) built into the equations.

**Limits.** The formula describes a steady state at one temperature. Real F1 tyre models add
thermal states (surface, bulk, inner liner), wear and pressure, and are fitted to Pirelli rig data
that teams receive under strict confidentiality.
""",
        "widget": W.magic_shape,
        "widget_blurb": "Change B, C and E and compare your curve with a typical slick.",
        "data": [("Tyre Physics", "The full version, with load and grip as well.")],
        "terms": ["grip", "friction coefficient"],
        "quiz": [
            ("Why is it called the 'magic' formula?", ["It uses magic numbers", "It fits data very well without being derived from physics",
                                                       "Pirelli invented it", "It's secret"], 1,
             "It's empirical, and remarkably accurate."),
            ("D in the magic formula is…", ["the slip angle", "the peak force", "the tyre diameter", "drag"], 1,
             "D = μ × load."),
            ("The initial slope (cornering stiffness) equals…", ["B + C + D", "B × C × D", "D ÷ B", "E"], 1,
             "C_α = BCD."),
            ("Who did Pacejka develop the formula with first?", ["Ferrari", "Volvo", "Pirelli", "NASA"], 1,
             "Bakker, Nyborg and Pacejka, 1987, with Volvo."),
            ("What does the basic formula leave out?", ["Slip", "Peak force", "Temperature and wear", "Load"], 2,
             "Full F1 models add thermal and wear states."),
        ],
        "sources": SOURCES + ["Bakker, E., Nyborg, L. & Pacejka, H. B. (1987). Tyre modelling for use in vehicle "
                              "dynamics studies. SAE 870421."],
    },
    {
        "id": "2.4",
        "title": "The friction circle and g-g diagrams",
        "summary": "One budget of grip, shared between turning and braking. Real laps trace its edge.",
        "basics": """
A tyre has **one budget of grip**. It can spend it all on cornering, all on braking, or share it.
Braking at the limit leaves nothing for turning; turning at the limit leaves nothing for braking.

Plot a car's sideways acceleration against its braking and acceleration for a whole lap, and the
dots trace a rough circle: the **friction circle**, or the *g-g diagram*. A great driver uses the
whole edge of it: braking hard in a straight line, then **trail braking** (easing off the brake
while turning in) so the combined grip stays at the limit all the way to the apex.

An F1 car's circle is lopsided: it brakes and corners at 4–6 g, but accelerates at only about
1–2 g, because acceleration is limited by power, not grip, above low speeds.
""",
        "engineer": """
**The ellipse.** With $F_{x,max}$ and $F_{y,max}$ the pure braking and cornering limits:

$$\\left(\\frac{F_x}{F_{x,max}}\\right)^2 + \\left(\\frac{F_y}{F_{y,max}}\\right)^2 \\le 1$$

Our lap simulator uses exactly this to share grip between cornering and braking.

**Measuring it.** From a lap's speed $v(s)$ and the track's curvature $\\kappa(s)$:

$$a_{long} = \\frac{dv}{dt} = v\\frac{dv}{ds} \\qquad a_{lat} = v^2 \\kappa$$

The demo does this for the real fastest lap. Fast corners reach higher lateral g than slow ones,
so the circle isn't a fixed shape: downforce grows it with speed. Teams therefore plot g-g-V
(a 3D envelope with speed as the third axis).
""",
        "deep": """
**Why the edge isn't sharp in real data.** Public data comes at about four samples a second, so
the derived accelerations are smoothed and noisy. Team data at hundreds of hertz shows a much
crisper edge. Drivers are also rarely exactly at the limit: the gap between the data and the
envelope is how engineers measure how much a driver is leaving on the table.

**Driving styles on the g-g.** A "V-style" driver brakes very late in a straight line and rotates
the car quickly (dots hug the axes). A "U-style" driver carries more speed through a longer arc
(dots fill the round shoulders of the circle). Which is faster depends on the car and corner.
""",
        "widget": W.real_gg_widget,
        "widget_blurb": "The real fastest lap as a g-g diagram, coloured by speed.",
        "data": [("Tyre Physics", "The same diagram with the lap simulator's car on top."),
                 ("Lap Simulator", "Braking zones and grip-limited corners coloured on the 3D track.")],
        "terms": ["friction circle", "lateral g", "longitudinal g"],
        "quiz": [
            ("The friction circle says that…", ["tyres are round", "grip is shared between turning and braking",
                                                "brakes overheat", "the car rotates"], 1, "One budget of grip."),
            ("Why does an F1 car accelerate at only 1–2 g but brake at 5 g?", ["Brakes are bigger than engines",
                                                                              "Acceleration is limited by power, braking by grip",
                                                                              "Rules", "Fuel"], 1,
             "Above low speed, power limits acceleration."),
            ("Trail braking means…", ["braking on the straight only", "easing off the brake while turning in",
                                      "braking with the left foot", "braking late"], 1,
             "It keeps the tyre at the combined limit."),
            ("Lateral acceleration is…", ["v ÷ κ", "v² × κ", "κ ÷ v", "v × t"], 1, "Speed squared times curvature."),
            ("Why do fast corners reach higher g?", ["Drivers are braver", "Downforce grows with speed",
                                                     "Tyres are hotter", "They're banked"], 1,
             "More downforce, more grip."),
        ],
        "sources": SOURCES + ["Segers, J. (2014). Analysis Techniques for Racecar Data Acquisition, ch. 6. SAE."],
    },
    {
        "id": "2.5",
        "title": "Load sensitivity",
        "summary": "Each extra newton buys a little less grip. That shapes the whole car.",
        "basics": """
Push a tyre down twice as hard and it grips harder, but **less than twice as hard**. Every extra
newton of load buys a little less grip than the one before. That's **load sensitivity**.

It explains two big things:

- **Downforce has diminishing returns.** Doubling downforce doesn't double cornering grip.
- **Weight transfer costs grip.** In a corner, load moves from the inside tyres to the outside
  ones. The outside tyre gains less grip than the inside tyre loses, so the pair grips less than
  if the load were shared evenly.

That second point is why racing cars are low (less weight transfer), wide (less weight transfer)
and carefully balanced between front and rear.
""",
        "engineer": """
**A simple model.** With $F_{z0}$ a reference load and $k$ the sensitivity:

$$\\mu(F_z) = \\mu_0 \\left(\\frac{F_z}{F_{z0}}\\right)^{-k} \\quad\\Rightarrow\\quad
F_{y,max} = \\mu_0 F_{z0}^{\\,k} F_z^{\\,1-k}$$

With $k = 0$ grip is proportional to load; with $k > 0$ the curve bends over. Our lap simulator
uses $k = 0.12$.

**Lateral weight transfer** on an axle with track width $t$ and centre of gravity height $h$:

$$\\Delta F_z = \\frac{m\\,a_{lat}\\,h}{t}$$

Lower $h$ or wider $t$, less transfer, more total grip. The split of that transfer between front
and rear (set by the anti-roll bars and springs) is one of the main ways engineers tune the car's
balance (Module 3).
""",
        "deep": """
**Why rubber behaves this way.** As load rises, the contact patch grows, but the average pressure
in it rises too, and rubber friction falls with contact pressure. So force grows more slowly
than load.

**Downforce vs mass.** Downforce adds load without adding mass, so it beats ballast even with load
sensitivity. But the returns shrink: the lap-time value of the next 5 % of downforce is lower on a
high-downforce car than on a low-downforce one. You can see this in the Setup Garage's
sensitivities as you raise the wing level.
""",
        "widget": W.weight_transfer,
        "widget_blurb": "Two tyres carrying the same total load, evenly or unevenly.",
        "data": [("Setup Garage", "Change load sensitivity under Advanced and watch the lap time."),
                 ("Tyre Physics", "Load sensitivity against a tyre whose grip grew in step with load.")],
        "terms": ["load sensitivity", "downforce", "grip"],
        "quiz": [
            ("Load sensitivity means…", ["grip grows faster than load", "grip grows more slowly than load",
                                         "grip doesn't depend on load", "tyres are fragile"], 1, "Diminishing returns."),
            ("Why does weight transfer cost grip?", ["The outside tyre gains less than the inside loses",
                                                     "It heats the brakes", "It lifts the car", "It doesn't"], 0,
             "That's load sensitivity at work."),
            ("Weight transfer falls if the car is…", ["higher and narrower", "lower and wider", "heavier", "faster"], 1,
             "ΔFz = m a h / t."),
            ("With k = 0, grip is…", ["zero", "proportional to load", "constant", "negative"], 1,
             "No load sensitivity."),
            ("Why does downforce still beat ballast?", ["It's lighter to make", "It adds load without adding mass",
                                                        "It's cheaper", "It cools the tyres"], 1,
             "Mass has to be accelerated; downforce doesn't."),
        ],
        "sources": SOURCES,
    },
    {
        "id": "2.6",
        "title": "Temperature and pressure",
        "summary": "Rubber has a window. Too cold or too hot and the grip falls away.",
        "basics": """
Rubber grips best inside a **temperature window**, roughly 90–120 °C for an F1 slick depending on
the compound. Below it, the rubber is hard and slippery. Above it, it turns greasy, wears quickly
and can blister.

The driver controls tyre temperature through how they drive. Sliding the tyre heats it; driving
smoothly lets it cool. So "tyre management" often means *temperature* management: pushing a
little less in some corners to keep the tyres in the window for the whole stint.

**Pressure** matters too. Higher pressure means a smaller, stiffer contact patch: less grip but
less heat build-up and more safety. Pirelli sets minimum starting pressures at every race for
safety, and teams run as close to them as they dare.
""",
        "engineer": """
**A one-node thermal model** (the demo uses this):

$$m c\\,\\frac{dT}{dt} = a\\,P_{slide} - h\\,(T - T_{air})$$

Sliding power $P_{slide}$ (force × sliding speed) heats the tread; convection to the air and
conduction to the track cool it. The grip factor is a bell curve around the optimum,
$\\exp\\left(-\\left(\\frac{T - T_{opt}}{w}\\right)^2\\right)$.

The feedback is what makes tyres tricky: a tyre above its window grips less, so it slides more,
so it heats more. Push too hard and it runs away from you.

**Surface vs core.** The surface heats and cools in a single corner; the core (carcass) changes
over many laps. A car can have hot surfaces and a cold core, the classic problem on the first lap
after a safety car.
""",
        "deep": """
**Real tyre thermal models** split the tyre into surface, bulk tread, carcass and inflation gas,
each with its own temperature, coupled by conduction. Brake heat conducts into the rim and the
gas, raising pressure. Teams use rim and brake cooling to steer tyre temperatures, which is why
brake-duct design is closely tied to tyre performance.

**Blankets and out-laps.** Tyres are pre-heated in electric blankets so they start nearer their
window. The FIA has been reducing permitted blanket temperatures, which makes warming tyres on
the out-lap a bigger part of the driver's job.

**Our model's limit.** One temperature for the whole tread and made-up but sensible constants:
it shows the shape of the problem, not Pirelli's numbers.
""",
        "widget": W.temperature_window,
        "widget_blurb": "A 25-lap stint: how hard the driver pushes decides the tyre temperature.",
        "data": [("Tyre Physics", "Three drivers' stints side by side, and the effect of track heat."),
                 ("Race Insights", "Track temperature through any race since 2023.")],
        "terms": ["grip"],
        "quiz": [
            ("An F1 slick works best roughly between…", ["20–40 °C", "50–70 °C", "90–120 °C", "200–250 °C"], 2,
             "Depending on the compound."),
            ("Why can an overheating tyre run away?", ["Less grip means more sliding, which means more heat",
                                                       "Air gets hotter", "Brakes fail", "Pressure falls"], 0,
             "A positive feedback loop."),
            ("Higher tyre pressure gives…", ["a bigger contact patch", "a smaller, stiffer patch", "more grip always",
                                             "no change"], 1, "Less grip, less heat build-up."),
            ("Why are tyres pre-heated in blankets?", ["To clean them", "To start nearer the temperature window",
                                                       "Rules require it", "To dry them"], 1,
             "Cold tyres grip poorly."),
            ("Tyre management is often really…", ["fuel management", "temperature management", "brake management",
                                                  "radio management"], 1, "Keeping the tyres in their window."),
        ],
        "sources": SOURCES,
    },
    {
        "id": "2.7",
        "title": "Wear, graining and the cliff",
        "summary": "How tyres lose performance: steadily, then suddenly.",
        "basics": """
Tyres lose performance in a few different ways:

- **Wear.** The tread gets thinner. A thinner tread runs cooler and can grip differently, but mostly
  the car slowly gets slower, lap after lap.
- **Graining.** When a tyre slides while it's too cold, the surface tears into little rolls of
  rubber that sit between the tyre and the road like ball bearings. Grip drops until they wear
  away, and it can recover.
- **Blistering.** When a tyre overheats inside, pockets of gas form and burst, taking chunks out of
  the tread. That damage doesn't recover.
- **The cliff.** Near the end of its life a tyre can suddenly lose a lot of grip in a few laps.

Strategy is mostly about these effects: when the time lost on old tyres outweighs the time a pit
stop costs, it's time to stop.
""",
        "engineer": """
**A practical model** (the one our Pit Wall strategist uses): lap-time loss grows in a straight
line with tyre age, plus a cliff near the end of the tyre's life:

$$\\Delta t(a) = w\\,a + \\tfrac{1}{2}r\\,(a - a_c)(a - a_c + 1) \\quad (a > a_c)$$

with $w$ the wear rate (seconds per lap of age), $a_c$ where the cliff starts and $r$ how steep it is.

**Thermal vs mechanical degradation.** Teams separate *thermal* degradation (grip lost because the
tyre is out of its window, which can recover) from *mechanical* wear (rubber gone, which can't).
A car that's hard on its tyres often suffers thermal degradation first: managing temperature
extends the stint more than anything else.
""",
        "deep": """
**Fuel hides wear.** A car gets lighter by about 1.5–2 kg per lap as it burns fuel, worth a few
hundredths each lap. So a stint's lap times can stay flat even while the tyres degrade. Separating
the two needs a model, which is what the Tyre Lab fit does (next chapters).

**Graining vs track evolution.** Early in a weekend, a green track grains tyres more. As rubber is
laid down, graining eases. Front graining is often a sign of understeer (the front sliding), rear
graining of traction problems.
""",
        "widget": W.tyre_cliff,
        "widget_blurb": "Lap time lost against tyre age: steady wear, then the cliff.",
        "data": [("Pit Wall", "The strategist uses this model to call stops."),
                 ("Be the Race Engineer", "Run a tyre too long and feel the cliff.")],
        "terms": ["grip"],
        "quiz": [
            ("Graining happens when a tyre…", ["is too hot", "slides while too cold", "is new", "is wet"], 1,
             "The surface tears into rolls of rubber."),
            ("Blistering is caused by…", ["cold", "overheating inside the tyre", "low pressure only", "rain"], 1,
             "Gas pockets form and burst."),
            ("The 'cliff' is…", ["a steep track", "a sudden drop in grip near the end of a tyre's life",
                                 "a type of kerb", "a pit wall"], 1, "Performance falls off quickly."),
            ("Why can lap times stay flat while tyres degrade?", ["Drivers push harder", "Burning fuel makes the car lighter",
                                                                  "The track cools", "They don't"], 1,
             "Fuel loss hides wear."),
            ("Which kind of degradation can recover?", ["Mechanical wear", "Thermal degradation", "Blistering", "None"], 1,
             "Bring the tyre back into its window and grip returns."),
        ],
        "sources": SOURCES,
    },
    {
        "id": "2.8",
        "title": "Compounds and construction",
        "summary": "C1 to C6, hards to softs, inters and wets, and what's inside a tyre.",
        "basics": """
Pirelli has supplied every Formula 1 team since 2011, and everyone uses the same tyres.

- **Dry compounds** run from **C1** (hardest) to **C6** (softest; added in 2025). At each race Pirelli
  picks three, labelled **hard** (white), **medium** (yellow) and **soft** (red). Softer rubber grips
  more but wears faster and overheats sooner.
- **Intermediates** (green) have shallow grooves for a damp or drying track.
- **Full wets** (blue) have deep grooves to clear standing water.

In a dry race each driver must use at least two different dry compounds, which forces at least one
pit stop and makes strategy matter.

Since 2022 the wheels are 18 inches across, with lower, stiffer sidewalls than the old 13-inch
tyres.
""",
        "engineer": """
**What's in a tyre.** A carcass of fabric cords (the structure), a belt package under the tread,
the tread compound on top, and an airtight inner liner. The carcass sets how the tyre deforms
under load, which sets its cornering stiffness and how it heats.

**Compound choice** is a trade between peak grip and how long it lasts. At circuits that are hard
on tyres (high-energy corners, rough surfaces, heat) Pirelli brings harder compounds; at street
circuits with smooth tarmac, softer ones.

**The 18-inch change (2022).** Shorter sidewalls flex less, so the tyre responds more directly and
is less able to absorb bumps. Teams could no longer rely on the sidewall as part of the
suspension, which changed setups.
""",
        "deep": """
**Water clearing.** At 300 km/h a full wet tyre can move tens of litres of water per second.
Aquaplaning starts when the water can't escape fast enough and the tyre rides on a film: grooves
and tread depth decide the speed at which that happens.

**Why one supplier.** A single supplier controls costs and lets the FIA and Pirelli set tyres that
degrade (to create strategy) rather than tyres built purely for speed. Tyre "wars" (Bridgestone vs
Michelin, up to 2006) produced very fast but very expensive, very car-specific tyres.
""",
        "terms": ["grip"],
        "quiz": [
            ("Which is the hardest dry compound?", ["C1", "C3", "C5", "C6"], 0, "C1 is hardest, C6 softest."),
            ("Intermediates are marked…", ["red", "yellow", "green", "blue"], 2, "Blue is the full wet."),
            ("In a dry race each driver must use…", ["one compound", "at least two different dry compounds",
                                                     "only softs", "three compounds"], 1, "This forces at least one stop."),
            ("Since 2022 F1 wheels are…", ["13 inch", "15 inch", "18 inch", "21 inch"], 2, "With lower sidewalls."),
            ("The carcass of a tyre is…", ["the tread", "the fabric structure underneath", "the valve", "the rim"], 1,
             "It sets how the tyre deforms."),
        ],
        "sources": SOURCES + ["FIA Formula 1 Sporting Regulations, tyre articles, fia.com"],
    },
    {
        "id": "2.9",
        "title": "Degradation in the data",
        "summary": "Taking fuel and driver out of real lap times to see what the tyres did.",
        "basics": """
Can you measure tyre degradation from lap times alone? Yes, if you're careful. A lap time mixes
together the driver's pace, the fuel load (lighter is faster), the tyre compound, the tyre's age,
traffic and mistakes.

The Tyre Lab takes every clean racing lap of a race (no first lap, no pit laps, no safety cars,
no very slow laps) and fits one model to all of them at once. That separates the **fuel effect**
(the same for everyone) from each **compound's speed** and **how fast each compound wears**. The
demo shows the result for a real race.
""",
        "engineer": """
**The model**, fitted by least squares on every clean lap:

$$t_{lap} = p_{driver} + f \\cdot n_{lap} + o_{compound} + w_{compound} \\cdot a_{tyre}$$

$p$ is each driver's base pace, $f$ the fuel effect per lap (the car gets lighter, so $f$ is
negative), $o$ each compound's offset from the reference, $w$ its wear rate and $a$ the tyre's age.
Because the lap number keeps counting through a pit stop but tyre age resets, the model can tell
fuel and wear apart.

**Honesty check.** It's fitted on 80 % of the laps and tested on the other 20 %. The typical error
on unseen laps is about a second, mostly traffic and driver variation.
""",
        "deep": """
**When it goes wrong.** Wet races, races with few clean laps, or a compound used only by a couple
of drivers give unreliable fits. A negative wear rate means laps got *faster* as the tyre aged:
track evolution outpacing wear, or drivers managing early in a stint and pushing later. Our
strategist blends each race's fit with what it learned at earlier races to stay sensible.

**What teams do beyond this:** long runs in practice at known fuel loads, tyre temperature and
wear measurements from sensors, and models fitted per driver and per corner type.
""",
        "widget": W.real_degradation,
        "widget_blurb": "Each compound's fitted wear for a real race.",
        "data": [("Tyre Lab", "The same fit for every race since 2023, with every clean lap plotted."),
                 ("Pit Wall", "The strategist uses fits like this to plan stops.")],
        "terms": ["telemetry"],
        "quiz": [
            ("Why is the first lap left out of the fit?", ["It's too fast", "It's chaotic and starts from a standstill",
                                                          "Rules", "No data"], 1, "Only clean racing laps are used."),
            ("How can the model tell fuel from wear?", ["Lap number keeps counting through stops, tyre age resets",
                                                        "Teams report it", "Radio", "It can't"], 0,
             "The two move differently after a stop."),
            ("The fuel effect per lap is negative because…", ["fuel is heavy", "the car gets lighter, so faster",
                                                              "the track cools", "of DRS"], 1, "Less mass, quicker laps."),
            ("A negative wear rate usually means…", ["the tyre improved with age by magic",
                                                     "track evolution or tyre management outpaced wear", "a bug", "rain"], 1,
             "Laps got faster as the stint went on."),
            ("How is the fit tested honestly?", ["On the same laps", "On 20 % of laps it didn't see",
                                                 "By asking teams", "It isn't"], 1, "Held-out laps measure the error."),
        ],
        "sources": SOURCES + ["Our own fits: tyres.py, on OpenF1 lap data."],
    },
]
