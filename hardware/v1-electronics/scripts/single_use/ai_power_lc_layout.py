"""Turn the LED-controller-1 group to the key slant, mirror it to the right half as LED controller 2,
and put the four power groups (USB-C, MP2721, AON7423, TPS61288) on one slanted line.
Plain text edit of slack.kicad_pcb (KiCad 10.0 format), written back in place - git has the old version.

Run from anywhere:  python3 scripts/single_use/ai_power_lc_layout.py
Made 2026-10-26 against the board as it was that day (the User.3 outlines below must still exist unchanged).
"""
import math, pathlib, re, uuid

IN  = pathlib.Path("/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/slack.kicad_pcb")
OUT = IN

SLANT    = -10.0          # the left-hand keys are rotated -10 deg; the right hand +10
MIRROR_X = 221.4484       # board centre line (mounting holes H1/H2 … mirror about it)

# --- group 1: LED controller 1 (rotate -10 deg about its User.3 outline centre, then mirror to LC2)
LC1_RECT  = (61.9, 130.14, 90.51, 150.92)
LC1_PARTS = ['IC3', 'C21', 'C22', 'C23', 'C24', 'C25', 'C34', 'C35', 'C36', 'R41', 'R42', 'R43']
LC2_OF    = {'IC3': 'IC4', 'C21': 'C26', 'C22': 'C27', 'C23': 'C28', 'C24': 'C29', 'C25': 'C30',
             'C34': 'C31', 'C35': 'C32', 'C36': 'C33', 'R41': 'R45', 'R42': 'R46', 'R43': 'R47'}

# --- group 2: the power chain, each rect is one rigid group; they get slid onto one -10 deg line
POWER = {   # name: (User.3 rect, parts)
    'USBC':     ((60.64, 75.33, 80.18, 93.08),   ['J1', 'D0', 'FL1']),
    'MP2721':   ((86.33, 83.63, 103.37, 99.28),  ['IC2', 'L1', 'C43', 'C46', 'C47', 'C49', 'C55', 'C40', 'C54', 'C50', 'R52', 'R53']),
    'AON7423':  ((110.4, 81.16, 120.32, 95.13),  ['Q1', 'R44', 'R48']),
    'TPS61288': ((125.78, 82.56, 159.8, 103.71), ['IC1', 'L2', 'C41', 'C42', 'C44', 'C45', 'C48', 'R50', 'R55', 'R56', 'C37', 'C38', 'C39']),
}
# The line: parallel to the key rows, LINE_OFFSET mm across from the USBC outline's centre (negative = toward the top
# edge).  USBC slides up its board edge onto it; the other groups slide along it by SLIDE.  Offset, slides and the two
# LC nudges are the smallest moves that keep every pad and body clear of the switches' alignment-peg holes
# (found with nudge.py / line_search.py; pads >= 0.25 mm from a hole edge, bodies off the holes).
LINE_OFFSET = -3.75
SLIDE = {'USBC': 0.0, 'MP2721': 3.0, 'AON7423': 0.25, 'TPS61288': 0.75}
LC1_NUDGE = (0.3, -2.4)        # after the rotation
LC2_NUDGE = (-2.8, 0.6)        # after the mirror (the peg holes are not mirror images: the footprint is only rotated)


def rot(x, y, deg):                       # KiCad rotation, y down, positive = counter-clockwise on screen
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), y * math.cos(a) - x * math.sin(a)

def norm(deg):                             # KiCad keeps angles in (-180, 180]
    deg = (deg + 180.0) % 360.0 - 180.0
    return 180.0 if deg == -180.0 else deg

def fmt(v):
    v = round(v, 6)
    return '0' if v == 0 else f'{v:.6f}'.rstrip('0').rstrip('.')

def centre(rect):
    return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2


class Board:
    def __init__(self, text):
        self.text = text

    def block(self, ref):
        """start, end of the (footprint …) block whose Reference property is ref"""
        m = re.search(r'\(property "Reference" "%s"' % re.escape(ref), self.text)
        start = self.text.rfind('(footprint ', 0, m.start())
        depth, i = 0, start
        while True:
            c = self.text[i]
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: return start, i + 1
            elif c == '"':                           # skip strings (they may hold parentheses)
                i += 1
                while self.text[i] != '"':
                    i += 2 if self.text[i] == '\\' else 1
            i += 1

    def place(self, ref):
        s, e = self.block(ref)
        m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', self.text[s:e])
        return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)

    def move(self, ref, x, y, angle):
        """set the footprint's place; pads/texts keep their local position but carry absolute angles"""
        s, e = self.block(ref)
        body = self.text[s:e]
        assert '(zone' not in body, ref + ' has a zone inside the footprint: not handled'
        old = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', body)
        d_angle = norm(angle - float(old.group(3) or 0))
        def turn(m):                                 # every other (at …) inside the block
            parts = m.group(1).split()
            a = float(parts[2]) if len(parts) > 2 else 0.0
            rest = parts[3:]
            return '(at %s %s %s%s)' % (parts[0], parts[1], fmt(norm(a + d_angle)), ''.join(' ' + r for r in rest))
        new = body[:old.start()] + '(at %s %s %s)' % (fmt(x), fmt(y), fmt(norm(angle))) + re.sub(r'\(at ([^)]*)\)', turn, body[old.end():])
        self.text = self.text[:s] + new + self.text[e:]


board = Board(IN.read_text())
log = []

# ---- LC1: rigid rotation about the outline centre
px, py = centre(LC1_RECT)
lc1 = {}
for ref in LC1_PARTS:
    x, y, a = board.place(ref)
    dx, dy = rot(x - px, y - py, SLANT)
    lc1[ref] = (px + dx + LC1_NUDGE[0], py + dy + LC1_NUDGE[1], norm(a + SLANT))
    board.move(ref, *lc1[ref])
    log.append(f'{ref:4} ({x:.2f}, {y:.2f}, {a:g}) -> ({lc1[ref][0]:.2f}, {lc1[ref][1]:.2f}, {lc1[ref][2]:g})')

# ---- LC2: mirror of the rotated LC1 (positions mirrored, angle -> 180 - angle)
for ref, (x, y, a) in lc1.items():
    ref2 = LC2_OF[ref]
    ox, oy, oa = board.place(ref2)
    new = (2 * MIRROR_X - x + LC2_NUDGE[0], y + LC2_NUDGE[1], norm(180 - a))
    board.move(ref2, *new)
    log.append(f'{ref2:4} ({ox:.2f}, {oy:.2f}, {oa:g}) -> ({new[0]:.2f}, {new[1]:.2f}, {new[2]:g})   mirror of {ref}')

# ---- power chain: move each group (rigid, no rotation) onto the line, then slide it along the line
ax, ay = centre(POWER['USBC'][0])
ux, uy = rot(1, 0, SLANT)                           # along the key rows (down-right on screen)
nx, ny = rot(0, 1, SLANT)                           # across them (down-left on screen)
shifts = {}
for name, (rect, parts) in POWER.items():
    cx, cy = centre(rect)
    along = (cx - ax) * ux + (cy - ay) * uy + SLIDE[name]
    tx, ty = ax + along * ux + LINE_OFFSET * nx, ay + along * uy + LINE_OFFSET * ny
    shifts[name] = (tx - cx, ty - cy)
    for ref in parts:
        x, y, a = board.place(ref)
        board.move(ref, x + shifts[name][0], y + shifts[name][1], a)
    log.append(f'{name:9} group moved by ({shifts[name][0]:+.2f}, {shifts[name][1]:+.2f})')

# ---- keep the User.3 outlines with their groups
def rect_text(rect):
    return r'\(gr_rect\s+\(start %s %s\)\s+\(end %s %s\)' % tuple(re.escape(fmt(v)) for v in rect)

text = board.text
for name, (rect, parts) in POWER.items():          # power rects: translate start/end
    dx, dy = shifts[name]
    m = re.search(rect_text(rect), text)
    text = text[:m.start()] + '(gr_rect\n\t\t(start %s %s)\n\t\t(end %s %s)' % (fmt(rect[0] + dx), fmt(rect[1] + dy), fmt(rect[2] + dx), fmt(rect[3] + dy)) + text[m.end():]
    label = {'MP2721': (96.46, 85.73), 'AON7423': (112.99, 82.98), 'TPS61288': (151.43, 84.96)}.get(name)
    if label:
        text = text.replace('(at %s %s 0)' % (fmt(label[0]), fmt(label[1])), '(at %s %s 0)' % (fmt(label[0] + dx), fmt(label[1] + dy)), 1)

def poly(points):                                   # a User.3 polygon from corner points
    pts = ' '.join('(xy %s %s)' % (fmt(x), fmt(y)) for x, y in points)
    return '(gr_poly\n\t\t(pts %s)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type default)\n\t\t)\n\t\t(fill no)\n\t\t(layer "User.3")\n\t\t(uuid "%s")\n\t)' % (pts, uuid.uuid4())

corners = [(LC1_RECT[0], LC1_RECT[1]), (LC1_RECT[2], LC1_RECT[1]), (LC1_RECT[2], LC1_RECT[3]), (LC1_RECT[0], LC1_RECT[3])]
lc1_poly = [(px + rot(x - px, y - py, SLANT)[0] + LC1_NUDGE[0], py + rot(x - px, y - py, SLANT)[1] + LC1_NUDGE[1]) for x, y in corners]
lc2_poly = [(2 * MIRROR_X - x + LC2_NUDGE[0], y + LC2_NUDGE[1]) for x, y in lc1_poly]
m = re.search(rect_text(LC1_RECT), text)
end = text.index('\n\t)', m.start()) + 3                        # end of that gr_rect
lc2_text = '(gr_text "LC2"\n\t\t(at %s %s 0)\n\t\t(layer "User.3")\n\t\t(uuid "%s")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t)' % (fmt(2 * MIRROR_X - 87.38 - 3 + LC2_NUDGE[0]), fmt(132.69 + LC2_NUDGE[1]), uuid.uuid4())
text = text[:m.start()] + poly(lc1_poly) + '\n\t' + poly(lc2_poly) + '\n\t' + lc2_text + text[end:]

OUT.write_text(text)
print('\n'.join(log))
print('wrote', OUT)
