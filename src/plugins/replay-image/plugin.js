/*
 * reveal plugin: an animated image that plays from its first frame each time it is shown. The
 * <img> keeps a still in `src` and names the animation in `data-animated-src`; print and
 * reduced motion keep the still.
 */

// The browser shares one playing copy per URL, so only a new blob URL starts it again.
const blobs = new Map();
function blobFor(url) {
  if (!blobs.has(url)) blobs.set(url, fetch(url).then((r) => r.blob()));
  return blobs.get(url);
}

// As reveal shows it: a current-visible fragment only while it is the current one.
function isShown(img) {
  const f = img.closest('.fragment');
  if (!f) return true;
  return f.classList.contains('visible')
    && (!f.classList.contains('current-visible') || f.classList.contains('current-fragment'));
}

async function play(img) {
  const blob = await blobFor(img.dataset.animatedSrc);
  if (!img.dataset.playing) return; // hidden again before the file arrived
  const old = img.dataset.blobUrl;
  img.dataset.blobUrl = URL.createObjectURL(blob);
  // Hidden until its first frame decodes, so the still never flashes up first.
  img.style.visibility = 'hidden';
  img.src = img.dataset.blobUrl;
  await img.decode().catch(() => {});
  img.style.visibility = '';
  if (old) URL.revokeObjectURL(old);
}

export default () => ({
  id: 'replay-image',
  init(deck) {
    if (deck.isPrintView() || matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const sync = (event) => {
      for (const img of event?.previousSlide?.querySelectorAll('img[data-animated-src]') ?? []) {
        delete img.dataset.playing;
      }
      for (const img of deck.getCurrentSlide().querySelectorAll('img[data-animated-src]')) {
        blobFor(img.dataset.animatedSrc); // fetched on arrival, ready for the click
        if (!isShown(img)) delete img.dataset.playing;
        else if (!img.dataset.playing) {
          img.dataset.playing = 'yes';
          play(img);
        }
      }
    };
    for (const name of ['ready', 'slidechanged', 'fragmentshown', 'fragmenthidden']) deck.on(name, sync);
  },
});
