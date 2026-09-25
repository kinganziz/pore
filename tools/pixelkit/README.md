# pixelkit

Turns flat HD vector drawings (SVG) into shaded pixel art, and renders pixel grids back to crisp SVG.
It is the one method behind every PORE pixel icon: draw the icon in HD, run it through pixelkit, done.
No hand-drawn pixels are needed, and the same drawing can be rendered at any grid size.

## What it does

Every element of the drawing becomes its own pixel region, in paint order, so the pixel version keeps the
drawing's layout, orientation and colours. Then, per region:

- **Shading**: light on the top/left rim, shadow on the bottom/right rim, taken from the drawing's own
  gradient (or a lighter and darker tone of a flat colour).
- **Dithered shading**: a second, checkerboard step inside each rim, the classic 16-bit way.
- **Ambient occlusion**: a region lying under another darkens where that one sits on it, so parts look
  tucked together (a gem in its setting, a guard on a blade).
- **Outline**: the drawing's own dark strokes are dropped and one clean 1-pixel outline is drawn around the
  whole silhouette, in the neighbouring part's ink.
- **Small details** (gems, eyes, studs) always keep at least one pixel.

When rendering: colours get a saturation and contrast boost (near-greys such as steel and silver keep their
colour, so metals are not tinted), and a soft 1-pixel **cast shadow** is drawn down-right.

## Use

```js
import { pixelKit } from './pixelkit/pixelkit.mjs';

const kit = pixelKit({ size: 32 });              // every option has a default
const grid = kit.compile(svgText);               // size x size array of '#rrggbb' or null
const text = kit.toTxt('Iron Sword', grid);      // editable text grid, one character per pixel
const svg  = kit.toSvg(kit.fromTxt(text));       // crisp pixel SVG
```

## Options

| Option     | Default | What it does                                               |
|------------|---------|------------------------------------------------------------|
| `size`     | 32      | grid size in pixels                                        |
| `viewBox`  | 64      | the drawings' viewBox width                                |
| `samples`  | 4       | sub-samples per pixel side when measuring coverage         |
| `dither`   | true    | the dithered second shading step                           |
| `ao`       | true    | ambient occlusion                                          |
| `shadow`   | 0.32    | cast shadow opacity (0 turns it off)                       |
| `vivid`    | 1.8     | colour saturation boost                                    |
| `contrast` | 1.16    | lightness contrast                                         |
| `mark`     | …       | the "generated" line written into text grids               |

## Text grids

`toTxt` writes a palette (one letter per colour) and a grid of those letters. A grid that still carries the
`mark` line is regenerated on every run; delete that line and the grid is kept as hand-edited.

## In PORE

`tools/pixelart.mjs` runs pixelkit over `icons/modern/*.svg` with PORE's settings and writes
`icons/pixel-src/*.txt`, `icons/pixel/*.svg` and `icons/sprite-pixel.svg`.

Copyright (c) 2026 anz. All rights reserved (see the repository's LICENSE).
