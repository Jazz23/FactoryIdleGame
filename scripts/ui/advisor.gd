class_name Advisor
extends PanelContainer
## Context-sensitive "what to do next" hints computed from the live simulation.

var hud
var box: VBoxContainer
var _t := 0.0
var collapsed := false


func _ready() -> void:
	add_theme_stylebox_override("panel", UI.box(Color(0.045, 0.05, 0.055, 0.88), Color(0.2, 0.21, 0.22), 6, 10))
	custom_minimum_size = Vector2(300, 0)
	var v := UI.vbox(4)
	add_child(v)
	var h := UI.hbox()
	h.add_child(UI.label("ADVISOR", 14, UI.ACCENT, "head_bold"))
	h.add_child(UI.spacer())
	var tg := UI.button("–", func(): collapsed = not collapsed; box.visible = not collapsed)
	tg.add_theme_font_size_override("font_size", 12)
	h.add_child(tg)
	v.add_child(h)
	box = UI.vbox(4)
	v.add_child(box)


func _process(delta: float) -> void:
	_t += delta
	if _t < 1.0 or collapsed:
		return
	_t = 0.0
	UI.clear(box)
	var tips := suggestions()
	for tip in tips.slice(0, 4):
		var b := Button.new()
		b.text = tip[0]
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.custom_minimum_size = Vector2(280, 0)
		b.add_theme_font_size_override("font_size", 14)
		b.add_theme_color_override("font_color", tip[2])
		b.focus_mode = Control.FOCUS_NONE
		if tip[3] != null:
			b.icon = tip[3]
			b.expand_icon = false
			b.add_theme_constant_override("icon_max_width", 26)
		var cb: Callable = tip[1]
		b.pressed.connect(cb)
		box.add_child(b)
	if tips.is_empty():
		box.add_child(UI.label("Everything is running smoothly.", 14, UI.GOOD))


func _producing(item: String) -> bool:
	for l in Game.lines:
		if l.count > 0 and l.recipe != "" and Content.recipes[l.recipe].get("outputs", {}).has(item):
			return true
	return false


func _open_build_for(item: String) -> void:
	var bp = hud.panel("build")
	bp.tab = "products"
	bp.search = Content.item_name(item).to_lower()
	bp.picked_recipe = ""
	bp.mark_dirty()
	hud.open("build")


## Returns Array of [text, callable, color, icon]
func suggestions() -> Array:
	var out: Array = []
	# siege
	if Game.siege > 0.01:
		out.append(["Frontier under siege — build defenses and supply ammunition.", func(): hud.open("frontier"), UI.BAD, null])
	# power
	if float(Game.power.sat) < 0.98 and float(Game.power.demand) > 0:
		out.append(["Power shortage (%s). Add generators or fuel." % Fmt.pct(Game.power.sat), func(): hud.open("power"), UI.BAD, null])
	# logistics
	if float(Game.throughput.solid_sat) < 0.99:
		out.append(["Logistics bottleneck: %s/%s items/s. Build conveyor hubs or better logistics." % [Fmt.num(Game.throughput.solid_flow), Fmt.num(Game.throughput.solid_cap)], func(): var bp = hud.panel("build"); bp.tab = "facilities"; bp.mark_dirty(); hud.open("build"), UI.BAD, null])
	# research
	var cur := Game.current_research()
	if cur == "":
		var any := false
		for t in Content.tech_list:
			if Game.tech_available(t.id):
				any = true
				break
		if any:
			out.append(["Choose a research project.", func(): hud.open("research"), UI.RESEARCH, null])
	else:
		var labs := Game.lab_speed()
		if labs <= 0:
			var lab_id := ""
			for b in Content.building_list:
				if b.get("role", "") == "research":
					lab_id = b.id
					break
			out.append(["Build a lab to research %s." % Content.techs[cur].name, func(): var bp = hud.panel("build"); bp.tab = "facilities"; bp.mark_dirty(); hud.open("build"), UI.RESEARCH, Content.icon(lab_id) if lab_id != "" else null])
		for it in Content.techs[cur].get("cost", {}):
			if Game.inv.get(it, 0.0) < 1.0 and not _producing(it):
				var item: String = it
				out.append(["Produce %s for research." % Content.item_name(it), func(): _open_build_for(item), UI.RESEARCH, Content.icon(it)])
	# starved lines whose input nobody makes
	var seen := {}
	for l in Game.lines:
		if l.count > 0 and l.status == "no_input" and l.status_item != "" and not seen.has(l.status_item):
			seen[l.status_item] = true
			if not _producing(l.status_item):
				var item: String = l.status_item
				out.append(["%s needs %s — nobody makes it." % [l.title(), Content.item_name(item)], func(): _open_build_for(item), UI.WARN, Content.icon(item)])
		elif l.count > 0 and l.status == "no_fuel":
			out.append(["%s is out of fuel." % l.title(), func(): hud.open("line", l.uid), UI.WARN, null])
		elif l.count > 0 and l.status == "output_full" and not seen.has("full_" + l.status_item) and (not Content.is_fluid(l.status_item) or l.recipe_spec().get("outputs", {}).size() > 1):
			seen["full_" + l.status_item] = true
			var item2: String = l.status_item
			out.append(["%s storage is full — sell it or enable auto-sell." % Content.item_name(item2), func(): hud.open("market"), UI.WARN, Content.icon(item2)])
		elif l.count > 0 and l.status == "no_slots":
			out.append(["No free deposit slots for %s — claim a sector." % l.title(), func(): hud.open("frontier"), UI.WARN, null])
	# contracts ready
	for cid in Game.contracts_active:
		var c := Game.contract(cid)
		if not c.is_empty() and Game.has_items(c.get("requires", {})):
			out.append(["Contract ready to deliver: %s" % c.get("name", cid), func(): hud.open("contracts"), UI.GOOD, null])
			break
	# claimable sector
	for s in Content.sectors:
		if not Game.sectors_claimed.has(s.id):
			if Game.can_claim(s.id) == "":
				out.append(["You can claim %s." % s.get("name", s.id), func(): hud.open("frontier"), UI.GOOD, null])
			break
	return out
