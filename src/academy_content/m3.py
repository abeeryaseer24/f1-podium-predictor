"""Module 3: Vehicle dynamics."""
import academy_widgets_m3 as W

SOURCES = ["Milliken, W. F. & Milliken, D. L. (1995). Race Car Vehicle Dynamics. SAE International.",
           "Gillespie, T. D. (1992). Fundamentals of Vehicle Dynamics. SAE International.",
           "Smith, C. (1978). Tune to Win. Aero Publishers."]


def quiz(*items):
    return list(items)


CHAPTERS = [
    {
        "id": "3.1",
        "title": "Weight transfer",
        "summary": "Brake, turn or accelerate, and load moves between the tyres.",
        "basics": """
When a car brakes, its weight seems to lurch forward; when it accelerates, backwards; in a
corner, towards the outside. Nothing actually moves inside the car: the tyres push at road level,
but the car's mass sits higher up, at its **centre of gravity**. That difference in height twists
the car, pressing some tyres down harder and lifting load off others. This is **weight transfer**.

Because of load sensitivity (Module 2), the tyres that gain load gain less grip than the others
lose. So weight transfer always costs some grip. Engineers fight it in two ways: keep the centre
of gravity **low**, and make the car **wide** and **long**.
""",
        "engineer": """
**Lateral transfer** (side to side) for the whole car, with track width $t$:

$$\\Delta F_{z,lat} = \\frac{m\\,a_y\\,h}{t}$$

**Longitudinal transfer** (front to back), with wheelbase $L$:

$$\\Delta F_{z,long} = \\frac{m\\,a_x\\,h}{L}$$

For an 800 kg car with $h = 0.28$ m and $t = 1.6$ m cornering at 3 g, that's about 4.1 kN moved
to the outside wheels, half the car's weight. Braking at 5 g moves about 3 kN onto the front.

**The total is fixed; the split isn't.** Physics fixes how much load moves side to side for a
given $h$ and $t$. The springs and anti-roll bars decide how much of it goes through the front
axle and how much through the rear. That split is one of the strongest tools for tuning
the car's balance (next chapter).
""",
        "deep": """
**Three paths for the load.** Lateral transfer on each axle splits into: (1) the part carried
through the suspension links via the roll centre (geometric, instant), (2) the part carried
through the springs and anti-roll bars as the body rolls (elastic, delayed by roll), and (3)
the unsprung mass's own transfer. Moving the roll centre or stiffening one axle's roll stiffness
shifts load transfer towards that axle, reducing its grip.

**Downforce changes the picture.** At speed, downforce adds thousands of newtons on top of the
car's weight, so the same weight transfer is a smaller share of the load on each tyre. That's
one reason high-downforce cars feel more stable in fast corners than slow ones.
""",
        "widget": W.weight_transfer_calc,
        "widget_blurb": "Load on each wheel for a car braking, accelerating and cornering.",
        "data": [("Tyre Physics", "What weight transfer costs a pair of tyres, in the load sensitivity tab.")],
        "terms": ["load sensitivity", "lateral g", "longitudinal g", "wheelbase"],
        "quiz": quiz(
            ("Why does weight transfer happen?", ["Fuel sloshes", "Tyre forces act at the ground, but the mass sits higher",
                                                  "The driver leans", "Air pressure"], 1,
             "The height difference twists the car."),
            ("Lateral weight transfer falls if the track is…", ["narrower", "wider", "longer", "shorter"], 1,
             "ΔFz = m·a·h / t."),
            ("Why does weight transfer cost grip?", ["Tyres are load-sensitive", "It heats brakes", "It slows the engine",
                                                     "It doesn't"], 0, "Loaded tyres gain less than unloaded ones lose."),
            ("What decides how the transfer splits between front and rear axles?", ["The engine", "Springs and anti-roll bars",
                                                                                    "The wing", "Tyre pressure"], 1,
             "Roll stiffness distribution."),
            ("At 3 g with h = 0.28 m and t = 1.6 m, an 800 kg car moves about…", ["400 N", "4,100 N", "41,000 N", "nothing"], 1,
             "800 × 3 × 9.81 × 0.28 / 1.6 ≈ 4,100 N."),
        ),
        "sources": SOURCES,
    },
    {
        "id": "3.2",
        "title": "Balance: understeer and oversteer",
        "summary": "Does the front or the rear run out of grip first? That's the car's balance.",
        "basics": """
In a corner, if the **front** tyres reach their limit first, the car runs wide even though the
driver is steering more: **understeer**. If the **rear** tyres go first, the back slides out and
the car turns more than asked: **oversteer**.

A little understeer is safe and predictable. A little oversteer can be fast (the car rotates into
the corner) but hard to control. Drivers talk constantly about balance, and it changes through a
corner: a car can understeer on entry and oversteer on exit.

Engineers tune balance with wings (front vs rear downforce), springs and anti-roll bars (weight
transfer split), tyre pressures and the differential.
""",
        "engineer": """
**The bicycle model** combines each axle's two tyres into one. With axle cornering stiffnesses
$C_f$ and $C_r$, weight on the front axle as a share $a$, and wheelbase $L$, the steering a car
needs on a corner of radius $R$ at speed $v$ is

$$\\delta = \\frac{L}{R} + K\\,\\frac{v^2}{R}, \\qquad K = m\\left(\\frac{1-a}{C_f} - \\frac{a}{C_r}\\right)$$

$K$ is the **understeer gradient**. $K > 0$: understeer, the car needs more steering as speed
rises. $K < 0$: oversteer, it needs less, and above the *critical speed* $v = \\sqrt{L/-K}$ it
becomes unstable. $K = 0$: neutral.

More weight on the front, or weaker front tyres, pushes towards understeer.
""",
        "deep": """
**Balance at the limit vs below it.** The bicycle model describes the linear range. At the limit,
balance depends on which axle saturates first, which load sensitivity and weight transfer split
decide. Shifting roll stiffness forward overloads the front tyres in corners: more understeer at
the limit, even if $K$ in the linear range barely changes.

**Aero balance.** Downforce has its own front/rear split, the *centre of pressure*. If it sits
further forward than the centre of gravity's share, the front gets relatively more grip at high
speed. Because the floor's downforce depends on pitch and ride height, aero balance moves with
speed and braking, which is why drivers report different balance in slow and fast corners.
""",
        "widget": W.understeer_demo,
        "widget_blurb": "Steering needed against speed on one corner, for your car and a neutral one.",
        "data": [("Setup Garage", "The point-mass model has no balance; the Academy's later chapters build up to one.")],
        "terms": ["grip", "lateral g"],
        "quiz": quiz(
            ("Understeer means…", ["the rear slides first", "the front runs out of grip first", "the brakes lock",
                                   "too much power"], 1, "The car runs wide."),
            ("An oversteering car above its critical speed is…", ["faster", "unstable", "understeering", "neutral"], 1,
             "It can spin without driver correction."),
            ("More weight on the front axle tends to cause…", ["oversteer", "understeer", "nothing", "wheelspin"], 1,
             "With the same tyres front and rear."),
            ("The understeer gradient K > 0 means…", ["less steering needed as speed rises",
                                                      "more steering needed as speed rises", "a spin", "no change"], 1,
             "That's understeer."),
            ("Aero balance is set by…", ["the centre of pressure of downforce", "tyre pressure", "the fuel load", "gearing"], 0,
             "Front vs rear share of downforce."),
        ),
        "sources": SOURCES,
    },
    {
        "id": "3.3",
        "title": "Suspension layouts",
        "summary": "Double wishbones, push rods and pull rods: holding the tyres and the floor exactly where they should be.",
        "basics": """
An F1 car's suspension has two jobs: keep each tyre in the best contact with the road, and hold
the car's floor at exactly the right height for the aerodynamics. On today's ground-effect cars
the second job matters enormously.

Each wheel is held by two carbon-fibre **wishbones** (an upper and a lower A-shaped arm). The
springs and dampers aren't at the wheel, where they'd disturb the airflow; they sit inside the
car, worked by a rod:

- a **push rod** runs from the bottom of the wheel upright up to the chassis, pushing as the wheel rises;
- a **pull rod** runs from the top of the upright down to the chassis, pulling as the wheel rises.

Pull rods put the heavy parts lower; push rods are easier to package and adjust. Teams pick
whichever suits their car's shape.
""",
        "engineer": """
**Double wishbones** let engineers set exactly how the wheel's angle (camber) and position
change as the suspension moves and the body rolls (next chapter).

**Inboard springs and rockers.** The rod works a rocker that converts the wheel's motion into
movement of torsion bars or springs, dampers and the anti-roll bar. The rocker's geometry sets the
**motion ratio** (how far the spring moves per millimetre of wheel travel), which lets designers
make the wheel rate rise as the car compresses.

**What the rules allow.** Since 2022 the regulations banned hydraulic suspension systems and
inerters, so cars use mechanical springs, dampers and anti-roll bars only. Ride-height control has
to come from the mechanical setup and the aero design.
""",
        "deep": """
**Heave, roll and pitch.** The suspension must react separately to the car moving straight down
(heave, under downforce), rolling (in corners) and pitching (under braking). Separate heave
elements (third springs) let engineers stiffen heave, to support downforce, without making the car
stiff in roll or over single-wheel bumps. Module 3.5 covers this.

**Anti-dive and anti-squat.** Angling the wishbone mounts makes the suspension itself resist
pitching under braking (anti-dive) and acceleration (anti-squat). That keeps the floor stable,
but too much makes the car harsh over bumps and can upset the tyres.
""",
        "terms": ["monocoque", "ground effect"],
        "quiz": quiz(
            ("A push rod runs…", ["from the top of the upright down", "from the bottom of the upright up to the chassis",
                                  "along the floor", "to the wing"], 1, "It pushes as the wheel rises."),
            ("Why are springs and dampers inside the car?", ["Rules", "To keep them out of the airflow", "To keep them warm",
                                                             "For the driver to adjust"], 1, "Cleaner aerodynamics."),
            ("What did the 2022 rules ban?", ["Wishbones", "Hydraulic suspension systems and inerters", "Dampers", "Springs"], 1,
             "Mechanical springs, dampers and bars only."),
            ("A motion ratio describes…", ["gear ratios", "spring travel per unit of wheel travel", "weight distribution",
                                           "tyre slip"], 1, "Set by the rocker geometry."),
            ("Anti-dive geometry resists…", ["rolling", "pitching under braking", "understeer", "wheelspin"], 1,
             "It keeps the floor level under braking."),
        ),
        "sources": SOURCES + ["FIA 2022 Formula 1 Technical Regulations, Article 10 (suspension), fia.com"],
    },
    {
        "id": "3.4",
        "title": "Kinematics",
        "summary": "Camber, toe and caster: the angles that decide how the tyre meets the road.",
        "basics": """
*Kinematics* is the geometry of how the wheel moves. Three angles matter most:

- **Camber**: how much the wheel leans in or out when seen from the front. Racing cars run the top
  of the wheel leaning *inwards* (negative camber), because in a corner the body rolls and the
  tyre deforms, and a little negative camber keeps the loaded outside tyre flat on the road.
- **Toe**: whether the front of the wheels point slightly in (toe-in) or out (toe-out) when seen
  from above. It trades straight-line stability against how eagerly the car turns in.
- **Caster**: how far the steering axis leans back. It gives the steering its self-centring feel.

Too much camber and the tyre runs on its inside edge on the straights, overheating it. Teams set
camber as far as Pirelli's limits and tyre temperatures allow.
""",
        "engineer": """
**Camber gain.** As the body rolls, the outside wheel would lean outwards with it (positive camber),
which loses grip. Double-wishbone geometry with a shorter upper arm makes the wheel gain negative
camber as it rises, cancelling part of the roll. The demo uses a simple gain of 0.6° per degree of
roll.

**Roll centre.** Lines drawn through the wishbones meet at the wheel's *instant centre*; joining
the instant centres of left and right wheels to their contact patches gives the *roll centre*, the
point the body rolls about. Its height sets how much lateral load transfer goes through the links
rather than the springs.

**Pirelli limits.** For safety, Pirelli publishes maximum camber and minimum pressures for each
race, because extreme camber can overheat the tyre's inside shoulder and damage it.
""",
        "deep": """
**Bump steer.** If the steering track rod isn't aligned with the wishbones, the wheel steers itself
as the suspension moves: unwanted toe change over bumps or under downforce. Designers place the
steering rack so bump steer is close to zero, or deliberately small, to tune stability.

**Kinematics vs compliance.** Real parts bend. Under a few tonnes of load, wishbones, uprights and
bearings deflect enough to change camber and toe by fractions of a degree, which matter to the
tyre. Teams measure this "compliance" on rigs and design it in.
""",
        "widget": W.camber_demo,
        "widget_blurb": "Static camber and body roll decide the outside tyre's angle in the corner.",
        "terms": ["grip"],
        "quiz": quiz(
            ("Negative camber means the top of the wheel leans…", ["outwards", "inwards", "forwards", "backwards"], 1,
             "It keeps the loaded tyre flat in a corner."),
            ("Toe is seen from…", ["the front", "above", "the side", "below"], 1, "Whether the wheels point in or out."),
            ("Caster gives the steering…", ["more lock", "self-centring feel", "less weight", "more grip"], 1,
             "The steering axis leans back."),
            ("Camber gain means…", ["the wheel gains negative camber as it rises", "camber never changes",
                                    "toe increases", "the tyre grows"], 0, "It cancels some of the body roll."),
            ("Why does Pirelli limit camber?", ["To slow cars down", "Extreme camber can overheat and damage the tyre",
                                                "For looks", "Cost"], 1, "Safety."),
        ),
        "sources": SOURCES,
    },
    {
        "id": "3.5",
        "title": "Springs, dampers and heave",
        "summary": "How stiff, how damped: holding the floor steady without upsetting the tyres.",
        "basics": """
**Springs** hold the car up and decide how much it moves under load. **Dampers** (shock absorbers)
slow that movement down so the car doesn't keep bouncing.

On a ground-effect car the floor must stay at an almost constant height for the aerodynamics, so
F1 cars run very stiff springs, far stiffer than any road car. But too stiff and the tyres skip
over bumps and kerbs, losing contact and grip. Every setup is a compromise between a stable floor
and tyres that stay in contact with the road.

Dampers then control *how fast* the car moves. Too little damping and it bounces; too much and it
can't follow bumps.
""",
        "engineer": """
**The quarter-car model.** One corner of the car as a mass $m$ on a spring $k$ and a damper $c$:

$$\\omega_n = \\sqrt{\\frac{k}{m}}, \\qquad f_n = \\frac{\\omega_n}{2\\pi}, \\qquad \\zeta = \\frac{c}{2\\sqrt{km}}$$

$f_n$ is the **natural frequency**: road cars sit around 1–1.5 Hz, while F1 cars run several times
higher. $\\zeta$ is the **damping ratio**: 1 is critically damped (no overshoot); around 0.6–0.8
settles fastest with little overshoot. The demo shows the body's response to a 20 mm kerb.

**Heave, roll and pitch springs.** Third (heave) elements stiffen the car against moving straight
down under downforce without stiffening single-wheel bumps or roll. Anti-roll bars stiffen roll
only. Separating these lets engineers support the aero platform and still let the tyres work.
""",
        "deep": """
**Wheel rate vs spring rate.** The stiffness the tyre feels is the spring rate times the motion
ratio squared, in series with the tyre's own vertical stiffness. With very stiff springs, the
tyre's sidewall becomes a large part of the suspension, which is one reason the 2022 switch to
lower-profile 18-inch tyres changed setups.

**Dampers by speed.** Dampers behave differently at low shaft speeds (body motion: roll, pitch,
heave) and high speeds (bumps and kerbs). Teams tune both ranges, and separately for compression
and rebound. Kerb-riding circuits like Monza and Austin need softer high-speed damping than smooth
street tracks.
""",
        "widget": W.quarter_car,
        "widget_blurb": "One corner of the car hitting a 20 mm kerb: spring, damper and mass.",
        "terms": ["ground effect"],
        "quiz": quiz(
            ("What do dampers do?", ["Hold the car up", "Slow down movement so the car doesn't keep bouncing",
                                     "Steer", "Brake"], 1, "Springs hold it up; dampers control the motion."),
            ("Why do F1 cars run very stiff springs?", ["Comfort", "To keep the floor at a steady height",
                                                        "To save weight", "Rules require it"], 1,
             "Ground-effect floors are height-sensitive."),
            ("Natural frequency is…", ["√(k/m) / 2π", "k × m", "c / m", "m / k"], 0, "Spring over mass, square-rooted."),
            ("A damping ratio of 1 means…", ["lots of bouncing", "critically damped: no overshoot", "no damper",
                                             "broken"], 1, "The fastest return without overshoot."),
            ("A heave spring stiffens the car against…", ["roll", "moving straight down", "steering", "braking only"], 1,
             "It supports downforce without stiffening roll."),
        ),
        "sources": SOURCES,
    },
    {
        "id": "3.6",
        "title": "Ride height and rake",
        "summary": "A few millimetres of ride height can be worth tenths of a second, until the floor stalls.",
        "basics": """
**Ride height** is how high the car sits off the ground. On a ground-effect car, running the floor
closer to the track speeds up the air underneath, lowers its pressure and adds downforce. So teams
want to run as low as possible.

But there's a limit. Get too close and the airflow under the floor **stalls**: downforce suddenly
drops, the car rises, the flow reattaches, the car is sucked down again, and the cycle repeats.
That's **porpoising**, the violent bouncing seen in 2022. Teams also have a wooden **plank** under
the car that must not wear away more than a set amount, which stops them running too low.

**Rake** is the nose-down angle of the car. Before 2022, high-rake cars used it to make the floor
work like a diffuser. Today's floors run much flatter.
""",
        "engineer": """
**Aero maps.** Teams measure downforce, drag and balance against front and rear ride height (and
yaw, steering and roll) in the wind tunnel and CFD. The car's setup then aims to keep the floor
inside the best part of that map at every point of the lap: under braking (nose dives), at top
speed (the car is pushed down by downforce) and in slow corners (the car rides higher).

**Why it's hard.** Downforce grows with $v^2$, so the car squashes onto its springs at high speed.
Stiff springs and heave elements keep the floor from bottoming out at 330 km/h while still letting
it run low enough in slow corners.

The demo uses an illustrative aero map and the lap simulator to show what a few millimetres are
worth.
""",
        "deep": """
**The stall.** Underbody flow accelerates through the throat between the floor and the track.
Too small a gap and the boundary layers on the floor and the track grow into each other, the
pressure recovery in the diffuser fails and the flow separates. The loss is abrupt and the
recovery hysteretic, which is what drives the oscillation (Module 4.11).

**Plank and skid rules.** The plank's thickness is measured after the race; excessive wear means
disqualification (as in the 2023 United States Grand Prix). The FIA also introduced a vertical
oscillation metric in 2022 to limit porpoising for safety.
""",
        "widget": W.ride_height_demo,
        "widget_blurb": "An illustrative floor's downforce against ride height, and its lap time on the simulator.",
        "data": [("Setup Garage", "The downforce slider under Advanced does the same thing directly.")],
        "terms": ["ground effect", "downforce"],
        "quiz": quiz(
            ("Lower ride height on a ground-effect car usually gives…", ["less downforce", "more downforce, up to a point",
                                                                         "more drag only", "nothing"], 1,
             "Until the floor stalls."),
            ("Porpoising is…", ["a pit stop", "bouncing caused by the floor stalling and recovering", "tyre wear",
                                "a type of corner"], 1, "Seen widely in 2022."),
            ("What stops teams running too low?", ["Nothing", "Plank wear rules and porpoising", "Tyre rules", "Fuel"], 1,
             "Excess plank wear means disqualification."),
            ("Why does the car run lower at high speed?", ["Less fuel", "Downforce squashes it onto its springs",
                                                           "The track is flatter", "It doesn't"], 1,
             "Downforce grows with speed squared."),
            ("An aero map shows…", ["the circuit", "downforce and balance against ride height and attitude",
                                    "the team's factory", "weather"], 1, "Measured in tunnels and CFD."),
        ),
        "sources": SOURCES + ["FIA Formula 1 Technical Directive TD039 (2022), on vertical oscillations."],
    },
    {
        "id": "3.7",
        "title": "Differentials and traction",
        "summary": "How the two rear wheels share the engine's torque in a corner.",
        "basics": """
In a corner the outside rear wheel travels further than the inside one, so it must turn faster.
A **differential** lets them. An **open** differential sends both wheels the same torque, which
means the lightly loaded inside wheel decides how much drive the car gets: when it spins, the car
loses traction.

A **locked** differential turns both wheels together. It gives far better traction but fights
the car's turning, pushing it straight on.

F1 cars use a **limited-slip** differential whose locking is controlled hydraulically and changes
through the corner: fairly open on entry (to help the car turn), locked on exit (for traction). The
driver adjusts the settings from the steering wheel, corner by corner if needed.
""",
        "engineer": """
**Open diff:** torque is split equally, so the drive force is limited to twice the inside wheel's
grip. In a corner the inside rear has lost load to weight transfer, so that limit is low.

**Locked diff:** each wheel can use its own grip, so drive approaches the sum of both. But because
the wheels are forced to the same speed, the faster-moving outside wheel is held back and the
inside one pushed forward, creating a yaw moment that resists turning (understeer on entry and
mid-corner), or, if the rears are at the limit, snap oversteer on exit.

**Entry, mid, exit.** F1 diffs typically have separate settings for off-throttle (entry), mid-corner
and on-throttle (exit). Engine braking and energy recovery under braking also act through the diff,
so the entry setting affects rear stability under braking.
""",
        "deep": """
**Traction control is banned** (since 2008, with the standard ECU), so traction out of slow corners
depends on the diff, the rear suspension, the throttle map and the driver's right foot. That's why
Car DNA's traction measurement differs between cars even at the same circuit.

**Interaction with energy recovery.** Since 2014 the MGU-K harvests under braking through the
rear axle, adding braking torque at the rear. Brake-by-wire blends the friction brakes to keep the
total stable, and the diff's entry setting has to cope with the varying rear torque.
""",
        "widget": W.diff_demo,
        "widget_blurb": "Drive force out of a corner with an open, locked or partly locked differential.",
        "data": [("Car DNA", "Traction out of slow corners, measured for every car.")],
        "terms": ["grip", "power"],
        "quiz": quiz(
            ("Why do the rear wheels need to turn at different speeds in a corner?", ["The outside wheel travels further",
                                                                                     "Tyre wear", "Rules", "They don't"], 0,
             "A differential allows it."),
            ("An open diff's traction is limited by…", ["the outside wheel", "the inside, lightly loaded wheel",
                                                       "the engine", "the brakes"], 1, "Equal torque to both."),
            ("A fully locked diff tends to…", ["help the car turn", "push the car straight on", "save fuel", "cool tyres"], 1,
             "It resists the speed difference."),
            ("F1 diff settings are typically split into…", ["one setting", "entry, mid-corner and exit", "wet and dry",
                                                            "qualifying only"], 1, "Adjustable from the wheel."),
            ("Traction control in F1 is…", ["mandatory", "banned", "only in the wet", "only for rookies"], 1,
             "Banned since 2008."),
        ),
        "sources": SOURCES,
    },
    {
        "id": "3.8",
        "title": "Steering",
        "summary": "Ackermann, power steering and why the driver feels the tyres through the wheel.",
        "basics": """
When a car turns, its inside front wheel follows a tighter circle than the outside one, so it needs
to turn slightly more. Geometry that does this is called **Ackermann** steering, after the
19th-century coachbuilder's patent. It's perfect for parking; at racing speeds it's less clear-cut,
because both tyres run at slip angles and the outside tyre does most of the work. Many F1 cars use
little Ackermann, or even the opposite (*anti-Ackermann*).

F1 cars have **power steering**, but the driver still feels the tyres through the wheel. As the
front tyres approach their limit, the steering goes light: that feedback is how drivers sense
understeer before it happens.
""",
        "engineer": """
**Ackermann angles.** With wheelbase $L$ and track $t$, on a corner of radius $R$:

$$\\delta_{in} = \\arctan\\frac{L}{R - t/2}, \\qquad \\delta_{out} = \\arctan\\frac{L}{R + t/2}$$

"% Ackermann" says how much of that difference the geometry gives: 100 % is perfect, 0 % parallel
steering, below 0 anti-Ackermann.

**Why the steering goes light.** The tyre's lateral force acts slightly behind the centre of the
contact patch (the *pneumatic trail*). As the tyre approaches its peak, that trail shrinks, so the
self-aligning torque the driver feels drops before the cornering force does: an early warning of
the limit.
""",
        "deep": """
**Steering ratio and lock.** F1 cars use a quick ratio and small lock (well under one turn from
lock to lock), with extra lock needed only at Monaco's hairpin, where some teams fit special
steering arms.

**Clever steering: DAS.** In 2020 Mercedes raced a "Dual Axis Steering" system: pushing and pulling
the wheel changed the front toe on the straights. It was legal that year and then banned from 2021,
a good example of the rules as a design box (Module 1.2).
""",
        "widget": W.ackermann_demo,
        "widget_blurb": "Inside and outside wheel angles for a corner radius and an Ackermann percentage.",
        "terms": ["wheelbase"],
        "quiz": quiz(
            ("Ackermann geometry turns…", ["both wheels equally", "the inside wheel more than the outside",
                                           "the outside wheel more", "the rear wheels"], 1, "It follows the tighter circle."),
            ("Why do many F1 cars use little Ackermann?", ["Cost", "At speed both tyres slip and the outside tyre does most work",
                                                           "Rules", "Weight"], 1, "Low-speed geometry matters less."),
            ("Steering going light warns the driver that…", ["the brakes are hot", "the front tyres near their limit",
                                                             "the engine is failing", "it's raining"], 1,
             "Pneumatic trail shrinks near the peak."),
            ("DAS let Mercedes change…", ["engine modes", "front toe on the straights", "brake bias", "gear ratios"], 1,
             "Raced in 2020, banned from 2021."),
            ("Anti-Ackermann means…", ["no steering", "the outside wheel turns more", "four-wheel steering", "power steering"], 1,
             "Below 0 % Ackermann."),
        ),
        "sources": SOURCES,
    },
    {
        "id": "3.9",
        "title": "Building a lap simulator",
        "summary": "Every idea so far, assembled into the engine behind this app's Simulator pages.",
        "basics": """
You now have every piece needed to build a lap simulator, the program that works out the fastest
possible lap for a car. This app's own simulator does it in four steps, and the demo lets you
watch each one:

1. **Corner limit:** at every point, the fastest speed the tyres allow sideways, with downforce
   helping more the faster you go.
2. **Forward pass:** starting from the slowest corner, accelerate as hard as the engine, the rear
   tyres and the air allow.
3. **Backward pass:** going backwards from the same point, brake as late as the tyres allow.
4. **The lap:** at every point, the car's speed is the lowest of the three. Add up the time.

It's the same method teams used for decades, and still use for quick studies.
""",
        "engineer": """
**What each step uses from this course:**

- *Corner limit*: $m v^2 \\kappa = \\mu(N)\\,N$ with $N = mg + \\tfrac12\\rho C_zA v^2$ and load
  sensitivity in $\\mu(N)$ (2.5), solved for $v$ by bisection at every point.
- *Forward pass*: $m\\,a = \\min(P/v,\\ \\text{rear grip}) - \\tfrac12\\rho C_xA v^2 - C_{rr}N - mg\\sin\\theta$,
  with the friction ellipse (2.4) leaving less traction mid-corner.
- *Backward pass*: braking grip from the friction ellipse plus drag and rolling resistance.
- *Track*: a smoothed spline through the real fastest lap, giving curvature and slope every 4 m.

**What it leaves out:** weight transfer (3.1), balance (3.2), suspension (3.3–3.6), the
differential (3.7) and steering (3.8). Adding those turns a point-mass simulator into a full
vehicle model, the next step teams take.
""",
        "deep": """
**From point mass to full vehicle.** Professional lap simulators solve an optimal-control
problem: find the steering, throttle and brake inputs over the whole lap that minimise lap time,
for a vehicle model with four tyres, suspension, aero maps and a power unit. They're solved with
large-scale nonlinear optimisation and take minutes to hours per lap. Our quasi-steady-state
method takes 3 ms because it skips all of that, and still lands within about 16 km/h of the real
speed trace on average after calibration (see the About page).

**Calibration as inverse problem.** Fitting wing, grip and power to a real lap is how this app
learns each circuit's car, and how Car DNA measures each team. It's a simple version of what teams
call *correlation*: making the simulation agree with the track.
""",
        "widget": W.build_lapsim,
        "widget_blurb": "Step through the simulator: corner limit, forward pass, backward pass, the lap.",
        "data": [("Lap Simulator", "The finished lap in 3D next to the real one."),
                 ("Car DNA", "The same simulator fitted to each team's fastest lap.")],
        "terms": ["lap simulator", "quasi-steady-state", "friction circle", "load sensitivity"],
        "quiz": quiz(
            ("The first step of the simulator is…", ["the backward pass", "the corner limit", "the lap time", "gears"], 1,
             "The fastest speed the tyres allow at each point."),
            ("The forward pass starts from…", ["the start line", "the slowest corner", "the fastest straight", "anywhere"], 1,
             "So it never starts too fast."),
            ("The car's speed at each point is…", ["the highest of the three", "the lowest of the three", "the average",
                                                   "the corner limit"], 1, "Whatever limits it most."),
            ("What does our simulator leave out?", ["Downforce", "Weight transfer and suspension", "Power", "Curvature"], 1,
             "It's a point mass."),
            ("Fitting the simulator to a real lap is called…", ["guessing", "calibration or correlation", "racing", "sampling"], 1,
             "Making the model agree with reality."),
        ),
        "sources": SOURCES + ["Perantoni, G. & Limebeer, D. J. N. (2014). Optimal control for a Formula One car with "
                              "variable parameters. Vehicle System Dynamics 52(5)."],
    },
]
