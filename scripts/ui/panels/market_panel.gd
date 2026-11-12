extends BasePanel
## Market: sell stock (price falls with saturation and recovers), buy unlocked items, auto-sell overflow.

var tab := "sell"
var search := ""
var _rows := []
var _list: VBoxContainer
var _since := 0.0


func _init() -> void:
	title = "Market"


func build() -> void:
	var tabs := UI.hbox(4)
	for t in [["sell", "Sell"], ["buy", "Buy"]]:
		var b := UI.button(t[1], func(): tab = t[0]; mark_dirty())
		if tab == t[0]:
			b.add_theme_color_override("font_color", UI.ACCENT)
		tabs.add_child(b)
	tabs.add_child(UI.spacer())
	var se := LineEdit.new()
	se.placeholder_text = "Search…"
	se.text = search
	se.custom_minimum_size.x = 220
	se.text_changed.connect(func(t): search = t.to_lower(); _fill())
	tabs.add_child(se)
	add_child(tabs)
	var note := "Prices drop as you flood the market and recover over a few minutes. Market bonus: " + Fmt.signed_pct(Game.market_mult() - 1.0)
	var nl := UI.label(note, 13, UI.DIM)
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(nl)
	if tab == "sell":
		var h := UI.hbox()
		h.add_child(UI.accent_button("Sell all surplus (keep 25%)", _sell_surplus))
		add_child(h)
	_list = UI.vbox(3)
	add_child(UI.scroll(_list))
	_fill()


func _sell_surplus() -> void:
	var total := 0.0
	for it in Game.inv.keys():
		if Content.buildings.has(it) or Content.research_items.has(it):
			continue
		var n := floorf(float(Game.inv[it]) * 0.75)
		if n >= 1:
			total += Game.sell(it, n)
	Game.emit_signal("notify", "Sold surplus for " + Fmt.credits(total), "good")


func _fill() -> void:
	if _list == null:
		return
	UI.clear(_list)
	_rows.clear()
	var items: Array = []
	for it in Content.item_list:
		if search != "" and not it.name.to_lower().contains(search):
			continue
		if tab == "sell":
			if Game.inv.get(it.id, 0.0) < 1.0 and not Game.overflow_sell.has(it.id):
				continue
		else:
			if not Game.can_buy(it.id):
				continue
		items.append(it)
	if tab == "sell":
		items.sort_custom(func(a, b): return Game.inv.get(a.id, 0.0) * float(a.value) > Game.inv.get(b.id, 0.0) * float(b.value))
	for it in items.slice(0, 160):
		var id: String = it.id
		var h := row(_list)
		h.add_child(UI.icon(Content.icon(id), 38))
		var tv := UI.vbox(0)
		tv.add_child(UI.label(it.name, 17, UI.TEXT, "head"))
		var sub := UI.label("", 13, UI.DIM)
		tv.add_child(sub)
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(tv)
		if tab == "sell":
			var sat := UI.bar(0, 1, UI.BAD, 6)
			sat.custom_minimum_size.x = 60
			sat.tooltip_text = "Market saturation"
			sat.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			h.add_child(sat)
			h.add_child(UI.button("10", func(): Game.sell(id, 10)))
			h.add_child(UI.button("Half", func(): Game.sell(id, floorf(Game.inv.get(id, 0.0) * 0.5))))
			h.add_child(UI.button("All", func(): Game.sell(id, Game.inv.get(id, 0.0))))
			var cb := CheckBox.new()
			cb.text = "Auto"
			cb.tooltip_text = "Automatically sell production that would overflow storage"
			cb.button_pressed = Game.overflow_sell.has(id)
			cb.focus_mode = Control.FOCUS_NONE
			cb.toggled.connect(func(on):
				if on:
					Game.overflow_sell[id] = true
				else:
					Game.overflow_sell.erase(id)
			)
			h.add_child(cb)
			_rows.append([id, sub, sat])
		else:
			h.add_child(UI.button("1", func(): Game.buy(id, 1)))
			h.add_child(UI.button("10", func(): Game.buy(id, 10)))
			h.add_child(UI.button("100", func(): Game.buy(id, 100)))
			_rows.append([id, sub, null])
	if items.is_empty():
		_list.add_child(UI.label("Nothing to show.", 16, UI.DIM))
	refresh()


func refresh() -> void:
	for r in _rows:
		var id: String = r[0]
		var sub: Label = r[1]
		if tab == "sell":
			sub.text = "%s / %s   ·   %s each   ·   %s total" % [Fmt.num(Game.inv.get(id, 0.0)), Fmt.num(Game.cap(id)), Fmt.credits(Game.market_price(id)), Fmt.credits(Game.market_price(id) * Game.inv.get(id, 0.0))]
			(r[2] as ProgressBar).value = float(Game.market_sat.get(id, 0.0))
		else:
			sub.text = "Buy %s each   ·   have %s" % [Fmt.credits(Game.buy_price(id)), Fmt.num(Game.inv.get(id, 0.0))]
