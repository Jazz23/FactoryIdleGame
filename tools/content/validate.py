"""Validation: references, schema values, coverage, consumption, scale minimums and a full
unlock-order reachability simulation. Errors go to C.errors, soft issues to C.warnings."""
import re
from collections import defaultdict

from common import (C, GROUPS, CATEGORIES, EXTRACTION_CATEGORIES, ITEM_ARCHETYPES, BUILDING_ARCHETYPES, MATERIALS,
                    ROLES, EFFECT_TYPES, AMMO_CLASSES, FUEL_CLASSES, GENERATOR_SOURCES, POWER_TARGETS, TECH_BRANCHES,
                    GATE_FOR_RESEARCH, BANNED_TERMS)

MINIMUMS = {"items": 230, "fluids": 16, "recipes": 220, "buildings": 100, "techs": 190, "repeatable techs": 8,
            "deposits": 12, "sectors": 16, "threats": 10, "contracts": 60, "achievements": 60, "megaprojects": 3,
            "orbital ark stages": 6, "modules": 20, "ammo items": 12, "raw resources": 12}

ACHIEVEMENT_TYPES = {"produce": "item", "build": "building", "research": "tech", "megaproject": "megaproject",
                     "research_count": None, "power": None, "credits": None, "sectors": None, "contracts": None,
                     "defense": None, "prestige": None}


def E(msg):
    C.errors.append(msg)


def W(msg):
    C.warnings.append(msg)


def check_visual(where, v, archetypes, building=False):
    if not isinstance(v, dict):
        E(f"{where}: visual missing")
        return
    if v.get("archetype") not in archetypes:
        E(f"{where}: visual archetype '{v.get('archetype')}' not in schema list")
    if v.get("material") not in MATERIALS:
        E(f"{where}: visual material '{v.get('material')}' not in schema list")
    col = v.get("color")
    if col is not None and (len(col) != 3 or any(not (0 <= c <= 1) for c in col)):
        E(f"{where}: visual color must be 3 floats in 0-1")
    params = v.get("params", {})
    if building:
        if params.get("tier") not in (1, 2, 3, 4):
            E(f"{where}: building visual params.tier must be 1-4")
        for k in ("paint", "accent", "glow"):
            if k in params and (len(params[k]) != 3 or any(not (0 <= c <= 1) for c in params[k])):
                E(f"{where}: building visual params.{k} must be 3 floats in 0-1")


def check_effect(where, e):
    t, tgt = e.get("type"), e.get("target")
    if t not in EFFECT_TYPES:
        E(f"{where}: unknown effect type '{t}'")
        return
    ok = {"craft_speed": tgt in CATEGORIES, "power_output": tgt is None or tgt in POWER_TARGETS,
          "defense": tgt is None or tgt in AMMO_CLASSES, "extraction_slots": tgt in ("solid", "fluid")}.get(t, tgt is None)
    if not ok:
        E(f"{where}: effect {t} has invalid target '{tgt}'")
    if not isinstance(e.get("value"), (int, float)) or e["value"] == 0:
        E(f"{where}: effect {t} needs a non-zero numeric value")


def unique_names(label, rows):
    seen = {}
    for r in rows:
        n = r["name"]
        if n in seen:
            E(f"{label}: duplicate name '{n}' ({seen[n]}, {r['id']})")
        seen[n] = r["id"]


def banned_scan():
    pats = [re.compile(r"\b" + re.escape(t) + r"s?\b", re.I) for t in BANNED_TERMS]

    def scan(where, text):
        for p in pats:
            if text and p.search(text):
                E(f"originality: {where} contains banned term '{p.pattern}'")

    for coll_name in ("items", "recipes", "buildings", "techs", "deposits", "sectors", "threats", "contracts",
                      "achievements", "megaprojects"):
        for oid, o in getattr(C, coll_name).items():
            scan(f"{coll_name}.{oid}", oid.replace("_", " "))
            scan(f"{coll_name}.{oid}", o.get("name", ""))
            scan(f"{coll_name}.{oid}", o.get("desc", ""))


def ancestors(tid, memo):
    if tid in memo:
        return memo[tid]
    memo[tid] = set()
    acc = set()
    for p in C.techs[tid]["prereqs"]:
        if p in C.techs:
            acc.add(p)
            acc |= ancestors(p, memo)
    memo[tid] = acc
    return acc


def validate():
    items, recipes, buildings, techs = C.items, C.recipes, C.buildings, C.techs

    # ---------------------------------------------------------------- names / originality
    unique_names("items", items.values())
    unique_names("recipes", recipes.values())
    unique_names("buildings", buildings.values())
    unique_names("techs", techs.values())
    world_rows = [r for coll in (C.deposits, C.sectors, C.threats, C.contracts, C.achievements, C.megaprojects)
                  for r in coll.values()]
    unique_names("world", world_rows)
    seen_world_ids = {}
    for coll_name in ("deposits", "sectors", "threats", "contracts", "achievements", "megaprojects"):
        for oid in getattr(C, coll_name):
            if oid in seen_world_ids and not (coll_name == "deposits" or seen_world_ids[oid] == "deposits"):
                E(f"world: id '{oid}' used in both {seen_world_ids[oid]} and {coll_name}")
            seen_world_ids.setdefault(oid, coll_name)
    banned_scan()

    # ---------------------------------------------------------------- items
    for iid, it in items.items():
        w = f"items.{iid}"
        if not re.fullmatch(r"[a-z][a-z0-9_]*", iid):
            E(f"{w}: id must be snake_case")
        if it["group"] not in GROUPS:
            E(f"{w}: group '{it['group']}' invalid")
        if it["kind"] not in ("solid", "fluid"):
            E(f"{w}: kind invalid")
        if it["kind"] == "fluid" and it["group"] != "fluids":
            E(f"{w}: fluids belong in group 'fluids'")
        if not (0 <= it["tier"] <= 7):
            E(f"{w}: tier out of range")
        if not it["desc"] or not it["name"]:
            E(f"{w}: needs name and desc")
        check_visual(w, it["visual"], ITEM_ARCHETYPES)
        if iid in buildings:
            if it["visual"]["archetype"] != "building_kit" or it["visual"].get("params", {}).get("building") != iid:
                E(f"{w}: building items use archetype building_kit with params.building = id")
        if "fuel_kj" in it and it.get("fuel_class") not in FUEL_CLASSES:
            E(f"{w}: fuel item needs a valid fuel_class")
        if "module" in it:
            m = it["module"]
            if set(m) != {"speed", "energy", "productivity", "pollution"}:
                E(f"{w}: module block needs speed/energy/productivity/pollution")
        if "ammo" in it:
            a = it["ammo"]
            if a.get("class") not in AMMO_CLASSES or not isinstance(a.get("mult"), (int, float)) or a["mult"] <= 0:
                E(f"{w}: ammo block needs a valid class and positive mult")

    # ---------------------------------------------------------------- recipes
    producers = defaultdict(list)
    for rid, r in recipes.items():
        w = f"recipes.{rid}"
        if r["category"] not in CATEGORIES:
            E(f"{w}: category '{r['category']}' invalid")
        if r["time"] <= 0:
            E(f"{w}: time must be > 0")
        if not r["outputs"]:
            E(f"{w}: needs at least one output")
        for side in ("inputs", "outputs"):
            for k, v in r[side].items():
                if k not in items:
                    E(f"{w}: {side} references unknown item '{k}'")
                if not isinstance(v, (int, float)) or v <= 0:
                    E(f"{w}: {side} amount for '{k}' must be > 0")
        if r["unlocked_by"] is not None and r["unlocked_by"] not in techs:
            E(f"{w}: unlocked_by unknown tech '{r['unlocked_by']}'")
        if r["category"] in EXTRACTION_CATEGORIES:
            dep = r.get("deposit")
            if dep is None or dep not in C.deposits:
                E(f"{w}: extraction recipe needs a known deposit")
            elif C.deposits[dep]["item"] not in r["outputs"]:
                E(f"{w}: deposit item must be an output")
        else:
            if "deposit" in r:
                E(f"{w}: only extraction recipes may name a deposit")
            if not r["inputs"]:
                E(f"{w}: non-extraction recipe needs inputs")
        for o in r["outputs"]:
            producers[o].append(rid)
    for iid in items:
        if not producers.get(iid):
            E(f"items.{iid}: no recipe produces it")
    for iid in C.base_values:
        if not any(recipes[r]["category"] in EXTRACTION_CATEGORIES for r in producers.get(iid, [])):
            E(f"items.{iid}: raw resource without an extraction recipe")

    # ---------------------------------------------------------------- buildings
    for bid, b in buildings.items():
        w = f"buildings.{bid}"
        if bid not in items:
            E(f"{w}: building is not an item")
        if b["role"] not in ROLES:
            E(f"{w}: role '{b['role']}' invalid")
        for c in b["categories"]:
            if c not in CATEGORIES:
                E(f"{w}: category '{c}' invalid")
        check_visual(w, b["visual"], BUILDING_ARCHETYPES, building=True)
        if any(not (1 <= s <= 6) for s in b["size"]) or len(b["size"]) != 2:
            E(f"{w}: size must be [w, d] with 1-6 tiles")
        if b["unlocked_by"] is not None and b["unlocked_by"] not in techs:
            E(f"{w}: unlocked_by unknown tech")
        own = recipes.get(bid)
        if own is None or own["outputs"] != {bid: 1}:
            E(f"{w}: needs a crafting recipe with the same id producing exactly 1")
        elif own["unlocked_by"] != b["unlocked_by"]:
            E(f"{w}: unlocked_by differs from its recipe's")
        if b["burner"] and (b["fuel_kw"] <= 0 or b["power_kw"] != 0):
            E(f"{w}: burner buildings need fuel_kw > 0 and power_kw 0")
        if not b["burner"] and b["fuel_kw"] != 0:
            E(f"{w}: fuel_kw only for burners")
        if b["role"] in ("producer", "research"):
            if not (0.5 <= b["speed"] <= 4):
                E(f"{w}: speed must be 0.5-4")
        if b["role"] == "producer" and not b["categories"]:
            E(f"{w}: producers need categories")
        if b["role"] != "producer" and b["categories"]:
            E(f"{w}: only producers have categories")
        if b["role"] == "generator":
            g = b.get("generator")
            if not g or b.get("power_out_kw", 0) <= 0:
                E(f"{w}: generators need generator block and power_out_kw")
            elif "fluid" in g:
                if items.get(g["fluid"], {}).get("kind") != "fluid" or g.get("rate", 0) <= 0:
                    E(f"{w}: generator fluid must be a fluid item with rate > 0")
            elif "fuel_class" in g:
                if g["fuel_class"] not in FUEL_CLASSES or g.get("fuel_kw", 0) <= 0:
                    E(f"{w}: generator fuel_class/fuel_kw invalid")
            elif g.get("source") in GENERATOR_SOURCES:
                if g["source"] == "accumulator" and b.get("capacity_kj", 0) <= 0:
                    E(f"{w}: accumulators need capacity_kj")
            else:
                E(f"{w}: generator block invalid")
        if b["role"] == "storage" and (b.get("storage_slots", 0) <= 0 or b.get("storage_kind") not in ("solid", "fluid")):
            E(f"{w}: storage needs storage_slots and storage_kind")
        if b["role"] == "logistics" and not (b.get("throughput") or b.get("fluid_throughput")):
            E(f"{w}: logistics needs throughput or fluid_throughput")
        if b["role"] == "defense":
            if b.get("defense", 0) <= 0 or "ammo" not in b or "ammo_per_min" not in b:
                E(f"{w}: defense needs defense, ammo, ammo_per_min")
            elif b["ammo"] is not None and (b["ammo"] not in AMMO_CLASSES or b["ammo_per_min"] <= 0):
                E(f"{w}: ammo class invalid or ammo_per_min <= 0")
        if b["role"] == "support" and not b.get("support") and b["pollution"] >= 0:
            E(f"{w}: support buildings need a support block or negative pollution")
        if b["module_slots"] < 0 or b["module_slots"] > 4:
            E(f"{w}: module_slots must be 0-4")

    # ---------------------------------------------------------------- category coverage
    used = {r["category"] for r in recipes.values()}
    served = {c for b in buildings.values() for c in b["categories"]}
    for c in sorted(used - served):
        E(f"categories: '{c}' used by recipes but no building runs it")
    for c in sorted(served - used):
        E(f"categories: '{c}' run by buildings but no recipe uses it")

    # ---------------------------------------------------------------- techs
    for tid, t in techs.items():
        w = f"techs.{tid}"
        if t["branch"] not in TECH_BRANCHES:
            E(f"{w}: branch '{t['branch']}' invalid")
        for p in t["prereqs"]:
            if p not in techs:
                E(f"{w}: unknown prereq '{p}'")
            elif techs[p]["tier"] > t["tier"]:
                E(f"{w}: tier {t['tier']} below prereq {p} tier {techs[p]['tier']}")
        if not t["cost"]:
            E(f"{w}: empty cost")
        for k, v in t["cost"].items():
            if items.get(k, {}).get("group") != "research":
                E(f"{w}: cost item '{k}' is not a research item")
            elif items[k]["tier"] > max(1, t["tier"]):
                E(f"{w}: cost item '{k}' (tier {items[k]['tier']}) above tech tier {t['tier']}")
            if v <= 0:
                E(f"{w}: cost amounts must be > 0")
        if t["units"] <= 0 or t["time"] <= 0:
            E(f"{w}: units and time must be > 0")
        for u in t["unlocks"]:
            if u not in recipes:
                E(f"{w}: unlocks unknown recipe '{u}'")
        for e in t["effects"]:
            check_effect(w, e)
        if not t["unlocks"] and not t["effects"]:
            E(f"{w}: tech unlocks nothing and has no effect")
    # acyclic
    state = {}

    def visit(tid, path):
        if state.get(tid) == 1:
            E(f"techs: prerequisite cycle {' -> '.join(path + [tid])}")
            return
        if state.get(tid) == 2:
            return
        state[tid] = 1
        for p in techs[tid]["prereqs"]:
            if p in techs:
                visit(p, path + [tid])
        state[tid] = 2

    for tid in techs:
        visit(tid, [])
    if not any(e.startswith("techs: prerequisite cycle") for e in C.errors):
        memo = {}
        for tid, t in techs.items():
            anc = ancestors(tid, memo)
            for k in t["cost"]:
                gate = GATE_FOR_RESEARCH.get(k)
                if gate and gate not in anc:
                    E(f"techs.{tid}: costs '{k}' but does not require its gate tech '{gate}'")

    # ---------------------------------------------------------------- world references
    for did, d in C.deposits.items():
        if d["item"] not in items:
            E(f"deposits.{did}: unknown item")
        elif items[d["item"]]["kind"] != d["kind"]:
            E(f"deposits.{did}: kind mismatch")
        check_visual(f"deposits.{did}", d["visual"], ITEM_ARCHETYPES)
    for raw_id in C.base_values:
        if raw_id not in C.deposits:
            E(f"items.{raw_id}: raw resource without a deposit")
    for sid, s in C.sectors.items():
        for k in s["claim_cost"]:
            if k not in items:
                E(f"sectors.{sid}: claim cost unknown item '{k}'")
        for k, v in s["deposits"].items():
            if k not in C.deposits or v <= 0:
                E(f"sectors.{sid}: bad deposit '{k}'")
        for h in s["hazards"]:
            if h not in C.threats:
                E(f"sectors.{sid}: unknown hazard '{h}'")
    for cid, c in C.contracts.items():
        for k in list(c["requires"]) + list(c["reward_items"]):
            if k not in items:
                E(f"contracts.{cid}: unknown item '{k}'")
    for aid, a in C.achievements.items():
        cond = a["condition"]
        kind = ACHIEVEMENT_TYPES.get(cond["type"], "bad")
        coll = {"item": items, "building": buildings, "tech": techs, "megaproject": C.megaprojects}.get(kind)
        if kind == "bad":
            E(f"achievements.{aid}: unknown condition type '{cond['type']}'")
        elif kind is None and cond["target"] is not None:
            E(f"achievements.{aid}: condition target must be null")
        elif coll is not None and cond["target"] not in coll:
            E(f"achievements.{aid}: unknown target '{cond['target']}'")
        elif kind == "megaproject" and cond["value"] > len(C.megaprojects[cond["target"]]["stages"]):
            E(f"achievements.{aid}: more stages than the megaproject has")
    for mid, mp in C.megaprojects.items():
        if mp["requires_building"] and mp["requires_building"] not in buildings:
            E(f"megaprojects.{mid}: unknown building")
        for st in mp["stages"]:
            for k in st["requires"]:
                if k not in items:
                    E(f"megaprojects.{mid}: stage '{st['name']}' unknown item '{k}'")
        for e in mp["reward"].get("effects", []):
            check_effect(f"megaprojects.{mid}", e)
    st = C.start
    for k in st["items"]:
        if k not in items:
            E(f"start: unknown item '{k}'")
    for k in st["buildings"]:
        if k not in buildings:
            E(f"start: unknown building '{k}'")
    for k in st["sectors"]:
        if k not in C.sectors:
            E(f"start: unknown sector '{k}'")

    # ---------------------------------------------------------------- consumption
    consumed = set()
    for r in recipes.values():
        consumed |= set(r["inputs"])
    consumed |= set(buildings)
    ammo_classes_used = {b["ammo"] for b in buildings.values() if b.get("ammo")}
    burner_exists = any(b["burner"] for b in buildings.values()) or any(
        b.get("generator", {}).get("fuel_class") == "chemical" for b in buildings.values())
    for iid, it in items.items():
        if "module" in it:
            consumed.add(iid)
        if "ammo" in it:
            if it["ammo"]["class"] in ammo_classes_used:
                consumed.add(iid)
            else:
                E(f"items.{iid}: no defense building fires ammo class '{it['ammo']['class']}'")
        if it.get("fuel_class") == "chemical" and burner_exists:
            consumed.add(iid)
    for t in techs.values():
        consumed |= set(t["cost"])
    for b in buildings.values():
        g = b.get("generator") or {}
        if "fluid" in g:
            consumed.add(g["fluid"])
    real = set(consumed)
    for s in C.sectors.values():
        consumed |= set(s["claim_cost"])
    for mp in C.megaprojects.values():
        for stg in mp["stages"]:
            consumed |= set(stg["requires"])
            real |= set(stg["requires"])
    for c in C.contracts.values():
        consumed |= set(c["requires"])
    for iid in items:
        if iid not in consumed and iid not in C.final_items:
            E(f"items.{iid}: never consumed (no recipe, building, fuel, ammo, module, research, claim, contract or megaproject use)")
        elif iid not in real and iid not in C.final_items:
            W(f"items.{iid}: only consumed by claims/contracts")

    # ---------------------------------------------------------------- reachability
    reachability(producers)

    # ---------------------------------------------------------------- scale minimums
    counts = scale_counts()
    for k, need in MINIMUMS.items():
        if counts[k] < need:
            E(f"scale: {k} = {counts[k]} < required {need}")


def scale_counts():
    items = C.items
    ark = C.megaprojects.get("orbital_ark")
    return {
        "items": len(items), "fluids": sum(1 for i in items.values() if i["kind"] == "fluid"),
        "recipes": len(C.recipes), "buildings": len(C.buildings), "techs": len(C.techs),
        "repeatable techs": sum(1 for t in C.techs.values() if t["repeatable"]), "deposits": len(C.deposits),
        "sectors": len(C.sectors), "threats": len(C.threats), "contracts": len(C.contracts),
        "achievements": len(C.achievements), "megaprojects": len(C.megaprojects),
        "orbital ark stages": len(ark["stages"]) if ark else 0,
        "modules": sum(1 for i in items.values() if "module" in i),
        "ammo items": sum(1 for i in items.values() if "ammo" in i),
        "raw resources": len(C.base_values),
    }


def reachability(producers):
    items, recipes, buildings, techs = C.items, C.recipes, C.buildings, C.techs
    start = C.start
    producible = set()
    reach_tier = {}
    recipe_tier = {}
    unlocked = {rid for rid, r in recipes.items() if r["unlocked_by"] is None}
    usable = set()
    done = set()
    claimed = list(start["sectors"])
    deposits = {d for s in claimed for d in C.sectors[s]["deposits"]}
    sectors_in_order = sorted(C.sectors.values(), key=lambda s: s["order"])
    start_buildings = set(start["buildings"])
    tier_now = 0
    tech_order = []

    def available(bid):
        return bid in producible or bid in start_buildings

    def power_ok():
        for b in buildings.values():
            if b["role"] != "generator" or not available(b["id"]):
                continue
            g = b["generator"]
            if g.get("source") in ("solar", "wind", "geothermal", "tidal"):
                return True
            if "fluid" in g and g["fluid"] in producible:
                return True
            if g.get("fuel_class") == "chemical" and chem_fuel():
                return True
        return False

    def chem_fuel():
        # starting stock seeds the bootstrap (burner drills mining their own coal)
        return any((i in producible or i in start["items"]) for i, it in items.items()
                   if it.get("fuel_class") == "chemical")

    def can_run(b, pw):
        if b["burner"]:
            return chem_fuel()
        if b["power_kw"] > 0:
            return pw
        return True

    def defense_ok(need):
        if need <= 0:
            return True
        for b in buildings.values():
            if b["role"] == "defense" and available(b["id"]):
                if b["ammo"] is None or any(it.get("ammo", {}).get("class") == b["ammo"] and i in producible
                                            for i, it in items.items()):
                    return True
        return False

    while True:
        changed = True
        while changed:
            changed = False
            pw = power_ok()
            cats = set()
            for b in buildings.values():
                if b["role"] == "producer" and available(b["id"]) and can_run(b, pw):
                    cats |= set(b["categories"])
            for rid in sorted(unlocked - usable):
                r = recipes[rid]
                if r["category"] not in cats:
                    continue
                if r.get("deposit") is not None and r["deposit"] not in deposits:
                    continue
                if not all(i in producible for i in r["inputs"]):
                    continue
                usable.add(rid)
                recipe_tier[rid] = tier_now
                for o in r["outputs"]:
                    if o not in producible:
                        producible.add(o)
                        reach_tier[o] = tier_now
                changed = True
            for s in sectors_in_order:
                if s["id"] in claimed:
                    continue
                if all(k in producible for k in s["claim_cost"]) and defense_ok(s["defense_required"]):
                    claimed.append(s["id"])
                    deposits |= set(s["deposits"])
                    changed = True
                break  # sectors unlock strictly in order
        pw = power_ok()
        lab_ok = any(b["role"] == "research" and available(b["id"]) and can_run(b, pw) for b in buildings.values())
        ready = [t for tid, t in techs.items() if tid not in done and lab_ok
                 and all(p in done for p in t["prereqs"]) and all(k in producible for k in t["cost"])]
        if not ready:
            break
        low = min(t["tier"] for t in ready)
        for t in ready:
            if t["tier"] == low:
                done.add(t["id"])
                tech_order.append(t["id"])
                unlocked |= set(t["unlocks"])
        tier_now = max(tier_now, low)

    bad_t = [t for t in techs if t not in done]
    bad_r = [r for r in recipes if r not in usable]
    bad_i = [i for i in items if i not in producible]

    def blocker(iid, depth=0, seen=None):
        """Follow the first blocked producer of an unproducible item back to a root cause."""
        seen = seen if seen is not None else set()
        if depth > 8 or iid in seen:
            return iid
        seen.add(iid)
        for rid in producers.get(iid, []):
            r = recipes[rid]
            if rid not in unlocked:
                return f"{iid} <- {rid} locked by '{r['unlocked_by']}'"
            if r.get("deposit") and r["deposit"] not in deposits:
                return f"{iid} <- {rid} needs unclaimed deposit '{r['deposit']}'"
            miss = [i for i in r["inputs"] if i not in producible]
            if miss:
                return f"{iid} <- {rid} <- " + blocker(miss[0], depth + 1, seen)
        return f"{iid} (no building/power to run its recipes)"

    if bad_t:
        E(f"reachability: {len(bad_t)} techs never researchable, e.g. {bad_t[:8]}")
        for tid in bad_t[:5]:
            t = techs[tid]
            miss_p = [p for p in t["prereqs"] if p not in done]
            miss_c = [k for k in t["cost"] if k not in producible]
            E(f"  {tid}: missing prereqs {miss_p} / unproducible cost {miss_c}")
            for k in miss_c[:1]:
                E(f"    root cause: {blocker(k)}")
    if bad_r:
        E(f"reachability: {len(bad_r)} recipes never usable, e.g. {bad_r[:8]}")
        for rid in bad_r[:6]:
            r = recipes[rid]
            why = []
            if rid not in unlocked:
                why.append(f"locked by {r['unlocked_by']}")
            miss = [i for i in r["inputs"] if i not in producible]
            if miss:
                why.append(f"inputs {miss}")
            if r.get("deposit") and r["deposit"] not in deposits:
                why.append(f"deposit {r['deposit']} not claimed")
            E(f"  {rid}: {', '.join(why) or 'no building can run it'}")
    if bad_i:
        E(f"reachability: {len(bad_i)} items never producible, e.g. {bad_i[:10]}")
    unclaimed = [s["id"] for s in sectors_in_order if s["id"] not in claimed]
    if unclaimed:
        E(f"reachability: sectors never claimable: {unclaimed}")

    # soft tier consistency checks
    for iid, it in items.items():
        rt = reach_tier.get(iid)
        if rt is None:
            continue
        if not (rt <= it["tier"] <= rt + 1):
            W(f"tier: item '{iid}' declared tier {it['tier']} but reachable at research tier {rt}")
    for rid, r in recipes.items():
        ut = r["unlocked_by"]
        if ut and rid in recipe_tier and recipe_tier[rid] > techs[ut]["tier"]:
            W(f"tier: recipe '{rid}' unlocked by tier-{techs[ut]['tier']} tech but only usable at tier {recipe_tier[rid]}")
    C.tech_order = tech_order
    C.reach_tier = reach_tier
