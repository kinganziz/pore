#!/usr/bin/env python3
"""PORE's pixel-art icon set, designed natively on a 16x16 grid -> icons/pixel/<key>.svg + icons/sprite-pixel.svg

Not a filter over the modern set: every icon is built pixel by pixel from grid primitives
(staircase diagonals, scanline polygons, discs) with pixel-art conventions:
  * auto-shading per shape: 3-tone ramp lit from the top-left (bevel on every edge)
  * a 1px outline in the darkest tone of the neighbouring material
  * hand-placed detail pixels (gems, sparkles, rivets, cracks)

Designs are PORE's own; the item name / material drives each spec.

Usage: python tools/pixel_icons.py
"""
from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "pixel"
SPRITE = ROOT / "icons" / "sprite-pixel.svg"
N = 16

# (light, mid, dark, outline)
P = {
    "wood": ("#e0a060", "#a8663a", "#6e3c20", "#2a1408"),
    "darkwood": ("#9a6a44", "#6a4428", "#44281a", "#1a0c06"),
    "leather": ("#8e6a52", "#5e4232", "#3a261c", "#140a06"),
    "copper": ("#ffb987", "#d0733f", "#8a3e1e", "#2e1006"),
    "iron": ("#f2ece0", "#c4b9a6", "#857a68", "#2a241c"),
    "steel": ("#eef4ff", "#a9b8d0", "#63708a", "#1c2230"),
    "slate": ("#b8c2d2", "#76819a", "#474f64", "#161a24"),
    "silver": ("#ffffff", "#d6d4ce", "#94908a", "#28262a"),
    "gold": ("#ffe98a", "#f4b12c", "#b86610", "#3a1c04"),
    "platinum": ("#ffffff", "#c9d8ea", "#7d8eaa", "#20283a"),
    "platring": ("#d0e8dc", "#8aa89a", "#4c6258", "#141c18"),
    "azurite": ("#9ad4ff", "#3a7ee8", "#1c3c94", "#0a1438"),
    "purpurite": ("#ffc0f2", "#d066dc", "#78309a", "#260c38"),
    "bogsteel": ("#c8e4b4", "#7ca47e", "#46644c", "#14201a"),
    "volcanic": ("#6a646e", "#3c3842", "#221f26", "#08070a"),
    "lava": ("#fff08a", "#ff9a30", "#d23c18", "#4a1004"),
    "fire": ("#fff08a", "#ffa032", "#e0481a", "#4a1004"),
    "emerald": ("#b4ffd4", "#40c486", "#1c6c4c", "#08281a"),
    "mint": ("#e4fff0", "#8aeebe", "#2e9a78", "#0c3024"),
    "ruby": ("#ffb4bc", "#ec3450", "#8c1024", "#34040e"),
    "red": ("#ff9a9a", "#e2343e", "#8c1420", "#2c0406"),
    "crimson": ("#ff9aac", "#d43c5c", "#7c1834", "#2a0612"),
    "sapphire": ("#c0e6ff", "#46a4ff", "#1a58b8", "#08204e"),
    "cyan": ("#d0fcff", "#46d6f0", "#1a7c9c", "#08303c"),
    "ice": ("#ffffff", "#bce8ff", "#58a4e0", "#123a64"),
    "amethyst": ("#e6ccff", "#9a62ff", "#4c24b0", "#180846"),
    "violet": ("#d8bcff", "#8c5ae0", "#4a2a8c", "#160836"),
    "pink": ("#ffd8ee", "#f07ab6", "#a8367a", "#380c2c"),
    "magenta": ("#ff94ca", "#c8307e", "#6c1446", "#240414"),
    "plum": ("#94769e", "#5c3c64", "#321e3a", "#100814"),
    "brownplate": ("#b88068", "#704232", "#3c2018", "#140806"),
    "leaf": ("#ccf49a", "#58c046", "#26762a", "#0a2a0e"),
    "olive": ("#e6de6c", "#b0a028", "#6a6010", "#242004"),
    "bone": ("#fffaf0", "#e6d6b8", "#a8947a", "#342e38"),
    "shadow": ("#6e6e8c", "#3c3c56", "#20202e", "#08080e"),
    "navy": ("#5a86c0", "#1e487c", "#0e2446", "#040c1a"),
    "sand": ("#fff0d4", "#d6be98", "#8e7456", "#2c2216"),
    "salmon": ("#ffd4bc", "#e89478", "#9c5244", "#34160e"),
    "chocolate": ("#d49476", "#8c4a34", "#4a2418", "#1a0804"),
    "yellow": ("#fff4a0", "#ffd034", "#cc8410", "#3a2204"),
    "white": ("#ffffff", "#e4e6ee", "#9ea4b4", "#282a34"),
    "teal": ("#c4fff2", "#48c6b2", "#1c6a66", "#082624"),
    "orange": ("#ffd49a", "#ff9834", "#c04a12", "#3e1204"),
    "moon": ("#ffffff", "#ddd4f4", "#9282b8", "#221a3e"),
    "cream": ("#fffcf0", "#efe2c2", "#b8a684", "#383024"),
    "skin": ("#ffe0c8", "#f0b490", "#b87056", "#3a1a10"),
}


def C(*t):
    return tuple(t)


# ----------------------------------------------------------------------------- grid geometry
def inb(x, y):
    return 0 <= x < N and 0 <= y < N


def line(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


OFF = {1: [(0, 0)], 2: [(0, 0), (1, 0)], 3: [(0, 0), (1, 0), (0, 1)], 4: [(0, 0), (1, 0), (0, 1), (1, 1)],
       5: [(0, 0), (1, 0), (0, 1), (1, 1), (-1, 0)], 6: [(0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)]}


def thick(pts, w):
    return {(x + dx, y + dy) for x, y in pts for dx, dy in OFF[w]}


def seg(x0, y0, x1, y1, w=1):
    return thick(line(x0, y0, x1, y1), w)


def poly(pts):
    m = set()
    for y in range(N):
        for x in range(N):
            px, py = x + 0.5, y + 0.5
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                m.add((x, y))
    return m


def disc(cx, cy, r):
    return {(x, y) for y in range(N) for x in range(N) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def ellipse(cx, cy, rx, ry):
    return {(x, y) for y in range(N) for x in range(N) if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1}


def ring(cx, cy, r_out, r_in):
    return disc(cx, cy, r_out) - disc(cx, cy, r_in)


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def mirror(mask):
    return {(N - 1 - x, y) for x, y in mask}


# ----------------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self):
        self.c: dict = {}
        self.o: dict = {}

    def shape(self, mask, pal, shade="auto", outline=True):
        mask = {p for p in mask if inb(*p)}
        for x, y in mask:
            if shade == "auto":
                up, lf = (x, y - 1) in mask, (x - 1, y) in mask
                dn, rt = (x, y + 1) in mask, (x + 1, y) in mask
                light = (not up) + (not lf)
                dark = (not dn) + (not rt)
                col = pal[0] if light and not dark else pal[2] if dark and not light else pal[1]
            elif shade == "flat":
                col = pal[1]
            elif shade == "light":
                col = pal[0]
            elif shade == "dark":
                col = pal[2]
            else:
                col = shade
            self.c[(x, y)] = col
            self.o[(x, y)] = pal[3] if outline else None
        return self

    def dot(self, x, y, color, outline=None):
        if inb(x, y):
            self.c[(x, y)] = color
            self.o[(x, y)] = outline
        return self

    def dots(self, pts, color, outline=None):
        for x, y in pts:
            self.dot(x, y, color, outline)
        return self

    def erase(self, pts):
        for p in pts:
            self.c.pop(p, None)
            self.o.pop(p, None)
        return self

    def svg(self) -> str:
        grid = dict(self.c)
        for y in range(N):
            for x in range(N):
                if (x, y) in self.c:
                    continue
                for nx, ny in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)):
                    oc = self.o.get((nx, ny))
                    if oc:
                        grid[(x, y)] = oc
                        break
        runs: dict = {}
        for y in range(N):
            x = 0
            while x < N:
                col = grid.get((x, y))
                if not col:
                    x += 1
                    continue
                x1 = x
                while x1 < N and grid.get((x1, y)) == col:
                    x1 += 1
                runs.setdefault(col, []).append(f"M{x} {y}h{x1 - x}v1h-{x1 - x}z")
                x = x1
        body = "".join(f'<path fill="{c}" d="{"".join(d)}"/>' for c, d in runs.items())
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" shape-rendering="crispEdges">{body}</svg>'


HL = "#ffffff"


def gem(cv, x, y, pal, big=False):
    if big:
        cv.shape(rect(x - 1, y - 1, x, y), pal)
        cv.dot(x - 1, y - 1, HL, pal[3])
    else:
        cv.shape({(x, y)}, pal, "flat")
        cv.dot(x, y, pal[0], pal[3])
    return cv


def sparkle(cv, x, y, color="#ffffff"):
    cv.dots([(x, y - 1), (x - 1, y), (x, y), (x + 1, y), (x, y + 1)], color)


# ----------------------------------------------------------------------------- weapons (tip top-right)
def sword(blade, guard=None, grip=None, pommel=None, shape="straight", w=2, L=8, gw=2, gshape="cross",
          gem_=None, pgem=None, extra=None):
    guard = guard or P["steel"]
    grip = grip or P["leather"]
    pommel = pommel or guard
    cv = Canvas()
    tip = (14, 1)
    base = (tip[0] - L + 1, tip[1] + L - 1)
    pts = line(*tip, *base)
    m = set()
    for i, (x, y) in enumerate(pts):
        ww = 1 if i == 0 else w
        if shape == "taper":
            ww = 1 if i < 2 else min(w, 1 + i // 3)
        m |= {(x + dx, y + dy) for dx, dy in OFF[ww]}
        if shape == "serrated" and i >= 2 and i % 2 == 0:
            m.add((x + (2 if ww >= 2 else 1), y + 1))
        if shape == "dserrated" and i >= 2:
            m.add((x - 1, y - 1) if i % 2 == 0 else (x + 2, y + 1))
        if shape == "curved" and 2 <= i <= L - 2:
            m.add((x + 1, y + 1))
            if 3 <= i <= L - 3:
                m.add((x + 2, y + 1))
        if shape == "wavy" and i >= 2:
            m.add((x - 1, y) if i % 3 == 0 else (x + 1, y + 1) if i % 3 == 1 else (x, y))
        if shape == "cleaver" and i >= 1:
            m |= {(x + 1, y + 1), (x + 2, y + 1), (x + 2, y)}
        if shape == "crystal" and 2 <= i <= L - 2:
            m |= {(x + 1, y + 1)}
            if i in (3, 4):
                m |= {(x - 1, y), (x + 2, y + 1)}
    cv.shape(m, blade)
    if w >= 3 or shape in ("cleaver", "crystal"):
        cv.dots([(x + 1, y) for x, y in pts[2:-1]], blade[0])
    if extra:
        sword_extra(cv, extra, pts)
    gx, gy = base[0] - 1, base[1] + 1
    if gshape == "cross":
        cv.shape(seg(gx - gw, gy - gw, gx + gw, gy + gw, 2), guard)
    elif gshape == "wing":
        cv.shape(seg(gx - gw, gy - gw, gx + gw, gy + gw, 2) | {(gx - gw, gy - gw - 1), (gx + gw + 1, gy + gw - 1)}, guard)
    elif gshape == "round":
        cv.shape(disc(gx + 1, gy + 0.5, 2.2), guard)
    elif gshape == "spiky":
        cv.shape(seg(gx - gw, gy - gw, gx + gw, gy + gw, 2) | {(gx - gw - 1, gy - gw - 1), (gx + gw + 2, gy + gw + 1), (gx - gw, gy - gw + 1)}, guard)
    elif gshape == "hook":
        cv.shape(seg(gx - gw, gy - gw, gx + gw, gy + gw, 2) | {(gx - gw, gy - gw - 1), (gx - gw + 1, gy - gw - 2), (gx + gw + 2, gy + gw), (gx + gw + 3, gy + gw - 1)}, guard)
    cv.shape(seg(gx - 1, gy + 1, gx - 3, gy + 3, 1), grip)
    cv.shape(rect(gx - 5, gy + 3, gx - 4, gy + 4), pommel)
    if pgem:
        cv.dot(gx - 5, gy + 3, pgem[1], pommel[3])
    if gem_:
        cv.dot(gx, gy, gem_[0], gem_[3]).dot(gx + 1, gy, gem_[1], gem_[3])
    return cv


def sword_extra(cv, kind, pts):
    if kind == "flames":
        for x, y in ((pts[3][0] - 1, pts[3][1] - 1), (pts[5][0] + 3, pts[5][1] + 1), (pts[1][0] - 1, pts[1][1] + 2)):
            cv.dot(x, y, "#ffd034").dot(x, y - 1, "#ff7a1a")
    elif kind == "cracks":
        for x, y in pts[2:-1:2]:
            cv.dot(x + 1, y, "#ff8a2a", None)
    elif kind == "drips":
        cv.dots([(pts[2][0] - 1, pts[2][1] + 2), (pts[4][0] - 1, pts[4][1] + 3), (pts[4][0] - 1, pts[4][1] + 4)], "#8ee04a")
    elif kind == "blood":
        cv.dots([(pts[2][0], pts[2][1]), (pts[3][0] + 1, pts[3][1])], "#d9253a")
    elif kind.startswith("glow"):
        color = kind.split(":")[1] if ":" in kind else "#bff4ff"
        sparkle(cv, 3, 3, color)
    elif kind == "vines":
        cv.dots([(x, y) for x, y in pts[3:-1:2]], "#58c046")
    elif kind == "prism":
        cv.dot(pts[2][0], pts[2][1], "#ff8adc").dot(pts[4][0] + 1, pts[4][1], "#9dff8a").dot(pts[6][0], pts[6][1], "#8ad8ff")
    elif kind == "rock":
        cv.dots([(pts[3][0] + 1, pts[3][1] + 1), (pts[5][0], pts[5][1])], "#3a4252")


def dagger(blade, *a, **kw):
    kw.setdefault("L", 6)
    kw.setdefault("gw", 1)
    return sword(blade, *a, **kw)


def spans(rows):
    """rows: {y: (x0, x1)} -> mask"""
    return {(x, y) for y, (x0, x1) in rows.items() for x in range(x0, x1 + 1)}


AXE_HEADS = {
    "crescent": {1: (11, 13), 2: (10, 14), 3: (10, 15), 4: (11, 15), 5: (12, 15), 6: (12, 15), 7: (11, 15), 8: (10, 14), 9: (10, 13)},
    "wedge": {2: (11, 13), 3: (11, 14), 4: (11, 15), 5: (11, 15), 6: (11, 15), 7: (11, 14), 8: (11, 13)},
    "cleaver": {1: (10, 15), 2: (10, 15), 3: (10, 15), 4: (10, 15), 5: (10, 15), 6: (10, 15), 7: (11, 15)},
    "bearded": {1: (11, 14), 2: (10, 15), 3: (10, 15), 4: (11, 15), 5: (12, 15), 6: (12, 14), 7: (12, 13), 8: (11, 13), 9: (11, 12)},
}


def axe(head, handle=None, kind="crescent", double=False, edge=None):
    handle = handle or P["wood"]
    cv = Canvas()
    cv.shape(seg(2, 14, 10, 6, 2), handle)
    rows = AXE_HEADS[kind]
    cv.shape(spans(rows), head)
    if double:
        cv.shape(mirror(spans(rows)) - {(x, y) for x, y in mirror(spans(rows)) if x > 6}, head)
    cv.dots([(x1, y) for y, (x0, x1) in rows.items() if 2 <= y <= 8], edge or head[0], head[3])
    cv.shape(rect(9, 4, 10, 7), P["shadow"])
    cv.dots([(9, 5), (10, 5)], P["steel"][0], P["shadow"][3])
    return cv


def staff(shaft, top="orb", gem_=None, accent=None, thin=False):
    gem_ = gem_ or P["sapphire"]
    accent = accent or P["gold"]
    cv = Canvas()
    cv.shape(seg(2, 14, 10, 6, 1 if thin else 2), shaft)
    if top == "orb":
        cv.shape({(10, 4), (9, 5), (12, 6), (13, 7)} | seg(9, 3, 9, 5) | seg(13, 7, 11, 7), accent)
        cv.shape(disc(12.5, 3.5, 2.7), gem_)
        cv.dot(11, 2, HL, gem_[3])
    elif top == "eye":
        cv.shape(disc(12.5, 3.5, 2.9), P["white"])
        cv.shape(rect(12, 3, 13, 4), gem_, "flat")
        cv.dot(13, 4, "#12060a", gem_[3])
    elif top == "crook":
        cv.shape(seg(10, 6, 12, 4, 2) | seg(12, 4, 12, 1, 1) | {(11, 0), (10, 0), (9, 1), (9, 2)}, shaft)
        cv.dot(10, 2, gem_[1])
    elif top == "crystal":
        cv.shape(rect(9, 5, 10, 6), accent)
        cv.shape(poly([(13, -0.5), (15.5, 3), (12.5, 7), (9.5, 4)]), gem_)
        cv.dot(12, 2, HL, gem_[3])
    elif top == "claw":
        cv.shape({(9, 4), (9, 3), (10, 2), (13, 7), (14, 6), (15, 5), (12, 1), (11, 1)}, accent)
        cv.shape(disc(12.5, 4.5, 2), gem_)
        cv.dot(12, 4, HL, gem_[3])
    elif top == "coral":
        cv.shape(seg(10, 6, 13, 3, 1) | seg(11, 5, 10, 2, 1) | seg(12, 4, 15, 4, 1) | {(13, 2), (14, 1)}, gem_)
        cv.dots([(10, 1), (15, 3), (14, 0), (9, 2)], "#ff9ad8", gem_[3])
    elif top == "maw":
        cv.shape(disc(12.5, 3.5, 3.2), P["violet"])
        cv.dots([(11, 2), (12, 2), (13, 2)], "#9dff4a").dots([(11, 5), (12, 5), (13, 5)], "#34d8e0")
        cv.dots([(12, 3), (13, 3), (12, 4), (13, 4)], "#12060a", None)
    return cv


def wand(shaft, tip="star", tip_pal=None):
    tip_pal = tip_pal or P["gold"]
    cv = Canvas()
    cv.shape(seg(2, 14, 11, 5), shaft)
    if tip == "star":
        cv.shape({(12, 2), (12, 3), (12, 4), (11, 3), (13, 3), (14, 2), (10, 4)}, tip_pal, "flat")
        cv.dot(12, 3, HL, tip_pal[3])
    elif tip == "leaf":
        cv.shape({(12, 4), (13, 3), (13, 4), (14, 3), (14, 2), (15, 2)} | {(9, 6), (8, 5), (7, 5), (8, 6)}, tip_pal)
    else:
        cv.shape({(12, 4), (11, 4), (12, 3)}, tip_pal)
    return cv


def mace(head, shaft=None, kind="spiked", studs=False):
    shaft = shaft or P["wood"]
    cv = Canvas()
    if kind == "spiked":
        cv.shape(seg(2, 14, 9, 7, 2), shaft)
        cv.shape(disc(11.5, 4.5, 3.2), head)
        cv.shape({(11, 0), (15, 4), (8, 3), (13, 8), (14, 1), (8, 7)} & set(), head)
        cv.shape({(11, 0), (15, 4), (7, 4), (12, 8), (14, 1), (8, 1)}, head, "flat")
        cv.dot(10, 3, HL, head[3])
    elif kind == "club":
        cv.shape(seg(2, 14, 7, 9, 2) | seg(7, 9, 12, 4, 4) | disc(12, 4, 2.8), head)
        if studs:
            cv.dots([(10, 5), (12, 3), (13, 5)], P["steel"][0], P["steel"][3])
    elif kind == "drumstick":
        cv.shape(seg(3, 13, 7, 9, 1) | {(2, 13), (3, 14), (2, 14)}, P["bone"])
        cv.shape(ellipse(11, 5, 4.2, 3.6), head)
        cv.dot(9, 3, head[0], head[3]).dot(12, 7, head[2], head[3])
    return cv


def scythe(blade, shaft):
    cv = Canvas()
    cv.shape(seg(13, 14, 5, 2, 1), shaft)
    cv.shape(poly([(5, 1), (9, 1.5), (5, 3), (2, 5), (0.5, 9), (0.5, 5), (2, 2)]), blade)
    cv.dots([(1, 5), (2, 3), (3, 2)], blade[0])
    return cv


def trident(head, shaft=None, ornate=False):
    shaft = shaft or P["shadow"]
    cv = Canvas()
    cv.shape(seg(2, 14, 9, 7, 1), shaft)
    cv.shape(seg(8, 5, 11, 8, 2), head)
    cv.shape(seg(8, 5, 11, 2, 1) | seg(10, 7, 14, 3, 1) | seg(11, 8, 14, 5, 1) | {(12, 1), (15, 2), (15, 4)}, head)
    if ornate:
        cv.dot(9, 7, P["ruby"][1], P["ruby"][3])
    return cv


def chakram(pal):
    cv = Canvas()
    m = ring(8, 8, 6.2, 3.2)
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        m.add((int(8 + 7 * math.cos(a)), int(8 + 7 * math.sin(a))))
    cv.shape(m, pal)
    cv.dots([(7, 7), (8, 7), (7, 8), (8, 8)], "#2a0c04")
    return cv


def nunchaku(pal):
    cv = Canvas()
    cv.shape(seg(2, 8, 5, 14, 2), pal).shape(seg(13, 8, 10, 14, 2), pal)
    cv.dots([(3, 6), (4, 4), (6, 3), (8, 3), (10, 3), (12, 4), (13, 6)], "#9aa0b4", "#1c1c28")
    return cv


def fates():
    cv = Canvas()
    cv.shape(seg(14, 14, 10, 10, 2), P["darkwood"])
    for x, y in ((4, 3), (10, 2), (3, 9)):
        cv.dots(line(10, 10, x, y)[1:-2], "#6a5a4a")
    for x, y in ((4, 3), (10, 2), (3, 9)):
        cv.shape(disc(x + 0.5, y + 0.5, 2.2), P["orange"])
        cv.dot(x, y, "#fff2c4", P["orange"][3])
    return cv


def stinger(pal):
    cv = Canvas()
    cv.shape(seg(14, 14, 12, 12, 2), P["amethyst"])
    pts = [(11, 11), (9, 11), (7, 10), (5, 9), (4, 7), (3, 5), (4, 3)]
    for i, (x, y) in enumerate(pts):
        cv.shape(rect(x - 1, y - 1, x, y), pal if i % 2 == 0 else P["plum"])
    cv.shape({(5, 1), (6, 1), (6, 2), (7, 2), (6, 0)}, P["amethyst"])
    return cv


# ----------------------------------------------------------------------------- helmets & hats (front view)
DOME = disc(8, 7.5, 5.8) | rect(2, 7, 13, 13)


def knight(pal, visor="slit", trim=None, crest=None, pattern=None, crest_pal=None):
    cv = Canvas()
    crest_pal = crest_pal or trim or P["red"]
    if crest == "plume":
        cv.shape({(8, 1), (9, 0), (10, 0), (11, 0), (12, 1), (13, 2), (13, 3), (10, 1), (11, 1)}, crest_pal)
    elif crest == "fin":
        cv.shape(rect(7, 0, 8, 2), crest_pal)
    elif crest == "horns":
        cv.shape({(1, 4), (1, 3), (0, 2), (0, 1)} | {(14, 4), (14, 3), (15, 2), (15, 1)}, crest_pal)
    elif crest == "wave":
        cv.shape({(6, 1), (7, 0), (8, 0), (9, 0), (10, 1), (11, 1), (12, 2), (13, 3), (13, 4)}, crest_pal)
    cv.shape(DOME, pal)
    if pattern:
        pattern_px(cv, pattern, 3, 3, 12, 12)
    if trim:
        cv.dots(line(7, 3, 7, 6) + line(8, 3, 8, 6), trim[1], trim[3])
        cv.dots(line(3, 12, 12, 12), trim[1], trim[3])
    ol = pal[3]
    if visor == "slit":
        cv.dots(line(4, 8, 11, 8), ol).dots([(5, 10), (7, 10), (9, 10)], ol)
    elif visor == "t":
        cv.dots(line(4, 7, 11, 7) + line(7, 8, 7, 11) + line(8, 8, 8, 11), ol)
    elif visor == "grille":
        for x in (5, 7, 9, 11):
            cv.dots(line(x, 7, x, 11), ol)
    elif visor == "eye":
        cv.dots(rect(5, 7, 10, 10), ol)
    elif visor == "open":
        cv.dots(rect(4, 7, 11, 12), ol).dots([(6, 9), (9, 9)], "#ffd23a")
    cv.dots([(5, 3), (4, 4)], HL, pal[3])
    return cv


def pattern_px(cv, kind, x0, y0, x1, y1):
    w, h = x1 - x0, y1 - y0
    if kind == "cracks":
        cv.dots([(x0 + 1, y0 + 4), (x0 + 2, y0 + 5), (x0 + 2, y0 + 6), (x1 - 2, y0 + 3), (x1 - 3, y0 + 4), (x1 - 2, y1 - 2)], "#ff7a2a")
    elif kind == "vines":
        cv.dots([(x0, y1 - 1), (x0 + 1, y1 - 2), (x0 + 1, y1 - 3), (x0 + 2, y1 - 4), (x1, y0 + 4), (x1 - 1, y0 + 5), (x1 - 1, y0 + 6)], "#5ce06a")
    elif kind == "frost":
        cv.dots([(x0 + 1, y0 + 3), (x0 + 2, y0 + 4), (x1 - 1, y0 + 3), (x1 - 2, y0 + 4), (x0 + 2, y1 - 1), (x1 - 2, y1 - 1)], "#f0c8ff")
    elif kind == "streaks":
        cv.dots([(x0 + 1, y0 + 5), (x0 + 2, y0 + 4), (x0 + 3, y0 + 5), (x1 - 1, y1 - 3), (x1 - 2, y1 - 2), (x1 - 3, y1 - 3)], "#3ed0ea")
    elif kind == "mottle":
        cv.dots([(x0 + 2, y0 + 3), (x0 + 5, y0 + 2), (x0 + 4, y0 + 6), (x1 - 2, y0 + 5), (x0 + 2, y1 - 2), (x1 - 3, y1 - 2)], "#cfeabe")
    elif kind == "checker":
        cv.dots([(x, y) for y in range(y0 + 1, y1) for x in range(x0 + 1, x1) if (x + y) % 3 == 0], "#ffffff40")
    elif kind == "planks":
        mid = (x0 + x1) // 2
        cv.dots(line(mid - 2, y0 + 1, mid - 2, y1 - 1) + line(mid + 2, y0 + 1, mid + 2, y1 - 1), "#3a1e10")
    elif kind == "rivets":
        cv.dots([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], "#2a2622")


def bucket(pal, visor="slit", bands=None, pattern=None):
    cv = Canvas()
    cv.shape(rect(3, 2, 12, 13) - {(3, 2), (12, 2)}, pal)
    if pattern:
        pattern_px(cv, pattern, 3, 2, 12, 13)
    if bands:
        cv.dots(line(3, 4, 12, 4) + line(3, 12, 12, 12), bands[1], bands[3])
    if visor == "slit":
        cv.dots(line(4, 7, 11, 7), pal[3])
    elif visor == "bars":
        for x in (5, 7, 9, 11):
            cv.dots(line(x, 6, x, 10), pal[3])
    cv.dots(line(4, 3, 4, 9), pal[0], pal[3])
    return cv


def crown(pal, gem_):
    cv = Canvas()
    cv.shape(poly([(1.5, 13), (1.5, 4), (4.5, 8), (6, 3), (8, 7), (10, 3), (11.5, 8), (14.5, 4), (14.5, 13)]), pal)
    cv.shape(rect(1, 11, 14, 13), pal)
    for x, y in ((1, 4), (6, 3), (10, 3), (14, 4)):
        cv.dot(x, y, gem_[1], gem_[3])
    cv.shape({(7, 9), (8, 9), (7, 10), (8, 10)}, gem_)
    cv.dot(7, 9, HL, gem_[3]).dot(4, 12, gem_[1]).dot(11, 12, gem_[1])
    return cv


def hat(kind, pal, band=None, accent=None):
    cv = Canvas()
    band = band or P["shadow"]
    accent = accent or P["red"]
    if kind == "fedora":
        cv.shape(ellipse(8, 11.5, 7.8, 2.4), pal)
        cv.shape(poly([(3.5, 11), (4, 5), (6, 3.5), (10, 3.5), (12, 5), (12.5, 11)]), pal)
        cv.dots(line(4, 9, 12, 9), band[1], band[3]).dots([(7, 4), (8, 5), (9, 4)], pal[2])
    elif kind == "sunhat":
        cv.shape(ellipse(8, 11, 8, 3), pal)
        cv.shape(ellipse(8, 7.5, 4, 4), pal)
        cv.dots(line(4, 9, 11, 9), band[1], band[3])
    elif kind == "wizard":
        cv.shape(ellipse(8, 13, 7.5, 2.4), band)
        cv.shape(poly([(3, 13), (6, 6), (9, 2), (13.5, 0.5), (11, 4), (11, 9), (13, 13)]), pal)
        cv.dots([(7, 9), (9, 6), (10, 11)], accent[0], accent[3])
    elif kind == "witch":
        cv.shape(ellipse(8, 13, 8, 2.4), pal)
        cv.shape(poly([(3.5, 13), (6, 7), (8, 1), (9.5, 0.5), (10, 6), (12.5, 13)]), pal)
        cv.dots(line(4, 11, 12, 11), band[1]).dot(9, 8, "#ff3a4a", pal[3])
    elif kind == "santa":
        cv.shape(poly([(3, 12), (4, 6), (8, 2.5), (12, 3), (14, 6), (12, 7), (11, 5), (12.5, 12)]), pal)
        cv.shape(rect(2, 11, 13, 13), P["white"])
        cv.shape(disc(13.5, 7.5, 1.8), P["white"])
    elif kind == "pirate":
        cv.shape(poly([(0.5, 10), (4, 11), (8, 8), (12, 11), (15.5, 10), (13, 13), (3, 13)]), pal)
        cv.shape(poly([(3.5, 10), (4, 5), (8, 3.5), (12, 5), (12.5, 10), (8, 8.5)]), pal)
        cv.shape({(11, 3), (12, 2), (13, 1), (14, 1), (13, 2)}, accent)
        cv.dots([(7, 6), (8, 7), (9, 6), (7, 8), (9, 8)], "#f2ece0", None)
    elif kind == "police":
        cv.shape(ellipse(8, 6.5, 6.5, 3.5), pal)
        cv.shape(rect(3, 8, 12, 10), P["shadow"])
        cv.shape(poly([(3, 10.5), (13, 10.5), (12, 13), (4, 13)]), P["shadow"])
        cv.dots(line(3, 9, 12, 9), "#f4c24a").shape(rect(7, 4, 8, 5), P["gold"])
    elif kind == "tophat":
        cv.shape(ellipse(8, 12.5, 7.5, 2), pal)
        cv.shape(rect(4, 2, 11, 12), pal)
        cv.dots(line(4, 9, 11, 9) + line(4, 10, 11, 10), band[1], band[3])
        cv.dots([(7, 9), (8, 9), (7, 10), (8, 10)], accent[1], accent[3])
    elif kind == "bycocket":
        cv.shape(poly([(0.5, 11), (4, 6), (9, 3), (14, 3.5), (15, 7), (11, 7.5), (7, 11), (2, 12)]), pal)
        cv.shape({(11, 6), (12, 5), (13, 4), (14, 3), (15, 2), (15, 1)}, accent)
    elif kind == "hardhat":
        cv.shape(ellipse(8, 9, 5.8, 5.8) & rect(0, 0, 15, 10), pal)
        cv.shape(rect(1, 10, 14, 11), pal)
        cv.shape(rect(6, 5, 9, 8), P["shadow"])
        cv.dots([(7, 6), (8, 6), (7, 7), (8, 7)], "#fff6c4")
    return cv


def bunny_ears():
    cv = Canvas()
    cv.shape(ellipse(8, 13, 6.5, 2) - ellipse(8, 14, 5, 1.6), P["shadow"])
    for x in (4, 10):
        cv.shape(ellipse(x + 1, 6, 1.8, 5.5), P["white"])
        cv.dots(line(x + 1, 3, x + 1, 9), "#ffb3c8")
    return cv


def glasses():
    cv = Canvas()
    cv.dots(line(6, 6, 9, 6), "#20202a", None)
    for x0 in (1, 9):
        cv.shape(rect(x0, 6, x0 + 5, 9) - {(x0, 9), (x0 + 5, 9)}, P["shadow"])
        cv.dot(x0 + 1, 7, HL, P["shadow"][3])
    cv.dots([(0, 6), (15, 6)], "#20202a")
    return cv


def mask(kind):
    cv = Canvas()
    if kind == "horror":
        cv.shape(ellipse(8, 8, 5.8, 7), P["cream"])
        cv.dots(rect(5, 6, 6, 7) | rect(9, 6, 10, 7), "#1a1612")
        cv.dots([(5, 3), (8, 2), (10, 3), (4, 10), (7, 11), (9, 11), (11, 10), (8, 13)], "#8a7a64")
    elif kind == "kitsune":
        cv.shape(poly([(2.5, 1), (5, 4.5), (11, 4.5), (13.5, 1), (14, 9), (8, 15), (2, 9)]), P["white"])
        cv.dots([(3, 3), (12, 3), (4, 8), (11, 8), (8, 5)], "#e8384a").dots([(5, 7), (6, 7), (9, 7), (10, 7)], "#1a1a22")
    elif kind == "mystery":
        cv.shape(poly([(2.5, 1), (5, 4), (11, 4), (13.5, 1), (14, 9), (8, 15), (2, 9)]), P["red"])
        cv.dots([(4, 7), (5, 7), (10, 7), (11, 7)], "#ffd23a").dots(rect(6, 10, 9, 11), "#2a0a0a").dots([(6, 10), (9, 10)], "#ffffff")
    return cv


# ----------------------------------------------------------------------------- body armour
TORSO = (rect(1, 3, 14, 6) | rect(3, 6, 12, 14)) - {(1, 3), (14, 3)} - rect(6, 3, 9, 3)


def chestplate(pal, trim=None, pattern=None, emblem=None):
    cv = Canvas()
    cv.shape(TORSO, pal)
    if pattern:
        pattern_px(cv, pattern, 3, 5, 12, 14)
    cv.dots([(6, 4), (7, 5), (8, 5), (9, 4)], pal[3]).dots(line(7, 7, 7, 13), pal[2])
    cv.dots(line(4, 11, 11, 11), pal[2])
    if trim:
        cv.dots(line(1, 4, 5, 4) + line(10, 4, 14, 4) + line(3, 14, 12, 14), trim[1], trim[3])
    if emblem == "cross":
        cv.dots(line(7, 7, 7, 10) + line(8, 7, 8, 10) + line(6, 8, 9, 8), "#d2323e", None)
    elif emblem:
        cv.dot(7, 8, emblem[0], emblem[3]).dot(8, 8, emblem[1], emblem[3])
    return cv


def cloak(pal, trim=None, collar=None, inner=None):
    cv = Canvas()
    if collar:
        cv.shape({(1, 4), (2, 4), (2, 5), (3, 5), (14, 4), (13, 4), (13, 5), (12, 5)}, collar)
    cv.shape(poly([(8, 0.5), (12, 2.5), (12.5, 6), (14.5, 15), (1.5, 15), (3.5, 6), (4, 2.5)]), pal)
    cv.dots(rect(6, 3, 9, 6) - {(6, 3), (9, 3)}, (inner or P["shadow"])[2], pal[3])
    cv.dots(line(8, 8, 8, 14), pal[2])
    if trim:
        cv.dots([(5, 2), (4, 4), (3, 7), (3, 10), (2, 13)] + [(10, 2), (11, 4), (12, 7), (12, 10), (13, 13)], trim[1], None)
    return cv


def shirt(pal, long_=False, pattern=None):
    cv = Canvas()
    body = rect(4, 3, 11, 14) | rect(1, 3, 14, 6) - {(1, 3), (14, 3)}
    if long_:
        body |= rect(1, 6, 2, 12) | rect(13, 6, 14, 12)
    cv.shape(body - rect(6, 3, 9, 3), pal)
    if pattern == "chain":
        cv.dots([(x, y) for y in range(5, 14) for x in range(4, 12) if (x + y) % 2 == 0], pal[2])
    cv.dots([(6, 4), (7, 4), (8, 4), (9, 4)], pal[2])
    return cv


def greaves(pal, trim=None, pattern=None):
    cv = Canvas()
    leg = rect(3, 1, 7, 11) | rect(2, 12, 7, 14)
    cv.shape(leg, pal).shape(mirror(leg), pal)
    if pattern:
        pattern_px(cv, pattern, 3, 1, 12, 14)
    for x0 in (3, 8):
        cv.dots([(x0 + 1, 6), (x0 + 2, 5), (x0 + 3, 6)], pal[0], pal[3]).dots([(x0 + 2, 7)], pal[2])
    if trim:
        cv.dots(line(3, 2, 7, 2) + line(8, 2, 12, 2) + line(2, 13, 7, 13) + line(8, 13, 13, 13), trim[1], trim[3])
    return cv


def lifebuoy():
    cv = Canvas()
    cv.shape(ring(8, 8, 7, 3.4), P["red"])
    for pts in ([(7, 1), (8, 1), (7, 2), (8, 2)], [(7, 13), (8, 13), (7, 14), (8, 14)], [(1, 7), (1, 8), (2, 7), (2, 8)], [(13, 7), (14, 7), (13, 8), (14, 8)]):
        cv.dots(pts, "#f4f4f8", "#3a0a14")
    return cv


def boot(pal, trim=None, pattern=None, kind="boot", gem_=None):
    cv = Canvas()
    if kind == "boot":
        cv.shape(rect(6, 1, 12, 10) | rect(2, 10, 12, 13) | {(1, 12), (1, 11)}, pal)
        if pattern:
            pattern_px(cv, pattern, 3, 2, 12, 13)
        cv.dots(line(6, 1, 12, 1) + line(6, 2, 12, 2), (trim or pal)[1], (trim or pal)[3])
        cv.dots(line(1, 13, 12, 13), pal[3], pal[3])
        if trim:
            cv.dots([(5, 10), (4, 10), (3, 11)], trim[1], None)
    elif kind == "loafer":
        cv.shape(poly([(0.5, 12), (2, 9), (6, 8.5), (9, 6.5), (13, 6.5), (15.5, 9), (15.5, 13.5), (0.5, 13.5)]), pal)
        cv.dots([(9, 8), (10, 8), (11, 8), (12, 8)], pal[3])
        if gem_:
            cv.dot(5, 10, gem_[1], gem_[3])
    elif kind == "sandal":
        cv.shape(poly([(8, 0.5), (11, 1.5), (12.5, 6), (11.5, 11), (10.5, 15), (5.5, 15), (4.5, 11), (3.5, 6), (5, 1.5)]), P["sand"])
        cv.shape(seg(8, 3, 5, 7, 1) | seg(8, 3, 11, 7, 1) | seg(5, 11, 10, 11, 1), pal)
        cv.dot(8, 3, pal[0], pal[3])
    elif kind == "clog":
        cv.shape(poly([(0.5, 12), (1.5, 8.5), (6, 8), (13, 6), (15.5, 8), (15.5, 13.5), (0.5, 13.5)]), pal)
        cv.dots([(9, 8), (10, 8), (11, 7), (12, 7)], pal[3]).dots(line(5, 11, 5, 12) + line(10, 11, 10, 12), "#3a1e10")
    elif kind == "shackle":
        cv.shape(ring(8, 7, 6.5, 4.2), P["slate"])
        cv.shape(rect(6, 11, 9, 15), P["slate"])
        cv.dots([(7, 13), (8, 13)], "#141216")
    return cv


def shield(kind, pal, rim=None, emblem=None, boss=None):
    rim = rim or pal
    cv = Canvas()
    if kind == "heater":
        outer = rect(2, 1, 13, 8) | poly([(1.5, 8), (14.5, 8), (13, 12), (8, 15.5), (3, 12)])
        cv.shape(outer, rim)
        cv.shape(rect(4, 3, 11, 8) | poly([(3.5, 8), (12.5, 8), (11, 11), (8, 13.5), (5, 11)]), pal)
    elif kind == "oval":
        cv.shape(ellipse(8, 8, 6.2, 7.6), rim)
        cv.shape(ellipse(8, 8, 4.4, 5.8), pal)
    elif kind == "round":
        cv.shape(disc(8, 8, 7.4), rim)
        cv.shape(disc(8, 8, 5.6), pal)
    elif kind == "tower":
        cv.shape(rect(2, 0, 13, 15) - {(2, 0), (13, 0), (2, 15), (13, 15)}, rim)
        cv.shape(rect(4, 2, 11, 13), pal)
    if emblem == "cross":
        cv.dots(line(7, 3, 7, 12) + line(8, 3, 8, 12) + line(4, 6, 11, 6) + line(4, 7, 11, 7), "#d2323e", None)
    elif emblem == "sun":
        cv.shape(disc(8, 7.5, 2.2), P["gold"]).dots([(8, 3), (8, 12), (4, 7), (12, 7), (5, 4), (11, 4), (5, 11), (11, 11)], "#ffc43a")
    elif emblem == "falcon":
        cv.dots([(4, 5), (5, 6), (6, 6), (7, 7), (8, 7), (9, 6), (10, 6), (11, 5), (7, 8), (8, 8), (7, 9), (8, 9), (6, 10), (9, 10)], "#3a2410")
    elif emblem == "chocolate":
        for x in (4, 8):
            for y in (2, 6, 10):
                cv.shape(rect(x, y, x + 3, y + 3), P["chocolate"])
    elif emblem == "turtle":
        cv.dots([(7, 4), (8, 4), (5, 6), (10, 6), (5, 9), (10, 9), (7, 11), (8, 11), (6, 7), (9, 7)], "#1c4a10")
    elif emblem == "x":
        cv.shape(seg(4, 4, 11, 11, 2) | seg(11, 4, 4, 11, 2), P["steel"])
    elif emblem == "cracks":
        pattern_px(cv, "cracks", 3, 2, 12, 13)
    elif emblem == "planks":
        cv.dots(line(6, 3, 6, 13) + line(10, 3, 10, 13), pal[3])
    elif emblem == "mottle":
        pattern_px(cv, "mottle", 3, 2, 12, 13)
    elif emblem == "bumps":
        cv.dots([(6, 5), (10, 5), (5, 8), (8, 8), (11, 8), (7, 11), (9, 11)], pal[2]).dots([(6, 4), (10, 4), (8, 7)], pal[0])
    elif emblem == "streak":
        cv.dots([(5, 4), (6, 5), (7, 7), (8, 8), (9, 10)], "#ffffff")
    if boss:
        cv.shape(rect(7, 7, 8, 8), boss)
        cv.dot(7, 7, HL, boss[3])
    return cv


# ----------------------------------------------------------------------------- jewellery
METAL = {"emerald": P["emerald"], "gold": P["gold"], "iron": P["iron"], "platinum": P["platring"]}
GEMS = {"air": P["white"], "earth": P["leaf"], "fire": P["ruby"], "water": P["amethyst"]}


def ring_icon(metal, style="plain", gem_=None):
    m = METAL[metal]
    cv = Canvas()
    if style == "attack":
        cv.shape(poly([(8, 1.5), (13.5, 8), (13.5, 11), (10.5, 14.5), (5.5, 14.5), (2.5, 11), (2.5, 8)]) - poly([(8, 5.5), (10.5, 9), (10.5, 11), (9, 12.5), (7, 12.5), (5.5, 11), (5.5, 9)]), m)
        return cv
    band = {"flat": ring(8, 10, 5.8, 2.4), "mana": ring(8, 10, 5.8, 2.6)}.get(style, ring(8, 10, 5.4, 3))
    cv.shape(band, m)
    if style in ("crit", "critdmg"):
        cv.shape(rect(4, 2, 11, 5), m)
        cv.dots([(x, y) for y in (3, 4) for x in range(5, 11) if (x + y) % 2 == 0], m[2])
        if style == "critdmg":
            cv.shape({(5, 0), (6, 1), (7, 1), (8, 1), (9, 1), (10, 0), (5, 1), (10, 1)}, P["ruby"])
    elif style == "mana":
        cv.shape(rect(4, 3, 11, 5), m)
        cv.dot(7, 4, P["sapphire"][1], P["sapphire"][3]).dot(8, 4, P["sapphire"][0], P["sapphire"][3])
    elif style == "flat":
        cv.dots(line(5, 5, 10, 5), m[0], m[3])
    if style == "gem" and gem_:
        cv.shape({(6, 4), (7, 5), (8, 5), (9, 4)}, m)
        cv.shape({(7, 1), (8, 1), (6, 2), (7, 2), (8, 2), (9, 2), (7, 3), (8, 3)}, gem_)
        cv.dot(7, 1, HL, gem_[3])
    return cv


def amulet(pendant, cord=None, kind="stone", frame=None):
    cord = cord or P["wood"]
    cv = Canvas()
    cv.shape(ring(8, 6.5, 6, 5) & rect(0, 0, 15, 8), cord)
    cv.dots([(3, 8), (4, 9), (12, 8), (11, 9)], cord[1], cord[3])
    if kind == "stone":
        cv.shape(disc(8, 11.5, 3.2), pendant)
        cv.dot(7, 10, HL, pendant[3])
    elif kind == "framed":
        cv.shape(disc(8, 11.5, 3.8), frame or P["orange"])
        cv.shape(disc(8, 11.5, 2.2), pendant)
        cv.dot(7, 10, HL, pendant[3])
    elif kind == "square":
        cv.shape(rect(5, 9, 10, 14), P["wood"])
        cv.shape(rect(7, 11, 8, 12), pendant)
    elif kind == "eye":
        cv.shape(disc(8, 11.5, 3.2), pendant)
        cv.dots([(8, 10), (8, 11), (8, 12), (8, 13)], "#0c1a0c", None)
    elif kind == "skull":
        cv.shape(rect(5, 9, 10, 12) | rect(6, 13, 9, 14), P["white"])
        cv.dots([(6, 11), (9, 11)], "#2a2c34").dots([(7, 14)], "#2a2c34")
    elif kind == "lucky":
        cv.shape(disc(8, 11.5, 3.4), P["cream"])
        cv.dots([(7, 10), (9, 10), (6, 11), (7, 11), (8, 11), (9, 11), (10, 11), (7, 12), (8, 12), (9, 12), (8, 13)], "#e2343e")
    return cv


def necklace(metal, pendant=None, kind="mining"):
    m = {"copper": P["copper"], "gold": P["gold"], "platinum": P["iron"]}[metal]
    cv = Canvas()
    if kind == "mining":
        cv.dots([(x, y) for x, y in sorted(ring(8, 7, 6.5, 5.5)) if (x + y) % 2 == 0 and y < 11], m[1], m[3])
        cv.shape(disc(8, 12, 3), m)
        cv.shape({(7, 11), (8, 11), (7, 12), (8, 12)}, pendant)
        cv.dot(7, 11, HL, pendant[3])
    elif kind == "liora":
        cv.shape(ring(8, 7, 6.4, 5.2), m)
        cv.shape({(6, 12), (7, 12), (8, 12), (9, 12), (7, 13), (8, 13), (7, 14), (8, 14), (6, 11), (9, 11)} - {(6, 11), (9, 11)} | {(6, 11), (9, 11)}, P["ruby"])
        cv.dot(7, 12, HL, P["ruby"][3])
    elif kind == "beads":
        for k in range(12):
            a = k * math.pi / 6
            x, y = round(8 + 5.5 * math.cos(a) - 0.5), round(8 + 5.5 * math.sin(a) - 0.5)
            cv.dot(x, y, ["#d0488a", "#34c0c8", "#9dff6a"][k % 3], "#1c0a12")
        cv.shape({(7, 12), (8, 12), (6, 11), (7, 11), (8, 11), (9, 11)}, P["red"]).dots([(7, 13), (8, 13)], "#f1e6c8", "#3a3226")
    return cv


# ----------------------------------------------------------------------------- tools
def glove(pal, pattern=None, cuff=None):
    cv = Canvas()
    hand = rect(4, 6, 11, 12) | rect(4, 2, 5, 6) | rect(6, 1, 7, 6) | rect(8, 2, 9, 6) | rect(10, 3, 11, 6) | {(2, 7), (3, 7), (2, 8), (3, 8), (3, 9)}
    cv.shape(hand, pal)
    if pattern == "scales":
        cv.dots([(5, 8), (7, 8), (9, 8), (6, 10), (8, 10), (10, 10)], pal[0])
    cv.shape(rect(4, 13, 11, 14), cuff or pal)
    return cv


def broom():
    cv = Canvas()
    cv.shape(seg(2, 2, 10, 10, 1), P["darkwood"])
    cv.shape(poly([(9, 10), (11.5, 8.5), (15.5, 13), (14, 15.5), (9.5, 14)]), P["sand"])
    cv.dots([(10, 10), (11, 9), (11, 10)], P["red"][1], P["red"][3])
    return cv


def lantern():
    cv = Canvas()
    cv.dots([(7, 0), (8, 0), (6, 1), (9, 1)], "#3a3440", "#0c0a10")
    cv.shape(rect(4, 2, 11, 3), P["shadow"])
    cv.shape(rect(4, 4, 11, 12), P["fire"])
    cv.dots(line(4, 4, 4, 12) + line(11, 4, 11, 12) + line(7, 4, 7, 6), "#141216")
    cv.shape({(7, 8), (8, 8), (7, 9), (8, 9), (7, 10), (8, 10), (8, 7)}, P["yellow"], "light")
    cv.shape(rect(3, 13, 12, 14), P["shadow"])
    return cv


def torch():
    cv = Canvas()
    cv.shape(seg(12, 14, 7, 9, 2), P["darkwood"])
    cv.shape(rect(5, 7, 7, 8), P["slate"])
    cv.shape(poly([(3, 7), (1.5, 4), (3, 0.5), (5, 2), (6.5, 0.5), (8.5, 3), (7, 6.5)]), P["fire"])
    cv.shape({(4, 4), (5, 4), (4, 5), (5, 5), (5, 3)}, P["yellow"], "light")
    return cv


def telescope():
    cv = Canvas()
    cv.shape(seg(2, 11, 6, 7, 4), P["gold"])
    cv.shape(seg(7, 7, 11, 3, 3), P["crimson"])
    cv.shape(seg(12, 3, 14, 1, 2), P["gold"])
    cv.dots([(1, 12), (2, 12), (1, 11)], "#bfe6ff", "#3a1c04")
    return cv


def skull(pal, eyes="#e6e04a", cracks=None):
    cv = Canvas()
    cv.shape(ellipse(8, 7, 6.2, 6) | rect(4, 11, 11, 14), pal)
    cv.dots(rect(4, 7, 6, 9) | rect(9, 7, 11, 9), "#141216").dots([(5, 8), (10, 8)], eyes)
    cv.dots([(7, 10), (8, 10)], "#141216").dots([(5, 13), (7, 13), (9, 13)], "#141216")
    if cracks:
        cv.dots([(9, 2), (10, 3), (9, 4), (4, 4), (3, 5)], cracks)
    return cv


# ----------------------------------------------------------------------------- charms
def charm(name):
    cv = Canvas()
    if name == "Clover":
        for cx, cy in ((6, 5), (10, 5), (6, 9), (10, 9)):
            cv.shape(disc(cx, cy, 2.6), P["olive"])
        cv.shape(seg(8, 10, 10, 14), P["olive"]).dots([(8, 7)], "#fff3a0", P["olive"][3])
    elif name == "Horseshoe":
        cv.shape(ring(8, 7.5, 6.5, 3.4) - rect(5, 9, 10, 15), P["steel"])
        cv.shape(rect(1, 9, 4, 14) | rect(11, 9, 14, 14), P["steel"])
        cv.dots([(2, 7), (13, 7), (2, 11), (13, 11), (5, 2), (10, 2)], "#39414f")
    elif name == "Lucky Egg":
        cv.shape(ellipse(8, 8.5, 5, 6.5), C("#ffe8f4", "#9af0ff", "#46b67a", "#2b2f45"))
        cv.dots([(5, 5), (6, 5), (7, 4), (9, 8), (10, 8), (11, 7), (4, 11), (5, 12)], "#ff6f9a").dots([(6, 3)], HL)
    elif name == "Lucky Rose":
        cv.shape(seg(3, 14, 8, 9), P["leaf"]).shape({(3, 10), (4, 10), (4, 11), (7, 13), (8, 13)}, P["leaf"])
        cv.shape(disc(10.5, 5, 4), P["red"])
        cv.dots([(10, 4), (11, 4), (11, 5), (10, 6), (9, 5)], "#7d0f1f").dot(9, 3, "#ffb3b3")
    elif name == "Rabbits Foot":
        cv.shape(seg(4, 11, 10, 5, 5) | disc(4.5, 11.5, 3.4), P["cream"])
        cv.dots([(2, 13), (4, 14), (1, 11)], P["cream"][2], P["cream"][3])
        cv.dots([(6, 8), (8, 6), (5, 10)], P["cream"][2])
        cv.shape(rect(11, 3, 12, 5) | {(10, 4), (11, 2)}, P["slate"])
        cv.dots([(13, 1), (14, 1), (14, 2), (13, 2)] and [(13, 1), (14, 2)], "#9aa0b4", "#1c1c28")
    elif name == "Starfish":
        cv.shape(poly([(8, 0.5), (10, 5.5), (15.5, 6), (11.5, 9.5), (13, 15), (8, 12), (3, 15), (4.5, 9.5), (0.5, 6), (6, 5.5)]), P["orange"])
        cv.dots([(8, 4), (8, 8), (11, 7), (5, 7), (10, 11), (6, 11)], "#fff1cf")
    elif name == "Wishbone":
        cv.shape(seg(8, 3, 4, 13, 2) | seg(8, 3, 12, 13, 2), P["bone"])
        cv.shape(rect(7, 1, 9, 3), P["bone"]).shape(rect(3, 13, 4, 14) | rect(12, 13, 13, 14), P["bone"])
    return cv


# ----------------------------------------------------------------------------- specs (PORE's own designs)
SPECS = {
    "Abyssal Edge": lambda: sword(C("#eaffff", "#5ad4ff", "#1c64b4", "#0a2046"), P["azurite"], shape="crystal", w=3, gshape="wing", gem_=P["cyan"], extra="glow:#8ff0ff"),
    "Abyssal Pincer": lambda: staff(P["violet"], "claw", P["fire"], P["orange"]),
    "Azurite Axe": lambda: axe(P["azurite"], P["shadow"], "crescent", edge="#dff4ff"),
    "Brutal Staff": lambda: staff(P["darkwood"], "eye", P["red"]),
    "Burning Dagger": lambda: dagger(P["fire"], P["shadow"], shape="curved", extra="flames"),
    "Caster Staff": lambda: staff(P["darkwood"], "crystal", P["sapphire"], P["copper"]),
    "Chaosweaver": lambda: sword(C("#f4f4f8", "#9a98a8", "#56546a", "#1a1824"), P["shadow"], shape="cleaver"),
    "Chill Strike": lambda: sword(C("#f0fffb", "#8ee8d6", "#2e8c8a", "#0c3030"), P["azurite"], gshape="spiky", gem_=P["ice"]),
    "Cleaver": lambda: dagger(P["steel"], P["shadow"], P["wood"], shape="cleaver", extra="blood"),
    "Club": lambda: mace(P["wood"], kind="club"),
    "Cool Stick": lambda: wand(P["wood"], "leaf", P["olive"]),
    "Copper Sword": lambda: sword(P["copper"], P["emerald"]),
    "Cosmic Coil": lambda: staff(P["purpurite"], "coral", P["purpurite"]),
    "Dawn's Justice": lambda: sword(C("#fff6c0", "#ffb03a", "#d05a1c", "#3e1406"), P["shadow"], w=3, gshape="wing", gem_=P["sapphire"], pgem=P["sapphire"]),
    "Drakespine Blade": lambda: sword(P["plum"], P["mint"], shape="dserrated", gshape="spiky", gem_=P["mint"]),
    "Duststrike": lambda: sword(P["sand"], P["sand"], shape="wavy", w=3, extra="rock"),
    "Earth Staff": lambda: staff(C("#d4a09a", "#8a5a5a", "#4c2c30", "#1c0e10"), "crook", P["leaf"]),
    "Earthshaper": lambda: sword(C("#c8ffb0", "#f0a8a0", "#a45062", "#2e1016"), P["salmon"], w=3, extra="vines"),
    "Expert Staff": lambda: staff(P["shadow"], "claw", P["leaf"], P["white"]),
    "Frostcurse": lambda: dagger(P["ice"], P["azurite"], shape="serrated", extra="glow:#ffffff"),
    "Frostheart Claymore": lambda: sword(C("#ffffff", "#6ee0ff", "#1a88d8", "#08305a"), P["azurite"], shape="crystal", w=3, L=9, gem_=P["ice"]),
    "Ghostweave Sword": lambda: sword(C("#e8fff8", "#7ec8c0", "#2e6a70", "#0c2428"), P["azurite"], shape="taper", w=2, gshape="spiky"),
    "Gilded Dominion": lambda: sword(P["gold"], P["white"], w=3, gshape="wing", gem_=P["ruby"], pgem=P["ruby"]),
    "Glutton's Scepter": lambda: mace(C("#ffc8b8", "#c8746a", "#7a3a34", "#2a0e0c"), kind="drumstick"),
    "Goblin Mace": lambda: mace(C("#e8b890", "#a8703e", "#5e3a1c", "#241206"), kind="club", studs=True),
    "Gold Sword": lambda: sword(P["gold"], P["gold"], pgem=P["amethyst"], gem_=P["amethyst"]),
    "Green Death": lambda: sword(P["mint"], P["teal"], w=3, gshape="round"),
    "Horn Dancer": lambda: sword(P["slate"], P["fire"], shape="taper", gshape="spiky", gem_=P["ruby"]),
    "Howling Edge": lambda: sword(P["pink"], P["magenta"], shape="curved"),
    "Hungry Blade": lambda: chakram(P["fire"]),
    "Ice Sword": lambda: sword(P["ice"], P["shadow"], gem_=P["emerald"]),
    "Infernal Brand": lambda: sword(C("#fff4b0", "#ff8a5a", "#d8306a", "#3e0822"), P["shadow"], shape="wavy", w=2, extra="flames"),
    "Infernal Fork": lambda: trident(C("#ffc4f0", "#e060b0", "#7a2a70", "#2a0826"), P["violet"], ornate=True),
    "Iron Mace": lambda: mace(P["slate"], P["orange"], kind="spiked"),
    "Iron Sword": lambda: sword(P["steel"], P["orange"], pgem=P["ruby"]),
    "Learner Staff": lambda: staff(P["slate"], "orb", P["sapphire"], P["slate"], thin=True),
    "Mindbreaker": lambda: sword(C("#ffd6ff", "#c07ae8", "#6a3a9a", "#200c38"), P["shadow"], w=3, gshape="spiky", gem_=P["pink"]),
    "Mindshatter": lambda: sword(C("#ffffff", "#f0b8d8", "#b0508a", "#3a0c2a"), P["magenta"], shape="curved", w=3),
    "Molten Axe": lambda: axe(P["lava"], P["darkwood"], "wedge", edge="#fff8c0"),
    "Molten Sword": lambda: sword(P["lava"], P["volcanic"], shape="cleaver", extra="cracks"),
    "Moonweaver": lambda: sword(P["moon"], P["pink"], shape="serrated", w=3, gshape="hook"),
    "Mountainheart": lambda: sword(C("#dce4f0", "#8a9ab4", "#4a566e", "#161c28"), P["slate"], w=3, extra="rock", gem_=P["pink"]),
    "Nightfang": lambda: sword(P["silver"], P["plum"], shape="taper", gem_=P["ruby"]),
    "Nunchaku": lambda: nunchaku(P["darkwood"]),
    "Plaguebringer": lambda: sword(P["bone"], P["bone"], w=3, extra="drips", gem_=P["leaf"]),
    "Platinum Dagger": lambda: dagger(P["platinum"], P["slate"]),
    "Platinum Sword": lambda: sword(P["platinum"], P["slate"]),
    "Purpurite Sword": lambda: sword(P["purpurite"], P["shadow"], gem_=P["amethyst"]),
    "Ray's Axe": lambda: axe(C("#ffd0e0", "#ff5a8a", "#a8204a", "#3a0616"), P["violet"], "crescent", edge="#dfffe8"),
    "Ray's Cleaver": lambda: axe(C("#dfffe0", "#ff6a9a", "#b0305a", "#3a0616"), P["violet"], "cleaver"),
    "Scythe": lambda: scythe(P["steel"], P["wood"]),
    "Serpent's Kiss": lambda: sword(C("#ffc8ec", "#e0609a", "#8a2c68", "#2a0822"), P["plum"], shape="wavy", extra="glow:#ffb0e0"),
    "Shackled Magma": lambda: sword(C("#ffe8a0", "#ff9a5a", "#4a3a4a", "#12080c"), P["volcanic"], shape="curved", w=3, extra="cracks"),
    "Silver Dagger": lambda: dagger(P["silver"], P["iron"], shape="taper"),
    "Silver Sword": lambda: sword(P["silver"], P["iron"]),
    "Simple Wand": lambda: wand(P["copper"], "none", P["orange"]),
    "Slime Wrath": lambda: staff(P["violet"], "orb", P["amethyst"], P["violet"], thin=True),
    "Soldier Sword": lambda: sword(P["slate"], P["gold"], gshape="wing"),
    "Soulharvest Scythe": lambda: scythe(P["slate"], P["pink"]),
    "Starcutter": lambda: sword(C("#ffffff", "#7ae8ff", "#b060e0", "#1c1440"), P["mint"], shape="crystal", w=3, gshape="spiky", extra="prism", gem_=P["pink"]),
    "Stinglash": lambda: stinger(C("#f0e0f0", "#b8a0c0", "#6a5478", "#241a2e")),
    "The All-Seeing Blade": lambda: sword(P["pink"], P["pink"], w=3, gshape="round", gem_=P["crimson"]),
    "The Devourer": lambda: staff(P["teal"], "maw"),
    "The Last Laugh": lambda: sword(C("#e0d0ff", "#8a74e0", "#40308a", "#140c34"), P["violet"], gshape="hook", gem_=P["cyan"]),
    "The Watcher's Gaze": lambda: sword(C("#ffffff", "#f0a0b0", "#b02a44", "#3a0612"), P["crimson"], w=3, gshape="spiky", gem_=P["red"]),
    "Three Fates": lambda: fates(),
    "Tidecaller": lambda: sword(P["orange"], P["leaf"], shape="cleaver", gshape="spiky", gem_=P["pink"]),
    "Tidewoven Blade": lambda: sword(C("#e8e0ff", "#8a7cf0", "#3e2a9a", "#140a3c"), P["silver"], shape="taper", L=9, gem_=P["silver"]),
    "Trident": lambda: trident(P["crimson"], P["shadow"]),
    "Vamp Blade": lambda: sword(P["shadow"], P["orange"]),
    "Vamp Blade +1": lambda: sword(C("#8a6a9a", "#4a2a5a", "#221028", "#0a0410"), P["orange"], gem_=P["crimson"]),
    "Vamp Blade +2": lambda: sword(C("#c07ac0", "#7a2a6a", "#301030", "#0e0410"), P["fire"], w=3, gem_=P["crimson"], extra="glow:#ff7ad0"),
    "Volcanic Sword": lambda: sword(P["volcanic"], P["volcanic"], w=3, extra="cracks", gem_=P["lava"]),
    "Warfin": lambda: sword(C("#eafffc", "#94b8c0", "#4a6470", "#141e24"), P["slate"], shape="serrated", w=3),
    "Wooden Sword": lambda: sword(P["wood"], P["wood"], P["darkwood"]),

    "Azurite Helmet": lambda: knight(P["azurite"], "slit", crest="fin", crest_pal=P["sapphire"]),
    "Bogsteel Helmet": lambda: knight(P["bogsteel"], "eye", pattern="mottle"),
    "Bunny Ears": lambda: bunny_ears(),
    "Bycocket": lambda: hat("bycocket", P["leaf"], accent=P["red"]),
    "Dark Crown": lambda: crown(P["shadow"], P["magenta"]),
    "Fedora": lambda: hat("fedora", P["wood"], band=P["darkwood"]),
    "Flameguard Helmet": lambda: knight(P["brownplate"], "t", trim=P["crimson"], crest="wave", crest_pal=P["crimson"]),
    "Forestguard Helmet": lambda: knight(P["plum"], "slit", pattern="vines"),
    "Frostguard Helmet": lambda: knight(P["plum"], "t", crest="wave", crest_pal=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38"), pattern="frost"),
    "Glasses": lambda: glasses(),
    "Gold Helmet": lambda: knight(P["gold"], "t", trim=P["violet"]),
    "Horror Mask": lambda: mask("horror"),
    "Iron Bucket": lambda: bucket(P["iron"], "slit", pattern="rivets"),
    "Kitsune Mask": lambda: mask("kitsune"),
    "Lucky Hat": lambda: hat("tophat", P["leaf"], band=P["darkwood"], accent=P["gold"]),
    "Mining Helmet": lambda: hat("hardhat", P["yellow"]),
    "Mystery Mask": lambda: mask("mystery"),
    "Pirate Hat": lambda: hat("pirate", P["slate"], accent=P["red"]),
    "Platinum Helmet": lambda: knight(P["platinum"], "grille", crest="plume", crest_pal=P["white"]),
    "Police Hat": lambda: hat("police", P["navy"]),
    "Purpurite Helmet": lambda: bucket(P["purpurite"], "bars", bands=P["plum"]),
    "Santa Hat": lambda: hat("santa", P["red"]),
    "Silver Helmet": lambda: knight(P["silver"], "slit", crest="plume", crest_pal=P["sand"]),
    "Sleepy Wizard Hat": lambda: hat("wizard", P["sapphire"], band=P["navy"], accent=P["orange"]),
    "Soldier Helmet": lambda: knight(P["steel"], "t", crest="plume", crest_pal=P["red"]),
    "Sunhat": lambda: hat("sunhat", P["yellow"], band=P["orange"]),
    "Volcanic Helmet": lambda: knight(P["volcanic"], "open", pattern="cracks"),
    "Windguard Helmet": lambda: knight(P["magenta"], "slit", pattern="streaks", crest="fin", crest_pal=P["cyan"]),
    "Witches Hat": lambda: hat("witch", P["slate"], band=P["shadow"]),
    "Wizard Hat": lambda: hat("wizard", P["sapphire"], band=P["white"], accent=P["white"]),
    "Wooden Helmet": lambda: bucket(P["wood"], "slit", bands=P["darkwood"], pattern="planks"),

    "Azurite Chestplate": lambda: chestplate(P["azurite"], trim=P["cyan"], emblem=P["cyan"]),
    "Bogsteel Chestplate": lambda: chestplate(P["bogsteel"], pattern="mottle"),
    "Chainmail Shirt": lambda: shirt(P["steel"], pattern="chain"),
    "Dark Blue Cloak": lambda: cloak(P["navy"], trim=P["slate"]),
    "Draculas Cloak": lambda: cloak(P["shadow"], collar=P["red"], inner=P["red"]),
    "Flameguard Chestplate": lambda: chestplate(P["brownplate"], trim=P["crimson"]),
    "Forestguard Chestplate": lambda: chestplate(P["plum"], pattern="vines"),
    "Frostguard Chestplate": lambda: chestplate(P["plum"], trim=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38"), pattern="frost"),
    "Gold Chestplate": lambda: chestplate(P["gold"], emblem=P["ruby"]),
    "Long sleeve Shirt": lambda: shirt(P["white"], long_=True),
    "Platinum Chestplate": lambda: chestplate(P["platinum"], trim=P["steel"], emblem=P["ice"]),
    "Purple Cloak": lambda: cloak(P["shadow"], trim=P["purpurite"]),
    "Purpurite Chestplate": lambda: chestplate(P["purpurite"], pattern="checker"),
    "Shirt": lambda: shirt(P["salmon"]),
    "Silver Chestplate": lambda: chestplate(P["silver"], trim=P["iron"]),
    "Soldier Chestplate": lambda: chestplate(P["iron"], trim=P["red"], emblem="cross"),
    "Volcanic Chestplate": lambda: chestplate(P["volcanic"], pattern="cracks"),
    "Windguard Chestplate": lambda: chestplate(P["magenta"], pattern="streaks"),
    "Wooden Chestplate": lambda: chestplate(P["wood"], pattern="planks"),

    "Azurite Greaves": lambda: greaves(P["azurite"], trim=P["cyan"]),
    "Bogsteel Greaves": lambda: greaves(P["bogsteel"], pattern="mottle"),
    "Flameguard Greaves": lambda: greaves(P["brownplate"], trim=P["crimson"]),
    "Forestguard Greaves": lambda: greaves(P["plum"], pattern="vines"),
    "Frostguard Greaves": lambda: greaves(P["plum"], trim=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38")),
    "Gold Greaves": lambda: greaves(P["gold"], trim=P["orange"]),
    "Lifebuoy": lambda: lifebuoy(),
    "Platinum Greaves": lambda: greaves(P["platinum"], trim=P["ice"]),
    "Purpurite Greaves": lambda: greaves(P["purpurite"], trim=P["violet"]),
    "Silver Greaves": lambda: greaves(P["silver"]),
    "Soldier Greaves": lambda: greaves(P["iron"], trim=P["red"]),
    "Volcanic Greaves": lambda: greaves(P["volcanic"], pattern="cracks"),
    "Windguard Greaves": lambda: greaves(P["magenta"], pattern="streaks"),
    "Wooden Greaves": lambda: greaves(P["wood"], trim=P["darkwood"]),

    "Azurite Shoes": lambda: boot(P["azurite"], trim=P["cyan"]),
    "Bogsteel Shoes": lambda: boot(P["bogsteel"], pattern="mottle"),
    "Flameguard Shoes": lambda: boot(P["brownplate"], trim=P["crimson"]),
    "Forestguard Shoes": lambda: boot(P["plum"], pattern="vines"),
    "Frostguard Shoes": lambda: boot(P["plum"], trim=C("#fff0ff", "#e6c0e8", "#9a78a8", "#2e1e38")),
    "Gold Boots": lambda: boot(P["gold"], trim=P["orange"]),
    "Magic Loafers": lambda: boot(P["orange"], kind="loafer", gem_=P["teal"]),
    "Platinum Boots": lambda: boot(P["platinum"], trim=P["ice"]),
    "Purpurite Shoes": lambda: boot(P["amethyst"], trim=P["purpurite"]),
    "Sandals": lambda: boot(P["copper"], kind="sandal"),
    "Shackle": lambda: boot(P["slate"], kind="shackle"),
    "Silver Batons": lambda: boot(P["silver"], trim=P["iron"]),
    "Soldier Boots": lambda: boot(P["iron"], trim=P["red"]),
    "Volcanic Boots": lambda: boot(P["volcanic"], pattern="cracks"),
    "Warm Boots": lambda: boot(P["copper"], trim=P["cream"]),
    "Windguard Shoes": lambda: boot(P["magenta"], pattern="streaks"),
    "Wooden Shoes": lambda: boot(P["wood"], kind="clog"),

    "Ancient Shield": lambda: shield("tower", C("#b8c8b8", "#6e8278", "#3a4a42", "#141c18"), P["slate"], emblem="sun"),
    "Blue Shield": lambda: shield("heater", C("#e0e4ff", "#8e98e8", "#4a4ea8", "#161838"), P["violet"], emblem="streak"),
    "Bogsteel Shield": lambda: shield("oval", P["bogsteel"], P["shadow"], emblem="mottle"),
    "Chocolate Shield": lambda: shield("tower", P["chocolate"], P["chocolate"], emblem="chocolate"),
    "Falcon Shield": lambda: shield("heater", P["gold"], P["darkwood"], emblem="falcon"),
    "Flameguard Shield": lambda: shield("oval", P["brownplate"], P["crimson"]),
    "Forestguard Shield": lambda: shield("oval", P["plum"], P["teal"]),
    "Frostguard Shield": lambda: shield("oval", P["plum"], C("#fff0ff", "#e6a0d8", "#9a5890", "#2e1028")),
    "Goblin Shield": lambda: shield("oval", P["sand"], P["darkwood"], emblem="bumps"),
    "Pink Shield": lambda: shield("heater", P["pink"], P["purpurite"], emblem="streak"),
    "Platinum Shield": lambda: shield("heater", P["platinum"], P["steel"], boss=P["ice"]),
    "Reinforced Shield": lambda: shield("round", P["wood"], P["steel"], emblem="x", boss=P["steel"]),
    "Rhino Shield": lambda: shield("round", C("#e0886a", "#a8402a", "#5a1c12", "#1e0806"), P["cream"], boss=P["bone"]),
    "Soldier Shield": lambda: shield("heater", P["cream"], P["iron"], emblem="cross"),
    "Turtle Shell": lambda: shield("oval", P["leaf"], C("#3c7a2c", "#24541a", "#123010", "#06140a"), emblem="turtle"),
    "Volcanic Shield": lambda: shield("oval", P["volcanic"], P["volcanic"], emblem="cracks"),
    "Windguard Shield": lambda: shield("oval", P["magenta"], P["sapphire"], emblem="streak"),
    "Wooden Shield": lambda: shield("round", P["wood"], P["darkwood"], emblem="planks", boss=P["steel"]),

    "Aggressive Amulet": lambda: amulet(P["slate"]),
    "Brutal Amulet": lambda: amulet(P["fire"], kind="framed", frame=P["copper"]),
    "Deadly Amulet": lambda: amulet(P["white"], cord=P["slate"], kind="skull"),
    "Energetic Amulet": lambda: amulet(P["cyan"]),
    "Lucky Amulet": lambda: amulet(P["cream"], kind="lucky"),
    "Ocean Spirit Amulet": lambda: amulet(P["cyan"], kind="framed", frame=P["orange"]),
    "Resilient Amulet": lambda: amulet(P["orange"], cord=P["slate"], kind="square"),
    "Serpentine Amulet": lambda: amulet(P["leaf"], kind="eye"),
    "Sun Demon Amulet": lambda: amulet(P["red"], kind="framed", frame=P["orange"]),
    "Terra Empress Amulet": lambda: amulet(P["leaf"], kind="framed", frame=P["orange"]),
    "Wind Ghost Amulet": lambda: amulet(P["sapphire"], kind="framed", frame=P["orange"]),

    "Copper Mining Necklace": lambda: necklace("copper", P["sapphire"]),
    "Gold Mining Necklace": lambda: necklace("gold", P["sapphire"]),
    "Platinum Mining Necklace": lambda: necklace("platinum", P["leaf"]),
    "Liora's Necklace": lambda: necklace("gold", kind="liora"),
    "Shroom Seeker": lambda: necklace("gold", kind="beads"),

    "Basic Gloves": lambda: glove(P["wood"]),
    "Elite Gloves": lambda: glove(P["violet"], cuff=P["teal"]),
    "Red Gloves": lambda: glove(P["crimson"]),
    "Snake Gloves": lambda: glove(P["darkwood"], pattern="scales", cuff=P["olive"]),
    "Broom": lambda: broom(),
    "Lantern": lambda: lantern(),
    "Torch": lambda: torch(),
    "Telescope": lambda: telescope(),
    "Mana Skull": lambda: skull(C("#d8dca0", "#8e9468", "#4e523a", "#1a1c12")),
    "Great Mana Skull": lambda: skull(P["violet"], eyes="#ff3a4a", cracks="#e6e04a"),
}


def ring_spec(name):
    words = name.replace(" Ring", "").split()
    if not words or words == ["Basic"]:
        return lambda: ring_icon("iron", "plain")
    metal, stat = words[-1].lower(), " ".join(words[:-1]).lower()
    if metal not in METAL:
        return None
    style, g = "plain", None
    if stat in GEMS:
        style, g = "gem", GEMS[stat]
    elif stat in ("attack", "crit", "flat", "mana"):
        style = stat
    elif stat == "crit damage":
        style = "critdmg"
    return lambda: ring_icon(metal, style, g)


def main():
    data = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    entries, missing = [], []
    for it in data["items"]:
        spec = SPECS.get(it["name"]) or (ring_spec(it["name"]) if it["type"] == "RING" else None)
        if not spec:
            missing.append(it["name"])
            continue
        entries.append((f"i{it['id']}", spec()))
    for ch in data.get("charms", []):
        entries.append((f"c{ch['id']}", charm(ch["name"])))
    symbols = []
    for key, cv in entries:
        svg = cv.svg()
        (OUT / f"{key}.svg").write_text(svg + "\n", encoding="utf-8")
        symbols.append(f'<symbol id="{key}" viewBox="0 0 {N} {N}">{svg[svg.index(">") + 1:svg.rindex("</svg>")]}</symbol>')
    sprite = f'<svg xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" style="display:none">{"".join(symbols)}</svg>'
    SPRITE.write_text(sprite, encoding="utf-8")
    print(f"pixel icons: {len(entries)} drawn at {N}x{N} -> icons/pixel/, icons/sprite-pixel.svg ({len(sprite) // 1024} KB); missing: {missing or 'none'}")


if __name__ == "__main__":
    main()
