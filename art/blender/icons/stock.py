"""Semi-finished stock icons: ingot, plate, plate stack, sheet coil, rod bundle, beam, pipe, wire spool,
cable coil, glass pane, brick, block."""
import math
import random

import bmesh
from mathutils import Euler, Vector

import kit as K
import kit_icons as KI
import materials as M
from icons import frame


def _metal(material, color, default="steel", **kw):
    m = material or default
    if KI.is_metal(m):
        return KI.metal(m, color, **kw)
    return KI.surf(m, color)


def _stock(material, color, default="steel"):
    """Rolled / drawn stock: mill-scale mottling for ferrous metals, brushed finish for the rest."""
    m = material or default
    if m in ("iron", "steel", "cast_iron", "dark_steel"):
        return KI.cast_metal(m, color, oxid=0.7, scale=3.0)
    if KI.is_metal(m):
        return KI.metal(m, color, dirt=0.45)
    if m == "paint":
        return KI.paint(color or (0.3, 0.07, 0.03), wear=0.3, grime=0.4, rust=0.2, name="primer")
    return KI.surf(m, color)


def _frustum_bar(L, W, H, taper=0.012, name="ingot", mat=None, bevel=0.005):
    """Trapezoidal bar: bottom L x W, top shrunk by `taper` on each side."""
    bm = bmesh.new()
    b = [bm.verts.new(v) for v in ((-L / 2, -W / 2, 0), (L / 2, -W / 2, 0), (L / 2, W / 2, 0), (-L / 2, W / 2, 0))]
    tl, tw = L / 2 - taper * 1.6, W / 2 - taper
    t = [bm.verts.new(v) for v in ((-tl, -tw, H), (tl, -tw, H), (tl, tw, H), (-tl, tw, H))]
    bm.faces.new(list(reversed(b)))
    bm.faces.new(t)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((b[i], b[j], t[j], t[i]))
    KI._fix_normals(bm)
    return KI.finish(name, bm, mat, bevel=bevel, segments=3)


def _face_mats(o, side_mat_index_fn):
    for poly in o.data.polygons:
        poly.material_index = side_mat_index_fn(poly.normal)


def ingot(item, material, color, p):
    """Three cast ingots (2 + 1) with stamped assay marks."""
    m = material or "copper"
    mat = KI.cast_metal(m, color) if KI.is_metal(m) else KI.surf(m, color)
    L, W, H = 0.3, 0.1, 0.058
    mark = p.get("stamp") or KI.STAMP.get(m, (item.get("name") or "")[:6].upper())
    for k, (y, z) in enumerate(((-W / 2 - 0.006, 0.0), (W / 2 + 0.006, 0.0), (0.0, H))):
        o = _frustum_bar(L, W, H, 0.011, mat=mat)
        KI.stamp(o, mark, 0.026, (0.0, 0.0, H), depth=0.0012)
        if k == 2:
            KI.stamp(o, "No 4471", 0.011, (L * 0.31, 0.0, H), rot=(0, 0, math.pi / 2), depth=0.0008)
        o.location = (0.0 if k < 2 else 0.012, y, z)
        o.rotation_euler = (0, 0, 0.0 if k < 2 else 0.04)
    return frame(pitch=54.0)


def plate(item, material, color, p):
    """Thick machined plate with drilled corner holes and a stamped heat number (silicon -> wafer)."""
    if material == "silicon":
        from icons import machines
        return machines.wafer(item, material, color, p)
    mat = _stock(material, color)
    S, D, T = 0.36, 0.29, 0.022
    o = K.box((S, D, T), (0, 0, 0), mat, bevel=0.003, base=True, name="plate")
    ins = 0.035
    KI.drill(o, [(sx * (S / 2 - ins), sy * (D / 2 - ins), T / 2) for sx in (-1, 1) for sy in (-1, 1)], 0.013, T * 3)
    KI.drill(o, [(0, 0, T / 2)], 0.03, T * 3, verts=40)
    KI.stamp(o, KI.STAMP.get(material or "", "S355"), 0.022, (-S * 0.18, -D * 0.3, T), depth=0.0008)
    o.rotation_euler = (0, 0, 0.22)
    return frame(pitch=46.0)


def plate_stack(item, material, color, p):
    """Strapped stack of plates."""
    mat = _stock(material, color)
    rnd = KI.rnd_for(item["id"])
    S, D, T = 0.36, 0.27, 0.017
    n = 6
    for i in range(n):
        o = K.box((S, D, T), (rnd.uniform(-0.006, 0.006), rnd.uniform(-0.006, 0.006), i * T), mat, bevel=0.0025,
                  base=True, name="plate")
        o.rotation_euler = (0, 0, rnd.uniform(-0.025, 0.025))
    strap = M.painted((0.02, 0.05, 0.12), wear=0.4, grime=0.3, rough=0.4, name="strap")
    Ht = n * T
    for x in (-S * 0.28, S * 0.28):
        K.box((0.022, D + 0.006, 0.002), (x, 0, Ht + 0.001), strap, bevel=0.0006)
        for sy in (-1, 1):
            K.box((0.022, 0.002, Ht + 0.002), (x, sy * (D / 2 + 0.004), 0), strap, bevel=0.0006, base=True)
        K.box((0.03, 0.012, 0.008), (x, -D / 2 - 0.006, Ht * 0.55), M.metal("steel", dirt=0.6), bevel=0.001)
    return frame(pitch=50.0)


def sheet_coil(item, material, color, p):
    """Wound sheet coil lying on its side with radial and circumferential straps."""
    m = material or "steel"
    outer = _stock(m, color)
    end = KI.coil_end(m, color) if KI.is_metal(m) else KI.surf(m, color)
    R, ri, W = 0.2, 0.085, 0.2
    objs = [KI.lathe([(ri, 0), (R, 0), (R, W), (ri, W)], None, segs=96, closed=True, mat_ids=[0, 1, 0, 2],
                     mats=[end, outer, M.metal(m if KI.is_metal(m) else "steel", dirt=0.8)], name="coil", smooth=30)]
    strap = M.painted((0.025, 0.03, 0.04), wear=0.5, grime=0.4, rough=0.45, name="strap")
    for z in (W * 0.22, W * 0.78):
        objs.append(KI.lathe([(R, z - 0.011), (R + 0.0025, z - 0.011), (R + 0.0025, z + 0.011), (R, z + 0.011)], strap,
                             segs=96, closed=True, name="band"))
    for k in range(3):
        a = k * math.tau / 3 + 0.5
        loop = [(ri - 0.0025, -0.0025), (R + 0.004, -0.0025), (R + 0.004, W + 0.0025), (ri - 0.0025, W + 0.0025)]
        path = []
        for (r0, z0), (r1, z1) in zip(loop, loop[1:] + loop[:1]):
            for i in range(6):
                u = i / 6
                rr, zz = r0 + (r1 - r0) * u, z0 + (z1 - z0) * u
                path.append((rr * math.cos(a), rr * math.sin(a), zz))
        objs.append(KI.sweep(path, [(-0.0012, -0.009), (0.0012, -0.009), (0.0012, 0.009), (-0.0012, 0.009)], strap,
                             closed=True, name="radial_strap"))
        # crimp seal
        objs.append(K.box((0.012, 0.026, 0.03), (0, 0, 0), M.metal("steel", dirt=0.5), bevel=0.002))
        objs[-1].location = ((R + 0.008) * math.cos(a), (R + 0.008) * math.sin(a), W / 2)
        objs[-1].rotation_euler = (0, 0, a)
    KI.group(objs, (0, 0, 0), (math.pi / 2, 0, -0.45))
    KI.ground(objs)
    return frame(pitch=52.0)


def rod(item, material, color, p):
    """Bundle of seven round bars, wire-tied, with colour-coded painted ends (variant 'cylinder' ->
    hydraulic cylinder)."""
    if p.get("variant") == "cylinder":
        from icons import machines
        return machines.hydraulic_cylinder(item, material, color, p)
    m = material or "steel"
    mat = _stock(m, color)
    rnd = KI.rnd_for(item["id"])
    r, L = 0.024, 0.52
    code = KI.paint(p.get("end_color", (0.6, 0.05, 0.02) if m in ("iron", "steel") else (0.02, 0.15, 0.6)), wear=0.2,
                    grime=0.2, rust=0.0, name="end_paint")
    centres = [(0, 0)] + [(2.04 * r * math.cos(k * math.pi / 3), 2.04 * r * math.sin(k * math.pi / 3)) for k in range(6)]
    objs = []
    for (y, z) in centres:
        dx = rnd.uniform(-0.012, 0.012)
        objs.append(K.cyl(r, L, (dx - L / 2, y, z), mat, rot=K.AXES["x"], verts=32, bevel=0.002, name="bar"))
        objs.append(K.cyl(r * 0.995, 0.0015, (dx + L / 2, y, z), code, rot=K.AXES["x"], verts=32, bevel=0, name="cap"))
    wire = M.metal("iron", dirt=0.9)
    for x in (-0.15, 0.15):
        objs.append(K.torus(3.05 * r + 0.0025, 0.0025, (x, 0, 0), wire, rot=K.AXES["x"], segs=48, rsegs=8))
    KI.group(objs, (0, 0, 0), (0, 0, 0.12))
    KI.ground(objs)
    return frame(pitch=52.0)


def beam(item, material, color, p):
    """Short wide-flange I-beam section with punched web holes and rolled-in mill marks."""
    m = material or "steel"
    mat = _stock(m, color)
    L, h, w = 0.46, 0.2, 0.15
    o = K.ibeam(L, h, w, (0, 0, h / 2), mat=mat)
    KI.drill(o, [(x, 0, h / 2 + dz) for x in (-0.15, 0.15) for dz in (-0.035, 0.035)], 0.011, 0.1, axis="y")
    KI.project_text("HEB 200  S355", 0.016, (0.02, -0.0089, h / 2), (0, -1, 0), mat=mat, depth=0.0012)
    objs = [o for o in K.collection().objects]
    KI.group(objs, (0, 0, 0), (0, 0, math.pi / 2 - 0.25))
    KI.ground(objs)
    return frame(pitch=54.0)


def pipe(item, material, color, p):
    """Flanged pipe spool lying on the floor."""
    m = material or "steel"
    mat = _stock(m, color)
    R, r, L = 0.055, 0.045, 0.42
    Rf, tf = 0.105, 0.016
    objs = [KI.lathe([(R, 0), (R, L), (r, L), (r, 0)], mat, segs=64, closed=True, name="pipe")]
    inner = M.metal("dark_steel", rough=0.7, dirt=1.0)
    objs.append(KI.lathe([(r - 0.0002, 0.001), (r - 0.0002, L - 0.001)], inner, segs=64, name="bore"))
    fl = _stock(m, color)
    for z0, flip in ((0.0, False), (L, True)):
        prof = [(r, 0), (Rf, 0), (Rf, tf), (R + 0.012, tf), (R + 0.003, tf + 0.03), (r, tf + 0.03)]
        f = KI.lathe(prof, fl, segs=64, closed=True, name="flange")
        KI.drill(f, [((Rf + R) / 2 * math.cos(a), (Rf + R) / 2 * math.sin(a), tf / 2)
                     for a in [k * math.tau / 8 + math.pi / 8 for k in range(8)]], 0.008, tf * 4)
        if flip:
            f.rotation_euler = (math.pi, 0, 0)
            f.location.z = L
        objs.append(f)
    KI.group(objs, (0, 0, 0), (0, math.pi / 2, -0.55))
    KI.ground(objs)
    return frame(pitch=52.0)


def wire_spool(item, material, color, p):
    """Plastic reel of wound wire with a loose end."""
    m = material or "copper"
    wmat = KI.metal(m, color, rough=0.25, dirt=0.25) if KI.is_metal(m) else KI.surf(m, color)
    spool = M.plastic(p.get("spool_color", (0.04, 0.045, 0.05)), 0.4, name="spool")
    Rf, rc, W, tf = 0.17, 0.05, 0.15, 0.014
    Rw = 0.13
    wr = 0.0045
    objs = []
    for z in (0.0, W + tf):
        objs.append(KI.lathe([(0.025, z), (Rf, z), (Rf + 0.003, z + 0.004), (Rf + 0.003, z + tf - 0.004), (Rf, z + tf),
                              (0.025, z + tf)], spool, segs=72, closed=True, name="flange"))
    objs.append(KI.lathe([(0.025, tf), (rc, tf), (rc, W + tf), (0.025, W + tf)], spool, segs=48, closed=True))
    objs.append(KI.lathe([(rc, tf), (Rw - wr, tf), (Rw - wr, W + tf), (rc, W + tf)], wmat, segs=72, closed=True))
    turns = (W - 2 * wr) / (2 * wr)
    pts = KI.helix_points(Rw, 2 * wr * 1.02, turns, z0=tf + wr, res=56)
    objs.append(KI.curve_tube(pts, wr, wmat, name="winding"))
    # loose end leading off the reel
    a_end = 2 * math.pi * turns
    e = Vector(pts[-1])
    tang = Vector((-math.sin(a_end), math.cos(a_end), 0))
    tail = [tuple(e + tang * (0.03 * k) + Vector((0, 0, 0.004 * k))) for k in range(1, 6)]
    objs.append(KI.curve_tube([pts[-1]] + tail, wr, wmat, name="tail"))
    # spool label
    lab = M.plastic((0.85, 0.84, 0.78), 0.6, name="label")
    ztop = W + 2 * tf
    objs.append(K.cyl(0.075, 0.001, (0, 0, ztop - 0.0003), lab, verts=48, bevel=0, base=True))
    t = KI.text_mesh(p.get("label", "1.5 mm"), 0.022, 0.0006, M.plastic((0.04, 0.04, 0.04), 0.5, name="ink"),
                     loc=(0, 0, ztop + 0.0006), rot=(0, 0, math.pi / 2))
    objs.append(t)
    for k in range(6):
        a = k * math.tau / 6
        objs.append(K.cyl(0.018, tf + 0.002, (0.11 * math.cos(a), 0.11 * math.sin(a), W + tf - 0.001), M.plastic((0.0, 0.0, 0.0), 0.9),
                          verts=20, bevel=0))
    KI.group(objs, (0, 0, 0), (math.pi / 2, 0, -0.25))
    KI.ground(objs)
    return frame(pitch=54.0)


def cable_coil(item, material, color, p):
    """Loosely coiled insulated cable with a stripped end and a plug."""
    sheath = KI.surf(material or "rubber", color) if material not in (None, "rubber") else M.rubber((0.03, 0.03, 0.032), 3.0)
    if material == "glass":
        sheath = KI.gem((0.8, 0.9, 0.92), 0.15, 0.75, glow=0.25)
    rnd = KI.rnd_for(item["id"])
    cr = 0.014
    R = 0.15
    turns = 4.3

    def rfn(u):
        return R * (1 + 0.04 * math.sin(u * turns * 3.1 + 1.0))

    pts = []
    n = int(turns * 60)
    for i in range(n + 1):
        u = i / n
        a = 2 * math.pi * turns * u
        rr = rfn(u)
        x, y = rr * math.cos(a), rr * math.sin(a) * 0.92
        z = cr + 0.018 * turns * u + 0.012 * math.sin(a + 0.6)
        pts.append((x + 0.02 * math.sin(u * 7), y, max(cr, z)))
    objs = [KI.curve_tube(pts, cr, sheath, name="cable", res=3)]
    # outer end runs out across the floor to stripped cores
    e = Vector(pts[-1])
    a_end = 2 * math.pi * turns
    d = Vector((-math.sin(a_end), math.cos(a_end), 0)).normalized()
    tail = [e + d * 0.04 * k + Vector((0, 0, -(e.z - cr) * min(1, k / 3))) for k in range(1, 5)]
    tail = [tuple(v) for v in tail]
    objs.append(KI.curve_tube([pts[-1]] + tail, cr, sheath, name="tail"))
    tip = Vector(tail[-1])
    cores = [(0.25, 0.1, 0.02), (0.02, 0.1, 0.5), (0.5, 0.45, 0.02)]
    side = Vector((-d.y, d.x, 0))
    cu = KI.metal("copper", None, rough=0.25, dirt=0.2)
    for k, cc in enumerate(cores):
        off = side * (k - 1) * 0.011
        c_pts = [tuple(tip), tuple(tip + d * 0.02 + off * 0.6), tuple(tip + d * 0.05 + off)]
        objs.append(KI.curve_tube(c_pts, 0.0055, M.plastic(cc, 0.35, name="core"), name="core"))
        a = tip + d * 0.05 + off
        objs.append(KI.curve_tube([tuple(a), tuple(a + d * 0.016)], 0.0032, cu, name="cu"))
    # inner end climbs over the coil to a plug
    s = Vector(pts[0])
    plug_pts = [tuple(s), tuple(s + Vector((-0.03, -0.02, 0.0))), tuple(s + Vector((-0.06, -0.05, 0.0)))]
    objs.append(KI.curve_tube(plug_pts, cr, sheath, name="lead"))
    pe = Vector(plug_pts[-1])
    pd = (pe - Vector(plug_pts[-2])).normalized()
    plug = KI.lathe([(0, 0), (cr * 1.2, 0), (0.024, 0.03), (0.026, 0.07), (0.022, 0.075), (0, 0.075)],
                    M.plastic((0.6, 0.35, 0.02), 0.45, name="plug") if not color else M.plastic((0.04, 0.04, 0.04), 0.4),
                    segs=32, name="plug")
    plug.location = pe
    plug.rotation_euler = pd.to_track_quat("Z", "Y").to_euler()
    objs.append(plug)
    for k in (-1, 1):
        pin = K.cyl(0.0035, 0.025, (0, 0, 0), KI.metal("brass", None, dirt=0.3), verts=10, bevel=0.0005)
        pin.location = pe + pd * 0.075 + Vector((-pd.y, pd.x, 0)) * 0.009 * k
        pin.rotation_euler = plug.rotation_euler
        objs.append(pin)
    KI.ground(objs)
    return frame(pitch=50.0)


def glass_pane(item, material, color, p):
    """Stack of float-glass sheets on timber battens (green edges)."""
    tint = KI.lin(color) if color else (0.9, 0.97, 0.95)
    face = KI.gem((0.72, 0.86, 0.84) if not color else tint, 0.02, 0.18)
    edge = KI.gem((0.25, 0.7, 0.5), 0.02, 0.8)
    batten = KI.wood((0.35, 0.22, 0.1), axis="y")
    S, D, T = 0.38, 0.28, 0.01
    objs = []
    for x in (-S * 0.3, S * 0.3):
        objs.append(K.box((0.04, D + 0.04, 0.03), (x, 0, 0), batten, bevel=0.003, base=True, name="batten"))
    rnd = KI.rnd_for(item["id"])
    for i in range(3):
        o = K.box((S, D, T), (rnd.uniform(-0.012, 0.012), rnd.uniform(-0.01, 0.01), 0.03 + i * (T + 0.0015)), face,
                  bevel=0.0015, base=True, name="pane")
        o.data.materials.append(edge)
        _face_mats(o, lambda n: 0 if abs(n.z) > 0.7 else 1)
        o.rotation_euler = (0, 0, rnd.uniform(-0.03, 0.03))
        objs.append(o)
    # protective corner tape on the top sheet
    tape = M.plastic((0.75, 0.55, 0.05), 0.6, name="tape")
    objs.append(K.box((0.05, 0.05, 0.0012), (S / 2 - 0.03, -D / 2 + 0.03, 0.03 + 3 * (T + 0.0015)), tape, bevel=0.0004))
    KI.group(objs, (0, 0, 0), (0, 0, 0.18))
    return frame(pitch=46.0)


def brick(item, material, color, p):
    """Three perforated bricks, two side by side with one laid across."""
    mat = KI.surf(material or "brick_clay", color)
    if material in ("ceramic", None):
        mat = KI.rock(base=KI.lin(color) if color else (0.6, 0.48, 0.3), base2=(0.45, 0.33, 0.18), speck=(0.2, 0.12, 0.06),
                      speck_amt=0.6, rough=0.9, scale=6.0, name="firebrick")
    L, W, H = 0.27, 0.13, 0.082
    objs = []
    for k, (x, y, z, rz) in enumerate(((0, -W / 2 - 0.004, 0, 0), (0, W / 2 + 0.004, 0, 0), (0.01, 0, H, math.pi / 2 + 0.06))):
        o = K.box((L, W, H), (0, 0, 0), mat, bevel=0.006, base=True, name="brick")
        if material != "ceramic":
            KI.drill(o, [(dx, 0, H / 2) for dx in (-0.075, 0, 0.075)], 0.017, H * 3, verts=20)
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, rz)
        objs.append(o)
    KI.group(objs, (0, 0, 0), (0, 0, 0.12))
    return frame(pitch=52.0)


def block(item, material, color, p):
    """Concrete masonry unit (two cores) or a machined block of the material with an engraved mark."""
    m = material or "concrete"
    if m == "concrete":
        mat = M.concrete(3.0, tint=KI.lin(color) if color else None)
        L, W, H = 0.39, 0.19, 0.19
        o = K.box((L, W, H), (0, 0, 0), mat, bevel=0.004, base=True, name="cmu")
        for x in (-0.095, 0.095):
            cut = K.box((0.13, 0.12, H * 2), (x, 0, -H / 2), None, bevel=0.0, base=True, name="cutter")
            cut.hide_render = True
            KI.apply_boolean(o, cut)
        o.rotation_euler = (0, 0, 0.3)
        return frame(pitch=50.0)
    mat = KI.cast_metal(m, color) if KI.is_metal(m) else KI.surf(m, color)
    S = 0.3
    o = K.box((S, S * 0.8, S * 0.62), (0, 0, 0), mat, bevel=0.01, base=True, name="block")
    KI.stamp(o, KI.STAMP.get(m, (item.get("name") or "")[:4].upper()), 0.04, (0, 0, S * 0.62), depth=0.0015)
    o.rotation_euler = (0, 0, 0.25)
    return frame(pitch=52.0)


ARCHETYPES = {
    "ingot": ingot,
    "plate": plate,
    "plate_stack": plate_stack,
    "sheet_coil": sheet_coil,
    "rod": rod,
    "beam": beam,
    "pipe": pipe,
    "wire_spool": wire_spool,
    "cable_coil": cable_coil,
    "glass_pane": glass_pane,
    "brick": brick,
    "block": block,
}
