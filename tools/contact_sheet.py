#!/usr/bin/env python3
"""Render enlarged contact sheets of the wiki's pixel icons, grouped by item type.

Used while drawing the modern icon set: each sheet shows the original sprite at 8x with its
key and name so a designer can study it.

Usage: python tools/contact_sheet.py [out_dir]
"""
from __future__ import annotations

import base64
import io
import json
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "items.json"
SCALE, CELL_W, CELL_H, COLS = 8, 200, 190, 6


def main() -> None:
    out_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".cache" / "sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    groups: dict[str, list] = {}
    for it in data["items"]:
        groups.setdefault(it["type"], []).append(("i" + str(it["id"]), it["name"], it["icon"]["src"]))
    groups["CHARM"] = [("c" + str(c["id"]), c["name"], c["icon"]["src"]) for c in data.get("charms", [])]
    for gtype, entries in groups.items():
        entries.sort(key=lambda e: e[1].lower())
        for part in range(0, len(entries), 30):
            chunk = entries[part:part + 30]
            rows = (len(chunk) + COLS - 1) // COLS
            sheet = Image.new("RGBA", (COLS * CELL_W, rows * CELL_H), (24, 26, 36, 255))
            draw = ImageDraw.Draw(sheet)
            for i, (key, name, src) in enumerate(chunk):
                png = base64.b64decode(src.split(",", 1)[1])
                im = Image.open(io.BytesIO(png)).convert("RGBA")
                im = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
                x, y = (i % COLS) * CELL_W, (i // COLS) * CELL_H
                sheet.paste(im, (x + (CELL_W - im.width) // 2, y + 8), im)
                draw.text((x + 6, y + CELL_H - 34), f"{key}", fill=(120, 130, 160, 255))
                draw.text((x + 6, y + CELL_H - 20), name[:30], fill=(230, 235, 245, 255))
            suffix = f"-{part // 30 + 1}" if len(entries) > 30 else ""
            sheet.save(out_dir / f"{gtype.lower()}{suffix}.png")
    print(f"wrote sheets for {len(groups)} types to {out_dir}")


if __name__ == "__main__":
    main()
