"""What sits behind the header of a team, driver or circuit page.

There are no photographs in this project, and that is deliberate: a motorsport photo
that is genuinely free to republish is hard to find, and twelve of them consistently
is harder still. Everything here is drawn in code instead, so it carries no licence
and nothing can rot.

Three layers stack up behind the frosted glass, each fainter than the one over it:

  1. a texture     carbon weave, speed streaks, a chequer fade and so on, tinted with
                   the team's own colour and picked from the team's id so a team keeps
                   the same one forever
  2. a trace       the actual data: a team's championship position every season since
                   1950, a driver's whole career, or a circuit's real shape
  3. the veil      the gradient cards.py already draws, which keeps text readable

If a photo is ever added to data/team_photos/ it simply sits on top of all this, so
dropping one in later needs no code change.
"""
import html

# ---------- the texture pack ----------

# Each one is a background-image that takes the team colour through {tint}. They are
# all pure CSS: no files, no requests, a few hundred bytes each.
TEXTURES = {
    "carbon": ("repeating-linear-gradient(45deg,{tint} 0 2px,transparent 2px 7px),"
               "repeating-linear-gradient(-45deg,{tint} 0 2px,transparent 2px 7px)"),
    "halftone": "radial-gradient({tint} 1.3px,transparent 1.5px)",
    "streaks": ("repeating-linear-gradient(101deg,transparent 0 22px,{tint} 22px 24px,"
                "transparent 24px 56px)"),
    "tread": ("repeating-linear-gradient(112deg,{tint} 0 5px,transparent 5px 19px),"
              "repeating-linear-gradient(0deg,{tint} 0 1px,transparent 1px 22px)"),
    "mesh": ("repeating-linear-gradient(60deg,{tint} 0 1px,transparent 1px 16px),"
             "repeating-linear-gradient(-60deg,{tint} 0 1px,transparent 1px 16px)"),
}
SIZES = {"carbon": "9px 9px", "halftone": "11px 11px", "streaks": "auto",
         "tread": "auto", "mesh": "auto"}
NAMES = sorted(TEXTURES)


def texture_for(key):
    """The same id always gets the same texture, so a team's page never changes look."""
    if not key:
        return NAMES[0]
    return NAMES[sum(ord(c) for c in str(key)) % len(NAMES)]


def texture_layer(key, colour, strength=0.30):
    """The CSS texture div, tinted with the team colour."""
    name = texture_for(key)
    tint = _rgba(colour, 0.5)
    image = TEXTURES[name].format(tint=tint)
    size = SIZES[name]
    size_rule = f"background-size:{size};" if size != "auto" else ""
    return (f'<div class="pp-weave" style="background-image:{image};{size_rule}'
            f'opacity:{strength}"></div>')


def _rgba(colour, alpha):
    colour = str(colour).lstrip("#")
    if len(colour) == 3:
        colour = "".join(c * 2 for c in colour)
    r, g, b = (int(colour[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ---------- the trace: a career, drawn ----------

WIDTH, HEIGHT = 1000, 220


def season_trace(rows, colour, best_position=None):
    """A line of championship positions through the years.

    rows = [(season, position, won_the_title)] in any order. The line rises when the
    season went well, which is the opposite of a standings table but the right way
    round for something read as a picture. Title years get a dot.
    """
    points = [(int(s), float(p), bool(w)) for s, p, w in rows
              if p is not None and p == p and p > 0]
    if len(points) < 2:
        return ""
    points.sort()
    seasons = [p[0] for p in points]
    worst = best_position or max(max(p[1] for p in points), 3)
    first, last = seasons[0], seasons[-1]
    span = max(last - first, 1)

    def place(season, position):
        x = WIDTH * (season - first) / span
        # position 1 near the top, the worst place near the bottom, with air either side
        y = 30 + (HEIGHT - 70) * (min(position, worst) - 1) / max(worst - 1, 1)
        return x, y

    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
                    for i, (x, y) in enumerate(place(s, p) for s, p, _ in points))
    area = f"{line} L{WIDTH},{HEIGHT} L0,{HEIGHT} Z"
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{colour}" opacity=".32"/>'
        for x, y in (place(s, p) for s, p, won in points if won))
    return (f'<svg class="pp-trace" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'preserveAspectRatio="none" aria-hidden="true">'
            f'<path d="{area}" fill="{colour}" opacity=".07"/>'
            f'<path d="{line}" fill="none" stroke="{colour}" stroke-width="9" '
            f'opacity=".08" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="{line}" fill="none" stroke="{colour}" stroke-width="3" '
            f'opacity=".24" stroke-linejoin="round" stroke-linecap="round"/>'
            f'{dots}</svg>')


# ---------- the trace: a circuit, drawn ----------

def track_trace(xs, ys, colour):
    """The real shape of a circuit as a single closed line.

    Unlike the career line, this is an object rather than a backdrop that stretches:
    the viewBox is the shape's own bounding box, so Monza stays long and thin and
    Monaco stays square whatever size the header ends up. CSS parks it on the right.
    """
    if xs is None or len(xs) < 20:
        return ""
    low_x, high_x = min(xs), max(xs)
    low_y, high_y = min(ys), max(ys)
    width, height = max(high_x - low_x, 1e-9), max(high_y - low_y, 1e-9)
    pad = max(width, height) * 0.06
    steps = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        px = pad + (x - low_x)
        py = pad + (high_y - y)                  # flip: screen y grows downwards
        steps.append(f"{'M' if i == 0 else 'L'}{px:.1f},{py:.1f}")
    path = " ".join(steps) + " Z"
    stroke = max(width, height) * 0.022
    return (f'<svg class="pp-track" viewBox="0 0 {width + 2 * pad:.1f} '
            f'{height + 2 * pad:.1f}" preserveAspectRatio="xMidYMid meet" '
            f'aria-hidden="true">'
            f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="{stroke * 3:.1f}" '
            f'opacity=".07" stroke-linejoin="round"/>'
            f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="{stroke:.1f}" '
            f'opacity=".30" stroke-linejoin="round"/></svg>')


def thin(values, most=260):
    """Keep at most `most` points, evenly spread. A lap has thousands and the line
    looks the same with a few hundred."""
    values = list(values)
    if len(values) <= most:
        return values
    step = len(values) / most
    return [values[int(i * step)] for i in range(most)]


# ---------- putting the layers together ----------

def build(colour, key=None, photo=None, trace="", strength=0.30, dark=True):
    """Everything that goes behind a page header, in order, as one block of HTML.

    The last layer is a shade that darkens the left-hand side, where the title and the
    blurb sit. It means the art can be as busy as it likes on the right while the
    words stay as readable as they would be on a plain panel.
    """
    shot = (f'<div class="shot" style="background-image:url(\'{html.escape(photo)}\')">'
            f'</div>' if photo else "")
    edge = "rgba(8,8,14,.80)" if dark else "rgba(255,255,255,.86)"
    middle = "rgba(8,8,14,.34)" if dark else "rgba(255,255,255,.44)"
    shade = (f'<div class="pp-shade" style="background:linear-gradient(90deg,'
             f'{edge} 0%,{middle} 38%,transparent 72%)"></div>')
    return f'{shot}{texture_layer(key, colour, strength)}{trace}{shade}'
