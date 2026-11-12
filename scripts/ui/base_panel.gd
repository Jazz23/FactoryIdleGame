class_name BasePanel
extends VBoxContainer
## Base class for side panels. Subclasses override build() (full rebuild) and refresh() (cheap
## per-0.25s update of numbers). `hud` is set by the HUD; use hud.open(...) to navigate.

var hud
var title := "Panel"
var dirty := true


func _ready() -> void:
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("separation", 8)


func build() -> void:
	pass


func refresh() -> void:
	pass


func mark_dirty() -> void:
	dirty = true


func ensure_built() -> void:
	if dirty:
		dirty = false
		UI.clear(self)
		build()
	refresh()


func section(text: String) -> Label:
	var l := UI.label(text.to_upper(), 15, UI.ACCENT, "head_bold")
	add_child(l)
	return l


## A row container with hover background, returns the inner HBox.
func row(parent: Control, cb: Callable = Callable(), tooltip := "") -> HBoxContainer:
	var p := PanelContainer.new()
	var normal := UI.box(Color(0.12, 0.125, 0.135, 0.9), Color(0.2, 0.21, 0.22), 4, 8)
	p.add_theme_stylebox_override("panel", normal)
	p.tooltip_text = tooltip
	var h := UI.hbox(8)
	p.add_child(h)
	if cb.is_valid():
		p.mouse_filter = Control.MOUSE_FILTER_STOP
		p.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		p.gui_input.connect(func(e):
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				cb.call())
		p.mouse_entered.connect(func(): p.add_theme_stylebox_override("panel", UI.box(Color(0.17, 0.165, 0.15, 0.95), UI.ACCENT.darkened(0.35), 4, 8)))
		p.mouse_exited.connect(func(): p.add_theme_stylebox_override("panel", normal))
	parent.add_child(p)
	return h


func recipe_line(r: Dictionary, crafts_per_sec := -1.0, size := 30) -> HBoxContainer:
	## inputs → outputs with icons; if crafts_per_sec >= 0 shows per-minute amounts
	var h := UI.hbox(4)
	var ins: Dictionary = r.get("inputs", {})
	var mult := crafts_per_sec * 60.0 if crafts_per_sec >= 0 else 1.0
	if ins.is_empty():
		if r.has("deposit"):
			h.add_child(UI.label(Content.deposits.get(r.deposit, {}).get("name", r.deposit), 15, UI.DIM))
	for it in ins:
		h.add_child(UI.item_chip(it, float(ins[it]) * mult, size))
	h.add_child(UI.label("  ➜  ", 18, UI.ACCENT))
	var outs: Dictionary = r.get("outputs", {})
	for it in outs:
		h.add_child(UI.item_chip(it, float(outs[it]) * mult, size, UI.GOOD.lightened(0.3)))
	if crafts_per_sec < 0:
		h.add_child(UI.label("  %ss" % Fmt.num(float(r.get("time", 1))), 14, UI.DIM))
	else:
		h.add_child(UI.label(" /min", 14, UI.DIM))
	return h
