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
many cut shots as setups without costing twice as much. Section 15 derives all
three and states its error bar; every number is provisional until chunks come back
finished.

The film is budgeted at **$5,000 of generation** — the gen-AI spend and nothing
else. Hosting, key art, the trailer, festivals, press and any launch push sit
outside it, costed separately in section 20 at roughly another $10,000. Divided
by the provisional 695 rolls that $5,000 is $6.26 a roll, which is also the break-even: below it the film fits, above it something
gives. Published rates put a roll at $0.80 to $3.20, so the target holds with
roughly 2x headroom. Section 19 is built around the target rather than around a
rate, and its calculator ends with a fits/does-not-fit verdict.

`script.html` is the production script as a page. It is generated from the
document in `script/`, and every branch, scene and viewer prompt in it has an
anchor, so the scene board can point at the exact beat a chunk covers.

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
script.html             the current script as a page — GENERATED, do not edit
sample.html             the playable sample — 28 beats, no hub chrome
script/versions.json    the version log: which script is current, what came before
script/versions/        every version, dated, as the file it arrived as
script/production-script.json  the current script as data — GENERATED
assets/css/site.css     hub styling (dark theme, custom properties at the top)
assets/css/script.css   screenplay layout and markers, on top of site.css
assets/css/sample.css   sample styling — deliberately its own file, shares nothing
assets/js/site.js       scene-board filter, budget calculator, scroll-spy nav
assets/js/script.js     the script page's scroll-spy, nothing else
assets/js/sample.js     the sample player
assets/img/             15 reference frames (WebP) + favicon
assets/img/scene/       149 frames generated from the script — the sample's library
assets/img/scene/full/  the full-resolution originals of a handful of those
tools/build_script.py   turns the .docx into script.html and the JSON
tools/check_links.py    fails if a page points at a missing asset, sibling page
                        or script anchor
tools/build_standalone.py  folds each page into one portable HTML file
```

The two pages share images and nothing else. That is on purpose: the sample is
not a section of the hub with the furniture removed, it is the experience, and
keeping its CSS separate stops hub styling from leaking into it.

The hub was originally authored as one 942 KB file with every image inlined as
base64. Those images are now real files, which is what makes browser caching and
`loading="lazy"` do something useful, and what lets the sample draw on a 30 MB
frame library without either page paying for it up front.

## The production script

The script lives in `script/versions/`, one dated file per version, and
`script/versions.json` is the log that says which one is current. The current
document is the source of truth for the story. It names its parts, and the
rest of the site keys off those names:

| in the document | what it is | example |
| --- | --- | --- |
| a bold bracketed heading | a **branch**: one path through the story. Act, decision, option taken. | `[II.2-A: Reason with The Bioform]` |
| a number, a letter and a tab | a **scene**: one slug line. Sequence, then slug within it. | `2E	INT. OPS DECK – CONTINUOUS` |
| a bold line starting DECISION, QUICK CHOICE, FINAL PROTOCOL | a **viewer prompt** | `DECISION II.2:` |
| THE END | an ending | `THE END (of this branch)` |
| TRY AGAIN? | a fail state that loops back | `ON SCREEN: TRY AGAIN?` |

`tools/build_script.py` reads the document with nothing but the standard
library and writes two files. `script.html` is the script as a page in the
hub's own styling, with an anchor per branch (`#br-II.2-A`), per scene
(`#2E`) and per prompt (`#d-3C`, named for the scene it appears in).
`script/production-script.json` is the same content as data: branches, scenes,
speeches grouped by character, and lists of every prompt, ending and fail
state.

```sh
python3 tools/build_script.py           # rebuild both after editing the document
python3 tools/build_script.py --check   # what CI runs: fails if either is stale
```

Edit the document, then rebuild and commit all three. The page is generated,
so a hand edit to `script.html` is lost on the next build and fails the CI
check.

### Versions

Every version is kept, never overwritten. The page says at the top which
version it is (the version date, not the build date) and lists every earlier
version at the end, each as the file it arrived as, with a link to its Drive
source. Today the log holds:

| date | what | kept as |
| --- | --- | --- |
| 2026-09-02 | Production script, the current version | `.docx`, built into `script.html` |
| 2026-04-06 | Shooting script (Google Doc, exported) | `.pdf` |
| 2025-10-13 | Draft 3, the text the recording was performed from | `.pdf` |

To add a version: drop the dated file in `script/versions/`
(`YYYY-MM-DD_Name.ext`), add an entry at the top of `script/versions.json`
with the date, title, file, format, source link and a note on what changed,
then rebuild. The newest `.docx` becomes the current page; every earlier
`.docx` gets its own archived page at `script/versions/<date>.html`, marked as
superseded, so it can be read the same way. PDFs are linked as files.
`check_links.py` fails if the log names a file that is not in the repo.

Two things worth knowing when the document changes:

- **Scene numbers are addresses.** Each scene board row carries
  `data-scenes="2F,2G"` and links its ID to the first of them; the pilot rows
  link each shot to its scene. `check_links.py` fails if a code no longer
  exists on the script page, so renumbering the document shows up as a red
  check rather than a dead link.
- **The document reuses one code.** Both *Free the Bioform* and *You are now
  Priya* are headed `V.1`. The page keeps them apart as `#br-V.1` and
  `#br-V.1-2` in document order, and the board already calls the Priya
  transfer V.1 and the Kaz transfer V.2. Renaming the second one in the
  document would remove the special case.

The page shows shouted headings in sentence case and leaves the document's
typos alone; the JSON keeps the document's own text.

## Editing

Content lives in `index.html` as plain markup — edit it directly. A few things
are wired to attributes rather than to code, so keep them intact:

- **Scene board rows** need `data-act` (which act chip shows the row),
  `data-hay` (the lowercase text the search box matches against) and
  `data-scenes` (the production-script scenes the chunk covers, which the ID
  cell also shows and links to). A row missing `data-hay` silently stops being
  searchable; a `data-scenes` code that is not on the script page fails
  `check_links.py`. The two numeric columns are Setups
  and Cut shots, in that order; `tools/coverage.py` regenerates both from the
  chunk descriptions and prints the totals the prose quotes.
- **Sidebar links** pair `href="#section-id"` with `data-nav="section-id"`.
  Both must match the `<section id>` or the scroll-spy highlight skips it.
- **Copy buttons** carry their payload in `data-copy`.
- **Wardrobe** is section 10 and deliberately sits *before* Characters: every
  character prompt depends on it, so a face generated against the wrong suit has
  to be generated again.
- **Lane cards** in section 03 carry `data-lane` and `data-task`. The compose
  box builds its picker from them, so adding a lane card is all it takes to add
  a lane — but the card's own `mailto:` is hardcoded in the markup on purpose,
  so every lane is still reachable with JavaScript off.
- **Cross-references in prose** wrap their number in `<span data-sec="budget">18</span>`.
  `check_links.py` verifies the printed number still matches that section's own
  eyebrow and fails if it does not — renumbering silently broke these three
  times before the check existed, and caught the Experiments insert cleanly.
  Write new ones the same way. Inserting a section renumbers every later one, so
  expect the check to fail once and rewrite the printed numbers from each
  section's own eyebrow.
- **Sample beats** live in `sample.html` as `<div class="beat">` panels, one per
  run of footage. Each holds a `.stage` with that run's frames **in shot
  order** — the player cross-fades them on a loop, so a beat with five frames
  plays five shots — and a `.choices` block whose optional `data-label` is the
  on-screen prompt title (`Quick Choice A`, `Decision II.1-A`, an ending's
  name). Labels use the prompt names the production script uses, so a viewer
  and a contributor are talking about the same thing.
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
python3 tools/build_standalone.py   # -> dist/cyoa-hub.html (~1.2 MB) and dist/cyoa-script.html
```

The script page bundles the same way. It has no images, so it stays small; the
hub's links into it are relative and stay live, like the sample's.

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
`main`. It checks that the script page matches the document, checks asset
references and builds the standalone bundle first, so a stale script page or a
broken image reference fails the deploy instead of shipping.

One-time setup: **Settings → Pages → Source → GitHub Actions**.

If the site ends up on a custom domain, set `og:image` in the `<head>` to an
absolute URL — most link-preview crawlers will not resolve the relative path.
