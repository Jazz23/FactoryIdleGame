"""Building archetype registry.

Every module in this package defines ``ARCHETYPES = {"name": build_fn}``.
``build_fn(spec, params) -> Rig`` where spec is the building dict from data/buildings.json
(``spec["size"] = [w, d]`` footprint in metres, model centred on the origin, ground at z=0) and
params = spec["visual"].get("params", {}).
"""
import importlib
import os
import pkgutil


class Rig:
    """Result of an archetype builder.

    height  - tallest point (m), used for camera framing
    frames  - animation frames in the loop (1 = static)
    fps     - playback rate in game
    update  - callable(t) with t in [0, 1): pose the model for that loop phase
    extra_points - additional world points that must be inside the frame
    lights  - optional list of {"pos": [x, y, z], "color": [r, g, b], "energy": float, "flicker": bool}
              exported to the sprite json so Godot can add matching 2D glow lights
    emitters - optional list of {"pos": [x, y, z], "type": "smoke"|"steam"|"sparks"|"fire"} for Godot particles
    """

    def __init__(self, height, frames=1, fps=12, update=None, extra_points=None, lights=None, emitters=None):
        self.height = height
        self.frames = frames
        self.fps = fps
        self.update = update or (lambda t: None)
        self.extra_points = extra_points or []
        self.lights = lights or []
        self.emitters = emitters or []


ARCHETYPES = {}

for _m in pkgutil.iter_modules([os.path.dirname(__file__)]):
    _mod = importlib.import_module(f"{__name__}.{_m.name}")
    ARCHETYPES.update(getattr(_mod, "ARCHETYPES", {}))
