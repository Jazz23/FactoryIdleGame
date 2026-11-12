"""Shared helpers for item icons and resource-deposit sprites.

* icon-specific natural materials the shared library approximates (rock & ore, powders, wood,
  bark, fabric, liquids, gems, PV cells) and ``surf(material, color)`` which picks the best
  material for a CONTENT_SCHEMA material name (falls back to ``materials.from_spec``),
* procedural mesh builders: faceted rocks, heaps, lathe (surface of revolution), ring/polygon
  extrusions, sweeps, helices, text, boolean cutting,
* framing: scene point cloud, bounding sphere, lens/shift camera fit (object fills a fixed share
  of the frame and its soft shadow stays inside it),
* the icon lighting rig (softbox key / fill / rim / top + dim HDRI),
* labelled contact sheets via the project venv's Pillow.

Everything is built at "hero scale" (largest dimension ~0.25-0.6 m) so the shared materials'
texture density and edge-wear masks read like close-up product photography.
"""
import json
import math
import os
import random
import subprocess
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector, noise

import kit as K
import materials as M
import studio

ROOT = studio.ROOT
VENV_PY = os.path.join(ROOT, ".venv", "bin", "python")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

_cache = {}


def reset():
    """Call after studio.reset(): drop material caches that point at freed datablocks."""
    _cache.clear()
    M._cache.clear()
    K.reset()


def seed_of(*parts):
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0xFFFFFFFF


def rnd_for(*parts):
    return random.Random(seed_of(*parts))


def lin(c, k=1.0):
    return tuple(max(0.0, float(v) * k) for v in c[:3])


def glow_color(c, k=2.0):
    """Saturate an emission colour so AgX keeps its hue instead of washing it to white."""
    c = lin(c)
    m = max(c) or 1.0
    return tuple((x / m) ** k * m for x in c)


def lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# =========================================================================== colours
# Representative LINEAR base colours for every schema material (used for powders, piles,
# tints and fall-backs).
MAT_COLOR = {
    "iron": (0.3, 0.3, 0.31), "steel": (0.45, 0.46, 0.47), "stainless": (0.55, 0.55, 0.55),
    "copper": (0.75, 0.38, 0.22), "brass": (0.72, 0.52, 0.2), "bronze": (0.55, 0.33, 0.16),
    "tin": (0.6, 0.6, 0.58), "aluminum": (0.7, 0.71, 0.72), "titanium": (0.48, 0.46, 0.43),
    "gold": (0.9, 0.62, 0.2), "silver": (0.85, 0.84, 0.82), "lead": (0.3, 0.31, 0.34),
    "tungsten": (0.36, 0.36, 0.38), "chrome": (0.7, 0.7, 0.72), "cast_iron": (0.16, 0.155, 0.15),
    "iron_ore": (0.22, 0.08, 0.045), "copper_ore": (0.06, 0.22, 0.14), "coal": (0.018, 0.018, 0.02),
    "stone": (0.26, 0.25, 0.23), "limestone": (0.55, 0.51, 0.42), "sand": (0.5, 0.36, 0.2),
    "quartz": (0.8, 0.8, 0.8), "bauxite": (0.38, 0.12, 0.05), "ilmenite": (0.04, 0.04, 0.045),
    "monazite": (0.5, 0.28, 0.1), "sulfur": (0.78, 0.6, 0.04), "salt": (0.85, 0.85, 0.86),
    "lithium": (0.62, 0.6, 0.62), "graphite": (0.035, 0.035, 0.04), "silicon": (0.12, 0.13, 0.17),
    "glass": (0.75, 0.82, 0.8), "concrete": (0.36, 0.35, 0.33), "brick_clay": (0.36, 0.11, 0.05),
    "rubber": (0.03, 0.03, 0.03), "plastic_white": (0.8, 0.8, 0.78), "plastic_black": (0.03, 0.03, 0.03),
    "plastic_color": (0.7, 0.2, 0.08), "carbon_fiber": (0.025, 0.025, 0.03), "ceramic": (0.8, 0.78, 0.72),
    "wood": (0.33, 0.18, 0.08), "pcb_green": (0.03, 0.2, 0.06), "pcb_blue": (0.02, 0.06, 0.25),
    "pcb_red": (0.3, 0.02, 0.02), "pcb_black": (0.02, 0.02, 0.02), "paint": (0.7, 0.5, 0.1),
    "glow": (0.3, 0.8, 1.0), "uranium_glass": (0.3, 1.0, 0.2), "thorium": (0.3, 0.33, 0.3),
    "crystal": (0.6, 0.8, 1.0),
}
METAL_NAMES = set(M.METALS) | {"chrome"}

STAMP = {
    "iron": "Fe", "steel": "ST-52", "stainless": "316L", "copper": "Cu 99.9", "brass": "CuZn37",
    "bronze": "CuSn8", "tin": "Sn 99.9", "aluminum": "AL 99.7", "titanium": "Ti-6Al", "gold": "Au 999.9",
    "silver": "Ag 999", "lead": "Pb 99.9", "tungsten": "W 99.95", "chrome": "Cr", "cast_iron": "GG-25",
    "lithium": "Li", "silicon": "Si 9N", "graphite": "C", "thorium": "Th-232", "uranium_glass": "U-235",
}


ICON_METAL_TINT = {
    "copper": (1.0, 0.72, 0.56), "brass": (1.0, 0.88, 0.62), "bronze": (1.0, 0.8, 0.62), "gold": (1.0, 0.86, 0.6),
}


def metal(material, color=None, **kw):
    """Shared metal with the icon tint (or the item colour) applied."""
    tint = tuple(color[:3]) if color else ICON_METAL_TINT.get(material)
    return M.metal(material, tint=tint, **kw)


OXIDE = {
    "copper": (0.22, 0.07, 0.035), "brass": (0.3, 0.2, 0.06), "bronze": (0.18, 0.1, 0.04), "steel": (0.07, 0.07, 0.075),
    "iron": (0.06, 0.055, 0.05), "cast_iron": (0.08, 0.05, 0.035), "aluminum": (0.55, 0.55, 0.55),
    "silver": (0.3, 0.27, 0.22), "lead": (0.22, 0.23, 0.25), "titanium": (0.3, 0.27, 0.24), "tin": (0.42, 0.42, 0.4),
    "tungsten": (0.17, 0.17, 0.19), "stainless": (0.35, 0.34, 0.33), "dark_steel": (0.05, 0.05, 0.05),
}


def cast_metal(material, color=None, rough=None, oxid=0.55, scale=6.0):
    """As-cast metal: oxidation / tarnish blotches, roughness breakup and fine casting pits."""
    key = _key("cast", material, color, rough, oxid, scale)
    if key in _cache:
        return _cache[key]
    base, r0, _ = M.METALS.get(material, M.METALS["steel"])
    tint = tuple(color[:3]) if color else ICON_METAL_TINT.get(material)
    if tint:
        base = tuple(b * t for b, t in zip(base, tint))
    r0 = rough if rough is not None else r0
    ox = OXIDE.get(material) if material != "gold" and material != "chrome" else None
    m, t = M._new(f"cast_{material}")
    p = t.bsdf()
    vec = t.coords(scale)
    blot = t.noise(vec, 1.4, 7, 0.62)
    fine = t.noise(vec, 14.0, 8, 0.7)
    col = base
    met = 1.0
    if ox:
        om = t.maprange(blot, 0.42, 0.72, 0.0, oxid)
        col = t.mix_color(om, base, ox)
        met = t.mix_float(om, 1.0, 0.55)
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.03), 0.85, clamp=True), col, (0.02, 0.018, 0.016))
    _set(p, "Base Color", col)
    _set(p, "Metallic", met)
    _set(p, "Roughness", t.maprange(fine, 0.25, 0.75, r0 * 0.75, min(0.9, r0 * 1.7)))
    pits = t.maprange(_voronoi(t, vec, 30.0), 0.0, 0.12, 0.0, 1.0)
    h = t.math("ADD", t.math("MULTIPLY", pits, 0.5), t.math("MULTIPLY", fine, 0.5))
    t.link(t.bump(h, 0.18, 0.0015), p.inputs["Normal"])
    _cache[key] = m
    return m


def heat_tint(material, color=None):
    """Machined superalloy / titanium with oxide heat-tint iridescence (thin film)."""
    key = _key("heattint", material, color)
    if key in _cache:
        return _cache[key]
    base, r0, _ = M.METALS.get(material, M.METALS["titanium"])
    if color:
        base = tuple(b * c for b, c in zip(base, color))
    m, t = M._new("heat_tint")
    p = t.bsdf()
    vec = t.coords(5.0)
    n = t.noise(vec, 1.5, 4, 0.5)
    _set(p, "Base Color", t.mix_color(t.math("MULTIPLY", t.cavity(0.03), 0.8, clamp=True), base, (0.05, 0.045, 0.04)))
    p.inputs["Metallic"].default_value = 1.0
    _set(p, "Roughness", t.maprange(t.noise(vec, 20, 6), 0.3, 0.7, r0 * 0.7, r0 * 1.2))
    _set(p, "Thin Film Thickness", t.maprange(n, 0.2, 0.8, 20.0, 75.0))
    p.inputs["Thin Film IOR"].default_value = 1.6
    _cache[key] = m
    return m


def coil_end(material, color=None, layers=420.0):
    """End face of a wound sheet coil: concentric layer rings (radial distance from local Z)."""
    key = _key("coilend", material, color, layers)
    if key in _cache:
        return _cache[key]
    base, r0, _ = M.METALS.get(material, M.METALS["steel"])
    tint = tuple(color[:3]) if color else ICON_METAL_TINT.get(material)
    if tint:
        base = tuple(b * t for b, t in zip(base, tint))
    m, t = M._new("coil_end")
    p = t.bsdf()
    tc = t.node("ShaderNodeTexCoord")
    s = _sep(t, tc.outputs["Object"])
    rr = t.math("SQRT", t.math("ADD", t.math("MULTIPLY", s.outputs["X"], s.outputs["X"]),
                               t.math("MULTIPLY", s.outputs["Y"], s.outputs["Y"])))
    ring = t.maprange(t.math("SINE", t.math("MULTIPLY", rr, layers * 6.283)), 0.4, 1.0)
    col = t.mix_color(ring, tuple(c * 0.35 for c in base), base)
    _set(p, "Base Color", col)
    p.inputs["Metallic"].default_value = 1.0
    _set(p, "Roughness", t.mix_float(ring, 0.6, r0))
    t.link(t.bump(ring, 0.4, 0.0008), p.inputs["Normal"])
    _cache[key] = m
    return m


def base_color(material, color=None):
    if color:
        return lin(color)
    return MAT_COLOR.get(material, (0.4, 0.4, 0.4))


def is_metal(material):
    return material in METAL_NAMES


# =========================================================================== materials
def _key(*a):
    return tuple(tuple(x) if isinstance(x, list) else x for x in a)


def _sep(t, vec):
    s = t.node("ShaderNodeSeparateXYZ")
    t.link(vec, s.inputs[0])
    return s


def _stretch(t, vec, k):
    n = t.node("ShaderNodeVectorMath", operation="MULTIPLY")
    n.inputs[1].default_value = tuple(k)
    t.link(vec, n.inputs[0])
    return n.outputs["Vector"]


def _voronoi(t, vec, scale, feature="F1", out="Distance", rand=1.0):
    v = t.node("ShaderNodeTexVoronoi", feature=feature)
    t.link(vec, v.inputs["Vector"])
    v.inputs["Scale"].default_value = scale
    v.inputs["Randomness"].default_value = rand
    return v.outputs[out]


# Rock / ore looks: base, base2 (mottle), vein colour + metal, speck colour + metal, roughness.
ORES = {
    "iron_ore": dict(base=(0.12, 0.04, 0.022), base2=(0.035, 0.022, 0.02), vein=(0.06, 0.06, 0.065), vein_metal=0.6,
                     vein_amt=0.35, speck=(0.22, 0.22, 0.24), speck_metal=1.0, speck_amt=0.45, rough=0.8,
                     speck2=(0.3, 0.1, 0.03)),
    "copper_ore": dict(base=(0.075, 0.065, 0.055), base2=(0.03, 0.028, 0.026), vein=(0.02, 0.26, 0.11), vein_amt=0.45,
                       speck=(0.75, 0.48, 0.12), speck_metal=1.0, speck_amt=0.45, rough=0.75, vein2=(0.02, 0.07, 0.4)),
    "coal": dict(base=(0.014, 0.014, 0.015), base2=(0.03, 0.029, 0.028), speck=(0.05, 0.05, 0.05), speck_amt=0.3,
                 rough=0.32, glossy=True),
    "stone": dict(base=(0.24, 0.23, 0.21), base2=(0.1, 0.095, 0.09), speck=(0.02, 0.02, 0.02), speck_amt=0.8, rough=0.8,
                  speck2=(0.6, 0.58, 0.55)),
    "limestone": dict(base=(0.5, 0.46, 0.37), base2=(0.33, 0.3, 0.23), speck=(0.22, 0.2, 0.16), speck_amt=0.3, rough=0.85),
    "bauxite": dict(base=(0.34, 0.1, 0.035), base2=(0.16, 0.05, 0.02), speck=(0.55, 0.22, 0.07), speck_amt=0.8, rough=0.9),
    "ilmenite": dict(base=(0.03, 0.03, 0.033), base2=(0.08, 0.075, 0.07), speck=(0.25, 0.25, 0.27), speck_metal=1.0,
                     speck_amt=0.7, rough=0.5, vein=(0.12, 0.12, 0.13), vein_metal=0.7, vein_amt=0.3),
    "monazite": dict(base=(0.22, 0.17, 0.11), base2=(0.1, 0.08, 0.06), speck=(0.62, 0.32, 0.08), speck_amt=0.9, rough=0.6,
                     vein=(0.5, 0.25, 0.06), vein_amt=0.5),
    "sulfur": dict(base=(0.8, 0.62, 0.03), base2=(0.55, 0.38, 0.015), speck=(0.95, 0.85, 0.2), speck_amt=0.5, rough=0.45),
    "quartz": dict(base=(0.75, 0.75, 0.74), base2=(0.5, 0.5, 0.5), speck=(0.9, 0.9, 0.9), speck_amt=0.3, rough=0.25),
    "salt": dict(base=(0.82, 0.8, 0.78), base2=(0.6, 0.55, 0.5), speck=(0.95, 0.95, 0.95), speck_amt=0.4, rough=0.35),
    "lithium": dict(base=(0.5, 0.42, 0.44), base2=(0.3, 0.27, 0.28), speck=(0.75, 0.72, 0.7), speck_metal=0.3,
                    speck_amt=0.6, rough=0.55, vein=(0.6, 0.5, 0.55), vein_amt=0.4),
    "graphite": dict(base=(0.03, 0.03, 0.034), base2=(0.06, 0.06, 0.065), speck=(0.15, 0.15, 0.16), speck_metal=0.9,
                     speck_amt=0.8, rough=0.42, vein=(0.1, 0.1, 0.11), vein_metal=0.8, vein_amt=0.5),
    "silicon": dict(base=(0.09, 0.1, 0.12), base2=(0.2, 0.21, 0.25), speck=(0.35, 0.36, 0.42), speck_metal=1.0,
                    speck_amt=0.7, rough=0.25, vein_metal=0.9),
    "sand": dict(base=(0.5, 0.36, 0.2), base2=(0.3, 0.2, 0.1), speck=(0.15, 0.1, 0.06), speck_amt=0.6, rough=0.9),
    "uranium_glass": dict(base=(0.025, 0.025, 0.025), base2=(0.06, 0.06, 0.05), vein=(0.4, 0.75, 0.05), vein_amt=0.7,
                          speck=(0.5, 0.9, 0.1), speck_amt=0.6, rough=0.55, emit=(0.35, 1.0, 0.1)),
    "thorium": dict(base=(0.12, 0.1, 0.08), base2=(0.05, 0.045, 0.04), vein=(0.45, 0.32, 0.12), vein_amt=0.5,
                    speck=(0.6, 0.5, 0.3), speck_amt=0.5, rough=0.6),
    "concrete": dict(base=(0.34, 0.33, 0.31), base2=(0.2, 0.19, 0.18), speck=(0.08, 0.08, 0.08), speck_amt=0.5, rough=0.9),
    "brick_clay": dict(base=(0.34, 0.1, 0.045), base2=(0.2, 0.06, 0.03), speck=(0.05, 0.03, 0.02), speck_amt=0.5, rough=0.9),
}


def rock(base=(0.2, 0.19, 0.18), base2=None, vein=None, vein_metal=0.0, vein_amt=0.0, speck=None, speck_metal=0.0,
         speck_amt=0.0, rough=0.75, scale=4.0, emit=None, glossy=False, vein2=None, speck2=None, name="rock"):
    """Natural rock / ore with mottling, mineral veins & patches, glinting specks and grain bump."""
    key = _key("rock", base, base2, vein, vein_metal, vein_amt, speck, speck_metal, speck_amt, rough, scale, emit,
               glossy, vein2, speck2)
    if key in _cache:
        return _cache[key]
    base2 = base2 or tuple(c * 0.5 for c in base)
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(scale)
    n1 = t.noise(vec, 1.6, 6, 0.55)
    n2 = t.noise(vec, 9.0, 8, 0.62)
    col = t.mix_color(t.maprange(n1, 0.3, 0.7), base, base2)
    col = t.mix_color(t.maprange(n2, 0.25, 0.75, 0.0, 0.45), col, tuple(c * 0.45 for c in base))
    metal_v = 0.0
    rough_v = rough
    if vein:
        vn = t.noise(vec, 1.2, 5, 0.55, 2.0)
        band = t.math("ABSOLUTE", t.math("SUBTRACT", vn, 0.5))
        w = 0.025 + 0.06 * vein_amt
        line = t.maprange(band, w, w * 0.45)
        blob = t.maprange(t.noise(vec, 2.2, 6, 0.6, 0.5), 0.66 - 0.16 * vein_amt, 0.7 - 0.16 * vein_amt)
        vm = t.math("MAXIMUM", line, blob)
        vcol = vein
        if vein2:
            vcol = t.mix_color(t.maprange(t.noise(vec, 3.0, 4), 0.45, 0.6), vein, vein2)
        col = t.mix_color(vm, col, vcol)
        metal_v = t.math("MULTIPLY", vm, vein_metal)
        rough_v = t.mix_float(vm, rough, 0.35 if vein_metal > 0.3 else rough * 0.8)
    if speck:
        sp = t.maprange(t.noise(vec, 55.0, 2, 0.5), 0.7 - 0.12 * speck_amt, 0.74 - 0.12 * speck_amt)
        col = t.mix_color(sp, col, speck)
        if speck_metal:
            metal_v = t.math("MAXIMUM", metal_v, t.math("MULTIPLY", sp, speck_metal)) if not isinstance(metal_v, float) \
                else t.math("MULTIPLY", sp, speck_metal)
            rough_v = t.mix_float(sp, rough_v, 0.25)
    if speck2:
        sp2 = t.maprange(t.noise(vec, 40.0, 2, 0.5), 0.3, 0.27)
        col = t.mix_color(sp2, col, speck2)
    # cavity grime
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.04), 0.9, clamp=True), col, tuple(c * 0.25 for c in base))
    _set(p, "Base Color", col)
    _set(p, "Metallic", metal_v)
    _set(p, "Roughness", rough_v)
    if glossy:
        p.inputs["Specular IOR Level"].default_value = 0.7
    if emit:
        em = t.math("MAXIMUM", t.maprange(t.noise(vec, 55.0, 2, 0.5), 0.6, 0.66),
                    t.maprange(t.math("ABSOLUTE", t.math("SUBTRACT", t.noise(vec, 1.2, 5, 0.55, 2.0), 0.5)), 0.06, 0.02))
        p.inputs["Emission Color"].default_value = M._rgba(emit)
        _set(p, "Emission Strength", t.math("MULTIPLY", em, 2.5))
    h = t.math("ADD", t.math("MULTIPLY", n2, 0.6), t.math("MULTIPLY", t.noise(vec, 60.0, 4, 0.6), 0.4))
    t.link(t.bump(h, 0.45, 0.004), p.inputs["Normal"])
    _cache[key] = m
    return m


def _set(p, ident, v):
    M._set(p, ident, v)


def ore(material, color=None, scale=4.0):
    look = dict(ORES.get(material) or {})
    if not look:
        b = base_color(material, color)
        look = dict(base=b, base2=tuple(c * 0.5 for c in b), speck=tuple(min(1, c * 1.6) for c in b), speck_amt=0.4,
                    rough=0.7)
    elif color:
        c = lin(color)
        if "vein" in look:
            look["vein"] = c
        else:
            look["base"] = c
            look["base2"] = tuple(x * 0.5 for x in c)
    return rock(scale=scale, name=f"ore_{material}", **look)


def granular(color, rough=0.92, metal=0.0, sparkle=0.0, scale=1.0, grain=1.0, name="powder"):
    """Fine powder / sand: grain bump, value mottling, optional metallic sparkle."""
    key = _key("gran", color, rough, metal, sparkle, scale, grain)
    if key in _cache:
        return _cache[key]
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(scale)
    g = _voronoi(t, vec, 260.0 * grain)
    mott = t.noise(vec, 6.0, 6, 0.6)
    col = t.mix_color(t.maprange(mott, 0.3, 0.7, 0.0, 0.35), color, tuple(c * 0.55 for c in color))
    col = t.mix_color(t.maprange(g, 0.0, 0.6, 0.25, 0.0), col, tuple(c * 0.4 for c in color))
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.03), 0.8, clamp=True), col, tuple(c * 0.3 for c in color))
    _set(p, "Base Color", col)
    if sparkle or metal:
        sp = t.maprange(t.noise(vec, 400.0 * grain, 1, 0.5), 0.68 - 0.1 * sparkle, 0.72 - 0.1 * sparkle)
        _set(p, "Metallic", t.math("MAXIMUM", sp, metal) if metal else sp)
        _set(p, "Roughness", t.mix_float(sp, rough, 0.3))
    else:
        p.inputs["Roughness"].default_value = rough
    t.link(t.bump(g, 0.5, 0.002), p.inputs["Normal"])
    _cache[key] = m
    return m


def wood(color=(0.3, 0.17, 0.07), axis="x", rough=0.72, scale=1.0, name="wood"):
    """Sawn timber: long grain streaks + fibre bump along `axis`."""
    key = _key("wood", color, axis, rough, scale)
    if key in _cache:
        return _cache[key]
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(scale)
    k = {"x": (0.08, 1.0, 1.0), "y": (1.0, 0.08, 1.0), "z": (1.0, 1.0, 0.08)}[axis]
    sv = _stretch(t, vec, k)
    grain = t.noise(sv, 7.0, 10, 0.62, 3.0)
    rings = t.node("ShaderNodeTexWave", wave_type="BANDS",
                   bands_direction={"x": "Y", "y": "X", "z": "X"}[axis])
    t.link(sv, rings.inputs["Vector"])
    rings.inputs["Scale"].default_value = 4.0
    rings.inputs["Distortion"].default_value = 8.0
    rings.inputs["Detail"].default_value = 4.0
    fib = t.noise(_stretch(t, vec, tuple(x * 10 for x in k)), 30.0, 4, 0.6)
    dark = tuple(c * 0.45 for c in color)
    light = tuple(min(1.0, c * 1.35) for c in color)
    col = t.mix_color(t.maprange(grain, 0.3, 0.7), light, color)
    col = t.mix_color(t.maprange(rings.outputs["Factor"], 0.6, 0.95, 0.0, 0.7), col, dark)
    col = t.mix_color(t.maprange(fib, 0.4, 0.7, 0.0, 0.25), col, dark)
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.05), 0.9, clamp=True), col, tuple(c * 0.2 for c in color))
    _set(p, "Base Color", col)
    _set(p, "Roughness", t.maprange(grain, 0.2, 0.8, rough * 0.85, rough * 1.1))
    t.link(t.bump(t.math("ADD", fib, t.math("MULTIPLY", rings.outputs["Factor"], 0.4)), 0.25, 0.002), p.inputs["Normal"])
    _cache[key] = m
    return m


def bark(color=(0.075, 0.05, 0.035), axis="x", scale=1.0):
    """Rough fissured bark: long irregular ridges along `axis`, lichen blotches."""
    key = _key("bark", color, axis, scale)
    if key in _cache:
        return _cache[key]
    m, t = M._new("bark")
    p = t.bsdf()
    vec = t.coords(scale)
    k = {"x": (3.0, 22.0, 22.0), "y": (22.0, 3.0, 22.0), "z": (22.0, 22.0, 3.0)}[axis]
    sv = _stretch(t, vec, k)
    warp = t.noise(vec, 6.0, 4, 0.6)
    ridges = t.noise(sv, 1.5, 8, 0.7, 2.5)
    fiss = t.maprange(t.math("ADD", ridges, t.math("MULTIPLY", warp, 0.15)), 0.42, 0.62)
    col = t.mix_color(fiss, tuple(c * 0.25 for c in color), color)
    col = t.mix_color(t.maprange(t.noise(vec, 5.0, 6), 0.45, 0.7, 0.0, 0.55), col, (0.12, 0.11, 0.09))
    moss = t.maprange(t.noise(vec, 3.0, 5, 0.6), 0.64, 0.72, 0.0, 0.45)
    col = t.mix_color(moss, col, (0.06, 0.075, 0.025))
    _set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = 0.9
    t.link(t.bump(t.math("ADD", fiss, t.math("MULTIPLY", t.noise(vec, 60, 6), 0.25)), 0.8, 0.008), p.inputs["Normal"])
    _cache[key] = m
    return m


def end_grain(color=(0.42, 0.26, 0.12), axis="x", scale=1.0):
    """Sawn log end: growth rings around the log axis + radial checks."""
    key = _key("endgrain", color, axis, scale)
    if key in _cache:
        return _cache[key]
    m, t = M._new("end_grain")
    p = t.bsdf()
    tc = t.node("ShaderNodeTexCoord")
    s = _sep(t, tc.outputs["Object"])
    a, b = {"x": ("Y", "Z"), "y": ("X", "Z"), "z": ("X", "Y")}[axis]
    rr = t.math("SQRT", t.math("ADD", t.math("MULTIPLY", s.outputs[a], s.outputs[a]),
                               t.math("MULTIPLY", s.outputs[b], s.outputs[b])))
    nz = t.noise(tc.outputs["Object"], 18.0 * scale, 4, 0.5)
    rr = t.math("ADD", rr, t.math("MULTIPLY", nz, 0.006))
    ring = t.math("SINE", t.math("MULTIPLY", rr, 260.0 * scale))
    ringm = t.maprange(ring, 0.55, 0.95)
    dark = tuple(c * 0.55 for c in color)
    col = t.mix_color(ringm, color, dark)
    col = t.mix_color(t.maprange(rr, 0.0, 0.05, 0.35, 0.0), col, tuple(c * 0.7 for c in color))
    _set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = 0.85
    t.link(t.bump(t.math("ADD", ringm, t.math("MULTIPLY", t.noise(tc.outputs["Object"], 80, 4), 0.5)), 0.25, 0.002),
           p.inputs["Normal"])
    _cache[key] = m
    return m


def fabric(color=(0.3, 0.21, 0.1), weave=320.0, rough=0.85, name="fabric", coarse=1.0):
    """Woven sack cloth (jute / polypropylene)."""
    key = _key("fabric", color, weave, rough, coarse)
    if key in _cache:
        return _cache[key]
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    w = []
    for d in ("X", "Z"):
        wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=d)
        t.link(vec, wv.inputs["Vector"])
        wv.inputs["Scale"].default_value = weave
        wv.inputs["Distortion"].default_value = 0.6 * coarse
        w.append(wv.outputs["Factor"])
    wy = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    t.link(vec, wy.inputs["Vector"])
    wy.inputs["Scale"].default_value = weave
    h = t.math("MAXIMUM", t.math("MAXIMUM", w[0], w[1]), wy.outputs["Factor"])
    mott = t.noise(vec, 8.0, 6, 0.6)
    col = t.mix_color(t.maprange(mott, 0.3, 0.7, 0.0, 0.3 * coarse), color, tuple(c * 0.6 for c in color))
    col = t.mix_color(t.maprange(h, 0.2, 0.9, 0.35, 0.0), col, tuple(c * 0.5 for c in color))
    col = t.mix_color(t.math("MULTIPLY", t.cavity(0.06), 0.8, clamp=True), col, tuple(c * 0.25 for c in color))
    _set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Sheen Weight"].default_value = 0.4
    p.inputs["Sheen Roughness"].default_value = 0.5
    t.link(t.bump(h, 0.35, 0.0015), p.inputs["Normal"])
    _cache[key] = m
    return m


def liquid(color, mode="clear", strength=None):
    """Coloured liquid that stays opaque in the alpha channel (so it keeps its colour over any UI).

    mode: clear (translucent glowing body via SSS), opaque (oil / slurry), glow (emissive plasma-like).
    """
    key = _key("liquid", color, mode, strength)
    if key in _cache:
        return _cache[key]
    m, t = M._new(f"liquid_{mode}")
    p = t.bsdf()
    c = lin(color)
    lw = t.node("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    face = lw.outputs["Facing"]
    rim = tuple(x * 0.35 for x in c)
    core = tuple(min(1.0, x * 1.15 + 0.02) for x in c)
    p.inputs["IOR"].default_value = 1.34
    p.inputs["Roughness"].default_value = 0.04
    if mode == "opaque":
        _set(p, "Base Color", t.mix_color(face, c, rim))
        p.inputs["Roughness"].default_value = 0.08
        p.inputs["Coat Weight"].default_value = 1.0
        p.inputs["Coat Roughness"].default_value = 0.03
    else:
        _set(p, "Base Color", t.mix_color(face, core, rim))
        p.inputs["Subsurface Weight"].default_value = 1.0
        p.inputs["Subsurface Radius"].default_value = tuple(0.05 + 0.95 * x for x in c)
        p.inputs["Subsurface Scale"].default_value = 0.03
        p.inputs["Emission Color"].default_value = M._rgba(glow_color(c) if mode == "glow" else c)
        s = strength if strength is not None else (1.2 if mode == "glow" else 0.25)
        _set(p, "Emission Strength", t.math("MULTIPLY", t.math("SUBTRACT", 1.0, face), s))
        p.inputs["Coat Weight"].default_value = 1.0
        p.inputs["Coat Roughness"].default_value = 0.02
    _cache[key] = m
    return m


def gas_volume(color, density=6.0, glow=0.0):
    key = _key("gasvol", color, density, glow)
    if key in _cache:
        return _cache[key]
    m, t = M._new("gas")
    out = t.nodes.get("Material Output") or t.node("ShaderNodeOutputMaterial")
    for n in list(t.nodes):
        if n.type == "BSDF_PRINCIPLED":
            t.nodes.remove(n)
    pv = t.node("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = M._rgba(lin(color))
    nz = t.noise(t.coords(8.0), 1.0, 4, 0.6)
    _set(pv, "Density", t.maprange(nz, 0.2, 0.8, density * 0.5, density * 1.3))
    pv.inputs["Absorption Color"].default_value = M._rgba(tuple(0.4 + 0.6 * x for x in lin(color)))
    if glow:
        pv.inputs["Emission Strength"].default_value = glow
        pv.inputs["Emission Color"].default_value = M._rgba(lin(color))
    t.link(pv.outputs[0], out.inputs["Volume"])
    _cache[key] = m
    return m


def gem(color=(0.6, 0.8, 1.0), rough=0.03, opacity=0.5, glow=0.0):
    """Crystal: refractive with enough body colour (SSS) to stay coloured over a transparent film."""
    key = _key("gem", color, rough, opacity, glow)
    if key in _cache:
        return _cache[key]
    m, t = M._new("gem")
    p = t.bsdf()
    c = lin(color)
    p.inputs["Base Color"].default_value = M._rgba(c)
    p.inputs["Roughness"].default_value = rough
    p.inputs["IOR"].default_value = 1.55
    p.inputs["Transmission Weight"].default_value = 1.0 - opacity
    p.inputs["Subsurface Weight"].default_value = opacity
    p.inputs["Subsurface Radius"].default_value = tuple(0.3 + 0.7 * x for x in c)
    p.inputs["Subsurface Scale"].default_value = 0.04
    p.inputs["Coat Weight"].default_value = 0.6
    if glow:
        p.inputs["Emission Color"].default_value = M._rgba(c)
        p.inputs["Emission Strength"].default_value = glow
    _cache[key] = m
    return m


def lab_glass(tint=(0.93, 0.98, 0.97)):
    return M.glass(tint, 0.0, name="lab_glass")


def coated_glass(tint=(0.95, 0.98, 0.98)):
    """Optical glass with an anti-reflection coating sheen (thin film)."""
    key = _key("coated", tint)
    if key in _cache:
        return _cache[key]
    m, t = M._new("coated_glass")
    p = t.bsdf()
    p.inputs["Base Color"].default_value = M._rgba(tint)
    p.inputs["Roughness"].default_value = 0.0
    p.inputs["Transmission Weight"].default_value = 1.0
    p.inputs["IOR"].default_value = 1.52
    p.inputs["Thin Film Thickness"].default_value = 280.0
    p.inputs["Thin Film IOR"].default_value = 1.38
    _cache[key] = m
    return m


def pv_cell(color=(0.012, 0.022, 0.07)):
    """Mono-crystalline PV cell: deep blue, fine silver fingers, glossy cover glass."""
    key = _key("pv", color)
    if key in _cache:
        return _cache[key]
    m, t = M._new("pv_cell")
    p = t.bsdf()
    tc = t.node("ShaderNodeTexCoord")
    wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    t.link(tc.outputs["Object"], wv.inputs["Vector"])
    wv.inputs["Scale"].default_value = 160.0
    fing = t.maprange(wv.outputs["Factor"], 0.93, 0.97)
    col = t.mix_color(t.maprange(t.noise(tc.outputs["Object"], 30, 4), 0.3, 0.7, 0.0, 0.3), color,
                      tuple(c * 1.8 for c in color))
    col = t.mix_color(fing, col, (0.55, 0.55, 0.56))
    _set(p, "Base Color", col)
    _set(p, "Metallic", fing)
    p.inputs["Roughness"].default_value = 0.25
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.02
    _cache[key] = m
    return m


def anodized(color=(0.02, 0.02, 0.022), rough=0.35):
    key = _key("anod", color, rough)
    if key in _cache:
        return _cache[key]
    m, t = M._new("anodized")
    p = t.bsdf()
    vec = t.coords(1.0)
    _set(p, "Base Color", t.mix_color(t.math("MULTIPLY", t.cavity(0.05), 0.7, clamp=True), color,
                                      tuple(c * 0.3 for c in color)))
    p.inputs["Metallic"].default_value = 0.85
    _set(p, "Roughness", t.maprange(t.noise(vec, 20, 4), 0.3, 0.7, rough * 0.8, rough * 1.2))
    p.inputs["Anisotropic"].default_value = 0.3
    _cache[key] = m
    return m


def surf(material, color=None, scale=4.0):
    """Best icon material for a schema material name.

    Natural / raw materials get the procedural rock, wood and powder looks defined here; everything
    else maps through materials.from_spec (metals, plastics, glass, paint, glow ...).
    """
    c = lin(color) if color else None
    if material in ORES and material not in ("concrete", "brick_clay", "quartz", "salt", "silicon", "graphite",
                                             "lithium", "uranium_glass", "thorium"):
        return ore(material, color, scale)
    if material == "wood":
        return wood(c or MAT_COLOR["wood"])
    if material == "concrete":
        return M.concrete(4.0, tint=c)
    if material == "brick_clay":
        return rock(base=c or (0.34, 0.1, 0.045), base2=(0.22, 0.065, 0.03), speck=(0.05, 0.03, 0.02), speck_amt=0.4,
                    rough=0.9, scale=6.0, name="brick_clay")
    if material in ("quartz", "salt"):
        return gem(c or MAT_COLOR[material], 0.15, 0.85)
    if material == "crystal":
        return gem(c or MAT_COLOR["crystal"], 0.03, 0.45)
    if material == "uranium_glass":
        return gem(c or (0.35, 1.0, 0.15), 0.08, 0.7, glow=2.5)
    if material == "silicon":
        return M.metal("dark_steel", rough=0.12, tint=(0.75, 0.82, 1.0), dirt=0.2)
    if material == "graphite":
        return M.metal("dark_steel", rough=0.45, dirt=0.3)
    if material == "carbon_fiber":
        return carbon_fiber()
    if material == "ceramic":
        return M.plastic(c or (0.82, 0.8, 0.74), 0.45, name="ceramic")
    if material == "coal":
        return ore("coal", None, scale)
    return M.from_spec(material, color)


def carbon_fiber():
    key = ("cf",)
    if key in _cache:
        return _cache[key]
    m, t = M._new("carbon_fiber")
    p = t.bsdf()
    vec = t.coords(1.0)
    chk = t.node("ShaderNodeTexChecker")
    t.link(vec, chk.inputs["Vector"])
    chk.inputs["Scale"].default_value = 120.0
    chk.inputs["Color1"].default_value = (0.012, 0.012, 0.014, 1)
    chk.inputs["Color2"].default_value = (0.045, 0.045, 0.05, 1)
    t.link(chk.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.35
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.05
    p.inputs["Anisotropic"].default_value = 0.5
    _cache[key] = m
    return m


def powder_for(material, color=None):
    c = base_color(material, color)
    if is_metal(material) or material in ("graphite", "silicon", "ilmenite"):
        return granular(tuple(x * 0.55 for x in c), rough=0.75, sparkle=0.9, name="metal_powder")
    if material in ("glow", "uranium_glass"):
        return gem(c, 0.5, 0.95, glow=1.5)
    return granular(c, sparkle=0.3 if material in ("sand", "quartz", "salt", "sulfur") else 0.0)


def paint(color, wear=0.35, grime=0.4, rough=0.42, rust=0.15, name="paint", coat=0.0, scale=2.0):
    return M.painted(lin(color), wear=wear, grime=grime, rough=rough, rust=rust, name=name, gloss_coat=coat,
                     scale=scale)


def dark_metal():
    return M.metal("dark_steel", dirt=0.4)


def text_color_mat(color=(0.85, 0.85, 0.82)):
    return M.plastic(color, 0.5, name="print")


# =========================================================================== mesh builders
def finish(name, bm, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segments=2, smooth=35.0):
    return K._finish(name, bm, mat, loc, rot, bevel, segments, smooth)


def set_mats(o, mats):
    """Replace an object's material slots with `mats` (list)."""
    o.data.materials.clear()
    for m in mats:
        o.data.materials.append(m)
    return o


def lathe(profile, mat=None, segs=48, name="lathe", loc=(0, 0, 0), rot=(0, 0, 0), closed=False, bevel=0.0,
          smooth=40.0, mat_ids=None, mats=None):
    """Surface of revolution of a (r, z) profile around local Z.

    Walk the profile so the solid is on your right when looking along +theta (e.g. bottom centre ->
    out -> up -> in -> top centre, or outer wall up / lip / inner wall down for vessels); faces then
    point outwards. r == 0 makes a pole. `mat_ids[i]` = material slot of profile segment i (needs `mats`).
    """
    bm = bmesh.new()
    angs = [2 * math.pi * i / segs for i in range(segs)]
    rings = []
    for r, z in profile:
        if r <= 1e-7:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in angs])
    pairs = list(zip(rings, rings[1:]))
    if closed:
        pairs.append((rings[-1], rings[0]))
    fmi = []
    for si, (A, B) in enumerate(pairs):
        if len(A) == 1 and len(B) == 1:
            continue
        mi = mat_ids[si] if mat_ids and si < len(mat_ids) else 0
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1:
                bm.faces.new((A[0], B[j], B[i]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[j], B[0]))
            else:
                bm.faces.new((A[i], A[j], B[j], B[i]))
            fmi.append(mi)
    o = finish(name, bm, mat if mat is not None else (mats[0] if mats else None), loc, rot, bevel, smooth=smooth)
    if mats:
        set_mats(o, mats)
        if mat_ids:
            o.data.polygons.foreach_set("material_index", fmi)
            o.data.update()
    return o


def _fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def ring_extrude(outer, inner, z0, z1, mat=None, name="ring", loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, smooth=35.0):
    """Extrude the area between two closed XY loops with the same vertex count (gears, washers)."""
    bm = bmesh.new()
    n = len(outer)
    ob = [bm.verts.new((x, y, z0)) for x, y in outer]
    ot = [bm.verts.new((x, y, z1)) for x, y in outer]
    ib = [bm.verts.new((x, y, z0)) for x, y in inner]
    it = [bm.verts.new((x, y, z1)) for x, y in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((it[i], it[j], ib[j], ib[i]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ib[i], ib[j], ob[j], ob[i]))
    _fix_normals(bm)
    return finish(name, bm, mat, loc, rot, bevel, smooth=smooth)


def poly_extrude(pts, z0, z1, mat=None, name="poly", loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, smooth=35.0):
    """Extrude a closed XY polygon (may be concave) from z0 to z1."""
    bm = bmesh.new()
    b = [bm.verts.new((x, y, z0)) for x, y in pts]
    t = [bm.verts.new((x, y, z1)) for x, y in pts]
    n = len(pts)
    bm.faces.new(list(reversed(b)))
    bm.faces.new(t)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))
    _fix_normals(bm)
    return finish(name, bm, mat, loc, rot, bevel, smooth=smooth)


def _frames(path, closed=False):
    """Rotation-minimising frames (tangent, normal, binormal) along a polyline."""
    pts = [Vector(p) for p in path]
    n = len(pts)
    tans = []
    for i in range(n):
        if closed:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tans.append((b - a).normalized())
    t0 = tans[0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    nrm = (ref - t0 * ref.dot(t0)).normalized()
    out = []
    for i in range(n):
        t = tans[i]
        if i > 0:
            # parallel transport
            nrm = (nrm - t * nrm.dot(t)).normalized()
        out.append((t, nrm, t.cross(nrm)))
    return pts, out


def sweep(path, section, mat=None, name="sweep", closed=False, caps=True, bevel=0.0, smooth=35.0, scale_fn=None):
    """Sweep a closed 2D section [(u, v)...] along a 3D polyline. u -> frame normal, v -> binormal."""
    pts, frames = _frames(path, closed)
    bm = bmesh.new()
    rings = []
    N = len(pts)
    for i, (p, (t, nrm, bn)) in enumerate(zip(pts, frames)):
        k = scale_fn(i / max(1, N - 1)) if scale_fn else 1.0
        rings.append([bm.verts.new(p + nrm * (u * k) + bn * (v * k)) for u, v in section])
    m = len(section)
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for A, B in pairs:
        for i in range(m):
            j = (i + 1) % m
            bm.faces.new((A[i], A[j], B[j], B[i]))
    if caps and not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    _fix_normals(bm)
    return finish(name, bm, mat, (0, 0, 0), (0, 0, 0), bevel, smooth=smooth)


def circle_section(r, n=12):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rect_section(w, h, chamfer=0.0):
    if chamfer <= 0:
        return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    c = chamfer
    return [(-w / 2 + c, -h / 2), (w / 2 - c, -h / 2), (w / 2, -h / 2 + c), (w / 2, h / 2 - c), (w / 2 - c, h / 2),
            (-w / 2 + c, h / 2), (-w / 2, h / 2 - c), (-w / 2, -h / 2 + c)]


def helix_points(r, pitch, turns, z0=0.0, res=40, start=0.0, r_fn=None):
    pts = []
    n = max(2, int(turns * res))
    for i in range(n + 1):
        u = i / n
        a = start + 2 * math.pi * turns * u
        rr = r_fn(u) if r_fn else r
        pts.append((rr * math.cos(a), rr * math.sin(a), z0 + pitch * turns * u))
    return pts


def curve_tube(points, r, mat=None, name="wire", res=3, smooth=True, caps=True):
    """Smooth round tube through points (NURBS-free poly curve, use dense points)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = caps
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_smooth = smooth
    o = bpy.data.objects.new(name, cu)
    K.collection().objects.link(o)
    if mat:
        cu.materials.append(mat)
    return o


def text_mesh(s, size=0.05, depth=0.002, mat=None, font=FONT_BOLD, loc=(0, 0, 0), rot=(0, 0, 0), align="CENTER",
              name="text", spacing=1.0):
    """Mesh text in the local XY plane (reads from +Z), centred, extruded `depth` along +Z from 0."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    if font and os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.space_character = spacing
    cu.offset_y = 0
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    K.collection().objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.transform(Matrix.Translation((0, 0, depth / 2)))
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)  # weld caps to sides -> manifold
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    K.collection().objects.link(o)
    if mat:
        me.materials.append(mat)
    o.location = Vector(loc)
    o.rotation_euler = Euler(rot, "XYZ")
    return o


def wrap_patch(r, a_center, width, z0, z1, mat=None, thick=0.0015, segs=24, name="label"):
    """Curved label / band patch on a cylinder of radius r around Z (angles in radians)."""
    bm = bmesh.new()
    rows = []
    for rad in (r, r + thick):
        ring = []
        for i in range(segs + 1):
            a = a_center - width / 2 + width * i / segs
            ring.append((bm.verts.new((rad * math.cos(a), rad * math.sin(a), z0)),
                         bm.verts.new((rad * math.cos(a), rad * math.sin(a), z1))))
        rows.append(ring)
    inner, outer = rows
    for i in range(segs):
        bm.faces.new((outer[i][0], outer[i + 1][0], outer[i + 1][1], outer[i][1]))
        bm.faces.new((inner[i][1], inner[i + 1][1], inner[i + 1][0], inner[i][0]))
        bm.faces.new((outer[i][1], outer[i + 1][1], inner[i + 1][1], inner[i][1]))
        bm.faces.new((inner[i][0], inner[i + 1][0], outer[i + 1][0], outer[i][0]))
    bm.faces.new((inner[0][0], outer[0][0], outer[0][1], inner[0][1]))
    bm.faces.new((outer[-1][0], inner[-1][0], inner[-1][1], outer[-1][1]))
    _fix_normals(bm)
    return finish(name, bm, mat, smooth=60)


def wrap_text(s, r, a_center, z, size, mat=None, depth=0.0008, font=FONT_BOLD, name="wtext"):
    """Text bent around a cylinder (radius r, around Z), centred at angle a_center, height z."""
    o = text_mesh(s, size, depth, mat, font, name=name)
    me = o.data
    for v in me.vertices:
        x, y, d = v.co
        th = a_center + x / r
        rad = r + d
        v.co = (rad * math.cos(th), rad * math.sin(th), z + y)
    me.update()
    return o


def project_text(s, size, center, normal, up=(0, 0, 1), mat=None, depth=0.0008, font=FONT_BOLD, name="ptext"):
    """Flat text placed at `center` facing `normal` (decal-style print on a flat face)."""
    o = text_mesh(s, size, depth, mat, font, name=name)
    n = Vector(normal).normalized()
    u = Vector(up)
    u = (u - n * u.dot(n)).normalized()
    xax = u.cross(n)
    m = Matrix((xax, u, n)).transposed().to_4x4()
    o.matrix_world = Matrix.Translation(Vector(center)) @ m
    return o


def apply_boolean(obj, cutter, op="DIFFERENCE", solver="MANIFOLD"):
    """Boolean `cutter` into obj's mesh data (before its bevel modifier) and delete the cutter."""
    mod = obj.modifiers.new("cut", "BOOLEAN")
    mod.operation = op
    mod.solver = solver
    mod.object = cutter
    obj.modifiers.move(len(obj.modifiers) - 1, 0)
    bpy.context.view_layer.update()
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    me = cutter.data
    bpy.data.objects.remove(cutter)
    if me and me.users == 0:
        bpy.data.meshes.remove(me)
    K._sharp_edges(obj.data, 35.0)
    return obj


def cutter_cyls(centers, r, depth, axis="z", verts=24):
    """One mesh holding several cylinders (boolean cutters) centred on `centers`."""
    bm = bmesh.new()
    rot = Euler(K.AXES[axis], "XYZ").to_matrix().to_4x4()
    for c in centers:
        geom = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r, radius2=r, depth=depth)
        bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(c)) @ rot, verts=geom["verts"])
    me = bpy.data.meshes.new("cutter")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("cutter", me)
    K.collection().objects.link(o)
    o.hide_render = True
    return o


def drill(obj, centers, r, depth, axis="z", verts=24):
    return apply_boolean(obj, cutter_cyls(centers, r, depth, axis, verts))


def stamp(obj, s, size, loc, rot=(0, 0, 0), depth=0.002, font=FONT_BOLD):
    """Stamp (engrave) text into obj; loc is on the surface, text faces local +Z of `rot`."""
    t = text_mesh(s, size, depth * 2, None, font, name="stamp_cut")
    m = Euler(rot, "XYZ").to_matrix().to_4x4()
    t.data.transform(Matrix.Translation((0, 0, -depth)))
    t.matrix_world = Matrix.Translation(Vector(loc)) @ m
    return apply_boolean(obj, t)


def rock_mesh(r=0.1, seed=0, cuts=7, subdiv=3, bump=0.12, squash=(1.0, 1.0, 0.8), name="rock", mat=None,
              detail=0.04, sharp=30.0):
    """Faceted rock: icosphere, random fracture planes (bisect + fill), fractal surface noise."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bmesh.ops.scale(bm, vec=squash, verts=bm.verts)
    off = Vector((rnd.uniform(-50, 50), rnd.uniform(-50, 50), rnd.uniform(-50, 50)))
    for v in bm.verts:
        p = v.co / r * 1.3 + off
        d = noise.fractal(p, 0.8, 2.0, 3) * bump * r
        v.co += v.co.normalized() * d
    for _ in range(cuts):
        n = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        dist = r * rnd.uniform(0.55, 0.85)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=n * dist, plane_no=n, clear_outer=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            try:
                f = bmesh.ops.edgeloop_fill(bm, edges=edges)
                for face in f["faces"]:
                    bmesh.ops.poke(bm, faces=[face])
            except Exception:
                bmesh.ops.holes_fill(bm, edges=edges)
    # fine displacement so fracture planes are not perfectly flat
    off2 = off * 1.7
    for v in bm.verts:
        p = v.co / r * 4.0 + off2
        v.co += Vector(noise.noise_vector(p)) * detail * r
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return finish(name, bm, mat, (0, 0, 0), (0, 0, 0), 0.0, smooth=sharp)


def heap(r=0.25, h=0.15, seed=0, rings=28, segs=72, rough=0.06, name="heap", mat=None, slump=1.0, lumps=0.25):
    """Conical pile (angle-of-repose profile, rounded top, irregular rim) resting on z=0."""
    rnd = random.Random(seed)
    off = Vector((rnd.uniform(-50, 50), rnd.uniform(-50, 50), 0))
    bm = bmesh.new()
    top = bm.verts.new((0, 0, h))
    grid = []
    for i in range(1, rings + 1):
        u = i / rings
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            rim = 1.0 + lumps * noise.fractal(Vector((math.cos(a) * 1.5, math.sin(a) * 1.5, 0)) + off, 0.7, 2.0, 3)
            rr = r * u * rim
            x, y = rr * math.cos(a), rr * math.sin(a)
            prof = (1 - u ** (1.25 * slump)) ** 1.15
            z = h * prof
            z += h * rough * noise.fractal(Vector((x / r * 3, y / r * 3, 0)) + off, 0.6, 2.0, 4) * (1 - u ** 4)
            row.append(bm.verts.new((x, y, max(0.0, z) if i < rings else 0.0)))
        grid.append(row)
    for j in range(segs):
        k = (j + 1) % segs
        bm.faces.new((top, grid[0][j], grid[0][k]))
    for i in range(rings - 1):
        A, B = grid[i], grid[i + 1]
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((A[j], B[j], B[k], A[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return finish(name, bm, mat, (0, 0, 0), (0, 0, 0), 0.0, smooth=80.0)


def heap_height(r, h, x, y, slump=1.0):
    u = min(1.0, math.hypot(x, y) / r)
    return h * (1 - u ** (1.25 * slump)) ** 1.15


def dup(o, loc=None, rot=None, scale=None, linked=True):
    """Duplicate an object (linked mesh data by default) - cheap instancing for scatter."""
    c = o.copy()
    if not linked and o.data:
        c.data = o.data.copy()
    K.collection().objects.link(c)
    if loc is not None:
        c.location = Vector(loc)
    if rot is not None:
        c.rotation_euler = Euler(rot, "XYZ")
    if scale is not None:
        c.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    return c


def ground(objs, z=0.0):
    """Translate objects (or their top-level parents) so the group's lowest vertex sits on z."""
    pts = points(objs)
    if pts is None:
        return 0.0
    dz = z - float(pts[:, 2].min())
    roots = []
    for o in objs:
        r = o
        while r.parent is not None:
            r = r.parent
        if r not in roots:
            roots.append(r)
    for r in roots:
        r.location.z += dz
    bpy.context.view_layer.update()
    return dz


def group(objs, loc=(0, 0, 0), rot=(0, 0, 0), name="group"):
    """Parent `objs` (or their top-level ancestors) to a new empty at the origin, then move / rotate
    the whole group. Nested groups are kept intact."""
    piv = K.pivot(name)
    roots = []
    for o in objs:
        if o is None:
            continue
        r = o
        while r.parent is not None:
            r = r.parent
        if r is not piv and r not in roots:
            roots.append(r)
    bpy.context.view_layer.update()
    for r in roots:
        mw = r.matrix_world.copy()
        r.parent = piv
        r.matrix_parent_inverse = Matrix.Identity(4)
        r.matrix_world = mw
    piv.location = Vector(loc)
    piv.rotation_euler = Euler(rot, "XYZ")
    bpy.context.view_layer.update()
    return piv


def model_objects():
    return [o for o in K.collection().all_objects if o.type in {"MESH", "CURVE", "FONT", "SURFACE"} and not o.hide_render]


# =========================================================================== bounds / framing
def points(objs=None, max_pts=40000):
    """World-space vertex cloud (numpy Nx3) of evaluated render objects."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    objs = objs if objs is not None else model_objects()
    chunks = []
    for o in objs:
        if o.type not in {"MESH", "CURVE", "FONT", "SURFACE"} or o.hide_render:
            continue
        eo = o.evaluated_get(dg)
        try:
            me = eo.to_mesh()
        except RuntimeError:
            continue
        n = len(me.vertices)
        if n:
            arr = np.empty(n * 3, dtype=np.float32)
            me.vertices.foreach_get("co", arr)
            arr = arr.reshape(-1, 3).astype(np.float64)
            mw = np.array(eo.matrix_world)
            chunks.append(arr @ mw[:3, :3].T + mw[:3, 3])
        eo.to_mesh_clear()
    if not chunks:
        return None
    P = np.concatenate(chunks)
    if len(P) > max_pts:
        P = P[:: max(1, len(P) // max_pts)]
    return P


def bounds(objs=None):
    """Bounding sphere (radius, centre) around the bbox centre of the model."""
    P = points(objs)
    if P is None:
        return 0.3, (0, 0, 0.15)
    lo, hi = P.min(0), P.max(0)
    c = (lo + hi) / 2
    r = float(np.sqrt(((P - c) ** 2).sum(1)).max())
    return r, tuple(float(x) for x in c)


def fit_camera(cam, fill=0.8, shadow_dir=None, shadow_k=0.55, shadow_fill=0.95, P=None):
    """Adjust focal length and lens shift so the model's projected bbox fills `fill` of the frame
    (centred) while its approximate soft shadow stays within `shadow_fill`."""
    P = points() if P is None else P
    if P is None:
        return
    cd = cam.data
    cd.shift_x = cd.shift_y = 0.0
    bpy.context.view_layer.update()
    mi = np.array(cam.matrix_world.inverted())

    def proj(Q):
        Qc = Q @ mi[:3, :3].T + mi[:3, 3]
        z = -Qc[:, 2]
        return Qc[:, 0] / z, Qc[:, 1] / z

    x, y = proj(P)
    cx, cy = (x.min() + x.max()) / 2, (y.min() + y.max()) / 2
    ext = max(x.max() - x.min(), y.max() - y.min())
    sensor = cd.sensor_width
    lens = sensor * fill / ext
    if shadow_dir is not None:
        L = np.array(shadow_dir, dtype=np.float64)
        h = np.clip(P[:, 2], 0, None)
        S = P + np.outer(h / max(1e-6, -L[2]), L) * shadow_k
        S[:, 2] = 0.0
        xs, ys = proj(S)
        hs = max(np.abs(xs - cx).max(), np.abs(ys - cy).max(), 1e-6)
        lens = min(lens, sensor * shadow_fill / 2 / hs)
    cd.lens = lens
    cd.shift_x = cx * lens / sensor
    cd.shift_y = cy * lens / sensor


# =========================================================================== lighting
def _area(name, loc, target, size, power, color=(1, 1, 1), shape="RECTANGLE", size_y=None, shadow=True):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = shape
    d.size = size
    if size_y:
        d.size_y = size_y
    d.energy = power
    d.color = color
    try:
        d.use_shadow = shadow
    except Exception:
        pass
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def _dir(azimuth_deg, elev_deg):
    a, e = math.radians(azimuth_deg), math.radians(elev_deg)
    return Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))


# Light rig expressed relative to the camera azimuth (camera sits at azimuth CAM_AZ, looking back
# at the model): key front-left-high, fill front-right-low, rim back-right, top softbox.
CAM_AZ = -55.0
RIG = {
    "key": dict(az=-112.0, el=50.0, dist=6.0, size=1.8, irr=1.45, color=(1.0, 0.95, 0.88)),
    "fill": dict(az=5.0, el=18.0, dist=7.0, size=5.0, irr=0.16, color=(0.86, 0.92, 1.0), shadow=False),
    "rim": dict(az=95.0, el=28.0, dist=6.0, size=2.0, irr=1.0, color=(0.92, 0.96, 1.0), shadow=False),
    "top": dict(az=-60.0, el=82.0, dist=6.0, size=4.0, irr=0.18, color=(1.0, 1.0, 1.0), shadow=False),
}


def key_dir(az_off=0.0):
    """Direction the key light travels (towards the ground) - for shadow-aware framing."""
    k = RIG["key"]
    return tuple(-_dir(k["az"] + az_off, k["el"]))


def icon_lights(center, radius, az_off=0.0, rig=RIG, scale=1.0):
    """Softbox rig scaled to the model; az_off rotates it with a non-default camera yaw."""
    c = Vector(center)
    out = []
    for name, L in rig.items():
        d = L["dist"] * radius
        loc = c + _dir(L["az"] + az_off, L["el"]) * d
        power = L["irr"] * math.pi * d * d * scale
        out.append(_area(name, loc, c, L["size"] * radius, power, L["color"], shadow=L.get("shadow", True)))
    return out


def icon_scene(quality, hdri="empty_warehouse_01_2k.hdr", hdri_strength=0.25):
    s = studio.reset(quality, hdri=hdri, hdri_strength=hdri_strength, sun=0)
    reset()
    s.view_settings.exposure = 0.0
    s.cycles.film_transparent_glass = True
    s.cycles.film_transparent_roughness = 0.1
    s.cycles.transmission_bounces = 12
    s.cycles.max_bounces = 12
    s.cycles.volume_bounces = 1
    return s


# =========================================================================== contact sheets
SHEET_SCRIPT = r"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
spec = json.loads(sys.argv[1])
cell, cols = spec["cell"], spec["cols"]
entries = spec["entries"]
rows = (len(entries) + cols - 1) // cols
lab = 16
W, H = cols * cell, rows * (cell + lab)
sheet = Image.new("RGBA", (W, H), (36, 38, 42, 255))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
except Exception:
    font = ImageFont.load_default()
d = ImageDraw.Draw(sheet)
for i, (path, label) in enumerate(entries):
    x, y = (i % cols) * cell, (i // cols) * (cell + lab)
    bg = (36, 38, 42, 255) if (i // cols + i % cols) % 2 == 0 else (58, 60, 66, 255)
    d.rectangle([x, y, x + cell - 1, y + cell + lab - 1], fill=bg)
    try:
        im = Image.open(path).convert("RGBA")
    except Exception:
        continue
    big = im.copy()
    big.thumbnail((cell, cell), Image.LANCZOS)
    sheet.alpha_composite(big, (x + (cell - big.width) // 2, y + (cell - big.height) // 2))
    if spec.get("small"):
        s = spec["small"]
        sm = im.resize((s, s), Image.LANCZOS)
        d.rectangle([x + cell - s - 3, y + 1, x + cell - 1, y + s + 3], fill=(20, 21, 24, 255))
        sheet.alpha_composite(sm, (x + cell - s - 2, y + 2))
    d.text((x + 3, y + cell + 1), label[:28], fill=(220, 220, 220, 255), font=font)
sheet.convert("RGB").save(spec["out"])
print("sheet", spec["out"], W, H)
"""


def contact_sheet(entries, out, cell=128, cols=8, small=48):
    """entries = [(png_path, label)] -> labelled sheet PNG (each cell shows a 48 px inset too)."""
    if not entries:
        return
    spec = json.dumps({"entries": entries, "out": out, "cell": cell, "cols": min(cols, len(entries)), "small": small})
    py = VENV_PY if os.path.exists(VENV_PY) else "python3"
    try:
        subprocess.run([py, "-c", SHEET_SCRIPT, spec], check=False, timeout=120)
    except Exception as e:  # pragma: no cover
        print("[sheet] failed:", e)
