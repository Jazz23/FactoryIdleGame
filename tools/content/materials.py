"""Raw resources, fluids, materials, intermediates, components and research data items.

Each crafted item is declared together with its primary recipe (recipe id == item id) so the
tree stays readable; alternative / multi-output recipes are declared with `alt`.
Tech ids referenced in `unlock=` are defined in techs.py.
"""
from common import C, V, add_item, add_recipe

EXTRACT_PREFIX = {"mining": "mine_", "pumping": "pump_", "oil_extraction": "drill_"}

# Colour palette (linear-ish sRGB 0-1)
COL = {
    "water": (0.25, 0.45, 0.75), "steam": (0.88, 0.9, 0.92), "crude": (0.08, 0.07, 0.06),
    "gas": (0.9, 0.75, 0.2), "brine": (0.55, 0.7, 0.72), "heavy": (0.25, 0.14, 0.06),
    "naphtha": (0.85, 0.62, 0.22), "fuel_gas": (0.55, 0.6, 0.62), "lube": (0.32, 0.55, 0.22),
    "acid": (0.9, 0.85, 0.2), "chlorine": (0.65, 0.85, 0.3), "hydrogen": (0.85, 0.2, 0.2),
    "bio": (0.35, 0.45, 0.12), "oxygen": (0.2, 0.45, 0.9), "nitrogen": (0.35, 0.35, 0.4),
    "ammonia": (0.6, 0.35, 0.8), "nitric": (0.95, 0.55, 0.15), "hcl": (0.75, 0.9, 0.6),
    "ticl4": (0.85, 0.85, 0.75), "superheated": (0.95, 0.6, 0.45), "kerosene": (0.8, 0.7, 0.45),
    "lox": (0.55, 0.8, 1.0), "lh2": (0.85, 0.9, 1.0), "deuterium": (0.3, 0.8, 0.95),
    "helium": (0.85, 0.5, 0.75), "lhe": (0.75, 0.95, 1.0),
}


def raw(iid, name, tier, arch, material, base, desc, kind="solid", color=None, **extra):
    group = "fluids" if kind == "fluid" else "raw"
    add_item(iid, name, group, tier, V(arch, material, color), desc, kind=kind, **extra)
    C.base_values[iid] = base


def extract(iid, cat, time, amount, unlock, name):
    add_recipe(EXTRACT_PREFIX[cat] + iid, name, cat, time, {}, {iid: amount}, unlock, deposit=iid)


def m(iid, name, group, tier, vis, desc, recipe=None, unlock=None, kind="solid", **extra):
    """Declare an item and (optionally) its primary recipe: recipe = (category, time, inputs[, amount])."""
    add_item(iid, name, group, tier, vis, desc, kind=kind, **extra)
    if recipe is not None:
        cat, time, inputs = recipe[:3]
        n = recipe[3] if len(recipe) > 3 else 1
        add_recipe(iid, name, cat, time, inputs, {iid: n}, unlock)


def liquid(iid, name, tier, color, desc, recipe=None, unlock=None):
    m(iid, name, "fluids", tier, V("fluid_orb", "glass", COL[color]), desc, recipe, unlock, kind="fluid")


def gas(iid, name, tier, color, desc, recipe=None, unlock=None):
    m(iid, name, "fluids", tier, V("gas_canister", "paint", COL[color]), desc, recipe, unlock, kind="fluid")


def alt(rid, name, cat, time, inputs, outputs, unlock, weights=None):
    add_recipe(rid, name, cat, time, inputs, outputs, unlock, weights=weights)


def define():
    # =====================================================================================
    # RAW RESOURCES (base values in ¢ per unit)
    # =====================================================================================
    raw("iron_ore", "Iron Ore", 0, "ore_chunks", "iron_ore", 1.5, "Rust-red hematite broken from shallow seams.")
    raw("copper_ore", "Copper Ore", 0, "ore_chunks", "copper_ore", 1.6, "Green-stained rock veined with copper sulfides.")
    raw("coal", "Coal", 0, "ore_chunks", "coal", 1.2, "Bituminous coal that burns in any furnace or boiler.",
        fuel_kj=4000.0, fuel_class="chemical", pollution_mult=1.0)
    raw("stone", "Stone", 0, "ore_chunks", "stone", 1.0, "Fieldstone and rubble for bricks and aggregate.")
    raw("water", "Water", 0, "fluid_orb", "glass", 0.1, "Raw intake water, the base of every boiler and reactor.",
        kind="fluid", color=COL["water"])
    raw("limestone", "Limestone", 1, "ore_chunks", "limestone", 1.3, "Pale sedimentary rock burned for lime and cement.")
    raw("quartz_sand", "Quartz Sand", 1, "powder_pile", "sand", 1.4, "Clean silica sand for glass and ceramics.")
    raw("cassiterite", "Cassiterite", 2, "ore_chunks", "stone", 2.4, "Heavy black tin-oxide gravel from river deltas.",
        color=(0.22, 0.18, 0.15))
    raw("native_sulfur", "Native Sulfur", 3, "crystal_cluster", "sulfur", 2.0, "Yellow sulfur crusts scraped from volcanic vents.")
    raw("crude_oil", "Crude Oil", 3, "fluid_orb", "glass", 0.3, "Black, sour crude pumped from deep reservoirs.",
        kind="fluid", color=COL["crude"])
    raw("natural_gas", "Natural Gas", 3, "gas_canister", "paint", 0.25, "Sour methane-rich gas from drilled wells.",
        kind="fluid", color=COL["gas"])
    raw("brine", "Brine", 3, "fluid_orb", "glass", 0.15, "Mineral-laden salt water pumped from aquifers.",
        kind="fluid", color=COL["brine"])
    raw("bauxite", "Bauxite", 4, "ore_chunks", "bauxite", 2.2, "Rusty-orange laterite, the ore of aluminum.")
    raw("ilmenite", "Ilmenite", 4, "gravel_pile", "ilmenite", 2.8, "Black beach sand rich in iron-titanium oxide.")
    raw("monazite_sand", "Monazite Sand", 5, "powder_pile", "monazite", 3.0, "Mildly radioactive sand carrying thorium and rare earths.")
    raw("wolframite", "Wolframite", 5, "crystal_cluster", "graphite", 3.0, "Dense black tungstate crystals from ridge veins.",
        color=(0.18, 0.18, 0.2))
    raw("rare_earth_ore", "Rare-Earth Ore", 6, "ore_chunks", "stone", 3.0, "Pinkish carbonatite ore laced with lanthanides and yttrium.",
        color=(0.62, 0.42, 0.4))
    raw("helium_gas", "Helium Gas", 6, "gas_canister", "paint", 0.5, "Inert gas tapped from deep radiogenic pockets.",
        kind="fluid", color=COL["helium"])

    extract("iron_ore", "mining", 2, 1, None, "Mine Iron Ore")
    extract("copper_ore", "mining", 2, 1, None, "Mine Copper Ore")
    extract("coal", "mining", 2, 1, None, "Mine Coal")
    extract("stone", "mining", 1.5, 1, None, "Quarry Stone")
    extract("water", "pumping", 1, 80, None, "Pump Water")
    extract("limestone", "mining", 2, 1, "quarrying", "Quarry Limestone")
    extract("quartz_sand", "mining", 2, 2, "glassmaking", "Dredge Quartz Sand")
    extract("cassiterite", "mining", 3, 1, "tin_smelting", "Mine Cassiterite")
    extract("native_sulfur", "mining", 3, 1, "sulfur_processing", "Scrape Native Sulfur")
    extract("crude_oil", "oil_extraction", 1, 10, "oil_extraction", "Pump Crude Oil")
    extract("natural_gas", "oil_extraction", 1, 15, "gas_processing", "Tap Natural Gas")
    extract("brine", "pumping", 1, 25, "chlor_alkali", "Pump Brine")
    extract("bauxite", "mining", 2.5, 1, "bayer_process", "Mine Bauxite")
    extract("ilmenite", "mining", 3, 1, "titanium_metallurgy", "Dredge Ilmenite")
    extract("monazite_sand", "mining", 4, 1, "monazite_processing", "Dredge Monazite Sand")
    extract("wolframite", "mining", 4, 1, "tungsten_metallurgy", "Mine Wolframite")
    extract("rare_earth_ore", "mining", 5, 1, "rare_earth_separation", "Mine Rare-Earth Ore")
    extract("helium_gas", "oil_extraction", 2, 5, "helium_recovery", "Tap Helium Gas")

    # =====================================================================================
    # TIER 0 — stone furnace and fitting bench era
    # =====================================================================================
    m("iron_ingot", "Iron Ingot", "materials", 0, V("ingot", "iron"), "Rough-cast pig iron, the root of most metalwork.",
      ("smelting", 3, {"iron_ore": 2}))
    m("copper_ingot", "Copper Ingot", "materials", 0, V("ingot", "copper"), "Fire-refined copper ready for drawing and pressing.",
      ("smelting", 3, {"copper_ore": 2}))
    m("stone_brick", "Stone Brick", "materials", 0, V("brick", "stone"), "Kiln-fired block for furnaces and footings.",
      ("smelting", 4, {"stone": 3}, 2))
    m("iron_plate", "Iron Plate", "intermediates", 0, V("plate", "iron"), "Pressed iron plate used in nearly everything.",
      ("pressing", 1.5, {"iron_ingot": 1}, 2))
    m("copper_sheet", "Copper Sheet", "intermediates", 0, V("plate", "copper"), "Thin rolled copper for contacts and heat spreaders.",
      ("pressing", 1.5, {"copper_ingot": 1}, 2))
    m("iron_rod", "Iron Rod", "intermediates", 0, V("rod", "iron"), "Drawn iron bar stock for shafts and fasteners.",
      ("pressing", 1, {"iron_ingot": 1}, 2))
    m("copper_wire", "Copper Wire", "intermediates", 0, V("wire_spool", "copper"), "Drawn copper wire on a wooden spool.",
      ("pressing", 1, {"copper_ingot": 1}, 3))
    m("iron_gear", "Iron Gear", "intermediates", 0, V("gear", "iron"), "Cut spur gear for drives and mechanisms.",
      ("assembling", 2, {"iron_plate": 3}, 2))
    m("iron_pipe", "Iron Pipe", "intermediates", 0, V("pipe", "iron"), "Rolled and seamed pipe section for fluids and steam.",
      ("assembling", 1.5, {"iron_plate": 2}))
    m("fasteners", "Fasteners", "intermediates", 0, V("bolts", "iron"), "Bolts, nuts and washers by the bucket.",
      ("assembling", 1, {"iron_rod": 1}, 4))
    gas("steam", "Steam", 0, "steam", "Low-pressure steam that drives piston engines.",
        ("boiling", 1, {"water": 40}, 40))

    # =====================================================================================
    # TIER 1 — coke, steel, lime, glass, mechanisms
    # =====================================================================================
    m("coke", "Coke", "materials", 1, V("ore_chunks", "graphite"), "Baked coal: hot-burning fuel and steelmaking reductant.",
      ("smelting", 5, {"coal": 3}, 2), "coking", fuel_kj=5000.0, fuel_class="chemical", pollution_mult=0.8)
    m("slag", "Slag", "materials", 1, V("gravel_pile", "stone", (0.3, 0.28, 0.27)), "Glassy furnace residue; reground into aggregate or cement.")
    m("scrap_metal", "Scrap Metal", "materials", 1, V("gravel_pile", "steel"), "Offcuts and trimmings from heavy rolling.")
    m("steel_ingot", "Steel Ingot", "materials", 1, V("ingot", "steel"), "Carbon steel cast from iron and coke.")
    alt("steel_ingot", "Steel Ingot", "smelting", 8, {"iron_ingot": 3, "coke": 1}, {"steel_ingot": 2, "slag": 1}, "steelmaking",
        weights={"steel_ingot": 9, "slag": 1})
    m("steel_plate", "Steel Plate", "intermediates", 1, V("plate", "steel"), "Hot-rolled plate for frames, tanks and armor.",
      ("pressing", 2, {"steel_ingot": 1}, 2), "steelmaking")
    m("steel_beam", "Steel Beam", "intermediates", 1, V("beam", "steel"), "Rolled I-beam for heavy structures.")
    alt("steel_beam", "Steel Beam", "pressing", 4, {"steel_ingot": 3}, {"steel_beam": 1, "scrap_metal": 1}, "steelmaking",
        weights={"steel_beam": 9, "scrap_metal": 1})
    alt("remelt_scrap", "Scrap Remelt", "recycling", 6, {"scrap_metal": 5}, {"steel_ingot": 3}, "scrap_reclamation")
    alt("regrind_slag", "Slag Regrinding", "recycling", 4, {"slag": 4}, {"gravel": 3, "iron_ingot": 1}, "scrap_reclamation",
        weights={"gravel": 1, "iron_ingot": 2})
    m("quicklime", "Quicklime", "materials", 1, V("powder_pile", "limestone"), "Calcined lime for cement, glass and flux.",
      ("smelting", 5, {"limestone": 2}), "quarrying")
    m("gravel", "Gravel", "materials", 1, V("gravel_pile", "stone"), "Crushed aggregate for concrete and roadbeds.",
      ("crushing", 2, {"stone": 2}, 3), "quarrying")
    m("cement", "Cement", "materials", 1, V("bag", "concrete"), "Ground clinker powder in paper sacks.",
      ("crushing", 4, {"quicklime": 1, "gravel": 2}, 3), "cement_works")
    alt("slag_cement", "Slag Cement", "crushing", 4, {"slag": 2, "quicklime": 1}, {"cement": 3}, "cement_works")
    m("concrete", "Concrete Slab", "materials", 1, V("block", "concrete"), "Precast slab for foundations, walls and pads.",
      ("mixing", 5, {"cement": 1, "gravel": 2, "water": 20}, 2), "cement_works")
    m("glass_pane", "Glass Pane", "materials", 1, V("glass_pane", "glass"), "Soda-lime glass for windows, gauges and cells.",
      ("smelting", 6, {"quartz_sand": 4, "quicklime": 1}, 2), "glassmaking")
    m("gearbox", "Gearbox", "intermediates", 1, V("gear", "cast_iron", params={"variant": "housing"}), "Enclosed reduction gearing for heavy drives.",
      ("assembling", 4, {"iron_gear": 4, "steel_plate": 1, "fasteners": 4}), "mechanical_engineering")
    m("coil_spring", "Coil Spring", "intermediates", 1, V("spring", "steel"), "Tempered spring for valves and recoil systems.",
      ("assembling", 1, {"iron_rod": 1}, 2), "mechanical_engineering")
    m("valve", "Valve", "intermediates", 1, V("nozzle", "cast_iron", params={"variant": "valve"}), "Spring-loaded gate valve for pipework.",
      ("assembling", 3, {"iron_pipe": 2, "coil_spring": 1, "fasteners": 2}), "mechanical_engineering")
    m("steel_frame", "Steel Frame", "components", 1, V("frame", "steel"), "Bolted structural frame for machines and towers.",
      ("assembling", 5, {"steel_beam": 2, "fasteners": 6}), "structural_steel")

    # =====================================================================================
    # TIER 2 — tin, motors, circuit boards
    # =====================================================================================
    m("tin_ingot", "Tin Ingot", "materials", 2, V("ingot", "tin"), "Soft white tin reduced from cassiterite.",
      ("smelting", 5, {"cassiterite": 3, "coke": 1}, 2), "tin_smelting")
    m("solder", "Solder", "materials", 2, V("wire_spool", "tin"), "Tin-copper solder wire for joining circuits.",
      ("smelting", 3, {"tin_ingot": 3, "copper_ingot": 1}, 4), "tin_smelting")
    m("bronze_ingot", "Bronze Ingot", "materials", 2, V("ingot", "bronze"), "Hard-wearing tin bronze for bushings.",
      ("smelting", 5, {"copper_ingot": 3, "tin_ingot": 1}, 4), "tin_smelting")
    m("ceramic_substrate", "Ceramic Substrate", "intermediates", 2, V("plate", "ceramic"), "Fired insulating wafer that carries circuitry.",
      ("smelting", 4, {"stone": 1, "quartz_sand": 2}, 2), "circuit_theory")
    m("circuit_board", "Circuit Board", "components", 2, V("circuit_board", "pcb_green"), "Soldered board with discrete logic on ceramic.",
      ("electronics", 6, {"ceramic_substrate": 1, "copper_wire": 4, "solder": 1}, 2), "circuit_theory")
    m("bearing", "Bearing", "intermediates", 2, V("bearing", "bronze"), "Bronze-caged steel bearing for rotating shafts.",
      ("assembling", 3, {"bronze_ingot": 1, "steel_plate": 1}, 2), "electromagnetism")
    m("electromagnet", "Electromagnet", "intermediates", 2, V("magnet", "copper"), "Copper-wound iron core.",
      ("assembling", 3, {"iron_rod": 1, "copper_wire": 6}), "electromagnetism")
    m("electric_motor", "Electric Motor", "components", 2, V("motor", "steel"), "Squirrel-cage induction motor for drives and pumps.",
      ("assembling", 6, {"electromagnet": 2, "bearing": 2, "steel_plate": 1}), "electromagnetism")
    m("capacitor", "Capacitor", "intermediates", 2, V("cell", "tin"), "Ceramic-layered capacitor that smooths power.",
      ("electronics", 3, {"copper_sheet": 1, "ceramic_substrate": 1}, 4), "passive_components")
    m("optical_sensor", "Optical Sensor", "components", 2, V("lens", "glass", (0.6, 0.3, 0.3)), "Photocell eye for counting, aiming and sorting.",
      ("electronics", 5, {"glass_pane": 1, "circuit_board": 1, "copper_wire": 2}), "passive_components")
    m("pv_cell", "Photovoltaic Cell", "components", 2, V("solar_cell", "glass", (0.15, 0.2, 0.45)), "Copper-oxide junction cell behind glass.",
      ("electronics", 6, {"glass_pane": 1, "copper_sheet": 2, "solder": 1}), "photovoltaics")
    m("pump_unit", "Pump Unit", "components", 2, V("motor", "cast_iron", params={"variant": "pump"}), "Motor-driven centrifugal pump.",
      ("assembling", 5, {"electric_motor": 1, "valve": 2, "iron_pipe": 2}), "hydraulics")

    # =====================================================================================
    # TIER 3 — oil, chemistry, bio
    # =====================================================================================
    liquid("heavy_oil", "Heavy Oil", 3, "heavy", "Thick distillation bottoms for lubricants and anodes.")
    liquid("naphtha", "Naphtha", 3, "naphtha", "Light distillate feeding polymers, rubber and solvents.")
    gas("fuel_gas", "Fuel Gas", 3, "fuel_gas", "Light hydrocarbon gas burned in turbines and crackers.")
    alt("crude_distillation", "Crude Distillation", "refining", 5, {"crude_oil": 100},
        {"heavy_oil": 20, "naphtha": 50, "fuel_gas": 30}, "oil_refining",
        weights={"heavy_oil": 20, "naphtha": 55, "fuel_gas": 25})
    alt("thermal_cracking", "Thermal Cracking", "refining", 4, {"heavy_oil": 40, "steam": 20},
        {"naphtha": 30, "fuel_gas": 10}, "oil_refining", weights={"naphtha": 3, "fuel_gas": 1})
    m("sulfur", "Sulfur", "materials", 3, V("powder_pile", "sulfur"), "Bright yellow sulfur for acid, rubber and powder.",
      ("crushing", 3, {"native_sulfur": 1}, 2), "sulfur_processing")
    alt("gas_sweetening", "Gas Sweetening", "refining", 4, {"natural_gas": 100}, {"fuel_gas": 90, "sulfur": 1},
        "gas_processing", weights={"fuel_gas": 9, "sulfur": 1})
    liquid("sulfuric_acid", "Sulfuric Acid", 3, "acid", "Oily, corrosive acid used across heavy chemistry.",
           ("chemistry", 2, {"sulfur": 2, "water": 40}, 40), "sulfur_processing")
    liquid("lubricant", "Lubricant", 3, "lube", "Blended base oil that keeps heavy machinery turning.",
           ("chemistry", 2, {"heavy_oil": 20}, 15), "lubricants")
    m("plastic_pellets", "Plastic Pellets", "materials", 3, V("pellets", "plastic_white"), "Polyethylene nurdles for molding and extrusion.",
      ("chemistry", 2, {"naphtha": 20, "fuel_gas": 10}, 2), "polymer_chemistry")
    m("plastic_sheet", "Plastic Sheet", "intermediates", 3, V("sheet_coil", "plastic_white"), "Extruded polymer sheet for housings and film.",
      ("pressing", 2, {"plastic_pellets": 2}), "polymer_chemistry")
    m("rubber", "Rubber", "materials", 3, V("block", "rubber"), "Sulfur-vulcanized synthetic rubber.",
      ("chemistry", 3, {"naphtha": 10, "sulfur": 1}, 2), "synthetic_rubber")
    m("insulated_cable", "Insulated Cable", "intermediates", 3, V("cable_coil", "rubber"), "Rubber-jacketed copper power cable.",
      ("assembling", 2, {"copper_wire": 4, "rubber": 1}, 2), "synthetic_rubber")
    gas("chlorine", "Chlorine", 3, "chlorine", "Toxic green gas for resins, acids and titanium refining.")
    gas("hydrogen", "Hydrogen", 3, "hydrogen", "Light reducing gas from electrolysis.")
    m("caustic_soda", "Caustic Soda", "materials", 3, V("pellets", "salt"), "Sodium hydroxide flakes for alumina and batteries.")
    alt("brine_electrolysis", "Brine Electrolysis", "electrolysis", 4, {"brine": 60},
        {"chlorine": 20, "hydrogen": 20, "caustic_soda": 2}, "chlor_alkali",
        weights={"chlorine": 3, "hydrogen": 2, "caustic_soda": 3})
    m("salt", "Salt", "materials", 3, V("powder_pile", "salt"), "Evaporated sodium chloride crystals.")
    m("potash", "Potash", "materials", 3, V("powder_pile", "salt", (0.85, 0.55, 0.45)), "Potassium salts for fertilizer and blasting powder.")
    alt("brine_evaporation", "Brine Evaporation", "chemistry", 5, {"brine": 80}, {"salt": 3, "potash": 1},
        "brine_evaporation", weights={"salt": 1, "potash": 1})
    m("battery_cell", "Sodium-Sulfur Cell", "components", 3, V("battery", "steel"), "Hot-running grid battery cell.",
      ("chemistry", 6, {"sulfur": 2, "caustic_soda": 1, "steel_plate": 1, "ceramic_substrate": 1}), "sodium_sulfur_batteries")
    m("epoxy_resin", "Epoxy Resin", "materials", 3, V("canister", "plastic_color", (0.85, 0.6, 0.2)), "Two-part resin for laminates and composites.",
      ("chemistry", 3, {"naphtha": 10, "chlorine": 10}, 2), "epoxy_resins")
    m("glass_fiber", "Glass Fiber", "materials", 3, V("cable_coil", "glass"), "Spun glass filament for laminates and optics.",
      ("smelting", 3, {"glass_pane": 1}, 3), "epoxy_resins")
    m("fiberglass_panel", "Fiberglass Laminate", "intermediates", 3, V("plate", "plastic_color", (0.75, 0.8, 0.45)), "Glass-epoxy laminate board.",
      ("pressing", 4, {"glass_fiber": 4, "epoxy_resin": 1}, 2), "epoxy_resins")
    m("control_board", "Control Board", "components", 3, V("circuit_board", "pcb_blue"), "Multilayer laminate board running machine logic.",
      ("electronics", 8, {"circuit_board": 3, "capacitor": 4, "fiberglass_panel": 1}), "control_systems")
    m("hydraulic_ram", "Hydraulic Ram", "components", 3, V("rod", "stainless", params={"variant": "cylinder"}), "Oil-filled cylinder for presses and booms.",
      ("assembling", 4, {"steel_plate": 2, "valve": 1, "lubricant": 10}), "lubricants")
    m("filter_cartridge", "Filter Cartridge", "components", 3, V("filter", "plastic_white"), "Activated-carbon cartridge for scrubbers and life support.",
      ("assembling", 4, {"coke": 2, "plastic_sheet": 1}), "precipitators")
    m("fuel_briquette", "Fuel Briquette", "materials", 3, V("block", "coal"), "Pressed coke and pitch; a long, clean burn.",
      ("pressing", 3, {"coke": 2, "heavy_oil": 10}, 2), "fuel_briquettes", fuel_kj=9000.0, fuel_class="chemical", pollution_mult=0.7)
    m("algae_paste", "Algae Paste", "materials", 3, V("flask", "glass", (0.25, 0.5, 0.15)), "Harvested microalgae concentrate.",
      ("bioprocessing", 10, {"water": 60, "potash": 1}, 5), "algae_cultivation")
    liquid("bio_oil", "Bio-Oil", 3, "bio", "Pressed algal lipids; a renewable feedstock.",
           ("bioprocessing", 5, {"algae_paste": 5}, 30), "algae_cultivation")
    alt("bio_lubricant", "Bio-Lubricant", "chemistry", 3, {"bio_oil": 20}, {"lubricant": 20}, "algae_cultivation")
    m("biofuel_pellet", "Biofuel Pellet", "materials", 3, V("pellets", "wood", (0.45, 0.5, 0.2)), "Dried algae pellets that burn with little smoke.",
      ("bioprocessing", 6, {"algae_paste": 4}, 2), "algae_cultivation", fuel_kj=6000.0, fuel_class="chemical", pollution_mult=0.3)
    m("blasting_powder", "Blasting Powder", "materials", 3, V("powder_pile", "graphite", (0.2, 0.2, 0.2)), "Potash-sulfur powder for shells and quarrying.",
      ("mixing", 4, {"sulfur": 1, "coke": 1, "potash": 1}, 3), "blasting_compounds")

    # =====================================================================================
    # TIER 4 — aluminum, titanium, silicon, composites, precision
    # =====================================================================================
    m("alumina", "Alumina", "materials", 4, V("powder_pile", "ceramic"), "White aluminum oxide from the Bayer process.")
    m("red_mud", "Red Mud", "materials", 4, V("powder_pile", "bauxite", (0.55, 0.2, 0.1)), "Iron-rich digestion residue; worth reclaiming.")
    alt("bayer_digestion", "Bayer Digestion", "chemistry", 6, {"bauxite": 4, "caustic_soda": 1, "steam": 30},
        {"alumina": 3, "red_mud": 1}, "bayer_process", weights={"alumina": 9, "red_mud": 1})
    alt("reclaim_red_mud", "Red Mud Reclamation", "recycling", 5, {"red_mud": 5},
        {"iron_ingot": 2, "gravel": 2}, "red_mud_recovery", weights={"iron_ingot": 3, "gravel": 1})
    m("carbon_anode", "Carbon Anode", "intermediates", 4, V("block", "graphite"), "Baked pitch-coke anode consumed in smelting pots.",
      ("pressing", 4, {"coke": 4, "heavy_oil": 10}), "aluminum_electrolysis")
    m("aluminum_ingot", "Aluminum Ingot", "materials", 4, V("ingot", "aluminum"), "Electrolytic aluminum, light and corrosion-proof.",
      ("electrolysis", 6, {"alumina": 4, "carbon_anode": 1}, 2), "aluminum_electrolysis")
    m("aluminum_sheet", "Aluminum Sheet", "intermediates", 4, V("sheet_coil", "aluminum"), "Cold-rolled aluminum coil.",
      ("pressing", 2, {"aluminum_ingot": 1}, 2), "aluminum_electrolysis")
    m("aluminum_powder", "Aluminum Powder", "materials", 4, V("powder_pile", "aluminum"), "Fine flake powder for thermite and propellants.",
      ("crushing", 3, {"aluminum_ingot": 1}, 3), "thermite")
    m("magnesium_ingot", "Magnesium Ingot", "materials", 4, V("ingot", "silver"), "Light reactive metal won from brine.")
    alt("magnesium_ingot", "Magnesium Ingot", "electrolysis", 8, {"brine": 150, "quicklime": 1},
        {"magnesium_ingot": 1, "chlorine": 20}, "magnesium_extraction", weights={"magnesium_ingot": 4, "chlorine": 1})
    liquid("titanium_tetrachloride", "Titanium Tetrachloride", 4, "ticl4", "Fuming chloride intermediate of titanium.",
           ("chemistry", 5, {"ilmenite": 3, "coke": 1, "chlorine": 30}, 30), "titanium_metallurgy")
    m("titanium_ingot", "Titanium Ingot", "materials", 4, V("ingot", "titanium"), "Sponge-melted titanium, strong and light.")
    alt("titanium_ingot", "Titanium Ingot", "smelting_advanced", 10, {"titanium_tetrachloride": 40, "magnesium_ingot": 1},
        {"titanium_ingot": 1, "chlorine": 20}, "titanium_metallurgy", weights={"titanium_ingot": 9, "chlorine": 1})
    m("titanium_plate", "Titanium Plate", "intermediates", 4, V("plate", "titanium"), "Rolled titanium for hot and corrosive duty.",
      ("pressing", 3, {"titanium_ingot": 1}, 2), "titanium_metallurgy")
    m("duralumin_ingot", "Duralumin Billet", "materials", 4, V("ingot", "aluminum", (0.8, 0.82, 0.86)), "Age-hardened aluminum-copper alloy.",
      ("foundry", 6, {"aluminum_ingot": 4, "copper_ingot": 1, "magnesium_ingot": 1}, 5), "aerospace_alloys")
    m("titanium_alloy", "Titanium Alloy Bar", "materials", 4, V("rod", "titanium"), "Titanium-aluminum alloy bar for airframes and rotors.",
      ("foundry", 8, {"titanium_ingot": 3, "aluminum_ingot": 1}, 3), "aerospace_alloys")
    m("silicon", "Metallurgical Silicon", "materials", 4, V("ore_chunks", "silicon"), "Arc-reduced silicon lumps.")
    alt("silicon", "Metallurgical Silicon", "smelting_advanced", 6, {"quartz_sand": 3, "coke": 2},
        {"silicon": 1, "slag": 1}, "arc_furnaces", weights={"silicon": 9, "slag": 1})
    liquid("hydrochloric_acid", "Hydrochloric Acid", 4, "hcl", "Strong acid for refining silicon and rare earths.",
           ("chemistry", 1, {"hydrogen": 20, "chlorine": 20}, 40), "semiconductor_refining")
    m("polysilicon", "Polysilicon", "materials", 4, V("crystal_cluster", "silicon"), "Hyper-pure silicon rods for crystal growth.",
      ("chemistry", 6, {"silicon": 2, "hydrochloric_acid": 20}), "semiconductor_refining")
    m("silicon_wafer", "Silicon Wafer", "intermediates", 4, V("plate", "silicon"), "Polished single-crystal wafer.")
    m("silicon_offcuts", "Silicon Offcuts", "materials", 4, V("gravel_pile", "silicon"), "Ingot ends and broken wafers.")
    alt("silicon_wafer", "Silicon Wafer", "smelting_advanced", 10, {"polysilicon": 2},
        {"silicon_wafer": 3, "silicon_offcuts": 1}, "semiconductor_refining", weights={"silicon_wafer": 9, "silicon_offcuts": 1})
    alt("recycle_silicon_offcuts", "Offcut Remelting", "recycling", 4, {"silicon_offcuts": 4}, {"polysilicon": 1},
        "semiconductor_refining")
    m("microchip", "Microchip", "components", 4, V("chip", "pcb_black"), "Lithographed logic die in a plastic package.",
      ("electronics", 6, {"silicon_wafer": 1, "copper_wire": 4, "plastic_pellets": 1}, 4), "microelectronics")
    m("fiber_optic_cable", "Fiber-Optic Cable", "intermediates", 4, V("cable_coil", "plastic_color", (0.95, 0.5, 0.1)), "Jacketed glass fiber for data links.",
      ("assembling", 3, {"glass_fiber": 4, "plastic_sheet": 1}, 2), "fiber_optics")
    m("embedded_controller", "Embedded Controller", "components", 4, V("circuit_board", "pcb_black"), "Board-level computer with on-chip memory.",
      ("electronics", 10, {"control_board": 1, "microchip": 4, "fiber_optic_cable": 1}), "embedded_systems")
    m("acrylic_fiber", "Acrylic Fiber", "materials", 4, V("cable_coil", "plastic_white"), "Spun polyacrylonitrile, the carbon fiber precursor.",
      ("chemistry", 4, {"naphtha": 20, "ammonia": 10}, 3), "carbon_fiber")
    m("carbon_fiber", "Carbon Fiber", "materials", 4, V("sheet_coil", "carbon_fiber"), "Carbonized filament tow, stiff and light.",
      ("smelting_advanced", 6, {"acrylic_fiber": 3}), "carbon_fiber")
    m("composite_panel", "Composite Panel", "components", 4, V("plate", "carbon_fiber"), "Cured carbon-epoxy panel.",
      ("pressing", 5, {"carbon_fiber": 2, "epoxy_resin": 2}), "carbon_fiber")
    m("servo_motor", "Servo Motor", "components", 4, V("motor", "aluminum"), "Closed-loop motor with encoder feedback.",
      ("precision_assembling", 6, {"electric_motor": 1, "microchip": 2, "bearing": 2}), "precision_engineering")
    m("optical_lens", "Optical Lens", "components", 4, V("lens", "glass"), "Ground and coated precision lens.",
      ("precision_assembling", 5, {"glass_pane": 3}), "precision_engineering")
    m("heat_sink", "Heat Sink", "intermediates", 4, V("heat_sink", "aluminum"), "Finned aluminum-copper heat spreader.",
      ("pressing", 3, {"aluminum_sheet": 2, "copper_sheet": 1}), "precision_engineering")
    m("harmonic_drive", "Harmonic Drive", "components", 4, V("gear", "titanium"), "Zero-backlash strain-wave reduction gear.",
      ("precision_assembling", 6, {"titanium_plate": 1, "bearing": 2, "iron_gear": 2}), "harmonic_drives")
    m("robotic_arm", "Robotic Arm", "components", 4, V("servo_arm", "aluminum"), "Six-axis manipulator for automated cells.",
      ("precision_assembling", 12, {"servo_motor": 2, "harmonic_drive": 1, "aluminum_sheet": 2, "embedded_controller": 1}), "robotics")
    gas("oxygen", "Oxygen", 4, "oxygen", "Separated oxygen for oxidizers and acids.")
    gas("nitrogen", "Nitrogen", 4, "nitrogen", "Separated nitrogen for ammonia synthesis.")
    alt("air_separation", "Air Separation", "cryogenics", 4, {"water": 20}, {"oxygen": 40, "nitrogen": 80},
        "air_separation", weights={"oxygen": 1, "nitrogen": 1})
    gas("ammonia", "Ammonia", 4, "ammonia", "Pungent synthesis gas for nitrates, fibers and cultures.",
        ("chemistry", 2, {"hydrogen": 30, "nitrogen": 10}, 20), "nitrogen_chemistry")
    liquid("nitric_acid", "Nitric Acid", 4, "nitric", "Oxidizing acid for high explosives.",
           ("chemistry", 3, {"ammonia": 20, "oxygen": 20, "water": 10}, 20), "nitrogen_chemistry")
    m("soda_ash", "Soda Ash", "materials", 4, V("powder_pile", "salt", (0.95, 0.95, 0.9)), "Sodium carbonate for float glass and lithium salts.",
      ("chemistry", 4, {"salt": 2, "limestone": 1, "ammonia": 5}, 2), "nitrogen_chemistry")
    alt("float_glass", "Float Glass", "smelting", 5, {"quartz_sand": 4, "soda_ash": 1}, {"glass_pane": 4}, "float_glass")
    alt("contact_process", "Contact Process Acid", "chemistry", 2, {"sulfur": 2, "oxygen": 20, "water": 40},
        {"sulfuric_acid": 80}, "contact_process")
    alt("hydrocracking", "Hydrocracking", "refining", 4, {"heavy_oil": 40, "hydrogen": 10}, {"naphtha": 45}, "hydrocracking")
    m("high_explosive", "High Explosive", "materials", 4, V("block", "plastic_color", (0.75, 0.68, 0.5)), "Stable nitrated charge for shells.",
      ("chemistry", 6, {"nitric_acid": 20, "naphtha": 10}, 2), "high_explosives")
    m("lithium_carbonate", "Lithium Carbonate", "materials", 4, V("powder_pile", "lithium"), "Battery-grade lithium salt from brine.")
    alt("lithium_carbonate", "Lithium Carbonate", "chemistry", 6, {"brine": 120, "soda_ash": 1},
        {"lithium_carbonate": 1, "salt": 2}, "lithium_extraction", weights={"lithium_carbonate": 9, "salt": 1})
    m("lithium_cell", "Lithium-Ion Cell", "components", 4, V("cell", "lithium"), "Dense rechargeable cell in an aluminum can.",
      ("electronics", 8, {"lithium_carbonate": 1, "aluminum_sheet": 1, "coke": 1, "plastic_sheet": 1}), "lithium_extraction")
    m("turbine_blade", "Turbine Blade", "components", 4, V("turbine_blade", "titanium"), "Cast titanium-alloy blade with cooling channels.",
      ("foundry", 8, {"titanium_alloy": 1, "ceramic_substrate": 1}, 2), "turbine_engineering")
    m("cargo_drone", "Cargo Drone", "components", 4, V("drone", "aluminum"), "Quad-rotor freight drone for depot logistics.",
      ("precision_assembling", 10, {"electric_motor": 4, "aluminum_sheet": 4, "lithium_cell": 2, "embedded_controller": 1}), "drone_logistics")
    alt("bioleached_copper", "Bioleached Copper", "bioprocessing", 8, {"copper_ore": 8, "sulfuric_acid": 10},
        {"copper_ingot": 5}, "bioleaching")
    alt("bioplastic", "Bioplastic Pellets", "bioprocessing", 4, {"algae_paste": 4, "bio_oil": 10},
        {"plastic_pellets": 3}, "bioplastics")

    # =====================================================================================
    # TIER 5 — nuclear, tungsten, rare earths, aerospace
    # =====================================================================================
    m("thorium_oxide", "Thorium Oxide", "materials", 5, V("powder_pile", "thorium"), "Fertile thoria powder for fuel fabrication.")
    m("rare_earth_oxide", "Rare-Earth Oxide", "materials", 5, V("powder_pile", "crystal", (0.75, 0.6, 0.65)), "Mixed lanthanide oxides for magnets and catalysts.")
    alt("monazite_digestion", "Monazite Digestion", "chemistry", 8, {"monazite_sand": 6, "sulfuric_acid": 30},
        {"thorium_oxide": 1, "rare_earth_oxide": 3}, "monazite_processing", weights={"thorium_oxide": 3, "rare_earth_oxide": 2})
    m("fissile_seed", "Fissile Seed", "materials", 5, V("pellets", "uranium_glass"), "Enriched fissile pellets that kindle the thorium cycle.")
    alt("seed_enrichment", "Seed Enrichment", "centrifuging", 30, {"thorium_oxide": 20},
        {"fissile_seed": 1, "thorium_oxide": 17}, "isotope_centrifuges")
    m("thorium_fuel_rod", "Thorium Fuel Rod", "components", 5, V("fuel_rod", "thorium"), "Clad thoria rod seeded with fissile pellets.",
      ("precision_assembling", 12, {"thorium_oxide": 6, "fissile_seed": 1, "titanium_plate": 2}), "thorium_fuel",
      fuel_kj=480000.0, fuel_class="nuclear")
    m("spent_fuel_rod", "Spent Fuel Rod", "materials", 5, V("fuel_rod", "lead"), "Hot, depleted rod awaiting reprocessing.")
    gas("superheated_steam", "Superheated Steam", 5, "superheated", "High-pressure dry steam for turbines.")
    alt("superheat_steam", "Steam Superheating", "boiling", 1, {"steam": 40}, {"superheated_steam": 40}, "steam_turbines")
    alt("thorium_fission", "Thorium Fission", "fission", 25, {"thorium_fuel_rod": 1, "water": 4000},
        {"superheated_steam": 4000, "spent_fuel_rod": 1}, "thorium_reactors",
        weights={"superheated_steam": 9, "spent_fuel_rod": 1})
    alt("fuel_reprocessing", "Fuel Reprocessing", "centrifuging", 40, {"spent_fuel_rod": 2},
        {"fissile_seed": 2, "thorium_oxide": 6, "rare_earth_oxide": 1}, "fuel_reprocessing",
        weights={"fissile_seed": 6, "thorium_oxide": 3, "rare_earth_oxide": 1})
    m("tungsten_ingot", "Tungsten Ingot", "materials", 5, V("ingot", "tungsten"), "Hydrogen-reduced tungsten, densest of the workshop metals.",
      ("smelting_advanced", 10, {"wolframite": 4, "hydrogen": 20}), "tungsten_metallurgy")
    m("tungsten_carbide", "Tungsten Carbide", "materials", 5, V("block", "tungsten"), "Sintered carbide for bits, nozzles and penetrators.",
      ("smelting_advanced", 8, {"tungsten_ingot": 1, "coke": 1}, 2), "tungsten_metallurgy")
    m("rare_earth_magnet", "Rare-Earth Magnet", "components", 5, V("magnet", "chrome"), "Sintered neodymium-iron magnet.",
      ("smelting_advanced", 8, {"rare_earth_oxide": 2, "iron_ingot": 2}, 2), "rare_earth_magnets")
    m("brushless_motor", "Brushless Motor", "components", 5, V("motor", "aluminum", (0.3, 0.32, 0.36)), "High-torque permanent-magnet motor.",
      ("precision_assembling", 8, {"rare_earth_magnet": 2, "insulated_cable": 2, "bearing": 2, "aluminum_sheet": 1}), "rare_earth_magnets")
    liquid("rocket_kerosene", "Rocket Kerosene", 5, "kerosene", "Refined, sulfur-free kerosene for first stages.",
           ("refining", 4, {"naphtha": 40, "hydrogen": 10}, 30), "rocket_propellants")
    liquid("liquid_oxygen", "Liquid Oxygen", 5, "lox", "Pale blue cryogenic oxidizer.",
           ("cryogenics", 2, {"oxygen": 40}, 20), "rocket_propellants")
    liquid("liquid_hydrogen", "Liquid Hydrogen", 5, "lh2", "Deep-cryogenic upper-stage fuel.",
           ("cryogenics", 3, {"hydrogen": 50}, 20), "cryogenic_liquefaction")
    m("thrust_nozzle", "Thrust Nozzle", "components", 5, V("nozzle", "tungsten"), "Regeneratively cooled bell nozzle.",
      ("precision_assembling", 12, {"tungsten_carbide": 2, "titanium_alloy": 2}), "rocket_engines")
    m("turbopump", "Turbopump", "components", 5, V("motor", "titanium"), "Propellant pump spun by a hot-gas turbine.",
      ("precision_assembling", 10, {"brushless_motor": 1, "turbine_blade": 2, "bearing": 4, "valve": 2}), "rocket_engines")
    m("rocket_engine", "Rocket Engine", "components", 5, V("rocket_part", "titanium"), "Liquid-fuel engine for heavy lift.",
      ("precision_assembling", 20, {"thrust_nozzle": 1, "turbopump": 2, "valve": 4, "liquid_oxygen": 50}), "rocket_engines")
    m("flight_computer", "Flight Computer", "components", 5, V("processor", "pcb_black"), "Radiation-tolerant triple-redundant computer.",
      ("electronics", 12, {"embedded_controller": 2, "lithium_cell": 1, "heat_sink": 2}), "avionics")
    m("gyroscope", "Ring-Laser Gyroscope", "components", 5, V("capsule", "aluminum"), "Laser loop that senses rotation without moving parts.",
      ("precision_assembling", 8, {"optical_lens": 2, "fiber_optic_cable": 2, "microchip": 2}), "avionics")
    m("antenna_array", "Phased Antenna Array", "components", 4, V("antenna", "aluminum"), "Electronically steered antenna panel.",
      ("electronics", 10, {"microchip": 4, "aluminum_sheet": 4, "fiber_optic_cable": 2}), "phased_arrays")
    m("avionics_suite", "Avionics Suite", "components", 5, V("crate", "aluminum", params={"variant": "avionics"}), "Racked navigation, guidance and comms.",
      ("precision_assembling", 15, {"flight_computer": 1, "gyroscope": 2, "antenna_array": 1}), "avionics")
    m("airframe_panel", "Airframe Panel", "components", 4, V("frame", "aluminum"), "Riveted duralumin-composite skin section.",
      ("precision_assembling", 10, {"duralumin_ingot": 3, "composite_panel": 2, "fasteners": 8}), "airframes")
    m("heat_shield_tile", "Heat Shield Tile", "components", 5, V("brick", "ceramic", (0.15, 0.15, 0.15)), "Silica-alumina tile that shrugs off re-entry heat.",
      ("smelting_advanced", 6, {"alumina": 2, "glass_fiber": 2}, 2), "heat_shielding")
    m("enzyme_culture", "Enzyme Culture", "materials", 5, V("flask", "glass", (0.85, 0.75, 0.3)), "Engineered microbes that bind metals and digest feedstock.",
      ("bioprocessing", 10, {"algae_paste": 3, "ammonia": 10}, 2), "fermentation")
    m("survey_probe", "Survey Probe", "components", 5, V("rocket_part", "aluminum", (0.9, 0.9, 0.9)), "Sub-orbital probe that maps deep deposits.",
      ("precision_assembling", 30, {"avionics_suite": 1, "rocket_engine": 1, "airframe_panel": 2, "lithium_cell": 4}), "launch_complex")

    # =====================================================================================
    # TIER 6 — superconductors, quantum, nano, fusion
    # =====================================================================================
    liquid("liquid_helium", "Liquid Helium", 6, "lhe", "Near-absolute-zero coolant for superconductors.",
           ("cryogenics", 4, {"helium_gas": 40}, 10), "helium_recovery")
    m("yttrium_oxide", "Yttrium Oxide", "materials", 6, V("powder_pile", "crystal", (0.95, 0.95, 0.98)), "Pure yttria for superconducting ceramics.")
    alt("solvent_extraction", "Rare-Earth Solvent Extraction", "chemistry", 8, {"rare_earth_ore": 5, "hydrochloric_acid": 30},
        {"rare_earth_oxide": 3, "yttrium_oxide": 1}, "rare_earth_separation", weights={"rare_earth_oxide": 1, "yttrium_oxide": 2})
    alt("biosorption", "Rare-Earth Biosorption", "bioprocessing", 10, {"rare_earth_ore": 5, "enzyme_culture": 1},
        {"rare_earth_oxide": 4, "yttrium_oxide": 2}, "biosorption", weights={"rare_earth_oxide": 1, "yttrium_oxide": 2})
    m("superconductor_tape", "Superconductor Tape", "components", 6, V("sheet_coil", "copper", (0.3, 0.3, 0.35)), "Yttrium-copper-oxide film on metal tape.",
      ("nanofab", 10, {"yttrium_oxide": 1, "copper_sheet": 4, "titanium_plate": 1, "oxygen": 20}, 3), "superconductors")
    m("cryocooler", "Cryocooler", "components", 6, V("tank_part", "stainless"), "Closed-cycle refrigerator holding millikelvin stages.",
      ("precision_assembling", 12, {"liquid_helium": 20, "brushless_motor": 1, "heat_sink": 2}), "cryocoolers")
    m("qubit_array", "Qubit Array", "components", 6, V("chip", "gold"), "Superconducting qubit lattice on a sapphire die.",
      ("nanofab", 15, {"silicon_wafer": 2, "superconductor_tape": 2, "microchip": 4}), "qubit_fabrication")
    m("graphene", "Graphene Film", "materials", 6, V("plate", "graphite", (0.1, 0.1, 0.12)), "Single-atom carbon film grown on copper foil.",
      ("nanofab", 6, {"fuel_gas": 40, "copper_sheet": 1}, 2), "graphene_synthesis")
    m("carbon_nanotube", "Carbon Nanotube Yarn", "materials", 6, V("cable_coil", "carbon_fiber"), "Spun nanotube yarn, stronger than steel cable.",
      ("nanofab", 8, {"fuel_gas": 30, "iron_plate": 1}, 3), "carbon_nanotubes")
    m("metamaterial_lattice", "Metamaterial Lattice", "components", 6, V("frame", "crystal", (0.4, 0.75, 0.9)), "Engineered nano-lattice with tuned stiffness and optics.",
      ("nanofab", 20, {"graphene": 2, "titanium_alloy": 1, "carbon_nanotube": 3}), "metamaterials")
    m("nano_coating", "Nano-Ceramic Coating", "materials", 6, V("canister", "ceramic", (0.85, 0.88, 0.95)), "Self-healing ceramic coating for hulls and armor.",
      ("nanofab", 10, {"alumina": 2, "carbon_nanotube": 1, "epoxy_resin": 1}, 2), "nano_coatings")
    m("quantum_processor", "Quantum Processor", "components", 6, V("processor", "gold", (1.0, 0.85, 0.5)), "Cryo-packaged qubit processor with classical control.",
      ("nanofab", 25, {"qubit_array": 2, "cryocooler": 1, "embedded_controller": 2}), "quantum_computing")
    gas("deuterium", "Deuterium", 6, "deuterium", "Heavy hydrogen isotope for fusion fuel.")
    alt("isotopic_electrolysis", "Isotopic Water Electrolysis", "electrolysis", 10, {"water": 600},
        {"hydrogen": 400, "oxygen": 180, "deuterium": 6}, "deuterium_separation",
        weights={"hydrogen": 2, "oxygen": 1, "deuterium": 5})
    m("fusion_pellet", "Fusion Fuel Pellet", "components", 6, V("pellets", "glow", (0.4, 0.9, 1.0)), "Deuterium-lithium target pellet.",
      ("precision_assembling", 10, {"deuterium": 40, "lithium_carbonate": 2, "graphene": 1}, 4), "fusion_fuel",
      fuel_kj=1800000.0, fuel_class="fusion")
    alt("dt_fusion", "Deuterium-Lithium Fusion", "fusion", 25, {"fusion_pellet": 1, "water": 15000},
        {"superheated_steam": 15000, "helium_gas": 20}, "fusion_power", weights={"superheated_steam": 19, "helium_gas": 1})
    alt("thorium_breeding", "Thorium Breeding Cycle", "fission", 25, {"thorium_fuel_rod": 1, "thorium_oxide": 10, "water": 3000},
        {"superheated_steam": 3000, "spent_fuel_rod": 1, "fissile_seed": 1}, "breeder_reactors",
        weights={"superheated_steam": 7, "spent_fuel_rod": 1, "fissile_seed": 2})
    m("plasma_coil", "Plasma Containment Coil", "components", 6, V("magnet", "glow", (0.6, 0.3, 1.0)), "Superconducting field coil for plasma confinement.",
      ("precision_assembling", 20, {"superconductor_tape": 6, "rare_earth_magnet": 2, "liquid_helium": 20, "steel_frame": 1}), "plasma_confinement")
    m("nutrient_paste", "Nutrient Paste", "materials", 6, V("flask", "plastic_white", (0.8, 0.7, 0.45)), "Complete synthetic food for long voyages.",
      ("bioprocessing", 10, {"algae_paste": 4, "enzyme_culture": 1, "water": 40}, 3), "nutrient_synthesis")
    m("coil_accelerator_segment", "Coil Accelerator Segment", "megaproject", 6, V("tank_part", "copper", (0.5, 0.35, 0.2)), "One stage of a superconducting launch rail.",
      ("precision_assembling", 30, {"superconductor_tape": 8, "steel_frame": 4, "lithium_cell": 6, "concrete": 10}), "mass_driver_engineering")

    # =====================================================================================
    # TIER 7 — Orbital Ark parts (orbital assembly)
    # =====================================================================================
    mp = "megaproject"
    m("heavy_launch_vehicle", "Heavy Launch Vehicle", mp, 7, V("rocket_part", "paint", (0.92, 0.92, 0.9)), "Fully fuelled heavy-lift stack ready for the pad.",
      ("orbital", 60, {"rocket_engine": 9, "airframe_panel": 20, "avionics_suite": 2, "heat_shield_tile": 20, "rocket_kerosene": 2000, "liquid_hydrogen": 1000}), "orbital_assembly")
    m("ark_hull_segment", "Ark Hull Segment", mp, 7, V("tank_part", "titanium"), "Pressure hull section with lattice armor.",
      ("orbital", 45, {"metamaterial_lattice": 4, "titanium_alloy": 20, "composite_panel": 10, "nano_coating": 6}), "ark_structures")
    m("ark_drive_nacelle", "Plasma Drive Nacelle", mp, 7, V("rocket_part", "tungsten", (0.6, 0.4, 1.0)), "Magnetic nozzle drive for the long voyage.",
      ("orbital", 60, {"plasma_coil": 4, "rocket_engine": 2, "tungsten_carbide": 10, "superconductor_tape": 6}), "ark_propulsion")
    m("ark_fusion_core", "Ark Fusion Core", mp, 7, V("capsule", "glow", (0.5, 0.9, 1.0)), "Compact tokamak heart of the Ark.",
      ("orbital", 90, {"plasma_coil": 8, "fusion_pellet": 40, "quantum_processor": 2, "cryocooler": 4}), "ark_fusion_core")
    m("ark_habitat_module", "Habitat Ring Module", mp, 7, V("tank_part", "aluminum", (0.9, 0.9, 0.88)), "Spun habitat ring section with living decks.",
      ("orbital", 60, {"composite_panel": 20, "glass_pane": 40, "lithium_cell": 20, "nano_coating": 4}), "ark_habitation")
    m("cryostasis_pod", "Cryostasis Pod", mp, 7, V("capsule", "glass", (0.7, 0.9, 1.0)), "Sleeper berth for the colonists.",
      ("orbital", 30, {"cryocooler": 2, "composite_panel": 4, "flight_computer": 1, "glass_pane": 4}), "ark_habitation")
    m("ark_life_support", "Closed-Loop Life Support", mp, 7, V("tank_part", "stainless", (0.5, 0.8, 0.5)), "Algae-scrubbed air and water loop.",
      ("orbital", 60, {"nutrient_paste": 40, "algae_paste": 40, "filter_cartridge": 20, "pump_unit": 6}), "ark_life_support")
    m("seed_vault", "Seed Vault Capsule", mp, 7, V("capsule", "titanium", (0.45, 0.7, 0.4)), "Cold archive of crops, cultures and soil biota.",
      ("bioprocessing", 60, {"enzyme_culture": 10, "nutrient_paste": 10, "cryocooler": 2, "titanium_plate": 10}), "ark_life_support")
    m("ark_navigation_core", "Deep-Space Navigation Core", mp, 7, V("processor", "glow", (1.0, 0.75, 0.3)), "Quantum navigator for interstellar dead reckoning.",
      ("orbital", 90, {"quantum_processor": 4, "avionics_suite": 4, "gyroscope": 8}), "ark_navigation")

    # =====================================================================================
    # RESEARCH DATA
    # =====================================================================================
    r = "research"
    m("blueprint_sheet", "Blueprint Sheets", r, 1, V("plate_stack", "paint", (0.15, 0.3, 0.7)), "Etched copper drafting plates of machine designs.",
      ("assembling", 6, {"copper_sheet": 1, "iron_rod": 1, "fasteners": 2}), None)
    m("circuit_schematic", "Circuit Schematics", r, 2, V("circuit_board", "pcb_blue", params={"variant": "annotated"}), "Annotated test boards tracing new logic.",
      ("electronics", 8, {"circuit_board": 2, "gearbox": 1, "glass_pane": 1}, 2), "circuit_theory")
    m("chemical_assay", "Chemical Assays", r, 3, V("flask", "glass", (0.3, 0.75, 0.4)), "Sealed reagent kits with logged reaction results.",
      ("chemistry", 10, {"sulfuric_acid": 20, "plastic_sheet": 2, "optical_sensor": 1, "insulated_cable": 2}, 2), "chemical_assays")
    m("alloy_specimen", "Alloy Specimens", r, 4, V("capsule", "titanium", (0.7, 0.72, 0.78)), "Stress-tested coupons of experimental alloys.",
      ("foundry", 12, {"titanium_alloy": 1, "duralumin_ingot": 2, "fiberglass_panel": 1}, 2), "materials_testing")
    m("flight_telemetry", "Flight Telemetry", r, 5, V("canister", "paint", (1.0, 0.45, 0.05)), "Data recorders recovered from test flights.",
      ("precision_assembling", 20, {"airframe_panel": 1, "antenna_array": 1, "rocket_kerosene": 30}, 3), "flight_testing")
    m("quantum_datacore", "Quantum Datacores", r, 6, V("crystal_cluster", "crystal", (0.3, 0.9, 0.95)), "Cryo-sealed qubit stores of experimental results.",
      ("precision_assembling", 25, {"qubit_array": 1, "cryocooler": 1, "fiber_optic_cable": 4}, 2), "quantum_datacores")
    m("field_report", "Field Reports", r, 2, V("bag", "paint", (0.4, 0.42, 0.25)), "After-action dispatches from the frontier patrols.",
      ("assembling", 10, {"steel_core_rounds": 4, "optical_sensor": 1, "concrete": 2}, 2), "field_reporting")
