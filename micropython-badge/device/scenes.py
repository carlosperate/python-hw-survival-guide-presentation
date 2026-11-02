# The deck's triggers other than the character, the link's icon, and parse(), which turns a line
# from the deck (triggers.json) into a scene and its step. The scenes are placeholders for now,
# rough on purpose: numbered cards, eyes, an LED, a heap strip and title cards. Sizes follow the
# research's e-paper guidance: shapes at least 30 px, flat black on white.
import asyncio

import framebuf
from deck.anim import Keyframes, Scene
from deck.idle import TRIGGERS
from sticky.display import HEIGHT as H
from sticky.display import WIDTH as W


def big_text(display, text, x, y, scale, c=0):
    """The built-in 8 px font, scaled up."""
    small = framebuf.FrameBuffer(bytearray(len(text) * 8), len(text) * 8, 8, framebuf.MONO_HLSB)
    small.fill(1)
    small.text(text, 0, 0, 0)
    for gy in range(8):
        for gx in range(len(text) * 8):
            if not small.pixel(gx, gy):
                display.fill_rect(x + gx * scale, y + gy * scale, scale, scale, c)


def centred_text(display, text, y, scale, c=0):
    big_text(display, text, (W - len(text) * 8 * scale) // 2, y, scale, c)


def ring(display, x, y, rx, ry, width):
    display.ellipse(x, y, rx, ry, 0, True)
    display.ellipse(x, y, rx - width, ry - width, 1, True)


class Eyes(Scene):
    name = "eyes"
    # Steps: 0 centre, 1 left, 2 right, 3 up, 4 surprised, 5 sleepy, 6 looking around.
    LOOK = {0: (0, 0), 1: (-40, 0), 2: (40, 0), 3: (0, -45), 4: (0, 0), 5: (0, 25)}
    blink = Keyframes([("open", 2500), ("shut", 250), ("open", 1000)])
    around = Keyframes([(0, 900), (1, 900), (0, 900), (2, 900), (3, 900)])

    def keyframes(self, step):
        return self.around if step == 6 else self.blink

    def draw(self, display, step, pose):
        display.fill(1)
        look = step if step != 6 else pose
        dx, dy = self.LOOK.get(look, (0, 0))
        surprised = step == 4
        rx, ry = (130, 150) if surprised else (110, 125)
        for x in (W // 2 - 170, W // 2 + 170):
            y = H // 2
            if pose == "shut":
                display.fill_rect(x - rx, y - 15, 2 * rx, 30, 0)
                continue
            ring(display, x, y, rx, ry, 14)
            pupil = 30 if surprised else 48
            display.ellipse(x + dx, y + dy, pupil, pupil, 0, True)
            if step == 5:  # sleepy: the upper lid half closed
                display.fill_rect(x - rx, y - ry, 2 * rx, ry - 10, 0)


class Led(Scene):
    name = "led"
    # Steps: 0 off, 1 on, 2 blinking once a second.
    blinking = Keyframes([(1, 1000), (0, 1000)] * 3)

    def keyframes(self, step):
        return self.blinking if step == 2 else None

    def draw(self, display, step, pose):
        on = pose if step == 2 else step == 1
        display.fill(1)
        big_text(display, "Pin(25)", 40, 40, 5)
        big_text(display, "ON" if on else "OFF", 40, 380, 6)
        x, y, r = 580, 260, 130
        if on:
            display.ellipse(x, y, r, r, 0, True)
            # Rays: right, left, below, above.
            display.fill_rect(x + r + 20, y - 15, 40, 30, 0)
            display.fill_rect(x - r - 60, y - 15, 40, 30, 0)
            display.fill_rect(x - 15, y + r + 20, 30, 40, 0)
            display.fill_rect(x - 15, y - r - 60, 30, 40, 0)
        else:
            ring(display, x, y, r, r, 16)


class Heap(Scene):
    name = "heap"
    # Step n: n of 12 blocks used. Each step only darkens new blocks, so partials stay clean.
    BLOCKS = 12

    def draw(self, display, step, pose):
        display.fill(1)
        centred_text(display, "heap", 60, 8)
        x0, y0, size, gap = 40, 260, 50, 10
        for i in range(self.BLOCKS):
            x = x0 + i * (size + gap)
            if i < step:
                display.fill_rect(x, y0, size, 120, 0)
            else:
                display.rect(x, y0, size, 120, 0)
                display.rect(x + 1, y0 + 1, size - 2, 118, 0)
        big_text(display, "%d/%d" % (min(step, self.BLOCKS), self.BLOCKS), 40, 410, 4)


class Title(Scene):
    name = "title"
    CARDS = [
        ("PYTHON", "on hardware"),
        ("DRIVERS", "find, read, fix"),
        ("DEBUG", "make time visible"),
    ]

    def draw(self, display, step, pose):
        big, small = self.CARDS[step % len(self.CARDS)]
        display.fill(1)
        display.fill_rect(0, 0, W, 24, 0)
        display.fill_rect(0, H - 24, W, 24, 0)
        centred_text(display, big, 150, 14)
        centred_text(display, small, 320, 4)


class Trigger(Scene):
    name = "trigger"
    # Step n: a placeholder for an animation: n, and a bar filling, then the picture inverted.
    frames = Keyframes([(k, 600) for k in range(5)])

    def keyframes(self, step):
        return self.frames

    def draw(self, display, step, k):
        ink = 1 if k == 4 else 0
        display.fill(1 - ink)
        centred_text(display, "TRIGGER", 30, 4, ink)
        centred_text(display, str(step), 110, 18, ink)
        display.rect(40, 390, W - 80, 50, ink)
        display.fill_rect(40, 390, (W - 80) * min(k + 1, 4) // 4, 50, ink)


def thick_line(display, x0, y0, x1, y1, w):
    for d in range(-(w // 2), w - w // 2):
        display.line(x0 + d, y0, x1 + d, y1, 0)


# Nothing while the deck is connected; while it isn't, the Bluetooth rune crossed out, in the
# corner every idle frame leaves blank.
def link_icon(display, link):
    if link.connected:
        return
    x, y, h = W - 36, H - 38, 46
    top, bottom, side, quarter = y - h // 2, y + h // 2, h * 27 // 100, h // 4
    thick_line(display, x, top, x, bottom, 5)
    thick_line(display, x - side, y + quarter, x + side, y - quarter, 5)
    thick_line(display, x + side, y - quarter, x, top, 5)
    thick_line(display, x - side, y - quarter, x + side, y + quarter, 5)
    thick_line(display, x + side, y + quarter, x, bottom, 5)
    thick_line(display, x - 22, y - 26, x + 22, y + 26, 6)


SKIPPED_MS = 1000


def skipped(display=None):
    """Up held at boot: one line for a second, then a blank panel. The old picture could pass for
    a programme that hung, and a reset mid-refresh leaves stripes. Fails quietly: the REPL is free.
    """
    try:
        if display is None:
            import reterminal_sticky
            from sticky.display import Display

            display = Display(reterminal_sticky.panel())
        asyncio.run(_skipped(display))
    except Exception as e:
        print("main: couldn't clear the glass", repr(e))


async def _skipped(display):
    display.fill(1)
    big_text(display, "Up held at start: programme skipped", 24, H - 48, 2)
    await display.show(True)
    await display.wait()
    await asyncio.sleep_ms(SKIPPED_MS)
    display.fill(1)
    await display.show(True)
    await display.power_off()


SCENES = [Eyes(), Led(), Heap(), Title(), Trigger()]


def parse(state, idle=None):
    """b"<scene> <step>" as (scene, step), as b"trigger 7"; b"blink <name>" and b"idle <name>" as
    the character's scene and one of its animations. idle: the Idle, None without its frames."""
    word, _, step = state.decode().partition(" ")
    if word in TRIGGERS:
        if not idle:
            raise ValueError("no idle frames")
        return idle.name, idle.named(word, step)
    return word, int(step or 0)
