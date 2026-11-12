"""Give the antenna room: widen the notch in the top edge, push the USB-C connector to its left wall, centre the MCU
in what is left.

Before   notch 199.8 .. 243.1 mm.  USB shell 14 mm left of the module, board wall 4.7 mm right of it.
After    notch 192.5 .. 250.4 mm (1.4 mm clear of the inner encoders' mounting pads).  USB shell and right wall
         both 17.8 mm from the module.

Moved    USB group  J1, D0, FL1                                                     9.35 mm left
         MCU group  U1 + its capacitors and pull-ups, J3, reset button, CC parts    5.76 mm left
         D87, D90   the charger's two status LEDs, out from under the USB connector 9.5 mm right
Removed  the prototype tracks, vias and teardrops that touched the two moved areas (they no longer line up).
The charger, boost, battery connector and everything else stay where they are.

Text edit, written back in place: close KiCad and commit first (git is the undo).
Run from anywhere:   python3 scripts/single_use/ai_antenna_clearance_rev.py
"""
import pathlib, re

pcb_path = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
pcb = pcb_path.read_text()

USB, MCU, LED = -9.35, -5.76, 9.5
GROUP = dict.fromkeys(['J1', 'D0', 'FL1'], USB)
GROUP.update(dict.fromkeys(['U1', 'J3', 'C51', 'C52', 'C53', 'R58', 'R59', 'SW84',
                            'D88', 'D89', 'JP5', 'JP6', 'R60', 'R61', 'R49', 'R51'], MCU))
GROUP.update(D87=LED, D90=LED)
LED_NETS = ('Net-(D87-A)', 'Net-(D90-A)', 'PG{slash}NTC2', 'STAT{slash}IB')


def moved_area(x, y, led_net):                                  # is this track end where a moved part was?
    usb = 203 <= x < 221.9 and 74 <= y < 88.6
    mcu = 221.9 <= x <= 256 and 74 <= y <= 104.5
    leds = led_net and x < 204 and y < 88
    return usb or mcu or leds


def num(v):
    return f'{v:.6f}'.rstrip('0').rstrip('.')


POINT = re.compile(r'\((start|mid|end|at|xy) (-?[\d.]+) (-?[\d.]+)')
starts = [m.start() for m in re.finditer(r'\n\t\(', pcb)] + [len(pcb)]
out = [pcb[:starts[0]]]
seen, removed = set(), 0
for a, b in zip(starts, starts[1:]):
    chunk = pcb[a:b]
    kind = re.match(r'\n\t\((\w+)', chunk)[1]
    if kind == 'footprint':
        ref = re.search(r'\(property "Reference" "([^"]*)"', chunk)[1]
        if ref in GROUP:
            seen.add(ref)
            dx = GROUP[ref]
            chunk = re.sub(r'(\n\t\t\(at )(-?[\d.]+)', lambda m: m[1] + num(float(m[2]) + dx), chunk, count=1)
            if ref == 'U1':                                     # its antenna keep-out is stored in board coordinates
                zone = chunk.index('\n\t\t(zone\n')
                chunk = chunk[:zone] + re.sub(r'\(xy (-?[\d.]+)', lambda m: '(xy ' + num(float(m[1]) + dx), chunk[zone:])
    elif kind in ('segment', 'arc', 'via', 'zone') and 'Edge.Cuts' not in chunk:
        led_net = any(n in chunk for n in LED_NETS)
        if any(moved_area(float(m[2]), float(m[3]), led_net) for m in POINT.finditer(chunk)):
            removed += 1
            continue
    elif kind == 'gr_rect' and '"B.Cu"' in chunk and '(start 206.15 76.5)' in chunk:      # copper patch on J1's pads
        chunk = POINT.sub(lambda m: f'({m[1]} {num(float(m[2]) + USB)} {m[3]}', chunk)
    elif kind == 'gr_poly' and 'Edge.Cuts' in chunk:            # the outline: slide the notch's four corner arcs
        left, right, slope = 192.5 - 199.826827, 250.4 - 243.055435, 0.17596     # the raised edge falls 10 degrees
        corners = {'(start 199.826827 70.2937)': (left, 0), '(start 196.520012 58.202939)': (left, left * slope),
                   '(start 239.055435 74.2937)': (right, 0), '(start 243.055435 62.144976)': (right, -right * slope)}
        for first, (dx, dy) in corners.items():
            arc = re.search(re.escape(first) + r'\s*\(mid [^)]*\)\s*\(end [^)]*\)', chunk)
            chunk = chunk.replace(arc[0], POINT.sub(lambda p: f'({p[1]} {num(float(p[2]) + dx)} {num(float(p[3]) + dy)}', arc[0]))
    out.append(chunk)
assert seen == set(GROUP), set(GROUP) - seen
pcb_path.write_text(''.join(out))
print(f'moved {len(GROUP)} footprints, removed {removed} prototype tracks/vias/teardrops; notch is now 192.5 .. 250.4')
