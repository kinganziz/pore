// Precompute the cheapest perfect max-level (P10, or P5 for boss weapons) cost for every item -> data/badges.json
//   node tools/badges.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(path.join(root, 'src', 'solver.js'), 'utf8');
const createSolver = new Function(src + '\nreturn createSolver;')();
const S = createSolver();
const db = JSON.parse(readFileSync(path.join(root, 'data', 'items.json'), 'utf8'));

// Must mirror STAT_META / CATS in src/app.html (default categories, no user overrides).
const CATS = { combat: { num: 1, den: 4 }, crit: { num: 1, den: 6 }, resource: { num: 1, den: 8 }, gather: { num: 1, den: 16 } };
function catFor(name) {
  const n = name.toLowerCase();
  if (n.startsWith('critical')) return 'crit';
  if (n.includes('mining') || n.includes('fishing')) return 'resource';
  if (n.includes('encounter')) return 'gather';
  return 'combat';
}

const badges = {};
const t0 = Date.now();
for (const it of db.items) {
  const names = Object.keys(it.stats);
  const base = names.map(n => it.stats[n]);
  const rates = names.map(n => CATS[catFor(n)]);
  badges['i' + it.id] = S.cheapest(base, rates, it.maxLevel || 10);   // boss weapons stop at P5
}
writeFileSync(path.join(root, 'data', 'badges.json'), JSON.stringify(badges) + '\n');
const costs = Object.values(badges);
console.log(`wrote data/badges.json: ${costs.length} items in ${Date.now() - t0} ms, cheapest ${Math.min(...costs)}, priciest ${Math.max(...costs)}`);
