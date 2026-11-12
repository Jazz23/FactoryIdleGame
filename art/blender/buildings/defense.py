"""Defense archetypes: turret, wall_segment, radar, shield_generator."""
import math

import bmesh
from mathutils import Vector

import kit as K
import kit_industry as KI
import materials as M
from buildings import Rig

TAU = KI.TAU


def _size(spec):
    w, d = spec.get("size", [1, 1])
    return float(w), float(d)


def _armor(st):
    """Armour paint per tier: olive drab -> sand -> naval grey -> graphite."""
    col = {1: (0.06, 0.07, 0.035), 2: (0.2, 0.16, 0.08), 3: (0.16, 0.17, 0.18), 4: (0.035, 0.037, 0.042)}[st.tier]
    return st.mat(tuple(st.paint) if st.variant == "paint" else col, name="armor", wear=0.9)


# =========================================================================== turret
def turret(spec, p):
    """Automated defence turret on an armoured octagonal pedestal. variant: 'gun' (default, twin
    autocannon with ammo box), 'laser' (focusing lens + radiator fins), 'missile' (4-cell box
    launcher). Head sweeps back and forth; sensor and status lamp blink."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s
    kinds = {"laser": "laser", "lance": "laser", "missile": "missile", "flame": "flame", "mortar": "mortar",
             "railgun": "railgun", "autocannon": "cannon", "howitzer": "howitzer", "cannon": "cannon"}
    variant = kinds.get(st.variant, "gun")
    if variant in ("howitzer", "mortar") or s > 2.5:
        k = s ** 0.85
    armor = _armor(st) if not p.get("paint") else st.body()
    trim = st.accent_mat() if st.tier >= 3 else M.metal("dark_steel", dirt=st.dirt)
    conc = st.concrete(0.5)
    K.box((w * 0.96, d * 0.96, 0.08), (0, 0, 0), conc, bevel=0.02, base=True)
    K.hazard_edge(w * 0.96, d * 0.96, 0.08, width=0.04 * k)
    z0 = 0.08
    pr = 0.34 * k
    ph = 0.32 * k
    K.cyl(pr * 1.12, 0.06, (0, 0, z0), M.metal("dark_steel", dirt=st.dirt), verts=8, bevel=0.01)
    K.cyl(pr, ph, (0, 0, z0 + 0.06), armor, verts=8, bevel=0.012, r2=pr * 0.85, name="pedestal")
    K.bolts(Vector((0, 0, z0 + 0.06)), pr * 1.04, 16, r=0.012 * k ** 0.5)
    K.box((pr * 0.55, 0.02, ph * 0.45), (0.05 * k, -pr * 0.88, z0 + 0.06 + ph * 0.3), M.metal("dark_steel", dirt=0.6), bevel=0.004, rot=(0.12, 0, 0.0))
    zr = z0 + 0.06 + ph
    K.cyl(pr * 0.8, 0.05 * k, (0, 0, zr), M.metal("steel", dirt=0.6), verts=40, name="race_ring")
    zh = zr + 0.05 * k
    head = []
    # armoured head (faceted)
    hw, hd, hh = 0.56 * k, 0.46 * k, 0.24 * k
    head.append(KI.frustum((hw, hd), (hw * 0.78, hd * 0.8), hh, (0, 0, zh), armor, top_offset=(-0.05 * k, 0), bevel=0.012, name="head"))
    head.append(K.box((hw * 0.4, hd * 1.02, hh * 0.25), (-hw * 0.18, 0, zh + hh * 0.3), trim, bevel=0.006))
    head.append(K.box((0.04 * k, hd * 0.86, hh * 0.9), (hw * 0.47, 0, zh + hh * 0.05), armor, bevel=0.01, base=True, name="mantlet"))
    head.append(KI.hazard_band((-hw * 0.05, -hd / 2 - 0.004, zh + hh * 0.12), hw * 0.6, 0.03 * k))
    # armour detail: commander hatch, side vents, seam bolts, spare track-style plates
    head.append(K.cyl(0.09 * k, 0.04 * k, (-hw * 0.28, -hd * 0.12, zh + hh), armor, verts=20, name="hatch"))
    head.append(K.torus(0.09 * k, 0.008 * k, (-hw * 0.28, -hd * 0.12, zh + hh + 0.04 * k), M.metal("dark_steel")))
    for sy in (-1, 1):
        head.append(K.box((hw * 0.35, 0.012, hh * 0.3), (-hw * 0.2, sy * (hd / 2 * 0.89 + 0.002), zh + hh * 0.55), M.metal("dark_steel", dirt=0.7), bevel=0.003))
        for i in range(4):
            head.append(K.box((hw * 0.32, 0.008, 0.012 * k), (-hw * 0.2, sy * (hd / 2 * 0.89 + 0.008), zh + hh * (0.45 + 0.06 * i)), M.metal("dark_steel"), bevel=0.001))
    head += KI.bolt_row((-hw * 0.4, -hd / 2 * 0.83 - 0.006, zh + hh * 0.85), (hw * 0.3, -hd / 2 * 0.83 - 0.006, zh + hh * 0.85), 7, axis="-y", r=0.009 * k ** 0.5)
    # sensor pod on top
    head.append(K.box((0.14 * k, 0.12 * k, 0.1 * k), (-0.08 * k, hd * 0.2, zh + hh + 0.05 * k), M.metal("dark_steel"), bevel=0.01))
    sens_m, sens_s = KI.anim_emit((1.0, 0.08, 0.04) if st.tier < 4 else st.glow_col, 8.0, "sensor")
    head.append(K.cyl(0.035 * k, 0.02, (-0.01 * k, hd * 0.2, zh + hh + 0.05 * k), sens_m, rot=K.AXES["x"], verts=16, base=False))
    head.append(K.cyl(0.004, 0.3 * k, (-0.2 * k, -hd * 0.25, zh + hh), M.metal("dark_steel"), verts=6))
    emitters = []
    lights = []
    # weapon on an elevation pivot (barrels along local +X)
    ep = Vector((hw * 0.35, 0, zh + hh * 0.55))
    weap = []
    gm = M.metal("dark_steel", rough=0.3)
    elev = -0.12
    if variant == "gun":
        Lg = 0.55 * k   # barrel length (kept short so the sweep barely leaves the footprint)
        for sy in (-1, 1):
            y = sy * hd * 0.2
            weap.append(K.cyl(0.04 * k, 0.2 * k, (hw * 0.45, y, ep.z), gm, rot=K.AXES["x"], verts=16, name="recoil"))
            weap.append(K.cyl(0.018 * k, Lg, (hw * 0.6, y, ep.z), gm, rot=K.AXES["x"], verts=12, name="barrel"))
            weap.append(K.cyl(0.028 * k, 0.07 * k, (hw * 0.6 + Lg - 0.05 * k, y, ep.z), gm, rot=K.AXES["x"], verts=12, name="muzzle"))
        head.append(K.box((0.24 * k, 0.12 * k, 0.16 * k), (-0.02 * k, -hd / 2 - 0.06 * k, zh + hh * 0.45), M.painted((0.08, 0.12, 0.05), wear=0.5, name="ammo_can"), bevel=0.008))
        head.append(K.box((0.12 * k, 0.04 * k, 0.03), (hw * 0.15, -hd / 2 - 0.02 * k, zh + hh * 0.62), M.metal("brass", dirt=0.5), bevel=0.003))
        mz = ep + Vector((hw * 0.6 + Lg + 0.03 * k - ep.x, 0, 0))
    elif variant in ("cannon", "howitzer"):
        L = (0.58 if variant == "cannon" else 0.78) * k
        cal = (0.035 if variant == "cannon" else 0.045) * k
        weap.append(K.cyl(cal * 2.4, 0.3 * k, (hw * 0.42, 0, ep.z), gm, rot=K.AXES["x"], verts=20, name="breech_sleeve"))
        for sy in (-1, 1):
            weap.append(K.cyl(cal * 0.8, 0.28 * k, (hw * 0.42, sy * cal * 2.6, ep.z + cal * 1.2), M.metal("chrome"), rot=K.AXES["x"], verts=12, name="recuperator"))
        weap.append(K.cyl(cal, L, (hw * 0.42 + 0.28 * k, 0, ep.z), gm, rot=K.AXES["x"], verts=20, name="barrel", r2=cal * 0.85))
        mb = Vector((hw * 0.42 + 0.28 * k + L, 0, ep.z))
        weap.append(K.box((0.1 * k, cal * 3.2, cal * 2.0), mb, gm, bevel=0.01, name="muzzle_brake"))
        head.append(K.box((0.3 * k, 0.16 * k, 0.2 * k), (-0.05 * k, -hd / 2 - 0.08 * k, zh + hh * 0.4), M.painted((0.08, 0.12, 0.05), wear=0.5, name="ammo_can"), bevel=0.01))
        mz = mb + Vector((0.08 * k, 0, 0))
        elev = -0.1 if variant == "cannon" else -0.3
    elif variant == "mortar":
        for i in range(2 if s >= 2.5 else 1):
            y = (i - 0.5) * hd * 0.45 if s >= 2.5 else 0.0
            weap.append(K.cyl(0.07 * k, 0.55 * k, (hw * 0.3, y, ep.z), gm, rot=K.AXES["x"], verts=24, name="tube"))
            weap.append(K.torus(0.072 * k, 0.012 * k, (hw * 0.3 + 0.55 * k, y, ep.z), gm, rot=K.AXES["x"], segs=24, rsegs=6))
            weap.append(K.torus(0.075 * k, 0.015 * k, (hw * 0.3 + 0.2 * k, y, ep.z), M.metal("steel"), rot=K.AXES["x"], segs=24, rsegs=6))
        mz = Vector((hw * 0.3 + 0.55 * k, 0, ep.z))   # tube mouth in the weapon frame (elevation applied by the pivot)
        elev = -0.95
        for i in range(4):
            head.append(K.cyl(0.04 * k, 0.22 * k, (-hw * 0.3 + i * 0.09 * k, hd * 0.55, zh), M.painted((0.25, 0.27, 0.12), name="shell_olive"), verts=12))
    elif variant == "flame":
        weap.append(K.cyl(0.05 * k, 0.5 * k, (hw * 0.42, 0, ep.z), gm, rot=K.AXES["x"], verts=16, r2=0.035 * k, name="projector"))
        weap.append(K.cyl(0.04 * k, 0.08 * k, (hw * 0.42 + 0.5 * k, 0, ep.z), M.metal("copper", dirt=0.8), rot=K.AXES["x"], verts=16, r2=0.03 * k))
        pm, ps = KI.soft_glow((1.0, 0.45, 0.06), 4.0, rim=False, name="pilot_flame", power=1.0)
        pilot = K.sphere(0.035 * k, (hw * 0.42 + 0.6 * k, 0, ep.z + 0.02 * k), pm, segs=12, rings=8, scale=(1.6, 1, 1))
        weap.append(pilot)
        an.value(ps, lambda t: 3.0 + 2.0 * KI.flicker(t, 0.3, 1.0))
        for sy in (-1, 1):
            head.append(K.cyl(0.08 * k, 0.4 * k, (-hw * 0.35, sy * hd * 0.32, zh + hh * 0.5), M.painted((0.5, 0.05, 0.02), wear=0.5, name="fuel_red"),
                              rot=K.AXES["x"], verts=24, base=False))
        mz = Vector((hw * 0.42 + 0.62 * k, 0, ep.z))
        lights.append({"pos": [mz.x, mz.y, mz.z], "color": [1.0, 0.5, 0.1], "energy": 0.4, "flicker": True})
        emitters.append({"pos": list(mz), "type": "fire"})
    elif variant == "railgun":
        cm, cs = KI.anim_emit(st.glow_col, 6.0, "rail_coil")
        L = 0.85 * k
        for sy in (-1, 1):
            weap.append(K.box((L, 0.03 * k, 0.07 * k), (hw * 0.42 + L / 2, sy * 0.05 * k, ep.z), gm, bevel=0.006, name="rail"))
        for i in range(6):
            x = hw * 0.42 + 0.08 * k + i * L / 6.5
            weap.append(K.box((0.035 * k, 0.17 * k, 0.12 * k), (x, 0, ep.z), st.accent_mat() if st.tier >= 3 else armor, bevel=0.006))
            weap.append(K.box((0.012, 0.18 * k, 0.02 * k), (x + 0.02 * k, 0, ep.z + 0.06 * k), cm, bevel=0.002))
        weap.append(K.box((0.22 * k, 0.24 * k, 0.18 * k), (hw * 0.42, 0, ep.z), armor, bevel=0.012, name="capacitor_block"))
        an.value(cs, lambda t: 2.0 + 10.0 * (t % 0.5) * 2)
        mz = Vector((hw * 0.42 + L, 0, ep.z))
        lights.append({"pos": [hw * 0.42 + L / 2, 0, ep.z], "color": list(st.glow_col), "energy": 0.6, "flicker": True})
        elev = -0.08
    elif variant == "laser":
        big = st.variant == "lance"
        kl = k * (1.3 if big else 1.0)
        weap.append(K.cyl(0.07 * kl, 0.55 * kl, (hw * 0.45, 0, ep.z), st.accent_mat() if st.tier >= 3 else armor, rot=K.AXES["x"], verts=24, name="emitter_body"))
        for i in range(6):
            weap.append(K.cyl(0.095 * kl, 0.012, (hw * 0.5 + i * 0.05 * kl, 0, ep.z), M.metal("aluminum", dirt=0.3), rot=K.AXES["x"], verts=24, base=False))
        lens_m, lens_s = KI.anim_emit(st.glow_col if (st.tier >= 3 or p.get("glow")) else (1.0, 0.25, 0.1), 10.0, "lens")
        weap.append(K.cyl(0.05 * kl, 0.02, (hw * 0.45 + 0.55 * kl, 0, ep.z), lens_m, rot=K.AXES["x"], verts=24))
        weap.append(K.torus(0.06 * kl, 0.012, (hw * 0.45 + 0.56 * kl, 0, ep.z), M.metal("chrome"), rot=K.AXES["x"]))
        an.value(lens_s, lambda t: 6.0 + 6.0 * (0.5 + 0.5 * math.sin(TAU * 2 * t)))
        mz = Vector((hw * 0.45 + 0.57 * kl, 0, ep.z))
        lights.append({"pos": [0, 0, ep.z], "color": list(st.glow_col), "energy": 0.5, "flicker": True})
    else:
        box = K.box((0.42 * k, 0.36 * k, 0.3 * k), (hw * 0.4, 0, ep.z), armor, bevel=0.015, name="launcher")
        weap.append(box)
        for i in range(2):
            for j in range(2):
                c = Vector((hw * 0.4 + 0.212 * k, (i - 0.5) * 0.17 * k, ep.z + (j - 0.5) * 0.14 * k))
                weap.append(K.cyl(0.055 * k, 0.012, c, M.plastic((0.02, 0.02, 0.02), 0.6), rot=K.AXES["x"], verts=20, base=False))
                weap.append(K.cyl(0.04 * k, 0.03 * k, c - Vector((0.005, 0, 0)), M.painted((0.6, 0.6, 0.58), name="warhead"), rot=K.AXES["x"], verts=16, r2=0.005))
        mz = Vector((hw * 0.4 + 0.25 * k, 0, ep.z))
    # markers that ride with the weapon so the Godot hints sit at the muzzle in the rest pose
    mz_mark = KI.pivot(mz, name="muzzle_mark")
    weap.append(mz_mark)
    lmarks = []
    for l_ in lights:
        lmarks.append(KI.pivot(l_["pos"], name="light_mark"))
        weap.append(lmarks[-1])
    epp = KI.pivot(ep, name="elevation")
    KI.bind(weap, epp)
    an.rotate(epp, lambda t: elev - 0.06 * math.sin(TAU * 2 * t), axis="Y")
    hp = KI.pivot((0, 0, 0), name="yaw")
    KI.bind(head + [epp], hp)
    base_yaw = math.radians(40)
    an.rotate(hp, lambda t: base_yaw + math.radians(50) * math.sin(TAU * t), axis="Z")
    an.value(sens_s, lambda t: 2.0 + 10.0 * KI.blink(t, 4, 0.3))
    # status lamp + junction box on pedestal
    _, ls = KI.status_lamp((pr * 0.6, -pr * 0.6, z0 + 0.06), (1.0, 0.08, 0.03), 10.0, r=0.025 * k ** 0.5)
    an.value(ls, lambda t: 1.0 + 12.0 * KI.blink(t, 2, 0.25))
    if s >= 1.5:
        KI.cabinet((0.36 * w, -0.34 * d, z0), 0.0, w=0.22 * k, d=0.12 * k, h=0.3 * k, mat=armor, screen_col=(1.0, 0.25, 0.1))
        for i in range(3):
            K.box((0.3 * k, 0.15 * k, 0.12 * k), (-0.32 * w + i * 0.01, 0.3 * d - i * 0.14 * k, z0), M.painted((0.18, 0.16, 0.1), wear=0.6, name="sandbag"), bevel=0.04 * k)
    if variant != "flame":
        emitters.append({"pos": list(mz), "type": "sparks"})
    # move muzzle/glow hints from the weapon's local frame to the rest pose (t=0)
    import bpy
    an(0.0)
    bpy.context.view_layer.update()
    mzw = list(mz_mark.matrix_world.translation)
    for e in emitters:
        e["pos"] = [round(v, 3) for v in mzw]
    for l_, m_ in zip(lights, lmarks):
        l_["pos"] = [round(v, 3) for v in m_.matrix_world.translation]
    # framing: with_bounds samples the head sweep, so no full-circle reach points are needed
    return Rig(height=max(zh + hh + 0.35 * k, mz.z + 0.25 * k), frames=16, fps=10, update=an, lights=lights, emitters=emitters)


# =========================================================================== wall segment
def wall_segment(spec, p):
    """Defensive wall block: reinforced concrete footing and chamfered body running along the
    footprint's long axis, bolted steel armour plates on the visible faces, hazard band, lifting
    eyes, razor wire (tier 1-2) or a light strip (tier 3+), red status lamp. Static.
    variant 'concrete': plain jersey-profile barrier with reflectors and chevrons."""
    w, d = _size(spec)
    if d > w * 1.2:
        import bpy
        before = set(bpy.data.objects)
        sub = dict(spec)
        sub["size"] = [d, w]
        rig = wall_segment(sub, p)
        new = [o for o in bpy.data.objects if o not in before and o.parent is None]
        piv = KI.pivot((0, 0, 0), name="wall_rot")
        KI.bind(new, piv)
        piv.rotation_euler = (0, 0, math.pi / 2)
        for l_ in rig.lights:
            x, y, z = l_["pos"]
            l_["pos"] = [-y, x, z]
        return rig
    KI.begin()
    st = KI.Style(p)
    s = min(w, d)
    conc = M.concrete(0.6, tint=(0.82, 0.8, 0.76) if st.tier < 3 else (0.95, 0.95, 0.93))
    armor = _armor(st) if not p.get("paint") else st.body()
    H = 1.0 + 0.25 * s
    K.box((w * 0.99, d * (0.99 if abs(w - d) < 0.1 else 0.8), 0.18), (0, 0, 0), conc, bevel=0.02, base=True, name="footing")
    bw, bd = w * 0.9, d * (0.9 if abs(w - d) < 0.1 else 0.58)
    ch = 0.12 * s
    if st.variant == "concrete":
        T = bd
        prof = [(-T / 2, 0), (T / 2, 0), (T / 2, 0.1), (T * 0.24, 0.32), (T * 0.16, H * 0.92), (-T * 0.16, H * 0.92), (-T * 0.24, 0.32), (-T / 2, 0.1)]
        nseg = max(1, int(round(bw / 1.0)))
        for i in range(nseg):
            L = bw / nseg
            x = -bw / 2 + L * (i + 0.5)
            K.prism(prof, L - 0.02, (x, 0, 0.18), conc, rot=(0, 0, math.pi / 2), bevel=0.02, name="jersey")
            K.torus(0.05, 0.012, (x + L / 2 - 0.02, 0, 0.18 + H * 0.92 + 0.0), M.metal("steel", dirt=0.9), rot=(math.pi / 2, 0, 0), segs=16, rsegs=6)
            for sy in (-1, 1):
                K.box((0.06, 0.01, 0.04), (x, sy * (T * 0.2 + 0.006), 0.18 + H * 0.62), M.emissive((1.0, 0.45, 0.05), 2.0), bevel=0.002, rot=(sy * 0.15, 0, 0))
        K.box((0.012, T * 0.5, 0.16), (bw / 2 + 0.006, 0, 0.18 + 0.12), M.hazard(9), bevel=0.002, base=True)
        lamp = Vector((bw * 0.36, 0, 0.18 + H * 0.92))
        KI.status_lamp(lamp, (1.0, 0.08, 0.03), 12.0, r=0.03)
        return Rig(height=0.18 + H + 0.2, frames=1, fps=1,
                   lights=[{"pos": list(lamp + Vector((0, 0, 0.06))), "color": [1.0, 0.1, 0.05], "energy": 0.3, "flicker": False}])
    # body with chamfered top (prism along X, profile in YZ)
    prof = [(-bd / 2, 0), (bd / 2, 0), (bd / 2, H - ch), (bd / 2 - ch, H), (-bd / 2 + ch, H), (-bd / 2, H - ch)]
    body = K.prism([(y, z) for y, z in prof], bw, (0, 0, 0.18), conc, rot=(0, 0, math.pi / 2), bevel=0.015, name="wall")
    # armour plates on -Y and +X faces (and their mirror sides for silhouettes)
    pz0, ph = 0.3, H * 0.62
    for face in ("-y", "+x"):
        if face == "-y":
            K.box((bw * 0.86, 0.03, ph), (0, -bd / 2 - 0.015, 0.18 + pz0), armor, bevel=0.008, base=True, name="plate")
            for zz in (pz0 + 0.06, pz0 + ph - 0.06):
                KI.bolt_row((-bw * 0.38, -bd / 2 - 0.032, 0.18 + zz), (bw * 0.38, -bd / 2 - 0.032, 0.18 + zz), max(3, int(bw / 0.2)), axis="-y", r=0.012)
            K.box((bw * 0.92, 0.012, 0.08), (0, -bd / 2 - 0.006, 0.18 + 0.08), M.hazard(7), bevel=0.002, base=True)
        else:
            K.box((0.03, bd * 0.86, ph), (bw / 2 + 0.015, 0, 0.18 + pz0), armor, bevel=0.008, base=True, name="plate")
            for zz in (pz0 + 0.06, pz0 + ph - 0.06):
                KI.bolt_row((bw / 2 + 0.032, -bd * 0.38, 0.18 + zz), (bw / 2 + 0.032, bd * 0.38, 0.18 + zz), max(3, int(bd / 0.2)), axis="x", r=0.012)
            K.box((0.012, bd * 0.92, 0.08), (bw / 2 + 0.006, 0, 0.18 + 0.08), M.hazard(7), bevel=0.002, base=True)
    # lifting eyes on top
    for x in (-bw * 0.3, bw * 0.3):
        K.torus(0.05, 0.012, (x, 0, 0.18 + H + 0.02), M.metal("steel", dirt=0.8), rot=(math.pi / 2, 0, 0), segs=16, rsegs=6)
    if st.tier <= 2:
        # razor wire coil along the top
        L = bw * 0.95
        n = int(L / 0.035)
        pts = []
        for i in range(n + 1):
            a = TAU * i / 7.0
            x = -L / 2 + L * i / n
            pts.append((x, math.cos(a) * 0.09, 0.18 + H + 0.12 + math.sin(a) * 0.09))
        K.tube(pts, 0.004, M.metal("steel", dirt=0.4, rough=0.3), verts=6)
        for x in (-bw * 0.42, 0.0, bw * 0.42):
            K.box((0.02, 0.02, 0.24), (x, 0, 0.18 + H - 0.02), M.metal("dark_steel"), bevel=0.003, base=True)
    else:
        lm = M.emissive(st.glow_col, 6.0)
        K.box((bw * 0.8, 0.012, 0.025), (0, -bd / 2 + ch * 0.5 - 0.006, 0.18 + H - ch * 0.5), lm, bevel=0.002, rot=(math.radians(45), 0, 0))
        K.box((0.012, bd * 0.8, 0.025), (bw / 2 - ch * 0.5 + 0.006, 0, 0.18 + H - ch * 0.5), lm, bevel=0.002, rot=(0, math.radians(-45), 0))
    lamp = Vector((bw * 0.36, -bd * 0.3, 0.18 + H))
    KI.status_lamp(lamp, (1.0, 0.08, 0.03), 12.0, r=0.03)
    return Rig(height=0.18 + H + 0.25, frames=1, fps=1,
               lights=[{"pos": list(lamp + Vector((0, 0, 0.06))), "color": [1.0, 0.1, 0.05], "energy": 0.3, "flicker": False}])


# =========================================================================== radar
def _reflector(width, height, depth, mat, thick=0.012):
    """Parabolic-cylinder radar reflector, concave toward local +X, centred on the origin."""
    bm = bmesh.new()
    nx, nz = 16, 6
    rows = []
    for j in range(nz + 1):
        z = -height / 2 + height * j / nz
        row = []
        for i in range(nx + 1):
            y = -width / 2 + width * i / nx
            x = -depth * (1 - (2 * y / width) ** 2) * (1 - 0.25 * (2 * z / height) ** 2)
            row.append(bm.verts.new((x, y, z)))
        rows.append(row)
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    o = KI.mesh_obj("reflector", bm, mat, (0, 0, 0), (0, 0, 0), 0, smooth=60)
    sm = o.modifiers.new("solid", "SOLIDIFY")
    sm.thickness = thick
    return o


def radar(spec, p):
    """Surveillance radar: lattice tower with a railed platform carrying a rotating
    parabolic-cylinder antenna (feed horn arm, back truss), equipment shelter with an A/C unit."""
    KI.begin()
    st = KI.Style(p, alt=p.get("tier", 1) in (2, 3))
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.8
    frame = st.frame()
    body = st.body()
    KI.concrete_pad(w * 0.97, d * 0.97, 0.08, st.concrete(0.5))
    z0 = 0.08
    T = Vector((-0.1 * w, 0.12 * d, z0))
    Ht = 0.9 + 0.75 * s
    tw = 0.42 * s
    tm = st.mat((0.6, 0.61, 0.6), name="tower_galv", wear=0.6) if st.tier >= 2 else frame
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.18 * k, 0.18 * k, 0.12), T + Vector((sx * tw / 2, sy * tw / 2, 0)), M.concrete(0.8), bevel=0.01, base=True)
    KI.lattice(T + Vector((0, 0, 0.12)), Ht - 0.12, tw, tw * 0.7, mat=tm, leg_r=0.025 * k, brace_r=0.01 * k, bay=0.45 * k)
    zp = z0 + Ht
    K.box((tw * 0.7 + 0.3, tw * 0.7 + 0.3, 0.04), T + Vector((0, 0, Ht)), M.tread_plate(1.2), bevel=0.006, base=True)
    hw = (tw * 0.7 + 0.3) / 2
    K.railing([T + Vector((-hw, -hw, Ht + 0.04)), T + Vector((hw, -hw, Ht + 0.04)), T + Vector((hw, hw, Ht + 0.04))], 0.5, st.safety())
    KI.ladder(T + Vector((0, -tw / 2 - 0.05, 0.12)), Ht - 0.1, w=0.3, mat=tm)
    K.cyl(0.12 * k, 0.22 * k, T + Vector((0, 0, Ht + 0.04)), body, verts=24, name="pedestal")
    # rotating antenna
    ant = []
    za = zp + 0.04 + 0.22 * k
    ant.append(K.cyl(0.13 * k, 0.08 * k, (T.x, T.y, za), M.metal("dark_steel"), verts=24, name="rotary_joint"))
    aw, ah = 1.2 * k, 0.5 * k
    ac = Vector((T.x, T.y, za + 0.08 * k + ah / 2 + 0.05))
    if st.variant == "phased":
        # back-to-back flat phased-array faces, tilted 15 deg, on a rotating drum
        pm = st.mat((0.55, 0.56, 0.55) if st.tier < 4 else (0.75, 0.76, 0.77), name="array_face", rust=0.0, wear=0.4)
        tile = M.plastic((0.05, 0.06, 0.07), 0.35, name="array_tiles")
        for sgn in (-1, 1):
            # each face + its tiles tilt back together about the face centre (A-frame, faces look up)
            fc = ac + Vector((sgn * 0.14 * k, 0, 0.05 * k))
            grp = [K.box((0.06 * k, aw, ah * 1.5), fc, pm, bevel=0.01, name="array")]
            for i in range(5):
                for j in range(3):
                    grp.append(K.box((0.012, aw / 5 * 0.88, ah * 1.5 / 3 * 0.86),
                                     fc + Vector((sgn * 0.036 * k, -aw / 2 + aw * (i + 0.5) / 5, -ah * 0.75 + ah * 1.5 * (j + 0.5) / 3)),
                                     tile, bevel=0.002))
            fp = KI.pivot(fc, name="array_face", children=grp)
            fp.rotation_euler = (0, -sgn * math.radians(15), 0)
            ant.append(fp)
        ant.append(K.cyl(0.16 * k, ah * 0.6, (T.x, T.y, za + 0.08 * k), body, verts=24, name="drum"))
    else:
        refl_m = M.metal("aluminum", rough=0.3, dirt=0.3) if st.tier < 4 else st.mat((0.75, 0.76, 0.77), name="refl_white")
        r = _reflector(aw, ah, 0.16 * k, refl_m)
        r.location = ac + Vector((0.06 * k, 0, 0))
        ant.append(r)
        for i in range(5):  # back ribs
            y = -aw / 2 + aw * (i + 0.5) / 5
            ant.append(KI.strut(ac + Vector((0.06 * k - 0.16 * k * (1 - (2 * y / aw) ** 2), y, -ah / 2)), ac + Vector((0.06 * k - 0.16 * k * (1 - (2 * y / aw) ** 2), y, ah / 2)), 0.008, tm, verts=6))
        ant.append(KI.strut(ac + Vector((-0.12 * k, -aw * 0.4, 0)), ac + Vector((-0.12 * k, aw * 0.4, 0)), 0.02 * k, tm, verts=8))
        ant.append(KI.strut((T.x, T.y, za + 0.08 * k), ac + Vector((-0.12 * k, 0, 0)), 0.04 * k, body, verts=12))
        feed = ac + Vector((0.45 * k, 0, -0.05 * k))
        for sy in (-1, 1):
            ant.append(KI.strut(ac + Vector((-0.02 * k, sy * aw * 0.3, -ah * 0.35)), feed, 0.01 * k, tm, verts=6))
        ant.append(K.box((0.1 * k, 0.16 * k, 0.08 * k), feed, body, bevel=0.008, name="feed_horn"))
        ant.append(K.box((0.2 * k, 0.12 * k, 0.12 * k), ac + Vector((-0.2 * k, 0, -ah * 0.2)), M.metal("dark_steel"), bevel=0.01, name="counterweight"))
    ap = KI.pivot((T.x, T.y, 0), children=ant)
    an.spin(ap, 1.0)
    _, bs = KI.status_lamp(T + Vector((hw - 0.05, hw - 0.05, Ht + 0.04)), (1.0, 0.08, 0.03), 12.0)
    an.value(bs, lambda t: 1.0 + 14.0 * KI.blink(t, 2, 0.2))
    # equipment shelter front-right with A/C fan
    sx0, sx1 = 0.04 * w, 0.46 * w
    sy0, sy1 = -0.46 * d, -0.1 * d
    sh = 0.7 + 0.15 * s
    sc = Vector(((sx0 + sx1) / 2, (sy0 + sy1) / 2, z0))
    shm = st.mat((0.62, 0.63, 0.6) if st.tier != 1 else (0.2, 0.22, 0.14), name="shelter", wear=0.7)
    K.box((sx1 - sx0, sy1 - sy0, sh), sc, shm, bevel=0.02, base=True, name="shelter")
    K.box((sx1 - sx0 + 0.04, sy1 - sy0 + 0.04, 0.05), sc + Vector((0, 0, sh)), shm, bevel=0.01, base=True)
    K.box((0.34, 0.03, sh * 0.8), (sc.x - (sx1 - sx0) * 0.2, sy0 - 0.012, z0), M.painted((0.5, 0.5, 0.48), name="door"), bevel=0.008, base=True)
    K.box((0.03, 0.03, 0.08), (sc.x - (sx1 - sx0) * 0.2 + 0.12, sy0 - 0.03, z0 + sh * 0.45), M.metal("chrome"), bevel=0.003)
    ac_c = Vector((sx1 + 0.12, sc.y, z0 + sh * 0.45))
    K.box((0.22, (sy1 - sy0) * 0.6, sh * 0.5), ac_c, M.painted((0.7, 0.7, 0.68), wear=0.4, name="ac_unit"), bevel=0.012)
    fo, rot = K.fan(ac_c + Vector((0.115, 0, 0)), r=min(0.13, (sy1 - sy0) * 0.22), axis="x", blades=5)
    an.spin(rot, 3.0 / 5.0)
    KI.plate_sign((sc.x + (sx1 - sx0) * 0.2, sy0 - 0.006, z0 + sh * 0.65), 0.2, 0.12, "-y", color=(0.8, 0.6, 0.03))
    KI.cable([(sc.x - (sx1 - sx0) * 0.4, sy1, z0 + sh * 0.8), (sc.x - (sx1 - sx0) * 0.4, sy1 + 0.1, z0 + sh * 0.8), (T.x + tw / 2, T.y - tw / 2, z0 + 0.6)], 0.016)
    return Rig(height=ac.z + ah / 2 + 0.15, frames=16, fps=10, update=an,
               lights=[{"pos": list(T + Vector((hw, hw, Ht + 0.1))), "color": [1.0, 0.1, 0.05], "energy": 0.3, "flicker": True}])


# =========================================================================== shield generator
def shield_generator(spec, p):
    """Field projector: octagonal stepped plinth, central emitter column with a glowing core held
    in two counter-rotating gimbal rings, four capacitor stacks with chase-lit caps, radiator
    banks and heavy power cables."""
    KI.begin()
    st = KI.Style(p)
    an = KI.Anim()
    w, d = _size(spec)
    s = min(w, d)
    k = s ** 0.85
    frame = st.frame()
    body = st.body()
    dark = st.accent_mat() if st.tier >= 3 else frame
    glow = st.glow_col if (st.tier >= 3 or p.get("glow")) else (0.25, 0.7, 1.0)
    conc = st.concrete(0.5)
    K.cyl(0.49 * s / math.cos(math.pi / 8), 0.12, (0, 0, 0), conc, verts=8, bevel=0.02, rot=(0, 0, math.pi / 8))
    K.cyl(0.38 * s / math.cos(math.pi / 8), 0.12, (0, 0, 0.12), conc, verts=8, bevel=0.02, rot=(0, 0, math.pi / 8))
    z0 = 0.24
    C = Vector((-0.02 * s, 0.02 * s, z0))
    # emitter column
    K.cyl(0.2 * k, 0.12, C, dark, verts=8, bevel=0.012, rot=(0, 0, math.pi / 8))
    col_h = 0.7 + 0.25 * s
    K.cyl(0.15 * k, col_h, C + Vector((0, 0, 0.12)), body, verts=24, r2=0.09 * k, name="column")
    for i in range(4):
        K.torus(0.15 * k - i * 0.015 * k, 0.012 * k, C + Vector((0, 0, 0.12 + col_h * (0.2 + 0.18 * i))), M.metal("copper", dirt=0.4), segs=32)
    zc = C.z + 0.12 + col_h + 0.32 * k
    K.cyl(0.07 * k, 0.12 * k, C + Vector((0, 0, 0.12 + col_h)), dark, verts=24)
    core_m, core_s = KI.anim_emit(glow, 12.0, "core", base=(0.3, 0.6, 0.8))
    K.sphere(0.13 * k, (C.x, C.y, zc), core_m, segs=32, rings=16)
    halo_m, halo_s = KI.soft_glow(glow, 4.0, rim=False, name="halo", power=2.0)
    K.sphere(0.2 * k, (C.x, C.y, zc), halo_m, segs=32, rings=16)
    # gimbal rings
    rm = M.metal("chrome", rough=0.15) if st.tier >= 3 else M.metal("steel", rough=0.3)
    outer = [KI.ring(0.36 * k, 0.32 * k, 0.05 * k, (C.x, C.y, zc), rm, rot=(math.pi / 2, 0, 0), segs=64)]
    for a in (0, math.pi):
        outer.append(K.cyl(0.03 * k, 0.06 * k, (C.x + math.cos(a) * 0.34 * k, C.y, zc), dark, rot=K.AXES["x"], verts=12, base=False))
    for i in range(6):
        a = TAU * i / 6
        m_, _s = KI.anim_emit(glow, 6.0, "ring_led")
        outer.append(K.box((0.03 * k, 0.055 * k, 0.03 * k), (C.x + math.cos(a) * 0.34 * k, C.y, zc + math.sin(a) * 0.34 * k), m_, bevel=0.003))
    inner = [KI.ring(0.27 * k, 0.24 * k, 0.04 * k, (C.x, C.y, zc), rm, rot=(0, math.pi / 2, 0), segs=64)]
    for a in (math.pi / 2, -math.pi / 2):
        inner.append(K.cyl(0.025 * k, 0.05 * k, (C.x, C.y + math.sin(a) * 0.255 * k, zc), dark, rot=K.AXES["y"], verts=12, base=False))
    op = KI.pivot((C.x, C.y, zc), children=outer)
    ip = KI.pivot((C.x, C.y, zc), children=inner)
    an.spin(op, 0.5, axis="Z")
    an.spin(ip, -0.5, axis="Z")
    an.add(lambda t: setattr(ip, "rotation_euler", (0.35 * math.sin(TAU * t), 0, -math.pi * t)))
    an.value(core_s, lambda t: 9.0 + 6.0 * (0.5 + 0.5 * math.sin(TAU * 2 * t)))
    an.value(halo_s, lambda t: 2.5 + 2.0 * (0.5 + 0.5 * math.sin(TAU * 2 * t)))
    # support arms from column top to the outer ring pivots
    for a in (0, math.pi):
        KI.strut(C + Vector((math.cos(a) * 0.06 * k, 0, 0.12 + col_h)), Vector((C.x + math.cos(a) * 0.41 * k, C.y, zc - 0.1 * k)), 0.022 * k, dark, verts=8)
        KI.strut(Vector((C.x + math.cos(a) * 0.41 * k, C.y, zc - 0.1 * k)), Vector((C.x + math.cos(a) * 0.4 * k, C.y, zc)), 0.022 * k, dark, verts=8)
    # capacitor stacks at four diagonal positions
    caps = []
    ins = M.plastic((0.85, 0.85, 0.82), 0.3, name="insulator") if st.tier >= 3 else M.plastic((0.32, 0.12, 0.05), 0.25, name="porcelain")
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        cp = C + Vector((math.cos(a) * 0.36 * s, math.sin(a) * 0.36 * s, 0))
        K.box((0.24 * k, 0.24 * k, 0.3 * k), cp, body, bevel=0.015, base=True, name="cap_base")
        for j in range(5):
            K.cyl(0.07 * k, 0.05 * k, cp + Vector((0, 0, 0.3 * k + j * 0.065 * k)), ins, verts=20, bevel=0.006)
            K.cyl(0.09 * k, 0.012, cp + Vector((0, 0, 0.3 * k + j * 0.065 * k + 0.05 * k)), ins, verts=20, bevel=0.003)
        m_, sk = KI.anim_emit(glow, 6.0, "cap_glow")
        K.sphere(0.06 * k, cp + Vector((0, 0, 0.3 * k + 0.36 * k)), m_, segs=16, rings=8)
        K.torus(0.075 * k, 0.015 * k, cp + Vector((0, 0, 0.3 * k + 0.33 * k)), M.metal("copper"))
        caps.append((i, sk))
        KI.cable(KI.sag(cp + Vector((0, 0, 0.15 * k)), C + Vector((0, 0, 0.1)), 0.0, 5), 0.03 * k)

    def chase(t):
        for i, sk in caps:
            ph = (t * 2 - i / 4.0) % 1.0
            sk.default_value = 2.0 + 14.0 * max(0.0, 1.0 - ph * 3)
    an.add(chase)
    # radiator banks on two sides
    for sx, sy, along_x in ((0.0, 0.4, True), (-0.4, 0.0, False)):
        rc = C + Vector((sx * s, sy * s, 0))
        K.box((0.42 * k if along_x else 0.14 * k, 0.14 * k if along_x else 0.42 * k, 0.06), rc, dark, bevel=0.008, base=True)
        for j in range(9):
            off = (j - 4) * 0.045 * k
            K.box((0.012 if along_x else 0.12 * k, 0.12 * k if along_x else 0.012, 0.34 * k), rc + Vector((off if along_x else 0, 0 if along_x else off, 0.06)),
                  M.metal("aluminum", dirt=0.3), bevel=0.002, base=True)
        K.box((0.44 * k if along_x else 0.03, 0.03 if along_x else 0.44 * k, 0.03), rc + Vector((0, 0, 0.06 + 0.34 * k)), dark, bevel=0.004, base=True)
    _, ls = KI.status_lamp((0.3 * s, -0.3 * s, 0.24), (0.1, 1.0, 0.3), 10.0, r=0.03)
    KI.cabinet((0.14 * s, -0.36 * s, 0.24), 0.0, w=0.3 * k, d=0.14, h=0.45 * k, mat=dark, screen_col=glow)
    light = KI.point_light((C.x, C.y, zc), glow, 40.0 * k, 0.15)
    an.energy(light, lambda t: 40.0 * k * (0.7 + 0.3 * math.sin(TAU * 2 * t)))
    return Rig(height=zc + 0.4 * k, frames=16, fps=12, update=an,
               lights=[{"pos": [C.x, C.y, zc], "color": list(glow), "energy": 2.0, "flicker": True}])


ARCHETYPES = KI.with_bounds({"turret": turret, "wall_segment": wall_segment, "radar": radar, "shield_generator": shield_generator})
