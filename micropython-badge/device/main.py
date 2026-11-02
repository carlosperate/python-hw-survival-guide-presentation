# The deck's programme: the character idles in the background, and each trigger from the deck
# plays once (scenes.py). Up held at boot skips it before anything is set up.
import machine
from deck.app import escape, run
from deck.idle import character
from machine import Pin
from scenes import SCENES, link_icon, parse, skipped

if escape():
    print("main: Page Up held at boot, not starting")
    skipped()
else:
    # A wake from deep sleep isn't a boot to point out.
    idle = character(boot=machine.reset_cause() != machine.DEEPSLEEP_RESET)
    scenes = SCENES
    if idle:
        idle.watch(Pin.board.BTN_UP, Pin.board.BTN_DOWN)
        scenes = SCENES + [idle]  # its animations are triggers too

    run(scenes, lambda state: parse(state, idle), background=idle, overlay=link_icon)
