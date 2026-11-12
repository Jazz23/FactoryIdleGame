extends BasePanel
## Rotating delivery contracts.

var _rows := []


func _init() -> void:
	title = "Contracts"


func build() -> void:
	_rows.clear()
	add_child(UI.label("Fulfilled: %d" % Game.contracts_done, 15, UI.DIM))
	var v := UI.vbox(8)
	add_child(UI.scroll(v))
	if Game.contracts_active.is_empty():
		v.add_child(UI.label("No contracts available yet.", 16, UI.DIM))
	for cid in Game.contracts_active:
		var c: Dictionary = Game.contract(cid)
		if c.is_empty():
			continue
		var p := UI.panel(Color(0.11, 0.115, 0.12, 0.95), UI.LINE, 12)
		var cv := UI.vbox(6)
		p.add_child(cv)
		var h := UI.hbox()
		h.add_child(UI.label(c.get("name", cid), 21, UI.TEXT, "head_bold"))
		h.add_child(UI.spacer())
		h.add_child(UI.label("T%d" % int(c.get("tier", 0)), 15, UI.ACCENT, "head_bold"))
		cv.add_child(h)
		if c.get("desc", "") != "":
			var d := UI.label(c.desc, 14, UI.DIM)
			d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			cv.add_child(d)
		var req := UI.vbox(2)
		var bars := []
		for it in c.get("requires", {}):
			var rh := UI.hbox()
			rh.add_child(UI.icon(Content.icon(it), 30))
			rh.add_child(UI.label(Content.item_name(it), 15))
			rh.add_child(UI.spacer())
			var lb := UI.label("", 15)
			rh.add_child(lb)
			var bar := UI.bar(0, float(c.requires[it]), UI.ACCENT, 6)
			bar.custom_minimum_size.x = 140
			bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			rh.add_child(bar)
			req.add_child(rh)
			bars.append([it, float(c.requires[it]), lb, bar])
		cv.add_child(req)
		var rw := UI.hbox()
		rw.add_child(UI.label("Reward: " + Fmt.credits(float(c.get("reward_credits", 0)) * Game.market_mult()), 17, UI.GOOD))
		for it in c.get("reward_items", {}):
			rw.add_child(UI.item_chip(it, float(c.reward_items[it]), 26, UI.GOOD))
		rw.add_child(UI.spacer())
		rw.add_child(UI.button("Reroll (%s)" % Fmt.credits(Game.reroll_cost()), func(): Game.reroll_contract(cid); mark_dirty()))
		var del := UI.accent_button("Deliver", func():
			if Game.fulfil_contract(cid):
				mark_dirty()
		)
		rw.add_child(del)
		cv.add_child(rw)
		v.add_child(p)
		_rows.append([bars, del])


func refresh() -> void:
	for r in _rows:
		var ok := true
		for b in r[0]:
			var have := float(Game.inv.get(b[0], 0.0))
			(b[2] as Label).text = "%s / %s" % [Fmt.num(minf(have, b[1])), Fmt.num(b[1])]
			(b[3] as ProgressBar).value = minf(have, b[1])
			if have < b[1]:
				ok = false
		(r[1] as Button).disabled = not ok
