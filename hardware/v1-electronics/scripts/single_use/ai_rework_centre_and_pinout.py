"""One pass over the board and the controller sheet: new floor plan for everything that is not an input device,
then the MCU pinout that suits it.  Replaces ai_refactor_mcu_pinout.py, ai_antenna_clearance_rev.py and
ai_floorplan_rev.py; run it on the board as committed in a55d204.

FLOOR PLAN   (whole groups move; inside a group every part, track and via keeps its place relative to the others)
  outline       notch in the top edge widened from 199.8..243.1 to 192.5..250.4 mm (antenna clearance)
  usb+charger   J1, D0, FL1, IC2 and its parts     9.35 mm left, against the notch's left wall
  mcu           U1, its capacitors and pull-ups, J3, reset button, CC parts     5.76 mm left
  boost         IC1, L2 and its parts              8 mm right, 2 mm down: clear of the mirror line, away from the charger
  load switch   Q1, R44, R48                       2.5 mm right, between charger and boost
  battery       J2 to just under the charger; thermistor pads TH1 + R57 3.2 mm left
  LED drivers   IC3 and IC4 with their parts to the middle of their own half, turned square to the board
  ladder        interrupt resistors R62-R65, JP2-JP4 to below the MCU
  status LEDs   D87, D90 out from under the USB connector
  Prototype tracks that ran from one group to another are removed; they no longer line up.

PINOUT   going clockwise round U1 (seen from the back) the pads follow the compass direction of each signal:
  right side, top to bottom   right top encoders, top-right columns, columns 11 and 10
  bottom, right to left       column 9, right LED driver, right scroll wheel (~{INT} between its two channels),
                              the two driver interrupts (met at the ladder), left scroll wheel
  six centre pads             the six rows
  left side, bottom to top    left LED driver, charger interrupt, columns 6-4, columns 1-3, left top encoders, column 7
  Not moved: USB D+/D-, CC1/CC2 (AIN6/AIN7), I2C (P0.11/P0.12), SWD, RESET (P0.18), power.  ~{INT} stays on an
  analog pin (P0.05 = AIN3).  Left free: P0.09/P0.10 (NFC), P0.00/P0.01 (32.768 kHz crystal pins), P1.02.

Text edit of slack.kicad_pcb and controller.kicad_sch, written back in place: close KiCad and commit first (git is
the undo).  Nothing is written unless every check passes.
Run from anywhere:   python3 scripts/single_use/ai_rework_centre_and_pinout.py
"""
import math, pathlib, re

HERE = pathlib.Path(__file__).resolve().parents[2]              # hardware/v1-electronics
pcb_path, sch_path = HERE / 'slack.kicad_pcb', HERE / 'controller.kicad_sch'
pcb, sch = pcb_path.read_text(), sch_path.read_text()

# ---------------------------------------------------------------- floor plan ----------------------------------
GROUPS = {      # name: (boxes x0, x1, y0, y1 around the group as committed,  move dx, dy)
    'usb+charger':  ([(203, 221.9, 74, 88.6), (203, 217.5, 88.6, 104.5)], -9.35, 0),
    'mcu':          ([(221.9, 256, 74, 104.5)], -5.76, 0),
    'load switch':  ([(206.5, 218.2, 106.8, 114)], 2.5, 0),
    'boost':        ([(218.2, 249, 104.6, 124)], 8, 2),
    'thermistor':   ([(193.5, 197, 84.8, 91.2)], -3.2, 0),
    'battery':      ([(186.5, 200.5, 94, 108)], 5.6, 11.2),
    'ladder':       ([(275.5, 294, 102, 111.5)], -68.9, 12.9),
    'left driver':  ([(64, 85, 129, 150)], 0, 0),               # these two turn as well: see TURN
    'right driver': ([(355, 376, 129, 150)], 0, 0),
}
TURN = {        # name: (pivot as committed = the IC's centre,  degrees to turn,  where the pivot goes)
    'left driver':  ((72.22547, 141.812818), 10, (129.0, 133.0)),
    'right driver': ((367.87133, 142.412818), -10, (313.9, 132.0)),
}
BY_NAME = {'J3': 'mcu', 'SW84': 'mcu'}                          # front-side parts that belong to a group
STATUS_LEDS = {'D87': 9.5, 'D90': 9.5}
LED_NETS = ('Net-(D87-A)', 'Net-(D90-A)', 'PG{slash}NTC2', 'STAT{slash}IB')
POINT = re.compile(r'\((start|mid|end|at|xy) (-?[\d.]+) (-?[\d.]+)')


def group_at(x, y):
    for name, (boxes, dx, dy) in GROUPS.items():
        if any(x0 <= x < x1 and y0 <= y < y1 for x0, x1, y0, y1 in boxes):
            return name


def num(v):
    return f'{v:.6f}'.rstrip('0').rstrip('.') or '0'


def place(name, x, y):                                          # where a point of this group ends up
    if name in TURN:
        (px, py), deg, (qx, qy) = TURN[name]
        a = math.radians(deg)                                   # KiCad's sense: positive is anticlockwise on screen
        return qx + (x - px) * math.cos(a) + (y - py) * math.sin(a), qy - (x - px) * math.sin(a) + (y - py) * math.cos(a)
    return x + GROUPS[name][1], y + GROUPS[name][2]


starts = [m.start() for m in re.finditer(r'\n\t\(', pcb)] + [len(pcb)]
out = [pcb[:starts[0]]]
moved, removed = {}, 0
for a, b in zip(starts, starts[1:]):
    chunk = pcb[a:b]
    kind = re.match(r'\n\t\((\w+)', chunk)[1]
    if kind == 'footprint':
        ref = re.search(r'\(property "Reference" "([^"]*)"', chunk)[1]
        at = re.search(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', chunk)
        x, y, angle = float(at[1]), float(at[2]), float(at[3] or 0)
        name = BY_NAME.get(ref) or (group_at(x, y) if '(layer "B.Cu")' in chunk[:400] else None)
        if ref in STATUS_LEDS:
            name, (nx, ny), turn = 'status LEDs', (x + STATUS_LEDS[ref], y), 0
        elif name:
            (nx, ny), turn = place(name, x, y), TURN.get(name, (0, 0))[1]
        if name:
            moved.setdefault(name, []).append(ref)
            if turn:                                            # every angle inside a footprint is stored absolute
                chunk = re.sub(r'(\n\t\t\t\(at -?[\d.]+ -?[\d.]+)(?: (-?[\d.]+))?\)',
                               lambda m: f'{m[1]} {num((float(m[2] or 0) + turn) % 360)})', chunk)
            chunk = chunk.replace(at[0], f'\n\t\t(at {num(nx)} {num(ny)}' + (f' {num(angle + turn)})' if angle + turn else ')'), 1)
            if ref == 'U1':                                     # its antenna keep-out is stored in board coordinates
                zone = chunk.index('\n\t\t(zone\n')
                chunk = chunk[:zone] + re.sub(r'\(xy (-?[\d.]+)', lambda m: '(xy ' + num(float(m[1]) + nx - x), chunk[zone:])
    elif kind in ('segment', 'arc', 'via', 'zone', 'gr_rect') and '.Cu"' in chunk:
        points = [(float(m[2]), float(m[3])) for m in POINT.finditer(chunk)]
        swd, led = '/MCU/SWD' in chunk, any(n in chunk for n in LED_NETS)
        where = {'mcu' if swd and group_at(x, y) else 'gone' if led and x < 204 and y < 88 else group_at(x, y) for x, y in points}
        loose = where == {None} and any(190 <= x < 222 and 84 <= y < 127 for x, y in points)
        if len(where) > 1 or 'gone' in where or loose or where == {'battery'}:      # between groups, or in a group's way
            removed += 1
            continue
        name = where.pop()
        if name:
            assert name not in TURN, 'a turned group has tracks; this script does not turn tracks'
            chunk = POINT.sub(lambda m: '({} {} {}'.format(m[1], *map(num, place(name, float(m[2]), float(m[3])))), chunk)
    elif kind == 'gr_poly' and 'Edge.Cuts' in chunk:            # the outline: slide the notch's four corner arcs
        left, right, slope = 192.5 - 199.826827, 250.4 - 243.055435, 0.17596     # the raised edge falls 10 degrees
        corners = {'(start 199.826827 70.2937)': (left, 0), '(start 196.520012 58.202939)': (left, left * slope),
                   '(start 239.055435 74.2937)': (right, 0), '(start 243.055435 62.144976)': (right, -right * slope)}
        for first, (dx, dy) in corners.items():
            arc = re.search(re.escape(first) + r'\s*\(mid [^)]*\)\s*\(end [^)]*\)', chunk)
            chunk = chunk.replace(arc[0], POINT.sub(lambda m: f'({m[1]} {num(float(m[2]) + dx)} {num(float(m[3]) + dy)}', arc[0]))
    out.append(chunk)
assert len(moved) == len(GROUPS) + 1, 'a group was not found: has this script already been run?'
pcb = ''.join(out)

# ---------------------------------------------------------------- pinout --------------------------------------
A, B = 'RotaryEncoder_AChannel', 'RotaryEncoder_BChannel'
PADS = {                                                        # U1 pad number -> label on the controller sheet
    3: 'Column8', 4: A + '2', 5: B + '2', 6: A + '4', 7: B + '4', 8: 'Column12', 9: 'Column13', 10: 'Column14',
    11: 'Column11', 13: 'Column10',
    16: 'Column9', 19: 'LEDMatrix2Shutdown', 20: B + '6', 21: '~{INT}', 22: A + '6', 23: '~{LEDMatrix2Interrupt}',
    24: '~{LEDMatrix1Interrupt}', 25: B + '5', 26: A + '5',
    36: 'LEDMatrix1Shutdown', 37: '~{ChargingChipInterrupt}', 38: 'Column6', 39: 'Column5', 41: 'Column4',
    42: 'Column1', 43: 'Column2', 44: 'Column3', 45: A + '3', 46: B + '3', 47: A + '1', 48: B + '1', 49: 'Column7',
    56: 'Row2', 57: 'Row3', 58: 'Row1', 59: 'Row4', 60: 'Row5', 61: 'Row6',
}
FREE = [17, 18, 50, 52, 54]
BOARD_NET = {'LEDMatrix1Shutdown': '/LED Matricies/Chip1Shutdown', 'LEDMatrix2Shutdown': '/LED Matricies/Chip2Shutdown',
             '~{LEDMatrix1Interrupt}': '/LED Matricies/~{Chip1Interrupt}',
             '~{LEDMatrix2Interrupt}': '/LED Matricies/~{Chip2Interrupt}'}

# schematic: every signal pin of U1 has a label or a no-connect mark sitting exactly on its end
u1 = re.search(r'\(symbol\n\t\t\(lib_id "RF_Module:MDBT50Q-1MV2"\)\n\t\t\(at ([\d.]+) ([\d.]+) 0\)', sch)
x0, y0 = float(u1[1]), float(u1[2])
lib = sch[sch.index('(symbol "RF_Module:MDBT50Q-1MV2"'):]
pin_end = {}                                                    # pad number -> (x, y) of the pin end on the sheet
for px, py, number in re.findall(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) \d+\).*?\(number "(\d+)"', lib[:lib.index('\n\t\t(symbol "', 10)], re.S):
    pin_end[int(number)] = (round(x0 + float(px), 2), round(y0 - float(py), 2))
MARK = re.compile(r'\t\((label|hierarchical_label|no_connect)(?: "([^"]*)")?\n(?:\t\t\(shape \w+\)\n)?\t\t\(at ([\d.]+) ([\d.]+)(?: (\d+))?\)'
                  r'(?:\n\t\t\(effects\n\t\t\t\(font\n\t\t\t\t\(size [\d. ]+\)\n\t\t\t\)\n\t\t\t\(justify (\w+)\)\n\t\t\))?')
ours = set(PADS) | set(FREE)
spot = {pin_end[p]: p for p in ours}
written = {spot[float(m[3]), float(m[4])]: (m[3], m[4]) for m in MARK.finditer(sch) if (float(m[3]), float(m[4])) in spot}
assert set(written) == ours, sorted(ours - set(written))
new_pad = {label: pad for pad, label in PADS.items()}
free, done = iter(FREE), []


def move(m):
    if (float(m[3]), float(m[4])) not in spot:
        return m[0]                                             # not at one of U1's pins (e.g. the ladder's labels)
    pad = next(free) if m[1] == 'no_connect' else new_pad[m[2]]
    done.append(pad)
    x, y = written[pad]
    text = m[0].replace(f'(at {m[3]} {m[4]}', f'(at {x} {y}')
    if m[1] != 'no_connect':
        left = float(x) < x0                                    # pins on the symbol's left side read right-to-left
        text = text.replace(f'(at {x} {y} {m[5]})', f'(at {x} {y} {180 if left else 0})')
        text = text.replace(f'(justify {m[6]})', f'(justify {"right" if left else "left"})')
    return text


sch = MARK.sub(move, sch)
assert sorted(done) == sorted(ours), 'a pin got two marks or none'

# board: U1's pads take the nets of their new pins
start = pcb.index('(footprint "RF_Module:Raytac_MDBT50Q"')
end = pcb.index('\n\t(footprint ', start + 1)
u1 = pcb[start:end]
for pad in sorted(ours):
    port = re.search(rf'\(pad "{pad}" [^\n]*\n(?:(?!\(pad ).)*?\(pinfunction "([^"_]+)_{pad}"', u1, re.S)[1]
    label = PADS.get(pad)
    net = BOARD_NET.get(label, f'/MCU/{label}') if label else f'unconnected-(U1-{port}-Pad{pad})'
    u1, n = re.subn(rf'(\(pad "{pad}" [^\n]*\n(?:(?!\(pad ).)*?\(net ")[^"]*"', lambda m: m[1] + net + '"', u1, count=1, flags=re.S)
    assert n == 1, pad
pcb = pcb[:start] + u1 + pcb[end:]

pcb_path.write_text(pcb)
sch_path.write_text(sch)
for name, refs in moved.items():
    print(f'{name:13}', ' '.join(sorted(refs)))
print(f'removed {removed} prototype tracks, vias and teardrops; moved {len(PADS)} MCU signals, {len(FREE)} pins left free')
