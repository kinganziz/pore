#!/usr/bin/env python3
"""Fetch equippable item and charm data (names, stats, factors) from the Pixel Odyssey wiki.

Artwork is NOT taken from the wiki: PORE uses its own drawings (icons/modern/, icons/pixel-modern/, icons/pixel/).

The wiki (https://wiki.pixel-odyssey.app) is an Obsidian Publish site, which
exposes a JSON index of every vault file plus raw file access:

  cache:  https://publish-01.obsidian.md/cache/<site-id>
  files:  https://publish-01.obsidian.md/access/<site-id>/<vault path>

Every item page under Items/*.md carries YAML frontmatter with the item's
name, type, slot and stats. This script reads that index,
keeps the equippable items that have stats and writes data/items.json.

Usage:
    python tools/fetch_wiki.py            # refresh data/items.json
    python tools/fetch_wiki.py --offline  # rebuild from .cache/ without network
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

SITE_ID = "8523d41cd5cf5681eee8dd91245b5c2b"
PUBLISH = "https://publish-01.obsidian.md"
CACHE_URL = f"{PUBLISH}/cache/{SITE_ID}"
ACCESS_URL = f"{PUBLISH}/access/{SITE_ID}/"
WIKI_URL = "https://wiki.pixel-odyssey.app/"

# Item types that can be equipped and therefore refined.
EQUIP_TYPES = [
    "WEAPON", "HELMET", "CHEST", "LEGGEAR", "SHOES",
    "SHIELD", "RING", "AMULET", "NECKLACE", "TOOL",
]

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cache"
OUT_FILE = ROOT / "data" / "items.json"


def fetch(url: str, dest: pathlib.Path, offline: bool) -> bytes:
    if dest.exists() and (offline or dest.stat().st_size > 0):
        return dest.read_bytes()
    if offline:
        raise SystemExit(f"offline mode but {dest} is missing")
    req = urllib.request.Request(url, headers={"User-Agent": "PORE-fetch/2.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data


def parse_frontmatter(markdown: str) -> dict:
    """Minimal YAML front-matter parser for the wiki's item pages.

    Handles `key: value`, quoted scalars, inline JSON objects, one level of block mappings
    (used by `stats:`) and duplicate keys (a later non-empty value wins). Obsidian's own cache
    drops the front matter of a couple of pages that contain duplicate keys, so this fallback
    keeps those items (e.g. Air Emerald Ring, Lucky Egg) in the database.
    """
    match = re.match(r"^---\r?\n(.*?)\r?\n---", markdown, re.S)
    if not match:
        return {}
    fm: dict = {}
    current = None
    for raw in match.group(1).splitlines():
        if not raw.strip():
            continue
        if raw.startswith(("  ", "\t")) and current is not None:
            sub = raw.strip()
            if sub.startswith("- "):
                fm.setdefault(current, [])
                if not isinstance(fm[current], list):
                    fm[current] = []
                fm[current].append(sub[2:])
                continue
            if ":" in sub:
                k, v = sub.split(":", 1)
                if not isinstance(fm.get(current), dict):
                    fm[current] = {}
                fm[current][k.strip()] = _scalar(v.strip())
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        key, value = key.strip(), value.strip()
        current = key
        if value == "":
            if key not in fm:
                fm[key] = None
            continue
        parsed = _scalar(value)
        if parsed is not None and parsed != "" or key not in fm:
            fm[key] = parsed
    return fm


def _scalar(value: str):
    if value.startswith("{"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def main() -> None:
    offline = "--offline" in sys.argv
    CACHE_DIR.mkdir(exist_ok=True)

    cache_path = CACHE_DIR / "cache.json"
    if not offline and cache_path.exists():
        cache_path.unlink()  # always refresh the index when online
    index = json.loads(fetch(CACHE_URL, cache_path, offline).decode("utf-8"))

    def frontmatter_of(path: str, meta: dict) -> dict:
        fm = meta.get("frontmatter")
        if fm:
            return fm
        # Obsidian's cache has no front matter for this page: read the page itself.
        markdown = fetch(ACCESS_URL + urllib.parse.quote(path), CACHE_DIR / "pages" / path, offline).decode("utf-8")
        return parse_frontmatter(markdown)

    picked = []
    skipped = []
    for path, meta in index.items():
        if not (path.startswith("Items/") and path.endswith(".md") and meta):
            continue
        fm = frontmatter_of(path, meta)
        if fm.get("type") not in EQUIP_TYPES:
            continue
        stats = fm.get("stats")
        if not isinstance(stats, dict):
            continue
        clean = {}
        for name, value in stats.items():
            if name == "None" or not isinstance(value, (int, float)) or value <= 0:
                continue
            clean[name] = int(value)
        if not clean:
            skipped.append(fm.get("name"))
            continue
        picked.append((path, fm, clean))

    items = []
    for path, fm, clean in picked:
        items.append({
            "id": fm.get("id"),
            "name": fm["name"],
            "type": fm["type"],
            "slot": fm.get("slot"),
            "stats": clean,
            "affinity": fm.get("affinity") or None,
            "desc": (fm.get("description") or "").strip(),
            "page": path[len("Items/"):-len(".md")],
        })

    type_order = {t: i for i, t in enumerate(EQUIP_TYPES)}
    items.sort(key=lambda it: (type_order[it["type"]], it["name"].lower()))

    # Charms: any item page with a numeric "charm" factor (success-chance multipliers for refining).
    charms = []
    for path, meta in index.items():
        if not (path.startswith("Items/") and path.endswith(".md") and meta):
            continue
        fm = frontmatter_of(path, meta)
        factor = fm.get("charm")
        if not isinstance(factor, (int, float)) or factor <= 0:
            continue
        charms.append({
            "id": fm.get("id"),
            "name": fm["name"],
            "factor": int(factor),
            "desc": (fm.get("description") or "").strip(),
            "page": path[len("Items/"):-len(".md")],
        })
    charms.sort(key=lambda c: (c["factor"], c["name"]))

    stat_names = sorted({name for it in items for name in it["stats"]})
    payload = {
        "source": WIKI_URL,
        "fetched": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(items),
        "statNames": stat_names,
        "items": items,
        "charms": charms,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    by_type = {}
    for it in items:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    print(f"wrote {OUT_FILE.relative_to(ROOT)}: {len(items)} items, {OUT_FILE.stat().st_size // 1024} KB")
    print("by type:", ", ".join(f"{k} {v}" for k, v in by_type.items()))
    if skipped:
        print("skipped (no usable stats):", ", ".join(str(s) for s in skipped))


if __name__ == "__main__":
    main()
