"""Mirror the left-hand slide-latch changes (made to fit the on/off switch SW7) onto the right hand.

SW81/LED81/D81 take the mirror image of SW70/LED70/D70, SW82/LED82/D82 of SW69/LED69/D69.
Only the footprint positions change; rotations stay as they are (the right hand is already +10 deg).
Run from anywhere: it edits hardware/v1-electronics/slack.kicad_pcb in place (commit first).
"""
import re, pathlib

BOARD = pathlib.Path(__file__).resolve().parents[2] / 'slack.kicad_pcb'
MIRROR_X = 221.4484
PAIRS = {'SW81': 'SW70', 'LED81': 'LED70', 'D81': 'D70', 'SW82': 'SW69', 'LED82': 'LED69', 'D82': 'D69'}

text = BOARD.read_text()


def position(ref):
    """(x, y, angle, start, end) of the footprint's own (at ...) for this reference."""
    m = re.search(r'\n\t\(footprint "[^"]+"(?:(?!\n\t\)).)*?\(property "Reference" "%s"' % re.escape(ref), text, re.S)
    at = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', text[m.start():m.end()])
    return float(at.group(1)), float(at.group(2)), float(at.group(3) or 0), m.start() + at.start(), m.start() + at.end()


def num(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


for right, left in PAIRS.items():
    lx, ly, _, _, _ = position(left)
    rx, ry, ra, i, j = position(right)
    nx, ny = 2 * MIRROR_X - lx, ly
    text = text[:i] + f'(at {num(nx)} {num(ny)} {num(ra)})' + text[j:]
    print(f'{right:6} ({rx:7.2f}, {ry:6.2f}) -> ({nx:8.4f}, {ny:6.2f})  = mirror of {left}')

BOARD.write_text(text)
print('written', BOARD)
