1. [x] confirm which components can be soldered by the manufacturer.
2. [x] select latching buttons.
3. [x] confirm that I can send in parts for assembly by JLC PCB

---

1. [ ] Select a keyboard layout. (Add all the ergonomic features you want)
2. [ ] implement and publish expected modules
  - [ ] LED matrix (IS31FL3741)
3. [ ] implement and publish experimental modules
  - [ ] Track Pad (IQS550, PCT3854QR)
  - [ ] Track Point (SK8707-06)
  - [ ] Haptics (DRV2605L, DRV8830)
  - [ ] Screen (select a screen)
4. [ ] design version 1 keyboard hardware design
5. [ ] design all experimental modules

- Update LED Matrix Driver (IS31FL3741)
  - [ ] add fine grain configuration logic. (global current is one)
  - [ ] add fault detection functionality
  - [ ] add fine grain fault detection logic
  - [ ] update the dependencies of `embedded-graphics-core`

what sequence do i need to change global current?

Unlock Command Register (write 11000101b to FEh)
Select The Configuration (write x04 to FDh)
Select Global Current Register (write 01h to FDh)
Write Global Current Register Value (write to FDh)

You'll need to tune the LED colors on your actual keyboard pcb.

-> we need to select a layout for the keyboard

Plank or split?

---

## Hardware

### [ ] Switch Matrix

1. [ ] select values for Rotary Encoder Filters: resistors and capacitors.

### [ ] Led Matrix

### [ ] Microcontroller

### [ ] Power Circuits


I need to define power circuitry
Select a configuration for the mcu.


I need to create the power block of my schematic.
The power block needs to expose a 3.3v (for mcu) line and 5.5v line (for led driver).
The power should allow for running and battery charging from a USB-C cable when plugged in and running from a battery when.
I should have indicator lights for charging, full charge, operating(on), and low power.

what is the cost of using the internal crystal vs external crystal.

VDD - power supply
VDDH - High voltage power supply
VSS - ground
VSS_PA - ground (for radio supply)
ANT - antenna single ended
NFC1, NFC2 - NFC antenna connection
TRACECLK  trace clock (what is this)
TRACEDATA 0..3 - trace data what is this?
DECUSB - usb 3.3v regulator supply decoupling
nRESET - reset pin
VBUS - 5V input for usb 3.3v regulator
SWDIO - serial wire debug i/o for debug and programming

XC2, XC1, XL1, Xl2
What are the `regulator supply decoupling` (1.1v, 1.3v) Pins: DEC
DCC - DC/DC converter output

DCCH - DC/DC converter output

Pre Kids
- set up a warobe and lifestyle