#!/usr/bin/env python3
# %% [markdown]
# # Convert global labels -> hierarchical labels on ONE KiCad sheet
#
# A `.kicad_sch` file *is* one sheet, so "a specific sheet" = one file.
#
# **Run order (top to bottom):**
# 1. Setup cell (imports + helper definitions) - run once.
# 2. Config cell - point `TARGET_SHEET` at your file, set `APPLY_CHANGES`.
# 3. Load -> Select/preview -> Convert (in memory) -> Write.
#
# Each workflow cell leaves its result in a variable you can inspect
# (`sch`, `targets`, `retained_shapes`).
#
# **Wiring caveat:** hierarchical labels only connect through a matching *sheet
# pin* on this sheet's symbol in its PARENT schematic. After converting, import
# the sheet pins in the parent (Eeschema can do this from the labels) and wire
# them, or these nets disconnect from the rest of the design. A hierarchical
# label's *shape* sets that pin's direction, so it is preserved here verbatim.

# %%
# ============================================================
# Setup: imports, type aliases, and all helper definitions.
# Run this cell ONCE before stepping through the workflow.
# ============================================================
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from sexpdata import Symbol
from skip import Schematic

# kicad-skip / sexpdata objects are dynamically typed; these aliases document
# intent without pinning fragile internal class paths.
SExpr = Any  # a sexpdata node: Symbol | str | int | float | list[SExpr]
Label = Any  # a kicad-skip label wrapper (GlobalLabelWrapper / ParsedValue)

# Child tokens that belong only to a global label and must be removed.
_GLOBAL_ONLY_TOKENS: set[str] = {"fields_autoplaced"}
_INTERSHEET_PROPERTY_NAME: str = "Intersheetrefs"
# Fallback shape, used only if a source label somehow has no (shape ...) node.
_DEFAULT_SHAPE: str = "input"


# ---- Unit 1: load the sheet ----------------------------------------
def load_sheet(path_str: str) -> Schematic:
    """Open the .kicad_sch file and return a parsed Schematic."""
    path = Path(path_str)
    if not path.is_file():
        raise FileNotFoundError(f"Sheet not found: {path}")
    return Schematic(str(path))


# ---- Unit 2: select which global labels to convert -----------------
def select_global_labels(
    sch: Schematic, name_filter: set[str] | None = None
) -> list[Label]:
    """
    Return the global-label wrappers to convert.

    Materialised into a fixed list on purpose: we are about to mutate each
    label so it stops being a global label, and we must not iterate a
    collection that changes underneath us.
    """
    labels: list[Label] = list(sch.global_label)
    if name_filter is not None:
        labels = [lbl for lbl in labels if lbl.value in name_filter]
    return labels


# ---- Unit 3: convert a single label, preserving its shape ----------
def _child_token(node: SExpr) -> str | None:
    """Leading symbol name of an S-expression child, or None if not a list-node."""
    if isinstance(node, list) and node and isinstance(node[0], Symbol):
        return node[0].value()
    return None


def _find_child(raw: list[SExpr], token: str) -> SExpr | None:
    """First child whose head symbol == token, else None."""
    for child in raw:
        if _child_token(child) == token:
            return child
    return None


def read_shape(raw: list[SExpr]) -> str | None:
    """Return the label's shape value (e.g. 'input'), or None if absent."""
    shape_node = _find_child(raw, "shape")
    if (
        shape_node is not None
        and len(shape_node) > 1
        and isinstance(shape_node[1], Symbol)
    ):
        return shape_node[1].value()
    return None


def _is_global_only_child(node: SExpr) -> bool:
    """True if this child is a global-label-only artifact to drop."""
    token = _child_token(node)
    if token is None:
        return False
    if token == "property" and len(node) > 1 and node[1] == _INTERSHEET_PROPERTY_NAME:
        return True
    return token in _GLOBAL_ONLY_TOKENS


def convert_label_in_place(label: Label) -> str:
    """
    Rewrite one global label's raw tree into a hierarchical label, in place.
    Returns the shape value carried over (handy to print/inspect).

    Shape is preserved two ways: the (shape ...) child is never filtered out,
    and we additionally guarantee a shape node exists afterwards, re-inserting
    the original value (or _DEFAULT_SHAPE) in the rare case one was missing.
    """
    raw: list[SExpr] = label.raw

    # Capture the shape BEFORE any edits.
    original_shape = read_shape(raw)

    # 1. Flip the element type token.
    raw[0] = Symbol("hierarchical_label")

    # 2. Drop global-only children. This never matches (shape ...), so the
    #    shape node (with its original value) survives this step.
    raw[:] = [child for child in raw if not _is_global_only_child(child)]

    # 3. Guarantee shape retention. Normally a no-op; rebuilds the node only if
    #    the source label had none, inserting it right after the name (index 2)
    #    to match KiCad's child ordering.
    shape_value = original_shape if original_shape is not None else _DEFAULT_SHAPE
    if _find_child(raw, "shape") is None:
        raw.insert(2, [Symbol("shape"), Symbol(shape_value)])

    return shape_value


# ---- Unit 4: backup + write ----------------------------------------
def back_up(path_str: str) -> Path:
    """Copy the sheet to '<file>.bak' and return the backup path."""
    src = Path(path_str)
    dst = src.with_suffix(src.suffix + ".bak")
    shutil.copy2(src, dst)  # copy2 preserves timestamps/metadata
    return dst


def write_sheet(sch: Schematic, path_str: str) -> None:
    """Persist the modified schematic back to its file."""
    sch.write(path_str)


print("hello world")
# %% [markdown]
# ## Step 1 - Configure (edit me)

# %%
TARGET_SHEET: str = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/switch_matrix.kicad_sch"
APPLY_CHANGES: bool = False  # False = preview; True = let Step 5 save
MAKE_BACKUP: bool = True  # write "<file>.bak" before overwriting
LABEL_NAME_FILTER: set[str] | None = None  # e.g. {"SCK", "MOSI"}; None = all globals

# %% [markdown]
# ## Step 2 - Load the sheet  (inspect `sch`)

# %%
sch = load_sheet(TARGET_SHEET)
print(f"Loaded {TARGET_SHEET}")

# %% [markdown]
# ## Step 3 - Select + preview  (inspect `targets`)
# Lists each label with the shape that becomes its parent sheet-pin direction.

# %%
targets = select_global_labels(sch, LABEL_NAME_FILTER)
if not targets:
    print("No matching global labels found - nothing to convert.")
else:
    print(f"{len(targets)} global label(s) queued for conversion:")
    for lbl in targets:
        print(f"  - {lbl.value!r:<24} shape={read_shape(lbl.raw)}")

# %% [markdown]
# ## Step 4 - Convert in memory  (inspect `retained_shapes`)
# Nothing is written to disk yet. `retained_shapes` confirms each label kept its shape.

# %%
retained_shapes = {lbl.value: convert_label_in_place(lbl) for lbl in targets}
print("Converted (label -> retained shape):")
for name, shape in retained_shapes.items():
    print(f"  - {name!r:<24} {shape}")

# %% [markdown]
# ## Step 5 - Write to disk
# Guarded by `APPLY_CHANGES`. Set it True in Step 1 (and re-run that cell) when ready.

# %%
if not APPLY_CHANGES:
    print("APPLY_CHANGES is False -> preview only, nothing written.")
else:
    if MAKE_BACKUP:
        print(f"Backup: {back_up(TARGET_SHEET)}")
    write_sheet(sch, TARGET_SHEET)
    print(f"Updated: {TARGET_SHEET}")
    print(
        "Next: in the PARENT sheet, import the matching sheet pins for these "
        "labels and wire them up."
    )
