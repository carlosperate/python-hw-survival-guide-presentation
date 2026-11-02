import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig } from 'vite';

const INCLUDE = /<!--\s*@include\s+(\S+)\s*-->/g;

/*
 * Inlines `<!-- @include path -->` into the HTML entry pages, and into included files in
 * turn, so the deck can live in one file per part (and its art in files of its
 * own) while reveal and the build still see a single plain HTML page.
 * Runs before Vite's own HTML pass, so asset URLs in included files resolve.
 */
function htmlIncludes() {
  let root;
  const included = new Set();

  function inline(html, chain) {
    return html.replace(INCLUDE, (_, file) => {
      const path = resolve(root, file);
      if (chain.includes(path)) throw new Error(`@include loop: ${[...chain, path].join(' -> ')}`);
      included.add(path);
      return inline(readFileSync(path, 'utf8'), [...chain, path]);
    });
  }

  return {
    name: 'html-includes',
    configResolved(config) {
      root = config.root;
    },
    transformIndexHtml: {
      order: 'pre',
      handler(html) {
        return inline(html, []);
      },
    },
    // Vite only reloads for the .html page being viewed, not for its partials.
    handleHotUpdate({ file, server }) {
      if (!included.has(file)) return;
      server.ws.send({ type: 'full-reload' });
      return [];
    },
  };
}

export default defineConfig({
  plugins: [htmlIncludes()],
  // Polling catches edits from sandboxed tools when filesystem events are missed. The badge's
  // MicroPython checkout is ignored: polling its 100k files would stall the server.
  server: {
    watch: {
      usePolling: true,
      interval: 250,
      ignored: ['**/micropython-badge/micropython-reterminal-sticky/**'],
    },
  },
  build: {
    rollupOptions: {
      input: {
        landing: resolve(import.meta.dirname, 'index.html'),
        presentation: resolve(import.meta.dirname, 'presentation.html'),
      },
    },
  },
});
