#!/usr/bin/env python3
"""Download the CC0 source textures and HDRIs used by the Blender render pipeline.

Sources (all CC0 / public domain):
  * Poly Haven  - https://polyhaven.com
  * ambientCG   - https://ambientcg.com

Files land in art/source/ (git-ignored). Re-run any time; existing files are skipped.

    python3 tools/fetch_assets.py
"""
import io
import json
import os
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "art", "source")
UA = {"User-Agent": "FactoryIdleGame-asset-fetch/1.0"}

RES = "2k"

POLYHAVEN_TEXTURES = [
    "concrete_floor_worn_001",
    "hangar_concrete_floor",
    "rusty_metal_02",
    "metal_plate",
    "metal_grate_rusty",
    "blue_metal_plate",
    "green_metal_rust",
    "rusty_painted_metal",
    "painted_metal_shutter",
]
# Poly Haven map key -> our canonical suffix
PH_MAPS = {"Diffuse": "color", "nor_gl": "normal", "Rough": "rough", "AO": "ao", "Displacement": "disp"}

POLYHAVEN_HDRIS = ["industrial_workshop_foundry", "machine_shop_02", "empty_warehouse_01"]

AMBIENTCG = ["Rubber004", "DiamondPlate008C", "Metal032", "PaintedMetal004", "PaintedMetal006"]
# ambientCG filename fragment -> canonical suffix
ACG_MAPS = {"_Color": "color", "_NormalGL": "normal", "_Roughness": "rough",
            "_AmbientOcclusion": "ao", "_Displacement": "disp", "_Metalness": "metal"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def fetch_polyhaven_texture(name):
    out_dir = os.path.join(SRC, "textures", name)
    files = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
    for key, suffix in PH_MAPS.items():
        dest = os.path.join(out_dir, f"{suffix}.jpg")
        if os.path.exists(dest):
            continue
        try:
            url = files[key][RES]["jpg"]["url"]
        except KeyError:
            continue
        print("  ", name, suffix)
        save(dest, get(url))


def fetch_polyhaven_hdri(name):
    dest = os.path.join(SRC, "hdri", f"{name}_{RES}.hdr")
    if os.path.exists(dest):
        return
    files = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
    print("  ", name)
    save(dest, get(files["hdri"][RES]["hdr"]["url"]))


def fetch_ambientcg(asset_id):
    out_dir = os.path.join(SRC, "textures", asset_id)
    if os.path.exists(os.path.join(out_dir, "color.jpg")):
        return
    print("  ", asset_id)
    data = get(f"https://ambientcg.com/get?file={asset_id}_{RES.upper()}-JPG.zip")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.namelist():
            base = os.path.basename(member)
            if not base.lower().endswith(".jpg"):
                continue
            for frag, suffix in ACG_MAPS.items():
                if frag + "." in base:
                    save(os.path.join(out_dir, f"{suffix}.jpg"), z.read(member))


def main():
    print("Poly Haven textures")
    for n in POLYHAVEN_TEXTURES:
        fetch_polyhaven_texture(n)
    print("Poly Haven HDRIs")
    for n in POLYHAVEN_HDRIS:
        fetch_polyhaven_hdri(n)
    print("ambientCG")
    for n in AMBIENTCG:
        fetch_ambientcg(n)
    print("done ->", SRC)


if __name__ == "__main__":
    sys.exit(main())
