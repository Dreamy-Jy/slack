// Lite-On LTST-FC12WEGBD-5A RGBW LED, 1.2 x 1.2 x 0.5 mm, 5 pads, no lead.
// Ergogen (KiCad 8 syntax) version of the attached LTSTFC12WEGBD5A.kicad_mod:
//   - body       1.2 x 1.2 (F.Fab), courtyard 3.2 x 3.2
//   - pads 1,2,3 0.2 x 0.2 at (0.38, -0.3 / 0 / 0.3)
//   - pad 4      0.2 x 0.8 at (-0.38, 0)
//   - pad 5      0.2 x 0.8 at (0, 0)
// Datasheet pin assignment: white 5-4, red 5-3, green 5-2, blue 5-1, so
// pad 5 is the common pin; check the datasheet drawing for its polarity.
//
// Requires the kicad8 PCB template (pcbs.<name>.template: kicad8).
//
// Nets
//   common: pad 5   white: pad 4   red: pad 3   green: pad 2   blue: pad 1
// Params
//   model: true   include the 3D model entry from the attached footprint

module.exports = {
  params: {
    designator: 'LED',
    model: true,
    common: { type: 'net', value: undefined },
    white: { type: 'net', value: undefined },
    red: { type: 'net', value: undefined },
    green: { type: 'net', value: undefined },
    blue: { type: 'net', value: undefined }
  },
  body: p => {
    const fp = `
    (footprint "LTSTFC12WEGBD5A"
      (layer "F.Cu")
      ${p.at}
      (property "Reference" "${p.ref}"
        (at 0 -1.905 ${p.r})
        (layer "F.SilkS")
        ${p.ref_hide}
        (effects (font (size 1.27 1.27) (thickness 0.254)))
      )
      (property "Value" "LTSTFC12WEGBD5A"
        (at 0 0 ${p.r})
        (layer "F.SilkS")
        (hide yes)
        (effects (font (size 1.27 1.27) (thickness 0.254)))
      )
      (attr smd)

      ${'' /* pin-1 marker */}
      (fp_circle (center 1.15 -0.3) (end 1.2 -0.3) (layer "F.SilkS") (stroke (width 0.1) (type solid)) (fill no))

      ${'' /* courtyard */}
      (fp_rect (start -1.6 -1.6) (end 1.6 1.6) (stroke (width 0.1) (type solid)) (fill no) (layer "F.CrtYd"))

      ${'' /* body */}
      (fp_rect (start -0.6 -0.6) (end 0.6 0.6) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))

      ${'' /* pads */}
      (pad "1" smd rect (at 0.38 -0.3 ${p.r}) (size 0.2 0.2) (layers "F.Cu" "F.Mask" "F.Paste") ${p.blue.str})
      (pad "2" smd rect (at 0.38 0 ${p.r}) (size 0.2 0.2) (layers "F.Cu" "F.Mask" "F.Paste") ${p.green.str})
      (pad "3" smd rect (at 0.38 0.3 ${p.r}) (size 0.2 0.2) (layers "F.Cu" "F.Mask" "F.Paste") ${p.red.str})
      (pad "4" smd rect (at -0.38 0 ${p.r}) (size 0.2 0.8) (layers "F.Cu" "F.Mask" "F.Paste") ${p.white.str})
      (pad "5" smd rect (at 0 0 ${p.r}) (size 0.2 0.8) (layers "F.Cu" "F.Mask" "F.Paste") ${p.common.str})
    `
    const model = `
      (model "LTST-FC12WEGBD-5A.stp"
        (offset (xyz 0 0 -0.009999999626))
        (scale (xyz 1 1 1))
        (rotate (xyz -90 0 -180))
      )
    `
    return fp + (p.model ? model : '') + `
    )
    `
  }
}