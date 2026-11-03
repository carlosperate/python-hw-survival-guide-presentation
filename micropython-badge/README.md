# micropython-badge

The talk's programme for the Seeed reTerminal Sticky, worn as a badge.

- A character idles on the e-paper.
- The slides send it triggers over Bluetooth, and each plays once.
- It runs on the
  [micropython-reterminal-sticky](https://github.com/carlosperate/micropython-reterminal-sticky)
  firmware.

## Load it

- You need [uv](https://docs.astral.sh/uv/).
- Run the commands from this folder.
- `uv run` installs the tools (`pyproject.toml`) the first time.

```sh
export PORT=/dev/cu.usbmodem…   # the Sticky's serial port: `uv run mpremote connect list`
make load
```

`make load` copies `device/` to the Sticky, skipping unchanged files, then restarts it.

Any mpremote command stops the programme, and Chrome can't find the Sticky until it restarts.
`make reset` restarts it over USB, as the Reset button does.
Give it a few seconds before the next mpremote command: while it boots, mpremote can't reach it.

To run it from this folder without copying:

```sh
uv run mpremote connect $PORT mount device exec "import main"
make reset   # afterwards
```

## Buttons

- **Up:** the badge, on and off.
- **Down:** the next eye style.
- **Up, held while it starts:** skip the programme and stay at the REPL. The glass says so for a
  second, then goes blank.

## Triggers

- `triggers.json` lists every trigger, by the name a slide uses.
- Each name maps to the line sent over Bluetooth.
- Three groups: presentation, blinks and idle animations.
- A slide plays one with `data-ble-badge="<name>"` on its `<section>`, or on a fragment. In the
  deck, B connects the Sticky.
- The Sticky advertises as `sticky-badge-XXXX`. If the chooser stays empty after a firmware
  change, macOS may still hold the old name: connect once from a scanner (nRF Connect) to
  refresh it.

To try them, run `make web`. It serves this folder and opens the test page, with a dropdown per
group. Web Bluetooth needs Chrome.

## Folders

- `device/`: everything that goes on the board.
  - `main.py` sets the programme up.
  - `scenes.py` holds the placeholder triggers.
  - `deck/` is the player, the line protocol and the character.
  - `idle/` holds the character's frames.
- `character/`: draws the art on the Mac, with Pillow.
- `web/`: `link.js`, the slides' side of the link, and the test page.
- `tests/`: unix and device tests.
- `docs/`: [animation.md](docs/animation.md) and [character.md](docs/character.md).
- `prototypes/`: how the character was chosen.

## Change the art

```sh
uv run python character/export.py   # frames and the badge, in device/idle/
uv run python character/idle.py     # GIFs, in build/previews/
uv run python character/badge.py    # the badge, in build/previews/
```

The badge reads the deck's photo, QR code and fonts: run `npm ci` in the deck's folder first. It
shows in four greys, which needs the port's firmware with `Display.show_grey()`.

Then load `device/` again.

## Tests

They need a checkout of
[micropython-reterminal-sticky](https://github.com/carlosperate/micropython-reterminal-sticky),
built there with `make submodules unix`.

- `STICKY` points at it. By default it's `micropython-reterminal-sticky/` in this folder.
- Unix tests run in Docker.
- Device tests use `PORT`, and restart the Sticky before and after.

```sh
make test STICKY=path/to/checkout
make test-device STICKY=path/to/checkout
uv run ruff check . && uv run ruff format --check .
```
