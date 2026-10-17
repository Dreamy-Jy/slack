# Adds the 14 M2 mounting holes to slack.kicad_pcb.
# Run from hardware/v1-electronics with stable KiCad's Python, with the board closed in KiCad:
#   /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 add_mounting_holes.py
# Commit first: git is the undo. Running it twice adds the holes twice.

import pcbnew

BOARD = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/slack.kicad_pcb"
LIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty"
HOLE = "MountingHole_2.2mm_M2_Pad_Via"   # M2, plated, 4.4 mm copper ring, stitching vias

# (x, y) in mm. Pairs mirror about x = 221.4484 (the board's centre line); H13 and H14 sit on it.
HOLES = [
    (147.678, 49.885), (295.218, 49.885),
    (72.818, 69.510), (370.078, 69.510),
    (56.318, 153.375), (386.578, 153.375),
    (166.768, 169.195), (276.128, 169.195),
    (92.838, 182.150), (350.058, 182.150),
    (128.723, 198.375), (314.173, 198.375),
    (221.448, 132.070),
    (221.448, 196.330),
]

board = pcbnew.LoadBoard(BOARD)
ground = board.FindNet("DGND")

for number, (x, y) in enumerate(HOLES, start=1):
    hole = pcbnew.FootprintLoad(LIB, HOLE)
    hole.SetReference(f"H{number}")
    hole.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    hole.SetBoardOnly(True)          # no schematic symbol, so F8 won't flag it
    hole.SetExcludedFromBOM(True)
    board.Add(hole)
    for pad in hole.Pads():
        pad.SetNet(ground)
    print(f"H{number} at ({x}, {y})")

board.Save(BOARD)
print("saved", BOARD)