extends Node
## Game state + rate-based simulation + persistence. Autoload "Game".

signal notify(text: String, kind: String)        # kind: info, good, warn, bad, research, achievement
signal lines_changed                               # line added/removed/re-laid out
signal line_updated(uid: int)
signal research_changed
signal tech_completed(tech_id: String)
signal sectors_changed
signal state_reset
signal offline_report(report: Dictionary)
signal built(uid: int, n: int)
signal sold(item: String, credits: float)

const SAVE_PATH := "user://industrium_save.json"
const TICK := 0.1
const AUTOSAVE_SEC := 30.0
const BASE_SOLID_CAP := 400.0
const BASE_FLUID_CAP := 2000.0
const MARKET_BUY_MULT := 1.6
const OFFLINE_BASE_EFF := 0.6
const OFFLINE_BASE_CAP_H := 8.0
const DAY_LENGTH := 600.0
const CONTRACT_SLOTS := 3

# ------------------------------------------------------------------ state
var credits := 0.0
var inv: Dictionary = {}
var lines: Array = []                 # Array[ProdLine]
var next_uid := 1
var researched: Dictionary = {}       # tech id -> level (int)
var research_queue: Array = []
var research_progress := 0.0          # units completed of the current tech (fractional)
var unlocked_recipes: Dictionary = {}
var sectors_claimed: Dictionary = {}
var market_sat: Dictionary = {}
var overflow_sell: Dictionary = {}    # item -> true: auto-sell when storage full
var pollution := 0.0
var accum_kj := 0.0
var contracts_active: Array = []      # contract ids
var contracts_done := 0
var achievements_done: Dictionary = {}
var mega_progress: Dictionary = {}    # mega id -> {"stage": int, "delivered": {item: n}}
var megas_completed: Dictionary = {}
var legacy := 0.0
var prestige_count := 0
var stats_produced: Dictionary = {}   # lifetime
var stats_consumed: Dictionary = {}
var lifetime_credits := 0.0
var play_time := 0.0
var game_time := 0.0
var last_save_unix := 0.0
var game_speed := 1.0

# ------------------------------------------------------------------ derived / runtime
var bonuses: Dictionary = {}
var rates_prod: Dictionary = {}       # item -> units/sec (smoothed)
var rates_cons: Dictionary = {}
var _tick_prod: Dictionary = {}
var _tick_cons: Dictionary = {}
var power: Dictionary = {"demand": 0.0, "supply": 0.0, "capacity": 0.0, "sat": 1.0, "accum": 0.0, "accum_cap": 0.0, "by_source": {}}
var threat := 0.0
var defense := 0.0
var siege := 0.0
var unlocked_tier := 0
var credits_rate := 0.0
var _credits_acc := 0.0
var _acc := 0.0
var _autosave := 0.0
var _slow := 0.0
var _caps_dirty := true
var _caps: Dictionary = {}
var _storage_add := {"solid": 0.0, "fluid": 0.0}
var _wind := 0.7
const SUPPORT_COVER := 8.0
const SLOTS_PER_DEPOSIT := 5     # extractors per listed deposit slot
var support: Dictionary = {"speed": 0.0, "energy": 0.0, "power": 0.0}
var throughput: Dictionary = {"solid_cap": 6.0, "fluid_cap": 400.0, "solid_flow": 0.0, "fluid_flow": 0.0, "solid_sat": 1.0, "fluid_sat": 1.0}
var _flow_solid := 0.0
var _flow_fluid := 0.0
var started := false
var simulating_offline := false


func _ready() -> void:
	process_priority = -10
	if not Content.loaded:
		Content.load_all()
	if not load_game():
		new_game()
	started = true


func _process(delta: float) -> void:
	if not started:
		return
	_acc += delta * game_speed
	var steps := 0
	while _acc >= TICK and steps < 50:
		_acc -= TICK
		tick(TICK)
		steps += 1
	_autosave += delta
	if _autosave >= AUTOSAVE_SEC:
		_autosave = 0.0
		save_game()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED:
		if started:
			save_game()


func setting(key: String, default: float) -> float:
	return float(Content.world.get("settings", {}).get(key, default))


func day_length() -> float:
	return setting("day_length_s", DAY_LENGTH)


# ================================================================== setup
func new_game(keep_legacy := false) -> void:
	var leg := legacy
	var pc := prestige_count
	var ach := achievements_done.duplicate()
	credits = 0.0
	inv = {}
	lines = []
	next_uid = 1
	researched = {}
	research_queue = []
	research_progress = 0.0
	unlocked_recipes = {}
	sectors_claimed = {}
	market_sat = {}
	overflow_sell = {}
	pollution = 0.0
	accum_kj = 0.0
	contracts_active = []
	mega_progress = {}
	megas_completed = {}
	stats_produced = {}
	stats_consumed = {}
	play_time = 0.0
	game_time = day_length() * 0.3
	last_save_unix = Time.get_unix_time_from_system()
	if keep_legacy:
		legacy = leg
		prestige_count = pc
		achievements_done = ach
	else:
		legacy = 0.0
		prestige_count = 0
		achievements_done = {}
		contracts_done = 0
		lifetime_credits = 0.0
	for r in Content.recipe_list:
		if r.get("unlocked_by") == null:
			unlocked_recipes[r.id] = true
	var st: Dictionary = Content.start
	credits = float(st.get("credits", 500))
	for it in st.get("items", {}):
		inv[it] = float(st.items[it])
	for s in st.get("sectors", []):
		sectors_claimed[s] = true
	if sectors_claimed.is_empty() and not Content.sectors.is_empty():
		sectors_claimed[Content.sectors[0].id] = true
	_caps_dirty = true
	recompute_bonuses()
	if st.has("lines"):
		for ld in st.lines:
			var bid: String = ld.get("building", "")
			var rid: String = ld.get("recipe", "")
			var l: ProdLine = add_line(bid, rid, false)
			if l:
				l.count += int(ld.get("count", 1))
	else:
		for bid in st.get("buildings", {}):
			var n := int(st.buildings[bid])
			var rid := default_recipe_for(bid)
			var l := add_line(bid, rid, false)
			if l:
				l.count = n
	for bid in st.get("buildings_in_storage", {}):
		inv[bid] = float(st.buildings_in_storage[bid])
	_fill_contracts()
	emit_signal("state_reset")
	emit_signal("lines_changed")


func default_recipe_for(bid: String) -> String:
	var b: Dictionary = Content.buildings.get(bid, {})
	if b.get("role", "producer") != "producer":
		return ""
	var used := {}
	for l in lines:
		used[l.recipe] = true
	var cands: Array = []
	for rid in Content.recipes_for_building(bid):
		if unlocked_recipes.has(rid):
			var r: Dictionary = Content.recipes[rid]
			if r.has("deposit") and deposit_slots(r.deposit) <= 0:
				continue
			cands.append(rid)
	for rid in cands:
		if not used.has(rid):
			return rid
	return cands[0] if not cands.is_empty() else ""


# ================================================================== lines
func add_line(bid: String, rid: String, notify_change := true) -> ProdLine:
	var b: Dictionary = Content.buildings.get(bid, {})
	if b.is_empty():
		return null
	var l := ProdLine.new()
	l.uid = next_uid
	next_uid += 1
	l.building = bid
	l.recipe = rid
	if l.kind() != ProdLine.Kind.PRODUCER:
		l.recipe = ""
		var existing := facility_line(bid)
		if existing:
			return existing
	l.bay = _free_bay()
	lines.append(l)
	_caps_dirty = true
	if notify_change:
		emit_signal("lines_changed")
	return l


func facility_line(bid: String) -> ProdLine:
	for l in lines:
		if l.building == bid and l.recipe == "":
			return l
	return null


func remove_line(uid: int) -> void:
	var l := get_line(uid)
	if l == null:
		return
	add_item(l.building, l.count)
	for m in l.modules:
		add_item(m, l.count)
	lines.erase(l)
	_caps_dirty = true
	emit_signal("lines_changed")


func get_line(uid: int) -> ProdLine:
	for l in lines:
		if l.uid == uid:
			return l
	return null


func _free_bay() -> Vector2i:
	var used := {}
	for l in lines:
		used[l.bay] = true
	var i := 0
	while true:
		var p := Vector2i(i % 4, i / 4)
		if not used.has(p):
			return p
		i += 1
	return Vector2i.ZERO


func buy_price(item: String) -> float:
	return Content.item_value(item) * setting("market_buy_mult", MARKET_BUY_MULT) / market_mult()


func can_buy(item: String) -> bool:
	return int(Content.items.get(item, {}).get("tier", 0)) <= unlocked_tier


## Adds `n` buildings to a line, taking them from storage first, then buying the rest.
func line_add(uid: int, n: int = 1) -> int:
	var l := get_line(uid)
	if l == null:
		return 0
	var added := 0
	for i in n:
		if l.recipe != "" and Content.is_extraction(l.recipe):
			var dep: String = Content.recipes[l.recipe].deposit
			if deposit_used(dep) >= deposit_slots(dep):
				if added == 0:
					emit_signal("notify", "No free %s deposit slots — claim more sectors." % Content.deposits.get(dep, {}).get("name", dep), "warn")
				break
		if inv.get(l.building, 0.0) >= 1.0:
			inv[l.building] -= 1.0
		elif can_buy(l.building) and credits >= buy_price(l.building):
			credits -= buy_price(l.building)
		else:
			if added == 0:
				emit_signal("notify", "Need a %s (craft one or earn %s)." % [Content.item_name(l.building), Fmt.credits(buy_price(l.building))], "warn")
			break
		for m in l.modules:
			if not take_item(m, 1.0):
				if credits >= buy_price(m) and can_buy(m):
					credits -= buy_price(m)
				else:
					l.modules.erase(m)
					break
		l.count += 1
		added += 1
	if added > 0:
		_caps_dirty = true
		emit_signal("line_updated", uid)
		emit_signal("built", uid, added)
	return added


## Faster buildings that can run this line's recipe and are available to the player.
func upgrade_options(uid: int) -> Array:
	var l := get_line(uid)
	if l == null or l.recipe == "":
		return []
	var cur := float(l.spec().get("speed", 1.0))
	var out: Array = []
	for bid in Content.buildings_for_recipe(l.recipe):
		if bid == l.building or float(Content.buildings[bid].get("speed", 1.0)) <= cur:
			continue
		if inv.get(bid, 0.0) >= 1.0 or can_buy(bid) and _recipe_unlocked_for(bid):
			out.append(bid)
	out.sort_custom(func(a, b): return float(Content.buildings[a].get("speed", 1)) > float(Content.buildings[b].get("speed", 1)))
	return out


func _recipe_unlocked_for(bid: String) -> bool:
	for rid in Content.recipes_by_output.get(bid, []):
		if unlocked_recipes.has(rid):
			return true
	return false


## Replaces up to all buildings of a line with `new_bid` (old ones return to storage).
## Returns how many were upgraded.
func upgrade_line(uid: int, new_bid: String) -> int:
	var l := get_line(uid)
	if l == null or l.recipe == "" or not Content.buildings_for_recipe(l.recipe).has(new_bid):
		return 0
	var target: ProdLine = null
	for x in lines:
		if x != l and x.recipe == l.recipe and x.building == new_bid:
			target = x
			break
	var k := 0
	while k < l.count:
		if inv.get(new_bid, 0.0) >= 1.0:
			inv[new_bid] -= 1.0
		elif can_buy(new_bid) and credits >= buy_price(new_bid):
			credits -= buy_price(new_bid)
		else:
			break
		k += 1
	if k == 0:
		emit_signal("notify", "Need %s to upgrade." % Content.item_name(new_bid), "warn")
		return 0
	if k == l.count and target == null:
		add_item(l.building, k)
		l.building = new_bid
		var slots := module_slots(l)
		while l.modules.size() > slots:
			add_item(l.modules.pop_back(), k)
	else:
		if target == null:
			target = add_line(new_bid, l.recipe, false)
		l.count -= k
		add_item(l.building, k)
		target.count += k
		if l.count == 0:
			for m in l.modules:
				pass
			lines.erase(l)
	_caps_dirty = true
	emit_signal("lines_changed")
	emit_signal("notify", "Upgraded %d to %s." % [k, Content.item_name(new_bid)], "good")
	return k


func line_remove(uid: int, n: int = 1) -> void:
	var l := get_line(uid)
	if l == null:
		return
	var k := mini(n, l.count)
	l.count -= k
	add_item(l.building, k)
	for m in l.modules:
		add_item(m, k)
	_caps_dirty = true
	emit_signal("line_updated", uid)


func set_line_recipe(uid: int, rid: String) -> void:
	var l := get_line(uid)
	if l and unlocked_recipes.has(rid) and Content.buildings_for_recipe(rid).has(l.building):
		l.recipe = rid
		emit_signal("line_updated", uid)
		emit_signal("lines_changed")


func module_slots(l: ProdLine) -> int:
	var s := int(l.spec().get("module_slots", 0))
	if s > 0:
		s += int(bonuses.get("module_slots", 0))
	return s


func line_add_module(uid: int, mod: String) -> bool:
	var l := get_line(uid)
	if l == null or l.modules.size() >= module_slots(l):
		return false
	var need := maxf(1.0, float(l.count))
	if inv.get(mod, 0.0) < need:
		emit_signal("notify", "Need %d × %s (one per building)." % [int(need), Content.item_name(mod)], "warn")
		return false
	take_item(mod, need)
	l.modules.append(mod)
	emit_signal("line_updated", uid)
	return true


func line_remove_module(uid: int, idx: int) -> void:
	var l := get_line(uid)
	if l == null or idx < 0 or idx >= l.modules.size():
		return
	add_item(l.modules[idx], l.count)
	l.modules.remove_at(idx)
	emit_signal("line_updated", uid)


# ================================================================== inventory
func cap(item: String) -> float:
	if _caps_dirty:
		_recompute_storage()
	if _caps.has(item):
		return _caps[item]
	var fluid := Content.is_fluid(item)
	var base := setting("base_cap_fluid", BASE_FLUID_CAP) if fluid else setting("base_cap_solid", BASE_SOLID_CAP)
	var add: float = _storage_add["fluid" if fluid else "solid"]
	var c := (base + add) * (1.0 + float(bonuses.get("storage_capacity", 0.0)))
	# buildings and research items get generous caps so they never block
	var it: Dictionary = Content.items.get(item, {})
	if Content.buildings.has(item) or it.has("module"):
		c = maxf(c, 1000.0)
	_caps[item] = c
	return c


func _recompute_storage() -> void:
	_caps.clear()
	_storage_add = {"solid": 0.0, "fluid": 0.0}
	for l in lines:
		var b: Dictionary = l.spec()
		if b.get("role", "") == "storage" and l.count > 0:
			var kind := _storage_kind(b)
			_storage_add[kind] += float(b.get("storage_slots", 0)) * l.count
	_caps_dirty = false


func _storage_kind(b: Dictionary) -> String:
	if b.has("storage_kind"):
		return b.storage_kind
	var arch: String = b.get("visual", {}).get("archetype", "")
	return "fluid" if arch in ["storage_tank"] else "solid"


func add_item(item: String, n: float) -> void:
	inv[item] = inv.get(item, 0.0) + n


func take_item(item: String, n: float) -> bool:
	if inv.get(item, 0.0) + 1e-6 < n:
		return false
	inv[item] = maxf(0.0, inv.get(item, 0.0) - n)
	return true


func has_items(req: Dictionary, mult := 1.0) -> bool:
	for k in req:
		if inv.get(k, 0.0) + 1e-6 < float(req[k]) * mult:
			return false
	return true


func take_items(req: Dictionary, mult := 1.0) -> bool:
	if not has_items(req, mult):
		return false
	for k in req:
		inv[k] = maxf(0.0, inv.get(k, 0.0) - float(req[k]) * mult)
		_count_cons(k, float(req[k]) * mult)
	return true


func _count_prod(item: String, n: float) -> void:
	_tick_prod[item] = _tick_prod.get(item, 0.0) + n
	stats_produced[item] = stats_produced.get(item, 0.0) + n


func _count_cons(item: String, n: float) -> void:
	_tick_cons[item] = _tick_cons.get(item, 0.0) + n
	stats_consumed[item] = stats_consumed.get(item, 0.0) + n


# ================================================================== bonuses
func recompute_bonuses() -> void:
	var b := {"craft_speed": {}, "mining_productivity": 0.0, "lab_speed": 0.0, "lab_productivity": 0.0,
		"power_output": {}, "storage_capacity": 0.0, "market_price": 0.0, "defense": {},
		"pollution_reduction": 0.0, "offline_efficiency": 0.0, "module_slots": 0, "extraction_slots": {},
		"global_speed": legacy * 0.02}
	var tier := 0
	var sources: Array = []
	for tid in researched:
		var t: Dictionary = Content.techs.get(tid, {})
		tier = maxi(tier, int(t.get("tier", 0)))
		sources.append([t.get("effects", []), int(researched[tid])])
	for m in Content.megaprojects:
		if megas_completed.has(m.id):
			var rw = m.get("reward", {})
			if rw is Dictionary:
				sources.append([rw.get("effects", []), 1])
	for src in sources:
		var lvl: int = src[1]
		for e in src[0]:
			var v := float(e.get("value", 0.0)) * lvl
			var typ: String = e.get("type", "")
			var target = e.get("target")
			match typ:
				"craft_speed", "power_output", "defense", "extraction_slots":
					var key: String = str(target) if target != null else "*"
					b[typ][key] = b[typ].get(key, 0.0) + v
				"module_slots":
					b.module_slots += int(v)
				_:
					if b.has(typ) and typeof(b[typ]) == TYPE_FLOAT:
						b[typ] += v
	bonuses = b
	unlocked_tier = maxi(tier, 1)
	_caps_dirty = true


func speed_bonus(category: String) -> float:
	var cs: Dictionary = bonuses.get("craft_speed", {})
	return float(cs.get(category, 0.0)) + float(cs.get("*", 0.0)) + float(bonuses.get("global_speed", 0.0))


func market_mult() -> float:
	return 1.0 + float(bonuses.get("market_price", 0.0)) + legacy * 0.05


# ================================================================== deposits / sectors
func deposit_slots(dep: String) -> int:
	var total := 0.0
	var kind: String = Content.deposits.get(dep, {}).get("kind", "solid")
	var es: Dictionary = bonuses.get("extraction_slots", {})
	var extra := float(es.get(kind, 0.0)) + float(es.get("*", 0.0))
	for s in Content.sectors:
		if not sectors_claimed.has(s.id):
			continue
		var n := float(s.get("deposits", {}).get(dep, 0))
		if n <= 0:
			continue
		n += extra
		if not _is_start_sector(s.id):
			n *= (1.0 - siege)
		total += n
	return int(floor(total * SLOTS_PER_DEPOSIT + 1e-6))


func _is_start_sector(sid: String) -> bool:
	var st: Array = Content.start.get("sectors", [])
	if not st.is_empty():
		return st.has(sid)
	return not Content.sectors.is_empty() and Content.sectors[0].id == sid


func deposit_used(dep: String) -> int:
	var n := 0
	for l in lines:
		if l.recipe != "" and Content.recipes.get(l.recipe, {}).get("deposit", "") == dep:
			n += l.count
	return n


func can_claim(sid: String) -> String:
	var s: Dictionary = Content.sector_by_id.get(sid, {})
	if s.is_empty() or sectors_claimed.has(sid):
		return "Already claimed"
	var idx := Content.sectors.find(s)
	if idx > 0 and not sectors_claimed.has(Content.sectors[idx - 1].id):
		return "Claim the previous sector first"
	if defense < float(s.get("defense_required", 0)):
		return "Needs defense %s (have %s)" % [Fmt.num(float(s.get("defense_required", 0))), Fmt.num(defense)]
	if not has_items(s.get("claim_cost", {})):
		return "Missing claim materials"
	return ""


func claim_sector(sid: String) -> bool:
	if can_claim(sid) != "":
		return false
	var s: Dictionary = Content.sector_by_id[sid]
	take_items(s.get("claim_cost", {}))
	sectors_claimed[sid] = true
	emit_signal("notify", "Sector claimed: " + s.get("name", sid), "good")
	emit_signal("sectors_changed")
	return true


# ================================================================== research
func tech_level(tid: String) -> int:
	return int(researched.get(tid, 0))


func tech_done(tid: String) -> bool:
	var t: Dictionary = Content.techs.get(tid, {})
	return researched.has(tid) and not t.get("repeatable", false)


func tech_available(tid: String) -> bool:
	if tech_done(tid):
		return false
	for p in Content.techs.get(tid, {}).get("prereqs", []):
		if not researched.has(p):
			return false
	return true


func tech_units(tid: String) -> float:
	var t: Dictionary = Content.techs.get(tid, {})
	var u := float(t.get("units", 1))
	if t.get("repeatable", false):
		u *= pow(setting("repeatable_cost_mult", 1.5), tech_level(tid))
	return u


func queue_research(tid: String, front := false) -> void:
	if not tech_available(tid):
		# queue missing prereqs first
		var chain := _prereq_chain(tid)
		for p in chain:
			if not research_queue.has(p):
				research_queue.append(p)
		emit_signal("research_changed")
		return
	if research_queue.has(tid):
		research_queue.erase(tid)
	if front:
		if not research_queue.is_empty() and research_queue[0] != tid:
			research_progress = 0.0
		research_queue.push_front(tid)
	else:
		research_queue.append(tid)
	emit_signal("research_changed")


func _prereq_chain(tid: String) -> Array:
	var out: Array = []
	var seen := {}
	var visit := func(id: String, f: Callable) -> void:
		if seen.has(id) or tech_done(id):
			return
		seen[id] = true
		for p in Content.techs.get(id, {}).get("prereqs", []):
			f.call(p, f)
		out.append(id)
	visit.call(tid, visit)
	return out


func dequeue_research(tid: String) -> void:
	var i := research_queue.find(tid)
	if i == 0:
		research_progress = 0.0
	research_queue.erase(tid)
	emit_signal("research_changed")


func current_research() -> String:
	while not research_queue.is_empty():
		var t: String = research_queue[0]
		if tech_available(t):
			return t
		if tech_done(t):
			research_queue.pop_front()
			research_progress = 0.0
			continue
		# blocked by prereqs not done yet: move the first available prereq ahead
		var chain := _prereq_chain(t)
		if chain.is_empty():
			research_queue.pop_front()
			continue
		research_queue.push_front(chain[0])
	return ""


func _complete_tech(tid: String) -> void:
	researched[tid] = tech_level(tid) + 1
	var t: Dictionary = Content.techs[tid]
	for r in t.get("unlocks", []):
		unlocked_recipes[r] = true
	recompute_bonuses()
	research_progress = 0.0
	if not t.get("repeatable", false):
		research_queue.erase(tid)
	elif not research_queue.is_empty() and research_queue[0] == tid:
		research_queue.pop_front()
	emit_signal("notify", "Research complete: " + t.get("name", tid) + ("" if not t.get("repeatable", false) else " " + str(tech_level(tid))), "research")
	emit_signal("tech_completed", tid)
	emit_signal("research_changed")
	_fill_contracts()


# ================================================================== market
func market_price(item: String) -> float:
	var s := float(market_sat.get(item, 0.0))
	return Content.item_value(item) * market_mult() * (1.0 - 0.65 * s)


func _sat_scale(item: String) -> float:
	return maxf(40.0, 40000.0 / maxf(Content.item_value(item), 0.01))


func sell(item: String, n: float) -> float:
	n = minf(n, inv.get(item, 0.0))
	if n <= 0.0:
		return 0.0
	# integrate price over the saturation increase
	var total := 0.0
	var remaining := n
	var chunk := maxf(1.0, n / 20.0)
	while remaining > 1e-6:
		var c := minf(chunk, remaining)
		total += market_price(item) * c
		market_sat[item] = minf(1.0, float(market_sat.get(item, 0.0)) + c / _sat_scale(item))
		remaining -= c
	inv[item] -= n
	credits += total
	lifetime_credits += total
	_credits_acc += total
	_count_cons(item, 0.0)
	emit_signal("sold", item, total)
	return total


func buy(item: String, n: float) -> bool:
	if not can_buy(item):
		return false
	var cost := buy_price(item) * n
	if credits < cost:
		return false
	credits -= cost
	add_item(item, n)
	return true


# ================================================================== contracts
func _fill_contracts() -> void:
	if Content.contracts.is_empty():
		return
	var pool: Array = []
	for c in Content.contracts:
		if int(c.get("tier", 0)) <= unlocked_tier and not contracts_active.has(c.id):
			pool.append(c.id)
	pool.shuffle()
	while contracts_active.size() < CONTRACT_SLOTS and not pool.is_empty():
		contracts_active.append(pool.pop_back())


func contract(cid: String) -> Dictionary:
	for c in Content.contracts:
		if c.id == cid:
			return c
	return {}


func fulfil_contract(cid: String) -> bool:
	var c := contract(cid)
	if c.is_empty() or not take_items(c.get("requires", {})):
		return false
	var cr := float(c.get("reward_credits", 0)) * market_mult()
	credits += cr
	lifetime_credits += cr
	for it in c.get("reward_items", {}):
		add_item(it, float(c.reward_items[it]))
	contracts_active.erase(cid)
	contracts_done += 1
	emit_signal("notify", "Contract fulfilled: %s (+%s)" % [c.get("name", cid), Fmt.credits(cr)], "good")
	_fill_contracts()
	return true


func reroll_contract(cid: String) -> void:
	var cost := reroll_cost()
	if credits < cost:
		return
	credits -= cost
	contracts_active.erase(cid)
	_fill_contracts()


func reroll_cost() -> float:
	return 50.0 * pow(4.0, unlocked_tier)


# ================================================================== megaprojects
func _mega_stages_done(mid: String) -> float:
	for m in Content.megaprojects:
		if m.id == mid:
			if megas_completed.has(mid):
				return float(m.get("stages", []).size())
			return float(mega_progress.get(mid, {}).get("stage", 0))
	return 0.0


func mega_blocker(mid: String) -> String:
	for m in Content.megaprojects:
		if m.id == mid:
			var rb: String = str(m.get("requires_building", ""))
			if rb != "" and rb != "<null>":
				var l := facility_line(rb)
				if l == null or l.count <= 0:
					return "Requires a %s" % Content.item_name(rb)
	return ""


func mega_state(mid: String) -> Dictionary:
	if not mega_progress.has(mid):
		mega_progress[mid] = {"stage": 0, "delivered": {}}
	return mega_progress[mid]


func mega_contribute(mid: String) -> float:
	var m: Dictionary = {}
	for x in Content.megaprojects:
		if x.id == mid:
			m = x
	if m.is_empty() or megas_completed.has(mid):
		return 0.0
	if mega_blocker(mid) != "":
		emit_signal("notify", mega_blocker(mid), "warn")
		return 0.0
	var st := mega_state(mid)
	var stages: Array = m.get("stages", [])
	if st.stage >= stages.size():
		return 1.0
	var req: Dictionary = stages[st.stage].get("requires", {})
	var done := true
	for it in req:
		var need := float(req[it]) - float(st.delivered.get(it, 0.0))
		if need > 0:
			var give := minf(need, inv.get(it, 0.0))
			if give > 0:
				inv[it] -= give
				_count_cons(it, give)
				st.delivered[it] = float(st.delivered.get(it, 0.0)) + give
			if give < need - 1e-6:
				done = false
	if done:
		emit_signal("notify", "%s — stage complete: %s" % [m.get("name", mid), stages[st.stage].get("name", "")], "good")
		st.stage += 1
		st.delivered = {}
		if st.stage >= stages.size():
			megas_completed[mid] = true
			recompute_bonuses()
			emit_signal("notify", "MEGAPROJECT COMPLETE: " + m.get("name", mid), "achievement")
	return float(st.stage) / maxf(1.0, stages.size())


func legacy_gain() -> float:
	var g = floor(sqrt(maxf(0.0, lifetime_credits) / 1.0e7))
	for m in Content.megaprojects:
		if megas_completed.has(m.id):
			var rw = m.get("reward", {})
			g += float(rw.get("prestige", 5.0)) if rw is Dictionary else 5.0
	return g


func can_prestige() -> bool:
	var final_id := final_megaproject()
	return final_id != "" and megas_completed.has(final_id)


func final_megaproject() -> String:
	return "" if Content.megaprojects.is_empty() else Content.megaprojects[-1].id


func prestige() -> void:
	if not can_prestige():
		return
	legacy += legacy_gain()
	prestige_count += 1
	new_game(true)
	recompute_bonuses()
	emit_signal("notify", "A new legacy begins. Legacy bonus: +%d%% speed, +%d%% prices" % [int(legacy * 2), int(legacy * 5)], "achievement")


# ================================================================== simulation
func tick(dt: float) -> void:
	play_time += dt
	game_time += dt
	if _caps_dirty:
		_recompute_storage()
	_tick_prod.clear()
	_tick_cons.clear()
	_compute_support()
	_simulate_power(dt)
	_simulate_lines(dt)
	_simulate_research(dt)
	_simulate_world(dt)
	# smoothed rates
	var k := 1.0 - exp(-dt / 6.0)
	for it in _tick_prod:
		rates_prod[it] = lerpf(rates_prod.get(it, 0.0), _tick_prod[it] / dt, k)
	for it in rates_prod.keys():
		if not _tick_prod.has(it):
			rates_prod[it] = lerpf(rates_prod[it], 0.0, k)
	for it in _tick_cons:
		rates_cons[it] = lerpf(rates_cons.get(it, 0.0), _tick_cons[it] / dt, k)
	for it in rates_cons.keys():
		if not _tick_cons.has(it):
			rates_cons[it] = lerpf(rates_cons[it], 0.0, k)
	credits_rate = lerpf(credits_rate, _credits_acc / dt, k)
	_credits_acc = 0.0
	_slow += dt
	if _slow >= 1.0:
		_slow = 0.0
		if not simulating_offline:
			_check_achievements()
		for it in market_sat.keys():
			market_sat[it] = float(market_sat[it]) * exp(-1.0 / 180.0)
			if market_sat[it] < 0.001:
				market_sat.erase(it)


func daylight() -> float:
	var ph := fmod(game_time, day_length()) / day_length()
	return clampf(sin(ph * TAU) * 1.4 + 0.2, 0.0, 1.0)


func _best_fuel(fuel_class: String, pinned: String, need_kj: float) -> String:
	if pinned != "" and inv.get(pinned, 0.0) > 0.0:
		return pinned
	var best := ""
	var best_kj := 0.0
	for it in inv:
		if inv[it] <= 0.0:
			continue
		var d: Dictionary = Content.items.get(it, {})
		if not d.has("fuel_kj"):
			continue
		if d.get("fuel_class", "chemical") != fuel_class:
			continue
		if Content.buildings.has(it):
			continue
		var kj := float(d.fuel_kj)
		if kj > best_kj:
			best_kj = kj
			best = it
	return best


## Burn `need_kj` of fuel of `fuel_class`; returns satisfied fraction.
func _burn(fuel_class: String, pinned: String, need_kj: float) -> float:
	if need_kj <= 0.0:
		return 1.0
	var got := 0.0
	for attempt in 3:
		var f := _best_fuel(fuel_class, pinned, need_kj - got)
		if f == "":
			break
		var kj := float(Content.items[f].fuel_kj)
		var units := minf(inv[f], (need_kj - got) / kj)
		inv[f] -= units
		_count_cons(f, units)
		got += units * kj
		if got >= need_kj - 1e-6:
			break
	return clampf(got / need_kj, 0.0, 1.0)


func _compute_support() -> void:
	# support buildings (relays, substations, cooling towers) each cover SUPPORT_COVER machines
	var producers := 0
	var gens := 0
	for l in lines:
		if l.count <= 0:
			continue
		match l.kind():
			ProdLine.Kind.PRODUCER:
				producers += l.count
			ProdLine.Kind.GENERATOR:
				if not _is_accumulator(l):
					gens += l.count
	var s := {"speed": 0.0, "energy": 0.0, "power": 0.0}
	var tput := setting("base_throughput", 6.0)
	var ftput := setting("base_fluid_throughput", 5000.0)
	var psat := float(power.get("sat", 1.0))
	for l in lines:
		if l.count <= 0 or not l.enabled:
			continue
		var b: Dictionary = l.spec()
		var elec := psat if float(b.get("power_kw", 0.0)) > 0.0 else 1.0
		var sup: Dictionary = b.get("support", {})
		if not sup.is_empty():
			var cov_p := minf(1.0, l.count * SUPPORT_COVER / maxf(1.0, producers))
			var cov_g := minf(1.0, l.count * SUPPORT_COVER / maxf(1.0, gens))
			s.speed += float(sup.get("speed_bonus", 0.0)) * cov_p * elec
			s.energy += float(sup.get("energy_bonus", 0.0)) * cov_p * elec
			s.power += float(sup.get("power_bonus", 0.0)) * cov_g * elec
		if b.get("role", "") == "logistics":
			tput += float(b.get("throughput", 0.0)) * l.count * elec
			ftput += float(b.get("fluid_throughput", 0.0)) * l.count * elec
	support = s
	throughput = {"solid_cap": tput, "fluid_cap": ftput, "solid_flow": _flow_solid, "fluid_flow": _flow_fluid,
		"solid_sat": 1.0 if _flow_solid <= tput else tput / _flow_solid,
		"fluid_sat": 1.0 if _flow_fluid <= ftput else ftput / _flow_fluid}


func _is_accumulator(l: ProdLine) -> bool:
	return l.spec().get("generator", {}).get("source", "") == "accumulator"


func _simulate_power(dt: float) -> void:
	# demand: electric consumers at last tick's activity (idle draw 10%)
	var demand := 0.0
	var demand_p := 0.0
	var energy_mult := 1.0 + float(support.get("energy", 0.0))
	for l in lines:
		if not l.enabled or l.count <= 0:
			l.power_draw = 0.0
			continue
		var b: Dictionary = l.spec()
		var kw := float(b.get("power_kw", 0.0))
		if kw <= 0.0 or b.get("burner", false) or b.get("role", "") == "generator":
			l.power_draw = 0.0
			continue
		var mt: Dictionary = l.module_totals()
		var load := 1.0
		if l.kind() == ProdLine.Kind.PRODUCER:
			load = maxf(0.1, l.activity if l.status != "no_power" else 1.0)
		elif b.get("role", "") == "research":
			load = 1.0 if current_research() != "" else 0.1
		l.power_draw = kw * l.count * load * maxf(0.2, energy_mult + float(mt.energy))
		demand += l.power_draw
		if is_priority(l):
			demand_p += l.power_draw
	# supply
	var capacity := 0.0
	var gens: Array = []
	var by_source := {}
	var accum_cap := 0.0
	var accum_rate := 0.0
	var pb: Dictionary = bonuses.get("power_output", {})
	for l in lines:
		if l.kind() != ProdLine.Kind.GENERATOR or not l.enabled or l.count <= 0:
			continue
		var b: Dictionary = l.spec()
		var g: Dictionary = b.get("generator", {})
		if _is_accumulator(l):
			accum_cap += float(b.get("capacity_kj", 0.0)) * l.count
			accum_rate += float(b.get("power_out_kw", 0.0)) * l.count
			l.status = "working"
			l.activity = clampf(accum_kj / maxf(1.0, accum_cap), 0.0, 1.0) if accum_cap > 0 else 0.0
			continue
		var out = float(b.get("power_out_kw", 0.0)) * l.count
		var src: String = g.get("source", g.get("fuel_class", g.get("fluid", "other")))
		out *= 1.0 + float(pb.get(src, 0.0)) + float(pb.get("*", 0.0)) + float(support.get("power", 0.0))
		var avail := 1.0
		if g.has("source"):
			match g.source:
				"solar":
					avail = daylight()
				"wind":
					avail = _wind
				"tidal":
					avail = 0.6 + 0.4 * sin(game_time / 300.0)
				_:
					avail = 1.0
		elif g.has("fluid"):
			avail = clampf(inv.get(g.fluid, 0.0) / maxf(0.001, float(g.get("rate", 1.0)) * l.count * dt), 0.0, 1.0)
		elif g.has("fuel_class"):
			avail = 1.0 if _best_fuel(g.fuel_class, l.fuel, 1.0) != "" else 0.0
		l.status = "working" if avail > 0.01 else ("no_fuel" if not g.has("source") else "idle")
		if l.status == "no_fuel" and g.has("fluid"):
			l.status = "no_input"
			l.status_item = g.fluid
		capacity += out * avail
		gens.append([l, out * avail, out])
	# dispatch: free sources first, then fluids, then fuel burners
	gens.sort_custom(func(a, b): return _gen_priority(a[0]) < _gen_priority(b[0]))
	var want := demand
	if accum_kj < accum_cap:
		want += minf((accum_cap - accum_kj) / dt, accum_rate)   # recharge headroom
	var remaining := want
	var supplied := 0.0
	for g in gens:
		var l: ProdLine = g[0]
		var avail_kw: float = g[1]
		var use := minf(avail_kw, remaining)
		remaining -= use
		var frac: float = use / maxf(0.001, g[2])
		l.activity = frac
		l.anim_phase = fmod(l.anim_phase + dt * frac, 1000.0)
		var gs: Dictionary = l.spec().get("generator", {})
		if gs.has("fluid"):
			var units := float(gs.get("rate", 1.0)) * l.count * frac * dt
			units = minf(units, inv.get(gs.fluid, 0.0))
			inv[gs.fluid] = inv.get(gs.fluid, 0.0) - units
			_count_cons(gs.fluid, units)
		elif gs.has("fuel_class"):
			var kj := float(gs.get("fuel_kw", l.spec().get("power_out_kw", 0.0))) * l.count * frac * dt
			var sat := _burn(gs.fuel_class, l.fuel, kj)
			if sat < 1.0:
				use *= sat
		supplied += use
		var key: String = gs.get("source", gs.get("fuel_class", gs.get("fluid", "other")))
		by_source[key] = by_source.get(key, 0.0) + use
	var surplus := supplied - demand
	if surplus > 0.0:
		accum_kj = minf(accum_cap, accum_kj + minf(surplus, accum_rate) * dt)
		supplied = demand
	elif surplus < 0.0 and accum_kj > 0.0:
		var draw := minf(minf(-surplus, accum_rate) * dt, accum_kj)
		accum_kj -= draw
		supplied += draw / dt
		by_source["accumulator"] = draw / dt
	var sat := 1.0 if demand <= 0.0 else clampf(supplied / demand, 0.0, 1.0)
	# priority circuit: water pumps, boilers and reactors are fed first
	var sat_p := 1.0 if demand_p <= 0.0 else clampf(supplied / demand_p, 0.0, 1.0)
	var rest := maxf(0.0, supplied - demand_p * sat_p)
	var dn := demand - demand_p
	var sat_n := 1.0 if dn <= 0.0 else clampf(rest / dn, 0.0, 1.0)
	power = {"demand": demand, "supply": supplied, "capacity": capacity, "sat": sat_n, "sat_priority": sat_p, "overall": sat,
		"accum": accum_kj, "accum_cap": accum_cap, "by_source": by_source}
	_wind = clampf(_wind + randf_range(-0.02, 0.02) * dt * 10.0, 0.25, 1.0)


const PRIORITY_CATEGORIES := ["pumping", "boiling", "fission", "fusion"]


func is_priority(l: ProdLine) -> bool:
	if l.recipe == "":
		return false
	var r: Dictionary = Content.recipes.get(l.recipe, {})
	if r.get("category", "") in PRIORITY_CATEGORIES:
		return true
	# fuel extraction keeps the boilers lit
	if r.has("deposit"):
		for it in r.get("outputs", {}):
			if Content.items.get(it, {}).has("fuel_kj"):
				return true
	return false


func _gen_priority(l: ProdLine) -> int:
	var g: Dictionary = l.spec().get("generator", {})
	if g.has("source"):
		return 0
	if g.has("fluid"):
		return 1
	return 2


func _recipe_burns_own_output(r: Dictionary) -> bool:
	for it in r.get("outputs", {}):
		var d: Dictionary = Content.items.get(it, {})
		if d.has("fuel_kj") and d.get("fuel_class", "chemical") == "chemical":
			return true
	return false


func _simulate_lines(dt: float) -> void:
	var psat := float(power.sat)
	var dep_used := {}
	var prod_bonus_mining := float(bonuses.get("mining_productivity", 0.0))
	var ssat := float(throughput.get("solid_sat", 1.0))
	var fsat := float(throughput.get("fluid_sat", 1.0))
	var flow_s := 0.0
	var flow_f := 0.0
	# ---- deposit slots go to the fastest extractors first
	var alloc := {}
	var ext: Array = []
	for l in lines:
		if l.enabled and l.count > 0 and l.recipe != "" and Content.recipes.get(l.recipe, {}).has("deposit"):
			ext.append(l)
	ext.sort_custom(func(a, b): return float(a.spec().get("speed", 1)) > float(b.spec().get("speed", 1)))
	for l in ext:
		var dep: String = Content.recipes[l.recipe].deposit
		var used := int(dep_used.get(dep, 0))
		var k := clampi(deposit_slots(dep) - used, 0, l.count)
		dep_used[dep] = used + k
		alloc[l.uid] = k
	# ---- pass 1: per-line desired crafts (all limits except shared inputs) + total input demand
	var plans: Array = []
	var demand := {}
	for l in lines:
		if l.kind() != ProdLine.Kind.PRODUCER:
			continue
		l.crafts_per_sec = 0.0
		if not l.enabled:
			l.activity = 0.0
			l.status = "disabled"
			continue
		if l.count <= 0 or l.recipe == "":
			l.activity = 0.0
			l.status = "idle"
			continue
		var b: Dictionary = l.spec()
		var r: Dictionary = l.recipe_spec()
		if r.is_empty():
			l.status = "idle"
			continue
		var n: int = l.count
		if r.has("deposit"):
			n = int(alloc.get(l.uid, 0))
			if n <= 0:
				l.activity = 0.0
				l.status = "no_slots"
				l.effective_count = 0
				continue
		l.effective_count = n
		var mt: Dictionary = l.module_totals()
		var speed := float(b.get("speed", 1.0)) * (1.0 + speed_bonus(r.category) + float(mt.speed) + float(support.get("speed", 0.0)))
		speed = maxf(speed, 0.05)
		var nominal: float = n * speed / maxf(0.01, float(r.get("time", 1.0))) * dt
		var limit := 1.0
		var why := "working"
		var why_item := ""
		var ins: Dictionary = r.get("inputs", {})
		var outs: Dictionary = r.get("outputs", {})
		var prod := 1.0 + float(mt.productivity) + (prod_bonus_mining if r.has("deposit") else 0.0)
		var electric: bool = float(b.get("power_kw", 0.0)) > 0.0 and not b.get("burner", false)
		var lsat: float = float(power.get("sat_priority", 1.0)) if is_priority(l) else psat
		if electric and lsat < limit:
			limit = lsat
			why = "no_power"
		var self_fuel := false
		if b.get("burner", false) and _best_fuel("chemical", l.fuel, 1.0) == "":
			if _recipe_burns_own_output(r):
				self_fuel = true
			else:
				limit = 0.0
				why = "no_fuel"
		var solid_out := 0.0
		var fluid_out := 0.0
		for it in outs:
			if Content.is_fluid(it):
				fluid_out += float(outs[it]) * prod
			else:
				solid_out += float(outs[it]) * prod
		var pre_logistics := limit
		var prio := is_priority(l)
		if solid_out > 0.0 and ssat < limit and not prio:
			limit = ssat
			why = "logistics"
		if fluid_out > 0.0 and fsat < limit and not prio:
			limit = fsat
			why = "logistics"
		for it in outs:
			var net: float = (float(outs[it]) * prod - float(ins.get(it, 0.0))) * nominal
			if net <= 0.0 or overflow_sell.has(it):
				continue
			var space: float = cap(it) - inv.get(it, 0.0)
			var ratio := clampf(space / net, 0.0, 1.0)
			if ratio < limit:
				limit = ratio
				why = "output_full"
				why_item = it
		flow_s += solid_out * nominal * minf(pre_logistics, 1.0) / dt
		flow_f += fluid_out * nominal * minf(pre_logistics, 1.0) / dt
		var desire: float = nominal * limit
		for it in ins:
			demand[it] = float(demand.get(it, 0.0)) + float(ins[it]) * desire
		plans.append([l, b, r, mt, n, nominal, limit, why, why_item, prod, self_fuel, desire])
	# ---- shared input supply ratios
	var supply := {}
	for it in demand:
		var d: float = demand[it]
		supply[it] = 1.0 if d <= 0.0 else clampf(inv.get(it, 0.0) / d, 0.0, 1.0)
	# ---- pass 2: run
	for pl in plans:
		var l: ProdLine = pl[0]
		var b: Dictionary = pl[1]
		var r: Dictionary = pl[2]
		var mt: Dictionary = pl[3]
		var n: int = pl[4]
		var nominal: float = pl[5]
		var limit: float = pl[6]
		var why: String = pl[7]
		var why_item: String = pl[8]
		var prod: float = pl[9]
		var self_fuel: bool = pl[10]
		var ins: Dictionary = r.get("inputs", {})
		var outs: Dictionary = r.get("outputs", {})
		var in_ratio := 1.0
		for it in ins:
			var sr: float = supply.get(it, 1.0)
			# never consume more than is physically present right now
			var need: float = float(ins[it]) * nominal * limit
			if need > 0.0:
				sr = minf(sr, clampf(inv.get(it, 0.0) / need, 0.0, 1.0))
			if sr < in_ratio:
				in_ratio = sr
				if sr < 0.999:
					why = "no_input"
					why_item = it
		var crafts: float = nominal * limit * in_ratio
		var fuel_kj: float = float(b.get("fuel_kw", 0.0)) * n * dt * (crafts / maxf(nominal, 1e-9)) if b.get("burner", false) else 0.0
		if fuel_kj > 0.0 and not self_fuel:
			var fs := _burn("chemical", l.fuel, fuel_kj)
			if fs < 1.0:
				crafts *= fs
				why = "no_fuel"
		if crafts > 0.0:
			var items := {}
			for it in ins:
				items[it] = -float(ins[it]) * crafts
			for it in outs:
				items[it] = float(items.get(it, 0.0)) + float(outs[it]) * crafts * prod
			for it in items:
				var d: float = items[it]
				if d < 0.0:
					inv[it] = maxf(0.0, inv.get(it, 0.0) + d)
					_count_cons(it, -d)
				elif d > 0.0:
					inv[it] = inv.get(it, 0.0) + d
					_count_prod(it, d)
					var c := cap(it)
					if inv[it] > c:
						var extra: float = inv[it] - c
						inv[it] = c
						if overflow_sell.has(it):
							var v := market_price(it) * extra
							credits += v
							lifetime_credits += v
							_credits_acc += v
							market_sat[it] = minf(1.0, float(market_sat.get(it, 0.0)) + extra / _sat_scale(it))
			if self_fuel and fuel_kj > 0.0:
				_burn("chemical", l.fuel, fuel_kj)
			var poll: float = float(b.get("pollution", 0.0)) * n * (crafts / maxf(nominal, 1e-9)) * dt / 60.0
			if poll > 0.0:
				poll *= maxf(0.1, 1.0 + float(mt.pollution))
			pollution += poll
		l.activity = crafts / maxf(nominal, 1e-9)
		l.crafts_per_sec = crafts / dt
		l.status = "working" if l.activity > 0.98 else why
		l.status_item = why_item if l.activity <= 0.98 else ""
		l.anim_phase = fmod(l.anim_phase + dt * l.activity, 1000.0)
	_flow_solid = flow_s
	_flow_fluid = flow_f


func lab_speed() -> float:
	var s := 0.0
	for l in lines:
		var b: Dictionary = l.spec()
		if b.get("role", "") == "research" and l.enabled and l.count > 0:
			var elec := float(b.get("power_kw", 0.0)) > 0.0
			s += float(b.get("speed", 1.0)) * l.count * (float(power.sat) if elec else 1.0)
	return s * (1.0 + float(bonuses.get("lab_speed", 0.0)) + float(bonuses.get("global_speed", 0.0)))


func _simulate_research(dt: float) -> void:
	var tid := current_research()
	var labs := []
	for l in lines:
		if l.spec().get("role", "") == "research":
			labs.append(l)
	if tid == "":
		for l in labs:
			l.activity = 0.0
			l.status = "idle"
		return
	var t: Dictionary = Content.techs[tid]
	var speed := lab_speed()
	if speed <= 0.0:
		return
	var units_delta := speed * dt / maxf(0.1, float(t.get("time", 10.0)))
	var cost: Dictionary = t.get("cost", {})
	var ratio := 1.0
	var missing := ""
	for it in cost:
		var need := float(cost[it]) * units_delta
		if need > 0:
			var r := clampf(inv.get(it, 0.0) / need, 0.0, 1.0)
			if r < ratio:
				ratio = r
				missing = it
	units_delta *= ratio
	for it in cost:
		var a := float(cost[it]) * units_delta
		inv[it] = maxf(0.0, inv.get(it, 0.0) - a)
		_count_cons(it, a)
	research_progress += units_delta * (1.0 + float(bonuses.get("lab_productivity", 0.0)))
	for l in labs:
		l.activity = ratio
		l.status = "working" if ratio > 0.98 else "no_input"
		l.status_item = missing if ratio <= 0.98 else ""
		l.anim_phase = fmod(l.anim_phase + dt * ratio, 1000.0)
	if research_progress >= tech_units(tid) - 1e-6:
		_complete_tech(tid)


func _simulate_world(dt: float) -> void:
	# pollution: natural absorption by claimed land + negative-pollution buildings (scrubbers)
	var absorb := 30.0 + 20.0 * sectors_claimed.size() + pollution * 0.2
	var def := 0.0
	var psat := float(power.sat)
	var dbon: Dictionary = bonuses.get("defense", {})
	for l in lines:
		if l.count <= 0 or not l.enabled:
			continue
		var b: Dictionary = l.spec()
		var role: String = b.get("role", "")
		var elec := psat if float(b.get("power_kw", 0.0)) > 0.0 else 1.0
		if role != "producer" and float(b.get("pollution", 0.0)) < 0.0:
			absorb += -float(b.pollution) * l.count * elec
		if role == "defense":
			var rating = float(b.get("defense", 0.0)) * l.count * elec
			var ammo_class = b.get("ammo")
			if ammo_class != null and str(ammo_class) != "":
				var cls := str(ammo_class)
				rating *= 1.0 + float(dbon.get(cls, 0.0))
				var per_sec = float(b.get("ammo_per_min", 0.0)) * l.count / 60.0 * clampf(threat / maxf(1.0, def + rating), 0.15, 1.0)
				var a := _best_ammo(cls)
				if a == "":
					rating *= 0.15
					l.status = "no_input"
					l.status_item = ""
				else:
					var mult := float(Content.items[a].get("ammo", {}).get("mult", 1.0))
					var use := minf(inv.get(a, 0.0), per_sec * dt)
					inv[a] -= use
					_count_cons(a, use)
					rating *= mult
					l.status = "working"
			else:
				l.status = "working"
			rating *= 1.0 + float(dbon.get("*", 0.0))
			l.activity = (1.0 if l.status == "working" else 0.2) * elec
			l.anim_phase = fmod(l.anim_phase + dt * l.activity, 1000.0)
			def += rating
		elif role in ["storage", "logistics", "support", "megaproject"]:
			l.status = "working" if elec > 0.99 else "no_power"
			l.activity = elec
			l.anim_phase = fmod(l.anim_phase + dt * l.activity, 1000.0)
	pollution = maxf(0.0, pollution - absorb * (1.0 + float(bonuses.get("pollution_reduction", 0.0))) * dt / 60.0)
	defense = def
	# threat: strongest hostile drawn in by pollution + frontier exposure of claimed sectors
	var base_threat := 0.0
	for th in Content.threats:
		if pollution >= float(th.get("appears_at_pollution", 0.0)):
			base_threat = maxf(base_threat, float(th.get("strength", 0.0)))
	var exposure := 0.0
	for sid in sectors_claimed:
		exposure += float(Content.sector_by_id.get(sid, {}).get("threat", 0.0))
	var target := (base_threat + exposure) * (1.0 + sqrt(pollution) / 40.0) if pollution > 0 or exposure > 0 else 0.0
	threat = lerpf(threat, target, 1.0 - exp(-dt / 30.0))
	var old_siege := siege
	var frontier := sectors_claimed.size() > maxi(1, Content.start.get("sectors", []).size())
	siege = clampf(1.0 - defense / threat, 0.0, 1.0) if threat > 1.0 and frontier else 0.0
	if old_siege < 0.05 and siege >= 0.05 and not simulating_offline:
		emit_signal("notify", "Frontier sectors under siege! Defense %s vs threat %s" % [Fmt.num(defense), Fmt.num(threat)], "bad")


func _best_ammo(cls: String) -> String:
	var best := ""
	var bm := 0.0
	for it in inv:
		if inv[it] <= 0.0:
			continue
		var a: Dictionary = Content.items.get(it, {}).get("ammo", {})
		if a.get("class", "") == cls and float(a.get("mult", 1.0)) > bm:
			bm = float(a.get("mult", 1.0))
			best = it
	return best


# ================================================================== achievements
func _check_achievements() -> void:
	for a in Content.achievements:
		if achievements_done.has(a.id):
			continue
		if _achievement_met(a.get("condition", {})):
			achievements_done[a.id] = Time.get_unix_time_from_system()
			emit_signal("notify", "Achievement: " + a.get("name", a.id), "achievement")


func achievement_progress(cond: Dictionary) -> Vector2:
	var typ: String = cond.get("type", "")
	var target = cond.get("target")
	var v := float(cond.get("value", 1))
	var have := 0.0
	match typ:
		"produce_total", "produce":
			have = float(stats_produced.get(target, 0.0))
		"build_count", "build", "own_building":
			if target == null or target == "":
				for l in lines:
					have += l.count
			else:
				for l in lines:
					if l.building == target:
						have += l.count
		"research", "tech":
			have = 1.0 if researched.has(target) else 0.0
			v = 1.0
		"research_count", "techs_researched":
			have = researched.size()
		"credits_total", "earn_credits", "lifetime_credits", "credits":
			have = lifetime_credits
		"power_kw", "power_production", "power":
			have = float(power.supply)
		"sector_claimed", "claim_sector":
			have = 1.0 if sectors_claimed.has(target) else 0.0
			v = 1.0
		"sectors_claimed", "sector_count", "sectors":
			have = sectors_claimed.size()
		"prestige", "prestige_count":
			have = prestige_count
		"contracts_done", "contracts":
			have = contracts_done
		"megaproject", "megaproject_complete":
			if target == null or str(target) == "":
				for m in Content.megaprojects:
					have += _mega_stages_done(m.id)
			else:
				have = _mega_stages_done(str(target))
		"lines", "line_count":
			have = lines.size()
		"defense":
			have = defense
		"pollution":
			have = pollution
		"play_time":
			have = play_time
		"items_in_storage", "inventory":
			have = float(inv.get(target, 0.0))
		"rate", "production_rate":
			have = float(rates_prod.get(target, 0.0)) * 60.0
		_:
			have = 0.0
	return Vector2(have, v)


func _achievement_met(cond: Dictionary) -> bool:
	var p := achievement_progress(cond)
	return p.x >= p.y and p.y > 0


# ================================================================== persistence
func to_dict() -> Dictionary:
	var ls: Array = []
	for l in lines:
		ls.append(l.to_dict())
	return {
		"version": 1, "credits": credits, "inv": inv, "lines": ls, "next_uid": next_uid,
		"researched": researched, "research_queue": research_queue, "research_progress": research_progress,
		"unlocked_recipes": unlocked_recipes.keys(), "sectors_claimed": sectors_claimed.keys(),
		"market_sat": market_sat, "overflow_sell": overflow_sell.keys(), "pollution": pollution,
		"accum_kj": accum_kj, "contracts_active": contracts_active, "contracts_done": contracts_done,
		"achievements_done": achievements_done, "mega_progress": mega_progress,
		"megas_completed": megas_completed.keys(), "legacy": legacy, "prestige_count": prestige_count,
		"stats_produced": stats_produced, "stats_consumed": stats_consumed,
		"lifetime_credits": lifetime_credits, "play_time": play_time, "game_time": game_time,
		"saved_at": Time.get_unix_time_from_system(), "threat": threat,
	}


func _keys_to_set(arr) -> Dictionary:
	var d := {}
	if arr is Array:
		for k in arr:
			d[k] = true
	return d


func from_dict(d: Dictionary) -> void:
	credits = float(d.get("credits", 0))
	inv = {}
	var di: Dictionary = d.get("inv", {})
	for k in di:
		inv[k] = float(di[k])
	lines = []
	for ld in d.get("lines", []):
		var l := ProdLine.from_dict(ld)
		if Content.buildings.has(l.building):
			lines.append(l)
	next_uid = int(d.get("next_uid", lines.size() + 1))
	researched = {}
	var rd: Dictionary = d.get("researched", {})
	for k in rd:
		if Content.techs.has(k):
			researched[k] = int(rd[k])
	research_queue = d.get("research_queue", []).filter(func(x): return Content.techs.has(x))
	research_progress = float(d.get("research_progress", 0))
	unlocked_recipes = _keys_to_set(d.get("unlocked_recipes", []))
	# make sure free + researched recipes are unlocked even if content changed
	for r in Content.recipe_list:
		if r.get("unlocked_by") == null:
			unlocked_recipes[r.id] = true
	for tid in researched:
		for r in Content.techs[tid].get("unlocks", []):
			unlocked_recipes[r] = true
	sectors_claimed = _keys_to_set(d.get("sectors_claimed", []))
	market_sat = d.get("market_sat", {})
	overflow_sell = _keys_to_set(d.get("overflow_sell", []))
	pollution = float(d.get("pollution", 0))
	accum_kj = float(d.get("accum_kj", 0))
	contracts_active = d.get("contracts_active", [])
	contracts_done = int(d.get("contracts_done", 0))
	achievements_done = d.get("achievements_done", {})
	mega_progress = d.get("mega_progress", {})
	megas_completed = _keys_to_set(d.get("megas_completed", []))
	legacy = float(d.get("legacy", 0))
	prestige_count = int(d.get("prestige_count", 0))
	stats_produced = d.get("stats_produced", {})
	stats_consumed = d.get("stats_consumed", {})
	lifetime_credits = float(d.get("lifetime_credits", 0))
	play_time = float(d.get("play_time", 0))
	game_time = float(d.get("game_time", 0))
	threat = float(d.get("threat", 0))
	last_save_unix = float(d.get("saved_at", Time.get_unix_time_from_system()))
	_caps_dirty = true
	recompute_bonuses()
	_fill_contracts()


func save_game() -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		push_warning("save failed")
		return
	f.store_string(JSON.stringify(to_dict()))
	f.close()


func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var txt := FileAccess.get_file_as_string(SAVE_PATH)
	var d = JSON.parse_string(txt)
	if not (d is Dictionary):
		return false
	from_dict(d)
	emit_signal("state_reset")
	emit_signal("lines_changed")
	call_deferred("_offline_progress")
	return true


func wipe_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
	new_game(false)


func offline_cap_hours() -> float:
	return setting("offline_cap_hours", OFFLINE_BASE_CAP_H) * (1.0 + float(bonuses.get("offline_efficiency", 0.0)))


func _offline_progress() -> void:
	var now := Time.get_unix_time_from_system()
	var elapsed := now - last_save_unix
	if elapsed < 60.0:
		return
	var capped := minf(elapsed, offline_cap_hours() * 3600.0)
	var eff := clampf(OFFLINE_BASE_EFF + float(bonuses.get("offline_efficiency", 0.0)), 0.1, 1.0)
	var sim_time := capped * eff
	var before := inv.duplicate()
	var credits_before := credits
	simulating_offline = true
	var step := 2.0
	var t := 0.0
	var steps := 0
	while t < sim_time and steps < 20000:
		var s := minf(step, sim_time - t)
		tick(s)
		t += s
		steps += 1
		if steps > 200:
			step = 10.0
	simulating_offline = false
	var gained := {}
	for k in inv:
		var dlt := float(inv[k]) - float(before.get(k, 0.0))
		if dlt > 0.5:
			gained[k] = dlt
	emit_signal("offline_report", {"elapsed": elapsed, "simulated": sim_time, "credits": credits - credits_before, "items": gained})
