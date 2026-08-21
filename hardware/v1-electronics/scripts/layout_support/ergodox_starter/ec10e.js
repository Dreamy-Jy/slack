// ALPS EC10E1220505 - 10 mm hollow through-shaft incremental encoder,
// horizontal type (shaft parallel to the PCB), 12 PPR / 24 detents.
// 1:1 transcription of the owner's EC10E1220505.kicad_mod (KiCad 10 export),
// with only the board-level bookkeeping removed to match the kicad8 template:
// the (version/generator) header and the KiCad-10-only tokens
// (duplicate_pad_numbers_are_jumpers, embedded_fonts). Pads, silk, fab,
// courtyard, mounting holes and the 3D model are verbatim.
//
// Geometry notes (from the ALPS product page + this footprint):
//   * The hollow shaft runs along the footprint's local y axis
//     (perpendicular to the A1-B1-C1 pad row); the code disc's ~10 mm
//     diameter spans the 9.8 mm body extent in x.
//   * The shaft line passes over footprint x = 2.48, 7.06 mm above the
//     board (the 3D model offset).
//   * So: rotate this footprint 90 deg to lay the shaft along the scroll
//     bar, and shift it so the x = 2.48 line lands on the bar's centreline.
//     The config does this with scroll_rot / scroll_enc_x / scroll_enc_y -
//     those offsets are provisional until checked against the real axle.
//
// Nets
//   a: encoder channel A (pad A1)
//   b: encoder channel B (pad B1)
//   c: common (pad C1, normally GND)
// MH1 / MH2 are the mounting legs - mechanical only, no net.

module.exports = {
    params: {
        designator: 'SCRL',
        a: undefined,
        b: undefined,
        c: undefined
    },
    body: p => `
    (footprint "EC10E1220505"
        (layer "F.Cu")
        ${p.at /* parametric position */}
        (descr "EC10E1220505-1")
        (tags "Integrated Circuit")
        (property "Reference" "${p.ref}"
            (at 2.5 -1.35 ${p.r})
            (layer "F.SilkS")
            ${p.ref_hide ? '(hide yes)' : ''}
            (uuid "38f86b4a-fa96-48a7-ae9f-9154a7b8b9b3")
            (effects
                (font
                    (size 1.27 1.27)
                    (thickness 0.254)
                )
            )
        )
        (property "Value" "EC10E1220505"
            (at 2.5 -1.35 ${p.r})
            (layer "F.SilkS")
            (hide yes)
            (uuid "aa6712a6-252a-4ee7-84f6-4327db05f103")
            (effects
                (font
                    (size 1.27 1.27)
                    (thickness 0.254)
                )
            )
        )
        (property "Datasheet" ""
            (at 0 0 ${p.r})
            (layer "F.Fab")
            (hide yes)
            (uuid "a205d1e8-d181-4ecf-a972-6f11f8c66fbc")
            (effects
                (font
                    (size 1.27 1.27)
                )
            )
        )
        (property "Description" ""
            (at 0 0 ${p.r})
            (layer "F.Fab")
            (hide yes)
            (uuid "9b09a766-923a-428d-9693-6b1788206564")
            (effects
                (font
                    (size 1.27 1.27)
                )
            )
        )
        (attr through_hole)
        (fp_line
            (start -2.4 -4.4)
            (end -2.4 -4.4)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "a09212cf-ff4a-43b7-9ce6-a3faafaa4794")
        )
        (fp_line
            (start -2.4 -4.4)
            (end 7.4 -4.4)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "7bfcc6e4-2b2d-44c7-b7dd-257b62a3c920")
        )
        (fp_line
            (start -2.4 0.5)
            (end -2.4 0.5)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "f8a90e22-23f5-454a-952d-9969869fc3c8")
        )
        (fp_line
            (start -2.4 0.5)
            (end -2.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "788601b3-2a97-49a2-8d1d-ac0b258b6794")
        )
        (fp_line
            (start -2.4 1.7)
            (end -2.4 0.5)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "793f7824-b06a-49e9-add7-7049693cc946")
        )
        (fp_line
            (start -2.4 1.7)
            (end -2.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "1160ffd3-e504-46bc-a6e1-ae6aaafe57f2")
        )
        (fp_line
            (start -2.4 1.7)
            (end -2.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "4b93ca14-944b-4227-8c85-c9746886298c")
        )
        (fp_line
            (start -2.4 1.7)
            (end 7.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "9d61edf4-6484-443c-ae15-f20a3c71adbb")
        )
        (fp_line
            (start 0 2.3)
            (end 0 2.3)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "e335d25d-a70f-4f3f-b5d7-d4ac354a8e5a")
        )
        (fp_line
            (start 0 2.3)
            (end 0 2.3)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "f1aed020-abcd-452d-937a-1c4e5b427e1f")
        )
        (fp_line
            (start 0 2.4)
            (end 0 2.4)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "a1f50148-e7e1-4cd6-8b3d-f43a61f67377")
        )
        (fp_line
            (start 7.4 -4.4)
            (end -2.4 -4.4)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "0ec345e4-9618-4df5-b2d5-440e0d85c7f1")
        )
        (fp_line
            (start 7.4 -4.4)
            (end 7.4 -4.4)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "d1a70ccd-905c-4229-9b03-f63ef3030f9c")
        )
        (fp_line
            (start 7.4 0.5)
            (end 7.4 0.5)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "d729ada1-ebae-4d6d-819b-68f11eac72b3")
        )
        (fp_line
            (start 7.4 0.5)
            (end 7.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "516301c4-ec12-4f09-99b1-ca104e7d7398")
        )
        (fp_line
            (start 7.4 1.7)
            (end -2.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "e27a7239-3f38-4ef4-a04e-f8bc60c0693e")
        )
        (fp_line
            (start 7.4 1.7)
            (end 7.4 0.5)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "e83cd7bd-7968-4a4c-a603-72787e6b8d79")
        )
        (fp_line
            (start 7.4 1.7)
            (end 7.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "91f673e0-5126-4a07-842b-68a9d2e4e016")
        )
        (fp_line
            (start 7.4 1.7)
            (end 7.4 1.7)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "c23f808e-7aaa-4b06-b2ff-76d657120986")
        )
        (fp_arc
            (start 0 2.3)
            (mid 0.05 2.35)
            (end 0 2.4)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "a5a476ec-b821-4759-83c5-fbd4db8481d9")
        )
        (fp_arc
            (start 0 2.4)
            (mid -0.05 2.35)
            (end 0 2.3)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "8e0ccc6f-4edd-4c03-a026-fb6e52fc4fe5")
        )
        (fp_arc
            (start 0 2.4)
            (mid -0.05 2.35)
            (end 0 2.3)
            (stroke
                (width 0.2)
                (type solid)
            )
            (layer "F.SilkS")
            (uuid "af07c505-92b8-4302-b176-0c117af3acc7")
        )
        (fp_line
            (start -4.9 -5.4)
            (end 9.9 -5.4)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.CrtYd")
            (uuid "3b9b2c32-147b-4506-b24d-280a65f6add3")
        )
        (fp_line
            (start -4.9 2.7)
            (end -4.9 -5.4)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.CrtYd")
            (uuid "13a1ac80-d3e5-45ea-9186-f160001ddb02")
        )
        (fp_line
            (start 9.9 -5.4)
            (end 9.9 2.7)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.CrtYd")
            (uuid "4a696fb5-43f2-4d3e-be10-eff705fd1227")
        )
        (fp_line
            (start 9.9 2.7)
            (end -4.9 2.7)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.CrtYd")
            (uuid "78b600fb-6e54-480b-b3ca-f07c4a022c35")
        )
        (fp_line
            (start -2.4 -4.4)
            (end -2.4 1.7)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.Fab")
            (uuid "e226378e-19ae-4890-8fb7-3834c3a8a115")
        )
        (fp_line
            (start -2.4 1.7)
            (end 7.4 1.7)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.Fab")
            (uuid "336f904c-7290-4768-95a1-0083d65bb1d1")
        )
        (fp_line
            (start 7.4 -4.4)
            (end -2.4 -4.4)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.Fab")
            (uuid "147928d4-5c4e-42e6-aea5-5441b47d3eba")
        )
        (fp_line
            (start 7.4 1.7)
            (end 7.4 -4.4)
            (stroke
                (width 0.1)
                (type solid)
            )
            (layer "F.Fab")
            (uuid "c5b583de-a3f2-4184-a50c-f4010675e5ae")
        )
        (fp_text user "\${REFERENCE}"
            (at 2.5 -1.35 ${p.r})
            (layer "F.Fab")
            (uuid "3c16830a-22e0-4125-b050-0ae2fe2908d8")
            (effects
                (font
                    (size 1.27 1.27)
                    (thickness 0.254)
                )
            )
        )
        (pad "A1" thru_hole circle
            (at 0 0 ${p.r})
            (size 1.5 1.5)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (uuid "77c7ce0d-1661-477f-bb0e-e34d08a770fb")
            ${p.a}
        )
        (pad "B1" thru_hole circle
            (at 2.5 0 ${p.r})
            (size 1.5 1.5)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (uuid "a713c9bf-c1ef-4550-af77-ab676d9894fc")
            ${p.b}
        )
        (pad "C1" thru_hole circle
            (at 5 0 ${p.r})
            (size 1.5 1.5)
            (drill 1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (uuid "77fe4296-ae19-494e-9dc2-9b385015872d")
            ${p.c}
        )
        (pad "MH1" thru_hole circle
            (at -2 -2 ${p.r})
            (size 3.4 3.4)
            (drill 2.1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (uuid "2eed5954-b57f-4a21-acb0-5ceb8b64da98")
        )
        (pad "MH2" thru_hole circle
            (at 7 -2 ${p.r})
            (size 3.4 3.4)
            (drill 2.1)
            (layers "*.Cu" "*.Mask")
            (remove_unused_layers no)
            (uuid "ff91206f-8edf-47f1-a494-f11b268d9007")
        )
        (model "EC10E1220505.stp"
            (offset
                (xyz 2.48 -0.3 7.06)
            )
            (scale
                (xyz 1 1 1)
            )
            (rotate
                (xyz -180 -180 -180)
            )
        )
    )
    `
}