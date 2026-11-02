"""Tidy Jordane's refactor rough-in of 2026-11-04 and make the top edge fit it:
1. RE1/RE3 (left) and RE2/RE4 (right) sit centred above the top-row keys SW6/SW5 and SW9/SW10, ENCODER_ABOVE_KEY up
   the column, turned like the keys; their RC filters get the PEC11S pattern (same as ai_encoder_filters.py) and the
   LED+diode pair sits between encoder and key, Cherry gap, diode outboard.
2. The top edge over the encoders is raised to the height of the H1/H2 mounting-hole bumps: the 10-degree stretch
   between the MCU cliff and the bump becomes the bump's own top line carried on, so the bump merges into the edge (its
   east corner and the flank below it go).  That straight edge runs STRAIGHT_PAST beyond the inner corner of the
   innermost encoder (RE1 / RE2) and only then drops to the MCU cliff at SLOPE_DEG from horizontal, with SLOPE_FILLET
   rounding the corner at the top and at the foot.
3. Latches SW72/SW73 and SW78/SW79 stand on end beside the inner-column keys SW34 / SW37, one above and one below
   the key's row, pair on their inboard side.  Buttons SW74-SW77 sit centred above their thumb keys with the pair beside.
4. The slide latches that stayed above the keys (SW69-71, SW80-82) are SS3235SL3 now, whose courtyard reaches 4.85 mm
   where the SSSS820201 had none, so their LED+diode pairs move from 5.9 to SLIDE_PAIR_Y below the switch.
Parts keep the angles Jordane gave them; only positions change.  Parked parts (RE5-RE8 below the board, SW7/J2/TH1/R57
above it) are not touched.
Text edit of slack.kicad_pcb (KiCad 10.0), written back in place - git has the old version.

Run from anywhere:  python3 scripts/single_use/ai_top_encoders_latches_edge.py
"""
import math, pathlib, re

IN  = pathlib.Path(__file__).resolve().parents[2] /'slack.kicad_pcb'
OUT = IN

MIRROR_X = 221.4484
STRAIGHT_PAST = 2.0               # the straight top edge ends this far past the innermost encoder's courtyard (see 2.)
SLOPE_DEG = 90.0                  # the drop from the raised edge to the MCU cliff, degrees from horizontal: vertical (the old chamfer was 44)
SLOPE_FILLET = 4.0                # radius of the two corners of each drop (was 2)
HALF_GAP = 1.225                  # half the Cherry LED-to-diode distance

ENCODERS = {'RE1/SW7': 'SW6', 'RE3/SW21': 'SW5', 'RE2/SW8': 'SW9', 'RE4/SW22': 'SW10'}   # encoder -> key it sits above
ENCODER_ABOVE_KEY = 25.0          # encoder centre up the key's column from the key centre (24.0 is the minimum)
ENCODER_PAIR_Y = 13.4             # LED/diode pair centre below the encoder centre: 11.6 above the key, the same height the pairs
                                  # under the slide latches have; 0.45 to the encoder courtyard (11.7), 0.85 to the key's
PEC11S = {   # RC filter parts in the encoder's frame, from ai_encoder_filters.py: pull-up, series resistor, cap per channel
    'A': {'pullup': (-4.1, 4.3, 0),   'series': (-3.75, 1.0, -90), 'cap': (-4.2, -1.6, 180)},
    'B': {'pullup': (4.1, 4.3, 180),  'series': (3.75, 1.0, -90),  'cap': (4.2, -1.6, 0)},
}

LATCHES = {'SW73': ('SW34', -1), 'SW72': ('SW34', +1), 'SW78': ('SW37', -1), 'SW79': ('SW37', +1)}  # latch -> (key, above/below)
LATCH_X, LATCH_Y = 12.75, 7.2     # key frame: sideways toward the board centre, and above/below the key's row line
LATCH_PAIR_Y = -6.4               # pair centre on the latch's inboard side, latch frame (courtyard ends at 4.85)
SLIDE_LATCHES = ['SW69', 'SW70', 'SW71', 'SW80', 'SW81', 'SW82']
SLIDE_PAIR_Y = 6.4                # pair centre below those latches, latch frame (was 5.9 for the SSSS820201)

BUTTONS = {'SW74': 'SW60', 'SW75': 'SW61', 'SW76': 'SW64', 'SW77': 'SW65'}   # latching button -> thumb key below it
BUTTON_ABOVE_KEY = 12.95          # key frame, up the column: button courtyard (3.3) then 0.15 to the key's courtyard (9.5)
BUTTON_PAIR_X = 4.75              # pair centre beside the button, button frame (courtyard ends at 3.3, diode is 1.25 long)


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

    def place(self, ref):
        m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', self.body(ref))
        return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)

    def pad_nets(self, ref):
        out = {}
        for pad in re.finditer(r'\(pad "([^"]*)"(.*?)\n\t\t\)', self.body(ref), re.S):
            n = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', pad.group(2))
            if n: out[pad.group(1)] = n.group(1)
        return out

    def move(self, ref, x, y, angle=None):
        s, e = self.blocks[ref]
        body = self.text[s:e]
        old = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', body)
        if angle is None: angle = float(old.group(3) or 0)
        d_angle = norm(angle - float(old.group(3) or 0))
        def turn(m):                                      # pads and texts carry absolute angles
            parts = m.group(1).split()
            a = float(parts[2]) if len(parts) > 2 else 0.0
            return '(at %s %s %s%s)' % (parts[0], parts[1], fmt(norm(a + d_angle)), ''.join(' ' + r for r in parts[3:]))
        new = body[:old.start()] + '(at %s %s %s)' % (fmt(x), fmt(y), fmt(norm(angle))) + re.sub(r'\(at ([^)]*)\)', turn, body[old.end():])
        self._splice(s, e, new)

    def _splice(self, s, e, new):
        self.text = self.text[:s] + new + self.text[e:]
        shift = len(new) - (e - s)
        self.blocks = {r: (a + (shift if a > s else 0), b + (shift if b > s else 0)) for r, (a, b) in self.blocks.items()}


board = Board(IN.read_text())

def outboard(ax, ay, bx, by):
    """of two candidate spots, (the one further from the centre line, the other one)"""
    return ((ax, ay), (bx, by)) if abs(ax - MIRROR_X) >= abs(bx - MIRROR_X) else ((bx, by), (ax, ay))

def place_pair(n, cx, cy, axis_deg, d_rule):
    """LED{n} and D{n} HALF_GAP either side of (cx, cy) along axis_deg; d_rule picks the diode's spot"""
    ax, ay = rot(HALF_GAP, 0, axis_deg)
    d_spot, led_spot = d_rule(cx + ax, cy + ay, cx - ax, cy - ay)
    board.move(f'D{n}', *d_spot); board.move(f'LED{n}', *led_spot)

# ---- 1. top encoders, their filters and pairs
filters = {}                                               # frozenset(nets) -> ref, for the encoder RC parts
for ref in board.blocks:
    if re.fullmatch(r'R([1-9]|[1-3]\d|40)|C([1-9]|1\d|20)', ref):
        filters[frozenset(board.pad_nets(ref).values())] = ref
for enc, key in ENCODERS.items():
    kx, ky, ka = board.place(key)
    ox, oy = rot(0, -ENCODER_ABOVE_KEY, ka)
    ex, ey, ea = kx + ox, ky + oy, ka
    board.move(enc, ex, ey, ea)
    nets = board.pad_nets(enc)
    for ch in ('A', 'B'):
        pin_net = nets[ch + '1']
        pullup = filters[frozenset({'V_REG0', pin_net})]
        series = next(r for k, r in filters.items() if pin_net in k and 'V_REG0' not in k)
        mcu_net = next(nn for nn in board.pad_nets(series).values() if nn != pin_net)
        cap = filters[frozenset({mcu_net, 'DGND'})]
        for ref, (lx, ly, la) in zip((pullup, series, cap), (PEC11S[ch]['pullup'], PEC11S[ch]['series'], PEC11S[ch]['cap'])):
            bx, by = rot(lx, ly, ea); board.move(ref, ex + bx, ey + by, norm(la + ea))
    n = re.search(r'SW(\d+)', enc).group(1)
    px, py = rot(0, ENCODER_PAIR_Y, ea)
    place_pair(n, ex + px, ey + py, ea, outboard)

# ---- 2. the top edge: push the 10-degree stretch out until the encoder courtyards have EDGE_MARGIN
def read_outline(text):
    poly = next(m for m in re.finditer(r'\n\t\(gr_poly\n.*?\n\t\)', text, re.S) if '(layer "Edge.Cuts")' in m.group(0))
    s = text.find('\n\t\t(pts', poly.start()); e = text.find('\n\t\t)', s) + 4
    entries = []
    for m in re.finditer(r'\(xy ([-\d.]+) ([-\d.]+)\)|\(arc\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(mid ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\)', text[s:e]):
        g = m.groups()
        entries.append(('xy', (float(g[0]), float(g[1]))) if g[0] is not None else
                       ('arc', ((float(g[2]), float(g[3])), (float(g[4]), float(g[5])), (float(g[6]), float(g[7])))))
    return s, e, entries

def write_outline(entries):
    out = ['\n\t\t(pts']
    for k, v in entries:
        if k == 'xy': out.append(f'\n\t\t\t(xy {fmt(v[0])} {fmt(v[1])})')
        else: out.append('\n\t\t\t(arc' + ''.join(f'\n\t\t\t\t({w} {fmt(p[0])} {fmt(p[1])})' for w, p in zip(('start', 'mid', 'end'), v)) + '\n\t\t\t)')
    return ''.join(out) + '\n\t\t)'

def arc_radius(a, b, c):
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    ux = ((a[0]**2 + a[1]**2) * (b[1] - c[1]) + (b[0]**2 + b[1]**2) * (c[1] - a[1]) + (c[0]**2 + c[1]**2) * (a[1] - b[1])) / d
    uy = ((a[0]**2 + a[1]**2) * (c[0] - b[0]) + (b[0]**2 + b[1]**2) * (a[0] - c[0]) + (c[0]**2 + c[1]**2) * (b[0] - a[0])) / d
    return math.hypot(a[0] - ux, a[1] - uy)

def unit(x, y):
    d = math.hypot(x, y); return x / d, y / d

def intersect(p, u, q, v):
    """point where line p + s*u meets line q + t*v"""
    den = u[0] * v[1] - u[1] * v[0]
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
    return p[0] + t * u[0], p[1] + t * u[1]

def fillet(corner, toward_prev, toward_next, r):
    """arc of radius r rounding the corner between two lines: (start on the incoming line, mid, end on the outgoing one)"""
    u, v = unit(*toward_prev), unit(*toward_next)
    theta = math.acos(max(-1, min(1, u[0] * v[0] + u[1] * v[1])))        # angle between the two rays
    t = r / math.tan(theta / 2)
    b = unit(u[0] + v[0], u[1] + v[1])
    m = r / math.sin(theta / 2) - r
    return ((corner[0] + u[0] * t, corner[1] + u[1] * t), (corner[0] + b[0] * m, corner[1] + b[1] * m), (corner[0] + v[0] * t, corner[1] + v[1] * t))

s, e, entries = read_outline(board.text)
N = len(entries)

def line(i, j):
    """the straight edge between the end of arc i and the start of arc j: (point, unit direction)"""
    p, q = entries[i][1][2], entries[j][1][0]
    return p, unit(q[0] - p[0], q[1] - p[1])

def outward(ln):
    p, u = ln; nrm = (u[1], -u[0])
    return nrm if (nrm[0] * (MIRROR_X - p[0]) + nrm[1] * (140 - p[1])) < 0 else (-nrm[0], -nrm[1])   # the normal pointing off the board

def chain(lines, radii, first_point, last_point):
    """arcs rounding the corners of consecutive lines (polygon order).  Each fillet keeps its old radius unless the
    straight piece next to it got too short, then it shrinks to what fits (never below 1 mm: router inside corners)."""
    corners = [intersect(*lines[k], *lines[k + 1]) for k in range(len(lines) - 1)]
    nodes = [first_point] + corners + [last_point]
    seg = [math.hypot(nodes[k + 1][0] - nodes[k][0], nodes[k + 1][1] - nodes[k][1]) for k in range(len(nodes) - 1)]
    arcs = []
    for k, c in enumerate(corners):
        (p, u), (q, v) = lines[k], lines[k + 1]
        theta = math.acos(max(-1, min(1, -u[0] * v[0] - u[1] * v[1])))
        room = min(seg[k] if k == 0 else seg[k] / 2, seg[k + 1] if k == len(corners) - 1 else seg[k + 1] / 2) - 0.05
        r = max(1.0, min(radii[k], room * math.tan(theta / 2)))
        arcs.append(('arc', fillet(c, (-u[0], -u[1]), v, r)))
    return arcs

# polygon order on the right half: MCU-cliff top edge -> slope -> (old 10-degree edge, flank) -> bump top -> ...
# (entries 0, 1, 2, 3, 4 end at the bump's near corner; entry 5 is its far corner).  Left half, last entries: ... bump far
# corner (N-6) -> near corner (N-5) -> flank fillet -> xy -> slope fillet -> cliff fillet (N-1).
def slope(top, old_slope, enc):
    """the new drop: SLOPE_DEG steep, starting on the top line STRAIGHT_PAST beyond the innermost courtyard corner of
    encoder enc (plus the bit the fillet takes); it runs down to the cliff's top edge wherever that lands"""
    p, u = top
    u_c = u if (MIRROR_X - p[0]) * u[0] > 0 else (-u[0], -u[1])             # along the top line, toward the board centre
    q, (vx, vy) = old_slope                                                  # only its sense is kept: it runs the polygon's way
    v = (math.copysign(math.cos(math.radians(SLOPE_DEG)), vx), math.copysign(math.sin(math.radians(SLOPE_DEG)), vy))
    down = v if v[1] > 0 else (-v[0], -v[1])                                 # the slope's downhill direction, for the angle
    ex, ey, ea = board.place(enc)
    inner = max((ex + dx - p[0]) * u_c[0] + (ey + dy - p[1]) * u_c[1] for cx in (-9.25, 9.25) for cy in (-10.5, 11.7) for dx, dy in [rot(cx, cy, ea)])
    theta = math.acos(max(-1, min(1, -u_c[0] * down[0] - u_c[1] * down[1])))   # angle between the two edges at the corner
    t = SLOPE_FILLET / math.tan(theta / 2)                                   # how much of the straight part the fillet takes
    top_corner = (p[0] + u_c[0] * (inner + STRAIGHT_PAST + t), p[1] + u_c[1] * (inner + STRAIGHT_PAST + t))
    return top_corner, v

right_top = line(4, 5)                      # the right bump's top line: this becomes the edge
left_top = line(N - 6, N - 5)               # the left bump's top line
notch = line(N - 1, 0)
right = [notch, slope(right_top, line(0, 1), 'RE2/SW8'), right_top]
left = [left_top, slope(left_top, line(N - 2, N - 1), 'RE1/SW7'), notch]
new_right = chain(right, [SLOPE_FILLET, SLOPE_FILLET], entries[N - 1][1][2], entries[5][1][0])
new_left = chain(left, [SLOPE_FILLET, SLOPE_FILLET], entries[N - 6][1][2], entries[0][1][0])
entries = new_right + entries[5:N - 5] + new_left
board._splice(s, e, write_outline(entries))

# ---- 3. latches beside the inner column, buttons above the thumb keys, with their pairs
for latch, (key, side) in LATCHES.items():
    kx, ky, ka = board.place(key)
    inboard = 1 if kx < MIRROR_X else -1
    ox, oy = rot(inboard * LATCH_X, side * LATCH_Y, ka)
    lx, ly, la = kx + ox, ky + oy, board.place(latch)[2]
    board.move(latch, lx, ly)
    px, py = rot(0, LATCH_PAIR_Y, la)
    place_pair(latch[2:], lx + px, ly + py, la, lambda ax, ay, bx, by: ((ax, ay), (bx, by)) if ay <= by else ((bx, by), (ax, ay)))   # diode = the upper spot
for btn, key in BUTTONS.items():
    kx, ky, ka = board.place(key)
    ox, oy = rot(0, -BUTTON_ABOVE_KEY, ka)
    bx, by, ba = kx + ox, ky + oy, board.place(btn)[2]
    board.move(btn, bx, by)
    px, py = rot(BUTTON_PAIR_X, 0, ba)
    place_pair(btn[2:], bx + px, by + py, ba + 90, outboard)

# ---- 4. pairs under the slide latches that kept their place
for latch in SLIDE_LATCHES:
    lx, ly, la = board.place(latch)
    px, py = rot(0, SLIDE_PAIR_Y, la)
    place_pair(latch[2:], lx + px, ly + py, la, outboard)

OUT.write_text(board.text)
print(f'top edge raised to the mounting-hole bumps\' height, straight past the inner encoders, then {SLOPE_DEG:g}-degree drops to the MCU cliff')
print('wrote', OUT)
