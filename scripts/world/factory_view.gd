class_name FactoryView
extends Node2D
## Isometric factory floor. Each production line is a painted "bay" with its machines,
## an output conveyor carrying product icons, and a status sign.

signal bay_clicked(uid: int)
signal empty_clicked

const TW := 64.0         # half tile width in px
const TH := 32.0         # half tile height
const ZPX := 78.4        # px per metre of height
const BAY_W := 11.0
const BAY_D := 6.0
const AISLE_X := 2.5
const AISLE_Y := 2.5
const MAX_SHOWN := 6

var floor_sprite: Sprite2D
var ground: Node2D       # flat decals (markings, deposits, belts)
var sorted: Node2D       # y-sorted machines
var signs: Node2D
var camera: Camera2D
var modulate_node: CanvasModulate
var bays: Dictionary = {}   # uid -> Dictionary of nodes
var _dragging := false
var _drag_moved := false
var _drag_start := Vector2.ZERO
var _cam_target_zoom := 0.55
var _belt_mat: ShaderMaterial
var hover_uid := -1


static func iso(x: float, y: float, z := 0.0) -> Vector2:
	return Vector2((x + y) * TW, (x - y) * TH - z * ZPX)


static func uniso(p: Vector2) -> Vector2:
	# inverse of iso at z = 0
	var a := p.x / TW
	var b := p.y / TH
	return Vector2((a + b) * 0.5, (a - b) * 0.5)


func _ready() -> void:
	modulate_node = CanvasModulate.new()
	modulate_node.color = Color(0.78, 0.78, 0.8)
	add_child(modulate_node)
	floor_sprite = Sprite2D.new()
	var ft := Content.env_texture("floor_tile")
	if ft:
		floor_sprite.texture = ft
		floor_sprite.region_enabled = true
		floor_sprite.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
		floor_sprite.region_rect = Rect2(0, 0, 1024 * 24, 512 * 48)
		floor_sprite.centered = true
		floor_sprite.z_index = -10
	add_child(floor_sprite)
	ground = Node2D.new()
	ground.z_index = -5
	add_child(ground)
	sorted = Node2D.new()
	sorted.y_sort_enabled = true
	add_child(sorted)
	signs = Node2D.new()
	signs.z_index = 50
	add_child(signs)
	camera = Camera2D.new()
	camera.zoom = Vector2(_cam_target_zoom, _cam_target_zoom)
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 10.0
	add_child(camera)
	camera.make_current()
	_belt_mat = ShaderMaterial.new()
	_belt_mat.shader = load("res://scripts/world/belt.gdshader")
	_add_hall_lights()
	Game.lines_changed.connect(rebuild)
	Game.line_updated.connect(_on_line_updated)
	Game.state_reset.connect(rebuild)
	rebuild()
	center_on_bays()


func _add_hall_lights() -> void:
	# overhead high-bay lamps: pools of warm light across the floor
	for i in range(-2, 9):
		for j in range(-8, 3):
			var l := FX.make_light(Color(1.0, 0.9, 0.75), 0.42, 9.0)
			l.position = iso(i * 14.0 + 6.0, j * 9.5 - 3.5)
			l.z_index = -1
			ground.add_child(l)


const DEPARTMENTS := [
	["power", "Power Plant"], ["extraction", "Extraction"], ["smelting", "Smelting & Casting"],
	["processing", "Metalworking"], ["assembly", "Assembly"], ["electronics", "Electronics"],
	["chemistry", "Chemical Works"], ["nuclear", "Nuclear & Fusion"], ["research", "Research"],
	["logistics", "Logistics & Storage"], ["defense", "Defense"], ["orbital", "Orbital Works"],
]
const CAT_DEPT := {
	"mining": "extraction", "pumping": "extraction", "oil_extraction": "extraction",
	"smelting": "smelting", "smelting_advanced": "smelting", "foundry": "smelting",
	"crushing": "processing", "pressing": "processing", "recycling": "processing", "mixing": "processing",
	"assembling": "assembly", "munitions": "assembly",
	"precision_assembling": "electronics", "electronics": "electronics", "nanofab": "electronics",
	"chemistry": "chemistry", "refining": "chemistry", "electrolysis": "chemistry", "cryogenics": "chemistry", "bioprocessing": "chemistry",
	"centrifuging": "nuclear", "fission": "nuclear", "fusion": "nuclear",
	"boiling": "power", "orbital": "orbital",
}
const PER_ROW := 6

var layout: Dictionary = {}      # uid -> Vector2 bay origin
var dept_labels: Array = []


static func department(l: ProdLine) -> String:
	var role: String = l.spec().get("role", "producer")
	match role:
		"generator": return "power"
		"research": return "research"
		"storage", "logistics", "support": return "logistics"
		"defense": return "defense"
		"megaproject": return "orbital"
	if l.recipe != "":
		return CAT_DEPT.get(Content.recipes.get(l.recipe, {}).get("category", ""), "assembly")
	var cats: Array = l.spec().get("categories", [])
	return CAT_DEPT.get(cats[0] if not cats.is_empty() else "", "assembly")


func _compute_layout() -> void:
	layout.clear()
	for n in dept_labels:
		n.queue_free()
	dept_labels.clear()
	var by_dept := {}
	for l in Game.lines:
		by_dept.get_or_add(department(l), []).append(l)
	var row := 0
	for d in DEPARTMENTS:
		if not by_dept.has(d[0]):
			continue
		var ls: Array = by_dept[d[0]]
		var rows_needed := int(ceil(float(ls.size()) / PER_ROW))
		var lbl := UI.label(d[1].to_upper(), 64, Color(0.95, 0.75, 0.3, 0.55), "head_bold")
		var ln := Node2D.new()
		ln.add_child(lbl)
		# paint the department name flat on the floor in the aisle in front of the row
		var y0 := -row * (BAY_D + AISLE_Y) - BAY_D - 0.25
		ln.transform = Transform2D(Vector2(1, 0.5), Vector2(-1, 0.5), iso(0.2, y0))
		lbl.position = Vector2.ZERO
		ground.add_child(ln)
		dept_labels.append(ln)
		for i in ls.size():
			var r := row + i / PER_ROW
			var c := i % PER_ROW
			layout[ls[i].uid] = Vector2(c * (BAY_W + AISLE_X), -r * (BAY_D + AISLE_Y) - BAY_D)
		row += rows_needed


func bay_origin_of(uid: int) -> Vector2:
	return layout.get(uid, Vector2.ZERO)


func rebuild() -> void:
	for uid in bays:
		_free_bay(bays[uid])
	bays.clear()
	_compute_layout()
	for l in Game.lines:
		_build_bay(l)


func _free_bay(b: Dictionary) -> void:
	for k in ["ground", "machines", "sign"]:
		if b.has(k):
			for n in b[k]:
				if is_instance_valid(n):
					n.queue_free()


func _on_line_updated(uid: int) -> void:
	var l: ProdLine = Game.get_line(uid)
	if l == null:
		return
	if bays.has(uid):
		_free_bay(bays[uid])
	_build_bay(l)


func _build_bay(l: ProdLine) -> void:
	var o := bay_origin_of(l.uid)
	var b := {"ground": [], "machines": [], "sign": [], "line": l, "items": []}
	var spec: Dictionary = l.spec()
	var size: Array = spec.get("size", [2, 2])
	var bw := float(size[0])
	var bd := float(size[1])
	# --- floor paint
	var outline := PackedVector2Array([iso(o.x, o.y), iso(o.x + BAY_W, o.y), iso(o.x + BAY_W, o.y + BAY_D), iso(o.x, o.y + BAY_D), iso(o.x, o.y)])
	var fill := Polygon2D.new()
	fill.polygon = outline
	fill.color = Color(0.0, 0.0, 0.0, 0.10)
	ground.add_child(fill)
	b.ground.append(fill)
	var line := Line2D.new()
	line.points = outline
	line.width = 5.0
	line.default_color = Color(0.85, 0.62, 0.1, 0.55)
	line.joint_mode = Line2D.LINE_JOINT_SHARP
	ground.add_child(line)
	b.ground.append(line)
	# --- floor wear & aisle clutter (deterministic per line)
	var rnd := RandomNumberGenerator.new()
	rnd.seed = hash(l.uid * 7919 + 13)
	for k in rnd.randi_range(1, 3):
		var dk: String = ["decal_oil_0", "decal_oil_1", "decal_grime_0", "decal_grime_1", "decal_rust_0", "decal_rust_1", "decal_puddle_0", "decal_puddle_1"][rnd.randi() % 8]
		var dn := _env_sprite(dk)
		if dn:
			dn.position = iso(o.x + rnd.randf_range(1.0, BAY_W - 1.0), o.y + rnd.randf_range(0.8, BAY_D - 0.8))
			dn.z_index = -1
			dn.modulate.a = rnd.randf_range(0.6, 1.0)
			ground.add_child(dn)
			b.ground.append(dn)
	if rnd.randf() < 0.35:
		var drn := _env_sprite("decal_drain_0")
		if drn:
			drn.position = iso(o.x + BAY_W + AISLE_X * 0.5, o.y + rnd.randf_range(1.0, BAY_D - 1.0))
			ground.add_child(drn)
			b.ground.append(drn)
	if rnd.randf() < 0.55:
		var pk: String = ["prop_pallet", "prop_drums", "prop_gas_cage", "prop_toolcart", "prop_bollards", "prop_pallet", "prop_forklift"][rnd.randi() % 7]
		var pn := _env_sprite(pk)
		if pn:
			var ps := Node2D.new()
			ps.position = iso(o.x + BAY_W + AISLE_X * 0.5, o.y + rnd.randf_range(1.2, BAY_D - 1.2))
			pn.position = Vector2.ZERO
			ps.add_child(pn)
			sorted.add_child(ps)
			b.ground.append(ps)
	# --- deposit patch for extraction lines
	var rs: Dictionary = l.recipe_spec()
	if rs.has("deposit"):
		var ds := Content.deposit_sprite(rs.deposit)
		if not ds.is_empty():
			var s := Sprite2D.new()
			s.texture = ds.texture
			s.centered = false
			var org: Array = ds.meta.get("origin", [ds.texture.get_width() / 2, ds.texture.get_height() / 2])
			s.offset = Vector2(-org[0], -org[1])
			s.position = iso(o.x + BAY_W * 0.45, o.y + BAY_D * 0.62)
			s.scale = Vector2(1.6, 1.6)
			ground.add_child(s)
			b.ground.append(s)
	# --- machines
	var gap := 0.5
	var fit := maxi(1, int(floor((BAY_W - 1.0) / (bw + gap))))
	var shown := mini(l.count, mini(fit, MAX_SHOWN))
	var my := o.y + 1.4 + bd / 2.0
	if bd > BAY_D - 2.0:
		my = o.y + BAY_D - bd / 2.0
	for i in shown:
		var m := MachineSprite.new()
		var mx := o.x + 0.8 + bw / 2.0 + i * (bw + gap)
		m.position = iso(mx, my)
		sorted.add_child(m)
		m.setup(l.building, float(i) * 0.37)
		b.machines.append(m)
	if l.count == 0:
		var ghost := MachineSprite.new()
		ghost.position = iso(o.x + 0.8 + bw / 2.0, my)
		ghost.modulate = Color(1, 1, 1, 0.25)
		sorted.add_child(ghost)
		ghost.setup(l.building)
		b.machines.append(ghost)
	# --- output belt along the -Y edge
	var out_item := Content.recipe_main_output(l.recipe) if l.recipe != "" else ""
	if out_item != "":
		var y0 := o.y + 0.55
		var poly := Polygon2D.new()
		poly.polygon = PackedVector2Array([iso(o.x + 0.3, y0 - 0.32), iso(o.x + BAY_W + AISLE_X * 0.5, y0 - 0.32), iso(o.x + BAY_W + AISLE_X * 0.5, y0 + 0.32), iso(o.x + 0.3, y0 + 0.32)])
		poly.uv = PackedVector2Array([Vector2(0, 0), Vector2(BAY_W, 0), Vector2(BAY_W, 1), Vector2(0, 1)])
		poly.material = _belt_mat.duplicate()
		poly.color = Color(1, 1, 1)
		ground.add_child(poly)
		b.ground.append(poly)
		b.belt = poly
		var tex := Content.icon(out_item)
		for k in 6:
			var s := Sprite2D.new()
			s.texture = tex
			var px := 26.0 / maxf(1.0, tex.get_width())
			s.scale = Vector2(px, px)
			ground.add_child(s)
			b.ground.append(s)
			b.items.append(s)
		b.belt_y = y0
	# --- positional machine sound
	if shown > 0 and not b.machines.is_empty():
		var arch: String = spec.get("visual", {}).get("archetype", "")
		var snd := AudioStreamPlayer2D.new()
		snd.stream = Sound.stream(Sound.loop_for(arch), true)
		snd.bus = "Machines"
		snd.max_distance = 2200.0
		snd.attenuation = 2.2
		snd.position = b.machines[0].position
		snd.volume_db = -80.0
		ground.add_child(snd)
		if snd.stream:
			snd.play(randf() * 2.0)
		b.ground.append(snd)
		b.sound = snd
	# --- sign
	var sign := _make_sign(l)
	sign.position = iso(o.x, o.y + BAY_D) + Vector2(-10, -40)
	signs.add_child(sign)
	b.sign.append(sign)
	b.origin = o
	bays[l.uid] = b


var _env_cache := {}


func _env_sprite(key: String) -> Sprite2D:
	if not _env_cache.has(key):
		var tex := Content.env_texture(key)
		var org := Vector2.ZERO
		var mp := "res://assets/env/" + key + ".json"
		if tex and FileAccess.file_exists(mp):
			var m = JSON.parse_string(FileAccess.get_file_as_string(mp))
			if m is Dictionary and m.has("origin"):
				org = Vector2(m.origin[0], m.origin[1])
		_env_cache[key] = [tex, org]
	var e: Array = _env_cache[key]
	if e[0] == null:
		return null
	var s := Sprite2D.new()
	s.texture = e[0]
	s.centered = false
	s.offset = -e[1]
	return s


func _make_sign(l: ProdLine) -> Control:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.055, 0.06, 0.82), Color(0.85, 0.62, 0.1, 0.6), 4, 8))
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var h := UI.hbox(8)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(h)
	var out_item := Content.recipe_main_output(l.recipe) if l.recipe != "" else l.building
	var ic := UI.icon(Content.icon(out_item), 44)
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(ic)
	var v := UI.vbox(0)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(v)
	var t := UI.label(l.title(), 22, UI.TEXT, "head")
	v.add_child(t)
	var sub := UI.label("", 17, UI.DIM)
	sub.name = "sub"
	v.add_child(sub)
	var dot := ColorRect.new()
	dot.custom_minimum_size = Vector2(10, 10)
	dot.name = "dot"
	dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(dot)
	p.set_meta("sub", sub)
	p.set_meta("dot", dot)
	return p


func _process(delta: float) -> void:
	_handle_keys(delta)
	var z := lerpf(camera.zoom.x, _cam_target_zoom, 1.0 - exp(-delta * 12.0))
	camera.zoom = Vector2(z, z)
	var dl := Game.daylight()
	modulate_node.color = Color(0.62, 0.64, 0.7).lerp(Color(0.8, 0.79, 0.78), dl)
	for uid in bays:
		var b: Dictionary = bays[uid]
		var l: ProdLine = b.line
		var act := l.activity if l.enabled else 0.0
		for m in b.machines:
			if m is MachineSprite:
				m.animate(act, l.anim_phase * (0.5 + 0.5 * act) + 0.0, delta)
		if b.has("belt"):
			var o: Vector2 = b.origin
			var n: int = b.items.size()
			var span := BAY_W + AISLE_X * 0.5 - 0.6
			for k in n:
				var t := fmod(l.anim_phase * 0.9 + float(k) / n, 1.0)
				var s: Sprite2D = b.items[k]
				s.position = iso(o.x + 0.6 + t * span, b.belt_y, 0.12)
				s.visible = l.count > 0 and (act > 0.02 or Game.inv.get(Content.recipe_main_output(l.recipe), 0.0) > 0)
			((b.belt as Polygon2D).material as ShaderMaterial).set_shader_parameter("offset", l.anim_phase * 0.9 * (BAY_W + AISLE_X * 0.5 - 0.6))
		if b.has("sound"):
			var snd: AudioStreamPlayer2D = b.sound
			var target_db := linear_to_db(0.02 + 0.5 * act * clampf(float(b.machines.size()) / 3.0, 0.4, 1.0)) - 4.0
			snd.volume_db = lerpf(snd.volume_db, target_db, 1.0 - exp(-delta * 4.0))
		if not b.sign.is_empty():
			var sg: Control = b.sign[0]
			var sub: Label = sg.get_meta("sub")
			var dot: ColorRect = sg.get_meta("dot")
			var txt := "×%d" % l.count
			if l.kind() == ProdLine.Kind.PRODUCER and l.recipe != "":
				var out := Content.recipe_main_output(l.recipe)
				var amt := float(l.recipe_spec().get("outputs", {}).get(out, 1.0))
				txt += "   " + Fmt.rate(l.crafts_per_sec * amt)
			elif l.kind() == ProdLine.Kind.GENERATOR:
				txt += "   " + Fmt.power(float(l.spec().get("power_out_kw", 0)) * l.count * l.activity)
			sub.text = txt
			dot.color = UI.status_color(l.status) if l.count > 0 else UI.DIM
			var sc := clampf(0.75 / camera.zoom.x, 1.0, 3.2)
			sg.scale = Vector2(sc, sc)
			sg.modulate.a = 1.0 if hover_uid == uid or camera.zoom.x > 0.22 else 0.0


func _handle_keys(delta: float) -> void:
	var v := Vector2.ZERO
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): v.x -= 1
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): v.x += 1
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): v.y -= 1
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): v.y += 1
	if v != Vector2.ZERO and get_viewport().gui_get_focus_owner() == null:
		camera.position += v.normalized() * 900.0 * delta / camera.zoom.x


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_at(1.12, mb.position)
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_at(1.0 / 1.12, mb.position)
		elif mb.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE]:
			if mb.pressed:
				_dragging = true
				_drag_moved = false
				_drag_start = mb.position
			else:
				if _dragging and not _drag_moved and mb.button_index == MOUSE_BUTTON_LEFT:
					var uid := bay_at(get_global_mouse_position())
					if uid >= 0:
						emit_signal("bay_clicked", uid)
					else:
						emit_signal("empty_clicked")
				_dragging = false
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if _dragging:
			if mm.position.distance_to(_drag_start) > 6.0:
				_drag_moved = true
			if _drag_moved:
				camera.position -= mm.relative / camera.zoom.x
		else:
			hover_uid = bay_at(get_global_mouse_position())
	elif event is InputEventMagnifyGesture:
		_zoom_at((event as InputEventMagnifyGesture).factor, get_viewport().get_mouse_position())
	elif event is InputEventPanGesture:
		camera.position += (event as InputEventPanGesture).delta * 20.0 / camera.zoom.x


func _zoom_at(f: float, screen_pos: Vector2) -> void:
	var before := get_global_mouse_position()
	_cam_target_zoom = clampf(_cam_target_zoom * f, 0.18, 1.6)
	camera.zoom = Vector2(_cam_target_zoom, _cam_target_zoom)
	var after := get_global_mouse_position()
	camera.position += before - after


func bay_at(world_pos: Vector2) -> int:
	var t := uniso(world_pos)
	for uid in bays:
		var o: Vector2 = bays[uid].origin
		if t.x >= o.x and t.x <= o.x + BAY_W and t.y >= o.y and t.y <= o.y + BAY_D:
			return uid
	return -1


func center_on_bays() -> void:
	if Game.lines.is_empty():
		camera.position = Vector2.ZERO
		return
	var mn := Vector2(INF, INF)
	var mx := Vector2(-INF, -INF)
	for l in Game.lines:
		var o := bay_origin_of(l.uid)
		for c in [iso(o.x, o.y), iso(o.x + BAY_W, o.y + BAY_D), iso(o.x + BAY_W, o.y), iso(o.x, o.y + BAY_D)]:
			mn = mn.min(c)
			mx = mx.max(c)
	camera.position = (mn + mx) * 0.5 + Vector2(160, 0)
	camera.reset_smoothing()


func focus_line(uid: int) -> void:
	if not bays.has(uid):
		return
	var o: Vector2 = bays[uid].origin
	camera.position = iso(o.x + BAY_W * 0.5, o.y + BAY_D * 0.5) + Vector2(200, 0)
	_cam_target_zoom = maxf(_cam_target_zoom, 0.6)
