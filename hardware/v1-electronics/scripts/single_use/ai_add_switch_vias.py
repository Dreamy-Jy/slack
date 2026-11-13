"""Add the via template (SW20's group, outlined on User.1) to every Cherry ULP switch.
Run on slack.kicad_pcb as committed in cb4c779, KiCad closed.  Board only.

Each via is placed relative to the part whose pad it serves, so it lands the same way on every key:
  switch pad 1 (column)   one via just above the pad
  diode pad 1 (row)       one via past the end of the diode
  LED pads 1-5            one via each, fanned out round the LED
LAYOUT = 'spread' moves the LED's three right-hand vias 0.7 mm apart, the closest the board rules allow.
LAYOUT = 'yours' keeps the template exactly; those three vias are 0.58 mm apart and break the clearance rules.
The 7 template vias are removed first and re-added with the rest.   python3 scripts/single_use/ai_add_switch_vias.py
"""
import math, pathlib, re, uuid

LAYOUT = 'spread'
path = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
pcb = path.read_text()

VIAS = {   # part: [(pad, x, y in the part's own coordinates)]
    'switch': [('1', -0.611, 0.146)],
    'diode':  [('1', -1.499, -0.029)],
    'led':    [('1', 1.192, -0.661), ('2', 1.173, -0.079), ('3', 1.109, 0.481), ('4', -1.046, 0.008), ('5', 0.033, -1.015)],
}
if LAYOUT == 'spread':
    VIAS['led'][:3] = [('1', 0.95, -0.75), ('2', 1.25, 0.0), ('3', 0.95, 0.75)]
TEMPLATE = ['175.98 94.2', '179.97 92.71', '179.85 93.28', '179.69 93.82', '177.65 92.98', '178.89 92.16', '177.78 96.19']

parts = {}
for m in re.finditer(r'\n\t\(footprint "([^"]*)".*?\n\t\)', pcb, re.S):
    c = m[0]
    at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', c)
    ref = re.search(r'"Reference" "([^"]*)"', c)[1]
    nets = dict(re.findall(r'\(pad "(\w+)" \w+ \w+\s.*?\(net "([^"]*)"\)', c, re.S))
    parts[ref] = (m[1], float(at[1]), float(at[2]), float(at[3] or 0), nets)


def board(ref, x, y):                                           # a part's own coordinates -> board coordinates
    _, px, py, a, _ = parts[ref]
    a = math.radians(a)
    return px + x * math.cos(a) + y * math.sin(a), py - x * math.sin(a) + y * math.cos(a)


new = []
for sw, (lib, *_, nets) in parts.items():
    if lib != 'Cherry:Cherry_ULP_SMD':
        continue
    led = 'LED' + sw[2:]
    diode = next(r for r, p in parts.items() if p[0] == 'Diode_SMD:D_SOD-523' and p[4].get('2') == nets['2'])
    for ref, kind in ((sw, 'switch'), (diode, 'diode'), (led, 'led')):
        for pad, x, y in VIAS[kind]:
            vx, vy = board(ref, x, y)
            new.append(f'\n\t(via\n\t\t(at {vx:.4f} {vy:.4f})\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")'
                       f'\n\t\t(net "{parts[ref][4][pad]}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')

for at in TEMPLATE:                                             # the template's own vias
    pcb, n = re.subn(r'\n\t\(via\n\t\t\(at ' + re.escape(at) + r'\)\n.*?\n\t\)', '', pcb, flags=re.S)
    assert n == 1, f'template via at {at} not found: is this the board from cb4c779?'
last = pcb.rindex('\n\t(via\n')
end = pcb.index('\n\t)', last) + 3
path.write_text(pcb[:end] + ''.join(new) + pcb[end:])
print(f'added {len(new)} vias ({LAYOUT} layout)')
