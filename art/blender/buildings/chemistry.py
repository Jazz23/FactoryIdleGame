"""Chemistry, process & research archetypes: chemical_plant, refinery, electrolyzer, centrifuge,
cryo_plant, bioreactor, lab."""
import math

from mathutils import Vector as V

import kit as K
import kit_plant as KP
import materials as M


def _clamp(x, a, b):
    return max(a, min(b, x))


def _spread(a, b, n):
    return [a] if n == 1 else [a + (b - a) * i / (n - 1) for i in range(n)]


# --------------------------------------------------------------------------- chemical plant
def chemical_plant(spec, params):
    """Agitated batch reactors on legs with top drives, feed pump, shell-and-tube exchanger,
    vent stack. Variants: "catalytic" (insulated fixed-bed reactors, no agitators),
    "flow" (helical tubular flow reactor coils in a frame)."""
    P = KP.Plant(spec, params, "process")
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.2, 0.6, 1.5)
    var = st.variant
    n_r = 2 if L < 3.8 else 3
    r = 0.36 * s
    h = 1.2 * s
    legs = 0.45 * s
    ry = S * 0.18
    xs = _spread(-L * 0.27, L * 0.2, n_r)
    tops = []
    if var == "flow":
        # helical flow-reactor coils in an open frame, glowing reaction windows
        fx0, fx1 = -L * 0.4, L * 0.3
        fy0, fy1 = ry - 0.35 * s, ry + 0.35 * s
        fh = 1.6 * s
        fm = st.frame
        for x in (fx0, fx1):
            for y in (fy0, fy1):
                K.box((0.07, 0.07, fh), (x, y, z0), fm, bevel=0.006, base=True)
        for z in (z0 + 0.1, z0 + fh):
            K.box((fx1 - fx0, 0.07, 0.07), ((fx0 + fx1) / 2, fy0, z), fm, bevel=0.006)
            K.box((fx1 - fx0, 0.07, 0.07), ((fx0 + fx1) / 2, fy1, z), fm, bevel=0.006)
        nc = max(3, int((fx1 - fx0) / (0.5 * s)))
        coil_m = st.metal("stainless")
        glow = []
        for i in range(nc):
            cx = fx0 + (fx1 - fx0) * (i + 0.5) / nc
            pts = []
            turns = 7
            for k in range(turns * 16 + 1):
                a = KP.TAU * k / 16
                pts.append((cx + math.cos(a) * 0.17 * s, ry + math.sin(a) * 0.17 * s, z0 + 0.25 * s + (fh - 0.5 * s) * k / (turns * 16)))
            K.tube(pts, 0.022 * s, coil_m)
            gm, gs = KP.glow_mat(st.glow, 4.0, name="flow_core")
            K.cyl(0.07 * s, fh - 0.5 * s, (cx, ry, z0 + 0.25 * s), gm, verts=20, bevel=0)
            glow.append((gs, i))
            K.cyl(0.05 * s, 0.1, (cx, ry, z0 + fh - 0.25 * s), coil_m, verts=16)
        for gs, i in glow:
            P.anim.pulse(gs, 2.0, 7.0, k=1, phase=i / nc)
        P.point_light(((fx0 + fx1) / 2, ry - 0.6, z0 + fh * 0.5), st.glow, 15.0 * s, radius=0.4, export=0.6)
        tops.append(z0 + fh)
    else:
        for i, x in enumerate(xs):
            insul = var == "catalytic"
            mat = M.metal("aluminum", rough=0.45, dirt=0.2 + 0.5 * st.grime) if insul else None
            hh = h * (1.35 if insul else 1.0)
            zt, _ = KP.vessel(P, (x, ry + (0.12 * s if i % 2 else 0), z0), r * (0.85 if insul else 1.0), hh, mat=mat,
                              legs=legs, bands=4 if insul else 2, nozzles=3)
            if insul:
                K.cyl(0.06 * s, 0.35 * s, (x, ry + (0.12 * s if i % 2 else 0), zt - 0.04), st.metal("stainless"), verts=16)
                K.flange((x, ry + (0.12 * s if i % 2 else 0), zt + 0.31 * s), 0.06 * s, "z")
                tops.append(zt + 0.35 * s)
            else:
                cp, top = KP.agitator_drive(P, (x, ry + (0.12 * s if i % 2 else 0), zt - 0.04), s=0.75 * s)
                tops.append(top)
            # level gauge glass on the visible side
            gx = x + r * 0.75
            gl, gsock = KP.glow_mat((0.9, 0.6, 0.15) if st.tier < 4 else st.glow, 1.5, name="sight")
            K.box((0.035, 0.035, hh * 0.6), (gx, ry - r * 0.75, z0 + legs + hh * 0.2), gl, bevel=0.004, base=True)
            K.box((0.05, 0.05, hh * 0.64), (gx + 0.003, ry - r * 0.75 + 0.012, z0 + legs + hh * 0.18), st.metal("steel"), bevel=0.004, base=True)
    # platform between reactor tops (larger footprints)
    if m >= 3.8 and var != "flow":
        pz = z0 + legs + h * 0.95
        KP.platform(P, xs[0] - r - 0.35, xs[-1] + r + 0.35, ry - r - 0.45, ry - r - 0.05, pz, rails=("-y",))
        KP.ladder(P, (xs[-1] + r + 0.15, ry - r - 0.6, z0), pz + 0.9 - z0, 0.0)
    # front: shell & tube heat exchanger (along X) + feed pump
    hx_y = -S * 0.27
    hx_x = L * 0.12
    hl = _clamp(L * 0.42, 0.9, 2.2)
    hr = 0.17 * s
    ztop, _ = KP.hdrum(P, (hx_x, hx_y, z0), hr, hl, mat=st.body if st.tier < 3 else st.metal("stainless"), saddle_h=0.18 * s, nozzles=2)
    # channel head + bolted cover on +X end
    K.cyl(hr * 1.05, 0.25 * s, (hx_x + hl / 2 + 0.02, hx_y, z0 + 0.18 * s + hr), st.accent_m, rot=K.AXES["x"], verts=40, base=True, bevel=0.008)
    K.cyl(hr * 1.3, 0.05, (hx_x + hl / 2 + 0.27 * s, hx_y, z0 + 0.18 * s + hr), st.accent_m, rot=K.AXES["x"], verts=40, base=True, bevel=0.008)
    K.bolts((hx_x + hl / 2 + 0.32 * s, hx_y, z0 + 0.18 * s + hr), hr * 1.15, 12, "x", r=0.012, h=0.016)
    pump, cpl = KP.pump(P, (-L * 0.28, -S * 0.3, z0), 0.0, s=0.75 * s)
    P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0))
    # process piping: pump -> reactor, exchanger -> reactor, header along the back
    pc = st.pipe
    pr = 0.045 * s
    rx0 = xs[0]
    K.pipe_run([(-L * 0.28 - 0.3 * 0.75 * s, -S * 0.3, z0 + 0.3 * s), (-L * 0.28 - 0.3 * 0.75 * s, -S * 0.3, z0 + 1.5 * s),
                (-L * 0.28 - 0.3 * 0.75 * s, ry - r - 0.1, z0 + 1.5 * s), (rx0 - 0.15, ry - r - 0.1, z0 + 1.5 * s)], r=pr, mat=pc)
    K.pipe_run([(hx_x - hl * 0.3, hx_y, ztop + 0.12), (hx_x - hl * 0.3, hx_y, z0 + 1.25 * s),
                (hx_x - hl * 0.3, ry - r - 0.2, z0 + 1.25 * s), (xs[-1], ry - r - 0.2, z0 + 1.25 * s)], r=pr, mat=pc)
    KP.valve((-L * 0.28 - 0.3 * 0.75 * s, -S * 0.3, z0 + 1.0 * s), "z", r=0.05 * s)
    KP.valve((hx_x - hl * 0.3, hx_y, z0 + 0.95 * s), "z", r=0.045 * s)
    # vent stack at the back corner
    vx, vy = L / 2 - 0.25, S / 2 - 0.25
    vh = max(tops) - z0 + 0.6 * s
    K.cyl(0.07 * s, vh, (vx, vy, z0), pc, verts=16)
    K.cyl(0.1 * s, 0.12, (vx, vy, z0 + vh - 0.12), st.dark, verts=20)
    for z in _spread(z0 + 0.6, z0 + vh - 0.5, 3):
        K.box((0.08, 0.3, 0.04), (vx, vy - 0.15, z), st.frame, bevel=0.004)
    P.emitter((vx, vy, z0 + vh + 0.05), "steam")
    # controls
    KP.cabinet(P, (L / 2 - 0.25, -S * 0.05, z0), math.pi / 2, w=0.5 * s, d=0.3, h=1.2 * s)
    KP.stack_light(P, (L / 2 - 0.25, -S * 0.05 + 0.1, z0 + 1.2 * s + 0.12), anim="run")
    KP.sign((hx_x - hl * 0.1, hx_y - hr - 0.004, z0 + 0.18 * s + hr), 0.0, "warn", 0.12)
    if st.tier <= 2:
        K.scatter_debris(L * 0.85, S * 0.85, 6, seed=3)
    return P.finish(max(tops + [z0 + vh]) + 0.15, frames=16, fps=12)


# --------------------------------------------------------------------------- refinery
def refinery(spec, params):
    """Distillation unit: insulated fractionating column with platforms and caged ladder,
    overhead line to a fin-fan condenser + reflux drum, fired heater with glowing burners and
    stack, product pumps, pipe rack. Variants: "cracker" (thick-walled hydrocracking reactor),
    "tower" (taller column + side stripper)."""
    P = KP.Plant(spec, params, "process")
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 5.0, 0.6, 1.5)
    var = st.variant
    # main column at the back-left
    cr = 0.42 * s
    ch = (5.6 if var == "tower" else 4.6) * s
    cx, cy = -L * 0.3, S * 0.25
    plats = [ch * 0.42, ch * 0.82]
    _, ctop = KP.column(P, (cx, cy, z0), cr, ch, platforms=plats, ladder_face="+x")
    ctop += z0
    if var == "tower":
        _, stop = KP.column(P, (cx + 1.15 * s, cy + 0.35 * s, z0), cr * 0.55, ch * 0.6, platforms=[ch * 0.45], ladder_face="-y")
    # overhead vapour line to fin-fan condenser at the back-right
    fx0, fx1 = L * 0.02, L * 0.46
    fy0, fy1 = S * 0.18, S * 0.46
    fz = 2.1 * s
    ff, ftop = KP.finfan(P, fx0, fx1, fy0, fy1, z0 + fz, fans=2)
    KP.steam_pipe(P, [(cx, cy, ctop - 0.05), (cx, cy, ctop + 0.35 * s), ((fx0 + fx1) / 2 - 0.4, cy, ctop + 0.35 * s),
                      ((fx0 + fx1) / 2 - 0.4, cy, z0 + fz + 0.3)], r=0.08 * s)
    # reflux drum under the fin-fan
    KP.hdrum(P, ((fx0 + fx1) / 2, (fy0 + fy1) / 2, z0), 0.28 * s, (fx1 - fx0) * 0.75, saddle_h=0.3 * s, nozzles=2)
    # fired heater (front-left): steel box with refractory, burner peepholes glowing, stack
    hx, hy = -L * 0.22, -S * 0.22
    hw, hd, hh = 1.4 * s, 1.0 * s, 1.8 * s
    if var == "cracker":
        hw, hh = 1.1 * s, 1.5 * s
    body = st.body
    K.box((hw, hd, 0.5 * s), (hx, hy, z0), st.frame, bevel=0.01, base=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.1, 0.1, 0.5 * s), (hx + sx * (hw / 2 - 0.05), hy + sy * (hd / 2 - 0.05), z0), st.dark, bevel=0.006, base=True)
    K.box((hw, hd, hh), (hx, hy, z0 + 0.5 * s), body, bevel=0.02, base=True, name="heater")
    for k in range(int(hw / 0.3)):
        K.box((0.05, hd + 0.04, hh), (hx - hw / 2 + 0.15 + k * 0.3, hy, z0 + 0.5 * s), st.frame, bevel=0.006, base=True)
    K.box((hw * 0.7, hd * 0.7, 0.45 * s), (hx, hy, z0 + 0.5 * s + hh), body, bevel=0.02, base=True, name="convection")
    stack_r = 0.2 * s
    stack_h = 2.4 * s
    K.chimney((hx, hy, z0 + 0.95 * s + hh), stack_r, stack_h, mat=st.paint_m((0.06, 0.06, 0.06), 1.2, name="stack_paint"))
    stack_top = z0 + 0.95 * s + hh + stack_h
    if st.smoke:
        P.emitter((hx, hy, stack_top + 0.05), "smoke")
    else:
        P.emitter((hx, hy, stack_top + 0.05), "steam")
    # burners under the floor glow + peepholes on the front
    fire_socks = []
    for k in range(3):
        bx = hx - hw * 0.3 + k * hw * 0.3
        fm, fs = KP.glow_mat((1.0, 0.45, 0.1), 12.0, base=(0.3, 0.08, 0.01), name="burner")
        K.cyl(0.07 * s, 0.25 * s, (bx, hy, z0 + 0.22 * s), fm, verts=16)
        K.cyl(0.035 * s, 0.03, (bx, hy - hd / 2 - 0.01, z0 + 0.5 * s + hh * 0.25), fm, rot=K.AXES["-y"], verts=12, base=False)
        fire_socks.append((fs, k))
    lightd = P.point_light((hx, hy - 0.1, z0 + 0.18 * s), (1.0, 0.45, 0.12), 40.0 * s, radius=0.3, export=0.8, flicker=True)
    for fs, k in fire_socks:
        P.anim.socket(fs, lambda t, k=k: 12.0 * (0.8 + 0.2 * math.sin(KP.TAU * (t * 2 + k * 0.3)) * math.sin(KP.TAU * (t * 3 + 0.1 * k))))
    P.anim.light(lightd, lambda t: 40.0 * s * (0.85 + 0.15 * math.sin(KP.TAU * t * 2)))
    KP.ladder(P, (hx + hw / 2 + 0.12, hy - hd * 0.2, z0), hh + 0.5 * s, math.pi / 2)
    # transfer line heater -> column
    KP.steam_pipe(P, [(hx + hw * 0.35, hy + hd / 2, z0 + 0.5 * s + hh * 0.7), (hx + hw * 0.35, cy - cr - 0.25, z0 + 0.5 * s + hh * 0.7),
                      (cx + 0.25, cy - cr - 0.25, z0 + 0.5 * s + hh * 0.7)], r=0.07 * s)
    # hydrocracker reactor (variant)
    if var == "cracker":
        rx, ry = L * 0.1, -S * 0.05
        zt, _ = KP.vessel(P, (rx, ry, z0), 0.38 * s, 2.4 * s, mat=st.body if st.tier < 3 else st.metal("stainless"), skirt=0.5 * s, bands=5, nozzles=2)
        K.cyl(0.08 * s, 0.4 * s, (rx, ry, zt - 0.05), st.metal("steel"), verts=16)
    # pumps + pipe rack at the front-right
    for i in range(2):
        pv, cpl = KP.pump(P, (L * 0.12 + i * 0.8 * s, -S * 0.36, z0), 0.0, s=0.7 * s)
        P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0), phase=0.1 * i)
    KP.pipe_rack(P, -L * 0.45, L * 0.45, -S * 0.02, z0 + 1.35 * s, n=4, r=0.05 * s)
    KP.cabinet(P, (L * 0.42, -S * 0.3, z0), math.pi / 2, w=0.55 * s, d=0.32, h=1.3 * s)
    KP.stack_light(P, (L * 0.42, -S * 0.3 + 0.1, z0 + 1.3 * s + 0.12), anim="run")
    KP.sign((hx + hw * 0.3, hy - hd / 2 - 0.006, z0 + 0.5 * s + hh * 0.6), 0.0, "danger", 0.18)
    top = max(ctop + 0.5, stack_top)
    return P.finish(top, frames=16, fps=12)


# --------------------------------------------------------------------------- electrolyzer
def electrolyzer(spec, params):
    """Filter-press electrolyser stacks (many cell frames clamped between end plates with tie rods)
    fed by copper busbars from a rectifier, gas/lye separators with vent stacks, lye pumps.
    Variant "membrane": compact PEM stacks in cabinets."""
    P = KP.Plant(spec, params, "process")
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.2, 0.6, 1.5)
    var = st.variant
    cu = M.metal("copper", rough=0.3, dirt=0.3)
    n_st = 2 if S >= 3.5 else 1
    sl = _clamp(L * 0.5, 1.1, 2.6)
    sx0 = -L * 0.44 + 0.05
    stack_h = 0.75 * s
    led_socks = []
    for j in range(n_st):
        y = -S * 0.25 + j * 0.85 * s
        zc = z0 + 0.32 * s + stack_h / 2
        # support frame
        K.box((sl + 0.2, 0.6 * s, 0.14), (sx0 + sl / 2, y, z0), st.frame, bevel=0.008, base=True)
        for x in (sx0 + 0.1, sx0 + sl - 0.1):
            K.box((0.12, 0.5 * s, 0.32 * s - 0.14), (x, y, z0 + 0.14), st.frame, bevel=0.008, base=True)
        if var == "membrane":
            K.box((sl, 0.6 * s, stack_h + 0.2), (sx0 + sl / 2, y, z0 + 0.32 * s), st.body, bevel=0.02, base=True)
            for k in range(int(sl / 0.35)):
                x = sx0 + 0.18 + k * 0.35
                KP.door(P, (x, y - 0.3 * s, z0 + 0.38 * s), 0.0, w=0.3, h=stack_h, mat=st.body)
            KP.status_leds(P, (sx0 + sl - 0.15, y - 0.3 * s - 0.035, z0 + 0.32 * s + stack_h), n=3, seed=j)
        else:
            # cell frames: alternating body / gasket plates
            n = int(sl / 0.045)
            cell_m = st.body
            gas_m = M.rubber((0.03, 0.03, 0.032))
            for k in range(n):
                x = sx0 + 0.15 + (sl - 0.3) * (k + 0.5) / n
                K.box(((sl - 0.3) / n * 0.72, 0.5 * s, stack_h), (x, y, zc), cell_m if k % 2 == 0 else st.accent_m, bevel=0.004)
            K.box((sl - 0.3, 0.47 * s, stack_h - 0.04), (sx0 + sl / 2, y, zc), gas_m, bevel=0)
            # end plates + tie rods
            for x in (sx0 + 0.1, sx0 + sl - 0.1):
                K.box((0.1, 0.62 * s, stack_h + 0.12), (x, y, zc), st.dark, bevel=0.012)
            for dy in (-0.27 * s, 0.27 * s):
                for dz in (-stack_h / 2 - 0.03, stack_h / 2 + 0.03):
                    K.cyl(0.018, sl - 0.1, (sx0 + 0.05, y + dy, zc + dz), M.metal("steel"), rot=K.AXES["x"], verts=10)
                    for x in (sx0 + 0.04, sx0 + sl - 0.04):
                        K.cyl(0.03, 0.04, (x, y + dy, zc + dz), M.metal("dark_steel"), rot=K.AXES["x"], verts=6, base=False)
            # top gas manifolds
            for dy, col in ((-0.12 * s, (0.75, 0.75, 0.75)), (0.12 * s, (0.1, 0.25, 0.65))):
                K.cyl(0.035 * s, sl - 0.2, (sx0 + 0.1, y + dy, zc + stack_h / 2 + 0.06), st.paint_m(col, 0.6, name="gas_line"), rot=K.AXES["x"], verts=14)
        # copper busbars from the rectifier end (+X)
        bz = z0 + 0.32 * s + stack_h * 0.5
        K.box((L * 0.44 - (sx0 + sl) + L * 0.06, 0.06, 0.012), ((sx0 + sl + L * 0.4) / 2, y - 0.12 * s, bz), cu, bevel=0.002)
        K.box((L * 0.44 - (sx0 + sl) + L * 0.06, 0.06, 0.012), ((sx0 + sl + L * 0.4) / 2, y + 0.12 * s, bz), cu, bevel=0.002)
    # rectifier / transformer cabinet at +X end
    rx = L / 2 - 0.45 * s - 0.05
    K.box((0.8 * s, 0.9 * s, 1.5 * s), (rx, -S * 0.15, z0), st.paint_m((0.55, 0.57, 0.57), 0.6, name="rectifier"), bevel=0.02, base=True)
    KP.louvre((rx + 0.4 * s + 0.012, -S * 0.15, z0 + 0.5 * s), math.pi / 2, 0.5 * s, 0.5 * s)
    K.box((0.012, 0.3 * s, 0.18 * s), (rx + 0.4 * s + 0.006, -S * 0.15 - 0.22 * s, z0 + 1.1 * s), M.screen((0.3, 0.9, 1.0), 2.0), bevel=0.002)
    KP.status_leds(P, (rx + 0.4 * s + 0.005, -S * 0.15 + 0.2 * s, z0 + 1.15 * s), math.pi / 2, n=4, seed=5)
    KP.sign((rx, -S * 0.15 - 0.45 * s - 0.004, z0 + 1.0 * s), 0.0, "danger", 0.16)
    # gas separators (H2 white, O2 blue) at the back with vent stacks
    sep_y = S * 0.28
    vents = []
    for i, (col, x) in enumerate((((0.8, 0.8, 0.78), -L * 0.15), ((0.12, 0.25, 0.6), L * 0.12))):
        mat = st.paint_m(col, 0.6, name="separator")
        zt, _ = KP.vessel(P, (x, sep_y, z0), 0.3 * s, 1.5 * s, mat=mat, legs=0.3 * s, bands=2, nozzles=2)
        vh = zt - z0 + 0.8 * s
        K.cyl(0.04 * s, vh - (zt - z0) + 0.1, (x, sep_y, zt - 0.1), st.metal("stainless"), verts=12)
        K.cyl(0.06 * s, 0.1, (x, sep_y, z0 + vh - 0.05), st.dark, verts=14)
        P.emitter((x, sep_y, z0 + vh + 0.05), "steam")
        vents.append(z0 + vh)
        # line from stacks to separator
        K.pipe_run([(sx0 + sl * (0.3 + 0.4 * i), -S * 0.25 + (0.12 * s if i else -0.12 * s), z0 + 0.32 * s + stack_h + 0.06),
                    (sx0 + sl * (0.3 + 0.4 * i), -S * 0.25 + (0.12 * s if i else -0.12 * s), z0 + 0.32 * s + stack_h + 0.4 * s + i * 0.15),
                    (x, -S * 0.25 + (0.12 * s if i else -0.12 * s), z0 + 0.32 * s + stack_h + 0.4 * s + i * 0.15),
                    (x, sep_y - 0.3 * s, z0 + 0.32 * s + stack_h + 0.4 * s + i * 0.15)], r=0.035 * s, mat=mat)
    # lye circulation pump
    pv, cpl = KP.pump(P, (-L * 0.38, S * 0.32, z0), 0.0, s=0.6 * s)
    P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0))
    KP.stack_light(P, (rx + 0.25 * s, -S * 0.15 - 0.3 * s, z0 + 1.5 * s), anim="run")
    if st.tier <= 2:
        K.scatter_debris(L * 0.8, S * 0.8, 5, seed=8)
    return P.finish(max(vents) + 0.2, frames=16, fps=12)


# --------------------------------------------------------------------------- centrifuge
def centrifuge(spec, params):
    """Decanter centrifuge (rotating bowl hub + belt drive, guard hood) on an inertia block in front,
    a cascade of tall gas centrifuges with header piping behind. Variant "maglev": glowing
    magnetic-bearing rings on the cascade."""
    P = KP.Plant(spec, params, "process", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 3.0, 0.6, 1.6)
    var = st.variant
    body = st.body
    # --- decanter in front along X
    dy = -S * 0.22
    dl = _clamp(L * 0.55, 1.3, 2.6)
    dx = -L * 0.08
    K.box((dl + 0.5 * s, 0.75 * s, 0.25 * s), (dx, dy, z0), st.concrete(0.5), bevel=0.02, base=True, name="inertia_block")
    K.box((dl + 0.3 * s, 0.6 * s, 0.12), (dx, dy, z0 + 0.25 * s), st.frame, bevel=0.01, base=True)
    zc = z0 + 0.37 * s + 0.3 * s
    br = 0.24 * s
    # bowl casing: lower half box + semicylindrical hood
    K.box((dl, 0.55 * s, 0.3 * s), (dx, dy, z0 + 0.37 * s), body, bevel=0.015, base=True)
    hood = K.cyl(0.28 * s, dl, (dx - dl / 2, dy, zc), body, rot=K.AXES["x"], verts=40, base=True, bevel=0.01, name="hood")
    for k in range(5):
        K.torus(0.282 * s, 0.012, (dx - dl / 2 + dl * (k + 0.5) / 5, dy, zc), st.frame, rot=K.AXES["x"], segs=40, rsegs=6)
    # feed tube (-X end) and solids chute / liquid outlet underneath
    K.cyl(0.04 * s, 0.4 * s, (dx - dl / 2 - 0.35 * s, dy, zc), st.metal("stainless"), rot=K.AXES["x"], verts=14)
    K.box((0.25 * s, 0.3 * s, 0.25 * s), (dx - dl * 0.3, dy, z0 + 0.12 * s), st.metal("stainless"), bevel=0.01, base=True)
    # rotating bowl hub / gearbox at +X end (the gearbox housing spins with the bowl)
    hub = K.pivot("bowl_hub", (dx + dl / 2, dy, zc))
    hub_parts = [K.cyl(br, 0.22 * s, (0, 0, 0), st.metal("steel"), rot=K.AXES["x"], verts=40, base=True, bevel=0.008),
                 K.cyl(br * 0.7, 0.1 * s, (0.22 * s, 0, 0), st.metal("cast_iron"), rot=K.AXES["x"], verts=32, base=True, bevel=0.006)]
    for k in range(8):
        a = KP.TAU * k / 8
        hub_parts.append(K.box((0.2 * s, 0.03 * s, 0.04 * s), (0.11 * s, math.cos(a) * br, math.sin(a) * br), st.accent_m, rot=(a, 0, 0), bevel=0.004))
        hub_parts.append(K.cyl(0.012 * s, 0.02, (0.32 * s, math.cos(a) * br * 0.5, math.sin(a) * br * 0.5), M.metal("dark_steel"), rot=K.AXES["x"], verts=6))
    KP.parent(hub_parts, hub)
    P.anim.spin(hub, turns=3 / 8, axis=(1, 0, 0))
    # main motor behind, with belt guard
    mx = dx + dl / 2 - 0.1 * s
    my = dy + 0.6 * s
    K.box((0.6 * s, 0.4 * s, 0.25 * s), (mx, my, z0), st.frame, bevel=0.01, base=True)
    K.motor((mx, my, z0 + 0.25 * s + 0.17 * s), "x", r=0.17 * s, length=0.5 * s, paint=(0.05, 0.14, 0.3) if st.tier <= 2 else (0.6, 0.62, 0.62))
    gm = st.paint_m((0.75, 0.5, 0.02), 0.6, name="guard")
    K.box((0.12 * s, (my - dy) + 0.45 * s, 0.5 * s), (dx + dl / 2 + 0.38 * s, (dy + my) / 2, zc - 0.25 * s), gm, bevel=0.02, base=True, name="belt_guard")
    # --- gas centrifuge cascade behind
    rows = 2 if S >= 3.5 else 1
    n = max(3, int(L * 0.8 / (0.38 * s)))
    cr = 0.11 * s
    ch = 1.7 * s
    cas_m = st.paint_m(st.paint if st.tier >= 3 else (0.6, 0.62, 0.62), 0.5, name="cascade")
    glow = []
    for j in range(rows):
        yy = S * 0.22 + j * 0.45 * s
        for i in range(n):
            x = -L * 0.4 + L * 0.8 * (i + 0.5) / n
            K.cyl(cr * 1.3, 0.08, (x, yy, z0), st.dark, verts=20, bevel=0.005)
            K.cyl(cr, ch, (x, yy, z0 + 0.08), cas_m, verts=28, bevel=0.006, name="gas_centrifuge")
            K.cyl(cr * 1.05, 0.08, (x, yy, z0 + 0.08 + ch), st.dark, verts=24, bevel=0.006)
            if var == "maglev" or st.tier >= 4:
                gmat, gs = KP.glow_mat(st.glow, 5.0, name="maglev")
                K.torus(cr * 1.03, 0.012, (x, yy, z0 + 0.08 + ch * 0.85), gmat, segs=24, rsegs=6)
                glow.append((gs, i + j * n))
            else:
                lm, ls = KP.glow_mat((0.1, 1.0, 0.25), 6.0, base=(0.02, 0.1, 0.03), name="cent_led")
                K.cyl(0.012, 0.01, (x, yy - cr - 0.002, z0 + 0.08 + ch * 0.85), lm, rot=K.AXES["-y"], verts=8, base=False)
                glow.append((ls, i + j * n))
            K.cyl(0.015, 0.25 * s, (x, yy, z0 + 0.16 + ch), st.metal("stainless"), verts=8)
        K.cyl(0.03 * s, L * 0.82, (-L * 0.41, yy, z0 + 0.16 + ch + 0.25 * s), st.metal("stainless"), rot=K.AXES["x"], verts=12)
        for x in (-L * 0.42, L * 0.42):
            K.box((0.05, 0.05, ch + 0.45 * s), (x, yy, z0), st.frame, bevel=0.004, base=True)
    for gs, i in glow:
        if var == "maglev" or st.tier >= 4:
            P.anim.pulse(gs, 3.0, 7.0, k=1, phase=(i % 5) / 5)
        else:
            P.anim.blink(gs, 6.0, 0.5, k=2, duty=0.85, phase=((i * 7) % 11) / 11)
    KP.hmi_panel(P, (L / 2 - 0.2, dy + 0.1, z0), math.pi / 2, z=1.15 * s)
    KP.stack_light(P, (-L * 0.42, S * 0.22 - 0.15, z0 + ch + 0.45 * s), anim="run")
    KP.sign((dx, dy - 0.28 * s - 0.004, z0 + 0.52 * s), 0.0, "warn", 0.12)
    return P.finish(z0 + ch + 0.65 * s, frames=16, fps=12)


# --------------------------------------------------------------------------- cryo plant
def cryo_plant(spec, params):
    """Air separation / liquefier: tall insulated cold box, main air compressor with intercoolers,
    vacuum-insulated LIN tank, frosted ambient vaporiser fins venting cold fog.
    Variant "dilution": cryostat 'chandelier' with glowing stages; "liquefier": twin tanks."""
    P = KP.Plant(spec, params, "process", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 4.0, 0.55, 1.5)
    var = st.variant
    frost = KP.frost_mat()
    # cold box (back-left)
    cbw, cbd, cbh = 1.1 * s, 1.0 * s, 3.6 * s
    cbx, cby = -L * 0.3, S * 0.25
    KP.housing(P, (cbw, cbd, cbh), (cbx, cby, z0), mat=st.body)
    KP.ladder(P, (cbx + cbw / 2 + 0.15, cby - 0.1, z0), cbh - 0.1, math.pi / 2, cage=True)
    KP.sign((cbx, cby - cbd / 2 - 0.006, z0 + 1.3 * s), 0.0, "plate", 0.14)
    KP.sign((cbx - 0.2 * s, cby - cbd / 2 - 0.006, z0 + 0.9 * s), 0.0, "warn", 0.14)
    for k in range(3):
        K.cyl(0.05 * s, 0.3 * s, (cbx - cbw * 0.3 + k * cbw * 0.3, cby, z0 + cbh), st.metal("stainless"), verts=14)
    # frosted pipe from cold box to tank
    tx, ty = L * 0.28, S * 0.22
    tr = 0.42 * s
    th = 2.6 * s
    if var == "dilution":
        # dilution refrigerator: suspended cryostat with gold-plated stages glowing
        K.box((1.3 * s, 1.3 * s, 0.12), (tx, ty, z0 + 2.4 * s), st.frame, bevel=0.01, base=True)
        for sx in (-1, 1):
            for sy in (-1, 1):
                K.box((0.08, 0.08, 2.4 * s), (tx + sx * 0.6 * s, ty + sy * 0.6 * s, z0), st.frame, bevel=0.006, base=True)
        gold = M.metal("gold", rough=0.2)
        zz = z0 + 2.4 * s
        for k, rr in enumerate((0.42, 0.36, 0.3, 0.24, 0.18)):
            zz -= 0.32 * s
            K.cyl(rr * s, 0.04, (tx, ty, zz), gold, verts=40, bevel=0.004)
            for a in range(4):
                aa = KP.TAU * a / 4 + k * 0.3
                K.cyl(0.012, 0.32 * s, (tx + math.cos(aa) * rr * 0.7 * s, ty + math.sin(aa) * rr * 0.7 * s, zz), gold, verts=8)
            for a in range(6):
                aa = KP.TAU * a / 6
                KP.rod((tx + math.cos(aa) * rr * 0.5 * s, ty + math.sin(aa) * rr * 0.5 * s, zz), (tx + math.cos(aa + 0.6) * rr * 0.45 * s, ty + math.sin(aa + 0.6) * rr * 0.45 * s, zz + 0.3 * s), 0.004, M.metal("copper"))
        gm, gs = KP.glow_mat(st.glow, 6.0, name="mixing_chamber")
        K.cyl(0.1 * s, 0.15 * s, (tx, ty, zz - 0.2 * s), gm, verts=24)
        P.anim.pulse(gs, 3.0, 9.0, k=1)
        P.point_light((tx, ty - 0.3, zz), st.glow, 12.0 * s, radius=0.3, export=0.6)
        top = z0 + 2.6 * s
    else:
        ntank = 2 if var == "liquefier" else 1
        top = z0
        for i in range(ntank):
            xx = tx - i * (tr * 2 + 0.25 * s)
            yy = ty + (0.15 * s if i else 0)
            rr = tr * (0.8 if i else 1.0)
            zt, _ = KP.vessel(P, (xx, yy, z0), rr, th * (0.85 if i else 1.0), mat=st.paint_m((0.75, 0.76, 0.75) if st.tier < 4 else st.paint, 0.5, name="lin_tank"),
                              legs=0.35 * s, bands=0, nozzles=0, manway=False)
            top = max(top, zt)
            K.cyl(rr * 1.01, 0.4 * s, (xx, yy, z0 + 0.35 * s + 0.1), frost, verts=40, bevel=0.004)
    K.pipe_run([(cbx + cbw / 2, cby - 0.2 * s, z0 + 1.0 * s), (tx - tr - 0.3 * s, cby - 0.2 * s, z0 + 1.0 * s),
                (tx - tr - 0.3 * s, ty - tr - 0.1, z0 + 1.0 * s)], r=0.06 * s, mat=frost)
    # ambient vaporiser bank (front-right): frosted star-finned tubes
    vx0, vx1 = L * 0.02, L * 0.42
    vy0, vy1 = -S * 0.42, -S * 0.15
    nvx = max(2, int((vx1 - vx0) / (0.32 * s)))
    nvy = max(1, int((vy1 - vy0) / (0.32 * s)))
    vh = 1.5 * s
    for i in range(nvx):
        for j in range(nvy):
            x = vx0 + (vx1 - vx0) * (i + 0.5) / nvx
            y = vy0 + (vy1 - vy0) * (j + 0.5) / nvy
            K.cyl(0.03 * s, vh, (x, y, z0 + 0.15), M.metal("aluminum"), verts=10)
            for k in range(4):
                fin = K.box((0.24 * s, 0.012, vh * (0.95 if True else 1)), (x, y, z0 + 0.15), M.metal("aluminum", rough=0.4, dirt=0.15), rot=(0, 0, k * math.pi / 4), bevel=0.002, base=True)
            K.cyl(0.13 * s, vh * 0.45, (x, y, z0 + 0.15), frost, verts=8, bevel=0.01)
    K.box((vx1 - vx0 + 0.1, vy1 - vy0 + 0.1, 0.15), ((vx0 + vx1) / 2, (vy0 + vy1) / 2, z0), st.frame, bevel=0.01, base=True)
    P.emitter(((vx0 + vx1) / 2, (vy0 + vy1) / 2, z0 + 0.3), "steam")
    # main air compressor (front-left) with motor + intercooler
    ax, ay = -L * 0.25, -S * 0.28
    K.box((1.6 * s, 0.7 * s, 0.25 * s), (ax, ay, z0), st.frame, bevel=0.01, base=True)
    K.motor((ax - 0.4 * s, ay, z0 + 0.25 * s + 0.24 * s), "x", r=0.24 * s, length=0.65 * s, paint=(0.05, 0.14, 0.3) if st.tier <= 2 else (0.6, 0.62, 0.62))
    comp = st.accent_m if st.tier >= 3 else st.body
    K.cyl(0.3 * s, 0.35 * s, (ax + 0.25 * s, ay, z0 + 0.25 * s + 0.3 * s), comp, rot=(math.pi / 2, 0, 0), verts=40, base=False, bevel=0.01)
    K.box((0.4 * s, 0.4 * s, 0.3 * s), (ax + 0.25 * s, ay, z0 + 0.25 * s), comp, bevel=0.015, base=True)
    cp = K.pivot("coupling", (ax - 0.02 * s, ay, z0 + 0.25 * s + 0.24 * s))
    KP.parent([K.cyl(0.08 * s, 0.1 * s, (0, 0, 0), M.metal("steel"), rot=K.AXES["x"], verts=20, base=False),
               K.box((0.1 * s, 0.18 * s, 0.03 * s), (0, 0, 0), M.painted((0.75, 0.5, 0.02), wear=0.4, name="coupling_paint"), bevel=0.004)], cp)
    P.anim.spin(cp, turns=2.0, axis=(1, 0, 0))
    KP.hdrum(P, (ax + 0.45 * s, ay + 0.55 * s, z0), 0.16 * s, 1.0 * s, mat=st.body, axis="x", saddle_h=0.2 * s, nozzles=0)
    K.pipe_run([(ax + 0.25 * s, ay, z0 + 0.25 * s + 0.6 * s), (ax + 0.25 * s, ay, z0 + 1.3 * s), (cbx + 0.2, ay, z0 + 1.3 * s),
                (cbx + 0.2, cby - cbd / 2, z0 + 1.3 * s)], r=0.07 * s, mat=st.pipe)
    KP.cabinet(P, (L / 2 - 0.22, S * 0.02, z0), math.pi / 2, w=0.5 * s, d=0.3, h=1.3 * s)
    KP.stack_light(P, (L / 2 - 0.22, S * 0.02 + 0.12, z0 + 1.3 * s + 0.12), anim="run")
    if var == "dilution" or st.hi:
        KP.led_strip((cbx - cbw / 2, cby - cbd / 2 - 0.02, z0 + cbh - 0.1), (cbx + cbw / 2, cby - cbd / 2 - 0.02, z0 + cbh - 0.1), st.glow, 6.0)
    P.emitter((cbx, cby, z0 + cbh + 0.35 * s), "steam")
    return P.finish(max(top, z0 + cbh + 0.35 * s) + 0.1, frames=16, fps=12)


# --------------------------------------------------------------------------- bioreactor
def bioreactor(spec, params):
    """Default: algae photobioreactor - racks of glowing green tubes + harvest tank + pumps.
    Variant "vat": stainless fermenters with sight glasses, agitator drives, sterile filters."""
    P = KP.Plant(spec, params, "process", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.5, 0.6, 1.5)
    var = st.variant
    culture = (0.25, 0.95, 0.2) if st.tier < 4 else st.glow
    tops = []
    if var == "vat":
        nv = 2 if L < 4.5 else 3
        for i, x in enumerate(_spread(-L * 0.25, L * 0.2, nv)):
            y = S * 0.18 + (0.15 * s if i % 2 else 0)
            r = 0.45 * s
            h = 1.6 * s
            zt, _ = KP.vessel(P, (x, y, z0), r, h, mat=st.metal("stainless", rough=0.2), legs=0.4 * s, bands=3, nozzles=2)
            cp, top = KP.agitator_drive(P, (x, y, zt - 0.04), s=0.75 * s)
            tops.append(top)
            # sight glass with fermenting culture
            fm, fs = KP.fluid_glow((0.9, 0.65, 0.2) if st.tier < 4 else culture, 1.2, name="ferment")
            K.cyl(0.11 * s, 0.03, (x + r * 0.4, y - r * 0.92, z0 + 0.4 * s + h * 0.45), fm, rot=KP._axis_rot(V((0.4, -0.92, 0))), verts=24, base=False)
            K.torus(0.11 * s, 0.015, (x + r * 0.42, y - r * 0.94, z0 + 0.4 * s + h * 0.45), st.metal("stainless"), rot=KP._axis_rot(V((0.4, -0.92, 0))), segs=24, rsegs=6)
            P.anim.pulse(fs, 0.8, 1.5, k=1, phase=i * 0.3)
            # sterile filter housing on top
            K.cyl(0.05 * s, 0.25 * s, (x - r * 0.5, y, zt - 0.08), st.metal("stainless"), verts=14)
        # CIP skid (front-left): two small tanks + pump on a frame
        kx, ky = -L * 0.3, -S * 0.3
        K.box((1.1 * s, 0.6 * s, 0.1), (kx, ky, z0), st.frame, bevel=0.008, base=True)
        for k in range(2):
            KP.vessel(P, (kx - 0.25 * s + k * 0.5 * s, ky + 0.05 * s, z0 + 0.1), 0.2 * s, 0.6 * s, mat=st.metal("stainless", rough=0.2),
                      legs=0.15 * s, bands=1, nozzles=1, manway=False, plate=False)
        pv2, cpl2 = KP.pump(P, (kx, ky - 0.2 * s, z0 + 0.1), 0.0, s=0.45 * s)
        P.anim.spin(cpl2, turns=2.0, axis=(1, 0, 0))
    else:
        # tube racks (photobioreactor): vertical glass tubes with glowing culture
        nr = 2 if S >= 3.5 else 1
        for j in range(nr):
            y = -S * 0.05 + j * 0.75 * s
            x0, x1 = -L * 0.42, L * 0.12
            nt = max(6, int((x1 - x0) / (0.16 * s)))
            th = 1.6 * s
            fm, fs = KP.fluid_glow(culture, 1.0, scale=10.0, name="algae")
            P.anim.pulse(fs, 0.7, 1.25, k=1, phase=j * 0.5)
            for i in range(nt):
                x = x0 + (x1 - x0) * (i + 0.5) / nt
                K.cyl(0.05 * s, th, (x, y, z0 + 0.25), fm, verts=16, bevel=0)
                K.cyl(0.058 * s, th + 0.02, (x, y, z0 + 0.24), KP.clear_panel(), verts=16, bevel=0)
            for z in (z0 + 0.18, z0 + 0.25 + th):
                K.cyl(0.06 * s, x1 - x0 + 0.1, (x0 - 0.05, y, z + 0.04), st.metal("stainless"), rot=K.AXES["x"], verts=16)
            for x in (x0 - 0.1, x1 + 0.1):
                K.box((0.06, 0.25 * s, th + 0.4), (x, y, z0), st.frame, bevel=0.006, base=True)
            K.box((x1 - x0 + 0.3, 0.3 * s, 0.05), ((x0 + x1) / 2, y, z0 + th + 0.45), st.frame, bevel=0.006, base=True)
            # grow lights above
            gl = KP.led((1.0, 0.45, 0.85) if st.tier < 4 else st.glow, 5.0)
            K.box((x1 - x0, 0.06, 0.02), ((x0 + x1) / 2, y - 0.12 * s, z0 + th + 0.43), gl, bevel=0)
            tops.append(z0 + th + 0.5)
        P.point_light((-L * 0.15, -S * 0.25, z0 + 1.0 * s), culture, 18.0 * s, radius=0.5, export=0.6)
        # harvest tank (back-right)
        zt, _ = KP.vessel(P, (L * 0.3, S * 0.25, z0), 0.4 * s, 1.3 * s, mat=st.body, legs=0.3 * s, bands=2, nozzles=2)
        cp, top = KP.agitator_drive(P, (L * 0.3, S * 0.25, zt - 0.04), s=0.65 * s)
        tops.append(top)
    # circulation pumps + CIP header
    pv, cpl = KP.pump(P, (L * 0.3, -S * 0.32, z0), 0.0, s=0.65 * s)
    P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0))
    K.pipe_run([(L * 0.3 - 0.3 * 0.65 * s, -S * 0.32, z0 + 0.3 * s), (L * 0.3 - 0.3 * 0.65 * s, -S * 0.32, z0 + 1.3 * s),
                (-L * 0.42, -S * 0.32, z0 + 1.3 * s)] if var != "vat" else
               [(L * 0.3 - 0.3 * 0.65 * s, -S * 0.32, z0 + 0.3 * s), (L * 0.3 - 0.3 * 0.65 * s, -S * 0.32, z0 + 1.3 * s),
                (-L * 0.25, -S * 0.32, z0 + 1.3 * s), (-L * 0.25, S * 0.18 - 0.5 * s, z0 + 1.3 * s)],
               r=0.04 * s, mat=st.metal("stainless"))
    KP.cabinet(P, (L / 2 - 0.22, S * 0.0, z0), math.pi / 2, w=0.5 * s, d=0.3, h=1.25 * s)
    KP.stack_light(P, (L / 2 - 0.22, 0.12, z0 + 1.25 * s + 0.12), anim="run")
    return P.finish(max(tops) + 0.15, frames=16, fps=12)


# --------------------------------------------------------------------------- lab
def lab(spec, params):
    """Research lab: lab block with lit windows and roof HVAC, glass-domed analysis station with a
    spinning sample carousel, server racks with blinking LEDs. Tier 1: drafting office shed with an
    instrument mast (spinning anemometer). Tier 4: adds a glowing quantum cryostat."""
    P = KP.Plant(spec, params, "machine", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 3.2, 0.6, 1.6)
    body = st.body
    # lab block along the back
    bw, bd = L * 0.82, _clamp(S * 0.38, 0.9, 2.2)
    bh = (1.9 if st.tier > 1 else 1.7) * s + 0.2
    bx, by = -L * 0.04, S / 2 - bd / 2 - 0.08
    if st.tier == 1:
        # corrugated shed with pitched roof
        K.box((bw, bd, bh), (bx, by, z0), body, bevel=0.02, base=True, name="shed")
        cor = st.paint_m(st.accent if st.accent else (0.3, 0.3, 0.3), 1.0, name="corrugated")
        for i in range(int(bw / 0.08)):
            K.cyl(0.018, bh - 0.1, (bx - bw / 2 + 0.04 + i * 0.08, by - bd / 2 - 0.005, z0 + 0.05), cor, verts=8, bevel=0)
        roof = K.prism([(-bd / 2 - 0.12, 0), (bd / 2 + 0.12, 0), (0, 0.45 * s)], bw + 0.2, (bx, by, z0 + bh), st.paint_m((0.12, 0.05, 0.03), 1.0, name="roof"),
                       rot=(0, 0, math.pi / 2), bevel=0.01)
    else:
        KP.housing(P, (bw, bd, bh), (bx, by, z0), mat=body)
    nwin = max(2, int(bw / 0.8))
    wsock = []
    for i in range(nwin):
        x = bx - bw / 2 + bw * (i + 0.5) / nwin
        if i == nwin // 2:
            KP.door(P, (x, by - bd / 2, z0 + 0.02), 0.0, w=0.7 * s, h=1.6 * s if bh > 1.8 * s else bh * 0.8, mat=st.accent_m, window=True)
            continue
        wm, ws = KP.window_mat((1.0, 0.92, 0.75), 0.6, name="lab_window")
        K.box((bw / nwin * 0.62, 0.02, bh * 0.36), (x, by - bd / 2 - 0.01, z0 + bh * 0.58), wm, bevel=0.006)
        K.box((bw / nwin * 0.62 + 0.06, 0.014, bh * 0.36 + 0.06), (x, by - bd / 2 - 0.004, z0 + bh * 0.58), st.frame, bevel=0.006)
        K.box((bw / nwin * 0.62 + 0.08, 0.06, 0.03), (x, by - bd / 2 - 0.03, z0 + bh * 0.4 - 0.03), st.frame, bevel=0.004)
        wsock.append(ws)
    KP.sign((bx - bw * 0.42, by - bd / 2 - 0.006, z0 + bh * 0.85), 0.0, "plate", 0.14)
    # roof gear
    if st.tier > 1:
        K.box((0.8 * s, 0.6 * s, 0.4 * s), (bx - bw * 0.25, by, z0 + bh + 0.05), st.light_grey, bevel=0.02, base=True, name="hvac")
        fo, rot = K.fan((bx - bw * 0.25, by, z0 + bh + 0.47 * s), r=0.2 * s, axis="z", blades=5)
        P.anim.spin(rot, turns=2 / 5)
        # antenna mast + dish
        mx, my = bx + bw * 0.35, by + bd * 0.2
        K.cyl(0.03, 1.0 * s, (mx, my, z0 + bh + 0.05), st.metal("steel"), verts=10)
        dish = K.sphere(0.22 * s, (mx - 0.05, my - 0.1, z0 + bh + 0.85 * s), st.light_grey, segs=24, rings=12, scale=(1, 1, 0.35))
        dish.rotation_euler = (math.radians(50), 0, math.radians(-30))
        K.cyl(0.012, 0.25 * s, (mx - 0.05, my - 0.1, z0 + bh + 0.85 * s), st.metal("steel"), rot=(math.radians(50), 0, math.radians(-30)), verts=8)
        bl_m, bl_s = KP.glow_mat((1.0, 0.1, 0.05), 10.0, name="mast_light")
        K.sphere(0.03, (mx, my, z0 + bh + 1.08 * s), bl_m, segs=10, rings=6)
        P.anim.blink(bl_s, 14.0, 0.2, k=1, duty=0.25)
        mast_top = z0 + bh + 1.1 * s
    else:
        # instrument mast with spinning anemometer
        mx, my = bx + bw * 0.42, by - bd * 0.1
        K.cyl(0.025, 1.6 * s, (mx, my, z0 + bh * 0.6), st.metal("steel"), verts=10)
        an = K.pivot("anemometer", (mx, my, z0 + bh * 0.6 + 1.6 * s))
        cups = []
        for k in range(3):
            a = KP.TAU * k / 3
            cups.append(KP.rod((0, 0, 0), (math.cos(a) * 0.18, math.sin(a) * 0.18, 0), 0.006, M.metal("steel")))
            c = K.sphere(0.04, (math.cos(a) * 0.18, math.sin(a) * 0.18, 0), M.plastic((0.05, 0.05, 0.05), 0.4), segs=12, rings=6, scale=(1, 1, 0.8))
            cups.append(c)
        KP.parent(cups, an)
        P.anim.spin(an, turns=1 / 3 * 2)
        K.cyl(0.06, 0.25 * s, (bx - bw * 0.3, by + 0.1, z0 + bh + 0.1), st.metal("cast_iron"), verts=16)
        P.emitter((bx - bw * 0.3, by + 0.1, z0 + bh + 0.1 + 0.25 * s), "smoke")
        bl_m, bl_s = KP.glow_mat((1.0, 0.6, 0.2), 6.0, name="lamp")
        K.sphere(0.05, (bx + bw * 0.2, by - bd / 2 - 0.12, z0 + bh * 0.85), bl_m, segs=12, rings=8)
        P.anim.socket(bl_s, lambda t: 6.0 * (0.85 + 0.15 * math.sin(KP.TAU * t * 3)))
        mast_top = z0 + bh * 0.6 + 1.7 * s
    # analysis station: pedestal + glass dome + sample carousel (front-left)
    ax, ay = -L * 0.2, -S * 0.2
    pr = 0.42 * s
    K.cyl(pr * 1.15, 0.7 * s, (ax, ay, z0), st.accent_m if st.tier >= 3 else st.dark, verts=48, bevel=0.015)
    K.cyl(pr * 1.2, 0.05, (ax, ay, z0 + 0.7 * s), st.metal("stainless"), verts=48, bevel=0.006)
    KP.status_leds(P, (ax, ay - pr * 1.15 - 0.002, z0 + 0.5 * s), n=5, seed=3)
    car = K.pivot("carousel", (ax, ay, z0 + 0.75 * s))
    parts = [K.cyl(pr * 0.95, 0.04, (0, 0, 0), st.metal("aluminum"), verts=48, bevel=0.004),
             K.cyl(0.05, 0.3 * s, (0, 0, 0), st.metal("steel"), verts=16)]
    cols = [(1.0, 0.15, 0.08), (0.2, 1.0, 0.3), (0.2, 0.5, 1.0), (1.0, 0.8, 0.1)]
    for k in range(12):
        a = KP.TAU * k / 12
        p = V((math.cos(a) * pr * 0.75, math.sin(a) * pr * 0.75, 0.04))
        parts.append(K.cyl(0.035 * s, 0.22 * s, p, KP.clear_panel(), verts=12, bevel=0))
        parts.append(K.cyl(0.03 * s, 0.14 * s, p, KP.led(cols[k % 4], 2.5), verts=12, bevel=0))
        parts.append(K.cyl(0.037 * s, 0.03, p + V((0, 0, 0.22 * s)), M.plastic((0.85, 0.85, 0.85), 0.3), verts=12, bevel=0.002))
    KP.parent(parts, car)
    P.anim.spin(car, turns=1 / 3)
    dome = K.sphere(pr * 1.1, (ax, ay, z0 + 0.72 * s), KP.clear_panel(), segs=40, rings=20, scale=(1, 1, 0.75))
    K.torus(pr * 1.1, 0.02, (ax, ay, z0 + 0.73 * s), st.metal("stainless"), segs=48, rsegs=8)
    # small robot arm feeding the carousel (tier >= 3)
    if st.tier >= 3:
        rb = KP.RobotArm(P, (ax + pr * 1.6, ay - 0.05, z0), s=0.5 * s)
        base = V((ax + pr * 1.6, ay - 0.05, z0))
        t1 = V((ax + pr * 0.95, ay + 0.15, z0 + 0.82 * s)) - base
        t2 = V((ax + pr * 1.7, ay + 0.45 * s, z0 + 0.75 * s)) - base
        K.box((0.3 * s, 0.25 * s, 0.7 * s), (ax + pr * 1.7, ay + 0.45 * s, z0), st.dark, bevel=0.01, base=True)
        rb.animate(P, [t1 + V((0, 0, 0.12)), t1, t1 + V((0, 0, 0.12)), t2 + V((0, 0, 0.12)), t2, t2 + V((0, 0, 0.12))], grips=[0, 1, 1, 1, 0, 0])
    # server racks on the right with blinking LEDs (visible +X and -Y faces)
    rx = L / 2 - 0.35 * s
    nrack = 2 if S >= 3.5 or st.tier >= 3 else 1
    for i in range(nrack):
        ry = -S * 0.3 + i * 0.65 * s
        K.box((0.55 * s, 0.6 * s, 1.5 * s), (rx, ry, z0), M.painted((0.025, 0.025, 0.028), wear=0.15, grime=0.2, rough=0.35, rust=0.0, name="rack"), bevel=0.012, base=True)
        K.box((0.012, 0.5 * s, 1.35 * s), (rx + 0.28 * s, ry, z0 + 0.07), KP.clear_panel(), bevel=0, base=True)
        for k in range(9):
            KP.status_leds(P, (rx + 0.27 * s, ry, z0 + 0.15 + k * 0.14 * s), math.pi / 2, n=6, spacing=0.06 * s, seed=i * 20 + k,
                           colors=[(0.1, 1.0, 0.25), (0.15, 0.6, 1.0), (1.0, 0.5, 0.0)])
            K.box((0.01, 0.48 * s, 0.1 * s), (rx + 0.265 * s, ry, z0 + 0.15 + k * 0.14 * s), M.plastic((0.06, 0.06, 0.065), 0.4), bevel=0.002)
    # quantum cryostat (tier 4)
    top = max(mast_top, z0 + bh + 0.5)
    if st.tier >= 4:
        qx, qy = L * 0.08, -S * 0.12
        K.box((0.9 * s, 0.9 * s, 0.08), (qx, qy, z0 + 2.0 * s), st.frame, bevel=0.01, base=True)
        for sx in (-1, 1):
            for sy in (-1, 1):
                K.box((0.06, 0.06, 2.0 * s), (qx + sx * 0.42 * s, qy + sy * 0.42 * s, z0), st.frame, bevel=0.006, base=True)
        gold = M.metal("gold", rough=0.2)
        zz = z0 + 2.0 * s
        for k, rr in enumerate((0.3, 0.25, 0.2, 0.15)):
            zz -= 0.3 * s
            K.cyl(rr * s, 0.035, (qx, qy, zz), gold, verts=36, bevel=0.004)
            for a in range(3):
                aa = KP.TAU * a / 3 + k
                K.cyl(0.01, 0.3 * s, (qx + math.cos(aa) * rr * 0.7 * s, qy + math.sin(aa) * rr * 0.7 * s, zz), gold, verts=8)
        gm, gs = KP.glow_mat(st.glow, 8.0, name="qubit")
        K.cyl(0.07 * s, 0.12 * s, (qx, qy, zz - 0.15 * s), gm, verts=20)
        P.anim.pulse(gs, 3.0, 10.0, k=2)
        P.point_light((qx, qy - 0.3, zz), st.glow, 10.0 * s, radius=0.3, export=0.7)
        top = max(top, z0 + 2.1 * s)
    if st.hi:
        KP.led_strip((bx - bw / 2, by - bd / 2 - 0.03, z0 + bh - 0.06), (bx + bw / 2, by - bd / 2 - 0.03, z0 + bh - 0.06), st.glow, 6.0)
    P.export_light((ax, ay, z0 + 0.9 * s), (0.6, 0.8, 1.0), 0.4)
    return P.finish(top, frames=12, fps=10)


ARCHETYPES = {
    "chemical_plant": chemical_plant,
    "refinery": refinery,
    "electrolyzer": electrolyzer,
    "centrifuge": centrifuge,
    "cryo_plant": cryo_plant,
    "bioreactor": bioreactor,
    "lab": lab,
}
