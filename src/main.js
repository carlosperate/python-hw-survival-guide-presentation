import Reveal from 'reveal.js';
import Notes from 'reveal.js/plugin/notes';
import Highlight from 'reveal.js/plugin/highlight';

import './fonts.js';

import 'reveal.js/reset.css';
import 'reveal.js/reveal.css';
import './styles/presentation.css';

import { mountBoardChrome } from './board/chrome.js';

const deck = new Reveal({
  // 16:9 for the projector; reveal's default is 960x700.
  width: 1280,
  height: 720,
  hash: true,
  // A reload lands on the same slide and fragment.
  fragmentInURL: true,
  // Slides lay themselves out from the top; `.is-centered` opts back in.
  center: false,
  // Reveal writes this inline onto the visible slide, so it is the only place
  // the slide's own layout mode can be set.
  display: 'flex',
  transition: 'fade',
  transitionSpeed: 'fast',
  backgroundTransition: 'fade',
  autoAnimateDuration: 0.55,
  autoAnimateUnmatched: false,
  plugins: [Notes, Highlight],
});

await deck.initialize();

// Chrome does not reliably repaint inline SVG <text> when a webfont arrives
// after the SVG was first rasterised, which silently blanks the pin-header and
// LED labels. Inserting the chrome once fonts have settled avoids the race.
await document.fonts.ready;
mountBoardChrome(deck);

export { deck };
