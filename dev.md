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

**PDF:** open <http://localhost:5173/?print-pdf> in Chrome and print to PDF
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
| B | Black screen |
| ? | All shortcuts |

## Where to edit

| To change | Edit |
|---|---|
| A slide | `slides/NN-part.html` |
| Order of parts | the `@include` lines in `index.html` |
| Title, name, event | the cover in `slides/01-intro.html` |
| Deck URL (QR caption) | `data-deck-url` on `.reveal` in `index.html` |
| QR code | regenerate `public/images/qr.svg` if the URL changes (square viewBox, same name) |
| Colours | `src/styles/tokens.css` |
| Pin header and LED labels | `src/themes/<name>/parts.html` |
| Default theme | first entry of `PREFERRED` in `src/themes/index.js` |

Every component, with examples, is on the slides in `slides/09-demo.html`
(the "Demo" part at the end of the deck).

## Themes

Hybrid is the default. **T** cycles themes on the same slide, a number key
picks one, `?theme=<name>` picks one too, and the browser remembers the last
choice. If a browser still opens in an old theme, press 1 or add
`?theme=hybrid` once.

| Key | Theme | What it is |
|---|---|---|
| 1 | [hybrid](http://localhost:5173/?theme=hybrid) | Default. Classic's board and palette, Oxanium titles, heavier type, a chip wired to the pin header on the cover, clean part dividers |
| 2 | [hybrid-matte](http://localhost:5173/?theme=hybrid-matte) | Hybrid on a flat, darker mask with the traces tented under it; the cover's traces are the Python logo's yellow and blue |
| 3 | [hybrid-schematic](http://localhost:5173/?theme=hybrid-schematic) | Each slide is a KiCad schematic sheet on paper, with a title block and the I2C circuit on the cover |
| 4 | [classic](http://localhost:5173/?theme=classic) | The original board from `reports/mockup/mockup1.png`, light Roboto throughout |
| 5 | [refined](http://localhost:5173/?theme=refined) | Cooler, bluer solder mask, heavier type, a QFN wired to a header on the cover, a small routing detail on content slides |

A theme is a folder in `src/themes/` holding `frame.svg`, `cover.svg`,
`parts.html` and an optional `theme.css`. Copy a folder to start a new one.

## Before the talk

- Once the deck URL is live, scan the QR on the cover and on a content slide with a real phone.
- Remove the `slides/09-demo.html` include from `index.html`, so the demo part isn't in the talk.
- `npm run build`, then `npm run preview`, and click through every slide and fragment.
- Check the deck at the venue's projector resolution, and with speaker view open.
- Open the deck URL on a real Android phone and an iPhone: the turn-sideways card in
  portrait, Full screen on Android, and the slides in landscape.
- Keep a PDF export as a fallback.
- The timings total 35 minutes with no buffer. Slides marked "Cut-first" in their notes are the ones to drop.
