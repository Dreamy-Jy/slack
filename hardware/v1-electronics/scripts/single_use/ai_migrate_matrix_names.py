"""ai_migrate_matrix_names.py  -  run once from scripts/single_use/; edits the files two folders up.

1. switch_matrix.kicad_sch: the latch row moves one column outward ("push this row back 1 column"):
   SW2-SW7 (left) from Column2-7 to Column1-6, SW8-SW13 (right) from Column8-13 to Column9-14.
   Each latch, its diode, and their little wires move one column pitch (27.94 mm) sideways; the column lines and
   the Row1 line stay where they are.
2. New references, H<half>-<kind><n>, numbered in LED strand order (both sheets and the board):
   keys H1-SW1..30, latches H1-L1..6 (left to right on the schematic), encoders H1-RE1..3,
   diodes copy their switch (H1-D5, H1-DL2, H1-DRE1), LEDs H1-LED1..48 in driver order.
3. slack.kicad_pcb: latch LEDs swap places so LED 31..36 sit on latch L1..L6 (LED k on switch k): on half 1 the
   moves are listed in TAKES.  Their vias and short pad tracks stay put and swap nets
   instead (each LED's via pattern is the same around it).  Moving between strands changes the anode too.

Afterwards: open the schematic, then in the board run Tools > Update PCB from Schematic (F8) to bring the latches'
new column nets across.  Tracks on the moved latches' old columns will need re-routing.
"""
import math, pathlib, re

root = pathlib.Path(__file__).resolve().parents[2]
SWM, LEDM, PCB = root / 'switch_matrix.kicad_sch', root / 'led_matrix.kicad_sch', root / 'slack.kicad_pcb'

# ---- the new names (old: new) ------------------------------------------------------------------------------------
KEYS = {1: [15, 16, 17, 18, 19, 20, 29, 30, 31, 32, 33, 34, 43, 44, 45, 46, 47, 48, 55, 56, 57, 58, 59, 60, 67, 68, 69, 70, 71, 72],
        2: [23, 24, 25, 26, 27, 28, 37, 38, 39, 40, 41, 42, 49, 50, 51, 52, 53, 54, 61, 62, 63, 64, 65, 66, 73, 74, 75, 76, 77, 78]}
LATCHES = {1: [2, 3, 4, 5, 6, 7], 2: [8, 9, 10, 11, 12, 13]}          # left to right on the schematic
ENCODERS = {1: ['RE1/SW21', 'RE3/SW35', 'RE5'], 2: ['RE2/SW22', 'RE4/SW36', 'RE6']}
LEDS = {1: '1 2 3 4 5 6 7 15 16 17 18 19 20 21 29 30 31 32 33 34 35 43 44 45 46 47 48 55 56 57 58 59 60 67 68 69 70 71 72 79 80 511 512 513 514 515 517 518',
        2: '8 9 10 11 12 13 14 22 23 24 25 26 27 28 36 37 38 39 40 41 42 49 50 51 52 53 54 61 62 63 64 65 66 73 74 75 76 77 78 81 82 521 522 523 524 525 526 527'}
NEW = {}
for h in (1, 2):
    for k, n in enumerate(KEYS[h], 1): NEW[f'SW{n}'], NEW[f'D{n}'] = f'H{h}-SW{k}', f'H{h}-D{k}'
    for k, n in enumerate(LATCHES[h], 1): NEW[f'SW{n}'], NEW[f'D{n}'] = f'H{h}-L{k}', f'H{h}-DL{k}'
    for k, ref in enumerate(ENCODERS[h], 1):
        NEW[ref] = f'H{h}-RE{k}'
        if '/' in ref: NEW['D' + ref.split('SW')[1]] = f'H{h}-DRE{k}'
    for k, n in enumerate(LEDS[h].split(), 1): NEW[f'LED{n}'] = f'H{h}-LED{k}'
assert len(set(NEW.values())) == len(NEW)


def rename(text):                                   # the Reference field and every instance's reference
    text = re.sub(r'(\(property "Reference" ")([^"]+)(")', lambda m: m[1] + NEW.get(m[2], m[2]) + m[3], text)
    return re.sub(r'(\(reference ")([^"]+)(")', lambda m: m[1] + NEW.get(m[2], m[2]) + m[3], text)


# ---- 1. latch row one column outward (switch_matrix.kicad_sch) -------------------------------------------------
PITCH = 27.94
num = lambda v: f'{v:.4f}'.rstrip('0').rstrip('.')
text = SWM.read_text()
out, moved = [], 0
for item in re.split(r'(?=\n\t\((?:symbol|wire|junction|no_connect|label|text|polyline|rectangle|circle|hierarchical_label|bus|bus_entry)\n)', text):
    kind = (re.match(r'\n\t\((\w+)', item) or [None, ''])[1]
    xy = [tuple(map(float, p)) for p in re.findall(r'\((?:at|xy) (-?[\d.]+) (-?[\d.]+)', item[:300])]
    ref = re.search(r'\(property "Reference" "([^"]+)"', item) if kind == 'symbol' else None
    shift = (kind == 'symbol' and ref and re.fullmatch(r'(SW|D)([2-9]|1[0-3])', ref[1])                # latch, its diode
             or kind == 'wire' and all(36 < y <= 58.42 for _, y in xy)                               # their little wires
             or kind == 'junction' and xy[0][1] in (38.1, 50.8, 66.04)                                # dots on column / Row1
             or kind == 'no_connect' and xy[0][1] < 60)
    if shift:
        d = -PITCH if xy[0][0] < 300 else 25.4 if xy[0][0] < 469.9 else PITCH   # left goes left, right goes right
        #   (Column8 -> Column9 is 25.4 mm on your sheet, every other step 27.94)
        item = re.sub(r'\((at|xy) (-?[\d.]+) (-?[\d.]+)', lambda m: f'({m[1]} {num(float(m[2]) + d)} {m[3]}', item)
        moved += 1
    out.append(item)
SWM.write_text(rename(''.join(out)))
LEDM.write_text(rename(LEDM.read_text()))

# ---- 3. board: swap the latch LEDs into L1..L6 order, then the same new names ----------------------------------
pcb = PCB.read_text()
FP = re.compile(r'\n\t\(footprint "[^"]*"\n(?:(?!\n\t\().)*', re.S)
fps = {re.search(r'\(property "Reference" "([^"]+)"', m[0])[1]: m for m in FP.finditer(pcb)}
AT = re.compile(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)')
info = {}
# latch LEDs: LED number -> the LED number whose spot it takes (LED k ends up on latch L(k-30))
TAKES = {1: {31: 34, 34: 33, 33: 36, 36: 31, 32: 35, 35: 32}, 2: {34: 36, 36: 34}}
led = lambda h, k: f'LED{LEDS[h].split()[k - 1]}'
info = {}
for ref in [led(h, k) for h in (1, 2) for k in TAKES[h]]:
    c = fps[ref][0]; a = AT.search(c)
    nets = dict(re.findall(r'\(pad "(\d)"(?:(?!\n\t\t\(pad).)*?\(net "([^"]*)"\)', c, re.S))
    info[ref] = dict(at=a[0], x=float(a[1]), y=float(a[2]), nets=nets)
swap_net, swap_at = {}, {}
for h in (1, 2):
    for k, spot in TAKES[h].items():
        new, old = led(h, k), led(h, spot)            # LED `new` moves onto `old`'s spot
        swap_at[new] = info[old]['at']
        for p in '12345':                               # the vias/tracks there now carry the newcomer's nets
            swap_net[(old, info[old]['nets'][p])] = info[new]['nets'][p]


def near_led(xs):                                       # which swapped LED a track/via belongs to (within 3 mm)
    for ref, i in info.items():
        if all(math.dist(p, (i['x'], i['y'])) < 3.0 for p in xs): return ref


def renet(m):
    s = m[0]
    pts = [tuple(map(float, p)) for p in re.findall(r'\((?:at|start|end) (-?[\d.]+) (-?[\d.]+)\)', s)]
    ref = near_led(pts)
    net = re.search(r'\(net "([^"]*)"\)', s)
    if ref and net and (ref, net[1]) in swap_net:
        return s.replace(f'(net "{net[1]}")', f'(net "{swap_net[(ref, net[1])]}")')
    return s


pcb = re.sub(r'\n\t\((?:via|segment)\n(?:(?!\n\t\().)*', renet, pcb, flags=re.S)
def move(m):                                            # footprint onto its new spot; KiCad keeps pad/text angles
    c = m[0]; ref = re.search(r'\(property "Reference" "([^"]+)"', c)[1]   # absolute, so turn those by the same amount
    if ref not in swap_at: return c
    turn = float(AT.search(swap_at[ref])[3] or 0) - float(AT.search(c)[3] or 0)
    c = re.sub(r'(\n\t\t\t\(at -?[\d.]+ -?[\d.]+)(?: (-?[\d.]+))?\)', lambda a: f'{a[1]} {num((float(a[2] or 0) + turn) % 360)})', c)
    return AT.sub(swap_at[ref], c, count=1)


pcb = FP.sub(move, pcb)
# nets KiCad named after a part (Net-(D15-A), unconnected-(SW15-H-Pad3)) get the part's new name too, so the board
# already agrees with the schematic and Update PCB has nothing to rename
pcb = re.sub(r'((?:Net|unconnected)-\()([^-()"]+)(-)', lambda m: m[1] + NEW.get(m[2], m[2]) + m[3], pcb)
PCB.write_text(rename(pcb))
print(f'moved {moved} latch-row items one column outward; renamed {len(NEW)} parts; '
      f'swapped {len(swap_at) // 2} pairs of latch LEDs on the board')
