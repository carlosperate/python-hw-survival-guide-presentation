# Developer Notes

## Commands

```sh
npm ci
npm run dev       # dev server, also on your network
npm run build     # static site in dist/
npm run preview   # serve dist/
```

- Landing page at `/`, deck at `/presentation`.
- On a phone on the same Wi-Fi: `http://<your-mac's-IP>:5173/presentation`.

## Where to edit

- A slide: `slides/NN-part.html`.
- Order of parts: the `@include` lines in `presentation.html`.
- Colours and code size: `src/styles/tokens.css`.
    - Per theme: its `theme.css`.
- A drawing's style: `src/styles/art/<name>.css`.
- A generated drawing: edit `scripts/art/<name>.py`, then run it with `python3`.
- Default theme: the first entry of `PREFERRED` in `src/themes/index.js`.

## Themes

**T** cycles themes, a number key picks one. So does `?theme=<name>`.
The browser remembers your pick; press **1** for the default.

- 1 hybrid-matte: the default. Hybrid on a darker, flat mask.
- 2 hybrid: Oxanium titles, a chip on the cover.
- 3 schematic: each slide is a KiCad schematic sheet.

Each theme is a folder in `src/themes/`. A theme inside another's folder
borrows the files it lacks.

## Browser checks

Start `npm run dev` first. Screenshots go to `.screenshots/`, replaced on
each run.

```sh
npm run check:browsers   # deck, all browsers and sizes, about 20 minutes
npm run check:browsers -- --browsers webkit --devices portrait --slides 16/0/4
npm run check:landing    # landing page, all browsers and sizes
npm run check:landing -- --browsers safari --devices desktop
```

- Options are at the top of each script in `scripts/`.
- A non-zero exit means a problem; the output says which.
- WebKit is Safari's engine at phone sizes, not a real iPhone.
- Safari won't start? Run `sudo /usr/bin/safaridriver --enable` once.
