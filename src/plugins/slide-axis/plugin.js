/*
 * reveal plugin: slides move the way you travel. Up and down a stack they
 * slide vertically, sideways out of or into a vertical slide horizontally;
 * horizontal to horizontal keeps the fade. Off in print and reduced motion.
 */
const SLIDE = 'slide';

export default () => ({
  id: 'slide-axis',
  init(deck) {
    if (deck.isPrintView() || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    for (const section of deck.getSlidesElement().querySelectorAll(':scope > section > section')) {
      section.dataset.transition ??= SLIDE;
    }

    // The incoming slide must already rest off to its side, or it only fades in.
    function setTransition(section, transition) {
      if (!section || (section.dataset.transition ?? null) === transition) return;
      section.classList.add('no-transition');
      if (transition) section.dataset.transition = transition;
      else delete section.dataset.transition;
      void getComputedStyle(section).transform;
      section.classList.remove('no-transition');
    }

    // Runs before reveal swaps the past, present and future classes.
    deck.on('beforeslidechange', ({ indexh: h, indexv: v }) => {
      const from = deck.getIndices();
      if (!deck.isReady() || deck.isOverview() || h === from.h) return;

      const tops = deck.getHorizontalSlides();
      // Left and right leave v unset, and reveal resumes a stack where it was left.
      const toV = v || Number(tops[h]?.dataset.previousIndexv) || 0;
      const transition = from.v > 0 || toV > 0 ? SLIDE : null;
      setTransition(tops[from.h], transition);
      setTransition(tops[h], transition);
    });
  },
});
