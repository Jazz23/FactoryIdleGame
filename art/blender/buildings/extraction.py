"""Extraction archetypes: drill, pumpjack, water_pump, gas_well."""
import math

from mathutils import Vector

import kit as K
import kit_industry as KI
import materials as M
from buildings import Rig

TAU = KI.TAU


def _size(spec):
    w, d = spec.get("size", [2, 2])
    return float(w), float(d)


# =========================================================================== drill
def drill(spec, p):
    """Crawler-style blast-hole / auger drill on a skid: lattice mast, top-drive head that
    feeds down and retracts while the auger string spins, diesel/electric power pack with a
    radiator fan, ore discharge belt."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    body = st.body()
    frame = st.frame()
    steel = st.steel()
    ore = KI.ore_material(p.get("ore", "iron") if isinstance(p.get("ore"), str) else "iron")

    sk, z0 = K.skid(w * 0.96, d * 0.96, 0.16, paint=st.frame_col)
    K.hazard_edge(w * 0.96, d * 0.96, z0, width=0.06)

    # ---- mast
    B = Vector((-0.12 * w, 0.06 * d, z0))
    m = 0.2 * s
    H = 0.9 + 0.85 * s
    leg_r = 0.026 + 0.01 * s
    KI.lattice(B, H, 2 * m, 2 * m, mat=frame, leg_r=leg_r, brace_r=0.01 + 0.004 * s, bay=0.38 + 0.12 * s,
               faces=(False, False, True, True))
    for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1))):
        for zz in (z0 + 0.12, z0 + H):
            KI.strut(B + Vector((ax * m, ay * m, zz - z0)), B + Vector((bx * m, by * m, zz - z0)), leg_r * 0.8, frame, verts=8)
    # gusset feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.16 * s ** 0.5, 0.16 * s ** 0.5, 0.03), B + Vector((sx * m, sy * m, 0.015)), frame, bevel=0.006)
    # crown block + sheave
    top = B + Vector((0, 0, H))
    K.box((2 * m + 0.12, 2 * m + 0.12, 0.1), top, body, bevel=0.012, base=True)
    KI.spoked_wheel(top + Vector((0, 0, 0.1 + 0.12 * s ** 0.5)), 0.12 * s ** 0.5, 0.05, spokes=5, mat=steel, rot=K.AXES["y"])
    K.box((0.05, 0.16 * s ** 0.5, 0.18 * s ** 0.5), top + Vector((0.04, 0, 0.1)), frame, base=True, bevel=0.005)
    K.box((0.05, 0.16 * s ** 0.5, 0.18 * s ** 0.5), top + Vector((-0.04, 0, 0.1)), frame, base=True, bevel=0.005)
    _, bsock = KI.status_lamp(top + Vector((m * 0.7, -m * 0.7, 0.1)), (1.0, 0.1, 0.05), 12.0)
    an.value(bsock, lambda t: 14.0 * KI.blink(t, 2, 0.35))
    KI.floodlight(B + Vector((m + 0.02, -m - 0.02, H * 0.92)), (-0.4, 0.4, -1.0), size=0.12 + 0.03 * s)

    # ---- collar + cuttings
    KI.ring(0.14 * s, 0.07 * s, 0.1, B + Vector((0, 0, 0.05)), M.metal("cast_iron", dirt=1.0), segs=32)
    K.bolts(B + Vector((0, 0, 0.1)), 0.11 * s, 8, r=0.012 + 0.003 * s)
    KI.rock_pile(B + Vector((0.02 * s, -0.04 * s, 0.0)), 0.36 * s, 0.32 * s, 0.1 + 0.03 * s, int(26 * s), ore, seed=4,
                 rmin=0.025 * s ** 0.5, rmax=0.055 * s ** 0.5)

    # ---- moving drill assembly (head + string)
    z_top = z0 + H * 0.8
    z_bot = z0 + H * 0.42
    head_h = 0.16 + 0.07 * s
    hw = 2 * m * 0.86
    head = []
    head.append(K.box((hw, hw * 0.8, head_h), B + Vector((0, 0, z_top - z0)), body, bevel=0.015, base=True, name="gearbox"))
    head.append(K.box((hw * 1.05, hw * 0.84, 0.03), B + Vector((0, 0, z_top - z0 + head_h * 0.55)), steel, bevel=0.006))
    mot_r = hw * 0.3
    head.append(K.cyl(mot_r, 0.22 + 0.1 * s, B + Vector((0, 0, z_top - z0 + head_h)), M.painted((0.06, 0.16, 0.32), wear=st.wear, grime=st.grime, name="motor_paint"), verts=32))
    for i in range(10):
        a = TAU * i / 10
        head.append(K.box((0.018, 0.018, 0.18 + 0.08 * s), B + Vector((math.cos(a) * mot_r, math.sin(a) * mot_r, z_top - z0 + head_h + 0.02)),
                          M.painted((0.06, 0.16, 0.32), wear=st.wear, grime=st.grime, name="motor_paint"), bevel=0.003, base=True))
    head.append(K.cyl(mot_r * 0.8, 0.04, B + Vector((0, 0, z_top - z0 + head_h + 0.22 + 0.1 * s)), M.metal("dark_steel"), verts=32))
    head.append(K.box((mot_r * 0.9, mot_r * 0.7, mot_r * 0.5), B + Vector((mot_r * 0.9, -mot_r * 0.2, z_top - z0 + head_h + 0.08)), body, bevel=0.008))
    for sx in (-1, 1):  # guide shoes riding on the front legs
        head.append(K.box((0.08, 0.1, head_h * 1.1), B + Vector((sx * m, -m, z_top - z0 + head_h * 0.5)), M.metal("dark_steel"), bevel=0.008))
    head.append(K.cyl(0.05 * s ** 0.5, 0.06, B + Vector((0, 0, z_top - z0 - 0.06)), M.metal("dark_steel"), verts=20))
    head += KI.hazard_band(B + Vector((0, -hw * 0.4 - 0.004, z_top - z0 + head_h * 0.25)), hw * 0.9, 0.04),
    # drill string (spins)
    rod_r = 0.03 * s ** 0.7
    L = z_top - z0 + 0.35
    string = [K.cyl(rod_r, L, B + Vector((0, 0, -0.35)), M.metal("steel", rough=0.3, dirt=0.6), verts=8, bevel=0.004, name="rod")]
    flight_top = (z_bot - z0) * 0.9
    string.append(KI.helix(rod_r * 0.9, 0.11 * s, 0.13 * s, (flight_top + 0.35) / (0.13 * s), B + Vector((0, 0, -0.35)),
                           M.metal("steel", rough=0.35, dirt=0.9), thick=0.012))
    string.append(K.cyl(rod_r * 1.6, 0.08, B + Vector((0, 0, z_top - z0 - 0.15)), M.metal("dark_steel"), verts=6, bevel=0.004))
    string += K.bolts(B + Vector((0, 0, z_top - z0 - 0.07)), rod_r * 1.25, 6, r=0.01)
    spin = KI.pivot(B, name="string")
    KI.bind(string, spin)
    headp = KI.pivot(B, name="head")
    KI.bind(head + [spin], headp)
    an.spin(spin, 2.0)

    # feed cylinders on the side faces, rods follow the head
    rods = []
    for sx in (-1, 1):
        a = B + Vector((sx * (m + 0.07), 0.0, 0.06))
        b = B + Vector((sx * (m + 0.07), 0.0, z_top - z0 + head_h * 0.4))
        objs, rp, _ = KI.hydraulic(a, b, r=0.035 + 0.01 * s, mat=st.accent_mat() if st.tier != 2 else M.painted((0.04, 0.04, 0.045), name="hyd_dark"))
        rods.append(rp)
        K.box((0.12, 0.08, 0.05), b + Vector((-sx * 0.04, 0, 0.0)), M.metal("dark_steel"), bevel=0.006)

    def head_z(t):
        if t < 0.72:
            return -(z_top - z_bot) * KI.smooth01(t / 0.72)
        return -(z_top - z_bot) * (1 - KI.smooth01((t - 0.72) / 0.28))
    an.move(headp, lambda t: (0, 0, head_z(t)))
    for rp in rods:
        an.move(rp, lambda t: (0, 0, head_z(t)))
    # bracket that ties each cylinder rod eye to the head
    # (rendered as part of head: small lugs)
    for sx in (-1, 1):
        lug = K.box((0.1, 0.06, 0.05), B + Vector((sx * (m + 0.03), 0, z_top - z0 + head_h * 0.4)), M.metal("dark_steel"), bevel=0.006)
        KI.bind([lug], headp)

    # ---- power pack
    px0, px1 = max(B.x + m + 0.18, 0.06 * w), 0.46 * w
    py0, py1 = 0.0 * d - 0.05, 0.45 * d
    pw, pd = px1 - px0, py1 - py0
    ph = 0.5 + 0.28 * s
    pc = Vector(((px0 + px1) / 2, (py0 + py1) / 2, z0))
    K.box((pw, pd, ph), pc, body, bevel=0.02, base=True, name="powerpack")
    K.box((pw + 0.04, pd + 0.04, 0.04), pc + Vector((0, 0, ph)), body, bevel=0.01, base=True)
    K.box((pw * 0.98, pd * 0.98, 0.08), pc, frame, bevel=0.006, base=True)
    KI.louvers(Vector((pc.x - pw * 0.15, py0 - 0.012, z0 + ph * 0.55)), pw * 0.5, ph * 0.45, "-y")
    KI.louvers(Vector((px1 + 0.012, pc.y + pd * 0.12, z0 + ph * 0.55)), pd * 0.5, ph * 0.5, "+x")
    for xx in (pc.x + pw * 0.28,):  # door seam + handle on -Y
        K.box((0.006, 0.006, ph * 0.86), (xx, py0 - 0.003, z0 + ph * 0.5), M.plastic((0.02, 0.02, 0.02)), bevel=0)
        K.box((0.018, 0.025, 0.09), (xx + 0.05, py0 - 0.012, z0 + ph * 0.55), M.metal("chrome"), bevel=0.003)
    KI.plate_sign((pc.x + pw * 0.36, py0 - 0.006, z0 + ph * 0.78), 0.12, 0.08, "-y", color=(0.8, 0.8, 0.78))
    fr = min(pw, pd) * 0.34
    fobjs, rotor = K.fan(pc + Vector((-pw * 0.12, pd * 0.08, ph + 0.05)), r=fr, axis="z", blades=7, mat=M.metal("aluminum", dirt=0.7))
    an.spin(rotor, 3.0 / 7.0)
    K.cyl(fr * 1.12, 0.05, pc + Vector((-pw * 0.12, pd * 0.08, ph)), M.metal("dark_steel"), verts=40)
    sl, socks = KI.stack_light(pc + Vector((pw * 0.38, -pd * 0.36, ph + 0.04)))
    an.value(socks[2], lambda t: 6.0)
    an.value(socks[1], lambda t: 8.0 * KI.blink(t, 4, 0.5))
    emitters = []
    if p.get("smoke", st.tier <= 2) or st.variant == "burner":  # diesel/burner: exhaust stack with rain cap
        ex = pc + Vector((pw * 0.32, pd * 0.32, ph))
        K.cyl(0.035 + 0.01 * s, 0.35 + 0.15 * s, ex, M.metal("dark_steel", dirt=1.0), verts=16)
        K.cyl(0.05 + 0.01 * s, 0.03, ex + Vector((0, 0, 0.36 + 0.15 * s)), M.metal("dark_steel", dirt=1.0), verts=16,
              rot=(0.4, 0, 0))
        emitters.append({"pos": [ex.x, ex.y, ex.z + 0.4 + 0.15 * s], "type": "smoke"})
    # hoses: power pack -> mast foot
    KI.bellows_hose([(px0, pc.y - pd * 0.2, z0 + 0.3), (B.x + m + 0.15, pc.y - pd * 0.2, z0 + 0.2), (B.x + m + 0.07, B.y, z0 + 0.25)], 0.022)
    KI.bellows_hose([(px0, pc.y - pd * 0.1, z0 + 0.4), (B.x + m + 0.2, pc.y - pd * 0.05, z0 + 0.3), (B.x + m + 0.07, B.y + 0.08, z0 + 0.35)], 0.018)

    # ---- discharge belt along the front edge (ore leaving the rig)
    by = -0.37 * d
    bx0 = B.x - 0.05 * s
    KI.frustum((0.3 * s ** 0.5, 0.26 * s ** 0.5), (0.45 * s ** 0.5, 0.4 * s ** 0.5), 0.22, (bx0 + 0.12, by, z0 + 0.42),
               body, open_top=True, thick=0.015)
    KI.belt_conveyor((bx0, by), (w / 2 - 0.02, by), 0.22 + 0.06 * s, z0 + 0.36, st, n_items=max(4, int((w / 2 - bx0) / 0.22)),
                     item_mat=ore, anim=an, seed=11, legs=True)
    # control cabinet front-left
    KI.cabinet((-0.36 * w, -0.32 * d + 0.0, z0), 0.0, w=0.3 + 0.05 * s, d=0.2, h=0.55 + 0.15 * s, mat=st.mat((0.55, 0.56, 0.54), wear=0.5))
    KI.cable(KI.sag((-0.36 * w + 0.1, -0.32 * d + 0.08, z0 + 0.6 + 0.15 * s), (B.x - m, B.y - m, z0 + 0.9), 0.12))
    K.scatter_debris(w * 0.9, d * 0.9, 6, seed=2, mat=st.steel("iron"))

    lights = [{"pos": [B.x + m, B.y - m, z0 + H * 0.9], "color": [1.0, 0.92, 0.78], "energy": 0.6, "flicker": False}]
    if st.variant == "plasma" or p.get("glow"):
        gcol = st.glow_col
        pm, ps = KI.anim_emit(gcol, 10.0, "plasma_bore")
        KI.ring(0.075 * s, 0.05 * s, 0.03, B + Vector((0, 0, 0.11)), pm, segs=32, bevel=0)
        hm, hs = KI.soft_glow(gcol, 5.0, rim=False, name="plasma_halo", power=1.5)
        K.cyl(0.07 * s, 0.25, B + Vector((0, 0, 0.1)), hm, verts=24, r2=0.02 * s, bevel=0)
        pl = KI.point_light(B + Vector((0, -0.2, 0.4)), gcol, 30.0 * s, 0.1)
        an.value(ps, lambda t: 8.0 + 6.0 * KI.flicker(t, 0.2, 1.0))
        an.energy(pl, lambda t: 30.0 * s * (0.6 + 0.4 * KI.flicker(t, 0.2, 1.0)))
        lights.append({"pos": [B.x, B.y, z0 + 0.3], "color": list(gcol), "energy": 1.0, "flicker": True})
    height = z0 + H + 0.1 + 0.26 * s ** 0.5
    return Rig(height=height, frames=16, fps=12, update=an, lights=lights, emitters=emitters)


# =========================================================================== pumpjack
def _capture_into(builder, spec, p, offset):
    """Run another builder, then hang everything it created on a pivot moved by `offset`."""
    import bpy
    before = set(bpy.data.objects)
    rig = builder(spec, p)
    new = [o for o in bpy.data.objects if o not in before and o.parent is None]
    piv = KI.pivot((0, 0, 0), name="sub")
    KI.bind(new, piv)
    piv.location = Vector(offset)
    return rig


def _offshore(spec, p):
    """Offshore production platform: braced tubular jacket standing in rippling sea, plated deck
    with a pumpjack, drilling derrick, accommodation block with helideck and a pedestal crane."""
    KI.begin()
    st = KI.Style(p)
    w, d = _size(spec)
    s = min(w, d)
    wmat, wsocks = _water_material("sea")
    K.box((w * 0.99, d * 0.99, 0.04), (0, 0, 0), wmat, bevel=0, base=True, name="sea")
    zd = 1.0 + 0.12 * s
    frame = st.mat((0.6, 0.45, 0.03) if st.tier < 4 else (0.55, 0.56, 0.57), name="jacket_paint", wear=1.1)
    lx, ly = 0.38 * w, 0.38 * d
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.cyl(0.12 * s ** 0.5, zd, (sx * lx, sy * ly, 0), frame, verts=20, name="jacket_leg")
            K.torus(0.13 * s ** 0.5, 0.02, (sx * lx, sy * ly, 0.08), M.metal("dark_steel", dirt=1.0))
    for zz in (0.35, zd - 0.25):
        for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            KI.strut((ax * lx, ay * ly, zz), (bx * lx, by * ly, zz), 0.045 * s ** 0.5, frame, verts=10)
    for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1))):
        KI.strut((ax * lx, ay * ly, 0.35), (bx * lx, by * ly, zd - 0.25), 0.035 * s ** 0.5, frame, verts=8)
        KI.strut((bx * lx, by * ly, 0.35), (ax * lx, ay * ly, zd - 0.25), 0.035 * s ** 0.5, frame, verts=8)
    K.box((w * 0.9, d * 0.9, 0.22), (0, 0, zd), st.frame(), bevel=0.02, base=True, name="deck_girder")
    K.box((w * 0.9, d * 0.9, 0.03), (0, 0, zd + 0.22), M.tread_plate(0.8, rust=st.tier == 1), bevel=0.006, base=True)
    zt = zd + 0.25
    K.railing([(-0.44 * w, -0.44 * d, zt), (0.44 * w, -0.44 * d, zt), (0.44 * w, 0.44 * d, zt)], 0.9, st.safety())
    # pumpjack on the deck (front-centre)
    sub = dict(spec)
    sub["size"] = [w * 0.5, d * 0.36]
    q = dict(p)
    q.pop("variant", None)
    rig = _capture_into(pumpjack, sub, q, (0.05 * w, -0.2 * d, zt))
    KI.begin()
    # derrick (back-left)
    dp = Vector((-0.27 * w, 0.24 * d, zt))
    dh = 2.2 + 0.8 * s
    KI.lattice(dp, dh, 0.42 * s ** 0.8, 0.12 * s ** 0.8, mat=frame, leg_r=0.03 * s ** 0.5, brace_r=0.012 * s ** 0.5, bay=0.5)
    K.box((0.5 * s ** 0.8, 0.5 * s ** 0.8, 0.1), dp, st.frame(), bevel=0.01, base=True)
    K.box((0.2 * s ** 0.8, 0.2 * s ** 0.8, 0.12), dp + Vector((0, 0, dh)), st.frame(), bevel=0.01, base=True)
    _, bs = KI.status_lamp(dp + Vector((0, 0, dh + 0.12)), (1.0, 0.08, 0.03), 12.0)
    # accommodation block + helideck (back-right)
    ap = Vector((0.24 * w, 0.26 * d, zt))
    ah = 1.0 + 0.2 * s
    aw_, ad_ = 0.38 * w, 0.3 * d
    K.box((aw_, ad_, ah), ap, st.mat((0.75, 0.76, 0.74), name="quarters"), bevel=0.02, base=True, name="quarters")
    for i in range(4):
        KI.window((ap.x - aw_ * 0.35 + i * aw_ * 0.23, ap.y - ad_ / 2 - 0.01, zt + ah * 0.6), aw_ * 0.12, ah * 0.18, "-y", lit=i % 2 == 0)
    hz = zt + ah + 0.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.cyl(0.04, 0.35, (ap.x + sx * aw_ * 0.4, ap.y + sy * ad_ * 0.4, zt + ah), st.frame(), verts=8)
    hr = min(aw_, ad_) * 0.75
    K.cyl(hr, 0.06, (ap.x, ap.y, hz), M.painted((0.05, 0.12, 0.06), wear=0.4, name="helideck"), verts=8, bevel=0.01)
    KI.ring(hr * 0.8, hr * 0.74, 0.004, (ap.x, ap.y, hz + 0.06), M.painted((0.75, 0.6, 0.03), name="marking_y"), segs=48, bevel=0)
    for dx in (-0.25, 0.25):
        K.box((0.05, hr * 0.7, 0.004), (ap.x + dx * hr, ap.y, hz + 0.062), M.painted((0.8, 0.8, 0.78), name="marking_w"), bevel=0)
    K.box((hr * 0.5, 0.05, 0.004), (ap.x, ap.y, hz + 0.062), M.painted((0.8, 0.8, 0.78), name="marking_w"), bevel=0)
    # pedestal crane (front-left)
    cp_ = Vector((-0.34 * w, -0.32 * d, zt))
    K.cyl(0.14 * s ** 0.5, 0.9, cp_, st.body(), verts=20)
    K.box((0.4, 0.35, 0.3), cp_ + Vector((0, 0, 0.9)), st.body(), bevel=0.02, base=True)
    tip = cp_ + Vector((0.6 * s ** 0.8, 0.5 * s ** 0.8, 0.9 + 1.4 * s ** 0.6))
    KI.box_truss(cp_ + Vector((0.1, 0.05, 1.05)), tip, 0.18, 0.18, st.body(), chord_r=0.02, web_r=0.008)
    KI.strut(tip, tip - Vector((0, 0, 1.0)), 0.006, M.metal("steel"), verts=4)
    K.box((0.1, 0.1, 0.12), tip - Vector((0, 0, 1.06)), M.painted((0.75, 0.55, 0.02), name="hookblock"), bevel=0.01)
    an = KI.Anim()
    for i, sock in enumerate(wsocks):
        an.value(sock, lambda t, i=i: -TAU * (1 + i) * t)
    an.value(bs, lambda t: 1 + 13 * KI.blink(t, 2, 0.3))

    def update(t):
        rig.update(t)
        an(t)
    return Rig(height=max(dp.z + dh + 0.3, hz + 0.3, tip.z + 0.2), frames=16, fps=8, update=update,
               lights=[{"pos": [ap.x, ap.y - ad_ / 2, zt + ah * 0.6], "color": [1.0, 0.85, 0.6], "energy": 0.5, "flicker": False}],
               emitters=[{"pos": [dp.x, dp.y, dp.z + dh], "type": "steam"}])


def pumpjack(spec, p):
    """Beam pumping unit ("nodding donkey"): samson post, walking beam with horsehead, crank
    arms with counterweights driven by a gear reducer, pitman arms, bridle + polished rod
    into a wellhead stuffing box. Solved 4-bar linkage, one stroke per loop.
    variant 'offshore': the unit sits on a jacket platform in the sea with derrick + quarters."""
    if str(p.get("variant", "")) == "offshore":
        return _offshore(spec, p)
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    body = st.body()
    frame = st.frame()
    dark = st.accent_mat() if st.tier in (2, 4) else st.mat((0.03, 0.03, 0.033), name="cw_paint")

    zb = 0.14
    KI.concrete_pad(w * 0.94, d * 0.62, zb, st.concrete())
    # base frame
    xw = 0.37 * w
    xp = 0.06 * w
    R = xw - xp
    b = 0.31 * w
    xg = xp - b
    zp = zb + 0.55 * w + 0.25
    zc = zb + 0.45 * (zp - zb)
    rc = 0.4 * b
    by = 0.16 * d
    for sy in (-1, 1):
        K.box((xp + 0.2 * w - (-0.47 * w), 0.1, 0.14), ((xp + 0.2 * w + -0.47 * w) / 2, sy * by, zb), frame, bevel=0.008, base=True)
    for xx in (-0.45 * w, xg - 0.32 * w * 0.5, xp, xp + 0.18 * w):
        K.box((0.1, 2 * by + 0.1, 0.12), (xx, 0, zb), frame, bevel=0.008, base=True)
    z1 = zb + 0.14

    # ---- samson post
    sad = Vector((xp, 0, zp - 0.12))
    for sy in (-1, 1):
        KI.beam((xp + 0.16 * w, sy * by, z1), sad + Vector((0.02, sy * 0.06, 0)), 0.09 + 0.02 * s, 0.07 + 0.02 * s, body)
        KI.beam((xp - 0.14 * w, sy * by, z1), sad + Vector((-0.02, sy * 0.06, 0)), 0.08 + 0.02 * s, 0.06 + 0.02 * s, body)
    for zz in (0.35, 0.65):
        f = zz
        ya = by + (0.06 - by) * f
        xa = xp + 0.16 * w + (0.02 - 0.16 * w) * f
        KI.beam((xa, -ya, z1 + (sad.z - z1) * f), (xa, ya, z1 + (sad.z - z1) * f), 0.05, 0.05, frame)
    K.box((0.24, 0.24 + 0.04 * s, 0.1), sad, M.metal("dark_steel"), bevel=0.01, base=True, name="saddle")
    KI.ladder(Vector((xp + 0.16 * w + 0.05, 0.0, z1)), zp - z1 - 0.3, rot_z=math.pi / 2, w=0.32, mat=st.safety())

    # ---- walking beam + horsehead (pivot at saddle bearing)
    pv = Vector((xp, 0, zp))
    beam_objs = []
    bh = 0.16 + 0.05 * s
    beam_objs.append(K.ibeam(R + b + 0.05, bh, 0.12 + 0.03 * s, (xp + (R - 0.18 * w - b) / 2, 0, zp + bh / 2 - 0.02), mat=body))
    beam_objs.append(K.box((0.2, 0.2 + 0.04 * s, 0.08), pv + Vector((0, 0, -0.06)), M.metal("dark_steel"), bevel=0.01))
    beam_objs.append(K.cyl(0.06, 0.34 + 0.06 * s, pv + Vector((0, 0, -0.06)), M.metal("steel"), rot=(math.pi / 2, 0, 0), verts=16, base=False))
    # horsehead: arc face of radius R about the pivot
    a0, a1 = math.radians(-24), math.radians(26)
    pts = []
    n = 14
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((R * math.cos(a), R * math.sin(a)))
    back = R - 0.22 * w
    pts += [(back, R * math.sin(a1) + 0.02), (back - 0.06 * w, bh * 0.3), (back - 0.04 * w, -bh * 0.1), (back, R * math.sin(a0) * 0.6)]
    pts = [(x, z) for x, z in pts]
    hh = KI.extrude_poly([(x, z) for x, z in pts], 0.2 + 0.06 * s, (0, 0, 0), body, rot=(math.pi / 2, 0, 0), bevel=0.012, name="horsehead")
    hh.location = pv
    beam_objs.append(hh)
    # face plate on the arc (wire-rope saddle)
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        seg = K.box((0.03, 0.22 + 0.06 * s, 2 * R * math.sin((a1 - a0) / n / 2) + 0.004), pv + Vector((R * math.cos(a), 0, R * math.sin(a))),
                    M.metal("dark_steel", dirt=0.8), bevel=0.003)
        seg.rotation_euler = (0, -a, 0)
        beam_objs.append(seg)
    # tail: equalizer bearing + cross bar
    e = 0.12 + 0.02 * s
    tail = pv + Vector((-b, 0, -e))
    beam_objs.append(K.box((0.16, 0.16, e), pv + Vector((-b, 0, -e)), M.metal("dark_steel"), bevel=0.01, base=True))
    gb_hy = 0.13 + 0.06 * s
    yarm = gb_hy + 0.08
    beam_objs.append(K.cyl(0.05, 2 * yarm + 0.12, tail, st.steel(), rot=(math.pi / 2, 0, 0), verts=16, base=False))
    beam_objs.append(K.box((0.12, 2 * yarm, 0.1), tail + Vector((0, 0, 0.02)), body, bevel=0.01))
    beamp = KI.pivot(pv, name="walking_beam")
    KI.bind(beam_objs, beamp)

    # ---- gear reducer + crank
    gx = xg
    K.box((0.3 + 0.06 * s, 2 * gb_hy, zc - z1 - 0.1), (gx, 0, z1), frame, bevel=0.01, base=True)  # pedestal
    gr = 0.15 + 0.05 * s
    K.box((0.5 + 0.12 * s, 2 * gb_hy, gr * 1.1), (gx - 0.06, 0, zc - 0.12 - gr * 0.3), body, bevel=0.03, base=True, name="reducer")
    K.cyl(gr, 2 * gb_hy, (gx, 0, zc), body, rot=(math.pi / 2, 0, 0), verts=40, base=False)
    K.cyl(gr * 0.75, 2 * gb_hy + 0.04, (gx - 0.18 - 0.05 * s, 0, zc - gr * 0.35), body, rot=(math.pi / 2, 0, 0), verts=36, base=False)
    K.bolts(Vector((gx, -gb_hy - 0.005, zc)), gr * 0.85, 12, axis="-y", r=0.012)
    crank = []
    crank.append(K.cyl(0.07, 2 * yarm + 0.14, (gx, 0, zc), st.steel(), rot=(math.pi / 2, 0, 0), verts=16, base=False))
    for sy in (-1, 1):
        yy = sy * yarm
        arm = K.box((rc + 1.5 * rc + 0.1, 0.08, 0.14 + 0.05 * s), (gx + (rc - 1.5 * rc) / 2, yy, zc), dark, bevel=0.012, name="crank_arm")
        crank.append(arm)
        crank.append(K.cyl(0.045, 0.12, (gx + rc, yy + sy * 0.05, zc), M.metal("steel"), rot=(math.pi / 2, 0, 0), verts=12, base=False))
        cwp = [(-0.75 * rc, -0.42 * rc)]
        for i in range(9):
            a = math.pi - 0.62 + 1.24 * i / 8
            cwp.append((1.75 * rc * math.cos(a), -1.75 * rc * math.sin(a)))
        cwp.append((-0.75 * rc, 0.42 * rc))
        cw = KI.extrude_poly(cwp, 0.16 + 0.04 * s, (gx, yy + sy * 0.05, zc), dark, rot=(math.pi / 2, 0, 0), bevel=0.014, name="counterweight")
        crank.append(cw)
        crank.append(K.box((0.03, 0.15 + 0.03 * s, 0.04), (gx - 1.45 * rc, yy + sy * 0.05, zc + 0.5 * rc), M.hazard(8.0), bevel=0.003))
    crankp = KI.pivot((gx, 0, zc), name="crank")
    KI.bind(crank, crankp)

    # pitman arms (solved each frame)
    T0 = Vector((xp - b, 0, zp - e))
    Lp = (T0 - Vector((gx, 0, zc))).length
    pit = []
    for sy in (-1, 1):
        o = K.box((0.07, 0.06, Lp), (0, 0, 0), body, bevel=0.01, base=True, name="pitman")
        pit.append((o, sy * (yarm + 0.08)))

    def rot_xz(x, z, ang):  # rotation about +Y by ang
        return x * math.cos(ang) + z * math.sin(ang), -x * math.sin(ang) + z * math.cos(ang)

    def solve(t):
        alpha = -TAU * t
        px, pz = rot_xz(rc, 0, alpha)
        P = Vector((gx + px, 0, zc + pz))
        lo, hi = -0.9, 0.9
        for _ in range(40):
            th = (lo + hi) / 2
            tx, tz = rot_xz(-b, -e, -th)
            T = Vector((xp + tx, 0, zp + tz))
            if (T - P).length > Lp:
                lo = th
            else:
                hi = th
        return alpha, (lo + hi) / 2, P, T

    th0 = solve(0.0)[1]

    # ---- wellhead + bridle / polished rod
    zsb = zb + 0.55 + 0.05 * s
    K.cyl(0.13 + 0.02 * s, 0.12, (xw, 0, zb), M.metal("cast_iron", dirt=0.9), verts=24)
    K.cyl(0.08 + 0.01 * s, zsb - zb - 0.12, (xw, 0, zb + 0.12), st.mat((0.4, 0.04, 0.02), name="wh_red"), verts=20)
    for zz in (zb + 0.12, zb + 0.32):
        K.flange((xw, 0, zz), 0.09 + 0.01 * s, "z")
    tee_z = zb + 0.42
    KI.pipe([(xw, -0.06, tee_z), (xw, -0.4 * d, tee_z), (xw, -0.4 * d, zb + 0.1), (xw, -0.49 * d, zb + 0.1)], r=0.04 + 0.01 * s,
            mat=st.mat((0.4, 0.4, 0.38), name="pipe_paint"))
    KI.gate_valve((xw, -0.22 * d, tee_z), "y", r=0.04 + 0.01 * s, wheel_up="z")
    g, needle = KI.gauge((xw + 0.12, -0.02, tee_z + 0.05), "+x", 0.035)
    KI.strut((xw, -0.0, tee_z + 0.05), (xw + 0.12, -0.0, tee_z + 0.05), 0.01, M.metal("brass"))
    an.rotate(needle, lambda t: 0.6 + 0.25 * math.sin(TAU * t))
    K.cyl(0.07, 0.12, (xw, 0, zsb - 0.12), M.metal("brass", dirt=0.8), verts=20)  # stuffing box
    zcar0 = zp + R * math.sin(th0) - 0.0
    bl = zp - R * math.sin(math.radians(22)) - (zsb + 0.25)
    rod = []
    zcar = zcar0 - bl
    rod.append(K.box((0.06, 0.26 + 0.06 * s, 0.05), (xw, 0, zcar), M.metal("dark_steel"), bevel=0.006, name="carrier"))
    rod.append(K.cyl(0.018, zcar - zsb + 0.5 + R * 0.5, (xw, 0, zsb - R * 0.5 - 0.3), M.metal("chrome"), verts=12, name="polished_rod"))
    rod.append(K.cyl(0.035, 0.08, (xw, 0, zcar + 0.03), M.metal("dark_steel"), verts=12))
    for sy in (-1, 1):
        rod.append(KI.strut((xw, sy * (0.1 + 0.02 * s), zcar), (xw, sy * (0.1 + 0.02 * s), zcar0 - 0.02), 0.009, M.metal("steel", dirt=0.9), verts=6))
    rodp = KI.pivot((xw, 0, zcar), name="bridle")
    KI.bind(rod, rodp)

    # ---- prime mover (back, +Y side) + belt guard
    mx = -0.43 * w
    KI.motor((mx + 0.08, 0.08 * d, z1 + 0.22 + 0.04 * s), axis="y", r=0.15 + 0.04 * s, length=0.4 + 0.1 * s,
             mat=M.painted((0.06, 0.16, 0.3), wear=st.wear, grime=st.grime, name="motor_paint"))
    K.box((0.4 + 0.1 * s, 0.6 + 0.1 * s, 0.07), (mx + 0.08, 0.08 * d, z1), frame, bevel=0.008, base=True)
    gy = gb_hy + 0.12
    gp = [(mx + 0.08, z1 + 0.22 + 0.04 * s), (gx - 0.18 - 0.05 * s, zc - gr * 0.35)]
    rr = [0.14 + 0.02 * s, 0.24 + 0.05 * s]
    poly = []
    for k, ((cx_, cz_), r_) in enumerate(zip(gp, rr)):
        dx, dz = gp[1][0] - gp[0][0], gp[1][1] - gp[0][1]
        base = math.atan2(dz, dx)
        rng = (base + math.pi / 2, base + 3 * math.pi / 2) if k == 0 else (base - math.pi / 2, base + math.pi / 2)
        for i in range(13):
            a = rng[0] + (rng[1] - rng[0]) * i / 12
            poly.append((cx_ + r_ * math.cos(a), cz_ + r_ * math.sin(a)))
    KI.extrude_poly(poly, 0.12, (0, gy + 0.06, 0), st.safety() if st.tier < 4 else body, rot=(math.pi / 2, 0, 0), bevel=0.01, name="belt_guard")
    # control panel on a post, front-left
    cp = Vector((-0.38 * w, -0.24 * d, zb))
    K.box((0.06, 0.06, 1.0), cp, M.metal("steel", dirt=0.8), bevel=0.005, base=True)
    KI.cabinet(cp + Vector((0, -0.06, 0.55)), 0.0, w=0.32, d=0.16, h=0.4, mat=st.mat((0.6, 0.6, 0.58), wear=0.6))
    _, lsock = KI.status_lamp(cp + Vector((0.08, -0.06, 0.97)), (0.1, 1.0, 0.25), 10.0)
    an.value(lsock, lambda t: 2.0 + 10.0 * KI.blink(t, 2, 0.5))
    KI.cable([(cp.x, cp.y + 0.03, zb + 0.4), (cp.x, cp.y + 0.03, zb + 0.02), (mx + 0.08, cp.y + 0.03, zb + 0.02), (mx + 0.08, 0.08 * d - 0.2, z1 + 0.25)], 0.018)
    K.scatter_debris(w * 0.9, d * 0.9, 5, seed=3)

    def update(t):
        alpha, th, P, T = solve(t)
        crankp.rotation_euler = (0, alpha, 0)
        beamp.rotation_euler = (0, -th, 0)
        for o, yy in pit:
            v = T - P
            o.location = Vector((P.x, yy, P.z))
            o.rotation_euler = (0, math.atan2(v.x, v.z), 0)
        rodp.location = Vector((xw, 0, zcar + R * (math.sin(th) - math.sin(th0))))
        an(t)

    top = zp + R * math.sin(math.radians(30)) + 0.25
    return Rig(height=top, frames=16, fps=8, update=update,
               lights=[{"pos": list(cp + Vector((0.08, -0.06, 1.0))), "color": [0.1, 1.0, 0.25], "energy": 0.3, "flicker": True}])


# =========================================================================== water pump
def _water_material(name="water"):
    """Murky glossy water with two crossing ripple bands. Returns (mat, [phase sockets])."""
    import bpy
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = M.NT(m)
    p = t.bsdf()
    socks = []
    hsum = None
    for scale, direction, rot in ((3.0, "X", 0.3), (4.5, "Y", -0.5)):
        tc = t.node("ShaderNodeTexCoord")
        mp = t.node("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, rot)
        t.link(tc.outputs["Object"], mp.inputs["Vector"])
        wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=direction)
        wv.inputs["Scale"].default_value = scale
        wv.inputs["Distortion"].default_value = 0.0
        t.link(mp.outputs["Vector"], wv.inputs["Vector"])
        socks.append(wv.inputs["Phase Offset"])
        hsum = wv.outputs["Factor"] if hsum is None else t.math("ADD", hsum, wv.outputs["Factor"])
    p.inputs["Base Color"].default_value = (0.04, 0.075, 0.07, 1)
    p.inputs["Roughness"].default_value = 0.12
    p.inputs["Specular IOR Level"].default_value = 0.6
    t.link(t.bump(hsum, 0.25, 0.01), p.inputs["Normal"])
    return m, socks


def _tidal(spec, p):
    """Tidal stream generator: concrete flow channel with a half-submerged cross-flow turbine
    rotor between bearing piers, generator nacelle, service bridge and switchgear."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    conc = st.concrete(0.4)
    body = st.body()
    K.box((w * 0.98, d * 0.98, 0.08), (0, 0, 0), conc, bevel=0.02, base=True)
    cy = -0.06 * d
    ch = 0.3 * d
    zt = 0.5
    for sy in (-1, 1):
        K.box((w * 0.98, 0.12 * s ** 0.5, zt - 0.08), (0, cy + sy * (ch + 0.06 * s ** 0.5), 0.08), conc, bevel=0.02, base=True, name="channel_wall")
    wmat, wsocks = _water_material("channel")
    K.box((w * 0.98, 2 * ch, 0.03), (0, cy, 0.22), wmat, bevel=0, base=True)
    for i, sock in enumerate(wsocks):
        an.value(sock, lambda t, i=i: -TAU * (2 + i) * t)
    rt = 0.62 * ch
    L = 0.62 * w
    zc = 0.3
    rotor = [K.cyl(0.06 * s ** 0.5, L + 0.3, (0, cy, zc), M.metal("steel"), rot=K.AXES["x"], verts=16, base=False, name="shaft")]
    for sx in (-1, 0, 1):
        rotor.append(K.cyl(rt, 0.03, (sx * L / 2, cy, zc), body, rot=K.AXES["x"], verts=40, base=False, name="end_disc"))
    nb = 8
    for i in range(nb):
        a_ = TAU * i / nb
        bl = K.box((L, 0.03 * s ** 0.5, 0.16 * s ** 0.5), (0, cy + math.cos(a_) * rt, zc + math.sin(a_) * rt), M.metal("stainless", dirt=0.5), bevel=0.006, name="blade")
        bl.rotation_euler = (a_ + 0.35, 0, 0)
        rotor.append(bl)
    rp = KI.pivot((0, cy, zc), axis="x", children=rotor)
    an.spin(rp, 3.0 / nb)
    for sx in (-1, 1):
        K.box((0.22 * s ** 0.5, 2 * ch + 0.1, 0.16), (sx * (L / 2 + 0.25), cy, zt + 0.0), conc, bevel=0.015, base=True, name="bearing_beam")
        K.box((0.2, 0.26, 0.2), (sx * (L / 2 + 0.25), cy, zc), M.metal("dark_steel"), bevel=0.012)
    nac = Vector((L / 2 + 0.55, cy, zt + 0.32))
    if nac.x + 0.4 > w * 0.49:
        nac.x = w * 0.49 - 0.4
    K.cyl(0.26 * s ** 0.5, 0.8, nac, body, rot=K.AXES["x"], verts=40, base=False, name="nacelle")
    K.sphere(0.26 * s ** 0.5, nac + Vector((0.4, 0, 0)), body, scale=(0.5, 1, 1))
    for i in range(8):
        K.torus(0.262 * s ** 0.5, 0.01, nac + Vector((-0.3 + i * 0.08, 0, 0)), body, rot=K.AXES["x"], segs=40, rsegs=6)
    K.box((0.9, 0.5, 0.08), nac - Vector((0, 0, 0.3 * s ** 0.5 + 0.04)), st.frame(), bevel=0.01)
    # service bridge across the channel
    bx = -L / 2 - 0.35
    K.box((0.5, 2 * ch + 0.3, 0.06), (bx, cy, zt + 0.1), M.tread_plate(1.2, rust=st.tier == 1), bevel=0.006, base=True)
    K.railing([(bx - 0.24, cy - ch, zt + 0.16), (bx - 0.24, cy + ch, zt + 0.16)], 0.8, st.safety())
    K.railing([(bx + 0.24, cy - ch, zt + 0.16), (bx + 0.24, cy + ch, zt + 0.16)], 0.8, st.safety())
    # switchgear (back) with cable
    sy_ = cy + ch + 0.35 * s ** 0.5
    sy_ = min(sy_, 0.4 * d)
    KI.cabinet((0.25 * w, sy_, 0.08), 0.0, w=0.6, d=0.3, h=1.0, mat=st.mat((0.6, 0.61, 0.6), wear=0.4), screen_col=st.glow_col)
    KI.cabinet((-0.05 * w, sy_, 0.08), 0.0, w=0.45, d=0.3, h=1.0, mat=st.mat((0.6, 0.61, 0.6), wear=0.4), screen_col=st.glow_col)
    KI.cable([nac + Vector((0, 0.2, 0.15)), Vector((nac.x, sy_ - 0.1, zt + 0.5)), Vector((0.25 * w, sy_ - 0.1, 0.9))], 0.03)
    _, ls = KI.status_lamp((0.25 * w + 0.2, sy_, 1.1), (0.1, 1.0, 0.3), 10.0, r=0.03)
    an.value(ls, lambda t: 2.0 + 9.0 * KI.blink(t, 2))
    return Rig(height=1.4, frames=16, fps=10, update=an, emitters=[{"pos": [0, cy, zc + 0.1], "type": "steam"}])


def water_pump(spec, p):
    """Vertical turbine pump over a concrete intake sump: hollow-shaft motor, discharge head with
    an open coupling lantern (spinning coupling), discharge riser with check + gate valve,
    rippling water. variant 'tidal': cross-flow tidal turbine in a flow channel."""
    if str(p.get("variant", "")) == "tidal":
        return _tidal(spec, p)
    KI.begin()
    st = KI.Style(p, alt=True if p.get("tier", 1) == 3 else False)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.75
    conc = st.concrete(0.5)
    body = st.body()
    # sump: base slab + curbs around a water pit on the front-left
    KI.concrete_pad(w * 0.96, d * 0.96, 0.1, conc)
    zt = 0.28
    px0, px1 = -0.46 * w, 0.26 * w
    py0, py1 = -0.46 * d, 0.16 * d
    cw = 0.07 + 0.02 * s
    K.box((px1 - px0, cw, zt - 0.1), ((px0 + px1) / 2, py0 + cw / 2, 0.1), conc, bevel=0.012, base=True)
    K.box((cw, py1 - py0, zt - 0.1), (px0 + cw / 2, (py0 + py1) / 2, 0.1), conc, bevel=0.012, base=True)
    K.box((w * 0.96 / 2 - px1, d * 0.96, zt - 0.1), ((px1 + w * 0.48) / 2, 0, 0.1), conc, bevel=0.015, base=True)
    K.box((px1 - px0, d * 0.48 - py1, zt - 0.1), ((px0 + px1) / 2, (py1 + d * 0.48) / 2, 0.1), conc, bevel=0.015, base=True)
    wmat, wsocks = _water_material()
    K.box((px1 - px0 - cw, py1 - py0 - cw, 0.02), ((px0 + px1 + cw) / 2, (py0 + py1 + cw) / 2, 0.17), wmat, bevel=0)
    for i, sock in enumerate(wsocks):
        an.value(sock, lambda t, i=i: -TAU * (1 + i) * t)
    # edge angle on the pit
    K.box((px1 - px0, 0.03, 0.03), ((px0 + px1) / 2, py0 + cw + 0.005, zt - 0.015), st.steel("iron"), bevel=0.003)
    # bridge beams across the pit carrying the pump
    pc = Vector(((px0 + px1) / 2 - 0.04 * w, py1 - 0.17 * k, zt))
    for sy in (-1, 1):
        KI.hbeam((px0 + cw, pc.y + sy * 0.16 * k, zt - 0.05), (px1 + 0.1, pc.y + sy * 0.16 * k, zt - 0.05), 0.1, 0.07, st.frame())
    K.box((0.46 * k, 0.46 * k, 0.03), pc + Vector((0, 0, 0.0)), st.steel("iron"), bevel=0.006, base=True)
    # discharge head
    hr = 0.15 * k
    K.cyl(hr * 1.3, 0.05, pc + Vector((0, 0, 0.03)), body, verts=32)
    K.cyl(hr, 0.3 * k, pc + Vector((0, 0, 0.08)), body, verts=32, name="dhead")
    zh = 0.08 + 0.3 * k
    # lantern: 4 posts + open windows, coupling inside
    lz0 = zt + zh
    lh = 0.22 * k
    K.cyl(hr * 1.05, 0.04, pc + Vector((0, 0, zh)), body, verts=32)
    for i in range(4):
        a = TAU * i / 4 + math.pi / 4
        K.box((0.05 * k, 0.05 * k, lh), pc + Vector((math.cos(a) * hr * 0.85, math.sin(a) * hr * 0.85, zh + 0.04)), body, bevel=0.008, base=True)
    K.cyl(hr * 1.05, 0.04, pc + Vector((0, 0, zh + 0.04 + lh)), body, verts=32)
    cpl = [K.cyl(0.03 * k, lh + 0.04, pc + Vector((0, 0, zh)), M.metal("steel"), verts=12)]
    cpl.append(K.cyl(0.07 * k, 0.07 * k, pc + Vector((0, 0, zh + lh * 0.38)), M.metal("dark_steel"), verts=24))
    cpl += K.bolts(pc + Vector((0, 0, zh + lh * 0.38 + 0.07 * k)), 0.05 * k, 6, r=0.009)
    cpl.append(K.box((0.012, 0.072 * k * 2, 0.06 * k), pc + Vector((0, 0, zh + lh * 0.42)), M.painted((0.7, 0.4, 0.02), name="mark"), bevel=0.002))
    cp = KI.pivot(pc, name="coupling")
    KI.bind(cpl, cp)
    an.spin(cp, 1.0)   # whole turn: the 2-fold marker bar must come back to its start pose
    # motor
    mz = zh + 0.08 + lh
    mr = 0.19 * k
    mh = 0.42 * k
    mm = M.painted((0.05, 0.14, 0.3), wear=st.wear * 0.6, grime=st.grime * 0.6, gloss_coat=st.gloss, name="motor_paint") if st.tier < 4 else body
    K.cyl(mr, mh, pc + Vector((0, 0, mz)), mm, verts=40)
    for i in range(16):
        a = TAU * i / 16
        K.box((0.02, 0.025, mh * 0.85), pc + Vector((math.cos(a) * mr, math.sin(a) * mr, mz + mh * 0.06)), mm, bevel=0.003, base=True,
              rot=(0, 0, a))
    K.cyl(mr * 1.08, 0.12 * k, pc + Vector((0, 0, mz + mh)), mm, verts=40, r2=mr * 0.7)  # drip cover
    K.cyl(mr * 0.35, 0.05, pc + Vector((0, 0, mz + mh + 0.12 * k)), M.metal("dark_steel"), verts=20)
    K.box((mr * 0.8, mr * 0.6, mr * 0.7), pc + Vector((mr * 0.95, -mr * 0.3, mz + mh * 0.45)), mm, bevel=0.01)
    for a in (0.3, math.pi + 0.3):
        K.torus(0.035, 0.008, pc + Vector((math.cos(a) * mr * 0.9, math.sin(a) * mr * 0.9, mz + mh + 0.14 * k)), M.metal("steel"), rot=(math.pi / 2, 0, a))
    KI.plate_sign(pc + Vector((0, -mr - 0.012, mz + mh * 0.62)), mr * 0.6, 0.05, "-y", color=(0.75, 0.75, 0.72))
    # discharge: from head side nozzle to +X then down to header at the edge
    pr = 0.06 * k
    dz = zt + 0.2 * k
    pm = st.mat((0.06, 0.2, 0.42) if st.tier >= 3 else (0.05, 0.12, 0.05) if st.tier == 2 else (0.1, 0.07, 0.05), name="pipe_paint")
    x_end = w * 0.48
    KI.pipe([(pc.x + hr, pc.y, dz), (x_end - 0.25 * k, pc.y, dz), (x_end - 0.25 * k, pc.y + 0.0, dz)], r=pr, mat=pm)
    KI.gate_valve((pc.x + hr + 0.22 * k, pc.y, dz), "x", r=pr * 0.95, wheel_up="z")
    K.cyl(pr * 1.4, 0.18 * k, (pc.x + hr + 0.45 * k, pc.y, dz), pm, rot=K.AXES["x"], verts=24, base=False, name="check")
    K.box((0.1 * k, 0.12 * k, 0.08 * k), (pc.x + hr + 0.45 * k, pc.y, dz + pr * 1.3), pm, bevel=0.008)
    KI.pipe([(x_end - 0.25 * k, pc.y, dz), (x_end - 0.02, pc.y, dz)], r=pr, mat=pm, flanges=True)
    K.box((0.06, 0.12, dz - zt + 0.02), (x_end - 0.2 * k, pc.y, zt), st.frame(), bevel=0.005, base=True)
    g, needle = KI.gauge((pc.x + hr + 0.1 * k, pc.y - pr - 0.03, dz + 0.12 * k), "-y", 0.04 * k)
    KI.strut((pc.x + hr + 0.1 * k, pc.y, dz), (pc.x + hr + 0.1 * k, pc.y - pr - 0.03, dz + 0.12 * k - 0.04 * k), 0.008, M.metal("brass"))
    an.rotate(needle, lambda t: 0.4 + 0.08 * math.sin(TAU * t * 3) + 0.05 * math.sin(TAU * t * 5))
    # control box on a stand, back-right
    cbx = Vector((0.3 * w, 0.3 * d, zt))
    K.box((0.04, 0.04, 0.5 * k), cbx + Vector((0.0, 0.03, 0)), M.metal("steel", dirt=0.7), base=True, bevel=0.004)
    KI.cabinet(cbx + Vector((0, -0.03, 0.25 * k)), 0.0, w=0.24 * k, d=0.12 * k, h=0.3 * k, mat=st.mat((0.62, 0.62, 0.6), wear=0.5))
    _, lsock = KI.status_lamp(cbx + Vector((0.0, -0.03, 0.55 * k + 0.02)), st.glow_col if st.tier >= 3 else (0.1, 1.0, 0.3), 10.0, r=0.025)
    an.value(lsock, lambda t: 3 + 9 * KI.blink(t, 1, 0.5))
    KI.cable([(cbx.x, cbx.y, zt + 0.25 * k), (cbx.x, cbx.y, zt + 0.02), (pc.x + mr * 1.3, cbx.y, zt + 0.02),
              (pc.x + mr * 1.3, pc.y, zt + 0.02), (pc.x + mr * 1.2, pc.y - mr * 0.3, mz + mh * 0.4)], 0.015)
    if st.tier >= 2:
        K.railing([(px0 + 0.03, py0 + 0.03, zt), (px1 - 0.05, py0 + 0.03, zt)], 0.7 * k, st.safety())
        K.railing([(px0 + 0.03, py0 + 0.03, zt), (px0 + 0.03, py1 - 0.05, zt)], 0.7 * k, st.safety())
    return Rig(height=zt + mz + mh + 0.2 * k, frames=16, fps=10, update=an,
               lights=[{"pos": list(cbx + Vector((0.0, -0.03, 0.55 * k + 0.05))), "color": list(st.glow_col if st.tier >= 3 else (0.1, 1.0, 0.3)),
                        "energy": 0.3, "flicker": True}])


# =========================================================================== gas well
def gas_well(spec, p):
    """Natural-gas wellhead: Christmas-tree valve stack, flowline to a horizontal separator, a guyed
    flare stack with a live flame, and a solar-powered RTU."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.7
    body = st.body()
    red = st.mat((0.45, 0.04, 0.02), name="tree_red") if st.tier < 3 else body
    steel = st.steel()
    KI.concrete_pad(w * 0.96, d * 0.96, 0.08, M.concrete(0.6, tint=(0.8, 0.78, 0.74)))
    z0 = 0.08
    # ---- cellar + christmas tree (front-centre)
    T = Vector((0.12 * w, -0.14 * d, z0))
    K.box((0.6 * k, 0.6 * k, 0.03), T, M.tread_plate(1.4, rust=st.tier == 1), bevel=0.004, base=True)
    K.cyl(0.16 * k, 0.12, T + Vector((0, 0, 0.03)), M.metal("cast_iron", dirt=1.0), verts=32)
    z = z0 + 0.15
    K.flange(T + Vector((0, 0, z - z0)), 0.13 * k, "z")
    K.cyl(0.1 * k, 0.16 * k, T + Vector((0, 0, z - z0)), steel, verts=24)
    z += 0.16 * k
    vr = 0.07 * k
    for i in range(2):  # master valves
        K.box((vr * 2.4, vr * 2.2, vr * 2.6), T + Vector((0, 0, z - z0)), red, bevel=0.012, base=True, name="master")
        K.flange(T + Vector((0, 0, z - z0)), vr * 1.1, "z")
        KI.strut(T + Vector((0, -vr * 1.1, z - z0 + vr * 1.3)), T + Vector((0, -vr * 2.8, z - z0 + vr * 1.3)), vr * 0.45, red, verts=12)
        KI.handwheel(T + Vector((0, -vr * 2.9, z - z0 + vr * 1.3)), vr * 1.3, "-y")
        z += vr * 2.6 + 0.02
    # cross with wing valves
    K.box((vr * 2.6, vr * 2.6, vr * 2.6), T + Vector((0, 0, z - z0)), steel, bevel=0.012, base=True, name="cross")
    zc = z + vr * 1.3
    for sx in (-1, 1):
        K.cyl(vr * 0.7, vr * 1.2, T + Vector((sx * vr * 1.3, 0, zc - z0)), steel, rot=K.AXES["x"], verts=16, base=False)
        vx = T.x + sx * vr * 3.0
        K.box((vr * 2.2, vr * 2.0, vr * 2.0), (vx, T.y, zc), red, bevel=0.01, name="wing")
        K.flange((vx - sx * vr * 1.15, T.y, zc), vr * 0.8, "x")
        KI.strut((vx, T.y, zc + vr), (vx, T.y, zc + vr * 2.6), vr * 0.4, red, verts=12)
        KI.handwheel((vx, T.y, zc + vr * 2.7), vr * 1.2, "z")
    z += vr * 2.6 + 0.02
    K.box((vr * 2.2, vr * 2.0, vr * 2.2), T + Vector((0, 0, z - z0)), red, bevel=0.012, base=True, name="swab")
    KI.strut(T + Vector((0, -vr, z - z0 + vr * 1.1)), T + Vector((0, -vr * 2.5, z - z0 + vr * 1.1)), vr * 0.4, red, verts=12)
    KI.handwheel(T + Vector((0, -vr * 2.6, z - z0 + vr * 1.1)), vr * 1.1, "-y")
    z += vr * 2.2
    K.cyl(vr * 1.0, vr * 1.2, T + Vector((0, 0, z - z0)), steel, verts=20, name="tree_cap")
    z += vr * 1.2
    g, needle = KI.gauge(T + Vector((0, -0.01, z - z0 + 0.06 * k)), "-y", 0.05 * k)
    KI.strut(T + Vector((0, 0, z - z0)), T + Vector((0, 0, z - z0 + 0.03 * k)), 0.012, M.metal("brass"))
    an.rotate(needle, lambda t: -0.3 + 0.06 * math.sin(TAU * t * 2) + 0.03 * math.sin(TAU * t * 7))
    tree_top = z + 0.12 * k

    # ---- separator (back, along X)
    sr = 0.17 * k
    sl = 0.62 * w
    S = Vector((-0.04 * w, 0.27 * d, z0 + 0.32 * k + sr))
    vm = st.mat((0.62, 0.63, 0.6), name="vessel") if st.tier != 2 else body
    K.cyl(sr, sl - 2 * sr * 0.5, S, vm, rot=K.AXES["x"], verts=40, base=False, name="separator")
    for sx in (-1, 1):
        K.sphere(sr, S + Vector((sx * (sl / 2 - sr * 0.5), 0, 0)), vm, scale=(0.45, 1, 1))
        K.prism([(-0.12 * k, 0), (0.12 * k, 0), (0.09 * k, S.z - z0 - sr * 0.6), (-0.09 * k, S.z - z0 - sr * 0.6)], sr * 1.6,
                (S.x + sx * sl * 0.3, S.y, z0), st.frame(), rot=(0, 0, 0), bevel=0.006, name="saddle")
    for xx in (-0.15, 0.2):
        K.torus(sr * 1.01, 0.012, S + Vector((xx * sl, 0, 0)), M.metal("steel", dirt=0.6), rot=K.AXES["x"])
    K.cyl(0.04 * k, 0.12 * k, S + Vector((sl * 0.18, 0, sr)), steel, verts=16)
    K.cyl(0.03 * k, 0.1 * k, S + Vector((sl * 0.18, 0, sr + 0.12 * k)), M.painted((0.6, 0.05, 0.02), name="psv"), verts=16)
    # level gauge glass on the -Y face
    K.box((0.05, 0.03, sr * 1.2), S + Vector((-sl * 0.1, -sr - 0.03, -sr * 0.6)), M.metal("chrome"), bevel=0.004, base=True)
    K.box((0.025, 0.02, sr * 0.5), S + Vector((-sl * 0.1, -sr - 0.045, -sr * 0.5)), M.emissive((0.9, 0.6, 0.2), 1.5), bevel=0.002, base=True)
    KI.plate_sign(S + Vector((sl * 0.05, -sr - 0.006, sr * 0.2)), 0.18 * k, 0.08 * k, "-y", color=(0.8, 0.8, 0.76))
    # flowline: tree +X wing -> separator inlet
    fr = 0.04 * k
    x_out = T.x + vr * 4.2
    KI.pipe([(x_out, T.y, zc), (S.x + sl * 0.42, T.y, zc), (S.x + sl * 0.42, S.y - sr - 0.05, zc), (S.x + sl * 0.42, S.y - sr - 0.05, S.z), (S.x + sl * 0.38, S.y - sr * 0.4, S.z)],
            r=fr, mat=st.mat((0.4, 0.4, 0.38), name="pipe_paint"))
    K.cyl(fr * 1.6, 0.14 * k, (S.x + sl * 0.42, T.y + 0.25 * d, zc), red, rot=K.AXES["y"], verts=20, base=False, name="choke")
    for xx in (T.x + vr * 6, S.x + sl * 0.42):
        K.box((0.06, 0.08, zc - z0 - fr), (xx, T.y if xx < S.x + sl * 0.4 else T.y + 0.12 * d, z0), st.frame(), base=True, bevel=0.004)

    # ---- flare stack (back-left corner) with guy wires
    F = Vector((-0.36 * w, 0.36 * d, z0))
    fh = 1.7 + 0.8 * s
    K.box((0.3 * k, 0.3 * k, 0.12), F, M.concrete(0.8), bevel=0.01, base=True)
    K.cyl(0.05 * k, fh, F + Vector((0, 0, 0.12)), M.metal("cast_iron", dirt=1.0), verts=20, name="flare_stack")
    for zz in (0.12, fh * 0.5, fh * 0.8):
        K.torus(0.05 * k * 1.1, 0.01, F + Vector((0, 0, zz)), M.metal("dark_steel"))
    tip = F + Vector((0, 0, 0.12 + fh))
    K.cyl(0.08 * k, 0.18 * k, tip, M.metal("stainless", dirt=1.0), verts=20, name="flare_tip")
    K.cyl(0.11 * k, 0.05, tip + Vector((0, 0, 0.18 * k)), M.metal("dark_steel", dirt=1.0), verts=20, r2=0.13 * k)
    for a in (0.3, 0.3 + TAU / 3, 0.3 + 2 * TAU / 3):
        anchor = F + Vector((math.cos(a) * 0.55 * s, math.sin(a) * 0.55 * s, 0))
        anchor.x = max(-0.48 * w, min(0.48 * w, anchor.x))
        anchor.y = max(-0.48 * d, min(0.48 * d, anchor.y))
        KI.strut(anchor, F + Vector((0, 0, fh * 0.78)), 0.005, M.metal("steel", dirt=0.8), verts=4)
        K.box((0.08, 0.08, 0.06), anchor, M.concrete(0.8), bevel=0.01, base=True)
    # gas line separator -> flare
    KI.pipe([(S.x - sl / 2 + 0.05, S.y, S.z + sr * 0.7), (F.x + 0.08, S.y, S.z + sr * 0.7), (F.x + 0.08, F.y, S.z + sr * 0.7), (F.x + 0.06, F.y, 0.5 + z0)],
            r=0.03 * k, mat=st.mat((0.5, 0.4, 0.03), name="gasline"), flanges=False)
    # flame: wind-blown layered soft blobs (opaque core, fading edges)
    # moderate strengths: AgX washes strong emission out to white, a real flare reads deep orange
    fmat_o, fs_o = KI.soft_glow((1.0, 0.42, 0.05), 3.0, rim=False, name="flame_outer", power=0.8)
    fmat_i, fs_i = KI.soft_glow((1.0, 0.72, 0.25), 6.0, rim=False, name="flame_inner", power=1.0)
    fl_h = 0.5 + 0.18 * s
    fr0 = 0.1 * k
    blobs = []
    for i, (zf, rf, dx, mat) in enumerate(((0.25, 1.0, 0.0, fmat_o), (0.6, 0.8, 0.12, fmat_o), (0.9, 0.55, 0.25, fmat_o),
                                            (0.22, 0.6, 0.0, fmat_i), (0.45, 0.42, 0.06, fmat_i))):
        o = K.sphere(fr0 * rf, (0, 0, 0), mat, segs=16, rings=10, scale=(1, 1, 1.9), name="flame")
        blobs.append((o, zf, rf, dx, i))
    flp = KI.pivot(tip + Vector((0, 0, 0.17 * k)), name="flame")
    KI.group([b_[0] for b_ in blobs], flp)
    light = KI.point_light(tip + Vector((0, 0, 0.35)), (1.0, 0.5, 0.15), 40.0 * k, 0.15)

    def flame_upd(t):
        f = KI.flicker(t, 0.3, 0.45)
        for o, zf, rf, dx, i in blobs:
            ph = i * 0.23
            lift = 0.08 * fl_h * KI.wave(t, 2, ph)
            o.location = (dx * fl_h * (1 + 0.3 * KI.wave(t, 3, ph)), 0.05 * fl_h * KI.wave(t, 2, ph + 0.4), zf * fl_h + lift)
            sc = 0.85 + 0.25 * KI.flicker(t, ph * 3, 1.0)
            o.scale = (sc, sc, sc * (1.0 + 0.2 * KI.wave(t, 4, ph)))
        fs_o.default_value = 2.4 + 1.4 * f
        fs_i.default_value = 4.5 + 3.0 * f
        light.energy = 40.0 * k * (0.6 + 0.5 * f)
    an.add(flame_upd)

    # ---- RTU with solar panel (front-left)
    R0 = Vector((-0.34 * w, -0.3 * d, z0))
    K.cyl(0.03, 1.1 * k, R0, M.metal("steel", dirt=0.6), verts=12)
    KI.cabinet(R0 + Vector((0, -0.05, 0.35 * k)), 0.0, w=0.26 * k, d=0.14 * k, h=0.32 * k, mat=st.mat((0.65, 0.66, 0.63), wear=0.4))
    sp = K.box((0.42 * k, 0.3 * k, 0.025), R0 + Vector((0, 0.0, 1.1 * k + 0.05)), M.metal("aluminum", dirt=0.3), bevel=0.006, rot=(math.radians(-35), 0, 0))
    K.box((0.4 * k, 0.28 * k, 0.01), R0 + Vector((0, -0.0 - 0.007, 1.1 * k + 0.063)), M.plastic((0.01, 0.02, 0.06), 0.15), bevel=0.002,
          rot=(math.radians(-35), 0, 0))
    K.cyl(0.006, 0.5 * k, R0 + Vector((0.08 * k, 0.04, 0.68 * k)), M.plastic((0.02, 0.02, 0.02)), verts=6)
    _, lsock = KI.status_lamp(R0 + Vector((-0.08 * k, -0.07, 0.69 * k)), (0.1, 1.0, 0.3), 10.0, r=0.02, h=0.04)
    an.value(lsock, lambda t: 1.0 + 10.0 * KI.blink(t, 4, 0.25))
    KI.cable(KI.sag((R0.x, R0.y + 0.02, z0 + 0.4 * k), (T.x - 0.1, T.y + 0.05, z0 + 0.1), 0.0, 6), 0.012)
    K.scatter_debris(w * 0.9, d * 0.9, 4, seed=8)
    height = max(tip.z + 0.2 * k + fl_h, tree_top)
    return Rig(height=height, frames=16, fps=12, update=an,
               lights=[{"pos": [tip.x, tip.y, tip.z + 0.4], "color": [1.0, 0.55, 0.15], "energy": 1.0, "flicker": True}],
               emitters=[{"pos": [tip.x, tip.y, tip.z + 0.3], "type": "fire"},
                         {"pos": [tip.x, tip.y, tip.z + fl_h + 0.3], "type": "smoke"}])


ARCHETYPES = KI.with_bounds({"drill": drill, "pumpjack": pumpjack, "water_pump": water_pump, "gas_well": gas_well})
