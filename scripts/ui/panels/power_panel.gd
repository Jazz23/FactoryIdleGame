extends BasePanel
## Power grid overview.

var _lbls := {}
var _hist: Array = []
var _graph: Control


func _init() -> void:
	title = "Power"


func build() -> void:
	_lbls.clear()
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 30)
	for k in [["supply", "Supplied"], ["demand", "Demand"], ["capacity", "Available capacity"], ["sat", "Satisfaction"], ["accum", "Stored energy"], ["day", "Daylight / wind"]]:
		g.add_child(UI.label(k[1], 16, UI.DIM))
		var l := UI.label("", 18, UI.TEXT, "head_bold")
		g.add_child(l)
		_lbls[k[0]] = l
	add_child(g)
	section("Load history (last 2 min)")
	_graph = Control.new()
	_graph.custom_minimum_size = Vector2(0, 140)
	_graph.draw.connect(_draw_graph)
	add_child(_graph)
	section("Generation by source")
	var src := UI.vbox(2)
	src.name = "src"
	add_child(src)
	section("Generators & storage")
	var v := UI.vbox(3)
	add_child(UI.scroll(v))
	for l in Game.lines:
		var b: Dictionary = l.spec()
		if b.get("role", "") == "generator" or b.has("capacity_kj") or ("boiling" in b.get("categories", [])):
			var uid: int = l.uid
			var h := row(v, func(): hud.open("line", uid))
			h.add_child(UI.icon(Content.icon(l.building), 40))
			h.add_child(UI.label("%s ×%d" % [b.name, l.count], 17, UI.TEXT, "head"))
			h.add_child(UI.spacer())
			h.add_child(UI.label(UI.status_text(l.status, l.status_item), 14, UI.status_color(l.status)))
	add_child(UI.button("+ Add power generation", func(): var bp = hud.panel("build"); bp.tab = "power"; bp.mark_dirty(); hud.open("build")))


func refresh() -> void:
	if _lbls.is_empty():
		return
	var p: Dictionary = Game.power
	_lbls.supply.text = Fmt.power(p.supply)
	_lbls.demand.text = Fmt.power(p.demand)
	_lbls.capacity.text = Fmt.power(p.capacity)
	_lbls.sat.text = Fmt.pct(p.sat)
	_lbls.sat.add_theme_color_override("font_color", UI.GOOD if p.sat > 0.99 else UI.BAD)
	_lbls.accum.text = "%s / %s" % [Fmt.energy(p.accum), Fmt.energy(p.accum_cap)]
	_lbls.day.text = "%s / %s" % [Fmt.pct(Game.daylight()), Fmt.pct(Game._wind)]
	_hist.append([float(p.supply), float(p.demand), float(p.capacity)])
	if _hist.size() > 480:
		_hist.pop_front()
	_graph.queue_redraw()
	var src := find_child("src", true, false)
	if src:
		UI.clear(src)
		var bs: Dictionary = p.by_source
		for k in bs:
			var h := UI.hbox()
			h.add_child(UI.label(str(k).replace("_", " ").capitalize(), 15, UI.DIM))
			h.add_child(UI.spacer())
			h.add_child(UI.label(Fmt.power(bs[k]), 15))
			src.add_child(h)


func _draw_graph() -> void:
	var r := _graph.get_rect()
	_graph.draw_rect(Rect2(Vector2.ZERO, r.size), Color(0.03, 0.035, 0.04, 0.9))
	if _hist.size() < 2:
		return
	var m := 1.0
	for h in _hist:
		m = maxf(m, maxf(h[1], h[2]))
	var cols := [UI.GOOD, UI.BAD, UI.INFO.darkened(0.3)]
	for k in [2, 1, 0]:
		var pts := PackedVector2Array()
		for i in _hist.size():
			pts.append(Vector2(r.size.x * i / 479.0, r.size.y - r.size.y * 0.92 * _hist[i][k] / m))
		_graph.draw_polyline(pts, cols[k], 2.0, true)
