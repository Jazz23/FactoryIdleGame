class_name ProdLine
extends RefCounted
## One group of identical buildings. Producers run a recipe; generators make power;
## facilities (labs, storage, defense, support, logistics, megaproject) just count.

enum Kind { PRODUCER, GENERATOR, FACILITY }

var uid: int = 0
var building: String = ""
var recipe: String = ""
var count: int = 0
var modules: Array = []          # module item ids (applies to every building in the line)
var enabled: bool = true
var fuel: String = ""            # pinned fuel item for burner buildings ("" = auto)
var bay: Vector2i = Vector2i(-1, -1)  # layout slot on the factory floor

# runtime (not saved)
var activity: float = 0.0        # 0..1 fraction of nominal speed achieved last tick
var crafts_per_sec: float = 0.0
var status: String = "idle"
var status_item: String = ""
var anim_phase: float = 0.0
var power_draw: float = 0.0
var fuel_sat: float = 1.0
var effective_count: int = 0


func kind() -> int:
	var b: Dictionary = Content.buildings.get(building, {})
	var role: String = b.get("role", "producer")
	if role == "producer":
		return Kind.PRODUCER
	if role == "generator":
		return Kind.GENERATOR
	return Kind.FACILITY


func spec() -> Dictionary:
	return Content.buildings.get(building, {})


func recipe_spec() -> Dictionary:
	return Content.recipes.get(recipe, {})


func to_dict() -> Dictionary:
	return {"uid": uid, "building": building, "recipe": recipe, "count": count, "modules": modules,
		"enabled": enabled, "fuel": fuel, "bay": [bay.x, bay.y]}


static func from_dict(d: Dictionary) -> ProdLine:
	var l := ProdLine.new()
	l.uid = int(d.get("uid", 0))
	l.building = d.get("building", "")
	l.recipe = d.get("recipe", "")
	l.count = int(d.get("count", 0))
	l.modules = d.get("modules", [])
	l.enabled = d.get("enabled", true)
	l.fuel = d.get("fuel", "")
	var b: Array = d.get("bay", [-1, -1])
	l.bay = Vector2i(int(b[0]), int(b[1]))
	return l


func title() -> String:
	if recipe != "":
		return Content.recipes.get(recipe, {}).get("name", recipe)
	return spec().get("name", building)


func module_totals() -> Dictionary:
	var t := {"speed": 0.0, "energy": 0.0, "productivity": 0.0, "pollution": 0.0}
	for m in modules:
		var md: Dictionary = Content.items.get(m, {}).get("module", {})
		for k in t:
			t[k] += float(md.get(k, 0.0))
	return t
