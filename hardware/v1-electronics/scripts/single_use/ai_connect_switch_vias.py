"""Connect every MX ULP (MX6C) key's vias to their pads with one straight F.Cu track each.
Run after ai_add_switch_vias.py, KiCad closed.  Board only.   python3 scripts/single_use/ai_connect_switch_vias.py

For each Cherry ULP switch, its row diode and its LED:
  switch pad 1 (column)  -> its via   0.2 mm track
  diode pad 1 (row)      -> its via   0.2 mm track
  LED pads 1-5           -> their vias 0.127 mm track (the LED pads are 0.2 mm, the board minimum is 0.127)
A pad's via is the nearest via on the same net within 2.5 mm of the pad.  Vias that already have a track
ending on them are skipped, so the script can be run again safely.
"""
import math, pathlib, re, uuid

path = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
pcb = path.read_text()
WIDTH = {'switch': 0.2, 'diode': 0.2, 'led': 0.127}
PADS = {'switch': ['1'], 'diode': ['1'], 'led': ['1', '2', '3', '4', '5']}
REACH = 2.5
TEMPLATE = {   # where ai_add_switch_vias.py ('spread') puts each via, in the part's own coordinates
    'switch': {'1': (-0.611, 0.146)},
    'diode': {'1': (-1.499, -0.029)},
    'led': {'1': (0.95, -0.75), '2': (1.25, 0.0), '3': (0.95, 0.75), '4': (-1.046, 0.008), '5': (0.033, -1.015)},
}

parts = {}
for m in re.finditer(r'\n\t\(footprint "([^"]*)".*?\n\t\)', pcb, re.S):
    c = m[0]
    at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', c)
    ref = re.search(r'"Reference" "([^"]*)"', c)[1]
    pads = {}
    for p in re.finditer(r'\(pad "(\w+)" \w+ \w+\s+\(at (-?[\d.]+) (-?[\d.]+)[^)]*\).*?\(layers "([^"]*)".*?\(net "([^"]*)"\)', c, re.S):
        pads.setdefault(p[1], (float(p[2]), float(p[3]), p[4], p[5]))
    parts[ref] = (m[1], float(at[1]), float(at[2]), float(at[3] or 0), pads)

vias = [(float(x), float(y), n, f'{x} {y}') for x, y, n in
        re.findall(r'\n\t\(via\n\t\t\(at (-?[\d.]+) (-?[\d.]+)\).*?\(net "([^"]*)"\)', pcb, re.S)]
ends = {(round(float(x), 3), round(float(y), 3)) for x, y in
        re.findall(r'\n\t\t\((?:start|end) (-?[\d.]+) (-?[\d.]+)\)', pcb)}


def board(ref, x, y):                                           # a part's own coordinates -> board coordinates
    _, px, py, a, _ = parts[ref]
    a = math.radians(a)
    return px + x * math.cos(a) + y * math.sin(a), py - x * math.sin(a) + y * math.cos(a)


new, missing, renetted, skipped = [], [], [], 0
for sw, (lib, *_, swpads) in parts.items():
    if lib != 'Cherry:Cherry_ULP_SMD':
        continue
    diode = next((r for r, p in parts.items() if p[0] == 'Diode_SMD:D_SOD-523' and p[4].get('2', (0, 0, 0, None))[3] == swpads['2'][3]), None)
    for ref, kind in ((sw, 'switch'), (diode, 'diode'), ('LED' + sw[2:], 'led')):
        if ref not in parts:
            missing.append(f'{sw}: no {kind}')
            continue
        for pad in PADS[kind]:
            lx, ly, layer, net = parts[ref][4][pad]
            px, py = board(ref, lx, ly)
            near = [v for v in vias if v[2] == net and math.dist(v[:2], (px, py)) <= REACH]
            if not near and pad in TEMPLATE[kind]:                  # template via carrying the wrong net: give it the pad's
                tx, ty = board(ref, *TEMPLATE[kind][pad])
                hit = [v for v in vias if math.dist(v[:2], (tx, ty)) < 0.01 and (round(v[0], 3), round(v[1], 3)) not in ends]
                if hit:
                    v = hit[0]
                    block = re.search(r'\n\t\(via\n\t\t\(at ' + re.escape(v[3]) + r'\)\n.*?\n\t\)', pcb, re.S)
                    pcb = pcb[:block.start()] + block[0].replace(f'(net "{v[2]}")', f'(net "{net}")') + pcb[block.end():]
                    near = [(v[0], v[1], net, v[3])]
                    vias[vias.index(v)] = near[0]
                    renetted.append(f'{ref} pad {pad}: via {v[2]} -> {net}')
            if not near:
                missing.append(f'{ref} pad {pad} ({net})')
                continue
            vx, vy, *_ = min(near, key=lambda v: math.dist(v[:2], (px, py)))
            if (round(vx, 3), round(vy, 3)) in ends:
                skipped += 1
                continue
            new.append(f'\n\t(segment\n\t\t(start {px:.4f} {py:.4f})\n\t\t(end {vx:.4f} {vy:.4f})\n\t\t(width {WIDTH[kind]})'
                       f'\n\t\t(layer "{layer.split()[0]}")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')

last = pcb.rindex('\n\t(segment\n')
end = pcb.index('\n\t)', last) + 3
path.write_text(pcb[:end] + ''.join(new) + pcb[end:])
print(f'added {len(new)} tracks, {skipped} vias already connected')
for r in renetted:
    print('re-netted', r)
for m in missing:
    print('no via for', m)
