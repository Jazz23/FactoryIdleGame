"""Render resource-deposit ground patches (isometric, same camera / light as buildings).

blender -b -P art/blender/render_deposits.py -- [--ids a,b] [--all] [--missing] [--samples]
        [--quality preview|draft|final]

Reads data/world.json ``deposits`` ({id, name, item, kind, visual}) and writes
assets/env/deposit_<id>.png (transparent, soft alpha edge, baked shadows) and
assets/env/deposit_<id>.json {"origin": [x, y], "size": [w, h], "style": ..., "emitters": [...]} where
origin is the pixel of the patch centre (world origin) and emitters are optional Godot particle hints.
--samples renders a fake deposit per style into art/render/icons/deposits/ with a contact sheet.

Styles (picked from visual.archetype / kind / ids): ore_field, rubble, sand_bar, crystal_outcrop,
fumarole, water_pool, oil_seep, brine_flat, gas_vent.
"""
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Vector, noise  # noqa: E402

import kit as K  # noqa: E402
import kit_icons as KI  # noqa: E402
import materials as M  # noqa: E402
import studio  # noqa: E402

OUT_DIR = os.path.join(studio.ROOT, "assets", "env")
SAMPLE_DIR = os.path.join(studio.RENDER_DIR, "icons", "deposits")
R_PATCH = 2.0          # patch radius (m) -> ~4 x 4 m
SOIL = (0.11, 0.075, 0.05)

SAMPLES = [
    {"id": "s_iron", "name": "Iron Ore Seam", "item": "iron_ore", "kind": "solid",
     "visual": {"archetype": "ore_chunks", "material": "iron_ore"}},
    {"id": "s_coal", "name": "Coal Seam", "item": "coal", "kind": "solid", "visual": {"archetype": "ore_chunks", "material": "coal"}},
    {"id": "s_stone", "name": "Rubble", "item": "stone", "kind": "solid", "visual": {"archetype": "gravel_pile", "material": "stone"}},
    {"id": "s_sand", "name": "Sandbar", "item": "quartz_sand", "kind": "solid", "visual": {"archetype": "powder_pile", "material": "sand"}},
    {"id": "s_sulfur", "name": "Sulfur Fumarole", "item": "native_sulfur", "kind": "solid",
     "visual": {"archetype": "crystal_cluster", "material": "sulfur"}},
    {"id": "s_water", "name": "Freshwater", "item": "water", "kind": "fluid", "visual": {"color": [0.25, 0.45, 0.75]}},
    {"id": "s_oil", "name": "Crude Oil", "item": "crude_oil", "kind": "fluid", "visual": {"color": [0.08, 0.07, 0.06]}},
    {"id": "s_brine", "name": "Brine", "item": "brine", "kind": "fluid", "visual": {"color": [0.55, 0.7, 0.72]}},
    {"id": "s_gas", "name": "Gas Pocket", "item": "natural_gas", "kind": "fluid", "visual": {"color": [0.9, 0.75, 0.2]}},
]


# =========================================================================== style selection
def style_of(d):
    v = d.get("visual") or {}
    if v.get("params", {}).get("style"):
        return v["params"]["style"]
    arch, mat = v.get("archetype"), v.get("material")
    key = f"{d.get('id', '')} {d.get('item', '')}".lower()
    if d.get("kind") == "fluid":
        if "oil" in key or "tar" in key or "bitumen" in key:
            return "oil_seep"
        if "brine" in key or "salt" in key or "lithium" in key:
            return "brine_flat"
        if "gas" in key or "helium" in key or "steam" in key or arch == "gas_canister":
            return "gas_vent"
        return "water_pool"
    if mat == "sulfur" or "sulfur" in key:
        return "fumarole"
    if arch == "crystal_cluster":
        return "crystal_outcrop"
    if arch == "powder_pile" or mat == "sand":
        return "sand_bar"
    if arch == "gravel_pile":
        return "rubble"
    return "ore_field"


# =========================================================================== materials
def _edge_alpha(t, p, R=R_PATCH, inner=0.62):
    """Soft, ragged radial alpha falloff (object space, patch centred on origin)."""
    tc = t.node("ShaderNodeTexCoord")
    sep = KI._sep(t, tc.outputs["Object"])
    r = t.math("SQRT", t.math("ADD", t.math("MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                              t.math("MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
    n = t.noise(tc.outputs["Object"], 0.9, 6, 0.6)
    n2 = t.noise(tc.outputs["Object"], 6.0, 4, 0.6)
    rr = t.math("ADD", r, t.math("ADD", t.math("MULTIPLY", n, 0.7), t.math("MULTIPLY", n2, 0.12)))
    a = t.maprange(rr, R * 1.33, R * (inner + 0.33), interp="SMOOTHSTEP")
    KI._set(p, "Alpha", a)
    return a


def soil(color=SOIL, tint=None, tint_amt=0.0, gravel=0.6, wet=0.3, crust=None, crust_amt=0.0, name="soil"):
    """Ground: dirt with pebble specks, damp patches, optional mineral tint / crust, soft alpha edge."""
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    n1 = t.noise(vec, 0.7, 6, 0.6)
    n2 = t.noise(vec, 3.5, 8, 0.65)
    base = color
    col = t.mix_color(t.maprange(n1, 0.3, 0.7), base, tuple(c * 0.55 for c in base))
    if tint:
        col = t.mix_color(t.maprange(t.noise(vec, 1.2, 6, 0.6, 0.6), 0.35, 0.65, 0.0, tint_amt), col, tint)
    peb = KI._voronoi(t, vec, 38.0)
    pm = t.maprange(peb, 0.12, 0.05, 0.0, gravel)
    pcol = t.mix_color(t.maprange(t.noise(vec, 40.0, 2), 0.3, 0.7), (0.2, 0.19, 0.17), (0.08, 0.075, 0.07))
    col = t.mix_color(pm, col, pcol)
    damp = t.maprange(n2, 0.55, 0.75, 0.0, wet)
    col = t.mix_color(damp, col, tuple(c * 0.45 for c in base))
    rough = t.mix_float(damp, 0.95, 0.55)
    if crust:
        cm = t.maprange(t.noise(vec, 2.0, 6, 0.6, 0.4), 0.55 - 0.25 * crust_amt, 0.62 - 0.25 * crust_amt)
        col = t.mix_color(cm, col, crust)
        rough = t.mix_float(cm, rough, 0.8)
    KI._set(p, "Base Color", col)
    KI._set(p, "Roughness", rough)
    _edge_alpha(t, p)
    h = t.math("ADD", t.math("MULTIPLY", pm, 0.6), t.math("MULTIPLY", t.noise(vec, 25.0, 6), 0.4))
    t.link(t.bump(h, 0.5, 0.01), p.inputs["Normal"])
    return m


def salt_crust(name="salt_crust"):
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    cells = KI._voronoi(t, vec, 2.2, feature="DISTANCE_TO_EDGE")
    ridge = t.maprange(cells, 0.0, 0.05)
    n = t.noise(vec, 5.0, 6, 0.6)
    col = t.mix_color(t.maprange(n, 0.3, 0.7), (0.78, 0.76, 0.72), (0.55, 0.52, 0.48))
    col = t.mix_color(t.math("SUBTRACT", 1.0, ridge), col, (0.95, 0.94, 0.92))
    col = t.mix_color(t.maprange(t.noise(vec, 0.8, 4), 0.6, 0.75, 0.0, 0.6), col, (0.35, 0.27, 0.2))
    KI._set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = 0.75
    _edge_alpha(t, p)
    t.link(t.bump(t.math("ADD", t.math("SUBTRACT", 1.0, ridge), t.math("MULTIPLY", t.noise(vec, 40, 4), 0.3)), 0.6, 0.01),
           p.inputs["Normal"])
    return m


def sand(color=(0.45, 0.33, 0.18), streak=None, name="sand"):
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    t.link(vec, wv.inputs["Vector"])
    wv.inputs["Scale"].default_value = 9.0
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 3.0
    n = t.noise(vec, 1.0, 6, 0.6)
    col = t.mix_color(t.maprange(n, 0.3, 0.7), color, tuple(c * 0.7 for c in color))
    if streak:
        col = t.mix_color(t.maprange(t.noise(_stretch3(t, vec, (0.6, 3.0, 1.0)), 1.5, 6, 0.6, 1.0), 0.55, 0.68), col, streak)
    g = KI._voronoi(t, vec, 120.0)
    col = t.mix_color(t.maprange(g, 0.0, 0.5, 0.25, 0.0), col, tuple(c * 0.5 for c in color))
    KI._set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = 0.9
    _edge_alpha(t, p)
    t.link(t.bump(t.math("ADD", wv.outputs["Factor"], t.math("MULTIPLY", g, 0.5)), 0.35, 0.01), p.inputs["Normal"])
    return m


def _stretch3(t, vec, k):
    n = t.node("ShaderNodeVectorMath", operation="MULTIPLY")
    n.inputs[1].default_value = tuple(k)
    t.link(vec, n.inputs[0])
    return n.outputs["Vector"]


def water(color=(0.25, 0.45, 0.75)):
    m, t = M._new("water")
    p = t.bsdf()
    vec = t.coords(1.0)
    c = KI.lin(color)
    deep = tuple(x * 0.12 for x in c)
    KI._set(p, "Base Color", deep)
    p.inputs["Roughness"].default_value = 0.03
    p.inputs["IOR"].default_value = 1.33
    p.inputs["Specular IOR Level"].default_value = 0.6
    p.inputs["Coat Weight"].default_value = 0.5
    p.inputs["Subsurface Weight"].default_value = 0.0
    rip = t.noise(_stretch3(t, vec, (1.0, 2.5, 1.0)), 3.0, 4, 0.5)
    t.link(t.bump(rip, 0.15, 0.01), p.inputs["Normal"])
    _edge_alpha(t, p)
    return m


def oil():
    m, t = M._new("oil")
    p = t.bsdf()
    vec = t.coords(1.0)
    p.inputs["Base Color"].default_value = (0.006, 0.005, 0.004, 1)
    p.inputs["Roughness"].default_value = 0.04
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.02
    KI._set(p, "Thin Film Thickness", t.maprange(t.noise(vec, 2.0, 4, 0.6, 1.5), 0.3, 0.8, 0.0, 650.0))
    p.inputs["Thin Film IOR"].default_value = 1.45
    t.link(t.bump(t.noise(vec, 4.0, 3, 0.5), 0.08, 0.01), p.inputs["Normal"])
    _edge_alpha(t, p)
    return m


# =========================================================================== geometry
def terrain(height_fn, mat, R=R_PATCH * 1.35, rings=70, segs=180, name="terrain"):
    """Polar-grid ground disc (radius R) with z = height_fn(x, y)."""
    bm = bmesh.new()
    centre = bm.verts.new((0, 0, height_fn(0.0, 0.0)))
    grid = []
    for i in range(1, rings + 1):
        u = (i / rings) ** 1.15
        row = []
        for j in range(segs):
            a = math.tau * j / segs
            x, y = R * u * math.cos(a), R * u * math.sin(a)
            row.append(bm.verts.new((x, y, height_fn(x, y))))
        grid.append(row)
    for j in range(segs):
        bm.faces.new((centre, grid[0][j], grid[0][(j + 1) % segs]))
    for A, B in zip(grid, grid[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((A[j], B[j], B[k], A[k]))
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    K.collection().objects.link(o)
    me.materials.append(mat)
    o.visible_shadow = False  # the faded rim must not darken the shadow catcher below
    return o


def envelope(x, y, R=R_PATCH):
    r = math.hypot(x, y) / R
    return max(0.0, 1.0 - max(0.0, r - 0.45) / 0.65) ** 2


def undulate(x, y, seed, amp=0.035):
    o = Vector((seed % 97, seed % 89, 0))
    return amp * noise.fractal(Vector((x * 0.9, y * 0.9, 0)) + o, 0.6, 2.0, 4) * envelope(x, y)


def scatter_rocks(mat, seed, n_big, n_small, R=R_PATCH * 0.85, big=(0.14, 0.36), small=(0.03, 0.08), sink=0.4, cluster=0.0,
                  hfn=None, squash=(1.0, 0.9, 0.7), cuts=8):
    rnd = random.Random(seed)
    pts = []
    for k in range(n_big):
        r = rnd.uniform(*big) * (1.2 if k == 0 else 1.0)
        a = rnd.uniform(0, math.tau)
        d = 0.0 if k == 0 else math.sqrt(rnd.random()) * R * (1 - cluster * 0.6)
        x, y = d * math.cos(a), d * math.sin(a)
        o = KI.rock_mesh(r, seed + k * 13, cuts=cuts, subdiv=4, bump=0.15, squash=squash, mat=mat, detail=0.05)
        o.rotation_euler = Euler((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, math.tau)), "XYZ")
        o.location = (x, y, 0)
        KI.ground([o])
        h = o.dimensions.z
        o.location.z += (hfn(x, y) if hfn else 0.0) - h * sink
        pts.append((x, y, o.location.z + h))
    protos = [KI.rock_mesh(1.0, seed + 500 + i, cuts=6, subdiv=2, bump=0.2, squash=(1, 1, 0.6), mat=mat) for i in range(5)]
    for pr in protos:
        pr.location = (0, 0, -20)
        pr.hide_render = True
    for k in range(n_small):
        a = rnd.uniform(0, math.tau)
        d = math.sqrt(rnd.random()) * R * 1.05
        x, y = d * math.cos(a), d * math.sin(a)
        s = rnd.uniform(*small) * (0.6 + 0.4 * envelope(x, y))
        z = (hfn(x, y) if hfn else 0.0) + s * 0.25
        KI.dup(protos[k % len(protos)], (x, y, z), (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)), s)
    return pts


def crack_depth(x, y, path, width=0.06, depth=0.08):
    """V-trench depth along a polyline crack."""
    best = 1e9
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + dx * u, ay + dy * u
        best = min(best, math.hypot(x - px, y - py))
    return -depth * max(0.0, 1 - best / width) ** 1.5, best


# =========================================================================== styles
def build(d):
    """Build the patch for deposit `d`; returns (style, points for framing, emitters)."""
    v = d.get("visual") or {}
    mat_name = v.get("material") or d.get("item")
    color = v.get("color")
    seed = KI.seed_of(d["id"])
    style = style_of(d)
    emitters = []
    pts = [(x * R_PATCH, y * R_PATCH, 0.0) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    def flat(x, y):
        return undulate(x, y, seed)

    if style == "ore_field":
        rock = KI.surf(mat_name, color, scale=1.6)
        tint = KI.base_color(mat_name, color)
        terrain(flat, soil(SOIL, tint=tint, tint_amt=0.55, gravel=0.5, wet=0.25))
        pts += scatter_rocks(rock, seed, 9, 140, cluster=0.3, hfn=flat)
    elif style == "rubble":
        rock = KI.surf(mat_name, color, scale=1.6)
        tint = KI.base_color(mat_name, color)

        def hf(x, y):
            h = flat(x, y)
            for cx, cy, r, hh in ((0.3, 0.2, 0.9, 0.22), (-0.6, -0.4, 0.6, 0.12)):
                u = math.hypot(x - cx, y - cy) / r
                if u < 1:
                    h += hh * (1 - u * u) ** 1.5
            return h
        terrain(hf, soil(tuple(c * 0.8 for c in SOIL), tint=tint, tint_amt=0.7, gravel=0.9, wet=0.15))
        pts += scatter_rocks(rock, seed, 14, 260, big=(0.08, 0.22), small=(0.03, 0.09), sink=0.25, hfn=hf)
    elif style == "sand_bar":
        sc = KI.base_color(mat_name, color)
        streak = (0.06, 0.05, 0.045) if mat_name == "monazite" else None

        def hf(x, y):
            o = Vector((seed % 31, seed % 17, 0))
            dune = 0.16 * max(0.0, noise.fractal(Vector((x * 0.55, y * 0.8, 0)) + o, 0.7, 2.0, 3) + 0.35)
            return (dune + undulate(x, y, seed, 0.02)) * envelope(x, y)
        terrain(hf, sand(sc if mat_name != "monazite" else (0.42, 0.3, 0.14), streak))
        pts += scatter_rocks(KI.surf("stone", None, scale=1.6), seed, 3, 40, big=(0.08, 0.16), small=(0.02, 0.05), sink=0.5,
                             hfn=hf)
        pts.append((0, 0, 0.3))
    elif style in ("crystal_outcrop", "fumarole"):
        sulfur = style == "fumarole"
        crust_c = (0.75, 0.58, 0.04) if sulfur else (0.6, 0.6, 0.58)
        path = [(-1.1, -0.5), (-0.3, -0.1), (0.2, 0.15), (1.0, 0.55)] if sulfur else [(-0.6, -0.8), (0.0, 0.0), (0.7, 0.6)]

        def hf(x, y):
            dd, _ = crack_depth(x, y, path, 0.09, 0.1) if sulfur else (0.0, 0)
            return flat(x, y) + dd * envelope(x, y) + (0.06 * math.exp(-(x * x + y * y) / 0.5) if sulfur else 0.0)
        terrain(hf, soil((0.09, 0.075, 0.06), tint=crust_c, tint_amt=0.6, gravel=0.4, wet=0.1, crust=crust_c,
                         crust_amt=0.8 if sulfur else 0.3))
        rock = KI.surf("stone", None, scale=1.6) if sulfur else KI.rock(base=(0.07, 0.065, 0.06), base2=(0.03, 0.03, 0.03),
                                                                         vein=(0.7, 0.68, 0.62), vein_amt=0.4, speck=(0.2, 0.2, 0.2),
                                                                         speck_amt=0.5, rough=0.7, scale=1.6, name="host_rock")
        pts += scatter_rocks(rock, seed, 6 if sulfur else 8, 90, cluster=0.5, hfn=hf, sink=0.45)
        if sulfur:
            cmat = KI.surf("sulfur", None, scale=4.0)
        else:
            c = KI.lin(color) if color else (0.16, 0.16, 0.18)
            cmat = M.metal("dark_steel", rough=0.25, tint=tuple(min(1.0, x / 0.16) for x in c), dirt=0.2)
        rnd = random.Random(seed + 3)
        clusters = [(0.0, 0.0), (0.7, -0.3), (-0.6, 0.4), (0.3, 0.7), (-0.4, -0.6)]
        for cx, cy in clusters:
            for k in range(rnd.randint(5, 9)):
                L = rnd.uniform(0.08, 0.25) * (0.7 if sulfur else 1.0)
                r = L * (0.22 if sulfur else 0.12)
                prof = [(0, -0.05), (r, -0.05), (r, L - r * 1.8), (r * 0.15, L), (0, L)]
                o = KI.lathe(prof, cmat, segs=6 if sulfur else 4, name="crystal", smooth=20)
                x, y = cx + rnd.uniform(-0.12, 0.12), cy + rnd.uniform(-0.12, 0.12)
                o.rotation_euler = (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, 6))
                o.location = (x, y, hf(x, y) - 0.01)
                if not sulfur:
                    o.scale = (1.0, 0.35, 1.0)
                pts.append((x, y, L))
        if sulfur:
            for vx, vy in ((-0.3, -0.1), (0.25, 0.17)):
                K.torus(0.09, 0.035, (vx, vy, hf(vx, vy) + 0.01), KI.surf("sulfur", None, scale=4.0), segs=32, rsegs=10)
                K.cyl(0.075, 0.02, (vx, vy, hf(vx, vy) - 0.005), M.plastic((0.01, 0.008, 0.006), 0.9), verts=32, bevel=0)
                emitters.append({"pos": [vx, vy, 0.05], "type": "steam"})
    elif style in ("water_pool", "oil_seep", "brine_flat"):
        level = -0.03
        if style == "water_pool":
            def hf(x, y):
                r = math.hypot(x * 1.0, y * 1.25)
                bowl = -0.16 * max(0.0, 1 - (r / 1.25) ** 2)
                return flat(x, y) + bowl + 0.03 * noise.noise(Vector((x * 2, y * 2, 3.0)))
            gm = soil((0.075, 0.06, 0.045), tint=(0.05, 0.07, 0.03), tint_amt=0.6, gravel=0.6, wet=0.7)
            liquid = water(color or (0.25, 0.45, 0.75))
        elif style == "oil_seep":
            o = Vector((seed % 41, seed % 23, 0))

            def hf(x, y):
                pud = 0.09 * noise.fractal(Vector((x * 0.9, y * 0.9, 0)) + o, 0.6, 2.0, 3)
                bowl = -0.06 * math.exp(-(x * x + y * y) / 0.9)
                return (flat(x, y) + pud + bowl) * envelope(x, y) + 0.004
            gm = soil((0.05, 0.04, 0.032), tint=(0.012, 0.01, 0.009), tint_amt=0.8, gravel=0.4, wet=0.9)
            liquid = oil()
        else:
            o = Vector((seed % 41, seed % 23, 0))

            def hf(x, y):
                pud = 0.06 * noise.fractal(Vector((x * 1.1, y * 1.1, 0)) + o, 0.6, 2.0, 3)
                return (flat(x, y) * 0.5 + pud - 0.025 * math.exp(-(x * x + y * y) / 1.2)) * envelope(x, y) + 0.005
            gm = salt_crust()
            liquid = water(color or (0.55, 0.7, 0.72))
        terrain(hf, gm)
        wm = bpy.data.meshes.new("liquid")
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, radius=R_PATCH * 1.3, segments=96)
        bm.to_mesh(wm)
        bm.free()
        wo = bpy.data.objects.new("liquid", wm)
        K.collection().objects.link(wo)
        wo.location.z = level
        wm.materials.append(liquid)
        stone = KI.surf("stone", None, scale=1.6)
        if style == "water_pool":
            pts += scatter_rocks(stone, seed, 7, 60, R=R_PATCH * 0.95, big=(0.1, 0.25), sink=0.45, hfn=hf)
        elif style == "oil_seep":
            pts += scatter_rocks(KI.rock(base=(0.05, 0.045, 0.04), base2=(0.02, 0.018, 0.016), speck=(0.1, 0.1, 0.1),
                                         speck_amt=0.4, rough=0.35, scale=1.6, glossy=True, name="tar_rock"),
                                 seed, 4, 40, big=(0.08, 0.18), sink=0.5, hfn=hf)
            emitters.append({"pos": [0.0, 0.0, 0.0], "type": "bubbles"})
    elif style == "gas_vent":
        cc = KI.lin(color) if color else (0.8, 0.7, 0.3)
        crust_c = tuple(0.25 + 0.6 * x for x in cc)
        path = [(-1.2, 0.4), (-0.5, 0.1), (0.1, 0.05), (0.6, -0.3), (1.2, -0.5)]
        path2 = [(0.1, 0.05), (0.3, 0.6), (0.2, 1.1)]

        def hf(x, y):
            d1, _ = crack_depth(x, y, path, 0.11, 0.14)
            d2, _ = crack_depth(x, y, path2, 0.07, 0.08)
            mound = 0.05 * math.exp(-((x - 0.1) ** 2 + (y - 0.05) ** 2) / 0.6)
            return flat(x, y) + (min(d1, d2) + mound) * envelope(x, y)
        terrain(hf, soil((0.085, 0.075, 0.065), tint=crust_c, tint_amt=0.5, gravel=0.5, wet=0.05, crust=crust_c, crust_amt=0.6))
        pts += scatter_rocks(KI.surf("stone", None, scale=1.6), seed, 6, 90, cluster=0.2, sink=0.4, hfn=hf)
        crust = KI.rock(base=crust_c, base2=tuple(x * 0.6 for x in crust_c), speck=(0.9, 0.9, 0.85), speck_amt=0.5, rough=0.85,
                        scale=3.0, name="vent_crust")
        for vx, vy in ((0.1, 0.05), (-0.5, 0.1), (0.6, -0.3)):
            K.torus(0.1, 0.045, (vx, vy, hf(vx, vy) + 0.02), crust, segs=32, rsegs=10)
            K.cyl(0.08, 0.02, (vx, vy, hf(vx, vy) - 0.01), M.plastic((0.008, 0.007, 0.006), 0.9), verts=32, bevel=0)
            emitters.append({"pos": [vx, vy, 0.05], "type": "steam"})
        # steel survey stake + marker flag so the vent reads as a claimable resource
        K.cyl(0.015, 0.6, (0.9, 0.6, hf(0.9, 0.6) - 0.05), M.metal("steel", dirt=0.6), verts=12)
        K.box((0.16, 0.01, 0.1), (0.98, 0.6, hf(0.9, 0.6) + 0.48), KI.paint(cc, wear=0.2, grime=0.3, rust=0.0, name="flag"),
              bevel=0.003)
        pts.append((0.9, 0.6, 0.6))
    return style, pts, emitters


# =========================================================================== render
def render_deposit(d, quality, out_png, out_json=None):
    t0 = time.time()
    studio.reset(quality)
    KI.reset()
    studio.shadow_catcher(size=40.0, z=-0.3)  # below pools / cracks (the catcher occludes what lies under it)
    style, pts, emitters = build(d)
    info = studio.frame_iso_camera(pts, margin_px=4)
    studio.render_to(out_png)
    if out_json:
        studio.write_json(out_json, {"origin": info["origin"], "size": [info["width"], info["height"]], "style": style,
                                     "emitters": [dict(e, px=studio.world_to_px(e["pos"])) for e in emitters]})
    print(f"[done] {d['id']} ({style}) {info['width']}x{info['height']} in {time.time() - t0:.1f}s")


def parse(argv):
    o = {"quality": "draft", "ids": None, "all": False, "missing": False, "samples": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--ids", "--quality"):
            o[a[2:]] = argv[i + 1]
            i += 2
            continue
        if a.startswith("--") and a[2:] in o:
            o[a[2:]] = True
        i += 1
    return o


def main():
    o = parse(studio.cli_args())
    if o["samples"]:
        entries = []
        for d in SAMPLES:
            path = os.path.join(SAMPLE_DIR, f"{d['id']}.png")
            try:
                render_deposit(d, o["quality"], path)
                entries.append((path, f"{d['id']}:{style_of(d)}"))
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[fail] {d['id']}: {e}")
        KI.contact_sheet(entries, os.path.join(SAMPLE_DIR, "sheet.png"), cell=256, cols=3, small=0)
        return
    try:
        deps = studio.load_data("world")["deposits"]
    except OSError:
        print("data/world.json not found - use --samples")
        return
    if o["ids"]:
        want = set(o["ids"].split(","))
        deps = [d for d in deps if d["id"] in want]
    elif not o["all"]:
        print("nothing selected (use --ids/--all/--samples)")
        return
    if o["missing"]:
        deps = [d for d in deps if not os.path.exists(os.path.join(OUT_DIR, f"deposit_{d['id']}.png"))]
    entries = []
    for d in deps:
        png = os.path.join(OUT_DIR, f"deposit_{d['id']}.png")
        try:
            render_deposit(d, o["quality"], png, os.path.join(OUT_DIR, f"deposit_{d['id']}.json"))
            entries.append((png, d["id"]))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[fail] {d['id']}: {e}")
    if entries:
        KI.contact_sheet(entries, os.path.join(studio.RENDER_DIR, "icons", "deposits_sheet.png"), cell=256, cols=4, small=0)


main()
