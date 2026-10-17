# ai_transfer_scrollbars.py: put the two scroll bars from the example board onto the Slack board.
#
# Plain Python, nothing to install, no KiCad needed. Run it with KiCad closed: `pixi run scrollbar`.
#
# Left scroll bar (RE9): middle click, the example's Lever class 2 (B2-...).
# Right scroll bar (RE10): end click, the example's Lever class 3 (B1-...).
#
# 1. Makes the two cap footprints the Slack project doesn't have, in v1-electronics/mechanical/,
#    copied from the example board with their absolute 3D model paths, and adds that folder to
#    the project's fp-lib-table. Every run refreshes them from the example board.
# 2. Checks every scroll-bar part is on the Slack board with the right footprint, the caps on
#    ground, and each click switch wired across its contacts. If not, it lists what to change
#    in the schematic and stops without touching the board.
# 3. Moves each part to where it sits next to its encoder on the example board, turned with the
#    Slack encoder. The board file stores each pad's and text's angle already turned, so those
#    turn by the same amount as the part (what KiCad does when you rotate a part). It checks the
#    result in memory, writes it, and reads it back. The board must be committed in git first,
#    so `git restore slack.kicad_pcb` undoes it.

import math
import os
import re
import subprocess

PROJECT = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics"
SLACK = f"{PROJECT}/slack.kicad_pcb"
MECH = f"{PROJECT}/mechanical"
EXAMPLE = ("/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-mechanics/"
           "scrollbars/example_scrollbar/example_scrollbar.kicad_pcb")
GROUND = "DGND"   # the caps' mounting pads

SIDES = {   # Slack encoder: (example encoder, {example ref: (Slack ref, the footprint it must have)})
    "RE9": ("B2-RE9", {   # left: middle click
        "B2-MP": ("MP62", "mechanical:grounded_scrollcap"),
        "B2-SW62": ("SW62", "ALPS Electric:SKQGAKE010"),
        "B2-LED62": ("LED62", "Liteon:LTSTFC12WEGBD5A"),
        "B2-D62": ("D62", "Diode_SMD:D_SOD-523"),
    }),
    "RE10": ("B1-RE9", {   # right: end click
        "B1-MP": ("MP63", "mechanical:switched_grounded_scrollcap"),
        "B1-SW62": ("SW63", "XKB Connection:TC-1109-C-E"),
        "B1-LED62": ("LED63", "Liteon:LTSTFC12WEGBD5A"),
        "B1-D62": ("D63", "Diode_SMD:D_SOD-523"),
    }),
}
MAKE = {   # footprint made in mechanical/: (example ref it's copied from, new pad numbers)
    "grounded_scrollcap": ("B2-MP", {}),
    "switched_grounded_scrollcap": ("B1-MP", {}),
}
LIB_LINE = ('\t(lib (name "mechanical") (type "KiCad") (uri "${KIPRJMOD}/mechanical") (options "") '
            '(descr "Scroll-bar footprints made by ai_transfer_scrollbars.py"))\n')

NUM = r"[-\d.e]+"
AT = re.compile(rf"\(at ({NUM}) ({NUM})(?: ({NUM}))?\)")   # a pad's or text's place and angle
TRANSFORM = re.compile(rf"(\(transform\s*\(translate )({NUM}) ({NUM})(\)\s*\(rotate )({NUM})(\))")
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
    """Every footprint in a board file, in order: (reference without *, start, end)."""
    out = []
    for m in re.finditer(r'\n\t\(footprint "', text):
        s = m.start() + 1
        e = text.index("\n\t)", s) + 3
        out.append((re.search(r'\(property "Reference" "([^"]*)"', text[s:e]).group(1).rstrip("*"), s, e))
    return out


def pose(block):
    """A footprint's place and rotation: (x, y, degrees)."""
    m = TRANSFORM.search(block)
    return float(m.group(2)), float(m.group(3)), float(m.group(5))


def pads(block):
    """Each pad: (number, x, y, net), x and y in the footprint's own frame."""
    out = []
    for m in re.finditer(r'\n\t\t\(pad "([^"]*)".*?\n\t\t\)', block, re.S):
        at = AT.search(m.group(0))
        net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', m.group(0))
        out.append((m.group(1), float(at.group(1)), float(at.group(2)), net.group(1) if net else ""))
    return out


# ================================================================ 1. the footprints to make

def to_library(block, name, renumber, header):
    """A footprint copied out of a board file, as a library footprint: at the origin, unturned,
    with no nets or schematic links. The board file stores pad and text angles already turned
    by the footprint's rotation, so that rotation comes off them."""
    turn_by = pose(block)[2]
    block = re.sub(r"\n\t\t\(transform\n.*?\n\t\t\)", "", block, count=1, flags=re.S)
    block = re.sub(r"\n\t\t\((uuid|path|sheetname|sheetfile) [^\n]*", "", block)   # the footprint's own
    block = re.sub(r"\n\t\t\t\((net|pinfunction|pintype) [^\n]*", "", block)       # each pad's
    if turn_by % 360:
        block = AT.sub(lambda m: f"(at {m.group(1)} {m.group(2)} {num(norm(float(m.group(3) or 0) - turn_by))})",
                       block)
    block = re.sub(r'\(pad "([^"]*)"', lambda m: f'(pad "{renumber.get(m.group(1), m.group(1))}"', block)
    block = re.sub(r'\(property "Reference" "[^"]*"', '(property "Reference" "REF**"', block, count=1)
    block = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{name}"', block, count=1)
    block = block[1:].replace("\n\t", "\n")   # one tab less: the footprint is the whole file now
    return re.sub(r'^\(footprint "[^"]*"', f'(footprint "{name}"\n{header}', block, count=1) + "\n"


def make_library():
    print("\nStep 1: make the footprints the Slack project doesn't have")
    text = read(EXAMPLE)
    header = "\n".join("\t" + line.strip() for line in text.split("\n")[1:4])   # version, generator
    blocks = {ref: text[s:e] for ref, s, e in footprints(text)}
    missing = [ref for ref, _ in MAKE.values() if ref not in blocks]
    if missing:
        stop([f"{ref} isn't on the example board" for ref in missing])
    os.makedirs(MECH, exist_ok=True)
    for name, (ref, renumber) in MAKE.items():
        lib = to_library(blocks[ref], name, renumber, header)
        write(f"{MECH}/{name}.kicad_mod", lib)
        model = re.search(r'\(model "([^"]*)"', lib)
        found = model and os.path.exists(model.group(1))
        ok(f"mechanical/{name}.kicad_mod from {ref}; 3D model {model.group(1) if model else 'none'}"
           + ("" if found else "  (STEP NOT FOUND)"))
    table = f"{PROJECT}/fp-lib-table"
    t = read(table)
    if '(name "mechanical")' in t:
        ok("the mechanical library is already in the project's fp-lib-table")
    else:
        write(table, t.rstrip()[:-1].rstrip("\n") + "\n" + LIB_LINE + ")\n")
        ok("added the mechanical library to the project's fp-lib-table")


# ================================================================ 2. check the Slack board

def wired_across(block):
    """True if each row of pads is on one net and the two rows on different nets: the pads in a
    row are joined inside the switch (Alps SKQG: 1-2 and 3-4; XKB TC-1109: numbered 1,1 and 2,2)."""
    rows = {}
    for _, _, y, net in pads(block):
        row = next((r for r in rows if abs(y - r) < 0.5), y)
        rows.setdefault(row, set()).add(net)
    nets = list(rows.values())
    good = len(nets) == 2 and all(len(n) == 1 and "" not in n for n in nets) and nets[0] != nets[1]
    return good, [sorted(n) for n in nets]


def check(text):
    print("\nStep 2: check the Slack board has every part, with the right footprint")
    refs = [ref for ref, _, _ in footprints(text)]
    blocks = {ref: text[s:e] for ref, s, e in footprints(text)}
    todo = []
    for enc, (_, parts) in SIDES.items():
        if enc not in blocks:
            todo.append(f"{enc} isn't on the Slack board")
        for ref, want in parts.values():
            b = blocks.get(ref)
            got = re.match(r'\t\(footprint "([^"]*)"', b).group(1) if b else None
            if b is None:
                todo.append(f"{ref}: add it in the schematic with footprint {want}, then Update PCB from Schematic")
            elif refs.count(ref) > 1:
                todo.append(f"{ref} is on the board {refs.count(ref)} times")
            elif got != want:
                todo.append(f"{ref}: change its footprint from {got} to {want} in the schematic, "
                            "then Update PCB from Schematic")
            elif ref.startswith("MP") and {p[3] for p in pads(b)} != {GROUND}:
                todo.append(f"{ref}: its pads aren't all on {GROUND}; wire its pin to {GROUND} in the schematic")
            elif ref.startswith("SW") and not wired_across(b)[0]:
                todo.append(f"{ref}: its pads are on {wired_across(b)[1]} by row. The switch joins each row of "
                            "pads inside, so each row needs one net and the two rows different nets. Number "
                            "the footprint's pads 1,1 and 2,2 by row, or give it a 4-pin symbol")
            elif any(re.search(rf"\n\t\t\({k}\b", b) for k in UNSURE):
                todo.append(f"{ref} contains a zone, group or similar, which this script can't turn")
    if todo:
        stop(todo)
    ok(f"all 8 parts are there with the right footprints; the caps' pads are on {GROUND}; "
       "both switches are wired across their contacts")


# ================================================================ 3. move them

def turn(x, y, deg):
    """KiCad's RotatePoint: y points down, a positive angle turns counter-clockwise on screen."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), y * math.cos(a) - x * math.sin(a)


def targets(example, slack):
    """Each Slack part's place: its offset from its encoder on the example board, turned and
    moved with the Slack encoder; its angle turns by the same amount."""
    ex = {ref: pose(example[s:e]) for ref, s, e in footprints(example)}
    sl = {ref: pose(slack[s:e]) for ref, s, e in footprints(slack)}
    out = {}
    for enc, (ex_enc, parts) in SIDES.items():
        (ex0, ey0, ea0), (sx0, sy0, sa0) = ex[ex_enc], sl[enc]
        for ex_ref, (ref, _) in parts.items():
            fx, fy, fa = ex[ex_ref]
            dx, dy = turn(fx - ex0, fy - ey0, sa0 - ea0)
            out[ref] = (sx0 + dx, sy0 + dy, norm(fa + sa0 - ea0))
    return out


def moved(block, x, y, a):
    """The footprint at (x, y), turned to a. Its pads and texts keep their places in its own
    frame; their angles, stored already turned, turn by the same amount as the footprint."""
    delta = norm(a - pose(block)[2])
    block = TRANSFORM.sub(lambda m: f"{m.group(1)}{num(x)} {num(y)}{m.group(4)}{num(a)}{m.group(6)}", block, count=1)
    if abs(delta) < 1e-9:
        return block
    return AT.sub(lambda m: f"(at {m.group(1)} {m.group(2)} {num(norm(float(m.group(3) or 0) + delta))})", block)


def verify(old, new, goal):
    """Problems with the new file: the parts must be where they should be, their pads and texts
    turned with them, and every other character of the file as it was."""
    fo, fn = footprints(old), footprints(new)
    if [r for r, _, _ in fo] != [r for r, _, _ in fn]:
        return ["the footprints in the file aren't the same ones in the same order"]

    def outside(text, spans):
        cuts = [0] + [x for _, s, e in spans for x in (s, e)] + [len(text)]
        return "".join(text[a:b] for a, b in zip(cuts[::2], cuts[1::2]))

    def mask(block):   # the footprint without its place and angles
        return AT.sub(lambda m: f"(at {m.group(1)} {m.group(2)})", TRANSFORM.sub(r"\1X X\4A\6", block))

    problems = [] if outside(old, fo) == outside(new, fn) else ["something outside the footprints changed"]
    for (ref, s0, e0), (_, s1, e1) in zip(fo, fn):
        b0, b1 = old[s0:e0], new[s1:e1]
        if ref not in goal:
            if b0 != b1:
                problems.append(f"{ref} changed")
            continue
        (x, y, a), (wx, wy, wa) = pose(b1), goal[ref]
        if abs(x - wx) > 1e-6 or abs(y - wy) > 1e-6 or abs(norm(a - wa)) > 1e-4:
            problems.append(f"{ref} is at ({x}, {y}) {a}°, expected ({wx:.6f}, {wy:.6f}) {wa:.4f}°")
        delta = norm(a - pose(b0)[2])
        for m0, m1 in zip(AT.finditer(b0), AT.finditer(b1)):
            if abs(norm(float(m1.group(3) or 0) - float(m0.group(3) or 0) - delta)) > 1e-4:
                problems.append(f"{ref}: a pad or text didn't turn with it")
                break
        if mask(b0) != mask(b1):
            problems.append(f"{ref}: something other than its place and angles changed")
    return problems


def move():
    text = read(SLACK)
    check(text)

    print("\nStep 3: move the parts next to their encoders")
    goal = targets(read(EXAMPLE), text)
    now = {ref: pose(text[s:e]) for ref, s, e in footprints(text)}
    for ref, (x, y, a) in goal.items():
        ox, oy, oa = now[ref]
        print(f"        {ref:6} ({ox:8.3f}, {oy:8.3f}) {norm(oa):8.2f}°  ->  ({x:8.3f}, {y:8.3f}) {a:8.2f}°")
    new = text
    for ref, s, e in sorted(footprints(text), key=lambda f: -f[1]):   # from the end, so places stay valid
        if ref in goal:
            new = new[:s] + moved(new[s:e], *goal[ref]) + new[e:]
    problems = verify(text, new, goal)
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
    make_library()
    move()