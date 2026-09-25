#!/usr/bin/env python3
"""Draw PORE's NPC portraits as HD drawings -> icons/modern/n-<name>.svg

Each NPC is our own drawing in the v2 skin kit's style (tools/skin_game.py: a big head filling the frame),
described from the character's look on the wiki. No artwork from the game or the wiki is used or stored.
tools/pixelart.mjs turns them into pixel icons like every other icon.

Usage: python tools/npc_icons.py
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from modern_icons import Icon  # noqa: E402
from skin_game import portrait  # noqa: E402
from skin_icons import _x  # noqa: E402   ('name:#colour' switches an extra on and sets its colour)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "modern"

# name: (style, hair or hat colour, skin, outfit, extras, eye colour, weapon)
NPCS = {
    "Merchant": ("hat", "#e6cf98", "light", "#b0885a", (), "#6a3a2a", None),              # a girl in a wide straw hat
    "Tsogy": ("wizard", "#9a96e8", "pale", "#6a64c8", ("beard:#f4f2ee",), "#3a6ad8", "staff"),   # the storm bearer: pointed hat, white beard
    "Jack": ("hood", "#2a2834", "pale", "#2a2834", ("mouthmask:#3a3846",), "#5a5e6e", "sword"),   # the silent ninja
    "Gul": ("round", "#4a8a2a", "#7ccf4a", "#7a5a3a", (), "#c83a2a", "staff"),         # a green orc with a staff
    "Ray": ("short", "#a4acb8", "light", "#5a4a3a", ("beard:#dcdcd8",), "#3aa86a", None),   # the blacksmith: grey hair and beard
    "Cheno": ("bear", "#e8f0fa", "#eef4fc", "#9ab4d8", (), "#2a3a6a", None),            # a white yeti
    "Firnen": ("round", "#6a8a2a", "#8ab43a", "#8a6a3a", ("band:#e8c060",), "#1a1a12", None),   # a green frog-like fablefolk
    "Vase": ("long", "#3a9a4a", "light", "#4a8a3a", ("flower:#8ad04a",), "#4a2a1a", None),   # the gaia princess: green hair, a leaf
    "Jin": ("bear", "#6a4a3a", "#7a5a44", "#3a4a3a", ("flower:#6ab83a",), "#1a1210", None),   # a brown animalian with a leaf
    "Olav": ("round", "#4a6a2a", "#6a9a3a", "#6a2a2a", ("band:#8a3a2a",), "#1a1a10", None),   # a big green orc with tusks
    "Mudder": ("blob", "#7a6a54", "#9c8a70", "#6a5a48", (), "#2a1a0a", None),           # a lump of mud
    "Spiky": ("blob", "#2a7a2a", "#4aaa3a", "#2a6a2a", ("flower:#e2343e", "stitches"), "#12240e", None),   # a cactus with a red flower
    "Rocky": ("stone", "#b8b4ac", "#ccc8c0", "#8a8680", (), "#3a3a36", None),           # the mineral muncher: a stone golem
    "Scarab Dealer": ("hood_dark", "#6a7a2a", "pale", "#5a6a24", ("horns:#8a6a3a",), "#ffd23a", None),   # a hooded swamp dweller, yellow eyes
    "Hank Mudtusk": ("round", "#e88aa4", "#f2a2b8", "#8a5a4a", (), "#2a1a1a", None),   # a pink boar with tusks
}


def slug(name: str) -> str:
    return "n-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (style, hair, skin, outfit, extras, eye, weapon) in NPCS.items():
        ic = Icon()
        ic.add(portrait(ic, style, hair, skin, outfit, _x(*extras), eye, weapon))
        (OUT / f"{slug(name)}.svg").write_text(ic.svg().replace("<svg ", '<svg data-generated="npc_icons.py" ', 1), encoding="utf-8")
    print(f"npc icons: wrote {len(NPCS)}")


if __name__ == "__main__":
    main()
