// Writes public/images/social-card.jpg, the link-preview image index.html names in
// its og:image tag: the cover slide in the default theme, at the 1200x630 the cards use.
// Needs the dev server: npm run dev, then node scripts/social-card.mjs
import { chromium } from 'playwright';

const URL = 'http://localhost:5173/presentation?theme=hybrid-matte#/0';
const OUT = new globalThis.URL('../public/images/social-card.jpg', import.meta.url).pathname;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, reducedMotion: 'reduce' });
await page.goto(URL);
await page.waitForTimeout(2500);
// Navigation and the progress bar mean nothing in a still.
await page.addStyleTag({ content: '.reveal .controls, .reveal .progress, .fullscreen-corner { display: none !important; }' });
await page.waitForTimeout(300);
// JPEG: messaging apps drop preview images much over 300 KB.
await page.screenshot({ path: OUT, type: 'jpeg', quality: 85 });
await browser.close();
console.log(`wrote ${OUT}`);
