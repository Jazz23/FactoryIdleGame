"""Shared helpers for plant / machine archetypes (assembly, chemistry, research, power).

Builds on kit.py (primitives) and materials.py (PBR):

* Style  - tier / paint / accent / glow / variant  ->  palette + weathering + materials
* Plant  - per-build context: footprint, style, animation, lights, emitters, final Rig.
           ``orient_long_x()`` lets a long machine follow the long side of any footprint.
* parts  - plinths, panel housings, doors, signs, stack lights, vessels, drums, valves, pumps,
           gauges, conveyors, robot arms, SCARA arms, gantries, platforms, cables, lattices ...
* anim   - spin / blink / pulse helpers that loop seamlessly over t in [0, 1).

Conventions: parts are built in LOCAL coordinates and grouped under pivots with ``group()``
(identity parent inverse), so they stay correct regardless of depsgraph evaluation state.
Visible faces are -Y (screen-left, lit) and +X (screen-right); face-mounted parts are built
facing -Y and rotated by FACE_ROT (``"-y": 0``, ``"+x": +90 deg``).
"""
import math
import random
import zlib

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

import kit as K
import materials as M
from buildings import Rig

TAU = 2.0 * math.pi
V = Vector
FACE_ROT = {"-y": 0.0, "+x": math.pi / 2, "+y": math.pi, "-x": -math.pi / 2}


# =========================================================================== housekeeping
def purge_stale_materials():
    """materials._cache survives studio.reset(); drop entries whose datablock was freed."""
    for k, m in list(M._cache.items()):
        try:
            m.name
        except ReferenceError:
            del M._cache[k]


def flat(items):
    if items is None:
        return
    if isinstance(items, (list, tuple, set)):
        for i in items:
            yield from flat(i)
    elif isinstance(items, bpy.types.Object):
        yield items


def parent(children, par):
    """Parent with identity inverse: children's transforms are in par's local space."""
    for c in flat(children):
        c.parent = par
        c.matrix_parent_inverse = Matrix.Identity(4)
    return par


def group(objs, loc=(0, 0, 0), rot_z=0.0, name="group", rot=None):
    """Put the top-level ancestors of objs under a new pivot at loc (objs built in local coords)."""
    piv = K.pivot(name, loc, rot if rot is not None else (0, 0, rot_z))
    tops = []
    for o in flat(objs):
        r = o
        while r.parent is not None:
            r = r.parent
        if r is not piv and r not in tops:
            tops.append(r)
    parent(tops, piv)
    return piv


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def wave(t, k=1, phase=0.0):
    """0..1 cosine wave, k whole cycles per loop (seamless)."""
    return 0.5 - 0.5 * math.cos(TAU * (t * k + phase))


def blink(t, k=1, duty=0.5, phase=0.0):
    return 1.0 if ((t * k + phase) % 1.0) < duty else 0.0


def lerp(a, b, u):
    return a + (b - a) * u


# =========================================================================== style
PALETTES = {
    # family: tier: (paint, accent, glow)   -- LINEAR rgb
    "machine": {
        1: ((0.062, 0.064, 0.055), (0.42, 0.2, 0.02), (1.0, 0.55, 0.15)),
        2: ((0.75, 0.42, 0.02), (0.035, 0.037, 0.04), (0.25, 1.0, 0.35)),
        3: ((0.03, 0.09, 0.24), (0.42, 0.44, 0.46), (0.25, 0.75, 1.0)),
        4: ((0.7, 0.71, 0.7), (0.022, 0.024, 0.028), (0.3, 0.8, 1.0)),
    },
    "process": {
        1: ((0.055, 0.06, 0.05), (0.32, 0.12, 0.03), (1.0, 0.55, 0.15)),
        2: ((0.045, 0.16, 0.065), (0.75, 0.45, 0.02), (0.3, 1.0, 0.4)),
        3: ((0.42, 0.44, 0.46), (0.03, 0.09, 0.24), (0.25, 0.75, 1.0)),
        4: ((0.72, 0.72, 0.7), (0.022, 0.024, 0.028), (0.35, 0.85, 1.0)),
    },
    "power": {
        1: ((0.07, 0.058, 0.045), (0.35, 0.15, 0.03), (1.0, 0.5, 0.12)),
        2: ((0.045, 0.12, 0.06), (0.75, 0.45, 0.02), (0.35, 1.0, 0.4)),
        3: ((0.32, 0.34, 0.37), (0.03, 0.1, 0.26), (0.3, 0.75, 1.0)),
        4: ((0.7, 0.71, 0.7), (0.022, 0.024, 0.028), (0.3, 0.75, 1.0)),
    },
}

TIER_LOOK = {
    1: dict(wear=0.8, grime=0.95, rust=0.5, rough=0.58, coat=0.0),
    2: dict(wear=0.5, grime=0.62, rust=0.18, rough=0.46, coat=0.0),
    3: dict(wear=0.2, grime=0.3, rust=0.03, rough=0.38, coat=0.2),
    4: dict(wear=0.05, grime=0.1, rust=0.0, rough=0.3, coat=0.6),
}
FRAME_COL = {1: (0.04, 0.04, 0.038), 2: (0.045, 0.047, 0.05), 3: (0.16, 0.17, 0.18), 4: (0.03, 0.031, 0.035)}
PIPE_COL = {1: (0.12, 0.11, 0.1), 2: (0.3, 0.3, 0.28), 3: (0.5, 0.52, 0.54), 4: (0.66, 0.67, 0.67)}
ROBOT_COL = {1: (0.5, 0.2, 0.03), 2: (0.85, 0.3, 0.02), 3: (0.8, 0.52, 0.02), 4: (0.74, 0.75, 0.74)}


def _rgb(v):
    return tuple(float(x) for x in list(v)[:3])


# Building params colours (paint / accent / glow) are passed to materials as LINEAR rgb, per
# docs/ART_PIPELINE.md (kit_industry does the same). Flip to True if the content palette is
# meant as display/sRGB values.
PARAM_SRGB = False


def param_color(v):
    c = _rgb(v)
    if PARAM_SRGB:
        c = tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
    return c


class Style:
    def __init__(self, params, family="machine", palette=None):
        params = params or {}
        try:
            tier = int(params.get("tier", 2))
        except (TypeError, ValueError):
            tier = 2
        self.raw_tier = tier
        self.tier = max(1, min(4, tier))
        pal = dict(PALETTES.get(family, PALETTES["machine"]))
        if palette:
            pal.update(palette)
        paint, accent, glow = pal[self.tier]
        self.paint = param_color(params["paint"]) if params.get("paint") else paint
        self.accent = param_color(params["accent"]) if params.get("accent") else accent
        self.glow = _rgb(params["glow"]) if params.get("glow") else glow
        look = TIER_LOOK[self.tier]
        self.wear, self.grime, self.rust = look["wear"], look["grime"], look["rust"]
        self.rough, self.coat = look["rough"], look["coat"]
        self.variant = str(params.get("variant") or "")
        self.smoke = params.get("smoke", True)
        self.rnd = random.Random(zlib.crc32((family + "/" + self.variant).encode()))
        self.hi = self.tier >= 4          # high-tech: LED accents
        self.clean = self.tier >= 3

    # --- materials
    def paint_m(self, color, k=1.0, name="paint", rough=None, under="steel", coat=None):
        return M.painted(tuple(color), wear=min(1.0, self.wear * k), grime=min(1.0, self.grime * k),
                         rough=self.rough if rough is None else rough, under=under,
                         gloss_coat=self.coat if coat is None else coat, rust=min(1.0, self.rust * k), name=name)

    @property
    def body(self):
        return self.paint_m(self.paint, name="body_paint")

    @property
    def accent_m(self):
        return self.paint_m(self.accent, 0.9, name="accent_paint")

    @property
    def frame(self):
        return self.paint_m(FRAME_COL[self.tier], 1.1, name="frame_paint")

    @property
    def dark(self):
        return self.paint_m((0.022, 0.022, 0.024), 0.8, name="dark_paint")

    @property
    def light_grey(self):
        return self.paint_m((0.5, 0.51, 0.5), 0.8, name="lgrey_paint")

    @property
    def pipe(self):
        return self.paint_m(PIPE_COL[self.tier], 1.0, name="pipe_paint")

    @property
    def robot_col(self):
        return ROBOT_COL[self.tier]

    def metal(self, kind="steel", rough=None):
        return M.metal(kind, rough=rough, dirt=0.15 + 0.6 * self.grime)

    @property
    def rubber(self):
        return M.rubber()

    @property
    def grating(self):
        return M.tread_plate(0.8, rust=self.tier <= 2)

    def concrete(self, scale=0.35, tint=None):
        if tint is None:
            tint = {1: (0.85, 0.82, 0.78), 2: (0.95, 0.93, 0.9), 3: (1.05, 1.05, 1.05), 4: (1.2, 1.2, 1.2)}[self.tier]
        return M.concrete(scale, tint=tint)


# =========================================================================== extra materials
_mcache = {}


def _cached(key, fn):
    m = _mcache.get(key)
    if m is not None:
        try:
            m.name
            return m
        except ReferenceError:
            pass
    m = fn()
    _mcache[key] = m
    return m


def glow_mat(color, strength=6.0, base=None, name="glow_anim"):
    """Unique emissive material; returns (mat, strength_socket) for animation."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*_rgb(base or color), 1)
    p.inputs["Emission Color"].default_value = (*_rgb(color), 1)
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Roughness"].default_value = 0.2
    p.inputs["Coat Weight"].default_value = 0.5
    return m, p.inputs["Emission Strength"]


def window_mat(inner, strength=0.35, tint=(0.015, 0.018, 0.022), noise=True, name="window"):
    """Glossy dark viewing window with a dimly lit interior (emission brighter toward the top,
    blotchy like out-of-focus machinery). Returns (mat, strength socket)."""
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(5.0)
    p.inputs["Base Color"].default_value = (*_rgb(tint), 1)
    p.inputs["Roughness"].default_value = 0.05
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.02
    p.inputs["Emission Color"].default_value = (*_rgb(inner), 1)
    mul = t.node("ShaderNodeMath", operation="MULTIPLY")
    mul.inputs[1].default_value = strength
    if noise:
        n = t.noise(vec, 0.8, 2, 0.4)
        k = t.maprange(n, 0.3, 0.7, 0.6, 1.1)
        tc = t.node("ShaderNodeTexCoord")
        sep = t.node("ShaderNodeSeparateXYZ")
        t.link(tc.outputs["Generated"], sep.inputs[0])
        grad = t.maprange(sep.outputs["Z"], 0.0, 1.0, 0.45, 1.25)
        t.link(t.math("MULTIPLY", k, grad), mul.inputs[0])
    else:
        mul.inputs[0].default_value = 1.0
    t.link(mul.outputs[0], p.inputs["Emission Strength"])
    return m, mul.inputs[1]


def clear_panel(tint=(0.86, 0.9, 0.92), name="clear_panel"):
    """Thin glazing / polycarbonate: transparent (passes shadow rays, unlike refractive glass)
    mixed with a white glossy layer by Fresnel, so lit interiors stay visible behind it."""
    def make():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        nodes = nt.nodes
        out = nodes["Material Output"]
        for n in list(nodes):
            if n.type == "BSDF_PRINCIPLED":
                nodes.remove(n)
        tr = nodes.new("ShaderNodeBsdfTransparent")
        tr.inputs["Color"].default_value = (*_rgb(tint), 1)
        gl = nodes.new("ShaderNodeBsdfGlossy")
        gl.inputs["Color"].default_value = (1, 1, 1, 1)
        gl.inputs["Roughness"].default_value = 0.03
        fr = nodes.new("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value = 2.0
        # backfaces (ray leaving the thin pane) would hit total internal reflection -> mask them
        geo = nodes.new("ShaderNodeNewGeometry")
        inv = nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(geo.outputs["Backfacing"], inv.inputs[1])
        mul = nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(fr.outputs[0], mul.inputs[0])
        nt.links.new(inv.outputs[0], mul.inputs[1])
        mix = nodes.new("ShaderNodeMixShader")
        nt.links.new(mul.outputs[0], mix.inputs["Fac"])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(gl.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        return m
    return _cached(("clear", tuple(tint)), make)


def fluid_glow(color, strength=3.0, scale=8.0, name="fluid"):
    """Bubbly glowing liquid / plasma (voronoi bubbles). Returns (mat, strength socket)."""
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(scale)
    vor = t.node("ShaderNodeTexVoronoi")
    t.link(vec, vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 3.0
    bub = t.maprange(vor.outputs["Distance"], 0.05, 0.4, 1.6, 0.6)
    n = t.maprange(t.noise(vec, 1.5, 3, 0.5), 0.3, 0.7, 0.7, 1.2)
    k = t.math("MULTIPLY", bub, n)
    mul = t.node("ShaderNodeMath", operation="MULTIPLY")
    t.link(k, mul.inputs[0])
    mul.inputs[1].default_value = strength
    c = _rgb(color)
    p.inputs["Base Color"].default_value = (*[x * 0.4 for x in c], 1)
    p.inputs["Emission Color"].default_value = (*c, 1)
    t.link(mul.outputs[0], p.inputs["Emission Strength"])
    p.inputs["Roughness"].default_value = 0.1
    p.inputs["Coat Weight"].default_value = 1.0
    return m, mul.inputs[1]


def pv_mat(tier=2):
    """Photovoltaic module: dark blue cells, silver busbars, glass coat."""
    def make():
        m, t = M._new("pv_cells")
        p = t.bsdf()
        tc = t.node("ShaderNodeTexCoord")
        br = t.node("ShaderNodeTexBrick")
        t.link(tc.outputs["Object"], br.inputs["Vector"])
        br.offset = 0.0
        br.squash = 1.0
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = 0.156
        br.inputs["Row Height"].default_value = 0.156
        br.inputs["Mortar Size"].default_value = 0.006
        br.inputs["Mortar Smooth"].default_value = 0.0
        br.inputs["Bias"].default_value = 0.0
        cell = (0.008, 0.014, 0.05) if tier <= 2 else (0.006, 0.008, 0.02)
        br.inputs["Color1"].default_value = (*cell, 1)
        br.inputs["Color2"].default_value = (*[c * 1.25 for c in cell], 1)
        br.inputs["Mortar"].default_value = (0.55, 0.56, 0.58, 1)
        # fine finger lines across each cell
        wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
        t.link(tc.outputs["Object"], wv.inputs["Vector"])
        wv.inputs["Scale"].default_value = 18.0
        fingers = t.maprange(wv.outputs["Factor"], 0.92, 0.98, 0.0, 0.25)
        col = t.mix_color(fingers, br.outputs["Color"], (0.4, 0.42, 0.45))
        _dirt = t.maprange(t.noise(t.coords(1.0), 2.0, 5, 0.6), 0.5, 0.8, 0.0, 0.25 if tier <= 2 else 0.05)
        col = t.mix_color(_dirt, col, (0.12, 0.1, 0.08))
        M._set(p, "Base Color", col)
        M._set(p, "Metallic", br.outputs["Fac"])
        p.inputs["Roughness"].default_value = 0.25
        p.inputs["Coat Weight"].default_value = 1.0
        p.inputs["Coat Roughness"].default_value = 0.03
        return m
    return _cached(("pv", tier), make)


def frost_mat():
    def make():
        m, t = M._new("frost")
        p = t.bsdf()
        vec = t.coords(12.0)
        n = t.noise(vec, 4.0, 8, 0.7)
        col = t.mix_color(t.maprange(n, 0.35, 0.7), (0.62, 0.66, 0.7), (0.85, 0.88, 0.9))
        M._set(p, "Base Color", col)
        p.inputs["Roughness"].default_value = 0.75
        p.inputs["Subsurface Weight"].default_value = 0.2
        t.link(t.bump(n, 0.6, 0.01), p.inputs["Normal"])
        return m
    return _cached("frost", make)


def porcelain(color=(0.18, 0.08, 0.03)):
    return M.plastic(color, 0.12, name="porcelain")


def led(color, strength=8.0):
    return M.emissive(_rgb(color), strength)


# =========================================================================== animation
class Anim:
    """Collects per-frame callables; call with t in [0, 1)."""

    def __init__(self):
        self.fns = []
        self.animated = False

    def add(self, fn):
        self.fns.append(fn)
        self.animated = True
        return fn

    def __call__(self, t):
        for f in self.fns:
            f(t)

    def spin(self, obj, turns=1.0, axis=(0, 0, 1), phase=0.0):
        """Rotate obj about its LOCAL axis by `turns` full turns per loop (use 1/symmetry multiples)."""
        base = obj.rotation_euler.to_quaternion() if obj.rotation_mode != "QUATERNION" else obj.rotation_quaternion.copy()
        obj.rotation_mode = "QUATERNION"
        ax = V(axis).normalized()

        def f(t):
            obj.rotation_quaternion = base @ Quaternion(ax, TAU * (turns * t + phase))
        f(0.0)
        return self.add(f)

    def socket(self, sock, fn):
        """sock.default_value = fn(t)."""
        def f(t):
            sock.default_value = fn(t)
        f(0.0)
        return self.add(f)

    def blink(self, sock, on, off=0.0, k=1, duty=0.5, phase=0.0):
        return self.socket(sock, lambda t: on if blink(t, k, duty, phase) else off)

    def pulse(self, sock, lo, hi, k=1, phase=0.0):
        return self.socket(sock, lambda t: lo + (hi - lo) * wave(t, k, phase))

    def light(self, ldata, fn):
        def f(t):
            ldata.energy = fn(t)
        f(0.0)
        return self.add(f)


# =========================================================================== build context
class Plant:
    """Per-building context. Typical use::

        P = Plant(spec, params, "machine")
        L, S = P.orient_long_x()   # optional: local X follows the long side
        ... build in local coords (footprint L x S centred on origin) ...
        return P.finish(height, frames=16, fps=12)
    """

    def __init__(self, spec, params, family="machine", palette=None, wear=1.0):
        purge_stale_materials()
        size = spec.get("size") or [3, 3]
        self.w, self.d = float(size[0]), float(size[1])
        self.L, self.S = self.w, self.d
        self.st = Style(params, family, palette)
        self.st.wear *= wear
        self.st.rust *= wear
        self.st.grime *= 0.5 + 0.5 * wear
        self.tier = self.st.tier
        self.anim = Anim()
        self.lights, self.emitters, self.extra = [], [], []
        self.rot = 0.0
        self.rnd = self.st.rnd

    @property
    def m(self):
        """Smaller footprint side (handy scale reference)."""
        return min(self.L, self.S)

    def orient_long_x(self):
        if self.d > self.w + 1e-6:
            self.rot = math.pi / 2
            self.L, self.S = self.d, self.w
        return self.L, self.S

    def point_light(self, loc, color, energy, radius=0.15, export=1.0, flicker=False, export_light=True):
        d = bpy.data.lights.new("glow", "POINT")
        d.energy = energy
        d.color = _rgb(color)
        d.shadow_soft_size = radius
        o = bpy.data.objects.new("glow", d)
        K.collection().objects.link(o)
        o.location = V(loc)
        if export_light:
            self.lights.append({"pos": list(V(loc)), "color": list(_rgb(color)), "energy": export, "flicker": flicker})
        return d

    def export_light(self, loc, color, energy=1.0, flicker=False):
        self.lights.append({"pos": list(V(loc)), "color": list(_rgb(color)), "energy": energy, "flicker": flicker})

    def emitter(self, loc, kind="steam"):
        self.emitters.append({"pos": list(V(loc)), "type": kind})

    def finish(self, height, frames=16, fps=12, still=False):
        if self.rot:
            root = K.pivot("root", (0, 0, 0), (0, 0, self.rot))
            tops = [o for o in K.collection().objects if o.parent is None and o is not root]
            parent(tops, root)
            R = Matrix.Rotation(self.rot, 3, "Z")
            for item in self.lights + self.emitters:
                item["pos"] = list(R @ V(item["pos"]))
            self.extra = [tuple(R @ V(p)) for p in self.extra]
        for item in self.lights + self.emitters:
            item["pos"] = [round(float(x), 3) for x in item["pos"]]
        animated = self.anim.animated and not still
        return Rig(height=height, frames=frames if animated else 1, fps=fps, update=self.anim,
                   extra_points=self.extra, lights=self.lights, emitters=self.emitters)


# =========================================================================== geometry helpers
def rod(a, b, r, mat, verts=12, bevel=0.0, name="rod"):
    """Cylinder from point a to point b."""
    a, b = V(a), V(b)
    d = b - a
    o = K.cyl(r, d.length, (0, 0, 0), mat, verts=verts, bevel=bevel, base=True, name=name)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = V((0, 0, 1)).rotation_difference(d.normalized())
    o.location = a
    return o


def bar(a, b, w, h, mat, bevel=0.004, name="bar"):
    """Rectangular bar from a to b (w across, h up)."""
    a, b = V(a), V(b)
    d = b - a
    o = K.box((d.length, w, h), (0, 0, 0), mat, bevel=bevel, name=name)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = V((1, 0, 0)).rotation_difference(d.normalized())
    o.location = (a + b) / 2
    return o


def disc(r, h, loc, mat, axis="z", verts=32, bevel=0.004, name="disc"):
    return K.cyl(r, h, loc, mat, rot=K.AXES[axis], verts=verts, bevel=bevel, base=False, name=name)


def ellip_head(r, loc, mat, k=0.5, up=True, segs=40):
    """2:1 ellipsoidal vessel head (full ellipsoid; the inner half hides in the shell)."""
    return K.sphere(r, loc, mat, segs=segs, rings=16, scale=(1, 1, k), name="head")


# =========================================================================== base / plinth
def plinth(P, w=None, d=None, h=None, style=None):
    """Foundation for the whole footprint. Tier 1-2: steel skid on tread plate; 3-4: concrete pad
    with steel kerb angle (+ LED edge on tier 4). Returns top z."""
    st = P.st
    w = w if w is not None else P.L * 0.97
    d = d if d is not None else P.S * 0.97
    style = style or ("skid" if st.tier <= 2 else "pad")
    if style == "skid":
        _, z = K.skid(w, d, h or 0.16, paint=FRAME_COL[st.tier] if st.tier > 1 else (0.06, 0.05, 0.04))
        return z
    h = h or 0.12
    K.box((w, d, h), (0, 0, 0), st.concrete(0.3), bevel=0.02, base=True, name="pad")
    kerb = st.paint_m((0.2, 0.21, 0.22) if st.tier == 3 else (0.03, 0.031, 0.035), 0.7, name="kerb")
    for sy in (-1, 1):
        K.box((w + 0.02, 0.04, 0.03), (0, sy * d / 2, h - 0.015), kerb, bevel=0.004)
    for sx in (-1, 1):
        K.box((0.04, d + 0.02, 0.03), (sx * w / 2, 0, h - 0.015), kerb, bevel=0.004)
    if st.tier == 3:
        K.hazard_edge(w - 0.1, d - 0.1, h, width=0.05, h=0.004)
    if st.hi:
        g = led(st.glow, 4.0)
        K.box((w - 0.08, 0.012, 0.012), (0, -d / 2 - 0.006, h * 0.5), g, bevel=0)
        K.box((0.012, d - 0.08, 0.012), (w / 2 + 0.006, 0, h * 0.5), g, bevel=0)
    return h


def floor_markings(P, w, d, z, inset=0.08):
    """Painted floor safety line around a work area (tier >= 2)."""
    col = (0.75, 0.55, 0.02) if P.tier <= 3 else (0.6, 0.62, 0.62)
    m = M.painted(col, wear=0.7, grime=0.6, rough=0.6, under="steel", rust=0.0, name="floorline")
    out = []
    for sy in (-1, 1):
        out.append(K.box((w, 0.05, 0.003), (0, sy * (d / 2 - inset), z + 0.0015), m, bevel=0))
    for sx in (-1, 1):
        out.append(K.box((0.05, d - 2 * inset, 0.003), (sx * (w / 2 - inset), 0, z + 0.0015), m, bevel=0))
    return out


# =========================================================================== housings & panels
def housing(P, size, loc, mat=None, seams=None, posts=True, roof=True, kick=True, faces=("-y", "+x")):
    """Machine enclosure: body, corner posts, panel seams on visible faces, roof lip, kick plate.
    loc = bottom centre. Returns body object."""
    st = P.st
    w, d, h = size
    c = V(loc)
    mat = mat or st.body
    body = K.box((w, d, h), c, mat, bevel=0.02, base=True, name="housing")
    seam_m = M.plastic((0.012, 0.012, 0.013), 0.6, name="seam")
    if seams is None:
        seams = max(1, int(round(max(w, d) / 0.9)))
    if "-y" in faces:
        n = max(1, int(round(w / 0.85)))
        for i in range(1, n):
            x = -w / 2 + w * i / n
            K.box((0.012, 0.006, h * 0.94), c + V((x, -d / 2 - 0.001, h * 0.03)), seam_m, bevel=0, base=True)
    if "+x" in faces:
        n = max(1, int(round(d / 0.85)))
        for i in range(1, n):
            y = -d / 2 + d * i / n
            K.box((0.006, 0.012, h * 0.94), c + V((w / 2 + 0.001, y, h * 0.03)), seam_m, bevel=0, base=True)
    if posts:
        pm = st.frame
        for sx in (-1, 1):
            for sy in (-1, 1):
                K.box((0.06, 0.06, h + 0.02), c + V((sx * (w / 2), sy * (d / 2), 0)), pm, bevel=0.008, base=True, name="post")
    if roof:
        K.box((w + 0.05, d + 0.05, 0.05), c + V((0, 0, h)), st.frame, bevel=0.012, base=True, name="roof_lip")
    if kick:
        K.box((w + 0.012, d + 0.012, 0.09), c, st.dark, bevel=0.006, base=True, name="kick")
    return body


def door(P, loc, rot_z=0.0, w=0.7, h=1.6, mat=None, window=False, handle_side=1):
    """Hinged service door (front faces -Y before rotation). loc = bottom centre on the wall."""
    st = P.st
    mat = mat or st.body
    out = [K.box((w, 0.03, h), (0, -0.015, 0), mat, bevel=0.01, base=True, name="door")]
    out.append(K.box((w + 0.04, 0.012, h + 0.04), (0, -0.004, -0.02), M.rubber(), bevel=0.003, base=True))
    hm = st.metal("stainless")
    for z in (h * 0.15, h * 0.85):
        out.append(K.cyl(0.018, 0.12, (-handle_side * w / 2, -0.035, z - 0.06), hm, verts=10))
    out.append(K.box((0.025, 0.03, 0.16), (handle_side * w * 0.38, -0.05, h * 0.5), hm, bevel=0.006))
    if window:
        out.append(K.box((w * 0.5, 0.012, h * 0.22), (0, -0.035, h * 0.72), M.glass((0.5, 0.6, 0.65), 0.05), bevel=0.004))
        out.append(K.box((w * 0.56, 0.008, h * 0.26), (0, -0.03, h * 0.72), st.dark, bevel=0.004))
    return group(out, loc, rot_z, "door")


def sign(loc, rot_z=0.0, kind="warn", s=0.16):
    """Face-mounted sticker/plate (front faces -Y before rotation)."""
    out = []
    if kind == "warn":
        tri = [(-s / 2, 0), (s / 2, 0), (0, s * 0.87)]
        out.append(K.prism(tri, 0.006, (0, 0, -s * 0.43), M.plastic((0.02, 0.02, 0.02), 0.5), bevel=0.002))
        tri2 = [(-s * 0.4, s * 0.06), (s * 0.4, s * 0.06), (0, s * 0.75)]
        out.append(K.prism(tri2, 0.006, (0, -0.002, -s * 0.43), M.plastic((0.85, 0.6, 0.02), 0.45), bevel=0.001))
        out.append(K.box((s * 0.05, 0.006, s * 0.3), (0, -0.004, -s * 0.43 + s * 0.38), M.plastic((0.02, 0.02, 0.02), 0.5), bevel=0))
    elif kind == "plate":
        out.append(K.box((s * 1.5, 0.006, s * 0.7), (0, 0, 0), M.metal("aluminum", dirt=0.3), bevel=0.002))
        out.append(K.box((s * 1.3, 0.006, s * 0.16), (0, -0.002, s * 0.15), M.plastic((0.03, 0.06, 0.16), 0.4), bevel=0))
        for i in range(3):
            out.append(K.box((s * (1.1 - 0.25 * i), 0.006, s * 0.05), (-s * 0.1 * i, -0.002, -s * 0.05 - i * s * 0.1),
                             M.plastic((0.05, 0.05, 0.05), 0.5), bevel=0))
    elif kind == "danger":
        out.append(K.box((s * 1.2, 0.006, s * 0.85), (0, 0, 0), M.plastic((0.85, 0.85, 0.82), 0.45), bevel=0.002))
        out.append(K.box((s * 1.2, 0.006, s * 0.28), (0, -0.002, s * 0.28), M.plastic((0.6, 0.02, 0.01), 0.4), bevel=0))
        for i in range(2):
            out.append(K.box((s * (0.9 - 0.3 * i), 0.006, s * 0.06), (0, -0.002, -s * 0.05 - i * s * 0.14),
                             M.plastic((0.03, 0.03, 0.03), 0.5), bevel=0))
    elif kind == "radiation":
        out.append(K.cyl(s * 0.5, 0.006, (0, 0, 0), M.plastic((0.85, 0.6, 0.02), 0.45), rot=K.AXES["-y"], verts=24, base=False))
        out.append(K.cyl(s * 0.1, 0.006, (0, -0.003, 0), M.plastic((0.02, 0.02, 0.02), 0.5), rot=K.AXES["-y"], verts=16, base=False))
        for i in range(3):
            a = math.radians(90 + i * 120)
            pts = [(0, 0)]
            for k in range(7):
                b = a - math.radians(30) + math.radians(60) * k / 6
                pts.append((math.cos(b) * s * 0.42, math.sin(b) * s * 0.42))
            prof = [(x, z) for x, z in pts[1:]] + [(math.cos(a + math.radians(30)) * s * 0.16, math.sin(a + math.radians(30)) * s * 0.16),
                                                    (math.cos(a - math.radians(30)) * s * 0.16, math.sin(a - math.radians(30)) * s * 0.16)]
            prof = list(reversed(prof))
            out.append(K.prism(prof, 0.006, (0, -0.003, 0), M.plastic((0.02, 0.02, 0.02), 0.5), bevel=0))
    for o in out:
        o.location.y -= 0.004
    return group(out, loc, rot_z, "sign")


def stack_light(P, loc, colors=None, anim=None, k=1, h_seg=0.07, r=0.035):
    """Andon signal tower: pole + red/amber/green lens segments. Animates by `anim` mode:
    None (green on), "run" (green steady, amber blinks), "cycle"."""
    colors = colors or [(1.0, 0.04, 0.02), (1.0, 0.45, 0.0), (0.1, 1.0, 0.2)]
    c = V(loc)
    dk = M.metal("dark_steel")
    out = [K.cyl(r * 0.9, 0.03, c, dk, verts=16), K.cyl(0.01, 0.12, c + V((0, 0, 0.03)), M.metal("stainless"), verts=8)]
    z = 0.15
    socks = []
    for i, col in enumerate(reversed(colors)):
        m, s = glow_mat(col, 0.0, base=tuple(x * 0.5 for x in col), name="stack_lens")
        out.append(K.cyl(r, h_seg, c + V((0, 0, z)), m, verts=20, bevel=0.003))
        out.append(K.cyl(r * 1.02, 0.008, c + V((0, 0, z + h_seg)), M.plastic((0.05, 0.05, 0.05), 0.4), verts=20, bevel=0))
        socks.append(s)
        z += h_seg + 0.008
    out.append(K.cyl(r * 0.95, 0.025, c + V((0, 0, z)), M.plastic((0.04, 0.04, 0.04), 0.4), verts=20, bevel=0.006))
    green, amber, red = socks[0], socks[1], socks[2]
    green.default_value = 9.0
    if anim == "run":
        P.anim.blink(amber, 10.0, 0.0, k=k * 2, duty=0.5)
    elif anim == "cycle":
        P.anim.blink(green, 9.0, 0.0, k=k, duty=0.6)
        P.anim.blink(amber, 9.0, 0.0, k=k, duty=0.4, phase=0.6)
    return out, z


def status_leds(P, loc, rot_z=0.0, n=4, colors=None, k=2, spacing=0.035, r=0.008, seed=0):
    """Row of small LEDs on a panel face (front -Y before rot), blinking pseudo-randomly."""
    rnd = random.Random(seed)
    colors = colors or [(0.1, 1.0, 0.25), (0.1, 1.0, 0.25), (1.0, 0.5, 0.0), (0.15, 0.5, 1.0)]
    out = []
    for i in range(n):
        col = colors[i % len(colors)]
        m, s = glow_mat(col, 6.0, base=tuple(x * 0.3 for x in col), name="led")
        out.append(K.cyl(r, 0.008, ((i - (n - 1) / 2) * spacing, -0.004, 0), m, rot=K.AXES["-y"], verts=10, bevel=0, base=False))
        if rnd.random() < 0.7:
            P.anim.blink(s, 7.0, 0.2, k=rnd.choice([1, 2, 2, 3, 4]), duty=rnd.uniform(0.3, 0.8), phase=rnd.random())
    return group(out, loc, rot_z, "leds")


def hmi_panel(P, loc, rot_z=0.0, w=0.45, h=0.32, screen_col=None, pedestal=True, z=1.0):
    """Operator panel: screen + buttons on a pedestal arm (front -Y)."""
    st = P.st
    screen_col = screen_col or ((0.25, 0.85, 1.0) if st.tier >= 3 else (0.3, 0.95, 0.5))
    out = []
    shell = st.paint_m((0.5, 0.51, 0.5) if st.tier < 4 else (0.04, 0.04, 0.045), 0.6, name="hmi")
    out.append(K.box((w, 0.08, h), (0, 0, z), shell, bevel=0.012))
    out.append(K.box((w * 0.66, 0.01, h * 0.6), (-w * 0.1, -0.042, z + h * 0.08), M.screen(screen_col, 2.2), bevel=0.002))
    for i, col in enumerate([(0.1, 0.9, 0.2), (0.9, 0.08, 0.04)]):
        out.append(K.cyl(0.018, 0.015, (w * 0.35, -0.045, z + h * 0.2 - i * 0.07), M.emissive(col, 3.0), rot=K.AXES["-y"], verts=12, base=False, bevel=0.002))
    out.append(K.cyl(0.03, 0.02, (w * 0.35, -0.045, z - h * 0.32), M.plastic((0.7, 0.03, 0.02), 0.3), rot=K.AXES["-y"], verts=16, base=False, bevel=0.004))
    if pedestal:
        out.append(K.cyl(0.03, z - h / 2, (0, 0.02, 0), st.metal("stainless"), verts=12))
        out.append(K.cyl(0.12, 0.02, (0, 0.02, 0), st.dark, verts=20))
    return group(out, loc, rot_z, "hmi")


def gauge(loc, rot_z=0.0, r=0.05):
    out = [K.cyl(r, 0.03, (0, 0, 0), M.plastic((0.9, 0.9, 0.88), 0.3), rot=K.AXES["-y"], verts=24, base=False, bevel=0.002),
           K.torus(r, r * 0.14, (0, -0.016, 0), M.metal("brass"), rot=K.AXES["y"]),
           K.box((r * 0.08, 0.004, r * 0.75), (r * 0.15, -0.018, r * 0.2), M.plastic((0.6, 0.02, 0.01), 0.4), rot=(0, 0.5, 0), bevel=0)]
    return group(out, loc, rot_z, "gauge")


def cabinet(P, loc, rot_z=0.0, w=0.6, d=0.35, h=1.4, paint=None, screen=True, leds=True, vents=True):
    """Electrical cabinet (front -Y before rotation): door seam, display, buttons, louvres, conduit."""
    st = P.st
    paint = paint or ((0.6, 0.61, 0.58) if st.tier <= 3 else (0.7, 0.71, 0.7))
    body_m = st.paint_m(paint, 0.5, name="cabinet_paint")
    out = [K.box((w, d, h), (0, 0, 0.08), body_m, bevel=0.015, base=True, name="cabinet")]
    out.append(K.box((w + 0.02, d + 0.02, 0.08), (0, 0, 0), st.dark, bevel=0.006, base=True))
    out.append(K.box((w + 0.03, d + 0.03, 0.03), (0, 0, h + 0.08), body_m, bevel=0.008, base=True))
    seam = M.plastic((0.015, 0.015, 0.015), 0.6)
    out.append(K.box((0.008, 0.004, h * 0.9), (0, -d / 2 - 0.001, 0.08 + h * 0.05), seam, bevel=0, base=True))
    hm = M.metal("dark_steel")
    for sx in (-1, 1):
        out.append(K.box((0.02, 0.025, 0.1), (sx * 0.05, -d / 2 - 0.012, 0.08 + h * 0.5), hm, bevel=0.004))
    if screen:
        out.append(K.box((w * 0.32, 0.012, h * 0.14), (-w * 0.22, -d / 2 - 0.005, 0.08 + h * 0.76), M.screen((0.25, 0.9, 0.6) if st.tier < 3 else (0.3, 0.8, 1.0), 2.2), bevel=0.002))
        out.append(K.box((w * 0.36, 0.01, h * 0.18), (-w * 0.22, -d / 2 - 0.002, 0.08 + h * 0.76), M.plastic((0.03, 0.03, 0.03), 0.4), bevel=0.004))
    if leds:
        cols = [(0.1, 1.0, 0.2), (1.0, 0.5, 0.0), (1.0, 0.05, 0.02)]
        for i, col in enumerate(cols):
            out.append(K.cyl(0.016, 0.015, (w * 0.18 + i * 0.05, -d / 2 - 0.005, 0.08 + h * 0.78), M.emissive(col, 3.0 if i != 2 else 0.4),
                             rot=K.AXES["-y"], verts=12, base=False, bevel=0.002))
    if vents:
        vm = M.plastic((0.05, 0.05, 0.055), 0.5)
        for i in range(4):
            out.append(K.box((w * 0.3, 0.01, 0.012), (w * 0.22, -d / 2 - 0.003, 0.08 + h * 0.12 + i * 0.03), vm, bevel=0))
    out.append(sign((-w * 0.22, -d / 2 - 0.004, 0.08 + h * 0.55), 0.0, "warn", 0.09))
    return group(out, loc, rot_z, "cabinet")


def louvre(loc, rot_z, w, h, mat=None, frame=None):
    """Louvred vent panel (front faces -Y)."""
    mat = mat or M.painted((0.25, 0.26, 0.27), wear=0.3, grime=0.5, name="louvre")
    out = [K.box((w + 0.04, 0.02, h + 0.04), (0, 0, 0), frame or M.metal("dark_steel", dirt=0.5), bevel=0.004)]
    out.append(K.box((w, 0.01, h), (0, 0.006, 0), M.plastic((0.01, 0.01, 0.01), 0.8), bevel=0))
    n = max(3, int(h / 0.055))
    for i in range(n):
        z = -h / 2 + (i + 0.5) * h / n
        s = K.box((w * 0.96, 0.01, h / n * 0.95), (0, -0.016, z), mat, bevel=0.002)
        s.rotation_euler = Euler((math.radians(-40), 0, 0), "XYZ")
        out.append(s)
    return group(out, loc, rot_z, "louvre")


def ladder(P, loc, h, rot_z=0.0, w=0.42, cage=False):
    """Fixed ladder (rungs along local X, stands off a wall facing -Y)."""
    mat = P.st.paint_m((0.75, 0.5, 0.02) if P.tier <= 2 else (0.5, 0.52, 0.54), 0.8, name="ladder_paint")
    out = [K.cyl(0.02, h, (-w / 2, 0, 0), mat, verts=10), K.cyl(0.02, h, (w / 2, 0, 0), mat, verts=10)]
    n = int(h / 0.3)
    for i in range(1, n + 1):
        out.append(K.cyl(0.013, w, (-w / 2, 0, i * 0.3), mat, rot=K.AXES["x"], verts=8, base=True))
    for z in (0.3, h - 0.2):
        for sx in (-1, 1):
            out.append(K.box((0.03, 0.12, 0.03), (sx * w / 2, 0.06, z), mat, bevel=0.004))
    if cage and h > 2.2:
        for k in range(int((h - 2.0) / 0.7) + 1):
            z = 2.0 + k * 0.7
            pts = [(-w / 2, 0, z)] + [(math.cos(a) * w * 0.65, -w * 0.15 - math.sin(a) * w * 0.65, z) for a in
                                      [math.pi - i * math.pi / 8 for i in range(9)]] + [(w / 2, 0, z)]
            out.append(K.tube(pts, 0.012, mat))
        for a in (math.pi * 0.25, math.pi * 0.5, math.pi * 0.75):
            p = (math.cos(a) * w * 0.65, -w * 0.15 - math.sin(a) * w * 0.65)
            out.append(K.cyl(0.01, h - 2.0, (p[0], p[1], 2.0), mat, verts=6))
    return group(out, loc, rot_z, "ladder")


def railing(P, pts, h=1.0, posts=1.0):
    mat = P.st.paint_m((0.75, 0.5, 0.02) if P.tier <= 3 else (0.6, 0.62, 0.62), 0.8, name="rail_paint")
    out = []
    pts = [V(p) for p in pts]
    out.append(K.tube([p + V((0, 0, h)) for p in pts], 0.021, mat))
    out.append(K.tube([p + V((0, 0, h * 0.5)) for p in pts], 0.016, mat))
    for a, b in zip(pts, pts[1:]):
        seg = b - a
        n = max(1, int(round(seg.length / posts)))
        for i in range(n + 1):
            out.append(K.cyl(0.02, h, a + seg * (i / n), mat, verts=10))
        # toe board
        mid = (a + b) / 2
        if abs(seg.x) > abs(seg.y):
            out.append(K.box((seg.length, 0.008, 0.1), mid + V((0, 0, 0.05)), mat, bevel=0.002))
        else:
            out.append(K.box((0.008, seg.length, 0.1), mid + V((0, 0, 0.05)), mat, bevel=0.002))
    return out


def platform(P, x0, x1, y0, y1, z, rails=("-y",), legs=True, beam=0.12):
    """Grating platform on steel legs with railings on the named edges."""
    st = P.st
    out = [K.box((x1 - x0, y1 - y0, 0.03), ((x0 + x1) / 2, (y0 + y1) / 2, z - 0.03), st.grating, bevel=0.004, base=True)]
    fm = st.frame
    for y in (y0, y1):
        out.append(K.box((x1 - x0, 0.05, beam), ((x0 + x1) / 2, y, z - 0.03 - beam), fm, bevel=0.005, base=True))
    for x in (x0, x1):
        out.append(K.box((0.05, y1 - y0, beam), (x, (y0 + y1) / 2, z - 0.03 - beam), fm, bevel=0.005, base=True))
    if legs:
        for x in (x0 + 0.04, x1 - 0.04):
            for y in (y0 + 0.04, y1 - 0.04):
                out.append(K.box((0.07, 0.07, z - 0.03 - beam), (x, y, 0), fm, bevel=0.006, base=True))
    edges = {"-y": [(x0, y0, z), (x1, y0, z)], "+y": [(x0, y1, z), (x1, y1, z)],
             "-x": [(x0, y0, z), (x0, y1, z)], "+x": [(x1, y0, z), (x1, y1, z)]}
    for e in rails:
        out += railing(P, edges[e], 1.0)
    return out


def cable(a, b, sag=0.15, r=0.016, mat=None, n=8):
    a, b = V(a), V(b)
    pts = [a.lerp(b, i / n) - V((0, 0, sag * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]
    return K.tube(pts, r, mat or M.rubber((0.02, 0.02, 0.022)))


# =========================================================================== process equipment
def vessel(P, loc, r, h, mat=None, legs=0.0, skirt=0.0, top=True, bottom=True, bands=2, manway=True,
           nozzles=2, insulated=False, face="-y", plate=True):
    """Vertical pressure vessel with 2:1 heads. loc = ground centre. Returns top-of-head z."""
    st = P.st
    c = V(loc)
    mat = mat or (st.metal("stainless") if st.tier >= 3 else st.body)
    out = []
    z0 = c.z + max(legs, skirt)
    if legs > 0:
        lm = st.frame
        for i in range(4):
            a = math.pi / 4 + i * math.pi / 2
            p = c + V((math.cos(a) * r * 0.82, math.sin(a) * r * 0.82, 0))
            out.append(K.cyl(0.045 + r * 0.03, legs + r * 0.25, p, lm, verts=12))
            out.append(K.box((0.16, 0.16, 0.015), p, lm, bevel=0.003, base=True))
    if skirt > 0:
        out.append(K.cyl(r * 0.98, skirt + 0.02, c, st.frame, verts=40, bevel=0.004))
        out.append(K.cyl(r * 1.12, 0.03, c, st.dark, verts=40, bevel=0.004))
    out.append(K.cyl(r, h, c + V((0, 0, z0 - c.z)), mat, verts=48, bevel=0.006, name="shell"))
    if bottom and skirt <= 0:
        out.append(ellip_head(r, c + V((0, 0, z0 - c.z)), mat))
    if top:
        out.append(ellip_head(r, c + V((0, 0, z0 - c.z + h)), mat))
    seam = st.metal("stainless" if st.tier >= 3 else "steel")
    for k in range(bands):
        zz = z0 + h * (k + 1) / (bands + 1)
        out.append(K.torus(r * 1.005, 0.012 if not insulated else 0.02, V((c.x, c.y, zz)), seam, segs=48, rsegs=8))
    fr = FACE_ROT[face]
    fdir = Matrix.Rotation(fr, 3, "Z") @ V((0, -1, 0))
    side = Matrix.Rotation(fr, 3, "Z") @ V((1, 0, 0))
    if manway and h > 0.9:
        mz = z0 + min(0.55, h * 0.3)
        p = c.xy.to_3d() + fdir * r + V((0, 0, mz))
        out.append(K.cyl(0.16, 0.12, p, mat, rot=_axis_rot(fdir), verts=24, base=False, bevel=0.006))
        out.append(K.cyl(0.21, 0.035, p + fdir * 0.07, mat, rot=_axis_rot(fdir), verts=28, base=False, bevel=0.006))
        for k in range(10):
            a = TAU * k / 10
            bp = p + fdir * 0.09 + side * math.cos(a) * 0.18 + V((0, 0, math.sin(a) * 0.18))
            out.append(K.cyl(0.012, 0.02, bp, M.metal("dark_steel"), rot=_axis_rot(fdir), verts=6, base=False, bevel=0))
        out.append(rod(p + fdir * 0.09 + side * 0.24 + V((0, 0, 0.1)), p + fdir * 0.09 + side * 0.24 - V((0, 0, 0.1)), 0.012, M.metal("steel")))
    fa = math.atan2(fdir.y, fdir.x)
    for k in range(nozzles):
        a = fa + (1 if k % 2 == 0 else -1) * math.radians(65 + 30 * (k // 2))
        dirv = V((math.cos(a), math.sin(a), 0))
        zz = z0 + h * (0.72 - 0.4 * (k % 2))
        p = c.xy.to_3d() + dirv * r + V((0, 0, zz))
        out.append(K.cyl(0.05, 0.14, p - dirv * 0.03, mat, rot=_axis_rot(dirv), verts=16, base=True, bevel=0.003))
        out += flange_d(p + dirv * 0.11, 0.05, dirv)
    if plate and h > 0.8:
        out.append(sign(c.xy.to_3d() + fdir * (r + 0.004) + V((0, 0, z0 + h * 0.65)) - side * r * 0.4, fr, "plate", 0.12))
    return z0 + h + r * 0.5, out


def _axis_rot(d):
    """Euler that maps local +Z onto direction d."""
    return V((0, 0, 1)).rotation_difference(V(d).normalized()).to_euler()


def flange_d(center, r_pipe, d, mat=None, thick=0.035):
    """Bolted flange facing direction d (any orientation)."""
    d = V(d).normalized()
    rot = _axis_rot(d)
    mat = mat or M.metal("cast_iron")
    out = [K.cyl(r_pipe * 1.75, thick, V(center), mat, rot=rot, verts=28, base=False, name="flange")]
    m3 = rot.to_matrix()
    n = 6 if r_pipe < 0.12 else 8
    for i in range(n):
        a = TAU * i / n
        p = V(center) + m3 @ V((math.cos(a) * r_pipe * 1.42, math.sin(a) * r_pipe * 1.42, thick / 2))
        out.append(K.cyl(max(0.011, r_pipe * 0.15), 0.014, p, M.metal("dark_steel"), rot=rot, verts=6, bevel=0.002, name="bolt"))
    return out


def _axis_name(d):
    d = V(d)
    ax = max((("x", abs(d.x)), ("y", abs(d.y)), ("z", abs(d.z))), key=lambda t: t[1])[0]
    return ax


def hdrum(P, loc, r, length, mat=None, axis="x", saddle_h=0.25, bands=2, nozzles=2):
    """Horizontal drum on two saddles. loc = ground centre. Returns top z."""
    st = P.st
    mat = mat or (st.metal("stainless") if st.tier >= 3 else st.body)
    c = V(loc)
    zc = c.z + saddle_h + r
    rot = K.AXES["x"] if axis == "x" else K.AXES["y"]
    ax = V((1, 0, 0)) if axis == "x" else V((0, 1, 0))
    perp = V((0, 1, 0)) if axis == "x" else V((1, 0, 0))
    out = [K.cyl(r, length, V((c.x, c.y, zc)), mat, rot=rot, verts=48, base=False, bevel=0.006, name="drum")]
    for s in (-1, 1):
        h = K.sphere(r, V((c.x, c.y, zc)) + ax * s * length / 2, mat, segs=40, rings=16,
                     scale=(0.5, 1, 1) if axis == "x" else (1, 0.5, 1), name="head")
        out.append(h)
        sp = V((c.x, c.y, c.z)) + ax * s * length * 0.32
        prof = [(-r * 0.8, 0), (r * 0.8, 0), (r * 0.8, saddle_h + r * 0.35), (-r * 0.8, saddle_h + r * 0.35)]
        sd = K.prism(prof, 0.08, (0, 0, 0), st.frame, rot=(0, 0, 0), bevel=0.006, name="saddle")
        sd.location = sp
        sd.rotation_euler = (0, 0, math.pi / 2 if axis == "x" else 0.0)
        out.append(sd)
        out.append(K.box((0.14, r * 1.8, 0.02), sp, st.dark, bevel=0.004, base=True) if axis == "x"
                   else K.box((r * 1.8, 0.14, 0.02), sp, st.dark, bevel=0.004, base=True))
    seam = st.metal("steel")
    for k in range(bands):
        p = V((c.x, c.y, zc)) + ax * (-length / 2 + length * (k + 1) / (bands + 1))
        out.append(K.torus(r * 1.005, 0.012, p, seam, rot=rot, segs=48, rsegs=8))
    for k in range(nozzles):
        p = V((c.x, c.y, zc + r)) + ax * (-length * 0.3 + length * 0.6 * k / max(1, nozzles - 1))
        out.append(K.cyl(0.045, 0.14, p - V((0, 0, 0.03)), mat, verts=16, bevel=0.003))
        out += K.flange(p + V((0, 0, 0.11)), 0.045, "z")
    return zc + r, out


def valve(loc, axis="x", r=0.05, wheel=(0.6, 0.03, 0.02), stem_dir="z"):
    """Inline gate valve with handwheel (pipe along `axis`)."""
    c = V(loc)
    body = M.metal("cast_iron", dirt=0.6)
    out = [K.sphere(r * 1.35, c, body, segs=16, rings=10, scale=(1, 1, 1.1))]
    out += K.flange(c + V({"x": (r * 1.3, 0, 0), "y": (0, r * 1.3, 0), "z": (0, 0, r * 1.3)}[axis]), r, axis)
    out += K.flange(c - V({"x": (r * 1.3, 0, 0), "y": (0, r * 1.3, 0), "z": (0, 0, r * 1.3)}[axis]), r, axis)
    up = V((0, 0, 1)) if stem_dir == "z" else V((0, -1, 0))
    out.append(K.cyl(r * 0.7, r * 2.2, c, body, rot=_axis_rot(up), verts=12, bevel=0.003))
    out.append(K.cyl(r * 0.18, r * 1.4, c + up * r * 2.2, M.metal("steel"), rot=_axis_rot(up), verts=8, bevel=0))
    wm = M.painted(wheel, wear=0.6, grime=0.4, name="handwheel")
    wc = c + up * r * 3.4
    out.append(K.torus(r * 1.6, r * 0.18, wc, wm, rot=_axis_rot(up), segs=24, rsegs=8))
    side = V((1, 0, 0)) if stem_dir == "z" else V((1, 0, 0))
    other = up.cross(side)
    for k in range(3):
        a = TAU * k / 3
        out.append(rod(wc, wc + (side * math.cos(a) + other * math.sin(a)) * r * 1.6, r * 0.12, wm, verts=6))
    return out


def pump(P, loc, rot_z=0.0, s=1.0, paint=None):
    """Horizontal centrifugal pump + motor on a baseplate (shaft along local X; suction faces -X).
    Returns (objs_pivot, coupling_pivot) - spin the coupling about local X."""
    st = P.st
    pm = st.paint_m(paint or ((0.05, 0.12, 0.3) if st.tier <= 2 else (0.06, 0.07, 0.08)), 0.7, name="pump_paint")
    out = [K.box((0.9 * s, 0.32 * s, 0.06 * s), (0, 0, 0), st.frame, bevel=0.006, base=True, name="baseplate")]
    zc = 0.24 * s
    # volute casing
    out.append(K.cyl(0.17 * s, 0.12 * s, (-0.3 * s, 0, zc), pm, rot=K.AXES["x"], verts=32, base=False, bevel=0.01))
    out.append(K.box((0.12 * s, 0.16 * s, 0.18 * s), (-0.3 * s, 0, 0.06 * s), pm, bevel=0.008, base=True))
    out.append(K.cyl(0.06 * s, 0.14 * s, (-0.46 * s, 0, zc), pm, rot=K.AXES["x"], verts=16, base=False, bevel=0.004))
    out.append(K.cyl(0.05 * s, 0.14 * s, (-0.3 * s, 0, zc + 0.15 * s), pm, verts=16, bevel=0.004))
    # bearing frame
    out.append(K.cyl(0.07 * s, 0.18 * s, (-0.12 * s, 0, zc), pm, rot=K.AXES["x"], verts=20, base=False, bevel=0.006))
    # motor
    out += K.motor((0.22 * s, 0, zc), "x", r=0.13 * s, length=0.36 * s,
                   paint=(0.05, 0.14, 0.3) if st.tier <= 2 else (0.55, 0.57, 0.58) if st.tier == 3 else (0.06, 0.06, 0.07))
    out.append(K.box((0.36 * s, 0.24 * s, zc - 0.06 * s), (0.22 * s, 0, 0.06 * s), st.frame, bevel=0.006, base=True))
    # coupling guard (open mesh look: two half-shells) and spinning coupling
    cp = K.pivot("coupling", (-0.0 * s, 0, zc), (0, 0, 0))
    cobj = [K.cyl(0.055 * s, 0.07 * s, (0, 0, 0), M.metal("steel"), rot=K.AXES["x"], verts=16, base=False, bevel=0.003)]
    for k in range(4):
        a = TAU * k / 4
        cobj.append(K.cyl(0.01 * s, 0.075 * s, (0, math.cos(a) * 0.04 * s, math.sin(a) * 0.04 * s), M.metal("dark_steel"),
                          rot=K.AXES["x"], verts=6, base=False, bevel=0))
    cobj.append(K.box((0.07 * s, 0.11 * s, 0.02 * s), (0, 0, 0), M.painted((0.75, 0.5, 0.02), wear=0.5, name="coupling_paint"), bevel=0.003))
    parent(cobj, cp)
    guard = K.box((0.1 * s, 0.16 * s, 0.03 * s), (0, 0, zc + 0.08 * s), M.painted((0.8, 0.55, 0.02), wear=0.5, name="guard"), bevel=0.004)
    out += [cp, guard]
    piv = group(out, loc, rot_z, "pump")
    return piv, cp


def agitator_drive(P, loc, s=1.0):
    """Top-mounted mixer drive: motor + gearbox + exposed spinning coupling. Returns coupling pivot."""
    st = P.st
    c = V(loc)
    mm = st.paint_m((0.05, 0.14, 0.3) if st.tier <= 2 else (0.6, 0.62, 0.62) if st.tier == 3 else (0.06, 0.06, 0.07), 0.7, name="drive_paint")
    out = [K.cyl(0.2 * s, 0.05 * s, c, st.frame, verts=32, bevel=0.005)]                 # mounting flange
    out += K.bolts(c + V((0, 0, 0.05 * s)), 0.17 * s, 8, "z", r=0.012, h=0.014)
    # lantern frame (open) with coupling visible
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        out.append(K.box((0.04 * s, 0.04 * s, 0.22 * s), c + V((math.cos(a) * 0.13 * s, math.sin(a) * 0.13 * s, 0.05 * s)), st.frame, bevel=0.004, base=True))
    cp = K.pivot("agit", c + V((0, 0, 0.16 * s)))
    co = [K.cyl(0.07 * s, 0.09 * s, (0, 0, -0.045 * s), M.metal("steel"), verts=20, bevel=0.003),
          K.box((0.17 * s, 0.035 * s, 0.05 * s), (0, 0, 0), M.painted((0.75, 0.5, 0.02), wear=0.5, name="coupling_paint"), bevel=0.005)]
    for k in range(4):
        a = TAU * k / 4
        co.append(K.cyl(0.012 * s, 0.1 * s, (math.cos(a) * 0.05 * s, math.sin(a) * 0.05 * s, -0.05 * s), M.metal("dark_steel"), verts=6, bevel=0))
    parent(co, cp)
    out.append(cp)
    # gearbox
    out.append(K.box((0.36 * s, 0.32 * s, 0.24 * s), c + V((0, 0, 0.27 * s)), mm, bevel=0.02, base=True, name="gearbox"))
    for k in range(5):
        out.append(K.box((0.37 * s, 0.012 * s, 0.2 * s), c + V((0, -0.12 * s + k * 0.06 * s, 0.29 * s)), mm, bevel=0.003, base=True))
    # motor on top (vertical)
    out.append(K.cyl(0.13 * s, 0.38 * s, c + V((0, 0, 0.51 * s)), mm, verts=32, bevel=0.01))
    for k in range(12):
        a = TAU * k / 12
        out.append(K.box((0.025 * s, 0.025 * s, 0.32 * s), c + V((math.cos(a) * 0.135 * s, math.sin(a) * 0.135 * s, 0.53 * s)), mm, bevel=0.004, base=True))
    out.append(K.cyl(0.11 * s, 0.06 * s, c + V((0, 0, 0.89 * s)), M.metal("cast_iron"), verts=24, bevel=0.006))
    out.append(K.box((0.12 * s, 0.1 * s, 0.1 * s), c + V((0.14 * s, -0.08 * s, 0.6 * s)), mm, bevel=0.008, base=True))
    P.anim.spin(cp, turns=1.0)
    return cp, c.z + 0.95 * s


def conveyor(P, x0, x1, y, z, width=0.5, items=None, item_spacing=0.5, speed=1, legs=True, mat=None):
    """Belt conveyor along X at height z (belt top). items: callable(local_loc)->[objs] for one item;
    they move +X by item_spacing*speed per loop (seamless). Returns list of objects."""
    st = P.st
    L = x1 - x0
    cx = (x0 + x1) / 2
    fm = mat or st.frame
    out = []
    out.append(K.box((L, width, 0.03), (cx, y, z - 0.03), st.rubber, bevel=0.006, base=True, name="belt"))
    for sy in (-1, 1):
        out.append(K.box((L + 0.06, 0.04, 0.14), (cx, y + sy * (width / 2 + 0.02), z - 0.1), fm, bevel=0.006, base=True, name="rail"))
    for x in (x0, x1):
        out.append(K.cyl(0.045, width + 0.02, (x, y, z - 0.045), M.metal("steel"), rot=(math.pi / 2, 0, 0), verts=16, base=False, bevel=0.002))
    if legs:
        n = max(2, int(L / 1.2) + 1)
        for i in range(n):
            x = x0 + 0.08 + (L - 0.16) * i / (n - 1)
            for sy in (-1, 1):
                out.append(K.box((0.05, 0.05, z - 0.1), (x, y + sy * (width / 2 + 0.02), 0), fm, bevel=0.005, base=True))
            out.append(K.box((0.04, width, 0.04), (x, y, z * 0.3), fm, bevel=0.004, base=True))
    if items:
        n = max(1, int(round(L / item_spacing)))
        sp = L / n
        carriers = []
        for i in range(n):
            pv = K.pivot("item", (x0 + i * sp, y, z))
            parent(items(), pv)
            carriers.append((pv, i))

        def f(t):
            for pv, i in carriers:
                u = (i * sp + t * sp * speed) % L
                pv.location.x = x0 + u
        f(0.0)
        P.anim.add(f)
        out += [c for c, _ in carriers]
    return out


# =========================================================================== robots
class RobotArm:
    """6-axis industrial robot (yaw J1, shoulder J2, elbow J3, wrist J5) with a 2-finger gripper.
    Build in local coords; `pose_for(target)` returns joint angles reaching a local target point with
    the tool pointing straight down."""

    def __init__(self, P, loc, s=1.0, color=None, rot_z=0.0, tool="gripper"):
        st = P.st
        self.s = s
        col = color or st.robot_col
        k = 0.6 if st.tier >= 3 else 1.0
        am = M.painted(col, wear=st.wear * 0.6 * k, grime=st.grime * 0.6, rough=0.35, gloss_coat=st.coat + 0.15,
                       rust=st.rust * 0.3, name="robot_paint")
        jm = M.painted((0.03, 0.03, 0.033), wear=0.2, grime=0.3, rough=0.35, rust=0.0, name="robot_joint")
        self.root = K.pivot("robot", loc, (0, 0, rot_z))
        base = [K.cyl(0.22 * s, 0.05 * s, (0, 0, 0), jm, verts=32, bevel=0.006),
                K.cyl(0.17 * s, 0.1 * s, (0, 0, 0.05 * s), am, verts=32, bevel=0.01)]
        base += K.bolts((0, 0, 0.05 * s), 0.19 * s, 8, "z", r=0.012 * s, h=0.012 * s)
        parent(base, self.root)
        self.h1 = 0.15 * s
        self.j1 = K.pivot("j1", (0, 0, self.h1))
        parent([self.j1], self.root)
        L1, L2, Lw = 0.62 * s, 0.56 * s, 0.1 * s
        self.L1, self.L2, self.Lw = L1, L2, Lw
        self.jx, self.jz = 0.07 * s, 0.24 * s      # shoulder offset in j1 frame
        tur = [K.cyl(0.15 * s, 0.14 * s, (0, 0, 0), am, verts=32, bevel=0.012),
               K.box((0.26 * s, 0.24 * s, 0.16 * s), (0.04 * s, 0, 0.1 * s), am, bevel=0.03 * s, base=True),
               K.cyl(0.07 * s, 0.14 * s, (-0.1 * s, 0.13 * s, 0.14 * s), jm, rot=K.AXES["-y"], verts=20, bevel=0.006)]
        parent(tur, self.j1)
        self.j2 = K.pivot("j2", (self.jx, 0, self.jz))
        parent([self.j2], self.j1)
        la = [K.cyl(0.11 * s, 0.22 * s, (0, 0, 0), am, rot=(math.pi / 2, 0, 0), verts=28, base=False, bevel=0.01),
              K.box((0.13 * s, 0.11 * s, L1), (0, 0.02 * s, 0), am, bevel=0.025 * s, base=True),
              K.cyl(0.08 * s, 0.04 * s, (0, -0.12 * s, 0), jm, rot=(math.pi / 2, 0, 0), verts=24, base=False, bevel=0.004)]
        parent(la, self.j2)
        self.j3 = K.pivot("j3", (0, 0, L1))
        parent([self.j3], self.j2)
        fa = [K.cyl(0.09 * s, 0.2 * s, (0, 0, 0), am, rot=(math.pi / 2, 0, 0), verts=28, base=False, bevel=0.01),
              K.box((0.2 * s, 0.15 * s, 0.15 * s), (-0.12 * s, 0, 0), am, bevel=0.025 * s),
              K.cyl(0.06 * s, 0.14 * s, (-0.26 * s, 0, 0), jm, rot=K.AXES["x"], verts=20, base=False, bevel=0.006),
              K.cyl(0.055 * s, L2 - 0.06 * s, (0.03 * s, 0, 0), am, rot=K.AXES["x"], verts=24, base=True, bevel=0.006),
              K.cyl(0.07 * s, 0.03 * s, (0, -0.105 * s, 0), jm, rot=(math.pi / 2, 0, 0), verts=24, base=False, bevel=0.004)]
        # cable loom along the forearm
        fa.append(K.tube([(-0.2 * s, 0.07 * s, 0.06 * s), (0.1 * s, 0.07 * s, 0.09 * s), (L2 * 0.8, 0.06 * s, 0.05 * s)], 0.014 * s,
                         M.rubber((0.02, 0.02, 0.02)), bend=0.05))
        parent(fa, self.j3)
        self.j5 = K.pivot("j5", (L2, 0, 0))
        parent([self.j5], self.j3)
        wr = [K.cyl(0.05 * s, 0.1 * s, (0, 0, 0), jm, rot=(math.pi / 2, 0, 0), verts=20, base=False, bevel=0.005),
              K.cyl(0.04 * s, 0.03 * s, (0, 0, -0.07 * s), M.metal("steel"), verts=20, bevel=0.003)]
        parent(wr, self.j5)
        self.tool = K.pivot("tool", (0, 0, -0.07 * s))
        parent([self.tool], self.j5)
        self.fingers = []
        if tool == "gripper":
            gm = M.metal("aluminum", dirt=0.4)
            tl = [K.box((0.1 * s, 0.05 * s, 0.05 * s), (0, 0, -0.05 * s), gm, bevel=0.006)]
            parent(tl, self.tool)
            for sx in (-1, 1):
                fp = K.pivot("finger", (sx * 0.03 * s, 0, -0.075 * s))
                parent([K.box((0.015 * s, 0.04 * s, 0.07 * s), (0, 0, -0.035 * s), M.metal("dark_steel"), bevel=0.003)], fp)
                parent([fp], self.tool)
                self.fingers.append((fp, sx))
            self.tool_len = 0.07 * s + 0.15 * s
        elif tool == "torch":
            tl = [K.cyl(0.03 * s, 0.08 * s, (0, 0, -0.08 * s), M.metal("dark_steel"), verts=12),
                  K.cyl(0.015 * s, 0.12 * s, (0, 0, -0.2 * s), M.metal("copper"), verts=10, r2=0.008 * s)]
            parent(tl, self.tool)
            self.tool_len = 0.07 * s + 0.2 * s
        else:  # vacuum cup
            tl = [K.cyl(0.02 * s, 0.08 * s, (0, 0, -0.08 * s), M.metal("steel"), verts=12),
                  K.cyl(0.04 * s, 0.03 * s, (0, 0, -0.11 * s), M.rubber(), verts=16, r2=0.025 * s)]
            parent(tl, self.tool)
            self.tool_len = 0.07 * s + 0.11 * s
        for p in (self.j1, self.j2, self.j3, self.j5):
            p.rotation_mode = "XYZ"

    def pose_for(self, target, wrist=0.0):
        """Joint angles (yaw, a2, a3, a5) to put the tool tip at local target (tool vertical)."""
        tx, ty, tz = target
        yaw = math.atan2(ty, tx)
        r = math.hypot(tx, ty) - self.jx
        zw = tz + self.tool_len - (self.h1 + self.jz)
        L1, L2 = self.L1, self.L2
        D = min(L1 + L2 - 1e-3, max(abs(L1 - L2) + 1e-3, math.hypot(r, zw)))
        c2 = (D * D - L1 * L1 - L2 * L2) / (2 * L1 * L2)
        th2 = -math.acos(max(-1, min(1, c2)))
        th1 = math.atan2(zw, r) - math.atan2(L2 * math.sin(th2), L1 + L2 * math.cos(th2))
        a2 = math.pi / 2 - th1
        phi = -(th1 + th2)
        a3 = phi - a2
        a5 = -phi + wrist          # keeps the tool vertical
        return (yaw, a2, a3, a5)

    def set_pose(self, q, grip=0.0):
        yaw, a2, a3, a5 = q
        self.j1.rotation_euler = (0, 0, yaw)
        self.j2.rotation_euler = (0, a2, 0)
        self.j3.rotation_euler = (0, a3, 0)
        self.j5.rotation_euler = (0, a5, 0)
        for fp, sx in self.fingers:
            fp.location.x = sx * self.s * (0.03 - 0.012 * grip)

    def animate(self, P, waypoints, grips=None, phase=0.0, k=1):
        """Cycle joint-space through local target waypoints (closed loop) with eased segments."""
        qs = [self.pose_for(w) for w in waypoints]
        grips = grips or [0.0] * len(qs)
        n = len(qs)

        def f(t):
            u = ((t * k + phase) % 1.0) * n
            i = int(u) % n
            j = (i + 1) % n
            e = smooth01(u - int(u))
            q = tuple(lerp(a, b, e) for a, b in zip(qs[i], qs[j]))
            self.set_pose(q, lerp(grips[i], grips[j], e))
        f(0.0)
        P.anim.add(f)


def scara(P, loc, s=1.0, color=None, rot_z=0.0):
    """SCARA arm: column + two horizontal links + vertical quill. Returns (j1, j2, quill)."""
    st = P.st
    col = color or ((0.75, 0.76, 0.75) if st.tier >= 3 else st.robot_col)
    am = M.painted(col, wear=st.wear * 0.5, grime=st.grime * 0.5, rough=0.33, gloss_coat=st.coat + 0.2, rust=0.0, name="scara_paint")
    jm = M.painted((0.03, 0.03, 0.033), wear=0.1, grime=0.3, rough=0.35, rust=0.0, name="robot_joint")
    root = K.pivot("scara", loc, (0, 0, rot_z))
    parent([K.cyl(0.13 * s, 0.04 * s, (0, 0, 0), jm, verts=24, bevel=0.005),
            K.box((0.2 * s, 0.2 * s, 0.42 * s), (0, 0, 0.04 * s), am, bevel=0.03 * s, base=True)], root)
    j1 = K.pivot("s1", (0, 0, 0.46 * s))
    parent([j1], root)
    parent([K.cyl(0.1 * s, 0.1 * s, (0, 0, 0), jm, verts=24, bevel=0.006),
            K.box((0.42 * s, 0.15 * s, 0.1 * s), (0.18 * s, 0, 0.1 * s), am, bevel=0.03 * s, base=True),
            K.cyl(0.08 * s, 0.1 * s, (0.4 * s, 0, 0.1 * s), am, verts=24, bevel=0.01)], j1)
    j2 = K.pivot("s2", (0.4 * s, 0, 0.2 * s))
    parent([j2], j1)
    parent([K.cyl(0.075 * s, 0.03 * s, (0, 0, 0), jm, verts=24, bevel=0.004),
            K.box((0.38 * s, 0.13 * s, 0.09 * s), (0.17 * s, 0, 0.03 * s), am, bevel=0.03 * s, base=True),
            K.cyl(0.065 * s, 0.14 * s, (0.34 * s, 0, 0.0), am, verts=24, bevel=0.01)], j2)
    quill = K.pivot("quill", (0.34 * s, 0, 0))
    parent([quill], j2)
    parent([K.cyl(0.018 * s, 0.42 * s, (0, 0, -0.22 * s), M.metal("chrome"), verts=12, bevel=0),
            K.cyl(0.03 * s, 0.05 * s, (0, 0, -0.27 * s), M.metal("aluminum"), verts=16, bevel=0.003)], quill)
    for p in (j1, j2):
        p.rotation_mode = "XYZ"
    return j1, j2, quill


def gantry(P, x0, x1, y0, y1, z, head_drop=0.3, mat=None):
    """Cartesian XY gantry over a work area: two Y-rails on posts, X-bridge, carriage, Z-head.
    Returns (bridge_pivot, carriage_pivot, z_pivot); bridge moves along Y, carriage along X (local
    to bridge), head along Z."""
    st = P.st
    fm = mat or st.frame
    rail_m = M.metal("stainless" if st.tier >= 3 else "steel")
    out = []
    for x in (x0, x1):
        for y in (y0, y1):
            out.append(K.box((0.08, 0.08, z), (x, y, 0), fm, bevel=0.008, base=True, name="gantry_post"))
        out.append(K.box((0.1, y1 - y0 + 0.08, 0.12), (x, (y0 + y1) / 2, z), fm, bevel=0.01, base=True, name="gantry_rail"))
        out.append(K.box((0.03, y1 - y0, 0.02), (x, (y0 + y1) / 2, z + 0.12), rail_m, bevel=0.003, base=True))
    bridge = K.pivot("bridge", ((x0 + x1) / 2, (y0 + y1) / 2, z + 0.14))
    bm = st.accent_m if st.tier != 2 else st.body
    parent([K.box((x1 - x0 + 0.14, 0.14, 0.12), (0, 0, 0), bm, bevel=0.012, base=True, name="bridge"),
            K.box((x1 - x0, 0.02, 0.02), (0, -0.08, 0.06), rail_m, bevel=0.003),
            K.tube([(-(x1 - x0) / 2, 0.08, 0.12), (0, 0.12, 0.2), ((x1 - x0) / 2 - 0.1, 0.08, 0.12)], 0.015, M.rubber(), bend=0.1)], bridge)
    for sx in (-1, 1):
        parent([K.box((0.16, 0.2, 0.1), (sx * (x1 - x0) / 2, 0, 0.0), st.dark, bevel=0.01, base=True)], bridge)
    car = K.pivot("carriage", (0, -0.12, 0.0))
    parent([car], bridge)
    parent([K.box((0.18, 0.1, 0.22), (0, 0, -0.05), st.dark, bevel=0.012, base=True),
            K.cyl(0.04, 0.1, (0, 0, 0.17), M.metal("dark_steel"), verts=16, bevel=0.003)], car)
    zp = K.pivot("zhead", (0, -0.03, 0.0))
    parent([zp], car)
    parent([K.box((0.06, 0.05, 0.45), (0, -0.02, -0.4 - head_drop * 0.0), M.metal("aluminum"), bevel=0.006, base=True),
            K.box((0.1, 0.08, 0.08), (0, -0.02, -0.45), st.dark, bevel=0.008, base=True),
            K.cyl(0.012, 0.06, (0, -0.02, -0.5), M.metal("chrome"), verts=10, bevel=0)], zp)
    return out, bridge, car, zp


# =========================================================================== structures
def lattice_column(P, base, h, w=0.4, mat=None, brace=0.5):
    """Square lattice mast of angle legs with X bracing."""
    mat = mat or P.st.metal("steel")
    b = V(base)
    out = []
    corners = [V((sx * w / 2, sy * w / 2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for c in corners:
        out.append(K.box((0.035, 0.035, h), b + c, mat, bevel=0.003, base=True))
    n = max(1, int(h / brace))
    for i in range(n):
        z0, z1 = h * i / n, h * (i + 1) / n
        for k in range(4):
            a, c = corners[k], corners[(k + 1) % 4]
            out.append(rod(b + a + V((0, 0, z0)), b + c + V((0, 0, z1)), 0.009, mat, verts=6))
            out.append(K.box((abs(c.x - a.x) + 0.02, abs(c.y - a.y) + 0.02, 0.02), b + (a + c) / 2 + V((0, 0, z1)), mat, bevel=0.002))
    return out


def insulator(loc, h=0.4, r=0.06, sheds=None, color=(0.16, 0.07, 0.03), axis=(0, 0, 1)):
    """Porcelain post insulator with sheds."""
    c = V(loc)
    ax = V(axis).normalized()
    pm = porcelain(color)
    rot = _axis_rot(ax)
    out = [K.cyl(r * 0.45, h, c, pm, rot=rot, verts=16, bevel=0)]
    n = sheds or max(3, int(h / 0.06))
    for i in range(n):
        out.append(K.cyl(r, 0.012, c + ax * (h * (i + 0.6) / (n + 0.2)), pm, rot=rot, verts=20, bevel=0.004, r2=r * 0.6))
    out.append(K.cyl(r * 0.6, 0.03, c, M.metal("steel"), rot=rot, verts=16, bevel=0.003))
    out.append(K.cyl(r * 0.5, 0.03, c + ax * (h - 0.02), M.metal("aluminum"), rot=rot, verts=16, bevel=0.003))
    return out


def radiator_bank(P, loc, w, h, n=None, depth=0.18, mat=None, axis="x"):
    """Transformer-style radiator fins (vertical plates). Fins stack along `axis`."""
    mat = mat or P.st.body
    c = V(loc)
    n = n or max(4, int(w / 0.06))
    out = []
    for i in range(n):
        o = -w / 2 + (i + 0.5) * w / n
        if axis == "x":
            out.append(K.box((0.012, depth, h), c + V((o, 0, 0)), mat, bevel=0.003, base=True))
        else:
            out.append(K.box((depth, 0.012, h), c + V((0, o, 0)), mat, bevel=0.003, base=True))
    for zz in (0.06, h - 0.06):
        if axis == "x":
            out.append(K.cyl(0.03, w, c + V((-w / 2, 0, zz)), mat, rot=K.AXES["x"], verts=12, bevel=0.002))
        else:
            out.append(K.cyl(0.03, w, c + V((0, -w / 2, zz)), mat, rot=(-math.pi / 2, 0, 0), verts=12, bevel=0.002))
    return out


def led_strip(a, b, color, strength=6.0, r=0.008):
    return rod(a, b, r, led(color, strength), verts=8)


def steam_pipe(P, pts, r=0.07, insulated=True, flanges=True):
    """Insulated steam line: aluminium jacket with lap bands, or bare painted pipe."""
    if insulated:
        jm = M.metal("aluminum", rough=0.42, dirt=0.15 + 0.5 * P.st.grime)
        out = [K.tube(pts, r * 1.35, jm, bend=r * 3)]
        pts_v = [V(p) for p in pts]
        for a, b in zip(pts_v, pts_v[1:]):
            seg = b - a
            n = int(seg.length / 0.45)
            for i in range(1, n):
                p = a + seg * (i / n)
                out.append(K.torus(r * 1.37, 0.006, p, jm, rot=_axis_rot(seg), segs=24, rsegs=6))
        if flanges:
            for i in (0, len(pts_v) - 1):
                p = pts_v[i]
                q = pts_v[1] if i == 0 else pts_v[-2]
                d = (p - q).normalized()
                out += K.flange(p - d * 0.02, r, _axis_name(d))
        return out
    return K.pipe_run(pts, r, P.st.pipe, flanges=flanges)


def machine_bed(P, x0, x1, y0, y1, h, mat=None, doors=True, feet=True, z=0.0):
    """Cabinet-style machine base (bottom at z, top at z+h) with service doors on the visible
    faces and levelling feet."""
    st = P.st
    mat = mat or st.body
    w, d = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    fz = 0.08 if feet else 0.0
    out = [K.box((w, d, h - fz), (cx, cy, z + fz), mat, bevel=0.015, base=True, name="bed")]
    out.append(K.box((w + 0.03, d + 0.03, 0.04), (cx, cy, z + h - 0.04), st.frame if st.tier < 4 else st.dark, bevel=0.008, base=True))
    if feet:
        fm = M.metal("dark_steel")
        for x in (x0 + 0.07, x1 - 0.07):
            for y in (y0 + 0.07, y1 - 0.07):
                out.append(K.cyl(0.05, 0.02, (x, y, z), M.rubber(), verts=16))
                out.append(K.cyl(0.015, fz, (x, y, z + 0.02), fm, verts=8))
        out.append(K.box((w - 0.04, d - 0.04, fz), (cx, cy, z), M.plastic((0.01, 0.01, 0.01), 0.9), bevel=0, base=True))
    if doors and h > 0.45:
        n = max(1, int(round(w / 0.7)))
        dw = w / n
        for i in range(n):
            x = x0 + dw * (i + 0.5)
            out.append(door(P, (x, y0, z + fz + 0.06), 0.0, w=dw - 0.06, h=h - fz - 0.16, mat=mat, handle_side=1 if i % 2 else -1))
        n = max(1, int(round(d / 0.7)))
        dd = d / n
        for i in range(n):
            y = y0 + dd * (i + 0.5)
            out.append(door(P, (x1, y, z + fz + 0.06), math.pi / 2, w=dd - 0.06, h=h - fz - 0.16, mat=mat, handle_side=1 if i % 2 else -1))
    return out


def enclosure(P, x0, x1, y0, y1, z0, z1, top="frame", post=0.045, rail_mat=None, front_low=0.0):
    """Aluminium-extrusion guard enclosure with clear panels on all sides.
    top: "frame" (open), "ffu" (fan filter unit over the back half), "solid".
    front_low > 0 leaves the -Y side as a low panel of that height (open above)."""
    st = P.st
    am = rail_mat or (M.metal("aluminum", rough=0.35, dirt=0.2 + 0.4 * st.grime) if st.tier >= 2 else st.frame)
    gl = clear_panel()
    out = []
    w, d = x1 - x0, y1 - y0
    xs = [x0 + w * i / max(1, int(round(w / 0.9))) for i in range(int(round(w / 0.9)) + 1)]
    ys = [y0 + d * i / max(1, int(round(d / 0.9))) for i in range(int(round(d / 0.9)) + 1)]
    H = z1 - z0
    for x in xs:
        for y in (y0, y1):
            out.append(K.box((post, post, H), (x, y, z0), am, bevel=0.004, base=True, name="extrusion"))
    for y in ys[1:-1]:
        for x in (x0, x1):
            out.append(K.box((post, post, H), (x, y, z0), am, bevel=0.004, base=True, name="extrusion"))
    for z in (z0 + 0.02, z1 - post / 2):
        for y in (y0, y1):
            out.append(K.box((w, post, post), ((x0 + x1) / 2, y, z), am, bevel=0.004, name="extrusion"))
        for x in (x0, x1):
            out.append(K.box((post, d, post), (x, (y0 + y1) / 2, z), am, bevel=0.004, name="extrusion"))
    # panels
    ph = H - 0.06
    out.append(K.box((w - 0.02, 0.008, ph if front_low <= 0 else front_low), ((x0 + x1) / 2, y0, z0 + 0.04), gl, bevel=0, base=True))
    if front_low > 0:
        out.append(K.box((w, post, post), ((x0 + x1) / 2, y0, z0 + front_low + 0.04), am, bevel=0.004))
    out.append(K.box((w - 0.02, 0.008, ph), ((x0 + x1) / 2, y1, z0 + 0.04), gl, bevel=0, base=True))
    for x in (x0, x1):
        out.append(K.box((0.008, d - 0.02, ph), (x, (y0 + y1) / 2, z0 + 0.04), gl, bevel=0, base=True))
    if top == "ffu":
        out.append(K.box((w + 0.02, d * 0.5, 0.22), ((x0 + x1) / 2, y1 - d * 0.25, z1), st.body if st.tier >= 3 else st.light_grey,
                         bevel=0.015, base=True, name="ffu"))
        for i in range(max(1, int(w / 0.7))):
            x = x0 + w * (i + 0.5) / max(1, int(w / 0.7))
            out.append(K.box((0.4, 0.3, 0.02), (x, y1 - d * 0.25, z1 + 0.22), M.metal("dark_steel"), bevel=0.003, base=True))
    elif top == "solid":
        out.append(K.box((w + 0.02, d + 0.02, 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, z1), st.body, bevel=0.01, base=True))
    return out


def finfan(P, x0, x1, y0, y1, z, fans=2, legs=True):
    """Air-cooled heat exchanger (fin-fan) on legs: finned tube bundle with header boxes, induced
    draft fans on top (spinning). Returns (objs, top_z)."""
    st = P.st
    out = []
    w, d = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    fm = st.frame
    if legs:
        for x in (x0 + 0.05, x1 - 0.05):
            for y in (y0 + 0.05, y1 - 0.05):
                out.append(K.box((0.08, 0.08, z), (x, y, 0), fm, bevel=0.006, base=True))
        for y in (y0 + 0.05, y1 - 0.05):
            out.append(rod((x0 + 0.05, y, 0.1), (x1 - 0.05, y, z * 0.85), 0.018, fm, verts=8))
    # tube bundle: dark finned block with header boxes at the ends
    out.append(K.box((w - 0.24, d, 0.22), (cx, cy, z), M.metal("aluminum", rough=0.6, dirt=0.4 + 0.4 * st.grime), bevel=0.004, base=True, name="bundle"))
    fin = M.plastic((0.08, 0.085, 0.09), 0.6)
    n = int(d / 0.05)
    for i in range(n):
        out.append(K.box((w - 0.24, 0.012, 0.2), (cx, y0 + (i + 0.5) * d / n, z + 0.01), fin, bevel=0, base=True))
    for sx in (-1, 1):
        out.append(K.box((0.14, d + 0.04, 0.32), (cx + sx * (w / 2 - 0.07), cy, z - 0.05), st.body, bevel=0.01, base=True, name="header"))
        for i in range(int(d / 0.12)):
            out.append(K.cyl(0.015, 0.012, (cx + sx * (w / 2 + 0.002), y0 + 0.06 + i * 0.12, z + 0.1), M.metal("dark_steel"), rot=K.AXES["x"], verts=6, base=False, bevel=0))
    # plenum + fan rings on top
    pz = z + 0.22
    out.append(K.box((w - 0.24, d, 0.14), (cx, cy, pz), st.body, bevel=0.01, base=True, name="plenum"))
    fr = min(d * 0.42, (w - 0.3) / fans * 0.42)
    for i in range(fans):
        fx = x0 + 0.12 + (w - 0.24) * (i + 0.5) / fans
        out.append(K.cyl(fr * 1.08, 0.22, (fx, cy, pz + 0.14), st.body, verts=40, bevel=0.01))
        out.append(K.cyl(fr * 1.0, 0.01, (fx, cy, pz + 0.3), M.plastic((0.01, 0.01, 0.01), 0.9), verts=40, bevel=0))
        fo, rot = K.fan((fx, cy, pz + 0.3), r=fr, axis="z", blades=6, housing=False)
        out += fo
        P.anim.spin(rot, turns=2 / 6, phase=i * 0.07)
        # guard mesh bars
        g = M.metal("dark_steel", dirt=0.3)
        for k in range(-3, 4):
            Lb = 2 * math.sqrt(max(0.0, (fr * 1.06) ** 2 - (k * fr * 0.28) ** 2))
            out.append(K.cyl(0.005, Lb, (fx + k * fr * 0.28, cy, pz + 0.37), g, rot=(math.pi / 2, 0, 0), verts=6, base=False, bevel=0))
    return out, pz + 0.38


def pipe_rack(P, x0, x1, y, z, n=3, r=0.06, colors=None, legs=True):
    """Pipe rack along X: T-posts and a bundle of parallel pipes at height z."""
    st = P.st
    out = []
    fm = st.frame
    if legs:
        nb = max(2, int((x1 - x0) / 1.4) + 1)
        for i in range(nb):
            x = x0 + (x1 - x0) * i / (nb - 1)
            out.append(K.box((0.1, 0.1, z), (x, y, 0), fm, bevel=0.006, base=True))
            out.append(K.box((0.1, n * r * 3 + 0.2, 0.1), (x, y, z - 0.05), fm, bevel=0.006))
    cols = colors or [PIPE_COL[st.tier], (0.05, 0.16, 0.06), (0.6, 0.45, 0.02), (0.3, 0.05, 0.03)]
    for i in range(n):
        yy = y - (n - 1) * r * 1.5 + i * r * 3
        out.append(K.cyl(r, x1 - x0, (x0, yy, z + r), st.paint_m(cols[i % len(cols)], 0.8, name="pipe_col"), rot=K.AXES["x"], verts=16, bevel=0.003))
    return out


def column(P, loc, r, h, mat=None, platforms=(), ladder_face="-y", insulated=True, skirt=0.6):
    """Tall process column on a skirt with circular platforms + caged ladder.
    Returns (objs, top_z)."""
    st = P.st
    c = V(loc)
    out = []
    mat = mat or (M.metal("aluminum", rough=0.45, dirt=0.15 + 0.5 * st.grime) if insulated else st.body)
    out.append(K.cyl(r * 1.02, skirt, c, st.frame, verts=40, bevel=0.006))
    out.append(K.cyl(r * 1.3, 0.05, c, st.concrete(0.5), verts=40, bevel=0.01))
    out.append(K.cyl(r, h, c + V((0, 0, skirt)), mat, verts=48, bevel=0.006, name="column"))
    out.append(ellip_head(r, c + V((0, 0, skirt + h)), mat))
    band = M.metal("steel", dirt=0.4)
    for i in range(int(h / 0.5)):
        out.append(K.torus(r * 1.004, 0.006, c + V((0, 0, skirt + 0.25 + i * 0.5)), band, segs=48, rsegs=6))
    for i in range(int(h / 1.1)):
        zz = skirt + 0.6 + i * 1.1
        a = 0.4 + i * 1.3
        dv = V((math.cos(a), math.sin(a), 0))
        out.append(K.cyl(0.06, 0.18, c + dv * r * 0.96 + V((0, 0, zz)), mat, rot=_axis_rot(dv), verts=16, bevel=0.003))
        out += flange_d(c + dv * (r + 0.15) + V((0, 0, zz)), 0.06, dv)
    pm = st.grating
    fm = st.frame
    for pz in platforms:
        out.append(K.cyl(r + 0.45, 0.04, c + V((0, 0, skirt + pz)), pm, verts=48, bevel=0.004))
        out.append(K.torus(r + 0.45, 0.02, c + V((0, 0, skirt + pz + 1.0)), st.paint_m((0.75, 0.5, 0.02) if st.tier <= 3 else (0.6, 0.62, 0.62), 0.8, name="rail_paint"), segs=48, rsegs=8))
        out.append(K.torus(r + 0.45, 0.015, c + V((0, 0, skirt + pz + 0.5)), st.paint_m((0.75, 0.5, 0.02) if st.tier <= 3 else (0.6, 0.62, 0.62), 0.8, name="rail_paint"), segs=48, rsegs=8))
        for k in range(10):
            a = TAU * k / 10
            out.append(K.cyl(0.018, 1.0, c + V((math.cos(a) * (r + 0.45), math.sin(a) * (r + 0.45), skirt + pz)), st.paint_m((0.75, 0.5, 0.02) if st.tier <= 3 else (0.6, 0.62, 0.62), 0.8, name="rail_paint"), verts=8))
            if k % 2 == 0:
                out.append(rod(c + V((math.cos(a) * r, math.sin(a) * r, skirt + pz - 0.3)), c + V((math.cos(a) * (r + 0.42), math.sin(a) * (r + 0.42), skirt + pz)), 0.02, fm, verts=6))
    fr = FACE_ROT[ladder_face]
    fdir = Matrix.Rotation(fr, 3, "Z") @ V((0, -1, 0))
    out.append(ladder(P, c + fdir * (r + 0.2) + V((0, 0, 0)), skirt + h - 0.2, fr, cage=True))
    return out, skirt + h + r * 0.5


def lathe(profile, loc, mat, segs=48, name="lathe", bevel=0.0, smooth_angle=60.0, closed=False):
    """Surface of revolution about local Z from a profile [(r, z), ...]. closed=True joins the
    last profile point back to the first (solid ring / thick shell)."""
    import bmesh
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = []
        for i in range(segs):
            ang = TAU * i / segs
            ring.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), z)))
        rings.append(ring)
    n = len(rings) if closed else len(rings) - 1
    for k in range(n):
        ra, rb = rings[k], rings[(k + 1) % len(rings)]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K._finish(name, bm, mat, loc, (0, 0, 0), bevel, smooth_angle=smooth_angle)


def spoked_wheel(r, width, mat, hub_mat=None, spokes=6, rim=0.06, name="wheel"):
    """Flywheel / pulley in the local XZ plane (axle along local Y), centred at the origin."""
    hub_mat = hub_mat or mat
    ring = lathe([(r, -width / 2), (r, width / 2), (r - rim, width / 2), (r - rim, -width / 2)], (0, 0, 0), mat,
                 segs=64, name=name + "_rim", closed=True)
    ring.rotation_euler = (math.pi / 2, 0, 0)
    out = [ring]
    for k in range(spokes):
        ang = TAU * k / spokes
        out.append(rod((math.cos(ang) * r * 0.12, 0, math.sin(ang) * r * 0.12), (math.cos(ang) * (r - rim * 0.8), 0, math.sin(ang) * (r - rim * 0.8)),
                       max(0.012, r * 0.045), mat, verts=10))
    out.append(K.cyl(r * 0.16, width * 1.3, (0, 0, 0), hub_mat, rot=(math.pi / 2, 0, 0), verts=24, base=False, bevel=0.006))
    return out
