# Move 1
# Moves mounting holes H3–H6 and H9–H12 (snapped to exact mirror images).
# Run with stable KiCad's Python, with the board closed in KiCad. Commit first.

from pathlib import Path
import pcbnew

# The script lives in v1-electronics/scripts/single_use/, so the board is two folders up.
BOARD = str("/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/slack.kicad_pcb")

# All pairs mirror about x = 221.4484 (the board's centre line).
# Every hole except H11/H12 sits exactly 6.201 mm from the nearest part (the distance H5/H6 already had).
NEW = {
    # H1/H2: slid toward the top switch's LED (LED71/LED80), the nearest part there.
    "H1": (147.238, 52.780), "H2": (295.659, 52.780),
    # H9/H10: tucked into the corner between the switch above (SW44/SW55) and the one beside it
    # (SW57/SW68), 6.201 mm from both.
    "H9": (95.806, 162.580), "H10": (347.090, 162.580),
    # H11/H12: in line with each scroll-bar assembly (on the cap's centre line, the roller's axis),
    # just past the cap's far end: 3.0 mm beyond the cap courtyard, leaving 0.55 mm between courtyards.
    "H11": (140.308, 201.210), "H12": (302.588, 201.210),
    # H3/H5 and H4/H6: on a line parallel to the outer key column (10 degrees from vertical),
    # 14.24 mm out from the column's centre line; H3/H4 slid along that line to be 6.201 mm from SW1/SW14.
    "H3": (71.759, 70.664), "H5": (57.149, 153.521),
    "H4": (371.138, 70.664), "H6": (385.748, 153.521),
}
 
board = pcbnew.LoadBoard(BOARD)
if board is None:
    raise SystemExit(f"Could not open {BOARD}")
 
for ref, (x, y) in NEW.items():
    hole = board.FindFootprintByReference(ref)
    if hole is None:
        raise SystemExit(f"No footprint {ref} on the board")
    hole.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    print(f"{ref} moved to ({x}, {y})")
 
board.Save(BOARD)
print("saved", BOARD)
 
