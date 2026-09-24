#!/usr/bin/env python3
"""Render the PORE gem logo as PNG app icons for the web app manifest.

Output: icons/app/icon-192.png, icons/app/icon-512.png, icons/app/maskable-512.png
Usage:  python tools/make_app_icons.py   (needs Pillow)
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "app"


def gradient(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    a, b = (139, 124, 255), (209, 109, 255)
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size - 2)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)
    return img


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def gem(draw: ImageDraw.ImageDraw, size: int, inset: float) -> None:
    s = size
    o = s * inset
    w = s - 2 * o
    p = lambda x, y: (o + x * w / 32, o + y * w / 32)  # noqa: E731 - logo drawn on a 32-unit grid
    body = [p(8, 4), p(24, 4), p(30, 12), p(16, 29), p(2, 12)]
    draw.polygon(body, fill=(255, 255, 255, 235))
    line = (123, 108, 240, 255)
    lw = max(1, int(w / 22))
    draw.line([p(8, 4), p(12, 12), p(16, 4), p(20, 12), p(24, 4)], fill=line, width=lw, joint="curve")
    draw.line([p(2, 12), p(30, 12)], fill=line, width=lw)
    draw.line([p(12, 12), p(16, 29), p(20, 12)], fill=line, width=lw, joint="curve")


def render(size: int, maskable: bool) -> Image.Image:
    img = gradient(size)
    if not maskable:
        img.putalpha(rounded_mask(size, size // 5))
    draw = ImageDraw.Draw(img)
    gem(draw, size, 0.28 if maskable else 0.2)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render(192, False).save(OUT / "icon-192.png")
    render(512, False).save(OUT / "icon-512.png")
    render(512, True).save(OUT / "maskable-512.png")
    print(f"wrote 3 app icons to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
