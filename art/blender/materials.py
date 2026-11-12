"""Physically based material library for the INDUSTRIUM render pipeline.

All materials use object-space box projection so procedural meshes need no UVs. Meshes are
built at real-world size (1 unit = 1 m) with unit object scale, so texture density is stable.

Main entry point: ``get(name, **params)`` (cached by name+params) or the specific factories.
"""
import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "art", "source", "textures")

_cache = {}


# --------------------------------------------------------------------------- node helpers
class NT:
    """Tiny node-tree builder."""

    def __init__(self, mat):
        self.nt = mat.node_tree
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self.x = -1600

    def node(self, kind, **props):
        n = self.nodes.new(kind)
        n.location = (self.x, 0)
        self.x += 40
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def sock(self, sockets, ident):
        if isinstance(ident, int):
            return sockets[ident]
        for s in sockets:
            if s.identifier == ident:
                return s
        return sockets[ident]

    def link(self, a, b):
        self.links.new(a, b)

    def val(self, node, ident, value):
        s = self.sock(node.inputs, ident)
        s.default_value = value
        return s

    # ---- composite helpers
    def math(self, op, a, b=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.link(v, n.inputs[i])
        return n.outputs[0]

    def maprange(self, v, fmin, fmax, tmin=0.0, tmax=1.0, interp="LINEAR"):
        n = self.node("ShaderNodeMapRange", interpolation_type=interp, clamp=True)
        self.link(v, n.inputs["Value"])
        n.inputs[1].default_value = fmin
        n.inputs[2].default_value = fmax
        n.inputs[3].default_value = tmin
        n.inputs[4].default_value = tmax
        return n.outputs["Result"]

    def mix_color(self, fac, a, b, blend="MIX"):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_result=True)
        for ident, v in (("Factor_Float", fac), ("A_Color", a), ("B_Color", b)):
            s = self.sock(n.inputs, ident)
            if isinstance(v, (int, float)):
                s.default_value = v
            elif isinstance(v, (tuple, list)):
                s.default_value = tuple(v) + ((1.0,) if len(v) == 3 else ())
            else:
                self.link(v, s)
        return self.sock(n.outputs, "Result_Color")

    def mix_float(self, fac, a, b):
        n = self.node("ShaderNodeMix", data_type="FLOAT", clamp_result=True)
        for ident, v in (("Factor_Float", fac), ("A_Float", a), ("B_Float", b)):
            s = self.sock(n.inputs, ident)
            if isinstance(v, (int, float)):
                s.default_value = v
            else:
                self.link(v, s)
        return self.sock(n.outputs, "Result_Float")

    def coords(self, scale=1.0):
        tc = self.node("ShaderNodeTexCoord")
        mp = self.node("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        self.link(tc.outputs["Object"], mp.inputs["Vector"])
        return mp.outputs["Vector"]

    def image(self, tex_id, kind, vec, noncolor=False):
        path = os.path.join(TEX, tex_id, f"{kind}.jpg")
        if not os.path.exists(path):
            return None
        img = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            img.colorspace_settings.name = "Non-Color"
        n = self.node("ShaderNodeTexImage", projection="BOX", projection_blend=0.25)
        n.image = img
        self.link(vec, n.inputs["Vector"])
        return n

    def noise(self, vec, scale, detail=6.0, rough=0.55, dist=0.0):
        n = self.node("ShaderNodeTexNoise")
        self.link(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = dist
        return n.outputs["Factor"]

    def edge_mask(self, radius=0.012, lo=0.002, hi=0.05):
        """1 on convex/concave hard edges, 0 on flat faces (Cycles Bevel node trick)."""
        bev = self.node("ShaderNodeBevel")
        bev.samples = 8
        bev.inputs["Radius"].default_value = radius
        geo = self.node("ShaderNodeNewGeometry")
        dot = self.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        self.link(bev.outputs["Normal"], dot.inputs[0])
        self.link(geo.outputs["Normal"], dot.inputs[1])
        inv = self.math("SUBTRACT", 1.0, dot.outputs["Value"])
        return self.maprange(inv, lo, hi)

    def cavity(self, distance=0.25):
        ao = self.node("ShaderNodeAmbientOcclusion", samples=8)
        ao.inputs["Distance"].default_value = distance
        return self.math("SUBTRACT", 1.0, ao.outputs["AO"])

    def bump(self, height, strength=0.3, distance=0.01, normal=None):
        b = self.node("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        self.link(height, b.inputs["Height"])
        if normal is not None:
            self.link(normal, b.inputs["Normal"])
        return b.outputs["Normal"]

    def bsdf(self):
        out = self.nodes.get("Material Output") or self.node("ShaderNodeOutputMaterial")
        p = self.nodes.get("Principled BSDF") or self.node("ShaderNodeBsdfPrincipled")
        self.link(p.outputs[0], out.inputs["Surface"])
        return p


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, NT(m)


def _rgba(c):
    c = tuple(c)
    return c + (1.0,) if len(c) == 3 else c


def _set(p, ident, v):
    if isinstance(v, (int, float)):
        p.inputs[ident].default_value = v
    elif isinstance(v, (tuple, list)):
        p.inputs[ident].default_value = _rgba(v)
    else:
        p.id_data.links.new(v, p.inputs[ident])


# --------------------------------------------------------------------------- base metals
METALS = {
    # name: (base color (linear-ish sRGB), roughness, metallic)
    "steel": ((0.56, 0.57, 0.58), 0.38, 1.0),
    "iron": ((0.42, 0.42, 0.42), 0.5, 1.0),
    "cast_iron": ((0.22, 0.215, 0.21), 0.62, 1.0),
    "stainless": ((0.66, 0.66, 0.66), 0.25, 1.0),
    "chrome": ((0.8, 0.8, 0.82), 0.08, 1.0),
    "aluminum": ((0.86, 0.87, 0.88), 0.32, 1.0),
    "copper": ((0.93, 0.56, 0.42), 0.3, 1.0),
    "brass": ((0.9, 0.72, 0.38), 0.3, 1.0),
    "bronze": ((0.72, 0.48, 0.28), 0.38, 1.0),
    "gold": ((1.0, 0.77, 0.34), 0.2, 1.0),
    "silver": ((0.95, 0.94, 0.92), 0.18, 1.0),
    "tin": ((0.78, 0.78, 0.76), 0.35, 1.0),
    "lead": ((0.45, 0.46, 0.5), 0.55, 1.0),
    "tungsten": ((0.5, 0.5, 0.52), 0.4, 1.0),
    "titanium": ((0.62, 0.6, 0.57), 0.33, 1.0),
    "dark_steel": ((0.16, 0.16, 0.17), 0.45, 1.0),
}


def metal(kind="steel", rough=None, brushed=0.6, dirt=0.5, scale=1.0, tint=None):
    key = ("metal", kind, rough, brushed, dirt, scale, tint)
    if key in _cache:
        return _cache[key]
    base, r0, met = METALS[kind]
    if tint:
        base = tuple(b * t for b, t in zip(base, tint))
    r0 = r0 if rough is None else rough
    m, t = _new(f"metal_{kind}")
    p = t.bsdf()
    vec = t.coords(scale)
    # roughness breakup from scanned brushed metal
    rimg = t.image("Metal032", "rough", vec, noncolor=True)
    rough_out = t.maprange(rimg.outputs["Color"], 0.0, 1.0, r0 * 0.7, r0 * 1.35) if rimg else r0
    # grime in cavities + large scale smudges
    cav = t.cavity(0.2)
    smudge = t.noise(vec, 3.0, 8, 0.6)
    grime = t.math("MULTIPLY", t.math("ADD", cav, t.maprange(smudge, 0.45, 0.75, 0.0, 0.35)), dirt, clamp=True)
    col = t.mix_color(grime, base, (0.05, 0.045, 0.04))
    _set(p, "Base Color", col)
    _set(p, "Metallic", t.mix_float(grime, met, 0.3))
    _set(p, "Roughness", t.mix_float(grime, rough_out, 0.85))
    p.inputs["Anisotropic"].default_value = 0.3 * brushed
    h = t.noise(vec, 140.0, 4, 0.5)
    p.inputs["Normal"].default_value = (0, 0, 0)
    t.link(t.bump(h, 0.05, 0.002), p.inputs["Normal"])
    _cache[key] = m
    return m


def painted(color, wear=0.5, grime=0.5, rough=0.42, under="steel", gloss_coat=0.0, scale=1.0, name="paint", rust=0.25):
    """Industrial enamel over metal: chipped edges, scratches, cavity grime, drip streaks, rust.

    `color` is LINEAR rgb (0.04 = dark grey, 0.2 = mid grey, 0.6 = light grey).
    """
    key = ("paint", tuple(color), wear, grime, rough, under, gloss_coat, scale, rust)
    if key in _cache:
        return _cache[key]
    m, t = _new(name)
    p = t.bsdf()
    vec = t.coords(scale)
    # --- masks
    edge = t.edge_mask(0.014, 0.004, 0.06)
    chip_noise = t.noise(vec, 22.0, 10, 0.7, 0.4)
    chips = t.maprange(t.math("MULTIPLY", edge, chip_noise), 0.18 * (1.3 - wear), 0.32 * (1.3 - wear))
    scr = t.image("PaintedMetal004", "metal", t.coords(scale * 0.7), noncolor=True)
    scratches = t.maprange(scr.outputs["Color"], 0.15, 0.6, 0.0, wear) if scr else 0.0
    bare = t.math("MAXIMUM", chips, scratches)
    cav = t.cavity(0.3)
    blotch = t.noise(vec, 1.6, 6, 0.6)
    # vertical drip streaks: noise stretched along Z
    sv = t.node("ShaderNodeVectorMath", operation="MULTIPLY")
    sv.inputs[1].default_value = (14.0, 14.0, 0.8)
    t.link(vec, sv.inputs[0])
    streak = t.maprange(t.noise(sv.outputs["Vector"], 1.0, 4, 0.5), 0.52, 0.72, 0.0, 0.55)
    dirt = t.math("ADD", t.math("MULTIPLY", cav, 1.6), t.maprange(blotch, 0.45, 0.75, 0.0, 0.5))
    dirt = t.math("MULTIPLY", t.math("ADD", dirt, streak), grime, clamp=True)
    # rust patches from the scanned rusty sheet (rust = darker, saturated areas), favouring edges
    rimg = t.image("rusty_metal_02", "color", t.coords(scale * 0.6))
    rust_col = rimg.outputs["Color"] if rimg else (0.3, 0.12, 0.04)
    lum = t.node("ShaderNodeRGBToBW")
    if rimg:
        t.link(rimg.outputs["Color"], lum.inputs[0])
    rmask = t.maprange(lum.outputs[0], 0.30, 0.16, 0.0, 1.0)
    rmask = t.math("MULTIPLY", t.math("ADD", rmask, t.math("MULTIPLY", edge, 0.5)), rust * 2.5, clamp=True)
    # --- paint colour with slight fade variation
    var = t.maprange(blotch, 0.3, 0.7, 0.85, 1.08)
    pc = t.node("ShaderNodeVectorMath", operation="SCALE")
    pc.inputs[0].default_value = tuple(color)
    t.link(var, pc.inputs["Scale"])
    paint_col = pc.outputs["Vector"]
    metal_base = METALS.get(under, METALS["steel"])[0]
    col = t.mix_color(bare, paint_col, metal_base)
    rust_dark = t.mix_color(0.45, rust_col, (0.12, 0.04, 0.015), blend="MULTIPLY")
    col = t.mix_color(rmask, col, rust_dark)
    col = t.mix_color(dirt, col, (0.03, 0.025, 0.02))
    _set(p, "Base Color", col)
    met = t.math("MULTIPLY", bare, t.math("SUBTRACT", 1.0, rmask), clamp=True)
    _set(p, "Metallic", met)
    r = t.mix_float(bare, rough, 0.33)
    r = t.mix_float(rmask, r, 0.85)
    r = t.mix_float(dirt, r, 0.92)
    _set(p, "Roughness", r)
    if gloss_coat:
        p.inputs["Coat Weight"].default_value = gloss_coat
        p.inputs["Coat Roughness"].default_value = 0.15
    # paint thickness bump at chip borders + rust pitting + orange peel
    h = t.math("ADD", t.math("MULTIPLY", t.math("SUBTRACT", 1.0, bare), 0.6), t.math("MULTIPLY", t.noise(vec, 90, 3, 0.5), 0.15))
    h = t.math("ADD", h, t.math("MULTIPLY", rmask, t.noise(vec, 60, 6, 0.7)))
    t.link(t.bump(h, 0.3, 0.003), p.inputs["Normal"])
    _cache[key] = m
    return m


def scanned(tex_id, scale=1.0, tint=None, metallic=None, rough_mul=1.0, bump=0.6, name=None, ao=True):
    """Material from a downloaded PBR scan set (color/rough/disp/metal)."""
    key = ("scan", tex_id, scale, tuple(tint) if tint else None, metallic, rough_mul, bump)
    if key in _cache:
        return _cache[key]
    m, t = _new(name or tex_id)
    p = t.bsdf()
    vec = t.coords(scale)
    c = t.image(tex_id, "color", vec)
    col = c.outputs["Color"]
    if tint:
        col = t.mix_color(1.0, col, tuple(tint), blend="MULTIPLY")
    if ao:
        col = t.mix_color(t.math("MULTIPLY", t.cavity(0.25), 0.8, clamp=True), col, (0.02, 0.02, 0.02))
    _set(p, "Base Color", col)
    r = t.image(tex_id, "rough", vec, noncolor=True)
    if r:
        _set(p, "Roughness", t.math("MULTIPLY", r.outputs["Color"], rough_mul, clamp=True))
    mt = t.image(tex_id, "metal", vec, noncolor=True)
    if metallic is not None:
        p.inputs["Metallic"].default_value = metallic
    elif mt:
        _set(p, "Metallic", mt.outputs["Color"])
    d = t.image(tex_id, "disp", vec, noncolor=True)
    if d and bump:
        t.link(t.bump(d.outputs["Color"], bump, 0.01), p.inputs["Normal"])
    _cache[key] = m
    return m


def concrete(scale=0.25, tint=None, tex="concrete_floor_worn_001"):
    return scanned(tex, scale=scale, tint=tint, metallic=0.0, bump=0.5, name="concrete")


def rubber(color=(0.035, 0.035, 0.037), scale=2.0):
    key = ("rubber", tuple(color), scale)
    if key in _cache:
        return _cache[key]
    m, t = _new("rubber")
    p = t.bsdf()
    vec = t.coords(scale)
    r = t.image("Rubber004", "rough", vec, noncolor=True)
    cav = t.cavity(0.15)
    _set(p, "Base Color", t.mix_color(t.math("MULTIPLY", cav, 0.6), color, (0.012, 0.012, 0.012)))
    if r:
        _set(p, "Roughness", t.maprange(r.outputs["Color"], 0, 1, 0.55, 0.9))
    d = t.image("Rubber004", "disp", vec, noncolor=True)
    if d:
        t.link(t.bump(d.outputs["Color"], 0.4, 0.004), p.inputs["Normal"])
    _cache[key] = m
    return m


def plastic(color, rough=0.38, name="plastic"):
    key = ("plastic", tuple(color), rough)
    if key in _cache:
        return _cache[key]
    m, t = _new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    cav = t.cavity(0.15)
    _set(p, "Base Color", t.mix_color(t.math("MULTIPLY", cav, 0.5), color, tuple(c * 0.35 for c in color)))
    _set(p, "Roughness", t.maprange(t.noise(vec, 12, 4), 0.3, 0.7, rough * 0.8, rough * 1.2))
    p.inputs["Specular IOR Level"].default_value = 0.5
    _cache[key] = m
    return m


def glass(tint=(0.85, 0.92, 0.95), rough=0.03, name="glass"):
    key = ("glass", tuple(tint), rough)
    if key in _cache:
        return _cache[key]
    m, t = _new(name)
    p = t.bsdf()
    p.inputs["Base Color"].default_value = _rgba(tint)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Transmission Weight"].default_value = 1.0
    p.inputs["IOR"].default_value = 1.5
    _cache[key] = m
    return m


def emissive(color, strength=8.0, name="glow"):
    key = ("emit", tuple(color), strength)
    if key in _cache:
        return _cache[key]
    m, t = _new(name)
    p = t.bsdf()
    p.inputs["Base Color"].default_value = _rgba(color)
    p.inputs["Emission Color"].default_value = _rgba(color)
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Roughness"].default_value = 0.3
    _cache[key] = m
    return m


def molten(color=(1.0, 0.38, 0.06), strength=14.0, scale=3.0):
    """Glowing molten metal / lava with crusty dark patches."""
    key = ("molten", tuple(color), strength, scale)
    if key in _cache:
        return _cache[key]
    m, t = _new("molten")
    p = t.bsdf()
    vec = t.coords(scale)
    vor = t.node("ShaderNodeTexVoronoi")
    t.link(vec, vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 4.0
    n = t.noise(vec, 6.0, 8, 0.65, 0.5)
    crust = t.maprange(t.math("ADD", vor.outputs["Distance"], t.math("MULTIPLY", n, 0.5)), 0.55, 0.85)
    heat = t.math("SUBTRACT", 1.0, crust)
    _set(p, "Base Color", t.mix_color(crust, color, (0.05, 0.03, 0.025)))
    _set(p, "Emission Color", t.mix_color(heat, (0.4, 0.05, 0.0), color))
    _set(p, "Emission Strength", t.math("MULTIPLY", heat, strength))
    _set(p, "Roughness", t.mix_float(crust, 0.25, 0.9))
    _cache[key] = m
    return m


def hazard(scale=6.0, colors=((0.85, 0.6, 0.02), (0.02, 0.02, 0.02)), wear=0.6):
    """Diagonal yellow/black safety stripes with wear."""
    key = ("hazard", scale, wear)
    if key in _cache:
        return _cache[key]
    m, t = _new("hazard")
    p = t.bsdf()
    vec = t.coords(1.0)
    sep = t.node("ShaderNodeSeparateXYZ")
    t.link(vec, sep.inputs[0])
    s = t.math("ADD", t.math("ADD", sep.outputs["X"], sep.outputs["Y"]), sep.outputs["Z"])
    s = t.math("MULTIPLY", s, scale)
    stripe = t.math("GREATER_THAN", t.math("FRACT", s), 0.5)
    col = t.mix_color(stripe, colors[0], colors[1])
    edge = t.edge_mask()
    wearn = t.maprange(t.math("MULTIPLY", edge, t.noise(vec, 25, 8, 0.7)), 0.2, 0.35)
    col = t.mix_color(wearn, col, METALS["steel"][0])
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.2), 0.8 * wear, clamp=True), col, (0.04, 0.035, 0.03))
    _set(p, "Base Color", col)
    _set(p, "Metallic", wearn)
    _set(p, "Roughness", 0.5)
    _cache[key] = m
    return m


def tread_plate(scale=1.0, rust=False):
    return scanned("metal_grate_rusty" if rust else "DiamondPlate008C", scale=scale, bump=0.8, name="tread")


def rusty(scale=1.0):
    return scanned("rusty_metal_02", scale=scale, metallic=0.4, bump=0.5, name="rust")


def screen(color=(0.2, 0.9, 0.5), strength=3.0):
    """Control panel display: emissive scanlines."""
    key = ("screen", tuple(color), strength)
    if key in _cache:
        return _cache[key]
    m, t = _new("screen")
    p = t.bsdf()
    vec = t.coords(1.0)
    wave = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
    t.link(vec, wave.inputs["Vector"])
    wave.inputs["Scale"].default_value = 60
    k = t.maprange(wave.outputs["Factor"], 0.2, 0.8, 0.6, 1.0)
    _set(p, "Base Color", (0.01, 0.01, 0.01))
    p.inputs["Emission Color"].default_value = _rgba(color)
    _set(p, "Emission Strength", t.math("MULTIPLY", k, strength))
    p.inputs["Roughness"].default_value = 0.1
    p.inputs["Coat Weight"].default_value = 1.0
    _cache[key] = m
    return m


def from_spec(material, color=None):
    """Map a CONTENT_SCHEMA material name to a bpy material (used by icons & deposits)."""
    c = tuple(color) if color else None
    if material in METALS:
        return metal(material, tint=c)
    table = {
        "iron_ore": lambda: scanned("rusty_metal_02", 2.0, tint=(0.55, 0.38, 0.3), metallic=0.2, name="iron_ore"),
        "copper_ore": lambda: painted((0.12, 0.45, 0.38), wear=0.9, grime=0.9, rough=0.8, under="copper"),
        "coal": lambda: plastic((0.02, 0.02, 0.022), 0.55),
        "stone": lambda: concrete(2.0, tint=(0.75, 0.72, 0.68)),
        "limestone": lambda: concrete(2.0, tint=(1.0, 0.97, 0.88)),
        "sand": lambda: concrete(6.0, tint=(1.1, 0.95, 0.7)),
        "quartz": lambda: glass((0.95, 0.95, 0.97), 0.25),
        "bauxite": lambda: concrete(2.0, tint=(1.0, 0.55, 0.35)),
        "ilmenite": lambda: metal("cast_iron", rough=0.7),
        "monazite": lambda: concrete(2.0, tint=(0.95, 0.75, 0.45)),
        "sulfur": lambda: plastic((0.95, 0.85, 0.15), 0.7),
        "salt": lambda: plastic((0.93, 0.93, 0.95), 0.6),
        "lithium": lambda: metal("silver", rough=0.4),
        "graphite": lambda: metal("dark_steel", rough=0.55),
        "silicon": lambda: metal("dark_steel", rough=0.15, tint=(0.7, 0.75, 0.9)),
        "glass": lambda: glass(),
        "concrete": lambda: concrete(1.0),
        "brick_clay": lambda: concrete(1.0, tint=(0.75, 0.35, 0.22)),
        "rubber": lambda: rubber(),
        "plastic_white": lambda: plastic((0.85, 0.85, 0.83)),
        "plastic_black": lambda: plastic((0.03, 0.03, 0.03)),
        "plastic_color": lambda: plastic(c or (0.8, 0.2, 0.1)),
        "carbon_fiber": lambda: plastic((0.02, 0.02, 0.025), 0.25),
        "ceramic": lambda: plastic((0.9, 0.88, 0.82), 0.5),
        "wood": lambda: plastic((0.45, 0.28, 0.14), 0.7),
        "pcb_green": lambda: plastic((0.03, 0.25, 0.08), 0.35),
        "pcb_blue": lambda: plastic((0.03, 0.08, 0.3), 0.35),
        "pcb_red": lambda: plastic((0.35, 0.03, 0.03), 0.35),
        "pcb_black": lambda: plastic((0.02, 0.02, 0.02), 0.3),
        "paint": lambda: painted(c or (0.7, 0.5, 0.1), wear=0.35, grime=0.35),
        "glow": lambda: emissive(c or (0.3, 0.8, 1.0), 10.0),
        "uranium_glass": lambda: emissive((0.3, 1.0, 0.2), 6.0),
        "thorium": lambda: metal("lead", tint=(0.9, 1.0, 0.9)),
        "crystal": lambda: glass(c or (0.6, 0.8, 1.0), 0.05),
    }
    f = table.get(material)
    return f() if f else plastic(c or (0.5, 0.5, 0.5))
