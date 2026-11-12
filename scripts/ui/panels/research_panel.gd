extends BasePanel
## Research: current tech, queue, and the browsable tech list.

var filter := "available"
var search := ""
var _cur_bar: ProgressBar
var _cur_lbl: Label
var _list: VBoxContainer


func _init() -> void:
	title = "Research"


func build() -> void:
	var cur := Game.current_research()
	var cp := UI.panel(Color(0.08, 0.1, 0.13, 0.95), UI.RESEARCH.darkened(0.5), 12)
	var cv := UI.vbox(4)
	cp.add_child(cv)
	if cur != "":
		var t: Dictionary = Content.techs[cur]
		cv.add_child(UI.label("RESEARCHING", 13, UI.RESEARCH, "head_bold"))
		cv.add_child(UI.label(t.name, 22, UI.TEXT, "head_bold"))
		_cur_bar = UI.bar(0, 1, UI.RESEARCH, 12)
		cv.add_child(_cur_bar)
		_cur_lbl = UI.label("", 14, UI.DIM)
		cv.add_child(_cur_lbl)
	else:
		cv.add_child(UI.label("No active research — pick a technology below.", 17, UI.WARN))
	var labs := Game.lab_speed()
	cv.add_child(UI.label("Lab throughput: %s research/s" % Fmt.num(labs), 14, UI.DIM if labs > 0 else UI.BAD))
	if Game.research_queue.size() > 1:
		var qh := UI.hbox(4)
		qh.add_child(UI.label("Queue:", 14, UI.DIM))
		for i in range(1, mini(Game.research_queue.size(), 9)):
			var tid: String = Game.research_queue[i]
			var qb := UI.button(Content.techs[tid].name, func(): Game.dequeue_research(tid))
			qb.tooltip_text = "Click to remove from queue"
			qb.add_theme_font_size_override("font_size", 13)
			qh.add_child(qb)
		var qs := ScrollContainer.new()
		qs.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		qs.custom_minimum_size.y = 40
		qs.add_child(qh)
		cv.add_child(qs)
	add_child(cp)
	var tabs := UI.hbox(4)
	for f in [["available", "Available"], ["all", "All"], ["done", "Completed"]]:
		var b := UI.button(f[1], func(): filter = f[0]; mark_dirty())
		if filter == f[0]:
			b.add_theme_color_override("font_color", UI.ACCENT)
		tabs.add_child(b)
	tabs.add_child(UI.spacer())
	var se := LineEdit.new()
	se.placeholder_text = "Search…"
	se.text = search
	se.custom_minimum_size.x = 200
	se.text_changed.connect(func(t): search = t.to_lower(); _fill())
	tabs.add_child(se)
	var done_n := 0
	for tid in Game.researched:
		done_n += 1
	tabs.add_child(UI.label("%d / %d" % [done_n, Content.tech_list.size()], 14, UI.DIM))
	add_child(tabs)
	_list = UI.vbox(4)
	add_child(UI.scroll(_list))
	_fill()


func _fill() -> void:
	UI.clear(_list)
	var shown := 0
	for t in Content.tech_list:
		var tid: String = t.id
		var avail := Game.tech_available(tid)
		var done := Game.tech_done(tid)
		match filter:
			"available":
				if not avail:
					continue
			"done":
				if not Game.researched.has(tid):
					continue
		if search != "" and not (t.name.to_lower().contains(search) or _unlock_match(t)):
			continue
		shown += 1
		if shown > 200:
			break
		_list.add_child(tech_card(t, avail, done))
	if shown == 0:
		_list.add_child(UI.label("Nothing here.", 16, UI.DIM))


func _unlock_match(t: Dictionary) -> bool:
	for r in t.get("unlocks", []):
		if Content.recipes.get(r, {}).get("name", "").to_lower().contains(search):
			return true
	return false


func tech_card(t: Dictionary, avail: bool, done: bool) -> Control:
	var tid: String = t.id
	var bg := Color(0.1, 0.12, 0.1, 0.9) if done else (Color(0.11, 0.12, 0.135, 0.95) if avail else Color(0.08, 0.08, 0.085, 0.9))
	var p := UI.panel(bg, (UI.GOOD.darkened(0.5) if done else (UI.RESEARCH.darkened(0.5) if avail else UI.LINE)), 8)
	var v := UI.vbox(3)
	p.add_child(v)
	var h := UI.hbox(8)
	h.add_child(UI.label("T%d" % int(t.get("tier", 0)), 14, UI.ACCENT, "head_bold"))
	var nm: String = t.name
	if t.get("repeatable", false):
		nm += "  (level %d)" % (Game.tech_level(tid) + 1)
	h.add_child(UI.label(nm, 19, UI.TEXT if avail or done else UI.DIM, "head"))
	h.add_child(UI.spacer())
	if done:
		h.add_child(UI.label("✓ Done", 15, UI.GOOD))
	elif avail:
		h.add_child(UI.button("Queue", func(): Game.queue_research(tid); mark_dirty()))
		h.add_child(UI.accent_button("Research", func(): Game.queue_research(tid, true); mark_dirty()))
	else:
		h.add_child(UI.button("Queue path", func(): Game.queue_research(tid); mark_dirty()))
	v.add_child(h)
	if t.get("desc", "") != "":
		var d := UI.label(t.desc, 13, UI.DIM)
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(d)
	var ch := UI.hbox(4)
	for it in t.get("cost", {}):
		ch.add_child(UI.item_chip(it, float(t.cost[it]), 22))
	ch.add_child(UI.label("× %s units  ·  %ss each" % [Fmt.num(Game.tech_units(tid)), Fmt.num(float(t.get("time", 10)))], 13, UI.DIM))
	v.add_child(ch)
	var uh := UI.hbox(3)
	var ul: Array = t.get("unlocks", [])
	if not ul.is_empty():
		uh.add_child(UI.label("Unlocks:", 13, UI.DIM))
		for r in ul:
			var ic := UI.icon(Content.icon(Content.recipe_main_output(r)), 26)
			ic.tooltip_text = Content.recipes.get(r, {}).get("name", r)
			uh.add_child(ic)
	for e in t.get("effects", []):
		uh.add_child(UI.label(_effect_text(e), 13, UI.GOOD))
	if uh.get_child_count() > 0:
		v.add_child(uh)
	if not avail and not done:
		var pre: Array = []
		for pr in t.get("prereqs", []):
			if not Game.researched.has(pr):
				pre.append(Content.techs.get(pr, {}).get("name", pr))
		if not pre.is_empty():
			v.add_child(UI.label("Requires: " + ", ".join(pre), 13, UI.WARN.darkened(0.2)))
	return p


static func _effect_text(e: Dictionary) -> String:
	var typ: String = e.get("type", "")
	var v := float(e.get("value", 0))
	var tgt = e.get("target")
	var t := typ.replace("_", " ").capitalize()
	if tgt != null and str(tgt) != "":
		t += " (" + str(tgt).replace("_", " ") + ")"
	if typ in ["module_slots"]:
		return "%s +%d" % [t, int(v)]
	if typ == "extraction_slots":
		return "%s +%s" % [t, Fmt.num(v)]
	return "%s %s" % [t, Fmt.signed_pct(v)]


func refresh() -> void:
	var cur := Game.current_research()
	if _cur_bar and is_instance_valid(_cur_bar) and cur != "":
		_cur_bar.max_value = Game.tech_units(cur)
		_cur_bar.value = Game.research_progress
		var speed := Game.lab_speed()
		var remain := (Game.tech_units(cur) - Game.research_progress) * float(Content.techs[cur].get("time", 10)) / maxf(speed, 0.0001)
		_cur_lbl.text = "%s / %s units   ·   ETA %s" % [Fmt.num(Game.research_progress), Fmt.num(Game.tech_units(cur)), Fmt.duration(remain) if speed > 0 else "∞ (no labs)"]
