"""1. Put every key's diode on the outboard side of its LED (left half: diode to the left of the LED, right half: to the
right).  Cherry keys: the LED stays under the switch window, the diode moves to the other end of the pocket.  Latches and
encoders and the scroll wheels: LED and diode trade places (only the right scroll wheel, SW63, needs it; its FreeCAD
pocket is symmetric, so the pair still fits - the FreeCAD model just shows the LED on the other side until it is updated).
2. Line up the two columns of spare LEDs (LED511-518 / LED521-527) and centre them on the board's mirror line.
3. Centre each scroll wheel's RC-filter cluster over its encoder (the EC10E body's centre line is x = 2.5 in its frame,
through pin B1; the old columns at x = -0.5 / 4.0 straddled x = 1.75 instead).
Text edit of slack.kicad_pcb (KiCad 10.0), written back in place - git has the old version.

Run from anywhere:  python3 scripts/single_use/ai_diode_side_and_centre_leds.py
"""
import math, pathlib, re

IN  = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
OUT = IN

MIRROR_X = 221.4484                      # the board's left/right mirror line
LEFT_COLUMN  = ['LED511', 'LED512', 'LED513', 'LED514', 'LED515', 'LED517', 'LED518']
RIGHT_COLUMN = ['LED521', 'LED522', 'LED523', 'LED524', 'LED525', 'LED526', 'LED527']
RIGHT_X, TOP_Y, PITCH = 224.58, 139.8, 4.3   # Jordane's right column, kept; the left one becomes its mirror image

# scroll-wheel filters, (ref, x, y, angle) in the encoder's own frame: the EC10E pattern from ai_encoder_filters.py with
# both columns moved +0.75 so they sit at 2.5 -/+ 2.25.  A channel on the left (pin A1 at x 0), B channel on the right.
SCROLL_FILTERS = {
    'RE9':  [('R33', 0.25, -6.7, 0), ('R34', 0.25, -10.7, -90), ('C17', 0.25, -14.2, 180),
             ('R3',  4.75, -6.7, 180), ('R36', 4.75, -10.7, -90), ('C18', 4.75, -14.2, 0)],
    'RE10': [('R37', 0.25, -6.7, 0), ('R38', 0.25, -10.7, -90), ('C19', 0.25, -14.2, 180),
             ('R39', 4.75, -6.7, 180), ('R40', 4.75, -10.7, -90), ('C20', 4.75, -14.2, 0)],
}


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
        self.blocks = {}
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
        s, e = self.blocks[ref]; return self.text[s:e]

    def lib(self, ref):
        return re.match(r'\(footprint "([^"]+)"', self.body(ref)).group(1)

    def place(self, ref):
        m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', self.body(ref))
        return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)

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
        shift = len(new) - (e - s)
        self.blocks = {r: (a + (shift if a > s else 0), b + (shift if b > s else 0)) for r, (a, b) in self.blocks.items()}


board = Board(IN.read_text())
flipped = {'cherry': [], 'exchanged': []}

# ---- 1. diode on the outboard side of its LED
for ref in list(board.blocks):
    m = re.fullmatch(r'(?:RE\d+/)?SW(\d+)', ref)
    if not m or ref in ('SW7', 'SW8'): continue                     # plain SW7/SW8 = power slide and reset button
    n = m.group(1)
    if f'LED{n}' not in board.blocks or f'D{n}' not in board.blocks: continue
    lib = board.lib(ref)
    sx = board.place(ref)[0]
    outboard = -1 if sx < MIRROR_X else 1                           # which way the outer wall is, in board x
    lx, ly, la = board.place(f'LED{n}')
    dx, dy, da = board.place(f'D{n}')
    if (dx - lx) * outboard > 0: continue                           # diode already on the outer side
    if 'Cherry_ULP' in lib:                                         # LED stays under the window; diode to the other end
        board.move(f'D{n}', 2 * lx - dx, 2 * ly - dy, da)
        flipped['cherry'].append(ref)
    else:                                                           # centred pairs: trade places, keep each part's angle
        board.move(f'LED{n}', dx, dy, la)
        board.move(f'D{n}', lx, ly, da)
        flipped['exchanged'].append(ref)

# ---- 2. the two columns of spare LEDs, mirror images of each other about the centre line
for k, (left, right) in enumerate(zip(LEFT_COLUMN, RIGHT_COLUMN)):
    board.move(right, RIGHT_X, TOP_Y + k * PITCH, 0)
    board.move(left, 2 * MIRROR_X - RIGHT_X, TOP_Y + k * PITCH, 0)

# ---- 3. scroll-wheel filter clusters, centred over their encoders
for enc, parts in SCROLL_FILTERS.items():
    ex, ey, ea = board.place(enc)
    for ref, lx, ly, la in parts:
        bx, by = rot(lx, ly, ea)
        board.move(ref, ex + bx, ey + by, norm(la + ea))

OUT.write_text(board.text)
print(f"diode moved to the other end of the pocket on {len(flipped['cherry'])} Cherry keys: {' '.join(flipped['cherry'])}")
print(f"LED and diode traded places on {len(flipped['exchanged'])} others: {' '.join(flipped['exchanged'])}")
print('wrote', OUT)
