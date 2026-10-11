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

**Reviewing design changes:** <http://localhost:5173/review/> shows each
change before and after, with a link to the live slide. Mark each one and
"Copy feedback" puts your notes on the clipboard to paste into the chat. The
`review/` folder is local only (ignored by git).

**On phones:** in portrait the deck asks to be turned sideways, with a Full
screen button on Android (iPhones can't go full screen from a web page). In
landscape a small full-screen button sits in the top-right corner.

## Shortcuts while presenting

| Key | Does |
|---|---|
| S | Speaker view: notes, next slide, timer |
| T | Next theme |
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
| Footer label, QR caption | `data-deck-label` and `data-deck-url` on `.reveal` in `index.html` |
| QR code | replace `public/images/qr.svg` (square viewBox, same name) |
| Colours | `src/styles/tokens.css` |
| Pin header and LED labels | `src/themes/<name>/parts.html` |
| Default theme | first entry of `PREFERRED` in `src/themes/index.js` |

Every component, with examples, is on the slides in `slides/09-demo.html`
(the "Demo" part at the end of the deck).

## Themes

Hybrid is the default. **T** cycles themes on the same slide, `?theme=<name>`
picks one, and the browser remembers the last choice. If a browser still opens
in an old theme, press T or add `?theme=hybrid` once.

| Theme | What it is |
|---|---|
| [hybrid](http://localhost:5173/?theme=hybrid) | Default. Classic's board and palette, Oxanium titles, heavier type, a chip wired to the pin header on the cover, clean part dividers |
| [classic](http://localhost:5173/?theme=classic) | The original board from `mockup/mockup1.png`, light Roboto throughout |
| [refined](http://localhost:5173/?theme=refined) | Cooler, bluer solder mask, heavier type, a QFN wired to a header on the cover, a small routing detail on content slides |

A theme is a folder in `src/themes/` holding `frame.svg`, `cover.svg`,
`parts.html` and an optional `theme.css`. Copy a folder to start a new one.

## The project's markdown files

| File | For | Holds |
|---|---|---|
| `README.md` | Anyone looking at the repo | What the talk is, how to run it |
| `dev.md` | Me | This file |
| `AGENTS.md` | Claude | How the repo works and the rules for changing it |
| `PRODUCT.md` | Claude (Impeccable) | Who the talk is for, what it must achieve, facts that must stay true |
| `DESIGN.md` | Claude (Impeccable) | The visual system: colours, type, slide types, components, do's and don'ts |
| `.impeccable/` | Impeccable | Machine-readable copy of DESIGN.md and live-mode config |

PRODUCT.md is the *why*: audience, purpose, accuracy rules. DESIGN.md is the
*look*. If the audience or a fact changes, update PRODUCT.md; if the look
changes, rerun `/impeccable document` so DESIGN.md matches the code.

Useful Impeccable commands for this deck: `/impeccable critique slides/04-drivers.html`
for a review of one part, `/impeccable polish <file>` before the talk,
`/impeccable live` to try variants in the browser.

## Before the talk

- Replace the placeholder `public/images/qr.svg` with a real QR code for the deck URL.
- Remove the `slides/09-demo.html` include from `index.html`, so the demo part isn't in the talk.
- `npm run build`, then `npm run preview`, and click through every slide and fragment.
- Check the deck at the venue's projector resolution, and with speaker view open.
- Keep a PDF export as a fallback.
- The timings total 35 minutes with no buffer. Slides marked "Cut-first" in their notes are the ones to drop.
