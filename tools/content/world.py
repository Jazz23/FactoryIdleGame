"""World data: deposits, frontier sectors, threats, contracts, achievements, megaprojects, start block."""
from common import C, V, eff, sig3

DEPOSITS = [
    # id (== item id), name, archetype, material, colour
    ("iron_ore", "Iron Ore Seam", "ore_chunks", "iron_ore", None),
    ("copper_ore", "Copper Ore Vein", "ore_chunks", "copper_ore", None),
    ("coal", "Coal Seam", "ore_chunks", "coal", None),
    ("stone", "Rubble Field", "gravel_pile", "stone", None),
    ("water", "Freshwater Inlet", "fluid_orb", "glass", (0.25, 0.45, 0.75)),
    ("limestone", "Limestone Face", "ore_chunks", "limestone", None),
    ("quartz_sand", "Quartz Sandbar", "powder_pile", "sand", None),
    ("cassiterite", "Cassiterite Placer", "gravel_pile", "stone", (0.22, 0.18, 0.15)),
    ("native_sulfur", "Sulfur Fumarole", "crystal_cluster", "sulfur", None),
    ("crude_oil", "Crude Oil Reservoir", "fluid_orb", "glass", (0.08, 0.07, 0.06)),
    ("natural_gas", "Gas Pocket", "gas_canister", "paint", (0.9, 0.75, 0.2)),
    ("brine", "Brine Aquifer", "fluid_orb", "glass", (0.55, 0.7, 0.72)),
    ("bauxite", "Bauxite Laterite", "ore_chunks", "bauxite", None),
    ("ilmenite", "Ilmenite Black Sand", "gravel_pile", "ilmenite", None),
    ("monazite_sand", "Monazite Beach", "powder_pile", "monazite", None),
    ("wolframite", "Wolframite Lode", "crystal_cluster", "graphite", (0.18, 0.18, 0.2)),
    ("rare_earth_ore", "Carbonatite Pipe", "ore_chunks", "stone", (0.62, 0.42, 0.4)),
    ("helium_gas", "Helium Reservoir", "gas_canister", "paint", (0.85, 0.5, 0.75)),
]

# id, name, tier, desc, claim cost, defense required, base threat, deposits {id: slots}, hazards
SECTORS = [
    ("rustfield_lot", "Rustfield Lot", 0, "The abandoned works where it all starts.", {}, 0, 0,
     {"iron_ore": 3, "copper_ore": 2, "coal": 3, "stone": 2, "water": 2}, ["scrap_swarm"]),
    ("slag_hills", "Slag Hills", 0, "Old spoil heaps over limestone and quartz.", {"iron_plate": 60, "iron_gear": 30, "stone_brick": 40}, 0, 0,
     {"iron_ore": 2, "coal": 2, "limestone": 2, "quartz_sand": 2, "water": 1}, ["scrap_swarm", "dust_storm"]),
    ("copper_gulch", "Copper Gulch", 1, "A dry ravine streaked green with copper.", {"steel_plate": 40, "iron_pipe": 30, "glass_pane": 20}, 5, 3,
     {"copper_ore": 4, "stone": 2, "coal": 1, "water": 2}, ["dust_storm", "rogue_salvager"]),
    ("tinmouth_delta", "Tinmouth Delta", 1, "Braided river channels heavy with tin gravel.", {"concrete": 50, "steel_beam": 20, "gearbox": 10}, 10, 6,
     {"cassiterite": 3, "quartz_sand": 2, "water": 3}, ["rogue_salvager", "scrap_swarm"]),
    ("limestone_terraces", "Limestone Terraces", 2, "Stepped quarry benches above the delta.", {"circuit_board": 40, "electric_motor": 10, "concrete": 100}, 20, 12,
     {"limestone": 3, "stone": 3, "cassiterite": 2, "coal": 2}, ["dust_storm", "rust_crawlers"]),
    ("blackwater_fields", "Blackwater Fields", 2, "Seeping crude and sulfur crusts on a dead marsh.", {"electric_motor": 20, "steel_frame": 10, "pump_unit": 6}, 30, 20,
     {"crude_oil": 3, "native_sulfur": 2, "water": 2}, ["rust_crawlers", "acid_rain"]),
    ("cinder_basin", "Cinder Basin", 2, "A coal-black basin of slag and fresh ore.", {"steel_frame": 20, "circuit_board": 60, "glass_pane": 50}, 40, 30,
     {"coal": 4, "iron_ore": 3, "copper_ore": 3}, ["rust_crawlers", "rogue_salvager"]),
    ("salt_flats", "Salt Flats", 3, "Blinding white pans over a brine aquifer.", {"plastic_sheet": 100, "insulated_cable": 60, "pump_unit": 10}, 60, 45,
     {"brine": 4, "limestone": 2, "quartz_sand": 2}, ["dust_storm", "feral_harvester"]),
    ("sulfur_vents", "Sulfur Vents", 3, "Steaming fumaroles over sour gas.", {"rubber": 100, "steel_frame": 30, "plastic_sheet": 100}, 80, 60,
     {"native_sulfur": 4, "natural_gas": 3}, ["acid_rain", "feral_harvester"]),
    ("red_mesa", "Red Mesa", 3, "Rust-red tableland of bauxite laterite.", {"control_board": 30, "battery_cell": 20, "concrete": 200}, 100, 80,
     {"bauxite": 4, "iron_ore": 3, "water": 2}, ["dust_storm", "feral_harvester"]),
    ("black_sand_coast", "Black Sand Coast", 3, "Storm beaches dark with ilmenite.", {"aluminum_sheet": 60, "control_board": 40, "hydraulic_ram": 20}, 130, 100,
     {"ilmenite": 4, "quartz_sand": 3, "brine": 2}, ["acid_rain", "magnetic_storm"]),
    ("dry_gas_field", "Dry Gas Field", 4, "Flat scrubland over a sweet gas dome.", {"titanium_plate": 40, "duralumin_ingot": 40, "control_board": 60}, 180, 140,
     {"natural_gas": 5, "crude_oil": 3}, ["scavenger_convoy", "magnetic_storm"]),
    ("quartz_dunes", "Quartz Dunes", 4, "Wind-sorted dunes of pure silica.", {"microchip": 100, "titanium_alloy": 30, "steel_frame": 60}, 240, 190,
     {"quartz_sand": 5, "limestone": 3, "bauxite": 2}, ["dust_storm", "scavenger_convoy"]),
    ("monazite_strand", "Monazite Strand", 4, "A faintly warm beach of heavy mineral sand.", {"embedded_controller": 40, "titanium_alloy": 40, "concrete": 400}, 320, 250,
     {"monazite_sand": 4, "ilmenite": 2, "brine": 2}, ["scavenger_convoy", "toxic_fog"]),
    ("wolfram_ridge", "Wolfram Ridge", 5, "A knife-edged ridge of tungsten lodes.", {"embedded_controller": 60, "lithium_cell": 60, "servo_motor": 40}, 400, 320,
     {"wolframite": 4, "copper_ore": 3, "cassiterite": 2}, ["siege_walker", "magnetic_storm"]),
    ("helium_steppe", "Helium Steppe", 5, "Endless grass over radiogenic gas traps.", {"flight_computer": 20, "airframe_panel": 30, "rare_earth_magnet": 60}, 520, 420,
     {"helium_gas": 3, "natural_gas": 4}, ["siege_walker", "ion_tempest"]),
    ("rare_earth_caldera", "Rare Earth Caldera", 5, "A collapsed volcano ringed with carbonatite.", {"brushless_motor": 40, "tungsten_carbide": 80, "embedded_controller": 80}, 650, 520,
     {"rare_earth_ore": 4, "monazite_sand": 2, "wolframite": 2}, ["toxic_fog", "salvage_leviathan"]),
    ("shattered_crater", "Shattered Crater", 6, "An impact crater laced with every ore on the frontier.", {"quantum_processor": 10, "superconductor_tape": 100, "graphene": 100}, 1000, 800,
     {"iron_ore": 6, "copper_ore": 6, "bauxite": 4, "ilmenite": 4, "rare_earth_ore": 3, "helium_gas": 2, "crude_oil": 4},
     ["salvage_leviathan", "ion_tempest"]),
    ("abyssal_trench", "Abyssal Trench", 7, "A drowned rift venting brine, gas and heavy sands.", {"metamaterial_lattice": 40, "plasma_coil": 10, "nano_coating": 100}, 1800, 1400,
     {"monazite_sand": 4, "wolframite": 4, "rare_earth_ore": 4, "helium_gas": 4, "natural_gas": 6, "brine": 6, "quartz_sand": 6},
     ["salvage_leviathan", "hive_barge", "ion_tempest"]),
]

# id, name, kind, desc, strength, appears_at_pollution
THREATS = [
    ("scrap_swarm", "Scrap Swarm", "machine", "Clouds of palm-sized salvage drones that strip anything loose.", 5, 50),
    ("dust_storm", "Dust Storm", "weather", "A brown wall of grit that clogs intakes and buries extractors.", 8, 120),
    ("rogue_salvager", "Rogue Salvager", "machine", "A reawakened demolition rig still following its last work order.", 20, 300),
    ("acid_rain", "Acid Rain", "weather", "Sulfurous downpours that eat exposed steel.", 30, 600),
    ("rust_crawlers", "Rust Crawlers", "machine", "Corroded maintenance bots that cannibalize pipework.", 50, 1000),
    ("feral_harvester", "Feral Harvester Rig", "machine", "An autonomous strip-mining rig gone off its claim map.", 90, 2000),
    ("magnetic_storm", "Magnetic Storm", "weather", "Geomagnetic surges that fry control boards and relays.", 140, 3500),
    ("scavenger_convoy", "Scavenger Convoy", "machine", "Armored haul trucks on a looping salvage route.", 220, 6000),
    ("siege_walker", "Siege Walker", "machine", "A legged excavator platform that tears down walls for scrap.", 400, 10000),
    ("toxic_fog", "Toxic Fog Bank", "weather", "A smog front so thick that crews and sensors go blind.", 600, 16000),
    ("salvage_leviathan", "Salvage Leviathan", "machine", "A crawling factory-ship that eats whole sectors.", 1000, 25000),
    ("ion_tempest", "Ion Tempest", "weather", "A charged superstorm drawn to large power grids.", 1600, 40000),
    ("hive_barge", "Hive Barge", "machine", "A drifting carrier that launches endless scrap swarms.", 2500, 60000),
]

CLIENTS = [
    ["Rustfield Co-op", "Harlan Brothers Haulage", "Dustwater Mission", "Old Pike Smithy"],
    ["Meridian Rail Co.", "Halvorsen Shipyards", "Granite Republic Works", "Coldharbor Mill"],
    ["Duskwater Utilities", "Ostrander Telegraph", "Vell & Sons Motors", "Kingsfield Waterworks"],
    ["Basalt Chemical Union", "Pellucid Polymers", "Morrow Tire & Rubber", "Saltmarsh Cooperative"],
    ["Kestrel Aerospace", "Ironveil Robotics", "Tamsin Instruments", "Northgate Foundries"],
    ["Orison Launch Authority", "Varga Atomics", "Highline Avionics", "Frontier Survey Bureau"],
    ["Aurelian Quantum", "Helix Fusion Consortium", "Lattice Dynamics", "Deepcold Labs"],
    ["Ark Steering Council", "Exodus Provisioning Board", "Last Light Foundation", "Ark Steering Council"],
]

CONTRACT_ITEMS = {
    0: [("iron_plate", 200), ("copper_wire", 300), ("iron_gear", 100), ("stone_brick", 150), ("iron_pipe", 80),
        ("fasteners", 400), ("copper_sheet", 150), ("blueprint_sheet", 30)],
    1: [("steel_plate", 200), ("steel_beam", 60), ("concrete", 150), ("glass_pane", 120), ("gearbox", 40),
        ("valve", 60), ("steel_frame", 30), ("coke", 300), ("cement", 200)],
    2: [("circuit_board", 150), ("electric_motor", 50), ("bronze_ingot", 120), ("bearing", 150), ("optical_sensor", 40),
        ("pump_unit", 30), ("capacitor", 300), ("pv_cell", 60), ("solar_array", 10)],
    3: [("plastic_sheet", 300), ("rubber", 200), ("insulated_cable", 200), ("control_board", 60), ("battery_cell", 80),
        ("lubricant", 2000), ("sulfuric_acid", 3000), ("fiberglass_panel", 120), ("hydraulic_ram", 40)],
    4: [("aluminum_sheet", 300), ("titanium_plate", 120), ("microchip", 300), ("composite_panel", 80),
        ("embedded_controller", 40), ("lithium_cell", 100), ("servo_motor", 60), ("robotic_arm", 20), ("turbine_blade", 40)],
    5: [("rocket_engine", 6), ("flight_computer", 30), ("rare_earth_magnet", 200), ("brushless_motor", 60),
        ("thorium_fuel_rod", 20), ("tungsten_carbide", 150), ("avionics_suite", 8), ("heat_shield_tile", 200),
        ("liquid_oxygen", 5000)],
    6: [("superconductor_tape", 200), ("quantum_processor", 10), ("graphene", 300), ("metamaterial_lattice", 20),
        ("fusion_pellet", 60), ("plasma_coil", 10), ("nano_coating", 120), ("cryocooler", 30)],
    7: [("heavy_launch_vehicle", 1), ("ark_hull_segment", 2), ("seed_vault", 1), ("cryostasis_pod", 10)],
}

# Per-tier reward item bundles, cycled through that tier's contracts (None = credits only).
REWARD_POOL = {
    0: [{"supply_crate": 2}, None, {"burner_drill": 2}, None],
    1: [{"electric_drill": 2}, None, {"storage_shed": 1}, {"conveyor_hub": 1}],
    2: [{"overclock_card_1": 1}, None, {"economizer_card_1": 1}, {"warehouse": 1}],
    3: [{"yield_optimizer_2": 1}, None, {"emission_filter_2": 2}, {"signal_relay": 1}],
    4: [{"overclock_card_3": 1}, None, {"robotic_arm": 4}, {"economizer_card_3": 1}],
    5: [{"yield_optimizer_4": 1}, None, {"thorium_fuel_rod": 4}, {"overclock_card_4": 1}],
    6: [{"overclock_card_5": 1}, None, {"yield_optimizer_5": 1}, {"fusion_pellet": 10}],
    7: [{"quantum_processor": 10}, {"yield_optimizer_5": 2}, {"economizer_card_5": 2}, {"plasma_coil": 4}],
}

# (id, name, desc, type, target, value)
ACHIEVEMENTS = [
    ("first_pour", "First Pour", "Smelt your first 100 iron ingots.", "produce", "iron_ingot", 100),
    ("plate_mountain", "Plate Mountain", "Press 10,000 iron plates.", "produce", "iron_plate", 10000),
    ("miles_of_wire", "Miles of Wire", "Draw 25,000 copper wire.", "produce", "copper_wire", 25000),
    ("drafting_department", "Drafting Department", "Produce 1,000 Blueprint Sheets.", "produce", "blueprint_sheet", 1000),
    ("crucible_keeper", "Crucible Keeper", "Cast 5,000 steel ingots.", "produce", "steel_ingot", 5000),
    ("poured_foundations", "Poured Foundations", "Pour 5,000 concrete slabs.", "produce", "concrete", 5000),
    ("clear_view", "Clear View", "Melt 2,000 glass panes.", "produce", "glass_pane", 2000),
    ("waste_not", "Waste Not", "Generate 2,000 scrap metal for the remelt line.", "produce", "scrap_metal", 2000),
    ("board_certified", "Board Certified", "Solder 1,000 circuit boards.", "produce", "circuit_board", 1000),
    ("spin_cycle", "Spin Cycle", "Wind 1,000 electric motors.", "produce", "electric_motor", 1000),
    ("schematic_archive", "Schematic Archive", "Produce 2,000 Circuit Schematics.", "produce", "circuit_schematic", 2000),
    ("dispatches", "Dispatches", "Compile 1,000 Field Reports.", "produce", "field_report", 1000),
    ("polymer_age", "Polymer Age", "Extrude 10,000 plastic sheets.", "produce", "plastic_sheet", 10000),
    ("acid_test", "Acid Test", "Brew 100,000 units of sulfuric acid.", "produce", "sulfuric_acid", 100000),
    ("under_control", "Under Control", "Build 1,000 control boards.", "produce", "control_board", 1000),
    ("wet_lab", "Wet Lab", "Produce 5,000 Chemical Assays.", "produce", "chemical_assay", 5000),
    ("green_thumb", "Green Thumb", "Harvest 5,000 algae paste.", "produce", "algae_paste", 5000),
    ("lightweight_champion", "Lightweight Champion", "Smelt 5,000 aluminum ingots.", "produce", "aluminum_ingot", 5000),
    ("titanic_effort", "Titanic Effort", "Win 2,000 titanium ingots.", "produce", "titanium_ingot", 2000),
    ("coupon_collector", "Coupon Collector", "Produce 10,000 Alloy Specimens.", "produce", "alloy_specimen", 10000),
    ("wafer_thin_margins", "Wafer-Thin Margins", "Fabricate 10,000 microchips.", "produce", "microchip", 10000),
    ("layered_thinking", "Layered Thinking", "Cure 1,000 composite panels.", "produce", "composite_panel", 1000),
    ("helping_hands", "Helping Hands", "Assemble 500 robotic arms.", "produce", "robotic_arm", 500),
    ("black_box", "Black Box", "Recover 20,000 Flight Telemetry recorders.", "produce", "flight_telemetry", 20000),
    ("ignition_sequence", "Ignition Sequence", "Build 50 rocket engines.", "produce", "rocket_engine", 50),
    ("fertile_ground", "Fertile Ground", "Fabricate 200 thorium fuel rods.", "produce", "thorium_fuel_rod", 200),
    ("zero_resistance", "Zero Resistance", "Deposit 2,000 superconductor tapes.", "produce", "superconductor_tape", 2000),
    ("superposition", "Superposition", "Package 100 quantum processors.", "produce", "quantum_processor", 100),
    ("datacore_vault", "Datacore Vault", "Produce 50,000 Quantum Datacores.", "produce", "quantum_datacore", 50000),
    ("bottled_star", "Bottled Star", "Press 1,000 fusion fuel pellets.", "produce", "fusion_pellet", 1000),
    ("heavy_lifter", "Heavy Lifter", "Stack 5 heavy launch vehicles.", "produce", "heavy_launch_vehicle", 5),
    ("age_of_steel", "Age of Steel", "Research Steelmaking.", "research", "steelmaking", 1),
    ("logic_gate", "Logic Gate", "Research Circuit Theory.", "research", "circuit_theory", 1),
    ("reagent_grade", "Reagent Grade", "Research Chemical Assays.", "research", "chemical_assays", 1),
    ("stress_test", "Stress Test", "Research Materials Testing.", "research", "materials_testing", 1),
    ("liftoff", "Liftoff", "Research Flight Testing.", "research", "flight_testing", 1),
    ("critical_mass", "Critical Mass", "Research Thorium Reactors.", "research", "thorium_reactors", 1),
    ("entangled", "Entangled", "Research Quantum Datacores.", "research", "quantum_datacores", 1),
    ("star_tamer", "Star Tamer", "Research Fusion Power.", "research", "fusion_power", 1),
    ("curious_mind", "Curious Mind", "Complete 10 technologies.", "research_count", None, 10),
    ("research_program", "Research Program", "Complete 50 technologies.", "research_count", None, 50),
    ("think_tank", "Think Tank", "Complete 150 technologies.", "research_count", None, 150),
    ("grand_library", "Grand Library", "Complete 300 technologies.", "research_count", None, 300),
    ("drill_team", "Drill Team", "Run 20 electric drills at once.", "build", "electric_drill", 20),
    ("line_up", "Line Up", "Run 25 assembly lines at once.", "build", "assembly_line", 25),
    ("refined_taste", "Refined Taste", "Run 5 distillation columns.", "build", "distillation_column", 5),
    ("sun_farm", "Sun Farm", "Build 100 solar arrays.", "build", "solar_array", 100),
    ("turbine_hall", "Turbine Hall", "Run 10 steam turbines.", "build", "steam_turbine", 10),
    ("lights_out_factory", "Lights-Out Factory", "Run 50 robotic workcells.", "build", "robotic_workcell", 50),
    ("reactor_row", "Reactor Row", "Run 4 thorium reactors.", "build", "thorium_reactor", 4),
    ("pad_zero", "Pad Zero", "Build a launch complex.", "build", "launch_complex", 1),
    ("twin_suns", "Twin Suns", "Run 2 tokamaks.", "build", "tokamak", 2),
    ("grid_online", "Grid Online", "Generate 1 MW.", "power", None, 1000),
    ("tens_of_megawatts", "Tens of Megawatts", "Generate 10 MW.", "power", None, 10000),
    ("utility_scale", "Utility Scale", "Generate 100 MW.", "power", None, 100000),
    ("gigawatt_grid", "Gigawatt Grid", "Generate 1 GW.", "power", None, 1000000),
    ("petty_cash", "Petty Cash", "Earn 10,000 credits in total.", "credits", None, 10000),
    ("foundry_fortune", "Foundry Fortune", "Earn 1,000,000 credits in total.", "credits", None, 1000000),
    ("industrial_empire", "Industrial Empire", "Earn 100,000,000 credits in total.", "credits", None, 100000000),
    ("planetary_ledger", "Planetary Ledger", "Earn 10,000,000,000 credits in total.", "credits", None, 10000000000),
    ("beyond_the_fence", "Beyond the Fence", "Claim a second sector.", "sectors", None, 2),
    ("frontier_baron", "Frontier Baron", "Hold 6 sectors.", "sectors", None, 6),
    ("map_filler", "Map Filler", "Hold 12 sectors.", "sectors", None, 12),
    ("every_corner", "Every Corner", "Hold every frontier sector.", "sectors", None, len(SECTORS)),
    ("first_order", "First Order", "Complete a contract.", "contracts", None, 1),
    ("reliable_supplier", "Reliable Supplier", "Complete 25 contracts.", "contracts", None, 25),
    ("preferred_vendor", "Preferred Vendor", "Complete 100 contracts.", "contracts", None, 100),
    ("hold_the_line", "Hold the Line", "Reach a defense rating of 100.", "defense", None, 100),
    ("fortress_works", "Fortress Works", "Reach a defense rating of 1,000.", "defense", None, 1000),
    ("unbreakable", "Unbreakable", "Reach a defense rating of 10,000.", "defense", None, 10000),
    ("bottom_of_the_well", "Bottom of the Well", "Complete the Deep Crust Borehole.", "megaproject", "deep_crust_borehole", 3),
    ("mapped_world", "Mapped World", "Complete the Planetary Survey Array.", "megaproject", "planetary_survey_array", 3),
    ("rail_to_the_sky", "Rail to the Sky", "Complete the Equatorial Mass Driver.", "megaproject", "equatorial_mass_driver", 4),
    ("keel_laid", "Keel Laid", "Finish the first stage of the Orbital Ark.", "megaproject", "orbital_ark", 1),
    ("exodus", "Exodus", "Launch the Orbital Ark.", "megaproject", "orbital_ark", 7),
    ("legacy", "Legacy", "Prestige for the first time.", "prestige", None, 1),
    ("dynasty", "Dynasty", "Prestige five times.", "prestige", None, 5),
]

MEGAPROJECTS = [
    ("deep_crust_borehole", "Deep Crust Borehole", 4, None,
     "A superdeep bore that maps the frontier's hidden ore bodies.",
     [("Drill Pad", {"concrete": 2000, "steel_frame": 200, "hydraulic_ram": 100}),
      ("Bore String", {"titanium_alloy": 200, "electric_motor": 300, "turbine_blade": 100}),
      ("Heat Probe", {"embedded_controller": 100, "heat_sink": 300, "composite_panel": 100})],
     {"effects": [eff("mining_productivity", None, 0.1), eff("extraction_slots", "solid", 1)]}),
    ("planetary_survey_array", "Planetary Survey Array", 5, "launch_complex",
     "Ground stations and sub-orbital probes that chart every deposit on the planet.",
     [("Ground Station", {"antenna_array": 200, "concrete": 3000, "embedded_controller": 200}),
      ("Probe Fleet", {"survey_probe": 40}),
      ("Deep Uplink", {"flight_computer": 100, "fiber_optic_cable": 1000, "lithium_cell": 400})],
     {"effects": [eff("extraction_slots", "fluid", 1), eff("extraction_slots", "solid", 1), eff("mining_productivity", None, 0.1)]}),
    ("equatorial_mass_driver", "Equatorial Mass Driver", 6, None,
     "A superconducting rail that flings cargo to orbit, cheapening every launch.",
     [("Foundation Trench", {"concrete": 20000, "steel_beam": 4000}),
      ("Accelerator Rail", {"coil_accelerator_segment": 100}),
      ("Capacitor Halls", {"lithium_cell": 2000, "superconductor_tape": 1000}),
      ("Guidance Bunker", {"quantum_processor": 20, "antenna_array": 200})],
     {"effects": [eff("market_price", None, 0.1), eff("craft_speed", "orbital", 0.25)]}),
    ("orbital_ark", "Orbital Ark", 7, "launch_complex",
     "A generation ship assembled in orbit: the frontier's last and greatest work.",
     [("Keel and Spine", {"ark_hull_segment": 10, "heavy_launch_vehicle": 5}),
      ("Drive Section", {"ark_drive_nacelle": 4, "heavy_launch_vehicle": 4}),
      ("Fusion Core", {"ark_fusion_core": 1, "heavy_launch_vehicle": 2}),
      ("Habitat Ring", {"ark_habitat_module": 12, "heavy_launch_vehicle": 6}),
      ("Life Support and Seed Vault", {"ark_life_support": 4, "seed_vault": 2, "heavy_launch_vehicle": 3}),
      ("Navigation and Command", {"ark_navigation_core": 1, "heavy_launch_vehicle": 1}),
      ("Crew Stasis and Departure", {"cryostasis_pod": 200, "heavy_launch_vehicle": 6})],
     {"prestige": True, "effects": []}),
]

START = {
    "credits": 500,
    "items": {"coal": 60, "stone": 40, "iron_plate": 40, "iron_gear": 12, "copper_wire": 20, "stone_brick": 10},
    "buildings": {"burner_drill": 4, "stone_furnace": 2, "fitting_bench": 1, "burner_boiler": 1, "steam_engine": 1,
                  "shore_intake": 1, "drafting_office": 1, "supply_crate": 1},
    "sectors": ["rustfield_lot"],
    # How the starting buildings are deployed (the engine creates these production lines).
    "lines": [
        {"building": "burner_drill", "recipe": "mine_iron_ore", "count": 2},
        {"building": "burner_drill", "recipe": "mine_coal", "count": 1},
        {"building": "burner_drill", "recipe": "mine_copper_ore", "count": 1},
        {"building": "stone_furnace", "recipe": "iron_ingot", "count": 1},
        {"building": "stone_furnace", "recipe": "copper_ingot", "count": 1},
        {"building": "fitting_bench", "recipe": "iron_plate", "count": 1},
        {"building": "shore_intake", "recipe": "pump_water", "count": 1},
        {"building": "burner_boiler", "recipe": "steam", "count": 1},
        {"building": "steam_engine", "recipe": "", "count": 1},
        {"building": "drafting_office", "recipe": "", "count": 1},
        {"building": "supply_crate", "recipe": "", "count": 1},
    ],
}

SETTINGS = {
    "base_cap_solid": 500, "base_cap_fluid": 5000, "base_throughput": 6, "offline_cap_hours": 8,
    "day_length_s": 600, "market_buy_mult": 1.6, "repeatable_cost_mult": 1.5,
}


def define():
    for did, name, arch, mat, col in DEPOSITS:
        item = C.items.get(did)
        C.deposits[did] = {"id": did, "name": name, "item": did, "kind": item["kind"] if item else "solid",
                           "visual": V(arch, mat, col, deposit=True)}
    for order, (sid, name, tier, desc, cost, dreq, threat, deps, hazards) in enumerate(SECTORS):
        C.sectors[sid] = {"id": sid, "name": name, "desc": desc, "tier": tier, "order": order, "claim_cost": cost,
                          "defense_required": dreq, "deposits": deps, "threat": threat, "hazards": hazards}
    for tid, name, kind, desc, strength, pol in THREATS:
        C.threats[tid] = {"id": tid, "name": name, "kind": kind, "desc": desc, "strength": strength,
                          "appears_at_pollution": pol}
    for mid, name, tier, building, desc, stages, reward in MEGAPROJECTS:
        C.megaprojects[mid] = {"id": mid, "name": name, "desc": desc, "tier": tier, "requires_building": building,
                               "stages": [{"name": n, "requires": req} for n, req in stages], "reward": reward}
    for aid, name, desc, ctype, target, value in ACHIEVEMENTS:
        C.achievements[aid] = {"id": aid, "name": name, "desc": desc,
                               "condition": {"type": ctype, "target": target, "value": value}}
    C.start = START
    C.settings = SETTINGS


# Target credit payout per contract by tier; amounts are derived from item values to hit it.
REWARD_TARGET = {0: 800, 1: 3000, 2: 10000, 3: 30000, 4: 90000, 5: 250000, 6: 700000, 7: 2000000}
VARIETY = [1.0, 0.7, 1.3, 0.85, 1.15]
NICE = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500,
        600, 800, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 15000, 20000, 30000, 50000]


def nice_amount(x):
    return min(NICE, key=lambda n: abs(n - x) / n)


def define_contracts():
    """Contracts need derived item values, so they are built after valuation. The amounts listed in
    CONTRACT_ITEMS are only hints; the delivered amount is set so the payout tracks REWARD_TARGET."""
    for tier, rows in CONTRACT_ITEMS.items():
        pool = REWARD_POOL[tier]
        for i, (iid, _hint) in enumerate(rows):
            item = C.items.get(iid)
            if item is None:
                C.errors.append(f"contracts: unknown item '{iid}'")
                continue
            client = CLIENTS[tier][i % len(CLIENTS[tier])]
            mult = 1.8 + 0.1 * tier
            amount = nice_amount(REWARD_TARGET[tier] * VARIETY[i % len(VARIETY)] / (item["value"] * mult))
            cid = f"t{tier}_{iid}"
            C.contracts[cid] = {"id": cid, "name": f"{item['name']} for {client}", "tier": tier,
                                "requires": {iid: amount}, "reward_credits": sig3(item["value"] * amount * mult),
                                "reward_items": dict(pool[i % len(pool)] or {})}
