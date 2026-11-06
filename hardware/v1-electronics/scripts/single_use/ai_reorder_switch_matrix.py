"""Re-order the switch matrix to follow the board: latch row on top, thumbs one column outward, keys renumbered.

Rows        The latch row becomes Row1 and is drawn at the top of the switch matrix sheet; today's Row1-Row5 become
            Row2-Row6 and move down under it.  The MCU sheet is not touched: each MCU row pin now reads the row with
            its number (the pin that read the top key row reads the latches).
Thumbs      Both thumb halves move one column outward (left: Columns 1-6, right: Columns 9-14) and each scroll click
            is the third key from the outer edge (Column3, Column12).  RE5 and RE6, with their filters, are redrawn
            under their scroll clicks.
Numbers     Keys are numbered row by row, left to right: latches SW1-SW14, then SW15-SW78.  A key's diode and LED take
            its number.  The encoder clicks keep their encoder's name (RE1/SW21, RE2/SW22, RE3/SW35, RE4/SW36).
SW7, SW8    The latch buttons in Columns 7 and 8 become SW7 and SW8, so the on/off switch (power sheet) becomes SW83
            and the reset button (MCU sheet) SW84: the first numbers no switch, diode or LED uses.
LEDs        Same rule as before: each driver chip lights its half's keys in key order, then LED79-LED82, then the
            spares.  Symbols (driver slots) are renamed; each LED footprint keeps its place under its key and takes the
            link and the five nets of the symbol that now has its name.

On the board nothing moves and no track changes (no row, column, diode or LED net has copper yet).  Footprints get
their new names, the matrix diodes their new row nets, and the six thumb keys that change column their new column net.

Text edit, written back in place: close KiCad and commit first (git is the undo).  Nothing is written unless every
check passes.
Run from anywhere:   python3 scripts/single_use/ai_reorder_switch_matrix.py
"""
import pathlib, re, uuid

HERE = pathlib.Path(__file__).resolve().parents[2]              # hardware/v1-electronics

# ------------------------------------------------------------------ the two orders, as numbers of today's keys
TODAY = [                                                       # 0 = no key in that column
    [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14],   # Row1
    [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],   # Row2
    [29, 30, 31, 32, 33, 34,  0,  0, 35, 36, 37, 38, 39, 40],   # Row3
    [41, 42, 43, 44, 45, 46,  0,  0, 47, 48, 49, 50, 51, 52],   # Row4
    [ 0, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,  0],   # Row5: thumbs; SW58, SW59 are the scroll clicks
    [65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78],   # Row6: latches
]
AFTER = [
    [65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78],   # Row1: latches
    [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14],   # Row2
    [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],   # Row3
    [29, 30, 31, 32, 33, 34,  0,  0, 35, 36, 37, 38, 39, 40],   # Row4
    [41, 42, 43, 44, 45, 46,  0,  0, 47, 48, 49, 50, 51, 52],   # Row5
    [53, 54, 58, 55, 56, 57,  0,  0, 60, 61, 62, 59, 63, 64],   # Row6: thumbs
]
ENCODER_CLICKS = {7: 'RE1', 8: 'RE2', 21: 'RE3', 22: 'RE4'}     # keys whose switch is inside an encoder
OTHER_SWITCHES = {'power.kicad_sch': ('SW7', 'SW83'), 'controller.kicad_sch': ('SW8', 'SW84')}

where_today = {n: (r, c) for r, row in enumerate(TODAY, 1) for c, n in enumerate(row, 1) if n}
where_after = {n: (r, c) for r, row in enumerate(AFTER, 1) for c, n in enumerate(row, 1) if n}
NUMBER = {n: i for i, n in enumerate((n for row in AFTER for n in row if n), start=1)}     # today's -> new number
ROW = {today: new for new, today in enumerate([6, 1, 2, 3, 4, 5], start=1)}              # today's row -> new row
assert where_today.keys() == where_after.keys()
assert all(ROW[where_today[n][0]] == where_after[n][0] for n in NUMBER), 'a key changes row in the tables'
moved = {n: (where_today[n][1], where_after[n][1]) for n in NUMBER if where_today[n][1] != where_after[n][1]}
assert sorted(moved) == [53, 54, 58, 59, 63, 64], 'only six thumb keys change column'


def switch(n, number):                                          # its name (an encoder click carries its encoder's)
    return f'{ENCODER_CLICKS[n]}/SW{number}' if n in ENCODER_CLICKS else f'SW{number}'


NAMES = {}                                                      # today's name -> new name: switches and diodes
for n, new in NUMBER.items():
    NAMES[switch(n, n)] = switch(n, new)
    NAMES[f'D{n}'] = f'D{new}'

# LEDs: a symbol is a driver slot, a footprint is a place under a key (chip 1 lights Columns 1-7, chip 2 Columns 8-14)
SLOT = {}                                                       # a symbol's name -> new name
for chip, columns in ((1, range(1, 8)), (2, range(8, 15))):
    slots_today = sorted(n for n in NUMBER if where_today[n][1] in columns)     # the keys it lights, in today's order
    slots_after = sorted(NUMBER[n] for n in slots_today)                         # the same keys, in the new order
    SLOT.update({f'LED{a}': f'LED{b}' for a, b in zip(slots_today, slots_after)})
PLACE = {f'LED{n}': f'LED{new}' for n, new in NUMBER.items()}   # a footprint's name -> new name
WIRING_OF = {new: old for old, new in SLOT.items()}             # a new name -> the symbol whose slot goes with it

# ------------------------------------------------------------------ where things are drawn (mm)
COLUMN_X = [33.02, 60.96, 88.9, 116.84, 144.78, 172.72, 200.66, 444.5, 469.9, 497.84, 525.78, 553.72, 581.66, 609.6]
LABEL_Y = 27.94                                                 # the column labels, where every column wire starts
LATCH_UP = -246.38                                              # latch row: its taps go to y 38.1, Row1's today
MAIN_DOWN = 60.96                                               # Rows 1-5 move down under it
THUMB_ROW_Y = 256.54                                            # today's Row5 wire, redrawn through the moved diodes
ENCODERS = {                                                    # box around each block today -> (dx, dy)
    'RE5': ((215, 220, 305, 270), (-129.54, 101.6)),            # its body right under the left scroll click
    'RE6': ((355, 220, 440, 270), (124.46, 101.6)),             # its body right under the right scroll click
}
NEW_PLACE = {'Latch Row': (660.4, 17.78), 'Main Matrix': (655.32, 78.74), 'separator': 73.66}


def mm(v):
    return f'{round(v, 4):.4f}'.rstrip('0').rstrip('.')


def moved_by(item, dx, dy):
    """The item with every point in it shifted by (dx, dy)."""
    return re.sub(r'(\((?:at|xy) )(-?[\d.]+) (-?[\d.]+)',
                  lambda m: f'{m.group(1)}{mm(float(m.group(2)) + dx)} {mm(float(m.group(3)) + dy)}', item)


def points(item):
    return [(float(x), float(y)) for x, y in re.findall(r'\((?:at|xy) (-?[\d.]+) (-?[\d.]+)', item)]


def inside(box, item, kind):
    x0, y0, x1, y1 = box
    pts = points(item) if kind == 'wire' else points(item)[:1]
    return all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)


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


def reference(item):
    return re.search(r'\(property "Reference" "([^"]+)"', item).group(1)


def rename(text, names):
    """New references for the parts in `names` (a schematic keeps each reference in two places, a board in one)."""
    return re.sub(r'(\(property "Reference" |\(reference )"([^"]+)"',
                  lambda m: f'{m.group(1)}"{names.get(m.group(2), m.group(2))}"', text)


def wire(template, x1, y1, x2, y2):
    return re.sub(r'\(pts\s+\(xy [^)]*\) \(xy [^)]*\)', f'(pts\n\t\t\t(xy {mm(x1)} {mm(y1)}) (xy {mm(x2)} {mm(y2)})',
                  re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{uuid.uuid4()}")', template))


def junction(template, x, y):
    return re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{uuid.uuid4()}")', re.sub(r'\(at [^)]*\)', f'(at {mm(x)} {mm(y)})', template))


files = {}                                                      # file -> its new text, written at the very end

# ------------------------------------------------------------------ 1. the switch matrix sheet
matrix = (HERE / 'switch_matrix.kicad_sch').read_text()
assert '(label "Row6"\n\t\t(at 27.94 312.42 180)' in matrix, 'the latch row is not at the bottom: already re-ordered?'
for n, (old, new) in moved.items():                             # each moving thumb key is where the table says
    assert f'(property "Reference" "{switch(n, n)}"' in matrix
    sw = next(matrix[s:e] for s, e in spans(matrix, 'symbol') if reference(matrix[s:e]) == switch(n, n))
    assert abs(points(sw)[0][0] - COLUMN_X[old - 1] - (5.08 if n in (58, 59) else 7.62)) < 0.01, f'SW{n} has moved'

edits, taps = [], {x: set() for x in COLUMN_X}                  # (start, end, new text); column x -> its taps' y
wire_template = junction_template = None
for kind in ('wire', 'junction', 'no_connect', 'label', 'symbol', 'text', 'polyline'):
    for start, end in spans(matrix, kind):
        item = matrix[start:end]
        (x, y), pts = points(item)[0], points(item)
        if kind in ('wire', 'junction') and all(px in COLUMN_X and px == x for px, py in pts):
            # a column wire or a junction on one: dropped, then each column is redrawn top to bottom through its taps
            if kind == 'wire':
                wire_template = wire_template or item
                c = COLUMN_X.index(x) + 1
                for _, ty in pts:
                    if ty == LABEL_Y:
                        continue
                    if ty > 270:                                # latch row tap
                        taps[x].add(ty + LATCH_UP)
                    else:                                       # key rows; a thumb key's tap follows its key
                        thumb = [n for n, (old, new) in moved.items() if old == c and 240 < ty < 250]
                        taps[COLUMN_X[moved[thumb[0]][1] - 1] if thumb else x].add(ty + MAIN_DOWN)
            else:
                junction_template = junction_template or item
            edits.append((start, end, ''))
        elif kind in ('wire', 'junction') and all(py == THUMB_ROW_Y for px, py in pts):
            edits.append((start, end, ''))                      # the thumb row wire: redrawn below
        elif kind == 'label' and re.match(r'\s*\(label "Column\d+"', item):
            continue                                            # column labels stay at the top
        elif kind == 'text':
            name = re.search(r'\(text "([^"]+)"', item).group(1)
            edits.append((start, end, moved_by(item, NEW_PLACE[name][0] - x, NEW_PLACE[name][1] - y)))
        elif kind == 'polyline':
            edits.append((start, end, moved_by(item, 0, NEW_PLACE['separator'] - y)))
        else:
            for box, (dx, dy) in ENCODERS.values():
                if inside(box, item, kind):
                    break
            else:
                dx, dy = 0, (LATCH_UP if y > 270 else MAIN_DOWN)
                for n, (old, new) in moved.items():             # the switch, diode and short wires of a thumb key
                    if inside((COLUMN_X[old - 1], 235, COLUMN_X[old - 1] + 15, 255), item, kind):
                        dx = COLUMN_X[new - 1] - COLUMN_X[old - 1]
            edits.append((start, end, moved_by(item, dx, dy)))
assert len([e for e in edits if e[2] == '']) == 78 + 64 + 12 + 11, 'unexpected column or thumb row wiring'

new_wires, new_junctions = [], []
for x, ys in taps.items():                                      # each column from its label down to its last tap
    ys = [LABEL_Y] + sorted(ys)
    new_wires += [wire(wire_template, x, a, x, b) for a, b in zip(ys, ys[1:])]
    new_junctions += [junction(junction_template, x, y) for y in ys[1:-1]]
thumb_y = THUMB_ROW_Y + MAIN_DOWN                               # the thumb row: label, then each diode's cathode
xs = [27.94] + [COLUMN_X[c - 1] + 10.16 for c, n in enumerate(AFTER[5], 1) if n]
new_wires += [wire(wire_template, a, thumb_y, b, thumb_y) for a, b in zip(xs, xs[1:])]
new_junctions += [junction(junction_template, x, thumb_y) for x in xs[1:-1]]

first_wire = min(s for s, e, t in edits if t == '' and matrix[s:e].startswith('\n\t(wire'))
first_junction = min(s for s, e, t in edits if t == '' and matrix[s:e].startswith('\n\t(junction'))
for start, end, text in sorted(edits, reverse=True):            # last one first, so earlier positions stay valid
    if start == first_wire:
        text = ''.join(new_wires)
    if start == first_junction:
        text = ''.join(new_junctions)
    matrix = matrix[:start] + text + matrix[end:]
matrix = re.sub(r'\(label "Row(\d)"', lambda m: f'(label "Row{ROW[int(m.group(1))]}"', matrix)
files[HERE / 'switch_matrix.kicad_sch'] = rename(matrix, NAMES)

# ------------------------------------------------------------------ 2. the LED sheet, and SW7/SW8 on their sheets
leds = (HERE / 'led_matrix.kicad_sch').read_text()
assert all(leds.count(f'(reference "{led}")') == 1 for led in SLOT), 'some key LEDs are not on the LED sheet'
files[HERE / 'led_matrix.kicad_sch'] = rename(leds, SLOT)
for sheet, (old, new) in OTHER_SWITCHES.items():
    text = (HERE / sheet).read_text()
    assert text.count(f'"{old}"') == 2 and f'"{new}"' not in text, f'{old} is not where expected on {sheet}'
    files[HERE / sheet] = rename(text, {old: new})

# ------------------------------------------------------------------ 3. the board: names and nets, nothing moves
board = (HERE / 'slack.kicad_pcb').read_text()
wiring = {}                                                     # an LED footprint -> (link to its symbol, pad nets)
for start, end in spans(board, 'footprint'):
    fp = board[start:end]
    if reference(fp) in PLACE:
        assert re.findall(r'\(pad "(\d)"', fp) == list('12345'), 'unexpected LED pads'
        wiring[reference(fp)] = (re.search(r'\(path "([^"]+)"\)', fp).group(1), re.findall(r'\(net "([^"]*)"\)', fp))
    if reference(fp) == 'D65':
        assert '(net "/MCU/Row6")' in fp, 'D65 is not on the latch row: already re-ordered?'
assert len(wiring) == len(PLACE), 'some key LEDs are not on the board'

for start, end in reversed(spans(board, 'footprint')):
    fp, ref = board[start:end], reference(board[start:end])
    if ref in PLACE:                                            # LED: new name, the link and nets of its new slot
        path, nets = wiring[WIRING_OF[PLACE[ref]]]
        nets = iter(nets)
        fp = fp.replace(f'(property "Reference" "{ref}"', f'(property "Reference" "{PLACE[ref]}"')
        fp = re.sub(r'\(path "[^"]+"\)', f'(path "{path}")', fp)
        fp = re.sub(r'\(net "[^"]*"\)', lambda m: f'(net "{next(nets)}")', fp)
    elif ref in NAMES and ref.startswith('D'):                  # matrix diode: its row's new number
        fp = re.sub(r'\(net "/MCU/Row(\d)"\)', lambda m: f'(net "/MCU/Row{ROW[int(m.group(1))]}")', fp)
    for n, (old, new) in moved.items():
        if ref == switch(n, n):                                 # thumb key that changes column
            assert f'(net "/MCU/Column{old}")' in fp
            fp = fp.replace(f'(net "/MCU/Column{old}")', f'(net "/MCU/Column{new}")')
    board = board[:start] + fp + board[end:]

board_names = {**NAMES, **dict(OTHER_SWITCHES.values())}
board = rename(board, board_names)
board = re.sub(r'\(net "((?:Net|unconnected)-\()(RE\d+/SW\d+|SW\d+|D\d+)(-[^"]*)"\)',   # net names KiCad built
               lambda m: f'(net "{m.group(1)}{board_names.get(m.group(2), m.group(2))}{m.group(3)}")', board)
refs = [r for r in re.findall(r'\(property "Reference" "([^"]+)"', board) if r != 'REF**']
assert len(refs) == len(set(refs)), 'two footprints would share a name'
files[HERE / 'slack.kicad_pcb'] = board

# ------------------------------------------------------------------ 4. the scroll-bar transfer script's table
porter = HERE / 'scripts' / 'layout_support' / 'layout_porter' / 'ai_transfer_scrollbars.py'
script = porter.read_text()
for old, new in [(f'("{kind}{n}"', f'("{kind}{NUMBER[n]}"') for n in (58, 59) for kind in ('SW', 'LED', 'D')]:
    assert script.count(old) == 1, f'{old} is not in {porter.name} exactly once'
    script = script.replace(old, new)
files[porter] = script

# ------------------------------------------------------------------ 5. every check has passed: write the files
for path, text in files.items():
    path.write_text(text)
print(f'switch matrix: latch row on top, {len(moved)} thumb keys moved, {len(NAMES)} switch and diode names changed')
print(f'LED sheet: {sum(a != b for a, b in SLOT.items())} LED names changed; on/off switch is SW83, reset button SW84')
print(f'board: {len(PLACE)} LED footprints re-wired in place, row nets of {len(NUMBER)} diodes and column nets of '
      f'{len(moved)} thumb keys changed, nothing moved')
