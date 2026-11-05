"""Close the gaps the four bottom encoders left in the numbering.  Run ai_remove_bottom_encoders.py first.

Switches and diodes   SW/D 37-48 become 35-46 and SW/D 51-82 become 47-78.
Scroll encoders       RE9 and RE10 become RE5 and RE6, on encoder channels 5 and 6 (same MCU pins as before).
LEDs                  The LED under key n is called LEDn again.  The four LEDs that lost their encoder
                      (LED35, LED49 on the left chip, LED36, LED50 on the right) become LED79-LED82.
LED driver order      Each driver chip lights its half's keys in key order, three to a current-source line.  The
                      order is re-packed: the 39 key LEDs of each half come first with no gaps, then the two
                      leftover LEDs, then the seven spares that were already last.

On the schematic an LED symbol stands for a driver slot, on the board an LED footprint stands for a place.  So the
symbols are only renamed, and each footprint keeps its place but takes over the link and the five nets of the symbol
that now carries its name.  Nothing on the board moves; no resistor or capacitor is renamed.

Text edit, written back in place: close KiCad and commit first (git is the undo).  Nothing is written unless every
check passes.
Run from anywhere:   python3 scripts/single_use/ai_shift_references.py
"""
import pathlib, re

HERE = pathlib.Path(__file__).resolve().parents[2]              # hardware/v1-electronics
GONE = [35, 36, 49, 50]                                         # the numbers the four encoders leave free


def shift(n):
    return n - sum(g < n for g in GONE)                         # 37 -> 35 ... 48 -> 46, 51 -> 47 ... 82 -> 78


NAMES = {f'{kind}{n}': f'{kind}{shift(n)}' for kind in ('SW', 'D') for n in range(37, 83) if n not in GONE}
NAMES.update({'RE9': 'RE5', 'RE10': 'RE6'})
CHANNELS = {'9': '5', '10': '6'}                                # RotaryEncoder_AChannel9 -> RotaryEncoder_AChannel5 ...

# LEDs by their old numbers, in the order each driver chip lights them: its half's keys, row by row
LEFT  = [*range(1, 8), *range(15, 22), *range(29, 36), *range(43, 50), *range(57, 63), *range(69, 76)]     # chip 1
RIGHT = [*range(8, 15), *range(22, 29), *range(36, 43), *range(50, 57), *range(63, 69), *range(76, 83)]    # chip 2
LEFTOVER = {35: 79, 49: 80, 36: 81, 50: 82}

PLACE = {f'LED{n}': f'LED{LEFTOVER.get(n) or shift(n)}' for n in LEFT + RIGHT}   # a footprint's old name -> new name
SLOT = {}                                                                         # a symbol's old name -> new name
for half in (LEFT, RIGHT):
    keys_then_leftovers = [n for n in half if n not in GONE] + [n for n in half if n in GONE]
    for slot_owner, newcomer in zip(half, keys_then_leftovers):                   # the slot's old LED, the LED moving in
        SLOT[f'LED{slot_owner}'] = PLACE[f'LED{newcomer}']
WIRING_OF = {new: old for old, new in SLOT.items()}             # a new name -> the old LED whose slot goes with it


def rename(text, names):
    """New references for the parts in `names` (a schematic keeps each reference in two places, a board in one)."""
    return re.sub(r'(\(property "Reference" |\(reference )"([^"]+)"',
                  lambda m: f'{m.group(1)}"{names.get(m.group(2), m.group(2))}"', text)


def renumber_channels(text):
    text = re.sub(r'(RotaryEncoder_[AB]Channel)(9|10)"', lambda m: f'{m.group(1)}{CHANNELS[m.group(2)]}"', text)
    return text.replace('Channel[1..10]"', 'Channel[1..6]"')    # the bus that carries the channels between sheets


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


files = {}                                                      # file -> its new text, written at the very end

# ------------------------------------------------------------------ 1. the schematic sheets
matrix = (HERE / 'switch_matrix.kicad_sch').read_text()
leds   = (HERE / 'led_matrix.kicad_sch').read_text()
board  = (HERE / 'slack.kicad_pcb').read_text()
for text in (matrix, board):
    assert '"SW82"' in text, 'the references are already shifted'
    assert '"RE5/SW35"' not in text, 'run ai_remove_bottom_encoders.py first'
assert all(f'(reference "{led}")' in leds for led in SLOT), 'some key LEDs are not on the LED sheet'

files[HERE / 'switch_matrix.kicad_sch'] = renumber_channels(rename(matrix, NAMES))
files[HERE / 'led_matrix.kicad_sch'] = rename(leds, SLOT)
for name in ('controller.kicad_sch', 'slack.kicad_sch'):        # the MCU's pin labels, and the bus pins on the top sheet
    files[HERE / name] = renumber_channels((HERE / name).read_text())

# ------------------------------------------------------------------ 2. the board

# 2a. LEDs: every footprint stays where it is and takes over the name, link and nets that belong to its place now
wiring = {}                                                     # old name -> (link to its symbol, its five pad nets)
for start, end in spans(board, 'footprint'):
    led = board[start:end]
    if reference(led) in PLACE:
        assert re.findall(r'\(pad "(\d)"', led) == list('12345'), 'unexpected LED pads'
        wiring[reference(led)] = (re.search(r'\(path "([^"]+)"\)', led).group(1), re.findall(r'\(net "([^"]*)"\)', led))
assert len(wiring) == len(PLACE), 'some key LEDs are not on the board'

for start, end in reversed(spans(board, 'footprint')):          # last one first, so earlier positions stay valid
    led = board[start:end]
    if reference(led) in PLACE:
        name = PLACE[reference(led)]
        path, nets = wiring[WIRING_OF[name]]
        nets = iter(nets)
        led = led.replace(f'(property "Reference" "{reference(led)}"', f'(property "Reference" "{name}"')
        led = re.sub(r'\(path "[^"]+"\)', f'(path "{path}")', led)
        led = re.sub(r'\(net "[^"]*"\)', lambda m: f'(net "{next(nets)}")', led)
        board = board[:start] + led + board[end:]

# 2b. switches, diodes and scroll encoders: their new names, and the net names KiCad builds from them
board = rename(board, NAMES)
board = re.sub(r'\(net "((?:Net|unconnected)-\()((?:SW|D|RE)\d+)(-[^"]*)"\)',
               lambda m: f'(net "{m.group(1)}{NAMES.get(m.group(2), m.group(2))}{m.group(3)}")', board)
files[HERE / 'slack.kicad_pcb'] = renumber_channels(board)

# ------------------------------------------------------------------ 3. the scroll-bar transfer script's table
porter = HERE / 'scripts' / 'layout_support' / 'layout_porter' / 'ai_transfer_scrollbars.py'
script = porter.read_text()
for old, new in [('"RE9": (', '"RE5": ('), ('"RE10": (', '"RE6": ('), ('(RE9)', '(RE5)'), ('(RE10)', '(RE6)'),
                 ('("SW62"', '("SW58"'), ('("LED62"', '("LED58"'), ('("D62"', '("D58"'),
                 ('("SW63"', '("SW59"'), ('("LED63"', '("LED59"'), ('("D63"', '("D59"')]:
    assert script.count(old) == 1, f'{old} is not in {porter.name} exactly once'
    script = script.replace(old, new)
files[porter] = script

# ------------------------------------------------------------------ 4. every check has passed: write the files
for path, text in files.items():
    path.write_text(text)
print(f'schematic: {len(NAMES)} switch, diode and encoder references and {len(SLOT)} LED references shifted')
print(f'board: {len(PLACE)} LED footprints re-wired in place, {len(NAMES)} other references shifted')
print(f'{porter.name}: its ten references updated')
