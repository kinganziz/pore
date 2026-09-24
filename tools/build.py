#!/usr/bin/env python3
"""Build the single-file app: inject data/items.json into src/app.html -> index.html.

Usage:
    python tools/build.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "app.html"
SOLVER = ROOT / "src" / "solver.js"
DATA = ROOT / "data" / "items.json"
OUT = ROOT / "index.html"
DATA_PLACEHOLDER = "__ITEMS_JSON__"
SOLVER_PLACEHOLDER = "__SOLVER_JS__"


def main() -> None:
    template = SRC.read_text(encoding="utf-8")
    for placeholder in (DATA_PLACEHOLDER, SOLVER_PLACEHOLDER):
        if template.count(placeholder) != 1:
            raise SystemExit(f"expected exactly one {placeholder} in {SRC}")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    badges = ROOT / "data" / "badges.json"
    if badges.exists():  # precomputed cheapest-P10 costs (node tools/badges.mjs)
        data["badges"] = json.loads(badges.read_text(encoding="utf-8"))
    solver = SOLVER.read_text(encoding="utf-8")
    if "</script" in solver.lower():
        raise SystemExit("solver.js must not contain '</script'")
    # Compact JSON; "</" can never appear inside base64 so the inline script stays safe,
    # but escape it anyway for robustness.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace(DATA_PLACEHOLDER, blob).replace(SOLVER_PLACEHOLDER, solver)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB, {data['count']} items, data fetched {data['fetched']})")

    # Service worker: version = content hash of the built page so every deploy refreshes the shell cache.
    version = hashlib.sha1(html.encode("utf-8")).hexdigest()[:10]
    sw = (ROOT / "src" / "sw.js").read_text(encoding="utf-8").replace("__VERSION__", version)
    (ROOT / "sw.js").write_text(sw, encoding="utf-8")
    print(f"wrote sw.js (version {version})")


if __name__ == "__main__":
    main()
