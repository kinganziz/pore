#!/usr/bin/env python3
"""Draw the modern PORE icon set: one new SVG per equipment item -> icons/modern/<key>.svg

Every icon is specified individually in SPECS below (silhouette, shape variant, palette, trims,
gems, details), based on the item's original sprite, and rendered with a shared set of drawing
primitives so the whole set has one consistent style: 64-unit grid, soft top-left light, dark
outline, gradient fills and a white highlight.

Hand-drawn files are never overwritten unless --force is given (the charms are drawn by hand).

Usage: python tools/modern_icons.py [--force] [--only "Name,Name"]
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"

# ----------------------------------------------------------------------------- palettes
# (highlight, mid, shadow, outline)
PAL = {
    "wood": ("#f2b884", "#b8703e", "#6e3c20", "#2c180c"),
    "darkwood": ("#b88a64", "#7a4e32", "#46291a", "#1c100a"),
    "leather": ("#9a7a66", "#5e4436", "#35251d", "#150e0a"),
    "copper": ("#ffcba2", "#d27c4a", "#7e3b22", "#2e140c"),
    "iron": ("#fbf6ec", "#cfc6b4", "#877e6e", "#2b2620"),
    "steel": ("#f2f6fc", "#aeb9cc", "#5c687e", "#1e232e"),
    "slate": ("#c8d0dc", "#7c8698", "#444c5c", "#181c24"),
    "silver": ("#ffffff", "#dcd8d0", "#908a80", "#2a2622"),
    "gold": ("#fff2a6", "#f6b62e", "#b0600c", "#3a1e06"),
    "platinum": ("#ffffff", "#cfdbe8", "#7c8ca8", "#232a3a"),
    "platring": ("#dcefe6", "#90aa9e", "#465a52", "#161e1a"),
    "azurite": ("#a6dcff", "#3a80e8", "#183a88", "#0a1636"),
    "purpurite": ("#ffc8f4", "#d36ad8", "#74308e", "#260e36"),
    "bogsteel": ("#d4ecc4", "#80aa84", "#40604a", "#16221a"),
    "volcanic": ("#6e6874", "#3a363f", "#1c1a20", "#08070a"),
    "lava": ("#fff4a6", "#ffa03c", "#d8421c", "#4e1206"),
    "fire": ("#fff2a0", "#ffa23a", "#e04a1c", "#4e1206"),
    "emerald": ("#bfffdc", "#46c48c", "#1c6a4c", "#0a281c"),
    "mint": ("#e6fff2", "#8ff0c0", "#2e9a78", "#0c3024"),
    "ruby": ("#ffb8c0", "#ea3450", "#8a1024", "#360610"),
    "red": ("#ff9a9a", "#e2343e", "#8a1420", "#2c0608"),
    "crimson": ("#ff9aac", "#d23c5c", "#7a1834", "#2a0814"),
    "sapphire": ("#c4e8ff", "#4aa8ff", "#1a5ab8", "#0a2450"),
    "cyan": ("#d4fcff", "#48d8f2", "#1a7c9c", "#08303c"),
    "ice": ("#ffffff", "#c2ecff", "#5aa8e2", "#143c66"),
    "amethyst": ("#e8d0ff", "#9a64ff", "#4c26b2", "#1a0a48"),
    "violet": ("#dcc0ff", "#8e5ce2", "#4a2a8e", "#180a38"),
    "pink": ("#ffdcef", "#f07cb8", "#a8387a", "#3a0e2e"),
    "magenta": ("#ff96cc", "#c83280", "#6c1648", "#260616"),
    "plum": ("#8e70a0", "#56395f", "#2e1e36", "#120a16"),
    "brownplate": ("#b07c64", "#6c4032", "#3a2018", "#160a06"),
    "leaf": ("#d0f7a0", "#5cc24a", "#28782c", "#0c2c10"),
    "olive": ("#e8e070", "#b4a42a", "#6c6212", "#262206"),
    "bone": ("#fffaf0", "#e8dabe", "#a8977e", "#38323e"),
    "shadow": ("#70708e", "#3c3c56", "#1e1e2e", "#0a0a12"),
    "navy": ("#5a88c0", "#1f4a7e", "#0f2646", "#050e1c"),
    "sand": ("#fff0d6", "#d8c09c", "#8e7658", "#2e2418"),
    "salmon": ("#ffd6c0", "#e8987c", "#9c5446", "#361810"),
    "chocolate": ("#d6987a", "#8e4c36", "#4a2418", "#1c0a06"),
    "yellow": ("#fff6a8", "#ffd23a", "#d08a10", "#3c2404"),
    "white": ("#ffffff", "#e6e8ee", "#a0a6b4", "#2a2c34"),
    "teal": ("#c6fff4", "#4cc8b4", "#1c6c68", "#082826"),
    "orange": ("#ffd8a0", "#ff9a3a", "#c24e14", "#401404"),
    "moon": ("#ffffff", "#e0d8f4", "#9486b8", "#241c40"),
    "cream": ("#fffdf2", "#f1e6c8", "#b9a888", "#3a3226"),
}
HL = "#ffffff"


# ----------------------------------------------------------------------------- canvas
class Icon:
    def __init__(self) -> None:
        self.defs: list[str] = []
        self.parts: list[str] = []
        self.n = 0

    def _id(self) -> str:
        self.n += 1
        return f"g{self.n}"

    def lg(self, pal, x1=0.0, y1=0.0, x2=1.0, y2=1.0) -> str:
        """Linear gradient in object bounding box units."""
        i = self._id()
        self.defs.append(
            f'<linearGradient id="{i}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{pal[0]}"/><stop offset=".55" stop-color="{pal[1]}"/>'
            f'<stop offset="1" stop-color="{pal[2]}"/></linearGradient>')
        return f"url(#{i})"

    def lgu(self, pal, x1=8, y1=8, x2=56, y2=56) -> str:
        """Linear gradient in user space (safe for strokes on straight lines)."""
        i = self._id()
        self.defs.append(
            f'<linearGradient id="{i}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{pal[0]}"/><stop offset=".5" stop-color="{pal[1]}"/>'
            f'<stop offset="1" stop-color="{pal[2]}"/></linearGradient>')
        return f"url(#{i})"

    def rg(self, pal, cx=0.38, cy=0.32, r=0.75) -> str:
        i = self._id()
        self.defs.append(
            f'<radialGradient id="{i}" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{pal[0]}"/><stop offset=".55" stop-color="{pal[1]}"/>'
            f'<stop offset="1" stop-color="{pal[2]}"/></radialGradient>')
        return f"url(#{i})"

    def add(self, *parts) -> None:
        for p in parts:
            if isinstance(p, (list, tuple)):
                self.add(*p)
            elif p:
                self.parts.append(p)

    def svg(self) -> str:
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{defs}{"".join(self.parts)}</svg>\n'


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def shape(ic: Icon, d: str, pal, grad: str | None = None, sw: float = 2.0, extra: str = "") -> str:
    return (f'<path d="{d}" fill="{grad or ic.lg(pal)}" stroke="{pal[3]}" stroke-width="{f(sw)}" '
            f'stroke-linejoin="round" stroke-linecap="round"{extra}/>')


def line(d: str, color: str, w: float, op: float = 1.0, cap: str = "round") -> str:
    o = "" if op >= 1 else f' opacity="{f(op)}"'
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{f(w)}" stroke-linecap="{cap}" '
            f'stroke-linejoin="round"{o}/>')


def tube(ic: Icon, d: str, pal, w: float, grad: str | None = None) -> list[str]:
    """A thick outlined stroke: shafts, bands, cords."""
    return [line(d, pal[3], w + 3), line(d, grad or ic.lgu(pal), w)]


def circle(ic: Icon, cx, cy, r, pal, grad: str | None = None, sw: float = 2.0) -> str:
    return (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{grad or ic.rg(pal)}" '
            f'stroke="{pal[3]}" stroke-width="{f(sw)}"/>')


def dot(cx, cy, r, color, op: float = 1.0) -> str:
    o = "" if op >= 1 else f' opacity="{f(op)}"'
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{color}"{o}/>'


def gem(ic: Icon, cx, cy, r, pal) -> list[str]:
    return [circle(ic, cx, cy, r, pal, sw=1.6), dot(cx - r * 0.35, cy - r * 0.38, max(0.9, r * 0.28), HL, 0.85)]


def facet_gem(ic: Icon, cx, cy, r, pal) -> list[str]:
    d = f"M{f(cx)} {f(cy - r)} L{f(cx + r)} {f(cy - r * 0.2)} L{f(cx)} {f(cy + r)} L{f(cx - r)} {f(cy - r * 0.2)} Z"
    return [shape(ic, d, pal, ic.lg(pal), 1.6),
            line(f"M{f(cx - r)} {f(cy - r * 0.2)} L{f(cx + r)} {f(cy - r * 0.2)}", pal[2], 1, 0.6),
            line(f"M{f(cx - r * 0.45)} {f(cy - r * 0.55)} L{f(cx - r * 0.1)} {f(cy - r * 0.75)}", HL, 1.4, 0.9)]


def sparkle(cx, cy, r, color) -> str:
    return (f'<path d="M{f(cx)} {f(cy - r)} Q{f(cx)} {f(cy)} {f(cx + r)} {f(cy)} Q{f(cx)} {f(cy)} {f(cx)} {f(cy + r)} '
            f'Q{f(cx)} {f(cy)} {f(cx - r)} {f(cy)} Q{f(cx)} {f(cy)} {f(cx)} {f(cy - r)} Z" fill="{color}"/>')


def rot(parts, angle=-45) -> str:
    return f'<g transform="rotate({angle} 32 32)">{"".join(parts)}</g>'


def mirror_x(d: str) -> str:
    """Mirror an absolute path (M/L/C/Q/Z with numbers) across x = 32."""
    import re

    out, toks = [], re.findall(r"[A-Za-z]|-?\d*\.?\d+", d)
    cmd, idx = None, 0
    for t in toks:
        if t.isalpha():
            cmd, idx = t, 0
            out.append(t)
            continue
        v = float(t)
        if cmd != "Z" and idx % 2 == 0:
            v = 64 - v
        idx += 1
        out.append(f(v))
    return " ".join(out)


# ----------------------------------------------------------------------------- weapons
def blade_path(shape_: str, cx, T, B, w) -> str:
    if shape_ == "straight":
        return f"M{f(cx - w)} {f(B)} L{f(cx - w)} {f(T + w * 1.7)} L{f(cx)} {f(T)} L{f(cx + w)} {f(T + w * 1.7)} L{f(cx + w)} {f(B)} Z"
    if shape_ == "taper":
        return f"M{f(cx - w)} {f(B)} L{f(cx - w * 0.55)} {f(T + w * 1.4)} L{f(cx)} {f(T)} L{f(cx + w * 0.55)} {f(T + w * 1.4)} L{f(cx + w)} {f(B)} Z"
    if shape_ == "curved":
        return f"M{f(cx - w)} {f(B)} L{f(cx - w)} {f(T + 18)} Q{f(cx - w)} {f(T + 3)} {f(cx + w)} {f(T)} Q{f(cx + w + 3)} {f((T + B) / 2)} {f(cx + w)} {f(B)} Z"
    if shape_ == "cleaver":
        return (f"M{f(cx - w)} {f(B)} L{f(cx - w)} {f(T + 4)} Q{f(cx - w)} {f(T)} {f(cx - w + 4)} {f(T)} L{f(cx + w + 2)} {f(T + 2)} "
                f"Q{f(cx + w + 4)} {f(T + 3)} {f(cx + w + 4)} {f(T + 7)} L{f(cx + w + 2)} {f(B - 6)} L{f(cx + w)} {f(B)} Z")
    if shape_ == "crystal":
        return (f"M{f(cx - w)} {f(B)} L{f(cx - w - 2.5)} {f(B - 14)} L{f(cx - w + 0.5)} {f(T + 16)} L{f(cx - 1)} {f(T)} "
                f"L{f(cx + w - 0.5)} {f(T + 10)} L{f(cx + w + 2.5)} {f(B - 18)} L{f(cx + w)} {f(B)} Z")
    if shape_ == "fin":
        return (f"M{f(cx - w * 0.6)} {f(B)} L{f(cx - w)} {f(T + 20)} Q{f(cx - w)} {f(T + 4)} {f(cx)} {f(T)} "
                f"Q{f(cx + w + 5)} {f(T + 10)} {f(cx + w)} {f(B - 4)} L{f(cx + w * 0.6)} {f(B)} Z")
    if shape_ == "leaf":
        return (f"M{f(cx - w * 0.6)} {f(B)} C{f(cx - w * 1.5)} {f(B - 20)} {f(cx - w)} {f(T + 12)} {f(cx)} {f(T)} "
                f"C{f(cx + w)} {f(T + 12)} {f(cx + w * 1.5)} {f(B - 20)} {f(cx + w * 0.6)} {f(B)} Z")
    if shape_ == "serrated":
        pts = [f"M{f(cx - w)} {f(B)}", f"L{f(cx - w)} {f(T + w * 1.7)}", f"L{f(cx)} {f(T)}", f"L{f(cx + w)} {f(T + w * 1.7)}"]
        y = T + w * 1.7
        while y < B - 6:
            pts.append(f"L{f(cx + w + 3)} {f(y + 2.5)} L{f(cx + w)} {f(y + 6)}")
            y += 6
        pts.append(f"L{f(cx + w)} {f(B)} Z")
        return " ".join(pts)
    if shape_ == "double_serrated":
        left, right = [], []
        y = T + w * 1.7
        while y < B - 6:
            right.append(f"L{f(cx + w + 3)} {f(y + 2.5)} L{f(cx + w)} {f(y + 6)}")
            left.append((y, f"L{f(cx - w)} {f(y + 6)} L{f(cx - w - 3)} {f(y + 2.5)}"))
            y += 6
        d = f"M{f(cx - w)} {f(B)} " + " ".join(s for _, s in reversed(left))
        d += f" L{f(cx - w)} {f(T + w * 1.7)} L{f(cx)} {f(T)} L{f(cx + w)} {f(T + w * 1.7)} " + " ".join(right)
        return d + f" L{f(cx + w)} {f(B)} Z"
    if shape_ == "wavy":
        n, pts_l, pts_r = 10, [], []
        for k in range(n + 1):
            y = T + 10 + (B - T - 10) * k / n
            a = 2.2 * math.sin(k * math.pi / 2)
            pts_l.append((cx - w - a, y))
            pts_r.append((cx + w + a, y))
        d = f"M{f(pts_l[-1][0])} {f(pts_l[-1][1])} " + " ".join(f"L{f(x)} {f(y)}" for x, y in reversed(pts_l[:-1]))
        d += f" L{f(cx)} {f(T)} " + " ".join(f"L{f(x)} {f(y)}" for x, y in pts_r)
        return d + " Z"
    raise ValueError(shape_)


def sword(ic, blade, guard=None, grip=None, pommel=None, shape_="straight", w=6.0, T=-8.0, B=46.0, gw=12.0,
          gshape="cross", gem_=None, pgem=None, extra=None, grip_len=13.0, fuller=True):
    guard = guard or PAL["steel"]
    grip = grip or PAL["leather"]
    pommel = pommel or guard
    cx = 32.0
    s = [shape(ic, blade_path(shape_, cx, T, B, w), blade, ic.lg(blade, 0, 0, 1, 0))]
    if fuller:
        s.append(line(f"M{f(cx)} {f(B - 3)} L{f(cx)} {f(T + w * 2.4)}", blade[2], max(1.2, w * 0.24), 0.55))
        s.append(line(f"M{f(cx - w * 0.55)} {f(B - 4)} L{f(cx - w * 0.55)} {f(T + w * 2.2)}", HL, 1.4, 0.5))
    if extra:
        s.append(sword_extra(ic, extra, cx, T, B, w))
    # grip + pommel
    s.append(f'<rect x="{f(cx - 2.8)}" y="{f(B + 3)}" width="5.6" height="{f(grip_len + 2)}" rx="2.2" fill="{ic.lg(grip, 0, 0, 1, 0)}" stroke="{grip[3]}" stroke-width="1.6"/>')
    y = B + 6
    while y < B + 3 + grip_len:
        s.append(line(f"M{f(cx - 2.6)} {f(y)} L{f(cx + 2.6)} {f(y + 1.6)}", grip[3], 1, 0.55))
        y += 3.2
    py = B + 5 + grip_len + 3
    s.append(circle(ic, cx, py, 3.8, pommel, sw=1.6))
    if pgem:
        s.append(dot(cx, py, 1.8, pgem[1]))
    # guard
    if gshape == "cross":
        s.append(f'<rect x="{f(cx - gw)}" y="{f(B - 1.5)}" width="{f(gw * 2)}" height="6" rx="3" fill="{ic.lg(guard, 0, 0, 0, 1)}" stroke="{guard[3]}" stroke-width="1.8"/>')
    elif gshape == "wing":
        s += tube(ic, f"M{f(cx - gw)} {f(B - 7)} Q{f(cx)} {f(B + 10)} {f(cx + gw)} {f(B - 7)}", guard, 4.4)
    elif gshape == "hook":
        s += tube(ic, f"M{f(cx - gw)} {f(B - 10)} C{f(cx - gw)} {f(B + 5)} {f(cx + gw)} {f(B + 5)} {f(cx + gw)} {f(B - 10)}", guard, 3.6)
    elif gshape == "round":
        s.append(circle(ic, cx, B + 1.5, gw * 0.55, guard, sw=1.8))
        s.append(f'<circle cx="{f(cx)}" cy="{f(B + 1.5)}" r="{f(gw * 0.3)}" fill="none" stroke="{guard[3]}" stroke-width="1.4" opacity=".6"/>')
    elif gshape == "spiky":
        d = (f"M{f(cx - gw)} {f(B + 3)} L{f(cx - gw - 2)} {f(B - 6)} L{f(cx - gw + 5)} {f(B - 1)} L{f(cx - 4)} {f(B - 7)} "
             f"L{f(cx)} {f(B - 2)} L{f(cx + 4)} {f(B - 7)} L{f(cx + gw - 5)} {f(B - 1)} L{f(cx + gw + 2)} {f(B - 6)} "
             f"L{f(cx + gw)} {f(B + 3)} Q{f(cx)} {f(B + 8)} {f(cx - gw)} {f(B + 3)} Z")
        s.append(shape(ic, d, guard, ic.lg(guard, 0, 0, 0, 1), 1.8))
    if gem_:
        s += gem(ic, cx, B + 1.5, 3.2, gem_)
    return rot(s)


def sword_extra(ic, kind: str, cx, T, B, w) -> str:
    out = []
    if kind == "drips":
        for x, y, r in ((cx - w - 4, T + 30, 3), (cx + w + 5, T + 20, 2.4), (cx - w - 3, T + 12, 2)):
            out.append(dot(x, y, r, "#8ee04a"))
            out.append(dot(x - r * 0.3, y - r * 0.3, r * 0.35, HL, 0.8))
    elif kind == "flames":
        for i, y in enumerate((T + 14, T + 26, T + 38)):
            side = -1 if i % 2 == 0 else 1
            x = cx + side * (w + 1)
            out.append(shape(ic, f"M{f(x)} {f(y + 6)} C{f(x + side * 6)} {f(y + 2)} {f(x + side * 3)} {f(y - 4)} {f(x + side * 7)} {f(y - 9)} "
                                 f"C{f(x + side * 1)} {f(y - 6)} {f(x - side * 1)} {f(y)} {f(x)} {f(y + 6)} Z", PAL["fire"], sw=1.2))
    elif kind == "cracks":
        out.append(line(f"M{f(cx - w * 0.6)} {f(B - 6)} L{f(cx + w * 0.3)} {f(B - 14)} L{f(cx - w * 0.3)} {f(B - 22)} "
                        f"L{f(cx + w * 0.4)} {f(B - 32)} L{f(cx)} {f(T + 12)}", "#ff7a2a", 1.6))
        out.append(line(f"M{f(cx + w * 0.3)} {f(B - 14)} L{f(cx + w * 0.8)} {f(B - 18)}", "#ffc04a", 1.2))
    elif kind == "blood":
        out += [dot(cx + w * 0.3, T + 16, 2.4, "#d9253a"), dot(cx - w * 0.4, T + 24, 1.6, "#d9253a"), dot(cx + w * 0.5, T + 30, 1.2, "#d9253a")]
    elif kind.startswith("glow"):
        color = kind.split(":", 1)[1] if ":" in kind else "#bff4ff"
        out += [sparkle(cx + w + 6, T + 10, 4, color), sparkle(cx - w - 5, T + 26, 3, color)]
    elif kind == "maw":   # a mouth down the blade: dark slit, fangs from both sides, an eye near the guard
        top, bot = T + 13, B - 9
        out.append(f'<path d="M{f(cx)} {f(top)} C{f(cx + w * 0.75)} {f(top + 9)} {f(cx + w * 0.75)} {f(bot - 9)} {f(cx)} {f(bot)} '
                   f'C{f(cx - w * 0.75)} {f(bot - 9)} {f(cx - w * 0.75)} {f(top + 9)} {f(cx)} {f(top)} Z" fill="#1a0606"/>')
        y = top + 5
        while y < bot - 4:
            out.append(f'<path d="M{f(cx - w * 0.62)} {f(y - 2.2)} L{f(cx + 0.8)} {f(y)} L{f(cx - w * 0.62)} {f(y + 2.2)} Z" fill="#fff8e6"/>')
            out.append(f'<path d="M{f(cx + w * 0.62)} {f(y + 0.3)} L{f(cx - 0.8)} {f(y + 2.5)} L{f(cx + w * 0.62)} {f(y + 4.7)} Z" fill="#fff8e6"/>')
            y += 5
        out.append(dot(cx, B - 4.5, 2.6, "#ffe24a"))
        out.append(dot(cx, B - 4.5, 1.2, "#1a0606"))
    elif kind == "rock":
        for x, y, r in ((cx - w * 0.4, T + 18, 2.2), (cx + w * 0.3, T + 28, 2.6), (cx - w * 0.2, T + 38, 1.8)):
            out.append(dot(x, y, r, "#2c3442", 0.35))
    elif kind == "vines":
        out.append(line(f"M{f(cx - w)} {f(B - 4)} C{f(cx + w)} {f(B - 12)} {f(cx - w)} {f(B - 22)} {f(cx + w * 0.6)} {f(B - 30)}", "#5cc24a", 1.8))
    elif kind == "prism":
        out.append(line(f"M{f(cx - w + 1)} {f(B - 6)} L{f(cx + w - 1)} {f(T + 18)}", "#ff8adc", 2, 0.6))
        out.append(line(f"M{f(cx - w + 2)} {f(B - 18)} L{f(cx + w - 2)} {f(B - 30)}", "#9dff8a", 2, 0.6))
    elif kind == "spiral":
        out.append(line(f"M{f(cx)} {f(B - 6)} C{f(cx + 5)} {f(B - 6)} {f(cx + 5)} {f(B - 13)} {f(cx)} {f(B - 13)} C{f(cx - 3)} {f(B - 13)} {f(cx - 3)} {f(B - 9)} {f(cx)} {f(B - 9)}", "#a8387a", 1.4))
    return "".join(out)


def dagger(ic, blade, *args, **kw):
    kw.setdefault("T", 8)
    kw.setdefault("B", 40)
    kw.setdefault("gw", 9)
    kw.setdefault("grip_len", 10)
    return sword(ic, blade, *args, **kw)


def axe(ic, head, handle=None, kind="crescent", double=False, edge=None):
    handle = handle or PAL["wood"]
    s = tube(ic, "M32 8 L32 70", handle, 5)
    heads = {
        "crescent": "M33 7 L20 4 C10 6 4 16 4 27 C4 35 8 41 12 43 C14 34 22 29 33 28 Z",
        "wedge": "M33 8 L16 3 C11 12 9 22 11 33 L33 27 Z",
        "cleaver": "M33 6 L11 6 C9 6 8 8 8 10 L8 30 C8 32 10 33 12 33 L33 29 Z",
        "bearded": "M33 7 L14 6 C9 10 8 18 10 24 C12 32 18 38 24 40 C23 32 26 28 33 27 Z",
    }
    d = heads[kind]
    s.append(shape(ic, d, head, ic.lg(head, 0, 0, 1, 1)))
    if double:
        s.append(shape(ic, mirror_x(d), head, ic.lg(head, 1, 0, 0, 1)))
    s.append(line("M8 26 C10 16 14 10 20 7", edge or HL, 2.2, 0.7) if kind != "cleaver" else line("M10 30 L10 10", edge or HL, 2.2, 0.7))
    s.append(f'<rect x="28.5" y="4" width="7" height="26" rx="2" fill="{ic.lg(PAL["slate"], 0, 0, 1, 0)}" stroke="{PAL["slate"][3]}" stroke-width="1.4"/>')
    s.append(circle(ic, 32, 72, 3.4, handle, sw=1.4))
    return rot(s, -40)


def staff(ic, shaft, top="orb", gem_=None, accent=None, thin=False, rings=True):
    gem_ = gem_ or PAL["sapphire"]
    accent = accent or PAL["gold"]
    w = 3.4 if thin else 4.6
    s = tube(ic, "M32 18 L32 74", shaft, w)
    if rings:
        for y in (30, 60):
            s.append(f'<rect x="{f(32 - w / 2 - 1)}" y="{y}" width="{f(w + 2)}" height="3" rx="1.2" fill="{accent[1]}" stroke="{accent[3]}" stroke-width="1"/>')
    if top == "orb":
        s += tube(ic, "M32 22 C24 21 22 12 25 5", accent, 2.6) + tube(ic, "M32 22 C40 21 42 12 39 5", accent, 2.6)
        s += gem(ic, 32, 11, 7.5, gem_)
    elif top == "eye":
        s += tube(ic, "M32 22 C24 21 22 12 25 5", accent, 2.6) + tube(ic, "M32 22 C40 21 42 12 39 5", accent, 2.6)
        s.append(circle(ic, 32, 11, 7.5, PAL["white"], sw=1.6))
        s += gem(ic, 33, 12, 3.8, gem_)
        s.append(dot(33, 12, 1.5, "#12060a"))
    elif top == "crook":
        s += tube(ic, "M32 22 L32 8 C32 -1 45 -2 46 7 C47 14 39 16 37 10", shaft, w)
        s.append(dot(38.5, 10, 2.2, gem_[1]))
    elif top == "crystal":
        s.append(f'<rect x="27" y="17" width="10" height="5" rx="2" fill="{accent[1]}" stroke="{accent[3]}" stroke-width="1.4"/>')
        s += facet_gem(ic, 32, 7, 10, gem_)
    elif top == "claw":
        for d in ("M32 23 C22 22 20 12 24 3", "M32 23 C42 22 44 12 40 3", "M32 22 L32 1"):
            s += tube(ic, d, accent, 2.4)
        s += gem(ic, 32, 11, 6.2, gem_)
    elif top == "spiral":
        s += tube(ic, "M32 22 L32 14 C32 6 40 4 42 10 C44 16 36 18 35 13", shaft, w * 0.8)
        s += gem(ic, 30, 8, 5.4, gem_)
    elif top == "coral":
        for d in ("M32 24 C30 16 24 12 20 4", "M32 24 C34 14 40 12 44 2", "M29 16 C26 14 24 16 22 14", "M35 14 C38 12 42 14 45 11", "M32 22 L32 6"):
            s += tube(ic, d, gem_, 3.2)
        for x, y in ((20, 4), (44, 2), (32, 5), (22, 14), (45, 11)):
            s.append(dot(x, y, 2.4, "#ff9ad8"))
    elif top == "coil":    # a glowing spiral around a star orb
        s += tube(ic, "M32 24 C22 24 17 14 23 7 C29 0 42 2 43 11 C44 18 36 21 32 17 C29 14 31 10 35 10", accent, 3.2)
        s += gem(ic, 34, 12.5, 4.4, gem_)
        s.append(sparkle(19, 5, 3.4, "#fff4b0"))
        s.append(sparkle(46, 21, 2.8, "#bff4ff"))
    elif top == "sprout":  # roots cup an earth orb, two leaves on top
        s += tube(ic, "M32 25 C24 23 21 17 23 10", shaft, 3.2) + tube(ic, "M32 25 C40 23 43 17 41 10", shaft, 3.2)
        s += gem(ic, 32, 14, 7.5, gem_)
        s.append(dot(29, 16, 2.4, "#7a5a2c", 0.55))
        s.append(dot(35.5, 12, 1.8, "#7a5a2c", 0.55))
        s.append(shape(ic, "M32 6.5 C28 0 21 -1 16 1.5 C20 7 26 8 32 6.5 Z", PAL["leaf"], sw=1.4))
        s.append(shape(ic, "M32 6.5 C36 0 43 -1 48 1.5 C44 7 38 8 32 6.5 Z", PAL["leaf"], sw=1.4))
    elif top == "maw":
        s.append(circle(ic, 32, 11, 11, PAL["violet"], sw=2))
        for d, c in (("M22 8 C26 2 36 1 42 6", "#9dff4a"), ("M22 14 C26 20 38 21 42 15", "#34d8e0"), ("M25 11 C28 7 36 7 39 11", "#ffe04a")):
            s.append(line(d, c, 2.6))
        s.append(dot(32, 11, 3.2, "#12060a"))
        s.append(dot(30.8, 9.8, 1, HL))
    return rot(s)


def wand(ic, shaft, tip="star", tip_pal=None, w=2.8):
    tip_pal = tip_pal or PAL["gold"]
    s = tube(ic, "M32 6 L32 72", shaft, w)
    if tip == "star":
        s.append(shape(ic, "M32 -2 L34.5 4 L41 4.5 L36 8.5 L37.8 15 L32 11.5 L26.2 15 L28 8.5 L23 4.5 L29.5 4 Z", tip_pal, sw=1.4))
    elif tip == "leaf":
        s.append(shape(ic, "M32 22 C38 18 44 18 48 12 C42 10 36 12 32 22 Z", tip_pal, sw=1.4))
        s.append(shape(ic, "M32 30 C27 26 21 26 17 21 C23 18 29 21 32 30 Z", tip_pal, sw=1.4))
    elif tip == "none":
        s.append(dot(32, 6, 2.4, tip_pal[1]))
    elif tip == "knob":
        s.append(f'<rect x="{f(32 - w / 2 - 1.2)}" y="52" width="{f(w + 2.4)}" height="14" rx="2" fill="{ic.lg(PAL["leather"], 0, 0, 1, 0)}" stroke="{PAL["leather"][3]}" stroke-width="1.4"/>')
        for y in (55.5, 59.5, 63.5):
            s.append(line(f"M{f(32 - w / 2 - 1)} {y} L{f(32 + w / 2 + 1)} {y + 1.4}", PAL["leather"][3], 1, 0.6))
        s.append(circle(ic, 32, 6, 5, tip_pal, sw=1.6))
        s.append(dot(30.4, 4.4, 1.5, HL, 0.85))
    s.append(circle(ic, 32, 72, 2.6, shaft, sw=1.2))
    return rot(s)


def mace(ic, head, shaft=None, kind="spiked", studs=False):
    shaft = shaft or PAL["wood"]
    s = []
    if kind == "spiked":
        s += tube(ic, "M32 26 L32 74", shaft, 5)
        for k in range(8):
            a = k * math.pi / 4
            x1, y1 = 32 + 9 * math.cos(a - 0.3), 16 + 9 * math.sin(a - 0.3)
            x2, y2 = 32 + 17 * math.cos(a), 16 + 17 * math.sin(a)
            x3, y3 = 32 + 9 * math.cos(a + 0.3), 16 + 9 * math.sin(a + 0.3)
            s.append(shape(ic, f"M{f(x1)} {f(y1)} L{f(x2)} {f(y2)} L{f(x3)} {f(y3)} Z", head, ic.lg(head), 1.4))
        s.append(circle(ic, 32, 16, 11, head))
        s.append(dot(28.5, 12.5, 2.4, HL, 0.6))
    elif kind == "club":
        if studs:   # iron spikes poking out on both sides (drawn first: the club covers their bases)
            for (bx, by, tx, ty) in ((25, 12, 11, 10), (26, 26, 12.5, 28), (39, 11, 53, 9), (38.5, 25, 52, 27)):
                s.append(shape(ic, f"M{bx} {by - 4.6} L{tx} {ty} L{bx} {by + 4.6} Z", PAL["steel"], ic.lg(PAL["steel"]), 1.8))
        s.append(shape(ic, "M29.5 74 L27.5 36 C21 24 21 6 32 2 C43 6 43 24 36.5 36 L34.5 74 Z", head, ic.lg(head, 0, 0, 1, 0)))
        s.append(line("M28 30 C26 20 27 10 30 6", HL, 2, 0.45))
        s.append(line("M35 20 L37 26 M31 14 L33 19", head[2], 1.4, 0.7))
        if studs:
            for x, y in ((29, 15), (35, 24)):
                s.append(dot(x, y, 1.6, head[3], 0.6))
    elif kind == "drumstick":
        s += tube(ic, "M32 34 L32 66", PAL["bone"], 5)
        s.append(circle(ic, 29, 68, 3.6, PAL["bone"], sw=1.6))
        s.append(circle(ic, 35, 68, 3.6, PAL["bone"], sw=1.6))
        s.append(shape(ic, "M32 1 C45 1 49 14 45 26 C43 32 39 37 34 39 L30 39 C25 37 21 32 19 26 C15 14 19 1 32 1 Z", head, ic.rg(head)))
        s.append(line("M24 12 C26 8 30 6 34 6", HL, 2.4, 0.55))
        s.append(dot(38, 22, 2, head[2], 0.6))
        s.append(dot(27, 28, 1.6, head[2], 0.6))
    return rot(s)


def scythe(ic, blade, shaft):
    s = tube(ic, "M56 62 L24 6", shaft, 4.4)
    s.append(shape(ic, "M26 8 C12 -1 0 8 1 30 C8 19 17 14 30 16 Z", blade, ic.lg(blade, 0, 0, 1, 1)))
    s.append(line("M3 25 C5 14 11 7 20 6", HL, 2, 0.7))
    s.append(f'<rect x="20" y="4" width="9" height="14" rx="2" transform="rotate(-30 24.5 11)" fill="{shaft[2]}" stroke="{shaft[3]}" stroke-width="1.4"/>')
    s.append(circle(ic, 57, 63, 3, shaft, sw=1.4))
    return "".join(s)


def trident(ic, head, shaft=None, ornate=False):
    shaft = shaft or PAL["shadow"]
    s = tube(ic, "M32 24 L32 74", shaft, 4.4)
    s += tube(ic, "M21 22 Q32 30 43 22", head, 4)
    for x, top in ((21, 6), (32, -3), (43, 6)):
        s += tube(ic, f"M{x} 23 L{x} {top + 6}", head, 3.4)
        s.append(shape(ic, f"M{x - 4} {top + 7} L{x} {top - 2} L{x + 4} {top + 7} Z", head, sw=1.4))
    if ornate:
        s += gem(ic, 32, 27, 3.4, PAL["ruby"])
    return rot(s)


# ----------------------------------------------------------------------------- special weapons
def chakram(ic, pal):
    pts = []
    for k in range(32):
        a = k * math.pi / 16
        r = 28 if k % 2 == 0 else 22.5
        pts.append(f"{'M' if k == 0 else 'L'}{f(32 + r * math.cos(a))} {f(32 + r * math.sin(a))}")
    s = [shape(ic, " ".join(pts) + " Z", pal, ic.rg(pal, 0.4, 0.35, 0.8))]
    s.append(f'<circle cx="32" cy="32" r="17" fill="none" stroke="{pal[2]}" stroke-width="1.6" opacity=".7"/>')
    # the maw: dark mouth, fangs from the top and bottom, two glowing eyes
    s.append(f'<ellipse cx="32" cy="33" rx="12" ry="10" fill="#1a0808" stroke="{pal[3]}" stroke-width="2"/>')
    for x in (25, 30, 35, 40):
        s.append(f'<path d="M{x - 2.4} 23.8 L{x + 2.4} 23.8 L{x} 30 Z" fill="#fff8e6"/>')
    for x in (27.5, 32.5, 37.5):
        s.append(f'<path d="M{x - 2.4} 42.2 L{x + 2.4} 42.2 L{x} 36.5 Z" fill="#fff8e6"/>')
    s.append(line("M13 22 C17 14 25 9 33 8.5", HL, 2, 0.55))
    return "".join(s)

def nunchaku(ic, pal):
    s = []
    # chain: links along a short arc between the two capped ends
    pts = [(18.5, 13), (22, 8.5), (27, 6), (32.5, 6.5), (37, 9.5), (40, 14)]
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        cx, cy, ang = (x1 + x2) / 2, (y1 + y2) / 2, math.degrees(math.atan2(y2 - y1, x2 - x1))
        s.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="3.4" ry="2" transform="rotate({f(ang)} {f(cx)} {f(cy)})" '
                 f'fill="none" stroke="#1e232e" stroke-width="3.4"/>')
        s.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="3.4" ry="2" transform="rotate({f(ang)} {f(cx)} {f(cy)})" '
                 f'fill="none" stroke="#c8d0dc" stroke-width="1.6"/>')
    # sticks: one hangs down on the left, one swings out to the right
    for a, b in (((17, 16), (11, 58)), ((42, 17), (56, 57))):
        s += tube(ic, f"M{a[0]} {a[1]} L{b[0]} {b[1]}", pal, 7.5)
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        # metal cap at the chain end, grip bands lower down, a light edge
        s += tube(ic, f"M{f(a[0] - ux)} {f(a[1] - uy)} L{f(a[0] + ux * 4)} {f(a[1] + uy * 4)}", PAL["steel"], 8)
        for t in (0.55, 0.68, 0.81):
            x, y = a[0] + dx * t, a[1] + dy * t
            s.append(line(f"M{f(x - uy * 4.2)} {f(y + ux * 4.2)} L{f(x + uy * 4.2)} {f(y - ux * 4.2)}", pal[3], 1.6, 0.8))
        s.append(line(f"M{f(a[0] + ux * 7 - uy * 2)} {f(a[1] + uy * 7 + ux * 2)} L{f(a[0] + ux * 22 - uy * 2)} {f(a[1] + uy * 22 + ux * 2)}", HL, 1.6, 0.55))
    return "".join(s)

def fates(ic):
    s = []
    heads = ((17, 15, PAL["orange"]), (37, 9, PAL["pink"]), (13, 35, PAL["violet"]))
    for x, y, _ in heads:
        s += tube(ic, f"M44 46 Q{f((x + 44) / 2 + 3)} {f((y + 46) / 2 + 4)} {x} {y}", PAL["leaf"], 2.4)
    s.append(shape(ic, "M31 30 C26 24 26 19 30 16 C35 20 35 25 31 30 Z", PAL["leaf"], sw=1.4))
    s.append(shape(ic, "M29 43 C22 45 18 42 17 38 C23 36 27 38 29 43 Z", PAL["leaf"], sw=1.4))
    for x, y, pal in heads:
        for k in range(5):
            a = k * 2 * math.pi / 5 - math.pi / 2
            s.append(circle(ic, x + 5.6 * math.cos(a), y + 5.6 * math.sin(a), 4, pal, sw=1.3))
        s.append(circle(ic, x, y, 3.2, PAL["yellow"], sw=1.2))
    # the stems are tied with a ribbon into a handle
    s += tube(ic, "M44 46 L58 60", PAL["leaf"], 5.4)
    s.append(shape(ic, "M40 44 L48 42 L50 50 L42 52 Z", PAL["red"], sw=1.4))
    s.append(shape(ic, "M44 47 L37 56 L41 57 Z M46 47 L50 58 L46 58 Z", PAL["red"], sw=1.2))
    return "".join(s)

def stinger(ic, pal):
    s = tube(ic, "M58 60 L48 50", PAL["amethyst"], 6)
    pts = [(46, 48), (41, 45), (36, 41), (31, 36), (27, 30), (24, 24), (22, 18), (22, 12)]
    for i, (x, y) in enumerate(pts):
        r = 6.4 - i * 0.35
        s.append(circle(ic, x, y, r, pal if i % 2 == 0 else PAL["plum"], sw=1.6))
    s.append(shape(ic, "M16 12 C15 3 23 -1 31 3 C27 5 26 9 27 14 C24 13 20 13 16 12 Z", PAL["amethyst"], sw=1.6))
    s.append(line("M18 8 C20 5 24 4 27 4", HL, 1.6, 0.7))
    return "".join(s)


# ----------------------------------------------------------------------------- helmets
HELM = "M14 42 C13 22 21 8 32 8 C43 8 51 22 50 42 L50 52 C50 56 47 58 43 58 L21 58 C17 58 14 56 14 52 Z"


def knight(ic, pal, visor="slit", trim=None, crest=None, pattern=None, crest_pal=None):
    s = []
    crest_pal = crest_pal or trim or PAL["red"]
    if crest == "plume":
        s.append(shape(ic, "M32 12 C28 2 36 -2 48 3 C54 6 56 12 54 18 C50 12 44 10 36 12 Z", crest_pal, sw=1.6))
    elif crest == "fin":
        s.append(shape(ic, "M24 12 C26 1 38 1 40 12 Z", crest_pal, sw=1.6))
    elif crest == "horns":
        s.append(shape(ic, "M16 26 C8 20 6 10 10 3 C12 12 16 16 22 18 Z", crest_pal, sw=1.6))
        s.append(shape(ic, mirror_x("M16 26 C8 20 6 10 10 3 C12 12 16 16 22 18 Z"), crest_pal, sw=1.6))
    elif crest == "wave":
        s.append(shape(ic, "M22 12 C20 0 44 -2 52 10 C56 16 54 26 50 30 C48 20 42 12 30 12 Z", crest_pal, sw=1.6))
    s.append(shape(ic, HELM, pal, ic.lg(pal, 0.1, 0, 0.9, 1)))
    s.append(f'<path d="M32 8 C43 8 51 22 50 42 L50 52 C50 56 47 58 43 58 L32 58 Z" fill="{pal[3]}" opacity=".16"/>')
    if pattern:
        s.append(pattern_marks(pattern, 14, 10, 50, 58))
    if trim:
        s.append(line("M32 9 L32 26", trim[1], 3.2))
        s.append(line("M15 50 L49 50", trim[1], 3.2))
    ol = pal[3]
    if visor == "slit":
        s.append(f'<rect x="18" y="31" width="28" height="5" rx="2.5" fill="{ol}"/>')
        for x in (24, 28, 32, 36, 40):
            s.append(dot(x, 43, 1.1, ol, 0.8))
    elif visor == "t":
        s.append(f'<rect x="18" y="29" width="28" height="5" rx="2.5" fill="{ol}"/><rect x="29.5" y="29" width="5" height="19" rx="2.5" fill="{ol}"/>')
    elif visor == "grille":
        for x in (22, 27, 32, 37, 42):
            s.append(f'<rect x="{x - 1.3}" y="30" width="2.6" height="17" rx="1.3" fill="{ol}"/>')
    elif visor == "eye":
        s.append(f'<ellipse cx="32" cy="36" rx="12" ry="8" fill="{ol}"/>')
        s.append(f'<ellipse cx="32" cy="36" rx="12" ry="8" fill="none" stroke="{pal[1]}" stroke-width="1.6"/>')
    elif visor == "open":
        s.append(f'<path d="M19 30 C19 26 45 26 45 30 L45 50 L19 50 Z" fill="{ol}"/>')
        s.append(dot(26, 38, 1.8, "#ffd23a"))
        s.append(dot(38, 38, 1.8, "#ffd23a"))
    s.append(line("M19 24 C20 17 24 12 29 11", HL, 2.2, 0.6))
    return "".join(s)


def pattern_marks(kind: str, x0, y0, x1, y1) -> str:
    if kind == "cracks":
        return (line(f"M{x0 + 6} {y0 + 16} L{x0 + 12} {y0 + 22} L{x0 + 9} {y0 + 30} L{x0 + 16} {y0 + 38}", "#ff7a2a", 1.8)
                + line(f"M{x1 - 6} {y0 + 12} L{x1 - 12} {y0 + 20} L{x1 - 8} {y0 + 28}", "#ffb03a", 1.6)
                + line(f"M{x1 - 10} {y1 - 8} L{x1 - 16} {y1 - 14}", "#ff7a2a", 1.4))
    if kind == "vines":
        return (line(f"M{x0 + 3} {y1 - 6} C{x0 + 14} {y1 - 16} {x0 + 4} {y0 + 18} {x0 + 14} {y0 + 8}", "#5ce06a", 2)
                + line(f"M{x1 - 3} {y1 - 10} C{x1 - 12} {y0 + 24} {x1 - 4} {y0 + 16} {x1 - 12} {y0 + 6}", "#2ec8a0", 2)
                + dot(x0 + 12, y0 + 20, 1.8, "#9dff6a") + dot(x1 - 8, y0 + 26, 1.8, "#9dff6a"))
    if kind == "frost":
        return (line(f"M{x0 + 5} {y0 + 10} L{x0 + 12} {y0 + 20} M{x1 - 5} {y0 + 12} L{x1 - 11} {y0 + 22}", "#f0c8ff", 2)
                + line(f"M{x0 + 8} {y1 - 6} L{x0 + 14} {y1 - 14} M{x1 - 8} {y1 - 6} L{x1 - 14} {y1 - 14}", "#f0c8ff", 1.6, 0.8))
    if kind == "streaks":
        return (line(f"M{x0 + 4} {y0 + 14} C{x0 + 12} {y0 + 10} {x0 + 14} {y0 + 22} {x0 + 22} {y0 + 18}", "#3ed0ea", 2.2)
                + line(f"M{x1 - 4} {y1 - 14} C{x1 - 12} {y1 - 10} {x1 - 14} {y1 - 20} {x1 - 22} {y1 - 16}", "#3ed0ea", 2.2))
    if kind == "mottle":
        out = ""
        for x, y, r in ((0.3, 0.3, 2.6), (0.62, 0.22, 2), (0.5, 0.55, 3), (0.24, 0.7, 2.2), (0.75, 0.7, 2.4), (0.72, 0.42, 1.6)):
            out += dot(x0 + (x1 - x0) * x, y0 + (y1 - y0) * y, r, "#d4f0c0", 0.45)
        return out
    if kind == "checker":
        out = ""
        for i in range(4):
            for j in range(5):
                if (i + j) % 2 == 0:
                    out += f'<rect x="{f(x0 + 4 + i * (x1 - x0 - 8) / 4)}" y="{f(y0 + 6 + j * (y1 - y0 - 10) / 5)}" width="{f((x1 - x0 - 8) / 4)}" height="{f((y1 - y0 - 10) / 5)}" fill="#ffffff" opacity=".13"/>'
        return out
    if kind == "flametrim":
        return line(f"M{x0 + 4} {y0 + 12} C{x0 + 8} {y0 + 4} {x1 - 8} {y0 + 4} {x1 - 4} {y0 + 12}", "#ff4d6d", 2.4)
    if kind == "planks":
        return (line(f"M{(x0 + x1) / 2 - 7} {y0 + 4} L{(x0 + x1) / 2 - 7} {y1 - 4}", "#3a1e10", 1.4, 0.7)
                + line(f"M{(x0 + x1) / 2 + 7} {y0 + 4} L{(x0 + x1) / 2 + 7} {y1 - 4}", "#3a1e10", 1.4, 0.7))
    if kind == "rivets":
        return "".join(dot(x, y, 1.5, "#2a2622", 0.7) for x, y in ((x0 + 5, y0 + 6), (x1 - 5, y0 + 6), (x0 + 5, y1 - 6), (x1 - 5, y1 - 6)))
    return ""


def bucket(ic, pal, visor="slit", bands=None, pattern=None):
    d = "M16 12 C16 8 20 6 24 6 L40 6 C44 6 48 8 48 12 L50 54 C50 57 48 58 45 58 L19 58 C16 58 14 57 14 54 Z"
    s = [shape(ic, d, pal, ic.lg(pal, 0, 0, 1, 0.4))]
    if pattern:
        s.append(pattern_marks(pattern, 14, 6, 50, 58))
    if bands:
        s.append(f'<rect x="15" y="14" width="34" height="4" rx="1.5" fill="{bands[1]}" stroke="{bands[3]}" stroke-width="1"/>')
        s.append(f'<rect x="14.5" y="48" width="35" height="4" rx="1.5" fill="{bands[1]}" stroke="{bands[3]}" stroke-width="1"/>')
    if visor == "slit":
        s.append(f'<rect x="17" y="27" width="30" height="5" rx="2" fill="{pal[3]}"/>')
    elif visor == "bars":
        for x in (21, 26.5, 32, 37.5, 43):
            s.append(f'<rect x="{x - 1.3}" y="22" width="2.6" height="24" rx="1.3" fill="{pal[3]}"/>')
    s.append(line("M19 14 L20 40", HL, 2.2, 0.45))
    return "".join(s)


def crown(ic, pal, gem_):
    d = "M10 50 L8 18 L20 30 L26 10 L32 26 L38 10 L44 30 L56 18 L54 50 Z"
    s = [shape(ic, d, pal, ic.lg(pal, 0, 0, 0, 1))]
    s.append(f'<rect x="9" y="44" width="46" height="9" rx="3" fill="{ic.lg(pal, 0, 0, 0, 1)}" stroke="{pal[3]}" stroke-width="2"/>')
    for x, y in ((8, 18), (26, 10), (38, 10), (56, 18)):
        s += gem(ic, x, y, 2.6, gem_)
    s += facet_gem(ic, 32, 38, 6, gem_)
    for x in (18, 46):
        s += gem(ic, x, 48.5, 2.4, gem_)
    return "".join(s)


def hat(ic, kind, pal, band=None, accent=None):
    s = []
    band = band or PAL["shadow"]
    if kind == "fedora":
        s.append(shape(ic, "M4 46 C4 40 18 38 32 38 C46 38 60 40 60 46 C60 50 46 52 32 52 C18 52 4 50 4 46 Z", pal))
        s.append(shape(ic, "M16 42 C15 28 20 16 32 16 C44 16 49 28 48 42 C40 45 24 45 16 42 Z", pal))
        s.append(line("M24 20 C28 24 36 24 40 20", pal[2], 2, 0.7))
        s.append(f'<path d="M16.5 36 C24 39 40 39 47.5 36 L48 41.5 C40 44.5 24 44.5 16 41.5 Z" fill="{band[1]}" stroke="{band[3]}" stroke-width="1.2"/>')
    elif kind == "sunhat":
        s.append(shape(ic, "M2 42 C2 34 16 32 32 32 C48 32 62 34 62 42 C62 50 48 54 32 54 C16 54 2 50 2 42 Z", pal, ic.lg(pal, 0, 0, 0, 1)))
        s.append(f'<path d="M5 45 C12 50 22 52 32 52 C42 52 52 50 59 45 C57 50 46 54 32 54 C18 54 7 50 5 45 Z" fill="{pal[2]}"/>')
        s.append(shape(ic, "M18 38 C18 24 24 14 32 14 C40 14 46 24 46 38 C38 42 26 42 18 38 Z", pal, ic.lg((pal[0], pal[0], pal[1]), 0, 0, 0, 1)))
        s.append(f'<path d="M18.2 31.5 C26 35 38 35 45.8 31.5 L46 38 C38 42 26 42 18 38 Z" fill="{band[1]}" stroke="{band[3]}" stroke-width="1.4"/>')
        s.append(line("M23 28 C23 22 26 18 30 17", HL, 2.2, 0.6))
    elif kind == "wizard":
        s.append(shape(ic, "M6 50 C6 44 18 42 32 42 C46 42 58 44 58 50 C58 55 46 58 32 58 C18 58 6 55 6 50 Z", band))
        s.append(shape(ic, "M14 48 C18 34 22 22 30 12 C36 4 46 2 54 6 C46 8 42 14 42 22 C42 32 46 40 50 48 C38 52 26 52 14 48 Z", pal))
        for x, y, r in ((26, 30, 3), (38, 38, 2.4), (34, 20, 2)):
            s.append(sparkle(x, y, r, (accent or PAL["yellow"])[1]))
    elif kind == "witch":
        s.append(shape(ic, "M4 50 C4 44 18 42 32 42 C46 42 60 44 60 50 C60 55 46 58 32 58 C18 58 4 55 4 50 Z", pal))
        s.append(shape(ic, "M16 48 C20 34 24 20 30 8 C33 2 38 2 40 6 C42 12 42 22 44 30 C46 38 48 44 50 48 C38 52 26 52 16 48 Z", pal))
        s.append(f'<path d="M16.8 44 C26 47 40 47 49.2 44 L50 48 C40 51.5 26 51.5 16 48 Z" fill="{band[1]}"/>')
        s.append(dot(35, 36, 2.2, "#ff3a4a"))
        s.append(dot(35, 36, 0.8, "#fff"))
    elif kind == "santa":
        s.append(shape(ic, "M12 44 C12 26 22 10 38 10 C48 10 54 18 56 30 C52 24 48 22 44 24 C48 30 50 38 50 44 Z", pal))
        s.append(shape(ic, "M8 46 C8 40 20 38 32 38 C44 38 56 40 56 46 C56 52 44 54 32 54 C20 54 8 52 8 46 Z", PAL["white"]))
        s.append(circle(ic, 56, 32, 6, PAL["white"]))
    elif kind == "pirate":
        s.append(shape(ic, "M4 40 C12 42 20 30 32 30 C44 30 52 42 60 40 C58 50 48 54 32 54 C16 54 6 50 4 40 Z", pal))
        s.append(shape(ic, "M14 40 C14 24 22 16 32 16 C42 16 50 24 50 40 C40 36 24 36 14 40 Z", pal))
        s.append(shape(ic, "M40 18 C44 8 52 4 60 6 C56 10 52 16 44 22 Z", accent or PAL["red"], sw=1.4))
        s.append(f'<path d="M14.5 38 C24 34 40 34 49.5 38 L50 42 C40 38.5 24 38.5 14 42 Z" fill="{(accent or PAL["red"])[1]}"/>')
        s.append(line("M26 26 L38 26 M28 23 L36 29 M36 23 L28 29", "#f4efe4", 1.6))
    elif kind == "police":
        s.append(shape(ic, "M8 30 C8 18 20 12 32 12 C44 12 56 18 56 30 C50 36 14 36 8 30 Z", pal))
        s.append(shape(ic, "M12 30 C18 34 46 34 52 30 L52 40 C46 43 18 43 12 40 Z", PAL["shadow"]))
        s.append(shape(ic, "M12 40 C18 43 46 43 52 40 C54 46 48 52 32 52 C16 52 10 46 12 40 Z", PAL["shadow"]))
        s.append(line("M14 37 C22 39.5 42 39.5 50 37", "#f6c453", 2))
        s += facet_gem(ic, 32, 23, 5.2, PAL["gold"])
    elif kind == "tophat":
        s.append(shape(ic, "M4 46 C4 40 18 38 32 38 C46 38 60 40 60 46 C60 52 46 54 32 54 C18 54 4 52 4 46 Z", pal))
        s.append(shape(ic, "M16 44 L18 8 C24 5 40 5 46 8 L48 44 C40 47 24 47 16 44 Z", pal))
        s.append(f'<path d="M16.8 32 C24 35 40 35 47.2 32 L47.6 39 C40 42 24 42 16.4 39 Z" fill="{band[1]}" stroke="{band[3]}" stroke-width="1.2"/>')
        s.append(f'<rect x="27" y="31" width="10" height="9" rx="1.5" fill="none" stroke="{(accent or PAL["gold"])[1]}" stroke-width="2.4"/>')
    elif kind == "bycocket":
        feather = accent or PAL["red"]
        s.append(shape(ic, "M44 40 C46 26 52 12 62 3 C62 16 56 30 50 42 Z", feather, sw=1.5))
        s.append(line("M47 40 C50 28 55 16 61 6", feather[3], 1.2, 0.7))
        s.append(shape(ic, "M12 44 C13 30 20 19 32 15 C42 12 52 16 53 28 L54 44 Z", pal))
        s.append(shape(ic, "M2 47 C12 42 26 41 40 41 L50 36 C56 32 61 36 60 42 C58 49 50 52 40 52 C24 53 10 52 2 47 Z", pal, ic.lg(pal, 0, 0, 0, 1)))
        s.append(line("M14 44 C24 42 38 42 48 40", pal[3], 1.4, 0.55))
        s.append(line("M19 36 C20 28 24 22 30 19", HL, 2.2, 0.55))
    elif kind == "hardhat":
        s.append(shape(ic, "M12 42 C12 22 20 10 32 10 C44 10 52 22 52 42 Z", pal))
        s.append(shape(ic, "M6 42 C6 38 10 38 32 38 C54 38 58 38 58 42 C58 47 54 48 32 48 C10 48 6 47 6 42 Z", pal))
        s.append(line("M32 11 L32 38", pal[2], 3, 0.6))
        s.append(f'<rect x="24" y="22" width="16" height="11" rx="4" fill="{PAL["shadow"][1]}" stroke="#0a0a12" stroke-width="1.4"/>')
        s.append(dot(32, 27.5, 4, "#fff6c4"))
        s.append(line("M18 30 C18 22 22 16 27 13", HL, 2.2, 0.6))
    return "".join(s)


def bunny_ears(ic):
    s = [shape(ic, "M8 50 C8 40 20 36 32 36 C44 36 56 40 56 50 C54 44 44 42 32 42 C20 42 10 44 8 50 Z", PAL["shadow"])]
    for d in ("M18 40 C12 26 12 8 20 4 C28 8 28 26 26 38 Z", "M38 38 C36 26 36 8 44 4 C52 8 52 26 46 40 Z"):
        s.append(shape(ic, d, PAL["white"]))
    for d in ("M20 36 C16 26 16 12 20 8 C24 12 24 26 23 35 Z", "M41 35 C40 26 40 12 44 8 C48 12 48 26 44 36 Z"):
        s.append(f'<path d="{d}" fill="#ffb3c8"/>')
    return "".join(s)


def glasses(ic):
    gold = PAL["gold"]
    s = tube(ic, "M27 31 C29 27 35 27 37 31", gold, 2.6)
    s += tube(ic, "M9 30 L3 26 M55 30 L61 26", gold, 2.6)
    for cx in (18, 46):
        s.append(f'<rect x="{cx - 10}" y="24" width="20" height="16" rx="7" fill="{ic.lg(PAL["navy"], 0, 0, 1, 1)}" stroke="{gold[3]}" stroke-width="5.4"/>')
        s.append(f'<rect x="{cx - 10}" y="24" width="20" height="16" rx="7" fill="none" stroke="{ic.lgu(gold, cx - 10, 24, cx + 10, 40)}" stroke-width="2.6"/>')
        s.append(line(f"M{cx - 6} 29 L{cx + 1} 29", HL, 2.4, 0.95))
        s.append(line(f"M{cx - 6} 33 L{cx - 3} 33", HL, 1.8, 0.7))
    return "".join(s)

def mask(ic, kind):
    s = []
    if kind == "horror":   # a hockey mask: slanted eye holes, red chevrons, rows of breathing holes
        s.append(shape(ic, "M32 4 C46 4 54 16 54 32 C54 48 44 60 32 60 C20 60 10 48 10 32 C10 16 18 4 32 4 Z", PAL["cream"]))
        eye = "M13 26 C16 19 25 19 29.5 26.5 C25.5 33 17 33 13 26 Z"
        s.append(f'<path d="{eye}" fill="#1a1612"/><path d="{mirror_x(eye)}" fill="#1a1612"/>')
        for d in ("M26 7 L32 15 L38 7 Z", "M12 36 L21 32 L21 41 Z", mirror_x("M12 36 L21 32 L21 41 Z")):
            s.append(f'<path d="{d}" fill="#d42a36" stroke="#6a0a12" stroke-width="1"/>')
        for x, y in ((26, 40), (32, 40), (38, 40), (29, 46.5), (35, 46.5), (32, 53)):
            s.append(dot(x, y, 2.5, "#3a3026"))
        s.append(line("M32 18 L32 33", "#b9a888", 1.6, 0.7))
    elif kind == "kitsune":   # a white fox mask: red ears and markings, closed smiling eyes
        s.append(shape(ic, "M11 4 L23 17 C27 15.5 37 15.5 41 17 L53 4 L55 30 C55 46 45 58 32 58 C19 58 9 46 9 30 Z", PAL["white"]))
        s.append(f'<path d="M14 11 L22 19 L15.5 25 Z" fill="#e8384a"/><path d="{mirror_x("M14 11 L22 19 L15.5 25 Z")}" fill="#e8384a"/>')
        s.append(shape(ic, "M32 18 C28.5 23 29.5 28 32 30 C34.5 28 35.5 23 32 18 Z", PAL["red"], sw=1.2))
        s.append(line("M16 33 C19 28.5 25 28.5 28 32.5", "#1a1a22", 3.4))
        s.append(line(mirror_x("M16 33 C19 28.5 25 28.5 28 32.5"), "#1a1a22", 3.4))
        s.append(line("M12 40 L21 42", "#e8384a", 3.2))
        s.append(line(mirror_x("M12 40 L21 42"), "#e8384a", 3.2))
        s.append(f'<path d="M28.5 43 L35.5 43 L32 47 Z" fill="#1a1a22"/>')
        s.append(line("M27 51 C30 53.5 34 53.5 37 51", "#e8384a", 2))
    elif kind == "mystery":
        s.append(shape(ic, "M12 10 L18 16 C24 14 40 14 46 16 L52 10 L54 34 C54 48 44 58 32 58 C20 58 10 48 10 34 Z", PAL["red"]))
        s.append(pattern_marks("checker", 10, 14, 54, 56))
        s.append(f'<path d="M18 30 L28 32 L26 36 L18 34 Z M46 30 L36 32 L38 36 L46 34 Z" fill="#ffd23a"/>')
        s.append(f'<path d="M22 44 L42 44 L38 50 L26 50 Z" fill="#2a0a0a"/>')
        s.append(f'<path d="M26 44 L28 47 L30 44 M34 44 L36 47 L38 44" fill="#fff"/>')
    return "".join(s)


# ----------------------------------------------------------------------------- body armor
TORSO = ("M20 8 C24 12 40 12 44 8 L54.5 14 C58 18 59 26 58.4 32 L48 32 L48 54 C48 57 46 58 44 58 L20 58 "
         "C18 58 16 57 16 54 L16 32 L5.6 32 C5 26 6 18 9.5 14 Z")   # sleeves land on whole pixels at 20x20


def chestplate(ic, pal, trim=None, pattern=None, emblem=None):
    s = [shape(ic, TORSO, pal, ic.lg(pal, 0.1, 0, 0.9, 1))]
    s.append(f'<path d="M32 11 C36 11 40 10 44 8 L54 14 C57 18 58 26 57 32 L48 32 L48 54 C48 57 46 58 44 58 L32 58 Z" fill="{pal[3]}" opacity=".15"/>')
    if pattern:
        s.append(pattern_marks(pattern, 16, 12, 48, 58))
    s.append(f'<path d="M22 9 C26 17 38 17 42 9" fill="{pal[3]}" opacity=".85"/>')
    s.append(line("M32 17 L32 56", pal[3], 1.4, 0.5))
    s.append(line("M18 42 C26 45 38 45 46 42 M18 49 C26 52 38 52 46 49", pal[3], 1.4, 0.45))
    for cx in (15, 49):
        s.append(f'<ellipse cx="{cx}" cy="20" rx="8" ry="6.5" fill="{ic.lg(pal)}" stroke="{pal[2]}" stroke-width="1.8"/>')   # mid-tone edge: no dark specks in pixels
    if trim:
        s.append(line("M8 26 C10 18 14 14 22 12", trim[1], 2.2))
        s.append(line("M56 26 C54 18 50 14 42 12", trim[1], 2.2))
        s.append(line("M17 56 L47 56", trim[1], 2.6))
    if emblem == "cross":
        s.append(f'<path d="M29 22 L35 22 L35 28 L41 28 L41 34 L35 34 L35 42 L29 42 L29 34 L23 34 L23 28 L29 28 Z" fill="#c8323c" stroke="#3a0a10" stroke-width="1"/>')
    elif emblem:
        s += gem(ic, 32, 30, 4, emblem)
    s.append(line("M12 16 C14 14 17 13 20 13", HL, 2, 0.6))
    s.append(line("M20 22 L20 40", HL, 1.8, 0.35))
    return "".join(s)


def cloak(ic, pal, trim=None, collar=None, inner=None):
    s = []
    if collar:
        s.append(shape(ic, "M8 20 C12 10 20 12 22 18 L32 26 L42 18 C44 12 52 10 56 20 C52 24 48 26 44 28 L32 34 L20 28 C16 26 12 24 8 20 Z", collar))
    s.append(shape(ic, "M32 6 C42 6 48 14 48 24 C50 34 54 46 56 58 L8 58 C10 46 14 34 16 24 C16 14 22 6 32 6 Z", pal, ic.lg(pal, 0.2, 0, 0.8, 1)))
    s.append(f'<path d="M24 21 C24 13 40 13 40 21 C40 29 36 33 32 33 C28 33 24 29 24 21 Z" fill="{(inner or PAL["shadow"])[2]}" stroke="{pal[3]}" stroke-width="1.6"/>')
    s.append(line("M32 34 L32 57", pal[3], 1.6, 0.55))
    if trim:
        s.append(line("M32 7 C23 7 17 14 17 24 C15 34 11 46 9 57", trim[1], 2.4))
        s.append(line("M32 7 C41 7 47 14 47 24 C49 34 53 46 55 57", trim[1], 2.4))
        s.append(line("M24 21 C24 13 40 13 40 21", trim[1], 2))
    s.append(line("M20 20 C20 14 24 10 28 9", HL, 2, 0.5))
    return "".join(s)


def shirt(ic, pal, long_=False, pattern=None):
    if long_:
        d = "M20 8 L26 6 C28 10 36 10 38 6 L44 8 L52 16 L57 46 L49 47 L46 26 L46 56 L18 56 L18 26 L15 47 L7 46 L12 16 Z"
    else:
        d = "M20 8 L26 6 C28 10 36 10 38 6 L44 8 L57 18 L51 29 L46 25 L46 56 L18 56 L18 25 L13 29 L7 18 Z"
    s = [shape(ic, d, pal, ic.lg(pal, 0, 0, 0, 1))]
    if long_:
        s.append(line("M8 42.5 L15.6 43.5", pal[2], 2.6))
        s.append(line(mirror_x("M8 42.5 L15.6 43.5"), pal[2], 2.6))
        s.append(line("M32 11 L32 55", pal[2], 1.4, 0.7))
        for y in (18, 27, 36, 45):
            s.append(dot(32, y, 1.7, pal[3], 0.75))
    if pattern == "chain":
        for j in range(8):
            for i in range(6):
                x = 21 + i * 4.4 + (2.2 if j % 2 else 0)
                y = 14 + j * 5.2
                if x < 45:
                    s.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="1.7" fill="none" stroke="{pal[3]}" stroke-width=".9" opacity=".6"/>')
    s.append(line("M26 6.5 C28 12 36 12 38 6.5", pal[3], 1.8, 0.8))
    s.append(line("M22 14 L22 50", HL, 1.8, 0.4))
    s.append(line("M42 14 L42 50", HL, 1.8, 0.4))
    return "".join(s)


def greaves(ic, pal, trim=None, pattern=None):
    legs = ("M11 12 L53 12 L54 53 C54 56.5 52 58 49 58 L37 58 C35 58 34 56.5 34 54.5 L32.4 29 L31.6 29 "
            "L30 54.5 C30 56.5 29 58 27 58 L15 58 C12 58 10 56.5 10 53 Z")
    s = [shape(ic, legs, pal, ic.lg(pal, 0, 0, 0, 1))]   # top to bottom: both legs shade alike
    if pattern:
        s.append(pattern_marks(pattern, 10, 12, 54, 56))
    band = trim or pal
    s.append(f'<rect x="9" y="6" width="46" height="9" rx="3" fill="{ic.lg(band, 0, 0, 0, 1)}" stroke="{band[3]}" stroke-width="2"/>')
    for cx in (20.8, 43.2):
        knee = f"M{cx - 7} 36 L{cx} 30.5 L{cx + 7} 36 L{cx + 5.5} 43 L{cx} 46 L{cx - 5.5} 43 Z"
        s.append(shape(ic, knee, band, ic.lg(band, 0, 0, 0, 1), 1.8))
    if trim:
        s.append(line("M11.5 54.5 L29.5 54.5 M34.5 54.5 L52.5 54.5", trim[1], 2.6))
    return "".join(s)

def lifebuoy(ic):
    s = [f'<circle cx="32" cy="32" r="20" fill="none" stroke="#3a0a14" stroke-width="17"/>',
         f'<circle cx="32" cy="32" r="20" fill="none" stroke="{ic.lgu(PAL["red"])}" stroke-width="13"/>']
    for a in (45, 135, 225, 315):
        s.append(f'<path d="M32 12 A20 20 0 0 1 {f(32 + 20 * math.sin(math.radians(28)))} {f(32 - 20 * math.cos(math.radians(28)))}" '
                 f'fill="none" stroke="#f4f4f8" stroke-width="13" transform="rotate({a - 14} 32 32)"/>')
    s.append(line("M18 22 C20 18 24 15 28 14", HL, 2.2, 0.6))
    return "".join(s)


def boot(ic, pal, trim=None, pattern=None, kind="boot", gem_=None):
    s = []
    if kind == "boot":
        d = "M24 6 L50 6 L51 40 L53 52 C53 56 51 58 48 58 L10 58 C7 58 5 56 5 53 C5 45 12 41 21 40 L24 38 Z"
        s.append(shape(ic, d, pal, ic.lg(pal, 0, 0, 1, 0.5)))
        if pattern:
            s.append(pattern_marks(pattern, 10, 6, 52, 56))
        s.append(f'<rect x="22" y="4" width="30" height="8" rx="3" fill="{ic.lg(trim or pal, 0, 0, 0, 1)}" stroke="{(trim or pal)[3]}" stroke-width="1.6"/>')
        s.append(f'<path d="M6 51 L53 51 L53 54 C53 56.5 51 58 48 58 L10 58 C7 58 5.5 56.5 5.5 54 Z" fill="{pal[3]}" opacity=".7"/>')
        if trim:
            s.append(line("M24 38 C20 40 14 42 9 46", trim[1], 2.2))
        s.append(line("M29 15 L29 36", HL, 2.2, 0.45))
    elif kind == "loafer":
        s.append(shape(ic, "M6 44 C6 36 16 32 26 32 C34 32 38 26 46 26 C54 26 58 32 58 40 L58 50 C58 54 56 56 52 56 L10 56 C7 56 6 54 6 50 Z", pal))
        s.append(f'<path d="M30 34 C36 32 42 30 50 32 C48 38 40 40 32 40 Z" fill="{pal[3]}" opacity=".55"/>')
        if gem_:
            s += gem(ic, 22, 38, 3.4, gem_)
        s.append(line("M12 40 C16 36 22 34 28 34", HL, 2, 0.6))
    elif kind == "sandal":   # seen from above: a foot-shaped sole, a thong strap, an ankle strap
        sole = "M32 3 C44 3 48 13 47 24 C46 34 45 44 45 51 C45 57 39.5 61 32 61 C24.5 61 19 57 19 51 C19 44 18 34 17 24 C16 13 20 3 32 3 Z"
        s.append(shape(ic, sole, PAL["sand"], ic.lg(PAL["sand"], 0, 0, 0, 1)))
        s += tube(ic, "M17.6 30 L32 12.8 L46.4 30", pal, 4.8)
        s += tube(ic, "M19.2 46 C25 50.5 39 50.5 44.8 46", pal, 4.8)
        s.append(circle(ic, 32, 12.8, 3.2, pal, sw=1.4))
    elif kind == "clog":   # a Dutch clog from the side: upturned toe, tall heel, opening on top, painted flower
        body = "M3 31 C6 31 10 32 16 31 L31 25 C34 24 37 23.5 40 23.5 L56 21 C60 20.5 62 24 62 29 L62 46 C62 53 58 57 51 57 L22 57 C13 57 8 51 5.5 43 C4 39 2.6 35 3 31 Z"
        s.append(shape(ic, body, pal, ic.lg(pal, 0, 0, 0.6, 1)))
        s.append(f'<path d="M36.5 25.5 C43 22.5 52 21.5 58 23.2 C57.5 28.5 49 31 39.5 30 C37.5 29.4 36.3 27.6 36.5 25.5 Z" fill="{pal[3]}" stroke="{pal[3]}" stroke-width="1.4"/>')
        s.append(f'<path d="M40 26.8 C45 25 51 24.6 55.5 25.4" fill="none" stroke="{pal[2]}" stroke-width="1.6" stroke-linecap="round" opacity=".8"/>')
        for d in ("M12 40 C22 37 36 36 58 38", "M14 47 C26 45 40 45 59 46"):   # grain
            s.append(line(d, pal[2], 1.4, 0.55))
        for k in range(5):   # painted flower on the toe
            a = k * 2 * math.pi / 5 - math.pi / 2
            s.append(dot(21 + 3.2 * math.cos(a), 39.5 + 3.2 * math.sin(a), 2.2, "#e2343e"))
        s.append(dot(21, 39.5, 1.8, "#fff2a6"))
        s.append(line("M8 34 C14 34.5 22 32 30 28.5", HL, 2.2, 0.6))
    elif kind == "shackle":
        s.append(f'<ellipse cx="32" cy="30" rx="24" ry="18" fill="none" stroke="#141216" stroke-width="12"/>')
        s.append(f'<ellipse cx="32" cy="30" rx="24" ry="18" fill="none" stroke="{ic.lgu(PAL["slate"])}" stroke-width="8"/>')
        s.append(f'<rect x="27" y="40" width="10" height="16" rx="2" fill="{ic.lg(PAL["slate"])}" stroke="#141216" stroke-width="1.8"/>')
        s.append(line("M32 44 L32 52", "#141216", 2))
        for x in (14, 50):
            s.append(dot(x, 30, 2.2, "#141216"))
        s.append(line("M14 22 C18 16 26 13 32 13", HL, 2, 0.5))
    return "".join(s)


def shield(ic, kind, pal, rim=None, emblem=None, boss=None):
    rim = rim or pal
    s = []
    if kind == "heater":
        d = "M12 8 L52 8 C53 8 54 9 54 10 L54 28 C54 42 45 52 32 58 C19 52 10 42 10 28 L10 10 C10 9 11 8 12 8 Z"
        s.append(shape(ic, d, rim, ic.lg(rim, 0, 0, 1, 1), 2))
        inner = "M15 12 L49 12 L49 28 C49 39 42 47 32 52 C22 47 15 39 15 28 Z"
        s.append(shape(ic, inner, pal, ic.lg(pal, 0.1, 0, 0.9, 1), 1.2))
        clip_x = (15, 12, 49, 52)
    elif kind == "oval":
        s.append(f'<ellipse cx="32" cy="32" rx="21" ry="26" fill="{ic.lg(rim)}" stroke="{rim[3]}" stroke-width="2"/>')
        s.append(f'<ellipse cx="32" cy="32" rx="16.5" ry="21.5" fill="{ic.rg(pal)}" stroke="{pal[3]}" stroke-width="1.2"/>')
        clip_x = (16, 11, 48, 53)
    elif kind == "round":
        s.append(circle(ic, 32, 32, 25, rim, ic.lg(rim)))
        s.append(circle(ic, 32, 32, 20, pal, ic.rg(pal), 1.2))
        clip_x = (13, 13, 51, 51)
    elif kind == "tower":
        s.append(f'<rect x="12" y="5" width="40" height="54" rx="6" fill="{ic.lg(rim)}" stroke="{rim[3]}" stroke-width="2"/>')
        s.append(f'<rect x="16" y="9" width="32" height="46" rx="4" fill="{ic.lg(pal, 0.1, 0, 0.9, 1)}" stroke="{pal[3]}" stroke-width="1.2"/>')
        clip_x = (16, 9, 48, 55)
    x0, y0, x1, y1 = clip_x
    if emblem == "cross":
        s.append(f'<path d="M28 13 L36 13 L36 25 L47 25 L47 33 L36 33 L36 50 L28 50 L28 33 L17 33 L17 25 L28 25 Z" fill="#d23240" stroke="#4a0a12" stroke-width="1.2"/>')
    elif emblem == "sun":
        for k in range(8):
            a = k * math.pi / 4
            s.append(line(f"M{f(32 + 7 * math.cos(a))} {f(30 + 7 * math.sin(a))} L{f(32 + 13 * math.cos(a))} {f(30 + 13 * math.sin(a))}", "#ffc43a", 2.6))
        s.append(circle(ic, 32, 30, 6, PAL["gold"]))
    elif emblem == "falcon":
        s.append(f'<path d="M32 18 C26 14 18 16 16 22 C22 22 26 24 28 28 C24 30 22 36 24 42 L32 36 L40 42 C42 36 40 30 36 28 C38 24 42 22 48 22 C46 16 38 14 32 18 Z" fill="#3a2410" opacity=".9"/>')
    elif emblem == "chocolate":
        for i in range(2):
            for j in range(3):
                s.append(f'<rect x="{19 + i * 14}" y="{12 + j * 14}" width="12" height="12" rx="2" fill="{ic.lg(PAL["chocolate"])}" stroke="#2a0e06" stroke-width="1.2"/>')
    elif emblem == "turtle":
        s.append(f'<path d="M32 18 L40 23 L40 33 L32 38 L24 33 L24 23 Z" fill="none" stroke="#1c4a10" stroke-width="2"/>')
        s.append(line("M32 18 L32 8 M40 23 L48 18 M40 33 L48 40 M32 38 L32 54 M24 33 L16 40 M24 23 L16 18", "#1c4a10", 2))
    elif emblem == "x":
        s += tube(ic, "M17 17 L47 47", PAL["steel"], 4) + tube(ic, "M47 17 L17 47", PAL["steel"], 4)
    elif emblem == "cracks":
        s.append(pattern_marks("cracks", 14, 10, 50, 56))
    elif emblem == "planks":
        s.append(line("M24 9 L24 55 M40 9 L40 55", pal[3], 1.6, 0.6))
    elif emblem == "mottle":
        s.append(pattern_marks("mottle", 14, 10, 50, 56))
    elif emblem == "bumps":
        for x, y in ((26, 20), (38, 20), (24, 32), (32, 30), (40, 32), (28, 43), (37, 43)):
            s.append(dot(x, y, 2.8, pal[2], 0.8))
            s.append(dot(x - 0.8, y - 0.8, 1.1, pal[0], 0.9))
    elif emblem == "streak":
        s.append(line("M22 16 C30 20 26 30 34 34 C40 37 38 46 44 50", "#ffffff", 2.4, 0.4))
    if boss:
        s += gem(ic, 32, 32, 5, boss)
    s.append(line("M15 14 L15 26" if kind in ("heater", "tower") else "M16 24 C17 18 21 13 26 11", HL, 2.2, 0.55))
    return "".join(s)


# ----------------------------------------------------------------------------- jewellery
METAL = {"emerald": PAL["emerald"], "gold": PAL["gold"], "iron": PAL["iron"], "platinum": PAL["platring"]}
GEMS = {"air": PAL["white"], "earth": PAL["leaf"], "fire": PAL["ruby"], "water": PAL["amethyst"]}


def ring(ic, metal, style="plain", gem_=None):
    m = METAL[metal]
    s = []
    if style == "attack":
        d = "M32 8 C39 17 49 25 49 39 C49 49 41 56 32 56 C23 56 15 49 15 39 C15 25 25 17 32 8 Z"
        s += tube(ic, d, m, 2.8, ic.lgu(m, 15, 8, 49, 56))   # no inner highlight: it thickened the thin band
        return "".join(s)
    # thin band, the same weight as the amulet cords (tube 2.8); flat and mana rings are a little wider
    width = {"flat": 4.5, "mana": 4}.get(style, 2.8)
    s.append(f'<circle cx="32" cy="40" r="15.5" fill="none" stroke="{m[3]}" stroke-width="{width + 3}"/>')
    s.append(f'<circle cx="32" cy="40" r="15.5" fill="none" stroke="{ic.lgu(m, 16, 24, 48, 56)}" stroke-width="{width}"/>')
    if style in ("crit", "critdmg"):
        s.append(f'<rect x="18" y="12" width="28" height="15" rx="3.5" fill="{ic.lg(m)}" stroke="{m[3]}" stroke-width="2"/>')
        for i in range(4):
            for j in range(2):
                if (i + j) % 2 == 0:
                    s.append(f'<rect x="{20 + i * 6}" y="{14 + j * 5.5}" width="6" height="5.5" fill="{m[3]}" opacity=".45"/>')
        if style == "critdmg":
            s.append(shape(ic, "M32 12 L20 4 L20 18 Z", PAL["ruby"], sw=1.4))
            s.append(shape(ic, "M32 12 L44 4 L44 18 Z", PAL["ruby"], sw=1.4))
            s.append(circle(ic, 32, 12, 3.4, PAL["ruby"], sw=1.2))
    elif style == "mana":
        s.append(f'<rect x="16" y="19.2" width="32" height="9.6" rx="4.8" fill="{ic.lg(m, 0, 0, 0, 1)}" stroke="{m[3]}" stroke-width="2"/>')
        s.append(circle(ic, 32, 24, 3.2, PAL["sapphire"], sw=1.4))   # 2 pixels wide: symmetric at 20x20
    elif style == "flat":
        s.append(f'<rect x="18" y="21" width="28" height="8" rx="3" fill="{m[0]}" stroke="{m[3]}" stroke-width="2"/>')
        s.append(line("M22 25 L42 25", m[2], 1.4, 0.6))
    if style == "gem" and gem_:
        s.append(f'<path d="M22 24 L26 17 L38 17 L42 24 L37 28 L27 28 Z" fill="{ic.lg(m)}" stroke="{m[3]}" stroke-width="1.6"/>')
        s += facet_gem(ic, 32, 13, 10, gem_)
    return "".join(s)


def amulet(ic, pendant, cord=None, kind="stone", frame=None):
    cord = cord or PAL["wood"]
    s = tube(ic, "M21 40 C4 30 7 5 29 4 C48 3 58 17 50 32 C48 36 46 38 43 40", cord, 2.8)
    cx, cy = 32, 45
    k = 1.3
    if kind == "stone":
        s.append(circle(ic, cx, cy, 13, pendant))
        s.append(dot(cx - 4.5, cy - 4.5, 3, HL, 0.7))
    elif kind == "framed":
        s.append(circle(ic, cx, cy, 15.5, frame or PAL["orange"], ic.lg(frame or PAL["orange"])))
        for j in range(10):
            a = j * math.pi / 5
            s.append(dot(cx + 13.4 * math.cos(a), cy + 13.4 * math.sin(a), 1.5, "#fff4d0"))
        s += gem(ic, cx, cy, 9.5, pendant)
    elif kind == "square":
        s.append(f'<rect x="{cx - 13}" y="{cy - 13}" width="26" height="26" rx="4" fill="{ic.lg(PAL["wood"])}" stroke="{PAL["wood"][3]}" stroke-width="2"/>')
        s.append(line(f"M{cx - 9} {cy - 9} L{cx + 9} {cy - 9}", HL, 1.6, 0.4))
        s += gem(ic, cx, cy, 6, pendant)
    elif kind == "eye":
        s.append(circle(ic, cx, cy, 13, pendant))
        s.append(f'<ellipse cx="{cx + 1}" cy="{cy}" rx="3.8" ry="9" fill="#0c1a0c"/>')
        s.append(dot(cx - 4, cy - 5, 2.6, HL, 0.8))
    elif kind == "skull":
        s.append(f'<g transform="translate({cx} {cy}) scale(1.25) translate({-cx} {-cy})">')
        s.append(shape(ic, f"M{cx} {cy - 11} C{cx + 9} {cy - 11} {cx + 12} {cy - 4} {cx + 11} {cy + 2} C{cx + 10} {cy + 6} {cx + 7} {cy + 7} {cx + 6} {cy + 11} L{cx - 6} {cy + 11} C{cx - 7} {cy + 7} {cx - 10} {cy + 6} {cx - 11} {cy + 2} C{cx - 12} {cy - 4} {cx - 9} {cy - 11} {cx} {cy - 11} Z", PAL["white"]))
        s.append(f'<ellipse cx="{cx - 4.5}" cy="{cy - 1}" rx="3" ry="3.4" fill="#2a2c34"/><ellipse cx="{cx + 4.5}" cy="{cy - 1}" rx="3" ry="3.4" fill="#2a2c34"/>')
        s.append(line(f"M{cx - 3} {cy + 8} L{cx - 3} {cy + 10} M{cx} {cy + 8} L{cx} {cy + 10} M{cx + 3} {cy + 8} L{cx + 3} {cy + 10}", "#2a2c34", 1.2))
        s.append('</g>')
    elif kind == "lucky":
        s.append(circle(ic, cx, cy, 13, PAL["cream"]))
        s.append(f'<path transform="translate({cx} {cy}) scale(1.35) translate({-cx} {-cy})" d="M{cx} {cy + 6} C{cx - 8} {cy} {cx - 7} {cy - 7} {cx - 2.5} {cy - 5.5} C{cx - 1} {cy - 5} {cx} {cy - 3.5} {cx} {cy - 3} C{cx} {cy - 3.5} {cx + 1} {cy - 5} {cx + 2.5} {cy - 5.5} C{cx + 7} {cy - 7} {cx + 8} {cy} {cx} {cy + 6} Z" fill="#e2343e"/>')
    return "".join(s)


def necklace(ic, metal, pendant=None, kind="mining"):
    m = {"copper": PAL["copper"], "gold": PAL["gold"], "platinum": PAL["iron"]}.get(metal, PAL["gold"])
    s = []
    if kind == "mining":
        d = "M16 46 C6 36 8 18 22 12 C34 6 50 10 54 22 C57 32 50 40 40 42 C34 43 30 40 28 44"
        # a solid chain: dark link dashes read as holes once the icon is pixelated
        s.append(line(d, m[3], 7))
        s.append(line(d, ic.lgu(m), 4.2))
        s.append(circle(ic, 18, 45, 12, m, ic.lg(m)))
        s += gem(ic, 18, 45, 7.5, pendant)
    elif kind == "liora":
        s.append(f'<circle cx="32" cy="30" r="21" fill="none" stroke="{m[3]}" stroke-width="7"/>')
        s.append(f'<circle cx="32" cy="30" r="21" fill="none" stroke="{ic.lgu(m)}" stroke-width="3.6"/>')
        s.append(f'<circle cx="32" cy="30" r="21" fill="none" stroke="{m[3]}" stroke-width="3.6" stroke-dasharray="1.2 3" opacity=".45"/>')
        s.append(shape(ic, "M32 60 C22 54 22 46 27 44 C30 43 32 45 32 47 C32 45 34 43 37 44 C42 46 42 54 32 60 Z", PAL["ruby"]))
        s.append(dot(28.5, 48.5, 1.6, HL, 0.8))
    elif kind == "beads":
        for k in range(18):
            a = k * math.pi * 2 / 18
            color = ["#b8386a", "#2eb0b8", "#9dff6a"][k % 3] if k % 2 == 0 else "#7a2a4a"
            s.append(f'<circle cx="{f(32 + 22 * math.cos(a))}" cy="{f(32 + 20 * math.sin(a))}" r="4.2" fill="{color}" stroke="#1c0a12" stroke-width="1.4"/>')
        s.append(shape(ic, "M24 44 C24 36 40 36 40 44 Z", PAL["red"], sw=1.4))
        s.append(f'<rect x="29" y="44" width="6" height="7" rx="2" fill="#f1e6c8" stroke="#3a3226" stroke-width="1.2"/>')
        s.append(dot(28.5, 41, 1.2, "#fff"))
        s.append(dot(35, 40.5, 1.4, "#fff"))
    return "".join(s)


# ----------------------------------------------------------------------------- tools
def glove(ic, pal, pattern=None, cuff=None):
    d = ("M18.6 50 L18.6 36 L13 30 C10.5 27.5 11 23.5 14.5 23.5 C16.5 23.5 17.8 25 18.6 27 "
         "L18.6 12 C18.6 9 23 9 23 12 L23 26 L25 26 L25 8 C25 5 29.4 5 29.4 8 L29.4 26 L31.4 26 "
         "L31.4 10 C31.4 7 35.8 7 35.8 10 L35.8 26 L37.8 26 L37.8 14 C37.8 11 42.2 11 42.2 14 "
         "L42.2 38 C42.2 44 41.4 47 41.4 50 Z")
    s = [shape(ic, d, pal, ic.lg(pal, 0, 0, 0, 1))]
    if pattern == "scales":
        for x, y in ((23, 36), (29, 34), (35, 36), (26, 42), (32, 42), (38, 42)):
            s.append(f'<path d="M{x - 2.4} {y} A2.4 2.4 0 0 0 {x + 2.4} {y}" fill="none" stroke="{pal[0]}" stroke-width="1.2" opacity=".6"/>')
    s.append(f'<rect x="16" y="48" width="28.8" height="9.6" rx="2.5" fill="{ic.lg(cuff or pal, 0, 0, 0, 1)}" stroke="{(cuff or pal)[3]}" stroke-width="1.6"/>')
    s.append(line("M20.8 13 L20.8 24 M27.2 9 L27.2 24 M33.6 11 L33.6 24", HL, 1.3, 0.4))
    return "".join(s)

def broom(ic):
    s = tube(ic, "M10 6 L40 40", PAL["darkwood"], 3.6)
    s.append(shape(ic, "M38 36 L46 30 L60 50 C58 56 52 60 46 58 Z", PAL["sand"]))
    s.append(line("M44 36 L52 54 M48 34 L56 50 M41 40 L48 56", PAL["sand"][2], 1.2, 0.7))
    s.append(f'<rect x="36" y="32" width="10" height="6" rx="2" transform="rotate(-37 41 35)" fill="{PAL["red"][1]}" stroke="#2c0608" stroke-width="1.2"/>')
    return "".join(s)


def lantern(ic):
    s = [line("M26 10 C26 2 38 2 38 10", "#3a3440", 2.6)]
    s.append(shape(ic, "M18 16 L46 16 L42 10 L22 10 Z", PAL["shadow"]))
    s.append(f'<rect x="18" y="16" width="28" height="34" rx="4" fill="{ic.rg(PAL["fire"], .5, .55, .6)}" stroke="#141216" stroke-width="2"/>')
    s.append(line("M25 17 L25 49 M39 17 L39 49", "#141216", 2.4))
    s.append(shape(ic, "M32 44 C26 42 26 34 32 26 C38 34 38 42 32 44 Z", PAL["yellow"], sw=1))
    s.append(shape(ic, "M16 50 L48 50 L46 58 L18 58 Z", PAL["shadow"]))
    return "".join(s)


def torch(ic):
    s = tube(ic, "M50 61 L30 31", PAL["darkwood"], 6)
    for t in (0.72, 0.82):   # cloth wraps near the top of the handle
        x, y = 50 + (30 - 50) * t, 61 + (31 - 61) * t
        s.append(line(f"M{f(x - 4)} {f(y - 2.6)} L{f(x + 4)} {f(y + 2.6)}", "#d8c09c", 3))
    s.append(shape(ic, "M19 27 L35 27 L32 35 L22 35 Z", PAL["slate"], ic.lg(PAL["slate"], 0, 0, 0, 1), 1.8))
    s.append(shape(ic, "M27 29 C15 28 12 18 18 10 C19 15 22 16 22 12 C22 7 25 3 29 1 C28 7 34 9 34 15 C36 13 36 10 35 8 C41 14 40 26 27 29 Z",
                   PAL["fire"], ic.lg(PAL["fire"], 0.5, 0, 0.5, 1)))
    s.append(shape(ic, "M27 27 C21 26 19.5 20 22.5 15 C23.5 18 25.5 18 26.5 15 C28.5 18 32 20 31 24 C30.5 26 29 27 27 27 Z", PAL["yellow"], sw=1))
    s.append(f'<path d="M27 26 C25 25.5 24.5 23 26 21 C26.5 22.5 27.5 22.5 28 21 C29 23 28.8 25.6 27 26 Z" fill="#fffbe8"/>')
    return "".join(s)

def telescope(ic):
    s = [f'<rect x="4" y="24" width="26" height="16" rx="3" fill="{ic.lg(PAL["gold"], 0, 0, 0, 1)}" stroke="#3a1e06" stroke-width="2"/>',
         f'<rect x="28" y="26" width="22" height="12" rx="3" fill="{ic.lg(PAL["crimson"], 0, 0, 0, 1)}" stroke="#2a0814" stroke-width="2"/>',
         f'<rect x="48" y="28" width="12" height="8" rx="2" fill="{ic.lg(PAL["gold"], 0, 0, 0, 1)}" stroke="#3a1e06" stroke-width="2"/>',
         f'<rect x="8" y="23" width="4" height="18" rx="1.5" fill="{PAL["gold"][2]}" stroke="#3a1e06" stroke-width="1.4"/>',
         f'<ellipse cx="4.5" cy="32" rx="2.5" ry="7" fill="#bfe6ff" stroke="#3a1e06" stroke-width="1.6"/>']
    s.append(line("M14 27 L28 27", HL, 1.8, 0.6))
    s.append(line("M31 29 L46 29", HL, 1.6, 0.5))
    return rot(s, -35)


def skull(ic, pal, eyes="#e6e04a", cracks=None):
    d = "M32 6 C46 6 56 16 56 28 C56 36 52 40 48 42 L48 52 C48 55 46 57 43 57 L21 57 C18 57 16 55 16 52 L16 42 C12 40 8 36 8 28 C8 16 18 6 32 6 Z"
    s = [shape(ic, d, pal, ic.lg(pal, 0.1, 0, 0.9, 1))]
    s.append(f'<ellipse cx="22" cy="30" rx="6.5" ry="7" fill="#141216"/><ellipse cx="42" cy="30" rx="6.5" ry="7" fill="#141216"/>')
    s.append(dot(22, 31, 2.8, eyes))
    s.append(dot(42, 31, 2.8, eyes))
    s.append(f'<path d="M32 38 L28 45 L36 45 Z" fill="#141216"/>')
    s.append(line("M22 50 L22 56 M27 50 L27 56 M32 50 L32 56 M37 50 L37 56 M42 50 L42 56", "#141216", 1.4, 0.7))
    if cracks:
        s.append(line("M36 8 L40 16 L36 22 M14 22 L20 18 L18 12", cracks, 2.2))
    s.append(line("M16 20 C18 14 24 10 30 9", HL, 2, 0.5))
    return "".join(s)


# ----------------------------------------------------------------------------- specs
def C(*stops):
    """Custom palette shortcut (hi, mid, lo, outline)."""
    return tuple(stops)


P = PAL
SPECS = {
    # ---------------------------------------------------------------- weapons
    "Abyssal Edge": lambda ic: sword(ic, C("#eaffff", "#5ad4ff", "#1c64b4", "#0a2046"), P["azurite"], shape_="crystal", w=8, gshape="wing", gw=13, gem_=P["cyan"], extra="glow:#8ff0ff"),
    "Abyssal Pincer": lambda ic: staff(ic, P["violet"], "claw", P["fire"], P["orange"]),
    "Azurite Axe": lambda ic: axe(ic, P["azurite"], P["shadow"], "crescent", edge="#bfe8ff"),
    "Brutal Staff": lambda ic: staff(ic, P["darkwood"], "eye", P["red"], P["slate"]),
    "Burning Dagger": lambda ic: dagger(ic, P["fire"], P["shadow"], shape_="curved", w=5.5, extra="flames"),
    "Caster Staff": lambda ic: staff(ic, P["darkwood"], "crystal", P["sapphire"], P["copper"]),
    "Chaosweaver": lambda ic: sword(ic, C("#f4f4f8", "#9a98a8", "#56546a", "#1a1824"), P["shadow"], shape_="cleaver", w=9, gw=11),
    "Chill Strike": lambda ic: sword(ic, C("#f0fffb", "#8ee8d6", "#2e8c8a", "#0c3030"), P["azurite"], shape_="straight", w=6.5, gshape="spiky", gem_=P["ice"]),
    "Cleaver": lambda ic: sword(ic, P["steel"], P["shadow"], P["wood"], shape_="cleaver", w=9, T=4, B=40, gw=6, extra="blood"),
    "Club": lambda ic: mace(ic, P["wood"], kind="club"),
    "Cool Stick": lambda ic: wand(ic, P["wood"], "leaf", P["olive"]),
    "Copper Sword": lambda ic: sword(ic, P["copper"], P["emerald"], shape_="straight", w=5.5),
    "Cosmic Coil": lambda ic: staff(ic, P["violet"], "coil", P["cyan"], P["pink"], rings=False),
    "Dawn's Justice": lambda ic: sword(ic, C("#fff6c0", "#ffb03a", "#d05a1c", "#3e1406"), P["shadow"], shape_="straight", w=7.5, gshape="wing", gw=14, gem_=P["sapphire"], pgem=P["sapphire"]),
    "Drakespine Blade": lambda ic: sword(ic, P["plum"], P["mint"], shape_="double_serrated", w=6.5, gshape="spiky", gem_=P["mint"]),
    "Duststrike": lambda ic: sword(ic, P["sand"], P["sand"], shape_="wavy", w=9, gw=10, extra="rock"),
    "Earth Staff": lambda ic: staff(ic, P["wood"], "sprout", P["emerald"]),
    "Earthshaper": lambda ic: sword(ic, C("#c8ffb0", "#f0a8a0", "#a45062", "#2e1016"), P["salmon"], shape_="straight", w=7, gshape="cross", gw=13, extra="vines"),
    "Expert Staff": lambda ic: staff(ic, P["darkwood"], "claw", P["leaf"], P["white"]),
    "Frostcurse": lambda ic: dagger(ic, P["ice"], P["azurite"], shape_="serrated", w=6, T=2, extra="glow:#ffffff"),
    "Frostheart Claymore": lambda ic: sword(ic, C("#ffffff", "#6ee0ff", "#1a88d8", "#08305a"), P["azurite"], shape_="crystal", w=9.5, gshape="cross", gw=14, gem_=P["ice"]),
    "Ghostweave Sword": lambda ic: sword(ic, C("#e8fff8", "#7ec8c0", "#2e6a70", "#0c2428"), P["azurite"], shape_="taper", w=6, gshape="spiky", gw=11),
    "Gilded Dominion": lambda ic: sword(ic, P["gold"], P["white"], shape_="straight", w=7.5, gshape="wing", gw=15, gem_=P["ruby"], pgem=P["ruby"]),
    "Glutton's Scepter": lambda ic: mace(ic, C("#ffc8b8", "#c8746a", "#7a3a34", "#2a0e0c"), kind="drumstick"),
    "Goblin Mace": lambda ic: mace(ic, C("#e8b890", "#a8703e", "#5e3a1c", "#241206"), kind="club", studs=True),
    "Gold Sword": lambda ic: sword(ic, P["gold"], P["gold"], shape_="straight", w=6.5, pgem=P["amethyst"], gem_=P["amethyst"]),
    "Green Death": lambda ic: sword(ic, P["mint"], P["teal"], shape_="straight", w=7, gshape="round", gw=11),
    "Horn Dancer": lambda ic: sword(ic, P["slate"], P["fire"], shape_="taper", w=6, gshape="spiky", gw=12, gem_=P["ruby"]),
    "Howling Edge": lambda ic: sword(ic, P["pink"], P["magenta"], shape_="curved", w=7, gshape="cross", gw=11),
    "Hungry Blade": lambda ic: sword(ic, P["fire"], P["gold"], shape_="straight", w=8, gw=13, gshape="spiky", extra="maw", fuller=False),
    "Ice Sword": lambda ic: sword(ic, P["ice"], P["shadow"], shape_="straight", w=5, gw=10, gem_=P["emerald"]),
    "Infernal Brand": lambda ic: sword(ic, C("#fff4b0", "#ff8a5a", "#d8306a", "#3e0822"), P["shadow"], shape_="wavy", w=7.5, extra="flames"),
    "Infernal Fork": lambda ic: trident(ic, C("#ffc4f0", "#e060b0", "#7a2a70", "#2a0826"), P["violet"], ornate=True),
    "Iron Mace": lambda ic: mace(ic, P["slate"], P["orange"], kind="spiked"),
    "Iron Sword": lambda ic: sword(ic, P["steel"], P["orange"], shape_="straight", w=6, pgem=P["ruby"]),
    "Learner Staff": lambda ic: staff(ic, P["wood"], "spiral", P["sapphire"], rings=False),
    "Mindbreaker": lambda ic: sword(ic, C("#ffd6ff", "#c07ae8", "#6a3a9a", "#200c38"), P["shadow"], shape_="straight", w=7, gshape="spiky", gw=13, gem_=P["pink"]),
    "Mindshatter": lambda ic: sword(ic, C("#ffffff", "#f0b8d8", "#b0508a", "#3a0c2a"), P["magenta"], shape_="curved", w=9, gw=12),
    "Molten Axe": lambda ic: axe(ic, P["lava"], P["darkwood"], "wedge", edge="#fff8c0"),
    "Molten Sword": lambda ic: sword(ic, P["lava"], P["volcanic"], shape_="cleaver", w=9, gw=10, extra="cracks"),
    "Moonweaver": lambda ic: sword(ic, P["moon"], P["pink"], shape_="serrated", w=8, gw=12, gshape="hook"),
    "Mountainheart": lambda ic: sword(ic, C("#dce4f0", "#8a9ab4", "#4a566e", "#161c28"), P["slate"], shape_="straight", w=9.5, gw=12, extra="rock", gem_=P["pink"]),
    "Nightfang": lambda ic: sword(ic, P["silver"], P["plum"], shape_="taper", w=5.5, gw=12, gem_=P["ruby"]),
    "Nunchaku": lambda ic: nunchaku(ic, P["darkwood"]),
    "Plaguebringer": lambda ic: sword(ic, P["bone"], P["bone"], shape_="straight", w=8.5, gw=12, extra="drips", gem_=P["leaf"]),
    "Platinum Dagger": lambda ic: dagger(ic, P["platinum"], P["slate"], w=5),
    "Platinum Sword": lambda ic: sword(ic, P["platinum"], P["slate"], shape_="straight", w=5, gw=11),
    "Purpurite Sword": lambda ic: sword(ic, P["purpurite"], P["shadow"], shape_="straight", w=5, gw=10, gem_=P["amethyst"]),
    "Ray's Axe": lambda ic: axe(ic, C("#ffd0e0", "#ff5a8a", "#a8204a", "#3a0616"), P["violet"], "crescent", edge="#dfffe8"),
    "Ray's Cleaver": lambda ic: axe(ic, C("#dfffe0", "#ff6a9a", "#b0305a", "#3a0616"), P["violet"], "cleaver"),
    "Scythe": lambda ic: scythe(ic, P["steel"], P["wood"]),
    "Serpent's Kiss": lambda ic: sword(ic, C("#ffc8ec", "#e0609a", "#8a2c68", "#2a0822"), P["plum"], shape_="wavy", w=6.5, gshape="cross", gw=11, extra="glow:#ffb0e0"),
    "Shackled Magma": lambda ic: sword(ic, C("#ffe8a0", "#ff9a5a", "#4a3a4a", "#12080c"), P["volcanic"], shape_="curved", w=8, gw=11, extra="cracks"),
    "Silver Dagger": lambda ic: dagger(ic, P["silver"], P["iron"], w=5.5, shape_="taper"),
    "Silver Sword": lambda ic: sword(ic, P["silver"], P["iron"], shape_="straight", w=6, gw=12),
    "Simple Wand": lambda ic: wand(ic, P["wood"], "knob", P["amethyst"], w=3.8),
    "Slime Wrath": lambda ic: staff(ic, P["violet"], "orb", P["amethyst"], P["violet"], thin=True, rings=False),
    "Soldier Sword": lambda ic: sword(ic, P["slate"], P["gold"], shape_="straight", w=6, gshape="wing", gw=12),
    "Soulharvest Scythe": lambda ic: scythe(ic, P["slate"], P["pink"]),
    "Starcutter": lambda ic: sword(ic, C("#ffffff", "#7ae8ff", "#b060e0", "#1c1440"), P["mint"], shape_="crystal", w=9, gshape="spiky", gw=13, extra="prism", gem_=P["pink"]),
    "Stinglash": lambda ic: stinger(ic, C("#f0e0f0", "#b8a0c0", "#6a5478", "#241a2e")),
    "The All-Seeing Blade": lambda ic: sword(ic, P["pink"], P["pink"], shape_="straight", w=8.5, gshape="round", gw=14, gem_=P["crimson"], extra="spiral"),
    "The Devourer": lambda ic: staff(ic, P["teal"], "maw", rings=False),
    "The Last Laugh": lambda ic: sword(ic, C("#e0d0ff", "#8a74e0", "#40308a", "#140c34"), P["violet"], shape_="straight", w=6.5, gshape="hook", gw=12, gem_=P["cyan"]),
    "The Watcher's Gaze": lambda ic: sword(ic, C("#ffffff", "#f0a0b0", "#b02a44", "#3a0612"), P["crimson"], shape_="straight", w=7, gshape="spiky", gw=13, gem_=P["red"]),
    "Three Fates": lambda ic: fates(ic),
    "Tidecaller": lambda ic: sword(ic, P["orange"], P["leaf"], shape_="cleaver", w=9, gshape="spiky", gw=13, gem_=P["pink"]),
    "Tidewoven Blade": lambda ic: sword(ic, C("#e8e0ff", "#8a7cf0", "#3e2a9a", "#140a3c"), P["silver"], shape_="taper", w=4.5, gw=11, gem_=P["silver"]),
    "Trident": lambda ic: trident(ic, P["crimson"], P["shadow"]),
    "Vamp Blade": lambda ic: sword(ic, C("#d6d4e6", "#7a7896", "#3a3852", "#0c0c16"), P["orange"], shape_="straight", w=5.5, gw=11, extra="blood"),
    "Vamp Blade +1": lambda ic: sword(ic, C("#e0b8ee", "#8e5aa4", "#44204e", "#10041a"), P["orange"], shape_="straight", w=5.5, gw=11, gem_=P["crimson"], extra="blood"),
    "Vamp Blade +2": lambda ic: sword(ic, C("#c07ac0", "#7a2a6a", "#301030", "#0e0410"), P["fire"], shape_="straight", w=6, gw=12, gem_=P["crimson"], extra="glow:#ff7ad0"),
    "Volcanic Sword": lambda ic: sword(ic, P["volcanic"], P["volcanic"], shape_="straight", w=7, gw=11, extra="cracks", gem_=P["lava"]),
    "Warfin": lambda ic: sword(ic, C("#eafffc", "#94b8c0", "#4a6470", "#141e24"), P["slate"], shape_="fin", w=9, gw=10),
    "Wooden Sword": lambda ic: sword(ic, P["wood"], P["wood"], P["darkwood"], shape_="straight", w=6.5, gw=12, fuller=False),

    # ---------------------------------------------------------------- helmets
    "Azurite Helmet": lambda ic: knight(ic, P["azurite"], "slit", crest="fin", crest_pal=P["sapphire"]),
    "Bogsteel Helmet": lambda ic: knight(ic, P["bogsteel"], "eye", pattern="mottle"),
    "Bunny Ears": lambda ic: bunny_ears(ic),
    "Bycocket": lambda ic: hat(ic, "bycocket", P["leaf"], accent=P["red"]),
    "Dark Crown": lambda ic: crown(ic, P["shadow"], P["magenta"]),
    "Fedora": lambda ic: hat(ic, "fedora", P["wood"], band=P["darkwood"]),
    "Flameguard Helmet": lambda ic: knight(ic, P["brownplate"], "t", trim=P["crimson"], crest="wave", crest_pal=P["crimson"]),
    "Forestguard Helmet": lambda ic: knight(ic, P["plum"], "slit", pattern="vines"),
    "Frostguard Helmet": lambda ic: knight(ic, P["plum"], "t", crest="wave", crest_pal=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38"), pattern="frost"),
    "Glasses": lambda ic: glasses(ic),
    "Gold Helmet": lambda ic: knight(ic, P["gold"], "t", trim=P["violet"]),
    "Horror Mask": lambda ic: mask(ic, "horror"),
    "Iron Bucket": lambda ic: bucket(ic, P["iron"], "slit", pattern="rivets"),
    "Kitsune Mask": lambda ic: mask(ic, "kitsune"),
    "Lucky Hat": lambda ic: hat(ic, "tophat", P["leaf"], band=P["darkwood"], accent=P["gold"]),
    "Mining Helmet": lambda ic: hat(ic, "hardhat", P["yellow"]),
    "Mystery Mask": lambda ic: mask(ic, "mystery"),
    "Pirate Hat": lambda ic: hat(ic, "pirate", P["slate"], accent=P["red"]),
    "Platinum Helmet": lambda ic: knight(ic, P["platinum"], "grille", crest="plume", crest_pal=P["white"]),
    "Police Hat": lambda ic: hat(ic, "police", P["navy"]),
    "Purpurite Helmet": lambda ic: knight(ic, P["purpurite"], "grille", trim=P["plum"], crest="fin", crest_pal=P["violet"]),
    "Santa Hat": lambda ic: hat(ic, "santa", P["red"]),
    "Silver Helmet": lambda ic: knight(ic, P["silver"], "slit", crest="plume", crest_pal=P["sand"]),
    "Sleepy Wizard Hat": lambda ic: hat(ic, "wizard", P["sapphire"], band=P["navy"], accent=P["orange"]),
    "Soldier Helmet": lambda ic: knight(ic, P["steel"], "t", crest="plume", crest_pal=P["red"]),
    "Sunhat": lambda ic: hat(ic, "sunhat", C("#fff6cc", "#f0cc68", "#b8862a", "#3a2408"), band=P["red"]),
    "Volcanic Helmet": lambda ic: knight(ic, P["volcanic"], "open", pattern="cracks"),
    "Windguard Helmet": lambda ic: knight(ic, P["magenta"], "slit", pattern="streaks", crest="fin", crest_pal=P["cyan"]),
    "Witches Hat": lambda ic: hat(ic, "witch", P["slate"], band=P["shadow"]),
    "Wizard Hat": lambda ic: hat(ic, "wizard", P["sapphire"], band=P["white"], accent=P["white"]),
    "Wooden Helmet": lambda ic: bucket(ic, P["wood"], "slit", bands=P["darkwood"], pattern="planks"),

    # ---------------------------------------------------------------- chest
    "Azurite Chestplate": lambda ic: chestplate(ic, P["azurite"], trim=P["cyan"], emblem=P["cyan"]),
    "Bogsteel Chestplate": lambda ic: chestplate(ic, P["bogsteel"], pattern="mottle"),
    "Chainmail Shirt": lambda ic: shirt(ic, P["steel"], long_=False, pattern="chain"),
    "Dark Blue Cloak": lambda ic: cloak(ic, P["navy"], trim=P["slate"]),
    "Draculas Cloak": lambda ic: cloak(ic, P["shadow"], collar=P["red"], inner=P["red"]),
    "Flameguard Chestplate": lambda ic: chestplate(ic, P["brownplate"], trim=P["crimson"], pattern="flametrim"),
    "Forestguard Chestplate": lambda ic: chestplate(ic, P["plum"], pattern="vines"),
    "Frostguard Chestplate": lambda ic: chestplate(ic, P["plum"], trim=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38"), pattern="frost"),
    "Gold Chestplate": lambda ic: chestplate(ic, P["gold"], emblem=P["ruby"]),
    "Long sleeve Shirt": lambda ic: shirt(ic, C("#ffffff", "#eceff5", "#c3c9d6", "#2a2c34"), long_=True),
    "Platinum Chestplate": lambda ic: chestplate(ic, P["platinum"], trim=P["steel"], emblem=P["ice"]),
    "Purple Cloak": lambda ic: cloak(ic, P["shadow"], trim=P["purpurite"]),
    "Purpurite Chestplate": lambda ic: chestplate(ic, P["purpurite"], pattern="checker"),
    "Shirt": lambda ic: shirt(ic, P["salmon"]),
    "Silver Chestplate": lambda ic: chestplate(ic, P["silver"], trim=P["iron"]),
    "Soldier Chestplate": lambda ic: chestplate(ic, P["iron"], trim=P["red"], emblem="cross"),
    "Volcanic Chestplate": lambda ic: chestplate(ic, P["volcanic"], pattern="cracks"),
    "Windguard Chestplate": lambda ic: chestplate(ic, P["magenta"], pattern="streaks"),
    "Wooden Chestplate": lambda ic: chestplate(ic, P["wood"], pattern="planks"),

    # ---------------------------------------------------------------- legs
    "Azurite Greaves": lambda ic: greaves(ic, P["azurite"], trim=P["cyan"]),
    "Bogsteel Greaves": lambda ic: greaves(ic, P["bogsteel"], pattern="mottle"),
    "Flameguard Greaves": lambda ic: greaves(ic, P["brownplate"], trim=P["crimson"]),
    "Forestguard Greaves": lambda ic: greaves(ic, P["plum"], pattern="vines"),
    "Frostguard Greaves": lambda ic: greaves(ic, P["plum"], trim=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38")),
    "Gold Greaves": lambda ic: greaves(ic, P["gold"], trim=P["orange"]),
    "Lifebuoy": lambda ic: lifebuoy(ic),
    "Platinum Greaves": lambda ic: greaves(ic, P["platinum"], trim=P["ice"]),
    "Purpurite Greaves": lambda ic: greaves(ic, P["purpurite"], trim=P["violet"]),
    "Silver Greaves": lambda ic: greaves(ic, P["silver"]),
    "Soldier Greaves": lambda ic: greaves(ic, P["iron"], trim=P["red"]),
    "Volcanic Greaves": lambda ic: greaves(ic, P["volcanic"], pattern="cracks"),
    "Windguard Greaves": lambda ic: greaves(ic, P["magenta"], pattern="streaks"),
    "Wooden Greaves": lambda ic: greaves(ic, P["wood"], trim=P["darkwood"]),

    # ---------------------------------------------------------------- feet
    "Azurite Shoes": lambda ic: boot(ic, P["azurite"], trim=P["cyan"]),
    "Bogsteel Shoes": lambda ic: boot(ic, P["bogsteel"], pattern="mottle"),
    "Flameguard Shoes": lambda ic: boot(ic, P["brownplate"], trim=P["crimson"]),
    "Forestguard Shoes": lambda ic: boot(ic, P["plum"], pattern="vines"),
    "Frostguard Shoes": lambda ic: boot(ic, P["plum"], trim=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38")),
    "Gold Boots": lambda ic: boot(ic, P["gold"], trim=P["orange"]),
    "Magic Loafers": lambda ic: boot(ic, P["orange"], kind="loafer", gem_=P["teal"]),
    "Platinum Boots": lambda ic: boot(ic, P["platinum"], trim=P["ice"]),
    "Purpurite Shoes": lambda ic: boot(ic, P["amethyst"], trim=P["purpurite"]),
    "Sandals": lambda ic: boot(ic, P["darkwood"], kind="sandal"),
    "Shackle": lambda ic: boot(ic, P["slate"], kind="shackle"),
    "Silver Batons": lambda ic: boot(ic, P["silver"], trim=P["iron"]),
    "Soldier Boots": lambda ic: boot(ic, P["iron"], trim=P["red"]),
    "Volcanic Boots": lambda ic: boot(ic, P["volcanic"], pattern="cracks"),
    "Warm Boots": lambda ic: boot(ic, P["copper"], trim=P["cream"]),
    "Windguard Shoes": lambda ic: boot(ic, P["magenta"], pattern="streaks"),
    "Wooden Shoes": lambda ic: boot(ic, P["wood"], kind="clog"),

    # ---------------------------------------------------------------- shields
    "Ancient Shield": lambda ic: shield(ic, "tower", C("#b8c8b8", "#6e8278", "#3a4a42", "#141c18"), P["slate"], emblem="sun"),
    "Blue Shield": lambda ic: shield(ic, "heater", C("#e0e4ff", "#8e98e8", "#4a4ea8", "#161838"), P["violet"], emblem="streak"),
    "Bogsteel Shield": lambda ic: shield(ic, "oval", P["bogsteel"], P["shadow"], emblem="mottle"),
    "Chocolate Shield": lambda ic: shield(ic, "tower", P["chocolate"], P["chocolate"], emblem="chocolate"),
    "Falcon Shield": lambda ic: shield(ic, "heater", P["gold"], P["darkwood"], emblem="falcon"),
    "Flameguard Shield": lambda ic: shield(ic, "oval", P["brownplate"], P["crimson"]),
    "Forestguard Shield": lambda ic: shield(ic, "oval", P["plum"], P["teal"]),
    "Frostguard Shield": lambda ic: shield(ic, "oval", P["plum"], C("#fff0ff", "#e6a0d8", "#9a5890", "#2e1028")),
    "Goblin Shield": lambda ic: shield(ic, "oval", P["sand"], P["darkwood"], emblem="bumps"),
    "Pink Shield": lambda ic: shield(ic, "heater", P["pink"], P["purpurite"], emblem="streak"),
    "Platinum Shield": lambda ic: shield(ic, "heater", P["platinum"], P["steel"], boss=P["ice"]),
    "Reinforced Shield": lambda ic: shield(ic, "round", P["wood"], P["steel"], emblem="x", boss=P["steel"]),
    "Rhino Shield": lambda ic: shield(ic, "round", C("#e0886a", "#a8402a", "#5a1c12", "#1e0806"), P["cream"], boss=P["bone"]),
    "Soldier Shield": lambda ic: shield(ic, "heater", P["cream"], P["iron"], emblem="cross"),
    "Turtle Shell": lambda ic: shield(ic, "oval", P["leaf"], C("#3c7a2c", "#24541a", "#123010", "#06140a"), emblem="turtle"),
    "Volcanic Shield": lambda ic: shield(ic, "oval", P["volcanic"], P["volcanic"], emblem="cracks"),
    "Windguard Shield": lambda ic: shield(ic, "oval", P["magenta"], P["sapphire"], emblem="streak"),
    "Wooden Shield": lambda ic: shield(ic, "round", P["wood"], P["darkwood"], emblem="planks", boss=P["steel"]),

    # ---------------------------------------------------------------- amulets
    "Aggressive Amulet": lambda ic: amulet(ic, P["slate"]),
    "Brutal Amulet": lambda ic: amulet(ic, P["fire"], kind="framed", frame=P["copper"]),
    "Deadly Amulet": lambda ic: amulet(ic, P["white"], cord=P["slate"], kind="skull"),
    "Energetic Amulet": lambda ic: amulet(ic, P["cyan"]),
    "Lucky Amulet": lambda ic: amulet(ic, P["cream"], kind="lucky"),
    "Ocean Spirit Amulet": lambda ic: amulet(ic, P["cyan"], kind="framed", frame=P["orange"]),
    "Resilient Amulet": lambda ic: amulet(ic, P["orange"], cord=P["slate"], kind="square"),
    "Serpentine Amulet": lambda ic: amulet(ic, P["leaf"], kind="eye"),
    "Sun Demon Amulet": lambda ic: amulet(ic, P["red"], kind="framed", frame=P["orange"]),
    "Terra Empress Amulet": lambda ic: amulet(ic, P["leaf"], kind="framed", frame=P["orange"]),
    "Wind Ghost Amulet": lambda ic: amulet(ic, P["sapphire"], kind="framed", frame=P["orange"]),

    # ---------------------------------------------------------------- necklaces
    "Copper Mining Necklace": lambda ic: necklace(ic, "copper", P["sapphire"]),
    "Gold Mining Necklace": lambda ic: necklace(ic, "gold", P["sapphire"]),
    "Platinum Mining Necklace": lambda ic: necklace(ic, "platinum", P["leaf"]),
    "Liora's Necklace": lambda ic: necklace(ic, "gold", kind="liora"),
    "Shroom Seeker": lambda ic: necklace(ic, "gold", kind="beads"),

    # ---------------------------------------------------------------- tools
    "Basic Gloves": lambda ic: glove(ic, P["wood"]),
    "Elite Gloves": lambda ic: glove(ic, P["violet"], cuff=P["teal"]),
    "Red Gloves": lambda ic: glove(ic, P["crimson"]),
    "Snake Gloves": lambda ic: glove(ic, P["darkwood"], pattern="scales", cuff=P["olive"]),
    "Broom": lambda ic: broom(ic),
    "Lantern": lambda ic: lantern(ic),
    "Torch": lambda ic: torch(ic),
    "Telescope": lambda ic: telescope(ic),
    "Mana Skull": lambda ic: skull(ic, C("#d8dca0", "#8e9468", "#4e523a", "#1a1c12")),
    "Great Mana Skull": lambda ic: skull(ic, P["violet"], eyes="#ff3a4a", cracks="#e6e04a"),
}


def ring_spec(name: str):
    """Rings follow the game's naming: '[Stat] <Metal> Ring' or 'Basic Ring'."""
    words = name.replace(" Ring", "").split()
    if not words or words == ["Basic"]:
        return lambda ic: ring(ic, "iron", "plain")
    metal = words[-1].lower()
    stat = " ".join(words[:-1]).lower()
    if metal not in METAL:
        return None
    style, gem_ = "plain", None
    if stat in GEMS:
        style, gem_ = "gem", GEMS[stat]
    elif stat == "attack":
        style = "attack"
    elif stat == "crit":
        style = "crit"
    elif stat == "crit damage":
        style = "critdmg"
    elif stat == "flat":
        style = "flat"
    elif stat == "mana":
        style = "mana"
    return lambda ic: ring(ic, metal, style, gem_)


def main() -> None:
    force = "--force" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    data = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    written, missing, kept = 0, [], 0
    for it in data["items"]:
        name = it["name"]
        if only and name not in only:
            continue
        spec = SPECS.get(name) or (ring_spec(name) if it["type"] == "RING" else None)
        if not spec:
            missing.append(name)
            continue
        path = OUT / f"i{it['id']}.svg"
        if path.exists() and not force and "generated" not in path.read_text(encoding="utf-8")[:200]:
            kept += 1
            continue
        ic = Icon()
        ic.add(spec(ic))
        svg = ic.svg().replace("<svg ", "<svg data-generated=\"modern_icons.py\" ", 1)
        path.write_text(svg, encoding="utf-8")
        written += 1
    print(f"modern icons: wrote {written}, kept {kept} hand-edited, missing specs: {missing or 'none'}")


if __name__ == "__main__":
    main()
