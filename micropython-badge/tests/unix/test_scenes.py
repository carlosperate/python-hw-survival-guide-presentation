import json
import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
HERE = __file__.rsplit("/", 3)[0]
sys.path.insert(0, HERE + "/device")
import unittest

from deck.idle import TRIGGERS as WORDS
from deck.idle import Idle
from scenes import SCENES, parse, skipped
from sticky.display import Display
from sticky_sim import SimPanel

WRITE = 20  # link.js writes 20 bytes at a time: a line and its newline fit one, so it isn't late

with open(HERE + "/triggers.json") as f:
    TRIGGERS = json.load(f)
with open(HERE + "/device/idle/idle.json") as f:
    TABLE = json.load(f)


class Shown(SimPanel):
    """Keeps the glass after each refresh."""

    def __init__(self):
        super().__init__()
        self.shown = []

    def show(self, frame, old=None):
        super().show(frame, old)
        self.shown.append(bytes(self.glass))


class Frames:
    def unpack(self, i, buffer):
        pass


def character():
    return Idle(TABLE, [Frames() for _ in TABLE["styles"]], Frames())


# triggers.json against the programme: every line the deck can send plays something.
class TestTriggers(unittest.TestCase):
    def test_every_presentation_trigger_draws(self):
        scenes = {scene.name: scene for scene in SCENES}
        display = Display(SimPanel())
        for line in TRIGGERS["presentation"].values():
            name, step = parse(line.encode())
            frames = scenes[name].keyframes(step)
            scenes[name].draw(display, step, frames.poses[0][0] if frames else None)

    def test_every_animation_of_the_character_and_no_other(self):
        lines = {
            line
            for group, entries in TRIGGERS.items()
            if group != "presentation"
            for line in entries.values()
        }
        names = {word + " " + name for word, group in WORDS.items() for name in TABLE[group]}
        self.assertEqual(lines, names)
        idle = character()
        for line in lines:
            self.assertEqual(parse(line.encode(), idle)[0], "idle")

    # A slide's card is found by name in the cards idle.json lists, in cards.frm's order.
    def test_every_card_a_slide_shows_is_on_the_board(self):
        named = {f for steps in TABLE["slides"].values() for f, _ in steps if isinstance(f, str)}
        self.assertLessEqual(named, set(TABLE["cards"]))

    def test_names_unique_and_each_line_fits_one_write(self):
        names = [name for group in TRIGGERS.values() for name in group]
        self.assertEqual(len(names), len(set(names)))
        for group in TRIGGERS.values():
            for line in group.values():
                self.assertTrue(len(line) + 1 <= WRITE, line)

    def test_an_unknown_animation_is_refused(self):
        with self.assertRaises(KeyError):
            parse(b"blink wink", character())
        with self.assertRaises(ValueError):
            parse(b"blink plain")  # the board has no frames


# Up held at boot: the glass says so, then is left blank with the high voltage off.
class TestSkipped(unittest.TestCase):
    def test_a_line_then_a_blank_glass(self):
        panel = Shown()
        skipped(Display(panel))
        blank = b"\xff" * len(panel.glass)
        self.assertEqual(panel.full, 2)
        self.assertNotEqual(panel.shown[0], blank)
        self.assertEqual(panel.glass, blank)
        self.assertTrue(panel.powered_off)

    # The REPL must stay free whatever happens: the unix port has no panel to make.
    def test_fails_quietly(self):
        skipped()


if __name__ == "__main__":
    unittest.main()
