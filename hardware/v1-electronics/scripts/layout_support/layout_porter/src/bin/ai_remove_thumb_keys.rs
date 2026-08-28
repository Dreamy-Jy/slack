//! Remove the outer keys of the thumb cluster on each side (SW57/D57 and SW72/D72),
//! then renumber the remaining switches/diodes so the matrix stays contiguous.
//!
//! Why this doesn't use SchematicDocument for the edits: kiutils_kicad 0.3.0 has no
//! API for deleting symbols, and `symbol_instances()` returns an owned Vec — calling
//! `.retain()` on it filters a temporary that is dropped immediately (the original bug).
//! So we edit the s-expression tree directly with kiutils_sexpr, whose CST fields are
//! public and mutable.
//!
//! Cargo.toml needs:
//!   kiutils_sexpr = "0.1.1"
//!   regex = "1"

use kiutils_sexpr::{Atom, Node, parse_one};
use regex::Regex;
use std::fs;

const TARGET_SCHEMATIC: &str = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/switch_matrix.kicad_sch";

const TARGET_REFERENCES: [u32; 2] = [57, 72];

fn main() {
    let src = fs::read_to_string(TARGET_SCHEMATIC).expect("could not read schematic");
    let mut cst = parse_one(&src).expect("could not parse schematic");

    // ^(SW|D)(digits)$ — capture the prefix and number separately so "RE1/SW57"-style
    // refs can't sneak wrong digits in.
    let ref_pattern = Regex::new(r"^(SW|D)(\d+)$").unwrap();

    let Some(Node::List { items, .. }) = cst.nodes.first_mut() else {
        panic!("unexpected file structure: no root list");
    };

    // ---- guard against bad state: bail if the targets are already gone ----
    let existing: Vec<u32> = items
        .iter()
        .filter(|n| head_of(n) == Some("symbol"))
        .filter_map(|n| reference_of(n))
        .filter_map(|r| parse_ref(&ref_pattern, &r))
        .map(|(_, num)| num)
        .collect();

    if !TARGET_REFERENCES.iter().all(|t| existing.contains(t)) {
        println!("thumb keys already removed (SW57/SW72 not found) — nothing to do");
        return;
    }

    // ---- pass 1: remove the target symbols ----
    let before = items.len();
    items.retain(|node| {
        if head_of(node) != Some("symbol") {
            return true;
        }
        let Some(reference) = reference_of(node) else {
            return true;
        };
        let Some((_, num)) = parse_ref(&ref_pattern, &reference) else {
            return true;
        };
        if TARGET_REFERENCES.contains(&num) {
            println!("removed {}", reference);
            false
        } else {
            true
        }
    });
    println!("removed {} symbols", before - items.len());

    // ---- pass 2: renumber everything above the gaps ----
    // 58..=71 -> minus one, 73.. -> minus two. Ascending order means the slot we
    // rename into is always already free.
    for node in items.iter_mut() {
        if head_of(node) != Some("symbol") {
            continue;
        }
        let Some(reference) = reference_of(node) else {
            continue;
        };
        let Some((prefix, num)) = parse_ref(&ref_pattern, &reference) else {
            continue;
        };

        let new_num = match num {
            58..=71 => num - 1,
            73.. => num - 2,
            _ => continue,
        };

        let new_reference = format!("{}{}", prefix, new_num);
        rename_in_subtree(node, &reference, &new_reference);
        println!("renamed {} -> {}", reference, new_reference);
    }

    // Canonical write: our edits live in the node tree, and to_lossless_string()
    // just returns the untouched original text. KiCad reformats on save anyway.
    fs::write(TARGET_SCHEMATIC, cst.to_canonical_string()).expect("could not write schematic");
    println!("saved {}", TARGET_SCHEMATIC);

    // Not handled here: wires that connected to the removed switches are still in
    // the file and will dangle. Open the schematic and run ERC to find and delete
    // them, or extend this to match wire endpoints against the removed symbol
    // positions.
}

/// First atom of a list node, e.g. "symbol" for (symbol ...).
fn head_of(node: &Node) -> Option<&str> {
    let Node::List { items, .. } = node else {
        return None;
    };
    match items.first() {
        Some(Node::Atom {
            atom: Atom::Symbol(s),
            ..
        }) => Some(s),
        _ => None,
    }
}

/// Value of the (property "Reference" "...") child of a symbol node.
fn reference_of(node: &Node) -> Option<String> {
    let Node::List { items, .. } = node else {
        return None;
    };
    items.iter().skip(1).find_map(|child| {
        let Node::List {
            items: prop_items, ..
        } = child
        else {
            return None;
        };
        if head_of(child) != Some("property") {
            return None;
        }
        let key = atom_string(prop_items.get(1)?)?;
        if key != "Reference" {
            return None;
        }
        atom_string(prop_items.get(2)?)
    })
}

fn atom_string(node: &Node) -> Option<String> {
    match node {
        Node::Atom {
            atom: Atom::Quoted(s),
            ..
        }
        | Node::Atom {
            atom: Atom::Symbol(s),
            ..
        } => Some(s.clone()),
        _ => None,
    }
}

/// Split "SW57" into ("SW", 57). None if it doesn't match the pattern.
fn parse_ref(pattern: &Regex, reference: &str) -> Option<(String, u32)> {
    let caps = pattern.captures(reference)?;
    let prefix = caps.get(1)?.as_str().to_string();
    let num = caps.get(2)?.as_str().parse().ok()?;
    Some((prefix, num))
}

/// Replace every quoted string equal to `old` anywhere inside this symbol's subtree.
/// This catches both the Reference property and the reference inside the symbol's
/// embedded (instances ...) block, which KiCad also keeps in sync.
fn rename_in_subtree(node: &mut Node, old: &str, new: &str) {
    match node {
        Node::Atom {
            atom: Atom::Quoted(s),
            ..
        } if s == old => *s = new.to_string(),
        Node::Atom { .. } => {}
        Node::List { items, .. } => {
            for child in items.iter_mut() {
                rename_in_subtree(child, old, new);
            }
        }
    }
}
