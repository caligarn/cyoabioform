#!/usr/bin/env python3
"""Draw the storyboard's text cards as SVG.

Every panel whose content is lettering -- text on screen, a choice prompt, a
fail card, an end card -- is authored here rather than generated. The image
tools cannot letter: ask one for a console readout and it returns convincing
glyphs that spell nothing. Anything a contributor is expected to READ has to be
drawn, which is the same call `tools/deck_diagram.py` makes about the station.

Each card is written to assets/img/sb/<panel-id>.svg, so they live in the repo
rather than on a blocked CDN and `check_links.py` can see them.

    python3 tools/storyboard_cards.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "sb"

W, H = 640, 360
BG = "#0d1417"
INK = "#ececeb"
MUTED = "#8ba3a5"
AMBER = "#f0a63c"
TEAL = "#7ea4ab"
LINE = "#2c4041"
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")


def frame(body, scan=True):
    """The common shell: dark 16:9 field, faint scan lines, a hairline border."""
    scans = ""
    if scan:
        scans = (f'<rect width="{W}" height="{H}" fill="url(#sl)"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" \
width="{W}" height="{H}" role="img">
<defs>
<pattern id="sl" width="1" height="3" patternUnits="userSpaceOnUse">
<rect width="1" height="1" fill="#ffffff" opacity="0.028"/></pattern>
<radialGradient id="vig" cx="50%" cy="46%" r="72%">
<stop offset="60%" stop-color="#000" stop-opacity="0"/>
<stop offset="100%" stop-color="#000" stop-opacity="0.55"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
{scans}
{body}
<rect width="{W}" height="{H}" fill="url(#vig)"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" \
stroke="{LINE}"/>
</svg>
"""


def mono(x, y, text, size=13, fill=INK, anchor="start", spacing=1.6,
         weight="400", opacity=1):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" '
            f'font-weight="{weight}" opacity="{opacity}">{text}</text>')


# ---- 1A-4 · the opening status readout -------------------------------------
# TEXT ON SCREEN: ORION STATION // COORDINATES: HIGH ORBIT TRAPPIST 1-E //
# ORACLE STATUS: ONLINE // LEMs: 6 //
def card_1A4():
    rows = [("ORION STATION", None),
            ("COORDINATES", "HIGH ORBIT TRAPPIST 1-E"),
            ("ORACLE STATUS", "ONLINE"),
            ("LEMs", "6")]
    body = [f'<rect x="56" y="104" width="{W-112}" height="1" fill="{LINE}"/>',
            mono(56, 92, "ORION STATION", 22, INK, spacing=4.4, weight="500")]
    y = 142
    for label, value in rows[1:]:
        body.append(mono(56, y, label, 11, MUTED, spacing=2.6))
        body.append(mono(W - 56, y, value, 13,
                         AMBER if value == "ONLINE" else TEAL,
                         anchor="end", spacing=2.2))
        body.append(f'<rect x="56" y="{y + 13}" width="{W-112}" height="1" '
                    f'fill="{LINE}" opacity="0.6"/>')
        y += 44
    # A blinking cursor block, the one thing that says this is live.
    body.append(f'<rect x="56" y="{y - 10}" width="9" height="13" '
                f'fill="{AMBER}" opacity="0.85"/>')
    return frame("\n".join(body))


# ---- 1A-5 · Press Start ----------------------------------------------------
def card_1A5():
    cx = W // 2
    body = [mono(cx, 150, "PRESS START", 26, INK, anchor="middle",
                 spacing=6.5, weight="500"),
            f'<rect x="{cx-118}" y="178" width="236" height="1" '
            f'fill="{AMBER}" opacity="0.7"/>',
            mono(cx, 212, "TO BEGIN", 12, MUTED, anchor="middle", spacing=5)]
    return frame("\n".join(body))


# ---- 1C-3 · Quick Choice A -------------------------------------------------
def card_1C3():
    cx = W // 2
    body = [mono(56, 86, "QUICK CHOICE A", 11, AMBER, spacing=3.4),
            f'<rect x="56" y="98" width="{W-112}" height="1" fill="{LINE}"/>']
    for i, (label, sub) in enumerate((
            ("MOP THE HYGIENE PODS", "scene 1D"),
            ("BURN THE TRASH", "scene 1E"))):
        y = 146 + i * 92
        body.append(f'<rect x="56" y="{y-26}" width="{W-112}" height="62" '
                    f'fill="none" stroke="{LINE}"/>')
        body.append(mono(76, y, label, 16, INK, spacing=2.4))
        body.append(mono(76, y + 22, sub, 10, MUTED, spacing=2.6))
        body.append(f'<rect x="{W-82}" y="{y-9}" width="7" height="14" '
                    f'fill="{TEAL}" opacity="{0.8 if i == 0 else 0.3}"/>')
    body.append(mono(cx, 330, "DETERMINES WHICH SCENE PLAYS NEXT", 9.5,
                     MUTED, anchor="middle", spacing=3))
    return frame("\n".join(body))


CARDS = {"1A-4": card_1A4, "1A-5": card_1A5, "1C-3": card_1C3}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for pid, fn in CARDS.items():
        svg = fn()
        # A card that renders no glyphs is the one failure mode that matters:
        # the whole reason these are authored is that they must be readable.
        if "<text" not in svg:
            raise SystemExit(f"storyboard_cards: {pid} drew no text")
        (OUT / f"{pid}.svg").write_text(svg)
        print(f"wrote assets/img/sb/{pid}.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
