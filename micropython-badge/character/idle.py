# The idle behaviours: what the character does between the deck's triggers. Each is a list of
# (pose, ms), starting after and ending on the rest pose, so any can follow any other. The eyes
# lead and the head follows; a blink covers a big move; frames last at least FRAME, about one
# partial refresh on the unit. Run it to preview every behaviour as GIFs.
import os
import sys
from functools import cache

from PIL import Image

import cards
import props
from face import FX, FY, REST, STYLES, H, W, eye_centres, face, pose, threshold

FRAME = 600  # ms
PREVIEWS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "build", "previews"))

UP = dict(fy=258, zoom=1.12, pitch=-0.5, roll=8, gy=-0.85, lift=14)
CLOCK_AT = dict(fx=238, fy=272, zoom=0.92)
CLOCK = dict(**CLOCK_AT, yaw=0.35, pitch=-0.4, roll=-7, gx=0.85, gy=-0.75, lift=10)
IDEA_AT = dict(fx=270, fy=270, zoom=1.05)
ASLEEP = dict(fx=320, fy=270, zoom=1.0, roll=-11)
SLEEPY = dict(arch=0, lift=-12, btilt=0, droop=0.3, fit=True)
DOWN = dict(fy=175, zoom=1.0, pitch=0.4, gy=0.9, lid=0.25, btilt=-5)
DESK = dict(fx=575, fy=205, zoom=1.0, yaw=-0.55, pitch=0.45, roll=8, lid=0.2, btilt=-6)
NOD = dict(pitch=0.35, eyes="happy")  # agreeing
HAPPY = dict(zoom=1.1, pitch=-0.1)  # leans back a little, so the big grin and brows fit
LEFT, RIGHT = (
    dict(fx=FX + k * 60, yaw=k * 0.55, roll=-k * 3) for k in (-1, 1)
)  # following the speaker
FLY = [(-80, 160), (66, 80), (716, 88), (95, 432), (400, 95), (730, 40)]
FLY_VIA = [None, (0, 40), (400, -120), (820, 600), (0, -160), (560, -100)]  # around the face
AROUND = 1.05  # the face, a little smaller while the fly is about


def gaze_at(at, x, y):
    ox, oy = at["fx"] + at["yaw"] * 45, at["fy"] + at["pitch"] * 35
    return max(-1, min(1, (x - ox) / 260)), max(-1, min(1, (y - oy) / 170))


def notes():
    frames = [(pose(), 1800), (pose(**DESK, eyes="closed", props=(("notes", 0),)), FRAME)]
    for k in range(7):
        progress = k * 0.5
        gx, gy = gaze_at({**REST, **DESK}, *props.notebook(Image.new("L", (W, H), 255), progress))
        frames.append(
            (pose(**DESK, gx=gx, gy=gy, props=(("notes", progress),)), 1200 if k == 0 else 700)
        )
    done = (("notes", 3, True, True),)
    frames.append((pose(**{**DESK, "lid": 0}, eyes="happy", mouth="smile", props=done), 1500))
    frames.append(
        (
            pose(**{**DESK, "lid": 0, "btilt": 0}, gx=0.55, gy=-0.15, mouth="smile", props=done),
            1200,
        )
    )
    return frames + [(pose(eyes="closed"), FRAME), (pose(), 1200)]


def fly():
    def hop(k, **kw):
        return ("fly", *FLY[k], *FLY[k - 1], *FLY_VIA[k], *kw.values())

    def at(k, **kw):
        gx, gy = gaze_at(REST, *FLY[k])
        return pose(gx=gx, gy=gy, zoom=AROUND, props=(hop(k),), **kw)

    landed = pose(
        zoom=AROUND, gy=-0.8, cross=0.75, lift=14, btilt=8, mouth="small-o", props=(hop(4),)
    )
    blown = pose(
        zoom=AROUND, lid=0.35, btilt=-8, mouth="o", props=(("puff",), hop(5, upside=True))
    )
    return [
        (pose(), 1800),
        (at(1, lift=8), 900),
        (at(2), 900),
        (at(3), 900),
        (landed, 1800),
        (blown, 1200),
        (pose(zoom=AROUND, gx=0.7, gy=-0.6, mouth="smile"), 1200),
        (pose(eyes="closed", mouth="smile"), FRAME),
        (pose(), 1200),
    ]


def bored():
    frames = [
        (pose(), 1800),
        (pose(gx=-0.85), 1200),
        (pose(gx=0.85), 1200),
        (pose(gy=0.1, lid=0.3, mouth="flat", **SLEEPY), 1800),
        (pose(lid=0.5, roll=-4, fy=FY + 8, mouth="flat", **SLEEPY), 1800),
        (pose(lid=0.72, roll=-8, fy=FY + 18, **SLEEPY), 1800),
        (pose(eyes="closed", roll=-12, fy=FY + 34, **SLEEPY), FRAME),
        (pose(lid=0.12, scale=1.06, pupil=0.85, lift=12), 900),  # nodded off: jolts awake
        (pose(lid=0.62, roll=-7, fy=FY + 16, **SLEEPY), 1500),
        (pose(eyes="closed", mouth="small-o", **ASLEEP, **SLEEPY), 1500),
    ]
    for n in (1, 2, 3, 4):  # asleep, breathing, the Zs building up
        breath = {**ASLEEP, "fy": ASLEEP["fy"] + 3 * (n % 2)}
        snore = pose(
            eyes="closed", **breath, mouth="o" if n % 2 else "small-o", props=(("z", n),), **SLEEPY
        )
        frames.append((snore, 1800 if n == 4 else 1200))
    startled = pose(
        scale=1.15, pupil=0.6, lift=30, fy=256, zoom=1.08, mouth="o", props=(("bang",),)
    )
    return frames + [(startled, 1200), (pose(eyes="closed"), FRAME), (pose(), 1200)]


def phone():
    def held(scroll, **kw):
        return pose(**{**DOWN, **kw}, props=(("phone", scroll),))

    return [
        (pose(), 1800),
        (pose(fy=175, zoom=1.0, gy=0.9, props=(("phone", 0),)), FRAME),
        (held(0), 1500),
        (held(50, gx=-0.25), 1200),
        (held(92, gx=0.15, lift=6), 1200),
        (
            pose(
                **{**DOWN, "lid": 0}, eyes="heart", lift=16, props=(("phone", 92), ("hearts", 1))
            ),
            1500,
        ),
        (
            pose(
                **{**DOWN, "lid": 0, "pitch": 0.2},
                eyes="happy",
                roll=6,
                props=(("phone", 92), ("hearts", 3)),
            ),
            1500,
        ),
        (pose(fy=175, zoom=1.0, props=(("phone", 92),)), 1200),
        (pose(eyes="closed"), FRAME),
        (pose(), 1200),
    ]


BEHAVIOURS = {
    "smile": [  # brows up as if recognising someone, then a happy squint
        (pose(), 1200),
        (pose(lift=16, scale=1.06, mouth="smile"), 800),
        (pose(eyes="happy", mouth="big-grin", lift=10, **HAPPY), 1500),
        (pose(eyes="happy", mouth="big-smile", lift=4, **HAPPY), 900),
        (pose(mouth="big-smile", **HAPPY), 1200),
        (pose(), 1200),
    ],
    "look-up": [
        (pose(), 1800),
        (pose(gy=-0.85, lift=6), FRAME),
        (pose(**UP), 1800),
        (pose(**UP, eyes=("open", "happy"), mouth="smile"), 1500),
        (pose(**UP), 900),
        (pose(eyes="closed"), FRAME),
        (pose(), 1200),
    ],
    "time": [
        (pose(), 1800),
        (pose(**CLOCK_AT, gx=0.85, gy=-0.75, props=(("clock", 10, 10),)), FRAME),
        (pose(**CLOCK, props=(("clock", 10, 10),)), 1800),
        (pose(**CLOCK, lift_r=14, mouth="small-o", props=(("clock", 10, 11),)), 1500),
        (pose(**{**CLOCK, "gx": 0, "gy": 0}, mouth="smile", props=(("clock", 10, 11),)), 1200),
        (pose(eyes="closed"), FRAME),
        (pose(), 1200),
    ],
    "bored": bored(),
    "phone": phone(),
    "notes": notes(),
    "idea": [
        (pose(), 1800),
        (pose(**IDEA_AT, gx=0.75, gy=-0.75, lift=-4, lift_r=20, props=(("question",),)), 1500),
        (
            pose(
                **IDEA_AT,
                gx=0.75,
                gy=-0.75,
                roll=-6,
                lid=0.3,
                btilt=-8,
                lift_r=16,
                mouth="flat",
                props=(("question",),),
            ),
            1500,
        ),
        (
            pose(
                **IDEA_AT,
                gx=0.3,
                gy=-0.3,
                scale=1.12,
                pupil=0.85,
                lift=24,
                mouth="o",
                props=(("bulb",),),
            ),
            1200,
        ),
        (pose(**IDEA_AT, eyes="happy", lift=16, mouth="grin", props=(("bulb",),)), 1500),
        (pose(eyes="closed", mouth="smile"), FRAME),
        (pose(), 1200),
    ],
    "fly": fly(),
    "speaker": [
        (pose(), 1800),
        (pose(gx=-0.85, gy=-0.5), FRAME),
        (pose(**LEFT, gx=-0.8, gy=-0.6, lift=6), 1500),
        (pose(**RIGHT, gx=0.8, eyes="closed"), FRAME),  # turns under a blink
        (pose(**RIGHT, gx=0.85, gy=-0.6, lift=6), 1500),
    ]
    + [
        (pose(**RIGHT, gx=0.85, gy=-0.35, mouth="smile", **NOD), 900),
        (pose(**RIGHT, gx=0.85, gy=-0.6, lift=6, mouth="smile"), 700),
    ]
    * 2
    + [
        (pose(gy=-0.65, lift=12, mouth="smile"), 1500),
        (pose(eyes="closed", mouth="smile"), FRAME),
        (pose(), 1200),
    ],
}


def _blink(*before, after=()):
    # Rest, a few poses, the blink, a few more, rest: the shape every blink shares.
    shut = (pose(eyes="closed"), FRAME)
    return [(pose(), 1200), *before, shut, *after, (pose(), 1200)]


# A person blinks every few seconds: these play between the behaviours, the eyes moving a little.
GLANCE = 900
BLINKS = {
    "plain": _blink(),
    "glance-left": _blink((pose(gx=-0.4), GLANCE)),
    "glance-right": _blink((pose(gx=0.4), GLANCE)),
    "double": _blink((pose(eyes="closed"), FRAME), (pose(), FRAME)),
    "glance-up": _blink((pose(gy=-0.4, lift=6), GLANCE)),
    "glance-down": _blink((pose(gy=0.4, lid=0.15), GLANCE)),
    "slow": _blink((pose(lid=0.4, fit=True), FRAME), after=[(pose(lid=0.4, fit=True), FRAME)]),
    "then-glance": _blink(after=[(pose(gx=0.35, gy=-0.25), GLANCE)]),
    "left-right": _blink((pose(gx=-0.4), 700), after=[(pose(gx=0.4), GLANCE)]),
    "brows": _blink(after=[(pose(lift=12), 700)]),
}


@cache  # the same in every style
def card(name):
    return cards.CARDS[name]()


def render(style, st):
    """One frame for the panel, 1-bit, 800x480: a pose drawn in style, or a card by its name."""
    if isinstance(st, str):
        return card(st)
    img = face(STYLES[style], st)
    props.draw(img, st["props"], (eye_centres(STYLES[style], st), st["zoom"]))
    return threshold(img)


def previews(out, animations):
    """Each animation as a GIF per style, out/<style>-<name>.gif, at the board's timing."""
    os.makedirs(out, exist_ok=True)
    for style in STYLES:
        for name, steps in animations.items():
            images = [render(style, st) for st, _ in steps]
            images[0].save(
                os.path.join(out, "%s-%s.gif" % (style, name)),
                save_all=True,
                append_images=images[1:],
                duration=[ms for _, ms in steps],
                loop=0,
            )
    print(out)


def main(out=PREVIEWS):
    previews(out, {**BEHAVIOURS, **{"blink-" + name: steps for name, steps in BLINKS.items()}})


if __name__ == "__main__":
    main(*sys.argv[1:])
