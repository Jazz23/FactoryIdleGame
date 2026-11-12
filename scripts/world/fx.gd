class_name FX
## Procedurally generated textures + particle presets for the world view.

static var _cache := {}


static func radial(size := 256, inner := Color(1, 1, 1, 1), outer := Color(1, 1, 1, 0), power := 1.6) -> Texture2D:
	var key := "radial_%d_%s_%s_%.2f" % [size, inner, outer, power]
	if _cache.has(key):
		return _cache[key]
	var g := Gradient.new()
	g.set_color(0, inner)
	g.set_color(1, outer)
	for i in 5:
		var t := float(i + 1) / 6.0
		g.add_point(t, inner.lerp(outer, pow(t, 1.0 / power)))
	var tex := GradientTexture2D.new()
	tex.gradient = g
	tex.width = size
	tex.height = size
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	_cache[key] = tex
	return tex


static func puff(size := 64) -> Texture2D:
	var key := "puff_%d" % size
	if _cache.has(key):
		return _cache[key]
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var noise := FastNoiseLite.new()
	noise.frequency = 0.08
	noise.fractal_octaves = 4
	for y in size:
		for x in size:
			var dx := (x - size / 2.0) / (size / 2.0)
			var dy := (y - size / 2.0) / (size / 2.0)
			var r := sqrt(dx * dx + dy * dy)
			var n := noise.get_noise_2d(x, y) * 0.5 + 0.5
			var a := clampf(1.0 - r, 0.0, 1.0)
			a = pow(a, 1.5) * clampf(0.55 + n * 0.7, 0.0, 1.0)
			img.set_pixel(x, y, Color(1, 1, 1, a))
	var tex := ImageTexture.create_from_image(img)
	_cache[key] = tex
	return tex


static func spark() -> Texture2D:
	return radial(16, Color(1, 1, 1, 1), Color(1, 0.8, 0.4, 0), 0.7)


static func make_emitter(kind: String) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.local_coords = false
	p.texture = puff()
	p.draw_order = CPUParticles2D.DRAW_ORDER_INDEX
	var curve := Curve.new()
	var ramp := Gradient.new()
	match kind:
		"steam":
			p.amount = 18
			p.lifetime = 3.2
			p.direction = Vector2(0.15, -1)
			p.spread = 12
			p.initial_velocity_min = 30
			p.initial_velocity_max = 50
			p.gravity = Vector2(6, -14)
			p.scale_amount_min = 0.5
			p.scale_amount_max = 0.8
			curve.add_point(Vector2(0, 0.4)); curve.add_point(Vector2(1, 2.6))
			ramp.set_color(0, Color(1, 1, 1, 0.0)); ramp.set_color(1, Color(1, 1, 1, 0))
			ramp.add_point(0.12, Color(0.95, 0.96, 0.98, 0.55))
			ramp.add_point(0.6, Color(0.9, 0.92, 0.95, 0.22))
		"fire":
			p.amount = 16
			p.lifetime = 0.8
			p.direction = Vector2(0, -1)
			p.spread = 18
			p.initial_velocity_min = 20
			p.initial_velocity_max = 40
			p.gravity = Vector2(0, -40)
			p.scale_amount_min = 0.25
			p.scale_amount_max = 0.45
			curve.add_point(Vector2(0, 1.0)); curve.add_point(Vector2(1, 0.2))
			ramp.set_color(0, Color(1, 0.9, 0.5, 0.9)); ramp.set_color(1, Color(0.6, 0.1, 0.0, 0))
			ramp.add_point(0.4, Color(1, 0.45, 0.1, 0.7))
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			p.material = mat
		"sparks":
			p.texture = spark()
			p.amount = 14
			p.lifetime = 0.7
			p.explosiveness = 0.6
			p.direction = Vector2(0.3, -1)
			p.spread = 60
			p.initial_velocity_min = 60
			p.initial_velocity_max = 140
			p.gravity = Vector2(0, 260)
			p.scale_amount_min = 0.3
			p.scale_amount_max = 0.6
			curve.add_point(Vector2(0, 1)); curve.add_point(Vector2(1, 0.3))
			ramp.set_color(0, Color(1, 0.95, 0.7, 1)); ramp.set_color(1, Color(1, 0.4, 0.05, 0))
			var mat2 := CanvasItemMaterial.new()
			mat2.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			p.material = mat2
		_: # smoke
			p.amount = 22
			p.lifetime = 4.5
			p.direction = Vector2(0.1, -1)
			p.spread = 10
			p.initial_velocity_min = 22
			p.initial_velocity_max = 36
			p.gravity = Vector2(5, -6)
			p.scale_amount_min = 0.45
			p.scale_amount_max = 0.7
			curve.add_point(Vector2(0, 0.35)); curve.add_point(Vector2(1, 3.0))
			ramp.set_color(0, Color(0.2, 0.19, 0.18, 0.0)); ramp.set_color(1, Color(0.35, 0.34, 0.33, 0))
			ramp.add_point(0.1, Color(0.16, 0.15, 0.14, 0.6))
			ramp.add_point(0.5, Color(0.3, 0.29, 0.28, 0.3))
	p.scale_amount_curve = curve
	p.color_ramp = ramp
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 4.0
	return p


static func make_light(color: Color, energy := 1.0, scale := 1.0) -> PointLight2D:
	var l := PointLight2D.new()
	l.texture = radial(256, Color(1, 1, 1, 1), Color(1, 1, 1, 0), 1.2)
	l.color = color
	l.energy = energy
	l.texture_scale = scale
	l.blend_mode = Light2D.BLEND_MODE_ADD
	return l
