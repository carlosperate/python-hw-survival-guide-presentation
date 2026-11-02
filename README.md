# Python on Hardware, The Missing Survival Guide

Presentation for the PyCon ES 2026 talk.

## Launch the slides

```sh
npm ci
npm run dev
```

The audience landing page is <http://localhost:5173/> and deck at
<http://localhost:5173/presentation>.

| Key | Does |
|---|---|
| Space / → | Next step |
| ↓ | Additional slides are sometimes available vertically down |
| S | Speaker notes |
| T | Switch visual theme (hybrid-matte the default) |
| F | Full screen |
| M (pressed down) | Magnifier glass on mouse pointer |
| B | Connect the reTerminal Sticky badge (Chrome) |
| ? | All shortcuts |

Built with [reveal.js](https://revealjs.com) and [Vite](https://vite.dev).
Fonts are [Roboto](https://fonts.google.com/specimen/Roboto),
[Oxanium](https://fonts.google.com/specimen/Oxanium) and
[JetBrains Mono](https://www.jetbrains.com/lp/mono/).
The Python logo is a trademark of the Python Software Foundation.

## BBC micro:bit presenter remote

Included in the `./microbit-presenter-remote/` directory.
Contains the BBC micro:bit MakeCode project to use the micro:bit as a Bluetooth
keyboard and mouse.

| Button | Does |
|---|---|
| A | Next slide |
| Face logo (pressed) | Activate the air mouse |
| B (pressed) | Air mouse + magnifier |

## reTerminal Sticky badge

Included in the `./micropython-badge/` directory.
A MicroPython programme for a Seeed reTerminal Sticky worn as a badge:
an e-paper character that idles and reacts to the slides over Bluetooth.

1. Flash the Sticky with the MicroPython firmware from
   [micropython-reterminal-sticky](https://github.com/carlosperate/micropython-reterminal-sticky).
2. Copy the programme to it, with its serial port in place of `<port>`:

   ```sh
   pip install mpremote
   cd micropython-badge/device
   mpremote connect <port> cp -r . :
   ```

3. Press the Sticky's Reset button.
4. Open the deck in Chrome, press B and pick the Sticky.

| Button | Does |
|---|---|
| Up | Badge mode on and off |
| Down | Next eye style |
| Up, held while it starts | Skip the programme |

Development notes are in [micropython-badge/README.md](micropython-badge/README.md).
