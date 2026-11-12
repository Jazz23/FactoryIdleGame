extends BasePanel
## Megaprojects and prestige (Legacy).


func _init() -> void:
	title = "Megaprojects"


func build() -> void:
	var lp := UI.panel(Color(0.12, 0.1, 0.06, 0.95), UI.ACCENT.darkened(0.4), 12)
	var lv := UI.vbox(4)
	lp.add_child(lv)
	lv.add_child(UI.label("LEGACY", 14, UI.ACCENT, "head_bold"))
	lv.add_child(UI.label("Legacy points: %s  →  +%d%% speed, +%d%% market prices" % [Fmt.num(Game.legacy), int(Game.legacy * 2), int(Game.legacy * 5)], 16))
	var final_name := ""
	if not Content.megaprojects.is_empty():
		final_name = Content.megaprojects[-1].get("name", "")
	var info := UI.label("Complete the %s to found a new legacy: the factory resets, but you keep Legacy points and achievements. Next reset grants %s points." % [final_name, Fmt.num(Game.legacy_gain())], 13, UI.DIM)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lv.add_child(info)
	var pb := UI.accent_button("Found new legacy", func(): Game.prestige(); mark_dirty())
	pb.disabled = not Game.can_prestige()
	lv.add_child(pb)
	add_child(lp)
	var v := UI.vbox(8)
	add_child(UI.scroll(v))
	for m in Content.megaprojects:
		var mid: String = m.id
		var st := Game.mega_state(mid)
		var stages: Array = m.get("stages", [])
		var done := Game.megas_completed.has(mid)
		var p := UI.panel(Color(0.1, 0.105, 0.115, 0.95), UI.GOOD.darkened(0.5) if done else UI.LINE, 12)
		var pv := UI.vbox(5)
		p.add_child(pv)
		var h := UI.hbox()
		h.add_child(UI.label(m.get("name", mid), 22, UI.TEXT, "head_bold"))
		h.add_child(UI.spacer())
		h.add_child(UI.label("COMPLETE" if done else "Stage %d / %d" % [mini(st.stage + 1, stages.size()), stages.size()], 15, UI.GOOD if done else UI.ACCENT, "head_bold"))
		pv.add_child(h)
		var d := UI.label(m.get("desc", ""), 14, UI.DIM)
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		pv.add_child(d)
		var sh := UI.hbox(3)
		for i in stages.size():
			var c := ColorRect.new()
			c.custom_minimum_size = Vector2(0, 8)
			c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			c.color = UI.GOOD if i < st.stage or done else (UI.ACCENT if i == st.stage else Color(0.2, 0.2, 0.22))
			c.tooltip_text = stages[i].get("name", "")
			sh.add_child(c)
		pv.add_child(sh)
		if not done and st.stage < stages.size():
			var stage: Dictionary = stages[st.stage]
			pv.add_child(UI.label(stage.get("name", ""), 18, UI.TEXT, "head"))
			if stage.get("desc", "") != "":
				var sd := UI.label(stage.desc, 13, UI.DIM)
				sd.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				pv.add_child(sd)
			var req: Dictionary = stage.get("requires", {})
			for it in req:
				var rh := UI.hbox()
				rh.add_child(UI.icon(Content.icon(it), 30))
				rh.add_child(UI.label(Content.item_name(it), 15))
				rh.add_child(UI.spacer())
				var dl := float(st.delivered.get(it, 0.0))
				rh.add_child(UI.label("%s / %s  (have %s)" % [Fmt.num(dl), Fmt.num(float(req[it])), Fmt.num(Game.inv.get(it, 0.0))], 14, UI.GOOD if dl >= float(req[it]) else UI.TEXT))
				var bar := UI.bar(dl, float(req[it]), UI.ACCENT, 6)
				bar.custom_minimum_size.x = 120
				bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				rh.add_child(bar)
				pv.add_child(rh)
			pv.add_child(UI.accent_button("Contribute from storage", func(): Game.mega_contribute(mid); mark_dirty()))
		if m.has("reward"):
			pv.add_child(UI.label("Reward: " + str(m.reward), 13, UI.GOOD))
		v.add_child(p)
