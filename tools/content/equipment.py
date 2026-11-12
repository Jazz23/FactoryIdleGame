"""Modules (speed / efficiency / productivity / emission families x Mk I-V) and ammunition."""
from common import V, add_item, add_recipe

ROMAN = ["I", "II", "III", "IV", "V"]

# Shared module core per Mk level: (tier, unlock tech, base inputs)
MODULE_CORE = [
    (2, "module_engineering", {"circuit_board": 5, "capacitor": 5}),
    (3, "module_engineering_2", {"control_board": 3}),
    (4, "module_engineering_3", {"embedded_controller": 2}),
    (5, "module_engineering_4", {"flight_computer": 1, "embedded_controller": 1}),
    (6, "module_engineering_5", {"quantum_processor": 1}),
]

# family id, display name, colour, desc, per-level extra inputs, per-level effects
MODULE_FAMILIES = [
    ("overclock_card", "Overclock Card", (0.2, 0.45, 0.95),
     "Pushes machines past their rated speed at a steep power cost.",
     [{"electric_motor": 1}, {"insulated_cable": 4}, {"heat_sink": 2}, {"brushless_motor": 1}, {"superconductor_tape": 2}],
     [dict(speed=s, energy=e, productivity=0.0, pollution=p) for s, e, p in
      [(0.15, 0.4, 0.05), (0.25, 0.5, 0.06), (0.35, 0.6, 0.07), (0.45, 0.7, 0.08), (0.6, 0.8, 0.1)]]),
    ("economizer_card", "Economizer Card", (0.25, 0.8, 0.35),
     "Trims idle draw and tunes motors for lower power use.",
     [{"copper_wire": 8}, {"battery_cell": 1}, {"lithium_cell": 1}, {"rare_earth_magnet": 2}, {"graphene": 2}],
     [dict(speed=0.0, energy=e, productivity=0.0, pollution=p) for e, p in
      [(-0.2, -0.02), (-0.3, -0.03), (-0.4, -0.04), (-0.5, -0.05), (-0.6, -0.06)]]),
    ("yield_optimizer", "Yield Optimizer", (0.95, 0.65, 0.15),
     "Recovers waste in-process for bonus output, slowing the line.",
     [{"gearbox": 2}, {"plastic_sheet": 4}, {"microchip": 6}, {"gyroscope": 1}, {"metamaterial_lattice": 1}],
     [dict(speed=s, energy=e, productivity=pr, pollution=p) for pr, s, e, p in
      [(0.03, -0.05, 0.4, 0.05), (0.05, -0.08, 0.5, 0.06), (0.07, -0.1, 0.6, 0.07), (0.1, -0.12, 0.7, 0.08),
       (0.14, -0.15, 0.8, 0.1)]]),
    ("emission_filter", "Emission Filter", (0.85, 0.92, 0.9),
     "Inline catalytic filter that cuts a machine's emissions.",
     [{"coke": 4}, {"filter_cartridge": 2}, {"alumina": 4}, {"rare_earth_oxide": 4}, {"carbon_nanotube": 2}],
     [dict(speed=0.0, energy=e, productivity=0.0, pollution=p) for p, e in
      [(-0.15, 0.1), (-0.25, 0.1), (-0.35, 0.15), (-0.45, 0.15), (-0.6, 0.2)]]),
]

# id, name, tier, unlock, class, mult, archetype, material, colour, desc, recipe(cat, time, inputs, amount)
AMMO = [
    ("scrap_shot", "Scrap Shot", 1, "munitions", "ballistic", 0.6, "ammo_box", "iron", None,
     "Crude canister shot packed with rolling-mill scrap.", ("munitions", 2, {"scrap_metal": 2, "coal": 1}, 2)),
    ("steel_core_rounds", "Steel-Core Rounds", 1, "munitions", "ballistic", 1.0, "ammo_box", "brass", None,
     "Standard belted rounds for sentry guns.", ("munitions", 3, {"steel_plate": 1, "copper_sheet": 1, "coal": 1}, 2)),
    ("ap_rounds", "Armor-Piercing Rounds", 2, "armor_piercing_rounds", "ballistic", 1.6, "ammo_box", "bronze", (0.6, 0.2, 0.15),
     "Hardened-tip rounds that punch through salvaged plating.",
     ("munitions", 4, {"steel_ingot": 1, "bronze_ingot": 1, "coke": 1}, 2)),
    ("frag_shell", "Fragmentation Shell", 3, "blasting_compounds", "explosive", 1.0, "shell", "steel", None,
     "Notched-casing mortar shell that shreds swarms.", ("munitions", 6, {"steel_plate": 2, "blasting_powder": 2})),
    ("incendiary_canister", "Incendiary Canister", 3, "incendiaries", "incendiary", 1.0, "canister", "paint", (0.75, 0.2, 0.1),
     "Gelled naphtha charge for flame projectors.", ("munitions", 5, {"naphtha": 20, "rubber": 1, "steel_plate": 1})),
    ("he_shell", "High-Explosive Shell", 4, "high_explosives", "explosive", 1.8, "shell", "steel", (0.55, 0.55, 0.3),
     "Thin-walled shell with a nitrated burster.", ("munitions", 8, {"steel_plate": 2, "high_explosive": 2, "copper_sheet": 1})),
    ("thermite_charge", "Thermite Charge", 4, "thermite", "incendiary", 1.8, "canister", "aluminum", (0.7, 0.35, 0.25),
     "Aluminum-oxide charge that burns through armor.",
     ("munitions", 6, {"aluminum_powder": 2, "iron_ore": 2, "plastic_sheet": 1})),
    ("capacitor_pack", "Capacitor Pack", 4, "laser_weapons", "energy", 1.0, "cell", "steel", (0.2, 0.6, 0.9),
     "Fast-discharge pack that fires pulse lasers.", ("electronics", 6, {"capacitor": 8, "battery_cell": 1, "aluminum_sheet": 1})),
    ("tungsten_rounds", "Tungsten Penetrators", 5, "tungsten_penetrators", "ballistic", 2.5, "ammo_box", "tungsten", None,
     "Carbide-cored rounds for heavy autocannons.", ("munitions", 6, {"tungsten_carbide": 1, "steel_plate": 1, "copper_sheet": 1}, 2)),
    ("smart_shell", "Guided Shell", 5, "guided_munitions", "explosive", 3.0, "shell", "titanium", (0.5, 0.55, 0.6),
     "Course-correcting shell with a strapdown seeker.", ("munitions", 10, {"he_shell": 1, "embedded_controller": 1, "gyroscope": 1})),
    ("pyro_gel_cell", "Pyrophoric Gel Cell", 5, "pyrophorics", "incendiary", 2.8, "canister", "titanium", (0.9, 0.5, 0.1),
     "Self-igniting kerosene gel for thermal lances.",
     ("munitions", 8, {"rocket_kerosene": 20, "aluminum_powder": 2, "titanium_plate": 1})),
    ("lithium_charge_pack", "Lithium Charge Pack", 5, "lithium_charge_packs", "energy", 1.8, "cell", "lithium", (0.3, 0.8, 0.9),
     "Dense rechargeable pack for beam weapons.", ("electronics", 8, {"lithium_cell": 2, "heat_sink": 1})),
    ("supercap_cell", "Graphene Supercapacitor", 6, "supercapacitors", "energy", 3.0, "cell", "graphite", (0.4, 0.9, 1.0),
     "Graphene-electrode cell that dumps megajoules instantly.",
     ("electronics", 10, {"graphene": 2, "lithium_cell": 1, "superconductor_tape": 1})),
    ("hypervelocity_slug", "Hypervelocity Slug", 6, "interceptor_drones", "ballistic", 4.0, "ammo_box", "tungsten", (0.3, 0.3, 0.4),
     "Nanotube-sabot carbide slug for interceptors and rails.",
     ("munitions", 8, {"tungsten_carbide": 2, "carbon_nanotube": 1}, 3)),
]


def define():
    for fam, fname, color, desc, extras, effects in MODULE_FAMILIES:
        for lvl in range(5):
            tier, unlock, core = MODULE_CORE[lvl]
            iid = f"{fam}_{lvl + 1}"
            name = f"{fname} Mk {ROMAN[lvl]}"
            add_item(iid, name, "components", tier, V("module_card", ["pcb_green", "pcb_blue", "pcb_black", "pcb_red", "pcb_black"][lvl], color,
                                                     tier=lvl + 1), desc, module=dict(effects[lvl]))
            inputs = dict(core)
            for k, v in extras[lvl].items():
                inputs[k] = inputs.get(k, 0) + v
            add_recipe(iid, name, "electronics", 10 + 5 * lvl, inputs, {iid: 1}, unlock)

    for iid, name, tier, unlock, cls, mult, arch, mat, color, desc, rec in AMMO:
        add_item(iid, name, "defense", tier, V(arch, mat, color), desc, ammo={"class": cls, "mult": mult})
        cat, time, inputs = rec[:3]
        n = rec[3] if len(rec) > 3 else 1
        add_recipe(iid, name, cat, time, inputs, {iid: n}, unlock)
