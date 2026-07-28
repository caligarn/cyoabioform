#!/usr/bin/env python3
"""Fold the site back into one portable HTML file.

The hub gets handed to contributors who are not always going to open a link --
some want a file they can keep, open on a plane, or forward. This inlines the
stylesheet, the script, and every image so `dist/cyoa-hub.html` works with no
network and no sibling files.
"""
import base64
import mimetypes
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "cyoa-hub.html"

html = (ROOT / "index.html").read_text(encoding="utf-8")


def data_uri(rel):
    path = ROOT / rel
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


# Stylesheet and script become inline blocks.
css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8").strip()
js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8").strip()
html = html.replace(
    '<link rel="stylesheet" href="assets/css/site.css">', f"<style>\n{css}\n</style>"
)
html = html.replace(
    '<script src="assets/js/site.js" defer></script>', f"<script>\n{js}\n</script>"
)

# Everything else that points at a file becomes a data URI.
html = re.sub(r'(src|href)="(assets/[^"]+)"', lambda m: f'{m.group(1)}="{data_uri(m.group(2))}"', html)
html = re.sub(r"url\((assets/[^)]+)\)", lambda m: f"url({data_uri(m.group(1))})", html)

if "assets/" in re.sub(r'content="[^"]*"', "", html):
    raise SystemExit("build_standalone: an asset reference was left un-inlined")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(html) / 1024:.0f} KB)")
