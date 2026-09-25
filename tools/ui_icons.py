#!/usr/bin/env python3
"""Draw PORE's interface icons (tab bar and coins) as HD drawings -> icons/modern/u-<name>.svg

Same kit and style as the item icons (tools/modern_icons.py), so tools/pixelart.mjs turns them into the
pixel versions like every other icon and the HD switch covers them too.

Usage: python tools/ui_icons.py
"""
from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from modern_icons import HL, Icon, C, P, circle, dot, f, line, shape  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"
INK = "#141216"
WALL = C("#fff4dc", "#e8d3a8", "#b0906a", "#3a2412")
ROOF = C("#ff9a8a", "#d9483b", "#8a2018", "#2c0a06")
WOOD = C("#e8b070", "#a8683a", "#6a3a18", "#2a1406")
PAPER = C("#fffaea", "#f2dfb0", "#c9a36a", "#3a2410")
LEATHER = C("#e0a070", "#a8683a", "#6a3a18", "#2a1406")
STEEL = C("#ffffff", "#c4ccd8", "#7c8aa0", "#1e2430")
GOLD = C("#fff2a6", "#f6c030", "#b8780c", "#3a1e06")
BRONZE = C("#ffd8a8", "#cf8f4f", "#8a5424", "#2e1606")


def home(ic):
    return "".join([
        shape(ic, "M14 30 L50 30 L50 56 L14 56 Z", WALL, ic.lg(WALL, 0, 0, 1, 1)),
        shape(ic, "M6 32 L32 8 L58 32 L50 32 L32 16 L14 32 Z", ROOF, ic.lg(ROOF, 0, 0, 1, 1)),
        shape(ic, "M14 32 L32 16 L50 32 Z", ROOF, ic.lg(ROOF, 0.3, 0, 0.7, 1)),
        shape(ic, "M20 40 L30 40 L30 56 L20 56 Z", WOOD), dot(27, 49, 1.4, "#ffd23a"),
        shape(ic, "M36 38 L46 38 L46 48 L36 48 Z", C("#e6f6ff", "#8fd0ff", "#3a88c8", "#10304a"), sw=1.8),
        line("M41 38 L41 48 M36 43 L46 43", "#10304a", 1.4),
        shape(ic, "M42 12 L48 12 L48 22 L42 18 Z", C("#c8a080", "#8a5a3a", "#5a3420", "#2a1406"), sw=1.8),
        line("M16 34 L16 52", HL, 2, 0.6),
    ])


def projects(ic):
    return "".join([
        shape(ic, "M16 14 L48 14 L48 54 L16 54 Z", PAPER, ic.lg(PAPER, 0, 0, 1, 1)),
        shape(ic, "M10 10 C10 6 14 6 16 8 L50 8 C54 8 54 14 50 16 L14 16 C10 16 10 12 10 10 Z", PAPER, ic.lg(PAPER, 0, 0, 0, 1)),
        shape(ic, "M12 52 C12 48 16 48 18 50 L52 50 C56 50 56 56 52 58 L16 58 C12 58 12 54 12 52 Z", PAPER, ic.lg(PAPER, 0, 0, 0, 1)),
        line("M22 24 L42 24 M22 31 L40 31 M22 38 L36 38", "#8a6a44", 2.2),
        circle(ic, 40, 44, 5.5, C("#ff9a9a", "#e0474f", "#8a1420", "#2c0608"), sw=1.8),
        line("M20 20 L20 46", HL, 1.8, 0.6),
    ])


def bag(ic):
    return "".join([
        line("M24 20 C24 8 40 8 40 20", LEATHER[3], 6), line("M24 20 C24 8 40 8 40 20", LEATHER[1], 3.6),
        shape(ic, "M12 26 C12 20 16 18 22 18 L42 18 C48 18 52 20 52 26 L54 50 C54 56 50 58 44 58 L20 58 C14 58 10 56 10 50 Z", LEATHER, ic.lg(LEATHER, 0.1, 0, 0.9, 1)),
        shape(ic, "M12 26 C20 32 44 32 52 26 L52 34 C44 40 20 40 12 34 Z", C("#c88a58", "#8a5428", "#5a3014", "#2a1406"), sw=1.8),
        shape(ic, "M27 32 L37 32 L37 42 L27 42 Z", GOLD, ic.lg(GOLD), sw=1.8), dot(32, 37, 1.6, "#6a3a08"),
        line("M16 40 C15 46 15 50 17 54", HL, 2, 0.6),
    ])


def settings(ic):
    pts = []
    for k in range(8):
        a0 = math.radians(k * 45)
        for da, r in ((-15, 20), (-10, 27), (10, 27), (15, 20)):
            a = a0 + math.radians(da)
            pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    gear = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    return "".join([
        shape(ic, gear, STEEL, ic.lg(STEEL, 0.1, 0, 0.9, 1)),
        circle(ic, 32, 32, 11, C("#8a96a8", "#5a6678", "#3a4454", "#1e2430"), sw=1.8),
        circle(ic, 32, 32, 7, GOLD, sw=1.8), dot(32, 32, 2.6, "#6a3a08"),
        line("M18 20 C21 16 25 14 29 13", HL, 2.2, 0.7),
    ])


def star(cx, cy, r1, r2):
    pts = []
    for k in range(10):
        r = r1 if k % 2 == 0 else r2
        a = math.radians(-90 + k * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def gold(ic):
    return "".join([
        circle(ic, 32, 32, 25, GOLD, ic.lg(GOLD, 0.2, 0, 0.8, 1)),
        f'<circle cx="32" cy="32" r="19" fill="none" stroke="{GOLD[2]}" stroke-width="2"/>',
        shape(ic, star(32, 33, 11, 5), C("#fff6c8", "#ffd84a", "#c8900c", "#8a5a08"), sw=1.4),
        line("M14 26 C16 18 22 12 30 10", HL, 2.6, 0.7),
    ])


def wb(ic):
    """a bronze coin with a real square hole: the coin and the raised rim around the hole are cut through (even-odd)"""
    coin = "M7 32 A25 25 0 1 0 57 32 A25 25 0 1 0 7 32 Z M25 25 L39 25 L39 39 L25 39 Z"
    rim = "M19 19 L45 19 L45 45 L19 45 Z M25 25 L39 25 L39 39 L25 39 Z"
    odd = ' fill-rule="evenodd"'
    return "".join([
        shape(ic, coin, BRONZE, ic.lg(BRONZE, 0.2, 0, 0.8, 1), extra=odd),
        f'<path d="M13 32 A19 19 0 1 0 51 32 A19 19 0 1 0 13 32 Z" fill="none" stroke="{BRONZE[2]}" stroke-width="2"/>',
        shape(ic, rim, C("#e8a868", "#b0703a", "#7a4a1e", "#2e1606"), extra=odd, sw=1.8),
        line("M14 26 C16 18 22 12 30 10", HL, 2.6, 0.7),
    ])


def map_(ic):
    """a folded parchment map with a dotted path to a red X"""
    return "".join([
        shape(ic, "M6 14 L22 8 L42 14 L58 8 L58 50 L42 56 L22 50 L6 56 Z", PAPER, ic.lg(PAPER, 0, 0, 1, 1)),
        shape(ic, "M22 8 L42 14 L42 56 L22 50 Z", C("#f0d8a0", "#dcc088", "#b09060", "#3a2410"), sw=1.6),
        line("M12 44 C16 36 22 40 26 32 C30 24 36 30 40 24", "#8a5a2a", 2.4, 0.9),
        line("M44 18 L52 26 M52 18 L44 26", "#d23a3a", 3.2),
        line("M12 20 L18 18", HL, 1.8, 0.6),
    ])


def chest(ic):
    """a wooden treasure chest with a domed lid, gold bands and a lock"""
    band = C("#fff2a6", "#f6c030", "#b8780c", "#3a1e06")
    return "".join([
        shape(ic, "M8 32 L56 32 L56 56 L8 56 Z", WOOD, ic.lg(WOOD, 0, 0, 1, 1)),
        shape(ic, "M8 32 C8 18 18 12 32 12 C46 12 56 18 56 32 Z", C("#f0b878", "#b8743e", "#7a4420", "#2a1406"), ic.lg(WOOD, 0, 0, 0.6, 1)),
        shape(ic, "M8 30 L56 30 L56 36 L8 36 Z", band, ic.lg(band, 0, 0, 0, 1), sw=1.6),
        shape(ic, "M14 14 L20 13 L20 56 L14 56 Z", band, sw=1.4), shape(ic, "M44 13 L50 14 L50 56 L44 56 Z", band, sw=1.4),
        shape(ic, "M27 30 L37 30 L37 42 L27 42 Z", band, ic.lg(band), sw=1.6), dot(32, 36, 1.8, "#3a1e06"),
        line("M24 18 C28 15 34 15 38 16", HL, 2, 0.6),
    ])


def encounter(ic):
    """a speech bubble with a big exclamation mark: something is here"""
    bub = C("#fffaea", "#f4e2b0", "#c9a36a", "#3a2410")
    return "".join([
        shape(ic, "M10 12 C10 8 12 6 16 6 L48 6 C52 6 54 8 54 12 L54 40 C54 44 52 46 48 46 L30 46 L18 58 L20 46 L16 46 C12 46 10 44 10 40 Z", bub, ic.lg(bub, 0, 0, 1, 1)),
        shape(ic, "M28 12 L36 12 L34 32 L30 32 Z", C("#ffe27a", "#f6a020", "#b8600c", "#3a1a04"), sw=1.6),
        circle(ic, 32, 39, 3.6, C("#ffe27a", "#f6a020", "#b8600c", "#3a1a04"), sw=1.6),
        line("M15 12 L15 36", HL, 1.8, 0.6),
    ])


def library(ic):
    """three books: two standing, one leaning, and a closed one on top"""
    red, blue, green = C("#ff9a9a", "#d8404a", "#8a1822", "#2c0608"), C("#9ad0ff", "#3a7ad8", "#1e4088", "#0a1430"), C("#a8f0a0", "#3aa84a", "#1e6a28", "#0a260e")
    page = C("#fffaf0", "#f4ead8", "#c8b89a", "#3a2a1a")
    return "".join([
        shape(ic, "M10 18 L22 18 L22 56 L10 56 Z", red, ic.lg(red, 0, 0, 1, 0)),
        line("M10 24 L22 24 M10 50 L22 50", "#ffd23a", 2),
        shape(ic, "M24 12 L36 12 L36 56 L24 56 Z", blue, ic.lg(blue, 0, 0, 1, 0)),
        line("M24 18 L36 18 M24 50 L36 50", "#ffd23a", 2),
        shape(ic, "M40 20 L50 16 L60 52 L50 56 Z", green, ic.lg(green, 0, 0, 1, 0)),
        shape(ic, "M6 56 L58 56 L58 60 L6 60 Z", C("#c8905a", "#8a5a2a", "#5a3414", "#2a1406"), sw=1.6),
        shape(ic, "M26 30 L34 30 L34 38 L26 38 Z", page, sw=1.2),
        line("M13 22 L13 46", HL, 1.6, 0.6),
    ])


ICONS = {"u-chest": chest, "u-encounter": encounter, "u-library": library, "u-map": map_, "u-home": home, "u-projects": projects, "u-bag": bag, "u-settings": settings, "u-gold": gold, "u-wb": wb}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, draw in ICONS.items():
        ic = Icon()
        ic.add(draw(ic))
        (OUT / f"{key}.svg").write_text(ic.svg().replace("<svg ", '<svg data-generated="ui_icons.py" ', 1), encoding="utf-8")
    print(f"ui icons: wrote {len(ICONS)}")


if __name__ == "__main__":
    main()
