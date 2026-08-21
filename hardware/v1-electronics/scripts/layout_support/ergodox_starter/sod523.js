// SOD-523 SMD diode (e.g. 1N4148WT / BAS316 in SOD-523), KiCad 8 format.
// Land pattern from KiCad's Diode_SMD:D_SOD-523 (Diodes Inc. AP02001 p.144):
// two 0.6 x 0.7 mm pads on a 1.4 mm pitch, 2.5 x 1.4 mm courtyard, body
// 1.2 x 0.8 mm and about 0.6 mm tall - small enough to sit inside the open
// window of the Cherry MX ULP switch base.
//
// Requires the kicad8 PCB template (pcbs.<name>.template: kicad8).
//
// Nets (same convention as ergogen's built-in diode)
//   from: anode   (pad 2)
//   to:   cathode (pad 1, marked with the silkscreen bar)
// Params
//   side: F (default) or B

module.exports = {
  params: {
    designator: 'D',
    side: 'F',
    from: { type: 'net', value: undefined },
    to: { type: 'net', value: undefined }
  },
  body: p => `
    (footprint "D_SOD-523"
      (layer "${p.side}.Cu")
      ${p.at}
      (property "Reference" "${p.ref}"
        (at 0 -1.3 ${p.r})
        (layer "${p.side}.SilkS")
        ${p.ref_hide}
        (effects (font (size 1 1) (thickness 0.15)))
      )
      (property "Value" "D_SOD-523"
        (at 0 1.4 ${p.r})
        (layer "${p.side}.Fab")
        (hide yes)
        (effects (font (size 1 1) (thickness 0.15)))
      )
      (attr smd)

      ${'' /* silkscreen: outline with cathode bar on the pad-1 side */}
      (fp_line (start -1.15 -0.6) (end -1.15 0.6) (layer "${p.side}.SilkS") (stroke (width 0.12) (type solid)))
      (fp_line (start 0.7 -0.6) (end -1.15 -0.6) (layer "${p.side}.SilkS") (stroke (width 0.12) (type solid)))
      (fp_line (start 0.7 0.6) (end -1.15 0.6) (layer "${p.side}.SilkS") (stroke (width 0.12) (type solid)))

      ${'' /* fab: body and diode symbol */}
      (fp_line (start -0.65 -0.45) (end 0.65 -0.45) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start 0.65 -0.45) (end 0.65 0.45) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start 0.65 0.45) (end -0.65 0.45) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start -0.65 0.45) (end -0.65 -0.45) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start 0.1 -0.2) (end 0.1 0.2) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start 0.1 -0.2) (end -0.2 0) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start -0.2 0) (end 0.1 0.2) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))
      (fp_line (start -0.2 -0.2) (end -0.2 0.2) (layer "${p.side}.Fab") (stroke (width 0.1) (type solid)))

      ${'' /* courtyard */}
      (fp_rect (start -1.25 -0.7) (end 1.25 0.7) (stroke (width 0.05) (type solid)) (fill no) (layer "${p.side}.CrtYd"))

      ${'' /* pads: 1 = cathode, 2 = anode */}
      (pad "1" smd rect (at -0.7 0 ${p.r}) (size 0.6 0.7) (layers "${p.side}.Cu" "${p.side}.Paste" "${p.side}.Mask") ${p.to.str})
      (pad "2" smd rect (at 0.7 0 ${p.r}) (size 0.6 0.7) (layers "${p.side}.Cu" "${p.side}.Paste" "${p.side}.Mask") ${p.from.str})
    )
  `
}
