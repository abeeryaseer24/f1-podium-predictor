"""Module 15: History of F1 engineering."""
from academy_content.m4 import ch

SOURCES = ["Nye, D. (1985). The Autocourse History of the Grand Prix Car 1966–85. Hazleton.",
           "Wright, P. (2001). Formula 1 Technology. SAE International.",
           "FIA and Formula 1 archive, technical regulations by season, fia.com and formula1.com"]

CHAPTERS = [
    ch("15.1", "Front engine to mid engine", "How Cooper put the engine behind the driver, and everyone followed.",
       """
In the 1950s Grand Prix cars had their engines in front of the driver, like road cars. Cooper, a small
British team, put the engine **behind** the driver. Stirling Moss won in Argentina in 1958 in a privately
entered Cooper, and Jack Brabham won the 1959 and 1960 titles in works Coopers. Within two years every
front-runner had moved the engine back.

In 1962 Lotus's Colin Chapman went further: the Lotus 25 had a **monocoque** chassis, a stiff aluminium
tub instead of a frame of tubes. In 1967 the Lotus 49 bolted the new Cosworth DFV engine straight to the
tub as part of the structure.
""",
       """
**Why mid-engine wins.** The heaviest component sits near the middle of the car, lowering the polar moment
of inertia (the car changes direction more easily), puts weight on the driven rear wheels for traction,
and lets the car be lower and narrower at the front, with less frontal area.

**The DFV.** As a stressed member, the engine carried the rear suspension loads, saving a subframe's
weight. The Cosworth DFV went on to win over 150 Grands Prix, the most of any engine design.
""",
       """
**Polar moment.** Yaw acceleration is torque divided by the moment of inertia about the vertical axis,
$\\ddot\\psi = M_z / I_z$. Moving mass towards the centre cuts $I_z$, so the same tyre forces turn the car
faster: the same reason the 2026 rules shrink the car's length.
""",
       [("Who won titles in 1959 and 1960 with a mid-engined Cooper?", ["Jack Brabham", "Juan Manuel Fangio", "Jim Clark", "Niki Lauda"], 0,
         "Moss had won in a Cooper in 1958."),
        ("The Lotus 25 (1962) introduced…", ["a monocoque chassis", "wings", "turbos", "ground effect"], 0, "A stiff tub."),
        ("A mid-engine layout helps because…", ["mass is near the centre, so the car turns more easily", "it's louder", "rules", "cheaper"], 0,
         "Lower polar moment."),
        ("The Cosworth DFV was used as…", ["a stressed member of the chassis", "a gearbox", "a wing", "a brake"], 0, "From the Lotus 49.")],
       sources=SOURCES),

    ch("15.2", "Wings arrive (1968)", "Downforce changes racing for ever, after a dangerous start.",
       """
In 1968 wings appeared on F1 cars: Ferrari and Brabham ran rear wings at Spa, and within weeks Lotus and
others had tall wings on struts, some mounted straight on the suspension. Lap times fell sharply: the
wings pushed the tyres into the road.

They also broke. At the 1969 Spanish Grand Prix both Lotuses crashed when their high wings collapsed, and
high, strut-mounted wings were banned. Wings stayed, but low and fixed to the body.
""",
       """
**Why mount wings on the suspension?** Downforce acting directly on the wheels loads the tyres without
compressing the springs, so the car keeps its ride height. Mounted on the body, downforce squashes the
suspension. It worked, but the struts failed under load.

**Downforce vs mass.** Wings add grip without adding mass: at 250 km/h a modern car makes more downforce
than its own weight (Module 4.3).
""",
       """
**The long arc.** From 1968 on, aerodynamics became the main area of development; today aerodynamics
departments are the biggest in every team (Module 14.3), and most rule changes since have been about
controlling downforce, drag and the wake.
""",
       [("Wings first appeared on F1 cars in…", ["1950", "1968", "1978", "1994"], 1, "At Spa."),
        ("Why were high wings banned in 1969?", ["They failed, causing crashes", "They were too slow", "Sponsors", "Noise"], 0, "Spain 1969."),
        ("Wings mounted on the suspension loaded…", ["the tyres without compressing the springs", "the engine", "the driver", "nothing"], 0,
         "Ride height stayed."),
        ("Wings add grip without adding…", ["mass", "drag", "speed", "noise"], 0, "Downforce.")],
       data=[("Wind Tunnel", "See how a wing makes lift and drag.")], terms=["downforce"], sources=SOURCES),

    ch("15.3", "Ground effect (1978) and why it was banned", "The whole car became a wing.",
       """
Lotus discovered that the **underside** of the car could make far more downforce than the wings. The Lotus
78 (1977) and 79 (1978) had sidepods shaped like upside-down wings, with **sliding skirts** sealing the gap
to the track. Mario Andretti won the 1978 title.

Brabham answered with the BT46B "fan car", which sucked air from under the car; it won its only race and was
withdrawn. Ground effect made cornering speeds soar, and cars became stiff, brutal and dangerous: skirts
were banned in 1981 and flat floors required from 1983.
""",
       """
**How it works.** Air squeezed through the narrow gap under the car speeds up and its pressure drops
(Bernoulli, Module 4.1). Skirts stopped air leaking in from the sides, keeping the pressure low. But if a
skirt stuck or the car bottomed, downforce vanished at once, with no warning to the driver.

**Ride height sensitivity.** Ground-effect downforce depends strongly on how close the floor is to the
track, so suspension became almost rigid to keep the gap constant.
""",
       """
**The return.** When ground effect came back in 2022 (15.10), the same sensitivity returned as porpoising
(Module 4.11): the floor stalls as it gets too close, downforce drops, the car rises, downforce returns,
and the cycle repeats.
""",
       [("The 1978 champion car using ground effect was the…", ["Lotus 79", "Ferrari 312T", "McLaren MP4/4", "Brabham BT52"], 0, "Andretti."),
        ("Sliding skirts…", ["sealed the gap between the sidepods and the track", "were brake parts", "cooled the engine", "were wings"], 0,
         "Keeping pressure low."),
        ("The Brabham BT46B used…", ["a fan to suck air from under the car", "a turbo", "six wheels", "a jet"], 0, "Won once."),
        ("Flat floors were required from…", ["1983", "1968", "2009", "2022"], 0, "After skirts went in 1981.")],
       widget=None, data=[("Porpoising Lab", "Why ground-effect cars bounce.")], terms=["ground effect"], sources=SOURCES),

    ch("15.4", "The turbo era", "From Renault's 'yellow teapot' to engines with over 1,000 horsepower.",
       """
In 1977 Renault brought the first **turbocharged** engine to F1: a 1.5-litre turbo against 3-litre
naturally aspirated engines. It was slow and unreliable at first (nicknamed the "yellow teapot" for its
smoke), but by 1983 Nelson Piquet won the title with a BMW turbo, and soon everyone had one.

Qualifying engines with the boost turned up made well over 1,000 horsepower for a lap. Turbos were
banned after 1988, when McLaren's Honda-powered MP4/4 won 15 of the 16 races.
""",
       """
**Why a turbo?** It uses exhaust energy to drive a compressor that forces more air into the engine, so a
small engine burns more fuel per cycle and makes far more power. Early turbos had big **lag**: power arrived
late after the driver pressed the throttle, a challenge on corner exit.

**Controlling it.** The rules progressively limited boost pressure and fuel to tame the power before
banning turbos outright for 1989.
""",
       """
**Turbos came back** in 2014 as part of the hybrid power unit (15.9), with a fuel-flow limit instead of a
boost limit, and the MGU-H using exhaust energy to remove turbo lag.
""",
       [("The first turbo F1 engine (1977) was built by…", ["Renault", "Ferrari", "Honda", "Cosworth"], 0, "The 'yellow teapot'."),
        ("The first turbo champion was…", ["Nelson Piquet, 1983", "Ayrton Senna, 1988", "Niki Lauda, 1975", "Jim Clark"], 0, "With BMW."),
        ("Turbo lag is…", ["the delay before power arrives", "a gearbox fault", "tyre wear", "a brake"], 0, "Exit challenge."),
        ("McLaren's MP4/4 in 1988 won…", ["15 of 16 races", "half the races", "one race", "none"], 0, "The last turbo year.")],
       data=[("Engine Room", "Power units through the eras, with their sound.")], sources=SOURCES),

    ch("15.5", "Active suspension and driver aids (1992–93)", "When computers drove the car, and the FIA said stop.",
       """
In 1992 and 1993 Williams dominated with cars full of electronics: **active suspension** (computer-controlled
hydraulics that held the car at the perfect ride height), **traction control**, anti-lock brakes and, in
testing, a continuously variable transmission. Nigel Mansell (1992) and Alain Prost (1993) won the titles.

For 1994 the FIA banned most of these aids, to put the driver back at the centre and to cut costs.
""",
       """
**Active suspension** replaced springs and dampers with hydraulic actuators driven by a computer reading
sensors, so the car's ride height and attitude stayed constant under braking, cornering and over bumps: a
stable platform for the aerodynamics.

**Traction control** cut engine power when the rear wheels started to spin. It returned legally from 2001 to
2007, then was banned again with the standard ECU (Module 10.1).
""",
       """
**Why ban good engineering?** Rules balance performance, cost, safety and spectacle. Active suspension made
the car faster and more stable, but it was expensive and, with traction control, reduced the driver's role.
Some of it lives on in road cars (adaptive dampers, traction control, ABS), a reminder that racing
technology often finds a home elsewhere.
""",
       [("Active suspension used…", ["computer-controlled hydraulics", "bigger springs", "softer tyres", "no suspension"], 0, "Constant ride height."),
        ("Which team dominated 1992–93 with driver aids?", ["Williams", "McLaren", "Ferrari", "Lotus"], 0, "Mansell and Prost."),
        ("Most driver aids were banned for…", ["1994", "1980", "2010", "2026"], 0, "And traction control again from 2008."),
        ("Traction control works by…", ["cutting power when the rear wheels spin", "braking the front", "adding downforce", "steering"], 0, "Grip control.")],
       sources=SOURCES),

    ch("15.6", "The V10 years", "Screaming 3-litre engines near 20,000 rpm.",
       """
From 1995 engines were 3-litre, and from 2000 they had to be **V10s**. It was an era of extraordinary
engines: light, compact and revving towards 20,000 rpm, with a sound many fans still miss. Michael
Schumacher and Ferrari won five titles in a row from 2000 to 2004.

In 2006 the rules switched to 2.4-litre **V8s**, which were later frozen in development and limited to
18,000 rpm, to cut costs.
""",
       """
**Why rpm means power.** Power is torque times engine speed. With a fixed displacement, the way to more
power is to run the engine faster, which needs light pistons, short strokes and, from the 1990s,
pneumatic valve springs instead of steel ones (steel springs can't follow the cam at those speeds).

**Reliability.** Engines had to last longer as the rules progressed: from a fresh engine every session
to one engine per two race weekends by 2005.
""",
       """
**The sound.** A V10 at 19,000 rpm fires each cylinder about 158 times a second; with ten cylinders that's
roughly 1,580 firings a second, the high-pitched scream. The Engine Room page synthesises it live from the
firing order and rpm.
""",
       [("V10s were compulsory from…", ["2000", "1980", "2014", "2026"], 0, "3-litre since 1995."),
        ("V10s revved to nearly…", ["9,000 rpm", "20,000 rpm", "50,000 rpm", "5,000 rpm"], 1, "Light pistons, pneumatic valves."),
        ("Pneumatic valve springs were needed because…", ["steel springs can't follow the cam at those speeds", "they're cheaper", "rules",
                                                          "they're louder"], 0, "Valve float."),
        ("V10s were replaced in 2006 by…", ["2.4-litre V8s", "turbos", "V12s", "electric motors"], 0, "To cut costs.")],
       data=[("Engine Room", "Hear the V10 at any rpm.")], sources=SOURCES),

    ch("15.7", "Blown diffusers, the double diffuser, the F-duct", "Three loopholes that won races.",
       """
**The double diffuser** (2009): Brawn, Toyota and Williams found a gap in the rules that let them stack a
second diffuser above the first, adding downforce. Brawn won both titles in its only season.

**The F-duct** (2010): McLaren let the driver block a hole in the cockpit with a knee or hand, sending air to
the rear wing to stall it on the straights and cut drag.

**Blown diffusers** (2010–11): Red Bull and others aimed the exhaust at the diffuser, and kept the exhaust
blowing even off the throttle, so downforce stayed up in slow corners.
""",
       """
**Stalling a wing.** A wing makes downforce as long as the air follows its surface. Blow air through a slot
at the right place and the flow separates: downforce and drag both collapse. The F-duct did that on demand,
and DRS (2011–2025) did the same thing legally with a moving flap.

**Exhaust blowing.** Hot, fast exhaust gas energises the flow over the diffuser, so it can work at a
steeper angle without separating. Engine maps that kept gas flowing with the throttle closed made it work
in braking too.
""",
       """
**All banned.** Each was legal at first and banned within a season or two. They show how rules are read:
the double diffuser used a gap between the "reference plane" and "step plane" definitions; the F-duct used
the fact that the driver wasn't a "moving part" of the bodywork. That's why rules are now written with
broad catch-all clauses.
""",
       [("Brawn won the 2009 titles helped by…", ["the double diffuser", "a turbo", "active suspension", "a fan"], 0, "A loophole."),
        ("The F-duct worked by…", ["the driver stalling the rear wing", "a bigger engine", "softer tyres", "a lighter car"], 0, "Less drag on straights."),
        ("Off-throttle exhaust blowing kept…", ["downforce up in slow corners", "the engine cool", "fuel low", "tyres hard"], 0, "Red Bull 2010–11."),
        ("Stalling a wing collapses…", ["downforce and drag", "only drag", "only weight", "nothing"], 0, "Flow separation.")],
       sources=SOURCES),

    ch("15.8", "DAS and clever loopholes", "Steering wheels that push, mass dampers and other ideas.",
       """
In 2020 Mercedes' drivers could push and pull the steering wheel to change the front wheels' **toe** on the
straights (Dual Axis Steering, **DAS**), helping warm the tyres and cut drag. It was legal that year and
banned from 2021.

Others came before it. Renault's **mass damper** (2005–06), a spring-mounted weight in the nose, calmed the
car over kerbs until it was banned as a moving aerodynamic device. **Inerters** (first called J-dampers)
controlled suspension movement in a new way and spread through the grid.
""",
       """
**Toe and tyres.** Toe-out helps turn-in but scrubs the tyres on the straights, adding drag and heat.
DAS let the driver straighten the wheels on the straights and restore toe for the corners, the best of both.

**Mass damper.** A tuned mass on a spring absorbs vibration at its natural frequency. Keeping the nose
steady kept the front wing at a constant height, which is why the FIA ruled it an aerodynamic device.
""",
       """
**Why loopholes keep coming.** The rules can't list every possible design, and teams employ people to find
what the text allows. Each new rule creates new edges. The F1 Commission usually lets a clever legal idea
run until the end of the season and then closes it, so the innovator gets their reward but not forever.
""",
       [("DAS changed the front wheels'…", ["toe", "camber", "size", "colour"], 0, "Push-pull steering."),
        ("Renault's mass damper was banned as…", ["a moving aerodynamic device", "too heavy", "unsafe", "a turbo"], 0, "It steadied the nose."),
        ("Toe-out on the straights causes…", ["tyre scrub, drag and heat", "more grip", "nothing", "less weight"], 0, "DAS fixed it."),
        ("Clever legal ideas are usually…", ["allowed to the season's end, then closed", "banned the same day", "kept forever", "fined"], 0,
         "The innovator's reward.")],
       sources=SOURCES),

    ch("15.9", "The hybrid era", "From 2014: 1.6-litre turbo V6s with energy recovery, and record efficiency.",
       """
In 2014 F1 switched to **hybrid power units**: a 1.6-litre turbocharged V6 with two electric machines, the
**MGU-K** (recovering energy under braking) and the **MGU-H** (recovering energy from the turbo's exhaust
gas), feeding a battery. Fuel flow was limited to 100 kg/h, so efficiency became power.

Mercedes got it right first and won eight constructors' titles in a row, from 2014 to 2021. By the end of
the decade the engines turned over half their fuel energy into work, which no road car engine does.
""",
       """
**Why the MGU-H mattered.** It turned the turbo's shaft into a generator (recovering exhaust energy) and a
motor (spinning the turbo up instantly, so no turbo lag). Hard to build, it was a big part of the advantage
of whoever mastered it, and it's dropped for 2026.

**Efficiency as power.** With fuel flow fixed, the only way to more power is to burn the same fuel better:
lean combustion with pre-chamber ignition, high compression and recovery of every joule possible.
""",
       """
**Thermal efficiency above 50%.** A road car engine is typically 30–40% efficient. The F1 hybrids passed 50%
counting the energy recovered, thanks to very lean, fast combustion (turbulent jet ignition), and turbo
compounding through the MGU-H. Module 5 covers the thermodynamics; the Energy Lab lets you run the battery.
""",
       [("The 2014 power unit was…", ["a 1.6-litre turbo V6 hybrid", "a 3-litre V10", "an electric motor only", "a V8"], 0, "With MGU-K and MGU-H."),
        ("The MGU-H recovered energy from…", ["the turbo's exhaust gas", "the brakes", "the driver", "the tyres"], 0, "And removed turbo lag."),
        ("Mercedes won the constructors' title every year from…", ["2014 to 2021", "2000 to 2004", "2010 to 2013", "2022 to 2026"], 0, "Eight in a row."),
        ("With fuel flow fixed, more power comes from…", ["burning fuel more efficiently", "more fuel", "bigger engines", "nothing"], 0,
         "Efficiency is power.")],
       data=[("Energy Lab", "Run the battery round a lap."), ("Engine Room", "The hybrid's energy flows.")], terms=["power unit", "MGU-K"],
       sources=SOURCES),

    ch("15.10", "2022: ground effect returns", "Venturi tunnels to help cars follow, and porpoising.",
       """
In 2022 the rules brought **ground effect** back: shaped tunnels under the car (venturi tunnels) made much
of the downforce, with simpler wings on top. The aim was to cut the **dirty air** behind a car so others
could follow and overtake.

It worked in part: cars could follow more closely. But early in 2022 many cars **porpoised**, bouncing on
the straights as the floor stalled and recovered, and the FIA stepped in with a technical directive and
later rule changes to stiffen floors and raise floor edges.
""",
       """
**Why underfloor downforce helps following.** Wings throw a turbulent wake up and back; floor tunnels leave
a wake that's lifted higher and is less disturbed at the height of the following car's wings. The Dirty Air
Lab compares how much downforce a following car keeps for 2017–21, 2022+ and 2026 cars.

**Porpoising** comes from the floor's strong ride-height sensitivity (15.3): close to the ground, the flow
stalls, downforce drops, the car rises, and the cycle repeats.
""",
       """
**The engineering fix.** Teams raised ride heights, stiffened floors and tuned suspension, giving up some
peak downforce for a stable car. The FIA added a metric for vertical oscillations that cars must stay under,
a rare case of a rule written as a measured limit on the car's behaviour.
""",
       [("The 2022 rules aimed to…", ["cut dirty air so cars could follow", "add turbos", "remove wings", "add weight"], 0, "Ground-effect tunnels."),
        ("Porpoising is…", ["bouncing as the floor stalls and recovers", "tyre wear", "engine failure", "a pit stop"], 0, "On the straights."),
        ("Underfloor downforce helps following because its wake is…", ["higher and less disturbed", "bigger", "hotter", "the same"], 0,
         "Dirty Air Lab shows it."),
        ("The FIA's porpoising fix included…", ["a limit on vertical oscillations", "banning floors", "lower ride heights", "nothing"], 0,
         "A measured limit.")],
       data=[("Porpoising Lab", "Make a ground-effect car bounce."), ("Dirty Air Lab", "Following downforce by era.")],
       terms=["ground effect"], sources=SOURCES),

    ch("15.11", "2026 and after", "Active aero, a 50/50 power split and sustainable fuel.",
       """
The 2026 rules are the biggest change in years. Cars are shorter, narrower and lighter. Front and rear wings
are **active**: they flatten on the straights to cut drag and close for the corners. The power unit splits
its power roughly **half and half** between the combustion engine and a far stronger electric motor (350 kW),
the MGU-H is gone, and the fuel is fully **sustainable**.

DRS is replaced by an **overtake mode**: extra electrical energy for a car close behind another. New
manufacturers joined: Audi with its own team, Ford with Red Bull, Honda with Aston Martin, and Cadillac as a
new team.
""",
       """
**Energy management.** With so much of the power electric, how the battery is harvested and spent round a lap
decides lap time; on long straights a car can run out of electric power ("clipping") before the braking
zone. The Energy Lab and the Energy Challenge are built on exactly this.

**Active aero.** A low-drag straight mode and a high-downforce corner mode let the car be efficient on the
straights without giving up grip in the corners, which a fixed wing can't do.
""",
       """
**After 2026.** Every set of rules is a hypothesis about what will make good racing, sustainable engineering
and close competition. The next changes will respond to how 2026 plays out: energy limits, the overtake mode's
effect, the cost cap and the push for sustainability. Module 16 hands you the pen: design a car yourself.
""",
       [("2026 wings are…", ["active, flattening on the straights", "fixed", "removed", "only at the front"], 0, "Low-drag and high-downforce modes."),
        ("The 2026 power split is roughly…", ["half and half electric and combustion", "all electric", "all combustion", "90/10"], 0,
         "A 350 kW motor."),
        ("DRS is replaced in 2026 by…", ["an overtake mode", "nothing", "a turbo boost", "bigger wings"], 0, "Extra electrical energy."),
        ("Which component is dropped in 2026?", ["The MGU-H", "The MGU-K", "The battery", "The turbo"], 0, "Too complex and costly.")],
       data=[("Energy Lab", "The 2026 battery round a lap."), ("Energy Challenge", "Beat the engineer's deployment plan.")],
       terms=["active aero"], sources=SOURCES),
]
