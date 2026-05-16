# BQ25186 vs BQ25185: Charger IC Comparison

What should I care about?

- In the worst case scenario my power system will not fail.
  - How do I find the worst case scenario?
  - Is current the only thing to be worried about?

How to calculate power budget?

Automated Power Budget Calculations

## Power Budget

### RGBW LED: **LTST-FC12WEGBD-5A**
Theoretical Max Continious Current:
2 * (42 * (4 * 20 mA)) = 6.72 A

Theoretical Max Instaneous Current:
2 * (42 * (3 * 75 mA + 50 mA)) = 23.1 A

Realistic Current:
2 * (42 * (4 * 5 mA)) = 1.68 A
- 5 mA was choosen as that is the current binning occured.


#### Definitions
Peak Forward Current (1/10 Duty Cycle, 0.1ms Pulse Width [what does this mean???]) - 40 mA RED Channel, 75 mA All Other Channels.
DC Forward Current - 20 mA all Channel (20 * 4)
Power Dissipation [what does this mean???] - 50 mW RED Channel, 76 mW All Other Channels.

Power Dissipation - heat generated?? is this usable.
Peak Forward Current - the max instantious current we should have running through the LED.
    (1/10 Duty Cycle, 0.1ms Pulse Width)
DC Forward Current - the max continuous current we should have running through the LED. 

Depending on how the matrix works we'll use I_PFC or I_DCFC.

Binning Current Is done at 5mA forward current.
The LEDs are very sensitive to heat. (we'll plan for max 60°C temp)

---
Operating Temperature Range
Storage Temperature Range 
Infrared Soldering Condition 

Luminous Intensity
Viewing Angle 
Peak Emission Wavelength 
Dominant Wavelength
Spectral Line Half-Width 
Chromaticity Coordinates 
Forward Voltage
Reverse Current 

 - 
 - 
 - 
 - 
 - 


- RED, BLUE, GREEN, & WHITE.

### LED Matrix IC: **IS31FL3733**

I don't know how the Matrix works:

- what is scan time, how does that effect PWM
- It's a PWM driver

Choosen settings:

- I_led = 5 mA
- I_out = (5mA x 256)/(Duty x PWM) = 64 mA
- R_ext = (840 x GCC)/(I_out x 256) = 13 kΩ

per chip 1024 mA 1.024 A, so 2 A to 2.5 A

### Charger IC: **BQ25185**
### Charger IC: **BQ25186**


Select the brightness of the LEDs.
**Luminous Intensity** - intensity of light weighted by human vision.
**Viewing Angle** - the angle at which you can see the light to a reasonable amount.
**Peak Emission Wavelength** - 
**Dominant Wavelength** - 
**Spectral Line Half-Width** - ??the amount of light emmissions that are significant for vision¿¿
**Chromaticity Coordinates** - ??hue and saturation independent of brightness¿¿
**Forward Voltage** - 
**Reverse Current** - how much current flowes when biased in the opposite direction.

**LED Binning** -


4 hrs - Pick a light range target, Pick a light correction method, Pick matrix and Charger characteristics

- (targetting +50 mcd) so now the question is how much less than 5mA can we go?
- s

Start Content Creation.

Matrx functionality

I_out = (840/R_ext)(GCC/256)

Duty = 1/12.75

I_led = (PWM/256)(I_out)(Duty)

I_led = 5 mA

I_out = (5mA x 256)/(Duty x PWM) = 64 mA

R_ext = (840 x GCC)/(I_out x 256) = 13 kΩ


Assume 50 mA for the cpu.

USB PD - 5 A, 48 V

BQ25690
BQ25898C

BQ25622E x (3 A)
BQ25622 x (3.5 A) (ic thermal regulation)
BQ25620 x (3.5 A)
BQ25640 x (5 A)
BQ25690
BQ25895

3 A system X

- Charger IC
  - BQ25622E

5 A system

- Charger IC
  - BQ25640 *(not available for purchase)
  - BQ25890
  - MP2721 *
- Voltage Regulator
  - TPS61288 *
  - MP3432
  - TPS61288, MP3432, MP3437, ~~LTC3789~~ , TPS43060
  - ??TPS6123x, TPS61088, MP3429, LTC3124¿¿
  - Manufacter:
    - Texas Instruments
    - Monolithic Power Systems
    - Analog Devices

Agent for helping with hardware engineering
- help with the selection components (Optimize the BOM)
- feature listing (are the feautures togglable)
- have determintic list of all manufactures and their product catalogues.


BOM Management

Not 5A: BQ25896, BQ25601

BQ25640 (not available)
BQ25895
MP2721
- Inductor
  - L = ((V_in - V_sys)÷ΔI_l_max) ✕ (V_sys÷(V_in ✕ f_sw))
  - 
- PMID Capacitor

Voltage Multiplier
Voltage Divider
Charge Pump
Switching regulator
