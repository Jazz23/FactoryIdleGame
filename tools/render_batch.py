#!/usr/bin/env python3
"""Batch-render building sprites one Blender process per building (resumable), then pack.

    python3 tools/render_batch.py [--quality preview] [--maxframes 8] [--archetypes a,b] [--ids x,y] [--force]
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", default="preview")
    ap.add_argument("--maxframes", default="8")
    ap.add_argument("--archetypes", default="")
    ap.add_argument("--ids", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    specs = json.load(open(os.path.join(ROOT, "data", "buildings.json")))["buildings"]
    arch = set(x for x in a.archetypes.split(",") if x)
    ids = set(x for x in a.ids.split(",") if x)
    todo = [s for s in specs if (not arch or s["visual"]["archetype"] in arch) and (not ids or s["id"] in ids)]
    t0 = time.time()
    for i, s in enumerate(todo):
        meta = os.path.join(ROOT, "art", "render", "buildings", s["id"], "meta.json")
        if not a.force and os.path.exists(meta):
            m = json.load(open(meta))
            if m.get("quality") == a.quality and m.get("batch"):
                continue
        t = time.time()
        r = subprocess.run(["blender", "-b", "-P", os.path.join(ROOT, "art", "blender", "render_buildings.py"), "--",
                            "--ids", s["id"], "--quality", a.quality, "--maxframes", a.maxframes],
                           capture_output=True, text=True)
        ok = os.path.exists(meta) and "[done]" in r.stdout
        if ok:
            m = json.load(open(meta))
            m["batch"] = True
            json.dump(m, open(meta, "w"), indent=1)
            subprocess.run([os.path.join(ROOT, ".venv", "bin", "python"), os.path.join(ROOT, "tools", "pack_sprites.py"), s["id"]],
                           capture_output=True)
        print(f"[{i + 1}/{len(todo)}] {s['id']} ({s['visual']['archetype']}) {'ok' if ok else 'FAILED'} {time.time() - t:.0f}s"
              f" total {(time.time() - t0) / 60:.1f}min", flush=True)
        if not ok:
            print((r.stdout + r.stderr)[-1500:], flush=True)


if __name__ == "__main__":
    sys.exit(main())
