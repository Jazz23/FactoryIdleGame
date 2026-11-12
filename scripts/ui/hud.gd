class_name HUD
extends Control
## Top bar, left navigation, right-hand panel host, toasts, modal dialogs.

const NAV := [
	["factory", "Factory", "F", "res://scripts/ui/panels/lines_panel.gd"],
	["build", "Build", "B", "res://scripts/ui/panels/build_panel.gd"],
	["research", "Research", "R", "res://scripts/ui/panels/research_panel.gd"],
	["market", "Market", "M", "res://scripts/ui/panels/market_panel.gd"],
	["contracts", "Contracts", "C", "res://scripts/ui/panels/contracts_panel.gd"],
	["frontier", "Frontier", "T", "res://scripts/ui/panels/frontier_panel.gd"],
	["power", "Power", "P", "res://scripts/ui/panels/power_panel.gd"],
	["storage", "Storage", "I", "res://scripts/ui/panels/storage_panel.gd"],
	["stats", "Statistics", "", "res://scripts/ui/panels/stats_panel.gd"],
	["mega", "Megaprojects", "", "res://scripts/ui/panels/mega_panel.gd"],
	["achievements", "Achievements", "", "res://scripts/ui/panels/achievements_panel.gd"],
	["settings", "Settings", "", "res://scripts/ui/panels/settings_panel.gd"],
]

var view: FactoryView
var top: PanelContainer
var nav: VBoxContainer
var host: PanelContainer
var host_title: Label
var host_body: MarginContainer
var toasts: VBoxContainer
var panels: Dictionary = {}
var current := ""
var current_panel: BasePanel
var nav_buttons: Dictionary = {}
var tree: TechTree
var _refresh_t := 0.0
# top bar widgets
var l_credits: Label
var l_credits_rate: Label
var l_power: Label
var b_power: ProgressBar
var l_research: Label
var b_research: ProgressBar
var l_threat: Label
var l_poll: Label
var l_day: Label


func _ready() -> void:
	theme = UI.theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_top()
	_build_nav()
	_build_host()
	var adv := Advisor.new()
	adv.hud = self
	adv.position = Vector2(10, 560)
	add_child(adv)
	toasts = UI.vbox(6)
	toasts.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	toasts.position = Vector2(330, -40)
	toasts.grow_vertical = Control.GROW_DIRECTION_BEGIN
	toasts.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(toasts)
	Game.notify.connect(toast)
	UI.on_item_clicked = func(it): open("item", it)
	Game.offline_report.connect(_on_offline)
	Game.lines_changed.connect(func(): _dirty(["factory", "build", "power", "storage"]))
	Game.research_changed.connect(func(): _dirty(["research"]))
	Game.tech_completed.connect(func(_t): _dirty(["research", "build", "market", "contracts"]))
	Game.sectors_changed.connect(func(): _dirty(["frontier", "build"]))
	Game.state_reset.connect(func(): _dirty(panels.keys()))


func _exit_tree() -> void:
	# static Callables must not outlive the HUD (avoids a crash at engine shutdown)
	UI.on_item_clicked = Callable()


func _build_top() -> void:
	top = PanelContainer.new()
	top.add_theme_stylebox_override("panel", UI.box(Color(0.045, 0.05, 0.055, 0.93), Color(0.2, 0.21, 0.22), 0, 14))
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.custom_minimum_size = Vector2(0, 66)
	add_child(top)
	var h := UI.hbox(26)
	top.add_child(h)
	var logo := UI.vbox(-6)
	logo.add_child(UI.label("INDUSTRIUM", 30, UI.ACCENT, "head_bold"))
	logo.add_child(UI.label("IDLE MEGAFACTORY", 12, UI.DIM, "head"))
	h.add_child(logo)
	h.add_child(VSeparator.new())
	var c := UI.vbox(-4)
	l_credits = UI.label("¢0", 28, UI.TEXT, "head_bold")
	l_credits_rate = UI.label("+¢0/min", 14, UI.GOOD)
	c.add_child(l_credits)
	c.add_child(l_credits_rate)
	c.custom_minimum_size.x = 170
	h.add_child(c)
	var p := UI.vbox(2)
	p.custom_minimum_size.x = 230
	p.add_child(UI.label("POWER", 12, UI.DIM, "head"))
	b_power = UI.bar(0, 1, UI.GOOD, 8)
	p.add_child(b_power)
	l_power = UI.label("", 14, UI.TEXT)
	p.add_child(l_power)
	h.add_child(p)
	var r := UI.vbox(2)
	r.custom_minimum_size.x = 300
	r.add_child(UI.label("RESEARCH", 12, UI.DIM, "head"))
	b_research = UI.bar(0, 1, UI.RESEARCH, 8)
	r.add_child(b_research)
	l_research = UI.label("", 14, UI.TEXT)
	l_research.clip_text = true
	l_research.custom_minimum_size.x = 300
	r.add_child(l_research)
	h.add_child(r)
	var t := UI.vbox(0)
	l_poll = UI.label("", 14, UI.TEXT)
	l_threat = UI.label("", 14, UI.TEXT)
	t.add_child(l_poll)
	t.add_child(l_threat)
	t.custom_minimum_size.x = 340
	h.add_child(t)
	h.add_child(UI.spacer())
	l_day = UI.label("", 14, UI.DIM)
	h.add_child(l_day)


func _build_nav() -> void:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UI.box(Color(0.045, 0.05, 0.055, 0.88), Color(0.2, 0.21, 0.22), 6, 8))
	p.position = Vector2(10, 78)
	add_child(p)
	nav = UI.vbox(4)
	p.add_child(nav)
	for n in NAV:
		var b := UI.button("  " + n[1], func(): toggle(n[0]), 160)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.add_theme_font_override("font", UI.font("head"))
		b.add_theme_font_size_override("font_size", 20)
		if n[2] != "":
			b.tooltip_text = "%s  [%s]" % [n[1], n[2]]
		nav.add_child(b)
		nav_buttons[n[0]] = b


func _build_host() -> void:
	host = PanelContainer.new()
	host.add_theme_stylebox_override("panel", UI.box(Color(0.06, 0.065, 0.07, 0.95), Color(0.24, 0.25, 0.27), 6, 14))
	host.anchor_left = 1.0
	host.anchor_right = 1.0
	host.anchor_top = 0.0
	host.anchor_bottom = 1.0
	host.offset_left = -700
	host.offset_right = -10
	host.offset_top = 78
	host.offset_bottom = -10
	host.visible = false
	add_child(host)
	var v := UI.vbox(8)
	host.add_child(v)
	var hh := UI.hbox()
	host_title = UI.heading("", 28)
	hh.add_child(host_title)
	hh.add_child(UI.spacer())
	hh.add_child(UI.button("✕", close_panel))
	v.add_child(hh)
	var sep := HSeparator.new()
	v.add_child(sep)
	host_body = MarginContainer.new()
	host_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(host_body)


func _dirty(keys: Array) -> void:
	for k in keys:
		if panels.has(k):
			panels[k].mark_dirty()


func panel(key: String) -> BasePanel:
	if panels.has(key):
		return panels[key]
	var path := ""
	for n in NAV:
		if n[0] == key:
			path = n[3]
	if key == "line":
		path = "res://scripts/ui/panels/line_panel.gd"
	if key == "tech":
		path = "res://scripts/ui/panels/tech_panel.gd"
	if key == "item":
		path = "res://scripts/ui/panels/item_panel.gd"
	if path == "":
		return null
	var p: BasePanel = load(path).new()
	p.hud = self
	panels[key] = p
	return p


func open(key: String, arg = null) -> void:
	var p := panel(key)
	if p == null:
		return
	if current_panel and current_panel.get_parent() == host_body:
		host_body.remove_child(current_panel)
	current = key
	current_panel = p
	if arg != null and p.has_method("set_arg"):
		p.set_arg(arg)
	host_body.add_child(p)
	host_title.text = p.title.to_upper()
	host.visible = true
	p.ensure_built()
	host_title.text = p.title.to_upper()
	for k in nav_buttons:
		nav_buttons[k].add_theme_color_override("font_color", UI.ACCENT if k == key else UI.TEXT)


func open_tree() -> void:
	if tree == null:
		tree = TechTree.new()
		tree.hud = self
		add_child(tree)
		tree.offset_top = 66
		tree.open()
		return
	if tree.visible:
		tree.visible = false
	else:
		move_child(tree, get_child_count() - 1)
		tree.open()


func toggle(key: String) -> void:
	if current == key and host.visible:
		close_panel()
	else:
		open(key)


func close_panel() -> void:
	host.visible = false
	current = ""
	for k in nav_buttons:
		nav_buttons[k].add_theme_color_override("font_color", UI.TEXT)


func _process(delta: float) -> void:
	_refresh_t += delta
	if _refresh_t < 0.25:
		return
	_refresh_t = 0.0
	_update_top()
	if host.visible and current_panel:
		current_panel.ensure_built()
		host_title.text = current_panel.title.to_upper()


func _update_top() -> void:
	l_credits.text = Fmt.credits(Game.credits)
	l_credits_rate.text = "+%s/min" % Fmt.credits(Game.credits_rate * 60.0)
	var pw: Dictionary = Game.power
	b_power.max_value = maxf(1.0, float(pw.demand))
	b_power.value = float(pw.supply)
	var sat := float(pw.sat)
	b_power.add_theme_stylebox_override("fill", UI.box(UI.GOOD if sat > 0.99 else (UI.WARN if sat > 0.6 else UI.BAD), Color(0, 0, 0, 0), 3, 0))
	l_power.text = "%s / %s  (cap %s)" % [Fmt.power(pw.supply), Fmt.power(pw.demand), Fmt.power(pw.capacity)]
	var tid := Game.current_research()
	if tid != "":
		var t: Dictionary = Content.techs[tid]
		b_research.max_value = Game.tech_units(tid)
		b_research.value = Game.research_progress
		var nm: String = t.get("name", tid)
		if t.get("repeatable", false):
			nm += " " + str(Game.tech_level(tid) + 1)
		l_research.text = "%s  %d/%d" % [nm, int(Game.research_progress), int(Game.tech_units(tid))]
	else:
		b_research.value = 0
		l_research.text = "No research selected"
	var tp: Dictionary = Game.throughput
	l_poll.text = "Pollution %s   ·   Logistics %s/%s per s" % [Fmt.num(Game.pollution), Fmt.num(tp.solid_flow), Fmt.num(tp.solid_cap)]
	l_poll.add_theme_color_override("font_color", UI.BAD if float(tp.solid_sat) < 0.99 else UI.TEXT)
	var siege := Game.siege
	l_threat.text = "Threat %s   Defense %s%s" % [Fmt.num(Game.threat), Fmt.num(Game.defense), ("   SIEGE %s" % Fmt.pct(siege)) if siege > 0.01 else ""]
	l_threat.add_theme_color_override("font_color", UI.BAD if siege > 0.01 else UI.TEXT)
	var dl := Game.daylight()
	l_day.text = ("☀ Day" if dl > 0.5 else ("◐ Dusk" if dl > 0.05 else "☾ Night")) + "   " + Fmt.duration(Game.play_time)


func toast(text: String, kind := "info") -> void:
	var col = {"good": UI.GOOD, "warn": UI.WARN, "bad": UI.BAD, "research": UI.RESEARCH, "achievement": UI.ACCENT}.get(kind, UI.INFO)
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.055, 0.06, 0.94), col.darkened(0.2), 4, 12))
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := UI.label(text, 17, col.lightened(0.25))
	p.add_child(l)
	toasts.add_child(p)
	while toasts.get_child_count() > 6:
		toasts.get_child(0).queue_free()
		toasts.remove_child(toasts.get_child(0))
	var tw := create_tween()
	tw.tween_interval(4.5)
	tw.tween_property(p, "modulate:a", 0.0, 0.8)
	tw.tween_callback(p.queue_free)


func _on_offline(r: Dictionary) -> void:
	var d := AcceptDialog.new()
	d.title = "Welcome back"
	d.theme = UI.theme()
	var v := UI.vbox(8)
	v.add_child(UI.label("You were away for %s. Your factory ran for %s of effective time." % [Fmt.duration(r.elapsed), Fmt.duration(r.simulated)], 17))
	v.add_child(UI.label("Credits earned: " + Fmt.credits(r.credits), 20, UI.GOOD))
	var g := GridContainer.new()
	g.columns = 6
	var items: Dictionary = r.items
	var keys := items.keys()
	keys.sort_custom(func(a, b): return items[a] * Content.item_value(a) > items[b] * Content.item_value(b))
	for k in keys.slice(0, 24):
		g.add_child(UI.item_chip(k, items[k], 30))
	v.add_child(g)
	d.add_child(v)
	add_child(d)
	d.popup_centered(Vector2i(720, 360))


func _unhandled_key_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	if get_viewport().gui_get_focus_owner() is LineEdit:
		return
	for n in NAV:
		if n[2] != "" and k.keycode == OS.find_keycode_from_string(n[2]):
			toggle(n[0])
			get_viewport().set_input_as_handled()
			return
	if k.keycode == KEY_G:
		open_tree()
		get_viewport().set_input_as_handled()
		return
	if k.keycode == KEY_ESCAPE:
		if tree and tree.visible:
			tree.visible = false
		else:
			close_panel()
