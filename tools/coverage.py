#!/usr/bin/env python3
"""Re-derive the scene board's Setups and Cut shots columns.

The board carries three quantities that a single "Shots" column used to conflate:

    setup     one camera position with its own start frame     — what you claim
    roll      one generation attempt from a setup              — what it costs
    cut shot  one appearance of a setup in the finished edit   — what plays

Coverage reuses setups, so cut shots climb much faster than setups or rolls do.
That is the whole reason the split exists, and the reason reading the script for
real coverage makes the film longer without making it much more expensive.

Everything here is a rule applied to the chunk descriptions on the board. Nothing
is read off a numbered script, so the totals are the right shape and the per-chunk
numbers are individually wrong. The pilot is the one stretch with a real authored
shot list, and the rule overestimates it by ~15% (rule: 27 setups for S09-S13;
actual list: 23) — assume the film total is similarly hot.

    python3 tools/coverage.py           # print the derivation and the totals
    python3 tools/coverage.py --write   # also rewrite the two columns in index.html
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HUB = ROOT / "index.html"

CREW = {"wren", "kaz", "priya", "amara", "elias"}

# A chunk earns an insert setup when it has a screen, an object or a VFX element
# that wants its own framing rather than sharing one.
INSERT = re.compile(
    r"oracle|holo|screen|randomi|medpod|cryo|stasis|sliver|biopsy|bioform|godseed"
    r"|ui|title|overlay|purge|airlock|metamorph",
    re.I,
)

# How many cut shots one beat turns into once it is properly covered. Spectacle
# does not divide — there is no eyeline geometry to cut against.
COVERAGE = {"spectacle": 1.0, "small": 1.4, "group": 2.2}

ROLLS_TO_LAND = 2.7   # attempts before a setup yields a usable take
DIALOGUE_SHARE = 0.4  # share of coverage cuts that carry new lines and need their
                      # own roll; the rest are reactions cut out of existing footage

# Readable beats per chunk — the board's original "Shots" column, and the only
# input here that came from a human reading the script rather than from a rule.
# It is source data, not recoverable from the derived columns, so it lives here.
# Replace an entry when a chunk comes back finished and you know the real figure.
BEATS = {
    "S01": 3, "S02": 3, "S03": 4, "S04": 2, "S05": 2,
    "S06": 2, "S07": 6, "S08": 4, "S09": 5, "S10": 8,
    "S11": 4, "S12": 6, "S13": 5, "S14": 8, "S15": 2,
    "S16": 6, "S17": 5, "S18": 6, "S19": 6, "S20": 5,
    "S21": 6, "S22": 3, "S23": 3, "S24": 5, "S25": 5,
    "S26": 4, "S27": 6, "S28": 4, "S29": 3, "S30": 6,
    "S31": 6, "S32": 3, "S33": 5, "S34": 6, "S35": 6,
    "S36": 6, "S37": 6, "S38": 5, "S39": 5, "S40": 3,
    "S41": 6, "S42": 6, "S43": 3, "S44": 5, "S45": 6,
}


def strip(html):
    return (re.sub(r"<[^>]+>", "", html)
            .replace("&#x27;", "'").replace("&amp;", "&").strip())


def principals(chars):
    c = chars.lower()
    if c == "(none)" or (c.startswith("(") and "drone" in c):
        return 0
    if "all" in c or c.startswith("crew"):
        return 5
    return sum(1 for name in CREW if name in c)


def derive(sid, beat, loc, chars, beats):
    p = principals(chars)
    locations = len([x for x in re.split(r"[/,]", loc) if x.strip()])
    insert = 1 if INSERT.search(beat + " " + chars) else 0

    if p == 0:
        setups, tier = beats, "spectacle"
    else:
        setups = locations + min(p, 4) + insert
        tier = "small" if p <= 2 else "group"

    cuts = max(round(beats * COVERAGE[tier]), setups)
    rolls = round(setups * ROLLS_TO_LAND
                  + (cuts - setups) * DIALOGUE_SHARE * ROLLS_TO_LAND)
    return {"setups": setups, "cuts": cuts, "rolls": rolls,
            "p": p, "tier": tier, "beats": beats}


def rows_from(hub):
    body = hub.split('<table id="board-t">')[1].split("</table>")[0]
    for _, row in re.findall(
            r'<tr data-act="([^"]*)" data-hay="[^"]*">(.*?)</tr>', body, re.S):
        tds = [strip(t) for t in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        # tds: id, beat, location, characters, setups, cut shots, status
        yield tds[0], tds[1], tds[2], tds[3], int(tds[4]), int(tds[5])


def main():
    hub = HUB.read_text()
    board = {sid: (cs, cc) for sid, _, _, _, cs, cc in rows_from(hub)}
    missing = set(board) ^ set(BEATS)
    if missing:
        sys.exit(f"BEATS and the board disagree about which chunks exist: {missing}")

    out = {}
    for sid, beat, loc, chars, _, _ in rows_from(hub):
        out[sid] = derive(sid, beat, loc, chars, BEATS[sid])
        out[sid]["beat"] = beat

    print(f"{'ID':4} {'tier':10} {'beats':>5} {'setups':>6} {'cuts':>5} {'rolls':>5}")
    for sid, c in out.items():
        print(f"{sid:4} {c['tier']:10} {c['beats']:5} {c['setups']:6} "
              f"{c['cuts']:5} {c['rolls']:5}  {c['beat'][:44]}")

    tot = {k: sum(c[k] for c in out.values()) for k in ("setups", "cuts", "rolls")}
    pilot = {k: sum(out[s][k] for s in ("S09", "S10", "S11", "S12", "S13"))
             for k in ("setups", "cuts", "rolls")}
    print(f"\nFILM   setups {tot['setups']}  cut shots {tot['cuts']}  "
          f"rolls {tot['rolls']}")
    print(f"PILOT  setups {pilot['setups']}  cut shots {pilot['cuts']}  "
          f"rolls {pilot['rolls']}   (authored shot list: 23 setups, ~32 cuts, ~85 rolls)")

    drift = [(s, c) for s, c in out.items()
             if (c["setups"], c["cuts"]) != board[s]]
    if drift:
        print(f"\n{len(drift)} chunk(s) differ from the board — rerun with --write:")
        for sid, c in drift:
            was = board[sid]
            print(f"  {sid}  board {was[0]}/{was[1]}  →  rule {c['setups']}/{c['cuts']}")
    else:
        print("\nboard matches the rule")

    if "--write" in sys.argv:
        head, rest = hub.split('<table id="board-t">', 1)
        tbl, tail = rest.split("</table>", 1)

        def fix(m):
            row = m.group(0)
            sid = re.search(r'<td class="id">(S\d\d)</td>', row).group(1)
            c = out[sid]
            return re.sub(r'<td class="num">\d+</td><td class="num">\d+</td>',
                          f'<td class="num">{c["setups"]}</td>'
                          f'<td class="num">{c["cuts"]}</td>', row, count=1)

        tbl = re.sub(r'<tr data-act="[^"]*" data-hay="[^"]*">.*?</tr>',
                     fix, tbl, flags=re.S)
        tbl = re.sub(
            r"<tfoot>.*?</tfoot>",
            '<tfoot><tr><td colspan="4">Provisional totals</td>'
            f'<td class="num" style="color:var(--teal)">{tot["setups"]}</td>'
            f'<td class="num" style="color:var(--teal)">{tot["cuts"]}</td>'
            "<td></td></tr></tfoot>", tbl, flags=re.S)
        HUB.write_text(head + '<table id="board-t">' + tbl + "</table>" + tail)
        print("\nrewrote the board's two numeric columns")
        print("prose totals are hand-written — check them against the figures above")


if __name__ == "__main__":
    main()
