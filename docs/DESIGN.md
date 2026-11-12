# INDUSTRIUM — design

An idle factory game rendered with photoreal pre-rendered isometric sprites (Blender Cycles →
sprite sheets → Godot 2D). Content scale target: comparable to a full-size factory-builder
(200+ items/fluids, 200+ recipes, 100+ buildings, ~190 technologies), but with an **original**
item tree, names, tech tree, enemies and endgame. Do not copy names or recipe trees from any
existing game.

## Premise

A derelict industrial frontier. You start with a handful of burner drills and a stone furnace on
an abandoned lot and grow it into a planet-scale industrial complex that finally assembles the
**Orbital Ark** megaproject (prestige → "Legacy").

## Core simulation (rate based, idle friendly)

- **Global storage.** All items live in one warehouse inventory. Each item has a cap
  (`base_cap` + storage buildings + techs). Fluids have their own tank cap.
- **Production groups.** The player builds N copies of building B and assigns recipe R
  (R.category ∈ B.categories). A group crafts `N × B.speed × (1 + bonuses) × power_sat / R.time`
  crafts/s, limited by input availability and output space. Groups appear as "bays" on the
  isometric factory floor.
- **Extraction** recipes (`mining`, `pumping`, `oil_extraction`) need deposit slots. Slots come
  from claimed **sectors** (+ `extraction_slots` techs).
- **Burner** buildings consume fuel items (best available chemical fuel, player can pin one).
- **Power.** Demand = Σ working electric buildings. Supply = generators (throttle to demand, so
  fuel/steam use ∝ load). `power_sat = min(1, supply / demand)` slows every electric building.
  Accumulators buffer surplus/deficit. Solar follows a day/night cycle (10 min day).
  Chains: boiler (water+fuel → steam) → steam engine; reactor (fuel rods + water → hot steam)
  → steam turbine; gas turbine burns gas fluid; solar / wind / geothermal are free but limited.
- **Modules** fit into module slots per group (applies to every building in the group).
- **Research.** Labs consume research items (tiered data items, e.g. *Blueprint Sheets*,
  *Circuit Schematics* …) to progress the active tech. Techs unlock recipes and give bonuses.
  Repeatable techs at the end of the tree.
- **Market.** Sell any item for its derived value (price drops with saturation and recovers
  over time). Buy items at 1.6× value (only tiers ≤ unlocked tier) — the bootstrap / unblock path.
- **Contracts.** Rotating orders (deliver X of item) for credit + item rewards.
- **Pollution & Frontier.** Pollution raises **threat** (original hostile machines and storms).
  Defense buildings + consumed ammo items give a defense rating. Sectors whose defense is below
  threat are *under siege*: their extractors stop. Claiming new sectors costs items and needs
  a minimum defense.
- **Offline progress.** On load, simulate elapsed time in coarse steps (cap 8 h base, techs extend).
- **Prestige.** Completing the Orbital Ark awards Legacy points (from lifetime production) that
  give permanent multipliers; the factory resets.
- **Achievements** for milestones.

## Visual pipeline

- Projection: true isometric-dimetric 2:1 — orthographic camera, pitch 60° from vertical,
  yaw 45°. 1 tile = 1 m = 128 px wide diamond at sprite scale 1.0.
- Lighting: HDRI (industrial interior) + warm key sun from screen top-left + Cycles shadow
  catcher → shadows baked into sprite alpha. AgX view transform.
- Buildings: animated loop sheets (12–16 frames). Items: 256 px icons (separate 3/4 product
  shot camera). Floor: seamless rendered concrete tile.
- Godot adds: particles (smoke, steam, sparks), Light2D glows, conveyor item flow, glow/bloom,
  colour grade, vignette.

## Code layout

- `tools/content/build_content.py` — content source of truth → `data/*.json`.
- `art/blender/` — Blender python: `studio.py` (shared scene/camera/light/materials),
  `icons.py`, `buildings.py`, `env.py`. Renders → `art/render/` → packed into `assets/`.
- `scripts/` — Godot GDScript. `scripts/core/` autoloads (Content, Game, Sim, Save),
  `scripts/ui/`, `scripts/world/`.
- `scenes/` — Godot scenes.

See `docs/CONTENT_SCHEMA.md` for the data contract.
