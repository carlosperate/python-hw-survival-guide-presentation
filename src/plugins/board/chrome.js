import { THEMES, themeLayers } from '../../themes/index.js';
import { startAmbient } from './ambient.js';

/*
 * Draws the PCB chrome behind the deck and keeps it registered with reveal's
 * slide rectangle, so the artwork's 1280x720 coordinates and the slides'
 * coordinates are the same coordinates.
 *
 * Also owns the theme switch: T cycles through src/themes and 1-9 pick one.
 * It reads ?theme= too, so two windows can be opened side by side, and it
 * remembers the last choice.
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
      <img src="${import.meta.env.BASE_URL}images/qr.svg" alt="" />
      <span class="board__qr-label">${head}${tail}</span>
    </div>`;
}

const railNumber = (number, total) =>
  `${String(number).padStart(2, '0')}<span> / ${String(total).padStart(2, '0')}</span>`;

/* The rail counts horizontal slides only. Export flattens vertical slides into
   pages, so each slide records its horizontal number before reveal lays out. */
export function numberHorizontalSlides(revealEl) {
  revealEl.querySelectorAll('.slides > section').forEach((h, i) => {
    for (const slide of [h, ...h.querySelectorAll(':scope > section')]) slide.dataset.railNumber = i + 1;
  });
}

/* Export lays every slide out as a page at once, so each page gets a board of
   its own, between the page's background and its slide. */
function printBoards(board) {
  const pages = [...document.querySelectorAll('.pdf-page')];
  const slides = pages.map((page) => page.querySelector(':scope > section'));
  const total = Math.max(...slides.map((slide) => Number(slide.dataset.railNumber)));
  pages.forEach((page, i) => {
    const slide = slides[i];
    const copy = board.cloneNode(true);
    copy.dataset.board = slide.dataset.board ?? 'plain';
    copy.style.left = slide.style.left;
    copy.style.top = slide.style.top;
    copy.querySelector('.board__rail-number').innerHTML = railNumber(slide.dataset.railNumber, total);
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

// Saved only when chosen, with ?theme=, T or a number key, so a new default reaches every other browser.
const THEME_KEY = 'pcb:theme-choice';

// A base theme's CSS is scoped by data-base-theme, so it also styles the themes built on it.
function markTheme(name) {
  document.documentElement.dataset.theme = name;
  document.documentElement.dataset.baseTheme = themeLayers(name).base;
}

export function chooseTheme() {
  const fromUrl = new URLSearchParams(location.search).get('theme');
  if (THEMES.includes(fromUrl)) store(THEME_KEY, fromUrl);
  const name = [fromUrl, stored(THEME_KEY)].find((option) => THEMES.includes(option)) ?? THEMES[0];
  markTheme(name);
  return name;
}

export function mountBoardChrome(deck, startTheme) {
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

  let theme = startTheme;

  function applyTheme(name) {
    const { frame, cover, parts } = themeLayers(name);
    frameEl.innerHTML = frame;
    tracesEl.innerHTML = cover;
    partsEl.innerHTML = parts;
    markTheme(name);
    // Themes change type sizes and gutters; let reveal re-measure.
    deck.layout();
  }

  function toast() {
    toastEl.innerHTML = `theme <b>${theme}</b>`;
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('is-visible'), TOAST_MS);
  }

  function switchTheme(name) {
    theme = name;
    applyTheme(name);
    store(THEME_KEY, name);
    toast();
    // Keep the URL shareable: reloading or copying it keeps the theme.
    const url = new URL(location.href);
    url.searchParams.set('theme', name);
    history.replaceState(history.state, '', url);
  }

  function sync() {
    const slide = deck.getCurrentSlide();
    board.dataset.board = slide?.dataset.board ?? 'plain';

    numberEl.innerHTML = railNumber(deck.getIndices().h + 1, deck.getHorizontalSlides().length);
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

  applyTheme(theme);
  if (deck.isPrintView()) {
    // The pages exist only once reveal has laid the export out.
    if (document.querySelector('.pdf-page')) printBoards(board);
    else deck.on('pdf-ready', () => printBoards(board));
    return;
  }

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
    () => switchTheme(THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length])
  );
  // In T's order, so the numbers follow PREFERRED in src/themes/index.js.
  THEMES.slice(0, 9).forEach((name, i) => {
    deck.addKeyBinding(
      { keyCode: 49 + i, key: String(i + 1), description: `Theme: ${name}` },
      () => switchTheme(name)
    );
  });

  // board.css places it from reveal's --slide-scale, which reveal's layout has set by 'ready'.
  board.classList.add('is-placed');
  sync();
  startAmbient(deck, board);
}
