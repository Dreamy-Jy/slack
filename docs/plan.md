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

##### Power

USB-C at USB 2.0

Power Path Charger to allow for charging and operation at the same time.

I don't know how to make power circuitry or design a charger.

I'll need to setup time on thursday to test the board at plugged in, and at battery power.

Down the line upgrade to mcu controlled power circuits.

Power gauges are a seperate circuit all together. I want a hardware fuel gauge, and down the line battery health.

ideal diode chip.


Power path:
Power mux
USB -> charger -> fuel gauge -> battery

step up regulator TPS613222

Compare a power chip to power train:

Power Train:
Power Path Charger
Step-up Regulator
Batter Full Gauge

Power Chip - MP2632,

LM66200 -> power mux (ideal diode)

Ideal power chip:

- hardware and software status
- software control (i2c, etc.)
- battery monitoring:
  - charge level
  - incompatible battery detection
  - battery health poor
- output:
  - 2 output (3v and 5v)

USB power delivery (for usb 2.0 or 3.0??)

A shitty first pass at a power circuitry
USB-C -> Battery Charger -> Boost Converter

##### Microcontroller Configuration

##### Switch Matrix

5 x 12 ULP Switches (Column Linear Alice with Thumb Clusters, 4 x 12 main part, 1x12 thumb cluster), Holes for Track points
10 Encoders (8 push button encoder, 2 through shaft encoder)
12 Latching Button

##### RGBW LED Matrix

84 RGBW LEDs for the switch matrix (max 87 RGBW)
15 Other LEDs

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
  - trackpad modules
    - Framework FRANFT0001 (PixArt PCT3854QR)
    - [ploopy touchpad](https://github.com/ploopyco/trackpad) (Microchip ATMXT1066TD)
    - [Patchouli](https://gitlab.com/yukidama/patchouli) (?)
    - TPS65-201A-S (IQS550/572/525-B000)
  - trackpoint modules (sprintek SK8707-06)
  - trackball modules?
- display modules
  - What will be the controls for this display?
- power electronics circuits
- Haptic Feedback Modules

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

 
Daycare Service

Divine Dreamers LLC.

What is a website vs what is a social media presence

Tasks:
digital presense

Wiatlist and blog
