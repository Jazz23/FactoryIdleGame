extends BasePanel
## Frontier: sectors (deposit slots), threat vs defense.

var _meter: Label
var _tbar: ProgressBar
var _dbar: ProgressBar


func _init() -> void:
	title = "Frontier"


func build() -> void:
	var p := UI.panel(Color(0.12, 0.08, 0.07, 0.9), UI.BAD.darkened(0.6), 12)
	var pv := UI.vbox(4)
	p.add_child(pv)
	_meter = UI.label("", 17)
	pv.add_child(_meter)
	var h1 := UI.hbox()
	h1.add_child(UI.label("Threat ", 14, UI.BAD))
	_tbar = UI.bar(0, 1, UI.BAD, 10)
	_tbar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h1.add_child(_tbar)
	pv.add_child(h1)
	var h2 := UI.hbox()
	h2.add_child(UI.label("Defense", 14, UI.GOOD))
	_dbar = UI.bar(0, 1, UI.GOOD, 10)
	_dbar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h2.add_child(_dbar)
	pv.add_child(h2)
	var expl := UI.label("Pollution draws hostile attention. If threat exceeds defense, frontier sectors fall under siege and their extraction slots shut down. Build defenses and keep them supplied with ammunition.", 13, UI.DIM)
	expl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pv.add_child(expl)
	add_child(p)
	var v := UI.vbox(6)
	add_child(UI.scroll(v))
	v.add_child(UI.label("SECTORS", 15, UI.ACCENT, "head_bold"))
	for s in Content.sectors:
		var sid: String = s.id
		var claimed := Game.sectors_claimed.has(sid)
		var sp := UI.panel(Color(0.08, 0.11, 0.08, 0.9) if claimed else Color(0.11, 0.115, 0.12, 0.9), UI.GOOD.darkened(0.55) if claimed else UI.LINE, 10)
		var sv := UI.vbox(4)
		sp.add_child(sv)
		var hh := UI.hbox()
		hh.add_child(UI.label(s.get("name", sid), 19, UI.TEXT, "head_bold"))
		hh.add_child(UI.label("T%d" % int(s.get("tier", 0)), 14, UI.ACCENT, "head_bold"))
		hh.add_child(UI.spacer())
		if claimed:
			hh.add_child(UI.label("CLAIMED", 15, UI.GOOD, "head_bold"))
		else:
			var why := Game.can_claim(sid)
			var b := UI.accent_button("Claim", func(): Game.claim_sector(sid); mark_dirty())
			b.disabled = why != ""
			b.tooltip_text = why
			hh.add_child(b)
		sv.add_child(hh)
		if s.get("desc", "") != "":
			var d := UI.label(s.desc, 13, UI.DIM)
			d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			sv.add_child(d)
		var dh := UI.hbox(10)
		for dep in s.get("deposits", {}):
			var dd: Dictionary = Content.deposits.get(dep, {})
			var c := UI.hbox(2)
			c.add_child(UI.icon(Content.icon(dd.get("item", dep)), 26))
			c.add_child(UI.label("%s ×%d" % [dd.get("name", dep), int(s.deposits[dep])], 14))
			dh.add_child(c)
		var dsc := ScrollContainer.new()
		dsc.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		dsc.custom_minimum_size.y = 34
		dsc.add_child(dh)
		sv.add_child(dsc)
		if not claimed:
			var ch := UI.hbox(4)
			ch.add_child(UI.label("Cost:", 13, UI.DIM))
			for it in s.get("claim_cost", {}):
				var have := float(Game.inv.get(it, 0))
				ch.add_child(UI.item_chip(it, float(s.claim_cost[it]), 24, UI.GOOD if have >= float(s.claim_cost[it]) else UI.WARN))
			ch.add_child(UI.label("  Defense ≥ %s" % Fmt.num(float(s.get("defense_required", 0))), 13, UI.GOOD if Game.defense >= float(s.get("defense_required", 0)) else UI.WARN))
			sv.add_child(ch)
		v.add_child(sp)
	v.add_child(UI.label("KNOWN THREATS", 15, UI.ACCENT, "head_bold"))
	for th in Content.threats:
		var active := Game.pollution >= float(th.get("appears_at_pollution", 0))
		var h := row(v)
		h.add_child(UI.label("⚠" if active else "·", 20, UI.BAD if active else UI.DIM))
		var tv := UI.vbox(0)
		tv.add_child(UI.label(th.get("name", th.id), 17, UI.TEXT if active else UI.DIM, "head"))
		var d2 := UI.label(th.get("desc", ""), 13, UI.DIM)
		d2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		tv.add_child(d2)
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(tv)
		h.add_child(UI.label("str %s\n@ pollution %s" % [Fmt.num(float(th.get("strength", 0))), Fmt.num(float(th.get("appears_at_pollution", 0)))], 12, UI.DIM))


func refresh() -> void:
	if _meter == null:
		return
	_meter.text = "Threat %s   ·   Defense %s   ·   Pollution %s%s" % [Fmt.num(Game.threat), Fmt.num(Game.defense), Fmt.num(Game.pollution), ("   ·   SIEGE %s" % Fmt.pct(Game.siege)) if Game.siege > 0.01 else ""]
	var m := maxf(1.0, maxf(Game.threat, Game.defense) * 1.2)
	_tbar.max_value = m
	_tbar.value = Game.threat
	_dbar.max_value = m
	_dbar.value = Game.defense
