#!/usr/bin/env python3
"""Fail if a page points at a local asset that isn't in the repo.

The pages are hand-edited, so a renamed or deleted image is the most likely way
to break them. This catches that before it ships.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ("index.html", "sample.html")

refs = set()
for page in PAGES:
    html = (ROOT / page).read_text(encoding="utf-8")
    for attr in ("src", "href"):
        refs |= set(re.findall(rf'{attr}="(assets/[^"]+)"', html))
    refs |= set(re.findall(r"url\((assets/[^)]+)\)", html))
    # A page linking to a sibling page has to find it.
    for link in re.findall(r'href="([\w.-]+\.html)"', html):
        if not (ROOT / link).is_file():
            print(f"\nMISSING: {page} links to {link}", file=sys.stderr)
            sys.exit(1)

missing = sorted(r for r in refs if not (ROOT / r).is_file())

# Images that exist but nothing references are dead weight in the repo.
referenced_imgs = {r for r in refs if r.startswith("assets/img/")}
on_disk = {
    f"assets/img/{p.name}"
    for p in (ROOT / "assets/img").iterdir()
    if p.suffix in {".webp", ".png", ".jpg", ".svg"}
}
orphans = sorted(on_disk - referenced_imgs)

scene = sorted((ROOT / "assets/img/scene").glob("*.jpeg"))
used = len({r for r in refs if "/scene/" in r})
print(f"checked {len(refs)} asset references across {len(PAGES)} pages")
print(f"  scene library: {used} of {len(scene)} frames in play (the rest are held for later)")
for o in orphans:
    print(f"  note: unreferenced file {o}")
if missing:
    print("\nMISSING:", file=sys.stderr)
    for m in missing:
        print(f"  {m}", file=sys.stderr)
    sys.exit(1)
print("all references resolve")
