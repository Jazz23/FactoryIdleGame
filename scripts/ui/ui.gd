class_name UI
## Theme + widget helpers. Industrial dark UI: graphite panels, amber accent.

const BG := Color(0.07, 0.075, 0.08, 0.94)
const BG2 := Color(0.11, 0.115, 0.125, 0.96)
const BG3 := Color(0.15, 0.16, 0.17, 1.0)
const LINE := Color(0.26, 0.27, 0.29, 1.0)
const TEXT := Color(0.9, 0.88, 0.84)
const DIM := Color(0.6, 0.62, 0.64)
const ACCENT := Color(0.96, 0.64, 0.18)
const GOOD := Color(0.45, 0.85, 0.45)
const WARN := Color(0.98, 0.78, 0.25)
const BAD := Color(0.95, 0.35, 0.3)
const INFO := Color(0.45, 0.7, 0.98)
const RESEARCH := Color(0.55, 0.75, 1.0)

static var _fonts := {}
static var _theme: Theme


static func font(kind: String = "body") -> Font:
	if _fonts.has(kind):
		return _fonts[kind]
	var files := {
		"body": "res://assets/fonts/Barlow-Medium.ttf",
		"body_bold": "res://assets/fonts/Barlow-SemiBold.ttf",
		"head": "res://assets/fonts/BarlowCondensed-SemiBold.ttf",
		"head_bold": "res://assets/fonts/BarlowCondensed-Bold.ttf",
	}
	var f: Font = null
	if ResourceLoader.exists(files.get(kind, "")):
		f = load(files[kind])
	if f == null:
		f = ThemeDB.fallback_font
	_fonts[kind] = f
	return f


static func box(bg: Color, border := Color(0, 0, 0, 0), radius := 4, pad := 8, bw := 1) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(bw if border.a > 0 else 0)
	s.set_corner_radius_all(radius)
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad * 0.6
	s.content_margin_bottom = pad * 0.6
	s.anti_aliasing = true
	return s


static func theme() -> Theme:
	if _theme:
		return _theme
	var t := Theme.new()
	t.default_font = font("body")
	t.default_font_size = 17
	t.set_color("font_color", "Label", TEXT)
	t.set_color("font_color", "Button", TEXT)
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", ACCENT)
	t.set_color("font_disabled_color", "Button", Color(0.45, 0.46, 0.47))
	t.set_stylebox("normal", "Button", box(BG3, LINE, 4, 10))
	t.set_stylebox("hover", "Button", box(Color(0.2, 0.21, 0.22), ACCENT.darkened(0.3), 4, 10))
	t.set_stylebox("pressed", "Button", box(Color(0.24, 0.2, 0.14), ACCENT, 4, 10))
	t.set_stylebox("disabled", "Button", box(Color(0.1, 0.105, 0.11), Color(0.18, 0.18, 0.19), 4, 10))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_stylebox("panel", "PanelContainer", box(BG, LINE, 6, 12))
	t.set_stylebox("panel", "Panel", box(BG, LINE, 6, 12))
	t.set_stylebox("panel", "TooltipPanel", box(Color(0.05, 0.055, 0.06, 0.97), ACCENT.darkened(0.4), 4, 10))
	t.set_color("font_color", "TooltipLabel", TEXT)
	t.set_font("font", "TooltipLabel", font("body"))
	t.set_font_size("font_size", "TooltipLabel", 16)
	var bar_bg := box(Color(0.04, 0.045, 0.05), LINE, 3, 0)
	var bar_fg := box(ACCENT, Color(0, 0, 0, 0), 3, 0)
	t.set_stylebox("background", "ProgressBar", bar_bg)
	t.set_stylebox("fill", "ProgressBar", bar_fg)
	t.set_color("font_color", "ProgressBar", TEXT)
	t.set_font_size("font_size", "ProgressBar", 13)
	t.set_stylebox("normal", "LineEdit", box(Color(0.04, 0.045, 0.05), LINE, 4, 8))
	t.set_stylebox("focus", "LineEdit", box(Color(0.05, 0.055, 0.06), ACCENT.darkened(0.2), 4, 8))
	t.set_color("font_color", "LineEdit", TEXT)
	t.set_stylebox("panel", "ScrollContainer", StyleBoxEmpty.new())
	t.set_stylebox("tab_selected", "TabBar", box(BG3, ACCENT, 4, 10))
	t.set_stylebox("tab_unselected", "TabBar", box(BG2, LINE, 4, 10))
	t.set_stylebox("tab_hovered", "TabBar", box(Color(0.18, 0.19, 0.2), LINE, 4, 10))
	t.set_color("font_selected_color", "TabBar", ACCENT)
	t.set_color("font_unselected_color", "TabBar", DIM)
	t.set_stylebox("panel", "TabContainer", box(BG2, LINE, 4, 8))
	t.set_stylebox("grabber", "VScrollBar", box(Color(0.3, 0.31, 0.33), Color(0, 0, 0, 0), 3, 0))
	t.set_stylebox("grabber_highlight", "VScrollBar", box(ACCENT.darkened(0.3), Color(0, 0, 0, 0), 3, 0))
	t.set_stylebox("scroll", "VScrollBar", box(Color(0, 0, 0, 0.2), Color(0, 0, 0, 0), 3, 0))
	t.set_stylebox("normal", "OptionButton", box(BG3, LINE, 4, 10))
	t.set_stylebox("hover", "OptionButton", box(Color(0.2, 0.21, 0.22), ACCENT.darkened(0.3), 4, 10))
	t.set_stylebox("panel", "PopupMenu", box(BG2, LINE, 4, 6))
	t.set_color("font_color", "PopupMenu", TEXT)
	t.set_color("font_hover_color", "PopupMenu", ACCENT)
	t.set_stylebox("hover", "PopupMenu", box(BG3, Color(0, 0, 0, 0), 2, 4))
	t.set_constant("separation", "HBoxContainer", 6)
	t.set_constant("separation", "VBoxContainer", 6)
	t.set_stylebox("separator", "HSeparator", box(LINE, Color(0, 0, 0, 0), 0, 0))
	_theme = t
	return t


# ------------------------------------------------------------------ widgets
static func label(text: String, size := 17, color := TEXT, kind := "body") -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font(kind))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


static func heading(text: String, size := 26) -> Label:
	var l := label(text.to_upper(), size, TEXT, "head_bold")
	l.add_theme_constant_override("outline_size", 0)
	return l


static func button(text: String, cb: Callable = Callable(), min_w := 0) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_override("font", font("body_bold"))
	b.add_theme_font_size_override("font_size", 16)
	if cb.is_valid():
		b.pressed.connect(cb)
	if min_w > 0:
		b.custom_minimum_size.x = min_w
	b.focus_mode = Control.FOCUS_NONE
	return b


static func accent_button(text: String, cb: Callable = Callable(), min_w := 0) -> Button:
	var b := button(text, cb, min_w)
	b.add_theme_stylebox_override("normal", box(Color(0.32, 0.22, 0.08), ACCENT.darkened(0.15), 4, 10))
	b.add_theme_stylebox_override("hover", box(Color(0.42, 0.29, 0.1), ACCENT, 4, 10))
	b.add_theme_color_override("font_color", Color(1, 0.92, 0.8))
	return b


static func icon(tex: Texture2D, size := 32) -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.custom_minimum_size = Vector2(size, size)
	r.mouse_filter = Control.MOUSE_FILTER_PASS
	return r


static func item_icon(item: String, size := 32) -> TextureRect:
	var r := icon(Content.icon(item), size)
	r.tooltip_text = Content.item_name(item)
	return r


## icon + amount, e.g. for recipe inputs
static func item_chip(item: String, amount: float, size := 28, color := TEXT) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 3)
	h.add_child(item_icon(item, size))
	h.add_child(label(Fmt.num(amount), 15, color))
	h.tooltip_text = Content.item_name(item)
	h.mouse_filter = Control.MOUSE_FILTER_PASS
	return h


static func hbox(sep := 6) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h


static func vbox(sep := 6) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v


static func spacer() -> Control:
	var c := Control.new()
	c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return c


static func panel(bg := BG2, border := LINE, pad := 10) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", box(bg, border, 5, pad))
	return p


static func bar(value: float, max_value := 1.0, color := ACCENT, h := 10) -> ProgressBar:
	var p := ProgressBar.new()
	p.max_value = max_value
	p.value = value
	p.show_percentage = false
	p.custom_minimum_size = Vector2(0, h)
	p.add_theme_stylebox_override("fill", box(color, Color(0, 0, 0, 0), 3, 0))
	p.mouse_filter = Control.MOUSE_FILTER_PASS
	return p


static func scroll(child: Control) -> ScrollContainer:
	var s := ScrollContainer.new()
	s.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	s.size_flags_vertical = Control.SIZE_EXPAND_FILL
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	child.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(child)
	return s


static func clear(n: Node) -> void:
	for c in n.get_children():
		n.remove_child(c)
		c.queue_free()


static func status_text(status: String, item := "") -> String:
	match status:
		"working": return "Running"
		"no_input": return "Waiting for " + (Content.item_name(item) if item != "" else "inputs")
		"output_full": return (Content.item_name(item) if item != "" else "Output") + " storage full"
		"no_power": return "Low power"
		"no_fuel": return "No fuel"
		"no_slots": return "No deposit slots"
		"disabled": return "Paused"
		"idle": return "Idle"
	return status.capitalize()


static func status_color(status: String) -> Color:
	match status:
		"working": return GOOD
		"no_input", "no_fuel": return WARN
		"output_full", "no_power", "no_slots": return BAD
	return DIM
