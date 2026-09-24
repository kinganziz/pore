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

// large lattice -> capped exact DP + greedy substitution must stay feasible and beat from-scratch
{
  const owned = [{ level: 3, stats: c20[3], qty: 20 }, { level: 4, stats: c20[4], qty: 9 }, { level: 2, stats: c20[2], qty: 30 }];
  const r = S.solve({ base: [20], mults: [M.combat], level: 10, target: c20[10], owned });
  const a = S.analyze(r.plan, owned.length);
  console.log(`capped mode: mode=${r.mode} K=${r.K} substituted=${r.substituted} cost=${r.cost} use=${a.ownedUse} ms=${r.ms}`);
  if (r.mode !== 'capped' || r.cost >= 200 || a.p1 !== r.cost) { failures++; console.log('FAIL capped mode'); }
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

console.log(failures ? `\n${failures} FAILURE(S)` : '\nall good');
process.exit(failures ? 1 : 0);
