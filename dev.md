# Working on the deck

## Commands

```sh
npm ci
npm run dev       # dev server on 0.0.0.0, so a phone on the LAN can open it
npm run build     # static deck in dist/
npm run preview   # serve dist/ to check the build
```

Editing a slide file reloads the browser on the same slide and fragment.

**Browsers and phones:** with the dev server running, `npm run check:browsers`
screenshots the deck in Chromium, Firefox and WebKit at desktop sizes and the
most common phone sizes, portrait and landscape, into `.screenshots/`. Options
are in AGENTS.md, "Testing in browsers". To try it on your own phone, open
`http://<your-mac's-LAN-IP>:5173` on the same Wi-Fi.

**PDF:** open <http://localhost:5173/presentation?print-pdf> in Chrome and print to PDF
(landscape, no margins, background graphics on). Each fragment state becomes a
page.

**Reviewing design changes:** when Claude proposes visual changes, it can
show them before and after at <http://localhost:5173/reports/before-after/>.
Space flips between the two; ← → move between changes. Reply in the chat
with the change numbers. How it works is in `reports/README.md`.

**On phones:** in portrait the deck asks to be turned sideways, with a Full
screen button on Android (iPhones can't go full screen from a web page). In
landscape a small full-screen button sits in the top-right corner.

## Shortcuts while presenting

| Key | Does |
|---|---|
| S | Speaker view: notes, next slide, timer |
| T | Next theme |
| 1–5 | A theme, in the order of the table under Themes |
| O or Esc | Overview of every slide |
| F | Fullscreen |
| M (hold) | Magnifier: zooms in where the mouse is, in the window with focus (so not the speaker view) |
| B | Web Bluetooth connect to MicroPython badge |
| ? | All shortcuts |

## Where to edit

| To change | Edit |
|---|---|
| A slide | `slides/NN-part.html` |
| Order of parts | the `@include` lines in `presentation.html` |
| Title, name, event | the cover in `slides/01-intro.html` |
| Deck URL (QR caption) | `data-deck-url` on `.reveal` in `presentation.html` |
| QR code | regenerate `public/images/qr.svg` if the URL changes (square viewBox, same name) |
| Colours, code size | `src/styles/tokens.css` (a theme sets its own in its `theme.css`) |
| A drawing's colours and line weights | `src/styles/art/<name>.css` |
| Pin header and LED labels | `src/themes/<name>/parts.html` |
| Default theme | first entry of `PREFERRED` in `src/themes/index.js` |
| The board chrome, the phone view or the heap grids | that plugin's folder in `src/plugins/` |
| A generated drawing (the owl slide's drawings, the deck map, the board scale) | its script in `scripts/art/`, then `python3 scripts/art/<name>.py` |

Most components, with examples, are on the slides in `slides/09-demo.html`
(a component reference, excluded from the published deck).

## Themes

Hybrid is the default. **T** cycles themes on the same slide, a number key
picks one, `?theme=<name>` picks one too, and the browser remembers the last
choice. If a browser still opens in an old theme, press 1 or add
`?theme=hybrid` once.

| Key | Theme | What it is |
|---|---|---|
| 1 | [hybrid](http://localhost:5173/presentation?theme=hybrid) | Default. Classic's board and palette, Oxanium titles, heavier type, a chip wired to the pin header on the cover, clean part dividers |
| 2 | [hybrid-matte](http://localhost:5173/presentation?theme=hybrid-matte) | Hybrid on a flat, darker mask with the traces tented under it; the cover's traces are the Python logo's yellow and blue |
| 3 | [schematic](http://localhost:5173/presentation?theme=schematic) | Each slide is a KiCad schematic sheet on paper, with a title block and the I2C circuit on the cover |
| 4 | [classic](http://localhost:5173/presentation?theme=classic) | The original board from `reports/mockup/mockup1.png`, light Roboto throughout |
| 5 | [refined](http://localhost:5173/presentation?theme=refined) | Cooler, bluer solder mask, heavier type, a QFN wired to a header on the cover, a small routing detail on content slides |

A theme is a folder in `src/themes/` holding `frame.svg`, `cover.svg`,
`parts.html` and an optional `theme.css`. Copy a folder to start a new one.
A theme inside another's folder builds on it and borrows the files it lacks:
hybrid-matte and schematic live in `src/themes/hybrid/`.

## Before the talk

- Once the deck URL is live, scan the QR on the cover and on a content slide with a real phone.
- Remove the `slides/09-demo.html` include from `index.html`, so the demo part isn't in the talk.
- `npm run build`, then `npm run preview`, and click through every slide and fragment.
- Check the deck at the venue's projector resolution, and with speaker view open.
- Open the deck URL on a real Android phone and an iPhone: the turn-sideways card in
  portrait, Full screen on Android, and the slides in landscape.
- Keep a PDF export as a fallback.
- The timings (33–34 minutes) leave almost no buffer in the 35-minute slot. Slides marked "Cut-first" in their notes are the ones to drop.

## Landing-page browser checks

With the dev server running, `npm run check:landing` checks the landing page at
25 sizes: five desktop/projector sizes and all ten phone sizes in both
orientations. It saves screenshots and `.screenshots/landing/report.json`.
The checks cover horizontal overflow, missing images/fonts, tap targets,
portrait trace connections and bottom clearance.

```sh
npm run check:landing
npm run check:landing -- --browsers chrome,firefox --devices desktop
npm run check:landing -- --browsers safari --devices desktop
npm run check:landing -- --browsers webkit --devices phones
```

Chrome uses the installed Google Chrome; Firefox and WebKit use the cached
Playwright browsers. Safari uses the installed Safari through WebDriver, with
no extra package. Enable Safari automation in your own Terminal with
`sudo /usr/bin/safaridriver --enable` if needed. Safari has no mobile emulation
and may enforce a minimum window size: the report records actual viewport
sizes and flags sizes it cannot match. WebKit supplies phone-size engine
coverage, not a claim of testing real iPhone Safari. Safari screenshots cover
the viewport and Safari console capture is unavailable through this check.

Exit 2 means layout checks failed or a browser could not start. Exit 3 means
requested viewport sizes could not be matched. An empty run is not a pass.
