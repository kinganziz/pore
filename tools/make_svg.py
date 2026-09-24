#!/usr/bin/env python3
"""Generate SVG twins of every pixel-art icon in data/items.json.

Each opaque pixel run becomes a 1-unit-high rectangle inside a per-colour <path>, so the
SVG renders identically to the PNG at any size and can be styled or recoloured with CSS.

Output: icons/svg/<key>.svg where key is i<item id> for equipment and c<item id> for charms.

Usage:
    python tools/make_svg.py
"""
from __future__ import annotations

import base64
import io
import json
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "items.json"
OUT_DIR = ROOT / "icons" / "svg"


def png_to_svg(png: bytes) -> str:
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    w, h = im.size
    px = im.load()
    runs: dict[tuple[int, int, int, int], list[str]] = {}
    for y in range(h):
        x = 0
        while x < w:
            color = px[x, y]
            if color[3] == 0:
                x += 1
                continue
            x0 = x
            while x < w and px[x, y] == color:
                x += 1
            runs.setdefault(color, []).append(f"M{x0} {y}h{x - x0}v1h-{x - x0}z")
    parts = []
    for (r, g, b, a), d in runs.items():
        fill = f"#{r:02x}{g:02x}{b:02x}"
        opacity = "" if a == 255 else f' fill-opacity="{a / 255:.3f}"'
        parts.append(f'<path fill="{fill}"{opacity} d="{"".join(d)}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges">{"".join(parts)}</svg>')


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = [("i", it) for it in data["items"]] + [("c", ch) for ch in data.get("charms", [])]
    total = 0
    symbols = []
    for prefix, entry in entries:
        png = base64.b64decode(entry["icon"]["src"].split(",", 1)[1])
        svg = png_to_svg(png)
        out = OUT_DIR / f"{prefix}{entry['id']}.svg"
        out.write_text(svg, encoding="utf-8")
        total += len(svg)
        # one <symbol> per icon for the single-request sprite the app uses
        inner = svg[svg.index(">") + 1:-len("</svg>")]
        symbols.append(f'<symbol id="{prefix}{entry["id"]}" viewBox="0 0 {entry["icon"]["w"]} {entry["icon"]["h"]}">{inner}</symbol>')
    sprite = ('<svg xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" style="display:none">'
              + "".join(symbols) + "</svg>")
    (ROOT / "icons" / "sprite.svg").write_text(sprite, encoding="utf-8")
    print(f"wrote {len(entries)} SVG icons to {OUT_DIR.relative_to(ROOT)} ({total // 1024} KB total) and icons/sprite.svg ({len(sprite) // 1024} KB)")

    # Modern set: hand-drawn icons in icons/modern/<key>.svg; items not drawn yet fall back to the pixel symbol.
    modern_dir = ROOT / "icons" / "modern"
    modern_symbols, drawn = [], 0
    for (prefix, entry), pixel_symbol in zip(entries, symbols):
        key = f"{prefix}{entry['id']}"
        path = modern_dir / f"{key}.svg"
        if path.exists():
            modern_symbols.append(modern_symbol(key, path.read_text(encoding="utf-8")))
            drawn += 1
        else:
            modern_symbols.append(pixel_symbol)
    modern_sprite = '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + "".join(modern_symbols) + "</svg>"
    (ROOT / "icons" / "sprite-modern.svg").write_text(modern_sprite, encoding="utf-8")
    print(f"wrote icons/sprite-modern.svg: {drawn}/{len(entries)} modern icons drawn, the rest fall back to pixel art")


def modern_symbol(key: str, svg: str) -> str:
    """Turn a standalone hand-drawn SVG into a <symbol>, namespacing ids so gradients cannot collide."""
    import re

    svg = re.sub(r"<\?xml[^>]*\?>|<!--.*?-->", "", svg, flags=re.S).strip()
    open_tag = re.match(r"<svg\b[^>]*>", svg, flags=re.S)
    if not open_tag:
        raise SystemExit(f"{key}: not an <svg> document")
    view = re.search(r'viewBox="([^"]+)"', open_tag.group(0))
    viewbox = view.group(1) if view else "0 0 64 64"
    inner = svg[open_tag.end():svg.rfind("</svg>")]
    inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{key}-{m.group(1)}"', inner)
    inner = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{key}-{m.group(1)})", inner)
    inner = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{key}-{m.group(1)}"', inner)
    return f'<symbol id="{key}" viewBox="{viewbox}">{inner}</symbol>'


if __name__ == "__main__":
    main()
