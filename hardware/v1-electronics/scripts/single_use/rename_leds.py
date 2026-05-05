"""
Bulk-rename LED references in a KiCad schematic (.kicad_sch).

Mapping:
    LED1  .. LED42  ->  LED1_1  .. LED42_1
    LED43 .. LED84  ->  LED1_2  .. LED42_2

Per the official KiCad Schematic File Format spec, a placed symbol
carries its reference designator in TWO places that must stay in sync:
  1) the symbol's "Reference" property
  2) the (reference "...") token inside the symbol's (instances) block

The instances block is the source of truth on load (KiCad uses it to
resolve per-sheet-path references in hierarchical designs), so this
script updates both.

Spec: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/

Tested with kicad-skip 0.2.5 against KiCad 7+ schematic format.

Usage:
    1. CLOSE the schematic in KiCad first (KiCad won't see external edits
       on an open file, and saving from KiCad would clobber your changes).
    2. Edit SCHEMATIC_PATH below to point at your file.
    3. Run:  python rename_leds.py
    4. Open the schematic in KiCad and run ERC.

A .bak file is written next to the original.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from skip import Schematic


SCHEMATIC_PATH = Path("/path/to/your/board.kicad_sch")


def build_rename_map() -> dict[str, str]:
    """LED1..LED42 -> LED{i}_1, LED43..LED84 -> LED{i-42}_2."""
    mapping: dict[str, str] = {}
    for i in range(1, 43):
        mapping[f"LED{i}"] = f"LED{i}_1"
    for i in range(43, 85):
        mapping[f"LED{i}"] = f"LED{i - 42}_2"
    return mapping


def update_instances_reference(symbol, new_ref: str) -> int:
    """
    Walk the symbol's (instances ...) block and update every
    (reference "...") token to `new_ref`.

    Structure per the KiCad schematic file format:
        (instances
          (project "PROJECT_NAME"
            (path "PATH_INSTANCE"
              (reference "REFERENCE")
              (unit UNIT))))

    Returns the number of reference tokens updated. A correctly-formed
    schematic should always have at least one per placed symbol.
    """
    instances = getattr(symbol, "instances", None)
    if instances is None:
        return 0

    count = 0
    for project in instances.children:
        # `project.children` includes the project name string AND the path objects
        for path in getattr(project, "children", []):
            if not hasattr(path, "entity_type") or path.entity_type != "path":
                continue
            for child in path.children:
                if hasattr(child, "entity_type") and child.entity_type == "reference":
                    child.value = new_ref
                    count += 1
    return count


def main(schematic_path: Path) -> None:
    if not schematic_path.exists():
        sys.exit(f"Schematic not found: {schematic_path}")

    backup = schematic_path.with_suffix(schematic_path.suffix + ".bak")
    shutil.copy2(schematic_path, backup)
    print(f"Backup written to: {backup}")

    sch = Schematic(str(schematic_path))
    rename = build_rename_map()
    expected = set(rename.keys())

    # First pass: gather targets and validate
    targets = []
    seen_old = set()
    for sym in sch.symbol:
        old = sym.property.Reference.value
        if old in rename:
            targets.append((sym, old, rename[old]))
            seen_old.add(old)

    missing = expected - seen_old
    if missing:
        print(
            f"WARNING: {len(missing)} expected references not found in schematic: "
            f"{sorted(missing, key=lambda r: int(r[3:]))}"
        )

    new_refs = [new for _, _, new in targets]
    if len(new_refs) != len(set(new_refs)):
        sys.exit("ABORT: target names collide with each other (bug in mapping).")

    existing = {sym.property.Reference.value for sym in sch.symbol}
    not_renamed = existing - seen_old
    collisions = set(new_refs) & not_renamed
    if collisions:
        sys.exit(
            f"ABORT: new names collide with existing refs already in the "
            f"schematic: {sorted(collisions)}"
        )

    # Second pass: apply
    for sym, old, new in targets:
        sym.property.Reference.value = new
        n = update_instances_reference(sym, new)
        if n == 0:
            print(f"  WARN  {old} -> {new}  (no instances block updated!)")
        else:
            print(f"  {old:>6} -> {new:<8}  (instances refs updated: {n})")

    sch.write(str(schematic_path))
    print(f"\nRenamed {len(targets)} symbols. Saved: {schematic_path}")
    print("Open the schematic in KiCad and run ERC to verify.")


if __name__ == "__main__":
    main(SCHEMATIC_PATH)
