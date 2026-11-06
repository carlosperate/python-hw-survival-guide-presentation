# The slides' animations: each plays once when its slide sends "slide <name>", never in the idle
# rotation. A step is (pose, ms), or (card, ms) for a picture in no style (cards.py). Designed in
# ../prototypes/ (rounds 30 to 34). Run it to preview them as GIFs.
import sys

import idle
from face import pose
from idle import FRAME, HAPPY

TOP = dict(fy=165, zoom=0.82)  # the face up and smaller, leaving the bottom for a prop
END = [(pose(eyes="closed", mouth="smile"), FRAME), (pose(), 1200)]


def leds():  # "Look who's talking": LEDs for eyes
    at = dict(fy=215, zoom=1.0)
    blinks = [(pose(**at, eyes="led-lit" if k % 2 else "led"), 700) for k in range(1, 5)]
    return [
        (pose(), 1200),
        (pose(eyes="closed"), FRAME),
        (pose(**at, eyes="led"), 900),
        *blinks,
        (pose(**at, eyes="led-lit", mouth="smile"), 1200),
        (pose(eyes=("open", "closed"), mouth="smile", lift_r=10), 1200),
        (pose(), 1200),
    ]


def card(name, ms):  # the owl and 640K: a picture, then the character again
    return [(pose(), 1200), (name, ms), (pose(eyes="closed"), FRAME), (pose(), 1200)]


def box():  # "Same language we love, just with tighter constraints": it fits, it sits
    small, inside, b = dict(fy=150, zoom=0.7), dict(fy=322, zoom=0.5), (("box",),)
    return [
        (pose(), 1200),
        (pose(**small, gy=0.9, lift=8, props=b), 1200),
        (pose(**small, gy=0.9, lift=16, scale=1.08, mouth="small-o", props=b), 900),
        (pose(fy=250, zoom=0.62, eyes="closed", roll=6, props=b), FRAME),
        (pose(**inside, eyes="happy", lift=6, props=b), 1200),
        (pose(**inside, gx=-0.5, props=b), 900),
        (pose(**inside, eyes="happy", lift=8, props=(("box",), ("hearts", 2))), 1800),
        *END,
    ]


def out_of_ram():  # running out of RAM: it swells as it fills, pops, and comes back dazed
    return [
        (pose(), 1200),
        (pose(zoom=1.32, scale=1.04, mouth="small-o", lift=8), 700),
        (pose(zoom=1.48, scale=1.08, lid=0.15, btilt=-8, mouth="o"), 700),
        (pose(zoom=1.66, scale=1.12, lid=0.35, btilt=-14, mouth="o", fy=236), 900),
        ("pop", FRAME),
        (pose(fy=280, zoom=0.78, eyes="x", mouth="o", roll=8, props=(("daze",),)), 1800),
        (pose(fy=250, zoom=1.0, eyes="closed", roll=-6), FRAME),
        (pose(), 1200),
    ]


def heap():  # fragmentation: a big block finds no gap; then big first, and it fits
    gaps = (1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0)

    def at(cells, *big, also=(), **kw):
        return pose(**TOP, **kw, props=(("heap", cells, *big),) + also)

    return [
        (at(gaps), 1200),
        (at(gaps, 3, 60, gx=-0.6, gy=0.8), 900),
        (at(gaps, 3, 284, gy=0.8, btilt=-8, lid=0.2), 900),
        (at(gaps, 3, 508, gx=0.6, gy=0.8, btilt=-10, lid=0.25, mouth="flat"), 900),
        (at(gaps, also=(("question",),), gy=0.3, btilt=-12, lid=0.3, mouth="flat"), 1500),
        (at((0,) * 12, eyes="closed"), FRAME),
        (at((1, 1, 1) + (0,) * 9, gx=-0.6, gy=0.8, lift=12), 900),
        (at((1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0), eyes="happy", mouth="grin", lift=10), 1500),
        *END,
    ]


def viper():  # the viper row: a slow python, then a fast one
    fast = dict(scale=1.1, pupil=0.7, lift=26, mouth="o")
    return [
        (pose(**TOP), 1200),
        (pose(**TOP, gx=-0.8, gy=0.8, props=(("snake", 90),)), 900),
        (
            pose(**TOP, gx=-0.6, gy=0.8, lid=0.45, mouth="flat", arch=0, props=(("snake", 150),)),
            900,
        ),
        (pose(**TOP, gx=-0.4, gy=0.8, lid=0.55, mouth="o", arch=0, props=(("snake", 200),)), 900),
        (
            pose(
                **TOP,
                **dict(fast, scale=1.12, lift=30),
                gx=0.9,
                gy=0.5,
                roll=-6,
                props=(("snake", 560, 4),),
            ),
            FRAME,
        ),
        (pose(**TOP, **fast, gx=0.9, gy=0.2, roll=-8), FRAME),
        (pose(**TOP, **fast, gx=-0.9, gy=0.5, roll=6, props=(("snake", 160, 4, True),)), FRAME),
        (pose(eyes="happy", mouth="big-grin", lift=12, **HAPPY), 1500),
        *END,
    ]


def racer():  # the Drivers divider: an F1 car, the face in its helmet
    def driving(x0, speed, **kw):
        return pose(fx=x0 + 284, fy=292, zoom=0.2, props=(("f1", x0, speed),), **kw)

    return [
        (pose(), 1200),
        (pose(eyes="closed"), FRAME),
        (driving(-330, 3, gx=0.9), 700),
        (driving(90, 3, gx=0.6), 700),
        (driving(90, 0, gx=-0.3, gy=-0.3), 1200),
        (driving(90, 0, eyes=("open", "closed")), 900),
        (driving(560, 4, gx=0.9), FRAME),
        (
            pose(
                fx=330,
                zoom=1.0,
                gx=0.7,
                gy=-0.6,
                eyes="happy",
                mouth="big-grin",
                lift=12,
                props=(("flag",),),
            ),
            1800,
        ),
        *END,
    ]


def scan():  # "Check the ID, wake it up": pings wake a sensor, which says its ID
    at = dict(fx=300, fy=210, zoom=0.95)
    look = dict(**at, gx=0.85, gy=0.55)

    def ping(n, mood="asleep", answer=False):
        said = (("bubble", 620, 214, 190, 80, (620, 284), "0x76", 44),) if answer else ()
        return (("pings", n), ("chip", 620, 352, mood)) + said

    return [
        (pose(), 1200),
        (pose(**look, props=ping(0)), 900),
        (pose(**look, lift=6, props=ping(1)), 700),
        (pose(**look, lift=6, props=ping(2)), 700),
        (pose(**look, lift=6, mouth="small-o", props=ping(3)), 700),
        (pose(**look, lift=20, scale=1.08, mouth="o", props=ping(0, "awake", True)), 1200),
        (pose(**at, eyes="happy", mouth="grin", lift=12, props=ping(0, "happy", True)), 1800),
        *END,
    ]


def detective():  # "New sensor ready to go, but..": a lens over each eye, then the bug
    small = dict(zoom=0.95)
    low = dict(fy=150, zoom=0.85)
    hmm = dict(btilt=-10, lid=0.2, mouth="flat")
    found = (("bug", 392, 410), ("lens", 400, 410))
    return [
        (pose(), 1200),
        (pose(**small, **hmm), 900),
        (pose(**small, **hmm, gx=0.3, props=(("lens", 0),)), 1200),
        (pose(**small, **hmm, gx=-0.3, lift_r=14, props=(("lens", 1),)), 1200),
        (pose(**low, gy=0.8, btilt=-10, lid=0.2, props=found), 1200),
        (
            pose(
                **low,
                gy=0.6,
                lift=24,
                scale=1.1,
                pupil=0.75,
                mouth="o",
                props=(("bang",),) + found,
            ),
            1200,
        ),
        *END,
    ]


def hello():  # "When the board won't talk to you": zipped shut until the laptop sends ^C
    at = dict(fx=560, fy=230, zoom=0.78)

    def asks(text, w):
        return ("bubble", 200, 70, w, 100, (170, 160), text, 44)

    return [
        (pose(), 1200),
        (pose(**at, gx=-0.8, props=(("laptop", "..."), ("zip",))), 900),
        (
            pose(**at, gx=-0.8, lid=0.2, props=(("laptop", "..."), asks("hello?", 250), ("zip",))),
            900,
        ),
        (
            pose(
                **at,
                gx=0.6,
                gy=-0.6,
                btilt=-10,
                lid=0.25,
                props=(("laptop", "..."), asks("hello??", 270), ("zip",), ("sweat", 700, 120)),
            ),
            900,
        ),
        (
            pose(
                **dict(at, fx=530),
                gx=-0.8,
                scale=1.06,
                pupil=0.7,
                lift=20,
                props=(("laptop", "^C", True), ("zip",)),
            ),
            900,
        ),
        (
            pose(
                **at,
                gx=-0.8,
                lift=12,
                mouth="o",
                props=(("laptop", "^C"), ("bubble", 240, 60, 180, 90, (360, 130), ">>>", 52)),
            ),
            1200,
        ),
        (pose(eyes="happy", mouth="grin", lift=10, **HAPPY), 1500),
        *END,
    ]


def xray():  # the Tooling divider: it can't see the wire, then sees its bits through glasses
    top = dict(fy=170, zoom=0.82)

    def seen(phase, **kw):
        return pose(**top, **kw, props=(("wire", phase), ("specs",)))

    return [
        (pose(**top, props=(("wire",),)), 1200),
        (pose(**top, gy=0.8, lid=0.4, btilt=-10, mouth="flat", props=(("wire",),)), 1200),
        (pose(**top, gy=-0.6, lift=10, props=(("wire",), ("specs",))), FRAME),
        (seen(0, gy=0.8, lift=20, scale=1.1, mouth="o"), 900),
        (seen(1, gx=-0.3, gy=0.8, lift=14), 700),
        (seen(2, gx=0.3, gy=0.8, lift=14), 700),
        (seen(3, eyes="happy", mouth="grin", lift=10), 1500),
        *END,
    ]


def beep():  # the multimeter: its continuity beep makes it jump; the second time it's ready
    top = dict(fy=170, zoom=0.86)
    jump = pose(
        fy=140, zoom=0.92, scale=1.15, pupil=0.6, lift=30, mouth="o", props=(("probes", 0, True),)
    )
    return [
        (pose(**top), 1200),
        (pose(**top, gy=0.85, lift=6, props=(("probes", 320),)), 900),
        (pose(**top, gy=0.85, lift=10, mouth="small-o", props=(("probes", 90),)), 900),
        (jump, FRAME),
        (pose(**top, gy=0.6, lid=0.25, btilt=-8, mouth="flat", props=(("probes", 260),)), 1200),
        (pose(**top, eyes="closed", btilt=-12, mouth="flat", props=(("probes", 60),)), 900),
        (pose(**top, eyes="happy", mouth="grin", lift=8, props=(("probes", 0, True),)), 1200),
        *END,
    ]


def ack():  # the logic analyser: it follows the bits going by until the sensor's ACK
    top = dict(fy=160, zoom=0.82)
    gazes = [(-0.7, 0), (-0.3, 0), (0.1, 6), (0.5, 6)]
    return [
        (pose(**top, props=(("analyser", 0),)), 1200),
        *[
            (pose(**top, gx=gx, gy=0.8, lift=lift, props=(("analyser", k + 1),)), 700)
            for k, (gx, lift) in enumerate(gazes)
        ],
        (
            pose(
                **top,
                gx=0.8,
                gy=0.4,
                lift=20,
                scale=1.08,
                mouth="o",
                props=(("analyser", 5, True),),
            ),
            900,
        ),
        (pose(**top, eyes="happy", mouth="grin", lift=10, props=(("analyser", 5, True),)), 1500),
        *END,
    ]


def thanks():  # "Thank you": a happy bow, heart eyes and hearts
    love = dict(eyes="heart", mouth="big-grin", lift=14, **HAPPY)
    return [
        (pose(), 1200),
        (pose(eyes="happy", mouth="smile", lift=8), 900),
        (pose(pitch=0.5, fy=255, zoom=1.15, eyes="closed", mouth="smile"), 1200),
        (pose(**love, props=(("hearts", 1),)), 900),
        (pose(**love, props=(("hearts", 3),)), 1500),
        (pose(eyes="happy", mouth="big-smile", **HAPPY), 1200),
        *END,
    ]


# By name, as "slide <name>" asks for it, in the deck's order.
SLIDES = {
    "leds": leds(),
    "owl": card("owl", 5000),
    "640k": card("640k", 4500),
    "box": box(),
    "out-of-ram": out_of_ram(),
    "heap": heap(),
    "viper": viper(),
    "f1": racer(),
    "scan": scan(),
    "bug": detective(),
    "hello": hello(),
    "specs": xray(),
    "beep": beep(),
    "ack": ack(),
    "thanks": thanks(),
}


def main(out=idle.PREVIEWS):
    idle.previews(out, {"slide-" + name: steps for name, steps in SLIDES.items()})


if __name__ == "__main__":
    main(*sys.argv[1:])
