import sys

# Run from a checkout of the port (STICKY), so the programme and the shared fakes are found from
# here.
ROOT = __file__.rsplit("/", 3)[0]
sys.path[:0] = [ROOT + "/device", ROOT + "/tests"]
import asyncio
import time
import unittest

from deck.anim import Keyframes, Player, Scene
from deck.app import run
from deck_fakes import Link, parse
from sticky.display import Display
from sticky_sim import SimPanel


class Recorded(Scene):
    """Keeps what it drew, and adds it to a log shared with the other scenes, timed."""

    def __init__(self, log=None):
        self.drawn = []
        self.log = [] if log is None else log

    def record(self, step, pose):
        self.drawn.append((step, pose) if self.name == "still" else pose)
        self.log.append((self.name, pose, time.ticks_ms()))


class Still(Recorded):
    name = "still"

    def draw(self, display, step, pose):
        self.record(step, pose)
        display.fill(1)
        display.fill_rect(10 * step, 0, 10, 10, 0)


class Blink(Recorded):
    name = "blink"

    def __init__(self, log=None):
        super().__init__(log)
        self.frames = Keyframes([("open", 30), ("shut", 30)])

    def draw(self, display, step, pose):
        self.record(step, pose)
        display.fill(1)
        display.fill_rect(0, 0, 100, 100 if pose == "open" else 10, 0)

    def keyframes(self, step):
        return self.frames


class Background(Recorded):
    name = "background"

    def keyframes(self, step):
        if step:  # one of its own animations, as a trigger
            return Keyframes([(100 + step, 30), (200 + step, 30)])

        def forever():
            n = 0
            while True:
                yield n, 20
                n += 1

        return Keyframes(forever())

    def draw(self, display, step, pose):
        self.record(step, pose)
        display.fill(1)
        display.fill_rect(200, 0, 10 + 10 * (pose % 2), 10, 0)


class Greyed(Background):
    """The background, held on a grey frame while on, as the idle scene holds its badge."""

    def __init__(self, log=None):
        super().__init__(log)
        self.on = False
        self.failed = []
        self.asked = 0
        self.frame = bytearray(b"\xaa" * 96000)

    def keyframes(self, step):
        def forever():
            n = 0
            while True:
                if self.on:
                    yield "grey", 20
                else:
                    yield n, 20
                    n += 1

        return Keyframes(forever())

    def grey(self, step, pose):
        if pose != "grey":
            return None
        self.asked += 1
        return self.frame

    def grey_failed(self, error):
        self.failed.append(error)
        self.on = False


class Broken(Scene):
    name = "broken"

    def draw(self, display, step, pose):
        raise IndexError("no such step")


class FailsLater(Blink):
    name = "fails"

    def draw(self, display, step, pose):
        if pose == "shut":
            raise ValueError("bad pose")
        super().draw(display, step, pose)


class Empty(Blink):
    name = "empty"

    def keyframes(self, step):
        return Keyframes([])


# Fixtures only: the test classes share them without running each other's tests.
class PlayerCase(unittest.TestCase):
    def setUp(self):
        self.panel = SimPanel()
        self.display = Display(self.panel, idle_ms=50)
        self.link = Link()

    # Drops the display's idle task, which would otherwise keep this test's buffers alive.
    def tearDown(self):
        asyncio.new_event_loop()

    # Sends each (state, wait_ms) in turn with the player running, then stops it. A state of None
    # only waits; a function is called instead.
    def session(self, *steps):
        async def main():
            task = asyncio.create_task(self.player.run(self.link))
            for state, wait_ms in steps:
                if callable(state):
                    state()
                elif state:
                    self.link.send(state)
                await asyncio.sleep_ms(wait_ms)
            task.cancel()
            # Cancelling run() stops its animation too, through its finally.
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(main())


class TestPlayer(PlayerCase):
    def setUp(self):
        super().setUp()
        self.log = []
        self.still = Still(self.log)
        self.blink = Blink(self.log)
        self.background = Background(self.log)
        self.player = self.make()

    def make(self, **kw):
        scenes = [self.still, self.blink, Broken(), Empty(), FailsLater()]
        return Player(self.display, scenes, parse, still_ms=50, **kw)

    def counts(self):
        return self.panel.full, self.panel.partial

    def names(self):
        # The log's scene names, each run of one scene once.
        out = []
        for name, _, _ in self.log:
            if not out or out[-1] != name:
                out.append(name)
        return out

    def test_still_scene_then_step(self):
        self.session((b"still 1", 60), (b"still 2", 60))
        self.assertEqual(self.still.drawn, [(1, None), (2, None)])
        # The first scene is a full refresh; a new step in it is a partial.
        self.assertEqual(self.counts(), (1, 1))
        self.assertEqual(self.panel.glass, self.display.buffer)

    def test_scene_change_is_full(self):
        self.session((b"still 1", 60), (b"blink 0", 50), (b"still 1", 60))
        self.assertEqual(self.panel.full, 3)

    def test_a_trigger_plays_at_once(self):
        self.session((b"still 1", 5))
        self.assertEqual(self.still.drawn, [(1, None)])

    def test_burst_ends_on_the_last(self):
        self.session((b"still 1", 1), (b"still 2", 1), (b"still 3", 100))
        self.assertEqual(self.still.drawn[-1], (3, None))
        self.assertEqual(self.panel.glass, self.display.buffer)

    def test_unknown_or_bad_state_ignored(self):
        self.session((b"still 1", 60), (b"nope 1", 60), (b"still x", 60))
        self.assertEqual(self.still.drawn, [(1, None)])
        self.assertEqual(self.counts(), (1, 0))

    def test_keyframes_play_once(self):
        self.session((b"blink 0", 400))
        self.assertEqual(self.blink.drawn, ["open", "shut"])

    def test_new_state_cuts_in(self):
        self.blink.frames = Keyframes([("open", 300), ("shut", 30)])
        self.session((b"blink 0", 60), (b"still 1", 100))
        self.assertEqual(self.blink.drawn, ["open"])
        self.assertEqual(self.still.drawn, [(1, None)])
        # The glass shows the new scene.
        self.assertEqual(self.panel.glass, self.display.buffer)

    def test_still_frame_powers_off(self):
        self.session((b"still 1", 100))
        self.assertEqual(self.panel.powered_off, 1)

    # Holds shorter than the display's idle time keep the supply on; a longer one turns it off.
    def test_long_hold_powers_off(self):
        self.blink.frames = Keyframes([("open", 200), ("shut", 30)])
        self.session((b"blink 0", 400))
        self.assertEqual(self.blink.drawn, ["open", "shut"])
        self.assertEqual(self.panel.powered_off, 2)

    def test_failing_scene_keeps_player(self):
        self.session((b"still 1", 100), (b"broken 0", 100), (b"still 2", 100))
        self.assertEqual(self.still.drawn, [(1, None), (2, None)])

    # The first pose turned the high voltage on; the failure mustn't leave it on.
    def test_failing_keyframe_powers_off(self):
        self.session((b"fails 0", 200))
        self.assertEqual(self.panel.powered_off, 1)

    def test_empty_keyframes_drawn_once(self):
        self.session((b"empty 0", 100), (b"still 1", 100))
        self.assertEqual(self.player.scenes["empty"].drawn, [None])
        self.assertEqual(self.still.drawn, [(1, None)])

    def test_background_plays_from_the_start(self):
        self.player = self.make(background=self.background)
        self.session((None, 150))
        self.assertTrue(len(self.background.drawn) >= 4, self.background.drawn)
        self.assertEqual(self.background.drawn[:3], [0, 1, 2])
        self.assertEqual(self.panel.full, 1)

    def test_trigger_plays_once_then_the_background_again(self):
        self.player = self.make(background=self.background)
        self.session((None, 60), (b"blink 0", 300))
        # The background never cuts in while the trigger plays.
        self.assertEqual(self.names(), ["background", "blink", "background"])
        self.assertEqual(self.blink.drawn, ["open", "shut"])
        # It starts again from its first pose, after a full refresh: a new scene each time.
        last = max(i for i, (name, _, _) in enumerate(self.log) if name == "blink")
        self.assertEqual(self.log[last + 1][:2], ("background", 0))
        self.assertEqual(self.panel.full, 3)

    def test_still_trigger_holds_then_the_background(self):
        self.player = self.make(background=self.background)
        self.session((None, 60), (b"still 1", 300))
        self.assertEqual(self.names(), ["background", "still", "background"])
        shown = next(t for name, _, t in self.log if name == "still")
        back = next(t for name, _, t in self.log if name == "background" and t > shown)
        self.assertTrue(time.ticks_diff(back, shown) >= 50, (shown, back))

    def test_failing_trigger_goes_back_to_the_background(self):
        self.player = self.make(background=self.background)
        self.session((None, 60), (b"broken 0", 150))
        self.assertEqual(self.names(), ["background"])
        self.assertEqual(self.background.drawn.count(0), 2)  # started again after the failure

    def test_the_backgrounds_own_animation_needs_no_full_refresh(self):
        # Registered as a scene too, the background plays a trigger of its own as the same scene.
        scenes = [self.blink, self.background]
        self.player = Player(self.display, scenes, parse, still_ms=50, background=self.background)
        self.session((None, 60), (b"background 1", 200))
        drawn = self.background.drawn
        self.assertEqual(drawn[drawn.index(101) + 1], 201)
        self.assertEqual(drawn[drawn.index(201) + 1], 0)  # then the background, from its start
        self.assertEqual(self.panel.full, 1)

    def test_triggers_ignored_while_the_background_holds_the_glass(self):
        self.background.holds = True
        self.player = self.make(background=self.background)
        self.session((None, 60), (b"blink 0", 100))
        self.assertEqual(self.names(), ["background"])
        self.background.holds = False
        self.session((b"blink 0", 100))
        self.assertEqual(self.blink.drawn, ["open", "shut"])

    # The badge, pressed during a trigger, shows within a chunk rather than when the trigger ends.
    def test_a_trigger_gives_way_when_the_background_takes_the_glass(self):
        self.player = self.make(background=self.background)
        self.player.still_ms = 5000

        def press():
            self.background.holds = True

        self.session((None, 60), (b"still 1", 300), (press, 400))
        self.assertEqual(self.names(), ["background", "still", "background"])

    # A background repeats its pose every chunk to watch its buttons: drawn once, then again only
    # when the link's icon changes.
    def test_a_repeated_pose_is_drawn_once(self):
        class Resting(Background):
            def keyframes(self, step):
                def forever():
                    while True:
                        yield 0, 20

                return Keyframes(forever())

        resting = Resting(self.log)
        self.player = self.make(background=resting)

        def drop():
            self.link.connected = False

        self.session((None, 200), (drop, 200))
        self.assertEqual(resting.drawn, [0, 0])

    def test_overlay_draws_over_every_frame(self):
        calls = []

        def overlay(display, link):
            calls.append(link)
            display.pixel(799, 479, 0 if link.connected else 1)

        self.player = self.make(background=self.background, overlay=overlay)
        self.link.connected = False
        self.session((None, 60), (b"blink 0", 200))
        self.assertEqual(len(calls), len(self.log))
        self.assertTrue(all(link is self.link for link in calls))
        self.assertEqual(self.panel.glass, self.display.buffer)
        self.assertEqual(self.display.pixel(799, 479), 1)


class TestGrey(PlayerCase):
    def setUp(self):
        super().setUp()
        self.greyed = Greyed()
        self.overlaid = []
        self.player = Player(
            self.display,
            [],
            parse,
            background=self.greyed,
            overlay=lambda display, link: self.overlaid.append(link.connected),
        )

    def on(self):
        self.greyed.on = True

    def off(self):
        self.greyed.on = False

    def counts(self):
        return self.panel.full, self.panel.partial, self.panel.grey

    # Held over many chunks: asked for and shown once, and no show() that would undo it.
    def test_shown_once_and_held(self):
        seen = []
        self.session((None, 60), (self.on, 150), (lambda: seen.append(self.counts()), 200))
        self.assertEqual(self.greyed.asked, 1)
        self.assertEqual(self.panel.grey, 1)
        self.assertEqual(self.counts(), seen[0])
        self.assertEqual(self.panel.greys, self.greyed.frame)

    def test_the_link_neither_redraws_nor_overlays_it(self):
        def drop():
            self.link.connected = False

        self.session((None, 60), (self.on, 100), (lambda: self.overlaid.clear(), 0), (drop, 200))
        self.assertEqual(self.panel.grey, 1)
        self.assertEqual(self.overlaid, [])

    def test_leaving_is_a_full_refresh(self):
        self.session((None, 60), (self.on, 100))
        full = self.panel.full
        self.session((self.off, 100))
        self.assertEqual(self.panel.full, full + 1)
        self.assertIsNone(self.panel.greys)
        self.assertEqual(self.panel.glass, self.display.buffer)

    # Up again during the grey refresh: it ends, then black and white comes back, in full.
    def test_off_during_the_refresh_waits_for_it(self):
        self.panel.refresh_ms = 150

        async def main():
            task = asyncio.create_task(self.player.run(self.link))
            await asyncio.sleep_ms(60)
            self.on()
            while not self.panel.grey:
                await asyncio.sleep_ms(1)
            self.assertTrue(self.panel.busy())
            full = self.panel.full
            self.off()
            await asyncio.sleep_ms(100)
            self.assertEqual(self.panel.full, full)  # not while the grey refresh runs
            await asyncio.sleep_ms(300)
            self.assertEqual(self.panel.full, full + 1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(main())
        self.assertEqual(self.panel.grey, 1)
        self.assertIsNone(self.panel.greys)

    # The player's own rule, whatever the display does: leaving grey is a full refresh.
    def test_leaving_is_full_on_any_display(self):
        calls = []

        class Recording(Display):
            async def show(self, full=False):
                calls.append(("show", full))
                await asyncio.sleep_ms(0)

            async def show_grey(self, frame, clean=False):
                calls.append(("grey", clean))
                await asyncio.sleep_ms(0)

        self.player.display = Recording(SimPanel())
        self.session((None, 60), (self.on, 60), (self.off, 60))
        # Cleaned first, then black and white again in full.
        after = calls[calls.index(("grey", True)) + 1 :]
        self.assertEqual(after[0], ("show", True))
        self.assertEqual(after[1], ("show", False))

    # Firmware before show_grey(): Up shows nothing, and the character carries on.
    def test_a_display_without_grey(self):
        class NoGrey:
            def __init__(self, display):
                self.inner = display

            def __getattr__(self, name):
                if name == "show_grey":
                    raise AttributeError(name)
                return getattr(self.inner, name)

        self.assertTrue(self.greyed.greys)
        self.player = Player(NoGrey(self.display), [], parse, background=self.greyed)
        self.assertFalse(self.greyed.greys)  # told before anything plays
        # A scene that asks anyway fails before anything changes: no extra full refresh.
        self.session((None, 60))
        full = self.panel.full
        self.session((self.on, 100))
        self.assertEqual(self.panel.grey, 0)
        self.assertEqual(len(self.greyed.failed), 1)
        self.assertFalse(self.greyed.on)
        self.assertEqual(self.panel.full, full)

    # grey() itself failing (no memory to inflate) mustn't stop the background.
    def test_grey_raising_goes_back_to_black_and_white(self):
        def broken(step, pose):
            if pose == "grey":
                raise MemoryError
            return None

        self.greyed.grey = broken
        self.session((None, 60), (self.on, 100))
        self.assertEqual(len(self.greyed.failed), 1)
        drawn = len(self.greyed.drawn)
        self.session((None, 100))
        self.assertTrue(len(self.greyed.drawn) > drawn)

    def test_a_failed_grey_frame_goes_back_to_black_and_white(self):
        def fail(frame):
            raise OSError("busy timeout")

        self.panel.show_grey = fail
        self.session((None, 60), (self.on, 100))
        self.assertEqual(len(self.greyed.failed), 1)
        self.assertFalse(self.greyed.on)
        drawn = len(self.greyed.drawn)
        self.session((None, 100))
        self.assertTrue(len(self.greyed.drawn) > drawn)


class TestRun(unittest.TestCase):
    def test_run_with_fakes(self):
        link = Link()
        panel = SimPanel()
        still = Still()
        background = Background()
        overlays = []

        async def deck():
            await asyncio.sleep_ms(100)
            link.send(b"still 2")
            await asyncio.sleep_ms(400)
            raise KeyboardInterrupt  # ends run(), which otherwise runs until reset

        link.run = deck
        with self.assertRaises(KeyboardInterrupt):
            run(
                [still],
                parse,
                link=link,
                display=Display(panel),
                background=background,
                overlay=lambda d, link: overlays.append(link),
            )
        self.assertEqual(still.drawn, [(2, None)])
        self.assertTrue(background.drawn)
        self.assertTrue(overlays)
        # The Ctrl-C path released the link and turned the panel's supply off.
        self.assertTrue(link.closed)
        self.assertEqual(panel.powered_off, 1)

    # The unix port has no panel, so making one fails: the link given is still released.
    def test_run_releases_the_link_when_setup_fails(self):
        link = Link()
        with self.assertRaises(ImportError):
            run([Still()], parse, link=link)
        self.assertTrue(link.closed)

    # Interrupted mid-animation, the player's own task stops too, and run() can start again.
    def test_run_twice(self):
        panel = SimPanel()
        background = Background()

        for _ in range(2):
            link = Link()

            async def deck():
                await asyncio.sleep_ms(400)
                raise KeyboardInterrupt

            link.run = deck
            with self.assertRaises(KeyboardInterrupt):
                run([], parse, link=link, display=Display(panel), background=background)
            drawn = len(background.drawn)

            # Nothing left over keeps animating once run() has returned.
            async def pause():
                await asyncio.sleep_ms(200)

            asyncio.run(pause())
            self.assertEqual(len(background.drawn), drawn)
        self.assertTrue(drawn >= 4)


if __name__ == "__main__":
    unittest.main()
