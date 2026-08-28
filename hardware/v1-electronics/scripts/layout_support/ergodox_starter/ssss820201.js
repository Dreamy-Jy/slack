// ALPS SSSS820201 - 2-position slide switch (latching), SMD with two
// locating NPTH pins. 1:1 transcription of the owner's SSSS820201.kicad_mod
// (KiCad 10 export), with the board-level bookkeeping removed to match the
// kicad8 template (version/generator header, duplicate_pad_numbers_are_jumpers,
// embedded_fonts). Pads, silk (including the pin-1 dot at kicad (-1.2, -3)),
// the 8 x 7 Margin body rect and the 3D model reference are verbatim.
//
// WIRING - NOT YET VERIFIED: the datasheet drawing was not checked for which
// pad is the common of each pole. This module assumes the usual slide-switch
// arrangement - middle pad is the common - and wires one pole only:
//   from: pad 2 (assumed common, e.g. the scan column)
//   to:   pad 1 (one throw, e.g. the per-switch colrow)
// Pads 3-6 are soldered but left off any net. Confirm on a real part.
// The four "7" pads are the mounting tabs (no net).
module.exports = {
    params: {
        designator: 'LSW',
        from: undefined,
        to: undefined
    },
    body: p => `
    (footprint "SSSS820201"
        (layer "F.Cu")
        ${p.at /* parametric position */}
        (property "Value" "SSSS820201"
            (at 0 4.2 ${p.r})
            (unlocked yes)
            (layer "F.Fab")
            (uuid "d0074517-1fd4-4d0b-871a-6ec37013a585")
            (effects (font (size 1 1) (thickness 0.15)))
        )
        (property "Reference" "${p.ref}"
            (at 0 1.3 ${p.r})
            (unlocked yes)
            (layer "F.SilkS")
            (uuid "0836449c-d899-405e-a739-4d4bee0eec88")
            (effects (font (size 1 1) (thickness 0.1)))
        )
        (attr through_hole)
        (fp_line (start -3.4 1.3) (end -3.4 -1.3) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "8f8fa66a-c27c-4251-b94c-9b53da5d0475"))
        (fp_line (start -2.7 -2.1) (end -2.8 -2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "e6fd9c03-2c8f-4ece-98e7-827275f2fc1f"))
        (fp_line (start -2.7 2.1) (end -2.8 2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "c195deb8-5cfd-442f-b94f-c2aaf3767f6f"))
        (fp_line (start 0.3 -2.1) (end -1.8 -2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "8ee63eab-5c7b-4961-a3b0-cd764637efcd"))
        (fp_line (start 0.3 2.1) (end -1.8 2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "26e717f2-3fdd-4797-8f4a-b77e9d25112f"))
        (fp_line (start 1.2 -2.1) (end 1.8 -2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "3c2d713b-1cbe-4b07-bbc6-8e16110e3920"))
        (fp_line (start 1.2 2.1) (end 1.8 2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "6126b79e-416b-4b3a-a217-b6adcb4b43ec"))
        (fp_line (start 2.8 -2.1) (end 2.7 -2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "1351fb69-68aa-4309-a2a9-26f884c35485"))
        (fp_line (start 2.8 2.1) (end 2.7 2.1) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "ea076050-1520-4d5a-86c4-a81b701f5c62"))
        (fp_line (start 3.4 -1.3) (end 3.4 1.3) (stroke (width 0.1) (type default)) (layer "F.SilkS") (uuid "71d294fc-3609-4ec3-9cfa-3970ab9ed1ef"))
        (fp_circle (center -1.2 -3) (end -1.4 -2.8) (stroke (width 0.1) (type default)) (fill yes) (layer "F.SilkS") (uuid "55b692a0-af76-4889-9e9f-23352af4edad"))
        (fp_rect (start -4 -3.5) (end 4 3.5) (stroke (width 0.05) (type default)) (fill no) (layer "Margin") (uuid "31eb2227-48b8-4a48-91e9-ad3054b3f5bd"))
        (pad "" np_thru_hole circle (at -1.5 0 ${p.r}) (size 0.9 0.9) (drill 0.9) (layers "*.Cu") (uuid "6629e0cd-1c24-40e5-b710-f277e267b0e7"))
        (pad "" np_thru_hole circle (at 1.5 0 ${p.r}) (size 0.9 0.9) (drill 0.9) (layers "*.Cu") (uuid "dca05658-1924-4f23-ac1c-9b46c8db5c4f"))
        (pad "1" smd rect (at -2.25 -2.55 ${p.r}) (size 0.7 1.5) (layers "F.Cu" "F.Mask") ${p.to.str} (uuid "41ecb46a-1e37-4541-aff7-50c91db28c70"))
        (pad "2" smd rect (at 0.75 -2.55 ${p.r}) (size 0.7 1.5) (layers "F.Cu" "F.Mask") ${p.from.str} (uuid "07712c97-e30a-47eb-b9b9-d86739ad4479"))
        (pad "3" smd rect (at 2.25 -2.55 ${p.r}) (size 0.7 1.5) (layers "F.Cu" "F.Mask") (uuid "e719f02a-dba1-424d-919b-8c02439270d1"))
        (pad "4" smd rect (at -2.25 2.55 ${p.r}) (size 0.7 1.5) (layers "F.Cu" "F.Mask") (uuid "433191ef-2ed1-42f5-a590-3dde6d443f67"))
        (pad "5" smd rect (at 0.75 2.55 ${p.r}) (size 0.7 1.5) (layers "F.Cu" "F.Mask") (uuid "569e820b-b605-4831-a29e-2614ba06c413"))
        (pad "6" smd rect (at 2.25 2.55 ${p.r}) (size 0.7 1.5) (layers "F.Cu" "F.Mask") (uuid "9a5fa41c-c363-4021-8dbf-b584a494120d"))
        (pad "7" smd rect (at -3.4 -1.8 ${p.r}) (size 1 0.8) (layers "F.Cu" "F.Mask") (uuid "3dc33671-ab4d-41dd-a650-dbe0c94f2d7f"))
        (pad "7" smd rect (at -3.4 1.8 ${p.r}) (size 1 0.8) (layers "F.Cu" "F.Mask") (uuid "5f55a21b-bc6a-4fdc-8a93-efac51364d7c"))
        (pad "7" smd rect (at 3.4 -1.8 ${p.r}) (size 1 0.8) (layers "F.Cu" "F.Mask") (uuid "f023ede3-17d5-4cbe-a650-dbe0c94f2d7f"))
        (pad "7" smd rect (at 3.4 1.8 ${p.r}) (size 1 0.8) (layers "F.Cu" "F.Mask") (uuid "229ded25-683e-4637-87b5-90b96f12054a"))
        (model "\${KIPRJMOD}/ALPS Electric/SSSS820201.STEP"
            (offset (xyz 0 0 0))
            (scale (xyz 1 1 1))
            (rotate (xyz -90 -0 -0))
        )
    )`
}