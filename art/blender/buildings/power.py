"""Power archetypes: boiler, steam_engine, steam_turbine, solar_array, wind_turbine, accumulator,
gas_turbine, reactor, heat_exchanger, cooling_tower, fusion_reactor, geothermal_plant, substation."""
import math

from mathutils import Vector as V

import kit as K
import kit_plant as KP
import materials as M


def _clamp(x, a, b):
    return max(a, min(b, x))


def _spread(a, b, n):
    return [a] if n == 1 else [a + (b - a) * i / (n - 1) for i in range(n)]


def _brick(st):
    return M.concrete(1.2, tint=(0.62, 0.3, 0.2) if st.tier <= 2 else (0.75, 0.42, 0.3), tex="concrete_floor_worn_001")


def _fire(P, loc, size, axis="-y", strength=14.0, phase=0.0):
    """Glowing furnace opening with flicker; returns emission socket."""
    fm, fs = KP.glow_mat((1.0, 0.42, 0.08), strength, base=(0.3, 0.07, 0.01), name="fire")
    rot = {"-y": (math.pi / 2, 0, 0), "+x": (0, math.pi / 2, 0)}[axis]
    K.cyl(size, 0.03, loc, fm, rot=rot, verts=24, base=False, bevel=0.0)
    P.anim.socket(fs, lambda t: strength * (0.78 + 0.22 * (0.5 + 0.5 * math.sin(KP.TAU * (t * 2 + phase))) *
                                            (0.7 + 0.3 * math.sin(KP.TAU * (t * 3 + 0.37 + phase)))))
    return fs


# --------------------------------------------------------------------------- boiler
def boiler(spec, params):
    """Default: riveted fire-tube shell boiler on a brick setting - glowing firing doors at the front
    (+X), steam dome with safety valves and stop valve, gauge glass, feed pump, rear chimney.
    Variant "water_tube": cased water-tube boiler with steam drum, burner front and steel stack."""
    P = KP.Plant(spec, params, "power")
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    s = _clamp(S / 2.2, 0.55, 1.5)
    body = st.body
    lag = st.paint_m(st.paint, 1.0, name="lagging")
    steel = st.metal("steel")
    emit_kind = "smoke" if st.smoke else "steam"
    if st.variant == "water_tube":
        cx0, cx1 = -L * 0.38, L * 0.22
        cw, ch = S * 0.66, 1.6 * s
        cy = S * 0.02
        K.box((cx1 - cx0, cw, ch), ((cx0 + cx1) / 2, cy, z0), body, bevel=0.02, base=True, name="casing")
        for i in range(int((cx1 - cx0) / 0.45) + 1):
            x = cx0 + i * 0.45
            K.box((0.07, cw + 0.06, ch + 0.04), (x, cy, z0), st.frame, bevel=0.006, base=True, name="buckstay")
        for z in (0.5, 1.1):
            K.box((cx1 - cx0 + 0.06, 0.06, 0.08), ((cx0 + cx1) / 2, cy - cw / 2 - 0.03, z0 + z * s), st.frame, bevel=0.006)
        # steam drum on top
        dr = 0.26 * s
        dz = z0 + ch + 0.12
        K.box((0.12, 0.12, 0.14), (cx0 + 0.3, cy, z0 + ch), st.frame, bevel=0.006, base=True)
        K.box((0.12, 0.12, 0.14), (cx1 - 0.3, cy, z0 + ch), st.frame, bevel=0.006, base=True)
        KP.hdrum(P, ((cx0 + cx1) / 2, cy, z0 + ch - 0.1), dr, (cx1 - cx0) * 0.85, mat=lag, saddle_h=0.2, nozzles=0)
        top_z = z0 + ch + 0.1 + dr * 2
        for k in range(2):
            x = (cx0 + cx1) / 2 - 0.25 + k * 0.5
            K.cyl(0.04 * s, 0.3 * s, (x, cy, top_z - 0.02), steel, verts=12)
            K.cyl(0.06 * s, 0.08, (x, cy, top_z + 0.28 * s), st.metal("brass"), verts=12)
        P.emitter(((cx0 + cx1) / 2, cy, top_z + 0.4 * s), "steam")
        # downcomers at the +X end
        for dy in (-0.15, 0.15):
            K.cyl(0.05 * s, ch, (cx1 + 0.08, cy + dy * s, z0), lag, verts=14)
        # burner front on +X: windbox + flame window + forced-draft fan
        bx = cx1 + 0.04
        K.box((0.25, cw * 0.7, ch * 0.6), (bx + 0.12, cy, z0 + 0.1), st.accent_m, bevel=0.015, base=True)
        _fire(P, (bx + 0.25, cy, z0 + 0.1 + ch * 0.3), 0.11 * s, axis="+x")
        K.torus(0.12 * s, 0.02, (bx + 0.26, cy, z0 + 0.1 + ch * 0.3), steel, rot=K.AXES["x"], segs=24, rsegs=6)
        K.cyl(0.3 * s, 0.22 * s, (bx + 0.5 * s, cy - cw * 0.3, z0 + 0.3 * s), st.accent_m, rot=(math.pi / 2, 0, 0), verts=36, base=False, bevel=0.01)
        K.motor((bx + 0.5 * s, cy - cw * 0.3 - 0.32 * s, z0 + 0.3 * s), "y", r=0.12 * s, length=0.3 * s)
        P.point_light((bx + 0.45, cy, z0 + 0.1 + ch * 0.3), (1.0, 0.45, 0.12), 25.0 * s, radius=0.15, export=0.8, flicker=True)
        # steel stack at the back
        sx_, sy_ = cx0 + 0.3, cy + cw * 0.15
        K.chimney((sx_, sy_, z0 + ch), 0.18 * s, 2.0 * s, mat=st.paint_m((0.06, 0.06, 0.06), 1.2, name="stack_paint"))
        P.emitter((sx_, sy_, z0 + ch + 2.0 * s + 0.05), emit_kind)
        top = z0 + ch + 2.0 * s
        KP.ladder(P, (cx0 + 0.5, cy - cw / 2 - 0.15, z0), ch + 0.2, 0.0)
        KP.gauge((bx + 0.26, cy + cw * 0.28, z0 + ch * 0.85), math.pi / 2, r=0.06)
        KP.cabinet(P, (L / 2 - 0.2, S / 2 - 0.25, z0), math.pi / 2, w=0.45 * s, d=0.3, h=1.1 * s)
        return P.finish(top + 0.1, frames=12, fps=10)

    # ---- fire-tube shell boiler
    r = _clamp(S * 0.3, 0.4, 1.3)
    sl = L * 0.62
    sx = -L * 0.06
    sy = S * 0.04
    set_h = 0.4 * s
    zc = z0 + set_h + r * 0.85
    br = _brick(st)
    K.box((sl + 0.1, r * 2.0, set_h + r * 0.6), (sx, sy, z0), br, bevel=0.02, base=True, name="setting")
    K.box((sl + 0.16, r * 2.06, 0.06), (sx, sy, z0 + set_h + r * 0.6), M.concrete(1.0, tint=(0.5, 0.48, 0.45)), bevel=0.01, base=True)
    K.cyl(r, sl, (sx - sl / 2, sy, zc), lag, rot=K.AXES["x"], verts=56, base=True, bevel=0.01, name="shell")
    seam = st.metal("cast_iron")
    for k in range(4):
        x = sx - sl / 2 + sl * (k + 0.5) / 4
        K.torus(r * 1.005, 0.018, (x, sy, zc), seam, rot=K.AXES["x"], segs=56, rsegs=8)
    # front plate (+X) with firing doors, gauge glass, gauges
    fx = sx + sl / 2
    K.cyl(r * 1.02, 0.06, (fx, sy, zc), st.accent_m if st.tier > 1 else seam, rot=K.AXES["x"], verts=56, base=True, bevel=0.01)
    for k in range(16):
        a = KP.TAU * k / 16
        K.cyl(0.012, 0.02, (fx + 0.06, sy + math.cos(a) * r * 0.94, zc + math.sin(a) * r * 0.94), M.metal("dark_steel"), rot=K.AXES["x"], verts=6)
    nd = 2 if S > 1.6 else 1
    socks = []
    for k in range(nd):
        dy = sy + (k - (nd - 1) / 2) * r * 0.85
        dz = zc - r * 0.35
        K.cyl(r * 0.3, 0.08, (fx + 0.05, dy, dz), st.metal("cast_iron"), rot=K.AXES["x"], verts=32, base=True, bevel=0.01)
        socks.append(_fire(P, (fx + 0.14, dy, dz), r * 0.17, axis="+x", phase=k * 0.3))
        for j in range(5):
            K.box((0.01, r * 0.28, 0.012), (fx + 0.155, dy, dz - r * 0.12 + j * r * 0.06), M.metal("dark_steel"), bevel=0)
    P.point_light((fx + 0.45, sy, zc - r * 0.35), (1.0, 0.45, 0.12), 30.0 * s, radius=0.2, export=0.9, flicker=True)
    # ash pit door under
    K.box((0.06, r * 1.2, set_h * 0.6), (fx + 0.06, sy, z0 + set_h * 0.15), st.metal("cast_iron"), bevel=0.01, base=True)
    # gauge glass + pressure gauge on the front plate
    K.box((0.04, 0.05, r * 0.55), (fx + 0.09, sy + r * 0.62, zc + r * 0.05), M.glass((0.7, 0.85, 0.9), 0.05), bevel=0.006, base=True)
    K.box((0.05, 0.07, 0.04), (fx + 0.09, sy + r * 0.62, zc + r * 0.05), M.metal("brass"), bevel=0.004, base=True)
    K.box((0.05, 0.07, 0.04), (fx + 0.09, sy + r * 0.62, zc + r * 0.6), M.metal("brass"), bevel=0.004, base=True)
    KP.gauge((fx + 0.1, sy - r * 0.5, zc + r * 0.45), math.pi / 2, r=0.07 * s + 0.02)
    KP.sign((fx + 0.07, sy, zc + r * 0.55), math.pi / 2, "plate", 0.12)
    # steam dome + safety valves + stop valve + steam main
    dzb = zc + r * 0.9
    K.cyl(r * 0.36, r * 0.55, (sx + sl * 0.15, sy, dzb), lag, verts=36, bevel=0.01)
    K.sphere(r * 0.36, (sx + sl * 0.15, sy, dzb + r * 0.55), lag, segs=36, rings=12, scale=(1, 1, 0.45))
    K.cyl(r * 0.42, 0.04, (sx + sl * 0.15, sy, dzb + 0.05), seam, verts=36, bevel=0.006)
    for k in range(2):
        x = sx - sl * 0.2 + k * 0.2 * s
        K.cyl(0.04 * s, 0.25 * s, (x, sy, zc + r * 0.96), st.metal("brass"), verts=12)
        K.cyl(0.055 * s, 0.05, (x, sy, zc + r * 0.96 + 0.25 * s), st.metal("brass"), verts=12)
    P.emitter((sx - sl * 0.2 + 0.1 * s, sy, zc + r + 0.35 * s), "steam")
    vtop = dzb + r * 0.55 + r * 0.16
    KP.valve((sx + sl * 0.15, sy, vtop + 0.08), "z", r=0.06 * s)
    K.pipe_run([(sx + sl * 0.15, sy, vtop + 0.2), (sx + sl * 0.15, sy, vtop + 0.4 * s), (sx + sl * 0.15, S / 2 - 0.1, vtop + 0.4 * s),
                (sx + sl * 0.15, S / 2 - 0.1, z0 + 0.2)], r=0.06 * s, mat=st.pipe)
    # rear smoke box + chimney (back-left)
    rx = sx - sl / 2 - 0.25 * s
    K.box((0.5 * s, r * 1.7, set_h + r * 1.5), (rx, sy, z0), br, bevel=0.02, base=True, name="smokebox")
    ch_h = 2.2 * s + r
    K.chimney((rx, sy, z0 + set_h + r * 1.5), 0.17 * s + 0.05, ch_h, mat=st.paint_m((0.05, 0.05, 0.05), 1.3, name="stack_paint"))
    P.emitter((rx, sy, z0 + set_h + r * 1.5 + ch_h + 0.05), emit_kind)
    # feed pump on the -Y side + water line
    pv, cpl = KP.pump(P, (sx - sl * 0.15, -S / 2 + 0.25 * s, z0), 0.0, s=0.55 * s)
    P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0))
    K.pipe_run([(sx - sl * 0.15 - 0.3 * 0.55 * s, -S / 2 + 0.25 * s, z0 + 0.32 * s), (sx - sl * 0.15 - 0.3 * 0.55 * s, sy - r * 0.95, z0 + 0.32 * s),
                (sx - sl * 0.15 - 0.3 * 0.55 * s, sy - r * 0.95, zc - r * 0.2)], r=0.035 * s, mat=st.pipe)
    # coal heap + shovel area at the front (tier 1/2), or a burner cabinet
    if st.tier <= 2:
        coal = M.plastic((0.015, 0.015, 0.017), 0.6)
        rnd = P.rnd
        for i in range(26):
            K.sphere(rnd.uniform(0.05, 0.09) * s, (fx + 0.35 * s + rnd.uniform(-0.15, 0.25) * s, -S / 2 + 0.3 + rnd.uniform(-0.1, 0.25) * s,
                                                     z0 + rnd.uniform(0.0, 0.12) * s), coal, segs=7, rings=5, scale=(1, 0.9, 0.7))
    else:
        KP.cabinet(P, (L / 2 - 0.2, S / 2 - 0.25, z0), math.pi / 2, w=0.45 * s, d=0.3, h=1.1 * s)
    if st.tier <= 1:
        K.scatter_debris(L * 0.85, S * 0.85, 8, seed=2)
    return P.finish(z0 + set_h + r * 1.5 + ch_h + 0.1, frames=12, fps=10)


# --------------------------------------------------------------------------- steam engine
def steam_engine(spec, params):
    """Horizontal mill engine: cylinder + valve chest, crosshead on guides, connecting rod, crank,
    big spoked flywheel, flyball governor, dynamo on the shaft. Full revolution per loop."""
    P = KP.Plant(spec, params, "power")
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.0, 0.55, 1.6)
    iron = st.metal("cast_iron")
    steel = M.metal("steel", rough=0.25, dirt=0.3)
    brass = M.metal("brass", rough=0.25, dirt=0.3)
    body = st.body
    ye = -S * 0.2
    zs = z0 + 0.85 * s
    xs = L * 0.2
    rc = 0.2 * s
    lc = 0.75 * s
    # bed plate
    K.box((xs - (-L * 0.44) + 0.25 * s, 0.42 * s, 0.38 * s), ((xs - L * 0.44) / 2, ye, z0), iron, bevel=0.02, base=True, name="bed")
    K.box((xs - (-L * 0.44) + 0.25 * s, 0.46 * s, 0.05), ((xs - L * 0.44) / 2, ye, z0 + 0.38 * s), body, bevel=0.01, base=True)
    # cylinder
    cyl_x0 = -L * 0.44
    cyl_len = 0.62 * s
    cr = 0.24 * s
    K.box((cyl_len * 0.8, 0.4 * s, zs - z0 - cr * 0.6), (cyl_x0 + cyl_len / 2, ye, z0), iron, bevel=0.02, base=True)
    K.cyl(cr, cyl_len, (cyl_x0, ye, zs), st.paint_m(st.paint, 1.0, name="lagging"), rot=K.AXES["x"], verts=40, base=True, bevel=0.01, name="cylinder")
    for x in (cyl_x0, cyl_x0 + cyl_len):
        K.cyl(cr * 1.12, 0.05, (x, ye, zs), iron, rot=K.AXES["x"], verts=40, base=False, bevel=0.008)
        K.bolts((x + (0.026 if x > cyl_x0 else -0.026), ye, zs), cr * 1.02, 12, "x", r=0.012, h=0.012)
    for k in range(3):
        K.torus(cr * 1.005, 0.01, (cyl_x0 + cyl_len * (k + 1) / 4, ye, zs), brass, rot=K.AXES["x"], segs=40, rsegs=6)
    # valve chest on top + steam inlet with stop valve
    K.box((cyl_len * 0.7, 0.28 * s, 0.22 * s), (cyl_x0 + cyl_len / 2, ye, zs + cr * 0.8), iron, bevel=0.015, base=True)
    vx = cyl_x0 + cyl_len / 2
    KP.valve((vx, ye, zs + cr * 0.8 + 0.22 * s + 0.08), "z", r=0.06 * s)
    K.pipe_run([(vx, ye, zs + cr * 0.8 + 0.22 * s + 0.2), (vx, ye, zs + 0.95 * s), (vx, S / 2 - 0.12, zs + 0.95 * s), (vx, S / 2 - 0.12, z0 + 0.15)],
               r=0.06 * s, mat=M.metal("aluminum", rough=0.45, dirt=0.4) if st.tier >= 3 else st.pipe)
    # exhaust to a stack at the back-left
    ex, ey_ = -L * 0.4, S * 0.32
    K.pipe_run([(cyl_x0 + cyl_len * 0.3, ye + 0.2 * s, zs - cr * 0.5), (cyl_x0 + cyl_len * 0.3, ey_, zs - cr * 0.5), (ex, ey_, zs - cr * 0.5)],
               r=0.07 * s, mat=st.pipe)
    stack_h = 2.4 * s
    K.cyl(0.09 * s, stack_h, (ex, ey_, zs - cr * 0.5), st.pipe, verts=20)
    K.cyl(0.13 * s, 0.25 * s, (ex, ey_, zs - cr * 0.5 + stack_h - 0.25 * s), iron, verts=20)
    P.emitter((ex, ey_, zs - cr * 0.5 + stack_h + 0.05), "steam")
    # guides
    gx0, gx1 = cyl_x0 + cyl_len + 0.03, xs - rc - 0.18 * s
    for dz in (-0.1 * s, 0.1 * s):
        K.box((gx1 - gx0, 0.16 * s, 0.035 * s), ((gx0 + gx1) / 2, ye, zs + dz + (0.07 if dz > 0 else -0.07) * s), steel, bevel=0.004)
    K.box((0.07 * s, 0.24 * s, 0.4 * s), (gx1 + 0.03, ye, zs - 0.2 * s), iron, bevel=0.008)
    # crank shaft along Y: main bearings + flywheel + dynamo
    yf = ye + 0.42 * s
    rf = zs - z0 - 0.1
    for y in (ye + 0.2 * s, yf + 0.18 * s):
        K.box((0.3 * s, 0.14 * s, zs - z0 + 0.06), (xs, y, z0), iron, bevel=0.012, base=True, name="pedestal")
        K.box((0.34 * s, 0.17 * s, 0.07 * s), (xs, y, zs + 0.06 * s), brass, bevel=0.008, base=False)
    K.cyl(0.055 * s, (yf + 0.75 * s) - (ye - 0.1 * s), (xs, ye - 0.1 * s, zs), steel, rot=(-math.pi / 2, 0, 0), verts=20, base=True)
    fly = K.pivot("flywheel", (xs, yf, zs))
    KP.parent(KP.spoked_wheel(rf, 0.16 * s, st.paint_m((0.05, 0.05, 0.05) if st.tier <= 2 else st.accent, 1.0, name="flywheel_paint"),
                              hub_mat=iron, spokes=6, rim=0.12 * s), fly)
    # pit under the flywheel
    K.box((rf * 2 + 0.2, 0.36 * s, 0.03), (xs, yf, z0 - 0.005), M.plastic((0.01, 0.01, 0.01), 0.9), bevel=0, base=True)
    # crank disc + pin
    crank = K.pivot("crank", (xs, ye, zs))
    KP.parent([K.box((rc * 2 + 0.16 * s, 0.07 * s, 0.18 * s), (rc * 0.5, 0, 0), iron, bevel=0.012),
               K.cyl(0.04 * s, 0.14 * s, (rc, -0.07 * s, 0), steel, rot=(math.pi / 2, 0, 0), verts=16, base=False)], crank)
    # crosshead + piston rod (slides along X), connecting rod (pivots at the crosshead)
    xh_piv = K.pivot("crosshead", (0, ye, zs))
    KP.parent([K.box((0.14 * s, 0.13 * s, 0.13 * s), (0, 0, 0), steel, bevel=0.01),
               K.cyl(0.025 * s, 0.7 * s, (-0.7 * s, 0, 0), M.metal("chrome", rough=0.1), rot=K.AXES["x"], verts=12, base=True)], xh_piv)
    rod = K.pivot("conrod", (0, ye - 0.07 * s, zs))
    KP.parent([K.box((lc, 0.05 * s, 0.08 * s), (lc / 2, 0, 0), steel, bevel=0.01),
               K.cyl(0.06 * s, 0.07 * s, (0, 0, 0), steel, rot=(math.pi / 2, 0, 0), verts=16, base=False),
               K.cyl(0.07 * s, 0.07 * s, (lc, 0, 0), brass, rot=(math.pi / 2, 0, 0), verts=16, base=False)], rod)
    for o in (crank, fly, rod):
        o.rotation_mode = "XYZ"
    # flyball governor on a column beside the valve chest, belt-driven from the shaft
    gpx, gpy = vx + cyl_len * 0.3, ye - 0.32 * s
    K.cyl(0.03 * s, 0.85 * s + zs - z0 - 0.5 * s, (gpx, gpy, z0), iron, verts=12)
    gov = K.pivot("governor", (gpx, gpy, zs + 0.38 * s))
    gparts = [K.cyl(0.012 * s, 0.32 * s, (0, 0, -0.05 * s), steel, verts=8), K.cyl(0.03 * s, 0.04, (0, 0, 0.26 * s), brass, verts=12)]
    for sgn in (-1, 1):
        gparts.append(KP.rod((0, 0, 0.25 * s), (sgn * 0.13 * s, 0, 0.05 * s), 0.008 * s, steel))
        gparts.append(K.sphere(0.045 * s, (sgn * 0.13 * s, 0, 0.05 * s), brass, segs=16, rings=10))
    KP.parent(gparts, gov)
    P.anim.spin(gov, turns=2.0)

    def update(t):
        th = KP.TAU * t
        crank.rotation_euler = (0, -th, 0)
        fly.rotation_euler = (0, -th, 0)
        px, pz = rc * math.cos(th), rc * math.sin(th)
        xh = xs + px - math.sqrt(lc * lc - pz * pz)
        xh_piv.location.x = xh
        rod.location.x = xh
        rod.rotation_euler = (0, math.atan2(-pz, xs + px - xh), 0)
    update(0.0)
    P.anim.add(update)
    # dynamo on the far side of the flywheel
    dyy = yf + 0.38 * s
    K.box((0.6 * s, 0.5 * s, zs - z0 - 0.3 * s), (xs, dyy + 0.15 * s, z0), iron, bevel=0.015, base=True)
    K.cyl(0.3 * s, 0.45 * s, (xs, dyy, zs), st.accent_m if st.tier > 1 else body, rot=(-math.pi / 2, 0, 0), verts=36, base=True, bevel=0.01, name="dynamo")
    for k in range(10):
        a = KP.TAU * k / 10
        K.box((0.03 * s, 0.4 * s, 0.03 * s), (xs + math.cos(a) * 0.3 * s, dyy + 0.22 * s, zs + math.sin(a) * 0.3 * s), iron, bevel=0.003)
    K.box((0.16 * s, 0.12 * s, 0.1 * s), (xs, dyy + 0.22 * s, zs + 0.33 * s), iron, bevel=0.008)
    # gauges, oilers, railing around the flywheel pit
    KP.gauge((cyl_x0 + cyl_len * 0.3, ye - 0.2 * s - 0.005, zs + 0.38 * s), 0.0, r=0.06 * s)
    for k in range(3):
        K.cyl(0.02 * s, 0.08 * s, (gx0 + 0.1 + k * 0.2 * s, ye, zs + 0.2 * s), M.glass((0.8, 0.7, 0.3), 0.1), verts=10)
    if st.tier >= 2:
        KP.railing(P, [(xs + rf + 0.15, yf - 0.3 * s, z0), (xs + rf + 0.15, yf + 0.3 * s, z0)], h=0.9)
    lm, ls = KP.glow_mat((0.1, 1.0, 0.25) if st.tier > 1 else (1.0, 0.6, 0.2), 6.0, name="pilot")
    K.sphere(0.03, (xs + 0.2 * s, dyy + 0.22 * s, zs + 0.45 * s), lm, segs=10, rings=6)
    if st.tier <= 1:
        K.scatter_debris(L * 0.85, S * 0.85, 7, seed=5)
    return P.finish(max(zs + rf, zs - cr * 0.5 + stack_h) + 0.1, frames=16, fps=12)


# --------------------------------------------------------------------------- steam turbine
def steam_turbine(spec, params):
    """Turbine-generator set on a concrete table: HP casing (tapered, split-flange bolts), crossover
    pipe to the LP casing, coupling guards, generator with cooler, exciter. Couplings spin."""
    P = KP.Plant(spec, params, "power", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    s = _clamp(S / 3.0, 0.55, 1.5)
    con = st.concrete(0.5)
    tz = z0 + 0.55 * s
    cy = -S * 0.05
    K.box((L * 0.9, 1.3 * s, 0.55 * s), (0, cy, z0), con, bevel=0.03, base=True, name="table")
    for x in _spread(-L * 0.4, L * 0.4, 4):
        K.box((0.25 * s, 1.4 * s, 0.1), (x, cy, z0 + 0.45 * s), con, bevel=0.01, base=True)
    body = st.body
    acc = st.accent_m
    zc = tz + 0.45 * s
    # HP turbine: tapered casing via lathe, horizontal split flange
    hx0, hx1 = -L * 0.43, -L * 0.17
    hp = KP.lathe([(0.0, 0), (0.26 * s, 0), (0.3 * s, 0.05), (0.38 * s, (hx1 - hx0) * 0.6), (0.4 * s, hx1 - hx0 - 0.05), (0.36 * s, hx1 - hx0), (0.0, hx1 - hx0)],
                  (hx0, cy, zc), body, segs=40, name="hp_casing")
    hp.rotation_euler = (0, math.pi / 2, 0)
    K.box((hx1 - hx0, 0.86 * s, 0.05), ((hx0 + hx1) / 2, cy, zc - 0.025), acc, bevel=0.006)
    for k in range(int((hx1 - hx0) / 0.09)):
        for sy in (-1, 1):
            K.cyl(0.014, 0.05, (hx0 + 0.05 + k * 0.09, cy + sy * 0.4 * s, zc + 0.02), M.metal("dark_steel"), verts=6)
    K.box((0.2 * s, 0.9 * s, zc - tz), (hx0 + 0.15 * s, cy, tz), st.dark, bevel=0.01, base=True)
    # stop valve chest + main steam lines from the back
    sv = V((hx0 + (hx1 - hx0) * 0.5, cy + 0.6 * s, tz))
    K.cyl(0.16 * s, 0.7 * s, sv, body, verts=28, bevel=0.01)
    K.cyl(0.08 * s, 0.25 * s, sv + V((0, 0, 0.7 * s)), M.metal("chrome", rough=0.15), verts=16)
    K.box((0.18 * s, 0.18 * s, 0.2 * s), sv + V((0, 0, 0.95 * s)), st.dark, bevel=0.01, base=True)
    KP.steam_pipe(P, [(sv.x, sv.y, tz + 0.3 * s), (sv.x, S / 2 - 0.1, tz + 0.3 * s), (sv.x, S / 2 - 0.1, z0 + 0.05)], r=0.09 * s)
    KP.steam_pipe(P, [(sv.x, sv.y - 0.16 * s, tz + 0.5 * s), (sv.x, cy, tz + 0.5 * s), (sv.x, cy, zc + 0.3 * s)], r=0.07 * s, flanges=False)
    # LP turbine: boxy exhaust hood + rounded top casing
    lx0, lx1 = -L * 0.13, L * 0.12
    K.box((lx1 - lx0, 1.1 * s, 0.5 * s), ((lx0 + lx1) / 2, cy, tz), body, bevel=0.02, base=True, name="lp_hood")
    lp = K.cyl(0.55 * s, lx1 - lx0 - 0.08, (lx0 + 0.04, cy, tz + 0.5 * s), body, rot=K.AXES["x"], verts=48, base=True, bevel=0.012, name="lp_casing")
    K.box((lx1 - lx0 + 0.04, 1.16 * s, 0.05), ((lx0 + lx1) / 2, cy, tz + 0.48 * s), acc, bevel=0.006, base=True)
    for k in range(4):
        K.box((0.04, 1.12 * s, 0.45 * s), (lx0 + (lx1 - lx0) * (k + 0.5) / 4, cy, tz), st.frame, bevel=0.004, base=True)
    # crossover pipe HP -> LP (arch)
    KP.steam_pipe(P, [((hx0 + hx1) / 2 + 0.1, cy, zc + 0.35 * s), ((hx0 + hx1) / 2 + 0.1, cy, zc + 0.95 * s),
                      ((lx0 + lx1) / 2, cy, zc + 0.95 * s), ((lx0 + lx1) / 2, cy, tz + 0.95 * s)], r=0.11 * s, flanges=True)
    # generator
    gx0, gx1 = L * 0.17, L * 0.38
    gr = 0.42 * s
    K.box((gx1 - gx0, 0.95 * s, zc - tz), ((gx0 + gx1) / 2, cy, tz), st.dark, bevel=0.015, base=True)
    K.cyl(gr, gx1 - gx0, (gx0, cy, zc), body, rot=K.AXES["x"], verts=48, base=True, bevel=0.012, name="generator")
    for x in (gx0, gx1):
        K.cyl(gr * 1.04, 0.08, (x, cy, zc), acc, rot=K.AXES["x"], verts=48, base=False, bevel=0.01)
    K.box((gx1 - gx0 - 0.2, 0.6 * s, 0.32 * s), ((gx0 + gx1) / 2, cy, zc + gr * 0.85), st.light_grey, bevel=0.02, base=True, name="cooler")
    for i in range(int((gx1 - gx0 - 0.3) / 0.12)):
        K.box((0.012, 0.012, 0.28 * s), (gx0 + 0.15 + i * 0.12, cy - 0.3 * s - 0.004, zc + gr * 0.85 + 0.02), st.dark, bevel=0, base=True)
    KP.sign((gx0 + 0.3, cy - gr - 0.004, zc), 0.0, "danger", 0.16)
    # exciter
    ex0 = gx1 + 0.12
    K.cyl(0.18 * s, L * 0.06, (ex0, cy, zc), acc, rot=K.AXES["x"], verts=32, base=True, bevel=0.008)
    # spinning shaft couplings (HP-LP, LP-gen, gen-exciter)
    for x0_, x1_ in ((hx1, lx0), (lx1, gx0), (gx1, ex0)):
        xm = (x0_ + x1_) / 2
        K.cyl(0.05 * s, x1_ - x0_ + 0.1, (x0_ - 0.05, cy, zc), M.metal("steel"), rot=K.AXES["x"], verts=16, base=True)
        cp = K.pivot("coupling", (xm, cy, zc))
        parts = [K.cyl(0.11 * s, 0.06, (0, 0, 0), M.metal("steel", rough=0.3), rot=K.AXES["x"], verts=24, base=False, bevel=0.004)]
        for k in range(6):
            a = KP.TAU * k / 6
            parts.append(K.cyl(0.012 * s, 0.08, (0, math.cos(a) * 0.08 * s, math.sin(a) * 0.08 * s), M.metal("dark_steel"), rot=K.AXES["x"], verts=6, base=False))
        parts.append(K.box((0.07, 0.03 * s, 0.22 * s), (0, 0, 0), M.painted((0.75, 0.5, 0.02), wear=0.4, name="coupling_paint"), bevel=0.003))
        KP.parent(parts, cp)
        P.anim.spin(cp, turns=1.0 / 2, axis=(1, 0, 0))
        # bearing pedestal
        K.box((0.12, 0.4 * s, zc - tz - 0.05), (x0_ + 0.02, cy, tz), st.dark, bevel=0.008, base=True)
    # gland steam vent + lube oil skid + panel
    P.emitter(((lx0 + lx1) / 2, cy + 0.3 * s, tz + 1.15 * s), "steam")
    K.cyl(0.03 * s, 0.6 * s, ((lx0 + lx1) / 2, cy + 0.3 * s, tz + 0.55 * s), st.pipe, verts=10)
    K.box((0.9 * s, 0.6 * s, 0.5 * s), (L * 0.3, S / 2 - 0.4 * s, z0), st.accent_m, bevel=0.015, base=True, name="lube_skid")
    pv, cpl = KP.pump(P, (L * 0.3, S / 2 - 0.4 * s, z0 + 0.5 * s), 0.0, s=0.45 * s)
    P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0))
    KP.hmi_panel(P, (L * 0.44, -S * 0.38, z0), math.pi / 2, z=1.1 * s)
    KP.stack_light(P, (gx1 - 0.1, cy + 0.2 * s, zc + gr * 0.85 + 0.32 * s), anim="run")
    if st.hi:
        KP.led_strip((-L * 0.45, cy - 0.65 * s - 0.01, tz - 0.05), (L * 0.45, cy - 0.65 * s - 0.01, tz - 0.05), st.glow, 6.0)
    return P.finish(zc + 1.1 * s, frames=16, fps=12)


# --------------------------------------------------------------------------- solar array
def solar_array(spec, params):
    """Fixed-tilt PV tables (modules in aluminium frames on galvanised posts) facing the lit side,
    combiner boxes and an inverter station with blinking status LEDs. Variant "thin_film"."""
    P = KP.Plant(spec, params, "power", wear=0.6)
    L, S = P.orient_long_x()
    st = P.st
    gravel = M.concrete(2.0, tint=(0.62, 0.6, 0.56))
    K.box((L * 0.98, S * 0.98, 0.04), (0, 0, 0), gravel, bevel=0.01, base=True, name="gravel")
    z0 = 0.04
    thin = st.variant == "thin_film"
    pv = KP.pv_mat(st.tier if not thin else 4)
    frame_m = M.metal("aluminum", rough=0.3, dirt=0.2 + 0.4 * st.grime)
    post_m = M.metal("steel", rough=0.35, dirt=0.3 + 0.5 * st.grime)
    tilt = math.radians(25)
    inv_w = _clamp(L * 0.16, 0.5, 1.0)
    x0, x1 = -L * 0.47, L * 0.47 - inv_w - 0.1
    nrow = max(1, int(round(S / 1.35)))
    pitch = S * 0.92 / nrow
    tw = pitch * 0.62                       # table depth along the slope
    mod_w = 0.55 if not thin else 0.6
    nmod = max(2, int((x1 - x0) / mod_w))
    mw = (x1 - x0) / nmod
    nup = 2 if tw > 0.9 else 1
    mh = tw / nup
    for j in range(nrow):
        yc = -S * 0.46 + pitch * (j + 0.5)
        zl = z0 + 0.35
        zc = zl + math.sin(tilt) * tw / 2
        table = K.pivot("table", (0, yc, zc), (tilt, 0, 0))
        parts = []
        for i in range(nmod):
            for k in range(nup):
                x = x0 + mw * (i + 0.5)
                y = -tw / 2 + mh * (k + 0.5)
                parts.append(K.box((mw - 0.02, mh - 0.02, 0.012), (x, y, 0.025), pv, bevel=0.002, name="pv_module"))
                parts.append(K.box((mw - 0.006, mh - 0.006, 0.035), (x, y, 0.0), frame_m, bevel=0.003, name="pv_frame"))
        for y in (-tw * 0.3, tw * 0.3):
            parts.append(K.box((x1 - x0, 0.05, 0.05), ((x0 + x1) / 2, y, -0.045), post_m, bevel=0.004))
        KP.parent(parts, table)
        # posts (front short, rear tall) + diagonal braces
        npost = max(2, int((x1 - x0) / 1.3) + 1)
        for x in _spread(x0 + 0.1, x1 - 0.1, npost):
            yf_, yr_ = yc - math.cos(tilt) * tw * 0.3, yc + math.cos(tilt) * tw * 0.3
            zf_, zr_ = zc - math.sin(tilt) * tw * 0.3 - 0.07, zc + math.sin(tilt) * tw * 0.3 - 0.07
            K.box((0.05, 0.05, zf_), (x, yf_, 0), post_m, bevel=0.004, base=True)
            K.box((0.05, 0.05, zr_), (x, yr_, 0), post_m, bevel=0.004, base=True)
            KP.rod((x, yf_, 0.1), (x, yr_, zr_ - 0.1), 0.012, post_m, verts=6)
            K.cyl(0.07, 0.05, (x, yf_, 0), M.concrete(1.0), verts=12)
            K.cyl(0.07, 0.05, (x, yr_, 0), M.concrete(1.0), verts=12)
        # combiner box on the last post with an LED
        cbx = x1 - 0.1
        K.box((0.16, 0.08, 0.2), (cbx + 0.1, yc - math.cos(tilt) * tw * 0.3 - 0.05, 0.25), st.light_grey, bevel=0.01, base=True)
        lm, ls = KP.glow_mat((0.1, 1.0, 0.25), 6.0, base=(0.02, 0.1, 0.03), name="combiner_led")
        K.cyl(0.01, 0.01, (cbx + 0.15, yc - math.cos(tilt) * tw * 0.3 - 0.091, 0.4), lm, rot=K.AXES["-y"], verts=8, base=False)
        P.anim.blink(ls, 7.0, 0.3, k=1, duty=0.8, phase=j * 0.37)
    # inverter station at the +X end
    ix = L * 0.47 - inv_w / 2
    K.box((inv_w + 0.1, S * 0.5, 0.12), (ix, -S * 0.12, z0), M.concrete(0.8), bevel=0.01, base=True)
    inv = st.paint_m(st.paint, 0.6, name="inverter")
    K.box((inv_w, 0.55, 1.0), (ix, -S * 0.2, z0 + 0.12), inv, bevel=0.015, base=True, name="inverter")
    KP.louvre((ix + inv_w / 2 + 0.012, -S * 0.2, z0 + 0.6), math.pi / 2, 0.3, 0.3)
    KP.status_leds(P, (ix, -S * 0.2 - 0.28, z0 + 0.95), n=4, seed=7)
    K.box((inv_w * 0.5, 0.012, 0.12), (ix, -S * 0.2 - 0.28, z0 + 0.75), M.screen((0.3, 0.9, 0.5), 1.8), bevel=0.002)
    KP.sign((ix - inv_w * 0.25, -S * 0.2 - 0.284, z0 + 0.45), 0.0, "danger", 0.1)
    K.box((inv_w * 0.8, 0.45, 0.7), (ix, -S * 0.2 + 0.6, z0 + 0.12), st.light_grey, bevel=0.015, base=True, name="transformer")
    KP.radiator_bank(P, (ix + inv_w * 0.4 + 0.08, -S * 0.2 + 0.6, z0 + 0.2), 0.36, 0.45, depth=0.12, axis="y", mat=st.light_grey)
    # cable trench along the tables
    K.box((0.12, S * 0.85, 0.05), (x1 + 0.12, 0, z0), M.concrete(1.0, tint=(0.8, 0.8, 0.8)), bevel=0.006, base=True)
    return P.finish(z0 + 1.3, frames=16, fps=8)


# --------------------------------------------------------------------------- wind turbine
def wind_turbine(spec, params):
    """Horizontal-axis wind turbine: tapered tubular tower on a concrete foundation, nacelle with
    spinner, three twisted blades (1/3 turn per loop), aviation light. Variant "heavy": taller."""
    P = KP.Plant(spec, params, "power", wear=0.5)
    st = P.st
    m = min(P.w, P.d)
    heavy = st.variant == "heavy"
    hub_h = (2.2 * m + 1.3) * (1.1 if heavy else 1.0)
    bl = (0.95 * m + 0.45) * (1.1 if heavy else 1.0)
    white = st.paint_m((0.72, 0.73, 0.72), 0.5, name="turbine_white", rough=0.35)
    # foundation
    K.cyl(0.42 * m, 0.2, (0, 0, 0), st.concrete(0.6), verts=8, bevel=0.02)
    K.cyl(0.22 * m, 0.12, (0, 0, 0.2), st.concrete(0.6), verts=24, bevel=0.01)
    z0 = 0.32
    rb = 0.09 * m + 0.1
    rt = rb * 0.55
    K.cyl(rb, hub_h - z0 - 0.15 * bl, (0, 0, z0), white, verts=40, r2=rt, bevel=0.006, name="tower")
    # tower sections + base band in the building paint
    for f in (0.33, 0.66):
        rr = rb + (rt - rb) * f
        K.torus(rr * 1.005, 0.012, (0, 0, z0 + (hub_h - z0 - 0.15 * bl) * f), M.metal("steel", rough=0.3, dirt=0.2), segs=40, rsegs=6)
    K.cyl(rb * 1.02, 0.5, (0, 0, z0), st.body, verts=40, r2=rb * 0.98, bevel=0.004)
    KP.door(P, (0, -rb * 0.98, z0 + 0.12), 0.0, w=0.32, h=0.75, mat=st.body)
    for k in range(3):
        K.box((0.4, 0.12, 0.04), (0, -rb - 0.12 - k * 0.12, z0 - 0.04 * (k + 1) + 0.04), M.metal("steel", rough=0.35, dirt=0.4), bevel=0.004)
    # pad-mount transformer
    K.box((0.4 * m / 2 + 0.1, 0.35, 0.45), (0.3 * m, -0.18 * m, 0), st.light_grey, bevel=0.015, base=True)
    KP.sign((0.3 * m, -0.18 * m - 0.18, 0.32), 0.0, "danger", 0.08)
    # nacelle (yawed to face the camera side)
    yaw = math.radians(-20)
    ny = K.pivot("yaw", (0, 0, hub_h), (0, 0, yaw))
    nl = 0.42 * bl
    nh = 0.15 * bl
    parts = [K.box((nl, nh * 0.95, nh), (-nl * 0.35, 0, 0), white, bevel=nh * 0.25, name="nacelle"),
             K.box((nl * 0.6, nh * 0.97, 0.03), (-nl * 0.4, 0, -nh * 0.25), st.accent_m, bevel=0.004),
             K.cyl(rt * 1.05, 0.15 * bl * 0.7, (0, 0, -nh * 0.5 - 0.15 * bl * 0.6), white, verts=24),
             K.box((nl * 0.2, nh * 0.6, nh * 0.25), (-nl * 0.7, 0, nh * 0.55), white, bevel=0.02),
             K.cyl(0.008, 0.25 * nh, (-nl * 0.75, nh * 0.2, nh * 0.6), M.metal("steel"), verts=6)]
    lm, ls = KP.glow_mat((1.0, 0.05, 0.02), 14.0, name="aviation")
    parts.append(K.sphere(0.035 + 0.01 * m, (-nl * 0.7, -nh * 0.1, nh * 0.72), lm, segs=12, rings=8))
    P.anim.blink(ls, 16.0, 0.3, k=1, duty=0.3)
    KP.parent(parts, ny)
    # rotor
    hub = K.pivot("rotor", (nl * 0.18, 0, 0))
    KP.parent([hub], ny)
    rparts = [K.sphere(0.075 * bl, (0.04 * bl, 0, 0), white, segs=24, rings=12, scale=(1.35, 1, 1), name="spinner"),
              K.cyl(0.07 * bl, 0.05 * bl, (-0.03 * bl, 0, 0), white, rot=K.AXES["x"], verts=24, base=True)]
    chord = [0.06, 0.1, 0.085, 0.065, 0.045, 0.03, 0.012]
    zs_ = [0.08, 0.18, 0.35, 0.55, 0.75, 0.92, 1.0]
    prof = [(-0.3 * c * bl, z * bl) for c, z in zip(chord, zs_)] + [(0.7 * c * bl, z * bl) for c, z in reversed(list(zip(chord, zs_)))]
    for k in range(3):
        a = KP.TAU * k / 3
        bp = K.pivot("blade", (0, 0, 0), (a, 0, 0))
        bparts = [K.cyl(0.035 * bl, 0.12 * bl, (0, 0, 0.03 * bl), white, verts=16, bevel=0.003)]
        b = K.prism(prof, 0.022 * bl, (0, 0, 0), white, rot=(0, 0, math.pi / 2 + math.radians(12)), bevel=0.004, name="blade")
        bparts.append(b)
        bparts.append(K.box((0.012, 0.02 * bl, 0.12 * bl), (0, 0, 0.86 * bl), st.paint_m((0.6, 0.06, 0.03), 0.4, name="tip_mark"), bevel=0.002, base=True))
        KP.parent(bparts, bp)
        KP.parent([bp], hub)
    KP.parent(rparts, hub)
    P.anim.spin(hub, turns=1 / 3, axis=(1, 0, 0))
    # framing: rotor disc
    d = V((math.cos(yaw), math.sin(yaw), 0))
    side = V((-math.sin(yaw), math.cos(yaw), 0))
    c = V((0, 0, hub_h)) + d * nl * 0.18
    for k in range(16):
        a = KP.TAU * k / 16
        P.extra.append(tuple(c + side * math.cos(a) * bl * 1.02 + V((0, 0, math.sin(a) * bl * 1.02))))
    P.export_light((-nl * 0.7 * math.cos(yaw), -nl * 0.7 * math.sin(yaw), hub_h + nh * 0.72), (1.0, 0.1, 0.05), 0.5, flicker=True)
    return P.finish(hub_h + bl, frames=16, fps=12)


# --------------------------------------------------------------------------- accumulator
def accumulator(spec, params):
    """Energy storage. Default: battery cabinets with animated charge-level LED bars and an HVAC
    unit. Variants: "lithium" (container ESS), "flywheel" (vacuum flywheel housings with chasing
    LED rings), "smes" (superconducting coil torus in a cryostat with glowing bands)."""
    P = KP.Plant(spec, params, "power", wear=0.6)
    L, S = P.orient_long_x()
    st = P.st
    var = st.variant
    z0 = KP.plinth(P, style="pad")
    m = P.m
    if var == "flywheel":
        s = _clamp(m / 2.0, 0.55, 1.6)
        n = 4 if m >= 1.8 else 2
        pos = [(-0.4, 0.15), (0.2, 0.32), (-0.35, -0.42), (0.25, -0.22)][:n]
        K.box((L * 0.88, S * 0.88, 0.06), (0, 0, z0), st.dark, bevel=0.01, base=True)
        z1 = z0 + 0.06
        for i, (fx, fy) in enumerate(pos):
            p = V((fx * L * 0.85, fy * S * 0.85, z1))
            rr = 0.27 * s
            K.cyl(rr * 1.15, 0.08, p, st.frame, verts=36, bevel=0.008)
            K.cyl(rr, 0.75 * s, p + V((0, 0, 0.08)), st.body, verts=40, bevel=0.012, name="flywheel_housing")
            for k in range(8):
                a = KP.TAU * k / 8
                K.box((0.03, 0.03, 0.72 * s), p + V((math.cos(a) * rr, math.sin(a) * rr, 0.09)), st.frame, rot=(0, 0, a), bevel=0.004, base=True)
            cap_z = 0.08 + 0.75 * s
            K.cyl(rr * 1.05, 0.08, p + V((0, 0, cap_z)), st.accent_m, verts=40, bevel=0.01)
            K.cyl(rr * 0.45, 0.18 * s, p + V((0, 0, cap_z + 0.08)), M.metal("aluminum"), verts=24, bevel=0.008)
            # chasing LED ring (reads as rotation)
            nl = 12
            socks = []
            for k in range(nl):
                a = KP.TAU * k / nl
                lm, ls = KP.glow_mat(st.glow if st.tier >= 3 else (0.2, 1.0, 0.4), 0.3, name="ring_led")
                K.box((0.05, 0.02, 0.012), p + V((math.cos(a) * rr * 0.78, math.sin(a) * rr * 0.78, cap_z + 0.08)), lm, rot=(0, 0, a + math.pi / 2), bevel=0)
                socks.append((ls, k))
            for ls, k in socks:
                P.anim.socket(ls, lambda t, k=k, i=i: 0.3 + 8.0 * max(0.0, 1.0 - (((t * 3 + i * 0.25) * nl - k) % nl) / 3.0))
            KP.sign(p + V((0, -rr - 0.004, 0.45 * s)), 0.0, "warn", 0.1)
        KP.cabinet(P, (L * 0.36, S * 0.3, z0), math.pi / 2, w=0.45 * s, d=0.28, h=0.95 * s)
        return P.finish(z1 + 1.2 * s, frames=12, fps=10)

    if var == "smes":
        s = _clamp(m / 5.0, 0.55, 1.5)
        R = 0.3 * m
        rr = 0.085 * m
        zc = z0 + 0.45 * s + rr
        cry = st.body
        for k in range(8):
            a = KP.TAU * k / 8 + math.pi / 8
            p = V((math.cos(a) * R, math.sin(a) * R, z0))
            K.box((0.25 * s, 0.25 * s, zc - z0 - rr * 0.6), p, st.frame, rot=(0, 0, a), bevel=0.01, base=True)
            K.cyl(0.12 * s, 0.1, p + V((0, 0, 0.05)), KP.frost_mat(), verts=16)
        coil = KP.lathe([(R - rr, -rr * 0.7), (R + rr, -rr * 0.7), (R + rr, rr * 0.7), (R - rr, rr * 0.7)], (0, 0, zc), cry, segs=96, closed=True, name="cryostat")
        glow = []
        for dz in (-rr * 0.35, rr * 0.35):
            gm, gs = KP.glow_mat(st.glow, 6.0, name="smes_band")
            KP.lathe([(R + rr + 0.004, dz - 0.015), (R + rr + 0.004, dz + 0.015)], (0, 0, zc), gm, segs=96, name="band")
            glow.append(gs)
        for k, gs in enumerate(glow):
            P.anim.pulse(gs, 2.0, 9.0, k=1, phase=0.5 * k)
        # cold heads + current leads on top
        for k in range(6):
            a = KP.TAU * k / 6
            p = V((math.cos(a) * R, math.sin(a) * R, zc + rr * 0.7))
            K.cyl(0.08 * s, 0.35 * s, p, M.metal("stainless"), verts=16)
            K.cyl(0.11 * s, 0.08, p + V((0, 0, 0.35 * s)), st.accent_m, verts=16)
        # power conditioning cabinets + cryoplant at the centre
        K.cyl(R - rr - 0.25, 0.9 * s, (0, 0, z0), st.dark, verts=6, bevel=0.02)
        KP.status_leds(P, (0, -(R - rr - 0.25) * 0.86 - 0.005, z0 + 0.7 * s), n=6, seed=4)
        for k in range(3):
            KP.cabinet(P, (L * 0.42, -S * 0.3 + k * 0.6 * s, z0), math.pi / 2, w=0.5 * s, d=0.32, h=1.3 * s, screen=k == 1)
        P.point_light((0, -R, zc + 0.3), st.glow, 20.0 * s, radius=0.5, export=0.6)
        return P.finish(zc + rr * 0.7 + 0.5 * s, frames=12, fps=10)

    s = _clamp(S / 2.0, 0.55, 1.5)
    if var == "lithium":
        # container ESS units
        n = 2 if S >= 2.8 else 1
        ch = 1.3 * s
        top = z0
        for j in range(n):
            y = -S * 0.22 + j * (S * 0.46)
            cw, cd = L * 0.8, _clamp(S * 0.36, 0.8, 1.4)
            K.box((cw, cd, ch), (-L * 0.05, y, z0 + 0.1), st.body, bevel=0.025, base=True, name="container")
            for k in range(int(cw / 0.07)):
                K.box((0.025, cd + 0.02, ch - 0.12), (-L * 0.05 - cw / 2 + 0.05 + k * 0.07, y, z0 + 0.16), st.body, bevel=0.004, base=True)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    K.box((0.1, 0.1, ch + 0.02), (-L * 0.05 + sx * (cw / 2 - 0.04), y + sy * (cd / 2 - 0.04), z0 + 0.09), st.frame, bevel=0.008, base=True)
            K.box((cw, 0.08, 0.06), (-L * 0.05, y - cd / 2, z0 + 0.1), st.frame, bevel=0.005, base=True)
            nd = max(2, int(cw / 0.9))
            for k in range(nd):
                x = -L * 0.05 - cw / 2 + cw * (k + 0.5) / nd
                KP.door(P, (x, y - cd / 2 - 0.01, z0 + 0.22), 0.0, w=cw / nd * 0.8, h=ch * 0.8, mat=st.body)
                _soc_bar(P, (x + cw / nd * 0.3, y - cd / 2 - 0.05, z0 + 0.22 + ch * 0.25), ch * 0.4, phase=k * 0.21 + j * 0.37)
            # HVAC on the +X end
            hx = -L * 0.05 + cw / 2
            K.box((0.3 * s, cd * 0.7, ch * 0.7), (hx + 0.15 * s, y, z0 + 0.25), st.light_grey, bevel=0.02, base=True)
            fo, rot = K.fan((hx + 0.31 * s, y, z0 + 0.25 + ch * 0.35), r=min(0.22 * s, cd * 0.3), axis="x", blades=5)
            P.anim.spin(rot, turns=2 / 5)
            top = max(top, z0 + 0.1 + ch)
        KP.cabinet(P, (L * 0.42, S * 0.38, z0), math.pi / 2, w=0.5 * s, d=0.3, h=1.2 * s)
        return P.finish(top + 0.3, frames=16, fps=10)

    # default battery bank: racks of cells in an open steel frame + HVAC + PCS cabinet
    bw, bd, bh = L * 0.66, _clamp(S * 0.5, 0.7, 1.6), 1.25 * s
    bx, by = -L * 0.1, S * 0.05
    KP.housing(P, (bw, bd, bh), (bx, by, z0), mat=st.body)
    nd = max(2, int(bw / 0.7))
    for k in range(nd):
        x = bx - bw / 2 + bw * (k + 0.5) / nd
        KP.door(P, (x, by - bd / 2, z0 + 0.12), 0.0, w=bw / nd * 0.84, h=bh * 0.78, mat=st.body)
        _soc_bar(P, (x + bw / nd * 0.28, by - bd / 2 - 0.04, z0 + 0.12 + bh * 0.25), bh * 0.42, phase=k * 0.17)
    K.box((bw * 0.6, 0.12, 0.08), (bx, by, z0 + bh + 0.05), M.metal("steel"), bevel=0.006, base=True)
    KP.sign((bx - bw * 0.4, by - bd / 2 - 0.006, z0 + bh * 0.9), 0.0, "danger", 0.12)
    # HVAC unit with fan on the visible +X end
    hx = bx + bw / 2 + 0.22 * s
    K.box((0.4 * s, bd * 0.8, bh * 0.75), (hx, by, z0), st.light_grey, bevel=0.02, base=True)
    fo, rot = K.fan((hx + 0.21 * s, by, z0 + bh * 0.4), r=min(0.2 * s, bd * 0.3), axis="x", blades=5)
    P.anim.spin(rot, turns=2 / 5)
    # PCS / inverter cabinet + cable tray
    KP.cabinet(P, (L * 0.4, -S * 0.32, z0), math.pi / 2, w=0.5 * s, d=0.3, h=1.1 * s)
    KP.cable((bx + bw * 0.3, by - bd / 2, z0 + 0.03), (L * 0.4 - 0.1, -S * 0.32, z0 + 0.03), sag=0.0, r=0.025)
    return P.finish(z0 + bh + 0.3, frames=16, fps=10)


def _soc_bar(P, loc, h, n=6, phase=0.0):
    """Vertical state-of-charge LED bar (front -Y): segments light up in sequence, top one blinks."""
    st = P.st
    loc = V(loc)
    out = [K.box((0.06, 0.012, h + 0.03), loc + V((0, 0.006, h / 2)), M.plastic((0.02, 0.02, 0.022), 0.4), bevel=0.003)]
    socks = []
    for k in range(n):
        col = (0.1, 1.0, 0.3) if k >= 1 else (1.0, 0.4, 0.05)
        if st.tier >= 4:
            col = st.glow
        lm, ls = KP.glow_mat(col, 0.2, name="soc")
        out.append(K.box((0.04, 0.008, h / n * 0.7), loc + V((0, 0, h * (k + 0.5) / n)), lm, bevel=0))
        socks.append((ls, k))
    for ls, k in socks:
        def f(t, k=k):
            lvl = ((t + phase) % 1.0) * (n + 1)
            if k < int(lvl):
                return 6.0
            if k == int(lvl):
                return 6.0 * KP.blink(t, 8, 0.5)
            return 0.15
        P.anim.socket(ls, f)
    return out


# --------------------------------------------------------------------------- gas turbine
def gas_turbine(spec, params):
    """Packaged gas turbine: acoustic enclosure with roof vent fans, filter house with weather hoods,
    exhaust duct + stack, generator enclosure with cooler fans. Variants: "gasifier" (coal
    gasifier + scrubber feeding a stationary gas engine with flywheel), "combined" (adds a heat
    recovery steam generator and stack)."""
    P = KP.Plant(spec, params, "power")
    L, S = P.orient_long_x()
    st = P.st
    var = st.variant
    z0 = KP.plinth(P)
    s = _clamp(S / 2.0, 0.55, 1.5)
    body = st.body
    if var == "gasifier":
        # gasifier vessel (brick lined) at the back-left with coal hopper + poke holes
        gx, gy = -L * 0.3, S * 0.12
        gr = 0.38 * s
        K.cyl(gr * 1.15, 0.3 * s, (gx, gy, z0), _brick(st), verts=32, bevel=0.01)
        K.cyl(gr, 1.5 * s, (gx, gy, z0 + 0.3 * s), body, verts=40, bevel=0.01, name="gasifier")
        for k in range(4):
            K.torus(gr * 1.01, 0.016, (gx, gy, z0 + 0.5 * s + k * 0.35 * s), st.metal("cast_iron"), segs=40, rsegs=6)
        socks = []
        for k in range(3):
            a = math.radians(-70 + k * 40)
            p = V((gx + math.cos(a) * gr, gy + math.sin(a) * gr, z0 + 0.6 * s))
            fm, fs = KP.glow_mat((1.0, 0.45, 0.1), 10.0, base=(0.3, 0.07, 0.01), name="pokehole")
            K.cyl(0.035 * s, 0.05, p, fm, rot=KP._axis_rot(V((math.cos(a), math.sin(a), 0))), verts=12, base=False)
            socks.append((fs, k))
        for fs, k in socks:
            P.anim.socket(fs, lambda t, k=k: 10.0 * (0.75 + 0.25 * math.sin(KP.TAU * (t * 2 + k * 0.33))))
        K.cyl(gr * 0.6, 0.35 * s, (gx, gy, z0 + 1.8 * s), st.metal("cast_iron"), verts=24, r2=gr * 0.9, bevel=0.006)
        K.cyl(gr * 0.9, 0.2 * s, (gx, gy, z0 + 2.15 * s), st.metal("cast_iron"), verts=24, bevel=0.006)
        # scrubber tower + gas main
        sx_, sy_ = -L * 0.02, S * 0.28
        zt, _ = KP.vessel(P, (sx_, sy_, z0), 0.22 * s, 1.5 * s, mat=st.accent_m, legs=0.2 * s, nozzles=1, bands=2)
        K.pipe_run([(gx, gy, z0 + 2.0 * s), (gx, sy_, z0 + 2.0 * s), (sx_, sy_, z0 + 2.0 * s), (sx_, sy_, zt)], r=0.07 * s, mat=st.pipe)
        # flare / vent
        K.cyl(0.04 * s, 0.6 * s, (sx_, sy_, zt - 0.05), st.pipe, verts=12)
        P.emitter((sx_, sy_, zt + 0.6 * s), "smoke" if st.smoke else "steam")
        P.emitter((gx, gy, z0 + 2.4 * s), "smoke" if st.smoke else "steam")
        # gas engine with flywheel + dynamo in front
        ex, ey = L * 0.08, -S * 0.22
        iron = st.metal("cast_iron")
        K.box((1.2 * s, 0.45 * s, 0.3 * s), (ex, ey, z0), iron, bevel=0.015, base=True)
        K.box((0.6 * s, 0.38 * s, 0.45 * s), (ex - 0.25 * s, ey, z0 + 0.3 * s), body, bevel=0.02, base=True, name="engine")
        K.cyl(0.14 * s, 0.35 * s, (ex - 0.25 * s, ey, z0 + 0.75 * s), iron, verts=24, bevel=0.008)
        fly = K.pivot("flywheel", (ex + 0.25 * s, ey - 0.25 * s, z0 + 0.62 * s))
        KP.parent(KP.spoked_wheel(0.5 * s, 0.1 * s, st.paint_m((0.05, 0.05, 0.05), 1.0, name="flywheel_paint"), hub_mat=iron, spokes=6, rim=0.08 * s), fly)
        P.anim.spin(fly, turns=1 / 3, axis=(0, 1, 0))
        K.cyl(0.035 * s, 0.6 * s, (ex + 0.25 * s, ey - 0.35 * s, z0 + 0.62 * s), M.metal("steel"), rot=(-math.pi / 2, 0, 0), verts=12)
        K.cyl(0.24 * s, 0.4 * s, (ex + 0.25 * s, ey + 0.05 * s, z0 + 0.62 * s), st.accent_m, rot=(-math.pi / 2, 0, 0), verts=32, bevel=0.01)
        K.pipe_run([(sx_, sy_ - 0.2 * s, z0 + 0.5 * s), (ex - 0.25 * s, sy_ - 0.2 * s, z0 + 0.5 * s), (ex - 0.25 * s, ey + 0.2 * s, z0 + 0.5 * s)], r=0.05 * s, mat=st.pipe)
        K.scatter_debris(L * 0.85, S * 0.85, 8, seed=9)
        coal = M.plastic((0.015, 0.015, 0.017), 0.6)
        for i in range(16):
            K.sphere(P.rnd.uniform(0.04, 0.08) * s, (-L * 0.42 + P.rnd.uniform(0, 0.4) * s, -S * 0.3 + P.rnd.uniform(0, 0.3) * s, z0 + P.rnd.uniform(0, 0.08)), coal, segs=7, rings=5)
        return P.finish(z0 + 2.5 * s + 0.6 * s, frames=12, fps=10)

    # --- packaged GT
    combined = var == "combined"
    ey = -S * 0.15 if combined else 0.0
    ew = _clamp(S * (0.5 if combined else 0.7), 0.9, 1.8)
    eh = 1.35 * s
    ex0, ex1 = -L * 0.3, L * 0.16
    KP.housing(P, (ex1 - ex0, ew, eh), ((ex0 + ex1) / 2, ey, z0), mat=body)
    for k in range(2):
        KP.door(P, (ex0 + (ex1 - ex0) * (0.3 + 0.4 * k), ey - ew / 2, z0 + 0.1), 0.0, w=0.55 * s, h=eh * 0.75, mat=body, window=True)
    KP.sign((ex0 + (ex1 - ex0) * 0.5, ey - ew / 2 - 0.006, z0 + eh * 0.7), 0.0, "danger", 0.14)
    for k in range(2):
        fx = ex0 + (ex1 - ex0) * (0.25 + 0.5 * k)
        K.cyl(0.24 * s, 0.25 * s, (fx, ey, z0 + eh + 0.05), st.light_grey, verts=32, bevel=0.01)
        fo, rot = K.fan((fx, ey, z0 + eh + 0.3 * s), r=0.2 * s, axis="z", blades=6)
        P.anim.spin(rot, turns=2 / 6, phase=0.2 * k)
    # filter house on stilts above the +X part of the enclosure
    fx0, fx1 = ex1 - (ex1 - ex0) * 0.35, ex1 + 0.1
    fz = z0 + eh + 0.35 * s
    fh = 1.1 * s
    for x in (fx0 + 0.05, fx1 - 0.05):
        for y in (ey - ew / 2 + 0.05, ey + ew / 2 - 0.05):
            K.box((0.07, 0.07, fz - z0 - eh), (x, y, z0 + eh), st.frame, bevel=0.006, base=True)
    fhm = st.light_grey if st.tier >= 2 else body
    K.box((fx1 - fx0, ew + 0.1, fh), ((fx0 + fx1) / 2, ey, fz), fhm, bevel=0.02, base=True, name="filter_house")
    K.box((fx1 - fx0 + 0.08, ew + 0.18, 0.05), ((fx0 + fx1) / 2, ey, fz + fh), st.frame, bevel=0.008, base=True)
    for k in range(2):
        KP.louvre(((fx0 + fx1) / 2, ey - ew / 2 - 0.06, fz + fh * (0.27 + 0.47 * k)), 0.0, (fx1 - fx0) * 0.8, fh * 0.36)
    KP.louvre((fx1 + 0.012, ey, fz + fh * 0.5), math.pi / 2, ew * 0.7, fh * 0.7)
    K.box(((fx1 - fx0) * 0.5, ew * 0.5, fz - z0 - eh), ((fx0 + fx1) / 2, ey, z0 + eh), st.metal("aluminum"), bevel=0.01, base=True, name="inlet_duct")
    # generator enclosure at +X end with cooler fans
    gx0, gx1 = ex1 + 0.15, L * 0.46
    gh = eh * 0.85
    KP.housing(P, (gx1 - gx0, ew * 0.9, gh), ((gx0 + gx1) / 2, ey, z0), mat=st.accent_m if st.tier >= 3 else body)
    fo, rot = K.fan(((gx0 + gx1) / 2, ey, z0 + gh + 0.08), r=min(0.22 * s, (gx1 - gx0) * 0.35), axis="z", blades=5)
    P.anim.spin(rot, turns=2 / 5)
    K.cyl(min(0.24 * s, (gx1 - gx0) * 0.38), 0.08, ((gx0 + gx1) / 2, ey, z0 + gh), st.light_grey, verts=32)
    KP.louvre((gx1 + 0.012, ey, z0 + gh * 0.5), math.pi / 2, ew * 0.5, gh * 0.4)
    # exhaust duct + stack at the -X end (back)
    sx_, sy_ = -L * 0.4, ey + ew * 0.1
    K.box((0.5 * s, ew * 0.8, eh * 0.8), (ex0 - 0.2 * s, ey, z0), st.metal("aluminum", rough=0.5), bevel=0.015, base=True, name="exhaust_duct")
    stack_h = 3.0 * s
    sr = 0.3 * s
    if combined:
        # HRSG: tall casing behind the GT, stack on top
        hx0, hx1 = -L * 0.45, L * 0.05
        hy = S * 0.25
        hw_ = S * 0.38
        hh = 2.4 * s
        K.box((0.6 * s, (hy - ey) + 0.2, eh * 0.7), (ex0 - 0.15 * s, (hy + ey) / 2, z0), st.metal("aluminum", rough=0.5), bevel=0.015, base=True)
        KP.housing(P, (hx1 - hx0, hw_, hh), ((hx0 + hx1) / 2, hy, z0), mat=st.paint_m((0.5, 0.52, 0.53), 0.7, name="hrsg"))
        for k in range(int((hx1 - hx0) / 0.4) + 1):
            K.box((0.06, hw_ + 0.05, hh), (hx0 + k * 0.4, hy, z0), st.frame, bevel=0.005, base=True)
        KP.hdrum(P, ((hx0 + hx1) / 2, hy, z0 + hh), 0.2 * s, (hx1 - hx0) * 0.7, mat=st.accent_m, saddle_h=0.15, nozzles=1)
        sx_, sy_ = hx0 + 0.35 * s, hy
        sz = z0 + hh
        stack_h = 1.8 * s
        K.chimney((sx_, sy_, sz), sr, stack_h, mat=st.paint_m((0.4, 0.42, 0.43), 0.8, name="stack_paint"))
        KP.ladder(P, (hx1 + 0.15, hy - 0.1, z0), hh, math.pi / 2, cage=True)
        top = sz + stack_h
    else:
        sz = z0
        K.cyl(sr * 1.25, 0.3, (sx_, sy_, sz), st.concrete(0.6), verts=24, bevel=0.01)
        K.chimney((sx_, sy_, sz + 0.3), sr, stack_h, mat=st.paint_m((0.4, 0.42, 0.43) if st.tier >= 2 else (0.06, 0.06, 0.06), 0.8, name="stack_paint"))
        K.cyl(sr * 1.25, 0.6 * s, (sx_, sy_, sz + 0.3 + stack_h * 0.55), st.metal("aluminum", rough=0.45), verts=32, bevel=0.01)
        top = sz + 0.3 + stack_h
    P.emitter((sx_, sy_, top + 0.05), "smoke" if st.smoke else "steam")
    # fuel gas skid + control
    K.box((0.6 * s, 0.5 * s, 0.12), (L * 0.36, S * 0.36, z0), st.frame, bevel=0.008, base=True)
    K.pipe_run([(L * 0.3, S * 0.36, z0 + 0.3), (ex1 - 0.2, S * 0.36, z0 + 0.3), (ex1 - 0.2, ey + ew / 2, z0 + 0.3)], r=0.04 * s,
               mat=st.paint_m((0.75, 0.55, 0.02), 0.6, name="gas_pipe"))
    KP.valve((L * 0.36, S * 0.36, z0 + 0.3), "x", r=0.05 * s)
    KP.stack_light(P, (gx1 - 0.15, ey - ew * 0.3, z0 + gh + 0.02), anim="run")
    return P.finish(max(top, fz + fh) + 0.1, frames=16, fps=12)


# --------------------------------------------------------------------------- reactor
def reactor(spec, params):
    """Fission plant block: containment cylinder + dome (concrete base, painted liner shell),
    equipment hatch with glowing viewport, auxiliary building, steam lines, tall vent stack with
    lattice. Core glow pulses (Cherenkov blue / params.glow)."""
    P = KP.Plant(spec, params, "power", wear=0.6)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 5.0, 0.55, 1.5)
    glow = st.glow if st.tier >= 4 else (0.25, 0.55, 1.0)
    cx, cy = -L * 0.12, S * 0.1
    R = 0.3 * m
    wall_h = 2.3 * s
    con = st.concrete(0.4)
    shell = st.paint_m(st.paint, 0.8, name="containment")
    K.cyl(R * 1.08, 0.35 * s, (cx, cy, z0), con, verts=64, bevel=0.02, name="basemat")
    K.cyl(R, wall_h, (cx, cy, z0 + 0.35 * s), shell, verts=64, bevel=0.01, name="containment")
    K.sphere(R, (cx, cy, z0 + 0.35 * s + wall_h), shell, segs=64, rings=24, scale=(1, 1, 0.7), name="dome")
    K.torus(R * 1.01, 0.05 * s, (cx, cy, z0 + 0.35 * s + wall_h), con, segs=64, rsegs=10)
    for k in range(3):
        a = math.radians(-100 + k * 60)
        K.box((0.12 * s, 0.12 * s, wall_h), (cx + math.cos(a) * R, cy + math.sin(a) * R, z0 + 0.35 * s), con, rot=(0, 0, a), bevel=0.01, base=True, name="buttress")
    # glowing ring band + equipment hatch viewport
    gm, gs = KP.glow_mat(glow, 5.0, name="core_band")
    K.torus(R * 1.004, 0.025 * s, (cx, cy, z0 + 0.35 * s + wall_h * 0.82), gm, segs=64, rsegs=8)
    hdir = V((0.35, -1, 0)).normalized()
    hp = V((cx, cy, z0 + 0.35 * s + wall_h * 0.42)) + hdir * R
    K.cyl(0.42 * s, 0.2, hp, con, rot=KP._axis_rot(hdir), verts=40, base=False, bevel=0.02)
    vm, vs = KP.glow_mat(glow, 4.0, base=(0.02, 0.05, 0.1), name="core_view")
    K.cyl(0.3 * s, 0.22, hp + hdir * 0.02, vm, rot=KP._axis_rot(hdir), verts=40, base=False, bevel=0.0)
    K.torus(0.33 * s, 0.03, hp + hdir * 0.13, st.metal("steel"), rot=KP._axis_rot(hdir), segs=40, rsegs=8)
    KP.sign(V((cx, cy, z0 + 0.35 * s + wall_h * 0.7)) + V((-0.45, -1, 0)).normalized() * (R + 0.01), -0.42, "radiation", 0.3 * s)
    P.anim.pulse(gs, 3.0, 8.0, k=1)
    P.anim.pulse(vs, 2.5, 6.5, k=1, phase=0.1)
    lightd = P.point_light(hp + hdir * 0.6, glow, 40.0 * s, radius=0.4, export=1.0)
    P.anim.light(lightd, lambda t: 40.0 * s * (0.75 + 0.25 * KP.wave(t, 1)))
    # personnel airlock
    adir = V((-1, -0.4, 0)).normalized()
    K.cyl(0.18 * s, 0.4 * s, V((cx, cy, z0 + 0.35 * s + 0.4 * s)) + adir * R * 0.95, st.metal("steel"), rot=KP._axis_rot(adir), verts=24, bevel=0.008)
    # auxiliary / turbine building on +X
    ax0, ax1 = L * 0.2, L * 0.47
    ay0, ay1 = -S * 0.42, S * 0.35
    ah = 1.7 * s
    KP.housing(P, (ax1 - ax0, ay1 - ay0, ah), ((ax0 + ax1) / 2, (ay0 + ay1) / 2, z0), mat=st.paint_m((0.55, 0.56, 0.56) if st.tier < 4 else st.paint, 0.7, name="aux_building"))
    for k in range(3):
        KP.louvre(((ax0 + ax1) / 2 - 0.5 + k * 0.5, ay0 - 0.012, z0 + ah * 0.65), 0.0, 0.35 * s, 0.3 * s)
    KP.door(P, (ax1, (ay0 + ay1) / 2, z0 + 0.02), math.pi / 2, w=0.8 * s, h=1.1 * s, mat=st.accent_m)
    K.box((0.6 * s, 0.5 * s, 0.3 * s), (ax0 + 0.5, ay1 - 0.4, z0 + ah), st.light_grey, bevel=0.015, base=True)
    fo, rot = K.fan((ax0 + 0.5, ay1 - 0.4, z0 + ah + 0.32 * s), r=0.18 * s, axis="z", blades=5)
    P.anim.spin(rot, turns=2 / 5)
    KP.stack_light(P, (ax1 - 0.2, ay0 + 0.2, z0 + ah + 0.05), anim="run")
    # steam lines containment -> aux building
    for k in range(2):
        yy = cy - 0.35 * s + k * 0.5 * s
        KP.steam_pipe(P, [(cx + R * 0.95, yy, z0 + 1.2 * s + k * 0.3 * s), (ax0, yy, z0 + 1.2 * s + k * 0.3 * s)], r=0.08 * s)
    # vent stack with lattice (back-right)
    vx, vy = L * 0.18, S * 0.42
    vh = 4.8 * s + wall_h * 0.5
    K.cyl(0.13 * s, vh, (vx, vy, z0), st.paint_m((0.75, 0.75, 0.73), 0.6, name="vent_stack"), verts=24)
    for k in range(4):
        K.cyl(0.135 * s, 0.25, (vx, vy, z0 + vh - 0.3 - k * 0.6), st.paint_m((0.6, 0.06, 0.03), 0.5, name="stack_band"), verts=24)
    KP.lattice_column(P, (vx, vy, z0), vh * 0.75, w=0.45 * s, mat=st.metal("steel", rough=0.4), brace=0.6)
    bl_m, bl_s = KP.glow_mat((1.0, 0.05, 0.02), 12.0, name="obstruction")
    K.sphere(0.04, (vx, vy - 0.14 * s, z0 + vh - 0.1), bl_m, segs=10, rings=6)
    P.anim.blink(bl_s, 14.0, 0.3, k=1, duty=0.3)
    P.emitter((vx, vy, z0 + vh + 0.05), "steam")
    # fence posts / security kerb at the front, transformer
    K.box((0.7 * s, 0.5 * s, 0.6 * s), (-L * 0.38, -S * 0.38, z0), st.light_grey, bevel=0.015, base=True, name="transformer")
    KP.radiator_bank(P, (-L * 0.38, -S * 0.38 - 0.3 * s, z0 + 0.05), 0.6 * s, 0.5 * s, depth=0.1, mat=st.light_grey)
    return P.finish(max(z0 + 0.35 * s + wall_h + R * 0.7, z0 + vh) + 0.1, frames=16, fps=10)


# --------------------------------------------------------------------------- heat exchanger
def heat_exchanger(spec, params):
    """Stacked shell-and-tube exchangers on a steel frame (bolted channel heads on the visible
    end), insulated hot lines, circulation pump; with params.smoke a compact fired superheater
    with glowing burners and stack, else a steam vent."""
    P = KP.Plant(spec, params, "power", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P)
    m = P.m
    s = _clamp(m / 3.0, 0.55, 1.5)
    hl = L * 0.58
    hr = 0.28 * s
    hx = L * 0.06
    hy = -S * 0.18
    shell_m = st.body
    head_m = st.accent_m
    fm = st.frame
    zs = [z0 + 0.25 * s + hr, z0 + 0.25 * s + hr * 3 + 0.18 * s]
    # frame
    for x in (hx - hl * 0.35, hx + hl * 0.3):
        for y in (hy - hr - 0.05, hy + hr + 0.05):
            K.box((0.07, 0.07, zs[1] - z0 + 0.05), (x, y, z0), fm, bevel=0.006, base=True)
        for z in zs:
            K.box((0.08, hr * 2 + 0.2, 0.08), (x, hy, z - hr - 0.08), fm, bevel=0.006, base=True)
    for i, zc in enumerate(zs):
        K.cyl(hr, hl, (hx - hl / 2, hy, zc), shell_m, rot=K.AXES["x"], verts=40, base=True, bevel=0.008, name="shell")
        K.sphere(hr, (hx - hl / 2, hy, zc), shell_m, segs=32, rings=12, scale=(0.5, 1, 1))
        for k in range(2):
            K.torus(hr * 1.005, 0.01, (hx - hl / 2 + hl * (k + 1) / 3, hy, zc), st.metal("steel"), rot=K.AXES["x"], segs=40, rsegs=6)
        # channel head + cover
        K.cyl(hr * 1.02, 0.3 * s, (hx + hl / 2, hy, zc), head_m, rot=K.AXES["x"], verts=40, base=True, bevel=0.008)
        K.cyl(hr * 1.3, 0.05, (hx + hl / 2 + 0.3 * s, hy, zc), head_m, rot=K.AXES["x"], verts=40, base=True, bevel=0.008)
        K.cyl(hr * 1.3, 0.05, (hx + hl / 2 - 0.02, hy, zc), head_m, rot=K.AXES["x"], verts=40, base=True, bevel=0.008)
        K.bolts((hx + hl / 2 + 0.35 * s + 0.002, hy, zc), hr * 1.15, 12, "x", r=0.012, h=0.014)
        # nozzles top / bottom
        K.cyl(0.06 * s, 0.18 * s, (hx + hl / 2 + 0.15 * s, hy - hr - 0.12 * s, zc), head_m, rot=(math.pi / 2, 0, 0), verts=16, base=False)
        K.flange((hx + hl / 2 + 0.15 * s, hy - hr - 0.2 * s, zc), 0.06 * s, "y")
    # insulated hot lines from the shells to the back
    KP.steam_pipe(P, [(hx - hl * 0.3, hy, zs[1] + hr), (hx - hl * 0.3, hy, zs[1] + hr + 0.35 * s), (hx - hl * 0.3, S * 0.3, zs[1] + hr + 0.35 * s),
                      (hx - hl * 0.3, S * 0.3, z0 + 0.2)], r=0.07 * s)
    KP.steam_pipe(P, [(hx + hl * 0.2, hy, zs[0] + hr), (hx + hl * 0.2, hy + hr + 0.2 * s, zs[0] + hr + 0.1),
                      (hx + hl * 0.2, S * 0.35, zs[0] + hr + 0.1)], r=0.06 * s, flanges=True)
    KP.steam_pipe(P, [(hx - hl * 0.1, hy, zs[0] + hr), (hx - hl * 0.1, hy, zs[1] - hr)], r=0.05 * s, flanges=False)
    KP.valve((hx - hl * 0.3, S * 0.05, zs[1] + hr + 0.35 * s), "y", r=0.07 * s)
    # circulation pump
    pv, cpl = KP.pump(P, (-L * 0.32, -S * 0.36, z0), 0.0, s=0.6 * s)
    P.anim.spin(cpl, turns=2.0, axis=(1, 0, 0))
    K.pipe_run([(-L * 0.32 - 0.3 * 0.6 * s, -S * 0.36, z0 + 0.3 * s), (-L * 0.32 - 0.3 * 0.6 * s, -S * 0.36, z0 + 0.9 * s),
                (hx - hl / 2 - hr * 0.5, -S * 0.36, z0 + 0.9 * s), (hx - hl / 2 - hr * 0.5, hy, z0 + 0.9 * s)], r=0.045 * s, mat=st.pipe)
    top = zs[1] + hr + 0.5 * s
    if st.smoke:
        # compact fired superheater at the back
        fx, fy = -L * 0.2, S * 0.28
        fw, fd, fh = 1.0 * s, 0.8 * s, 1.5 * s
        K.box((fw, fd, 0.35 * s), (fx, fy, z0), fm, bevel=0.01, base=True)
        K.box((fw, fd, fh), (fx, fy, z0 + 0.35 * s), st.paint_m((0.12, 0.12, 0.12) if st.tier <= 3 else st.paint, 1.0, name="heater"), bevel=0.02, base=True)
        for k in range(int(fw / 0.25) + 1):
            K.box((0.05, fd + 0.04, fh), (fx - fw / 2 + k * 0.25, fy, z0 + 0.35 * s), fm, bevel=0.005, base=True)
        socks = []
        for k in range(2):
            bx = fx - fw * 0.2 + k * fw * 0.4
            fmat, fs = KP.glow_mat((1.0, 0.45, 0.1), 12.0, base=(0.3, 0.08, 0.01), name="burner")
            K.cyl(0.06 * s, 0.2 * s, (bx, fy, z0 + 0.12 * s), fmat, verts=16)
            K.cyl(0.04 * s, 0.03, (bx, fy - fd / 2 - 0.01, z0 + 0.35 * s + fh * 0.2), fmat, rot=(math.pi / 2, 0, 0), verts=12, base=False)
            socks.append((fs, k))
        for fs, k in socks:
            P.anim.socket(fs, lambda t, k=k: 12.0 * (0.8 + 0.2 * math.sin(KP.TAU * (t * 2 + k * 0.4))))
        P.point_light((fx, fy - 0.1, z0 + 0.15 * s), (1.0, 0.45, 0.12), 25.0 * s, radius=0.25, export=0.8, flicker=True)
        ch = 1.8 * s
        K.chimney((fx + fw * 0.25, fy, z0 + 0.35 * s + fh), 0.14 * s, ch, mat=st.paint_m((0.06, 0.06, 0.06), 1.2, name="stack_paint"))
        P.emitter((fx + fw * 0.25, fy, z0 + 0.35 * s + fh + ch + 0.05), "smoke")
        top = max(top, z0 + 0.35 * s + fh + ch)
    else:
        K.cyl(0.04 * s, 0.7 * s, (hx + hl * 0.35, hy, zs[1] + hr - 0.05), st.pipe, verts=12)
        P.emitter((hx + hl * 0.35, hy, zs[1] + hr + 0.7 * s), "steam")
    KP.gauge((hx + hl / 2 + 0.36 * s, hy + hr * 0.6, zs[0] + hr * 0.9), math.pi / 2, r=0.05)
    KP.cabinet(P, (L / 2 - 0.2, S * 0.15, z0), math.pi / 2, w=0.45 * s, d=0.3, h=1.1 * s)
    KP.stack_light(P, (L / 2 - 0.2, S * 0.15 + 0.12, z0 + 1.1 * s + 0.12), anim="run")
    return P.finish(top, frames=12, fps=10)


# --------------------------------------------------------------------------- cooling tower
def cooling_tower(spec, params):
    """Natural-draft hyperboloid cooling tower: thin concrete shell on diagonal column legs, basin
    with water, coloured band near the rim, inlet pipes and pump house. Static; steam emitters."""
    P = KP.Plant(spec, params, "power", wear=0.6)
    st = P.st
    m = min(P.w, P.d)
    z0 = 0.0
    rb = 0.46 * m
    H = 1.55 * m
    leg_h = 0.11 * H
    rt = 0.31 * m
    rtop = 0.335 * m
    t = 0.035 * m
    con = M.concrete(0.35, tint=(1.35, 1.32, 1.27) if st.tier < 4 else (1.0, 1.0, 1.05))
    # basin
    K.cyl(rb + 0.12, 0.25, (0, 0, z0), con, verts=64, bevel=0.02, name="basin_wall")
    K.cyl(rb + 0.02, 0.012, (0, 0, z0 + 0.2), M.glass((0.3, 0.38, 0.4), 0.02), verts=64, bevel=0, name="water")
    # shell profile (hyperbola-ish) outer up, inner down
    prof_out, prof_in = [], []
    n = 14
    for i in range(n + 1):
        u = i / n
        z = leg_h + (H - leg_h) * u
        zt = 0.72
        if u < zt:
            r = rb + (rt - rb) * math.sin(u / zt * math.pi / 2)
        else:
            r = rt + (rtop - rt) * ((u - zt) / (1 - zt)) ** 1.5
        prof_out.append((r, z))
        prof_in.append((r - t, z))
    shell = KP.lathe(prof_out + list(reversed(prof_in)), (0, 0, z0), con, segs=72, closed=True, name="shell")
    # inner darkening (wet interior)
    KP.lathe([(r - t - 0.005, z) for r, z in prof_in], (0, 0, z0), M.concrete(0.35, tint=(0.35, 0.34, 0.33)), segs=72, name="inner")
    # coloured band near the top
    band = st.paint_m(st.accent, 0.6, name="tower_band")
    zb0 = H * 0.86
    KP.lathe([(rtop * 0.985 + 0.004, zb0), (rtop + 0.004, H - 0.08)], (0, 0, z0), band, segs=72, name="band")
    K.torus(rtop - t / 2, t * 0.7, (0, 0, z0 + H), con, segs=72, rsegs=8)
    # diagonal legs (V pairs)
    nl = 24
    leg_m = M.concrete(0.8, tint=(0.85, 0.83, 0.8))
    for k in range(nl):
        a = KP.TAU * k / nl
        a2 = KP.TAU * (k + 0.5) / nl
        p0 = V((math.cos(a) * (rb - t / 2), math.sin(a) * (rb - t / 2), z0 + 0.2))
        p1 = V((math.cos(a2) * (rb - t / 2), math.sin(a2) * (rb - t / 2), z0 + leg_h + 0.02))
        p2 = V((math.cos(a - KP.TAU / nl * 0.5) * (rb - t / 2), math.sin(a - KP.TAU / nl * 0.5) * (rb - t / 2), z0 + leg_h + 0.02))
        KP.rod(p0, p1, 0.028 * m, leg_m, verts=8)
        KP.rod(p0, p2, 0.028 * m, leg_m, verts=8)
    # fill pack visible through the legs
    K.cyl(rb - 0.1, leg_h * 0.6, (0, 0, z0 + 0.22), M.plastic((0.05, 0.06, 0.06), 0.8), verts=48, bevel=0)
    # aviation lights on the rim
    for k in range(3):
        a = math.radians(-60 + k * 120)
        K.sphere(0.04 + 0.01 * m, (math.cos(a) * rtop, math.sin(a) * rtop, z0 + H + 0.05), M.emissive((1.0, 0.05, 0.02), 10.0), segs=10, rings=6)
    # inlet pipes + pump house on the +X side
    for k in range(2):
        yy = -0.25 * m + k * 0.5 * m * 0.5
        K.pipe_run([(m * 0.5, yy, z0 + 0.35), (rb + 0.05, yy, z0 + 0.35), (rb + 0.05, yy, z0 + 0.15)], r=0.05 * m, mat=st.pipe, flanges=False)
    K.box((0.18 * m, 0.24 * m, 0.16 * m), (m * 0.42, m * 0.35, z0), st.body, bevel=0.02, base=True, name="pump_house")
    K.box((0.2 * m, 0.26 * m, 0.02), (m * 0.42, m * 0.35, z0 + 0.16 * m), st.frame, bevel=0.006, base=True)
    # emitters: plume at the top
    for k in range(3):
        a = KP.TAU * k / 3 + 0.3
        P.emitter((math.cos(a) * rt * 0.45, math.sin(a) * rt * 0.45, z0 + H + 0.1), "steam")
    P.emitter((0, 0, z0 + H + 0.2), "steam")
    return P.finish(z0 + H + 0.1, frames=1, fps=8, still=True)


# --------------------------------------------------------------------------- fusion reactor
def fusion_reactor(spec, params):
    """Tokamak: toroidal vacuum vessel ringed by D-shaped field coils, central solenoid, poloidal
    rings, equatorial ports with pulsing plasma viewports, neutral-beam injector, cryostat base,
    power/cryo cabinets."""
    P = KP.Plant(spec, params, "power", wear=0.4)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 6.0, 0.5, 1.5)
    glow = st.glow
    plasma = (0.85, 0.4, 1.0) if st.tier < 4 else glow
    cx, cy = -L * 0.05, S * 0.06
    R0 = 0.22 * m
    a = 0.1 * m
    zc = z0 + 0.55 * s + a + 0.25 * m * 0.12
    # cryostat base + bioshield ring
    K.cyl(R0 + a + 0.45 * s, 0.4 * s, (cx, cy, z0), st.dark, verts=64, bevel=0.02)
    K.cyl(R0 + a + 0.5 * s, 0.05, (cx, cy, z0 + 0.4 * s), st.accent_m if st.tier < 4 else st.metal("stainless"), verts=64, bevel=0.006)
    # vacuum vessel torus
    vv = st.metal("stainless", rough=0.3)
    K.torus(R0, a, (cx, cy, zc), vv, segs=72, rsegs=24)
    # D-shaped TF coils
    coil_m = st.paint_m(st.paint, 0.5, name="tf_coil")
    ncoil = 12
    R_in = R0 - a - 0.08 * s
    R_out = R0 + a + 0.14 * s
    hD = a + 0.2 * s
    for k in range(ncoil):
        ang = KP.TAU * k / ncoil
        cs, sn = math.cos(ang), math.sin(ang)
        pts = []
        for i in range(25):
            th = math.pi / 2 - math.pi * i / 24
            r = R_in + (R_out - R_in) * math.cos(th)
            pts.append((cx + cs * r, cy + sn * r, zc + hD * math.sin(th)))
        pts.append((cx + cs * R_in, cy + sn * R_in, zc - hD))
        pts.append((cx + cs * R_in, cy + sn * R_in, zc + hD))
        K.tube(pts, 0.055 * s, coil_m)
        # coil outer band glow strip (tier 4)
        if st.hi:
            KP.led_strip((cx + cs * (R_out + 0.05 * s), cy + sn * (R_out + 0.05 * s), zc - 0.12 * s), (cx + cs * (R_out + 0.05 * s), cy + sn * (R_out + 0.05 * s), zc + 0.12 * s), glow, 6.0, r=0.012)
    # central solenoid + PF coils
    K.cyl(R_in - 0.1 * s, hD * 2 + 0.4 * s, (cx, cy, zc - hD - 0.2 * s), st.accent_m, verts=40, bevel=0.01, name="solenoid")
    for k in range(5):
        K.torus(R_in - 0.09 * s, 0.025 * s, (cx, cy, zc - hD + k * hD / 2), st.metal("copper"), segs=40, rsegs=8)
    for dz in (-hD - 0.05 * s, hD + 0.05 * s):
        K.torus(R0 + a * 0.6, 0.05 * s, (cx, cy, zc + dz), coil_m, segs=72, rsegs=10)
    K.torus(R_out + 0.25 * s, 0.045 * s, (cx, cy, zc + hD * 0.6), coil_m, segs=72, rsegs=10)
    K.torus(R_out + 0.25 * s, 0.045 * s, (cx, cy, zc - hD * 0.6), coil_m, segs=72, rsegs=10)
    # equatorial ports with plasma viewports (between coils)
    socks = []
    for k in range(ncoil):
        ang = KP.TAU * (k + 0.5) / ncoil
        d = V((math.cos(ang), math.sin(ang), 0))
        p = V((cx, cy, zc)) + d * (R0 + a * 0.8)
        K.cyl(0.09 * s, 0.35 * s, p, vv, rot=KP._axis_rot(d), verts=20, base=True, bevel=0.004)
        pm, ps = KP.glow_mat(plasma, 8.0, base=(0.05, 0.02, 0.08), name="plasma_port")
        K.cyl(0.065 * s, 0.02, p + d * 0.36 * s, pm, rot=KP._axis_rot(d), verts=20, base=False)
        K.torus(0.09 * s, 0.015 * s, p + d * 0.35 * s, M.metal("dark_steel"), rot=KP._axis_rot(d), segs=20, rsegs=6)
        socks.append((ps, k))
    for ps, k in socks:
        P.anim.socket(ps, lambda t, k=k: 4.0 + 10.0 * (0.5 + 0.5 * math.cos(KP.TAU * (t - k / ncoil))) ** 2)
    # neutral beam injector on the front (-Y), tangential
    nb_dir = V((1, 0.25, 0)).normalized()
    nb_c = V((cx - R0 * 0.3, cy - R0 - a - 1.0 * s, zc))
    nb = K.box((1.3 * s, 0.5 * s, 0.55 * s), nb_c, st.body if st.tier < 4 else st.accent_m, bevel=0.03, name="nbi")
    nb.rotation_euler = (0, 0, math.atan2(nb_dir.y, nb_dir.x))
    K.cyl(0.12 * s, (R0 + a) * 0.6, nb_c + nb_dir * 0.6 * s, vv, rot=KP._axis_rot(nb_dir + V((0, 0.9, 0))), verts=20, base=True)
    for k in range(2):
        K.box((0.12 * s, 0.12 * s, zc - z0 - 0.27 * s), nb_c + nb_dir * (k - 0.5) * 0.9 * s - V((0, 0, zc - z0)), st.frame, bevel=0.008, base=True)
    nm, ns = KP.glow_mat(glow, 4.0, name="nbi_glow")
    K.box((0.4 * s, 0.012, 0.08 * s), nb_c + V((0, -0.255 * s, 0.1 * s)), nm, bevel=0, rot=(0, 0, math.atan2(nb_dir.y, nb_dir.x)))
    P.anim.pulse(ns, 2.0, 7.0, k=2)
    # cryo + power cabinets along the back and side
    for k in range(4):
        KP.cabinet(P, (-L * 0.42 + k * 0.62 * s, S * 0.42, z0), 0.0, w=0.55 * s, d=0.35 * s, h=1.6 * s,
                   paint=st.paint if st.tier >= 3 else None, screen=k % 2 == 0)
    for k in range(2):
        zt, _ = KP.vessel(P, (L * 0.38, S * 0.28 - k * 0.8 * s, z0), 0.25 * s, 1.4 * s, mat=st.paint_m((0.72, 0.73, 0.72), 0.5, name="dewar"), legs=0.25 * s, nozzles=1, bands=0, manway=False)
    K.pipe_run([(L * 0.38, S * 0.28, z0 + 1.4 * s), (cx + R_out, S * 0.28, z0 + 1.4 * s), (cx + R_out, cy, z0 + 1.4 * s)], r=0.05 * s, mat=KP.frost_mat())
    KP.hmi_panel(P, (L * 0.44, -S * 0.35, z0), math.pi / 2, z=1.15 * s)
    KP.stack_light(P, (-L * 0.42, S * 0.42 - 0.2, z0 + 1.6 * s + 0.12), anim="run")
    lightd = P.point_light((cx, cy - R0, zc + 0.2), plasma, 60.0 * s, radius=0.6, export=1.0)
    P.anim.light(lightd, lambda t: 60.0 * s * (0.75 + 0.25 * KP.wave(t, 1)))
    return P.finish(zc + hD + 0.3 * s, frames=16, fps=12)


# --------------------------------------------------------------------------- geothermal plant
def geothermal_plant(spec, params):
    """Geothermal station: production wellheads (stacked master valves) with expansion-looped
    steam lines to a cyclone separator, turbine hall, mechanical-draft cooling cells with spinning
    fans, rock muffler venting steam."""
    P = KP.Plant(spec, params, "power", wear=0.6)
    L, S = P.orient_long_x()
    st = P.st
    z0 = KP.plinth(P, style="pad")
    m = P.m
    s = _clamp(m / 5.0, 0.55, 1.5)
    # wellheads (front-left)
    wells = [(-L * 0.38, -S * 0.36), (-L * 0.14, -S * 0.4)]
    for wx, wy in wells:
        K.box((0.9 * s, 0.9 * s, 0.25 * s), (wx, wy, z0 - 0.2 * s), st.concrete(0.6), bevel=0.01, base=True, name="cellar")
        K.cyl(0.14 * s, 0.25 * s, (wx, wy, z0 + 0.05 * s), st.metal("cast_iron"), verts=24, bevel=0.008)
        z = z0 + 0.3 * s
        for k in range(2):
            K.cyl(0.18 * s, 0.05, (wx, wy, z), st.metal("cast_iron"), verts=24, bevel=0.006)
            K.box((0.22 * s, 0.22 * s, 0.22 * s), (wx, wy, z + 0.05), st.paint_m((0.6, 0.06, 0.03) if k else st.accent, 0.6, name="valve_body"), bevel=0.02, base=True)
            K.cyl(0.03 * s, 0.25 * s, (wx, wy - 0.11 * s, z + 0.16 * s), M.metal("steel"), rot=(math.pi / 2, 0, 0), verts=10, base=True)
            K.torus(0.1 * s, 0.015 * s, (wx, wy - 0.37 * s, z + 0.16 * s), M.painted((0.6, 0.05, 0.02), wear=0.5, name="handwheel"), rot=(math.pi / 2, 0, 0), segs=20, rsegs=6)
            z += 0.32 * s
        K.cyl(0.08 * s, 0.25 * s, (wx, wy, z), st.metal("steel"), verts=16)
        KP.gauge((wx + 0.12 * s, wy - 0.1 * s, z + 0.15 * s), 0.0, r=0.05)
    # steam line with an expansion loop to the separator
    sep = V((-L * 0.33, S * 0.02, z0))
    lz = z0 + 0.75 * s
    pr = 0.07 * s
    for wx, wy in wells:
        KP.steam_pipe(P, [(wx + 0.12 * s, wy, z0 + 0.3 * s + 0.16 * s), (wx + 0.35 * s, wy, z0 + 0.46 * s), (wx + 0.35 * s, wy, lz)], r=0.05 * s, flanges=False)
    loop_x = L * 0.04
    wy0 = wells[0][1]
    KP.steam_pipe(P, [(wells[0][0] + 0.35 * s, wy0, lz), (loop_x - 0.4 * s, wy0, lz), (loop_x - 0.4 * s, wy0, lz + 0.9 * s),
                      (loop_x + 0.4 * s, wy0, lz + 0.9 * s), (loop_x + 0.4 * s, wy0, lz), (loop_x + 0.75 * s, wy0, lz),
                      (loop_x + 0.75 * s, -S * 0.12, lz), (sep.x + 0.45 * s, -S * 0.12, lz), (sep.x + 0.45 * s, sep.y, lz)], r=pr)
    for x in _spread(wells[0][0] + 0.6 * s, loop_x + 0.7 * s, 4):
        K.box((0.12, 0.3 * s, lz - z0 - pr * 1.4), (x, wells[0][1], z0), st.frame, bevel=0.006, base=True)
    zt, _ = KP.vessel(P, sep, 0.4 * s, 1.5 * s, mat=st.paint_m((0.75, 0.75, 0.73) if st.tier >= 3 else st.paint, 0.7, name="separator"), skirt=0.4 * s, bands=3, nozzles=2)
    # turbine hall (+X back)
    hx0, hx1 = L * 0.2, L * 0.47
    hy0, hy1 = -S * 0.2, S * 0.44
    hh = 1.8 * s
    hall = st.paint_m(st.paint, 0.7, name="hall")
    KP.housing(P, (hx1 - hx0, hy1 - hy0, hh), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, z0), mat=hall)
    roof = K.prism([(-(hy1 - hy0) / 2 - 0.08, 0), ((hy1 - hy0) / 2 + 0.08, 0), (0, 0.3 * s)], hx1 - hx0 + 0.12, ((hx0 + hx1) / 2, (hy0 + hy1) / 2, z0 + hh),
                   st.paint_m(st.accent, 0.6, name="roof"), rot=(0, 0, math.pi / 2), bevel=0.01)
    for k in range(3):
        KP.louvre((hx0 + (hx1 - hx0) * (k + 0.5) / 3, hy0 - 0.012, z0 + hh * 0.7), 0.0, 0.4 * s, 0.35 * s)
    KP.door(P, (hx1, (hy0 + hy1) / 2, z0 + 0.02), math.pi / 2, w=1.0 * s, h=1.3 * s, mat=st.accent_m)
    KP.steam_pipe(P, [(sep.x, sep.y, zt - 0.05), (sep.x, sep.y, zt + 0.3 * s), (hx0 - 0.2, sep.y, zt + 0.3 * s), (hx0 - 0.2, (hy0 + hy1) / 2, zt + 0.3 * s),
                      (hx0, (hy0 + hy1) / 2, zt + 0.3 * s)] if zt + 0.3 * s < z0 + hh else
                  [(sep.x, sep.y, zt - 0.05), (sep.x, sep.y, z0 + hh * 0.8), (hx0, sep.y, z0 + hh * 0.8)], r=0.08 * s)
    KP.stack_light(P, (hx1 - 0.15, hy0 + 0.15, z0 + hh + 0.06), anim="run")
    # transformer at the front-right
    tx_, ty_ = L * 0.33, -S * 0.38
    K.box((0.8 * s, 0.55 * s, 0.7 * s), (tx_, ty_, z0), st.light_grey, bevel=0.015, base=True, name="transformer")
    KP.radiator_bank(P, (tx_, ty_ - 0.32 * s, z0 + 0.05), 0.7 * s, 0.55 * s, depth=0.1, mat=st.light_grey)
    for k in range(3):
        KP.insulator((tx_ - 0.25 * s + k * 0.25 * s, ty_, z0 + 0.7 * s), h=0.3 * s, r=0.04 * s)
    KP.sign((tx_ - 0.2 * s, ty_ - 0.28 * s, z0 + 0.5 * s), 0.0, "danger", 0.12)
    # mechanical-draft cooling cells along the back
    cx0, cx1 = -L * 0.46, L * 0.14
    cy_ = S * 0.36
    cd = S * 0.22
    ch = 1.2 * s
    ncell = max(2, int((cx1 - cx0) / (1.0 * s)))
    K.box((cx1 - cx0, cd, ch), ((cx0 + cx1) / 2, cy_, z0), st.paint_m((0.55, 0.57, 0.58), 0.7, name="cooling_cells"), bevel=0.02, base=True)
    for k in range(ncell):
        x = cx0 + (cx1 - cx0) * (k + 0.5) / ncell
        KP.louvre((x, cy_ - cd / 2 - 0.012, z0 + ch * 0.35), 0.0, (cx1 - cx0) / ncell * 0.8, ch * 0.45)
        fr = min(cd * 0.4, (cx1 - cx0) / ncell * 0.4)
        KP.lathe([(fr * 1.05, 0), (fr * 1.08, 0.12 * s), (fr * 1.2, 0.25 * s), (fr * 1.15, 0.25 * s), (fr * 1.02, 0.12 * s), (fr * 1.0, 0)],
                 (x, cy_, z0 + ch), st.paint_m((0.55, 0.57, 0.58), 0.7, name="cooling_cells"), segs=40, name="fan_stack")
        K.cyl(fr * 1.0, 0.01, (x, cy_, z0 + ch + 0.02), M.plastic((0.01, 0.01, 0.01), 0.9), verts=40, bevel=0)
        fo, rot = K.fan((x, cy_, z0 + ch + 0.1 * s), r=fr * 0.95, axis="z", blades=6, housing=False)
        P.anim.spin(rot, turns=2 / 6, phase=0.13 * k)
        P.emitter((x, cy_, z0 + ch + 0.35 * s), "steam")
    # rock muffler venting steam (front, between wells and hall)
    mx, my = L * 0.1, S * 0.1
    K.cyl(0.38 * s, 0.7 * s, (mx, my, z0), st.concrete(0.6), verts=40, bevel=0.02, name="muffler")
    K.cyl(0.3 * s, 0.08, (mx, my, z0 + 0.7 * s), M.metal("dark_steel", rough=0.8), verts=40, bevel=0.004)
    P.emitter((mx, my, z0 + 0.85 * s), "steam")
    return P.finish(max(z0 + hh + 0.3 * s, zt + 0.5 * s, z0 + ch + 0.5 * s) + 0.1, frames=16, fps=12)


# --------------------------------------------------------------------------- substation
def substation(spec, params):
    """Distribution substation: oil transformer with radiator banks + cooling fans (spinning),
    conservator, porcelain HV bushings, a small lattice gantry with insulators and conductors,
    disconnect switch, gravel yard."""
    P = KP.Plant(spec, params, "power", wear=0.7)
    L, S = P.orient_long_x()
    st = P.st
    m = P.m
    s = _clamp(m / 2.0, 0.5, 1.6)
    gravel = M.concrete(2.5, tint=(0.6, 0.58, 0.55))
    K.box((L * 0.98, S * 0.98, 0.05), (0, 0, 0), gravel, bevel=0.01, base=True, name="gravel")
    z0 = 0.05
    K.box((L * 0.6, S * 0.55, 0.12), (-L * 0.05, -S * 0.08, z0), st.concrete(0.6), bevel=0.01, base=True, name="plinth")
    z1 = z0 + 0.12
    tw, td, th = L * 0.38, S * 0.28, 0.75 * s
    tx, ty = -L * 0.08, -S * 0.08
    tank = st.paint_m(st.paint, 0.7, name="transformer")
    K.box((tw, td, th), (tx, ty, z1), tank, bevel=0.015, base=True, name="tank")
    K.box((tw + 0.04, td + 0.04, 0.04), (tx, ty, z1 + th), tank, bevel=0.008, base=True)
    # radiator banks on -Y and +X sides
    KP.radiator_bank(P, (tx, ty - td / 2 - 0.1 * s, z1 + 0.08), tw * 0.85, th * 0.8, depth=0.12 * s, mat=tank, axis="x")
    KP.radiator_bank(P, (tx + tw / 2 + 0.1 * s, ty, z1 + 0.08), td * 0.8, th * 0.8, depth=0.12 * s, mat=tank, axis="y")
    # cooling fans under the -Y radiator
    for k in range(2):
        fx = tx - tw * 0.2 + k * tw * 0.4
        fo, rot = K.fan((fx, ty - td / 2 - 0.25 * s, z1 + th * 0.3), r=0.1 * s, axis="y", blades=5)
        P.anim.spin(rot, turns=2 / 5, phase=0.3 * k)
        K.box((0.04, 0.12 * s, 0.04), (fx, ty - td / 2 - 0.2 * s, z1 + th * 0.3 - 0.11 * s), st.frame, bevel=0.004)
    # conservator tank on brackets
    cz = z1 + th + 0.25 * s
    K.cyl(0.08 * s, tw * 0.6, (tx - tw * 0.3, ty + td * 0.3, cz), tank, rot=K.AXES["x"], verts=24, base=True, bevel=0.006)
    for x in (tx - tw * 0.25, tx + tw * 0.25):
        K.box((0.03, 0.03, 0.25 * s), (x, ty + td * 0.3, z1 + th), st.frame, bevel=0.003, base=True)
    # HV bushings (porcelain) + LV bushings
    bus = []
    for k in range(3):
        bx = tx - tw * 0.3 + k * tw * 0.3
        KP.insulator((bx, ty - td * 0.15, z1 + th), h=0.45 * s, r=0.035 * s)
        bus.append(V((bx, ty - td * 0.15, z1 + th + 0.45 * s)))
        KP.insulator((bx + 0.05, ty + td * 0.2, z1 + th), h=0.18 * s, r=0.025 * s, color=(0.5, 0.5, 0.5))
    # gantry at the back with incoming line insulators
    gy = S * 0.36
    gh = 1.5 * s
    gx0, gx1 = -L * 0.38, L * 0.25
    for x in (gx0, gx1):
        KP.lattice_column(P, (x, gy, z0), gh, w=0.18 * s, mat=st.metal("steel", rough=0.35), brace=0.35 * s)
    K.box((gx1 - gx0 + 0.2, 0.08, 0.1), ((gx0 + gx1) / 2, gy, z0 + gh), st.metal("steel", rough=0.35), bevel=0.006)
    tops = []
    for k in range(3):
        x = tx - tw * 0.3 + k * tw * 0.3
        KP.insulator((x, gy, z0 + gh - 0.32 * s), h=0.32 * s, r=0.03 * s, sheds=5)
        tops.append(V((x, gy, z0 + gh - 0.32 * s)))
    alu = M.metal("aluminum", rough=0.3)
    for a, b in zip(tops, bus):
        KP.cable(a, b, sag=0.08 * s, r=0.008, mat=alu)
    # disconnect switch on post insulators (+X side)
    sx_ = L * 0.35
    for k in range(3):
        y = -S * 0.3 + k * 0.22 * s
        K.box((0.05, 0.05, 0.5 * s), (sx_, y, z0), st.metal("steel"), bevel=0.004, base=True)
        KP.insulator((sx_, y, z0 + 0.5 * s), h=0.25 * s, r=0.025 * s)
        KP.rod((sx_, y, z0 + 0.75 * s), (sx_ - 0.25 * s, y, z0 + 0.75 * s), 0.008, M.metal("copper"))
    KP.sign((tx, ty - td / 2 - 0.006, z1 + th * 0.75), 0.0, "danger", 0.12)
    KP.sign((tx + tw / 2 + 0.006, ty + td * 0.25, z1 + th * 0.75), math.pi / 2, "plate", 0.1)
    lm, ls = KP.glow_mat((0.1, 1.0, 0.25), 6.0, name="sub_led")
    K.box((0.12 * s, 0.08 * s, 0.25 * s), (L * 0.35, S * 0.25, z0), st.light_grey, bevel=0.01, base=True)
    K.cyl(0.01, 0.01, (L * 0.35, S * 0.25 - 0.04 * s - 0.001, z0 + 0.2 * s), lm, rot=K.AXES["-y"], verts=8, base=False)
    P.anim.blink(ls, 7.0, 0.3, k=1, duty=0.7)
    # low perimeter kerb + corner bollards
    for sx in (-1, 1):
        K.cyl(0.04, 0.4 * s, (sx * (L / 2 - 0.08), -S / 2 + 0.08, z0), M.painted((0.8, 0.55, 0.02), wear=0.5, name="bollard"), verts=12)
    return P.finish(z0 + gh + 0.1, frames=12, fps=10)


ARCHETYPES = {
    "boiler": boiler,
    "steam_engine": steam_engine,
    "steam_turbine": steam_turbine,
    "solar_array": solar_array,
    "wind_turbine": wind_turbine,
    "accumulator": accumulator,
    "gas_turbine": gas_turbine,
    "reactor": reactor,
    "heat_exchanger": heat_exchanger,
    "cooling_tower": cooling_tower,
    "fusion_reactor": fusion_reactor,
    "geothermal_plant": geothermal_plant,
    "substation": substation,
}
