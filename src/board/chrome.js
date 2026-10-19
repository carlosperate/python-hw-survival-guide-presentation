import { THEMES, themeLayers } from '../themes/index.js';
import { startAmbient } from './ambient.js';

/*
 * Draws the PCB chrome behind the deck and keeps it registered with reveal's
 * slide rectangle, so the artwork's 1280x720 coordinates and the slides'
 * coordinates are the same coordinates.
 *
 * Also owns the theme switch: T cycles through src/themes. It reads ?theme=
 * too, so two windows can be opened side by side, and it remembers the last
 * choice.
 */

const PULSE_MS = 240;
const RAIL_PULSE_MS = 460;
const TOAST_MS = 1800;

/* Chrome rather than slide markup, so every slide carries it: large on the
   cover, small in the corner everywhere else. public/images/qr.svg must encode
   data-deck-url; regenerate it if the URL changes. */
function qr(revealEl) {
  const url = revealEl.dataset.deckUrl ?? '';
  // "https://" opens the first line and the second starts with a dot, so both read as one URL.
  const [head, ...rest] = url.split('.');
  const tail = rest.length ? `<br>.${rest.join('.')}` : '';
  return `
    <div class="board__qr">
      <img src="/images/qr.svg" alt="" />
      <span class="board__qr-label">${head}${tail}</span>
    </div>`;
}

const railNumber = (number, total) =>
  `${String(number).padStart(2, '0')}<span> / ${String(total).padStart(2, '0')}</span>`;

/* Export lays every slide out as a page at once, so each page gets a board of
   its own, between the page's background and its slide. */
function printBoards(board) {
  const pages = [...document.querySelectorAll('.pdf-page')];
  // Reveal follows each slide's page with a copy per fragment step; only the first shows none.
  let count = 0;
  const numbers = pages.map((page) => (page.querySelector('.fragment.visible') ? count : ++count));
  pages.forEach((page, i) => {
    const slide = page.querySelector(':scope > section');
    const copy = board.cloneNode(true);
    copy.dataset.board = slide.dataset.board ?? 'plain';
    copy.style.left = slide.style.left;
    copy.style.top = slide.style.top;
    copy.querySelector('.board__rail-number').innerHTML = railNumber(numbers[i], count);
    page.insertBefore(copy, slide);
  });
  board.remove();
}

function stored(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null; // private browsing
  }
}

function store(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private browsing */
  }
}

function initial(param, options) {
  const fromUrl = new URLSearchParams(location.search).get(param);
  if (options.includes(fromUrl)) return fromUrl;

  const saved = stored(`pcb:${param}`);
  return options.includes(saved) ? saved : options[0];
}

// Set before reveal's first layout, which gives the print pages their background.
const startTheme = initial('theme', THEMES);
document.documentElement.dataset.theme = startTheme;

export function mountBoardChrome(deck) {
  const revealEl = deck.getRevealElement();

  const board = document.createElement('div');
  board.className = 'board';
  board.setAttribute('aria-hidden', 'true');
  board.innerHTML = `
    <div class="board__frame"></div>
    <div class="board__art">
      <div class="board__traces"></div>
      <div class="board__parts"></div>
    </div>
    ${qr(revealEl)}
    <div class="board__rail">
      <span class="board__rail-trace"></span>
      <span class="board__rail-number"></span>
    </div>
    <div class="board__toast"></div>`;
  revealEl.before(board);

  const frameEl = board.querySelector('.board__frame');
  const tracesEl = board.querySelector('.board__traces');
  const partsEl = board.querySelector('.board__parts');
  const numberEl = board.querySelector('.board__rail-number');
  const toastEl = board.querySelector('.board__toast');

  const pulses = new Map();
  let toastTimer;

  const current = { theme: startTheme };

  function applyTheme(name) {
    const { frame, cover, parts } = themeLayers(name);
    frameEl.innerHTML = frame;
    tracesEl.innerHTML = cover;
    partsEl.innerHTML = parts;
    document.documentElement.dataset.theme = name;
    store('pcb:theme', name);
    // Themes change type sizes and gutters; let reveal re-measure.
    deck.layout();
  }

  function toast() {
    toastEl.innerHTML = `theme <b>${current.theme}</b>`;
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('is-visible'), TOAST_MS);
  }

  function cycle(axis, options, apply) {
    const next = options[(options.indexOf(current[axis]) + 1) % options.length];
    current[axis] = next;
    apply(next);
    toast();
    // Keep the URL shareable: reloading or copying it keeps the theme.
    const url = new URL(location.href);
    url.searchParams.set(axis, next);
    history.replaceState(history.state, '', url);
  }

  /* Reveal centres the slide rectangle in the viewport, so deriving the
     position from the scale is independent of how `.slides` is boxed. */
  function place() {
    const { width, height } = deck.getConfig();
    const viewport = deck.getViewportElement().getBoundingClientRect();
    const scale = deck.getScale() || 1;

    board.style.left = `${viewport.left + (viewport.width - width * scale) / 2}px`;
    board.style.top = `${viewport.top + (viewport.height - height * scale) / 2}px`;
    board.style.transform = `scale(${scale})`;
    board.classList.add('is-placed');
  }

  function sync() {
    const slide = deck.getCurrentSlide();
    board.dataset.board = slide?.dataset.board ?? 'plain';

    numberEl.innerHTML = railNumber(deck.getSlidePastCount() + 1, deck.getTotalSlides());
  }

  // Restarts the rail pulse; `dir` is the way the deck just moved between slides.
  let pulseTimer;
  function railPulse(dir) {
    board.classList.remove('is-step-fwd', 'is-step-back');
    void board.offsetWidth;
    board.classList.add(`is-step-${dir}`);
    clearTimeout(pulseTimer);
    pulseTimer = setTimeout(() => board.classList.remove(`is-step-${dir}`), RAIL_PULSE_MS);
  }

  function pulse(state) {
    board.classList.add(state);
    clearTimeout(pulses.get(state));
    pulses.set(state, setTimeout(() => board.classList.remove(state), PULSE_MS));
  }

  applyTheme(current.theme);
  if (deck.isPrintView()) {
    // The pages exist only once reveal has laid the export out.
    if (document.querySelector('.pdf-page')) printBoards(board);
    else deck.on('pdf-ready', () => printBoards(board));
    return;
  }

  deck.on('resize', place);
  deck.on('slidechanged', (event) => {
    sync();
    pulse('is-rx');
    const was = event.previousSlide ? deck.getIndices(event.previousSlide) : null;
    if (was) railPulse(event.indexh > was.h || (event.indexh === was.h && event.indexv > was.v) ? 'fwd' : 'back');
  });
  deck.on('fragmentshown', () => pulse('is-tx'));
  deck.on('fragmenthidden', () => pulse('is-rx'));

  // The overview grid has its own geometry; the chrome does not belong there.
  deck.on('overviewshown', () => board.classList.add('is-hidden'));
  deck.on('overviewhidden', () => board.classList.remove('is-hidden'));

  deck.addKeyBinding(
    { keyCode: 84, key: 'T', description: 'Next theme' },
    () => cycle('theme', THEMES, applyTheme)
  );

  place();
  sync();
  startAmbient(deck, board);
}
