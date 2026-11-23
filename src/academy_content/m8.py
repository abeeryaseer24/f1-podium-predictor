"""Module 8: Chassis, materials and safety."""
import academy_widgets_m8 as W
from academy_content.m4 import ch

SOURCES = ["FIA Formula 1 Technical Regulations, safety and survival cell articles, fia.com",
           "Savage, G. (2010). Formula 1 composites engineering. Engineering Failure Analysis 17(1).",
           "FIA, Bahrain 2020 accident investigation summary (Grosjean), published March 2021, fia.com"]

CHAPTERS = [
    ch("8.1", "The carbon-fibre monocoque", "The survival cell is also the car's backbone.",
       """
The **monocoque** is the tub the driver sits in. It's made of carbon fibre: thin sheets of carbon
threads set in resin, laid up by hand in a mould, layer on layer, then baked under pressure. The result
is lighter than aluminium and stiffer than steel for its weight.

It does two jobs at once. It's the car's main structure (the engine bolts to the back, the front
suspension to the front), and it's the driver's **survival cell**, built to stay intact in a crash
when almost everything around it breaks away.
""",
       """
**Layup and cure.** Pre-impregnated carbon plies ("prepreg") go into the mould at chosen angles, so the
part is stiff where the loads run. Between carbon skins sits a light honeycomb core (aluminium or aramid):
a sandwich panel, stiff in bending like an I-beam. The part cures in an **autoclave**, an oven pressurised
to several bar, which squeezes out voids and sets the resin.

**Stiffness matters for lap time.** A tub that twists acts like an extra, uncontrolled spring, so the
suspension can't do its job. Torsional stiffness is one of the first numbers a chassis designer checks.

**Anti-intrusion.** The cockpit sides carry extra panels of Zylon, a very strong fibre, to stop debris
or another car's nose punching through.
""", """
**Why the fibre angles matter.** Carbon is anisotropic: strong along the fibres, weak across them.
Laminate theory adds up each ply's stiffness at its angle; a quasi-isotropic layup (0°, ±45°, 90°)
behaves the same in every direction, but designers bias it towards the real load paths to save mass.
Damage tolerance and the way carbon fails (it shatters and absorbs energy as it does, rather than
bending like metal) shape both the tub and the crash structures in 8.3.
""",
       [("The monocoque is made mainly of…", ["steel", "carbon-fibre composite", "titanium", "magnesium"], 1, "Layered carbon in resin."),
        ("An autoclave is…", ["a pressurised oven that cures the carbon", "a crash test", "a gearbox part", "a fuel pump"], 0, "It squeezes out voids."),
        ("Why does a stiff tub help lap time?", ["It lets the suspension work as designed", "It's lighter", "Rules", "It cools the engine"], 0,
         "A flexing tub is an uncontrolled spring."),
        ("Zylon panels on the cockpit sides stop…", ["heat", "debris and noses punching through", "rain", "noise"], 1, "Anti-intrusion."),
        ("A sandwich panel puts a light core between…", ["two carbon skins", "two steel plates", "rubber", "glass"], 0, "Stiff in bending for its mass.")],
       terms=["monocoque"], sources=SOURCES),

    ch("8.2", "Weight, ballast and the minimum mass", "Why teams build under the limit and then add weight back.",
       """
The rules set a **minimum mass** for the car with its driver (798 kg in 2022–2025, about 768 kg from
2026). Every kilo over it costs lap time, so teams try to build the car lighter than the limit.

If they manage it, they add **ballast**: dense metal blocks bolted low down where the engineers want the
weight. That's better than a car that's simply at the limit, because the ballast can be placed to tune
the balance and lower the centre of gravity.

Drivers matter too: since 2019 the driver and seat count as at least 80 kg, with ballast in the cockpit
to make up the difference, so a lighter driver no longer gives a free advantage.
""",
       """
**What a kilo costs.** The lap simulator below adds or removes mass on a calibrated car. A common rule of
thumb is about 0.03 s a lap per 10 kg, but it depends on the circuit: more where the car accelerates out
of many slow corners, less on a high-speed track.

**Weight distribution.** The rules also fix limits on how the mass is split between the axles, so teams
can't move all the ballast to suit one circuit.
""",
       """
**Mass, grip and the friction circle.** Extra mass needs more force to accelerate, brake and turn, but it
also adds load to the tyres. Because grip grows more slowly than load (load sensitivity, Module 2.5), the
added load buys less grip than the mass costs, so a heavier car is always slower in corners as well as on
the straights. Fuel is the biggest mass that changes in a race: about 100 kg at the start, burning off
lap by lap.
""",
       [("Ballast is used when…", ["the car is under the minimum mass", "it rains", "the engine is new", "the car is too heavy"], 0,
         "Weight placed where the engineers want it."),
        ("Why is ballast better than a car built exactly at the limit?", ["It can be placed to tune balance and lower the CoG", "It's cheaper",
                                                                          "Rules prefer it", "It isn't"], 0, "Placement is the point."),
        ("Since 2019 the driver and seat count as at least…", ["60 kg", "80 kg", "100 kg", "no minimum"], 1, "Lighter drivers carry ballast."),
        ("Why is a heavier car slower in corners too?", ["Grip grows more slowly than load", "Drag", "Rules", "It isn't"], 0,
         "Load sensitivity."),
        ("The biggest mass that changes during a race is…", ["the driver", "the fuel", "the tyres", "the ballast"], 1, "About 100 kg burns off.")],
       widget=W.mass_cost, blurb="What 10 kg costs on any circuit, from the lap simulator.",
       data=[("Setup Garage", "Mass among the sensitivities.")], terms=["minimum mass", "sensitivity"], sources=SOURCES),

    ch("8.3", "Crash structures and FIA tests", "Parts designed to break, so the driver doesn't.",
       """
Around the survival cell sit **crash structures**: the nose, the side-impact tubes and the rear structure
behind the gearbox. They're designed to crush in a controlled way and soak up the energy of an impact,
so the deceleration reaching the driver stays survivable.

Before a car can race, its structures must pass the FIA's **crash tests**: the nose is fired into a wall,
side and rear structures are hit by impactors, and the roll hoop, the halo and the cockpit sides must
hold big static loads without failing.
""",
       """
**Distance is everything.** Stopping from speed $v$ over a crush distance $d$ means an average
deceleration of $v^2 / 2d$. The demo below shows it: halve the crush distance and the g doubles. Crash
structures, deformable barriers and run-off all exist to add distance.

**Carbon crushes.** A carbon nose fails progressively, fibre by fibre, at a fairly steady force, which
gives a flatter, safer deceleration pulse than a metal structure that buckles and then goes solid.
""",
       """
**Test design.** Tests fix the impact speed and mass and set limits on the average and peak deceleration
and on damage to the survival cell. Over the years they've been extended: higher side-impact energies,
squeeze tests on the cockpit sides, and tougher roll-hoop loads after the roll-hoop failure in Zhou
Guanyu's Silverstone crash in 2022.
""",
       [("A crash structure is designed to…", ["stay perfectly rigid", "crush in a controlled way", "add downforce", "cool the brakes"], 1,
         "It absorbs energy."),
        ("Halving the crush distance makes the average deceleration…", ["half", "the same", "double", "four times"], 2, "a = v²/2d."),
        ("Why are carbon noses good crash structures?", ["They crush progressively at a steady force", "They bounce", "They're heavy", "They melt"], 0,
         "A flatter pulse."),
        ("Roll-hoop tests were toughened after…", ["Zhou's 2022 Silverstone crash", "Monaco 1955", "a rain race", "nothing"], 0, "The hoop failed."),
        ("Run-off areas help because they…", ["add stopping distance", "look nice", "are cheap", "cool tyres"], 0, "Distance lowers g.")],
       widget=W.crash_pulse, blurb="Impact speed and crush distance → the g the driver feels.",
       sources=SOURCES),

    ch("8.4", "The halo, HANS and the survival cell", "The parts that keep the driver's head and neck safe.",
       """
The **halo** is the titanium hoop over the cockpit, compulsory since 2018. Many disliked how it looked;
within a few years it had saved several drivers, including Romain Grosjean in Bahrain 2020, Charles
Leclerc at Spa 2018, Lewis Hamilton at Monza 2021 and Zhou Guanyu at Silverstone 2022.

The **HANS** device (head and neck support), compulsory since 2003, tethers the helmet to a collar on
the driver's shoulders, so the head can't whip forward in a frontal crash. Add the high cockpit sides,
the padded headrest and the wheel tethers that stop wheels flying off, and the driver sits in a
protected cell.
""",
       """
**Halo loads.** It weighs only about 7 kg but must take loads of the order of 100 kN, roughly the weight of
a London bus, from above and from the front without breaking or moving the survival cell.

**HANS physics.** In a big frontal impact the torso is held by the belts but the head keeps going. HANS
transfers that load through the tethers into the shoulders, cutting the neck forces that caused fatal
basal skull fractures in the past.
""",
       """
**Systems thinking.** Safety comes from layers, not one part: barriers absorb energy, the crash structure
absorbs more, the survival cell stays intact, the seat (moulded to the driver and removable with them
inside) and belts hold them, HANS protects the neck, the halo protects the head, and the helmet and
fireproof kit do the rest. Every layer was added after an accident showed the need for it (8.6).
""",
       [("The halo has been compulsory since…", ["2003", "2014", "2018", "2022"], 2, "It's titanium."),
        ("HANS protects…", ["the head and neck", "the feet", "the fuel tank", "the gearbox"], 0, "Head and neck support."),
        ("Wheel tethers stop…", ["punctures", "wheels flying off in a crash", "lock-ups", "wheelspin"], 1, "They hold the wheel to the car."),
        ("Which crash did the halo famously help in?", ["Grosjean, Bahrain 2020", "Monaco 1955", "Imola 1982", "none"], 0, "Among others."),
        ("Safety comes from…", ["one strong part", "many layers working together", "luck", "the helmet only"], 1, "A system.")],
       data=[("3D Part Explorer", "Find the halo and the survival cell.")], terms=["halo"], sources=SOURCES),

    ch("8.5", "Fire, the medical car and circuit safety", "What happens in the seconds after a crash.",
       """
Safety doesn't stop at the car. Drivers wear **fireproof** suits, gloves, boots and balaclavas made of
aramid fibres, tested to keep heat out for long enough to escape. Grosjean spent close to half a minute in
the fire in Bahrain 2020 and walked away with burns to his hands.

The **medical car**, with the FIA doctor, follows the field on the first lap and can be at any crash
within seconds. Marshals, fire crews and extraction teams are stationed round the circuit. And the
circuit itself must meet the FIA's highest grade: run-off areas, energy-absorbing barriers (tyre walls,
TecPro blocks, SAFER-style barriers) and debris fencing.
""",
       """
**Barrier choice.** Different barriers suit different impacts: tyre walls for low angles, TecPro or
conveyor-belted tyre stacks where a car may hit head-on, steel and concrete only where they're far enough
away. The FIA simulates likely run-off trajectories for every corner when grading a circuit.

**The first lap.** Crashes are most likely at the start with the field bunched up, which is why the medical
car follows the cars round the opening lap.
""",
       """
**Extraction.** The seat lifts out with the driver strapped in, so a driver with a suspected spinal injury
can be removed without bending their back. Teams practise extraction regularly, and the driver must
show they can get out of the cockpit unaided within a few seconds before a car is approved.
""",
       [("Race suits are made of…", ["cotton", "aramid fibres", "nylon", "wool"], 1, "Fire resistant."),
        ("The medical car follows the field on…", ["every lap", "the first lap", "the last lap", "never"], 1, "When crashes are most likely."),
        ("Why does the seat lift out with the driver?", ["To protect a possibly injured spine", "Rules about weight", "Comfort", "Speed"], 0,
         "Extraction without bending the back."),
        ("TecPro barriers are…", ["energy-absorbing blocks", "concrete walls", "paint", "fences only"], 0, "They crush on impact."),
        ("How long was Grosjean in the fire in 2020?", ["about 2 s", "close to half a minute", "5 minutes", "no fire"], 1,
         "He walked away.")],
       sources=SOURCES),

    ch("8.6", "Great crashes and what engineering learned", "Every safety device has an accident behind it.",
       """
F1's safety record is written in its crashes. After the deaths of Roland Ratzenberger and Ayrton Senna at
Imola in 1994, cockpit sides were raised, crash tests were made much harder and circuits were rebuilt.
Robert Kubica survived a huge crash in Canada 2007. Felipe Massa was hit by a loose spring in 2009, and
helmet visors got a strong strip on top. After Jules Bianchi's crash in Japan 2014, the **virtual safety
car** arrived in 2015 and the case for head protection grew into the halo.

In Bahrain 2020, Grosjean's car split in two and caught fire after a 67 g impact with a barrier. The halo,
the survival cell and the fireproof kit all did their jobs, and the FIA's report led to changes in barriers,
fuel tanks and gloves.
""",
       """
**The pattern.** Each accident is investigated (the FIA's research arm studies the data, the in-car
accident recorder and high-speed camera footage), the lesson becomes a regulation, and a new test makes
sure every car meets it. The accident data recorder, standard on every car, measures the crash pulse at
high rates, which is how numbers like "67 g" are known.

**Virtual safety car.** Bianchi hit a recovery tractor under yellow flags. The VSC makes every driver slow
to a set delta time at once, so nobody gains by not slowing enough.
""",
       """
**Measuring progress.** In the 1960s and 70s drivers died almost every season; since 1994 one driver
(Bianchi, who died of his injuries in 2015) has lost their life from an accident at a Grand Prix. Speeds
are higher than ever, so the improvement is engineering: energy management, structural integrity and
protection of the head, neck and body.
""",
       [("After Imola 1994…", ["cockpit sides were raised and crash tests toughened", "nothing changed", "turbos returned", "DRS arrived"], 0,
         "A turning point."),
        ("The virtual safety car arrived after…", ["Bianchi's 2014 crash", "Senna 1994", "Grosjean 2020", "Massa 2009"], 0, "In 2015."),
        ("Grosjean's 2020 impact was about…", ["6 g", "67 g", "670 g", "1 g"], 1, "Measured by the accident recorder."),
        ("How are crash g-forces known?", ["The accident data recorder", "Guesswork", "Driver estimate", "TV"], 0, "On every car."),
        ("Massa's 2009 accident led to…", ["a strong strip on the helmet visor", "the halo", "VSC", "DRS"], 0, "Against loose objects.")],
       data=[("Race Director", "Judge real incidents and safety cars yourself.")], sources=SOURCES),
]
