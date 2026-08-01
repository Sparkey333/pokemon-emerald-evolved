// Copy the Indigo Dexforge web payload out of iCloud into dist/ for packaging.
//
// The canonical project lives in iCloud ("New project 2/indigo-dexforge"); building a
// Tauri app directly in there is slow and trips the fileprovider xattr race at signing
// time, so the app is built here and the payload is copied in.
//
// Only what the app needs to DISPLAY is copied — no python tools, no research HTML,
// no node_modules. Reference-only vault art (kanto-151, evolved) IS included because
// this build is Brandon's personal local viewer, and the UI labels it as such.
import { cp, mkdir, rm, readFile, writeFile, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = dirname(dirname(fileURLToPath(import.meta.url)));
const SRC = process.env.DEXFORGE_SRC
  || '/Users/ansom/Library/Mobile Documents/com~apple~CloudDocs/New project 2/indigo-dexforge';
const DIST = join(APP, 'dist');

if (!existsSync(SRC)) {
  console.error(`!! Dexforge source not found:\n   ${SRC}\n   Set DEXFORGE_SRC to override.`);
  process.exit(1);
}

await rm(DIST, { recursive: true, force: true });
await mkdir(DIST, { recursive: true });

const FILES = ['dashboard.html', 'index.html', 'README.md'];
const DIRS = ['data', 'sheets', 'vault'];

for (const f of FILES) {
  const from = join(SRC, f);
  if (existsSync(from)) await cp(from, join(DIST, f));
}
for (const d of DIRS) {
  const from = join(SRC, d);
  if (!existsSync(from)) continue;
  await cp(from, join(DIST, d), {
    recursive: true,
    filter: (p) => !/(^|\/)(\.DS_Store|__pycache__|\._.*)$/.test(p),
  });
}

// The app opens at index.html; Dexforge's dashboard is the real front door.
await cp(join(DIST, 'dashboard.html'), join(DIST, 'index.html'));

// Count what shipped so the build log is honest.
const { execSync } = await import('node:child_process');
const pngs = execSync(`find "${DIST}" -name '*.png' | wc -l`).toString().trim();
const size = execSync(`du -sh "${DIST}" | cut -f1`).toString().trim();
console.log(`synced payload -> dist/  (${pngs} pngs, ${size})`);
