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