# The character's face: two eyes, eyebrows and a mouth, drawn from a pose (a dict of the fields in
# REST). Three styles share every pose. Host only (Pillow): the board gets the frames, not this.
import math

from PIL import Image, ImageDraw

W, H = 800, 480
FX, FY = 400, 232  # the face's centre at rest

STYLES = {
    # Outlined eyes with big pupils (B1 in ../prototypes/).
    "outlined": dict(
        kind="outlined",
        sep=145,
        rx=78,
        ry=98,
        ow=18,
        pr=50,
        hl=(-0.4, -0.45, 0.38),
        bw=22,
        bh=55,
        gap=48,
        arch=12,
        mouth=153,
    ),
    # Solid ovals with one highlight (F1).
    "oval": dict(
        kind="solid",
        sep=150,
        shape="oval",
        w=70,
        h=100,
        glint=(-0.35, -0.45, 0.24, 0.17),
        bw=22,
        bh=56,
        gap=45,
        arch=14,
        mouth=160,
    ),
    # Solid soft squares (F3).
    "rounded": dict(
        kind="solid",
        sep=150,
        shape=64,
        w=78,
        h=90,
        glint=(-0.4, -0.4, 0.28, 0.24),
        bw=26,
        bh=54,
        gap=45,
        arch=18,
        mouth=160,
    ),
}

# A pose. Head: centre (fx, fy), turn (yaw), nod (pitch), tilt (roll, degrees), size (zoom).
# Eyes: gaze (gx, gy, -1..1), cross, upper lid (lid, 0..1) and its droop, eye size (scale) and
# pupil size, fit (the pupil kept whole below the lid), and what they show (eyes: open, closed,
# happy, heart, or a symbol: led, led-lit, x; or one per eye). Brows: lift, lift_r (right one
# only), btilt (inner ends up), arch (0 flattens them).
REST = dict(
    fx=FX,
    fy=FY,
    yaw=0,
    pitch=0,
    roll=0,
    zoom=1.2,
    gx=0,
    gy=0,
    cross=0,
    lid=0,
    droop=0,
    scale=1,
    pupil=1,
    fit=False,
    eyes="open",
    lift=0,
    lift_r=0,
    btilt=0,
    arch=1,
    mouth=None,
    props=(),
)


def pose(**kw):
    return {**REST, **kw}


def oval(d, cx, cy, rx, ry, fill):
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill)


def thick_line(d, p, q, w):
    d.line([p, q], fill=0, width=w)
    for x, y in (p, q):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=0)


def brow(d, cx, y, half, tilt, w, arch=0):
    # tilt > 0 raises the right end; arch bends it up in the middle.
    pts = []
    for i in range(9):
        t = i / 8 * 2 - 1
        pts.append((cx + t * half, y - tilt * t - arch * (1 - t * t)))
    d.line(pts, fill=0, width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=0)


def heart(d, cx, cy, size, fill=0):
    r = size * 0.5
    oval(d, cx - r * 0.95, cy - r * 0.3, r, r, fill)
    oval(d, cx + r * 0.95, cy - r * 0.3, r, r, fill)
    d.polygon([(cx - size * 0.97, cy), (cx + size * 0.97, cy), (cx, cy + size * 1.1)], fill=fill)


def closed(d, cx, cy, half, w):
    d.arc((cx - half, cy - 22, cx + half, cy + 22), 15, 165, fill=0, width=w)


def lid_cut(mask, cx, top, ry, rx, lid, side, droop, inset=0):
    # A straight lid; `droop` lowers its outer end, which reads as sleepy.
    edge = top + lid * 2 * ry - inset

    def y(x):
        return edge + droop * ry * side * (x - cx) / rx

    x0, x1 = cx - 3 * rx, cx + 3 * rx
    ImageDraw.Draw(mask).polygon(
        [(x0, top - 3 * ry), (x1, top - 3 * ry), (x1, y(x1)), (x0, y(x0))], fill=0
    )


def mouth(d, kind, x, y):
    if kind == "smile":
        d.arc((x - 38, y - 40, x + 38, y + 18), 20, 160, fill=0, width=12)
    elif kind == "grin":
        d.pieslice((x - 34, y - 26, x + 34, y + 30), 0, 180, fill=0)
    elif kind == "big-smile":
        d.arc((x - 66, y - 62, x + 66, y + 30), 22, 158, fill=0, width=16)
    elif kind == "big-grin":
        d.pieslice((x - 62, y - 40, x + 62, y + 46), 0, 180, fill=0)
    elif kind == "o":
        oval(d, x, y + 10, 17, 21, 0)
    elif kind == "small-o":
        oval(d, x, y + 8, 9, 11, 0)
    elif kind == "flat":
        thick_line(d, (x - 22, y + 6), (x + 26, y + 2), 10)


def outlined_eye(img, p, eye, side, ex, ey, wf, hf, st):
    d = ImageDraw.Draw(img)
    rx, ry, ow = p["rx"] * wf * st["scale"], p["ry"] * hf * st["scale"], p["ow"]
    if eye == "closed":
        return closed(d, ex, ey + ry * 0.15, rx, ow + 4)
    if eye == "happy":
        return d.arc(
            (ex - rx, ey - ry * 0.4, ex + rx, ey + ry * 1.2), 200, 340, fill=0, width=ow + 8
        )
    outer, inner = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
    oval(ImageDraw.Draw(outer), ex, ey, rx + ow, ry + ow, 255)
    oval(ImageDraw.Draw(inner), ex, ey, rx, ry, 255)
    if st["lid"]:
        lid_cut(outer, ex, ey - ry, ry, rx, st["lid"], side, st["droop"], inset=ow)
        lid_cut(inner, ex, ey - ry, ry, rx, st["lid"], side, st["droop"])
    img.paste(0, mask=outer)
    layer = Image.new("L", (W, H), 255)
    ld = ImageDraw.Draw(layer)
    pr = p["pr"] * st["pupil"]
    px, py = ex + st["gx"] * (rx - pr * wf * 0.55), ey + st["gy"] * (ry - pr * 0.55)
    fit = st["fit"] and st["lid"]
    if fit:
        # Half shut, a pupil the lid cuts in half reads as a blob at the bottom: keep it whole,
        # centred in what's open.
        top = ey - ry + st["lid"] * 2 * ry
        pr = min(pr, (ey + ry - top) * 0.42)
        py = (top + ey + ry) / 2
    if eye == "heart":
        heart(ld, px, py - pr * 0.35, pr * 1.05)
    else:
        oval(ld, px, py, pr * wf, pr, 0)
        dx, dy, r = p["hl"]
        hy = py + dy * pr
        if st["lid"] and not fit:
            hy = max(hy, ey - ry + st["lid"] * 2 * ry + r * pr + 6)
        oval(ld, px + dx * pr * wf, hy, r * pr * wf, r * pr, 255)
    img.paste(layer, mask=inner)


def solid_eye(img, p, eye, side, ex, ey, wf, hf, st):
    d = ImageDraw.Draw(img)
    w, h = p["w"] * wf * st["scale"], p["h"] * hf * st["scale"]
    ex, ey = ex + st["gx"] * 30 * wf, ey + st["gy"] * 25  # solid eyes look by moving
    if eye == "closed":
        return closed(d, ex, ey + h * 0.25, w, 16)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    if eye == "heart":
        heart(md, ex, ey - h * 0.35, w * 1.05, 255)
    elif p["shape"] == "oval":
        oval(md, ex, ey, w, h, 255)
    else:
        md.rounded_rectangle((ex - w, ey - h, ex + w, ey + h), p["shape"], fill=255)
    if eye == "happy":
        oval(md, ex, ey + h * 1.15, w * 1.4, h * 1.1, 0)
    if st["lid"] and eye == "open":
        lid_cut(mask, ex, ey - h, h, w, st["lid"], side, st["droop"])
    layer = Image.new("L", (W, H), 0)
    dx, dy, gw, gh = p["glint"]
    gxp, gyp = ex + dx * w, ey + dy * h
    if st["lid"] and eye == "open":
        gyp = max(gyp, ey - h + st["lid"] * 2 * h + gh * h + 10)
    if eye == "heart":
        gxp, gyp = ex - w * 0.5, ey - h * 0.45
    oval(ImageDraw.Draw(layer), gxp, gyp, gw * w, gh * h, 255)
    img.paste(layer, mask=mask)


def threshold(img):
    """Greys to the panel's 1 bit: partial refreshes can't show grey."""
    return img.point(lambda v: 255 if v > 127 else 0).convert("1")


def symbol_eye(d, eye, x, y, st):
    """An eye drawn as a symbol, the same in every style: an LED, lit or not, or a dazed X."""
    k = st["scale"]
    if eye == "x":
        r = 46 * k
        thick_line(d, (x - r, y - r), (x + r, y + r), 20)
        thick_line(d, (x - r, y + r), (x + r, y - r), 20)
        return
    lit = eye == "led-lit"
    w, h = 64 * k, 92 * k
    top, bottom = y - h / 2, y + h / 2
    fill = 0 if lit else 255
    d.chord((x - w, top - w * 0.2, x + w, top + w * 1.8), 180, 360, fill=fill, outline=0, width=14)
    d.rectangle((x - w, top + w * 0.8, x + w, bottom), fill=fill, outline=0, width=14)
    d.rectangle((x - w - 12, bottom - 4, x + w + 12, bottom + 14), fill=0)
    # Its legs, the anode's the longer.
    thick_line(d, (x - w * 0.4, bottom), (x - w * 0.4, bottom + 70), 10)
    thick_line(d, (x + w * 0.4, bottom), (x + w * 0.4, bottom + 50), 10)
    if lit:
        oval(d, x - w * 0.45, top + w * 0.6, 12, 18, 255)
        cy, r = top + w * 0.8, w + 26
        for a in (-160, -125, -55, -20, 0, 180):  # it shines
            c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
            thick_line(d, (x + c * r, cy + s * r), (x + c * (r + 34), cy + s * (r + 34)), 11)


SYMBOLS = ("led", "led-lit", "x")


def _head(p, st):
    """The eyes' separation, and the face's centre, before the tilt and zoom."""
    sep = p["sep"] * (1 - 0.2 * abs(st["yaw"]))
    return sep, st["fx"] + st["yaw"] * 45, st["fy"] + st["pitch"] * 35


def eye_centres(p, st):
    """Where face() puts the two eyes' centres on the panel, after the tilt and zoom."""
    sep, ox, oy = _head(p, st)
    a, z = math.radians(st["roll"]), st["zoom"]
    centres = []
    for side in (-1, 1):
        dx, dy = ox + side * sep - st["fx"], oy - st["fy"]
        # As Image.rotate turns it: anticlockwise on the panel, with y pointing down.
        dx, dy = dx * math.cos(a) + dy * math.sin(a), dy * math.cos(a) - dx * math.sin(a)
        centres.append((st["fx"] + dx * z, st["fy"] + dy * z))
    return centres


def face(p, st):
    """The face alone, in greys (anti-aliased by the tilt and zoom); threshold() it for the panel."""
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    outlined = p["kind"] == "outlined"
    yaw, pitch = st["yaw"], st["pitch"]
    sep, ox, oy = _head(p, st)
    hf = 1 - 0.12 * abs(pitch)
    eyes = st["eyes"] if isinstance(st["eyes"], tuple) else (st["eyes"],) * 2
    for side, eye in zip((-1, 1), eyes):
        # The far eye narrows as the head turns; the near one grows a little.
        wf = 1 - 0.35 * max(0, side * yaw) + 0.06 * max(0, -side * yaw)
        ex = ox + side * sep
        est = {**st, "gx": st["gx"] - side * st["cross"]}
        if eye in SYMBOLS:
            symbol_eye(d, eye, ex, oy, st)
        else:
            (outlined_eye if outlined else solid_eye)(img, p, eye, side, ex, oy, wf, hf, est)
        top = oy - p["ry" if outlined else "h"] * hf * st["scale"] - p["gap"]
        lift = st["lift"] + (st["lift_r"] if side > 0 else 0)
        inner = st["btilt"] + (0 if outlined else 4 * st["arch"])
        brow(d, ex, top - lift, p["bh"] * wf, -side * inner, p["bw"], arch=p["arch"] * st["arch"])
    mouth(d, st["mouth"], ox + yaw * 15, oy + p["mouth"] * hf)
    if st["roll"]:
        img = img.rotate(st["roll"], Image.BICUBIC, center=(st["fx"], st["fy"]), fillcolor=255)
    if st["zoom"] != 1:
        z, fx, fy = st["zoom"], st["fx"], st["fy"]
        img = img.transform(
            (W, H),
            Image.AFFINE,
            (1 / z, 0, fx - fx / z, 0, 1 / z, fy - fy / z),
            Image.BICUBIC,
            fillcolor=255,
        )
    return img
