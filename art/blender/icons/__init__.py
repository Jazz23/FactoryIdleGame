"""Item icon archetype registry.

Every module in this package defines ``ARCHETYPES = {"name": build_fn}``.
``build_fn(item, material, color, params) -> Frame`` builds the model at hero scale (largest
dimension ~0.25-0.6 m), centred on the origin and resting on z = 0, and returns its framing.

* item     - the item dict from data/items.json (id, name, kind, group, tier, visual ...)
* material - CONTENT_SCHEMA material name (may be None) -> ``kit_icons.surf`` / ``materials.from_spec``
* color    - optional [r, g, b] tint (linear 0-1)
* params   - visual["params"] dict (archetype specific, all optional)
"""
import importlib
import os
import pkgutil


class Frame:
    """Framing hints returned by an icon builder.

    radius/center - bounding sphere of the model (world units)
    pitch/yaw     - optional product-camera override (degrees, studio.product_camera convention;
                    pitch 58 = 32 deg above the horizon, lower pitch = more top-down)
    fill          - share of the frame the model's projected bbox should fill (default 0.8)
    """

    def __init__(self, radius, center, pitch=None, yaw=None, fill=None):
        self.radius = radius
        self.center = tuple(center)
        self.pitch = pitch
        self.yaw = yaw
        self.fill = fill


def frame(pitch=None, yaw=None, fill=None):
    """Measure the current model and return a Frame (convenience for builders)."""
    import kit_icons as KI
    r, c = KI.bounds()
    return Frame(r, c, pitch, yaw, fill)


ARCHETYPES = {}

for _m in pkgutil.iter_modules([os.path.dirname(__file__)]):
    _mod = importlib.import_module(f"{__name__}.{_m.name}")
    ARCHETYPES.update(getattr(_mod, "ARCHETYPES", {}))
