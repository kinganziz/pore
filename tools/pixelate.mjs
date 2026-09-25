// "Modern pixel" icon style: PORE's modern drawings (icons/modern/) re-drawn as clean pixel art.
//
// Unlike a plain downscale (which blurs gradients into noise), every grid cell takes the colour
// that dominates it, picked from the drawing's own palette (its fills, strokes and gradient stops),
// so gradients become flat shading bands. The dark outline is then rebuilt as one continuous
// 1-pixel line, stair-step corners are thinned (pixel-perfect lines) and stray pixels are removed.
//
//   npm install                      (once; installs @resvg/resvg-js)
//   node tools/pixelate.mjs [--size 20]
//
// Writes icons/pixel-modern/<key>.svg and the bundle icons/sprite-pixel-modern.svg.

import { readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'icons', 'modern');
const OUT = path.join(ROOT, 'icons', 'pixel-modern');
const SPRITE = path.join(ROOT, 'icons', 'sprite-pixel-modern.svg');
const arg = name => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : null; };
const GRID = Number(arg('--size') || 20);   // 20x20: chunky enough to read as pixel art at 48px, keeps the details
const SUB = 12;                               // sub-samples per cell side
const FILL_MIN = 0.42;                        // share of a cell that must be covered to paint it

const hexToRgb = h => {
  h = h.replace('#', '');
  if (h.length === 3) h = [...h].map(c => c + c).join('');
  return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
};
const toHex = c => '#' + c.map(v => v.toString(16).padStart(2, '0')).join('');
const lum = ([r, g, b]) => (0.299 * r + 0.587 * g + 0.114 * b) / 255;
const dist = (a, b) => {                      // "redmean" perceptual distance
  const rm = (a[0] + b[0]) / 2, dr = a[0] - b[0], dg = a[1] - b[1], db = a[2] - b[2];
  return (2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db;
};

// Pixel-art colour treatment: richer saturation, a little more contrast, and hue-shifted ramps
// (shadows lean cool, highlights lean warm) so the flat bands read bright rather than dull.
function rgbToHsl([r, g, b]) {
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2;
  if (mx === mn) return [0, 0, l];
  const d = mx - mn, s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
  const h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [h * 60, s, l];
}
function hslToRgb([h, s, l]) {
  const f = n => { const k = (n + h / 30) % 12, a = s * Math.min(l, 1 - l); return Math.round(255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1)))); };
  return [f(0), f(8), f(4)];
}
function vivid(rgb) {
  let [h, s, l] = rgbToHsl(rgb);
  if (l < 0.13 || l > 0.96) return rgb;                         // outline ink and pure white stay
  const toward = (target, amt) => { let d = ((target - h + 540) % 360) - 180; return (h + d * amt + 360) % 360; };
  if (s > 0.12) {
    s = Math.min(1, s * 1.35 + 0.08);
    h = l < 0.45 ? toward(250, 0.08 * (0.45 - l) / 0.45 * 2) : toward(55, 0.06 * (l - 0.45) / 0.55 * 2);
  } else {
    s = Math.min(0.22, s + 0.06); h = l < 0.5 ? 225 : h || 220;  // greys become cool steel
  }
  l = Math.min(0.94, Math.max(0.14, 0.5 + (l - 0.5) * 1.12 + 0.02));
  return hslToRgb([h, s, l]);
}

function paletteOf(svg) {
  const seen = new Map();
  for (const m of svg.matchAll(/(?:fill|stroke|stop-color)="(#[0-9a-fA-F]{3,6})"/g)) {
    const rgb = hexToRgb(m[1]);
    seen.set(toHex(rgb), rgb);
  }
  return [...seen.values()];
}

function pixelate(svg) {
  const palette = paletteOf(svg);          // matching uses the drawing's colours, output uses vivid ones
  const inkIdx = palette.reduce((best, c, i) => (lum(c) < 0.16 && (best < 0 || lum(c) < lum(palette[best])) ? i : best), -1);
  if (inkIdx < 0) palette.push([20, 20, 30]);
  const INK = inkIdx < 0 ? palette.length - 1 : inkIdx;
  // Outline ink = dark colours the drawing uses as strokes. A dark *fill* (the shadowed side of a black
  // cloak) is fabric, not outline: it still gets an outline around it instead of melting into the edge.
  const strokeInk = new Set();
  for (const m of svg.matchAll(/stroke="(#[0-9a-fA-F]{3,6})"/g)) { const c = hexToRgb(m[1]); if (lum(c) < 0.3) strokeInk.add(toHex(c)); }
  const isInk = i => i === INK || (lum(palette[i]) < 0.2 && (strokeInk.size === 0 || strokeInk.has(toHex(palette[i]))));
  const isShine = i => lum(palette[i]) > 0.9;

  const px = SUB * GRID;
  const img = new Resvg(svg, { fitTo: { mode: 'width', value: px }, background: 'rgba(0,0,0,0)' }).render();
  const data = img.pixels, W = img.width;
  const cache = new Map();
  const nearest = (r, g, b) => {
    const key = (r << 16) | (g << 8) | b;
    let v = cache.get(key);
    if (v === undefined) {
      let bd = Infinity; v = 0;
      palette.forEach((c, i) => { const d = dist(c, [r, g, b]); if (d < bd) { bd = d; v = i; } });
      cache.set(key, v);
    }
    return v;
  };

  // 1. sample: each cell takes its dominant palette colour
  const T = -1;
  let grid = Array.from({ length: GRID }, () => new Array(GRID).fill(T));
  for (let cy = 0; cy < GRID; cy++) {
    for (let cx = 0; cx < GRID; cx++) {
      const counts = new Map(); let covered = 0;
      for (let sy = 0; sy < SUB; sy++) {
        for (let sx = 0; sx < SUB; sx++) {
          const o = ((cy * SUB + sy) * W + cx * SUB + sx) * 4;
          if (data[o + 3] < 128) continue;
          covered++;
          const k = nearest(data[o], data[o + 1], data[o + 2]);
          counts.set(k, (counts.get(k) || 0) + 1);
        }
      }
      const area = SUB * SUB;
      if (covered / area < FILL_MIN) continue;
      let best = T, bestN = 0;
      for (const [k, n] of counts) {
        // small bright highlights survive if they own a quarter of the cell
        const w = isShine(k) && n / area >= 0.25 ? n * 3 : n;
        if (w > bestN) { bestN = w; best = k; }
      }
      grid[cy][cx] = best;
    }
  }
  const coverage = (cx, cy) => {
    const counts = new Map(); let covered = 0;
    for (let sy = 0; sy < SUB; sy++) for (let sx = 0; sx < SUB; sx++) {
      const o = ((cy * SUB + sy) * W + cx * SUB + sx) * 4;
      if (data[o + 3] < 128) continue;
      covered++;
      const k = nearest(data[o], data[o + 1], data[o + 2]);
      counts.set(k, (counts.get(k) || 0) + 1);
    }
    return { share: covered / (SUB * SUB), top: [...counts].sort((a, b) => b[1] - a[1])[0]?.[0] ?? T };
  };
  const at = (g, x, y) => (y < 0 || y >= GRID || x < 0 || x >= GRID) ? T : g[y][x];
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const N8 = [...N4, [1, 1], [1, -1], [-1, 1], [-1, -1]];
  const isFill = k => k !== T && !isInk(k);
  const RING = [[-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0]];

  // 1b. bridge thin lines: a lightly covered cell that joins separate painted neighbours is painted
  for (let pass = 0; pass < 2; pass++) {
    const add = [];
    for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) {
      if (grid[y][x] !== T) continue;
      const on = RING.map(([dx, dy]) => at(grid, x + dx, y + dy) !== T);
      let groups = 0;
      for (let i = 0; i < 8; i++) if (on[i] && !on[(i + 7) % 8]) groups++;
      if (groups === 0 && on.every(Boolean)) groups = 1;
      if (groups < 2) continue;
      const c = coverage(x, y);
      if (c.share >= 0.16 && c.top !== T) add.push([x, y, c.top]);
    }
    add.forEach(([x, y, k]) => { grid[y][x] = k; });
  }

  // 2. stray pixels: a fill cell unlike all 8 neighbours takes the most common neighbouring colour
  grid = grid.map((row, y) => row.map((k, x) => {
    if (!isFill(k) || isShine(k)) return k;
    const ns = N8.map(([dx, dy]) => at(grid, x + dx, y + dy));
    if (ns.includes(k)) return k;
    const fills = ns.filter(isFill);
    if (fills.length < 5) return k;
    const tally = new Map(); fills.forEach(n => tally.set(n, (tally.get(n) || 0) + 1));
    return [...tally].sort((a, b) => b[1] - a[1])[0][0];
  }));

  // 3. continuous outline: every fill cell that touches the outside gets an ink cell next to it
  // the outline colour the drawing mostly uses on its silhouette (a gold ring keeps its brown outline)
  const edgeInk = new Map();
  for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) {
    const k = grid[y][x];
    if (k !== T && isInk(k) && N4.some(([dx, dy]) => at(grid, x + dx, y + dy) === T)) edgeInk.set(k, (edgeInk.get(k) || 0) + 1);
  }
  const OUTLINE = edgeInk.size ? [...edgeInk].sort((a, b) => b[1] - a[1])[0][0] : INK;
  const out = grid.map(r => r.slice());
  const added = new Set();
  for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) {
    if (grid[y][x] !== T) continue;
    if (!N4.some(([dx, dy]) => isFill(at(grid, x + dx, y + dy)))) continue;
    const near = new Map();                                     // continue the neighbouring outline's colour
    N8.forEach(([dx, dy]) => { const n = at(grid, x + dx, y + dy); if (n !== T && isInk(n)) near.set(n, (near.get(n) || 0) + 1); });
    out[y][x] = near.size ? [...near].sort((a, b) => b[1] - a[1])[0][0] : OUTLINE;
    added.add(y * GRID + x);
  }
  grid = out;

  // 4. thin the outline: drop ink that touches no fill, and stair-step corners (pixel-perfect lines)
  for (let pass = 0; pass < 2; pass++) {
    for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) {
      const k = grid[y][x];
      if (k === T || !isInk(k) || !added.has(y * GRID + x)) continue;      // drawn dark parts stay
      if (!N8.some(([dx, dy]) => isFill(at(grid, x + dx, y + dy)))) { grid[y][x] = T; continue; }
      if (N4.some(([dx, dy]) => isFill(at(grid, x + dx, y + dy)))) continue;
      const inks = N4.filter(([dx, dy]) => { const n = at(grid, x + dx, y + dy); return n !== T && isInk(n); });
      if (inks.length === 2 && inks[0][0] !== inks[1][0] && inks[0][1] !== inks[1][1]) grid[y][x] = T;
    }
  }

  // 4b. drop specks: groups of 1-2 cells cut off from the drawing (sparkles, drips) read as stray pixels at 20x20
  const seen = new Set(), comps = [];
  for (let y = 0; y < GRID; y++) for (let x = 0; x < GRID; x++) {
    if (grid[y][x] === T || seen.has(y * GRID + x)) continue;
    const comp = [], stack = [[x, y]];
    seen.add(y * GRID + x);
    while (stack.length) {
      const [cx, cy] = stack.pop();
      comp.push([cx, cy]);
      for (const [dx, dy] of N8) {
        const nx = cx + dx, ny = cy + dy;
        if (nx < 0 || ny < 0 || nx >= GRID || ny >= GRID || grid[ny][nx] === T || seen.has(ny * GRID + nx)) continue;
        seen.add(ny * GRID + nx); stack.push([nx, ny]);
      }
    }
    comps.push(comp);
  }
  if (comps.some(c => c.length > 2)) for (const c of comps) if (c.length <= 2) for (const [x, y] of c) grid[y][x] = T;

  // 5. emit horizontal runs grouped by colour
  const runs = new Map();
  for (let y = 0; y < GRID; y++) {
    let x = 0;
    while (x < GRID) {
      const k = grid[y][x];
      if (k === T) { x++; continue; }
      let x1 = x + 1;
      while (x1 < GRID && grid[y][x1] === k) x1++;
      const c = toHex(isInk(k) ? palette[k] : vivid(palette[k]));
      if (!runs.has(c)) runs.set(c, []);
      runs.get(c).push(`M${x} ${y}h${x1 - x}v1h-${x1 - x}z`);
      x = x1;
    }
  }
  const paths = [...runs].map(([c, d]) => `<path fill="${c}" d="${d.join('')}"/>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${GRID} ${GRID}" shape-rendering="crispEdges">${paths}</svg>`;
}

rmSync(OUT, { recursive: true, force: true });
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
console.log(`modern pixel icons: ${files.length} at ${GRID}x${GRID} -> icons/pixel-modern/, icons/sprite-pixel-modern.svg (${Math.round(sprite.length / 1024)} KB)`);
