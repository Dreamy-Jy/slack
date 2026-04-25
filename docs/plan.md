# Plans
## Revision One

### Bill Off Materials (BOM)

- MCU nice!nano (nRF52840)

- Momentary(Main) Switches (Mfr. #: MX6C-K3NB)
- Latching(Secondary) Switches (Not chosen yet: DB2C-A1LB, SPPH110900)
- Encoder(Secondary) Switches (Mfr. #: PEC11S-929K-S0015)
- Encoder(trestary) shaftless switchless (Mfr. #: )
- Sliding Switch (Not chosen yet)

- Diodes (Mfr. #: BAS16TS_R1_00001)
- RGB LEDs (Mfr. #: LTST-FC12WEGBD-5A)
- LED Driver (Mfr. #: IS31FL3741A-QFLS4-TR)

- Battery \[4.2V Lithium @ 100/500mA rate\] (Not chosen yet)
- Battery Connector

### Layout

#### Physical

5 x 12 ULP Switches (Column Linear Alice with Thumb Clusters, 4 x 12 main part, 1x12 thumb cluster), Holes for Track points
10 Encoders (8 push button encoder, 2 through shaft encoder)
+12 Latching Button

##### Issues

As I've started the hardware design I've realized 2 things:

- the nice!nano does not expose enough io for this project (pick a new module, I get access documentation, and my pcba suppler has)
  - I've chosen the Raytac MDBT50Q-1MV2 nrf52840 module as a replacement
    - I'll to implement:
      - module support circuitry
      - battery charging
      - more
- As the project evolves the number of IO will ballon. (we need i2c chips) (if we switch to a more expansive module, and use i2c we should be fine)
  - if we have buses available

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

Experimental modules:

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

## Further Study

- Upgrade the board the nrf54:
  - Make dev boards and rust drivers for nrf54hx and nrf54lx
- Create a test bench for the device:
  - `embedded-graphics-core`
- Break down svd2rust and chiptool

## Considerations For Revision Two

For the end product I want to do a skeletonized design.
- use metal knob encoders
I want to have seperate encoders for the display modules and the encoder inputs.
I could create my own colors clicking encoders.
