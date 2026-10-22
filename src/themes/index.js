/*
 * Themes, discovered from src/themes/<name>/: frame.svg, cover.svg and
 * parts.html are inlined into the board chrome; theme.css, if present, is
 * bundled. A theme in another's folder (src/themes/<base>/<name>/) builds on
 * it, borrowing any of those files it lacks.
 */

const files = import.meta.glob('./**/{frame.svg,cover.svg,parts.html}', {
  query: '?raw',
  import: 'default',
  eager: true,
});

// Bases first, so a variant's rules override its base's at equal specificity.
import.meta.glob('./*/theme.css', { eager: true });
const variantStyles = import.meta.glob('./*/*/theme.css', { eager: true });

const themes = {};
const bases = {};

// './hybrid/hybrid-matte/theme.css' belongs to hybrid-matte, which is built on hybrid.
function layersOf(path) {
  const folders = path.split('/').slice(1, -1);
  const name = folders.at(-1);
  if (folders.length > 1) bases[name] = folders[0];
  return (themes[name] ??= {});
}

for (const [path, source] of Object.entries(files)) layersOf(path)[path.match(/(\w+)\.\w+$/)[1]] = source;
// A variant with only a theme.css still borrows all its art.
for (const path in variantStyles) layersOf(path);

for (const [name, layers] of Object.entries(themes)) {
  const base = bases[name];
  themes[name] = { parts: '', ...(base && themes[base]), ...layers, base: base ?? name };
}

// T cycles in this order, the first is the default; others follow alphabetically.
const PREFERRED = ['hybrid', 'hybrid-matte', 'schematic', 'classic', 'refined'];

const complete = (name) => themes[name]?.frame && themes[name]?.cover;

export const THEMES = [
  ...PREFERRED.filter(complete),
  ...Object.keys(themes).filter((name) => !PREFERRED.includes(name) && complete(name)).sort(),
];

export const themeLayers = (name) => themes[name];
