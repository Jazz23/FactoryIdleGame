class_name MachineSprite
extends Node2D
## One building on the factory floor: animated sprite sheet + glow lights + particle emitters.
## Position = ground point of the footprint centre (y-sorted by this).

var building := ""
var sprite: Sprite2D
var frames := 1
var fps := 10.0
var lights: Array = []
var light_base: Array = []
var emitters: Array = []
var placeholder := false
var _t := 0.0
var _seed := 0.0


func setup(bid: String, seed := 0.0) -> void:
	building = bid
	_seed = seed
	var sheet := Content.building_sheet(bid)
	if sheet.is_empty():
		_make_placeholder()
		return
	var meta: Dictionary = sheet.meta
	sprite = Sprite2D.new()
	sprite.texture = sheet.texture
	sprite.centered = false
	frames = int(meta.get("frames", 1))
	var cols := int(meta.get("columns", 1))
	sprite.hframes = cols
	sprite.vframes = int(ceil(float(frames) / cols))
	var origin: Array = meta.get("origin", [0, 0])
	sprite.offset = Vector2(-float(origin[0]), -float(origin[1]))
	fps = float(meta.get("fps", 10))
	add_child(sprite)
	for ld in meta.get("lights", []):
		var c: Array = ld.get("color", [1, 0.6, 0.2])
		var px: Array = ld.get("px", [0, 0])
		var l := FX.make_light(Color(c[0], c[1], c[2]), float(ld.get("energy", 1.0)) * 0.9, 1.1)
		l.position = Vector2(px[0], px[1])
		l.set_meta("flicker", ld.get("flicker", false))
		add_child(l)
		lights.append(l)
		light_base.append(l.energy)
	for ed in meta.get("emitters", []):
		var px: Array = ed.get("px", [0, 0])
		var e := FX.make_emitter(ed.get("type", "smoke"))
		e.position = Vector2(px[0], px[1])
		e.z_index = 2
		add_child(e)
		emitters.append(e)


func _make_placeholder() -> void:
	placeholder = true
	var b: Dictionary = Content.buildings.get(building, {})
	var sz: Array = b.get("size", [2, 2])
	var w := float(sz[0]) * 0.9
	var d := float(sz[1]) * 0.9
	var h := 0.8 + 0.25 * (w + d)
	var col := Color.from_hsv(float(hash(b.get("role", "x") + str(b.get("tier", 0))) % 360) / 360.0, 0.25, 0.55)
	var p := func(x: float, y: float, z: float) -> Vector2:
		return Vector2((x + y) * 64.0, (x - y) * 32.0 - z * 78.4)
	var top := Polygon2D.new()
	top.polygon = PackedVector2Array([p.call(-w/2, -d/2, h), p.call(w/2, -d/2, h), p.call(w/2, d/2, h), p.call(-w/2, d/2, h)])
	top.color = col.lightened(0.25)
	var left := Polygon2D.new()
	left.polygon = PackedVector2Array([p.call(-w/2, -d/2, 0), p.call(w/2, -d/2, 0), p.call(w/2, -d/2, h), p.call(-w/2, -d/2, h)])
	left.color = col
	var right := Polygon2D.new()
	right.polygon = PackedVector2Array([p.call(w/2, -d/2, 0), p.call(w/2, d/2, 0), p.call(w/2, d/2, h), p.call(w/2, -d/2, h)])
	right.color = col.darkened(0.35)
	add_child(left); add_child(right); add_child(top)
	var lbl := Label.new()
	lbl.text = b.get("name", building)
	lbl.add_theme_font_size_override("font_size", 22)
	lbl.position = p.call(0, 0, h) + Vector2(-80, -40)
	lbl.custom_minimum_size = Vector2(160, 0)
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(lbl)


func animate(activity: float, phase: float, delta: float) -> void:
	_t += delta
	if sprite and frames > 1:
		var f := int(floor((phase + _seed) * fps)) % frames
		sprite.frame = f
	var on := activity > 0.05
	for i in lights.size():
		var l: PointLight2D = lights[i]
		var e: float = light_base[i] * (0.25 + 0.75 * activity)
		if l.get_meta("flicker", false):
			e *= 0.85 + 0.15 * sin(_t * 13.0 + _seed * 7.0) * sin(_t * 7.3 + 1.7)
		l.energy = e
	for e in emitters:
		e.emitting = on
