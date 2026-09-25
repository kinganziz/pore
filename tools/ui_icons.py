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
    return "".join([
        circle(ic, 32, 32, 25, BRONZE, ic.lg(BRONZE, 0.2, 0, 0.8, 1)),
        f'<circle cx="32" cy="32" r="19" fill="none" stroke="{BRONZE[2]}" stroke-width="2"/>',
        shape(ic, "M20 20 L44 20 L44 44 L20 44 Z", C("#8a5424", "#6a3a14", "#4a2808", "#2e1606"), sw=1.8),
        shape(ic, "M26 26 L38 26 L38 38 L26 38 Z", C(INK, INK, INK, "#2e1606"), sw=1.2),
        line("M14 26 C16 18 22 12 30 10", HL, 2.6, 0.7),
    ])


ICONS = {"u-home": home, "u-projects": projects, "u-bag": bag, "u-settings": settings, "u-gold": gold, "u-wb": wb}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, draw in ICONS.items():
        ic = Icon()
        ic.add(draw(ic))
        (OUT / f"{key}.svg").write_text(ic.svg().replace("<svg ", '<svg data-generated="ui_icons.py" ', 1), encoding="utf-8")
    print(f"ui icons: wrote {len(ICONS)}")


if __name__ == "__main__":
    main()
