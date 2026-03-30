# Plans
## Revision One

### Bill Off Materials (BOM)

- Momentary(Main) Switches (Mfr. #: MX6C-K3NB)
- Latching(Secondary) Switches (Not chosen yet: DB2C-A1LB, SPPH110900, PS-5824SVB-4PL)
- Encoder(Secondary) Switches (Mfr. #: PEC11S-929K-S0015)
- Sliding Switch (Not chosen yet)

- Diodes (Mfr. #: BAS16TS_R1_00001)
- RGB LEDs (Mfr. #: LTST-FC12WEGBD-5A)
- LED Driver (Mfr. #: IS31FL3741A-QFLS4-TR)

- Battery \[4.2V Lithium @ 100/500mA rate\] (Not chosen yet)
- Battery Connector

### Layout

#### Physical

Consider adding a horizontal scroll wheel to the thumb clusters

6 x 12 Ortholinear
6 - 12 Encoder (amount depends on hardware design)
+12 Latching Button

#### Software

Based on [Glorious Engrammer Layout](https://sunaku.github.io/moergo-glove80-keyboard.html).

Base Layer - QWERTY + Home Row Mods
Navigation Layers - (Keyboard and Mouse)
Symbol Layer - spacegrams,
Emoji Layer
World Layer
System Layer

I'll need to adapt this to use Latches and Encoders

## Post Revision One Experiments

Experimental modules.
- pointing device modules
  - trackpad modules (Framework FRANFT0001)
  - trackpoint modules (sprintek SK8707-06)
  - trackball modules?
- display modules
  - What will be the controls for this display?
- power electronics circuits
- Haptic Feedback Modules

https://patchouli.readthedocs.io/en/latest/
https://github.com/ploopyco/trackpad

[ ] modernize existing drivers the [drv2605l-rs](https://github.com/jacobrosenthal/drv2605l-rs/tree/master) driver to use [embedded_hal](https://github.com/rust-embedded/embedded-hal/tree/master) v1 and the latest [bitfield](https://github.com/dzamlo/rust-bitfield) version.

## Considerations For Revision Two

For the end product I want to do a skeletonized design.
- use metal knob encoders
I want to have seperate encoders for the display modules and the encoder inputs.
I could create my own colors clicking encoders.
