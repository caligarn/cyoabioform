#!/usr/bin/env python3
"""Fold each page into one portable HTML file.

The hub gets handed to contributors who are not always going to open a link --
some want a file they can keep, open on a plane, or forward. This inlines the
stylesheet, the script, and every image so the files in `dist/` work with no
network. Keep the two next to each other: the hub's Play the sample link is a
relative one, so it resolves only when `sample.html` is its sibling.
"""
import base64
import mimetypes
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"

PAGES = {
    "index.html": "cyoa-hub.html",
    "sample.html": "sample.html",
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

    if "assets/" in re.sub(r'content="[^"]*"', "", html):
        raise SystemExit(f"build_standalone: an asset reference was left un-inlined in {page}")
    return html


OUT.mkdir(exist_ok=True)
for page, name in PAGES.items():
    html = inline(page)
    # The hub links to the sample by its dist filename, not its source one.
    html = html.replace('href="sample.html"', f'href="{PAGES["sample.html"]}"')
    (OUT / name).write_text(html, encoding="utf-8")
    print(f"wrote dist/{name} ({len(html) / 1024:.0f} KB)")
