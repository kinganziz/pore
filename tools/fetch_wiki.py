#!/usr/bin/env python3
"""Fetch equippable item and charm data (names, stats, factors) from the Pixel Odyssey wiki.

Artwork is NOT taken from the wiki: PORE uses its own drawings (icons/modern/, icons/pixel/).

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

# Everything else a player can own (food, potions, ores, drops, skins...).
GOODS_TYPES = [
    "POTION", "FOOD", "FRUIT", "MUSHROOM", "PLANT", "ORE", "INGOT", "MATERIAL", "MONSTER_DROP",
    "KEY", "VALUABLE", "RELIC", "RESOURCE", "EVENT", "BASIC", "SKIN",
]

# World boss weapons can only be refined up to this level.
BOSS_MAX_LEVEL = 5

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


def norm(name: str) -> str:
    """Link targets and item names differ in case and punctuation ("Jack O Lantern" = "Jack-o'-Lantern")."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def link(value) -> str | None:
    m = re.match(r"\s*\[\[([^\]|#]+)", str(value or ""))
    return m.group(1).strip() if m else None


def sources(index: dict, items: list, charms: list, goods: list, frontmatter_of) -> tuple[dict, dict]:
    """Where every item comes from and what it is used for, from the wiki's monster, location, encounter,
    ore node, chest, NPC shop, recipe, event and coliseum pages. Items are referred to by their app key
    (i<id>, charms c<id>); places by name.

    where[key] entries:  ["mob", monster, drop %, [locations]]   ["find", location, %]
                         ["enc", encounter, %, amount, [locations]]   ["mine", node, mining power, [locations]]
                         ["chest", chest, "common"|"rare"|"epic", key item]   ["shop", npc, gold, [locations]]
                         ["craft", [[item, amount], ...], needs unlock]   ["boss", world boss]   ["event"]   ["coliseum"]
                         ["diamonds"]   ["login"]   ["free"]  (skins)
    uses[key] entries:   ["craft", product, amount]   ["key", chest]
    """
    key_of = {}
    for it in items:
        key_of[norm(it["page"])] = key_of[norm(it["name"])] = "i%s" % it["id"]
    for c in charms:
        key_of[norm(c["page"])] = key_of[norm(c["name"])] = "c%s" % c["id"]
    for g in goods:
        key_of[norm(g["page"])] = key_of[norm(g["name"])] = "i%s" % g["id"]
    pages = {}   # normalised file name -> (folder, front matter)
    for path, meta in index.items():
        if path.endswith(".md") and "/" in path:
            folder, base = path.split("/")[0], path.rsplit("/", 1)[1][:-3]
            fm = (meta or {}).get("frontmatter") or {}
            if fm:
                pages.setdefault(norm(base), (folder, fm))
    title = lambda fm, fallback: (fm.get("name") or fallback).replace("_", " ")
    where, uses = {}, {}

    def add(k, e):
        if k and e not in where.setdefault(k, []):
            where[k].append(e)

    # which locations each monster, encounter, ore node and NPC turns up in (plus items found lying around)
    at = {}
    for path, meta in index.items():
        fm = (meta or {}).get("frontmatter") or {}
        if fm.get("fileClass") != "location":
            continue
        loc = fm.get("name")
        found = {}
        for d in fm.get("drops") or []:
            t = link(d.get("drop"))
            if not t:
                continue
            k = key_of.get(norm(t))
            if k:
                found[k] = found.get(k, 0) + (d.get("chance") or 0)
            elif norm(t) in pages:
                at.setdefault(norm(t), [])
                if loc not in at[norm(t)]:
                    at[norm(t)].append(loc)
        for k, ch in found.items():
            add(k, ["find", loc, round(ch, 2)])
    for nk, (folder, fm) in pages.items():
        cls = fm.get("fileClass")
        locs = at.get(nk, [])
        if cls == "monster":
            for d in fm.get("drops") or []:
                add(key_of.get(norm(link(d.get("item")))), ["mob", fm.get("name"), d.get("chance"), locs])
        elif cls == "encounter":
            for o in fm.get("options") or []:
                o = o.get("option") or {}
                drop = o.get("drop") or {}
                add(key_of.get(norm(link(drop.get("item_id")))), ["enc", title(fm, nk), o.get("chance"), drop.get("amount") or 1, locs])
        elif cls == "ore-node":
            add(key_of.get(norm(link(fm.get("ore")))), ["mine", fm.get("name"), int(fm.get("required-mining-power") or 0), locs])
        elif cls == "npc":
            for o in fm.get("obj_for_gold") or []:
                add(key_of.get(norm(link(o.get("obj")))), ["shop", fm.get("name"), o.get("price"), locs])
        elif cls == "chest":
            kk = key_of.get(norm(link(fm.get("key"))))
            for tier in ("common", "rare", "epic"):
                for d in fm.get(tier + "_drops") or []:
                    add(key_of.get(norm(link(d))), ["chest", fm.get("name"), tier, kk])
            if kk:
                uses.setdefault(kk, []).append(["key", fm.get("name")])
        elif cls == "world-boss":
            add(key_of.get(norm(link(fm.get("weapon")))), ["boss", fm.get("name")])
    # recipes (any item page) and what their ingredients are used for
    for path, meta in index.items():
        if not (path.startswith("Items/") and path.endswith(".md") and meta):
            continue
        fm = frontmatter_of(path, meta)
        k = key_of.get(norm(fm.get("name"))) or key_of.get(norm(path[6:-3]))
        rec = fm.get("recipe")
        if not k or not isinstance(rec, list):
            continue
        parts = []
        for r in rec:
            ik = key_of.get(norm(link(r.get("ingredient")))) if isinstance(r, dict) else None
            if ik:
                parts.append([ik, r.get("amount") or 1])
                uses.setdefault(ik, []).append(["craft", k, r.get("amount") or 1])
        if parts:
            add(k, ["craft", parts, 1 if fm.get("recipe_requires_unlock") else 0])
    # skins name their own source: bought with diamonds, a login reward or free
    for path, meta in index.items():
        if not (path.startswith("Items/") and path.endswith(".md") and meta):
            continue
        fm = frontmatter_of(path, meta)
        src = str(fm.get("source") or "").lower()
        if fm.get("type") == "SKIN" and src in ("diamonds", "login", "free"):
            add(key_of.get(norm(fm.get("name"))), [src])
    # the event and coliseum pages are plain lists of links
    for page, tag in (("Events.md", "event"), ("Coliseum.md", "coliseum")):
        for l in (index.get(page) or {}).get("links") or []:
            add(key_of.get(norm(l.get("link"))), [tag])
    return where, uses


def bosses_of(index):
    """The world bosses in the wiki's order: description, element and fight stats (their weapon is in `where`)."""
    num = lambda v: int(float(v)) if str(v).replace(".", "", 1).isdigit() else 0
    out = []
    for path, meta in index.items():
        fm = (meta or {}).get("frontmatter") or {}
        if fm.get("fileClass") != "world-boss" or not fm.get("name"):
            continue
        out.append({"name": fm["name"], "id": num(fm.get("id")), "desc": (fm.get("description") or "").strip(),
                    "element": str(fm.get("element") or "").strip(),
                    "hp": num(fm.get("hp")), "atk": num(fm.get("attack")), "def": num(fm.get("defense")),
                    "spd": num(fm.get("speed")), "luck": num(fm.get("luck")), "mana": num(fm.get("mana"))})
    out.sort(key=lambda b: (b["id"], b["name"]))
    return out


def monsters_of(index):
    """The monsters, weakest first by the wiki's power: description, element and fight stats (drops are in `where`)."""
    num = lambda v: int(float(v)) if str(v).replace(".", "", 1).isdigit() else 0
    out = []
    for path, meta in index.items():
        fm = (meta or {}).get("frontmatter") or {}
        if fm.get("fileClass") != "monster" or not fm.get("name"):
            continue
        desc = str(fm.get("description") or "").strip()
        out.append({"name": fm["name"], "id": num(fm.get("id")), "desc": "" if desc == "None" else desc,
                    "element": str(fm.get("element") or "").strip(), "power": num(fm.get("power")),
                    "hp": num(fm.get("hp")), "atk": num(fm.get("attack")), "def": num(fm.get("defense")),
                    "spd": num(fm.get("speed")), "luck": num(fm.get("luck")), "mana": num(fm.get("mana"))})
    out.sort(key=lambda m: (m["power"], m["name"]))
    return out


def encounters_of(index):
    """The encounters (things met while exploring) with their description; what they give is in `where`."""
    out = []
    for path, meta in index.items():
        fm = (meta or {}).get("frontmatter") or {}
        if fm.get("fileClass") != "encounter" or not fm.get("name"):
            continue
        desc = str(fm.get("description") or "").strip()
        out.append({"name": fm["name"], "desc": "" if desc == "None" else desc})
    out.sort(key=lambda e: e["name"])
    return out


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

    # World boss weapons: each boss page names its weapon ("weapon: [[Page]]"). They refine only up to P5.
    boss_of = {}
    for path, meta in index.items():
        fm = (meta or {}).get("frontmatter") or {}
        if fm.get("fileClass") != "world-boss":
            continue
        m = re.match(r"\[\[([^\]|]+)", str(fm.get("weapon") or ""))
        if m:
            boss_of[m.group(1).strip()] = fm.get("name")
    for it in items:
        if it["page"] in boss_of:
            it["boss"] = boss_of[it["page"]]
            it["maxLevel"] = BOSS_MAX_LEVEL
    missing = set(boss_of) - {it["page"] for it in items}
    if missing:
        print("boss weapons without an item page:", ", ".join(sorted(missing)))

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

    goods = []
    for path, meta in index.items():
        if not (path.startswith("Items/") and path.endswith(".md") and meta):
            continue
        fm = frontmatter_of(path, meta)
        if fm.get("type") not in GOODS_TYPES or fm.get("charm"):
            continue
        g = {"id": fm.get("id"), "name": fm["name"], "type": fm["type"], "desc": (fm.get("description") or "").strip(),
             "page": path[len("Items/"):-len(".md")]}
        sub = fm.get("slot")
        if sub and sub != fm["type"]:
            g["sub"] = sub
        if fm.get("rarity"):
            g["rarity"] = str(fm["rarity"]).lower()
        if isinstance(fm.get("stats"), dict):   # relics: percent bonuses on top of everything else
            pct = {k.replace(" PercentOnTop", ""): v for k, v in fm["stats"].items() if isinstance(v, (int, float)) and v}
            if pct:
                g["pct"] = pct
        goods.append(g)
    goods_order = {t: i for i, t in enumerate(GOODS_TYPES)}
    num = lambda name: int(re.sub(r"\D", "", name) or 0)   # Skin #2 before Skin #10
    goods.sort(key=lambda g: (goods_order[g["type"]], num(g["name"]) if g["type"] == "SKIN" else 0, g["name"].lower()))

    where, uses = sources(index, items, charms, goods, frontmatter_of)

    # the maps: every location with its description and the steps it takes to unlock, in game order
    places = []
    for path, meta in index.items():
        fm = (meta or {}).get("frontmatter") or {}
        if fm.get("fileClass") != "location" or not fm.get("name"):
            continue
        places.append({"name": fm["name"], "desc": (fm.get("description") or "").strip(), "steps": int(fm.get("required-steps") or 0), "kind": fm.get("bg-name") or fm.get("type") or ""})
    places.sort(key=lambda pl: (pl["steps"], pl["name"]))

    bosses = bosses_of(index)
    monsters = monsters_of(index)
    encounters = encounters_of(index)

    stat_names = sorted({name for it in items for name in it["stats"]})
    payload = {
        "source": WIKI_URL,
        "fetched": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(items),
        "statNames": stat_names,
        "items": items,
        "charms": charms,
        "goods": goods,
        "where": where,
        "uses": uses,
        "places": places,
        "bosses": bosses,
        "monsters": monsters,
        "encounters": encounters,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    by_type = {}
    for it in items:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    print(f"wrote {OUT_FILE.relative_to(ROOT)}: {len(items)} items, {len(goods)} other items, {OUT_FILE.stat().st_size // 1024} KB")
    print(f"sources for {len(where)} of {len(items) + len(charms) + len(goods)} items, uses for {len(uses)}")
    print("by type:", ", ".join(f"{k} {v}" for k, v in by_type.items()))
    if skipped:
        print("skipped (no usable stats):", ", ".join(str(s) for s in skipped))


if __name__ == "__main__":
    main()
