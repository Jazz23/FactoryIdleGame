extends Node
## Audio manager (autoload "Sound"): hall ambience, event sfx, volume settings.
## Machine loops are positional AudioStreamPlayer2D nodes created by FactoryView via loop_for().

const DIR := "res://assets/audio/"
const ARCH_LOOP := {
	"drill": "loop_drill", "gas_well": "loop_drill", "pumpjack": "loop_drill", "crusher": "loop_drill", "water_pump": "loop_drill",
	"burner_furnace": "loop_furnace", "electric_furnace": "loop_furnace", "arc_furnace": "loop_furnace", "foundry": "loop_furnace", "boiler": "loop_furnace",
	"press": "loop_press", "rolling_mill": "loop_press", "wire_drawer": "loop_press",
	"assembler": "loop_servo", "precision_assembler": "loop_servo", "electronics_fab": "loop_servo", "nanofab": "loop_servo", "munitions_plant": "loop_servo", "orbital_assembler": "loop_servo",
	"chemical_plant": "loop_bubbling", "refinery": "loop_bubbling", "mixer": "loop_bubbling", "electrolyzer": "loop_bubbling", "bioreactor": "loop_bubbling", "cryo_plant": "loop_bubbling",
	"steam_engine": "loop_turbine", "steam_turbine": "loop_turbine", "gas_turbine": "loop_turbine", "wind_turbine": "loop_turbine", "centrifuge": "loop_turbine",
	"cooling_tower": "loop_steam", "heat_exchanger": "loop_steam", "geothermal_plant": "loop_steam", "scrubber": "loop_steam",
}

var _streams := {}
var _ambience: AudioStreamPlayer
var _sfx_pool: Array = []
var volumes := {"Master": 0.8, "Ambience": 0.7, "Machines": 0.8, "SFX": 0.8}
var _last_play := {}


func _ready() -> void:
	for bus in ["Ambience", "Machines", "SFX"]:
		if AudioServer.get_bus_index(bus) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, "Master")
	var mi := AudioServer.get_bus_index("Machines")
	var rev := AudioEffectReverb.new()
	rev.room_size = 0.85
	rev.damping = 0.4
	rev.wet = 0.18
	rev.dry = 0.9
	AudioServer.add_bus_effect(mi, rev)
	_load_settings()
	_apply_volumes()
	_ambience = AudioStreamPlayer.new()
	_ambience.bus = "Ambience"
	_ambience.stream = stream("ambience_hall", true)
	_ambience.volume_db = -6.0
	add_child(_ambience)
	if _ambience.stream:
		_ambience.play()
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_sfx_pool.append(p)
	Game.tech_completed.connect(func(_t): play("sfx_research", -4.0))
	Game.notify.connect(_on_notify)
	Game.built.connect(func(_u, _n): play("sfx_build", -6.0))
	Game.sold.connect(func(_i, c): if c > 0.0: play("sfx_coins", -10.0))


func _on_notify(_text: String, kind: String) -> void:
	match kind:
		"achievement": play("sfx_achievement", -3.0)
		"bad": play("sfx_alarm", -8.0)


func stream(name: String, loop := false) -> AudioStream:
	var key := name + ("_l" if loop else "")
	if _streams.has(key):
		return _streams[key]
	var s: AudioStream = null
	var path := DIR + name + ".ogg"
	if ResourceLoader.exists(path):
		s = load(path)
		if s and loop:
			s = s.duplicate()
			s.set("loop", true)
	_streams[key] = s
	return s


func play(name: String, db := 0.0) -> void:
	var now := Time.get_ticks_msec()
	if now - int(_last_play.get(name, 0)) < 60:
		return
	_last_play[name] = now
	var s := stream(name)
	if s == null:
		return
	for p in _sfx_pool:
		if not p.playing:
			p.stream = s
			p.volume_db = db
			p.play()
			return


func loop_for(archetype: String) -> String:
	return ARCH_LOOP.get(archetype, "loop_hum")


func set_volume(bus: String, v: float) -> void:
	volumes[bus] = clampf(v, 0.0, 1.0)
	_apply_volumes()
	_save_settings()


func _apply_volumes() -> void:
	for bus in volumes:
		var i := AudioServer.get_bus_index(bus)
		if i >= 0:
			AudioServer.set_bus_volume_db(i, linear_to_db(maxf(0.0001, volumes[bus])))
			AudioServer.set_bus_mute(i, volumes[bus] <= 0.001)


func _load_settings() -> void:
	var cf := ConfigFile.new()
	if cf.load("user://settings.cfg") == OK:
		for bus in volumes:
			volumes[bus] = float(cf.get_value("audio", bus, volumes[bus]))


func _save_settings() -> void:
	var cf := ConfigFile.new()
	cf.load("user://settings.cfg")
	for bus in volumes:
		cf.set_value("audio", bus, volumes[bus])
	cf.save("user://settings.cfg")
