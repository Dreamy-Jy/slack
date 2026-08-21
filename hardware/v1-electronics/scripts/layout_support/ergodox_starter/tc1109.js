// XKB Connection TC-1109-C-E - 4-pin tact switch, 4.5 mm actuator, used as
// the click under each thumb scroll bar.
// 1:1 transcription of the owner's TC-1109-C-E.kicad_mod (KiCad 10 export),
// with only the board-level bookkeeping removed to match the kicad8 template:
// the (version/generator) header, the KiCad-10-only tokens
// (duplicate_pad_numbers_are_jumpers, embedded_fonts), and the two
// documentation-only (dimension ...) annotations on User.1 (the 3 mm / 5 mm
// pad-pitch callouts), which KiCad 8 does not accept inside a footprint.
// Pads, silk, the Margin body rect and the 3D model are verbatim.
//
// WIRING - NOT YET VERIFIED: the datasheet drawing does not show which pin
// pairs are internally common (1-2 / 3-4 rows, or 1-3 / 2-4 columns). This
// footprint therefore wires only the DIAGONAL pads 1 and 4 - that pairing is
// always across the contact whichever way the bridging goes, so it can never
// short the switch closed. Pads 2 and 3 are soldered but left off any net.
// Confirm the internal pairing on a real part before ordering boards.
//
// Nets
//   from: pad 1 (the click signal, e.g. {{name}}_SW)
//   to:   pad 4 (normally GND)

module.exports = {
    params: {
        designator: 'SCLK',
        from: undefined,
        to: undefined
    },
    body: p => `
    (footprint "TC-1109-C-E"
        (layer "F.Cu")
        ${p.at /* parametric position */}
        (property "Value" "TC-1109-C-E"
            (at 0 4.5 ${p.r})
            (unlocked yes)
            (layer "F.Fab")
            (uuid "297bbb22-ccce-49a4-96c9-245f98a317db")
            (effects
                (font
                    (size 1 1)
                    (thickness 0.15)
                )
            )
        )
        (property "Datasheet" ""
            (at 0 0 ${p.r})
            (unlocked yes)
            (layer "F.Fab")
            (hide yes)
            (uuid "5bcf6f90-2ba4-4379-9ba8-c184d4dae37b")
            (effects
                (font
                    (size 1 1)
                    (thickness 0.15)
                )
            )
        )
        (property "Description" ""
            (at 0 0 ${p.r})
            (unlocked yes)
            (layer "F.Fab")
            (hide yes)
            (uuid "8e600a79-077f-4451-8d39-ca4ab9046fb6")
            (effects
                (font
                    (size 1 1)
                    (thickness 0.15)
                )
            )
        )
        (property "Reference" "${p.ref}"
            (at 0 -4 ${p.r})
            (unlocked yes)
            (layer "F.SilkS")
            ${p.ref_hide ? '(hide yes)' : ''}
            (uuid "24e77b72-50f8-4c39-8d21-364591d27e5b")
            (effects
                (font
                    (size 1 1)
                    (thickness 0.1)
                )
            )
        )
        (attr smd)
        (fp_line
            (start -4 -2.5)
            (end -2 -2.5)
            (stroke
                (width 0.1)
                (type default)
            )
            (layer "F.SilkS")
            (uuid "ba0b1140-ace9-4053-b4eb-91db3b612cfb")
        )
        (fp_line
            (start -3.5 -1)
            (end -3.5 -3)
            (stroke
                (width 0.1)
                (type default)
            )
            (layer "F.SilkS")
            (uuid "2e7b1bd8-9ddd-4bdc-91f8-f4c55f371671")
        )
        (fp_line
            (start 3.5 1)
            (end 3.5 3)
            (stroke
                (width 0.1)
                (type default)
            )
            (layer "F.SilkS")
            (uuid "d7ce6544-86ac-4ed1-bc61-f226baf1be5a")
        )
        (fp_line
            (start 4 2.5)
            (end 2 2.5)
            (stroke
                (width 0.1)
                (type default)
            )
            (layer "F.SilkS")
            (uuid "72dd6f82-63ed-4e94-b6e3-8bc0288a4b68")
        )
        (fp_rect
            (start -3.5 -2.5)
            (end 3.5 2.5)
            (stroke
                (width 0.1)
                (type default)
            )
            (fill no)
            (layer "Margin")
            (uuid "dfa61a00-84cf-4cb5-8099-8148d9a3a573")
        )
        (fp_text user "\${REFERENCE}"
            (at 0 6 ${p.r})
            (unlocked yes)
            (layer "F.Fab")
            (uuid "4fddf0f2-e2f4-4c88-ad24-4783cf0d7eac")
            (effects
                (font
                    (size 1 1)
                    (thickness 0.15)
                )
            )
        )
        (pad "1" thru_hole roundrect
            (at -2.5 -1.5 ${p.r})
            (size 1.27 1.27)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (roundrect_rratio 0.15)
            (uuid "493069b2-d654-43c4-9597-7a52b0ff2c8d")
            ${p.from}
        )
        (pad "2" thru_hole roundrect
            (at 2.5 -1.5 ${p.r})
            (size 1.27 1.27)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (roundrect_rratio 0.15)
            (uuid "9ecaf4e2-31bd-4fbf-8271-8e42a682c046")
        )
        (pad "3" thru_hole roundrect
            (at -2.5 1.5 ${p.r})
            (size 1.27 1.27)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (roundrect_rratio 0.15)
            (uuid "1d8b1171-f471-420b-a8db-efb111063de5")
        )
        (pad "4" thru_hole roundrect
            (at 2.5 1.5 ${p.r})
            (size 1.27 1.27)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (roundrect_rratio 0.15)
            (uuid "c6a88325-c78f-4099-9eda-195fe8087387")
            ${p.to}
        )
        (model "\${KIPRJMOD}/XKB Connection/tc-1109-c-e.stp"
            (offset
                (xyz 0 0 0.1)
            )
            (scale
                (xyz 1 1 1)
            )
            (rotate
                (xyz -90 -0 -0)
            )
        )
    )
    `
}