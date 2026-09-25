/* PORE refinement solver — pure logic, no DOM.
 *
 * Runs inside a Web Worker, on the main thread, or in Node (see tools/test_solver.mjs).
 * The whole solver is wrapped in createSolver() so it can be stringified into a worker.
 *
 * Model (the formula PORE v1 used, verified in-game by the community):
 *   Refining a BASE item (level L) with a MATERIAL item (level <= L) yields level L+1.
 *   For every stat i:  result_i = floor(base_i + max(2, material_i * rate_i))
 *   where rate_i is the stat category rate (combat 1/4, critical 1/6, resource 1/8, gathering 1/16).
 *   Only items of the same kind can be combined. Cost is counted in base (P1) items consumed.
 *
 * Rounding variants ("models") exist because the game occasionally lands 1 off the exact formula;
 * observations recorded in the app override the formula for the exact recipes that were seen,
 * and the "robust" model plans only with results every plausible variant agrees on.
 *
 * Algorithm: bottom-up dynamic programming over refinement levels keeping, per level, the
 * Pareto frontier of (cost, stats) — a state is dropped when another state at the same level
 * is at least as cheap and at least as good in every stat. Owned items are free leaves; their
 * limited quantity is tracked exactly as a usage vector inside the frontier while the usage
 * lattice is small. Larger inventories are solved with capped quantities and the leftovers are
 * substituted greedily into the expanded plan (feasible, near-optimal, flagged "approximate").
 */
function createSolver() {
  'use strict';

  const MIN_GAIN = 2;              // every refine adds at least +2 to each stat
  const MAX_LEVEL = 10;
  const K_MAX = 64;                // largest owned-usage lattice solved exactly
  const CANDIDATE_BUDGET = 3e6;    // per-level base x material pairs before reducing the lattice

  const GOLD = { 2: 250, 3: 500, 4: 750, 5: 1000, 6: 1250, 7: 1500, 8: 1750, 9: 2000, 10: 3000 };
  const SUCCESS = { 2: 100, 3: 60, 4: 30, 5: 20, 6: 10, 7: 5, 8: 3, 9: 1, 10: 0.5 };

  const now = () => (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now());
  const f32 = Math.fround;

  function sum(a) { let t = 0; for (let i = 0; i < a.length; i++) t += a[i]; return t; }
  function geq(a, b) { for (let i = 0; i < a.length; i++) if (a[i] < b[i]) return false; return true; }
  function leq(a, b) { for (let i = 0; i < a.length; i++) if (a[i] > b[i]) return false; return true; }

  /* ---------- formula variants ----------
   * rate = { num, den, f64, dec }:
   *   num/den  exact fraction (1/4, 1/6, 1/8, 1/16)
   *   f64      the constant PORE v1 used (0.25, 0.16666667, 0.125, 0.0625)
   *   dec      the percentage as printed on the wiki (0.25, 0.167, 0.125, 0.0625)
   * Every model maps (base[], mat[], rates[]) -> result[] so item-level variants are possible.
   */
  function perStat(fn) { return (b, m, r) => b.map((v, i) => fn(v, m[i], r[i])); }
  const MODELS = {
    exact: { label: 'Exact fractions, round down', group: 'per stat',
      desc: 'floor(base + max(2, material × rate)) with the rate as an exact fraction. PORE default.',
      fn: perStat((b, m, r) => Math.floor((b * r.den + Math.max(MIN_GAIN * r.den, m * r.num)) / r.den)) },
    v1f64: { label: 'Legacy expression, 64-bit float', group: 'per stat',
      desc: 'base × rate × (1 − (base − material) / base) in double precision, exactly as PORE v1 computed it.',
      fn: perStat((b, m, r) => Math.floor(b + Math.max(MIN_GAIN, b * r.f64 * (1 - (b - m) / b)))) },
    v1f32: { label: 'Legacy expression, 32-bit float', group: 'per stat',
      desc: 'The same expression in single precision, the way a game engine would evaluate it. Lands 1 short on some high-stat boundaries.',
      fn: perStat((b, m, r) => { const ratio = f32(f32(b - m) / b); const gain = f32(f32(b * f32(r.f64)) * f32(1 - ratio)); return Math.floor(f32(b + Math.max(MIN_GAIN, gain))); }) },
    dec64: { label: 'Wiki percentages, 64-bit float', group: 'per stat',
      desc: 'material × 0.167 (etc.), using the rounded percentages printed on the wiki.',
      fn: perStat((b, m, r) => Math.floor(b + Math.max(MIN_GAIN, m * r.dec))) },
    dec32: { label: 'Wiki percentages, 32-bit float', group: 'per stat',
      desc: 'The same in single precision.',
      fn: perStat((b, m, r) => Math.floor(f32(b + Math.max(MIN_GAIN, f32(m * f32(r.dec)))))) },
    main64: { label: 'Main-stat penalty, 64-bit float', group: 'item level',
      desc: 'One penalty ratio from the first stat (1 − (base − material) / base) applied to every stat. Explains ±1 quirks on multi-stat items.',
      fn: (b, m, r) => { const pen = 1 - (b[0] - m[0]) / b[0]; return b.map((v, i) => Math.floor(v + Math.max(MIN_GAIN, v * r[i].f64 * pen))); } },
    main32: { label: 'Main-stat penalty, 32-bit float', group: 'item level',
      desc: 'The same in single precision.',
      fn: (b, m, r) => { const pen = f32(1 - f32(f32(b[0] - m[0]) / b[0])); return b.map((v, i) => Math.floor(f32(v + Math.max(MIN_GAIN, f32(f32(v * f32(r[i].f64)) * pen))))); } },
    round: { label: 'Round to nearest', group: 'per stat',
      desc: 'base + max(2, round(material × rate)).',
      fn: perStat((b, m, r) => b + Math.max(MIN_GAIN, Math.floor(m * r.num / r.den + 0.5))) },
    ceil: { label: 'Round up', group: 'per stat',
      desc: 'base + max(2, ceil(material × rate)).',
      fn: perStat((b, m, r) => b + Math.max(MIN_GAIN, Math.ceil(m * r.num / r.den - 1e-9))) },
    min1: { label: 'Exact, minimum gain +1', group: 'per stat',
      desc: 'Like the default but the guaranteed gain is +1 instead of +2.',
      fn: perStat((b, m, r) => Math.floor((b * r.den + Math.max(1 * r.den, m * r.num)) / r.den)) },
  };
  const ROBUST_SET = ['exact', 'v1f64', 'v1f32', 'dec64', 'dec32', 'main64', 'main32'];
  MODELS.robust = { label: 'Safe: lowest of all plausible variants', group: 'safe',
    desc: 'Plans with, per stat, the lowest result any plausible variant predicts, so a refine can never come up short at a rounding boundary. Costs a few more items.',
    fn: (b, m, r) => { let out = null; for (const k of ROBUST_SET) { const v = MODELS[k].fn(b, m, r); out = out ? out.map((x, i) => Math.min(x, v[i])) : v; } return out; } };

  function normRate(r) {
    return { num: r.num, den: r.den, f64: r.f64 != null ? r.f64 : r.num / r.den, dec: r.dec != null ? r.dec : r.num / r.den };
  }

  function recipeKey(baseL, base, matL, mat) { return baseL + ':' + base.join(',') + '|' + matL + ':' + mat.join(','); }

  /* ctx = { model: fn, overrides: Map|null } */
  function makeCtx(modelName, overrides, nStats) {
    const model = MODELS[modelName] || MODELS.exact;
    let map = null;
    if (overrides && overrides.length) {
      map = new Map();
      for (const o of overrides) {
        if (!o || !o.base || !o.mat || !o.actual || o.actual.length !== nStats) continue;
        map.set(recipeKey(o.baseL, o.base, o.matL, o.mat), o.actual.map(Number));
      }
    }
    return { model: model.fn, name: model.fn === MODELS.exact.fn ? 'exact' : modelName, overrides: map, hits: 0 };
  }

  function combine(base, mat, rates, ctx, baseL, matL) {
    if (ctx && ctx.overrides) {
      const hit = ctx.overrides.get(recipeKey(baseL, base, matL, mat));
      if (hit) { ctx.hits++; return hit.slice(); }
    }
    return (ctx ? ctx.model : MODELS.exact.fn)(base, mat, rates);
  }

  function predict(modelName, base, mat, rates) {
    return (MODELS[modelName] || MODELS.exact).fn(base.map(Number), mat.map(Number), rates.map(normRate));
  }

  function perfectChain(base, rates, maxLevel, ctx) {
    const rr = rates.map(normRate);
    const chain = [null, base.slice()];
    for (let L = 2; L <= (maxLevel || MAX_LEVEL); L++) chain[L] = combine(chain[L - 1], chain[L - 1], rr, ctx, L - 1, L - 1);
    return chain;
  }

  function meets(stats, target) {
    for (let i = 0; i < stats.length; i++) {
      const t = target[i];
      if (t != null && stats[i] < t) return false;
    }
    return true;
  }

  // kind: 0 = base item (P1), 1 = owned item, 2 = refine(base, mat)
  function mkState(L, p, s, u, kind, b, m, j) {
    return { L: L, p: p, s: s, u: u, k: kind, b: b, m: m, j: j, t: sum(s) };
  }

  // Keep non-dominated states. Dominance: cost <=, usage <= (all), stats >= (all).
  function pareto(list, hasU) {
    list.sort((a, b) => (a.p - b.p) || (b.t - a.t) || (hasU ? sum(a.u) - sum(b.u) : 0));
    const kept = [];
    outer: for (let i = 0; i < list.length; i++) {
      const s = list[i];
      for (let j = 0; j < kept.length; j++) {
        const k = kept[j];
        if (k.t < s.t) continue;                  // cannot dominate with a smaller stat sum
        if (hasU && !leq(k.u, s.u)) continue;
        if (geq(k.s, s.s)) continue outer;
      }
      kept.push(s);
    }
    return kept;
  }

  class BudgetExceeded extends Error {}

  /* Frontier DP. owned = [{level, stats, qty}], qty already capped by the caller. */
  function solveCore(base, rates, maxLevel, owned, ctx) {
    const n = base.length;
    const hasU = owned.length > 0;
    const q = owned.map(o => o.qty);
    const zeroU = hasU ? owned.map(() => 0) : null;

    // numeric dedupe keys: stats in mixed radix R, usage in mixed radix (q+1)
    let R = 2;
    const chain = perfectChain(base, rates, maxLevel, ctx);
    for (let L = 1; L <= maxLevel; L++) for (const v of chain[L]) R = Math.max(R, v + 2);
    for (const o of owned) for (const v of o.stats) R = Math.max(R, v + 2);
    if (ctx && ctx.overrides) for (const v of ctx.overrides.values()) for (const x of v) R = Math.max(R, x + 2);
    let K = 1;
    for (const c of q) K *= (c + 1);

    const F = [];
    for (let L = 0; L <= maxLevel; L++) F.push([]);
    F[1].push(mkState(1, 1, base.slice(), zeroU, 0, null, null, -1));
    owned.forEach((o, j) => {
      if (o.level < 2 || o.level > maxLevel || o.qty <= 0) return;
      const u = zeroU.slice(); u[j] = 1;
      F[o.level].push(mkState(o.level, 0, o.stats.slice(), u, 1, null, null, j));
    });

    let mats = pareto(F[1].slice(), hasU);
    const sizes = [0, F[1].length];
    for (let L = 2; L <= maxLevel; L++) {
      const bases = F[L - 1];
      if (bases.length * mats.length > CANDIDATE_BUDGET) throw new BudgetExceeded('too many candidates');
      const best = new Map();
      for (let xi = 0; xi < bases.length; xi++) {
        const x = bases[xi];
        for (let yi = 0; yi < mats.length; yi++) {
          const y = mats[yi];
          let u = null, uKey = 0;
          if (hasU) {
            u = new Array(q.length);
            let ok = true, radix = 1;
            for (let j = 0; j < q.length; j++) {
              const v = x.u[j] + y.u[j];
              if (v > q[j]) { ok = false; break; }
              u[j] = v; uKey += v * radix; radix *= (q[j] + 1);
            }
            if (!ok) continue;
          }
          const s = combine(x.s, y.s, rates, ctx, x.L, y.L);
          let key = 0;
          for (let i = n - 1; i >= 0; i--) key = key * R + Math.min(s[i], R - 1);
          key = key * K + uKey;
          const p = x.p + y.p;
          const prev = best.get(key);
          if (prev === undefined || prev.p > p) best.set(key, mkState(L, p, s, u, 2, x, y, -1));
        }
      }
      const list = F[L].concat(Array.from(best.values()));
      F[L] = pareto(list, hasU);
      sizes.push(F[L].length);
      if (L < maxLevel) mats = pareto(mats.concat(F[L]), hasU);
    }
    return { F: F, sizes: sizes, chain: chain };
  }

  function choose(list, target) {
    let best = null;
    for (let i = 0; i < list.length; i++) {
      const s = list[i];
      if (!meets(s.s, target)) continue;
      if (!best || s.p < best.p || (s.p === best.p && s.t > best.t)) best = s;
    }
    return best;
  }

  /* ---------- plan trees ---------- */

  // Expand a (shared) plan tree into an explicit tree of physical items.
  function expand(nd, parentBaseLevel) {
    const node = { L: nd.L, p: nd.p, s: nd.s, k: nd.k, j: nd.j, b: null, m: null, dead: false };
    if (nd.k === 2) {
      node.b = expand(nd.b, nd.b.L);
      node.m = expand(nd.m, nd.b.L);
    }
    node.baseLevel = parentBaseLevel;   // level of the base item this node is combined with (material role)
    return node;
  }

  // Greedily replace the most expensive sub-trees with leftover owned items that dominate them.
  function substitute(root, owned, leftover) {
    const all = [];
    (function collect(nd, role) { nd.role = role; all.push(nd); if (nd.k === 2) { collect(nd.b, 'base'); collect(nd.m, 'mat'); } })(root, 'root');
    all.sort((a, b) => b.p - a.p);
    const order = owned.map((o, j) => j).sort((a, b) => owned[b].level - owned[a].level);
    let saved = 0;
    for (const j of order) {
      const o = owned[j];
      while (leftover[j] > 0) {
        let target = null;
        for (const nd of all) {
          if (nd.dead || nd.k !== 2 || nd.p <= 0) continue;
          if (!geq(o.stats, nd.s)) continue;
          if (nd.role === 'mat' ? o.level > nd.baseLevel : o.level !== nd.L) continue;
          target = nd; break;
        }
        if (!target) break;
        (function kill(nd) { nd.dead = true; if (nd.k === 2) { kill(nd.b); kill(nd.m); } })(target);
        saved += target.p;
        target.dead = false;
        target.k = 1; target.j = j; target.p = 0; target.b = null; target.m = null; target.s = o.stats.slice();
        leftover[j]--;
      }
    }
    // recompute p bottom-up
    (function fix(nd) { if (nd.k === 2) { fix(nd.b); fix(nd.m); nd.p = nd.b.p + nd.m.p; } })(root);
    return saved;
  }

  // Rebuild a shared DAG (structural hashing) and serialize it.
  function serializeTree(root) {
    const nodes = [];
    const memo = new Map();
    function visit(nd) {
      let bId = -1, mId = -1;
      if (nd.k === 2) { bId = visit(nd.b); mId = visit(nd.m); }
      const key = nd.k + ':' + nd.L + ':' + nd.s.join(',') + ':' + (nd.k === 1 ? nd.j : '') + ':' + bId + ':' + mId;
      if (memo.has(key)) return memo.get(key);
      const id = nodes.length;
      nodes.push({ id: id, L: nd.L, p: nd.p, s: nd.s.slice(), k: nd.k, j: nd.j, b: bId, m: mId });
      memo.set(key, id);
      return id;
    }
    const root_ = visit(root);
    return { nodes: nodes, root: root_ };
  }

  function usageOf(plan, nOwned) {
    const a = analyze(plan, nOwned);
    return a.ownedUse;
  }

  /* req = { base:[..], rates:[{num,den,f64,dec}..], level, target:[number|null ..],
             owned:[{level, stats:[..], qty}], model:'exact'|..., overrides:[{baseL, base, matL, mat, actual}] } */
  function solve(req) {
    const t0 = now();
    const base = req.base.map(Number);
    const rates = (req.rates || req.mults).map(normRate);
    const level = Math.min(MAX_LEVEL, Math.max(2, req.level | 0));
    const owned = (req.owned || []).filter(o => o && o.qty > 0 && o.level >= 2 && o.level <= MAX_LEVEL)
      .map(o => ({ level: o.level | 0, stats: o.stats.map(Number), qty: o.qty | 0 }));
    const target = (req.target || base.map(() => null)).map(t => (t == null ? null : Number(t)));
    const ctx = makeCtx(req.model || 'exact', req.overrides || [], base.length);

    // Cap quantities so the usage lattice stays small; higher-level items get priority.
    const caps = owned.map(() => 0);
    let K = 1;
    const prio = owned.map((o, j) => j).sort((a, b) => (owned[b].level - owned[a].level) || (sum(owned[b].stats) - sum(owned[a].stats)));
    let grew = true;
    while (grew) {
      grew = false;
      for (const j of prio) {
        if (caps[j] >= owned[j].qty) continue;
        const K2 = K / (caps[j] + 1) * (caps[j] + 2);
        if (K2 > K_MAX) continue;
        caps[j]++; K = K2; grew = true;
      }
    }

    let res = null, pick = null;
    let capped = owned.map((o, j) => ({ level: o.level, stats: o.stats, qty: caps[j] }));
    for (;;) {
      try {
        res = solveCore(base, rates, MAX_LEVEL, capped, ctx);
        pick = choose(res.F[level], target);
        break;
      } catch (err) {
        if (!(err instanceof BudgetExceeded)) throw err;
        // shrink the lattice and retry
        const active = capped.filter(o => o.qty > 0);
        if (!active.length) { res = solveCore(base, rates, MAX_LEVEL, [], ctx); pick = choose(res.F[level], target); break; }
        capped = capped.map(o => ({ level: o.level, stats: o.stats, qty: Math.floor(o.qty / 2) }));
      }
    }
    const chain = res.chain;
    const exact = capped.every((o, j) => o.qty === owned[j].qty);

    let plan = null, substituted = 0;
    if (pick) {
      const tree = expand(pick, pick.L);
      if (!exact) {
        const used = usageOf(serializeTree(tree), owned.length);
        const leftover = owned.map((o, j) => o.qty - used[j]);
        substituted = substitute(tree, owned, leftover);
      }
      plan = serializeTree(tree);
    }

    const ladder = [];
    for (let L = 2; L <= MAX_LEVEL; L++) {
      const s = choose(res.F[L], chain[L]);
      ladder.push({ level: L, cost: s ? s.p : null, standard: Math.pow(2, L - 1) });
    }

    return {
      ok: !!pick,
      mode: exact ? 'exact' : 'capped',
      approximate: !exact,
      K: K,
      substituted: substituted,
      sizes: res.sizes,
      ladder: ladder,
      chain: chain,
      plan: plan,
      cost: plan ? plan.nodes[plan.root].p : null,
      standard: Math.pow(2, level - 1),
      overrideHits: ctx.hits,
      model: ctx.name,
      ms: Math.round(now() - t0),
    };
  }

  // Cheapest perfect item from scratch (used for catalogue badges).
  function cheapest(base, rates, level, modelName) {
    const L = level || MAX_LEVEL;
    const ctx = makeCtx(modelName || 'exact', [], base.length);
    const res = solveCore(base, rates.map(normRate), L, [], ctx);
    const s = choose(res.F[L], res.chain[L]);
    return s ? s.p : null;
  }

  /* Turn a serialized plan into grouped crafting steps.
     Returns { steps:[{id, L, count, result, base, mat}], p1, ownedUse:[], refines, gold, byLevel:{L:{count,gold}}, count:[] } */
  function analyze(plan, nOwned) {
    const nodes = plan.nodes;
    const count = new Array(nodes.length).fill(0);
    count[plan.root] = 1;
    for (let id = plan.root; id >= 0; id--) {           // children always have smaller ids
      const nd = nodes[id];
      if (!count[id] || nd.k !== 2) continue;
      count[nd.b] += count[id];
      count[nd.m] += count[id];
    }
    const steps = [];
    const ownedUse = new Array(nOwned || 0).fill(0);
    let p1 = 0, refines = 0, gold = 0;
    const byLevel = {};
    nodes.forEach((nd, id) => {
      const n = count[id];
      if (!n) return;
      if (nd.k === 0) p1 += n;
      else if (nd.k === 1) ownedUse[nd.j] = (ownedUse[nd.j] || 0) + n;
      else {
        steps.push({ id: id, L: nd.L, count: n, result: nd, base: nodes[nd.b], mat: nodes[nd.m] });
        refines += n;
        gold += n * GOLD[nd.L];
        const bl = byLevel[nd.L] || (byLevel[nd.L] = { count: 0, gold: 0 });
        bl.count += n;
        bl.gold += n * GOLD[nd.L];
      }
    });
    // An owned P2 is still a P2: refines with the same stats merge into one step, whether their inputs are
    // crafted or come from your inventory. The crafted node stays the representative (its id keeps old ticks).
    const merged = new Map();
    for (const st of steps) {
      const key = st.L + '|' + st.result.s.join(',') + '|' + st.base.L + ':' + st.base.s.join(',') + '|' + st.mat.L + ':' + st.mat.s.join(',');
      const own = (st.base.k === 1 ? st.count : 0) + (st.mat.k === 1 ? st.count : 0);
      const m = merged.get(key);
      if (!m) { st.ids = [st.id]; st.ownedIn = own; merged.set(key, st); continue; }
      const stOwned = st.base.k === 1 || st.mat.k === 1, mOwned = m.base.k === 1 || m.mat.k === 1;
      if (mOwned && !stOwned) { m.id = st.id; m.result = st.result; m.base = st.base; m.mat = st.mat; }
      m.ids.push(st.id); m.count += st.count; m.ownedIn += own;
    }
    const list = Array.from(merged.values());
    list.sort((a, b) => (a.L - b.L) || (sum(b.result.s) - sum(a.result.s)) || (b.count - a.count));
    return { steps: list, p1: p1, ownedUse: ownedUse, refines: refines, gold: gold, byLevel: byLevel, count: count };
  }

  function standardGold(level) {
    let g = 0;
    for (let L = 2; L <= level; L++) g += Math.pow(2, level - L) * GOLD[L];
    return g;
  }

  const modelList = Object.keys(MODELS).map(k => ({ key: k, label: MODELS[k].label, desc: MODELS[k].desc, group: MODELS[k].group }));

  return { solve: solve, cheapest: cheapest, analyze: analyze, predict: predict, perfectChain: perfectChain, makeCtx: makeCtx,
           combine: (b, m, r, ctx, bl, ml) => combine(b, m, r.map(normRate), ctx, bl, ml),
           standardGold: standardGold, models: modelList, GOLD: GOLD, SUCCESS: SUCCESS, MAX_LEVEL: MAX_LEVEL, MIN_GAIN: MIN_GAIN };
}
