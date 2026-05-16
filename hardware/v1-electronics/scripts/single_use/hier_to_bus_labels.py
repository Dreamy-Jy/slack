#!/usr/bin/env python3
"""
hier_to_bus_labels.py
=====================

Project-wide refactor: convert per-pin *hierarchical labels* into plain *local
labels* whose names are members of an existing hierarchical bus.

Example conversions (defined by TRANSFORMS):

    (hierarchical_label "CS1_1"   (shape input) ...)  ->  (label "Chip1CurrentSource1" ...)
    (hierarchical_label "SW1_B_1" (shape input) ...)  ->  (label "Chip1SinkSwitch1"    ...)

Local labels carry no direction, so the (shape ...) child is dropped. A local
label joins its bus purely by name -- e.g. "Chip1CurrentSource1" is a member of
the bus "Chip1CurrentSource[1..16]" -- so no wiring changes are required.

How it works
------------
* Only hierarchical labels whose name matches a rule in TRANSFORMS are touched.
  Everything else -- the bus labels themselves and any other hierarchical
  labels -- is left exactly as it was.
* Edits are applied as surgical text changes (rewrite the one-line header,
  delete the one-line shape) so the diff stays minimal and reviewable under
  version control, instead of reformatting the whole file.
* After editing, every file is re-parsed and checked against the plan. A file
  is written only if the result parses and matches what was intended.

Usage
-----
    python hier_to_bus_labels.py              # process the project (see CONFIG)
    python hier_to_bus_labels.py --self-test  # run the built-in tests, touch nothing
"""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TypeAlias, Union

import sexpdata
from sexpdata import Symbol

# ======================================================================
# Types
# ======================================================================
# A parsed S-expression node, as produced by sexpdata.
SExpr: TypeAlias = Union[Symbol, str, int, float, "list[SExpr]"]
# A compiled rename rule: a pattern matching an OLD name + its replacement.
Rule: TypeAlias = "tuple[re.Pattern[str], str]"


# ======================================================================
# CONFIG  --  edit me
# ======================================================================
# Folder to search for schematic files.
PROJECT_DIR: Path = Path("/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/")

# Which files to process. Use "**/*.kicad_sch" to recurse into sub-folders.
FILE_GLOB: str = "*.kicad_sch"

# True  -> report what would change and write nothing.
# False -> apply the edits in place.
DRY_RUN: bool = False

# Write "<file>.bak" beside each file before overwriting it.
MAKE_BACKUP: bool = True

# The transformation table: (regex matching the OLD hierarchical-label name,
# replacement producing the NEW local-label name). Patterns are anchored so
# only intended labels match; "\1" is the captured index. The colour letter in
# the SW patterns is matched but discarded by design.
TRANSFORMS: list[tuple[str, str]] = [
    (r"^RE(\d+)_A-Channel$", r"RotaryEncoder_AChannel\1"),
    (r"^RE(\d+)_B-Channel$", r"RotaryEncoder_BChannel\1"),
    (r"^CS(\d+)_1$",         r"Chip1CurrentSource\1"),
    (r"^CS(\d+)_2$",         r"Chip2CurrentSource\1"),
    (r"^SW(\d+)_[BGRW]_1$",  r"Chip1SinkSwitch\1"),
    (r"^SW(\d+)_[BGRW]_2$",  r"Chip2SinkSwitch\1"),
]


# ======================================================================
# Result data structures
# ======================================================================
@dataclass(frozen=True)
class Rename:
    """One planned label conversion."""

    old: str  # original hierarchical-label name
    new: str  # resulting local-label name


@dataclass
class LabelSurvey:
    """A snapshot of the labels in one sheet, used for planning and checking."""

    hierarchical: set[str]       # names of all hierarchical labels
    local: set[str]              # names of all local labels
    local_with_shape: set[str]   # local labels that (wrongly) still have a shape


@dataclass
class FileResult:
    """Outcome of processing a single schematic file."""

    path: Path
    renames: list[Rename]
    collisions: dict[str, list[str]]  # new_name -> [old_names] when >1 maps to it
    written: bool


# ======================================================================
# Rule handling
# ======================================================================
def compile_rules(transforms: list[tuple[str, str]]) -> list[Rule]:
    """Pre-compile the (pattern, replacement) table once."""
    return [(re.compile(pattern), replacement) for pattern, replacement in transforms]


def new_name_for(old_name: str, rules: list[Rule]) -> str | None:
    """
    Return the new local-label name for `old_name`, or None if no rule applies.

    Raises ValueError if more than one rule matches, since the table is meant to
    be unambiguous.
    """
    matches = [
        pattern.sub(replacement, old_name)
        for pattern, replacement in rules
        if pattern.match(old_name)
    ]
    if len(matches) > 1:
        raise ValueError(f"{old_name!r} matched multiple rules: {matches}")
    return matches[0] if matches else None


# ======================================================================
# S-expression inspection (read-only)
# ======================================================================
def node_token(node: SExpr) -> str | None:
    """The leading symbol name of an S-expression list node, else None."""
    if isinstance(node, list) and node and isinstance(node[0], Symbol):
        return str(node[0].value())
    return None


def survey_labels(text: str) -> LabelSurvey:
    """
    Parse `text` and summarise its labels. Also proves the text is parseable,
    which is why the verification step re-runs it on the edited output.
    """
    document = sexpdata.loads(text)
    hierarchical: set[str] = set()
    local: set[str] = set()
    local_with_shape: set[str] = set()

    for node in document:
        token = node_token(node)
        if token == "hierarchical_label":
            hierarchical.add(str(node[1]))
        elif token == "label":
            name = str(node[1])
            local.add(name)
            if any(node_token(child) == "shape" for child in node[2:]):
                local_with_shape.add(name)

    return LabelSurvey(hierarchical, local, local_with_shape)


# ======================================================================
# Planning
# ======================================================================
def plan_renames(text: str, rules: list[Rule]) -> tuple[list[Rename], dict[str, list[str]]]:
    """
    Work out which hierarchical labels in `text` should be converted.

    Returns the list of conversions and any target-name collisions
    (new_name -> [old_names]) so the caller can flag unintended merges.
    """
    survey = survey_labels(text)
    renames: list[Rename] = []
    by_target: dict[str, list[str]] = {}

    for old in sorted(survey.hierarchical):
        new = new_name_for(old, rules)
        if new is None:
            continue  # not a target -> leave it as a hierarchical label
        renames.append(Rename(old=old, new=new))
        by_target.setdefault(new, []).append(old)

    collisions = {new: olds for new, olds in by_target.items() if len(olds) > 1}
    return renames, collisions


# ======================================================================
# Applying the edits (surgical, minimal-diff)
# ======================================================================
def _conversion_pattern(old_name: str) -> re.Pattern[str]:
    """
    Match a canonical KiCad hierarchical-label header and its shape line:

        <indent>(hierarchical_label "<old_name>"
        <indent>    (shape <word>)

    Group 1 is the header indentation; group 2 is the header's line ending
    (so the original CRLF/LF is preserved). The shape line is consumed entirely
    and therefore removed.
    """
    return re.compile(
        r'^([ \t]*)\(hierarchical_label "' + re.escape(old_name) + r'"[ \t]*(\r?\n)'
        r'[ \t]*\(shape \w+\)[ \t]*\r?\n',
        re.MULTILINE,
    )


def _to_local_label(match: re.Match[str], new: str) -> str:
    """Replacement body: collapse the header+shape block to one local-label line."""
    indent, eol = match.group(1), match.group(2)
    return f'{indent}(label "{new}"{eol}'


def apply_renames(text: str, renames: list[Rename]) -> str:
    """
    Apply each conversion as a targeted edit. Every line except the two per
    label (header rewritten, shape removed) is left byte-for-byte unchanged.

    Raises RuntimeError if an expected label/shape block cannot be located,
    which signals unexpected formatting rather than silently skipping it.
    """
    for rename in renames:
        pattern = _conversion_pattern(rename.old)
        text, count = pattern.subn(partial(_to_local_label, new=rename.new), text)
        if count == 0:
            raise RuntimeError(
                f"Could not find hierarchical_label {rename.old!r} followed by a "
                f"(shape ...) line; formatting is not what was expected."
            )
    return text


# ======================================================================
# Verification (run before any file is written)
# ======================================================================
def verify(original_text: str, new_text: str, renames: list[Rename]) -> None:
    """
    Re-parse the edited text and assert it matches the plan exactly:

      * it still parses,
      * precisely the planned labels changed from hierarchical to local,
      * no other label changed kind,
      * every new local label exists and carries no shape.

    Raises AssertionError on any discrepancy.
    """
    before = survey_labels(original_text)
    after = survey_labels(new_text)  # also confirms new_text parses

    planned_olds = {rename.old for rename in renames}
    planned_news = {rename.new for rename in renames}

    # Exactly the planned names left the hierarchical set; nothing else moved.
    assert after.hierarchical == before.hierarchical - planned_olds, (
        "hierarchical labels changed unexpectedly: "
        f"{after.hierarchical ^ (before.hierarchical - planned_olds)}"
    )
    # Every planned new name is present as a local label.
    missing = planned_news - after.local
    assert not missing, f"expected new local labels are missing: {sorted(missing)}"
    # No unexpected local labels appeared.
    unexpected = (after.local - before.local) - planned_news
    assert not unexpected, f"unexpected local labels appeared: {sorted(unexpected)}"
    # None of the converted labels kept a shape.
    kept_shape = planned_news & after.local_with_shape
    assert not kept_shape, f"converted labels still carry a shape: {sorted(kept_shape)}"


# ======================================================================
# Per-file orchestration
# ======================================================================
def convert_file(
    path: Path, rules: list[Rule], *, dry_run: bool, make_backup: bool
) -> FileResult:
    """Plan, apply, verify, and (unless dry_run) write a single schematic file."""
    original = path.read_text(encoding="utf-8")
    renames, collisions = plan_renames(original, rules)

    if not renames:
        return FileResult(path=path, renames=[], collisions={}, written=False)

    updated = apply_renames(original, renames)
    verify(original, updated, renames)  # raises if anything is off

    written = False
    if not dry_run:
        if make_backup:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        path.write_text(updated, encoding="utf-8")
        written = True

    return FileResult(path=path, renames=renames, collisions=collisions, written=written)


def find_sheets(project_dir: Path, file_glob: str) -> list[Path]:
    """All matching schematic files, excluding our own .bak backups."""
    return sorted(
        p for p in project_dir.glob(file_glob)
        if p.suffix == ".kicad_sch" and p.is_file()
    )


# ======================================================================
# Entry points
# ======================================================================
def main() -> None:
    """Process every schematic under PROJECT_DIR according to the CONFIG block."""
    rules = compile_rules(TRANSFORMS)
    sheets = find_sheets(PROJECT_DIR, FILE_GLOB)

    if not sheets:
        print(f"No schematic files found under {PROJECT_DIR}/{FILE_GLOB}")
        return

    mode = "DRY-RUN (nothing written)" if DRY_RUN else "APPLYING CHANGES"
    print(f"{mode} -- {len(sheets)} sheet(s) under {PROJECT_DIR}\n")

    total = 0
    for sheet in sheets:
        result = convert_file(sheet, rules, dry_run=DRY_RUN, make_backup=MAKE_BACKUP)
        total += len(result.renames)

        if not result.renames:
            print(f"  {sheet.name}: no matching labels")
            continue

        state = "written" if result.written else "preview"
        print(f"  {sheet.name}: {len(result.renames)} label(s) [{state}]")
        for rename in result.renames:
            print(f"      {rename.old:<18} -> {rename.new}")
        for new, olds in result.collisions.items():
            print(f"      WARNING: {olds} all map to {new!r} (these labels will merge)")

    print(f"\nTotal conversions: {total}")
    if DRY_RUN:
        print("Set DRY_RUN = False to apply.")


# ----------------------------------------------------------------------
# Built-in self-test (no external files needed)
# ----------------------------------------------------------------------
def _label_block(kind: str, name: str, shape: str | None, uuid: str) -> str:
    """Emit one label block in canonical KiCad multi-line formatting."""
    lines = [f'\t({kind} "{name}"']
    if shape is not None:
        lines.append(f"\t\t(shape {shape})")
    lines += [
        "\t\t(at 10 10 0)",
        "\t\t(effects",
        "\t\t\t(font",
        "\t\t\t\t(size 1.27 1.27)",
        "\t\t\t)",
        "\t\t\t(justify left)",
        "\t\t)",
        f'\t\t(uuid "{uuid}")',
        "\t)",
    ]
    return "\n".join(lines)


def _make_synthetic_sheet() -> str:
    """A small sheet with 4 convertible labels + a bus + a misc label + a local."""
    blocks = [
        _label_block("label", "PVCC1_1", None, "0000-0001"),               # pre-existing local
        _label_block("hierarchical_label", "CS1_1", "input", "0000-0002"),
        _label_block("hierarchical_label", "CS1_2", "input", "0000-0003"),
        _label_block("hierarchical_label", "RE1_A-Channel", "input", "0000-0004"),
        _label_block("hierarchical_label", "SW1_B_1", "input", "0000-0005"),
        _label_block("hierarchical_label", "Chip1CurrentSource[1..16]", "output", "0000-0006"),
        _label_block("hierarchical_label", "USB{D+, D-}", "bidirectional", "0000-0007"),
    ]
    return (
        "(kicad_sch\n"
        "\t(version 20231120)\n"
        '\t(generator "eeschema")\n'
        '\t(uuid "00000000-0000-0000-0000-000000000000")\n'
        '\t(paper "A4")\n'
        "\t(lib_symbols)\n"
        + "\n".join(blocks)
        + "\n\t(sheet_instances\n\t\t(path \"/\"\n\t\t\t(page \"1\")\n\t\t)\n\t)\n"
        ")\n"
    )


def self_test() -> None:
    """Build a synthetic sheet, convert it, and assert the outcome."""
    import tempfile

    rules = compile_rules(TRANSFORMS)
    source = _make_synthetic_sheet()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "unit.kicad_sch"
        path.write_text(source, encoding="utf-8")
        result = convert_file(path, rules, dry_run=False, make_backup=False)
        output = path.read_text(encoding="utf-8")

    survey = survey_labels(output)
    expected_new = {
        "Chip1CurrentSource1", "Chip2CurrentSource1",
        "RotaryEncoder_AChannel1", "Chip1SinkSwitch1",
    }
    converted_old = {"CS1_1", "CS1_2", "RE1_A-Channel", "SW1_B_1"}

    assert len(result.renames) == 4, result.renames
    assert expected_new <= survey.local, f"missing new locals: {expected_new - survey.local}"
    assert not (expected_new & survey.local_with_shape), "a converted label kept its shape"
    assert not (converted_old & survey.hierarchical), "a source label survived"
    assert {"Chip1CurrentSource[1..16]", "USB{D+, D-}"} <= survey.hierarchical, \
        "a non-target hierarchical label was altered"
    assert "PVCC1_1" in survey.local, "the pre-existing local label was lost"

    # Minimal diff: exactly 4 headers retyped and 4 shape lines removed.
    assert output.count("(hierarchical_label") == source.count("(hierarchical_label") - 4
    assert output.count("(shape ") == source.count("(shape ") - 4

    print("self-test: PASS")
    print("  4 conversions, shapes dropped, bus + misc + local labels untouched")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        main()
