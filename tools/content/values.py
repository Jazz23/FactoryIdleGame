"""Item value derivation.

value(crafted) = (sum(input value x amount) + recipe.time x 0.5¢ x 1.6^tier) x 1.2 / output amount,
using the cheapest producing recipe. Multi-output recipes split their cost by declared weights
(evenly per output otherwise). Items appearing on both sides of a recipe are netted out first.
A recipe may only set an item's value if none of its inputs depends on that item through the
currently chosen recipes, so recycling / breeding loops never feed back into their own price.
Only recipes unlocked at or below the item's own tier price it (late alternates do not deflate
early prices); if an item has no such recipe, any recipe may.
"""
from common import C, EXTRACTION_CATEGORIES, sig3

TIME_COST = 0.5
TIER_FACTOR = 1.6
MARKUP = 1.2


def net_io(r):
    ins, outs = dict(r["inputs"]), dict(r["outputs"])
    for k in set(ins) & set(outs):
        m = min(ins[k], outs[k])
        ins[k] -= m
        outs[k] -= m
    return {k: v for k, v in ins.items() if v > 0}, {k: v for k, v in outs.items() if v > 0}


def derive_values():
    items, recipes = C.items, C.recipes
    raw = dict(C.base_values)
    cands = []  # (rid, net_in, net_out, tier)
    for rid, r in recipes.items():
        if r["category"] in EXTRACTION_CATEGORIES:
            continue
        if any(i not in items for i in list(r["inputs"]) + list(r["outputs"])):
            continue  # reported by validation
        ins, outs = net_io(r)
        outs = {k: v for k, v in outs.items() if k not in raw}
        if not outs:
            continue
        tier = max(items[o]["tier"] for o in r["outputs"])
        cands.append((rid, ins, outs, tier))

    def share(rid, ins, outs, tier, o, vals):
        cost = (sum(vals[i] * a for i, a in ins.items()) + recipes[rid]["time"] * TIME_COST * TIER_FACTOR ** tier) * MARKUP
        w = C.recipe_weights.get(rid, {})
        weights = {k: float(w.get(k, 1.0)) for k in outs}
        return cost * weights[o] / sum(weights.values()) / outs[o]

    def unlock_tier(rid):
        t = C.techs.get(recipes[rid]["unlocked_by"])
        return t["tier"] if t else 0

    tier_ok = {}
    for rid, ins, outs, tier in cands:
        for o in outs:
            tier_ok.setdefault(o, set())
            if unlock_tier(rid) <= items[o]["tier"]:
                tier_ok[o].add(rid)

    def eligible(rid, o):
        return rid in tier_ok[o] or not tier_ok[o]

    by_id = {c[0]: c for c in cands}
    value = dict(raw)
    chosen = {}

    # Phase 1: discovery order — value each item from the first recipes whose inputs are all valued.
    while True:
        best = {}
        for rid, ins, outs, tier in cands:
            if not all(i in value for i in ins):
                continue
            for o in outs:
                if o in value or not eligible(rid, o):
                    continue
                v = share(rid, ins, outs, tier, o, value)
                if o not in best or v < best[o][0]:
                    best[o] = (v, rid)
        if not best:
            break
        for o, (v, rid) in best.items():
            value[o] = v
            chosen[o] = rid

    # Phase 2: switch to cheaper recipes when that does not create a dependency loop.
    def depends(start, target, memo):
        if start == target:
            return True
        if start in memo:
            return memo[start]
        memo[start] = False
        rid = chosen.get(start)
        res = False
        if rid is not None:
            res = any(depends(i, target, memo) for i in by_id[rid][1])
        memo[start] = res
        return res

    def recompute():
        vals = dict(raw)

        def val(x, stack=()):
            if x in vals:
                return vals[x]
            rid, ins, outs, tier = by_id[chosen[x]]
            for i in ins:
                val(i, stack + (x,))
            vals[x] = share(rid, ins, outs, tier, x, vals)
            return vals[x]

        for x in chosen:
            val(x)
        return vals

    for _ in range(60):
        changed = False
        for rid, ins, outs, tier in cands:
            if not all(i in value for i in ins):
                continue
            for o in outs:
                if chosen.get(o) == rid or not eligible(rid, o):
                    continue
                v = share(rid, ins, outs, tier, o, value)
                if v < value[o] * 0.999:
                    if any(depends(i, o, {}) for i in ins):
                        continue
                    chosen[o] = rid
                    value = recompute()
                    changed = True
        if not changed:
            break

    for iid, item in items.items():
        if iid in value:
            item["value"] = max(0.001, sig3(value[iid]))
        else:
            C.errors.append(f"values: no recipe chain gives item '{iid}' a value")
    C.chosen_recipe = chosen
    return chosen
