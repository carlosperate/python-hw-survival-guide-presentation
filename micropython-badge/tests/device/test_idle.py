import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/device")
# The idle scene on the frame packs installed in /idle/ (character/export.py, copied as
# docs/character.md says): every pack loads and unpacks, within a bound set from the unit.
import os
import time
import unittest

from deck.idle import BADGE, CHUNK_MS, Idle
from sticky.display import HEIGHT, WIDTH


class Display:
    buffer = bytearray(WIDTH * HEIGHT // 8)


class TestIdle(unittest.TestCase):
    def setUp(self):
        try:
            os.stat("/idle/idle.json")
        except OSError:
            self.skipTest("no frame packs in /idle")
        self.scene = Idle.load()

    def test_every_style_and_card_unpacks(self):
        display = Display()
        poses = [(style, self.scene.rest) for style in range(len(self.scene.styles))]
        for pose in poses + [(0, card) for card in self.scene.card_names]:
            t = time.ticks_ms()
            self.scene.draw(display, 0, pose)
            # Measured at 17 to 36 ms a frame on the unit: well inside a 600 ms frame.
            ms = time.ticks_diff(time.ticks_ms(), t)
            self.assertTrue(ms < 100, ms)

    # badge.gs2 loads whole on this firmware, which has the grey refresh.
    def test_the_badge_holds_the_glass(self):
        self.assertEqual(len(self.scene.grey(0, BADGE)), WIDTH * HEIGHT // 4)
        self.scene.toggle_badge()
        gen = self.scene.forever()
        self.assertEqual(next(gen), (BADGE, CHUNK_MS))
        self.assertTrue(self.scene.holds)


if __name__ == "__main__":
    unittest.main()
