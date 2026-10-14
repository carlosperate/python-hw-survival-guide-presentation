/*
  Idle life for cover slides, which stay up for minutes: every EVERY_MS a short
  bright pulse runs along one trace, each trace taking a turn before any repeats.
  The LED breathing is CSS in the theme. Off under reduced motion and in print.
*/

const FIRST_MS = 4000;
const EVERY_MS = 5000;
const SPEED = 520; // deck px per second
const DASH = 70;
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

function run(path) {
  const length = path.getTotalLength();
  const stroke = path.closest('[stroke]').getAttribute('stroke');
  const spark = path.cloneNode();
  spark.classList.add('trace-pulse');
  spark.style.stroke = `color-mix(in srgb, ${stroke} 45%, var(--pcb-silk))`;
  spark.setAttribute('stroke-dasharray', `${DASH} ${length + DASH}`);
  path.after(spark);

  const at = (t) => DASH - t * (length + DASH);
  spark
    .animate(
      [
        { strokeDashoffset: at(0), opacity: 0 },
        { strokeDashoffset: at(0.1), opacity: 1, offset: 0.1 },
        { strokeDashoffset: at(0.85), opacity: 1, offset: 0.85 },
        { strokeDashoffset: at(1), opacity: 0 },
      ],
      { duration: Math.max(1000, (length / SPEED) * 1000) }
    )
    .finished.then(() => spark.remove(), () => spark.remove());
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
