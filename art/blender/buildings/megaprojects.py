"""Megaproject archetypes: launch_pad, orbital_assembler."""
import math
import random

from mathutils import Vector

import kit as K
import kit_industry as KI
import materials as M
from buildings import Rig

TAU = KI.TAU


def _size(spec):
    w, d = spec.get("size", [6, 6])
    return float(w), float(d)


def _rocket_colors(st):
    return {1: ((0.45, 0.46, 0.46), (0.05, 0.05, 0.05)), 2: ((0.72, 0.72, 0.7), (0.55, 0.22, 0.03)),
            3: ((0.75, 0.76, 0.76), (0.04, 0.09, 0.25)), 4: ((0.8, 0.81, 0.82), (0.03, 0.032, 0.036))}[st.tier]


# =========================================================================== launch pad
def launch_pad(spec, p):
    """Orbital launch complex: concrete pad with a raised launch mount and flame trench, a two-stage
    rocket held by clamp arms, lattice umbilical tower with swing arms and lightning mast,
    spherical propellant tanks with feed lines, floodlight masts; venting vapour, blinking
    aviation lights."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    frame = st.frame()
    body = st.body()
    conc = M.concrete(0.25, tint=(0.85, 0.84, 0.8))
    K.box((w * 0.99, d * 0.99, 0.12), (0, 0, 0), conc, bevel=0.03, base=True, name="pad")
    z0 = 0.12
    R = Vector((0.04 * w, -0.02 * d, z0))
    # launch mount with a flame trench toward -Y
    mh = 0.35 + 0.1 * s
    mw = 0.3 * s
    K.box((mw, mw, mh), R, conc, bevel=0.04, base=True, name="mount")
    K.box((mw * 1.04, mw * 1.04, 0.08), R + Vector((0, 0, mh)), M.metal("dark_steel", dirt=1.0), bevel=0.012, base=True)
    tr_w = mw * 0.45
    soot = M.plastic((0.015, 0.014, 0.013), 0.95, name="soot")
    K.box((tr_w, mw * 0.08, mh * 0.85), R + Vector((0, -mw / 2 - 0.005, 0)), soot, bevel=0.01, base=True)
    ty1 = -0.495 * d
    for sx in (-1, 1):
        K.box((0.12 * s ** 0.5, (R.y - mw / 2) - ty1, 0.3), (R.x + sx * (tr_w / 2 + 0.06 * s ** 0.5), (R.y - mw / 2 + ty1) / 2, z0), conc, bevel=0.02, base=True)
    K.box((tr_w, (R.y - mw / 2) - ty1, 0.01), (R.x, (R.y - mw / 2 + ty1) / 2, z0), soot, bevel=0, base=True)
    K.box((tr_w * 1.4, 0.06, 0.06), (R.x, ty1 + 0.15, z0 + 0.3), M.hazard(5), bevel=0.004, base=True)
    # rocket
    rr = 0.075 * s
    Hr = 1.3 * s
    zr = z0 + mh + 0.08 + 0.12 * s ** 0.5
    c_body, c_acc = _rocket_colors(st)
    skin = st.mat(c_body, name="rocket_skin", wear=0.5, grime=0.5, rust=0.0)
    acc = st.mat(c_acc, name="rocket_band", wear=0.4, rust=0.0)
    # engines under the stage
    eng = M.metal("dark_steel", rough=0.35, dirt=0.6)
    for i in range(5):
        if i == 4:
            ex, ey = 0, 0
        else:
            a = math.pi / 4 + i * math.pi / 2
            ex, ey = math.cos(a) * rr * 0.55, math.sin(a) * rr * 0.55
        K.cyl(rr * 0.22, 0.16 * s ** 0.5, (R.x + ex, R.y + ey, zr - 0.16 * s ** 0.5), eng, verts=20, r2=rr * 0.1, name="nozzle")
    L1 = Hr * 0.58
    K.cyl(rr, L1, (R.x, R.y, zr), skin, verts=48, name="stage1")
    K.cyl(rr * 1.01, 0.05 * Hr, (R.x, R.y, zr + L1), acc, verts=48, name="interstage")
    L2 = Hr * 0.2
    K.cyl(rr, L2, (R.x, R.y, zr + L1 + 0.05 * Hr), skin, verts=48, name="stage2")
    fz = zr + L1 + 0.05 * Hr + L2
    K.cyl(rr * 1.08, Hr * 0.07, (R.x, R.y, fz), skin, verts=48, name="fairing_base")
    K.sphere(rr * 1.08, (R.x, R.y, fz + Hr * 0.07), skin, segs=48, rings=24, scale=(1, 1, 2.0))
    top = fz + Hr * 0.07 + rr * 1.08 * 2.0
    for zz in (zr + 0.08, zr + L1 * 0.62):
        K.cyl(rr * 1.005, 0.05 * Hr * 0.4, (R.x, R.y, zz), acc, verts=48)
    for i in range(4):  # grid fins / legs
        a = math.pi / 4 + i * math.pi / 2
        leg = KI.beam((R.x + math.cos(a) * rr, R.y + math.sin(a) * rr, zr + 0.05), (R.x + math.cos(a) * rr * 1.02, R.y + math.sin(a) * rr * 1.02, zr + Hr * 0.17),
                      0.05 * s ** 0.5, 0.03 * s ** 0.5, acc)
        K.box((0.12 * s ** 0.5, 0.012, 0.1 * s ** 0.5), (R.x + math.cos(a) * rr * 1.05, R.y + math.sin(a) * rr * 1.05, zr + L1 - 0.1 * Hr), eng, bevel=0.004,
              rot=(0, 0, a + math.pi / 2))
    KI.plate_sign((R.x + rr * 0.3, R.y - rr * 0.97, zr + L1 * 0.4), rr * 0.5, rr * 1.2, "-y", color=c_acc, text=False, border=False)
    for zz, wdt in ((0.25, 0.4), (0.3, 0.25)):
        K.box((rr * wdt, 0.01, rr * 0.06), (R.x - rr * 0.1, R.y - rr * 0.99, zr + L1 * zz), acc, bevel=0)
    # hold-down clamps
    for i in range(4):
        a = i * math.pi / 2
        K.box((0.14 * s ** 0.5, 0.1 * s ** 0.5, 0.12 * s ** 0.5 + 0.08), (R.x + math.cos(a) * (rr + 0.04), R.y + math.sin(a) * (rr + 0.04), z0 + mh + 0.08), frame, bevel=0.01, base=True, rot=(0, 0, a))
    # umbilical tower (back-left of the rocket)
    T = Vector((R.x - rr - 0.16 * s, R.y + rr + 0.14 * s, z0))
    tw = 0.13 * s
    th = top - z0 + 0.25 * s
    tm = st.mat((0.6, 0.12, 0.03) if st.tier <= 2 else (0.55, 0.56, 0.56), name="tower_paint", wear=0.8)
    KI.lattice(T, th, tw, tw, mat=tm, leg_r=0.02 * s ** 0.7, brace_r=0.008 * s ** 0.7, bay=0.55)
    nlev = max(3, int(th / 1.6))
    for i in range(1, nlev + 1):
        K.box((tw + 0.12, tw + 0.12, 0.03), T + Vector((0, 0, th * i / nlev)), M.tread_plate(1.4), bevel=0.004, base=True)
    K.cyl(0.015 * s ** 0.5, 0.25 * s, T + Vector((0, 0, th)), M.metal("steel"), verts=8, name="lightning_mast")
    for zz in (0.55, 0.86):
        z = zr + (top - zr) * zz
        a0 = T + Vector((tw / 2, -tw / 2, z - z0))
        b0 = Vector((R.x - rr * 0.6, R.y + rr * 0.6, z))
        KI.box_truss(a0, b0, 0.08 * s ** 0.5, 0.08 * s ** 0.5, tm, chord_r=0.012 * s ** 0.5, web_r=0.006 * s ** 0.5)
        K.box((0.16 * s ** 0.5, 0.16 * s ** 0.5, 0.12 * s ** 0.5), b0, M.metal("dark_steel"), bevel=0.01)
    KI.cable(KI.sag(T + Vector((tw / 2, 0, th * 0.35)), (R.x - rr * 0.9, R.y + rr * 0.3, zr + L1 * 0.3), 0.15 * s ** 0.5, 8), 0.025 * s ** 0.5)
    aviation = []
    for zz in (th * 0.5, th):
        m_, sk = KI.anim_emit((1.0, 0.06, 0.03), 10.0, "aviation")
        K.sphere(0.035 * s ** 0.5, T + Vector((tw / 2 + 0.03, -tw / 2 - 0.03, zz)), m_, segs=12, rings=6)
        aviation.append(sk)
    for i, sk in enumerate(aviation):
        an.value(sk, lambda t, i=i: 1.0 + 16.0 * KI.blink(t, 2, 0.3, i * 0.1))
    # propellant spheres (back-right) + feed lines
    for i, (fx, fy) in enumerate(((0.3, 0.32), (0.38, 0.1))):
        c = Vector((fx * w, fy * d, z0))
        r = 0.085 * s
        K.sphere(r, c + Vector((0, 0, r + 0.25 * s ** 0.5)), st.mat((0.75, 0.76, 0.74), name="sphere_white", rust=0.0), segs=40, rings=20)
        K.torus(r * 1.003, 0.012 * s ** 0.5, c + Vector((0, 0, r + 0.25 * s ** 0.5)), acc, segs=48)
        for j in range(4):
            a = math.pi / 4 + j * math.pi / 2
            K.cyl(0.025 * s ** 0.5, 0.25 * s ** 0.5 + r, c + Vector((math.cos(a) * r * 0.75, math.sin(a) * r * 0.75, 0)), frame, verts=10)
        KI.pipe([c + Vector((0, -r * 0.5, 0.12)), Vector((c.x, R.y + mw * 0.3, z0 + 0.12)), Vector((R.x + mw / 2 + 0.05, R.y + mw * 0.3, z0 + 0.12 + i * 0.12))],
                r=0.035 * s ** 0.5, mat=st.mat((0.6, 0.6, 0.58) if i == 0 else (0.1, 0.25, 0.6), name=f"propline{i}"), flanges=True)
    # floodlight masts (back + side corners)
    lights = []
    for fx, fy in ((-0.44, 0.44), (0.44, 0.44), (-0.44, -0.44)):
        mp = Vector((fx * w, fy * d, z0))
        mh_ = 1.4 + 0.45 * s
        K.cyl(0.05 * s ** 0.5, mh_, mp, M.metal("steel", dirt=0.6), verts=12, r2=0.03 * s ** 0.5)
        aim = (R - mp).normalized()
        for j in range(3):
            KI.floodlight(mp + Vector((0.12 * (j - 1) * aim.y, -0.12 * (j - 1) * aim.x, mh_)), (aim.x, aim.y, -0.6), size=0.16 * s ** 0.5)
        lights.append({"pos": [mp.x, mp.y, z0 + mh_], "color": [1.0, 0.95, 0.85], "energy": 1.0, "flicker": False})
    # crawler-way markings + hazard stripes around the mount
    KI.ring(mw * 0.95, mw * 0.95 - 0.06, 0.006, (R.x, R.y, z0 + 0.003), M.painted((0.75, 0.55, 0.02), name="marking_y"), segs=64, bevel=0)
    vent = Vector((R.x + rr, R.y - rr * 0.3, zr + L1 + 0.05 * Hr + L2 * 0.5))
    return Rig(height=max(top, z0 + th + 0.25 * s) + 0.1, frames=8, fps=4, update=an, lights=lights,
               emitters=[{"pos": [vent.x, vent.y, vent.z], "type": "steam"},
                         {"pos": [R.x, R.y - mw / 2 - 0.2, z0 + mh * 0.4], "type": "steam"}])


# =========================================================================== orbital assembler
def orbital_assembler(spec, p):
    """Orbital module assembly hall: a hull section (ring frames, stringers, part-skinned) turning
    on a turntable inside a portal gantry with a travelling bridge crane lowering a skin panel,
    two welding robots throwing sparks, parts racks and a control pulpit."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    frame = st.frame()
    body = st.body()
    floor = M.concrete(0.3, tint=(0.75, 0.76, 0.76) if st.tier >= 3 else (0.85, 0.83, 0.78))
    K.box((w * 0.99, d * 0.99, 0.1), (0, 0, 0), floor, bevel=0.02, base=True)
    z0 = 0.1
    yel = M.painted((0.75, 0.55, 0.02), wear=0.4, name="lane")
    for sy in (-1, 1):
        K.box((w * 0.9, 0.05, 0.004), (0, sy * 0.45 * d, z0), yel, bevel=0, base=True)
    H0 = Vector((0.0, 0.02 * d, z0))
    # turntable + hull section
    K.cyl(0.27 * s, 0.12, H0, M.metal("dark_steel", dirt=0.6), verts=64)
    hull = []
    hr = 0.17 * s
    hh = 0.55 * s
    zt = z0 + 0.12
    hull.append(K.cyl(hr * 1.15, 0.08, (H0.x, H0.y, zt), body, verts=64, name="cradle"))
    skin = st.mat((0.78, 0.79, 0.8) if st.tier >= 2 else (0.55, 0.56, 0.56), name="hull_skin", rust=0.0, wear=0.3)
    hull.append(K.cyl(hr, hh * 0.42, (H0.x, H0.y, zt + 0.08), skin, verts=64, name="hull_skinned"))
    al = M.metal("aluminum", rough=0.3, dirt=0.2)
    nring = 6
    for i in range(nring + 1):
        hull.append(K.torus(hr, 0.018 * s ** 0.5, (H0.x, H0.y, zt + 0.08 + hh * (0.42 + 0.58 * i / nring)), al, segs=64, rsegs=8))
    nstr = 12
    for i in range(nstr):
        a = TAU * i / nstr
        hull.append(K.box((0.025 * s ** 0.5, 0.04 * s ** 0.5, hh * 0.6), (H0.x + math.cos(a) * hr, H0.y + math.sin(a) * hr, zt + 0.08 + hh * 0.4), al, bevel=0.003, base=True,
                          rot=(0, 0, a)))
    # skin panel band already fitted all round (12-fold, so the 1/12-turn loop stays seamless)
    for i in range(nstr):
        a = TAU * (i + 0.5) / nstr
        pnl = K.box((0.012, 2 * hr * math.sin(math.pi / nstr) * 1.02, hh * 0.19), (H0.x + math.cos(a) * hr * 1.01, H0.y + math.sin(a) * hr * 1.01, zt + 0.08 + hh * 0.43),
                    skin, bevel=0.003, base=True, rot=(0, 0, a))
        hull.append(pnl)
    hull.append(K.cyl(hr * 0.55, 0.1 * s ** 0.5, (H0.x, H0.y, zt + 0.08 + hh), st.accent_mat(), verts=48, name="docking_ring"))
    for i in range(nstr):  # lifting lugs, one per bay (12-fold like the rest of the hull)
        a = TAU * (i + 0.5) / nstr
        hull.append(K.box((0.1 * s ** 0.5, 0.06, 0.08 * s ** 0.5), (H0.x + math.cos(a) * hr * 1.0, H0.y + math.sin(a) * hr * 1.0, zt + 0.08 + hh * 0.2), M.painted((0.75, 0.55, 0.02), name="handle"), bevel=0.006,
                          rot=(0, 0, a)))
    hp = KI.pivot(H0, children=hull)
    an.spin(hp, 1.0 / 12.0)
    # portal gantry (4 columns + runway girders along X) and travelling bridge
    gx, gy = 0.42 * w, 0.4 * d
    gh = zt + hh + 0.45 * s
    gm = st.mat((0.7, 0.5, 0.03) if st.tier <= 2 else (0.5, 0.51, 0.52) if st.tier == 3 else (0.75, 0.76, 0.77), name="gantry", wear=0.6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.18 * s ** 0.5, 0.18 * s ** 0.5, gh - z0), (sx * gx, sy * gy, z0), gm, bevel=0.015, base=True, name="column")
            K.box((0.3 * s ** 0.5, 0.3 * s ** 0.5, 0.05), (sx * gx, sy * gy, z0), M.metal("dark_steel"), bevel=0.006, base=True)
    for sy in (-1, 1):
        KI.hbeam((-gx - 0.1, sy * gy, gh + 0.12), (gx + 0.1, sy * gy, gh + 0.12), 0.25 * s ** 0.5, 0.16 * s ** 0.5, gm)
        KI.strut((-gx, sy * gy, gh - 0.6), (-gx + 0.6, sy * gy, gh), 0.025 * s ** 0.5, gm)
        KI.strut((gx, sy * gy, gh - 0.6), (gx - 0.6, sy * gy, gh), 0.025 * s ** 0.5, gm)
    bridge = []
    bh = gh + 0.25 * s ** 0.5 + 0.02
    for sx in (-1, 1):
        bridge.append(KI.beam((sx * 0.14 * s ** 0.5, -gy - 0.15, bh), (sx * 0.14 * s ** 0.5, gy + 0.15, bh), 0.12 * s ** 0.5, 0.22 * s ** 0.5, gm, name="bridge"))
    for sy in (-1, 1):
        bridge.append(K.box((0.5 * s ** 0.5, 0.2 * s ** 0.5, 0.16 * s ** 0.5), (0, sy * gy, bh - 0.02), M.metal("dark_steel"), bevel=0.012, name="end_truck"))
    yh = H0.y - hr - 0.14 * s ** 0.5   # hoist lowers the panel just outside the hull wall
    bridge.append(K.box((0.42 * s ** 0.5, 0.36 * s ** 0.5, 0.2 * s ** 0.5), (0, yh, bh + 0.11 * s ** 0.5), M.metal("dark_steel", dirt=0.5), bevel=0.015, name="hoist"))
    hook_z = zt + hh + 0.2 * s ** 0.5
    for sx in (-1, 1):
        bridge.append(KI.strut((sx * 0.06, yh, bh), (sx * 0.06, yh, hook_z + 0.15), 0.006 * s ** 0.5, M.metal("steel"), verts=4))
    bridge.append(K.box((0.16 * s ** 0.5, 0.1 * s ** 0.5, 0.18 * s ** 0.5), (0, yh, hook_z + 0.05), M.painted((0.75, 0.55, 0.02), name="hookblock"), bevel=0.01))
    bridge.append(K.box((0.6 * s ** 0.5, 0.012, 0.4 * s ** 0.5), (0, yh, hook_z - 0.3 * s ** 0.5), skin, bevel=0.004, name="panel_load"))
    for sx in (-1, 1):
        bridge.append(KI.strut((0, yh, hook_z - 0.04), (sx * 0.28 * s ** 0.5, yh, hook_z - 0.1 * s ** 0.5), 0.004 * s ** 0.5, M.metal("steel"), verts=4))
    bp = KI.pivot((0, 0, 0), children=bridge)
    an.move(bp, lambda t: (gx * 0.55 * math.sin(TAU * t), 0, 0))
    _, bsk = KI.status_lamp((0.25 * s ** 0.5, gy, bh + 0.11 * s ** 0.5), (1.0, 0.55, 0.05), 12.0)
    an.value(bsk, lambda t: 14.0 * KI.blink(t, 4, 0.4))
    # welding robots (front-left and front-right of the hull)
    sparks = []
    weld_lights = []
    rob = M.painted((0.75, 0.42, 0.02), wear=0.25, grime=0.3, name="robot_orange") if st.tier < 4 else st.mat((0.78, 0.79, 0.8), name="robot_white", rust=0.0)
    for i, (rx, ry, yaw0) in enumerate(((-0.05 * s, -0.36 * s, math.radians(80)), (0.36 * s, -0.02 * s, math.radians(170)))):
        base = Vector((H0.x + rx, H0.y + ry, z0))
        tip, sk = KI.robot_arm(base, 0.32 * s ** 0.8, rob, an,
                               yaw=lambda t, y0=yaw0, i=i: y0 + 0.25 * math.sin(TAU * (t + i * 0.3)),
                               shoulder=lambda t, i=i: 0.35 + 0.12 * math.sin(TAU * (2 * t + i * 0.25)),
                               elbow=lambda t, i=i: 0.25 - 0.1 * math.sin(TAU * (2 * t + i * 0.25)),
                               tool_glow=(0.7, 0.85, 1.0))
        an.value(sk, lambda t, i=i: 6.0 + 30.0 * KI.blink(t, 8, 0.6, i * 0.37))
        L = KI.point_light(base + Vector((0, 0, 0.9 * s ** 0.8)), (0.7, 0.85, 1.0), 20.0, 0.05)
        an.energy(L, lambda t, i=i: 5.0 + 40.0 * KI.blink(t, 8, 0.6, i * 0.37))
        sparks.append({"pos": [base.x, base.y, base.z + 0.8 * s ** 0.8], "type": "sparks"})
        weld_lights.append({"pos": [base.x, base.y, base.z + 0.8 * s ** 0.8], "color": [0.7, 0.85, 1.0], "energy": 1.0, "flicker": True})
    # parts racks (back corners): stacked curved panels and tanks
    rack = st.frame()
    for rx, ry in ((-0.33 * w, 0.3 * d), (0.33 * w, 0.33 * d)):
        c = Vector((rx, ry, z0))
        for sx in (-1, 1):
            K.box((0.05, 0.6 * s ** 0.5, 0.9 * s ** 0.5), c + Vector((sx * 0.3 * s ** 0.5, 0, 0)), rack, bevel=0.005, base=True)
        for j in range(3):
            K.box((0.62 * s ** 0.5, 0.62 * s ** 0.5, 0.03), c + Vector((0, 0, 0.05 + j * 0.3 * s ** 0.5)), rack, bevel=0.004, base=True)
            for q in range(3):
                K.box((0.5 * s ** 0.5, 0.012, 0.18 * s ** 0.5), c + Vector((0, -0.18 * s ** 0.5 + q * 0.12 * s ** 0.5, 0.08 + j * 0.3 * s ** 0.5)), skin, bevel=0.003, base=True,
                      rot=(0.15, 0, 0))
    for j in range(2):
        tc = Vector((-0.38 * w + j * 0.42 * s ** 0.5, -0.05 * d, z0 + 0.2 * s ** 0.5))
        K.cyl(0.18 * s ** 0.5, 0.5 * s ** 0.5, tc, M.metal("aluminum", dirt=0.2), rot=K.AXES["y"], verts=32, base=False)
    # control pulpit (front-right corner)
    cpp = Vector((0.36 * w, -0.38 * d, z0))
    K.box((0.9 * s ** 0.5, 0.5 * s ** 0.5, 0.7 * s ** 0.5), cpp, st.mat((0.55, 0.56, 0.57) if st.tier < 4 else (0.04, 0.042, 0.046), name="pulpit"), bevel=0.02, base=True)
    KI.window((cpp.x - 0.1, cpp.y - 0.25 * s ** 0.5 - 0.01, z0 + 0.45 * s ** 0.5), 0.6 * s ** 0.5, 0.2 * s ** 0.5, "-y", lit=True, warm=(0.5, 0.8, 1.0))
    sl, socks = KI.stack_light(cpp + Vector((0.35 * s ** 0.5, 0, 0.7 * s ** 0.5)))
    an.value(socks[2], lambda t: 6.0)
    return Rig(height=bh + 0.4 * s ** 0.5, frames=16, fps=10, update=an, lights=weld_lights, emitters=sparks)


ARCHETYPES = KI.with_bounds({"launch_pad": launch_pad, "orbital_assembler": orbital_assembler})
