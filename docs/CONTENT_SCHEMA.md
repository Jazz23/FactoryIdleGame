# Content schema

All game content is data. `tools/content/build_content.py` (Python, stdlib only) is the single
source of truth: it defines content in Python, derives balance numbers (item values), validates
everything, and writes the JSON files in `data/` that both Godot and the Blender render
pipeline read. **Never hand-edit `data/*.json`.**

```
python3 tools/content/build_content.py      # writes data/*.json, prints stats, exits non-zero on error
```

Units: time = seconds, power = kW, energy = kJ, fluids = units (1 unit ≈ 1 L), money = credits (¢).
IDs are `snake_case`, unique across their file. Display names are Title Case English.

## data/items.json — `{"items": [Item, ...]}`

| field | type | notes |
|---|---|---|
| id | str | |
| name | str | |
| desc | str | one short flavour/usage sentence |
| kind | `"solid"` \| `"fluid"` | |
| group | str | UI tab, one of GROUPS below |
| tier | int 0–7 | progression tier (0 = raw starting resources) |
| value | float | derived market price per unit (¢), computed by the build script |
| fuel_kj | float, optional | if set, item can be burned in burner buildings / generators |
| fuel_class | `"chemical"` \| `"nuclear"` \| `"fusion"`, optional | |
| pollution_mult | float, optional | |
| visual | Visual | how the icon is rendered (see below) |

GROUPS: `raw`, `materials`, `intermediates`, `components`, `fluids`, `research`, `logistics`,
`production`, `power`, `defense`, `megaproject`.

## data/recipes.json — `{"recipes": [Recipe, ...]}`

| field | type | notes |
|---|---|---|
| id | str | |
| name | str | |
| category | str | one of CATEGORIES; selects which buildings can run it |
| time | float | seconds per craft at speed 1.0 |
| inputs | `{item_id: amount}` | may be empty for extraction |
| outputs | `{item_id: amount}` | ≥1 entry |
| unlocked_by | str \| null | tech id; null = available from start |
| deposit | str, optional | extraction recipes only: the resource deposit type consumed (`iron_ore`, `crude_oil`, …) |

CATEGORIES: `mining`, `pumping` (water/brine/gas wells), `oil_extraction`, `smelting`, `crushing`,
`pressing`, `assembling`, `precision_assembling`, `electronics`, `chemistry`, `refining`,
`mixing`, `electrolysis`, `centrifuging`, `cryogenics`, `foundry` (molten metal casting),
`bioprocessing`, `nanofab`, `orbital` (megaproject assembly), `munitions`,
`boiling` (water → steam in boilers), `fission` (reactors: fuel + water → hot steam),
`fusion`, `smelting_advanced`, `recycling`.
Research is not a recipe category: labs consume research items directly (see techs).

## data/buildings.json — `{"buildings": [Building, ...]}`

| field | type | notes |
|---|---|---|
| id | str | also an item id: every building is an item that recipes produce |
| name, desc | str | |
| role | str | `producer` (runs recipes), `generator` (makes power), `storage`, `research`, `logistics`, `defense`, `support` (beacon-like / pollution scrubber / etc.), `megaproject` |
| categories | [str] | recipe categories it can run (producer) |
| speed | float | crafting speed multiplier |
| power_kw | float | electric draw while working (0 for burner) |
| burner | bool | consumes fuel items instead of electricity |
| fuel_kw | float | burner fuel consumption (kJ per s) while working |
| power_out_kw | float | generators only |
| generator | object, generators only | one of `{"fuel_class": "chemical", "fuel_kw": 1800}` (burns fuel items; power_out = fuel_kw × efficiency), `{"fluid": "steam", "rate": 30}` (consumes fluid units/s at full output), `{"source": "solar"\|"wind"\|"geothermal"\|"tidal"}` (free, variable). Generators throttle to demand. |
| capacity_kj | float, optional | accumulators: energy stored |
| module_slots | int | |
| pollution | float | pollution per minute while working |
| storage_slots | int, optional | storage role: capacity added (units per item type) |
| defense | float, optional | defense role: defense rating added |
| support | object, optional | e.g. `{"speed_bonus": 0.25, "range": "bay"}` |
| size | [w, d] | footprint in tiles (1 tile = 1 m) — drives sprite size |
| tier | int 0–7 | |
| unlocked_by | str \| null | |
| visual | Visual | |

Every building id MUST also appear in items.json (group `production`/`power`/`logistics`/`defense`/…)
with a recipe that crafts it (category `assembling` etc.).

## data/modules — modules are ordinary items with an extra block

Item field `module: {"speed": 0.2, "energy": 0.5, "productivity": 0.0, "pollution": 0.1}` (fractions; negative allowed).

## data/techs.json — `{"techs": [Tech, ...]}`

| field | type | notes |
|---|---|---|
| id, name, desc | str | |
| prereqs | [tech_id] | |
| cost | `{research_item_id: amount}` | consumed by labs |
| time | float | lab-seconds per research unit |
| units | int | number of research units (total cost = cost × units) |
| unlocks | [recipe_id] | recipes unlocked (buildings are unlocked via their recipe) |
| effects | [Effect] | permanent bonuses |
| tier | int | |
| repeatable | bool | infinite tech; cost scales ×1.5 per level |

Effect: `{"type": T, "target": category_or_item_or_null, "value": float}` with T one of
`craft_speed` (target = recipe category), `mining_productivity`, `lab_speed`, `lab_productivity`,
`power_output` (target = generator_fuel), `storage_capacity`, `market_price`, `defense`,
`pollution_reduction`, `offline_efficiency`, `module_slots`, `extraction_slots`.

## data/world.json

`{"deposits": [...], "sectors": [...], "threats": [...], "contracts": [...], "achievements": [...], "megaprojects": [...]}`

- **deposit**: `{id, name, item, kind: "solid"|"fluid", visual}` — resource nodes.
- **sector**: `{id, name, desc, tier, claim_cost: {item: n}, defense_required, deposits: {deposit_id: slots}, threat}` — Frontier map regions, unlocked in order; slots = max extractors on that deposit.
- **threat**: `{id, name, desc, strength, appears_at_pollution}` — original hostile machines/weather.
- **contract**: `{id, name, tier, requires: {item: n}, reward_credits, reward_items: {}}`.
- **achievement**: `{id, name, desc, condition: {type, target, value}}`.
- **megaproject**: `{id, name, desc, stages: [{name, requires: {item: n}}], reward}` — endgame / prestige.

## Visual

Shared by items, buildings and deposits. Consumed by the Blender pipeline (`art/blender/`).

```json
{"archetype": "ingot", "material": "copper", "color": [r, g, b] (0-1, optional tint), "params": {}}
```

Item icon archetypes (each a procedural Blender model):
`ore_chunks`, `powder_pile`, `gravel_pile`, `crystal_cluster`, `ingot`, `plate`, `plate_stack`,
`sheet_coil`, `rod`, `beam`, `pipe`, `wire_spool`, `cable_coil`, `gear`, `bolts`, `spring`,
`bearing`, `circuit_board`, `chip`, `battery`, `motor`, `frame`, `solar_cell`, `glass_pane`,
`brick`, `block`, `pellets`, `barrel`, `gas_canister`, `flask`, `crate`, `module_card`,
`magnet`, `lens`, `filter`, `fuel_rod`, `ammo_box`, `shell`, `rocket_part`, `drone`,
`servo_arm`, `tank_part`, `fluid_orb`, `cell` (power cell), `log` (wood), `bag` (sack),
`canister`, `nozzle`, `antenna`, `processor`, `capsule`, `heat_sink`, `turbine_blade`,
`building_kit` (crated building, used for building items — params.building = building id).

Materials (shared library): `iron`, `steel`, `stainless`, `copper`, `brass`, `bronze`, `tin`,
`aluminum`, `titanium`, `gold`, `silver`, `lead`, `tungsten`, `chrome`, `cast_iron`,
`iron_ore`, `copper_ore`, `coal`, `stone`, `limestone`, `sand`, `quartz`, `bauxite`,
`ilmenite`, `monazite`, `sulfur`, `salt`, `lithium`, `graphite`, `silicon`, `glass`,
`concrete`, `brick_clay`, `rubber`, `plastic_white`, `plastic_black`, `plastic_color`
(uses color), `carbon_fiber`, `ceramic`, `wood`, `pcb_green`, `pcb_blue`, `pcb_red`,
`pcb_black`, `paint` (uses color), `glow` (emissive, uses color), `uranium_glass`
(emissive green), `thorium`, `crystal` (uses color).

Building archetypes (each a procedural Blender model, animated loop):
`drill` (mining), `pumpjack`, `water_pump`, `gas_well`, `burner_furnace`, `electric_furnace`,
`arc_furnace`, `crusher`, `press`, `rolling_mill`, `wire_drawer`, `assembler`, `precision_assembler`,
`electronics_fab`, `chemical_plant`, `refinery`, `mixer`, `electrolyzer`, `centrifuge`,
`cryo_plant`, `foundry`, `bioreactor`, `nanofab`, `lab`, `boiler`, `steam_engine`,
`steam_turbine`, `solar_array`, `wind_turbine`, `accumulator`, `gas_turbine`, `reactor`,
`heat_exchanger`, `cooling_tower`, `fusion_reactor`, `geothermal_plant`, `storage_tank`,
`warehouse`, `silo`, `conveyor_hub`, `rail_depot`, `drone_port`, `beacon`, `scrubber`,
`turret`, `wall_segment`, `radar`, `shield_generator`, `launch_pad`, `orbital_assembler`,
`substation`, `munitions_plant`.

Building `params`: `{"tier": 1-4 (detail/paint level), "paint": [r,g,b], "accent": [r,g,b], "glow": [r,g,b] (optional emissive), "smoke": bool, "variant": str}`.

## Asset path conventions (produced by the art pipeline, consumed by Godot)

- Item icon: `assets/icons/items/<item_id>.png` (256×256, transparent).
- Building sheet: `assets/buildings/<building_id>.png` + `assets/buildings/<building_id>.json`
  `{"frames": N, "columns": C, "frame_w": W, "frame_h": H, "fps": F, "origin": [x, y]}`
  where origin = pixel of the footprint centre on the ground inside a frame.
- Deposit sprite: `assets/env/deposit_<deposit_id>.png`.

Godot falls back to a generated placeholder when a file is missing, so content and art can progress independently.

## Defense fields

Defense buildings (`role: "defense"`) always carry all three fields:

| field | type | notes |
|---|---|---|
| defense | float | defense rating this building adds while supplied (walls/radar/shields: always) |
| ammo | `"ballistic"` \| `"explosive"` \| `"incendiary"` \| `"energy"` \| null | ammo class it consumes; null = needs no ammo (walls, radar, shield domes) |
| ammo_per_min | float | ammo items consumed per minute per building while the frontier is under threat (0 when `ammo` is null) |

Ammo items carry `ammo: {"class": <ammo class>, "mult": float}`. A turret's effective rating is
`defense × mult` of the best ammo of its class in storage (player can pin one); with no ammo of its
class it contributes 0. Powered turrets/shields (`power_kw > 0`) are also scaled by `power_sat`.
`defense` tech effects multiply ratings: `target` null = all defense, or an ammo class.
