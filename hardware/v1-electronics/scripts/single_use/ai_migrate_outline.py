# eventually change names for migration naming
# Outline v2 + J1 move. Replaces the board outline with ONE closed polygon on Edge.Cuts that keeps real arcs,
# and slides J1 (USB-C) 2.708 mm outward so its "PCB Edge" mark sits on the left edge.
# Plain Python (no pcbnew): it edits slack.kicad_pcb as text.
#   1. deletes every board-level drawing on Edge.Cuts (gr_rect, gr_line, gr_arc, gr_poly, ...)
#   2. adds one gr_poly built from slack_outline_curves_v2.json (same folder as this script)
# In KiCad's file format a polygon's points can be plain corners (xy x y) or arcs
# (arc (start ..) (mid ..) (end ..)); straight edges are implied between consecutive points.
# Run with the board closed in KiCad. Commit first: git is the undo.

from pathlib import Path
import json
import re
import uuid

HERE = Path(__file__).resolve().parent
BOARD = Path(HERE.parents[1] / "slack.kicad_pcb")     # script is in v1-electronics/scripts/single_use/
PIECES = json.loads((HERE / "slack_outline_curves_v2.json").read_text())

text = Path(BOARD).read_text()      # Path() so this works even if BOARD is a plain string

# 1. Split the file into its top-level items (KiCad writes each one starting on "\n\t(").
body = text.rstrip()
body = body[:-1].rstrip() if body.endswith(")") else body     # drop the file's final ")"
head, *items = re.split(r"\n\t(?=\()", body)
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

# 3. Move J1: only its own (at ...) line changes; its pads are stored relative to it.
old_at, new_at = "(at 72.883884 88.196945 80)", "(at 70.2168 87.7268 80)"
j1 = next(i for i, item in enumerate(kept) if '(property "Reference" "J1"' in item)
assert old_at in kept[j1], "J1 isn't where this script expects; was it moved?"
kept[j1] = kept[j1].replace(old_at, new_at, 1)
print("moved J1 to", new_at)

Path(BOARD).write_text(head + "".join("\n\t" + item for item in kept + [poly]) + "\n)\n")
arcs = sum(p["type"] == "arc" for p in PIECES)
print(f"added one polygon: {len(PIECES) - arcs} straight edges and {arcs} arcs")
print("saved", BOARD)
