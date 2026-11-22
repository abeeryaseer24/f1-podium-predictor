"""Module 12: Strategy."""
import academy_widgets_m11 as W
from academy_content.m4 import ch

SOURCES = ["Heilmeier, A., Graf, M. & Lienkamp, M. (2018). A race simulation for strategy decisions in circuit motorsports. "
           "IEEE ITSC.",
           "Bekker, J. & Lotz, W. (2009). Planning Formula One race strategies using discrete-event simulation. JORS 60(7).",
           "FIA Formula 1 Sporting Regulations, tyre and pit-lane articles, fia.com"]

CHAPTERS = [
    ch("12.1", "The race as an optimisation", "Finding the fastest way to cover the race distance, against rivals who are doing the same.",
       """
Strategy asks one question: what's the fastest way to complete the race? Pit stops cost time
(20–25 seconds at most circuits), but old tyres cost time too, lap after lap. The best plan balances
the two: how many stops, when, and on which tyres.

Then add rivals, safety cars, weather and traffic, and the "fastest" plan becomes the plan that gives
the best **finishing position**, which isn't always the same thing.
""",
       """
**The objective.** For a single car alone on track, minimise total race time:

$$T = \\sum_{laps} t_{lap}(\\text{fuel}, \\text{tyre}, \\text{age}) + n_{stops}\\,t_{pit}$$

subject to the rules (at least two dry compounds in a dry race). With rivals the objective becomes finishing
position, which depends on track position and traffic, so teams simulate the whole race (12.6).
""",
       """
**Discrete choices, continuous effects.** The number of stops and the compounds are discrete; stop laps are
nearly continuous. Strategy tools search this space with fast race simulators, then re-run the search every
lap as the race unfolds.
""",
       [("A pit stop typically costs…", ["2 s", "20–25 s", "60 s", "5 minutes"], 1, "Pit lane time included."),
        ("Why not stop every lap?", ["Pit stops cost time", "Rules", "Tyres are free", "No reason"], 0, "Balance stops against wear."),
        ("In a dry race drivers must use…", ["one compound", "at least two dry compounds", "only softs", "wets"], 1, "Forces a stop."),
        ("With rivals the real objective is…", ["shortest lap", "best finishing position", "least fuel", "most stops"], 1,
         "Track position matters."),
        ("Strategy plans are re-run…", ["once a season", "every lap as the race unfolds", "never", "only in the wet"], 1, "Live updates.")],
       widget=W.stop_calculator, blurb="One stop or two? Time lost to tyres and stops for every plan.", sources=SOURCES),

    ch("12.2", "Degradation, fuel and pit loss", "The three numbers every strategy is built on.",
       """
Three numbers drive most strategy calls:

- **Degradation:** how much slower each compound gets per lap of age (and when it falls off the cliff).
- **Fuel effect:** how much faster the car gets as fuel burns off.
- **Pit loss:** how much time a stop costs, mostly the slow drive through the pit lane.

High degradation and a short pit lane favour more stops; low degradation and a long pit lane favour fewer.
The Tyre Lab measures the first two for every race, and the pit loss too.
""",
       """
**Pit loss** is the extra time the in-lap and out-lap take compared with two normal laps. It depends on
pit-lane length and speed limit, the stationary time (around 2–3 s), and the cold-tyre out-lap. It's lower
under safety cars (12.4).

**Interaction.** Fuel effect makes later stints faster; degradation makes them slower; both shape where the
best stop lap falls. The demo shows how a harder-wearing track shifts the balance towards two stops.
""",
       """
**Uncertainty.** Each number is estimated from practice and earlier races and carries error. Strategy tools
run many simulations with these numbers varied, which is part of why Monte Carlo methods (12.6) are used.
""",
       [("High degradation tends to favour…", ["fewer stops", "more stops", "no stops", "rain tyres"], 1, "Old tyres cost more."),
        ("Pit loss is mainly…", ["the stationary time", "the drive through the pit lane", "the tyre cost", "fuel"], 1,
         "Speed limit and length."),
        ("The fuel effect makes later laps…", ["slower", "faster", "the same", "wet"], 1, "The car gets lighter."),
        ("Where can you see measured degradation?", ["Tyre Lab", "Quiz", "Engine Room", "About"], 0, "For every race."),
        ("Why use many simulations?", ["The numbers are uncertain", "Rules", "It's free", "For fun"], 0, "Monte Carlo.")],
       data=[("Tyre Lab", "Degradation, fuel effect and pit loss for every race.")], sources=SOURCES),

    ch("12.3", "Undercut and overcut", "Stopping first to jump a rival, or staying out to do the same.",
       """
Two cars are close on track. The one behind stops first: on fresh tyres it laps much faster than the
rival still on old tyres. When the rival stops a lap later, it may come out **behind**. That's the
**undercut**.

The **overcut** is the opposite: stay out longer, use the clear track, and come out ahead after your stop.
It works when tyres degrade slowly, fresh tyres take a long time to warm up, or the rival comes out into
traffic.
""",
       """
**When the undercut works.** The gain is roughly the fresh-tyre advantage on the laps the rival stays out,
minus your out-lap warm-up penalty, plus the rival's own cold out-lap. If that's bigger than the gap, the
undercut works. The demo lets you vary each part.

**Defending.** The car ahead often "covers" by stopping on the next lap, or the lap the rival stops,
which is why teams watch each other's pit crews come out.
""",
       """
**Traffic and pit windows.** The undercut also needs clear air on the out-lap. Strategists track a **pit
window**: the laps where a car can stop and rejoin ahead of slower cars, which changes as gaps open and close.
""",
       [("The undercut means…", ["stopping later than a rival", "stopping first to jump a rival", "a type of corner", "a penalty"], 1,
         "Fresh tyres first."),
        ("The overcut works best when…", ["tyres degrade quickly", "tyres degrade slowly and warm up slowly", "it rains", "never"], 1,
         "Stay out and push."),
        ("A rival 'covers' an undercut by…", ["stopping the next lap or the same lap", "slowing down", "changing team", "nothing"], 0,
         "Reacting to the stop."),
        ("Out-lap warm-up mainly hurts…", ["the undercut", "the overcut", "nobody", "the safety car"], 0, "Cold fresh tyres."),
        ("A pit window is…", ["a pit-lane window", "laps where a car can stop and rejoin in clear air", "a rule", "a weather gap"], 1,
         "Changes as gaps change.")],
       widget=W.undercut, blurb="Does the undercut work? Gap, fresh-tyre advantage and warm-up.", sources=SOURCES),

    ch("12.4", "Safety cars", "Cheap pit stops, bunched fields and races turned upside down.",
       """
When a **safety car** comes out, the field slows down and bunches up behind it. Two big things change:

- **Pit stops become cheaper:** everyone is slow, so a stop costs roughly half its usual time. Teams often
  stop immediately, so watch the pit lane fill.
- **Gaps disappear:** a leader's 15-second margin is gone in a lap, and the race restarts close together.

A **virtual safety car** (VSC) slows everyone to a set delta without bunching, so stops are cheaper but gaps
stay. Safety-car timing can make or break a strategy, and luck plays a big part.
""",
       """
**Our models.** The strategist and the race engine use stops costing 55 % of normal under a safety car and
70 % under a VSC. The race engine's safety-car chance comes from how often they've happened at each circuit
in our data.

**Stay out or stop?** If everyone stops, staying out gains track position but leaves you on older tyres for
the restart. The right call depends on how many laps remain, the tyre gap and how hard overtaking is.
""",
       """
**Red flags** stop the race completely. Teams may change tyres for free during the stoppage, which can wipe
out the advantage of a car that stopped just before (Monaco 2024 began with exactly that).
""",
       [("Under a safety car a pit stop costs…", ["the same", "about half as much", "double", "nothing"], 1, "About 55 % in our models."),
        ("What happens to gaps under a safety car?", ["They grow", "They disappear as the field bunches", "Nothing", "They're frozen"], 1,
         "Restart close together."),
        ("A VSC differs because…", ["the field doesn't bunch", "cars stop", "it's faster", "it's longer"], 0, "Gaps stay."),
        ("During a red flag teams may…", ["change tyres for free", "refuel only", "nothing", "change engines"], 0, "A free stop."),
        ("Staying out under a safety car gains…", ["fresh tyres", "track position", "fuel", "points directly"], 1,
         "At the cost of older tyres.")],
       widget=W.sc_saving, blurb="What a stop costs under a safety car and a VSC.",
       data=[("Race Simulator", "Force a safety car on any lap and see the result change."),
             ("Win Probability", "Safety-car laps marked on the race's odds.")], sources=SOURCES),

    ch("12.5", "Game theory", "Strategy is a game against nine other teams who are thinking about you.",
       """
A strategy isn't chosen in isolation: rivals react. If you stop, the car behind might stop next lap to
cover; if you stay out, they might too. Each team tries to guess the others' moves, like in chess or poker.

That's **game theory**: the best choice depends on what you expect others to do. Teams sometimes split
strategies across their two cars to cover both options, or bluff by sending the pit crew out without
stopping.
""",
       """
**Leader's dilemma.** The leader usually copies whatever the second car does (covering), since that keeps
the lead. The chasing car must take a different strategy to have a chance, accepting some risk.

**Nash equilibrium.** A pair of strategies where neither team can gain by changing alone. In practice
uncertainty is so large that teams think in probabilities: which choice gives the best expected result
across what the rival might do.
""",
       """
**Our engine's limit.** The Race Simulator keeps every other driver on their real strategy, so it doesn't
model rivals reacting to your change. Real strategy tools add reaction rules or search over rivals' options,
and that's where much of the remaining strategic skill lies.
""",
       [("Game theory in strategy means…", ["playing video games", "choosing while considering how rivals react", "random choices",
                                            "copying others"], 1, "Rivals react."),
        ("Why does the leader often copy the second car?", ["To cover and keep the lead", "Rules", "Fuel", "Tyres only"], 0,
         "Covering."),
        ("Why might a team split its two cars' strategies?", ["To cover both options", "Rules", "Cost", "Mistake"], 0, "Hedging."),
        ("A Nash equilibrium is…", ["a corner", "strategies where neither side gains by changing alone", "a tyre", "a penalty"], 1,
         "Stable choices."),
        ("What does our Race Simulator not model?", ["Tyres", "Rivals reacting to your change", "Fuel", "Safety cars"], 1,
         "Others keep their real plans.")],
       sources=SOURCES),

    ch("12.6", "Monte Carlo strategy", "Simulate the race thousands of times and pick the plan with the best odds.",
       """
A race has a lot of randomness: lap-time variation, safety cars, retirements, overtaking chances. So
instead of simulating it once, strategy tools simulate it **thousands of times** with different random
events, then compare plans by their odds: chance of winning, of a podium, average finish.

That's the **Monte Carlo** method, named after the casino. It's how our Race Simulator, Win Probability and
Championship Odds pages work, and how many teams' strategy tools work too.
""",
       """
**Convergence.** With few runs, the odds jump around from one batch to the next; with hundreds they settle.
The error of an estimated probability $p$ from $N$ runs is about $\\sqrt{p(1-p)/N}$: 400 runs give about
±2–3 percentage points. The demo shows it on a real race.

**Variance reduction.** Using the same random numbers for every plan being compared ("common random numbers")
makes differences between plans clearer, a trick our simulator uses through fixed seeds.
""",
       """
**From odds to decisions.** The best plan might maximise expected points, chance of winning, or minimise the
risk of a bad result, depending on the championship situation. A title leader may prefer a safe plan; a car
that needs a win takes the gamble.
""",
       [("Monte Carlo strategy means…", ["simulating the race many times with random events", "racing in Monaco", "guessing", "copying rivals"], 0,
         "Odds from many runs."),
        ("More runs make the odds…", ["noisier", "more stable", "always 50 %", "irrelevant"], 1, "They converge."),
        ("Error of a probability from N runs is about…", ["p × N", "√(p(1−p)/N)", "N/p", "1/p"], 1, "Shrinks with √N."),
        ("Which app pages use Monte Carlo?", ["Race Simulator, Win Probability and Championship Odds", "Quiz only", "About", "None"], 0,
         "All replay many times."),
        ("Why might a title leader choose a lower-risk plan?", ["Protecting the championship matters more than a win", "Rules", "Fuel", "Tyres"], 0,
         "Objectives differ.")],
       widget=W.monte_carlo, blurb="The same race simulated three times: watch the odds settle as the runs grow.",
       data=[("Race Simulator", "Change a strategy and compare odds over 400 races.")], sources=SOURCES),

    ch("12.7", "Reinforcement learning", "Teaching a computer to make strategy calls by letting it race millions of times.",
       """
**Reinforcement learning** (RL) trains a computer agent by trial and error: it makes decisions (box or stay
out, which tyre), sees what happens in a simulated race, and gradually learns which decisions lead to better
results. Given a good enough race simulator, an RL agent can play millions of races, far more than any human
strategist ever sees.

Research groups and some teams have explored RL for pit-stop decisions. This project's **AI Strategist** page
does it too: an agent learns every race's strategy from simulated races built from that race's data, then
takes on the real winner's stops.
""",
       """
**How it works.** At each lap the agent sees a *state* (tyre age, gaps, laps left, safety car or not) and
chooses an *action* (stay out, or stop for a compound). At the end it receives a *reward* (finishing position
or points). Algorithms like PPO or Monte Carlo tree search improve the agent's *policy*, the map from states
to actions.

**The catch.** The agent is only as good as the simulator. If the simulator gets overtaking or degradation
wrong, the agent learns to exploit those errors, which is why simulator validation matters so much.
""",
       """
**Interpretability.** An RL policy can be visualised as a map: for each tyre age and gap, box or stay. That
helps engineers trust (or challenge) its recommendations, and spot where it's exploiting a modelling flaw.
""",
       [("Reinforcement learning trains an agent by…", ["reading books", "trial and error with rewards", "copying humans only", "random rules"], 1,
         "Learning from outcomes."),
        ("An RL agent's 'state' might include…", ["tyre age, gaps and laps left", "the team logo", "the weather forecast only", "nothing"], 0,
         "What it sees each lap."),
        ("The biggest risk with RL strategy is…", ["it's too slow", "it exploits errors in the simulator", "it's illegal", "it's expensive"], 1,
         "Only as good as the simulator."),
        ("A policy is…", ["a rule book from the FIA", "the map from states to actions", "a tyre", "insurance"], 1, "What the agent learns."),
        ("Where can you see an RL strategist in this app?", ["Nowhere", "The AI Strategist page", "Only in quizzes", "The About page"], 1,
         "Trained on every race.")],
       data=[("AI Strategist", "A policy-search agent trained on every race, against the real teams.")],
       sources=SOURCES + ["Schulman, J. et al. (2017). Proximal Policy Optimization Algorithms. arXiv:1707.06347.",
                          "Rubinstein, R. & Kroese, D. (2004). The Cross-Entropy Method. Springer."]),

    ch("12.8", "Wet races and crossovers", "When to switch from intermediates to slicks, or back.",
       """
In a race that changes from wet to dry (or back), the biggest strategy call is **when to switch tyres**. On a
drying track, intermediates overheat and slow down while slicks get faster; at some lap, slicks become
quicker. That's the **crossover**. Stop too early and you crawl round on cold slicks on a damp track; stop
too late and you lose time on worn-out intermediates.

Drivers' feedback is crucial: they feel the track drying before the lap times show it. Teams also watch the
first car to gamble on slicks: if its sectors go green, everyone follows.
""",
       """
**Measuring the crossover.** Comparing the lap times of cars on intermediates with cars on slicks, lap by
lap, shows where the lines cross. In practice the field switches within a lap or two, so there are few laps
with both running on clean laps. The Rain Crossover page measures it where it can and estimates it where
it can't.

**Rain arriving** is the reverse problem: when does a light shower make intermediates faster than slicks?
Radar and the weather station guide the call.
""",
       """
**Asymmetric risk.** Going to slicks a lap early can cost a lot (spins, big time loss on a damp track), while
a lap late costs a few seconds. So teams often wait for proof, unless they're behind and need to gamble.
""",
       [("The crossover is…", ["a corner", "the lap where slicks become faster than intermediates (or the reverse)", "a penalty",
                               "a tyre brand"], 1, "The key wet-race call."),
        ("Switching to slicks too early risks…", ["more grip", "cold slicks on a damp track", "a free stop", "nothing"], 1,
         "Big time loss or a spin."),
        ("Why watch the first car on slicks?", ["Its sector times show if slicks work", "Rules", "Luck", "Sponsors"], 0,
         "Green sectors mean go."),
        ("Why are crossovers hard to measure?", ["The field switches within a lap or two", "No data exists", "Rules", "Rain"], 0,
         "Few overlapping laps."),
        ("Why do teams often wait for proof?", ["Early is riskier than late", "Rules", "Fuel", "Tyres are free"], 0,
         "Asymmetric risk.")],
       data=[("Rain Crossover", "Crossovers and every driver's tyre switch in mixed-weather races.")], sources=SOURCES),
]
