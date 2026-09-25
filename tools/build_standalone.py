#!/usr/bin/env python3
"""Fold the hub into one portable HTML file.

The hub gets handed to contributors who are not always going to open a link --
some want a file they can keep, open on a plane, or forward. This inlines the
stylesheet, the script, and every image so `dist/cyoa-hub.html` works with no
network.

The production script page bundles the same way to `dist/cyoa-script.html`;
it has no images, so it stays small. The hub's links into it are relative and
stay live, like the sample's.

The sample is deliberately not bundled. It draws on the scene library in
assets/img/scene, and inlining those frames as base64 produced a 29 MB file --
past the point where a single HTML document is a convenient thing to send
someone. Its Play the sample link stays live, the same carve-out the Drive
embed already has.
"""
import base64
import mimetypes
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"

PAGES = {
    "index.html": "cyoa-hub.html",
    "script.html": "cyoa-script.html",
}


def data_uri(rel):
    path = ROOT / rel
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def inline(page):
    html = (ROOT / page).read_text(encoding="utf-8")

    # Stylesheets and scripts become inline blocks.
    for css in re.findall(r'<link rel="stylesheet" href="(assets/[^"]+)">', html):
        text = (ROOT / css).read_text(encoding="utf-8").strip()
        html = html.replace(
            f'<link rel="stylesheet" href="{css}">', f"<style>\n{text}\n</style>"
        )
    for js in re.findall(r'<script src="(assets/[^"]+)" defer></script>', html):
        text = (ROOT / js).read_text(encoding="utf-8").strip()
        html = html.replace(
            f'<script src="{js}" defer></script>', f"<script>\n{text}\n</script>"
        )

    # Everything else that points at a file becomes a data URI.
    html = re.sub(r'(src|href)="(assets/[^"]+)"', lambda m: f'{m.group(1)}="{data_uri(m.group(2))}"', html)
    html = re.sub(r"url\((assets/[^)]+)\)", lambda m: f"url({data_uri(m.group(1))})", html)

    # Only attribute-shaped references count. Prose is allowed to name a path --
    # section 12 tells contributors where to drop files -- and a bare substring
    # search flags that as a missed asset.
    # A reference always sits right after ="  or  ( . Prose never does, and the
    # page's copy does name a path -- section 12 tells contributors where to drop
    # files. Matching the punctuation rather than the attribute name keeps this
    # broader than the inliner above, so a shape it does not handle still trips.
    # og:image stays a relative path on purpose -- crawlers want a URL, not a data
    # URI -- so meta content is excluded, exactly as the original check did.
    scanned = re.sub(r'content="[^"]*"', "", html)
    missed = re.findall(r'(?:="|\()assets/[^"\')]+', scanned)
    if missed:
        raise SystemExit(
            f"build_standalone: {len(missed)} asset reference(s) left un-inlined in {page}: "
            + ", ".join(missed[:3]))
    return html


OUT.mkdir(exist_ok=True)
for page, name in PAGES.items():
    html = inline(page)
    (OUT / name).write_text(html, encoding="utf-8")
    print(f"wrote dist/{name} ({len(html) / 1024:.0f} KB)")
