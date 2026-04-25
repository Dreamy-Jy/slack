#

## Plan

We'll to add battery circuitry
We'll need to add programming circuitry

## Further Study

- Source: Encoder Filters - Rotary Encoders require a low pass filter.
  - RC circuits
  - Electronic Filters: Why, When, How
- Source: Switch Matrix Diodes: Why

- Source: MCU Module Configuration
  - Why are there 2 oscillators 32 mHz (XC) and 32.768 kHz (XL)? Why is one optional?
    - This is some what covered in Chapter 5.4
    - The chip has 2 clocks, with one being for optional precise functionality (real time)
    - External Crystals, Internal Oscillators, feed into the PMU
  - What is the effect of the range of electrical properties (voltage, current etc.) on the device's function.
  - What is the difference been operating the chip at normal and high voltage modes?
  - Power: what are LDO and DC/DC regulators
  - Power: why have a multistage power regulator?
    - Stage 1 (REG0) is only used in high voltage mode
    - LDO (Low Drop Out) or DC/DC(Buck) regulator
    - LDO is the default
    - you can power external circuitry with VDD. We won't do this.
    - Whats the difference between using 5v and 3v? (i think I'll be using the chip in normal voltage mode )
  - 2 power systems
  - 2 clock systems
- Source: Power/USB-C
  - When possible use simplified usb-c ports.
