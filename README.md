# PORE · Pixel Odyssey Refinement Engine

A mobile-first planner that finds the **cheapest refinement path** for any equippable item in
[Pixel Odyssey](https://wiki.pixel-odyssey.app/). A perfect P10 normally costs 512 base items
(1 → 2 → 4 → … → 512). PORE finds paths that reach the same stats with far fewer, and walks you
through the refines step by step.

Live app: the repository root is a static site — enable GitHub Pages on the `main` branch (root)
and open `index.html`.

## Features

- **Every item from the wiki**: weapons, helmets, chest, leg gear, shoes, shields, rings, amulets,
  necklaces, tools, each with its own PORE-drawn icon. Custom items (up to 3 stats) are supported too.
- **1, 2 and 3-stat items.** The solver keeps a Pareto frontier of (cost, stats) per level, so
  multi-stat items are solved exactly, not stat by stat.
- **Any target**: level P2–P10, perfect stats or "at least X", ignore a stat you do not care about.
- **Items you already have** (any level, any stats, any quantity) are used for free where they
  fit best; small inventories are solved exactly, large ones with a capped search plus greedy
  substitution (flagged "approximate").
- **Crafting guide** grouped by level with tick-off progress, gold fees, base success rate and the
  charm factor needed for a guaranteed refine. Bottom-up or top-down view.
- **Cost ladder** for every target level, shopping list, perfect-stat table, share links, copy as text.
- **Formula lab**: record the real in-game result of any refine (pencil on the step). PORE
  re-plans with your number, keeps the observation, and scores every candidate formula variant
  against all observations so the hidden rounding rule can be pinned down. A "Safe" mode plans
  only with results every plausible variant agrees on.

## The model

For every stat of the item:

```
result = floor( base + max(2, material × rate) )
```

The result is one level above the base item; the material can be any level up to the base level.
Rates by stat category (from the wiki's Refining page): combat 25 %, critical 16.7 % (1/6),
resource 12.5 %, gathering 6.25 %. Stats the wiki does not list are assigned a category by best
guess and can be changed in the app.

The game occasionally lands ±1 off this formula on high-stat or multi-stat items. The solver
ships several candidate variants (32/64-bit float evaluation of the legacy expression, wiki
percentages, an item-level penalty from the main stat, round/ceil, +1 minimum gain) and the
formula lab tells you which one matches your recorded observations.

## Repository layout

```
index.html          built single-file app (data + solver inlined) — this is what GitHub Pages serves
src/app.html        app template (UI, styles, worker glue)
src/solver.js       the solver (pure JS; runs in a Web Worker, on the page, or in Node)
data/items.json     equipment + charm database generated from the wiki (names, stats, factors; no artwork)
tools/fetch_wiki.py refreshes data/items.json from the wiki's Obsidian Publish cache
tools/modern_icons.py draws PORE's equipment icons -> icons/modern/ (charms there are hand-drawn)
tools/make_svg.py   bundles icons/modern/ into icons/sprite.svg
tools/pixel_icons.py draws the retro pixel-art set natively on a 16x16 grid -> icons/pixel/, icons/sprite-pixel.svg
tools/pixelate.mjs   redraws the modern icons as 24x24 pixel art ("Pixel HD") -> icons/pixel-modern/, icons/sprite-pixel-modern.svg
tools/build.py      injects data + solver into the template -> index.html
tools/test_solver.mjs  solver regression tests (reference values + brute-force cross-check)
```

## Working on it

```bash
python tools/fetch_wiki.py     # refresh item + charm data from the wiki (needs network)
python tools/modern_icons.py   # draw icons for new items (never overwrites hand-edited files)
python tools/make_svg.py       # bundle icons/modern/ into icons/sprite.svg
python tools/pixel_icons.py    # redraw the retro pixel-art icon set
npm install && node tools/pixelate.mjs   # redraw the Pixel HD set from icons/modern/
python tools/build.py          # rebuild index.html after editing src/
node tools/test_solver.mjs     # run the solver tests
```

All icons are PORE's own drawings, in three sets: modern vector icons, Pixel HD (the modern drawings as 24x24 pixel art) and a
hand-built 16x16 retro pixel-art set; no artwork from the
game or the wiki is used or stored.
Charms (with their success multipliers) are read from the wiki too and drive the automatic batch
splitting in the crafting guide.

Edit `src/app.html` / `src/solver.js`, rebuild, commit `index.html` together with the sources.

## Credits

Item names and stats belong to Pixel Odyssey and are taken from the official wiki. The icons are
PORE's own drawings. PORE is a fan-made tool.
