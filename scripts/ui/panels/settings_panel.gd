extends BasePanel
## Settings, save management and credits.

var _confirm := false


func _init() -> void:
	title = "Settings"


func build() -> void:
	section("Game")
	var h := UI.hbox()
	h.add_child(UI.button("Save now", func(): Game.save_game(); Game.emit_signal("notify", "Game saved.", "info")))
	var w := UI.button("Reset everything…" if not _confirm else "Click again to WIPE save", func():
		if _confirm:
			Game.wipe_save()
			_confirm = false
		else:
			_confirm = true
		mark_dirty()
	)
	w.add_theme_color_override("font_color", UI.BAD)
	h.add_child(w)
	add_child(h)
	add_child(UI.label("Autosaves every 30 s. Offline progress: %s%% efficiency, up to %s." % [int((Game.OFFLINE_BASE_EFF + float(Game.bonuses.get("offline_efficiency", 0))) * 100), Fmt.duration(Game.offline_cap_hours() * 3600)], 14, UI.DIM))
	section("Audio")
	for bus in ["Master", "Ambience", "Machines", "SFX"]:
		var h2 := UI.hbox()
		var lb := UI.label(bus, 15)
		lb.custom_minimum_size.x = 110
		h2.add_child(lb)
		var sl := HSlider.new()
		sl.min_value = 0.0
		sl.max_value = 1.0
		sl.step = 0.01
		sl.value = Sound.volumes.get(bus, 0.8)
		sl.custom_minimum_size.x = 300
		sl.focus_mode = Control.FOCUS_NONE
		var bname: String = bus
		sl.value_changed.connect(func(v): Sound.set_volume(bname, v))
		h2.add_child(sl)
		add_child(h2)
	section("Display")
	var fs := CheckBox.new()
	fs.text = "Fullscreen"
	fs.button_pressed = DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	fs.toggled.connect(func(on): DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if on else DisplayServer.WINDOW_MODE_WINDOWED))
	add_child(fs)
	section("Controls")
	var c := UI.label("Drag (any mouse button) or WASD / arrows to pan · mouse wheel to zoom · click a bay to inspect it\nHotkeys: F factory · B build · R research · M market · C contracts · T frontier · P power · I storage · Esc close", 14, UI.DIM)
	c.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(c)
	section("Credits")
	var cr := UI.label("Industrium — an idle megafactory.\nArt: procedurally modelled and rendered in Blender Cycles.\nTextures & HDRIs: Poly Haven and ambientCG (CC0).\nFonts: Barlow & Barlow Condensed (SIL Open Font License).\nEngine: Godot.", 14, UI.DIM)
	cr.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(cr)
