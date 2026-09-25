"""Chibi skins like Pixel Odyssey's own (used by tools/goods_icons.py).

The game's skins are simple full-body chibis with a big head: the head is about two thirds of the figure
(hair with a fringe, small dark eyes, a tiny mouth), under it a small body with stubby arms and feet,
sometimes a weapon in hand. Drawn with the same kit as the other icons (outlines, soft gradients), so the
converter makes the pixel versions. Each skin keeps its style, colours and extras from the SKINS table in
tools/skin_icons.py. (Earlier kits, kept outside the repo: the first portraits and the MMO-like v2.)
"""
from __future__ import annotations

from modern_icons import HL, circle, dot, line, shape
from skin_icons import SKINS, extras_color, ramp

INK = "#141216"
TONES = {
    "light": ("#fff6ec", "#ffe4cc", "#e8b898", "#5a3426"),
    "pale": ("#ffffff", "#f6eee6", "#d6c6bc", "#4a3e3a"),
    "tan": ("#fce6cc", "#eec09a", "#c48c62", "#4a2a16"),
    "dark": ("#d8a888", "#a8765a", "#6e4630", "#2a160a"),
}
HUMAN = {"long", "short", "bob", "spiky", "bald", "hood", "hood_dark", "wizard", "hat", "cap", "helmet", "knight", "mask"}
HEAD = "M10 26 C10 12 20 4 32 4 C44 4 54 12 54 26 C54 38 45 45 32 45 C19 45 10 38 10 26 Z"
FACE = "M15 28 C15 20 22 17 32 17 C42 17 49 20 49 28 C49 37 42 43 32 43 C22 43 15 37 15 28 Z"
FRINGE = "M11 27 C10 12 20 4 32 4 C44 4 54 12 53 27 L48 22 L44 27 L39 20 L34 26 L29 20 L24 27 L19 21 L15 28 Z"


def eyes(color, y=31, glow=False):
    if glow:
        return "".join(f'<ellipse cx="{x}" cy="{y}" rx="3" ry="2.2" fill="{color}"/>' for x in (24, 40))
    out = []
    for x in (24, 40):
        out += [f'<ellipse cx="{x}" cy="{y}" rx="2.4" ry="3.4" fill="{INK}"/>', dot(x, y + 1.6, 1.3, color), dot(x - 0.8, y - 1.2, 0.9, HL)]
    return "".join(out)


def body(ic, outfit, hands, weapon=None):
    O = ramp(outfit)
    p = []
    if weapon == "sword":
        p += [line("M50 60 L60 40", "#1e232e", 5.4), line("M50 60 L60 40", "#dfe6f0", 3), line("M46 56 L54 60", "#3a2410", 4.4), line("M46 56 L54 60", "#e0a050", 2.4)]
    elif weapon == "staff":
        p += [line("M52 62 L58 34", "#2a1406", 4.4), line("M52 62 L58 34", "#a8683a", 2.6), circle(ic, 58.5, 32, 3.6, ramp("#8e5ce2"), sw=1.4)]
    p += [
        f'<rect x="23" y="55" width="7" height="7" rx="2.5" fill="#3a3040" stroke="{INK}" stroke-width="1.6"/>',   # feet
        f'<rect x="34" y="55" width="7" height="7" rx="2.5" fill="#3a3040" stroke="{INK}" stroke-width="1.6"/>',
        shape(ic, "M22 42 L42 42 C44 42 45 44 45 46 L45 55 C45 57 44 58 42 58 L22 58 C20 58 19 57 19 55 L19 46 C19 44 20 42 22 42 Z", O, ic.lg(O, 0, 0, 1, 1)),
        shape(ic, "M18 44 C14 45 13 50 14 53 L19 53 L20 45 Z", O, sw=1.6),                                            # arms
        shape(ic, "M46 44 C50 45 51 50 50 53 L45 53 L44 45 Z", O, sw=1.6),
        circle(ic, 16.5, 54, 2.8, hands, sw=1.4), circle(ic, 47.5, 54, 2.8, hands, sw=1.4),                          # hands
    ]
    return "".join(p)


def chibi(ic, style, hair, skin, outfit, extras=(), eye="#3a6ad8", weapon=None):
    ex = set(extras)
    S = TONES.get(skin) or ramp(skin)
    H = ramp(hair)
    human = style in HUMAN
    p = []
    if style == "long":
        p.append(shape(ic, "M10 26 C10 12 20 4 32 4 C44 4 54 12 54 26 L55 50 C51 52 47 50 46 46 L18 46 C17 50 13 52 9 50 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
    if style in ("hood", "hood_dark", "mask"):
        p.append(shape(ic, "M7 44 C5 20 14 3 32 3 C50 3 59 20 57 44 C50 50 14 50 7 44 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
    p.append(body(ic, outfit if human else (S[1] if style not in ("robot",) else "#b8c0cc"), S, weapon))
    if human:
        if style not in ("hood", "hood_dark", "mask", "long"):
            p.append(shape(ic, HEAD, H, ic.lg(H, 0.2, 0, 0.8, 1)))                    # the back of the hair / headgear
        if style == "hood_dark":
            p.append(shape(ic, FACE, ramp("#241c2c"), sw=1.2))
            p.append(eyes(eye, 31, glow=True))
        elif style == "knight":
            p.append(shape(ic, HEAD, H, ic.lg(H, 0.2, 0, 0.8, 1)))
            p.append(f'<rect x="16" y="26" width="32" height="5" rx="1.5" fill="{INK}"/>')
            p.append(line("M32 6 L32 24", H[2], 1.6))
        else:
            p.append(shape(ic, FACE, S, ic.rg(S, 0.45, 0.4, 0.75)))
            p.append(eyes(eye, glow="glow" in ex))
            p.append(line("M30 38.5 C31.5 39.5 32.5 39.5 34 38.5", "#8a4a3a", 1.3))
            if skin in ("light", "pale"):
                p += [dot(19, 35, 2, "#ff8a9a", 0.45), dot(45, 35, 2, "#ff8a9a", 0.45)]
        if style in ("long", "short", "bob", "hood", "mask"):
            p.append(shape(ic, FRINGE, H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style in ("long", "bob"):
            p += [shape(ic, "M11 24 L17 26 L16 40 L11 42 Z", H), shape(ic, "M53 24 L47 26 L48 40 L53 42 Z", H)]
        if style == "spiky":
            p.append(shape(ic, "M11 29 L5 18 L13 17 L10 5 L21 11 L25 0 L32 9 L39 0 L43 11 L54 5 L51 17 L59 18 L53 29 L48 22 L44 27 "
                               "L39 20 L34 26 L29 20 L24 27 L19 21 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style == "bald":
            p.append(shape(ic, "M13 24 C13 10 22 4 32 4 C42 4 51 10 51 24 C46 19 40 17 32 17 C24 17 18 19 13 24 Z", S, ic.lg(S, 0.2, 0, 0.8, 1)))
        if style == "wizard":
            p += [shape(ic, "M3 19 C13 13 51 13 61 19 C53 24 11 24 3 19 Z", H), shape(ic, "M16 17 L34 -2 L41 4 L48 17 Z", H, ic.lg(H, 0.2, 0, 0.8, 1))]
        if style == "hat":
            p += [shape(ic, "M1 17 C11 10 53 10 63 17 C53 22 11 22 1 17 Z", H), shape(ic, "M16 15 C16 6 23 1 32 1 C41 1 48 6 48 15 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)),
                  line("M16 13 L48 13", H[3], 2.2)]
        if style == "cap":
            p += [shape(ic, "M11 20 C11 9 20 3 32 3 C44 3 53 9 53 20 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)), shape(ic, "M30 18 L62 18 C60 23 38 24 30 22 Z", H)]
        if style == "helmet":
            p.append(shape(ic, "M9 30 C8 12 19 3 32 3 C45 3 56 12 55 30 L49 30 L49 21 L15 21 L15 30 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style == "mask":
            p.append(shape(ic, "M16 33 L48 33 C48 39 42 43 32 43 C22 43 16 39 16 33 Z", H))
    else:
        heads = {"blob": "M8 40 C6 18 16 4 32 4 C48 4 58 18 56 40 C52 46 12 46 8 40 Z",
                 "tree": "M10 44 L10 12 C10 6 16 4 22 6 L28 2 L34 6 C42 3 54 6 54 12 L54 44 Z",
                 "stone": "M8 42 L10 12 L22 4 L44 5 L56 12 L56 42 L44 46 L20 46 Z",
                 "robot": "M8 38 L8 12 C8 7 12 5 17 5 L47 5 C52 5 56 7 56 12 L56 38 C56 43 52 45 47 45 L17 45 C12 45 8 43 8 38 Z",
                 "skull": "M11 26 C10 12 19 4 32 4 C45 4 54 12 53 26 C53 32 50 36 47 38 L47 45 L17 45 L17 38 C14 36 11 32 11 26 Z"}
        if style == "cat":
            p += [shape(ic, "M10 18 L12 0 L24 9 Z", S), shape(ic, "M54 18 L52 0 L40 9 Z", S)]
        if style == "bear":
            p += [circle(ic, 14, 9, 6, S), circle(ic, 50, 9, 6, S)]
        if style == "dog":
            p += [shape(ic, "M14 8 C4 10 2 28 8 36 C12 34 14 26 16 18 Z", ramp("#8a5a2a")), shape(ic, "M50 8 C60 10 62 28 56 36 C52 34 50 26 48 18 Z", ramp("#8a5a2a"))]
        if style == "elephant":
            p += [shape(ic, "M14 14 C0 10 0 34 12 38 Z", S), shape(ic, "M50 14 C64 10 64 34 52 38 Z", S)]
        p.append(shape(ic, heads.get(style, HEAD), S, ic.rg(S, 0.4, 0.35, 0.8)))
        if style == "skull":
            p += [f'<ellipse cx="23" cy="25" rx="6" ry="6.5" fill="{INK}"/>', f'<ellipse cx="41" cy="25" rx="6" ry="6.5" fill="{INK}"/>',
                  f'<path d="M32 30 L29 36 L35 36 Z" fill="{INK}"/>', line("M24 41 L24 45 M30 41 L30 45 M36 41 L36 45 M42 41 L42 45", INK, 1.4)]
        elif style == "robot":
            p += [f'<rect x="14" y="16" width="36" height="13" rx="5" fill="{INK}"/>', f'<rect x="18" y="20" width="10" height="5" rx="2" fill="{eye}"/>',
                  f'<rect x="36" y="20" width="10" height="5" rx="2" fill="{eye}"/>', line("M32 5 L32 0", S[3], 2)]
        elif style in ("tree", "stone"):
            p += [line("M16 14 L18 38 M46 12 L48 40" if style == "tree" else "M16 18 L24 22 M40 12 L48 18 M18 38 L26 36", S[2], 1.6), eyes(eye, 26, glow=True)]
        else:
            p.append(eyes(eye, 26, glow=style == "blob" or "glow" in ex))
            if style in ("bear", "dog", "cat"):
                m = ramp("#f4e8d8")
                p += [f'<ellipse cx="32" cy="36" rx="7" ry="5" fill="{m[1]}" stroke="{m[3]}" stroke-width="1.2"/>', dot(32, 34, 2, INK)]
            elif style == "elephant":
                p.append(line("M32 30 C32 38 30 44 26 48", S[3], 6) + line("M32 30 C32 38 30 44 26 48", S[1], 3.8))
            else:
                p += [f'<path d="M24 35 L40 35 L38 39 L26 39 Z" fill="{INK}"/>', f'<path d="M26 35 L28 38 L30 35 Z" fill="#ffffff"/>', f'<path d="M34 35 L36 38 L38 35 Z" fill="#ffffff"/>']
        if style == "cat":
            p.append(line("M10 32 L2 30 M10 36 L2 38 M54 32 L62 30 M54 36 L62 38", S[3], 1.2))
    # extras
    if "stripes" in ex:
        p.append(line("M20 8 L22 14 M32 5 L32 11 M44 8 L42 14 M10 22 L15 24 M54 22 L49 24", INK, 2.2))
    if "stitches" in ex:
        p.append(line("M14 13 L50 13 M20 10 L20 16 M28 10 L28 16 M36 10 L36 16 M44 10 L44 16", S[3], 1.5))
    if "band" in ex:
        p.append(shape(ic, "M11 15 C20 10 44 10 53 15 L53 20 C44 15 20 15 11 20 Z", ramp(extras_color(extras, "band", "#e2343e")), sw=1.4))
    if "crown" in ex:
        p.append(shape(ic, "M21 9 L23 -2 L27 4 L32 -4 L37 4 L41 -2 L43 9 Z", ramp("#ffc83a"), sw=1.4))
    if "horns" in ex:
        hc = ramp(extras_color(extras, "horns", "#f4e8d0"))
        p += [shape(ic, "M14 12 C8 8 6 2 8 -4 C12 2 16 4 20 8 Z", hc, sw=1.6), shape(ic, "M50 12 C56 8 58 2 56 -4 C52 2 48 4 44 8 Z", hc, sw=1.6)]
    if "goggles" in ex:
        g = ramp(extras_color(extras, "goggles", "#8a5a2a"))
        p += [line("M10 14 L54 14", g[3], 3.4), circle(ic, 24, 14, 5.2, ramp("#9ad8ff"), sw=1.8), circle(ic, 40, 14, 5.2, ramp("#9ad8ff"), sw=1.8)]
    if "patch" in ex:
        p += [line("M14 20 L50 34", INK, 1.6), f'<ellipse cx="40" cy="31" rx="4.6" ry="4.2" fill="{INK}"/>']
    if "beard" in ex:
        b = ramp(extras_color(extras, "beard", "#e8e4dc"))
        p.append(shape(ic, "M16 32 C18 42 24 50 32 52 C40 50 46 42 48 32 C44 37 38 40 32 40 C26 40 20 37 16 32 Z", b, ic.lg(b, 0.2, 0, 0.8, 1)))
    if "mouthmask" in ex:
        p.append(shape(ic, "M16 33 L48 33 C48 39 42 43 32 43 C22 43 16 39 16 33 Z", ramp(extras_color(extras, "mouthmask", "#2a2a36")), sw=1.4))
    if "bow" in ex:
        bc = ramp(extras_color(extras, "bow", "#e2343e"))
        p += [shape(ic, "M46 8 L37 2 L37 14 Z", bc, sw=1.4), shape(ic, "M46 8 L55 2 L55 14 Z", bc, sw=1.4), circle(ic, 46, 8, 2.4, bc, sw=1.2)]
    if "flower" in ex:
        fc = extras_color(extras, "flower", "#ff6a8a")
        p += [circle(ic, 14 + dx, 10 + dy, 3, ramp(fc), sw=1) for dx, dy in ((0, -3), (3, 0), (0, 3), (-3, 0))]
        p.append(dot(14, 10, 2, "#ffd23a"))
    if "scar" in ex:
        p.append(line("M19 22 L24 37", "#c83a3a", 2))
    if "blood" in ex:
        p.append(line("M40 4 L42 16 M45 6 L47 14", "#d22a2a", 2.2))
    return "".join(p)


WEAPONS = {3: "sword", 9: "sword", 13: "sword", 19: "sword", 20: "staff", 25: "sword", 29: "sword", 38: "sword", 43: "sword", 85: "sword", 88: "sword"}


def skin_spec(name: str):
    try:
        n = int(name.replace("Skin", "").replace("#", "").strip())
    except ValueError:
        return None
    if n not in SKINS:
        return None
    style, hair, skin, outfit, extras, eye = SKINS[n]
    return lambda ic: chibi(ic, style, hair, skin, outfit, extras, eye, WEAPONS.get(n))
