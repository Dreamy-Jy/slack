# DRV2605L Haptic Driver Implementation

## Summary
Implement a modern Rust driver for the DRV2605L haptic motor controller using `embedded-hal` v1 traits. The driver will support I2C communication, register access, calibration, waveform playback from ROM library, and real-time playback (RTP) mode for both ERM and LRA actuators.

## Current State
- **Project**: Custom mechanical keyboard ("Slack") in planning phase
- **Language**: Rust with `embedded-hal` v1
- **Target**: MCU not yet selected
- **Existing Reference**: `drv2605l-rs` driver (outdated, uses old `embedded-hal` and `bitfield` versions)
- **Hardware**: DRV2605L haptic driver listed as experimental module for post-revision-one
- **Datasheet**: Available at `documents/datasheets/DRV2605LYZFT.pdf`
- **No firmware code exists yet** — this is a greenfield implementation

## Steps

### Phase 1: Project Setup and Register Definitions

- [ ] **Step 1.1: Create driver crate structure**
  - **Files**: `src/drv2605l/mod.rs`, `src/drv2605l/registers.rs`, `Cargo.toml` (create or modify)
  - **What**: Set up Rust crate structure for the DRV2605L driver module
  - **Why**: Establish foundation for driver implementation
  - **Details**:
    - Add dependencies: `embedded-hal = "1.0"`, `bitfield = "0.14"` (or latest)
    - Create module hierarchy: `drv2605l/` containing `mod.rs`, `registers.rs`, `types.rs`
    - Export public API from `mod.rs`

- [ ] **Step 1.2: Define register addresses and bitfields**
  - **File**: `src/drv2605l/registers.rs` (create)
  - **What**: Define all DRV2605L register addresses and bitfield structures
  - **Why**: Type-safe register access using Rust's type system
  - **Details**:
    - Register addresses (from datasheet section 8.6):
      - `STATUS = 0x00` (bits: DIAG_RESULT, OVER_TEMP, OC_DETECT)
      - `MODE = 0x01` (bits: DEV_RESET, STANDBY, MODE[2:0])
      - `RTP_INPUT = 0x02` (8-bit RTP data)
      - `LIBRARY_SEL = 0x03` (bits: HI_Z, LIBRARY_SEL[2:0])
      - `WAVEFORM_SEQ_1..8 = 0x04..0x0B` (bits: WAIT, WAV_FRM_SEQ[6:0])
      - `GO = 0x0C` (bit: GO)
      - `OVERDRIVE_OFFSET = 0x0D`, `SUSTAIN_POS_OFFSET = 0x0E`, `SUSTAIN_NEG_OFFSET = 0x0F`, `BRAKE_OFFSET = 0x10`
      - `RATED_VOLTAGE = 0x16`, `OD_CLAMP = 0x17`
      - `FEEDBACK_CONTROL = 0x1A` (bits: N_ERM_LRA, FB_BRAKE_FACTOR[2:0], LOOP_GAIN[1:0], BEMF_GAIN[1:0])
      - `CONTROL1 = 0x1B`, `CONTROL2 = 0x1C`, `CONTROL3 = 0x1D` (bits: N_PWM_ANALOG, LRA_OPEN_LOOP, ERM_OPEN_LOOP, etc.)
      - `CONTROL4 = 0x1E` (bits: OTP_PROGRAM, OTP_STATUS), `CONTROL5 = 0x1F`
      - `VBAT_MONITOR = 0x21`, `LRA_PERIOD = 0x22`
    - Use `bitfield!` macro for register bitfield definitions
    - Define enums for mode selection, library selection, actuator type

- [ ] **Step 1.3: Define driver types and enums**
  - **File**: `src/drv2605l/types.rs` (create)
  - **What**: Define public types, enums, and constants
  - **Why**: Provide type-safe API for driver configuration
  - **Details**:
    - `ActuatorType` enum: `ERM`, `LRA`
    - `Mode` enum: `InternalTrigger`, `ExternalEdge`, `ExternalLevel`, `PwmAnalog`, `AudioToVibe`, `RealTimePlayback`, `Diagnostics`, `AutoCalibration`
    - `Library` enum: `Empty`, `TS2200_A`, `TS2200_B`, `TS2200_C`, `TS2200_D`, `TS2200_E`, `LRA`, `TS2200_F`
    - `LoopMode` enum: `OpenLoop`, `ClosedLoop`
    - `Error` enum: `I2cError`, `CalibrationFailed`, `DiagnosticFailed`, `InvalidConfig`
    - Constants: `I2C_ADDRESS = 0x5A` (7-bit address from datasheet)

### Phase 2: Core Driver Implementation

- [ ] **Step 2.1: Implement driver struct and initialization**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Create main `Drv2605l` struct with I2C interface
  - **Why**: Provide core driver structure for all operations
  - **Details**:
    - Generic over I2C bus: `Drv2605l<I2C> where I2C: embedded_hal::i2c::I2c`
    - Constructor: `new(i2c: I2C) -> Self`
    - `init()` method: Clear STANDBY bit, verify device communication by reading STATUS register
    - Store I2C instance and device state
    - Device I2C address: `0x5A` (fixed, no address pins on DRV2605L)

- [ ] **Step 2.2: Implement register read/write methods**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Low-level register access methods
  - **Why**: Foundation for all device operations
  - **Details**:
    - `write_register(&mut self, reg: u8, value: u8) -> Result<(), Error>`
    - `read_register(&mut self, reg: u8) -> Result<u8, Error>`
    - `modify_register(&mut self, reg: u8, mask: u8, value: u8) -> Result<(), Error>`
    - Use `i2c.write(I2C_ADDRESS, &[reg, value])` and `i2c.write_read(I2C_ADDRESS, &[reg], &mut buf)`
    - Map I2C errors to driver `Error::I2cError`

- [ ] **Step 2.3: Implement device control methods**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: High-level device control API
  - **Why**: Provide user-friendly interface for common operations
  - **Details**:
    - `reset(&mut self) -> Result<(), Error>`: Set DEV_RESET bit in MODE register (0x01)
    - `standby(&mut self, enable: bool) -> Result<(), Error>`: Set/clear STANDBY bit
    - `set_mode(&mut self, mode: Mode) -> Result<(), Error>`: Write MODE[2:0] bits
    - `set_actuator_type(&mut self, actuator: ActuatorType) -> Result<(), Error>`: Set N_ERM_LRA bit in FEEDBACK_CONTROL (0x1A)
    - `set_library(&mut self, library: Library) -> Result<(), Error>`: Write LIBRARY_SEL register (0x03)
    - `get_status(&mut self) -> Result<u8, Error>`: Read STATUS register (0x00)

### Phase 3: Waveform Playback and RTP Mode

- [ ] **Step 3.1: Implement waveform sequencer**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Methods for ROM library waveform playback
  - **Why**: Enable pre-programmed haptic effects from device ROM
  - **Details**:
    - `set_waveform(&mut self, slot: u8, waveform_id: u8) -> Result<(), Error>`: Write to WAVEFORM_SEQ registers (0x04-0x0B), slot 0-7
    - `set_waveform_sequence(&mut self, waveforms: &[u8]) -> Result<(), Error>`: Write multiple waveforms, auto-terminate with 0x00
    - `insert_delay(&mut self, slot: u8, delay_ms: u8) -> Result<(), Error>`: Set WAIT bit and delay value (delay = 10ms × value)
    - `play(&mut self) -> Result<(), Error>`: Set GO bit (register 0x0C) to start playback
    - `stop(&mut self) -> Result<(), Error>`: Clear GO bit to cancel playback
    - `is_playing(&mut self) -> Result<bool, Error>`: Read GO bit status

- [ ] **Step 3.2: Implement real-time playback (RTP) mode**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Real-time waveform streaming via I2C
  - **Why**: Allow custom haptic effects generated by host processor
  - **Details**:
    - `set_rtp_input(&mut self, value: u8) -> Result<(), Error>`: Write to RTP_INPUT register (0x02)
    - `enable_rtp_mode(&mut self) -> Result<(), Error>`: Set MODE to RealTimePlayback (5), clear STANDBY
    - `set_data_format(&mut self, signed: bool) -> Result<(), Error>`: Set DATA_FORMAT_RTP bit in CONTROL3 (0x1D)
    - RTP value interpretation depends on loop mode (see datasheet section 8.5.8.1)
    - Streaming: repeatedly call `set_rtp_input()` with new values

- [ ] **Step 3.3: Implement loop mode configuration**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Configure open-loop vs closed-loop operation
  - **Why**: Different actuators require different control strategies
  - **Details**:
    - `set_loop_mode(&mut self, mode: LoopMode) -> Result<(), Error>`:
      - For ERM: set ERM_OPEN_LOOP bit in CONTROL3 (0x1D)
      - For LRA: set LRA_OPEN_LOOP bit in CONTROL3 (0x1D)
    - `set_rated_voltage(&mut self, voltage_mv: u16) -> Result<(), Error>`: Calculate and write RATED_VOLTAGE register (0x16)
      - Formula: `RATED_VOLTAGE = voltage_mv / 21.2` (from datasheet section 8.5.10.1)
    - `set_overdrive_clamp(&mut self, voltage_mv: u16) -> Result<(), Error>`: Calculate and write OD_CLAMP register (0x17)
      - Formula: `OD_CLAMP = voltage_mv / 21.2`

### Phase 4: Auto-Calibration and Diagnostics

- [ ] **Step 4.1: Implement auto-calibration**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Automatic actuator calibration routine
  - **Why**: Optimize performance for specific actuator characteristics
  - **Details**:
    - `calibrate(&mut self, config: CalibrationConfig) -> Result<CalibrationResult, Error>`:
      1. Set MODE to AutoCalibration (7)
      2. Configure input parameters (from datasheet section 8.5.6):
         - `FB_BRAKE_FACTOR = 2` (default)
         - `LOOP_GAIN = 2` (default)
         - `RATED_VOLTAGE` (user-provided)
         - `OD_CLAMP` (user-provided)
         - `AUTO_CAL_TIME = 3` (default)
         - `DRIVE_TIME` (calculated from actuator resonant frequency)
         - `SAMPLE_TIME = 3`, `BLANKING_TIME = 1`, `IDISS_TIME = 1`, `ZC_DET_TIME = 0`
      3. Set GO bit to start calibration
      4. Poll GO bit until clear (calibration complete)
      5. Read STATUS register, check DIAG_RESULT bit
      6. If successful, read calibration results: `A_CAL_COMP`, `A_CAL_BEMF` registers
      7. Return `CalibrationResult` struct with results
    - `CalibrationConfig` struct: rated_voltage, overdrive_clamp, drive_time
    - `CalibrationResult` struct: success, comp_result, bemf_result

- [ ] **Step 4.2: Implement diagnostics**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Actuator diagnostic test
  - **Why**: Verify actuator is connected and functioning
  - **Details**:
    - `run_diagnostics(&mut self) -> Result<DiagnosticResult, Error>`:
      1. Set MODE to Diagnostics (6)
      2. Set GO bit
      3. Poll GO bit until clear
      4. Read STATUS register, check DIAG_RESULT bit
      5. Return result: `DiagnosticResult::Pass` or `DiagnosticResult::Fail`
    - Check for OVER_TEMP and OC_DETECT flags in STATUS register
    - Return detailed error information

- [ ] **Step 4.3: Implement battery voltage monitoring**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: Read supply voltage during operation
  - **Why**: Monitor battery level for power management
  - **Details**:
    - `read_supply_voltage(&mut self) -> Result<u16, Error>`: Read VBAT_MONITOR register (0x21)
    - Convert to millivolts: `voltage_mv = (vbat_value * 5600) / 255` (from datasheet section 8.3.8)
    - Only valid during playback

### Phase 5: Advanced Features and Examples

- [ ] **Step 5.1: Implement OTP memory programming**
  - **File**: `src/drv2605l/mod.rs` (modify)
  - **What**: One-time programmable memory for calibration storage
  - **Why**: Persist calibration across power cycles
  - **Details**:
    - `program_otp(&mut self) -> Result<(), Error>`:
      1. Verify VDD is 4.0-4.4V (document requirement, cannot verify in software)
      2. Set OTP_PROGRAM bit in CONTROL4 register (0x1E)
      3. Wait for completion
      4. Read OTP_STATUS bit to verify
    - **WARNING**: Can only be programmed once — document clearly in API
    - `is_otp_programmed(&mut self) -> Result<bool, Error>`: Read OTP_STATUS bit

- [ ] **Step 5.2: Add builder pattern for configuration**
  - **File**: `src/drv2605l/builder.rs` (create)
  - **What**: Fluent API for driver configuration
  - **Why**: Improve ergonomics for complex initialization
  - **Details**:
    - `Drv2605lBuilder` struct with methods:
      - `with_actuator(actuator: ActuatorType)`
      - `with_library(library: Library)`
      - `with_rated_voltage(voltage_mv: u16)`
      - `with_overdrive_clamp(voltage_mv: u16)`
      - `with_loop_mode(mode: LoopMode)`
      - `build(i2c: I2C) -> Result<Drv2605l<I2C>, Error>`
    - Initialize device with all settings in `build()`

- [ ] **Step 5.3: Create usage examples**
  - **File**: `examples/basic_playback.rs`, `examples/rtp_mode.rs`, `examples/calibration.rs` (create)
  - **What**: Example code demonstrating driver usage
  - **Why**: Help users understand how to use the driver
  - **Details**:
    - `basic_playback.rs`: Initialize driver, select library, play waveform sequence
    - `rtp_mode.rs`: Stream custom waveform data via RTP mode
    - `calibration.rs`: Run auto-calibration and store results
    - Use `#[cfg(feature = "std")]` for examples that need std (or use `no_std` compatible examples)
    - Document hardware setup requirements (I2C pins, actuator connection)

- [ ] **Step 5.4: Add documentation and tests**
  - **File**: `src/drv2605l/mod.rs`, `README.md`, `tests/` (modify/create)
  - **What**: Comprehensive documentation and unit tests
  - **Why**: Ensure code quality and usability
  - **Details**:
    - Add rustdoc comments to all public APIs
    - Document register addresses and bit meanings
    - Add usage examples in doc comments
    - Create `README.md` with quick start guide
    - Unit tests for register calculations (voltage conversions, etc.)
    - Integration tests with mock I2C (using `embedded-hal-mock`)

## Files Involved

| File | Action | Purpose |
|------|--------|---------|
| `Cargo.toml` | Create/Modify | Add dependencies: `embedded-hal`, `bitfield` |
| `src/drv2605l/mod.rs` | Create | Main driver implementation |
| `src/drv2605l/registers.rs` | Create | Register addresses and bitfield definitions |
| `src/drv2605l/types.rs` | Create | Public types, enums, error types |
| `src/drv2605l/builder.rs` | Create | Builder pattern for configuration |
| `examples/basic_playback.rs` | Create | Example: ROM library waveform playback |
| `examples/rtp_mode.rs` | Create | Example: Real-time playback mode |
| `examples/calibration.rs` | Create | Example: Auto-calibration procedure |
| `README.md` | Create | Driver documentation and quick start |
| `tests/register_tests.rs` | Create | Unit tests for register operations |

## Open Questions

1. **MCU Selection**: Which MCU will be used for the final keyboard? This affects I2C peripheral configuration in examples.
   - **Impact**: Examples will need to be generic or provide multiple MCU-specific examples
   - **Resolution**: Use generic `embedded-hal` traits in driver, provide MCU-specific examples later

2. **Actuator Type**: Will you use ERM or LRA actuators for haptic feedback?
   - **Impact**: Determines default calibration parameters and library selection
   - **Resolution**: Driver supports both, but examples should demonstrate the chosen type

3. **Power Supply Voltage**: What will VDD be in the final design?
   - **Impact**: Affects rated voltage and overdrive clamp calculations
   - **Resolution**: Document voltage range (2.0-5.2V per datasheet), examples use 3.3V typical

4. **OTP Programming**: Will calibration values be stored in OTP or loaded from host?
   - **Impact**: Determines initialization sequence
   - **Resolution**: Provide both options, document OTP is one-time only

5. **Integration with Keyboard Firmware**: How will haptic feedback be triggered (key press, layer change, etc.)?
   - **Impact**: Determines which playback modes are most important
   - **Resolution**: Driver provides all modes, application layer decides usage

## Implementation Notes

- **I2C Speed**: DRV2605L supports standard (100 kHz) and fast mode (400 kHz) I2C
- **EN Pin**: Must be pulled high before I2C communication (document in examples)
- **Startup Time**: Allow 250μs after EN goes high before I2C access (datasheet section 6.6)
- **Watchdog Timer**: I2C watchdog resets protocol after 4.33ms of inactivity (except in standby)
- **Register Retention**: Registers retain values in standby mode and when EN is low (except after DEV_RESET)
- **Thermal Protection**: Device shuts down if overheated, sets OVER_TEMP flag
- **Overcurrent Protection**: Device shuts down on output short, sets OC_DETECT flag
- **Library Compatibility**: TS2200 Library A (with overdrive) only works in open-loop mode; Libraries B-F work in both modes
- **Closed-Loop Requirements**: Requires calibration for optimal performance
- **LRA Frequency Range**: Supports 125-300 Hz resonant frequency (datasheet section 6.3)

## References

- **Datasheet**: `documents/datasheets/DRV2605LYZFT.pdf`
- **Existing Driver**: https://github.com/jacobrosenthal/drv2605l-rs (reference for API design)
- **embedded-hal**: https://github.com/rust-embedded/embedded-hal
- **Application Note**: TI SLOA189 "DRV2605 Setup Guide"
