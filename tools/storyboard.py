#!/usr/bin/env python3
"""Author the storyboard section from the production script.

The board is derived, not drawn by hand. One rule turns the script's own lines
into panels, so a new script draft redraws the whole board instead of leaving
98 scenes to be re-slotted by hand:

    a new location              -> one ESTABLISHING panel, unless the scene is
                                   CONTINUOUS from the same place as the last.
    action / option line        -> one panel PER BEAT. Sentences split; a short
                                   trailing fragment ("Familiar." "Easy.") is a
                                   note on the beat before it, not its own shot.
    screen / prompt / retry /
      end line                  -> one CARD panel. Lettering, so it is drawn,
                                   never generated -- generators cannot letter.
    a run of speech lines       -> the coverage, boarded out: one speaker gets a
                                   single; two or more get a master, a single
                                   each, and a reaction.
    a run of NARRATOR / TEXT    -> no panel. It is voice-over; it rides the
                                   panel next to it and is printed under it.
    a scene under MIN_PANELS    -> topped up with alternate framings of its own
                                   first beat (wide / tighter / detail), so no
                                   scene offers nothing to pick from.

The first version of this collapsed a whole run of dialogue into one panel
labelled Coverage. That was honest about SETUPS -- coverage reuses the setup it
came from, so it costs rolls and not new positions -- but it was useless as a
thing to claim, because the panel a contributor wants to take is one framing,
not "the exchange". So the board now boards coverage and over-provisions on
purpose: it offers more panels than the finished film will use. You pick from
them and the rest get cut. That makes the panel count a MENU, not an estimate,
and it is emphatically not a budget: see the note the section prints about what
this board does and does not say about cost.

It stays provisional in the same way the scene board is: the rule is right about
the shape and wrong about any one scene. A scene gets its panels replaced the
moment a real board comes back.

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

# A trailing sentence shorter than this is read as a note on the beat before it
# rather than a shot of its own. Tuned against the script: it catches
# "Familiar.", "Easy.", "One sharp inhale.", "Focus returns." and leaves every
# sentence that actually describes a new action standing on its own.
FRAGMENT = 30

# No scene offers fewer than this many panels, so there is always a choice.
MIN_PANELS = 3
ALTS = ("wide", "tighter", "detail")

# What a panel's chip says. A plain action beat gets none -- it is the default,
# and tagging every box would make the tags worthless.
TAG = {"establishing": "Establishing", "master": "Master", "single": "Single",
       "reaction": "Reaction", "alt": "Alt framing", "option": "Branch option"}

# Art that exists. Keyed by panel id. The CDN these land on is blocked from the
# build container by network policy, so the page hotlinks them and carries the
# basename it would have had -- see `data-local` on every generated image in
# this repo. `shot` is the framing actually generated, which is not always the
# framing the rule guessed; where they differ the panel prints the real one.
#
# `beat` is the start of the panel's description as it read when the art was
# matched to it, and it is the important field. A panel id is an ORDINAL, so
# changing the boarding rule slides every id in a scene -- which once silently
# moved all 22 frames onto neighbouring panels while every key stayed valid, so
# nothing complained and the page quietly lied. Checking `beat` turns that into
# a build failure. When a rule change moves a frame, re-point it and re-record
# the beat; do not just delete the field.
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


def beats(text):
    """Split an action line into the visual beats inside it.

    A line often carries several shots: "He hands Amara her towel when she exits
    the showers. Familiar. Easy." is one beat with two notes on it, while "Wren
    kneels beside a waste port. They reach in with a suction wand." is two. The
    split is on sentences, and a short trailing sentence is read as a note on the
    beat before it rather than a shot of its own -- which is what "Familiar.",
    "Easy.", "One sharp inhale." and "Focus returns." actually are.
    """
    out = []
    for part in re.split(r"(?<=[.!?])\s+", text):
        part = part.strip()
        if not part:
            continue
        if out and len(part) < FRAGMENT:
            out[-1] += " " + part
        else:
            out.append(part)
    return out or [text.strip()]


def location(slug):
    """The place part of a slug, for deciding whether the camera has moved."""
    return re.split(r"\s+[-–—]\s+", slug.upper())[0].strip()


def panel(kind, desc, **kw):
    p = {"kind": kind, "desc": desc, "vo": [], "who": [], "lines": []}
    p.update(kw)
    return p


def panels_for(scene, fresh_location):
    """Apply the rule to one scene. Returns a list of panel dicts."""
    out = []
    if fresh_location:
        out.append(panel("establishing", scene["slug"]))

    run = []   # (speaker, line) pairs, in order, for the dialogue run in hand

    def flush():
        """Board the run of dialogue in hand as separate framings."""
        if not run:
            return
        who = []
        for speaker, _ in run:
            if speaker not in who:
                who.append(speaker)
        first = run[0][1]
        if len(who) == 1:
            # Nobody to cut against, so the exchange is one framing.
            out.append(panel("single", first, who=who))
        else:
            out.append(panel("master", first, who=who))
            for name in who:
                said = next(t for s, t in run if s == name)
                out.append(panel("single", said, who=[name]))
            # Whoever is not speaking last is who the camera turns to.
            listeners = [n for n in who if n != run[-1][0]] or who[:1]
            out.append(panel("reaction", run[-1][1], who=listeners))
        run.clear()

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
                    out.append(panel("pending-vo", "", vo=[text]))
                continue
            run.append((who, text))
            continue

        flush()
        if kind in CARD:
            made = [panel("card", text, card=CARD[kind])]
        else:
            made = [panel("option" if kind == "option" else "shot", b)
                    for b in beats(text)]

        # A scene that opened on voice-over hands it to the first real panel.
        if len(out) == 1 and out[0]["kind"] == "pending-vo":
            made[0]["vo"] = out[0]["vo"] + made[0]["vo"]
            out = []
        out.extend(made)
    flush()

    # A scene that is nothing but voice-over still needs one panel to hold it.
    for p in out:
        if p["kind"] == "pending-vo":
            p["kind"] = "shot"
            p["desc"] = "Voice-over only — no action written. Needs a framing."

    # A one-line scene would otherwise offer a contributor a single box and no
    # choice. Top it up with alternate framings of its own first beat. Prefer a
    # beat of action to frame against; a scene that is nothing but one line of
    # dialogue (7D is the only one) has to fall back on its own slug.
    source = next((p for p in out if p["kind"] in ("shot", "option",
                                                   "establishing")), None)
    against = source["desc"] if source else scene["slug"]
    alt = 0
    while len(out) < MIN_PANELS:
        out.append(panel("alt", against, alt=ALTS[alt % len(ALTS)]))
        alt += 1
    return out


def describe(p):
    """The short line printed under the panel."""
    who = ", ".join(n.title() for n in p["who"])
    if p["kind"] == "establishing":
        return f"Establishing · {clip(p['desc'], 120)}"
    if p["kind"] == "master":
        return f"Master · {who} — the geography of the exchange"
    if p["kind"] == "single":
        return f"Single · {who} — “{clip(p['desc'], 90)}”"
    if p["kind"] == "reaction":
        return f"Reaction · {who} — on “{clip(p['desc'], 70)}”"
    if p["kind"] == "alt":
        return f"Alt framing · {p['alt']} on: {clip(p['desc'], 100)}"
    return clip(p["desc"])


def build():
    board = []
    previous = None
    for branch, scene in scenes():
        here = location(scene["slug"])
        fresh = "CONTINUOUS" not in scene["slug"].upper() and here != previous
        previous = here
        ps = panels_for(scene, fresh)
        for i, p in enumerate(ps, 1):
            p["id"] = f"{scene['id']}-{i}"
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
    cls = f'sbp k-{p["kind"]}'
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
    tag = (p["card"] if p["kind"] == "card" else TAG.get(p["kind"]))
    if tag:
        bits.append(f'<span class="sbtag">{esc(tag)}</span>')
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
    per_scene = [len(ps) for _, _, ps in board]
    least, most = min(per_scene), max(per_scene)

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
           f'<span class="pill">{least}–{most} per scene</span>'
           '<span class="pill hot">98 scenes</span></div>',
           '<div class="note" style="margin:0 0 16px"><b>More panels than the '
           'film will use, on purpose.</b> This board used to fold a whole run '
           'of dialogue into one box labelled <em>Coverage</em>. That was honest '
           'about camera positions and useless to work from, because the thing '
           'you want to claim is one framing, not “the exchange”. So the '
           'coverage is boarded out now: one speaker gets a '
           '<b style="color:var(--ink);font-weight:500">single</b>, two or more '
           'get a <b style="color:var(--ink);font-weight:500">master</b>, a '
           'single each and a <b style="color:var(--ink);font-weight:500">'
           'reaction</b>. Action lines split into one panel per beat. A new '
           'location opens on an <b style="color:var(--ink);font-weight:500">'
           'establishing</b> plate unless the scene is continuous from the last '
           'one. Any scene thin enough to offer no choice is topped up with '
           '<b style="color:var(--ink);font-weight:500">alt framings</b> of its '
           'own first beat, or of its location when it has no action written. '
           f'No scene offers fewer than {least} boxes and the biggest offers '
           f'{most}. None of it is a quota — take the ones that carry the scene '
           'and let the rest go.</div>',
           '<div class="note" style="margin:0 0 16px">'
           'Narration never gets a box: it is voice-over, printed under the '
           'panel it plays over. Cards (text on screen, choice prompts, fail '
           'and end cards) are <b style="color:var(--ink);font-weight:500">drawn, '
           'never generated</b> — the generators cannot letter, so anything '
           'with words on it is authored by hand '
           '(<code>tools/storyboard_cards.py</code>).</div>',
           '<div class="note" style="margin:0 0 16px"><b style="color:var(--amber)">'
           'Provisional, like the scene board.</b> The panels come from a rule '
           'applied to the script\'s own lines (<code>tools/storyboard.py</code>), '
           'not from a human reading it shot by shot. The rule is right about '
           'the shape and wrong about any given scene. Claim a scene, board it '
           'properly, and your panels replace the derived ones.</div>',
           '<div class="note" style="margin:0 0 20px">'
           '<b style="color:var(--rust)">What this board does not say.</b> '
           f'It is not a shot count and not a bill. {shots} photographed boxes '
           'is a menu — deliberately more options than the cut needs. The '
           'scene board in section <span data-sec="board">16</span> runs a '
           'different rule (<code>tools/coverage.py</code>) and counts 188 '
           'camera setups and 361 cut shots for the same film. Those two rules read different '
           'things: one summarises a chunk in a sentence, this one reads every '
           'beat and then offers alternates on top. Neither is the film\'s shot '
           'list. <b style="color:var(--ink);font-weight:500">Claiming a panel '
           'is not a budget commitment</b> — the budget in section '
           '<span data-sec="budget">21</span> still rests on 188 setups and '
           'about 695 rolls, so check there before generating a scene\'s worth '
           'of options.</div>']

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

    panel_by_id = {p["id"]: p for _, _, ps in board for p in ps}
    # Art keyed to a panel the rule no longer produces is a silent orphan: the
    # image stops appearing and nothing says so.
    orphan = sorted(set(FRAMES) - set(panel_by_id))
    if orphan:
        sys.exit(f"storyboard: {len(orphan)} frame(s) key no panel: {orphan}")

    # The worse failure is art whose key is still a real panel but a DIFFERENT
    # one, because a rule change slid the ordinals under it. Every frame records
    # the beat it was matched to; if the panel no longer says that, the frame is
    # on the wrong box and the page is lying about what the image shows.
    moved = []
    for pid, art in sorted(FRAMES.items()):
        beat = art.get("beat")
        if beat is None:
            moved.append(f"  {pid}: no beat recorded, so nothing can check it")
        elif not describe(panel_by_id[pid]).startswith(beat):
            moved.append(f"  {pid} now reads  {describe(panel_by_id[pid])[:58]!r}\n"
                         f"  {'':{len(pid)}}  art was matched to  {beat!r}")
    if moved:
        sys.exit("storyboard: {} frame(s) no longer match their panel:\n{}".format(
            len(moved), "\n".join(moved)))

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
