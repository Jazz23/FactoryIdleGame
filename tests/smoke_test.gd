extends Node
## Headless functional smoke test of game systems on the real content.
##   godot --headless --path . -- --smoke

var fails := 0


func check(cond: bool, what: String) -> void:
	if cond:
		print("  ok   ", what)
	else:
		fails += 1
		print("  FAIL ", what)


func _ready() -> void:
	Game.game_speed = 0.0
	Game.new_game(false)
	print("== start state")
	check(Game.lines.size() >= 8, "start lines created (%d)" % Game.lines.size())
	check(Game.credits > 0, "start credits")
	for i in 600:
		Game.tick(0.5)
	check(Game.inv.get("iron_ore", 0.0) + Game.stats_produced.get("iron_ingot", 0.0) > 0, "mining + smelting produce")
	check(float(Game.power.supply) > 0, "steam power online (%s)" % Fmt.power(Game.power.supply))

	print("== research")
	var first := ""
	for t in Content.tech_list:
		if Game.tech_available(t.id):
			first = t.id
			break
	Game.queue_research(first, true)
	for it in Content.techs[first].cost:
		Game.add_item(it, 1000)
	var before := Game.researched.size()
	for i in 4000:
		Game.tick(0.5)
		if Game.researched.size() > before:
			break
	check(Game.researched.has(first), "researched %s" % first)
	var unl: Array = Content.techs[first].get("unlocks", [])
	check(unl.is_empty() or Game.unlocked_recipes.has(unl[0]), "tech unlocked its recipes")

	print("== planner + lines")
	var p := Planner.plan("iron_gear", 1.0)
	check(not p.is_empty(), "planner produces a plan for iron_gear")
	Game.credits += 1e6
	var n := Planner.apply(p)
	check(n > 0, "planner built %d buildings" % n)

	print("== market")
	Game.add_item("iron_plate", 100)
	var c0 := Game.credits
	var got := Game.sell("iron_plate", 50)
	check(got > 0 and Game.credits > c0, "sold plates for %s" % Fmt.credits(got))
	check(Game.market_price("iron_plate") < Content.item_value("iron_plate") * Game.market_mult(), "saturation lowers price")
	check(Game.buy("coal", 10), "bought coal")

	print("== contracts")
	check(not Game.contracts_active.is_empty(), "contracts offered (%d)" % Game.contracts_active.size())
	var cid: String = Game.contracts_active[0]
	var cdef := Game.contract(cid)
	for it in cdef.requires:
		Game.add_item(it, float(cdef.requires[it]))
	check(Game.fulfil_contract(cid), "contract fulfilled")

	print("== sectors")
	var s1: Dictionary = Content.sectors[1]
	for it in s1.claim_cost:
		Game.add_item(it, float(s1.claim_cost[it]))
	check(Game.claim_sector(s1.id), "claimed %s" % s1.id)
	check(Game.deposit_slots(s1.deposits.keys()[0]) > 0, "sector adds deposit slots")

	print("== defense / threat")
	Game.pollution = 5000.0
	for i in 200:
		Game.tick(1.0)
	check(Game.threat > 0, "pollution creates threat (%s)" % Fmt.num(Game.threat))

	print("== megaproject + prestige")
	var final_id := Game.final_megaproject()
	var m: Dictionary = Content.megaprojects[-1]
	var rb: String = str(m.get("requires_building", ""))
	if rb != "" and rb != "<null>":
		var l := Game.add_line(rb, "")
		Game.add_item(rb, 1)
		Game.line_add(l.uid, 1)
	for st in m.stages:
		for it in st.requires:
			Game.add_item(it, float(st.requires[it]))
		Game.mega_contribute(final_id)
	check(Game.megas_completed.has(final_id), "final megaproject completed")
	check(Game.can_prestige(), "prestige available")
	var gain := Game.legacy_gain()
	Game.prestige()
	check(Game.legacy >= gain and Game.prestige_count == 1, "prestige granted legacy %s" % Fmt.num(Game.legacy))
	check(Game.researched.is_empty(), "prestige reset research")

	print("== save / load")
	for i in 100:
		Game.tick(0.5)
	var d := Game.to_dict()
	var txt := JSON.stringify(d)
	var d2 = JSON.parse_string(txt)
	Game.from_dict(d2)
	check(absf(Game.credits - float(d.credits)) < 0.01, "credits roundtrip")
	check(Game.lines.size() == d.lines.size(), "lines roundtrip")
	check(Game.legacy == float(d.legacy), "legacy roundtrip")

	print("== offline progress")
	Game.last_save_unix = Time.get_unix_time_from_system() - 3600.0
	var ore0 := float(Game.stats_produced.get("iron_ore", 0.0))
	Game._offline_progress()
	check(float(Game.stats_produced.get("iron_ore", 0.0)) > ore0, "offline hour produced ore")

	print("== achievements")
	Game._check_achievements()
	check(Game.achievements_done.size() > 0, "achievements unlocked (%d)" % Game.achievements_done.size())

	print("\nSMOKE %s (%d failures)" % ["PASSED" if fails == 0 else "FAILED", fails])
	get_tree().quit(1 if fails > 0 else 0)
