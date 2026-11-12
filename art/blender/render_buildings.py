"""Render building sprite frames.

blender -b -P art/blender/render_buildings.py -- [--ids a,b] [--archetype x] [--all]
        [--quality preview|draft|final] [--frames N] [--spec '{json}'] [--missing]

Writes art/render/buildings/<id>/f_00.png ... and meta.json. Pack with tools/pack_sprites.py.
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kit  # noqa: E402
import studio  # noqa: E402
from buildings import ARCHETYPES  # noqa: E402


def parse(argv):
    opts = {"quality": "draft", "ids": None, "archetype": None, "all": False, "frames": None,
            "spec": None, "missing": False, "maxframes": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--ids", "--archetype", "--quality", "--frames", "--spec", "--maxframes"):
            opts[a[2:]] = argv[i + 1]
            i += 2
            continue
        if a == "--all":
            opts["all"] = True
        if a == "--missing":
            opts["missing"] = True
        i += 1
    return opts


def render_building(spec, quality, frames_override=None, maxframes=None):
    vis = spec.get("visual", {})
    arch = vis.get("archetype")
    if arch not in ARCHETYPES:
        print(f"[skip] {spec['id']}: archetype '{arch}' not implemented")
        return False
    params = dict(vis.get("params", {}))
    if "color" in vis and "paint" not in params:
        params["paint"] = vis["color"]
    studio.reset(quality)
    kit.reset()
    studio.shadow_catcher()
    t0 = time.time()
    rig = ARCHETYPES[arch](spec, params)
    w, d = spec.get("size", [2, 2])
    pts = studio.footprint_points(w, d, rig.height) + list(rig.extra_points)
    info = studio.frame_iso_camera(pts)
    frames = int(frames_override) if frames_override else rig.frames
    fps = rig.fps
    if maxframes and frames > int(maxframes):
        fps = max(4, round(rig.fps * int(maxframes) / frames))   # keep the loop duration
        frames = int(maxframes)
    out = os.path.join(studio.RENDER_DIR, "buildings", spec["id"])
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"):
            os.remove(os.path.join(out, f))
    for i in range(frames):
        rig.update(i / frames)
        studio.render_to(os.path.join(out, f"f_{i:02d}.png"))
    meta = {
        "id": spec["id"], "archetype": arch, "frames": frames, "fps": fps,
        "frame_w": info["width"], "frame_h": info["height"], "origin": info["origin"],
        "size": [w, d], "height": rig.height,
        "lights": [dict(l, px=studio.world_to_px(l["pos"])) for l in rig.lights],
        "emitters": [dict(e, px=studio.world_to_px(e["pos"])) for e in rig.emitters],
        "quality": quality,
    }
    studio.write_json(os.path.join(out, "meta.json"), meta)
    print(f"[done] {spec['id']} ({arch}) {frames}f {info['width']}x{info['height']} in {time.time() - t0:.1f}s")
    return True


def main():
    o = parse(studio.cli_args())
    if o["spec"]:
        specs = [json.loads(o["spec"])]
    else:
        specs = studio.load_data("buildings")["buildings"]
        if o["ids"]:
            want = set(o["ids"].split(","))
            specs = [s for s in specs if s["id"] in want]
        elif o["archetype"]:
            specs = [s for s in specs if s.get("visual", {}).get("archetype") == o["archetype"]]
        elif not o["all"]:
            print("nothing selected (use --ids/--archetype/--all/--spec)")
            return
        if o["missing"]:
            specs = [s for s in specs if not os.path.exists(os.path.join(studio.RENDER_DIR, "buildings", s["id"], "meta.json"))]
    for s in specs:
        render_building(s, o["quality"], o["frames"], o["maxframes"])


main()
