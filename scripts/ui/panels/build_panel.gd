extends BasePanel
## Create a new production line: pick a product/recipe, then a compatible building.
## Also lists facilities (generators, labs, storage, defense, support).

var search := ""
var tab := "products"
var picked_recipe := ""
var _search_box: LineEdit


func _init() -> void:
	title = "Build"


func build() -> void:
	var tabs := UI.hbox(4)
	for t in [["products", "Products"], ["power", "Power"], ["facilities", "Facilities"]]:
		var b := UI.button(t[1], func(): tab = t[0]; picked_recipe = ""; mark_dirty())
		if tab == t[0]:
			b.add_theme_color_override("font_color", UI.ACCENT)
		tabs.add_child(b)
	tabs.add_child(UI.spacer())
	_search_box = LineEdit.new()
	_search_box.placeholder_text = "Search…"
	_search_box.text = search
	_search_box.custom_minimum_size.x = 220
	_search_box.text_changed.connect(func(t): search = t.to_lower(); _rebuild_list())
	tabs.add_child(_search_box)
	add_child(tabs)
	if picked_recipe != "":
		_build_pick_building()
		return
	var v := UI.vbox(4)
	v.name = "list"
	add_child(UI.scroll(v))
	_fill(v)


func _rebuild_list() -> void:
	var s := find_child("list", true, false)
	if s:
		UI.clear(s)
		_fill(s)


func _fill(v: VBoxContainer) -> void:
	if tab == "products":
		_fill_recipes(v)
	else:
		_fill_facilities(v, tab == "power")


func _fill_recipes(v: VBoxContainer) -> void:
	var cats := {}
	for r in Content.recipe_list:
		if not Game.unlocked_recipes.has(r.id):
			continue
		if search != "" and not (r.name.to_lower().contains(search) or _outputs_match(r)):
			continue
		cats.get_or_add(r.category, []).append(r)
	var order := cats.keys()
	order.sort()
	for c in order:
		v.add_child(UI.label(c.capitalize().to_upper(), 15, UI.ACCENT, "head_bold"))
		for r in cats[c]:
			var rid: String = r.id
			var h := row(v, func(): _pick(rid))
			h.add_child(UI.icon(Content.icon(Content.recipe_main_output(rid)), 40))
			var tv := UI.vbox(2)
			tv.add_child(UI.label(r.name, 18, UI.TEXT, "head"))
			tv.add_child(recipe_line(r, -1.0, 24))
			tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			h.add_child(tv)
			var have := 0
			for l in Game.lines:
				if l.recipe == rid:
					have += l.count
			if have > 0:
				h.add_child(UI.label("×%d" % have, 16, UI.DIM))
	if cats.is_empty():
		v.add_child(UI.label("Nothing matches.", 16, UI.DIM))


func _outputs_match(r: Dictionary) -> bool:
	for o in r.get("outputs", {}):
		if Content.item_name(o).to_lower().contains(search):
			return true
	return false


func _building_unlocked(bid: String) -> bool:
	for rid in Content.recipes_by_output.get(bid, []):
		if Game.unlocked_recipes.has(rid):
			return true
	return Game.inv.get(bid, 0.0) >= 1.0 or Game.facility_line(bid) != null


func _fill_facilities(v: VBoxContainer, power: bool) -> void:
	var roles := {}
	for b in Content.building_list:
		var role: String = b.get("role", "producer")
		if role == "producer":
			continue
		if power != (role == "generator" or b.has("capacity_kj")):
			continue
		if not _building_unlocked(b.id):
			continue
		if search != "" and not b.name.to_lower().contains(search):
			continue
		roles.get_or_add(role, []).append(b)
	if power:
		# boilers are producers but belong in the power tab
		for b in Content.building_list:
			if "boiling" in b.get("categories", []) or "fission" in b.get("categories", []) or "fusion" in b.get("categories", []):
				if _building_unlocked(b.id):
					roles.get_or_add("steam & heat", []).append(b)
	for role in roles:
		v.add_child(UI.label(role.capitalize().to_upper(), 15, UI.ACCENT, "head_bold"))
		for b in roles[role]:
			var bid: String = b.id
			var h := row(v, func(): _create_facility(bid))
			h.add_child(UI.icon(Content.icon(bid), 48))
			var tv := UI.vbox(0)
			tv.add_child(UI.label(b.name, 18, UI.TEXT, "head"))
			tv.add_child(UI.label(_facility_summary(b), 14, UI.DIM))
			var d := UI.label(b.get("desc", ""), 13, UI.DIM)
			d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			tv.add_child(d)
			tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			h.add_child(tv)
			var fl := Game.facility_line(bid)
			h.add_child(UI.label("×%d" % (fl.count if fl else 0), 16, UI.DIM))


static func _facility_summary(b: Dictionary) -> String:
	var parts: Array = []
	if b.has("power_out_kw"):
		parts.append("+" + Fmt.power(float(b.power_out_kw)))
	if float(b.get("power_kw", 0)) > 0:
		parts.append("uses " + Fmt.power(float(b.power_kw)))
	if b.has("capacity_kj"):
		parts.append("stores " + Fmt.energy(float(b.capacity_kj)))
	if b.has("storage_slots"):
		parts.append("+%s storage" % Fmt.num(float(b.storage_slots)))
	if b.has("defense"):
		parts.append("defense %s" % Fmt.num(float(b.defense)))
	if b.get("role", "") == "research":
		parts.append("research speed %s" % Fmt.num(float(b.get("speed", 1))))
	if b.has("categories") and not b.categories.is_empty():
		parts.append("speed %s" % Fmt.num(float(b.get("speed", 1))))
	return "  ·  ".join(parts)


func _create_facility(bid: String) -> void:
	var b: Dictionary = Content.buildings[bid]
	var l: ProdLine
	if b.get("role", "producer") == "producer":
		l = Game.add_line(bid, Game.default_recipe_for(bid))
	else:
		l = Game.facility_line(bid)
		if l == null:
			l = Game.add_line(bid, "")
	if l:
		Game.line_add(l.uid, 1)
		hud.open("line", l.uid)
		hud.view.focus_line(l.uid)


func _pick(rid: String) -> void:
	var bs: Array = Content.buildings_for_recipe(rid).filter(func(x): return _building_unlocked(x))
	if bs.size() == 1:
		_create(rid, bs[0])
		return
	picked_recipe = rid
	mark_dirty()


func _build_pick_building() -> void:
	var r: Dictionary = Content.recipes[picked_recipe]
	var hh := UI.hbox()
	hh.add_child(UI.button("← Back", func(): picked_recipe = ""; mark_dirty()))
	hh.add_child(UI.label(r.name, 22, UI.TEXT, "head"))
	add_child(hh)
	add_child(recipe_line(r, -1.0, 32))
	section("Choose a building")
	var v := UI.vbox(4)
	add_child(UI.scroll(v))
	var any := false
	for bid in Content.buildings_for_recipe(picked_recipe):
		if not _building_unlocked(bid):
			continue
		any = true
		var b: Dictionary = Content.buildings[bid]
		var h := row(v, func(): _create(picked_recipe, bid))
		h.add_child(UI.icon(Content.icon(bid), 56))
		var tv := UI.vbox(0)
		tv.add_child(UI.label(b.name, 19, UI.TEXT, "head"))
		var rate: float = float(b.get("speed", 1)) / float(r.get("time", 1)) * 60.0
		var energy: String = ("burner " + Fmt.power(float(b.get("fuel_kw", 0)))) if b.get("burner", false) else Fmt.power(float(b.get("power_kw", 0)))
		tv.add_child(UI.label("%s crafts/min each  ·  %s  ·  modules %d" % [Fmt.num(rate), energy, int(b.get("module_slots", 0))], 14, UI.DIM))
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(tv)
		h.add_child(UI.label("in storage: %d" % int(Game.inv.get(bid, 0)), 14, UI.DIM))
	if not any:
		v.add_child(UI.label("No building for this recipe is unlocked yet.", 16, UI.WARN))


func _create(rid: String, bid: String) -> void:
	var l := Game.add_line(bid, rid)
	if l:
		Game.line_add(l.uid, 1)
		picked_recipe = ""
		mark_dirty()
		hud.open("line", l.uid)
		hud.view.focus_line(l.uid)
