// Node test harness for src/solver.js
//   node tools/test_solver.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const src = readFileSync(path.join(here, '..', 'src', 'solver.js'), 'utf8');
const createSolver = new Function(src + '\nreturn createSolver;')();
const S = createSolver();

const M = { combat: { num: 1, den: 4 }, crit: { num: 1, den: 6 }, resource: { num: 1, den: 8 }, gather: { num: 1, den: 16 } };

let failures = 0;
function check(name, actual, expected) {
  const ok = actual === expected;
  if (!ok) failures++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}: got ${actual}, expected ${expected}`);
}

function run(name, base, mults, expected, owned = [], level = 10, target = null) {
  const chain = S.perfectChain(base, mults);
  const t = target || chain[level];
  const r = S.solve({ base, mults, level, target: t, owned });
  check(`${name} [${r.mode}, ${r.ms}ms, sizes ${r.sizes.slice(1).join('/')}]`, r.cost, expected);
  if (r.plan) {
    const a = S.analyze(r.plan, owned.length);
    if (a.p1 !== r.cost) { failures++; console.log(`FAIL  ${name}: analyze p1 ${a.p1} != cost ${r.cost}`); }
    a.ownedUse.forEach((n, j) => { if (n > owned[j].qty) { failures++; console.log(`FAIL  ${name}: owned ${j} used ${n} > qty ${owned[j].qty}`); } });
    // every step must be internally consistent
    for (const st of a.steps) {
      const s = S.combine(st.base.s, st.mat.s, mults);
      if (s.join() !== st.result.s.join()) { failures++; console.log(`FAIL  ${name}: step mismatch`, st); }
      if (st.base.L !== st.L - 1 || st.mat.L > st.base.L) { failures++; console.log(`FAIL  ${name}: level rule broken`, st); }
    }
  }
  return r;
}

// ---- reference values from the independent Python prototype ----
run('Base20', [20], [M.combat], 260);
run('Wooden Sword', [10, 5], [M.combat, M.combat], 158);
run('Mindbreaker', [145], [M.combat], 409);
run('Iron Sword', [24, 14], [M.combat, M.combat], 286);
run('Purpurite Sword', [94, 20, 14], [M.combat, M.crit, M.combat], 364);
run('Wind Ghost Amulet', [5], [M.combat], 101);
run('Platinum Dagger', [17, 30], [M.crit, M.crit], 119);

const c20 = S.perfectChain([20], [M.combat]);
run('Base20 + 1xP5', [20], [M.combat], 248, [{ level: 5, stats: c20[5], qty: 1 }]);
run('Base20 + 2xP5', [20], [M.combat], 236, [{ level: 5, stats: c20[5], qty: 2 }]);
run('Base20 + 3xP5 + 1xL7(68) + 2xP3', [20], [M.combat], 193, [
  { level: 5, stats: c20[5], qty: 3 }, { level: 7, stats: [68], qty: 1 }, { level: 3, stats: c20[3], qty: 2 }]);
run('Base20 + 10xP3', [20], [M.combat], 220, [{ level: 3, stats: c20[3], qty: 10 }]);
const cw = S.perfectChain([10, 5], [M.combat, M.combat]);
run('Wooden Sword + 2xP6 + 1xP4', [10, 5], [M.combat, M.combat], 118, [
  { level: 6, stats: cw[6], qty: 2 }, { level: 4, stats: cw[4], qty: 1 }]);
const cp = S.perfectChain([94, 20, 14], [M.combat, M.crit, M.combat]);
run('Purpurite + 1xP7 + 2xP5', [94, 20, 14], [M.combat, M.crit, M.combat], 280, [
  { level: 7, stats: cp[7], qty: 1 }, { level: 5, stats: cp[5], qty: 2 }]);

// a big inventory (30 P2, 20 P3, 9 P4): solved exactly (57, the same as an unlimited plain search), merges and all
{
  const owned = [{ level: 3, stats: c20[3], qty: 20 }, { level: 4, stats: c20[4], qty: 9 }, { level: 2, stats: c20[2], qty: 30 }];
  const r = S.solve({ base: [20], mults: [M.combat], level: 10, target: c20[10], owned });
  const a = S.analyze(r.plan, owned.length);
  console.log(`big inventory: mode=${r.mode} K=${r.K} cost=${r.cost} use=${a.ownedUse} ms=${r.ms}`);
  if (r.mode !== 'exact' || r.cost !== 57 || a.p1 !== r.cost) { failures++; console.log('FAIL big inventory'); }
  a.ownedUse.forEach((n, j) => { if (n > owned[j].qty) { failures++; console.log(`FAIL capped: owned ${j} used ${n} > qty ${owned[j].qty}`); } });
  for (const st of a.steps) {
    const s = S.combine(st.base.s, st.mat.s, [M.combat]);
    if (!(s[0] >= st.result.s[0]) || st.base.L !== st.L - 1 || st.mat.L > st.base.L) { failures++; console.log('FAIL capped step', st); }
  }
  // the final item must still meet the target
  if (r.plan.nodes[r.plan.root].s[0] < c20[10][0]) { failures++; console.log('FAIL capped target'); }
}

// lower targets (81 confirmed by the independent Python prototype)
run('Base20 target P10 >= 120', [20], [M.combat], 81, [], 10, [120]);
run('Base20 target P6', [20], [M.combat], 21, [], 6);

// brute force cross-check up to level 6 for a few bases
function bruteMin(base, mults, level, target) {
  const memo = new Map();
  function trees(L) {          // all (cost, stats) reachable at level L (deduped)
    if (memo.has(L)) return memo.get(L);
    let out;
    if (L === 1) out = [{ c: 1, s: base }];
    else {
      const bases = trees(L - 1);
      let mats = [];
      for (let m = 1; m < L; m++) mats = mats.concat(trees(m));
      const seen = new Map();
      for (const x of bases) for (const y of mats) {
        const s = S.combine(x.s, y.s, mults), c = x.c + y.c, key = s.join() + '|' + c;
        if (!seen.has(key)) seen.set(key, { c, s });
      }
      out = Array.from(seen.values());
    }
    memo.set(L, out);
    return out;
  }
  let best = null;
  for (const t of trees(level)) if (t.s.every((v, i) => v >= target[i]) && (best === null || t.c < best)) best = t.c;
  return best;
}
for (const [name, base, mults] of [['b20', [20], [M.combat]], ['ws', [10, 5], [M.combat, M.combat]], ['pd', [17, 30], [M.crit, M.crit]], ['amulet', [5], [M.combat]]]) {
  for (let L = 2; L <= 6; L++) {
    const chain = S.perfectChain(base, mults);
    const r = S.solve({ base, mults, level: L, target: chain[L], owned: [] });
    check(`brute ${name} P${L}`, r.cost, bruteMin(base, mults, L, chain[L]));
  }
}

// Safe's margin: 1 less per stat when neither item is perfect (brute force over every tree up to level 5)
{
  const rates = [{ num: 1, den: 4 }, { num: 1, den: 4 }];
  const ctx = S.makeCtx('robust', [], 2), chain = S.perfectChain([35, 50], rates, 6, ctx);
  check('margin: perfect + imperfect unchanged', S.combine([82, 120], [79, 116], rates, ctx, 5, 5).join('/'), S.combine([82, 120], [79, 116], rates, S.makeCtx('robust', [], 2), 5, 5).join('/'));   // a ctx without the chain: no margin
  check('margin: imperfect pair 1 lower', S.combine([79, 116], [79, 116], rates, ctx, 5, 5).join('/'), '97/144');
  const memo = new Map();
  function trees(L) {
    if (memo.has(L)) return memo.get(L);
    let out;
    if (L === 1) out = [{ c: 1, s: [35, 50] }];
    else {
      const seen = new Map();
      for (const x of trees(L - 1)) for (let m = 1; m < L; m++) for (const y of trees(m)) {
        const s = S.combine(x.s, y.s, rates, ctx, L - 1, m), c = x.c + y.c, key = s.join() + '|' + c;
        if (!seen.has(key)) seen.set(key, { c, s });
      }
      out = Array.from(seen.values());
    }
    memo.set(L, out);
    return out;
  }
  for (const L of [4, 5]) for (const k of [0, 2, 4, 6]) {
    const target = chain[L].map(v => v - k);
    let best = null;
    for (const t of trees(L)) if (t.s.every((v, i) => v >= target[i]) && (best === null || t.c < best)) best = t.c;
    const r = S.solve({ base: [35, 50], rates, level: L, target, owned: [], model: 'robust' });
    check(`margin brute P${L}-${k}`, r.cost, best);
  }
}

// ---- formula variants & observation overrides ----
{
  const rates = [{ num: 1, den: 4, f64: 0.25, dec: 0.25 }];
  // every model agrees on a perfect P2 from 20
  for (const m of S.models) check(`model ${m.key} P1+P1`, S.predict(m.key, [20], [20], rates)[0], m.key === 'min1' || true ? 25 : 25);
  // robust can never exceed exact
  const rExact = S.solve({ base: [20], rates, level: 10, target: c20[10], owned: [], model: 'exact' });
  const rRobust = S.solve({ base: [20], rates, level: 10, target: c20[10], owned: [], model: 'robust' });
  console.log(`robust cost ${rRobust.cost} vs exact ${rExact.cost} (chain P10 ${rRobust.chain[10]} vs ${rExact.chain[10]})`);
  if (rRobust.cost < rExact.cost) { failures++; console.log('FAIL robust cheaper than exact'); }
  // count boundary recipes in the exact plan where the 32-bit legacy expression disagrees
  const a = S.analyze(rExact.plan, 0);
  let disagree = 0;
  for (const st of a.steps) {
    const p32 = S.predict('v1f32', st.base.s, st.mat.s, rates)[0];
    if (p32 !== st.result.s[0]) disagree++;
  }
  console.log(`exact plan has ${a.steps.length} recipes, ${disagree} where float32 legacy math lands lower`);
  // an observation override changes the perfect chain and the plan
  const overrides = [{ baseL: 1, base: [20], matL: 1, mat: [20], actual: [24] }];
  const rO = S.solve({ base: [20], rates, level: 3, target: null, owned: [], model: 'exact', overrides });
  check('override changes P2', rO.chain[2][0], 24);
  check('override hits counted', rO.overrideHits > 0, true);
  const aO = S.analyze(rO.plan, 0);
  const p2 = aO.steps.find(st => st.L === 2);
  check('override applied in plan', p2 && p2.result.s[0], 24);
  // level-specific override must not leak to other levels with the same stats
  const rO2 = S.solve({ base: [20], rates, level: 4, target: null, owned: [], model: 'exact', overrides: [{ baseL: 2, base: [25], matL: 1, mat: [20], actual: [29] }] });
  const aO2 = S.analyze(rO2.plan, 0);
  const leaked = aO2.steps.some(st => !(st.base.L === 2 && st.mat.L === 1) && st.base.s[0] === 25 && st.mat.s[0] === 20 && st.result.s[0] === 29);
  check('override level-specific', leaked, false);
}

// ---- owned items against exhaustive search (every reachable item and usage, no pruning) ----
{
  const exact = (b, m, r) => b.map((v, i) => Math.floor((v * r[i].den + Math.max(2 * r[i].den, m[i] * r[i].num)) / r[i].den));
  function brute(base, rates, maxL, owned) {
    const q = owned.map(o => o.qty), F = [null];
    for (let L = 1; L <= maxL; L++) F.push(new Map());
    const put = (L, s, u, p) => { const k = s.join(',') + '|' + u.join(','); const o = F[L].get(k); if (!o || o.p > p) F[L].set(k, { s, u, p }); };
    put(1, base, q.map(() => 0), 1);
    owned.forEach((o, j) => { const u = q.map(() => 0); u[j] = 1; put(o.level, o.stats, u, 0); });
    for (let L = 2; L <= maxL; L++) {
      const mats = []; for (let l = 1; l < L; l++) mats.push(...F[l].values());
      for (const x of [...F[L - 1].values()]) for (const y of mats) {
        const u = x.u.map((v, j) => v + y.u[j]); if (u.some((v, j) => v > q[j])) continue;
        put(L, exact(x.s, y.s, rates), u, x.p + y.p);
      }
    }
    return F;
  }
  let seed = 99; const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return Math.floor(seed / 65536) % n; };
  const bases = [[[20], [M.combat]], [[10, 5], [M.combat, M.combat]], [[17, 30], [M.crit, M.crit]], [[45, 12], [M.combat, M.resource]], [[94, 20], [M.combat, M.crit]]];
  let bad = 0;
  for (let t = 0; t < 60; t++) {
    const [base, rates] = bases[rnd(bases.length)], maxL = 5 + rnd(2), chain = S.perfectChain(base, rates, maxL);
    const owned = [];
    for (let j = 0, m = 1 + rnd(3); j < m; j++) { const lv = 2 + rnd(maxL - 2); owned.push({ level: lv, stats: rnd(3) ? chain[lv].slice() : chain[lv].map(v => Math.max(1, v - 1 - rnd(3))), qty: 1 + rnd(3) }); }
    const target = rnd(2) ? chain[maxL] : chain[maxL].map(v => v - 2);
    let want = null; for (const v of brute(base, rates, maxL, owned)[maxL].values()) if (v.s.every((x, i) => x >= target[i])) want = want == null ? v.p : Math.min(want, v.p);
    const r = S.solve({ base, rates, level: maxL, maxLevel: maxL, target, owned });
    if (r.cost !== want) { bad++; console.log(`FAIL owned brute ${JSON.stringify({ base, maxL, owned, target })}: solver ${r.cost}, best ${want}`); }
    else if (r.plan) {
      const a = S.analyze(r.plan, owned.length);
      a.ownedUse.forEach((n, j) => { if (n > owned[j].qty) { bad++; console.log('FAIL owned overuse', j); } });
    }
  }
  check('owned items: 60 random inventories match exhaustive search', bad, 0);
  // nine perfect P2 make a P5 (a world boss weapon's max) out of nothing
  const cf = S.perfectChain([94, 20], [M.combat, M.crit], 5);
  check('9 perfect P2 -> free P5', S.solve({ base: [94, 20], rates: [M.combat, M.crit], level: 5, maxLevel: 5, target: cf[5], owned: [{ level: 2, stats: cf[2], qty: 9 }] }).cost, 0);
  // identical owned rows are solved as one and their uses handed back row by row
  const rs = S.solve({ base: [94, 20], rates: [M.combat, M.crit], level: 5, maxLevel: 5, target: cf[5], owned: [{ level: 2, stats: cf[2], qty: 5 }, { level: 2, stats: cf[2], qty: 4 }] });
  const as = S.analyze(rs.plan, 2);
  check('identical rows: cost', rs.cost, 0);
  check('identical rows: uses split 5 + 3', as.ownedUse.join('+'), '5+3');
  // perfect items of the rows below merge into the missing ones: 25 P2 and 3 P5 (174, as a plain unlimited search)
  const c20b = S.perfectChain([20], [M.combat], 10);
  const rg = S.solve({ base: [20], rates: [M.combat], level: 10, maxLevel: 10, target: c20b[10], owned: [{ level: 2, stats: c20b[2], qty: 25 }, { level: 5, stats: c20b[5], qty: 3 }] });
  const ag = S.analyze(rg.plan, 2);
  check('merge gaps: cost', rg.cost, 174);
  check('merge gaps: counts kept', ag.ownedUse.every((u, j) => u <= [25, 3][j]), true);
  check('merge gaps: every step recomputes', ag.steps.every(st => S.combine(st.base.s, st.mat.s, [M.combat]).join() === st.result.s.join() && st.base.L === st.L - 1 && st.mat.L <= st.base.L), true);
  // a big typed inventory, searched without work limits (what the app runs in the background): the proven best
  const cf2 = S.perfectChain([50, 10], [M.combat, M.combat], 10);
  const typedReq = { base: [50, 10], rates: [M.combat, M.combat], level: 10, maxLevel: 10, target: cf2[10],
    owned: [{ level: 4, stats: [cf2[4][0] - 2, cf2[4][1] - 1], qty: 12 }, { level: 4, stats: cf2[4], qty: 9 }, { level: 2, stats: cf2[2], qty: 14 }, { level: 3, stats: cf2[3], qty: 12 }] };
  const rq = S.solve(typedReq), rx = S.solve(Object.assign({}, typedReq, { exhaustive: true }));
  const ax = S.analyze(rx.plan, 4);
  check('exhaustive: never worse than the quick plan', rx.cost <= rq.cost, true);
  check('exhaustive: exact', rx.mode === 'exact' || rx.mode === 'proven', true);
  check('exhaustive: counts kept', ax.ownedUse.every((u, j) => u <= typedReq.owned[j].qty), true);
  check('exhaustive: every step recomputes', ax.steps.every(st => S.combine(st.base.s, st.mat.s, typedReq.rates).join() === st.result.s.join()), true);
  // nothing is computed above the item's max level
  check('max level respected', S.solve({ base: [94, 20], rates: [M.combat, M.crit], level: 5, maxLevel: 5, target: cf[5], owned: [] }).ladder.filter(r => r.level > 5).every(r => r.cost == null), true);
}

console.log(failures ? `\n${failures} FAILURE(S)` : '\nall good');
process.exit(failures ? 1 : 0);
