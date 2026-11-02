/*
 * reveal plugin: the reTerminal Sticky badge over Web Bluetooth. B connects it; arriving on a
 * slide sends its `data-ble-badge` trigger and a fragment shown sends its own. Off in print, in
 * an iframe (the speaker view's previews), without Web Bluetooth and with ?ble-badge=0.
 */
import './ble-badge.css';
import { StickyLink } from '../../../micropython-badge/web/link.js';
import triggers from '../../../micropython-badge/triggers.json';

const KEY_B = 66;
const TOAST_MS = 1800;

// A slide names a trigger; the Sticky gets its line. Names are unique across the groups.
const LINES = new Map(Object.values(triggers).flatMap(Object.entries));

function warnUnknown(deck) {
  for (const el of deck.getSlidesElement().querySelectorAll('[data-ble-badge]')) {
    if (!LINES.has(el.dataset.bleBadge)) {
      console.warn(`ble-badge: no trigger "${el.dataset.bleBadge}" in triggers.json`, el);
    }
  }
}

function mountToast(deck) {
  const el = document.createElement('div');
  el.className = 'ble-badge__toast';
  el.setAttribute('role', 'status');
  deck.getRevealElement().append(el);
  let timer;
  return (state) => {
    el.innerHTML = `badge <b>${state}</b>`;
    el.classList.add('is-visible');
    clearTimeout(timer);
    timer = setTimeout(() => el.classList.remove('is-visible'), TOAST_MS);
  };
}

export default () => ({
  id: 'ble-badge',
  init(deck) {
    if (deck.isPrintView() || window.self !== window.top) return;

    // Landing on a slide mid-way, reveal shows its fragments before `slidechanged`: those
    // `fragmentshown` belong to the arrival, which sends the slide's trigger only.
    let arrived = null;
    deck.on('ready', () => {
      warnUnknown(deck);
      arrived = deck.getCurrentSlide();
    });

    const off = new URLSearchParams(location.search).get('ble-badge') === '0';
    if (off || !navigator.bluetooth) return;

    const link = new StickyLink(navigator.bluetooth);
    link.addEventListener('error', (e) => console.warn('ble-badge:', e.detail));
    const toast = mountToast(deck);

    // A keydown is a user gesture, which the chooser needs. Reconnects are the link's own.
    deck.addKeyBinding({ keyCode: KEY_B, key: 'B', description: 'Connect the Sticky badge' }, () => {
      if (link.status !== 'off') {
        toast(link.status === 'connected' ? 'already connected' : link.status);
        return;
      }
      // A cancelled chooser and Bluetooth turned off both reject with NotFoundError.
      link.connect().then(
        () => {
          toast('connected');
          send(deck.getCurrentSlide().dataset.bleBadge); // as if the slide had just arrived
        },
        (e) => {
          toast('not connected');
          console.warn('ble-badge:', e);
        },
      );
    });

    // Every line fits one write (test_scenes.py), so trigger() never throws here.
    function send(name) {
      const line = LINES.get(name);
      if (line) link.trigger(line);
    }

    deck.on('slidechanged', ({ currentSlide }) => {
      arrived = currentSlide;
      send(currentSlide.dataset.bleBadge);
    });
    deck.on('fragmentshown', ({ fragments }) => {
      if (deck.getCurrentSlide() !== arrived) return;
      // Several at once (a jump within the slide): the newest wins, as on the link.
      send(fragments.findLast((el) => el.dataset.bleBadge)?.dataset.bleBadge);
    });
  },
});
