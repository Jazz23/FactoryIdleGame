class_name Planner
extends RefCounted
## Production-chain calculator: how many buildings of which recipes are needed to make
## an item at a target rate. Used by the in-game planner UI and the autoplay test bot.


## Best unlocked recipe that produces `item` (prefers the recipe sharing the item's id,
## then extraction with free slots, then the highest output per craft).
static func recipe_for(item: String, allow_locked := false) -> String:
	var best := ""
	var best_score := -INF
	for rid in Content.recipes_by_output.get(item, []):
		if not allow_locked and not Game.unlocked_recipes.has(rid):
			continue
		var r: Dictionary = Content.recipes[rid]
		if r.get("inputs", {}).has(item):
			continue  # self-consuming (enrichment loops) - not a primary source
		if best_building(rid) == "":
			continue
		var score := 0.0
		if rid == item:
			score += 100.0
		if r.has("deposit"):
			score += 50.0 if Game.deposit_slots(r.deposit) > Game.deposit_used(r.deposit) else -200.0
		score += float(r.outputs.get(item, 1)) / maxf(0.1, float(r.get("time", 1)))
		score -= float(r.get("inputs", {}).size()) * 0.5
		if score > best_score:
			best_score = score
			best = rid
	return best


## Fastest unlocked building able to run the recipe (or any building if none unlocked yet).
static func best_building(rid: String) -> String:
	var best := ""
	var best_speed := -1.0
	for bid in Content.buildings_for_recipe(rid):
		if not building_available(bid):
			continue
		var sp := float(Content.buildings[bid].get("speed", 1.0))
		if sp > best_speed:
			best_speed = sp
			best = bid
	return best


static func building_available(bid: String) -> bool:
	if Game.inv.get(bid, 0.0) >= 1.0:
		return true
	for l in Game.lines:
		if l.building == bid and l.count > 0:
			return true
	for rid in Content.recipes_by_output.get(bid, []):
		if Game.unlocked_recipes.has(rid):
			return true
	return false


static func crafts_per_building(rid: String, bid: String) -> float:
	var r: Dictionary = Content.recipes[rid]
	var b: Dictionary = Content.buildings[bid]
	var speed := float(b.get("speed", 1.0)) * (1.0 + Game.speed_bonus(r.category) + float(Game.support.get("speed", 0.0)))
	return maxf(speed, 0.05) / maxf(0.01, float(r.get("time", 1.0)))


static func output_per_craft(rid: String, item: String) -> float:
	var r: Dictionary = Content.recipes[rid]
	var prod := 1.0
	if r.has("deposit"):
		prod += float(Game.bonuses.get("mining_productivity", 0.0))
	return (float(r.outputs.get(item, 0.0)) - float(r.get("inputs", {}).get(item, 0.0))) * prod


## Returns {recipe_id: crafts_per_sec} needed to produce `rate` items/s of `item` (recursive).
static func plan(item: String, rate: float, acc: Dictionary = {}, depth := 0, stack: Dictionary = {}) -> Dictionary:
	if rate <= 0.0 or depth > 24 or stack.has(item):
		return acc
	var rid := recipe_for(item)
	if rid == "":
		acc["__missing__" + item] = float(acc.get("__missing__" + item, 0.0)) + rate
		return acc
	var per := output_per_craft(rid, item)
	if per <= 0.0:
		return acc
	var crafts := rate / per
	acc[rid] = float(acc.get(rid, 0.0)) + crafts
	stack[item] = true
	var r: Dictionary = Content.recipes[rid]
	for it in r.get("inputs", {}):
		if r.outputs.has(it):
			continue
		plan(it, float(r.inputs[it]) * crafts, acc, depth + 1, stack)
	stack.erase(item)
	return acc


## Converts a plan into [{recipe, building, count_needed, have, crafts}] rows.
static func rows(p: Dictionary) -> Array:
	var out: Array = []
	for rid in p:
		if str(rid).begins_with("__missing__"):
			out.append({"missing": str(rid).substr(11), "rate": p[rid]})
			continue
		var bid := best_building(rid)
		var per := crafts_per_building(rid, bid) if bid != "" else 0.0
		var need := int(ceil(float(p[rid]) / per - 1e-6)) if per > 0 else 0
		var have := 0
		for l in Game.lines:
			if l.recipe == rid:
				have += l.count
		out.append({"recipe": rid, "building": bid, "need": need, "have": have, "crafts": p[rid]})
	return out


## Brings every line in the plan up to the needed building count. Buys missing buildings with
## credits when not in storage. Returns number of buildings added.
static func apply(p: Dictionary, max_spend := INF) -> int:
	var added := 0
	var spent := 0.0
	for row in rows(p):
		if row.has("missing") or row.building == "":
			continue
		var deficit: int = row.need - row.have
		if deficit <= 0:
			continue
		var l: ProdLine = null
		for x in Game.lines:
			if x.recipe == row.recipe and x.building == row.building:
				l = x
				break
		if l == null:
			l = Game.add_line(row.building, row.recipe)
		if l == null:
			continue
		for i in deficit:
			var before := Game.credits
			if spent > max_spend:
				break
			if Game.line_add(l.uid, 1) == 0:
				break
			spent += before - Game.credits
			added += 1
	return added
