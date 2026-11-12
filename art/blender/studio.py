"""Shared scene / camera / lighting / render setup for every INDUSTRIUM sprite.

Projection contract (must match the Godot side, see docs/DESIGN.md):
  * orthographic, pitch 60 deg from vertical, yaw 45 deg  ->  2:1 dimetric
  * 1 m ground tile = 128 px wide diamond (PX_PER_M = 128 / sqrt(2))
  * world +X runs screen right-down, world +Y runs screen right-up, +Z is up.
  * key light from the front-left -> lit -Y faces, shadows fall up-right behind objects.
"""
import json
import math
import os

import bpy
from mathutils import Euler, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HDRI_DIR = os.path.join(ROOT, "art", "source", "hdri")
RENDER_DIR = os.path.join(ROOT, "art", "render")

PX_PER_M = 128.0 / math.sqrt(2.0)
ISO_PITCH = math.radians(60.0)
ISO_YAW = math.radians(45.0)
SUN_ELEV = math.radians(52.0)


QUALITY = {
    # samples, adaptive threshold
    "preview": (16, 0.08),
    "draft": (32, 0.05),
    "final": (96, 0.02),
}


def reset(quality="draft", hdri="industrial_workshop_foundry_2k.hdr", hdri_strength=0.3, sun=5.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        import materials
        materials._cache.clear()   # cached datablocks died with the old scene
    except ImportError:
        pass
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    samples, thresh = QUALITY[quality]
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = thresh
    s.cycles.use_denoising = True
    try:
        s.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    s.cycles.max_bounces = 6
    s.cycles.diffuse_bounces = 3
    s.cycles.glossy_bounces = 3
    s.cycles.transmission_bounces = 6
    s.cycles.transparent_max_bounces = 8
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.blur_glossy = 1.0
    s.cycles.sample_clamp_indirect = 8.0
    s.render.threads_mode = "AUTO"
    s.render.film_transparent = True
    s.cycles.film_transparent_glass = True
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    s.render.image_settings.color_depth = "8"
    s.render.image_settings.compression = 40
    s.render.resolution_percentage = 100
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    s.view_settings.exposure = -0.15
    s.render.use_persistent_data = True

    world = bpy.data.worlds.new("world")
    s.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    path = os.path.join(HDRI_DIR, hdri)
    if os.path.exists(path):
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(path, check_existing=True)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(110))
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    else:
        bg.inputs["Color"].default_value = (0.35, 0.37, 0.4, 1)
    bg.inputs["Strength"].default_value = hdri_strength

    if sun > 0:
        add_sun(sun)
    return s


def add_sun(strength=3.2, color=(1.0, 0.93, 0.84), angle=4.0):
    d = bpy.data.lights.new("key", "SUN")
    d.energy = strength
    d.color = color
    d.angle = math.radians(angle)
    o = bpy.data.objects.new("key", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = sun_dir().to_track_quat("-Z", "Y").to_euler()
    return o


def sun_dir():
    """Unit vector the key light travels along (toward the ground).

    Light comes from the viewer's front-left: it lights the -Y faces (screen-left visible face)
    strongly, the +X faces (screen-right visible face) softly, and casts shadows up-right
    (behind objects).
    """
    hx, hy = -0.35, 1.0
    n = math.hypot(hx, hy)
    return Vector((hx / n * math.cos(SUN_ELEV), hy / n * math.cos(SUN_ELEV), -math.sin(SUN_ELEV)))


def iso_basis():
    rot = Euler((ISO_PITCH, 0.0, ISO_YAW), "XYZ").to_matrix()
    right = rot @ Vector((1, 0, 0))
    up = rot @ Vector((0, 1, 0))
    fwd = rot @ Vector((0, 0, -1))
    return right, up, fwd


def shadow_catcher(size=60.0, z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    o = bpy.context.object
    o.name = "shadow_catcher"
    o.is_shadow_catcher = True
    return o


def frame_iso_camera(points, margin_px=12, extra_shadow=True, px_per_m=PX_PER_M):
    """Create an orthographic iso camera framing `points` (world coords, plus their shadow tips).

    Returns dict(width, height, origin=[x, y]) where origin is the pixel of world (0,0,0).
    The world origin always lands on an exact pixel so sprites align with the tile grid.
    """
    right, up, fwd = iso_basis()
    pts = [Vector(p) for p in points]
    if extra_shadow:
        sd = sun_dir()
        for p in list(pts):
            if p.z > 0.01:
                pts.append(p + sd * (p.z / -sd.z))
    xs = [p.dot(right) * px_per_m for p in pts]
    ys = [p.dot(up) * px_per_m for p in pts]
    x0 = math.floor(min(xs)) - margin_px
    x1 = math.ceil(max(xs)) + margin_px
    y0 = math.floor(min(ys)) - margin_px
    y1 = math.ceil(max(ys)) + margin_px
    w, h = x1 - x0, y1 - y0
    # keep even dimensions (nicer for packing / centring)
    w += w % 2
    h += h % 2
    x1, y1 = x0 + w, y0 + h
    cx = (x0 + x1) / 2.0 / px_per_m
    cy = (y0 + y1) / 2.0 / px_per_m
    centre = right * cx + up * cy
    cam_d = bpy.data.cameras.new("iso")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = max(w, h) / px_per_m
    cam_d.clip_start = 0.1
    cam_d.clip_end = 400
    cam = bpy.data.objects.new("iso", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.rotation_euler = Euler((ISO_PITCH, 0.0, ISO_YAW), "XYZ")
    cam.location = centre - fwd * 100.0
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x = w
    s.render.resolution_y = h
    # ortho_scale spans the larger dimension; origin pixel (image y down)
    ox = -x0
    oy = y1  # world y=0 is y1 pixels below the top
    return {"width": w, "height": h, "origin": [int(ox), int(oy)]}


def footprint_points(w, d, h):
    pts = []
    for x in (-w / 2, w / 2):
        for y in (-d / 2, d / 2):
            for z in (0.0, h):
                pts.append((x, y, z))
    return pts


def product_camera(radius=0.5, center=(0, 0, 0), size_px=256, lens=120.0, yaw=35.0, pitch=58.0, fill=0.86):
    """3/4 product-shot camera for item icons (long lens perspective)."""
    s = bpy.context.scene
    s.render.resolution_x = size_px
    s.render.resolution_y = size_px
    cam_d = bpy.data.cameras.new("icon")
    cam_d.lens = lens
    cam_d.sensor_width = 36
    cam = bpy.data.objects.new("icon", cam_d)
    s.collection.objects.link(cam)
    rot = Euler((math.radians(pitch), 0, math.radians(yaw)), "XYZ")
    cam.rotation_euler = rot
    fov = 2 * math.atan(cam_d.sensor_width / (2 * lens))
    dist = radius / math.sin(fov / 2) / fill
    fwd = rot.to_matrix() @ Vector((0, 0, -1))
    cam.location = Vector(center) - fwd * dist
    cam_d.clip_start = dist * 0.1
    cam_d.clip_end = dist * 10
    s.camera = cam
    return cam


def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = bpy.context.scene
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


def load_data(name):
    with open(os.path.join(ROOT, "data", f"{name}.json")) as f:
        return json.load(f)


def cli_args():
    import sys
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else []


def world_to_px(p, px_per_m=PX_PER_M):
    """World point -> pixel offset from the sprite origin (x right, y down)."""
    right, up, _ = iso_basis()
    v = Vector(p)
    return [round(v.dot(right) * px_per_m, 1), round(-v.dot(up) * px_per_m, 1)]
