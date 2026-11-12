"""Shared industrial helpers for building archetypes (layered on kit.py / materials.py).

* ``begin()``         - call first in every builder (drops stale material-cache entries left by a
                        previous studio.reset(), so several buildings can render in one process).
* ``Style(params)``   - tier styling (paint / accent / frame / glow colours, wear, grime, rust).
* ``Anim``            - collects per-frame callbacks; ``Rig(update=anim)``.
* geometry helpers    - struts, beams, lattice masts, gears, wheels, rings, helices, frusta,
                        corrugated sheet, rock piles, belts, valves, gauges, ladders, cabinets...
* special materials   - animated emission, soft flames, shield glow, scrolling hot metal.

Parenting: ``bind(children, pivot)`` keeps world transforms (build in world space, then hang the
parts on a pivot placed at the rotation centre); ``group(children, pivot)`` treats the children's
transforms as pivot-local.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import kit as K
import materials as M

TAU = 2.0 * math.pi
UP = Vector((0, 0, 1))


# --------------------------------------------------------------------------- session / styling
def begin():
    """Purge material-cache entries whose datablock was removed by a scene reset."""
    for k, m in list(M._cache.items()):
        try:
            m.name
        except ReferenceError:
            del M._cache[k]


def wave(t, cycles=1.0, phase=0.0):
    return math.sin(TAU * (t * cycles + phase))


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


TIERS = {
    # paint, alt paint, accent, frame, wear, grime, rust, rough, gloss, glow
    1: dict(paint=(0.062, 0.058, 0.05), alt=(0.09, 0.055, 0.03), accent=(0.30, 0.12, 0.02),
            frame=(0.035, 0.035, 0.037), wear=0.55, grime=0.95, rust=0.55, rough=0.6, gloss=0.0,
            glow=(1.0, 0.45, 0.08), metal_dirt=1.0),
    2: dict(paint=(0.72, 0.40, 0.02), alt=(0.06, 0.18, 0.07), accent=(0.035, 0.037, 0.04),
            frame=(0.06, 0.064, 0.07), wear=0.45, grime=0.6, rust=0.2, rough=0.45, gloss=0.0,
            glow=(1.0, 0.62, 0.12), metal_dirt=0.7),
    3: dict(paint=(0.035, 0.11, 0.26), alt=(0.30, 0.32, 0.34), accent=(0.42, 0.44, 0.45),
            frame=(0.16, 0.17, 0.18), wear=0.18, grime=0.3, rust=0.04, rough=0.38, gloss=0.15,
            glow=(0.2, 1.0, 0.45), metal_dirt=0.4),
    4: dict(paint=(0.70, 0.71, 0.72), alt=(0.03, 0.032, 0.036), accent=(0.03, 0.032, 0.036),
            frame=(0.035, 0.037, 0.04), wear=0.05, grime=0.12, rust=0.0, rough=0.3, gloss=0.4,
            glow=(0.15, 0.75, 1.0), metal_dirt=0.15),
}


class Style:
    """Tier styling from building params.

    params: tier 1-4 (higher clamps to 4), paint / accent / glow overrides (linear rgb),
    variant (str): "alt" picks the tier's alternative paint; any string seeds ``rnd``.
    """

    def __init__(self, p, alt=False, paint=None, accent=None):
        self.raw_tier = int(p.get("tier", 1) or 1)
        self.tier = max(1, min(4, self.raw_tier))
        T = TIERS[self.tier]
        self.variant = str(p.get("variant", "") or "")
        use_alt = alt or self.variant in ("alt", "green", "grey", "graphite")
        self.paint = tuple(p.get("paint") or paint or (T["alt"] if use_alt else T["paint"]))
        self.accent = tuple(p.get("accent") or accent or T["accent"])
        self.glow_col = tuple(p.get("glow") or T["glow"])
        self.frame_col = T["frame"]
        self.wear, self.grime, self.rust = T["wear"], T["grime"], T["rust"]
        self.rough, self.gloss, self.dirt = T["rough"], T["gloss"], T["metal_dirt"]
        self.smoke = p.get("smoke", None)
        seed = sum(ord(c) * (i + 1) for i, c in enumerate(self.variant)) + self.tier * 101
        self.rnd = random.Random(seed)

    # ---- materials
    def mat(self, color, wear=1.0, grime=1.0, rust=1.0, rough=None, under="steel", name="paint"):
        return M.painted(tuple(color), wear=min(1.0, self.wear * wear), grime=min(1.0, self.grime * grime),
                         rough=self.rough if rough is None else rough, under=under,
                         gloss_coat=self.gloss, rust=self.rust * rust, name=name)

    def body(self, **kw):
        return self.mat(self.paint, name="body_paint", **kw)

    def accent_mat(self, **kw):
        return self.mat(self.accent, name="accent_paint", **kw)

    def frame(self, **kw):
        kw.setdefault("wear", 1.2)
        return self.mat(self.frame_col, name="frame_paint", **kw)

    def safety(self):
        """Safety-yellow handrails/guards (tier 4: light grey)."""
        c = (0.72, 0.5, 0.02) if self.tier < 4 else (0.5, 0.52, 0.54)
        return self.mat(c, wear=0.9, name="safety_paint")

    def steel(self, kind="steel"):
        return M.metal(kind, dirt=self.dirt)

    def dark(self):
        return M.metal("dark_steel", dirt=self.dirt)

    def glow(self, strength=10.0, color=None):
        return M.emissive(color or self.glow_col, strength)

    def concrete(self, scale=0.35):
        return M.concrete(scale, tint=(0.92, 0.9, 0.86) if self.tier < 3 else (1.0, 1.0, 0.98))


# --------------------------------------------------------------------------- animation
class Anim:
    """Collects per-frame callbacks; pass the instance as Rig(update=anim)."""

    def __init__(self):
        self.fns = []

    def __call__(self, t):
        for f in self.fns:
            f(t)

    def add(self, fn):
        self.fns.append(fn)
        return fn

    def spin(self, obj, turns=1.0, axis="Z", phase=0.0):
        """Rotate obj about its LOCAL axis by `turns` full turns per loop (use k/symmetry)."""
        base = obj.matrix_basis.copy()

        def f(t):
            obj.matrix_basis = base @ Matrix.Rotation(TAU * (turns * t + phase), 4, axis)
        self.fns.append(f)
        return f

    def rotate(self, obj, angle_fn, axis="Z"):
        """Rotate obj about its local axis by angle_fn(t) radians."""
        base = obj.matrix_basis.copy()

        def f(t):
            obj.matrix_basis = base @ Matrix.Rotation(angle_fn(t), 4, axis)
        self.fns.append(f)
        return f

    def move(self, obj, offset_fn):
        """Translate obj (in parent space) by offset_fn(t) -> (dx, dy, dz)."""
        base = obj.location.copy()

        def f(t):
            obj.location = base + Vector(offset_fn(t))
        self.fns.append(f)
        return f

    def value(self, socket, fn):
        def f(t):
            socket.default_value = fn(t)
        self.fns.append(f)
        return f

    def energy(self, light_data, fn):
        def f(t):
            light_data.energy = fn(t)
        self.fns.append(f)
        return f

    def visible(self, objs, fn):
        objs = list(objs)

        def f(t):
            on = bool(fn(t))
            for o in objs:
                o.hide_render = not on
        self.fns.append(f)
        return f


def blink(t, cycles=2, duty=0.5, phase=0.0):
    return 1.0 if ((t * cycles + phase) % 1.0) < duty else 0.0


def flicker(t, seed=0.0, depth=0.3):
    a = 0.5 + 0.5 * math.sin(TAU * (t * 2 + seed))
    b = 0.5 + 0.5 * math.sin(TAU * (t * 5 + seed * 1.7))
    c = 0.5 + 0.5 * math.sin(TAU * (t * 3 + seed * 2.3))
    return 1.0 - depth + depth * (0.45 * a + 0.3 * b + 0.25 * c)


# --------------------------------------------------------------------------- parenting
def world_of(o):
    if o.parent is None:
        return o.matrix_basis.copy()
    return world_of(o.parent) @ o.matrix_parent_inverse @ o.matrix_basis


def bind(children, pivot):
    """Parent children to pivot keeping their current world transforms (no depsgraph update)."""
    pw = world_of(pivot)
    inv = pw.inverted()
    for c in _flat(children):
        if c is None or c is pivot:
            continue
        cw = world_of(c)
        c.parent = pivot
        c.matrix_parent_inverse = inv
        c.matrix_basis = cw
    return pivot


def group(children, pivot):
    """Parent children whose transforms are already expressed in pivot-local space."""
    for c in _flat(children):
        if c is None or c is pivot:
            continue
        c.parent = pivot
        c.matrix_parent_inverse = Matrix.Identity(4)
    return pivot


def _flat(items):
    out = []
    for i in items:
        if isinstance(i, (list, tuple)):
            out += _flat(i)
        else:
            out.append(i)
    return out


def pivot(loc=(0, 0, 0), rot=(0, 0, 0), name="pivot", children=None, axis=None):
    """Empty at loc. axis='x'|'y'|'-y'... aligns its local Z with that world axis."""
    if axis is not None:
        rot = K.AXES[axis]
    p = K.pivot(name, loc, rot)
    if children:
        bind(children, p)
    return p


def pivot_dir(loc, direction, name="pivot", children=None):
    """Empty at loc whose local Z points along `direction`."""
    q = Vector(direction).normalized().to_track_quat("Z", "Y")
    p = K.pivot(name, loc, q.to_euler())
    if children:
        bind(children, p)
    return p


# --------------------------------------------------------------------------- lights / glow
def point_light(loc, color, energy, radius=0.12, name="glow"):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy
    d.color = tuple(color)
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    K.collection().objects.link(o)
    o.location = Vector(loc)
    return d


def spot_light(loc, direction, color, energy, angle=60.0, radius=0.05, name="spot"):
    d = bpy.data.lights.new(name, "SPOT")
    d.energy = energy
    d.color = tuple(color)
    d.spot_size = math.radians(angle)
    d.spot_blend = 0.6
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    K.collection().objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()
    return d


def anim_emit(color, strength=8.0, name="anim_glow", base=(0.02, 0.02, 0.02)):
    """Unique (uncached) emissive material; returns (material, strength_socket)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Roughness"].default_value = 0.25
    p.inputs["Coat Weight"].default_value = 0.6
    return m, p.inputs["Emission Strength"]


def soft_glow(color, strength=6.0, rim=True, name="soft_glow", power=1.6):
    """Glow with soft, partly transparent edges (flames, plasma, shield shells).

    Emission is opaque for film alpha, so the glow survives on transparent sprites; transparency
    only fades the silhouette (rim=False: bright core, fading edges) or the core (rim=True:
    bright rim, see-through centre). Returns (material, strength_socket)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    mix = nt.nodes.new("ShaderNodeMixShader")
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = power
    if rim:
        nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    else:
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(lw.outputs["Facing"], inv.inputs[1])
        nt.links.new(inv.outputs[0], pw.inputs[0])
    nt.links.new(pw.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m, em.inputs["Strength"]


def scrolling_hot_metal(color=(1.0, 0.42, 0.08), strength=9.0, axis="X", period=0.6, name="hot_strip"):
    """Glowing hot metal with scale bands every `period` m along `axis` that scroll when the
    returned Phase Offset socket is animated (phase = -2*pi*k*t moves k bands toward +axis per
    loop, seamlessly). Returns (material, phase_socket)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = M.NT(m)
    p = t.bsdf()
    tc = t.node("ShaderNodeTexCoord")
    wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=axis)
    wv.inputs["Scale"].default_value = TAU / (20.0 * period)
    wv.inputs["Distortion"].default_value = 0.0
    t.link(tc.outputs["Object"], wv.inputs["Vector"])
    n = t.noise(tc.outputs["Object"], 7.0, 6, 0.6)
    heat = t.math("ADD", t.maprange(wv.outputs["Factor"], 0.0, 1.0, 0.5, 1.0), t.maprange(n, 0.3, 0.7, -0.3, 0.1))
    p.inputs["Base Color"].default_value = (0.08, 0.03, 0.02, 1)
    p.inputs["Emission Color"].default_value = (*color, 1)
    t.link(t.math("MULTIPLY", heat, strength), p.inputs["Emission Strength"])
    p.inputs["Roughness"].default_value = 0.6
    return m, wv.inputs["Phase Offset"]


# --------------------------------------------------------------------------- mesh helpers
def mesh_obj(name, bm, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, smooth=35.0):
    o = K._finish(name, bm, mat, loc, rot, bevel, smooth_angle=smooth)
    return o


def extrude_poly(points, thick, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), bevel=0.004, name="poly", centered=True):
    """Extrude a 2D polygon (XY, CCW) along local Z by thick."""
    bm = bmesh.new()
    z0 = -thick / 2 if centered else 0.0
    bot = [bm.verts.new((x, y, z0)) for x, y in points]
    top = [bm.verts.new((x, y, z0 + thick)) for x, y in points]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mat, loc, rot, bevel)


def ring(r_out, r_in, h, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), segs=48, bevel=0.004, name="ring", centered=True):
    """Annulus extruded along local Z (thick washers, rims, riding tyres)."""
    bm = bmesh.new()
    z0 = -h / 2 if centered else 0.0
    rings = []
    for r in (r_out, r_in):
        for z in (z0, z0 + h):
            rings.append([bm.verts.new((r * math.cos(TAU * i / segs), r * math.sin(TAU * i / segs), z)) for i in range(segs)])
    ob, ot, ib, it = rings
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))      # outer wall
        bm.faces.new((ib[j], ib[i], it[i], it[j]))      # inner wall
        bm.faces.new((ot[i], ot[j], it[j], it[i]))      # top
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))      # bottom
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mat, loc, rot, bevel)


def gear(loc, r, thick, teeth=None, mat=None, rot=(0, 0, 0), tooth_h=None, hub=True, name="gear"):
    """Spur gear (axis local Z). Returns list of objects (gear body [+ hub])."""
    teeth = teeth or max(10, int(r * 60))
    th = tooth_h or max(0.012, r * 0.09)
    pts = []
    for i in range(teeth):
        a0 = TAU * i / teeth
        da = TAU / teeth
        for f, rr in ((0.0, r - th), (0.18, r), (0.5, r), (0.68, r - th)):
            a = a0 + f * da
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    out = [extrude_poly(pts, thick, loc, mat, rot, bevel=min(0.004, th * 0.25), name=name)]
    if hub:
        out.append(K.cyl(r * 0.28, thick * 1.6, loc, M.metal("dark_steel"), rot=rot, verts=24, base=False, name="hub"))
    return out


def spoked_wheel(loc, R, width, spokes=6, mat=None, rot=(0, 0, 0), rim=0.12, hub_r=None, grooves=0, name="wheel"):
    """Flywheel / pulley with spokes; axis = local Z. Returns objects (first = rim)."""
    mat = mat or M.metal("cast_iron")
    rot_m = Euler(rot, "XYZ").to_matrix()
    c = Vector(loc)
    rim_t = R * rim
    out = [ring(R, R - rim_t, width, c, mat, rot, segs=56, bevel=0.006, name=name)]
    hub_r = hub_r or R * 0.18
    out.append(K.cyl(hub_r, width * 1.35, c, mat, rot=rot, verts=28, base=False, name="hub"))
    out.append(K.cyl(hub_r * 0.45, width * 1.6, c, M.metal("steel"), rot=rot, verts=16, base=False, name="shaft"))
    for i in range(spokes):
        a = TAU * i / spokes
        mid = (R - rim_t * 0.5 + hub_r) / 2
        L = R - rim_t * 0.6 - hub_r * 0.8
        sp = K.box((L, width * 0.42, width * 0.42), (0, 0, 0), mat, bevel=0.006, name="spoke")
        sp.location = c + rot_m @ Vector((math.cos(a) * mid, math.sin(a) * mid, 0))
        sp.rotation_euler = (Euler(rot, "XYZ").to_matrix() @ Euler((0, 0, a), "XYZ").to_matrix()).to_euler()
        out.append(sp)
    for g in range(grooves):
        z = (g + 0.5) / grooves - 0.5
        out.append(K.torus(R * 1.0, width / grooves * 0.28, c + rot_m @ Vector((0, 0, z * width)), M.metal("dark_steel"),
                           rot=rot, segs=56, rsegs=8, name="groove"))
    return out


def helix(r_in, r_out, pitch, turns, loc=(0, 0, 0), mat=None, thick=0.012, steps_per_turn=36, rot=(0, 0, 0), name="flight"):
    """Auger / screw flight around local Z, starting at z=0 going up."""
    bm = bmesh.new()
    n = int(turns * steps_per_turn)
    prev = None
    for i in range(n + 1):
        a = TAU * i / steps_per_turn
        z = pitch * i / steps_per_turn
        vi = bm.verts.new((r_in * math.cos(a), r_in * math.sin(a), z))
        vo = bm.verts.new((r_out * math.cos(a), r_out * math.sin(a), z))
        if prev:
            bm.faces.new((prev[0], prev[1], vo, vi))
        prev = (vi, vo)
    o = mesh_obj(name, bm, mat, loc, rot, 0, smooth=60)
    s = o.modifiers.new("solid", "SOLIDIFY")
    s.thickness = thick
    s.offset = 0
    return o


def frustum(bottom, top, h, loc=(0, 0, 0), mat=None, top_offset=(0, 0), open_top=False, thick=0.02,
            bevel=0.008, rot=(0, 0, 0), name="frustum"):
    """Rectangular frustum (hoppers, chutes, roofs). bottom/top = (w, d); loc = bottom centre."""
    bm = bmesh.new()
    (bw, bd), (tw, td) = bottom, top
    ox, oy = top_offset
    b = [bm.verts.new((sx * bw / 2, sy * bd / 2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    tt = [bm.verts.new((ox + sx * tw / 2, oy + sy * td / 2, h)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(list(reversed(b)))
    if not open_top:
        bm.faces.new(tt)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((b[i], b[j], tt[j], tt[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, mat, loc, rot, bevel)
    if open_top:
        s = o.modifiers.new("solid", "SOLIDIFY")
        s.thickness = thick
        s.offset = -1
        o.modifiers.move(len(o.modifiers) - 1, 0)
    return o


def cone_shell(r_bot, r_top, h, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), segs=40, name="cone"):
    return K.cyl(r_bot, h, loc, mat, rot=rot, verts=segs, r2=r_top, name=name)


def corrugated(width, height, loc, rot_z=0.0, mat=None, pitch=0.2, depth=0.035, name="sheet"):
    """Trapezoidal profiled cladding sheet. Built in the XZ plane facing -Y (before rot_z);
    loc = bottom-centre of the outer face."""
    n = max(1, int(round(width / pitch)))
    pitch = width / n
    prof = []
    for i in range(n):
        x0 = -width / 2 + i * pitch
        for f, y in ((0.0, 0.0), (0.12, 0.0), (0.27, depth), (0.73, depth), (0.88, 0.0)):
            prof.append((x0 + f * pitch, y))
    prof.append((width / 2, 0.0))
    bm = bmesh.new()
    bot = [bm.verts.new((x, -y, 0.0)) for x, y in prof]
    top = [bm.verts.new((x, -y, height)) for x, y in prof]
    for i in range(len(prof) - 1):
        bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, mat, loc, (0, 0, rot_z), 0, smooth=30)
    s = o.modifiers.new("solid", "SOLIDIFY")
    s.thickness = 0.006
    return o


def strut(a, b, r, mat=None, verts=8, bevel=0.0, name="strut"):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = K.cyl(r, d.length, (0, 0, 0), mat, verts=verts, bevel=bevel, base=True, name=name)
    o.location = a
    o.rotation_euler = d.normalized().to_track_quat("Z", "Y").to_euler()
    return o


def beam(a, b, w, h, mat=None, bevel=0.006, name="beam", roll_up=(0, 0, 1)):
    """Rectangular section beam from a to b (w across, h 'up')."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = K.box((w, h, d.length), (0, 0, 0), mat, bevel=bevel, base=True, name=name)
    o.location = a
    dn = d.normalized()
    up = Vector(roll_up)
    if abs(dn.dot(up)) > 0.98:
        up = Vector((0, 1, 0))
    x = up.cross(dn).normalized()
    y = dn.cross(x).normalized()
    o.rotation_euler = Matrix((x, y, dn)).transposed().to_euler()
    return o


def hbeam(a, b, h=0.2, w=0.14, mat=None, name="hbeam"):
    """I-beam between two points (web vertical for horizontal runs)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = K.ibeam(d.length, h, w, (0, 0, 0), mat=mat, name=name)
    # K.ibeam lies along local X; orient X to d
    dn = d.normalized()
    up = UP if abs(dn.dot(UP)) < 0.98 else Vector((0, 1, 0))
    y = up.cross(dn).normalized()
    z = dn.cross(y).normalized()
    o.rotation_euler = Matrix((dn, y, z)).transposed().to_euler()
    o.location = (a + b) / 2
    return o


def lattice(base, h, w0, w1=None, d0=None, d1=None, mat=None, leg_r=0.03, brace_r=0.012, bay=0.6,
            faces=(True, True, True, True), top_ring=True):
    """Four-legged lattice tower (derricks, masts). base = bottom centre."""
    w1 = w0 if w1 is None else w1
    d0 = w0 if d0 is None else d0
    d1 = w1 if d1 is None else d1
    c = Vector(base)
    nb = max(1, int(round(h / bay)))
    out = []

    def corner(i, z):
        f = z / h
        hw = (w0 + (w1 - w0) * f) / 2
        hd = (d0 + (d1 - d0) * f) / 2
        sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i]
        return c + Vector((sx * hw, sy * hd, z))

    for i in range(4):
        out.append(strut(corner(i, 0), corner(i, h), leg_r, mat, verts=10, name="leg"))
    for k in range(nb + 1):
        z = h * k / nb
        if k == 0 or (k == nb and not top_ring):
            continue
        for i in range(4):
            if faces[i]:
                out.append(strut(corner(i, z), corner((i + 1) % 4, z), brace_r, mat, verts=6, name="brace"))
    for k in range(nb):
        z0, z1 = h * k / nb, h * (k + 1) / nb
        for i in range(4):
            if not faces[i]:
                continue
            j = (i + 1) % 4
            if k % 2 == 0:
                out.append(strut(corner(i, z0), corner(j, z1), brace_r, mat, verts=6, name="diag"))
            else:
                out.append(strut(corner(j, z0), corner(i, z1), brace_r, mat, verts=6, name="diag"))
    return out


def truss(a, b, depth=0.4, mat=None, chord_r=0.03, web_r=0.014, bays=None, up=(0, 0, 1)):
    """Planar Warren truss between a and b (chords offset by depth along `up`)."""
    a, b = Vector(a), Vector(b)
    u = Vector(up).normalized() * depth
    L = (b - a).length
    n = bays or max(2, int(round(L / max(0.3, depth))))
    out = [strut(a, b, chord_r, mat, verts=8, name="chord"), strut(a + u, b + u, chord_r, mat, verts=8, name="chord")]
    for i in range(n + 1):
        p = a.lerp(b, i / n)
        out.append(strut(p, p + u, web_r, mat, verts=6, name="web"))
        if i < n:
            q = a.lerp(b, (i + 1) / n)
            out.append(strut(p if i % 2 == 0 else p + u, q + u if i % 2 == 0 else q, web_r, mat, verts=6, name="web"))
    return out


def box_truss(a, b, w=0.4, h=0.4, mat=None, chord_r=0.025, web_r=0.012):
    """Square-section truss boom between a and b (crane jibs, bridges)."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    side = UP.cross(d)
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    up = d.cross(side).normalized()
    out = []
    for sx, sz in ((-1, 0), (1, 0)):
        o = side * (sx * w / 2)
        out += truss(a + o, b + o, h, mat, chord_r, web_r, up=up)
    L = (b - a).length
    n = max(2, int(round(L / max(0.3, h))))
    for i in range(n + 1):
        p = a.lerp(b, i / n)
        out.append(strut(p - side * w / 2, p + side * w / 2, web_r, mat, verts=6, name="tie"))
        out.append(strut(p - side * w / 2 + up * h, p + side * w / 2 + up * h, web_r, mat, verts=6, name="tie"))
    return out


# --------------------------------------------------------------------------- detail parts
def concrete_pad(w, d, h=0.12, mat=None, loc=(0, 0, 0), chamfer=0.03):
    mat = mat or M.concrete(0.35)
    return K.box((w, d, h), Vector(loc), mat, bevel=chamfer, base=True, name="pad")


def plinth(w, d, h, st, loc=(0, 0, 0)):
    """Concrete plinth with a dark steel edge angle."""
    out = [concrete_pad(w, d, h, st.concrete(), loc)]
    return out


def bolt_row(a, b, n, axis="z", r=0.014, mat=None):
    a, b = Vector(a), Vector(b)
    mat = mat or M.metal("dark_steel")
    return [K.cyl(r, r * 0.9, a.lerp(b, i / max(1, n - 1)), mat, rot=K.AXES[axis], verts=6, bevel=0.002, name="bolt")
            for i in range(n)]


def plate_sign(loc, w, h, facing="-y", color=(0.75, 0.55, 0.02), text=True, border=True):
    """Small rectangular sign / nameplate on a wall facing -y or +x."""
    rot = {"-y": (0, 0, 0), "+x": (0, 0, math.pi / 2), "y": (0, 0, math.pi), "-x": (0, 0, -math.pi / 2)}[facing]
    p = K.pivot("sign", loc, rot)
    out = [K.box((w, 0.008, h), (0, 0, 0), M.painted(color, wear=0.3, grime=0.3, name="sign_paint"), bevel=0.002)]
    if border:
        out.append(K.box((w * 1.06, 0.004, h * 1.1), (0, 0.003, 0), M.plastic((0.02, 0.02, 0.02)), bevel=0.001))
    if text:
        ink = M.plastic((0.015, 0.015, 0.015), 0.6)
        for i, f in enumerate((0.75, 0.55, 0.35)):
            out.append(K.box((w * (0.7 if i == 0 else 0.55), 0.004, h * 0.09), (-w * (0.0 if i == 0 else 0.08), -0.005, h * (f - 0.5)), ink, bevel=0))
    group(out, p)
    return out


def hazard_band(loc, w, h, facing="-y", depth=0.006):
    rot = {"-y": (0, 0, 0), "+x": (0, 0, math.pi / 2)}[facing]
    return K.box((w, depth, h), loc, M.hazard(7.0), bevel=0.001, rot=rot, name="hazard")


def status_lamp(loc, color, strength=10.0, r=0.035, h=0.06, axis="z"):
    """Cylindrical signal lamp; returns (objs, strength_socket)."""
    mat, sock = anim_emit(color, strength, "lamp")
    rot = K.AXES[axis]
    m3 = Euler(rot, "XYZ").to_matrix()
    c = Vector(loc)
    out = [K.cyl(r * 1.25, 0.02, c, M.metal("dark_steel"), rot=rot, verts=16, bevel=0.003),
           K.cyl(r, h, c + m3 @ Vector((0, 0, 0.02)), mat, rot=rot, verts=16, bevel=0.004)]
    return out, sock


def stack_light(loc, colors=((0.9, 0.08, 0.03), (1.0, 0.6, 0.02), (0.1, 0.9, 0.2)), r=0.03):
    """Machine signal tower (red/amber/green). Returns (objs, [sockets])."""
    c = Vector(loc)
    out = [K.cyl(0.008, 0.12, c, M.metal("steel"), verts=8), K.cyl(r * 1.1, 0.025, c + Vector((0, 0, 0.12)), M.plastic((0.03, 0.03, 0.03)), verts=16)]
    socks = []
    z = 0.145
    for col in reversed(colors):
        mat, s = anim_emit(col, 0.3, "stack")
        out.append(K.cyl(r, 0.05, c + Vector((0, 0, z)), mat, verts=16, bevel=0.004))
        socks.append(s)
        z += 0.052
    out.append(K.cyl(r * 0.8, 0.015, c + Vector((0, 0, z)), M.plastic((0.03, 0.03, 0.03)), verts=16))
    return out, list(reversed(socks))


def floodlight(loc, direction, color=(1.0, 0.92, 0.78), size=0.18, strength=12.0, mat=None):
    """Floodlight head on a bracket aimed along `direction`."""
    mat = mat or M.painted((0.05, 0.05, 0.055), wear=0.2, grime=0.4, name="lamp_body")
    p = pivot_dir(loc, direction, "flood")
    out = [K.box((size, size * 0.75, size * 0.35), (0, 0, -size * 0.17), mat, bevel=0.01),
           K.box((size * 0.86, size * 0.62, 0.01), (0, 0, 0.005), M.emissive(color, strength), bevel=0.002)]
    for i in range(4):
        out.append(K.box((size * 0.9, 0.006, size * 0.15), (0, -size * 0.3 + i * size * 0.2, -size * 0.38), mat, bevel=0.001))
    group(out, p)
    return out


def cable(points, r=0.02, mat=None, bend=0.15):
    return K.tube(points, r, mat or M.rubber(), verts=10, bend=bend, name="cable")


def sag(a, b, drop=0.15, n=8):
    """Points along a sagging cable from a to b."""
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, drop * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]


def handwheel(loc, r=0.08, axis="z", mat=None):
    mat = mat or M.painted((0.5, 0.04, 0.02), wear=0.4, name="wheel_red")
    rot = K.AXES[axis]
    m3 = Euler(rot, "XYZ").to_matrix()
    out = [K.torus(r, r * 0.11, loc, mat, rot=rot, segs=28, rsegs=8)]
    for i in range(3):
        a = TAU * i / 3
        p = Vector(loc)
        q = p + m3 @ Vector((math.cos(a) * r, math.sin(a) * r, 0))
        out.append(strut(p, q, r * 0.06, mat, verts=6))
    out.append(K.cyl(r * 0.18, r * 0.3, loc, mat, rot=rot, verts=12, base=False))
    return out


def gate_valve(loc, axis="x", r=0.06, mat=None, wheel_up="z"):
    """In-line gate valve: body + flanges + bonnet + handwheel (stem points along wheel_up)."""
    mat = mat or M.painted((0.18, 0.2, 0.22), wear=0.4, grime=0.6, name="valve_paint")
    c = Vector(loc)
    rot = K.AXES[axis]
    out = [K.cyl(r * 1.25, r * 2.4, c, mat, rot=rot, verts=20, base=False, name="valve")]
    m3 = Euler(rot, "XYZ").to_matrix()
    for s in (-1, 1):
        out.append(K.cyl(r * 1.7, 0.03, c + m3 @ Vector((0, 0, s * r * 1.25)), mat, rot=rot, verts=24, base=False))
    up = Vector({"z": (0, 0, 1), "x": (1, 0, 0), "-y": (0, -1, 0), "y": (0, 1, 0)}[wheel_up])
    bon = c + up * r * 1.1
    out.append(strut(c, bon + up * r * 1.6, r * 0.55, mat, verts=16))
    out.append(strut(bon + up * r * 1.6, bon + up * r * 2.6, r * 0.12, M.metal("steel"), verts=8))
    out += handwheel(bon + up * r * 2.5, r * 1.3, wheel_up if wheel_up in K.AXES else "z")
    return out


def gauge(loc, facing="-y", r=0.05):
    """Pressure gauge dial. Returns (objs, needle_pivot) - spin needle about local Z."""
    rot = {"-y": K.AXES["-y"], "+x": K.AXES["x"], "z": (0, 0, 0)}[facing]
    m3 = Euler(rot, "XYZ").to_matrix()
    c = Vector(loc)
    out = [K.cyl(r * 1.15, 0.03, c, M.metal("dark_steel"), rot=rot, verts=24, base=False),
           K.cyl(r, 0.032, c, M.plastic((0.85, 0.85, 0.82), 0.25), rot=rot, verts=24, base=False),
           K.torus(r * 1.08, r * 0.1, c + m3 @ Vector((0, 0, 0.016)), M.metal("chrome"), rot=rot, segs=24, rsegs=6)]
    piv = K.pivot("needle", c + m3 @ Vector((0, 0, 0.018)), rot)
    nd = K.box((0.006, r * 0.8, 0.003), (0, r * 0.35, 0), M.plastic((0.6, 0.03, 0.02)), bevel=0)
    group([nd], piv)
    out.append(nd)
    return out, piv


def ladder(loc, h, rot_z=0.0, w=0.42, mat=None, cage=False):
    """Fixed steel ladder (rungs face -Y before rot_z). loc = bottom centre."""
    mat = mat or M.painted((0.72, 0.5, 0.02), wear=0.6, grime=0.5, name="ladder_paint")
    p = K.pivot("ladder", loc, (0, 0, rot_z))
    out = [K.box((0.05, 0.012, h), (-w / 2, 0, h / 2), mat, bevel=0.003),
           K.box((0.05, 0.012, h), (w / 2, 0, h / 2), mat, bevel=0.003)]
    n = int(h / 0.3)
    for i in range(1, n + 1):
        out.append(K.cyl(0.012, w, (-w / 2, 0, i * 0.3), mat, rot=K.AXES["x"], verts=8, base=True))
    if cage and h > 2.2:
        z = 2.2
        while z < h + 0.01:
            pts = [(math.cos(math.pi * k / 10) * w * 0.62, -math.sin(math.pi * k / 10) * w * 0.85 - 0.0, z) for k in range(11)]
            out.append(K.tube(pts, 0.01, mat, verts=6, name="hoop"))
            z += 0.7
        for x in (-w * 0.45, 0.0, w * 0.45):
            yy = -math.sqrt(max(0.0, 1 - (x / (w * 0.62)) ** 2)) * w * 0.85
            out.append(K.box((0.03, 0.006, h - 2.2), (x, yy, 2.2 + (h - 2.2) / 2), mat, bevel=0.002))
    group(out, p)
    return out


def cabinet(loc, rot_z=0.0, w=0.6, d=0.35, h=1.4, mat=None, screen_col=(0.25, 0.95, 0.55), door_lines=True):
    """Electrical control cabinet (front faces -Y before rot_z). loc = bottom centre."""
    mat = mat or M.painted((0.62, 0.63, 0.6), wear=0.25, grime=0.4, rough=0.5, name="cabinet_paint")
    p = K.pivot("cabinet", loc, (0, 0, rot_z))
    out = [K.box((w, d, h), (0, 0, 0), mat, bevel=0.012, base=True),
           K.box((w + 0.04, d + 0.04, 0.03), (0, 0, h), mat, bevel=0.008, base=True),
           K.box((w * 0.98, d * 0.9, 0.06), (0, 0, 0), M.metal("dark_steel"), bevel=0.004, base=True)]
    out.append(K.box((w * 0.5, 0.012, h * 0.16), (-w * 0.12, -d / 2 - 0.003, h * 0.76), M.screen(screen_col, 2.5), bevel=0.002))
    out.append(K.box((w * 0.58, 0.01, h * 0.22), (-w * 0.12, -d / 2 - 0.001, h * 0.76), M.plastic((0.03, 0.03, 0.035)), bevel=0.004))
    cols = [(0.9, 0.08, 0.04), (0.1, 0.85, 0.15), (0.95, 0.7, 0.05)]
    for i, col in enumerate(cols):
        out.append(K.cyl(0.018, 0.02, (w * 0.3, -d / 2 - 0.005, h * (0.82 - i * 0.07)), M.emissive(col, 4.0), rot=K.AXES["-y"], verts=12, bevel=0.002))
    if door_lines and w > 0.5:
        out.append(K.box((0.006, 0.006, h * 0.92), (0, -d / 2 - 0.002, h * 0.5), M.plastic((0.02, 0.02, 0.02)), bevel=0))
    out.append(K.box((0.02, 0.025, 0.1), (w * 0.08 if w > 0.5 else w * 0.38, -d / 2 - 0.012, h * 0.5), M.metal("chrome"), bevel=0.003))
    out.append(K.box((w * 0.24, 0.006, h * 0.08), (-w * 0.25, -d / 2 - 0.004, h * 0.45), M.painted((0.8, 0.6, 0.02), wear=0.2, name="label_y"), bevel=0.001))
    out.append(K.box((w * 0.6, 0.012, h * 0.1), (0, -d / 2 - 0.004, h * 0.2), M.metal("dark_steel"), bevel=0.002))  # vent
    group(out, p)
    return out


def motor(loc, axis="x", r=0.16, length=0.45, mat=None, fan_cover=True):
    """TEFC motor along `axis` (+ terminal box, feet). loc = centre."""
    mat = mat or M.painted((0.08, 0.2, 0.36), wear=0.3, grime=0.5, name="motor_paint")
    rot = K.AXES[axis]
    m3 = Euler(rot, "XYZ").to_matrix()
    c = Vector(loc)
    ax = m3 @ Vector((0, 0, 1))
    out = [K.cyl(r, length, c, mat, rot=rot, verts=36, base=False, name="motor")]
    nfin = 12
    for i in range(nfin):
        a = TAU * i / nfin
        if abs(math.sin(a) + 1) < 0.3:
            continue
        off = m3 @ Vector((math.cos(a) * r, math.sin(a) * r, 0))
        fin = K.box((0.022, 0.022, length * 0.8), (0, 0, 0), mat, bevel=0.003, name="fin")
        fin.location = c + off * 1.03
        fin.rotation_euler = (m3 @ Euler((0, 0, a), "XYZ").to_matrix()).to_euler()
        out.append(fin)
    if fan_cover:
        out.append(K.cyl(r * 1.02, length * 0.22, c - ax * (length / 2 + length * 0.1), mat, rot=rot, verts=36, base=False, name="fancover"))
        out.append(K.cyl(r * 0.9, 0.01, c - ax * (length / 2 + length * 0.21), M.metal("dark_steel"), rot=rot, verts=36, base=False))
    out.append(K.cyl(r * 0.88, 0.04, c + ax * (length / 2), mat, rot=rot, verts=36, base=False))
    out.append(K.cyl(r * 0.18, length * 0.25, c + ax * (length / 2 + length * 0.12), M.metal("steel"), rot=rot, verts=16, base=False))
    out.append(K.box((r * 0.8, r * 0.75, r * 0.5), c + Vector((0, 0, r * 1.15)), mat, bevel=0.01, name="tbox"))
    # feet
    side = UP.cross(ax).normalized()
    for s in (-1, 1):
        out.append(K.box((r * 0.5 if abs(ax.x) < 0.5 else length * 0.7, r * 0.5 if abs(ax.y) < 0.5 else length * 0.7, r * 0.75),
                         c + side * s * r * 0.6 - Vector((0, 0, r * 0.62)), mat, bevel=0.006, base=False))
    return out


def rock(loc, r, mat, seed=0, flat=0.7):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in bm.verts:
        v.co *= rnd.uniform(0.72, 1.18)
        v.co.z *= flat
    o = mesh_obj("rock", bm, mat, loc, (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 6)), 0, smooth=50)
    return o


def rock_pile(center, rx, ry, h, n, mat, seed=0, rmin=0.04, rmax=0.09):
    """Mound of lumps (ore, gravel, coal)."""
    rnd = random.Random(seed)
    c = Vector(center)
    out = []
    for i in range(n):
        u = rnd.random() ** 0.6
        a = rnd.uniform(0, TAU)
        x, y = math.cos(a) * u * rx, math.sin(a) * u * ry
        z = h * (1 - u * u)
        out.append(rock(c + Vector((x, y, z)), rnd.uniform(rmin, rmax), mat, seed=seed * 1000 + i))
    return out


def ore_material(kind="iron"):
    if kind == "coal":
        return M.plastic((0.015, 0.015, 0.017), 0.55)
    if kind == "copper":
        return M.painted((0.1, 0.32, 0.26), wear=0.9, grime=0.9, rough=0.8, under="copper", name="cu_ore")
    if kind == "stone":
        return M.concrete(2.0, tint=(0.75, 0.72, 0.68))
    return M.scanned("rusty_metal_02", 2.0, tint=(0.55, 0.38, 0.3), metallic=0.1, name="iron_ore")


def walkway(x0, x1, y0, y1, z, st, legs=True, rails="", mat=None):
    """Grated platform deck at height z spanning the rectangle, with legs + optional rails.

    rails: string of sides to rail: any of 'nsew' (n=+Y, s=-Y, e=+X, w=-X)."""
    out = []
    w, d = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out.append(K.box((w, d, 0.03), (cx, cy, z - 0.015), M.tread_plate(1.2, rust=st.tier == 1), bevel=0.004, name="deck"))
    fm = mat or st.frame()
    for y in (y0 + 0.03, y1 - 0.03):
        out.append(K.box((w, 0.06, 0.12), (cx, y, z - 0.09), fm, bevel=0.005))
    for x in (x0 + 0.03, x1 - 0.03):
        out.append(K.box((0.06, d, 0.12), (x, cy, z - 0.09), fm, bevel=0.005))
    if legs:
        nx = max(1, int(round(w / 2.0)))
        ny = max(1, int(round(d / 2.0)))
        for i in range(nx + 1):
            for j in range(ny + 1):
                if 0 < i < nx and 0 < j < ny:
                    continue
                x = x0 + 0.05 + (w - 0.1) * i / nx
                y = y0 + 0.05 + (d - 0.1) * j / ny
                out.append(K.box((0.07, 0.07, z - 0.15), (x, y, 0), fm, bevel=0.005, base=True))
    rm = st.safety()
    sides = {"s": [(x0, y0 + 0.03, z), (x1, y0 + 0.03, z)], "n": [(x0, y1 - 0.03, z), (x1, y1 - 0.03, z)],
             "w": [(x0 + 0.03, y0, z), (x0 + 0.03, y1, z)], "e": [(x1 - 0.03, y0, z), (x1 - 0.03, y1, z)]}
    for s in rails:
        out += K.railing(sides[s], 0.9, rm)
    return out


def bellows_hose(points, r=0.025):
    """Hydraulic hose (black rubber, slight sag)."""
    return cable(points, r, M.rubber((0.02, 0.02, 0.022)), bend=0.12)


def hydraulic(a, b, r=0.05, ext=0.5, mat=None):
    """Hydraulic cylinder anchored at `a` pointing to `b` (fully retracted length |b-a|).

    Returns (objs, rod_pivot, axis_vec): translate rod_pivot along its local Z (0..ext) to extend."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    mat = mat or M.painted((0.6, 0.45, 0.03), wear=0.4, name="hyd_paint")
    barrel = strut(a, a + d * 0.62, r, mat, verts=20, bevel=0.004, name="barrel")
    cap = strut(a + d * 0.6, a + d * 0.66, r * 1.18, M.metal("dark_steel"), verts=20, name="gland")
    piv = pivot_dir(a + d * 0.6, d, "rod")
    rod = K.cyl(r * 0.5, L * 0.4 + ext * 0.0, (0, 0, 0), M.metal("chrome"), verts=16, name="rod")
    eye = K.cyl(r * 0.85, r * 1.0, (0, 0, L * 0.4), M.metal("dark_steel"), rot=(math.pi / 2, 0, 0), verts=16, base=False)
    group([rod, eye], piv)
    return [barrel, cap, rod, eye], piv, d.normalized()


def belt_conveyor(a, b, width, z, st, n_items=0, item_fn=None, legs=True, item_mat=None, seed=0, anim=None,
                  speed_items=1):
    """Straight belt conveyor from a to b (xy) at height z (top of belt).

    If n_items and anim are given, loads are spawned along the belt and animated to advance by
    `speed_items` spacings per loop (seamless). Returns objects."""
    a = Vector((a[0], a[1], z))
    b = Vector((b[0], b[1], z))
    d = b - a
    L = d.length
    dn = d.normalized()
    side = UP.cross(dn).normalized()
    out = []
    fm = st.frame()
    ang = math.atan2(dn.y, dn.x)
    mid = (a + b) / 2
    # side stringers
    for s in (-1, 1):
        out.append(K.box((L, 0.04, 0.16), mid + side * s * (width / 2 + 0.03) - Vector((0, 0, 0.06)), fm,
                         rot=(0, 0, ang), bevel=0.006, name="stringer"))
    out.append(K.box((L, width, 0.03), mid - Vector((0, 0, 0.018)), M.rubber((0.03, 0.03, 0.032)), rot=(0, 0, ang),
                     bevel=0.008, name="belt"))
    # end drums
    for p in (a, b):
        out.append(K.cyl(0.06, width + 0.02, p - Vector((0, 0, 0.065)), M.metal("steel", dirt=0.8),
                         rot=(math.pi / 2, 0, ang), verts=20, base=False))
    if legs:
        n = max(1, int(L / 1.4))
        for i in range(n + 1):
            p = a.lerp(b, 0.08 + 0.84 * i / n)
            for s in (-1, 1):
                q = p + side * s * (width / 2 + 0.03)
                out.append(K.box((0.045, 0.045, z - 0.14), (q.x, q.y, 0), fm, bevel=0.004, base=True, name="leg"))
    if n_items and anim is not None:
        rnd = random.Random(seed)
        spacing = L / n_items
        items = []
        for i in range(n_items):
            if item_fn:
                o = item_fn(rnd)
            else:
                o = rock((0, 0, 0), rnd.uniform(0.05, 0.08), item_mat or ore_material("iron"), seed=seed + i)
            items.append(o)
        bases = [o.location.copy() for o in items]

        def f(t, items=items, bases=bases):
            for i, o in enumerate(items):
                u = ((i + t * speed_items) * spacing) % L
                o.location = a + dn * u + bases[i] + Vector((0, 0, 0.02))
        anim.add(f)
        f(0.0)
        out += items
    return out


def skid_frame(w, d, h, st, loc=(0, 0, 0)):
    """I-beam base frame with tread deck (wrapper over K.skid honouring style colours)."""
    objs, top = K.skid(w, d, h, paint=st.frame_col)
    if loc != (0, 0, 0):
        p = K.pivot("skid", loc)
        bind(objs, p)
    return objs, top


def louvers(loc, w, h, facing="-y", mat=None, n=None):
    """Weather louvre panel on a wall facing -y or +x (loc = centre)."""
    rot = {"-y": 0.0, "+x": math.pi / 2, "y": math.pi, "-x": -math.pi / 2}[facing]
    p = K.pivot("louver", loc, (0, 0, rot))
    mat = mat or M.metal("dark_steel", dirt=0.5)
    out = [K.box((w + 0.04, 0.03, h + 0.04), (0, 0.01, 0), mat, bevel=0.005)]
    out.append(K.box((w, 0.02, h), (0, 0.0, 0), M.plastic((0.01, 0.01, 0.01), 0.9), bevel=0))
    n = n or max(3, int(h / 0.06))
    for i in range(n):
        z = -h / 2 + (i + 0.5) * h / n
        s = K.box((w * 0.98, 0.01, h / n * 1.05), (0, -0.02, z), mat, bevel=0.002)
        s.rotation_euler = (math.radians(-40), 0, 0)
        out.append(s)
    group(out, p)
    return out


def window(loc, w, h, facing="-y", lit=False, frame_mat=None, warm=(1.0, 0.75, 0.45)):
    rot = {"-y": 0.0, "+x": math.pi / 2}[facing]
    p = K.pivot("window", loc, (0, 0, rot))
    fm = frame_mat or M.metal("aluminum", dirt=0.4)
    glass_m = M.emissive(warm, 1.1) if lit else M.plastic((0.012, 0.016, 0.02), 0.05)
    out = [K.box((w + 0.06, 0.03, h + 0.06), (0, 0.005, 0), fm, bevel=0.006),
           K.box((w, 0.035, h), (0, 0.0, 0), glass_m, bevel=0.002),
           K.box((0.025, 0.04, h), (0, 0, 0), fm, bevel=0.003)]
    group(out, p)
    return out


def roller_door(loc, w, h, facing="-y", mat=None):
    """Roll-up shutter door with box header (loc = bottom centre of the door opening)."""
    rot = {"-y": 0.0, "+x": math.pi / 2}[facing]
    p = K.pivot("door", loc, (0, 0, rot))
    mat = mat or M.scanned("painted_metal_shutter", 1.0, metallic=0.6, bump=0.8, name="shutter")
    out = [K.box((w, 0.04, h), (0, -0.01, h / 2), mat, bevel=0.004),
           K.box((w + 0.2, 0.3, 0.3), (0, -0.12, h + 0.12), M.metal("dark_steel", dirt=0.6), bevel=0.01),
           K.box((0.08, 0.1, h), (-w / 2 - 0.04, -0.04, h / 2), M.hazard(8.0), bevel=0.004),
           K.box((0.08, 0.1, h), (w / 2 + 0.04, -0.04, h / 2), M.hazard(8.0), bevel=0.004)]
    # horizontal slat lines
    for i in range(1, int(h / 0.12)):
        out.append(K.box((w * 0.99, 0.006, 0.008), (0, -0.033, i * 0.12), M.metal("dark_steel"), bevel=0))
    group(out, p)
    return out


def pipe(points, r=0.06, mat=None, flanges=True, bend=None):
    return K.pipe_run(points, r, mat, flanges, bend)


def rail_track(x0, x1, y, st, gauge_w=1.0, ballast=True):
    """Standard-ish rail track along X at row y (sleepers, rails, ballast)."""
    out = []
    L = x1 - x0
    if ballast:
        out.append(frustum((L, gauge_w + 1.0), (L, gauge_w + 0.6), 0.12, ((x0 + x1) / 2, y, 0),
                           M.concrete(1.5, tint=(0.55, 0.52, 0.48), tex="concrete_floor_worn_001"), bevel=0.01, name="ballast"))
    wood = M.plastic((0.06, 0.045, 0.03), 0.85, name="sleeper") if st.tier < 3 else M.concrete(1.0)
    n = int(L / 0.6)
    for i in range(n):
        x = x0 + (i + 0.5) * L / n
        out.append(K.box((0.22, gauge_w + 0.55, 0.1), (x, y, 0.12), wood, bevel=0.01, base=True, name="sleeper"))
    rail_m = M.metal("steel", rough=0.25, dirt=0.4)
    for s in (-1, 1):
        prof = [(-0.04, 0), (0.04, 0), (0.04, 0.015), (0.012, 0.03), (0.012, 0.09), (0.03, 0.1), (0.03, 0.13),
                (-0.03, 0.13), (-0.03, 0.1), (-0.012, 0.09), (-0.012, 0.03), (-0.04, 0.015)]
        r = K.prism(prof, L, ((x0 + x1) / 2, y + s * gauge_w / 2, 0.22), rail_m, rot=(0, 0, math.pi / 2), bevel=0.002, name="rail")
        out.append(r)
    return out


def robot_arm(base, scale=1.0, mat=None, an=None, yaw=None, shoulder=None, elbow=None, tool_glow=None):
    """Floor-mounted articulated robot (yaw / shoulder / elbow), reach ~1.1*scale m.

    Angles are functions of t (radians). Returns (tip_world_rest, glow_socket|None)."""
    s = scale
    b = Vector(base)
    mat = mat or M.painted((0.75, 0.42, 0.02), wear=0.25, grime=0.3, name="robot_orange")
    dark = M.metal("dark_steel", dirt=0.4)
    K.cyl(0.2 * s, 0.06 * s, b, dark, verts=24, bevel=0.006)
    turret = [K.cyl(0.16 * s, 0.22 * s, b + Vector((0, 0, 0.06 * s)), mat, verts=24, name="robot_turret"),
              K.box((0.22 * s, 0.26 * s, 0.16 * s), b + Vector((0.02 * s, 0, 0.3 * s)), mat, bevel=0.02 * s)]
    sp_loc = b + Vector((0.04 * s, 0, 0.34 * s))
    upper = [K.cyl(0.09 * s, 0.3 * s, sp_loc, dark, rot=(math.pi / 2, 0, 0), verts=20, base=False),
             K.box((0.13 * s, 0.14 * s, 0.6 * s), sp_loc + Vector((0, -0.0, 0.3 * s)), mat, bevel=0.025 * s, name="upper_arm"),
             K.cyl(0.07 * s, 0.12 * s, sp_loc + Vector((0, -0.12 * s, 0)), mat, rot=(math.pi / 2, 0, 0), verts=20, base=False)]
    ep_loc = sp_loc + Vector((0, 0, 0.6 * s))
    fore = [K.cyl(0.075 * s, 0.22 * s, ep_loc, dark, rot=(math.pi / 2, 0, 0), verts=20, base=False),
            K.box((0.5 * s, 0.11 * s, 0.11 * s), ep_loc + Vector((0.22 * s, 0, 0.02 * s)), mat, bevel=0.02 * s, name="forearm"),
            K.box((0.16 * s, 0.13 * s, 0.13 * s), ep_loc + Vector((-0.06 * s, 0, 0.03 * s)), mat, bevel=0.02 * s),
            K.cyl(0.04 * s, 0.12 * s, ep_loc + Vector((0.5 * s, 0, 0.02 * s)), dark, rot=K.AXES["x"], verts=16, base=True),
            KI_strut(ep_loc + Vector((0.6 * s, 0, 0.02 * s)), ep_loc + Vector((0.72 * s, 0, -0.1 * s)), 0.018 * s, M.metal("copper", dirt=0.4))]
    tip = ep_loc + Vector((0.73 * s, 0, -0.11 * s))
    sock = None
    if tool_glow is not None:
        gm, sock = anim_emit(tool_glow, 20.0, "weld_arc", base=(0.8, 0.8, 1.0))
        fore.append(K.sphere(0.025 * s, tip, gm, segs=12, rings=6))
    yp = K.pivot("robot_yaw", b)
    sp = K.pivot("robot_shoulder", sp_loc)
    ep = K.pivot("robot_elbow", ep_loc)
    bind(fore, ep)
    bind(upper + [ep], sp)
    bind(turret + [sp], yp)
    if an is not None:
        if yaw:
            an.rotate(yp, yaw, "Z")
        if shoulder:
            an.rotate(sp, shoulder, "Y")
        if elbow:
            an.rotate(ep, elbow, "Y")
    return tip, sock


def KI_strut(a, b, r, mat):
    return strut(a, b, r, mat, verts=8)


# --------------------------------------------------------------------------- framing
def bounds_points(rig=None, times=(0.0,)):
    """World points that bound every visible part (and its shadow tip) in the iso view, sampled
    at several loop phases. Feed to Rig.extra_points so overhanging/moving parts never clip."""
    import studio
    right, up, _ = studio.iso_basis()
    sd = studio.sun_dir()
    best = {}
    for t in times:
        if rig is not None:
            rig.update(t)
        bpy.context.view_layer.update()
        for o in K.collection().all_objects:
            if o.type not in ("MESH", "CURVE") or o.hide_render:
                continue
            mw = o.matrix_world
            for c in o.bound_box:
                p_ = mw @ Vector(c)
                q = p_ + sd * (p_.z / -sd.z) if p_.z > 0.01 else p_
                for i, v in enumerate((p_.dot(right), p_.dot(up), q.dot(right), q.dot(up))):
                    if (i, 1) not in best or v > best[(i, 1)][0]:
                        best[(i, 1)] = (v, p_.copy())
                    if (i, 0) not in best or v < best[(i, 0)][0]:
                        best[(i, 0)] = (v, p_.copy())
    if rig is not None:
        rig.update(0.0)
    return [tuple(v[1]) for v in best.values()]


def with_bounds(table):
    """Wrap archetype builders so their Rig.extra_points include bounds_points()."""
    def wrap(fn):
        def inner(spec, params):
            rig = fn(spec, params)
            try:
                times = (0.0,) if rig.frames <= 1 else (0.0, 0.25, 0.5, 0.75)
                rig.extra_points = list(rig.extra_points) + bounds_points(rig, times)
            except Exception as e:  # never fail a render because of framing
                print("[bounds] skipped:", e)
            return rig
        inner.__name__ = fn.__name__
        inner.__doc__ = fn.__doc__
        return inner
    return {k: wrap(v) for k, v in table.items()}
