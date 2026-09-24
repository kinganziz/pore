// Pixel-art style of PORE's own icons.
//
// Renders every drawing in icons/modern/ onto a small grid with resvg (no anti-aliasing),
// posterizes the colours, adds a dark 1-pixel outline, and writes a crisp-edged SVG per icon
// (icons/pixel/<key>.svg) plus the bundled sprite icons/sprite-pixel.svg.
// Only PORE's own drawings are used as input.
//
//   npm install          (once; installs @resvg/resvg-js)
//   node tools/pixelate.mjs [--size 24]

import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'icons', 'modern');
const OUT = path.join(ROOT, 'icons', 'pixel');
const SPRITE = path.join(ROOT, 'icons', 'sprite-pixel.svg');
const argSize = process.argv.indexOf('--size');
const GRID = argSize > 0 ? Number(process.argv[argSize + 1]) : 24;   // final grid (incl. 1px outline margin)
const INNER = GRID - 2;

const STEP = 20;                     // colour posterization step per channel
const post = v => Math.min(255, Math.round(v / STEP) * STEP);
const hex = (r, g, b) => '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');

function pixelate(svgText) {
  const r = new Resvg(svgText, { fitTo: { mode: 'width', value: INNER }, shapeRendering: 0, background: 'rgba(0,0,0,0)' }).render();
  const w = r.width, h = r.height, px = r.pixels;          // RGBA, not premultiplied
  const grid = Array.from({ length: GRID }, () => new Array(GRID).fill(null));
  const ox = Math.floor((GRID - w) / 2), oy = Math.floor((GRID - h) / 2);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      if (px[i + 3] < 128) continue;
      grid[y + oy][x + ox] = [post(px[i]), post(px[i + 1]), post(px[i + 2])];
    }
  }
  // 1px outline: transparent cells touching a filled cell become a dark shade of that neighbour.
  const out = grid.map(row => row.slice());
  for (let y = 0; y < GRID; y++) {
    for (let x = 0; x < GRID; x++) {
      if (grid[y][x]) continue;
      const n = [[0, -1], [0, 1], [-1, 0], [1, 0]].map(([dx, dy]) => (grid[y + dy] || [])[x + dx]).find(Boolean);
      if (n) out[y][x] = [Math.round(n[0] * 0.22), Math.round(n[1] * 0.22), Math.round(n[2] * 0.26)];
    }
  }
  // Emit horizontal runs grouped by colour.
  const runs = new Map();
  for (let y = 0; y < GRID; y++) {
    let x = 0;
    while (x < GRID) {
      const c = out[y][x];
      if (!c) { x++; continue; }
      const key = hex(...c);
      let x1 = x;
      while (x1 < GRID && out[y][x1] && hex(...out[y][x1]) === key) x1++;
      if (!runs.has(key)) runs.set(key, []);
      runs.get(key).push(`M${x} ${y}h${x1 - x}v1h-${x1 - x}z`);
      x = x1;
    }
  }
  const paths = [...runs].map(([c, d]) => `<path fill="${c}" d="${d.join('')}"/>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${GRID} ${GRID}" shape-rendering="crispEdges">${paths}</svg>`;
}

mkdirSync(OUT, { recursive: true });
const files = readdirSync(SRC).filter(f => f.endsWith('.svg')).sort();
const symbols = [];
for (const f of files) {
  const key = f.replace(/\.svg$/, '');
  const svg = pixelate(readFileSync(path.join(SRC, f), 'utf8'));
  writeFileSync(path.join(OUT, f), svg + '\n');
  symbols.push(`<symbol id="${key}" viewBox="0 0 ${GRID} ${GRID}">${svg.slice(svg.indexOf('>') + 1, svg.lastIndexOf('</svg>'))}</symbol>`);
}
const sprite = `<svg xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" style="display:none">${symbols.join('')}</svg>`;
writeFileSync(SPRITE, sprite);
console.log(`pixel icons: ${files.length} at ${GRID}x${GRID} -> icons/pixel/, icons/sprite-pixel.svg (${Math.round(sprite.length / 1024)} KB)`);
