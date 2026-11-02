/* Landing-page QA, independent of the presentation's browser checks.
 * Start npm run dev, then npm run check:landing.
 * Real Safari uses macOS WebDriver; WebKit adds phone-size engine coverage.
 */
import { chromium, firefox, webkit } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { createServer } from 'node:net';

const options = { base: 'http://localhost:5173/', browsers: 'chrome,firefox,webkit,safari', devices: 'all', out: '.screenshots/landing' };
for (let i = 2; i < process.argv.length; i += 2) {
  const name = process.argv[i].replace(/^--/, '');
  if (!(name in options) || !process.argv[i + 1]) throw new Error(`Unknown or incomplete option: ${process.argv[i]}`);
  options[name] = process.argv[i + 1];
}
const sizes = {
  projector: [1280, 720], 'projector-4x3': [1024, 768], laptop: [1440, 900], desktop: [1920, 1080], ultrawide: [2560, 1440],
  'iphone-11': [414, 896], 'galaxy-a': [384, 832], 'android-budget': [360, 800], redmi: [393, 873],
  'iphone-12': [390, 844], 'iphone-17': [402, 874], 'galaxy-s': [360, 780], pixel: [412, 915], 'pro-max': [440, 956], zoomed: [320, 693],
};
const desktopNames = Object.keys(sizes).slice(0, 5);
const phoneNames = Object.keys(sizes).slice(5);
for (const name of phoneNames) sizes[`${name}-landscape`] = [...sizes[name]].reverse();
const names = options.devices === 'all' ? Object.keys(sizes)
  : options.devices === 'desktop' ? desktopNames
  : options.devices === 'phones' ? [...phoneNames, ...phoneNames.map(n => `${n}-landscape`)]
  : options.devices.split(',');
for (const name of names) if (!sizes[name]) throw new Error(`Unknown device: ${name}`);
const report = { created: new Date().toISOString(), url: options.base, results: [], startupErrors: [] };
await mkdir(options.out, { recursive: true });

// Runs unchanged through Playwright and Safari's JavaScript execution endpoint.
function inspectPage() {
  const box = el => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom }; };
  const card = document.querySelector('.landing');
  const photo = document.querySelector('.profile__frame');
  const last = document.querySelector('.links a:last-child');
  const problems = [];
  if (!card || !photo || !last) return { problems: ['Landing page did not load'], viewport: [innerWidth, innerHeight] };
  if (document.documentElement.scrollWidth > innerWidth + 1) problems.push('Horizontal page overflow');
  if (document.body.getBoundingClientRect().height + 1 < innerHeight) problems.push('Page background is shorter than the viewport');
  for (const img of document.images) if (!img.complete || img.naturalWidth === 0) problems.push(`Image failed: ${img.getAttribute('src')}`);
  for (const a of document.querySelectorAll('main a')) {
    const r = a.getBoundingClientRect();
    if (r.width < 44 || r.height < 44) problems.push(`Small tap target: ${a.getAttribute('aria-label') || a.textContent.trim()}`);
    if (r.x < 0 || r.right > innerWidth + 1) problems.push(`Link outside viewport: ${a.textContent.trim()}`);
  }
  if (!document.fonts.check('16px "Roboto Variable"')) problems.push('Roboto font did not load');
  if (!document.fonts.check('32px "Oxanium Variable"')) problems.push('Oxanium font did not load');
  const portrait = box(photo);
  const ends = [...document.querySelectorAll('.profile__routes path')].map(path => {
    const point = path.getPointAtLength(0).matrixTransform(path.getScreenCTM());
    return { x: point.x, y: point.y };
  });
  if (ends.some(p => p.x < portrait.x || p.x > portrait.right || p.y < portrait.y || p.y > portrait.bottom)) problems.push('Portrait route starts outside the photo frame');
  return { viewport: [innerWidth, innerHeight], problems, portrait, routeStarts: ends,
    bottomClearance: box(card).bottom - box(last).bottom,
    backgroundRepeat: getComputedStyle(document.body).backgroundRepeat,
    lowerRouteTransform: getComputedStyle(document.querySelector('.route--lower')).transform };
}
function record(browser, device, data, extra = {}) {
  const requested = sizes[device];
  const matched = data.viewport?.every((v, i) => Math.abs(v - requested[i]) <= 2);
  const result = { browser, device, requested, ...data, viewportMatched: matched, ...extra };
  report.results.push(result);
  console.log(`${browser} ${device}: ${data.problems.length ? 'FAIL ' + data.problems.join('; ') : 'OK'}${matched ? '' : ` (actual viewport ${data.viewport}; requested size unsupported)`}`);
}
async function checkPlaywright(name) {
  const engine = { chrome: chromium, firefox, webkit }[name];
  if (!engine) throw new Error(`Unknown browser: ${name}`);
  const browser = await engine.launch({ ...(name === 'chrome' ? { channel: 'chrome' } : {}), headless: true });
  try {
    for (const device of names) {
      const [width, height] = sizes[device];
      const mobile = !desktopNames.includes(device) && name !== 'firefox';
      const context = await browser.newContext({ viewport: { width, height }, ...(mobile ? { isMobile: true, hasTouch: true, deviceScaleFactor: 2 } : {}) });
      try {
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
        const url = new URL(options.base); url.searchParams.set('r', `${name}-${device}-${Date.now()}`);
        await page.goto(url.href);
        await page.locator('.landing').waitFor();
        await page.evaluate(() => document.fonts.ready);
        await page.waitForTimeout(1500);
        const data = await page.evaluate(inspectPage);
        data.problems.push(...errors);
        const dir = `${options.out}/${name}`; await mkdir(dir, { recursive: true });
        const screenshot = `${dir}/${device}.png`;
        await page.screenshot({ path: screenshot, fullPage: true });
        record(name, device, data, { screenshot, consoleErrors: errors });
      } finally { await context.close(); }
    }
  } finally { await browser.close(); }
}
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
async function freePort() {
  const server = createServer(); await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port; await new Promise(resolve => server.close(resolve)); return port;
}
async function checkSafari() {
  const port = await freePort();
  const driver = spawn('/usr/bin/safaridriver', ['-p', String(port)], { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = ''; driver.stderr.on('data', data => { stderr += data; });
  let launchError; driver.on('error', error => { launchError = error; });
  const root = `http://127.0.0.1:${port}`;
  let session;
  async function call(method, path, body) {
    const response = await fetch(root + path, { method, headers: { 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(20000) });
    const { value } = await response.json();
    if (!response.ok || value?.error) throw new Error(value?.message || `WebDriver HTTP ${response.status}`);
    return value;
  }
  try {
    let ready = false;
    for (let i = 0; i < 30; i++) {
      if (launchError || driver.exitCode !== null) throw new Error(launchError?.message || `safaridriver exited ${driver.exitCode}. ${stderr} Enable Safari automation with sudo safaridriver --enable.`);
      try { await call('GET', '/status'); ready = true; break; } catch { await pause(250); }
    }
    if (!ready) throw new Error(`Safari WebDriver did not start. ${stderr}`);
    session = (await call('POST', '/session', { capabilities: { alwaysMatch: { browserName: 'safari' } } })).sessionId;
    const prefix = `/session/${session}`;
    const execute = script => call('POST', `${prefix}/execute/sync`, { script, args: [] });
    for (const device of names) {
      const [width, height] = sizes[device];
      await call('POST', `${prefix}/window/rect`, { width, height });
      // Safari sizes the whole window. Correct for toolbar and frame dimensions.
      for (let i = 0; i < 2; i++) {
        const actual = await execute('return [innerWidth, innerHeight, outerWidth, outerHeight]');
        await call('POST', `${prefix}/window/rect`, { width: width + actual[2] - actual[0], height: height + actual[3] - actual[1] });
      }
      const url = new URL(options.base); url.searchParams.set('r', `safari-${device}-${Date.now()}`);
      await call('POST', `${prefix}/url`, { url: url.href });
      await pause(1800);
      const data = await execute(`return (${inspectPage.toString()})()`);
      const dir = `${options.out}/safari`; await mkdir(dir, { recursive: true });
      const screenshot = `${dir}/${device}.png`;
      await writeFile(screenshot, Buffer.from(await call('GET', `${prefix}/screenshot`), 'base64'));
      record('safari', device, data, { screenshot, consoleErrors: null, note: 'Real desktop Safari; no mobile emulation. Screenshot covers the viewport. Browser console capture is unavailable through this WebDriver check.' });
    }
  } finally {
    if (session) await call('DELETE', `/session/${session}`).catch(() => {});
    driver.kill();
  }
}
for (const name of options.browsers.split(',')) {
  try { await (name === 'safari' ? checkSafari() : checkPlaywright(name)); }
  catch (error) { report.startupErrors.push({ browser: name, error: error.message }); console.error(`${name}: ${error.message.split('\n')[0]}`); }
}
await writeFile(`${options.out}/report.json`, JSON.stringify(report, null, 2));
const failed = report.results.filter(r => r.problems.length);
const mismatches = report.results.filter(r => !r.viewportMatched);
console.log(`${report.results.length} checks; ${failed.length} failed; ${mismatches.length} unsupported viewport sizes; ${report.startupErrors.length} browser errors. Report: ${options.out}/report.json`);
process.exitCode = failed.length || report.startupErrors.length ? 2 : mismatches.length ? 3 : 0;
