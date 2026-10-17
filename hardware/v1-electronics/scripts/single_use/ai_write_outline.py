# Replaces the board outline: deletes everything on Edge.Cuts (the old rectangle) and draws the
# new outline as separate lines and arcs from slack_outline_curves.json (same folder as this script).
# Each entry is {"type": "line", "points": [start, end]} or {"type": "arc", "points": [start, mid, end]},
# in mm, in order around the board; each piece ends where the next one starts.
# Run with stable KiCad's Python, with the board closed in KiCad. Commit first.

from pathlib import Path
import json
import pcbnew

HERE = Path(__file__).resolve().parent
BOARD = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/slack.kicad_pcb"      # script is in v1-electronics/scripts/single_use/
PIECES = json.loads((HERE / "slack_outline_curves.json").read_text())

board = pcbnew.LoadBoard(BOARD)
if board is None:
    raise SystemExit(f"Could not open {BOARD}")

# 1. Remove the old outline (board-level drawings on Edge.Cuts only; footprints are untouched).
old = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
for d in old:
    board.Remove(d)
print(f"removed {len(old)} old Edge.Cuts shape(s)")

# 2. Draw each line and arc.
mm = lambda p: pcbnew.VECTOR2I_MM(p[0], p[1])
for piece in PIECES:
    pts = piece["points"]
    if piece["type"] == "line":
        shape = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        shape.SetStart(mm(pts[0]))
        shape.SetEnd(mm(pts[1]))
    else:
        shape = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        shape.SetArcGeometry(mm(pts[0]), mm(pts[1]), mm(pts[2]))   # start, a point on the arc, end
    shape.SetLayer(pcbnew.Edge_Cuts)
    shape.SetWidth(pcbnew.FromMM(0.05))
    board.Add(shape)

lines = sum(p["type"] == "line" for p in PIECES)
print(f"added {lines} lines and {len(PIECES) - lines} arcs")

board.Save(BOARD)
print("saved", BOARD)
