"""Assembly & fabrication archetypes: assembler, precision_assembler, electronics_fab,
nanofab, munitions_plant."""
import math

from mathutils import Vector as V

import kit as K
import kit_plant as KP
import materials as M


def _clamp(x, a, b):
    return max(a, min(b, x))


# --------------------------------------------------------------------------- assembler
def assembler(spec, params):
    """Robot work cell: two 6-axis arms transfer parts from an infeed conveyor to a rotary
    indexing table; control module + magazine at the back."""
    P = KP.Plant(spec, params, "machine")
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.3, 0.55, 1.5)
    if st.tier >= 2:
        KP.floor_markings(P, L * 0.9, S * 0.9, z0)

    # ---- back module (control + parts magazine), tall parts at the back (+Y)
    bh = (1.3 + 0.12 * st.tier) * s + 0.25
    bd = _clamp(S * 0.2, 0.45, 1.2)
    by = S / 2 - bd / 2 - 0.08
    bw = L * 0.68
    bx = -L * 0.12
    KP.housing(P, (bw, bd, bh), (bx, by, z0))
    # inspection windows into the module (lit)
    wm, _ = KP.window_mat((1.0, 0.9, 0.75) if st.tier < 4 else st.glow, 0.5)
    nwin = max(1, int(bw / 1.0))
    for i in range(nwin):
        x = bx - bw / 2 + bw * (i + 0.5) / nwin
        K.box((min(0.6, bw / nwin * 0.6), 0.02, bh * 0.28), (x, by - bd / 2 - 0.01, z0 + bh * 0.55), wm, bevel=0.006)
        K.box((min(0.6, bw / nwin * 0.6) + 0.06, 0.012, bh * 0.28 + 0.06), (x, by - bd / 2 - 0.004, z0 + bh * 0.55), st.dark, bevel=0.008)
    KP.louvre((bx + bw * 0.3, by - bd / 2 - 0.012, z0 + bh * 0.2), 0.0, 0.42 * s, 0.26 * s)
    KP.sign((bx - bw * 0.3, by - bd / 2 - 0.006, z0 + bh * 0.25), 0.0, "warn", 0.15)
    KP.sign((bx, by - bd / 2 - 0.006, z0 + bh * 0.24), 0.0, "plate", 0.12)
    KP.stack_light(P, (bx + bw / 2 - 0.15, by, z0 + bh + 0.05), anim="run")
    # roof: duct + cable tray
    K.box((bw * 0.5, bd * 0.5, 0.18), (bx - bw * 0.15, by, z0 + bh + 0.05), st.frame, bevel=0.01, base=True)
    fan_objs, rotor = K.fan((bx - bw * 0.15, by, z0 + bh + 0.24), r=min(0.2, bd * 0.3), axis="z", blades=5)
    P.anim.spin(rotor, turns=2 / 5)
    # side cabinet on the +X end of the module
    KP.cabinet(P, (bx + bw / 2 + 0.33 * s + 0.06, by + 0.05, z0), 0.0, w=0.6 * s, d=0.35 * s, h=1.35 * s + 0.2)

    # ---- parts magazine (vertical bin stack) at the back-left corner
    mx, my = -L / 2 + 0.35 * s + 0.08, by - bd / 2 - 0.3 * s
    K.box((0.55 * s, 0.45 * s, 0.9 * s), (mx, my, z0), st.accent_m, bevel=0.015, base=True)
    for k in range(3):
        K.box((0.5 * s, 0.4 * s, 0.035), (mx, my - 0.04, z0 + 0.95 * s + k * 0.17 * s), st.frame, bevel=0.006, base=True)
        K.box((0.42 * s, 0.32 * s, 0.13 * s), (mx, my - 0.04, z0 + 0.985 * s + k * 0.17 * s), M.plastic((0.04, 0.15, 0.4) if k % 2 else (0.6, 0.35, 0.02), 0.5), bevel=0.01, base=True)

    # ---- infeed conveyor across the cell
    cz = z0 + 0.72 * s + 0.1
    cy = by - bd / 2 - 0.35 * s - 0.05
    cy = min(cy, S * 0.18)
    cx0, cx1 = -L / 2 + 0.06, L / 2 - 0.06
    part_m = st.metal("aluminum")

    def part():
        return [K.box((0.16 * s, 0.13 * s, 0.07 * s), (0, 0, 0), part_m, bevel=0.01, base=True),
                K.cyl(0.035 * s, 0.05 * s, (0.02 * s, 0, 0.07 * s), M.metal("steel"), verts=16)]
    KP.conveyor(P, cx0, cx1, cy, cz, width=0.34 * s, items=part, item_spacing=0.55 * s)
    # tunnels hide wrap-around at both ends
    tl = _clamp(L * 0.12, 0.35, 0.8)
    for sx in (-1, 1):
        x = sx * (L / 2 - tl / 2 - 0.04)
        K.box((tl, 0.5 * s, 0.32 * s), (x, cy, cz - 0.02), st.body if st.tier != 1 else st.accent_m, bevel=0.012, base=True, name="tunnel")
        K.box((0.02, 0.36 * s, 0.2 * s), (x - sx * tl / 2, cy, cz), M.rubber(), bevel=0.003, base=True)

    # ---- rotary indexing table at the front centre
    ty = -S * 0.22
    tz = z0 + 0.62 * s
    tr = 0.3 * s
    K.cyl(0.2 * s, tz - z0, (0, ty, z0), st.frame, verts=32)
    K.box((0.5 * s, 0.5 * s, 0.06), (0, ty, z0), st.dark, bevel=0.008, base=True)
    table = K.pivot("table", (0, ty, tz))
    tparts = [K.cyl(tr + 0.08 * s, 0.06 * s, (0, 0, 0), M.metal("steel"), verts=48, bevel=0.006)]
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p = V((math.cos(a) * tr, math.sin(a) * tr, 0.06 * s))
        tparts.append(K.box((0.2 * s, 0.17 * s, 0.04 * s), p, st.accent_m if st.tier != 2 else st.dark, rot=(0, 0, a), bevel=0.006, base=True))
        tparts.append(K.box((0.15 * s, 0.12 * s, 0.07 * s), p + V((0, 0, 0.04 * s)), part_m, rot=(0, 0, a), bevel=0.01, base=True))
        tparts.append(K.cyl(0.04 * s, 0.05 * s, p + V((0, 0, 0.11 * s)), M.metal("brass"), verts=16))
    KP.parent(tparts, table)
    P.anim.add(lambda t: setattr(table.rotation_euler, "z", math.pi / 4 + math.pi / 2 * KP.smooth01((t - 0.38) / 0.3)))

    # ---- two robots on pedestals, out of phase
    for i, sx in enumerate((-1, 1)):
        rx = sx * _clamp(L * 0.27, 0.6, L / 2 - 0.4 * s)
        ry = (cy + ty) / 2 - 0.05
        ph = 0.2 * s
        K.box((0.36 * s, 0.36 * s, ph), (rx, ry, z0), st.dark, bevel=0.012, base=True)
        K.box((0.42 * s, 0.42 * s, 0.03), (rx, ry, z0), st.frame, bevel=0.006, base=True)
        rb = KP.RobotArm(P, (rx, ry, z0 + ph), s=s * 0.95)
        base = V((rx, ry, z0 + ph))
        pick = V((rx - sx * 0.05, cy, cz + 0.07 * s)) - base
        place = V((sx * tr * 0.72, ty - 0.0, tz + 0.17 * s)) - base
        up = V((0, 0, 0.25 * s))
        rb.animate(P, [pick + up, pick, pick, pick + up, place + up, place, place, place + up],
                   grips=[0, 0, 1, 1, 1, 1, 0, 0], phase=0.5 * i)
        # carried part (visible while gripped)
        carried = K.box((0.12 * s, 0.1 * s, 0.06 * s), (0, 0, -0.2 * s), part_m, bevel=0.008)
        KP.parent([carried], rb.tool)

        def vis(t, o=carried, ph_=0.5 * i):
            u = ((t + ph_) % 1.0) * 8
            o.hide_render = not (2.0 <= u <= 6.0)
        vis(0.0)
        P.anim.add(vis)
        # floor cable from module to robot
        KP.cable((rx + 0.1, by - bd / 2, z0 + 0.03), (rx, ry + 0.2 * s, z0 + 0.03), sag=0.0, r=0.022)

    # ---- front details: HMI, light-curtain posts
    KP.hmi_panel(P, (L / 2 - 0.25, -S * 0.02, z0), math.pi / 2, z=1.05 * s + 0.1)
    # parts bins on the floor at the front-left
    for k in range(2):
        K.box((0.42 * s, 0.32 * s, 0.24 * s), (-L / 2 + 0.35 * s + k * 0.47 * s, -S / 2 + 0.3 * s, z0),
              M.plastic((0.04, 0.15, 0.4) if k else (0.6, 0.35, 0.02), 0.55), bevel=0.015, base=True)
    if st.tier == 1:
        K.scatter_debris(L * 0.9, S * 0.9, 10, seed=4)
    if st.hi:
        KP.led_strip((bx - bw / 2, by - bd / 2 - 0.02, z0 + bh - 0.06), (bx + bw / 2, by - bd / 2 - 0.02, z0 + bh - 0.06), st.glow, 6.0)
    P.export_light((0, -S * 0.1, z0 + 1.2), st.glow, 0.4)
    return P.finish(z0 + bh + 0.5, frames=16, fps=12)




# --------------------------------------------------------------------------- precision assembler
def precision_assembler(spec, params):
    """Guarded precision cell on a machine bed: XY gantry pick-and-place + SCARA arm behind
    clear panels, fan-filter unit on top."""
    P = KP.Plant(spec, params, "machine", palette={
        2: ((0.55, 0.56, 0.54), (0.75, 0.42, 0.02), (0.25, 1.0, 0.35)),
        3: ((0.6, 0.62, 0.63), (0.03, 0.09, 0.24), (0.25, 0.75, 1.0))}, wear=0.6)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.0, 0.55, 1.5)
    x0, x1 = -L * 0.44, L * 0.4
    y0, y1 = -S * 0.36, S * 0.34
    bh = 0.85 * s + 0.1
    KP.machine_bed(P, x0, x1, y0, y1, bh, mat=st.body if st.tier != 2 else st.light_grey, z=z0)
    zt = z0 + bh
    K.box((x1 - x0 - 0.06, y1 - y0 - 0.06, 0.03), ((x0 + x1) / 2, (y0 + y1) / 2, zt), st.metal("stainless"), bevel=0.004, base=True)
    zt += 0.03
    eh = 0.95 * s + 0.25
    KP.enclosure(P, x0 + 0.02, x1 - 0.02, y0 + 0.02, y1 - 0.02, zt, zt + eh, top="ffu" if st.tier >= 3 else "frame")
    # --- gantry over left 60 %
    gx0, gx1 = x0 + 0.12, x0 + (x1 - x0) * 0.58
    gy0, gy1 = y0 + 0.14, y1 - 0.14
    gz = 0.62 * s
    objs, bridge, car, zp = KP.gantry(P, gx0, gx1, gy0, gy1, gz, mat=st.dark)
    g = KP.group(objs + [bridge], (0, 0, zt), name="gantry")
    # feeder trays at the back, fixture nest at front
    for i in range(4):
        x = gx0 + 0.15 + (gx1 - gx0 - 0.3) * i / 3
        K.box((0.16 * s, 0.22 * s, 0.03), (x, gy1 - 0.15, zt), M.plastic((0.02, 0.02, 0.025), 0.4), bevel=0.003, base=True)
        for k in range(3):
            K.box((0.03 * s, 0.03 * s, 0.015), (x - 0.04 * s + k * 0.04 * s, gy1 - 0.15, zt + 0.03), M.metal("gold"), bevel=0.002, base=True)
    nest_x, nest_y = (gx0 + gx1) / 2, gy0 + 0.25
    K.box((0.32 * s, 0.24 * s, 0.08), (nest_x, nest_y, zt), M.metal("aluminum"), bevel=0.006, base=True)
    K.box((0.22 * s, 0.16 * s, 0.02), (nest_x, nest_y, zt + 0.08), M.plastic((0.03, 0.2, 0.06), 0.35), bevel=0.002, base=True)
    bx_c = (gx0 + gx1) / 2
    gw = (gx1 - gx0) / 2 - 0.2
    ys = gy1 - 0.15 - (gy0 + gy1) / 2
    yf = nest_y - (gy0 + gy1) / 2

    def gfn(t):
        u = (t * 2) % 1.0
        # 0-0.15 dip at feeder, 0.15-0.5 travel, 0.5-0.65 dip at nest, 0.65-1 travel back
        if u < 0.15:
            y, x, dz = ys, -gw * 0.6, -0.12 * math.sin(math.pi * u / 0.15)
        elif u < 0.5:
            e = KP.smooth01((u - 0.15) / 0.35)
            y, x, dz = KP.lerp(ys, yf, e), KP.lerp(-gw * 0.6, gw * 0.2, e), 0.0
        elif u < 0.65:
            y, x, dz = yf, gw * 0.2, -0.12 * math.sin(math.pi * (u - 0.5) / 0.15)
        else:
            e = KP.smooth01((u - 0.65) / 0.35)
            y, x, dz = KP.lerp(yf, ys, e), KP.lerp(gw * 0.2, -gw * 0.6, e), 0.0
        bridge.location.y = (gy0 + gy1) / 2 + y
        car.location.x = x
        zp.location.z = dz
    gfn(0.0)
    P.anim.add(gfn)
    # --- SCARA in the right part
    sx_ = x0 + (x1 - x0) * 0.8
    j1, j2, quill = KP.scara(P, (sx_, (y0 + y1) / 2 + 0.05, zt), s=s * 0.85, rot_z=math.pi)
    K.box((0.26 * s, 0.2 * s, 0.07), (sx_ - 0.05, y0 + 0.2, zt), M.metal("aluminum"), bevel=0.006, base=True)
    K.cyl(0.09 * s, 0.05, (sx_ + 0.12, y1 - 0.25, zt), M.plastic((0.6, 0.35, 0.02), 0.5), verts=24)
    P.anim.add(lambda t: (setattr(j1.rotation_euler, "z", -0.7 + 1.1 * KP.wave(t, 2)),
                          setattr(j2.rotation_euler, "z", 1.2 - 1.6 * KP.wave(t, 2, 0.1)),
                          setattr(quill.location, "z", -0.06 * KP.wave(t, 4))))
    # --- exterior details
    KP.stack_light(P, (x1 - 0.1, y0 + 0.1, zt + eh + (0.22 if st.tier >= 3 else 0.02)), anim="run")
    KP.hmi_panel(P, (x1 + 0.05, (y0 + y1) / 2 - 0.2, z0), math.pi / 2, z=1.25 * s + 0.15)
    KP.cabinet(P, (L / 2 - 0.2, y1 - 0.1, z0), math.pi / 2, w=0.5 * s, d=0.3, h=1.1 * s + 0.2)
    KP.sign(((x0 + x1) / 2 - 0.3, y0 - 0.005, z0 + bh * 0.75), 0.0, "plate", 0.12)
    KP.sign((x0 + 0.3, y0 - 0.005, z0 + bh * 0.75), 0.0, "warn", 0.12)
    if st.hi:
        KP.led_strip((x0, y0 - 0.02, zt - 0.05), (x1, y0 - 0.02, zt - 0.05), st.glow, 6.0)
        KP.led_strip((x1 + 0.02, y0, zt - 0.05), (x1 + 0.02, y1, zt - 0.05), st.glow, 6.0)
    # interior work light
    P.point_light(((x0 + x1) / 2, (y0 + y1) / 2, zt + eh - 0.1), (1.0, 0.97, 0.92), 25.0 * s, radius=0.3, export=0.3)
    return P.finish(zt + eh + 0.45, frames=16, fps=12)


# --------------------------------------------------------------------------- electronics fab
def electronics_fab(spec, params):
    """SMT line along the long side: magazine loader -> stencil printer -> pick-and-place
    (gantry heads under a clear hood, feeder bank) -> reflow oven (glowing zones) -> unloader."""
    P = KP.Plant(spec, params, "machine", palette={
        1: ((0.3, 0.29, 0.25), (0.06, 0.07, 0.06), (1.0, 0.55, 0.15)),
        2: ((0.55, 0.56, 0.54), (0.06, 0.065, 0.07), (0.3, 1.0, 0.4)),
        3: ((0.62, 0.64, 0.65), (0.03, 0.09, 0.24), (0.25, 0.75, 1.0))}, wear=0.45)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    s = _clamp(S / 3.0, 0.55, 1.4)
    if st.tier >= 2:
        KP.floor_markings(P, L * 0.92, S * 0.9, z0)
    cy = -S * 0.05
    cz = z0 + 0.9 * s
    D = _clamp(S * 0.55, 0.9, 2.2)          # module depth
    xa, xb = -L / 2 + 0.08, L / 2 - 0.08
    span = xb - xa
    # section boundaries (fractions of span)
    fr = [0.0, 0.13, 0.3, 0.62, 0.92, 1.0]
    X = [xa + span * f for f in fr]
    pcb_m = M.plastic((0.02, 0.18, 0.05), 0.35)

    def pcb():
        o = [K.box((0.28 * s, 0.2 * s, 0.012), (0, 0, 0), pcb_m, bevel=0.002, base=True)]
        for k in range(3):
            o.append(K.box((0.04 * s, 0.04 * s, 0.012), (-0.08 * s + k * 0.08 * s, 0.03 * s, 0.012), M.plastic((0.02, 0.02, 0.02), 0.3), bevel=0.002, base=True))
        return o
    KP.conveyor(P, xa + 0.1, xb - 0.1, cy, cz, width=0.24 * s, items=pcb, item_spacing=0.5 * s, legs=False)
    body = st.body
    trim = st.paint_m(tuple(c * 0.75 for c in st.paint), 0.8, name="lid_paint")
    stripe = st.accent_m

    def module(x0, x1, h, name):
        w = x1 - x0 - 0.04
        xc = (x0 + x1) / 2
        KP.machine_bed(P, xc - w / 2, xc + w / 2, cy - D / 2, cy + D / 2, cz - z0 - 0.06, mat=body, doors=True, z=z0)
        return xc, w

    # 1 loader: magazine rack
    xc, w = module(X[0], X[1], 0, "loader")
    K.box((w * 0.9, D * 0.7, 0.75 * s), (xc, cy, cz - 0.06), body, bevel=0.015, base=True)
    K.box((w * 0.7, 0.02, 0.5 * s), (xc, cy - D * 0.35 - 0.01, cz + 0.05), M.metal("aluminum"), bevel=0.004, base=True)
    for k in range(8):
        K.box((w * 0.66, 0.025, 0.008), (xc, cy - D * 0.35 - 0.02, cz + 0.08 + k * 0.055 * s), M.metal("dark_steel"), bevel=0, base=True)
    # 2 stencil printer: closed body with smoked window and squeegee carriage
    xc, w = module(X[1], X[2], 0, "printer")
    ph = 0.55 * s
    K.box((w, D, ph), (xc, cy, cz - 0.06), body, bevel=0.02, base=True)
    K.box((w * 0.92, D * 0.86, 0.12), (xc, cy, cz - 0.06 + ph), trim, bevel=0.03, base=True)
    K.box((w + 0.004, 0.03, 0.05), (xc, cy - D / 2, cz - 0.06 + ph - 0.08), stripe, bevel=0.004)
    sw, _ = KP.window_mat((0.9, 0.95, 1.0), 0.25)
    K.box((w * 0.7, 0.02, ph * 0.5), (xc, cy - D / 2 - 0.01, cz + ph * 0.2), sw, bevel=0.01)
    KP.status_leds(P, (xc + w * 0.3, cy - D / 2 - 0.012, cz - 0.15), n=3, seed=2)
    # 3 pick-and-place: hood with clear top, feeder bank on -Y side, gantry heads inside
    xc, w = module(X[2], X[3], 0, "pnp")
    hh = 0.6 * s
    for sx in (-1, 1):
        K.box((0.08, D, hh), (xc + sx * (w / 2 - 0.04), cy, cz - 0.06), body, bevel=0.015, base=True)
    K.box((w, 0.08, hh), (xc, cy + D / 2 - 0.04, cz - 0.06), body, bevel=0.015, base=True)
    K.box((w, D, 0.06), (xc, cy, cz - 0.06 + hh), trim, bevel=0.015, base=True)
    gl = KP.clear_panel()
    K.box((w - 0.16, 0.01, hh - 0.08), (xc, cy - D / 2 + 0.02, cz - 0.02), gl, bevel=0, base=True)
    K.box((w - 0.16, 0.01, 0.06), (xc, cy - D / 2 + 0.02, cz - 0.06 + hh - 0.06), M.metal("aluminum"), bevel=0.003, base=True)
    # feeder bank (reels) on the -Y face, below the hood
    nf = max(4, int(w / 0.09))
    for i in range(nf):
        x = xc - w * 0.42 + w * 0.84 * i / (nf - 1)
        col = [(0.03, 0.03, 0.035), (0.6, 0.6, 0.6), (0.03, 0.1, 0.3)][i % 3]
        K.cyl(0.13 * s, 0.018, (x, cy - D / 2 - 0.12 * s, cz - 0.28 * s), M.plastic(col, 0.35), rot=K.AXES["x"], verts=28, base=False, bevel=0.002)
        K.box((0.025, 0.3 * s, 0.05), (x, cy - D / 2 + 0.02, cz - 0.1), M.metal("aluminum"), bevel=0.003, base=False)
    K.box((w * 0.9, 0.06, 0.04), (xc, cy - D / 2 - 0.1 * s, cz - 0.48 * s), st.dark, bevel=0.004)
    # gantry heads (two) inside the hood
    gz = cz + hh * 0.55
    rail = M.metal("stainless")
    for sy in (-1, 1):
        K.box((w - 0.2, 0.06, 0.06), (xc, cy + sy * D * 0.35, gz), st.dark, bevel=0.006)
        K.box((w - 0.2, 0.02, 0.012), (xc, cy + sy * D * 0.35, gz + 0.036), rail, bevel=0.002)
    heads = []
    for i, ph_ in enumerate((0.0, 0.5)):
        br = K.pivot("pnp_bridge", (xc, cy, gz))
        KP.parent([K.box((0.1, D * 0.75, 0.07), (0, 0, 0.02), trim if st.tier != 3 else st.dark, bevel=0.008)], br)
        hd = K.pivot("pnp_head", (0, 0, 0))
        KP.parent([hd], br)
        KP.parent([K.box((0.12, 0.1, 0.14), (0, 0, -0.08), st.dark, bevel=0.01),
                   K.cyl(0.008, 0.08, (-0.03, 0, -0.22), M.metal("chrome"), verts=8, bevel=0),
                   K.cyl(0.008, 0.08, (0.03, 0, -0.22), M.metal("chrome"), verts=8, bevel=0)], hd)
        heads.append((br, hd, ph_, i))

    def hfn(t):
        for br, hd, ph_, i in heads:
            br.location.x = xc + (-1 if i == 0 else 1) * w * 0.22 + w * 0.12 * math.sin(KP.TAU * (t * 3 + ph_))
            hd.location.y = D * 0.3 * math.sin(KP.TAU * (t * 2 + ph_ + 0.25 * i))
    hfn(0.0)
    P.anim.add(hfn)
    KP.stack_light(P, (xc + w / 2 - 0.1, cy + D / 2 - 0.1, cz - 0.06 + hh + 0.06), anim="run")
    # 4 reflow oven: long body, lid, glowing view ports, exhaust stacks + fans
    xc, w = module(X[3], X[4], 0, "oven")
    oh = 0.42 * s
    K.box((w, D, oh), (xc, cy, cz - 0.06), body, bevel=0.02, base=True)
    K.box((w * 0.98, D * 0.98, 0.16 * s), (xc, cy, cz - 0.06 + oh), trim, bevel=0.035, base=True)
    K.box((w + 0.004, 0.03, 0.05), (xc, cy - D / 2, cz - 0.06 + oh - 0.08), stripe, bevel=0.004)
    nz = max(3, int(w / 0.35))
    glow_socks = []
    for i in range(nz):
        x = xc - w / 2 + w * (i + 0.5) / nz
        heat = 0.3 + 0.7 * math.sin(math.pi * (i + 0.5) / nz)
        mat, sock = KP.window_mat((1.0, 0.35 + 0.15 * heat, 0.05), 0.6 + 2.2 * heat, tint=(0.03, 0.012, 0.005), name="oven_port")
        K.box((w / nz * 0.55, 0.02, oh * 0.32), (x, cy - D / 2 - 0.01, cz + oh * 0.12), mat, bevel=0.006)
        K.box((w / nz * 0.62, 0.012, oh * 0.4), (x, cy - D / 2 - 0.004, cz + oh * 0.12), st.dark, bevel=0.006)
        K.box((0.08, 0.012, 0.035), (x, cy - D / 2 - 0.006, cz + oh * 0.48), M.screen((1.0, 0.25, 0.05), 2.5), bevel=0.002)
        glow_socks.append((sock, 0.6 + 2.2 * heat, i))
    for sock, base, i in glow_socks:
        P.anim.pulse(sock, base * 0.85, base * 1.1, k=1, phase=i * 0.17)
    for i in range(2):
        x = xc - w * 0.25 + w * 0.5 * i
        ez = cz - 0.06 + oh + 0.16 * s
        K.cyl(0.07 * s, 0.35 * s, (x, cy + D * 0.2, ez), st.metal("aluminum"), verts=24)
        K.cyl(0.085 * s, 0.03, (x, cy + D * 0.2, ez + 0.35 * s), st.metal("aluminum"), verts=24)
        P.emitter((x, cy + D * 0.2, ez + 0.4 * s), "steam")
        fo, rot = K.fan((x, cy - D * 0.15, ez + 0.03), r=0.1 * s, axis="z", blades=5)
        P.anim.spin(rot, turns=2 / 5)
    P.point_light((xc, cy - D / 2 - 0.25, cz + oh * 0.1), (1.0, 0.4, 0.1), 8.0 * s, radius=0.2, export=0.6)
    # 5 unloader
    xc, w = module(X[4], X[5], 0, "unload")
    K.box((w * 0.9, D * 0.7, 0.75 * s), (xc, cy, cz - 0.06), body, bevel=0.015, base=True)
    KP.hmi_panel(P, (xc + w / 2 + 0.05, cy - D * 0.15, z0), math.pi / 2, z=1.2 * s)
    # cabling/tray behind the line
    KP.cabinet(P, (X[1] + 0.3, S / 2 - 0.25, z0), 0.0, w=0.55 * s, d=0.32, h=1.2 * s)
    KP.cabinet(P, (X[3] - 0.4, S / 2 - 0.25, z0), 0.0, w=0.55 * s, d=0.32, h=1.2 * s, screen=False)
    tray_z = cz + 0.75 * s
    K.box((span * 0.8, 0.18, 0.05), ((xa + xb) / 2, cy + D / 2 + 0.15, tray_z), M.metal("steel", rough=0.4), bevel=0.004)
    for x in (xa + span * 0.1, xa + span * 0.5, xa + span * 0.9):
        K.box((0.05, 0.05, tray_z - z0), (x, cy + D / 2 + 0.24, z0), st.frame, bevel=0.004, base=True)
    if st.hi:
        KP.led_strip((xa, cy - D / 2 - 0.03, cz - 0.08), (xb, cy - D / 2 - 0.03, cz - 0.08), st.glow, 6.0)
    return P.finish(cz + 0.95 * s, frames=16, fps=12)


# --------------------------------------------------------------------------- nanofab
def nanofab(spec, params):
    """Semiconductor cluster tool: hexagonal transfer chamber with a twin-arm wafer handler under a
    glass lid, plasma process chambers around it, load locks + front-end module with load ports,
    gas cabinets and RF generators at the back."""
    P = KP.Plant(spec, params, "machine", palette={
        1: ((0.38, 0.37, 0.33), (0.05, 0.05, 0.05), (0.75, 0.35, 1.0)),
        2: ((0.6, 0.61, 0.6), (0.04, 0.1, 0.26), (0.7, 0.35, 1.0)),
        3: ((0.66, 0.67, 0.68), (0.03, 0.09, 0.24), (0.6, 0.4, 1.0)),
        4: ((0.72, 0.72, 0.71), (0.022, 0.024, 0.028), (0.55, 0.45, 1.0))}, wear=0.5)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 3.5, 0.5, 1.6)
    # raised floor tiles
    tile = st.paint_m((0.55, 0.56, 0.56), 0.4, name="raised_floor")
    K.box((L * 0.9, S * 0.9, 0.05), (0, 0, z0), tile, bevel=0.003, base=True)
    seam = M.plastic((0.08, 0.08, 0.085), 0.6)
    nt = int(L * 0.9 / 0.6)
    for i in range(1, nt):
        K.box((0.008, S * 0.9, 0.004), (-L * 0.45 + L * 0.9 * i / nt, 0, z0 + 0.05), seam, bevel=0, base=True)
    nt = int(S * 0.9 / 0.6)
    for i in range(1, nt):
        K.box((L * 0.9, 0.008, 0.004), (0, -S * 0.45 + S * 0.9 * i / nt, z0 + 0.05), seam, bevel=0, base=True)
    z0 += 0.05
    body = st.body
    dark = st.accent_m
    steel = st.metal("stainless")
    # transfer chamber
    tc = V((L * 0.1, S * 0.06, z0))
    tr = 0.5 * s
    th = 1.0 * s
    K.box((tr * 1.6, tr * 1.6, th * 0.8), tc, dark, bevel=0.02, base=True)
    K.cyl(tr, th * 0.22, tc + V((0, 0, th * 0.8)), steel, verts=6, bevel=0.01)
    K.cyl(tr * 1.03, 0.04, tc + V((0, 0, th * 1.02)), steel, verts=6, bevel=0.006)
    K.cyl(tr * 0.82, 0.012, tc + V((0, 0, th * 1.06 - 0.005)), KP.clear_panel(), verts=6, bevel=0)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        K.cyl(0.018, 0.03, tc + V((math.cos(a) * tr * 0.92, math.sin(a) * tr * 0.92, th * 1.06)), M.metal("dark_steel"), verts=6, bevel=0)
    # wafer handler inside
    hp = K.pivot("handler", tc + V((0, 0, th * 0.88)))
    arm = [K.cyl(0.12 * s, 0.06, (0, 0, 0), M.metal("aluminum"), verts=24)]
    for sgn in (-1, 1):
        arm.append(K.box((0.55 * tr, 0.06 * s, 0.025), (sgn * 0.3 * tr, 0, 0.05), M.metal("aluminum"), bevel=0.004))
        arm.append(K.box((0.2 * tr, 0.12 * s, 0.01), (sgn * 0.62 * tr, 0, 0.07), M.plastic((0.6, 0.55, 0.45), 0.3), bevel=0.002))
        arm.append(K.cyl(0.11 * s, 0.004, (sgn * 0.62 * tr, 0, 0.08), M.metal("silver", rough=0.05), verts=32, bevel=0))
    KP.parent(arm, hp)
    P.anim.add(lambda t: setattr(hp.rotation_euler, "z", math.pi / 6 + (math.pi / 3) * 2 * KP.smooth01(KP.wave(t, 1) * 1.25 - 0.12)))
    # process chambers on 3 back facets + load locks on 2 front facets
    pr = 0.34 * s
    plasma = []
    for k, a_deg in enumerate((90, 150, 30)):
        a = math.radians(a_deg)
        dirv = V((math.cos(a), math.sin(a), 0))
        c = tc + dirv * (tr + pr * 1.1)
        K.box((pr * 1.7, pr * 1.7, th * 0.8), c, body, bevel=0.02, base=True)
        K.cyl(pr, th * 0.3, c + V((0, 0, th * 0.8)), steel, verts=40, bevel=0.008)
        K.cyl(pr * 1.05, 0.05, c + V((0, 0, th * 1.1)), steel, verts=40, bevel=0.008)
        # RF match box + coax
        K.box((pr * 0.9, pr * 0.8, 0.28 * s), c + V((0, 0, th * 1.15)), dark, bevel=0.015, base=True)
        K.cyl(0.03, 0.2, c + V((pr * 0.3, 0, th * 1.15 + 0.28 * s)), M.metal("aluminum"), verts=12)
        # slit valve body between chamber and transfer chamber
        K.box((0.2 * s, 0.2 * s, th * 0.28), tc + dirv * (tr + 0.02) + V((0, 0, th * 0.78)), steel, rot=(0, 0, a), bevel=0.01, base=True)
        # viewport with plasma glow, facing the camera-ish side
        vdir = (dirv + V((0.6, -1.0, 0))).normalized()
        vp = c + vdir * pr + V((0, 0, th * 0.95))
        mat, sock = KP.glow_mat(st.glow, 6.0, base=(0.05, 0.02, 0.08), name="plasma_port")
        K.cyl(0.06 * s, 0.05, vp, mat, rot=KP._axis_rot(vdir), verts=20, base=False, bevel=0.003)
        K.torus(0.065 * s, 0.012, vp + vdir * 0.02, steel, rot=KP._axis_rot(vdir), segs=24, rsegs=6)
        plasma.append((sock, k))
        # gas line drop
        KP.rod(c + V((-pr * 0.6, 0, th * 1.15)), c + V((-pr * 0.6, 0, th * 1.6)), 0.012, steel)
    for sock, k in plasma:
        P.anim.socket(sock, lambda t, k=k: 2.0 + 8.0 * KP.smooth01(math.sin(KP.TAU * (t + k / 3)) * 1.5))
    for a_deg in (-50, -130):
        a = math.radians(a_deg)
        dirv = V((math.cos(a), math.sin(a), 0))
        c = tc + dirv * (tr + 0.22 * s)
        K.box((0.42 * s, 0.4 * s, th * 1.0), c, steel, rot=(0, 0, a), bevel=0.015, base=True)
        K.box((0.3 * s, 0.05, 0.12), c + dirv * 0.21 * s + V((0, 0, th * 0.6)), M.screen((0.3, 0.8, 1.0), 1.5), rot=(0, 0, a + math.pi / 2), bevel=0.003)
    # front-end module (EFEM) with load ports + FOUPs along the -Y side
    ex0, ex1 = -L * 0.4, L * 0.1
    ey = -S * 0.38
    eh = 1.25 * s
    K.box((ex1 - ex0, 0.5 * s, eh), ((ex0 + ex1) / 2, ey + 0.25 * s, z0), body, bevel=0.02, base=True)
    K.box((ex1 - ex0 + 0.04, 0.54 * s, 0.1 * s), ((ex0 + ex1) / 2, ey + 0.25 * s, z0 + eh), body, bevel=0.02, base=True)
    K.box((ex1 - ex0 + 0.05, 0.55 * s, 0.03), ((ex0 + ex1) / 2, ey + 0.25 * s, z0 + eh + 0.02), dark, bevel=0.006, base=True)
    wm, _ = KP.window_mat(st.glow if st.tier >= 4 else (0.85, 0.9, 1.0), 0.3)
    K.box((ex1 - ex0 - 0.3, 0.02, eh * 0.22), ((ex0 + ex1) / 2, ey - 0.01, z0 + eh * 0.66), wm, bevel=0.008, base=True)
    nports = max(2, min(4, int((ex1 - ex0) / 0.7)))
    for i in range(nports):
        x = ex0 + (ex1 - ex0) * (i + 0.5) / nports
        K.box((0.45 * s, 0.4 * s, 0.05), (x, ey - 0.18 * s, z0 + 0.85 * s), dark, bevel=0.008, base=True)
        K.box((0.35 * s, 0.32 * s, 0.3 * s), (x, ey - 0.18 * s, z0 + 0.9 * s), M.plastic((0.55, 0.57, 0.6), 0.25) if st.tier < 4 else M.plastic((0.08, 0.08, 0.09), 0.25),
              bevel=0.04 * s, base=True, name="foup")
        K.box((0.16 * s, 0.08 * s, 0.03), (x, ey - 0.18 * s, z0 + 1.2 * s), M.plastic((0.3, 0.3, 0.3), 0.4), bevel=0.01, base=True)
        K.box((0.45 * s, 0.2 * s, 0.85 * s), (x, ey - 0.1 * s, z0), body, bevel=0.012, base=True)
        KP.status_leds(P, (x + 0.12 * s, ey - 0.2 * s - 0.001, z0 + 0.7 * s), n=2, seed=i, spacing=0.03)
    KP.stack_light(P, (ex1 - 0.12, ey + 0.3 * s, z0 + eh + 0.18 * s), anim="run")
    # back: gas cabinets + RF generator rack, vacuum pumps
    gx = -L * 0.38
    for i in range(2):
        KP.cabinet(P, (gx + i * 0.7 * s, S * 0.4, z0), 0.0, w=0.6 * s, d=0.4 * s, h=1.7 * s, paint=st.paint if st.tier >= 3 else (0.5, 0.5, 0.48))
    K.box((0.5 * s, 0.6 * s, 1.2 * s), (L * 0.38, -S * 0.25, z0), dark, bevel=0.015, base=True)
    KP.status_leds(P, (L * 0.38 + 0.25 * s + 0.002, -S * 0.25, z0 + 1.0 * s), math.pi / 2, n=5, seed=9)
    KP.status_leds(P, (L * 0.38 + 0.25 * s + 0.002, -S * 0.25, z0 + 0.9 * s), math.pi / 2, n=5, seed=10)
    for i in range(2):
        px = -L * 0.12 + i * 0.5 * s
        K.box((0.35 * s, 0.25 * s, 0.3 * s), (px, -S * 0.08, z0), st.paint_m((0.04, 0.12, 0.3), 0.5, name="pump_paint"), bevel=0.02, base=True)
        K.cyl(0.04, 0.25, (px, -S * 0.08 + 0.12 * s, z0 + 0.3 * s), steel, rot=(-math.pi / 2, 0, 0), verts=12)
    # overhead stainless gas lines
    KP.rod((gx, S * 0.32, z0 + 1.6 * s), (tc.x, S * 0.32, z0 + 1.6 * s), 0.015, steel)
    KP.rod((tc.x, S * 0.32, z0 + 1.6 * s), (tc.x, tc.y + tr, z0 + 1.6 * s), 0.015, steel)
    if st.hi:
        KP.led_strip((ex0, ey - 0.02, z0 + eh - 0.04), (ex1, ey - 0.02, z0 + eh - 0.04), st.glow, 6.0)
    P.point_light(tc + V((0.2, -0.4, th + 0.4)), st.glow, 10.0 * s, radius=0.3, export=0.7)
    return P.finish(z0 + max(eh + 0.4, th * 1.7), frames=12, fps=10)


# --------------------------------------------------------------------------- munitions plant
def munitions_plant(spec, params):
    """Shell line behind blast walls: hydraulic press draws casings, conveyor carries them through a
    hooded filling station to a crate packer. Rotating amber warning beacon."""
    P = KP.Plant(spec, params, "machine", palette={
        1: ((0.06, 0.065, 0.04), (0.35, 0.16, 0.03), (1.0, 0.4, 0.05)),
        2: ((0.08, 0.1, 0.045), (0.75, 0.42, 0.02), (1.0, 0.35, 0.05)),
        3: ((0.22, 0.24, 0.2), (0.6, 0.05, 0.02), (1.0, 0.3, 0.05)),
        4: ((0.05, 0.052, 0.055), (0.6, 0.05, 0.02), (1.0, 0.25, 0.05))})
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    s = _clamp(S / 3.0, 0.55, 1.4)
    # blast walls (back + left), concrete with steel caps
    con = st.concrete(0.5)
    wt = 0.22
    wh = 1.6 * s + 0.4
    K.box((L * 0.96, wt, wh), (0, S / 2 - wt / 2 - 0.04, z0), con, bevel=0.02, base=True, name="blast_wall")
    K.box((wt, S * 0.7, wh), (-L / 2 + wt / 2 + 0.04, S * 0.13, z0), con, bevel=0.02, base=True, name="blast_wall")
    cap = M.metal("cast_iron", dirt=0.8)
    K.box((L * 0.96 + 0.02, wt + 0.04, 0.05), (0, S / 2 - wt / 2 - 0.04, z0 + wh), cap, bevel=0.006, base=True)
    K.box((wt + 0.04, S * 0.7, 0.05), (-L / 2 + wt / 2 + 0.04, S * 0.13, z0 + wh), cap, bevel=0.006, base=True)
    hz = M.hazard(4.0)
    K.box((L * 0.96, 0.01, 0.12), (0, S / 2 - wt - 0.045, z0 + 0.1), hz, bevel=0, base=True)
    # conveyor along X
    cy = -S * 0.08
    cz = z0 + 0.8 * s
    brass = M.metal("brass", rough=0.25)
    steel = st.metal("steel")

    def shell():
        return [K.cyl(0.045 * s, 0.22 * s, (0, 0, 0), brass, verts=20, bevel=0.003),
                K.cyl(0.04 * s, 0.1 * s, (0, 0, 0.22 * s), steel if st.tier < 3 else M.metal("dark_steel"), verts=20, bevel=0.003, r2=0.012 * s)]
    x0c, x1c = -L / 2 + 0.35, L / 2 - 0.15
    KP.conveyor(P, x0c, x1c, cy, cz, width=0.22 * s, items=shell, item_spacing=0.32 * s)
    # hydraulic press at the infeed (left)
    px = x0c + 0.35 * s
    pw = 0.75 * s
    body = st.body
    K.box((pw, 0.7 * s, cz - z0 - 0.05), (px, cy, z0), body, bevel=0.02, base=True)
    for sx in (-1, 1):
        K.box((0.14 * s, 0.5 * s, 1.5 * s), (px + sx * pw * 0.42, cy, cz - 0.05), body, bevel=0.02, base=True, name="press_column")
    crown_z = cz - 0.05 + 1.5 * s
    K.box((pw + 0.1, 0.6 * s, 0.3 * s), (px, cy, crown_z), body, bevel=0.025, base=True)
    K.cyl(0.14 * s, 0.4 * s, (px, cy, crown_z + 0.3 * s), st.accent_m, verts=32, bevel=0.01)
    K.cyl(0.05 * s, 0.25 * s, (px, cy, crown_z + 0.7 * s), M.metal("chrome"), verts=16)
    ram = K.pivot("ram", (px, cy, crown_z))
    KP.parent([K.cyl(0.07 * s, 0.6 * s, (0, 0, -0.6 * s), M.metal("chrome", rough=0.12), verts=24, bevel=0.003),
               K.box((pw * 0.7, 0.45 * s, 0.14 * s), (0, 0, -0.72 * s), st.dark, bevel=0.012, base=True),
               K.cyl(0.05 * s, 0.12 * s, (0, 0, -0.84 * s), M.metal("tungsten"), verts=20)], ram)
    stroke = 0.38 * s
    P.anim.add(lambda t: setattr(ram.location, "z", crown_z - stroke * (KP.smooth01(t / 0.35) if t < 0.35 else 1 - KP.smooth01((t - 0.35) / 0.3) if t < 0.65 else 0.0)))
    K.pipe_run([(px - pw * 0.42, cy + 0.25 * s, crown_z + 0.2), (px - pw * 0.42, cy + 0.6 * s, crown_z + 0.2),
                 (px - pw * 0.42, cy + 0.6 * s, z0 + 0.2)], r=0.03, mat=st.pipe)
    K.box((0.5 * s, 0.4 * s, 0.6 * s), (px - 0.05, S / 2 - wt - 0.3 * s, z0), st.accent_m if st.tier < 3 else st.dark, bevel=0.015, base=True, name="hpu")
    KP.sign((px, cy - 0.35 * s - 0.004, z0 + 0.5 * s), 0.0, "warn", 0.14)
    # filling station hood (centre)
    fx = (x0c + x1c) / 2 + 0.2 * s
    fw = 0.9 * s
    K.box((fw, 0.65 * s, 0.9 * s), (fx, cy, cz + 0.32 * s), st.accent_m if st.tier >= 3 else body, bevel=0.025, base=True)
    for sx in (-1, 1):
        K.box((0.1, 0.65 * s, cz - z0 + 0.32 * s), (fx + sx * (fw / 2 - 0.05), cy, z0), body, bevel=0.012, base=True)
    K.box((0.04, 0.03, 0.04), (fx, cy, cz + 0.33 * s), st.dark, bevel=0.0)
    sw, _ = KP.window_mat((1.0, 0.75, 0.4), 0.4)
    K.box((fw * 0.5, 0.02, 0.3 * s), (fx, cy - 0.33 * s, cz + 0.65 * s), sw, bevel=0.006)
    KP.sign((fx + fw * 0.35, cy - 0.33 * s - 0.004, cz + 0.6 * s), 0.0, "danger", 0.14)
    head = K.pivot("filler", (fx, cy, cz + 0.32 * s))
    KP.parent([K.cyl(0.03 * s, 0.22 * s, (0, 0, -0.18 * s), M.metal("stainless"), verts=12)], head)
    P.anim.add(lambda t: setattr(head.location, "z", cz + 0.32 * s + 0.08 * s * KP.wave(t, 1)))
    # hopper / chemical feed pipe from the wall
    K.cyl(0.25 * s, 0.35 * s, (fx, S / 2 - wt - 0.35 * s, cz + 0.55 * s), st.metal("stainless"), verts=32, r2=0.08 * s)
    K.cyl(0.25 * s, 0.4 * s, (fx, S / 2 - wt - 0.35 * s, cz + 0.9 * s), st.metal("stainless"), verts=32)
    K.pipe_run([(fx, S / 2 - wt - 0.35 * s, cz + 0.55 * s), (fx, cy + 0.33 * s, cz + 0.55 * s)], r=0.04, mat=st.pipe)
    for sx in (-1, 1):
        K.box((0.05, 0.05, cz + 0.55 * s - z0), (fx + sx * 0.22 * s, S / 2 - wt - 0.35 * s, z0), st.frame, bevel=0.004, base=True)
    # crate packer at the outfeed (right)
    ox = x1c - 0.3 * s
    for k in range(2):
        cr = K.box((0.5 * s, 0.38 * s, 0.26 * s), (ox - 0.05, cy - 0.5 * s, z0 + k * 0.27 * s), M.painted((0.08, 0.1, 0.04), wear=0.6, grime=0.6, name="ammo_crate"), bevel=0.012, base=True)
        K.box((0.5 * s + 0.01, 0.06, 0.04), (ox - 0.05, cy - 0.5 * s - 0.17 * s, z0 + k * 0.27 * s + 0.18 * s), M.painted((0.75, 0.6, 0.05), wear=0.5, name="crate_band"), bevel=0.003)
    K.box((0.9 * s, 0.7 * s, 0.1), (L / 2 - 0.55 * s, S * 0.2, z0), M.plastic((0.25, 0.17, 0.08), 0.8), bevel=0.01, base=True, name="pallet")
    for k in range(3):
        K.box((0.42 * s, 0.32 * s, 0.24 * s), (L / 2 - 0.55 * s + (k - 1) * 0.28 * s, S * 0.2 + (0.1 if k % 2 else -0.1) * s, z0 + 0.1), M.painted((0.08, 0.1, 0.04), wear=0.6, grime=0.6, name="ammo_crate"), rot=(0, 0, 0.1 * (k - 1)), bevel=0.01, base=True)
    # rotating amber warning beacon on the blast wall + red lamps
    bxp = V((L * 0.3, S / 2 - wt / 2 - 0.04, z0 + wh + 0.05))
    K.cyl(0.08, 0.06, bxp, M.metal("dark_steel"), verts=16)
    K.cyl(0.075, 0.16, bxp + V((0, 0, 0.06)), M.glass((1.0, 0.45, 0.05), 0.15), verts=24)
    rp = K.pivot("beacon_rot", bxp + V((0, 0, 0.13)))
    bm, bsock = KP.glow_mat((1.0, 0.45, 0.05), 15.0, name="beacon_lamp")
    KP.parent([K.box((0.1, 0.02, 0.07), (0, 0, 0), bm, bevel=0.005), K.box((0.02, 0.05, 0.08), (0.04, 0.0, 0), M.metal("chrome", rough=0.05), bevel=0.003)], rp)
    P.anim.spin(rp, turns=2.0)
    P.export_light(bxp + V((0, 0, 0.13)), (1.0, 0.45, 0.05), 0.8, flicker=True)
    for i in range(2):
        lm, ls = KP.glow_mat((1.0, 0.05, 0.02), 8.0, name="red_lamp")
        lp = V((fx - fw / 2 + 0.08 + i * (fw - 0.16), cy - 0.33 * s - 0.03, cz + 1.12 * s))
        K.sphere(0.035, lp, lm, segs=12, rings=8)
        P.anim.blink(ls, 12.0, 0.3, k=2, duty=0.5, phase=0.5 * i)
    KP.cabinet(P, (L / 2 - 0.3, -S * 0.3 + 0.3, z0), math.pi / 2, w=0.55 * s, d=0.3, h=1.15 * s)
    if st.tier <= 2:
        K.scatter_debris(L * 0.85, S * 0.6, 8, seed=6, mat=brass)
    return P.finish(z0 + max(wh, crown_z - z0 + 0.95 * s) + 0.2, frames=16, fps=12)


ARCHETYPES = {
    "assembler": assembler,
    "precision_assembler": precision_assembler,
    "electronics_fab": electronics_fab,
    "nanofab": nanofab,
    "munitions_plant": munitions_plant,
}
