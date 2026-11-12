extends Node
## Headless balance test: a greedy bot plays the game at high speed and logs progression.
##   godot --headless --path . -- --autoplay=HOURS [--dt=1.0] [--log=res://tests/autoplay_log.txt]

var hours := 10.0
var dt := 1.0
var sim_t := 0.0
var next_decision := 0.0
var next_report := 0.0
var last_tech_count := 0
var last_progress_t := 0.0
var log_lines: PackedStringArray = []
var tech_times: Dictionary = {}
var research_target_minutes := 6.0
var blacklist: Dictionary = {}       # tech -> sim time until which it is skipped
var watch_tech := ""
var watch_progress := 0.0
var watch_since := 0.0


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--autoplay="):
			hours = float(a.substr(11))
		elif a.begins_with("--dt="):
			dt = float(a.substr(5))
	Game.game_speed = 0.0
	Game.new_game(false)
	Game.tech_completed.connect(func(t): tech_times[t] = sim_t)
	_log("autoplay start: %d techs, %d recipes" % [Content.tech_list.size(), Content.recipe_list.size()])
	var t0 := Time.get_ticks_msec()
	while sim_t < hours * 3600.0:
		Game.tick(dt)
		sim_t += dt
		if sim_t >= next_decision:
			next_decision = sim_t + 20.0
			decide()
		if sim_t >= next_report:
			next_report = sim_t + 1800.0
			report()
		if Game.researched.size() != last_tech_count:
			last_tech_count = Game.researched.size()
			last_progress_t = sim_t
		elif sim_t - last_progress_t > 4.0 * 3600.0:
			_log("STALLED for 4h")
			diagnose()
			break
		if _all_done():
			_log("ALL NON-REPEATABLE TECHS DONE")
			break
	report()
	diagnose()
	_log("real time %.1fs" % ((Time.get_ticks_msec() - t0) / 1000.0))
	if OS.get_cmdline_user_args().has("--save"):
		Game.save_game()
		_log("saved game")
	var f := FileAccess.open("user://autoplay_log.txt", FileAccess.WRITE)
	f.store_string("\n".join(log_lines))
	get_tree().quit()


func _log(s: String) -> void:
	var line := "[%s] %s" % [Fmt.duration(sim_t), s]
	print(line)
	log_lines.append(line)


func _all_done() -> bool:
	for t in Content.tech_list:
		if not t.get("repeatable", false) and not Game.researched.has(t.id):
			return false
	return Game.megas_completed.size() >= Content.megaprojects.size()


func report() -> void:
	var nr := 0
	for t in Content.tech_list:
		if not t.get("repeatable", false):
			nr += 1
	var cur := Game.current_research()
	var bcount := 0
	for l in Game.lines:
		bcount += l.count
	_log("techs %d/%d tier %d | credits %s | power %s/%s sat %s | lines %d bldgs %d | logistics %s/%s | poll %s threat %s def %s | sectors %d | megas %d | researching %s" % [
		Game.researched.size(), nr, Game.unlocked_tier, Fmt.num(Game.credits), Fmt.power(Game.power.supply), Fmt.power(Game.power.capacity),
		Fmt.pct(Game.power.sat), Game.lines.size(), bcount, Fmt.num(Game.throughput.solid_flow), Fmt.num(Game.throughput.solid_cap),
		Fmt.num(Game.pollution), Fmt.num(Game.threat), Fmt.num(Game.defense), Game.sectors_claimed.size(), Game.megas_completed.size(), cur])


func diagnose() -> void:
	var cur := Game.current_research()
	if cur != "":
		var t: Dictionary = Content.techs[cur]
		_log("current %s progress %.1f/%.1f labs %.2f" % [cur, Game.research_progress, Game.tech_units(cur), Game.lab_speed()])
		for it in t.cost:
			var p := Planner.plan(it, 0.1)
			_log("  cost item %s inv %.1f rate %.3f/s plan-missing %s" % [it, Game.inv.get(it, 0.0), Game.rates_prod.get(it, 0.0), str(p.keys().filter(func(k): return str(k).begins_with("__")))])
	var bad := {}
	for l in Game.lines:
		if l.count > 0 and l.status != "working":
			var k := "%s:%s" % [l.status, l.status_item]
			bad[k] = int(bad.get(k, 0)) + 1
	_log("line statuses: " + str(bad))
	for sct in Content.sectors:
		if not Game.sectors_claimed.has(sct.id):
			_log("  next sector %s: %s cost %s" % [sct.id, Game.can_claim(sct.id), str(sct.claim_cost)])
			for it in sct.claim_cost:
				_log("    %s inv %.0f recipe '%s'" % [it, Game.inv.get(it, 0.0), Planner.recipe_for(it)])
			break
	for l in Game.lines:
		if l.spec().get("role", "") == "research":
			_log("  lab line %s x%d (stock %d, can_buy %s, price %s)" % [l.building, l.count, int(Game.inv.get(l.building, 0)), Game.can_buy(l.building), Fmt.num(Game.buy_price(l.building))])
	for dep in Content.deposits:
		var sl := Game.deposit_slots(dep)
		if sl > 0:
			_log("  deposit %s slots %d used %d prod %.2f/s cons %.2f/s inv %.0f" % [dep, sl, Game.deposit_used(dep), Game.rates_prod.get(dep, 0.0), Game.rates_cons.get(dep, 0.0), Game.inv.get(dep, 0.0)])
	var cur2 := Game.current_research()
	if cur2 != "":
		for it in Content.techs[cur2].cost:
			var rows := Planner.rows(Planner.plan(it, 0.5))
			for r in rows:
				if r.has("recipe"):
					_log("    plan %s: %s need %d have %d" % [it, r.recipe, r.need, r.have])


func diagnose_item(it: String, depth := 0) -> void:
	if depth > 3:
		return
	var rid := Planner.recipe_for(it)
	_log("%s%s: recipe %s inv %.1f prod %.3f cons %.3f" % ["  ".repeat(depth + 2), it, rid, Game.inv.get(it, 0.0), Game.rates_prod.get(it, 0.0), Game.rates_cons.get(it, 0.0)])
	if rid == "":
		return
	for l in Game.lines:
		if l.recipe == rid:
			_log("%s line %s x%d status %s %s" % ["  ".repeat(depth + 3), l.building, l.count, l.status, l.status_item])
	for i in Content.recipes[rid].get("inputs", {}):
		if Game.rates_prod.get(i, 0.0) < 0.01:
			diagnose_item(i, depth + 1)


# ------------------------------------------------------------------ decisions
func decide() -> void:
	_emergency()
	_pick_research()
	_ensure_labs()
	_ensure_research_supply()
	_ensure_fuel()
	_ensure_power()
	_ensure_logistics()
	_ensure_sectors()
	_ensure_defense()
	_control_pollution()
	_megaprojects()
	_upgrade_lines()
	_balance_deficits()
	_sell_surplus()


func _emergency() -> void:
	# out of fuel: liquidate stock and buy coal, like a player would
	if Game.inv.get("coal", 0.0) < 30.0:
		var need := Game.buy_price("coal") * 300.0
		if Game.credits < need:
			var keys := Game.inv.keys()
			keys.sort_custom(func(a, b): return Game.inv[a] * Content.item_value(a) > Game.inv[b] * Content.item_value(b))
			for it in keys:
				if Game.credits >= need:
					break
				if Content.buildings.has(it) or Content.is_fluid(it) or it == "coal":
					continue
				Game.sell(it, Game.inv[it] * 0.5)
		Game.buy("coal", minf(300.0, Game.credits / Game.buy_price("coal")))


func _balance_deficits() -> void:
	# latent demand: lines waiting on an input tell us exactly what is short
	var short := {}
	for l in Game.lines:
		if l.status != "no_input" or l.status_item == "" or l.recipe == "" or l.count <= 0:
			continue
		var r: Dictionary = Content.recipes[l.recipe]
		var b: Dictionary = l.spec()
		var nominal = l.effective_count * float(b.get("speed", 1.0)) * (1.0 + Game.speed_bonus(r.category)) / maxf(0.01, float(r.get("time", 1.0)))
		var it: String = l.status_item
		short[it] = float(short.get(it, 0.0)) + float(r.inputs.get(it, 0.0)) * nominal * (1.0 - l.activity)
	for it in short:
		if not Content.buildings.has(it):
			Planner.apply(Planner.plan(it, short[it] * 1.1), Game.credits * 0.3)
	# expand production of any item consumed faster than it is produced while stock runs low
	for it in Game.rates_cons.keys():
		var c: float = Game.rates_cons[it]
		var p: float = Game.rates_prod.get(it, 0.0)
		if c <= 0.0001 or Content.buildings.has(it):
			continue
		if c > p * 1.02 and Game.inv.get(it, 0.0) < Game.cap(it) * 0.25:
			Planner.apply(Planner.plan(it, (c - p) * 1.3 + 0.02), Game.credits * 0.3)


func _upgrade_lines() -> void:
	for l in Game.lines.duplicate():
		if l.count <= 0 or l.recipe == "":
			continue
		var ups := Game.upgrade_options(l.uid)
		if not ups.is_empty() and Game.credits > Game.buy_price(ups[0]) * l.count * 1.5:
			Game.upgrade_line(l.uid, ups[0])


func _tech_cost_value(t: Dictionary) -> float:
	var v := 0.0
	for it in t.get("cost", {}):
		v += Content.item_value(it) * float(t.cost[it])
	return v * Game.tech_units(t.id) * float(t.get("time", 10))


func _pick_research() -> void:
	var cur := Game.current_research()
	if cur != "":
		if cur != watch_tech:
			watch_tech = cur
			watch_progress = Game.research_progress
			watch_since = sim_t
		elif Game.research_progress > watch_progress + 0.5:
			watch_progress = Game.research_progress
			watch_since = sim_t
		elif sim_t - watch_since > 2700.0:
			_log("research %s stuck, deferring (%s)" % [cur, str(Content.techs[cur].cost.keys().map(func(k): return "%s inv %.0f prod %.3f" % [k, Game.inv.get(k, 0.0), Game.rates_prod.get(k, 0.0)]))])
			diagnose_item(Content.techs[cur].cost.keys()[0])
			blacklist[cur] = sim_t + 7200.0
			Game.dequeue_research(cur)
		else:
			return
		if Game.current_research() != "":
			return
	var best := ""
	var bv := INF
	for t in Content.tech_list:
		if not Game.tech_available(t.id) or blacklist.get(t.id, -1.0) > sim_t:
			continue
		var v := _tech_cost_value(t)
		if t.get("repeatable", false):
			v *= 50.0
		if v < bv:
			bv = v
			best = t.id
	if best != "":
		Game.queue_research(best, true)


func _lab_line() -> ProdLine:
	var best := ""
	var bs := -1.0
	for b in Content.building_list:
		if b.get("role", "") == "research" and Planner.building_available(b.id):
			if float(b.get("speed", 1)) > bs:
				bs = float(b.get("speed", 1))
				best = b.id
	if best == "":
		return null
	var l := Game.facility_line(best)
	if l == null:
		l = Game.add_line(best, "")
	return l


func _ensure_labs() -> void:
	var cur := Game.current_research()
	if cur == "":
		return
	var t: Dictionary = Content.techs[cur]
	var lab_time := Game.tech_units(cur) * float(t.get("time", 10))
	var want_speed := lab_time / (research_target_minutes * 60.0)
	var l := _lab_line()
	if l == null:
		return
	var tries := 0
	while Game.lab_speed() < want_speed and tries < 10:
		if Game.line_add(l.uid, 1) == 0:
			_craft_building(l.building)
			break
		tries += 1


func _craft_building(bid: String) -> void:
	# can't buy (tier lock / credits): plan a slow production of the building item
	Planner.apply(Planner.plan(bid, 1.0 / 60.0), Game.credits * 0.5)


func _ensure_research_supply() -> void:
	var cur := Game.current_research()
	if cur == "":
		return
	var t: Dictionary = Content.techs[cur]
	var speed := maxf(Game.lab_speed(), 0.1)
	for it in t.cost:
		var rate := speed * float(t.cost[it]) / maxf(0.1, float(t.get("time", 10)))
		Planner.apply(Planner.plan(it, rate * 1.1), Game.credits * 0.8)


func _ensure_fuel() -> void:
	var kw := 0.0
	for l in Game.lines:
		var b: Dictionary = l.spec()
		if b.get("burner", false) and l.count > 0:
			kw += float(b.get("fuel_kw", 0)) * l.count * maxf(l.activity, 0.3)
	var gf := 0.0
	for l in Game.lines:
		var g: Dictionary = l.spec().get("generator", {})
		if g.has("fuel_class") and l.count > 0:
			gf += float(g.get("fuel_kw", 0)) * l.count * maxf(l.activity, 0.3)
	var total := kw + gf
	if total <= 0:
		return
	var fuel := "coal"
	for it in ["fuel_briquette", "coke", "coal"]:
		if Planner.recipe_for(it) != "":
			fuel = it
			break
	var need := total / float(Content.items[fuel].get("fuel_kj", 4000)) * 1.25
	if Game.rates_prod.get(fuel, 0.0) - Game.rates_cons.get(fuel, 0.0) < 0.0 or Game.inv.get(fuel, 0.0) < 50:
		Planner.apply(Planner.plan(fuel, need))


func _best_generator() -> String:
	var best := ""
	var bs := -1.0
	for b in Content.building_list:
		if b.get("role", "") != "generator":
			continue
		var g: Dictionary = b.get("generator", {})
		if g.get("source", "") == "accumulator" or not Planner.building_available(b.id):
			continue
		var score := float(b.get("power_out_kw", 0))
		if g.has("source"):
			score *= 0.35   # intermittent
		if g.has("fluid") and Planner.recipe_for(g.fluid) == "":
			continue
		if score > bs:
			bs = score
			best = b.id
	return best


func _ensure_power() -> void:
	var cap := float(Game.power.capacity)
	var demand := float(Game.power.demand)
	var want := demand * 1.3 + 100.0
	var gid := _best_generator()
	if gid == "":
		return
	var b: Dictionary = Content.buildings[gid]
	var l := Game.facility_line(gid)
	if l == null:
		l = Game.add_line(gid, "")
	if cap < want:
		var n := int(ceil((want - cap) / maxf(1.0, float(b.power_out_kw))))
		if Game.line_add(l.uid, mini(n, 5)) == 0:
			_craft_building(gid)
	# feed fluid generators
	for gl in Game.lines:
		var g: Dictionary = gl.spec().get("generator", {})
		if g.has("fluid") and gl.count > 0:
			var rate = float(g.get("rate", 1)) * gl.count * 1.05
			Planner.apply(Planner.plan(g.fluid, rate))


func _ensure_logistics() -> void:
	var tp: Dictionary = Game.throughput
	if float(tp.solid_flow) < float(tp.solid_cap) * 0.85 and float(tp.fluid_flow) < float(tp.fluid_cap) * 0.85:
		return
	var fluid := float(tp.fluid_flow) >= float(tp.fluid_cap) * 0.85
	var best := ""
	var bs := -1.0
	for b in Content.building_list:
		if b.get("role", "") == "logistics" and Planner.building_available(b.id):
			var v := float(b.get("fluid_throughput" if fluid else "throughput", 0))
			if v > bs:
				bs = v
				best = b.id
	if best == "" or bs <= 0:
		return
	var l := Game.facility_line(best)
	if l == null:
		l = Game.add_line(best, "")
	if Game.line_add(l.uid, 2) == 0:
		_craft_building(best)


func _ensure_sectors() -> void:
	for s in Content.sectors:
		if Game.sectors_claimed.has(s.id):
			continue
		if Game.can_claim(s.id) == "":
			Game.claim_sector(s.id)
			_log("claimed sector " + s.id)
			return
		# work toward claim cost (buy what the market sells, produce the rest)
		for it in s.get("claim_cost", {}):
			var short = float(s.claim_cost[it]) - Game.inv.get(it, 0.0)
			if short > 0 and Game.can_buy(it) and Game.credits > Game.buy_price(it) * short * 2.0:
				Game.buy(it, short)
		for it in s.get("claim_cost", {}):
			if Game.inv.get(it, 0.0) < float(s.claim_cost[it]):
				Planner.apply(Planner.plan(it, float(s.claim_cost[it]) / 600.0), Game.credits * 0.3)
		if Game.defense < float(s.get("defense_required", 0)):
			_add_defense()
		return


func _ensure_defense() -> void:
	if Game.threat > Game.defense * 0.9 and Game.sectors_claimed.size() > 1:
		_add_defense()
	# keep ammo flowing
	for l in Game.lines:
		var b: Dictionary = l.spec()
		if b.get("role", "") == "defense" and b.get("ammo") != null and l.count > 0:
			var ammo := ""
			for it in Content.item_list:
				if it.get("ammo", {}).get("class", "") == b.ammo and Planner.recipe_for(it.id) != "":
					ammo = it.id
			if ammo != "":
				Planner.apply(Planner.plan(ammo, float(b.get("ammo_per_min", 0)) * l.count / 60.0 * 1.1), Game.credits * 0.2)


func _control_pollution() -> void:
	if Game.pollution < 600.0:
		return
	var best := ""
	var bs := 0.0
	for b in Content.building_list:
		if b.get("role", "") != "producer" and float(b.get("pollution", 0)) < 0.0 and Planner.building_available(b.id):
			var v := -float(b.pollution) / maxf(1.0, Content.item_value(b.id))
			if v > bs:
				bs = v
				best = b.id
	if best == "":
		return
	var l := Game.facility_line(best)
	if l == null:
		l = Game.add_line(best, "")
	if Game.line_add(l.uid, 3) == 0:
		_craft_building(best)


func _add_defense() -> void:
	var best := ""
	var bs := -1.0
	for b in Content.building_list:
		if b.get("role", "") == "defense" and Planner.building_available(b.id):
			var v := float(b.get("defense", 0)) / maxf(1.0, Content.item_value(b.id))
			if v > bs:
				bs = v
				best = b.id
	if best == "":
		return
	var l := Game.facility_line(best)
	if l == null:
		l = Game.add_line(best, "")
	if Game.line_add(l.uid, 2) == 0:
		_craft_building(best)


func _megaprojects() -> void:
	for m in Content.megaprojects:
		if Game.megas_completed.has(m.id):
			continue
		var rb: String = str(m.get("requires_building", ""))
		if rb != "" and rb != "<null>":
			if not Planner.building_available(rb):
				continue
			var l := Game.facility_line(rb)
			if l == null:
				l = Game.add_line(rb, "")
			if l.count == 0:
				if Game.line_add(l.uid, 1) == 0:
					_craft_building(rb)
					continue
		var st := Game.mega_state(m.id)
		var stage: Dictionary = m.stages[st.stage]
		var ok := true
		for it in stage.requires:
			if Planner.recipe_for(it) == "":
				ok = false
		if not ok:
			continue
		for it in stage.requires:
			var left := float(stage.requires[it]) - float(st.delivered.get(it, 0.0))
			if left > 0:
				Planner.apply(Planner.plan(it, left / 1800.0), Game.credits * 0.5)
		Game.mega_contribute(m.id)
		return


func _sell_surplus() -> void:
	# byproduct jams: auto-sell whatever overflows on multi-output lines
	for l in Game.lines:
		if l.status == "output_full" and l.status_item != "" and l.recipe != "":
			if Content.recipes[l.recipe].get("outputs", {}).size() > 1 or Content.is_fluid(l.status_item):
				Game.overflow_sell[l.status_item] = true
	for it in Game.inv.keys():
		var have: float = Game.inv[it]
		if have <= 0 or Content.buildings.has(it) or Content.is_fluid(it):
			continue
		var c := Game.cap(it)
		if have > c * 0.6:
			Game.sell(it, have - c * 0.4)
