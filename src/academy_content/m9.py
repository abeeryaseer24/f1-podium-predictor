"""Module 9: Cooling and thermal management."""
import academy_widgets_m8 as W
from academy_content.m4 import ch

SOURCES = ["FIA Formula 1 Technical Regulations, power unit and fuel-flow articles, fia.com",
           "Incropera, F. P. et al. (2011). Fundamentals of Heat and Mass Transfer, 7th ed. Wiley.",
           "Heisler, H. (2002). Advanced Vehicle Technology, 2nd ed. Butterworth-Heinemann (cooling systems)."]

CHAPTERS = [
    ch("9.1", "The heat budget", "Half the fuel's energy becomes heat the car has to get rid of.",
       """
An F1 engine is one of the most efficient ever built, turning about half of its fuel's energy into work.
The other half becomes **heat**. Some leaves with the exhaust; the rest goes into the engine's water and
oil, the turbo's compressed air, the battery and its electronics, and the gearbox. All of that has to be
carried away by air flowing through radiators.

At full throttle the fuel flowing in carries over a megawatt of power, so even "the other half" is
hundreds of kilowatts of heat, about as much as a hundred home heaters.
""",
       """
**The numbers.** From 2014 to 2025 fuel flow was capped at 100 kg/h. At about 43 MJ/kg that's

$$P_{fuel} = \\frac{100 \\times 43\\times10^6}{3600} \\approx 1.2\\ \\text{MW}.$$

At 50% efficiency about 600 kW reaches the crankshaft (with energy recovery helping), and about 600 kW is
heat. In 2026 the limit becomes an energy-flow cap of 3,000 MJ/h, about 830 kW of fuel power, with much
more of the car's power coming from the battery, which needs its own cooling at lower temperatures.

**Different circuits, different temperatures.** Water and oil run hot (well over 100 °C, under pressure),
but the battery and power electronics want to stay much cooler, so they need separate circuits.
""",
       """
**Where the heat goes.** A rough split for a hybrid power unit: about half the waste heat leaves in the
exhaust (partly recovered by the turbo and, until 2025, the MGU-H), and the rest is shared between the water
radiators, oil coolers and the charge-air cooler (intercooler), with smaller loads from the ERS. Because
radiator size, and so drag, scales with heat to reject, every efficiency gain pays twice: more power and
less cooling drag.
""",
       [("An F1 engine turns about how much of its fuel energy into work?", ["10%", "half", "90%", "all of it"], 1, "Very efficient for an engine."),
        ("Fuel flow from 2014 to 2025 was capped at…", ["10 kg/h", "100 kg/h", "1,000 kg/h", "no cap"], 1, "About 1.2 MW of fuel power."),
        ("The 2026 limit is…", ["an energy-flow cap of 3,000 MJ/h", "no limit", "200 kg/h", "a rev limit only"], 0, "About 830 kW of fuel power."),
        ("Why does the battery need its own cooling circuit?", ["It must stay much cooler than the engine", "Rules", "Weight", "It doesn't"], 0,
         "Batteries hate heat."),
        ("Why does efficiency pay twice?", ["More power and smaller radiators (less drag)", "Lower fuel price", "Better sound", "It doesn't"], 0,
         "Less heat to reject.")],
       widget=W.heat_budget, blurb="Fuel energy in, work out, and the radiator the rest needs.",
       data=[("Engine Room", "Energy-flow Sankeys for each power-unit era.")], terms=["power unit"], sources=SOURCES),

    ch("9.2", "Radiators, louvres and sidepod design", "Every kilowatt of cooling costs drag.",
       """
The radiators sit inside the **sidepods**, fed by inlets beside the cockpit. Air flows through the
radiator cores, picks up heat, and leaves through outlets: openings at the back of the bodywork and
**louvres**, slatted vents on the top of the sidepods and engine cover.

Cooling is a compromise. Bigger inlets and outlets cool better but cost drag and can upset the airflow to
the rear of the car. Teams bring different bodywork to each race, with more or fewer louvres open,
depending on how hot it will be.
""",
       """
**Heat transfer.** A radiator rejects heat $Q = U A \\Delta T$: an overall heat-transfer coefficient $U$,
the core area $A$, and the temperature difference between coolant and air. Running the coolant hotter
(pressurised systems let water run well above 100 °C) raises $\\Delta T$, so the radiator can be smaller.

**Cooling drag.** The air slowed down inside the radiator has lost momentum, and that loss is drag. A
well-designed duct slows the air before the core (less loss) and accelerates it back out, and the hot
exhaust air can even add a little thrust.
""",
       """
**Packaging.** Sidepod shape is as much aerodynamics as cooling: since 2022 teams have tried very different
answers (deep undercuts, "zero pod" concepts, downwash ramps) to the same packaging problem, because the
sidepod shapes the airflow to the floor's edges and the beam wing. Radiator angle, core thickness and where
the hot air leaves are all chosen with the floor in mind.
""",
       [("Where are the radiators?", ["In the sidepods", "In the nose", "Under the seat", "In the wheels"], 0, "Fed by sidepod inlets."),
        ("Louvres are…", ["slatted vents letting hot air out", "brake parts", "wing flaps", "seat belts"], 0, "On the bodywork."),
        ("In Q = U·A·ΔT, running the coolant hotter…", ["raises ΔT so the radiator can shrink", "lowers ΔT", "changes nothing", "raises drag"], 0,
         "Pressurised systems help."),
        ("Why do teams bring different bodywork to hot races?", ["More cooling openings", "Looks", "Sponsors", "Rules"], 0, "Cooling vs drag."),
        ("Cooling drag comes from…", ["momentum lost by air through the radiator", "the tyres", "the driver", "nothing"], 0, "Slowed air is drag.")],
       widget=W.cooling_drag, blurb="What extra cooling openings cost a lap, from the lap simulator.",
       terms=["drag"], sources=SOURCES),

    ch("9.3", "Hot races and cooling compromises", "Singapore, Qatar, Bahrain: when heat sets the pace.",
       """
On hot days the radiators have less temperature difference to work with, so engines run closer to their
limits. Teams open up the bodywork (losing some speed) or ask the driver to manage temperatures: lifting
and coasting into corners, or dropping back out of another car's wake, because following closely means
breathing hot, slow air.

Some races are famous for it. Singapore is slow, humid and long. Qatar 2023 was so hot and humid that
several drivers were ill. Bahrain and Hungary can be brutal in the heat of the day.
""",
       """
**Traffic.** A car following closely gets less air, and hotter air, into its radiators. That's why the
radio often says "temperatures are high, drop back": the engineer is trading track position for
reliability.

**Choices before the race.** Cooling configuration is fixed by parc fermé after qualifying, so it has to
be chosen before anyone knows how the race will go. Too little cooling and the driver may have to back
off; too much and the car is slow on the straights all race.
""",
       """
**Brakes and tyres too.** The same trade-offs apply to brake ducts (Module 7.4) and to tyre temperatures
(Module 2.6). In the data, hot races show more lift-and-coast and more cars managing gaps, which also
changes how strategies play out.
""",
       [("On a hot day radiators work less well because…", ["the temperature difference to the air is smaller", "the air is thinner", "rules", "they don't"], 0,
         "ΔT shrinks."),
        ("Why do engineers tell drivers to drop back?", ["Following means hotter, slower air into the radiators", "To save fuel only", "Rules", "To let them pass"], 0,
         "Reliability vs position."),
        ("Cooling configuration is fixed after qualifying by…", ["parc fermé", "the driver", "the weather", "the stewards' choice"], 0,
         "So it's chosen in advance."),
        ("Which race in 2023 made several drivers ill from heat?", ["Qatar", "Monaco", "Silverstone", "Spa"], 0, "Hot and humid."),
        ("Lift and coast helps cooling by…", ["using less power, so less heat", "adding downforce", "cooling the driver", "nothing"], 0,
         "Less fuel burnt.")],
       data=[("Team Radio", "Search for temperature calls in the race radio.")], sources=SOURCES),

    ch("9.4", "Cooling the driver", "The cockpit can top 50 °C, and the driver is the hottest part.",
       """
The cockpit sits between the engine and the hot air off the radiators, and the driver wears fireproof
layers from head to toe. In a hot race the cockpit can go above 50 °C and a driver can lose a few
kilograms of sweat, and with it, concentration and reaction time.

Drivers train for it (heat training in saunas and hot rooms), drink from an in-car bottle, and teams
duct cool air to the cockpit. From 2025 the FIA can declare a **heat hazard** for a hot race, and cars
then carry a cooling system for the driver, with an allowance in the minimum mass for it.
""",
       """
**The physiology.** Core body temperature above about 39 °C starts to affect decision-making and fine
control; dehydration of a few per cent of body mass does the same. That's why heat is a safety issue,
not just comfort.

**Cooling systems.** Driver cooling uses cool liquid pumped through tubes in a vest under the race suit,
a direct way to take heat out of the body.
""",
       """
**Engineering the human.** Teams treat the driver as part of the car: sweat rate tests, fluid strategies
and acclimatisation plans for each race. Heat stress is one of the reasons the FIA now publishes heat
rules, and one of the clearest examples of the driver's limits shaping engineering decisions.
""",
       [("A hot cockpit can top…", ["25 °C", "over 50 °C", "100 °C", "0 °C"], 1, "Between engine and radiators."),
        ("A driver can lose in sweat during a hot race…", ["a few grams", "a few kilograms", "nothing", "20 kg"], 1, "Affecting concentration."),
        ("From 2025 the FIA can declare…", ["a heat hazard, requiring driver cooling", "no racing", "free tyres", "night racing"], 0,
         "With a mass allowance."),
        ("Why is heat a safety issue?", ["It harms decision-making and control", "It doesn't", "Rules", "Paint"], 0, "Core temperature."),
        ("Driver cooling vests work by…", ["pumping cool liquid through tubes", "fans only", "ice in the helmet", "magic"], 0, "Direct cooling.")],
       sources=SOURCES),
]
