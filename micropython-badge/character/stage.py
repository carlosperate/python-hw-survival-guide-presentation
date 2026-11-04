# Props for the slides' animations (slides.py), drawn over the face as props.py's are. Unlike the
# character's own, some carry a label in the deck's JetBrains Mono, and some need the eyes'
# centres: a lens over an eye, glasses round both.
import math

from PIL import Image, ImageDraw

import badge
from face import oval, thick_line


def label(d, x, y, text, size):
    d.text(
        (x, y), text, font=badge.font("jetbrains-mono", size, 800, scale=1), fill=0, anchor="mm"
    )


def spikes(x, y, outer, inner, n, turn=0):
    """A polygon's points, n spikes round (x, y), the first at turn degrees."""
    pts = []
    for i in range(n * 2):
        a = math.radians(turn + i * 180 / n)
        k = outer if i % 2 == 0 else inner
        pts.append((x + k * math.cos(a), y + k * math.sin(a)))
    return pts


def burst(d, x, y, r1, r2, n, w):
    d.polygon(spikes(x, y, r2, r1, n), fill=255, outline=0, width=w)


def star(d, x, y, r):
    d.polygon(spikes(x, y, r, r * 0.45, 5, turn=-90), fill=0)


def daze(d):
    """Stars round a dazed head."""
    for x, y, r in ((290, 60, 22), (400, 40, 28), (510, 60, 22)):
        star(d, x, y, r)


def bubble(d, x, y, w, h, tail, text, size):
    """A speech bubble centred at (x, y), its tail pointing at tail, saying text."""
    d.rounded_rectangle(
        (x - w / 2, y - h / 2, x + w / 2, y + h / 2), 24, fill=255, outline=0, width=9
    )
    base = (x - 18, y + h / 2 - 6), (x + 18, y + h / 2 - 6)
    d.polygon([base[0], tail, base[1]], fill=255)
    d.line([base[0], tail, base[1]], fill=0, width=9)
    label(d, x, y, text, size)


def tick(d, x, y):
    d.line([(x - 18, y), (x - 4, y + 14), (x + 22, y - 16)], fill=0, width=9, joint="curve")


def waves(d, x, y, n=3):
    for k in range(n):
        r = 46 + 34 * k
        d.arc((x - r, y - r, x + r, y + r), 200, 340, fill=0, width=10)


def chip(d, x, y, mood):
    """A sensor in a black package with a face of its own: asleep, awake or happy."""
    w, h = 150, 96
    for k in range(4):
        px = x - w / 2 + 22 + k * (w - 44) / 3
        d.rectangle((px - 6, y - h / 2 - 16, px + 6, y + h / 2 + 16), fill=0)
    d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 10, fill=0)
    for side in (-1, 1):
        if mood == "asleep":
            thick_line(d, (x + side * 30 - 13, y - 4), (x + side * 30 + 13, y - 4), 7)
        else:
            oval(d, x + side * 30, y - 6, 9, 12, 255)
    if mood == "happy":
        d.arc((x - 18, y - 2, x + 18, y + 26), 20, 160, fill=255, width=7)


def pings(d, n):
    for k in range(n):  # out from the face, towards the chip
        r = 120 + k * 50
        d.arc((440 - r, 250 - r, 440 + r, 250 + r), -10, 70, fill=0, width=10)


def heap(d, cells, big=0, big_x=0):
    """The heap as a row of 12 cells, 1 used and 0 free; big, a block that many wide above it."""
    y = 372
    for i, used in enumerate(cells):
        x = 60 + i * 56
        d.rectangle((x, y, x + 48, y + 56), fill=0 if used else 255, outline=0, width=6)
    if big:
        d.rectangle((big_x, y - 100, big_x + big * 56 - 8, y - 44), fill=0)
        for k in range(1, big):
            d.line((big_x + k * 56 - 4, y - 100, big_x + k * 56 - 4, y - 44), fill=255, width=6)


def snake(d, x, speed=0, flip=False):
    """A python along the bottom, its head at x; speed draws lines behind it."""
    hy, s = 400, -1 if flip else 1
    pts = [(x - s * t, hy + 30 * math.sin(t / 55)) for t in range(0, 360, 8)]
    d.line(pts, fill=0, width=44, joint="curve")
    oval(d, pts[-1][0], pts[-1][1], 22, 22, 0)
    oval(d, x + s * 20, hy - 4, 52, 38, 0)
    oval(d, x + s * 34, hy - 18, 13, 13, 255)
    oval(d, x + s * 37, hy - 19, 6, 6, 0)
    tongue = x + s * 70
    d.line([(tongue, hy + 8), (tongue + s * 30, hy + 8)], fill=0, width=8)
    d.line([(tongue + s * 30, hy + 8), (tongue + s * 46, hy - 6)], fill=0, width=7)
    d.line([(tongue + s * 30, hy + 8), (tongue + s * 46, hy + 22)], fill=0, width=7)
    for k in range(speed):
        y = hy - 60 + k * 34
        x0 = pts[-1][0] - s * (50 + 30 * (k % 2))
        thick_line(d, (x0, y), (x0 - s * (150 + 60 * (k % 2)), y), 12)


def lens(img, d, cx, cy, r=165, mag=1.3):
    """A magnifying glass, what's under it enlarged."""
    box = (round(cx - r / mag), round(cy - r / mag), round(cx + r / mag), round(cy + r / mag))
    inside = img.crop(box).resize((2 * r, 2 * r), Image.BICUBIC)
    mask = Image.new("L", inside.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 2 * r, 2 * r), fill=255)
    img.paste(inside, (round(cx - r), round(cy - r)), mask)
    c, s = math.cos(math.radians(40)), math.sin(math.radians(40))
    thick_line(d, (cx + c * r, cy + s * r), (cx + c * (r + 110), cy + s * (r + 110)), 30)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=0, width=18)


def specs(d, eyes):
    """Round glasses over both eyes, each lens at its own eye's height."""
    ((x1, y1), (x2, y2)), z = eyes
    for x, y in ((x1, y1), (x2, y2)):
        d.ellipse((x - 122 * z, y - 128 * z, x + 122 * z, y + 128 * z), outline=0, width=16)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    d.arc((cx - 50 * z, cy - 80 * z, cx + 50 * z, cy), 200, 340, fill=0, width=14)
    thick_line(d, (x1 - 122 * z, y1 - 20 * z), (x1 - 190 * z, y1 - 50 * z), 14)
    thick_line(d, (x2 + 122 * z, y2 - 20 * z), (x2 + 190 * z, y2 - 50 * z), 14)


def wave(d, phase, y_hi, y_lo, bits, step):
    """A square wave scrolling left by phase steps."""
    pts, x = [], 40 - phase * step
    for bit in bits * 2:
        y = y_hi if bit == "1" else y_lo
        if pts:
            pts.append((x, y))
        pts.append((x, y))
        x += step
        pts.append((x, y))
    d.line(pts, fill=0, width=12)
    d.rectangle((0, y_hi - 30, 30, y_lo + 30), fill=255)
    d.rectangle((680, y_hi - 30, 800, y_lo + 30), fill=255)


def probes(d, gap, zap=False):
    """A multimeter's two probes from either side, their tips gap apart at x = 400; zap, the
    continuity beep as they touch."""
    y, lx, rx = 356, 400 - gap / 2, 400 + gap / 2
    d.rounded_rectangle((lx - 300, y - 22, lx - 70, y + 22), 18, fill=0)
    thick_line(d, (lx - 80, y), (lx, y), 10)
    d.rounded_rectangle((rx + 70, y - 22, rx + 300, y + 22), 18, fill=255, outline=0, width=9)
    thick_line(d, (rx, y), (rx + 80, y), 10)
    if zap:
        burst(d, 400, 356, 30, 70, 10, 8)
        waves(d, 400, 300)


def wire(d, phase=None):
    """A plain wire, or, seen through the specs, its bits."""
    if phase is None:
        thick_line(d, (0, 420), (800, 420), 14)
    else:
        wave(d, phase, 380, 440, "0110100111", 56)


def analyser(d, phase, ack=False):
    """The bits going by, then the sensor's answer."""
    wave(d, phase, 330, 392, "0110100111010", 62)
    if ack:
        bubble(d, 610, 220, 250, 84, (580, 300), "", 42)
        label(d, 588, 220, "ACK", 42)
        tick(d, 672, 220)


def box(d):
    d.polygon([(250, 330), (220, 270), (330, 290), (330, 340)], fill=255, outline=0, width=10)
    d.polygon([(550, 330), (580, 270), (470, 290), (470, 340)], fill=255, outline=0, width=10)
    d.rectangle((250, 330, 550, 470), fill=255, outline=0, width=12)
    label(d, 400, 405, "256 KB", 48)


def f1(img, d, x0, speed):
    """An open-wheeled racing car facing right, its rear wing at x0, the face in its helmet."""
    body = [
        (x0 + 20, 392),
        (x0 + 30, 350),
        (x0 + 200, 338),
        (x0 + 236, 300),
        (x0 + 330, 300),
        (x0 + 360, 340),
        (x0 + 600, 382),
        (x0 + 610, 400),
        (x0 + 400, 408),
        (x0 + 20, 408),
    ]
    d.polygon(body, fill=255, outline=0, width=10)
    d.line((x0 + 120, 372, x0 + 330, 372), fill=0, width=8)  # the sidepod's edge
    d.rectangle((x0 - 20, 278, x0 + 70, 300), fill=0)  # the rear wing
    d.rectangle((x0 + 10, 296, x0 + 32, 392), fill=0)
    d.rectangle((x0 + 540, 414, x0 + 640, 428), fill=0)  # the front wing
    d.rectangle((x0 + 626, 396, x0 + 640, 428), fill=0)
    for wx, r in ((x0 + 110, 56), (x0 + 500, 50)):
        oval(d, wx, 410, r, r, 0)
        oval(d, wx, 410, r * 0.45, r * 0.45, 255)
        oval(d, wx, 410, r * 0.18, r * 0.18, 0)
    # The helmet, black but for its visor, where the face drawn under it shows through.
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((x0 + 228, 238, x0 + 332, 342), fill=255)
    md.rounded_rectangle((x0 + 238, 268, x0 + 326, 312), 14, fill=0)
    img.paste(0, (0, 0), mask)
    d.arc((x0 + 200, 222, x0 + 360, 350), 200, 330, fill=0, width=12)  # the halo
    for k in range(speed):
        y = 300 + k * 34
        thick_line(d, (x0 - 40, y), (x0 - 180 - 50 * (k % 2), y), 10)


def flag(d):
    """A chequered flag."""
    x, y, n, s = 560, 40, 5, 34
    thick_line(d, (x - 8, y - 10), (x - 8, y + 260), 12)
    for i in range(n):
        for j in range(3):
            if (i + j) % 2 == 0:
                d.rectangle(
                    (x + i * s, y + j * s + i * 6, x + (i + 1) * s, y + (j + 1) * s + i * 6),
                    fill=0,
                )
    d.line([(x, y), (x + n * s, y + n * 6)], fill=0, width=6)
    d.line([(x, y + 3 * s), (x + n * s, y + 3 * s + n * 6)], fill=0, width=6)


def draw(img, d, name, args, eyes):
    """One of these props, by name; eyes: the eyes' centres and the face's zoom."""
    if name == "daze":
        daze(d)
    elif name == "box":
        box(d)
    elif name == "heap":
        heap(d, *args)
    elif name == "snake":
        snake(d, *args)
    elif name == "f1":
        f1(img, d, *args)
    elif name == "flag":
        flag(d)
    elif name == "pings":
        pings(d, *args)
    elif name == "chip":
        chip(d, *args)
    elif name == "bubble":
        bubble(d, *args)
    elif name in ("lens", "specs") and eyes is None and len(args) < 2:
        raise ValueError(name + " needs the eyes' centres: draw it through idle.render()")
    elif name == "lens":  # over an eye (0 or 1), or at a point
        lens(img, d, *(eyes[0][args[0]] if len(args) == 1 else args))
    elif name == "specs":
        specs(d, eyes)
    elif name == "wire":
        wire(d, *args)
    elif name == "probes":
        probes(d, *args)
    elif name == "analyser":
        analyser(d, *args)
    else:
        raise ValueError("no prop " + name)
