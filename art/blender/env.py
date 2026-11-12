"""Environment renders: seamless isometric floor tile (+ later: decals, deposits, walls).

blender -b -P art/blender/env.py -- [--quality final]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import kit as K  # noqa: E402
import materials as M  # noqa: E402
import studio  # noqa: E402

ASSETS = os.path.join(studio.ROOT, "assets", "env")


def floor_tile(quality, period=8.0, tex="concrete_floor_worn_001", name="floor_tile"):
    """Render a screen-space seamless tile.

    The texture repeats every `period` metres along world X and Y, so in the 2:1 iso view the
    image repeats every period*sqrt(2) horizontally and period*sqrt(2)/2 vertically.
    """
    studio.reset(quality)
    K.reset()
    bpy.ops.mesh.primitive_plane_add(size=period * 6, location=(0, 0, 0))
    plane = bpy.context.object
    plane.data.materials.append(M.scanned(tex, scale=1.0 / period, metallic=0.0, bump=0.4, ao=False, name="floor"))
    right, up, fwd = studio.iso_basis()
    w_m = period * math.sqrt(2)
    w_px = int(round(w_m * studio.PX_PER_M))
    h_px = w_px // 2
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = w_m
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.rotation_euler = Euler((studio.ISO_PITCH, 0, studio.ISO_YAW), "XYZ")
    cam.location = -fwd * 100
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x = w_px
    s.render.resolution_y = h_px
    s.render.film_transparent = False
    studio.render_to(os.path.join(ASSETS, f"{name}.png"))
    print(f"[done] {name} {w_px}x{h_px}")


if __name__ == "__main__":
    args = studio.cli_args()
    q = args[args.index("--quality") + 1] if "--quality" in args else "draft"
    floor_tile(q)
