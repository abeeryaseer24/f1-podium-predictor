"""Module 14: Rules, money and the business."""
import academy_widgets_m8 as W
from academy_content.m4 import ch

SOURCES = ["FIA Formula 1 Technical, Sporting and Financial Regulations, fia.com",
           "FIA, decisions on the 2021 Financial Regulations compliance (October 2022), fia.com",
           "FIA International Sporting Code and Judicial and Disciplinary Rules, fia.com"]

CHAPTERS = [
    ch("14.1", "Technical vs sporting regulations", "The two rulebooks: what the car may be, and how the race is run.",
       """
Formula 1 has several rulebooks, written by the **FIA** (the sport's governing body). The **technical
regulations** define the car: dimensions, weights, materials, the power unit, safety structures. The
**sporting regulations** define the competition: the weekend's sessions, qualifying, parc fermé, tyres,
penalties, points. Since 2021 there are also **financial regulations**: the cost cap (14.2).

Formula 1's commercial side (TV rights, races, prize money) is run by Formula One Management. The teams,
the FIA and F1 agree how it all works together in the **Concorde Agreement**.
""",
       """
**How rules change.** Changes go through the F1 Commission (F1, the FIA and the teams) and the FIA's World
Motor Sport Council. Big technical changes are agreed years ahead (the 2026 rules were published in 2024)
so teams can design to them; safety changes can come in at once.

**Technical directives.** Between rule changes, the FIA issues technical directives: its reading of how a
rule applies. A directive can close a loophole mid-season, as with the 2022 porpoising directive.
""",
       """
**Writing rules is design.** The technical rules are a box the designers work inside (Module 1.2), and the
rule-makers try to predict how teams will exploit every sentence. Wording matters: "bodywork", "any
specific part" and "rigidly secured" have all decided championships. Many rule changes are attempts to fix
the unintended consequences of earlier ones.
""",
       [("The technical regulations define…", ["the car", "the race weekend", "TV rights", "ticket prices"], 0, "Dimensions, weights, PU, safety."),
        ("The sporting regulations define…", ["the competition: sessions, penalties, points", "the car's mass", "the halo", "fuel"], 0,
         "How the race is run."),
        ("Who writes the rules?", ["The FIA", "One team", "The drivers", "TV"], 0, "With the F1 Commission."),
        ("A technical directive is…", ["the FIA's reading of how a rule applies", "a new car", "a penalty", "a race"], 0,
         "It can close loopholes."),
        ("The Concorde Agreement covers…", ["how teams, the FIA and F1 work together commercially", "tyre compounds", "the halo", "nothing"], 0,
         "Including prize money.")],
       terms=["regulations"], sources=SOURCES),

    ch("14.2", "The cost cap and what it limits", "A spending limit that changed how teams develop.",
       """
Since 2021 teams may spend only so much a year on designing, building and running their cars: the **cost
cap**. It started at $145 million, fell to $135 million by 2023 (with adjustments for inflation and extra
races), and was reset higher for 2026 as more items were brought inside it.

Not everything counts. Drivers' salaries, the three best-paid staff, marketing and some other costs sit
outside the cap. What's inside is audited by the FIA every year.
""",
       """
**Effects.** Big teams had to cut or move staff and choose which upgrades are worth their cost; development
became a budget allocation problem. Spending on next year's car competes with this year's.

**Breaches.** Red Bull exceeded the 2021 cap by a small margin and was fined $7 million and given a 10%
cut in its aerodynamic testing allowance (14.4). Aston Martin received a smaller fine for a procedural
breach the same year.
""",
       """
**Game theory of a cap.** With money fixed, a team's best returns come from efficiency: getting more lap
time per dollar. That favours good processes and correlation (Module 10.6) over sheer size, and it's one
reason the field has tightened since 2021. Team Principal in the Games menu turns this into a game: a fixed
development budget and a wind-tunnel allowance set by your championship place.
""",
       [("The cost cap started in…", ["2010", "2021", "2026", "1994"], 1, "At $145 million."),
        ("Which of these is outside the cap?", ["Drivers' salaries", "Building the car", "Wind-tunnel parts", "Race-team travel for the car"], 0,
         "So are the top three salaries and marketing."),
        ("Red Bull's 2021 breach cost them…", ["$7 million and 10% less aero testing", "their title", "nothing", "a race ban"], 0, "A minor overspend."),
        ("Under a cap, the best returns come from…", ["efficiency: lap time per dollar", "spending more", "more staff", "luck"], 0,
         "Money is fixed."),
        ("Who audits the cap?", ["The FIA", "The teams themselves only", "TV companies", "Nobody"], 0, "Every year.")],
       data=[("Team Principal", "Run a season inside a development budget.")], sources=SOURCES),

    ch("14.3", "How teams are organised", "From aerodynamicists to the pit crew: around a thousand people.",
       """
A top F1 team has close to a thousand staff, most of them at the factory. The **technical director** leads
the design of the car; the **team principal** runs the whole operation. Under them sit departments:
**aerodynamics** (the largest), **design** (turning ideas into parts), **vehicle performance** (simulation,
setup, data), the **power unit** (if the team builds its own), **manufacturing**, and the **race team**.

At the track, each car has a race engineer, a performance engineer and a group of mechanics, backed by
strategists and specialists, with the factory watching live (Module 10.2).
""",
       """
**The design loop.** Aerodynamicists find gains in CFD and the tunnel; designers package them into parts
that are light and strong enough; manufacturing makes them; the race team fits and runs them; data comes
back; repeat. How fast a team goes round that loop, and how well each step correlates, decides how fast
the car improves through a season.

**Customer teams.** Some teams buy their power unit and gearbox from another team, and share some
non-listed parts within the rules, which lets a smaller team spend its resources elsewhere.
""",
       """
**Organisation is performance.** Many of F1's great turnarounds (Red Bull from 2009, Mercedes from 2014)
came from people and structure as much as from one clever idea: hiring, clear technical leadership and
fast decision-making. The cost cap has made organisational efficiency even more important.
""",
       [("The largest technical department is usually…", ["aerodynamics", "catering", "marketing", "legal"], 0, "Downforce is lap time."),
        ("Who leads the design of the car?", ["The technical director", "The driver", "The FIA", "The sponsor"], 0, "Under the team principal."),
        ("A race engineer is…", ["the driver's main contact at the track", "a mechanic", "a steward", "a TV presenter"], 0, "Radio voice."),
        ("Customer teams buy…", ["power units and gearboxes from another team", "drivers", "circuits", "nothing"], 0, "Within the rules."),
        ("Great turnarounds came largely from…", ["people and structure", "luck only", "paint", "rule breaks"], 0, "Organisation is performance.")],
       sources=SOURCES),

    ch("14.4", "Testing limits and the ATR", "Little track testing, and wind-tunnel time handed out by championship place.",
       """
Teams once tested almost every week. Today track testing is tightly limited: a few days of pre-season
testing, plus restricted running of older cars and tyre tests for the supplier. Most development happens
in the factory.

There it's limited too. The **aerodynamic testing restriction (ATR)** caps how much wind-tunnel time and
CFD each team may use, and it slides with the championship: the champions get the least, the last-placed
team the most. It's a handicap system meant to let the field close up.
""",
       """
**The sliding scale.** Since 2022 the allowance runs from 70% of a baseline for the championship leader up
to 115% for tenth place, in 5% steps, recalculated from the standings during the season. A cost-cap breach
can also cut a team's allowance, as it did for Red Bull (14.2).

**Rookies and practice.** Teams must also give young drivers some practice sessions each season, a cheap way
to keep testing new talent.
""",
       """
**Does it work?** The ATR changes development rates at the margin: a few per cent more tunnel runs is worth
something but rarely overturns a big deficit. Its effect compounds with the cost cap, and it's one of the
reasons a team with a good concept can't simply out-develop everyone else by spending more.
""",
       [("Today most development happens…", ["in the factory", "on track every week", "at races only", "nowhere"], 0, "Testing is limited."),
        ("Under the ATR the champions get…", ["the most wind-tunnel time", "the least", "the same as everyone", "none"], 1, "70% of the baseline."),
        ("Tenth place gets…", ["70%", "100%", "115%", "200%"], 2, "Of the baseline allowance."),
        ("The ATR is meant to…", ["help the field close up", "reward winners", "save fuel", "nothing"], 0, "A handicap."),
        ("Pre-season track testing is about…", ["a few days", "a full month", "unlimited", "none"], 0, "Tightly limited.")],
       widget=W.atr_scale, blurb="The wind-tunnel allowance for each championship place.",
       data=[("Team Principal", "Your wind-tunnel time follows your championship place.")], sources=SOURCES),

    ch("14.5", "Protests, appeals and grey areas", "When a clever idea meets the rulebook.",
       """
If a team thinks a rival's car breaks the rules, it can **protest** to the race stewards, who can ask the
FIA's technical delegate to inspect it. Decisions can be appealed to the FIA's International Court of
Appeal. Many famous innovations started as **grey areas**: designs the rules didn't clearly allow or ban.

Brawn's double diffuser in 2009 was protested and declared legal, and won the title. Mercedes' DAS steering
in 2020 was legal that year and banned from the next. Racing Point's 2020 brake ducts, copied from a
Mercedes, cost the team 15 points and a fine.
""",
       """
**How a grey area plays out.** A team finds an interpretation; it may ask the FIA privately whether it's
legal (a clarification); rivals spot it and protest or ask for a directive; the FIA rules, and the rules
are usually rewritten for the following season. Being first to a legal loophole can be worth a season's
advantage while others copy it.

**Scrutineering.** Cars are checked every weekend: dimensions, mass, flexibility tests on wings and floors,
fuel samples, and the power unit's sealed parts.
""",
       """
**Flexibility tests.** Bodywork must be rigid, but every part flexes a little. The FIA defines load tests
with allowed deflections, and teams design parts that pass the static test but bend usefully at speed, so
the FIA keeps tightening the tests and adding on-car cameras to watch wings flex. It's a permanent arms
race between designers and regulators, and a good example of rules shaping engineering.
""",
       [("A protest is made to…", ["the stewards", "the drivers", "the fans", "TV"], 0, "They can order an inspection."),
        ("Brawn's double diffuser in 2009 was…", ["declared legal and won the title", "banned at once", "never raced", "a tyre"], 0, "After protests."),
        ("Mercedes' DAS was…", ["legal in 2020, banned from 2021", "illegal at once", "a brake", "never used"], 0, "Steering-based toe change."),
        ("Racing Point's 2020 brake ducts cost…", ["15 points and a fine", "nothing", "the title", "a race ban"], 0, "Copied design rules."),
        ("Why do the FIA tighten flexibility tests?", ["Parts pass static tests but bend usefully at speed", "Paint", "Weight", "Sponsors"], 0,
         "An arms race.")],
       data=[("Race Director", "Judge real incidents and penalties yourself.")], sources=SOURCES),
]
