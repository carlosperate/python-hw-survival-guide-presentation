import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/device")
import json
import os
import time
import unittest

from deck.idle import BOOT_MS, CHUNK_MS, Idle, character

REST = 0
TABLE = {
    "styles": ["a", "b", "c"],
    "rest": REST,
    "behaviours": {
        "look": [[REST, 1800], [2, 600], [3, 1800], [REST, 1200]],
        "nod": [[REST, 1800], [4, 900], [REST, 900], [5, 700], [REST, 1200]],
    },
    "blinks": {
        "plain": [[REST, 1200], [1, 600], [REST, 1200]],
        "double": [[REST, 1200], [1, 600], [REST, 600], [1, 600], [REST, 1200]],
    },
}
CARDS = 9


class Frames:
    """Fills the buffer with the pack's and the frame's numbers."""

    def __init__(self, pack):
        self.pack = pack

    def unpack(self, i, buffer):
        buffer[0], buffer[1] = self.pack, i


class Display:
    buffer = bytearray(2)


class Pin:
    IN, PULL_UP, IRQ_FALLING, IRQ_RISING = 1, 2, 4, 8
    level = 1

    def init(self, mode, pull):
        self.mode, self.pull = mode, pull

    def irq(self, handler, trigger):
        self.handler, self.trigger = handler, trigger

    def value(self):
        return self.level

    def set(self, *levels):
        """Edges, each seen by the handler."""
        for self.level in levels:
            self.handler(self)


def idle(rand=lambda n: 0, boot=False):
    return Idle(TABLE, [Frames(i) for i in range(3)], Frames(CARDS), boot, rand=rand)


def holds(steps):
    """The chunks merged back into holds, by frame: the style stays 0 unless a test changes it."""
    out = []
    for (_, frame), ms in steps:
        if out and out[-1][0] == frame:
            out[-1][1] += ms
        else:
            out.append([frame, ms])
    return out


def first(gen, n):
    return [next(gen) for _ in range(n)]


class TestIdle(unittest.TestCase):
    def test_trimmed_drops_the_rest_pose_at_both_ends(self):
        scene = idle()
        self.assertEqual(scene.trimmed(TABLE["blinks"]["plain"]), [[1, 600]])
        self.assertEqual(
            scene.trimmed(TABLE["behaviours"]["nod"]), [[4, 900], [REST, 900], [5, 700]]
        )

    def test_two_blinks_then_a_behaviour_with_rests_between(self):
        steps = first(idle().forever(), 600)
        self.assertTrue(all(ms <= CHUNK_MS for _, ms in steps))
        # Split at the 8 s rests: the blinks show frame 1 only, the behaviours frames 2 to 5.
        animations, current = [], []
        for frame, ms in holds(steps)[:-1]:
            if [frame, ms] == [REST, 8000]:
                if current:
                    animations.append(current)
                current = []
            else:
                current.append(frame)
        self.assertEqual(holds(steps)[0], [REST, 8000])
        kinds = ["blink" if set(a) <= {REST, 1} else "behaviour" for a in animations]
        self.assertEqual(kinds[:6], ["blink", "blink", "behaviour"] * 2)

    def test_each_pick_is_random(self):
        picks = []

        def rand(n):
            picks.append(n)
            return n - 1

        scene = idle(rand)
        steps = first(scene.forever(), 400)
        self.assertEqual(picks[:3], [2, 2, 2])
        # The last of each group, in whatever order the table's dict keeps them.
        blink = scene.trimmed(scene.blinks[1])
        self.assertEqual(holds(steps[8000 // CHUNK_MS :])[: len(blink)], blink)

    def test_boot_shows_the_power_symbol_once(self):
        scene = idle(boot=True)
        self.assertEqual(holds(first(scene.forever(), 40))[:2], [["boot", BOOT_MS], [REST, 8000]])
        self.assertEqual(holds(first(scene.forever(), 32))[0], [REST, 8000])

    def test_badge_cuts_in_and_out(self):
        scene = idle()
        gen = scene.forever()
        first(gen, 3)
        scene.toggle_badge()
        self.assertEqual(first(gen, 3), [((0, "badge"), CHUNK_MS)] * 3)
        scene.toggle_badge()
        # Back to the rest pose, in full, then the next animation.
        self.assertEqual(holds(first(gen, 40))[:2], [[REST, 8000], [1, 600]])

    def test_a_named_animation_is_a_step(self):
        scene = idle()
        self.assertEqual(scene.named("blink", "double"), ("blinks", "double"))
        self.assertEqual(scene.named("idle", "nod"), ("behaviours", "nod"))
        for word, name in (("blink", "nod"), ("idle", "plain"), ("wink", "plain")):
            with self.assertRaises(KeyError):
                scene.named(word, name)

    def test_a_named_animation_plays_once_without_its_rests(self):
        steps = list(idle().keyframes(("blinks", "double")).poses)
        self.assertTrue(all(ms <= CHUNK_MS for _, ms in steps))
        self.assertEqual(holds(steps), [[1, 600], [REST, 600], [1, 600]])

    def test_the_badge_cuts_a_named_animation(self):
        scene = idle()
        poses = scene.keyframes(("behaviours", "look")).poses
        first(poses, 2)
        scene.toggle_badge()
        self.assertEqual(list(poses), [])

    def test_styles_wrap(self):
        scene = idle()
        for _ in range(3):
            scene.next_style()
        self.assertEqual(scene.style, 0)

    # The player redraws a held frame only when its pose changes, so the pose names the style.
    def test_a_style_switch_shows_in_the_next_chunk(self):
        scene = idle()
        gen = scene.forever()
        self.assertEqual(next(gen), ((0, REST), CHUNK_MS))
        scene.next_style()
        self.assertEqual(next(gen), ((1, REST), CHUNK_MS))

    def test_draw_uses_the_poses_style_or_the_cards(self):
        scene, display = idle(), Display()
        scene.draw(display, 0, (1, 4))
        self.assertEqual(bytes(display.buffer), bytes([1, 4]))
        scene.draw(display, 0, (2, "badge"))
        self.assertEqual(bytes(display.buffer), bytes([CARDS, 1]))

    def test_buttons_act_once_per_press(self):
        scene, up, down = idle(), Pin(), Pin()
        scene.watch(up, down)
        edges = Pin.IRQ_FALLING | Pin.IRQ_RISING
        self.assertEqual((up.mode, up.pull, up.trigger), (Pin.IN, Pin.PULL_UP, edges))
        down.set(0, 1, 0)  # a press, bouncing
        self.assertEqual(scene.style, 1)
        up.set(0)  # at once: each button on its own
        self.assertTrue(scene.badge)
        self.assertTrue(scene.holds)
        time.sleep_ms(300)  # held
        up.set(1, 0, 1)  # released, bouncing: not a press
        self.assertTrue(scene.badge)
        time.sleep_ms(50)
        up.set(0)
        self.assertFalse(scene.badge)
        self.assertEqual(scene.style, 1)

    # An interrupted copy leaves damaged frames: the triggers must still play without them.
    def test_missing_or_damaged_frames_mean_no_character(self):
        folder = "/tmp/idle-test"
        try:
            os.mkdir(folder)
        except OSError:
            pass
        self.assertIsNone(character(folder + "/none"))
        with open(folder + "/idle.json", "w") as f:
            f.write('{"styles": ["a"')
        self.assertIsNone(character(folder))
        with open(folder + "/idle.json", "w") as f:
            json.dump(dict(TABLE, styles=["a"]), f)
        for name in ("a.frm", "cards.frm"):
            with open(folder + "/" + name, "wb") as f:
                f.write(b"FRM")
        self.assertIsNone(character(folder))


if __name__ == "__main__":
    unittest.main()
