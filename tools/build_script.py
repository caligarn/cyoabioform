#!/usr/bin/env python3
"""Turn the production script into a readable page and a parseable file.

The script lives in `script/CYOA_The_Bioform_Production_Script.docx`. It is the
source of truth for every beat on the hub, and it carries the codes the rest of
the system keys off:

    branch   [II.2-A: Reason with The Bioform]   a path through the story
    scene    2E  INT. OPS DECK – CONTINUOUS       one slug, numbered per sequence
    prompt   DECISION II.2 / QUICK CHOICE A       a viewer choice
    end      THE END (of this branch)             an ending
    retry    TRY AGAIN?                           a fail state that loops

This reads the document with the standard library only (the site has no
dependencies and CI should stay that way) and writes two things:

    script.html                     the script as a page, one anchor per branch,
                                    scene and prompt, so a board row can link to
                                    the exact scene it covers
    script/production-script.json   the same content as data — branches, scenes,
                                    speeches, prompts — for anything that wants
                                    to pull a specific element out of the story

    python3 tools/build_script.py           # rebuild both
    python3 tools/build_script.py --check   # fail if either is stale (CI)

Edit the document, not the outputs. Formatting in the document is what the
parser reads: a bold line that starts with a branch code is a heading, a line
that starts with a number and a letter and a tab is a slug, and indentation
separates a character cue from a parenthetical from a line of dialogue.
"""
import html
import json
import pathlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCX = ROOT / "script" / "CYOA_The_Bioform_Production_Script.docx"
PAGE = ROOT / "script.html"
DATA = ROOT / "script" / "production-script.json"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Indents, in twentieths of a point, that the document uses for each kind of
# line. Anything else is action.
IND_DIALOGUE, IND_PAREN, IND_CUE = 1440, 2160, 2880

CODE = r"[IVX]+\.\d+(?:-[A-Z](?:\.\d+)?)?"
HEADING = re.compile(r"^(ADDENDUM\s+)?(" + CODE + r")\s*[-:–—]?\s*(.*)$", re.I)
SLUG = re.compile(r"^(\d+)([A-Z])\t\s*(.+?)\s*[-–—]*\s*$")
PROMPT = re.compile(
    r"^(DECISION|QUICK CHOICE|CHOICE ON SCREEN|FINAL CHOICE|FINAL PROTOCOL"
    r"|INSERT WREN MICRO CHOICE)", re.I)
PROMPT_CODE = re.compile(r"^DECISION\s*:?\s*([IVX]+)\.?\s*(\d+(?:-[A-Z])?)?", re.I)
QUICK_CODE = re.compile(r"^QUICK CHOICE\s+([A-Z])\b", re.I)
RETRY = re.compile(r"TRY AGAIN", re.I)
END = re.compile(r"^THE END\b", re.I)
SCREEN = re.compile(r"^(TEXT\s+)?ON\s?SCREEN\s*:", re.I)
OPTION = re.compile(r"^(▷|CHOSE\b)")


# ---------------------------------------------------------------- reading ---

def on(rpr, tag):
    """A run property is on unless it is explicitly turned off."""
    el = rpr.find(W + tag) if rpr is not None else None
    return el is not None and el.get(W + "val") not in ("0", "false", "none")


def paragraphs(docx):
    """Yield (indent, runs) per paragraph; a run is (text, bold, italic)."""
    doc = ET.fromstring(zipfile.ZipFile(docx).read("word/document.xml"))
    for p in doc.find(W + "body").iter(W + "p"):
        indent = 0
        ppr = p.find(W + "pPr")
        if ppr is not None:
            ind = ppr.find(W + "ind")
            if ind is not None:
                indent = int(ind.get(W + "left") or ind.get(W + "start") or 0)
        indent = max(indent, 0)     # headings hang left of the margin
        runs = []
        for r in p.iter(W + "r"):
            rpr = r.find(W + "rPr")
            text = "".join(
                (x.text or "") if x.tag == W + "t" else
                "\t" if x.tag == W + "tab" else
                "\n" if x.tag == W + "br" else ""
                for x in r)
            if not text:
                continue
            bold, italic = on(rpr, "b"), on(rpr, "i")
            if not text.strip():          # whitespace carries no formatting
                bold = italic = False
            if runs and runs[-1][1:] == (bold, italic):
                runs[-1] = (runs[-1][0] + text, bold, italic)
            else:
                runs.append((text, bold, italic))
        yield indent, runs


def plain(runs):
    return "".join(t for t, _, _ in runs)


def mostly_bold(runs):
    inked = [(t, b) for t, b, _ in runs if t.strip()]
    return bool(inked) and all(b for _, b in inked)


def tidy(s):
    return re.sub(r"[ \t]+", " ", s).strip()


# ---------------------------------------------------------------- parsing ---

def parse(docx):
    """Return the script as branches → scenes → lines."""
    branches, seen_branch = [], {}
    branch = scene = None
    prev = None                     # type of the previous non-blank line

    def start_branch(code, title, addendum):
        base = "br-" + ("ADDENDUM-" if addendum else "") + code
        ident = base
        n = 1
        while ident in seen_branch:  # the document reuses V.1 — keep both
            n += 1
            ident = f"{base}-{n}"
        seen_branch[ident] = True
        b = {"id": ident, "code": code, "title": title, "addendum": addendum,
             "scenes": []}
        branches.append(b)
        return b

    for indent, runs in paragraphs(docx):
        text = plain(runs)
        if not text.strip():
            continue
        flat = tidy(text.replace("\n", " "))

        m = SLUG.match(text.strip())
        if m:
            if branch is None:
                branch = start_branch("0", "Untitled", False)
            scene = {"id": m.group(1) + m.group(2), "seq": int(m.group(1)),
                     "letter": m.group(2), "slug": tidy(m.group(3)),
                     "branch": branch["id"], "lines": []}
            branch["scenes"].append(scene)
            prev = "slug"
            continue

        stripped = flat.strip("[]{} ")
        if indent == 0 and mostly_bold(runs) and not PROMPT.match(stripped):
            m = HEADING.match(stripped)
            if m:
                branch = start_branch(m.group(2).upper(), tidy(m.group(3)),
                                      bool(m.group(1)))
                scene = None
                prev = "heading"
                continue

        if scene is None:           # text before any slug: park it in a stub
            scene = {"id": branch["id"].replace("br-", "pre-"), "seq": 0,
                     "letter": "", "slug": "", "branch": branch["id"],
                     "lines": []}
            branch["scenes"].append(scene)

        line = {"runs": runs, "text": flat}
        if PROMPT.match(stripped):
            line["type"] = "prompt"
            m = PROMPT_CODE.match(stripped)
            q = QUICK_CODE.match(stripped)
            if q:
                line["code"] = "QUICK " + q.group(1).upper()
            elif m:
                line["code"] = m.group(1).upper() + ("." + m.group(2).upper()
                                                     if m.group(2) else "")
            elif stripped.upper().startswith("FINAL PROTOCOL"):
                line["code"] = branch["code"]
            elif stripped.upper().startswith("FINAL CHOICE"):
                line["code"] = branch["code"]
            elif stripped.upper().startswith("INSERT"):
                line["code"] = "MICRO"
            else:
                line["code"] = branch["code"]
            line["text"] = stripped
        elif RETRY.search(flat) and indent == 0 and (
                mostly_bold(runs) or SCREEN.match(flat)):
            line["type"] = "retry"
        elif END.match(stripped):
            line["type"] = "end"
            line["text"] = stripped
        elif indent == 0 and (OPTION.match(flat) or
                              (mostly_bold(runs) and prev in ("prompt", "option"))):
            line["type"] = "option"
        elif SCREEN.match(flat):
            line["type"] = "screen"
        elif indent >= IND_CUE:
            line["type"] = "cue"
            line["text"] = tidy(flat).upper()
        elif indent >= IND_PAREN:
            line["type"] = "paren"
        elif indent >= IND_DIALOGUE:
            line["type"] = "dialogue"
        else:
            line["type"] = "action"
        scene["lines"].append(line)
        prev = line["type"]

    return branches


def speeches(lines):
    """Fold cue / parenthetical / dialogue runs into speech blocks for the JSON."""
    out, cur = [], None
    for ln in lines:
        t = ln["type"]
        if t == "cue":
            name, ext = ln["text"], ""
            if "(" in name:
                name, ext = name.split("(", 1)
                ext = "(" + ext
            cur = {"type": "speech", "character": name.strip(),
                   "extension": ext.strip(), "text": []}
            out.append(cur)
        elif t in ("paren", "dialogue") and cur is not None:
            cur["text"].append(ln["text"])
        else:
            cur = None
            item = {"type": t, "text": ln["text"]}
            if "code" in ln:
                item["code"] = ln["code"]
            if "id" in ln:
                item["id"] = ln["id"]
            out.append(item)
    return out


# -------------------------------------------------------------- rendering ---

def esc(s):
    return html.escape(s, quote=False)


def inline(runs):
    """Action and dialogue keep the document's bold and italic."""
    out = []
    for text, bold, italic in runs:
        t = esc(text).replace("\n", "<br>")
        if bold:
            t = f"<b>{t}</b>"
        if italic:
            t = f"<i>{t}</i>"
        out.append(t)
    return "".join(out).strip()


def link_refs(markup, branch_ids, decision_ids):
    """Turn the document's own cross-references into links."""
    markup = re.sub(r"\[SEE ADDENDUM\]",
                    lambda m: '<a href="#br-ADDENDUM-IV.1-C">[see addendum]</a>'
                    if "br-ADDENDUM-IV.1-C" in branch_ids else m.group(0), markup)
    markup = re.sub(r"GO TO (" + CODE + ")",
                    lambda m: f'GO TO <a href="#br-{m.group(1)}">{m.group(1)}</a>'
                    if "br-" + m.group(1) in branch_ids else m.group(0), markup)
    markup = re.sub(r"BACK TO DECISION (" + CODE + ")",
                    lambda m: f'BACK TO <a href="#{decision_ids[m.group(1)]}">'
                              f'DECISION {m.group(1)}</a>'
                    if m.group(1) in decision_ids else m.group(0), markup)
    return markup


NAMES = ("Bioform", "Godseed", "Oracle", "Wren", "Amara", "Kaz", "Priya", "Elias",
         "Orion", "Trappist", "AI")


def nice(title):
    """Headings in the document are shouted and typo-cased. The page shows a
    shouted one in sentence case, with names and codes put back; the JSON
    keeps the document's own text."""
    t = title.strip(" :-–")
    letters = [c for c in t if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < 0.6:
        return t
    t = t.lower()
    t = re.sub(r"\b(" + "|".join(n.lower() for n in NAMES) + r")\b",
               lambda m: dict((n.lower(), n) for n in NAMES)[m.group(1)], t)
    t = re.sub(r"\b([ivx]+)\.(\d)", lambda m: m.group(1).upper() + "." + m.group(2), t)
    return t[:1].upper() + t[1:]


def render(branches):
    branch_ids = {b["id"] for b in branches}
    scenes = [s for b in branches for s in b["scenes"]]
    prompts, ends, retries = [], [], []
    decision_ids = {}
    for b in branches:
        for s in b["scenes"]:
            for ln in s["lines"]:
                if ln["type"] == "prompt":
                    ln["id"] = "d-" + s["id"]
                    prompts.append((b, s, ln))
                    decision_ids.setdefault(ln["code"], ln["id"])
                elif ln["type"] == "end":
                    ends.append((b, s, ln))
                elif ln["type"] == "retry":
                    retries.append((b, s, ln))
    real_scenes = [s for s in scenes if s["seq"]]

    def scene_span(b):
        ids = [s["id"] for s in b["scenes"] if s["seq"]]
        if not ids:
            return ""
        return ids[0] if len(ids) == 1 else f"{ids[0]}–{ids[-1]}"

    def label(b):
        return ("Addendum " if b["addendum"] else "") + b["code"]

    o = []
    o.append('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
             '<title>CYOA: The Bioform · Production script</title>\n'
             '<meta name="description" content="The production script for CYOA: The '
             'Bioform, with every branch, scene and viewer prompt anchored so the '
             'scene board can point at the exact beat.">\n'
             '<meta name="color-scheme" content="dark">\n'
             '<meta name="robots" content="noindex">\n'
             '<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">\n'
             '<link rel="stylesheet" href="assets/css/site.css">\n'
             '<link rel="stylesheet" href="assets/css/script.css"></head>'
             '<body class="script">\n'
             '<!-- Generated by tools/build_script.py from '
             'script/CYOA_The_Bioform_Production_Script.docx. Edit the document, '
             'then rebuild. -->\n')

    # sidebar
    o.append('<div class="shell"><nav class="side">\n'
             '<div class="brand"><div class="t">CYOA: The Bioform</div>'
             '<div class="s">Production script</div></div>\n'
             '<a href="index.html" class="ext"><span class="n">←</span>Contributor hub</a>\n'
             '<a href="sample.html" class="ext"><span class="n">▶</span>Play the sample</a>\n'
             '<a href="#contents" data-nav="contents"><span class="n">§</span>Contents</a>\n'
             '<div class="grp">Branches</div>\n')
    for b in branches:
        o.append(f'<a href="#{b["id"]}" data-nav="{b["id"]}"><span class="n">'
                 f'{esc(label(b))}</span>{esc(nice(b["title"]))}</a>\n')
    o.append('</nav><main>\n<div class="mobbar">\n<a href="index.html">Hub</a>\n'
             '<a href="#contents">Contents</a>\n')
    for b in branches:
        o.append(f'<a href="#{b["id"]}">{esc(label(b))}</a>\n')
    o.append('</div>\n<div class="wrap">\n')

    # top
    o.append('<header class="top">\n'
             '<div class="kicker">Machine Cinema · production script · generated from the document</div>\n'
             '<h1>CYOA: The Bioform</h1>\n'
             '<p>The script as one page, every branch, scene and prompt with its own '
             'anchor. This is the text the scene board, the branch map and the '
             'sample are cut from. If a shot fights the board, the script wins.</p>\n'
             '<div class="statrow">\n'
             f'<div class="stat"><b>{len(branches)}</b><i>Branches</i></div>\n'
             f'<div class="stat"><b>{len(real_scenes)}</b><i>Scenes</i></div>\n'
             f'<div class="stat"><b>{len(prompts)}</b><i>Viewer prompts</i></div>\n'
             f'<div class="stat"><b>{len(ends)}</b><i>Endings</i></div>\n'
             f'<div class="stat"><b>{len(retries)}</b><i>Fail loops</i></div>\n'
             '</div>\n'
             '<div class="card keys"><span class="lbl">How to read the codes</span>\n'
             '<div class="grid2" style="margin-top:8px">\n'
             '<div><b class="code">II.2-A</b><span>A <b>branch</b>: one path through the story. '
             'The roman numeral is the act, the digit is the decision, the letter is '
             'the option taken. The scene board and the branch map use the same codes.</span></div>\n'
             '<div><b class="code">2E</b><span>A <b>scene</b>: one slug line. The number is the '
             'sequence, the letter is the slug within it. A board row lists the scenes '
             'it covers, so <code>#2E</code> on this page is the beat a claim points at.</span></div>\n'
             '<div><b class="code amber">DECISION</b><span>A <b>viewer prompt</b>. Amber blocks are '
             'where the film stops and asks. Quick choices are cosmetic, decisions '
             'fork the story, and the final protocol picks the ending.</span></div>\n'
             '<div><b class="code rust">TRY AGAIN?</b><span>A <b>fail state</b>: the branch kills the '
             'crew and loops the viewer back to the choice they blew. '
             '<b class="pink">THE END</b> marks an ending.</span></div>\n'
             '</div></div>\n'
             '<p class="gen">Generated from <code>script/CYOA_The_Bioform_Production_Script.docx</code> '
             'by <code>tools/build_script.py</code>. Edit the document, not this page. '
             'The same content is available as data in '
             '<a href="script/production-script.json">production-script.json</a>.</p>\n'
             '</header>\n')

    # contents
    o.append('<section id="contents"><div class="eyebrow">Contents</div>'
             '<h2 class="sec">Every branch, and where it stops to ask</h2>\n'
             '<div class="toc">\n')
    for b in branches:
        o.append(f'<a href="#{b["id"]}"><span class="c">{esc(label(b))}</span>'
                 f'<span class="t">{esc(nice(b["title"]))}</span>'
                 f'<span class="s">{esc(scene_span(b))}</span></a>\n')
    o.append('</div>\n<div class="grid2" style="margin-top:22px">\n'
             '<div class="card"><span class="lbl">Viewer prompts</span><ul class="clean plist">\n')
    for b, s, ln in prompts:
        o.append(f'<li><a href="#{ln["id"]}"><span class="c">{esc(s["id"])}</span>'
                 f'{esc(ln["text"])}</a></li>\n')
    o.append('</ul></div>\n<div><div class="card"><span class="lbl">Endings</span>'
             '<ul class="clean plist">\n')
    for b, s, ln in ends:
        o.append(f'<li><a href="#{s["id"]}"><span class="c">{esc(s["id"])}</span>'
                 f'{esc(nice(b["title"]))}</a></li>\n')
    o.append('</ul></div>\n<div class="card"><span class="lbl">Fail states</span>'
             '<ul class="clean plist">\n')
    for b, s, ln in retries:
        o.append(f'<li><a href="#{s["id"]}"><span class="c">{esc(s["id"])}</span>'
                 f'{esc(nice(b["title"]))}</a></li>\n')
    o.append('</ul></div></div></div>\n</section>\n')

    # the script
    for b in branches:
        cls = "branch addendum" if b["addendum"] else "branch"
        o.append(f'<section class="{cls}" id="{b["id"]}">'
                 f'<div class="eyebrow">{"Addendum" if b["addendum"] else "Branch"} '
                 f'{esc(b["code"])}</div>'
                 f'<h2 class="sec">{esc(nice(b["title"]))}</h2>\n')
        for s in b["scenes"]:
            if s["seq"]:
                o.append(f'<div class="scene" id="{s["id"]}"><h3>'
                         f'<a href="#{s["id"]}" class="num">{s["id"]}</a>'
                         f'<span class="slug">{esc(s["slug"])}</span></h3>\n')
            else:
                o.append('<div class="scene stub">\n')
            for ln in s["lines"]:
                t = ln["type"]
                if t == "prompt":
                    o.append(f'<div class="prompt" id="{ln["id"]}">'
                             f'<span class="tag">Prompt · {esc(ln["code"])}</span>'
                             f'<p>{link_refs(esc(ln["text"]), branch_ids, decision_ids)}</p></div>\n')
                elif t == "option":
                    o.append(f'<p class="option">{inline(ln["runs"])}</p>\n')
                elif t == "retry":
                    o.append(f'<p class="retry">{link_refs(esc(ln["text"]), branch_ids, decision_ids)}</p>\n')
                elif t == "end":
                    o.append(f'<p class="end">{esc(ln["text"])}</p>\n')
                elif t == "screen":
                    o.append(f'<p class="screen">{inline(ln["runs"])}</p>\n')
                elif t == "cue":
                    o.append(f'<p class="cue">{esc(ln["text"])}</p>\n')
                elif t == "paren":
                    o.append(f'<p class="paren">{esc(ln["text"])}</p>\n')
                elif t == "dialogue":
                    o.append(f'<p class="dlg">{inline(ln["runs"])}</p>\n')
                else:
                    o.append(f'<p class="action">{link_refs(inline(ln["runs"]), branch_ids, decision_ids)}</p>\n')
            o.append('</div>\n')
        o.append('</section>\n')

    o.append('<footer>Generated from the production script document. '
             'Codes on this page are the codes the scene board, the branch map and '
             'the sample use. A beat that reads differently on the hub is the hub '
             'being out of date, not the script.</footer>\n'
             '</div></main></div>\n'
             '<script src="assets/js/script.js" defer></script></body></html>\n')
    return "".join(o)


def data(branches):
    out = {
        "source": "script/CYOA_The_Bioform_Production_Script.docx",
        "generated_by": "tools/build_script.py",
        "codes": {
            "branch": "roman act . decision [-option[.sub]]  e.g. II.1-A.2",
            "scene": "sequence number + slug letter  e.g. 2E",
            "prompt_id": "d- + the scene the prompt appears in  e.g. d-2G",
        },
        "branches": [],
        "prompts": [],
        "endings": [],
        "fail_states": [],
    }
    for b in branches:
        jb = {"id": b["id"], "code": b["code"], "title": b["title"],
              "addendum": b["addendum"], "scenes": []}
        for s in b["scenes"]:
            js = {"id": s["id"], "seq": s["seq"], "letter": s["letter"],
                  "slug": s["slug"], "lines": speeches(s["lines"])}
            jb["scenes"].append(js)
            for ln in s["lines"]:
                ref = {"scene": s["id"], "branch": b["code"], "text": ln["text"]}
                if ln["type"] == "prompt":
                    out["prompts"].append({"id": ln["id"], "code": ln["code"], **ref})
                elif ln["type"] == "end":
                    out["endings"].append(ref)
                elif ln["type"] == "retry":
                    out["fail_states"].append(ref)
        out["branches"].append(jb)
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


def main():
    branches = parse(DOCX)
    page = render(branches)
    blob = data(branches)
    if "--check" in sys.argv:
        stale = [str(p.relative_to(ROOT)) for p, want in ((PAGE, page), (DATA, blob))
                 if not p.is_file() or p.read_text(encoding="utf-8") != want]
        if stale:
            sys.exit("stale, rebuild with tools/build_script.py: " + ", ".join(stale))
        print("script.html and production-script.json match the document")
        return
    PAGE.write_text(page, encoding="utf-8")
    DATA.write_text(blob, encoding="utf-8")
    scenes = sum(1 for b in branches for s in b["scenes"] if s["seq"])
    prompts = sum(1 for b in branches for s in b["scenes"]
                  for ln in s["lines"] if ln["type"] == "prompt")
    print(f"wrote script.html ({len(page) / 1024:.0f} KB) and "
          f"script/production-script.json ({len(blob) / 1024:.0f} KB): "
          f"{len(branches)} branches, {scenes} scenes, {prompts} prompts")


if __name__ == "__main__":
    main()
