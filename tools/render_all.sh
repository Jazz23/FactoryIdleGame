#!/usr/bin/env bash
# Batch-render every building sprite sheet (resumable) and pack them for Godot.
#   tools/render_all.sh [quality] [--force]
# quality: preview | draft (default) | final
set -euo pipefail
cd "$(dirname "$0")/.."
Q="${1:-draft}"
FORCE="${2:-}"
ids=$(python3 -c "import json;print(' '.join(b['id'] for b in json.load(open('data/buildings.json'))['buildings']))")
n=0; total=$(echo $ids | wc -w)
for id in $ids; do
  n=$((n+1))
  meta="art/render/buildings/$id/meta.json"
  if [[ -z "$FORCE" && -f "$meta" ]] && grep -q "\"quality\": \"$Q\"" "$meta"; then
    continue
  fi
  echo "[$n/$total] $id"
  blender -b -P art/blender/render_buildings.py -- --ids "$id" --quality "$Q" 2>&1 | grep -E "^\[(done|skip)\]|Error|Traceback" || true
  .venv/bin/python tools/pack_sprites.py "$id" || true
done
echo "all done"
