# What the face looks at: drawn over it, never tilted with it, and big enough to read across a
# room. Each sits in a corner; the pose moves the face to the opposite one.
import math
import random

from PIL import Image, ImageDraw

import stage
from face import H, W, heart, oval, thick_line


def clock(d, hh, mm, cx=660, cy=142, r=112):
    k = r / 84
    oval(d, cx, cy, r + 16 * k, r + 16 * k, 0)
    oval(d, cx, cy, r, r, 255)
    for hour in range(12):
        a = math.radians(hour * 30)
        sx, sy = math.sin(a), -math.cos(a)
        if hour % 3 == 0:
            p, q = (
                (cx + sx * r * 0.88, cy + sy * r * 0.88),
                (cx + sx * r * 0.66, cy + sy * r * 0.66),
            )
            thick_line(d, p, q, round(10 * k))
        else:
            oval(d, cx + sx * r * 0.82, cy + sy * r * 0.82, 5 * k, 5 * k, 0)
    hands = (((hh % 12 + mm / 60) * 30, 0.5, round(16 * k)), (mm * 6, 0.78, round(10 * k)))
    for angle, length, width in hands:
        a = math.radians(angle)
        thick_line(
            d, (cx, cy), (cx + math.sin(a) * r * length, cy - math.cos(a) * r * length), width
        )
    oval(d, cx, cy, 12 * k, 12 * k, 0)


PHONE = (255, 325, 545)  # left, top, right; it runs off the bottom, as if held below


def phone(img, scroll):
    d = ImageDraw.Draw(img)
    x0, y0, x1 = PHONE
    k = (x1 - x0) / 200  # laid out at 200 px wide
    d.rounded_rectangle((x0, y0, x1, H + 60), 30 * k, fill=0)
    mid = (x0 + x1) / 2
    d.rounded_rectangle(
        (mid - 18 * k, y0 + 12 * k, mid + 18 * k, y0 + 19 * k), 3 * k, fill=255
    )  # speaker
    screen = (x0 + 12 * k, y0 + 30 * k, x1 - 12 * k, H + 60)
    layer, mask = Image.new("L", (W, H), 255), Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle(screen, 16 * k, fill=255)
    ld = ImageDraw.Draw(layer)
    top = screen[1] + (8 - scroll) * k
    for i, width in enumerate((100, 70, 110)):  # chat bubbles, left and right
        x = screen[0] + 8 * k if i % 2 == 0 else screen[2] - (8 + width) * k
        ld.rounded_rectangle(
            (x, top + i * 24 * k, x + width * k, top + (i * 24 + 16) * k), 8 * k, fill=0
        )
    # A photo of a cat.
    px0, py0 = screen[0] + 8 * k, top + 82 * k
    ld.rounded_rectangle(
        (px0, py0, screen[2] - 8 * k, py0 + 84 * k), 8 * k, outline=0, width=round(4 * k)
    )
    cx, cy = (px0 + screen[2] - 8 * k) / 2, py0 + 48 * k
    for side in (-1, 1):
        ear = [
            (cx + side * 26 * k, cy - 8 * k),
            (cx + side * 22 * k, cy - 36 * k),
            (cx + side * 6 * k, cy - 20 * k),
        ]
        ld.polygon(ear, fill=0)
    oval(ld, cx, cy, 27 * k, 22 * k, 0)
    for side in (-1, 1):
        oval(ld, cx + side * 10 * k, cy - 3 * k, 4 * k, 6 * k, 255)
    ld.polygon([(cx - 4 * k, cy + 7 * k), (cx + 4 * k, cy + 7 * k), (cx, cy + 11 * k)], fill=255)
    img.paste(layer, mask=mask)


# The notebook lies in the bottom left, turned to face the eyes, as its writer would have it: the
# page's top points away from them, into the corner. (u, v) runs across a line and down the page.
BOOK_C, BOOK_W, BOOK_H = (186, 291), 290, 218
PAGE_DOWN = (0.86, -0.51)  # down the page: towards the eyes
LINES = [0.32, 0.5, 0.68, 0.86]


def flat_at(u, v):
    (dx, dy), (cx, cy) = PAGE_DOWN, BOOK_C
    a, b = (u - 0.5) * BOOK_W, (v - 0.5) * BOOK_H
    return cx + dy * a + dx * b, cy - dx * a + dy * b


_CORNERS = [flat_at(u, v) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
_NEAR = max(y for _, y in _CORNERS)
_DEPTH = _NEAR - min(y for _, y in _CORNERS)
_MID = sum(x for x, _ in _CORNERS) / 4


def book_at(u, v):
    # A little perspective: the far (upper) side recedes, so the pad lies on the desk.
    x, y = flat_at(u, v)
    far = (_NEAR - y) / _DEPTH  # 0 at the near edge, 1 at the far one
    return _MID + (x - _MID) * (1 - 0.15 * far), _NEAR - (_NEAR - y) * 0.82


def page_heart(d, u, v, size):
    pts = []
    for k in range(48):
        t = k / 48 * 2 * math.pi
        hx = 16 * math.sin(t) ** 3
        hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(book_at(u + hx / 32 * size / BOOK_W, v - hy / 32 * size / BOOK_H))
    d.polygon(pts, fill=0)


def scribble(line, upto):
    """Joined-up loops along a ruled line, in words, up to `upto` (0..1) of its length."""
    pts, words = [], []
    u = 0.08
    rng = random.Random(line)
    while u < 0.08 + 0.84 * upto:
        n = rng.randint(3, 6)  # loops in this word
        word = []
        for k in range(n * 8 + 1):
            tt = k / 8 * 2 * math.pi
            uu = u + 0.0105 * tt - 0.016 * math.sin(tt)
            if uu > 0.08 + 0.84 * upto or uu > 0.92:
                break
            word.append(book_at(uu, LINES[line] - 0.015 - 0.07 * (1 - math.cos(tt)) / 2))
        if len(word) > 1:
            words.append(word)
            pts = word
        u += 0.0105 * n * 2 * math.pi + 0.05
    return words, pts[-1] if pts else book_at(0.08, LINES[line] - 0.015)


def pencil(d, tip, wiggle=0, k=1.3):
    ang = math.radians(-105 + wiggle)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    hw = 13 * k

    def at(t, side=0):
        return tip[0] + ux * t * k + nx * side * hw, tip[1] + uy * t * k + ny * side * hw

    d.polygon([at(34, -1), at(120, -1), at(120, 1), at(34, 1)], fill=255, outline=0, width=6)
    d.line([at(36), at(118)], fill=0, width=4)
    d.polygon([tip, at(34, -1), at(34, 1)], fill=255, outline=0, width=6)
    d.polygon([tip, at(12, -12 / 34), at(12, 12 / 34)], fill=0)
    d.polygon([at(120, -1), at(134, -1), at(134, 1), at(120, 1)], fill=0)  # the ferrule
    oval(d, *at(142), hw, hw, 0)  # the eraser
    oval(d, *at(142), hw - 6, hw - 6, 255)
    d.polygon([at(134, -0.6), at(142, -0.6), at(142, 0.6), at(134, 0.6)], fill=255)


def notebook(img, progress, doodle=False, lifted=False):
    """Returns where the pencil's tip is, for the eyes to follow."""
    d = ImageDraw.Draw(img)
    d.polygon(
        [book_at(0, 0), book_at(1, 0), book_at(1, 1), book_at(0, 1)], fill=255, outline=0, width=7
    )
    for v in LINES:
        d.line([book_at(0.06, v), book_at(0.94, v)], fill=0, width=3)
    for k in range(9):  # the spiral binding
        x, y = book_at(0.08 + k * 0.105, -0.02)
        oval(d, x, y, 10, 10, 255)
        d.ellipse((x - 10, y - 10, x + 10, y + 10), outline=0, width=5)
    tip = book_at(0.08, LINES[0] - 0.015)
    for line in range(3):
        upto = min(1, max(0, progress - line))
        if upto <= 0:
            break
        words, tip = scribble(line, upto)
        for word in words:
            d.line(word, fill=0, width=5, joint="curve")
    if doodle:
        page_heart(d, 0.4, LINES[3] - 0.06, 42)
        tip = book_at(0.62, LINES[3] - 0.02)
    if lifted:
        tip = (tip[0] + 22, tip[1] - 30)
    pencil(d, tip, wiggle=6 if int(progress * 2) % 2 else -4)
    return tip


def question(d, x=650, y=26, size=150):
    w = int(size / 5)
    d.arc((x - size * 0.45, y, x + size * 0.45, y + size * 0.8), 200, 90, fill=0, width=w)
    thick_line(d, (x, y + size * 0.8), (x, y + size * 1.08), w)
    oval(d, x, y + size * 1.4, w * 0.75, w * 0.75, 0)


def _curve(a, c, b, n=12):
    # A quadratic Bézier from a to b, pulled towards c.
    return [
        (
            (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
            (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1],
        )
        for t in (k / n for k in range(n + 1))
    ]


def bulb(d, x=650, y=152, r=80):
    k = r / 58
    for a in (-160, -125, -90, -55, -20):  # it shines
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        p, q = (
            (x + ca * (r + 18 * k), y + sa * (r + 18 * k)),
            (x + ca * (r + 40 * k), y + sa * (r + 40 * k)),
        )
        thick_line(d, p, q, round(9 * k))
    # The glass: a round top that narrows into a neck.
    glass = [
        (x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a)))
        for a in range(140, 401, 5)
    ]
    glass += _curve(
        (x + 0.77 * r, y + 0.64 * r), (x + 0.42 * r, y + 0.95 * r), (x + 0.42 * r, y + 1.3 * r)
    )
    glass += _curve(
        (x - 0.42 * r, y + 1.3 * r), (x - 0.42 * r, y + 0.95 * r), (x - 0.77 * r, y + 0.64 * r)
    )
    d.polygon(glass, fill=255)
    d.line(glass + glass[:2], fill=0, width=round(9 * k), joint="curve")
    for side in (-1, 1):  # the filament: two wires splaying out to a coil
        d.line(
            (x + side * 0.12 * r, y + 1.3 * r, x + side * 0.28 * r, y + 0.45 * r),
            fill=0,
            width=round(4 * k),
        )
    coil = [
        (x - 0.28 * r + i * 0.07 * r, y + 0.45 * r - (0.1 * r if i % 2 else 0)) for i in range(9)
    ]
    d.line(coil, fill=0, width=round(5 * k), joint="curve")
    d.rounded_rectangle(
        (x - 0.47 * r, y + 1.26 * r, x + 0.47 * r, y + 1.86 * r), 6 * k, fill=0
    )  # the screw
    for t in (1.42, 1.62):
        d.line(
            (x - 0.4 * r, y + t * r + 4, x + 0.4 * r, y + t * r - 4), fill=255, width=round(4 * k)
        )
    tip = [
        (x - 0.3 * r, y + 1.85 * r),
        (x + 0.3 * r, y + 1.85 * r),
        (x + 0.14 * r, y + 2.04 * r),
        (x - 0.14 * r, y + 2.04 * r),
    ]
    d.polygon(tip, fill=0)


def trail(d, a, b, c):
    # A dashed flight path from a to b, curving towards c, stopping short of b.
    pts = [q for q in _curve(a, c, b, 40) if math.dist(q, b) > 80]
    for k in range(0, len(pts) - 1, 2):
        d.line([pts[k], pts[k + 1]], fill=0, width=6)


def fly(d, x, y, upside=False, k=3.0):
    s = -1 if upside else 1
    for wx, wy in ((-8, -14), (5, -16)):  # wings, behind the body
        box = (x + k * (wx - 8), y + k * (s * wy - 12), x + k * (wx + 8), y + k * (s * wy + 12))
        d.ellipse(box, fill=255, outline=0, width=4)
    for lx in (-7, 0, 7):
        d.line((x + k * lx, y + k * s * 6, x + k * lx * 1.5, y + k * s * 16), fill=0, width=4)
    oval(d, x, y, 14 * k, 10 * k, 0)
    oval(d, x + 15 * k, y - s * 3 * k, 7 * k, 7 * k, 0)
    oval(d, x + 17 * k, y - s * 5 * k, 2.5 * k, 2.5 * k, 255)


def puff(d, x=400, y=414):
    for dx in (-20, 0, 20):
        thick_line(d, (x + dx, y - 36), (x + dx * 1.6, y - 80), 8)


def zee(d, x, y, size):
    w = max(7, int(size / 5))
    thick_line(d, (x, y), (x + size, y), w)
    thick_line(d, (x + size, y), (x, y + size), w)
    thick_line(d, (x, y + size), (x + size, y + size), w)


ZEES = [(560, 330, 40), (610, 236, 56), (660, 128, 74), (700, 12, 92)]
HEARTS = [(610, 400, 40), (690, 335, 30), (185, 405, 34)]


def draw(img, props, eyes=None):
    """Each prop over the face, in order; eyes: the eyes' centres and the face's zoom, for the
    slides' props (stage.py) that need them."""
    d = ImageDraw.Draw(img)
    for name, *args in props:
        if name == "clock":
            clock(d, *args)
        elif name == "phone":
            phone(img, *args)
        elif name == "notes":
            notebook(img, *args)
        elif name == "z":
            for x, y, size in ZEES[: args[0]]:
                zee(d, x, y, size)
        elif name == "hearts":
            for x, y, size in HEARTS[: args[0]]:
                heart(d, x, y, size)
        elif name == "question":
            question(d)
        elif name == "bulb":
            bulb(d)
        elif name == "fly":
            x, y, fx, fy, cx, cy, *upside = args
            trail(d, (fx, fy), (x, y), (cx, cy))
            fly(d, x, y, *upside)
        elif name == "puff":
            puff(d)
        elif name == "bang":
            thick_line(d, (754, 24), (742, 136), 30)
            oval(d, 738, 180, 18, 18, 0)
        elif name == "bug":  # the fly, on its own: what the detective finds
            fly(d, *args)
        else:
            stage.draw(img, d, name, args, eyes)
