/*
 * Screenshots the running deck in Chromium, Firefox and WebKit at desktop and
 * phone sizes, and reports how large body text ends up on each screen.
 * Needs `npm run dev` running. See AGENTS.md, "Testing in browsers".
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium, firefox, webkit } from 'playwright';

// Phone sizes from StatCounter (Spain, Europe and worldwide, Sep 2026) and
// DeviceAtlas (May 2026). Sizes are CSS pixels.
const DEVICES = {
  'projector':        { width: 1280, height: 720 },
  'laptop':           { width: 1440, height: 900, dpr: 2 },
  'iphone-11-class':  { width: 414, height: 896, dpr: 2, mobile: true },
  'galaxy-a-ultra':   { width: 384, height: 832, dpr: 2.8125, mobile: true },
  'android-budget':   { width: 360, height: 800, dpr: 3, mobile: true },
  'redmi-xiaomi':     { width: 393, height: 873, dpr: 2.75, mobile: true },
  'iphone-12-16e':    { width: 390, height: 844, dpr: 3, mobile: true },
  'iphone-17':        { width: 402, height: 874, dpr: 3, mobile: true },
  'galaxy-s-base':    { width: 360, height: 780, dpr: 3, mobile: true },
  'pixel':            { width: 412, height: 915, dpr: 2.625, mobile: true },
  'iphone-pro-max':   { width: 440, height: 956, dpr: 3, mobile: true },
  'zoomed-320':       { width: 320, height: 693, dpr: 3, mobile: true },
};

// Every phone is tested both ways up.
for (const [name, d] of Object.entries(DEVICES)) {
  if (d.mobile) DEVICES[`${name}-landscape`] = { ...d, width: d.height, height: d.width };
}

const GROUPS = {
  desktop: ['projector', 'laptop'],
  phones: Object.keys(DEVICES).filter((name) => DEVICES[name].mobile),
};
GROUPS.portrait = GROUPS.phones.filter((name) => !name.endsWith('-landscape'));
GROUPS.landscape = GROUPS.phones.filter((name) => name.endsWith('-landscape'));
GROUPS.all = [...GROUPS.desktop, ...GROUPS.phones];

const BROWSERS = { chromium, firefox, webkit };

// Cover, divider, heap grid, waveform end state, table, card row.
const DEFAULT_SLIDES = ['0', '30', '16/0/4', '25/0/12', '20', '48'];

// Below this, body text is unreadable on the screen it lands on.
const MIN_BODY_PX = 12;
const BODY_PX = 27;

function args() {
  const opts = { browsers: 'chromium,firefox,webkit', devices: 'all', slides: '', theme: 'hybrid',
    base: 'http://localhost:5173', out: '.screenshots' };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i += 2) opts[argv[i].replace(/^--/, '')] = argv[i + 1];
  return opts;
}

async function slideList(browser, opts) {
  if (opts.slides && opts.slides !== 'all') return opts.slides.split(',');
  if (!opts.slides) return DEFAULT_SLIDES;
  const page = await browser.newPage();
  await page.goto(`${opts.base}/?theme=${opts.theme}`);
  const count = await page.locator('.reveal .slides > section').count();
  await page.close();
  return Array.from({ length: count }, (_, i) => String(i));
}

async function check(name, opts, slides, results) {
  const browser = await BROWSERS[name].launch();
  const deviceNames = GROUPS[opts.devices] ?? opts.devices.split(',');

  for (const device of deviceNames) {
    const d = DEVICES[device];
    const context = await browser.newContext({
      viewport: { width: d.width, height: d.height },
      deviceScaleFactor: d.dpr ?? 1,
      // Firefox has no mobile emulation in Playwright; it gets the size only.
      ...(d.mobile && name !== 'firefox' ? { isMobile: true, hasTouch: true } : {}),
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (msg) => msg.type() === 'error' && errors.push(msg.text()));

    const dir = `${opts.out}/${name}/${device}`;
    await mkdir(dir, { recursive: true });

    let n = 0;
    for (const slide of slides) {
      // A changed query forces a real load; a hash-only change would not.
      const url = `${opts.base}/?theme=${opts.theme}&r=${n++}#/${slide}`;
      // Vite restarts when dependencies change; give it one more chance.
      await page.goto(url).catch(() => page.waitForTimeout(3000).then(() => page.goto(url)));
      await page.locator('.reveal.ready').waitFor({ timeout: 10000 }).catch(() => {});
      await page.waitForTimeout(1500);
      // Below scrollActivationWidth reveal swaps the deck for a scrolling page.
      const view = await page.evaluate(() => {
        const scroll = document.querySelector('.reveal-viewport')?.classList.contains('reveal-scroll') ?? false;
        const onScreen = [...document.querySelectorAll('.reveal .slides section')]
          .map((el) => el.getBoundingClientRect())
          .find((r) => r.width > 0 && r.bottom > 0 && r.top < innerHeight);
        // The board is only really there if its frame is on screen.
        const frame = document.querySelector('.board__frame')?.getBoundingClientRect();
        const board = document.querySelector('.board');
        const chrome = !!frame && !scroll && board.classList.contains('is-placed')
          && getComputedStyle(board).opacity !== '0' && frame.width > 0;
        const card = document.querySelector('.phone-card');
        const covered = !!card && getComputedStyle(card).display !== 'none';
        return { scroll, scale: onScreen ? onScreen.width / 1280 : 0, chrome, covered, hash: location.hash };
      });
      await page.screenshot({ path: `${dir}/${slide.replaceAll('/', '-')}.png` });
      results.push({ browser: name, device, slide, view: view.scroll ? 'scroll' : 'slides',
        scale: +view.scale.toFixed(3), bodyPx: +(BODY_PX * view.scale).toFixed(1),
        chrome: view.chrome, covered: view.covered, landedOn: view.hash });
    }
    results.push({ browser: name, device, errors });
    await context.close();
  }
  await browser.close();
}

const opts = args();
try {
  await fetch(opts.base);
} catch {
  console.error(`Nothing at ${opts.base}. Start the deck with npm run dev first.`);
  process.exit(1);
}

const results = [];
const probe = await chromium.launch();
const slides = await slideList(probe, opts);
await probe.close();

for (const name of opts.browsers.split(',')) await check(name, opts, slides, results);

await writeFile(`${opts.out}/report.json`, JSON.stringify(results, null, 2));

const rows = results.filter((r) => r.slide === slides[0]);
console.log('browser   device                       view    scale  body   chrome');
for (const r of rows) {
  // In portrait the turn-sideways card covers the slides; the size applies after "Show anyway".
  const flag = r.covered ? '  behind the turn-sideways card' : r.bodyPx < MIN_BODY_PX ? '  too small' : '';
  console.log(`${r.browser.padEnd(9)} ${r.device.padEnd(28)} ${r.view.padEnd(7)} ${String(r.scale).padEnd(6)} `
    + `${`${r.bodyPx}px`.padEnd(6)} ${r.chrome ? 'yes' : 'no '}${flag}`);
}
// reveal drops the hash on the cover and clamps fragments past the last one.
const slideOf = (hash) => Number(hash.replace('#/', '').split('/')[0] || 0);
const lost = results.filter((r) => r.slide && slideOf(r.landedOn) !== slideOf(`#/${r.slide}`));
if (lost.length) console.log(`\n${lost.length} loads did not land on the requested slide (deep link lost).`);
const failures = results.filter((r) => r.errors?.length);
for (const r of failures) console.log(`\n${r.browser} / ${r.device} errors:\n  ${r.errors.join('\n  ')}`);
console.log(`\nScreenshots and report.json in ${opts.out}/`);
process.exit(failures.length ? 2 : 0);
