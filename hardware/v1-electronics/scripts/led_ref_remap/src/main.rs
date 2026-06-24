//! led_ref_remap
//! =============
//!
//! Rename the per-key RGBW LEDs in `led_matrix.kicad_sch` so that each LED's
//! reference matches the keyboard switch it drives (`SW42` -> `LED42`).
//!
//! The mapping
//! ----------
//! The board is a split keyboard whose two halves are lit by two IS31FL3733
//! matrix drivers (Chip 1 = LEFT half / columns 1-7, Chip 2 = RIGHT half /
//! columns 8-14). Each driver exposes 12 sink lines grouped into three blocks of
//! four (block0 = SW1-4, block1 = SW5-8, block2 = SW9-12); each RGBW LED uses one
//! current source `CS` (the common anode) plus the four sinks of one block (the
//! B/G/R/W cathodes). Walking that half's switches in keyboard row-major order
//! (index `i` = 0..41), the LED that lights switch `i` sits at:
//!
//! ```text
//!     block = i % 3            CS = i / 3 + 1
//! ```
//!
//! i.e. each current source lights three consecutive keys, one per sink-block.
//! The two switchless rotary encoders get no LED, and each chip has exactly one
//! spare LED (block0 / CS15) with no associated switch; those spares are listed
//! in [`SKIP_UNCHANGED`] and left alone. The full, reviewed result is the
//! [`RENAME`] table below; this program only applies that table.
//!
//! Why a token rewrite instead of the library's writer
//! --------------------------------------------------
//! A symbol's reference lives in two places in the sheet: the displayed
//! `(property "Reference" "<ref>" ...)` and the authoritative per-instance
//! `(instances ... (reference "<ref>") ...)`. `kiutils_kicad` 0.3.0 can rewrite
//! the property (`upsert_symbol_instance_property`) but has no setter for the
//! instance reference, and in KiCad 6+ the instance value wins -- so a
//! property-only edit would be silently reverted on load. Both occurrences are
//! the same quoted token `"<ref>"`, so the rename is applied as an exact
//! quoted-token rewrite (updating both, touching nothing else, two changed lines
//! per LED). `kiutils_kicad` is still used for what it is good at: a typed parse
//! that verifies the sheet matches the table before the edit, and that the
//! rewritten sheet still parses as valid KiCad afterwards.
//!
//! Run with `cargo run --release` (or `pixi run run`). See the CONFIG block.

use kiutils_kicad::SchematicFile;
use regex::Regex;
use std::collections::HashMap;
use std::error::Error;
use std::fs;

type Result<T> = std::result::Result<T, Box<dyn Error>>;

// ======================================================================
// CONFIG  --  edit me
// ======================================================================

/// The LED-matrix schematic to rewrite, in place. Relative to the working
/// directory, so run from the folder holding the sheet or give an absolute path.
const INPUT_PATH: &str = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/led_matrix.kicad_sch";

/// `true`  -> report what would change and write nothing.
/// `false` -> apply the edits in place.
const DRY_RUN: bool = false;

/// Write `"<file>.bak"` beside the sheet before overwriting it.
const MAKE_BACKUP: bool = true;

/// LEDs deliberately left unchanged: the one spare LED per chip (block0 / CS15)
/// that has no associated switch. Listing them here documents the intent and
/// stops the "uncovered LED" check from flagging them.
const SKIP_UNCHANGED: &[&str] = &["LED43_1", "LED43_2"];

/// The reviewed rename table: `(old_reference, new_reference)`.
///
/// Grouped by chip; within a chip the rows follow the switches in keyboard
/// row-major order. The trailing comment gives the switch each LED now matches
/// and the driver slot (block / CS) the LED occupies. New names keep the `LED`
/// designator on purpose -- all sheets share one KiCad project, so naming an LED
/// bare `SW1` would collide with the switch `SW1` and fail ERC; `LED<n>` carries
/// the switch number without the clash.
const RENAME: &[(&str, &str)] = &[
    // ---- Chip 1 (LEFT, cols 1-7); switches in keyboard row-major order ----
    ("LED1_1", "LED1"),       // SW1       (blk0 CS1)
    ("LED17_1", "LED2"),      // SW2       (blk1 CS1)
    ("LED33_1", "LED3"),      // SW3       (blk2 CS1)
    ("LED2_1", "LED4"),       // SW4       (blk0 CS2)
    ("LED18_1", "LED5"),      // SW5       (blk1 CS2)
    ("LED34_1", "LED6"),      // SW6       (blk2 CS2)
    ("LED3_1", "LED7"),       // RE1/SW7   (blk0 CS3)
    ("LED19_1", "LED15"),     // SW15      (blk1 CS3)
    ("LED35_1", "LED16"),     // SW16      (blk2 CS3)
    ("LED4_1", "LED17"),      // SW17      (blk0 CS4)
    ("LED20_1", "LED18"),     // SW18      (blk1 CS4)
    ("LED36_1", "LED19"),     // SW19      (blk2 CS4)
    ("LED5_1", "LED20"),      // SW20      (blk0 CS5)
    ("LED21_1", "LED21"),     // RE3/SW21  (blk1 CS5)
    ("LED37_1", "LED29"),     // SW29      (blk2 CS5)
    ("LED6_1", "LED30"),      // SW30      (blk0 CS6)
    ("LED22_1", "LED31"),     // SW31      (blk1 CS6)
    ("LED38_1", "LED32"),     // SW32      (blk2 CS6)
    ("LED7_1", "LED33"),      // SW33      (blk0 CS7)
    ("LED23_1", "LED34"),     // SW34      (blk1 CS7)
    ("LED39_1", "LED35"),     // RE5/SW35  (blk2 CS7)
    ("LED8_1", "LED43"),      // SW43      (blk0 CS8)
    ("LED24_1", "LED44"),     // SW44      (blk1 CS8)
    ("LED40_1", "LED45"),     // SW45      (blk2 CS8)
    ("LED9_1", "LED46"),      // SW46      (blk0 CS9)
    ("LED25_1", "LED47"),     // SW47      (blk1 CS9)
    ("LED41_1", "LED48"),     // SW48      (blk2 CS9)
    ("LED10_1", "LED49"),     // RE7/SW49  (blk0 CS10)
    ("LED26_1", "LED57"),     // SW57      (blk1 CS10)
    ("LED42_1", "LED58"),     // SW58      (blk2 CS10)
    ("LED11_1", "LED59"),     // SW59      (blk0 CS11)
    ("LED27_1", "LED60"),     // SW60      (blk1 CS11)
    ("LED16_1", "LED61"),     // SW61      (blk2 CS11)
    ("LED12_1", "LED62"),     // SW62      (blk0 CS12)
    ("LED28_1", "LED63"),     // SW63      (blk1 CS12)
    ("LED32_1", "LED73"),     // SW73      (blk2 CS12)
    ("LED13_1", "LED74"),     // SW74      (blk0 CS13)
    ("LED29_1", "LED75"),     // SW75      (blk1 CS13)
    ("LED15_1", "LED76"),     // SW76      (blk2 CS13)
    ("LED14_1", "LED77"),     // SW77      (blk0 CS14)
    ("LED30_1", "LED78"),     // SW78      (blk1 CS14)
    ("LED31_1", "LED79"),     // SW79      (blk2 CS14)
    // ---- Chip 2 (RIGHT, cols 8-14); switches in keyboard row-major order ----
    ("LED1_2", "LED8"),       // RE2/SW8   (blk0 CS1)
    ("LED17_2", "LED9"),      // SW9       (blk1 CS1)
    ("LED33_2", "LED10"),     // SW10      (blk2 CS1)
    ("LED2_2", "LED11"),      // SW11      (blk0 CS2)
    ("LED18_2", "LED12"),     // SW12      (blk1 CS2)
    ("LED34_2", "LED13"),     // SW13      (blk2 CS2)
    ("LED3_2", "LED14"),      // SW14      (blk0 CS3)
    ("LED19_2", "LED22"),     // RE4/SW22  (blk1 CS3)
    ("LED35_2", "LED23"),     // SW23      (blk2 CS3)
    ("LED4_2", "LED24"),      // SW24      (blk0 CS4)
    ("LED20_2", "LED25"),     // SW25      (blk1 CS4)
    ("LED36_2", "LED26"),     // SW26      (blk2 CS4)
    ("LED5_2", "LED27"),      // SW27      (blk0 CS5)
    ("LED21_2", "LED28"),     // SW28      (blk1 CS5)
    ("LED37_2", "LED36"),     // RE6/SW36  (blk2 CS5)
    ("LED6_2", "LED37"),      // SW37      (blk0 CS6)
    ("LED22_2", "LED38"),     // SW38      (blk1 CS6)
    ("LED38_2", "LED39"),     // SW39      (blk2 CS6)
    ("LED7_2", "LED40"),      // SW40      (blk0 CS7)
    ("LED23_2", "LED41"),     // SW41      (blk1 CS7)
    ("LED39_2", "LED42"),     // SW42      (blk2 CS7)
    ("LED8_2", "LED50"),      // RE8/SW50  (blk0 CS8)
    ("LED24_2", "LED51"),     // SW51      (blk1 CS8)
    ("LED40_2", "LED52"),     // SW52      (blk2 CS8)
    ("LED9_2", "LED53"),      // SW53      (blk0 CS9)
    ("LED25_2", "LED54"),     // SW54      (blk1 CS9)
    ("LED41_2", "LED55"),     // SW55      (blk2 CS9)
    ("LED10_2", "LED56"),     // SW56      (blk0 CS10)
    ("LED26_2", "LED66"),     // SW66      (blk1 CS10)
    ("LED42_2", "LED67"),     // SW67      (blk2 CS10)
    ("LED11_2", "LED68"),     // SW68      (blk0 CS11)
    ("LED27_2", "LED69"),     // SW69      (blk1 CS11)
    ("LED16_2", "LED70"),     // SW70      (blk2 CS11)
    ("LED12_2", "LED71"),     // SW71      (blk0 CS12)
    ("LED28_2", "LED72"),     // SW72      (blk1 CS12)
    ("LED32_2", "LED80"),     // SW80      (blk2 CS12)
    ("LED13_2", "LED81"),     // SW81      (blk0 CS13)
    ("LED29_2", "LED82"),     // SW82      (blk1 CS13)
    ("LED31_2", "LED83"),     // SW83      (blk2 CS13)
    ("LED14_2", "LED84"),     // SW84      (blk0 CS14)
    ("LED30_2", "LED85"),     // SW85      (blk1 CS14)
    ("LED15_2", "LED86"),     // SW86      (blk2 CS14)
];

// ======================================================================
// Implementation
// ======================================================================

/// Each reference appears twice in the sheet: the `(property "Reference" ...)`
/// and the per-instance `(... (reference ...))`.
const EXPECTED_OCCURRENCES: usize = 2;

/// Matches a quoted *old-form* LED reference token, e.g. `"LED43_1"`. The new
/// names (`LED29`) deliberately do not match this form.
const OLD_TOKEN_PATTERN: &str = r#""(LED\d+_\d+)""#;

fn main() -> Result<()> {
    run(INPUT_PATH, DRY_RUN, MAKE_BACKUP)
}

/// Read the sheet, verify it matches the table, rewrite the references, and
/// (unless `dry_run`) write the result back, re-parsing it to confirm validity.
fn run(input_path: &str, dry_run: bool, make_backup: bool) -> Result<()> {
    let map = build_map(RENAME)?;

    // ---- parse with kiutils and verify the sheet matches the table ----
    let doc = SchematicFile::read(input_path)?;
    let present: Vec<String> = doc
        .ast()
        .symbols
        .iter()
        .filter_map(|s| s.reference.clone())
        .collect();
    verify_sheet_matches_table(&present, &map, SKIP_UNCHANGED)?;

    // ---- apply the rename as an exact quoted-token rewrite ----
    let src = fs::read_to_string(input_path)?;
    let out = rewrite_references(&src, &map)?;
    verify_rewrite(&out, &map)?;

    println!("{input_path}: {} LED references to rename.", map.len());
    for &(old, new) in RENAME.iter().take(3) {
        println!("    {old:>9}  ->  {new}");
    }
    println!("    ... ({} more)", map.len().saturating_sub(3));
    println!("    spares left unchanged: {}", SKIP_UNCHANGED.join(", "));

    if dry_run {
        println!("DRY_RUN is true: nothing written. Set DRY_RUN = false to apply.");
        return Ok(());
    }

    if make_backup {
        let backup = format!("{input_path}.bak");
        fs::write(&backup, &src)?;
        println!("    backup written to {backup}");
    }
    fs::write(input_path, &out)?;

    // ---- re-parse the written sheet with kiutils as a final sanity check ----
    let after = SchematicFile::read(input_path)?;
    confirm_new_references(&after, &map)?;
    println!("    {input_path} updated and re-validated.");
    Ok(())
}

/// Build the lookup table, rejecting a duplicate `old` (ambiguous source) or a
/// duplicate `new` (two LEDs would collapse to one reference -- invalid).
fn build_map(pairs: &[(&'static str, &'static str)]) -> Result<HashMap<&'static str, &'static str>> {
    let mut map = HashMap::with_capacity(pairs.len());
    let mut targets: HashMap<&str, &str> = HashMap::with_capacity(pairs.len());
    for &(old, new) in pairs {
        if map.insert(old, new).is_some() {
            return Err(format!("rename table lists {old:?} more than once").into());
        }
        if let Some(prev) = targets.insert(new, old) {
            return Err(format!("rename table maps both {prev:?} and {old:?} to {new:?}").into());
        }
    }
    Ok(map)
}

/// Confirm the parsed sheet is exactly the one the table was built for:
/// every `old` is present, no `new` already exists, and every old-form LED
/// reference is either in the table or an acknowledged spare.
fn verify_sheet_matches_table(
    present: &[String],
    map: &HashMap<&str, &str>,
    skip: &[&str],
) -> Result<()> {
    let count = |needle: &str| present.iter().filter(|r| r.as_str() == needle).count();

    for (&old, &new) in map {
        match count(old) {
            1 => {}
            0 => return Err(format!("expected LED {old:?} not found -- wrong or already-renamed sheet").into()),
            n => return Err(format!("LED {old:?} appears {n} times; references must be unique").into()),
        }
        if count(new) != 0 {
            return Err(format!("target name {new:?} already exists in the sheet").into());
        }
    }

    let old_form = Regex::new(r"^LED\d+_\d+$")?;
    for reference in present {
        if old_form.is_match(reference)
            && !map.contains_key(reference.as_str())
            && !skip.contains(&reference.as_str())
        {
            return Err(format!("LED {reference:?} is not covered by the rename table or the spare list").into());
        }
    }
    Ok(())
}

/// Replace every quoted old-form token with its mapped new name in one pass.
/// Tokens not in the map (the spares) are left exactly as they are.
fn rewrite_references(src: &str, map: &HashMap<&str, &str>) -> Result<String> {
    let re = Regex::new(OLD_TOKEN_PATTERN)?;
    let out = re.replace_all(src, |caps: &regex::Captures| match map.get(&caps[1]) {
        Some(new) => format!("\"{new}\""),
        None => caps[0].to_string(),
    });
    Ok(out.into_owned())
}

/// Text-level post-check: every new name now appears the expected number of
/// times and no renamed old token survives.
fn verify_rewrite(out: &str, map: &HashMap<&str, &str>) -> Result<()> {
    let count = |token: &str| out.matches(&format!("\"{token}\"")).count();
    for (&old, &new) in map {
        if count(new) != EXPECTED_OCCURRENCES {
            return Err(format!("after rewrite, {new:?} appears {} times (expected {EXPECTED_OCCURRENCES})", count(new)).into());
        }
        if count(old) != 0 {
            return Err(format!("after rewrite, old reference {old:?} still present").into());
        }
    }
    Ok(())
}

/// Library-level post-check: re-parse the written sheet and confirm every new
/// reference is present and no renamed old reference remains.
fn confirm_new_references(doc: &kiutils_kicad::SchematicDocument, map: &HashMap<&str, &str>) -> Result<()> {
    let present: Vec<&str> = doc
        .ast()
        .symbols
        .iter()
        .filter_map(|s| s.reference.as_deref())
        .collect();
    for (&old, &new) in map {
        if !present.contains(&new) {
            return Err(format!("re-parse: expected new reference {new:?} missing").into());
        }
        if present.contains(&old) {
            return Err(format!("re-parse: old reference {old:?} still present").into());
        }
    }
    Ok(())
}

// ======================================================================
// Tests
// ======================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// A minimal stand-in for a symbol: the reference appears in the property
    /// and again in the instance block, exactly as in a real sheet.
    fn symbol(reference: &str) -> String {
        format!(
            "(symbol (lib_id \"LED:RGBW\")\n  \
               (property \"Reference\" \"{reference}\" (at 0 0 0))\n  \
               (instances (project \"slack\" (path \"/p\" (reference \"{reference}\") (unit 1))))\n)\n"
        )
    }

    #[test]
    fn real_table_is_a_clean_bijection() {
        let map = build_map(RENAME).expect("RENAME must be valid");
        assert_eq!(map.len(), RENAME.len());
        let news: std::collections::HashSet<&str> = RENAME.iter().map(|&(_, n)| n).collect();
        assert_eq!(news.len(), RENAME.len(), "new names must be unique");
        let olds: std::collections::HashSet<&str> = RENAME.iter().map(|&(o, _)| o).collect();
        assert!(news.is_disjoint(&olds), "new names must not collide with old names");
        // The spares must not be renamed by the table.
        for spare in SKIP_UNCHANGED {
            assert!(!map.contains_key(spare), "spare {spare} must not be in RENAME");
        }
    }

    #[test]
    fn build_map_rejects_duplicate_old() {
        assert!(build_map(&[("LED1_1", "LEDA"), ("LED1_1", "LEDB")]).is_err());
    }

    #[test]
    fn build_map_rejects_duplicate_new() {
        assert!(build_map(&[("LED1_1", "LEDX"), ("LED2_1", "LEDX")]).is_err());
    }

    #[test]
    fn rewrite_changes_both_occurrences_and_skips_spares() {
        let map = build_map(&[("LED1_1", "LED1"), ("LED2_1", "LED4")]).unwrap();
        let src = format!("{}{}{}", symbol("LED1_1"), symbol("LED2_1"), symbol("LED43_1"));
        let out = rewrite_references(&src, &map).unwrap();
        verify_rewrite(&out, &map).unwrap();
        assert_eq!(out.matches("\"LED1\"").count(), 2);
        assert_eq!(out.matches("\"LED4\"").count(), 2);
        assert_eq!(out.matches("\"LED1_1\"").count(), 0);
        assert_eq!(out.matches("\"LED43_1\"").count(), 2, "spare must be untouched");
    }

    #[test]
    fn rewrite_has_no_substring_bleed() {
        // "LED1_1" -> "LED1" must not corrupt the unrelated "LED15_1" token.
        let map = build_map(&[("LED1_1", "LED1"), ("LED15_1", "LED76")]).unwrap();
        let src = format!("{}{}", symbol("LED1_1"), symbol("LED15_1"));
        let out = rewrite_references(&src, &map).unwrap();
        verify_rewrite(&out, &map).unwrap();
        assert_eq!(out.matches("\"LED15_1\"").count(), 0);
        assert_eq!(out.matches("\"LED76\"").count(), 2);
    }

    #[test]
    fn verify_sheet_rejects_missing_reference() {
        let map = build_map(&[("LED1_1", "LED1")]).unwrap();
        let present = vec!["LED2_1".to_string()]; // LED1_1 absent
        assert!(verify_sheet_matches_table(&present, &map, &[]).is_err());
    }

    #[test]
    fn verify_sheet_rejects_preexisting_target() {
        let map = build_map(&[("LED1_1", "LED1")]).unwrap();
        let present = vec!["LED1_1".to_string(), "LED1".to_string()]; // target already used
        assert!(verify_sheet_matches_table(&present, &map, &[]).is_err());
    }

    #[test]
    fn verify_sheet_rejects_uncovered_led() {
        let map = build_map(&[("LED1_1", "LED1")]).unwrap();
        let present = vec!["LED1_1".to_string(), "LED9_9".to_string()]; // LED9_9 not covered
        assert!(verify_sheet_matches_table(&present, &map, &[]).is_err());
    }

    #[test]
    fn verify_sheet_allows_listed_spare() {
        let map = build_map(&[("LED1_1", "LED1")]).unwrap();
        let present = vec!["LED1_1".to_string(), "LED43_1".to_string()];
        assert!(verify_sheet_matches_table(&present, &map, &["LED43_1"]).is_ok());
    }
}