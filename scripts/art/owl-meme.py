"""Writes slides/art/owl-meme.svg, step 2 of the owl slide: the "How to draw an owl" meme's drawings, whose
owl is traced and built as an owl-shaped board. The board is traced from the drawing, in its pixels.

Each board part carries an svg.build role and its start in quarter beats (see diagrams.css).
"""
import math
import re
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'

# The meme's two drawings, title and captions painted out (public/images/other/owl-meme-drawing.png),
# and where its owl sits: the board is drawn in the owl's own pixels from there.
DRAW_W, DRAW_H = 530, 384
OWL_AT = (236, 4)

# The drawing shows on its own for about 3 s before the trace starts, in quarter beats (65 ms each).
HOLD = 46

# Traced from the drawing: tufts, head, body, then the tail below the branch.
OWL = ('M99 2 C104 10 110 22 116 30 C128 26 150 26 164 34 C170 26 176 18 181 13 '
       'C184 24 182 40 176 50 C182 62 184 82 186 96 C198 108 204 140 205 180 '
       'C207 215 204 245 196 262 C190 276 186 290 183 304 C186 330 183 352 176 364 '
       'C168 372 150 374 140 368 C128 360 114 340 104 318 C98 306 92 294 84 284 '
       'C66 268 52 248 50 220 C47 180 50 140 56 108 C60 100 64 96 66 92 '
       'C63 78 64 62 70 50 C78 36 86 18 99 2 Z')

# The branch along its own axis: from the drawing's left edge, down to the right at ~12°.
BRANCH_AT = (4, 259)
BRANCH_ANGLE = 11.8
BRANCH = 'M2 -13 L282 -8 Q288 0 282 8 L2 13 Q-4 0 2 -13 Z'
BRANCH_G = f'translate({BRANCH_AT[0]} {BRANCH_AT[1]}) rotate({BRANCH_ANGLE})'

EYES = [(114, 71), (156, 71)]

# Wing resistor arrays, one column down each side.
WINGS = [(63, 134), (195, 128)]
WING_STEP, WING_COUNT = 12, 6


def n(v):
    return f'{round(v, 2):g}'


def body_edges(y):
    """Inside of the body at height y, read off the drawing."""
    left = {100: 56, 150: 52, 200: 50, 230: 52, 250: 60, 270: 75}
    right = {100: 188, 150: 200, 200: 205, 230: 205, 250: 198, 270: 190}

    def lerp(tab):
        ks = sorted(tab)
        for a, b in zip(ks, ks[1:]):
            if a <= y <= b:
                return tab[a] + (tab[b] - tab[a]) * (y - a) / (b - a)
        return tab[ks[0]] if y < ks[0] else tab[ks[-1]]
    return lerp(left), lerp(right)


def branch_top(x):
    return BRANCH_AT[1] - 13 + math.tan(math.radians(BRANCH_ANGLE)) * (x - BRANCH_AT[0])


def at(x, y, rot, body):
    return f'<g transform="translate({n(x)} {n(y)}) rotate({n(rot)})">{body}</g>'


def passive(x, y, rot=0, kind='res', w=6, h=3):
    """A two-terminal SMD part: body, tinned ends."""
    cap = w * 0.22
    return at(x, y, rot, f'<rect class="op-{kind}" x="{n(-w / 2)}" y="{n(-h / 2)}" width="{n(w)}" height="{n(h)}"/>'
                         f'<path class="op-tin" d="M{n(-w / 2)} {n(-h / 2)}h{n(cap)}v{n(h)}h{n(-cap)}z '
                         f'M{n(w / 2 - cap)} {n(-h / 2)}h{n(cap)}v{n(h)}h{n(-cap)}z"/>')


def ic(x, y, w, h, legs, rot=0, sides=2):
    pins = []
    for k in range(legs):
        px = -w / 2 + (k + 0.5) * w / legs - 0.5
        pins.append(f'M{n(px)} {n(-h / 2 - 1.8)}h1v1.8h-1z M{n(px)} {n(h / 2)}h1v1.8h-1z')
        if sides == 4:
            py = -h / 2 + (k + 0.5) * h / legs - 0.5
            pins.append(f'M{n(-w / 2 - 1.8)} {n(py)}h1.8v1h-1.8z M{n(w / 2)} {n(py)}h1.8v1h-1.8z')
    return at(x, y, rot, f'<rect class="op-ic" x="{n(-w / 2)}" y="{n(-h / 2)}" width="{n(w)}" height="{n(h)}" rx="0.6"/>'
                         f'<path class="op-tin" d="{" ".join(pins)}"/>'
                         f'<circle class="op-silk-dot" cx="{n(-w / 2 + 1.4)}" cy="{n(-h / 2 + 1.4)}" r="0.5"/>')


def via(x, y, r=2):
    return f'<circle class="op-via" cx="{n(x)}" cy="{n(y)}" r="{r}"/>'


def led_ring(cx, cy, cls):
    rects = []
    for k in range(10):
        a = math.radians(k * 36 - 90)
        x, y = cx + 13.5 * math.cos(a), cy + 13.5 * math.sin(a)
        rects.append(f'<rect class="{cls}" x="{n(x - 2)}" y="{n(y - 2)}" width="4" height="4" rx="0.5"/>')
    return ''.join(rects)


def eye(cx, cy):
    return (led_ring(cx, cy, 'op-led') +
            f'<circle class="op-lcd" cx="{cx}" cy="{cy}" r="9"/>'
            f'<circle class="op-iris" cx="{cx}" cy="{cy}" r="5.6"/>'
            f'<circle class="op-hole" cx="{cx}" cy="{cy}" r="2.8"/>'
            f'<circle class="op-shine" cx="{n(cx + 2)}" cy="{n(cy - 2.2)}" r="1.2"/>')


def feathers():
    """The drawing's scalloped rows: (row, x, y) for each feather, clear of the branch, the power
    channel down the middle and the wing arrays."""
    spots = []
    for row, y in enumerate(range(184, 280, 11)):
        lo, hi = body_edges(y)
        x = lo + 11 + (6 if row % 2 else 0)
        while x <= hi - 11:
            clear = (y < branch_top(x) - 7 and not 112 <= x <= 148
                     and not (x < 72 and y < 202) and not (x > 186 and y < 196))
            if clear:
                spots.append((row, x, y))
            x += 12
    return spots


def board():
    out = []

    # Once the mask covers the drawing, the pencil left round it goes too; "2." and the circles stay.
    out.append('<path class="om-paper b-fade" style="--d:18" d="M46 -4 H294 V378 H0 V188 H46 Z"/>')

    # Traced round the drawing first, then the mask covers it: one board from two shapes.
    out.append(f'<path class="op-edge om-pen b-draw" pathLength="1" style="--d:0" d="{OWL}"/>')
    out.append(f'<path class="op-edge om-pen b-draw" pathLength="1" style="--d:3" transform="{BRANCH_G}" d="{BRANCH}"/>')
    out.append(f'<g class="b-fade" style="--d:12"><path class="op-mask" d="{OWL}"/>'
               f'<path class="op-mask" transform="{BRANCH_G}" d="{BRANCH}"/></g>')

    # Traces: eyes, collar, wings, power down the middle to the tail, data out along the branch.
    for d, path in [(16, 'M126 147 V104 L118 96 V90'), (16, 'M134 147 V104 L144 94 V90'),
                    (17, 'M117 156 H96 L88 148 V128'), (17, 'M143 156 H166 L174 148 V128'),
                    (17, 'M117 152 H92 L80 140 H70'), (17, 'M117 158 H96 L84 170 H70'),
                    (17, 'M143 152 H168 L180 140 H188'), (17, 'M143 158 H164 L176 170 H188'),
                    (18, 'M124 173 V300 L132 308 V338'), (18, 'M136 173 V300 L144 308 V338')]:
        out.append(f'<path class="op-trace b-draw" pathLength="1" style="--d:{d}" d="{path}"/>')
    out.append('<path class="op-trace op-trace--power b-draw" pathLength="1" style="--d:18" d="M130 173 V340"/>')
    out.append(f'<g transform="{BRANCH_G}"><path class="op-trace b-draw" pathLength="1" style="--d:19" d="M96 -3 H70"/>'
               f'<path class="op-trace b-draw" pathLength="1" style="--d:19" d="M96 1 H70"/>'
               f'<path class="op-trace b-draw" pathLength="1" style="--d:19" d="M182 -3 H196"/>'
               f'<path class="op-trace b-draw" pathLength="1" style="--d:19" d="M182 1 H196"/></g>')
    vias = [via(x, y) for x, y in ((96, 128), (174, 128), (118, 90), (144, 90))]
    vias += [via(x, y, 1.2) for x, y in ((60, 115), (198, 112), (72, 230), (186, 226), (100, 286), (160, 294))]
    out.append('<g class="b-fade" style="--d:21">' + ''.join(vias) + '</g>')

    # Silkscreen: the facial disc, the drawing's white V brows, the headers and names.
    out.append('<g class="b-fade" style="--d:20">'
               '<path class="op-silk" d="M86 56 C80 74 88 94 104 100 M184 56 C190 74 182 94 166 100"/>'
               '<path class="op-silk" d="M134 86 L127 62 C122 52 108 47 94 50 M138 86 L145 62 C150 52 164 47 178 50"/>'
               '<path class="op-silk" d="M132 80 L124 60 C118 51 106 49 96 53 M140 80 L148 60 C154 51 166 49 176 53"/>'
               '<text class="op-title" x="130" y="141" text-anchor="middle">OWL-1</text>'
               '<text class="op-text" x="100" y="160" text-anchor="middle">U2</text>'
               '<text class="op-text" x="158" y="145" text-anchor="middle">Y1</text>'
               f'<g transform="{BRANCH_G}"><path class="op-silk" d="M2 -11 L282 -6.5 M2 11 L282 6.5"/>'
               '<rect class="op-silk" x="10" y="-6" width="66" height="12" rx="1"/>'
               '<rect class="op-silk" x="192" y="-6" width="82" height="12" rx="1"/>'
               '<text class="op-text" x="10" y="-8">J1</text><text class="op-text" x="192" y="-8">J2</text></g>'
               '<text class="op-text" x="147" y="349">J3</text></g>')

    # U1 on the pale chest patch, flash and crystal beside it, its decoupling at the corners;
    # the dark collar bars become a band of chips.
    out.append(f'<g class="b-place" style="--d:22">{ic(130, 160, 26, 26, 7, sides=4)}'
               '<image href="/images/python-mark.svg" x="122" y="152" width="16" height="16"/></g>')
    out.append('<g class="b-place" style="--d:23">' + ic(100, 150, 9, 7, 4) + passive(158, 149, 0, 'metal', 8, 4.5)
               + passive(158, 158, 0, 'cap', 4, 2) + ''.join(passive(x, y, 90, 'cap', 4, 2)
                                                             for x, y in ((112, 149), (148, 149), (118, 178), (142, 178)))
               + '</g>')
    for k, (x, y) in enumerate([(70, 110), (86, 119), (103, 123), (157, 123), (174, 119), (181, 107)]):
        out.append(f'<g class="b-place" style="--d:{22 + k // 2}">{ic(x, y, 12, 7, 4)}</g>')

    # The eyes where the drawing's are, unlit for now, and the beak between them.
    for k, (x, y) in enumerate(EYES):
        out.append(f'<g class="b-place" style="--d:{24 + k}">{eye(x, y)}</g>')
    out.append('<path class="op-gold b-place" style="--d:25" d="M136 86 L140 93 L136 101 L132 93 Z"/>')

    # Wings: resistor arrays, top down. Belly: each feather a V of two 0603 parts, resistors and
    # capacitors by rows, a via under every other; they go down row by row.
    for k in range(WING_COUNT):
        out.append(f'<g class="b-place" style="--d:{25 + k}">'
                   + ''.join(ic(x, y + k * WING_STEP, 9, 5, 4, rot=90) for x, y in WINGS) + '</g>')
    for i, (row, x, y) in enumerate(feathers()):
        kind = 'res' if row % 2 == 0 else 'cap'
        v = passive(x - 2.3, y - 0.6, 38, kind) + passive(x + 2.3, y - 0.6, -38, kind)
        if i % 2 == 0:
            v += via(x, y + 4.6, 1.3)
        out.append(f'<g class="b-place" style="--d:{26 + row}">{v}</g>')

    # Talons over the branch, its header pins and the USB-C on the tail.
    talons = ''.join(f'<rect class="op-gold" x="{n(x - 1.5)}" y="{n(branch_top(x) - 4)}" width="3" height="8" rx="1.5"/>'
                     for x in (94, 100, 106, 162, 168, 174))
    out.append(f'<g class="b-place" style="--d:28">{talons}</g>')
    pins = ''.join(f'<circle class="op-gold" cx="{x}" cy="0" r="2.8"/><circle class="op-hole" cx="{x}" cy="0" r="1.3"/>'
                   for x in list(range(16, 76, 9)) + list(range(198, 276, 9)))
    out.append(f'<g class="b-fade" style="--d:27"><g transform="{BRANCH_G}">{pins}</g></g>')
    out.append('<g class="b-place" style="--d:30"><rect class="op-metal" x="119" y="340" width="24" height="11" rx="2"/>'
               '<rect class="op-metal-top" x="120.5" y="341.5" width="21" height="8" rx="1.4"/>'
               '<rect class="op-usb-mouth" x="123" y="349" width="16" height="3" rx="1.2"/></g>')

    # Last, once the feathers are on, the eyes light up.
    glow = ''.join(f'<circle class="op-glow" cx="{x}" cy="{y}" r="17"/>{led_ring(x, y, "op-led-on")}' for x, y in EYES)
    out.append(f'<g class="b-glow" style="--d:36">{glow}</g>')
    return re.sub(r'--d:(\d+)', lambda m: f'--d:{int(m[1]) + HOLD}', '\n  '.join(out))


def build():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="diagram owl-pcb owl-pcb--green build owl-meme" viewBox="0 0 {DRAW_W} {DRAW_H}" width="{DRAW_W}" height="{DRAW_H}" role="img">
  <title>The "How to draw an owl" meme: 1. two circles; 2. the owl, traced and built as an owl-shaped circuit board perched on a pin-header branch</title>
  <rect class="om-paper" width="{DRAW_W}" height="{DRAW_H}" rx="3"/>
  <image class="om-sketch" href="/images/other/owl-meme-drawing.png" width="{DRAW_W}" height="{DRAW_H}"/>
  <g transform="translate({OWL_AT[0]} {OWL_AT[1]})">
  {board()}
  </g>
</svg>
'''


(ART / 'owl-meme.svg').write_text(build())
print('wrote', ART / 'owl-meme.svg')
