"""Procedural hard-surface modelling kit (1 unit = 1 m, object scale always 1).

Primitives take real dimensions and return bpy objects with a material and a bevel
modifier (bevels catch highlights - the single biggest realism win for hard surfaces).
Parts compose primitives into reusable industrial details.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import materials as M

_coll = None


def collection():
    global _coll
    if _coll is None or _coll.name not in bpy.data.collections:
        _coll = bpy.data.collections.new("model")
        bpy.context.scene.collection.children.link(_coll)
    return _coll


def reset():
    global _coll
    _coll = None


def _finish(name, bm, mat, loc, rot, bevel, segments=2, smooth_angle=35.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    collection().objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = Euler(rot, "XYZ") if not isinstance(rot, Euler) else rot
    if mat is not None:
        me.materials.append(mat)
    if bevel and bevel > 0:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = segments
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        b.harden_normals = True
        b.miter_outer = "MITER_ARC"
    for p in me.polygons:
        p.use_smooth = True
    sm = o.modifiers.new("smooth", "NODES") if False else None  # placeholder (auto smooth via edges)
    _sharp_edges(me, smooth_angle)
    return o


def _sharp_edges(me, angle_deg):
    """Mark edges sharper than angle as sharp so smooth shading keeps hard corners."""
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle_deg)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim:
            e.smooth = False
        elif len(e.link_faces) != 2:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


# --------------------------------------------------------------------------- primitives
def box(size, loc=(0, 0, 0), mat=None, bevel=0.015, rot=(0, 0, 0), name="box", base=False):
    """Axis aligned box of `size` (x, y, z). If base=True, loc is the bottom-centre."""
    sx, sy, sz = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if base:
        bmesh.ops.translate(bm, vec=(0, 0, sz / 2), verts=bm.verts)
    return _finish(name, bm, mat, loc, rot, bevel)


def cyl(r, h, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), verts=32, bevel=0.006, name="cyl", base=True, r2=None):
    """Cylinder along local Z. base=True -> loc is the bottom centre. r2 makes a cone/frustum."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r,
                          radius2=r if r2 is None else r2, depth=h)
    if base:
        bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    return _finish(name, bm, mat, loc, rot, bevel)


def sphere(r, loc=(0, 0, 0), mat=None, segs=32, rings=16, name="sphere", scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    o = _finish(name, bm, mat, loc, (0, 0, 0), 0, smooth_angle=89)
    return o


def torus(R, r, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), name="torus", segs=40, rsegs=12):
    bm = bmesh.new()
    verts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        ring = []
        for j in range(rsegs):
            b = 2 * math.pi * j / rsegs
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)
    for i in range(segs):
        for j in range(rsegs):
            a = verts[i][j]
            b = verts[(i + 1) % segs][j]
            c = verts[(i + 1) % segs][(j + 1) % rsegs]
            d = verts[i][(j + 1) % rsegs]
            bm.faces.new((a, b, c, d))
    return _finish(name, bm, mat, loc, rot, 0, smooth_angle=89)


def tube(points, r, mat=None, verts=16, name="tube", bend=0.0):
    """Pipe through `points` (list of xyz). bend>0 rounds corners with that radius."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = max(2, verts // 4)
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    pts = [Vector(p) for p in points]
    if bend > 0 and len(pts) > 2:
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            a, b, c = pts[i - 1], pts[i], pts[i + 1]
            da = (a - b).normalized()
            dc = (c - b).normalized()
            k = min(bend, (a - b).length / 2, (c - b).length / 2)
            p0, p2 = b + da * k, b + dc * k
            for t in range(7):
                u = t / 6
                out.append(p0 * (1 - u) ** 2 + b * 2 * u * (1 - u) + p2 * u * u)
        out.append(pts[-1])
        pts = out
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1)
    o = bpy.data.objects.new(name, cu)
    collection().objects.link(o)
    if mat:
        cu.materials.append(mat)
    return o


def prism(profile, depth, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), bevel=0.01, name="prism"):
    """Extrude a 2D profile (list of (x, z) in the XZ plane) along +Y by depth (centred)."""
    bm = bmesh.new()
    front = [bm.verts.new((x, -depth / 2, z)) for x, z in profile]
    back = [bm.verts.new((x, depth / 2, z)) for x, z in profile]
    n = len(profile)
    bm.faces.new(list(reversed(front)))
    bm.faces.new(back)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(name, bm, mat, loc, rot, bevel)


def pivot(name="pivot", loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    collection().objects.link(e)
    e.location = Vector(loc)
    e.rotation_euler = Euler(rot, "XYZ")
    return e


def attach(children, parent):
    for c in children:
        if c is None:
            continue
        mw = c.matrix_world.copy()
        c.parent = parent
        c.matrix_parent_inverse = parent.matrix_world.inverted()
        c.matrix_world = mw
    return parent


def join(objs, name="joined"):
    """Join mesh objects into one (keeps materials & modifiers of the first)."""
    objs = [o for o in objs if o is not None and o.type == "MESH"]
    if len(objs) < 2:
        return objs[0] if objs else None
    for o in objs:
        for m in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
        o.select_set(True)
    ctx = {"active_object": objs[0], "selected_editable_objects": objs, "object": objs[0]}
    with bpy.context.temp_override(**ctx):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


AXES = {"x": (0, math.pi / 2, 0), "y": (-math.pi / 2, 0, 0), "z": (0, 0, 0),
        "-x": (0, -math.pi / 2, 0), "-y": (math.pi / 2, 0, 0)}


# --------------------------------------------------------------------------- parts
def bolts(center, radius, n, axis="z", r=0.018, h=0.016, mat=None, start=0.0):
    """Ring of hex bolt heads on a flange face."""
    mat = mat or M.metal("dark_steel")
    rot = Euler(AXES[axis], "XYZ").to_matrix()
    out = []
    for i in range(n):
        a = start + 2 * math.pi * i / n
        p = Vector(center) + rot @ Vector((math.cos(a) * radius, math.sin(a) * radius, 0))
        out.append(cyl(r, h, p, mat, rot=AXES[axis], verts=6, bevel=0.003, name="bolt"))
    return out


def flange(center, r_pipe, axis="z", mat=None, thick=0.035):
    mat = mat or M.metal("cast_iron")
    rot = AXES[axis]
    f = cyl(r_pipe * 1.75, thick, center, mat, rot=rot, verts=32, base=False, name="flange")
    n = 6 if r_pipe < 0.12 else 8
    b = bolts(Vector(center) + Euler(rot, "XYZ").to_matrix() @ Vector((0, 0, thick / 2)),
              r_pipe * 1.42, n, axis, r=max(0.012, r_pipe * 0.16), h=0.015)
    return [f] + b


def pipe_run(points, r=0.08, mat=None, flanges=True, bend=None):
    mat = mat or M.painted((0.45, 0.45, 0.42), wear=0.4, grime=0.6, name="pipe_paint")
    out = [tube(points, r, mat, bend=bend if bend is not None else r * 2.5)]
    if flanges:
        for i in (0, len(points) - 1):
            p = Vector(points[i])
            q = Vector(points[1] if i == 0 else points[-2])
            d = (p - q).normalized()
            ax = max((("x", abs(d.x)), ("y", abs(d.y)), ("z", abs(d.z))), key=lambda t: t[1])[0]
            out += flange(p - d * 0.02, r, ax)
    return out


def ibeam(length, h=0.2, w=0.12, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, name="beam"):
    """I-beam along local X."""
    mat = mat or M.painted((0.2, 0.22, 0.24), wear=0.5, grime=0.6, name="beam_paint")
    t = 0.018
    prof = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, -h / 2 + t), (t / 2, -h / 2 + t), (t / 2, h / 2 - t),
            (w / 2, h / 2 - t), (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, h / 2 - t), (-t / 2, h / 2 - t),
            (-t / 2, -h / 2 + t), (-w / 2, -h / 2 + t)]
    o = prism(prof, length, (0, 0, 0), mat, rot=(0, 0, 0), bevel=0.003, name=name)
    o.rotation_euler = Euler((0, 0, math.pi / 2), "XYZ")
    bpy.context.view_layer.update()
    o.data.transform(o.matrix_basis)
    o.matrix_basis = Matrix.Identity(4)
    o.location = Vector(loc)
    o.rotation_euler = Euler(rot, "XYZ")
    return o


def skid(w, d, h=0.18, paint=(0.22, 0.24, 0.26), tread=True):
    """Steel base frame (perimeter I-beams + tread-plate deck). Returns (objs, deck_top_z)."""
    out = []
    beam_mat = M.painted(paint, wear=0.55, grime=0.7, name="skid_paint")
    for y in (-d / 2 + 0.06, d / 2 - 0.06):
        out.append(ibeam(w, h, 0.12, (0, y, h / 2), mat=beam_mat))
    for x in (-w / 2 + 0.06, w / 2 - 0.06):
        out.append(ibeam(d - 0.24, h, 0.12, (x, 0, h / 2), rot=(0, 0, math.pi / 2), mat=beam_mat))
    if tread:
        out.append(box((w, d, 0.012), (0, 0, h + 0.006), M.tread_plate(0.8), bevel=0.004, name="deck"))
    return out, h + 0.012


def hazard_edge(w, d, z, width=0.08, h=0.01):
    m = M.hazard(5.0)
    return [box((w, width, h), (0, -d / 2 + width / 2, z + h / 2), m, bevel=0.002),
            box((w, width, h), (0, d / 2 - width / 2, z + h / 2), m, bevel=0.002),
            box((width, d - 2 * width, h), (-w / 2 + width / 2, 0, z + h / 2), m, bevel=0.002),
            box((width, d - 2 * width, h), (w / 2 - width / 2, 0, z + h / 2), m, bevel=0.002)]


def control_cabinet(loc, rot_z=0.0, w=0.6, d=0.35, h=1.4, paint=(0.78, 0.78, 0.74), screen_col=(0.25, 0.95, 0.55)):
    """Electrical cabinet with display, push buttons and cable conduit. Front faces -Y (before rot)."""
    out = []
    body_mat = M.painted(paint, wear=0.25, grime=0.4, rough=0.5, name="cabinet_paint")
    piv = pivot("cabinet", loc, (0, 0, rot_z))
    body = box((w, d, h), (0, 0, 0), body_mat, bevel=0.02, base=True)
    out.append(body)
    out.append(box((w * 0.62, 0.012, h * 0.24), (0, -d / 2 - 0.004, h * 0.72), M.screen(screen_col, 2.5), bevel=0.002))
    out.append(box((w * 0.72, 0.02, h * 0.32), (0, -d / 2 - 0.002, h * 0.72), M.plastic((0.04, 0.04, 0.045)), bevel=0.006))
    cols = [(0.9, 0.1, 0.05), (0.1, 0.8, 0.15), (0.95, 0.75, 0.05)]
    for i, c in enumerate(cols):
        out.append(cyl(0.025, 0.03, (-w * 0.25 + i * w * 0.25, -d / 2 - 0.0, h * 0.42), M.emissive(c, 3.0), rot=AXES["-y"], verts=16, bevel=0.003))
    out.append(box((w * 0.9, 0.01, 0.02), (0, -d / 2 - 0.004, h * 0.12), M.hazard(8), bevel=0.001))
    out.append(cyl(0.035, 0.4, (w * 0.35, 0, h), M.metal("steel", dirt=0.6), verts=12))
    attach(out, piv)
    return out


def motor(loc, axis="x", r=0.16, length=0.45, paint=(0.1, 0.25, 0.45)):
    """Electric motor with cooling fins, end cap and terminal box."""
    mat = M.painted(paint, wear=0.35, grime=0.5, name="motor_paint")
    rot = Euler(AXES[axis], "XYZ")
    m3 = rot.to_matrix()
    c = Vector(loc)
    out = [cyl(r, length, c, mat, rot=AXES[axis], verts=36, base=False, name="motor")]
    nfin = 14
    for i in range(nfin):
        a = 2 * math.pi * i / nfin
        off = m3 @ Vector((math.cos(a) * r, math.sin(a) * r, 0))
        fin = box((0.03, 0.03, length * 0.86), c + off * 1.02, mat, bevel=0.004, name="fin")
        fin.rotation_euler = rot
        fin.rotation_euler.rotate(Euler((0, 0, a), "XYZ"))
        out.append(fin)
    out.append(cyl(r * 0.85, 0.05, c + m3 @ Vector((0, 0, length / 2)), M.metal("cast_iron"), rot=AXES[axis], base=False))
    out.append(box((r * 0.9, r * 0.7, r * 0.6), c + Vector((0, 0, r + r * 0.25)), mat, bevel=0.01))
    return out


def fan(loc, r=0.35, axis="z", blades=7, mat=None, housing=True):
    """Axial fan; returns (objs, rotor_pivot). Animate rotor_pivot.rotation_euler."""
    mat = mat or M.metal("aluminum", dirt=0.6)
    out = []
    piv = pivot("fan_rotor", loc, AXES[axis])
    blades_o = []
    for i in range(blades):
        a = 2 * math.pi * i / blades
        b = box((r * 0.82, r * 0.28, 0.012), (0, 0, 0), mat, bevel=0.003, name="blade")
        b.location = Vector((math.cos(a) * r * 0.5, math.sin(a) * r * 0.5, 0))
        b.rotation_euler = Euler((math.radians(28), 0, a), "XYZ")
        b.rotation_euler = Euler((0, 0, a), "XYZ")
        b.rotation_euler.rotate_axis("X", math.radians(28))
        blades_o.append(b)
    hub = cyl(r * 0.18, 0.06, (0, 0, -0.03), M.metal("dark_steel"), verts=24)
    blades_o.append(hub)
    for b in blades_o:
        b.parent = piv
    out += blades_o
    if housing:
        ring = torus(r * 1.04, 0.025, loc, M.painted((0.25, 0.27, 0.28), name="fan_ring"), rot=AXES[axis])
        out.append(ring)
        # guard grille bars
        g = M.metal("dark_steel", dirt=0.3)
        m3 = Euler(AXES[axis], "XYZ").to_matrix()
        for k in range(-3, 4):
            off = m3 @ Vector((k * r * 0.28, 0, 0.05))
            L = 2 * math.sqrt(max(0.0, (r * 1.04) ** 2 - (k * r * 0.28) ** 2))
            bar = cyl(0.006, L, Vector(loc) + off, g, rot=(0, 0, 0), verts=6, base=False, bevel=0)
            bar.rotation_euler = Euler(AXES[axis], "XYZ")
            bar.rotation_euler.rotate_axis("X", math.pi / 2)
            out.append(bar)
    return out, piv


def chimney(loc, r=0.22, h=3.0, mat=None):
    mat = mat or M.metal("cast_iron", dirt=0.9)
    out = [cyl(r, h, loc, mat, verts=32)]
    soot = M.metal("dark_steel", rough=0.9, dirt=1.0)
    for k in range(3):
        out.append(torus(r * 1.02, 0.018, Vector(loc) + Vector((0, 0, h * (0.25 + 0.3 * k))), mat))
    out.append(cyl(r * 1.12, 0.12, Vector(loc) + Vector((0, 0, h - 0.06)), soot, verts=32))
    out.append(cyl(r * 0.9, 0.02, Vector(loc) + Vector((0, 0, h)), M.plastic((0.01, 0.01, 0.01), 0.95), verts=32, bevel=0))
    return out


def beacon(loc, color=(1.0, 0.55, 0.05), on=True):
    out = [cyl(0.05, 0.04, loc, M.metal("dark_steel"), verts=16)]
    out.append(cyl(0.042, 0.08, Vector(loc) + Vector((0, 0, 0.04)),
                   M.emissive(color, 12.0 if on else 0.3) if on else M.glass(color, 0.2), verts=16))
    return out


def ladder(loc, h, rot_z=0.0, w=0.42, mat=None):
    mat = mat or M.painted((0.85, 0.65, 0.05), wear=0.6, grime=0.5, name="ladder_paint")
    piv = pivot("ladder", loc, (0, 0, rot_z))
    out = [cyl(0.02, h, (-w / 2, 0, 0), mat, verts=10), cyl(0.02, h, (w / 2, 0, 0), mat, verts=10)]
    n = int(h / 0.3)
    for i in range(1, n + 1):
        out.append(cyl(0.013, w, (-w / 2, 0, i * 0.3), mat, rot=AXES["x"], verts=8, base=True))
    attach(out, piv)
    return out


def railing(points, h=1.0, mat=None):
    mat = mat or M.painted((0.9, 0.7, 0.05), wear=0.5, grime=0.5, name="rail_paint")
    out = []
    pts = [Vector(p) for p in points]
    top = [p + Vector((0, 0, h)) for p in pts]
    mid = [p + Vector((0, 0, h * 0.5)) for p in pts]
    out.append(tube(top, 0.02, mat))
    out.append(tube(mid, 0.015, mat))
    for a, b in zip(pts, pts[1:]):
        seg = (b - a)
        n = max(1, int(seg.length / 1.0))
        for i in range(n + 1):
            p = a + seg * (i / n)
            out.append(cyl(0.02, h, p, mat, verts=10))
    return out


def tank(loc, r, h, mat=None, dome=True, bands=3, legs=False):
    mat = mat or M.painted((0.75, 0.76, 0.74), wear=0.3, grime=0.5, name="tank_paint")
    c = Vector(loc)
    out = []
    z0 = 0.0
    if legs:
        z0 = 0.5
        for i in range(4):
            a = math.pi / 4 + i * math.pi / 2
            out.append(ibeam(0.5, 0.12, 0.08, c + Vector((math.cos(a) * r * 0.8, math.sin(a) * r * 0.8, 0.25)), rot=(0, math.pi / 2, a)))
    out.append(cyl(r, h, c + Vector((0, 0, z0)), mat, verts=48, bevel=0.01))
    if dome:
        out.append(sphere(r, c + Vector((0, 0, z0 + h)), mat, scale=(1, 1, 0.35)))
    for k in range(bands):
        out.append(torus(r * 1.008, 0.02, c + Vector((0, 0, z0 + h * (k + 1) / (bands + 1))), M.metal("steel", dirt=0.7)))
    return out


def vent_grille(loc, w, h, rot_z=0.0, depth_axis="-y"):
    """Louvred vent on a wall (front faces -Y before rotation)."""
    piv = pivot("vent", loc, (0, 0, rot_z))
    out = [box((w, 0.02, h), (0, 0, 0), M.metal("dark_steel", dirt=0.6), bevel=0.004)]
    n = max(3, int(h / 0.05))
    m = M.painted((0.3, 0.31, 0.32), wear=0.3, name="vent_paint")
    for i in range(n):
        z = -h / 2 + (i + 0.5) * h / n
        s = box((w * 0.94, 0.012, h / n * 0.9), (0, -0.02, z), m, bevel=0.002)
        s.rotation_euler = Euler((math.radians(-35), 0, 0), "XYZ")
        out.append(s)
    attach(out, piv)
    return out


def cable_tray(points, w=0.2):
    m = M.metal("steel", dirt=0.6)
    out = [tube(points, 0.03, M.plastic((0.02, 0.02, 0.02), 0.6), bend=0.2)]
    return out


def rivet_strip(start, end, n=8, r=0.012, mat=None):
    mat = mat or M.metal("dark_steel")
    a, b = Vector(start), Vector(end)
    return [sphere(r, a.lerp(b, i / (n - 1)), mat, segs=8, rings=4, scale=(1, 1, 0.5)) for i in range(n)]


def scatter_debris(w, d, n=10, seed=0, mat=None):
    """Small floor clutter: bolts, offcuts, puddles - grounds machines in their scene."""
    rnd = random.Random(seed)
    mat = mat or M.metal("iron", dirt=0.8)
    out = []
    for _ in range(n):
        x = rnd.uniform(-w / 2, w / 2)
        y = rnd.uniform(-d / 2, d / 2)
        out.append(box((rnd.uniform(0.03, 0.12), rnd.uniform(0.02, 0.05), 0.012), (x, y, 0.006), mat,
                       rot=(0, 0, rnd.uniform(0, math.pi)), bevel=0.002, name="debris"))
    return out
