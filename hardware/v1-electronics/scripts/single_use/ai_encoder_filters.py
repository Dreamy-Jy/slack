"""Place the encoder RC filters: one clean pattern per encoder type, applied in each encoder's own frame
(so the parts follow the encoder's angle).  Patterns are Jordane's RE1/SW7 and RE9 placements, straightened
and made symmetric.  Text edit of slack.kicad_pcb (KiCad 10.0), written back in place - git has the old version.

Run from anywhere:  python3 scripts/single_use/ai_encoder_filters.py
"""
import math, pathlib, re

IN  = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
OUT = IN

# Each channel: pull-up (V_REG0 <-> encoder pin), series (encoder pin <-> MCU net), cap (MCU net <-> GND).
# Offsets are in the encoder footprint's frame (x right, y down, before the encoder's rotation), angles too.
# Pad 1 of every resistor/cap is the first net named in the schematic: pull-up 1 = V_REG0, series 1 = MCU, cap 1 = MCU.
PEC11S = {   # Bourns PEC11S: pins A1/B1 at (-2.5, 7.3)/(2.5, 7.3); only the two shaft holes exist on the back
    'A': {'pullup': (-4.1, 4.3, 0),   'series': (-3.75, 1.0, -90), 'cap': (-4.2, -1.6, 180)},
    'B': {'pullup': (4.1, 4.3, 180),  'series': (3.75, 1.0, -90),  'cap': (4.2, -1.6, 0)},
}
EC10E = {    # Alps EC10E scroll encoder: pins A1/B1 at (0, 0)/(2.5, 0), through-hole; the tail hangs off -y
    'A': {'pullup': (-0.5, -6.7, 0),  'series': (-0.5, -10.7, -90), 'cap': (-0.5, -14.2, 180)},
    'B': {'pullup': (4.0, -6.7, 180), 'series': (4.0, -10.7, -90),  'cap': (4.0, -14.2, 0)},
}
NUDGE = {}   # encoder ref -> (dx, dy) in board mm, only where the straight pattern would hit something


def rot(x, y, deg):                       # KiCad rotation, y down, positive = counter-clockwise on screen
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), y * math.cos(a) - x * math.sin(a)

def norm(deg):
    deg = (deg + 180.0) % 360.0 - 180.0
    return 180.0 if deg == -180.0 else deg

def fmt(v):
    v = round(v, 6)
    return '0' if v == 0 else f'{v:.6f}'.rstrip('0').rstrip('.')


class Board:
    def __init__(self, text):
        self.text = text
        self.blocks = {}                                   # ref -> (start, end) of its (footprint …) block
        for m in re.finditer(r'\(property "Reference" "([^"]+)"', text):
            start = text.rfind('(footprint ', 0, m.start())
            self.blocks[m.group(1)] = (start, self._end(start))

    def _end(self, start):
        depth, i = 0, start
        while True:
            c = self.text[i]
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: return i + 1
            elif c == '"':
                i += 1
                while self.text[i] != '"':
                    i += 2 if self.text[i] == '\\' else 1
            i += 1

    def body(self, ref):
        s, e = self.blocks[ref]
        return self.text[s:e]

    def place(self, ref):
        m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', self.body(ref))
        return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)

    def pad_nets(self, ref):
        """{pad number: net name} for a footprint"""
        out = {}
        for pad in re.finditer(r'\(pad "([^"]*)"(.*?)\n\t\t\)', self.body(ref), re.S):
            n = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', pad.group(2))
            if n: out[pad.group(1)] = n.group(1)
        return out

    def move(self, ref, x, y, angle):
        s, e = self.blocks[ref]
        body = self.text[s:e]
        old = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', body)
        d_angle = norm(angle - float(old.group(3) or 0))
        def turn(m):                                      # pads and texts carry absolute angles
            parts = m.group(1).split()
            a = float(parts[2]) if len(parts) > 2 else 0.0
            return '(at %s %s %s%s)' % (parts[0], parts[1], fmt(norm(a + d_angle)), ''.join(' ' + r for r in parts[3:]))
        new = body[:old.start()] + '(at %s %s %s)' % (fmt(x), fmt(y), fmt(norm(angle))) + re.sub(r'\(at ([^)]*)\)', turn, body[old.end():])
        self.text = self.text[:s] + new + self.text[e:]
        shift = len(new) - (e - s)                         # keep the block index valid
        self.blocks = {r: (a + (shift if a > s else 0), b + (shift if b > s else 0)) for r, (a, b) in self.blocks.items()}


board = Board(IN.read_text())

# index the filter parts by their two nets
filters = {}                                               # frozenset(nets) -> ref
for ref in board.blocks:
    if re.fullmatch(r'R([1-9]|[1-3]\d|40)|C([1-9]|1\d|20)', ref):
        filters[frozenset(board.pad_nets(ref).values())] = ref

def find(net_a, net_b):
    return filters[frozenset({net_a, net_b})]

encoders = [r for r in board.blocks if 'PEC11S' in board.body(r)[:200] or 'EC10E' in board.body(r)[:200]]
for enc in sorted(encoders):
    tpl = PEC11S if 'PEC11S' in board.body(enc)[:200] else EC10E
    ex, ey, ea = board.place(enc)
    nets = board.pad_nets(enc)
    dx0, dy0 = NUDGE.get(enc, (0, 0))
    for ch in ('A', 'B'):
        pin_net = nets[ch + '1']                           # the encoder pin's own net, e.g. Net-(RE1/SW7-A)
        pullup = find('V_REG0', pin_net)
        series = next(r for k, r in filters.items() if pin_net in k and 'V_REG0' not in k)
        mcu_net = next(n for n in board.pad_nets(series).values() if n != pin_net)
        cap = find(mcu_net, 'DGND')
        for ref, (lx, ly, la) in zip((pullup, series, cap), (tpl[ch]['pullup'], tpl[ch]['series'], tpl[ch]['cap'])):
            bx, by = rot(lx, ly, ea)
            board.move(ref, ex + bx + dx0, ey + by + dy0, norm(la + ea))
        print(f'{enc:9} {ch}: pull-up {pullup:4} series {series:4} cap {cap:4}')

OUT.write_text(board.text)
print('wrote', OUT)
