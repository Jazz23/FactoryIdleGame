"""Electronics icons: circuit board, chip, processor, module card, battery, power cell, solar cell, lens,
filter."""
import math
import random

import bmesh
from mathutils import Euler, Vector

import kit as K
import kit_icons as KI
import materials as M
from icons import frame

MASK = {"pcb_green": (0.025, 0.2, 0.06), "pcb_blue": (0.015, 0.05, 0.28), "pcb_red": (0.32, 0.02, 0.015),
        "pcb_black": (0.012, 0.012, 0.014)}


def solder_mask(color, name="solder_mask"):
    key = ("mask", tuple(color))
    if key in KI._cache:
        return KI._cache[key]
    m, t = M._new(name)
    p = t.bsdf()
    vec = t.coords(4.0)
    col = t.mix_color(t.maprange(t.noise(vec, 6, 4), 0.3, 0.7, 0.0, 0.25), color, tuple(c * 0.7 for c in color))
    KI._set(p, "Base Color", col)
    p.inputs["Roughness"].default_value = 0.3
    p.inputs["Coat Weight"].default_value = 0.7
    p.inputs["Coat Roughness"].default_value = 0.08
    p.inputs["Subsurface Weight"].default_value = 0.0
    KI._cache[key] = m
    return m


def _mask_color(material, color):
    if color:
        return KI.lin(color)
    return MASK.get(material, MASK["pcb_green"])


def _qfp(size, h, pins, body_mat, pin_mat, loc=(0, 0, 0), rz=0.0, text=None, ink=None):
    """Quad flat package centred at loc (resting on z=loc.z)."""
    objs = [K.box((size, size, h), (0, 0, 0), body_mat, bevel=h * 0.12, base=True, name="qfp")]
    pitch = size * 0.8 / pins
    pw = pitch * 0.45
    for side in range(4):
        a = side * math.pi / 2
        for i in range(pins):
            u = -size * 0.4 + pitch * (i + 0.5)
            out = size / 2
            path = [(out - 0.002, u, h * 0.5), (out + h * 0.25, u, h * 0.5), (out + h * 0.45, u, h * 0.06),
                    (out + h * 0.8, u, h * 0.03)]
            path = [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z) for x, y, z in path]
            objs.append(KI.sweep(path, [(-h * 0.03, -pw / 2), (h * 0.03, -pw / 2), (h * 0.03, pw / 2), (-h * 0.03, pw / 2)],
                                 pin_mat, name="pin"))
    objs.append(K.cyl(size * 0.035, 0.0006, (-size * 0.36, -size * 0.36, h - 0.0004), M.plastic((0.06, 0.06, 0.06), 0.8),
                      verts=16, bevel=0))
    if text:
        objs.append(KI.text_mesh(text, size * 0.11, 0.0002, ink or M.plastic((0.25, 0.25, 0.25), 0.7, name="laser"),
                                 loc=(0, 0, h)))
    KI.group(objs, loc, (0, 0, rz))
    return objs


def _soic(L, W, h, pins, body_mat, pin_mat, loc, rz=0.0):
    objs = [K.box((L, W, h), (0, 0, 0), body_mat, bevel=h * 0.12, base=True, name="soic")]
    pitch = L * 0.85 / pins
    for s in (-1, 1):
        for i in range(pins):
            x = -L * 0.425 + pitch * (i + 0.5)
            path = [(x, s * (W / 2 - 0.001), h * 0.5), (x, s * (W / 2 + h * 0.3), h * 0.5), (x, s * (W / 2 + h * 0.5), h * 0.05),
                    (x, s * (W / 2 + h * 0.85), h * 0.03)]
            objs.append(KI.sweep(path, KI.rect_section(pitch * 0.45, h * 0.06), pin_mat, name="pin"))
    KI.group(objs, loc, (0, 0, rz))
    return objs


def circuit_board(item, material, color, p):
    """Populated PCB: QFP + SOIC chips, electrolytic caps, SMD passives, header, gold edge fingers, traces.
    variant 'annotated' -> blueprint schematics under a board."""
    if p.get("variant") == "annotated":
        from icons import machines
        return machines.schematics(item, material, color, p)
    rnd = KI.rnd_for(item["id"])
    mc = _mask_color(material, color)
    mask = solder_mask(mc)
    trace = solder_mask(tuple(min(1.0, c * 1.9 + 0.01) for c in mc), name="trace")
    gold = KI.metal("gold", None, rough=0.22, dirt=0.05)
    tin = KI.metal("tin", None, rough=0.25, dirt=0.1)
    black = M.plastic((0.018, 0.018, 0.02), 0.45, name="epoxy")
    silk = M.plastic((0.85, 0.85, 0.82), 0.6, name="silk")
    W, D, T = 0.36, 0.26, 0.008
    board = K.box((W, D, T), (0, 0, 0), mask, bevel=0.0012, base=True, name="pcb")
    holes = [(sx * (W / 2 - 0.016), sy * (D / 2 - 0.016), T / 2) for sx in (-1, 1) for sy in (-1, 1)]
    KI.drill(board, holes, 0.0055, 0.05)
    for x, y, _ in holes:
        KI.ring_extrude(_circle(0.01, 32), _circle(0.0056, 32), T, T + 0.0004, gold, name="pad", loc=(x, y, 0))
    # gold edge fingers along the -Y edge
    for i in range(14):
        x = -W * 0.3 + i * W * 0.6 / 13
        K.box((0.011, 0.028, 0.0005), (x, -D / 2 + 0.016, T), gold, bevel=0.0002, base=True)
    z = T + 0.0004
    # traces: Manhattan routes with 45-degree jogs
    lim_x, lim_y = W / 2 - 0.012, D / 2 - 0.012
    for i in range(70):
        x0, y0 = rnd.uniform(-W * 0.42, W * 0.3), rnd.uniform(-D * 0.3, D * 0.42)
        L1 = rnd.uniform(0.02, 0.1)
        horizontal = rnd.random() < 0.5
        w = rnd.choice((0.0018, 0.0018, 0.0026))
        d = rnd.choice((-1, 1)) * rnd.uniform(0.01, 0.03)
        L2 = rnd.uniform(0.01, 0.05)
        if horizontal and (x0 + L1 + abs(d) + L2 > lim_x or not -lim_y < y0 + d < lim_y):
            continue
        if not horizontal and y0 + L1 > lim_y:
            continue
        if horizontal:
            K.box((L1, w, 0.0004), (x0 + L1 / 2, y0, T), trace, bevel=0, base=True)
            jx = x0 + L1
            s = K.box((abs(d) * 1.414, w, 0.0004), (jx + abs(d) / 2, y0 + d / 2, T), trace, bevel=0, base=True)
            s.rotation_euler = (0, 0, math.copysign(math.pi / 4, d))
            K.box((L2, w, 0.0004), (jx + abs(d) + L2 / 2, y0 + d, T), trace, bevel=0, base=True)
        else:
            K.box((w, L1, 0.0004), (x0, y0 + L1 / 2, T), trace, bevel=0, base=True)
        K.cyl(w * 1.6, 0.0005, (x0, y0, T), tin, verts=12, bevel=0)
    # components
    _qfp(0.075, 0.009, 14, black, tin, (-0.06, 0.03, z), 0.0, text="IX-80", ink=M.plastic((0.3, 0.3, 0.3), 0.7))
    _soic(0.045, 0.02, 0.006, 7, black, tin, (0.07, 0.07, z), 0.0)
    _soic(0.045, 0.02, 0.006, 7, black, tin, (0.07, 0.025, z), 0.0)
    _soic(0.03, 0.02, 0.006, 4, black, tin, (0.13, -0.04, z), math.pi / 2)
    can = KI.metal("aluminum", None, rough=0.3, dirt=0.1)
    sleeve = M.plastic((0.02, 0.05, 0.25), 0.35, name="cap_sleeve")
    for k, (x, y) in enumerate(((-0.14, 0.08), (-0.14, 0.03), (0.0, -0.05), (0.035, -0.05))):
        r = 0.011 if k < 2 else 0.0085
        h = 0.03 if k < 2 else 0.022
        K.cyl(r, h, (x, y, z), sleeve, verts=24, bevel=0.0015)
        K.cyl(r * 0.92, 0.0012, (x, y, z + h), can, verts=24, bevel=0.0004)
        K.box((r * 1.6, 0.0012, 0.0008), (x, y, z + h + 0.0012), M.plastic((0.15, 0.15, 0.16)), bevel=0)
    smd_b = M.plastic((0.03, 0.03, 0.03), 0.4)
    smd_c = M.plastic((0.35, 0.22, 0.1), 0.5, name="mlcc")
    for i in range(22):
        x, y = rnd.uniform(-W * 0.4, W * 0.42), rnd.uniform(-D * 0.28, D * 0.4)
        rz = rnd.choice((0, math.pi / 2))
        body = smd_b if rnd.random() < 0.5 else smd_c
        K.box((0.007, 0.0035, 0.0025), (x, y, z), body, bevel=0.0004, base=True, rot=(0, 0, rz))
        for s in (-1, 1):
            K.box((0.0016, 0.0037, 0.0027), (x + s * 0.0035 * math.cos(rz), y + s * 0.0035 * math.sin(rz), z), tin,
                  bevel=0.0003, base=True, rot=(0, 0, rz))
    # crystal + header + connector
    K.box((0.016, 0.006, 0.006), (-0.005, 0.085, z), can, bevel=0.002, base=True)
    hdr = M.plastic((0.02, 0.02, 0.02), 0.5)
    K.box((0.1, 0.012, 0.01), (0.07, 0.105, z), hdr, bevel=0.001, base=True)
    for i in range(10):
        for j in (-1, 1):
            K.box((0.0025, 0.0025, 0.026), (0.025 + i * 0.01, 0.105 + j * 0.003, z), gold, bevel=0.0004, base=True)
    K.box((0.05, 0.035, 0.022), (-0.135, -0.075, z), M.plastic((0.85, 0.84, 0.8), 0.4), bevel=0.002, base=True)
    # silkscreen
    for txt, x, y, s in (("U1", -0.06, -0.012, 0.012), ("C3", -0.14, 0.105, 0.009), ("J2", 0.07, 0.125, 0.01),
                         ("INDUSTRIUM  REV 2.1", 0.06, -0.085, 0.012)):
        KI.text_mesh(txt, s, 0.0002, silk, loc=(x, y, T + 0.0004))
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.15))
    return frame(pitch=44.0)


def _circle(r, n):
    return [(r * math.cos(math.tau * i / n), r * math.sin(math.tau * i / n)) for i in range(n)]


def chip(item, material, color, p):
    """Quad flat package IC with gull-wing leads and laser marking."""
    if material == "ceramic":
        body = M.plastic((0.82, 0.8, 0.72), 0.45, name="ceramic")
    elif material in ("gold", "pcb_black", "pcb_green", "pcb_blue", "pcb_red"):
        body = M.plastic((0.02, 0.02, 0.022), 0.5, name="epoxy")
    else:
        body = KI.surf(material or "plastic_black", color) if material not in (None, "plastic_black") else \
            M.plastic((0.02, 0.02, 0.022), 0.5, name="epoxy")
    tin = KI.metal("tin", None, rough=0.2, dirt=0.05)
    objs = _qfp(0.22, 0.032, 16, body, tin, (0, 0, 0), 0.0, text=None)
    ink = M.plastic((0.32, 0.32, 0.32), 0.7, name="laser") if material != "ceramic" else M.plastic((0.05, 0.05, 0.05))
    for txt, y, s in (("IX-4040", 0.03, 0.028), ("2647 KR", -0.01, 0.02), ("MADE IN FRONTIER", -0.045, 0.012)):
        KI.text_mesh(txt, s, 0.0003, ink, loc=(0.0, y, 0.032))
    if material in ("ceramic", "gold"):
        K.box((0.11, 0.11, 0.002), (0, 0, 0.032), KI.metal("gold", None, rough=0.2, dirt=0.05), bevel=0.003, base=True)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.3))
    return frame(pitch=44.0)


def processor(item, material, color, p):
    """CPU: green substrate, nickel heat spreader with engraved marking, SMD caps, gold corner marker."""
    mc = MASK.get(material) or MASK["pcb_green"] if material != "glow" else (0.012, 0.012, 0.014)
    if material == "gold":
        mc = (0.02, 0.02, 0.022)
    sub = solder_mask(mc)
    nickel = KI.metal("gold", None, rough=0.15, dirt=0.05) if material == "gold" else \
        KI.metal("stainless", None, rough=0.22, dirt=0.1)
    gold = KI.metal("gold", None, rough=0.2, dirt=0.05)
    S, T = 0.26, 0.012
    K.box((S, S, T), (0, 0, 0), sub, bevel=0.0015, base=True, name="substrate")
    ihs = K.box((0.19, 0.19, 0.008), (0, 0, T), nickel, bevel=0.004, base=True, name="ihs_flange")
    top = K.box((0.16, 0.16, 0.008), (0, 0, T + 0.008), nickel, bevel=0.006, base=True, name="ihs")
    ink = M.metal("dark_steel", rough=0.6)
    for txt, y, s in (("INDUSTRIUM", 0.035, 0.019), ("IX9 9900K", 0.005, 0.016), ("6.20 GHZ", -0.02, 0.013),
                      ("SRZ7Q  L341", -0.045, 0.011)):
        KI.text_mesh(txt, s, 0.0003, ink, loc=(0.0, y, T + 0.016), font=KI.FONT_MONO)
    K.prism([(0, 0), (0.025, 0), (0, 0.025)], 0.0008, (-S / 2 + 0.006, -S / 2 + 0.006, T), gold, rot=(math.pi / 2, 0, 0), bevel=0)
    cap = M.plastic((0.35, 0.22, 0.1), 0.5, name="mlcc")
    for i in range(10):
        for s in (-1, 1):
            x = -0.09 + i * 0.02
            K.box((0.006, 0.003, 0.0025), (x, s * 0.112, T), cap, bevel=0.0004, base=True)
            K.box((0.0015, 0.0032, 0.0027), (x - 0.003, s * 0.112, T), KI.metal("tin", None, dirt=0.1), bevel=0.0003, base=True)
            K.box((0.0015, 0.0032, 0.0027), (x + 0.003, s * 0.112, T), KI.metal("tin", None, dirt=0.1), bevel=0.0003, base=True)
    if material == "glow" or (color and material == "gold"):
        gc = KI.glow_color(color) if color else (1.0, 0.55, 0.15)
        K.box((0.1, 0.1, 0.0012), (0, 0, T + 0.016), M.emissive(gc, 0.9), bevel=0.003, base=True)
        K.box((0.104, 0.104, 0.0014), (0, 0, T + 0.0155), M.plastic((0.01, 0.01, 0.01), 0.3), bevel=0.003, base=True)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.25))
    return frame(pitch=46.0)


def module_card(item, material, color, p):
    """Rugged plug-in module cartridge: coloured anodised shell, glowing status window, gold contacts."""
    c = KI.lin(color) if color else (0.04, 0.25, 0.8)
    shell = KI.anodized(tuple(x * 0.6 for x in c), 0.32) if material not in ("plastic_color", "plastic_white", "plastic_black") \
        else KI.surf(material, color)
    if material == "plastic_color":
        shell = M.plastic(c, 0.35, name="module_shell")
    end = M.painted((0.03, 0.032, 0.036), wear=0.15, grime=0.2, rough=0.4, name="graphite")
    gold = KI.metal("gold", None, rough=0.2, dirt=0.05)
    W, D, H = 0.32, 0.075, 0.22
    z0 = 0.022
    K.box((W - 0.06, 0.012, z0 + 0.004), (0, 0, 0), solder_mask(MASK.get(material, MASK["pcb_green"])), bevel=0.001, base=True)
    for i in range(18):
        x = -W / 2 + 0.045 + i * (W - 0.09) / 17
        for s in (-1, 1):
            K.box((0.008, 0.0008, 0.018), (x, s * 0.0064, 0.002), gold, bevel=0.0002, base=True)
    K.box((W - 0.05, D, H - 0.01), (0, 0, z0), shell, bevel=0.012, base=True, name="shell")
    for sx in (-1, 1):
        K.box((0.03, D + 0.008, H), (sx * (W / 2 - 0.015), 0, z0 - 0.004), end, bevel=0.01, base=True, name="endcap")
    # ribbed grip + glowing status window on the -Y face
    for i in range(7):
        K.box((0.006, 0.006, 0.07), (W * 0.22 + i * 0.012, -D / 2 - 0.002, z0 + H * 0.55), end, bevel=0.002)
    K.box((W * 0.48, 0.006, 0.03), (-W * 0.08, -D / 2 - 0.002, z0 + H * 0.72), M.plastic((0.01, 0.01, 0.012), 0.2), bevel=0.004)
    K.box((W * 0.44, 0.004, 0.018), (-W * 0.08, -D / 2 - 0.0035, z0 + H * 0.72), M.emissive(KI.glow_color(c), 1.1), bevel=0.002)
    lab = M.plastic((0.85, 0.85, 0.82), 0.5, name="label")
    K.box((W * 0.3, 0.003, 0.05), (-W * 0.15, -D / 2 - 0.001, z0 + H * 0.36), lab, bevel=0.001)
    KI.project_text(p.get("label", (item.get("name") or "MODULE").upper()[:10]), 0.014, (-W * 0.15, -D / 2 - 0.0027, z0 + H * 0.37),
                    (0, -1, 0), mat=M.plastic((0.03, 0.03, 0.03), 0.5), depth=0.0004)
    KI.project_text("MK " + ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"][max(0, min(7, int(p.get("tier", 1)) - 1))], 0.03, (W * 0.2, -D / 2 - 0.0005, z0 + H * 0.25), (0, -1, 0),
                    mat=M.plastic((0.9, 0.9, 0.88), 0.4), depth=0.0006)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, -0.2))
    return frame(pitch=55.0)


def battery(item, material, color, p):
    """Industrial lead-acid battery block: lead terminals with red/black boots, vent caps, handle, label."""
    c = KI.lin(color) if color else (0.02, 0.022, 0.025)
    case = M.plastic(c, 0.42, name="battery_case") if material in (None, "paint", "plastic_color", "plastic_black") else \
        KI.surf(material, color)
    lid = M.plastic((0.05, 0.052, 0.056) if sum(c) > 0.2 else (0.22, 0.22, 0.23), 0.45, name="battery_lid")
    lead = KI.metal("lead", None, rough=0.45, dirt=0.3)
    W, D, H = 0.32, 0.18, 0.2
    K.box((W, D, H), (0, 0, 0), case, bevel=0.008, base=True, name="case")
    K.box((W + 0.006, D + 0.006, 0.03), (0, 0, H), lid, bevel=0.006, base=True, name="lid")
    zt = H + 0.03
    for sx, boot, sign in ((-1, (0.6, 0.02, 0.01), "+"), (1, (0.02, 0.02, 0.02), "-")):
        x = sx * (W / 2 - 0.045)
        K.cyl(0.026, 0.008, (x, -0.04, zt), lid, verts=32, bevel=0.002)
        K.cyl(0.015, 0.03, (x, -0.04, zt + 0.008), lead, verts=24, bevel=0.002, r2=0.013)
        bt = KI.lathe([(0.0, 0.0), (0.024, 0.0), (0.022, 0.02), (0.012, 0.032), (0.0, 0.034)], M.plastic(boot, 0.45),
                      segs=32, name="boot")
        bt.location = (x, -0.04, zt + 0.014)
        bt.scale = (1, 1, 1)
        KI.text_mesh(sign, 0.04, 0.0008, M.plastic((0.9, 0.9, 0.88), 0.4), loc=(x, 0.03, zt + 0.0002))
    for i in range(6):
        K.cyl(0.011, 0.006, (-0.075 + i * 0.03, 0.03, zt), M.plastic((0.6, 0.6, 0.6) if sum(c) < 0.2 else (0.03, 0.03, 0.03), 0.5),
              verts=20, bevel=0.002)
    # handle folded down
    hp = [(-0.06, 0.06, zt + 0.004), (-0.06, 0.075, zt + 0.006), (0.06, 0.075, zt + 0.006), (0.06, 0.06, zt + 0.004)]
    KI.sweep(hp, KI.rect_section(0.012, 0.006, 0.002), M.plastic((0.02, 0.02, 0.02), 0.5), name="handle")
    # front label band
    band = KI.paint((0.8, 0.45, 0.01), wear=0.0, grime=0.1, rust=0.0, rough=0.4, name="label_band")
    K.box((W * 0.86, 0.002, 0.065), (0, -D / 2 - 0.001, H * 0.55), band, bevel=0.0006)
    KI.project_text("12V  200Ah", 0.026, (0, -D / 2 - 0.0025, H * 0.56), (0, -1, 0), mat=M.plastic((0.02, 0.02, 0.02), 0.5),
                    depth=0.0005)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.28))
    return frame(pitch=52.0)


def cell(item, material, color, p):
    """High-density power cell: knurled metal end caps, carbon sleeve, glowing charge window."""
    c = KI.lin(color) if color else (0.15, 0.6, 1.0)
    cap = KI.metal("stainless", None, rough=0.2, dirt=0.25)
    sleeve = KI.carbon_fiber() if material in (None, "glow", "carbon_fiber") else KI.surf(material, color)
    R, H = 0.085, 0.3
    objs = []
    prof = [(0, 0), (R - 0.004, 0), (R, 0.004), (R, 0.05)]
    objs.append(KI.lathe(prof + [(R - 0.006, 0.055), (0, 0.055)], cap, segs=64, name="cap_lo"))
    objs.append(KI.lathe([(0, 0.052), (R - 0.004, 0.052), (R - 0.004, H - 0.052), (0, H - 0.052)], sleeve, segs=64))
    objs.append(KI.lathe([(0, H - 0.055), (R - 0.006, H - 0.055), (R, H - 0.05), (R, H - 0.004), (R - 0.004, H),
                          (0.03, H), (0.03, H + 0.012), (0.024, H + 0.016), (0, H + 0.016)], cap, segs=64, name="cap_hi"))
    for z in (0.015, 0.027, 0.039, H - 0.039, H - 0.027, H - 0.015):
        objs.append(K.torus(R + 0.0005, 0.0025, (0, 0, z), KI.metal("dark_steel", None, dirt=0.3), segs=64, rsegs=8))
    # glowing window bands
    glow = KI.liquid(c, "glow", 0.7)
    objs.append(KI.lathe([(R - 0.003, H * 0.42), (R + 0.001, H * 0.42), (R + 0.001, H * 0.58), (R - 0.003, H * 0.58)], glow,
                         segs=64, closed=True, name="window"))
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        objs.append(K.box((0.012, 0.012, H * 0.2), ((R + 0.002) * math.cos(a), (R + 0.002) * math.sin(a), H * 0.4), cap,
                          bevel=0.003, base=True, rot=(0, 0, a)))
    objs.append(KI.wrap_text("9.6 kWh", R + 0.0003, math.radians(-55), H * 0.27, 0.022,
                             M.plastic((0.85, 0.85, 0.82), 0.4, name="print")))
    return frame(pitch=55.0)


def solar_cell(item, material, color, p):
    """Small mono-crystalline PV module on a kick-stand."""
    cellm = KI.pv_cell(KI.lin(color) if color else (0.012, 0.022, 0.07))
    alu = KI.metal("aluminum", None, rough=0.3, dirt=0.25)
    back = M.plastic((0.8, 0.8, 0.78), 0.5, name="backsheet")
    silver = KI.metal("silver", None, rough=0.25, dirt=0.05)
    W, D = 0.42, 0.31
    objs = [K.box((W, D, 0.004), (0, 0, 0), back, bevel=0.001, base=True)]
    nx, ny = 4, 3
    cw, ch = (W - 0.04) / nx, (D - 0.04) / ny
    for i in range(nx):
        for j in range(ny):
            x = -W / 2 + 0.02 + cw * (i + 0.5)
            y = -D / 2 + 0.02 + ch * (j + 0.5)
            objs.append(K.box((cw - 0.004, ch - 0.004, 0.002), (x, y, 0.004), cellm, bevel=0.0015, base=True))
            for b in (-1, 1):
                objs.append(K.box((0.0025, ch - 0.006, 0.0004), (x + b * cw * 0.22, y, 0.006), silver, bevel=0, base=True))
    for sx in (-1, 1):
        objs.append(K.box((0.012, D + 0.012, 0.016), (sx * (W / 2 + 0.006), 0, -0.006), alu, bevel=0.002, base=True))
    for sy in (-1, 1):
        objs.append(K.box((W, 0.012, 0.016), (0, sy * (D / 2 + 0.006), -0.006), alu, bevel=0.002, base=True))
    jb = K.box((0.08, 0.05, 0.02), (0, 0.04, -0.026), M.plastic((0.02, 0.02, 0.02), 0.5), bevel=0.004, base=True)
    objs.append(jb)
    tilt = math.radians(34)
    KI.group(objs, (0, 0, 0), (tilt, 0, 0))
    dz = KI.ground(objs)
    yb, zb = (D / 2) * math.cos(tilt), (D / 2) * math.sin(tilt) + dz
    for sx in (-1, 1):
        KI.curve_tube([(sx * W * 0.36, yb - 0.03, zb - 0.03), (sx * W * 0.36, yb + 0.07, 0.004)], 0.0065, alu, name="leg")
        K.box((0.03, 0.03, 0.004), (sx * W * 0.36, yb + 0.07, 0.0), alu, bevel=0.001, base=True)
    KI.group(KI.model_objects(), (0, 0, 0), (0, 0, 0.25))
    return frame(pitch=50.0)


def lens(item, material, color, p):
    """Coated biconvex lens in a knurled anodised mount on a post."""
    tint = KI.lin(color) if color else (0.95, 0.98, 0.98)
    glass = KI.coated_glass(tint)
    mount = KI.anodized((0.015, 0.015, 0.017), 0.35)
    R = 0.11
    sag, e = 0.022, 0.006
    Rs = (R * R + sag * sag) / (2 * sag)
    prof = [(0, -e - sag)]
    for i in range(1, 17):
        r = R * i / 16
        prof.append((r, -e - (sag - (Rs - math.sqrt(Rs * Rs - r * r)))))
    prof += [(R, e)]
    for i in range(15, -1, -1):
        r = R * i / 16
        prof.append((r, e + (sag - (Rs - math.sqrt(Rs * Rs - r * r)))))
    parts = [KI.lathe(prof, glass, segs=72, name="lens", smooth=60)]
    ring = [(R - 0.006, -0.02), (R + 0.022, -0.02), (R + 0.022, 0.02), (R - 0.006, 0.02), (R - 0.006, 0.012), (R - 0.001, 0.012),
            (R - 0.001, -0.012), (R - 0.006, -0.012)]
    parts.append(KI.lathe(ring, mount, segs=96, closed=True, name="mount", bevel=0.0012))
    for k in range(72):
        a = math.tau * k / 72
        parts.append(K.box((0.0035, 0.004, 0.026), ((R + 0.0225) * math.cos(a), (R + 0.0225) * math.sin(a), 0), mount,
                           bevel=0.0008, rot=(0, 0, a)))
    parts.append(KI.text_mesh("f 250  Ø 220", 0.011, 0.0004, M.plastic((0.85, 0.85, 0.82), 0.4, name="print"),
                              loc=(0, -R - 0.004, 0.0205), rot=(0, 0, 0)))
    g = KI.group(parts, (0, 0, 0), (0, 0, 0))
    g.rotation_euler = Euler((math.radians(90), 0, math.radians(-20)), "XYZ")
    g.location = (0, 0, R + 0.075)
    post = KI.metal("stainless", None, rough=0.2, dirt=0.15)
    K.cyl(0.011, 0.07, (0, 0.0, 0.012), post, verts=24)
    K.cyl(0.055, 0.012, (0, 0.0, 0.0), mount, verts=48, bevel=0.003)
    return frame(pitch=58.0)


def filter_(item, material, color, p):
    """Pleated cartridge filter with metal end caps and perforated core."""
    media_c = KI.lin(color) if color else (0.75, 0.68, 0.5)
    media = KI.fabric(media_c, weave=900.0, rough=0.9, name="media", coarse=0.3)
    capm = KI.metal(material if KI.is_metal(material or "") else "stainless", None, rough=0.3, dirt=0.4)
    n = 44
    ro, ri = 0.1, 0.075
    outer, inner = [], []
    for i in range(n * 2):
        a = math.pi * i / n
        r = ro if i % 2 == 0 else ri
        outer.append((r * math.cos(a), r * math.sin(a)))
        inner.append(((ri - 0.012) * math.cos(a), (ri - 0.012) * math.sin(a)))
    H = 0.28
    KI.ring_extrude(outer, inner, 0.02, H - 0.02, media, name="pleats", smooth=20)
    for z0, flip in ((0.0, False), (H, True)):
        prof = [(0.04, 0), (ro + 0.008, 0), (ro + 0.008, 0.028), (ro + 0.002, 0.03), (ro + 0.002, 0.008), (0.05, 0.008),
                (0.04, 0.008)]
        c = KI.lathe(prof, capm, segs=96, closed=True, name="endcap")
        if flip:
            c.rotation_euler = (math.pi, 0, 0)
            c.location.z = H
    K.torus(0.046, 0.007, (0, 0, H + 0.004), M.rubber(), segs=48, rsegs=12)
    core = KI.lathe([(0.052, 0.008), (0.052, H - 0.008), (0.048, H - 0.008), (0.048, 0.008)], KI.metal("steel", None, dirt=0.5),
                    segs=48, closed=True, name="core")
    return frame(pitch=55.0)


ARCHETYPES = {
    "circuit_board": circuit_board,
    "chip": chip,
    "processor": processor,
    "module_card": module_card,
    "battery": battery,
    "cell": cell,
    "solar_cell": solar_cell,
    "lens": lens,
    "filter": filter_,
}
