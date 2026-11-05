"""Remove the four bottom encoders RE5-RE8 and the parts that only serve them: their RC filters and matrix diodes.

Their LEDs (LED35, LED36, LED49, LED50) stay.  ai_shift_references.py renumbers everything afterwards.

Schematic  The 32 parts go from switch_matrix.kicad_sch, then whatever they leave hanging goes too: wires that now
           end in mid-air, junction dots that no longer join three ends, and labels, no-connect crosses and power
           arrows left standing alone.  On controller.kicad_sch the eight MCU pins that carried encoder channels
           5-8 trade their labels for no-connect crosses.
Board      The 32 footprints are deleted and those eight MCU pads become unconnected.  Nothing moves.

Text edit, written back in place: close KiCad and commit first (git is the undo).  Nothing is written unless every
check passes.
Run from anywhere:   python3 scripts/single_use/ai_remove_bottom_encoders.py
"""
import math, pathlib, re

HERE   = pathlib.Path(__file__).resolve().parents[2]            # hardware/v1-electronics
MATRIX = HERE / 'switch_matrix.kicad_sch'
MCU    = HERE / 'controller.kicad_sch'
BOARD  = HERE / 'slack.kicad_pcb'

REMOVE = ['RE5/SW35', 'R17', 'R18', 'R19', 'R20', 'C9',  'C10', 'D35',      # encoder, pull-ups and series resistors,
          'RE6/SW36', 'R21', 'R22', 'R23', 'R24', 'C11', 'C12', 'D36',      # filter caps, matrix diode
          'RE7/SW49', 'R25', 'R27', 'R11', 'R28', 'C13', 'C14', 'D49',
          'RE8/SW50', 'R29', 'R30', 'R31', 'R32', 'C15', 'C16', 'D50']
FREED_CHANNELS = [f'RotaryEncoder_{ab}Channel{n}' for n in (5, 6, 7, 8) for ab in 'AB']


def spans(text, kind):
    """(start, end) of every top-level '(kind ...)' item in a KiCad file, leading newline included."""
    found = []
    for m in re.finditer(r'\n\t\(%s\b' % kind, text):
        depth, i = 0, m.start() + 2
        while True:
            c = text[i]
            if c == '"':                                        # skip over a quoted string
                i += 1
                while text[i] != '"':
                    i += 2 if text[i] == '\\' else 1
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        found.append((m.start(), i + 1))
    return found


def cut(text, doomed):
    """The text without the given spans."""
    for start, end in sorted(doomed, reverse=True):
        text = text[:start] + text[end:]
    return text


def reference(item):
    return re.search(r'\(property "Reference" "([^"]+)"', item).group(1)


def point(x, y):
    return round(float(x) * 100), round(float(y) * 100)         # 0.01 mm grid, so equal places compare equal


# ------------------------------------------------------------------ 1. switch_matrix.kicad_sch
sheet = MATRIX.read_text()


def place(span):
    """Where a junction, label, no-connect cross or symbol sits."""
    return point(*re.search(r'\(at (-?[\d.]+) (-?[\d.]+)', sheet[span[0]:span[1]]).groups())


def library_pins(lib_id):
    """Pin ends of a library symbol in its own frame (y pointing up)."""
    start = sheet.index('\n\t\t(symbol "%s"' % lib_id)
    end = sheet.find('\n\t\t(symbol "', start + 1)
    return [(float(x), float(y)) for x, y in re.findall(r'\(pin \w+ \w+\s+\(at (-?[\d.]+) (-?[\d.]+)', sheet[start:end if end > 0 else None])]


def pin_points(span):
    """Where a placed symbol's pins end on the sheet."""
    item = sheet[span[0]:span[1]]
    x0, y0, angle = map(float, re.search(r'\(at (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)\)', item).groups())
    mirror = re.search(r'\n\t\t\(mirror (\w)\)', item)
    cos, sin = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    points = []
    for px, py in library_pins(re.search(r'\(lib_id "([^"]+)"\)', item).group(1)):
        x, y = px, -py                                          # the library's y points up, the sheet's points down
        x, y = x * cos + y * sin, y * cos - x * sin             # turned by the symbol's angle (counter-clockwise)
        if mirror and mirror.group(1) == 'y': x = -x
        if mirror and mirror.group(1) == 'x': y = -y
        points.append(point(x0 + x, y0 + y))
    return points


wires = {}                                                      # span -> its two end points
for span in spans(sheet, 'wire'):
    x1, y1, x2, y2 = re.search(r'\(xy (-?[\d.]+) (-?[\d.]+)\) \(xy (-?[\d.]+) (-?[\d.]+)\)', sheet[span[0]:span[1]]).groups()
    wires[span] = (point(x1, y1), point(x2, y2))
dots    = {place(s): s for s in spans(sheet, 'junction')}       # everything else, by the point it sits on
crosses = {place(s): s for s in spans(sheet, 'no_connect')}
labels  = {place(s): s for s in spans(sheet, 'label') + spans(sheet, 'hierarchical_label')}
arrows, kept_pins, gone, loose = {}, set(), set(), set()        # arrows = power symbols; loose = points that lost a pin
for span in spans(sheet, 'symbol'):
    ref = reference(sheet[span[0]:span[1]])
    if ref in REMOVE:
        gone.add(span)
        loose.update(pin_points(span))
    elif ref.startswith('#'):
        arrows[pin_points(span)[0]] = span
    else:
        kept_pins.update(pin_points(span))
assert len(gone) == len(REMOVE), 'some of the parts to remove are not on the sheet'


def passes(p, a, b):
    """The wire a-b runs through p without ending there."""
    return (p not in (a, b) and (b[0] - a[0]) * (p[1] - a[1]) == (b[1] - a[1]) * (p[0] - a[0])
            and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def here(things, p):
    """The label, cross, arrow or dot still standing on p, if any."""
    return things.get(p) if things.get(p) not in gone else None


while loose:                                                    # pull every loose thread until nothing is left hanging
    p = loose.pop()
    ending  = [w for w, ends in wires.items() if w not in gone and p in ends]
    passing = [w for w, ends in wires.items() if w not in gone and passes(p, *ends)]
    ways = len(ending) + 2 * len(passing) + (p in kept_pins)    # how many ways still lead away from this point
    if ways == 1 and ending and not here(labels, p) and not here(arrows, p):
        gone.add(ending[0])                                     # a wire that now ends in mid-air:
        loose.update(wires[ending[0]])                          # it goes, and both its ends get looked at again
    elif ways == 0:
        gone.update(s for s in (here(labels, p), here(crosses, p), here(arrows, p), here(dots, p)) if s)
    elif ways < 3 and here(dots, p):
        gone.add(dots[p])                                       # a junction dot needs three ends to join


# ------------------------------------------------------------------ 2. controller.kicad_sch
mcu = MCU.read_text()
new_crosses, old_labels = [], []
for span in spans(mcu, 'label'):
    label = mcu[span[0]:span[1]]
    if re.match(r'\n\t\(label "([^"]+)"', label).group(1) in FREED_CHANNELS:
        x, y = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)', label).groups()
        uuid = re.search(r'\(uuid "([^"]+)"\)', label).group(1)                 # the cross takes over the label's id
        new_crosses.append(f'\n\t(no_connect\n\t\t(at {x} {y})\n\t\t(uuid "{uuid}")\n\t)')
        old_labels.append(span)
assert len(old_labels) == len(FREED_CHANNELS), 'expected one label per freed channel on the MCU sheet'
mcu = cut(mcu, old_labels)
first_wire = mcu.index('\n\t(wire')                             # KiCad keeps no-connects just before the wires
mcu = mcu[:first_wire] + ''.join(sorted(new_crosses, key=lambda c: c.split('uuid')[1])) + mcu[first_wire:]

# ------------------------------------------------------------------ 3. slack.kicad_pcb
board = BOARD.read_text()
doomed = [s for s in spans(board, 'footprint') if reference(board[s[0]:s[1]]) in REMOVE]
assert len(doomed) == len(REMOVE), 'some of the parts to remove are not on the board'
board = cut(board, doomed)


def unhook(m):
    """One MCU pad that was on a freed channel: give it the name KiCad gives an unconnected pin."""
    pin_name, pad = m.group(1).rsplit('_', 1)                   # "P0.17_41" -> P0.17, 41
    return (f'(net "unconnected-(U1-{pin_name}-Pad{pad})")\n\t\t\t(pinfunction "{m.group(1)}")'
            f'\n\t\t\t(pintype "{m.group(2)}+no_connect")')


board, freed = re.subn(r'\(net "/MCU/RotaryEncoder_[AB]Channel[5-8]"\)\n\t\t\t\(pinfunction "([^"]+)"\)\n\t\t\t\(pintype "([^"]+)"\)', unhook, board)
assert freed == len(FREED_CHANNELS), 'expected exactly the eight MCU pads on the freed channels'

# ------------------------------------------------------------------ 4. every check has passed: write the three files
MATRIX.write_text(cut(sheet, gone))
MCU.write_text(mcu)
BOARD.write_text(board)

count = lambda things: sum(s in gone for s in things.values())
print(f'switch_matrix: {len(REMOVE)} parts, {sum(w in gone for w in wires)} wires, {count(dots)} junction dots, '
      f'{count(labels)} labels, {count(arrows)} power arrows, {count(crosses)} no-connect crosses removed')
print(f'controller: {len(old_labels)} channel labels replaced by no-connect crosses')
print(f'board: {len(doomed)} footprints deleted, {freed} MCU pads unhooked')
