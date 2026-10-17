# ai_transfer_scrollbars.py: put the two scroll bars from the example board onto the Slack board.
#
# Plain Python, nothing to install, no KiCad needed. Run it with KiCad closed: `pixi run scrollbar`.
# The Slack board must be in KiCad 10.0's format. The example board can be 10.0 or 10.99.
#
# Left scroll bar (RE9): middle click, the example's Lever class 2 (B2-...).
# Right scroll bar (RE10): end click, the example's Lever class 3 (B1-...).
#
# 1. Finds the 8 scroll-bar parts on the Slack board: the switches, LEDs and diodes by reference,
#    the two caps by footprint (they're only on the board, not in the schematic). Each must have
#    the right footprint, with its pads in the same places as the example part's. If not, it lists
#    what to change and stops without touching the board.
# 2. Moves each part to where it sits next to its encoder on the example board, turned with the
#    Slack encoder. The board file stores each pad's and text's angle already turned, so those
#    turn by the same amount as the part (what KiCad does when you rotate a part). It checks the
#    result in memory, writes it, and reads it back. The board must be committed in git first,
#    so `git restore slack.kicad_pcb` undoes it.

import math
import re
import subprocess

PROJECT = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics"
SLACK = f"{PROJECT}/slack.kicad_pcb"
EXAMPLE = ("/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-mechanics/"
           "scrollbars/example_scrollbar/example_scrollbar.kicad_pcb")
KICAD_10 = "(version 20260206)"   # near the top of every board saved by KiCad 10.0

SIDES = {   # Slack encoder: (example encoder, {example part: (Slack reference, the footprint it must have)})
    "RE9": ("B2-RE9", {   # left: middle click
        "B2-MP": ("", "Mechanical:grounded_scrollcap"),   # no reference: found by its footprint
        "B2-SW62": ("SW62", "ALPS Electric:SKQGAKE010"),
        "B2-LED62": ("LED62", "Liteon:LTSTFC12WEGBD5A"),
        "B2-D62": ("D62", "Diode_SMD:D_SOD-523"),
    }),
    "RE10": ("B1-RE9", {   # right: end click
        "B1-MP": ("", "Mechanical:switched_grounded_scrollcap"),
        "B1-SW62": ("SW63", "XKB Connection:TC-1109-C-E"),
        "B1-LED62": ("LED63", "Liteon:LTSTFC12WEGBD5A"),
        "B1-D62": ("D63", "Diode_SMD:D_SOD-523"),
    }),
}

NUM = r"[-\d.e]+"
AT = rf"\(at ({NUM}) ({NUM})(?: ({NUM}))?\)"
OWN_AT = re.compile(rf"\n\t\t{AT}")          # KiCad 10.0: a footprint's own place, two tabs in
CHILD_AT = re.compile(rf"(\n\t\t\t+){AT}")   # its pads' and texts' places, three or more tabs in
TRANSFORM = re.compile(rf"\(transform\s*\(translate ({NUM}) ({NUM})\)\s*\(rotate ({NUM})\)")   # KiCad 10.99
UNSURE = ("zone", "group", "dimension", "fp_text_box", "textbox", "table", "image", "barcode")


def ok(msg):
    print(f"  ok    {msg}")


def stop(problems, board_written=False):
    for p in problems:
        print(f"  FAIL  {p}")
    raise SystemExit("Stopped. " + (f"Undo with: git -C '{PROJECT}' restore slack.kicad_pcb" if board_written
                                    else "The Slack board was not changed."))


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def num(v):
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def norm(a):
    """An angle in (-180, 180], as KiCad writes them."""
    a %= 360
    return a - 360 if a > 180 else a


def footprints(text):
    """Every footprint in a board file, in order: (reference without *, footprint, start, end)."""
    out = []
    for m in re.finditer(r'\n\t\(footprint "([^"]*)"', text):
        s = m.start() + 1
        e = text.index("\n\t)", s) + 3
        ref = re.search(r'\(property "Reference" "([^"]*)"', text[s:e]).group(1).rstrip("*")
        out.append((ref, m.group(1), s, e))
    return out


def pose(block):
    """A footprint's place and rotation: (x, y, degrees). KiCad 10.99 writes them in a
    (transform ...) block, KiCad 10.0 as the footprint's own (at x y degrees)."""
    m = TRANSFORM.search(block) or OWN_AT.search(block)
    return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)


def pad_places(block):
    """Where the footprint's pads sit in its own frame, sorted (stored the same way by 10.0 and 10.99)."""
    places = []
    for pad in re.findall(r"\n\t\t\(pad .*?\n\t\t\)", block, re.S):
        m = CHILD_AT.search(pad)
        places.append((round(float(m.group(2)), 3), round(float(m.group(3)), 3)))
    return sorted(places)


# ================================================================ 1. find the parts

def find(text, example):
    """Each scroll-bar part's position in the Slack board's list of footprints, with its name and
    the example part it copies: {index: (name, example part)}. Stops with a to-do list if anything's off."""
    print("\nStep 1: find the scroll-bar parts on the Slack board")
    if KICAD_10 not in text[:200]:
        stop(["slack.kicad_pcb isn't in KiCad 10.0's format. Was it saved by the nightly?"])
    fps = footprints(text)
    ex = {ref: example[s:e] for ref, _, s, e in footprints(example)}
    found, todo = {}, []
    for enc, (_, parts) in SIDES.items():
        if [f[0] for f in fps].count(enc) != 1:
            todo.append(f"{enc} should be on the board once")
        for ex_ref, (ref, want) in parts.items():
            name = ref or want.split(":")[1]   # the caps go by their footprint's name
            hits = [i for i, (r, lib, _, _) in enumerate(fps) if (r == ref if ref else lib == want)]
            if len(hits) != 1:
                todo.append(f"{name} is on the board {len(hits)} times; it should be there once")
                continue
            _, got, s, e = fps[hits[0]]
            if got != want:
                todo.append(f"{name} has footprint {got}; it should have {want}")
            elif ex_ref not in ex or pad_places(text[s:e]) != pad_places(ex[ex_ref]):
                todo.append(f"{name}'s pads aren't in the same places as {ex_ref}'s on the example board")
            elif any(re.search(rf"\n\t\t\({k}\b", text[s:e]) for k in UNSURE):
                todo.append(f"{name} contains a zone, group or similar, which this script can't turn")
            else:
                found[hits[0]] = (name, ex_ref)
    if todo:
        stop(todo)
    ok("found all 8 parts, each with the right footprint and its pads where the example part has them")
    return found


# ================================================================ 2. move them

def turn(x, y, deg):
    """KiCad's RotatePoint: y points down, a positive angle turns counter-clockwise on screen."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), y * math.cos(a) - x * math.sin(a)


def targets(example, text, found):
    """Each part's place: its offset from its encoder on the example board, turned and moved with
    the Slack encoder; its angle turns by the same amount. {index: (x, y, degrees)}"""
    ex = {ref: pose(example[s:e]) for ref, _, s, e in footprints(example)}
    sl = {ref: pose(text[s:e]) for ref, _, s, e in footprints(text)}   # only the encoders are used
    side = {ex_ref: (enc, ex_enc) for enc, (ex_enc, parts) in SIDES.items() for ex_ref in parts}
    out = {}
    for i, (_, ex_ref) in found.items():
        enc, ex_enc = side[ex_ref]
        (ex0, ey0, ea0), (sx0, sy0, sa0), (fx, fy, fa) = ex[ex_enc], sl[enc], ex[ex_ref]
        dx, dy = turn(fx - ex0, fy - ey0, sa0 - ea0)
        out[i] = (sx0 + dx, sy0 + dy, norm(fa + sa0 - ea0))
    return out


def moved(block, x, y, a):
    """The footprint at (x, y), turned to a, in KiCad 10.0's format. Its pads and texts keep their
    places in its own frame; their angles, stored already turned, turn by the same amount."""
    delta = norm(a - pose(block)[2])
    own = f"\n\t\t(at {num(x)} {num(y)}" + ("" if num(a) == "0" else f" {num(a)}") + ")"
    block = OWN_AT.sub(lambda m: own, block, count=1)
    if abs(delta) < 1e-9:
        return block
    return CHILD_AT.sub(lambda m: f"{m.group(1)}(at {m.group(2)} {m.group(3)} "
                                  f"{num(norm(float(m.group(4) or 0) + delta))})", block)


def verify(old, new, goal, found):
    """Problems with the new file: the parts must be where they should be, their pads and texts
    turned with them, and every other character of the file as it was."""
    fo, fn = footprints(old), footprints(new)
    if [f[:2] for f in fo] != [f[:2] for f in fn]:
        return ["the footprints in the file aren't the same ones in the same order"]

    def outside(text, fps):   # everything in the file that isn't a footprint
        cuts = [0] + [x for *_, s, e in fps for x in (s, e)] + [len(text)]
        return "".join(text[a:b] for a, b in zip(cuts[::2], cuts[1::2]))

    def mask(block):   # the footprint without its own place and its pads' and texts' angles
        block = OWN_AT.sub("\n\t\t(at)", block, count=1)
        return CHILD_AT.sub(lambda m: f"{m.group(1)}(at {m.group(2)} {m.group(3)})", block)

    problems = [] if outside(old, fo) == outside(new, fn) else ["something outside the footprints changed"]
    for i, ((ref, _, s0, e0), (_, _, s1, e1)) in enumerate(zip(fo, fn)):
        b0, b1 = old[s0:e0], new[s1:e1]
        if i not in goal:
            if b0 != b1:
                problems.append(f"{ref} changed")
            continue
        name = found[i][0]
        (x, y, a), (wx, wy, wa) = pose(b1), goal[i]
        if abs(x - wx) > 1e-6 or abs(y - wy) > 1e-6 or abs(norm(a - wa)) > 1e-4:
            problems.append(f"{name} is at ({x}, {y}) {a}°, expected ({wx:.6f}, {wy:.6f}) {wa:.4f}°")
        delta = norm(a - pose(b0)[2])
        for m0, m1 in zip(CHILD_AT.finditer(b0), CHILD_AT.finditer(b1)):
            if abs(norm(float(m1.group(4) or 0) - float(m0.group(4) or 0) - delta)) > 1e-4:
                problems.append(f"{name}: a pad or text didn't turn with it")
                break
        if mask(b0) != mask(b1):
            problems.append(f"{name}: something other than its place and angles changed")
    return problems


def move():
    text, example = read(SLACK), read(EXAMPLE)
    found = find(text, example)

    print("\nStep 2: move the parts next to their encoders")
    goal = targets(example, text, found)
    fps = footprints(text)
    for i, (x, y, a) in goal.items():
        ox, oy, oa = pose(text[fps[i][2]:fps[i][3]])
        print(f"        {found[i][0]:28} ({ox:8.3f}, {oy:8.3f}) {norm(oa):8.2f}°"
              f"  ->  ({x:8.3f}, {y:8.3f}) {a:8.2f}°")
    new = text
    for i in sorted(goal, reverse=True):   # from the end of the file, so the earlier places stay valid
        _, _, s, e = fps[i]
        new = new[:s] + moved(new[s:e], *goal[i]) + new[e:]
    problems = verify(text, new, goal, found)
    if problems:
        stop(problems)
    ok("checked in memory: the 8 parts are in place, their pads and texts turned with them, "
       "and the rest of the file is unchanged")
    if new == text:
        print("\nDone. Everything was already in place; nothing to write.")
        return

    dirty = subprocess.run(["git", "-C", PROJECT, "status", "--porcelain", "--", "slack.kicad_pcb"],
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        stop(["slack.kicad_pcb has changes that aren't committed; commit them first, "
              "so `git restore slack.kicad_pcb` can undo this"])
    write(SLACK, new)
    if read(SLACK) != new:
        stop(["the file doesn't read back as written"], board_written=True)
    ok("wrote slack.kicad_pcb and read it back")
    print("\nDone. Open the board in KiCad, look at both scroll bars, and run DRC.")


if __name__ == "__main__":
    move()