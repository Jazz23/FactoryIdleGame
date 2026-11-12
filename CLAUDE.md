# INDUSTRIUM — notes for agents

Idle factory game, Godot 4.7 (Compatibility renderer), photoreal isometric sprites rendered from
procedural Blender 5.2 models. Read `README.md`, `docs/DESIGN.md`, `docs/CONTENT_SCHEMA.md`,
`docs/ART_PIPELINE.md` first.

## Ground rules
- Content is data: edit `tools/content/*.py`, then `python3 tools/content/build_content.py`
  (validates + writes `data/*.json`). Never hand-edit `data/*.json`.
- Original IP: no names/recipe trees copied from other factory games.
- Godot scripts: avoid `:=` on Variant expressions (dictionary lookups, untyped returns) — the
  project treats inference-from-Variant as an error. `python3 tools/fix_infer.py <files>` fixes
  them automatically. After adding a new `class_name` script run `godot --headless --import --path .`.
- Static vars holding Callables must be cleared on exit (see `HUD._exit_tree`) or the engine
  crashes at shutdown.
- Never `pkill -f <pattern>` with a pattern that appears in your own command line (it kills your shell); use `pkill -x godot` or a bracket pattern like `pkill -f "[h]ttp.server"`.
- Smoke test of every game system: `godot --headless --path . -- --smoke` (must print SMOKE PASSED).
- Exports: templates for 4.7.2 live in `~/.local/share/godot/export_templates/4.7.2.stable/`; `godot --headless --path . --export-release "Linux" build/linux/Industrium.x86_64`.

## Verifying changes
- Screenshot: `xvfb-run -a -s "-screen 0 1920x1080x24" godot --path . --rendering-driver opengl3 -- --fresh --shot=/path/out.png --frames=60 [--zoom=0.5] [--panel=build|research|...] [--line=N] [--tree] [--intro]`
- Test data: `-- --data=res://tests/fixtures/` loads the tiny fixture set.
- Balance bot: `godot --headless --path . -- --autoplay=HOURS --dt=1.0` (logs progress/stalls).
- Art preview: `blender -b -P art/blender/render_buildings.py -- --ids X --quality preview --frames 1`
  then `.venv/bin/python tools/preview.py out.png art/render/buildings/X/f_00.png`.

## Simulation model (scripts/core/game.gd)
Rate-based lines; two-pass fair sharing of scarce inputs; deposit slots (×5 per listed slot,
fastest extractors first); power with priority circuit (pumping/boiling/fission/fusion/fuel
extraction) + accumulators; logistics throughput caps (priority lines exempt); support coverage
(8 machines per support building); pollution absorption → threat → siege of non-start sectors;
market saturation; contracts; megaprojects (requires_building, rewards); prestige "Legacy";
offline progress (coarse ticks).
