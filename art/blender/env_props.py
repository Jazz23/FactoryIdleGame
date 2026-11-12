"""Environment props and floor decals scattered through the factory aisles.

blender -b -P art/blender/env_props.py -- [--quality draft] [--only name,name]

Writes assets/env/prop_<name>.png + .json ({"origin": [x, y], "size": [w, d]}) and
assets/env/decal_<name>.png + .json.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import kit as K  # noqa: E402
import materials as M  # noqa: E402
import studio  # noqa: E402

OUT = os.path.join(studio.ROOT, "assets", "env")


def _wood():
    m = bpy.data.materials.new("wood")
    m.use_nodes = True
    t = M.NT(m)
    p = t.bsdf()
    vec = t.coords(1.0)
    wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    t.link(vec, wv.inputs["Vector"])
    wv.inputs["Scale"].default_value = 18.0
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    g = t.maprange(wv.outputs["Factor"], 0.0, 1.0, 0.0, 1.0)
    col = t.mix_color(g, (0.42, 0.27, 0.13), (0.28, 0.16, 0.07))
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.12), 0.9, clamp=True), col, (0.05, 0.035, 0.02))
    t.link(col, p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.8
    return m


def _cardboard():
    m = bpy.data.materials.new("cardboard")
    m.use_nodes = True
    t = M.NT(m)
    p = t.bsdf()
    vec = t.coords(1.0)
    n = t.noise(vec, 30.0, 4, 0.5)
    col = t.mix_color(t.maprange(n, 0.3, 0.7), (0.5, 0.33, 0.17), (0.42, 0.27, 0.13))
    t.link(col, p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.85
    return m


def pallet(seed=1):
    rnd = random.Random(seed)
    wood = _wood()
    out = []
    for x in (-0.5, 0.0, 0.5):
        out.append(K.box((0.1, 1.0, 0.1), (x, 0, 0.0), wood, bevel=0.006, base=True))
    for y in (-0.42, -0.21, 0.0, 0.21, 0.42):
        out.append(K.box((1.2, 0.14, 0.025), (0, y, 0.1), wood, bevel=0.003, base=True))
    box = _cardboard()
    tape = M.plastic((0.6, 0.45, 0.2), 0.4)
    z = 0.125
    for layer in range(rnd.randint(2, 3)):
        for ix in (-0.29, 0.29):
            for iy in (-0.24, 0.24):
                if rnd.random() < 0.1 and layer > 0:
                    continue
                h = 0.3
                b = K.box((0.56, 0.46, h), (ix + rnd.uniform(-0.01, 0.01), iy, z), box, bevel=0.008, base=True)
                b.rotation_euler = (0, 0, rnd.uniform(-0.03, 0.03))
                K.box((0.57, 0.06, 0.004), (ix, iy, z + h), tape, bevel=0, base=True)
        z += 0.3
    return z + 0.1, (1.2, 1.0)


def drums(seed=2):
    rnd = random.Random(seed)
    cols = [(0.03, 0.12, 0.35), (0.35, 0.04, 0.03), (0.05, 0.06, 0.06), (0.4, 0.28, 0.02)]
    pos = [(-0.32, -0.32), (0.32, -0.3), (-0.3, 0.33), (0.34, 0.34)]
    for i, (x, y) in enumerate(pos):
        if i == 3 and rnd.random() < 0.5:
            continue
        mat = M.painted(rnd.choice(cols), wear=0.5, grime=0.7, rust=0.35, name="drum")
        K.cyl(0.29, 0.88, (x, y, 0), mat, verts=40, bevel=0.01)
        for z in (0.29, 0.59):
            K.torus(0.292, 0.012, (x, y, z), mat)
        K.cyl(0.04, 0.02, (x + 0.12, y + 0.08, 0.88), M.metal("steel"), verts=16)
    return 0.95, (1.4, 1.4)


def gas_cage(seed=3):
    frame = M.painted((0.7, 0.42, 0.02), wear=0.6, grime=0.6, name="cage")
    w, d, h = 1.4, 0.8, 1.7
    for x in (-w / 2, w / 2):
        for y in (-d / 2, d / 2):
            K.box((0.05, 0.05, h), (x, y, 0), frame, bevel=0.005, base=True)
    for z in (0.05, h * 0.5, h):
        K.box((w, 0.04, 0.04), (0, -d / 2, z), frame, bevel=0.004)
        K.box((w, 0.04, 0.04), (0, d / 2, z), frame, bevel=0.004)
        K.box((0.04, d, 0.04), (-w / 2, 0, z), frame, bevel=0.004)
        K.box((0.04, d, 0.04), (w / 2, 0, z), frame, bevel=0.004)
    mesh = M.metal("dark_steel", dirt=0.5)
    for i in range(15):
        x = -w / 2 + (i + 0.5) * w / 15
        K.cyl(0.006, h - 0.1, (x, -d / 2, 0.05), mesh, verts=6, bevel=0)
    cols = [(0.02, 0.25, 0.06), (0.6, 0.6, 0.6), (0.02, 0.02, 0.02), (0.45, 0.02, 0.02), (0.02, 0.1, 0.4)]
    rnd = random.Random(seed)
    for i in range(5):
        x = -0.5 + i * 0.25
        c = rnd.choice(cols)
        mat = M.painted(c, wear=0.3, grime=0.4, rough=0.35, name="cyl")
        K.cyl(0.11, 1.25, (x, 0.05, 0.05), mat, verts=32)
        K.sphere(0.11, (x, 0.05, 1.3), mat, scale=(1, 1, 0.6))
        K.cyl(0.035, 0.12, (x, 0.05, 1.36), M.metal("brass"), verts=16)
    return h + 0.1, (w, d)


def forklift(seed=4):
    body = M.painted((0.75, 0.42, 0.01), wear=0.45, grime=0.6, rust=0.15, name="forklift")
    dark = M.painted((0.03, 0.03, 0.03), wear=0.3, grime=0.5, name="fl_dark")
    tyre = M.rubber()
    K.box((1.0, 1.9, 0.55), (0, 0.1, 0.25), body, bevel=0.06, base=True)
    K.box((0.95, 0.6, 0.45), (0, 0.75, 0.55), dark, bevel=0.08, base=True)    # counterweight
    K.box((0.5, 0.5, 0.08), (0, 0.15, 0.8), M.plastic((0.04, 0.04, 0.04), 0.7), bevel=0.03, base=True)  # seat
    K.box((0.45, 0.08, 0.45), (0, 0.38, 0.85), M.plastic((0.04, 0.04, 0.04), 0.7), bevel=0.03, base=True)
    for x in (-0.45, 0.45):
        for y in (-0.6, 0.45):
            K.box((0.05, 0.05, 1.3), (x, y, 0.8), dark, bevel=0.01, base=True)
    K.box((0.98, 1.15, 0.05), (0, -0.07, 2.1), dark, bevel=0.01, base=True)
    for x in (-0.3, 0.3):
        K.box((0.1, 0.1, 2.1), (x, -0.9, 0.05), dark, bevel=0.01, base=True)     # mast
    K.box((0.85, 0.06, 0.45), (0, -0.98, 0.15), dark, bevel=0.01, base=True)
    for x in (-0.25, 0.25):
        K.box((0.12, 1.1, 0.04), (x, -1.55, 0.06), M.metal("dark_steel", dirt=0.6), bevel=0.005, base=True)
    for x in (-0.5, 0.5):
        for y in (-0.55, 0.7):
            K.cyl(0.25, 0.22, (x, y, 0.25), tyre, rot=K.AXES["x"], verts=32, base=False, bevel=0.03)
    K.cyl(0.18, 0.04, (0, 0.05, 1.15), dark, rot=(math.radians(40), 0, 0), verts=24)
    K.beacon((0.35, 0.5, 2.15), (1.0, 0.55, 0.05), on=True)
    return 2.3, (1.2, 3.0)


def toolcart(seed=5):
    red = M.painted((0.45, 0.02, 0.015), wear=0.35, grime=0.45, rough=0.35, name="toolcart")
    K.box((0.8, 0.5, 0.95), (0, 0, 0.1), red, bevel=0.02, base=True)
    for i in range(5):
        z = 0.2 + i * 0.16
        K.box((0.72, 0.01, 0.12), (0, -0.255, z), red, bevel=0.003, base=True)
        K.box((0.3, 0.02, 0.015), (0, -0.27, z + 0.08), M.metal("chrome"), bevel=0.003, base=True)
    K.box((0.84, 0.54, 0.03), (0, 0, 1.05), M.rubber(), bevel=0.01, base=True)
    for x in (-0.33, 0.33):
        for y in (-0.18, 0.18):
            K.cyl(0.05, 0.04, (x, y, 0.05), M.rubber(), rot=K.AXES["x"], verts=16, base=False)
    K.box((0.15, 0.1, 0.08), (0.2, 0.05, 1.07), M.metal("steel"), bevel=0.01, base=True)
    return 1.2, (0.9, 0.6)


def bollards(seed=6):
    m = M.painted((0.75, 0.45, 0.01), wear=0.7, grime=0.6, rust=0.3, name="bollard")
    for x in (-0.6, 0.0, 0.6):
        K.cyl(0.08, 1.0, (x, 0, 0), m, verts=24)
        K.cyl(0.085, 0.06, (x, 0, 0.8), M.hazard(8), verts=24)
    K.tube([(-0.6, 0, 0.75), (0.6, 0, 0.75)], 0.04, m)
    return 1.1, (1.4, 0.3)


PROPS = {"pallet": pallet, "drums": drums, "gas_cage": gas_cage, "forklift": forklift,
         "toolcart": toolcart, "bollards": bollards}


def render_prop(name, fn, quality):
    studio.reset(quality)
    K.reset()
    studio.shadow_catcher()
    h, (w, d) = fn()
    info = studio.frame_iso_camera(studio.footprint_points(w, d, h), margin_px=8)
    path = os.path.join(OUT, f"prop_{name}.png")
    studio.render_to(path)
    studio.write_json(os.path.join(OUT, f"prop_{name}.json"), {"origin": info["origin"], "size": [w, d]})
    print("[done] prop", name)


# --------------------------------------------------------------------------- decals
def decal(kind, quality, seed=0):
    studio.reset(quality)
    K.reset()
    size = 3.0
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0.002))
    pl = bpy.context.object
    m = bpy.data.materials.new("decal")
    m.use_nodes = True
    t = M.NT(m)
    p = t.bsdf()
    vec = t.coords(1.0)
    # radial falloff * noise -> alpha
    tc = t.node("ShaderNodeTexCoord")
    grad = t.node("ShaderNodeTexGradient", gradient_type="SPHERICAL")
    mp = t.node("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / (size * 0.48), 1.0 / (size * 0.36), 1)
    t.link(tc.outputs["Object"], mp.inputs["Vector"])
    t.link(mp.outputs["Vector"], grad.inputs["Vector"])
    n = t.noise(t.coords(1.2 + seed * 0.1), 1.6, 8, 0.65, 0.6)
    shape = t.math("MULTIPLY", grad.outputs["Factor"], t.maprange(n, 0.35, 0.7, 0.2, 1.6))
    if kind == "oil":
        alpha = t.maprange(shape, 0.2, 0.6, 0.0, 0.5)
        p.inputs["Base Color"].default_value = (0.02, 0.017, 0.012, 1)
        p.inputs["Roughness"].default_value = 0.12
        p.inputs["Coat Weight"].default_value = 0.6
    elif kind == "puddle":
        alpha = t.maprange(shape, 0.3, 0.42, 0.0, 0.5)
        p.inputs["Base Color"].default_value = (0.09, 0.095, 0.1, 1)
        p.inputs["Roughness"].default_value = 0.03
        p.inputs["Metallic"].default_value = 0.0
        p.inputs["Specular IOR Level"].default_value = 0.8
    elif kind == "rust":
        alpha = t.maprange(shape, 0.15, 0.6, 0.0, 0.38)
        p.inputs["Base Color"].default_value = (0.11, 0.045, 0.018, 1)
        p.inputs["Roughness"].default_value = 0.9
    else:  # soot / tyre grime
        alpha = t.maprange(shape, 0.1, 0.6, 0.0, 0.35)
        p.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
        p.inputs["Roughness"].default_value = 0.8
    t.link(alpha, p.inputs["Alpha"])
    pl.data.materials.append(m)
    info = studio.frame_iso_camera(studio.footprint_points(size, size, 0.0), margin_px=2, extra_shadow=False)
    path = os.path.join(OUT, f"decal_{kind}_{seed}.png")
    studio.render_to(path)
    studio.write_json(os.path.join(OUT, f"decal_{kind}_{seed}.json"), {"origin": info["origin"]})
    print("[done] decal", kind, seed)


def drain(quality):
    studio.reset(quality)
    K.reset()
    studio.shadow_catcher()
    K.box((0.6, 0.6, 0.01), (0, 0, 0), M.metal("cast_iron", dirt=0.9), bevel=0.01, base=True)
    for i in range(7):
        K.box((0.04, 0.5, 0.012), (-0.24 + i * 0.08, 0, 0.004), M.plastic((0.005, 0.005, 0.005), 0.9), bevel=0, base=True)
    info = studio.frame_iso_camera(studio.footprint_points(0.6, 0.6, 0.02), margin_px=4, extra_shadow=False)
    studio.render_to(os.path.join(OUT, "decal_drain_0.png"))
    studio.write_json(os.path.join(OUT, "decal_drain_0.json"), {"origin": info["origin"]})


if __name__ == "__main__":
    args = studio.cli_args()
    q = args[args.index("--quality") + 1] if "--quality" in args else "draft"
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
    for name, fn in PROPS.items():
        if only is None or name in only:
            render_prop(name, fn, q)
    if only is None or "decals" in only:
        for kind in ("oil", "puddle", "rust", "grime"):
            for sd in (0, 1):
                decal(kind, q, sd)
        drain(q)
