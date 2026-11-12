extends BasePanel
## Codex: every item, building and fluid in the game, grouped, with discovery state.

var search := ""
var group := ""
var _grid_host: VBoxContainer


func _init() -> void:
	title = "Codex"


func build() -> void:
	var known := 0
	for it in Content.item_list:
		if _discovered(it.id):
			known += 1
	var h := UI.hbox()
	h.add_child(UI.label("%d / %d discovered" % [known, Content.item_list.size()], 15, UI.DIM))
	h.add_child(UI.spacer())
	var se := LineEdit.new()
	se.placeholder_text = "Search…"
	se.text = search
	se.custom_minimum_size.x = 220
	se.text_changed.connect(func(t): search = t.to_lower(); _fill())
	h.add_child(se)
	add_child(h)
	var tabs := HFlowContainer.new()
	tabs.add_theme_constant_override("h_separation", 4)
	tabs.add_theme_constant_override("v_separation", 4)
	var groups := {}
	for it in Content.item_list:
		groups[it.get("group", "misc")] = true
	for g in [""] + groups.keys():
		var gname: String = g
		var b := UI.button("All" if gname == "" else gname.capitalize(), func(): group = gname; mark_dirty())
		b.add_theme_font_size_override("font_size", 13)
		if group == gname:
			b.add_theme_color_override("font_color", UI.ACCENT)
		tabs.add_child(b)
	add_child(tabs)
	_grid_host = UI.vbox(6)
	add_child(UI.scroll(_grid_host))
	_fill()


func _discovered(id: String) -> bool:
	if Game.inv.get(id, 0.0) > 0.0 or Game.stats_produced.has(id):
		return true
	for rid in Content.recipes_by_output.get(id, []):
		if Game.unlocked_recipes.has(rid):
			return true
	return false


func _fill() -> void:
	if _grid_host == null:
		return
	UI.clear(_grid_host)
	var by_tier := {}
	for it in Content.item_list:
		if group != "" and it.get("group", "misc") != group:
			continue
		if search != "" and not it.name.to_lower().contains(search):
			continue
		by_tier.get_or_add(int(it.get("tier", 0)), []).append(it)
	var tiers := by_tier.keys()
	tiers.sort()
	for t in tiers:
		_grid_host.add_child(UI.label("TIER %d" % t, 15, UI.ACCENT, "head_bold"))
		var grid := GridContainer.new()
		grid.columns = 8
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 6)
		for it in by_tier[t]:
			var id: String = it.id
			var disc := _discovered(id)
			var p := UI.panel(Color(0.1, 0.105, 0.11, 0.95) if disc else Color(0.06, 0.06, 0.065, 0.95), UI.LINE, 4)
			p.custom_minimum_size = Vector2(72, 72)
			p.tooltip_text = "%s\n%s%s" % [it.name, it.get("desc", ""), "" if disc else "\n(not yet discovered)"]
			p.mouse_filter = Control.MOUSE_FILTER_STOP
			p.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
			p.gui_input.connect(func(e):
				if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
					hud.open("item", id)
			)
			var ic := UI.icon(Content.icon(id), 58)
			ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
			if not disc:
				ic.modulate = Color(0.25, 0.25, 0.27, 0.9)
			p.add_child(ic)
			grid.add_child(p)
		_grid_host.add_child(grid)
