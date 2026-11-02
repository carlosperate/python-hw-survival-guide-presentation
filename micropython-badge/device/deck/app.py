# Runs a programme's scenes: the BLE link from the deck, the player, and the panel's display.

import asyncio

from deck.anim import Player

# The deck's chooser lists only this prefix, so a Sticky running another programme stays out.
NAME_PREFIX = "sticky-badge-"


def link_name(ble):
    """NAME_PREFIX and the MAC's last two bytes in hex, as the port names a BLEUART by default.
    ble must be active: the MAC is read from the running radio."""
    mac = ble.config("mac")[1]
    return "%s%02x%02x" % (NAME_PREFIX, mac[-2], mac[-1])


def run(scenes, parse, link=None, display=None, background=None, overlay=None):
    """Play scenes as the deck triggers them, until reset. parse(state) returns (scene name, step);
    background and overlay are the player's.

    Without link or display, reads lines from a BLE UART named link_name() and drives the board's
    panel.
    """
    radio = None
    try:
        if display is None:
            import reterminal_sticky
            from sticky.display import Display

            display = Display(reterminal_sticky.panel())
        if link is None:
            import bluetooth
            from deck.lines import Lines
            from sticky.bleuart import BLEUART

            radio = bluetooth.BLE()
            radio.active(True)
            link = Lines(BLEUART(link_name(radio)))
        player = Player(display, scenes, parse, background, overlay)
        asyncio.run(_main(player, link))
    finally:
        # A Ctrl-C escapes the scheduler and leaves the task it hit half-run, so nothing can await
        # the old tasks: drop them, then turn the high voltage off and release the link directly.
        asyncio.new_event_loop()
        for part in (display, link):
            if part is not None:
                try:
                    part.close()
                except Exception as e:
                    print("deck.app: closing", part, "failed", repr(e))
        if link is None and radio is not None:
            radio.active(False)  # on before the link existed to turn it off


async def _main(player, link):
    asyncio.create_task(link.run())
    await player.run(link)


# Page Up held at boot: main.py checks it before anything loads, so a broken programme can't
# lock out mpremote, and a press during start-up isn't mistaken for it.
def escape():
    try:
        from machine import Pin

        button = Pin.board.BTN_UP
    except (ImportError, AttributeError):
        return False
    button.init(Pin.IN, Pin.PULL_UP)
    return button() == 0
