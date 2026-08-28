//! Remove the outer keys of the thumb cluster on each side, maybe if they haven't been already removed.
//! Modify the rest of the matrix to account for this change.
//!
//! This is a failed experiement. kiutils_kicad has not api for easy symbol removal that I could find.
use kiutils_kicad::SchematicFile;
use regex::Regex;

const TARGET_SCHEMATIC: &str = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/switch_matrix.kicad_sch";

const TARGET_REFERENCES: [u8; 2] = [57, 72];

fn main() {
    let mut doc = SchematicFile::read(TARGET_SCHEMATIC).unwrap();

    println!("symbol_count: {}", doc.ast().symbol_count);

    let symbols = doc.symbol_instances();

    let regex_pattern = Regex::new(r"(^SW\d+$)|(^D\d+$)").unwrap();
    // previous pattern r"(SW\d+)|(D\d+)|(RE\d+/SW\d+)"

    // remove unwanted notes
    doc.symbol_instances()
        .retain_mut(|symbol| match symbol.reference {
            Some(ref reference) => match regex_pattern.is_match(&reference) {
                true => {
                    let ref_digits: String =
                        reference.chars().filter(|c| c.is_ascii_digit()).collect();
                    let ref_number: u32 = ref_digits.parse().unwrap();

                    if ref_number == 57 || ref_number == 72 {
                        println!("removed {}", reference);
                        return false;
                    }

                    return true;
                }
                false => return true,
            },
            None => return true,
        });

    println!("starting check");
    for symbol in doc.symbol_instances() {
        match symbol.reference {
            Some(r#ref) => {
                if regex_pattern.is_match(&r#ref) {
                    let ref_digits: String = r#ref.chars().filter(|c| c.is_ascii_digit()).collect();
                    let ref_number: u32 = ref_digits.parse().unwrap();

                    if ref_number == 57 {
                        // delete this node and it's connected wires
                        println!("this node will be deleted: {}", r#ref);
                    } else if ref_number > 57 && ref_number < 72 {
                        // decrease the reference number by one
                        // println!("this node will be decreased by one {}", r#ref);
                    } else if ref_number == 72 {
                        // delete this node
                        println!("this node will be deleted: {}", r#ref);
                    } else if ref_number > 72 {
                        // decrease the reference number by two
                        // println!("this node will be decreased by two {}", r#ref);
                    }
                }
            }
            None => continue,
        }
    }

    // guard against bad state
    // check if the thumb buttons have already been removed

    // remove the respective switches and diodes

    // adjust the rest of the matrix for the change
}
