# Plan: Update embedded-graphics-core Dependency

**Goal**: Update `embedded-graphics-core` from 0.4.0 to 0.4.1 in the is31fl3741-rs driver

**Scope**: Dependency version bump only — no new features

---

## Phase 1: Update Dependencies

- [x] **Step 1.1**: Update `embedded-graphics-core` in `drivers/is31fl3741-rs/Cargo.toml` from `0.4.0` to `0.4.1`
- [x] **Step 1.2**: Update `embedded-graphics-core` in example projects:
  - `drivers/is31fl3741-rs/examples/adafruit_rgb/Cargo.toml` (inherits from `embedded-graphics`)
  - `drivers/is31fl3741-rs/examples/ledmatrix/Cargo.toml` (inherits from `embedded-graphics`)
- [x] **Step 1.3**: Run `cargo update` in `drivers/is31fl3741-rs/` to refresh `Cargo.lock`

---

## Phase 2: Verify Build

- [x] **Step 2.1**: Build the main driver library: `cargo build --manifest-path drivers/is31fl3741-rs/Cargo.toml`
- [x] **Step 2.2**: Build the adafruit_rgb example: `cargo build --manifest-path drivers/is31fl3741-rs/examples/adafruit_rgb/Cargo.toml`
- [x] **Step 2.3**: Build the ledmatrix example: `cargo build --manifest-path drivers/is31fl3741-rs/examples/ledmatrix/Cargo.toml`

---

## Phase 3: Test & Finalize

- [x] **Step 3.1**: Run `cargo check --all-features` in `drivers/is31fl3741-rs/`
- [x] **Step 3.2**: Verify no breaking changes in the `embedded-graphics-core` 0.4.0 → 0.4.1 changelog (patch version should be compatible)
- [x] **Step 3.3**: Bump driver version in `drivers/is31fl3741-rs/Cargo.toml` from `0.4.0` to `0.4.1` (patch bump for dependency update)

---

**Next Steps After This Plan**: Create separate plans for error detection and interrupt pin features.
