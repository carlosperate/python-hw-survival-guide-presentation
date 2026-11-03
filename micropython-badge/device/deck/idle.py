# The character between the deck's triggers, as the player's background: rests, random blinks
# and behaviours, or the badge in four greys. A frame has the same number in every style, so a
# style switch keeps the place. As a scene too, it plays a named animation for a trigger: the same
# scene, so with no full refresh.
import json
import random
import time

from deck.anim import CHUNK_MS, Keyframes, Scene
from deck.frames import Frames, Grey

SETTLE_MS = 30  # longer than a contact bounces: a press needs the pin released this long first
REST_MS = 8000  # between two animations: a blink starts about every 10 s
EVERY = 3  # every third animation is a behaviour, about every 30 s
BOOT_MS = 2000
CARDS = ("boot",)  # cards.frm's frames, in order
BADGE = (None, "badge")  # the badge's pose, in no style: switching style leaves it as it is
TRIGGERS = {"blink": "blinks", "idle": "behaviours"}  # a trigger's first word: its group


class Idle(Scene):
    name = "idle"

    def __init__(self, table, frames, cards, boot=False, rest_ms=REST_MS, rand=None, badge=None):
        """table: export.py's idle.json, loaded. frames: a Frames per style, in table's order.
        boot: show the power symbol first, once. badge: a Grey (deck.frames), or None for none."""
        self.rest = table["rest"]
        self.groups = {
            group: {name: self.trimmed(steps) for name, steps in table[group].items()}
            for group in TRIGGERS.values()
        }
        self.behaviours = list(self.groups["behaviours"].values())
        self.blinks = list(self.groups["blinks"].values())
        self.styles = table["styles"]
        self.frames = frames
        self.cards = cards
        self.boot = boot
        self.rest_ms = rest_ms
        self.rand = rand or random.randrange
        self.style = 0
        self.badge = False
        self.badge_grey = badge

    @classmethod
    def load(cls, folder="/idle", boot=False):
        with open(folder + "/idle.json") as f:
            table = json.load(f)
        frames = [Frames("%s/%s.frm" % (folder, s)) for s in table["styles"]]
        return cls(table, frames, Frames(folder + "/cards.frm"), boot, badge=grey_badge(folder))

    def next_style(self):
        self.style = (self.style + 1) % len(self.styles)

    def toggle_badge(self):
        # Never on without a badge to show: holding the glass would only block the triggers.
        if self.badge:
            self.badge = False
        elif self.badge_grey is None:
            print("deck.idle: no badge to show")
        elif not self.greys:
            print("deck.idle: no badge: the display has no grey refresh")
        else:
            self.badge = True

    @property
    def holds(self):
        return self.badge  # triggers are ignored while the badge shows

    # Inflated anew each time: the player asks once a showing, and drops it once it's sent.
    def grey(self, step, pose):
        if pose != BADGE or self.badge_grey is None:
            return None
        return self.badge_grey.frame()

    def grey_failed(self, error):
        # Off for this press, the badge kept: Up tries again, but nothing retries on its own.
        self.badge = False

    def draw(self, display, step, pose):
        style, frame = pose
        if frame in CARDS:
            self.cards.unpack(CARDS.index(frame), display.buffer)
        else:
            self.frames[style].unpack(frame, display.buffer)

    def named(self, word, name):
        """The step for the trigger b"<word> <name>"; KeyError if there's no such animation."""
        group = TRIGGERS[word]
        self.groups[group][name]
        return group, name

    def keyframes(self, step):
        """0 as the background; (group, name) from named() for that animation once."""
        if step:
            group, name = step
            return Keyframes(self.play(self.groups[group][name]))
        return Keyframes(self.forever())

    def forever(self):
        """((style, frame), ms) pairs, never ending: the style is part of what a pose shows."""
        if self.boot:
            self.boot = False
            yield from self.play([("boot", BOOT_MS)])
        n = 0
        while True:
            if self.badge:
                yield BADGE, CHUNK_MS
                continue
            yield from self.play([(self.rest, self.rest_ms)])
            n += 1
            group = self.behaviours if n % EVERY == 0 else self.blinks
            yield from self.play(group[self.rand(len(group))])

    def play(self, steps):
        # In chunks, cut short when the badge goes on.
        for frame, ms in steps:
            while ms > 0 and not self.badge:
                yield (self.style, frame), min(ms, CHUNK_MS)
                ms -= CHUNK_MS

    def trimmed(self, steps):
        # An animation starts and ends on the rest pose. Without it, the rest between animations
        # stands for it, and a trigger shows at once.
        start, end = 0, len(steps)
        while start < end and steps[start][0] == self.rest:
            start += 1
        while end > start and steps[end - 1][0] == self.rest:
            end -= 1
        return steps[start:end]

    def watch(self, up, down):
        """Up switches the badge on and off, down steps through the styles (pins, active low)."""
        for pin, action in ((up, self.toggle_badge), (down, self.next_style)):
            pin.init(pin.IN, pin.PULL_UP)
            last = [1, time.ticks_add(time.ticks_ms(), -SETTLE_MS)]  # the level seen, and since
            pin.irq(
                handler=lambda p, a=action, s=last: _edge(p, a, s),
                trigger=pin.IRQ_FALLING | pin.IRQ_RISING,
            )


def _edge(pin, action, last):
    # Contacts bounce on press and on release: only a fall after a settled release is a press.
    level, now = pin.value(), time.ticks_ms()
    if level != last[0]:
        if level == 0 and time.ticks_diff(now, last[1]) >= SETTLE_MS:
            action()
        last[0], last[1] = level, now


def grey_badge(folder):
    """badge.gs2 from folder, or None if it's missing or damaged: the character runs either way.
    Whether the display can show it is the player's to find out."""
    try:
        return Grey(folder + "/badge.gs2")
    except Exception as e:
        print("deck.idle: no badge from", folder, repr(e))
        return None


def character(folder="/idle", boot=False):
    """The Idle from folder, or None when its frames are missing or damaged (an interrupted copy):
    the triggers still play without it."""
    try:
        return Idle.load(folder, boot)
    except Exception as e:
        print("deck.idle: no character from", folder, repr(e))
        return None
