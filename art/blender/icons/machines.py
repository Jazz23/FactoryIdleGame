"""Fuel rod archetype + variant builders the base archetypes dispatch to (params.variant or material):
gearbox, gate valve, pump unit, hydraulic cylinder, flight case, schematics, silicon wafer,
electromagnet, rare-earth magnets, plasma coil."""
import math

from mathutils import Euler, Vector

import kit as K
import kit_icons as KI
import materials as M
from icons import frame


def _rp(pts, rad, n=6):
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


# --------------------------------------------------------------------------- fuel rod
def fuel_rod(item, material, color, p):
    """Nuclear fuel assembly: 5x5 clad rods, spacer grids, top/bottom nozzles, lifting bail, hazard tag."""
    spent = "spent" in item.get("id", "") or material == "lead"
    clad = KI.heat_tint("titanium", (0.85, 0.82, 0.78)) if spent else KI.metal("stainless", None, rough=0.25, dirt=0.15)
    grid = KI.metal("stainless", None, rough=0.3, dirt=0.6 if spent else 0.2)
    nozzle = KI.metal("steel", None, rough=0.35, dirt=0.8 if spent else 0.3)
    n, pitch, rr, L = 5, 0.026, 0.0105, 0.44
    half = (n - 1) * pitch / 2
    objs = []
    for i in range(n):
        for j in range(n):
            y, z = -half + i * pitch, -half + j * pitch
            objs.append(K.cyl(rr, L, (-L / 2, y, z), clad, rot=K.AXES["x"], verts=20, bevel=0.002, name="rod"))
    S = n * pitch + 0.006
    for x in (-L * 0.32, 0.0, L * 0.32):
        for (sy, sz, w, h) in ((0, S / 2, 0.002, S), (0, -S / 2, 0.002, S)):
            objs.append(K.box((0.028, h, 0.003), (x, 0, sz), grid, bevel=0.0006))
        for sy in (-S / 2, S / 2):
            objs.append(K.box((0.028, 0.003, S), (x, sy, 0), grid, bevel=0.0006))
    for x, sgn in ((-L / 2 - 0.02, -1), (L / 2 + 0.02, 1)):
        objs.append(K.box((0.04, S + 0.012, S + 0.012), (x, 0, 0), nozzle, bevel=0.004, name="nozzle"))
    # lifting bail on the top nozzle
    objs.append(KI.sweep(_rp([(L / 2 + 0.04, -S * 0.3, -S * 0.2), (L / 2 + 0.07, -S * 0.3, -S * 0.2), (L / 2 + 0.07, S * 0.3, S * 0.2),
                              (L / 2 + 0.04, S * 0.3, S * 0.2)], 0.012), KI.circle_section(0.005, 10), nozzle, name="bail"))
    tag = KI.paint((0.85, 0.65, 0.02), wear=0.15, grime=0.3 if spent else 0.1, rust=0.0, rough=0.4, name="tag")
    objs.append(K.box((0.07, 0.002, 0.045), (L * 0.16, -S / 2 - 0.004, 0), tag, bevel=0.0008))
    objs.append(KI.project_text("☢", 0.034, (L * 0.16 - 0.018, -S / 2 - 0.0055, 0), (0, -1, 0),
                                mat=M.plastic((0.02, 0.02, 0.02), 0.5), depth=0.0004))
    objs.append(KI.project_text("Th-232" if material == "thorium" else "SPENT", 0.011, (L * 0.16 + 0.012, -S / 2 - 0.0055, 0),
                                (0, -1, 0), mat=M.plastic((0.02, 0.02, 0.02), 0.5), depth=0.0004))
    if not spent:
        glow = M.emissive((0.25, 0.75, 1.0), 2.0)
        objs.append(K.box((L * 0.9, S * 0.8, S * 0.8), (0, 0, 0), glow, bevel=0))
    g = KI.group(objs, (0, 0, 0), (0, 0, math.radians(-18)))
    KI.ground(objs)
    return frame(pitch=54.0)


# --------------------------------------------------------------------------- gearbox
def gearbox(item, material, color, p):
    """Helical reduction gearbox: ribbed cast housing, bearing bosses, input/output shafts, feet."""
    pm = KI.paint(color or (0.05, 0.11, 0.13), wear=0.3, grime=0.45, rough=0.45, rust=0.08, name="gearbox_paint")
    sh = KI.metal("steel", None, rough=0.18, dirt=0.15)
    W, D, H = 0.34, 0.2, 0.22
    K.box((W, D, H), (0, 0, 0.03), pm, bevel=0.018, base=True, name="housing")
    K.box((W + 0.03, D + 0.01, 0.03), (0, 0, 0), pm, bevel=0.006, base=True, name="feet")
    K.box((W + 0.012, D + 0.012, 0.02), (0, 0, 0.03 + H * 0.55), pm, bevel=0.005, base=True, name="split_flange")
    for x in (-W / 2 + 0.03, -0.06, 0.06, W / 2 - 0.03):
        for y in (-1, 1):
            K.cyl(0.006, 0.006, (x, y * (D / 2 + 0.006), 0.03 + H * 0.55 + 0.02), M.metal("dark_steel"), verts=6, bevel=0.001)
    for x in (-0.1, 0.0, 0.1):
        K.box((0.012, 0.01, H * 0.5), (x, -D / 2 - 0.004, 0.03 + 0.005), pm, bevel=0.003, base=True)
    for x, r, L in ((-0.09, 0.055, 0.03), (0.08, 0.075, 0.035)):
        K.cyl(r, L, (x, -D / 2 + 0.005, 0.03 + H * 0.55), pm, rot=K.AXES["-y"], verts=40, bevel=0.004)
        K.bolts((x, -D / 2 - L + 0.004, 0.03 + H * 0.55), r * 0.78, 6, axis="-y", r=0.006, h=0.006)
    K.cyl(0.018, 0.09, (-0.09, -D / 2 - 0.02, 0.03 + H * 0.55), sh, rot=K.AXES["-y"], verts=24, bevel=0.002)
    K.cyl(0.028, 0.07, (W / 2 - 0.01, 0.02, 0.03 + H * 0.4), sh, rot=K.AXES["x"], verts=32, bevel=0.002)
    K.box((0.05, 0.01, 0.008), (W / 2 + 0.035, 0.02, 0.03 + H * 0.4 + 0.029), sh, bevel=0.001)
    K.box((0.12, 0.09, 0.012), (0.0, 0.0, 0.03 + H), pm, bevel=0.004, base=True)
    K.cyl(0.014, 0.025, (0.08, 0.04, 0.03 + H), M.metal("brass"), verts=6, bevel=0.002)
    K.box((0.06, 0.002, 0.03), (0.0, -D / 2 - 0.0, 0.03 + H * 0.25), M.metal("aluminum", dirt=0.3), bevel=0.0005)
    KI.project_text("i = 25:1", 0.01, (0.0, -D / 2 - 0.0015, 0.03 + H * 0.25), (0, -1, 0), mat=M.metal("dark_steel"), depth=0.0004)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, math.radians(-12)))
    return frame(pitch=55.0)


# --------------------------------------------------------------------------- gate valve
def gate_valve(item, material, color, p):
    """Flanged gate valve with bonnet, rising stem, yoke and red handwheel."""
    body = KI.cast_metal(material if KI.is_metal(material or "") else "cast_iron", None, oxid=0.4)
    red = KI.paint(color or (0.55, 0.03, 0.02), wear=0.25, grime=0.3, rough=0.4, rust=0.05, name="wheel_red")
    sh = KI.metal("steel", None, rough=0.2, dirt=0.2)
    objs = [K.sphere(0.075, (0, 0, 0.11), body, segs=32, rings=16, scale=(1.0, 0.9, 1.05))]
    for sx in (-1, 1):
        objs.append(K.cyl(0.05, 0.08, (sx * 0.04, 0, 0.11), body, rot=K.AXES["x"] if sx > 0 else K.AXES["-x"], verts=32, bevel=0.003))
        f = KI.lathe([(0.03, 0), (0.105, 0), (0.105, 0.02), (0.03, 0.02)], body, segs=48, closed=True, name="flange", bevel=0.001)
        KI.drill(f, [(0.08 * math.cos(a), 0.08 * math.sin(a), 0.01) for a in [k * math.tau / 8 + math.pi / 8 for k in range(8)]],
                 0.008, 0.06)
        f.rotation_euler = (0, sx * math.pi / 2, 0)
        f.location = (sx * 0.12, 0, 0.11)
        objs.append(f)
    objs.append(KI.lathe([(0.0, 0.16), (0.055, 0.16), (0.06, 0.18), (0.045, 0.27), (0.03, 0.28), (0, 0.28)], body, segs=40,
                         name="bonnet"))
    objs += K.bolts((0, 0, 0.18), 0.05, 8, r=0.006, h=0.008)
    for sx in (-1, 1):
        objs.append(K.box((0.012, 0.02, 0.1), (sx * 0.028, 0, 0.28), body, bevel=0.003, base=True))
    objs.append(K.box((0.07, 0.03, 0.016), (0, 0, 0.375), body, bevel=0.004, base=True))
    objs.append(K.cyl(0.008, 0.15, (0, 0, 0.27), sh, verts=16))
    wz = 0.4
    objs.append(K.torus(0.085, 0.009, (0, 0, wz), red, segs=48, rsegs=10))
    objs.append(K.cyl(0.02, 0.025, (0, 0, wz - 0.012), red, verts=24))
    for k in range(5):
        a = math.tau * k / 5
        objs.append(K.cyl(0.0055, 0.08, (0, 0, wz), red, rot=(0, math.pi / 2, a), verts=10, bevel=0))
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, math.radians(-15)))
    KI.ground(KI.model_objects())
    return frame(pitch=56.0)


# --------------------------------------------------------------------------- pump unit
def pump_unit(item, material, color, p):
    """Close-coupled centrifugal pump: motor + volute casing on a common baseplate."""
    from icons import parts
    parts.motor(item, "paint", color or (0.03, 0.14, 0.38), {})
    objs = KI.model_objects()
    KI.group(objs, (-0.08, 0, 0.012), (0, 0, 0))
    body = KI.cast_metal("cast_iron", None, oxid=0.5)
    pm = KI.paint((0.45, 0.04, 0.02), wear=0.3, grime=0.4, rust=0.1, name="pump_red")
    zc = 0.152
    vol = KI.lathe([(0.0, 0.0), (0.11, 0.0), (0.125, 0.02), (0.125, 0.06), (0.11, 0.08), (0.04, 0.085), (0.04, 0.1), (0, 0.1)],
                   pm, segs=48, name="volute")
    vol.rotation_euler = (0, math.pi / 2, 0)
    vol.location = (0.15, -0.01, zc)
    K.cyl(0.04, 0.12, (0.21, -0.03, zc + 0.08), pm, verts=32, bevel=0.003)
    K.cyl(0.065, 0.016, (0.21, -0.03, zc + 0.2), pm, verts=32, bevel=0.003)
    K.bolts((0.21, -0.03, zc + 0.216), 0.05, 6, r=0.005, h=0.006)
    K.cyl(0.035, 0.06, (0.25, 0.0, zc), pm, rot=K.AXES["x"], verts=32, bevel=0.003)
    K.cyl(0.06, 0.016, (0.31, 0.0, zc), pm, rot=K.AXES["x"], verts=32, bevel=0.003)
    K.box((0.62, 0.32, 0.012), (0.03, 0, 0), KI.paint((0.05, 0.05, 0.055), wear=0.4, grime=0.5, rust=0.2, name="baseplate"),
          bevel=0.003, base=True)
    K.box((0.07, 0.14, zc - 0.11), (0.21, -0.01, 0.012), body, bevel=0.004, base=True)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, math.radians(-8)))
    return frame(pitch=55.0)


# --------------------------------------------------------------------------- hydraulic cylinder
def hydraulic_cylinder(item, material, color, p):
    """Tie-rod hydraulic cylinder with chrome piston rod, clevis ends and pressure ports."""
    barrel = KI.paint(color or (0.04, 0.05, 0.06), wear=0.25, grime=0.4, rust=0.05, name="ram_paint") \
        if material not in ("stainless", "titanium", "aluminum") else KI.metal(material, None, rough=0.25, dirt=0.35)
    chrome = KI.metal("chrome", None, rough=0.06, dirt=0.05)
    steel = KI.metal("steel", None, rough=0.3, dirt=0.4)
    R, L = 0.055, 0.3
    objs = [K.cyl(R, L, (-L / 2, 0, 0), barrel, rot=K.AXES["x"], verts=48, bevel=0.003, name="barrel")]
    for x in (-L / 2 - 0.03, L / 2):
        objs.append(K.box((0.03, 2 * R + 0.03, 2 * R + 0.03), (x + 0.015, 0, 0), steel, bevel=0.005))
    for sy in (-1, 1):
        for sz in (-1, 1):
            objs.append(K.cyl(0.006, L + 0.07, (-L / 2 - 0.035, sy * (R + 0.006), sz * (R + 0.006)), steel, rot=K.AXES["x"],
                              verts=12, bevel=0.001))
    objs.append(K.cyl(0.028, 0.2, (L / 2 + 0.03, 0, 0), chrome, rot=K.AXES["x"], verts=32, bevel=0.002, name="rod"))
    for x, sgn in ((L / 2 + 0.23, 1), (-L / 2 - 0.03, -1)):
        c = K.box((0.05, 0.035, 0.06), (x + sgn * 0.025, 0, 0), steel, bevel=0.008)
        KI.drill(c, [(x + sgn * 0.03, 0, 0)], 0.012, 0.1, axis="y")
        objs.append(c)
        objs.append(K.cyl(0.011, 0.06, (x + sgn * 0.03, -0.03, 0), chrome, rot=K.AXES["y"], verts=16))
    brass = KI.metal("brass", None, dirt=0.3)
    for x in (-L / 2 + 0.02, L / 2 - 0.03):
        objs.append(K.cyl(0.012, 0.03, (x, 0, R - 0.005), brass, verts=6, bevel=0.002))
        objs.append(K.cyl(0.009, 0.02, (x, 0, R + 0.025), brass, verts=16))
    KI.group(objs, (0, 0, 0), (0, 0, math.radians(10)))
    KI.ground(objs)
    return frame(pitch=54.0)


# --------------------------------------------------------------------------- flight case
def flight_case(item, material, color, p):
    """Ruggedised aluminium electronics case: ribbed shell, corner guards, latches, connector panel, LEDs."""
    alu = KI.metal(material if KI.is_metal(material or "") else "aluminum", None, rough=0.3, dirt=0.35)
    dark = M.painted((0.03, 0.032, 0.035), wear=0.2, grime=0.3, rough=0.4, name="graphite")
    W, D, H = 0.4, 0.28, 0.2
    K.box((W, D, H), (0, 0, 0), alu, bevel=0.01, base=True, name="case")
    for z in (0.06, H - 0.06):
        K.box((W + 0.008, D + 0.008, 0.012), (0, 0, z), alu, bevel=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (0.0, H - 0.04):
                K.box((0.045, 0.045, 0.04), (sx * (W / 2 - 0.016), sy * (D / 2 - 0.016), z), dark, bevel=0.008, base=True)
    for x in (-0.11, 0.11):
        K.box((0.04, 0.012, 0.03), (x, -D / 2 - 0.006, H * 0.5), M.metal("stainless", dirt=0.3), bevel=0.003)
    K.box((W * 0.6, 0.005, 0.07), (0, -D / 2 - 0.002, H * 0.27), dark, bevel=0.002)
    for i, c in enumerate(((0.1, 1.0, 0.2), (1.0, 0.6, 0.05), (0.1, 1.0, 0.2))):
        K.cyl(0.006, 0.004, (-0.09 + i * 0.02, -D / 2 - 0.005, H * 0.27 + 0.02), M.emissive(c, 4.0), rot=K.AXES["-y"], verts=12)
    for i in range(3):
        K.cyl(0.014, 0.012, (0.0 + i * 0.04, -D / 2 - 0.005, H * 0.25), KI.metal("stainless", None, dirt=0.2), rot=K.AXES["-y"], verts=20)
        K.cyl(0.008, 0.013, (0.0 + i * 0.04, -D / 2 - 0.005, H * 0.25), M.plastic((0.01, 0.01, 0.01), 0.6), rot=K.AXES["-y"], verts=16)
    hp = [(-0.07, 0.0, H), (-0.07, 0.0, H + 0.035), (0.07, 0.0, H + 0.035), (0.07, 0.0, H)]
    KI.sweep(_rp(hp, 0.02), KI.circle_section(0.008, 10), dark, name="handle")
    KI.project_text(p.get("label", "AVIONICS"), 0.022, (0, -D / 2 - 0.0002, H * 0.7), (0, -1, 0), mat=dark, depth=0.0004)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.25))
    return frame(pitch=55.0)


# --------------------------------------------------------------------------- schematics
def blueprint_mat():
    key = ("blueprint",)
    if key in KI._cache:
        return KI._cache[key]
    m, t = M._new("blueprint")
    p = t.bsdf()
    tc = t.node("ShaderNodeTexCoord")
    lines = []
    for d, sc, w in (("X", 60.0, 0.94), ("Y", 60.0, 0.94), ("X", 12.0, 0.97), ("Y", 12.0, 0.97)):
        wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=d)
        t.link(tc.outputs["Object"], wv.inputs["Vector"])
        wv.inputs["Scale"].default_value = sc
        lines.append(t.maprange(wv.outputs["Factor"], w, 1.0))
    g = t.math("MAXIMUM", t.math("MULTIPLY", t.math("MAXIMUM", lines[0], lines[1]), 0.35), t.math("MAXIMUM", lines[2], lines[3]))
    col = t.mix_color(g, (0.02, 0.07, 0.3), (0.75, 0.82, 0.95))
    KI._set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = 0.7
    KI._cache[key] = m
    return m


def schematics(item, material, color, p):
    """Blueprint sheets (one rolled) under a populated circuit board."""
    from icons import electronics
    electronics.circuit_board(item, material, color, {})
    board = KI.model_objects()
    g = KI.group(board, (0.03, -0.02, 0.003), (0, 0, 0.0))
    g.scale = (0.72, 0.72, 0.72)
    bp = blueprint_mat()
    sheet = K.box((0.46, 0.34, 0.002), (0, 0, 0), bp, bevel=0, base=True, name="sheet")
    sheet.rotation_euler = (0, 0, -0.12)
    roll = K.cyl(0.03, 0.4, (-0.2, 0.2, 0.03), bp, rot=K.AXES["x"], verts=32, bevel=0.002)
    roll.rotation_euler = (0, math.pi / 2, 0.3)
    roll.location = (-0.2, 0.17, 0.03)
    white = M.plastic((0.85, 0.88, 0.95), 0.6, name="bp_ink")
    KI.text_mesh("SCHEMATIC  A-17", 0.018, 0.0002, white, loc=(-0.1, -0.13, 0.0021), rot=(0, 0, -0.12))
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.12))
    return frame(pitch=45.0)


# --------------------------------------------------------------------------- silicon wafer
def wafer_mat():
    key = ("wafer",)
    if key in KI._cache:
        return KI._cache[key]
    m, t = M._new("wafer")
    p = t.bsdf()
    tc = t.node("ShaderNodeTexCoord")
    lines = []
    for d in ("X", "Y"):
        wv = t.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction=d)
        t.link(tc.outputs["Object"], wv.inputs["Vector"])
        wv.inputs["Scale"].default_value = 26.0
        lines.append(t.maprange(wv.outputs["Factor"], 0.9, 0.96))
    street = t.math("MAXIMUM", lines[0], lines[1])
    die = t.noise(t.coords(90.0), 1.0, 2, 0.5)
    p.inputs["Metallic"].default_value = 1.0
    KI._set(p, "Base Color", t.mix_color(street, (0.35, 0.36, 0.42), (0.6, 0.6, 0.62)))
    KI._set(p, "Roughness", t.mix_float(street, t.maprange(die, 0.3, 0.7, 0.08, 0.2), 0.3))
    KI._set(p, "Thin Film Thickness", t.mix_float(street, t.maprange(die, 0.2, 0.8, 250.0, 420.0), 60.0))
    p.inputs["Thin Film IOR"].default_value = 1.9
    KI._cache[key] = m
    return m


def wafer(item, material, color, p):
    """Patterned silicon wafer (with flat) on a black conductive-foam tray."""
    R = 0.16
    pts = []
    for i in range(96):
        a = math.tau * i / 96
        x, y = R * math.cos(a), R * math.sin(a)
        pts.append((x, max(y, -R * 0.94)))
    w = KI.poly_extrude(pts, 0.012, 0.016, wafer_mat(), name="wafer", bevel=0.0008)
    K.box((0.4, 0.4, 0.012), (0, 0, 0), M.plastic((0.02, 0.02, 0.022), 0.85, name="foam"), bevel=0.004, base=True)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.3))
    return frame(pitch=44.0)


# --------------------------------------------------------------------------- magnets
def electromagnet(item, material, color, p):
    """Laminated U-core with two copper-wound coils and terminal leads."""
    core = KI.metal("dark_steel", None, rough=0.4, dirt=0.4)
    cu = KI.metal("copper", None, rough=0.25, dirt=0.2)
    s = 0.055
    path = [(-0.1, 0.0, 0.2), (-0.1, 0.0, 0.0), (0.1, 0.0, 0.0), (0.1, 0.0, 0.2)]
    objs = [KI.sweep(_rp(path, 0.05), KI.rect_section(s, s, 0.004), core, name="core")]
    for x in (-0.1, 0.1):
        objs.append(K.cyl(0.05, 0.12, (x, 0, 0.055), cu, verts=48, bevel=0.003))
        pts = KI.helix_points(0.051, 0.008, 14.5, z0=0.058, res=40)
        w = KI.curve_tube(pts, 0.0038, cu, name="winding")
        w.location = (x, 0, 0)
        objs.append(w)
        for z in (0.05, 0.18):
            objs.append(K.cyl(0.06, 0.008, (x, 0, z), M.plastic((0.03, 0.03, 0.03), 0.5), verts=48, bevel=0.002))
    for k, x in enumerate((-0.04, 0.04)):
        objs.append(KI.curve_tube(_rp([(x * 2.2, -0.04, 0.12), (x, -0.08, 0.09), (x * 1.5, -0.12, 0.012)], 0.03), 0.005,
                                  M.plastic((0.6, 0.03, 0.02) if k == 0 else (0.03, 0.03, 0.03), 0.4), name="lead"))
    for x in (-0.1, 0.1):
        objs.append(K.box((s + 0.006, s + 0.006, 0.02), (x, 0, 0.2), KI.metal("steel", None, rough=0.2, dirt=0.1), bevel=0.003,
                          base=True))
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, math.radians(-20)))
    KI.ground(KI.model_objects())
    return frame(pitch=55.0)


def rare_earth(item, material, color, p):
    """Nickel-plated neodymium disc stack and ring magnet."""
    ni = KI.metal("chrome", None, rough=0.12, dirt=0.1) if material != "glow" else KI.metal("silver", None, rough=0.15, dirt=0.1)
    red = M.plastic((0.6, 0.03, 0.02), 0.4, name="pole_dot")
    for k in range(3):
        K.cyl(0.085, 0.03, (0.01 * k, -0.008 * k, 0.03 * k + 0.0002 * k), ni, verts=64, bevel=0.003)
    KI.text_mesh("N", 0.03, 0.0006, red, loc=(0.02, -0.016, 0.0906))
    ring = KI.ring_extrude([(0.075 * math.cos(a), 0.075 * math.sin(a)) for a in [math.tau * i / 64 for i in range(64)]],
                           [(0.03 * math.cos(a), 0.03 * math.sin(a)) for a in [math.tau * i / 64 for i in range(64)]],
                           0, 0.026, ni, name="ring", bevel=0.002)
    ring.rotation_euler = (math.radians(70), 0, math.radians(-35))
    ring.location = (0.14, 0.12, 0.0)
    KI.ground([ring])
    return frame(pitch=52.0)


def plasma_coil(item, material, color, p):
    """Toroidal confinement coil: copper D-coils around a glowing plasma ring on a steel stand."""
    c = KI.lin(color) if color else (0.6, 0.3, 1.0)
    cu = KI.metal("copper", None, rough=0.25, dirt=0.2)
    steel = KI.metal("stainless", None, rough=0.25, dirt=0.3)
    R0, r0 = 0.15, 0.04
    plasma = M.emissive(KI.glow_color(c), 1.3)
    objs = [K.torus(R0, r0, (0, 0, 0), plasma, segs=64, rsegs=24)]
    n = 12
    for k in range(n):
        a = math.tau * k / n
        ring = KI.sweep([((r0 + 0.02) * math.cos(t), 0, (r0 + 0.026) * math.sin(t)) for t in [math.tau * i / 24 for i in range(24)]],
                        KI.rect_section(0.014, 0.022, 0.003), cu, closed=True, name="dcoil")
        ring.rotation_euler = Euler((0, 0, a), "XYZ")
        ring.location = (R0 * math.cos(a), R0 * math.sin(a), 0)
        objs.append(ring)
    objs.append(K.torus(R0 - r0 - 0.03, 0.012, (0, 0, -0.02), steel, segs=48, rsegs=10))
    for k in range(4):
        a = math.tau * k / 4 + 0.4
        objs.append(K.box((0.03, 0.03, 0.09), ((R0 + 0.04) * math.cos(a), (R0 + 0.04) * math.sin(a), -0.1), steel, bevel=0.004,
                          base=True))
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0))
    KI.ground(KI.model_objects())
    return frame(pitch=50.0)


ARCHETYPES = {
    "fuel_rod": fuel_rod,
}
