# PORE art guide: from a reference picture to a PORE icon

How every PORE picture is made: items, skins, NPC and world boss portraits, the tab bar and map pictures.
Follow it for any new picture so the whole app keeps one look.

## The rule

**Look at the reference, never copy it.** A reference picture (from the wiki or the game) is only a guide to
*what* the thing is: its silhouette, its main colours and the one or two features that make it recognisable.
Every PORE picture is drawn from scratch as a vector drawing with our own kits. No pixel, shape or file from a
reference is traced, sampled, shipped or kept in the repository. References live in a scratch folder while
drawing and are thrown away afterwards.

## The one method

```
reference (scratch only) -> describe it -> HD drawing (SVG, 64x64, from a kit) -> pixelkit -> 32x32 pixel icon
```

1. **HD drawing.** A Python kit writes `icons/modern/<key>.svg` (64x64 viewBox): flat shapes with a dark
   outline stroke and simple gradients for the parts that should look round.
2. **pixelkit** (`tools/pixelkit/`, run by `node tools/pixelart.mjs`) turns every drawing into pixel art at
   32x32: per-part shading light top-left and dark bottom-right, a dithered second step, ambient occlusion
   where parts overlap, one clean outline around the silhouette, strong colour and a soft cast shadow.
3. **Never edit pixels by hand.** If a pixel icon looks wrong, fix the drawing or the kit, or improve pixelkit
   for every icon (as with thin dark rings staying flat). The owner reviews converted icons and decides.

## The kits

| Kit | Draws | Keys |
|-----|-------|------|
| `tools/modern_icons.py` | gear (weapons, armour, rings…) | `i<id>` |
| `tools/goods_icons.py` | every other item (food, ores, potions…) | `i<id>`, `c<id>` |
| `tools/skin_game.py` (v2) | skins: big-head portraits | via goods_icons |
| `tools/npc_icons.py` | NPC portraits, using the skin kit | `n-<name>` |
| `tools/boss_icons.py` | world boss portraits: the monster kit | `b-<name>` |
| `tools/ui_icons.py` | tab bar, coins, map | `u-<name>` |
| `tools/library_icons.py` | Library: spell and talent rune tiles, obol coins, books | `l-<name>` |

Shared helpers (`modern_icons.py`): `shape` (a filled outlined path with a gradient), `circle`, `dot`, `line`,
`tube`; colour ramps (`skin_icons.ramp`: highlight, mid, shadow, outline from one colour).

## Step by step

1. **Collect references** into the scratchpad (for example with curl from the wiki's media files). Make an
   enlarged contact sheet (nearest-neighbour, x4 to x8) so every reference can be studied side by side.
2. **Describe each one in words before drawing**, in three parts:
   - *silhouette*: what fills the frame (a round head, a cube, a hooded figure, a worm in a curve);
   - *palette*: two or three main colours, one per part (skin, clothes, hair or shell, accents);
   - *signature*: the one or two features that make it *that* character (a straw hat, a single slit eye,
     a sword stuck in a slime, a spiral shell, red runes). Keep those; drop everything else.
   Write the description as a comment next to the entry (see `npc_icons.py`, `boss_icons.py`).
3. **Build it from kit parts.** Portraits are framed like the game's: the head or body **fills the 64x64
   frame**, with a sliver of outfit or body at the bottom and extras (weapon, wings, horns) at the sides.
   - People and animal NPCs: the skin kit's `portrait(style, hair, skin, outfit, extras, eye, weapon)`.
   - Monsters: the monster kit (`body`, `blob`, `eye`, `glow_eyes`, `grin`, `horns`, `wings`, `tentacles`,
     `flame`, `blade`, `stars`), layered back to front: wings and weapons, then body, then head, then face.
4. **Generate and convert**: run the kit, then `node tools/pixelart.mjs`.
5. **Compare** on a page with the reference and our pixel icon side by side, both enlarged. Check that each
   one is recognisable at app size (about 39 px): silhouette and signature first, colours second.
6. **Adjust the description, not the pixels.** Typical fixes: a figure that reads as a blob gets its face
   shown (Jack), a bean-shaped head gets a creature head with fangs (Gul), a colour too saturated is muted
   (Mudder).
7. **Wire it in**, rebuild (`python tools/build.py`) and commit the kit, the drawings and the pixel icons.

## Style rules

- **Few big parts.** 5 to 12 shapes. At 32x32 anything smaller than about 2 HD units disappears, except
  small details (eyes, gems, studs), which pixelkit always keeps at one pixel at least.
- **One colour per part**, from the reference's main colours; the ramp makes light, shade and outline.
  Use a gradient (`ic.lg`) on parts that should look round; flat fills for flat things.
- **Dark outline strokes** (width 1.2 to 2) on every shape. pixelkit replaces them with its own outline.
- **Faces carry the character**: eye style (big anime eyes, glowing slits, one huge eye) and mouth (a small
  line, a toothy grin, fangs) say more than any other detail.
- **Exaggerate the signature**: bigger hat, bigger eye, longer horns than in the reference.
- **Readable on dark and light backgrounds**: avoid near-black bodies without a lighter part next to them.
- **Our look, not the game's**: never match the reference pixel for pixel; the result should feel like it
  belongs with PORE's other icons.

## Naming and places

- HD drawings: `icons/modern/<key>.svg`; pixel sources: `icons/pixel-src/<key>.txt`; pixel icons:
  `icons/pixel/<key>.svg` and the sprite `icons/sprite-pixel.svg`.
- Keys: `i<id>` / `c<id>` items and charms, `n-<name>` NPCs, `m-<name>` monsters, `b-<name>` world bosses,
  `l-<name>` Library entries, `u-<name>` interface. `n-`, `m-`, `b-` and `l-` go to the second sheet,
  `icons/sprite-portraits.svg`.
- Old kits and reference-free backups live outside the repository in `D:\data\pore-resources`.

Copyright (c) 2026 anz. All rights reserved (see LICENSE).
