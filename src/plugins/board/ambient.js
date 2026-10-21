/*
  Idle life for cover slides, which stay up for minutes: every EVERY_MS a short
  bright pulse runs along one trace, each trace taking a turn before any repeats.
  The LED breathing is CSS in the theme. Off under reduced motion and in print.
*/

const FIRST_MS = 3000;
const EVERY_MS = 3000;
const SPEED = 520; // deck px per second
const DASH = 110;
const MIN_LENGTH = 160;

function shuffled(items) {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// Drawn single-run traces only: not mask outlines, nor the stub groups that
// are one path of many short moves.
function traces(board) {
  return [...board.querySelectorAll('.board__traces path')].filter(
    (p) =>
      !p.closest('defs, mask, symbol') &&
      (p.getAttribute('d').match(/M/gi) ?? []).length === 1 &&
      p.getTotalLength() >= MIN_LENGTH
  );
}

// Stacked runs centred on one point: the glow widens as it shortens, the core whitens as it
// shortens, so the pulse tapers to the trace's own width and colour at both ends.
const LAYERS = [
  { length: 0.95, grow: 1.5, glow: true },
  { length: 0.85, grow: 3, glow: true },
  { length: 0.74, grow: 4.5, glow: true },
  { length: 0.62, grow: 6, glow: true },
  { length: 0.5, grow: 7.5, glow: true },
  { length: 0.38, grow: 9, glow: true },
  { length: 1, grow: 0, mix: 75 },
  { length: 0.85, grow: 0.3, mix: 62 },
  { length: 0.7, grow: 0.6, mix: 50 },
  { length: 0.56, grow: 0.9, mix: 38 },
  { length: 0.43, grow: 1.2, mix: 26 },
  { length: 0.3, grow: 1.6, mix: 15 },
];

function run(path) {
  const length = path.getTotalLength();
  const stroke = path.closest('[stroke]').getAttribute('stroke');
  const width = parseFloat(getComputedStyle(path).strokeWidth);
  const duration = Math.max(1000, (length / SPEED) * 1000);

  let last = path;
  for (const layer of LAYERS) {
    const dash = DASH * layer.length;
    const el = path.cloneNode();
    el.classList.add('trace-pulse');
    if (layer.glow) el.classList.add('trace-pulse--glow');
    el.style.stroke = layer.glow ? stroke : `color-mix(in srgb, ${stroke} ${layer.mix}%, var(--pcb-silk))`;
    el.style.strokeWidth = `${width + layer.grow}px`;
    el.setAttribute('stroke-dasharray', `${dash} ${length + DASH}`);
    last.after(el);
    last = el;

    // The dash's centre runs from DASH / 2 before the start to DASH / 2 past the end.
    const at = (t) => (DASH + dash) / 2 - t * (length + DASH);
    el.animate(
      [
        { strokeDashoffset: at(0), opacity: 0 },
        { strokeDashoffset: at(0.1), opacity: 1, offset: 0.1 },
        { strokeDashoffset: at(0.85), opacity: 1, offset: 0.85 },
        { strokeDashoffset: at(1), opacity: 0 },
      ],
      { duration }
    ).finished.then(() => el.remove(), () => el.remove());
  }
}

export function startAmbient(deck, board) {
  if (deck.isPrintView() || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  let timer;
  let queue = [];
  let last;

  function next() {
    const live = traces(board);
    queue = queue.filter((p) => live.includes(p));
    if (!queue.length) {
      queue = shuffled(live);
      if (queue[0] === last && queue.length > 1) queue.push(queue.shift());
    }
    last = queue.shift();
    if (last) run(last);
    timer = setTimeout(next, EVERY_MS);
  }

  function sync() {
    clearTimeout(timer);
    board.querySelectorAll('.trace-pulse').forEach((s) => s.remove());
    if (board.dataset.board === 'cover') timer = setTimeout(next, FIRST_MS);
  }

  // Registered after the chrome's own handler, so board.dataset.board is current.
  deck.on('slidechanged', sync);
  sync();
}
