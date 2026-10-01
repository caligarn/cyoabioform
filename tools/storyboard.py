#!/usr/bin/env python3
"""Author the storyboard section from the production script.

The board is derived, not drawn by hand. One rule turns the script's own lines
into panels, so a new script draft redraws the whole board instead of leaving
98 scenes to be re-slotted by hand:

    action line                 -> one panel. The visual it describes.
    option line                 -> one panel. A branch's alternative visual.
    screen / prompt / retry /
      end line                  -> one CARD panel. Lettering, so it is drawn,
                                   never generated -- generators cannot letter.
    a run of speech lines       -> ONE panel standing for the coverage, labelled
                                   with the speakers in it.
    a run of NARRATOR / TEXT    -> no panel. It is voice-over; it rides the
                                   panel next to it and is printed under it.

The speech rule is the one worth arguing about, and it is the same call the
pilot shot list already makes: P-08, P-14 and P-18 each write four people's
framings as one row. A panel here is a SETUP, not a cut shot. Boarding every
reverse would triple the panel count without planning anything new, because
coverage reuses the setup it came from.

So the panel count is the setup count, and it is provisional in the same way
the scene board is: the rule is right about the shape and wrong about any one
scene. A scene gets its panels replaced the moment a real board comes back.

    python3 tools/storyboard.py            # print the derivation
    python3 tools/storyboard.py --write    # also write the section into index.html
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HUB = ROOT / "index.html"
SCRIPT = ROOT / "script" / "production-script.json"

OPEN = "<!-- storyboard:begin -->"
CLOSE = "<!-- storyboard:end -->"

# Spoken by nobody on screen, so it never earns a framing of its own.
NARRATOR = {"NARRATOR / TEXT", "NARRATOR", "TEXT", "NARRATOR/TEXT"}

# Lines that are lettering rather than photography.
CARD = {"screen": "On screen", "prompt": "Choice card",
        "retry": "Fail card", "end": "End card"}

# Art that exists. Keyed by panel id. The CDN these land on is blocked from the
# build container by network policy, so the page hotlinks them and carries the
# basename it would have had -- see `data-local` on every generated image in
# this repo. `shot` is the framing actually generated, which is not always the
# framing the rule guessed; where they differ the panel prints the real one.
FRAMES = {}

ART = ROOT / "tools" / "storyboard_frames.json"
if ART.is_file():
    FRAMES = json.loads(ART.read_text())


def scenes():
    doc = json.loads(SCRIPT.read_text())
    for branch in doc["branches"]:
        for scene in branch["scenes"]:
            yield branch, scene


def clip(text, n=150):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def panels_for(scene):
    """Apply the rule to one scene's lines. Returns a list of panel dicts."""
    out = []
    for line in scene["lines"]:
        kind = line["type"]
        text = line["text"]
        if isinstance(text, list):
            text = " ".join(text)

        if kind == "speech":
            who = (line.get("character") or "").strip()
            if who.upper() in NARRATOR:
                # Voice-over. It rides the neighbouring panel; if the scene
                # opens on it there is nothing to ride yet, so it waits for the
                # first panel and is attached below.
                if out:
                    out[-1]["vo"].append(text)
                else:
                    out.append({"kind": "pending-vo", "vo": [text], "who": [],
                                "desc": ""})
                continue
            if out and out[-1]["kind"] == "coverage":
                if who not in out[-1]["who"]:
                    out[-1]["who"].append(who)
                out[-1]["lines"].append(text)
            else:
                out.append({"kind": "coverage", "who": [who], "lines": [text],
                            "vo": [], "desc": ""})
            continue

        panel = {"vo": [], "who": [], "lines": [], "desc": text}
        if kind in CARD:
            panel["kind"] = "card"
            panel["card"] = CARD[kind]
        elif kind == "option":
            panel["kind"] = "option"
        else:
            panel["kind"] = "shot"

        # A scene that opened on voice-over hands it to the first real panel.
        if out and out[0]["kind"] == "pending-vo" and len(out) == 1:
            panel["vo"] = out[0]["vo"] + panel["vo"]
            out = []
        out.append(panel)

    # A scene that is nothing but voice-over still needs one panel to hold it.
    for p in out:
        if p["kind"] == "pending-vo":
            p["kind"] = "shot"
            p["desc"] = "Voice-over only — no action written. Needs a framing."
    return out


def describe(p):
    """The short line printed under the panel."""
    if p["kind"] == "coverage":
        who = ", ".join(n.title() for n in p["who"])
        label = "Single" if len(p["who"]) == 1 else "Singles"
        cue = clip(p["lines"][0], 90)
        return f"{label} · {who} — “{cue}”"
    return clip(p["desc"])


def build():
    board = []
    for branch, scene in scenes():
        ps = panels_for(scene)
        for i, p in enumerate(ps, 1):
            pid = f"{scene['id']}-{i}"
            p["id"] = pid
            p["scene"] = scene["id"]
            p["slug"] = scene["slug"]
            p["branch"] = branch["code"]
            p["btitle"] = branch["title"]
        board.append((branch, scene, ps))
    return board


def esc(s):
    return html.escape(s, quote=True)


def panel_html(p):
    art = FRAMES.get(p["id"])
    cls = "sbp"
    if p["kind"] == "card":
        cls += " card"
    if art:
        cls += " has"

    if art:
        # A hotlinked frame carries the basename it would have on disk, for the
        # scripted swap once the CDN is reachable. A card is already on disk.
        local = (f' data-local="{esc(art["basename"])}"'
                 if art["url"].startswith("http") else "")
        box = (f'<a href="{esc(art["url"])}" target="_blank" rel="noopener">'
               f'<img loading="lazy" src="{esc(art["url"])}"{local}'
               f' alt="Storyboard panel {esc(p["id"])} — {esc(describe(p))}"></a>')
    elif p["kind"] == "card":
        box = '<div class="sbbox"><span class="sbk">card</span></div>'
    else:
        box = f'<div class="sbbox"><span class="sbk">{esc(p["id"])}</span></div>'

    bits = [f'<div class="{cls}" id="sb-{esc(p["id"])}">{box}',
            f'<div class="sbid">{esc(p["id"])}']
    if p["kind"] == "card":
        bits.append(f'<span class="sbtag">{esc(p["card"])}</span>')
    elif p["kind"] == "option":
        bits.append('<span class="sbtag">Branch option</span>')
    elif p["kind"] == "coverage":
        bits.append('<span class="sbtag">Coverage</span>')
    if art and art.get("shot"):
        bits.append(f'<span class="sbtag go">{esc(art["shot"])}</span>')
    bits.append("</div>")
    bits.append(f'<p class="sbd">{esc(describe(p))}</p>')
    for vo in p["vo"]:
        bits.append(f'<p class="sbvo">VO · {esc(clip(vo, 130))}</p>')
    bits.append("</div>")
    return "".join(bits)


def section_html(board, num):
    filled = len(FRAMES)
    panels = sum(len(ps) for _, _, ps in board)
    cards = sum(1 for _, _, ps in board for p in ps if p["kind"] == "card")
    shots = panels - cards

    out = [OPEN,
           f'<section id="storyboard"><div class="eyebrow">{num} · Storyboard</div>'
           '<h2 class="sec">Every shot in the film, as a box</h2>',
           '<p class="lede">The whole production script boarded out: '
           f'{panels} panels across 98 scenes, every one of them claimable. '
           'Most are still empty on purpose — an empty box with the description '
           'under it <em>is</em> the brief. Scenes 1A to 1J are filled in, so you '
           'can see what a finished panel looks like before you take one. These '
           'are shot as photographic key frames rather than sketches, because a '
           'panel that works also works as the start frame the shot gets '
           'generated from.</p>',
           f'<div class="toolbar"><span class="pill go">{filled} filled</span>'
           f'<span class="pill">{panels} panels</span>'
           f'<span class="pill">{shots} photographed</span>'
           f'<span class="pill">{cards} lettered cards</span>'
           '<span class="pill hot">98 scenes</span></div>',
           '<div class="note" style="margin:0 0 16px"><b>A panel is a setup, '
           'not a cut shot.</b> A run of dialogue is one panel labelled '
           '<em>Coverage</em>, the same call the pilot shot list makes when '
           'P-08 writes four people\'s framings as one row — boarding every '
           'reverse would triple the count without planning anything new. '
           'Narration never gets a box: it is voice-over, printed under the '
           'panel it plays over. Cards (text on screen, choice prompts, fail '
           'and end cards) are <b style="color:var(--ink);font-weight:500">drawn, '
           'never generated</b> — the generators cannot letter, so anything '
           'with words on it is authored by hand.</div>',
           '<div class="note" style="margin:0 0 16px"><b style="color:var(--amber)">'
           'Provisional, like the scene board.</b> The panels come from a rule '
           'applied to the script\'s own lines (<code>tools/storyboard.py</code>), '
           'not from a human reading it shot by shot. The rule is right about '
           'the shape and wrong about any given scene. Claim a scene, board it '
           'properly, and your panels replace the derived ones.</div>',
           '<div class="note" style="margin:0 0 20px">'
           '<b style="color:var(--rust)">This board disagrees with the scene '
           f'board, and that is worth knowing.</b> It counts {shots} '
           'photographed setups for the film. The scene board\'s rule '
           '(<code>tools/coverage.py</code>) counts 188, because it reads one '
           'sentence per chunk where this reads every action line in the script '
           '— so it under-counts by construction. This one over-counts too: '
           '<em>“Her feet magnetize gently to the floor”</em> is a continuation '
           'of the shot before it, not a new camera position. The real number is '
           'somewhere between 188 and ' f'{shots}' ', nobody has it yet, and '
           '<b style="color:var(--ink);font-weight:500">the budget in section '
           '<span data-sec="budget">21</span> is still built on 188.</b> '
           'Boarding scenes for real is what settles it; until then treat the '
           'budget as a floor, not an estimate.</div>']

    # Group by branch so the page is navigable; Act I opens, the rest fold.
    groups = []
    for branch, scene, ps in board:
        key = (branch["code"], branch["title"], branch["addendum"])
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append((scene, ps))

    for i, ((code, title, addendum), items) in enumerate(groups):
        n = sum(len(ps) for _, ps in items)
        have = sum(1 for _, ps in items for p in ps if p["id"] in FRAMES)
        openat = " open" if i == 0 else ""
        badge = (f'<span class="pill go">{have} filled</span>' if have
                 else f'<span class="pill">{n} to board</span>')
        out.append(f'<details class="sbact"{openat}><summary>'
                   f'<b>{esc(code)}</b> {esc(title.strip())}'
                   f'{" <em>(addendum)</em>" if addendum else ""}'
                   f'<span class="sbn">{len(items)} scene'
                   f'{"s" if len(items) != 1 else ""} · {n} panels</span>'
                   f'{badge}</summary>')
        for scene, ps in items:
            out.append(f'<div class="sbscene"><h4>'
                       f'<a href="script.html#{esc(scene["id"])}">{esc(scene["id"])}</a>'
                       f' <span>{esc(scene["slug"])}</span></h4>'
                       f'<div class="sbgrid">')
            out.extend(panel_html(p) for p in ps)
            out.append("</div></div>")
        out.append("</details>")

    out.append("</section>")
    out.append(CLOSE)
    return "\n".join(out)


def main():
    board = build()
    panels = sum(len(ps) for _, _, ps in board)
    kinds = {}
    for _, _, ps in board:
        for p in ps:
            kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1

    print(f"{'scene':6} {'panels':>6}  slug")
    for _, scene, ps in board:
        print(f"{scene['id']:6} {len(ps):6}  {scene['slug'][:58]}")
    print(f"\n98 scenes, {panels} panels: "
          + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())))
    print(f"art on file for {len(FRAMES)} panel(s)")

    ids = {p["id"] for _, _, ps in board for p in ps}
    # Art keyed to a panel the rule no longer produces is a silent orphan: the
    # image stops appearing and nothing says so.
    orphan = sorted(set(FRAMES) - ids)
    if orphan:
        sys.exit(f"storyboard: {len(orphan)} frame(s) key no panel: {orphan}")

    # Every scene in the script has to reach the board, or a scene silently
    # vanishes from the only page that claims to list all of them.
    boarded = {scene["id"] for _, scene, _ in board}
    want = {s["id"] for _, s in scenes()}
    if boarded != want:
        sys.exit(f"storyboard: scenes missing from the board: {want - boarded}")

    if "--write" in sys.argv:
        hub = HUB.read_text()
        if OPEN not in hub or CLOSE not in hub:
            sys.exit("storyboard: index.html has no storyboard:begin/end markers")
        num = re.search(r'<a href="#storyboard" data-nav="storyboard">'
                        r'<span class="n">(\d\d)</span>', hub)
        if not num:
            sys.exit("storyboard: no sidebar entry for the storyboard section")
        head, rest = hub.split(OPEN, 1)
        _, tail = rest.split(CLOSE, 1)
        body = section_html(board, num.group(1))
        HUB.write_text(head + body + tail)
        print(f"wrote section {num.group(1)}, {len(body)} bytes into index.html")


if __name__ == "__main__":
    main()
