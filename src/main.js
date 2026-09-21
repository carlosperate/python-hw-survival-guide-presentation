import Reveal from 'reveal.js';
import Notes from 'reveal.js/plugin/notes';
import Highlight from 'reveal.js/plugin/highlight';

import 'reveal.js/reveal.css';
import 'reveal.js/theme/black.css';
import 'reveal.js/plugin/highlight/monokai.css';

import './styles/presentation.css';

const deck = new Reveal({
  // 16:9 for the projector; reveal's default is 960x700.
  width: 1280,
  height: 720,
  hash: true,
  // A reload lands on the same slide and fragment.
  fragmentInURL: true,
  transition: 'fade',
  plugins: [Notes, Highlight],
});

deck.initialize();
