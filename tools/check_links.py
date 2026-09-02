#!/usr/bin/env python3
"""Fail if a page points at a local asset that isn't in the repo.

The pages are hand-edited, so a renamed or deleted image is the most likely way
to break them. This catches that before it ships.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ("index.html", "sample.html", "script.html")

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

# Cross-references in prose carry the section id they point at, because
# renumbering has silently broken them three times. Verify the printed number
# still matches the section's own eyebrow.
hub = (ROOT / "index.html").read_text(encoding="utf-8")
numbers = dict(
    (sid, num)
    for sid, num in re.findall(
        r'<section id="([\w-]+)">\s*<div class="eyebrow">(\d\d) · ', hub
    )
)
stale = []
for sid, shown in re.findall(r'<span data-sec="([\w-]+)">(\d\d)</span>', hub):
    real = numbers.get(sid)
    if real is None:
        stale.append(f"  data-sec=\"{sid}\" points at no such section")
    elif real != shown:
        stale.append(f"  {sid} is section {real}, but the text says {shown}")

missing = sorted(r for r in refs if not (ROOT / r).is_file())

# The board and the pilot list point into the production script by scene
# number, and the script page is generated -- so a renumbered scene in the
# document silently orphans those links unless something checks. Every
# data-scenes code and every script.html#anchor has to be an id on the page.
script = (ROOT / "script.html").read_text(encoding="utf-8")
anchors = set(re.findall(r'\sid="([^"]+)"', script))
wanted = set()
for page in PAGES:
    html = (ROOT / page).read_text(encoding="utf-8")
    wanted |= set(re.findall(r'href="script\.html#([^"]+)"', html))
    for codes in re.findall(r'data-scenes="([^"]+)"', html):
        wanted |= set(codes.split(","))
broken = sorted(w for w in wanted if w not in anchors)
if broken:
    print("\nSCRIPT ANCHORS THAT DO NOT EXIST:", file=sys.stderr)
    for b in broken:
        print(f"  #{b}", file=sys.stderr)
    sys.exit(1)

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
if stale:
    print("\nSTALE CROSS-REFERENCES:", file=sys.stderr)
    for x in stale:
        print(x, file=sys.stderr)
    sys.exit(1)
if missing:
    print("\nMISSING:", file=sys.stderr)
    for m in missing:
        print(f"  {m}", file=sys.stderr)
    sys.exit(1)
print(f"all references resolve, {len(re.findall(r'data-sec=', hub))} cross-references check out, "
      f"{len(wanted)} script anchors found")
