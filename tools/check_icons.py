#!/usr/bin/env python3
"""Check that every item (key i<id>: equipment and the other items) and charm (key c<id>) has a drawing in each icon style:

    icons/modern/<key>.svg        HD     (tools/modern_icons.py; charms drawn by hand) - loaded by the app as images
    icons/pixel/<key>.svg         Pixel  (tools/pixelart.mjs from icons/pixel-src/<key>.txt, the default style)

Usage:
    python tools/check_icons.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "items.json"
STYLES = {"HD": "modern", "Pixel": "pixel"}


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    keys = [f"i{it['id']}" for it in data["items"] + data.get("goods", [])] + [f"c{ch['id']}" for ch in data.get("charms", [])]
    keys += ["u-home", "u-projects", "u-bag", "u-settings", "u-gold", "u-wb"]   # interface icons (tools/ui_icons.py)
    failed = False
    for name, folder in STYLES.items():
        missing = [k for k in keys if not (ROOT / "icons" / folder / f"{k}.svg").exists()]
        print(f"{name:8} icons/{folder}/: {len(keys) - len(missing)}/{len(keys)}")
        if missing:
            failed = True
            print("  missing:", ", ".join(missing))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
