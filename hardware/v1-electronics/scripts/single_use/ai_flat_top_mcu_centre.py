"""Flat top edge, MCU on the centre line.  Run on slack.kicad_pcb as it is AFTER ai_rework_centre_and_pinout.py
(the board Jordane uploaded on 12 Nov).  Board only; the schematic does not change.

  outline     pocket removed; the top edge is one straight line (y = 48.89) between the two high corners
  mcu         U1 + its capacitors and pull-ups onto the mirror line, antenna at the new top edge
  antenna box rectangle on Dwgs.User, 20 mm out from every side of U1's antenna keep-out
  usb         J1, D0, FL1 to the top edge, left of the antenna box
  charger     IC2 group up 11.19 mm, thermistor pads up 3 mm; battery, on/off transistor, ladder, boost up 11 mm
  cc/reset    CC resistors, reset button and SWD header up beside / below the MCU
  graphics    the outline boxes and labels on User.3 and two copper shapes that the last script left behind
              are brought to their groups, and move with them from now on
  tracks      a track or via inside one group moves with it; one that joins two groups, or lies loose in the
              centre area, is removed; a via left with no track (other than DGND) is removed
  circles     the two guide circles drawn on F.Cu go to Dwgs.User (in copper they short the pads under them)
  ENCODERS_VERTICAL = True   also gives the four top encoders a quarter turn (they keep the 10 degree tilt of
              the switches under them); False leaves them as they are

Close KiCad and commit first (git is the undo).   python3 scripts/single_use/ai_flat_top_mcu_centre.py
"""
import math, pathlib, re, uuid

ENCODERS_VERTICAL = False
OUTER, INNER = -1.0, 2.6                                        # mm each pair's outer / inner encoder slides along its row (+ = towards the centre)
path = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
pcb = path.read_text()

MIRROR, TOP, RADIUS = 221.4484, 48.8923, 6.224
MCU = (MIRROR - 227.4, TOP + 0.09 - 74.38)                      # antenna keep-out's top edge lands on the board edge
GROUPS = {      # name: (box x0, x1, y0, y1 on the board as it is now,  dx, dy)
    'usb':        ((193.5, 212.5, 74.5, 86.4), -15.5, MCU[1]),
    'thermistor': ((190, 193.45, 85, 91), 1.1, -3),
    'charger':    ((193.5, 207.5, 88.6, 104.6), 1.1, -11.19),
    'battery':    ((193.5, 205, 105, 118.5), 0, -11),
    'switch':     ((208.5, 219.6, 106.9, 114), 0, -11),
    'ladder':     ((207, 224.2, 115.5, 124), 0, -11),
    'boost':      ((226, 253, 106.5, 121.5), 0, -11),
    'mcu':        ((220.5, 234, 74, 94), *MCU),
    'cc+reset':   ((238, 248, 92.5, 104.6), MCU[0], -19.5),
    'swd':        ((212.6, 217.7, 77.5, 82), 6.35, -3),
}
FRONT = {'J3': 'swd', 'SW84': 'cc+reset'}                       # front-side parts that belong to a group
TURN = {}                                                       # ref: (pivot x, y, degrees, new pivot x, y)
if ENCODERS_VERTICAL:                                           # each encoder and its six parts: a quarter turn, slid along its row
    for enc, parts, deg, slide in (('RE3/SW35', 'R9 R10 C5 R26 R12 C6', 90, OUTER), ('RE1/SW21', 'R1 R2 C1 R35 R4 C2', 90, INNER),
                                   ('RE2/SW22', 'C3 R6 R5 C4 R8 R7', -90, -INNER), ('RE4/SW36', 'C7 R14 R13 C8 R16 R15', -90, -OUTER)):
        at = re.search(r'"Reference" "' + enc + r'"', pcb).start()
        x, y = map(float, re.findall(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)', pcb[:at])[-1])
        tilt = math.radians(10 if deg > 0 else -10)             # the row runs 10 degrees off level, down towards the centre
        for ref in [enc] + parts.split():
            TURN[ref] = (x, y, deg, x + slide * math.cos(tilt), y + slide * math.sin(tilt))
LEFT_BEHIND = {  # first point of a graphic the last script did not move: what it should have done to it
    '(xy 211.05126 92.26)': (-9.35, 0), '(xy 211.69 96.79)': (-9.35, 0),                    # charger copper shapes
    '(start 204.051867 105.726544)': (2.5, 0), '(at 210.9 115.29': (2.5, 0),                # AON7423 box, label
    '(start 214.16 103.995)': (8, 2), '(at 239.81 106.395': (8, 2),                         # TPS61288 box, label
    '(xy 64.22153 125.41381)': (72.22547, 141.812818, 10, 129.0, 133.0), '(at 87.38 132.69': (72.22547, 141.812818, 10, 129.0, 133.0),
    '(xy 375.87527 126.01381)': (367.87133, 142.412818, -10, 313.9, 132.0), '(at 349.7168 133.29': (367.87133, 142.412818, -10, 313.9, 132.0),
}
POINT = re.compile(r'\((start|mid|end|at|xy|center) (-?[\d.]+) (-?[\d.]+)')


def num(v):
    return f'{v:.6f}'.rstrip('0').rstrip('.') or '0'


def group_at(x, y):
    for name, ((x0, x1, y0, y1), dx, dy) in GROUPS.items():
        if x0 <= x < x1 and y0 <= y < y1:
            return name


def turned(x, y, px, py, deg, qx, qy):                          # KiCad's sense: positive is anticlockwise on screen
    a = math.radians(deg)
    return qx + (x - px) * math.cos(a) + (y - py) * math.sin(a), qy - (x - px) * math.sin(a) + (y - py) * math.cos(a)


def shift(chunk, how):                                          # move every point of a loose item
    f = (lambda x, y: turned(x, y, *how)) if len(how) == 5 else (lambda x, y: (x + how[0], y + how[1]))
    return POINT.sub(lambda m: '({} {} {}'.format(m[1], *map(num, f(float(m[2]), float(m[3])))), chunk)


def fillet(ax, ay, bx, by, r):      # arc joining the line a->b (coming up the corner) to the flat top edge
    d = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / d, (by - ay) / d
    nx, ny = (-uy, ux) if ux > 0 else (uy, -ux)                 # the line's normal that points down into the board
    cy = TOP + r                                                # centre: r below the top edge, r inside the line
    t = (cy - ay - ny * r) / uy
    cx = ax + ux * t + nx * r
    m = math.hypot(nx, ny + 1)
    return (cx - nx * r, cy - ny * r), (cx - nx / m * r, cy - (ny + 1) / m * r), (cx, TOP)


starts = [m.start() for m in re.finditer(r'\n\t\(', pcb)] + [len(pcb)]
out, moved, removed = [pcb[:starts[0]]], {}, 0
for a, b in zip(starts, starts[1:]):
    chunk = pcb[a:b]
    kind = re.match(r'\n\t\((\w+)', chunk)[1]
    if kind == 'footprint':
        ref = re.search(r'\(property "Reference" "([^"]*)"', chunk)[1]
        at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', chunk)
        x, y, angle = float(at[1]), float(at[2]), float(at[3] or 0)
        name = FRONT.get(ref) or (group_at(x, y) if '(layer "B.Cu")' in chunk[:400] else None)
        turn = 0
        if ref in TURN:
            (nx, ny), turn, name = turned(x, y, *TURN[ref]), TURN[ref][2], 'encoders'
        elif name:
            nx, ny = x + GROUPS[name][1], y + GROUPS[name][2]
        if name:
            moved.setdefault(name, []).append(ref)
            if turn:                                            # every angle inside a footprint is stored absolute
                chunk = re.sub(r'(\n\t\t\t\(at -?[\d.]+ -?[\d.]+)(?: (-?[\d.]+))?\)',
                               lambda m: f'{m[1]} {num((float(m[2] or 0) + turn) % 360)})', chunk)
            chunk = chunk.replace(at[0], f'\n\t\t(at {num(nx)} {num(ny)}' + (f' {num(angle + turn)})' if angle + turn else ')'), 1)
            if ref == 'U1':                                     # its antenna keep-out is stored in board coordinates
                z = chunk.index('\n\t\t(zone\n')
                zone = shift(chunk[z:], (nx - x, ny - y)); chunk = chunk[:z] + zone
                xs, ys = zip(*[(float(p), float(q)) for p, q in re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', zone)[:4]])
                antenna = (min(xs), min(ys), max(xs), max(ys))
    elif kind in ('segment', 'arc', 'via', 'zone') or (kind.startswith('gr_') and 'Edge.Cuts' not in chunk and kind != 'gr_text_box'):
        left = next((how for needle, how in LEFT_BEHIND.items() if needle in chunk), None)
        if left:
            chunk = shift(chunk, left)
        where = {group_at(float(m[2]), float(m[3])) for m in POINT.finditer(chunk)}
        copper = '.Cu"' in chunk and kind in ('segment', 'arc', 'via', 'zone')
        loose = copper and where == {None} and any(190 <= float(m[2]) < 254 and 50 <= float(m[3]) < 125 for m in POINT.finditer(chunk))
        if kind == 'gr_circle' and '"F.Cu"' in chunk:           # the two guide circles were drawn in copper
            chunk = chunk.replace('(layer "F.Cu")', '(layer "Dwgs.User")')
        if copper and len(where) > 1 or loose and '(net "DGND")' not in chunk:      # joins two groups, or is in a group's way
            removed += 1
            continue
        if len(where) > 1:                                      # a drawing that spans more than one box: go with its centre
            pts = [(float(m[2]), float(m[3])) for m in POINT.finditer(chunk)]
            where = {group_at(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))}
        name = where.pop()
        if name:
            chunk = shift(chunk, GROUPS[name][1:])
    elif kind == 'gr_poly':                                     # the outline: drop the pocket, flatten the top edge
        item = r'\(xy [^)]*\)|\(arc\s*\(start [^)]*\)\s*\(mid [^)]*\)\s*\(end [^)]*\)\s*\)'
        items = re.findall(item, chunk)
        assert len(items) == 44 and '(start 192.5 70.2937)' in items[43], 'outline is not the one this script expects'
        s, m_, e = fillet(134.1614, 53.4545, 138.9796, 50.0748, RADIUS)
        arc = lambda p, q, r: '(arc\n\t\t\t\t(start {} {})\n\t\t\t\t(mid {} {})\n\t\t\t\t(end {} {})\n\t\t\t)'.format(*map(num, p + q + r))
        mir = lambda p: (2 * MIRROR - p[0], p[1])
        new = [arc(mir(e), mir(m_), mir(s))] + items[3:41] + [arc(s, m_, e)]
        first, last = chunk.index(items[0]), chunk.rindex(items[43]) + len(items[43])
        chunk = chunk[:first] + '\n\t\t\t'.join(new) + chunk[last:]
    out.append(chunk)
assert set(moved) >= set(GROUPS), 'a group was not found: is this the board after the first rework script?'

# the antenna box, then vias that lost their tracks
x0, y0, x1, y1 = antenna
box = (f'\n\t(gr_rect\n\t\t(start {num(x0 - 20)} {num(y0 - 20)})\n\t\t(end {num(x1 + 20)} {num(y1 + 20)})\n\t\t(stroke\n\t\t\t(width 0.15)\n'
       f'\t\t\t(type dash)\n\t\t)\n\t\t(fill no)\n\t\t(layer "Dwgs.User")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
ends = [(float(m[2]), float(m[3])) for c in out if c.startswith(('\n\t(segment', '\n\t(arc')) for m in POINT.finditer(c)]
keep = []
for c in out:
    if c.startswith('\n\t(via') and '(net "DGND")' not in c:
        m = POINT.search(c); x, y = float(m[2]), float(m[3])
        if not any(abs(x - p) < 0.02 and abs(y - q) < 0.02 for p, q in ends):
            removed += 1
            continue
    keep.append(c)
last = max(i for i, c in enumerate(keep) if c.startswith('\n\t(gr_'))
keep.insert(last + 1, box)
path.write_text(''.join(keep))
print(f'moved {sum(map(len, moved.values()))} parts in {len(moved)} groups, removed {removed} tracks and vias;'
      f' antenna box {num(x0 - 20)},{num(y0 - 20)} to {num(x1 + 20)},{num(y1 + 20)}')
