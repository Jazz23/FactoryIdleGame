extends Node
## Root: builds the world view, post-processing layer and HUD.

var view: FactoryView
var hud: HUD


func _ready() -> void:
	var cf := ConfigFile.new()
	if cf.load("user://settings.cfg") == OK:
		get_tree().root.content_scale_factor = float(cf.get_value("display", "ui_scale", 1.0))
	for a in OS.get_cmdline_user_args():
		if a == "--smoke":
			add_child(load("res://tests/smoke_test.gd").new())
			return
		if a.begins_with("--autoplay"):
			var scr = load("res://tests/autoplay.gd")
			if scr == null or not scr.can_instantiate():
				push_error("autoplay script failed to load")
				get_tree().quit(1)
				return
			add_child(scr.new())
			return
	view = FactoryView.new()
	add_child(view)
	var fx_layer := CanvasLayer.new()
	fx_layer.layer = 1
	add_child(fx_layer)
	var grade := ColorRect.new()
	grade.set_anchors_preset(Control.PRESET_FULL_RECT)
	grade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = load("res://scripts/world/vignette.gdshader")
	grade.material = mat
	fx_layer.add_child(grade)
	var ui_layer := CanvasLayer.new()
	ui_layer.layer = 2
	add_child(ui_layer)
	hud = HUD.new()
	hud.view = view
	ui_layer.add_child(hud)
	view.bay_clicked.connect(func(uid): hud.open("line", uid); view.focus_line(uid))
	_handle_cli()
	if Game.play_time < 5.0 and not " ".join(OS.get_cmdline_user_args()).contains("--shot"):
		hud.show_intro()


func _handle_cli() -> void:
	# --shot=<path> [--panel=<key>] [--frames=N] : render a screenshot for automated visual checks
	var args := OS.get_cmdline_user_args()
	var shot := ""
	var frames := 20
	for a in args:
		if a.begins_with("--shot="):
			shot = a.substr(7)
		elif a.begins_with("--panel="):
			hud.open(a.substr(8))
		elif a.begins_with("--frames="):
			frames = int(a.substr(9))
		elif a.begins_with("--zoom="):
			view._cam_target_zoom = float(a.substr(7))
		elif a.begins_with("--line="):
			hud.open("line", Game.lines[int(a.substr(7))].uid)
		elif a == "--intro":
			hud.show_intro()
		elif a == "--tree":
			hud.open_tree()
		elif a == "--fresh":
			Game.new_game(false)
			for c in hud.get_children():
				if c is ColorRect:
					c.queue_free()
	if shot != "":
		for i in frames:
			await get_tree().process_frame
		var img := get_viewport().get_texture().get_image()
		img.save_png(shot)
		print("SHOT ", shot)
		get_tree().quit()
