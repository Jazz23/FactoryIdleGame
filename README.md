# Industrium

An idle megafactory game with photoreal, pre-rendered isometric art. Grow an abandoned lot into
a planet-spanning industrial complex and launch the **Orbital Ark**.

- **Content scale:** 339 items (26 fluids), 345 recipes, 129 buildings, 351 technologies,
  19 frontier sectors, 13 threats, 65 contracts, 77 achievements and 4 megaprojects
  (see `docs/CONTENT_STATS.md`).
- **Systems:** rate-based production lines; electricity with a priority circuit, accumulators,
  solar day/night and wind; burner fuel; logistics throughput; modules; support relays; a market
  with saturation; contracts; pollution → threat → defense with ammunition; sector claims for
  deposit slots; megaprojects and prestige ("Legacy"); offline progress; achievements.
- **Tools in game:** production planner (click any item → plan → *Build missing*), line upgrades,
  tech tree (G), advisor hints.

## Running

Requires Godot **4.7** (Compatibility renderer).

```
godot --path .            # play
godot -e --path .         # open in the editor
```

To export, install the 4.7 export templates and use the presets in `export_presets.cfg`
(Linux, Windows, Web): `godot --headless --path . --export-release "Linux" build/linux/Industrium.x86_64`.

## Controls

Drag with any mouse button (or WASD / arrows) to pan, mouse wheel to zoom, click a bay to inspect it.
Hotkeys: **F** factory · **B** build · **R** research · **G** tech tree · **M** market ·
**C** contracts · **T** frontier · **P** power · **I** storage · **Esc** close.

## Project layout

| path | what |
|---|---|
| `scripts/core/` | autoloads: `content.gd` (data), `game.gd` (simulation, save/offline), `sound.gd`; `planner.gd`, `prod_line.gd` |
| `scripts/world/` | isometric factory floor, machine sprites, particles, shaders |
| `scripts/ui/` | HUD, panels, tech tree, advisor |
| `data/*.json` | generated content — edit `tools/content/*.py` and run `python3 tools/content/build_content.py` |
| `art/blender/` | procedural Blender models + render scripts (see `docs/ART_PIPELINE.md`) |
| `assets/` | rendered sprites, icons, floor, fonts, audio |
| `tests/` | `autoplay.gd` balance bot, fixtures |

## Regenerating assets

```
python3 tools/fetch_assets.py                                  # CC0 textures/HDRIs (Poly Haven, ambientCG)
blender -b -P art/blender/render_buildings.py -- --all --quality draft
blender -b -P art/blender/render_icons.py -- --all --quality draft
blender -b -P art/blender/render_deposits.py -- --all
blender -b -P art/blender/env.py -- --quality final
.venv/bin/python tools/pack_sprites.py
.venv/bin/python tools/gen_audio.py                            # then convert to .ogg with ffmpeg
```

## Balance testing

```
godot --headless --path . -- --autoplay=20 --dt=1.0
```
runs a greedy bot for 20 simulated hours and logs research progress, power, logistics, threat and stalls.

## Credits

Textures & HDRIs: Poly Haven, ambientCG (CC0). Fonts: Barlow / Barlow Condensed (SIL OFL).
Audio: procedurally synthesised (`tools/gen_audio.py`).
