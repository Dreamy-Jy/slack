"""LED matrix refactor for slack.kicad_pcb (board as uploaded 15 Nov).  Board only; the schematic is not touched.
Close KiCad and commit first (git is the undo).      python3 scripts/single_use/ai_led_matrix_refactor.py

PART 1  LED fan-out vias
  1. every LED that belongs to an input (key, encoder, button, switch) gets vias; the 18 loose centre-line LEDs don't
  2. each of those LEDs is turned (180 degrees where needed) so its red, green and blue pads face the board's
     centre line; the anode via then points up and the white via down
  3. the old LED vias and their short pad-to-via tracks are removed and replaced by the pattern below

  4. the left half's LEDs are moved onto the exact mirror image of their right-half twins (see TWIN, MASTER)

  3b. first the master (right) half is cleaned up: every latch is centred on its nearest key switch, turned 90
      degrees to it, and its LED and diode put at the same spot on every latch of its kind (LATCH_SPOT, SUPPORT)

PART 2  mirror the halves
  every left-half key switch, encoder, latch and diode is put on the mirror image of its right-half twin (TWIN).
  The left half's latches change places to match the right: SW2/SW3 (slide) go beside the inner column with SW4,
  SW5 (button) goes down to the thumb row.  Tracks and vias already on moved parts are not moved: re-route them.

PART 3  LED order along the current-source strands
  the LED footprints are moved so schematic LED number k on a half sits on the k-th part in ORDER (rows run left to
  right on the board, then thumb row, latch buttons, slide latches, encoders).  Each 3 LEDs in a row share one
  current source.  Wiring is unchanged: only which LED sits where (the firmware's key-to-LED map) changes.

  Pattern, in the LED's own frame: u points towards the centre line, v points up.  Pads: R/G/B at u = +0.38,
  anode at u = 0, white at u = -0.38.  The three colour vias are staggered (short, medium, long) like the sketch.
"""
import math, pathlib, re, uuid

PARTS = {1, 2, 3}
path = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
pcb = path.read_text()

CENTRE = 192.3245                              # x of the board's centre line (middle of the outline)
LOOSE = set('LED511 LED512 LED513 LED514 LED515 LED517 LED518 LED521 LED522 LED523 LED524 LED525 LED526 LED527 '
            'LED79 LED80 LED81 LED82'.split())
VIA, DRILL, THIN, WIDE = 0.5, 0.2, 0.127, 0.2  # via size, drill; colour-track and anode/white-track widths
PATTERN = {    # pad: (via u, v), [track bends u, v], track width.  u = toward the centre line, v = up, mm from the LED centre.
    # Spread out so a 0.127 mm track (0.152 clearance) fits between any two vias, for routing through later.
    'top':    ((1.10, 0.80), [(0.60, 0.30)], THIN),
    'middle': ((1.80, 0.00), [], THIN),
    'bottom': ((2.40, -1.30), [(0.60, -0.30), (1.60, -1.30)], THIN),
    '5':      ((0.00, 1.00), [], WIDE),       # anode, straight up from its pad
    '4':      ((-0.38, -1.00), [], WIDE),     # white, straight down, centred on the white cathode
}

# Mirror: the RIGHT half is the master; the left half is moved onto its mirror image.  Your numbering already runs in
# mirror order, so every switch, encoder and latch has a twin on the other half (table: right: left).  Each right-half LED n and diode Dn follows its switch's twin.
TWIN = {
    'SW8': 'SW7', 'SW9': 'SW6', 'SW10': 'SW5', 'SW11': 'SW4', 'SW12': 'SW3', 'SW13': 'SW2', 'RE2/SW22': 'RE1/SW21',
    'SW23': 'SW20', 'SW24': 'SW19', 'SW25': 'SW18', 'SW26': 'SW17', 'SW27': 'SW16', 'SW28': 'SW15',
    'RE4/SW36': 'RE3/SW35', 'SW37': 'SW34', 'SW38': 'SW33', 'SW39': 'SW32', 'SW40': 'SW31', 'SW41': 'SW30',
    'SW42': 'SW29', 'SW49': 'SW48', 'SW50': 'SW47', 'SW51': 'SW46', 'SW52': 'SW45', 'SW53': 'SW44', 'SW54': 'SW43',
    'SW61': 'SW60', 'SW62': 'SW59', 'SW63': 'SW58', 'SW64': 'SW57', 'SW65': 'SW56', 'SW66': 'SW55', 'SW73': 'SW72',
    'SW74': 'SW71', 'SW75': 'SW70', 'SW77': 'SW68', 'SW78': 'SW67'
}
TWIN_EXTRA = {'LED14': 'LED1', 'H8': 'H7'}       # LED14 has no switch; H7 is in the way of SW5 unless it mirrors H8
MASTER = 'right'                               # which half stays put                 # LEDs with no switch of their own
# Clean-up of the master half before the mirror: each latch is centred on its nearest key switch and turned 90 degrees
# to it; its LED and diode sit at the same spot on every latch of that kind.  (part's position in the key's own frame)
LATCH_SPOT = {'SW8': ('SW73', (0, -12.95)), 'SW9': ('SW74', (0, -12.95)), 'SW10': ('SW75', (0, -12.95)),    # buttons above the thumb keys
              'SW11': ('SW61', (-13.25, 0)), 'SW12': ('SW49', (-13.25, 0)), 'SW13': ('SW37', (-13.25, 0))}  # slides beside the inner column
SUPPORT = {'BTSA-L-S-8': {'LED': ((4.75, -1.225), -90), 'D': ((4.75, 1.225), 0)},     # (spot in the latch's frame), angle to the latch
           'SS3235SL3':  {'LED': ((-1.225, -6.4), -90), 'D': ((1.225, -6.4), 90)}}
# Part 3: the order of the LEDs along the current-source strands (your sketch, 15 Nov).  Schematic LED number k on a
# half (strand CS = ceil(k / 3); 1st/2nd/3rd LED of a strand on sink set SW1-4 / SW5-8 / SW9-12) goes on the k-th part
# below.  A part's LED spot is the one its own LED had (LED<n> for SW<n>, RE../SW<n>); LED1/LED14 name the LED itself.
ORDER = {1: ['SW15', 'SW16', 'SW17', 'SW18', 'SW19', 'SW20',      # top row, outer -> inner  (Half 1 LED 1 = SW15)
             'SW29', 'SW30', 'SW31', 'SW32', 'SW33', 'SW34',      # row 2
             'SW43', 'SW44', 'SW45', 'SW46', 'SW47', 'SW48',      # row 3
             'SW55', 'SW56', 'SW57', 'SW58', 'SW59', 'SW60',      # row 4
             'SW67', 'SW68', 'SW69', 'SW70', 'SW71', 'SW72',      # thumb row (SW69 = scroll click)
             'SW7', 'SW6', 'SW5',                                 # latch buttons, inner -> outer  (LED 31 = SW7)
             'SW2', 'SW3', 'SW4',                                 # slide latches, top -> bottom
             'RE1/SW21', 'RE3/SW35', 'LED1'],                     # encoders, then the LED by the centre line
         2: ['SW23', 'SW24', 'SW25', 'SW26', 'SW27', 'SW28',      # top row, inner -> outer  (Half 2 LED 1 = SW23)
             'SW37', 'SW38', 'SW39', 'SW40', 'SW41', 'SW42',
             'SW49', 'SW50', 'SW51', 'SW52', 'SW53', 'SW54',
             'SW61', 'SW62', 'SW63', 'SW64', 'SW65', 'SW66',
             'SW73', 'SW74', 'SW75', 'SW76', 'SW77', 'SW78',      # thumb row (SW76 = scroll click)
             'SW8', 'SW9', 'SW10',                                # latch buttons, inner -> outer  (LED 31 = SW8)
             'SW13', 'SW12', 'SW11',                              # slide latches, top -> bottom
             'RE2/SW22', 'RE4/SW36', 'LED14']}

# How the rotation mirrors (KiCad can't flip a part, so a mirrored part is turned instead): new angle = C - twin angle.
# 180 for parts whose pads face across the board (buttons, LEDs, diodes), 0 for the rest (keys, slide latches, encoders).
FLIP_C = {'BTSA-L-S-8': 180, 'LTSTFC12WEGBD5A': 180, 'D_SOD-523': 180}

AT = re.compile(r'\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)')
num = lambda v: f'{v:.4f}'.rstrip('0').rstrip('.') or '0'


def board_xy(x, y, rot, lx, ly):               # a footprint's own coordinates -> board coordinates (KiCad's sense)
    a = math.radians(rot)
    return x + lx * math.cos(a) + ly * math.sin(a), y - lx * math.sin(a) + ly * math.cos(a)


def number(ref): return re.search(r'(\d+)$', ref)[1]
TWINS = dict(TWIN_EXTRA)
for r, l in TWIN.items():
    TWINS[r] = l
    for p in ('LED', 'D'): TWINS[p + number(r)] = p + number(l)
if MASTER == 'right': TWINS = {l: r for r, l in TWINS.items()}      # key = the part that moves, value = its twin


def turn_to(c, x, y, rot):                     # put a footprint at x, y, rot (pad and text angles inside are absolute)
    a = AT.search(c); old = float(a[3] or 0); d = rot - old
    c = re.sub(r'(\n\t\t\t\(at -?[\d.]+ -?[\d.]+)(?: (-?[\d.]+))?\)', lambda m: f'{m[1]} {num((float(m[2] or 0) + d) % 360)})', c)
    rot = (rot + 180) % 360 - 180
    return AT.sub(f'\n\t\t(at {num(x)} {num(y)}' + (f' {num(rot)})' if rot else ')'), c, count=1)


def chunks(text):
    s = [m.start() for m in re.finditer(r'\n\t\(', text)] + [len(text)]
    return [text[a:b] for a, b in zip(s, s[1:])]


def part1(text):
    items, leds = chunks(text), {}
    head = text[:text.index(items[0])]
    for i, c in enumerate(items):
        if c.startswith('\n\t(footprint "Liteon:'):
            ref = re.search(r'\(property "Reference" "([^"]*)"', c)[1]
            if ref in LOOSE: continue
            a = AT.search(c); x, y, rot = float(a[1]), float(a[2]), float(a[3] or 0)
            pads = {p[1]: ((float(p[2]), float(p[3])), p[4]) for p in
                    re.finditer(r'\(pad "(\d)" smd rect\s*\(at (-?[\d.]+) (-?[\d.]+)[^)]*\).*?\(net "([^"]*)"\)', c, re.S)}
            want = 1 if x < CENTRE else -1      # the LED's own +x (its colour pads) must point at the centre line
            rot0 = rot
            turn = 180 if math.copysign(1, math.cos(math.radians(rot))) != want else 0
            if turn:                             # every angle inside a footprint is stored absolute
                c = re.sub(r'(\n\t\t\t\(at -?[\d.]+ -?[\d.]+)(?: (-?[\d.]+))?\)',
                           lambda m: f'{m[1]} {num((float(m[2] or 0) + 180) % 360)})', c)
                rot = (rot + 180) % 360
                c = AT.sub(f'\n\t\t(at {num(x)} {num(y)}' + (f' {num(rot)})' if rot else ')'), c, count=1)
                items[i] = c
            leds[ref] = dict(x=x, y=y, rot=rot, rot0=rot0, pads=pads, turned=bool(turn))

    # 3. remove the old LED vias and the short tracks from LED pads to them
    nets_near = [(L['x'], L['y'], {n for _, n in L['pads'].values()}) for L in leds.values()]
    old_vias, keep = set(), []
    for c in items:
        if c.startswith('\n\t(via'):
            a = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)\)', c); vx, vy = float(a[1]), float(a[2])
            net = re.search(r'\(net "([^"]*)"\)', c)[1]
            if any(math.dist((vx, vy), (x, y)) < 2.5 and net in ns for x, y, ns in nets_near):
                old_vias.add((round(vx, 4), round(vy, 4))); continue
        keep.append(c)
    items, removed = [], 0                    # tracks: ends on an old LED via, or short ones starting on one of these LEDs' pads
    old_pads = [(board_xy(*o, *xy), net) for o, L in ((( L['x'], L['y'], L['rot0']), L) for L in leds.values())
                for xy, net in L['pads'].values()]
    for c in keep:
        if c.startswith('\n\t(segment'):
            ends = [(round(float(a), 4), round(float(b), 4)) for a, b in re.findall(r'\((?:start|end) (-?[\d.]+) (-?[\d.]+)\)', c)]
            net = re.search(r'\(net "([^"]*)"\)', c)[1]
            on_pad = any(math.dist(e, p) < 0.45 and net == n for e in ends for p, n in old_pads)
            if (any(e in old_vias for e in ends) or (on_pad and '"F.Cu"' in c)) and math.dist(*ends) < 3:
                removed += 1; continue
        items.append(c)

    # 3b. clean up the master half's latches, their LEDs and diodes (before anything is mirrored from them)
    idx = {re.search(r'\(property "Reference" "([^"]*)"', c)[1]: i for i, c in enumerate(items) if c.startswith('\n\t(footprint')}
    pos = lambda r: (lambda a: (float(a[1]), float(a[2]), float(a[3] or 0)))(AT.search(items[idx[r]]))
    tidy = []
    for sw, (key, spot) in LATCH_SPOT.items():
        kx, ky, krot = pos(key); x, y, rot = pos(sw)
        lx, ly = board_xy(kx, ky, krot, *spot); lrot = (krot + 90) % 360
        items[idx[sw]] = turn_to(items[idx[sw]], lx, ly, lrot); tidy.append((sw, math.dist((x, y), (lx, ly))))
        kind = re.search(r'footprint "[^:"]*:([^"]*)"', items[idx[sw]])[1]
        for p, (spot2, rel) in SUPPORT[kind].items():
            ref = p + number(sw); x, y, _ = pos(ref)
            nx, ny = board_xy(lx, ly, lrot, *spot2); nrot = (lrot + rel) % 360
            if ref in leds:                       # keep the LED's colour pads facing the centre line
                if (math.cos(math.radians(nrot)) > 0) != (nx < CENTRE): nrot = (nrot + 180) % 360
                leds[ref].update(x=nx, y=ny, rot=nrot)
            items[idx[ref]] = turn_to(items[idx[ref]], nx, ny, nrot); tidy.append((ref, math.dist((x, y), (nx, ny))))
    print('clean-up:', ', '.join(f'{r} {d:.2f} mm' for r, d in tidy if d > 0.005))

    # 4. mirror the LEDs onto their master-half twins (after the old vias are gone, before the new ones go in)
    for ref, L in leds.items():
        if ref not in TWINS or TWINS[ref] not in leds: continue
        T = leds[TWINS[ref]]; nx, ny, nrot = 2 * CENTRE - T['x'], T['y'], (180 - T['rot']) % 360
        i = next(i for i, c in enumerate(items) if f'(property "Reference" "{ref}"' in c)
        items[i] = turn_to(items[i], nx, ny, nrot)
        L['moved'] = math.dist((nx, ny), (L['x'], L['y'])); L['x'], L['y'], L['rot'] = nx, ny, nrot

    # 5. (part 3) put each LED on its spot along the strands: LED number k of a half goes on ORDER[half][k-1]
    if 3 in PARTS:
        spots = {r: (L['x'], L['y'], L['rot']) for r, L in leds.items()}           # every spot, before anything moves
        owner = lambda part: part if part.startswith('LED') else 'LED' + number(part)
        for ref, L in leds.items():
            cs = re.search(r'Chip(\d)CurrentSource(\d+)', L['pads']['5'][1])
            sink = int(re.search(r'SinkSwitch(\d+)', L['pads']['1'][1])[1])
            k = 3 * (int(cs[2]) - 1) + (sink - 1) // 4                              # 0-based slot on its half
            if k >= len(ORDER[int(cs[1])]): continue                                  # indicators (CS14-16)
            nx, ny, nrot = spots[owner(ORDER[int(cs[1])][k])]
            i = next(i for i, c in enumerate(items) if f'(property "Reference" "{ref}"' in c)
            items[i] = turn_to(items[i], nx, ny, nrot)
            L['strand_moved'] = math.dist((nx, ny), (L['x'], L['y'])); L['x'], L['y'], L['rot'] = nx, ny, nrot
        print(f'part 3: {sum(L.get("strand_moved", 0) > 0.01 for L in leds.values())} LEDs put on their strand spot')

    # 1 + 2. new vias and pad-to-via tracks
    new = []
    for ref, L in leds.items():
        s = 1 if math.cos(math.radians(L['rot'])) > 0 else -1           # local -y is "up" when s = +1
        to_local = lambda u, v: (u, -s * v)
        colour = sorted((p for p in ('1', '2', '3')), key=lambda p: s * L['pads'][p][0][1])    # top (largest v) first
        for name, pad in [('top', colour[0]), ('middle', colour[1]), ('bottom', colour[2]), ('5', '5'), ('4', '4')]:
            (lx, ly), net = L['pads'][pad]
            via, bends, width = PATTERN[name]
            pts = [(lx, ly)] + [to_local(*b) for b in bends] + [to_local(*via)]
            if name in ('5', '4'): pts[0] = (lx, ly + (0.3 if pts[-1][1] > ly else -0.3))
            xy = [board_xy(L['x'], L['y'], L['rot'], *p) for p in pts]
            for a, b in zip(xy, xy[1:]):
                new.append(f'\n\t(segment\n\t\t(start {num(a[0])} {num(a[1])})\n\t\t(end {num(b[0])} {num(b[1])})\n\t\t(width {width})'
                           f'\n\t\t(layer "F.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
            new.append(f'\n\t(via\n\t\t(at {num(xy[-1][0])} {num(xy[-1][1])})\n\t\t(size {VIA})\n\t\t(drill {DRILL})\n\t\t(layers "F.Cu" "B.Cu")'
                       f'\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
    last = max(i for i, c in enumerate(items) if c.startswith(('\n\t(segment', '\n\t(via')))
    if not NO_NEW: items[last + 1:last + 1] = new
    print(f'part 1: {len(leds)} LEDs ({sum(L["turned"] for L in leds.values())} turned 180), '
          f'removed {len(old_vias)} old vias and {removed} tracks, added {len(leds) * 5} vias, '
          f'moved {sum("moved" in L for L in leds.values())} LEDs (max {max(L.get("moved", 0) for L in leds.values()):.2f} mm)')
    return head + ''.join(items)


def part2(text):
    """PART 2  the other half's switches, encoders, latches and diodes go to the mirror image of their master-half twins."""
    items = chunks(text); head = text[:text.index(items[0])]
    at = {}
    for c in items:
        if c.startswith('\n\t(footprint'):
            a = AT.search(c); at[re.search(r'\(property "Reference" "([^"]*)"', c)[1]] = (float(a[1]), float(a[2]), float(a[3] or 0), c)
    moved = []
    for i, c in enumerate(items):
        if not c.startswith('\n\t(footprint') or c.startswith('\n\t(footprint "Liteon:'): continue
        ref = re.search(r'\(property "Reference" "([^"]*)"', c)[1]
        if ref not in TWINS or TWINS[ref] not in at: continue
        lx, ly, lrot, _ = at[TWINS[ref]]; x, y, rot, _ = at[ref]
        flip = FLIP_C.get(re.search(r'footprint "[^:"]*:?([^"]*)"', c)[1], 0)
        nx, ny, nrot = 2 * CENTRE - lx, ly, (flip - lrot) % 360
        items[i] = turn_to(c, nx, ny, nrot)
        moved.append((ref, math.dist((x, y), (nx, ny)), ((nrot - rot + 180) % 360) - 180))
    big = sorted((m for m in moved if m[1] > 0.05 or abs(m[2]) > 0.05), key=lambda m: -m[1])
    print(f'part 2: {len(moved)} parts placed on their twin\'s mirror image; moved more than 0.05 mm or turned:',
          ', '.join(f'{r} {d:.2f} mm{f" {a:+.0f} deg" if abs(a) > 0.05 else ""}' for r, d, a in big))
    return head + ''.join(items)


NO_NEW = False                                   # (testing) remove and turn only
if 1 in PARTS: pcb = part1(pcb)
if 2 in PARTS: pcb = part2(pcb)
path.write_text(pcb)
