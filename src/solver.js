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
 * lattice is small. At the plan's own level the last step is a lookup, and (default formula) items that
 * cannot be part of any plan meeting the target are skipped, so even big inventories solve exactly. Only if
 * that still grows too big are quantities capped and the leftovers substituted greedily into the expanded
 * plan (feasible, near-optimal, flagged "approximate").
 * With the default formula a material adds gains that do not depend on the base (integer base +
 * floor(...)), so materials are compared by the gains they add: far fewer candidates, same optimum.
 * The DP only runs up to the item's max level; above the requested level it may stop early (the
 * ladder rungs there stay unknown) rather than weaken the plan.
 */
function createSolver() {
  'use strict';

  const MIN_GAIN = 2;              // every refine adds at least +2 to each stat
  const MAX_LEVEL = 10;
  const K_START = 512;             // largest owned-usage lattice tried first (it shrinks while the search is too big)
  const QUICK_K = 64;              // the quick plan's owned-usage lattice (its cost bounds the exact search)
  const QUICK_SKIP = 20000;        // req.quick: from this many owned-usage combinations on, no exact search in the first answer
  const QUICK_K_SEP = 512;         // the same for the fast (separable) search: a wider quick plan, a much better bound
  const CANDIDATE_BUDGET = 3e6;    // per-level base x material pairs before reducing the lattice
  const WORK_BUDGET = 2e7;         // with owned items: pairs tried + frontier comparisons per search (about a second)

  const GOLD = { 2: 250, 3: 500, 4: 750, 5: 1000, 6: 1250, 7: 1500, 8: 1750, 9: 2000, 10: 3000 };
  // base success chance per level (the wiki's table, except where the game's refine screen showed otherwise:
  // level 5 is 15% there, the wiki says 20%; level 6 is 8%, the wiki says 10%)
  const SUCCESS = { 2: 100, 3: 60, 4: 30, 5: 15, 6: 8, 7: 5, 8: 3, 9: 1, 10: 0.5 };

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
    exact: { label: 'Exact fractions, round down', group: 'per stat', sep: true,
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
    round: { label: 'Round to nearest', group: 'per stat', sep: true,
      desc: 'base + max(2, round(material × rate)).',
      fn: perStat((b, m, r) => b + Math.max(MIN_GAIN, Math.floor(m * r.num / r.den + 0.5))) },
    ceil: { label: 'Round up', group: 'per stat', sep: true,
      desc: 'base + max(2, ceil(material × rate)).',
      fn: perStat((b, m, r) => b + Math.max(MIN_GAIN, Math.ceil(m * r.num / r.den - 1e-9))) },
    min1: { label: 'Exact, minimum gain +1', group: 'per stat', sep: true,
      desc: 'Like the default but the guaranteed gain is +1 instead of +2.',
      fn: perStat((b, m, r) => Math.floor((b * r.den + Math.max(1 * r.den, m * r.num)) / r.den)) },
  };
  const ROBUST_SET = ['exact', 'v1f64', 'v1f32', 'dec64', 'dec32', 'main64', 'main32'];
  // margin: the game keeps values its screen doesn't show, and two imperfect items came out 1 lower than the formula
  // (79/116 + 79/116 -> 98/144 instead of 98/145). Safe plans for 1 less per stat whenever neither item is perfect.
  // ubExact: never more than the exact formula (a minimum over variants that include it, less a margin), so the exact
  // formula's gains bound it and the search's usefulness floors hold for it too
  MODELS.robust = { label: 'Safe: lowest of all plausible variants', group: 'safe', margin: true, ubExact: true,
    desc: 'Plans with, per stat, the lowest result any plausible variant predicts, and 1 less per stat when neither item is perfect, so a refine can never come up short. Costs a few more items.',
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
    // sep: the model adds a gain that depends on the material alone (integer base + floor(...)), so materials that
    // add the same gains are interchangeable. Recorded results (overrides) are per recipe and switch this off.
    const ovMat = map ? new Set(overrides.filter(o => o && o.mat).map(o => o.matL + '|' + o.mat.join(','))) : null;
    return { model: model.fn, name: model.fn === MODELS.exact.fn ? 'exact' : modelName, overrides: map, ovMat: ovMat, hits: 0, sep: !!model.sep, ovList: map ? overrides : null,
      margin: !!model.margin, ubExact: !!model.ubExact, chain: null, memo: new Map(), ids: new Map(), tag: ++ctxTag };   // chain: the perfect items, set by perfectChain (the margin needs them)
  }

  // with recorded results the fast search stays on only if none beats the formula (checked once the rates are known)
  function sepCheck(ctx, rates) {
    if (ctx.ubExact && ctx.overrides) for (const o of ctx.ovList) {   // a recorded result above the exact formula: no bound
      if (o && o.base && o.mat && o.actual && o.actual.some((v, i) => Number(v) > MODELS.exact.fn(o.base.map(Number), o.mat.map(Number), rates)[i])) { ctx.ubExact = false; break; }
    }
    if (!ctx.sep || !ctx.overrides) return;
    for (const o of ctx.ovList) {
      if (!o || !o.base || !o.mat || !o.actual) continue;
      const f = ctx.model(o.base.map(Number), o.mat.map(Number), rates);
      if (o.actual.some((v, i) => Number(v) > f[i])) { ctx.sep = false; return; }
    }
  }
  // Results are remembered per solve: the searches meet the same pairs again and again (a slow model such as Safe
  // works each pair out once). An item is known by an id kept on its stats array (level and stats).
  let ctxTag = 0;
  function itemId(ctx, arr, L) {
    if (arr._pt === ctx.tag && arr._pl === L) return arr._pi;
    const k = L + ':' + arr.join(',');
    let id = ctx.ids.get(k);
    if (id === undefined) { id = ctx.ids.size; ctx.ids.set(k, id); }
    arr._pt = ctx.tag; arr._pl = L; arr._pi = id;
    return id;
  }
  function combine(base, mat, rates, ctx, baseL, matL) {
    let key = -1;
    if (ctx && ctx.memo && baseL != null && matL != null) {
      key = itemId(ctx, base, baseL) * 4194304 + itemId(ctx, mat, matL);
      const m = ctx.memo.get(key);
      if (m) { if (m.hit) ctx.hits++; return m.s.slice(); }
      if (ctx.memo.size > 3e6) { ctx.memo.clear(); ctx.ids.clear(); ctx.tag = ++ctxTag; key = -1; }
    }
    let out = null, hit = false;
    if (ctx && ctx.overrides) {
      const h = ctx.overrides.get(recipeKey(baseL, base, matL, mat));
      if (h) { ctx.hits++; out = h.slice(); hit = true; }
    }
    if (!out) {
      out = (ctx ? ctx.model : MODELS.exact.fn)(base, mat, rates);
      if (ctx && ctx.margin && ctx.chain) {
        const pb = ctx.chain[baseL], pm = ctx.chain[matL];
        const perfect = (s, p) => !!p && s.every((v, i) => v === p[i]);
        if (!perfect(base, pb) && !perfect(mat, pm)) for (let i = 0; i < out.length; i++) out[i] = Math.max(base[i], out[i] - 1);
      }
    }
    if (key >= 0) ctx.memo.set(key, { s: out.slice(), hit: hit });
    return out;
  }

  function predict(modelName, base, mat, rates) {
    return (MODELS[modelName] || MODELS.exact).fn(base.map(Number), mat.map(Number), rates.map(normRate));
  }

  function perfectChain(base, rates, maxLevel, ctx) {
    const rr = rates.map(normRate);
    const chain = [null, base.slice()];
    for (let L = 2; L <= (maxLevel || MAX_LEVEL); L++) chain[L] = combine(chain[L - 1], chain[L - 1], rr, ctx, L - 1, L - 1);
    if (ctx && ctx.margin && (!ctx.chain || ctx.chain.length < chain.length)) ctx.chain = chain;
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
    return { L: L, p: p, s: s, u: u, k: kind, b: b, m: m, j: j, t: sum(s), um: -1, w: 0 };   // um: bit mask of the owned rows it uses (worked out when needed)
  }

  // Keep non-dominated states. Dominance: cost <=, usage no worse (uLeq, default: <= for every owned row),
  // stats >= (all). uW orders ties so that a dominating state tends to come first.
  // the work counter of the running search: it gives up (BudgetExceeded) past workLimit
  let work = 0, workLimit = Infinity, boundless = false, subBudget = 0;   // subBudget: a small search inside a bigger one   // boundless: a solve with req.exhaustive (no work limits)
  function spend(n) { work += n; if (work > workLimit) throw new BudgetExceeded('too much work'); }

  // Keep non-dominated states. Dominance: cost <=, stats >= (all), inventory use no worse (inv.leq: owned rows count
  // by count, perfect ones mergeable upwards). Kept states are grouped by their exact stats, so a state is only
  // compared with groups at least as good in every stat; a big group answers from its inventory map instead of
  // comparing with each member (near the target: few distinct stats, thousands of cost / inventory variants).
  function pareto(list, hasU, inv) {
    const uLeq = inv ? inv.leq : leq, uW = inv ? inv.weight : sum, map = hasU && inv ? inv.map : null;
    const n4 = inv ? 1 + (inv.cap.length >> 1) : 1;   // work per marked map point (it tries a move per owned row)
    let cmp = 0;
    if (hasU) for (const s of list) s.w = uW(s.u);   // the inventory weight once per state, not per comparison
    list.sort((a, b) => (a.p - b.p) || (b.t - a.t) || (hasU ? a.w - b.w : 0));
    const groups = new Map(), glist = [], kept = [];   // glist: highest stat total first, so a scan stops at the first lower one
    outer: for (let i = 0; i < list.length; i++) {
      const s = list[i];
      let si = -1;
      for (let gi = 0; gi < glist.length; gi++) {
        const g = glist[gi];
        if ((++cmp & 8191) === 0) spend(8192);
        if (g.t < s.t) break;                       // this group and all after it are weaker in total
        if (!geq(g.s, s.s)) continue;              // not as good in every stat
        if (!hasU) continue outer;                  // kept states come first in cost order: this one is dominated
        if (g.bits) { if (si < 0) si = map.idx(s.u); if (map.has(g.bits, si)) continue outer; continue; }
        const ks = g.k;
        for (let j = 0; j < ks.length; j++) {
          if ((++cmp & 8191) === 0) spend(8192);
          if (uLeq(ks[j].u, s.u)) continue outer;
        }
      }
      const key = s.s.join(',');
      let g = groups.get(key);
      if (!g) {
        g = { s: s.s, t: s.t, k: [], bits: null }; groups.set(key, g);
        let lo = 0, hi = glist.length;   // keep glist in descending total
        while (lo < hi) { const mid = (lo + hi) >> 1; if (glist[mid].t >= g.t) lo = mid + 1; else hi = mid; }
        glist.splice(lo, 0, g);
      }
      g.k.push(s);
      if (map) {
        if (g.bits) spend(map.up(g.bits, s.u) * n4);
        else if (g.k.length >= 24) { g.bits = new Uint32Array(map.words); spend(map.words); for (const k of g.k) spend(map.up(g.bits, k.u) * n4); }
      }
      kept.push(s);
    }
    return kept;
  }

  class BudgetExceeded extends Error {}

  /* Owned inventory. A perfect owned item can always be merged upwards for free (two perfect P(l) refine into a
     perfect P(l+1), no base item needed). So the DP counts, per owned row, how many of that item a plan *asks for*
     (its demand), and a demand is fine when the inventory covers it: every perfect row can take the leftovers of
     the rows below it, merged up level by level. Typed (non-perfect) rows are counted one by one. Asking for less
     in that sense is never worse, which keeps the frontiers small; the plan builder turns any perfect item asked
     for beyond its row into a merge of lower ones. */
  /* The inventory map: the grid of what a plan can ask for (0..cap per owned row). up(bits, u) marks every point
     from which u can be had (more of any row, or a perfect item split into two of the perfect row below it: the
     reverse of a merge), stopping at points already marked (what they reach is marked already). */
  const MAP_MAX = 1 << 21;   // grid points (one bit each: up to 256 KB per map)
  function lattice(owned, perfect, order, cap) {
    const n = owned.length, radix = [];
    let K = 1;
    const most = boundless ? MAP_MAX * 4 : MAP_MAX;   // the long background search may use bigger maps
    for (let j = 0; j < n; j++) { radix.push(K); K *= cap[j] + 1; if (K > most) return null; }
    const below = owned.map(() => -1), mult = owned.map(() => 0);   // the perfect row a perfect row splits into
    for (let k = 1; k < order.length; k++) { const j = order[k], i = order[k - 1]; below[j] = i; mult[j] = Math.pow(2, owned[j].level - owned[i].level); }
    const idx = u => { let t = 0; for (let j = 0; j < n; j++) t += u[j] * radix[j]; return t; };
    const coord = (i, j) => Math.floor(i / radix[j]) % (cap[j] + 1);
    let stack = new Int32Array(1024);
    const cs = new Int32Array(n);   // the coordinates of the point being marked
    function up(bits, u) {   // marks every point from which u can be had; returns how many it marked
      let top = 0, marked = 0;
      stack[top++] = idx(u);
      while (top) {
        const i = stack[--top];
        if (bits[i >>> 5] & (1 << (i & 31))) continue;
        bits[i >>> 5] |= 1 << (i & 31);
        marked++;
        if (top + 2 * n >= stack.length) { const bigger = new Int32Array(stack.length * 2); bigger.set(stack); stack = bigger; }
        for (let j = 0, r = i; j < n; j++) { const m = cap[j] + 1, c = r % m; cs[j] = c; r = (r - c) / m; }
        for (let j = 0; j < n; j++) {
          const cj = cs[j];
          if (cj < cap[j]) { const w = i + radix[j]; if (!(bits[w >>> 5] & (1 << (w & 31)))) stack[top++] = w; }
          const b = below[j];
          if (b >= 0 && cj > 0 && cs[b] + mult[j] <= cap[b]) { const w = i - radix[j] + mult[j] * radix[b]; if (!(bits[w >>> 5] & (1 << (w & 31)))) stack[top++] = w; }
        }
      }
      return marked;
    }
    const has = (bits, i) => (bits[i >>> 5] & (1 << (i & 31))) !== 0;
    return { K: K, idx: idx, up: up, has: has, words: (K + 31) >>> 5 };
  }

  function inventory(owned, chain) {
    const perfect = owned.map(o => !!chain[o.level] && o.stats.every((v, i) => v === chain[o.level][i]));
    const order = owned.map((o, j) => j).filter(j => perfect[j]).sort((a, b) => owned[a].level - owned[b].level);
    // covers(X, Y): Y can be had from X by merging perfect items upwards and leaving some unused
    function covers(X, Y) {
      for (let j = 0; j < X.length; j++) if (!perfect[j] && X[j] < Y[j]) return false;
      let carry = 0, lv = 0;
      for (let k = 0; k < order.length; k++) {
        const j = order[k], L = owned[j].level;
        if (lv) for (let l = lv; l < L && carry; l++) carry = Math.floor(carry / 2);
        const have = X[j] + carry;
        if (have < Y[j]) return false;
        carry = have - Y[j]; lv = L;
      }
      return true;
    }
    const q = owned.map(o => o.qty);
    const cap = q.slice();   // the most a plan can ask for of each row
    { let carry = 0, lv = 0;
      for (const j of order) { const L = owned[j].level; if (lv) for (let l = lv; l < L && carry; l++) carry = Math.floor(carry / 2); cap[j] = q[j] + carry; carry = cap[j]; lv = L; } }
    const w = owned.map(o => Math.pow(2, o.level - 1));
    return {
      perfect: perfect, order: order, cap: cap, map: lattice(owned, perfect, order, cap),
      fits: u => covers(q, u),
      leq: (a, b) => covers(b, a),   // a asks for no more than b
      // tie order for the frontier: less demand first, and at equal weight the higher-level demand first (it is
      // the one that dominates: one P3 leaves more room than two P2)
      weight: u => { let t = 0, h = 0; for (let j = 0; j < u.length; j++) { t += u[j] * w[j]; h += u[j] * w[j] * owned[j].level; } return t - h / 1e6; },
    };
  }

  /* Frontier DP. owned = [{level, stats, qty}], qty already capped by the caller.
     need: the level that was asked for. Above it the frontier only feeds the ladder, so when it grows too big there
     the DP stops (those ladder rungs stay unknown) instead of failing the whole plan.
     targets: when the asked level is the top of the DP, the targets to find there (the plan's target, and the
     perfect item for the ladder). Then two exact shortcuts apply:
       - the last level is a lookup: bases in cost order, each with its cheapest fitting material, stopping as soon
         as nothing cheaper is possible (no need for the whole frontier there);
       - separable models: an item is dropped unless it can still be part of some plan that meets the weakest
         target, as the base line (its stats plus the strongest gains still to come) or as a material (the gain it
         adds, on the strongest base it could go on). Both bounds are optimistic, so every item of every plan that
         meets a target survives: the plan, and every perfect ladder rung below, stay exact. */
  function solveCore(base, rates, maxLevel, owned, ctx, need, targets, free, cap) {
    const n = base.length;
    const hasU = owned.length > 0 && !free;   // free: owned items unlimited (at 0 or at the given prices), no counts kept
    if (cap == null) cap = Infinity;          // cap: only plans cheaper than this are wanted (branch and bound)
    work = 0; workLimit = subBudget || (owned.length && !boundless ? WORK_BUDGET : Infinity);   // any search with owned items is bounded
    let tick = 0;
    const zeroU = hasU ? owned.map(() => 0) : null;

    // numeric dedupe keys: stats in mixed radix R, usage in mixed radix (q+1); anything outside that range (an
    // owned item typed above the perfect one lifts what it builds) or a range too big for exact numbers uses text
    let R = 2;
    const chain = perfectChain(base, rates, maxLevel, ctx);
    for (let L = 1; L <= maxLevel; L++) for (const v of chain[L]) R = Math.max(R, v + 2);
    for (const o of owned) for (const v of o.stats) R = Math.max(R, v + 2);
    if (ctx && ctx.overrides) for (const v of ctx.overrides.values()) for (const x of v) R = Math.max(R, x + 2);
    const inv = inventory(owned, chain);
    const q = inv.cap;   // per row: the most a plan can ask for; inv.fits(u) says whether a demand can be met
    let K = 1;
    for (const c of q) K *= (c + 1);
    const textKeys = Math.pow(R, n) * K >= 9e15;

    const front = list => pareto(list, hasU, inv);

    const F = [];
    for (let L = 0; L <= maxLevel; L++) F.push([]);
    F[1].push(mkState(1, 1, base.slice(), zeroU, 0, null, null, -1));
    owned.forEach((o, j) => {
      if (o.level < 2 || o.level > maxLevel || o.qty <= 0) return;
      const u = hasU ? zeroU.slice() : null; if (u) u[j] = 1;
      F[o.level].push(mkState(o.level, Array.isArray(free) ? free[j] : 0, o.stats.slice(), u, 1, null, null, j));   // free: prices, or 0
    });

    // Separable models: a material only matters through the gains it adds, so the material list is kept as its
    // Pareto frontier over (cost, usage, gains): far fewer candidates, the same optimum.
    const sep = !!(ctx && ctx.sep);
    const zero = base.map(() => 0);
    const gainOf = v => ctx.model(zero, v, rates);
    const ovMat = sep && ctx.ovMat && ctx.ovMat.size ? ctx.ovMat : null;
    const gainList = ms => {
      if (!sep) return ms;
      const g = ms.map(y => { const v = gainOf(y.s); return { p: y.p, s: v, u: y.u, t: sum(v), y: y, ov: !!ovMat && ovMat.has(y.L + '|' + y.s.join(',')) }; });
      if (!ovMat) return front(g);
      const out = front(g.filter(x => !x.ov)).concat(g.filter(x => x.ov));
      return out.sort((a, b) => a.p - b.p);   // the searches walk materials cheapest first
    };
    let mats = front(F[1].slice()), matsG = gainList(mats);
    const sizes = [0, F[1].length];

    const lookup = !!(targets && targets.length && need === maxLevel);
    // the gains the floors are worked out with: the model's own (separable), or the exact formula's as a bound (Safe)
    const gainUB = sep ? gainOf : (ctx && ctx.ubExact ? v => MODELS.exact.fn(zero, v, rates) : null);
    // usefulness floors T[L] (see above); an item below T[L] in any stat cannot be in a plan that meets a target
    let T = null, Mb = null, Gb = null;   // Mb[l]: strongest possible level-l base; Gb[l]: strongest gain from a material up to level l
    if (lookup && gainUB) {
      const ginv = (i, v) => {   // the smallest stat whose gain reaches v (per stat: separable models are per stat)
        const one = x => { const vec = zero.slice(); vec[i] = x; return gainUB(vec)[i]; };
        if (!(v > one(0))) return -Infinity;
        let lo = 0, hi = 1;
        while (one(hi) < v) { hi *= 2; if (hi > 1e9) return Infinity; }
        while (hi - lo > 1) { const mid = Math.floor((lo + hi) / 2); if (one(mid) >= v) hi = mid; else lo = mid; }
        return hi;
      };
      // M[l]: no item at level l beats it in any stat; Mup[l]: the same over every level up to l (any material there)
      const M = [null, base.slice()], Mup = [null, base.slice()];
      for (let l = 2; l < need; l++) {
        const g = gainUB(Mup[l - 1]);
        M[l] = M[l - 1].map((v, i) => v + g[i]);
        for (const o of owned) if (o.level === l) for (let i = 0; i < n; i++) M[l][i] = Math.max(M[l][i], o.stats[i]);
        Mup[l] = Mup[l - 1].map((v, i) => Math.max(v, M[l][i]));
      }
      Mb = M; Gb = [];
      for (let l = 1; l < need; l++) Gb[l] = gainUB(Mup[l]);
      T = [];
      T[need] = base.map((v, i) => { let t = Infinity; for (const tg of targets) t = Math.min(t, tg[i] == null ? -Infinity : tg[i]); return t; });
      for (let L = need - 1; L >= 1; L--) {
        const gmax = gainUB(Mup[L]);
        T[L] = base.map((v, i) => {
          const asBase = T[L + 1][i] - gmax[i];
          let asMat = Infinity;
          for (let b = L; b < need; b++) asMat = Math.min(asMat, ginv(i, T[b + 1][i] - M[b][i]));
          return Math.min(asBase, asMat);
        });
      }
    }

    let top = maxLevel;
    for (let L = 2; L <= maxLevel; L++) {
      const bases = F[L - 1];
      if (lookup && L === need) {   // the last level: the cheapest item for each target, looked up
        // separable models: materials grouped by the gains they add (cheapest first in each group); a base only
        // looks at the groups whose gains take it to the target, and bases with the same stats share that list
        let groups = null;
        if (sep) {
          const gm = new Map();
          for (const g of matsG) {
            const k = g.ov ? 'ov' + gm.size : g.s.join(',');   // a material with a recorded result: its own group, always tried
            let e = gm.get(k); if (!e) { e = { g: g.ov ? g.s.map(() => Infinity) : g.s, list: [] }; gm.set(k, e); } e.list.push(g);
          }
          groups = Array.from(gm.values());
        }
        const tu = hasU ? new Array(q.length) : null, useMaskL = hasU && q.length <= 30;
        const rowMask = y => { if (y.um < 0) { let m = 0; for (let j = 0; j < q.length && j < 30; j++) if (y.u[j] > 0) m |= 1 << j; y.um = m; } return y.um; };
        const fullOf = x => { let m = 0; for (let j = 0; j < q.length && j < 30; j++) if (x.u[j] >= q[j]) m |= 1 << j; return m; };
        const tryPair = (x, g, y, target, bestP) => {   // the merged state if the pair fits the inventory and the target, else null
          let u = null;
          if (hasU) {
            for (let j = 0; j < q.length; j++) { const v = x.u[j] + y.u[j]; if (v > q[j]) return null; tu[j] = v; }
            if (!inv.fits(tu)) return null;
            u = tu.slice();
          }
          let s;
          if (sep && !g.ov) { s = new Array(n); for (let i = 0; i < n; i++) s[i] = x.s[i] + g.s[i]; } else s = combine(x.s, y.s, rates, ctx, x.L, y.L);
          if (!meets(s, target)) return null;
          return mkState(L, x.p + y.p, s, u, 2, x, y, -1);
        };
        for (const target of targets) {
          let bestP = cap, win = null;
          for (const o of F[L]) if (o.p < bestP && meets(o.s, target)) { bestP = o.p; win = o; }   // an owned item already there
          const fitting = new Map();   // base stats -> the material groups that take it to the target
          for (let xi = 0; xi < bases.length; xi++) {
            const x = bases[xi];
            if (x.p >= bestP) break;                       // bases are sorted by cost
            const full = useMaskL ? fullOf(x) : 0;         // rows this base has used up: materials needing them are skipped
            if (groups) {
              const k = x.s.join(',');
              let gs = fitting.get(k);
              if (!gs) {
                gs = groups.filter(e => { for (let i = 0; i < n; i++) { const t = target[i]; if (t != null && x.s[i] + e.g[i] < t) return false; } return true; });
                fitting.set(k, gs);
              }
              for (const e of gs) {
                const list = e.list;
                for (let yi = 0; yi < list.length; yi++) {
                  const g = list[yi];
                  if (x.p + g.p >= bestP) break;          // each group is sorted by cost
                  if ((++tick & 8191) === 0) spend(8192);
                  if (full && (rowMask(g.y) & full)) continue;
                  const w = tryPair(x, g, g.y, target, bestP);
                  if (w) { bestP = w.p; win = w; break; }
                }
              }
            } else {
              for (let yi = 0; yi < matsG.length; yi++) {
                const y = matsG[yi];
                if (x.p + y.p >= bestP) break;             // materials are sorted by cost
                if ((++tick & 8191) === 0) spend(8192);
                if (full && (rowMask(y) & full)) continue;
                const w = tryPair(x, null, y, target, bestP);
                if (w) { bestP = w.p; win = w; break; }  // the cheapest material that fits this base
              }
            }
          }
          if (win && F[L].indexOf(win) < 0) F[L].push(win);
        }
        sizes.push(F[L].length);
        top = L;
        break;
      }
      const pairs = bases.length * matsG.length;
      if (!boundless && (pairs > CANDIDATE_BUDGET || (hasU && work + pairs > workLimit * 2))) {
        if (need && L > need) { top = L - 1; break; }
        throw new BudgetExceeded('too many candidates');
      }
      const floor = T ? T[L] : null;
      // with floors: a base must be able to reach T[L] with the strongest material, a material must lift the
      // strongest possible base to T[L]; pairs outside that cannot pass the floor anyway
      let xs = bases, ys = matsG;
      if (floor) {
        xs = bases.filter(x => { for (let i = 0; i < n; i++) if (x.s[i] + Gb[L - 1][i] < floor[i]) return false; return true; });
        ys = matsG.filter(g => { const gs = sep ? g.s : gainUB(g.s); for (let i = 0; i < n; i++) if (Mb[L - 1][i] + gs[i] < floor[i]) return false; return true; });
      }
      const best = new Map();
      // scratch buffers: a pair's stats and inventory use are worked out in place, and copied only when kept
      const ss = new Array(n), su = hasU ? new Array(q.length) : null;
      const NY = ys.length, Q = hasU ? q.length : 0, useMask = hasU && Q <= 30;
      const yP = new Float64Array(NY), yS = new Float64Array(NY * n), yU = hasU ? new Int32Array(NY * Q) : null, yM = new Int32Array(NY), yF = new Uint8Array(NY), yO = new Array(NY);
      for (let k = 0; k < NY; k++) {
        const g = sep ? ys[k] : null, y = sep ? g.y : ys[k], sv = sep && !g.ov ? g.s : y.s;
        yO[k] = y; yP[k] = y.p; yF[k] = sep && !g.ov ? 1 : 0;   // 1: stats add the gain; 0: worked out by combine()
        for (let i = 0; i < n; i++) yS[k * n + i] = sv[i];
        if (hasU) { let m = 0; for (let j = 0; j < Q; j++) { yU[k * Q + j] = y.u[j]; if (y.u[j] > 0 && j < 30) m |= 1 << j; } yM[k] = m; }
      }
      // materials bucketed by the owned rows they use (each bucket cheapest first): a base skips whole buckets
      const buckets = [];
      if (useMask) {
        const bm = new Map();
        for (let k = 0; k < NY; k++) { let b = bm.get(yM[k]); if (!b) { b = { m: yM[k], ids: [] }; bm.set(yM[k], b); buckets.push(b); } b.ids.push(k); }
      } else buckets.push({ m: 0, ids: Array.from({ length: NY }, (v, k) => k) });
      for (let xi = 0; xi < xs.length; xi++) {
        const x = xs[xi], xp = x.p, xsv = x.s, xu = x.u;
        if (xp >= cap) break;                    // bases are sorted by cost
        let full = 0;                            // the owned rows this base has used up
        if (useMask) for (let j = 0; j < Q; j++) if (xu[j] >= q[j]) full |= 1 << j;
        for (let bi = 0; bi < buckets.length; bi++) {
          if (buckets[bi].m & full) continue;    // they need a row this base has used up
          const ids = buckets[bi].ids;
          for (let t = 0; t < ids.length; t++) {
          const yi = ids[t];
          const p = xp + yP[yi];
          if (p >= cap) break;                   // each bucket is sorted by cost
          if ((++tick & 8191) === 0) spend(8192);
          let s = ss;
          if (yF[yi]) { const o = yi * n; for (let i = 0; i < n; i++) ss[i] = xsv[i] + yS[o + i]; } else s = combine(xsv, yO[yi].s, rates, ctx, x.L, yO[yi].L);
          if (floor) { let ok = true; for (let i = 0; i < n; i++) if (s[i] < floor[i]) { ok = false; break; } if (!ok) continue; }
          let uKey = 0;
          if (hasU) {
            let ok = true, radix = 1;
            const o = yi * Q;
            for (let j = 0; j < Q; j++) {
              const v = xu[j] + yU[o + j];
              if (v > q[j]) { ok = false; break; }
              su[j] = v; uKey += v * radix; radix *= (q[j] + 1);
            }
            if (!ok || !inv.fits(su)) continue;
          }
          let key = 0, text = textKeys;
          for (let i = n - 1; i >= 0; i--) { if (s[i] >= R) text = true; key = key * R + s[i]; }
          key = text ? s.join(',') + '|' + uKey : key * K + uKey;
          const prev = best.get(key);
          if (prev === undefined || prev.p > p) best.set(key, mkState(L, p, s.slice(), su ? su.slice() : null, 2, x, yO[yi], -1));
          }
        }
      }
      const list = F[L].concat(Array.from(best.values()));
      F[L] = front(list);
      sizes.push(F[L].length);
      if (L < maxLevel) { mats = front(mats.concat(F[L])); matsG = gainList(mats); }
    }
    return { F: F, sizes: sizes, chain: chain, top: top };
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

  // Turn owned demand into a physical plan: perfect owned leaves beyond their row's count are made by merging
  // leftover perfect items from the rows below (lowest first), exactly as inventory().fits allowed.
  function realize(root, owned, chain, rates, ctx) {
    const inv = inventory(owned, chain);
    if (inv.order.length < 2) return;
    const leaves = new Map();
    (function walk(nd) { if (nd.k === 1 && inv.perfect[nd.j]) { if (!leaves.has(nd.j)) leaves.set(nd.j, []); leaves.get(nd.j).push(nd); } if (nd.k === 2) { walk(nd.b); walk(nd.m); } })(root);
    let spare = [], lv = 0;   // spare: items at level lv not asked for (owned leaves or merged sub-plans)
    for (const j of inv.order) {
      const L = owned[j].level;
      for (let l = lv; lv && l < L; l++) {   // merge spares up to this level, two by two
        const up = [];
        for (let i = 0; i + 1 < spare.length; i += 2) {
          const b = spare[i], m = spare[i + 1];
          b.baseLevel = l; m.baseLevel = l;   // both sides of a merge sit on a level-l base
          up.push({ L: l + 1, p: 0, s: combine(b.s, m.s, rates, ctx, l, l), k: 2, j: -1, b: b, m: m, dead: false });
        }
        spare = up;
      }
      const want = leaves.get(j) || [];
      const own = [];
      for (let i = 0; i < owned[j].qty; i++) own.push({ L: L, p: 0, s: owned[j].stats.slice(), k: 1, j: j, b: null, m: null, dead: false });
      const pool = own.concat(spare);
      want.forEach((nd, i) => { const src = pool[i]; if (src && src.k === 2) { nd.k = 2; nd.j = -1; nd.b = src.b; nd.m = src.m; nd.s = src.s; } });
      spare = pool.slice(want.length);
      lv = L;
    }
  }

  // Greedily replace the most expensive sub-trees with leftover owned items that dominate them.
  function substitute(root, owned, leftover, rates, ctx, goal) {
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
          if (nd.dead || nd.noSub || nd.k !== 2 || nd.p <= 0) continue;
          if (!geq(o.stats, nd.s)) continue;
          if (nd.role === 'mat' ? o.level > nd.baseLevel : o.level !== nd.L) continue;
          target = nd; break;
        }
        if (!target) break;
        // a stronger item gives at least as much, except where a recorded result says otherwise: the swap is kept only
        // if the plan still gets there with every result worked out again
        const was = { k: target.k, j: target.j, p: target.p, b: target.b, m: target.m, s: target.s };
        target.k = 1; target.j = j; target.p = 0; target.b = null; target.m = null; target.s = o.stats.slice();
        const keep = new Map();
        (function fix(nd) { if (nd.k === 2) { fix(nd.b); fix(nd.m); keep.set(nd, nd.s); nd.s = combine(nd.b.s, nd.m.s, rates, ctx, nd.b.L, nd.m.L); } })(root);
        if (goal && !meets(root.s, goal)) {
          for (const [nd, v] of keep) nd.s = v;
          Object.assign(target, was);
          target.noSub = true;   // not this one again
          continue;
        }
        (function kill(nd) { nd.dead = true; if (nd.k === 2) { kill(nd.b); kill(nd.m); } })(was.b ? { k: 2, b: was.b, m: was.m } : { k: 0 });
        saved += was.p;
        target.dead = false;
        leftover[j]--;
      }
    }
    (function fix(nd) { if (nd.k === 2) { fix(nd.b); fix(nd.m); nd.p = nd.b.p + nd.m.p; nd.s = combine(nd.b.s, nd.m.s, rates, ctx, nd.b.L, nd.m.L); } })(root);
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
  // req.exhaustive: no work limits, so the plan is always the best one (a big inventory can take a while: the app
  // runs it in a worker of its own, after showing the quick plan)
  function solve(req) {
    boundless = !!req.exhaustive;
    try { return solveOnce(req); } finally { boundless = false; }
  }
  function solveOnce(req) {
    const t0 = now();
    const base = req.base.map(Number);
    const rates = (req.rates || req.mults).map(normRate);
    const level = Math.min(MAX_LEVEL, Math.max(2, req.level | 0));
    const topLevel = Math.min(MAX_LEVEL, Math.max(level, (req.maxLevel | 0) || MAX_LEVEL));   // the item's own max: no work above it
    // owned rows that are the same item (level and stats) are one row with the counts added: a smaller lattice
    const rows = (req.owned || []).map((o, i) => ({ o: o, i: i })).filter(r => r.o && r.o.qty > 0 && r.o.level >= 2 && r.o.level <= MAX_LEVEL);
    const owned = [], rowOf = new Map(), members = [];
    for (const r of rows) {
      const k = (r.o.level | 0) + ':' + r.o.stats.map(Number).join(',');
      let j = rowOf.get(k);
      if (j == null) { j = owned.length; rowOf.set(k, j); owned.push({ level: r.o.level | 0, stats: r.o.stats.map(Number), qty: 0 }); members.push([]); }
      owned[j].qty += r.o.qty | 0; members[j].push(r.i);
    }
    const target = (req.target || base.map(() => null)).map(t => (t == null ? null : Number(t)));
    const ctx = makeCtx(req.model || 'exact', req.overrides || [], base.length);
    sepCheck(ctx, rates);
    const qK = ctx.sep ? QUICK_K_SEP : QUICK_K;

    // Cap quantities so the usage lattice (the product of qty + 1) stays within kMax, handing counts out one at a
    // time with higher-level items first; the leftovers are substituted into the plan afterwards.
    const prio = owned.map((o, j) => j).sort((a, b) => (owned[b].level - owned[a].level) || (sum(owned[b].stats) - sum(owned[a].stats)));
    function capsFor(kMax, topFirst) {
      const caps = owned.map(() => 0);
      let k = 1, grew = true;
      if (topFirst) {   // the highest rows as full as the lattice allows, one after the other
        for (const j of prio) { const room = Math.floor(kMax / k) - 1; caps[j] = Math.max(0, Math.min(owned[j].qty, room)); k *= caps[j] + 1; }
        return { caps: caps, k: k };
      }
      while (grew) {
        grew = false;
        for (const j of prio) {
          if (caps[j] >= owned[j].qty) continue;
          const k2 = k / (caps[j] + 1) * (caps[j] + 2);
          if (k2 > kMax) continue;
          caps[j]++; k = k2; grew = true;
        }
      }
      return { caps: caps, k: k };
    }

    const chainTop = perfectChain(base, rates, topLevel, ctx);
    const lvTargets = [target, chainTop[level]];
    let res = null, pick = null, K = 1, capped = owned, lad = null, status = 'exact', built = null;
    for (const o of owned) K *= (o.qty + 1);
    // expand a plan into physical items: merges and swaps of owned items, their rows' counts respected
    function build(pk, rows) {
      const tree = expand(pk, pk.L);
      realize(tree, rows, chainTop, rates, ctx);
      let sub = 0;
      if (rows !== owned) {
        const used = usageOf(serializeTree(tree), owned.length);
        sub = substitute(tree, owned, owned.map((o, j) => o.qty - used[j]), rates, ctx, target);
      }
      return { tree: tree, sub: sub, cost: tree.p };
    }
    // a quick plan from part of the inventory (handed out evenly, higher levels first), the rest swapped in afterwards
    function quick(kMax, topFirst) {
      for (;;) {
        const c = capsFor(kMax, topFirst);
        const rows = owned.map((o, j) => ({ level: o.level, stats: o.stats, qty: c.caps[j] }));
        try {
          const r = solveCore(base, rates, level, rows, ctx, level, lvTargets), pk = choose(r.F[level], target);
          return { res: r, pick: pk, rows: rows, built: pk ? build(pk, rows) : null };
        } catch (err) {
          if (!(err instanceof BudgetExceeded)) throw err;
          if (c.k <= 1) {
            const r = solveCore(base, rates, level, [], ctx, level, lvTargets), pk = choose(r.F[level], target), rows = owned.map(o => ({ level: o.level, stats: o.stats, qty: 0 }));
            return { res: r, pick: pk, rows: rows, built: pk ? build(pk, rows) : null };
          }
          kMax = Math.max(1, Math.floor(c.k / 4));
        }
      }
    }
    // a quick plan from given counts per row (null when the search is too big for them)
    function quickCaps(caps) {
      const rows = owned.map((o, j) => ({ level: o.level, stats: o.stats, qty: caps[j] }));
      try {
        const r = solveCore(base, rates, level, rows, ctx, level, lvTargets), pk = choose(r.F[level], target);
        return { res: r, pick: pk, rows: rows, built: pk ? build(pk, rows) : null };
      } catch (err) { if (!(err instanceof BudgetExceeded)) throw err; return null; }
    }
    // Warm start (req.hint: the plan you were following, its done refines turned into owned items): replayed with the
    // recorded results; if it still gets there it is a plan as it is, else the cheapest single change that makes it
    // get there (a sub-plan made again to the stats its place needs: the one that fell short, or the item it is
    // combined with, made stronger), repeated while needed. Its cost bounds the exact search.
    function warmStart(hint) {
      if (!hint || !Array.isArray(hint.nodes) || hint.root == null) return null;
      const H = hint.nodes;
      const mk = id => {
        const h = H[id]; if (!h) throw new Error('hint');
        if (h.k === 0) return { L: 1, p: 1, s: base.slice(), k: 0, j: -1, b: null, m: null, dead: false };
        if (h.k === 1) { const j = rowOf.get((h.L | 0) + ':' + h.s.map(Number).join(',')); if (j == null) throw new Error('hint'); return { L: h.L, p: 0, s: owned[j].stats.slice(), k: 1, j: j, b: null, m: null, dead: false }; }
        return { L: h.L, p: 0, s: null, k: 2, j: -1, b: mk(h.b), m: mk(h.m), dead: false, want: h.s.map(Number) };   // want: its stats in that plan
      };
      let root;
      try { root = mk(hint.root); } catch (e) { return null; }
      if (root.L !== level) return null;
      const nOw = owned.length;
      const fix = nd => {   // stats, cost and owned use, worked out again from the leaves
        if (nd.k === 0) { nd.u = new Array(nOw).fill(0); return; }
        if (nd.k === 1) { nd.u = new Array(nOw).fill(0); nd.u[nd.j] = 1; return; }
        fix(nd.b); fix(nd.m);
        nd.s = combine(nd.b.s, nd.m.s, rates, ctx, nd.b.L, nd.m.L); nd.p = nd.b.p + nd.m.p; nd.u = nd.b.u.map((v, j) => v + nd.m.u[j]);
      };
      const fitsQty = u => u.every((v, j) => v <= owned[j].qty);
      const ok = () => meets(root.s, target) && fitsQty(root.u);
      fix(root);
      if (ok()) return { tree: root, sub: 0, cost: root.p };
      if (!ctx.sep) return null;   // the repair works out what each place needs from separable gains
      const tEnd = now() + (boundless ? 3000 : 400);   // a first answer must come fast: the repair stops in time
      const zero = base.map(() => 0), gain = v => ctx.model(zero, v, rates);
      const ginv = (i, v) => {   // the smallest stat whose gain reaches v
        const one = x => { const vec = zero.slice(); vec[i] = x; return gain(vec)[i]; };
        if (!(v > one(0))) return 0;
        let lo = 0, hi = 1;
        while (one(hi) < v) { hi *= 2; if (hi > 1e9) return Infinity; }
        while (hi - lo > 1) { const mid = Math.floor((lo + hi) / 2); if (one(mid) >= v) hi = mid; else lo = mid; }
        return hi;
      };
      const keyOf = nd => nd.key || (nd.key = nd.k === 2 ? '2:' + nd.L + ':' + keyOf(nd.b) + '|' + keyOf(nd.m) : nd.k + ':' + nd.L + ':' + nd.j);
      for (let round = 0; round < 6; round++) {
        // what every place needs so that the top gets there (the rest as it is)
        const places = [];
        (function need(nd, r, parent, side) {
          nd.req = r; places.push({ nd: nd, parent: parent, side: side });
          if (nd.k !== 2) return;
          const gm = gain(nd.m.s);
          need(nd.b, r.map((v, i) => v == null ? null : v - gm[i]), nd, 'b');
          need(nd.m, r.map((v, i) => v == null ? null : ginv(i, v - nd.b.s[i])), nd, 'm');
        })(root, target.slice(), null, null);
        const short = places.filter(x => !meets(x.nd.s, x.nd.req));
        // first: a refine that no longer gives what the plan counted on (its inputs still do) made again to those stats
        const causes = new Map();
        for (const x of places) {
          const nd = x.nd;
          if (nd.k !== 2 || !nd.want || meets(nd.s, nd.want)) continue;
          const kidOk = c => c.k !== 2 || !c.want || meets(c.s, c.want);
          if (!kidOk(nd.b) || !kidOk(nd.m)) continue;
          const k = keyOf(nd);
          let c = causes.get(k); if (!c) { c = { L: nd.L, req: nd.want.slice(), at: [] }; causes.set(k, c); }
          c.at.push({ nd: nd, parent: x.parent });
        }
        // then: a bigger sub-plan around it made again to what the plan counted on (its items free for a new layout)
        const parentOf = new Map();
        for (const x of places) if (x.parent) parentOf.set(x.nd, x.parent);
        for (const c of Array.from(causes.values())) for (const a of c.at) {
          let A = a.parent;
          while (A && A !== root) {
            const P = parentOf.get(A);
            const k = 'up:' + keyOf(A);
            let e = causes.get(k); if (!e) { e = { L: A.L, req: A.want.slice(), at: [] }; causes.set(k, e); }
            if (!e.at.some(z => z.nd === A)) e.at.push({ nd: A, parent: P });
            A = P;
          }
        }
        // candidates: a place that falls short made again, or the item it is combined with made stronger; the same
        // sub-plan in several places is changed in all of them at once, to the most any of them needs
        const cands = new Map();
        const add = (nd, r, parent) => {
          const k = keyOf(nd) + '@' + (parent ? keyOf(parent) : 'root');
          let c = cands.get(k);
          if (!c) { c = { L: nd.L, req: r.slice(), at: [] }; cands.set(k, c); }
          else c.req = c.req.map((v, i) => v == null ? r[i] : r[i] == null ? v : Math.max(v, r[i]));
          c.at.push({ nd: nd, parent: parent });
        };
        for (const x of short) {
          add(x.nd, x.nd.req, x.parent);
          if (x.parent) {
            const A = x.parent, rA = A.req;
            if (x.side === 'b') add(A.m, rA.map((v, i) => v == null ? null : ginv(i, v - x.nd.s[i])), A);
            else { const g = gain(x.nd.s); add(A.b, rA.map((v, i) => v == null ? null : v - g[i]), A); }
          }
        }
        let best = null;
        for (const c of Array.from(causes.values()).concat(Array.from(cands.values()))) {   // the likeliest changes first
          if (now() > tEnd) break;
          const mult = c.at.length;
          const u = root.u.slice();
          for (const a of c.at) for (let j = 0; j < nOw; j++) u[j] -= a.nd.u[j];
          const sub = owned.map((o, j) => ({ level: o.level, stats: o.stats, qty: Math.max(0, Math.floor((o.qty - u[j]) / mult)) }));
          let r = null, pk = null;
          const keepW = work, keepL = workLimit;
          subBudget = WORK_BUDGET / 4;
          try { r = solveCore(base, rates, c.L, sub, ctx, c.L, [c.req, c.req]); pk = choose(r.F[c.L], c.req); }
          catch (err) { if (!(err instanceof BudgetExceeded)) throw err; }
          finally { subBudget = 0; work = keepW; workLimit = keepL; }
          if (!pk) continue;
          const cost = root.p + mult * pk.p - c.at.reduce((t, a) => t + a.nd.p, 0);
          if (!best || cost < best.cost) best = { c: c, pk: pk, sub: sub, cost: cost };
        }
        if (!best || now() > tEnd && !best) return null;
        for (const a of best.c.at) {   // each place gets a sub-plan of its own (merges made real from the rows it may use)
          const t = expand(best.pk, best.pk.L);
          realize(t, best.sub, chainTop, rates, ctx);
          if (!a.parent) root = t; else if (a.parent.b === a.nd) a.parent.b = t; else a.parent.m = t;
        }
        (function clear(nd) { nd.key = null; if (nd.k === 2) { clear(nd.b); clear(nd.m); } })(root);
        fix(root);
        if (ok()) return { tree: root, sub: 0, cost: root.p };
        if (now() > tEnd) return null;
      }
      return null;
    }
    const use = qk => { res = qk.res; pick = qk.pick; capped = qk.rows; built = qk.built; };
    // A big inventory: first a quick plan; its cost bounds the exact search (branch and bound), which then skips
    // everything that already costs as much, and starts its last-level lookup from it.
    // First the plan with unlimited copies of every owned row, at a tiny price each (so it asks for as few as it can).
    // Nothing can be cheaper, so when that plan fits the real inventory (merges allowed) it is the best one.
    let epsUse = null;
    if (owned.length && capsFor(qK).k < K) {
      try {
        const eps = owned.map(o => Math.pow(2, o.level - 1) * 1e-7);
        const r = solveCore(base, rates, level, owned, ctx, level, lvTargets, eps), pk = choose(r.F[level], target);
        if (pk) {
          const tree = expand(pk, pk.L), u = owned.map(() => 0);
          (function walk(nd) { if (nd.k === 1) u[nd.j]++; else if (nd.k === 2) { walk(nd.b); walk(nd.m); } })(tree);
          if (inventory(owned, chainTop).fits(u)) {
            realize(tree, owned, chainTop, rates, ctx);
            (function fix(nd) { if (nd.k === 2) { fix(nd.b); fix(nd.m); nd.p = nd.b.p + nd.m.p; } else if (nd.k === 1) nd.p = 0; })(tree);
            res = r; pick = pk; capped = owned; built = { tree: tree, sub: 0, cost: tree.p };
          } else epsUse = u;   // it asks for more than you have: its use still says which rows matter
        }
      } catch (err) { if (!(err instanceof BudgetExceeded)) throw err; }
    }
    let qk = null;
    if (!built && owned.length && capsFor(qK).k < K) {   // two quick plans: counts handed out evenly, or the highest rows first
      qk = quick(qK);
      const q2 = quick(qK, true);
      if (q2.built && (!qk.built || q2.built.cost < qk.built.cost)) qk = q2;
      if (epsUse) {   // a third: the rows the unlimited plan used, as many as it used (or you have)
        const q3 = quickCaps(owned.map((o, j) => Math.min(o.qty, epsUse[j])));
        if (q3 && q3.built && (!qk.built || q3.built.cost < qk.built.cost)) qk = q3;
      }
    }
    if (req.hint && owned.length) {   // the plan you were following, repaired: often the best one already
      const hk = warmStart(req.hint);
      if (hk && (!qk || !qk.built || hk.cost < qk.built.cost)) {
        const r0 = qk ? qk.res : solveCore(base, rates, level, [], ctx, level, lvTargets);   // for the ladder and sizes
        qk = { res: r0, pick: { L: level, p: hk.cost, s: hk.tree.s }, rows: owned, built: hk };
      }
    }
    const ub = qk && qk.built ? qk.built.cost : Infinity;
    if (built) { /* the unlimited plan fits: it is the best one */ }
    else if (qk && ub === 0) { use(qk); status = 'proven'; }   // nothing is cheaper than free
    // req.quick (the app's first answer): a big inventory gets its quick plan at once, marked approximate; the
    // app's background search (exhaustive) finds the best one
    else if (req.quick && !boundless && qk && qk.built && K > QUICK_SKIP) { use(qk); status = 'capped'; }
    else {
      try {
        const r = solveCore(base, rates, level, owned, ctx, level, lvTargets, false, ub), pk = choose(r.F[level], target);
        if (pk) { res = r; pick = pk; capped = owned; }
        else if (qk) use(qk);                 // nothing cheaper than the quick plan: it is the best one
        else { res = r; pick = null; }                     // no plan at all
      } catch (err) {
        if (!(err instanceof BudgetExceeded)) throw err;
        // Too big even so. Keep a quick plan (a bigger one if there was none yet) and try to prove it optimal.
        status = 'capped';
        if (!qk) qk = quick(K_START);
        use(qk);
        if (pick) {
          const cost = built.cost;
          if (cost === 0) status = 'proven';
          else {
            try {   // proven optimal if unlimited copies of every owned item could not do better
              const rel = solveCore(base, rates, level, owned, ctx, level, [target], true), lb = choose(rel.F[level], target);
              if (lb && lb.p >= cost) status = 'proven';
            } catch (e2) { if (!(e2 instanceof BudgetExceeded)) throw e2; }
            if (status !== 'proven' && cost < ub) {   // a new, better bound: the exact search once more with it
              try {
                const r2 = solveCore(base, rates, level, owned, ctx, level, lvTargets, false, cost), p2 = choose(r2.F[level], target);
                if (p2) { res = r2; pick = p2; capped = owned; built = null; status = 'exact'; } else status = 'exact';
              } catch (e3) { if (!(e3 instanceof BudgetExceeded)) throw e3; }
            }
          }
        }
      }
    }
    lad = res;
    if (topLevel > level) {   // the ladder above the plan's level: one more search up to the item's max
      try { lad = solveCore(base, rates, topLevel, owned, ctx, topLevel, [chainTop[topLevel]]); }
      catch (err) { if (!(err instanceof BudgetExceeded)) throw err; }
    }
    const chain = chainTop;

    let plan = null, substituted = 0;
    if (pick) {
      if (!built) built = build(pick, capped);
      substituted = built.sub;
      plan = serializeTree(built.tree);
      // owned items point back at the caller's rows; merged rows share their uses out in order (see analyze)
      for (const nd of plan.nodes) if (nd.k === 1) nd.j = members[nd.j][0];
      plan.split = members.filter(m => m.length > 1).map(m => m.map(i => [i, req.owned[i].qty | 0]));
    }

    const ladder = [];
    for (let L = 2; L <= MAX_LEVEL; L++) {
      // a rung the bounded search skipped (it costs at least the plan's bound) comes from the quick plan's search
      const s = (L <= lad.top ? choose(lad.F[L], chain[L]) : null) || (qk && L <= qk.res.top ? choose(qk.res.F[L], chain[L]) : null);
      ladder.push({ level: L, cost: s ? s.p : null, standard: Math.pow(2, L - 1) });
    }

    return {
      ok: !!pick,
      mode: status,
      approximate: status === 'capped',
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
    const rr = rates.map(normRate), top = perfectChain(base, rr, L, ctx)[L];
    const res = solveCore(base, rr, L, [], ctx, L, [top]);
    const s = choose(res.F[L], top);
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
    // identical owned rows were solved as one: hand the uses back out, filling each row up to its count
    for (const grp of plan.split || []) {
      let left = 0; for (const [i] of grp) { left += ownedUse[i] || 0; ownedUse[i] = 0; }
      for (const [i, q] of grp) { const t = Math.min(q, left); ownedUse[i] = t; left -= t; }
    }
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
