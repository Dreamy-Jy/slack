//! script to transfer my actual components to a generated layout I've pasted in my pcb file.
//! 
//! # Plan:
//! 1. create a transfer map generate footprint -> actual components
//! 2. for all generated footprints:
//!     a. place there real footprint over them in the same orientation
//!     b. lock the real foot print.
//!     c. delete the generate footprint.
//! 3. save the edits
//! 
//! This script failed

use kiutils_rs::{self, PcbFile, PcbFootprint};
use std::collections::HashMap;


const TARGET_PCB: &str = "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-electronics/slack.kicad_pcb";

fn main() {
    // generated ref -> real ref (generated = footprint with no schematic path)
    let transfer_map: HashMap<&str, &str> = HashMap::from([
        // --- key switches
        ("S4", "SW1"), ("D4", "D1"), ("LED4", "LED1"), // row1 col1
        ("S8", "SW2"), ("D8", "D2"), ("LED8", "LED2"), // row1 col2
        ("S12", "SW3"), ("D12", "D3"), ("LED12", "LED3"), // row1 col3
        ("S16", "SW4"), ("D16", "D4"), ("LED16", "LED4"), // row1 col4
        ("S20", "SW5"), ("D20", "D5"), ("LED20", "LED5"), // row1 col5
        ("S24", "SW6"), ("D24", "D6"), ("LED24", "LED6"), // row1 col6
        ("S53", "SW9"), ("D53", "D9"), ("LED53", "LED9"), // row1 col9
        ("S49", "SW10"), ("D49", "D10"), ("LED49", "LED10"), // row1 col10
        ("S45", "SW11"), ("D45", "D11"), ("LED45", "LED11"), // row1 col11
        ("S41", "SW12"), ("D41", "D12"), ("LED41", "LED12"), // row1 col12
        ("S37", "SW13"), ("D37", "D13"), ("LED37", "LED13"), // row1 col13
        ("S33", "SW14"), ("D33", "D14"), ("LED33", "LED14"), // row1 col14
        ("S3", "SW15"), ("D3", "D15"), ("LED3", "LED15"), // row2 col1
        ("S7", "SW16"), ("D7", "D16"), ("LED7", "LED16"), // row2 col2
        ("S11", "SW17"), ("D11", "D17"), ("LED11", "LED17"), // row2 col3
        ("S15", "SW18"), ("D15", "D18"), ("LED15", "LED18"), // row2 col4
        ("S19", "SW19"), ("D19", "D19"), ("LED19", "LED19"), // row2 col5
        ("S23", "SW20"), ("D23", "D20"), ("LED23", "LED20"), // row2 col6
        ("S52", "SW23"), ("D52", "D23"), ("LED52", "LED23"), // row2 col9
        ("S48", "SW24"), ("D48", "D24"), ("LED48", "LED24"), // row2 col10
        ("S44", "SW25"), ("D44", "D25"), ("LED44", "LED25"), // row2 col11
        ("S40", "SW26"), ("D40", "D26"), ("LED40", "LED26"), // row2 col12
        ("S36", "SW27"), ("D36", "D27"), ("LED36", "LED27"), // row2 col13
        ("S32", "SW28"), ("D32", "D28"), ("LED32", "LED28"), // row2 col14
        ("S2", "SW29"), ("D2", "D29"), ("LED2", "LED29"), // row3 col1
        ("S6", "SW30"), ("D6", "D30"), ("LED6", "LED30"), // row3 col2
        ("S10", "SW31"), ("D10", "D31"), ("LED10", "LED31"), // row3 col3
        ("S14", "SW32"), ("D14", "D32"), ("LED14", "LED32"), // row3 col4
        ("S18", "SW33"), ("D18", "D33"), ("LED18", "LED33"), // row3 col5
        ("S22", "SW34"), ("D22", "D34"), ("LED22", "LED34"), // row3 col6
        ("S51", "SW37"), ("D51", "D37"), ("LED51", "LED37"), // row3 col9
        ("S47", "SW38"), ("D47", "D38"), ("LED47", "LED38"), // row3 col10
        ("S43", "SW39"), ("D43", "D39"), ("LED43", "LED39"), // row3 col11
        ("S39", "SW40"), ("D39", "D40"), ("LED39", "LED40"), // row3 col12
        ("S35", "SW41"), ("D35", "D41"), ("LED35", "LED41"), // row3 col13
        ("S31", "SW42"), ("D31", "D42"), ("LED31", "LED42"), // row3 col14
        ("S1", "SW43"), ("D1", "D43"), ("LED1", "LED43"), // row4 col1
        ("S5", "SW44"), ("D5", "D44"), ("LED5", "LED44"), // row4 col2
        ("S9", "SW45"), ("D9", "D45"), ("LED9", "LED45"), // row4 col3
        ("S13", "SW46"), ("D13", "D46"), ("LED13", "LED46"), // row4 col4
        ("S17", "SW47"), ("D17", "D47"), ("LED17", "LED47"), // row4 col5
        ("S21", "SW48"), ("D21", "D48"), ("LED21", "LED48"), // row4 col6
        ("S50", "SW51"), ("D50", "D51"), ("LED50", "LED51"), // row4 col9
        ("S46", "SW52"), ("D46", "D52"), ("LED46", "LED52"), // row4 col10
        ("S42", "SW53"), ("D42", "D53"), ("LED42", "LED53"), // row4 col11
        ("S38", "SW54"), ("D38", "D54"), ("LED38", "LED54"), // row4 col12
        ("S34", "SW55"), ("D34", "D55"), ("LED34", "LED55"), // row4 col13
        ("S30", "SW56"), ("D30", "D56"), ("LED30", "LED56"), // row4 col14
        ("S25", "SW57"), ("D25", "D57"), ("LED25", "LED57"), // row5 col2
        ("S26", "SW58"), ("D26", "D58"), ("LED26", "LED58"), // row5 col3
        ("S27", "SW59"), ("D27", "D59"), ("LED27", "LED59"), // row5 col4
        ("S28", "SW60"), ("D28", "D60"), ("LED28", "LED60"), // row5 col5
        ("S29", "SW61"), ("D29", "D61"), ("LED29", "LED61"), // row5 col6
        ("S58", "SW64"), ("D58", "D64"), ("LED58", "LED64"), // row5 col9
        ("S57", "SW65"), ("D57", "D65"), ("LED57", "LED65"), // row5 col10
        ("S56", "SW66"), ("D56", "D66"), ("LED56", "LED66"), // row5 col11
        ("S55", "SW67"), ("D55", "D67"), ("LED55", "LED67"), // row5 col12
        ("S54", "SW68"), ("D54", "D68"), ("LED54", "LED68"), // row5 col13
        // --- encoders (Col7 left = ENC1-4, Col8 right = ENC5-8, row 1 = top)
        ("ENC4", "RE1/SW7"), ("D64", "D7"), ("LED62", "LED7"), // row1 col7
        ("ENC8", "RE2/SW8"), ("D68", "D8"), ("LED66", "LED8"), // row1 col8
        ("ENC3", "RE3/SW21"), ("D63", "D21"), ("LED61", "LED21"), // row2 col7
        ("ENC7", "RE4/SW22"), ("D67", "D22"), ("LED65", "LED22"), // row2 col8
        ("ENC2", "RE5/SW35"), ("D62", "D35"), ("LED60", "LED35"), // row3 col7
        ("ENC6", "RE6/SW36"), ("D66", "D36"), ("LED64", "LED36"), // row3 col8
        ("ENC1", "RE7/SW49"), ("D61", "D49"), ("LED59", "LED49"), // row4 col7
        ("ENC5", "RE8/SW50"), ("D65", "D50"), ("LED63", "LED50"), // row4 col8
        // --- scroll-bar click buttons; scroll-bar LEDs ride along
        ("SCLK1", "SW62"), ("D59", "D62"), ("LED67", "LED62"), // row5 col7
        ("SCLK2", "SW63"), ("D60", "D63"), ("LED68", "LED63"), // row5 col8
        // --- scroll-bar encoders
        ("SCRL1", "RE9"),
        ("SCRL2", "RE10"),
        // --- latches
        ("LSW1", "SW69"), ("D69", "D69"), ("LED69", "LED69"), // row6 col1
        ("LSW2", "SW70"), ("D70", "D70"), ("LED70", "LED70"), // row6 col2
        ("LSW3", "SW71"), ("D71", "D71"), ("LED71", "LED71"), // row6 col3
        ("LSW4", "SW72"), ("D72", "D72"), ("LED72", "LED72"), // row6 col4
        ("LSW5", "SW73"), ("D73", "D73"), ("LED73", "LED73"), // row6 col5
        ("LSW10", "SW78"), ("D78", "D78"), ("LED78", "LED78"), // row6 col10
        ("LSW9", "SW79"), ("D77", "D79"), ("LED77", "LED79"), // row6 col11
        ("LSW8", "SW80"), ("D76", "D80"), ("LED76", "LED80"), // row6 col12
        ("LSW7", "SW81"), ("D75", "D81"), ("LED75", "LED81"), // row6 col13
        ("LSW6", "SW82"), ("D74", "D82"), ("LED74", "LED82"), // row6 col14
        // --- push latches
        ("PSW1", "SW74"), ("D79", "D74"), ("LED79", "LED74"), // row6 col6
        ("PSW2", "SW75"), ("D80", "D75"), ("LED80", "LED75"), // row6 col7
        ("PSW4", "SW76"), ("D82", "D76"), ("LED82", "LED76"), // row6 col8
        ("PSW3", "SW77"), ("D81", "D77"), ("LED81", "LED77"), // row6 col9
    ]);

    let mut pcb = PcbFile::read(TARGET_PCB).unwrap();

    let mut pcb_ast = pcb.ast_mut();

    let mut deleted_fp:Vec<PcbFootprint>  = Vec::with_capacity(transfer_map.keys().len());

    for fp in &mut pcb_ast.footprints {
        match transfer_map.get(&fp.reference.as_ref().unwrap() as &str) { // why do I need to do this cast?
            Some(pcb_ref) => {
            },
            None => continue
        }
        println!("Footprint Reference: {}", fp.reference.as_ref().unwrap());
    }
}