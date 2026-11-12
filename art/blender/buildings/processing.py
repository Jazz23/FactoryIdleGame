"""Processing archetypes: electric_furnace, arc_furnace, crusher, press, rolling_mill,
wire_drawer, foundry, mixer."""
import math
import random

from mathutils import Vector

import kit as K
import kit_industry as KI
import materials as M
from buildings import Rig

TAU = KI.TAU


def _size(spec):
    w, d = spec.get("size", [2, 2])
    return float(w), float(d)


def _hot(strength=8.0):
    return M.molten((1.0, 0.42, 0.08), strength, 4.0)


# =========================================================================== electric furnace
def electric_furnace(spec, p):
    """Electric chamber furnace: insulated casing with a vertical-lift door (hoist on top) that
    opens onto a glowing hearth of billets, transformer with radiators + fans, busbars, cooling
    water, charging roller table."""
    KI.begin()
    st = KI.Style(p, alt=p.get("tier", 1) == 3)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    steel = st.steel()
    KI.concrete_pad(w * 0.96, d * 0.96, 0.1, st.concrete())
    z0 = 0.1
    fx0, fx1 = -0.46 * w, 0.1 * w
    fy0, fy1 = -0.2 * d, 0.44 * d
    fw, fd = fx1 - fx0, fy1 - fy0
    fh = 0.75 + 0.42 * s
    cx = (fx0 + fx1) / 2
    cy = (fy0 + fy1) / 2
    K.box((fw + 0.06, fd + 0.06, 0.14), (cx, cy, z0), frame, bevel=0.01, base=True)
    zb = z0 + 0.14
    # opening in the -Y face
    dw = fw * 0.5
    dh = fh * 0.5
    dz0 = zb + fh * 0.18
    rec = 0.22 + 0.05 * s  # recess depth
    K.box((fw, fd - rec, fh), (cx, cy + rec / 2, zb), body, bevel=0.02, base=True, name="casing")
    side = (fw - dw) / 2
    for sx in (-1, 1):
        K.box((side, rec, fh), (cx + sx * (dw / 2 + side / 2), fy0 + rec / 2, zb), body, bevel=0.02, base=True)
    K.box((dw, rec, fh - (dz0 - zb) - dh), (cx, fy0 + rec / 2, dz0 + dh), body, bevel=0.02, base=True)
    K.box((dw, rec, dz0 - zb), (cx, fy0 + rec / 2, zb), body, bevel=0.02, base=True)
    # hot interior: refractory walls + hearth + billets
    hot_wall = M.molten((1.0, 0.35, 0.06), 2.2, 3.0)
    K.box((dw, 0.02, dh), (cx, fy0 + rec - 0.01, dz0 + dh / 2), M.molten((1.0, 0.45, 0.1), 5.0, 2.5), bevel=0)
    for sx in (-1, 1):
        K.box((0.02, rec, dh), (cx + sx * (dw / 2 - 0.01), fy0 + rec / 2, dz0 + dh / 2), hot_wall, bevel=0)
    K.box((dw, rec, 0.02), (cx, fy0 + rec / 2, dz0 + dh - 0.01), hot_wall, bevel=0)
    for i in range(3):
        K.box((0.1 * k, rec * 0.9, 0.08 * k), (cx + (i - 1) * dw * 0.3, fy0 + rec / 2, dz0 + 0.01), M.molten((1.0, 0.55, 0.15), 9.0, 5.0), bevel=0.01, base=True)
    # door frame columns + hoist
    colh = fh + dh * 0.9 + 0.1
    for sx in (-1, 1):
        K.box((0.1 * k, 0.12, colh), (cx + sx * (dw / 2 + 0.06 * k), fy0 - 0.07, zb), frame, bevel=0.01, base=True)
    K.box((dw + 0.3 * k, 0.16, 0.14), (cx, fy0 - 0.07, zb + colh), frame, bevel=0.012, base=True)
    KI.motor((cx + dw * 0.25, fy0 - 0.02, zb + colh + 0.24), axis="x", r=0.08 * k, length=0.22 * k,
             mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, grime=st.grime, name="motor_paint"))
    for sx in (-1, 1):
        K.cyl(0.07 * k, 0.05, (cx + sx * dw * 0.3, fy0 - 0.07, zb + colh + 0.07), M.metal("dark_steel"), rot=K.AXES["y"], verts=20, base=False)
    # door (lifts)
    door = [K.box((dw + 0.08, 0.1, dh + 0.08), (cx, fy0 - 0.06, dz0 + dh / 2), st.accent_mat() if st.tier != 1 else frame, bevel=0.015, name="door")]
    door.append(K.box((dw * 0.9, 0.02, dh * 0.9), (cx, fy0 - 0.115, dz0 + dh / 2), M.metal("dark_steel", dirt=0.8), bevel=0.006))
    for i in range(3):
        door.append(K.box((dw * 0.92, 0.03, 0.04), (cx, fy0 - 0.13, dz0 + dh * (0.2 + 0.3 * i)), frame, bevel=0.004))
    door.append(K.cyl(0.04 * k, 0.03, (cx, fy0 - 0.13, dz0 + dh * 0.62), M.molten((1.0, 0.5, 0.12), 10.0, 6.0), rot=K.AXES["-y"], verts=16))
    door.append(K.box((dw * 0.5, 0.012, 0.06), (cx, fy0 - 0.115, dz0 + dh * 0.35), M.hazard(10), bevel=0.002))
    for sx in (-1, 1):
        door.append(KI.strut((cx + sx * dw * 0.3, fy0 - 0.07, dz0 + dh + 0.04), (cx + sx * dw * 0.3, fy0 - 0.07, zb + colh), 0.008, M.metal("steel", dirt=0.7), verts=6))
    doorp = KI.pivot((cx, fy0, 0), name="door")
    KI.bind(door, doorp)

    def opening(t):
        if t < 0.08:
            return 0.0
        if t < 0.3:
            return KI.smooth01((t - 0.08) / 0.22)
        if t < 0.6:
            return 1.0
        if t < 0.85:
            return 1.0 - KI.smooth01((t - 0.6) / 0.25)
        return 0.0
    an.move(doorp, lambda t: (0, 0, opening(t) * dh * 0.85))
    glow = KI.point_light((cx, fy0 - 0.4, dz0 + dh * 0.4), (1.0, 0.45, 0.12), 5.0, 0.2)
    an.energy(glow, lambda t: 6.0 + 90.0 * k * opening(t) * KI.flicker(t, 0.2, 0.15))
    # casing stiffeners, bands, roof
    for zz in (zb + 0.04, zb + fh - 0.06):
        K.box((fw + 0.03, fd + 0.03, 0.06), (cx, cy, zz), frame, bevel=0.006, base=True)
    nr = max(2, int(fd / 0.4))
    for i in range(1, nr):
        K.box((0.05, 0.05, fh), (fx1 + 0.02, fy0 + fd * i / nr, zb), frame, bevel=0.006, base=True)
    K.box((fw * 0.92, fd * 0.9, 0.08), (cx, cy, zb + fh), M.plastic((0.6, 0.58, 0.54), 0.85, name="insulation"), bevel=0.02, base=True)
    nt = max(2, int(fw / 0.4))
    term = []
    for i in range(nt):
        x = fx0 + fw * (i + 0.5) / nt
        term.append(Vector((x, cy + fd * 0.12, zb + fh + 0.08)))
        K.box((0.16 * k, 0.16 * k, 0.14), term[-1], M.metal("dark_steel"), bevel=0.01, base=True)
    # exhaust stack (back-left) with steam
    ex = Vector((fx0 + 0.18 * k, fy1 - 0.15 * k, zb + fh + 0.08))
    K.cyl(0.08 * k, 0.45 * k, ex, M.metal("stainless", dirt=st.dirt), verts=24)
    K.cyl(0.1 * k, 0.04, ex + Vector((0, 0, 0.45 * k)), M.metal("dark_steel"), verts=24)
    # ---- transformer with radiators on +X
    tx0, tx1 = fx1 + 0.12, 0.46 * w
    ty0, ty1 = -0.02 * d, 0.42 * d
    th = 0.5 + 0.25 * s
    tc = Vector(((tx0 + tx1) / 2, (ty0 + ty1) / 2, z0))
    tm = st.mat((0.3, 0.32, 0.3) if st.tier < 4 else (0.6, 0.61, 0.62), name="xfmr_paint")
    K.box((tx1 - tx0 - 0.12, ty1 - ty0, th), tc + Vector((-0.06, 0, 0)), tm, bevel=0.02, base=True, name="transformer")
    K.box((tx1 - tx0 - 0.1, ty1 - ty0 + 0.02, 0.05), tc + Vector((-0.06, 0, th)), tm, bevel=0.008, base=True)
    nf = max(4, int((ty1 - ty0) / 0.07))
    for i in range(nf):
        y = ty0 + 0.04 + (ty1 - ty0 - 0.08) * i / (nf - 1)
        K.box((0.14, 0.012, th * 0.75), (tx1 - 0.08, y, z0 + th * 0.12), tm, bevel=0.003, base=True, name="fin")
    for i, yy in enumerate((0.3, 0.7)):
        fo, rot = K.fan(Vector((tx1 + 0.0, ty0 + (ty1 - ty0) * yy, z0 + th * 0.25)), r=0.1 * k, axis="x", blades=5,
                        mat=M.metal("aluminum", dirt=0.5))
        an.spin(rot, 2.0 / 5.0 + i * 1.0 / 5.0)
    bush = []
    for i in range(3):
        b0 = tc + Vector((-0.06 - 0.12 * k + i * 0.12 * k, -(ty1 - ty0) * 0.15, th + 0.05))
        for j in range(4):
            K.cyl(0.035 * k - j * 0.002, 0.04 * k, b0 + Vector((0, 0, j * 0.04 * k)), M.plastic((0.32, 0.12, 0.05), 0.25, name="porcelain"), verts=16, bevel=0.004)
            K.torus(0.045 * k, 0.008, b0 + Vector((0, 0, j * 0.04 * k + 0.02 * k)), M.plastic((0.32, 0.12, 0.05), 0.25, name="porcelain"))
        bush.append(b0 + Vector((0, 0, 0.17 * k)))
    K.cyl(0.08 * k, (tx1 - tx0) * 0.5, tc + Vector((-0.06, (ty1 - ty0) * 0.32, th + 0.2)), tm, rot=K.AXES["x"], verts=24, base=False, name="conservator")
    cu = M.metal("copper", dirt=0.6)
    for i, b0 in enumerate(bush):
        tgt = term[min(len(term) - 1, len(term) - 1 - i)]
        K.tube([b0, b0 + Vector((0, 0, 0.12)), Vector((tgt.x, tgt.y - 0.03 * i, b0.z + 0.12)), tgt + Vector((0, 0, 0.16))], 0.014 * k, cu, bend=0.06)
    # cooling water lines (blue supply / red return) along the +X face
    for j, col in enumerate(((0.03, 0.12, 0.45), (0.45, 0.05, 0.03))):
        KI.pipe([(fx1 + 0.06, fy0 + 0.1 + j * 0.08, z0 + 0.05), (fx1 + 0.06, fy0 + 0.1 + j * 0.08, zb + fh * (0.75 - j * 0.1)),
                 (fx1 + 0.03, fy0 + 0.1 + j * 0.08, zb + fh * (0.75 - j * 0.1))], r=0.022 * k, mat=st.mat(col, name="water_line"), flanges=False)
    # ---- charging roller table in front of the door
    ty_a, ty_b = -0.48 * d, fy0 - 0.14
    zt = dz0 - 0.02
    if ty_b - ty_a > 0.15:
        for sx in (-1, 1):
            K.box((0.06, ty_b - ty_a, 0.1), (cx + sx * dw * 0.45, (ty_a + ty_b) / 2, zt - 0.1), frame, bevel=0.006, base=True)
            for yy in (ty_a + 0.05, ty_b - 0.05):
                K.box((0.05, 0.05, zt - 0.1 - z0), (cx + sx * dw * 0.45, yy, z0), frame, bevel=0.005, base=True)
        nroll = max(2, int((ty_b - ty_a) / 0.14))
        rollers = []
        for i in range(nroll):
            y = ty_a + 0.05 + (ty_b - ty_a - 0.1) * i / max(1, nroll - 1)
            rollers.append(K.cyl(0.035, dw * 0.86, (cx, y, zt - 0.035), steel, rot=K.AXES["x"], verts=16, base=False))
        tray_y = (ty_a + ty_b) / 2
        K.box((dw * 0.7, (ty_b - ty_a) * 0.6, 0.03), (cx, tray_y, zt), M.metal("dark_steel", dirt=0.9), bevel=0.006, base=True)
        for i in range(3):
            K.box((0.09 * k, (ty_b - ty_a) * 0.5, 0.07 * k), (cx + (i - 1) * dw * 0.22, tray_y, zt + 0.03), M.metal("cast_iron", dirt=0.6), bevel=0.008, base=True)
    # control desk front-right
    KI.cabinet((0.3 * w, -0.38 * d, z0), 0.0, w=0.4 * k, d=0.22, h=0.6 + 0.3 * s, mat=st.mat((0.6, 0.61, 0.6), wear=0.5))
    sl, socks = KI.stack_light((0.3 * w + 0.12 * k, -0.38 * d, z0 + 0.6 + 0.3 * s + 0.03))
    an.value(socks[2], lambda t: 6.0 if opening(t) == 0 else 0.3)
    an.value(socks[1], lambda t: 7.0 * KI.blink(t, 4) if opening(t) > 0 else 0.3)
    KI.plate_sign((cx + dw / 2 + 0.25 * k, fy0 - 0.005, zb + fh * 0.7), 0.16 * k, 0.12 * k, "-y")
    KI.cable(KI.sag((0.3 * w, -0.38 * d + 0.1, z0 + 0.65 + 0.3 * s), (fx1 - 0.05, fy0 - 0.02, zb + fh * 0.85), 0.2), 0.016)
    return Rig(height=zb + colh + 0.4, frames=16, fps=10, update=an,
               lights=[{"pos": [cx, fy0 - 0.3, dz0 + dh * 0.4], "color": [1.0, 0.5, 0.15], "energy": 1.0, "flicker": True}],
               emitters=[{"pos": [ex.x, ex.y, ex.z + 0.5 * k], "type": "steam"}])


# =========================================================================== arc furnace
def arc_furnace(spec, p):
    """Electric arc furnace: tilting refractory vessel with water-cooled panel rings, domed roof,
    three graphite electrodes on regulating arms, water-cooled flexible cables to a transformer
    vault wall, fume elbow, glowing slag door and tapping spout."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    body = st.body()
    frame = st.frame()
    conc = st.concrete(0.4)
    KI.concrete_pad(w * 0.98, d * 0.98, 0.1, conc)
    # operating platform
    zpl = 0.32 + 0.06 * s
    K.box((w * 0.9, d * 0.82, zpl - 0.1), (0, 0.06 * d, 0.1), conc, bevel=0.02, base=True)
    K.box((w * 0.9, 0.04, 0.05), (0, 0.06 * d - d * 0.41, zpl - 0.05), M.hazard(6.0), bevel=0.003)
    vr = 0.26 * s
    V = Vector((-0.06 * w, -0.06 * d, zpl))
    # rockers + cradle
    for sx in (-1, 1):
        pts = [(sx * 0.0 - vr * 0.7, 0.0), (vr * 0.7, 0.0), (vr * 0.62, 0.14 * s ** 0.5), (-vr * 0.62, 0.14 * s ** 0.5)]
        K.prism([(x, z) for x, z in pts], 0.12, V + Vector((0, sx * vr * 0.55, 0)), frame, rot=(0, 0, math.pi / 2), bevel=0.02, name="rocker")
    zv = zpl + 0.14 * s ** 0.5
    hh = 0.32 * vr
    K.cyl(vr * 0.92, hh, (V.x, V.y, zv), M.metal("dark_steel", dirt=1.0), verts=48, name="hearth")
    K.cyl(vr * 0.98, 0.06, (V.x, V.y, zv + hh), frame, verts=48)
    uh = 0.42 * vr
    zu = zv + hh + 0.06
    K.cyl(vr * 0.9, uh, (V.x, V.y, zu), M.metal("dark_steel", dirt=1.0), verts=48)
    panel = st.mat((0.05, 0.22, 0.1) if st.tier <= 2 else (0.06, 0.12, 0.3) if st.tier == 3 else (0.55, 0.56, 0.57), name="panel_paint", wear=0.8)
    n_rings = max(5, int(uh / (0.07 * s ** 0.5)))
    for i in range(n_rings):
        K.torus(vr * 0.93, uh / n_rings * 0.42, (V.x, V.y, zu + uh * (i + 0.5) / n_rings), panel, segs=56, rsegs=8)
    for i in range(6):
        a = TAU * i / 6 + 0.3
        KI.strut((V.x + math.cos(a) * vr * 0.97, V.y + math.sin(a) * vr * 0.97, zu), (V.x + math.cos(a) * vr * 0.97, V.y + math.sin(a) * vr * 0.97, zu + uh),
                 0.025 * s ** 0.5, frame, verts=8)
    # arc glow gap under the roof
    arc_col = tuple(st.glow_col) if (p.get("glow") or st.variant == "plasma") else (1.0, 0.55, 0.15)
    glow_mat, glow_s = KI.anim_emit(arc_col, 14.0, "arc_gap")
    K.cyl(vr * 0.9, 0.035, (V.x, V.y, zu + uh), glow_mat, verts=48, bevel=0)
    zr = zu + uh + 0.035
    K.torus(vr * 0.95, 0.045 * s ** 0.5, (V.x, V.y, zr + 0.03), panel, segs=56, rsegs=10)
    K.sphere(vr * 0.97, (V.x, V.y, zr), panel, segs=48, rings=20, scale=(1, 1, 0.26))
    for i in range(12):
        a = TAU * i / 12
        KI.strut((V.x + math.cos(a) * vr * 0.35, V.y + math.sin(a) * vr * 0.35, zr + vr * 0.22), (V.x + math.cos(a) * vr * 0.9, V.y + math.sin(a) * vr * 0.9, zr + vr * 0.08),
                 0.018 * s ** 0.5, M.metal("steel", dirt=0.9), verts=8)
    K.cyl(vr * 0.36, 0.1 * s ** 0.5, (V.x, V.y, zr + vr * 0.2), M.plastic((0.55, 0.52, 0.48), 0.9, name="delta_refractory"), verts=32)
    zdelta = zr + vr * 0.2 + 0.1 * s ** 0.5
    # electrodes on arms (each regulates up/down)
    er = 0.07 * vr + 0.02
    eh = 1.9 * vr
    yb = V.y + vr * 1.25
    arm_z = zdelta + 0.75 * vr
    wall_y = V.y + vr * 1.25 + 0.55 * s ** 0.5
    cab = M.rubber((0.025, 0.025, 0.028))
    cu = M.metal("copper", dirt=0.7)
    arcs = []
    for i in range(3):
        a = math.radians(-90 + 120 * i) + math.radians(30)
        ex_, ey_ = V.x + math.cos(a) * vr * 0.2, V.y + math.sin(a) * vr * 0.2
        grp = []
        K.torus(er * 1.25, 0.012, (ex_, ey_, zdelta + 0.005), M.emissive(arc_col, 12.0))
        grp.append(K.cyl(er, eh, (ex_, ey_, zdelta - 0.1), M.metal("dark_steel", rough=0.75, dirt=0.4, tint=(0.55, 0.55, 0.6)), verts=24, name="electrode"))
        for j in range(1, 3):
            grp.append(K.cyl(er * 1.02, 0.02, (ex_, ey_, zdelta - 0.1 + eh * j / 3), M.metal("dark_steel"), verts=24))
        az = arm_z + (i - 1) * 0.05 * s ** 0.5
        grp.append(K.box((er * 3.2, er * 3.2, 0.2 * s ** 0.5), (ex_, ey_, az - 0.05), cu, bevel=0.012, name="clamp"))
        grp.append(KI.beam((ex_, ey_ + er * 1.4, az), (ex_, yb, az), 0.11 * s ** 0.5, 0.15 * s ** 0.5, body, name="arm"))
        grp.append(KI.beam((ex_, ey_ + er * 1.4, az + 0.1 * s ** 0.5), (ex_, yb, az + 0.1 * s ** 0.5), 0.05 * s ** 0.5, 0.04 * s ** 0.5, cu, name="bus"))
        mast_top = az + 0.15
        grp.append(K.box((0.2 * s ** 0.5, 0.2 * s ** 0.5, 0.25), (ex_, yb, az - 0.12), body, bevel=0.012, base=False))
        # flexible cables loop from arm end to the vault wall
        for c in (-1, 1):
            pts = KI.sag((ex_ + c * 0.05 * s ** 0.5, yb + 0.08, az + 0.05), (ex_ + c * 0.05 * s ** 0.5, wall_y - 0.08, az + 0.15), 0.35 * s ** 0.5, 8)
            grp.append(KI.cable(pts, 0.03 * s ** 0.5, cab, bend=0.1))
        piv = KI.pivot((ex_, ey_, 0), name=f"electrode_{i}")
        KI.bind(grp, piv)
        ph = 0.17 + 0.29 * i
        an.move(piv, lambda t, ph=ph: (0, 0, 0.035 * s ** 0.5 * (KI.wave(t, 1, ph) + 0.4 * KI.wave(t, 3, ph * 2))))
        # mast column (static guide) under the arm
        K.box((0.16 * s ** 0.5, 0.16 * s ** 0.5, az - 0.3 - zpl), (ex_, yb, zpl), frame, bevel=0.012, base=True, name="mast")
        K.box((0.24 * s ** 0.5, 0.24 * s ** 0.5, 0.1), (ex_, yb, zpl), frame, bevel=0.01, base=True)
        arcs.append((ex_, ey_))
    # vault wall with busbar terminals
    wh = arm_z + 0.35
    xs_ = [a_[0] for a_ in arcs]
    hx0, hx1 = min(xs_) - 0.45 * s ** 0.5, max(xs_) + 0.45 * s ** 0.5
    hd = 0.42 * s ** 0.5
    house = st.mat((0.2, 0.21, 0.2) if st.tier < 4 else (0.6, 0.61, 0.62), name="house_paint", wear=0.8)
    K.box((hx1 - hx0, hd, wh - 0.1), ((hx0 + hx1) / 2, wall_y + hd / 2 - 0.08, 0.1), house, bevel=0.02, base=True, name="transformer_house")
    for i in range(3):
        K.box((0.3 * s ** 0.5, 0.06, 0.3 * s ** 0.5), (arcs[i][0], wall_y - 0.1, arm_z + 0.15), cu, bevel=0.01)
    K.box((hx1 - hx0 + 0.06, hd + 0.06, 0.06), ((hx0 + hx1) / 2, wall_y + hd / 2 - 0.08, wh), frame, bevel=0.01, base=True)
    KI.louvers((hx1 + 0.012, wall_y + hd * 0.3, wh * 0.45), hd * 0.5, wh * 0.3, "+x")
    KI.plate_sign((hx1 - 0.25, wall_y - 0.085, wh * 0.4), 0.22, 0.16, "-y", color=(0.8, 0.6, 0.03))
    # fume elbow from the 4th hole
    fa = math.radians(60)
    fh = Vector((V.x + math.cos(fa) * vr * 0.55, V.y + math.sin(fa) * vr * 0.55, zr + vr * 0.15))
    dr = 0.09 * s ** 0.5
    K.tube([fh, fh + Vector((0, 0, 0.3 * s ** 0.5)), Vector((0.36 * w, fh.y + 0.25, fh.z + 0.3 * s ** 0.5)), Vector((0.36 * w, 0.49 * d, fh.z + 0.3 * s ** 0.5))],
           dr, st.mat((0.05, 0.05, 0.052), name="duct_paint", wear=1.2), bend=0.25 * s ** 0.5)
    K.cyl(dr * 1.3, 0.12, fh - Vector((0, 0, 0.06)), M.metal("dark_steel"), verts=24)
    # slag door (-Y) and tapping spout (+X)
    sd = Vector((V.x, V.y - vr * 0.92, zu + uh * 0.3))
    sd_mat, sd_s = KI.anim_emit((1.0, 0.45, 0.08), 12.0, "slag_door")
    K.box((vr * 0.55, 0.12, uh * 0.55), sd, frame, bevel=0.015, base=True)
    K.box((vr * 0.4, 0.13, uh * 0.38), sd + Vector((0, -0.005, uh * 0.05)), sd_mat, bevel=0.008, base=True)
    K.box((vr * 0.5, 0.25, 0.04), sd + Vector((0, -0.12, -0.03)), M.metal("cast_iron", dirt=1.0), bevel=0.008, base=True)
    sp = Vector((V.x + vr * 0.95, V.y + vr * 0.1, zv + hh * 0.7))
    K.prism([(-0.06 * s ** 0.5, 0), (0.06 * s ** 0.5, 0), (0.08 * s ** 0.5, 0.08 * s ** 0.5), (-0.08 * s ** 0.5, 0.08 * s ** 0.5)], vr * 0.45,
            sp + Vector((vr * 0.15, 0, 0)), M.metal("cast_iron", dirt=1.0), rot=(0, 0, math.pi / 2), bevel=0.01, name="spout")
    K.box((vr * 0.3, 0.05 * s ** 0.5, 0.02), sp + Vector((vr * 0.18, 0, 0.065 * s ** 0.5)), M.molten((1.0, 0.45, 0.08), 6.0, 5.0), bevel=0.004)
    # railing along the platform front + stairs
    K.railing([(-0.45 * w, 0.06 * d - 0.39 * d, zpl), (0.45 * w, 0.06 * d - 0.39 * d, zpl)], 0.9, st.safety())
    KI.cabinet((0.36 * w, -0.24 * d, zpl), 0.0, w=0.42, d=0.24, h=0.9, mat=st.mat((0.6, 0.6, 0.58), wear=0.6))
    light = KI.point_light((V.x, V.y, zdelta + 0.25), arc_col, 150.0 * s, 0.2)
    sdl = KI.point_light(sd + Vector((0, -0.35, uh * 0.2)), (1.0, 0.45, 0.1), 30.0 * s, 0.15)
    rnd = random.Random(5)
    fl = [rnd.random() for _ in range(64)]

    def flick(t):
        i = int(t * 16) % 16
        f = 0.55 + 0.45 * fl[i] * (0.6 + 0.4 * fl[i + 16])
        glow_s.default_value = 10.0 + 14.0 * f
        sd_s.default_value = 8.0 + 8.0 * fl[i + 32]
        light.energy = 150.0 * s * f
        sdl.energy = 30.0 * s * (0.6 + 0.4 * fl[i + 32])
    an.add(flick)
    top = max(arm_z + 0.6 + 0.1, zdelta - 0.1 + eh + 0.1)
    return Rig(height=top, frames=16, fps=12, update=an,
               lights=[{"pos": [V.x, V.y, zdelta + 0.3], "color": [1.0, 0.65, 0.3], "energy": 1.5, "flicker": True},
                       {"pos": [sd.x, sd.y - 0.3, sd.z], "color": [1.0, 0.45, 0.1], "energy": 0.8, "flicker": True}],
               emitters=[{"pos": [V.x, V.y, zdelta + 0.1], "type": "sparks"},
                         {"pos": [sd.x, sd.y - 0.1, sd.z + 0.1], "type": "sparks"},
                         {"pos": [fh.x, fh.y, fh.z + 0.1], "type": "smoke"}])


# =========================================================================== crusher
def crusher(spec, p):
    """Single-toggle jaw crusher on concrete piers: ribbed side plates, twin flywheels (one a
    V-belt sheave driven by a motor on a slide base), eccentric pitman, feed hopper with rock,
    discharge belt carrying gravel away. variants: 'cone' (cone crusher), 'mill' (ball mill =
    rotary drum), 'recycler' (scrap in the hopper)."""
    v = str(p.get("variant", ""))
    if v == "mill":
        return mixer(spec, p)
    if v == "cone":
        return _cone_crusher(spec, p)
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    conc = st.concrete(0.4)
    rockm = M.concrete(2.0, tint=(0.7, 0.66, 0.6))
    KI.concrete_pad(w * 0.96, d * 0.96, 0.1, conc)
    C = Vector((-0.08 * w, 0.1 * d, 0))
    fw_ = 0.46 * w
    fd_ = 0.34 * d
    zf = 0.32 + 0.12 * s
    fh_ = 0.42 + 0.3 * s
    # piers
    for sy in (-1, 1):
        K.box((fw_ * 1.05, 0.18 * k, zf - 0.1), (C.x, C.y + sy * (fd_ / 2 - 0.02), 0.1), conc, bevel=0.02, base=True)
    # side plates with ribs
    pt = 0.07 * k
    for sy in (-1, 1):
        prof = [(-fw_ / 2, 0), (fw_ / 2, 0), (fw_ / 2, fh_ * 0.9), (fw_ * 0.3, fh_), (-fw_ / 2, fh_)]
        K.prism(prof, pt, (C.x, C.y + sy * fd_ / 2, zf), body, bevel=0.012, name="side_plate")
        for i in range(4):
            x = C.x - fw_ / 2 + fw_ * (i + 0.5) / 4
            K.box((0.05 * k, 0.06 * k, fh_ * (0.75 if i < 3 else 0.62)), (x, C.y + sy * (fd_ / 2 + pt / 2 + 0.03 * k), zf), body, bevel=0.008, base=True)
        K.box((fw_ * 1.02, 0.07 * k, 0.06 * k), (C.x, C.y + sy * (fd_ / 2 + pt / 2 + 0.03 * k), zf), frame, bevel=0.008, base=True)
    # fixed jaw (front) + toggle housing (back)
    K.box((0.18 * k, fd_, fh_ * 0.88), (C.x + fw_ / 2 - 0.09 * k, C.y, zf), body, bevel=0.015, base=True, name="fixed_jaw")
    K.box((0.2 * k, fd_, fh_ * 0.5), (C.x - fw_ / 2 + 0.1 * k, C.y, zf), body, bevel=0.015, base=True, name="toggle_block")
    for i in range(3):
        KI.strut((C.x - fw_ / 2 - 0.02, C.y - fd_ * 0.3 + i * fd_ * 0.3, zf + fh_ * 0.25), (C.x - fw_ / 2 - 0.28 * k, C.y - fd_ * 0.3 + i * fd_ * 0.3, zf + fh_ * 0.25),
                 0.022 * k, M.metal("chrome"), verts=12)
    K.box((0.06, fd_ * 0.9, 0.12 * k), (C.x - fw_ / 2 - 0.3 * k, C.y, zf + fh_ * 0.25), frame, bevel=0.008)
    # hopper with rock
    hz = zf + fh_
    KI.frustum((fw_ * 0.8, fd_ * 0.92), (fw_ * 1.25, fd_ * 1.5), 0.28 * k, (C.x + fw_ * 0.08, C.y, hz), body, open_top=True, thick=0.03)
    if v == "recycler":
        scrap = M.rusty(1.5)
        KI.rock_pile((C.x + fw_ * 0.08, C.y, hz + 0.05 * k), fw_ * 0.45, fd_ * 0.55, 0.12 * k, int(18 * k), scrap, seed=3, rmin=0.04 * k, rmax=0.08 * k)
        rr_ = random.Random(5)
        for i in range(6):
            K.box((rr_.uniform(0.2, 0.4) * k, 0.03 * k, 0.05 * k), (C.x + fw_ * 0.08 + rr_.uniform(-0.2, 0.2) * fw_, C.y + rr_.uniform(-0.3, 0.3) * fd_, hz + 0.18 * k),
                  M.metal("iron", dirt=1.0), bevel=0.004, rot=(rr_.uniform(-0.4, 0.4), rr_.uniform(-0.3, 0.3), rr_.uniform(0, 3)))
    else:
        KI.rock_pile((C.x + fw_ * 0.08, C.y, hz + 0.05 * k), fw_ * 0.45, fd_ * 0.55, 0.16 * k, int(30 * k), rockm, seed=3, rmin=0.04 * k, rmax=0.09 * k)
    K.box((fw_ * 1.3, 0.05, 0.05), (C.x + fw_ * 0.08, C.y - fd_ * 0.75, hz + 0.28 * k), M.hazard(8), bevel=0.004)
    # eccentric shaft, pitman, flywheels
    sx_ = C.x - fw_ * 0.18
    sz = zf + fh_ * 0.86
    R = 0.3 * s ** 0.9
    ww = 0.08 + 0.04 * s
    shaft_len = fd_ + 2 * (pt + 0.12 + ww)
    K.cyl(0.05 * k, shaft_len, (sx_, C.y, sz), M.metal("steel"), rot=(math.pi / 2, 0, 0), verts=16, base=False)
    for sy in (-1, 1):
        K.box((0.2 * k, 0.12, 0.16 * k), (sx_, C.y + sy * (fd_ / 2 + pt / 2 + 0.07), sz - 0.04 * k), M.metal("dark_steel"), bevel=0.012)
    pit = [K.box((0.32 * k, fd_ * 0.8, 0.24 * k), (sx_, C.y, sz), M.metal("cast_iron", dirt=1.0), bevel=0.02, name="pitman")]
    pit.append(K.cyl(0.09 * k, fd_ * 0.82, (sx_, C.y, sz), M.metal("dark_steel"), rot=(math.pi / 2, 0, 0), verts=24, base=False))
    pit.append(K.box((0.12 * k, fd_ * 0.7, fh_ * 0.5), (sx_ + 0.12 * k, C.y, sz - fh_ * 0.45), M.metal("cast_iron", dirt=1.0), bevel=0.015))
    pp = KI.pivot((sx_, C.y, sz), name="pitman")
    KI.bind(pit, pp)
    ecc = 0.025 * k
    an.move(pp, lambda t: (ecc * math.cos(TAU * t), 0, ecc * math.sin(TAU * t)))
    wheels = []
    yf = C.y - (fd_ / 2 + pt + 0.12 + ww / 2)
    sheave = KI.spoked_wheel((sx_, yf, sz), R, ww, spokes=6, mat=st.accent_mat() if st.tier != 1 else M.metal("cast_iron"),
                             rot=(math.pi / 2, 0, 0), rim=0.16, grooves=4)
    yb_ = C.y + (fd_ / 2 + pt + 0.12 + ww / 2)
    fly = KI.spoked_wheel((sx_, yb_, sz), R, ww * 1.4, spokes=6, mat=st.accent_mat() if st.tier != 1 else M.metal("cast_iron"),
                          rot=(math.pi / 2, 0, 0), rim=0.22)
    for objs, yy in ((sheave, yf), (fly, yb_)):
        objs.append(K.box((R * 0.25, 0.012, R * 0.08), (sx_ + R * 0.55, yy - ww * 0.72, sz), M.painted((0.85, 0.85, 0.82), name="mark"), bevel=0.002))
        wp = KI.pivot((sx_, yy, sz), name="wheel")
        KI.bind(objs, wp)
        an.spin(wp, 1.0, axis="Y")
    # motor on slide base + V-belts
    mz = 0.38 + 0.06 * s
    mx = sx_ + R * 1.25 + 0.15
    mr = 0.13 * k
    ml = 0.4 * k
    my = yf - 0.06 - ml / 2
    K.box((ml * 1.2, ml * 1.1, mz - mr - 0.1), (mx, my + 0.05, 0.1), frame, bevel=0.01, base=True)
    KI.motor((mx, my, mz), axis="y", r=mr, length=ml, mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, grime=st.grime, name="motor_paint"))
    pr = 0.07 * k
    pul = K.cyl(pr, ww, (mx, yf, mz), M.metal("cast_iron"), rot=(math.pi / 2, 0, 0), verts=24, base=False)
    pulp = KI.pivot((mx, yf, mz), children=[pul])
    an.spin(pulp, R / pr / 4, axis="Y")
    a_c = Vector((sx_, sz))
    b_c = Vector((mx, mz))
    dvec = (b_c - a_c)
    L = dvec.length
    ang = math.atan2(dvec.y, dvec.x)
    beta = math.asin((R - pr) / L)
    belt = M.rubber((0.02, 0.02, 0.022))
    for sgn in (-1, 1):
        nrm = ang + sgn * (math.pi / 2 + beta)
        p1 = a_c + Vector((math.cos(nrm), math.sin(nrm))) * R * 0.92
        p2 = b_c + Vector((math.cos(nrm), math.sin(nrm))) * pr
        for g in range(3):
            y = yf - ww * 0.3 + g * ww * 0.3
            KI.strut((p1.x, y, p1.y), (p2.x, y, p2.y), 0.012, belt, verts=6)
    # discharge belt under the crusher, out to +X
    KI.belt_conveyor((C.x - fw_ * 0.35, C.y), (w * 0.5, C.y), 0.3 * k, zf - 0.06, st, n_items=max(6, int(w * 3)),
                     item_mat=rockm, anim=an, seed=21, legs=False,
                     item_fn=lambda rnd: KI.rock((0, 0, 0), rnd.uniform(0.03, 0.05) * k, rockm, seed=rnd.randint(0, 999)))
    for xx in (C.x + fw_ * 0.75, w * 0.46):
        if xx < w * 0.47:
            for sy in (-1, 1):
                K.box((0.05, 0.05, zf - 0.2), (xx, C.y + sy * 0.18 * k, 0.1), frame, bevel=0.004, base=True)
    # ladder + control box
    KI.cabinet((-0.36 * w, -0.36 * d, 0.1), 0.0, w=0.3 * k, d=0.18, h=0.5 + 0.2 * s, mat=st.mat((0.6, 0.6, 0.58), wear=0.6))
    _, ls = KI.status_lamp((-0.36 * w + 0.08, -0.36 * d, 0.1 + 0.5 + 0.2 * s), (0.1, 1.0, 0.25), 10.0, r=0.025)
    an.value(ls, lambda t: 2 + 9 * KI.blink(t, 2))
    KI.rock_pile((w * 0.36, -0.3 * d, 0.1), 0.25 * k, 0.2 * k, 0.12 * k, int(14 * k), rockm, seed=9, rmin=0.03 * k, rmax=0.06 * k)
    return Rig(height=hz + 0.3 * k + 0.2, frames=16, fps=12, update=an,
               emitters=[{"pos": [C.x + fw_ * 0.08, C.y, hz + 0.3 * k], "type": "smoke"}])


def _cone_crusher(spec, p):
    """Cone crusher: bolted bottom/top shells on a steel stand, spider cap and round feed hopper,
    ring of hydraulic clearing cylinders, V-belt countershaft drive, discharge belt."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    rockm = M.concrete(2.0, tint=(0.7, 0.66, 0.6))
    KI.concrete_pad(w * 0.96, d * 0.96, 0.1, st.concrete(0.4))
    C = Vector((-0.08 * w, 0.12 * d, 0.1))
    r = 0.22 * s
    zs = 0.45 + 0.12 * s
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.14 * k, 0.14 * k, zs - 0.1), C + Vector((sx * r * 0.8, sy * r * 0.8, 0)), frame, bevel=0.01, base=True)
    K.box((2 * r * 1.05, 2 * r * 1.05, 0.12), C + Vector((0, 0, zs - 0.12)), frame, bevel=0.012, base=True)
    z = C.z + zs - 0.1
    K.cyl(r, 0.32 * s ** 0.8, (C.x, C.y, z), body, verts=48, name="bottom_shell")
    K.cyl(r * 1.1, 0.06, (C.x, C.y, z + 0.32 * s ** 0.8), body, verts=48)
    K.bolts(Vector((C.x, C.y, z + 0.32 * s ** 0.8 + 0.06)), r * 1.04, 20, r=0.015)
    z2 = z + 0.38 * s ** 0.8
    K.cyl(r * 0.92, 0.26 * s ** 0.8, (C.x, C.y, z2), body, verts=48, r2=r * 0.7, name="top_shell")
    for i in range(6):
        a_ = TAU * i / 6 + 0.3
        q = Vector((C.x + math.cos(a_) * r * 1.02, C.y + math.sin(a_) * r * 1.02, z + 0.04))
        K.cyl(0.035 * k, 0.24 * s ** 0.8, q, st.accent_mat() if st.tier != 1 else M.metal("dark_steel"), verts=16)
        K.cyl(0.015 * k, 0.12 * s ** 0.8, q + Vector((0, 0, 0.24 * s ** 0.8)), M.metal("chrome"), verts=10)
    z3 = z2 + 0.26 * s ** 0.8
    for a_ in (0, math.pi / 2):
        K.box((2 * r * 0.75, 0.12 * k, 0.1 * k), (C.x, C.y, z3), body, bevel=0.012, rot=(0, 0, a_ + math.pi / 4), name="spider")
    K.cyl(0.1 * k, 0.12 * k, (C.x, C.y, z3), M.metal("dark_steel"), verts=24)
    K.cyl(r * 0.55, 0.3 * k, (C.x, C.y, z3 + 0.04), body, verts=40, r2=r * 0.9, name="feed_hopper")
    KI.rock_pile((C.x, C.y, z3 + 0.26 * k), r * 0.7, r * 0.7, 0.08 * k, int(24 * k), rockm, seed=4, rmin=0.03 * k, rmax=0.06 * k)
    # countershaft + sheave toward -Y, motor in front
    ml = 0.32 * k
    yh = max(C.y - r - 0.12, -0.5 * d + ml + 0.1)
    K.box((0.18 * k, (C.y - r) - yh + 0.1, 0.18 * k), (C.x, (C.y - r + yh) / 2, z + 0.1 * s ** 0.8), body, bevel=0.012, name="countershaft_housing")
    R = 0.2 * k
    sh = KI.spoked_wheel((C.x, yh - 0.06, z + 0.1 * s ** 0.8), R, 0.1 * k, spokes=5, mat=st.accent_mat() if st.tier != 1 else M.metal("cast_iron"), rot=(math.pi / 2, 0, 0), grooves=4)
    sp_ = KI.pivot((C.x, yh - 0.06, z + 0.1 * s ** 0.8), children=sh)
    an.spin(sp_, 2.0 / 5.0, axis="Y")
    mxp = min(C.x + R + 0.45 * k, 0.5 * w - 0.14 * k - 0.05)
    mzp = 0.1 + 0.12 * k + 0.1
    KI.motor((mxp, yh - 0.06 - ml / 2, mzp), axis="y", r=0.11 * k, length=ml, mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, name="motor_paint"))
    K.box((0.32 * k, ml * 1.1, mzp - 0.11 * k - 0.1), (mxp, yh - 0.06 - ml / 2, 0.1), frame, bevel=0.01, base=True)
    belt = M.rubber((0.02, 0.02, 0.022))
    for g in range(3):
        y = yh - 0.06 - 0.03 * k + g * 0.03 * k
        KI.strut((C.x, y, z + 0.1 * s ** 0.8 + R * 0.95), (mxp, y, mzp + 0.07 * k), 0.012, belt, verts=6)
        KI.strut((C.x, y, z + 0.1 * s ** 0.8 - R * 0.95), (mxp, y, mzp - 0.07 * k), 0.012, belt, verts=6)
    KI.belt_conveyor((C.x, C.y), (w * 0.5, C.y), 0.3 * k, C.z + zs - 0.25, st, n_items=max(6, int(w * 3)), anim=an, seed=21, legs=False,
                     item_fn=lambda rnd: KI.rock((0, 0, 0), rnd.uniform(0.03, 0.05) * k, rockm, seed=rnd.randint(0, 999)))
    KI.cabinet((-0.38 * w, -0.36 * d, 0.1), 0.0, w=0.3 * k, d=0.18, h=0.5 + 0.2 * s, mat=st.mat((0.6, 0.6, 0.58), wear=0.6))
    _, ls = KI.status_lamp((-0.38 * w + 0.08, -0.36 * d, 0.1 + 0.5 + 0.2 * s), (0.1, 1.0, 0.25), 10.0, r=0.025)
    an.value(ls, lambda t: 2 + 9 * KI.blink(t, 2))
    return Rig(height=z3 + 0.35 * k + 0.2, frames=16, fps=12, update=an,
               emitters=[{"pos": [C.x, C.y, z3 + 0.4 * k], "type": "smoke"}])


# =========================================================================== press
def press(spec, p):
    """Straight-side mechanical stamping press: columns + tie rods, crown with flywheel and
    belt-drive motor, crank-driven slide with die set, light curtains, two-hand control stand."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    KI.concrete_pad(w * 0.96, d * 0.96, 0.1, st.concrete())
    z0 = 0.1
    P = Vector((-0.06 * w, 0.06 * d, z0))
    px = 0.27 * w
    pd = 0.46 * d
    cw = 0.17 * k
    zb = z0 + 0.42 + 0.12 * s
    H = 1.1 + 0.6 * s
    crown_h = 0.32 * k
    zc = z0 + H - crown_h
    # bed
    K.box((2 * px + cw, pd, zb - z0), P, body, bevel=0.02, base=True, name="bed")
    K.box((2 * px + cw + 0.06, pd + 0.06, 0.08), P, frame, bevel=0.01, base=True)
    # columns
    for sx in (-1, 1):
        K.box((cw, pd * 0.9, zc - zb), P + Vector((sx * px, 0, zb - z0)), body, bevel=0.02, base=True, name="column")
        K.box((0.03, pd * 0.5, zc - zb - 0.1), P + Vector((sx * (px - cw / 2 - 0.015), 0, zb - z0 + 0.05)), M.metal("steel", rough=0.25), bevel=0.004, base=True)
        K.box((cw * 0.6, 0.02, (zc - zb) * 0.6), P + Vector((sx * px, -pd * 0.45 - 0.01, zb - z0 + (zc - zb) * 0.2)), frame, bevel=0.004, base=True)
    # crown
    K.box((2 * px + cw + 0.1, pd + 0.08, crown_h), P + Vector((0, 0, zc - z0)), body, bevel=0.025, base=True, name="crown")
    K.box((2 * px + cw + 0.14, pd + 0.12, 0.05), P + Vector((0, 0, zc - z0 + crown_h * 0.15)), frame, bevel=0.008, base=True)
    # tie rods (chrome) with nuts
    for sx in (-1, 1):
        for sy in (-1, 1):
            tp = P + Vector((sx * (px + cw * 0.55), sy * pd * 0.45, 0))
            K.cyl(0.03 * k, H + 0.08, tp + Vector((0, 0, 0.02)), M.metal("chrome"), verts=16, name="tie_rod")
            for zz in (zb - z0 - 0.02, H + 0.02):
                K.cyl(0.05 * k, 0.07, tp + Vector((0, 0, zz)), M.metal("dark_steel"), verts=6, bevel=0.004)
    # bolster + lower die + blank
    K.box((2 * px - cw * 0.9, pd * 0.8, 0.07), P + Vector((0, 0, zb - z0)), M.metal("dark_steel", dirt=0.8), bevel=0.006, base=True)
    ld_h = 0.14 * k
    K.box((2 * px * 0.65, pd * 0.6, ld_h), P + Vector((0, 0, zb - z0 + 0.07)), M.metal("steel", dirt=0.7), bevel=0.01, base=True, name="lower_die")
    K.box((2 * px * 0.55, pd * 0.5, 0.012), P + Vector((0, 0, zb - z0 + 0.07 + ld_h)), M.metal("stainless", dirt=0.2), bevel=0.002, base=True, name="blank")
    die_top = zb + 0.07 + ld_h + 0.012
    stroke = 0.22 * k
    gap = 0.03
    # slide (moves)
    sh = 0.32 * k
    ud_h = 0.14 * k
    slide_bottom_bdc = die_top + gap
    sb_tdc = slide_bottom_bdc + stroke
    slide = [K.box((2 * px - cw - 0.02, pd * 0.8, sh), (P.x, P.y, sb_tdc + ud_h), st.accent_mat() if st.tier != 2 else frame, bevel=0.02, base=True, name="slide")]
    slide.append(K.box((2 * px * 0.65, pd * 0.6, ud_h), (P.x, P.y, sb_tdc), M.metal("steel", dirt=0.7), bevel=0.01, base=True, name="upper_die"))
    slide.append(K.box((2 * px - cw - 0.04, 0.02, 0.06), (P.x, P.y - pd * 0.4 - 0.01, sb_tdc + ud_h + sh * 0.2), M.hazard(8), bevel=0.002))
    conrods = []
    for sx in (-0.5, 0.5):
        conrods.append(K.box((0.1 * k, 0.12 * k, zc - (sb_tdc + ud_h + sh) + stroke + 0.05), (P.x + sx * px, P.y, sb_tdc + ud_h + sh - 0.02), M.metal("cast_iron"), bevel=0.012, base=True))
    slp = KI.pivot((P.x, P.y, 0), name="slide")
    KI.bind(slide + conrods, slp)

    def dz(t):
        return -stroke * (1 - math.cos(TAU * t)) / 2
    an.move(slp, lambda t: (0, 0, dz(t)))
    hyd = st.variant == "hydraulic"
    if hyd:
        # hydraulic forge press: main + side cylinders on the crown, power unit beside, hot billet
        for xx, rr in ((0.0, 0.11 * k), (-px * 0.55, 0.06 * k), (px * 0.55, 0.06 * k)):
            K.cyl(rr, 0.3 * k, (P.x + xx, P.y, zc + crown_h), M.metal("dark_steel", dirt=st.dirt), verts=32, name="main_cylinder")
            K.cyl(rr * 1.18, 0.05, (P.x + xx, P.y, zc + crown_h + 0.3 * k), st.accent_mat(), verts=32)
            K.bolts(Vector((P.x + xx, P.y, zc + crown_h + 0.3 * k + 0.05)), rr * 0.85, 8, r=0.012)
        hpu = Vector((P.x + px + cw / 2 + 0.35 * k, P.y + pd * 0.15, z0))
        hpu.x = min(hpu.x, 0.42 * w)
        K.box((0.5 * k, 0.7 * k, 0.45 * k), hpu, M.painted((0.06, 0.16, 0.3), wear=st.wear, name="hpu_tank"), bevel=0.015, base=True, name="hpu")
        KI.motor(hpu + Vector((0, -0.1 * k, 0.45 * k + 0.1 * k)), axis="y", r=0.09 * k, length=0.28 * k,
                 mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, name="motor_paint"))
        for i in range(3):
            KI.bellows_hose([hpu + Vector((-0.2 * k, 0.2 * k - i * 0.1 * k, 0.45 * k)), Vector((hpu.x - 0.2 * k, P.y + 0.1 * k - i * 0.08 * k, zc + crown_h + 0.4 * k)),
                             Vector((P.x + 0.1 * k, P.y + 0.1 * k - i * 0.08 * k, zc + crown_h + 0.3 * k))], 0.015 * k)
        K.box((2 * px * 0.3, pd * 0.25, 0.12 * k), P + Vector((0, 0, zb - z0 + 0.07 + ld_h + 0.012)), M.molten((1.0, 0.42, 0.08), 6.0, 5.0), bevel=0.02, base=True, name="hot_billet")
        hl = KI.point_light(P + Vector((0, -pd * 0.5, zb - z0 + 0.4)), (1.0, 0.45, 0.12), 40.0 * k, 0.15)
    else:
        # flywheel on +X end of crown (axis X) with motor on crown + belts
        R = 0.36 * k
        fxw = P.x + px + cw / 2 + 0.12
        fz = zc + crown_h * 0.5
        fly = KI.spoked_wheel((fxw, P.y - pd * 0.05, fz), R, 0.12 * k, spokes=5, mat=st.accent_mat() if st.tier != 1 else M.metal("cast_iron"),
                              rot=K.AXES["x"], rim=0.2, grooves=3)
        fly.append(K.box((0.012, R * 0.25, R * 0.08), (fxw + 0.07 * k, P.y - pd * 0.05 + R * 0.55, fz), M.painted((0.85, 0.85, 0.82), name="mark"), bevel=0.002))
        flp = KI.pivot((fxw, P.y - pd * 0.05, fz), name="flywheel")
        KI.bind(fly, flp)
        an.spin(flp, 1.0, axis="X")
        mz = zc + crown_h + 0.2 * k
        my = P.y + pd * 0.2
        KI.motor((P.x + px * 0.45, my, mz), axis="x", r=0.15 * k, length=0.45 * k,
                 mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, grime=st.grime, name="motor_paint"))
        K.box((0.6 * k, 0.4 * k, 0.05), (P.x + px * 0.45, my, zc + crown_h), frame, bevel=0.006, base=True)
        belt = M.rubber((0.02, 0.02, 0.022))
        for g in range(3):
            x = fxw - 0.04 * k + g * 0.04 * k
            KI.strut((x, my, mz + 0.08), (x, P.y - pd * 0.05 + R * 0.2, fz + R * 0.95), 0.012, belt, verts=6)
            KI.strut((x, my, mz - 0.08), (x, P.y - pd * 0.05 + R * 0.6, fz + R * 0.7), 0.012, belt, verts=6)
        K.cyl(0.08 * k, 0.12 * k, (fxw, my, mz), M.metal("cast_iron"), rot=K.AXES["x"], verts=20, base=False)
        KI.strut((P.x + px * 0.45 + 0.25 * k, my, mz), (fxw, my, mz), 0.03 * k, M.metal("steel"), verts=12)
    # light curtains at the front corners + two-hand control
    lc_mat, lc_s = KI.anim_emit((1.0, 0.1, 0.05), 6.0, "curtain")
    for sx in (-1, 1):
        lx = P.x + sx * (px - cw * 0.2)
        ly = P.y - pd / 2 - 0.12
        K.box((0.06, 0.06, (zc - zb) * 0.8), (lx, ly, zb), M.painted((0.75, 0.55, 0.02), wear=0.3, name="curtain_yel"), bevel=0.006, base=True)
        K.box((0.012, 0.02, (zc - zb) * 0.7), (lx - sx * 0.032, ly, zb + (zc - zb) * 0.05), lc_mat, bevel=0, base=True)
        K.box((0.04, 0.12, 0.04), (lx, ly + 0.07, zb + 0.02), M.metal("dark_steel"), bevel=0.004)
    an.value(lc_s, lambda t: 2.0 + 6.0 * (1.0 if math.cos(TAU * t) < 0 else 0.3))
    cs = Vector((P.x + 0.05, -0.42 * d, z0))
    K.cyl(0.05, 0.9, cs, M.metal("steel", dirt=0.6), verts=12)
    K.box((0.5 * k, 0.16, 0.12), cs + Vector((0, 0, 0.9)), M.painted((0.75, 0.55, 0.02), wear=0.3, name="curtain_yel"), bevel=0.012, base=True)
    for sx in (-1, 1):
        K.cyl(0.035, 0.03, cs + Vector((sx * 0.17 * k, 0, 1.02)), M.emissive((0.1, 0.4, 1.0) if sx < 0 else (0.1, 0.4, 1.0), 2.0), verts=16)
    K.cyl(0.045, 0.04, cs + Vector((0, -0.02, 1.02)), M.emissive((1.0, 0.05, 0.03), 4.0), verts=16)
    sl, socks = KI.stack_light((P.x - px - cw / 2 - 0.02, P.y - pd * 0.3, zc + crown_h + 0.0))
    an.value(socks[2], lambda t: 6.0)
    # parts bin at front-right with stampings
    bx = Vector((0.36 * w, -0.3 * d, z0))
    KI.frustum((0.36 * k, 0.3 * k), (0.42 * k, 0.36 * k), 0.3 * k, bx, M.painted((0.08, 0.2, 0.42), wear=0.6, name="bin_blue"), open_top=True, thick=0.015)
    for i in range(6):
        K.box((0.12 * k, 0.08 * k, 0.008), bx + Vector(((i % 3 - 1) * 0.09 * k, (i // 3 - 0.5) * 0.1 * k, 0.24 * k + i * 0.004)),
              M.metal("stainless", dirt=0.3), bevel=0.002, rot=(0.1 * i, 0.15, i))
    KI.cable(KI.sag((cs.x, cs.y + 0.03, z0 + 0.4), (P.x - 0.2, P.y - pd / 2, z0 + 0.3), 0.0, 4), 0.014)
    return Rig(height=zc + crown_h + 0.2 * k + 0.2 * k, frames=16, fps=12, update=an,
               emitters=[{"pos": [P.x, P.y - pd * 0.3, die_top + 0.02], "type": "sparks"}])


# =========================================================================== rolling mill
def rolling_mill(spec, p):
    """Four-high rolling stand: two housings with screw-down capsules, work + backup rolls, drive
    spindles from a pinion stand and DC motor, entry/exit roller tables carrying a glowing strip
    that scrolls through the bite, descaling sprays."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    steel = st.steel()
    KI.concrete_pad(w * 0.98, d * 0.98, 0.1, st.concrete())
    z0 = 0.1
    Ym = -0.1 * d
    Xs = -0.04 * w
    zp = z0 + 0.42 + 0.08 * s
    hy = 0.2 * d + 0.05
    hwx = 0.32 * k
    ht = 0.16 * k
    rw = 0.065 * k
    rb = 0.13 * k
    H = zp + 2 * rw + 2 * rb + 0.32 * k
    # housings (window frames) at y = Ym +- hy
    for sy in (-1, 1):
        y = Ym + sy * hy
        for sx in (-1, 1):
            K.box((hwx * 0.3, ht, H - z0), (Xs + sx * hwx * 0.35, y, z0), body, bevel=0.02, base=True, name="post")
        K.box((hwx, ht, 0.24 * k), (Xs, y, H - 0.24 * k), body, bevel=0.02, base=True)
        K.box((hwx, ht, zp - rw - 2 * rb - z0 - 0.04), (Xs, y, z0), body, bevel=0.02, base=True)
        K.box((hwx * 1.3, ht * 1.4, 0.08), (Xs, y, z0), frame, bevel=0.01, base=True)
        cap = K.cyl(0.11 * k, 0.16 * k, (Xs, y, H), M.metal("dark_steel"), verts=24)
        K.cyl(0.06 * k, 0.06, (Xs, y, H + 0.16 * k), M.metal("chrome"), verts=16)
        # chocks
        for zz in (zp + rw + 0.006 + rb, zp - rw - 0.006 - rb):
            K.box((hwx * 0.4, ht * 1.05, rb * 1.6), (Xs, y, zz), st.accent_mat(), bevel=0.01)
        for zz in (zp + rw + 0.006, zp - rw - 0.006):
            K.box((hwx * 0.4, ht * 1.05, rw * 1.5), (Xs, y, zz), st.accent_mat(), bevel=0.008)
    KI.beam((Xs, Ym - hy, H + 0.1 * k), (Xs, Ym + hy, H + 0.1 * k), 0.16 * k, 0.12 * k, frame)
    # rolls
    rolls = []
    marks = M.painted((0.75, 0.5, 0.02), name="roll_mark")
    roll_len = 2 * hy + ht + 0.2
    for zz, r, sgn in ((zp + rw + 0.006, rw, -1), (zp - rw - 0.006, rw, 1), (zp + 2 * rw + 0.006 + rb, rb, 1), (zp - 2 * rw - 0.006 - rb, rb, -1)):
        grp = [K.cyl(r, roll_len, (Xs, Ym, zz), M.metal("steel", rough=0.18, dirt=0.3), rot=(math.pi / 2, 0, 0), verts=40, base=False, name="roll")]
        grp.append(K.box((r * 0.5, 0.012, r * 0.18), (Xs + r * 0.45, Ym - roll_len / 2 - 0.004, zz), marks, bevel=0.001))
        rp = KI.pivot((Xs, Ym, zz), children=grp)
        rolls.append(rp)
        an.spin(rp, sgn * 1.0 * (rw / r), axis="Y")
    # spindles + pinion stand + motor at the back
    yps = 0.36 * d
    pz = [zp + rw + 0.006, zp - rw - 0.006]
    K.box((0.42 * k, 0.32 * k, zp + 0.28 * k - z0), (Xs, yps, z0), body, bevel=0.02, base=True, name="pinion_stand")
    K.box((0.48 * k, 0.36 * k, 0.06), (Xs, yps, zp + 0.28 * k), frame, bevel=0.008, base=True)
    for i, zz in enumerate(pz):
        y0 = Ym + roll_len / 2
        y1 = yps - 0.16 * k
        grp = [K.cyl(0.035 * k, y1 - y0, (Xs, (y0 + y1) / 2, zz), steel, rot=(math.pi / 2, 0, 0), verts=12, base=False, name="spindle")]
        for yy in (y0 + 0.04, y1 - 0.04):
            grp.append(K.cyl(0.06 * k, 0.08, (Xs, yy, zz), M.metal("dark_steel"), rot=(math.pi / 2, 0, 0), verts=16, base=False))
            grp += K.bolts(Vector((Xs, yy - 0.04, zz)), 0.045 * k, 4, axis="-y", r=0.01)
        sp = KI.pivot((Xs, Ym, zz), children=grp)
        an.spin(sp, (1 if i == 0 else -1) * -0.5, axis="Y")
    mr = 0.24 * k
    mlen = Xs - 0.21 * k - (-0.47 * w)
    if mlen > 0.3:
        mc = Vector((Xs - 0.21 * k - mlen / 2, yps, z0 + mr + 0.08))
        K.cyl(mr, mlen * 0.8, mc, M.painted((0.06, 0.16, 0.3), wear=st.wear, grime=st.grime, name="motor_paint") if st.tier < 4 else body,
              rot=K.AXES["x"], verts=40, base=False, name="dc_motor")
        K.box((mlen * 0.85, mr * 1.6, 0.1), (mc.x, mc.y, z0), frame, bevel=0.01, base=True)
        K.box((mlen * 0.3, mr * 0.9, mr * 0.6), mc + Vector((0, 0, mr * 0.9)), body, bevel=0.012)
        for i in range(5):
            K.torus(mr * 1.01, 0.012, mc + Vector((-mlen * 0.35 + i * mlen * 0.175, 0, 0)), M.metal("dark_steel"), rot=K.AXES["x"])
    # roller tables + strip
    tw = 0.34 * d
    tz = zp - 0.04
    hot_m, hot_phase = KI.scrolling_hot_metal(color=(1.0, 0.3, 0.04), axis="X", period=0.25, strength=7.0)
    table_rollers = []
    for xa, xb, thick in ((-w * 0.49, Xs - hwx / 2 - 0.05, 0.07 * k), (Xs + hwx / 2 + 0.05, w * 0.49, 0.03 * k)):
        L = xb - xa
        K.box((L, 0.06, 0.2), ((xa + xb) / 2, Ym - tw / 2 - 0.03, tz - 0.2), frame, bevel=0.008, base=True)
        K.box((L, 0.06, 0.2), ((xa + xb) / 2, Ym + tw / 2 + 0.03, tz - 0.2), frame, bevel=0.008, base=True)
        K.box((L, 0.03, 0.12), ((xa + xb) / 2, Ym - tw / 2 - 0.07, tz), st.safety() if st.tier < 4 else frame, bevel=0.006, base=True)
        n = max(2, int(L / 0.2))
        for i in range(n):
            x = xa + (i + 0.5) * L / n
            ro = K.cyl(0.04, tw, (x, Ym, tz - 0.04), steel, rot=(math.pi / 2, 0, 0), verts=16, base=False)
        for x in (xa + 0.1, xb - 0.1):
            for sy in (-1, 1):
                K.box((0.08, 0.08, tz - 0.2 - z0), (x, Ym + sy * (tw / 2 + 0.03), z0), frame, bevel=0.006, base=True)
        K.box((L, tw * 0.62, thick), ((xa + xb) / 2, Ym, tz), hot_m, bevel=0.004, base=True, name="strip")
    an.value(hot_phase, lambda t: -TAU * 3 * t)
    # descaling header with spray (steam)
    hx = Xs - hwx / 2 - 0.35 * k
    for zz in (tz + 0.18,):
        K.cyl(0.03, tw * 1.1, (hx, Ym, zz), steel, rot=(math.pi / 2, 0, 0), verts=12, base=False)
        KI.pipe([(hx, Ym + tw * 0.55, zz), (hx, Ym + tw * 0.75, zz), (hx, Ym + tw * 0.75, z0 + 0.05)], r=0.025, mat=st.mat((0.05, 0.15, 0.4), name="water_line"), flanges=False)
    # control pulpit cabinet on the -Y side of the exit table
    KI.cabinet((0.3 * w, -0.43 * d, z0), 0.0, w=0.38 * k, d=0.16, h=0.75, mat=st.mat((0.6, 0.6, 0.58), wear=0.5)) if d >= 2.5 else None
    sl, socks = KI.stack_light((Xs + hwx * 0.4, Ym - hy - ht / 2 + 0.02, H + 0.1))
    an.value(socks[2], lambda t: 6.0)
    glow = KI.point_light((Xs + 0.6, Ym, tz + 0.4), (1.0, 0.5, 0.15), 40.0 * k, 0.3)
    glow2 = KI.point_light((Xs - 0.8, Ym, tz + 0.4), (1.0, 0.5, 0.15), 40.0 * k, 0.3)
    return Rig(height=H + 0.25 * k, frames=16, fps=12, update=an,
               lights=[{"pos": [Xs, Ym, tz + 0.3], "color": [1.0, 0.5, 0.15], "energy": 1.0, "flicker": False}],
               emitters=[{"pos": [hx, Ym, tz + 0.15], "type": "steam"}, {"pos": [Xs, Ym - hy * 0.5, zp + 0.1], "type": "steam"}])


# =========================================================================== wire drawer
def wire_drawer(spec, p):
    """Multi-die wire drawing machine: rod payoff turntable, a row of water-cooled capstans with
    die boxes between them, take-up spooler with traversing guide, lube tank and controls."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.7
    body = st.body()
    frame = st.frame()
    steel = st.steel()
    cu = M.metal("copper", rough=0.25, dirt=0.25)
    KI.concrete_pad(w * 0.96, d * 0.96, 0.08, st.concrete())
    z0 = 0.08
    # machine bed
    bx0, bx1 = -0.28 * w, 0.24 * w
    by0, by1 = -0.18 * d, 0.2 * d
    bh = 0.55 + 0.12 * s
    bc = Vector(((bx0 + bx1) / 2, (by0 + by1) / 2, z0))
    K.box((bx1 - bx0, by1 - by0, bh), bc, body, bevel=0.025, base=True, name="bed")
    K.box((bx1 - bx0 + 0.04, by1 - by0 + 0.04, 0.05), bc + Vector((0, 0, bh)), M.metal("stainless", dirt=st.dirt), bevel=0.008, base=True)
    K.box((bx1 - bx0 - 0.04, by1 - by0 - 0.04, 0.06), bc, frame, bevel=0.006, base=True)
    n_door = max(2, int((bx1 - bx0) / 0.45))
    for i in range(n_door):
        x = bx0 + (bx1 - bx0) * (i + 0.5) / n_door
        K.box((0.006, 0.006, bh * 0.75), (x - (bx1 - bx0) / n_door / 2 + 0.02, by0 - 0.004, z0 + bh * 0.12), M.plastic((0.02, 0.02, 0.02)), bevel=0)
        KI.louvers((x, by0 - 0.012, z0 + bh * 0.4), (bx1 - bx0) / n_door * 0.5, bh * 0.25, "-y")
    # capstans
    zt = z0 + bh + 0.05
    n = max(3, int((bx1 - bx0) / (0.34 * k)))
    cr = min(0.17 * k, (bx1 - bx0) / n * 0.42)
    ch = 0.2 * k
    cy = bc.y - 0.02 * d
    xs = [bx0 + (bx1 - bx0) * (i + 0.5) / n for i in range(n)]
    for i, x in enumerate(xs):
        grp = []
        grp.append(K.cyl(cr * 1.12, 0.03, (x, cy, zt + 0.03), M.metal("dark_steel"), verts=40))
        grp.append(K.cyl(cr, ch, (x, cy, zt + 0.06), M.metal("chrome", rough=0.15), verts=40, name="capstan"))
        for j in range(3):
            grp.append(K.torus(cr * 1.01, 0.008, (x, cy, zt + 0.08 + j * 0.022), cu, segs=40, rsegs=6))
        grp.append(K.cyl(cr * 1.1, 0.03, (x, cy, zt + 0.06 + ch), M.metal("dark_steel"), verts=40))
        grp.append(K.cyl(cr * 0.35, 0.04, (x, cy, zt + 0.09 + ch), M.metal("steel"), verts=6))
        grp += K.bolts(Vector((x, cy, zt + 0.09 + ch)), cr * 0.7, 6, r=0.012)
        grp.append(K.box((cr * 0.5, 0.025, 0.012), (x + cr * 0.6, cy, zt + 0.094 + ch), M.painted((0.8, 0.55, 0.02), name="mark"), bevel=0.002))
        cp = KI.pivot((x, cy, 0), children=grp)
        an.spin(cp, (2 + i) / 6.0 * 2)
        K.cyl(cr * 0.5, 0.06, (x, cy, zt), frame, verts=24)
        # die box between capstans
        if i < n - 1:
            dx = (x + xs[i + 1]) / 2
            K.box((0.1 * k, 0.14 * k, 0.12 * k), (dx, cy - cr * 0.95, zt), M.painted((0.05, 0.05, 0.055), wear=0.3, name="diebox"), bevel=0.01, base=True)
            K.box((0.08 * k, 0.1 * k, 0.012), (dx, cy - cr * 0.95, zt + 0.12 * k), M.plastic((0.6, 0.6, 0.55), 0.6, name="soap"), bevel=0.003, base=True)
    # wire path: tangent runs on the -Y side (r tiny)
    wz = zt + 0.1
    for i in range(n - 1):
        K.tube([(xs[i], cy - cr * 1.02, wz), (xs[i + 1], cy - cr * 1.02, wz)], 0.008, cu)
    # payoff turntable with rod coil (-X end)
    po = Vector((-0.4 * w, -0.04 * d, z0))
    pr = min(0.16 * w, 0.24 * d)
    K.cyl(pr * 1.05, 0.2, po, frame, verts=40)
    coil = [K.cyl(pr, 0.03, po + Vector((0, 0, 0.2)), M.metal("dark_steel"), verts=40)]
    rodm = M.metal("copper", rough=0.45, dirt=0.7)
    for j in range(6):
        coil.append(K.torus(pr * 0.78, 0.035 * k, po + Vector((0, 0, 0.26 + j * 0.06 * k)), rodm, segs=40, rsegs=8))
    for j in range(4):
        coil.append(K.box((0.04, 0.04, 0.5 * k), po + Vector((math.cos(j * TAU / 4) * pr * 0.45, math.sin(j * TAU / 4) * pr * 0.45, 0.23)), M.metal("steel"), bevel=0.004, base=True))
    cp = KI.pivot(po, children=coil)
    an.spin(cp, 0.25)
    K.tube([po + Vector((pr * 0.78, 0, 0.26 + 0.3 * k)), po + Vector((pr * 0.9, -0.05, 0.6 * k)), (xs[0] - cr, cy - cr * 1.01, wz)], 0.008, rodm)
    # take-up spooler (+X end)
    tu = Vector((0.38 * w, -0.02 * d, z0))
    spr = min(0.17 * k, 0.12 * w)
    sph = 0.34 * k
    K.box((spr * 2 + 0.2, 0.1, spr * 2 + 0.4), tu + Vector((0, sph / 2 + 0.1, 0)), body, bevel=0.015, base=True)
    K.box((spr * 2 + 0.3, sph * 1.6, 0.12), tu, frame, bevel=0.01, base=True)
    spz = z0 + 0.15 + spr + 0.05
    spool = [K.cyl(spr * 0.55, sph, (tu.x, tu.y, spz), cu, rot=(math.pi / 2, 0, 0), verts=40, base=False, name="windings")]
    for sy in (-1, 1):
        spool.append(K.cyl(spr, 0.025, (tu.x, tu.y + sy * sph / 2, spz), M.metal("steel", dirt=0.5), rot=(math.pi / 2, 0, 0), verts=40, base=False))
    for j in range(5):
        a = TAU * j / 5
        spool.append(K.cyl(spr * 0.08, 0.03, (tu.x + math.cos(a) * spr * 0.75, tu.y - sph / 2 - 0.012, spz + math.sin(a) * spr * 0.75), M.metal("dark_steel"), rot=(math.pi / 2, 0, 0), verts=12, base=False))
    sp = KI.pivot((tu.x, tu.y, spz), children=spool)
    an.spin(sp, 2.0 / 5.0, axis="Y")
    K.cyl(0.025, sph + 0.2, (tu.x, tu.y, spz), M.metal("steel"), rot=(math.pi / 2, 0, 0), verts=12, base=False)
    # traverse guide
    gz = spz + spr + 0.12
    K.cyl(0.015, sph * 1.2, (tu.x - spr * 0.3, tu.y, gz), M.metal("chrome"), rot=(math.pi / 2, 0, 0), verts=10, base=False)
    guide = [K.box((0.06, 0.05, 0.08), (tu.x - spr * 0.3, tu.y, gz), M.painted((0.75, 0.5, 0.02), name="guide"), bevel=0.006),
             K.cyl(0.02, 0.012, (tu.x - spr * 0.3, tu.y, gz - 0.05), M.metal("dark_steel"), rot=(0, math.pi / 2, 0), verts=12, base=False)]
    gp = KI.pivot((tu.x, tu.y, gz), children=guide)
    an.move(gp, lambda t: (0, sph * 0.4 * math.sin(TAU * t), 0))
    K.tube([(xs[-1] + cr * 0.2, cy - cr * 1.01, wz), (tu.x - spr * 0.3, tu.y, gz - 0.05)], 0.004, cu)
    # lube tank + pump at the back, cabinet front-left
    lt = Vector((bc.x, 0.36 * d, z0))
    K.box(((bx1 - bx0) * 0.6, 0.18 * d, 0.4 * k), lt, st.mat((0.25, 0.27, 0.28), name="tank_grey"), bevel=0.015, base=True)
    KI.motor((lt.x + (bx1 - bx0) * 0.2, lt.y, z0 + 0.4 * k + 0.08), axis="x", r=0.06 * k, length=0.16 * k,
             mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, name="motor_paint"))
    KI.pipe([(lt.x - (bx1 - bx0) * 0.15, lt.y, z0 + 0.4 * k), (lt.x - (bx1 - bx0) * 0.15, lt.y, zt + 0.25), (lt.x - (bx1 - bx0) * 0.15, cy + cr * 1.3, zt + 0.25),
             (lt.x + (bx1 - bx0) * 0.2, cy + cr * 1.3, zt + 0.25)], r=0.018, mat=st.mat((0.05, 0.25, 0.08), name="lube_green"), flanges=False)
    KI.cabinet((-0.38 * w, 0.36 * d, z0), 0.0, w=0.3 * k, d=0.16, h=0.9 * k, mat=st.mat((0.6, 0.61, 0.6), wear=0.4))
    KI.cable(KI.sag((-0.38 * w + 0.1, 0.36 * d - 0.05, z0 + 0.3), (bx0, by1 - 0.1, z0 + 0.3), 0.05, 4), 0.014)
    sl, socks = KI.stack_light((bx1 - 0.08, by1 - 0.08, z0 + bh + 0.05))
    an.value(socks[2], lambda t: 6.0)
    return Rig(height=zt + ch + 0.6 * k + 0.1, frames=16, fps=12, update=an)


# =========================================================================== foundry
def foundry(spec, p):
    """Casting foundry cell: tilting induction crucible on a raised deck pours a molten stream into
    sand moulds that index along a roller line into a cooling tunnel; fume hood + duct."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    steel = st.steel()
    KI.concrete_pad(w * 0.98, d * 0.98, 0.1, st.concrete())
    z0 = 0.1
    line_y = -0.27 * d
    zl = z0 + 0.42
    # crucible geometry
    sc_ = min(s, 3.4)
    cr = 0.19 * sc_
    ch = 0.5 * sc_
    spout = 0.12 * k
    Fx = -0.16 * w
    Fy = line_y + cr + spout
    zpf = z0 + 0.42 + 0.15 * sc_
    lip = Vector((Fx, line_y, zpf + 0.12 + ch))
    # deck
    dy0 = line_y + 0.38 * k
    K.box((w * 0.62, 0.48 * d - dy0, 0.06), (-0.17 * w, (dy0 + 0.48 * d) / 2, zpf - 0.06), M.tread_plate(1.2, rust=st.tier == 1), bevel=0.006, base=True)
    for xx in (-0.46 * w, 0.12 * w):
        for yy in (dy0 + 0.05, 0.45 * d):
            K.box((0.1, 0.1, zpf - 0.06 - z0), (xx, yy, z0), frame, bevel=0.006, base=True)
    K.box((w * 0.62, 0.08, 0.12), (-0.17 * w, dy0 + 0.04, zpf - 0.18), frame, bevel=0.008, base=True)
    K.railing([(Fx + cr + 0.15, dy0 + 0.03, zpf), (0.13 * w, dy0 + 0.03, zpf)], 0.9, st.safety())
    # tilting crucible furnace (pivot at the spout lip, tilts toward -Y)
    furn = []
    fc = Vector((Fx, Fy, zpf + 0.12))
    furn.append(K.box((cr * 2.3, cr * 2.3, ch * 0.92), fc, body, bevel=0.025, base=True, name="furnace_body"))
    furn.append(K.cyl(cr * 1.05, 0.08, fc + Vector((0, 0, ch * 0.92)), M.metal("dark_steel", dirt=1.0), verts=40))
    furn.append(KI.ring(cr * 0.98, cr * 0.72, 0.06, fc + Vector((0, 0, ch + 0.0)), M.plastic((0.5, 0.45, 0.4), 0.9, name="refractory"), segs=40))
    furn.append(K.cyl(cr * 0.74, 0.02, fc + Vector((0, 0, ch - 0.05)), M.molten((1.0, 0.5, 0.1), 12.0, 4.0), verts=40, bevel=0, name="melt"))
    furn.append(K.prism([(-0.06 * k, 0), (0.06 * k, 0), (0.04 * k, 0.05 * k), (-0.04 * k, 0.05 * k)], spout + cr * 0.3,
                        (Fx, line_y + (spout + cr * 0.3) / 2, zpf + 0.12 + ch - 0.05 * k), M.metal("cast_iron", dirt=1.0), rot=(0, 0, 0), bevel=0.006, name="spout"))
    for zz in (0.25, 0.55, 0.8):
        furn.append(K.box((cr * 2.36, cr * 2.36, 0.04), fc + Vector((0, 0, ch * zz)), frame, bevel=0.006, base=True))
    furn.append(K.box((cr * 1.2, 0.02, ch * 0.2), fc + Vector((0, -cr * 1.15 - 0.01, ch * 0.3)), M.plastic((0.02, 0.02, 0.02)), bevel=0.002))
    for i in range(3):
        furn.append(K.cyl(0.03 * k, 0.04, fc + Vector((-cr * 0.4 + i * cr * 0.4, -cr * 1.15 - 0.02, ch * 0.55)), M.metal("copper"), rot=K.AXES["-y"], verts=12))
    fp = KI.pivot(lip, name="furnace_tilt")
    KI.bind(furn, fp)
    # trunnion stands + tilt cylinder
    for sx in (-1, 1):
        K.box((0.1 * k, 0.16 * k, ch * 0.95), (Fx + sx * (cr * 1.15 + 0.07 * k), line_y + 0.12 * k, zpf), frame, bevel=0.01, base=True)
        K.cyl(0.06 * k, 0.12, (Fx + sx * (cr * 1.15 + 0.07 * k), line_y + 0.12 * k, lip.z - 0.02), M.metal("dark_steel"), rot=K.AXES["x"], verts=16, base=False)
    hobjs, hrod, hdir = KI.hydraulic((Fx, Fy + cr * 1.3, zpf), (Fx, Fy + cr * 1.18, zpf + 0.12 + ch * 0.35), r=0.05 * k)

    def tilt(t):
        if t < 0.1:
            return KI.smooth01(t / 0.1)
        if t < 0.55:
            return 1.0
        if t < 0.68:
            return 1.0 - KI.smooth01((t - 0.55) / 0.13)
        return 0.0
    max_tilt = math.radians(28)
    an.rotate(fp, lambda t: max_tilt * tilt(t), axis="X")
    an.move(hrod, lambda t: (0, 0, 0.12 * k * tilt(t)))
    # pouring stream
    mold_h = 0.22 * k
    stream_m, stream_s = KI.anim_emit((1.0, 0.32, 0.04), 5.0, "stream")
    stream = K.cyl(0.022 * k, lip.z - (zl + mold_h + 0.02), (lip.x, lip.y - 0.03, zl + mold_h + 0.02), stream_m, verts=12, bevel=0, name="stream")
    an.visible([stream], lambda t: 0.12 < t < 0.56)
    # roller line along X
    lx0, lx1 = -0.49 * w, 0.49 * w
    lw_ = 0.42 * k
    for sy in (-1, 1):
        K.box((lx1 - lx0, 0.06, 0.12), ((lx0 + lx1) / 2, line_y + sy * (lw_ / 2 + 0.03), zl - 0.14), frame, bevel=0.006, base=True)
    nrl = int((lx1 - lx0) / 0.16)
    for i in range(nrl):
        K.cyl(0.03, lw_, (lx0 + (i + 0.5) * (lx1 - lx0) / nrl, line_y, zl - 0.03), steel, rot=(math.pi / 2, 0, 0), verts=12, base=False)
    for x in (lx0 + 0.1, (lx0 + lx1) / 2, lx1 - 0.1):
        for sy in (-1, 1):
            K.box((0.06, 0.06, zl - 0.14 - z0), (x, line_y + sy * (lw_ / 2 + 0.03), z0), frame, bevel=0.005, base=True)
    # cooling tunnel at the +X end
    tx0 = 0.14 * w
    th = mold_h + 0.18 * k
    tunnel_m = st.mat((0.28, 0.29, 0.3) if st.tier < 4 else (0.6, 0.61, 0.62), name="tunnel")
    K.box((lx1 - tx0, lw_ + 0.2, 0.06), ((tx0 + lx1) / 2, line_y, zl + th), tunnel_m, bevel=0.01, base=True)
    for sy in (-1, 1):
        K.box((lx1 - tx0, 0.05, th), ((tx0 + lx1) / 2, line_y + sy * (lw_ / 2 + 0.08), zl), tunnel_m, bevel=0.008, base=True)
    for i in range(8):
        K.box((0.012, lw_ / 8 * 0.9, th * 0.95), (tx0 - 0.01, line_y - lw_ / 2 + (i + 0.5) * lw_ / 8, zl + th * 0.02), M.plastic((0.25, 0.2, 0.1), 0.4, name="strip_curtain"), bevel=0.002, base=True)
    KI.louvers(((tx0 + lx1) / 2, line_y - lw_ / 2 - 0.11, zl + th * 0.55), (lx1 - tx0) * 0.6, th * 0.4, "-y")
    for i in range(2):
        fo, rot = K.fan(Vector((tx0 + (lx1 - tx0) * (0.3 + 0.4 * i), line_y, zl + th + 0.08)), r=lw_ * 0.3, axis="z", blades=5)
        an.spin(rot, 2.0 / 5.0)
    # moulds that index one pitch per loop
    pitch = 0.5 * k
    n = int((lx1 - lx0) / pitch) + 2
    u0 = int(math.floor((lx0 - Fx) / pitch))
    flask = M.metal("dark_steel", dirt=1.0)
    sand = M.concrete(2.0, tint=(0.35, 0.3, 0.25))
    molds = []
    for i in range(n):
        u = u0 + i
        grp = [K.box((0.36 * k, lw_ * 0.85, mold_h), (0, 0, 0), flask, bevel=0.01, base=True, name="flask")]
        grp.append(K.box((0.33 * k, lw_ * 0.8, 0.01), (0, 0, mold_h), sand, bevel=0.002, base=True))
        for sx in (-1, 1):
            grp.append(K.box((0.03, lw_ * 0.9, 0.04), (sx * 0.17 * k, 0, mold_h * 0.5), flask, bevel=0.004))
        gm, gs = KI.anim_emit((1.0, 0.45, 0.08), 0.0, "pour_cup")
        grp.append(K.cyl(0.045 * k, 0.012, (0, 0, mold_h), gm, verts=16, bevel=0))
        grp.append(K.torus(0.05 * k, 0.01, (0, 0, mold_h + 0.01), sand))
        piv = KI.pivot((0, 0, 0))
        KI.group(grp, piv)
        molds.append((piv, u, gs, grp))
    span = n * pitch

    def mold_upd(t):
        sh = KI.smooth01((t - 0.68) / 0.3) if t > 0.68 else 0.0
        for piv, u, gs, grp in molds:
            x = Fx + (u + sh) * pitch
            # wrap into the visible line range
            while x > lx1 + pitch * 0.5:
                x -= span
            while x < lx0 - pitch * 0.5:
                x += span
            piv.location = (x, line_y, zl)
            uu = round((x - Fx) / pitch - sh)
            if uu >= 1:
                g = 1.0
            elif uu == 0:
                g = KI.smooth01((t - 0.12) / 0.4) if t < 0.68 else 1.0
            else:
                g = 0.0
            gs.default_value = 9.0 * g
            hide = x < lx0 + 0.12 * k or x > lx1 - 0.1
            for o in grp:
                o.hide_render = hide
    an.add(mold_upd)
    # fume hood over the furnace + duct
    hz = lip.z + 0.5 * k
    hood_m = st.mat((0.06, 0.062, 0.065), name="hood", wear=1.3)
    KI.frustum((cr * 2.5, cr * 2.5), (cr * 0.9, cr * 0.9), 0.25 * k, (Fx, Fy + 0.05, hz), hood_m, open_top=False, bevel=0.01)
    dz = hz + 0.25 * k
    K.tube([(Fx, Fy + 0.05, dz), (Fx, Fy + 0.05, dz + 0.2 * k), (Fx, 0.47 * d, dz + 0.2 * k)],
           0.085 * k, hood_m, bend=0.2 * k)
    dz -= 0.05 * k
    for sx in (-1, 1):
        K.box((0.06, 0.06, hz - zpf), (Fx + sx * cr * 1.5, Fy + cr * 1.4, zpf), frame, bevel=0.005, base=True)
    # sand silo on legs, back-right, with chute toward the mould line start
    sp = Vector((0.32 * w, 0.28 * d, z0))
    sr = 0.15 * s
    sz = 0.6 + 0.12 * s
    for i in range(4):
        a_ = math.pi / 4 + i * math.pi / 2
        K.box((0.07, 0.07, sz + 0.1), sp + Vector((math.cos(a_) * sr * 0.8, math.sin(a_) * sr * 0.8, 0)), frame, bevel=0.005, base=True)
    K.cyl(0.06 * k, sr * 0.9, sp + Vector((0, 0, sz - sr * 0.9)), body, verts=24, r2=sr, name="silo_cone")
    K.cyl(sr, 0.6 * s, sp + Vector((0, 0, sz)), body, verts=40, name="silo")
    K.sphere(sr, sp + Vector((0, 0, sz + 0.6 * s)), body, scale=(1, 1, 0.25))
    for zz in (0.3, 0.6):
        K.torus(sr * 1.01, 0.012, sp + Vector((0, 0, sz + 0.6 * s * zz)), M.metal("steel", dirt=0.6))
    KI.ladder(sp + Vector((sr + 0.02, 0, 0)), sz + 0.6 * s, rot_z=math.pi / 2, w=0.3, mat=st.safety())
    KI.plate_sign(sp + Vector((0, -sr - 0.006, sz + 0.35 * s)), 0.2 * k, 0.1 * k, "-y", color=(0.8, 0.8, 0.76))
    # control pulpit on the deck
    KI.cabinet((0.0 * w, 0.32 * d, zpf), 0.0, w=0.4 * k, d=0.2, h=0.8, mat=st.mat((0.6, 0.6, 0.58), wear=0.5))
    sl, socks = KI.stack_light((0.0 * w + 0.15 * k, 0.32 * d, zpf + 0.82))
    an.value(socks[1], lambda t: 8.0 * KI.blink(t, 4) if 0.1 < t < 0.6 else 0.3)
    an.value(socks[2], lambda t: 6.0 if not (0.1 < t < 0.6) else 0.3)
    light = KI.point_light((lip.x, lip.y - 0.25, zl + mold_h + 0.4), (1.0, 0.5, 0.12), 0.0, 0.15)
    an.energy(light, lambda t: 10.0 + 70.0 * k * (1.0 if 0.12 < t < 0.56 else 0.15) * KI.flicker(t, 0.4, 0.2))
    an.add(lambda t: setattr(stream_s, "default_value", 4.5 + 1.5 * KI.flicker(t, 0.7, 0.4)))
    return Rig(height=dz + 0.3 * k + 0.15 * k, frames=16, fps=10, update=an,
               lights=[{"pos": [lip.x, lip.y, zl + mold_h + 0.3], "color": [1.0, 0.5, 0.15], "energy": 1.0, "flicker": True}],
               emitters=[{"pos": [lip.x, lip.y, zl + mold_h + 0.05], "type": "sparks"},
                         {"pos": [Fx, 0.47 * d, dz + 0.25 * k], "type": "smoke"}])


# =========================================================================== mixer
def mixer(spec, p):
    """Rotary drum mixer: drum with riding tyres and girth gear on trunnion rollers, pinion +
    gearmotor drive, feed hoppers with a screw feeder into the inlet, discharge hood and chute."""
    KI.begin()
    st = KI.Style(p, alt=p.get("tier", 1) == 2)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    body = st.body()
    frame = st.frame()
    steel = st.steel()
    KI.concrete_pad(w * 0.96, d * 0.96, 0.1, st.concrete())
    z0 = 0.1
    rd = 0.17 * s + 0.07
    Ld = 0.6 * w
    D = Vector((-0.04 * w, 0.04 * d, z0 + rd + 0.3 + 0.04 * s))
    # piers + trunnion rollers under each tyre
    ty = [D.x - Ld * 0.3, D.x + Ld * 0.3]
    for tx in ty:
        K.box((0.24 * k, rd * 2.0, 0.24), (tx, D.y, z0), st.concrete(0.5), bevel=0.02, base=True)
        for sy in (-1, 1):
            rc = Vector((tx, D.y + sy * rd * 0.72, D.z - rd * 0.98))
            rr = 0.09 * k
            K.cyl(rr, 0.12 * k, rc, steel, rot=K.AXES["x"], verts=24, base=False)
            K.box((0.3 * k, 0.12, rc.z - z0 - 0.24 + 0.04), (tx, rc.y, z0 + 0.24), frame, bevel=0.01, base=True)
            for sx in (-1, 1):
                K.box((0.07, 0.14, 0.12), (tx + sx * 0.12 * k, rc.y, rc.z - 0.04), M.metal("dark_steel"), bevel=0.008)
    # drum group (rotates about X)
    drum = []
    drum.append(K.cyl(rd, Ld, D, body, rot=K.AXES["x"], verts=64, base=False, name="drum"))
    for sx in (-1, 1):
        drum.append(K.cyl(rd, rd * 0.4, D + Vector((sx * (Ld / 2 + rd * 0.2), 0, 0)), body, rot=(0, sx * math.pi / 2, 0), verts=64, base=True, r2=rd * 0.55, name="cone"))
    for tx in ty:
        drum.append(KI.ring(rd * 1.1, rd * 0.98, 0.12 * k, (tx, D.y, D.z), steel, rot=K.AXES["x"], segs=64, name="tyre"))
    gx = D.x - Ld * 0.08
    drum += KI.gear((gx, D.y, D.z), rd * 1.16, 0.08 * k, teeth=60, mat=M.metal("dark_steel", dirt=0.7), rot=K.AXES["x"], hub=False)
    for a in (0.0, math.pi):  # 2-fold features: hatches, seams, stripes
        for xx in (-0.15, 0.16):
            c = D + Vector((xx * Ld, math.cos(a + 0.6) * rd, math.sin(a + 0.6) * rd))
            hb = K.box((0.26 * k, 0.05, 0.2 * k), c, M.metal("dark_steel", dirt=0.6), bevel=0.01, name="hatch")
            hb.rotation_euler = (a + 0.6 + math.pi / 2, 0, 0)
            drum.append(hb)
        for xx in (0.0,):
            seam = K.box((Ld, 0.02, 0.02), D + Vector((0, math.cos(a + 1.9) * rd, math.sin(a + 1.9) * rd)), steel, bevel=0.004)
            drum.append(seam)
        stripe = KI.ring(rd * 1.004, rd * 0.99, 0.06, D + Vector((Ld * 0.38, 0, 0)), M.hazard(10.0), rot=K.AXES["x"], segs=64, bevel=0)
        drum.append(stripe)
    for i in range(6):
        a = TAU * i / 6
        drum.append(K.box((0.03, 0.04, 0.04), D + Vector((-Ld * 0.08 - 0.06 * k, math.cos(a) * rd * 1.0, math.sin(a) * rd * 1.0)), steel, bevel=0.004))
    dp = KI.pivot(D, axis="x", name="drum")
    KI.bind(drum, dp)
    an.spin(dp, 0.5)
    # pinion + gearmotor on the -Y side
    pr = rd * 0.28
    pc = Vector((gx, D.y - (rd * 1.16 + pr * 0.98) * math.cos(0.5), D.z - (rd * 1.16 + pr * 0.98) * math.sin(0.5)))
    pin = KI.gear(pc, pr, 0.1 * k, teeth=15, mat=steel, rot=K.AXES["x"], hub=True)
    pp = KI.pivot(pc, axis="x", children=pin)
    an.spin(pp, -0.5 * 60 / 15)
    K.cyl(0.03 * k, 0.5 * k, (pc.x + 0.25 * k, pc.y, pc.z), steel, rot=K.AXES["x"], verts=12, base=False)
    gbx = pc.x + 0.35 * k
    K.box((0.26 * k, 0.3 * k, 0.32 * k), (gbx, pc.y, pc.z - 0.16 * k), st.accent_mat() if st.tier != 1 else frame, bevel=0.02, base=True, name="gearbox")
    K.box((0.3 * k, 0.34 * k, pc.z - 0.16 * k - z0), (gbx, pc.y, z0), frame, bevel=0.01, base=True)
    KI.motor((gbx, pc.y - 0.15 * k - 0.2 * k, pc.z - 0.02 * k), axis="-y", r=0.1 * k, length=0.3 * k,
             mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, grime=st.grime, name="motor_paint"))
    K.box((0.25 * k, 0.32 * k, pc.z - 0.12 * k - z0), (gbx, pc.y - 0.33 * k, z0), frame, bevel=0.01, base=True)
    # inlet: hopper on a stand + inclined screw feeder into the -X cone
    hx = D.x - Ld / 2 - rd * 0.2
    hp = Vector((-0.38 * w, 0.32 * d, z0))
    hh = D.z + rd * 0.7
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.06, 0.06, hh - z0), hp + Vector((sx * 0.18 * k, sy * 0.18 * k, 0)), frame, bevel=0.005, base=True)
    KI.frustum((0.2 * k, 0.2 * k), (0.62 * k, 0.62 * k), 0.45 * k, hp + Vector((0, 0, hh - z0)), body, open_top=True, thick=0.02)
    KI.rock_pile(hp + Vector((0, 0, hh - z0 + 0.38 * k)), 0.26 * k, 0.26 * k, 0.05, int(18 * k), M.concrete(3.0, tint=(0.9, 0.85, 0.75)), seed=6,
                 rmin=0.03, rmax=0.05)
    inlet = Vector((D.x - Ld / 2 - rd * 0.5, D.y, D.z + rd * 0.05))
    K.tube([hp + Vector((0, 0, hh - z0 - 0.05)), Vector((hp.x, hp.y, inlet.z + 0.35 * k)), inlet + Vector((-0.15 * k, 0, 0.1 * k)), inlet],
           0.08 * k, st.mat((0.4, 0.4, 0.38), name="feeder"), bend=0.15)
    K.cyl(rd * 0.6, 0.2 * k, (inlet.x - 0.08 * k, D.y, D.z), st.mat((0.4, 0.4, 0.38), name="feeder"), rot=K.AXES["x"], verts=40, base=False, name="inlet_seal")
    # discharge hood + chute + receiving bin (+X end)
    ox = D.x + Ld / 2 + rd * 0.35
    K.box((0.4 * k, rd * 1.6, rd * 2.2), (ox + 0.15 * k, D.y, D.z - rd * 1.1 - 0.15), body, bevel=0.02, base=True, name="discharge_hood")
    KI.frustum((0.3 * k, 0.3 * k), (0.38 * k, rd * 1.2), 0.3 * k, (ox + 0.15 * k, D.y - rd * 0.6, z0 + 0.0), body, top_offset=(0, rd * 0.5), bevel=0.01)
    K.cyl(0.07 * k, 0.4 * k, (ox + 0.15 * k, D.y, D.z + rd * 1.1 - 0.15), M.metal("stainless", dirt=st.dirt), verts=20)
    bin_ = Vector((0.36 * w, -0.3 * d, z0))
    KI.frustum((0.34 * k, 0.34 * k), (0.44 * k, 0.44 * k), 0.36 * k, bin_, st.accent_mat(), open_top=True, thick=0.02)
    KI.rock_pile(bin_ + Vector((0, 0, 0.3 * k)), 0.18 * k, 0.18 * k, 0.05, int(12 * k), M.concrete(3.0, tint=(0.55, 0.52, 0.48)), seed=8, rmin=0.025, rmax=0.045)
    KI.cabinet((-0.36 * w, -0.36 * d, z0), 0.0, w=0.32 * k, d=0.18, h=0.6 + 0.2 * s, mat=st.mat((0.6, 0.61, 0.6), wear=0.5))
    _, ls = KI.status_lamp((-0.36 * w + 0.08, -0.36 * d, z0 + 0.6 + 0.2 * s), (0.1, 1.0, 0.25), 10.0, r=0.025)
    an.value(ls, lambda t: 2 + 9 * KI.blink(t, 2))
    return Rig(height=max(hh + 0.45 * k, D.z + rd * 1.1 + 0.25 * k) + 0.05, frames=16, fps=10, update=an,
               emitters=[{"pos": [ox + 0.15 * k, D.y, D.z + rd * 1.1 + 0.3 * k], "type": "steam"}])


ARCHETYPES = KI.with_bounds({
    "electric_furnace": electric_furnace,
    "arc_furnace": arc_furnace,
    "crusher": crusher,
    "press": press,
    "rolling_mill": rolling_mill,
    "wire_drawer": wire_drawer,
    "foundry": foundry,
    "mixer": mixer,
})
