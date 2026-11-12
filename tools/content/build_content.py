#!/usr/bin/env python3
"""INDUSTRIUM content build: the single source of truth for all game data.

    python3 tools/content/build_content.py

Defines every item, recipe, building, tech and world entry (sibling modules in this folder),
derives item values, validates everything (references, coverage, consumption, reachability,
scale minimums, originality) and writes data/*.json plus docs/CONTENT_STATS.md.
Exits non-zero, writing nothing, if validation fails.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from common import C  # noqa: E402
import materials  # noqa: E402
import equipment  # noqa: E402
import buildings  # noqa: E402
import techs  # noqa: E402
import world  # noqa: E402
import values  # noqa: E402
import validate  # noqa: E402
import report  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")


def link_unlocks():
    for t in C.techs.values():
        t["unlocks"] = []
    for rid, r in C.recipes.items():
        t = C.techs.get(r["unlocked_by"])
        if t is not None:
            t["unlocks"].append(rid)
    for t in C.techs.values():
        t["unlocks"].sort()


def recipe_tier(r):
    return max((C.items[o]["tier"] for o in r["outputs"] if o in C.items), default=0)


def write_json(name, payload):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return path


def main():
    materials.define()
    equipment.define()
    buildings.define()
    techs.define()
    world.define()
    link_unlocks()
    values.derive_values()
    world.define_contracts()
    validate.validate()

    for w in C.warnings:
        print(f"warning: {w}")
    if C.errors:
        print(f"\nCONTENT BUILD FAILED with {len(C.errors)} error(s):", file=sys.stderr)
        for e in C.errors:
            print(f"  error: {e}", file=sys.stderr)
        return 1

    os.makedirs(DATA, exist_ok=True)
    items = sorted(C.items.values(), key=lambda i: (i["tier"], i["id"]))
    recipes = sorted(C.recipes.values(), key=lambda r: (recipe_tier(r), r["id"]))
    blds = sorted(C.buildings.values(), key=lambda b: (b["tier"], b["id"]))
    tchs = sorted(C.techs.values(), key=lambda t: (t["tier"], t["id"]))
    write_json("items.json", {"items": items})
    write_json("recipes.json", {"recipes": recipes})
    write_json("buildings.json", {"buildings": blds})
    write_json("techs.json", {"techs": tchs})
    write_json("world.json", {
        "settings": C.settings,
        "start": C.start,
        "deposits": list(C.deposits.values()),
        "sectors": sorted(C.sectors.values(), key=lambda s: s["order"]),
        "threats": list(C.threats.values()),
        "contracts": sorted(C.contracts.values(), key=lambda c: (c["tier"], c["id"])),
        "achievements": list(C.achievements.values()),
        "megaprojects": list(C.megaprojects.values()),
    })
    stats_md = report.render()
    with open(os.path.join(ROOT, "docs", "CONTENT_STATS.md"), "w", encoding="utf-8") as f:
        f.write(stats_md)
    report.print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
