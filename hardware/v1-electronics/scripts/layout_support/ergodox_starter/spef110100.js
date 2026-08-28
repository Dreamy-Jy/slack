// ALPS SPEF110100 - push-on / push-off (latching) side-actuated switch,
// through-hole. Transcribed from the owner's SPEF110100.kicad_mod, which is
// in the old KiCad 5 "module" format; pads, the F.Fab body box and the
// F.CrtYd courtyard are 1:1. The original silk contained degenerate
// zero-length lines and 0.05 mm arcs at the plunger (vendor-converter
// leftovers); they are replaced by one clean silk circle marking the plunger
// at (2.15, 0). The plunger pokes out the footprint's +x side.
//
// Geometry (footprint frame, kicad): body x -10.6..-1.6, y -1.65..7.35;
// courtyard x -14.175..3.2, y -2.7..8.35; pads 1 (0,0), 2 (0,5.7),
// C1 (-12.2,0), C2 (-12.2,5.7); MH1-4 are mounting holes (no net).
//
// WIRING - NOT YET VERIFIED: the internal contact arrangement (which of
// 1/2/C1/C2 pair across the switch) was not checked against the datasheet.
// This module wires pads 1 and 2 as the switch:
//   from: pad 1 (e.g. the scan column)      to: pad 2 (e.g. the colrow)
// C1 and C2 are soldered but left off any net. Confirm on a real part
// before ordering boards.
module.exports = {
    params: {
        designator: 'PSW',
        from: undefined,
        to: undefined
    },
    body: p => `
    (footprint "SPEF110100"
        (layer "F.Cu")
        ${p.at /* parametric position */}
        (property "Value" "SPEF110100"
            (at -5.488 2.825 ${p.r})
            (unlocked yes)
            (layer "F.Fab")
            (uuid "a1f3b0e2-0001-4c58-9a2e-5be0d1c00001")
            (effects (font (size 1 1) (thickness 0.15)))
        )
        (property "Reference" "${p.ref}"
            (at -5.488 4.4 ${p.r})
            (unlocked yes)
            (layer "F.SilkS")
            (uuid "a1f3b0e2-0002-4c58-9a2e-5be0d1c00002")
            (effects (font (size 1 1) (thickness 0.1)))
        )
        (attr through_hole)
        (fp_line (start -10.6 7.35) (end -1.6 7.35) (stroke (width 0.2) (type default)) (layer "F.Fab") (uuid "a1f3b0e2-0003-4c58-9a2e-5be0d1c00003"))
        (fp_line (start -1.6 7.35) (end -1.6 -1.65) (stroke (width 0.2) (type default)) (layer "F.Fab") (uuid "a1f3b0e2-0004-4c58-9a2e-5be0d1c00004"))
        (fp_line (start -1.6 -1.65) (end -10.6 -1.65) (stroke (width 0.2) (type default)) (layer "F.Fab") (uuid "a1f3b0e2-0005-4c58-9a2e-5be0d1c00005"))
        (fp_line (start -10.6 -1.65) (end -10.6 7.35) (stroke (width 0.2) (type default)) (layer "F.Fab") (uuid "a1f3b0e2-0006-4c58-9a2e-5be0d1c00006"))
        (fp_line (start -14.175 -2.7) (end 3.2 -2.7) (stroke (width 0.1) (type default)) (layer "F.CrtYd") (uuid "a1f3b0e2-0007-4c58-9a2e-5be0d1c00007"))
        (fp_line (start 3.2 -2.7) (end 3.2 8.35) (stroke (width 0.1) (type default)) (layer "F.CrtYd") (uuid "a1f3b0e2-0008-4c58-9a2e-5be0d1c00008"))
        (fp_line (start 3.2 8.35) (end -14.175 8.35) (stroke (width 0.1) (type default)) (layer "F.CrtYd") (uuid "a1f3b0e2-0009-4c58-9a2e-5be0d1c00009"))
        (fp_line (start -14.175 8.35) (end -14.175 -2.7) (stroke (width 0.1) (type default)) (layer "F.CrtYd") (uuid "a1f3b0e2-000a-4c58-9a2e-5be0d1c0000a"))
        (fp_line (start -7.5 -1.65) (end -1.6 -1.65) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "a1f3b0e2-000b-4c58-9a2e-5be0d1c0000b"))
        (fp_line (start -1.6 -1.65) (end -1.6 1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "a1f3b0e2-000c-4c58-9a2e-5be0d1c0000c"))
        (fp_line (start -10.6 4.5) (end -10.6 7.35) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "a1f3b0e2-000d-4c58-9a2e-5be0d1c0000d"))
        (fp_line (start -10.6 7.35) (end -4.5 7.35) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "a1f3b0e2-000e-4c58-9a2e-5be0d1c0000e"))
        (fp_circle (center 2.15 0) (end 2.65 0) (stroke (width 0.15) (type default)) (fill no) (layer "F.SilkS") (uuid "a1f3b0e2-000f-4c58-9a2e-5be0d1c0000f"))
        (pad "1" thru_hole circle (at 0 0 ${p.r}) (size 1.95 1.95) (drill 1.3) (layers "*.Cu" "*.Mask") ${p.from.str} (uuid "a1f3b0e2-0010-4c58-9a2e-5be0d1c00010"))
        (pad "2" thru_hole circle (at 0 5.7 ${p.r}) (size 1.95 1.95) (drill 1.3) (layers "*.Cu" "*.Mask") ${p.to.str} (uuid "a1f3b0e2-0011-4c58-9a2e-5be0d1c00011"))
        (pad "C1" thru_hole circle (at -12.2 0 ${p.r}) (size 1.95 1.95) (drill 1.3) (layers "*.Cu" "*.Mask") (uuid "a1f3b0e2-0012-4c58-9a2e-5be0d1c00012"))
        (pad "C2" thru_hole circle (at -12.2 5.7 ${p.r}) (size 1.95 1.95) (drill 1.3) (layers "*.Cu" "*.Mask") (uuid "a1f3b0e2-0013-4c58-9a2e-5be0d1c00013"))
        (pad "MH1" thru_hole circle (at -9.1 -0.5 ${p.r}) (size 2.4 2.4) (drill 1.6) (layers "*.Cu" "*.Mask") (uuid "a1f3b0e2-0014-4c58-9a2e-5be0d1c00014"))
        (pad "MH2" thru_hole circle (at -11 2.85 ${p.r}) (size 2.25 2.25) (drill 1.5) (layers "*.Cu" "*.Mask") (uuid "a1f3b0e2-0015-4c58-9a2e-5be0d1c00015"))
        (pad "MH3" thru_hole circle (at -3.1 6.2 ${p.r}) (size 1.65 1.65) (drill 1.1) (layers "*.Cu" "*.Mask") (uuid "a1f3b0e2-0016-4c58-9a2e-5be0d1c00016"))
        (pad "MH4" thru_hole circle (at -1.2 2.85 ${p.r}) (size 2.25 2.25) (drill 1.5) (layers "*.Cu" "*.Mask") (uuid "a1f3b0e2-0017-4c58-9a2e-5be0d1c00017"))
        (model "SPEF110100.stp"
            (offset (xyz -0.24015747656034 -0.11102361941901 0.051574800896832))
            (scale (xyz 1 1 1))
            (rotate (xyz -90 0 -180))
        )
    )`
}