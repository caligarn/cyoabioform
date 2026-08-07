# CYOA: The Bioform — Contributor Hub

The single-page hub for *CYOA: The Bioform*, a branching science-fiction film
generated one shot at a time by a distributed group. Nine decision points,
eight endings, about 188 setups cutting to roughly 361 shots.

The hub is the contributor's whole starting point: the premise, the locked look,
the reference wall, the branch map, all 45 claimable scene chunks, the pilot
shot list, the prompt rubric, and the budget model.

Counts come in three units and they are not interchangeable. A **setup** is one
camera position with its own start frame — the claimable unit. A **roll** is one
generation attempt from a setup — the cost unit, and what the budget calculator
multiplies. A **cut shot** is one appearance of a setup in the edit — the runtime
unit. Coverage reuses setups, which is why the finished film has roughly twice as
many cut shots as setups without costing twice as much. Section 13 derives all
three and states its error bar; every number is provisional until chunks come back
finished.

`sample.html` is the other half and stands on its own: the film as the viewer
would meet it. Every branch in the script is wired up, so a run through it is a
real run through the graph the branch map draws — and it plays the actual
frames, in shot order, so the branch you pick changes what you see.

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
assets/img/scene/       149 frames generated from the script — the sample's library
assets/img/scene/full/  the full-resolution originals of a handful of those
tools/check_links.py    fails if a page points at a missing asset or sibling page
tools/build_standalone.py  folds each page into one portable HTML file
```

The two pages share images and nothing else. That is on purpose: the sample is
not a section of the hub with the furniture removed, it is the experience, and
keeping its CSS separate stops hub styling from leaking into it.

The hub was originally authored as one 942 KB file with every image inlined as
base64. Those images are now real files, which is what makes browser caching and
`loading="lazy"` do something useful, and what lets the sample draw on a 30 MB
frame library without either page paying for it up front.

## Editing

Content lives in `index.html` as plain markup — edit it directly. A few things
are wired to attributes rather than to code, so keep them intact:

- **Scene board rows** need `data-act` (which act chip shows the row) and
  `data-hay` (the lowercase text the search box matches against). A row missing
  `data-hay` silently stops being searchable. The two numeric columns are Setups
  and Cut shots, in that order; `tools/coverage.py` regenerates both from the
  chunk descriptions and prints the totals the prose quotes.
- **Sidebar links** pair `href="#section-id"` with `data-nav="section-id"`.
  Both must match the `<section id>` or the scroll-spy highlight skips it.
- **Copy buttons** carry their payload in `data-copy`.
- **Lane cards** in section 03 carry `data-lane` and `data-task`. The compose
  box builds its picker from them, so adding a lane card is all it takes to add
  a lane — but the card's own `mailto:` is hardcoded in the markup on purpose,
  so every lane is still reachable with JavaScript off.
- **Cross-references in prose** wrap their number in `<span data-sec="budget">17</span>`.
  `check_links.py` verifies the printed number still matches that section's own
  eyebrow and fails if it does not — renumbering silently broke these three
  times before the check existed. Write new ones the same way.
- **Sample beats** live in `sample.html` as `<div class="beat">` panels, one per
  run of footage. Each holds a `.stage` with that run's frames **in shot
  order** — the player cross-fades them on a loop, so a beat with five frames
  plays five shots — and a `.choices` block whose optional `data-label` is the
  on-screen prompt title (`Quick Choice A`, `Decision I.1`, an ending's name).
  Frames come from `assets/img/scene/`; 84 of the 149 are in play and the rest
  are held for beats that do not exist yet. Only the first beat's frames load
  up front — the player warms the frames of every beat you could reach next, so
  the cut stays instant without pulling 30 MB at once. Choices point at the
  next beat with `data-go`. Three targets are not literal beat ids:

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

Swapping motion into the sample: a beat's `.stage` holds that run's frames.
Replace them with one `<video autoplay muted playsinline loop>` and delete the
`.scrub` bar, which exists only to make a sequence of frames read as playback.

## The portable single-file version

Some contributors want a file rather than a link — something to keep, open
offline, or forward. `tools/build_standalone.py` inlines the CSS, the JS, and
every image into one document:

```sh
python3 tools/build_standalone.py   # -> dist/cyoa-hub.html (~1.2 MB)
```

It works from `file://` with no network. Verified: every image renders, and the
scene filter and budget calculator both work.

The sample is deliberately not bundled. Inlining its 84 frames as base64 made a
29 MB file, past the point where a single HTML document is a convenient thing to
send someone, so **Play the sample** stays a live link in the portable file —
the same carve-out the Google Drive embed of the performed script already has.

`dist/` is gitignored and rebuilt in CI, so the current bundle is always
downloadable from the deployed site at `/dist/cyoa-hub.html`.

## Deploying

`.github/workflows/deploy.yml` publishes to GitHub Pages on every push to
`main`. It checks asset references and builds the standalone bundle first, so a
broken image reference fails the deploy instead of shipping.

One-time setup: **Settings → Pages → Source → GitHub Actions**.

If the site ends up on a custom domain, set `og:image` in the `<head>` to an
absolute URL — most link-preview crawlers will not resolve the relative path.
