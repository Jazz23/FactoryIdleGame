class_name Fmt
## Number / time / rate formatting helpers.

const SUFFIXES := ["", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc",
	"UDc", "DDc", "TDc", "QaDc", "QiDc", "SxDc", "SpDc", "OcDc", "NoDc", "Vg"]


static func num(v: float, decimals: int = 2) -> String:
	if is_nan(v):
		return "—"
	var neg := v < 0.0
	var a := absf(v)
	var s: String
	if a < 1000.0:
		if a == floorf(a):
			s = str(int(a))
		elif a >= 100.0:
			s = "%.0f" % a
		elif a >= 10.0:
			s = "%.1f" % a
		else:
			s = ("%." + str(decimals) + "f") % a
			s = s.rstrip("0").rstrip(".") if s.contains(".") else s
	else:
		var tier := int(floor(log(a) / log(1000.0)))
		if tier >= SUFFIXES.size():
			s = "%.2e" % a
		else:
			var m := a / pow(1000.0, tier)
			var fmt := "%.2f" if m < 10.0 else ("%.1f" if m < 100.0 else "%.0f")
			s = (fmt % m) + SUFFIXES[tier]
	return ("-" if neg else "") + s


static func credits(v: float) -> String:
	return "¢" + num(v)


static func rate(per_sec: float) -> String:
	var pm := per_sec * 60.0
	if absf(pm) >= 1.0 or pm == 0.0:
		return num(pm) + "/min"
	return num(per_sec * 3600.0) + "/h"


static func power(kw: float) -> String:
	var a := absf(kw)
	if a >= 1.0e6:
		return num(kw / 1.0e6) + " GW"
	if a >= 1000.0:
		return num(kw / 1000.0) + " MW"
	return num(kw) + " kW"


static func energy(kj: float) -> String:
	var a := absf(kj)
	if a >= 1.0e9:
		return num(kj / 1.0e9) + " TJ"
	if a >= 1.0e6:
		return num(kj / 1.0e6) + " GJ"
	if a >= 1000.0:
		return num(kj / 1000.0) + " MJ"
	return num(kj) + " kJ"


static func duration(sec: float) -> String:
	sec = maxf(sec, 0.0)
	if sec < 60.0:
		return "%ds" % int(ceil(sec))
	if sec < 3600.0:
		return "%dm %02ds" % [int(sec / 60.0), int(sec) % 60]
	if sec < 86400.0:
		return "%dh %02dm" % [int(sec / 3600.0), int(sec / 60.0) % 60]
	return "%dd %02dh" % [int(sec / 86400.0), int(sec / 3600.0) % 24]


static func pct(v: float) -> String:
	return "%d%%" % int(round(v * 100.0))


static func signed_pct(v: float) -> String:
	return ("+" if v >= 0 else "") + "%d%%" % int(round(v * 100.0))
