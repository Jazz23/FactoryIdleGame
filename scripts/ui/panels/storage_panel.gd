extends BasePanel
## Warehouse inventory grouped by item group, with fill levels.

var _cells := []
var search := ""
var _grid_host: VBoxContainer


func _init() -> void:
	title = "Storage"


func build() -> void:
	var h := UI.hbox()
	h.add_child(UI.label("Solid cap %s · Fluid cap %s per item" % [Fmt.num(Game.cap("__solid")), Fmt.num(Game.BASE_FLUID_CAP + Game._storage_add.fluid)], 14, UI.DIM))
	h.add_child(UI.spacer())
	var se := LineEdit.new()
	se.placeholder_text = "Search…"
	se.text = search
	se.custom_minimum_size.x = 200
	se.text_changed.connect(func(t): search = t.to_lower(); _fill())
	h.add_child(se)
	add_child(h)
	_grid_host = UI.vbox(6)
	add_child(UI.scroll(_grid_host))
	_fill()


func _fill() -> void:
	UI.clear(_grid_host)
	_cells.clear()
	var groups := {}
	for it in Content.item_list:
		if Game.inv.get(it.id, 0.0) < 0.01:
			continue
		if search != "" and not it.name.to_lower().contains(search):
			continue
		groups.get_or_add(it.get("group", "misc"), []).append(it)
	for g in groups:
		_grid_host.add_child(UI.label(g.to_upper(), 15, UI.ACCENT, "head_bold"))
		var grid := GridContainer.new()
		grid.columns = 6
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 6)
		for it in groups[g]:
			var id: String = it.id
			var p := UI.panel(Color(0.1, 0.105, 0.11, 0.95), UI.LINE, 4)
			p.custom_minimum_size = Vector2(98, 100)
			p.tooltip_text = it.name + "\n" + it.get("desc", "")
			p.mouse_filter = Control.MOUSE_FILTER_STOP
			p.gui_input.connect(func(e):
				if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
					hud.open("item", id)
			)
			var v := UI.vbox(1)
			p.add_child(v)
			var ic := UI.icon(Content.icon(id), 52)
			ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
			v.add_child(ic)
			var l := UI.label("", 14)
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			v.add_child(l)
			var bar := UI.bar(0, 1, UI.ACCENT, 4)
			v.add_child(bar)
			grid.add_child(p)
			_cells.append([id, l, bar])
		_grid_host.add_child(grid)
	refresh()


func refresh() -> void:
	for c in _cells:
		var have := float(Game.inv.get(c[0], 0.0))
		var cp := Game.cap(c[0])
		(c[1] as Label).text = Fmt.num(have)
		(c[2] as ProgressBar).max_value = cp
		(c[2] as ProgressBar).value = have
		var full := have >= cp * 0.999
		(c[2] as ProgressBar).add_theme_stylebox_override("fill", UI.box(UI.BAD if full else UI.ACCENT, Color(0, 0, 0, 0), 2, 0))
