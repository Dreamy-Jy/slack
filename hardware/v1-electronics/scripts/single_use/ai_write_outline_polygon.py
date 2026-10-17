# Replaces the board outline with ONE closed polygon on Edge.Cuts that keeps real arcs.
# Plain Python (no pcbnew): it edits slack.kicad_pcb as text.
#   1. deletes every board-level drawing on Edge.Cuts (gr_rect, gr_line, gr_arc, gr_poly, ...)
#   2. adds one gr_poly built from slack_outline_curves.json (same folder as this script)
# In KiCad's file format a polygon's points can be plain corners (xy x y) or arcs
# (arc (start ..) (mid ..) (end ..)); straight edges are implied between consecutive points.
# Run with the board closed in KiCad. Commit first: git is the undo.

from pathlib import Path
import json
import re
import uuid

HERE = Path(__file__).resolve().parent
BOARD = Path("/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/slack.kicad_pcb")           # script is in v1-electronics/scripts/single_use/
PIECES = json.loads((HERE / "slack_outline_curves_chin20mm.json").read_text())

text = BOARD.read_text()

# 1. Split the file into its top-level items (KiCad writes each one starting on "\n\t(").
head, *items = re.split(r"\n\t(?=\()", text.rstrip().removesuffix(")").rstrip())
is_edge_drawing = lambda item: item.startswith("(gr_") and '(layer "Edge.Cuts")' in item
kept = [item for item in items if not is_edge_drawing(item)]
print(f"removed {len(items) - len(kept)} old Edge.Cuts drawing(s)")

# 2. Build the polygon's point list.
xy = lambda p: f"(xy {p[0]:.4f} {p[1]:.4f})"
pts = []
for i, piece in enumerate(PIECES):
    previous = PIECES[i - 1]          # for i == 0 this is the last piece: the outline is closed
    p = piece["points"]
    if piece["type"] == "arc":
        pts.append(f"(arc\n\t\t\t\t(start {p[0][0]:.4f} {p[0][1]:.4f})\n\t\t\t\t(mid {p[1][0]:.4f} {p[1][1]:.4f})"
                   f"\n\t\t\t\t(end {p[2][0]:.4f} {p[2][1]:.4f})\n\t\t\t)")
    elif previous["type"] != "arc":   # a line's start point; after an arc that point is the arc's end
        pts.append(xy(p[0]))

poly = ("(gr_poly\n\t\t(pts\n\t\t\t" + "\n\t\t\t".join(pts) + "\n\t\t)\n"
        "\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid)\n\t\t)\n"
        "\t\t(fill no)\n"
        '\t\t(layer "Edge.Cuts")\n'
        f'\t\t(uuid "{uuid.uuid4()}")\n\t)')

BOARD.write_text(head + "".join("\n\t" + item for item in kept + [poly]) + "\n)\n")
arcs = sum(p["type"] == "arc" for p in PIECES)
print(f"added one polygon: {len(PIECES) - arcs} straight edges and {arcs} arcs")
print("saved", BOARD)
