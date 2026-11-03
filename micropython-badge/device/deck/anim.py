# Scenes, keyframes and the player that turns the deck's triggers into frames on the glass.
# A scene draws its whole frame: the partial refresh only drives the pixels that changed.

import asyncio

STILL_MS = 3000
CHUNK_MS = 250  # holds are cut into these, so a button press shows within one


class Scene:
    """Subclass with a name and draw(); override keyframes() to animate."""

    name = None
    holds = False  # as the background: True while it keeps the glass from triggers (a badge)
    greys = True  # set by the player: whether its display can show grey frames

    def draw(self, display, step, pose):
        raise NotImplementedError

    def keyframes(self, step):
        """The Keyframes to play for step, or None for a still frame."""
        return None

    def grey(self, step, pose):
        """A four-grey frame (800x480 GS2_HMSB) to show for pose instead of drawing it, asked for
        once a showing: shown with a grey refresh and held, with no overlay. None, as here, to
        draw it."""
        return None

    def grey_failed(self, error):
        """The grey frame couldn't be shown (or grey() raised): go back to black and white."""


class Keyframes:
    """(pose, hold_ms) pairs, played once; a generator can go on for ever. A hold counts from the
    refresh's start, so a short one is a refresh."""

    def __init__(self, poses):
        self.poses = poses


class Player:
    """Plays the background, and each scene parse(state) names for a new state of link (changed()
    and state) once, then the background again. overlay(display, link) draws over every frame,
    from link.connected."""

    def __init__(
        self,
        display,
        scenes,
        parse,
        background=None,
        overlay=None,
        still_ms=STILL_MS,
    ):
        self.display = display
        self.scenes = {scene.name: scene for scene in scenes}
        # Told before anything plays, so a scene never asks for what this display can't show.
        greys = hasattr(display, "show_grey")
        for scene in list(self.scenes.values()) + [background]:
            if scene is not None:
                scene.greys = greys
        self.parse = parse
        self.background = background
        self.overlay = overlay
        self.still_ms = still_ms
        self.link = None
        self._task = None
        self._shown = None  # (scene name, step, pose, link.connected) of the last frame shown

    async def run(self, link):
        self.link = link
        try:
            self._task = asyncio.create_task(self._play(None, 0))
            while True:
                # At once, not after a pause for a burst to end: a trigger that waits looks like a
                # slow link. A newer one cuts in the same way.
                state = await link.changed()
                if self.background and self.background.holds:
                    print("deck.anim: ignored", state, "while the background holds the glass")
                    continue
                try:
                    name, step = self.parse(state)
                    scene = self.scenes[name]
                except Exception as e:
                    # What's playing carries on: a typo in the deck mustn't blank the Sticky.
                    print("deck.anim: ignored", state, repr(e))
                    continue
                await self._stop()
                self._task = asyncio.create_task(self._play(scene, step))
        finally:
            await self._stop()

    async def _stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _play(self, scene, step):
        if scene:
            await self._once(scene, step, self.still_ms)
        if self.background:
            await self._once(self.background, 0, 0)

    # A failing scene logs and leaves the glass: one bad frame mustn't end the programme. The
    # display turns the high voltage off once the frames stop, whatever the reason.
    async def _once(self, scene, step, still_ms):
        try:
            frames = scene.keyframes(step)
            poses = frames.poses if frames and frames.poses else [(None, still_ms)]
            for pose, hold_ms in poses:
                await self._frame(scene, step, pose)
                if await self._hold(scene, hold_ms):
                    return
        except Exception as e:
            print("deck.anim: scene failed", scene.name, step, repr(e))

    async def _hold(self, scene, ms):
        """True if the background takes the glass meanwhile (the badge): a trigger gives way."""
        if not self.background or scene is self.background:
            await asyncio.sleep_ms(ms)
            return False
        while ms > 0:
            await asyncio.sleep_ms(min(ms, CHUNK_MS))
            ms -= CHUNK_MS
            if self.background.holds:
                return True
        return False

    async def _frame(self, scene, step, pose):
        # A grey frame is held: no overlay or show(), which would bring black and white back.
        # None marks it, where a drawn frame has link.connected.
        grey_shown = (scene.name, step, pose, None)
        if self._shown == grey_shown:
            return
        try:
            grey = scene.grey(step, pose)
            if grey is not None:
                show_grey = self.display.show_grey  # before anything changes, if it can't
                self._shown = None
                # Cleaned first: a picture held for long (the character's eyes) shows through less.
                await show_grey(grey, clean=True)
                self._shown = grey_shown
                return
        except Exception as e:
            print("deck.anim: grey frame failed", scene.name, step, repr(e))
            scene.grey_failed(e)
            return
        shown = (scene.name, step, pose, self.link.connected)
        # A new scene gets a full refresh: it clears ghosting where the picture changes anyway.
        # So does a frame after greys: only a full refresh clears them.
        full = not self._shown or self._shown[0] != scene.name or self._shown[3] is None
        # A pose repeated to watch the buttons is in the buffer already, unless the icon changed.
        # show() still runs: only the display knows what the glass holds.
        if shown != self._shown:
            self._shown = None  # a draw that fails or is cancelled leaves the buffer unknown
            scene.draw(self.display, step, pose)
            if self.overlay:
                self.overlay(self.display, self.link)
        await self.display.show(full)
        # Only once shown: a scene change cancelled before this still gets its full refresh.
        self._shown = shown
