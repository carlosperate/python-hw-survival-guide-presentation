/*
 * Themes, discovered from src/themes/<name>/: frame.svg, cover.svg and
 * parts.html are inlined into the board chrome; theme.css, if present, is
 * bundled and scoped to :root[data-theme="<name>"].
 */

const files = import.meta.glob('./*/{frame.svg,cover.svg,parts.html}', {
  query: '?raw',
  import: 'default',
  eager: true,
});
import.meta.glob('./*/theme.css', { eager: true });

const themes = {};
for (const [path, source] of Object.entries(files)) {
  const [, name, file] = path.match(/^\.\/([^/]+)\/(\w+)\./);
  (themes[name] ??= { parts: '' })[file] = source;
}

// T cycles in this order, the first is the default; others follow alphabetically.
const PREFERRED = ['classic', 'hybrid', 'refined', 'alternative'];

const complete = (name) => themes[name]?.frame && themes[name]?.cover;

export const THEMES = [
  ...PREFERRED.filter(complete),
  ...Object.keys(themes).filter((name) => !PREFERRED.includes(name) && complete(name)).sort(),
];

export const themeLayers = (name) => themes[name];
