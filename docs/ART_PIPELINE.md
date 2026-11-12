# Art pipeline (Blender 5.2 Cycles → sprites)

Everything is procedural Python run headless: `blender -b -P <script> -- <args>`.
Source PBR scans/HDRIs: `python3 tools/fetch_assets.py` (→ `art/source/`, git-ignored, CC0).
Machine: 4 CPU cores, no GPU, ~4 GB free RAM → keep test renders small (`--quality preview`, `--frames 1`).

## Modules (`art/blender/`)
- `studio.py` — scene reset (Cycles, AgX, HDRI + key sun), `shadow_catcher()`, iso camera framing
  (`frame_iso_camera`), `product_camera` (icons), `render_to`, `world_to_px`, `load_data`.
- `materials.py` — PBR library. **Colours are LINEAR RGB** (0.03 = near-black paint, 0.2 = mid grey,
  0.6 = light grey; saturated industrial yellow ≈ (0.75, 0.42, 0.02)). Main factories:
  `painted(color, wear, grime, rough, under, rust)` (the workhorse: chipped edges, scratches,
  drip streaks, cavity grime, rust), `metal(kind)` (`METALS` table), `scanned(tex_id)`,
  `concrete`, `rubber`, `plastic`, `glass`, `emissive`, `molten`, `hazard`, `tread_plate`,
  `rusty`, `screen`, `from_spec(material_name, color)` (schema material → bpy material).
- `kit.py` — primitives at real size (`box`, `cyl`, `sphere`, `torus`, `tube`, `prism`, `ibeam`,
  `pivot`, `attach`) and parts (`skid`, `hazard_edge`, `control_cabinet`, `motor`, `fan`,
  `chimney`, `beacon`, `ladder`, `railing`, `tank`, `vent_grille`, `pipe_run`, `flange`, `bolts`,
  `rivet_strip`, `scatter_debris`). Add new reusable parts here (keep them generic).
- `buildings/` — archetype modules, each exporting `ARCHETYPES = {name: build_fn}`;
  `build_fn(spec, params) -> Rig` (see `buildings/__init__.py`). Reference: `buildings/smelting.py`.
- `render_buildings.py` — CLI: `--ids a,b | --archetype x | --all | --spec '{json}'`,
  `--quality preview|draft|final`, `--frames N`, `--missing`.
- `env.py` — floor tile and other environment renders.

## Conventions for building models
- Footprint `spec["size"] = [w, d]` metres, centred on the origin, ground z = 0. Stay inside it
  (small overhangs ok). Heights: 1×1 ≈ ≤1.5 m, 3×3 ≈ 2–4 m, 5×5 up to ~7 m (chimneys/towers may go higher).
- Camera looks toward −X/+Y. **Visible faces are −Y (screen-left, brightly lit) and +X
  (screen-right, shaded).** Put doors, displays, glowing openings, nameplates, ladders on those.
  Tall parts go toward the back (+Y / −X) so they don't hide the machine.
- Realism checklist: bevels everywhere (kit does it), real-world proportions, layered detail
  (base skid/plinth → main body → secondary parts → small details: bolts, cables, gauges,
  warning labels, beacons), weathering appropriate to tier (tier 1 rusty/grimy, tier 4 clean,
  painted, glossy), at least one emissive status element, no floating parts.
- Tier styling via params: tier 1 dark/worn/rusty, tier 2 industrial yellow/green paint,
  tier 3 blue/grey clean, tier 4+ white/graphite high-tech with emissive accents.
  `params.paint` / `params.accent` / `params.glow` override colours.
- Animation: `Rig(frames=12..16, fps=8..15, update=fn(t))` – rotate pivots, move pistons, flicker
  emission. t ∈ [0,1) must loop seamlessly (use whole numbers of rotations / sin(2πt·k)).
  Static buildings: frames=1. Prefer rotational symmetry (a 7-blade fan only needs 1/7 turn per loop).
- Export Godot hints in the Rig: `lights=[{pos, color, energy, flicker}]` for glows,
  `emitters=[{pos, type}]` (`smoke`, `steam`, `sparks`, `fire`) at chimney tops / vents.
- Render budget: final quality ~5–20 s per frame. Keep frames ≤ 16.

## Workflow
```
blender -b -P art/blender/render_buildings.py -- --ids <id> --quality preview --frames 1
.venv/bin/python tools/preview.py /tmp/.../out.png art/render/buildings/<id>/f_00.png --scale 1.5
# look at out.png (Read tool), iterate, then:
blender -b -P art/blender/render_buildings.py -- --ids <id> --quality final
.venv/bin/python tools/pack_sprites.py <id>
```
