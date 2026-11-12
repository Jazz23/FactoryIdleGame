extends BasePanel
## Detail view for one production line.

var uid := -1
var _status: Label
var _count: Label
var _rates: VBoxContainer
var _buy_lbl: Label
var _bar: ProgressBar
var _power: Label


func _init() -> void:
	title = "Production line"


func set_arg(a) -> void:
	if int(a) != uid:
		uid = int(a)
		mark_dirty()


func _ready() -> void:
	super._ready()
	Game.line_updated.connect(func(u): if u == uid: mark_dirty())


func build() -> void:
	var l: ProdLine = Game.get_line(uid)
	if l == null:
		add_child(UI.label("Line removed.", 18, UI.DIM))
		return
	var b: Dictionary = l.spec()
	title = l.title()
	var head := UI.hbox(12)
	head.add_child(UI.icon(Content.icon(l.building), 96))
	var hv := UI.vbox(2)
	hv.add_child(UI.label(b.get("name", l.building), 24, UI.TEXT, "head_bold"))
	var desc := UI.label(b.get("desc", ""), 14, UI.DIM)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.custom_minimum_size.x = 420
	hv.add_child(desc)
	_status = UI.label("", 17)
	hv.add_child(_status)
	_bar = UI.bar(0, 1, UI.GOOD, 8)
	hv.add_child(_bar)
	hv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hv)
	add_child(head)
	# count controls
	var ch := UI.hbox(6)
	_count = UI.label("", 30, UI.TEXT, "head_bold")
	_count.custom_minimum_size.x = 90
	ch.add_child(_count)
	ch.add_child(UI.button("−10", func(): Game.line_remove(uid, 10)))
	ch.add_child(UI.button("−1", func(): Game.line_remove(uid, 1)))
	ch.add_child(UI.accent_button("+1", func(): Game.line_add(uid, 1), 70))
	ch.add_child(UI.button("+10", func(): Game.line_add(uid, 10)))
	ch.add_child(UI.button("+Max", func(): Game.line_add(uid, 1000)))
	add_child(ch)
	_buy_lbl = UI.label("", 14, UI.DIM)
	add_child(_buy_lbl)
	_power = UI.label("", 14, UI.DIM)
	add_child(_power)
	# recipe
	if l.kind() == ProdLine.Kind.PRODUCER:
		section("Recipe")
		var rh := UI.hbox()
		var opt := OptionButton.new()
		opt.focus_mode = Control.FOCUS_NONE
		var rids: Array = Content.recipes_for_building(l.building).filter(func(x): return Game.unlocked_recipes.has(x))
		for i in rids.size():
			opt.add_icon_item(Content.icon(Content.recipe_main_output(rids[i])), Content.recipes[rids[i]].name)
			opt.set_item_metadata(i, rids[i])
			if rids[i] == l.recipe:
				opt.select(i)
		opt.item_selected.connect(func(i): Game.set_line_recipe(uid, opt.get_item_metadata(i)); mark_dirty())
		opt.expand_icon = true
		opt.add_theme_constant_override("icon_max_width", 28)
		rh.add_child(opt)
		add_child(rh)
		if l.recipe != "":
			add_child(recipe_line(l.recipe_spec(), -1.0, 34))
			section("Throughput (actual)")
			_rates = UI.vbox(2)
			add_child(_rates)
		if b.get("burner", false):
			section("Fuel")
			var fh := UI.hbox()
			var fopt := OptionButton.new()
			fopt.focus_mode = Control.FOCUS_NONE
			fopt.add_item("Auto (best available)")
			fopt.set_item_metadata(0, "")
			var i := 1
			for it in Content.item_list:
				if it.has("fuel_kj") and it.get("fuel_class", "chemical") == "chemical" and not Content.buildings.has(it.id):
					fopt.add_icon_item(Content.icon(it.id), "%s (%s)" % [it.name, Fmt.energy(float(it.fuel_kj))])
					fopt.set_item_metadata(i, it.id)
					if it.id == l.fuel:
						fopt.select(i)
					i += 1
			fopt.expand_icon = true
			fopt.add_theme_constant_override("icon_max_width", 24)
			fopt.item_selected.connect(func(k): Game.get_line(uid).fuel = fopt.get_item_metadata(k))
			fh.add_child(fopt)
			add_child(fh)
	elif l.kind() == ProdLine.Kind.GENERATOR:
		section("Generator")
		var g: Dictionary = b.get("generator", {})
		var t := "Output %s each" % Fmt.power(float(b.get("power_out_kw", 0)))
		if g.has("fluid"):
			t += "  ·  consumes %s %s/s at full load" % [Fmt.num(float(g.get("rate", 0))), Content.item_name(g.fluid)]
		elif g.has("fuel_class"):
			t += "  ·  burns %s fuel (%s)" % [g.fuel_class, Fmt.power(float(g.get("fuel_kw", 0)))]
		elif g.has("source"):
			t += "  ·  " + str(g.source).capitalize() + " (variable)"
		add_child(UI.label(t, 15, UI.DIM))
		_rates = UI.vbox(2)
		add_child(_rates)
	# modules
	var slots := Game.module_slots(l)
	if slots > 0:
		section("Modules (%d/%d)" % [l.modules.size(), slots])
		var mh := UI.hbox(6)
		for i in l.modules.size():
			var idx := i
			var mb := Button.new()
			mb.icon = Content.icon(l.modules[i])
			mb.expand_icon = true
			mb.custom_minimum_size = Vector2(48, 48)
			mb.tooltip_text = Content.item_name(l.modules[i]) + "\nClick to remove"
			mb.pressed.connect(func(): Game.line_remove_module(uid, idx))
			mh.add_child(mb)
		add_child(mh)
		if l.modules.size() < slots:
			var avail := UI.hbox(4)
			var anymod := false
			for it in Content.item_list:
				if it.has("module") and Game.inv.get(it.id, 0.0) >= 1.0:
					anymod = true
					var mid: String = it.id
					var ab := Button.new()
					ab.icon = Content.icon(mid)
					ab.expand_icon = true
					ab.custom_minimum_size = Vector2(40, 40)
					ab.tooltip_text = "%s (have %d)\n%s" % [it.name, int(Game.inv[mid]), _module_desc(it.module)]
					ab.pressed.connect(func(): Game.line_add_module(uid, mid))
					avail.add_child(ab)
			if anymod:
				add_child(UI.label("Insert (one per building):", 14, UI.DIM))
				add_child(avail)
			else:
				add_child(UI.label("No modules in storage.", 14, UI.DIM))
	add_child(UI.spacer())
	var bot := UI.hbox()
	var en := UI.button("Pause" if l.enabled else "Resume", func(): Game.get_line(uid).enabled = not Game.get_line(uid).enabled; mark_dirty())
	bot.add_child(en)
	bot.add_child(UI.spacer())
	var rm := UI.button("Dismantle line", func(): Game.remove_line(uid); hud.open("factory"))
	rm.add_theme_color_override("font_color", UI.BAD)
	bot.add_child(rm)
	add_child(bot)


static func _module_desc(m: Dictionary) -> String:
	var p: Array = []
	for k in ["speed", "productivity", "energy", "pollution"]:
		if float(m.get(k, 0)) != 0:
			p.append("%s %s" % [k.capitalize(), Fmt.signed_pct(float(m[k]))])
	return ", ".join(p)


func refresh() -> void:
	var l: ProdLine = Game.get_line(uid)
	if l == null or _status == null:
		return
	_status.text = UI.status_text(l.status, l.status_item) if l.count > 0 else "No buildings — press +1"
	_status.add_theme_color_override("font_color", UI.status_color(l.status) if l.count > 0 else UI.DIM)
	_bar.value = l.activity
	_count.text = "×%d" % l.count
	var bp := Game.buy_price(l.building)
	var have := int(Game.inv.get(l.building, 0.0))
	_buy_lbl.text = "In storage: %d %s   ·   buy new: %s%s" % [have, Content.item_name(l.building), Fmt.credits(bp), "" if Game.can_buy(l.building) else " (tier locked)"]
	if l.recipe != "" and Content.is_extraction(l.recipe):
		var dep: String = l.recipe_spec().deposit
		_buy_lbl.text += "   ·   deposit slots %d/%d" % [Game.deposit_used(dep), Game.deposit_slots(dep)]
	var b: Dictionary = l.spec()
	if b.get("burner", false):
		_power.text = "Burner: %s fuel per building" % Fmt.power(float(b.get("fuel_kw", 0)))
	elif float(b.get("power_kw", 0)) > 0:
		_power.text = "Power draw: %s (max %s)" % [Fmt.power(l.power_draw), Fmt.power(float(b.power_kw) * l.count)]
	else:
		_power.text = ""
	if _rates and is_instance_valid(_rates):
		UI.clear(_rates)
		if l.kind() == ProdLine.Kind.PRODUCER and l.recipe != "":
			_rates.add_child(recipe_line(l.recipe_spec(), l.crafts_per_sec, 30))
		elif l.kind() == ProdLine.Kind.GENERATOR:
			_rates.add_child(UI.label("Producing %s (%s load)" % [Fmt.power(float(b.get("power_out_kw", 0)) * l.count * l.activity), Fmt.pct(l.activity)], 16))
