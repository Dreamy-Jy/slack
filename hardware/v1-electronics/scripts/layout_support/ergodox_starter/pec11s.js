// Bourns PEC11S-929K-S0015 rotary encoder with push switch, surface mount.
// Ergogen (KiCad 8 syntax) version of the attached PEC11S929KS0015.kicad_mod:
//   - body            11.7 x 14.2 mm (F.Fab), long axis along the footprint's y
//   - courtyard       x +/-9.25, y -10.5..11.7 (includes all pads)
//   - encoder pads    A1 (-2.5, 7.3), C1 (0, 7.3), B1 (2.5, 7.3)   1.3 x 2.4
//   - switch pads     D1 (-2.5, -7),  E1 (2.5, -7)                 1.3 x 2.4
//   - locating holes  MH1 (0, 0) d2.15, MH2 (0, 4.5) d2.89
//   - anchor pads     MP1-MP6, no net
// The shaft is at the footprint origin.
//
// Requires the kicad8 PCB template (pcbs.<name>.template: kicad8).
//
// Nets
//   a, b:   encoder phases (pads A1, B1)
//   c:      encoder common (pad C1), default GND
//   s1, s2: push switch (pads D1, E1), s2 defaults to GND
// Params
//   model: true   include the 3D model entry from the attached footprint

module.exports = {
  params: {
    designator: 'ENC',
    model: true,
    a: { type: 'net', value: undefined },
    b: { type: 'net', value: undefined },
    c: { type: 'net', value: 'GND' },
    s1: { type: 'net', value: undefined },
    s2: { type: 'net', value: 'GND' }
  },
  body: p => {
    const fp = `
    (footprint "PEC11S929KS0015"
      (layer "F.Cu")
      ${p.at}
      (property "Reference" "${p.ref}"
        (at 0 0.6 ${p.r})
        (layer "F.SilkS")
        ${p.ref_hide}
        (effects (font (size 1.27 1.27) (thickness 0.254)))
      )
      (property "Value" "PEC11S929KS0015"
        (at 0 0.6 ${p.r})
        (layer "F.SilkS")
        (hide yes)
        (effects (font (size 1.27 1.27) (thickness 0.254)))
      )
      (attr smd)

      ${'' /* body outline */}
      (fp_line (start -5.85 7.1) (end 5.85 7.1) (layer "F.Fab") (stroke (width 0.2) (type solid)))
      (fp_line (start 5.85 7.1) (end 5.85 -7.1) (layer "F.Fab") (stroke (width 0.2) (type solid)))
      (fp_line (start 5.85 -7.1) (end -5.85 -7.1) (layer "F.Fab") (stroke (width 0.2) (type solid)))
      (fp_line (start -5.85 -7.1) (end -5.85 7.1) (layer "F.Fab") (stroke (width 0.2) (type solid)))

      ${'' /* courtyard */}
      (fp_line (start -9.25 -10.5) (end 9.25 -10.5) (layer "F.CrtYd") (stroke (width 0.1) (type solid)))
      (fp_line (start 9.25 -10.5) (end 9.25 11.7) (layer "F.CrtYd") (stroke (width 0.1) (type solid)))
      (fp_line (start 9.25 11.7) (end -9.25 11.7) (layer "F.CrtYd") (stroke (width 0.1) (type solid)))
      (fp_line (start -9.25 11.7) (end -9.25 -10.5) (layer "F.CrtYd") (stroke (width 0.1) (type solid)))

      ${'' /* pin A marker */}
      (fp_circle (center -2.5 10.65) (end -2.5 10.95) (layer "F.SilkS") (stroke (width 0.2) (type solid)) (fill yes))

      ${'' /* encoder: A, C (common), B */}
      (pad "A1" smd rect (at -2.5 7.3 ${p.r}) (size 1.3 2.4) (layers "F.Cu" "F.Paste" "F.Mask") ${p.a.str})
      (pad "C1" smd rect (at 0 7.3 ${p.r}) (size 1.3 2.4) (layers "F.Cu" "F.Paste" "F.Mask") ${p.c.str})
      (pad "B1" smd rect (at 2.5 7.3 ${p.r}) (size 1.3 2.4) (layers "F.Cu" "F.Paste" "F.Mask") ${p.b.str})

      ${'' /* push switch */}
      (pad "D1" smd rect (at -2.5 -7 ${p.r}) (size 1.3 2.4) (layers "F.Cu" "F.Paste" "F.Mask") ${p.s1.str})
      (pad "E1" smd rect (at 2.5 -7 ${p.r}) (size 1.3 2.4) (layers "F.Cu" "F.Paste" "F.Mask") ${p.s2.str})

      ${'' /* locating holes */}
      (pad "MH1" np_thru_hole circle (at 0 0) (size 2.15 2.15) (drill 2.15) (layers "*.Cu" "*.Mask"))
      (pad "MH2" np_thru_hole circle (at 0 4.5) (size 2.89 2.89) (drill 2.89) (layers "*.Cu" "*.Mask"))

      ${'' /* mechanical anchor pads, no net */}
      (pad "MP1" smd rect (at -6.375 0 ${p.r}) (size 3.75 4) (layers "F.Cu" "F.Paste" "F.Mask"))
      (pad "MP2" smd rect (at 6.375 0 ${p.r}) (size 3.75 4) (layers "F.Cu" "F.Paste" "F.Mask"))
      (pad "MP3" smd rect (at -5 -7.9 ${p.r}) (size 2.5 3.2) (layers "F.Cu" "F.Paste" "F.Mask"))
      (pad "MP4" smd rect (at 5 -7.9 ${p.r}) (size 2.5 3.2) (layers "F.Cu" "F.Paste" "F.Mask"))
      (pad "MP5" smd rect (at -5 7.9 ${p.r}) (size 2.5 3.2) (layers "F.Cu" "F.Paste" "F.Mask"))
      (pad "MP6" smd rect (at 5 7.9 ${p.r}) (size 2.5 3.2) (layers "F.Cu" "F.Paste" "F.Mask"))
    `
    const model = `
      (model "PEC11S-929K-S0015.stp"
        (offset (xyz -0.070078739031093 0.15196849980692 -0.0039370079326817))
        (scale (xyz 1 1 1))
        (rotate (xyz 0 0 0))
      )
    `
    return fp + (p.model ? model : '') + `
    )
    `
  }
}