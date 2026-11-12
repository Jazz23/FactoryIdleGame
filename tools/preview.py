#!/usr/bin/env python3
"""Composite rendered frames onto a floor backdrop for quick visual review.

.venv/bin/python tools/preview.py OUT.png path/to/frame.png [more.png ...] [--scale 2] [--bg floor|grey]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    args = sys.argv[1:]
    scale = 1.0
    bg = "floor"
    if "--scale" in args:
        i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
    if "--bg" in args:
        i = args.index("--bg"); bg = args[i + 1]; del args[i:i + 2]
    out, frames = args[0], args[1:]
    ims = [Image.open(f).convert("RGBA") for f in frames]
    W = sum(i.width for i in ims) + 20 * (len(ims) + 1)
    H = max(i.height for i in ims) + 40
    floor = os.path.join(ROOT, "assets", "env", "floor_tile.png")
    if bg == "floor" and os.path.exists(floor):
        tile = Image.open(floor).convert("RGBA")
        canvas = Image.new("RGBA", (W, H))
        for y in range(0, H, tile.height):
            for x in range(0, W, tile.width):
                canvas.paste(tile, (x, y))
    else:
        canvas = Image.new("RGBA", (W, H), (92, 92, 90, 255))
    x = 20
    for im in ims:
        canvas.alpha_composite(im, (x, 20))
        x += im.width + 20
    if scale != 1.0:
        canvas = canvas.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    canvas.convert("RGB").save(out)


if __name__ == "__main__":
    main()
