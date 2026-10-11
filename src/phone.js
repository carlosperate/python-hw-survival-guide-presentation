/*
 * Phones: in portrait a card asks to turn the phone sideways, with a Full
 * screen button where the browser allows it. iPhone Safari has no element
 * full screen, so iPhones get the card alone. Full screen locks landscape.
 */

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

function button(className, label, html) {
  const el = document.createElement('button');
  el.type = 'button';
  el.className = className;
  el.innerHTML = html ?? label;
  if (html) el.setAttribute('aria-label', label);
  return el;
}

export function mountPhoneView() {
  if (canFullscreen) root.classList.add('can-fullscreen');
  if (sessionStorage.getItem(DISMISSED)) root.classList.add('portrait-dismissed');

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
  anyway.addEventListener('click', () => {
    sessionStorage.setItem(DISMISSED, '1');
    root.classList.add('portrait-dismissed');
  });
  document.addEventListener('fullscreenchange', () => {
    root.classList.toggle('is-fullscreen', !!document.fullscreenElement);
    if (!document.fullscreenElement) screen.orientation?.unlock?.();
  });

  document.body.append(card, corner);
}
