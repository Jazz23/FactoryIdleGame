extends BasePanel
## Encyclopedia entry for an item: how it's made, what uses it.

var item := ""
var plan_rate := 60.0   # per minute


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
	_build_planner(s)
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


func _build_planner(s: VBoxContainer) -> void:
	s.add_child(UI.label("PRODUCTION PLANNER", 15, UI.ACCENT, "head_bold"))
	var h := UI.hbox(4)
	h.add_child(UI.label("Target:", 14, UI.DIM))
	for r in [10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0]:
		var rate: float = r
		var b := UI.button(Fmt.num(rate) + "/min", func(): plan_rate = rate; mark_dirty())
		if is_equal_approx(plan_rate, rate):
			b.add_theme_color_override("font_color", UI.ACCENT)
		b.add_theme_font_size_override("font_size", 13)
		h.add_child(b)
	s.add_child(h)
	var p := Planner.plan(item, plan_rate / 60.0)
	var rows := Planner.rows(p)
	var cost := 0.0
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 10)
	for row in rows:
		if row.has("missing"):
			grid.add_child(UI.item_icon(row.missing, 26))
			grid.add_child(UI.label("%s — no unlocked recipe" % Content.item_name(row.missing), 14, UI.BAD))
			grid.add_child(Control.new())
			grid.add_child(Control.new())
			continue
		grid.add_child(UI.icon(Content.icon(Content.recipe_main_output(row.recipe)), 26))
		grid.add_child(UI.label(Content.recipes[row.recipe].name, 14))
		var bi := UI.icon(Content.icon(row.building), 26)
		bi.tooltip_text = Content.item_name(row.building)
		grid.add_child(bi)
		var ok: bool = row.have >= row.need
		grid.add_child(UI.label("%d / %d" % [row.have, row.need], 14, UI.GOOD if ok else UI.WARN))
		var deficit: int = maxi(0, row.need - row.have)
		var stock := int(Game.inv.get(row.building, 0.0))
		cost += maxi(0, deficit - stock) * Game.buy_price(row.building)
	s.add_child(grid)
	var bh := UI.hbox()
	var btn := UI.accent_button("Build missing  (%s)" % Fmt.credits(cost), func():
		var n := Planner.apply(Planner.plan(item, plan_rate / 60.0))
		Game.emit_signal("notify", "Planner added %d buildings." % n, "good" if n > 0 else "warn")
		mark_dirty()
	)
	bh.add_child(btn)
	bh.add_child(UI.label("Uses stored buildings first, then buys the rest.", 13, UI.DIM))
	s.add_child(bh)
