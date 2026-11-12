"""Render item icons (256x256 RGBA product shots, transparent background + soft contact shadow).

blender -b -P art/blender/render_icons.py -- [--ids a,b] [--archetype x[,y]] [--all] [--missing]
        [--samples [--first]] [--quality preview|draft|final] [--size 256] [--sheet]

  --ids / --archetype / --all   select items from data/items.json
  --missing                     skip items whose icon already exists
  --samples                     render representative fake items per archetype (no data needed) into
                                art/render/icons/samples/ + a labelled contact sheet (sheet*.png)
  --first                       with --samples: only the first sample of each archetype
  --sheet                       also build a contact sheet of the rendered items (art/render/icons/)

Output: assets/icons/items/<item_id>.png. Items whose visual archetype is ``building_kit`` or whose id
is a building (data/buildings.json) are skipped - tools/pack_sprites.py makes those icons.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kit_icons as KI  # noqa: E402
import studio  # noqa: E402
from icons import ARCHETYPES, Frame  # noqa: E402

OUT_DIR = os.path.join(studio.ROOT, "assets", "icons", "items")
SAMPLE_DIR = os.path.join(studio.RENDER_DIR, "icons", "samples")
SHEET_DIR = os.path.join(studio.RENDER_DIR, "icons")

DEFAULT_PITCH = 55.0   # 35 deg above the horizon
DEFAULT_YAW = 35.0
DEFAULT_FILL = 0.8

# Representative fake items per archetype: (material, color, params)
SAMPLES = {
    "ore_chunks": [("iron_ore", None, {}), ("copper_ore", None, {}), ("coal", None, {}), ("bauxite", None, {}),
                   ("uranium_glass", None, {}), ("stone", None, {})],
    "powder_pile": [("sulfur", None, {}), ("iron", None, {}), ("sand", None, {})],
    "gravel_pile": [("stone", None, {}), ("limestone", None, {})],
    "crystal_cluster": [("crystal", [0.55, 0.2, 0.9], {}), ("quartz", None, {}), ("salt", None, {})],
    "ingot": [("copper", None, {}), ("steel", None, {}), ("gold", None, {})],
    "plate": [("iron", None, {}), ("aluminum", None, {})],
    "plate_stack": [("steel", None, {}), ("copper", None, {})],
    "sheet_coil": [("steel", None, {}), ("copper", None, {})],
    "rod": [("iron", None, {}), ("copper", None, {})],
    "beam": [("steel", None, {}), ("paint", [0.35, 0.05, 0.02], {})],
    "pipe": [("steel", None, {}), ("copper", None, {})],
    "wire_spool": [("copper", None, {}), ("gold", None, {})],
    "cable_coil": [("rubber", None, {}), ("plastic_color", [0.8, 0.25, 0.02], {})],
    "gear": [("steel", None, {}), ("brass", None, {})],
    "bolts": [("steel", None, {}), ("brass", None, {})],
    "spring": [("steel", None, {}), ("chrome", None, {})],
    "bearing": [("chrome", None, {}), ("steel", None, {})],
    "circuit_board": [("pcb_green", None, {}), ("pcb_blue", None, {}), ("pcb_black", None, {"tier": 4})],
    "chip": [("plastic_black", None, {}), ("ceramic", None, {})],
    "battery": [("paint", [0.05, 0.15, 0.5], {}), ("plastic_black", None, {})],
    "motor": [("paint", [0.05, 0.18, 0.45], {}), ("paint", [0.6, 0.35, 0.02], {})],
    "frame": [("steel", None, {}), ("paint", [0.7, 0.4, 0.02], {})],
    "solar_cell": [("silicon", None, {})],
    "glass_pane": [("glass", None, {})],
    "brick": [("brick_clay", None, {}), ("ceramic", None, {})],
    "block": [("concrete", None, {}), ("graphite", None, {})],
    "pellets": [("plastic_color", [0.1, 0.4, 0.8], {}), ("uranium_glass", None, {})],
    "barrel": [("paint", [0.6, 0.05, 0.02], {}), ("paint", [0.02, 0.12, 0.4], {})],
    "gas_canister": [("paint", [0.05, 0.25, 0.08], {}), ("paint", [0.5, 0.5, 0.52], {})],
    "flask": [("glass", [0.9, 0.1, 0.05], {}), ("glass", [0.1, 0.5, 0.95], {})],
    "crate": [("wood", None, {})],
    "module_card": [("plastic_color", [0.05, 0.3, 0.9], {}), ("plastic_color", [0.9, 0.3, 0.02], {})],
    "magnet": [("paint", [0.7, 0.02, 0.02], {})],
    "lens": [("glass", None, {})],
    "filter": [("steel", None, {})],
    "fuel_rod": [("uranium_glass", None, {}), ("thorium", None, {})],
    "ammo_box": [("paint", [0.09, 0.12, 0.05], {})],
    "shell": [("brass", None, {})],
    "rocket_part": [("plastic_white", None, {})],
    "drone": [("plastic_white", None, {}), ("carbon_fiber", None, {})],
    "servo_arm": [("paint", [0.8, 0.3, 0.01], {})],
    "tank_part": [("paint", [0.6, 0.6, 0.58], {})],
    "fluid_orb": [("glass", [0.05, 0.25, 0.9], {}), ("glass", [0.01, 0.008, 0.005], {"mode": "opaque"}),
                  ("glass", [0.9, 0.85, 0.1], {"gas": True}), ("glass", [0.95, 0.3, 0.02], {"mode": "glow"})],
    "cell": [("glow", [0.2, 0.7, 1.0], {})],
    "log": [("wood", None, {})],
    "bag": [("paint", [0.3, 0.21, 0.1], {})],
    "canister": [("paint", [0.55, 0.05, 0.02], {})],
    "nozzle": [("copper", None, {})],
    "antenna": [("aluminum", None, {})],
    "processor": [("pcb_green", None, {})],
    "capsule": [("stainless", [0.3, 1.0, 0.5], {})],
    "heat_sink": [("aluminum", None, {})],
    "turbine_blade": [("titanium", None, {})],
}


def parse(argv):
    o = {"quality": "draft", "ids": None, "archetype": None, "all": False, "missing": False, "samples": False,
         "first": False, "sheet": False, "size": "256"}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--ids", "--archetype", "--quality", "--size"):
            o[a[2:]] = argv[i + 1]
            i += 2
            continue
        if a.startswith("--") and a[2:] in o:
            o[a[2:]] = True
        i += 1
    return o


def fallback_archetype(item):
    return "fluid_orb" if item.get("kind") == "fluid" else "crate"


def render_icon(item, quality, out_path, size=256):
    vis = item.get("visual") or {}
    arch = vis.get("archetype")
    if arch not in ARCHETYPES:
        fb = fallback_archetype(item)
        print(f"[warn] {item['id']}: archetype '{arch}' not implemented -> {fb}")
        arch = fb
    params = dict(vis.get("params") or {})
    nested = params.pop("params", None)  # tolerate {"params": {"params": {...}}} from content
    if isinstance(nested, dict):
        params.update(nested)
    params.setdefault("tier", item.get("tier", 1))
    t0 = time.time()
    KI.icon_scene(quality)
    studio.shadow_catcher(size=40.0)
    fr = ARCHETYPES[arch](item, vis.get("material"), vis.get("color"), params)
    if not isinstance(fr, Frame):
        r, c = fr[0], fr[1]
        fr = Frame(r, c)
    yaw = fr.yaw if fr.yaw is not None else DEFAULT_YAW
    pitch = fr.pitch if fr.pitch is not None else DEFAULT_PITCH
    cam = studio.product_camera(fr.radius, fr.center, size_px=size, pitch=pitch, yaw=yaw)
    KI.icon_lights(fr.center, fr.radius, yaw - DEFAULT_YAW)
    KI.fit_camera(cam, fr.fill or DEFAULT_FILL, shadow_dir=KI.key_dir(yaw - DEFAULT_YAW))
    t1 = time.time()
    studio.render_to(out_path)
    print(f"[done] {item['id']} ({arch}) build {t1 - t0:.1f}s render {time.time() - t1:.1f}s")
    return True


def building_ids():
    try:
        return {b["id"] for b in studio.load_data("buildings")["buildings"]}
    except (OSError, ValueError, KeyError):
        return set()


def run_samples(o):
    want = set(o["archetype"].split(",")) if o["archetype"] else None
    entries = []
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    for arch, samples in SAMPLES.items():
        if want and arch not in want:
            continue
        if arch not in ARCHETYPES:
            print(f"[todo] {arch}")
            continue
        for k, (mat, col, params) in enumerate(samples[:1] if o["first"] else samples):
            tag = mat + (f"_{k}" if k else "")
            item = {"id": f"sample_{arch}_{tag}", "name": f"{arch} {mat}", "kind": "fluid" if arch == "fluid_orb" else "solid",
                    "tier": params.get("tier", 2),
                    "visual": {"archetype": arch, "material": mat, "color": col, "params": params}}
            path = os.path.join(SAMPLE_DIR, f"{arch}__{tag}.png")
            try:
                render_icon(item, o["quality"], path, int(o["size"]))
                entries.append((path, f"{arch}:{mat}"))
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[fail] {arch} {mat}: {e}")
    name = "sheet" + ("_" + "_".join(sorted(want))[:60] if want else "") + ".png"
    KI.contact_sheet(entries, os.path.join(SAMPLE_DIR, name), cell=128, cols=8)


def main():
    o = parse(studio.cli_args())
    if o["samples"]:
        run_samples(o)
        return
    try:
        items = studio.load_data("items")["items"]
    except OSError:
        print("data/items.json not found - use --samples")
        return
    if o["ids"]:
        want = set(o["ids"].split(","))
        items = [it for it in items if it["id"] in want]
    elif o["archetype"]:
        want = set(o["archetype"].split(","))
        items = [it for it in items if (it.get("visual") or {}).get("archetype") in want]
    elif not o["all"]:
        print("nothing selected (use --ids/--archetype/--all/--samples)")
        return
    bids = building_ids()
    items = [it for it in items if it["id"] not in bids and (it.get("visual") or {}).get("archetype") != "building_kit"]
    if o["missing"]:
        items = [it for it in items if not os.path.exists(os.path.join(OUT_DIR, f"{it['id']}.png"))]
    entries = []
    t0 = time.time()
    for it in items:
        path = os.path.join(OUT_DIR, f"{it['id']}.png")
        try:
            render_icon(it, o["quality"], path, int(o["size"]))
            entries.append((path, it["id"]))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[fail] {it['id']}: {e}")
    if entries:
        print(f"[total] {len(entries)} icons in {time.time() - t0:.0f}s ({(time.time() - t0) / len(entries):.1f}s/icon)")
    if o["sheet"] and entries:
        for k in range(0, len(entries), 96):
            KI.contact_sheet(entries[k:k + 96], os.path.join(SHEET_DIR, f"items_{k // 96:02d}.png"), cell=96, cols=12)


main()
