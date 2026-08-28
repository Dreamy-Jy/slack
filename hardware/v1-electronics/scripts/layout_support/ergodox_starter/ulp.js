// Cherry MX Ultra Low Profile switch (MX6C-K3NB click / MX6C-T3NB tactile)
//
// Ergogen version of Cherry_ULP_SMD.kicad_mod (community footprint by
// pashutk, re-saved from KiCad 10 with courtyards, component window, keepout
// zone, dimensions and 3D models). Geometry is copied 1:1 from that file:
//   - silkscreen body      14.2 x 12.8 mm
//   - courtyard            13.6 x 12.2 mm (the switch module), plus an
//                          18 x 18 mm square around it for keycap clearance
//   - component window     x -3.6..3.1, y -4.2..-1.8 (Dwgs.User) - the open
//                          pocket in the switch base, ~1.5 mm headroom, where
//                          the RGB LED (and here the SOD-523 diode) can sit
//   - 3 locating pins      (-5.8, 1.2) d1.05, (5.8, +/-3.26) d1.2
//   - 2 contact pads       0.7 x 3.4 at (-0.65, 2.3) and (1.8, 2.3)
//   - 5 mechanical pads    (no net) along the left/right edges
//   - keepout zone         x -5..-1.2, y 2.2..4.2 (no tracks/vias/pads/pour)
//   - 2 dimensions         13.9 mm (silk left edge to courtyard right edge)
//                          and 12.8 mm (body height), on Cmts.User
//
// Requires the kicad8 PCB template (pcbs.<name>.template: kicad8). The
// KiCad 9+/10-only tokens in the .kicad_mod (duplicate_pad_numbers_are_jumpers,
// embedded_fonts, zone placement) are left out so the output stays KiCad 8
// compatible; they carry no geometry.
//
// Nets
//   from: contact pad 1
//   to:   contact pad 2
// Params
//   keepout: true        emit the keepout zone (as a board-level rule area)
//   keepout_layer: Dwgs.User   layer of that zone, as in the attached file.
//                        Set to F.Cu if you want DRC to actually enforce it.
//   dimensions: true     include the two Cmts.User dimension annotations
//                        (set false to drop 2 measuring arrows per switch)
//   models: true         include the 3D model entries from the attached file.
//                        Note the two keycap models point at absolute paths
//                        on the author's machine, exactly as in the file.

module.exports = {
  params: {
    designator: 'S',
    keepout: true,
    keepout_layer: 'Dwgs.User',
    dimensions: true,
    models: true,
    from: { type: 'net', value: undefined },
    to: { type: 'net', value: undefined }
  },
  body: p => {
    const footprint = `
    (footprint "Cherry_ULP_SMD"
      (layer "F.Cu")
      ${p.at}
      (property "Reference" "${p.ref}"
        (at -0.05 -7.5 ${p.r})
        (unlocked yes)
        (layer "F.SilkS")
        ${p.ref_hide}
        (effects (font (size 1 1) (thickness 0.15)))
      )
      (property "Value" "Cherry_ULP_SMD"
        (at 0 0 ${p.r})
        (unlocked yes)
        (layer "F.Fab")
        (hide yes)
        (effects (font (size 1 1) (thickness 0.15)))
      )
      (property "Datasheet" ""
        (at 0 0 ${p.r})
        (layer "F.Fab")
        (hide yes)
        (effects (font (size 1.27 1.27) (thickness 0.15)))
      )
      (property "Description" ""
        (at 0 0 ${p.r})
        (layer "F.Fab")
        (hide yes)
        (effects (font (size 1.27 1.27) (thickness 0.15)))
      )
      (attr smd)

      ${'' /* switch module body */}
      (fp_rect (start -7.1 -6.4) (end 7.1 6.4) (stroke (width 0.1) (type solid)) (fill no) (layer "F.SilkS"))

      ${'' /* component window in the switch base */}
      (fp_rect (start -3.6 -1.8) (end 3.1 -4.2) (stroke (width 0.05) (type solid)) (fill no) (layer "Dwgs.User"))

      ${'' /* courtyards: keycap clearance square, then the switch module */}
      (fp_rect (start -9.5 -9.5) (end 9.5 9.5) (stroke (width 0.15) (type solid)) (fill no) (layer "F.CrtYd"))
      (fp_rect (start -6.8 -6.1) (end 6.8 6.1) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
    `

    // Measuring annotations from the .kicad_mod, on the comments layer
    const dimensions = `
      (dimension
        (type aligned)
        (layer "Cmts.User")
        (pts (xy -7.1 -6.4) (xy 6.8 -6.4))
        (height -2.1)
        (format (prefix "") (suffix "") (units 3) (units_format 1) (precision 4))
        (style (thickness 0.1) (arrow_length 1.27) (text_position_mode 0) (arrow_direction outward) (extension_height 0.58642) (extension_offset 0.5) (keep_text_aligned yes))
        (gr_text "13.9000 mm"
          (at -0.15 -9.6 0)
          (layer "Cmts.User")
          (effects (font (size 1 1) (thickness 0.1)))
        )
      )
      (dimension
        (type aligned)
        (layer "Cmts.User")
        (pts (xy -7.1 6.4) (xy -7.1 -6.4))
        (height -2.9)
        (format (prefix "") (suffix "") (units 3) (units_format 1) (precision 4))
        (style (thickness 0.1) (arrow_length 1.27) (text_position_mode 0) (arrow_direction outward) (extension_height 0.58642) (extension_offset 0.5) (keep_text_aligned yes))
        (gr_text "12.8000 mm"
          (at -11.1 0 90)
          (layer "Cmts.User")
          (effects (font (size 1 1) (thickness 0.1)))
        )
      )
    `

    const pads = `
      ${'' /* locating pins */}
      (pad "" np_thru_hole circle (at -5.8 1.2) (size 1.05 1.05) (drill 1.05) (layers "*.Cu" "*.Mask"))
      (pad "" np_thru_hole circle (at 5.8 -3.26) (size 1.2 1.2) (drill 1.2) (layers "*.Cu" "*.Mask"))
      (pad "" np_thru_hole circle (at 5.8 3.26) (size 1.2 1.2) (drill 1.2) (layers "*.Cu" "*.Mask"))

      ${'' /* contacts */}
      (pad "1" smd rect (at -0.65 2.3 ${p.r}) (size 0.7 3.4) (layers "F.Cu" "F.Mask" "F.Paste") ${p.from.str})
      (pad "2" smd rect (at 1.8 2.3 ${p.r}) (size 0.7 3.4) (layers "F.Cu" "F.Mask" "F.Paste") ${p.to.str})

      ${'' /* mechanical anchor pads, no net */}
      (pad "3" smd rect (at -6.2 -3.9 ${p.r}) (size 1.6 3.8) (layers "F.Cu" "F.Mask" "F.Paste"))
      (pad "3" smd rect (at -6.2 4.5 ${p.r}) (size 1.6 3) (layers "F.Cu" "F.Mask" "F.Paste"))
      (pad "3" smd rect (at 6.2 -5.025 ${p.r}) (size 1.6 1.8) (layers "F.Cu" "F.Mask" "F.Paste"))
      (pad "3" smd rect (at 6.2 0 ${p.r}) (size 1.6 2.6) (layers "F.Cu" "F.Mask" "F.Paste"))
      (pad "3" smd rect (at 6.2 5.025 ${p.r}) (size 1.6 1.8) (layers "F.Cu" "F.Mask" "F.Paste"))
    `

    const models = `
      (model "\${KIPRJMOD}/Cherry/Switch-Cherry_MX_ULP.step"
        (offset (xyz -5.5 0 3))
        (scale (xyz 1 1 1))
        (rotate (xyz -0 -0 -90))
      )
      (model "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-mechanics/keycaps/OVT13_keycap.step"
        (hide yes)
        (offset (xyz 0 0 0))
        (scale (xyz 1 1 1))
        (rotate (xyz 0 0 0))
      )
      (model "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-mechanics/keycaps/mnhttn_keycap.step"
        (hide yes)
        (offset (xyz 0 0 4))
        (scale (xyz 1 1 1))
        (rotate (xyz -180 -0 -0))
      )
      (model "/Users/jordanethomas/Documents/Projects/keyboards/slack/hardware/v1-mechanics/keycaps/ulp_dactyl_keycap.step"
        (offset (xyz 0 0 4.5))
        (scale (xyz 1 1 1))
        (rotate (xyz -180 -0 -0))
      )
    `

    const closing = `
    )
    `

    // The keepout is emitted as a board-level rule area in absolute coordinates
    // (eaxy = rotated with the switch, never mirrored), so it lands in the same
    // spot relative to the switch on both halves.
    const keepout = `
    (zone
      (net 0)
      (net_name "")
      (layer "${p.keepout_layer}")
      (hatch edge 0.508)
      (connect_pads (clearance 0))
      (min_thickness 0.254)
      (filled_areas_thickness no)
      (keepout
        (tracks not_allowed)
        (vias not_allowed)
        (pads not_allowed)
        (copperpour not_allowed)
        (footprints allowed)
      )
      (fill (thermal_gap 0.508) (thermal_bridge_width 0.508))
      (polygon
        (pts
          (xy ${p.eaxy(-1.2, 4.2)})
          (xy ${p.eaxy(-5, 4.2)})
          (xy ${p.eaxy(-5, 2.2)})
          (xy ${p.eaxy(-1.2, 2.2)})
        )
      )
    )
    `

    return footprint
      + (p.dimensions ? dimensions : '')
      + pads
      + (p.models ? models : '')
      + closing
      + (p.keepout ? keepout : '')
  }
}