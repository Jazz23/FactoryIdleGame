"""Container icons: fluid orb, barrel, gas canister, lab flask, jerry canister, crate, capsule."""
import math
import random

import bmesh
from mathutils import Euler, Vector

import kit as K
import kit_icons as KI
import materials as M
from icons import frame


def _arc(R, zc, a0, a1, n):
    """Points (r, z) on a circle of radius R centred at (0, zc), angles in radians from +r axis."""
    return [(max(0.0, R * math.cos(a0 + (a1 - a0) * i / n)), zc + R * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _liquid_mode(material, color, p):
    if p.get("mode"):
        return p["mode"]
    if material == "glow":
        return "glow"
    if color and sum(color[:3]) < 0.12:
        return "opaque"
    return "clear"


def fluid_orb(item, material, color, p):
    """Heavy round-bottom glass flask in a steel cage with a valve cap, holding the coloured fluid."""
    col = color or KI.MAT_COLOR.get(material or "", None) or (0.08, 0.3, 0.85)
    if material == "glass" and not color:
        col = (0.08, 0.3, 0.85)
    R, t = 0.15, 0.008
    rr, R_ring = 0.012, 0.085
    zc = rr + math.sqrt((R + rr) ** 2 - R_ring ** 2) + 0.002
    neck_r = 0.046
    neck_top = zc + R + 0.07
    a_neck = math.acos(neck_r / R)
    ai_neck = math.acos((neck_r - t) / (R - t))
    prof = [(0, zc - R)] + _arc(R, zc, -math.pi / 2, a_neck, 40)[1:]
    prof += [(neck_r, neck_top - 0.006), (neck_r + 0.006, neck_top - 0.002), (neck_r + 0.004, neck_top),
             (neck_r - t, neck_top)]
    prof += _arc(R - t, zc, ai_neck, -math.pi / 2, 40)
    glass = KI.lab_glass()
    KI.lathe(prof, glass, segs=72, name="orb_glass", smooth=60)

    # contents
    Ri = R - t - 0.0006
    if p.get("gas"):
        vol = KI.gas_volume(col, density=p.get("density", 9.0), glow=p.get("glow", 0.0))
        KI.lathe([(0, zc - Ri)] + _arc(Ri, zc, -math.pi / 2, math.pi / 2, 32)[1:], vol, segs=48, name="gas")
        # faint condensate film on the glass bottom keeps the colour readable
        fill = p.get("fill", 0.12)
    else:
        fill = p.get("fill", 0.64)
    mode = _liquid_mode(material, color, p)
    zf = zc - Ri + 2 * Ri * fill
    af = math.asin(max(-1.0, min(1.0, (zf - zc) / Ri)))
    rf = Ri * math.cos(af)
    lprof = [(0, zc - Ri)] + _arc(Ri, zc, -math.pi / 2, af, 36)[1:]
    lprof += [(rf - 0.004, zf - 0.0025), (rf - 0.012, zf - 0.0035), (0, zf - 0.0035)]
    lmat = KI.liquid(col, mode) if not p.get("gas") else KI.liquid(col, "clear", 0.3)
    KI.lathe(lprof, lmat, segs=72, name="liquid", smooth=60)

    # cast-iron foot ring + steel cage + neck collar + valve cap
    iron = M.metal("cast_iron", dirt=0.6)
    steel = M.metal("stainless", dirt=0.5)
    brass = M.metal("brass", dirt=0.6)
    K.torus(R_ring, rr, (0, 0, rr), iron, segs=64, rsegs=14)
    for i in range(3):
        a = math.radians(120 * i + 25)
        K.cyl(0.016, 0.012, (math.cos(a) * R_ring, math.sin(a) * R_ring, 0), M.rubber(), verts=16)
    collar_z = neck_top - 0.045
    K.torus(neck_r + 0.007, 0.006, (0, 0, collar_z), steel, segs=48, rsegs=10)
    phi0 = -math.asin(min(1.0, (zc - rr) / (R + rr)))
    for i in range(3):
        a = math.radians(120 * i + 5)
        rad = R + 0.0045
        pts = []
        for k in range(33):
            phi = phi0 + (a_neck - phi0) * k / 32
            pts.append((math.cos(a) * rad * math.cos(phi), math.sin(a) * rad * math.cos(phi), zc + rad * math.sin(phi)))
        pts.append((math.cos(a) * (neck_r + 0.0045), math.sin(a) * (neck_r + 0.0045), collar_z))
        KI.sweep(pts, KI.rect_section(0.004, 0.014, 0.0012), steel, name="strap")
    # screw cap with grip ribs, gauge stem and valve wheel
    cz = neck_top - 0.03
    KI.lathe([(0, cz + 0.002), (neck_r + 0.012, cz), (neck_r + 0.014, cz + 0.003), (neck_r + 0.014, cz + 0.04),
              (neck_r + 0.01, cz + 0.044), (0.02, cz + 0.046), (0, cz + 0.046)], steel, segs=64, name="cap", smooth=40)
    for i in range(30):
        a = math.tau * i / 30
        K.box((0.004, 0.006, 0.03), (math.cos(a) * (neck_r + 0.0145), math.sin(a) * (neck_r + 0.0145), cz + 0.021),
              steel, rot=(0, 0, a), bevel=0.001)
    K.cyl(0.008, 0.035, (0, 0, cz + 0.045), brass, verts=16)
    K.torus(0.026, 0.004, (0, 0, cz + 0.08), M.painted((0.6, 0.03, 0.02), wear=0.3, grime=0.2, name="wheel"),
            segs=40, rsegs=8)
    for i in range(4):
        a = math.tau * i / 4 + 0.4
        K.cyl(0.0025, 0.026, (0, 0, cz + 0.08), M.painted((0.6, 0.03, 0.02), wear=0.3, grime=0.2, name="wheel"),
              rot=(0, math.pi / 2, a), base=True, verts=8, bevel=0)
    K.cyl(0.007, 0.012, (0, 0, cz + 0.078), brass, verts=12)
    # small pressure gauge on a side port of the cap
    gx, gy = math.cos(math.radians(-60)), math.sin(math.radians(-60))
    K.cyl(0.005, 0.03, (gx * (neck_r + 0.012), gy * (neck_r + 0.012), cz + 0.022), brass, rot=(0, math.pi / 2, math.radians(-60)),
          verts=10)
    g = K.cyl(0.018, 0.012, (gx * (neck_r + 0.045), gy * (neck_r + 0.045), cz + 0.022), brass,
              rot=(0, math.pi / 2, math.radians(-60)), verts=24, base=False)
    face = K.cyl(0.0155, 0.002, (gx * (neck_r + 0.0515), gy * (neck_r + 0.0515), cz + 0.022), M.plastic((0.85, 0.85, 0.8)),
                 rot=(0, math.pi / 2, math.radians(-60)), verts=24, base=False, bevel=0)
    return frame()


def barrel(item, material, color, p):
    """200 L steel drum: chimes, rolling hoops, bungs, label."""
    c = color or (0.55, 0.05, 0.02)
    tier = p.get("tier", 1)
    body = KI.paint(c, wear=0.3 - 0.05 * tier, grime=0.55 - 0.06 * tier, rough=0.38, rust=0.22 - 0.04 * tier,
                    name="drum_paint", scale=3.5) if material in (None, "paint", "steel", "iron") else KI.surf(material, color)
    R, H = 0.29, 0.88
    hoop = lambda z: [(R, z - 0.022), (R + 0.011, z - 0.008), (R + 0.011, z + 0.008), (R, z + 0.022)]
    prof = [(0, 0.016), (R - 0.016, 0.016), (R - 0.012, 0.0), (R + 0.006, 0.002), (R + 0.009, 0.014), (R, 0.03)]
    prof += hoop(0.3) + hoop(0.59)
    prof += [(R, H - 0.03), (R + 0.009, H - 0.014), (R + 0.006, H - 0.002), (R - 0.012, H), (R - 0.016, H - 0.016),
             (0, H - 0.016)]
    KI.lathe(prof, body, segs=96, name="drum", smooth=30)
    steel = M.metal("steel", dirt=0.7)
    for (x, y, r) in ((0.15, 0.12, 0.034), (-0.17, -0.1, 0.02)):
        K.cyl(r * 1.25, 0.006, (x, y, H - 0.016), body, verts=24)
        K.cyl(r, 0.014, (x, y, H - 0.012), steel, verts=6 if r < 0.025 else 24, bevel=0.002)
        if r > 0.025:
            for i in range(8):
                a = math.tau * i / 8
                K.box((0.006, 0.006, 0.004), (x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55, H + 0.003), steel,
                      rot=(0, 0, a), bevel=0.001)
    # label on the camera-facing side
    lab = M.plastic((0.82, 0.8, 0.72), 0.6, name="label")
    a0 = math.radians(-55)
    KI.wrap_patch(R + 0.001, a0, math.radians(56), 0.37, 0.52, lab)
    KI.wrap_text("INDUSTRIUM", R + 0.0025, a0, 0.47, 0.028, M.plastic((0.03, 0.03, 0.03), 0.6, name="ink"))
    KI.wrap_text(p.get("label", item.get("name", "").upper()[:14]), R + 0.0025, a0, 0.415, 0.022,
                 M.plastic((0.03, 0.03, 0.03), 0.6, name="ink"))
    return frame()


def gas_canister(item, material, color, p):
    """Compressed-gas cylinder: domed shoulder band, brass valve with handwheel, foot ring."""
    col = color or (0.05, 0.22, 0.07)
    body = KI.paint(col, wear=0.25, grime=0.3, rough=0.35, rust=0.08, name="cyl_paint", coat=0.3) \
        if material in (None, "paint", "steel") else KI.surf(material, color)
    shoulder = KI.paint((0.85, 0.85, 0.82), wear=0.15, grime=0.25, rough=0.4, rust=0.0, name="shoulder_paint")
    brass = KI.metal("brass", None, rough=0.3, dirt=0.4)
    steel = KI.metal("steel", None, dirt=0.5)
    R, H = 0.105, 0.4
    prof = [(0, 0.012), (R - 0.02, 0.012), (R - 0.004, 0.02), (R, 0.04), (R, H - 0.03)]
    dome = [(R * math.cos(a), H - 0.03 + 0.09 * math.sin(a)) for a in [math.pi / 2 * i / 12 for i in range(1, 12)]]
    neck = [(0.026, H + 0.06), (0.026, H + 0.075), (0, H + 0.075)]
    KI.lathe(prof + dome + neck, body, segs=72, name="cylinder", mat_ids=None)
    KI.lathe([(R * math.cos(a) + 0.0012, H - 0.03 + 0.09 * math.sin(a))
              for a in [math.pi / 2 * i / 12 for i in range(0, 9)]], shoulder, segs=72, name="shoulder")
    KI.lathe([(R + 0.004, 0.0), (R + 0.004, 0.045), (R + 0.0005, 0.048), (R + 0.0005, 0.0)], steel, segs=72, closed=True,
             name="foot")
    zv = H + 0.075
    K.cyl(0.022, 0.03, (0, 0, zv), brass, verts=6, bevel=0.002)
    K.cyl(0.02, 0.05, (0, 0, zv + 0.03), brass, verts=24, bevel=0.002)
    K.cyl(0.009, 0.05, (0, -0.0, zv + 0.045), brass, rot=K.AXES["-y"], verts=16, base=True)
    K.cyl(0.012, 0.012, (0, -0.05, zv + 0.045), brass, rot=K.AXES["-y"], verts=6, base=True)
    K.cyl(0.006, 0.03, (0, 0, zv + 0.08), steel, verts=12)
    wheel = M.painted((0.03, 0.03, 0.032), wear=0.2, grime=0.3, name="wheel")
    K.torus(0.032, 0.006, (0, 0, zv + 0.105), wheel, segs=40, rsegs=8)
    for k in range(5):
        a = math.tau * k / 5
        K.cyl(0.004, 0.03, (0, 0, zv + 0.105), wheel, rot=(0, math.pi / 2, a), verts=8, bevel=0)
    KI.wrap_text(p.get("label", _short(item)), R * 0.98 + 0.0015, math.radians(-55), H - 0.0, 0.028,
                 M.plastic((0.03, 0.03, 0.03), 0.5, name="ink"))
    KI.wrap_text("200 BAR", R + 0.0005, math.radians(-55), H * 0.55, 0.022, M.plastic((0.9, 0.9, 0.88), 0.4, name="white_print"))
    return frame(pitch=56.0)


FORMULA = {"steam": "H₂O", "superheated_steam": "H₂O", "hydrogen": "H₂", "oxygen": "O₂", "nitrogen": "N₂",
           "chlorine": "Cl₂", "ammonia": "NH₃", "natural_gas": "CH₄", "fuel_gas": "C₃H₈", "helium_gas": "He",
           "helium": "He", "deuterium": "D₂", "argon": "Ar", "carbon_dioxide": "CO₂"}


def _short(item):
    if item.get("id") in FORMULA:
        return FORMULA[item["id"]]
    name = (item.get("name") or "GAS").upper()
    words = name.split()
    return words[0][:8] if words else "GAS"


def flask(item, material, color, p):
    """Erlenmeyer flask with coloured reagent, rubber stopper and printed graduations."""
    col = color or (0.85, 0.12, 0.05)
    R0, Rn, H, Hn = 0.13, 0.032, 0.25, 0.08
    t = 0.006
    prof = [(0, 0.0), (R0 - 0.012, 0.0), (R0, 0.012), (R0 - 0.004, 0.03)]
    prof += [(Rn + (R0 - Rn) * (1 - u) ** 1.08, 0.03 + (H - 0.03) * u) for u in [i / 10 for i in range(1, 11)]]
    prof += [(Rn, H + Hn), (Rn + 0.006, H + Hn + 0.004), (Rn + 0.004, H + Hn + 0.01), (Rn - t, H + Hn + 0.01)]
    inner = [(Rn - t, H + 0.01)] + [(Rn - t + (R0 - Rn - t * 1.6) * (1 - u) ** 1.08, 0.03 + (H - 0.03) * u)
                                      for u in [i / 10 for i in range(9, -1, -1)]] + [(R0 - 0.016, t), (0, t)]
    KI.lathe(prof + inner, KI.lab_glass(), segs=72, name="flask", smooth=50)
    fill = p.get("fill", 0.42)
    zf = 0.03 + (H - 0.03) * fill
    lp = [(0, t + 0.0005), (R0 - 0.017, t + 0.0005), (R0 - t * 1.8 - 0.001, 0.03)]
    lp += [(Rn - t + (R0 - Rn - t * 1.6) * (1 - u) ** 1.08 - 0.0008, 0.03 + (H - 0.03) * u) for u in [fill * i / 6 for i in range(1, 7)]]
    rf = lp[-1][0]
    lp += [(rf - 0.006, zf - 0.002), (0, zf - 0.002)]
    KI.lathe(lp, KI.liquid(col, _liquid_mode(material, color, p)), segs=72, name="liquid", smooth=50)
    stopper = M.rubber((0.08, 0.02, 0.015), 3.0)
    KI.lathe([(0, H + Hn - 0.025), (Rn - t - 0.001, H + Hn - 0.025), (Rn + 0.003, H + Hn + 0.03), (Rn - 0.002, H + Hn + 0.035),
              (0, H + Hn + 0.035)], stopper, segs=48, name="stopper")
    white = M.plastic((0.92, 0.92, 0.9), 0.4, name="enamel")
    for k, z in enumerate((0.07, 0.11, 0.15)):
        u = (z - 0.03) / (H - 0.03)
        rz = Rn + (R0 - Rn) * (1 - u) ** 1.08 + 0.0008
        KI.wrap_patch(rz, math.radians(-75), 0.18, z - 0.0012, z + 0.0012, white, thick=0.0005, segs=8, name="grad")
        KI.wrap_text(str(100 * (k + 1)), rz + 0.0002, math.radians(-47), z, 0.014, white)
    return frame(pitch=56.0)


def canister(item, material, color, p):
    """Jerry can: pressed X ribs, triple handle, spout with locking cap."""
    col = color or (0.5, 0.04, 0.015)
    pm = KI.paint(col, wear=0.35, grime=0.4, rough=0.38, rust=0.15, name="can_paint") if material in (None, "paint", "steel") \
        else KI.surf(material, color)
    W, D, H = 0.34, 0.16, 0.42
    K.box((W, D, H), (0, 0, 0), pm, bevel=0.022, base=True, name="can")
    for sy in (-1, 1):
        y = sy * (D / 2 + 0.002)
        for a in (1, -1):
            L = math.hypot(W * 0.78, H * 0.72)
            r = K.box((L, 0.01, 0.022), (0, y, H * 0.5), pm, bevel=0.005, name="rib")
            r.rotation_euler = (0, a * math.atan2(H * 0.72, W * 0.78), 0)
        K.box((W * 0.82, 0.008, 0.02), (0, y, H * 0.12), pm, bevel=0.004)
        K.box((W * 0.82, 0.008, 0.02), (0, y, H * 0.88), pm, bevel=0.004)
    for x in (-0.08, 0.0, 0.08):
        path = [(x, -0.045, H - 0.005), (x, -0.045, H + 0.04), (x, 0.045, H + 0.04), (x, 0.045, H - 0.005)]
        KI.sweep(KI_round(path, 0.02), KI.rect_section(0.016, 0.014, 0.004), pm, name="handle")
    sx = W / 2 - 0.05
    K.cyl(0.026, 0.03, (sx, 0, H - 0.01), pm, verts=32, bevel=0.003)
    K.cyl(0.03, 0.026, (sx, 0, H + 0.02), pm, verts=32, bevel=0.005)
    K.box((0.05, 0.016, 0.01), (sx - 0.04, 0, H + 0.04), KI.metal("steel", None, dirt=0.5), bevel=0.002)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.35))
    return frame(pitch=55.0)


def KI_round(pts, rad, n=6):
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


def crate(item, material, color, p):
    """Nailed plank crate with corner battens, steel corner caps and stencil marks (metal material or
    variant 'avionics' -> rugged aluminium equipment case)."""
    if p.get("variant") == "avionics" or KI.is_metal(material or ""):
        from icons import machines
        return machines.flight_case(item, material, color, p)
    wc = KI.lin(color) if color and material in (None, "wood") else (0.36, 0.22, 0.1)
    planks_x = KI.wood(wc, axis="x")
    planks_y = KI.wood(wc, axis="y")
    batt = KI.wood(tuple(c * 0.8 for c in wc), axis="z")
    steel = KI.metal("steel", None, dirt=0.7)
    W, D, H = 0.44, 0.34, 0.32
    t = 0.014
    K.box((W - 0.01, D - 0.01, H - 0.01), (0, 0, 0.005), M.plastic((0.02, 0.015, 0.01), 0.9), bevel=0, base=True)
    n = 4
    gap = 0.006
    ph = (H - gap * (n - 1)) / n
    for i in range(n):
        z = i * (ph + gap)
        for sy in (-1, 1):
            K.box((W, t, ph), (0, sy * (D / 2 - t / 2), z), planks_x, bevel=0.002, base=True, name="plank")
        for sx in (-1, 1):
            K.box((t, D - 2 * t, ph), (sx * (W / 2 - t / 2), 0, z), planks_y, bevel=0.002, base=True, name="plank")
    pw = (W - gap * 3) / 4
    for i in range(4):
        x = -W / 2 + pw / 2 + i * (pw + gap)
        K.box((pw, D, t), (x, 0, H), planks_y, bevel=0.002, base=True, name="lid")
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.03, 0.03, H + t), (sx * (W / 2 + 0.008), sy * (D / 2 + 0.008), 0), batt, bevel=0.003, base=True)
            K.box((0.05, 0.05, 0.05), (sx * (W / 2 + 0.006), sy * (D / 2 + 0.006), H + t - 0.04), steel, bevel=0.004, base=True)
    for x in (-W / 2 + 0.06, W / 2 - 0.06):
        K.box((0.03, 0.006, H), (x, -D / 2 - 0.003, 0.0), batt, bevel=0.002, base=True)
    ink = M.plastic((0.02, 0.02, 0.02), 0.8, name="stencil_ink")
    KI.project_text("INDUSTRIUM", 0.034, (0, -D / 2 - 0.0002, H * 0.62), (0, -1, 0), mat=ink, depth=0.0003)
    KI.project_text(p.get("label", "FRAGILE  ↑↑"), 0.022, (0, -D / 2 - 0.0002, H * 0.36), (0, -1, 0), mat=ink,
                    depth=0.0003)
    for y in (-D / 2 + t / 2, D / 2 - t / 2):
        for x in (-W / 2 + 0.03, W / 2 - 0.03):
            for z in (0.04, H - 0.04):
                K.cyl(0.003, 0.002, (x, y - 0.008 if y < 0 else y + 0.008, z), steel, rot=K.AXES["y"], verts=8, base=False)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.1))
    return frame(pitch=55.0)


def capsule(item, material, color, p):
    """Sealed pill-shaped containment capsule with a glowing payload window and clamp bands."""
    col = color or (0.3, 1.0, 0.45)
    body = KI.metal(material, None, rough=0.22, dirt=0.3) if KI.is_metal(material or "") else \
        KI.metal("stainless", None, rough=0.22, dirt=0.3)
    R, L = 0.1, 0.3
    hz = L / 2
    cap = [(0, -hz - R)] + [(R * math.sin(a), -hz - R * math.cos(a)) for a in [math.pi / 2 * i / 12 for i in range(1, 13)]]
    left = cap + [(R, -0.07), (0, -0.07)]
    right = [(0, 0.07), (R, 0.07)] + [(R * math.cos(a), hz + R * math.sin(a)) for a in [math.pi / 2 * i / 12 for i in range(0, 12)]] \
        + [(0, hz + R)]
    objs = [KI.lathe(left, body, segs=64, name="end_l"), KI.lathe(right, body, segs=64, name="end_r")]
    objs.append(KI.lathe([(R * 0.96, -0.072), (R * 0.96, 0.072)], M.glass((0.9, 0.97, 0.95), 0.02), segs=64, name="window"))
    objs.append(KI.lathe([(0, -0.07), (R * 0.8, -0.07), (R * 0.8, 0.07), (0, 0.07)], KI.liquid(col, "glow", 0.45), segs=48,
                         name="payload"))
    dark = M.painted((0.03, 0.032, 0.035), wear=0.2, grime=0.3, rough=0.45, name="graphite")
    for z in (-0.075, 0.075, -0.16, 0.16):
        objs.append(KI.lathe([(R - 0.002, z - 0.011), (R + 0.008, z - 0.011), (R + 0.008, z + 0.011), (R - 0.002, z + 0.011)],
                             dark, segs=64, closed=True, name="clamp", bevel=0.001))
    for k in range(8):
        a = math.tau * k / 8
        for z in (-0.075, 0.075):
            objs.append(K.cyl(0.004, 0.004, ((R + 0.008) * math.cos(a), (R + 0.008) * math.sin(a), z), M.metal("dark_steel"),
                              rot=(0, math.pi / 2, a), verts=6, base=False, bevel=0.0008))
    g = KI.group(objs, (0, 0, R + 0.03), (0, math.pi / 2, 0))
    for x in (-0.12, 0.12):
        K.box((0.03, 0.16, 0.03), (x, 0, 0), dark, bevel=0.004, base=True)
        K.box((0.02, 0.12, 0.012), (x, 0, 0.03), M.rubber(), bevel=0.003, base=True)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, -0.35))
    KI.ground(KI.model_objects())
    return frame(pitch=54.0)


ARCHETYPES = {
    "fluid_orb": fluid_orb,
    "barrel": barrel,
    "gas_canister": gas_canister,
    "flask": flask,
    "canister": canister,
    "crate": crate,
    "capsule": capsule,
}
