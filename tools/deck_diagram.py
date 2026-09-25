# -*- coding: utf-8 -*-
"""Author the deck diagram as SVG rather than generating it.

Every prompt in this project says "no readable text" because generators cannot
letter reliably, and a blueprint whose whole job is labelling scenes is exactly
what they are worst at. Authored SVG gets correct labels, real scene IDs, crisp
type at any zoom, ~20 KB instead of 3 MB, and it survives being edited when the
scene list changes."""
import pathlib
import re

# name, scene ids, side ('l'|'r'), height in units, kind
DECKS = [
 ("Boom anchor & parasol",  [],                                                  'r', 3,  'plant'),
 ("Data-centre stacks",     [],                                                  'l', 7,  'plant'),  # noqa
 ("Docking Bay",            ["S11"],                                             'r', 3,  'crew'),
 ("Observation Area",       ["S13","S14"],                                       'l', 2,  'crew'),
 ("Containment Chamber",    ["S15","S16","S20","S24","S36","S37","S45"],         'r', 3,  'hero'),
 ("Ops Assembly Deck",      ["S10","S12","S14","S15","S17","S18","S19","S22",
                             "S23","S24","S26","S28","S29","S30","S31","S32",
                             "S33","S34","S35","S36","S38","S40","S41","S43","S44"], 'l', 6, 'hero'),
 ("Control Center",         ["S06"],                                             'r', 2,  'crew'),
 ("Medpod Bay",             ["S19","S21"],                                       'l', 2,  'crew'),
 ("Crew quarters",          ["S08"],                                             'r', 2,  'crew'),
 ("Shower module · zero-g", ["S07"],                                             'l', 2,  'crew'),
 ("Hygiene pods",           ["S04"],                                             'r', 2,  'crew'),
 ("Biosphere Deck",         ["S07"],                                             'l', 4,  'crew'),
 ("Power & battery substation", ["S07"],                                         'r', 4,  'plant'),
 ("Waste Bay & incineration",   ["S03","S05"],                                   'l', 3,  'crew'),
 ("Sub-Deck C",             ["S25","S26"],                                       'r', 3,  'crew'),
 ("Escape pod bay",         ["S42"],                                             'l', 2,  'crew'),
 ("Engine block",           [],                                                  'r', 4,  'plant'),
]
NOTE = {
 "Boom anchor & parasol": "no scenes · structure only",
 "Data-centre stacks":    "no scenes · this is why the station is big",
 "Power & battery substation": "no scenes · S07 is in the shaft beside it",
 "Engine block":          "no scenes · never seen inside",
}
COL = {'plant': '#5f829f', 'crew': '#8fd0d6', 'hero': '#e879b0'}

U = 15            # px per height unit
TOP = 46          # space above the first deck
CX = 470          # column centre
HALF_TOP, HALF_BOT = 92, 52   # the column tapers
LABEL_L, LABEL_R = 300, 640

total = sum(d[3] for d in DECKS)
H = TOP + total * U + 74
rows, y = [], TOP
for name, ids, side, h, kind in DECKS:
    rows.append((name, ids, side, y, h * U, kind))
    y += h * U

def half(yy):
    t = (yy - TOP) / (total * U)
    return HALF_TOP + (HALF_BOT - HALF_TOP) * t

o = [f'<svg viewBox="0 0 940 {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
     f'aria-label="Deck diagram of Orion Station showing where every scene happens">',
     '<title>Orion Station · deck diagram</title>']

# the column body, tapering
o.append(f'<path d="M{CX-HALF_TOP},{TOP} L{CX+HALF_TOP},{TOP} '
         f'L{CX+HALF_BOT},{TOP+total*U} L{CX-HALF_BOT},{TOP+total*U} Z" '
         f'fill="#141f20" stroke="#40595a" stroke-width="1"/>')

# the boom and the parasol, above everything
o.append(f'<line x1="{CX}" y1="{TOP}" x2="{CX}" y2="18" stroke="#40595a" stroke-width="1.4" '
         f'stroke-dasharray="3,3"/>')
o.append(f'<line x1="{CX-190}" y1="14" x2="{CX+190}" y2="14" stroke="#8fd0d6" stroke-width="3"/>')
o.append(f'<text x="{CX-200}" y="32" fill="#8ba3a5" font-family="ui-monospace,monospace" '
         f'font-size="10" letter-spacing="1.4" text-anchor="end">RADIATOR PARASOL</text>')
o.append(f'<text x="{CX+200}" y="32" fill="#5f757d" font-family="ui-monospace,monospace" '
         f'font-size="9" letter-spacing="1.2">held off on the boom</text>')

for name, ids, side, yy, hh, kind in rows:
    hw = half(yy + hh/2)
    c = COL[kind]
    o.append(f'<rect x="{CX-hw:.0f}" y="{yy}" width="{hw*2:.0f}" height="{hh-2}" '
             f'fill="{c}" fill-opacity="{0.20 if kind=="hero" else 0.10}" '
             f'stroke="{c}" stroke-opacity=".55" stroke-width="1"/>')
    lx, anchor = (LABEL_L, 'end') if side == 'l' else (LABEL_R, 'start')
    ty = yy + hh/2
    ex = CX - hw if side == 'l' else CX + hw
    o.append(f'<line x1="{lx + (8 if side=="l" else -8)}" y1="{ty:.0f}" x2="{ex:.0f}" y2="{ty:.0f}" '
             f'stroke="{c}" stroke-opacity=".5" stroke-width="1"/>')
    o.append(f'<circle cx="{ex:.0f}" cy="{ty:.0f}" r="2.5" fill="{c}"/>')
    o.append(f'<text x="{lx}" y="{ty-1:.0f}" text-anchor="{anchor}" fill="#ececeb" '
             f'font-family="Helvetica,Arial,sans-serif" font-size="12.5">{name}</text>')
    if ids:
        # every scene has to be visible -- wrap rather than truncate, or a chunk
        # silently has nowhere to happen
        per = 9
        lines = [ids[k:k+per] for k in range(0, len(ids), per)]
        for n, line in enumerate(lines):
            o.append(f'<text x="{lx}" y="{ty+13+n*11:.0f}" text-anchor="{anchor}" fill="{c}" '
                     f'font-family="ui-monospace,monospace" font-size="9.5" '
                     f'letter-spacing="1">{" ".join(line)}</text>')
    else:
        o.append(f'<text x="{lx}" y="{ty+13:.0f}" text-anchor="{anchor}" fill="#5f757d" '
                 f'font-family="ui-monospace,monospace" font-size="9.5" '
                 f'letter-spacing="1">{NOTE.get(name, "no scenes")}</text>')

# the central shaft, running the whole height -- the thing the column design buys
o.append(f'<rect x="{CX-9}" y="{TOP}" width="18" height="{total*U}" fill="#0b1011" '
         f'stroke="#f0a63c" stroke-opacity=".6" stroke-width="1"/>')
o.append(f'<text x="{CX}" y="{TOP+total*U+18}" text-anchor="middle" fill="#f0a63c" '
         f'font-family="ui-monospace,monospace" font-size="9.5" letter-spacing="1.4">'
         f'CENTRAL SERVICE SHAFT · S07 S25 S27 · runs the full height</text>')
o.append(f'<text x="{CX}" y="{TOP+total*U+34}" text-anchor="middle" fill="#5f757d" '
         f'font-family="ui-monospace,monospace" font-size="9" letter-spacing="1.2">'
         f'EXTERIOR: S01 S09 S11 S37 S38 S39</text>')
# S02 is the narrator drifting through the interiors -- it belongs to no single deck
o.append(f'<text x="{CX}" y="{TOP+total*U+48}" text-anchor="middle" fill="#5f757d" '
         f'font-family="ui-monospace,monospace" font-size="9" letter-spacing="1.2">'
         f'MOVES THROUGH THE WHOLE COLUMN: S02</text>')
o.append('</svg>')
svg = '\n'.join(o)

# A scene with nowhere to happen is the failure this file exists to prevent.
placed = set(re.findall(r'S\d\d', svg))
missing = sorted({f'S{n:02d}' for n in range(1, 46)} - placed)
if missing:
    raise SystemExit(f'deck_diagram: {len(missing)} scene(s) placed nowhere: {missing}')

ROOT = pathlib.Path(__file__).resolve().parent.parent
hub = ROOT / 'index.html'
h = hub.read_text()
i = h.index('<div class="mapbox"><svg viewBox="0 0 940')
j = h.index('</svg>', i) + 6
hub.write_text(h[:i] + '<div class="mapbox">' + svg + h[j:])
print(f'deck_diagram: {len(rows)} decks, all 45 scenes placed, {len(svg)} bytes into index.html')
