import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';

// Screenshots are for inspecting one run, so each run replaces the last.
// Only folders inside .screenshots/ are wiped, so a stray --out cannot delete source.
export async function freshOutputDir(dir) {
  if (!path.resolve(dir).startsWith(path.resolve('.screenshots') + path.sep)) {
    throw new Error(`--out must be a folder inside .screenshots/, got ${dir}`);
  }
  await rm(dir, { recursive: true, force: true });
  await mkdir(dir, { recursive: true });
}
