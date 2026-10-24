/*
 * reveal plugin: a magnifying lens while M is held. The whole page zooms about
 * the pointer and everything outside a circle round it dims, so the lens shows
 * the live slide and board, never a copy of them. Off in print.
 */
import './magnifier.css';

const KEY = 77; // M
const DIAMETER = 360; // deck px, so the lens covers the same share of the slide on any screen

const root = document.documentElement;

export default () => ({
  id: 'magnifier',
  init(deck) {
    if (deck.isPrintView()) return;

    const body = document.body;
    const lens = document.createElement('div');
    lens.className = 'magnifier';
    body.append(lens);

    let on = false;
    let zoomed = false; // from M down until the zoom-out has finished
    let x = innerWidth / 2;
    let y = innerHeight / 2;
    let frame = 0;

    // The zoom's origin is the pointer, so the point under it stays put; in the
    // zoomed body that point is still at (x, y), which is where the lens goes.
    function place() {
      frame = 0;
      body.style.transformOrigin = `${x}px ${y}px`;
      lens.style.translate = `${x}px ${y}px`;
    }

    function size() {
      lens.style.setProperty('--magnifier-diameter', `${DIAMETER * deck.getScale()}px`);
    }

    function show() {
      if (on || deck.isOverview()) return;
      on = zoomed = true;
      size();
      place();
      root.classList.add('is-magnifying');
    }

    function hide() {
      on = false;
      root.classList.remove('is-magnifying');
    }

    document.addEventListener(
      'pointermove',
      (event) => {
        x = event.clientX;
        y = event.clientY;
        // Still followed while zooming out, so pressing M again then doesn't jump.
        if (zoomed && !frame) frame = requestAnimationFrame(place);
      },
      { passive: true }
    );
    body.addEventListener('transitionend', (event) => {
      if (event.target === body && event.propertyName === 'scale' && !on) zoomed = false;
    });
    deck.on('resize', size);

    deck.addKeyBinding({ keyCode: KEY, key: 'M', description: 'Magnifier (hold)' }, show);
    // reveal reports key presses only, so letting go of M needs a listener of its own.
    document.addEventListener('keyup', (event) => {
      if (event.keyCode === KEY) hide();
    });
    // A key let go in another window never reaches this one.
    window.addEventListener('blur', hide);
    deck.on('overviewshown', hide);
  },
});
