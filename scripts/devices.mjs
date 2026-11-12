/*
 * Test devices for the check scripts, in CSS px as the page sees them: the
 * browser's and the OS's bars are already taken off, so each size is a viewport,
 * not a screen. The bars move on rotation, so landscape is its own size.
 * Sources and estimates: AGENTS.md, "Test devices".
 */

const BASE = {
  projector: { width: 1280, height: 720, kind: 'desktop' },
  laptop: { width: 1440, height: 790, dpr: 2, kind: 'desktop' },
  'large-display': { width: 1920, height: 950, kind: 'desktop' },
  's26-chrome': { width: 360, height: 637, dpr: 3, kind: 'phone', landscape: [695, 274] },
  // Full screen locks landscape (the phone plugin), so there is no portrait run.
  's26-fullscreen': { width: 360, height: 780, dpr: 3, kind: 'phone', landscapeOnly: true },
  // iPhone Safari has no element full screen, so it never gets the screen size.
  'iphone-17': { width: 402, height: 681, dpr: 3, kind: 'phone', landscape: [756, 352], noFullscreen: true },
  'iphone-17-pro-max': { width: 440, height: 763, dpr: 3, kind: 'phone', landscape: [838, 390], noFullscreen: true },
  'ipad-11': { width: 820, height: 1106, dpr: 2, kind: 'tablet', landscape: [1180, 746] },
  'ipad-mini': { width: 744, height: 1059, dpr: 2, kind: 'tablet', landscape: [1133, 670] },
  // Run by name only.
  'projector-4x3': { width: 1024, height: 768, kind: 'desktop', extra: true },
  's26-chrome-zoomed': { width: 320, height: 566, dpr: 3, kind: 'phone', landscape: [618, 244], extra: true },
};

export const DEVICES = {};
for (const [name, { landscape, landscapeOnly, ...d }] of Object.entries(BASE)) {
  const mobile = d.kind !== 'desktop';
  if (!landscapeOnly) DEVICES[name] = { ...d, mobile };
  if (!mobile) continue;
  const [width, height] = landscape ?? [d.height, d.width];
  DEVICES[`${name}-landscape`] = { ...d, mobile, width, height };
}

const pick = (test) => Object.keys(DEVICES).filter((name) => !DEVICES[name].extra && test(DEVICES[name], name));
export const GROUPS = {
  all: pick(() => true),
  desktop: pick((d) => d.kind === 'desktop'),
  phones: pick((d) => d.kind === 'phone'),
  tablets: pick((d) => d.kind === 'tablet'),
  portrait: pick((d, name) => d.mobile && !name.endsWith('-landscape')),
  landscape: pick((d, name) => name.endsWith('-landscape')),
};

// A group name, or device names separated by commas.
export function deviceNames(arg) {
  const names = GROUPS[arg] ?? arg.split(',');
  for (const name of names) if (!DEVICES[name]) throw new Error(`Unknown device: ${name}`);
  return names;
}
