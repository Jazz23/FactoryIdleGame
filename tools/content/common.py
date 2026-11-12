"""Shared schema constants, the content registry and small helpers.

Everything that defines content imports `C` (the single registry) and the add_* helpers.
Python-only metadata (raw base values, multi-output value weights, tech branches used for
validation) lives on the registry too and is stripped or exported explicitly by the writer.
"""

GROUPS = ["raw", "materials", "intermediates", "components", "fluids", "research", "logistics",
          "production", "power", "defense", "megaproject"]

CATEGORIES = ["mining", "pumping", "oil_extraction", "smelting", "crushing", "pressing", "assembling",
              "precision_assembling", "electronics", "chemistry", "refining", "mixing", "electrolysis",
              "centrifuging", "cryogenics", "foundry", "bioprocessing", "nanofab", "orbital", "munitions",
              "boiling", "fission", "fusion", "smelting_advanced", "recycling"]

EXTRACTION_CATEGORIES = {"mining", "pumping", "oil_extraction"}

ITEM_ARCHETYPES = ["ore_chunks", "powder_pile", "gravel_pile", "crystal_cluster", "ingot", "plate", "plate_stack",
                   "sheet_coil", "rod", "beam", "pipe", "wire_spool", "cable_coil", "gear", "bolts", "spring",
                   "bearing", "circuit_board", "chip", "battery", "motor", "frame", "solar_cell", "glass_pane",
                   "brick", "block", "pellets", "barrel", "gas_canister", "flask", "crate", "module_card",
                   "magnet", "lens", "filter", "fuel_rod", "ammo_box", "shell", "rocket_part", "drone",
                   "servo_arm", "tank_part", "fluid_orb", "cell", "log", "bag", "canister", "nozzle", "antenna",
                   "processor", "capsule", "heat_sink", "turbine_blade", "building_kit"]

MATERIALS = ["iron", "steel", "stainless", "copper", "brass", "bronze", "tin", "aluminum", "titanium", "gold",
             "silver", "lead", "tungsten", "chrome", "cast_iron", "iron_ore", "copper_ore", "coal", "stone",
             "limestone", "sand", "quartz", "bauxite", "ilmenite", "monazite", "sulfur", "salt", "lithium",
             "graphite", "silicon", "glass", "concrete", "brick_clay", "rubber", "plastic_white", "plastic_black",
             "plastic_color", "carbon_fiber", "ceramic", "wood", "pcb_green", "pcb_blue", "pcb_red", "pcb_black",
             "paint", "glow", "uranium_glass", "thorium", "crystal"]

BUILDING_ARCHETYPES = ["drill", "pumpjack", "water_pump", "gas_well", "burner_furnace", "electric_furnace",
                       "arc_furnace", "crusher", "press", "rolling_mill", "wire_drawer", "assembler",
                       "precision_assembler", "electronics_fab", "chemical_plant", "refinery", "mixer",
                       "electrolyzer", "centrifuge", "cryo_plant", "foundry", "bioreactor", "nanofab", "lab",
                       "boiler", "steam_engine", "steam_turbine", "solar_array", "wind_turbine", "accumulator",
                       "gas_turbine", "reactor", "heat_exchanger", "cooling_tower", "fusion_reactor",
                       "geothermal_plant", "storage_tank", "warehouse", "silo", "conveyor_hub", "rail_depot",
                       "drone_port", "beacon", "scrubber", "turret", "wall_segment", "radar", "shield_generator",
                       "launch_pad", "orbital_assembler", "substation", "munitions_plant"]

ROLES = ["producer", "generator", "storage", "research", "logistics", "defense", "support", "megaproject"]

EFFECT_TYPES = ["craft_speed", "mining_productivity", "lab_speed", "lab_productivity", "power_output",
                "storage_capacity", "market_price", "defense", "pollution_reduction", "offline_efficiency",
                "module_slots", "extraction_slots"]

AMMO_CLASSES = ["ballistic", "explosive", "incendiary", "energy"]
FUEL_CLASSES = ["chemical", "nuclear", "fusion"]
GENERATOR_SOURCES = ["solar", "wind", "geothermal", "tidal", "accumulator"]
POWER_TARGETS = ["steam", "superheated_steam", "fuel_gas", "solar", "wind", "geothermal", "tidal"]

TECH_BRANCHES = ["logistics", "metallurgy", "electronics", "chemistry", "power", "defense", "mining",
                 "research", "aerospace", "quantum", "manufacturing", "biotech"]

# Research data items, keyed by research tier. Field Reports are the defense side branch.
RESEARCH_BY_TIER = {1: "blueprint_sheet", 2: "circuit_schematic", 3: "chemical_assay", 4: "alloy_specimen",
                    5: "flight_telemetry", 6: "quantum_datacore"}
FIELD_REPORT = "field_report"

# Gate tech that first unlocks each research item's recipe (None = available from start).
GATE_FOR_RESEARCH = {"blueprint_sheet": None, "circuit_schematic": "circuit_theory",
                     "chemical_assay": "chemical_assays", "alloy_specimen": "materials_testing",
                     "flight_telemetry": "flight_testing", "quantum_datacore": "quantum_datacores",
                     "field_report": "field_reporting"}

# Terms that belong to other games and must never appear in names/descs/ids.
BANNED_TERMS = ["science pack", "electronic circuit", "advanced circuit", "processing unit", "inserter",
                "transport belt", "splitter", "underground belt", "assembling machine", "biter", "spitter",
                "worm", "spawner", "rocket silo", "satellite", "low density structure", "rocket control unit",
                "kovarex", "uranium-235", "uranium-238", "uranium 235", "uranium 238", "fish"]


class Content:
    def __init__(self):
        self.items = {}
        self.recipes = {}
        self.buildings = {}
        self.techs = {}
        self.deposits = {}
        self.sectors = {}
        self.threats = {}
        self.contracts = {}
        self.achievements = {}
        self.megaprojects = {}
        self.start = None
        self.settings = {}
        # python-only metadata
        self.base_values = {}      # raw item id -> base value (¢)
        self.recipe_weights = {}   # recipe id -> {output id: weight}
        self.final_items = set()   # items allowed to have no consumer
        self.errors = []
        self.warnings = []


C = Content()


def err(msg):
    C.errors.append(msg)


def warn(msg):
    C.warnings.append(msg)


def V(archetype, material, color=None, **params):
    """Visual block shared by items, buildings and deposits."""
    v = {"archetype": archetype, "material": material}
    if color is not None:
        v["color"] = [round(float(c), 3) for c in color]
    if params:
        v["params"] = params
    return v


def add_item(iid, name, group, tier, visual, desc, kind="solid", **extra):
    if iid in C.items:
        err(f"items: duplicate id '{iid}'")
    d = {"id": iid, "name": name, "desc": desc, "kind": kind, "group": group, "tier": tier, "value": 0.0}
    for k in ("fuel_kj", "fuel_class", "pollution_mult", "module", "ammo"):
        if k in extra:
            d[k] = extra.pop(k)
    if extra:
        err(f"items: '{iid}' has unknown fields {sorted(extra)}")
    d["visual"] = visual
    C.items[iid] = d
    return d


def add_recipe(rid, name, category, time, inputs, outputs, unlock, deposit=None, weights=None):
    if rid in C.recipes:
        err(f"recipes: duplicate id '{rid}'")
    d = {"id": rid, "name": name, "category": category, "time": float(time),
         "inputs": dict(inputs), "outputs": dict(outputs), "unlocked_by": unlock}
    if deposit is not None:
        d["deposit"] = deposit
    C.recipes[rid] = d
    if weights:
        C.recipe_weights[rid] = dict(weights)
    return d


def add_tech(tid, name, desc, tier, branch, prereqs, cost, units, time, effects=None, repeatable=False):
    if tid in C.techs:
        err(f"techs: duplicate id '{tid}'")
    d = {"id": tid, "name": name, "desc": desc, "branch": branch, "prereqs": list(prereqs), "cost": dict(cost),
         "time": float(time), "units": int(units), "unlocks": [], "effects": list(effects or []), "tier": tier,
         "repeatable": repeatable}
    C.techs[tid] = d
    return d


def eff(etype, target, value):
    return {"type": etype, "target": target, "value": value}


def sig3(x):
    """Round to 3 significant figures."""
    if x == 0:
        return 0.0
    return float(f"{x:.3g}")
