import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/device")
import json
import os
import struct
import time
import unittest

from deck.idle import BADGE, BOOT_MS, CHUNK_MS, Idle, character

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
    # Frames 6 and 7 only the slides use; a card is named, as cards.frm holds it.
    "slides": {
        "pop": [[REST, 1200], [6, 700], ["pop", 600], [7, 900], [REST, 1200]],
        "photo": [[REST, 1200], ["640k", 4500], [1, 600], [REST, 1200]],
    },
    "cards": ["boot", "640k", "owl", "pop"],  # cards.frm's order
}
CARDS = 9


class Badge:
    """Stands in for deck.frames.Grey, counting how often it's inflated."""

    def __init__(self):
        self.inflated = 0

    def frame(self):
        self.inflated += 1
        return bytearray(96000)


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


def idle(rand=lambda n: 0, boot=False, badge=True):
    badge = Badge() if badge is True else badge
    return Idle(TABLE, [Frames(i) for i in range(3)], Frames(CARDS), boot, rand=rand, badge=badge)


def holds(steps):
    """The chunks merged back into holds, by frame: the style stays 0 unless a test changes it."""
    out = []
    for (_, frame), ms in steps:
        if out and out[-1][0] == frame:
            out[-1][1] += ms
        else:
            out.append([frame, ms])
    return out


EMPTY = b"FRM1" + struct.pack("<HI", 0, 10)  # a pack of no frames


def folder(path, pack=EMPTY, **table):
    """path, made if need be, with TABLE (one style, changed by table) as idle.json and pack as
    both a.frm and cards.frm."""
    try:
        os.mkdir(path)
    except OSError:
        pass
    with open(path + "/idle.json", "w") as f:
        json.dump(dict(TABLE, styles=["a"], **table), f)
    for name in ("a.frm", "cards.frm"):
        with open(path + "/" + name, "wb") as f:
            f.write(pack)
    return path


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
        self.assertEqual(first(gen, 3), [(BADGE, CHUNK_MS)] * 3)
        scene.toggle_badge()
        # Back to the rest pose, in full, then the next animation.
        self.assertEqual(holds(first(gen, 40))[:2], [[REST, 8000], [1, 600]])

    def test_a_named_animation_is_a_step(self):
        scene = idle()
        self.assertEqual(scene.named("blink", "double"), ("blinks", "double"))
        self.assertEqual(scene.named("idle", "nod"), ("behaviours", "nod"))
        self.assertEqual(scene.named("slide", "pop"), ("slides", "pop"))
        for word, name in (
            ("blink", "nod"),
            ("idle", "plain"),
            ("wink", "plain"),
            ("slide", "nod"),
        ):
            with self.assertRaises(KeyError):
                scene.named(word, name)

    # Only from their slides: the rotation never picks one.
    def test_slides_never_play_in_the_rotation(self):
        shown = {frame for (_, frame), _ in first(idle().forever(), 4000)}
        self.assertEqual(shown & {6, 7, "pop", "640k"}, set())

    def test_a_slide_animation_plays_once_cards_and_all(self):
        steps = list(idle().keyframes(("slides", "pop")).poses)
        self.assertEqual(holds(steps), [[6, 700], ["pop", 600], [7, 900]])
        steps = list(idle().keyframes(("slides", "photo")).poses)
        self.assertEqual(holds(steps), [["640k", 4500], [1, 600]])

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
        scene.draw(display, 0, (2, "boot"))
        self.assertEqual(bytes(display.buffer), bytes([CARDS, 0]))
        scene.draw(display, 0, (2, "pop"))
        self.assertEqual(bytes(display.buffer), bytes([CARDS, 3]))

    # The badge is the one grey frame, in no style: a style switch doesn't change its pose.
    def test_the_badge_is_grey_in_every_style(self):
        scene = idle()
        self.assertEqual(len(scene.grey(0, BADGE)), 96000)
        self.assertIsNone(scene.grey(0, (0, REST)))
        scene.toggle_badge()
        gen = scene.forever()
        self.assertEqual(next(gen), (BADGE, CHUNK_MS))
        scene.next_style()
        self.assertEqual(next(gen), (BADGE, CHUNK_MS))

    # Holding the glass with nothing to show would only block the triggers.
    def test_no_badge_means_up_does_nothing(self):
        scene = idle(badge=None)
        scene.toggle_badge()
        self.assertFalse(scene.badge)
        self.assertFalse(scene.holds)
        self.assertEqual(next(scene.forever()), ((0, REST), CHUNK_MS))

    # On a display without greys (older firmware), Up changes nothing at all.
    def test_no_greys_means_up_does_nothing(self):
        scene = idle()
        scene.greys = False
        scene.toggle_badge()
        self.assertFalse(scene.holds)
        self.assertEqual(scene.badge_grey.inflated, 0)

    # Inflated each time it's asked for and never kept: the player asks once a showing.
    def test_the_badge_is_inflated_when_asked(self):
        scene = idle()
        scene.toggle_badge()
        self.assertIsNot(scene.grey(0, BADGE), scene.grey(0, BADGE))
        self.assertEqual(scene.badge_grey.inflated, 2)

    # Off for this press only: one busy timeout mustn't lose the badge until a reset.
    def test_a_failed_badge_goes_off_until_up(self):
        scene = idle()
        scene.toggle_badge()
        scene.grey(0, BADGE)
        scene.grey_failed(OSError("busy timeout"))
        self.assertFalse(scene.holds)
        scene.toggle_badge()
        self.assertTrue(scene.holds)
        self.assertEqual(len(scene.grey(0, BADGE)), 96000)

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
        path = folder("/tmp/idle-test", pack=b"FRM")
        self.assertIsNone(character(path + "/none"))
        self.assertIsNone(character(path))
        with open(path + "/idle.json", "w") as f:
            f.write('{"styles": ["a"')
        self.assertIsNone(character(path))

    # A cards.frm that doesn't match idle.json (half a copy) is refused at load, not mid-slide.
    def test_too_few_cards_mean_no_character(self):
        self.assertIsNone(character(folder("/tmp/idle-cards-test")))  # four named, none packed

    # Without its badge, or with a damaged one, the character still runs: Up does nothing.
    def test_missing_or_damaged_badge_means_no_badge(self):
        path = folder("/tmp/idle-badge-test", cards=[])
        try:
            os.remove(path + "/badge.gs2")
        except OSError:
            pass
        self.assertIsNone(character(path).badge_grey)
        with open(path + "/badge.gs2", "wb") as f:
            f.write(b"GRY1")
        self.assertIsNone(character(path).badge_grey)
        with open(__file__.rsplit("/", 3)[0] + "/device/idle/badge.gs2", "rb") as f:
            exported = f.read()
        with open(path + "/badge.gs2", "wb") as f:
            f.write(exported)
        self.assertEqual(len(character(path).grey(0, BADGE)), 96000)


if __name__ == "__main__":
    unittest.main()
