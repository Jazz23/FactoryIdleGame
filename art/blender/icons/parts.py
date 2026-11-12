"""Mechanical part icons: gear, bolts, spring, bearing, frame, magnet, heat sink, turbine blade, nozzle,
motor, servo arm, tank part, antenna."""
import math
import random

import bmesh
from mathutils import Euler, Matrix, Vector

import kit as K
import kit_icons as KI
import materials as M
from icons import frame


def _mach(material, color, default="steel", rough=None):
    """Machined finish for metals (brushed, light grime); schema material otherwise."""
    m = material or default
    if KI.is_metal(m):
        return KI.metal(m, color, rough=rough, dirt=0.35)
    if m == "paint":
        return KI.paint(color or (0.6, 0.35, 0.02), wear=0.25, grime=0.3, rust=0.05)
    return KI.surf(m, color)


def _paint_or(material, color, default_col, **kw):
    if material in (None, "paint") or not KI.is_metal(material or ""):
        if material not in (None, "paint") and material not in ("plastic_color", "plastic_white", "plastic_black"):
            return KI.surf(material, color)
        if material in ("plastic_color", "plastic_white", "plastic_black"):
            return KI.surf(material, color)
        return KI.paint(color or default_col, **kw)
    return KI.metal(material, color, dirt=0.4)


def _circle(r, n, a0=0.0):
    return [(r * math.cos(a0 + math.tau * i / n), r * math.sin(a0 + math.tau * i / n)) for i in range(n)]


def _hexagon(r, sub=4):
    pts = []
    for k in range(6):
        a0, a1 = math.tau * k / 6, math.tau * (k + 1) / 6
        p0 = Vector((r * math.cos(a0), r * math.sin(a0)))
        p1 = Vector((r * math.cos(a1), r * math.sin(a1)))
        for s in range(sub):
            q = p0.lerp(p1, s / sub)
            pts.append((q.x, q.y))
    return pts


# --------------------------------------------------------------------------- gear
def gear_outline(n, r_pitch, depth):
    ra, rf = r_pitch + depth * 0.45, r_pitch - depth * 0.55
    prof = [(0.0, rf), (0.16, rf), (0.27, r_pitch - depth * 0.1), (0.35, ra - depth * 0.05), (0.4, ra), (0.6, ra),
            (0.65, ra - depth * 0.05), (0.73, r_pitch - depth * 0.1), (0.84, rf)]
    pts = []
    for i in range(n):
        for u, r in prof:
            a = math.tau * (i + u) / n
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def make_gear(n, r_pitch, thick, mat, bore=None, holes=5, hub=True, name="gear"):
    depth = 2.25 * (2 * r_pitch / n)
    outer = gear_outline(n, r_pitch, depth)
    rb = bore or r_pitch * 0.2
    inner = _circle(rb, len(outer), 0.0)
    g = KI.ring_extrude(outer, inner, 0, thick, mat, name=name, bevel=0.0012)
    objs = [g]
    rf = r_pitch - depth * 0.55
    if holes and rf > rb * 2.6:
        rh = (rf - rb * 1.9) * 0.36
        rc = (rf + rb * 1.9) / 2
        KI.drill(g, [(rc * math.cos(math.tau * k / holes + 0.3), rc * math.sin(math.tau * k / holes + 0.3), thick / 2)
                     for k in range(holes)], rh, thick * 4, verts=28)
    # keyway
    kc = K.box((rb * 0.5, rb * 0.6, thick * 3), (rb, 0, -thick), None, bevel=0, base=True, name="cutter")
    kc.hide_render = True
    KI.apply_boolean(g, kc)
    if hub:
        objs.append(KI.lathe([(rb, thick), (rb * 1.9, thick), (rb * 1.85, thick + thick * 0.45), (rb, thick + thick * 0.45)],
                             mat, segs=48, closed=True, name="hub", bevel=0.001))
    return objs


def gear(item, material, color, p):
    """Large spur gear lying flat with a meshing pinion (variant 'housing' -> gearbox)."""
    if p.get("variant") == "housing":
        from icons import machines
        return machines.gearbox(item, material, color, p)
    mat = _mach(material, color)
    n1, n2 = p.get("teeth", 30), 14
    big = make_gear(n1, 0.16, 0.042, mat)
    small = make_gear(n2, 0.16 * n2 / n1, 0.05, mat, holes=0, name="pinion")
    a = math.radians(-35)
    d = 0.16 + 0.16 * n2 / n1
    KI.group(small, (d * math.cos(a), d * math.sin(a), 0), (0, 0, a + math.pi + math.pi / n2))
    return frame(pitch=47.0)


# --------------------------------------------------------------------------- fasteners
def threaded(r, L, pitch, depth, mat, segs=32, tip=0.006, name="thread"):
    bm = bmesh.new()
    rows = max(8, int(L / pitch * 8))
    rings = []
    for i in range(rows + 1):
        z = L * i / rows
        ring = []
        for j in range(segs):
            th = math.tau * j / segs
            ph = (th / math.tau + z / pitch) % 1.0
            rr = r - depth * (1 - abs(ph * 2 - 1))
            if z > L - tip:
                rr = min(rr, r - (z - (L - tip)) * 0.9)
            ring.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), z)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((A[j], A[k], B[k], B[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return KI.finish(name, bm, mat, smooth=60)


def hex_bolt(d, L, mat, mark="8.8"):
    """Hex bolt along +Z: head 0..k, thread k..k+L."""
    r = d / 2
    k = d * 0.65
    head = KI.poly_extrude(_hexagon(d * 0.92, 1), 0, k, mat, name="head", bevel=d * 0.06)
    shank = KI.lathe([(0, k - 0.001), (r * 0.98, k - 0.001), (r * 0.98, k + L * 0.3), (0, k + L * 0.3)], mat, segs=32)
    th = threaded(r, L * 0.7, d * 0.15, d * 0.08, mat)
    th.location.z = k + L * 0.3
    t = KI.text_mesh(mark, d * 0.32, d * 0.02, mat, rot=(math.pi, 0, 0), loc=(0, 0, 0.0001))
    return [head, shank, th, t]


def hex_nut(d, mat):
    m = d * 0.8
    return KI.ring_extrude(_hexagon(d * 0.92, 8), _circle(d * 0.5, 48, 0.0), 0, m, mat, name="nut", bevel=d * 0.05)


def washer(d, mat):
    return KI.ring_extrude(_circle(d * 1.05, 48), _circle(d * 0.54, 48), 0, d * 0.16, mat, name="washer", bevel=d * 0.02)


def bolts(item, material, color, p):
    """Hex bolts, nut and washer."""
    mat = _mach(material, color, rough=0.32)
    d = 0.06
    a = hex_bolt(d, 0.26, mat)
    KI.group(a, (0.02, 0.05, 0.0), (0, 0, 0.3))  # standing on its head
    b = hex_bolt(d, 0.24, mat)
    gb = KI.group(b, (-0.1, -0.02, 0.0), (math.pi / 2, 0, 0.35))
    gb.rotation_euler = Euler((0, math.pi / 2, -0.25), "XYZ")
    gb.location = (-0.16, -0.06, d * 0.92 * math.cos(math.pi / 6))
    nb = hex_nut(d, mat)
    nb.rotation_euler = (0, math.pi / 2, -0.25)
    nb.location = Vector((-0.16, -0.06, d * 0.92 * math.cos(math.pi / 6))) + Vector((math.cos(-0.25), math.sin(-0.25), 0)) * 0.2
    KI.ground(b + [nb])
    n2 = hex_nut(d, mat)
    n2.location = (0.13, -0.13, 0)
    n2.rotation_euler = (0, 0, 0.2)
    w = washer(d, mat)
    w.location = (0.17, -0.02, 0)
    return frame(pitch=52.0)


# --------------------------------------------------------------------------- spring
def spring(item, material, color, p):
    """Helical compression spring with closed ends."""
    mat = _mach(material, color, "steel", rough=0.25)
    R, wr = 0.085, 0.012
    turns = 7.5
    P = 0.052
    pts = []
    n = int(turns * 48)
    z = wr
    prev_a = 0.0
    for i in range(n + 1):
        u = i / n
        a = math.tau * turns * u
        da = a - prev_a
        prev_a = a
        tt = a / math.tau
        pitch = 2.1 * wr if (tt < 0.9 or tt > turns - 0.9) else P
        z += pitch * da / math.tau
        pts.append((R * math.cos(a), R * math.sin(a), z))
    KI.curve_tube(pts, wr, mat, name="spring", res=4)
    return frame(pitch=54.0)


# --------------------------------------------------------------------------- bearing
def bearing(item, material, color, p):
    """Open deep-groove ball bearing standing on edge."""
    mat = _mach(material, color, "chrome", rough=0.12)
    Ro, w = 0.16, 0.06
    rb = 0.026
    rp = 0.112
    Roi = rp + rb * 0.55
    Rii = rp - rb * 0.55
    rbore = 0.06
    gr = rb * 1.04

    def groove(rc, sign, n=10):
        pts = []
        for i in range(n + 1):
            a = -math.pi / 2 + math.pi * i / n
            z = gr * math.sin(a) * 0.62
            r_ = rc + sign * gr * math.cos(a) * 0.35
            pts.append((r_, z))
        return pts

    outer = [(Roi, -w / 2), (Ro - 0.004, -w / 2), (Ro, -w / 2 + 0.004), (Ro, w / 2 - 0.004), (Ro - 0.004, w / 2),
             (Roi, w / 2)]
    g_o = groove(Roi, +1)
    outer += list(reversed(g_o))[1:-1]
    inner = [(rbore, -w / 2), (Rii, -w / 2)] + groove(Rii, -1)[1:-1] + [(Rii, w / 2), (rbore + 0.003, w / 2),
                                                                          (rbore, w / 2 - 0.003)]
    objs = [KI.lathe(outer, mat, segs=96, closed=True, name="outer_ring"),
            KI.lathe(inner, mat, segs=96, closed=True, name="inner_ring")]
    nb = 10
    ball = KI.metal("chrome", None, rough=0.05, dirt=0.1)
    for k in range(nb):
        a = math.tau * k / nb
        objs.append(K.sphere(rb, (rp * math.cos(a), rp * math.sin(a), 0), ball, segs=24, rings=12))
    cage = KI.metal("brass", None, rough=0.3, dirt=0.3)
    for s in (-1, 1):
        objs.append(KI.lathe([(rp - 0.008, s * rb * 0.75), (rp + 0.008, s * rb * 0.75), (rp + 0.008, s * rb * 0.85),
                              (rp - 0.008, s * rb * 0.85)], cage, segs=96, closed=True, name="cage"))
    objs.append(KI.text_mesh("6312-2RS", 0.014, 0.0005, M.metal("dark_steel"), loc=(0, -(Ro + Roi) / 2, w / 2 + 0.0001)))
    KI.group(objs, (0, 0, 0), (math.radians(68), 0, math.radians(-30)))
    KI.ground(objs)
    return frame(pitch=56.0)


# --------------------------------------------------------------------------- frame
def frame_(item, material, color, p):
    """Welded square-tube frame cube with gussets, bracing and drilled foot plates."""
    mat = _paint_or(material, color, (0.55, 0.32, 0.02), wear=0.35, grime=0.4, rust=0.15) if material != "steel" else \
        KI.cast_metal("steel", color, oxid=0.6, scale=3.0)
    W, D, H = 0.36, 0.3, 0.3
    s = 0.026
    plate_m = KI.cast_metal("steel", None, oxid=0.5, scale=3.0)
    tp = 0.008
    z0 = tp
    for x in (-W / 2 + s / 2, W / 2 - s / 2):
        for y in (-D / 2 + s / 2, D / 2 - s / 2):
            K.box((s, s, H), (x, y, z0), mat, bevel=0.002, base=True, name="post")
            fp = K.box((s * 2.2, s * 2.2, tp), (x, y, 0), plate_m, bevel=0.0015, base=True, name="foot")
            KI.drill(fp, [(x + (0.016 if x > 0 else -0.016), y + (0.016 if y > 0 else -0.016), tp / 2)], 0.0045, 0.05)
    for z in (z0 + s / 2, z0 + H - s / 2):
        for y in (-D / 2 + s / 2, D / 2 - s / 2):
            K.box((W - 2 * s, s, s), (0, y, z), mat, bevel=0.002, name="rail")
        for x in (-W / 2 + s / 2, W / 2 - s / 2):
            K.box((s, D - 2 * s, s), (x, 0, z), mat, bevel=0.002, name="rail")
    # diagonal brace on the -Y face and gussets in the top corners
    L = math.hypot(W - 2 * s, H - 2 * s)
    ang = math.atan2(H - 2 * s, W - 2 * s)
    br = K.box((L, s * 0.7, s * 0.7), (0, -D / 2 + s / 2, z0 + H / 2), mat, bevel=0.0015, name="brace")
    br.rotation_euler = (0, -ang, 0)
    gus = [(0, 0), (0.06, 0), (0, 0.06)]
    for x, sx in ((-W / 2 + s, 1), (W / 2 - s, -1)):
        g = K.prism([(0, 0), (0.06 * sx, 0), (0, -0.06)], 0.006, (x, -D / 2 + s / 2, z0 + H - s), mat, bevel=0.001)
    for x in (-W / 2 + s / 2, W / 2 - s / 2):
        for y in (-D / 2 + s / 2, D / 2 - s / 2):
            K.box((s * 1.4, s * 1.4, 0.005), (x, y, z0 + H), plate_m, bevel=0.0015, base=True)
            K.cyl(0.005, 0.004, (x, y, z0 + H + 0.005), M.metal("dark_steel"), verts=6, bevel=0.001)
    return frame(pitch=54.0)


# --------------------------------------------------------------------------- magnet
def magnet(item, material, color, p):
    """Horseshoe magnet with ground steel pole pieces (copper -> electromagnet, chrome -> rare-earth
    discs, glow -> plasma containment coil)."""
    from icons import machines
    if material == "copper":
        return machines.electromagnet(item, material, color, p)
    if material in ("chrome", "silver", "lithium"):
        return machines.rare_earth(item, material, color, p)
    if material == "glow":
        return machines.plasma_coil(item, material, color, p)
    pm = KI.paint(color or (0.65, 0.02, 0.015), wear=0.3, grime=0.2, rough=0.35, rust=0.05, name="magnet_paint", coat=0.6)
    steel = KI.metal("steel", None, rough=0.2, dirt=0.2)
    Rm, arm = 0.1, 0.12
    w = h = 0.058
    path = [(-Rm, arm, h / 2)] + [(Rm * math.cos(a), Rm * math.sin(a) * 0.95, h / 2)
                                  for a in [math.pi + math.pi * i / 32 for i in range(33)]] + [(Rm, arm, h / 2)]
    path[1] = (-Rm, 0.0, h / 2)
    KI.sweep(path, KI.rect_section(w, h, 0.006), pm, name="horseshoe")
    for sx, letter in ((-1, "N"), (1, "S")):
        K.box((w, 0.04, h), (sx * Rm, arm + 0.02, h / 2), steel, bevel=0.003)
        KI.text_mesh(letter, 0.04, 0.0008, M.plastic((0.9, 0.9, 0.88), 0.4, name="white_paint"),
                     loc=(sx * Rm, arm - 0.04, h + 0.0002), rot=(0, 0, 0))
    objs = KI.model_objects()
    KI.group(objs, (0, 0, 0), (0, 0, math.radians(-30)))
    return frame(pitch=48.0)


# --------------------------------------------------------------------------- heat sink
def heat_sink(item, material, color, p):
    """Extruded aluminium fin stack on a base plate with copper heat pipes."""
    m = material or "aluminum"
    mat = KI.anodized(KI.lin(color)) if color else _mach(m, None, "aluminum", rough=0.3)
    W, D, T = 0.28, 0.22, 0.02
    K.box((W, D, T), (0, 0, 0), mat, bevel=0.002, base=True, name="base")
    nf = 14
    for i in range(nf):
        x = -W / 2 + 0.008 + i * (W - 0.016) / (nf - 1)
        K.box((0.0055, D, 0.15), (x, 0, T), mat, bevel=0.0012, base=True, name="fin")
    cu = KI.metal("copper", None, rough=0.25, dirt=0.25)
    for y in (-D * 0.28, 0.0, D * 0.28):
        pts = [(-W * 0.36, y, T + 0.17)] + [(-W * 0.36 + 0.0, y, T * 0.5)] + [(W * 0.36, y, T * 0.5), (W * 0.36, y, T + 0.17)]
        KI.sweep(_round_path(pts, 0.035), KI.circle_section(0.0075, 16), cu, name="heatpipe")
    KI.project_text("TDP 250W", 0.016, (0.0, -D / 2 - 0.0001, T * 0.5), (0, -1, 0), mat=M.metal("dark_steel"), depth=0.0006)
    o = KI.model_objects()
    KI.group(o, (0, 0, 0), (0, 0, 0.3))
    return frame(pitch=52.0)


def _round_path(pts, rad, n=8):
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        k = min(rad, (a - b).length / 2, (c - b).length / 2)
        p0, p2 = b + (a - b).normalized() * k, b + (c - b).normalized() * k
        for t in range(n + 1):
            u = t / n
            out.append(p0 * (1 - u) ** 2 + b * 2 * u * (1 - u) + p2 * u * u)
    out.append(pts[-1])
    return [tuple(v) for v in out]


# --------------------------------------------------------------------------- turbine blade
def _airfoil(chord, t=0.12, m=0.07, pp=0.4, n=20):
    up, lo = [], []
    for i in range(n + 1):
        x = (1 - math.cos(math.pi * i / n)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        yc = m / pp ** 2 * (2 * pp * x - x * x) if x < pp else m / (1 - pp) ** 2 * ((1 - 2 * pp) + 2 * pp * x - x * x)
        up.append(((x - 0.35) * chord, (yc + yt) * chord))
        lo.append(((x - 0.35) * chord, (yc - yt) * chord))
    return up + list(reversed(lo[1:-1]))


def turbine_blade(item, material, color, p):
    """Gas-turbine blade: fir-tree root, platform, twisted airfoil, tip shroud (heat-tinted)."""
    m = material or "titanium"
    mat = KI.metal(m, color, rough=0.22, dirt=0.25) if KI.is_metal(m) else KI.surf(m, color)
    # fir-tree root (profile in XZ, extruded along Y)
    prof = [(-0.018, 0.0), (0.018, 0.0), (0.024, 0.012), (0.02, 0.018), (0.03, 0.03), (0.025, 0.036), (0.036, 0.048),
            (0.03, 0.055), (0.042, 0.068), (-0.042, 0.068), (-0.03, 0.055), (-0.036, 0.048), (-0.025, 0.036),
            (-0.03, 0.03), (-0.02, 0.018), (-0.024, 0.012)]
    objs = [K.prism(prof, 0.075, (0, 0, 0), mat, bevel=0.0015, name="root")]
    objs.append(K.box((0.11, 0.095, 0.012), (0, 0, 0.068), mat, bevel=0.002, base=True, name="platform"))
    # lofted twisted airfoil
    bm = bmesh.new()
    rings = []
    span = 0.3
    ns = 14
    for s in range(ns + 1):
        u = s / ns
        chord = 0.12 - 0.035 * u
        tw = math.radians(-8 + 34 * u)
        sec = _airfoil(chord, 0.12 - 0.04 * u, 0.09)
        ring = []
        for x, y in sec:
            xr = x * math.cos(tw) - y * math.sin(tw)
            yr = x * math.sin(tw) + y * math.cos(tw)
            ring.append(bm.verts.new((yr, xr, 0.078 + span * u)))
        rings.append(ring)
    nn = len(rings[0])
    for A, B in zip(rings, rings[1:]):
        for j in range(nn):
            k = (j + 1) % nn
            bm.faces.new((A[j], A[k], B[k], B[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    KI._fix_normals(bm)
    objs.append(KI.finish("airfoil", bm, mat, smooth=50))
    tw = math.radians(30)
    shroud = K.box((0.075, 0.05, 0.01), (0, 0, 0.078 + span), mat, bevel=0.0015, base=True, name="shroud")
    shroud.rotation_euler = (0, 0, tw)
    objs.append(shroud)
    KI.group(objs, (0, 0, 0), (0, math.radians(-90), math.radians(-12)))
    KI.ground(objs)
    return frame(pitch=52.0)


# --------------------------------------------------------------------------- nozzle
def nozzle(item, material, color, p):
    """Regeneratively cooled bell nozzle on its side, sooty throat visible, with manifold and flange.
    variant 'valve' -> gate valve; params.glow = [r,g,b] makes the throat glow (plasma drives)."""
    if p.get("variant") == "valve":
        from icons import machines
        return machines.gate_valve(item, material, color, p)
    m = material or "copper"
    mat = KI.cast_metal(m, color, oxid=0.35) if KI.is_metal(m) else KI.surf(m, color)
    soot = KI.cast_metal("dark_steel", None, oxid=0.0, rough=0.8) if not p.get("glow") else KI.liquid(p["glow"], "glow", 1.0)
    dark = KI.metal("dark_steel", None, rough=0.6, dirt=0.9)
    Re, Rt, Rc, t = 0.15, 0.048, 0.075, 0.007
    zt, zc, zt2 = 0.25, 0.3, 0.38

    def bell_r(z):
        if z <= zt:
            return Rt + (Re - Rt) * (1 - z / zt) ** 1.7
        if z <= zc:
            return Rt + (Rc - Rt) * ((z - zt) / (zc - zt)) ** 0.8
        return Rc

    zs = [zt * i / 24 for i in range(25)] + [zt + (zc - zt) * i / 6 for i in range(1, 7)] + [zc + (zt2 - 0.02 - zc) * i / 4 for i in range(1, 5)]
    inner = [(bell_r(z) - t, z) for z in reversed(zs)]
    outer = [(bell_r(z), z) for z in zs[1:]]
    prof = [(0, zt2 - 0.02)] + inner + [(Re + 0.004, 0.0)] + outer + [(Rc + 0.03, zt2), (Rc + 0.03, zt2 + 0.02), (0.03, zt2 + 0.035),
                                                                     (0, zt2 + 0.035)]
    ids = [1] * (len(inner) + 1) + [0] * (len(prof))
    o = KI.lathe(prof, None, segs=128, name="bell", smooth=40, mat_ids=ids, mats=[mat, soot])
    me = o.data
    for v in me.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if 0.006 < v.co.z < zt and r > bell_r(v.co.z) - 0.001:
            th = math.atan2(v.co.y, v.co.x)
            k = 1 + 0.003 / r * abs(math.cos(th * 36))
            v.co.x *= k
            v.co.y *= k
    me.update()
    objs = [o]
    rm = bell_r(zt * 0.42) + 0.012
    objs.append(K.torus(rm, 0.012, (0, 0, zt * 0.42), dark, segs=64, rsegs=12))
    objs.append(K.torus(Re + 0.008, 0.007, (0, 0, 0.008), dark, segs=64, rsegs=10))
    for a in (0.6, 0.6 + math.pi):
        pts = [(rm * math.cos(a), rm * math.sin(a), zt * 0.42), ((rm + 0.02) * math.cos(a), (rm + 0.02) * math.sin(a), zt * 0.62),
               ((Rc + 0.03) * math.cos(a), (Rc + 0.03) * math.sin(a), zt2 - 0.01)]
        objs.append(KI.curve_tube(_round_path(pts, 0.04), 0.009, dark, name="feed"))
    objs += K.bolts((0, 0, zt2 + 0.02), Rc + 0.018, 12, r=0.006, h=0.008)
    objs.append(K.cyl(0.035, 0.05, (0, 0, zt2 + 0.035), dark, verts=24))
    objs.append(K.box((0.07, 0.07, 0.03), (0, 0, zt2 + 0.08), dark, bevel=0.004, base=True))
    g = KI.group(objs)
    d = Vector((math.cos(math.radians(100)), math.sin(math.radians(100)), 0.22)).normalized()
    g.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    KI.ground(objs)
    return frame(pitch=54.0)


# --------------------------------------------------------------------------- motor
def motor(item, material, color, p):
    """TEFC induction motor: finned frame, feet, fan cowl, keyed shaft, terminal box, nameplate.
    variant 'pump' -> close-coupled pump unit."""
    if p.get("variant") == "pump":
        from icons import machines
        return machines.pump_unit(item, material, color, p)
    if material in ("steel", "cast_iron", "iron"):
        pm = KI.paint(color or (0.03, 0.14, 0.38), wear=0.25, grime=0.35, rust=0.05)
    else:
        pm = _paint_or(material, color, (0.03, 0.14, 0.38), wear=0.25, grime=0.35, rust=0.05)
    dark = KI.metal("cast_iron", None, dirt=0.6)
    R, L = 0.11, 0.26
    zc = 0.14
    objs = []
    objs.append(K.cyl(R, L, (-L / 2, 0, zc), pm, rot=K.AXES["x"], verts=48, bevel=0.004, name="frame"))
    for k in range(22):
        a = math.tau * k / 22
        if math.sin(a) < -0.55:
            continue
        f = K.box((L * 0.9, 0.006, 0.026), (0, 0, 0), pm, bevel=0.0015, name="fin")
        f.location = (0, math.cos(a) * (R + 0.01), zc + math.sin(a) * (R + 0.01))
        f.rotation_euler = (a - math.pi / 2, 0, 0)
        objs.append(f)
    for x in (-L / 2 - 0.01, L / 2 + 0.01):
        objs.append(K.cyl(R * 1.02, 0.025, (x - 0.0125, 0, zc), pm, rot=K.AXES["x"], verts=48, bevel=0.004))
        for k in range(6):
            a = math.tau * k / 6 + 0.3
            objs.append(K.cyl(0.006, 0.006, (x + (0.0125 if x > 0 else -0.019), math.cos(a) * R * 0.85, zc + math.sin(a) * R * 0.85),
                              M.metal("dark_steel"), rot=K.AXES["x"], verts=6, bevel=0.001))
    # fan cowl at -X with intake slots
    cowl = KI.lathe([(0.0, 0.0), (R * 0.75, 0.0), (R * 0.98, 0.03), (R * 1.0, 0.09), (R * 1.0 - 0.003, 0.09), (0, 0.09)],
                    pm, segs=48, name="cowl", smooth=30)
    cowl.location = (-L / 2 - 0.025, 0, zc)
    cowl.rotation_euler = (0, -math.pi / 2, 0)
    objs.append(cowl)
    for k in range(5):
        y = -R * 0.5 + k * R * 0.25
        objs.append(K.box((0.004, 0.012, R * 1.0), (-L / 2 - 0.115, y, zc), M.plastic((0.005, 0.005, 0.005), 0.9),
                          bevel=0.001))
    # shaft + key at +X
    sh = KI.metal("steel", None, rough=0.18, dirt=0.15)
    objs.append(K.cyl(0.028, 0.03, (L / 2 + 0.02, 0, zc), dark, rot=K.AXES["x"], verts=32))
    objs.append(K.cyl(0.02, 0.085, (L / 2 + 0.045, 0, zc), sh, rot=K.AXES["x"], verts=32, bevel=0.002))
    objs.append(K.box((0.05, 0.008, 0.006), (L / 2 + 0.095, 0, zc + 0.021), sh, bevel=0.001))
    # feet
    for x in (-L * 0.3, L * 0.3):
        fp = K.box((0.05, 2 * R + 0.05, 0.016), (x, 0, 0), pm, bevel=0.003, base=True, name="foot")
        KI.drill(fp, [(x, sy * (R + 0.008), 0.008) for sy in (-1, 1)], 0.007, 0.06)
        objs.append(fp)
        objs.append(K.box((0.04, R * 1.3, zc - 0.03), (x, 0, 0.016), pm, bevel=0.004, base=True))
    # terminal box + gland
    objs.append(K.box((0.09, 0.08, 0.05), (0.02, 0, zc + R - 0.01), pm, bevel=0.006, base=True, name="tbox"))
    objs.append(K.box((0.094, 0.084, 0.008), (0.02, 0, zc + R + 0.04), pm, bevel=0.003, base=True))
    objs.append(K.cyl(0.012, 0.02, (0.02, -0.04, zc + R + 0.015), M.plastic((0.02, 0.02, 0.02), 0.5), rot=K.AXES["-y"], verts=16))
    # nameplate on the -Y side
    ang = math.radians(-100)
    K.box((0.08, 0.002, 0.04), (0.04, -(R + 0.024), zc), M.metal("aluminum", dirt=0.3), bevel=0.0005)
    KI.project_text("3~ 15 kW", 0.01, (0.04, -(R + 0.0252), zc + 0.007), (0, -1, 0), mat=M.metal("dark_steel"), depth=0.0005)
    KI.project_text("IE3  400V", 0.008, (0.04, -(R + 0.0252), zc - 0.008), (0, -1, 0), mat=M.metal("dark_steel"), depth=0.0005)
    o = KI.model_objects()
    KI.group(o, (0, 0, 0), (0, 0, math.radians(-12)))
    return frame(pitch=55.0)


# --------------------------------------------------------------------------- servo arm
def _link(a, b, w, h, mat, name="link"):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = K.box((d.length, w, h), (a + b) / 2, mat, bevel=min(w, h) * 0.3, name=name)
    o.rotation_euler = (0, -math.atan2(d.z, math.hypot(d.x, d.y)), math.atan2(d.y, d.x))
    return o


def servo_arm(item, material, color, p):
    """Six-axis industrial robot arm with a two-finger gripper."""
    pm = _paint_or(material, color, (0.75, 0.25, 0.005), wear=0.15, grime=0.2, rough=0.35, rust=0.0)
    dark = M.painted((0.03, 0.032, 0.035), wear=0.1, grime=0.3, rough=0.45, name="graphite")
    steel = KI.metal("steel", None, rough=0.25, dirt=0.2)
    objs = []
    objs.append(KI.lathe([(0, 0), (0.12, 0), (0.12, 0.03), (0.1, 0.045), (0.0, 0.045)], dark, segs=64, name="base"))
    for k in range(6):
        a = math.tau * k / 6
        objs.append(K.cyl(0.007, 0.006, (0.105 * math.cos(a), 0.105 * math.sin(a), 0.03), steel, verts=6, bevel=0.001))
    objs.append(KI.lathe([(0, 0.045), (0.085, 0.045), (0.085, 0.1), (0.07, 0.115), (0, 0.115)], pm, segs=64, name="turret"))
    sh = Vector((0.0, 0.0, 0.17))
    objs.append(K.box((0.12, 0.13, 0.08), (0, 0, 0.1), pm, bevel=0.02, base=True, name="shoulder"))
    objs.append(K.cyl(0.058, 0.17, (0, -0.085, sh.z), dark, rot=K.AXES["y"], verts=40, bevel=0.004))
    el = sh + Vector((-0.08, 0, 0.26))
    objs.append(_link(sh, el, 0.085, 0.09, pm, "upper_arm"))
    objs.append(K.cyl(0.048, 0.13, (el.x, -0.065, el.z), dark, rot=K.AXES["y"], verts=40, bevel=0.004))
    wr = el + Vector((0.24, 0, -0.06))
    objs.append(_link(el, wr, 0.065, 0.07, pm, "forearm"))
    objs.append(K.cyl(0.036, 0.09, (wr.x, -0.045, wr.z), dark, rot=K.AXES["y"], verts=32, bevel=0.003))
    tip = wr + Vector((0.03, 0, -0.07))
    objs.append(_link(wr, tip, 0.05, 0.05, pm, "wrist"))
    objs.append(K.cyl(0.03, 0.015, tip + Vector((0, 0, -0.015)), steel, verts=32))
    gb = tip + Vector((0, 0, -0.04))
    objs.append(K.box((0.07, 0.03, 0.025), gb, dark, bevel=0.004))
    for s in (-1, 1):
        objs.append(K.box((0.012, 0.022, 0.05), gb + Vector((s * 0.022, 0, -0.035)), steel, bevel=0.002))
    # cable loom along the upper arm
    objs.append(KI.curve_tube(_round_path([tuple(sh + Vector((0.05, 0.05, -0.03))), tuple(sh + Vector((0.03, 0.06, 0.12))),
                                           tuple(el + Vector((0.03, 0.06, -0.02)))], 0.05), 0.009,
                              M.plastic((0.02, 0.02, 0.02), 0.6), name="loom"))
    dd = el - sh
    KI.project_text("IX-6", 0.03, ((sh + el) / 2) + Vector((0, -0.0435, 0)), (0, -1, 0), up=(-dd.z, 0, dd.x),
                    mat=M.plastic((0.9, 0.9, 0.88), 0.4, name="white_print"), depth=0.0006)
    o = KI.model_objects()
    KI.group(o, (0, 0, 0), (0, 0, math.radians(20)))
    KI.ground(o)
    return frame(pitch=58.0)


# --------------------------------------------------------------------------- tank part
def tank_part(item, material, color, p):
    """Horizontal pressure vessel on saddles with manway, nozzles, gauge and nameplate."""
    pm = _paint_or(material, color, (0.62, 0.62, 0.6), wear=0.2, grime=0.35, rough=0.4, rust=0.08)
    R, L = 0.115, 0.3
    hd = R * 0.5
    prof = [(0, -hd)] + [(R * math.sin(a), -hd * math.cos(a)) for a in [math.pi / 2 * i / 12 for i in range(1, 13)]]
    prof += [(R, L)] + [(R * math.cos(a), L + hd * math.sin(a)) for a in [math.pi / 2 * i / 12 for i in range(1, 12)]]
    prof += [(0, L + hd)]
    shell = KI.lathe(prof, pm, segs=64, name="shell")
    shell.rotation_euler = (0, math.pi / 2, 0)
    shell.location = (-L / 2, 0, R + 0.05)
    objs = [shell]
    zc = R + 0.05
    sad = KI.paint((0.05, 0.05, 0.055), wear=0.3, grime=0.5, rust=0.2, name="saddle")
    for x in (-L * 0.3, L * 0.3):
        objs.append(K.box((0.03, R * 1.5, 0.012), (x, 0, 0), sad, bevel=0.002, base=True))
        objs.append(K.box((0.012, R * 1.3, zc - R * 0.55), (x, 0, 0.012), sad, bevel=0.002, base=True))
        objs.append(KI.lathe([(R + 0.001, -0.015), (R + 0.008, -0.015), (R + 0.008, 0.015), (R + 0.001, 0.015)], sad,
                             segs=64, closed=True))
        objs[-1].rotation_euler = (0, math.pi / 2, 0)
        objs[-1].location = (x, 0, zc)
    steel = KI.metal("steel", None, dirt=0.5)
    # manway on top
    objs.append(K.cyl(0.05, 0.05, (0.03, 0, zc + R - 0.01), pm, verts=40))
    objs.append(K.cyl(0.068, 0.016, (0.03, 0, zc + R + 0.04), pm, verts=40, bevel=0.003))
    objs += K.bolts((0.03, 0, zc + R + 0.056), 0.058, 10, r=0.0055, h=0.007)
    objs.append(K.cyl(0.01, 0.04, (0.03, 0, zc + R + 0.056), steel, verts=12))
    # small nozzle + valve + gauge
    objs.append(K.cyl(0.018, 0.05, (-0.1, 0, zc + R - 0.01), pm, verts=24))
    objs.append(K.cyl(0.03, 0.01, (-0.1, 0, zc + R + 0.04), pm, verts=24))
    g = K.cyl(0.03, 0.016, (-0.1, -0.008, zc + R + 0.085), KI.metal("brass", None, dirt=0.3), rot=K.AXES["-y"], verts=32, base=False)
    K.cyl(0.006, 0.04, (-0.1, 0, zc + R + 0.05), KI.metal("brass", None, dirt=0.3), verts=10)
    K.cyl(0.026, 0.002, (-0.1, -0.017, zc + R + 0.085), M.plastic((0.9, 0.9, 0.88)), rot=K.AXES["-y"], verts=32, base=False, bevel=0)
    # nameplate
    K.box((0.08, 0.002, 0.045), (0.0, -R - 0.001, zc), M.metal("stainless", dirt=0.3), bevel=0.0005)
    KI.project_text("PN 16", 0.014, (0.0, -R - 0.0025, zc + 0.006), (0, -1, 0), mat=M.metal("dark_steel"), depth=0.0005)
    KI.project_text("V = 50 L", 0.009, (0.0, -R - 0.0025, zc - 0.011), (0, -1, 0), mat=M.metal("dark_steel"), depth=0.0005)
    o = KI.model_objects()
    KI.group(o, (0, 0, 0), (0, 0, math.radians(-8)))
    return frame(pitch=55.0)


# --------------------------------------------------------------------------- antenna
def antenna(item, material, color, p):
    """Parabolic dish antenna with feed horn on struts, yoke mount and mast."""
    dm = _paint_or(material, color, (0.62, 0.63, 0.61), wear=0.1, grime=0.3, rough=0.6, rust=0.0) \
        if not KI.is_metal(material or "") else KI.metal(material, None, rough=0.6, dirt=0.5)
    dark = M.painted((0.05, 0.05, 0.055), wear=0.2, grime=0.4, name="mount")
    Rd, f = 0.17, 0.11
    prof_f = [(r, r * r / (4 * f)) for r in [Rd * i / 20 for i in range(21)]]
    prof = [(0, 0.0)] + prof_f[1:] + [(Rd + 0.006, Rd * Rd / (4 * f) + 0.004)] + \
        [(r, r * r / (4 * f) - 0.008) for r in [Rd * (20 - i) / 20 for i in range(21)]][:-1] + [(0, -0.008)]
    dish = KI.lathe(list(reversed(prof)), dm, segs=72, name="dish", smooth=50)
    parts = [dish]
    parts.append(K.cyl(0.018, 0.04, (0, 0, f - 0.02), dark, verts=24))
    parts.append(K.box((0.03, 0.03, 0.05), (0, 0, f + 0.02), M.plastic((0.85, 0.85, 0.83), 0.4), bevel=0.005))
    for k in range(3):
        a = math.tau * k / 3 + 0.5
        rim = Vector((Rd * 0.97 * math.cos(a), Rd * 0.97 * math.sin(a), (Rd * 0.97) ** 2 / (4 * f)))
        parts.append(KI.curve_tube([tuple(rim), (0.0, 0.0, f - 0.01)], 0.004, dark, name="strut"))
    parts.append(K.cyl(0.05, 0.04, (0, 0, -0.045), dark, verts=24))
    g = KI.group(parts, (0, 0, 0), (0, 0, 0))
    g.rotation_euler = Euler((math.radians(55), 0, math.radians(15)), "XYZ")
    g.location = (0, 0, 0.27)
    mast = [K.box((0.18, 0.18, 0.015), (0, 0.04, 0), dark, bevel=0.003, base=True),
            K.cyl(0.022, 0.25, (0, 0.04, 0.015), KI.metal("steel", None, dirt=0.3), verts=24),
            K.box((0.05, 0.05, 0.05), (0, 0.04, 0.24), dark, bevel=0.006, base=False)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.cyl(0.006, 0.005, (sx * 0.07, 0.04 + sy * 0.07, 0.015), M.metal("dark_steel"), verts=6, bevel=0.001)
    o = KI.model_objects()
    KI.ground(o)
    return frame(pitch=56.0)


ARCHETYPES = {
    "gear": gear,
    "bolts": bolts,
    "spring": spring,
    "bearing": bearing,
    "frame": frame_,
    "magnet": magnet,
    "heat_sink": heat_sink,
    "turbine_blade": turbine_blade,
    "nozzle": nozzle,
    "motor": motor,
    "servo_arm": servo_arm,
    "tank_part": tank_part,
    "antenna": antenna,
}
