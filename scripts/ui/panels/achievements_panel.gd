extends BasePanel
## Achievements with progress.


func _init() -> void:
	title = "Achievements"


func build() -> void:
	add_child(UI.label("%d / %d unlocked" % [Game.achievements_done.size(), Content.achievements.size()], 16, UI.DIM))
	var v := UI.vbox(3)
	add_child(UI.scroll(v))
	var list: Array = Content.achievements.duplicate()
	list.sort_custom(func(a, b): return int(Game.achievements_done.has(a.id)) > int(Game.achievements_done.has(b.id)))
	for a in list:
		var done := Game.achievements_done.has(a.id)
		var h := row(v)
		h.add_child(UI.label("★" if done else "☆", 26, UI.ACCENT if done else UI.DIM))
		var tv := UI.vbox(0)
		tv.add_child(UI.label(a.get("name", a.id), 17, UI.TEXT if done else UI.DIM, "head"))
		var d := UI.label(a.get("desc", ""), 13, UI.DIM)
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		tv.add_child(d)
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(tv)
		if not done:
			var p := Game.achievement_progress(a.get("condition", {}))
			if p.y > 1:
				var bar := UI.bar(minf(p.x, p.y), p.y, UI.ACCENT, 6)
				bar.custom_minimum_size.x = 120
				bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				bar.tooltip_text = "%s / %s" % [Fmt.num(p.x), Fmt.num(p.y)]
				h.add_child(bar)
