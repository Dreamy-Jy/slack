"""ai_led_via_fixes.py  -  two fixes on slack.kicad_pcb (two folders up), after ai_led_matrix_refactor.py

1. Each input LED's anode via and white-cathode via move out from 1.0 mm to 1.5 mm from the LED centre.  That puts
   both outside the key switch's box on Dwgs.User (1.2 mm above and below the LED) and the white via on the same
   line as the diode's via.  The track from the pad is stretched with it.  Done on every input LED, keys or not.
2. The left half's diode vias are put back on the mirror image of their right-half twin's via (Part 2 moved the
   left diodes 0.5 mm but their vias stayed behind).  Any track ending on a moved via moves its end with it.
3. Diodes of the other inputs (latches, encoders, scroll click) get the same via the key diodes have: 0.5/0.2, on the
   row pad's side, 1.5 mm from the diode centre along its length, joined to the pad by a 0.2 mm front track.
4. Every diode via is joined to its diode's row pad: a stub that ends on the via but not on the pad (the left
   diodes' stubs were left at the old pad spot when the diodes moved) has its loose end put on the pad centre.
"""
import uuid
import math, pathlib, re

path = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
CENTRE = 192.3245
OUT = 1.5                       # new anode / white via distance from the LED centre (switch box edge 1.2 + via radius 0.25 + 0.05)
# diode twins, right: left (from ai_led_matrix_refactor.py's TWIN; diodes keep their switch's number)
TWIN = {15: 28, 16: 27, 17: 26, 18: 25, 19: 24, 20: 23, 21: 22, 29: 42, 30: 41, 31: 40, 32: 39, 33: 38, 34: 37, 35: 36,
        43: 54, 44: 53, 45: 52, 46: 51, 47: 50, 48: 49, 55: 66, 56: 65, 57: 64, 58: 63, 59: 62, 60: 61, 67: 78, 68: 77,
        69: 76, 70: 75, 71: 74, 72: 73, 2: 13, 3: 12, 4: 11, 5: 10, 6: 9, 7: 8}          # left: right

text = path.read_text()
num = lambda v: f'{v:.6f}'.rstrip('0').rstrip('.')
fps = {}
for m in re.finditer(r'\n\t\(footprint "([^"]*)"\n(?:(?!\n\t\().)*', text, re.S):
    c = m[0]; at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', c)
    ref = re.search(r'\(property "Reference" "([^"]*)"', c)[1]
    pads = {p[1]: (float(p[2]), float(p[3]), p[4]) for p in
            re.finditer(r'\(pad "([^"]*)"(?:(?!\n\t\t\(pad).)*?\(at (-?[\d.]+) (-?[\d.]+)(?:(?!\n\t\t\(pad).)*?\(net "([^"]*)"\)', c, re.S)}
    fps[ref] = dict(lib=m[1], x=float(at[1]), y=float(at[2]), rot=float(at[3] or 0), pads=pads)
vias = [dict(x=float(m[1]), y=float(m[2]), at=f'{m[1]} {m[2]}', net=m[3]) for m in
        re.finditer(r'\n\t\(via\n\t\t\(at (-?[\d.]+) (-?[\d.]+)\)(?:(?!\n\t\().)*?\(net "([^"]*)"\)', text, re.S)]


def to_local(f, x, y):
    a = math.radians(f['rot']); dx, dy = x - f['x'], y - f['y']
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)


def to_board(f, lx, ly):
    a = math.radians(f['rot'])
    return f['x'] + lx * math.cos(a) + ly * math.sin(a), f['y'] - lx * math.sin(a) + ly * math.cos(a)


moves = []                                          # (old 'x y' as written in the file, new x, new y)
# 1. anode (pad 5) and white (pad 4) vias out to the box edge
for ref, f in fps.items():
    if not f['lib'].startswith('Liteon'): continue
    for pad in ('5', '4'):
        px, py, net = f['pads'][pad]
        for v in vias:
            if v['net'] != net or math.dist((v['x'], v['y']), (f['x'], f['y'])) > 1.6: continue
            lx, ly = to_local(f, v['x'], v['y'])
            if abs(lx - px) < 0.02 and 0.95 < abs(ly) < 1.05:
                moves.append((v['at'], *to_board(f, px, math.copysign(OUT, ly))))
n1 = len(moves)
# 2. left diode vias onto the mirror of the right twin's via
for l, r in TWIN.items():
    L, R = fps.get(f'D{l}'), fps.get(f'D{r}')
    if not L or not R: continue
    row = R['pads']['1'][2]
    rv = [v for v in vias if v['net'] == row and math.dist((v['x'], v['y']), (R['x'], R['y'])) < 2]
    lv = [v for v in vias if v['net'] == L['pads']['1'][2] and math.dist((v['x'], v['y']), (L['x'], L['y'])) < 2.2]
    if len(rv) != 1 or len(lv) != 1: continue
    nx, ny = 2 * CENTRE - rv[0]['x'], rv[0]['y']
    if math.dist((nx, ny), (lv[0]['x'], lv[0]['y'])) > 0.001: moves.append((lv[0]['at'], nx, ny))

# 3. new vias for diodes that have none (a via already next to the row pad counts).  Right half: same spot as the key
# diodes in the diode's own frame; left half: the mirror of the right twin's via, or the mirrored spot if it has none.
twin_of = {f'D{l}': f'D{r}' for l, r in TWIN.items()}
new = []
for ref, f in fps.items():
    if not re.match(r'D\d+$', ref) or not f['lib'].endswith('D_SOD-523') or '1' not in f['pads']: continue
    row = f['pads']['1'][2]
    if not row.startswith('/MCU/Row') or any(v['net'] == row and math.dist((v['x'], v['y']), (f['x'], f['y'])) < 2.2 for v in vias): continue
    left = f['x'] < CENTRE
    R = fps.get(twin_of.get(ref, ''))
    rv = [v for v in vias if R and v['net'] == R['pads']['1'][2] and math.dist((v['x'], v['y']), (R['x'], R['y'])) < 2]
    x, y = (2 * CENTRE - rv[0]['x'], rv[0]['y']) if left and len(rv) == 1 else to_board(f, -1.499, 0.029 if left else -0.029)
    new.append((ref, row, to_board(f, f['pads']['1'][0], f['pads']['1'][1]), (x, y)))
u = lambda: str(uuid.uuid4())
add = ''.join(f'\n\t(via\n\t\t(at {num(x)} {num(y)})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{row}")\n\t\t(uuid "{u()}")\n\t)'
              f'\n\t(segment\n\t\t(start {num(px)} {num(py)})\n\t\t(end {num(x)} {num(y)})\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n\t\t(net "{row}")\n\t\t(uuid "{u()}")\n\t)'
              for ref, row, (px, py), (x, y) in new)
last = max(m.end() for m in re.finditer(r'\n\t\((?:via|segment)\n(?:(?!\n\t\().)*', text, re.S))
text = text[:last] + add + text[last:]

# apply: the via itself, and any track end sitting on it (matched by position, to 0.001 mm)
moved = {}
for at, nx, ny in moves:
    text, k = re.subn(rf'\(at {re.escape(at)}\)', f'(at {num(nx)} {num(ny)})', text); assert k == 1, at
    moved[tuple(map(float, at.split()))] = (nx, ny)


def end(m):
    x, y = float(m[2]), float(m[3])
    for (ox, oy), (nx, ny) in moved.items():
        if abs(x - ox) < 1e-3 and abs(y - oy) < 1e-3: return f'({m[1]} {num(nx)} {num(ny)})'
    return m[0]


text = re.sub(r'\((start|end) (-?[\d.]+) (-?[\d.]+)\)', end, text)

# 4. join each diode via to its row pad: move a stub's loose end onto the pad centre
SEG = re.compile(r'\(segment\n\t\t\(start (-?[\d.]+) (-?[\d.]+)\)\n\t\t\(end (-?[\d.]+) (-?[\d.]+)\)(\n\t\t\(width [\d.]+\)\n\t\t\(layer "F.Cu"\)\n\t\t\(net "([^"]*)"\))')
ends = [(float(m[i]), float(m[i + 1])) for m in SEG.finditer(text) for i in (1, 3)]
dvias = [(float(m[1]), float(m[2]), m[3]) for m in re.finditer(r'\n\t\(via\n\t\t\(at (-?[\d.]+) (-?[\d.]+)\)(?:(?!\n\t\().)*?\(net "([^"]*)"\)', text, re.S)]
pad_of = {}                                        # via (x, y) -> row pad centre of the diode it belongs to
for ref, f in fps.items():
    if re.match(r'D\d+$', ref) and f['lib'].endswith('D_SOD-523') and '1' in f['pads']:
        px, py, row = f['pads']['1']
        for x, y, n in dvias:
            if n == row and math.dist((x, y), (f['x'], f['y'])) < 2.2: pad_of[(x, y)] = to_board(f, px, py)
joined = 0


def join(m):
    global joined
    a, b = (float(m[1]), float(m[2])), (float(m[3]), float(m[4]))
    for via, end, keep in ((b, a, 'start'), (a, b, 'end')):
        pad = next((p for v, p in pad_of.items() if math.dist(v, via) < 1e-3), None)
        if pad is None or math.dist(end, pad) < 0.05: continue
        if sum(math.dist(e, end) < 1e-3 for e in ends) > 1: continue          # the other end goes somewhere: leave it
        joined += 1
        new = f'(start {num(pad[0])} {num(pad[1])})\n\t\t(end {m[3]} {m[4]})' if keep == 'start' else f'(start {m[1]} {m[2]})\n\t\t(end {num(pad[0])} {num(pad[1])})'
        return f'(segment\n\t\t{new}{m[5]}'
    return m[0]


text = SEG.sub(join, text)
path.write_text(text)
print(f'moved {n1} anode/white vias out to {OUT} mm, {len(moves) - n1} left-half diode vias onto their mirror spot; '
      f'{joined} diode stubs joined to their pad, new diode vias on {", ".join(r for r, *_ in sorted(new, key=lambda n: int(n[0][1:])))}')
