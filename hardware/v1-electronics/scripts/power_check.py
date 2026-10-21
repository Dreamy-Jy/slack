import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import math
    from types import SimpleNamespace as NS

    import marimo as mo
    import numpy as np

    return NS, math, mo, np


@app.cell
def _(mo):
    mo.md(r"""
    # Slack power system check

    **USB-C → charger (MP2721) → load switch (Q1) → 5 V boost (TPS61288) → load**<br>
    **battery ↗**

    Set the input source, the battery and the load at the top. Every check below shows the
    **ideal** value worked out from the datasheet next to **your** value, so you can try other
    parts while the ideal stays visible.

    Datasheets: TPS61288 (SLVSFP3C), MP2721 (Rev. 1.1), AON7423. Values marked *est.* are
    assumptions you should replace with real numbers when you have them.
    """)
    return


@app.cell
def _(NS):
    # ---------------------------------------------------------------- datasheet numbers
    # Every number here comes from a datasheet; the comment says where.
    TPS = NS(  # TPS61288 boost, SLVSFP3C
        fsw_min=440e3,
        fsw_typ=500e3,
        fsw_max=600e3,  # §7.5 switching frequency
        ilim_min=12.0,
        ilim_typ=15.0,
        ilim_max=17.1,  # §7.5 peak current limit (A)
        vref_min=0.588,
        vref=0.600,
        vref_max=0.612,  # §7.5 FB reference (V)
        gm=180e-6,  # §7.5 error amp transconductance (S)
        kcomp=13.5,  # §7.5 power stage transconductance (A/V)
        l_min=1.0e-6,
        l_max=4.7e-6,  # §9.2.2.2 supported inductor range
        uvlo_rise=2.4,
        uvlo_fall=1.9,  # §7.5 input UVLO max rising / typ falling (V)
        ton_min=110e-9,  # §7.5 minimum on-time, max (s)
        iq_vout=110e-6,  # §7.5 quiescent current from VOUT (A)
        r2_needs_c6=15e3,  # §9.2.2.1 add 27 pF across R2 above this
    )
    MP = NS(  # MP2721 charger, Rev. 1.1
        vin_rec_min=3.9,
        vin_rec_max=16.0,
        vin_abs_max=26.0,  # recommended operating / abs max (V)
        ovp_options={"6.3 V": 6.3, "11 V": 11.0, "14 V": 14.0},  # input OVP settings
        headroom=0.24,  # VIN must exceed VBATT by this (typ, V)
        iin_max=3.2,  # recommended max input current (A)
        icc_step=0.08,
        icc_max=5.0,  # charge current step / max (A)
        r_battfet=14e-3,  # BATT-SYS switch on resistance (Ω)
        vtrack=0.15,  # SYS sits this far above SYS_MIN (V)
        battfet_ocp=7.0,  # battery discharge trip (A)
        batt_uv=2.5,  # battery undervoltage lockout (V)
        vcc=3.65,  # VCC LDO output, typ (V); only with USB present
        vpre=3.0,
        ipre=0.24,  # pre-charge threshold and current (defaults)
        fsw_options={
            "750 kHz": (630e3, 750e3),
            "1 MHz": (900e3, 1050e3),
            "1.25 MHz": (1060e3, 1250e3),
            "1.5 MHz": (1260e3, 1475e3),
        },  # (min, typ)
        # Pin table p.6: what each capacitor must be
        cap_in=1e-6,
        cap_pmid=10e-6,
        cap_sys=20e-6,
        cap_batt=20e-6,
        cap_vcc=4.7e-6,
        cap_bst=22e-9,
        # JEITA NTC thresholds as a fraction of VRNTC and the temperature MPS designed them for
        ntc=[
            ("cold", 0.742, 0),
            ("cool", 0.648, 10),
            ("warm", 0.326, 45),
            ("hot", 0.230, 60),
        ],
        led_sink_max=10e-3,  # STAT / PG pins: 0.2 V max at 10 mA
    )
    Q1 = NS(  # AON7423 P-channel load switch
        vgs_max=8.0,
        vth_max=0.9,
        # max RDS(on) vs gate drive |VGS| (V -> Ω)
        rds_table=[(1.5, 11e-3), (1.8, 8.5e-3), (2.5, 6.5e-3), (4.5, 5e-3)],
        gate_leak_max=100e-9,
        ciss=5626e-12,
    )
    LED_DRIVER = NS(  # IS31FL3733, from your charger-ic-comparison notes: I_OUT = 840 / R_EXT × GCC/256
        k=840.0,
        outputs_per_chip=16,
        chips=2,
    )
    OTHER = (
        NS(  # parts on the same nets that limit the input voltage (from memory, verify)
            nrf_vbus_max=5.5,  # nRF52840 VBUS pin, recommended max (V)
            usblc6_vbus_max=5.25,  # D0 USBLC6-2SC6 working voltage (V)
        )
    )
    return LED_DRIVER, MP, OTHER, Q1, TPS


@app.cell
def _():
    # ---------------------------------------------------------------- USB input options
    # volts, amps the source can give, what the MP2721's D+/D- detection calls it and the input
    # current limit it then sets (MP2721 table 2), and what firmware could set by reading CC.
    USB = {
        "USB 2.0 port (SDP)": dict(
            v=5.0, i=0.5, detect="SDP", iin_auto=0.5, iin_cc=0.5
        ),
        "USB 3.x port (SDP)": dict(
            v=5.0, i=0.9, detect="SDP", iin_auto=0.5, iin_cc=0.9
        ),
        "BC1.2 charging port (CDP)": dict(
            v=5.0, i=1.5, detect="CDP", iin_auto=1.5, iin_cc=1.5
        ),
        "BC1.2 wall charger (DCP)": dict(
            v=5.0, i=1.5, detect="DCP", iin_auto=2.0, iin_cc=1.5
        ),
        "Apple-style 1 A": dict(
            v=5.0, i=1.0, detect="Divider 1", iin_auto=1.0, iin_cc=1.0
        ),
        "Apple-style 2.1 A": dict(
            v=5.0, i=2.1, detect="Divider 2", iin_auto=2.1, iin_cc=2.1
        ),
        "Apple-style 2.4 A": dict(
            v=5.0, i=2.4, detect="Divider 3", iin_auto=2.4, iin_cc=2.4
        ),
        "USB-C default current": dict(
            v=5.0, i=0.9, detect="Unknown", iin_auto=0.5, iin_cc=0.9
        ),
        "USB-C 1.5 A": dict(v=5.0, i=1.5, detect="Unknown", iin_auto=0.5, iin_cc=1.5),
        "USB-C 3.0 A": dict(v=5.0, i=3.0, detect="Unknown", iin_auto=0.5, iin_cc=3.0),
        # USB-PD is handled separately below: 5–48 V at 3 or 5 A, but only after a PD controller
        # negotiates. Without one the source stays at 5 V with its USB-C advertisement.
        "USB-PD charger": dict(
            v=5.0, i=3.0, detect="Unknown", iin_auto=0.5, iin_cc=3.0
        ),
        "Free form": None,
    }
    PD_VOLTS = [
        5,
        9,
        15,
        20,
        28,
        36,
        48,
    ]  # PD fixed voltages (SPR up to 20 V, EPR 28–48 V)
    return PD_VOLTS, USB


@app.cell
def _(PD_VOLTS, USB, mo):
    # ---------------------------------------------------------------- inputs: source
    src = mo.ui.dropdown(options=list(USB), value="USB-C 3.0 A", label="Source")
    usb_on = mo.ui.switch(value=True, label="USB plugged in")
    cc_fw = mo.ui.switch(
        value=False, label="Firmware reads CC and sets the input limit"
    )
    cable_r = mo.ui.number(
        start=0.0,
        stop=2.0,
        step=0.01,
        value=0.2,
        label="Cable + connector resistance, round trip (Ω)",
    )
    pd_v = mo.ui.dropdown(
        options=[str(v) for v in PD_VOLTS],
        value="20",
        label="PD voltage the charger offers (V)",
    )
    pd_i = mo.ui.dropdown(
        options=["3", "5"],
        value="3",
        label="PD current (A, 5 A needs an e-marked cable)",
    )
    pd_ctrl = mo.ui.switch(
        value=False, label="Board has a PD controller (it doesn't today)"
    )
    free_v = mo.ui.number(
        start=0.0, stop=48.0, step=0.1, value=5.0, label="Free form: volts"
    )
    free_i = mo.ui.number(
        start=0.0, stop=5.0, step=0.1, value=1.0, label="Free form: amps"
    )
    mo.vstack(
        [
            mo.md("## Input source"),
            mo.hstack([src, usb_on, cc_fw]),
            cable_r,
            mo.md("*USB-PD only:*"),
            mo.hstack([pd_v, pd_i, pd_ctrl]),
            mo.md("*Free form only:*"),
            mo.hstack([free_v, free_i]),
        ]
    )
    return cable_r, cc_fw, free_i, free_v, pd_ctrl, pd_i, pd_v, src, usb_on


@app.cell
def _(mo):
    # ---------------------------------------------------------------- inputs: battery
    bat_type = mo.ui.dropdown(
        options={"Li-ion / LiPo (4.2 V)": 4.2, "LiHV (4.35 V)": 4.35},
        value="Li-ion / LiPo (4.2 V)",
        label="Cell type",
    )
    bat_mah = mo.ui.number(
        start=100, stop=20000, step=50, value=2000, label="Capacity (mAh)"
    )
    bat_cut = mo.ui.number(
        start=2.5,
        stop=3.6,
        step=0.05,
        value=3.0,
        label="Cutoff: firmware shuts down at (V)",
    )
    bat_dis = mo.ui.number(
        start=0.1, stop=20.0, step=0.1, value=4.0, label="Max continuous discharge (A)"
    )
    bat_rate = mo.ui.number(
        start=0.1, stop=3.0, step=0.1, value=1.0, label="Max charge rate (C)"
    )
    bat_rint = mo.ui.number(
        start=0, stop=500, step=5, value=50, label="Internal resistance (mΩ, est.)"
    )
    bat_rwire = mo.ui.number(
        start=0, stop=200, step=1, value=15, label="Wires + XT30 + traces (mΩ, est.)"
    )
    bat_v = mo.ui.slider(
        start=3.0,
        stop=4.35,
        step=0.05,
        value=3.7,
        label="Battery voltage now (V)",
        show_value=True,
    )
    mo.vstack(
        [
            mo.md("## Battery"),
            mo.hstack([bat_type, bat_mah, bat_cut]),
            mo.hstack([bat_dis, bat_rate]),
            mo.hstack([bat_rint, bat_rwire]),
            bat_v,
        ]
    )
    return (
        bat_cut,
        bat_dis,
        bat_mah,
        bat_rate,
        bat_rint,
        bat_rwire,
        bat_type,
        bat_v,
    )


@app.cell
def _(MP, mo):
    # ---------------------------------------------------------------- inputs: charger registers
    icc = mo.ui.number(
        start=0.08,
        stop=5.0,
        step=0.08,
        value=2.0,
        label="Charge current ICC (A, default 2 A)",
    )
    iin_override = mo.ui.number(
        start=0.0,
        stop=3.2,
        step=0.1,
        value=0.0,
        label="Input limit IIN_LIM override (A, 0 = automatic)",
    )
    vin_lim = mo.ui.number(
        start=3.88,
        stop=5.08,
        step=0.08,
        value=4.36,
        label="Input voltage floor VIN_LIM (V)",
    )
    sys_min = mo.ui.dropdown(
        options={
            "2.975": 2.975,
            "3.325": 3.325,
            "3.5": 3.5,
            "3.588 (default)": 3.588,
            "3.763": 3.763,
        },
        value="3.588 (default)",
        label="SYS_MIN (V)",
    )
    chg_fsw = mo.ui.dropdown(
        options=list(MP.fsw_options), value="1 MHz", label="Charger switching frequency"
    )
    ovp = mo.ui.dropdown(options=list(MP.ovp_options), value="6.3 V", label="Input OVP")
    buck_eff = mo.ui.number(
        start=50, stop=99, step=1, value=90, label="Charger efficiency (% est.)"
    )
    mo.vstack(
        [
            mo.md("## Charger settings (MP2721 registers)"),
            mo.hstack([icc, iin_override]),
            mo.hstack([vin_lim, sys_min]),
            mo.hstack([chg_fsw, ovp, buck_eff]),
        ]
    )
    return buck_eff, chg_fsw, icc, iin_override, ovp, sys_min, vin_lim


@app.cell
def _(mo):
    # ---------------------------------------------------------------- inputs: load on the 5 V rail
    load_mode = mo.ui.dropdown(
        options=[
            "Worst case from the chats (13 kΩ, full brightness)",
            "LED drivers with R_EXT below",
            "Free form",
        ],
        value="Worst case from the chats (13 kΩ, full brightness)",
        label="Load",
    )
    r_ext = mo.ui.number(
        start=3000,
        stop=100000,
        step=100,
        value=22000,
        label="LED driver R_EXT (Ω, R41/R45)",
    )
    gcc = mo.ui.slider(
        start=1,
        stop=255,
        step=1,
        value=255,
        label="LED global current GCC (0–255)",
        show_value=True,
    )
    mcu_ma = mo.ui.number(
        start=0, stop=500, step=1, value=50, label="MCU and the rest (mA)"
    )
    free_load = mo.ui.number(
        start=0.0, stop=6.0, step=0.05, value=2.0, label="Free form load (A at 5 V)"
    )
    mo.vstack(
        [
            mo.md("## Load (5 V rail)"),
            load_mode,
            mo.hstack([r_ext, gcc]),
            mo.hstack([mcu_ma, free_load]),
        ]
    )
    return free_load, gcc, load_mode, mcu_ma, r_ext


@app.cell(expand_output=True)
def _(mo):
    # ---------------------------------------------------------------- inputs: your parts and targets
    # Defaults are the values on power.kicad_sch (and C21/C26 on the LED sheets).
    tgt_ripple = mo.ui.number(
        start=5, stop=500, step=5, value=50, label="Boost ripple target (mV)"
    )
    tgt_eff = mo.ui.number(
        start=50, stop=99, step=1, value=85, label="Boost efficiency to plan with (%)"
    )
    l_tol = mo.ui.number(
        start=0, stop=40, step=5, value=30, label="Inductor tolerance (−%)"
    )
    l2 = mo.ui.number(start=0.5, stop=10, step=0.1, value=2.2, label="L2 (µH)")
    l2_isat = mo.ui.number(
        start=1, stop=40, step=0.1, value=13.2, label="L2 saturation (A)"
    )
    l2_dcr = mo.ui.number(start=0, stop=50, step=0.5, value=7, label="L2 DCR (mΩ)")
    r50 = mo.ui.number(
        start=100, stop=1e6, step=100, value=22000, label="R50, FB top (Ω)"
    )
    r55 = mo.ui.number(
        start=100, stop=1e6, step=100, value=3000, label="R55, FB bottom (Ω)"
    )
    rc = mo.ui.number(start=100, stop=1e6, step=100, value=15000, label="R56 = RC (Ω)")
    cc = mo.ui.number(start=10, stop=100000, step=10, value=2200, label="C45 = CC (pF)")
    cp = mo.ui.number(
        start=0, stop=10000, step=1, value=0, label="CP (pF, 0 = not fitted)"
    )
    n_cer = mo.ui.number(
        start=0, stop=12, step=1, value=3, label="Output ceramics (count)"
    )
    c_cer = mo.ui.number(
        start=0.1,
        stop=100,
        step=0.1,
        value=9.0,
        label="…effective µF each at 5 V (22 µF 0805, est.)",
    )
    esr_cer = mo.ui.number(
        start=0.5, stop=50, step=0.5, value=5, label="…ESR each (mΩ, est.)"
    )
    n_tan = mo.ui.number(
        start=0, stop=6, step=1, value=2, label="Tantalums C21/C26 (count)"
    )
    c_tan = mo.ui.number(start=1, stop=470, step=1, value=22, label="…µF each")
    esr_tan = mo.ui.number(
        start=10, stop=5000, step=10, value=2400, label="…ESR each (mΩ, est.)"
    )
    l1 = mo.ui.number(
        start=0.47, stop=4.7, step=0.01, value=1.0, label="L1 charger inductor (µH)"
    )
    l1_isat = mo.ui.number(
        start=1, stop=30, step=0.1, value=10, label="L1 saturation (A)"
    )
    c_in = mo.ui.number(
        start=0,
        stop=50,
        step=0.1,
        value=0.8,
        label="IN cap C43 effective (µF, 1 µF nominal)",
    )
    c_pmid = mo.ui.number(
        start=0,
        stop=50,
        step=0.5,
        value=6.0,
        label="PMID cap C49 effective (µF, 10 µF nominal)",
    )
    c_sys = mo.ui.number(
        start=0,
        stop=100,
        step=0.5,
        value=12.0,
        label="SYS caps C40+C54 effective (µF, 20 µF nominal)",
    )
    c_batt = mo.ui.number(
        start=0,
        stop=100,
        step=0.5,
        value=6.0,
        label="BATT cap C50 effective (µF, 10 µF nominal)",
    )
    c_bst = mo.ui.number(
        start=0,
        stop=100000,
        step=1,
        value=22000,
        label="BST cap C47 (nF; the ordered part is 22 µF = 22000 nF)",
    )
    r44 = mo.ui.number(
        start=1000, stop=10e6, step=1000, value=100000, label="R44 gate pull-up (Ω)"
    )
    r48 = mo.ui.number(
        start=0, stop=100000, step=100, value=1000, label="R48 gate resistor (Ω)"
    )
    r_ntc_pull = mo.ui.number(
        start=1000, stop=100000, step=100, value=10000, label="R57 NTC pull-up (Ω)"
    )
    ntc_r25 = mo.ui.number(
        start=1000, stop=100000, step=100, value=10000, label="TH1 R25 (Ω)"
    )
    ntc_b = mo.ui.number(
        start=2000, stop=5000, step=1, value=3435, label="TH1 B constant (K)"
    )
    led_r = mo.ui.number(
        start=100, stop=100000, step=100, value=10000, label="R52/R53 LED resistor (Ω)"
    )
    led_vf = mo.ui.number(
        start=1.5, stop=3.5, step=0.05, value=3.0, label="Status LED Vf (V, est.)"
    )
    led_src = mo.ui.dropdown(
        options=["VCC (charger, 3.65 V, USB only)", "SYS"],
        value="VCC (charger, 3.65 V, USB only)",
        label="Status LEDs fed from",
    )
    led_target = mo.ui.number(
        start=0.1, stop=10, step=0.1, value=2.0, label="Status LED target (mA)"
    )
    mo.vstack(
        [
            mo.md("## Your parts and targets"),
            mo.md("**Boost (TPS61288)**"),
            mo.hstack([tgt_ripple, tgt_eff, l_tol]),
            mo.hstack([l2, l2_isat, l2_dcr]),
            mo.hstack([r50, r55]),
            mo.hstack([rc, cc, cp]),
            mo.hstack([n_cer, c_cer, esr_cer]),
            mo.hstack([n_tan, c_tan, esr_tan]),
            mo.md("**Charger (MP2721)**"),
            mo.hstack([l1, l1_isat]),
            mo.hstack([c_in, c_pmid]),
            mo.hstack([c_sys, c_batt, c_bst]),
            mo.hstack([r_ntc_pull, ntc_r25, ntc_b]),
            mo.hstack([led_src, led_r, led_vf, led_target]),
            mo.md("**Load switch (Q1)**"),
            mo.hstack([r44, r48]),
        ]
    )
    return (
        c_batt,
        c_bst,
        c_cer,
        c_in,
        c_pmid,
        c_sys,
        c_tan,
        cc,
        cp,
        esr_cer,
        esr_tan,
        l1,
        l1_isat,
        l2,
        l2_isat,
        l_tol,
        led_r,
        led_src,
        led_target,
        led_vf,
        n_cer,
        n_tan,
        ntc_b,
        ntc_r25,
        r44,
        r48,
        r50,
        r55,
        r_ntc_pull,
        rc,
        tgt_eff,
        tgt_ripple,
    )


@app.cell
def _(math):
    # ---------------------------------------------------------------- display helpers
    PREFIX = [
        (1e-12, "p"),
        (1e-9, "n"),
        (1e-6, "µ"),
        (1e-3, "m"),
        (1, ""),
        (1e3, "k"),
        (1e6, "M"),
    ]

    def fmt(x, unit=""):
        """3 significant figures with an SI prefix: fmt(0.0022, 'A') -> '2.20 mA'."""
        if x is None:
            return "—"
        if isinstance(x, str):
            return x
        if x == 0 or not math.isfinite(x):
            return f"{x:g} {unit}".strip()
        scale, p = max(
            (s for s in PREFIX if abs(x) >= s[0] * 0.9995), default=PREFIX[0]
        )
        return f"{x / scale:.3g} {p}{unit}".strip()

    def table(rows):
        """rows: (check, ideal, yours, rule, ok) -> markdown table. ok: True / False / None."""
        mark = {True: "✅", False: "❌", None: "ℹ️"}
        lines = ["| Check | Ideal | Yours | Rule / source | |", "|---|---|---|---|---|"]
        lines += [f"| {c} | {i} | {y} | {r} | {mark[o]} |" for c, i, y, r, o in rows]
        return "\n".join(lines)

    E6 = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]

    def nearest_e6(x):
        """Nearest standard E6 value at or above x (for inductors and caps)."""
        decade = 10 ** math.floor(math.log10(x))
        for v in E6 + [10.0]:
            if v * decade >= x * 0.999:
                return v * decade
        return 10 * decade

    return fmt, nearest_e6, table


@app.cell
def _(LED_DRIVER, free_load, gcc, load_mode, mcu_ma, r_ext):
    # ---------------------------------------------------------------- load current on 5 V
    def led_rail_current(r, g):
        per_output = LED_DRIVER.k / r * g / 256  # A per current output
        return per_output, per_output * LED_DRIVER.outputs_per_chip * LED_DRIVER.chips

    if load_mode.value.startswith("Worst"):
        led_out, led_total = led_rail_current(13000, 256)
    elif load_mode.value.startswith("LED"):
        led_out, led_total = led_rail_current(r_ext.value, gcc.value)
    else:
        led_out, led_total = None, free_load.value - mcu_ma.value / 1000
    i_load = led_total + mcu_ma.value / 1000
    return i_load, led_out


@app.cell
def _(
    MP,
    OTHER,
    USB,
    cc_fw,
    free_i,
    free_v,
    iin_override,
    ovp,
    pd_ctrl,
    pd_i,
    pd_v,
    src,
    usb_on,
):
    # ---------------------------------------------------------------- what the source really gives
    # Without a PD controller a PD charger only offers 5 V; its current is its USB-C advertisement.
    notes = []
    if src.value == "Free form":
        v_src, i_src, iin_auto, iin_cc = free_v.value, free_i.value, 0.5, free_i.value
    else:
        _s = USB[src.value]
        v_src, i_src, iin_auto, iin_cc = _s["v"], _s["i"], _s["iin_auto"], _s["iin_cc"]
        if src.value == "USB-PD charger":
            if pd_ctrl.value:
                v_src, i_src = float(pd_v.value), float(pd_i.value)
                iin_cc = i_src
            else:
                notes.append(
                    f"No PD controller: the charger stays at 5 V even though it can offer {pd_v.value} V."
                )
    iin_lim = (
        iin_override.value
        if iin_override.value > 0
        else (iin_cc if cc_fw.value else iin_auto)
    )
    iin_lim = min(iin_lim, MP.iin_max)

    # Voltage limits on the USB input side
    v_limits = [
        (
            "MP2721 input OVP",
            MP.ovp_options[ovp.value],
            "charger stops; nothing is damaged below 26 V",
        ),
        ("MP2721 recommended max", MP.vin_rec_max, "datasheet operating range"),
        ("MP2721 absolute max", MP.vin_abs_max, "damage"),
        (
            "nRF52840 VBUS pin",
            OTHER.nrf_vbus_max,
            "damage (from memory, verify in the nRF52840 PS)",
        ),
        (
            "D0 USBLC6-2 VBUS",
            OTHER.usblc6_vbus_max,
            "clamps/overheats (from memory, verify)",
        ),
    ]
    usb_ok = usb_on.value and MP.vin_rec_min <= v_src <= MP.ovp_options[ovp.value]
    return i_src, iin_lim, notes, usb_ok, v_limits, v_src


@app.cell
def _(
    MP,
    Q1,
    bat_cut,
    bat_rint,
    bat_rwire,
    bat_type,
    bat_v,
    buck_eff,
    cable_r,
    i_load,
    i_src,
    icc,
    iin_lim,
    math,
    r44,
    r48,
    sys_min,
    tgt_eff,
    usb_ok,
    v_src,
    vin_lim,
):
    # ---------------------------------------------------------------- power path (MP2721 NVDC rules)
    def q1_rds(v_gate):
        """AON7423 max RDS(on) for a gate drive of v_gate volts (straight-line between table points)."""
        pts = Q1.rds_table
        if v_gate <= pts[0][0]:
            return pts[0][1]
        for (v0, r0), (v1, r1) in zip(pts, pts[1:]):
            if v_gate <= v1:
                return r0 + (r1 - r0) * (v_gate - v0) / (v1 - v0)
        return pts[-1][1]

    def path(usb, v_bat):
        """Currents and voltages from the source to the boost's input for one situation."""
        p_boost_in = 5.0 * i_load / (tgt_eff.value / 100)  # power the boost draws
        standby = 0.0
        if usb:
            # Input: limited by IIN_LIM, by the source, and by VIN_LIM (cable drop)
            i_in_max = min(iin_lim, i_src)
            if cable_r.value > 0:
                i_in_max = min(i_in_max, (v_src - vin_lim.value) / cable_r.value)
            i_in_max = max(i_in_max, 0.0)
            v_in = v_src - i_in_max * cable_r.value
            v_sys = max(sys_min.value + MP.vtrack, v_bat)
            v_tps = v_sys
            for _ in range(20):  # Q1 drop depends on the current
                i_sys = p_boost_in / v_tps
                v_tps = v_sys - i_sys * q1_rds(v_sys)
            standby = v_sys / (r44.value + r48.value)
            p_avail = v_in * i_in_max * buck_eff.value / 100
            p_need = v_sys * (i_sys + standby)
            charge_cap = icc.value if v_bat >= MP.vpre else MP.ipre
            if v_bat >= bat_type.value - 0.01:
                charge_cap = 0.0  # full: terminated
            if p_avail >= p_need:
                i_chg = min(charge_cap, (p_avail - p_need) / v_bat)
                i_bat = -i_chg
                i_in = (p_need + i_chg * v_bat) / (buck_eff.value / 100) / v_in
            else:
                # Supplement mode: USB gives all it can, the battery covers the rest, and SYS
                # drops to the battery voltage minus the drops along the battery's path.
                i_chg, i_in = 0.0, i_in_max
                r_bat_path = (bat_rint.value + bat_rwire.value) / 1000 + MP.r_battfet
                for _ in range(20):
                    v_sys = min(
                        max(sys_min.value + MP.vtrack, v_bat),
                        v_bat - max(p_need - p_avail, 0) / v_sys * r_bat_path,
                    )
                    v_tps = v_sys - i_sys * q1_rds(v_sys)
                    i_sys = p_boost_in / v_tps
                    p_need = v_sys * (i_sys + standby)
                i_bat = (p_need - p_avail) / v_sys
            return dict(
                usb=True,
                v_in=v_in,
                i_in=i_in,
                v_sys=v_sys,
                v_tps=v_tps,
                i_sys=i_sys,
                i_bat=i_bat,
                i_chg=i_chg,
                v_bat_term=v_bat,
                ok=True,
            )
        # Battery only: battery -> wires -> BATTFET -> SYS -> Q1 -> boost
        r_path = (bat_rint.value + bat_rwire.value) / 1000 + MP.r_battfet
        v_tps, i_sys = v_bat, 0.0
        for _ in range(50):
            rq = q1_rds(max(v_tps, 1.0))
            # p = v_tps * i,  v_tps = v_bat - i * (r_path + rq)  ->  solve the quadratic for i
            r = r_path + rq
            disc = v_bat**2 - 4 * r * p_boost_in
            if disc < 0:
                return dict(
                    usb=False,
                    ok=False,
                    v_tps=float("nan"),
                    i_sys=float("nan"),
                    i_bat=float("nan"),
                    v_sys=float("nan"),
                    v_bat_term=float("nan"),
                    i_chg=0.0,
                    v_in=0.0,
                    i_in=0.0,
                )
            i_sys = (v_bat - math.sqrt(disc)) / (2 * r)
            v_tps = v_bat - i_sys * r
        v_term = v_bat - i_sys * (bat_rint.value + bat_rwire.value) / 1000
        v_sys = v_term - i_sys * MP.r_battfet
        standby = v_sys / (r44.value + r48.value)
        return dict(
            usb=False,
            ok=True,
            v_in=0.0,
            i_in=0.0,
            v_sys=v_sys,
            v_tps=v_tps,
            i_sys=i_sys,
            i_bat=i_sys + standby,
            i_chg=0.0,
            v_bat_term=v_term,
        )

    full = bat_type.value
    scenarios = {
        "Battery only, empty": path(False, bat_cut.value),
        "Battery only, now": path(False, bat_v.value),
        "Battery only, full": path(False, full),
    }
    if usb_ok:
        scenarios.update(
            {
                "USB, battery empty": path(True, bat_cut.value),
                "USB, battery now": path(True, bat_v.value),
                "USB, battery full": path(True, full),
            }
        )
    good = [s for s in scenarios.values() if s["ok"]]
    vin_min = min(s["v_tps"] for s in good) if good else float("nan")
    vin_max = max(s["v_tps"] for s in good) if good else float("nan")
    worst_name = min(
        (n for n, s in scenarios.items() if s["ok"]),
        key=lambda n: scenarios[n]["v_tps"],
        default="—",
    )
    return q1_rds, scenarios, vin_max, vin_min, worst_name


@app.cell
def _(
    fmt,
    i_load,
    i_src,
    iin_lim,
    led_out,
    mo,
    notes,
    scenarios,
    src,
    usb_ok,
    v_limits,
    v_src,
    worst_name,
):
    # ---------------------------------------------------------------- show: source and power path
    _rows = [
        "| Situation | Boost input | From USB | Battery (+ out / − charging) | SYS |",
        "|---|---|---|---|---|",
    ]
    for _name, _s in scenarios.items():
        if not _s["ok"]:
            _rows.append(f"| {_name} | **battery can't supply this load** | | | |")
            continue
        _usb_part = (
            f"{fmt(_s['i_in'], 'A')} at {fmt(_s['v_in'], 'V')}" if _s["usb"] else "—"
        )
        _rows.append(
            f"| {_name}{' ← worst' if _name == worst_name else ''} | {fmt(_s['v_tps'], 'V')}, {fmt(_s['i_sys'], 'A')} "
            f"| {_usb_part} | {fmt(_s['i_bat'], 'A')} | {fmt(_s['v_sys'], 'V')} |"
        )
    _lim_rows = ["| Part | Limit | Source voltage | |", "|---|---|---|---|"]
    _lim_rows += [
        f"| {_n} | {fmt(_v, 'V')} ({_why}) | {fmt(v_src, 'V')} | {'✅' if v_src <= _v else '❌'} |"
        for _n, _v, _why in v_limits
    ]
    _led_line = f" ({fmt(led_out, 'A')} per LED output)" if led_out else ""
    mo.vstack(
        [
            mo.md(
                f"## What the board gets\n**{src.value}:** {fmt(v_src, 'V')}, source can give {fmt(i_src, 'A')}; "
                f"charger input limit set to **{fmt(iin_lim, 'A')}**. USB usable: {'yes' if usb_ok else '**no**'}.  \n"
                f"Load on 5 V: **{fmt(i_load, 'A')}**{_led_line}.  \n"
                + "  \n".join(f"⚠️ {_n}" for n in notes)
            ),
            mo.md("\n".join(_lim_rows)),
            mo.md("### Power path in each situation\n" + "\n".join(_rows)),
        ]
    )
    return


@app.cell
def _(
    TPS,
    fmt,
    i_load,
    l2,
    l2_isat,
    l_tol,
    mo,
    nearest_e6,
    r50,
    r55,
    table,
    tgt_eff,
    vin_max,
    vin_min,
    worst_name,
):
    # ---------------------------------------------------------------- boost: output voltage and inductor
    vout = TPS.vref * (1 + r50.value / r55.value)
    vout_lo = TPS.vref_min * (1 + r50.value * 0.99 / (r55.value * 1.01))
    vout_hi = TPS.vref_max * (1 + r50.value * 1.01 / (r55.value * 0.99))
    r1_ideal = (5.0 - TPS.vref) * r55.value / TPS.vref  # Eq. 1

    eff = tgt_eff.value / 100
    l_low = l2.value * 1e-6 * (1 - l_tol.value / 100)  # worst-case inductance
    i_dc = vout * i_load / (vin_min * eff)  # Eq. 2

    def i_pp(l):  # Eq. 3
        return 1 / (l * (1 / (vout - vin_min) + 1 / vin_min) * TPS.fsw_min)

    i_peak = i_dc + i_pp(l_low) / 2  # Eq. 4

    # Ideal inductor: ripple about 30 % of the DC current, inside TI's 1–4.7 µH range
    l_need = (
        1
        / (0.3 * i_dc * (1 / (vout - vin_min) + 1 / vin_min) * TPS.fsw_min)
        / (1 - l_tol.value / 100)
    )
    l_ideal = min(max(nearest_e6(l_need), TPS.l_min), TPS.l_max)
    i_peak_ideal = i_dc + i_pp(l_ideal * (1 - l_tol.value / 100)) / 2

    duty_max = 1 - vin_min * eff / vout
    duty_min = 1 - vin_max / vout
    ton_min_now = duty_min / TPS.fsw_max

    boost_rows = [
        (
            "Output voltage (R50/R55)",
            fmt(r1_ideal, "Ω") + " top for 5.00 V",
            f"{fmt(vout, 'V')} ({fmt(vout_lo, 'V')}–{fmt(vout_hi, 'V')})",
            "Eq. 1, VREF 0.588–0.612 V, 1 % resistors",
            4.75 <= vout_lo and vout_hi <= 5.25,
        ),
        (
            "27 pF across R55 needed?",
            "only if R55 > 15 kΩ",
            fmt(r55.value, "Ω"),
            "§9.2.2.1",
            r55.value <= TPS.r2_needs_c6,
        ),
        (
            "Lowest boost input",
            "—",
            f"{fmt(vin_min, 'V')} ({worst_name})",
            f"UVLO {TPS.uvlo_rise} V start, {TPS.uvlo_fall} V stop",
            vin_min > TPS.uvlo_rise,
        ),
        ("Inductor DC current", "—", fmt(i_dc, "A"), "Eq. 2 at lowest input", None),
        (
            "Inductor value",
            fmt(l_ideal, "H") + " (ripple ≈ 30 %)",
            fmt(l2.value * 1e-6, "H"),
            "TI range 1–4.7 µH",
            TPS.l_min <= l2.value * 1e-6 <= TPS.l_max,
        ),
        (
            "Inductor ripple (peak-peak)",
            fmt(i_pp(l_ideal * (1 - l_tol.value / 100)), "A"),
            fmt(i_pp(l_low), "A"),
            f"Eq. 3, −{l_tol.value} % L, {fmt(TPS.fsw_min, 'Hz')}",
            None,
        ),
        (
            "Inductor peak current",
            fmt(i_peak_ideal, "A"),
            fmt(i_peak, "A"),
            f"Eq. 4, must stay below the {TPS.ilim_min} A minimum current limit",
            i_peak < TPS.ilim_min,
        ),
        (
            "Inductor saturation (practical)",
            f"≥ {fmt(i_peak * 1.2, 'A')}",
            fmt(l2_isat.value, "A"),
            "above the peak with 20 % margin",
            l2_isat.value >= i_peak * 1.2,
        ),
        (
            "Inductor saturation (TI's rule)",
            f"≥ {fmt(TPS.ilim_max, 'A')}",
            fmt(l2_isat.value, "A"),
            "§9.2.2.2: above the current limit, survives a short",
            l2_isat.value >= TPS.ilim_max,
        ),
        ("Duty cycle", "—", f"{duty_min:.0%}–{duty_max:.0%}", "", None),
        (
            "Shortest on-time",
            f"≥ {fmt(TPS.ton_min, 's')}",
            fmt(ton_min_now, "s"),
            "§7.5 minimum on-time",
            ton_min_now >= TPS.ton_min,
        ),
    ]
    mo.md("## Boost (TPS61288): voltage and inductor\n" + table(boost_rows))
    return duty_max, i_peak, vout


@app.cell
def _(
    TPS,
    c_cer,
    c_tan,
    cc,
    cp,
    duty_max,
    esr_cer,
    esr_tan,
    fmt,
    i_load,
    i_peak,
    l2,
    l_tol,
    math,
    mo,
    n_cer,
    n_tan,
    np,
    rc,
    table,
    tgt_ripple,
    vin_min,
    vout,
):
    # ---------------------------------------------------------------- boost: output caps and loop
    c_ceramic = n_cer.value * c_cer.value * 1e-6
    r_ceramic = esr_cer.value / 1000 / max(n_cer.value, 1)
    # Eq. 5 + 6 with the ceramics (the tantalums' ESR is too high to help at 500 kHz)
    v_ripple = (
        (vout - vin_min) * i_load / (vout * TPS.fsw_min * c_ceramic)
        + i_peak * r_ceramic
        if c_ceramic
        else float("inf")
    )
    budget = tgt_ripple.value / 1000 - i_peak * r_ceramic
    c_min = (
        (vout - vin_min) * i_load / (vout * TPS.fsw_min * budget)
        if budget > 0
        else float("inf")
    )

    # Loop at the worst case (lowest input, full load): Eq. 7–14
    r_o = vout / i_load
    _l_low = l2.value * 1e-6 * (1 - l_tol.value / 100)
    d = duty_max
    f_rhpz = r_o * (1 - d) ** 2 / (2 * math.pi * _l_low)  # Eq. 10
    fc_ideal = min(TPS.fsw_min / 10, f_rhpz / 5)
    rc_ideal = (
        2
        * math.pi
        * vout
        * c_ceramic
        * fc_ideal
        / ((1 - d) * TPS.vref * TPS.gm * TPS.kcomp)
    )  # Eq. 12
    cc_ideal = r_o * c_ceramic / (2 * rc_ideal)  # Eq. 13
    cp_ideal = r_ceramic * c_ceramic / rc_ideal  # Eq. 14

    # Full loop gain with your parts, all output caps as real impedances
    _f = np.logspace(1, 6, 4000)
    _s = 2j * np.pi * _f
    z_caps = [(esr_cer.value / 1000 + 1 / (_s * c_cer.value * 1e-6))] * int(n_cer.value)
    z_caps += [(esr_tan.value / 1000 + 1 / (_s * c_tan.value * 1e-6))] * int(
        n_tan.value
    )
    y_out = 2 / r_o + sum(1 / z for z in z_caps)  # RO/2 in parallel with the caps
    g_ps = (
        TPS.kcomp * (1 - d) * (1 / y_out) * (1 - _s / (2 * math.pi * f_rhpz))
    )  # Eq. 7, generalised
    z_comp = rc.value + 1 / (_s * cc.value * 1e-12)
    if cp.value > 0:
        z_comp = 1 / (1 / z_comp + _s * cp.value * 1e-12)
    g_c = TPS.gm * TPS.vref / vout * z_comp  # transconductance amp into RC/CC/CP
    loop = g_ps * g_c
    mag = 20 * np.log10(np.abs(loop))
    phase = np.unwrap(np.angle(loop)) * 180 / np.pi
    cross = np.where(np.diff(np.sign(mag)) < 0)[0]
    fc_yours = _f[cross[0]] if len(cross) else float("nan")
    pm = 180 + phase[cross[0]] if len(cross) else float("nan")
    p180 = np.where(np.diff(np.sign(phase + 180)) < 0)[0]
    gm_db = -mag[p180[0]] if len(p180) else float("inf")

    loop_rows = [
        (
            "Output ripple",
            f"≤ {fmt(tgt_ripple.value / 1000, 'V')}",
            fmt(v_ripple, "V"),
            "Eq. 5 + 6, ceramics only",
            v_ripple <= tgt_ripple.value / 1000,
        ),
        (
            "Effective ceramic output C",
            f"≥ {fmt(c_min, 'F')}",
            fmt(c_ceramic, "F"),
            "Eq. 5 solved for the ripple target",
            c_ceramic >= c_min,
        ),
        (
            "Right-half-plane zero",
            "—",
            fmt(f_rhpz, "Hz"),
            "Eq. 10 at the lowest input",
            None,
        ),
        (
            "Crossover frequency",
            fmt(fc_ideal, "Hz"),
            fmt(fc_yours, "Hz"),
            "≤ fsw/10 and ≤ fRHPZ/5",
            fc_yours <= fc_ideal * 1.05,
        ),
        ("RC (R56)", fmt(rc_ideal, "Ω"), fmt(rc.value, "Ω"), "Eq. 12", None),
        ("CC (C45)", fmt(cc_ideal, "F"), fmt(cc.value * 1e-12, "F"), "Eq. 13", None),
        (
            "CP",
            fmt(cp_ideal, "F") + (" → leave open" if cp_ideal < 10e-12 else ""),
            fmt(cp.value * 1e-12, "F"),
            "Eq. 14, open if < 10 pF",
            None,
        ),
        ("Phase margin", "> 45°", f"{pm:.0f}°", "§9.2.2.5", pm > 45),
        (
            "Gain margin",
            "> 10 dB",
            f"{gm_db:.0f} dB" if math.isfinite(gm_db) else "phase never reaches −180°",
            "§9.2.2.5",
            gm_db > 10,
        ),
    ]
    mo.vstack(
        [
            mo.md(
                "## Boost (TPS61288): output capacitors and stability\n"
                + table(loop_rows)
            ),
            mo.md(
                "*Ideal RC/CC/CP use the ceramics only, as TI's equations assume. The phase and gain margin use "
                "every output capacitor, including the tantalums at the LED drivers with their ESR; set their count "
                "to 0 to see the ceramics alone.*"
            ),
        ]
    )
    return


@app.cell
def _(
    MP,
    bat_dis,
    bat_mah,
    bat_rate,
    bat_type,
    c_batt,
    c_bst,
    c_in,
    c_pmid,
    c_sys,
    chg_fsw,
    fmt,
    icc,
    iin_lim,
    l1,
    l1_isat,
    led_r,
    led_src,
    led_target,
    led_vf,
    math,
    mo,
    nearest_e6,
    ntc_b,
    ntc_r25,
    r_ntc_pull,
    scenarios,
    sys_min,
    table,
    v_src,
):
    # ---------------------------------------------------------------- charger checks
    # Charge current: no more than the cell's rate, in 80 mA steps
    icc_ideal = (
        math.floor(min(bat_rate.value * bat_mah.value / 1000, MP.icc_max) / MP.icc_step)
        * MP.icc_step
    )

    # Buck inductor L1: worst ripple and peak at full input power
    f_lo, _f_typ = MP.fsw_options[chg_fsw.value]
    _v_sys = sys_min.value + MP.vtrack
    _v_in = min(v_src, 5.5)
    ripple_l1 = (
        _v_sys * (1 - _v_sys / _v_in) / (l1.value * 1e-6 * f_lo)
        if _v_in > _v_sys
        else 0.0
    )
    i_buck = (
        max(
            (s["i_sys"] + s["i_chg"])
            for s in scenarios.values()
            if s["ok"] and s["usb"]
        )
        if any(s["usb"] for s in scenarios.values())
        else iin_lim * _v_in / _v_sys
    )
    i_peak_l1 = i_buck + ripple_l1 / 2
    l1_ideal = (
        nearest_e6(
            _v_sys * (1 - _v_sys / _v_in) / (0.3 * max(i_buck, 0.1) * f_lo) * 1e6
        )
        if _v_in > _v_sys
        else 1.0
    )

    # NTC thresholds with your divider
    def ntc_temp(ratio):
        r_ntc = r_ntc_pull.value * ratio / (1 - ratio)
        return 1 / (1 / 298.15 + math.log(r_ntc / ntc_r25.value) / ntc_b.value) - 273.15

    # Status LEDs
    v_led = MP.vcc if led_src.value.startswith("VCC") else _v_sys
    i_led = max(v_led - led_vf.value, 0) / led_r.value
    r_led_ideal = (
        (v_led - led_vf.value) / (led_target.value / 1000)
        if v_led > led_vf.value
        else float("inf")
    )

    i_bat_max = max(
        (s["i_bat"] for s in scenarios.values() if s["ok"]), default=float("nan")
    )
    _rows = [
        (
            "Charge current ICC",
            fmt(icc_ideal, "A"),
            fmt(icc.value, "A"),
            f"≤ {bat_rate.value}C of {bat_mah.value} mAh",
            icc.value <= icc_ideal + 1e-9,
        ),
        (
            "Full-charge voltage",
            fmt(bat_type.value, "V"),
            "set VBATT_REG to match",
            "cell type",
            None,
        ),
        (
            "Battery discharge, worst",
            f"≤ {fmt(bat_dis.value, 'A')}",
            fmt(i_bat_max, "A"),
            "cell rating",
            i_bat_max <= bat_dis.value,
        ),
        (
            "Battery discharge vs charger trip",
            f"≤ {fmt(MP.battfet_ocp, 'A')}",
            fmt(i_bat_max, "A"),
            "BATTFET OCP 7 A",
            i_bat_max <= MP.battfet_ocp,
        ),
        (
            "L1 ripple (peak-peak)",
            "≈ 30 % of load",
            fmt(ripple_l1, "A"),
            f"buck at {fmt(f_lo, 'Hz')} (min)",
            None,
        ),
        (
            "L1 value",
            fmt(l1_ideal * 1e-6, "H"),
            fmt(l1.value * 1e-6, "H"),
            "ripple ≈ 30 % at full input",
            None,
        ),
        (
            "L1 peak vs saturation",
            f"≥ {fmt(i_peak_l1 * 1.2, 'A')}",
            fmt(l1_isat.value, "A"),
            "peak + 20 %",
            l1_isat.value >= i_peak_l1 * 1.2,
        ),
        (
            "IN cap (C43)",
            f"{fmt(MP.cap_in, 'F')}",
            fmt(c_in.value * 1e-6, "F") + " eff.",
            "pin table p.6",
            c_in.value * 1e-6 >= MP.cap_in * 0.7,
        ),
        (
            "PMID cap (C49)",
            f"≥ {fmt(MP.cap_pmid, 'F')}",
            fmt(c_pmid.value * 1e-6, "F") + " eff.",
            "pin table p.6",
            c_pmid.value * 1e-6 >= MP.cap_pmid * 0.7,
        ),
        (
            "SYS caps (C40+C54)",
            f"≥ {fmt(MP.cap_sys, 'F')}",
            fmt(c_sys.value * 1e-6, "F") + " eff.",
            "pin table p.6, minimum",
            c_sys.value * 1e-6 >= MP.cap_sys,
        ),
        (
            "BATT cap (C50)",
            f"≥ {fmt(MP.cap_batt, 'F')}",
            fmt(c_batt.value * 1e-6, "F") + " eff.",
            "pin table p.6, minimum",
            c_batt.value * 1e-6 >= MP.cap_batt,
        ),
        (
            "BST cap (C47)",
            fmt(MP.cap_bst, "F"),
            fmt(c_bst.value * 1e-9, "F"),
            "pin table p.6",
            abs(c_bst.value * 1e-9 - MP.cap_bst) < 5e-9,
        ),
        (
            "NTC pull-up (R57)",
            fmt(ntc_r25.value, "Ω"),
            fmt(r_ntc_pull.value, "Ω"),
            "equal to the NTC's R25",
            abs(r_ntc_pull.value - ntc_r25.value) < 1,
        ),
    ]
    _rows += [
        (
            f"NTC {name} threshold",
            f"{t_design} °C",
            f"{ntc_temp(ratio):.1f} °C",
            f"{ratio:.1%} of VRNTC",
            abs(ntc_temp(ratio) - t_design) <= 3,
        )
        for name, ratio, t_design in MP.ntc
    ]
    _rows += [
        (
            "Status LED current",
            f"{fmt(led_target.value / 1000, 'A')} target",
            fmt(i_led, "A"),
            f"from {led_src.value.split(' (')[0]}",
            i_led >= led_target.value / 1000 * 0.5,
        ),
        (
            "Status LED resistor",
            fmt(r_led_ideal, "Ω"),
            fmt(led_r.value, "Ω"),
            f"pin sinks ≤ {fmt(MP.led_sink_max, 'A')}",
            i_led <= MP.led_sink_max,
        ),
    ]
    mo.md("## Charger (MP2721)\n" + table(_rows))
    return


@app.cell
def _(
    Q1,
    TPS,
    bat_mah,
    fmt,
    i_load,
    mo,
    q1_rds,
    r44,
    r48,
    scenarios,
    table,
    tgt_eff,
):
    # ---------------------------------------------------------------- load switch, standby, runtime
    worst = min((x for x in scenarios.values() if x["ok"]), key=lambda x: x["v_tps"])
    rds = q1_rds(worst["v_sys"])
    p_q1 = worst["i_sys"] ** 2 * rds
    standby_on = worst["v_sys"] / (r44.value + r48.value)
    r44_ideal = 1e6  # gate leakage 100 nA × 1 MΩ = 0.1 V, still off
    off_time = r44.value * Q1.ciss
    p_in = 5.0 * i_load / (tgt_eff.value / 100)
    runtime_h = (bat_mah.value / 1000 * 3.7) / p_in if p_in else float("inf")
    _rows = [
        (
            "Q1 gate drive",
            f"≥ {Q1.vth_max} V, ≤ {Q1.vgs_max} V",
            fmt(worst["v_sys"], "V"),
            "AON7423 VGS(th) max / VGS max",
            Q1.vth_max < worst["v_sys"] < Q1.vgs_max,
        ),
        (
            "Q1 on-resistance (max)",
            "—",
            fmt(rds, "Ω"),
            "datasheet table, interpolated",
            None,
        ),
        (
            "Q1 heat at worst case",
            "< 0.5 W",
            fmt(p_q1, "W"),
            f"{fmt(worst['i_sys'], 'A')} through it",
            p_q1 < 0.5,
        ),
        (
            "R44 standby drain while on",
            fmt(worst["v_sys"] / (r44_ideal + r48.value), "A") + " with 1 MΩ",
            fmt(standby_on, "A"),
            "SYS / (R44 + R48)",
            standby_on < 10e-6,
        ),
        (
            "Q1 turn-off time (R44 × Ciss)",
            "—",
            fmt(off_time, "s"),
            "fine for a slide switch",
            None,
        ),
        ("Boost idle draw from 5 V", "—", fmt(TPS.iq_vout, "A"), "TPS61288 §7.5", None),
        (
            "Rough runtime at this load",
            "—",
            f"{runtime_h:.1f} h",
            f"{bat_mah.value} mAh × 3.7 V ÷ {fmt(p_in, 'W')}",
            None,
        ),
    ]
    mo.md("## Load switch (Q1), standby and runtime\n" + table(_rows))
    return


if __name__ == "__main__":
    app.run()
