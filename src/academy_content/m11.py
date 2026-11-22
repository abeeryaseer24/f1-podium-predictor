"""Module 11: Race engineering."""
import academy_widgets_m11 as W
import academy_widgets_m2 as W2
from academy_content.m4 import ch

SOURCES = ["FIA Formula 1 Sporting Regulations (current issue), fia.com",
           "Segers, J. (2014). Analysis Techniques for Racecar Data Acquisition. SAE International.",
           "Public team technical briefings and race-engineer interviews."]

CHAPTERS = [
    ch("11.1", "The weekend from the engineer's chair", "Three practice sessions, qualifying and the race: what the engineers do in each.",
       """
A race weekend is a race against the clock for the engineers as much as the drivers. With only a
few hours of practice, they must find a setup, understand the tyres, and prepare strategies for
qualifying and the race.

- **Practice** builds understanding: setup changes, tyre runs, long runs on race fuel, practice starts.
- **Qualifying** needs the car at its fastest over one lap, on low fuel and fresh tyres.
- **The race** is about managing tyres, fuel, energy and strategy over 300 km.

Each car has a **race engineer** (the voice on the radio), a performance engineer (data and setup),
and specialists for the power unit, tyres, strategy and more, many of them back at the factory
watching live data.
""",
       """
**Sprint weekends** have only one practice session before the car goes into parc fermé (11.4), so the
first hour decides almost everything.

**Mission control.** Teams run operations rooms at their factories with dozens of engineers watching
telemetry, running simulations and feeding the pit wall. The rules limit how many people may work at
the track itself, so much of the analysis happens remotely.

**Run plans.** Every practice minute is scripted in advance: which setup to test, which tyres, how much
fuel, which aero measurements to take (11.2).
""",
       """
**Curfews and working hours.** The sporting regulations limit how long team staff may work at the circuit
overnight, to protect people's health, with a few jokers per season. Simulation work at the factory
continues overnight, often including driver-in-the-loop simulator runs with a reserve driver.
""",
       [("Who is the voice on the driver's radio?", ["The team principal", "The race engineer", "A steward", "Pirelli"], 1,
         "The driver's main contact."),
        ("What are long runs in practice for?", ["Qualifying speed", "Understanding race pace and tyre wear on race fuel", "Starts only",
                                                 "Photos"], 1, "Race preparation."),
        ("Sprint weekends have how many practice sessions?", ["Three", "Two", "One", "None"], 2, "Then parc fermé."),
        ("Where is much of the analysis done?", ["Only at the track", "In factory operations rooms too", "By the FIA", "Nowhere"], 1,
         "Mission control."),
        ("Why are there working-hour curfews?", ["To save money only", "To protect staff health", "Noise rules", "Tyre rules"], 1,
         "Overnight limits at the track.")],
       sources=SOURCES),

    ch("11.2", "Practice run plans", "Every minute scripted: aero tests, setup checks, tyre runs and long runs.",
       """
Practice is planned minute by minute. A typical run plan might start with **aero measurements**
(sensor rakes behind the wheels, flow-visualisation paint), then **setup comparisons** (one change at a
time so its effect is clear), then **short qualifying-style runs** on low fuel, and finally **long runs**
on race fuel to learn how the tyres degrade.

Reading long runs is tricky: as fuel burns off the car gets faster, hiding the tyres' wear. Engineers
**correct for fuel** to see the true degradation, which the demo shows.
""",
       """
**Fuel correction.** At about 0.03 s per kilogram per lap and around 1.5–2 kg burned per lap, fuel alone
makes a car several hundredths faster each lap. Subtract it and the remaining slope is the tyre
degradation the strategy needs (Module 2.9 does this on every race).

**Comparing teams.** Rival teams run different fuel loads and engine modes in practice, so engineers
estimate rivals' fuel from lap times and stint lengths to judge the true pecking order.
""",
       """
**Tyre allocation.** Each driver has a fixed number of sets for the weekend, some of which must be
returned after practice. Using a set in practice means not having it for qualifying or the race, so
run plans are also tyre plans.
""",
       [("Why correct long runs for fuel?", ["Fuel burn hides tyre wear", "Rules", "To save fuel", "It doesn't matter"], 0,
         "The car gets lighter each lap."),
        ("Flow-visualisation paint shows…", ["the team colours", "how air flows over the surface", "tyre wear", "fuel"], 1,
         "Aero checks."),
        ("Why change one setup item at a time?", ["So its effect is clear", "Rules", "To save tyres", "No reason"], 0,
         "Clean comparisons."),
        ("Fuel is worth roughly…", ["0.3 s per kg per lap", "0.03 s per kg per lap", "3 s per kg", "nothing"], 1, "Rule of thumb."),
        ("Why is practice also a tyre plan?", ["Sets used now aren't available later", "Tyres are free", "Rules on colours", "Weather"], 0,
         "Limited allocation.")],
       widget=W.long_run, blurb="A long run as driven and with the fuel effect taken out.",
       data=[("Tyre Lab", "Fuel-corrected degradation for every race.")], sources=SOURCES),

    ch("11.3", "Setup work", "Wings, ride heights, springs, bars, camber and brake balance: finding the compromise.",
       """
A car's **setup** is every adjustable setting: front and rear wing angles, ride heights, springs,
anti-roll bars, dampers, camber and toe, brake balance, differential settings and more. Engineers look
for the best compromise for the circuit, the conditions and the driver's style.

Setup choices pull against each other: more wing helps the corners but costs top speed; softer springs
help the tyres over bumps but let the floor move. The driver's feedback plus the data decide which
compromise is fastest. The Setup Garage lets you try some of these trade-offs on our lap simulator.
""",
       """
**Order of work.** Teams usually fix the big items first (wing level from simulation, ride heights for
the aero platform), then tune balance with springs, bars and front wing, and finally fine-tune with
camber, toe, brake balance and differential maps.

**Simulation first.** Before the weekend, the vehicle model and driver-in-the-loop simulator narrow the
setup down, so practice confirms and refines rather than starting from scratch.
""",
       """
**Correlation feedback.** When the car behaves differently from the simulation, engineers update the
models (tyre, aero map, suspension compliance) so the next prediction is better. That loop between track
and factory is one of a team's biggest competitive advantages.
""",
       [("A setup is…", ["the car's livery", "every adjustable setting on the car", "the engine only", "the team order"], 1,
         "Wings, springs, camber and more."),
        ("More wing usually means…", ["faster straights", "faster corners, slower straights", "nothing", "less grip"], 1,
         "The classic trade."),
        ("What's usually decided first?", ["Brake balance", "Wing level and ride heights", "Toe", "Diff maps"], 1,
         "The big items."),
        ("Why use simulation before the weekend?", ["To narrow down the setup", "Rules", "For fans", "It's free"], 0,
         "Practice refines."),
        ("Correlation feedback improves…", ["the models", "the paint", "the tyres", "the rules"], 0, "Track and factory agree.")],
       data=[("Setup Garage", "Change wing, power, weight and grip and see what each is worth.")], sources=SOURCES),

    ch("11.4", "Parc fermé", "Once qualifying starts, the setup is locked until the race.",
       """
From the start of qualifying, cars are in **parc fermé** conditions: teams may not change the setup
(no wing-angle changes except the front flap within limits, no suspension changes, no new parts)
until the race. Breaking parc fermé means starting from the pit lane.

So the setup must work for **both** qualifying (low fuel, fresh tyres, one lap) and the race (heavy fuel,
tyre management, often different weather). Engineers choose a compromise before qualifying that they'll
have to live with on Sunday.
""",
       """
**What's allowed.** Teams may still adjust the front wing flap, tyre pressures within limits, brake
cooling for weather, and fix genuine damage with like-for-like parts under FIA supervision.

**Weather gambles.** If rain is forecast for the race but not qualifying, a team might choose more wing or
softer settings than ideal for qualifying, a classic parc fermé gamble.
""",
       """
**Sprint weekends** put cars into parc fermé after just one practice session, which raises the stakes on
setup choices and makes simulation preparation even more valuable.
""",
       [("Parc fermé begins…", ["after the race", "at the start of qualifying", "on Friday", "never"], 1, "Setup is locked."),
        ("Breaking parc fermé means…", ["a fine only", "starting from the pit lane", "disqualification always", "nothing"], 1,
         "The usual penalty."),
        ("Which can still be adjusted?", ["Rear wing", "Front wing flap within limits", "Springs", "Gear ratios"], 1, "Small balance tweaks."),
        ("Why is setup a compromise between qualifying and the race?", ["The same setup must do both", "Rules on colours",
                                                                        "Fuel is the same", "It isn't"], 0, "Locked in."),
        ("Sprint weekends lock the car after…", ["three practices", "one practice", "the race", "qualifying only"], 1,
         "Higher stakes.")],
       sources=SOURCES),

    ch("11.5", "Qualifying preparation", "Tyre warm-up, track evolution and finding a gap in traffic.",
       """
Qualifying is three knockout sessions (Q1, Q2, Q3). Drivers need the tyres in their **temperature
window** for one perfect lap, a clear track, and the best grip, which keeps rising as rubber goes down
(*track evolution*), so going out late is usually faster.

That makes timing everything: leave the garage too early and the track is slower; too late and you
risk a red flag or traffic ending your session. Out-laps are planned carefully to bring the tyres up to
temperature without overheating them.
""",
       """
**Out-lap and preparation lap.** Drivers weave and brake hard to warm tyres, or do a slow lap then a
build-up lap, depending on the circuit and the tyre. The aim is the right surface and core temperature at
the start of the flying lap (Module 2.6).

**Tows.** On power circuits, running behind a team-mate for a slipstream can be worth a few tenths, but
getting the gap right is hard, and traffic jams on slow out-laps cause penalties for impeding.
""",
       """
**Energy in qualifying.** A qualifying lap can start with a full battery and empty it (Module 5.7), and the
engine runs its most aggressive mode, so power-unit settings are part of qualifying preparation too.
""",
       [("Why go out late in qualifying?", ["The track gets faster as rubber goes down", "Rules", "Less fuel", "Cooler air only"], 0,
         "Track evolution."),
        ("An out-lap's job is to…", ["set a fast time", "bring the tyres into their temperature window", "save fuel", "test brakes only"], 1,
         "Ready for the flying lap."),
        ("A tow in qualifying is…", ["a recovery truck", "a slipstream from a car ahead", "a penalty", "a tyre"], 1, "Worth tenths on power tracks."),
        ("Risk of going out too late?", ["A red flag or traffic ends the session", "More grip", "Less fuel", "None"], 0,
         "Timing gamble."),
        ("In qualifying the battery…", ["can't be used", "can start full and be emptied", "only harvests", "is removed"], 1,
         "One lap flat out.")],
       widget=W2.temperature_window, blurb="Tyre temperature against how hard the driver pushes (from Module 2).", sources=SOURCES),

    ch("11.6", "Driver and engineer", "The radio relationship: information, instructions and trust.",
       """
The race engineer is the driver's link to the team: they give gaps, tyre and fuel targets, warnings,
strategy calls and encouragement, in short messages timed for the straights so the driver isn't
distracted in corners. Good partnerships last years and rely on trust and a shared shorthand.

The driver feeds back too: balance, tyre feel, traffic, problems. That information shapes strategy calls
in real time.
""",
       """
**What drivers are told.** The rules restrict "driver coaching" at times, but engineers routinely give lap
deltas, targets for tyre and energy management, engine and brake balance settings, and pit calls.

**Codes.** Teams use code words for strategy ("Plan B", "box opposite") to avoid helping rivals, who
can hear the published radio. The Team Radio page shows real published messages, sorted by topic.
""",
       """
**Information overload.** Engineers filter dozens of data streams into a few words. Research on driver
workload shows short, consistent messages at predictable moments work best: which is why many radio
messages follow fixed formats.
""",
       [("When do engineers usually talk to drivers?", ["Mid-corner", "On the straights", "Never", "Under braking"], 1,
         "Less distraction."),
        ("Why use code words on the radio?", ["Rivals can hear published radio", "Rules", "Fun", "Translation"], 0,
         "Strategy secrecy."),
        ("Driver feedback shapes…", ["the livery", "real-time strategy and setup decisions", "the calendar", "nothing"], 1,
         "Balance, tyres, traffic."),
        ("Good radio messages are…", ["long and detailed", "short, consistent and well timed", "rare", "shouted"], 1,
         "Workload."),
        ("Which page shows real published radio?", ["Team Radio", "Tyre Lab", "Quiz", "Engine Room"], 0, "Transcribed and sorted.")],
       data=[("Team Radio", "Real published radio messages, transcribed and sorted by topic.")], sources=SOURCES),
]
