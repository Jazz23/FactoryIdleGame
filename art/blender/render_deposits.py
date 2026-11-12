"""Render resource-deposit ground patches (isometric, same camera / light as buildings).

blender -b -P art/blender/render_deposits.py -- [--all] [--ids a,b] [--missing] [--quality preview|draft|final]

Reads data/world.json ``deposits`` ({id, name, item, kind, visual}) and writes
assets/env/deposit_<id>.png (transparent, soft alpha edge) and assets/env/deposit_<id>.json
{"origin": [x, y]} (pixel of the patch centre on the ground; vents add optional "emitters" hints).
A contact sheet of the batch goes to art/render/icons/deposits/sheet.png.

Concept: the deposit is a ~4 x 4 m patch where the factory's concrete floor slab has broken open and the
resource shows through. Layers:
  * apron   - the same scanned concrete as assets/env/floor_tile.png (same scale / lighting), carrying the
              resource's spill (ore dust, oil stain, salt bloom, wet halo) and radial cracks, and fading to
              alpha 0 so it cross-fades into the in-game floor;
  * break   - ragged slab edge with spalled rim, exposed aggregate, rebar stubs and fallen slab fragments;
  * ground  - style-specific terrain inside the opening (ore chunks in dirt, rubble, sand, bedrock with a
              quartz vein, fumarole / gas fissure with mineral crust, water / oil / brine pools).
Everything stays low (rocks <= ~0.25 m above the floor) because mining machines stand on top.

Styles: ore_field, rubble, placer, sand_bar, lode, fumarole, gas_vent, water_pool, oil_seep, brine_flat
(per-id looks in LOOKS; unknown deposits fall back to style_of()).
"""
import bisect
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

import kit as K  # noqa: E402
import kit_icons as KI  # noqa: E402
import materials as M  # noqa: E402
import studio  # noqa: E402

OUT_DIR = os.path.join(studio.ROOT, "assets", "env")
SHEET = os.path.join(studio.RENDER_DIR, "icons", "deposits", "sheet.png")

PATCH = 2.0                 # half size of the framed 4 x 4 m patch
R_HOLE = 1.4                # mean radius of the opening in the slab
R_OUT = 2.95                # apron mesh radius
FADE = (1.75, 2.4)          # apron alpha 1 -> 0 between these radii (plus ragged noise)
SLAB = 0.18                 # slab thickness
RIM_Z = -0.12               # ground level where it meets the broken slab edge
FLOOR_TEX, FLOOR_PERIOD = "concrete_floor_worn_001", 8.0   # must match env.floor_tile()


# =========================================================================== per-deposit looks
# Colours are LINEAR. soil = ground inside the opening, tint = ore staining, dust = spill on the apron.
LOOKS = {
    "iron_ore": dict(style="ore_field", soil=(0.055, 0.03, 0.021), tint=(0.085, 0.034, 0.02), tint_amt=0.6,
                     dust=(0.075, 0.035, 0.022), host=(0.06, 0.045, 0.038), tint2=(0.1, 0.055, 0.022)),
    "copper_ore": dict(style="ore_field", soil=(0.05, 0.043, 0.035), tint=(0.02, 0.055, 0.035), tint_amt=0.4,
                       dust=(0.045, 0.055, 0.045), host=(0.06, 0.056, 0.05),
                       ore=dict(vein=(0.012, 0.1, 0.045), vein2=(0.012, 0.035, 0.13), vein_amt=0.2, speck=(0.3, 0.2, 0.06))),
    "coal": dict(style="ore_field", soil=(0.03, 0.027, 0.024), tint=(0.01, 0.01, 0.011), tint_amt=0.8,
                 dust=(0.015, 0.015, 0.016), dust_amt=0.9, blocky=True, seam=True, host=(0.06, 0.055, 0.05), glossy=True),
    "limestone": dict(style="ore_field", soil=(0.13, 0.12, 0.095), tint=(0.2, 0.185, 0.145), tint_amt=0.5,
                      dust=(0.15, 0.145, 0.12), blocky=True, seam=True, slabby=True, bedrock=0.6, host=(0.17, 0.16, 0.13),
                      ore_cap=0.3),
    "bauxite": dict(style="ore_field", soil=(0.085, 0.042, 0.024), tint=(0.12, 0.05, 0.024), tint_amt=0.55,
                    dust=(0.1, 0.05, 0.028), nodular=True, host=(0.09, 0.055, 0.035), ore_cap=0.15,
                    ore=dict(base2=(0.09, 0.04, 0.02), speck=(0.22, 0.12, 0.05)), tint2=(0.12, 0.085, 0.05)),
    "rare_earth_ore": dict(style="ore_field", soil=(0.075, 0.062, 0.052), tint=(0.13, 0.085, 0.075), tint_amt=0.45,
                           dust=(0.12, 0.09, 0.08), host=(0.06, 0.057, 0.054), ore_cap=0.17,
                           ore=dict(speck=(0.02, 0.02, 0.022), speck_amt=0.6, speck2=(0.25, 0.2, 0.08))),
    "stone": dict(style="rubble", soil=(0.065, 0.06, 0.054), dust=(0.13, 0.125, 0.115)),
    "cassiterite": dict(style="placer", soil=(0.07, 0.062, 0.05), dust=(0.075, 0.065, 0.052)),
    "quartz_sand": dict(style="sand_bar", sand=(0.26, 0.22, 0.155), dust=(0.16, 0.14, 0.1), dust_amt=0.85),
    "ilmenite": dict(style="sand_bar", sand=(0.022, 0.022, 0.024), streak=(0.16, 0.135, 0.1), sparkle=1.0,
                     dust=(0.025, 0.025, 0.027), dust_amt=0.9),
    "monazite_sand": dict(style="sand_bar", sand=(0.22, 0.165, 0.1), streak=(0.1, 0.045, 0.02), sparkle=0.3,
                          dust=(0.15, 0.1, 0.05), dust_amt=0.85),
    "wolframite": dict(style="lode", soil=(0.045, 0.044, 0.043), dust=(0.1, 0.1, 0.1)),
    "native_sulfur": dict(style="fumarole", soil=(0.065, 0.06, 0.052), crust=(0.5, 0.34, 0.015),
                          dust=(0.15, 0.105, 0.012)),
    "natural_gas": dict(style="gas_vent", soil=(0.07, 0.058, 0.046), crust=(0.3, 0.25, 0.13), dust=(0.13, 0.115, 0.08)),
    "helium_gas": dict(style="gas_vent", soil=(0.065, 0.062, 0.062), crust=(0.33, 0.3, 0.35), dust=(0.14, 0.13, 0.145)),
    "water": dict(style="water_pool", soil=(0.05, 0.045, 0.035)),
    "crude_oil": dict(style="oil_seep", soil=(0.025, 0.021, 0.017)),
    "brine": dict(style="brine_flat", soil=(0.45, 0.45, 0.43)),
}


def style_of(d):
    """Fallback style for deposits without a LOOKS entry."""
    v = d.get("visual") or {}
    if v.get("params", {}).get("style"):
        return v["params"]["style"]
    arch, mat = v.get("archetype"), v.get("material")
    key = f"{d.get('id', '')} {d.get('item', '')} {d.get('name', '')}".lower()
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
    if "sand" in key or arch == "powder_pile":
        return "sand_bar"
    if "placer" in key:
        return "placer"
    if arch == "crystal_cluster" or "lode" in key:
        return "lode"
    if arch == "gravel_pile":
        return "rubble"
    return "ore_field"


def look_for(d):
    v = d.get("visual") or {}
    lk = dict(LOOKS.get(d["id"]) or {})
    lk.setdefault("style", style_of(d))
    base = KI.base_color(v.get("material") or d.get("item"), v.get("color"))
    lk.setdefault("soil", tuple(0.2 * c + 0.03 for c in base))
    lk.setdefault("tint", scaled(base, 0.5))
    lk.setdefault("tint_amt", 0.45)
    lk.setdefault("dust", tuple(c * min(1.0, 0.13 / max(1e-3, max(base))) for c in base))
    lk.setdefault("sand", scaled(base, 0.6))
    lk.setdefault("crust", tuple(0.25 + 0.6 * c for c in KI.lin(v.get("color") or base)))
    lk["mat"] = v.get("material") or d.get("item")
    lk["color"] = v.get("color")
    return lk


# =========================================================================== small helpers
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def seg_dist(x, y, path):
    """Distance from (x, y) to a polyline, and the parameter (0..1) along it of the nearest point."""
    best, bu, acc = 1e9, 0.0, 0.0
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
    total = sum(lens) or 1.0
    for (ax, ay), (bx, by), L in zip(path, path[1:], lens):
        dx, dy = bx - ax, by - ay
        u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (L * L or 1.0)))
        dd = math.hypot(x - ax - dx * u, y - ay - dy * u)
        if dd < best:
            best, bu = dd, (acc + u * L) / total
        acc += L
    return best, bu


def attr(t, name):
    return t.node("ShaderNodeAttribute", attribute_name=name).outputs["Fac"]


def vmath(t, op, a, b=None):
    n = t.node("ShaderNodeVectorMath", operation=op)
    t.link(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (tuple, list)):
            n.inputs[1].default_value = tuple(b)
        else:
            t.link(b, n.inputs[1])
    return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Value"]


def combine(t, x, y, z):
    n = t.node("ShaderNodeCombineXYZ")
    for i, v in enumerate((x, y, z)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            t.link(v, n.inputs[i])
    return n.outputs[0]


def scaled(c, k):
    return tuple(min(1.0, x * k) for x in c)


# =========================================================================== the opening
class Hole:
    """Ragged outline of the broken slab: r(angle) = jagged polygon x ellipse x wobble."""

    def __init__(self, seed, R=R_HOLE, jag=0.2, k=12, stretch=None, rot=None):
        rnd = random.Random(seed)
        if stretch is None:
            e = rnd.uniform(1.0, 1.22)
            stretch = (e, 1.0 / math.sqrt(e))
        rot = rnd.uniform(0, math.pi) if rot is None else rot
        self.R, self.sx, self.sy, self.rot = R, stretch[0], stretch[1], rot
        self.ctrl = sorted(((i + rnd.uniform(-0.38, 0.38)) / k * math.tau % math.tau, rnd.uniform(1 - jag, 1 + jag * 0.55))
                           for i in range(k))
        self._a = [c[0] for c in self.ctrl]
        self._f = [c[1] for c in self.ctrl]
        self.off = Vector((seed % 113 * 0.37, seed % 71 * 0.53, seed % 37 * 0.11))
        self.rmax = max(self.r(math.tau * i / 360) for i in range(360))

    def r(self, a):
        a %= math.tau
        A, F = self._a, self._f
        i = bisect.bisect_right(A, a)
        if i == 0:
            a0, f0, a1, f1 = A[-1] - math.tau, F[-1], A[0], F[0]
        elif i == len(A):
            a0, f0, a1, f1 = A[-1], F[-1], A[0] + math.tau, F[0]
        else:
            a0, f0, a1, f1 = A[i - 1], F[i - 1], A[i], F[i]
        f = f0 + (f1 - f0) * (a - a0) / (a1 - a0)
        ca, sa = math.cos(a - self.rot), math.sin(a - self.rot)
        ell = 1.0 / math.sqrt((ca / self.sx) ** 2 + (sa / self.sy) ** 2)
        p = Vector((math.cos(a), math.sin(a), 0.0))
        wob = 0.045 * noise.fractal(p * 1.3 + self.off, 0.6, 2.0, 3)
        fine = 0.012 * noise.noise(p * 16.0 + self.off)
        return self.R * f * ell + self.R * wob + fine

    def depth(self, x, y):
        """>0 inside the opening: distance (m, radial) from the slab edge."""
        return self.r(math.atan2(y, x)) - math.hypot(x, y)


class Ctx:
    def __init__(self, d, look):
        self.d, self.look = d, look
        self.seed = KI.seed_of(d["id"])
        self.rnd = random.Random(self.seed)
        self.hole = Hole(self.seed, **look.get("hole", {}))
        self.pts = [(x * PATCH, y * PATCH, 0.0) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        self.emitters = []
        self.level = None          # liquid level, if any
        self.hf = lambda x, y: RIM_Z
        self.off = Vector((self.seed % 97 * 0.31, self.seed % 89 * 0.27, 0.0))

    def inner(self, x, y, w=0.35):
        return smoothstep(0.0, w, self.hole.depth(x, y))

    def undulate(self, x, y, amp=0.03, freq=0.9):
        return amp * noise.fractal(Vector((x * freq, y * freq, 0)) + self.off, 0.6, 2.0, 4)

    def sample(self, margin=0.1, bias=0.0, rnd=None):
        """Random point inside the opening at least `margin` from the edge (bias>0 favours the centre)."""
        rnd = rnd or self.rnd
        rm = self.hole.rmax
        for _ in range(200):
            x, y = rnd.uniform(-rm, rm), rnd.uniform(-rm, rm)
            dp = self.hole.depth(x, y)
            if dp < margin:
                continue
            if bias and rnd.random() > (1 - bias) + bias * min(1.0, dp / (0.7 * self.hole.R)):
                continue
            return x, y
        return 0.0, 0.0


# =========================================================================== materials
def apron_mat(look):
    """Floor concrete identical to floor_tile.png + spill / stain / cracks / spalled rim, radial alpha fade."""
    m, t = M._new("apron")
    p = t.bsdf()
    vec = t.coords(1.0 / FLOOR_PERIOD)
    col = t.image(FLOOR_TEX, "color", vec).outputs["Color"]
    rough = t.image(FLOOR_TEX, "rough", vec, noncolor=True).outputs["Color"]
    disp = t.image(FLOOR_TEX, "disp", vec, noncolor=True).outputs["Color"]
    p.inputs["Metallic"].default_value = 0.0
    obj = t.coords(1.0)
    d = attr(t, "d")
    n1 = t.noise(obj, 1.1, 6, 0.6)
    n2 = t.noise(obj, 4.5, 6, 0.6)
    n3 = t.noise(obj, 22.0, 3, 0.5)

    # radial cracks: voronoi edges in (direction, distance-from-edge) space -> cells long in the radial direction
    sep = KI._sep(t, obj)
    nrm = vmath(t, "NORMALIZE", combine(t, sep.outputs["X"], sep.outputs["Y"], 0.0))
    sn = KI._sep(t, nrm)
    cv = combine(t, t.math("MULTIPLY", sn.outputs["X"], 5.5), t.math("MULTIPLY", sn.outputs["Y"], 5.5),
                 t.math("MULTIPLY", d, 0.35))
    wig = t.node("ShaderNodeTexNoise")
    t.link(obj, wig.inputs["Vector"])
    wig.inputs["Scale"].default_value = 3.0
    wig.inputs["Detail"].default_value = 4.0
    cv = vmath(t, "ADD", cv, vmath(t, "MULTIPLY", vmath(t, "SUBTRACT", wig.outputs["Color"], (0.5, 0.5, 0.5)),
                                    (0.5, 0.5, 0.0)))
    edge = KI._voronoi(t, cv, 1.0, feature="DISTANCE_TO_EDGE")
    reach = look.get("cracks", 0.75)
    crack = t.math("MULTIPLY", t.maprange(edge, 0.022, 0.003),
                   t.math("MULTIPLY", t.maprange(t.math("ADD", d, t.math("MULTIPLY", n1, 0.6)), reach + 0.3, 0.25),
                          t.maprange(t.noise(cv, 0.9, 3, 0.5), 0.42, 0.52)))
    col = t.mix_color(t.math("MULTIPLY", crack, 0.85), col, (0.025, 0.024, 0.022))

    # spalled rim: top surface broken away, exposing aggregate
    sp = t.maprange(t.math("ADD", d, t.math("MULTIPLY", t.math("SUBTRACT", n2, 0.5), 0.08)), 0.035, 0.012)
    agg = t.mix_color(t.maprange(n3, 0.35, 0.65), (0.2, 0.19, 0.175), (0.08, 0.075, 0.07))
    col = t.mix_color(sp, col, agg)
    rough = t.mix_float(sp, rough, 0.92)

    # resource spill (dust / stain / salt bloom / wet halo) concentrated at the opening
    kind = look.get("spill", "dust")
    spread = look.get("spread", 0.55)
    amt = look.get("dust_amt", 0.75)
    fan = t.maprange(t.noise(obj, 0.7, 3, 0.5), 0.3, 0.7, 0.35, 1.5)          # spill reaches further in places
    dd = t.math("DIVIDE", d, fan)
    sf = t.maprange(t.math("ADD", dd, t.math("ADD", t.math("MULTIPLY", t.math("SUBTRACT", n1, 0.5), spread * 1.1),
                                             t.math("MULTIPLY", t.math("SUBTRACT", n2, 0.5), 0.16))),
                    spread, 0.0, 0.0, amt, interp="SMOOTHSTEP")
    dc = look.get("dust", (0.2, 0.2, 0.2))
    if kind == "wet":      # damp concrete: darker, glossier
        col = t.mix_color(sf, col, t.mix_color(1.0, col, (0.45, 0.45, 0.46), blend="MULTIPLY"))
        rough = t.mix_float(sf, rough, 0.18)
    elif kind == "oil":    # black glossy stain with a brown halo
        halo = t.maprange(t.math("ADD", dd, t.math("MULTIPLY", t.math("SUBTRACT", n1, 0.5), spread * 1.1)),
                          spread * 1.5, spread * 0.6, 0.0, 0.5)
        col = t.mix_color(halo, col, t.mix_color(1.0, col, (0.45, 0.38, 0.3), blend="MULTIPLY"))
        blot = t.math("MULTIPLY", sf, t.maprange(t.noise(obj, 3.0, 4, 0.6), 0.36, 0.52, 0.45, 1.0))
        col = t.mix_color(blot, col, (0.012, 0.01, 0.009))
        rough = t.mix_float(blot, rough, 0.08)
    else:                  # dust / crust: fine grains + patchy coverage
        grains = t.maprange(n3, 0.4, 0.65, 0.0, 1.0)
        blot = t.maprange(t.noise(obj, 2.6, 5, 0.6), 0.36, 0.58, 0.25, 1.0)
        cov = t.math("MULTIPLY", t.math("MULTIPLY", sf, blot), t.maprange(grains, 0.0, 1.0, 0.6, 1.0))
        dcol = t.mix_color(t.maprange(n2, 0.3, 0.7), dc, scaled(dc, 0.6))
        col = t.mix_color(cov, col, dcol)
        rough = t.mix_float(cov, rough, look.get("dust_rough", 0.95))
        specks = t.math("MULTIPLY", t.maprange(t.noise(obj, 90.0, 1, 0.5), 0.66, 0.7),
                        t.maprange(t.math("ADD", dd, t.math("MULTIPLY", n1, 0.4)), spread * 1.8, spread * 0.4))
        col = t.mix_color(t.math("MULTIPLY", specks, 0.8), col, scaled(dc, 0.8))
    KI._set(p, "Base Color", col)
    KI._set(p, "Roughness", rough)

    h = t.math("SUBTRACT", t.math("ADD", disp, t.math("MULTIPLY", sp, t.math("MULTIPLY", n3, 0.6))),
               t.math("MULTIPLY", crack, 0.7))
    t.link(t.bump(h, 0.4, 0.01), p.inputs["Normal"])

    # alpha: ragged radial fade; shadow rays see the apron only where it is fully opaque
    r = vmath(t, "LENGTH", combine(t, sep.outputs["X"], sep.outputs["Y"], 0.0))
    nf = t.noise(obj, 0.55, 4, 0.55)
    rr = t.math("ADD", r, t.math("ADD", t.math("MULTIPLY", t.math("SUBTRACT", nf, 0.5), 1.1),
                                 t.math("MULTIPLY", t.math("SUBTRACT", n2, 0.5), 0.16)))
    a = t.maprange(rr, FADE[1], FADE[0], interp="SMOOTHSTEP")
    a = t.math("MAXIMUM", a, t.maprange(d, 0.6, 0.38, interp="SMOOTHSTEP"))
    lp = t.node("ShaderNodeLightPath")
    a = t.mix_float(lp.outputs["Is Shadow Ray"], a, t.math("GREATER_THAN", a, 0.97))
    KI._set(p, "Alpha", a)
    return m


def broken_concrete():
    return KI.rock(base=(0.115, 0.11, 0.1), base2=(0.07, 0.066, 0.06), speck=(0.03, 0.028, 0.025), speck_amt=0.8,
                   speck2=(0.2, 0.19, 0.17), rough=0.92, scale=3.0, name="broken_concrete")


def ground_mat(soil, tint=None, tint_amt=0.0, gravel=0.5, damp=0.2, crust=None, vein=None, bedrock=0.0, gloss=0.0,
               wet_col=None, tint2=None, deep=None, name="ground"):
    """Dirt / bedrock for the opening. Vertex attributes (0..1) drive overlays: stain (ore tint), crust (mineral
    crust), vein (quartz), wet (dark & glossy)."""
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    n1 = t.noise(vec, 0.8, 6, 0.6)
    n2 = t.noise(vec, 3.5, 8, 0.65)
    n3 = t.noise(vec, 14.0, 4, 0.6)
    n0 = t.noise(vec, 0.35, 3, 0.5)
    clod = KI._voronoi(t, vec, 7.0, feature="SMOOTH_F1")
    col = t.mix_color(t.maprange(n1, 0.3, 0.7), soil, scaled(soil, 0.55))
    col = t.mix_color(t.maprange(n0, 0.35, 0.65, 0.0, 0.6), col, scaled(soil, 0.6))
    col = t.mix_color(t.maprange(n3, 0.3, 0.7, 0.0, 0.5), col, scaled(soil, 1.45))
    col = t.mix_color(t.maprange(clod, 0.25, 0.55, 0.0, 0.35), col, scaled(soil, 0.5))
    rough = 0.94
    if tint:
        tm = t.math("ADD", t.maprange(t.noise(vec, 1.3, 6, 0.6, 0.6), 0.38, 0.62, 0.0, tint_amt),
                    t.math("MULTIPLY", attr(t, "stain"), t.maprange(n2, 0.25, 0.6, 0.55, 1.0)))
        col = t.mix_color(t.math("MINIMUM", tm, 1.0), col, t.mix_color(t.maprange(n3, 0.3, 0.7), tint, scaled(tint, 0.6)))
    if tint2:
        col = t.mix_color(t.maprange(t.noise(vec, 2.2, 6, 0.6, 0.8), 0.6, 0.7, 0.0, 0.7), col, tint2)
    if bedrock:
        dist = t.node("ShaderNodeTexNoise")
        t.link(vec, dist.inputs["Vector"])
        dist.inputs["Scale"].default_value = 1.6
        wv = vmath(t, "ADD", vec, vmath(t, "MULTIPLY", dist.outputs["Color"], (0.45, 0.45, 0.45)))
        fr = KI._voronoi(t, wv, 1.5, feature="DISTANCE_TO_EDGE")
        keep = t.maprange(t.noise(wv, 1.2, 3, 0.5), 0.42, 0.55)        # joints die out in places
        frac = t.math("MULTIPLY", t.math("MULTIPLY", t.maprange(fr, 0.02, 0.004), keep), bedrock)
        col = t.mix_color(t.math("MULTIPLY", frac, 0.8), col, scaled(soil, 0.25))
    else:
        frac = 0.0
    peb = KI._voronoi(t, vec, 34.0)
    pm = t.maprange(peb, 0.13, 0.05, 0.0, gravel)
    pcol = t.mix_color(t.maprange(t.noise(vec, 40.0, 2), 0.3, 0.7), scaled(soil, 1.9), scaled(soil, 0.7))
    col = t.mix_color(pm, col, pcol)
    dm = t.maprange(n2, 0.55, 0.75, 0.0, damp)
    col = t.mix_color(dm, col, scaled(soil, 0.5))
    rough = t.mix_float(dm, rough, 0.6)
    if crust:
        cm = t.maprange(t.math("ADD", attr(t, "crust"), t.math("MULTIPLY", t.math("SUBTRACT", n2, 0.5), 0.7)), 0.35, 0.6)
        ccol = t.mix_color(t.maprange(n3, 0.3, 0.75), crust, scaled(crust, 0.65))
        ccol = t.mix_color(t.maprange(t.noise(vec, 60.0, 2), 0.62, 0.68), ccol, scaled(crust, 1.3))
        col = t.mix_color(cm, col, ccol)
        rough = t.mix_float(cm, rough, 0.8)
    else:
        cm = 0.0
    if vein:
        vm = t.maprange(t.math("ADD", attr(t, "vein"), t.math("MULTIPLY", t.math("SUBTRACT", n3, 0.5), 0.5)), 0.4, 0.55)
        vcol = t.mix_color(t.maprange(n2, 0.3, 0.7), vein, scaled(vein, 0.7))
        col = t.mix_color(vm, col, vcol)
        rough = t.mix_float(vm, rough, 0.4)
    wet = t.maprange(t.math("ADD", attr(t, "wet"), t.math("MULTIPLY", t.math("SUBTRACT", n2, 0.5), 0.3)), 0.3, 0.6)
    col = t.mix_color(wet, col, t.mix_color(1.0, col, wet_col or (0.5, 0.5, 0.5), blend="MULTIPLY"))
    rough = t.mix_float(wet, rough, 0.22)
    if gloss:
        rough = t.mix_float(gloss, rough, 0.12)
    if deep:   # water column absorption: attribute uw = 1 - exp(-depth * k)
        col = t.mix_color(attr(t, "uw"), col, deep)
    col = t.mix_color(t.math("MULTIPLY", attr(t, "pit"), 0.85), col, scaled(soil, 0.12))
    KI._set(p, "Base Color", col)
    KI._set(p, "Roughness", rough)
    h = t.math("ADD", t.math("MULTIPLY", pm, 0.6), t.math("MULTIPLY", t.noise(vec, 30.0, 6), 0.4))
    h = t.math("SUBTRACT", h, t.math("MULTIPLY", clod, 0.8))
    if bedrock:
        h = t.math("SUBTRACT", h, t.math("MULTIPLY", frac, 1.2))
    if crust:
        h = t.math("ADD", h, t.math("MULTIPLY", cm, t.noise(vec, 45.0, 4, 0.7)))
    t.link(t.bump(h, 0.8, 0.01), p.inputs["Normal"])
    return m


def sand_mat(color, streak=None, sparkle=0.0, name="sand"):
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    warp = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    t.link(KI._stretch(t, vec, (1.0, 0.35, 1.0)), warp.inputs["Vector"])
    warp.inputs["Scale"].default_value = 11.0
    warp.inputs["Distortion"].default_value = 7.0
    warp.inputs["Detail"].default_value = 3.0
    ripple = warp.outputs["Factor"]
    n = t.noise(vec, 1.0, 6, 0.6)
    col = t.mix_color(t.maprange(n, 0.3, 0.7), color, scaled(color, 0.72))
    col = t.mix_color(t.maprange(ripple, 0.6, 1.0, 0.0, 0.25), col, scaled(color, 0.7))
    if streak:
        sm = t.math("ADD", attr(t, "stain"), t.math("MULTIPLY", t.math("SUBTRACT", t.noise(vec, 3.0, 6, 0.6), 0.5), 0.6))
        sm = t.math("MAXIMUM", t.maprange(sm, 0.35, 0.6), t.math("MULTIPLY", t.maprange(ripple, 0.75, 0.95), 0.5))
        col = t.mix_color(sm, col, t.mix_color(t.maprange(t.noise(vec, 40, 2), 0.3, 0.7), streak, scaled(streak, 0.6)))
    g = KI._voronoi(t, vec, 140.0)
    col = t.mix_color(t.maprange(g, 0.0, 0.5, 0.3, 0.0), col, scaled(color, 0.5))
    wet = t.maprange(attr(t, "wet"), 0.3, 0.7)
    col = t.mix_color(wet, col, t.mix_color(1.0, col, (0.55, 0.55, 0.55), blend="MULTIPLY"))
    KI._set(p, "Base Color", col)
    if sparkle:
        sp = t.maprange(t.noise(vec, 300.0, 1, 0.5), 0.7 - 0.08 * sparkle, 0.73 - 0.08 * sparkle)
        KI._set(p, "Metallic", t.math("MULTIPLY", sp, 0.9))
        KI._set(p, "Roughness", t.mix_float(sp, t.mix_float(wet, 0.9, 0.35), 0.25))
    else:
        KI._set(p, "Roughness", t.mix_float(wet, 0.9, 0.35))
    t.link(t.bump(t.math("ADD", ripple, t.math("MULTIPLY", g, 0.4)), 0.3, 0.01), p.inputs["Normal"])
    return m


def salt_mat(name="salt_crust"):
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    cells = KI._voronoi(t, vec, 2.6, feature="DISTANCE_TO_EDGE")
    ridge = t.maprange(cells, 0.06, 0.0)
    n = t.noise(vec, 5.0, 6, 0.6)
    col = t.mix_color(t.maprange(n, 0.3, 0.7), (0.3, 0.29, 0.275), (0.2, 0.19, 0.175))
    col = t.mix_color(ridge, col, (0.46, 0.45, 0.43))
    col = t.mix_color(t.maprange(t.noise(vec, 0.9, 4), 0.6, 0.75, 0.0, 0.55), col, (0.16, 0.13, 0.1))
    wet = t.maprange(t.math("ADD", attr(t, "wet"), t.math("MULTIPLY", t.math("SUBTRACT", n, 0.5), 0.4)), 0.35, 0.6)
    col = t.mix_color(wet, col, (0.3, 0.33, 0.32))
    col = t.mix_color(t.math("MULTIPLY", attr(t, "uw"), 0.85), col, (0.05, 0.12, 0.12))
    KI._set(p, "Base Color", col)
    KI._set(p, "Roughness", t.mix_float(wet, 0.75, 0.2))
    p.inputs["Subsurface Weight"].default_value = 0.15
    p.inputs["Subsurface Radius"].default_value = (0.6, 0.6, 0.55)
    p.inputs["Subsurface Scale"].default_value = 0.01
    h = t.math("ADD", t.math("MULTIPLY", ridge, 1.0), t.math("MULTIPLY", t.noise(vec, 50, 4), 0.35))
    t.link(t.bump(h, 0.7, 0.012), p.inputs["Normal"])
    return m


def water_mat(tint=(0.6, 0.8, 0.85), rough=0.02, name="water"):
    """Clear water surface: refraction + reflection; shadow & diffuse rays pass straight through so the pool floor
    stays lit. The depth colour is painted into the ground via its "uw" attribute (see ground_mat)."""
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(1.0)
    p.inputs["Base Color"].default_value = M._rgba(tint)
    p.inputs["Transmission Weight"].default_value = 1.0
    p.inputs["IOR"].default_value = 1.333
    p.inputs["Roughness"].default_value = rough
    rip = t.noise(KI._stretch(t, vec, (1.0, 2.2, 1.0)), 2.6, 4, 0.55)
    t.link(t.bump(rip, 0.12, 0.01), p.inputs["Normal"])
    tr = t.node("ShaderNodeBsdfTransparent")
    lp = t.node("ShaderNodeLightPath")
    mix = t.node("ShaderNodeMixShader")
    t.link(t.math("MAXIMUM", lp.outputs["Is Shadow Ray"], lp.outputs["Is Diffuse Ray"]), mix.inputs[0])
    t.link(p.outputs[0], mix.inputs[1])
    t.link(tr.outputs[0], mix.inputs[2])
    out = t.nodes.get("Material Output")
    t.link(mix.outputs[0], out.inputs["Surface"])
    return m


def oil_mat():
    m, t = M._new("crude")
    p = t.bsdf()
    vec = t.coords(1.0)
    p.inputs["Base Color"].default_value = (0.006, 0.005, 0.004, 1)
    p.inputs["Roughness"].default_value = 0.07
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.02
    KI._set(p, "Thin Film Thickness", t.maprange(t.noise(vec, 1.6, 4, 0.6, 1.5), 0.35, 0.75, 0.0, 600.0))
    p.inputs["Thin Film IOR"].default_value = 1.45
    swell = t.math("ADD", t.noise(vec, 2.2, 2, 0.4), t.math("MULTIPLY", t.noise(vec, 9.0, 2, 0.5), 0.15))
    t.link(t.bump(swell, 1.0, 0.05), p.inputs["Normal"])
    return m


# =========================================================================== geometry
def build_apron(ctx, look, segs=288, rings=30):
    """Slab top (apron) + broken inner wall, one mesh. Vertex attribute d = distance from the break (m)."""
    hole, off = ctx.hole, ctx.off
    bm = bmesh.new()
    dl = bm.verts.layers.float.new("d")
    rows = [[] for _ in range(3 + rings)]
    for j in range(segs):
        a = math.tau * j / segs
        ca, sa = math.cos(a), math.sin(a)
        rh = hole.r(a)
        pv = Vector((ca, sa, 0.0))
        chip = -(0.006 + 0.032 * max(0.0, noise.fractal(pv * 5.0 + off, 0.6, 2.0, 3) + 0.15))
        sag = -0.012 * max(0.0, noise.fractal(pv * 1.4 + off * 1.3, 0.6, 2.0, 2) + 0.1)
        # broken face: bottom (buried), middle (rough, set back a little), rim
        jit = lambda k, s: s * noise.noise(pv * k + off + Vector((0, 0, s * 37)))  # noqa: E731
        wall = [(rh + 0.02 + jit(9.0, 0.03), RIM_Z - 0.06, 0.0),
                (rh + 0.012 + jit(13.0, 0.028), -0.045 + jit(7.0, 0.015), 0.0),
                (rh + jit(17.0, 0.01), chip + sag, 0.0)]
        for i, (r, z, d) in enumerate(wall):
            v = bm.verts.new((r * ca, r * sa, z))
            v[dl] = d
            rows[i].append(v)
        span = R_OUT - rh
        for i in range(1, rings + 1):
            d = span * (i / rings) ** 1.55
            r = rh + d
            z = chip * math.exp(-d / 0.035) + sag * math.exp(-d / 0.3)
            v = bm.verts.new((r * ca, r * sa, z))
            v[dl] = d
            rows[2 + i].append(v)
    for ri, (A, B) in enumerate(zip(rows, rows[1:])):
        for j in range(segs):
            k = (j + 1) % segs
            f = bm.faces.new((A[j], B[j], B[k], A[k]))
            f.material_index = 1 if ri < 2 else 0
            f.smooth = ri >= 2
    me = bpy.data.meshes.new("apron")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("apron", me)
    K.collection().objects.link(o)
    me.materials.append(apron_mat(look))
    me.materials.append(broken_concrete())
    return o


def terrain(ctx, hf, mat, attrs=None, rings=90, segs=300, name="ground"):
    """Polar-grid ground under the opening; follows the outline and tucks 0.18 m under the slab edge."""
    hole = ctx.hole
    attrs = attrs or {}
    bm = bmesh.new()
    layers = {k: bm.verts.layers.float.new(k) for k in attrs}

    def mk(x, y):
        v = bm.verts.new((x, y, hf(x, y)))
        for k, fn in attrs.items():
            v[layers[k]] = max(0.0, min(1.0, fn(x, y)))
        return v
    centre = mk(0.0, 0.0)
    edge = [hole.r(math.tau * j / segs) + 0.18 for j in range(segs)]
    grid = []
    for i in range(1, rings + 1):
        u = i / rings
        grid.append([mk(edge[j] * u * math.cos(math.tau * j / segs), edge[j] * u * math.sin(math.tau * j / segs))
                     for j in range(segs)])
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
    ctx.hf = hf
    return o


def liquid_surface(ctx, level, mat, segs=192):
    """Liquid surface following the outline, tucked 0.1 m under the slab edge (depth colour lives in the ground)."""
    bm = bmesh.new()
    vs = []
    for j in range(segs):
        a = math.tau * j / segs
        r = ctx.hole.r(a) + 0.1
        vs.append(bm.verts.new((r * math.cos(a), r * math.sin(a), level)))
    bm.faces.new(vs)
    me = bpy.data.meshes.new("liquid")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("liquid", me)
    K.collection().objects.link(o)
    me.materials.append(mat)
    return o


def _settle(o, x, y, zg, sink, rot, scale=1.0):
    """Rotate, then drop so the lowest vertex sits `sink` x height below ground height zg. Returns top z."""
    o.rotation_euler = Euler(rot, "XYZ")
    Rm = o.rotation_euler.to_matrix()
    zs = [(Rm @ v.co).z * scale for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    o.location = (x, y, zg - lo - (hi - lo) * sink)
    return o.location.z + hi


def rock_at(ctx, x, y, r, mat, sink=0.4, squash=(1.0, 0.9, 0.65), cuts=8, subdiv=4, bump=0.15, tilt=0.4, seed=0,
            detail=0.09):
    rnd = ctx.rnd
    o = KI.rock_mesh(r, ctx.seed + seed, cuts=cuts, subdiv=subdiv, bump=bump, squash=squash, mat=mat, detail=detail)
    top = _settle(o, x, y, ctx.hf(x, y), sink, (rnd.uniform(-tilt, tilt), rnd.uniform(-tilt, tilt), rnd.uniform(0, 6.3)))
    ctx.pts.append((x, y, top))
    return o


def scatter(ctx, mats, n, size, sink=0.3, squash=(1.0, 0.9, 0.7), cuts=6, subdiv=2, bump=0.2, margin=0.05, bias=0.3,
            where=None, protos_per_mat=3, seed=0, dry=False):
    """Instanced small stones (linked duplicates). where(rnd) -> (x, y) overrides uniform sampling."""
    rnd = random.Random(ctx.seed + 991 + seed)
    protos = []
    for i, mt in enumerate(mats):
        for k in range(protos_per_mat):
            pr = KI.rock_mesh(1.0, ctx.seed + 300 + seed + i * 17 + k, cuts=cuts, subdiv=subdiv, bump=bump, squash=squash,
                              mat=mt, detail=0.05)
            pr.location = (0, 0, -30)
            pr.hide_render = True
            protos.append(pr)
    lo, hi = size
    for k in range(n):
        x, y = where(rnd) if where else ctx.sample(margin, bias, rnd)
        if ctx.hole.depth(x, y) < margin:
            continue
        if dry and ctx.level is not None and ctx.hf(x, y) < ctx.level + 0.005:
            continue
        s = lo * (hi / lo) ** (rnd.random() ** 1.7)
        pr = protos[rnd.randrange(len(protos))]
        o = KI.dup(pr, scale=s)
        o.hide_render = False
        _settle(o, x, y, ctx.hf(x, y), sink, (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)), s)


def slab_chunk(rnd, size, thick):
    """Broken piece of floor slab: irregular polygon prism, floor concrete on top, broken concrete on the sides."""
    k = rnd.randint(5, 7)
    angs = sorted(rnd.uniform(0, math.tau) for _ in range(k))
    pts = [(size * rnd.uniform(0.55, 1.0) * math.cos(a), size * rnd.uniform(0.55, 1.0) * math.sin(a)) for a in angs]
    o = KI.poly_extrude(pts, -thick, 0.0, floor_concrete(), name="slab_chunk", bevel=0.004)
    o.data.materials.append(broken_concrete())
    for poly in o.data.polygons:
        if abs(poly.normal.z) < 0.5:
            poly.material_index = 1
    return o


def floor_concrete():
    return M.scanned(FLOOR_TEX, scale=1.0 / FLOOR_PERIOD, metallic=0.0, bump=0.4, ao=False, name="floor_chunk")


def fragments(ctx, n, sink=0.35):
    """Pieces of the broken slab: some still hinged at the rim and tipped into the opening, some fallen in."""
    rnd = random.Random(ctx.seed + 77)
    used = []
    for k in range(n):
        for _ in range(30):
            a = rnd.uniform(0, math.tau)
            if all(abs((a - b + math.pi) % math.tau - math.pi) > 0.6 for b in used):
                break
        used.append(a)
        rh = ctx.hole.r(a)
        hinged = k < n // 2
        size = rnd.uniform(0.12, 0.22) if hinged else rnd.uniform(0.07, 0.15)
        o = slab_chunk(rnd, size, rnd.uniform(0.07, 0.11))
        dd = rh - size * (0.75 if hinged else rnd.uniform(1.2, 2.5))
        x, y = dd * math.cos(a), dd * math.sin(a)
        tip = rnd.uniform(0.12, 0.3) if hinged else rnd.uniform(-0.4, 0.4)
        # tip the piece down toward the centre of the opening (rotate about the tangent)
        tang = Vector((-math.sin(a), math.cos(a), 0.0))
        rot = (Matrix.Rotation(-tip, 3, tang) @ Matrix.Rotation(rnd.uniform(0, 6.3), 3, "Z")).to_euler("XYZ")
        if hinged:
            o.rotation_euler = rot
            Rm = rot.to_matrix()
            hi = max((Rm @ v.co).z for v in o.data.vertices)
            o.location = (x, y, -0.012 - rnd.uniform(0.0, 0.03) - hi)
            ctx.pts.append((x, y, 0.0))
        else:
            top = _settle(o, x, y, ctx.hf(x, y), sink, tuple(rot))
            ctx.pts.append((x, y, top))
    # concrete grit along the edge
    scatter(ctx, [broken_concrete()], n * 14, (0.012, 0.04), sink=0.3, squash=(1, 0.8, 0.5), margin=0.0,
            where=lambda rr: _edge_point(ctx, rr, 0.0, 0.35), protos_per_mat=4, seed=5, dry=True)


def _edge_point(ctx, rnd, d0, d1):
    a = rnd.uniform(0, math.tau)
    dd = ctx.hole.r(a) - rnd.uniform(d0, d1) * rnd.random()
    return dd * math.cos(a), dd * math.sin(a)


def rebar(ctx, n):
    """Rusty reinforcing bar stubs sticking out of the broken slab face."""
    mat = KI.rock(base=(0.045, 0.022, 0.012), base2=(0.02, 0.012, 0.008), speck=(0.09, 0.04, 0.015), speck_amt=0.6,
                  rough=0.75, scale=25.0, name="rebar_rust")
    rnd = random.Random(ctx.seed + 31)
    for k in range(n):
        a = rnd.uniform(0, math.tau)
        rh = ctx.hole.r(a)
        L = rnd.uniform(0.1, 0.26)
        b = a + math.pi + rnd.uniform(-0.45, 0.45)       # pointing into the opening
        z0 = -0.07 + rnd.uniform(-0.015, 0.015)
        x0, y0 = (rh + 0.06) * math.cos(a), (rh + 0.06) * math.sin(a)
        droop = rnd.uniform(0.15, 0.6)
        pts = []
        for i in range(9):
            u = i / 8 * (L + 0.06)
            pts.append((x0 + u * math.cos(b), y0 + u * math.sin(b), z0 - droop * max(0.0, u - 0.08) ** 2 * 1.6))
        KI.curve_tube(pts, 0.011, mat, name="rebar", res=2)


# =========================================================================== styles
def ore_mat(lk, k=0.75):
    """Deposit chunk material: the icon ore look (kit_icons.ORES), darker (capped albedo so chunks sit in the same
    light as the floor concrete), fewer metal glints, plus per-deposit overrides (look["ore"])."""
    look = dict(KI.ORES.get(lk["mat"]) or {})
    if not look:
        return KI.surf(lk["mat"], lk["color"], scale=2.5)
    if lk["color"]:
        c = KI.lin(lk["color"])
        if "vein" in look:
            look["vein"] = c
        else:
            look["base"], look["base2"] = c, scaled(c, 0.5)
    look.update(lk.get("ore", {}))
    k = min(k, lk.get("ore_cap", 0.18) / max(1e-3, max(look["base"])))
    look["base"] = scaled(look["base"], k)
    look["base2"] = scaled(look.get("base2") or scaled(look["base"], 0.5), k)
    look["speck_amt"] = look.get("speck_amt", 0.0) * 0.6
    look["speck_metal"] = look.get("speck_metal", 0.0) * 0.5
    look["vein_metal"] = look.get("vein_metal", 0.0) * 0.5
    look["rough"] = max(look.get("rough", 0.75), 0.75) if not look.get("glossy") else look.get("rough", 0.4)
    return KI.rock(scale=2.5, name=f"dep_{lk['mat']}", **look)


def s_ore_field(ctx, lk):
    rnd, hole = ctx.rnd, ctx.hole
    ore = ore_mat(lk)
    hb = lk.get("host", (0.1, 0.09, 0.08))
    host = KI.rock(base=hb, base2=scaled(hb, 0.5), speck=scaled(hb, 2.0), speck_amt=0.5, rough=0.85, scale=3.0,
                   name="host_rock")
    blocky, nodular = lk.get("blocky"), lk.get("nodular")
    cuts, bump = (12, 0.05) if blocky else ((3, 0.32) if nodular else (8, 0.14))
    squash = (1.0, 0.85, 0.42) if lk.get("slabby") else ((1.0, 0.9, 0.6) if blocky else (1.0, 0.9, 0.7))
    # seam: a band of ore across the opening (coal bed, limestone bedding)
    sa = rnd.uniform(0, math.pi)
    sdx, sdy = math.cos(sa), math.sin(sa)
    soff = rnd.uniform(-0.25, 0.25)

    def seam(x, y):
        if not lk.get("seam"):
            return 0.0
        return 1.0 - smoothstep(0.35, 0.65, abs(-x * sdy + y * sdx - soff))
    clusters = [ctx.sample(0.45, 0.6) for _ in range(3)]
    big = []
    for k in range(lk.get("n_big", 11)):
        for _ in range(40):
            if lk.get("seam") and k % 3:
                u = rnd.uniform(-1.2, 1.2)
                x, y = u * sdx - (soff + rnd.gauss(0, 0.2)) * sdy, u * sdy + (soff + rnd.gauss(0, 0.2)) * sdx
            else:
                cx, cy = clusters[k % 3]
                x, y = cx + rnd.gauss(0, 0.3), cy + rnd.gauss(0, 0.3)
            r = rnd.uniform(0.08, 0.2) * (1.25 if k < 3 else 1.0)
            if hole.depth(x, y) > r + 0.08 and all(math.hypot(x - bx, y - by) > (r + br) * 0.85 for bx, by, br in big):
                big.append((x, y, r))
                break

    def hf(x, y):
        z = ctx.undulate(x, y, 0.035) + 0.05 * math.exp(-(x * x + y * y) / 0.8)
        for bx, by, br in big:
            q = math.hypot(x - bx, y - by) / (br * 1.5)
            if q < 1.6:
                z += 0.32 * br * math.exp(-q * q * 1.6)
        return RIM_Z + ctx.inner(x, y, 0.4) * z

    def stain(x, y):
        s = max(math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / 0.35) for cx, cy in clusters)
        return max(s, seam(x, y))
    gm = ground_mat(lk["soil"], lk["tint"], lk["tint_amt"], gravel=0.55, damp=0.25, bedrock=lk.get("bedrock", 0.0),
                    gloss=0.3 if lk.get("glossy") else 0.0, tint2=lk.get("tint2"))
    terrain(ctx, hf, gm, {"stain": stain})
    for k, (x, y, r) in enumerate(big):
        rock_at(ctx, x, y, r, ore if k % 4 else (host if not lk.get("seam") else ore), sink=0.42, squash=squash, cuts=cuts,
                bump=bump, subdiv=3, seed=k * 13)

    def near(rr):
        if rr.random() < 0.65:
            if lk.get("seam") and rr.random() < 0.7:
                u = rr.uniform(-1.3, 1.3)
                w = soff + rr.gauss(0, 0.25)
                return u * sdx - w * sdy, u * sdy + w * sdx
            cx, cy = clusters[rr.randrange(3)]
            return cx + rr.gauss(0, 0.45), cy + rr.gauss(0, 0.45)
        return ctx.sample(0.05, 0.2, rr)
    grit = KI.rock(base=scaled(lk["soil"], 1.5), base2=scaled(lk["soil"], 0.7), rough=0.9, scale=4.0, name="grit")
    scatter(ctx, [ore, ore, host], lk.get("n_mid", 170), (0.03, 0.08), sink=0.35, squash=squash, cuts=max(3, cuts - 2),
            bump=bump, where=near, seed=1)
    scatter(ctx, [ore, host, grit], 650, (0.015, 0.035), sink=0.35, squash=(1, 0.9, 0.6), cuts=max(3, cuts - 3),
            bump=bump, where=near, seed=2)


def s_rubble(ctx, lk):
    rnd = ctx.rnd
    mats = [ore_mat(dict(lk, mat="stone", color=None, ore_cap=0.17)),
            KI.rock(base=(0.2, 0.19, 0.18), base2=(0.12, 0.115, 0.11), speck=(0.03, 0.03, 0.03), speck_amt=0.7, rough=0.85,
                    scale=3.0, name="stone_b"),
            KI.rock(base=(0.3, 0.27, 0.22), base2=(0.18, 0.16, 0.13), speck=(0.08, 0.07, 0.06), speck_amt=0.5, rough=0.85,
                    scale=3.0, name="stone_c")]
    mounds = [(*ctx.sample(0.6, 0.5), rnd.uniform(0.55, 0.8), rnd.uniform(0.1, 0.15)) for _ in range(2)]

    def hf(x, y):
        z = ctx.undulate(x, y, 0.03)
        for cx, cy, r, h in mounds:
            q = math.hypot(x - cx, y - cy) / r
            if q < 1:
                z += h * (1 - q * q) ** 1.6
        return RIM_Z + ctx.inner(x, y, 0.4) * z
    terrain(ctx, hf, ground_mat(lk["soil"], (0.09, 0.07, 0.05), 0.35, gravel=0.9, damp=0.15, tint2=(0.12, 0.115, 0.105)))
    big = []
    for k in range(16):
        for _ in range(30):
            if k < 10:
                cx, cy, r0, _h = mounds[k % 2]
                x, y = cx + rnd.gauss(0, r0 * 0.5), cy + rnd.gauss(0, r0 * 0.5)
            else:
                x, y = ctx.sample(0.15, 0.3)
            r = rnd.uniform(0.06, 0.16)
            if ctx.hole.depth(x, y) > r + 0.06 and all(math.hypot(x - bx, y - by) > (r + br) * 0.8 for bx, by, br in big):
                big.append((x, y, r))
                break
    for k, (x, y, r) in enumerate(big):
        rock_at(ctx, x, y, r, mats[k % 3], sink=0.3, squash=(1, 0.85, 0.6), cuts=10, bump=0.08, seed=k * 7)

    def near(rr):
        if rr.random() < 0.6:
            cx, cy, r0, _h = mounds[rr.randrange(2)]
            return cx + rr.gauss(0, r0 * 0.6), cy + rr.gauss(0, r0 * 0.6)
        return ctx.sample(0.04, 0.2, rr)
    scatter(ctx, mats, 220, (0.025, 0.07), sink=0.25, squash=(1, 0.85, 0.6), cuts=8, bump=0.08, where=near, seed=1)
    scatter(ctx, mats, 900, (0.008, 0.025), sink=0.3, squash=(1, 0.85, 0.6), cuts=6, bump=0.1, where=near, seed=2)


def s_placer(ctx, lk):
    """Alluvial gravel bar: rounded pebbles, dark heavy cassiterite pay-streak, a puddle in the low channel."""
    rnd = ctx.rnd
    tin = KI.rock(base=(0.07, 0.045, 0.03), base2=(0.025, 0.02, 0.018), speck=(0.2, 0.18, 0.16), speck_metal=0.6,
                  speck_amt=0.6, rough=0.35, scale=3.0, glossy=True, name="cassiterite")
    peb = [KI.rock(base=(0.14, 0.135, 0.13), base2=(0.08, 0.077, 0.074), speck=(0.03, 0.03, 0.03), speck_amt=0.5, rough=0.55,
                   scale=3.0, name="pebble_grey"),
           KI.rock(base=(0.2, 0.15, 0.1), base2=(0.12, 0.09, 0.06), rough=0.6, scale=3.0, name="pebble_tan"),
           KI.rock(base=(0.3, 0.29, 0.27), base2=(0.2, 0.195, 0.185), rough=0.4, scale=3.0, name="pebble_quartz"),
           KI.rock(base=(0.1, 0.1, 0.11), base2=(0.05, 0.05, 0.055), rough=0.5, scale=3.0, name="pebble_dark")]
    ca = rnd.uniform(0, math.pi)
    cdx, cdy = math.cos(ca), math.sin(ca)
    coff = rnd.choice((-1, 1)) * rnd.uniform(0.45, 0.65)
    level = RIM_Z - 0.012

    def chan(x, y):
        return -x * cdy + y * cdx - coff

    def hf(x, y):
        c = chan(x, y)
        z = 0.04 + ctx.undulate(x, y, 0.025) - 0.12 * math.exp(-(c / 0.32) ** 2)
        z += 0.025 * math.sin((x * cdx + y * cdy) * 7.0 + c * 2.0) * math.exp(-(c / 0.6) ** 2)
        return RIM_Z + ctx.inner(x, y, 0.35) * z

    def streak(x, y):
        return math.exp(-((chan(x, y) + 0.3 * math.copysign(1, coff)) / 0.28) ** 2)

    def wet(x, y):
        return 1.0 if hf(x, y) < level + 0.025 else 0.35 * streak(x, y)

    def uw(x, y):
        return 1.0 - math.exp(-max(0.0, level - hf(x, y)) * 25.0)
    terrain(ctx, hf, ground_mat(lk["soil"], (0.05, 0.04, 0.032), 0.4, gravel=0.85, damp=0.35, wet_col=(0.55, 0.53, 0.5),
                                deep=(0.035, 0.03, 0.02)),
            {"stain": streak, "wet": wet, "uw": uw})
    ctx.level = level
    liquid_surface(ctx, level, water_mat((0.7, 0.68, 0.55), rough=0.04, name="muddy_water"))

    def where_peb(rr):
        return ctx.sample(0.05, 0.1, rr)

    def where_tin(rr):
        for _ in range(30):
            x, y = ctx.sample(0.05, 0.0, rr)
            if rr.random() < streak(x, y):
                return x, y
        return x, y
    for k in range(10):
        x, y = where_tin(rnd) if k % 2 else where_peb(rnd)
        rock_at(ctx, x, y, rnd.uniform(0.05, 0.11), tin if k % 2 else peb[k % 4], sink=0.4, squash=(1, 0.8, 0.55), cuts=1,
                bump=0.08, tilt=0.2, seed=k * 11)
    scatter(ctx, peb, 260, (0.02, 0.06), sink=0.35, squash=(1, 0.8, 0.55), cuts=1, subdiv=2, bump=0.1, where=where_peb, seed=1)
    scatter(ctx, [tin], 160, (0.015, 0.045), sink=0.35, squash=(1, 0.85, 0.6), cuts=2, bump=0.12, where=where_tin, seed=3)
    scatter(ctx, peb + [tin], 700, (0.007, 0.02), sink=0.3, squash=(1, 0.85, 0.6), cuts=1, bump=0.12, where=where_peb,
            seed=2)


def s_sand_bar(ctx, lk):
    rnd = ctx.rnd
    o = Vector((ctx.seed % 31, ctx.seed % 17, 0))
    sa = rnd.uniform(0, math.pi)

    def hf(x, y):
        dune = 0.11 * max(0.0, noise.fractal(Vector((x * 0.6, y * 0.8, 0)) + o, 0.7, 2.0, 3) + 0.45)
        z = 0.06 * math.exp(-(x * x + y * y) / 1.0) + dune + ctx.undulate(x, y, 0.015)
        return RIM_Z + ctx.inner(x, y, 0.5) * z

    def streak(x, y):
        u = -x * math.sin(sa) + y * math.cos(sa)
        w = math.sin(u * 11.0 + 2.2 * noise.noise(Vector((x * 1.2, y * 1.2, 0)) + o))
        fade = 0.5 + 0.5 * noise.noise(Vector((x * 2.0, y * 2.0, 3.0)) + o)
        return smoothstep(0.78, 0.97, w) * fade + 0.2 * smoothstep(0.2, 0.8, fade - 0.3)

    def wet(x, y):
        return 0.6 * (1.0 - smoothstep(0.0, 0.3, ctx.hole.depth(x, y)))
    terrain(ctx, hf, sand_mat(lk["sand"], lk.get("streak"), lk.get("sparkle", 0.0)),
            {"stain": streak if lk.get("streak") else (lambda x, y: 0.0), "wet": wet})
    stone = KI.surf("stone", None, scale=2.5)
    shell = KI.rock(base=(0.7, 0.66, 0.6), base2=(0.5, 0.46, 0.4), rough=0.5, scale=4.0, name="shell")
    for k in range(4):
        x, y = ctx.sample(0.3, 0.0)
        rock_at(ctx, x, y, rnd.uniform(0.05, 0.1), stone, sink=0.55, squash=(1, 0.8, 0.6), cuts=2, bump=0.1, seed=k * 9)
    scatter(ctx, [stone, shell], 50, (0.012, 0.035), sink=0.45, squash=(1, 0.8, 0.5), cuts=2, seed=1)


def s_lode(ctx, lk):
    """Dark bedrock crossed by a milky quartz vein carrying black bladed wolframite crystals."""
    rnd = ctx.rnd
    va = rnd.uniform(0.2, 1.3)
    vdx, vdy = math.cos(va), math.sin(va)
    path = [((u * vdx - 0.08 * math.sin(u * 2.3) * vdy), (u * vdy + 0.08 * math.sin(u * 2.3) * vdx)) for u in
            (-2.0, -1.2, -0.5, 0.0, 0.6, 1.3, 2.0)]
    W = 0.21

    def vein(x, y):
        dd, _ = seg_dist(x, y, path)
        return 1.0 - smoothstep(W * 0.8, W * 1.15, dd)

    def hf(x, y):
        z = 0.02 + ctx.undulate(x, y, 0.04, 1.4) + 0.035 * vein(x, y)
        return RIM_Z + ctx.inner(x, y, 0.35) * z
    terrain(ctx, hf, ground_mat(lk["soil"], (0.12, 0.11, 0.1), 0.25, gravel=0.4, damp=0.1, vein=(0.72, 0.71, 0.68),
                                bedrock=1.0), {"vein": vein})
    host = KI.rock(base=(0.08, 0.078, 0.075), base2=(0.04, 0.04, 0.04), vein=(0.6, 0.6, 0.58), vein_amt=0.25,
                   speck=(0.18, 0.18, 0.18), speck_amt=0.5, rough=0.7, scale=3.0, name="host_rock")
    quartz = KI.rock(base=(0.7, 0.69, 0.66), base2=(0.5, 0.49, 0.47), speck=(0.1, 0.1, 0.1), speck_amt=0.3, rough=0.3,
                     scale=3.0, name="vein_quartz")
    wolf = M.metal("dark_steel", rough=0.28, tint=(0.8, 0.76, 0.7), dirt=0.25)
    # blades of wolframite growing out of the vein, mostly lying low
    for k in range(34):
        u = rnd.uniform(0.0, 1.0)
        i = min(len(path) - 2, int(u * (len(path) - 1)))
        f = u * (len(path) - 1) - i
        x = path[i][0] + (path[i + 1][0] - path[i][0]) * f + rnd.gauss(0, W * 0.4) * -vdy
        y = path[i][1] + (path[i + 1][1] - path[i][1]) * f + rnd.gauss(0, W * 0.4) * vdx
        if ctx.hole.depth(x, y) < 0.12:
            continue
        L = rnd.uniform(0.07, 0.18)
        o = K.box((L, rnd.uniform(0.02, 0.04), rnd.uniform(0.008, 0.016)), (0, 0, 0), wolf, bevel=0.002, name="blade")
        top = _settle(o, x, y, ctx.hf(x, y), 0.35, (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.6, 0.6),
                                                     va + math.pi / 2 + rnd.gauss(0, 0.5)))
        ctx.pts.append((x, y, top))
    for k in range(9):
        x, y = ctx.sample(0.25, 0.3)
        rock_at(ctx, x, y, rnd.uniform(0.07, 0.17), host if k % 3 else quartz, sink=0.4, squash=(1, 0.85, 0.55), cuts=10,
                bump=0.08, seed=k * 5)

    def on_vein(rr):
        for _ in range(20):
            x, y = ctx.sample(0.05, 0.0, rr)
            if rr.random() < 0.15 + vein(x, y):
                return x, y
        return x, y
    scatter(ctx, [quartz, host, wolf], 160, (0.02, 0.06), sink=0.3, squash=(1, 0.85, 0.55), cuts=8, bump=0.08,
            where=on_vein, seed=1)
    scatter(ctx, [host, quartz], 500, (0.008, 0.022), sink=0.3, squash=(1, 0.85, 0.6), cuts=6, seed=2)


def _vents(ctx, n, spacing=0.55, along=None):
    pts = []
    rnd = ctx.rnd
    for _ in range(n):
        for _ in range(60):
            if along:
                u = rnd.uniform(0.2, 0.8)
                i = min(len(along) - 2, int(u * (len(along) - 1)))
                f = u * (len(along) - 1) - i
                x = along[i][0] + (along[i + 1][0] - along[i][0]) * f
                y = along[i][1] + (along[i + 1][1] - along[i][1]) * f
            else:
                x, y = ctx.sample(0.45, 0.5)
            if ctx.hole.depth(x, y) > 0.4 and all(math.hypot(x - a, y - b) > spacing for a, b, _ in pts):
                pts.append((x, y, rnd.uniform(0.05, 0.08)))
                break
    return pts


def s_fumarole(ctx, lk):
    rnd = ctx.rnd
    vents = _vents(ctx, 3)

    def vent_h(x, y):
        z = 0.0
        for vx, vy, vr in vents:
            q = math.hypot(x - vx, y - vy)
            z += 0.08 * math.exp(-(q / 0.32) ** 2) - 0.16 * math.exp(-(q / vr) ** 4)
        return z

    def hf(x, y):
        return RIM_Z + ctx.inner(x, y, 0.35) * (0.02 + ctx.undulate(x, y, 0.035, 1.2) + vent_h(x, y))

    def crust(x, y):
        return max(math.exp(-(math.hypot(x - vx, y - vy) / 0.42) ** 2) for vx, vy, _ in vents) * 1.1

    def stain(x, y):
        return 0.6 * max(math.exp(-(math.hypot(x - vx, y - vy) / 0.7) ** 2) for vx, vy, _ in vents)

    def pit(x, y):
        return max(math.exp(-(math.hypot(x - vx, y - vy) / (vr * 0.9)) ** 4) for vx, vy, vr in vents)
    terrain(ctx, hf, ground_mat(lk["soil"], (0.13, 0.06, 0.02), 0.0, gravel=0.35, damp=0.1, crust=lk["crust"],
                                bedrock=0.4), {"crust": crust, "stain": stain, "pit": pit})
    sulfur = KI.surf("sulfur", None, scale=3.0)
    host = KI.rock(base=(0.14, 0.13, 0.11), base2=(0.07, 0.065, 0.06), vein=(0.7, 0.52, 0.03), vein_amt=0.4,
                   speck=(0.75, 0.55, 0.04), speck_amt=0.4, rough=0.85, scale=3.0, name="crusted_rock")
    for k in range(8):
        x, y = ctx.sample(0.2, 0.2)
        rock_at(ctx, x, y, rnd.uniform(0.06, 0.15), host if k % 3 else sulfur, sink=0.4, squash=(1, 0.85, 0.6), cuts=8,
                bump=0.14, seed=k * 3)
    # sulfur needle crystals crowding the vent mouths
    for vx, vy, vr in vents:
        ctx.emitters.append({"pos": [round(vx, 3), round(vy, 3), round(ctx.hf(vx + vr * 1.8, vy) + 0.02, 3)],
                             "type": "steam"})   # at the vent mouth
        for k in range(rnd.randint(14, 20)):
            a = rnd.uniform(0, math.tau)
            dd = vr * rnd.uniform(1.0, 2.4)
            x, y = vx + dd * math.cos(a), vy + dd * math.sin(a)
            L = rnd.uniform(0.025, 0.06)
            r = L * 0.22
            o = KI.lathe([(0, -0.02), (r, -0.02), (r, L - r * 1.6), (r * 0.1, L), (0, L)], sulfur, segs=6, name="xtal",
                         smooth=20)
            o.rotation_euler = (rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), rnd.uniform(0, 6))
            o.location = (x, y, ctx.hf(x, y) - 0.005)

    def near_vent(rr):
        vx, vy, _ = vents[rr.randrange(len(vents))]
        return vx + rr.gauss(0, 0.3), vy + rr.gauss(0, 0.3)
    scatter(ctx, [sulfur, host], 140, (0.015, 0.05), sink=0.3, squash=(1, 0.85, 0.6), cuts=6, where=near_vent, seed=1)
    scatter(ctx, [host, KI.surf("stone", None, scale=3.0)], 400, (0.008, 0.025), sink=0.3, seed=2)


def s_gas_vent(ctx, lk):
    """Dry cracked ground split by a fissure lined with mineral crust; gas escapes from vents along it."""
    rnd = ctx.rnd
    fa = rnd.uniform(0, math.pi)
    fdx, fdy = math.cos(fa), math.sin(fa)
    path = []
    for u in (-1.8, -1.1, -0.55, 0.0, 0.5, 1.05, 1.8):
        w = rnd.uniform(-0.12, 0.12)
        path.append((u * fdx - w * fdy, u * fdy + w * fdx))
    branch = [path[3], (path[3][0] + 0.45 * -fdy + 0.2 * fdx, path[3][1] + 0.45 * fdx + 0.2 * fdy),
              (path[3][0] + 0.85 * -fdy + 0.15 * fdx, path[3][1] + 0.85 * fdx + 0.15 * fdy)]
    vents = _vents(ctx, 3, 0.5, along=path)

    def fiss(x, y):
        d1, u = seg_dist(x, y, path)
        d2, _ = seg_dist(x, y, branch)
        w1 = 0.07 * (0.5 + math.sin(u * math.pi))
        return min(d1 / w1, d2 / 0.045)

    def hf(x, y):
        q = fiss(x, y)
        z = 0.025 + ctx.undulate(x, y, 0.03, 1.1)
        z += 0.035 * math.exp(-(q / 3.0) ** 2)            # crust levee
        z -= 0.24 * max(0.0, 1 - q) ** 1.2                 # the fissure
        for vx, vy, vr in vents:
            dd = math.hypot(x - vx, y - vy)
            z += 0.05 * math.exp(-(dd / 0.22) ** 2) - 0.2 * math.exp(-(dd / vr) ** 4)
        return RIM_Z + ctx.inner(x, y, 0.3) * z

    def crust(x, y):
        v = max(math.exp(-(math.hypot(x - vx, y - vy) / 0.32) ** 2) for vx, vy, _ in vents)
        q = fiss(x, y)
        return max(v * 1.1, math.exp(-(q / 3.2) ** 2)) * smoothstep(0.7, 1.3, q)

    def pit(x, y):
        q = fiss(x, y)
        v = max(math.exp(-(math.hypot(x - vx, y - vy) / vr) ** 4) for vx, vy, vr in vents)
        return max(1.0 - smoothstep(0.4, 1.05, q), v)
    terrain(ctx, hf, ground_mat(lk["soil"], None, 0.0, gravel=0.35, damp=0.05, crust=lk["crust"], bedrock=0.6),
            {"crust": crust, "pit": pit}, segs=360, rings=110)
    stone = KI.rock(base=lk["soil"], base2=scaled(lk["soil"], 0.55), speck=scaled(lk["crust"], 0.9), speck_amt=0.4,
                    rough=0.85, scale=3.0, name="vent_rock")
    crust_m = KI.rock(base=lk["crust"], base2=scaled(lk["crust"], 0.6), speck=(0.9, 0.9, 0.88), speck_amt=0.5, rough=0.85,
                      scale=4.0, name="vent_crust")
    for vx, vy, vr in vents:
        ctx.emitters.append({"pos": [round(vx, 3), round(vy, 3), round(ctx.hf(vx + vr * 1.8, vy) + 0.02, 3)],
                             "type": "steam"})   # at the vent mouth
    for k in range(7):
        u = rnd.uniform(0.1, 0.9)
        i = int(u * (len(path) - 1))
        f = u * (len(path) - 1) - i
        side = rnd.choice((-1, 1)) * rnd.uniform(0.16, 0.3)
        x = path[i][0] + (path[i + 1][0] - path[i][0]) * f - side * fdy
        y = path[i][1] + (path[i + 1][1] - path[i][1]) * f + side * fdx
        if ctx.hole.depth(x, y) > 0.2:
            rock_at(ctx, x, y, rnd.uniform(0.06, 0.13), stone if k % 2 else crust_m, sink=0.4, squash=(1, 0.85, 0.5),
                    cuts=10, bump=0.08, seed=k * 3)

    def near_f(rr):
        for _ in range(20):
            x, y = ctx.sample(0.05, 0.0, rr)
            if rr.random() < math.exp(-(fiss(x, y) / 6.0) ** 2) and fiss(x, y) > 1.3:
                return x, y
        return x, y
    scatter(ctx, [stone, crust_m], 200, (0.015, 0.05), sink=0.3, squash=(1, 0.85, 0.5), cuts=8, where=near_f, seed=1)
    scatter(ctx, [stone], 350, (0.008, 0.022), sink=0.3, seed=2)


def s_water_pool(ctx, lk):
    rnd = ctx.rnd
    level = RIM_Z + 0.025
    sh = rnd.uniform(0, math.tau)

    def hf(x, y):
        dp = ctx.hole.depth(x, y)
        bowl = -0.26 * smoothstep(0.0, 0.9, dp)
        shore = 0.13 * math.exp(-((x - 0.9 * math.cos(sh)) ** 2 + (y - 0.9 * math.sin(sh)) ** 2) / 0.25)
        return RIM_Z + ctx.inner(x, y, 0.25) * (bowl + shore + ctx.undulate(x, y, 0.04, 1.2))

    def stain(x, y):   # algae / silt band just below the waterline
        dz = level - hf(x, y)
        return math.exp(-((dz - 0.06) / 0.05) ** 2)

    def wet(x, y):
        return 1.0 if hf(x, y) < level + 0.04 else 0.4

    def uw(x, y):
        return 1.0 - math.exp(-max(0.0, level - hf(x, y)) * 8.0)
    terrain(ctx, hf, ground_mat(lk["soil"], (0.035, 0.05, 0.02), 0.25, gravel=0.6, damp=0.4, wet_col=(0.55, 0.55, 0.5),
                                deep=(0.008, 0.02, 0.024)),
            {"stain": stain, "wet": wet, "uw": uw})
    ctx.level = level
    liquid_surface(ctx, level, water_mat((0.64, 0.8, 0.8)))
    stone = KI.rock(base=(0.1, 0.095, 0.085), base2=(0.05, 0.048, 0.045), speck=(0.02, 0.02, 0.02), speck_amt=0.6,
                    rough=0.7, scale=3.0, name="river_stone")
    mossy = KI.rock(base=(0.05, 0.06, 0.03), base2=(0.025, 0.03, 0.015), speck=(0.1, 0.1, 0.08), speck_amt=0.4, rough=0.6,
                    scale=3.0, name="mossy_rock")

    def shallow(rr):
        for _ in range(40):
            x, y = ctx.sample(0.06, 0.0, rr)
            if level - ctx.hf(x, y) < 0.06:
                return x, y
        return x, y
    for k in range(6):
        x, y = shallow(rnd)
        rock_at(ctx, x, y, rnd.uniform(0.07, 0.15), stone if k % 2 else mossy, sink=0.35, squash=(1, 0.85, 0.6), cuts=2,
                bump=0.12, tilt=0.2, seed=k * 3)
    scatter(ctx, [stone, mossy], 90, (0.015, 0.05), sink=0.35, squash=(1, 0.8, 0.55), cuts=2, bump=0.12, where=shallow,
            seed=1)


def s_oil_seep(ctx, lk):
    rnd = ctx.rnd
    level = RIM_Z - 0.01
    o = Vector((ctx.seed % 41, ctx.seed % 23, 0))

    def hf(x, y):
        lumps = 0.07 * noise.fractal(Vector((x * 1.1, y * 1.1, 0)) + o, 0.6, 2.0, 3)
        bowl = -0.09 * math.exp(-(x * x + y * y) / 0.7)
        return RIM_Z + ctx.inner(x, y, 0.3) * (lumps + bowl + 0.015)

    def wet(x, y):
        return 1.0
    terrain(ctx, hf, ground_mat(lk["soil"], (0.012, 0.01, 0.009), 0.7, gravel=0.35, damp=0.6, gloss=0.6,
                                wet_col=(0.35, 0.3, 0.27)), {"wet": wet})
    ctx.level = level
    liquid_surface(ctx, level, oil_mat())
    tar = KI.rock(base=(0.03, 0.026, 0.023), base2=(0.014, 0.012, 0.011), speck=(0.08, 0.075, 0.07), speck_amt=0.3, rough=0.4,
                  scale=3.0, name="tar_rock")
    for k in range(5):
        x, y = ctx.sample(0.2, 0.0)
        rock_at(ctx, x, y, rnd.uniform(0.06, 0.13), tar, sink=0.45, squash=(1, 0.85, 0.55), cuts=4, bump=0.15, seed=k * 3)
    scatter(ctx, [tar], 70, (0.015, 0.045), sink=0.45, squash=(1, 0.85, 0.55), cuts=4, seed=1, dry=True)
    # bubbles rising in the pool
    for k in range(4):
        x, y = ctx.sample(0.35, 0.6)
        if ctx.hf(x, y) < level - 0.01:
            K.sphere(rnd.uniform(0.008, 0.02), (x, y, level), oil_mat(), segs=16, rings=8, scale=(1, 1, 0.55))
    ctx.emitters.append({"pos": [0.0, 0.0, round(level, 3)], "type": "bubbles"})


def s_brine_flat(ctx, lk):
    rnd = ctx.rnd
    level = RIM_Z + 0.0
    o = Vector((ctx.seed % 41, ctx.seed % 23, 0))

    def hf(x, y):
        pud = 0.06 * noise.fractal(Vector((x * 1.3, y * 1.3, 0)) + o, 0.6, 2.0, 3)
        return RIM_Z + ctx.inner(x, y, 0.3) * (0.012 + pud - 0.03 * math.exp(-(x * x + y * y) / 0.9))

    def wet(x, y):
        return 1.0 - smoothstep(0.0, 0.04, hf(x, y) - level)

    def uw(x, y):
        return 1.0 - math.exp(-max(0.0, level - hf(x, y)) * 22.0)
    terrain(ctx, hf, salt_mat(), {"wet": wet, "uw": uw})
    ctx.level = level
    liquid_surface(ctx, level, water_mat((0.66, 0.8, 0.78), rough=0.03, name="brine"))
    salt = KI.rock(base=(0.45, 0.44, 0.42), base2=(0.3, 0.29, 0.27), rough=0.5, scale=5.0, name="salt_lump")
    # cubic halite crystals on the pool margins
    for k in range(70):
        x, y = ctx.sample(0.08, 0.0)
        zg = ctx.hf(x, y)
        if abs(zg - level) > 0.02:
            continue
        s = rnd.uniform(0.008, 0.025)
        K.box((s, s, s), (x, y, zg + s * 0.2), salt, bevel=0.001, rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4),
                                                                         rnd.uniform(0, 6)), name="halite")
    for k in range(5):
        x, y = ctx.sample(0.2, 0.0)
        rock_at(ctx, x, y, rnd.uniform(0.05, 0.1), salt, sink=0.5, squash=(1, 0.9, 0.45), cuts=6, bump=0.2, seed=k)


STYLES = {
    "ore_field": s_ore_field, "rubble": s_rubble, "placer": s_placer, "sand_bar": s_sand_bar, "lode": s_lode,
    "fumarole": s_fumarole, "gas_vent": s_gas_vent, "water_pool": s_water_pool, "oil_seep": s_oil_seep,
    "brine_flat": s_brine_flat,
}
SPILL = {   # apron overlay per style: (kind, spread m, amount)
    "water_pool": ("wet", 0.28, 0.9), "oil_seep": ("oil", 0.38, 0.8), "brine_flat": ("dust", 0.4, 0.6),
    "sand_bar": ("dust", 0.6, 0.9), "fumarole": ("dust", 0.35, 0.7), "gas_vent": ("dust", 0.3, 0.55),
}


def build(d):
    lk = look_for(d)
    style = lk["style"]
    kind, spread, amt = SPILL.get(style, ("dust", 0.5, 0.75))
    lk.setdefault("spill", kind)
    lk.setdefault("spread", spread)
    lk.setdefault("dust_amt", amt)
    if style == "brine_flat":
        lk.setdefault("dust", (0.17, 0.165, 0.155))
    ctx = Ctx(d, lk)
    build_apron(ctx, lk)
    STYLES[style](ctx, lk)
    fluid = style in ("water_pool", "oil_seep", "brine_flat")
    fragments(ctx, 3 if fluid else 6)
    rebar(ctx, ctx.rnd.randint(3, 5))
    return style, ctx


# =========================================================================== render
def render_deposit(d, quality, out_png, out_json=None):
    t0 = time.time()
    studio.reset(quality)
    KI.reset()
    # No shadow catcher: every shadow falls on real geometry (the apron *is* the floor), and a catcher under the
    # fading apron would only pick up the apron's own occlusion as a dark halo.
    style, ctx = build(d)
    info = studio.frame_iso_camera(ctx.pts, margin_px=4)
    studio.render_to(out_png)
    if out_json:
        meta = {"origin": info["origin"]}
        if ctx.emitters:
            meta["emitters"] = [dict(e, px=studio.world_to_px(e["pos"])) for e in ctx.emitters]
        studio.write_json(out_json, meta)
    print(f"[done] {d['id']} ({style}) {info['width']}x{info['height']} in {time.time() - t0:.1f}s", flush=True)


def parse(argv):
    o = {"quality": "draft", "ids": None, "all": False, "missing": False}
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
    deps = studio.load_data("world")["deposits"]
    if o["ids"]:
        want = o["ids"].split(",")
        deps = [d for w in want for d in deps if d["id"] == w]
    if o["missing"]:
        deps = [d for d in deps if not os.path.exists(os.path.join(OUT_DIR, f"deposit_{d['id']}.png"))]
    entries = []
    t0 = time.time()
    for d in deps:
        png = os.path.join(OUT_DIR, f"deposit_{d['id']}.png")
        try:
            render_deposit(d, o["quality"], png, os.path.join(OUT_DIR, f"deposit_{d['id']}.json"))
            entries.append((png, d["id"]))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[fail] {d['id']}: {e}", flush=True)
    print(f"[total] {len(entries)}/{len(deps)} deposits in {time.time() - t0:.1f}s", flush=True)
    if len(entries) > 1:
        KI.contact_sheet(entries, SHEET, cell=256, cols=4, small=0)


main()
