#!/usr/bin/env python3
"""Fail if index.html points at a local asset that isn't in the repo.

The hub is hand-edited, so a renamed or deleted image is the most likely way
to break it. This catches that before it ships.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
html = (ROOT / "index.html").read_text(encoding="utf-8")

refs = set()
for attr in ("src", "href"):
    refs |= set(re.findall(rf'{attr}="(assets/[^"]+)"', html))
refs |= set(re.findall(r"url\((assets/[^)]+)\)", html))

missing = sorted(r for r in refs if not (ROOT / r).is_file())

# Images that exist but nothing references are dead weight in the repo.
referenced_imgs = {r for r in refs if r.startswith("assets/img/")}
on_disk = {
    f"assets/img/{p.name}"
    for p in (ROOT / "assets/img").iterdir()
    if p.suffix in {".webp", ".png", ".jpg", ".svg"}
}
orphans = sorted(on_disk - referenced_imgs)

print(f"checked {len(refs)} asset references")
for o in orphans:
    print(f"  note: unreferenced file {o}")
if missing:
    print("\nMISSING:", file=sys.stderr)
    for m in missing:
        print(f"  {m}", file=sys.stderr)
    sys.exit(1)
print("all references resolve")
