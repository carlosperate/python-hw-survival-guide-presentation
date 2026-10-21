/*
 * reveal plugin: phone viewing. Portrait gets a card asking to turn the phone,
 * with Full screen where the browser allows it (not iPhone Safari, which has no
 * element full screen). Full screen locks landscape.
 */
import './phone.css';

const DISMISSED = 'pcb:portrait-dismissed';
const root = document.documentElement;
const canFullscreen = document.fullscreenEnabled || document.webkitFullscreenEnabled;

const ROTATE_ICON = `
  <svg viewBox="0 0 64 64" aria-hidden="true">
    <rect x="22" y="8" width="20" height="36" rx="3" class="phone-card__before" />
    <rect x="10" y="38" width="36" height="20" rx="3" class="phone-card__after" />
    <path d="M48 20a14 14 0 0 1 4 12M48 32l4 1 1-4" class="phone-card__arrow" />
  </svg>`;

const FULLSCREEN_ICON = `
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" />
  </svg>`;

async function enterFullscreen() {
  await (root.requestFullscreen?.({ navigationUI: 'hide' }) ?? root.webkitRequestFullscreen?.());
  // Only allowed in full screen, and refused by some browsers; the card covers that.
  await screen.orientation?.lock?.('landscape').catch(() => {});
}

// Blocked storage throws; the card then simply returns on the next load.
function dismissed() {
  try {
    return sessionStorage.getItem(DISMISSED);
  } catch {
    return null;
  }
}

function dismiss() {
  root.classList.add('portrait-dismissed');
  try {
    sessionStorage.setItem(DISMISSED, '1');
  } catch {
    /* blocked */
  }
}

function button(className, label, html) {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = className;
  el.innerHTML = html ?? label;
  if (html) el.setAttribute('aria-label', label);
  return el;
}

function mount() {
  if (canFullscreen) root.classList.add('can-fullscreen');
  if (dismissed()) root.classList.add('portrait-dismissed');

  const card = document.createElement('div');
  card.className = 'phone-card';
  card.setAttribute('role', 'dialog');
  card.setAttribute('aria-modal', 'true');
  card.setAttribute('aria-labelledby', 'phone-card-text');
  card.innerHTML = `${ROTATE_ICON}<p id="phone-card-text">Turn your phone sideways to follow the slides.</p>`;

  const full = button('phone-card__fullscreen', 'Full screen');
  const anyway = button('phone-card__anyway', 'Show anyway');
  card.append(full, anyway);

  const corner = button('fullscreen-corner', 'Full screen', FULLSCREEN_ICON);

  full.addEventListener('click', enterFullscreen);
  corner.addEventListener('click', enterFullscreen);
  anyway.addEventListener('click', dismiss);
  document.addEventListener('fullscreenchange', () => {
    root.classList.toggle('is-fullscreen', !!document.fullscreenElement);
    if (!document.fullscreenElement) screen.orientation?.unlock?.();
  });

  document.body.append(card, corner);
}

// Needs nothing from reveal, so it mounts straight away: the card shows before the deck is ready.
export default () => ({
  id: 'phone',
  init() {
    mount();
  },
});
