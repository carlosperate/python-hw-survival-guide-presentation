# Python HW Survival Guide

Slides for a talk at PyCon ES 2026, built with [reveal.js](https://revealjs.com).

## Launch the slides

You need Node.js 20.19+ (or 22.12+).

```sh
npm ci
npm run dev
```

Then open the URL Vite prints, usually <http://localhost:5173>.

## Themes

Press **T** to cycle through the themes on the same slide and fragment, or pick
one with `?theme=`. The browser remembers the last choice.

- [classic](http://localhost:5173/?theme=classic): the original board, the default
- [hybrid](http://localhost:5173/?theme=hybrid): classic, with refined's cover
  part, heavier headings and quieter components
- [refined](http://localhost:5173/?theme=refined): cooler mask, a QFN wired to a
  header on the cover, a small routing detail on content slides
- [alternative](http://localhost:5173/?theme=alternative): currently a copy of
  classic, ready to be replaced

Each theme is one folder, and adding a folder adds a theme:

| File in `src/themes/<name>/` | What it holds |
|---|---|
| `frame.svg` | Board edge and gutter art, on every slide |
| `cover.svg` | The trace network, on cover and section slides |
| `parts.html` | Labelled parts drawn over the art: LEDs, pin header, silkscreen |
| `theme.css` | Optional. Overrides scoped to `[data-theme="<name>"]` |

Everything outside `src/themes` is shared, and classic is what the shared styles
draw. `src/themes/index.js` discovers the folders and sets the cycling order.
Use reveal's **?** help overlay to see the shortcuts.

## The board theme

The deck is styled as a printed circuit board: dark solder mask, copper traces
in the two Python logo colours, and silkscreen type. `mockup/mockup1.png` is the
reference the theme was built from.

Everything drawn behind the slides is "chrome": `src/board/chrome.js` inlines the
artwork and pins it to reveal's slide rectangle, so the SVGs' 1280×720
coordinates and the slides' coordinates are the same. Move a trace to x 600 and
it lines up with a slide element at x 600.

| File | What lives there |
|---|---|
| `src/styles/tokens.css` | Palette, spacing, motion |
| `src/styles/theme.css` | reveal.js element styling (headings, lists, code, tables) |
| `src/styles/board.css` | The chrome layer: frame, pin header, LEDs, footer rail |
| `src/styles/components.css` | Slide building blocks |
| `src/themes/<name>/` | One theme's artwork, parts and overrides; see [Themes](#themes) |
| `public/images/python-mark.svg` | The official Python logo, unmodified (python.org, via Wikimedia Commons) |

The SVGs read their colours from the CSS custom properties in `tokens.css` and
fall back to literal values, so they also render correctly opened on their own.

Labels on the pin header and the LED block are HTML, not SVG text: Chrome does
not reliably rasterise webfont SVG `<text>` inside the scaled chrome layer, and
at some window sizes the labels silently vanish.

### The QR footprint

In classic, alternative and hybrid, `frame.svg` dresses the content-slide QR as
a QFN package with pads and escape traces, and `board.css` centres the QR image
in its body (x 1120–1212, y 577–669; hybrid's sits 10px lower and its
`theme.css` moves the image to match). Move one and you must move the other.

Escapes either run out to the board outline, the way a net bound for another
part of the board does, or stop on a via. Per side:

| Side | Escape |
|---|---|
| Right | Out, one 45, then straight to the edge — the four step up as a parallel set |
| Top right | Up a little, then one 45 carried all the way out to the right edge |
| Bottom | Straight down to the edge |
| Left | Five stubs onto vias, each longer than the one above so the ends fall away in a diagonal; the bottom one turns down and runs to the edge |
| Top (other five) | Short stubs onto a staggered two-row via fence |

The right side deliberately does not climb the gutter: a full-height bus there
made that edge of the slide too busy.

Escapes are authored with their 45s already in them and are **not** run through
`mitre()`. That helper turns a right angle into a 45 cut, so applying it to a
corner that is already 45 splits it in two and the trace reads as rounded. A
direction change is one turn; stepping up and carrying on is two.

### The QR code

Every slide carries one: large under the cover title block, small in the
bottom-right corner everywhere else. It is board chrome, not slide markup, so
new slides get it for free, and the footer rail stops short of that corner.

Replace `public/images/qr.svg` with your own, keeping the name and a square
viewBox. The shipped file is deliberately not a scannable pattern — a fake one
that fails to scan at a conference is worse than an obviously empty box. Set the
caption under the cover QR with `data-deck-url` on `.reveal`.

### How the artwork is kept off the content

Both layers are generated against a list of keep-out rectangles — the title
block, the Python mark, the pin header, both QR footprints, the chip list, the
footer rail — and the generator refuses to emit artwork that lands in one. The
routing itself follows the rules a real board does: 45-degree mitres only; true
constant-clearance parallel offsets, so a bus keeps its pitch through every
corner and the mitres stagger; traces of one colour never crossing each other;
and vias only where a route terminates or hands a net to the other layer.

### Slide recipes

How much of the theme's artwork a slide shows is chosen with `data-board`:

```html
<section data-board="cover">   <!-- full artwork: traces, pin header, LEDs -->
<section data-board="section"> <!-- dimmed artwork, for part dividers -->
<section>                      <!-- frame and footer rail only -->
```

Slides lay out from the top. Add `is-centered` to centre the content
vertically, and `section-slide` with `data-part="02"` for the large ghosted
part number on a divider.

The components are plain classes, all shown in `index.html`:
`trace-rule`, `slide-head`, `lede`, `tagline`, `cols` (`--wide-left`,
`--wide-right`), `panel[data-label]`, `callout` (`--warn`, `--danger`),
`specs`/`spec__value`/`spec__label`, `pinout`, `quote`, `net`, `chip-list`,
`qr-slot`, `stamp`.

Two extra fragment styles sit alongside reveal's own: `highlight-trace` and
`dim-past`, which keeps a step visible but muted until it is the current one.

### Changing the deck's identity

- Title and subtitle: the cover section in `index.html`.
- Footer rail label: `data-deck-label` on `.reveal`.
- Colours: `src/styles/tokens.css`.
- Default theme: the first entry of `PREFERRED` in `src/themes/index.js`.
- Pin header nets and LED labels: each theme's `parts.html`.
- QR code: replace `public/images/qr.svg`; caption via `data-deck-url` on `.reveal`.

### Fonts

Roboto at light weights carries the deck, after
[quarto-revealjs-clean](https://github.com/grantmcdermott/quarto-revealjs-clean);
JetBrains Mono does labels, pin names and code. The hybrid theme sets its
titles, section numerals and spec values in Oxanium. All three are self-hosted
through `@fontsource-variable` and imported in `src/fonts.js`, so the deck
renders identically with no network. Weights live in `src/styles/tokens.css`,
and a theme's own overrides in its `theme.css`.
