"""Module 16: Capstone, design your car."""
import academy_widgets_m8 as W
from academy_content.m4 import ch

SOURCES = ["Milliken, W. F. and Milliken, D. L. (1995). Race Car Vehicle Dynamics. SAE International.",
           "Katz, J. (2006). Race Car Aerodynamics. Bentley Publishers.",
           "This app's lap simulator (src/lapsim.py) and its calibration against real pole laps."]

CHAPTERS = [
    ch("16.1", "Design, simulate, race, debrief", "Everything in the course, in one car of your own.",
       """
This is where it comes together. You have a fixed budget of **design points**. Spend them on downforce, low
drag, weight saving and power, and the lap simulator from Module 3.9 drives your car round a real circuit,
calibrated against that circuit's real pole lap. Then your car races a typical field 2,000 times, and you
see where it finishes.

There's no single right answer. A car built for Monza is slow at Monaco, and the other way round (Module 1.4).
The job is the engineer's job: understand the circuit, decide what matters most there, and spend where it
pays.
""",
       """
**A design process.**

1. **Read the circuit.** Is it long straights or slow corners? Module 13's tours and the sensitivity map in
   Module 1.3 tell you what the lap simulator thinks matters most.
2. **Spend.** Points buy small changes: about 0.4% of downforce or drag, 0.6 kg or 1.6 kW each.
3. **Simulate.** Compare your speed trace with the calibrated car's: where do you gain, where do you lose?
4. **Race.** Lap time becomes a win chance through the same noisy race model the predictor and Team Principal
   use: being quicker raises your odds, it doesn't guarantee a win.
5. **Debrief.** Change one thing at a time and watch the result, like an engineer running a setup sweep.
""",
       """
**What the capstone leaves out.** Real design trades are coupled: more downforce usually means more drag;
cooling (Module 9) needs openings that cost drag; a lighter car needs cleverer materials (Module 8); more
power needs more fuel and more heat rejection. The rules then cap most of it. Treat the points as a simple
stand-in for those costs, and go further with the Setup Garage, the Energy Lab, the Wind Tunnel and Team
Principal, which each model one part of the problem in more depth.
""",
       [("A low-drag car suits…", ["Monza", "Monaco", "every circuit", "no circuit"], 0, "Long straights."),
        ("Why test one change at a time?", ["To see which change caused the result", "Rules", "It's faster", "No reason"], 0, "A setup sweep."),
        ("Being quicker over a lap…", ["raises your win chance but doesn't guarantee a win", "guarantees a win", "doesn't matter", "loses races"], 0,
         "Races are noisy."),
        ("In real design, more downforce usually also means…", ["more drag", "less drag", "less mass", "more power"], 0, "Coupled trades."),
        ("Where do you find what matters most at a circuit?", ["Module 1.3's sensitivity map and Module 13's tours", "The glossary", "Nowhere",
                                                               "The quiz"], 0, "The lap simulator's view.")],
       widget=W.capstone, blurb="Spend 100 design points, then race the car you built.",
       data=[("Setup Garage", "Every setup change, corner by corner."), ("Team Principal", "Develop a car through a whole season."),
             ("Circuit Designer", "Design the circuit too.")],
       terms=["lap simulator", "sensitivity", "wing level"], sources=SOURCES),
]
