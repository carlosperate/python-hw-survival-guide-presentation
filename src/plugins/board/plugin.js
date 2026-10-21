/*
 * reveal plugin: the PCB board behind the slides (frame, cover traces, parts,
 * QR, footer rail), the theme switch and the cover's idle pulse. It loads the
 * themes in src/themes, whose CSS comes after board.css and overrides it.
 */
import './board.css';
import { chooseTheme, mountBoardChrome } from './chrome.js';

export default () => ({
  id: 'board',
  init(deck) {
    // Before reveal's first layout, which gives the print pages their background.
    const theme = chooseTheme();
    // The board registers with the laid-out slide rectangle, so it waits for the deck.
    deck.on('ready', () => mountBoardChrome(deck, theme));
  },
});
