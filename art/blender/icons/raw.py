"""Raw-material icons: ore chunks, powder / gravel piles, crystal clusters, pellets, logs, sacks."""
import math
import random

import bmesh
from mathutils import Euler, Vector, noise

import kit as K
import kit_icons as KI
import materials as M
from icons import frame


def _cluster(specs, mat, seed, cuts=7, squash=(1, 1, 0.75), bump=0.14):
    """specs: [(r, x, y, lift)] -> faceted rocks resting on the ground (lift > 0 stacks a rock on others)."""
    rnd = random.Random(seed)
    out = []
    for k, (r, x, y, lift) in enumerate(specs):
        o = KI.rock_mesh(r, seed + k * 17, cuts=cuts, bump=bump, squash=squash, mat=mat, subdiv=4, detail=0.05)
        o.rotation_euler = Euler((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, math.tau)), "XYZ")
        o.location = (x, y, 0)
        KI.ground([o])
        o.location.z += lift
        out.append(o)
    return out


def ore_chunks(item, material, color, p):
    """A small heap of broken ore lumps: one big chunk, others leaning on it, a few chips."""
    mat = KI.ore(material, color) if material in KI.ORES else KI.surf(material or "stone", color)
    if KI.is_metal(material or ""):
        mat = KI.metal(material, color, rough=0.45, dirt=0.8)
    seed = KI.seed_of(item["id"])
    specs = [(0.115, 0.0, 0.04, 0.0), (0.08, -0.12, -0.05, 0.0), (0.078, 0.11, -0.06, 0.0), (0.06, 0.0, -0.13, 0.0),
             (0.065, -0.02, -0.01, 0.1), (0.036, 0.19, 0.05, 0.0), (0.032, -0.19, 0.07, 0.0), (0.03, 0.12, -0.18, 0.0),
             (0.026, -0.12, -0.17, 0.0)]
    _cluster(specs, mat, seed, cuts=8, squash=(1.0, 0.9, 0.78))
    return frame()


def powder_pile(item, material, color, p):
    """Conical heap of fine powder on a steel tray, with a few loose grains."""
    mat = KI.powder_for(material or "sand", color)
    seed = KI.seed_of(item["id"])
    KI.heap(0.19, 0.17, seed, mat=mat, rough=0.05, lumps=0.1, slump=0.8)
    tray = M.metal("stainless", dirt=0.7)
    KI.lathe([(0, 0), (0.225, 0), (0.237, 0.004), (0.245, 0.028), (0.237, 0.03), (0.23, 0.01), (0, 0.01)],
             tray, segs=64, name="tray")
    for o in K.collection().objects:
        if o.name.startswith("heap"):
            o.location.z = 0.009
    return frame()


def gravel_pile(item, material, color, p):
    """Heap of crushed angular stone."""
    mat = KI.surf(material or "stone", color)
    seed = KI.seed_of(item["id"])
    rnd = random.Random(seed)
    R, H = 0.24, 0.13
    KI.heap(R * 0.93, H * 0.9, seed, mat=mat, rough=0.1, lumps=0.15)
    protos = [KI.rock_mesh(0.026, seed + i, cuts=6, bump=0.2, mat=mat) for i in range(6)]
    for o in protos:
        o.location = (0, 0, -5)
    n = 170
    for i in range(n):
        a = rnd.uniform(0, math.tau)
        u = math.sqrt(rnd.random()) * 1.02
        x, y = math.cos(a) * u * R, math.sin(a) * u * R
        z = KI.heap_height(R * 0.93, H * 0.9, x, y) + 0.008
        s = rnd.uniform(0.6, 1.25)
        KI.dup(protos[i % len(protos)], (x, y, z), (rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6)), s)
    for o in protos:
        o.hide_render = True
    return frame()


def crystal_cluster(item, material, color, p):
    """Hexagonal crystals with pointed terminations radiating from a rocky matrix."""
    seed = KI.seed_of(item["id"])
    rnd = random.Random(seed)
    if material in (None, "crystal", "glass", "quartz", "salt", "uranium_glass", "glow"):
        c = color or KI.MAT_COLOR.get(material or "crystal", (0.6, 0.8, 1.0))
        glow = 2.0 if material in ("uranium_glass", "glow") else 0.0
        cmat = KI.gem(c, 0.04, 0.5, glow)
    else:
        cmat = KI.surf(material, color)
    base_mat = KI.rock(base=(0.08, 0.075, 0.07), base2=(0.03, 0.03, 0.03), speck=(0.2, 0.2, 0.2), speck_amt=0.4,
                       rough=0.8, name="matrix")
    b = KI.rock_mesh(0.14, seed, cuts=6, bump=0.12, squash=(1.1, 1.0, 0.45), mat=base_mat)
    KI.ground([b])
    crystals = [(0.0, 0.0, 0.34, 0.05, 0.0, 0.0), (0.06, 0.03, 0.24, 0.04, 0.45, 0.6), (-0.06, 0.04, 0.22, 0.038, -0.4, 0.3),
                (0.02, -0.07, 0.2, 0.035, 0.2, -0.55), (-0.05, -0.05, 0.16, 0.03, -0.5, -0.5),
                (0.09, -0.04, 0.13, 0.026, 0.8, -0.3), (-0.1, 0.0, 0.12, 0.025, -0.85, 0.1), (0.04, 0.08, 0.15, 0.03, 0.3, 0.8)]
    for x, y, L, r, tx, ty in crystals:
        L *= rnd.uniform(0.9, 1.1)
        tip = r * rnd.uniform(1.6, 2.2)
        prof = [(0, -0.05), (r * 0.98, -0.05), (r, L - tip), (r * 0.15, L - 0.004), (0, L)]
        o = KI.lathe(prof, cmat, segs=6, name="crystal", smooth=20)
        o.rotation_euler = Euler((ty * 0.8, tx * 0.8, rnd.uniform(0, 1)), "XYZ")
        o.location = (x, y, 0.07)
    return frame()


def pellets(item, material, color, p):
    """Small heap of cylindrical pellets in a shallow dish."""
    seed = KI.seed_of(item["id"])
    rnd = random.Random(seed)
    mat = KI.surf(material or "plastic_color", color)
    if material in ("uranium_glass",):
        mat = M.metal("lead", rough=0.5, tint=(0.75, 0.9, 0.55), dirt=0.3)
    elif material == "glow":
        mat = KI.gem(color or (0.4, 0.9, 1.0), 0.1, 0.8, glow=0.35)
    proto = KI.lathe([(0, 0), (0.0105, 0), (0.012, 0.002), (0.012, 0.02), (0.0105, 0.022), (0, 0.022)], mat, segs=16,
                     name="pellet", smooth=50)
    proto.location = (0, 0, -5)
    R, H = 0.17, 0.13
    dish = M.metal("stainless", dirt=0.6)
    KI.lathe([(0, 0), (0.21, 0), (0.225, 0.006), (0.235, 0.03), (0.228, 0.032), (0.22, 0.01), (0, 0.01)], dish, segs=64,
             name="dish")
    count = 0
    for layer in range(7):
        for i in range(110):
            a = rnd.uniform(0, math.tau)
            u = math.sqrt(rnd.random())
            x, y = math.cos(a) * u * R, math.sin(a) * u * R
            z = 0.01 + KI.heap_height(R, H, x, y) * (layer + 1) / 7
            if z < 0.012 and layer > 0:
                continue
            KI.dup(proto, (x, y, z), (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)))
            count += 1
    proto.hide_render = True
    if material in ("uranium_glass", "glow"):
        # faint Cherenkov-ish glow under the pile
        K.cyl(0.15, 0.002, (0, 0, 0.011), M.emissive(KI.lin(color or (0.3, 1.0, 0.2)), 1.5), verts=48)
    return frame()


def log(item, material, color, p):
    """Three sawn logs (2 + 1) with bark and end grain."""
    seed = KI.seed_of(item["id"])
    rnd = random.Random(seed)
    wc = KI.lin(color) if color else (0.55, 0.36, 0.17)
    bmat = KI.bark(axis="x")
    emat = KI.end_grain(wc, axis="x")
    out = []
    specs = [(0.075, 0.48, (0, -0.078, 0.075)), (0.072, 0.46, (0.02, 0.078, 0.072)), (0.07, 0.44, (0.01, 0.0, 0.2))]
    for r, L, loc in specs:
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=28, radius1=r, radius2=r * 0.95, depth=L)
        off = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), 0))
        for v in bm.verts:
            d = 1 + 0.06 * noise.noise(Vector((v.co.x * 12, v.co.y * 12, v.co.z * 3)) + off)
            v.co.x *= d
            v.co.y *= d
        for f in bm.faces:
            f.material_index = 1 if abs(f.normal.z) > 0.9 else 0
        o = KI.finish("log", bm, None, (0, 0, 0), (0, math.pi / 2, 0), 0.004, smooth=50)
        # mesh axis is Z; rotate to X. Materials: bark / end grain (end grain uses object X axis)
        KI.set_mats(o, [bmat, KI.end_grain(wc, axis="z")])
        o.location = Vector(loc)
        o.rotation_euler = Euler((0, math.pi / 2, rnd.uniform(-0.08, 0.08)), "XYZ")
        out.append(o)
    KI.ground(out)
    return frame(yaw=28.0)


def bag(item, material, color, p):
    """Filled woven sack, sewn top, printed band."""
    seed = KI.seed_of(item["id"])
    c = KI.lin(color) if color else (0.32, 0.22, 0.1)
    mat = KI.fabric(c, coarse=1.0 if not color else 0.5)
    W, D, H = 0.3, 0.2, 0.42
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=10, use_grid_fill=True)
    off = Vector((seed % 97, seed % 89, 0)) * 0.1
    for v in bm.verts:
        x, y, z = v.co  # -0.5..0.5
        zz = z + 0.5  # 0..1
        # rounded pillow cross-section, bulging belly, flat bottom, pinched sewn top
        belly = 1.0 + 0.12 * math.sin(math.pi * min(1, zz * 1.1))
        pinch = 1.0 - 0.55 * max(0.0, zz - 0.78) / 0.22
        sx = W * belly
        sy = D * belly * (1.0 - 0.75 * max(0.0, zz - 0.72) / 0.28)
        rx, ry = x * 2, y * 2
        k = 1 - 0.18 * (rx * rx * ry * ry)
        nx = x * sx * k * (pinch if abs(x) > 0.3 else 1)
        ny = y * sy * k
        nz = zz * H
        nz -= 0.03 * (rx * rx) * zz ** 3  # top seam sags at the corners
        wr = 0.006 * noise.noise(Vector((nx * 30, ny * 30, nz * 30)) + off)
        v.co = Vector((nx, ny, max(0.0, nz + wr)))
    o = KI.finish("sack", bm, mat, (0, 0, 0), (0, 0, 0), 0.0, smooth=70)
    o.modifiers.new("sub", "SUBSURF").levels = 1
    # sewn top seam + printed band
    seam = M.plastic((0.6, 0.55, 0.45), 0.8, name="thread")
    K.box((W * 1.02, 0.03, 0.025), (0, 0, H - 0.01), mat, bevel=0.008)
    for i in range(14):
        x = -W * 0.48 + i * W * 0.96 / 13
        K.box((0.004, 0.034, 0.006), (x, 0, H - 0.006), seam, bevel=0.001)
    band = KI.paint((0.6, 0.05, 0.02) if not color else (0.85, 0.82, 0.75), wear=0.2, grime=0.3, rough=0.7, rust=0.0,
                    name="print_band")
    o2 = KI.text_mesh("50 KG", 0.05, 0.001, band, loc=(0, -D * 0.58, H * 0.48), rot=(math.pi / 2, 0, 0))
    o2.location.y -= 0.004
    return frame()


ARCHETYPES = {
    "ore_chunks": ore_chunks,
    "powder_pile": powder_pile,
    "gravel_pile": gravel_pile,
    "crystal_cluster": crystal_cluster,
    "pellets": pellets,
    "log": log,
    "bag": bag,
}
