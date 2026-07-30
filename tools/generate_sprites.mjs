#!/usr/bin/env node
/**
 * Generate 64x64 DIY starter sprites as PNG for ROM import.
 * Output: hack/assets/sprites/diy/<name>.png
 */
import { writeFileSync, mkdirSync } from 'fs';
import { createCanvas } from 'canvas';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, '..', 'hack', 'assets', 'sprites', 'diy');
mkdirSync(OUT, { recursive: true });

function px(ctx, x, y, c, s = 1) {
  ctx.fillStyle = c;
  ctx.fillRect(x, y, s, s);
}

function drawGrass(ctx, variant) {
  const cx = 32, cy = 36;
  const big = variant === 'verdantaur';
  ctx.fillStyle = big ? '#166534' : '#3d9a5f';
  ctx.beginPath(); ctx.ellipse(cx, cy + 8, big ? 18 : 14, 12, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = big ? '#4ade80' : '#5ecf7a';
  ctx.beginPath(); ctx.ellipse(cx, cy, big ? 18 : 16, big ? 16 : 14, 0, 0, Math.PI * 2); ctx.fill();
  const petals = big ? 8 : 6;
  for (let i = 0; i < petals; i++) {
    const a = (i / petals) * Math.PI * 2;
    ctx.fillStyle = ['#e879f9', '#c084fc', '#a855f7'][i % 3];
    ctx.beginPath();
    ctx.ellipse(cx + Math.cos(a) * 14, cy - 10 + Math.sin(a) * 8, 6, 4, a, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = '#fde047';
  ctx.beginPath(); ctx.arc(cx, cy - 10, big ? 7 : 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#111';
  ctx.fillRect(cx - 6, cy, 3, 3); ctx.fillRect(cx + 5, cy, 3, 3);
}

function drawFire(ctx, variant) {
  const cx = 32, cy = 36;
  const big = variant === 'infernodrake';
  ctx.fillStyle = '#f97316';
  ctx.beginPath(); ctx.ellipse(cx, cy + 4, big ? 16 : 13, big ? 17 : 15, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#dc2626';
  ctx.beginPath();
  ctx.moveTo(cx - 10, cy - 8); ctx.lineTo(cx - 30, cy - 24); ctx.lineTo(cx - 8, cy + 2); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(cx + 10, cy - 8); ctx.lineTo(cx + 30, cy - 24); ctx.lineTo(cx + 8, cy + 2); ctx.fill();
  const fh = big ? 20 : 12;
  ctx.fillStyle = '#fde047';
  ctx.beginPath(); ctx.moveTo(cx, cy + 14); ctx.lineTo(cx - 6, cy + 14 + fh); ctx.lineTo(cx, cy + 10 + fh); ctx.lineTo(cx + 6, cy + 14 + fh); ctx.fill();
  ctx.fillStyle = '#111';
  ctx.fillRect(cx - 5, cy - 5, 2, 2); ctx.fillRect(cx + 4, cy - 5, 2, 2);
}

function drawWater(ctx, variant) {
  const cx = 32, cy = 36;
  const big = variant === 'tsunamoise';
  ctx.fillStyle = '#7dd3fc';
  ctx.beginPath(); ctx.ellipse(cx, cy + 6, 14, 11, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = big ? '#0c4a6e' : '#1d4ed8';
  ctx.beginPath(); ctx.ellipse(cx, cy - 2, big ? 20 : 18, big ? 16 : 14, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#94a3b8';
  const off = big ? 26 : 22;
  ctx.fillRect(cx - off, cy - 4, 10, 6);
  ctx.fillRect(cx + off - 10, cy - 4, 10, 6);
  ctx.fillStyle = '#7dd3fc';
  ctx.beginPath(); ctx.ellipse(cx, cy - 14, 9, 8, 0, 0, Math.PI * 2); ctx.fill();
}

const DIY = [
  ['florasaur', drawGrass, 'florasaur'],
  ['verdantaur', drawGrass, 'verdantaur'],
  ['charblaze', drawFire, 'charblaze'],
  ['infernodrake', drawFire, 'infernodrake'],
  ['torrentoise', drawWater, 'torrentoise'],
  ['tsunamoise', drawWater, 'tsunamoise'],
];

// Use pure node canvas-less approach with raw PNG if canvas pkg missing
let hasCanvas = true;
try { await import('canvas'); } catch { hasCanvas = false; }

if (!hasCanvas) {
  // Minimal PNG writer via BMP-like raw - use pokeemerald copy fallback message
  console.log('canvas package not installed — writing placeholder marker files');
  for (const [name] of DIY) {
    writeFileSync(join(OUT, `${name}.txt`), `Run: npm install canvas && node tools/generate_sprites.mjs\nOr copy parent sprite in bootstrap.`);
  }
  process.exit(0);
}

const { createCanvas: mk } = await import('canvas');
for (const [file, fn, variant] of DIY) {
  const c = mk(64, 64);
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, 64, 64);
  fn(ctx, variant);
  writeFileSync(join(OUT, `${file}.png`), c.toBuffer('image/png'));
  console.log('wrote', file);
}
