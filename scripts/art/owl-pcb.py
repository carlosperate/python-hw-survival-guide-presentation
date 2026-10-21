"""Writes slides/art/owl-pcb.svg, "2. Build the rest of the owl": an owl-shaped board that builds itself.

Each part carries an svg.build role and its start in quarter beats (see diagrams.css).
"""
import math
import re
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'

OWL = ('M176 8 C196 24 220 34 240 34 C260 34 284 24 304 8 C316 30 326 54 326 84 '
       'C344 116 352 160 336 196 C320 230 282 248 240 248 C198 248 160 230 144 196 '
       'C128 160 136 116 154 84 C154 54 164 30 176 8 Z')


def n(v):
    v = round(v, 2)
    return f'{v:g}'


def pts_d(pts, closed=False):
    d = 'M' + ' L'.join(f'{n(x)} {n(y)}' for x, y in pts)
    return d + (' Z' if closed else '')


def check45(pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = round(x1 - x0, 3), round(y1 - y0, 3)
        assert dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) < 0.01, f'not 45°: {(x0, y0)} -> {(x1, y1)}'


def intersect(p1, p2, p3, p4):
    x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return p2
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def offset_polyline(pts, d):
    """Constant-clearance parallel offset, joined at the offset lines' intersections."""
    segs = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        segs.append(((x0 + nx * d, y0 + ny * d), (x1 + nx * d, y1 + ny * d)))
    out = [segs[0][0]]
    for (a0, a1), (b0, b1) in zip(segs, segs[1:]):
        out.append(intersect(a0, a1, b0, b1))
    out.append(segs[-1][1])
    return out


def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def parse_cubics(d):
    """Only M and C commands, absolute."""
    toks = re.findall(r'[MCZ]|-?\d+(?:\.\d+)?', d)
    i, cur, segs = 0, None, []
    while i < len(toks):
        t = toks[i]
        if t == 'M':
            cur = (float(toks[i + 1]), float(toks[i + 2])); i += 3
        elif t == 'C':
            i += 1
            while i < len(toks) and toks[i] not in 'MCZ':
                p1 = (float(toks[i]), float(toks[i + 1])); p2 = (float(toks[i + 2]), float(toks[i + 3])); p3 = (float(toks[i + 4]), float(toks[i + 5]))
                segs.append((cur, p1, p2, p3)); cur = p3; i += 6
        else:
            i += 1
    return segs


U1 = (240, 166)
STEP_TRACE = 8  # first trace starts after the outline and mask


class Build:
    """Collects elements in drawing order, each with a build role and its start in quarter beats."""

    def __init__(self):
        self.out = []

    def raw(self, s):
        self.out.append(s)

    def role(self, s, role, d):
        self.out.append(f'<g class="b-{role}" style="--d:{d}">{s}</g>')

    def draw(self, d_attr, cls, d):
        self.out.append(f'<path class="{cls} b-draw" pathLength="1" style="--d:{d}" d="{d_attr}"/>')

    def trace(self, pts, cls='op-trace', d=None):
        check45(pts)
        if d is None:
            x, y = pts[0]
            d = STEP_TRACE + round(math.hypot(x - U1[0], y - U1[1]) / 14)
        self.draw(pts_d(pts), cls, d)

    def bus(self, pts, count, pitch, d=None):
        check45(pts)
        lines = []
        for k in range(count):
            off = (k - (count - 1) / 2) * pitch
            ln = offset_polyline(pts, off) if off else list(pts)
            lines.append(ln)
            self.trace(ln, d=d)
        return lines


def ring(x, y, r):
    return f'M{n(x - r)} {n(y)} a{n(r)} {n(r)} 0 1 0 {n(2 * r)} 0 a{n(r)} {n(r)} 0 1 0 {n(-2 * r)} 0'


def via_path(points, r=2.1):
    return ' '.join(ring(x, y, r) for x, y in points)


def chip(x, y, kind, rot, w, h):
    cap = w * 0.2
    return (f'<g transform="translate({n(x)} {n(y)}) rotate({rot})">'
            f'<rect class="op-{kind}" x="{n(-w / 2)}" y="{n(-h / 2)}" width="{n(w)}" height="{n(h)}"/>'
            f'<path class="op-tin" d="M{n(-w / 2)} {n(-h / 2)}h{n(cap)}v{n(h)}h{n(-cap)}z M{n(w / 2 - cap)} {n(-h / 2)}h{n(cap)}v{n(h)}h{n(-cap)}z"/></g>')


def text(x, y, s, cls='op-text', anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ''
    return f'<text class="{cls}" x="{n(x)}" y="{n(y)}"{a}>{s}</text>'


def left_edge_x(y):
    """Leftmost x of the owl outline at height y."""
    best = None
    for s in parse_cubics(OWL):
        prev = cubic(*s, 0)
        for k in range(1, 201):
            cur = cubic(*s, k / 200)
            if (prev[1] - y) * (cur[1] - y) <= 0 and prev[1] != cur[1]:
                t = (y - prev[1]) / (cur[1] - prev[1])
                x = prev[0] + t * (cur[0] - prev[0])
                if x < 240 and (best is None or x < best):
                    best = x
            prev = cur
    return best


def qfn_pads(cx, cy, size, pins):
    h = size / 2
    step = size / (pins + 1)
    return [(-h + i * step) for i in range(1, pins + 1)], h


def build():
    b = Build()
    branch = ('M12 224 C40 214 120 216 240 214 C360 216 440 214 468 224 C476 236 474 252 462 258 '
              'C380 260 300 256 240 258 C180 260 100 260 18 258 C6 252 6 234 12 224 Z')

    # Board: the outline routes, then the mask covers it. Union of two shapes: strokes, then fills.
    b.draw(branch, 'op-edge', 0)
    b.draw(OWL, 'op-edge', 1)
    b.role(f'<path class="op-mask" d="{branch}"/><path class="op-mask" d="{OWL}"/>', 'fade', 4)

    # ---- U1 and the nets around it ----
    offs, h = qfn_pads(*U1, 28, 11)
    cx, cy = U1
    L = [cy + o for o in offs]   # left and right pad y
    B = [cx + o for o in offs]   # top and bottom pad x
    edge_l, edge_r, edge_t, edge_b = cx - h - 2, cx + h + 2, cy - h - 2, cy + h + 2.4

    # U2 (flash): right legs straight into U1, left legs drop to vias, VCC through its cap.
    u2x = 206
    legs = [L[2], L[4], L[6], L[8]]  # 159, 163.67, 168.33, 173
    for y in legs:
        b.trace([(u2x + 11, y), (edge_l, y)])
    flash_vias = [(191, legs[0]), (188.5, legs[1]), (191, legs[2])]
    for (vx, vy) in flash_vias:
        b.trace([(u2x - 11, vy), (vx + 2.1, vy)])
    b.trace([(u2x - 11, legs[3]), (191, legs[3]), (191, 179)])
    b.trace([(191, 183), (191, 186)])

    # Eye data out of U1's top, 45° to the bottom LED of each ring.
    b.trace([(B[5] - 2.33, edge_t), (B[5] - 2.33, 142), (219.67, 124), (209, 124)])
    b.trace([(B[5] + 2.33, edge_t), (B[5] + 2.33, 142), (260.33, 124), (271, 124)])

    # Crystal on the right.
    b.trace([(edge_r, L[0]), (263, L[0])])
    b.trace([(edge_r, L[2]), (263, L[2])])
    b.trace([(275, L[0]), (277, L[0]), (277, L[0] - 5.3), (279, L[0] - 5.3)])
    b.trace([(275, L[2]), (277, L[2]), (277, L[2] + 4), (279, L[2] + 4)])

    # Header buses: left from U1's bottom, right from its right side, one line per pad.
    pad_y = 250
    lb = b.bus([(sum(B[:4]) / 4, edge_b), (sum(B[:4]) / 4, 190), (sum(B[:4]) / 4 - 36, 226), (150, 226)], 4, B[1] - B[0])
    for (x, y), tx in zip(sorted((ln[-1] for ln in lb), key=lambda p: -p[1]), [140, 130, 120, 110]):
        b.trace([(x, y), (tx, y), (tx, pad_y - 3.4)])
    ry = sum(L[6:10]) / 4
    rb = b.bus([(edge_r, ry), (266, ry), (266, 188), (300, 222), (330, 222)], 4, L[1] - L[0])
    for (x, y), tx in zip(sorted((ln[-1] for ln in rb), key=lambda p: -p[1]), [340, 350, 360, 370]):
        b.trace([(x, y), (tx, y), (tx, pad_y - 3.4)])

    # USB: D+/D- as a pair straight up into U1, VBUS to the regulator, shell ground to vias.
    usb_pads = [227.17 + 2.333 * k for k in range(12)]
    for x0, x1 in ((B[8], usb_pads[5]), (B[9], usb_pads[6])):
        drop = x0 - x1
        b.trace([(x0, edge_b), (x0, 222.17 - drop), (x1, 222.17), (x1, 224)], d=STEP_TRACE + 5)
    b.trace([(usb_pads[2], 224), (usb_pads[2], 219), (226.83, 214), (227, 214)], 'op-trace op-trace--power')
    b.trace([(usb_pads[0], 224), (usb_pads[0], 223), (224.17, 220)])
    b.trace([(usb_pads[11], 224), (usb_pads[11], 223), (255.83, 220)])

    # Decoupling at U1's corners and the crystal's load caps: pin, cap, ground via.
    b.trace([(231, 145), (233, 147), (233, edge_t)])
    b.trace([(227, 145), (225.6, 145)])
    b.trace([(249, 145), (247, 147), (247, edge_t)])
    b.trace([(253, 145), (254.4, 145)])
    b.trace([(edge_l, L[10]), (222, L[10]), (222, 184)])
    b.trace([(222, 188), (219, 191)])
    b.trace([(edge_r, L[10]), (256, L[10]), (256, 184)])
    b.trace([(256, 188), (256, 189.4)])
    b.trace([(283, L[0] - 5.3), (286.2, L[0] - 5.3)])
    b.trace([(283, L[2] + 4), (286.2, L[2] + 4)])

    # U3 regulator above the USB: ground and enable to vias, output up to a via.
    b.trace([(227, 210), (224.6, 210)])
    b.trace([(227, 206), (224, 206), (224, 203.5)])
    b.trace([(243, 206), (246, 203), (246, 201.5)])

    # ---- Wings: a touch slider of chevron pads (feathers), each through a series resistor to a via ----
    w, th, gap, count = 16, 11, 2, 6
    dv = w / 2  # 45° chevrons
    tops = [120 + (th + gap) * k for k in range(count)]
    lo = math.ceil(max(left_edge_x(y) for t in tops for y in (t, t + th, t + th + dv)) + 3)
    hi = lo + w
    xr = hi + 5
    xv = xr + 6
    assert xv + 1.8 < flash_vias[1][0] - 2.1 - 1.5, 'wing vias crowd the flash vias'
    wing_feathers, wing_vias = [], []
    for side in (1, -1):
        mx = (lambda x: x) if side == 1 else (lambda x: 480 - x)
        l, r, m = mx(lo), mx(hi), mx(lo + w / 2)
        for i, t in enumerate(tops):
            shape = (f'M{n(l)} {t} L{n(m)} {n(t + dv)} L{n(r)} {t} V{t + th} '
                     f'L{n(m)} {n(t + th + dv)} L{n(l)} {t + th} Z')
            wing_feathers.append((shape, 12 + i))
            yc = t + th / 2
            b.trace([(r, yc), (mx(xr) - side * 2.5, yc)], d=14 + i)
            b.trace([(mx(xr) + side * 2.5, yc), (mx(xv) - side * 1.8, yc)], d=15 + i)
            wing_vias.append((mx(xv), yc))
    scales = [(lo, t + th / 2 - 7) for t in tops]

    # ---- Copper you can see: pads, holes, vias, fiducials ----
    pads_l = [(50 + 10 * i, pad_y) for i in range(10)]
    pads_r = [(340 + 10 * i, pad_y) for i in range(10)]
    b.role('<rect class="op-gold" x="46.6" y="246.6" width="6.8" height="6.8" rx="0.6"/>'
           f'<path class="op-gold" d="{via_path(pads_l[1:] + pads_r, 3.4)}"/>'
           f'<path class="op-hole" d="{via_path(pads_l + pads_r, 1.5)}"/>', 'fade', 16)
    for shape, d in wing_feathers:
        b.role(f'<path class="op-clear-ring" d="{shape}"/><path class="op-gold" d="{shape}"/>', 'fade', d)
    b.role(f'<path class="op-via" d="{via_path(wing_vias, 1.8)}"/>', 'fade', 18)
    other_vias = list(flash_vias) + [(191, 189), (222, 132), (258, 132), (196, 128), (284, 128),
                                     (222, 210), (224, 201.5), (246, 199.5), (222.67, 218.5), (257.33, 218.5), (178, 212), (302, 212),
                                     (223.5, 145), (256.5, 145), (217.5, 192.5), (256, 191.5), (288.3, 154.33 - 5.3), (288.3, 163.67 + 4)]
    b.role(f'<path class="op-via" d="{via_path(other_vias)}"/>', 'fade', 17)
    for mxh in (28, 452):
        b.role(f'<circle class="op-gold" cx="{mxh}" cy="240" r="7.5"/><circle class="op-hole" cx="{mxh}" cy="240" r="4.2"/>', 'fade', 15)
    for fx in (186, 294):
        b.role(f'<circle class="op-clear" cx="{fx}" cy="40" r="4.2"/><circle class="op-gold" cx="{fx}" cy="40" r="1.8"/>', 'fade', 15)

    # ---- Silkscreen ----
    silk = ['<rect class="op-silk" x="43" y="243" width="104" height="14" rx="1"/>',
            '<rect class="op-silk" x="333" y="243" width="104" height="14" rx="1"/>',
            '<circle class="op-silk" cx="28" cy="240" r="10"/>', '<circle class="op-silk" cx="452" cy="240" r="10"/>',
            '<rect class="op-silk" x="213" y="221" width="54" height="40" rx="1.5"/>',
            text(44, 241, 'J1'), text(426, 241, 'J2'), text(262, 218, 'J3 USB-C'),
            text(240, 48, 'OWL-1', 'op-title', 'middle'), text(240, 56, 'REV A · PyCon ES 2026', 'op-text', 'middle'),
            text(171, 64, 'D1-D12'), text(276, 64, 'D13-D24'),
            text(218, 150, 'U1'), text(199, 153, 'U2'), text(263, 150, 'Y1'), text(228, 202, 'U3'),
            text(lo - 2, 116, 'R1-R6'), text(480 - hi - 6, 116, 'R7-R12')]
    for cxe in (205, 275):
        silk.append(f'<circle class="op-silk" cx="{cxe}" cy="96" r="34"/>')
    b.role(''.join(silk), 'fade', 18)

    # ---- Parts, placed in order ----
    def soic(x, y, w2, h2, legs_y, dot):
        d = ' '.join(f'M{n(x - w2 / 2 - 4)} {n(ly - 1)}h4v2h-4z M{n(x + w2 / 2)} {n(ly - 1)}h4v2h-4z' for ly in legs_y)
        return (f'<rect class="op-ic" x="{n(x - w2 / 2)}" y="{n(y - h2 / 2)}" width="{w2}" height="{h2}" rx="1"/>'
                f'<path class="op-tin" d="{d}"/><circle class="op-silk-dot" cx="{n(dot[0])}" cy="{n(dot[1])}" r="0.9"/>')

    ticks = []
    for o in offs:
        ticks += [f'M{n(cx + o - 0.55)} {n(cy - h - 2)}h1.1v2.4h-1.1z', f'M{n(cx + o - 0.55)} {n(cy + h - 0.4)}h1.1v2.4h-1.1z',
                  f'M{n(cx - h - 2)} {n(cy + o - 0.55)}v1.1h2.4v-1.1z', f'M{n(cx + h - 0.4)} {n(cy + o - 0.55)}v1.1h2.4v-1.1z']
    m = 28 * 0.62
    b.role(f'<rect class="op-ic" x="{cx - h}" y="{cy - h}" width="28" height="28" rx="1"/>'
           f'<path class="op-tin" d="{" ".join(ticks)}"/>'
           f'<image href="/images/python-mark.svg" x="{n(cx - m / 2)}" y="{n(cy - m / 2)}" width="{n(m)}" height="{n(m)}"/>'
           f'<circle class="op-silk-dot" cx="{cx - h + 2.6}" cy="{cy - h + 2.6}" r="0.9"/>', 'place', 20)
    b.role(soic(u2x, 166, 14, 20, legs, (u2x + 4.5, 173.5)), 'place', 21)
    b.role('<rect class="op-metal" x="263" y="152.5" width="12" height="9.5" rx="1.2"/>'
           '<rect class="op-metal-top" x="264.5" y="154" width="9" height="6.5" rx="0.8"/>', 'place', 22)
    b.role(soic(235, 210, 8, 12, [], (232.5, 206.5)) +
           '<path class="op-tin" d="M227 205h4v2h-4z M227 209h4v2h-4z M227 213h4v2h-4z M239 205h4v2h-4z M239 213h4v2h-4z"/>', 'place', 23)
    passives = [(229, 145, 'cap', 0), (251, 145, 'cap', 0), (222, 186, 'cap', 90), (256, 186, 'cap', 90),
                (191, 181, 'cap', 90), (281, 154.33 - 5.3, 'cap', 0), (281, 163.67 + 4, 'cap', 0)]
    for i, (x, y, kind, rot) in enumerate(passives):
        b.role(chip(x, y, kind, rot, 4, 2), 'place', 24 + i // 2)
    for side in (1, -1):
        for i, (x0, y0) in enumerate(scales):
            b.role(chip(xr if side == 1 else 480 - xr, y0 + 7, 'res', 0, 4, 2), 'place', 25 + i)

    # USB-C receptacle: stainless shell, shell legs in plated slots, a fine-pitch pad row behind it.
    slots = ''.join(f'<rect class="op-gold" x="{sx - 3.5}" y="{sy - 5}" width="7" height="10" rx="3.5"/>'
                    f'<rect class="op-hole" x="{sx - 1.6}" y="{sy - 3.4}" width="3.2" height="6.8" rx="1.6"/>'
                    for sx in (218.5, 261.5) for sy in (236, 251))
    pads = ' '.join(f'M{n(x - 0.6)} 224h1.2v4.4h-1.2z' for x in usb_pads)
    b.role(slots + f'<path class="op-gold" d="{pads}"/>', 'fade', 16)
    b.role('<rect class="op-metal" x="222" y="230" width="36" height="29" rx="2"/>'
           '<rect class="op-metal-top" x="223.5" y="231.5" width="33" height="26" rx="1.4"/>'
           '<path class="op-metal-edge" d="M224 234.2 H256"/>'
           '<rect class="op-metal-edge" x="228" y="237" width="24" height="12" rx="1.6"/>'
           '<rect class="op-usb-mouth" x="230.5" y="251.2" width="5" height="2.6" rx="0.6"/>'
           '<rect class="op-usb-mouth" x="244.5" y="251.2" width="5" height="2.6" rx="0.6"/>'
           '<rect class="op-usb-mouth" x="225" y="256.5" width="30" height="3" rx="1.5"/>'
           '<path class="op-metal-edge" d="M222 241 h-2.5 M222 246 h-2.5 M258 241 h2.5 M258 246 h2.5"/>', 'place', 28)

    # Feet gripping the branch.
    b.role(''.join(f'<rect class="op-gold" x="{fx + dx - 2}" y="{236 + abs(dx) // 3}" width="4" height="11" rx="2"/>'
                   for fx in (200, 280) for dx in (-7, 0, 7)), 'fade', 17)

    # ---- The eyes and beak, switched on last ----
    eyes = []
    for cxe in (205, 275):
        cye = 96
        leds = ''.join(f'<rect class="op-led" x="{n(cxe + 25 * math.cos(a) - 4)}" y="{n(cye + 25 * math.sin(a) - 4)}" width="8" height="8" rx="0.8"/>'
                       for a in (math.pi * 2 * k / 12 for k in range(12)))
        b.role(leds + f'<circle class="op-lcd" cx="{cxe}" cy="{cye}" r="15.5"/>', 'place', 30)
        eyes.append(f'<circle class="op-glow" cx="{cxe}" cy="{cye}" r="30"/>'
                    + ''.join(f'<rect class="op-led-on" x="{n(cxe + 25 * math.cos(a) - 2.2)}" y="{n(cye + 25 * math.sin(a) - 2.2)}" width="4.4" height="4.4" rx="0.5"/>'
                              for a in (math.pi * 2 * k / 12 for k in range(12)))
                    + f'<circle class="op-iris" cx="{cxe}" cy="{cye}" r="10"/>'
                      f'<circle class="op-hole" cx="{cxe}" cy="{cye}" r="5"/>'
                      f'<circle class="op-shine" cx="{cxe + 3}" cy="{cye - 3}" r="1.8"/>')
    b.role('<path class="op-gold" d="M240 112 L247 120 L240 130 L233 120 Z"/>', 'fade', 16)
    b.role(''.join(eyes), 'glow', 34)
    return b


if __name__ == '__main__':
    b = build()
    inner = '\n'.join('  ' + line for line in b.out)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" class="diagram owl-pcb owl-pcb--green build" viewBox="0 0 480 262" width="480" height="262" role="img">\n'
           '  <title>An owl-shaped PCB perched on a branch-shaped pin header, its eyes rings of LEDs round two round displays</title>\n'
           f'{inner}\n</svg>\n')
    (ART / 'owl-pcb.svg').write_text(svg, encoding='utf-8')
    print('slides/art/owl-pcb.svg', len(svg), 'bytes')
