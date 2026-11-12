class_name TechTree
extends Control
## Full-screen pannable technology graph. Columns = prerequisite depth.

const NODE_W := 230.0
const NODE_H := 64.0
const COL_GAP := 120.0
const ROW_GAP := 18.0

var hud
var canvas: Control
var pos: Dictionary = {}      # tech id -> Vector2
var nodes: Dictionary = {}    # tech id -> PanelContainer
var selected := ""
var detail: PanelContainer
var _drag := false
var _zoom := 1.0
var _search: LineEdit


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.035, 0.04, 1.0)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	clip_contents = true
	canvas = Control.new()
	canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.draw.connect(_draw_edges)
	add_child(canvas)
	var top := UI.hbox(10)
	top.position = Vector2(20, 80)
	top.add_child(UI.heading("Technology", 32))
	_search = LineEdit.new()
	_search.placeholder_text = "Find technology…"
	_search.custom_minimum_size.x = 280
	_search.text_submitted.connect(_find)
	top.add_child(_search)
	top.add_child(UI.label("drag to pan · wheel to zoom · click a node", 14, UI.DIM))
	top.add_child(UI.button("Close  [G]", func(): visible = false))
	add_child(top)
	detail = UI.panel(Color(0.06, 0.065, 0.07, 0.97), UI.RESEARCH.darkened(0.4), 14)
	detail.position = Vector2(20, 140)
	detail.custom_minimum_size = Vector2(460, 0)
	detail.visible = false
	add_child(detail)
	_layout()
	Game.research_changed.connect(_restyle)
	Game.tech_completed.connect(func(_t): _restyle())


func _layout() -> void:
	var depth := {}
	var get_depth := func(id: String, f: Callable) -> int:
		if depth.has(id):
			return depth[id]
		var d := 0
		for p in Content.techs.get(id, {}).get("prereqs", []):
			if Content.techs.has(p):
				d = maxi(d, f.call(p, f) + 1)
		depth[id] = d
		return d
	var cols := {}
	for t in Content.tech_list:
		var d: int = get_depth.call(t.id, get_depth)
		cols.get_or_add(d, []).append(t.id)
	var order := {}
	var keys := cols.keys()
	keys.sort()
	for c in keys:
		var ids: Array = cols[c]
		# barycentre ordering against previous column
		ids.sort_custom(func(a, b): return _bary(a, order) < _bary(b, order))
		for i in ids.size():
			order[ids[i]] = float(i)
			pos[ids[i]] = Vector2(80 + c * (NODE_W + COL_GAP), 160 + i * (NODE_H + ROW_GAP))
	for t in Content.tech_list:
		var n := _make_node(t)
		n.position = pos[t.id]
		canvas.add_child(n)
		nodes[t.id] = n
	var mx := Vector2.ZERO
	for p in pos.values():
		mx = mx.max(p)
	canvas.size = mx + Vector2(NODE_W + 200, NODE_H + 200)
	canvas.position = Vector2(500, 0)
	_restyle()


func _bary(id: String, order: Dictionary) -> float:
	var s := 0.0
	var n := 0
	for p in Content.techs[id].get("prereqs", []):
		if order.has(p):
			s += order[p]
			n += 1
	return s / n if n > 0 else 1e9 + hash(id) % 1000


func _make_node(t: Dictionary) -> PanelContainer:
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(NODE_W, NODE_H)
	p.size = Vector2(NODE_W, NODE_H)
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	var h := UI.hbox(6)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(h)
	var icon_id := ""
	for r in t.get("unlocks", []):
		icon_id = Content.recipe_main_output(r)
		break
	if icon_id == "":
		for c in t.get("cost", {}):
			icon_id = c
	var ic := UI.icon(Content.icon(icon_id), 44)
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(ic)
	var v := UI.vbox(0)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var nl := UI.label(t.name, 16, UI.TEXT, "head")
	nl.clip_text = true
	nl.custom_minimum_size.x = NODE_W - 70
	v.add_child(nl)
	var cost := UI.hbox(2)
	cost.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for c in t.get("cost", {}):
		var ci := UI.icon(Content.icon(c), 16)
		ci.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cost.add_child(ci)
	cost.add_child(UI.label("×%s" % Fmt.num(float(t.get("units", 1))), 12, UI.DIM))
	v.add_child(cost)
	h.add_child(v)
	var tid: String = t.id
	p.gui_input.connect(func(e):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			_select(tid)
			accept_event()
	)
	return p


func _restyle() -> void:
	var queued := {}
	for q in Game.research_queue:
		queued[q] = true
	var cur := Game.current_research()
	for id in nodes:
		var done := Game.researched.has(id)
		var avail := Game.tech_available(id)
		var col := UI.LINE
		var bg := Color(0.08, 0.085, 0.09)
		if done:
			col = UI.GOOD.darkened(0.3)
			bg = Color(0.07, 0.11, 0.07)
		elif id == cur:
			col = UI.RESEARCH
			bg = Color(0.07, 0.1, 0.15)
		elif queued.has(id):
			col = UI.RESEARCH.darkened(0.4)
		elif avail:
			col = UI.ACCENT.darkened(0.2)
			bg = Color(0.12, 0.11, 0.09)
		if id == selected:
			col = Color.WHITE
		nodes[id].add_theme_stylebox_override("panel", UI.box(bg, col, 5, 6, 2 if id == selected or id == cur else 1))
		nodes[id].modulate = Color(1, 1, 1, 1.0 if done or avail or queued.has(id) else 0.62)
	canvas.queue_redraw()


func _draw_edges() -> void:
	for t in Content.tech_list:
		var b: Vector2 = pos[t.id] + Vector2(0, NODE_H * 0.5)
		for p in t.get("prereqs", []):
			if not pos.has(p):
				continue
			var a: Vector2 = pos[p] + Vector2(NODE_W, NODE_H * 0.5)
			var done := Game.researched.has(p)
			var hl: bool = selected != "" and (t.id == selected or p == selected)
			var col := (UI.ACCENT if hl else (Color(0.35, 0.55, 0.35, 0.55) if done else Color(0.4, 0.42, 0.45, 0.35)))
			var mid := (a.x + b.x) * 0.5
			var pts := PackedVector2Array()
			for i in 17:
				var u := i / 16.0
				var x := lerpf(a.x, b.x, u)
				var y := lerpf(a.y, b.y, u * u * (3.0 - 2.0 * u))
				pts.append(Vector2(x, y))
			canvas.draw_polyline(pts, col, 3.0 if hl else 1.6, true)


func _select(tid: String) -> void:
	selected = tid
	_restyle()
	UI.clear(detail)
	detail.visible = true
	var rp = load("res://scripts/ui/panels/research_panel.gd").new()
	rp.hud = hud
	var card: Control = rp.tech_card(Content.techs[tid], Game.tech_available(tid), Game.tech_done(tid))
	rp.queue_free()
	detail.add_child(card)


func _find(text: String) -> void:
	text = text.to_lower()
	for t in Content.tech_list:
		if t.name.to_lower().contains(text):
			canvas.position = -pos[t.id] * _zoom + size * 0.5
			_select(t.id)
			return


func open() -> void:
	visible = true
	var cur := Game.current_research()
	var target := cur
	if target == "":
		for t in Content.tech_list:
			if Game.tech_available(t.id):
				target = t.id
				break
	if target != "":
		canvas.position = -pos[target] * _zoom + size * 0.5
	_restyle()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
			_drag = mb.pressed
		elif mb.pressed and mb.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			var f := 1.1 if mb.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.1
			var nz := clampf(_zoom * f, 0.35, 1.5)
			var local := (mb.position - canvas.position) / _zoom
			_zoom = nz
			canvas.scale = Vector2(_zoom, _zoom)
			canvas.position = mb.position - local * _zoom
	elif event is InputEventMouseMotion and _drag:
		canvas.position += (event as InputEventMouseMotion).relative
