#!/usr/bin/env python3
"""Draw PORE's own icons for the non-equipment items (potions, food, ores, drops, keys, skins...) -> icons/modern/i<id>.svg

Same drawing kit and style as tools/modern_icons.py (64-unit grid, soft top-left light, dark outline,
gradient fills, white highlight); tools/pixelart.mjs then turns every drawing into the pixel icon.
Hand-edited files are kept unless --force is given.

Usage: python tools/goods_icons.py [--force] [--only "Name,Name"]
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from modern_icons import HL, Icon, C, P, circle, dot, f, facet_gem, line, shape, sparkle, tube  # noqa: E402
from skin_icons import skin_spec  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"
INK = "#141216"

GLASS = C("#ffffff", "#dfeaf2", "#93a6b8", "#26303c")
CORK = C("#e8c49a", "#b0804e", "#6e4a26", "#2c180c")
LIME = C("#faffc0", "#bde632", "#5e8a10", "#1c2a04")
DARK = C("#8a8aa0", "#4a4a5e", "#24242e", "#0a0a10")
COAL = C("#6a6a78", "#34343e", "#18181e", "#060608")
BLOOD = C("#ff8a8a", "#c01830", "#600818", "#240408")
HONEY = C("#fff2a0", "#ffbc2e", "#c46a0c", "#3c1e04")
STONE = C("#d8d0c4", "#a09484", "#665a4c", "#241e18")
GHOST = C("#ffffff", "#d8e4e0", "#8aa09a", "#1e2826")
SLIME = C("#e6ffb0", "#7ee83a", "#2e8a1a", "#0c2a06")
BROWN = C("#e0a878", "#9a6038", "#5a3218", "#200e04")
SKIN = C("#ffe0c0", "#e8a878", "#a8683e", "#3a1c0a")


# ----------------------------------------------------------------------------- small helpers
def J(parts) -> str:
    """Join drawing parts; some helpers (tube, facet_gem) return lists."""
    return "".join(J(p) if isinstance(p, (list, tuple)) else (p or "") for p in parts)


def ell(ic, cx, cy, rx, ry, pal, grad=None, sw=2.0) -> str:
    return (f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{grad or ic.rg(pal)}" '
            f'stroke="{pal[3]}" stroke-width="{f(sw)}"/>')


def rect(ic, x, y, w, h, pal, rx=0.0, grad=None, sw=2.0) -> str:
    return (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(rx)}" fill="{grad or ic.lg(pal)}" '
            f'stroke="{pal[3]}" stroke-width="{f(sw)}"/>')


def flat(d, color, op=1.0) -> str:
    o = "" if op >= 1 else f' opacity="{f(op)}"'
    return f'<path d="{d}" fill="{color}"{o}/>'


def hl(d, w=2.2, op=0.8) -> str:
    return line(d, HL, w, op)


def poly(pts) -> str:
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def star_pts(cx, cy, r1, r2, n=5, a0=-90):
    pts = []
    for k in range(n * 2):
        r = r1 if k % 2 == 0 else r2
        a = math.radians(a0 + k * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def leaf(ic, x, y, ang=-30, size=9.0, pal=None) -> str:
    pal = pal or P["leaf"]
    d = f"M0 0 C{f(size * .4)} {f(-size * .45)} {f(size * .9)} {f(-size * .35)} {f(size * 1.2)} 0 C{f(size * .9)} {f(size * .35)} {f(size * .4)} {f(size * .45)} 0 0 Z"
    return f'<g transform="translate({f(x)} {f(y)}) rotate({ang})">{shape(ic, d, pal, sw=1.6)}</g>'


# ----------------------------------------------------------------------------- potions
def potion(ic, size, liquid=None, extra=None):
    """small = round flask, medium = cone flask, large = tall square bottle; liquid None = empty glass."""
    s = []
    if size == "small":
        body = "M27 14 L37 14 L37 26 C46 28 51 35 51 42 C51 52 43 58 32 58 C21 58 13 52 13 42 C13 35 18 28 27 26 Z"
        liq = "M16 33 L48 33 C50 36 50 39 50 42 C50 51 43 56.5 32 56.5 C21 56.5 14 51 14 42 C14 39 14 36 16 33 Z"
        cork = (25, 7, 14, 9)
        shine = "M19 38 C19 34 22 31 25 30"
    elif size == "medium":
        body = "M27 14 L37 14 L37 26 L51 50 C53 54 50 58 46 58 L18 58 C14 58 11 54 13 50 L27 26 Z"
        liq = "M20.5 38 L43.5 38 L50 49.5 C51.5 53 49.5 56.5 45.5 56.5 L18.5 56.5 C14.5 56.5 12.5 53 14 49.5 Z"
        cork = (25, 7, 14, 9)
        shine = "M24 32 L18 44"
    else:
        body = "M27 12 L37 12 L37 20 L46 26 L46 54 C46 57 44 58 41 58 L23 58 C20 58 18 57 18 54 L18 26 L27 20 Z"
        liq = "M19.5 33 L44.5 33 L44.5 54 C44.5 56 43 56.5 41 56.5 L23 56.5 C21 56.5 19.5 56 19.5 54 Z"
        cork = (25, 5, 14, 9)
        shine = "M22 30 L22 48"
    s.append(shape(ic, body, GLASS, ic.lg(GLASS, 0, 0, 1, 1)))
    if liquid:
        s.append(shape(ic, liq, liquid, ic.lg(liquid, 0.2, 0, 0.8, 1), sw=0.01))
    s.append(rect(ic, *cork, CORK, rx=2))
    if extra:
        s.append(extra)
    s.append(hl(shine, 2.6, 0.85))
    return J(s)


def potion_set(size, liquid, bubbles=None):
    def draw(ic):
        extra = ""
        if bubbles:
            y = {"small": 47, "medium": 48, "large": 45}[size]
            extra = J(dot(x, y + dy, 2.2, c) for (x, dy), c in zip([(25, 0), (34, -4), (40, 3)], bubbles))
        return potion(ic, size, liquid, extra)
    return draw


RAGE = C("#ffb0e8", "#e0409a", "#7c1650", "#2a061a")
RAGE_B = ["#ffd23a", "#5ce07a", "#4aa8ff"]
MINING = C("#b8b8c8", "#5e5e72", "#2c2c38", "#0e0e14")
POTIONS = {
    "Agility": P["orange"], "Endurance": P["red"], "Experience": LIME, "Luck": P["leaf"], "Mining": MINING,
    "Protection": P["sapphire"], "Rage": RAGE,
}


def potion_spec(name):
    size = "large" if name.startswith("Large ") else "medium" if name.startswith("Medium ") else "small"
    base = name.replace("Large ", "").replace("Medium ", "")
    if base == "Empty Potion":
        return potion_set(size, None)
    for k, pal in POTIONS.items():
        if k in base:
            return potion_set(size, pal, RAGE_B if k == "Rage" else None)
    return None


def love_potion(ic):
    heart = "M32 58 C22 50 10 42 10 30 C10 22 16 17 22 17 C27 17 30 20 32 23 C34 20 37 17 42 17 C48 17 54 22 54 30 C54 42 42 50 32 58 Z"
    return J([rect(ic, 28, 8, 8, 11, GLASS, 1), shape(ic, heart, P["pink"], ic.lg(P["pink"], 0.1, 0, 0.9, 1)),
                    rect(ic, 26, 4, 12, 7, CORK, 2), hl("M17 26 C17 23 19 21 22 21", 2.6)])


def pig_perfume(ic):
    body = "M18 30 C18 24 24 22 32 22 C40 22 46 24 46 30 L46 50 C46 55 42 58 32 58 C22 58 18 55 18 50 Z"
    return J([line("M36 14 C42 8 48 8 52 12", "#3a2a30", 2.4), ell(ic, 52, 16, 6, 5, P["pink"]),
                    rect(ic, 27, 12, 10, 11, P["gold"], 2), shape(ic, body, P["crimson"], ic.lg(P["crimson"], 0.1, 0, 0.9, 1)),
                    ell(ic, 32, 42, 7, 5.5, P["pink"], sw=1.4), dot(29.5, 42, 1.3, INK), dot(34.5, 42, 1.3, INK), hl("M23 30 L23 46", 2.6)])


def blood_potion(ic):
    return J([shape(ic, "M26 10 L38 10 L38 20 C49 23 55 31 55 40 C55 51 45 58 32 58 C19 58 9 51 9 40 C9 31 15 23 26 20 Z", GLASS, ic.lg(GLASS)),
                    circle(ic, 32, 40, 17, BLOOD), rect(ic, 24, 5, 16, 8, CORK, 2), hl("M18 36 C18 31 22 27 26 26", 2.8)])


def beast_vial(ic):
    parts = [rect(ic, 26, 18, 12, 36, GLASS, 5), rect(ic, 27.5, 30, 9, 22.5, BROWN, 4, sw=0.01),
             rect(ic, 24, 10, 16, 9, P["gold"], 2), dot(32, 14.5, 2.2, P["ruby"][1]), hl("M30 22 L30 44", 2)]
    return f'<g transform="rotate(35 32 32)">{J(parts)}</g>'


def forget_me_now(ic):
    murky = C("#e8e6a0", "#8e8a3a", "#4c4818", "#1c1a06")
    return potion(ic, "small", murky, line("M24 48 C24 44 30 43 32 46 C34 50 40 49 40 45", "#e8e6c0", 2, 0.9))


# ----------------------------------------------------------------------------- ores, ingots, nuggets
def ore(ic, pal, speck=None):
    big = "M8 40 L14 24 L28 18 L40 24 L42 40 L34 50 L16 52 Z"
    small = "M38 44 L44 34 L54 34 L58 44 L52 54 L42 54 Z"
    s = [shape(ic, big, pal, ic.lg(pal, 0, 0, 1, 1)), shape(ic, small, pal, ic.lg(pal, 0, 0, 1, 1))]
    s.append(line("M14 24 L24 32 L28 18 M24 32 L16 52 M24 32 L42 40", pal[2], 1.4, 0.8))
    s.append(line("M44 34 L48 44 L58 44 M48 44 L42 54", pal[2], 1.2, 0.8))
    if speck:
        for x, y, r in [(18, 34, 2.4), (32, 28, 2), (30, 42, 2.2), (50, 42, 1.8)]:
            s.append(dot(x, y, r, speck))
    s.append(hl("M12 30 L15 25 L26 20", 2.4))
    return J(s)


def ingot(ic, pal):
    top = "M12 30 L38 18 L54 25 L28 37 Z"
    front = "M12 30 L28 37 L28 48 L12 41 Z"
    side = "M28 37 L54 25 L54 36 L28 48 Z"
    return J([shape(ic, front, pal, ic.lg(pal, 0, 0, 0.2, 1.4)), shape(ic, side, pal, ic.lg((pal[1], pal[2], pal[2], pal[3]), 0, 0, 1, 1)),
                    shape(ic, top, pal, ic.lg((pal[0], pal[0], pal[1], pal[3]), 0, 0, 1, 1)), hl("M18 29 L37 20.5", 2.2, 0.9)])


def nugget(ic, pal):
    d = "M14 38 C12 30 20 24 28 25 C34 20 46 22 50 30 C56 34 54 44 46 46 C38 50 22 50 14 38 Z"
    return J([shape(ic, d, pal, ic.rg(pal)), dot(26, 34, 2, pal[2]), dot(40, 38, 2.4, pal[2]), dot(36, 30, 1.6, pal[2]),
                    hl("M20 32 C22 29 26 28 29 29", 2.4)])


def coal(ic):
    s = [shape(ic, "M10 40 L16 26 L30 20 L44 24 L52 34 L50 48 L36 54 L18 52 Z", COAL, ic.lg(COAL, 0, 0, 1, 1))]
    s.append(line("M16 26 L28 34 L30 20 M28 34 L18 52 M28 34 L50 48 M28 34 L44 24", "#5a5a66", 1.4, 0.8))
    s.append(hl("M14 32 L17 27 L28 22", 2.2))
    return J(s)


# ----------------------------------------------------------------------------- keys
def key(ic, pal, bow="round", gem_pal=None):
    s = [rect(ic, 29, 26, 6, 30, pal, 1.5), rect(ic, 34, 44, 9, 5, pal, 1), rect(ic, 34, 51, 7, 5, pal, 1)]
    if bow == "round":
        s.append(circle(ic, 32, 18, 11, pal))
        s.append(circle(ic, 32, 18, 4.5, C(INK, INK, INK, pal[3]), sw=1.2))
    elif bow == "ornate":
        for cx, cy in [(22, 16), (42, 16), (32, 8)]:
            s.append(circle(ic, cx, cy, 7, pal))
        s.append(circle(ic, 32, 20, 9, pal))
        s.append(circle(ic, 32, 20, 3.5, C(INK, INK, INK, pal[3]), sw=1.2))
    elif bow == "spiky":
        s.append(shape(ic, poly(star_pts(32, 18, 15, 8, 7)), pal, ic.rg(pal)))
        s.append(circle(ic, 32, 18, 4.5, C("#ff6ab8", "#c8327a", "#6c1648", "#260616"), sw=1.2))
    if gem_pal:
        s += [facet_gem(ic, 32, 34, 4.5, gem_pal)]
    s.append(hl("M24 14 C25 11 28 9 31 9" if bow != "ornate" else "M28 6 C29 4 31 3 33 3", 2.2))
    return J(s)


# ----------------------------------------------------------------------------- fruit, berries
def berries(ic, pal, spots=None, glow=None):
    s = [line("M32 8 C30 14 26 18 22 22 M32 8 C36 14 40 20 42 22 M32 8 L32 24", "#3a5a2a", 2.4), leaf(ic, 33, 10, -20, 10)]
    for cx, cy, r in [(22, 30, 9), (42, 30, 9), (32, 44, 9.5), (18, 48, 7), (46, 48, 7)]:
        s.append(circle(ic, cx, cy, r, pal, sw=2.2 if glow is None else 1.6))
        if glow:
            s.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r - 2.5)}" fill="none" stroke="{glow}" stroke-width="1.6"/>')
        if spots:
            s.append(dot(cx + 2, cy + 2, 1.6, spots))
        s.append(dot(cx - r * 0.4, cy - r * 0.4, max(1.2, r * 0.22), HL, 0.9))
    return J(s)


def apple(ic, pal=None, worm=False):
    pal = pal or P["red"]
    body = "M32 20 C38 14 52 14 54 30 C56 44 46 58 38 56 C35 55 34 54 32 54 C30 54 29 55 26 56 C18 58 8 44 10 30 C12 14 26 14 32 20 Z"
    s = [shape(ic, body, pal, ic.lg(pal, 0.1, 0, 0.9, 1)), line("M32 22 C32 16 34 10 38 7", "#4a2a14", 2.8), leaf(ic, 36, 12, -25, 11)]
    if worm:
        s.append(circle(ic, 40, 36, 4, C(INK, INK, INK, "#2a0608"), sw=1))
        s.append(tube(ic, "M40 36 C46 34 50 38 54 34", C("#ffd6e0", "#f09ab0", "#a85068", "#3a1420"), 3.5))
        s.append(dot(53, 33.5, 1, INK))
    s.append(hl("M16 30 C16 25 19 21 23 20", 2.8))
    return J(s)


def cherry(ic, pal=None, cursed=False):
    pal = pal or P["red"]
    s = [line("M22 40 C24 26 30 14 40 8 M42 42 C42 28 40 16 40 8", "#3a5a2a" if not cursed else "#4a3a4a", 2.4), leaf(ic, 40, 8, 10, 11)]
    s += [circle(ic, 22, 44, 10, pal), circle(ic, 43, 46, 10, pal)]
    s += [dot(18, 40, 2.2, HL, 0.9), dot(39, 42, 2.2, HL, 0.9)]
    if cursed:
        s += [dot(20, 46, 1.6, "#ff4a6a"), dot(25, 46, 1.6, "#ff4a6a"), dot(41, 48, 1.6, "#ff4a6a"), dot(46, 48, 1.6, "#ff4a6a")]
    return J(s)


def soulfruit(ic):
    ghost = "M14 54 L14 28 C14 16 22 8 32 8 C42 8 50 16 50 28 L50 54 L44 48 L38 54 L32 48 L26 54 L20 48 Z"
    return J([shape(ic, ghost, GHOST, ic.lg(GHOST, 0.1, 0, 0.9, 1)), ell(ic, 25, 28, 3.6, 5, C(INK, INK, INK, INK), sw=0.5),
                    ell(ic, 39, 28, 3.6, 5, C(INK, INK, INK, INK), sw=0.5), ell(ic, 32, 40, 3, 3.5, C(INK, INK, INK, INK), sw=0.5),
                    hl("M19 26 C19 19 23 14 28 13", 2.6)])


def strawberry(ic):
    body = "M32 58 C22 52 12 40 12 30 C12 22 20 18 32 20 C44 18 52 22 52 30 C52 40 42 52 32 58 Z"
    s = [shape(ic, body, P["red"], ic.lg(P["red"], 0.1, 0, 0.9, 1))]
    s += [dot(x, y, 1.3, "#ffe6a0") for x, y in [(22, 30), (32, 28), (42, 30), (18, 38), (28, 38), (38, 38), (46, 38), (24, 46), (34, 46), (30, 52), (40, 46)]]
    s.append(shape(ic, poly(star_pts(32, 20, 12, 4.5, 6)), P["leaf"], sw=1.6))
    s.append(hl("M17 30 C17 26 20 24 23 24", 2.4))
    return J(s)


def tomato(ic):
    body = "M32 18 C46 18 56 26 56 38 C56 50 46 58 32 58 C18 58 8 50 8 38 C8 26 18 18 32 18 Z"
    return J([shape(ic, body, P["red"], ic.rg(P["red"])), shape(ic, poly(star_pts(32, 19, 13, 4, 5)), P["leaf"], sw=1.6),
                    line("M32 18 L33 10", "#3a5a2a", 2.4), hl("M14 34 C15 29 19 25 24 24", 2.8)])


def pumpkin(ic, face=False):
    pal = P["orange"]
    s = [line("M32 16 C31 12 33 8 37 6", "#4a3a14", 3.4)]
    s += [ell(ic, 20, 38, 12, 18, pal), ell(ic, 44, 38, 12, 18, pal), ell(ic, 32, 38, 12, 19, pal)]
    if face:
        s += [flat("M20 32 L27 32 L23.5 26 Z", "#ffe66a"), flat("M37 32 L44 32 L40.5 26 Z", "#ffe66a"),
              flat("M18 42 L46 42 C44 50 38 53 32 53 C26 53 20 50 18 42 Z", "#ffe66a"), flat("M26 42 L30 42 L28 46 Z M34 42 L38 42 L36 46 Z", "#c24e14")]
    s += [leaf(ic, 36, 16, -10, 10)]
    s.append(hl("M12 32 C12 27 14 24 17 22", 2.4))
    return J(s)


def acorn(ic):
    return J([ell(ic, 32, 40, 13, 16, BROWN), shape(ic, "M14 30 C14 20 22 14 32 14 C42 14 50 20 50 30 C44 33 20 33 14 30 Z", C("#c8a070", "#7a5230", "#46301a", "#1c1008")),
                    line("M20 22 L44 22 M17 27 L47 27", "#4a321a", 1.2, 0.7), line("M32 14 L33 7", "#4a2a14", 3), hl("M22 38 C22 34 24 32 26 31", 2.4)])


def potato(ic, roast=False):
    pal = C("#f0c890", "#c08a4a", "#7a5226", "#2e1c0a") if not roast else C("#d88a4a", "#8a4a1e", "#4a220c", "#1c0a04")
    s = [shape(ic, "M12 36 C10 26 18 18 30 18 C44 16 54 24 54 34 C54 46 44 52 32 52 C20 52 14 46 12 36 Z", pal, ic.rg(pal))]
    s += [dot(x, y, 1.4, pal[2]) for x, y in [(24, 30), (40, 28), (34, 40), (46, 40), (20, 42)]]
    if roast:
        s.append(line("M18 30 L44 22 M16 38 L50 30 M20 46 L52 38", "#2e1406", 2, 0.8))
    s.append(hl("M17 32 C18 27 22 24 27 23", 2.4))
    return J(s)


def pickle(ic):
    d = "M14 50 C8 44 12 34 22 26 C32 18 44 12 50 16 C56 22 50 32 42 40 C32 50 20 56 14 50 Z"
    s = [shape(ic, d, C("#d8e070", "#7e8a2a", "#44501a", "#161c06"), None)]
    s += [dot(x, y, 1.5, "#e8f0a0") for x, y in [(22, 38), (30, 30), (38, 24), (28, 42), (40, 34), (46, 22)]]
    s.append(hl("M16 44 C18 38 24 32 30 27", 2.4))
    return J(s)


def baguette(ic):
    d = "M10 46 C6 40 12 34 20 30 L44 16 C52 12 58 18 54 26 C52 28 50 30 46 32 L22 46 C18 50 12 50 10 46 Z"
    pal = C("#ffd89a", "#e0a050", "#9a5a1e", "#3a1e06")
    return J([shape(ic, d, pal, ic.lg(pal, 0, 0, 1, 1)), line("M20 36 L26 40 M30 30 L36 34 M40 24 L46 28", "#fff0c8", 2.4), hl("M14 42 L22 36", 2.2)])


def cheese(ic):
    top = "M8 32 L38 16 L56 30 Z"
    front = "M8 32 L56 30 L56 48 L8 52 Z"
    pal = C("#fff6b0", "#ffd23a", "#d0900c", "#3c2404")
    return J([shape(ic, front, pal, ic.lg(pal, 0, 0, 0.3, 1)), shape(ic, top, pal, ic.lg((pal[0], pal[0], pal[1], pal[3]))),
                    ell(ic, 20, 42, 4, 3.5, C("#e0a020", "#c08010", "#8a5808", "#6a4006"), sw=0.8), ell(ic, 40, 40, 3, 2.6, C("#e0a020", "#c08010", "#8a5808", "#6a4006"), sw=0.8),
                    ell(ic, 34, 26, 3.4, 2, C("#e0a020", "#c08010", "#8a5808", "#6a4006"), sw=0.8), hl("M12 36 L52 34", 1.8, 0.8)])


def sausages(ic):
    pal = C("#f0a080", "#b85a3a", "#6e2a18", "#2a0c06")
    return J([tube(ic, "M14 46 C14 30 22 16 34 12", pal, 9), tube(ic, "M30 52 C34 36 42 24 52 20", pal, 9),
                    hl("M13 40 C14 32 18 24 24 18", 2), hl("M30 46 C33 38 38 30 44 25", 2)])


def ribs(ic):
    meat = C("#e89070", "#a44a30", "#5e2414", "#240a04")
    s = [shape(ic, "M10 36 C8 24 20 16 32 18 C44 20 50 30 46 42 C42 52 20 54 10 36 Z", meat, ic.rg(meat))]
    for y in (26, 34, 42):
        s.append(tube(ic, f"M36 {y} L56 {y - 8}", P["bone"], 4))
    s.append(line("M16 28 C20 34 22 40 22 46 M26 24 C30 30 32 38 32 46", "#5e2414", 1.6, 0.7))
    s.append(hl("M14 30 C16 25 20 22 25 21", 2.4))
    return J(s)


def sandwich(ic):
    bread = C("#fff0c8", "#e8c080", "#a07838", "#3a2410")
    return J([shape(ic, "M8 44 L32 56 L56 42 L56 36 L32 48 L8 36 Z", bread),
                    shape(ic, "M8 36 L32 48 L56 36 L50 32 L32 42 L14 32 Z", P["leaf"], sw=1.4),
                    shape(ic, "M12 32 L32 42 L52 32 L46 29 L32 36 L18 29 Z", P["red"], sw=1.4),
                    shape(ic, "M8 30 L32 42 L56 30 L32 12 Z", bread, ic.lg(bread, 0, 0, 1, 1)), hl("M16 28 L32 16", 2.2)])


def durum(ic):
    wrap = C("#fff0d0", "#e6c898", "#a88a58", "#3a2c16")
    s = [tube(ic, "M14 50 L48 16", wrap, 16), dot(46, 18, 4, P["red"][1]), dot(51, 22, 3.4, P["leaf"][1]), dot(42, 14, 3, P["leaf"][1]),
         dot(47, 13, 2.6, "#8a4a2a"), line("M20 38 L26 44 M26 32 L32 38", "#a88a58", 1.6, 0.8), hl("M12 44 L36 20", 2.2)]
    return J(s)


def pie_slice(ic, filling, cream=False):
    crust = C("#ffe0a8", "#d89850", "#8a5418", "#321a04")
    s = [shape(ic, "M6 44 L56 30 L56 42 L6 54 Z", crust), shape(ic, "M8 46 L54 34 L54 38 L8 50 Z", filling, sw=1),
         shape(ic, "M6 44 L56 30 C56 24 50 20 44 20 Z", filling if cream else crust, ic.lg(crust if not cream else filling, 0, 0, 1, 1))]
    if cream:
        s.append(ell(ic, 42, 24, 5, 4, P["white"]))
    else:
        s.append(line("M20 38 L40 26 M26 40 L48 28", "#8a5418", 1.6, 0.8))
    s.append(hl("M12 42 L40 24", 2))
    return J(s)


def jar(ic, fill, label=None, lid=None):
    lid = lid or P["red"]
    s = [shape(ic, "M16 22 L48 22 L50 28 L50 52 C50 56 46 58 42 58 L22 58 C18 58 14 56 14 52 L14 28 Z", GLASS, ic.lg(GLASS)),
         rect(ic, 16, 28, 32, 27, fill, 3, sw=0.01), rect(ic, 14, 12, 36, 10, lid, 3)]
    if label:
        s.append(rect(ic, 20, 36, 24, 12, C("#ffffff", "#f4ecd8", "#c8b890", "#5a4a30"), 2, sw=1.2))
    s.append(hl("M19 30 L19 50", 2.4))
    return J(s)


def honeyjar(ic):
    pot = HONEY
    return J([ell(ic, 32, 42, 20, 16, pot), rect(ic, 20, 18, 24, 10, pot, 3), rect(ic, 16, 12, 32, 8, CORK, 3),
                    flat("M20 28 C20 34 24 34 24 30 C24 36 28 36 28 30 L36 30 C36 38 40 38 40 30 L44 28 Z", "#ffe070"), hl("M17 38 C18 33 21 30 25 29", 2.6)])


def honeycomb(ic):
    s = []
    for cx, cy in [(22, 22), (38, 22), (14, 36), (30, 36), (46, 36), (22, 50), (38, 50)]:
        s.append(shape(ic, poly([(cx + 8 * math.cos(math.radians(a)), cy + 8 * math.sin(math.radians(a))) for a in range(30, 390, 60)]), HONEY, ic.rg(HONEY), sw=1.8))
        s.append(dot(cx - 2, cy - 2, 1.6, "#fff6c0"))
    return J(s)


def wine(ic):
    bottle = C("#b86a80", "#6a1a34", "#34081a", "#140206")
    return J([shape(ic, "M28 6 L36 6 L36 22 C42 24 44 28 44 32 L44 56 C44 58 42 59 40 59 L24 59 C22 59 20 58 20 56 L20 32 C20 28 22 24 28 22 Z", bottle, ic.lg(bottle)),
                    rect(ic, 27, 4, 10, 8, P["red"], 1.5), rect(ic, 22, 36, 20, 12, C("#fffaf0", "#f0e6d0", "#b8a888", "#4a3e2a"), 1.5, sw=1.2),
                    line("M26 42 L38 42", "#6a1a34", 1.6), hl("M24 30 L24 52", 2.4)])


def sardine_tin(ic):
    tin = C("#f4f6fa", "#b8c0cc", "#6a7486", "#1e232e")
    return J([rect(ic, 10, 26, 44, 26, tin, 6), rect(ic, 14, 22, 36, 10, tin, 4),
                    ell(ic, 32, 40, 14, 6, C("#ffd6a0", "#e0904a", "#9a5220", "#3a1a06")), line("M22 40 L42 40", "#9a5220", 1.4),
                    tube(ic, "M50 24 C56 22 58 16 54 12", tin, 3), hl("M14 32 L14 46", 2.2)])


def coconut_drink(ic):
    nut = C("#b88a64", "#7a4e32", "#46291a", "#1c100a")
    return J([ell(ic, 32, 42, 20, 16, nut), ell(ic, 32, 30, 16, 5, C("#ffffff", "#f4f0e0", "#c8c0a8", "#3a3226"), sw=1.6),
                    line("M36 30 L46 8", "#e84a6a", 3), sparkle(20, 16, 6, "#8fd0ff"), circle(ic, 24, 24, 5, P["sapphire"], sw=1.2),
                    hl("M16 40 C16 35 19 32 23 30", 2.4)])


def crispy_seaweed(ic):
    pal = C("#8ab070", "#3e6a3a", "#1e3a1e", "#0a160a")
    return J([shape(ic, "M12 18 L44 10 L54 44 L20 54 Z", pal, ic.lg(pal, 0, 0, 1, 1)),
                    line("M20 24 L42 18 M22 32 L46 26 M24 40 L48 34", "#1e3a1e", 1.6, 0.8), dot(30, 36, 1.4, "#ffffff"), dot(40, 28, 1.4, "#ffffff"),
                    hl("M16 22 L40 15", 2)])


def chocolate_bunny(ic):
    choc = P["chocolate"]
    return J([ell(ic, 24, 14, 4.5, 11, choc), ell(ic, 36, 14, 4.5, 11, choc), ell(ic, 30, 30, 12, 11, choc), ell(ic, 34, 48, 16, 12, choc),
                    dot(26, 28, 1.8, INK), dot(34, 28, 1.8, INK), ell(ic, 50, 50, 5, 5, C("#ffffff", "#f4ecd8", "#c8b890", "#5a4a30"), sw=1.4),
                    hl("M22 26 C22 23 24 21 27 20", 2.2)])


def gingerbread(ic):
    dough = C("#e8b070", "#b0703a", "#6e3e18", "#2a1406")
    icing = "#ffffff"
    return J([shape(ic, "M10 30 L32 10 L54 30 L50 30 L50 56 L14 56 L14 30 Z", dough, ic.lg(dough)),
                    line("M10 30 L32 10 L54 30", icing, 2.6), rect(ic, 27, 40, 10, 16, C("#ff9aac", "#e2343e", "#8a1420", "#2c0608"), 1.5, sw=1.2),
                    rect(ic, 18, 34, 7, 7, C("#fff6a8", "#ffd23a", "#d08a10", "#3c2404"), 1, sw=1), rect(ic, 39, 34, 7, 7, C("#fff6a8", "#ffd23a", "#d08a10", "#3c2404"), 1, sw=1),
                    dot(32, 24, 2, "#e2343e"), line("M14 50 L50 50", icing, 1.4, 0.9)])


def candy(ic):
    wrap = C("#ffd8a0", "#ff9a3a", "#c24e14", "#401404")
    return J([shape(ic, "M20 32 L4 20 L8 32 L4 44 Z", wrap), shape(ic, "M44 32 L60 20 L56 32 L60 44 Z", wrap),
              ell(ic, 32, 32, 15, 13, C("#8a8a9a", "#3a3446", "#1a1620", "#060608")),
              line("M22 24 L28 42 M32 20 L38 44 M40 22 L44 36", "#ff9a3a", 3.2), hl("M21 28 C22 24 25 21 29 20", 2.2)])


def super_berry(ic):
    pal = HONEY
    return berries(ic, pal, spots="#fff6c0") + sparkle(52, 14, 6, "#fff6a8")


def super_shroom(ic):
    return mushroom(ic, HONEY, spots="#fff6c0") + sparkle(52, 12, 6, "#fff6a8")


# ----------------------------------------------------------------------------- mushrooms and plants
STEM = C("#fffaf0", "#e8dcc4", "#a8977e", "#38323e")


def mushroom(ic, cap, stem=None, spots=None, kind="dome"):
    stem = stem or STEM
    s = [shape(ic, "M25 34 L23 52 C23 56 41 56 41 52 L39 34 Z", stem, ic.lg(stem, 0, 0, 1, 0))]
    if kind == "dome":
        d = "M8 36 C8 20 18 10 32 10 C46 10 56 20 56 36 C46 40 18 40 8 36 Z"
    elif kind == "flat":
        d = "M6 30 C8 20 20 14 32 14 C44 14 56 20 58 30 C52 36 12 36 6 30 Z"
    elif kind == "bell":
        d = "M14 38 C12 26 20 8 32 6 C44 8 52 26 50 38 C42 42 22 42 14 38 Z"
    else:  # wavy
        d = "M6 34 C4 22 16 10 32 10 C48 10 60 22 56 34 C52 30 48 38 42 34 C38 38 30 32 26 36 C20 32 14 38 6 34 Z"
    s.append(shape(ic, d, cap, ic.lg(cap, 0.2, 0, 0.8, 1)))
    if spots:
        for x, y, r in [(20, 24, 3), (34, 18, 2.6), (44, 28, 2.8), (28, 30, 2)]:
            s.append(dot(x, y, r, spots))
    s.append(hl("M14 28 C16 20 22 15 28 14", 2.6))
    return J(s)


def cluster(ic, cap, stem=None, spots=None):
    stem = stem or C("#8a8a9a", "#4a4a5a", "#24242e", "#0a0a10")
    s = []
    for x, y, r, h in [(22, 26, 11, 26), (42, 32, 10, 20), (30, 42, 9, 12)]:
        s.append(rect(ic, x - 3, y, 6, h, stem, 2))
    for x, y, r in [(22, 24, 11), (42, 30, 10), (30, 42, 9)]:
        s.append(shape(ic, f"M{f(x - r)} {f(y + 2)} C{f(x - r)} {f(y - r)} {f(x + r)} {f(y - r)} {f(x + r)} {f(y + 2)} Z", cap, ic.lg(cap, 0.2, 0, 0.8, 1)))
        if spots:
            s.append(dot(x + 2, y - 3, 1.8, spots))
    s.append(hl("M14 22 C15 17 18 15 22 14", 2.2))
    return J(s)


def cave_coral(ic):
    pal = C("#ff9aa8", "#c83a5a", "#6a1a3a", "#240814")
    blue = C("#9ab8ff", "#3a58c8", "#1a2a6a", "#080e2a")
    return J([tube(ic, "M32 58 L32 34 M32 44 C24 40 22 30 18 22 M32 38 C40 34 44 24 46 16", pal, 6),
                    circle(ic, 18, 20, 6, blue), circle(ic, 46, 14, 6, blue), circle(ic, 32, 30, 6, blue)])


def trumpet(ic):
    pal = C("#fff0d6", "#d8c09c", "#8e7658", "#2e2418")
    return J([shape(ic, "M28 56 L30 34 C22 30 14 22 12 12 C22 16 42 16 52 12 C50 22 42 30 34 34 L36 56 Z", pal, ic.lg(pal, 0, 0, 1, 1)),
                    ell(ic, 32, 13, 20, 5, C("#b8a080", "#8e7658", "#5a4a36", "#2e2418"), sw=1.6), hl("M18 18 C22 24 26 28 30 30", 2)])


def flower(ic, petal, center, n=6, r=13, stem=True, petal_r=7.0):
    s = []
    if stem:
        s += [line("M32 40 L32 60", "#2e6a2a", 3.2), leaf(ic, 32, 54, -150, 10), leaf(ic, 32, 50, -30, 10)]
    for k in range(n):
        a = math.radians(-90 + k * 360 / n)
        s.append(ell(ic, 32 + r * math.cos(a), 28 + r * math.sin(a), petal_r, petal_r, petal, sw=1.8))
    s.append(circle(ic, 32, 28, 7, center, sw=1.6))
    s.append(dot(30, 26, 1.8, HL, 0.9))
    return J(s)


def bluebell(ic):
    bell = C("#d0e0ff", "#6a8cf0", "#2a3aa0", "#0c1440")
    s = [line("M20 58 C20 40 26 20 42 10", "#2e6a2a", 3)]
    for x, y in [(42, 12), (30, 22), (24, 36)]:
        s.append(shape(ic, f"M{x - 7} {y + 12} C{x - 7} {y + 2} {x - 4} {y} {x} {y} C{x + 4} {y} {x + 7} {y + 2} {x + 7} {y + 12} L{x + 4} {y + 10} L{x} {y + 13} L{x - 4} {y + 10} Z", bell))
    s.append(leaf(ic, 20, 54, -60, 12))
    return J(s)


def bloodrose(ic):
    rose = P["crimson"]
    return J([line("M32 34 L32 60", "#2e6a2a", 3.2), leaf(ic, 32, 50, -150, 11), leaf(ic, 32, 46, -30, 11),
                    circle(ic, 32, 24, 16, rose), line("M24 22 C26 16 38 16 40 22 C40 30 28 30 28 24 C28 20 34 20 34 24", rose[3], 1.8),
                    hl("M20 20 C21 15 24 12 28 11", 2.4)])


def frost_thistle(ic):
    ice = P["ice"]
    s = [line("M32 36 L32 60", "#3a6a5a", 3)]
    for a in (-60, -30, 0, 30, 60):
        s.append(f'<g transform="rotate({a} 32 36)">{shape(ic, "M29 36 L29 16 L32 8 L35 16 L35 36 Z", ice)}</g>')
    s.append(ell(ic, 32, 38, 9, 6, C("#c6fff4", "#4cc8b4", "#1c6c68", "#082826")))
    return J(s)


def honeydew(ic):
    s = [line("M32 40 L32 60 M32 48 L20 36 M32 46 L44 34", "#2e6a2a", 2.8)]
    for x, y in [(20, 30), (44, 28), (32, 20)]:
        for k in range(5):
            a = math.radians(-90 + k * 72)
            s.append(ell(ic, x + 5.5 * math.cos(a), y + 5.5 * math.sin(a), 4, 4, P["yellow"], sw=1.4))
        s.append(dot(x, y, 2.6, "#e07a2a"))
    return J(s)


def ice_lotus(ic):
    petal = C("#ffffff", "#e6f4ff", "#8ab8e2", "#1a3a5c")
    s = [ell(ic, 32, 50, 22, 6, P["leaf"])]
    for a in (-60, -30, 0, 30, 60):
        s.append(f'<g transform="rotate({a} 32 46)">{shape(ic, "M32 46 C24 38 26 24 32 16 C38 24 40 38 32 46 Z", petal)}</g>')
    s.append(circle(ic, 32, 40, 4.5, P["orange"], sw=1.4))
    return J(s)


def liana(ic):
    return J([tube(ic, "M30 58 C18 50 20 40 32 36 C44 32 46 22 34 16 C26 12 28 6 34 6", P["leaf"], 4),
                    leaf(ic, 22, 46, 160, 10), leaf(ic, 42, 28, -20, 10), leaf(ic, 28, 16, 200, 9)])


def rockplum(ic):
    fruit = C("#e0a080", "#9a5a3a", "#5a2e1a", "#200c04")
    return J([leaf(ic, 32, 44, 180, 22), leaf(ic, 32, 44, 0, 22), ell(ic, 32, 36, 16, 12, fruit),
                    line("M20 34 L44 34 M24 40 L40 40", fruit[2], 1.4, 0.8), hl("M20 32 C21 28 24 26 28 25", 2.2)])


def root(ic):
    pal = C("#f0c890", "#b8844a", "#6e4a22", "#2a1a08")
    return tube(ic, "M36 8 L32 26 L20 36 L14 50 M32 26 L42 38 L40 54 M32 26 L34 44 M20 36 L10 38", pal, 5)


def seaweed(ic):
    pal = C("#9ae08a", "#3a9a4a", "#1e5a2a", "#0a2410")
    return J([tube(ic, "M20 58 C14 44 26 36 20 20 C18 14 22 8 26 6", pal, 6), tube(ic, "M34 58 C40 44 28 34 36 20 C40 14 38 10 36 6", pal, 6),
                    tube(ic, "M46 58 C52 46 44 40 50 28", pal, 5)])


def starzest(ic):
    pal = C("#ffe6b0", "#e8a858", "#9a6224", "#361e06")
    return J([shape(ic, poly(star_pts(32, 34, 24, 10)), pal, ic.lg(pal, 0.1, 0, 0.9, 1)), leaf(ic, 30, 12, -140, 10), hl("M24 26 L30 16", 2.2)])


def sunburst_petal(ic):
    pal = C("#ffe07a", "#f05a1e", "#a8200c", "#3a0a04")
    d = "M12 54 L22 40 L10 36 L26 30 L20 16 L34 24 L40 8 L44 26 L58 22 L48 36 L56 44 L40 44 L42 56 L30 46 Z"
    return J([shape(ic, d, pal, ic.lg(pal, 1, 0, 0, 1)), line("M12 54 L40 30", "#6a1a0a", 2)])


def sunflower(ic):
    return flower(ic, P["yellow"], C("#a86a3a", "#6a3a1a", "#3a1a08", "#1a0a04"), n=12, r=16, stem=False, petal_r=6)


def death_nut(ic):
    pal = C("#6a6478", "#2e2a36", "#16141c", "#060508")
    return J([shape(ic, "M32 8 C44 16 52 28 50 42 C48 54 38 58 32 58 C26 58 16 54 14 42 C12 28 20 16 32 8 Z", pal, ic.lg(pal, 0.1, 0, 0.9, 1)),
                    line("M32 12 C28 24 28 44 32 56 M24 18 C18 30 20 46 26 54 M40 18 C46 30 44 46 38 54", "#56506a", 1.6, 0.9),
                    line("M30 8 L22 2", "#3a2a1a", 3), hl("M20 30 C21 24 24 19 28 16", 2)])


# ----------------------------------------------------------------------------- monster drops
def bone(ic, pal=None):
    pal = pal or P["bone"]
    return J([tube(ic, "M18 46 L46 18", pal, 7), circle(ic, 14, 46, 6, pal), circle(ic, 18, 51, 6, pal),
                    circle(ic, 46, 13, 6, pal), circle(ic, 51, 18, 6, pal), hl("M22 38 L38 22", 1.8)])


def tooth(ic, pal=None, curve=False):
    pal = pal or C("#ffffff", "#e6e8f4", "#9aa0c0", "#2a2c40")
    d = "M18 12 C28 8 42 10 48 16 C50 30 40 48 22 56 C24 44 22 30 18 12 Z" if curve else "M20 10 L44 10 C46 26 40 44 32 58 C24 44 18 26 20 10 Z"
    return J([shape(ic, d, pal, ic.lg(pal, 0, 0, 1, 1)), hl("M25 16 C25 26 26 34 28 42", 2.4)])


def claw(ic):
    pal = C("#ffffff", "#d8d8e0", "#8a8a9a", "#1e1e28")
    s = []
    for dx in (-12, 0, 12):
        s.append(shape(ic, f"M{24 + dx} 50 C{20 + dx} 36 {26 + dx} 18 {40 + dx} 10 C{36 + dx} 22 {34 + dx} 36 {34 + dx} 50 Z", pal, ic.lg(pal, 0, 0, 1, 1)))
    s.append(rect(ic, 8, 48, 44, 8, BROWN, 3))
    return J(s)


def tail(ic):
    pal = C("#8a6a8a", "#3e2a44", "#1e1422", "#0a060c")
    return J([tube(ic, "M44 8 C56 16 50 30 36 30 C22 30 18 42 26 50 C30 54 26 58 20 56", pal, 6),
                    shape(ic, "M20 56 L10 52 L16 60 Z", C("#ff9a9a", "#e2343e", "#8a1420", "#2c0608"))])


def tentacle(ic):
    pal = C("#ff9ad0", "#c83a8a", "#6a1a48", "#260616")
    s = [tube(ic, "M12 54 C10 36 24 30 36 34 C48 38 54 28 50 16 C48 10 42 10 40 14", pal, 10)]
    s += [dot(x, y, 2.2, "#ffd23a") for x, y in [(16, 44), (24, 36), (34, 38), (44, 36), (50, 26)]]
    return J(s)


def eyeball(ic):
    return J([circle(ic, 32, 32, 22, C("#ffffff", "#f0e6e0", "#b8a09a", "#3a2622")),
                    line("M14 24 L22 28 M12 38 L20 36 M44 50 L40 44", "#d23c3c", 1.4, 0.9), circle(ic, 36, 30, 10, P["ruby"]),
                    circle(ic, 37, 29, 5, C(INK, INK, INK, INK), sw=0.5), dot(34, 26, 2, HL), hl("M16 26 C18 19 23 14 29 12", 2.4)])


def slime(ic, pal=None):
    pal = pal or SLIME
    d = "M8 52 C6 44 12 40 14 36 C14 20 22 10 32 10 C42 10 50 20 50 36 C54 38 58 44 56 52 C50 56 44 52 40 56 C36 58 28 58 24 56 C20 52 14 56 8 52 Z"
    return J([shape(ic, d, pal, ic.lg(pal, 0.1, 0, 0.9, 1)), dot(24, 30, 3, HL, 0.9), dot(20, 38, 1.8, HL, 0.7), hl("M20 24 C22 18 26 15 30 14", 2.6)])


def sludge(ic):
    pal = C("#e8b0ff", "#9a3ae0", "#4a1480", "#1a0630")
    d = "M8 50 C8 44 16 42 20 38 C22 26 28 16 34 12 C36 20 40 30 44 36 C50 40 58 44 56 50 C52 56 14 56 8 50 Z"
    return J([shape(ic, d, pal, ic.lg(pal, 0.1, 0, 0.9, 1)), hl("M28 26 C29 22 31 18 33 16", 2.4)])


def icicle(ic):
    pal = C("#ffffff", "#8ee0ff", "#2a88d8", "#0a2a5a")
    return f'<g transform="rotate(-40 32 32)">{shape(ic, "M26 4 L38 4 L42 12 L36 60 L32 62 L28 60 L22 12 Z", pal, ic.lg(pal, 0, 0, 1, 0))}{line("M32 8 L32 52", "#ffffff", 1.6)}</g>'


def sting(ic):
    pal = C("#fffaf0", "#e8dabe", "#a8977e", "#38323e")
    tip = C("#6a6478", "#2e2a36", "#16141c", "#060508")
    return J([shape(ic, "M8 20 C18 8 40 6 52 18 C58 26 58 40 52 52 C50 40 44 30 34 26 C26 22 16 22 8 20 Z", pal, ic.lg(pal, 0, 0, 1, 1)),
                    shape(ic, "M50 36 C54 42 54 48 52 52 C48 46 46 42 44 38 Z", tip, sw=1.4), line("M16 16 L20 20 M26 12 L28 18 M36 12 L36 18", "#a8977e", 1.6)])


def monster_skull(ic):
    horn = C("#fff0d6", "#d8c09c", "#8e7658", "#2e2418")
    s = [tube(ic, "M18 26 C8 22 6 12 10 6", horn, 5), tube(ic, "M46 26 C56 22 58 12 54 6", horn, 5)]
    d = "M32 12 C44 12 52 20 52 32 C52 38 48 42 46 44 L46 52 L18 52 L18 44 C16 42 12 38 12 32 C12 20 20 12 32 12 Z"
    s += [shape(ic, d, P["bone"], ic.lg(P["bone"], 0.1, 0, 0.9, 1)), ell(ic, 24, 32, 5, 5.5, C(INK, INK, INK, INK), sw=0.5),
          ell(ic, 40, 32, 5, 5.5, C(INK, INK, INK, INK), sw=0.5), flat("M32 38 L29 44 L35 44 Z", INK), line("M24 48 L24 52 M32 48 L32 52 M40 48 L40 52", INK, 1.4),
          hl("M18 26 C19 20 23 16 28 15", 2.4)]
    return J(s)


def hide(ic, pal, pattern=None, scales=False):
    d = ("M20 8 C24 12 28 12 32 10 C36 12 40 12 44 8 L48 16 C54 16 58 20 56 26 C52 26 50 30 52 34 C58 38 56 46 50 46 "
         "L48 54 L42 52 C38 56 26 56 22 52 L16 54 L14 46 C8 46 6 38 12 34 C14 30 12 26 8 26 C6 20 10 16 16 16 Z")
    s = [shape(ic, d, pal, ic.rg(pal, 0.4, 0.35, 0.8))]
    if pattern == "stripes":
        s.append(line("M18 22 L28 26 M36 26 L46 22 M16 32 L28 34 M36 34 L48 32 M20 42 L28 42 M36 42 L44 42", "#ffb040", 2.2))
    elif pattern == "spots":
        s += [dot(x, y, 2.6, pal[2]) for x, y in [(24, 24), (40, 26), (30, 36), (44, 40), (22, 42)]]
    elif pattern == "eye":
        s += [circle(ic, 32, 30, 7, C("#ffffff", "#f0e6e0", "#b8a09a", "#3a2622"), sw=1.4), dot(32, 30, 3, INK)]
    elif pattern == "stitch":
        s.append(line("M20 22 L44 44 M24 20 L22 24 M30 26 L28 30 M36 32 L34 36 M42 38 L40 42", "#2a1a14", 1.6))
    if scales:
        for y in (20, 28, 36, 44):
            for x in range(18 if y % 16 else 22, 48, 8):
                s.append(line(f"M{x} {y} C{x + 2} {y + 4} {x + 6} {y + 4} {x + 8} {y}", pal[3], 1.2, 0.7))
    s.append(hl("M18 20 C22 18 26 18 30 16", 2))
    return J(s)


# ----------------------------------------------------------------------------- materials
def bat_wing(ic):
    pal = C("#8a7a9a", "#443a54", "#221c2e", "#0a080e")
    d = "M8 16 C20 12 36 10 56 8 C54 20 52 30 46 40 C42 36 38 38 36 44 C32 40 26 42 24 48 C20 42 14 42 10 44 C12 34 12 24 8 16 Z"
    return J([shape(ic, d, pal, ic.lg(pal, 0, 0, 1, 1)), line("M8 16 L46 40 M20 13 L36 44 M34 11 L24 48", "#6a5a7a", 1.6)])


def branch(ic):
    return J([tube(ic, "M10 54 L52 12 M30 34 L22 18 M40 24 L52 30", BROWN, 5), leaf(ic, 22, 18, -110, 9), leaf(ic, 52, 30, 20, 9)])


def butterfly_wing(ic):
    pal = C("#c8f0ff", "#4ab0f0", "#1a5aa8", "#0a2448")
    return J([shape(ic, "M30 32 C20 12 34 4 50 10 C56 20 50 30 30 32 Z", pal, ic.lg(pal, 0, 0, 1, 1)),
                    shape(ic, "M30 34 C44 34 52 44 44 54 C34 58 26 48 30 34 Z", pal, ic.lg(pal, 0, 0, 1, 1)),
                    dot(42, 18, 3.6, "#ffd23a"), dot(40, 46, 3, "#ffd23a"), line("M30 32 L48 12 M30 34 L42 52", "#0a2448", 1.4)])


def chain(ic):
    pal = P["iron"]
    s = []
    for k, (x, y) in enumerate([(22, 14), (32, 30), (42, 46)]):
        s.append(f'<g transform="rotate({45 if k % 2 == 0 else -45} {x} {y})">{rect(ic, x - 6, y - 10, 12, 20, pal, 6, sw=2)}'
                 f'{rect(ic, x - 2, y - 6, 4, 12, C(INK, INK, INK, INK), 2, sw=0.5)}</g>')
    return J(s)


def emberfruit(ic):
    pal = C("#ffd07a", "#e05a1a", "#7a1a08", "#2a0602")
    return J([shape(ic, "M32 10 C44 14 54 26 52 40 C50 52 40 58 32 58 C24 58 14 52 12 40 C10 26 20 14 32 10 Z", pal, ic.rg(pal)),
                    line("M22 28 L30 36 L26 46 M40 24 L36 34 L44 42", "#ffe66a", 2), line("M32 10 L34 4", "#3a1a08", 3), hl("M18 32 C19 26 22 20 26 17", 2.4)])


def emerald(ic):
    return facet_gem(ic, 32, 32, 22, P["emerald"])


def nail(ic):
    pal = P["steel"]
    return f'<g transform="rotate(40 32 32)">{rect(ic, 20, 8, 24, 6, pal, 2)}{shape(ic, "M29 14 L35 14 L35 50 L32 58 L29 50 Z", pal, ic.lg(pal, 0, 0, 1, 0))}</g>'


def powder(ic):
    pal = C("#ffffff", "#a8e8ff", "#3a9ae0", "#0e2e5a")
    return J([shape(ic, "M6 50 C12 38 22 22 32 20 C42 22 52 38 58 50 C44 54 20 54 6 50 Z", pal, ic.lg(pal, 0.2, 0, 0.8, 1)),
                    sparkle(24, 36, 4, "#ffffff"), sparkle(40, 32, 3, "#ffffff"), dot(54, 56, 1.8, "#3a9ae0"), dot(58, 52, 1.4, "#3a9ae0")])


# ----------------------------------------------------------------------------- relics (golden idols)
GOLD = P["richgold"]


def relic(ic, kind):
    s = []
    if kind == "chalice":
        s += [shape(ic, "M14 12 L50 12 C50 28 42 36 32 36 C22 36 14 28 14 12 Z", GOLD), rect(ic, 29, 36, 6, 12, GOLD),
              shape(ic, "M18 56 C20 48 44 48 46 56 Z", GOLD), facet_gem(ic, 32, 22, 5, P["emerald"])]
    elif kind == "lamp":
        s += [shape(ic, "M6 24 C14 24 16 30 20 34 L44 34 C50 30 56 30 58 36 C54 36 50 40 46 44 C40 50 24 50 18 44 C14 40 10 32 6 24 Z", GOLD),
              ell(ic, 32, 30, 10, 5, GOLD), circle(ic, 32, 24, 3.5, GOLD), shape(ic, "M8 18 C10 12 16 10 12 4 C20 8 18 16 12 22 Z", P["fire"], sw=1.4)]
    elif kind == "heart":
        s += [shape(ic, "M32 58 C22 50 8 42 8 28 C8 18 16 12 24 12 C28 12 30 14 32 18 C34 14 36 12 40 12 C48 12 56 18 56 28 C56 42 42 50 32 58 Z", GOLD),
              facet_gem(ic, 32, 32, 7, P["ruby"])]
    elif kind == "wing":
        s += [shape(ic, "M32 20 C24 10 12 8 6 14 C12 18 10 24 16 26 C12 30 14 36 20 36 C22 42 28 42 32 38 Z", GOLD),
              shape(ic, "M32 20 C40 10 52 8 58 14 C52 18 54 24 48 26 C52 30 50 36 44 36 C42 42 36 42 32 38 Z", GOLD),
              rect(ic, 24, 36, 16, 20, C("#fffaf0", "#f0e6d0", "#b8a888", "#4a3e2a"), 2), line("M28 42 L36 42 M28 47 L36 47 M28 52 L34 52", "#8a5716", 1.4)]
    elif kind == "axe":
        s += [rect(ic, 29, 12, 6, 46, GOLD, 2), shape(ic, "M34 12 C46 10 56 18 56 30 C48 28 40 30 34 34 Z", GOLD),
              shape(ic, "M30 12 C18 10 8 18 8 30 C16 28 24 30 30 34 Z", GOLD), facet_gem(ic, 32, 10, 5, P["ruby"])]
    elif kind == "coins":
        for x, y in [(20, 46), (44, 46), (32, 44), (26, 36), (38, 36), (32, 28), (32, 20)]:
            s.append(ell(ic, x, y, 10, 4, GOLD, sw=1.8))
        s.append(sparkle(48, 16, 6, "#fff6d2"))
    elif kind == "hound":
        s += [shape(ic, "M10 56 L14 36 C14 28 18 22 24 18 L22 8 L30 14 L40 14 C46 14 50 18 52 24 L58 26 L54 32 L46 32 C44 40 44 48 46 56 L38 56 L36 42 L22 44 L20 56 Z", GOLD),
              dot(42, 21, 1.8, INK)]
    elif kind == "flame":
        s += [shape(ic, "M32 6 C40 18 52 24 50 40 C48 52 40 58 32 58 C24 58 16 52 14 40 C14 30 22 26 24 16 C28 22 30 26 30 30 C34 22 34 14 32 6 Z", GOLD),
              shape(ic, "M32 34 C38 40 40 46 36 52 C32 56 26 52 28 46 C28 42 32 40 32 34 Z", P["fire"], sw=1.4)]
    elif kind == "shield":
        s += [shape(ic, "M32 6 L54 14 C54 34 46 50 32 58 C18 50 10 34 10 14 Z", GOLD), shape(ic, "M32 14 L46 19 C46 32 40 44 32 50 C24 44 18 32 18 19 Z", C("#8ab8ff", "#3a6ae0", "#1a2a8a", "#08103a"), sw=1.6)]
    s.append(hl("M16 18 C18 14 22 12 26 11", 2.2))
    return J(s)


# ----------------------------------------------------------------------------- valuables, events, others
def pouch(ic, size):
    pal = C("#d8d0a0", "#8e8a5a", "#4a4a2a", "#1a1a0a")
    k = {"Small Pouch": 0.8, "Pouch": 0.9, "Big Pouch": 1.0}[size]
    s = [f'<g transform="translate(32 60) scale({k}) translate(-32 -60)">',
         shape(ic, "M18 24 C10 32 8 44 12 52 C16 58 48 58 52 52 C56 44 54 32 46 24 Z", pal, ic.rg(pal, 0.4, 0.4, 0.8)),
         shape(ic, "M20 12 L26 18 L32 12 L38 18 L44 12 L46 24 L18 24 Z", pal), rect(ic, 16, 22, 32, 5, P["crimson"], 2, sw=1.4)]
    if size != "Small Pouch":
        s.append(ell(ic, 32, 42, 7, 7, P["gold"], sw=1.6))
    if size == "Big Pouch":
        s += [ell(ic, 20, 48, 5, 5, P["gold"], sw=1.4), ell(ic, 44, 48, 5, 5, P["gold"], sw=1.4)]
    s += [hl("M16 38 C17 33 19 30 22 28", 2.4), "</g>"]
    return J(s)


def gift(ic, box, ribbon):
    return J([rect(ic, 10, 28, 44, 28, box, 2), rect(ic, 8, 20, 48, 10, box, 2), rect(ic, 28, 20, 8, 36, ribbon, 1, sw=1.4),
                    shape(ic, "M32 20 C24 10 14 12 18 20 Z", ribbon, sw=1.6), shape(ic, "M32 20 C40 10 50 12 46 20 Z", ribbon, sw=1.6),
                    hl("M13 32 L13 50", 2)])


def pearl(ic):
    return J([circle(ic, 32, 32, 18, C("#ffffff", "#f4ecdc", "#bcae96", "#3a3226")), dot(26, 26, 5, HL, 0.9)])


def oyster(ic):
    shell = C("#e8d8c8", "#a88e7a", "#5e4a3e", "#221a14")
    return J([shape(ic, "M6 38 C8 24 22 16 36 18 C50 20 58 30 58 38 C48 44 18 44 6 38 Z", shell, ic.lg(shell)),
                    shape(ic, "M6 38 C18 44 48 44 58 38 C56 48 44 54 32 54 C20 54 8 48 6 38 Z", shell, ic.lg(shell, 0, 1, 1, 0)),
                    line("M14 30 L24 38 M26 22 L30 38 M40 22 L38 38 M50 28 L46 38", "#5e4a3e", 1.4, 0.8)])


def shell(ic):
    pal = C("#ffe6e0", "#f0a8a0", "#a85a5a", "#3a1414")
    return J([shape(ic, "M32 56 C18 50 8 36 10 20 C18 10 46 10 54 20 C56 36 46 50 32 56 Z", pal, ic.lg(pal, 0.1, 0, 0.9, 1)),
                    line("M32 54 L18 16 M32 54 L26 13 M32 54 L32 12 M32 54 L38 13 M32 54 L46 16", "#a85a5a", 1.6),
                    rect(ic, 26, 52, 12, 6, pal, 2, sw=1.6)])


def easter_egg(ic):
    pal = P["violet"]
    return J([shape(ic, "M32 6 C44 6 52 24 52 38 C52 50 44 58 32 58 C20 58 12 50 12 38 C12 24 20 6 32 6 Z", pal, ic.lg(pal, 0.1, 0, 0.9, 1)),
                    line("M14 30 C22 26 26 34 32 30 C38 26 42 34 50 30", "#ffd23a", 2.4), line("M13 42 L51 42", "#8ff0c0", 2.4),
                    hl("M20 22 C22 16 25 12 28 11", 2.4)])


def heart_box(ic):
    pal = P["pink"]
    return J([shape(ic, "M32 58 C22 50 6 40 6 26 C6 16 14 10 22 10 C27 10 30 13 32 16 C34 13 37 10 42 10 C50 10 58 16 58 26 C58 40 42 50 32 58 Z", pal, ic.lg(pal, 0.1, 0, 0.9, 1)),
                    line("M8 30 C18 34 46 34 56 30", "#a8387a", 1.8), shape(ic, "M32 16 C28 8 20 8 22 14 Z", P["red"], sw=1.2),
                    hl("M12 22 C13 18 16 15 20 14", 2.4)])


def fossil(ic, kind):
    s = [shape(ic, "M8 34 C6 22 16 10 30 10 C46 8 58 20 56 34 C56 48 44 56 30 56 C16 56 10 46 8 34 Z", STONE, ic.lg(STONE, 0.1, 0, 0.9, 1))]
    ink = "#5a3a30"
    if kind == "Fossil":
        s.append(line("M32 32 C34 30 36 32 34 35 C31 38 26 34 28 29 C31 23 40 25 40 33 C40 42 28 45 23 38 C17 29 24 18 34 19 C44 20 49 29 47 37", ink, 2.4))
    elif kind == "Flora Fossil":
        s.append(line("M18 48 L44 18 M24 42 L20 32 M28 37 L24 26 M33 31 L30 20 M26 44 L36 44 M31 38 L41 38 M36 32 L46 32", ink, 2.2))
    else:
        s.append(line("M14 34 L20 28 L20 40 Z M20 34 C26 26 40 26 48 34 C40 42 26 42 20 34 M26 28 L28 40 M32 27 L34 41 M38 28 L40 40", ink, 2))
        s.append(dot(44, 32, 1.6, ink))
    s.append(hl("M14 26 C16 20 20 16 26 14", 2.2))
    return J(s)


def ticket(ic):
    pal = C("#fffaf0", "#f0e0c0", "#b8a07a", "#3a2c16")
    return J([shape(ic, "M6 18 L58 18 L58 28 C54 28 54 36 58 36 L58 46 L6 46 L6 36 C10 36 10 28 6 28 Z", pal, ic.lg(pal)),
                    line("M44 20 L44 44", "#b8a07a", 1.6), rect(ic, 12, 24, 26, 16, P["crimson"], 1.5, sw=1.2),
                    line("M17 29 L33 29 M17 35 L29 35", "#ffe6a0", 1.8)])


def rune(ic):
    pal = C("#6a5a7a", "#34283e", "#1a1420", "#08060a")
    return J([shape(ic, "M32 4 L54 16 L56 44 L32 60 L8 44 L10 16 Z", pal, ic.lg(pal, 0.1, 0, 0.9, 1)),
                    line("M32 16 L32 44 M22 34 L32 44 L42 34", "#ff5a4a", 3.2), hl("M14 18 L30 9", 2)])


def present(ic):
    return gift(ic, P["sapphire"], P["orange"])


# ----------------------------------------------------------------------------- specs
SPECS = {
    # potions (the rest follow their name: size + effect)
    "Love Potion": love_potion, "Pig Perfume": pig_perfume, "Blood Potion": blood_potion, "Beast Vial": beast_vial, "Forget Me Now": forget_me_now,
    # food
    "Acorn": acorn, "Apple": apple, "Apple with worm": lambda ic: apple(ic, worm=True), "Baguette": baguette,
    "Berry Pie": lambda ic: pie_slice(ic, P["violet"]), "Cheese": cheese, "Cherry": cherry, "Chocolate Bunny": chocolate_bunny,
    "Coconut Drink": coconut_drink, "Crispy Seaweed": crispy_seaweed, "Durum": durum, "Gingerbread": gingerbread,
    "Halloween Candy": candy, "Honeycomb": honeycomb, "Honeyjar": honeyjar, "Jam": lambda ic: jar(ic, P["red"], label=True, lid=P["crimson"]),
    "Pickle": pickle, "Potato": potato, "Pumpkin": pumpkin, "Pumpkin Pie": lambda ic: pie_slice(ic, P["orange"], cream=True),
    "Ribs": ribs, "Roast Potato": lambda ic: potato(ic, roast=True), "Sandwich": sandwich, "Sardine Tin": sardine_tin,
    "Sausages": sausages, "Strawberry": strawberry, "Super Berry": super_berry, "Super Shroom": super_shroom, "Tomato": tomato, "Wine": wine,
    # fruit
    "Black Berries": lambda ic: berries(ic, DARK), "Cursed Cherry": lambda ic: cherry(ic, DARK, cursed=True),
    "Green Berries": lambda ic: berries(ic, LIME), "Pink Berries": lambda ic: berries(ic, P["magenta"]), "Red Berries": lambda ic: berries(ic, P["crimson"]),
    "Soulfruit": soulfruit, "Spotted Berries": lambda ic: berries(ic, P["amethyst"], spots="#ffd6ff"),
    "Strange Fruit": lambda ic: berries(ic, C("#4a5a6a", "#1e2a36", "#0e141c", "#040608"), glow="#6af0ff"),
    "Underwater Berries": lambda ic: berries(ic, P["sapphire"]), "White Berries": lambda ic: berries(ic, P["white"]),
    "Yellow Berries": lambda ic: berries(ic, P["yellow"]),
    # mushrooms
    "Cave Coral": cave_coral, "Cheddar Shroom": lambda ic: mushroom(ic, P["yellow"], kind="bell"),
    "Dreamspore": lambda ic: mushroom(ic, P["cream"], C("#d0f7a0", "#5cc24a", "#28782c", "#0c2c10"), kind="wavy"),
    "Glittercap": lambda ic: mushroom(ic, C("#ffb08a", "#c8503a", "#6e2014", "#2a0804"), spots="#ffe6a0"),
    "Glowshroom": lambda ic: mushroom(ic, C("#ffffc0", "#ffe23a", "#c89010", "#3c2404"), kind="wavy") + sparkle(52, 10, 5, "#fff6a8"),
    "Icy Truffle": lambda ic: mushroom(ic, P["ice"], C("#ffe0c0", "#e8a878", "#a8683e", "#3a1c0a"), spots="#ffffff"),
    "Inferno Fungus": lambda ic: mushroom(ic, P["magenta"], P["sapphire"], spots="#ffb0e0", kind="flat"),
    "Meadow Mushroom": lambda ic: mushroom(ic, C("#f8e0c8", "#c89a7a", "#7a5440", "#2a1a10"), kind="flat"),
    "Nightshade Shroom": lambda ic: mushroom(ic, C("#8a92a0", "#3a4250", "#1c222c", "#080a10"), DARK, spots="#6a7484"),
    "Rift Mushroom": lambda ic: cluster(ic, C("#8a9ab0", "#3e4a5e", "#1e2430", "#080a10"), spots="#e2343e"),
    "Tunnel Mushroom": lambda ic: cluster(ic, C("#a0c0c0", "#4a6a6e", "#223436", "#0a1414"), spots="#c6fff4"),
    "Underwater Trumpet": trumpet,
    # plants
    "Bloodrose": bloodrose, "Bluebell": bluebell, "Death Nut": death_nut, "Frost Thistle": frost_thistle, "Honeydew": honeydew,
    "Ice Lotus": ice_lotus, "Liana": liana, "Rockplum": rockplum, "Root": root, "Seaweed": seaweed, "Starzest": starzest,
    "Sunburst Petal": sunburst_petal, "Sunflower": sunflower,
    # ores, ingots
    "Coal": coal, "Copper ore": lambda ic: ore(ic, P["copper"]), "Iron ore": lambda ic: ore(ic, P["slate"], "#e8dcc8"),
    "Silver ore": lambda ic: ore(ic, P["silver"]), "Gold ore": lambda ic: ore(ic, STONE, "#ffd23a"),
    "Platinum ore": lambda ic: ore(ic, P["slate"], "#8ff0d8"), "Azurite ore": lambda ic: ore(ic, P["azurite"]),
    "Purpurite ore": lambda ic: ore(ic, P["purpurite"]),
    "Copper ingot": lambda ic: ingot(ic, P["copper"]), "Iron ingot": lambda ic: ingot(ic, P["slate"]), "Silver ingot": lambda ic: ingot(ic, P["silver"]),
    "Gold ingot": lambda ic: ingot(ic, P["gold"]), "Platinum ingot": lambda ic: ingot(ic, C("#ffffff", "#bfeee0", "#5a9a8a", "#16302a")),
    "Azurite ingot": lambda ic: ingot(ic, P["azurite"]), "Purpurite ingot": lambda ic: ingot(ic, P["purpurite"]),
    # keys
    "Copper Key": lambda ic: key(ic, P["copper"]), "Iron Key": lambda ic: key(ic, P["slate"]), "Silver Key": lambda ic: key(ic, P["silver"]),
    "Gold Key": lambda ic: key(ic, P["gold"]), "Fancy Key": lambda ic: key(ic, P["orange"], "ornate"),
    "Relic Key": lambda ic: key(ic, GOLD, "ornate", P["ruby"]), "Monster Key": lambda ic: key(ic, P["plum"], "spiky"),
    # materials
    "Bat Wing": bat_wing, "Branch": branch, "Butterfly Wing": butterfly_wing, "Chain": chain, "Emberfruit": emberfruit,
    "Emerald": emerald, "Gold Nugget": lambda ic: nugget(ic, P["gold"]), "Silver Nugget": lambda ic: nugget(ic, P["silver"]),
    "Nail": nail, "Resonance Powder": powder,
    # monster drops
    "Bone": bone, "Golden Bone": lambda ic: bone(ic, P["gold"]), "Tooth": tooth, "Fang": lambda ic: tooth(ic, curve=True),
    "Claw": claw, "Tail": tail, "Tentacle": tentacle, "Eyeball": eyeball, "Slime": slime, "Purple Sludge": sludge, "Icicle": icicle,
    "Wyvern Sting": sting, "Skull": monster_skull,
    "Brown Hide": lambda ic: hide(ic, BROWN), "Cyclops Hide": lambda ic: hide(ic, C("#f0c890", "#c08a4a", "#7a5226", "#2e1c0a"), "eye"),
    "Forest Horror Hide": lambda ic: hide(ic, C("#d88080", "#8a3030", "#4a1414", "#1a0404")),
    "Half Dead Hide": lambda ic: hide(ic, C("#b8b08a", "#6e684a", "#3a3622", "#14120a"), "stitch"),
    "Lava Eater Hide": lambda ic: hide(ic, C("#c86a3a", "#7a2e14", "#401406", "#180602"), "stripes"),
    "Minotaur Hide": lambda ic: hide(ic, C("#e0a060", "#a0602a", "#5a300e", "#200e02"), "spots"),
    "Snake Skin": lambda ic: hide(ic, C("#8a8298", "#4a4258", "#24202e", "#0a080e"), scales=True),
    # relics
    "Chalice of Abundance": lambda ic: relic(ic, "chalice"), "Lamp of Seeking": lambda ic: relic(ic, "lamp"),
    "Colossus Heart": lambda ic: relic(ic, "heart"), "Courier's Testament": lambda ic: relic(ic, "wing"),
    "Executioner's Verdict": lambda ic: relic(ic, "axe"), "Fools Fortune": lambda ic: relic(ic, "coins"),
    "Huntsman's Mark": lambda ic: relic(ic, "hound"), "Inferno's Wrath": lambda ic: relic(ic, "flame"),
    "Warden's Oath": lambda ic: relic(ic, "shield"),
    # valuables, events, fossils, resources
    "Small Pouch": lambda ic: pouch(ic, "Small Pouch"), "Pouch": lambda ic: pouch(ic, "Pouch"), "Big Pouch": lambda ic: pouch(ic, "Big Pouch"),
    "Food Gift": lambda ic: gift(ic, P["leaf"], P["orange"]), "Monsterdrop Gift": lambda ic: gift(ic, P["orange"], P["sapphire"]),
    "Ore Gift": lambda ic: gift(ic, P["sapphire"], P["pink"]), "Potion Gift": lambda ic: gift(ic, P["crimson"], P["white"]),
    "Pearl": pearl, "Shut Oyster": oyster,
    "Christmas Present": lambda ic: gift(ic, P["red"], P["leaf"]), "Easter Egg": easter_egg, "Heart Shaped Box": heart_box,
    "Jack-o'-Lantern": lambda ic: pumpkin(ic, face=True), "Shell": shell,
    "Fossil": lambda ic: fossil(ic, "Fossil"), "Flora Fossil": lambda ic: fossil(ic, "Flora Fossil"), "Fish Fossil": lambda ic: fossil(ic, "Fish Fossil"),
    "Coliseum Ticket": ticket, "Tower Revert Rune": rune,
}


def main() -> None:
    force = "--force" in sys.argv
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    data = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    written, kept, missing = 0, 0, []
    for g in data.get("goods", []):
        name = g["name"]
        if only and name not in only:
            continue
        spec = SPECS.get(name) or (potion_spec(name) if g["type"] == "POTION" else skin_spec(name) if g["type"] == "SKIN" else None)
        if not spec:
            missing.append(name)
            continue
        path = OUT / f"i{g['id']}.svg"
        if path.exists() and not force and "generated" not in path.read_text(encoding="utf-8")[:200]:
            kept += 1
            continue
        ic = Icon()
        ic.add(spec(ic))
        path.write_text(ic.svg().replace("<svg ", '<svg data-generated="goods_icons.py" ', 1), encoding="utf-8")
        written += 1
    print(f"goods icons: wrote {written}, kept {kept} hand-edited, missing specs: {missing or 'none'}")


if __name__ == "__main__":
    main()
