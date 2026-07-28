# CYOA: The Bioform — Contributor Hub

The single-page hub for *CYOA: The Bioform*, a branching science-fiction film
generated one shot at a time by a distributed group. Nine decision points,
eight endings, roughly 214 shots.

The page is the contributor's whole starting point: the premise, the locked
look, the reference wall, the branch map, all 45 claimable scene chunks, the
pilot shot list, the prompt rubric, and the budget model.

## Running it

It is a static site with no build step and no dependencies. Open `index.html`
directly, or serve the folder if you want the Google Drive embed and relative
paths to behave exactly as they do in production:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

## Layout

```
index.html              the page itself — all copy and markup
assets/css/site.css     all styling (dark theme, custom properties at the top)
assets/js/site.js       scene-board filter, budget calculator, scroll-spy nav
assets/img/             15 reference frames (WebP) + favicon
tools/check_links.py    fails if index.html points at a missing asset
tools/build_standalone.py  folds everything back into one portable HTML file
```

The page was originally authored as one 942 KB file with every image inlined as
base64. Those images are now real files: the HTML dropped to ~175 KB, the 27
image references deduplicated down to 15 actual files, and browser caching and
`loading="lazy"` do something useful now instead of nothing.

## Editing

Content lives in `index.html` as plain markup — edit it directly. A few things
are wired to attributes rather than to code, so keep them intact:

- **Scene board rows** need `data-act` (which act chip shows the row) and
  `data-hay` (the lowercase text the search box matches against). A row missing
  `data-hay` silently stops being searchable.
- **Sidebar links** pair `href="#section-id"` with `data-nav="section-id"`.
  Both must match the `<section id>` or the scroll-spy highlight skips it.
- **Copy buttons** carry their payload in `data-copy`.

Adding an image: drop the file in `assets/img/`, reference it as
`assets/img/name.webp`, and give it a real `alt`. Run `python3
tools/check_links.py` before pushing.

## The portable single-file version

Some contributors want a file rather than a link — something to keep, open
offline, or forward. `tools/build_standalone.py` inlines the CSS, the JS, and
every image back into one document:

```sh
python3 tools/build_standalone.py   # -> dist/cyoa-hub.html (~920 KB)
```

That file works from `file://` with no network and no sibling files. Verified:
all 21 images render, the scene filter and budget calculator both work. The one
thing it cannot carry offline is the Google Drive embed of the performed script
in **The recording** — that stays a live link by nature.

`dist/` is gitignored and rebuilt in CI, so the current bundle is always
downloadable from the deployed site at `/dist/cyoa-hub.html`.

## Deploying

`.github/workflows/deploy.yml` publishes to GitHub Pages on every push to
`main`. It checks asset references and builds the standalone bundle first, so a
broken image reference fails the deploy instead of shipping.

One-time setup: **Settings → Pages → Source → GitHub Actions**.

If the site ends up on a custom domain, set `og:image` in the `<head>` to an
absolute URL — most link-preview crawlers will not resolve the relative path.
