#!/usr/bin/env python3
"""Draw PORE's world boss portraits as HD drawings -> icons/modern/b-<name>.svg

Each boss is our own drawing, built from a small monster kit (bodies, eyes, toothy mouths, horns, wings,
tentacles, flames, weapons) to match the boss's silhouette and colours as the wiki describes and shows it.
No artwork from the game or the wiki is used or stored. tools/pixelart.mjs turns them into pixel icons like
every other icon.

Usage: python tools/boss_icons.py
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from modern_icons import HL, Icon, circle, dot, line, shape  # noqa: E402
from skin_icons import ramp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"
INK = "#141216"


# ----------------------------------------------------------------------------- the monster kit
def body(ic, d, col, grad=True, sw=2.0):
    R = ramp(col)
    return shape(ic, d, R, ic.lg(R, 0.2, 0, 0.8, 1) if grad else None, sw)


def blob(ic, cx, cy, rx, ry, col):
    d = f"M{cx - rx} {cy} C{cx - rx} {cy - ry * 1.1} {cx + rx} {cy - ry * 1.1} {cx + rx} {cy} C{cx + rx} {cy + ry * 1.05} {cx - rx} {cy + ry * 1.05} {cx - rx} {cy} Z"
    return body(ic, d, col)


def eye(ic, cx, cy, r, iris="#e2343e", slit=False, white="#fff6ee"):
    out = [circle(ic, cx, cy, r, ramp(white), sw=1.6), dot(cx, cy, r * 0.6, iris)]
    out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 0.16}" ry="{r * 0.5}" fill="{INK}"/>' if slit else dot(cx, cy, r * 0.28, INK))
    out.append(dot(cx - r * 0.35, cy - r * 0.4, max(0.8, r * 0.2), HL))
    return "".join(out)


def glow_eyes(xs, y, col, w=4, h=3):
    return "".join(f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="1" fill="{col}"/>' for x in xs)


def grin(cx, cy, w, h, teeth=6):
    """A dark open mouth with a row of white teeth top and bottom."""
    x0, x1 = cx - w / 2, cx + w / 2
    out = [f'<path d="M{x0} {cy} C{x0 + w * 0.15} {cy + h} {x1 - w * 0.15} {cy + h} {x1} {cy} C{x1 - w * 0.2} {cy + h * 0.25} {x0 + w * 0.2} {cy + h * 0.25} {x0} {cy} Z" fill="{INK}"/>']
    step = w / teeth
    for i in range(teeth):
        tx = x0 + step * (i + 0.5)
        out.append(f'<path d="M{tx - step * 0.42} {cy + 0.6} L{tx} {cy + h * 0.45} L{tx + step * 0.42} {cy + 0.6} Z" fill="#fffaf0"/>')
    for i in range(1, teeth - 1):
        tx = x0 + step * (i + 0.5)
        out.append(f'<path d="M{tx - step * 0.38} {cy + h * 0.78} L{tx} {cy + h * 0.42} L{tx + step * 0.38} {cy + h * 0.78} Z" fill="#fffaf0"/>')
    return "".join(out)


def horns(ic, col, curl=False, y=14, spread=14):
    if curl:
        l = f"M{32 - spread} {y + 4} C{32 - spread - 14} {y} {32 - spread - 12} {y - 14} {32 - spread - 2} {y - 10} C{32 - spread - 8} {y - 6} {32 - spread - 6} {y + 2} {32 - spread + 4} {y + 6} Z"
        r = f"M{32 + spread} {y + 4} C{32 + spread + 14} {y} {32 + spread + 12} {y - 14} {32 + spread + 2} {y - 10} C{32 + spread + 8} {y - 6} {32 + spread + 6} {y + 2} {32 + spread - 4} {y + 6} Z"
    else:
        l = f"M{32 - spread + 4} {y + 4} C{32 - spread - 2} {y - 2} {32 - spread - 4} {y - 10} {32 - spread - 2} {y - 14} C{32 - spread + 2} {y - 8} {32 - spread + 6} {y - 4} {32 - spread + 10} {y} Z"
        r = f"M{32 + spread - 4} {y + 4} C{32 + spread + 2} {y - 2} {32 + spread + 4} {y - 10} {32 + spread + 2} {y - 14} C{32 + spread - 2} {y - 8} {32 + spread - 6} {y - 4} {32 + spread - 10} {y} Z"
    return body(ic, l, col, sw=1.6) + body(ic, r, col, sw=1.6)


def wings(ic, col, y=26):
    l = f"M24 {y} C14 {y - 16} 4 {y - 14} 1 {y - 4} C6 {y - 4} 6 {y + 2} 4 {y + 8} C9 {y + 5} 11 {y + 9} 11 {y + 14} C15 {y + 9} 20 {y + 10} 24 {y + 8} Z"
    r = f"M40 {y} C50 {y - 16} 60 {y - 14} 63 {y - 4} C58 {y - 4} 58 {y + 2} 60 {y + 8} C55 {y + 5} 53 {y + 9} 53 {y + 14} C49 {y + 9} 44 {y + 10} 40 {y + 8} Z"
    return body(ic, l, col, sw=1.6) + body(ic, r, col, sw=1.6)


def tentacles(col, pts, w=5):
    R = ramp(col)
    return "".join(line(d, R[3], w + 3) + line(d, R[1], w) for d in pts)


def flame(ic, cx, cy, s, col="#ff8a2a"):
    d = f"M{cx} {cy - s} C{cx + s * 0.9} {cy - s * 0.2} {cx + s * 0.7} {cy + s * 0.8} {cx} {cy + s * 0.8} C{cx - s * 0.7} {cy + s * 0.8} {cx - s * 0.9} {cy - s * 0.2} {cx - s * 0.3} {cy - s * 0.4} C{cx - s * 0.2} {cy - s * 0.1} {cx} {cy - s * 0.4} {cx} {cy - s} Z"
    inner = f"M{cx} {cy - s * 0.3} C{cx + s * 0.45} {cy + s * 0.1} {cx + s * 0.3} {cy + s * 0.65} {cx} {cy + s * 0.65} C{cx - s * 0.3} {cy + s * 0.65} {cx - s * 0.45} {cy + s * 0.1} {cx} {cy - s * 0.3} Z"
    return body(ic, d, col, sw=1.4) + body(ic, inner, "#ffe27a", sw=0)


def blade(d, col="#c4ccd8", w=4):
    R = ramp(col)
    return line(d, R[3], w + 3) + line(d, R[1], w)


def stars(pts, col="#ffffff"):
    return "".join(dot(x, y, r, col) for x, y, r in pts)


# ----------------------------------------------------------------------------- the bosses
def bills_cousin(ic):   # a purple cube with one green eye
    return [body(ic, "M32 8 L56 20 L56 46 L32 58 L8 46 L8 20 Z", "#8a6ae0"),
            body(ic, "M32 8 L56 20 L32 32 L8 20 Z", "#b49aff", sw=1.4),
            body(ic, "M32 32 L56 20 L56 46 L32 58 Z", "#5a44a8", sw=1.4),
            f'<ellipse cx="20" cy="37" rx="7" ry="5" fill="#fff6ee" stroke="{INK}" stroke-width="1.4"/>', dot(20, 37, 3, "#3aa84a"), dot(20, 37, 1.3, INK)]


def bound_blaze(ic):   # a dark golem held in chains, burning hands and head, one orange eye
    return [flame(ic, 32, 14, 10), flame(ic, 10, 30, 8), flame(ic, 54, 30, 8),
            body(ic, "M16 28 C16 18 24 14 32 14 C40 14 48 18 48 28 L50 50 C44 58 20 58 14 50 Z", "#4a3a6a"),
            eye(ic, 32, 32, 7, "#ff8a2a"), line("M18 44 L46 44", "#b8b0a0", 2.4), line("M20 50 L44 50", "#b8b0a0", 2.4)]


def brain_storm(ic):   # a pink brain with a toothy maw, grey claws below
    return [tentacles("#8a8a9a", ["M20 50 L12 60", "M30 52 L28 62", "M40 52 L44 62"], 4),
            body(ic, "M6 32 C4 14 18 6 32 6 C46 6 60 14 58 32 C58 46 46 54 32 54 C18 54 6 46 6 32 Z", "#f08aa8"),
            line("M14 20 C20 16 22 24 28 20 M36 16 C40 22 46 16 50 22 M12 30 C16 26 20 32 24 28", "#b84a6a", 1.6),
            grin(32, 34, 28, 14, 7)]


def deep_blue_director(ic):   # a cluster of blue jellyfish domes with trailing tentacles and yellow eyes
    return [tentacles("#3a7ae8", ["M14 36 C12 46 16 52 12 60", "M26 38 C26 48 22 54 24 62", "M38 38 C40 48 36 54 40 62", "M50 36 C52 46 48 52 52 60"], 3),
            blob(ic, 16, 24, 11, 10, "#4a8aff"), blob(ic, 48, 24, 11, 10, "#4a8aff"), blob(ic, 32, 18, 13, 12, "#6aa8ff"),
            glow_eyes([28, 36], 22, "#ffd23a"), glow_eyes([13, 19], 26, "#ffd23a", 3, 2), glow_eyes([45, 51], 26, "#ffd23a", 3, 2)]


def fragment_of_madness(ic):   # a shadowy purple ball that is mostly a huge grin
    return [body(ic, "M6 32 C4 14 18 4 32 4 C46 4 60 14 58 32 C58 50 46 60 32 60 C18 60 6 50 6 32 Z", "#3a2a4a"),
            dot(16, 14, 2, "#6a4a8a"), dot(46, 10, 2.4, "#6a4a8a"), dot(52, 22, 1.6, "#6a4a8a"),
            grin(32, 30, 42, 22, 8), glow_eyes([22, 42], 20, "#e8e0ff", 5, 2)]


def galactic_tear(ic):   # a starry spirit figure, arms spread
    return [body(ic, "M32 6 C38 6 40 12 38 18 C44 20 50 28 58 26 C54 32 46 30 42 30 L40 44 C42 52 38 60 32 60 C26 60 22 52 24 44 L22 30 C18 30 10 32 6 26 C14 28 20 20 26 18 C24 12 26 6 32 6 Z", "#1a2a5a"),
            stars([(32, 30, 1.4), (28, 40, 1), (36, 48, 1.2), (30, 54, 0.9), (46, 27, 0.9), (16, 27, 0.9)]),
            glow_eyes([29, 35], 13, "#dff4ff", 2.4, 1.6), line("M32 24 L32 36 M26 30 L38 30", "#ffffff", 1)]


def goblin_king(ic):   # a fat green goblin with a wide toothy grin and long claws
    return [body(ic, "M8 60 C6 44 14 34 32 34 C50 34 58 44 56 60 Z", "#3a9a5a"),
            body(ic, "M2 18 L14 24 L12 30 Z", "#4aba6a", sw=1.4), body(ic, "M62 18 L50 24 L52 30 Z", "#4aba6a", sw=1.4),
            body(ic, "M12 26 C12 12 20 6 32 6 C44 6 52 12 52 26 C52 38 44 44 32 44 C20 44 12 38 12 26 Z", "#4aba6a"),
            eye(ic, 24, 22, 3.6, "#ffd23a"), eye(ic, 40, 22, 3.6, "#ffd23a"), grin(32, 32, 24, 10, 7),
            line("M16 52 L10 58 M20 52 L16 60 M44 52 L48 60 M48 52 L54 58", "#e8f0d0", 1.6)]


def hells_warden(ic):   # a red devil with bat wings, horns and a trident
    return [wings(ic, "#8a2a2a", 24), line("M52 8 L52 60", "#3a2a2a", 3), line("M46 6 L46 12 L58 12 L58 6 M52 4 L52 12", "#c8ccd8", 2),
            body(ic, "M20 58 C18 44 24 38 32 38 C40 38 46 44 44 58 Z", "#c8343e"),
            body(ic, "M18 26 C18 14 24 10 32 10 C40 10 46 14 46 26 C46 36 40 42 32 42 C24 42 18 36 18 26 Z", "#e2443e"),
            horns(ic, "#3a2a2a", False, 12, 12), glow_eyes([26, 38], 26, "#ffd23a", 5, 3), grin(32, 33, 14, 6, 5)]


def horn_havoc(ic):   # a dark brown horned beast with glowing red eyes
    return [body(ic, "M8 60 C6 42 16 34 32 34 C48 34 58 42 56 60 Z", "#4a3024"),
            body(ic, "M14 30 C14 16 22 10 32 10 C42 10 50 16 50 30 C50 42 42 48 32 48 C22 48 14 42 14 30 Z", "#5a3a2a"),
            horns(ic, "#c86a3a", True, 16, 12), glow_eyes([24, 40], 26, "#ff3a2a", 6, 3),
            body(ic, "M26 36 C26 42 38 42 38 36 C36 40 28 40 26 36 Z", "#3a2018", sw=1.2)]


def hungry_eye(ic):   # a red blob covered in small eyes around one big eye
    return [body(ic, "M6 40 C2 22 14 6 32 6 C50 6 62 22 58 40 C56 56 44 62 32 62 C20 62 8 56 6 40 Z", "#c8344a"),
            eye(ic, 18, 20, 4, "#ffd23a"), eye(ic, 44, 16, 4.4, "#ffd23a"), eye(ic, 52, 34, 3.6, "#ffd23a"), eye(ic, 12, 38, 3.6, "#ffd23a"),
            eye(ic, 30, 14, 3, "#ffd23a"), eye(ic, 32, 38, 10, "#ff8a2a", slit=True)]


def ice_cube_slime(ic):   # a green-blue jelly cube with a sword stuck in the top
    return [blade("M40 2 L34 22", "#c4ccd8", 3.4), line("M34 8 L44 12", "#6a4a2a", 3),
            body(ic, "M10 24 C10 18 14 16 20 16 L46 16 C52 16 54 20 54 24 L56 52 C56 58 52 60 46 60 L18 60 C12 60 8 58 8 52 Z", "#7ae0b8"),
            f'<rect x="16" y="22" width="10" height="6" rx="2" fill="#ffffff" opacity=".6"/>', glow_eyes([24, 40], 38, "#1a3a2a", 4, 5),
            f'<path d="M28 48 C30 51 34 51 36 48" fill="none" stroke="#1a3a2a" stroke-width="2"/>']


def king_nothing(ic):   # a fat king on a throne with a crown
    return [body(ic, "M4 60 L4 22 C4 16 10 14 14 18 L14 60 Z", "#8a5a2a"), body(ic, "M60 60 L60 22 C60 16 54 14 50 18 L50 60 Z", "#8a5a2a"),
            body(ic, "M10 60 C8 40 18 32 32 32 C46 32 56 40 54 60 Z", "#c89a6a"),
            body(ic, "M18 26 C18 16 24 12 32 12 C40 12 46 16 46 26 C46 34 40 38 32 38 C24 38 18 34 18 26 Z", "#e8c8a0"),
            body(ic, "M20 14 L22 2 L27 9 L32 0 L37 9 L42 2 L44 14 Z", "#ffc83a", sw=1.4), dot(32, 8, 1.8, "#e2343e"),
            eye(ic, 27, 24, 2.4, "#3a2a1a"), eye(ic, 37, 24, 2.4, "#3a2a1a"), line("M28 32 C30 34 34 34 36 32", "#8a4a3a", 1.4),
            line("M20 44 L44 44", "#ffc83a", 2.4)]


def lazy_dweller(ic):   # a teal deep-sea brute with a glowing lure
    return [line("M32 12 C32 4 40 2 44 6", "#2a4a4a", 2), circle(ic, 45, 8, 3.4, ramp("#9af0ff"), sw=1.4),
            body(ic, "M4 44 C2 30 8 24 16 24 L48 24 C56 24 62 30 60 44 L56 60 L8 60 Z", "#2a8a8a"),
            body(ic, "M14 30 C14 18 22 12 32 12 C42 12 50 18 50 30 C50 40 42 44 32 44 C22 44 14 40 14 30 Z", "#3aa8a0"),
            glow_eyes([25, 39], 26, "#fff6a0", 5, 3), grin(32, 34, 18, 7, 6)]


def matchstick_mike(ic):   # a living fireball with a glowing carved face
    return [flame(ic, 32, 30, 28, "#ff5a1a"), body(ic, "M14 36 C14 22 22 16 32 16 C42 16 50 22 50 36 C50 48 42 54 32 54 C22 54 14 48 14 36 Z", "#e8581a"),
            f'<path d="M20 30 L28 30 L24 36 Z" fill="#ffe27a"/>', f'<path d="M36 30 L44 30 L40 36 Z" fill="#ffe27a"/>',
            f'<path d="M20 42 L24 46 L28 42 L32 46 L36 42 L40 46 L44 42 C40 50 24 50 20 42 Z" fill="#ffe27a"/>']


def minds_end(ic):   # a dark teal tentacle-faced horror with red bat wings
    return [wings(ic, "#b8343e", 22),
            body(ic, "M18 58 C16 44 22 36 32 36 C42 36 48 44 46 58 Z", "#2a5a5a"),
            body(ic, "M18 24 C18 12 24 8 32 8 C40 8 46 12 46 24 C46 32 40 36 32 36 Z", "#3a7a7a"),
            tentacles("#3a7a7a", ["M24 34 C22 42 26 46 24 52", "M30 36 C30 44 28 48 30 54", "M36 36 C36 44 38 48 36 54", "M42 34 C44 42 40 46 42 52"], 3),
            glow_eyes([27, 37], 22, "#ffe27a", 4, 3)]


def moon_moon(ic):   # a pale owl-like beast with a red mane and a crescent on its brow
    return [body(ic, "M2 30 C8 14 20 8 32 8 C44 8 56 14 62 30 C54 26 50 32 46 28 C42 34 22 34 18 28 C14 32 10 26 2 30 Z", "#c83a3a"),
            body(ic, "M10 60 C8 40 18 28 32 28 C46 28 56 40 54 60 Z", "#d8d0c8"),
            body(ic, "M18 30 C18 20 24 14 32 14 C40 14 46 20 46 30 C46 40 40 44 32 44 C24 44 18 40 18 30 Z", "#ece6de"),
            body(ic, "M32 16 C28 18 28 24 32 26 C29 26 26 24 26 21 C26 18 29 16 32 16 Z", "#ffe27a", sw=1),
            eye(ic, 25, 30, 4, "#ff8a2a"), eye(ic, 39, 30, 4, "#ff8a2a"), body(ic, "M30 36 L34 36 L32 41 Z", "#e8a83a", sw=1)]


def mr_pupil(ic):   # a round red creature that is one huge slit-pupilled eye
    return [tentacles("#a8243a", ["M16 50 L10 60", "M26 54 L24 62", "M38 54 L40 62", "M48 50 L54 60"], 4),
            body(ic, "M6 32 C4 14 18 4 32 4 C46 4 60 14 58 32 C58 50 46 58 32 58 C18 58 6 50 6 32 Z", "#d8344a"),
            dot(14, 12, 3, "#e8586a"), dot(52, 16, 2.4, "#e8586a"), eye(ic, 32, 32, 18, "#ff8a1a", slit=True, white="#ffe6c8")]


def muscle_sprout(ic):   # a purple muscular plant with a crown of leaves and a skull face
    return [body(ic, "M20 12 L14 0 L26 8 Z", "#8ad04a", sw=1.4), body(ic, "M32 10 L32 -2 L38 8 Z", "#8ad04a", sw=1.4), body(ic, "M44 12 L50 0 L38 8 Z", "#8ad04a", sw=1.4),
            body(ic, "M4 36 C2 20 14 10 32 10 C50 10 62 20 60 36 C58 52 46 60 32 60 C18 60 6 52 4 36 Z", "#6a4ab8"),
            body(ic, "M22 30 C22 22 26 18 32 18 C38 18 42 22 42 30 C42 36 38 40 32 40 C26 40 22 36 22 30 Z", "#f4f0e8", sw=1.4),
            dot(28, 29, 2.6, INK), dot(36, 29, 2.6, INK), line("M28 36 L36 36", INK, 1.6),
            line("M8 44 C12 40 16 42 18 46 M56 44 C52 40 48 42 46 46", "#9ad0e8", 2)]


def necro_rat(ic):   # a rat in a purple robe with gold trim, holding a skull staff
    return [line("M52 6 L52 60", "#4a3a2a", 3), circle(ic, 52, 8, 4.6, ramp("#e8e0d0"), sw=1.4), dot(50.5, 7.5, 1, INK), dot(53.5, 7.5, 1, INK), flame(ic, 52, 2, 4, "#6ae05a"),
            body(ic, "M8 60 C6 36 18 20 32 20 C46 20 56 36 54 60 Z", "#5a3a8a"), line("M18 40 C24 46 40 46 46 40", "#ffc83a", 2.4),
            body(ic, "M14 22 C10 14 12 8 18 10 C22 12 22 18 20 22 Z", "#8a8a9a", sw=1.4), body(ic, "M50 22 C54 14 52 8 46 10 C42 12 42 18 44 22 Z", "#8a8a9a", sw=1.4),
            body(ic, "M18 26 C18 16 24 12 32 12 C40 12 46 16 46 26 C46 34 40 38 32 38 C24 38 18 34 18 26 Z", "#9a9aa8"),
            glow_eyes([26, 38], 24, "#6ae05a", 4, 3), dot(32, 32, 2.2, "#e88aa8")]


def nightmare_soldier(ic):   # a dark stone knight holding a glowing green sword
    return [blade("M32 6 L32 60", "#6ae05a", 4), line("M24 36 L40 36", "#4a4a5a", 3.4),
            body(ic, "M8 60 C6 42 14 34 22 32 L42 32 C50 34 58 42 56 60 Z", "#5a5a6a"),
            body(ic, "M18 24 C18 12 24 6 32 6 C40 6 46 12 46 24 L46 34 L18 34 Z", "#6a6a7a"),
            f'<rect x="20" y="20" width="24" height="5" rx="1" fill="{INK}"/>', glow_eyes([27, 37], 22.5, "#b88aff", 4, 2),
            blade("M32 26 L32 60", "#6ae05a", 4)]


def phantom_knight(ic):   # a dark blue knight with teal glowing seams
    return [body(ic, "M6 60 C4 42 12 32 22 30 L42 30 C52 32 60 42 58 60 Z", "#2a3a5a"),
            body(ic, "M4 32 C4 24 10 22 16 24 L20 36 Z", "#3a4a6a", sw=1.4), body(ic, "M60 32 C60 24 54 22 48 24 L44 36 Z", "#3a4a6a", sw=1.4),
            body(ic, "M18 22 C18 10 24 4 32 4 C40 4 46 10 46 22 L46 32 L18 32 Z", "#34466a"),
            f'<rect x="20" y="18" width="24" height="5" rx="1" fill="{INK}"/>', glow_eyes([27, 37], 20.5, "#5af0e0", 5, 2),
            line("M32 36 L32 56 M22 44 L42 44", "#5af0e0", 1.6)]


def predator_prime(ic):   # a green dinosaur beast with orange spikes and a huge maw
    return [body(ic, "M10 60 C8 44 16 36 32 36 C48 36 56 44 54 60 Z", "#2a9a5a"),
            body(ic, "M22 8 L26 2 L28 10 Z M34 6 L38 0 L40 8 Z M44 10 L50 6 L48 14 Z", "#ff8a2a", sw=1.2),
            body(ic, "M8 30 C8 14 18 6 32 6 C46 6 56 14 56 30 C56 42 46 48 32 48 C18 48 8 42 8 30 Z", "#3ab86a"),
            eye(ic, 20, 18, 3.4, "#ffd23a", slit=True), eye(ic, 44, 18, 3.4, "#ffd23a", slit=True), grin(32, 28, 38, 16, 9)]


def radiant_huntress(ic):   # a hooded huntress with a golden sword and a red cape
    return [body(ic, "M40 20 C52 22 62 34 60 60 L44 60 Z", "#b8243a", sw=1.6), blade("M8 58 L28 26", "#ffd23a", 3.4),
            body(ic, "M12 60 C10 44 18 36 32 36 C46 36 54 44 52 60 Z", "#3a2a5a"),
            body(ic, "M14 32 C12 14 22 4 32 4 C42 4 52 14 50 32 C46 40 18 40 14 32 Z", "#4a3a7a"),
            body(ic, "M22 28 C22 20 26 16 32 16 C38 16 42 20 42 28 C42 34 38 36 32 36 C26 36 22 34 22 28 Z", "#f4dcd0", sw=1.2),
            glow_eyes([28, 36], 26, "#5a8aff", 3, 3)]


def rune_wolf(ic):   # a grey wolf with glowing red runes
    return [body(ic, "M8 60 C6 42 16 34 32 34 C48 34 58 42 56 60 Z", "#9a9aa4"),
            body(ic, "M14 20 L10 4 L24 12 Z", "#8a8a94", sw=1.4), body(ic, "M50 20 L54 4 L40 12 Z", "#8a8a94", sw=1.4),
            body(ic, "M12 28 C12 16 20 10 32 10 C44 10 52 16 52 28 C52 36 46 40 40 42 L32 50 L24 42 C18 40 12 36 12 28 Z", "#b0b0ba"),
            glow_eyes([24, 40], 26, "#ff3a3a", 5, 3), dot(32, 44, 2.6, INK),
            line("M20 52 L24 46 L28 52 M38 50 C40 46 44 48 42 52 M16 18 L20 22 M48 18 L44 22", "#ff3a3a", 1.6)]


def sandstorm_seeker(ic):   # a pale sand worm rising in a curve
    return [line("M8 62 C8 44 20 44 22 32 C24 20 20 12 30 8", "#8a6a4a", 16), line("M8 62 C8 44 20 44 22 32 C24 20 20 12 30 8", "#e8c8a8", 12),
            line("M10 52 L18 52 M16 42 L26 44 M20 32 L28 34 M22 22 L30 24", "#b8987a", 1.4),
            body(ic, "M24 12 C26 2 38 0 44 6 C48 10 46 18 40 20 C34 22 26 20 24 12 Z", "#e8c8a8"),
            f'<circle cx="38" cy="12" r="4" fill="{INK}"/>', dot(38, 12, 1.4, "#e2343e"),
            line("M50 50 C54 46 58 48 60 44 M44 58 C50 56 54 60 60 56", "#c8a888", 2)]


def sharpfin(ic):   # a grey shark warrior with an orange blade
    return [blade("M4 60 L22 30", "#ff8a2a", 5),
            body(ic, "M10 60 C8 44 18 36 32 36 C46 36 56 44 54 60 Z", "#6a7a8a"),
            body(ic, "M32 2 L40 14 L28 12 Z", "#6a7a8a", sw=1.4),
            body(ic, "M8 30 C8 18 18 10 32 10 C46 10 56 18 56 30 C56 40 46 46 32 46 C18 46 8 40 8 30 Z", "#8a9aaa"),
            eye(ic, 20, 22, 3.4, INK), eye(ic, 44, 22, 3.4, INK), grin(32, 32, 30, 10, 8),
            line("M12 50 L52 50", "#a83a3a", 3)]


def spiral_sam(ic):   # a purple snail with a big spiral shell
    return [body(ic, "M4 58 C4 50 10 46 20 46 L56 46 C60 46 62 50 60 56 C60 60 56 62 50 62 L10 62 C6 62 4 60 4 58 Z", "#b8a8d8"),
            circle(ic, 34, 30, 22, ramp("#7a5ab8")), line("M34 30 m-4 0 a4 4 0 1 1 8 0 a8 8 0 1 1 -16 0 a12 12 0 1 1 24 0 a16 16 0 1 1 -32 0", "#4a3a78", 2.2),
            line("M12 48 L8 36 M18 46 L16 34", "#b8a8d8", 2.4), dot(8, 35, 2.4, INK), dot(16, 33, 2.4, INK)]


def squiggles(ic):   # a mass of dark purple tentacles with toothy mouths
    return [tentacles("#4a2a6a", ["M10 60 C6 44 14 36 8 24", "M54 60 C58 44 50 36 56 24", "M20 20 C16 10 22 4 18 0", "M44 20 C48 10 42 4 46 0"], 6),
            body(ic, "M10 40 C8 24 18 14 32 14 C46 14 56 24 54 40 C54 54 44 62 32 62 C20 62 10 54 10 40 Z", "#5a3a7a"),
            grin(22, 32, 12, 8, 4), grin(42, 30, 12, 8, 4), grin(32, 46, 14, 9, 5), glow_eyes([20, 44], 24, "#ffd23a", 3, 2)]


def stone_sentinel(ic):   # a mossy stone golem with red vines
    return [body(ic, "M6 60 L8 38 C8 32 12 30 18 30 L46 30 C52 30 56 32 56 38 L58 60 Z", "#8a8a80"),
            body(ic, "M14 30 L16 10 L26 4 L40 4 L50 10 L50 30 C44 36 20 36 14 30 Z", "#a8a89c"),
            body(ic, "M12 12 C18 2 30 0 40 4 C48 2 56 8 54 14 C44 10 22 10 12 12 Z", "#4a9a3a", sw=1.4),
            glow_eyes([26, 38], 20, "#8aff6a", 5, 3), line("M24 28 L40 28", "#6a6a60", 2.4),
            line("M14 40 C20 46 26 38 32 44 C38 50 44 40 50 46", "#c83a3a", 1.8)]


def the_final_chef(ic):   # a black hooded reaper with a great scythe
    return [line("M52 4 L40 62", "#5a3a2a", 3), line("M52 4 C38 2 20 6 10 20 C24 12 38 10 50 12", "#c8ccd8", 3),
            body(ic, "M8 60 C6 40 14 26 32 26 C50 26 58 40 56 60 Z", "#2a2630"),
            body(ic, "M14 34 C12 16 22 6 32 6 C42 6 52 16 50 34 C44 42 20 42 14 34 Z", "#34303c"),
            body(ic, "M22 30 C22 22 26 18 32 18 C38 18 42 22 42 30 C42 36 38 38 32 38 C26 38 22 36 22 30 Z", "#141218", sw=1),
            glow_eyes([28, 36], 28, "#ff5a3a", 3, 2)]


def toxic_drake(ic):   # a purple dragon dripping green poison
    return [wings(ic, "#6a4a9a", 20),
            body(ic, "M14 60 C12 46 20 38 32 38 C44 38 52 46 50 60 Z", "#5a3a8a"),
            body(ic, "M14 30 C12 16 22 8 32 8 C42 8 52 16 50 30 C50 40 44 46 32 46 C20 46 14 40 14 30 Z", "#7a5ab0"),
            horns(ic, "#d8d0e8", False, 12, 12), eye(ic, 24, 24, 3.4, "#8aff4a", slit=True), eye(ic, 40, 24, 3.4, "#8aff4a", slit=True),
            grin(32, 34, 18, 7, 6), line("M28 42 L28 50 M36 42 L36 54", "#8aff4a", 2.4), dot(28, 51, 1.8, "#8aff4a"), dot(36, 55, 1.8, "#8aff4a")]


def triple_trouble(ic):   # a dark armoured beast with three skull heads
    return [body(ic, "M8 62 C6 46 16 36 32 36 C48 36 58 46 56 62 Z", "#3a3a48"),
            body(ic, "M2 24 C2 16 8 12 14 12 C20 12 24 16 24 24 C24 30 20 34 14 34 C8 34 2 30 2 24 Z", "#c8c4d0"),
            body(ic, "M40 24 C40 16 44 12 50 12 C56 12 62 16 62 24 C62 30 56 34 50 34 C44 34 40 30 40 24 Z", "#c8c4d0"),
            body(ic, "M20 18 C20 8 26 2 32 2 C38 2 44 8 44 18 C44 26 38 30 32 30 C26 30 20 26 20 18 Z", "#dcd8e4"),
            dot(9, 22, 2.4, INK), dot(18, 22, 2.4, INK), dot(46, 22, 2.4, INK), dot(55, 22, 2.4, INK),
            dot(27, 16, 3, INK), dot(37, 16, 3, INK), line("M28 25 L36 25 M8 29 L20 29 M44 29 L56 29", INK, 1.4)]


def twilight_terror(ic):   # a red-haired winged sorceress in a dark gown
    return [wings(ic, "#3a2a4a", 24),
            body(ic, "M8 30 C6 12 18 4 32 4 C46 4 58 12 56 30 L58 56 L46 56 L44 36 L20 36 L18 56 L6 56 Z", "#c8243a"),
            body(ic, "M14 62 C12 48 20 42 32 42 C44 42 52 48 50 62 Z", "#3a2240"),
            body(ic, "M20 28 C20 18 25 14 32 14 C39 14 44 18 44 28 C44 36 39 42 32 42 C25 42 20 36 20 28 Z", "#f4dcd0", sw=1.2),
            body(ic, "M18 26 C20 14 26 10 32 10 C38 10 44 14 46 26 C40 20 26 20 18 26 Z", "#c8243a", sw=1.2),
            eye(ic, 27, 29, 2.6, "#e2343e"), eye(ic, 37, 29, 2.6, "#e2343e"), line("M29 36 C31 37 33 37 35 36", "#a8344a", 1.4)]


BOSSES = {
    "Bills Cousin": bills_cousin, "Bound Blaze": bound_blaze, "Brain Storm": brain_storm, "Deep Blue Director": deep_blue_director,
    "Fragment of Madness": fragment_of_madness, "Galactic Tear": galactic_tear, "Goblin King": goblin_king, "Hell's Warden": hells_warden,
    "Horn Havoc": horn_havoc, "Hungry Eye": hungry_eye, "Ice Cube Slime": ice_cube_slime, "King Nothing": king_nothing,
    "Lazy Dweller": lazy_dweller, "Matchstick Mike": matchstick_mike, "Mind's End": minds_end, "Moon Moon": moon_moon,
    "Mr Pupil": mr_pupil, "Muscle Sprout": muscle_sprout, "Necro Rat": necro_rat, "Nightmare Soldier": nightmare_soldier,
    "Phantom Knight": phantom_knight, "Predator Prime": predator_prime, "Radiant Huntress": radiant_huntress, "Rune Wolf": rune_wolf,
    "Sandstorm Seeker": sandstorm_seeker, "Sharpfin": sharpfin, "Spiral Sam": spiral_sam, "Squiggles": squiggles,
    "Stone Sentinel": stone_sentinel, "The Final Chef": the_final_chef, "Toxic Drake": toxic_drake, "Triple Trouble": triple_trouble,
    "Twilight Terror": twilight_terror,
}


def slug(name: str) -> str:
    return "b-" + re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "")).strip("-")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in BOSSES.items():
        ic = Icon()
        ic.add(draw(ic))
        (OUT / f"{slug(name)}.svg").write_text(ic.svg().replace("<svg ", '<svg data-generated="boss_icons.py" ', 1), encoding="utf-8")
    print(f"boss icons: wrote {len(BOSSES)}")


if __name__ == "__main__":
    main()
