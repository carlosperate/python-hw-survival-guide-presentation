"""Writes slides/art/maker-owl.svg, the conclusion's owl: off-the-shelf parts laid over the intro's owl board.

It is drawn in the meme drawing's pixels, as owl-meme.py's board is, so it lands where that board was.
Each part carries an svg.build role and its start in quarter beats (see diagrams.css).
"""
import math
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'

DRAW_W, DRAW_H = 530, 384
BRANCH_AT, BRANCH_ANGLE, BRANCH_LEN = (240, 263), 11.8, 286
EYES = [(350, 78), (394, 78)]
MIDDLE = 372

# The breadboard body's hole grid, 8 apart either side of its channel.
PITCH = 8
LEFT_COLS = [318 + PITCH * k for k in range(6)]
RIGHT_COLS = [386 + PITCH * k for k in range(6)]
ROWS = [140 + PITCH * k for k in range(21)]


def n(v):
    return f'{round(v, 2):g}'


def ring(x, y, r):
    return f'M{n(x - r)} {n(y)} a{n(r)} {n(r)} 0 1 0 {n(2 * r)} 0 a{n(r)} {n(r)} 0 1 0 {n(-2 * r)} 0'


def role(body, kind, d):
    return f'<g class="b-{kind}" style="--d:{d}">{body}</g>'


def drawn(d_attr, cls, d):
    return f'<path class="{cls} b-draw" pathLength="1" style="--d:{d}" d="{d_attr}"/>'


def wire(d_attr, colour, ends, d):
    """A jumper wire: its pins go in first, then the wire draws from one end to the other."""
    pins = ''.join(f'<circle class="bb-pin" cx="{x}" cy="{y}" r="2.2"/>' for x, y in ends)
    return (role(pins, 'fade', d) + drawn(d_attr, 'bb-wire-edge', d)
            + drawn(d_attr, f'bb-wire bb-wire--{colour}', d))


def branch_top(x):
    """The top edge of the branch strip at x."""
    a = math.radians(BRANCH_ANGLE)
    return BRANCH_AT[1] + math.tan(a) * (x - BRANCH_AT[0]) - 13 / math.cos(a)


def defs():
    rail = ''.join(f'<rect class="bb-hole" x="{2.5 + PITCH * i}" y="2.5" width="3" height="3" rx="0.5"/>' for i in range(5))
    return ('<defs>'
            f'<pattern id="mo-holes" width="{PITCH}" height="{PITCH}" x="{LEFT_COLS[0] - 4}" y="{ROWS[0] - 4}" patternUnits="userSpaceOnUse">'
            '<rect class="bb-hole" x="2.5" y="2.5" width="3" height="3" rx="0.5"/></pattern>'
            f'<pattern id="mo-rail-holes" width="48" height="10" x="8" y="-10" patternUnits="userSpaceOnUse">{rail}</pattern>'
            '</defs>')


def paper():
    """Covers the owl board and its branch; "2." and the circles stay."""
    return role('<path class="om-paper" d="M282 0 H530 V384 H236 V192 H282 Z"/>', 'fade', 0)


def body():
    """A breadboard stood on end: its rows of holes are the drawing's rows of feathers."""
    top, bottom = ROWS[0] - 4, ROWS[-1] + 4
    holes = ''.join(f'<rect fill="url(#mo-holes)" x="{cols[0] - 4}" y="{top}" width="{PITCH * len(cols)}" height="{bottom - top}"/>'
                    for cols in (LEFT_COLS, RIGHT_COLS))
    return role('<rect class="bb" x="302" y="112" width="140" height="210" rx="44"/>'
                f'<path class="bb-rail" d="M308 150 V284"/><path class="bb-rail bb-rail--pos" d="M436 150 V284"/>'
                f'<rect class="bb-channel" x="{MIDDLE - 4}" y="128" width="8" height="180" rx="1"/>' + holes, 'place', 4)


def chest():
    """A microcontroller board pressed in across the channel, its pins in the breadboard's holes."""
    pins = [(x, y) for x in (LEFT_COLS[3], RIGHT_COLS[2]) for y in ROWS[:7]]
    rings = ''.join(f'<circle class="op-gold" cx="{x}" cy="{y}" r="2.6"/><circle class="op-hole" cx="{x}" cy="{y}" r="1.2"/>' for x, y in pins)
    board = ('<g class="op-green">'
             '<rect class="op-mask bb-pico" x="334" y="130" width="76" height="70" rx="3"/>'
             '<path class="op-trace" d="M352 148 H360 M352 164 H360 M384 156 H392 M384 172 H392 M368 176 V188 M376 176 V188"/>'
             + rings +
             f'<rect class="op-ic" x="{MIDDLE - 12}" y="148" width="24" height="24" rx="1"/>'
             f'<image href="/images/python-mark.svg" x="{MIDDLE - 8}" y="152" width="16" height="16"/>'
             f'<rect class="op-metal" x="{MIDDLE - 10}" y="188" width="20" height="10" rx="2"/>'
             '</g>')
    return role(board, 'drop', 8)


def tail():
    """The USB cable: out of the board, down the channel, behind the branch and off the paper."""
    plug = f'<rect class="bb-plug" x="{MIDDLE - 7}" y="196" width="14" height="14" rx="2.5"/>'
    return role(plug, 'place', 10) + drawn(f'M{MIDDLE} 208 V318 C{MIDDLE} 340 384 356 388 380', 'mo-cable', 10)


def wing(cx, cy, angle, d):
    """A sensor breakout folded against the body: four header pins, its chip and the sensor's can."""
    pins = ''.join(f'<circle class="op-gold" cx="{x}" cy="-30" r="2.2"/><circle class="op-hole" cx="{x}" cy="-30" r="1"/>'
                   for x in (-9, -3, 3, 9))
    board = (f'<g transform="translate({cx} {cy}) rotate({angle})">'
             '<rect class="mo-breakout" x="-18" y="-38" width="36" height="84" rx="4"/>'
             + pins + '<path class="mo-breakout-trace" d="M-9 -26 V-14 M-3 -26 V-12 M3 -26 V-12 M9 -26 V-14"/>'
             '<rect class="op-ic" x="-7" y="-10" width="14" height="14" rx="1"/>'
             '<rect class="op-metal" x="-8" y="18" width="16" height="12" rx="1.5"/>'
             '<rect class="op-metal-top" x="-6" y="20" width="12" height="8" rx="1"/></g>')
    return role(board, 'place', d)


def wing_wires():
    """From the board's top pins up and over to each wing's header."""
    left, right = (LEFT_COLS[3], ROWS[1]), (RIGHT_COLS[2], ROWS[1])
    return (wire(f'M{left[0]} {left[1]} C326 {left[1]} 312 160 303 184', 'blue', [left, (303, 184)], 14)
            + wire(f'M{right[0]} {right[1]} C418 {right[1]} 432 160 441 184', 'gold', [right, (441, 184)], 15))


def head():
    """A perfboard face, its top corners cut to the drawing's ear tufts."""
    pads = ' '.join(ring(x, y, 1.5) for x in range(318, 430, PITCH) for y in range(46, 120, PITCH))
    return role('<g class="op-green">'
                '<path class="op-mask" d="M310 30 L328 42 H416 L434 30 V104 C434 120 420 128 404 128 H340 C324 128 310 120 310 104 Z"/>'
                f'<path class="op-gold" d="{pads}"/></g>', 'place', 16)


def eyes():
    """Two LED-ring modules, dark until the owl is finished."""
    out = []
    for k, (cx, cy) in enumerate(EYES):
        leds = ''.join(f'<rect class="op-led" x="{n(cx + 16 * math.cos(a) - 2.5)}" y="{n(cy + 16 * math.sin(a) - 2.5)}" width="5" height="5" rx="0.6"/>'
                       for a in (math.pi * 2 * i / 12 for i in range(12)))
        out.append(role(f'<path class="op-ic" fill-rule="evenodd" d="{ring(cx, cy, 21)} {ring(cx, cy, 11)}"/>{leds}', 'place', 18 + k))
    return ''.join(out)


def beak():
    """A plain LED, pushed into the perfboard upside down."""
    return role(f'<path class="bb-lead" d="M{MIDDLE - 4} 98 V92 M{MIDDLE + 4} 98 V92"/>'
                f'<rect class="mo-beak-flange" x="{MIDDLE - 8}" y="96" width="16" height="4" rx="1.2"/>'
                f'<path class="mo-beak" d="M{MIDDLE - 6} 99 V110 A6 6 0 0 0 {MIDDLE + 6} 110 V99 Z"/>', 'drop', 20)


def tufts():
    """Two jumper wires plugged into the head's corners, their black housings at the tips."""
    def housing(x, y, angle):
        return (f'<g transform="translate({x} {y}) rotate({angle})">'
                '<rect class="op-ic" x="-3" y="-12" width="6" height="12" rx="1"/>'
                '<rect class="op-tin" x="-1" y="-15" width="2" height="3"/></g>')
    return (wire('M318 46 C316 38 314 30 312 22', 'gold', [(318, 46)], 21)
            + wire('M426 46 C428 38 430 30 432 22', 'blue', [(426, 46)], 21)
            + role(housing(312, 22, -8) + housing(432, 22, 8), 'fade', 24))


def branch():
    """A breadboard power-rail strip for the branch."""
    strip = (f'<g transform="translate({BRANCH_AT[0]} {BRANCH_AT[1]}) rotate({BRANCH_ANGLE})">'
             f'<rect class="bb" x="0" y="-13" width="{BRANCH_LEN}" height="26" rx="3"/>'
             f'<path class="bb-rail" d="M6 -10.5 H{BRANCH_LEN - 6}"/><path class="bb-rail bb-rail--pos" d="M6 10.5 H{BRANCH_LEN - 6}"/>'
             f'<rect fill="url(#mo-rail-holes)" x="6" y="-8" width="{BRANCH_LEN - 12}" height="16"/></g>')
    return role(strip, 'place', 22)


def talons():
    """Header pins gripping the strip."""
    pins = ''.join(f'<rect class="op-gold" x="{x - 1.5}" y="{n(branch_top(x) - 6)}" width="3" height="10" rx="1.5"/>'
                   for x in (338, 344, 350, 394, 400, 406))
    return role(pins, 'fade', 25)


def lights():
    """Last, the eyes light up."""
    glow = ''.join(f'<circle class="op-glow" cx="{cx}" cy="{cy}" r="26"/>'
                   + ''.join(f'<rect class="op-led-on" x="{n(cx + 16 * math.cos(a) - 2)}" y="{n(cy + 16 * math.sin(a) - 2)}" width="4" height="4" rx="0.5"/>'
                             for a in (math.pi * 2 * i / 12 for i in range(12)))
                   for cx, cy in EYES)
    return role(glow, 'glow', 28)


def build():
    parts = [defs(), paper(), body(), chest(), tail(), wing(304, 220, 6, 12), wing(440, 220, -6, 13),
             wing_wires(), head(), eyes(), beak(), tufts(), branch(), talons(), lights()]
    inner = '\n  '.join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="diagram maker-owl build" viewBox="0 0 {DRAW_W} {DRAW_H}" '
            f'width="{DRAW_W}" height="{DRAW_H}" role="img">\n'
            '  <title>The owl from the meme, built from parts: a breadboard body, a microcontroller board on its chest, '
            'a perfboard head with LED rings for eyes and an LED beak, jumper-wire ear tufts, sensor boards for wings, '
            'perched on a breadboard power strip, with a USB cable for a tail</title>\n'
            f'  {inner}\n</svg>\n')


if __name__ == '__main__':
    svg = build()
    (ART / 'maker-owl.svg').write_text(svg, encoding='utf-8')
    print('slides/art/maker-owl.svg', len(svg), 'bytes')
