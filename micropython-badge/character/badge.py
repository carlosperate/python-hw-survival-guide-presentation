# The conference badge: a development board in four greys, with the portrait and the QR code as
# its chips. Run it for a preview in build/previews/; export.py writes it to device/idle/ for the
# board. It reads the deck's photo, QR code and fonts, so the deck needs `npm ci` first.
import math
import os
import re
import sys
from functools import cache
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from face import H, W

HERE = Path(__file__).resolve().parent
DECK = HERE.parents[1]  # the deck's checkout, which holds this programme
PHOTO = DECK / "public/images/profil-pic.jpg"
QR_SVG = DECK / "public/images/qr.svg"
FONTS = DECK / "node_modules/@fontsource-variable"
PREVIEW = HERE.parent / "build/previews/badge.png"

SCALE = 3  # drawn at three times the panel's size, then reduced
GREYS = (0, 85, 170, 255)
OUTLINE = [(35, 16), (765, 16), (784, 35), (784, 445), (765, 464), (35, 464), (16, 445), (16, 35)]
HOLES = ((33, 33), (767, 33), (33, 447), (767, 447))
OUTWARD = {"left": (-1, 0), "right": (1, 0), "top": (0, -1), "bottom": (0, 1)}
ALONG = {"left": (0, 1), "right": (0, 1), "top": (1, 0), "bottom": (1, 0)}
STYLES = {
    "name": (90, "oxanium", 600),
    "surname": (38, "oxanium", 600),
    "title": (26, "oxanium", 600),
    "subtitle": (26, "oxanium", 600),
    "day": (23, "roboto", 450),
    "room": (23, "roboto", 450),
}
SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged"}


class Problem(Exception):
    """Something the badge's checks found; export.py writes nothing then."""


def need(ok, *what):
    # Not assert: python -O would skip the checks and export a badge that fails them.
    if not ok:
        raise Problem(*what)


def require():
    """Stop with what to do if the deck's assets aren't there."""
    fonts = [font_path(f) for f in ("jetbrains-mono", "oxanium", "roboto")]
    missing = [p for p in (PHOTO, QR_SVG, *fonts) if not p.exists()]
    if missing:
        sys.exit(
            "badge.py needs the deck's assets, missing:\n  %s\nFonts come from `npm ci` in %s."
            % ("\n  ".join(str(p) for p in missing), DECK)
        )


def font_path(family):
    return FONTS / family / "files" / (family + "-latin-wght-normal.woff2")


@cache  # each face parsed once: export and the previews ask for the same few again and again
def font(family, size, weight, scale=SCALE):
    path = font_path(family)
    if (
        not path.exists()
    ):  # the slides' props and cards use the deck's fonts too, not only the badge
        sys.exit("%s is missing: the fonts come from `npm ci` in %s." % (path, DECK))
    face = ImageFont.truetype(str(path), round(size * scale))
    face.set_variation_by_axes([weight])
    return face


def text_width(family, size, weight, value):
    return font(family, size, weight).getbbox(value, anchor="lt")[2] / SCALE


def qr_cells():
    """The deck's QR code as (x, y) dark modules, read from its SVG rather than encoded again."""
    svg = QR_SVG.read_text()
    cells = set()
    for x, y, width in re.findall(r"M(\d+) (\d+)h(\d+)v1h-\d+z", svg):
        cells.update((xx, int(y)) for xx in range(int(x), int(x) + int(width)))
    for x, y in re.findall(r"M([\d.]+) ([\d.]+)a0\.42", svg):
        cells.add((int(float(x)), int(float(y))))
    need(len(cells) > 250 and all(0 <= x < 25 and 0 <= y < 25 for x, y in cells), "QR cells")
    return cells


def scaled(points):
    return [(round(x * SCALE), round(y * SCALE)) for x, y in points]


def four_greys(img):
    return img.convert("L").point([min(GREYS, key=lambda g: abs(g - n)) for n in range(256)])


class Board:
    """A canvas that knows its copper: named terminals, nets between them, vias and text boxes,
    so the checks can find crossings and copper under text."""

    def __init__(self):
        self.img = Image.new("L", (W * SCALE, H * SCALE), 255)
        self.d = ImageDraw.Draw(self.img)
        self.codes = []
        self.text_boxes = []
        self.terminals = {}
        self.nets = []
        self.vias = []
        self.trace_mask = Image.new("L", self.img.size)

    def rect(self, box, fill=0, outline=None, width=1, radius=0):
        box = tuple(round(v * SCALE) for v in box)
        args = dict(fill=fill, outline=outline, width=width * SCALE)
        if radius:
            self.d.rounded_rectangle(box, radius=radius * SCALE, **args)
        else:
            self.d.rectangle(box, **args)

    def line(self, points, fill=0, width=1):
        self.d.line(scaled(points), fill=fill, width=width * SCALE, joint="curve")

    def circle(self, x, y, r, fill=255, outline=0, width=2):
        self.d.ellipse(
            tuple(round(v * SCALE) for v in (x - r, y - r, x + r, y + r)),
            fill=fill,
            outline=outline,
            width=width * SCALE,
        )

    def poly(self, points, fill=None, outline=None, width=1):
        self.d.polygon(scaled(points), fill=fill, outline=outline, width=width * SCALE)

    def text(self, x, y, value, size, face="roboto", fill=0, weight=550):
        f = font(face, size, weight)
        box = self.d.textbbox((x * SCALE, y * SCALE), value, font=f, anchor="lt")
        need(box[2] <= W * SCALE and box[3] <= H * SCALE, "text off the panel", value, box)
        self.d.text((x * SCALE, y * SCALE), value, font=f, fill=fill, anchor="lt")
        self.text_boxes.append([value, [round(v / SCALE, 2) for v in box]])

    def label(self, x, y, value):
        self.text(x, y, value, 10, "jetbrains-mono", weight=500)

    def photo(self, x, y, width, height):
        # Head and shoulders of the deck's portrait, dithered to the four greys.
        source = Image.open(PHOTO).convert("L").crop((190, 125, 1070, 1120))
        source = ImageOps.fit(source, (width * SCALE, height * SCALE), centering=(0.5, 0.35))
        source = ImageEnhance.Contrast(source).enhance(1.02)
        source = source.filter(
            ImageFilter.UnsharpMask(radius=1.5 * SCALE, percent=110, threshold=3)
        )
        palette = Image.new("P", (1, 1))
        palette.putpalette([g for n in GREYS for g in (n, n, n)] + [255] * (252 * 3))
        source = source.resize((width, height), Image.Resampling.LANCZOS).convert("RGB")
        source = source.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        source = source.convert("L").resize(
            (width * SCALE, height * SCALE), Image.Resampling.NEAREST
        )
        self.img.paste(source, (x * SCALE, y * SCALE))

    def qr(self, x, y, module):
        # Placed after the reduction, so its modules stay pure black and white.
        self.codes.append((x, y, module))

    def terminal(self, name, point):
        need(name not in self.terminals, "terminal named twice", name)
        self.terminals[name] = tuple(point)
        return name

    def via(self, point):
        name = "via.%d" % len(self.vias)
        self.terminal(name, point)
        self.vias.append(tuple(point))
        return name

    def net(self, start, end, bends=(), ink=85, width=2):
        """A trace from start to end through bends, horizontal, vertical or at 45 degrees."""
        points = [self.terminals[start], *bends, self.terminals[end]]
        points = [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            need(x1 == x2 or y1 == y2 or abs(x2 - x1) == abs(y2 - y1), "not 45 degrees", points)
        self.line(points, fill=ink, width=width)
        ImageDraw.Draw(self.trace_mask).line(scaled(points), fill=255, width=width * SCALE)
        self.nets.append(
            {"start": start, "end": end, "points": points, "ink": ink, "width": width}
        )

    def stub(self, pin, point):
        self.net(pin, self.via(point))

    def finish(self, cells):
        """The panel-sized image in four greys, after the copper checks."""
        for x, y in self.vias:
            self.circle(x, y, 3, fill=255, outline=85, width=1)
        mask = Image.new("L", self.img.size)
        ImageDraw.Draw(mask).polygon(scaled(OUTLINE), fill=255)
        outside = ImageChops.multiply(self.trace_mask, ImageChops.invert(mask))
        need(outside.getbbox() is None, "copper outside the board's edge")
        for value, (x0, y0, x1, y1) in self.text_boxes:
            box = [int(v * SCALE) for v in (x0 - 3, y0 - 3, x1 + 3, y1 + 3)]
            need(self.trace_mask.crop(box).getbbox() is None, "copper under text", value)
        result = four_greys(self.img.resize((W, H), Image.Resampling.LANCZOS))
        d = ImageDraw.Draw(result)
        for x, y, module in self.codes:
            size = module * 33
            d.rectangle((x, y, x + size - 1, y + size - 1), fill=255)
            for xx, yy in cells:
                left, top = x + (xx + 4) * module, y + (yy + 4) * module
                d.rectangle((left, top, left + module - 1, top + module - 1), fill=0)
        native = Image.new("L", (W, H))
        ImageDraw.Draw(native).polygon(OUTLINE, fill=255)
        # Only antialiasing outside the board's edge goes.
        result = Image.composite(result, Image.new("L", (W, H), 255), native)
        need(set(result.get_flattened_data()) == set(GREYS), "not four greys")
        return result


# Parts. Each returns its terminals: pins by side for chips, pads in order for the rest.


def board_edge(c):
    c.line(OUTLINE + [OUTLINE[0]], fill=85, width=2)
    for x, y in HOLES:
        c.circle(x, y, 6, outline=85, width=2)
        c.circle(x, y, 2, fill=85, outline=85, width=0)


def header(c, x, y, count):
    c.rect((x - 9, y - 10, x + (count - 1) * 22 + 9, y + 26), fill=255, outline=85, width=2)
    names = []
    for i in range(count):
        for row in (0, 1):
            xx, yy = x + i * 22, y + row * 16
            c.circle(xx, yy, 4, fill=255, outline=0, width=2)
            name = c.terminal("header.%d.%d" % (i, row), (xx, yy))
            if row == 1:
                names.append(name)
    # Pin 1's pad is square.
    c.rect((x - 5, y - 5, x + 5, y + 5), fill=0)
    c.circle(x, y, 2, fill=255, outline=255, width=0)
    return names


def portrait_chip(c, x, y, w, h):
    """The photo as a chip's die, in a package with pins on all four sides."""
    c.rect((x - 5, y - 5, x + w + 5, y + h + 5), fill=0)
    c.photo(x, y, w, h)
    sides = {"left": [], "right": [], "top": [], "bottom": []}
    for yy in range(y + 16, y + h - 7, 24):
        c.rect((x - 19, yy - 3, x - 6, yy + 3), fill=85)
        c.rect((x + w + 6, yy - 3, x + w + 19, yy + 3), fill=85)
        sides["left"].append((x - 19, yy))
        sides["right"].append((x + w + 19, yy))
    for xx in range(x + 17, x + w - 6, 24):
        c.rect((xx - 3, y - 19, xx + 3, y - 6), fill=85)
        c.rect((xx - 3, y + h + 6, xx + 3, y + h + 19), fill=85)
        sides["top"].append((xx, y - 19))
        sides["bottom"].append((xx, y + h + 19))
    c.circle(x - 13, y - 13, 3, fill=0, outline=0, width=0)
    return {
        side: [c.terminal("photo.%s.%d" % (side, i), p) for i, p in enumerate(points)]
        for side, points in sides.items()
    }


def qr_chip(c, x, y):
    """The QR code as a chip: 25 modules and a four-module quiet zone, 4 px each."""
    size = 132
    c.rect((x - 4, y - 4, x + size + 3, y + size + 3), fill=255, outline=0, width=2, radius=3)
    sides = {side: [] for side in ("top", "bottom", "left", "right")}
    for i, t in enumerate(range(14, 120, 20)):
        boxes = {
            "top": (x + t - 3, y - 15, x + t + 3, y - 5),
            "bottom": (x + t - 3, y + size + 4, x + t + 3, y + size + 14),
            "left": (x - 15, y + t - 3, x - 5, y + t + 3),
            "right": (x + size + 4, y + t - 3, x + size + 14, y + t + 3),
        }
        points = {
            "top": (x + t, y - 15),
            "bottom": (x + t, y + size + 14),
            "left": (x - 15, y + t),
            "right": (x + size + 14, y + t),
        }
        for side in sides:
            c.rect(boxes[side], fill=85, radius=1)
            sides[side].append(c.terminal("qr.%s.%d" % (side, i), points[side]))
    c.circle(x - 13, y - 13, 3, fill=0, outline=0, width=0)
    c.qr(x, y, module=4)
    return sides


def part(c, x, y, name, vertical=False, capacitor=False, label=None):
    """A two-pad part, its designator beside it or at label: a resistor's body black, a
    capacitor's grey."""
    body = 170 if capacitor else 0
    if vertical:
        c.rect((x - 5, y - 15, x + 5, y - 8), fill=85, radius=1)
        c.rect((x - 5, y + 8, x + 5, y + 15), fill=85, radius=1)
        c.rect((x - 5, y - 8, x + 5, y + 8), fill=body, outline=85, width=1)
        pads = ((x, y - 15), (x, y + 15))
        c.label(*(label or (x - 23, y - 10)), name)
    else:
        c.rect((x - 15, y - 5, x - 8, y + 5), fill=85, radius=1)
        c.rect((x + 8, y - 5, x + 15, y + 5), fill=85, radius=1)
        c.rect((x - 8, y - 5, x + 8, y + 5), fill=body, outline=85, width=1)
        pads = ((x - 15, y), (x + 15, y))
        c.label(*(label or (x - 8, y - 20)), name)
    return [c.terminal(name + ".%d" % i, p) for i, p in enumerate(pads, 1)]


def led(c, x, y, direction):
    """An SMD LED centred at (x, y); direction is the unit step from anode to cathode."""
    dx, dy = direction

    def at(u, v):
        return x + u * dx - v * dy, y + u * dy + v * dx

    def box(a, b):
        return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))

    c.rect(box(at(-20, -5), at(-13, 5)), fill=85, radius=1)
    c.rect(box(at(13, -5), at(20, 5)), fill=85, radius=1)
    c.rect(box(at(-13, -6), at(13, 6)), fill=170, outline=0, width=1, radius=1)
    c.rect(box(at(-9, -3), at(7, 3)), fill=255)
    c.line(sorted([at(9, -4), at(9, 4)]), width=2)
    return (
        c.terminal("LED1.anode", tuple(round(v) for v in at(-20, 0))),
        c.terminal("LED1.cathode", tuple(round(v) for v in at(20, 0))),
    )


def segment(p, q, t, gap):
    # A pointed bar between two corners of a digit, shortened at both ends.
    (x0, y0), (x1, y1) = p, q
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -uy * t / 2, ux * t / 2
    x0, y0, x1, y1 = x0 + ux * gap, y0 + uy * gap, x1 - ux * gap, y1 - uy * gap
    return [
        (x0, y0),
        (x0 + ux * t / 2 + nx, y0 + uy * t / 2 + ny),
        (x1 - ux * t / 2 + nx, y1 - uy * t / 2 + ny),
        (x1, y1),
        (x1 - ux * t / 2 - nx, y1 - uy * t / 2 - ny),
        (x0 + ux * t / 2 - nx, y0 + uy * t / 2 - ny),
    ]


def seven_segment(c, x, y, text, w=11, h=18, t=3):
    """A four-digit LED display, white segments on black; returns its right edge."""
    digits = [ch for ch in text if ch != ":"]
    pitch, pad = w + 6, 6
    width = pad + len(digits) * w + (len(digits) - 1) * 6 + 6 + 6
    c.rect((x, y, x + width, y + h + 10), fill=0, width=2, radius=2)
    for i, digit in enumerate(digits):
        dx = x + pad + i * pitch + (6 if i >= 2 else 0)
        left, right = dx + t / 2, dx + w - t / 2
        top, middle, bottom = y + 5 + t / 2, y + 5 + h / 2, y + 5 + h - t / 2
        ends = {
            "a": ((left, top), (right, top)),
            "g": ((left, middle), (right, middle)),
            "d": ((left, bottom), (right, bottom)),
            "f": ((left, top), (left, middle)),
            "b": ((right, top), (right, middle)),
            "e": ((left, middle), (left, bottom)),
            "c": ((right, middle), (right, bottom)),
        }
        for name, (p, q) in ends.items():
            if name in SEGMENTS[digit]:
                c.poly(segment(p, q, t, 0.8), fill=255)
    cx = x + pad + 2 * pitch - 3
    for cy in (y + 5 + h * 0.3, y + 5 + h * 0.7):
        c.rect((cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5), fill=255)
    return x + width


def castellation(c, x, y, side):
    """A plated half-hole on the board's edge, with its pad: side is the edge it's on."""
    if side == "bottom":
        c.rect((x - 6, y - 9, x + 6, 466), fill=170, outline=85, width=1, radius=3)
        c.circle(x, 464, 4, fill=255, outline=85, width=2)
        return c.terminal("edge.%d.%d" % (x, y), (x, y - 9))
    c.rect((12, y - 6, 25, y + 6), fill=170, outline=85, width=1, radius=2)
    c.circle(16, y, 4, fill=255, outline=85, width=2)
    return c.terminal("edge.%d.%d" % (x, y), (25, y))


def step(point, side, out=0, along=0):
    (x, y), (ox, oy), (ax, ay) = point, OUTWARD[side], ALONG[side]
    return (x + ox * out + ax * along, y + oy * out + ay * along)


def via_in_pad(c, side, tip, depth):
    x, y = step(tip, side, out=-depth)
    c.circle(x, y, 1.8, fill=255, outline=255, width=0)


def render():
    """The badge as a four-grey board, and its copper for the checks."""
    c = Board()
    board_edge(c)
    tag = "#PyConES2026"
    c.text(
        62 + (218 - text_width("jetbrains-mono", 20, 500, tag)) / 2,
        38,
        tag,
        20,
        "jetbrains-mono",
        weight=500,
    )
    h = header(c, 562, 34, 8)
    p = portrait_chip(c, 62, 110, 218, 248)
    q = qr_chip(c, 630, 305)
    c.label(56, 93, "U1")
    c.label(624, 287, "U2")
    c.label(538, 30, "J1")
    used = set()

    def connect(start, end, bends=(), width=2):
        c.net(start, end, bends, width=width)
        used.update((start, end))

    # U1 to the header: one pin over the top, two up the right side.
    connect(p["top"][-1], h[0], [(271, 82), (283, 70), (542, 70)])
    for i in range(2):
        start, end = p["right"][i], h[i + 1]
        sx, sy = c.terminals[start]
        hx, hy = c.terminals[end]
        cx, lane = sx + 10 + i * 8, 78 + i * 8
        connect(
            start,
            end,
            [
                (cx - 6, sy),
                (cx, sy - 6),
                (cx, lane + 22),
                (cx + 22, lane),
                (hx - 12 - (lane - hy), lane),
                (hx - 12, hy),
            ],
        )
    # A matched pair from U1 to U2, above the talk's title and down beside it.
    connect(
        p["right"][6], q["left"][0], [(309, 270), (321, 258), (600, 258), (608, 266), (608, 312)]
    )
    connect(
        p["right"][7],
        q["left"][1],
        [(309, 294), (337, 266), (592, 266), (600, 274), (600, 331), (608, 339)],
    )
    for i in range(2):
        start, end = q["top"][-1 - i], h[-1 - i]
        sx, sy = c.terminals[start]
        ex, ey = c.terminals[end]
        turn_y = 90 + i * 8
        connect(start, end, [(sx, turn_y), (ex, turn_y - abs(sx - ex))])

    # U2's supply through R1, decoupled by C1 and C2 to ground vias.
    r1 = part(c, 664, 198, "R1")
    c1 = part(c, 644, 259, "C1", vertical=True, capacitor=True)
    c2 = part(c, 684, 259, "C2", vertical=True, capacitor=True)
    supply = c.terminal("supply.junction", (704, 274))
    connect(h[3], r1[0], [(628, 177)], width=3)
    connect(r1[1], supply, [(692, 198), (704, 210)], width=3)
    connect(supply, q["top"][3], width=3)
    connect(c1[1], q["top"][0], width=3)
    connect(c2[1], q["top"][2], width=3)
    for pads, x in ((c1, 644), (c2, 684)):
        connect(pads[0], c.via((x, 236)))

    # The status LED down the right edge, from the header's last top-row pad.
    r2 = part(c, 772, 90, "R2", vertical=True, label=(752, 86))
    anode, cathode = led(c, 772, 140, (0, 1))
    c.label(752, 136, "D1")
    c.label(756, 182, "ACT")
    connect("header.7.0", r2[0], [(745, 34), (772, 61)])
    connect(r2[1], anode)
    connect(cathode, c.via((772, 174)))

    # The time on a 7-segment display that U2 drives.
    right = seven_segment(
        c, round(341 + text_width("roboto", 23, 450, "Sunday") + 12), 376, "12:10"
    )
    c.label(right + 8, 374, "DS1")
    pads = []
    for y in (390, 398):
        c.rect((right, y - 2, right + 4, y + 2), fill=85)
        pads.append(c.terminal("DS1.%d" % y, (right + 4, y)))
    connect(pads[0], q["left"][4], [(597, 390), (606, 399)])
    connect(pads[1], q["left"][5], [(583, 398), (604, 419)])

    # U2's bottom pins drop straight onto castellations at the board's edge.
    for name in q["bottom"]:
        x, y = c.terminals[name]
        connect(name, castellation(c, x, 464, "bottom"))

    handle = "@carlosperate"
    c.text(
        62 + (218 - text_width("jetbrains-mono", 24, 500, handle)) / 2,
        411,
        handle,
        24,
        "jetbrains-mono",
        weight=500,
    )
    # Optical alignment: every line's ink starts at x = 342.
    lines = [
        ("name", (335, 110), "Carlos"),
        ("surname", (339, 203), "Pereira Atencio"),
        ("title", (340, 303), "Python on Hardware"),
        ("subtitle", (341, 337), "Survival Guide"),
        ("day", (341, 379), "Sunday"),
        ("room", (341, 411), "Aula B5 – Nagarro"),
    ]
    for key, position, value in lines:
        size, face, weight = STYLES[key]
        c.text(*position, value, size, face, weight=weight)

    # Every other pin is routed out: U1's middle left pins to castellations, the rest to a via
    # fence of near and far rows. U2's right pins end 8 px from the edge: vias in their pads.
    chips = {"U1": (p, 15), "U2": (q, 13)}  # pins, and the far row's distance
    for chip, (pins, far) in chips.items():
        for side, names in pins.items():
            for i, name in enumerate(names):
                if name in used:
                    continue
                tip = c.terminals[name]
                if chip == "U1" and side == "left" and 1 <= i <= 8:
                    c.net(name, castellation(c, 16, tip[1], "left"))
                elif chip == "U2" and side == "right":
                    via_in_pad(c, side, tip, 3)
                else:
                    c.stub(name, step(tip, side, out=far if i % 2 else 7))
    return c


def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    t = (
        0
        if dx == dy == 0
        else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    )
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def check(c):
    """Problems with the copper: nets that touch, vias too close to anything."""
    problems = []

    def cross(a, b, d):
        return (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])

    def on(a, b, d):
        return (
            cross(a, b, d) == 0
            and min(a[0], b[0]) <= d[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= d[1] <= max(a[1], b[1])
        )

    def touch(a, b, d, e):
        values = cross(a, b, d), cross(a, b, e), cross(d, e, a), cross(d, e, b)
        return (values[0] * values[1] < 0 and values[2] * values[3] < 0) or any(
            (on(a, b, d), on(a, b, e), on(d, e, a), on(d, e, b))
        )

    # One layer of copper shows: nets that share no terminal must not meet.
    for n, m in combinations(c.nets, 2):
        if {n["start"], n["end"]} & {m["start"], m["end"]}:
            continue
        for a, b in zip(n["points"], n["points"][1:]):
            for d, e in zip(m["points"], m["points"][1:]):
                if touch(a, b, d, e):
                    problems.append(("nets touch", n["start"], m["start"]))
    for i, v in enumerate(c.vias):
        name = "via.%d" % i
        for net in c.nets:
            if name in (net["start"], net["end"]):
                continue
            for a, b in zip(net["points"], net["points"][1:]):
                if seg_dist(v, a, b) < 4 + net["width"] / 2:
                    problems.append(("via on copper", name, net["start"]))
        for j, w in enumerate(c.vias[:i]):
            if math.dist(v, w) < 8:
                problems.append(("vias touch", name, "via.%d" % j))
        for value, (x0, y0, x1, y1) in c.text_boxes:
            if x0 - 5 < v[0] < x1 + 5 and y0 - 5 < v[1] < y1 + 5:
                problems.append(("via on text", name, value))
        if any(math.dist(v, hole) < 12 for hole in HOLES):
            problems.append(("via by a hole", name))
        if not (21 <= v[0] <= W - 21 and 21 <= v[1] <= H - 21):
            problems.append(("via by the edge", name))
    return problems


def check_qr(image, c, cells):
    """The QR code pure black on white, in its four-module quiet zone, as a reader needs."""
    ((x, y, module),) = c.codes
    size = module * 33
    for yy in range(size):
        for xx in range(size):
            cx, cy = xx // module - 4, yy // module - 4
            want = 0 if (cx, cy) in cells else 255
            need(image.getpixel((x + xx, y + yy)) == want, "QR module", cx, cy)


def draw():
    """The badge's image: 800x480, four greys, checked."""
    require()
    cells = qr_cells()
    c = render()
    problems = check(c)
    need(not problems, *problems)
    image = c.finish(cells)
    check_qr(image, c, cells)
    return image


def gs2(image):
    """The image as an 800x480 GS2_HMSB frame (0 black to 3 white), as framebuf packs it: a
    byte's leftmost pixel in its lowest two bits."""
    level = {g: i for i, g in enumerate(GREYS)}
    data = image.tobytes()
    return bytes(
        level[data[i]]
        | level[data[i + 1]] << 2
        | level[data[i + 2]] << 4
        | level[data[i + 3]] << 6
        for i in range(0, len(data), 4)
    )


def main():
    image = draw()
    os.makedirs(PREVIEW.parent, exist_ok=True)
    image.save(PREVIEW)
    print(PREVIEW)


if __name__ == "__main__":
    main()
