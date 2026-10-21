"""1. Tidy the MCU's support parts around U1.   2. Give every non-Cherry key the Cherry LED+diode pair
(LED, then the diode 2.45 mm along the LED's +x, turned 90 deg), using Jordane's template positions per switch type;
SPEF110100 latches move 2.5 mm "up" in their own frame and get the pair below them (the diode needs 2.8 mm turned the Cherry way).
The scroll wheels (RE9/RE10, SW62/SW63, their caps, LED62/D62, LED63/D63) are placed from FreeCAD and are not touched.
Text edit of slack.kicad_pcb (KiCad 10.0), written back in place - git has the old version.

Run from anywhere:  python3 scripts/single_use/ai_mcu_and_led_patterns.py
"""
import math, pathlib, re

IN  = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
OUT = IN

# ---- 1. MCU area, board coordinates (the module U1 sits at (221, 82.13), 180 deg, on the back; antenna at the top)
MCU_AREA = {
    # the three 10 uF decouplers under the power pins on the module's bottom edge (V_BUS pin 32, +5V pin 30, V_REG0 pin 28)
    'C53': (216.15, 92.3, -90), 'C51': (218.3, 92.3, -90), 'C52': (220.45, 92.3, -90),
    # I2C pull-ups and the INT pull-up next to them, all hanging on V_REG0
    'R59': (222.4, 91.6, 90), 'R58': (223.5, 91.6, 90), 'R65': (225.5, 92.3, 90),
    # the interrupt ladder: resistor + its bypass jumper, one column beside the INT pin (pin 10, right edge)
    'R62': (229.1, 80.4, 0), 'JP2': (229.1, 82.8, 0),
    'R63': (229.1, 85.2, 0), 'JP3': (229.1, 87.6, 0),
    'R64': (229.1, 90.0, 0), 'JP4': (229.1, 92.4, 0),
    # programming connector and reset button on the top side, on the SWD/RESET side of the module (left edge)
    'J3': (202.0, 78.5, 0), 'SW8': (203.0, 85.0, 0),
}

# ---- 2. LED + diode pairs.  Cherry keys have LED at (-0.25, -3.0, 0) and D at (2.2, -3.0, 90) in the switch frame:
# the diode is 2.45 mm along the LED's +x and turned +90.  Pair centre per footprint type, in the switch frame
# (from Jordane's SW73/SW78 templates).  The scroll clicks SW62 (SKQGAKE010) / SW63 (TC-1109) are deliberately absent:
# their LED + diode sit in the cap's pocket where FreeCAD put them (ai_transfer_scrollbars.py), gap 2.7 mm.
PAIR_CENTRE = {
    'SSSS820201': (0.0, 5.9),       # slide latches: below the switch, centred (his SW73 / SW78 templates averaged)
    'SPEF110100': (-5.55, 9.78),    # push latches: in the gap between the latch and its thumb key, once the latch is moved up
    'PEC11S':     None,             # encoders: handled below (Jordane's RE1/RE2 template)
}
SPEF_SHIFT = (0.0, -2.5)            # move each SPEF110100 by this much in its own frame ("up"): 0.35 mm gap + 2.5 = 2.85, the
                                    # diode's footprint needs 2.8 when it is turned the Cherry way; 2.0 would only fit it turned flat
# Encoders (PEC11S), from the RE1/RE2 template: the pair sits just past the switch-pin end (local -y), LED first, diode
# 2.45 mm further out; the LED lies like the Cherry LEDs of its half (board -10 deg on the left, +10 on the right).
ENCODER_LED, ENCODER_D = (0.0, -11.55), (0.0, -14.0)
HALF_GAP = 1.225                    # half of the Cherry LED->diode distance (2.45 mm)


def rot(x, y, deg):
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
        def turn(m):
            parts = m.group(1).split()
            a = float(parts[2]) if len(parts) > 2 else 0.0
            return '(at %s %s %s%s)' % (parts[0], parts[1], fmt(norm(a + d_angle)), ''.join(' ' + r for r in parts[3:]))
        new = body[:old.start()] + '(at %s %s %s)' % (fmt(x), fmt(y), fmt(norm(angle))) + re.sub(r'\(at ([^)]*)\)', turn, body[old.end():])
        self.text = self.text[:s] + new + self.text[e:]
        shift = len(new) - (e - s)
        self.blocks = {r: (a + (shift if a > s else 0), b + (shift if b > s else 0)) for r, (a, b) in self.blocks.items()}


board = Board(IN.read_text())
log = []

for ref, (x, y, a) in MCU_AREA.items():
    board.move(ref, x, y, a); log.append(f'{ref} -> ({x}, {y}, {a})')

for ref in list(board.blocks):
    m = re.fullmatch(r'(?:RE\d+/)?SW(\d+)', ref)
    if not m or ref in ('SW7', 'SW8'): continue              # plain SW7/SW8 are the power slide and reset button, not keys
    n = m.group(1)
    kind = next((k for k in PAIR_CENTRE if k in board.lib(ref)), None)
    if kind is None or f'LED{n}' not in board.blocks or f'D{n}' not in board.blocks: continue
    sx, sy, sa = board.place(ref)
    if kind == 'SPEF110100':                               # the latch itself moves first
        dx, dy = rot(*SPEF_SHIFT, sa)
        sx, sy = sx + dx, sy + dy
        board.move(ref, sx, sy, sa)
    if kind == 'PEC11S':
        led_rel = -90 if sa > 0 else 90                   # left encoders are at +80, right ones at -80
        ox, oy = rot(*ENCODER_LED, sa); board.move(f'LED{n}', sx + ox, sy + oy, norm(sa + led_rel))
        ox, oy = rot(*ENCODER_D, sa);   board.move(f'D{n}', sx + ox, sy + oy, norm(sa + led_rel + 90))
        log.append(f'{ref:9} {kind:10} LED{n} at local {ENCODER_LED} / D{n} at {ENCODER_D}, LED angle {norm(sa + led_rel):g}')
        continue
    else:
        cx, cy = PAIR_CENTRE[kind]
        ox, oy = rot(cx - HALF_GAP, cy, sa)
        lx, ly, la = sx + ox, sy + oy, sa                # LED: pair centre minus half the gap, same angle as the switch
        board.move(f'LED{n}', lx, ly, norm(la))
    ddx, ddy = rot(2 * HALF_GAP, 0, la)                  # diode: 2.45 mm along the LED's +x, turned 90
    board.move(f'D{n}', lx + ddx, ly + ddy, norm(la + 90))
    log.append(f'{ref:9} {kind:10} LED{n} ({lx:.2f}, {ly:.2f}, {norm(la):g})  D{n} ({lx + ddx:.2f}, {ly + ddy:.2f}, {norm(la + 90):g})')

OUT.write_text(board.text)
print('\n'.join(log)); print('wrote', OUT)
