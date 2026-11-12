extends BasePanel
## Production statistics: live rates and lifetime totals.

var _list: VBoxContainer
var mode := "rates"


func _init() -> void:
	title = "Statistics"


func build() -> void:
	var g := GridContainer.new()
	g.columns = 4
	g.add_theme_constant_override("h_separation", 24)
	var items := [
		["Play time", Fmt.duration(Game.play_time)], ["Lifetime credits", Fmt.credits(Game.lifetime_credits)],
		["Technologies", "%d / %d" % [Game.researched.size(), Content.tech_list.size()]], ["Production lines", str(Game.lines.size())],
		["Sectors", "%d / %d" % [Game.sectors_claimed.size(), Content.sectors.size()]], ["Contracts", str(Game.contracts_done)],
		["Achievements", "%d / %d" % [Game.achievements_done.size(), Content.achievements.size()]], ["Legacy", "%s (×%d)" % [Fmt.num(Game.legacy), Game.prestige_count]],
	]
	for it in items:
		g.add_child(UI.label(it[0], 14, UI.DIM))
		g.add_child(UI.label(it[1], 16, UI.TEXT, "head_bold"))
	add_child(g)
	var tabs := UI.hbox(4)
	for t in [["rates", "Live rates"], ["lifetime", "Lifetime produced"]]:
		var b := UI.button(t[1], func(): mode = t[0]; mark_dirty())
		if mode == t[0]:
			b.add_theme_color_override("font_color", UI.ACCENT)
		tabs.add_child(b)
	add_child(tabs)
	var hdr := UI.hbox()
	hdr.add_child(UI.label("Item", 13, UI.DIM))
	hdr.add_child(UI.spacer())
	hdr.add_child(UI.label("Produced" if mode == "rates" else "Total", 13, UI.DIM))
	if mode == "rates":
		var c := UI.label("Consumed", 13, UI.DIM)
		c.custom_minimum_size.x = 110
		c.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		hdr.add_child(c)
		var n := UI.label("Net", 13, UI.DIM)
		n.custom_minimum_size.x = 110
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		hdr.add_child(n)
	add_child(hdr)
	_list = UI.vbox(2)
	add_child(UI.scroll(_list))


func refresh() -> void:
	if _list == null:
		return
	UI.clear(_list)
	var keys: Array = []
	if mode == "rates":
		var s := {}
		for k in Game.rates_prod:
			if Game.rates_prod[k] > 1e-4:
				s[k] = true
		for k in Game.rates_cons:
			if Game.rates_cons[k] > 1e-4:
				s[k] = true
		keys = s.keys()
		keys.sort_custom(func(a, b): return Game.rates_prod.get(a, 0.0) * Content.item_value(a) > Game.rates_prod.get(b, 0.0) * Content.item_value(b))
	else:
		keys = Game.stats_produced.keys()
		keys.sort_custom(func(a, b): return Game.stats_produced[a] * Content.item_value(a) > Game.stats_produced[b] * Content.item_value(b))
	for k in keys.slice(0, 80):
		var h := UI.hbox()
		h.add_child(UI.icon(Content.icon(k), 26))
		h.add_child(UI.label(Content.item_name(k), 15))
		h.add_child(UI.spacer())
		if mode == "rates":
			var p := float(Game.rates_prod.get(k, 0.0))
			var c := float(Game.rates_cons.get(k, 0.0))
			for val in [[p, UI.GOOD], [c, UI.WARN], [p - c, UI.GOOD if p >= c else UI.BAD]]:
				var l := UI.label(Fmt.rate(val[0]), 15, val[1])
				l.custom_minimum_size.x = 110
				l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
				h.add_child(l)
		else:
			h.add_child(UI.label(Fmt.num(float(Game.stats_produced[k])), 15))
		_list.add_child(h)
	if keys.is_empty():
		_list.add_child(UI.label("Nothing produced yet.", 15, UI.DIM))
