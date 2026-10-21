/*
 * reveal plugin: draws <pre class="heap-map"> text as a grid of heap blocks, one
 * character per 16-byte block as micropython.mem_info(1) prints them. Runs in
 * init, before reveal indexes fragments, because a heap map can be one.
 */
import './heap-map.css';

const KINDS = {
  '.': 'free',
  A: 'array',
  F: 'float',
  S: 'str',
  x: 'garbage', // not a MicroPython letter: unreachable, not yet swept
};

function render(root) {
  for (const pre of root.querySelectorAll('pre.heap-map')) {
    const rows = pre.textContent.trim().split('\n').map((row) => row.trim());
    const grid = document.createElement('div');

    grid.className = pre.className.replace('heap-map', 'heap');
    Object.assign(grid.dataset, pre.dataset);
    grid.style.setProperty('--cols', rows[0].length);
    grid.setAttribute('role', 'img');
    grid.setAttribute('aria-label', pre.getAttribute('aria-label') ?? 'Heap blocks');

    // '=' continues the object whose head came before it, as in mem_info(1).
    let kind = 'free';
    for (const ch of rows.join('')) {
      if (ch !== '=') kind = KINDS[ch] ?? 'other';
      const cell = document.createElement('span');
      cell.className = `heap__cell heap__cell--${kind}`;
      grid.append(cell);
    }

    pre.replaceWith(grid);
  }
}

export default () => ({
  id: 'heap-map',
  init(deck) {
    render(deck.getSlidesElement());
  },
});
