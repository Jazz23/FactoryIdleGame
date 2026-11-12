"""Buildings. Every building is also an item (group by role) crafted by an `assembling` recipe
whose id equals the building id and whose unlocked_by equals the building's unlocked_by.

Power balance (speed 1.0, documented in CONTENT_STATS.md):
  * Burner Boiler: 2400 kW fuel -> 40 steam/s; Steam Engine eats 20 steam/s -> 900 kW.  1 boiler : 2 engines.
  * High-Pressure Boiler (speed 2.5): 6000 kW fuel -> 100 steam/s.                       1 boiler : 5 engines.
  * Fired Superheater: 2400 kW fuel, 40 steam -> 40 superheated/s; Steam Turbine eats 40/s -> 4000 kW.
  * Thorium Reactor: 1 rod / 25 s -> 160 superheated/s.                                   1 reactor : 4 turbines.
  * Breeder Reactor (speed 2): 240 superheated/s (breeding recipe).                        1 reactor : 6 turbines.
  * Tokamak: 1 pellet / 25 s -> 600 superheated/s.                                         1 tokamak : 15 turbines.
  * Gas Turbine 10 fuel gas/s -> 3000 kW; Combined-Cycle Turbine 20 fuel gas/s -> 9000 kW.
"""
from common import C, V, add_item, add_recipe

ROLE_GROUP = {"producer": "production", "generator": "power", "storage": "logistics", "research": "production",
              "logistics": "logistics", "defense": "defense", "support": "production", "megaproject": "megaproject"}
BUILD_TIME = [3, 5, 8, 10, 15, 20, 30, 45]

TIER_PAINT = [
    ((0.45, 0.38, 0.3), (0.7, 0.5, 0.2), None),
    ((0.35, 0.42, 0.3), (0.85, 0.65, 0.15), None),
    ((0.2, 0.45, 0.55), (0.9, 0.7, 0.1), None),
    ((0.25, 0.35, 0.6), (0.95, 0.55, 0.1), None),
    ((0.82, 0.82, 0.8), (0.95, 0.45, 0.1), None),
    ((0.9, 0.9, 0.88), (0.2, 0.35, 0.7), None),
    ((0.2, 0.21, 0.24), (0.3, 0.8, 0.95), (0.3, 0.8, 1.0)),
    ((0.92, 0.92, 0.95), (0.95, 0.75, 0.3), (1.0, 0.8, 0.4)),
]
DEFENSE_PAINT = (0.33, 0.36, 0.3)

OPTIONAL_ORDER = ["power_out_kw", "generator", "capacity_kj"]
OPTIONAL_TAIL = ["storage_slots", "storage_kind", "defense", "ammo", "ammo_per_min", "support", "throughput",
                 "fluid_throughput"]


def B(bid, name, role, tier, unlock, arch, size, desc, cost, cats=(), speed=1.0, power=0.0, burner=False,
      fuel_kw=0.0, pollution=0.0, slots=0, mat="steel", paint=None, accent=None, glow=None, smoke=False,
      variant=None, group=None, **extra):
    tp, ta, tg = TIER_PAINT[tier]
    if role == "defense" and paint is None:
        paint = DEFENSE_PAINT
    params = {"tier": min(4, 1 + tier // 2), "paint": list(paint or tp), "accent": list(accent or ta)}
    if glow or tg:
        params["glow"] = list(glow or tg)
    params["smoke"] = bool(smoke)
    if variant:
        params["variant"] = variant
    d = {"id": bid, "name": name, "desc": desc, "role": role, "categories": list(cats), "speed": float(speed),
         "power_kw": float(power), "burner": burner, "fuel_kw": float(fuel_kw)}
    for k in OPTIONAL_ORDER:
        if k in extra:
            d[k] = extra.pop(k)
    d["module_slots"] = slots
    d["pollution"] = float(pollution)
    for k in OPTIONAL_TAIL:
        if k in extra:
            d[k] = extra.pop(k)
    if extra:
        C.errors.append(f"buildings: '{bid}' has unknown fields {sorted(extra)}")
    d["size"] = list(size)
    d["tier"] = tier
    d["unlocked_by"] = unlock
    d["visual"] = V(arch, mat, **params)
    if bid in C.buildings:
        C.errors.append(f"buildings: duplicate id '{bid}'")
    C.buildings[bid] = d
    add_item(bid, name, group or ROLE_GROUP[role], tier, V("building_kit", "wood", building=bid), desc)
    add_recipe(bid, name, "assembling", BUILD_TIME[tier], cost, {bid: 1}, unlock)


def P(bid, name, tier, unlock, arch, size, desc, cost, cats, speed, power=0.0, **kw):
    B(bid, name, "producer", tier, unlock, arch, size, desc, cost, cats=cats, speed=speed, power=power, **kw)


def GEN(bid, name, tier, unlock, arch, size, desc, cost, gen, out_kw, **kw):
    B(bid, name, "generator", tier, unlock, arch, size, desc, cost, power_out_kw=float(out_kw), generator=gen, **kw)


def ACC(bid, name, tier, unlock, size, desc, cost, capacity, rate, **kw):
    B(bid, name, "generator", tier, unlock, "accumulator", size, desc, cost, power_out_kw=float(rate),
      generator={"source": "accumulator"}, capacity_kj=float(capacity), **kw)


def DEF(bid, name, tier, unlock, arch, size, desc, cost, defense, ammo=None, per_min=0.0, power=0.0, **kw):
    B(bid, name, "defense", tier, unlock, arch, size, desc, cost, power=power, defense=float(defense), ammo=ammo,
      ammo_per_min=float(per_min), **kw)


def STORE(bid, name, tier, unlock, arch, size, desc, cost, slots, kind="solid", **kw):
    B(bid, name, "storage", tier, unlock, arch, size, desc, cost, storage_slots=slots, storage_kind=kind, **kw)


def LOG(bid, name, tier, unlock, arch, size, desc, cost, power, throughput=0, fluid=0, **kw):
    extra = {}
    if throughput:
        extra["throughput"] = float(throughput)
    if fluid:
        extra["fluid_throughput"] = float(fluid)
    B(bid, name, "logistics", tier, unlock, arch, size, desc, cost, power=power, **extra, **kw)


def SUP(bid, name, tier, unlock, arch, size, desc, cost, power, support=None, pollution=0.0, **kw):
    extra = {"support": support} if support else {}
    B(bid, name, "support", tier, unlock, arch, size, desc, cost, power=power, pollution=pollution, **extra, **kw)


def LAB(bid, name, tier, unlock, size, desc, cost, speed, power, slots=0, **kw):
    B(bid, name, "research", tier, unlock, "lab", size, desc, cost, speed=speed, power=power, slots=slots, **kw)


def define():
    # ------------------------------------------------------------------ extraction
    P("burner_drill", "Burner Drill", 0, None, "drill", (2, 2), "Coal-fired percussion drill for shallow ore.",
      {"iron_gear": 4, "iron_plate": 6, "stone_brick": 4}, ["mining"], 0.5, burner=True, fuel_kw=150, pollution=10,
      smoke=True, mat="cast_iron", variant="burner")
    P("electric_drill", "Electric Drill", 1, "electric_mining", "drill", (3, 3), "Motorized rotary drill for any solid deposit.",
      {"iron_gear": 8, "iron_plate": 10, "copper_wire": 12, "iron_rod": 6}, ["mining"], 1.0, 90, pollution=8)
    P("heavy_bore_drill", "Heavy Bore Drill", 3, "heavy_drilling", "drill", (4, 4), "Hydraulic-fed bore with a lubricated cutting head.",
      {"steel_frame": 4, "electric_motor": 6, "gearbox": 8, "hydraulic_ram": 4, "circuit_board": 6}, ["mining"], 2.0, 360,
      pollution=14, slots=2, variant="heavy")
    P("deep_core_drill", "Deep Core Drill", 5, "deep_core_drilling", "drill", (5, 5), "Carbide-bit drill reaching the deep seams.",
      {"tungsten_carbide": 10, "steel_frame": 6, "electric_motor": 8, "hydraulic_ram": 6, "embedded_controller": 2}, ["mining"],
      3.0, 1200, pollution=20, slots=3, variant="deep")
    P("plasma_bore", "Plasma Bore", 6, "plasma_boring", "drill", (6, 6), "Plasma-spalling borer that vaporizes host rock.",
      {"deep_core_drill": 1, "plasma_coil": 2, "tungsten_carbide": 20, "embedded_controller": 4}, ["mining"], 4.0, 3600,
      pollution=18, slots=4, variant="plasma")
    P("shore_intake", "Shore Intake", 0, None, "water_pump", (1, 2), "Gravity sluice and screen feeding water to the works.",
      {"iron_pipe": 6, "iron_gear": 3, "stone_brick": 4}, ["pumping"], 1.0, 0, variant="intake")
    P("pump_station", "Pump Station", 2, "hydraulics", "water_pump", (2, 2), "Electric pump lifting water or brine from wells.",
      {"pump_unit": 2, "iron_pipe": 10, "steel_plate": 6}, ["pumping"], 2.0, 60, slots=1)
    P("deep_well_pump", "Deep-Well Pump", 3, "chlor_alkali", "gas_well", (2, 3), "Submersible pump string for deep aquifers.",
      {"pump_unit": 3, "steel_plate": 12, "iron_pipe": 16, "circuit_board": 4}, ["pumping"], 3.0, 200, slots=2,
      variant="pump")
    P("pumpjack", "Pumpjack", 2, "oil_extraction", "pumpjack", (3, 3), "Nodding beam pump lifting crude from the reservoir.",
      {"steel_frame": 2, "pump_unit": 2, "gearbox": 4, "electric_motor": 2}, ["oil_extraction"], 1.0, 90, pollution=10,
      slots=1)
    P("wellhead_compressor", "Wellhead Compressor", 3, "gas_processing", "gas_well", (3, 3), "Compressed-lift wellhead for gas and light crude.",
      {"steel_frame": 4, "pump_unit": 4, "valve": 8, "circuit_board": 8}, ["oil_extraction"], 1.5, 250, pollution=8, slots=2)
    P("offshore_rig", "Offshore Rig", 5, "offshore_drilling", "pumpjack", (6, 6), "Jack-up platform drilling the shelf reservoirs.",
      {"steel_frame": 20, "pump_unit": 8, "tungsten_carbide": 6, "embedded_controller": 4, "concrete": 60}, ["oil_extraction"],
      3.0, 1500, pollution=15, slots=3, variant="offshore")

    # ------------------------------------------------------------------ smelting / casting
    P("stone_furnace", "Stone Furnace", 0, None, "burner_furnace", (2, 2), "Coal-fed fieldstone furnace for ore and bricks.",
      {"stone": 10}, ["smelting"], 1.0, burner=True, fuel_kw=90, pollution=2, smoke=True, mat="stone")
    P("blast_furnace", "Blast Furnace", 1, "blast_furnaces", "burner_furnace", (4, 4), "Hot-blast stack that doubles smelting throughput.",
      {"stone_brick": 30, "steel_plate": 10, "iron_pipe": 8}, ["smelting"], 2.0, burner=True, fuel_kw=300, pollution=6,
      smoke=True, mat="brick_clay", variant="blast")
    P("induction_furnace", "Induction Furnace", 3, "induction_furnaces", "electric_furnace", (3, 3), "Clean electric furnace with induction coils.",
      {"electromagnet": 12, "steel_plate": 12, "stone_brick": 20, "circuit_board": 6}, ["smelting"], 2.0, 180, pollution=1,
      slots=2)
    P("arc_furnace", "Electric Arc Furnace", 3, "arc_furnaces", "arc_furnace", (4, 4), "Graphite-electrode furnace for reductions and refractory work.",
      {"steel_frame": 4, "electromagnet": 10, "insulated_cable": 20, "concrete": 20, "control_board": 4},
      ["smelting", "smelting_advanced"], 2.0, 1000, pollution=5, slots=2)
    P("plasma_arc_furnace", "Plasma Arc Furnace", 6, "plasma_furnaces", "arc_furnace", (5, 5), "Plasma-torch furnace for any melt or reduction.",
      {"superconductor_tape": 10, "tungsten_carbide": 10, "steel_frame": 6, "embedded_controller": 4},
      ["smelting", "smelting_advanced"], 4.0, 4000, pollution=2, slots=4, variant="plasma")
    P("casting_foundry", "Casting Foundry", 3, "aerospace_alloys", "foundry", (5, 5), "Ladle-and-mold line for alloys and cast parts.",
      {"steel_frame": 6, "stone_brick": 40, "concrete": 30, "control_board": 6, "pump_unit": 2}, ["foundry"], 1.0, 800,
      pollution=6, slots=2, smoke=True)
    P("vacuum_foundry", "Vacuum Foundry", 6, "vacuum_casting", "foundry", (5, 5), "Vacuum induction casting for flawless alloys.",
      {"titanium_alloy": 20, "pump_unit": 8, "embedded_controller": 4, "superconductor_tape": 4}, ["foundry"], 2.5, 3000,
      pollution=2, slots=4, variant="vacuum")

    # ------------------------------------------------------------------ crushing / pressing
    P("jaw_crusher", "Jaw Crusher", 1, "quarrying", "crusher", (2, 2), "Toggle-jaw crusher for rock and clinker.",
      {"iron_plate": 12, "iron_gear": 12, "stone_brick": 6}, ["crushing"], 1.0, 75, pollution=5)
    P("cone_crusher", "Cone Crusher", 3, "cone_crushers", "crusher", (3, 3), "Gyratory cone crusher with fine product.",
      {"steel_frame": 3, "gearbox": 6, "electric_motor": 3, "bearing": 8}, ["crushing"], 2.0, 250, pollution=6, slots=2,
      variant="cone")
    P("ball_mill", "Ball Mill", 5, "ball_mills", "crusher", (4, 3), "Rotating drum mill grinding to powder.",
      {"steel_frame": 6, "gearbox": 10, "electric_motor": 6, "tungsten_carbide": 10}, ["crushing"], 3.5, 900, pollution=6,
      slots=3, variant="mill")
    P("scrap_recycler", "Scrap Recycler", 1, "scrap_reclamation", "crusher", (3, 2), "Shear-and-sort line returning scrap to the melt.",
      {"steel_plate": 12, "iron_gear": 10, "copper_wire": 10}, ["recycling"], 1.0, 90, pollution=4, variant="recycler")
    P("reclamation_plant", "Reclamation Plant", 4, "red_mud_recovery", "crusher", (4, 4), "Magnetic and flotation recovery of process residues.",
      {"steel_frame": 4, "electric_motor": 6, "filter_cartridge": 6, "control_board": 4}, ["recycling"], 2.5, 600,
      pollution=3, slots=2, variant="reclaimer")
    P("stamping_press", "Stamping Press", 1, "stamping_presses", "press", (2, 2), "Flywheel press for plate, rod and wire.",
      {"iron_plate": 15, "iron_gear": 8, "iron_rod": 6, "copper_wire": 6}, ["pressing"], 1.0, 100, pollution=3)
    P("wire_drawer", "Wire Drawing Bench", 2, "rolling_mills", "wire_drawer", (3, 2), "Multi-die drawing bench for rod and wire.",
      {"steel_plate": 8, "electric_motor": 2, "iron_gear": 10}, ["pressing"], 1.5, 120, pollution=2, slots=1)
    P("rolling_mill", "Rolling Mill", 2, "rolling_mills", "rolling_mill", (4, 2), "Four-high mill for plate, sheet and sections.",
      {"steel_frame": 3, "electric_motor": 4, "gearbox": 4, "bearing": 8}, ["pressing"], 2.0, 300, pollution=4, slots=1)
    P("hydraulic_forge_press", "Hydraulic Forge Press", 4, "hydraulic_presses", "press", (4, 4), "Multi-thousand-tonne press for any forming job.",
      {"hydraulic_ram": 8, "steel_frame": 6, "control_board": 4, "electric_motor": 4, "titanium_plate": 6}, ["pressing"], 3.0,
      1200, pollution=4, slots=3, variant="hydraulic")

    # ------------------------------------------------------------------ assembling / electronics
    P("fitting_bench", "Fitting Bench", 0, None, "assembler", (2, 2), "Powered workbench with vise, punch and drill press.",
      {"iron_plate": 8, "iron_gear": 6, "copper_wire": 6, "fasteners": 8}, ["assembling", "pressing"], 0.5, 40, pollution=2,
      variant="bench")
    P("assembly_station", "Assembly Station", 0, "assembly_stations", "assembler", (3, 3), "Jig-fed station for routine assemblies.",
      {"iron_gear": 10, "iron_plate": 12, "copper_wire": 10, "fasteners": 12}, ["assembling"], 0.75, 75, pollution=3)
    P("assembly_line", "Assembly Line", 2, "assembly_lines", "assembler", (3, 3), "Motorized line with powered fixtures.",
      {"steel_frame": 2, "electric_motor": 4, "circuit_board": 6, "gearbox": 2}, ["assembling"], 1.25, 150, pollution=2,
      slots=2)
    P("robotic_workcell", "Robotic Workcell", 4, "robotics", "assembler", (3, 3), "Robot-tended cell building anything that fits.",
      {"robotic_arm": 2, "steel_frame": 2, "embedded_controller": 2}, ["assembling"], 2.0, 450, pollution=1, slots=3,
      variant="robotic")
    P("autonomous_fabricator", "Autonomous Fabricator", 6, "autonomous_fabrication", "assembler", (4, 4), "Self-scheduling fabricator for general and precision work.",
      {"robotic_arm": 6, "quantum_processor": 1, "steel_frame": 6}, ["assembling", "precision_assembling"], 3.5, 1500,
      pollution=1, slots=4, variant="autonomous")
    P("clean_room_assembler", "Clean-Room Assembler", 4, "precision_engineering", "precision_assembler", (4, 4), "Filtered-air bay for tight-tolerance assembly.",
      {"steel_frame": 4, "microchip": 10, "filter_cartridge": 10, "electric_motor": 6, "aluminum_sheet": 10},
      ["precision_assembling"], 1.0, 500, pollution=1, slots=2)
    P("micro_precision_cell", "Micro-Precision Cell", 6, "micro_precision", "precision_assembler", (4, 4), "Vibration-isolated cell working at nanometer tolerance.",
      {"robotic_arm": 4, "optical_lens": 10, "embedded_controller": 4, "superconductor_tape": 4}, ["precision_assembling"],
      2.5, 1800, slots=4, variant="micro")
    P("circuit_fab", "Circuit Fab", 1, "circuit_theory", "electronics_fab", (3, 3), "Solder-reflow line for boards and components.",
      {"steel_frame": 2, "copper_wire": 20, "glass_pane": 6, "gearbox": 2}, ["electronics"], 1.0, 200, pollution=2, slots=1)
    P("surface_mount_line", "Surface-Mount Line", 3, "surface_mount", "electronics_fab", (4, 3), "Pick-and-place line for dense boards.",
      {"control_board": 4, "electric_motor": 6, "steel_frame": 4, "optical_sensor": 4}, ["electronics"], 2.0, 450,
      pollution=1, slots=2, variant="smt")
    P("lithography_fab", "Lithography Fab", 4, "microelectronics", "electronics_fab", (5, 5), "Photolithography cleanroom for dies and controllers.",
      {"control_board": 10, "glass_pane": 20, "steel_frame": 4, "electric_motor": 6, "aluminum_sheet": 20}, ["electronics"],
      3.0, 2000, pollution=1, slots=3, variant="litho")

    # ------------------------------------------------------------------ chemistry / refining / mixing
    P("chemical_reactor", "Chemical Reactor", 2, "polymer_chemistry", "chemical_plant", (3, 3), "Jacketed stirred reactor for liquid-phase chemistry.",
      {"steel_plate": 15, "iron_pipe": 10, "valve": 6, "circuit_board": 6, "glass_pane": 6}, ["chemistry"], 1.0, 210,
      pollution=4, slots=2)
    P("catalytic_reactor", "Catalytic Reactor", 4, "catalytic_reactors", "chemical_plant", (3, 3), "Fixed-bed catalytic reactor with titanium internals.",
      {"steel_plate": 20, "titanium_plate": 10, "valve": 8, "control_board": 6}, ["chemistry"], 2.0, 600, pollution=3,
      slots=3, variant="catalytic")
    P("flow_reactor", "Continuous-Flow Reactor", 6, "flow_chemistry", "chemical_plant", (4, 4), "Microchannel reactor with graphene heat exchange.",
      {"titanium_alloy": 20, "pump_unit": 6, "embedded_controller": 4, "graphene": 4}, ["chemistry"], 3.5, 1800, pollution=2,
      slots=4, variant="flow")
    P("distillation_column", "Distillation Column", 2, "oil_refining", "refinery", (5, 5), "Atmospheric column splitting crude into cuts.",
      {"steel_plate": 40, "iron_pipe": 30, "valve": 10, "circuit_board": 6, "concrete": 20}, ["refining"], 1.0, 420,
      pollution=6, slots=2, smoke=True)
    P("hydrocracker", "Hydrocracker", 4, "hydrocracking", "refinery", (5, 5), "High-pressure hydrogen cracking unit.",
      {"steel_frame": 6, "valve": 16, "pump_unit": 4, "control_board": 6, "titanium_plate": 10}, ["refining"], 2.0, 1000,
      pollution=5, slots=3, variant="cracker")
    P("fractionation_tower", "Fractionation Tower", 5, "fractionation", "refinery", (6, 6), "Tall vacuum fractionator with fine cuts.",
      {"steel_frame": 10, "valve": 30, "titanium_plate": 20, "embedded_controller": 2}, ["refining"], 3.0, 2500,
      pollution=4, slots=3, variant="tower")
    P("batch_mixer", "Batch Mixer", 1, "cement_works", "mixer", (2, 2), "Drum mixer for concrete and powders.",
      {"iron_plate": 10, "iron_gear": 6, "iron_pipe": 6, "copper_wire": 6}, ["mixing"], 1.0, 60, pollution=2)
    P("industrial_blender", "Industrial Blender", 3, "industrial_mixers", "mixer", (3, 3), "Twin-shaft blender with metered dosing.",
      {"steel_plate": 15, "electric_motor": 4, "gearbox": 4, "plastic_sheet": 6}, ["mixing"], 2.0, 220, pollution=2,
      slots=2, variant="blender")
    P("electrolytic_cell", "Electrolytic Cell", 3, "chlor_alkali", "electrolyzer", (4, 3), "Diaphragm cell bank for electrowinning.",
      {"steel_plate": 20, "copper_sheet": 30, "plastic_sheet": 10, "circuit_board": 6}, ["electrolysis"], 1.0, 1000,
      pollution=2, slots=2)
    P("membrane_electrolyzer", "Membrane Electrolyzer", 5, "membrane_electrolysis", "electrolyzer", (4, 4), "Ion-membrane stack with titanium electrodes.",
      {"titanium_plate": 30, "plastic_sheet": 20, "embedded_controller": 2, "copper_sheet": 40}, ["electrolysis"], 2.5,
      3000, pollution=1, slots=3, variant="membrane")
    P("centrifuge_cascade", "Centrifuge Cascade", 5, "isotope_centrifuges", "centrifuge", (3, 3), "Carbon-rotor centrifuges in series.",
      {"electric_motor": 10, "bearing": 20, "composite_panel": 6, "embedded_controller": 2, "steel_frame": 2},
      ["centrifuging"], 1.0, 600, slots=2)
    P("isotope_separator", "Isotope Separator", 6, "isotope_separators", "centrifuge", (4, 4), "Magnetic-levitation rotor bank.",
      {"centrifuge_cascade": 2, "superconductor_tape": 10, "embedded_controller": 4}, ["centrifuging"], 2.5, 2200, slots=4,
      variant="maglev")
    P("air_separation_unit", "Air Separation Unit", 4, "air_separation", "cryo_plant", (4, 4), "Cold box that fractionates liquefied air.",
      {"steel_plate": 30, "pump_unit": 4, "valve": 10, "control_board": 6, "aluminum_sheet": 20}, ["cryogenics"], 1.0, 800,
      slots=2)
    P("cryo_liquefier", "Cryogenic Liquefier", 5, "cryogenic_liquefaction", "cryo_plant", (4, 4), "Turbo-expander liquefaction train.",
      {"pump_unit": 6, "aluminum_sheet": 30, "embedded_controller": 2, "heat_sink": 10}, ["cryogenics"], 2.0, 1800, slots=3,
      variant="liquefier")
    P("dilution_refrigerator", "Dilution Refrigerator", 6, "dilution_refrigeration", "cryo_plant", (4, 4), "Helium-mixture refrigerator reaching millikelvin.",
      {"cryocooler": 4, "titanium_alloy": 10, "superconductor_tape": 4}, ["cryogenics"], 3.5, 3000, slots=4,
      variant="dilution")
    P("algae_bioreactor", "Algae Bioreactor", 3, "algae_cultivation", "bioreactor", (4, 4), "Sunlit tube photobioreactor that also eats smog.",
      {"glass_pane": 30, "plastic_sheet": 10, "pump_unit": 2, "steel_frame": 2}, ["bioprocessing"], 1.0, 150, pollution=-3,
      slots=2)
    P("fermentation_vat", "Fermentation Vat", 5, "fermentation", "bioreactor", (4, 4), "Sterile titanium vat for engineered cultures.",
      {"titanium_plate": 10, "glass_pane": 30, "pump_unit": 4, "embedded_controller": 1}, ["bioprocessing"], 2.0, 500,
      pollution=-5, slots=3, variant="vat")
    P("nanofabricator", "Nanofabricator", 5, "superconductors", "nanofab", (4, 4), "Deposition chamber assembling films atom by atom.",
      {"composite_panel": 10, "embedded_controller": 6, "robotic_arm": 2, "filter_cartridge": 20, "titanium_alloy": 10},
      ["nanofab"], 1.0, 2500, slots=2)
    P("molecular_assembler", "Molecular Assembler", 6, "molecular_assembly", "nanofab", (4, 4), "Directed self-assembly reactor.",
      {"nanofabricator": 1, "metamaterial_lattice": 4, "quantum_processor": 1}, ["nanofab"], 2.5, 6000, slots=4,
      variant="molecular")
    P("orbital_gantry", "Orbital Assembly Gantry", 6, "orbital_assembly", "orbital_assembler", (6, 6), "Towering gantry that stacks launch vehicles and Ark modules.",
      {"steel_frame": 60, "robotic_arm": 12, "quantum_processor": 2, "concrete": 400}, ["orbital"], 1.0, 10000, slots=2)
    P("heavy_orbital_gantry", "Heavy Orbital Gantry", 7, "zero_g_assembly", "orbital_assembler", (6, 6), "Twin-crane gantry with lattice cradles.",
      {"orbital_gantry": 1, "metamaterial_lattice": 10, "quantum_processor": 4, "robotic_arm": 12}, ["orbital"], 2.0, 20000,
      slots=4, variant="heavy")
    P("munitions_works", "Munitions Works", 1, "munitions", "munitions_plant", (3, 3), "Press-and-fill line for rounds and shells.",
      {"steel_plate": 10, "iron_gear": 10, "copper_wire": 10, "iron_pipe": 4}, ["munitions"], 1.0, 80, pollution=5)
    P("automated_arsenal", "Automated Arsenal", 4, "automated_arsenals", "munitions_plant", (4, 4), "Robotic ordnance line with blast cells.",
      {"robotic_arm": 2, "steel_frame": 4, "embedded_controller": 2, "concrete": 30}, ["munitions"], 2.5, 600, pollution=3,
      slots=3, variant="arsenal")

    # ------------------------------------------------------------------ boiling / nuclear / fusion
    P("burner_boiler", "Burner Boiler", 0, None, "boiler", (3, 2), "Fire-tube boiler: 40 steam/s, enough for two engines.",
      {"stone_brick": 10, "iron_pipe": 6, "iron_plate": 4}, ["boiling"], 1.0, burner=True, fuel_kw=2400, pollution=30,
      smoke=True, group="power")
    P("high_pressure_boiler", "High-Pressure Boiler", 2, "high_pressure_steam", "boiler", (4, 3), "Water-tube boiler: 100 steam/s for five engines.",
      {"steel_plate": 20, "iron_pipe": 12, "valve": 6, "stone_brick": 20}, ["boiling"], 2.5, burner=True, fuel_kw=6000,
      pollution=55, smoke=True, group="power", variant="water_tube")
    P("fired_superheater", "Fired Superheater", 4, "steam_turbines", "heat_exchanger", (3, 3), "Radiant superheater lifting steam to turbine grade.",
      {"steel_plate": 30, "iron_pipe": 30, "valve": 10, "stone_brick": 30, "titanium_plate": 6}, ["boiling"], 1.0,
      burner=True, fuel_kw=2400, pollution=20, smoke=True, group="power")
    P("thorium_reactor", "Thorium Reactor", 5, "thorium_reactors", "reactor", (5, 5), "Pressurized thorium reactor: 160 superheated steam/s.",
      {"concrete": 200, "steel_frame": 10, "titanium_plate": 30, "embedded_controller": 4, "pump_unit": 6}, ["fission"], 1.0,
      400, group="power")
    P("breeder_reactor", "Breeder Reactor", 6, "breeder_reactors", "reactor", (5, 5), "Fast-spectrum reactor that breeds fissile seed.",
      {"thorium_reactor": 1, "tungsten_carbide": 20, "titanium_alloy": 20, "embedded_controller": 6}, ["fission"], 2.0, 900,
      group="power", variant="breeder")
    P("tokamak", "Tokamak Fusion Reactor", 6, "fusion_power", "fusion_reactor", (6, 6), "Superconducting tokamak: 600 superheated steam/s.",
      {"plasma_coil": 12, "cryocooler": 6, "titanium_alloy": 40, "quantum_processor": 1, "concrete": 300}, ["fusion"], 1.0,
      6000, group="power")

    # ------------------------------------------------------------------ research
    LAB("drafting_office", "Drafting Office", 0, None, (3, 3), "Drawing tables and test rigs that study Blueprint Sheets.",
        {"copper_wire": 12, "iron_gear": 6, "iron_plate": 8, "stone_brick": 6}, 1.0, 60)
    LAB("research_laboratory", "Research Laboratory", 2, "research_laboratories", (3, 3), "Instrumented lab with fume hoods and benches.",
        {"circuit_board": 10, "glass_pane": 10, "steel_frame": 2, "electric_motor": 2}, 2.0, 250, slots=2)
    LAB("materials_test_lab", "Materials Test Lab", 4, "materials_labs", (4, 4), "Load frames, spectrometers and climate chambers.",
        {"steel_frame": 4, "control_board": 10, "optical_sensor": 6, "glass_pane": 20, "titanium_plate": 10}, 3.0, 800, slots=3)
    LAB("quantum_research_center", "Quantum Research Center", 6, "quantum_research", (5, 5), "Cryogenic computing hall that simulates experiments.",
        {"quantum_processor": 2, "cryocooler": 4, "steel_frame": 6, "fiber_optic_cable": 40}, 4.0, 3000, slots=4)

    # ------------------------------------------------------------------ generators
    GEN("steam_engine", "Steam Engine", 0, None, "steam_engine", (3, 3), "Piston engine: 20 steam/s for 900 kW.",
        {"iron_gear": 10, "iron_pipe": 8, "iron_plate": 12, "fasteners": 10}, {"fluid": "steam", "rate": 20}, 900,
        pollution=0)
    GEN("producer_gas_generator", "Producer-Gas Generator", 1, "gasifier_power", "gas_turbine", (3, 2), "Gasifier engine burning solid fuel directly at 60%.",
        {"steel_plate": 12, "iron_pipe": 10, "gearbox": 2, "copper_wire": 20}, {"fuel_class": "chemical", "fuel_kw": 800}, 480,
        pollution=12, smoke=True, variant="gasifier")
    GEN("solar_array", "Solar Array", 2, "photovoltaics", "solar_array", (3, 3), "Tilted cell panels: 90 kW at noon, nothing at night.",
        {"pv_cell": 12, "steel_frame": 2, "copper_wire": 10}, {"source": "solar"}, 90)
    GEN("thin_film_solar_field", "Thin-Film Solar Field", 4, "thin_film_solar", "solar_array", (5, 5), "Silicon thin-film field: 400 kW peak.",
        {"silicon_wafer": 20, "glass_pane": 20, "aluminum_sheet": 10, "steel_frame": 2}, {"source": "solar"}, 400,
        variant="thin_film")
    GEN("wind_turbine", "Wind Turbine", 2, "wind_power", "wind_turbine", (2, 2), "Three-blade turbine averaging 300 kW.",
        {"steel_beam": 6, "electromagnet": 8, "gearbox": 2, "bearing": 4}, {"source": "wind"}, 300)
    GEN("heavy_wind_turbine", "Heavy Wind Turbine", 5, "heavy_wind_turbines", "wind_turbine", (3, 3), "Direct-drive magnet turbine averaging 1.8 MW.",
        {"composite_panel": 20, "rare_earth_magnet": 20, "bearing": 12, "steel_frame": 6}, {"source": "wind"}, 1800,
        variant="heavy")
    GEN("gas_turbine", "Gas Turbine", 3, "gas_turbines", "gas_turbine", (4, 2), "Open-cycle turbine: 10 fuel gas/s for 3 MW.",
        {"steel_frame": 4, "gearbox": 6, "bearing": 10, "electric_motor": 2, "circuit_board": 8},
        {"fluid": "fuel_gas", "rate": 10}, 3000, pollution=15)
    GEN("combined_cycle_turbine", "Combined-Cycle Turbine", 5, "combined_cycle", "gas_turbine", (5, 3), "Gas turbine with heat-recovery steam stage: 20 gas/s for 9 MW.",
        {"turbine_blade": 40, "steel_frame": 6, "embedded_controller": 2, "titanium_alloy": 8},
        {"fluid": "fuel_gas", "rate": 20}, 9000, pollution=18, variant="combined")
    GEN("steam_turbine", "Steam Turbine", 4, "steam_turbines", "steam_turbine", (5, 3), "Multi-stage turbine: 40 superheated steam/s for 4 MW.",
        {"turbine_blade": 20, "steel_frame": 6, "bearing": 12, "copper_wire": 40, "control_board": 4},
        {"fluid": "superheated_steam", "rate": 40}, 4000)
    GEN("geothermal_plant", "Geothermal Plant", 5, "geothermal_power", "geothermal_plant", (5, 5), "Deep-well flash plant: steady 6 MW.",
        {"turbine_blade": 30, "tungsten_carbide": 10, "steel_frame": 8, "pump_unit": 6, "concrete": 80},
        {"source": "geothermal"}, 6000, pollution=2)
    GEN("tidal_generator", "Tidal Barrage Turbine", 4, "tidal_power", "water_pump", (4, 3), "Bulb turbine in a sea wall averaging 1.5 MW.",
        {"turbine_blade": 10, "concrete": 60, "electromagnet": 20, "steel_frame": 4}, {"source": "tidal"}, 1500,
        variant="tidal")
    ACC("flywheel_store", "Flywheel Store", 2, "flywheel_storage", (2, 2), "Steel rotor in vacuum: 20 MJ at up to 300 kW.",
        {"steel_ingot": 20, "bearing": 8, "electric_motor": 2, "concrete": 10}, 20000, 300, variant="flywheel")
    ACC("battery_bank", "Battery Bank", 3, "sodium_sulfur_batteries", (3, 2), "Sodium-sulfur racks: 100 MJ at up to 1 MW.",
        {"battery_cell": 20, "steel_frame": 2, "circuit_board": 6, "copper_wire": 20}, 100000, 1000)
    ACC("lithium_storage_array", "Lithium Storage Array", 5, "grid_lithium_storage", (4, 3), "Containerized lithium racks: 800 MJ at 5 MW.",
        {"lithium_cell": 40, "steel_frame": 4, "embedded_controller": 2, "heat_sink": 10}, 800000, 5000, variant="lithium")
    ACC("smes_ring", "Superconducting Storage Ring", 6, "smes", (5, 5), "Magnetic energy ring: 5 GJ at 25 MW.",
        {"superconductor_tape": 60, "cryocooler": 4, "concrete": 100, "steel_frame": 6}, 5000000, 25000, variant="smes")

    # ------------------------------------------------------------------ support
    SUP("substation", "Substation", 2, "power_distribution", "substation", (2, 2), "Transformer yard that cuts line losses in its bay.",
        {"steel_beam": 4, "copper_wire": 30, "electromagnet": 4, "ceramic_substrate": 6}, 0,
        {"energy_bonus": -0.1, "range": "bay"}, group="power")
    SUP("cooling_tower", "Cooling Tower", 5, "thorium_reactors", "cooling_tower", (4, 4), "Hyperbolic tower: +10% output for generators in its bay.",
        {"concrete": 150, "steel_beam": 20, "pump_unit": 4}, 50, {"power_bonus": 0.1, "range": "bay"}, group="power")
    SUP("signal_relay", "Signal Relay", 3, "signal_relays", "beacon", (2, 2), "Timing relay that speeds up machines in its bay.",
        {"control_board": 4, "insulated_cable": 10, "steel_frame": 1, "optical_sensor": 2}, 300,
        {"speed_bonus": 0.1, "range": "bay"})
    SUP("overclock_relay", "Overclock Relay", 5, "overclock_relays", "beacon", (2, 2), "Fiber-linked relay with a stronger bay-wide boost.",
        {"embedded_controller": 4, "fiber_optic_cable": 20, "heat_sink": 10, "steel_frame": 2}, 900,
        {"speed_bonus": 0.2, "range": "bay"}, variant="overclock")
    SUP("quantum_sync_relay", "Quantum Sync Relay", 6, "quantum_sync", "beacon", (2, 2), "Quantum-clocked relay synchronizing a whole bay.",
        {"quantum_processor": 1, "fiber_optic_cable": 30, "superconductor_tape": 6}, 2400,
        {"speed_bonus": 0.35, "range": "bay"}, variant="quantum")
    SUP("pollution_scrubber", "Pollution Scrubber", 2, "air_scrubbing", "scrubber", (2, 2), "Wet scrubber that removes 20 pollution/min.",
        {"steel_plate": 10, "electric_motor": 2, "iron_pipe": 10, "coke": 20}, 80, pollution=-20)
    SUP("electrostatic_precipitator", "Electrostatic Precipitator", 3, "precipitators", "scrubber", (3, 3), "Charged-plate precipitator removing 60 pollution/min.",
        {"steel_plate": 20, "insulated_cable": 10, "filter_cartridge": 6, "electric_motor": 2}, 250, pollution=-60,
        variant="precipitator")
    SUP("catalytic_scrubber", "Catalytic Scrubber", 5, "catalytic_scrubbers", "scrubber", (3, 3), "Rare-earth catalyst bed removing 180 pollution/min.",
        {"rare_earth_oxide": 20, "steel_plate": 30, "electric_motor": 4, "embedded_controller": 1}, 700, pollution=-180,
        variant="catalytic")
    SUP("carbon_capture_tower", "Carbon Capture Tower", 6, "carbon_capture", "scrubber", (4, 4), "Nanotube sorbent tower removing 500 pollution/min.",
        {"carbon_nanotube": 20, "steel_frame": 10, "pump_unit": 6, "filter_cartridge": 20}, 2000, pollution=-500,
        variant="tower")

    # ------------------------------------------------------------------ storage
    STORE("supply_crate", "Supply Crate", 0, None, "warehouse", (1, 1), "Bolted crate: +100 per item type.",
          {"iron_plate": 10, "fasteners": 6}, 100, variant="crate", mat="iron")
    STORE("storage_shed", "Storage Shed", 0, "storage_sheds", "warehouse", (3, 3), "Racked shed: +400 per item type.",
          {"iron_plate": 20, "iron_rod": 10, "stone_brick": 20}, 400, variant="shed")
    STORE("fluid_tank", "Fluid Tank", 1, "fluid_storage", "storage_tank", (3, 3), "Riveted tank: +2,500 per fluid.",
          {"steel_plate": 12, "iron_pipe": 6, "valve": 2}, 2500, kind="fluid")
    STORE("warehouse", "Warehouse", 2, "warehousing", "warehouse", (5, 4), "Steel-framed warehouse: +1,500 per item type.",
          {"steel_beam": 20, "concrete": 40, "steel_plate": 20}, 1500)
    STORE("bulk_silo", "Bulk Silo", 2, "warehousing", "silo", (3, 3), "Tall silo for loose solids: +3,000 per item type.",
          {"steel_plate": 40, "concrete": 20, "electric_motor": 2}, 3000)
    STORE("automated_warehouse", "Automated Warehouse", 4, "automated_storage", "warehouse", (6, 5), "Robot-picked high bay: +8,000 per item type.",
          {"steel_beam": 40, "concrete": 80, "robotic_arm": 4, "embedded_controller": 2}, 8000, variant="automated")
    STORE("pressurized_tank_farm", "Pressurized Tank Farm", 4, "pressurized_tanks", "storage_tank", (5, 5), "Sphere tanks: +25,000 per fluid.",
          {"steel_plate": 80, "titanium_plate": 10, "valve": 12, "concrete": 40}, 25000, kind="fluid", variant="sphere")
    STORE("cryogenic_tank", "Cryogenic Tank", 5, "cryogenic_storage", "storage_tank", (4, 4), "Vacuum-jacketed dewar: +80,000 per fluid.",
          {"aluminum_sheet": 60, "composite_panel": 10, "valve": 10, "concrete": 40}, 80000, kind="fluid", variant="cryo")
    STORE("vault_complex", "Vault Complex", 6, "vault_complexes", "warehouse", (6, 6), "Underground vaults: +40,000 per item type.",
          {"concrete": 400, "steel_beam": 80, "robotic_arm": 6, "nano_coating": 10}, 40000, variant="vault")

    # ------------------------------------------------------------------ logistics (global throughput, items/s)
    LOG("conveyor_hub", "Conveyor Hub", 1, "conveyor_hubs", "conveyor_hub", (3, 3), "Roller-conveyor junction: +10 items/s.",
        {"iron_gear": 10, "iron_plate": 10, "copper_wire": 8, "fasteners": 10}, 30, throughput=10)
    LOG("sorting_hub", "Sorting Hub", 2, "sorting_hubs", "conveyor_hub", (3, 3), "Sensor-gated diverter hub: +30 items/s.",
        {"conveyor_hub": 2, "electric_motor": 4, "optical_sensor": 4}, 90, throughput=30, variant="sorting")
    LOG("pneumatic_hub", "Pneumatic Tube Hub", 3, "pneumatic_tubes", "conveyor_hub", (3, 3), "Capsule tube exchange: +80 items/s.",
        {"sorting_hub": 2, "pump_unit": 2, "plastic_sheet": 10, "circuit_board": 6}, 200, throughput=80, variant="pneumatic")
    LOG("pipeline_station", "Pipeline Pumping Station", 3, "pipelines", "water_pump", (3, 2), "Booster station: +2,000 fluid/s.",
        {"pump_unit": 4, "steel_plate": 20, "valve": 10, "circuit_board": 6}, 250, fluid=2000, variant="booster")
    LOG("rail_depot", "Rail Depot", 3, "rail_logistics", "rail_depot", (6, 4), "Freight sidings and gantry crane: +250 items/s.",
        {"steel_beam": 40, "concrete": 60, "electric_motor": 6, "control_board": 4}, 300, throughput=250)
    LOG("drone_port", "Drone Port", 4, "drone_logistics", "drone_port", (3, 3), "Charging pads and a cargo-drone flight: +400 items/s.",
        {"cargo_drone": 6, "steel_frame": 4, "embedded_controller": 2, "concrete": 30}, 600, throughput=400)
    LOG("freight_yard", "Freight Yard", 4, "freight_yards", "rail_depot", (6, 6), "Hump yard with automated couplers: +800 items/s.",
        {"rail_depot": 2, "steel_beam": 40, "control_board": 10, "concrete": 80}, 800, throughput=800, variant="yard")
    LOG("heavy_drone_port", "Heavy Drone Port", 5, "heavy_drones", "drone_port", (4, 4), "Heavy-lift drone wing: +1,500 items/s.",
        {"cargo_drone": 10, "brushless_motor": 10, "steel_frame": 6, "embedded_controller": 4}, 1500, throughput=1500,
        variant="heavy")
    LOG("maglev_terminal", "Maglev Freight Terminal", 6, "maglev_freight", "rail_depot", (6, 5), "Superconducting freight line: +5,000 items/s.",
        {"superconductor_tape": 40, "rare_earth_magnet": 40, "concrete": 200, "embedded_controller": 6}, 4000,
        throughput=5000, fluid=20000, variant="maglev")

    # ------------------------------------------------------------------ defense
    DEF("palisade_wall", "Palisade Wall", 1, "fortifications", "wall_segment", (2, 1), "Rod-and-brick barricade (+4 defense).",
        {"iron_rod": 8, "stone_brick": 10}, 4, mat="iron")
    DEF("concrete_barrier", "Concrete Barrier", 1, "concrete_barriers", "wall_segment", (2, 1), "Precast barrier block (+10 defense).",
        {"concrete": 12, "iron_rod": 6}, 10, mat="concrete", variant="concrete")
    DEF("sentry_gun", "Sentry Gun", 1, "munitions", "turret", (2, 2), "Spring-fed autogun firing ballistic rounds.",
        {"steel_plate": 8, "iron_gear": 6, "coil_spring": 4, "copper_wire": 6}, 15, "ballistic", 6)
    DEF("radar_station", "Radar Station", 2, "radar", "radar", (3, 3), "Rotating radar giving early warning (+8 defense).",
        {"steel_frame": 3, "circuit_board": 10, "electric_motor": 2, "copper_wire": 20}, 8, power=150)
    DEF("heavy_autocannon", "Heavy Autocannon", 3, "heavy_autocannons", "turret", (3, 3), "Belt-fed twin cannon on a powered mount.",
        {"steel_frame": 3, "electric_motor": 4, "gearbox": 4, "optical_sensor": 4}, 45, "ballistic", 10, power=30,
        variant="autocannon")
    DEF("mortar_battery", "Mortar Battery", 3, "blasting_compounds", "turret", (3, 3), "Indirect-fire tubes for massed swarms.",
        {"steel_plate": 20, "gearbox": 4, "optical_sensor": 2, "concrete": 10}, 70, "explosive", 4, variant="mortar")
    DEF("flame_projector", "Flame Projector", 3, "incendiaries", "turret", (2, 2), "Pressurized projector spraying burning gel.",
        {"steel_plate": 12, "pump_unit": 2, "valve": 4, "rubber": 6}, 40, "incendiary", 6, power=20, variant="flame")
    DEF("armored_bulwark", "Armored Bulwark", 4, "armored_bulwarks", "wall_segment", (2, 1), "Titanium-faced wall (+40 defense).",
        {"titanium_plate": 6, "concrete": 20, "steel_beam": 4}, 40, mat="titanium", variant="armored")
    DEF("pulse_laser_turret", "Pulse Laser Turret", 4, "laser_weapons", "turret", (2, 2), "Capacitor-fed laser that never jams.",
        {"optical_lens": 4, "capacitor": 20, "heat_sink": 6, "steel_frame": 2, "embedded_controller": 1}, 90, "energy", 3,
        power=600, variant="laser", glow=(0.9, 0.2, 0.2))
    DEF("howitzer_emplacement", "Howitzer Emplacement", 5, "guided_munitions", "turret", (4, 4), "Long-range gun with a computed fire solution.",
        {"steel_frame": 6, "gearbox": 10, "hydraulic_ram": 6, "flight_computer": 1}, 260, "explosive", 3, power=100,
        variant="howitzer")
    DEF("thermal_lance", "Thermal Lance Tower", 5, "pyrophorics", "turret", (3, 3), "Focused pyrophoric jet that melts armor.",
        {"titanium_plate": 10, "pump_unit": 4, "optical_lens": 4, "embedded_controller": 1}, 180, "incendiary", 4, power=400,
        variant="lance")
    DEF("shield_projector", "Shield Projector", 5, "shield_projectors", "shield_generator", (4, 4), "Magnetic deflector dome (+200 defense).",
        {"rare_earth_magnet": 20, "lithium_cell": 20, "embedded_controller": 4, "steel_frame": 4}, 200, power=2500)
    DEF("radar_array", "Early-Warning Radar Array", 5, "early_warning", "radar", (4, 4), "Phased-array radar fusing frontier tracks (+40 defense).",
        {"antenna_array": 4, "steel_frame": 4, "embedded_controller": 2}, 40, power=1000, variant="phased")
    DEF("railgun_battery", "Railgun Battery", 6, "railguns", "turret", (4, 4), "Supercapacitor rail launcher of hypersonic slugs.",
        {"superconductor_tape": 20, "graphene": 6, "steel_frame": 8, "embedded_controller": 4}, 600, "energy", 2, power=8000,
        variant="railgun", glow=(0.4, 0.8, 1.0))
    DEF("interceptor_drone_nest", "Interceptor Drone Nest", 6, "interceptor_drones", "drone_port", (4, 4), "Armed drone wing that hunts raiders.",
        {"cargo_drone": 8, "brushless_motor": 8, "flight_computer": 2, "steel_frame": 4}, 400, "ballistic", 8, power=1500,
        variant="interceptor")
    DEF("aegis_field_array", "Aegis Field Array", 6, "aegis_fields", "shield_generator", (5, 5), "Plasma-backed field dome (+900 defense).",
        {"plasma_coil": 4, "superconductor_tape": 20, "quantum_processor": 1, "lithium_cell": 40}, 900, power=12000,
        variant="aegis")

    # ------------------------------------------------------------------ megaproject
    B("launch_complex", "Launch Complex", "megaproject", 5, "launch_complex", "launch_pad", (6, 6),
      "Pad, tower and flame trench where megaproject stages are delivered.",
      {"concrete": 500, "steel_frame": 40, "heat_shield_tile": 40, "embedded_controller": 10, "pump_unit": 10}, power=2000)
