#!/usr/bin/env python3
"""Draw the Library's icons (spells, talents, obols, books) as HD drawings -> icons/modern/l-<name>.svg

Our own drawings, made from a small symbol kit. The wiki's pictures were only looked at to learn what each
entry is about (see tools/ART_GUIDE.md); nothing from them is traced or kept.

- Spells: a rune tile in the spell's element colour (fire red, water teal, air blue, earth brown, plain
  violet) with the effect drawn big on it: a fireball, a snowflake, a lightning bolt...
- Talents: a rune tile in the colour of what it improves (attack red, defense amber, health crimson, mana
  blue, luck gold, speed green) with its symbol; "%" talents carry a small % badge and "Mastery" talents a gold
  up-arrow badge, so the families read at a glance.
- Obols: a coin in its material (iron, gold, emerald, ruby, opal, topaz, bismuth): round metal coins,
  eight-sided cut gems, stamped with the stat's symbol (sword, shield, heart, clover, mana drop, chevrons).
- Books: closed books, each with its own cover colour and emblem.

Usage: python tools/library_icons.py
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from modern_icons import HL, Icon, circle, dot, f, line, shape  # noqa: E402
from skin_icons import ramp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"
INK = "#141216"


# ----------------------------------------------------------------------------- basics
def part(ic, d, col, sw=1.8, grad=(0.2, 0, 0.8, 1), extra=""):
    R = ramp(col)
    return shape(ic, d, R, ic.lg(R, *grad), sw, extra)


def ball(ic, cx, cy, r, col, sw=1.8):
    return circle(ic, cx, cy, r, ramp(col), sw=sw)


def cord(d, col, w):
    """a thick stroke with its own dark rim (streaks, arcs, handles)"""
    R = ramp(col)
    return line(d, R[3], w + 3) + line(d, col, w)


def J(parts) -> str:
    if isinstance(parts, (list, tuple)):
        return "".join(J(p) for p in parts)
    return parts or ""


def at(parts, x, y, s=1.0, a=0):
    """place a symbol drawn around (0, 0) at (x, y), scaled and turned"""
    return f'<g transform="translate({f(x)} {f(y)}) rotate({f(a)}) scale({f(s)})">{J(parts)}</g>'


def poly(pts, s=1.0, x=0.0, y=0.0):
    return "M" + " L".join(f"{f(x + px * s)} {f(y + py * s)}" for px, py in pts) + " Z"


def star_pts(n, r1, r2, a0=-90):
    return [((r1 if k % 2 == 0 else r2) * math.cos(math.radians(a0 + k * 180 / n)),
             (r1 if k % 2 == 0 else r2) * math.sin(math.radians(a0 + k * 180 / n))) for k in range(2 * n)]


# ----------------------------------------------------------------------------- the rune tile
def tile(ic, col):
    """a rounded square in a deep colour, lit from the top left, with a soft glow behind the symbol"""
    R = ramp(col)
    return [shape(ic, "M11 4 H53 Q60 4 60 11 V53 Q60 60 53 60 H11 Q4 60 4 53 V11 Q4 4 11 4 Z", R, ic.lg((R[1], R[1], R[2]), 0, 0, 1, 1), 2),
            f'<circle cx="32" cy="31" r="20" fill="{R[1]}"/>']


def pct(ic):
    """the percentage badge, bottom right: a little pie chart with a quarter taken out"""
    return [circle(ic, 49, 49, 11, ramp("#f2e6c8"), sw=2),
            part(ic, "M49 49 L49 40 A9 9 0 1 1 40 49 Z", "#3aa0e8", 1.2)]


def mastery(ic):
    """the gold up-arrow badge of Mastery talents, bottom right"""
    return [circle(ic, 49, 49, 11, ramp("#3a2a5a"), sw=2),
            part(ic, "M49 40 L57 49 L52.5 49 L52.5 57 L45.5 57 L45.5 49 L41 49 Z", "#ffc83a", 1.4)]


# ----------------------------------------------------------------------------- symbols (drawn around 0,0, about 40 wide)
HEART = "M0 17 C-24 2 -22 -18 -10 -18 C-4 -18 -1 -14 0 -10 C1 -14 4 -18 10 -18 C22 -18 24 2 0 17 Z"
SHIELD = "M0 -19 L16 -13 C16 2 10 12 0 19 C-10 12 -16 2 -16 -13 Z"
DROP = "M0 -20 C4 -12 14 -4 14 5 C14 14 7 19 0 19 C-7 19 -14 14 -14 5 C-14 -4 -4 -12 0 -20 Z"


def heart(ic, col="#e8344a"):
    return [part(ic, HEART, col), line("M-12 -12 C-16 -10 -17 -6 -16 -2", HL, 2.4, 0.8)]


def shield(ic, col="#d08a2a", boss="#ffd23a"):
    return [part(ic, SHIELD, col),
            part(ic, "M0 -13 L10 -9 C10 1 6 8 0 13 Z", ramp(col)[0], 0),
            ball(ic, 0, -1, 4, boss, 1.4)]


def sword(ic, blade="#dfe6f0", hilt="#8a5a2a", guard="#ffc83a"):
    return [part(ic, "M-3 8 L-3 -18 L0 -23 L3 -18 L3 8 Z", blade, 1.6, (0, 0, 1, 0)),
            part(ic, "M-10 8 L10 8 L10 12 L-10 12 Z", guard, 1.6),
            part(ic, "M-2.5 12 L2.5 12 L2.5 20 L-2.5 20 Z", hilt, 1.4),
            ball(ic, 0, 22, 3, guard, 1.4)]


def drop(ic, col="#3aa8f0"):
    return [part(ic, DROP, col), line("M-7 3 C-8 8 -6 12 -3 14", HL, 2.4, 0.8)]


def flame(ic, col="#ff7a1a", core="#ffe27a"):
    return [part(ic, "M0 -22 C6 -14 16 -8 16 4 C16 14 9 20 0 20 C-9 20 -16 14 -16 4 C-16 -4 -11 -8 -8 -14 C-6 -8 -4 -6 -2 -6 C-4 -12 -3 -18 0 -22 Z", col),
            part(ic, "M0 -4 C4 1 8 5 8 10 C8 15 4 17 0 17 C-4 17 -8 15 -8 10 C-8 5 -4 1 0 -4 Z", core, 0)]


def bolt(ic, col="#ffe04a"):
    return [part(ic, poly([(-2, -22), (12, -22), (3, -5), (12, -5), (-8, 22), (-3, 2), (-12, 2)]), col, 1.8)]


def gust(ic, col="#bfe8ff"):
    return [cord("M-18 -8 H6 C14 -8 14 -18 7 -18 C2 -18 2 -12 6 -12", col, 4),
            cord("M-20 2 H12 C20 2 20 13 12 13 C7 13 7 8 11 8", col, 4),
            cord("M-14 12 H0", col, 4)]


def rock(ic, col="#a07850"):
    return [part(ic, poly([(-14, -6), (-6, -15), (8, -14), (16, -4), (13, 11), (0, 16), (-13, 10)]), col),
            line("M-4 -6 L2 0 L8 -2", ramp(col)[2], 2), dot(-7, 4, 1.8, ramp(col)[2])]


def crescent(ic, col="#e8f6ff"):
    return [part(ic, "M-14 -16 C4 -16 16 -4 14 16 C8 2 -2 -8 -14 -16 Z", col, 1.6)]


def skull(ic, col="#f2ead8"):
    return [part(ic, "M-13 -2 C-13 -14 -7 -18 0 -18 C7 -18 13 -14 13 -2 C13 4 10 6 8 7 L8 13 L-8 13 L-8 7 C-10 6 -13 4 -13 -2 Z", col),
            f'<ellipse cx="-5.5" cy="-2" rx="4" ry="4.4" fill="{INK}"/>', f'<ellipse cx="5.5" cy="-2" rx="4" ry="4.4" fill="{INK}"/>',
            f'<path d="M0 3 L2 7 L-2 7 Z" fill="{INK}"/>', line("M-3 10 L-3 13 M1 10 L1 13 M5 10 L5 13", INK, 1.4)]


def figure(ic, col):
    return [ball(ic, 0, -12, 7, col), part(ic, "M-14 18 C-14 4 -10 -2 0 -2 C10 -2 14 4 14 18 Z", col)]


def wing(ic, col="#f2f6ff"):
    return [part(ic, "M-16 12 C-16 -6 -4 -18 16 -20 C12 -14 14 -12 10 -8 C14 -8 12 -4 8 -2 C12 -1 10 4 4 5 C6 8 2 11 -4 11 Z", col),
            line("M-10 6 C-6 -2 0 -8 8 -12", ramp(col)[2], 1.6)]


def clover(ic, col="#4ac85a"):
    leaf = "M0 0 C-12 -4 -12 -17 -5 -17 C-2 -17 0 -14 0 -12 C0 -14 2 -17 5 -17 C12 -17 12 -4 0 0 Z"
    return [cord("M0 0 C2 8 4 12 9 18", "#3a8a3a", 2.4)] + \
           [f'<g transform="rotate({a})">{part(ic, leaf, col, 1.6)}</g>' for a in (-45, 45, 135, -135)] + [dot(0, 0, 2, ramp(col)[2])]


def orb(ic, col="#4ab8f0"):
    return [ball(ic, 0, 0, 16, col), f'<path d="M-9 -7 C-6 -12 0 -13 4 -11 C-1 -10 -5 -8 -9 -3 Z" fill="{HL}"/>', dot(7, 7, 2, ramp(col)[0])]


def die(ic, pips, col="#f4ecd8"):
    out = [part(ic, "M-11 -13 H11 Q13 -13 13 -11 V11 Q13 13 11 13 H-11 Q-13 13 -13 11 V-11 Q-13 -13 -11 -13 Z", col)]
    spots = {3: [(-6, -6), (0, 0), (6, 6)], 5: [(-6, -6), (6, -6), (0, 0), (-6, 6), (6, 6)]}
    return out + [dot(x, y, 2.4, INK) for x, y in spots[pips]]


def fist(ic, col="#f0b890"):
    return [part(ic, "M-12 -8 C-12 -14 -6 -16 -2 -14 C0 -18 6 -18 8 -14 C12 -16 16 -12 15 -6 L15 6 C15 14 10 18 2 18 C-8 18 -14 12 -14 4 Z", col),
            line("M-6 -12 L-6 -4 M2 -14 L2 -4 M9 -13 L9 -4", ramp(col)[2], 1.8),
            part(ic, "M-14 0 C-8 -4 -2 -2 0 2 C-4 6 -10 6 -14 4 Z", ramp(col)[0], 1.2)]


def chevrons(ic, col="#bff0a0"):
    return [part(ic, poly([(-18, -12), (-8, -12), (4, 0), (-8, 12), (-18, 12), (-6, 0)]), col, 1.6),
            part(ic, poly([(-2, -12), (8, -12), (20, 0), (8, 12), (-2, 12), (10, 0)]), col, 1.6)]


def arrow(ic, col="#e0e6f0", fletch="#e84a4a"):
    return [cord("M-18 18 L12 -12", "#b08050", 2.4),
            part(ic, poly([(8, -16), (20, -20), (16, -8)]), col, 1.4),
            part(ic, poly([(-18, 18), (-22, 12), (-14, 10), (-12, 14)]), fletch, 1.2)]


def coin(ic, cx, cy, col="#ffc83a", r=8):
    R = ramp(col)
    return [f'<ellipse cx="{f(cx)}" cy="{f(cy + 2)}" rx="{f(r)}" ry="{f(r * 0.5)}" fill="{R[2]}" stroke="{R[3]}" stroke-width="1.6"/>',
            f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(r)}" ry="{f(r * 0.5)}" fill="{ic.lg(R, 0, 0, 1, 1)}" stroke="{R[3]}" stroke-width="1.6"/>']


def burst(ic, col="#fff2a0", n=8, r1=20, r2=9):
    return [part(ic, poly(star_pts(n, r1, r2)), col, 1.6)]


def snowflake(ic, col="#e8faff"):
    arm_ = cord("M0 -20 L0 20 M-6 -16 L0 -11 L6 -16 M-6 16 L0 11 L6 16", col, 3)
    return [f'<g transform="rotate({a})">{arm_}</g>' for a in (0, 60, 120)] + [ball(ic, 0, 0, 4, col, 1.4)]


def eye(ic, col="#6ad0ff"):
    return [part(ic, "M-18 0 C-10 -12 10 -12 18 0 C10 12 -10 12 -18 0 Z", "#f8f4ec"),
            ball(ic, 0, 0, 7, col, 1.4), dot(0, 0, 3, INK), dot(-2.5, -2.5, 1.4, HL)]


def mirror(parts):
    return f'<g transform="scale(-1 1)">{J(parts)}</g>'


# ----------------------------------------------------------------------------- element and stat colours
TILE = {"FIRE": "#b8341c", "WATER": "#1c8a8a", "AIR": "#2a3eb8", "EARTH": "#8a5a28", "": "#6a38a8",
        "attack": "#b8301e", "defense": "#b8741c", "hp": "#a81e3a", "mana": "#1c6aa8", "luck": "#b8961c",
        "speed": "#2a8a44", "crit": "#c8501a", "grace": "#c8a040", "dark": "#3a3050", "hunt": "#6a4a24"}
ELEM = {"Fire": lambda ic: flame(ic), "Water": lambda ic: drop(ic, "#4ad8e8"),
        "Air": lambda ic: gust(ic), "Earth": lambda ic: rock(ic)}
ELEM_TILE = {"Fire": "FIRE", "Water": "WATER", "Air": "AIR", "Earth": "EARTH"}


# ----------------------------------------------------------------------------- spells
def phoenix(ic):
    w = "M0 -6 C-6 -10 -14 -20 -22 -20 C-18 -14 -18 -8 -12 -4 C-18 -4 -20 2 -16 4 C-10 4 -6 2 -3 0 Z"
    return [part(ic, w, "#ffb030"), mirror(part(ic, w, "#ffb030")),
            part(ic, "M0 -12 C5 -12 6 -6 4 0 L6 14 L0 22 L-6 14 L-4 0 C-6 -6 -5 -12 0 -12 Z", "#ff5a1a"),
            part(ic, "M0 -12 L5 -16 L3 -10 Z", "#ffd23a", 1.2), dot(-1.5, -8, 1.3, INK)]


def fairy(ic):
    up = "M-2 -6 C-12 -22 -24 -16 -18 -6 C-14 -2 -6 -2 -2 -4 Z"
    low = "M-2 0 C-10 4 -16 12 -10 14 C-6 14 -3 8 -1 4 Z"
    wc = "#c8f0ff"
    return [part(ic, up, wc, 1.4), mirror(part(ic, up, wc, 1.4)), part(ic, low, wc, 1.4), mirror(part(ic, low, wc, 1.4)),
            part(ic, "M0 -4 L6 14 L-6 14 Z", "#ff8ad0", 1.4), ball(ic, 0, -9, 5, "#ffe0c0", 1.4),
            dot(-15, 17, 1.8, "#fff6a0"), dot(16, 16, 1.8, "#fff6a0"), dot(-18, -20, 1.6, "#fff6a0")]


def dragon_head(ic):
    return [part(ic, "M-20 -4 C-20 -14 -12 -18 -4 -16 L-10 -24 L0 -18 C4 -16 6 -12 6 -8 L10 -6 L6 0 L10 2 L2 6 C-6 10 -14 10 -20 4 Z", "#c83a28"),
            part(ic, "M-4 -16 L-10 -24 L0 -18 Z", "#f0d8a0", 1.2), dot(-4, -9, 2.2, "#ffe24a"), dot(-4, -9, 0.9, INK)]


def up_arrow(ic, col="#ffd23a"):
    return [part(ic, poly([(0, -10), (7, -2), (3, -2), (3, 8), (-3, 8), (-3, -2), (-7, -2)]), col, 1.4)]


def spells():
    S = {}
    S["Air Shot"] = ("AIR", lambda ic: [cord("M-20 20 L-10 10 M-22 10 L-14 4 M-10 22 L-4 14", "#8ad0ff", 2.4),
                                        at(arrow(ic, "#f2f6ff", "#8ad0ff"), 2, -2, 1.1)])
    S["Air Slam"] = ("AIR", lambda ic: [cord("M-20 18 H20", "#f2e6c8", 3),
                                        part(ic, poly([(-8, -22), (8, -22), (8, 0), (16, 0), (0, 14), (-16, 0), (-8, 0)]), "#d8f0ff"),
                                        cord("M-18 10 L-24 6 M18 10 L24 6", "#bfe8ff", 2.4)])
    S["Catapult"] = ("EARTH", lambda ic: [cord("M-22 18 C-18 -4 -4 -16 10 -18", "#e8d0a0", 2.2),
                                          at(rock(ic, "#a88058"), 6, -4, 1.1)])
    S["Comet Shower"] = ("FIRE", lambda ic: [at([cord("M-10 -10 L2 2", "#ffb050", 4), ball(ic, 5, 5, 6, "#ffd23a", 1.4)], x, y, s)
                                             for x, y, s in ((-12, -12, 1.0), (8, -4, 1.3), (-6, 12, 1.0))])
    S["Defense Break"] = ("", lambda ic: [at(shield(ic, "#4ab8b0", "#e8f8f0"), 0, 0, 1.1),
                                          cord("M-4 -22 L2 -8 L-4 0 L4 10 L0 22", "#fff2c0", 2.6)])
    S["Double Strike"] = ("", lambda ic: [at(sword(ic), 0, 0, 1.05, -35), at(sword(ic, "#fff4d8"), 0, 0, 1.05, 35)])
    S["Dragon's Breath"] = ("FIRE", lambda ic: [at(flame(ic, "#ff8a1a"), 12, 6, 0.75, 70), at(dragon_head(ic), -6, 2, 0.9)])
    S["Fairy's Blessing"] = ("AIR", lambda ic: [at(fairy(ic), 0, 0, 1.1)])
    S["Fire Ball"] = ("FIRE", lambda ic: [at(flame(ic, "#ff8a1a"), 4, -4, 1.0, 45), ball(ic, -3, 3, 10, "#ffcc3a")])
    S["Fire Flash"] = ("FIRE", lambda ic: [at(burst(ic, "#ffe08a", 8, 22, 10), 0, 0, 1), at(eye(ic, "#ff6a2a"), 0, 0, 0.7)])
    S["Freeze"] = ("WATER", lambda ic: [at(snowflake(ic), 0, 0, 1.05)])
    S["Ice Fort"] = ("WATER", lambda ic: [part(ic, "M-16 20 L-16 -16 L-10 -16 L-10 -10 L-3 -10 L-3 -16 L3 -16 L3 -10 L10 -10 L10 -16 L16 -16 L16 20 Z", "#a8e8f0"),
                                          part(ic, "M-5 20 L-5 8 C-5 2 5 2 5 8 L5 20 Z", "#1c5a6a", 1.4),
                                          line("M-12 -4 L-12 10", HL, 2, 0.7)])
    S["Ice Shock"] = ("WATER", lambda ic: [part(ic, poly([(0, -22), (10, -4), (0, 20), (-10, -4)]), "#b0f0f8"),
                                           line("M0 -22 L0 20", ramp("#b0f0f8")[2], 1.4),
                                           at(bolt(ic, "#ffe04a"), 10, 6, 0.55)])
    S["Ice Shot"] = ("WATER", lambda ic: [cord("M-22 18 L-12 8 M-20 6 L-14 2 M-8 20 L-4 14", "#9ae0f0", 2.2),
                                          at([part(ic, poly([(0, -22), (6, -6), (0, 14), (-6, -6)]), "#c8f6ff"),
                                              line("M0 -18 L0 10", HL, 1.6, 0.8)], 4, -4, 1.0, 45)])
    S["Lightning Strike"] = ("AIR", lambda ic: [at(bolt(ic), 0, 0, 1.1)])
    S["Phoenix"] = ("FIRE", lambda ic: [at(phoenix(ic), 0, 0, 1.05)])
    S["Quicksand"] = ("EARTH", lambda ic: [ball(ic, 0, 0, 20, "#e8c888"),
                                           cord("M0 0 C4 -2 4 -8 -2 -8 C-10 -8 -12 2 -6 8 C2 14 14 8 14 -2 C14 -14 2 -20 -10 -16", "#8a5a28", 3)])
    S["Rock Volley"] = ("EARTH", lambda ic: [at(rock(ic, "#b08860"), x, y, s) for x, y, s in ((-10, -10, 0.55), (10, -6, 0.6), (-2, 10, 0.7))])
    S["Strength Buff"] = ("", lambda ic: [at(sword(ic, "#f0e8ff"), 6, 0, 1.0), at(up_arrow(ic), -11, -8, 1.2)])
    S["Water Slash"] = ("WATER", lambda ic: [part(ic, "M-20 16 C-20 -6 -4 -20 14 -18 C22 -16 22 -6 14 -6 C8 -6 8 -12 12 -12 C0 -12 -10 0 -8 16 Z", "#8ae8f0"),
                                             line("M-14 10 C-14 -4 -6 -12 4 -14", HL, 2, 0.7)])
    S["Wind Slash"] = ("AIR", lambda ic: [at(crescent(ic, "#e8f8ff"), -7, -3, 1.25), at(crescent(ic, "#9ad0ff"), 9, 5, 1.1)])
    return S


# ----------------------------------------------------------------------------- talents
def talents():
    T = {}
    E = ELEM
    T["Agility"] = ("speed", lambda ic: [at(wing(ic), 2, 0, 1.1)], None)
    T["Agility Mastery"] = ("speed", lambda ic: [at(wing(ic), -2, -3, 0.95)], mastery)
    for el in ("Air", "Earth", "Fire", "Water"):
        T[f"{el} Attack"] = (ELEM_TILE[el], (lambda e: lambda ic: [at(E[e](ic), -5, -4, 0.85), at(sword(ic), 8, 6, 0.7, 35)])(el), None)
        T[f"{el} Resistance"] = (ELEM_TILE[el], (lambda e: lambda ic: [at(shield(ic, "#c8ccd8", "#c8ccd8"), 0, 0, 1.15), at(E[e](ic), 0, -1, 0.55)])(el), None)
    T["Angels Dare"] = ("grace", lambda ic: [at(wing(ic, "#fffaf0"), -9, 4, 0.8), at(mirror(wing(ic, "#fffaf0")), 9, 4, 0.8),
                                             '<ellipse cx="0" cy="-14" rx="10" ry="3.6" fill="none" stroke="#3a2a06" stroke-width="5"/>',
                                             '<ellipse cx="0" cy="-14" rx="10" ry="3.6" fill="none" stroke="#ffe24a" stroke-width="2.6"/>'], None)
    horn = "M-14 -12 C-24 -14 -26 -24 -22 -28 C-20 -22 -16 -20 -10 -18 Z"
    T["Berserk"] = ("attack", lambda ic: [part(ic, horn, "#f4ecd8", 1.4), mirror(part(ic, horn, "#f4ecd8", 1.4)),
                                          part(ic, "M-16 8 C-16 -10 -8 -18 0 -18 C8 -18 16 -10 16 8 Z", "#a8b0c0"),
                                          part(ic, "M-16 6 H16 V12 H-16 Z", "#8a5a2a", 1.4), part(ic, "M-2 -18 H2 V6 H-2 Z", "#d8c060", 1.2),
                                          '<rect x="-11" y="-4" width="7" height="3" fill="#ff3a2a"/>', '<rect x="4" y="-4" width="7" height="3" fill="#ff3a2a"/>'], None)
    T["Bleed Damage"] = ("attack", lambda ic: [at(sword(ic, "#e8ecf4"), -2, -2, 0.95, 40),
                                               at(drop(ic, "#e02a3a"), -12, 12, 0.3), at(drop(ic, "#e02a3a"), -4, 18, 0.25), at(drop(ic, "#e02a3a"), 12, 12, 0.35)], None)
    T["Coin Greed"] = ("attack", lambda ic: [coin(ic, -6, 12, r=11), coin(ic, -6, 6, r=11), coin(ic, -6, 0, r=11), coin(ic, 8, 12, r=10), coin(ic, 8, 6, r=10),
                                             at(up_arrow(ic, "#ff5a3a"), 10, -12, 1.0)], None)
    T["Critical Chance"] = ("crit", lambda ic: ['<circle cx="0" cy="0" r="15" fill="none" stroke="#2a0a04" stroke-width="7"/>',
                                                '<circle cx="0" cy="0" r="15" fill="none" stroke="#ffe0b0" stroke-width="3.4"/>',
                                                cord("M0 -22 V-10 M0 10 V22 M-22 0 H-10 M10 0 H22", "#ffe0b0", 3), ball(ic, 0, 0, 5, "#ff4a2a", 1.4)], None)
    T["Critical Damage"] = ("crit", lambda ic: [at(burst(ic, "#ffd84a", 7, 20, 9), 4, 4, 1), at(sword(ic), -4, -4, 0.8, -45)], None)
    T["Critical Evade"] = ("crit", lambda ic: [at(shield(ic, "#e05a3a", "#ffe08a"), 0, 0, 1.1),
                                               at(burst(ic, "#fff2c0", 5, 7, 3), -16, -16, 1), at(burst(ic, "#fff2c0", 5, 6, 2.6), 17, 14, 1)], None)
    T["Damage Per Kill"] = ("dark", lambda ic: [at(skull(ic), -9, 8, 0.6), at(skull(ic), 9, 8, 0.6), at(skull(ic), 0, -7, 0.7)], None)
    T["Deal with the reaper"] = ("dark", lambda ic: [part(ic, "M-20 20 C-20 -6 -12 -22 0 -22 C12 -22 20 -6 20 20 Z", "#8a5ad8"), at(skull(ic), 0, 2, 0.75)], None)
    T["Defense"] = ("defense", lambda ic: [at(shield(ic, "#e08a2a"), 0, 0, 1.15)], None)
    T["Defense Expertise"] = ("defense", lambda ic: [at(shield(ic, "#e08a2a"), -2, -2, 1.0)], pct)
    T["Defense Mastery"] = ("defense", lambda ic: [at(shield(ic, "#e08a2a"), -2, -2, 1.0)], mastery)
    T["First Strike"] = ("attack", lambda ic: [cord("M-20 -10 L-10 -10 M-22 -2 L-8 -2 M-20 6 L-12 6", "#ffd0a0", 2.2), at(sword(ic), 6, 0, 1.0, 90)], None)
    T["Globetrotter"] = ("speed", lambda ic: [at(globe(ic), 0, 0, 1.05),
                                              '<ellipse cx="0" cy="0" rx="8" ry="18" fill="none" stroke="#1a4a7a" stroke-width="1.4"/>'], None)
    T["HP"] = ("hp", lambda ic: [at(heart(ic), 0, 0, 1.1)], None)
    T["HP %"] = ("hp", lambda ic: [at(heart(ic), -2, -3, 0.95)], pct)
    T["HP Mastery"] = ("hp", lambda ic: [at(heart(ic), -2, -3, 0.95)], mastery)
    T["Help from a friend"] = ("hp", lambda ic: [at(figure(ic, "#e8c8a0"), -9, 2, 0.8), at(figure(ic, "#f0d8b8"), 9, 2, 0.8),
                                                 at(heart(ic, "#ff5a6a"), 0, -17, 0.5)], None)
    T["Hunter's Concentration"] = ("hunt", lambda ic: [at(drop(ic, "#4ab8f0"), 0, 0, 1.0), at(arrow(ic), 0, 0, 0.9)], None)
    T["Hunter's Heart"] = ("hunt", lambda ic: [at(heart(ic), 0, 0, 1.0), at(arrow(ic), 0, 0, 0.95)], None)
    T["Hunter's Instinct"] = ("hunt", lambda ic: [ball(ic, 0, 6, 9, "#f4e0b8"), ball(ic, -12, -4, 4.5, "#f4e0b8", 1.4), ball(ic, -5, -13, 4.5, "#f4e0b8", 1.4),
                                                  ball(ic, 5, -13, 4.5, "#f4e0b8", 1.4), ball(ic, 12, -4, 4.5, "#f4e0b8", 1.4)], None)
    fang = "M-3 0 C-3 8 0 14 2 16 C4 10 4 4 3 0 Z"
    T["Hunter's Necklace"] = ("hunt", lambda ic: [cord("M-20 -20 C-16 2 16 2 20 -20", "#c8783a", 3.4)] +
                              [at(part(ic, fang, "#f4ecd8", 1.4), x, y, 1.5, a) for x, y, a in ((-11, -6, 25), (0, -2, 0), (11, -6, -25))], None)
    T["Hunter's Reflexes"] = ("hunt", lambda ic: [at(wing(ic, "#e8f0ff"), 0, 0, 1.0), at(arrow(ic), 0, 2, 0.85)], None)
    T["Hunter's Tenacity"] = ("hunt", lambda ic: [at(shield(ic, "#c8ccd8", "#c8ccd8"), 0, 0, 1.15), at(drop(ic, "#e02a3a"), 0, -1, 0.5)], None)
    T["Hunter's Wrath"] = ("hunt", lambda ic: [part(ic, "M-20 -8 C-10 -16 10 -16 20 -8 L20 8 C10 16 -10 16 -20 8 Z", "#5a1a14")] +
                           [part(ic, poly([(x - 4, -12), (x + 4, -12), (x, -1)]), "#f8f0dc", 1.2) for x in (-12, -4, 4, 12)] +
                           [part(ic, poly([(x - 4, 12), (x + 4, 12), (x, 2)]), "#f8f0dc", 1.2) for x in (-8, 0, 8)], None)
    T["Luck"] = ("luck", lambda ic: [at(clover(ic), 0, -2, 1.05)], None)
    T["Mana"] = ("mana", lambda ic: [at(orb(ic), 0, 0, 1.1)], None)
    T["Mana %"] = ("mana", lambda ic: [at(orb(ic), -2, -3, 0.95)], pct)
    T["Mana Regen"] = ("mana", lambda ic: [at(orb(ic), -3, 2, 0.85), ball(ic, 12, -10, 4, "#8ae0ff", 1.2), ball(ic, 16, -18, 2.6, "#8ae0ff", 1.2), ball(ic, 6, -18, 2, "#8ae0ff", 1.2)], None)
    T["Meditation Reward"] = ("mana", lambda ic: [part(ic, "M-20 18 C-20 10 -12 8 -8 6 L-8 -2 C-8 -6 8 -6 8 -2 L8 6 C12 8 20 10 20 18 Z", "#e8d8c0"),
                                                  ball(ic, 0, -12, 6.5, "#e8d8c0"),
                                                  '<circle cx="0" cy="-12" r="11" fill="none" stroke="#ffe24a" stroke-width="2"/>'], None)
    T["Number of Dice"] = ("luck", lambda ic: [at(die(ic, 5), -6, -6, 0.85, -10), at(die(ic, 3), 9, 9, 0.75, 12)], None)
    T["Parallel Casting"] = ("", lambda ic: [ball(ic, -8, 2, 9, "#ff7a3a"), ball(ic, 8, -2, 9, "#4ac8f0"),
                                             at(burst(ic, "#fff6c0", 4, 8, 3), 0, 0, 1), at(burst(ic, "#fff6c0", 4, 5, 2), -14, -14, 1), at(burst(ic, "#fff6c0", 4, 5, 2), 14, 14, 1)], None)
    T["Pride"] = ("luck", lambda ic: [cord("M-12 -14 C-20 -14 -20 -2 -10 -2 M12 -14 C20 -14 20 -2 10 -2", "#ffcc3a", 2.6),
                                      part(ic, "M-12 -18 H12 V-6 C12 4 6 8 0 8 C-6 8 -12 4 -12 -6 Z", "#ffcc3a"),
                                      part(ic, "M-3 8 H3 V14 H-3 Z", "#d89a1a", 1.2), part(ic, "M-10 14 H10 V20 H-10 Z", "#8a5a2a", 1.4),
                                      line("M-7 -14 C-8 -8 -7 -2 -4 2", HL, 2, 0.7)], None)
    T["Strength"] = ("attack", lambda ic: [at(dumbbell(ic), 0, 0, 1.0, -30)], None)
    T["Strength Mastery"] = ("attack", lambda ic: [at(dumbbell(ic), -3, -4, 0.85, -30)], mastery)
    T["Toadsskin"] = ("speed", lambda ic: [part(ic, "M-20 10 C-20 -4 -12 -10 0 -10 C12 -10 20 -4 20 10 C12 14 -12 14 -20 10 Z", "#8ac83a"),
                                           ball(ic, -9, -12, 6, "#8ac83a"), ball(ic, 9, -12, 6, "#8ac83a"),
                                           dot(-9, -12, 2.8, INK), dot(9, -12, 2.8, INK), dot(-10, -13, 1, HL), dot(8, -13, 1, HL),
                                           line("M-10 4 C-4 8 4 8 10 4", "#2a4a0a", 1.8), dot(-12, 0, 1.4, "#d8a02a"), dot(13, -1, 1.2, "#d8a02a")], None)
    T["Willpower"] = ("grace", lambda ic: [at(fist(ic), 0, 0, 1.05)], None)
    T["Willpower Mastery"] = ("grace", lambda ic: [at(fist(ic), -2, -3, 0.9)], mastery)
    return T


# ----------------------------------------------------------------------------- obols
METAL = {"iron": "#9aa4b4", "gold": "#f2c030"}
GEMS = {"emerald": "#2ec060", "ruby": "#e0283c", "opal": "#3a5af0", "topaz": "#ff9a1a"}
STAT_SYM = {
    "attack": lambda ic, c: at(sword(ic, c, c, c), 0, 0, 0.62, 40),
    "defense": lambda ic, c: at(part(ic, SHIELD, c), 0, 0, 0.62),
    "hp": lambda ic, c: at(part(ic, HEART, c), 0, 1, 0.6),
    "luck": lambda ic, c: at(clover(ic, c), 0, -1, 0.62),
    "mana": lambda ic, c: at(part(ic, DROP, c), 0, 0, 0.62),
    "speed": lambda ic, c: at(chevrons(ic, c), 0, 0, 0.62),
}


def octagon(r):
    return poly([(math.cos(math.radians(22.5 + 45 * k)) * r, math.sin(math.radians(22.5 + 45 * k)) * r) for k in range(8)], 1, 32, 32)


def obol(ic, tier, stat):
    if tier in METAL:   # a round coin with a raised rim and a stamped symbol
        R = ramp(METAL[tier])
        return [circle(ic, 32, 32, 24, R, ic.lg(R, 0.2, 0, 0.8, 1), 2),
                f'<circle cx="32" cy="32" r="18.5" fill="{R[2]}" stroke="{R[3]}" stroke-width="1"/>',
                at(STAT_SYM[stat](ic, R[0]), 32, 32, 1.3),
                line("M13 26 C15 18 21 12 29 10", HL, 2.4, 0.7)]
    # a gem cut as an eight-sided coin: a bevelled rim, a flat face and the symbol in a light tone of the stone
    if tier == "bismuth":   # iridescent: a rainbow sweep
        i, j = ic._id(), ic._id()
        ic.defs.append(f'<linearGradient id="{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff5ad0"/><stop offset=".3" stop-color="#8a5aff"/>'
                       f'<stop offset=".55" stop-color="#3ad8f0"/><stop offset=".8" stop-color="#6af05a"/><stop offset="1" stop-color="#ffd23a"/></linearGradient>')
        ic.defs.append(f'<linearGradient id="{j}" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6af0c8"/><stop offset=".5" stop-color="#5a8aff"/>'
                       f'<stop offset="1" stop-color="#d05aff"/></linearGradient>')
        return [f'<path d="{octagon(26)}" fill="url(#{i})" stroke="#1a1030" stroke-width="2" stroke-linejoin="round"/>',
                f'<path d="{octagon(18)}" fill="url(#{j})" stroke="#2a1850" stroke-width="1.2" stroke-linejoin="round"/>',
                at(STAT_SYM[stat](ic, "#fff4a8"), 32, 32, 1.3), line("M14 22 L22 12", HL, 2.4, 0.8)]
    R = ramp(GEMS[tier])
    return [shape(ic, octagon(26), R, ic.lg(R, 0.1, 0, 0.9, 1), 2),
            shape(ic, octagon(19), R, ic.lg((R[2], R[2], R[1]), 0.1, 0, 0.9, 1), 1.2),
            at(STAT_SYM[stat](ic, ramp(R[0])[0]), 32, 32, 1.3), line("M14 22 L22 12", HL, 2.4, 0.8)]


# ----------------------------------------------------------------------------- books
def book(cover, emblem, spine=None, clasp="#e8c050", band=None, marker=None):
    def draw(ic):
        C = ramp(cover)
        S = ramp(spine or C[2])
        out = [part(ic, "M14 10 H50 V56 H14 Z", "#f4ecd8", 1.6),                                 # the page block, seen under the cover
               line("M18 54 H48 M18 51.5 H48", "#c8b898", 1.2),
               shape(ic, "M10 6 H46 Q50 6 50 10 V50 Q50 52 46 52 H10 Z", C, ic.lg(C, 0, 0, 1, 1), 2),
               shape(ic, "M8 6 H15 V52 H8 Q6 52 6 50 V8 Q6 6 8 6 Z", S, ic.lg(S, 0, 0, 1, 0), 1.8),   # the spine
               line("M8 14 H14 M8 44 H14", S[0], 1.6, 0.8)]
        if band:
            out.append(part(ic, "M15 12 H50 V16 H15 Z M15 42 H50 V46 H15 Z", band, 1.2))
        if marker:
            out.append(part(ic, "M38 4 H44 V62 L41 58 L38 62 Z", marker, 1.4))
        out.append(at(emblem(ic), 30.5, 29, 0.8))
        if clasp:
            out.append(part(ic, "M48 24 H54 V34 H48 Z", clasp, 1.4))
        out.append(line("M19 10 H44", HL, 1.6, 0.5))
        return out
    return draw


def apple(ic):
    return [ball(ic, 0, 4, 15, "#e0302a"), part(ic, "M0 -10 C2 -16 6 -20 10 -20 C8 -16 6 -14 2 -10 Z", "#3aa83a", 1.2), cord("M0 -10 L-1 -16", "#6a3a14", 1.6),
            dot(-6, -2, 3, "#ff9a8a")]


def claws(ic):
    return [cord(f"M{x} -18 L{x + 14} 16", "#f0dcc0", 3.4) for x in (-18, -8, 2)]


def star_gem(ic):
    return [part(ic, poly(star_pts(4, 20, 7)), "#ffd23a", 1.6), ball(ic, 0, 0, 6, "#f0f4ff", 1.4)]


def shadow_eye(ic):
    return [part(ic, poly([(0, -20), (20, 0), (0, 20), (-20, 0)]), "#c02a3a", 1.6),
            part(ic, poly([(0, -11), (11, 0), (0, 11), (-11, 0)]), "#2a0a18", 1.2), dot(0, 0, 3.6, "#ff5a5a")]


def dumbbell(ic):
    return [cord("M-12 0 H12", "#c8ccd8", 3.6),
            part(ic, "M-20 -9 H-12 V9 H-20 Z", "#5a5a6a", 1.4), part(ic, "M12 -9 H20 V9 H12 Z", "#5a5a6a", 1.4),
            part(ic, "M-24 -6 H-20 V6 H-24 Z", "#5a5a6a", 1.2), part(ic, "M20 -6 H24 V6 H20 Z", "#5a5a6a", 1.2)]


def globe(ic):
    return [ball(ic, 0, 0, 17, "#3a9ae0"),
            part(ic, "M-10 -12 C-4 -14 2 -10 0 -4 C-4 0 -2 6 -8 8 C-14 4 -16 -6 -10 -12 Z", "#6ad04a", 1.2),
            part(ic, "M6 2 C12 0 16 6 12 12 C8 14 4 10 6 2 Z", "#6ad04a", 1.2)]


def notes(ic):
    return [part(ic, "M-14 -16 H14 V16 H-14 Z", "#f4ecd8", 1.4), line("M-9 -9 H9 M-9 -3 H9 M-9 3 H5 M-9 9 H7", "#8a6a44", 1.8)]


BOOKS = {
    "Adventure Tales": book("#3a8ad8", sword),
    "Cookbook for Travelers": book("#a8683a", apple),
    "Diary of Grunk": book("#7a5a3a", claws, clasp=None, band="#5a3a20"),
    "Field Notes": book("#8a5a2a", notes, clasp=None, marker="#3a9ae8"),
    "Guard Report": book("#d8962a", star_gem, band="#f0d070", clasp=None),
    "Obituary": book("#3a4050", skull, spine="#2a2e3a", clasp="#8a8e9a"),
    "The Shadow Walker: HIDDEN TRUTHS EXPOSED": book("#2a3a44", shadow_eye, spine="#1a2228", clasp="#c02a3a"),
    "Training Log": book("#c83a2a", dumbbell),
    "World History": book("#7a2032", globe, band="#c8963a"),
}


# ----------------------------------------------------------------------------- output
def slug(name: str) -> str:
    return "l-" + re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")


def write(key, draw):
    ic = Icon()
    ic.add(J(draw(ic)))
    (OUT / f"{key}.svg").write_text(ic.svg().replace("<svg ", '<svg data-generated="library_icons.py" ', 1), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lib = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8")).get("library", {})
    n, missing = 0, []
    S, T = spells(), talents()
    for x in lib.get("spells", []):
        if x["name"] not in S:
            missing.append(x["name"]); continue
        el, draw = S[x["name"]]
        write(slug(x["name"]), lambda ic, el=el, draw=draw: [tile(ic, TILE[el]), at(draw(ic), 32, 31)]); n += 1
    for x in lib.get("talents", []):
        if x["name"] not in T:
            missing.append(x["name"]); continue
        col, draw, badge = T[x["name"]]
        write(slug(x["name"]), lambda ic, col=col, draw=draw, badge=badge: [tile(ic, TILE[col]), at(draw(ic), 32, 31), badge(ic) if badge else ""]); n += 1
    for x in lib.get("obols", []):
        write(slug(x["name"]), lambda ic, x=x: obol(ic, x["tier"], x["stat"])); n += 1
    for x in lib.get("books", []):
        if x["name"] not in BOOKS:
            missing.append(x["name"]); continue
        write(slug(x["name"]), BOOKS[x["name"]]); n += 1
    print(f"library icons: wrote {n}" + (f"; no drawing for {missing}" if missing else ""))


if __name__ == "__main__":
    main()
