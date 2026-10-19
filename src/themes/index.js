/*
 * Themes, discovered from src/themes/<name>/: frame.svg, cover.svg and
 * parts.html are inlined into the board chrome; theme.css, if present, is
 * bundled and scoped to :root[data-theme="<name>"]. A "<base>-<variant>"
 * folder borrows any of those files it lacks from <base>.
 */

const files = import.meta.glob('./*/{frame.svg,cover.svg,parts.html}', {
  query: '?raw',
  import: 'default',
  eager: true,
});

// Bases first, so a variant's rules override its base's at equal specificity.
import.meta.glob(['./*/theme.css', '!./*-*/theme.css'], { eager: true });
const variantStyles = import.meta.glob('./*-*/theme.css', { eager: true });

const themes = {};
for (const [path, source] of Object.entries(files)) {
  const [, name, file] = path.match(/^\.\/([^/]+)\/(\w+)\./);
  (themes[name] ??= {})[file] = source;
}
// A variant with only a theme.css still borrows all its art.
for (const path in variantStyles) themes[path.split('/')[1]] ??= {};

for (const [name, layers] of Object.entries(themes)) {
  const [base, variant] = name.split('-');
  themes[name] = { parts: '', ...(variant && themes[base]), ...layers };
}

// T cycles in this order, the first is the default; others follow alphabetically.
const PREFERRED = ['hybrid', 'hybrid-matte', 'hybrid-schematic', 'classic', 'refined'];

const complete = (name) => themes[name]?.frame && themes[name]?.cover;

export const THEMES = [
  ...PREFERRED.filter(complete),
  ...Object.keys(themes).filter((name) => !PREFERRED.includes(name) && complete(name)).sort(),
];

export const themeLayers = (name) => themes[name];
