#!/usr/bin/env python3
"""Draw PORE's monster portraits as HD drawings -> icons/modern/m-<name>.svg

Our own drawings from the monster kit in tools/boss_icons.py (plus a skull, a slime and spider legs), matched to
each monster's silhouette and colours as the wiki describes and shows it (see tools/ART_GUIDE.md). No artwork
from the game or the wiki is used or stored. tools/pixelart.mjs turns them into pixel icons.

Usage: python tools/monster_icons.py
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from boss_icons import INK, blade, blob, body, eye, flame, glow_eyes, grin, horns, tentacles, wings  # noqa: E402
from modern_icons import Icon, circle, dot, line  # noqa: E402
from skin_icons import ramp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"
BONE = "#ece6d6"


# ----------------------------------------------------------------------------- a few more parts
def skull(ic, cx, cy, r, glow=None):
    d = f"M{cx - r} {cy} C{cx - r} {cy - r * 1.3} {cx + r} {cy - r * 1.3} {cx + r} {cy} C{cx + r} {cy + r * 0.6} {cx + r * 0.6} {cy + r * 0.8} {cx + r * 0.5} {cy + r * 1.1} L{cx - r * 0.5} {cy + r * 1.1} C{cx - r * 0.6} {cy + r * 0.8} {cx - r} {cy + r * 0.6} {cx - r} {cy} Z"
    out = [body(ic, d, BONE), f'<ellipse cx="{cx - r * 0.4}" cy="{cy}" rx="{r * 0.28}" ry="{r * 0.32}" fill="{INK}"/>', f'<ellipse cx="{cx + r * 0.4}" cy="{cy}" rx="{r * 0.28}" ry="{r * 0.32}" fill="{INK}"/>',
           f'<path d="M{cx} {cy + r * 0.35} L{cx - r * 0.14} {cy + r * 0.6} L{cx + r * 0.14} {cy + r * 0.6} Z" fill="{INK}"/>']
    if glow:
        out += [dot(cx - r * 0.4, cy, r * 0.12, glow), dot(cx + r * 0.4, cy, r * 0.12, glow)]
    return "".join(out)


def ribs(ic, cx, top, w, h):
    return body(ic, f"M{cx - w / 2} {top} L{cx + w / 2} {top} L{cx + w * 0.4} {top + h} L{cx - w * 0.4} {top + h} Z", "#d8d0bc") + \
        line(" ".join(f"M{cx - w * 0.4} {top + h * t} L{cx + w * 0.4} {top + h * t}" for t in (0.3, 0.55, 0.8)), "#6a6454", 1.4)


def slime(ic, col, crown=False):
    d = "M8 56 C6 44 14 30 32 28 C50 30 58 44 56 56 C50 60 14 60 8 56 Z"
    out = [body(ic, d, col)]
    if crown:
        out.append(body(ic, "M14 34 L18 22 L24 30 L32 18 L40 30 L46 22 L50 34 Z", col, sw=1.6))
    out += [glow_eyes([26, 38], 44, INK, 3, 5), f'<ellipse cx="18" cy="38" rx="3" ry="2" fill="#ffffff" opacity=".7"/>']
    return out


def legs(col, n=4, y=40):
    R = ramp(col)
    ds = []
    for i in range(n):
        dy = i * 5
        ds += [f"M22 {y + dy} C14 {y - 6 + dy} 8 {y + dy} 4 {y + 12 + dy}", f"M42 {y + dy} C50 {y - 6 + dy} 56 {y + dy} 60 {y + 12 + dy}"]
    return "".join(line(d, R[3], 4.6) + line(d, R[1], 2.4) for d in ds)


def goblin_head(ic, skin="#6aba4a", y=30):
    return [body(ic, f"M4 {y - 8} L16 {y - 2} L14 {y + 4} Z", skin, sw=1.4), body(ic, f"M60 {y - 8} L48 {y - 2} L50 {y + 4} Z", skin, sw=1.4),
            body(ic, f"M14 {y} C14 {y - 14} 22 {y - 20} 32 {y - 20} C42 {y - 20} 50 {y - 14} 50 {y} C50 {y + 10} 42 {y + 16} 32 {y + 16} C22 {y + 16} 14 {y + 10} 14 {y} Z", skin),
            eye(ic, 25, y - 2, 3, "#ffd23a"), eye(ic, 39, y - 2, 3, "#ffd23a"), grin(32, y + 6, 14, 6, 5)]


def hood(ic, col, y=6):
    return body(ic, f"M10 60 C8 40 12 {y + 10} 32 {y} C52 {y + 10} 56 40 54 60 Z", col)


# ----------------------------------------------------------------------------- the monsters
M = {}
def m(name):
    def reg(fn):
        M[name] = fn
        return fn
    return reg


@m("Angry Tree")
def angry_tree(ic):
    return [body(ic, "M22 60 L24 38 L40 38 L42 60 Z", "#8a5a3a"), line("M22 60 L14 62 M42 60 L50 62", "#5a3a22", 3),
            blob(ic, 32, 22, 26, 16, "#3a9a3a"), blob(ic, 18, 28, 10, 8, "#4aaa3a"), blob(ic, 46, 28, 10, 8, "#4aaa3a"),
            glow_eyes([28, 36], 44, "#ff5a2a", 4, 2.4), line("M26 41 L30 43 M38 41 L34 43", INK, 1.6), line("M28 52 C30 50 34 50 36 52", INK, 1.8)]


@m("Baby Cyclops")
def baby_cyclops(ic):
    return [body(ic, "M14 60 C12 44 18 36 32 36 C46 36 52 44 50 60 Z", "#a86a3a"),
            body(ic, "M12 28 C12 14 20 8 32 8 C44 8 52 14 52 28 C52 40 44 46 32 46 C20 46 12 40 12 28 Z", "#b8783e"),
            eye(ic, 32, 26, 9, "#3a2a1a"), line("M26 40 C30 42 34 42 38 40", "#5a3a1a", 1.8)]


@m("Bat")
def bat(ic):
    return [wings(ic, "#8a5a3a", 28), circle(ic, 32, 32, 14, ramp("#a8744a")), eye(ic, 32, 31, 8, "#3a2a1a"),
            f'<path d="M27 44 L29 48 L31 44 Z M33 44 L35 48 L37 44 Z" fill="#ffffff"/>']


@m("Colossal Bloom")
def colossal_bloom(ic):
    petals = "".join(body(ic, f"M32 16 L{32 + 13 * c} {16 + 13 * s} L{32 + 5 * c2} {16 + 5 * s2} Z", "#ffc83a", sw=1.2)
                     for c, s, c2, s2 in [(1, 0, .7, .7), (0, 1, -.7, .7), (-1, 0, -.7, -.7), (0, -1, .7, -.7), (.7, .7, 0, 1), (-.7, .7, -1, 0), (-.7, -.7, 0, -1), (.7, -.7, 1, 0)])
    return [tentacles("#3a8a3a", ["M32 26 C30 40 34 48 30 62", "M30 44 C22 40 16 46 10 42", "M32 50 C40 46 46 52 54 48"], 4),
            body(ic, "M10 42 C6 38 8 32 14 36 Z M54 48 C58 44 58 38 52 42 Z", "#4aaa3a", sw=1.2),
            petals, circle(ic, 32, 16, 7, ramp("#7a4a1a")), glow_eyes([29, 35], 15, "#ffd23a", 2, 2)]


@m("Decay Overlord")
def decay_overlord(ic):
    return [line("M54 20 L46 62", "#3a2a3a", 3), hood(ic, "#4a2a5a", 8), horns(ic, "#3a2a3a", False, 10, 12),
            body(ic, "M22 30 C22 22 26 18 32 18 C38 18 42 22 42 30 C42 36 38 38 32 38 C26 38 22 36 22 30 Z", "#1a1220", sw=1),
            glow_eyes([28, 36], 28, "#ff3a4a", 3, 2), dot(10, 46, 1.6, "#ff5ac8"), dot(14, 52, 1.2, "#ff5ac8"), dot(8, 56, 1, "#ff5ac8")]


@m("Dracula")
def dracula(ic):
    return [body(ic, "M4 24 L14 12 L50 12 L60 24 L58 62 L6 62 Z", "#2a1a24"), body(ic, "M14 62 L20 36 L44 36 L50 62 Z", "#b82a3a"),
            body(ic, "M20 30 C20 18 25 12 32 12 C39 12 44 18 44 30 C44 38 39 42 32 42 C25 42 20 38 20 30 Z", "#f0e6e6"),
            body(ic, "M18 26 C18 12 26 6 32 6 C38 6 46 12 46 26 C42 18 36 16 32 20 C28 16 22 18 18 26 Z", "#1a1420", sw=1.2),
            eye(ic, 27, 29, 2.4, "#e2343e"), eye(ic, 37, 29, 2.4, "#e2343e"), f'<path d="M29 36 L30 39 L31 36 Z M33 36 L34 39 L35 36 Z" fill="#ffffff"/>']


@m("Forest Horror")
def forest_horror(ic):
    return [horns(ic, "#e8b83a", False, 12, 14), body(ic, "M6 60 C4 42 14 32 32 32 C50 32 60 42 58 60 Z", "#a83a2a"),
            body(ic, "M12 30 C12 16 20 10 32 10 C44 10 52 16 52 30 C52 40 44 46 32 46 C20 46 12 40 12 30 Z", "#3a8a3a"),
            glow_eyes([24, 40], 26, "#ffd23a", 5, 3), grin(32, 34, 20, 7, 6), line("M12 48 L52 48", "#3a8a3a", 3)]


@m("Frosto")
def frosto(ic):
    return [flame(ic, 12, 34, 9, "#4aa8ff"), flame(ic, 52, 34, 9, "#4aa8ff"),
            body(ic, "M18 60 C16 44 20 34 32 34 C44 34 48 44 46 60 Z", "#3ab8a0"),
            body(ic, "M18 26 C18 12 24 6 32 6 C40 6 46 12 46 26 C46 34 40 38 32 38 C24 38 18 34 18 26 Z", "#5ad8c0"),
            body(ic, "M22 8 L26 0 L30 8 M34 8 L38 0 L42 8", "#9af0e0", sw=1.2), glow_eyes([27, 37], 24, "#e8fcff", 4, 3)]


@m("Glutton Button")
def glutton_button(ic):
    return [body(ic, "M6 40 C4 20 16 8 32 8 C48 8 60 20 58 40 C58 54 48 60 32 60 C16 60 6 54 6 40 Z", "#3a3036"),
            glow_eyes([24, 40], 24, "#e2343e", 4, 3), grin(32, 32, 32, 12, 8), line("M14 46 C24 54 40 54 50 46", "#e8b83a", 2.6),
            circle(ic, 32, 52, 3, ramp("#ffc83a"), sw=1)]


@m("Goblin General")
def goblin_general(ic):
    return [body(ic, "M6 60 C4 42 14 36 32 36 C50 36 60 42 58 60 Z", "#7a7a86"), line("M20 44 L44 44", "#5a5a66", 2),
            *goblin_head(ic, "#5aa84a", 30), body(ic, "M14 22 C14 10 22 6 32 6 C42 6 50 10 50 22 L50 24 L14 24 Z", "#8a8a96"),
            horns(ic, "#e8e0cc", False, 8, 14), dot(46, 14, 2.6, "#c83a2a")]


@m("Goblin Mage")
def goblin_mage(ic):
    return [line("M54 12 L48 62", "#8a5a3a", 3), circle(ic, 54, 10, 4, ramp("#e2343e"), sw=1.2),
            body(ic, "M12 60 C10 46 18 40 32 40 C46 40 54 46 52 60 Z", "#6a4a8a"), *goblin_head(ic, "#6aba4a", 30)]


@m("Goblin Warrior")
def goblin_warrior(ic):
    return [line("M52 30 L60 60", "#6a4a2a", 5), blob(ic, 52, 28, 6, 7, "#8a6a3a"),
            body(ic, "M12 60 C10 46 18 40 32 40 C46 40 54 46 52 60 Z", "#8a6a3a"), *goblin_head(ic, "#5aa04a", 30)]


@m("Golem")
def golem(ic):
    return [body(ic, "M6 56 L4 30 L14 12 L34 6 L52 12 L60 30 L58 56 L40 62 L20 62 Z", "#9a9a90"),
            body(ic, "M14 14 C22 8 34 6 44 10 C38 14 24 14 14 14 Z", "#5aa04a", sw=1.2), dot(48, 40, 3, "#5aa04a"), dot(14, 44, 2.4, "#5aa04a"),
            line("M18 26 L26 32 M44 22 L50 30 M22 48 L30 46", "#6a6a60", 1.8), glow_eyes([26, 38], 34, "#3a3a36", 5, 3)]


@m("Green Slime")
def green_slime(ic):
    return slime(ic, "#7ad04a")


@m("Guardling")
def guardling(ic):
    return [line("M12 34 L4 26 M52 34 L60 26 M14 44 L6 48 M50 44 L58 48 M18 50 L14 58 M46 50 L50 58", "#8a1a1a", 3),
            body(ic, "M12 40 C12 28 20 22 32 22 C44 22 52 28 52 40 C52 50 44 54 32 54 C20 54 12 50 12 40 Z", "#d23a2a"),
            body(ic, "M22 22 L18 10 L28 20 Z M42 22 L46 10 L36 20 Z", "#d23a2a", sw=1.2), glow_eyes([26, 38], 36, "#ffd23a", 3, 3)]


@m("Half Dead")
def half_dead(ic):
    return [body(ic, "M8 60 C6 44 14 36 32 36 C50 36 58 44 56 60 Z", "#3a3a44"),
            body(ic, "M14 28 C14 14 22 8 32 8 C42 8 50 14 50 28 C50 38 42 44 32 44 C22 44 14 38 14 28 Z", "#9aa4a0"),
            eye(ic, 25, 26, 3.4, "#c83a3a"), glow_eyes([39], 26, INK, 5, 2), line("M26 36 L38 36", INK, 2), line("M36 12 L40 20", "#6a746e", 1.6)]


@m("Ice Dragon")
def ice_dragon(ic):
    return [line("M40 60 C60 56 60 40 46 38 C32 36 30 26 38 20", "#1a4a8a", 12), line("M40 60 C60 56 60 40 46 38 C32 36 30 26 38 20", "#4aa8f0", 8),
            body(ic, "M22 22 C20 10 30 4 40 8 C48 12 48 22 42 26 C36 30 24 30 22 22 Z", "#6ac0ff"),
            body(ic, "M26 8 L22 0 L32 6 Z M38 6 L44 0 L42 10 Z", "#dff4ff", sw=1.2), eye(ic, 34, 16, 3, "#1a2a6a", slit=True),
            grin(28, 22, 12, 5, 4), line("M10 50 L20 40 M6 40 L16 34", "#9ad8ff", 2)]


@m("Ice Fly")
def ice_fly(ic):
    return [body(ic, "M30 30 L4 12 L10 30 Z", "#aaf0f0", sw=1.2), body(ic, "M34 30 L60 12 L54 30 Z", "#aaf0f0", sw=1.2),
            body(ic, "M30 36 L6 46 L14 34 Z", "#8ae0e8", sw=1.2), body(ic, "M34 36 L58 46 L50 34 Z", "#8ae0e8", sw=1.2),
            line("M32 30 L32 60", "#1a8a8a", 5), line("M32 30 L32 60", "#3ad0c0", 3), circle(ic, 32, 26, 6, ramp("#3ad0c0")), glow_eyes([29, 35], 25, "#1a2a3a", 2.4, 2.4)]


@m("Ice Prince")
def ice_prince(ic):
    return [line("M12 60 L20 4", "#3a6aa8", 3), body(ic, "M20 4 L16 14 L24 14 Z", "#bff0ff", sw=1.2),
            body(ic, "M16 60 L22 30 L42 30 L48 60 Z", "#3a8ad8"), body(ic, "M22 30 L26 8 L32 16 L38 6 L42 30 Z", "#8ad8ff"),
            glow_eyes([29, 35], 24, "#ffffff", 3, 2)]


@m("Jellyfish")
def jellyfish(ic):
    return [tentacles("#4a8ad8", ["M18 36 C16 46 20 52 16 60", "M26 38 C26 48 22 54 24 62", "M38 38 C38 48 42 54 40 62", "M46 36 C48 46 44 52 48 60"], 3),
            body(ic, "M8 36 C8 16 18 6 32 6 C46 6 56 16 56 36 C50 40 14 40 8 36 Z", "#6aa8f0"), glow_eyes([26, 38], 24, "#1a2a4a", 3, 3)]


@m("Jungle Spider")
def jungle_spider(ic):
    return [legs("#2a3a24", 3, 34), blob(ic, 32, 42, 18, 14, "#3a4a2e"), blob(ic, 32, 26, 12, 9, "#445a36"),
            glow_eyes([27, 32, 37], 24, "#e2343e", 3, 3), glow_eyes([29.5, 34.5], 29, "#e2343e", 2, 2)]


@m("Lava Eater")
def lava_eater(ic):
    return [body(ic, "M8 60 L6 36 L14 22 L10 12 L22 16 L28 6 L34 14 L42 6 L44 18 L54 14 L52 28 L58 38 L56 60 Z", "#d2461a"),
            dot(22, 30, 3, "#ffb02e"), dot(42, 36, 3.4, "#ffb02e"), dot(30, 50, 2.6, "#ffb02e"),
            glow_eyes([26, 38], 28, "#ffe27a", 4, 3), grin(32, 38, 16, 7, 5)]


@m("Minotaur")
def minotaur(ic):
    return [line("M6 64 L14 20", "#6a6a74", 4), body(ic, "M4 22 C8 12 18 12 18 22 L14 30 Z", "#b8c0cc", sw=1.2),
            body(ic, "M8 60 C6 44 16 36 32 36 C48 36 58 44 56 60 Z", "#6a4a2a"),
            body(ic, "M16 28 C16 16 22 10 32 10 C42 10 48 16 48 28 C48 38 42 44 32 44 C22 44 16 38 16 28 Z", "#8a5a34"),
            horns(ic, "#ffd23a", True, 16, 12), glow_eyes([25, 39], 26, "#e2343e", 4, 3),
            body(ic, "M26 34 C26 42 38 42 38 34 Z", "#c89a6a", sw=1.2), dot(29, 37, 1.2, INK), dot(35, 37, 1.2, INK)]


@m("Peaks Dweller")
def peaks_dweller(ic):
    return [line("M4 30 L16 44", "#6a4a2a", 5), body(ic, "M8 60 C4 40 12 20 32 20 C52 20 60 40 56 60 Z", "#b8d8f0"),
            body(ic, "M20 36 C20 28 24 24 32 24 C40 24 44 28 44 36 C44 42 40 46 32 46 C24 46 20 42 20 36 Z", "#8ab0d0", sw=1.2),
            glow_eyes([27, 37], 34, "#1a2a3a", 3, 3), line("M28 41 L36 41", INK, 1.6)]


@m("Pink Slime")
def pink_slime(ic):
    return slime(ic, "#e86ac8")


@m("Purple Slime")
def purple_slime(ic):
    return slime(ic, "#9a5ae8", crown=True)


@m("Pyro")
def pyro(ic):
    return [flame(ic, 12, 22, 8), body(ic, "M14 60 C12 40 18 30 32 30 C46 30 52 40 50 60 Z", "#3a8a3a"),
            body(ic, "M16 26 C16 10 24 4 32 4 C40 4 48 10 48 26 Z", "#3a8a3a"),
            body(ic, "M22 26 C22 18 26 14 32 14 C38 14 42 18 42 26 C42 32 38 36 32 36 C26 36 22 32 22 26 Z", "#f0d8b8", sw=1.2),
            body(ic, "M24 30 C26 44 30 50 32 52 C34 50 38 44 40 30 C36 34 28 34 24 30 Z", "#ffe27a", sw=1.2), glow_eyes([28, 36], 25, INK, 2.4, 2.4)]


@m("Rhino")
def rhino(ic):
    return [circle(ic, 44, 44, 14, ramp("#6a4a3a")), circle(ic, 44, 44, 6, ramp("#a8744a"), sw=1.4),
            body(ic, "M4 36 C4 22 14 14 28 14 C40 14 48 20 48 32 C48 44 38 50 26 50 C12 50 4 46 4 36 Z", "#8a8a96"),
            body(ic, "M6 30 L0 14 L12 24 Z", "#e8e0cc", sw=1.2), glow_eyes([20], 28, INK, 3, 3), line("M10 40 L20 40", "#5a5a66", 1.6)]


@m("Rogue Undead")
def rogue_undead(ic):
    return [circle(ic, 48, 44, 12, ramp("#8a5a3a")), line("M6 60 L16 36", "#6a4a2a", 3), body(ic, "M4 36 L16 30 L14 42 Z", "#c4ccd8", sw=1.2),
            ribs(ic, 30, 40, 18, 18), skull(ic, 30, 24, 11, "#ffb02e")]


@m("Smiler")
def smiler(ic):
    return [body(ic, "M32 2 L40 16 L26 14 Z", "#2a4a6a", sw=1.4),
            body(ic, "M4 40 C4 22 16 12 32 12 C48 12 60 22 60 40 C60 54 48 60 32 60 C16 60 4 54 4 40 Z", "#34587a"),
            eye(ic, 18, 28, 3, "#ffd23a"), eye(ic, 46, 28, 3, "#ffd23a"), grin(32, 38, 40, 16, 10)]


@m("Snake")
def snake(ic):
    return [line("M8 58 C20 62 44 62 50 54 C56 46 44 40 34 44", "#2a2a36", 12), line("M8 58 C20 62 44 62 50 54 C56 46 44 40 34 44", "#5a5a6a", 8),
            body(ic, "M18 40 C18 28 26 22 34 24 C42 26 44 36 38 42 C32 48 18 48 18 40 Z", "#6a6a7a"),
            glow_eyes([26, 34], 34, "#e2343e", 3, 3), line("M24 44 L20 50 M20 50 L18 48 M20 50 L22 52", "#e2343e", 1.2)]


@m("Soil Serpent")
def soil_serpent(ic):
    return [body(ic, "M10 60 C10 40 16 20 32 16 C48 20 54 40 54 60 Z", "#8a5a3a"),
            line("M14 50 L50 50 M16 40 L48 40", "#6a4228", 1.6), glow_eyes([26, 38], 26, INK, 3, 3),
            f'<ellipse cx="32" cy="34" rx="7" ry="5" fill="{INK}"/>', f'<path d="M27 32 L29 35 L31 32 Z M33 32 L35 35 L37 32 Z" fill="#ffffff"/>']


@m("Spawn Camper")
def spawn_camper(ic):
    return [body(ic, "M6 44 C4 24 16 10 32 10 C48 10 60 24 58 44 C56 56 46 60 32 60 C18 60 8 56 6 44 Z", "#e8c050"),
            eye(ic, 22, 26, 5, "#3a2a1a"), grin(36, 38, 26, 12, 7), dot(46, 20, 2.4, "#c89a30"), dot(14, 46, 2, "#c89a30")]


@m("Tiny Caster")
def tiny_caster(ic):
    return [line("M10 60 L20 12", "#6a4a2a", 3), circle(ic, 20, 10, 3.4, ramp("#4aa8ff"), sw=1.2),
            hood(ic, "#3a5a3a", 10), body(ic, "M22 32 C22 24 26 20 32 20 C38 20 42 24 42 32 C42 38 38 40 32 40 C26 40 22 38 22 32 Z", "#141a14", sw=1),
            glow_eyes([28, 36], 30, "#b8ffb8", 3, 2)]


@m("Tree Trunker")
def tree_trunker(ic):
    return [body(ic, "M10 60 L14 24 C22 18 42 18 50 24 L54 60 Z", "#9a4a2a"), body(ic, "M14 24 C22 18 42 18 50 24 C42 30 22 30 14 24 Z", "#d8a070", sw=1.4),
            line("M20 24 C26 22 38 22 44 24", "#a86a3a", 1.2), body(ic, "M50 30 L60 22 L56 34 Z", "#4aa03a", sw=1.2),
            glow_eyes([26, 38], 38, INK, 3, 4), line("M28 50 C30 48 34 48 36 50", INK, 1.8)]


@m("Tummy")
def tummy(ic):
    return [body(ic, "M4 50 C2 30 14 14 32 14 C50 14 62 30 60 50 C54 60 10 60 4 50 Z", "#8a6a3a"),
            circle(ic, 32, 38, 12, ramp("#e2843a")), f'<circle cx="32" cy="38" r="6" fill="{INK}"/>', glow_eyes([22, 42], 26, INK, 3, 3)]


@m("Undead")
def undead(ic):
    return [line("M52 28 L60 50", "#8a5a3a", 3), ribs(ic, 32, 40, 20, 18), skull(ic, 32, 24, 12)]


@m("Undead Guardian")
def undead_guardian(ic):
    return [line("M10 62 L18 2", "#6a4a2a", 3), body(ic, "M44 30 L60 34 L58 56 L46 62 Z", "#8a4ac8"),
            ribs(ic, 32, 40, 18, 18), skull(ic, 32, 26, 11), body(ic, "M20 20 C20 10 26 6 32 6 C38 6 44 10 44 20 Z", "#e8c040"),
            horns(ic, "#f4f0e8", False, 8, 12)]


@m("Undead Hulk")
def undead_hulk(ic):
    return [line("M4 60 L22 40", "#6a4a2a", 6), blob(ic, 8, 58, 6, 5, "#8a6a3a"), ribs(ic, 34, 34, 30, 24), skull(ic, 34, 20, 12)]


@m("Undead Oracle")
def undead_oracle(ic):
    return [line("M10 60 L14 8", "#c8a040", 3), circle(ic, 14, 8, 3.4, ramp("#8aff4a"), sw=1.2), hood(ic, "#2a2430", 16),
            skull(ic, 32, 30, 11, "#ff3a3a"), body(ic, "M18 20 L22 4 L27 14 L32 2 L37 14 L42 4 L46 20 Z", "#e8c040", sw=1.4)]


@m("Undead Shaman")
def undead_shaman(ic):
    return [line("M50 60 L46 8", "#4a3a2a", 3), circle(ic, 46, 8, 4, ramp("#6ae05a"), sw=1.2), hood(ic, "#3a2a48", 12),
            horns(ic, "#e8e0cc", False, 12, 12), skull(ic, 32, 32, 10, "#8aff4a")]


@m("Well Guardian")
def well_guardian(ic):
    return [line("M10 60 L14 10", "#3a8a3a", 3), line("M8 14 L8 6 M14 12 L14 2 M20 14 L20 6 M8 14 L20 14", "#6ae05a", 2),
            body(ic, "M14 60 C12 40 20 22 34 22 C48 22 56 40 54 60 Z", "#3ab8b0"),
            body(ic, "M22 30 C22 20 28 14 34 14 C40 14 46 20 46 30 C46 38 40 42 34 42 C28 42 22 38 22 30 Z", "#5ad8c8"),
            glow_eyes([29, 39], 28, "#e2343e", 3, 3), grin(34, 34, 12, 5, 4)]


@m("Winged Undead")
def winged_undead(ic):
    return [wings(ic, "#3a3440", 22), line("M8 6 C16 2 22 6 24 12", "#c8ccd8", 3), line("M22 10 L14 62", "#5a4a3a", 2.6),
            hood(ic, "#5a5a68", 10), skull(ic, 34, 30, 10, "#9af0ff")]


@m("Wyvern")
def wyvern(ic):
    return [wings(ic, "#8a9a2a", 20), line("M32 44 C30 54 40 58 48 60", "#4a5a1a", 8), line("M32 44 C30 54 40 58 48 60", "#a8b83a", 5),
            body(ic, "M18 34 C18 22 24 16 32 16 C40 16 46 22 46 34 C46 42 40 48 32 48 C24 48 18 42 18 34 Z", "#b8c83a"),
            eye(ic, 26, 30, 3, "#e2343e", slit=True), eye(ic, 38, 30, 3, "#e2343e", slit=True), grin(32, 38, 14, 6, 5)]


@m("Zwigli")
def zwigli(ic):
    return [line("M30 20 C22 18 18 8 26 4 C34 2 34 12 28 12", "#1a8a6a", 6), line("M30 20 C22 18 18 8 26 4 C34 2 34 12 28 12", "#3ae0b0", 3.6),
            body(ic, "M18 60 C16 44 22 20 32 20 C42 20 48 44 46 60 Z", "#2a9a6a"),
            glow_eyes([28, 36], 36, "#e8fff4", 3, 3), line("M28 44 C30 46 34 46 36 44", "#0a3a2a", 1.6)]


def slug(name: str) -> str:
    return "m-" + re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in M.items():
        ic = Icon()
        ic.add(draw(ic))
        (OUT / f"{slug(name)}.svg").write_text(ic.svg().replace("<svg ", '<svg data-generated="monster_icons.py" ', 1), encoding="utf-8")
    print(f"monster icons: wrote {len(M)}")


if __name__ == "__main__":
    main()
