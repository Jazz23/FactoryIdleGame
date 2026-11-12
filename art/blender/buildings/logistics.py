"""Logistics / support archetypes: storage_tank, warehouse, silo, conveyor_hub, rail_depot,
drone_port, beacon, scrubber."""
import math
import random

import bpy
from mathutils import Vector

import kit as K
import kit_industry as KI
import materials as M
from buildings import Rig

TAU = KI.TAU


def _size(spec):
    w, d = spec.get("size", [2, 2])
    return float(w), float(d)


def _translucent(color, alpha=0.3, name="rotor_blur"):
    """Partly transparent dark disc (rotor blur) - keeps real alpha on transparent sprites."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = 0.5
    bs.inputs["Alpha"].default_value = alpha
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return m


# =========================================================================== storage tank
def storage_tank(spec, p):
    """Fluid storage: welded vertical tank (cone roof, caged ladder, roof rail, float level gauge,
    manway, valved outlet) inside a concrete bund. variant 'sphere' / 'horizontal' for pressure
    vessels. Static with a roof status light."""
    KI.begin()
    st = KI.Style(p)
    w, d = _size(spec)
    s = min(w, d)
    variant = st.variant
    conc = st.concrete(0.4)
    KI.concrete_pad(w * 0.98, d * 0.98, 0.08, conc)
    z0 = 0.08
    bw = 0.07 + 0.02 * s
    for sy in (-1, 1):
        K.box((w * 0.96, bw, 0.22), (0, sy * (d * 0.48 - bw / 2), z0), conc, bevel=0.012, base=True)
    for sx in (-1, 1):
        K.box((bw, d * 0.96 - 2 * bw, 0.22), (sx * (w * 0.48 - bw / 2), 0, z0), conc, bevel=0.012, base=True)
    shell = st.body() if st.tier != 2 else st.mat((0.62, 0.63, 0.6), name="tank_white")
    band = st.accent_mat() if st.tier != 2 else st.body()
    steel = st.steel()
    lights = []
    if variant == "sphere":
        many = s >= 4.0
        r = (0.25 if many else 0.4) * s
        cs_ = [Vector((-0.2 * w, 0.2 * d, 0)), Vector((0.2 * w, -0.18 * d, 0))] if many else [Vector((-0.04 * w, 0.04 * d, 0))]
        for n_, c0 in enumerate(cs_):
            C = Vector((c0.x, c0.y, z0 + 0.25 * s ** 0.8 + r))
            K.sphere(r, C, shell, segs=48, rings=24)
            K.torus(r * 1.003, 0.03, C, band, segs=64)
            for i in range(6):
                a = TAU * i / 6 + 0.3
                top = C + Vector((math.cos(a) * r * 0.98, math.sin(a) * r * 0.98, 0))
                K.cyl(0.05 * s ** 0.5, top.z - z0, Vector((top.x, top.y, z0)), st.frame(), verts=16)
                K.box((0.14, 0.14, 0.04), Vector((top.x, top.y, z0)), M.metal("dark_steel"), bevel=0.006, base=True)
            for i in range(6):
                a0 = TAU * i / 6 + 0.3
                a1 = TAU * (i + 1) / 6 + 0.3
                KI.strut((C.x + math.cos(a0) * r * 0.98, C.y + math.sin(a0) * r * 0.98, z0 + 0.1), (C.x + math.cos(a1) * r * 0.98, C.y + math.sin(a1) * r * 0.98, C.z - r * 0.2), 0.012, st.frame(), verts=6)
            top_z = C.z + r
            K.cyl(0.18, 0.08, (C.x, C.y, top_z - 0.03), steel, verts=24)
            K.railing([(C.x - 0.25, C.y - 0.25, top_z + 0.04), (C.x + 0.25, C.y - 0.25, top_z + 0.04), (C.x + 0.25, C.y + 0.25, top_z + 0.04)], 0.6, st.safety())
            K.box((0.6, 0.6, 0.03), (C.x, C.y, top_z + 0.02), M.tread_plate(1.2), bevel=0.004)
            KI.pipe([(C.x, C.y, C.z - r * 0.95), (C.x, C.y, z0 + 0.3), (w * 0.47, C.y, z0 + 0.3)], r=0.05 * s ** 0.5, mat=st.mat((0.5, 0.5, 0.48), name="pipe_paint"))
            KI.gate_valve((C.x + r * 0.7, C.y, z0 + 0.3), "x", r=0.05 * s ** 0.5)
            KI.plate_sign((C.x, C.y - r - 0.01, C.z + r * 0.25), 0.3 * s ** 0.5, 0.15 * s ** 0.5, "-y", color=(0.85, 0.85, 0.82))
            if n_ == 0:
                lamp = Vector((C.x + 0.2, C.y - 0.2, top_z + 0.65))
                top_z0 = top_z
        if many:
            # stair tower / pipe bridge between the spheres
            KI.pipe([(cs_[0].x + r * 0.7, cs_[0].y, z0 + 0.6), (cs_[1].x - r * 0.3, cs_[0].y, z0 + 0.6), (cs_[1].x - r * 0.3, cs_[1].y + r * 0.7, z0 + 0.6)],
                    r=0.06 * s ** 0.5, mat=st.mat((0.6, 0.45, 0.03), name="gas_line"))
        top_z = top_z0
    elif variant == "horizontal":
        r = 0.27 * d
        L = w * 0.78
        C = Vector((-0.02 * w, 0.02 * d, z0 + 0.32 + r))
        K.cyl(r, L - r * 0.8, C, shell, rot=K.AXES["x"], verts=48, base=False)
        for sx in (-1, 1):
            K.sphere(r, C + Vector((sx * (L / 2 - r * 0.4), 0, 0)), shell, scale=(0.4, 1, 1))
            K.prism([(-0.14, 0), (0.14, 0), (0.1, C.z - z0 - r * 0.5), (-0.1, C.z - z0 - r * 0.5)], r * 1.5, (C.x + sx * L * 0.3, C.y, z0), st.frame(), bevel=0.008)
        for xx in (-0.15, 0.15):
            K.torus(r * 1.005, 0.025, C + Vector((xx * L, 0, 0)), band, rot=K.AXES["x"], segs=48)
        top_z = C.z + r
        K.cyl(0.12, 0.1, (C.x, C.y, top_z - 0.02), steel, verts=20)
        K.cyl(0.04, 0.2, (C.x + L * 0.25, C.y, top_z - 0.02), steel, verts=12)
        KI.pipe([(C.x - L * 0.25, C.y, C.z - r * 0.9), (C.x - L * 0.25, C.y, z0 + 0.16), (C.x - L * 0.25, -d * 0.47, z0 + 0.16)], r=0.04 * s ** 0.5,
                mat=st.mat((0.5, 0.5, 0.48), name="pipe_paint"))
        KI.gate_valve((C.x - L * 0.25, -d * 0.3, z0 + 0.16), "y", r=0.04 * s ** 0.5)
        KI.plate_sign((C.x, C.y - r - 0.01, C.z), 0.3, 0.16, "-y", color=(0.85, 0.85, 0.82))
        KI.ladder(Vector((C.x + L * 0.2, C.y - r - 0.05, z0)), top_z - z0, w=0.34, mat=st.safety())
        lamp = Vector((C.x - L * 0.3, C.y, top_z + 0.0))
    else:
        r = 0.38 * s
        H = 0.8 + 0.72 * s
        C = Vector((-0.04 * w, 0.05 * d, z0))
        K.cyl(r * 1.04, 0.08, C, M.concrete(0.8), verts=56)
        K.cyl(r, H, C + Vector((0, 0, 0.08)), shell, verts=64, name="tank_shell")
        courses = max(3, int(H / 0.6))
        for i in range(1, courses):
            K.torus(r * 1.001, 0.006, C + Vector((0, 0, 0.08 + H * i / courses)), shell, segs=64, rsegs=6)
        K.torus(r * 1.004, 0.035, C + Vector((0, 0, 0.08 + H * 0.62)), band, segs=64, rsegs=8)
        K.torus(r * 1.004, 0.035, C + Vector((0, 0, 0.08 + H * 0.55)), band, segs=64, rsegs=8)
        top = 0.08 + H
        K.cyl(r * 1.02, 0.17 * r, C + Vector((0, 0, top)), shell, verts=64, r2=0.12, name="roof")
        K.torus(r * 1.0, 0.03, C + Vector((0, 0, top)), steel, segs=64)
        # roof railing arc on the front quarter
        arc = [C + Vector((math.cos(a) * r * 0.95, math.sin(a) * r * 0.95, top + 0.02)) for a in [math.radians(-150 + 15 * i) for i in range(9)]]
        K.railing(arc, 0.55 + 0.1 * s, st.safety())
        # roof nozzles: vent gooseneck + PRV + gauge hatch
        K.cyl(0.08, 0.25, C + Vector((r * 0.25, r * 0.15, top + 0.12)), steel, verts=16)
        K.tube([C + Vector((r * 0.25, r * 0.15, top + 0.36)), C + Vector((r * 0.25, r * 0.15, top + 0.48)), C + Vector((r * 0.25, r * 0.3, top + 0.42))], 0.07, steel)
        K.cyl(0.06, 0.18, C + Vector((-r * 0.3, -r * 0.05, top + 0.1)), M.painted((0.6, 0.05, 0.02), name="prv"), verts=16)
        # caged ladder on the +X side up to the roof
        KI.ladder(C + Vector((r + 0.05, -r * 0.25, 0.08)), top - 0.08 + 0.6, rot_z=math.pi / 2, w=0.36, mat=st.safety(), cage=True)
        # float level gauge board on the -Y face
        gy = C.y - r - 0.04
        K.box((0.05, 0.03, H * 0.9), (C.x - r * 0.35, gy + 0.02 + r * (1 - math.cos(math.asin(0.35))), z0 + 0.15), M.painted((0.85, 0.85, 0.82), name="gauge_board"), bevel=0.004, base=True)
        mk_z = z0 + 0.15 + H * 0.9 * 0.62
        K.box((0.08, 0.04, 0.05), (C.x - r * 0.35, gy + r * (1 - math.cos(math.asin(0.35))), mk_z), M.painted((0.8, 0.1, 0.02), name="float_mark"), bevel=0.004)
        # manway + outlet with valve
        K.cyl(0.22 * s ** 0.5, 0.06, (C.x + r * 0.35, C.y - r * 0.94, z0 + 0.45), steel, rot=(math.pi / 2, 0, -0.36), verts=32, base=False)
        K.bolts(Vector((C.x + r * 0.35 + 0.012, C.y - r * 0.94 - 0.035, z0 + 0.45)), 0.18 * s ** 0.5, 12, axis="-y", r=0.012)
        oy = C.y - r * 0.3
        KI.pipe([(C.x + r * 0.95, oy, z0 + 0.3), (w * 0.47, oy, z0 + 0.3)], r=0.05 * s ** 0.5, mat=st.mat((0.5, 0.5, 0.48), name="pipe_paint"))
        KI.gate_valve((C.x + r + 0.25, oy, z0 + 0.3), "x", r=0.05 * s ** 0.5)
        KI.pipe([(C.x - r * 0.5, C.y - r * 0.87, top + 0.05), (C.x - r * 0.5, C.y - r * 0.87 - 0.12, top + 0.05), (C.x - r * 0.5, C.y - r * 0.87 - 0.12, z0 + 0.25),
                 (C.x - r * 0.5, -d * 0.47, z0 + 0.25)], r=0.035 * s ** 0.5, mat=st.mat((0.5, 0.5, 0.48), name="pipe_paint"))
        KI.plate_sign((C.x + r * 0.05, C.y - r - 0.015, z0 + H * 0.35), 0.32 * s ** 0.5, 0.2 * s ** 0.5, "-y", color=(0.85, 0.85, 0.82))
        top_z = C.z + top + 0.17 * r
        if variant == "cryo":
            # frosted base + ambient air vaporiser bank (finned tubes)
            K.cyl(r * 1.01, 0.35, C + Vector((0, 0, 0.08)), M.plastic((0.85, 0.88, 0.9), 0.7, name="frost"), verts=64)
            vx0, vy0 = C.x + r + 0.2, -0.38 * d
            vx0 = min(vx0, 0.3 * w)
            for i in range(3):
                for j in range(2):
                    vp = Vector((vx0 + i * 0.22 * s ** 0.5, vy0 + j * 0.22 * s ** 0.5, z0))
                    K.cyl(0.03, H * 0.55, vp, M.metal("aluminum", dirt=0.2), verts=8)
                    for q in range(4):
                        K.box((0.16 * s ** 0.5, 0.006, H * 0.55), vp + Vector((0, 0, 0)), M.metal("aluminum", dirt=0.2), bevel=0.001, base=True, rot=(0, 0, q * math.pi / 4))
                    K.cyl(0.035, 0.18, vp, M.plastic((0.9, 0.93, 0.95), 0.6, name="frost"), verts=8)
            KI.pipe([(C.x + r * 0.8, C.y - r * 0.5, z0 + 0.5), (vx0, C.y - r * 0.5, z0 + 0.5), (vx0, vy0, z0 + 0.5)], r=0.04 * s ** 0.5,
                    mat=M.plastic((0.88, 0.9, 0.92), 0.6, name="insulated"))
        lamp = C + Vector((-r * 0.6, -r * 0.6, top + 0.02))
    _, sock = KI.status_lamp(lamp, st.glow_col if st.tier >= 3 else (0.1, 1.0, 0.25), 12.0)
    KI.cabinet((w * 0.36, -d * 0.36, z0), 0.0, w=0.24, d=0.14, h=0.5, mat=st.mat((0.6, 0.6, 0.58), wear=0.5)) if w >= 2 else None
    K.scatter_debris(w * 0.8, d * 0.8, 3, seed=5)
    return Rig(height=top_z + 0.7, frames=1, fps=1,
               lights=[{"pos": list(lamp + Vector((0, 0, 0.05))), "color": [0.2, 1.0, 0.3], "energy": 0.3, "flicker": False}])


# =========================================================================== warehouse
def warehouse(spec, p):
    """Portal-frame steel shed: trapezoidal cladding, low-pitch gable roof with skylights and ridge
    vent, roller doors with bollards and lamps on the front, strip windows, gutters/downpipes,
    pallets of stock outside. Static, lit door lamps + status light.
    variants: 'crate' (single supply crate, small footprints), 'vault' (armoured concrete store with
    a round blast door), 'automated' (adds a high-bay racking block, rooftop HVAC, feed conveyor)."""
    v = str(p.get("variant", ""))
    w0, d0 = _size(spec)
    if v == "crate" or max(w0, d0) < 1.6:
        return _supply_crate(spec, p)
    if v == "vault":
        return _vault(spec, p)
    KI.begin()
    tier = max(1, min(4, int(p.get("tier", 1) or 1)))
    default = {1: (0.11, 0.085, 0.06), 2: (0.07, 0.15, 0.08), 3: (0.1, 0.15, 0.24), 4: (0.62, 0.63, 0.64)}[tier]
    st = KI.Style(p, paint=default)
    if not p.get("paint"):
        st.paint = default
    w, d = _size(spec)
    s = min(w, d)
    trim = st.mat((0.04, 0.042, 0.045) if tier != 4 else (0.035, 0.037, 0.04), name="trim")
    clad = st.body(rough=0.45)
    conc = st.concrete(0.4)
    K.box((w * 0.98, d * 0.98, 0.14), (0, 0, 0), conc, bevel=0.02, base=True, name="slab")
    z0 = 0.14
    ww, dd = w * 0.9, d * 0.82
    cy = 0.05 * d
    H = 1.5 + 0.38 * s
    pitch = math.radians(9)
    rise = dd / 2 * math.tan(pitch)
    # cladding (all four walls; gables get triangles on top)
    KI.corrugated(ww, H, (0, cy - dd / 2, z0), 0.0, clad)
    KI.corrugated(ww, H, (0, cy + dd / 2, z0), math.pi, clad)
    KI.corrugated(dd, H, (ww / 2, cy, z0), math.pi / 2, clad)
    KI.corrugated(dd, H, (-ww / 2, cy, z0), -math.pi / 2, clad)
    for sx in (-1, 1):
        K.prism([(-dd / 2, 0), (dd / 2, 0), (0, rise)], 0.03, (sx * (ww / 2 - 0.01), cy, z0 + H), clad, rot=(0, 0, math.pi / 2), bevel=0.004)
    K.box((ww - 0.06, dd - 0.06, H), (0, cy, z0), M.plastic((0.02, 0.02, 0.02), 0.9), bevel=0, base=True)  # inner volume (no see-through)
    # base kerb + corner trims + eave trims
    K.box((ww + 0.06, dd + 0.06, 0.2), (0, cy, z0), conc, bevel=0.01, base=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.08, 0.08, H), (sx * ww / 2, cy + sy * dd / 2, z0), trim, bevel=0.006, base=True)
    # roof: two corrugated slopes, ridge cap, gutters
    slope = (dd / 2 + 0.12) / math.cos(pitch)
    roof_m = st.mat((0.3, 0.31, 0.32) if tier < 4 else (0.55, 0.56, 0.57), name="roof", wear=0.6)
    for sy in (-1, 1):
        o = KI.corrugated(ww + 0.2, slope, (0, cy + sy * (dd / 2 + 0.12), z0 + H - 0.12 * math.tan(pitch)), 0.0, roof_m, pitch=0.25, depth=0.04)
        o.rotation_euler = (-(math.pi / 2 - pitch), 0, 0 if sy < 0 else math.pi)
        K.box((ww + 0.24, 0.1, 0.08), (0, cy + sy * (dd / 2 + 0.12), z0 + H - 0.12 * math.tan(pitch) - 0.04), trim, bevel=0.01)
    K.box((ww + 0.22, 0.22, 0.06), (0, cy, z0 + H + rise + 0.02), trim, bevel=0.01, name="ridge")
    # ridge ventilators + skylight strips
    nv = max(1, int(ww / 1.4))
    for i in range(nv):
        x = -ww / 2 + ww * (i + 0.5) / nv
        K.cyl(0.14 * s ** 0.3, 0.18, (x, cy, z0 + H + rise), M.metal("aluminum", dirt=0.6), verts=20)
        K.sphere(0.15 * s ** 0.3, (x, cy, z0 + H + rise + 0.18), M.metal("aluminum", dirt=0.6), scale=(1, 1, 0.6))
    sky = M.plastic((0.55, 0.6, 0.6), 0.25, name="skylight")
    for i in range(nv + 1):
        x = -ww / 2 + ww * (i + 0.25) / (nv + 1) + 0.2
        sl = K.box((0.35, slope * 0.55, 0.02), (x, cy - dd * 0.22, z0 + H + rise * 0.48 + 0.04), sky, bevel=0.004)
        sl.rotation_euler = (pitch, 0, 0)
    # front (-Y): roller doors, bollards, lamps
    fy = cy - dd / 2 - 0.04
    nd = max(1, int(ww / 1.6))
    dw = min(1.1 + 0.15 * s, ww / nd * 0.62)
    dh = min(H * 0.72, 1.3 + 0.25 * s)
    lamp_mat = M.emissive((1.0, 0.85, 0.6), 12.0)
    lights = []
    for i in range(nd):
        x = -ww / 2 + ww * (i + 0.5) / nd - 0.08 * ww / nd
        KI.roller_door((x, fy, z0), dw, dh, "-y")
        for sx in (-1, 1):
            K.cyl(0.05, 0.6, (x + sx * (dw / 2 + 0.2), fy - 0.25, z0 - 0.0), M.painted((0.75, 0.55, 0.02), wear=0.6, name="bollard"), verts=16)
            K.cyl(0.052, 0.06, (x + sx * (dw / 2 + 0.2), fy - 0.25, z0 + 0.4), M.plastic((0.02, 0.02, 0.02)), verts=16)
        K.box((0.16, 0.12, 0.05), (x, fy - 0.08, z0 + dh + 0.45), M.metal("dark_steel"), bevel=0.008)
        K.box((0.13, 0.1, 0.012), (x, fy - 0.08, z0 + dh + 0.42), lamp_mat, bevel=0.002)
        K.box((dw * 1.1, 0.012, 0.012), (x, fy - 0.05, z0 + 0.003), M.hazard(8), bevel=0)
        lights.append({"pos": [x, fy - 0.15, z0 + dh + 0.4], "color": [1.0, 0.85, 0.6], "energy": 0.5, "flicker": False})
    # personnel door + canopy at the right end of the front
    px = ww / 2 - 0.35
    K.box((0.42, 0.04, 1.0), (px, fy + 0.01, z0), M.painted((0.6, 0.6, 0.58) if tier != 4 else (0.04, 0.04, 0.045), name="pdoor"), bevel=0.01, base=True)
    K.box((0.6, 0.35, 0.04), (px, fy - 0.15, z0 + 1.15), trim, bevel=0.008)
    K.box((0.12, 0.08, 0.03), (px, fy - 0.1, z0 + 1.12), lamp_mat, bevel=0.003)
    _, ssock = KI.status_lamp((px + 0.3, fy - 0.03, z0 + 1.25), (0.1, 1.0, 0.25), 10.0, r=0.03, axis="-y")
    KI.plate_sign((-ww * 0.05, fy - 0.01, z0 + H * 0.86), min(ww * 0.4, 1.6), 0.28, "-y", color=(0.85, 0.85, 0.82) if tier != 4 else (0.04, 0.05, 0.06))
    # strip windows on +X + downpipes
    for i in range(max(1, int(dd / 0.9))):
        y = cy - dd / 2 + dd * (i + 0.5) / max(1, int(dd / 0.9))
        KI.window((ww / 2 + 0.03, y, z0 + H * 0.72), min(0.6, dd * 0.18), 0.35, "+x", lit=(i % 2 == 0))
    for sx in (-1, 1):
        KI.strut((sx * (ww / 2 - 0.12), fy - 0.1, z0 + 0.05), (sx * (ww / 2 - 0.12), fy - 0.1, z0 + H - 0.1), 0.035, trim, verts=12)
    # pallets with crates (front-right)
    wood = M.plastic((0.32, 0.2, 0.1), 0.8, name="pallet_wood")
    rnd = random.Random(4)
    for i in range(2 if w >= 3 else 1):
        pc = Vector((ww * 0.32 - i * 0.55, -d * 0.43 + 0.12, 0.14))
        K.box((0.48, 0.38, 0.1), pc, wood, bevel=0.01, base=True)
        cols = [(0.35, 0.22, 0.1), (0.05, 0.1, 0.25), (0.5, 0.35, 0.15)]
        K.box((0.42, 0.34, 0.3 + rnd.uniform(0, 0.15)), pc + Vector((0, 0, 0.1)), M.plastic(cols[i % 3], 0.75, name="crates"), bevel=0.02, base=True)
    top = z0 + H + rise + 0.35
    if v == "automated":
        # high-bay racking block at the back-left, rooftop HVAC units, inbound conveyor on +X
        hb = H * 1.45
        hx0, hx1 = -ww / 2, -ww / 2 + ww * 0.42
        hy0, hy1 = cy + dd * 0.02, cy + dd / 2
        K.box((hx1 - hx0, hy1 - hy0, hb), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, z0), clad, bevel=0.02, base=True, name="high_bay")
        KI.corrugated(hx1 - hx0, hb, ((hx0 + hx1) / 2, hy0 - 0.01, z0), 0.0, clad)
        KI.corrugated(hy1 - hy0, hb, (hx1 + 0.01, (hy0 + hy1) / 2, z0), math.pi / 2, clad)
        K.box((hx1 - hx0 + 0.1, hy1 - hy0 + 0.1, 0.08), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, z0 + hb), trim, bevel=0.01, base=True)
        for i in range(2):
            u = Vector((ww * (0.05 + 0.22 * i), cy + dd * 0.25, z0 + H + rise * 0.5))
            K.box((0.6, 0.45, 0.4), u, M.painted((0.6, 0.61, 0.6), wear=0.3, name="hvac"), bevel=0.02, base=True)
            fo, rot = K.fan(u + Vector((0, 0, 0.42)), r=0.16, axis="z", blades=5)
        KI.belt_conveyor((ww / 2 + 0.05, cy - dd * 0.25), (w * 0.495, cy - dd * 0.25), 0.4, z0 + 0.7, st, legs=True)
        K.box((0.08, 0.6, 0.9), (ww / 2 + 0.04, cy - dd * 0.25, z0 + 0.3), M.plastic((0.02, 0.02, 0.02), 0.8), bevel=0.004, base=True)
        top = max(top, z0 + hb + 0.2)
    return Rig(height=top, frames=1, fps=1, lights=lights)


def _supply_crate(spec, p):
    """Supply cache: banded timber shipping crate on a pallet with a steel tool chest on top and a
    small status beacon."""
    KI.begin()
    st = KI.Style(p)
    w, d = _size(spec)
    s = min(w, d)
    wood = M.plastic((0.3, 0.19, 0.09), 0.8, name="crate_wood")
    dark_wood = M.plastic((0.16, 0.1, 0.05), 0.85, name="crate_wood_dark")
    K.box((w * 0.92, d * 0.92, 0.04), (0, 0, 0), M.concrete(0.8), bevel=0.01, base=True)
    pw, pd = w * 0.82, d * 0.82
    for y in (-pd * 0.4, 0, pd * 0.4):
        K.box((pw, 0.1 * s, 0.08), (0, y, 0.04), dark_wood, bevel=0.008, base=True)
    K.box((pw, pd, 0.025), (0, 0, 0.12), wood, bevel=0.004, base=True)
    cw_, cd_, ch_ = pw * 0.94, pd * 0.94, 0.55 * s + 0.1
    z = 0.145
    K.box((cw_, cd_, ch_), (0, 0, z), wood, bevel=0.012, base=True, name="crate")
    for i in range(1, 4):
        K.box((cw_ + 0.004, cd_ + 0.004, 0.006), (0, 0, z + ch_ * i / 4), dark_wood, bevel=0, base=True)
    for sx in (-1, 1):  # corner battens
        for sy in (-1, 1):
            K.box((0.05, 0.05, ch_ + 0.01), (sx * (cw_ / 2 - 0.02), sy * (cd_ / 2 - 0.02), z), dark_wood, bevel=0.006, base=True)
    band = M.metal("steel", dirt=0.8)
    for x in (-cw_ * 0.3, cw_ * 0.3):
        K.box((0.03, cd_ + 0.012, 0.004), (x, 0, z + ch_ + 0.002), band, bevel=0)
        K.box((0.03, 0.004, ch_), (x, -cd_ / 2 - 0.003, z), band, bevel=0, base=True)
    KI.plate_sign((0.0, -cd_ / 2 - 0.005, z + ch_ * 0.6), cw_ * 0.45, ch_ * 0.25, "-y", color=(0.75, 0.55, 0.02), text=True)
    KI.plate_sign((cw_ / 2 + 0.005, 0, z + ch_ * 0.55), cd_ * 0.35, ch_ * 0.2, "+x", color=(0.8, 0.8, 0.76), text=True)
    tz = z + ch_
    K.box((cw_ * 0.5, cd_ * 0.36, 0.18 * s), (-cw_ * 0.12, cd_ * 0.1, tz), st.body(), bevel=0.012, base=True, name="tool_chest")
    K.box((cw_ * 0.18, 0.02, 0.02), (-cw_ * 0.12, cd_ * 0.1 - cd_ * 0.18 - 0.01, tz + 0.12 * s), M.metal("chrome"), bevel=0.003)
    lamp = Vector((cw_ * 0.3, -cd_ * 0.25, tz))
    KI.status_lamp(lamp, (1.0, 0.55, 0.05) if st.tier < 3 else st.glow_col, 12.0, r=0.03)
    return Rig(height=tz + 0.18 * s + 0.15, frames=1, fps=1,
               lights=[{"pos": list(lamp + Vector((0, 0, 0.06))), "color": [1.0, 0.55, 0.05], "energy": 0.3, "flicker": False}])


def _vault(spec, p):
    """Armoured vault store: reinforced concrete block with chamfered parapet, round blast door in
    a steel frame on the front, armoured vents, glowing access strips, rooftop plant."""
    KI.begin()
    st = KI.Style(p)
    w, d = _size(spec)
    s = min(w, d)
    conc = M.concrete(0.35, tint=(0.62, 0.63, 0.64) if st.tier >= 4 else (0.85, 0.83, 0.8))
    dark = st.body()
    glow = M.emissive(st.glow_col, 6.0)
    K.box((w * 0.98, d * 0.98, 0.14), (0, 0, 0), M.concrete(0.4), bevel=0.02, base=True)
    z0 = 0.14
    bw, bd = w * 0.88, d * 0.8
    cy = 0.06 * d
    H = 1.6 + 0.3 * s
    K.box((bw, bd, H), (0, cy, z0), conc, bevel=0.04, base=True, name="vault_block")
    K.box((bw + 0.1, bd + 0.1, 0.25), (0, cy, z0), conc, bevel=0.03, base=True)
    K.box((bw + 0.06, bd + 0.06, 0.2), (0, cy, z0 + H), dark, bevel=0.03, base=True, name="parapet")
    # panel joints
    for i in range(1, int(bw / 1.2)):
        x = -bw / 2 + i * bw / int(bw / 1.2)
        K.box((0.02, 0.01, H * 0.98), (x, cy - bd / 2 - 0.003, z0), M.plastic((0.05, 0.05, 0.05), 0.9), bevel=0, base=True)
    # blast door
    fy = cy - bd / 2
    dr = min(0.75, H * 0.36)
    dx = -bw * 0.12
    dz = z0 + dr + 0.12
    K.box((dr * 2.5, 0.2, dr * 2.5), (dx, fy - 0.06, dz), dark, bevel=0.03, name="door_frame")
    K.cyl(dr, 0.18, (dx, fy - 0.12, dz), M.metal("steel", rough=0.3, dirt=0.3), rot=K.AXES["-y"], verts=48, base=False, name="blast_door")
    K.torus(dr * 0.75, 0.025, (dx, fy - 0.22, dz), M.metal("dark_steel"), rot=K.AXES["-y"], segs=48)
    K.bolts(Vector((dx, fy - 0.21, dz)), dr * 0.88, 16, axis="-y", r=0.02)
    KI.handwheel((dx, fy - 0.26, dz), dr * 0.3, "-y", mat=M.metal("chrome"))
    for sx in (-1, 1):
        K.box((0.06, 0.04, dr * 2.3), (dx + sx * dr * 1.32, fy - 0.17, dz), glow, bevel=0.004)
    KI.hazard_band((dx, fy - 0.17, z0 + 0.06), dr * 2.4, 0.08)
    # vents + keypad + lamps
    KI.louvers((bw * 0.3, fy - 0.02, z0 + H * 0.7), bw * 0.2, 0.3, "-y")
    KI.louvers((bw / 2 + 0.02, cy, z0 + H * 0.7), bd * 0.25, 0.3, "+x")
    KI.cabinet((dx + dr * 1.6 + 0.2, fy - 0.12, z0), 0.0, w=0.22, d=0.1, h=1.2, mat=dark, screen_col=st.glow_col)
    K.box((bw * 0.9, 0.02, 0.04), (0, fy - 0.01, z0 + H - 0.1), glow, bevel=0.003)
    K.box((0.02, bd * 0.9, 0.04), (bw / 2 + 0.01, cy, z0 + H - 0.1), glow, bevel=0.003)
    for i in range(2):
        u = Vector((-bw * 0.2 + i * bw * 0.35, cy + bd * 0.1, z0 + H))
        K.box((0.7, 0.5, 0.45), u, M.painted((0.5, 0.51, 0.52), wear=0.2, name="plant"), bevel=0.02, base=True)
        K.fan(u + Vector((0, 0, 0.47)), r=0.17, axis="z", blades=5)
    lamp = Vector((bw / 2 - 0.2, fy + 0.2, z0 + H + 0.2))
    KI.status_lamp(lamp, (1.0, 0.08, 0.03), 12.0)
    return Rig(height=z0 + H + 0.75, frames=1, fps=1,
               lights=[{"pos": [dx, fy - 0.4, dz], "color": list(st.glow_col), "energy": 0.5, "flicker": False}])


# =========================================================================== silo
def silo(spec, p):
    """Bulk solids silo(s): corrugated galvanised bin on a braced leg frame, hopper cone with slide
    gate over a reclaim belt, caged ladder, roof rail, bucket elevator with head and spout."""
    KI.begin()
    st = KI.Style(p)
    w, d = _size(spec)
    s = min(w, d)
    L = max(w, d)
    n = max(1, int(round(L / s)))
    along_x = w >= d
    conc = st.concrete(0.4)
    KI.concrete_pad(w * 0.98, d * 0.98, 0.1, conc)
    z0 = 0.1
    galv = M.metal("aluminum" if st.tier >= 3 else "steel", rough=0.35 if st.tier >= 3 else 0.5, dirt=st.dirt * 0.8, brushed=0.2) if st.tier < 4 else st.body()
    frame = st.frame()
    r = 0.36 * s
    zs = 0.4 + 0.2 * s
    Hb = 0.8 + 0.62 * s
    cone_h = r * 0.9
    centers = []
    for i in range(n):
        f = (i + 0.5) / n - 0.5
        c = Vector((f * w * 0.9 + 0.04 * w if along_x else 0.06 * w, f * d * 0.9 if not along_x else 0.06 * d, z0))
        if n == 1:
            c = Vector((0.04 * w, 0.06 * d, z0))
        centers.append(c)
    top_z = z0 + zs + cone_h + Hb
    for c in centers:
        # legs + bracing
        for j in range(4):
            a = math.pi / 4 + j * math.pi / 2
            lp = c + Vector((math.cos(a) * r * 0.82, math.sin(a) * r * 0.82, 0))
            K.box((0.09 * s ** 0.5, 0.09 * s ** 0.5, zs + cone_h), lp, frame, bevel=0.008, base=True, name="leg")
            K.box((0.18 * s ** 0.5, 0.18 * s ** 0.5, 0.03), lp, M.metal("dark_steel"), bevel=0.005, base=True)
            b = math.pi / 4 + (j + 1) * math.pi / 2
            lq = c + Vector((math.cos(b) * r * 0.82, math.sin(b) * r * 0.82, 0))
            KI.strut(lp + Vector((0, 0, 0.15)), lq + Vector((0, 0, zs * 0.85)), 0.015, frame, verts=6)
            KI.strut(lq + Vector((0, 0, 0.15)), lp + Vector((0, 0, zs * 0.85)), 0.015, frame, verts=6)
            KI.strut(lp + Vector((0, 0, zs * 0.9)), lq + Vector((0, 0, zs * 0.9)), 0.02, frame, verts=8)
        # hopper + gate
        K.cyl(0.1 * s ** 0.5, cone_h, c + Vector((0, 0, zs)), galv, verts=48, r2=r, name="hopper")
        K.box((0.24 * s ** 0.5, 0.24 * s ** 0.5, 0.14), c + Vector((0, 0, zs - 0.14)), M.metal("dark_steel"), bevel=0.01, base=True)
        K.box((0.12, 0.3 * s ** 0.5, 0.06), c + Vector((0.18 * s ** 0.5, 0, zs - 0.1)), M.hazard(8), bevel=0.004, base=True)
        # bin with corrugation rings and vertical stiffeners
        zb = z0 + zs + cone_h
        K.cyl(r, Hb, c + Vector((0, 0, zs + cone_h)), galv, verts=64, name="bin")
        nr = int(Hb / 0.11)
        for i in range(1, nr):
            K.torus(r * 1.002, 0.012, c + Vector((0, 0, zs + cone_h + Hb * i / nr)), galv, segs=64, rsegs=6)
        for j in range(12):
            a = TAU * j / 12
            K.box((0.03, 0.03, Hb), c + Vector((math.cos(a) * r * 1.01, math.sin(a) * r * 1.01, zs + cone_h)), galv, bevel=0.004, base=True, rot=(0, 0, a))
        K.cyl(r * 1.03, r * 0.42, c + Vector((0, 0, zs + cone_h + Hb)), galv, verts=64, r2=0.14 * s ** 0.5, name="roof")
        K.cyl(0.16 * s ** 0.5, 0.18, c + Vector((0, 0, zs + cone_h + Hb + r * 0.4)), galv, verts=24)
        for j in range(3):
            a = TAU * j / 3 + 0.5
            K.cyl(0.06, 0.12, c + Vector((math.cos(a) * r * 0.55, math.sin(a) * r * 0.55, zs + cone_h + Hb + r * 0.18)), M.metal("dark_steel"), verts=12)
        arc = [c + Vector((math.cos(a) * r * 0.97, math.sin(a) * r * 0.97, top_z + 0.02)) for a in [math.radians(-170 + 20 * i) for i in range(8)]]
        K.railing(arc, 0.55, st.safety())
        KI.ladder(c + Vector((r * 0.97 + 0.04, -r * 0.2, zs + cone_h)), Hb + 0.55, rot_z=math.pi / 2, w=0.34, mat=st.safety(), cage=True)
        KI.ladder(c + Vector((r * 0.82 + 0.1, -r * 0.2, 0)), zs + cone_h, rot_z=math.pi / 2, w=0.34, mat=st.safety())
        KI.plate_sign(c + Vector((0, -r - 0.02, zs + cone_h + Hb * 0.55)), 0.4 * s ** 0.5, 0.22 * s ** 0.5, "-y",
                      color=(0.75, 0.55, 0.02) if st.tier < 3 else (0.06, 0.12, 0.3))
    # reclaim belt under the gates (along X at the silo row)
    by_ = centers[0].y if along_x else 0.06 * d
    KI.belt_conveyor((-0.48 * w, by_), (0.48 * w, by_), 0.3 * s ** 0.5, z0 + 0.42, st, legs=True) if along_x else \
        KI.belt_conveyor((0.06 * w, -0.48 * d), (0.06 * w, 0.48 * d), 0.3 * s ** 0.5, z0 + 0.42, st, legs=True)
    # bucket elevator at the back-left feeding the first silo roof
    c0 = centers[0]
    ex = Vector((c0.x - r - 0.25 * s ** 0.5, c0.y + r * 0.55, z0)) if along_x or n == 1 else Vector((c0.x - r * 0.9, c0.y + r * 0.2, z0))
    ex.x = max(-0.46 * w, ex.x)
    eh = top_z + 0.7 - z0
    em = st.body()
    K.box((0.22 * s ** 0.5, 0.36 * s ** 0.5, eh), ex, em, bevel=0.01, base=True, name="elevator_leg")
    K.box((0.3 * s ** 0.5, 0.44 * s ** 0.5, 0.36 * s ** 0.5), ex + Vector((0, 0, eh)), em, bevel=0.015, base=True, name="elevator_head")
    K.box((0.4 * s ** 0.5, 0.6 * s ** 0.5, 0.2), ex, M.metal("dark_steel"), bevel=0.01, base=True, name="boot")
    for zz in (eh * 0.3, eh * 0.6):
        K.box((0.25 * s ** 0.5, 0.39 * s ** 0.5, 0.04), ex + Vector((0, 0, zz)), frame, bevel=0.004, base=True)
    KI.motor(ex + Vector((0.0, -0.3 * s ** 0.5, eh + 0.18 * s ** 0.5)), axis="x", r=0.08 * s ** 0.5, length=0.2 * s ** 0.5,
             mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, name="motor_paint"))
    K.tube([ex + Vector((0.1 * s ** 0.5, 0, eh + 0.1)), c0 + Vector((-0.05, 0, top_z - z0 + 0.25))], 0.07 * s ** 0.5, em)
    _, sk = KI.status_lamp(ex + Vector((0, 0, eh + 0.36 * s ** 0.5)), (1.0, 0.08, 0.03), 12.0)
    KI.cabinet((0.38 * w, -0.38 * d, z0), 0.0, w=0.28, d=0.15, h=0.55, mat=st.mat((0.6, 0.6, 0.58), wear=0.5))
    _, sk2 = KI.status_lamp((0.38 * w + 0.08, -0.38 * d, z0 + 0.57), (0.1, 1.0, 0.25), 10.0, r=0.022)
    return Rig(height=max(top_z + 0.6, z0 + eh + 0.5 * s ** 0.5), frames=1, fps=1,
               lights=[{"pos": [ex.x, ex.y, z0 + eh + 0.45], "color": [1.0, 0.1, 0.05], "energy": 0.3, "flicker": False}])


# =========================================================================== conveyor hub
def conveyor_hub(spec, p):
    """Belt junction / sorter: four belt stubs meeting a powered roller turntable that turns crates
    through 90 degrees under a scanner arch with a laser line; status tower."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    frame = st.frame()
    body = st.body()
    KI.concrete_pad(w * 0.98, d * 0.98, 0.06, st.concrete(0.5))
    z0 = 0.06
    zt = z0 + 0.38 + 0.08 * s
    bw = 0.3 * k
    tr = 0.27 * k
    # turntable base
    K.box((2 * tr + 0.1, 2 * tr + 0.1, zt - z0 - 0.06), (0, 0, z0), body, bevel=0.02, base=True, name="tt_base")
    K.box((2 * tr + 0.16, 2 * tr + 0.16, 0.05), (0, 0, zt - 0.11), frame, bevel=0.008, base=True)
    KI.louvers((0, -tr - 0.062, z0 + (zt - z0) * 0.45), tr * 0.9, (zt - z0) * 0.35, "-y")
    KI.louvers((tr + 0.062, 0, z0 + (zt - z0) * 0.45), tr * 0.9, (zt - z0) * 0.35, "+x")
    tt = [K.cyl(tr, 0.05, (0, 0, zt - 0.06), M.metal("dark_steel", dirt=0.6), verts=48, name="turntable")]
    tt.append(K.torus(tr, 0.012, (0, 0, zt - 0.01), M.painted((0.75, 0.55, 0.02), name="tt_rim"), segs=48, rsegs=6))
    nrl = 7
    for i in range(nrl):
        y = -tr * 0.75 + tr * 1.5 * i / (nrl - 1)
        L = 2 * math.sqrt(max(0.01, tr * tr * 0.9 - y * y))
        tt.append(K.cyl(0.025 * k, L, (0, y, zt - 0.005), M.metal("steel", rough=0.25), rot=K.AXES["x"], verts=12, base=False))
    crate_m = M.plastic((0.3, 0.19, 0.09), 0.7, name="crate_kraft")
    cs = 0.17 * k
    tt.append(K.box((cs, cs, cs * 0.8), (0, 0, zt + 0.02), crate_m, bevel=0.012, base=True, name="crate"))
    tt.append(K.box((cs * 1.01, cs * 0.3, cs * 0.81), (0, 0, zt + 0.02), M.plastic((0.6, 0.55, 0.45), 0.6, name="tape"), bevel=0.004, base=True))
    ttp = KI.pivot((0, 0, 0), children=tt)
    an.rotate(ttp, lambda t: (math.pi / 2) * KI.smooth01((t - 0.2) / 0.6))
    # four belt stubs with moving crates (in on -X and +Y, out on +X and -Y)
    rnd = random.Random(2)

    def crate_fn(rnd_):
        c = rnd_.choice([(0.3, 0.19, 0.09), (0.1, 0.105, 0.11), (0.03, 0.07, 0.18), (0.3, 0.19, 0.09)])
        o = K.box((cs, cs * 0.85, cs * 0.7), (0, 0, 0.0), M.plastic(c, 0.7, name="crate"), bevel=0.008, base=True)
        return o
    stubs = [((-w / 2, 0), (-tr - 0.06, 0)), ((0, d / 2), (0, tr + 0.06)), ((tr + 0.06, 0), (w / 2, 0)), ((0, -tr - 0.06), (0, -d / 2))]
    for a, b in stubs:
        L = (Vector(b) - Vector(a)).length
        if L < 0.12:
            continue
        n_it = max(1, int(L / (cs * 2.2)))
        KI.belt_conveyor(a, b, bw, zt - 0.02, st, n_items=n_it, item_fn=crate_fn, anim=an, seed=rnd.randint(0, 99), legs=L > 0.5)
    # scanner arch over the turntable
    ah = zt + 0.55 * k
    for sx in (-1, 1):
        K.box((0.07, 0.07, ah - z0), (sx * (tr + 0.12), -tr - 0.08, z0), frame, bevel=0.006, base=True)
    K.box((2 * tr + 0.32, 0.12, 0.1), (0, -tr - 0.08, ah), body, bevel=0.012, base=True, name="scanner")
    laser_m, laser_s = KI.anim_emit((1.0, 0.05, 0.03), 8.0, "laser")
    K.box((2 * tr, 0.008, 0.006), (0, -tr * 0.6, zt + 0.0 + cs * 0.82), laser_m, bevel=0)
    K.box((2 * tr * 0.9, 0.02, 0.02), (0, -tr - 0.08, ah - 0.01), laser_m, bevel=0)
    an.value(laser_s, lambda t: 10.0 * KI.blink(t, 8, 0.5) + 2.0)
    sl, socks = KI.stack_light((tr + 0.12, -tr - 0.08, ah + 0.1))
    an.value(socks[2], lambda t: 7.0 if t < 0.2 or t > 0.8 else 0.4)
    an.value(socks[1], lambda t: 8.0 if 0.2 <= t <= 0.8 else 0.4)
    K.box((0.2 * k, 0.12, 0.26 * k), (-tr - 0.0, -tr - 0.16, z0 + 0.3), M.painted((0.6, 0.6, 0.58), wear=0.5, name="jbox"), bevel=0.01, base=True) if w >= 1.5 else None
    return Rig(height=ah + 0.45, frames=16, fps=12, update=an)


# =========================================================================== rail depot
def rail_depot(spec, p):
    """Rail freight terminal: ballasted track with buffer stop and signal, open hopper wagon,
    rail-mounted gantry crane shuttling a container between wagon side and the stack, control
    cabin, floodlight mast."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.6
    frame = st.frame()
    body = st.body()
    conc = st.concrete(0.4)
    K.box((w * 0.99, d * 0.99, 0.06), (0, 0, 0), conc, bevel=0.01, base=True)
    v = st.variant
    maglev = v == "maglev"
    ty = -0.18 * d if d < 5.5 else -0.26 * d
    tracks = [ty] + ([ty + 1.7] if (v == "yard" or d >= 5.5) and not maglev else [])
    zr = 0.35
    gl = M.emissive(st.glow_col, 5.0)
    for i, yy in enumerate(tracks):
        if maglev:
            K.box((w * 0.99, 0.9, 0.3), (0, yy, 0.06), M.concrete(0.5, tint=(0.75, 0.76, 0.78)), bevel=0.03, base=True, name="guideway")
            K.box((w * 0.99, 0.5, 0.06), (0, yy, 0.36), st.accent_mat() if st.tier >= 3 else M.metal("dark_steel"), bevel=0.01, base=True)
            for sy in (-1, 1):
                K.box((w * 0.99, 0.02, 0.03), (0, yy + sy * 0.455, 0.3), gl, bevel=0.002)
        else:
            KI.rail_track(-w * 0.495, w * 0.495, yy, st)
            # buffer stop (-X end)
            bx = -w * 0.46
            K.box((0.2, 1.3, 0.5), (bx, yy, 0.12), M.painted((0.6, 0.05, 0.03), wear=0.6, name="buffer_red"), bevel=0.02, base=True)
            for sy in (-1, 1):
                K.cyl(0.07, 0.25, (bx + 0.1, yy + sy * 0.4, 0.5), M.metal("chrome"), rot=K.AXES["x"], verts=16, base=True)
                K.cyl(0.12, 0.04, (bx + 0.35, yy + sy * 0.4, 0.5), M.metal("dark_steel"), rot=K.AXES["x"], verts=20, base=False)
    wl = min(w * 0.55, 3.6)
    wx = -w * 0.17
    wz = zr + 0.45
    wm = st.mat((0.25, 0.07, 0.03) if st.tier < 3 else st.paint, name="wagon_paint", wear=1.2)
    if maglev:
        # streamlined maglev freight pod hovering on the guideway
        pz = 0.48 + 0.42
        pod = st.mat((0.75, 0.76, 0.77) if st.tier >= 3 else st.paint, name="pod_skin", rust=0.0, wear=0.3)
        K.cyl(0.42, wl, (wx, ty, pz), pod, rot=K.AXES["x"], verts=40, base=False, name="pod")
        for sx in (-1, 1):
            K.sphere(0.42, (wx + sx * wl / 2, ty, pz), pod, scale=(1.6, 1, 1))
        K.box((wl * 0.9, 0.86, 0.12), (wx, ty, pz - 0.36), M.metal("dark_steel"), bevel=0.02, base=False)
        K.box((wl * 0.85, 0.01, 0.06), (wx, ty - 0.42, pz + 0.12), gl, bevel=0.002)
        hl = KI.soft_glow(st.glow_col, 3.0, rim=False, name="lev_glow", power=1.0)[0]
        K.box((wl * 0.9, 0.5, 0.02), (wx, ty, 0.44), hl, bevel=0)
    else:
        for sx in (-1, 1):  # bogies
            bc = Vector((wx + sx * wl * 0.34, ty, zr))
            K.box((0.9, 1.05, 0.18), bc + Vector((0, 0, 0.14)), M.metal("dark_steel", dirt=1.0), bevel=0.02, base=True)
            for ax in (-1, 1):
                for sy in (-1, 1):
                    K.cyl(0.21, 0.06, bc + Vector((ax * 0.3, sy * 0.5, 0.21)), M.metal("steel", dirt=0.9), rot=(math.pi / 2, 0, 0), verts=24, base=False)
        K.box((wl, 1.25, 0.12), (wx, ty, wz), M.metal("dark_steel", dirt=1.0), bevel=0.01, base=True)
        KI.frustum((wl * 0.92, 1.0), (wl, 1.4), 0.75, (wx, ty, wz + 0.12), wm, open_top=True, thick=0.04, bevel=0.01, name="wagon_body")
        for i in range(5):
            x = wx - wl / 2 + wl * (i + 0.5) / 5
            K.box((0.05, 1.44, 0.7), (x, ty, wz + 0.15), wm, bevel=0.006, base=True)
        KI.rock_pile((wx, ty, wz + 0.62), wl * 0.42, 0.6, 0.18, int(wl * 22), KI.ore_material("iron"), seed=7, rmin=0.06, rmax=0.11)
        for sx in (-1, 1):
            K.box((0.15, 1.2, 0.08), (wx + sx * (wl / 2 + 0.07), ty, wz + 0.02), M.metal("dark_steel"), bevel=0.01)
    if len(tracks) > 1:
        # tank wagon on the second track
        y2 = tracks[1]
        tl = min(w * 0.45, 3.0)
        tx = w * 0.12
        for sx in (-1, 1):
            K.box((0.9, 1.05, 0.18), (tx + sx * tl * 0.36, y2, zr + 0.14), M.metal("dark_steel", dirt=1.0), bevel=0.02, base=True)
            for ax in (-1, 1):
                for sy in (-1, 1):
                    K.cyl(0.21, 0.06, (tx + sx * tl * 0.36 + ax * 0.3, y2 + sy * 0.5, zr + 0.21), M.metal("steel", dirt=0.9), rot=(math.pi / 2, 0, 0), verts=24, base=False)
        K.box((tl, 1.1, 0.12), (tx, y2, wz), M.metal("dark_steel", dirt=1.0), bevel=0.01, base=True)
        tm = st.mat((0.06, 0.06, 0.065), name="tank_black", wear=0.8)
        K.cyl(0.6, tl - 0.4, (tx, y2, wz + 0.72), tm, rot=K.AXES["x"], verts=40, base=False, name="tank_wagon")
        for sx in (-1, 1):
            K.sphere(0.6, (tx + sx * (tl / 2 - 0.2), y2, wz + 0.72), tm, scale=(0.35, 1, 1))
        K.cyl(0.18, 0.15, (tx, y2, wz + 1.3), tm, verts=20)
        KI.plate_sign((tx, y2 - 0.61, wz + 0.72), 0.4, 0.3, "-y", color=(0.8, 0.55, 0.02), text=False)
    # container stack behind the track (+Y)
    cc = [(0.45, 0.12, 0.04), (0.05, 0.16, 0.3), (0.06, 0.25, 0.1), (0.55, 0.42, 0.06)]
    clen, cwid, chei = min(2.4, w * 0.3), 0.95, 0.95
    stack_y = tracks[-1] + 0.5 + 0.55 * d * 0.5 + 0.3
    stack_y = min(stack_y, d * 0.48 - cwid / 2)
    rnd = random.Random(3)

    def container(loc, col, name="container"):
        objs = []
        m = st.mat(col, name="cont_" + name, wear=1.1)
        objs.append(K.box((clen, cwid, chei), loc, M.plastic((0.02, 0.02, 0.02), 0.8), bevel=0.01, base=True))
        for face, fy in ((0, -cwid / 2), (1, cwid / 2)):
            o = KI.corrugated(clen - 0.08, chei - 0.06, Vector(loc) + Vector((0, fy + (0.0 if face else 0.0), 0.03)), 0.0 if face == 0 else math.pi, m, pitch=0.18, depth=0.03)
            objs.append(o)
        objs.append(K.box((clen, cwid, 0.04), Vector(loc) + Vector((0, 0, chei - 0.04)), m, bevel=0.006, base=True))
        for sx in (-1, 1):
            objs.append(K.box((0.04, cwid, chei), Vector(loc) + Vector((sx * clen / 2, 0, 0)), m, bevel=0.006, base=True))
            for sy in (-1, 1):
                for zz in (0.0, chei - 0.05):
                    objs.append(K.box((0.07, 0.07, 0.05), Vector(loc) + Vector((sx * (clen / 2 - 0.02), sy * (cwid / 2 - 0.02), zz)), M.metal("dark_steel"), bevel=0.004, base=True))
        return objs
    ncol = max(1, int(w * 0.75 / (clen + 0.15)))
    for i in range(ncol):
        x = -w * 0.4 + (clen + 0.15) * i + clen / 2
        container((x, stack_y, 0.06), cc[i % 4], f"s{i}")
        if i % 2 == 0:
            container((x, stack_y, 0.06 + chei), cc[(i + 2) % 4], f"t{i}")
    # rail-mounted gantry crane spanning track + stack (girder along Y)
    gx = w * 0.18
    gy0, gy1 = ty - 1.0, min(d * 0.48, stack_y + cwid / 2 + 0.25)
    gy0 = max(gy0, -d * 0.48)
    gh = 0.06 + 2 * chei + 0.9
    gm = st.body() if st.tier != 1 else st.mat((0.6, 0.4, 0.03), name="crane_yel")
    for yy in (gy0, gy1):
        for sx in (-1, 1):
            K.box((0.16, 0.16, gh), (gx + sx * 0.7, yy, 0.06), gm, bevel=0.012, base=True, name="crane_leg")
        K.box((1.6, 0.26, 0.22), (gx, yy, 0.06), gm, bevel=0.015, base=True, name="sill")
        for sx in (-1, 1):
            K.cyl(0.08, 0.06, (gx + sx * 0.6, yy, 0.12), M.metal("dark_steel"), rot=(0, math.pi / 2, 0), verts=16, base=False)
        KI.strut((gx - 0.7, yy, 0.3), (gx + 0.7, yy, gh * 0.7), 0.025, gm, verts=8)
    for sx in (-1, 1):
        KI.beam((gx + sx * 0.7, gy0 - 0.15, gh + 0.06), (gx + sx * 0.7, gy1 + 0.15, gh + 0.06), 0.16, 0.3, gm, name="girder")
    K.box((0.5, 0.6, 0.45), (gx + 1.0, gy1 - 0.2, gh - 0.45), M.painted((0.6, 0.6, 0.58), wear=0.4, name="cab"), bevel=0.02, base=True, name="crane_cab")
    KI.window((gx + 1.0, gy1 - 0.5 - 0.01, gh - 0.25), 0.36, 0.2, "-y")
    # trolley + spreader + hanging container (animated along Y)
    hz_ = gh - chei - 0.45
    tro = [K.box((1.55, 0.6, 0.25), (gx, 0, gh + 0.26), M.metal("dark_steel", dirt=0.7), bevel=0.015, base=True, name="trolley")]
    for sx in (-1, 1):
        for sy in (-1, 1):
            tro.append(KI.strut((gx + sx * 0.5, sy * 0.25, gh + 0.25), (gx + sx * clen * 0.4, sy * 0.3, hz_ + chei + 0.12), 0.008, M.metal("steel", dirt=0.6), verts=4))
    tro.append(K.box((clen * 0.95, cwid * 0.9, 0.1), (gx, 0, hz_ + chei + 0.02), M.painted((0.75, 0.55, 0.02), name="spreader"), bevel=0.01, base=True))
    tro += container((gx, 0, hz_), cc[3], "hang")
    trp = KI.pivot((0, 0, 0), children=tro)
    ya, yb = ty, stack_y if stack_y - ty < 3.0 else ty + 2.0

    def tro_y(t):
        return ya + (yb - ya) * (0.5 - 0.5 * math.cos(TAU * t))
    an.move(trp, lambda t: (0, tro_y(t), 0.25 * math.sin(TAU * t) ** 2))
    # control cabin front-right + signal + floodlight mast
    cx_, cy_ = w * 0.38, -d * 0.42 + 0.3
    if cy_ + 0.3 < ty - 0.75:
        K.box((0.8, 0.6, 0.9), (cx_, cy_, 0.06), M.painted((0.55, 0.56, 0.55) if st.tier < 4 else (0.7, 0.71, 0.72), wear=st.wear, grime=st.grime, name="cabin"), bevel=0.02, base=True)
        K.box((0.9, 0.7, 0.06), (cx_, cy_, 0.96), frame, bevel=0.01, base=True)
        KI.window((cx_ - 0.1, cy_ - 0.31, 0.6), 0.4, 0.25, "-y", lit=True)
        KI.window((cx_ + 0.41, cy_, 0.6), 0.35, 0.25, "+x", lit=True)
    sp = Vector((w * 0.44, ty - 0.85, 0.06))
    K.cyl(0.04, 1.4, sp, M.metal("dark_steel"), verts=12)
    K.box((0.16, 0.1, 0.36), sp + Vector((0, 0, 1.4)), M.plastic((0.02, 0.02, 0.02)), bevel=0.02, base=True)
    sig_r, sr_s = KI.anim_emit((1.0, 0.05, 0.03), 8.0, "sig_red")
    sig_g, sg_s = KI.anim_emit((0.1, 1.0, 0.3), 8.0, "sig_green")
    K.cyl(0.04, 0.02, sp + Vector((0, -0.05, 1.66)), sig_r, rot=K.AXES["-y"], verts=16, base=False)
    K.cyl(0.04, 0.02, sp + Vector((0, -0.05, 1.5)), sig_g, rot=K.AXES["-y"], verts=16, base=False)
    an.value(sr_s, lambda t: 9.0 if 0.25 < t < 0.75 else 0.3)
    an.value(sg_s, lambda t: 0.3 if 0.25 < t < 0.75 else 9.0)
    mp = Vector((-w * 0.44, d * 0.42, 0.06))
    K.cyl(0.06, 3.0 + 0.3 * s, mp, M.metal("steel", dirt=0.6), verts=12, r2=0.04)
    for i in range(3):
        KI.floodlight(mp + Vector((0.12 * (i - 1), -0.1, 3.0 + 0.3 * s)), (0.6, -0.5, -0.6), size=0.2)
    _, bk = KI.status_lamp((gx, gy1, gh + 0.36), (1.0, 0.55, 0.05), 12.0)
    an.value(bk, lambda t: 14.0 * KI.blink(t, 4, 0.4))
    return Rig(height=max(gh + 0.7, 3.5 + 0.3 * s), frames=16, fps=10, update=an,
               lights=[{"pos": [mp.x, mp.y, 3.0 + 0.3 * s], "color": [1.0, 0.95, 0.85], "energy": 1.0, "flicker": False}])


# =========================================================================== drone port
def _drone(loc, size, st, an, hover=True, phase=0.0):
    """Quadcopter: body pod, four arms, motors, spinning props over translucent blur discs."""
    body = st.mat((0.72, 0.73, 0.74) if st.tier >= 3 else (0.6, 0.4, 0.03), name="drone_body", wear=0.5)
    dark = M.plastic((0.02, 0.02, 0.025), 0.35)
    objs = []
    c = Vector((0, 0, 0))
    objs.append(K.box((size * 0.5, size * 0.36, size * 0.16), c, body, bevel=0.02 * size, name="pod"))
    objs.append(K.box((size * 0.32, size * 0.26, size * 0.1), c + Vector((0, 0, -size * 0.12)), dark, bevel=0.01 * size, name="cargo"))
    for sx in (-1, 1):
        objs.append(K.box((0.02 * size, size * 0.5, 0.02 * size), c + Vector((sx * size * 0.14, 0, -size * 0.2)), dark, bevel=0.004))
    blur = _translucent((0.05, 0.05, 0.06), 0.28)
    props = []
    led_mat, led_s = KI.anim_emit((0.1, 0.9, 1.0) if st.tier >= 3 else (1.0, 0.2, 0.05), 10.0, "drone_led")
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        tip = c + Vector((math.cos(a) * size * 0.55, math.sin(a) * size * 0.55, size * 0.03))
        objs.append(KI.strut(c, tip, 0.025 * size, dark, verts=8))
        objs.append(K.cyl(0.05 * size, 0.07 * size, tip, dark, verts=16, name="motor"))
        objs.append(K.cyl(0.36 * size, 0.004, tip + Vector((0, 0, 0.08 * size)), blur, verts=32, bevel=0, name="prop_blur"))
        objs.append(K.sphere(0.02 * size, tip + Vector((0, 0, -0.01)), led_mat, segs=8, rings=4))
        pp = KI.pivot(tip + Vector((0, 0, 0.085 * size)), name="prop")
        bl = K.box((0.7 * size, 0.05 * size, 0.006), (0, 0, 0), dark, bevel=0.002, name="blade")
        KI.group([bl], pp)
        an.spin(pp, 3.0 + 0.5 * (i % 2), axis="Z")
        props.append(pp)
        objs.append(pp)
    dp = KI.pivot(loc, name="drone")
    KI.group(objs, dp)
    if hover:
        an.move(dp, lambda t: (0.03 * size * math.sin(TAU * (t + phase)), 0.02 * size * math.cos(TAU * (t + phase)), 0.06 * size * math.sin(TAU * (2 * t + phase))))
    an.value(led_s, lambda t: 10.0 * KI.blink(t, 4, 0.3, phase))
    return dp


def drone_port(spec, p):
    """Drone port: raised landing deck with ring markings and chase-lit edge lamps, charging
    hangar with solar roof and antenna mast, windsock, one quadcopter hovering over the pad and
    one parked on a charging plate."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.7
    frame = st.frame()
    body = st.body()
    KI.concrete_pad(w * 0.98, d * 0.98, 0.06, st.concrete(0.5))
    z0 = 0.06
    zd = z0 + 0.28 + 0.05 * s
    # deck on legs
    dx0, dx1, dy0, dy1 = -0.47 * w, 0.47 * w, -0.47 * d, 0.47 * d
    K.box((dx1 - dx0, dy1 - dy0, 0.08), ((dx0 + dx1) / 2, (dy0 + dy1) / 2, zd - 0.08), M.concrete(0.5, tint=(0.55, 0.56, 0.58)), bevel=0.02, base=True, name="deck")
    K.box((dx1 - dx0 + 0.02, dy1 - dy0 + 0.02, 0.1), ((dx0 + dx1) / 2, (dy0 + dy1) / 2, zd - 0.18), frame, bevel=0.01, base=True)
    for x in (dx0 + 0.1, dx1 - 0.1):
        for y in (dy0 + 0.1, dy1 - 0.1):
            K.box((0.12, 0.12, zd - 0.18 - z0), (x, y, z0), frame, bevel=0.008, base=True)
    K.box((dx1 - dx0, 0.03, 0.03), ((dx0 + dx1) / 2, dy0 + 0.02, zd), M.hazard(6), bevel=0.003, base=True)
    K.box((0.03, dy1 - dy0, 0.03), (dx1 - 0.02, (dy0 + dy1) / 2, zd), M.hazard(6), bevel=0.003, base=True)
    # landing pad: ring + cross markings
    P = Vector((0.12 * w, -0.12 * d, zd))
    pr = 0.27 * s
    white = M.painted((0.75, 0.75, 0.72), wear=0.5, grime=0.4, name="marking")
    yel = M.painted((0.75, 0.5, 0.02), wear=0.5, grime=0.4, name="marking_y")
    KI.ring(pr, pr - 0.06 * k, 0.006, P + Vector((0, 0, 0.003)), white, segs=64, bevel=0)
    KI.ring(pr * 0.55, pr * 0.55 - 0.04 * k, 0.006, P + Vector((0, 0, 0.003)), yel, segs=48, bevel=0)
    for a in (0, math.pi / 2):
        K.box((pr * 0.8, 0.05 * k, 0.006), P + Vector((0, 0, 0.003)), white, bevel=0, rot=(0, 0, a + math.pi / 4))
    lamps = []
    nl = 12
    for i in range(nl):
        a = TAU * i / nl
        m, sk = KI.anim_emit(st.glow_col if st.tier >= 3 else (0.2, 1.0, 0.3), 6.0, "pad_lamp")
        K.cyl(0.025 * k, 0.025, P + Vector((math.cos(a) * (pr + 0.06), math.sin(a) * (pr + 0.06), 0)), m, verts=12, bevel=0.003)
        lamps.append((i, sk))

    def chase(t):
        for i, sk in lamps:
            ph = (t * 2 - i / nl) % 1.0
            sk.default_value = 1.0 + 12.0 * max(0.0, 1.0 - ph * 4)
    an.add(chase)
    # hangar / charging station (back-left)
    hx0, hx1 = -0.46 * w, -0.08 * w
    hy0, hy1 = 0.12 * d, 0.46 * d
    hh = 0.8 + 0.25 * s
    hc = Vector(((hx0 + hx1) / 2, (hy0 + hy1) / 2, zd))
    hm = st.body() if st.tier != 2 else st.mat((0.55, 0.56, 0.55), name="hangar")
    K.box((hx1 - hx0, hy1 - hy0, hh), hc, hm, bevel=0.03, base=True, name="hangar")
    K.box((hx1 - hx0 + 0.06, hy1 - hy0 + 0.06, 0.06), hc + Vector((0, 0, hh)), frame, bevel=0.01, base=True)
    KI.roller_door((hc.x - (hx1 - hx0) * 0.12, hy0 - 0.01, zd), (hx1 - hx0) * 0.5, hh * 0.68, "-y")
    for i in range(2):  # solar panels tilted to the sun (front-left)
        sp = K.box(((hx1 - hx0) * 0.44, (hy1 - hy0) * 0.8, 0.03), hc + Vector((-(hx1 - hx0) * 0.24 + i * (hx1 - hx0) * 0.48, 0, hh + 0.18)),
                   M.plastic((0.015, 0.025, 0.07), 0.12, name="pv"), bevel=0.006)
        sp.rotation_euler = (math.radians(-18), 0, 0)
    K.cyl(0.03, 1.2 * k, hc + Vector(((hx1 - hx0) * 0.38, (hy1 - hy0) * 0.35, hh)), M.metal("steel"), verts=10)
    K.cyl(0.08, 0.05, hc + Vector(((hx1 - hx0) * 0.38, (hy1 - hy0) * 0.35, hh + 1.2 * k)), M.plastic((0.8, 0.8, 0.78)), verts=20)
    _, bsk = KI.status_lamp(hc + Vector(((hx1 - hx0) * 0.38, (hy1 - hy0) * 0.35, hh + 1.25 * k)), (1.0, 0.08, 0.03), 12.0, r=0.03)
    an.value(bsk, lambda t: 14.0 * KI.blink(t, 2, 0.25))
    KI.window((hx1 + 0.02, hc.y, zd + hh * 0.6), (hy1 - hy0) * 0.4, hh * 0.25, "+x", lit=True)
    # charging plate with parked drone (right-back)
    cp = Vector((0.3 * w, 0.28 * d, zd))
    cm, cs = KI.anim_emit(st.glow_col, 3.0, "charge_ring")
    K.box((0.5 * k, 0.5 * k, 0.04), cp, M.metal("dark_steel"), bevel=0.01, base=True)
    KI.ring(0.2 * k, 0.17 * k, 0.012, cp + Vector((0, 0, 0.045)), cm, segs=32, bevel=0)
    an.value(cs, lambda t: 2.0 + 4.0 * (0.5 + 0.5 * math.sin(TAU * t)))
    _drone(cp + Vector((0, 0, 0.04 + 0.27 * 0.45 * k)), 0.45 * k, st, an, hover=False, phase=0.3)
    # windsock (front-left corner)
    wsx = Vector((-0.4 * w, -0.4 * d, zd))
    K.cyl(0.02, 0.9 * k, wsx, M.metal("steel"), verts=8)
    sock = []
    for i in range(4):
        sock.append(K.cyl(0.07 * k - i * 0.01, 0.12 * k, wsx + Vector((0.04 + i * 0.12 * k, 0, 0.88 * k - i * 0.025)), M.painted((0.85, 0.25, 0.02) if i % 2 == 0 else (0.85, 0.85, 0.82), name=f"sock{i % 2}"),
                          rot=(0, math.radians(95), 0), verts=16, bevel=0))
    sockp = KI.pivot(wsx + Vector((0, 0, 0.88 * k)), children=sock)
    an.rotate(sockp, lambda t: 0.25 * math.sin(TAU * t) + 0.08 * math.sin(TAU * 3 * t), axis="Z")
    # hovering drone over the pad
    if st.variant == "interceptor":
        for i, (dx, dy, dz) in enumerate(((0, 0, 0.75), (-0.35, 0.25, 1.15), (0.3, 0.35, 1.45))):
            _drone(P + Vector((dx * s, dy * s, dz + 0.15 * s)), 0.3 * k, st, an, hover=True, phase=0.33 * i)
    else:
        _drone(P + Vector((0, 0, 0.75 + 0.2 * s)), (0.8 if st.variant == "heavy" else 0.6) * k, st, an, hover=True)
    KI.cabinet((0.38 * w, -0.4 * d + 0.0, zd), 0.0, w=0.26, d=0.14, h=0.5, mat=st.mat((0.6, 0.6, 0.58), wear=0.4)) if w >= 2.5 else None
    return Rig(height=max(zd + 0.75 + 0.2 * s + 0.3, zd + hh + 1.35 * k), frames=16, fps=12, update=an,
               lights=[{"pos": [P.x, P.y, zd + 0.1], "color": list(st.glow_col if st.tier >= 3 else (0.2, 1.0, 0.3)), "energy": 0.5, "flicker": True}])


# =========================================================================== beacon
def beacon(spec, p):
    """Signal beacon / effect broadcaster: tubular mast with stacked radome antennas and three
    emitter rings that pulse in an upward wave, rotating lamp head, RF equipment cabinet."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.7
    frame = st.frame()
    body = st.body()
    conc = st.concrete(0.5)
    z0 = 0.12
    K.cyl(0.46 * s, z0, (0, 0, 0), conc, verts=8, bevel=0.02, name="plinth")
    K.cyl(0.44 * s, 0.03, (0, 0, z0), M.tread_plate(1.4, rust=st.tier == 1), verts=8, bevel=0.005)
    H = 1.1 + 0.7 * s
    M_ = Vector((-0.06 * s, 0.06 * s, z0 + 0.03))
    # base flange + mast
    K.cyl(0.14 * k, 0.08, M_, body, verts=24)
    K.bolts(M_ + Vector((0, 0, 0.08)), 0.11 * k, 8, r=0.012)
    K.cyl(0.06 * k, H, M_ + Vector((0, 0, 0.08)), st.steel("steel"), verts=20, r2=0.045 * k, name="mast")
    # three emitter rings that pulse upward
    rings = []
    for i in range(3):
        z = M_.z + 0.08 + H * (0.35 + 0.18 * i)
        m, sk = KI.anim_emit(st.glow_col, 6.0, "emitter_ring")
        K.cyl(0.13 * k - i * 0.01, 0.05, (M_.x, M_.y, z - 0.035), body, verts=32)
        K.torus(0.13 * k - i * 0.01, 0.022 * k, (M_.x, M_.y, z + 0.03), m, segs=40, rsegs=10)
        K.cyl(0.1 * k - i * 0.01, 0.05, (M_.x, M_.y, z + 0.025), body, verts=32)
        rings.append((i, sk))

    def pulse(t):
        for i, sk in rings:
            ph = (t * 2 - i * 0.18) % 1.0
            sk.default_value = 1.5 + 22.0 * math.exp(-((ph - 0.15) ** 2) / 0.006)
    an.add(pulse)
    # radome stack at the top + rotating lamp head
    zt = M_.z + 0.08 + H
    rad = M.plastic((0.82, 0.82, 0.78), 0.45, name="radome") if st.tier > 1 else M.plastic((0.6, 0.55, 0.45), 0.6, name="radome_old")
    K.cyl(0.07 * k, 0.32 * k, (M_.x, M_.y, zt - 0.32 * k), rad, verts=24)
    for sx in (-1, 1):
        K.cyl(0.025 * k, 0.5 * k, (M_.x + sx * 0.14 * k, M_.y, zt - 0.6 * k), rad, verts=12)
        KI.strut((M_.x, M_.y, zt - 0.45 * k), (M_.x + sx * 0.14 * k, M_.y, zt - 0.45 * k), 0.012, st.steel(), verts=6)
    K.cyl(0.09 * k, 0.04, (M_.x, M_.y, zt), M.metal("dark_steel"), verts=24)
    lens_m, lens_s = KI.anim_emit(st.glow_col, 4.0, "lens")
    head = [K.cyl(0.075 * k, 0.12 * k, (M_.x, M_.y, zt + 0.04), M.glass((0.9, 0.95, 1.0), 0.05), verts=24, name="lens_glass"),
            K.box((0.06 * k, 0.03 * k, 0.07 * k), (M_.x + 0.035 * k, M_.y, zt + 0.1 * k), lens_m, bevel=0.003),
            K.box((0.06 * k, 0.03 * k, 0.07 * k), (M_.x - 0.035 * k, M_.y, zt + 0.1 * k), lens_m, bevel=0.003),
            K.cyl(0.08 * k, 0.03, (M_.x, M_.y, zt + 0.16 * k), M.metal("dark_steel"), verts=24)]
    K.cyl(0.03 * k, 0.12 * k, (M_.x, M_.y, zt + 0.04), lens_m, verts=12, bevel=0)
    hp = KI.pivot((M_.x, M_.y, 0), children=head)
    an.spin(hp, 0.5)
    an.value(lens_s, lambda t: 6.0 + 4.0 * (0.5 + 0.5 * math.cos(TAU * 2 * t)))
    # equipment cabinet (front-right) with cable to mast
    cab_m = st.body() if st.tier != 2 else st.mat((0.6, 0.6, 0.58), name="rf_cab")
    cx, cy = 0.18 * s, -0.2 * s
    KI.cabinet((cx, cy, z0 + 0.03), 0.0, w=0.32 * k, d=0.22 * k, h=0.5 + 0.12 * s, mat=cab_m, screen_col=st.glow_col)
    for i in range(4):
        K.box((0.008, 0.06 * k, 0.32 * k), (cx + 0.16 * k + 0.004, cy - 0.06 * k + i * 0.04 * k, z0 + 0.12), M.metal("aluminum", dirt=0.4), bevel=0.002, base=True)
    KI.cable([(cx - 0.1 * k, cy + 0.11 * k, z0 + 0.4), (cx - 0.1 * k, cy + 0.15 * k, z0 + 0.06), (M_.x + 0.08 * k, M_.y - 0.05, z0 + 0.06), (M_.x + 0.06 * k, M_.y, z0 + 0.25)], 0.014)
    # grounding rods + rail
    for a in (0.6, 2.2, 3.8, 5.4):
        K.cyl(0.012, 0.25, (math.cos(a) * 0.38 * s, math.sin(a) * 0.38 * s, z0), M.metal("copper", dirt=0.8), verts=8)
    K.railing([(-0.4 * s, -0.4 * s, z0 + 0.03), (0.4 * s, -0.4 * s, z0 + 0.03)], 0.5 + 0.1 * s, st.safety()) if s >= 2 else None
    return Rig(height=zt + 0.25 * k, frames=16, fps=12, update=an,
               lights=[{"pos": [M_.x, M_.y, zt + 0.1], "color": list(st.glow_col), "energy": 1.0, "flicker": True}])


# =========================================================================== scrubber
def scrubber(spec, p):
    """Wet gas scrubber: packed absorption column with sight glasses and spray header, flanged inlet
    duct with damper, recirculation pump, reagent dosing tank, exhaust stack topped by an
    induced-draft fan (visible spinning) venting steam. variant 'precipitator': electrostatic
    precipitator casing on hoppers with roof transformer-rectifiers."""
    if str(p.get("variant", "")) == "precipitator":
        return _precipitator(spec, p)
    KI.begin()
    st = KI.Style(p, alt=p.get("tier", 1) == 3)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    frame = st.frame()
    body = st.body()
    steel = st.steel()
    KI.concrete_pad(w * 0.97, d * 0.97, 0.1, st.concrete(0.4))
    z0 = 0.1
    C = Vector((-0.14 * w, 0.14 * d, z0))
    cr = 0.24 * s
    ch = 1.2 + 0.6 * s
    shell = st.mat((0.62, 0.63, 0.6), name="frp_white") if st.tier in (2, 4) else body
    K.cyl(cr * 1.05, 0.1, C, M.concrete(0.8), verts=48)
    K.cyl(cr, ch, C + Vector((0, 0, 0.1)), shell, verts=48, name="column")
    for zz in (0.25, 0.5, 0.75):
        K.torus(cr * 1.01, 0.02, C + Vector((0, 0, 0.1 + ch * zz)), steel, segs=48)
        K.cyl(cr * 1.04, 0.03, C + Vector((0, 0, 0.1 + ch * zz - 0.015)), steel, verts=48)
    for zz in (0.35, 0.62):  # sight glasses
        g = C + Vector((cr * 0.2, -cr * 0.98, 0.1 + ch * zz))
        K.cyl(0.07 * k, 0.05, g, steel, rot=(math.pi / 2, 0, -0.2), verts=20, base=False)
        K.cyl(0.05 * k, 0.055, g, M.emissive((0.4, 0.8, 0.9), 1.2), rot=(math.pi / 2, 0, -0.2), verts=20, base=False)
    K.cyl(cr, cr * 0.5, C + Vector((0, 0, 0.1 + ch)), shell, verts=48, r2=cr * 0.45, name="transition")
    zs = 0.1 + ch + cr * 0.5
    sr = cr * 0.45
    sh = 0.5 + 0.25 * s
    K.cyl(sr, sh, C + Vector((0, 0, zs)), steel, verts=40, name="stack")
    fz = zs + sh
    K.cyl(sr * 1.25, 0.25 * k, C + Vector((0, 0, fz)), body if shell is not body else st.accent_mat(), verts=40, name="fan_housing")
    fo, rotor = K.fan(C + Vector((0, 0, fz + 0.2 * k)), r=sr * 1.1, axis="z", blades=6, mat=M.metal("aluminum", dirt=0.5))
    an.spin(rotor, 3.0 / 6.0)
    for i in range(3):
        a = TAU * i / 3
        KI.strut(C + Vector((math.cos(a) * sr * 1.2, math.sin(a) * sr * 1.2, fz + 0.12 * k)), C + Vector((math.cos(a) * sr * 0.2, math.sin(a) * sr * 0.2, fz + 0.12 * k)), 0.012, frame, verts=6)
    # spray header pipe + recirculation loop
    pm = st.mat((0.06, 0.25, 0.1) if st.tier <= 2 else (0.05, 0.15, 0.42), name="recirc")
    px = C.x + cr * 0.8
    pump = Vector((C.x + cr + 0.35 * k, C.y - cr * 0.4, z0))
    K.box((0.4 * k, 0.24 * k, 0.1), pump, frame, bevel=0.008, base=True)
    K.cyl(0.11 * k, 0.12 * k, pump + Vector((-0.08 * k, 0, 0.1 + 0.11 * k)), pm, rot=(math.pi / 2, 0, 0), verts=24, base=False, name="volute")
    KI.motor(pump + Vector((0.1 * k, 0, 0.1 + 0.1 * k)), axis="x", r=0.08 * k, length=0.2 * k, mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, name="motor_paint"))
    KI.pipe([pump + Vector((-0.08 * k, 0, 0.1 + 0.22 * k)), Vector((pump.x - 0.08 * k, pump.y, z0 + ch * 0.95)), Vector((C.x + cr + 0.02, pump.y, z0 + ch * 0.95))],
            r=0.035 * k, mat=pm)
    KI.pipe([Vector((C.x + cr * 0.7, C.y - cr * 0.7, z0 + 0.2)), Vector((pump.x - 0.3 * k, pump.y, z0 + 0.2)), Vector((pump.x - 0.2 * k, pump.y, z0 + 0.1 + 0.11 * k))],
            r=0.035 * k, mat=pm, flanges=False)
    g, needle = KI.gauge((pump.x - 0.08 * k, pump.y - 0.06, z0 + ch * 0.5), "-y", 0.04)
    an.rotate(needle, lambda t: 0.5 + 0.05 * math.sin(TAU * 3 * t))
    # inlet duct from the front-right into the column base
    dz = z0 + 0.45 + 0.1 * s
    dw_ = 0.32 * k
    duct_m = st.mat((0.3, 0.31, 0.32), name="duct", wear=0.9)
    x0 = C.x + cr * 0.6
    KI.beam((x0, C.y - 0.0, dz), (w * 0.48, C.y - 0.0, dz), dw_, dw_, duct_m, name="duct")
    for x in (x0 + 0.3, (x0 + w * 0.48) / 2, w * 0.46):
        K.box((0.04, dw_ + 0.06, dw_ + 0.06), (x, C.y, dz), frame, bevel=0.005)
    K.box((0.12, dw_ + 0.08, dw_ + 0.08), ((x0 + w * 0.48) / 2 + 0.15, C.y, dz), M.metal("dark_steel"), bevel=0.008, name="damper")
    KI.handwheel(((x0 + w * 0.48) / 2 + 0.15, C.y - dw_ / 2 - 0.08, dz), 0.06, "-y")
    for x in (x0 + 0.35, w * 0.4):
        K.box((0.06, 0.06, dz - dw_ / 2 - z0), (x, C.y, z0), frame, bevel=0.005, base=True)
    # reagent dosing tank + pump (front-left)
    tk = Vector((-0.32 * w, -0.3 * d, z0))
    K.cyl(0.16 * k, 0.45 * k, tk, M.plastic((0.75, 0.74, 0.62), 0.5, name="poly_tank"), verts=32)
    K.cyl(0.07 * k, 0.04, tk + Vector((0, 0, 0.45 * k)), M.plastic((0.05, 0.1, 0.4), 0.5), verts=20)
    KI.plate_sign(tk + Vector((0, -0.16 * k - 0.006, 0.3 * k)), 0.1 * k, 0.1 * k, "-y", color=(0.8, 0.6, 0.02), text=False)
    KI.cable(KI.sag(tk + Vector((0.1 * k, 0.1 * k, 0.4 * k)), C + Vector((-cr * 0.2, -cr * 0.98, 0.3)), 0.05, 5), 0.01, M.plastic((0.85, 0.85, 0.8), 0.5))
    KI.cabinet((0.12 * w, -0.4 * d + 0.0, z0), 0.0, w=0.3 * k, d=0.16, h=0.55 + 0.15 * s, mat=st.mat((0.6, 0.6, 0.58), wear=0.5))
    _, ls = KI.status_lamp((0.12 * w + 0.1 * k, -0.4 * d, z0 + 0.57 + 0.15 * s), (0.1, 1.0, 0.25), 10.0, r=0.025)
    an.value(ls, lambda t: 2.0 + 9.0 * KI.blink(t, 2))
    KI.ladder(C + Vector((-cr * 0.5, -cr * 0.88, 0.1)), ch, rot_z=-0.5, w=0.32, mat=st.safety(), cage=True)
    return Rig(height=C.z + fz + 0.3 * k, frames=16, fps=12, update=an,
               emitters=[{"pos": [C.x, C.y, C.z + fz + 0.35 * k], "type": "steam"}])


def _precipitator(spec, p):
    """Electrostatic precipitator: plated casing with stiffeners on legs over pyramid ash hoppers,
    inlet/outlet transition ducts, roof transformer-rectifier sets with bushings, rapper drives,
    exhaust stack with spinning ID fan."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    KI.concrete_pad(w * 0.97, d * 0.97, 0.1, st.concrete(0.4))
    z0 = 0.1
    cx, cy = -0.06 * w, 0.06 * d
    bw, bd = 0.55 * w, 0.55 * d
    zs = 0.65 + 0.15 * s
    H = 0.9 + 0.35 * s
    nh = 2
    for i in range(nh):
        hx = cx - bw / 2 + bw * (i + 0.5) / nh
        KI.frustum((0.14 * k, 0.14 * k), (bw / nh * 0.98, bd * 0.98), zs * 0.55, (hx, cy, z0 + zs * 0.45), body, bevel=0.01, name="ash_hopper")
        K.box((0.16 * k, 0.16 * k, 0.12), (hx, cy, z0 + zs * 0.45 - 0.12), M.metal("dark_steel"), bevel=0.01, base=True)
        K.cyl(0.07 * k, 0.12 * k, (hx, cy - 0.1 * k, z0 + zs * 0.45 - 0.06), M.painted((0.06, 0.16, 0.3), name="motor_paint"), rot=K.AXES["y"], verts=16, base=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.12 * k, 0.12 * k, zs), (cx + sx * bw * 0.47, cy + sy * bd * 0.47, z0), frame, bevel=0.01, base=True)
    K.box((bw, bd, H), (cx, cy, z0 + zs), body, bevel=0.02, base=True, name="esp_casing")
    for i in range(1, 6):
        x = cx - bw / 2 + bw * i / 6
        K.box((0.04, 0.05, H), (x, cy - bd / 2 - 0.02, z0 + zs), frame, bevel=0.004, base=True)
    for i in range(1, 5):
        y = cy - bd / 2 + bd * i / 5
        K.box((0.05, 0.04, H), (cx + bw / 2 + 0.02, y, z0 + zs), frame, bevel=0.004, base=True)
    K.box((bw + 0.08, bd + 0.08, 0.08), (cx, cy, z0 + zs + H), frame, bevel=0.01, base=True)
    zr = z0 + zs + H + 0.08
    for i in range(2):  # T/R sets with bushings
        tp = Vector((cx - bw * 0.22 + i * bw * 0.44, cy + bd * 0.12, zr))
        K.box((0.42 * k, 0.32 * k, 0.32 * k), tp, M.painted((0.3, 0.32, 0.3), wear=0.3, name="tr_set"), bevel=0.015, base=True)
        for j in range(3):
            K.cyl(0.03 * k, 0.04 * k, tp + Vector((0, -0.06 * k, 0.32 * k + j * 0.04 * k)), M.plastic((0.32, 0.12, 0.05), 0.25, name="porcelain"), verts=12, bevel=0.003)
    for i in range(6):  # rapper drives
        K.cyl(0.035 * k, 0.12 * k, (cx - bw * 0.4 + i * bw * 0.16, cy - bd * 0.3, zr), M.metal("dark_steel"), verts=12)
    K.railing([(cx - bw / 2, cy - bd / 2 + 0.03, zr), (cx + bw / 2, cy - bd / 2 + 0.03, zr)], 0.8, st.safety())
    KI.ladder(Vector((cx + bw / 2 + 0.1, cy - bd * 0.3, z0)), zr - z0, rot_z=math.pi / 2, w=0.34, mat=st.safety(), cage=True)
    # inlet duct from the front-left, outlet to stack at the back-right
    dz = z0 + zs + H * 0.5
    KI.frustum((H * 0.5, bd * 0.5), (H * 0.9, bd * 0.9), 0.4 * k, (cx - bw / 2 - 0.4 * k, cy, dz), body, rot=(0, math.pi / 2, 0), bevel=0.01, name="inlet_cone")
    KI.beam((cx - bw / 2 - 0.4 * k, cy, dz), (-w * 0.495, cy, dz), bd * 0.5, H * 0.5, st.mat((0.3, 0.31, 0.32), name="duct"), name="inlet_duct")
    sx_, sy_ = 0.36 * w, 0.32 * d
    sr = 0.14 * k
    KI.beam((cx + bw / 2, cy + bd * 0.2, dz), (sx_ - sr, cy + bd * 0.2, dz), 0.3 * k, 0.4 * k, st.mat((0.3, 0.31, 0.32), name="duct"))
    sh = zr + 0.6 * k
    K.cyl(sr, sh, (sx_, sy_, z0), M.metal("steel", dirt=st.dirt), verts=32, name="stack")
    K.cyl(sr * 1.3, 0.22 * k, (sx_, sy_, z0 + sh), st.accent_mat(), verts=32)
    fo, rotor = K.fan((sx_, sy_, z0 + sh + 0.18 * k), r=sr * 1.15, axis="z", blades=6)
    an.spin(rotor, 3.0 / 6.0)
    KI.cabinet((0.3 * w, -0.38 * d, z0), 0.0, w=0.32 * k, d=0.16, h=0.6 + 0.15 * s, mat=st.mat((0.6, 0.6, 0.58), wear=0.5))
    _, ls = KI.status_lamp((0.3 * w + 0.1 * k, -0.38 * d, z0 + 0.62 + 0.15 * s), (0.1, 1.0, 0.25), 10.0, r=0.025)
    an.value(ls, lambda t: 2.0 + 9.0 * KI.blink(t, 2))
    return Rig(height=z0 + sh + 0.4 * k, frames=16, fps=12, update=an,
               emitters=[{"pos": [sx_, sy_, z0 + sh + 0.4 * k], "type": "steam"}])


ARCHETYPES = KI.with_bounds({
    "storage_tank": storage_tank,
    "warehouse": warehouse,
    "silo": silo,
    "conveyor_hub": conveyor_hub,
    "rail_depot": rail_depot,
    "drone_port": drone_port,
    "beacon": beacon,
    "scrubber": scrubber,
})
