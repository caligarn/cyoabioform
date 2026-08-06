# CYOA: The Bioform — Contributor Hub

The single-page hub for *CYOA: The Bioform*, a branching science-fiction film
generated one shot at a time by a distributed group. Nine decision points,
eight endings, roughly 214 shots.

The hub is the contributor's whole starting point: the premise, the locked look,
the reference wall, the branch map, all 45 claimable scene chunks, the pilot
shot list, the prompt rubric, and the budget model.

`sample.html` is the other half and stands on its own: the film as the viewer
would meet it. Every branch in the script is wired up, so a run through it is a
real run through the graph the branch map draws.

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
index.html              the hub — all copy and markup
sample.html             the playable sample — 28 beats, no hub chrome
assets/css/site.css     hub styling (dark theme, custom properties at the top)
assets/css/sample.css   sample styling — deliberately its own file, shares nothing
assets/js/site.js       scene-board filter, budget calculator, scroll-spy nav
assets/js/sample.js     the sample player
assets/img/             15 reference frames (WebP) + favicon
tools/check_links.py    fails if a page points at a missing asset or sibling page
tools/build_standalone.py  folds each page into one portable HTML file
```

The two pages share images and nothing else. That is on purpose: the sample is
not a section of the hub with the furniture removed, it is the experience, and
keeping its CSS separate stops hub styling from leaking into it.

The hub was originally authored as one 942 KB file with every image inlined as
base64. Those images are now real files: the HTML dropped to ~175 KB, every
image reference across both pages resolves to one of 15 actual files, and
browser caching and `loading="lazy"` do something useful now instead of nothing.

## Editing

Content lives in `index.html` as plain markup — edit it directly. A few things
are wired to attributes rather than to code, so keep them intact:

- **Scene board rows** need `data-act` (which act chip shows the row) and
  `data-hay` (the lowercase text the search box matches against). A row missing
  `data-hay` silently stops being searchable.
- **Sidebar links** pair `href="#section-id"` with `data-nav="section-id"`.
  Both must match the `<section id>` or the scroll-spy highlight skips it.
- **Copy buttons** carry their payload in `data-copy`.
- **Sample beats** live in `sample.html` as `<div class="beat">` panels, one per
  run of footage. Each holds a `.stage` with the stills for that run — the
  player cross-fades them on a loop, so a beat with five stills plays five
  "shots" — and a `.choices` block whose optional `data-label` is the on-screen
  prompt title (`Quick Choice A`, `Decision I.1`, an ending's name). Choices
  point at the next beat with `data-go`. Three targets are not literal beat ids:

  | target | meaning |
  | --- | --- |
  | `$back` | the prompt you just answered — how the fail states loop |
  | `$name` | read the beat id out of state, set by `data-set="name=beat"` |
  | `cut_$act4` | interpolation works mid-string, so one prompt can fork on state |

  `data-kind="fail"` and `data-kind="end"` only change the accent colour.

  Keep the sample bare. The only text in it should be text the film's viewer
  would actually be shown: the prompt title and the options. No scene
  description, no dialogue, no shot IDs — that is what the hub is for.

Adding an image: drop the file in `assets/img/`, reference it as
`assets/img/name.webp`, and give it a real `alt`. Run `python3
tools/check_links.py` before pushing.

Swapping real footage into the sample: a beat's `.stage` holds the placeholder
stills for that run of footage. Replace them with one `<video autoplay muted
playsinline loop>` and delete the `.scrub` bar, which exists only to make a
slideshow read as playback. A local video file gets inlined into the standalone
bundle, so link anything large rather than committing it.

## The portable single-file version

Some contributors want a file rather than a link — something to keep, open
offline, or forward. `tools/build_standalone.py` inlines the CSS, the JS, and
every image, once per page:

```sh
python3 tools/build_standalone.py   # -> dist/cyoa-hub.html, dist/sample.html
```

Both work from `file://` with no network. Verified: every image renders, the
sample plays every branch, and the scene filter and budget calculator both work.
Keep the two files together — the hub's **Play the sample** link is relative, so
it resolves only when `sample.html` is its sibling. Each reference inlines its
own copy of the image, which is why the sample bundle is the bigger of the two.
The one thing neither bundle can carry offline is the Google Drive embed of the
performed script in **The recording** — that stays a live link by nature.

`dist/` is gitignored and rebuilt in CI, so the current bundles are always
downloadable from the deployed site at `/dist/cyoa-hub.html` and
`/dist/sample.html`.

## Deploying

`.github/workflows/deploy.yml` publishes to GitHub Pages on every push to
`main`. It checks asset references and builds the standalone bundle first, so a
broken image reference fails the deploy instead of shipping.

One-time setup: **Settings → Pages → Source → GitHub Actions**.

If the site ends up on a custom domain, set `og:image` in the `<head>` to an
absolute URL — most link-preview crawlers will not resolve the relative path.
