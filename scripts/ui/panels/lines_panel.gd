extends BasePanel
## Factory overview: every production line with status, count and throughput.

var _rows := {}


func _init() -> void:
	title = "Factory"


func build() -> void:
	_rows.clear()
	var top := UI.hbox()
	top.add_child(UI.accent_button("+ New production line", func(): hud.open("build")))
	top.add_child(UI.spacer())
	top.add_child(UI.label("%d lines" % Game.lines.size(), 15, UI.DIM))
	add_child(top)
	var v := UI.vbox(4)
	add_child(UI.scroll(v))
	var groups := {"Power": [], "Extraction": [], "Production": [], "Research": [], "Facilities": []}
	for l in Game.lines:
		var role: String = l.spec().get("role", "producer")
		var g := "Production"
		if role == "generator":
			g = "Power"
		elif role == "research":
			g = "Research"
		elif role != "producer":
			g = "Facilities"
		elif l.recipe != "" and Content.is_extraction(l.recipe):
			g = "Extraction"
		elif l.recipe != "" and Content.recipes[l.recipe].category == "boiling":
			g = "Power"
		groups[g].append(l)
	for g in groups:
		if groups[g].is_empty():
			continue
		v.add_child(UI.label(g.to_upper(), 15, UI.ACCENT, "head_bold"))
		for l in groups[g]:
			var uid: int = l.uid
			var h := row(v, func(): hud.open("line", uid); hud.view.focus_line(uid))
			var out: String = Content.recipe_main_output(l.recipe) if l.recipe != "" else l.building
			h.add_child(UI.icon(Content.icon(l.building), 40))
			h.add_child(UI.icon(Content.icon(out), 30))
			var tv := UI.vbox(0)
			tv.add_child(UI.label(l.title(), 18, UI.TEXT, "head"))
			var st := UI.label("", 14, UI.DIM)
			tv.add_child(st)
			tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			h.add_child(tv)
			var cnt := UI.label("", 20, UI.TEXT, "head_bold")
			h.add_child(cnt)
			_rows[uid] = [st, cnt, l]


func refresh() -> void:
	for uid in _rows:
		var r: Array = _rows[uid]
		var l: ProdLine = r[2]
		var st: Label = r[0]
		var txt := UI.status_text(l.status, l.status_item) if l.count > 0 else "No buildings"
		if l.kind() == ProdLine.Kind.PRODUCER and l.recipe != "" and l.count > 0:
			var out := Content.recipe_main_output(l.recipe)
			txt += "  ·  " + Fmt.rate(l.crafts_per_sec * float(l.recipe_spec().outputs.get(out, 1)))
		elif l.kind() == ProdLine.Kind.GENERATOR:
			txt += "  ·  " + Fmt.power(float(l.spec().get("power_out_kw", 0)) * l.count * l.activity)
		st.text = txt
		st.add_theme_color_override("font_color", UI.status_color(l.status) if l.count > 0 else UI.DIM)
		(r[1] as Label).text = "×%d" % l.count
