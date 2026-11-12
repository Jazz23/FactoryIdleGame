"""Defense / aerospace icons: ammo box, shell, rocket part, drone."""
import math
import random

from mathutils import Euler, Vector

import kit as K
import kit_icons as KI
import materials as M
from icons import frame


def _cartridge(scale, case_mat, bullet_mat):
    """Small-arms cartridge along +Z (base at 0)."""
    s = scale
    prof = [(0, 0), (0.0062 * s, 0), (0.0062 * s, 0.0012 * s), (0.0052 * s, 0.0016 * s), (0.0052 * s, 0.0028 * s),
            (0.006 * s, 0.0032 * s), (0.0058 * s, 0.038 * s), (0.0045 * s, 0.042 * s), (0.0043 * s, 0.049 * s), (0, 0.049 * s)]
    case = KI.lathe(prof, case_mat, segs=32, name="case")
    b = [(0, 0.045 * s)] + [(0.0041 * s * math.cos(a) ** 0.6, 0.049 * s + 0.024 * s * math.sin(a))
                             for a in [math.pi / 2 * i / 10 for i in range(0, 11)]]
    b[-1] = (0, b[-1][1])
    bullet = KI.lathe(b, bullet_mat, segs=32, name="bullet")
    return [case, bullet]


def ammo_box(item, material, color, p):
    """Steel ammunition can with latch, carry handle, stencil, and loose cartridges in front."""
    col = color or (0.07, 0.09, 0.035)
    pm = KI.paint(col, wear=0.4, grime=0.45, rough=0.55, rust=0.15, name="od_paint")
    steel = KI.metal("steel", None, dirt=0.6)
    W, D, H = 0.3, 0.15, 0.19
    K.box((W, D, H), (0, 0, 0), pm, bevel=0.006, base=True, name="can")
    K.box((W + 0.008, D + 0.008, 0.04), (0, 0, H - 0.005), pm, bevel=0.006, base=True, name="lid")
    for x in (-W * 0.3, 0.0, W * 0.3):
        K.box((0.012, D + 0.01, 0.006), (x, 0, 0.0), pm, bevel=0.002, base=True)
    # latch on +X end
    K.box((0.012, 0.07, 0.11), (W / 2 + 0.008, 0, H - 0.08), steel, bevel=0.003, base=True, name="latch")
    K.cyl(0.008, 0.08, (W / 2 + 0.012, -0.04, H - 0.07), steel, rot=K.AXES["y"], verts=12)
    # handle folded on the lid
    hp = [(-0.06, 0.03, H + 0.037), (-0.06, -0.03, H + 0.04), (0.06, -0.03, H + 0.04), (0.06, 0.03, H + 0.037)]
    KI.sweep(hp, KI.rect_section(0.014, 0.008, 0.002), M.plastic((0.02, 0.02, 0.02), 0.6), name="handle")
    ink = M.plastic((0.75, 0.62, 0.08), 0.6, name="stencil_yellow")
    KI.project_text(p.get("label", "CTG 7.62MM"), 0.022, (0, -D / 2 - 0.0005, H * 0.62), (0, -1, 0), mat=ink, depth=0.0003)
    KI.project_text("800 ROUNDS  LOT 0417", 0.012, (0, -D / 2 - 0.0005, H * 0.42), (0, -1, 0), mat=ink, depth=0.0003)
    brass = KI.metal("brass", None, rough=0.25, dirt=0.3)
    cu = KI.metal("copper", None, rough=0.3, dirt=0.25) if material in (None, "paint", "brass", "copper") else \
        (KI.metal(material, None, rough=0.25, dirt=0.2) if KI.is_metal(material) else KI.surf(material, None))
    rnd = KI.rnd_for(item["id"])
    for k, (x, y, a) in enumerate(((-0.06, -0.15, 0.3), (0.0, -0.14, -0.25), (0.05, -0.17, 0.5))):
        objs = _cartridge(2.2, brass, cu)
        g = KI.group(objs, (0, 0, 0), (0, math.pi / 2, 0))
        g.rotation_euler = Euler((0, math.pi / 2, a), "XYZ")
        g.location = (x, y, 0.0062 * 2.2)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.22))
    return frame(pitch=54.0)


def _shell(mat_case, mat_proj, band, fuze, ring, scale=1.0):
    s = scale
    case = [(0, 0), (0.05 * s, 0), (0.05 * s, 0.006 * s), (0.044 * s, 0.009 * s), (0.044 * s, 0.014 * s), (0.047 * s, 0.017 * s),
            (0.046 * s, 0.19 * s), (0.044 * s, 0.205 * s), (0.044 * s, 0.215 * s), (0, 0.215 * s)]
    objs = [KI.lathe(case, mat_case, segs=64, name="case")]
    z0 = 0.212 * s
    zb = z0 + 0.035 * s
    proj = [(0, z0), (0.0438 * s, z0), (0.0438 * s, zb + 0.06 * s)]
    L = 0.13 * s
    for i in range(1, 13):
        u = i / 12
        proj.append((0.0438 * s * math.sqrt(max(0.0, 1 - u * u)) * (1 - 0.35 * u) + 0.012 * s * u, zb + 0.06 * s + L * u))
    proj.append((0, zb + 0.06 * s + L))
    objs.append(KI.lathe(proj, mat_proj, segs=64, name="projectile"))
    objs.append(KI.lathe([(0.0436 * s, z0 + 0.012 * s), (0.0452 * s, z0 + 0.014 * s), (0.0452 * s, z0 + 0.026 * s),
                          (0.0436 * s, z0 + 0.028 * s)], band, segs=64, closed=True, name="band"))
    objs.append(KI.lathe([(0.0441 * s, zb + 0.02 * s), (0.0441 * s, zb + 0.035 * s)], ring, segs=64, name="ring"))
    zt = zb + 0.06 * s + L
    objs.append(KI.lathe([(0, zt - 0.006 * s), (0.0125 * s, zt - 0.006 * s), (0.011 * s, zt + 0.02 * s), (0.004 * s, zt + 0.032 * s),
                          (0, zt + 0.033 * s)], fuze, segs=48, name="fuze"))
    return objs


def shell(item, material, color, p):
    """Three artillery rounds: brass cases, painted projectiles with copper driving bands and fuzes."""
    m = material or "brass"
    case = KI.metal(m, None, rough=0.25, dirt=0.35) if KI.is_metal(m) else KI.surf(m, color)
    proj = KI.paint(color or (0.12, 0.13, 0.06), wear=0.25, grime=0.3, rough=0.45, rust=0.05, name="shell_paint")
    band = KI.metal("copper", None, rough=0.3, dirt=0.3)
    fuze = KI.metal("aluminum", None, rough=0.3, dirt=0.3)
    ring = KI.paint((0.75, 0.55, 0.02), wear=0.1, grime=0.2, rust=0.0, name="he_band")
    for x, y, s in ((-0.06, 0.06, 1.0), (0.065, 0.075, 1.0), (0.0, -0.05, 1.0)):
        objs = _shell(case, proj, band, fuze, ring, s)
        KI.group(objs, (x, y, 0), (0, 0, 0))
    return frame(pitch=58.0)


def rocket_part(item, material, color, p):
    """Rocket upper stage on transport cradles: nose fairing, roll-pattern body, fins, engine bell.
    Engines / nacelles / thrusters (by name or params.variant) render as a bell nozzle instead."""
    nm = (item.get("name") or "").lower() + " " + str(p.get("variant", ""))
    if any(k in nm for k in ("engine", "nacelle", "thruster")):
        from icons import parts
        return parts.nozzle(item, material, None, {"glow": color} if color else {})
    white = KI.paint(color or (0.78, 0.78, 0.76), wear=0.12, grime=0.2, rough=0.35, rust=0.0, name="rocket_paint")
    black = KI.paint((0.015, 0.015, 0.017), wear=0.1, grime=0.2, rough=0.4, rust=0.0, name="roll_black")
    R, L = 0.075, 0.34
    objs = [KI.lathe([(0, 0), (R, 0), (R, L), (0, L)], white, segs=64, name="body")]
    objs.append(KI.wrap_patch(R + 0.0005, math.radians(0), math.pi / 2, L * 0.55, L * 0.85, black, thick=0.0006, segs=16))
    objs.append(KI.wrap_patch(R + 0.0005, math.radians(180), math.pi / 2, L * 0.55, L * 0.85, black, thick=0.0006, segs=16))
    nose = [(R, L)] + [(R * (1 - (u ** 1.6)) ** 0.75, L + 0.17 * u) for u in [i / 16 for i in range(1, 16)]] + [(0, L + 0.17)]
    objs.append(KI.lathe([(0, L)] + nose, white, segs=64, name="nose"))
    objs.append(KI.lathe([(R + 0.0008, L * 0.3), (R + 0.0008, L * 0.33)], black, segs=64, name="stripe"))
    objs.append(KI.lathe([(R + 0.002, L - 0.004), (R + 0.002, L + 0.004)], KI.metal("aluminum", None, dirt=0.3), segs=64))
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        f = K.prism([(0, 0), (0.09, 0), (0.09, 0.03), (0, 0.11)], 0.006, (0, 0, 0), white, bevel=0.0015, name="fin")
        f.rotation_euler = (0, 0, a)
        f.location = (R * math.cos(a) - 0.0, R * math.sin(a), 0.0)
        f.rotation_euler = Euler((0, 0, a), "XYZ")
        objs.append(f)
    eng = KI.lathe([(0.03, 0), (0.06, -0.07), (0.064, -0.072), (0.034, 0.0)], KI.cast_metal("copper", None, oxid=0.6),
                   segs=48, closed=True, name="bell")
    objs.append(eng)
    objs.append(KI.lathe([(0, -0.001), (0.045, -0.001), (0.045, 0.0), (0, 0.0)], KI.metal("dark_steel", None), segs=48))
    objs.append(KI.wrap_text(p.get("label", "IND-2"), R + 0.0006, math.radians(-90), L * 0.38, 0.03,
                             M.plastic((0.03, 0.03, 0.03), 0.5, name="ink")))
    g = KI.group([o for o in objs if o], (0, 0, R + 0.06), (0, math.pi / 2, 0))
    dark = M.painted((0.25, 0.22, 0.03), wear=0.4, grime=0.5, rough=0.5, name="cradle")
    for x in (-0.02, 0.24):
        K.box((0.03, 0.2, 0.06), (x - 0.12, 0, 0), dark, bevel=0.004, base=True)
        K.box((0.032, 0.17, 0.018), (x - 0.12, 0, 0.06), M.rubber(), bevel=0.003, base=True)
    g.location.x -= 0.12
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, math.radians(-25)))
    KI.ground(KI.model_objects())
    return frame(pitch=55.0)


def drone(item, material, color, p):
    """Quad-rotor drone: shell body, four arms with motors and props, landing skids, gimbal camera, nav LEDs."""
    body = KI.surf(material or "plastic_white", color) if material != "plastic_color" else M.plastic(KI.lin(color or (0.8, 0.3, 0.02)), 0.35)
    if material in (None, "plastic_white"):
        body = M.plastic((0.8, 0.8, 0.78), 0.32, name="drone_shell")
    arm_m = KI.carbon_fiber()
    dark = M.plastic((0.02, 0.02, 0.022), 0.4, name="dark_plastic")
    motor_m = KI.metal("aluminum", None, rough=0.3, dirt=0.2)
    zc = 0.09
    objs = []
    objs.append(K.box((0.2, 0.14, 0.06), (0, 0, zc), body, bevel=0.022, base=True, name="body"))
    objs.append(K.sphere(0.075, (0, 0, zc + 0.06), body, scale=(1.3, 0.95, 0.42)))
    objs.append(K.box((0.12, 0.003, 0.02), (0.0, -0.0715, zc + 0.03), M.emissive((0.2, 0.7, 1.0), 2.0), bevel=0.001))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        tip = d * 0.18 + Vector((0, 0, zc + 0.035))
        objs.append(KI.sweep([tuple(d * 0.05 + Vector((0, 0, zc + 0.035))), tuple(tip)], KI.rect_section(0.024, 0.026, 0.006),
                             arm_m, name="arm"))
        objs.append(K.cyl(0.026, 0.034, tip + Vector((0, 0, -0.004)), motor_m, verts=32, bevel=0.002))
        objs.append(K.torus(0.085, 0.005, tip + Vector((0, 0, 0.04)), arm_m, segs=48, rsegs=8))
        objs.append(K.cyl(0.008, 0.012, tip + Vector((0, 0, 0.03)), dark, verts=16))
        for s in (0, math.pi):
            bl = K.box((0.08, 0.026, 0.003), (0, 0, 0), dark, bevel=0.0012, name="blade")
            bl.location = tip + Vector((math.cos(a * 1.7 + s) * 0.042, math.sin(a * 1.7 + s) * 0.042, 0.04))
            bl.rotation_euler = Euler((math.radians(12) * (1 if s == 0 else -1), 0, a * 1.7 + s), "XYZ")
            objs.append(bl)
        led = M.emissive((0.1, 1.0, 0.2) if k in (0, 3) else (1.0, 0.08, 0.04), 6.0)
        objs.append(K.sphere(0.006, tip - d * 0.02 + Vector((0, 0, -0.004)), led, segs=12, rings=6))
    for sy in (-1, 1):
        objs.append(KI.curve_tube([(-0.06, sy * 0.045, zc), (-0.07, sy * 0.07, 0.006), (0.07, sy * 0.07, 0.006),
                                   (0.06, sy * 0.045, zc)], 0.005, dark, name="skid"))
    objs.append(K.sphere(0.024, (0.07, 0, zc - 0.012), dark, segs=24, rings=12))
    objs.append(K.cyl(0.011, 0.012, (0.088, 0, zc - 0.012), KI.coated_glass(), rot=K.AXES["x"], verts=24))
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, math.radians(-30)))
    KI.ground(KI.model_objects())
    return frame(pitch=54.0)


ARCHETYPES = {
    "ammo_box": ammo_box,
    "shell": shell,
    "rocket_part": rocket_part,
    "drone": drone,
}
