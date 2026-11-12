"""Technology tree.

Cost profile per research unit (two most recent research tiers, not one of everything):
  T0-1 {Blueprint Sheets}  T2 {Blueprint, Circuit Schematics}  T3 {Schematics, Chemical Assays}
  T4 {Assays, Alloy Specimens}  T5 {Specimens, Flight Telemetry}  T6 {Telemetry, Quantum Datacores}
  T7 {Specimens, Telemetry, 2x Datacores}.  Defense branch ("fr") swaps the older item for Field Reports.
`unlocks` is filled from recipes' unlocked_by by build_content.py.
"""
from common import add_tech, eff, RESEARCH_BY_TIER as R, FIELD_REPORT as FR

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
TIME = [5, 10, 15, 20, 30, 40, 50, 60]
UNITS = [15, 50, 120, 250, 500, 1000, 2000, 4000]
GATE = {0: None, 1: None, 2: "circuit_theory", 3: "chemical_assays", 4: "materials_testing", 5: "flight_testing",
        6: "quantum_datacores", 7: "orbital_assembly"}


def cost_for(tier, fr=False):
    if fr:
        return {2: {FR: 1, R[2]: 1}, 3: {FR: 1, R[3]: 1}, 4: {FR: 1, R[4]: 1}, 5: {FR: 2, R[5]: 1},
                6: {FR: 2, R[6]: 1}, 7: {FR: 2, R[6]: 2}}[tier]
    if tier <= 1:
        return {R[1]: 1}
    if tier == 7:
        return {R[4]: 1, R[5]: 1, R[6]: 2}
    return {R[tier - 1]: 1, R[tier]: 1}


# (id, name, tier, branch, prereqs, units, desc, flags)   flags: "fr" = defense cost profile
UNLOCK_TECHS = [
    # ---------------------------------------------------------------- tier 0
    ("electric_mining", "Electric Mining", 0, "mining", [], 15, "Motorized drills that run on the grid instead of coal."),
    ("assembly_stations", "Assembly Stations", 0, "manufacturing", [], 15, "Jig-fed stations that out-build the fitting bench."),
    ("storage_sheds", "Storage Sheds", 0, "logistics", [], 10, "Racked sheds for the growing stockpile."),
    ("coking", "Coking", 0, "metallurgy", [], 10, "Bake coal into coke for hotter fires and steel."),
    ("stamping_presses", "Stamping Presses", 0, "metallurgy", [], 15, "Dedicated flywheel presses for plate, rod and wire."),
    # ---------------------------------------------------------------- tier 1
    ("steelmaking", "Steelmaking", 1, "metallurgy", ["coking"], 40, "Alloy iron with coke for plate and structural beams."),
    ("blast_furnaces", "Blast Furnaces", 1, "metallurgy", ["steelmaking"], 50, "Hot-blast stacks with double throughput."),
    ("scrap_reclamation", "Scrap Reclamation", 1, "metallurgy", ["steelmaking"], 50, "Remelt rolling scrap and regrind slag."),
    ("quarrying", "Quarrying", 1, "mining", ["electric_mining"], 30, "Open limestone faces, crushers and lime kilns."),
    ("cement_works", "Cement Works", 1, "manufacturing", ["quarrying"], 40, "Grind clinker and pour concrete slabs."),
    ("glassmaking", "Glassmaking", 1, "metallurgy", ["quarrying"], 40, "Dredge quartz sand and melt soda-lime glass."),
    ("mechanical_engineering", "Mechanical Engineering", 1, "manufacturing", ["assembly_stations", "steelmaking"], 50,
     "Gearboxes, springs and valves for real machinery."),
    ("structural_steel", "Structural Steel", 1, "manufacturing", ["steelmaking"], 40, "Bolted steel frames for heavy equipment."),
    ("conveyor_hubs", "Conveyor Hubs", 1, "logistics", ["assembly_stations"], 30, "Roller junctions that raise factory throughput."),
    ("fluid_storage", "Fluid Storage", 1, "logistics", ["storage_sheds", "mechanical_engineering"], 40, "Riveted tanks for water, steam and oils."),
    ("gasifier_power", "Gasifier Power", 1, "power", ["mechanical_engineering"], 50, "Burn solid fuel in a gas engine without boilers."),
    ("fortifications", "Fortifications", 1, "defense", [], 20, "Palisades against scavengers and scrap swarms."),
    ("concrete_barriers", "Concrete Barriers", 1, "defense", ["fortifications", "cement_works"], 40, "Precast barriers for the perimeter."),
    ("munitions", "Munitions", 1, "defense", ["fortifications", "mechanical_engineering"], 50, "Sentry guns and a works to load their rounds."),
    ("tin_smelting", "Tin Smelting", 1, "metallurgy", ["glassmaking", "coking"], 50, "Reduce cassiterite to tin for solder and bronze."),
    ("circuit_theory", "Circuit Theory", 1, "electronics", ["tin_smelting", "mechanical_engineering"], 75,
     "Ceramic boards, soldered logic and the Circuit Schematics that teach it."),
    # ---------------------------------------------------------------- tier 2
    ("electromagnetism", "Electromagnetism", 2, "electronics", ["circuit_theory"], 100, "Wound magnets, bearings and induction motors."),
    ("passive_components", "Passive Components", 2, "electronics", ["circuit_theory"], 100, "Capacitors and optical sensors."),
    ("hydraulics", "Hydraulics", 2, "manufacturing", ["electromagnetism"], 120, "Motor-driven pumps and pump stations."),
    ("wind_power", "Wind Power", 2, "power", ["electromagnetism"], 120, "Free, gusty power from the frontier winds."),
    ("photovoltaics", "Photovoltaics", 2, "power", ["passive_components"], 150, "Copper-oxide cells and the first solar arrays."),
    ("flywheel_storage", "Flywheel Storage", 2, "power", ["electromagnetism"], 120, "Spin up rotors to buffer the grid."),
    ("high_pressure_steam", "High-Pressure Steam", 2, "power", ["hydraulics"], 150, "Water-tube boilers feeding five engines each."),
    ("power_distribution", "Power Distribution", 2, "power", ["electromagnetism"], 100, "Substations that trim a bay's power draw."),
    ("rolling_mills", "Rolling Mills", 2, "metallurgy", ["electromagnetism"], 120, "Rolling mills and drawing benches."),
    ("assembly_lines", "Assembly Lines", 2, "manufacturing", ["electromagnetism"], 150, "Motorized assembly lines."),
    ("research_laboratories", "Research Laboratories", 2, "research", ["passive_components", "electromagnetism"], 150,
     "Instrumented labs that research twice as fast."),
    ("warehousing", "Warehousing", 2, "logistics", ["electromagnetism"], 100, "Warehouses and bulk silos."),
    ("sorting_hubs", "Sorting Hubs", 2, "logistics", ["conveyor_hubs", "passive_components", "electromagnetism"], 120,
     "Sensor-gated sorting for more throughput."),
    ("air_scrubbing", "Air Scrubbing", 2, "chemistry", ["electromagnetism"], 120, "Wet scrubbers that pull smog out of the air."),
    ("radar", "Radar", 2, "defense", ["passive_components", "munitions", "electromagnetism"], 120, "Rotating radar for early warning."),
    ("field_reporting", "Field Reporting", 2, "defense", ["radar", "concrete_barriers"], 100,
     "Compile patrol data into Field Reports for defense research."),
    ("armor_piercing_rounds", "Armor-Piercing Rounds", 2, "defense", ["field_reporting"], 150, "Hardened rounds for armored salvagers.", "fr"),
    ("module_engineering", "Module Engineering", 2, "electronics", ["passive_components", "electromagnetism"], 150,
     "Plug-in Mk I module cards for any bay."),
    ("oil_extraction", "Oil Extraction", 2, "chemistry", ["hydraulics"], 150, "Pumpjacks on the crude reservoirs."),
    ("oil_refining", "Oil Refining", 2, "chemistry", ["oil_extraction"], 175, "Distill crude into heavy oil, naphtha and fuel gas."),
    ("polymer_chemistry", "Polymer Chemistry", 2, "chemistry", ["oil_refining"], 175, "Chemical reactors, plastic pellets and sheet."),
    ("sulfur_processing", "Sulfur Processing", 2, "chemistry", ["polymer_chemistry"], 150, "Mine native sulfur and make sulfuric acid."),
    ("synthetic_rubber", "Synthetic Rubber", 2, "chemistry", ["sulfur_processing"], 175, "Vulcanized rubber and insulated cable."),
    ("chemical_assays", "Chemical Assays", 2, "research", ["synthetic_rubber", "research_laboratories"], 200,
     "Sealed reagent kits that unlock chemical-era research."),
    # ---------------------------------------------------------------- tier 3
    ("gas_processing", "Gas Processing", 3, "chemistry", ["chemical_assays"], 200, "Tap gas wells and sweeten sour gas into fuel gas."),
    ("gas_turbines", "Gas Turbines", 3, "power", ["gas_processing"], 250, "Open-cycle turbines burning fuel gas."),
    ("lubricants", "Lubricants", 3, "chemistry", ["chemical_assays"], 200, "Base-oil blending and hydraulic rams."),
    ("chlor_alkali", "Chlor-Alkali Process", 3, "chemistry", ["chemical_assays"], 250, "Pump brine and split it into chlorine, hydrogen and caustic soda."),
    ("brine_evaporation", "Brine Evaporation", 3, "chemistry", ["chlor_alkali"], 200, "Evaporate brine for salt and potash."),
    ("sodium_sulfur_batteries", "Sodium-Sulfur Batteries", 3, "power", ["chlor_alkali"], 250, "Hot sodium-sulfur cells and grid battery banks."),
    ("epoxy_resins", "Epoxy Resins", 3, "chemistry", ["chlor_alkali"], 250, "Epoxy, glass fiber and fiberglass laminate."),
    ("control_systems", "Control Systems", 3, "electronics", ["epoxy_resins"], 300, "Multilayer control boards for smarter machines."),
    ("surface_mount", "Surface-Mount Assembly", 3, "electronics", ["control_systems"], 300, "Pick-and-place electronics lines."),
    ("induction_furnaces", "Induction Furnaces", 3, "metallurgy", ["chemical_assays"], 200, "Clean, fast electric smelting."),
    ("cone_crushers", "Cone Crushers", 3, "mining", ["chemical_assays"], 200, "Gyratory crushers with double throughput."),
    ("industrial_mixers", "Industrial Mixers", 3, "manufacturing", ["chemical_assays"], 200, "Twin-shaft blenders with metered dosing."),
    ("heavy_drilling", "Heavy Drilling", 3, "mining", ["lubricants"], 250, "Hydraulic bore drills with twice the bite."),
    ("signal_relays", "Signal Relays", 3, "electronics", ["control_systems"], 300, "Bay-wide timing relays that speed up machines."),
    ("precipitators", "Electrostatic Precipitators", 3, "chemistry", ["air_scrubbing", "chemical_assays"], 250,
     "Filter cartridges and charged-plate precipitators."),
    ("pneumatic_tubes", "Pneumatic Tubes", 3, "logistics", ["sorting_hubs", "chemical_assays"], 250, "Capsule tubes linking every bay."),
    ("rail_logistics", "Rail Logistics", 3, "logistics", ["pneumatic_tubes", "control_systems"], 300, "Rail depots for bulk freight."),
    ("pipelines", "Pipelines", 3, "logistics", ["chemical_assays", "fluid_storage"], 200, "Booster stations for long fluid lines."),
    ("algae_cultivation", "Algae Cultivation", 3, "biotech", ["brine_evaporation"], 250, "Photobioreactors for algae, bio-oil and biofuel."),
    ("fuel_briquettes", "Fuel Briquettes", 3, "power", ["chemical_assays"], 150, "Press coke and pitch into long-burning briquettes."),
    ("blasting_compounds", "Blasting Compounds", 3, "defense", ["brine_evaporation", "field_reporting"], 250,
     "Blasting powder, fragmentation shells and mortars.", "fr"),
    ("incendiaries", "Incendiaries", 3, "defense", ["field_reporting", "chemical_assays"], 250, "Gelled-fuel canisters and flame projectors.", "fr"),
    ("heavy_autocannons", "Heavy Autocannons", 3, "defense", ["armor_piercing_rounds", "chemical_assays"], 300,
     "Powered twin-cannon mounts.", "fr"),
    ("module_engineering_2", "Module Engineering II", 3, "electronics", ["control_systems", "module_engineering", "precipitators", "sodium_sulfur_batteries"], 300,
     "Mk II module cards on control boards."),
    ("bayer_process", "Bayer Process", 3, "metallurgy", ["chlor_alkali"], 300, "Mine bauxite and digest it to alumina."),
    ("aluminum_electrolysis", "Aluminum Electrolysis", 3, "metallurgy", ["bayer_process"], 300, "Carbon anodes and electrolytic aluminum."),
    ("magnesium_extraction", "Magnesium Extraction", 3, "metallurgy", ["chlor_alkali"], 250, "Win magnesium metal from brine."),
    ("arc_furnaces", "Arc Furnaces", 3, "metallurgy", ["induction_furnaces", "control_systems"], 300, "Arc furnaces and metallurgical silicon."),
    ("titanium_metallurgy", "Titanium Metallurgy", 3, "metallurgy", ["arc_furnaces", "magnesium_extraction"], 350,
     "Chloride-process titanium from ilmenite sand."),
    ("aerospace_alloys", "Aerospace Alloys", 3, "metallurgy", ["titanium_metallurgy", "aluminum_electrolysis"], 400,
     "Casting foundries, duralumin and titanium alloy."),
    ("materials_testing", "Materials Testing", 3, "research", ["aerospace_alloys", "epoxy_resins"], 400,
     "Alloy Specimens that open advanced-materials research."),
    # ---------------------------------------------------------------- tier 4
    ("air_separation", "Air Separation", 4, "chemistry", ["materials_testing"], 400, "Cold boxes that split air into oxygen and nitrogen."),
    ("nitrogen_chemistry", "Nitrogen Chemistry", 4, "chemistry", ["air_separation"], 450, "Ammonia, nitric acid and soda ash."),
    ("contact_process", "Contact Process", 4, "chemistry", ["air_separation"], 350, "Oxygen-fed sulfuric acid at double yield."),
    ("float_glass", "Float Glass", 4, "metallurgy", ["nitrogen_chemistry"], 350, "Soda-ash glass at twice the yield."),
    ("hydrocracking", "Hydrocracking", 4, "chemistry", ["materials_testing"], 400, "Crack heavy oil to naphtha with hydrogen."),
    ("catalytic_reactors", "Catalytic Reactors", 4, "chemistry", ["materials_testing"], 450, "Faster fixed-bed chemical reactors."),
    ("semiconductor_refining", "Semiconductor Refining", 4, "electronics", ["materials_testing"], 500,
     "Hydrochloric acid, polysilicon and single-crystal wafers."),
    ("microelectronics", "Microelectronics", 4, "electronics", ["semiconductor_refining"], 500, "Lithography fabs and microchips."),
    ("fiber_optics", "Fiber Optics", 4, "electronics", ["materials_testing"], 400, "Jacketed glass fiber for data links."),
    ("embedded_systems", "Embedded Systems", 4, "electronics", ["microelectronics", "fiber_optics"], 550, "Board-level computers for every machine."),
    ("carbon_fiber", "Carbon Fiber", 4, "metallurgy", ["nitrogen_chemistry"], 500, "Acrylic precursor, carbon fiber and composite panels."),
    ("precision_engineering", "Precision Engineering", 4, "manufacturing", ["microelectronics"], 500,
     "Clean-room assembly, servos, lenses and heat sinks."),
    ("harmonic_drives", "Harmonic Drives", 4, "manufacturing", ["precision_engineering"], 450, "Zero-backlash strain-wave gearing."),
    ("robotics", "Robotics", 4, "manufacturing", ["harmonic_drives", "embedded_systems"], 600, "Six-axis arms and robotic workcells."),
    ("lithium_extraction", "Lithium Extraction", 4, "chemistry", ["nitrogen_chemistry"], 500, "Lithium carbonate from brine and lithium-ion cells."),
    ("turbine_engineering", "Turbine Engineering", 4, "power", ["materials_testing"], 450, "Cast titanium turbine blades."),
    ("steam_turbines", "Steam Turbines", 4, "power", ["turbine_engineering", "high_pressure_steam"], 500,
     "Superheaters and multi-stage steam turbines."),
    ("thin_film_solar", "Thin-Film Solar", 4, "power", ["semiconductor_refining", "photovoltaics"], 500, "Silicon thin-film solar fields."),
    ("tidal_power", "Tidal Power", 4, "power", ["turbine_engineering"], 450, "Bulb turbines in a tidal barrage."),
    ("hydraulic_presses", "Hydraulic Presses", 4, "metallurgy", ["materials_testing", "lubricants", "control_systems"], 450,
     "Forge presses three times faster than a mill."),
    ("automated_storage", "Automated Storage", 4, "logistics", ["robotics", "warehousing"], 550, "Robot-picked high-bay warehouses."),
    ("pressurized_tanks", "Pressurized Tanks", 4, "logistics", ["materials_testing", "pipelines"], 400, "Sphere tank farms for fluids."),
    ("drone_logistics", "Drone Logistics", 4, "logistics", ["robotics", "lithium_extraction"], 600, "Cargo drones and drone ports."),
    ("freight_yards", "Freight Yards", 4, "logistics", ["rail_logistics", "materials_testing"], 500, "Hump yards with automatic couplers."),
    ("bioleaching", "Bioleaching", 4, "biotech", ["algae_cultivation", "materials_testing"], 400, "Microbes that leach copper at high yield."),
    ("bioplastics", "Bioplastics", 4, "biotech", ["bioleaching"], 400, "Plastic pellets from algae and bio-oil."),
    ("red_mud_recovery", "Red Mud Recovery", 4, "metallurgy", ["materials_testing", "precipitators"], 350,
     "Reclamation plants that win iron back from residue."),
    ("materials_labs", "Materials Labs", 4, "research", ["materials_testing"], 500, "Materials test labs at triple research speed."),
    ("thermite", "Thermite", 4, "defense", ["materials_testing", "field_reporting"], 400, "Aluminum powder and thermite charges.", "fr"),
    ("high_explosives", "High Explosives", 4, "defense", ["nitrogen_chemistry", "blasting_compounds"], 500, "Nitrated explosives and HE shells.", "fr"),
    ("laser_weapons", "Laser Weapons", 4, "defense", ["precision_engineering", "embedded_systems", "field_reporting", "sodium_sulfur_batteries"], 600,
     "Capacitor packs and pulse laser turrets.", "fr"),
    ("armored_bulwarks", "Armored Bulwarks", 4, "defense", ["materials_testing", "concrete_barriers", "field_reporting"], 400,
     "Titanium-faced perimeter walls.", "fr"),
    ("automated_arsenals", "Automated Arsenals", 4, "defense", ["robotics", "munitions", "field_reporting"], 600, "Robotic ordnance lines.", "fr"),
    ("module_engineering_3", "Module Engineering III", 4, "electronics",
     ["embedded_systems", "module_engineering_2", "precision_engineering", "lithium_extraction"], 600, "Mk III module cards on embedded controllers."),
    ("rocket_propellants", "Rocket Propellants", 4, "aerospace", ["air_separation", "hydrocracking"], 500, "Rocket kerosene and liquid oxygen."),
    ("airframes", "Airframes", 4, "aerospace", ["carbon_fiber", "precision_engineering", "aerospace_alloys"], 500, "Duralumin-composite airframe panels."),
    ("phased_arrays", "Phased Arrays", 4, "aerospace", ["embedded_systems"], 500, "Electronically steered antenna panels."),
    ("flight_testing", "Flight Testing", 4, "aerospace", ["rocket_propellants", "airframes", "phased_arrays"], 800,
     "Fly instrumented test articles and recover their telemetry."),
    # ---------------------------------------------------------------- tier 5
    ("monazite_processing", "Monazite Processing", 5, "power", ["flight_testing"], 800, "Digest monazite into thoria and rare earths."),
    ("isotope_centrifuges", "Isotope Centrifuges", 5, "power", ["monazite_processing"], 900, "Centrifuge cascades that enrich fissile seed."),
    ("thorium_fuel", "Thorium Fuel", 5, "power", ["isotope_centrifuges"], 1000, "Fabricate seeded thorium fuel rods."),
    ("thorium_reactors", "Thorium Reactors", 5, "power", ["thorium_fuel", "steam_turbines"], 1200, "Reactors, fission and cooling towers."),
    ("fuel_reprocessing", "Fuel Reprocessing", 5, "power", ["thorium_reactors"], 1000, "Recover fissile seed and thoria from spent rods."),
    ("tungsten_metallurgy", "Tungsten Metallurgy", 5, "metallurgy", ["flight_testing"], 800, "Mine wolframite and sinter tungsten carbide."),
    ("rare_earth_magnets", "Rare-Earth Magnets", 5, "electronics", ["monazite_processing"], 900, "Sintered magnets and brushless motors."),
    ("rocket_engines", "Rocket Engines", 5, "aerospace", ["tungsten_metallurgy", "rare_earth_magnets", "turbine_engineering"], 1200,
     "Nozzles, turbopumps and liquid-fuel engines."),
    ("avionics", "Avionics", 5, "aerospace", ["flight_testing"], 1000, "Flight computers, laser gyros and avionics suites."),
    ("heat_shielding", "Heat Shielding", 5, "aerospace", ["flight_testing"], 800, "Ceramic heat shield tiles."),
    ("cryogenic_liquefaction", "Cryogenic Liquefaction", 5, "chemistry", ["flight_testing"], 800, "Turbo-expanders and liquid hydrogen."),
    ("deep_core_drilling", "Deep Core Drilling", 5, "mining", ["tungsten_metallurgy"], 900, "Carbide-bit drills for the deep seams."),
    ("offshore_drilling", "Offshore Drilling", 5, "mining", ["deep_core_drilling"], 1000, "Jack-up rigs on the shelf reservoirs."),
    ("geothermal_power", "Geothermal Power", 5, "power", ["deep_core_drilling", "steam_turbines"], 1100, "Flash plants on deep hot wells."),
    ("heavy_wind_turbines", "Heavy Wind Turbines", 5, "power", ["rare_earth_magnets"], 1000, "Direct-drive magnet turbines."),
    ("combined_cycle", "Combined Cycle", 5, "power", ["flight_testing", "turbine_engineering"], 1000, "Gas turbines with a steam bottoming stage."),
    ("membrane_electrolysis", "Membrane Electrolysis", 5, "chemistry", ["flight_testing"], 900, "Ion-membrane electrolyzer stacks."),
    ("fractionation", "Fractionation", 5, "chemistry", ["flight_testing"], 900, "Vacuum fractionation towers."),
    ("ball_mills", "Ball Mills", 5, "mining", ["tungsten_metallurgy"], 800, "Carbide-lined grinding mills."),
    ("fermentation", "Fermentation", 5, "biotech", ["flight_testing", "bioplastics"], 900, "Sterile vats and engineered enzyme cultures."),
    ("grid_lithium_storage", "Grid Lithium Storage", 5, "power", ["flight_testing"], 900, "Containerized lithium storage arrays."),
    ("overclock_relays", "Overclock Relays", 5, "electronics", ["flight_testing", "signal_relays"], 1000, "Stronger bay-wide speed relays."),
    ("catalytic_scrubbers", "Catalytic Scrubbers", 5, "chemistry", ["monazite_processing", "precipitators"], 900, "Rare-earth catalyst scrubbers."),
    ("heavy_drones", "Heavy Drones", 5, "logistics", ["rare_earth_magnets", "drone_logistics"], 1100, "Heavy-lift drone ports."),
    ("cryogenic_storage", "Cryogenic Storage", 5, "logistics", ["cryogenic_liquefaction", "pressurized_tanks"], 900, "Vacuum-jacketed dewars."),
    ("launch_complex", "Launch Complex", 5, "aerospace", ["rocket_engines", "avionics", "heat_shielding"], 1500,
     "A launch pad and survey probes for the first megaprojects."),
    ("tungsten_penetrators", "Tungsten Penetrators", 5, "defense", ["tungsten_metallurgy", "heavy_autocannons"], 1000, "Carbide-cored rounds.", "fr"),
    ("guided_munitions", "Guided Munitions", 5, "defense", ["avionics", "high_explosives"], 1200, "Guided shells and howitzers.", "fr"),
    ("pyrophorics", "Pyrophorics", 5, "defense", ["thermite", "incendiaries", "flight_testing"], 1000, "Pyrophoric gel and thermal lances.", "fr"),
    ("lithium_charge_packs", "Lithium Charge Packs", 5, "defense", ["laser_weapons", "flight_testing"], 1000, "Dense packs for beam weapons.", "fr"),
    ("shield_projectors", "Shield Projectors", 5, "defense", ["rare_earth_magnets", "field_reporting"], 1300, "Magnetic deflector domes.", "fr"),
    ("early_warning", "Early Warning", 5, "defense", ["phased_arrays", "radar", "flight_testing", "field_reporting"], 900, "Phased-array radar networks.", "fr"),
    ("module_engineering_4", "Module Engineering IV", 5, "electronics", ["module_engineering_3", "avionics", "rare_earth_magnets"], 1200,
     "Mk IV module cards with flight-grade computers."),
    ("helium_recovery", "Helium Recovery", 5, "quantum", ["cryogenic_liquefaction"], 1000, "Tap helium wells and liquefy the gas."),
    ("rare_earth_separation", "Rare-Earth Separation", 5, "quantum", ["monazite_processing", "semiconductor_refining"], 1000,
     "Mine rare-earth ore and separate yttrium by solvent extraction."),
    ("superconductors", "Superconductors", 5, "quantum", ["rare_earth_separation", "robotics", "air_separation"], 1200,
     "Nanofabricators and superconducting tape."),
    ("cryocoolers", "Cryocoolers", 5, "quantum", ["helium_recovery", "rare_earth_magnets"], 1100, "Closed-cycle millikelvin refrigerators."),
    ("qubit_fabrication", "Qubit Fabrication", 5, "quantum", ["superconductors", "cryocoolers"], 1400, "Superconducting qubit arrays."),
    ("quantum_datacores", "Quantum Datacores", 5, "research", ["qubit_fabrication"], 1500,
     "Cryo-sealed datacores that open quantum-era research."),
    # ---------------------------------------------------------------- tier 6
    ("graphene_synthesis", "Graphene Synthesis", 6, "quantum", ["quantum_datacores"], 1500, "Grow graphene film on copper foil."),
    ("carbon_nanotubes", "Carbon Nanotubes", 6, "quantum", ["graphene_synthesis"], 1800, "Spin nanotube yarn."),
    ("metamaterials", "Metamaterials", 6, "quantum", ["carbon_nanotubes"], 2200, "Engineered nano-lattices."),
    ("nano_coatings", "Nano Coatings", 6, "quantum", ["carbon_nanotubes"], 1800, "Self-healing nano-ceramic coatings."),
    ("quantum_computing", "Quantum Computing", 6, "quantum", ["quantum_datacores"], 2000, "Packaged quantum processors."),
    ("deuterium_separation", "Deuterium Separation", 6, "power", ["quantum_datacores"], 1500, "Isotopic electrolysis for heavy hydrogen."),
    ("fusion_fuel", "Fusion Fuel", 6, "power", ["deuterium_separation", "graphene_synthesis", "lithium_extraction"], 2000,
     "Deuterium-lithium target pellets."),
    ("plasma_confinement", "Plasma Confinement", 6, "power", ["quantum_datacores", "rare_earth_magnets"], 2200, "Superconducting containment coils."),
    ("fusion_power", "Fusion Power", 6, "power", ["fusion_fuel", "plasma_confinement", "quantum_computing"], 3000, "Tokamak reactors."),
    ("smes", "Superconducting Storage", 6, "power", ["plasma_confinement"], 2000, "Magnetic energy storage rings."),
    ("breeder_reactors", "Breeder Reactors", 6, "power", ["quantum_datacores", "fuel_reprocessing"], 2200, "Fast reactors that breed fissile seed."),
    ("plasma_furnaces", "Plasma Furnaces", 6, "metallurgy", ["quantum_datacores"], 1800, "Plasma-torch arc furnaces."),
    ("vacuum_casting", "Vacuum Casting", 6, "metallurgy", ["quantum_datacores"], 1800, "Vacuum induction foundries."),
    ("micro_precision", "Micro-Precision Assembly", 6, "manufacturing", ["quantum_datacores"], 2000, "Nanometer-tolerance assembly cells."),
    ("autonomous_fabrication", "Autonomous Fabrication", 6, "manufacturing", ["quantum_computing"], 2500, "Self-scheduling general fabricators."),
    ("flow_chemistry", "Flow Chemistry", 6, "chemistry", ["graphene_synthesis"], 2000, "Continuous microchannel reactors."),
    ("isotope_separators", "Isotope Separators", 6, "power", ["quantum_datacores"], 2000, "Maglev rotor isotope separators."),
    ("dilution_refrigeration", "Dilution Refrigeration", 6, "quantum", ["quantum_datacores"], 2000, "Millikelvin cryogenic plants."),
    ("molecular_assembly", "Molecular Assembly", 6, "quantum", ["metamaterials", "quantum_computing"], 3000, "Directed self-assembly reactors."),
    ("plasma_boring", "Plasma Boring", 6, "mining", ["plasma_confinement", "deep_core_drilling"], 2500, "Plasma-spalling bores."),
    ("quantum_research", "Quantum Research", 6, "research", ["quantum_computing"], 2500, "Quantum research centers."),
    ("quantum_sync", "Quantum Synchronization", 6, "electronics", ["quantum_computing", "overclock_relays"], 2500, "Quantum-clocked bay relays."),
    ("carbon_capture", "Carbon Capture", 6, "chemistry", ["carbon_nanotubes"], 2000, "Nanotube sorbent capture towers."),
    ("maglev_freight", "Maglev Freight", 6, "logistics", ["quantum_datacores", "rare_earth_magnets"], 2200, "Superconducting freight terminals."),
    ("vault_complexes", "Vault Complexes", 6, "logistics", ["nano_coatings", "robotics"], 2000, "Underground vault storage."),
    ("biosorption", "Biosorption", 6, "biotech", ["quantum_datacores", "fermentation"], 1500, "Enzyme cultures that sort rare earths."),
    ("nutrient_synthesis", "Nutrient Synthesis", 6, "biotech", ["quantum_datacores", "fermentation"], 1500, "Complete synthetic food paste."),
    ("mass_driver_engineering", "Mass Driver Engineering", 6, "aerospace", ["quantum_datacores", "lithium_extraction"], 2500,
     "Superconducting accelerator segments."),
    ("railguns", "Railguns", 6, "defense", ["graphene_synthesis", "field_reporting"], 2500, "Railgun batteries.", "fr"),
    ("supercapacitors", "Supercapacitors", 6, "defense", ["graphene_synthesis", "lithium_charge_packs"], 2000, "Graphene supercapacitor cells.", "fr"),
    ("interceptor_drones", "Interceptor Drones", 6, "defense", ["carbon_nanotubes", "heavy_drones", "avionics", "tungsten_penetrators"], 2500,
     "Armed drone nests and hypervelocity slugs.", "fr"),
    ("aegis_fields", "Aegis Fields", 6, "defense", ["plasma_confinement", "quantum_computing", "shield_projectors"], 3000,
     "Plasma-backed field domes.", "fr"),
    ("module_engineering_5", "Module Engineering V", 6, "electronics",
     ["quantum_computing", "metamaterials", "module_engineering_4"], 3000, "Mk V module cards on quantum processors."),
    ("orbital_assembly", "Orbital Assembly", 6, "aerospace", ["launch_complex", "metamaterials", "quantum_computing", "cryogenic_liquefaction"], 4000,
     "Orbital gantries and heavy launch vehicles."),
    # ---------------------------------------------------------------- tier 7
    ("ark_structures", "Ark Structures", 7, "aerospace", ["orbital_assembly", "nano_coatings"], 3000, "Lattice-armored hull segments."),
    ("ark_propulsion", "Ark Propulsion", 7, "aerospace", ["ark_structures", "plasma_confinement"], 4000, "Plasma drive nacelles."),
    ("ark_fusion_core", "Ark Fusion Core", 7, "aerospace", ["ark_propulsion", "fusion_power"], 5000, "The Ark's compact tokamak heart."),
    ("ark_habitation", "Ark Habitation", 7, "aerospace", ["ark_structures", "cryocoolers"], 4000, "Habitat rings and cryostasis pods."),
    ("ark_life_support", "Ark Life Support", 7, "biotech", ["ark_habitation", "nutrient_synthesis"], 4000, "Closed-loop life support and seed vaults."),
    ("ark_navigation", "Ark Navigation", 7, "aerospace", ["ark_structures", "quantum_computing", "avionics"], 5000, "Quantum deep-space navigation."),
    ("zero_g_assembly", "Zero-G Assembly", 7, "manufacturing", ["ark_structures"], 4000, "Heavy orbital gantries."),
]

# (base, name, branch, tiers, effect, target, per level, first-level prereqs, flavour, fr)
LEVELED = [
    ("drill_bit_metallurgy", "Drill Bit Metallurgy", "mining", [1, 2, 3, 4, 5], "mining_productivity", None, 0.1, ["electric_mining"], "Harder bit alloys and better flushing", False),
    ("survey_claims", "Survey Claims", "mining", [1, 3, 5], "extraction_slots", "solid", 1, ["quarrying"], "Registered survey rights on claimed land", False),
    ("well_permits", "Well Permits", "mining", [3, 4, 6], "extraction_slots", "fluid", 1, ["gas_processing"], "Extra drilling and pumping permits", False),
    ("furnace_draft", "Furnace Draft", "metallurgy", [1, 2, 3, 4], "craft_speed", "smelting", 0.1, ["blast_furnaces"], "Forced-draft fans and better refractories", False),
    ("assembly_tooling", "Assembly Tooling", "manufacturing", [1, 2, 3, 4, 5], "craft_speed", "assembling", 0.1, ["mechanical_engineering"], "Quick-change jigs and torque tools", False),
    ("press_hydraulics", "Press Hydraulics", "metallurgy", [1, 3, 4], "craft_speed", "pressing", 0.1, ["stamping_presses"], "Faster ram cycles", False),
    ("circuit_yield", "Circuit Yield", "electronics", [2, 3, 4, 5], "craft_speed", "electronics", 0.1, ["passive_components"], "Better reflow profiles and fewer rejects", False),
    ("reaction_kinetics", "Reaction Kinetics", "chemistry", [3, 4, 5], "craft_speed", "chemistry", 0.1, ["chemical_assays"], "Tuned temperatures and stirring", False),
    ("cracking_catalysts", "Cracking Catalysts", "chemistry", [3, 4, 5], "craft_speed", "refining", 0.1, ["chemical_assays"], "Zeolite catalysts in every column", False),
    ("lab_automation", "Lab Automation", "research", [0, 1, 2, 3, 4, 5, 6], "lab_speed", None, 0.1, [], "Automated sample handling", False),
    ("peer_review", "Peer Review", "research", [2, 4, 6], "lab_productivity", None, 0.05, ["research_laboratories"], "Shared results and fewer repeated trials", False),
    ("warehouse_racking", "Warehouse Racking", "logistics", [0, 1, 2, 3, 4, 5], "storage_capacity", None, 0.15, ["storage_sheds"], "Taller racks and tighter packing", False),
    ("boiler_efficiency", "Boiler Efficiency", "power", [1, 2, 3], "power_output", "steam", 0.1, ["mechanical_engineering"], "Economizers and lagged steam lines", False),
    ("photovoltaic_efficiency", "Photovoltaic Efficiency", "power", [2, 3, 4, 5], "power_output", "solar", 0.1, ["photovoltaics"], "Anti-reflective coatings and trackers", False),
    ("blade_aerodynamics", "Blade Aerodynamics", "power", [2, 4, 5], "power_output", "wind", 0.1, ["wind_power"], "Twisted, tapered blade profiles", False),
    ("turbine_superalloys", "Turbine Superalloys", "power", [4, 5, 6], "power_output", "superheated_steam", 0.05, ["steam_turbines"], "Hotter inlet temperatures", False),
    ("combustion_tuning", "Combustion Tuning", "power", [3, 4, 5], "power_output", "fuel_gas", 0.1, ["gas_turbines"], "Lean-burn combustors", False),
    ("market_analytics", "Market Analytics", "logistics", [1, 2, 3, 4, 5], "market_price", None, 0.05, ["conveyor_hubs"], "Price tracking and timed sales", False),
    ("emission_controls", "Emission Controls", "chemistry", [2, 3, 4, 5, 6], "pollution_reduction", None, 0.08, ["air_scrubbing"], "Sealed processes and flare recovery", False),
    ("night_shift", "Night Shift Protocols", "logistics", [1, 3, 5, 6], "offline_efficiency", None, 0.1, ["conveyor_hubs"], "Unattended operation procedures", False),
    ("fortification_doctrine", "Fortification Doctrine", "defense", [2, 3, 4, 5, 6], "defense", None, 0.1, ["field_reporting"], "Layered perimeters and kill zones", True),
    ("ballistic_calibration", "Ballistic Calibration", "defense", [2, 3, 4, 5], "defense", "ballistic", 0.15, ["armor_piercing_rounds"], "Ranging tables and better barrels", True),
    ("explosive_yield", "Explosive Yield", "defense", [3, 4, 5], "defense", "explosive", 0.15, ["blasting_compounds"], "Shaped bursters and better fuzes", True),
    ("incendiary_compounds", "Incendiary Compounds", "defense", [3, 4, 5], "defense", "incendiary", 0.15, ["incendiaries"], "Stickier, hotter gels", True),
    ("beam_focusing", "Beam Focusing", "defense", [4, 5, 6], "defense", "energy", 0.15, ["laser_weapons"], "Adaptive optics on every emitter", True),
    ("module_bays", "Module Bay Expansion", "electronics", [3, 5], "module_slots", None, 1, ["module_engineering_2"], "Extra card cages in every bay", False),
    ("foundry_practice", "Foundry Practice", "metallurgy", [4, 5, 6], "craft_speed", "foundry", 0.1, ["aerospace_alloys"], "Faster pours and quicker mold turnover", False),
    ("arc_metallurgy", "Arc Metallurgy", "metallurgy", [4, 5, 6], "craft_speed", "smelting_advanced", 0.1, ["arc_furnaces"], "Higher-current electrodes", False),
    ("electrode_coatings", "Electrode Coatings", "chemistry", [3, 4, 5], "craft_speed", "electrolysis", 0.1, ["chlor_alkali"], "Low-overpotential electrode coatings", False),
    ("cryogenic_insulation", "Cryogenic Insulation", "chemistry", [4, 5, 6], "craft_speed", "cryogenics", 0.1, ["air_separation"], "Multilayer vacuum insulation", False),
    ("strain_optimization", "Strain Optimization", "biotech", [4, 5, 6], "craft_speed", "bioprocessing", 0.1, ["algae_cultivation"], "Selected high-yield strains", False),
    ("nanofab_precision", "Nanofab Precision", "quantum", [6, 6, 7], "craft_speed", "nanofab", 0.1, ["graphene_synthesis"], "Faster deposition with fewer defects", False),
    ("orbital_logistics", "Orbital Logistics", "aerospace", [7, 7, 7], "craft_speed", "orbital", 0.1, ["ark_structures"], "Tighter launch and assembly cadence", False),
    ("rotor_balancing", "Rotor Balancing", "power", [5, 6], "craft_speed", "centrifuging", 0.1, ["isotope_centrifuges"], "Precision-balanced rotors", False),
    ("crusher_liners", "Crusher Liners", "mining", [1, 3, 5], "craft_speed", "crushing", 0.1, ["quarrying"], "Manganese-steel liners", False),
    ("mixer_impellers", "Mixer Impellers", "manufacturing", [2, 4], "craft_speed", "mixing", 0.1, ["cement_works"], "High-shear impellers", False),
    ("munitions_lines", "Munitions Lines", "defense", [2, 4, 6], "craft_speed", "munitions", 0.1, ["field_reporting"], "Faster press-and-fill lines", True),
    ("precision_tolerances", "Precision Tolerances", "manufacturing", [4, 5, 6], "craft_speed", "precision_assembling", 0.1, ["precision_engineering"], "Metrology-driven assembly", False),
    ("pump_impellers", "Pump Impellers", "mining", [2, 4], "craft_speed", "pumping", 0.1, ["hydraulics"], "Cavitation-free impellers", False),
    ("wellbore_stimulation", "Wellbore Stimulation", "mining", [3, 4, 5], "craft_speed", "oil_extraction", 0.1, ["oil_extraction"], "Acidized and fractured wellbores", False),
    ("sorting_optics", "Sorting Optics", "metallurgy", [2, 4], "craft_speed", "recycling", 0.1, ["scrap_reclamation"], "Optical sorting on the scrap line", False),
    ("neutron_economy", "Neutron Economy", "power", [5, 6], "craft_speed", "fission", 0.1, ["thorium_reactors"], "Better moderators and reflectors", False),
    ("plasma_stability", "Plasma Stability", "power", [6, 7], "craft_speed", "fusion", 0.1, ["fusion_power"], "Real-time instability suppression", False),
    ("feedwater_heating", "Feedwater Heating", "power", [1, 3], "craft_speed", "boiling", 0.1, ["mechanical_engineering"], "Preheated feedwater", False),
]

REPEATABLES = [
    ("deep_mining_survey", "Deep Mining Survey", "mining", ["drill_bit_metallurgy_5", "ark_structures"], [eff("mining_productivity", None, 0.05)]),
    ("research_throughput", "Research Throughput", "research", ["lab_automation_7", "ark_structures"], [eff("lab_speed", None, 0.05)]),
    ("logistics_optimization", "Logistics Optimization", "logistics", ["warehouse_racking_6", "ark_structures"], [eff("storage_capacity", None, 0.1)]),
    ("grid_optimization", "Grid Optimization", "power", ["turbine_superalloys_3", "ark_structures"], [eff("power_output", None, 0.03)]),
    ("market_dominance", "Market Dominance", "logistics", ["market_analytics_5", "ark_structures"], [eff("market_price", None, 0.02)]),
    ("lean_manufacturing", "Lean Manufacturing", "manufacturing", ["assembly_tooling_5", "ark_structures"],
     [eff("craft_speed", "assembling", 0.05), eff("craft_speed", "precision_assembling", 0.05), eff("craft_speed", "electronics", 0.05)]),
    ("planetary_defense_grid", "Planetary Defense Grid", "defense", ["fortification_doctrine_5", "ark_structures"], [eff("defense", None, 0.05)]),
    ("atmospheric_restoration", "Atmospheric Restoration", "chemistry", ["emission_controls_5", "ark_structures"], [eff("pollution_reduction", None, 0.02)]),
    ("nanofab_throughput", "Nanofab Throughput", "quantum", ["nanofab_precision_3"], [eff("craft_speed", "nanofab", 0.05)]),
    ("orbital_cadence", "Orbital Cadence", "aerospace", ["orbital_logistics_3"], [eff("craft_speed", "orbital", 0.05)]),
    ("autonomous_operations", "Autonomous Operations", "logistics", ["night_shift_4", "ark_structures"], [eff("offline_efficiency", None, 0.02)]),
]

CATEGORY_LABEL = {"smelting_advanced": "advanced smelting", "precision_assembling": "precision assembly",
                  "oil_extraction": "well", "bioprocessing": "bioprocess", "nanofab": "nanofab"}


def effect_text(etype, target, value):
    pct = f"{round(value * 100):g}%"
    if etype == "craft_speed":
        return f"+{pct} {CATEGORY_LABEL.get(target, target.replace('_', ' '))} speed."
    return {
        "mining_productivity": f"+{pct} bonus output from all extractors.",
        "lab_speed": f"+{pct} lab research speed.",
        "lab_productivity": f"+{pct} free research per unit.",
        "power_output": f"+{pct} output from {(target or 'all').replace('_', ' ')} generators.",
        "storage_capacity": f"+{pct} storage capacity.",
        "market_price": f"+{pct} market sell prices.",
        "defense": f"+{pct} {(target + ' ') if target else ''}defense rating.",
        "pollution_reduction": f"-{pct} pollution from all buildings.",
        "offline_efficiency": f"+{pct} offline production efficiency.",
        "module_slots": f"+{int(value)} module slot in every bay.",
        "extraction_slots": f"+{int(value)} extractor slot on every claimed {target} deposit.",
    }[etype]


def define():
    for row in UNLOCK_TECHS:
        tid, name, tier, branch, prereqs, units, desc = row[:7]
        fr = len(row) > 7 and row[7] == "fr"
        add_tech(tid, name, desc, tier, branch, prereqs, cost_for(tier, fr), units, TIME[tier])

    for base, name, branch, tiers, etype, target, per, first, flavour, fr in LEVELED:
        prev = None
        for i, tier in enumerate(tiers):
            prereqs = list(first) if prev is None else [prev]
            gate = GATE[tier]
            if gate and gate not in prereqs:
                prereqs.append(gate)
            if fr and "field_reporting" not in prereqs and prev is None:
                prereqs.append("field_reporting")
            same_tier_rank = tiers[:i].count(tier)
            units = int(UNITS[tier] * (1 + 0.3 * same_tier_rank) * (0.8 if tier <= 1 else 1.0))
            tid = f"{base}_{i + 1}"
            add_tech(tid, f"{name} {ROMAN[i]}", f"{flavour}: {effect_text(etype, target, per)}", tier, branch, prereqs,
                     cost_for(tier, fr and tier >= 2), units, TIME[tier], effects=[eff(etype, target, per)])
            prev = tid

    for tid, name, branch, prereqs, effects in REPEATABLES:
        desc = "Repeatable: " + " ".join(effect_text(e["type"], e["target"], e["value"]) for e in effects)
        add_tech(tid, name, desc, 7, branch, prereqs, cost_for(7), 3000, TIME[7], effects=effects, repeatable=True)
