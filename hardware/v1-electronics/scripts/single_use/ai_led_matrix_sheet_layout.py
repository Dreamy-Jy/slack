"""ai_led_matrix_sheet_layout.py  -  redraws led_matrix.kicad_sch (two folders up) in the keyboard-shaped layout.

Run it AFTER ai_migrate_matrix_names.py (it looks the LEDs up by their new names, H1-LED1 ... H2-LED48).
Keep led_driver_order.png next to this script: it is embedded in the sheet as the read/write explainer.

What it does (connections do not change, only how the sheet is drawn):
  * moves every LED symbol to its place: key rows, thumb row, latch buttons, slide latches, encoders, and an
    indicator block (spare LED + CS14-16) under each half
  * each strand (3 LEDs on one current source) gets one anode wire with one label, inside a dashed outline
  * LEDs of the same sink set that sit in one column share a 4-wire bus on their right (blue, green, red, white);
    the outlines have gaps where a bus passes.  LEDs with no column partner keep a label on each cathode pin
  * group names on both halves, page enlarged to 1232 x 1000 mm, explainer image bottom left
"""
import base64, collections, pathlib, re, uuid

here = pathlib.Path(__file__).resolve()
path = here.parents[2] / 'led_matrix.kicad_sch'
image = here.parent / 'led_driver_order.png'

# ---- where every LED goes: {half: {LED number: (x, y)}}, mm, on the 2.54 grid ---------------------------------
COLS = {1: [160.02, 220.98, 284.48, 358.14, 421.64, 482.6], 2: [810.26, 871.22, 934.72, 1008.38, 1071.88, 1132.84]}
ROWS = [132.08, 200.66, 269.24, 335.28, 403.86]          # top row, rows 2-4, thumb row
ENCODERS, BUTTONS, SLIDES = 63.5, 474.98, [200.66, 269.24, 335.28]
INDICATOR_COLS = {1: [421.64, 482.6, 543.56], 2: [810.26, 871.22, 934.72]}
SPARE, INDICATOR_ROWS = 604.52, [673.1, 741.68, 810.26]
POS = {1: {}, 2: {}}
for h in (1, 2):
    for k in range(1, 31): POS[h][k] = (COLS[h][(k - 1) % 6], ROWS[(k - 1) // 6])
    for k in range(40, 49): POS[h][k] = (INDICATOR_COLS[h][(k - 40) % 3], INDICATOR_ROWS[(k - 40) // 3])
    POS[h][39] = (INDICATOR_COLS[h][2], SPARE)
for i in range(3):
    POS[1][31 + i] = (556.26, SLIDES[i]);            POS[2][36 - i] = (746.76, SLIDES[i])      # slide latches
    POS[1][34 + i] = (COLS[1][3 + i], BUTTONS);      POS[2][31 + i] = (COLS[2][i], BUTTONS)    # latch buttons
POS[1][38], POS[1][37] = (COLS[1][4], ENCODERS), (COLS[1][5], ENCODERS)
POS[2][37], POS[2][38] = (COLS[2][0], ENCODERS), (COLS[2][1], ENCODERS)
NAMES = {1: 'Top row', 3: 'Row 2', 5: 'Row 3', 7: 'Row 4', 9: 'Thumb row', 13: 'Encoders', 14: 'Indicators'}

r2 = lambda v: round(v, 2)
U = lambda: str(uuid.uuid4())
new = []                                              # everything this script draws


def wire(a, b):
    new.append(f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {r2(a[0])} {r2(a[1])}) (xy {r2(b[0])} {r2(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def dot(x, y):
    new.append(f'\n\t(junction\n\t\t(at {r2(x)} {r2(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')


def label(name, x, y, down=False, size=1.27):
    new.append(f'\n\t(label "{name}"\n\t\t(at {r2(x)} {r2(y)} {270 if down else 0})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify {"right" if down else "left"} bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def dash(a, b):
    new.append(f'\n\t(polyline\n\t\t(pts\n\t\t\t(xy {r2(a[0])} {r2(a[1])}) (xy {r2(b[0])} {r2(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0.4)\n\t\t\t(type dash)\n\t\t\t(color 120 130 145 1)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def text(s, x, y, size=2.2):
    new.append(f'\n\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {r2(x)} {r2(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness {size / 8})\n\t\t\t\t(color 0 0 194 1)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


# ---- 1. clear the old drawing, move the symbols ---------------------------------------------------------------
sheet = path.read_text()
end_of_file = sheet.rindex('\n)')                     # the file's closing bracket stays where it is
kept, seen = [], set()
for item in re.split(r'(?=\n\t\((?!\s))', sheet[:end_of_file]):
    kind = (re.match(r'\n\t\((\w+)', item) or [0, ''])[1]
    xs = [float(x) for x, _ in re.findall(r'\((?:at|xy|start|end) (-?[\d.]+) (-?[\d.]+)', item)]
    if kind == 'paper': item = '\n\t(paper "User" 1232 1000)'
    if kind in ('wire', 'junction', 'label') and max(xs) >= 120: continue          # old LED wiring
    if kind in ('rectangle', 'text') and (max(xs) >= 130 or 'Matrix Halve' in item): continue
    if kind in ('polyline', 'image'): continue
    if kind == 'symbol':
        m = re.search(r'"Reference" "H(\d)-LED(\d+)"', item)
        assert m, 'run ai_migrate_matrix_names.py first'
        h, k = int(m[1]), int(m[2]); seen.add((h, k))
        at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+) 90\)', item)
        dx, dy = POS[h][k][0] - float(at[1]), POS[h][k][1] - float(at[2])
        item = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+)', lambda q: f'(at {round(float(q[1]) + dx, 4)} {round(float(q[2]) + dy, 4)}', item)
        if not re.search(r'\(property "Value" "[^"]*"\n\t\t\t\(at [^\n]*\n\t\t\t\(hide yes\)', item):   # hide the part number
            item = re.sub(r'(\(property "Value" "[^"]*"\n\t\t\t\(at [^\n]*\n)', r'\1\t\t\t(hide yes)\n', item, count=1)
    kept.append(item)
assert len(seen) == 96, f'expected 96 LEDs, found {len(seen)}'

# ---- 2. cathodes: a shared bus per column where two or more LEDs of the same sink set line up ----------------
PIN_X = [-2.54, 2.54, 7.62, 12.7]                     # blue, green, red, white pin, from the symbol's origin
sink = lambda h, k, i: f'Chip{h}SinkSwitch{4 * ((k - 1) % 3) + i + 1}'
columns = collections.defaultdict(list)
for h in (1, 2):
    for k, (x, y) in POS[h].items(): columns[(h, (k - 1) % 3, x, k >= 39)].append(k)
buses = []                                            # (x from, x to, y from, y to) of each bus, for the outline gaps
for (h, _, x, _), ks in columns.items():
    if len(ks) < 2:                                   # nobody to share with: a label on each pin
        for i in range(4): label(sink(h, ks[0], i), x + PIN_X[i], POS[h][ks[0]][1] + 12.7, down=True, size=1.0)
        continue
    ks.sort(key=lambda k: POS[h][k][1])
    end = POS[h][ks[-1]][1] + 40.64
    buses.append((x + 31.4, x + 42.3, POS[h][ks[0]][1] + 12.7, end))
    for i in range(4):
        xb, taps = x + 33.02 + 2.54 * i, []
        for k in ks:
            px, py = x + PIN_X[i], POS[h][k][1] + 12.7
            y_tap = py + 2.54 * (4 - i)               # white taps highest, blue lowest, so taps never cross
            wire((px, py), (px, y_tap)); wire((px, y_tap), (xb, y_tap)); taps.append(y_tap)
        wire((xb, taps[0]), (xb, end))
        for y_tap in taps[1:]: dot(xb, y_tap)
        label(sink(h, ks[0], i), xb, end, down=True)

# ---- 3. strands: one anode wire + label, a dashed outline with gaps for the buses, a group name --------------
for h in (1, 2):
    for cs in range(1, 17):
        members = [3 * (cs - 1) + i for i in (1, 2, 3)]
        parts = [members] if cs != 13 else [members[:2], members[2:]]          # the spare sits apart from the encoders
        for ks in parts:
            P = sorted(POS[h][k] for k in ks)
            A = [(x - 12.7, y) for x, y in P]         # anode pins
            name = f'Chip{h}CurrentSource{cs}'
            if len({y for _, y in P}) == 1:           # side by side: wire above
                rail = P[0][1] - 12.7
                for ax, ay in A: wire((ax, ay), (ax, rail))
                wire((A[0][0] - 2.54, rail), (A[-1][0], rail)); label(name, A[0][0] - 2.54, rail)
                for ax, _ in A[:-1]: dot(ax, rail)
                x0, x1, y0, y1 = P[0][0] - 19, P[-1][0] + 46, P[0][1] - 18, P[0][1] + 36
            else:                                     # stacked (slide latches): wire down the left
                rail = A[0][0] - 2.54
                for ax, ay in A: wire((ax, ay), (rail, ay))
                wire((rail, A[0][1] - 10.16), (rail, A[-1][1])); label(name, rail, A[0][1] - 10.16)
                for _, ay in A[:-1]: dot(rail, ay)
                x0, x1, y0, y1 = P[0][0] - 19, P[0][0] + 30, P[0][1] - 26, P[-1][1] + 36
            dash((x0, y0), (x0, y1)); dash((x1, y0), (x1, y1))
            for y in (y0, y1):                        # top and bottom edge, skipping where a bus passes
                x = x0
                for a, b in sorted((a, b) for a, b, ya, yb in buses if ya < y < yb and a < x1 and b > x0):
                    if a > x: dash((x, y), (a, y))
                    x = max(x, b)
                if x < x1: dash((x, y), (x1, y))
            side_by_side = len({y for _, y in P}) == 1
            group = ('Spare' if ks == [39] else ('Latch buttons 1' if side_by_side else 'Latch buttons 2') if cs in (11, 12)
                     else NAMES.get(cs))
            if group: text(group, x0, y0 - 2.5)
    text(f'Half {h}  (LED driver {h})', 222 if h == 1 else 872, 28, size=5)

# ---- 4. the explainer picture ---------------------------------------------------------------------------------
b64 = base64.b64encode(image.read_bytes()).decode()
rows = '\n'.join(f'\t\t\t"{b64[i:i + 76]}"' for i in range(0, len(b64), 76))
new.append(f'\n\t(image\n\t\t(at 205 760)\n\t\t(scale 1.4)\n\t\t(uuid "{U()}")\n\t\t(data\n{rows}\n\t\t)\n\t)')

path.write_text(''.join(kept) + ''.join(new) + sheet[end_of_file:])
print(f'led_matrix.kicad_sch redrawn: 96 LEDs placed, {len(buses)} cathode buses, explainer embedded')
