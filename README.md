# Python Hardware Survival Guide

Slides for the PyCon ES 2026 talk.

## Launch the slides

```sh
npm ci
npm run dev
```

The audience landing page is <http://localhost:5173/>. Open the deck at
<http://localhost:5173/presentation>.

Edit the portrait, social icons and links in `index.html`; the deck’s includes and QR
destination live in `presentation.html`. Fonts and images are self-hosted.

| Key | Does |
|---|---|
| Space / → | Next step |
| S | Speaker notes, with the sources for every number |
| T | Switch visual theme (hybrid is the default) |
| ? | All shortcuts |

Built with [reveal.js](https://revealjs.com) and [Vite](https://vite.dev).
Fonts are [Roboto](https://fonts.google.com/specimen/Roboto),
[Oxanium](https://fonts.google.com/specimen/Oxanium) and
[JetBrains Mono](https://www.jetbrains.com/lp/mono/). The Python logo is a
trademark of the Python Software Foundation and is used unmodified.


## Publishing

`.github/workflows/deploy.yml` builds and deploys `dist/` on pushes to `main`
(except those that only change Markdown), or when run manually in Actions.
GitHub Pages must use **GitHub Actions** as its source. The workflow reads Pages’ base path, so it supports both the
repository URL and a custom domain without changing asset paths.

The initial landing page URL is:
<https://carlosperate.github.io/python-hw-survival-guide-presentation/>.
The presentation is at `presentation` under that address (GitHub Pages serves
`presentation.html` without its extension).

The QR currently encodes the planned custom domain, `pycones2026.embeddedlog.com`.
The site itself can be deployed at `github.io` before that domain is configured.
To change the QR destination, update `data-deck-url` in
`presentation.html` and the visible link in `slides/01-intro.html`, then
regenerate `public/images/qr.svg` and verify it by scanning on a real phone.

Before publishing, review the page and deck.

## Keeping editions of the talk

Keep `main` for ongoing edits. After presenting, tag the exact delivered commit
(e.g. `pycones-es-2026`) and create a GitHub Release. Attach the built site as a
ZIP, a PDF, and release notes naming the event and date, plus a recording link
when available. The ZIP should contain the complete `dist/` tree, including
fonts, images and both HTML pages. Save the actual deployed build rather than
rebuilding it later with different tools.

The tag preserves editable source; the ZIP preserves the delivered output.
Use a new tag for each subsequent event. If a published edition needs a
correction, create a new release instead of moving the original tag.

An online archive such as `/archive/pycones-es-2026/` can be added when the
first release exists. Its assets must use paths relative to that archive
(or be built for that exact path), and each deployment must restore archived
editions into its output. GitHub Pages replaces the deployed site: the current
workflow does **not** preserve old deployments as browsable archives.
