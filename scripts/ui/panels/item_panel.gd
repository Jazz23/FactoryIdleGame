extends BasePanel
## Encyclopedia entry for an item: how it's made, what uses it.

var item := ""


func _init() -> void:
	title = "Item"


func set_arg(a) -> void:
	item = str(a)
	mark_dirty()


func build() -> void:
	var it: Dictionary = Content.items.get(item, {})
	title = it.get("name", item)
	var h := UI.hbox(12)
	h.add_child(UI.icon(Content.icon(item), 128))
	var v := UI.vbox(3)
	v.add_child(UI.label(it.get("name", item), 26, UI.TEXT, "head_bold"))
	var d := UI.label(it.get("desc", ""), 15, UI.DIM)
	d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	d.custom_minimum_size.x = 400
	v.add_child(d)
	v.add_child(UI.label("Tier %d · %s · value %s" % [int(it.get("tier", 0)), str(it.get("group", "")).capitalize(), Fmt.credits(float(it.get("value", 0)))], 14, UI.DIM))
	v.add_child(UI.label("In storage: %s / %s" % [Fmt.num(Game.inv.get(item, 0.0)), Fmt.num(Game.cap(item))], 15))
	if it.has("fuel_kj"):
		v.add_child(UI.label("Fuel value: " + Fmt.energy(float(it.fuel_kj)), 14, UI.WARN))
	h.add_child(v)
	add_child(h)
	var s := UI.vbox(4)
	add_child(UI.scroll(s))
	s.add_child(UI.label("MADE BY", 15, UI.ACCENT, "head_bold"))
	for rid in Content.recipes_by_output.get(item, []):
		var r: Dictionary = Content.recipes[rid]
		var rr := UI.hbox()
		rr.add_child(UI.label(("✓ " if Game.unlocked_recipes.has(rid) else "🔒 ") + r.name, 15, UI.TEXT if Game.unlocked_recipes.has(rid) else UI.DIM))
		s.add_child(rr)
		s.add_child(recipe_line(r, -1.0, 24))
	s.add_child(UI.label("USED IN", 15, UI.ACCENT, "head_bold"))
	var uses: Array = Content.recipes_by_input.get(item, [])
	for rid in uses.slice(0, 30):
		var r: Dictionary = Content.recipes[rid]
		s.add_child(UI.label(r.name, 15, UI.TEXT if Game.unlocked_recipes.has(rid) else UI.DIM))
		s.add_child(recipe_line(r, -1.0, 24))
	for t in Content.tech_list:
		if t.get("cost", {}).has(item):
			s.add_child(UI.label("Research: " + t.name, 14, UI.RESEARCH))
	if uses.is_empty():
		s.add_child(UI.label("—", 15, UI.DIM))
