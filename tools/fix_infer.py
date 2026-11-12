#!/usr/bin/env python3
"""Iteratively replace ':=' with '=' on lines Godot reports as un-inferable (Variant) types."""
import re, subprocess, sys, glob
files = sys.argv[1:] or sorted(glob.glob("scripts/**/*.gd", recursive=True))
pat = re.compile(r"(Cannot infer the type|inferred from a Variant value)[\s\S]*?\((res://[^:]+):(\d+)\)")
for it in range(30):
    fixed = 0
    for f in files:
        out = subprocess.run(["godot", "--headless", "--check-only", "--script", f, "--path", "."], capture_output=True, text=True, timeout=120).stderr
        out += subprocess.run(["true"], capture_output=True, text=True).stdout
        for m in pat.finditer(out):
            path = m.group(2).replace("res://", "")
            ln = int(m.group(3)) - 1
            lines = open(path).read().split("\n")
            if ":=" in lines[ln]:
                lines[ln] = lines[ln].replace(":=", "=", 1)
                open(path, "w").write("\n".join(lines))
                fixed += 1
    print("pass", it, "fixed", fixed)
    if fixed == 0:
        break
