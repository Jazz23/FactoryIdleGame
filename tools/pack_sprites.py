#!/usr/bin/env python3
"""Pack rendered building frames into sprite sheets for Godot.

art/render/buildings/<id>/f_XX.png + meta.json  ->  assets/buildings/<id>.png + <id>.json
                                                    + assets/icons/items/<id>.png (building item icon)

    .venv/bin/python tools/pack_sprites.py            # all rendered buildings
    .venv/bin/python tools/pack_sprites.py id1 id2    # selected

Frames are cropped to the union of their alpha bounding boxes (origin adjusted) so sheets stay
small, then laid out in a grid no wider than 4096 px.
"""
import json
import math
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "art", "render", "buildings")
DST = os.path.join(ROOT, "assets", "buildings")
ICONS = os.path.join(ROOT, "assets", "icons", "items")
MAX_W = 4096


def pack(bid):
    d = os.path.join(SRC, bid)
    meta = json.load(open(os.path.join(d, "meta.json")))
    frames = [Image.open(os.path.join(d, f"f_{i:02d}.png")).convert("RGBA") for i in range(meta["frames"])]
    # union bbox of non-transparent pixels (alpha > 2)
    box = None
    for f in frames:
        b = f.getchannel("A").point(lambda a: 255 if a > 2 else 0).getbbox()
        if b is None:
            continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    if box is None:
        box = (0, 0, frames[0].width, frames[0].height)
    pad = 2
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(frames[0].width, box[2] + pad), min(frames[0].height, box[3] + pad))
    fw, fh = box[2] - box[0], box[3] - box[1]
    n = len(frames)
    cols = max(1, min(n, MAX_W // fw))
    rows = math.ceil(n / cols)
    sheet = Image.new("RGBA", (cols * fw, rows * fh))
    for i, f in enumerate(frames):
        sheet.paste(f.crop(box), ((i % cols) * fw, (i // cols) * fh))
    os.makedirs(DST, exist_ok=True)
    sheet.save(os.path.join(DST, f"{bid}.png"), optimize=True)
    ox, oy = meta["origin"]
    out = {
        "frames": n, "columns": cols, "frame_w": fw, "frame_h": fh, "fps": meta["fps"],
        "origin": [ox - box[0], oy - box[1]], "size": meta["size"], "height": meta["height"],
        "lights": meta.get("lights", []), "emitters": meta.get("emitters", []),
    }
    json.dump(out, open(os.path.join(DST, f"{bid}.json"), "w"), indent=1)
    # building item icon: frame 0 fitted into 256x256
    icon = frames[0].crop(box)
    k = min(240 / icon.width, 240 / icon.height)
    icon = icon.resize((max(1, int(icon.width * k)), max(1, int(icon.height * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (256, 256))
    canvas.alpha_composite(icon, ((256 - icon.width) // 2, (256 - icon.height) // 2))
    os.makedirs(ICONS, exist_ok=True)
    canvas.save(os.path.join(ICONS, f"{bid}.png"), optimize=True)
    kb = os.path.getsize(os.path.join(DST, f"{bid}.png")) // 1024
    print(f"{bid}: {n} frames {fw}x{fh} -> {cols}x{rows} sheet ({kb} KB)")


def main():
    ids = sys.argv[1:] or sorted(x for x in os.listdir(SRC) if os.path.exists(os.path.join(SRC, x, "meta.json")))
    for i in ids:
        pack(i)


if __name__ == "__main__":
    main()
