"""AI generated throw away
Fix the references issues with the switch and LED matrices
"""

import re

SWITCH_SCH = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/switch_matrix.kicad_sch"
LED_SCH = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/led_matrix.kicad_sch"

# old ref -> new ref
RENAME = {f"SW{n}": f"SW{n-2}" for n in range(65, 85)}
RENAME |= {f"D{n}": f"D{n-2}" for n in range(65, 85)}
RENAME |= {
    "LED63": "LED69", "LED73": "LED70", "LED74": "LED71", "LED75": "LED72",
    "LED76": "LED73", "LED77": "LED74", "LED78": "LED75",
    "LED66": "LED63", "LED67": "LED64", "LED68": "LED65", "LED69": "LED66",
    "LED70": "LED67", "LED71": "LED68", "LED72": "LED76", "LED80": "LED77",
    "LED81": "LED78", "LED82": "LED79", "LED83": "LED80", "LED84": "LED81",
    "LED85": "LED82",
}
RENAME |= {f"LED{n}": "LED??" for n in (79, 86, *range(501, 513))}


def rename(path: str):
    text = open(path).read()
    # one symbol instance per chunk; the first chunk is the header/lib_symbols
    chunks = text.split("\n\t(symbol\n")
    for i, chunk in enumerate(chunks[1:], 1):
        m = re.search(r'\(property "Reference" "([^"]*)"', chunk)
        old = m.group(1)
        if old in RENAME:
            new = RENAME[old]
            chunk = chunk.replace(f'(property "Reference" "{old}"', f'(property "Reference" "{new}"', 1)
            chunk = chunk.replace(f'(reference "{old}")', f'(reference "{new}")')
            chunks[i] = chunk
    open(path, "w").write("\n\t(symbol\n".join(chunks))


rename(SWITCH_SCH)
rename(LED_SCH)