"""Game-style skin portraits (used by tools/goods_icons.py).

Like the game's own skins, the head fills the frame: big hair with bangs down to the eyes and side locks,
large anime eyes with a dark lash line, no nose, pale skin, a sliver of outfit at the bottom and sometimes
a weapon at the side. Creatures are bulky heads that fill the frame too. Every skin keeps its own style,
colours and extras from the SKINS table in tools/skin_icons.py (the first, simpler portrait kit).
"""
from __future__ import annotations

from modern_icons import HL, circle, dot, line, shape
from skin_icons import SKINS, extras_color, ramp

INK = "#141216"
TONES = {   # hand-set ramps (light, mid, shadow, outline): pale, never orange
    "light": ("#fff8f2", "#fde4d6", "#eab8a6", "#6a3a36"),
    "pale": ("#ffffff", "#f6ece8", "#d8c4c0", "#5a4a4a"),
    "tan": ("#fce8d4", "#eec4a0", "#c8906c", "#5a3422"),
    "dark": ("#d8a888", "#a8765a", "#6e4630", "#2e180c"),
}
FACE = "M17 28 C17 19 23 15 32 15 C41 15 47 19 47 28 L47 36 C47 45 40 50 32 50 C24 50 17 45 17 36 Z"
BANGS = ("M11 31 C10 14 19 5 32 5 C45 5 54 14 53 31 L49 25 L46 31 L42 24 L38 30 L34 23 L30 30 L26 24 "
         "L22 31 L19 25 L15 32 Z")
HUMAN = {"long", "short", "bob", "spiky", "bald", "hood", "hood_dark", "wizard", "hat", "cap", "helmet", "knight", "mask"}


def eyes(color, y=37, glow=False):
    if glow:
        return "".join(f'<rect x="{x}" y="{y - 2}" width="6" height="4" rx="1" fill="{color}"/>' for x in (21, 37))
    out = []
    for x in (24.5, 39.5):
        out += [f'<rect x="{x - 4.5}" y="{y - 5}" width="9" height="2.4" rx="1" fill="{INK}"/>',
                f'<ellipse cx="{x}" cy="{y}" rx="3" ry="3.8" fill="{INK}"/>',
                f'<ellipse cx="{x}" cy="{y + 0.8}" rx="2" ry="2.6" fill="{color}"/>',
                dot(x - 1, y - 1.2, 1.1, HL)]
    return "".join(out)


def weapon(ic, kind):
    if kind == "sword":
        return "".join([line("M4 62 L20 38", "#1e232e", 6), line("M4 62 L20 38", "#c4ccd8", 3.4),
                        line("M13 56 L7 50", "#3a2410", 4), line("M13 56 L7 50", "#e0a050", 2.2)])
    if kind == "staff":
        return "".join([line("M6 64 L18 30", "#2a1406", 5), line("M6 64 L18 30", "#a8683a", 3), circle(ic, 19, 27, 4, ramp("#8e5ce2"), sw=1.6)])
    return ""


def portrait(ic, style, hair, skin, outfit, extras=(), eye="#3a6ad8", weapon_=None):
    ex = set(extras)
    S = TONES.get(skin) or ramp(skin)
    H, O = ramp(hair), ramp(outfit)
    p = []
    if weapon_:
        p.append(weapon(ic, weapon_))
    # a sliver of outfit at the bottom, with a collar
    p.append(shape(ic, "M12 64 L15 55 C18 50 24 48 32 48 C40 48 46 50 49 55 L52 64 Z", O, ic.lg(O, 0, 0, 1, 1)))
    p.append(shape(ic, "M26 49 L32 56 L38 49 Z", ramp("#f4f0e8") if "collar" in ex or style in HUMAN else O, sw=1.4))
    if style in HUMAN:
        # hair (or hood) behind the head
        if style == "long":
            p.append(shape(ic, "M8 30 C7 12 18 3 32 3 C46 3 57 12 56 30 L58 60 L48 60 L46 44 L18 44 L16 60 L6 60 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        elif style in ("bob", "short", "spiky", "helmet", "cap", "hat", "wizard"):
            p.append(shape(ic, "M9 30 C8 12 19 4 32 4 C45 4 56 12 55 30 L54 46 L46 44 L18 44 L10 46 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        elif style in ("hood", "hood_dark", "mask"):
            p.append(shape(ic, "M6 56 C4 30 12 4 32 4 C52 4 60 30 58 56 C48 60 16 60 6 56 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        # face
        if style == "hood_dark":
            p.append(shape(ic, FACE, ramp("#241c2c"), sw=1.2))
            p.append(eyes(eye, 34, glow=True))
        else:
            p.append(shape(ic, FACE, S, ic.rg(S, 0.45, 0.4, 0.75)))
            p.append(eyes(eye, glow="glow" in ex))
            p.append(line("M30 45 C31.5 46 32.5 46 34 45", "#a8584a", 1.4))
            if skin in ("light", "pale"):
                p += [dot(20, 42, 2, "#ff8a9a", 0.5), dot(44, 42, 2, "#ff8a9a", 0.5)]
        # bangs, side locks and headgear
        if style in ("long", "short", "bob", "hood", "wizard", "hat", "cap"):
            p.append(shape(ic, BANGS, H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style in ("long", "bob"):
            p += [shape(ic, "M11 28 L18 30 L18 48 L12 52 Z", H), shape(ic, "M53 28 L46 30 L46 48 L52 52 Z", H)]
        if style == "spiky":
            p.append(shape(ic, "M10 32 L4 20 L13 18 L10 6 L21 12 L25 1 L32 10 L39 1 L43 12 L54 6 L51 18 L60 20 L54 32 L49 25 L45 31 "
                               "L41 24 L37 30 L33 23 L29 30 L25 24 L21 31 L17 25 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style == "bald":
            p.append(shape(ic, "M17 28 C17 12 24 8 32 8 C40 8 47 12 47 28 C44 22 40 20 32 20 C24 20 20 22 17 28 Z", S, ic.lg(S, 0.2, 0, 0.8, 1)))
        if style == "wizard":
            p += [shape(ic, "M4 22 C14 16 50 16 60 22 C52 28 12 28 4 22 Z", H), shape(ic, "M16 20 L34 0 L42 6 L48 20 Z", H, ic.lg(H, 0.2, 0, 0.8, 1))]
        if style == "hat":
            p += [shape(ic, "M2 20 C12 13 52 13 62 20 C52 25 12 25 2 20 Z", H), shape(ic, "M16 18 C16 8 23 3 32 3 C41 3 48 8 48 18 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)),
                  line("M16 16 L48 16", H[3], 2.4)]
        if style == "cap":
            p += [shape(ic, "M11 22 C11 10 20 4 32 4 C44 4 53 10 53 22 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)), shape(ic, "M30 20 L62 20 C60 25 38 27 30 25 Z", H)]
        if style == "helmet":
            p.append(shape(ic, "M10 34 C8 14 18 4 32 4 C46 4 56 14 54 34 L48 34 L48 26 L16 26 L16 34 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
        if style == "knight":
            p.append(shape(ic, "M8 52 C6 18 16 4 32 4 C48 4 58 18 56 52 L44 52 L44 40 L20 40 L20 52 Z", H, ic.lg(H, 0.2, 0, 0.8, 1)))
            p.append(f'<rect x="14" y="32" width="36" height="6" rx="1" fill="{INK}"/>')
            p.append(line("M32 6 L32 30", H[2], 1.6))
        if style == "mask":
            p += [shape(ic, "M12 32 C10 16 20 8 32 8 C44 8 54 16 52 32 L46 30 L18 30 Z", H), shape(ic, "M16 40 L48 40 C48 46 42 50 32 50 C22 50 16 46 16 40 Z", H)]
    else:
        # creatures: a bulky head that fills the frame
        heads = {"blob": "M6 48 C4 24 14 6 32 6 C50 6 60 24 58 48 C54 56 10 56 6 48 Z",
                 "tree": "M8 54 L8 14 C8 6 16 4 22 6 L28 2 L34 6 C42 3 56 6 56 14 L56 54 Z",
                 "stone": "M6 52 L8 14 L22 4 L44 5 L58 14 L58 52 L44 58 L20 58 Z",
                 "robot": "M6 48 L6 14 C6 8 10 6 16 6 L48 6 C54 6 58 8 58 14 L58 48 C58 54 54 56 48 56 L16 56 C10 56 6 54 6 48 Z",
                 "skull": "M10 32 C8 14 18 4 32 4 C46 4 56 14 54 32 C54 40 50 44 48 46 L48 54 L16 54 L16 46 C14 44 10 40 10 32 Z"}
        head = heads.get(style, "M8 34 C6 14 18 5 32 5 C46 5 58 14 56 34 C56 48 46 56 32 56 C18 56 8 48 8 34 Z")
        if style == "cat":
            p += [shape(ic, "M8 22 L10 2 L24 12 Z", S), shape(ic, "M56 22 L54 2 L40 12 Z", S)]
        if style == "bear":
            p += [circle(ic, 12, 10, 7, S), circle(ic, 52, 10, 7, S)]
        if style == "dog":
            p += [shape(ic, "M12 10 C2 12 0 32 6 42 C10 40 12 30 14 22 Z", ramp("#8a5a2a")), shape(ic, "M52 10 C62 12 64 32 58 42 C54 40 52 30 50 22 Z", ramp("#8a5a2a"))]
        if style == "elephant":
            p += [shape(ic, "M12 16 C-2 12 -2 38 10 42 Z", S), shape(ic, "M52 16 C66 12 66 38 54 42 Z", S)]
        p.append(shape(ic, head, S, ic.rg(S, 0.4, 0.35, 0.8)))
        if style == "skull":
            p += [f'<ellipse cx="22" cy="30" rx="7" ry="7.5" fill="{INK}"/>', f'<ellipse cx="42" cy="30" rx="7" ry="7.5" fill="{INK}"/>',
                  f'<path d="M32 36 L28.5 43 L35.5 43 Z" fill="{INK}"/>', line("M22 50 L22 54 M28 50 L28 54 M34 50 L34 54 M40 50 L40 54", INK, 1.6)]
        elif style == "robot":
            p += [f'<rect x="12" y="20" width="40" height="16" rx="6" fill="{INK}"/>', f'<rect x="16" y="25" width="12" height="6" rx="2" fill="{eye}"/>',
                  f'<rect x="36" y="25" width="12" height="6" rx="2" fill="{eye}"/>', line("M22 46 L42 46", S[3], 2)]
        elif style in ("tree", "stone"):
            p += [line("M14 16 L16 44 M48 14 L50 46 M30 8 L30 16" if style == "tree" else "M14 20 L24 26 M42 14 L50 22 M16 44 L26 42", S[2], 1.8),
                  eyes(eye, 30, glow=True), line("M24 44 L40 44", S[3], 2.4)]
        else:
            glow = style in ("blob",) or "glow" in ex
            p.append(eyes(eye, 30 if style == "blob" else 32, glow=glow))
            if style in ("bear", "dog", "cat"):
                m = ramp("#f4e8d8")
                p += [f'<ellipse cx="32" cy="44" rx="9" ry="6.5" fill="{m[1]}" stroke="{m[3]}" stroke-width="1.2"/>', dot(32, 41, 2.4, INK)]
            elif style == "elephant":
                p.append(line("M32 38 C32 48 30 54 24 58", S[3], 7) + line("M32 38 C32 48 30 54 24 58", S[1], 4.6))
            else:
                p.append(f'<path d="M22 44 L42 44 L40 48 L24 48 Z" fill="{INK}"/>')
                p += [f'<path d="M25 44 L27 47 L29 44 Z" fill="#ffffff"/>', f'<path d="M35 44 L37 47 L39 44 Z" fill="#ffffff"/>']
        if style == "cat":
            p.append(line("M8 40 L-2 38 M8 44 L-2 46 M56 40 L66 38 M56 44 L66 46", S[3], 1.2))
    # extras
    if "stripes" in ex:
        p.append(line("M20 10 L22 18 M32 6 L32 14 M44 10 L42 18 M8 28 L14 30 M56 28 L50 30", INK, 2.4))
    if "stitches" in ex:
        p.append(line("M14 16 L50 16 M20 13 L20 19 M28 13 L28 19 M36 13 L36 19 M44 13 L44 19", S[3], 1.6))
    if "band" in ex:
        p.append(shape(ic, "M11 18 C20 13 44 13 53 18 L53 23 C44 18 20 18 11 23 Z", ramp(extras_color(extras, "band", "#e2343e")), sw=1.4))
    if "crown" in ex:
        p.append(shape(ic, "M20 12 L22 0 L27 7 L32 -2 L37 7 L42 0 L44 12 Z", ramp("#ffc83a"), sw=1.4))
    if "horns" in ex:
        hc = ramp(extras_color(extras, "horns", "#f4e8d0"))
        p += [shape(ic, "M14 14 C8 10 6 4 8 -2 C12 4 16 6 20 10 Z", hc, sw=1.6), shape(ic, "M50 14 C56 10 58 4 56 -2 C52 4 48 6 44 10 Z", hc, sw=1.6)]
    if "goggles" in ex:
        g = ramp(extras_color(extras, "goggles", "#8a5a2a"))
        p += [line("M9 16 L55 16", g[3], 3.6), circle(ic, 23, 16, 6, ramp("#9ad8ff"), sw=2), circle(ic, 41, 16, 6, ramp("#9ad8ff"), sw=2)]
    if "patch" in ex:
        p += [line("M14 22 L50 38", INK, 1.8), f'<ellipse cx="39.5" cy="37" rx="5.5" ry="5" fill="{INK}"/>']
    if "beard" in ex:
        b = ramp(extras_color(extras, "beard", "#e8e4dc"))
        p.append(shape(ic, "M16 38 C18 48 24 60 32 62 C40 60 46 48 48 38 C44 43 38 46 32 46 C26 46 20 43 16 38 Z", b, ic.lg(b, 0.2, 0, 0.8, 1)))
    if "mouthmask" in ex:
        p.append(shape(ic, "M16 40 L48 40 C48 47 41 51 32 51 C23 51 16 47 16 40 Z", ramp(extras_color(extras, "mouthmask", "#2a2a36")), sw=1.4))
    if "bow" in ex:
        bc = ramp(extras_color(extras, "bow", "#e2343e"))
        p += [shape(ic, "M46 10 L36 3 L36 17 Z", bc, sw=1.4), shape(ic, "M46 10 L56 3 L56 17 Z", bc, sw=1.4), circle(ic, 46, 10, 2.6, bc, sw=1.2)]
    if "flower" in ex:
        fc = extras_color(extras, "flower", "#ff6a8a")
        p += [circle(ic, 14 + dx, 12 + dy, 3.4, ramp(fc), sw=1) for dx, dy in ((0, -3.4), (3.4, 0), (0, 3.4), (-3.4, 0))]
        p.append(dot(14, 12, 2.2, "#ffd23a"))
    if "scar" in ex:
        p.append(line("M20 26 L26 44", "#c83a3a", 2.2))
    if "blood" in ex:
        p.append(line("M40 6 L42 20 M45 8 L47 18", "#d22a2a", 2.4))
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
    return lambda ic: portrait(ic, style, hair, skin, outfit, extras, eye, WEAPONS.get(n))
