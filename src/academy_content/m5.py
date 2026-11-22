"""Module 5: Power unit."""
import academy_widgets_m4 as W
from academy_content.m4 import ch

SOURCES = ["Heywood, J. B. (2018). Internal Combustion Engine Fundamentals, 2nd ed. McGraw-Hill.",
           "FIA Formula 1 Technical Regulations, power unit articles (2014–2025 and 2026 issues), fia.com",
           "Mercedes-AMG High Performance Powertrains, public material on thermal efficiency (2017)."]

CHAPTERS = [
    ch("5.1", "Engine thermodynamics", "Turning fuel into motion: the four-stroke cycle and why efficiency is limited.",
       """
An F1 engine is a four-stroke petrol engine, like most car engines, just far more extreme. Each
cylinder repeats four strokes: **suck** air and fuel in, **squeeze** them, **bang** (the spark
ignites the mixture and the expanding gas pushes the piston down), **blow** the exhaust out.

Only part of the fuel's energy becomes motion. The rest leaves as heat in the exhaust and the
cooling system. The fraction that becomes work is the engine's **thermal efficiency**. A typical road
car manages around 30–35 %. The best 2014–2025 F1 power units passed 50 %, counting the energy they
recovered from the exhaust.
""",
       """
**The ideal Otto cycle** (constant-volume combustion) has efficiency

$$\\eta = 1 - \\frac{1}{r^{\\,\\gamma - 1}}$$

with $r$ the compression ratio and $\\gamma \\approx 1.3$–1.4. Higher compression, higher efficiency,
but too high and the mixture ignites on its own (knock, 5.2). The 2014–2025 rules capped compression at 18:1.

**Where the rest goes:** heat lost through the cylinder walls, friction, the work of pumping air in
and out, incomplete combustion, and above all the hot exhaust, which is why recovering exhaust energy
(turbo, MGU-H) mattered so much.
""",
       """
**Brake thermal efficiency** (BTE) is useful work at the crankshaft divided by fuel energy. F1 quotes
of "over 50 %" for 2014–2025 power units include electrical energy recovered from the exhaust by the
MGU-H and returned to the crankshaft. For a lone engine without recovery, the best numbers are in the
mid-40s per cent.

**Why efficiency equals power in F1.** With fuel flow capped (5.4), the only route to more power is
turning more of each gram of fuel into work. That made thermodynamics, not displacement or revs, the
battleground of the hybrid era.
""",
       [("The four strokes are…", ["suck, squeeze, bang, blow", "start, stop, go, turn", "fuel, spark, gear, wheel",
                                   "in, out, up, down"], 0, "Intake, compression, power, exhaust."),
        ("Higher compression ratio gives…", ["lower efficiency", "higher efficiency, up to knock", "more noise only", "nothing"], 1,
         "η = 1 − 1/r^(γ−1)."),
        ("The best 2014–25 F1 power units reached about…", ["20 %", "35 %", "over 50 %", "90 %"], 2, "Counting MGU-H recovery."),
        ("Where does most wasted energy go?", ["Noise", "Hot exhaust and cooling", "Tyres", "Light"], 1, "Heat."),
        ("Why is efficiency the same as power in F1?", ["Fuel flow is capped", "Rules ban power", "Tyres", "Weight"], 0,
         "More work from the same fuel.")],
       widget=W.otto_efficiency, blurb="Ideal efficiency against compression ratio.", terms=["power unit", "power"],
       sources=SOURCES),

    ch("5.2", "Combustion", "Lean burn, pre-chambers and knock: getting more out of every drop of fuel.",
       """
Burning fuel faster and more completely means more work from each cycle. F1 engines run **lean**
(more air than the fuel strictly needs) and use a small **pre-chamber** near the spark plug: the
spark lights a little mixture there, which shoots jets of flame into the main chamber and burns it
quickly and evenly.

The enemy is **knock**: pockets of mixture exploding on their own before the flame reaches them,
hammering the piston. Knock limits compression and boost, so stopping it is worth power.
""",
       """
**Turbulent jet ignition.** A pre-chamber with a few small holes turns one spark into many flame
jets, so even a very lean mixture burns fast. Faster burning means less time for heat to escape and
less chance of knock.

**Lean burn.** With excess air, combustion temperatures fall (less heat lost to the walls) and the
ratio of specific heats rises, both improving efficiency. The cost is harder ignition, solved by the
pre-chamber.

**Fuel matters too.** Fuel companies tune the blend's knock resistance and burn speed within the rules.
""",
       """
**Knock** happens when the unburned "end gas" is compressed and heated by the advancing flame until it
autoignites. Engineers control it with spark timing, charge cooling, combustion speed and fuel
chemistry. Knock sensors listen for it and the engine backs off timing within milliseconds.

**2026 sustainable fuel** behaves differently from fossil petrol: its chemistry affects burn speed and
knock, so fuel and engine are now developed together even more closely.
""",
       [("A pre-chamber…", ["stores fuel", "lights a small charge that jets flame into the cylinder", "cools the engine", "is the turbo"], 1,
         "Turbulent jet ignition."),
        ("Lean burn means…", ["more fuel than air needs", "more air than the fuel needs", "no air", "diesel"], 1, "Excess air."),
        ("Knock is…", ["a pit stop", "the mixture exploding on its own too early", "a gear change", "a sensor"], 1, "It damages engines."),
        ("Why does faster combustion help?", ["Less time for heat loss and knock", "Louder", "Lighter", "Cheaper"], 0, "More efficient."),
        ("Who helps tune knock resistance?", ["Tyre suppliers", "Fuel companies", "Stewards", "Drivers"], 1, "Within the fuel rules.")],
       sources=SOURCES),

    ch("5.3", "Turbocharging", "Using the exhaust's waste energy to force more air into the engine.",
       """
A **turbocharger** has two wheels on one shaft: a **turbine** spun by the hot exhaust, and a
**compressor** that squeezes more air into the engine. More air means more fuel can burn, so more
power from a small engine, and some of the exhaust's wasted energy gets used.

Turbos have a weakness: **lag**. When the driver presses the throttle after a corner, the turbo takes
time to spin up. From 2014 to 2025 F1 solved this with the **MGU-H**, an electric motor on the turbo
shaft that could spin it up instantly (and harvest energy from it when it wasn't needed).
""",
       """
**Pressure ratio.** The compressor raises the intake pressure several times above atmospheric, the
air is cooled in an intercooler (cooler air is denser and reduces knock), and the engine breathes it in.

**MGU-H (2014–2025).** On the turbo shaft: as a generator it took excess exhaust energy that would
have been dumped through a wastegate and turned it into electricity, unlimited by the per-lap harvest
rules; as a motor it eliminated lag. It was brilliant engineering but costly and complex, so it was
dropped for 2026.
""",
       """
**2026 without the MGU-H.** Turbo lag returns as a design problem, managed by turbo sizing, the MGU-K's
torque fill and engine calibration. The loss of free exhaust recovery is one reason the 2026 rules
allow far more harvesting under braking.

**Altitude.** In thin air (Mexico City) the turbo spins faster to deliver the same mass of air,
approaching its speed limit, so engines lose a little power there despite the turbo.
""",
       [("A turbo's turbine is spun by…", ["the crankshaft", "exhaust gas", "the driver", "the wheels"], 1, "Waste energy."),
        ("Turbo lag is…", ["a delay before boost builds", "a rule", "a gear", "fuel"], 0, "The turbo needs to spin up."),
        ("The MGU-H was mounted on…", ["the wheels", "the turbo shaft", "the gearbox", "the wing"], 1, "Motor and generator."),
        ("Why was the MGU-H dropped for 2026?", ["Too slow", "Cost and complexity", "Too loud", "Unsafe"], 1, "And road relevance."),
        ("An intercooler…", ["heats the air", "cools compressed air", "stores energy", "is a radiator for brakes"], 1,
         "Denser air, less knock.")],
       terms=["power unit"], sources=SOURCES),

    ch("5.4", "The fuel-flow limit", "One rule that turned F1 into an efficiency race.",
       """
From 2014 to 2025, F1 limited how fast fuel could flow into the engine: **100 kg per hour** at high
revs, measured by an FIA sensor. It sounds like a fuel-saving rule, but its real effect was deeper:
since nobody could burn fuel faster, the only way to more power was to get more work from every
gram. Engines were judged on **efficiency**, and they became the most efficient piston engines ever built.

For 2026 the limit changed from mass to **energy flow**: 3,000 megajoules per hour of fuel energy,
fair to any sustainable fuel blend whatever its energy per kilogram.
""",
       """
**Power from fuel flow:**

$$P = \\dot m_{fuel} \\times LHV \\times \\eta$$

100 kg/h is 27.8 g/s; at about 43 MJ/kg that's roughly 1.2 MW of chemical power. At 50 % efficiency,
about 600 kW (800 hp) from the combustion side. The demo does the arithmetic.

**2026:** 3,000 MJ/h is 833 kW of fuel energy, so a combustion engine of about 400 kW needs roughly
48 % efficiency; the rest of the car's power comes from the 350 kW MGU-K.
""",
       """
**Policing.** An FIA-homologated ultrasonic flow meter on each car measures flow continuously.
Suspicions of teams getting around the meter (the 2019 Ferrari case, settled privately with the FIA)
show how valuable a few kilograms per hour are.

**Race fuel load.** A separate limit on total race fuel (110 kg in 2019–2025) meant drivers also had to
manage consumption over a race distance, lifting and coasting into corners when needed.
""",
       [("2014–25 fuel flow was limited to…", ["10 kg/h", "100 kg/h", "1,000 kg/h", "unlimited"], 1, "Above 10,500 rpm."),
        ("Why did the limit make efficiency so important?", ["More power needs more work per gram", "It banned turbos", "Cost", "Noise"], 0,
         "Fuel rate was fixed."),
        ("The 2026 limit is on…", ["fuel mass", "fuel energy flow", "engine size", "revs"], 1, "3,000 MJ/h."),
        ("100 kg/h of fuel carries roughly…", ["12 kW", "120 kW", "1.2 MW", "12 MW"], 2, "Of chemical power."),
        ("Who measures fuel flow?", ["Teams only", "An FIA flow meter on each car", "Drivers", "Pirelli"], 1, "Ultrasonic sensor.")],
       widget=W.fuel_flow_power, blurb="Power from a fuel flow and a thermal efficiency.", sources=SOURCES),

    ch("5.5", "Energy recovery", "The MGU-K: harvesting under braking and deploying on the straights.",
       """
The **MGU-K** (Motor Generator Unit – Kinetic) is an electric machine connected to the engine's
crankshaft. Under braking it works as a **generator**, slowing the car and turning some of its energy
of motion into electricity for the battery. On the throttle it works as a **motor**, adding power.

From 2014 to 2025 it was limited to 120 kW. In 2026 it nearly tripled to **350 kW**, roughly the same
as the combustion engine: half the car's power is now electric.
""",
       """
**Limits (2014–2025):** 120 kW either way, 2 MJ harvested per lap by the MGU-K and 4 MJ deployed per
lap (the MGU-H could supply the rest). **2026:** 350 kW, with a much larger harvest allowance and no MGU-H.

**Harvesting costs braking stability.** The MGU-K brakes the rear axle only; as it harvests more or
less, the brake-by-wire system adjusts the rear friction brakes to keep the total steady (Module 7).
""",
       """
**Harvesting on the throttle.** When the battery is short, teams can harvest while the car is
accelerating ("super clipping"): the MGU-K absorbs some engine power near the end of a straight. It
costs top speed but recharges the battery. In 2026 managing harvest and deploy round every lap is a
central part of racing, and the Energy Lab shows why.
""",
       [("MGU-K stands for…", ["Motor Generator Unit – Kinetic", "Main Gear Unit – Key", "Mechanical Grip Unit", "Motor Gas Unit"], 0,
         "Connected to the crankshaft."),
        ("Under braking the MGU-K…", ["adds power", "harvests energy", "does nothing", "heats tyres"], 1, "As a generator."),
        ("The 2026 MGU-K is rated at…", ["60 kW", "120 kW", "350 kW", "1,000 kW"], 2, "Nearly triple."),
        ("The MGU-K acts on…", ["the front axle", "the rear axle (through the engine)", "all wheels", "the turbo"], 1,
         "So brake-by-wire balances the rear."),
        ("'Super clipping' means…", ["harvesting while accelerating", "a fast lap", "a gear", "a pit stop"], 0, "Recharging near the end of a straight.")],
       widget=W.energy_mini, blurb="The battery round a lap for each era.",
       data=[("Energy Lab", "Plan where to deploy and see the clipping.")], terms=["MGU-K", "power unit"], sources=SOURCES),

    ch("5.6", "The battery", "Lithium-ion cells that charge and discharge at enormous power every lap.",
       """
The **energy store** (ES) is a lithium-ion battery, but very different from a phone's. It holds only a
few megajoules (a few kilowatt-hours would be far more), but it charges and discharges at hundreds of
kilowatts, many times every lap, for a whole season. It's built for **power**, not range.

It sits low in the car under the fuel tank, must weigh at least a set minimum, and needs its own
cooling, because pushing that much power in and out makes heat.
""",
       """
**Power vs energy.** A road EV battery might store 60 kWh (216 MJ). An F1 store holds a few MJ but
delivers 120 kW (2014–25) or 350 kW (2026) in bursts of seconds. That needs cells with very low
internal resistance and excellent cooling.

**Usable window.** The battery is never run completely full or empty: a usable window (about 4 MJ) is
used to protect the cells. Our energy model uses that window.
""",
       """
**Thermal management.** Resistive heating grows with current squared, so high-power cells heat quickly;
cell temperature affects both performance and life. Battery cooling is part of the sidepod cooling
puzzle (4.9, Module 9).

**Safety.** A damaged battery can go into thermal runaway. Marshals treat a stopped car carefully until
the car's safety light shows the high-voltage system is safe.
""",
       [("An F1 battery is designed for…", ["range", "power in short bursts", "weight", "noise"], 1, "Hundreds of kW, for seconds."),
        ("Compared with a road EV, an F1 battery stores…", ["much more energy", "much less energy", "the same", "no energy"], 1,
         "A few MJ."),
        ("Where does the battery sit?", ["In the nose", "Low, under the fuel tank", "In the rear wing", "In the sidepod top"], 1,
         "Low centre of gravity."),
        ("Why does the battery need cooling?", ["High current makes heat", "Rules", "Weight", "It doesn't"], 0, "Losses grow with current²."),
        ("The car's safety light tells marshals…", ["the fuel level", "whether the high-voltage system is safe", "the gear", "tyre wear"], 1,
         "Before touching the car.")],
       terms=["power unit"], sources=SOURCES),

    ch("5.7", "Energy management over a lap", "When to harvest, when to deploy, and what clipping is.",
       """
Every lap is an energy budget. The car **harvests** in braking zones and **deploys** on the straights.
If it deploys more than it harvests, the battery drains lap by lap; if it runs out mid-straight, the
car loses the electric power and slows even at full throttle: **clipping**.

Engineers plan deployment corner by corner to get the most lap time from the energy available, and
change the plan for attacking, defending, qualifying and saving.
""",
       """
**Where deployment is worth most.** Electrical power is worth most where the car is power-limited:
accelerating out of slow corners and along long straights. At very high speed drag eats most of the
gain. Teams optimise deployment maps with lap simulation, much like the Energy Lab's plan search.

**Race vs qualifying.** In the race a lap must roughly pay for itself; in qualifying the battery can
start full and be emptied in one lap. The Energy Lab models both.
""",
       """
**2026: an energy-limited formula.** With half the power electric and limited harvesting, some
circuits (long straights, few heavy braking zones) leave the cars short of energy. Active aero, lifting
and coasting, and harvesting on the throttle all become part of the driver's job.
""",
       [("Clipping means…", ["cutting a corner", "running out of electric power mid-straight", "a gear change", "a penalty"], 1,
         "Speed falls even at full throttle."),
        ("Where is deployment worth most?", ["In braking zones", "Where the car is power-limited", "In corners at the limit", "In the pits"], 1,
         "Out of slow corners and on straights."),
        ("In qualifying the battery can…", ["not be used", "start full and be emptied", "only harvest", "be swapped"], 1, "One flat-out lap."),
        ("Which circuits challenge 2026 cars' energy most?", ["Few braking zones, long straights", "Slow street tracks", "All equally",
                                                              "None"], 0, "Little harvest, lots of deploy."),
        ("A deployment map is…", ["a track map", "a plan of where to use electric power", "a pit schedule", "a tyre plan"], 1,
         "Optimised by simulation.")],
       widget=W.energy_mini, blurb="Harvest and deploy round a real circuit.",
       data=[("Energy Lab", "Make your own deployment plan.")], sources=SOURCES),

    ch("5.8", "Sustainable fuels", "From 2026, fuel made without fossil oil.",
       """
From 2026 F1 cars run on **100 % sustainable fuel**: a drop-in petrol made from non-fossil carbon, for
example captured carbon, municipal waste or non-food biomass. Burning it still releases CO₂, but that
carbon came out of the atmosphere (or out of waste) in the first place, so over its life cycle the
fuel adds far less new carbon.

Before that, F1 used E10 (10 % ethanol) from 2022. Sustainable fuel has to meet strict chemical rules
so that it behaves like petrol in the engine.
""",
       """
**Drop-in fuel.** The goal is a fuel that works in existing engines, which is why F1 frames it as road-
relevant. Making it is energy-intensive and currently expensive; F1's volumes are tiny, so the sport's
role is mainly development and demonstration.

**Energy-flow limit.** Because sustainable blends can differ in energy per kilogram, the 2026 limit is on
energy flow (MJ/h), not mass flow, keeping it fair between suppliers.
""",
       """
**Certification.** Suppliers must prove the sustainability of each component through a chain of custody,
audited by the FIA. **Engine-fuel co-development** matters more than ever: combustion speed and knock
(5.2) depend on the molecules, so manufacturers and fuel partners develop together.
""",
       [("2026 F1 fuel is…", ["diesel", "100 % sustainable petrol", "pure ethanol", "hydrogen"], 1, "Non-fossil carbon."),
        ("Burning sustainable fuel…", ["releases no CO₂", "releases CO₂ that came from the atmosphere or waste", "releases water only",
                                       "is banned"], 1, "Lower life-cycle emissions."),
        ("What did F1 use from 2022 to 2025?", ["E10", "Diesel", "Leaded petrol", "Electricity only"], 0, "10 % ethanol."),
        ("Why is the 2026 limit on energy flow?", ["Fair across blends with different energy per kg", "Cheaper", "Louder", "Lighter"], 0,
         "MJ/h, not kg/h."),
        ("A drop-in fuel…", ["needs a new engine", "works in existing engines", "is a battery", "is water"], 1, "Road relevance.")],
       sources=SOURCES),

    ch("5.9", "The 2026 power unit", "Half combustion, half electric, no MGU-H, and new manufacturers.",
       """
The 2026 power unit keeps a 1.6-litre V6 turbo, but almost everything around it changed. The
combustion engine makes roughly **400 kW**; the MGU-K makes up to **350 kW**: close to a 50/50 split.
The MGU-H is gone, the fuel is fully sustainable, and the rules aimed to cut costs and attract new
manufacturers (Audi joined, Ford partnered with Red Bull, Honda continued with Aston Martin).
""",
       """
**Consequences:** much more energy recovered under braking, much more deployed per lap, and energy
management (5.7) becoming central. The cars got lighter and smaller and gained active aero (4.14) so
the power unit's limited energy goes further.

**Overtake mode.** A driver close behind another can use extra electrical deployment, replacing DRS
as the main overtaking aid.
""",
       """
**Cost control.** Power-unit spending has its own cost cap, and some parts are standardised. The aim was
competitive engines without the very expensive MGU-H development race of the previous era.

**Our model.** The Energy Lab's 2026 setting uses rounded public numbers (400 kW + 350 kW, about 8.5 MJ
harvest per lap, a 4 MJ window); real deployment rules are more detailed.
""",
       [("The 2026 combustion engine makes roughly…", ["150 kW", "400 kW", "1,000 kW", "60 kW"], 1, "About half the total."),
        ("Which part was removed for 2026?", ["MGU-K", "MGU-H", "Turbo", "Battery"], 1, "Exhaust-side motor."),
        ("The 2026 power split is roughly…", ["90/10", "50/50", "10/90", "all electric"], 1, "Combustion and electric."),
        ("Which manufacturer joined F1 for 2026?", ["Audi", "Toyota", "BMW", "Porsche"], 0, "Taking over Sauber."),
        ("What replaced DRS as the main overtaking aid?", ["Bigger tyres", "An electrical overtake mode", "Fans", "Nothing"], 1,
         "Extra deployment when close behind.")],
       data=[("Energy Lab", "Compare the 2026 rules with 2022–2025 on any circuit.")], terms=["MGU-K", "power unit"],
       sources=SOURCES),

    ch("5.10", "Reliability and penalties", "A handful of each part per season, and grid places for every extra one.",
       """
Teams can't use a new engine every race. Each driver gets a small number of each power-unit
component per season (engines, turbos, MGU-Ks, batteries, control electronics, exhausts). Using one
more than allowed costs **grid places**: the first extra part a big penalty, further ones less.

So engines must survive several race weekends at full power. Engineers balance performance against
reliability, and teams sometimes take a deliberate penalty at a track where overtaking is easy to get
a fresh set of parts.
""",
       """
**Mileage planning.** Teams plan which engine runs where, rotating fresher units for qualifying and
races and older ones for practice. A failure early in the season can force extra parts and penalties
later.

**Strategic penalties.** If a penalty is unavoidable, taking it at a circuit with easy overtaking (and
taking several new parts at once to build a "pool") limits the cost.
""",
       """
**The Power Units page** in this app tracks parts used against the allowance and how close each driver
is to a penalty (when the data has been entered). The roadmap's Engine Penalty Planner will turn that into
an optimisation: where to take new parts for the smallest total cost.
""",
       [("Using an extra power-unit part costs…", ["money only", "grid places", "nothing", "points"], 1, "A grid penalty."),
        ("Why might a team take a penalty on purpose?", ["To build a pool of fresh parts at an easy-overtaking track", "To slow down",
                                                         "Rules require it", "Sponsors"], 0, "Strategic penalty."),
        ("Teams rotate engines to…", ["save fresher units for qualifying and races", "confuse rivals", "cool them", "sell them"], 0,
         "Mileage planning."),
        ("An early failure…", ["has no effect", "can force penalties later", "gives a bonus", "is fixed free"], 1, "Fewer spares."),
        ("Which page tracks parts used?", ["Tyre Lab", "Power Units", "Lap One", "Quiz"], 1, "When data is entered.")],
       data=[("Power Units", "Parts used and how close each driver is to a penalty.")], sources=SOURCES),

    ch("5.11", "Engines through history", "From V12s to V10 screams to turbo hybrids, and how each one sounded.",
       """
F1 engines have changed with the rules and with technology:

- **1977–1988:** the first turbo era, with qualifying engines rumoured above 1,300 hp for a lap.
- **1989–1994:** 3.5-litre naturally aspirated V8s, V10s and V12s.
- **1995–2005:** 3.0-litre V10s, revving past 19,000 rpm, the loudest era.
- **2006–2013:** 2.4-litre V8s, rev limits and an engine freeze.
- **2014–2025:** 1.6-litre V6 turbo hybrids, the most efficient engines ever raced.
- **2026–:** V6 turbo hybrids with half their power electric, on sustainable fuel.

The demo synthesises each one's sound from its firing frequency.
""",
       """
**Pitch.** A four-stroke fires each cylinder every two turns, so the firing frequency is
$f = \\frac{\\text{rpm}}{60}\\times\\frac{n_{cyl}}{2}$. A V10 at 19,000 rpm fires about 1,580 times a
second; a hybrid V6 at 11,500 rpm about 575. That's why the V10s screamed and the hybrids sound
deeper. Turbos and energy recovery also take energy out of the exhaust, muffling it further.

**Rev limits** were introduced to control cost and power (19,000 then 18,000 rpm for the V8s; 15,000
for the hybrids, though fuel-flow limits meant they rarely went past about 12,000).
""",
       """
**Why power didn't fall as engines shrank.** Turbocharging, efficiency and electric power more than
made up for lost displacement: a 2020s hybrid makes about as much power as a 2005 V10 from just over
half the cylinders and roughly two-thirds of the fuel.
""",
       [("Which era revved past 19,000 rpm?", ["V6 hybrid", "3.0 V10", "1.5 turbo", "2026"], 1, "The loudest era."),
        ("Firing frequency for a four-stroke is…", ["rpm × cylinders", "rpm/60 × cylinders/2", "rpm ÷ 2", "cylinders ÷ rpm"], 1,
         "Each cylinder fires every two turns."),
        ("Why do the hybrids sound deeper?", ["Fewer cylinders, lower revs, and exhaust energy recovered", "Bigger engines", "Rules on noise",
                                              "Different fuel only"], 0, "Lower firing frequency and muffling."),
        ("The first turbo era ran roughly…", ["1950–1960", "1977–1988", "1995–2005", "2014–2025"], 1, "Ended with the 1989 ban."),
        ("Hybrid V6s rarely exceeded about…", ["5,000 rpm", "12,000 rpm", "19,000 rpm", "25,000 rpm"], 1, "Fuel flow capped useful revs.")],
       widget=W.engine_sound_mini, blurb="Hear each era: start the engine and drag the rev counter.",
       data=[("Engine Room", "Every era side by side, and drive a real lap with each one.")], sources=SOURCES),
]
