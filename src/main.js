import Reveal from 'reveal.js';
import Notes from 'reveal.js/plugin/notes';
import Highlight from 'reveal.js/plugin/highlight';

import './fonts.js';

import 'reveal.js/reset.css';
import 'reveal.js/reveal.css';
import './styles/presentation.css';

// The deck's own plugins, each a folder bringing its CSS after the shared
// styles. Board comes last: it loads the themes, whose CSS overrides the rest.
import HeapMap from './plugins/heap-map/plugin.js';
import Phone from './plugins/phone/plugin.js';
import Magnifier from './plugins/magnifier/plugin.js';
import Board from './plugins/board/plugin.js';

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
  // Phones keep the slides; portrait gets the turn-sideways card instead of
  // reveal's scroll view, which shrinks text to 7-9px.
  scrollActivationWidth: null,
  plugins: [Notes, Highlight, HeapMap, Phone, Magnifier, Board],
});

deck.initialize();
