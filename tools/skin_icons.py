"""PORE's own portraits for the 89 skins (used by tools/goods_icons.py).

Every skin gets a chibi head-and-shoulders portrait from one shared kit, set per skin in SKINS below:
the head style (hair cut, hood, hat, helmet, or a creature's head), its colours, and a few extras
(beard, eye patch, horns, goggles, bow, flower, mask...). Style is ours; only the idea follows the game.
"""
from __future__ import annotations

import colorsys

from modern_icons import HL, circle, dot, f, line, shape

INK = "#141216"
SKIN_TONES = {"light": "#f8d4bc", "tan": "#dcb092", "dark": "#9a7258", "pale": "#f4eeea"}   # soft: the pixel icons add saturation


def ramp(hex_: str):
    """(highlight, mid, shadow, outline) from one colour."""
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)

    def mk(l, s):
        rr, gg, bb = colorsys.hls_to_rgb(hh, max(0, min(1, l)), max(0, min(1, s)))
        return "#%02x%02x%02x" % (round(rr * 255), round(gg * 255), round(bb * 255))
    return (mk(ll + (1 - ll) * 0.45, ss), hex_, mk(ll * 0.62, ss), mk(ll * 0.22, ss * 0.8))


def J(parts) -> str:
    return "".join(J(p) if isinstance(p, (list, tuple)) else (p or "") for p in parts)


HEAD = "M16 30 C16 18 22 12 32 12 C42 12 48 18 48 30 C48 40 42 46 32 46 C22 46 16 40 16 30 Z"


def eyes(color="#2a2440", glow=False, y=32):
    if glow:
        return J([f'<ellipse cx="25" cy="{y}" rx="3" ry="2.4" fill="{color}"/>', f'<ellipse cx="39" cy="{y}" rx="3" ry="2.4" fill="{color}"/>'])
    return J([f'<ellipse cx="25" cy="{y}" rx="2.6" ry="3.4" fill="{INK}"/>', f'<ellipse cx="39" cy="{y}" rx="2.6" ry="3.4" fill="{INK}"/>',
              dot(25, y + 1, 1.3, color), dot(39, y + 1, 1.3, color), dot(24, y - 1.4, 0.9, HL), dot(38, y - 1.4, 0.9, HL)])


def portrait(ic, style="short", hair="#6a4a2a", skin="light", outfit="#4a6ab8", extras=(), eye="#3a6ad8", face=None):
    """style: long, short, bob, spiky, bald, hood, hood_dark, wizard, hat, cap, helmet, knight, mask (ninja),
    or a creature head: creature (round), bear, cat, dog, elephant, blob, skull, tree, stone, robot."""
    ex = set(extras)
    skin_hex = SKIN_TONES.get(skin, skin)
    S, H, O = ramp(skin_hex), ramp(hair), ramp(outfit)
    p = []
    creature = style in ("creature", "bear", "cat", "dog", "elephant", "blob", "skull", "tree", "stone", "robot")
    # shoulders
    p.append(shape(ic, "M8 62 C8 52 16 46 32 46 C48 46 56 52 56 62 Z", O, ic.lg(O, 0, 0, 1, 1)))
    if "collar" in ex:
        p.append(shape(ic, "M24 47 L32 56 L40 47 Z", ramp("#f4f0e8"), sw=1.4))
    # hair or hood behind the head
    if style == "long":
        p.append(shape(ic, "M12 30 C12 14 22 8 32 8 C42 8 52 14 52 30 L54 54 C48 58 44 54 42 50 L22 50 C20 54 16 58 10 54 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
    elif style in ("hood", "hood_dark"):
        p.append(shape(ic, "M10 50 C8 30 14 8 32 8 C50 8 56 30 54 50 C46 54 18 54 10 50 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
    # head
    if style == "cat":
        p += [shape(ic, "M16 22 L18 6 L28 14 Z", S), shape(ic, "M48 22 L46 6 L36 14 Z", S)]
    if style == "bear":
        p += [circle(ic, 18, 14, 6, S), circle(ic, 46, 14, 6, S)]
    if style == "dog":
        p += [shape(ic, "M18 16 C10 16 8 30 12 38 C16 36 18 28 20 22 Z", ramp(face or "#8a5a2a")), shape(ic, "M46 16 C54 16 56 30 52 38 C48 36 46 28 44 22 Z", ramp(face or "#8a5a2a"))]
    if style == "elephant":
        p += [shape(ic, "M18 20 C6 16 4 34 14 38 Z", S), shape(ic, "M46 20 C58 16 60 34 50 38 Z", S)]
    head_d = {"blob": "M14 40 C12 24 20 10 32 10 C44 10 52 24 50 40 C48 46 16 46 14 40 Z",
              "tree": "M16 44 L16 18 C16 12 22 10 26 12 L30 8 L34 12 C40 10 48 12 48 18 L48 44 Z",
              "stone": "M14 42 L16 16 L26 10 L42 11 L50 18 L50 42 L40 46 L22 46 Z",
              "robot": "M14 40 L14 18 C14 14 18 12 22 12 L42 12 C46 12 50 14 50 18 L50 40 C50 44 46 46 42 46 L22 46 C18 46 14 44 14 40 Z"}.get(style, HEAD)
    if style in ("hood_dark",):
        p.append(shape(ic, HEAD, ramp("#241c2c"), sw=1.2))
    else:
        p.append(shape(ic, head_d, S, ic.rg(S, 0.4, 0.35, 0.8)))
    if style == "skull":
        p += [f'<ellipse cx="25" cy="31" rx="5" ry="5.5" fill="{INK}"/>', f'<ellipse cx="39" cy="31" rx="5" ry="5.5" fill="{INK}"/>',
              f'<path d="M32 36 L29.5 41 L34.5 41 Z" fill="{INK}"/>', line("M25 44 L25 47 M30 44 L30 47 M35 44 L35 47 M40 44 L40 47", INK, 1.4)]
    elif style == "robot":
        p += [f'<rect x="19" y="26" width="26" height="10" rx="4" fill="{INK}"/>', f'<rect x="22" y="29" width="7" height="4" rx="1" fill="{eye}"/>',
              f'<rect x="35" y="29" width="7" height="4" rx="1" fill="{eye}"/>', line("M32 12 L32 6", O[3], 2), dot(32, 5, 2.4, eye)]
    elif style == "hood_dark":
        p.append(eyes(eye, glow=True, y=31))
    elif style == "tree":
        p += [line("M20 20 L22 40 M40 18 L42 42 M30 14 L30 22", S[2], 1.4, 0.9), eyes(eye, glow=True, y=31)]
    elif style == "stone":
        p += [line("M20 24 L28 28 M38 20 L44 26 M22 40 L30 38", S[2], 1.6), eyes(eye, glow=True, y=31)]
    elif style == "blob":
        p.append(eyes(eye, glow="glow" in ex, y=30))
    else:
        p.append(eyes(eye, glow="glow" in ex))
        if creature and style in ("bear", "dog", "cat"):
            muzzle = ramp(face or "#f4e8d8")
            p += [f'<ellipse cx="32" cy="40" rx="7" ry="5" fill="{muzzle[1]}" stroke="{muzzle[3]}" stroke-width="1.2"/>', dot(32, 38, 2, INK)]
        elif style == "elephant":
            p.append(line("M32 36 C32 44 30 50 26 52", S[3], 5) + line("M32 36 C32 44 30 50 26 52", S[1], 3.2))
        elif not creature:
            p.append(line("M29.5 40 C31 41 33 41 34.5 40", "#a8584a", 1.4))
            if skin in ("light", "pale"):
                p += [dot(21, 37, 2, "#ff9a9a", 0.55), dot(43, 37, 2, "#ff9a9a", 0.55)]
    if style == "cat":
        p += [line("M16 38 L8 36 M16 40 L8 42 M48 38 L56 36 M48 40 L56 42", S[3], 1.2)]
    if "stripes" in ex:
        p.append(line("M22 16 L24 22 M32 12 L32 18 M42 16 L40 22 M17 28 L21 29 M47 28 L43 29", INK, 2))
    if "stitches" in ex:
        p.append(line("M20 20 L44 20 M24 18 L24 22 M30 18 L30 22 M36 18 L36 22 M42 18 L42 22 M18 38 L46 36", S[3], 1.4))
    # hair / hats on top
    if style == "long" or style == "short" or style == "bob":
        p.append(shape(ic, "M14 30 C12 16 22 8 32 8 C42 8 52 16 50 30 C46 26 44 20 42 18 C36 24 26 24 20 20 C18 24 16 28 14 30 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style == "bob":
            p += [shape(ic, "M14 28 L14 42 C16 44 20 44 20 40 L18 26 Z", H), shape(ic, "M50 28 L50 42 C48 44 44 44 44 40 L46 26 Z", H)]
    elif style == "spiky":
        p.append(shape(ic, "M14 30 L10 20 L18 18 L16 8 L26 14 L30 4 L36 12 L44 6 L44 16 L54 16 L50 30 C46 24 42 20 40 18 C34 22 26 22 22 20 C18 24 16 28 14 30 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
    elif style == "wizard":
        p += [shape(ic, "M8 24 C16 20 48 20 56 24 C50 28 14 28 8 24 Z", H), shape(ic, "M18 23 L34 2 L40 8 L46 23 Z", H, ic.lg(H, 0.2, 0, 0.8, 1))]
    elif style == "hat":
        p += [shape(ic, "M6 24 C14 18 50 18 58 24 C50 28 14 28 6 24 Z", H), shape(ic, "M18 22 C18 12 24 8 32 8 C40 8 46 12 46 22 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)),
              line("M18 20 L46 20", H[3], 2.4)]
    elif style == "cap":
        p += [shape(ic, "M14 26 C14 14 22 8 32 8 C42 8 50 14 50 26 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)), shape(ic, "M30 24 L58 24 C56 28 36 30 30 28 Z", H)]
    elif style in ("helmet", "knight"):
        p.append(shape(ic, "M14 34 C12 18 20 8 32 8 C44 8 52 18 50 34 L46 34 L46 26 L18 26 L18 34 Z" if style == "helmet" else
                       "M14 44 C12 20 20 8 32 8 C44 8 52 20 50 44 L40 46 L40 34 L24 34 L24 46 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style == "knight":
            p.append(f'<rect x="18" y="28" width="28" height="5" rx="1" fill="{INK}"/>')
            p.append(line("M32 8 L32 26", H[2], 1.6))
    elif style == "mask":
        p += [shape(ic, "M14 30 C12 16 22 8 32 8 C42 8 52 16 50 30 L46 28 L18 28 Z", H), shape(ic, "M16 36 L48 36 C48 42 42 46 32 46 C22 46 16 42 16 36 Z", H)]
    elif style == "bald":
        p.append(line("M22 16 C26 13 30 12 34 12", HL, 2, 0.7))
    if "band" in ex:
        p.append(shape(ic, "M15 22 C22 18 42 18 49 22 L49 26 C42 22 22 22 15 26 Z", ramp(extras_color(extras, "band", "#e2343e")), sw=1.4))
    if "crown" in ex:
        p.append(shape(ic, "M20 14 L22 4 L27 10 L32 2 L37 10 L42 4 L44 14 Z", ramp("#ffc83a"), sw=1.4))
    if "horns" in ex:
        hc = ramp(extras_color(extras, "horns", "#f4e8d0"))
        p += [shape(ic, "M18 18 C12 14 10 8 12 2 C16 8 20 10 24 14 Z", hc, sw=1.6), shape(ic, "M46 18 C52 14 54 8 52 2 C48 8 44 10 40 14 Z", hc, sw=1.6)]
    if "goggles" in ex:
        g = ramp(extras_color(extras, "goggles", "#8a5a2a"))
        p += [line("M14 20 L50 20", g[3], 3.4), circle(ic, 24, 20, 5, ramp("#9ad8ff"), sw=2), circle(ic, 40, 20, 5, ramp("#9ad8ff"), sw=2)]
    if "patch" in ex:
        p += [line("M16 24 L48 36", INK, 1.6), f'<ellipse cx="39" cy="32" rx="4.5" ry="4" fill="{INK}"/>']
    if "beard" in ex:
        b = ramp(extras_color(extras, "beard", "#e8e4dc"))
        p.append(shape(ic, "M18 36 C20 44 24 54 32 56 C40 54 44 44 46 36 C42 40 38 42 32 42 C26 42 22 40 18 36 Z", b, ic.lg(b, 0.2, 0, 0.8, 1)))
    if "mouthmask" in ex:
        p.append(shape(ic, "M18 36 L46 36 C46 42 40 46 32 46 C24 46 18 42 18 36 Z", ramp(extras_color(extras, "mouthmask", "#2a2a36")), sw=1.4))
    if "bow" in ex:
        bc = ramp(extras_color(extras, "bow", "#e2343e"))
        p += [shape(ic, "M44 12 L36 6 L36 18 Z", bc, sw=1.4), shape(ic, "M44 12 L52 6 L52 18 Z", bc, sw=1.4), circle(ic, 44, 12, 2.4, bc, sw=1.2)]
    if "flower" in ex:
        fc = extras_color(extras, "flower", "#ff6a8a")
        p += [circle(ic, 16 + dx, 16 + dy, 3, ramp(fc), sw=1) for dx, dy in ((0, -3), (3, 0), (0, 3), (-3, 0))]
        p.append(dot(16, 16, 2, "#ffd23a"))
    if "scar" in ex:
        p.append(line("M22 22 L28 40", "#c83a3a", 2))
    if "blood" in ex:
        p.append(line("M40 10 L42 22 M44 12 L46 20", "#d22a2a", 2.2))
    return J(p)


def extras_color(extras, name, default):
    for e in extras:
        if isinstance(e, str) and e.startswith(name + ":"):
            return e.split(":", 1)[1]
    return default


def _x(*names):
    """extras list; 'name:#colour' sets that extra's colour and also switches it on."""
    out = []
    for n in names:
        out.append(n)
        if ":" in n:
            out.append(n.split(":", 1)[0])
    return tuple(out)


# (style, hair or hat colour, skin, outfit colour, extras, eye colour)
SKINS = {
    1: ("long", "#f09ab8", "light", "#f4f0e8", _x(), "#e2346a"),
    2: ("long", "#ffd84a", "light", "#5cc24a", _x("band:#5cc24a"), "#3a9a3a"),
    3: ("helmet", "#c0c8d4", "light", "#8a5a2a", _x(), "#3a6ad8"),
    4: ("wizard", "#6a4aa8", "pale", "#4a3a7a", _x(), "#8e5ce2"),
    5: ("long", "#e8ecf4", "pale", "#c8d0e0", _x(), "#8a98c0"),
    6: ("long", "#f0a040", "light", "#c83a3a", _x(), "#c86a1a"),
    7: ("knight", "#b8c0cc", "light", "#8a929e", _x(), "#3a6ad8"),
    8: ("knight", "#e0a830", "light", "#a8781a", _x(), "#3a6ad8"),
    9: ("short", "#2a2430", "light", "#3a4a6a", _x(), "#3a3a4a"),
    10: ("short", "#f0d070", "light", "#6a7a9a", _x("goggles:#6a5a4a"), "#3a6ad8"),
    11: ("bob", "#f4c8d8", "pale", "#e8a8c0", _x("flower:#ffffff"), "#e2346a"),
    12: ("hood", "#f4f0e8", "light", "#e8d8b8", _x("band:#ffc83a"), "#e2346a"),
    13: ("bob", "#8aa83a", "light", "#8a3a2a", _x(), "#3a8a3a"),
    14: ("long", "#1e1a24", "pale", "#e8ecf4", _x(), "#3a6ad8"),
    15: ("long", "#f4b0c8", "pale", "#e8ecf4", _x("goggles:#8ab8d8"), "#e2346a"),
    16: ("long", "#d8dce8", "pale", "#b8c0d4", _x("bow:#8a98c0"), "#8a98c0"),
    17: ("hat", "#8aa83a", "light", "#e8ecf4", _x(), "#e2346a"),
    18: ("creature", "#5a8a3a", "#7ec84a", "#6a4a2a", _x(), "#e2343e"),
    19: ("short", "#c8ccd8", "light", "#6a4a3a", _x(), "#5a6a8a"),
    20: ("wizard", "#8a8a9a", "light", "#6a6a7a", _x("beard:#e8e4dc"), "#3a3a4a"),
    21: ("short", "#6a4a2a", "light", "#f4f0e8", _x("band:#f4f0e8"), "#6a4a2a"),
    22: ("bob", "#6a5a9a", "light", "#8a4aa8", _x("crown"), "#e2346a"),
    23: ("hat", "#7a4a2a", "light", "#c83a3a", _x(), "#6a4a2a"),
    24: ("long", "#6ae0a0", "light", "#e8a040", _x(), "#1c8a5a"),
    25: ("mask", "#2a2a36", "light", "#2a2a36", _x(), "#e8e8f0"),
    26: ("hood_dark", "#a82a3a", "light", "#8a1a2a", _x(), "#f4f0e8"),
    27: ("knight", "#6a6a7a", "light", "#4a4a5a", _x(), "#e8e8f0"),
    28: ("helmet", "#7a7a8a", "pale", "#5a5a6a", _x("mouthmask:#4a4a5a"), "#3a3a4a"),
    29: ("bald", "#e0a878", "tan", "#e8a040", _x("patch", "scar"), "#3a3a4a"),
    30: ("bald", "#e0a878", "tan", "#3a8a3a", _x("beard:#8a8a8a"), "#3a3a4a"),
    31: ("spiky", "#ff9a2a", "light", "#2a2a36", _x("mouthmask:#f4f0e8"), "#3a8a3a"),
    32: ("elephant", "#6a6a8a", "#8a8aa8", "#5a5a7a", _x(), "#2a2a36"),
    33: ("tree", "#6a4a2a", "#8a5a34", "#5a3a1a", _x(), "#ffd23a"),
    34: ("blob", "#b8bcc8", "#c8ccd8", "#8a8e9a", _x(), "#2a2a36"),
    35: ("skull", "#f4f0e8", "#f4f0e8", "#c8c4bc", _x(), "#2a2a36"),
    36: ("short", "#8a5a2a", "light", "#6a4a2a", _x("goggles:#8a929e"), "#c86a1a"),
    37: ("spiky", "#ffe070", "light", "#f4f0e8", _x("horns:#f4f0e8"), "#e2343e"),
    38: ("hat", "#6a4a2a", "light", "#8a5a3a", _x(), "#3a3a4a"),
    39: ("short", "#2a2430", "light", "#c83a3a", _x("bow:#e2343e"), "#e2343e"),
    40: ("long", "#d8dce8", "dark", "#3a3a4a", _x(), "#e8a040"),
    41: ("short", "#2a2430", "light", "#f4f0e8", _x("band:#f4f0e8"), "#3a8a3a"),
    42: ("bob", "#f4e8d0", "pale", "#f4f0e8", _x(), "#8a98c0"),
    43: ("short", "#1e1a24", "light", "#3a3a4a", _x(), "#3a3a4a"),
    44: ("cat", "#ff9a2a", "#ffa040", "#e8e4dc", _x("stripes"), "#3a8a3a"),
    45: ("robot", "#f4f8fc", "#e8ecf4", "#b8c0cc", _x(), "#4ae0ff"),
    46: ("bear", "#8a5a34", "#9a6a3a", "#e8e4dc", _x(), "#2a2a36"),
    47: ("long", "#9ad8ff", "pale", "#4a8ae0", _x("flower:#ffd23a"), "#2a6ad8"),
    48: ("short", "#1e1a24", "light", "#2a3a5a", _x(), "#3a6ad8"),
    49: ("hat", "#5a8a3a", "light", "#e8a040", _x(), "#3a8a3a"),
    50: ("short", "#f0a040", "light", "#8a5a2a", _x("goggles:#6a4a2a"), "#3a8a3a"),
    51: ("bear", "#6a6a5a", "#7a7a6a", "#4a4a3a", _x("mouthmask:#3a3a34"), "#e8e070"),
    52: ("cat", "#3a3440", "#4a4454", "#2a2430", _x(), "#e8e070"),
    53: ("blob", "#e8f0f8", "#f0f6fc", "#b8c8d8", _x(), "#4a8ae0"),
    54: ("creature", "#6a9a3a", "#8ab84a", "#5a7a2a", _x(), "#e8e070"),
    55: ("tree", "#8a5a2a", "#a8783a", "#6a4a1a", _x(), "#2a2a36"),
    56: ("blob", "#5a5a6a", "#6a6a7a", "#4a4a5a", _x(), "#e8e8f0"),
    57: ("blob", "#3a8a3a", "#4aa84a", "#2a6a2a", _x("flower:#e2343e"), "#1a3a1a"),
    58: ("creature", "#e8dcc4", "#e8dcc4", "#c8b898", _x("stitches"), "#e2343e"),
    59: ("dog", "#d8a860", "#e8c080", "#3a8a3a", _x(), "#2a2a36"),
    60: ("bob", "#f4b0a0", "light", "#c83a5a", _x("scar"), "#3a8a3a"),
    61: ("spiky", "#3a8ad8", "light", "#3a6a4a", _x(), "#3a8a3a"),
    62: ("long", "#a82a3a", "light", "#3a8a3a", _x("flower:#ffd23a"), "#3a8a3a"),
    63: ("spiky", "#ffb020", "light", "#e8e070", _x(), "#e2343e"),
    64: ("long", "#f07ab0", "light", "#e8ecf4", _x("bow:#e2346a"), "#e2346a"),
    65: ("hood", "#3a8a3a", "light", "#2a6a2a", _x(), "#3a8a3a"),
    66: ("hat", "#d8c8a8", "light", "#a8906a", _x(), "#3a3a4a"),
    67: ("short", "#2a2430", "light", "#2a2430", _x("glow", "blood"), "#e2343e"),
    68: ("bob", "#e8e4dc", "pale", "#8a8e9a", _x(), "#5a6a8a"),
    69: ("stone", "#5a6a6a", "#6a7a7a", "#4a5a5a", _x(), "#8ae0d8"),
    70: ("hood_dark", "#5a7a2a", "light", "#4a6a1a", _x(), "#ffe23a"),
    71: ("hood_dark", "#5a3a24", "light", "#4a2a18", _x(), "#e8e070"),
    72: ("bob", "#2a2430", "light", "#f4f0e8", _x("bow:#f09ab8"), "#3a3a4a"),
    73: ("bob", "#8a5a3a", "light", "#6a8a4a", _x(), "#6a4a2a"),
    74: ("long", "#f0909a", "light", "#3a6ad8", _x(), "#3a6ad8"),
    75: ("creature", "#6a8a2a", "#7a9a3a", "#5a4a2a", _x("horns:#e8e4dc"), "#e2343e"),
    76: ("stone", "#a8906a", "#b8a078", "#8a7250", _x("stitches"), "#2a2a36"),
    77: ("hood", "#4a6a3a", "#6a8a4a", "#3a5a2a", _x("mouthmask:#3a4a2a"), "#e8e070"),
    78: ("hood_dark", "#7a5a3a", "light", "#5a3a24", _x(), "#fff6c0"),
    79: ("hood", "#f4f0e8", "light", "#f4f0e8", _x(), "#3a8a3a"),
    80: ("stone", "#8a8e96", "#a0a4ac", "#6a6e76", _x(), "#2a2a36"),
    81: ("long", "#ffe08a", "light", "#8a3a2a", _x(), "#3a6ad8"),
    82: ("creature", "#6a8a8a", "#8aa8a8", "#4a6a6a", _x("stitches"), "#e8e070"),
    83: ("creature", "#4a7a2a", "#5a8a34", "#4a3a24", _x("mouthmask:#3a2a1a"), "#e2343e"),
    84: ("creature", "#a82a2a", "#c83a3a", "#6a1a1a", _x("horns:#2a2430"), "#ffe23a"),
    85: ("short", "#6a6e7a", "light", "#4a4e5a", _x(), "#5a6a8a"),
    86: ("long", "#f07a9a", "light", "#c8506a", _x(), "#e2346a"),
    87: ("cap", "#3a6ad8", "light", "#f4f0e8", _x(), "#3a6ad8"),
    88: ("short", "#1e1a24", "light", "#2a2430", _x("band:#e2343e"), "#e2343e"),
    89: ("long", "#f4f0e8", "pale", "#f4f0e8", _x("blood"), "#e2343e"),
}


def skin_spec(name: str):
    try:
        n = int(name.replace("Skin", "").replace("#", "").strip())
    except ValueError:
        return None
    if n not in SKINS:
        return None
    style, hair, skin, outfit, extras, eye = SKINS[n]
    return lambda ic: portrait(ic, style, hair, skin, outfit, extras, eye)
