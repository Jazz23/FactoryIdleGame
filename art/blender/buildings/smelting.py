"""Smelting archetypes: burner_furnace (reference model for the art style)."""
import math
import random

import bpy
from mathutils import Vector

import kit as K
import materials as M
from buildings import Rig


def _flicker_material(color, strength):
    m = bpy.data.materials.new("fire")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = strength
    return m, p.inputs["Emission Strength"]


def _point_light(loc, color, energy, radius=0.15):
    d = bpy.data.lights.new("glow", "POINT")
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new("glow", d)
    K.collection().objects.link(o)
    o.location = Vector(loc)
    return d


def burner_furnace(spec, p):
    w, d = spec.get("size", [2, 2])
    paint = tuple(p.get("paint", (0.035, 0.036, 0.04)))
    tier = p.get("tier", 1)
    skid, z = K.skid(w * 0.96, d * 0.96, 0.14)
    body_w, body_d, body_h = w * 0.62, d * 0.62, 1.15
    casing = M.painted(paint, wear=0.75, grime=0.95, rough=0.6, under="cast_iron", name="furnace_casing")
    brick = M.painted((0.018, 0.017, 0.016), wear=0.3, grime=1.0, rough=0.8, rust=0.5, name="soot_plate")
    cx, cy = -0.05 * w, 0.05 * d
    base = Vector((cx, cy, z))
    K.box((body_w, body_d, body_h), base, casing, bevel=0.03, base=True, name="casing")
    # angle-iron corners and tie bands
    angle = M.metal("cast_iron", dirt=1.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            K.box((0.07, 0.07, body_h + 0.04), base + Vector((sx * body_w / 2, sy * body_d / 2, 0)), angle, bevel=0.008, base=True)
    for hz in (0.25, 0.8):
        K.box((body_w + 0.03, body_d + 0.03, 0.05), base + Vector((0, 0, body_h * hz)), angle, bevel=0.008, base=True)
    # refractory brick crown
    K.box((body_w * 0.86, body_d * 0.86, 0.16), base + Vector((0, 0, body_h)), brick, bevel=0.02, base=True)
    # firebox mouth on the -Y face (lit side) with glowing coals
    mouth_w, mouth_h = body_w * 0.42, body_h * 0.34
    mz = z + body_h * 0.32
    front = cy - body_d / 2
    K.box((mouth_w + 0.12, 0.06, mouth_h + 0.1), (cx, front - 0.02, mz + mouth_h / 2), angle, bevel=0.01)
    K.box((mouth_w, 0.08, mouth_h), (cx, front - 0.03, mz + mouth_h / 2), M.plastic((0.01, 0.008, 0.006), 0.9), bevel=0.004)
    fire_mat, fire_strength = _flicker_material((1.0, 0.36, 0.05), 18.0)
    coals = M.molten((1.0, 0.42, 0.08), 10.0, 6.0)
    K.box((mouth_w * 0.9, 0.1, mouth_h * 0.35), (cx, front - 0.02, mz + mouth_h * 0.18), coals, bevel=0.01)
    K.box((mouth_w * 0.92, 0.01, mouth_h * 0.7), (cx, front + 0.03, mz + mouth_h * 0.55), fire_mat, bevel=0)
    # hinged door swung open
    door = K.box((mouth_w * 0.95, 0.04, mouth_h * 1.05), (0, 0, 0), casing, bevel=0.01)
    door.location = (cx - mouth_w / 2 - mouth_w * 0.42, front - 0.25, mz + mouth_h / 2)
    door.rotation_euler = (0, 0, math.radians(-62))
    K.cyl(0.02, 0.18, (cx - mouth_w * 0.75, front - 0.42, mz + mouth_h * 0.45), M.metal("steel"), rot=K.AXES["x"], verts=10)
    # ash tray / grate slot
    K.box((mouth_w * 0.8, 0.12, 0.05), (cx, front - 0.08, mz - 0.1), M.tread_plate(1.5, rust=True), bevel=0.006)
    # coal hopper on +X side
    hop = M.painted((0.32, 0.16, 0.02), wear=0.6, grime=0.8, rust=0.35, name="hopper_paint")
    hx = cx + body_w / 2 + 0.22
    K.prism([(-0.25, 0.0), (0.25, 0.0), (0.38, 0.45), (-0.38, 0.45)], 0.55, (hx + 0.05, cy - 0.05, z + 0.62), hop,
            rot=(0, 0, math.pi / 2), bevel=0.012, name="hopper")
    coal = M.plastic((0.015, 0.015, 0.017), 0.6)
    rnd = random.Random(3)
    for i in range(22):
        K.sphere(rnd.uniform(0.04, 0.07), (hx + 0.05 + rnd.uniform(-0.22, 0.22), cy - 0.05 + rnd.uniform(-0.2, 0.2), z + 1.07 + rnd.uniform(-0.02, 0.02)),
                 coal, segs=7, rings=5, scale=(1, 0.9, 0.7))
    K.box((0.16, 0.2, 0.62), (hx - 0.12, cy - 0.05, z), hop, bevel=0.01, base=True)
    # chimney on back corner
    ch_pos = Vector((cx - body_w * 0.22, cy + body_d * 0.22, z + body_h + 0.1))
    K.chimney(ch_pos, 0.16, 1.9, mat=M.painted((0.025, 0.024, 0.022), wear=0.4, grime=1.0, rough=0.75, rust=0.6, name="stack"))
    # gauge + pipe
    K.pipe_run([(cx + body_w / 2, cy - body_d * 0.3, z + 0.9), (cx + body_w / 2 + 0.2, cy - body_d * 0.3, z + 0.9),
                (cx + body_w / 2 + 0.2, cy - body_d * 0.3, z + 0.12)], r=0.035)
    K.cyl(0.06, 0.03, (cx + body_w * 0.2, front - 0.01, z + body_h * 0.82), M.plastic((0.9, 0.9, 0.88)), rot=K.AXES["-y"], verts=24)
    K.torus(0.06, 0.008, (cx + body_w * 0.2, front - 0.025, z + body_h * 0.82), M.metal("brass"), rot=K.AXES["y"])
    K.beacon((cx + body_w * 0.35, cy + body_d * 0.3, z + body_h + 0.16), (1.0, 0.5, 0.05), on=True)
    K.scatter_debris(w * 0.9, d * 0.9, 6, seed=1, mat=coal)
    if tier >= 2:
        K.control_cabinet((cx + body_w / 2 + 0.3, cy + body_d * 0.25, z), rot_z=math.pi / 2, w=0.4, d=0.25, h=0.9)

    light = _point_light((cx, front - 0.25, mz + mouth_h * 0.4), (1.0, 0.45, 0.12), 60.0)
    rnd2 = random.Random(7)
    phases = [rnd2.random() for _ in range(4)]

    def update(t):
        f = 0.75 + 0.25 * (0.5 + 0.5 * math.sin(2 * math.pi * (t * 2 + phases[0]))) * (0.7 + 0.3 * math.sin(2 * math.pi * (t * 3 + phases[1])))
        fire_strength.default_value = 18.0 * f
        light.energy = 60.0 * f

    return Rig(height=z + body_h + 0.1 + 1.9, frames=12, fps=10, update=update,
               lights=[{"pos": [cx, front - 0.3, mz], "color": [1.0, 0.5, 0.15], "energy": 1.0, "flicker": True}],
               emitters=[{"pos": [ch_pos.x, ch_pos.y, ch_pos.z + 1.9], "type": "smoke"}])


ARCHETYPES = {"burner_furnace": burner_furnace}
