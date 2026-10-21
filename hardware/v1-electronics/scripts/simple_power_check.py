import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import math
    import marimo as mo

    return math, mo


@app.cell
def _(mo):
    # MP2721 operating point (buck: USB in -> SYS out)
    mp_vin = mo.ui.number(4.4, 5.25, 0.05, value=5.0, label="V_IN, USB (V)")
    mp_vsys = mo.ui.number(3.0, 4.4, 0.05, value=3.7, label="V_SYS (V)")
    # I_LOAD: the most the buck can deliver = IIN_LIM max 3.2 A × 5 V × ~90 % / 3.7 V ≈ 3.9 A.
    # The real demand (boost ≈ 2.2 A + 2 A charging) is above that, so the input limit sets it.
    mp_iload = mo.ui.number(0.5, 5.0, 0.1, value=3.9, label="I_LOAD, buck max (A)")
    mp_ripple = mo.ui.number(
        0.2, 0.4, 0.05, value=0.3, label="ΔI_L_MAX, fraction of load"
    )
    mp_fsw = mo.ui.dropdown(
        {"750 kHz": 750e3, "1 MHz": 1.0e6, "1.25 MHz": 1.25e6, "1.5 MHz": 1.5e6},
        value="1 MHz",
        label="f_SW",
    )
    mo.vstack([mo.md("## MP2721 inputs"), mp_vin, mp_vsys, mp_iload, mp_ripple, mp_fsw])
    return mp_fsw, mp_iload, mp_ripple, mp_vin, mp_vsys


@app.cell
def _(math, mo, mp_fsw, mp_iload, mp_ripple, mp_vin, mp_vsys):
    # MP2721 Application Information, p.40
    V_IN, V_SYS, I_LOAD, f_SW = (
        mp_vin.value,
        mp_vsys.value,
        mp_iload.value,
        mp_fsw.value,
    )
    dI_L_MAX = mp_ripple.value * I_LOAD

    L = ((V_IN - V_SYS) * V_SYS) / (dI_L_MAX * V_IN * f_SW)  # Eq 1
    I_SAT = I_LOAD + (dI_L_MAX / 2)  # Eq 2
    I_RMS_MAX = I_LOAD * math.sqrt(V_SYS * (V_IN - V_SYS)) / V_IN  # Eq 3

    mo.md(
        fr'''
        # MP2721 Components
        ## L1 Input Inductor Characteristics

        | title | formula | value |
        |-------|---------|-------|
        | Inductance | ${{ L = \frac{{V_{{\text{{IN}}}} - V_{{\text{{SYS}}}}}}{{\Delta I_{{\text{{L\_MAX}}}}}} \cdot \frac{{V_{{\text{{SYS}}}}}}{{V_{{\text{{IN}}}} \cdot f_{{\text{{SW}}}}}} }}$ | {L*1e6:.2f} µH |
        | Saturation Current | ${{ I_{{\text{{SAT}}}} > I_{{\text{{LOAD}}}} + \frac{{\Delta I_{{\text{{L\_MAX}}}}}}{{2}} }}$ | {I_SAT:.2f} A |

        ## C49 (C<sub>PMID</sub>) Minimum Electrical Ratings

        | title | formula | value |
        |-------|---------|-------|
        |Capacitor Minimum Current Rating| ${{ I_{{\text{{MIN\_Rating}}}} > I_{{\text{{RMS\_MAX}}}} ; I_{{\text{{RMS\_MAX}}}} = \frac{{I_{{\text{{LOAD}}}} \cdot \sqrt{{V_{{\text{{SYS}}}} \cdot (V_{{\text{{IN}}}} - V_{{\text{{SYS}}}})}}}}{{V_{{\text{{IN}}}}}} }}$ | {I_RMS_MAX:.2f} A |
        |Capacitor Minimum Voltage Rating| $V_{{\text{{MIN\_Rating}}}} > MAX(V_{{\text{{IN}}}}, V_{{\text{{OS}}}})$ | $V_{{\text{{IN}}}} =$ {V_IN} V |
        |Recommended Capacitance| N/A | 10 μF |

        $V_{{\text{{OS}}}}$ - the plug in over shoot voltage. A spike in voltage when a device is plugged in.
        '''
    )
    return


@app.cell
def _(mo):
    # TPS61288 operating point (boost: SYS -> 5 V). Worst case = lowest V_IN at full load.
    tp_vout = mo.ui.slider(4.5, 5.5, 0.05, value=5.0, label="V_OUT (V)", show_value=True)
    tp_vin = mo.ui.slider(2.5, 4.4, 0.05, value=3.0, label="V_IN_MIN (V)", show_value=True)
    # I_OUT worst case, IS31FL3733 datasheet: I_OUT per CS = 840/R_EXT × GCC/256 = 38 mA typ at 22 kΩ,
    # ~42 mA at the max tolerance (46 mA at 20 kΩ scaled). 16 CS on per scan slot × 2 chips = 1.33 A,
    # + 2 × 3 mA quiescent + ~50 mA MCU = 1.39 A.
    tp_iout = mo.ui.slider(0.1, 3.0, 0.01, value=1.39, label="I_OUT (A)", show_value=True)
    tp_eta = mo.ui.slider(0.70, 0.95, 0.01, value=0.85, label="η", show_value=True)
    # L2 = Sunlord MWSA1004S-2R2MT: 2.2 µH ±20 %, DCR 7 mΩ, Isat 13.2 A (datasheet p.29)
    tp_l = mo.ui.slider(1.0, 4.7, 0.1, value=2.2, label="L2 (µH)", show_value=True)
    tp_r1 = mo.ui.number(1000, 300000, 100, value=22000, label="R1 = R50 (Ω)")
    tp_r2 = mo.ui.number(1000, 300000, 100, value=3000, label="R2 = R55 (Ω)")
    # C41 (C_power stage) = Samsung CL21A106KAYNNNE: 10 µF ±10 %, 25 V, X5R, 0805.
    # DC-bias loss and ESR are ESTIMATES: Samsung's spec sheet has no per-part curves.
    c41_nom = mo.ui.number(0.1, 100, 0.1, value=10, label="C41 nominal (µF)")
    c41_loss = mo.ui.number(0, 90, 1, value=40, label="C41 DC-bias loss at V_IN (%)")
    c41_esr = mo.ui.number(0.1, 100, 0.1, value=2, label="C41 ESR (mΩ)")
    # C37–C39 (C_OUT) = Samsung CL21A226MAQNNNE: 22 µF ±20 %, 25 V, X5R, 0805.
    # DC-bias loss and ESR are ESTIMATES: Samsung's spec sheet has no per-part curves.
    cap_count = mo.ui.number(1, 12, 1, value=3, label="C_OUT count")
    cap_nom = mo.ui.number(0.1, 100, 0.1, value=22, label="C_OUT nominal each (µF)")
    cap_loss = mo.ui.number(0, 90, 1, value=60, label="C_OUT DC-bias loss at V_OUT (%)")
    cap_esr = mo.ui.number(0.1, 100, 0.1, value=5, label="C_OUT ESR each (mΩ)")
    mo.vstack(
        [
            mo.md("## TPS61288 inputs"),
            tp_vout, tp_vin, tp_iout, tp_eta, tp_l, tp_r1, tp_r2,
            c41_nom, c41_loss, c41_esr,
            cap_count, cap_nom, cap_loss, cap_esr,
        ]
    )
    return (
        c41_esr,
        c41_loss,
        c41_nom,
        cap_count,
        cap_esr,
        cap_loss,
        cap_nom,
        tp_eta,
        tp_iout,
        tp_l,
        tp_r1,
        tp_r2,
        tp_vin,
        tp_vout,
    )


@app.cell
def _(
    c41_esr,
    c41_loss,
    c41_nom,
    cap_count,
    cap_esr,
    cap_loss,
    cap_nom,
    math,
    mo,
    tp_eta,
    tp_iout,
    tp_l,
    tp_r1,
    tp_r2,
    tp_vin,
    tp_vout,
):
    # TPS61288 §9.2.2 and §7.5
    # L_TOL: TI says plan for −30 % (covers the ±20 % tolerance plus the drop at high current)
    V_REF, f_SW_T, G_EA, K_COMP, L_TOL = 0.6, 440e3, 180e-6, 13.5, 0.30   # f_SW minimum, L −30 %
    V_OUT, V_IN_MIN, I_OUT, eta = tp_vout.value, tp_vin.value, tp_iout.value, tp_eta.value
    L2 = tp_l.value * 1e-6 * (1 - L_TOL)
    R1, R2 = tp_r1.value, tp_r2.value

    # Output voltage (Eq 1 as a ratio)
    V_OUT_ratio = (V_OUT - V_REF) / V_REF
    v_out_ratio_formula_p1 = r"\frac{R_{1}}{R_{2}}"
    v_out_ratio_formula_p2 = r"\frac{V_{OUT} - V_{REF}}{V_{REF}}"
    v_out_ratio_formula = rf"{v_out_ratio_formula_p1} = {v_out_ratio_formula_p2}"

    # Inductor (Eq 2–4)
    I_DC = V_OUT * I_OUT / (V_IN_MIN * eta)
    I_DC_formula = r"I_{DC} = \frac{V_{OUT} \times I_{OUT}}{V_{IN} \times η}"
    I_PP = 1 / (L2 * (1 / (V_OUT - V_IN_MIN) + 1 / V_IN_MIN) * f_SW_T)
    I_PP_formula = r"\Delta I_L = \frac{1}{L \times \left( \frac{1}{V_{OUT} - V_{IN}} + \frac{1}{V_{IN}} \right) \times f_{SW}}"
    I_Lpeak = I_DC + I_PP / 2
    I_Lpeak_formula = r"I_{Lpeak} = I_{DC} + \frac{\Delta I_L}{2}"

    # Input capacitor C41 (C_power stage): triangle current (Fig 9-2), so ΔI_L = I_PP at V_IN_MIN
    dV_IN_MAX = 0.100                                            # TI §9.2.2.3: under 100 mV
    C_PS = c41_nom.value * 1e-6 * (1 - c41_loss.value / 100)
    R_PS_ESR = c41_esr.value * 1e-3
    dV_IN = I_PP * math.sqrt(R_PS_ESR**2 + (1 / (8 * f_SW_T * C_PS)) ** 2)
    V_IN_ripple_formula = r"\Delta V_{IN} = \Delta I_L \cdot \sqrt{r_{C_{power stage} ESR}^2 + \left(\frac{1}{8 \cdot f_{SW} \cdot C_{power stage EFF}}\right)^2}"

    # Output capacitors C37–C39 (Eq 5–6): identical caps in parallel
    C_OUT = cap_count.value * cap_nom.value * 1e-6 * (1 - cap_loss.value / 100)
    R_ESR = cap_esr.value * 1e-3 / cap_count.value
    V_ripple_dis = (V_OUT - V_IN_MIN) * I_OUT / (V_OUT * f_SW_T * C_OUT)
    V_ripple_ESR = I_Lpeak * R_ESR
    V_ripple_dis_formula = r"V_{ripple\_dis} = \frac{(V_{OUT} - V_{IN\_MIN}) \times I_{OUT}}{V_{OUT} \times f_{SW} \times C_{OUT}}"
    V_ripple_ESR_formula = r"V_{ripple\_ESR} = I_{Lpeak} \times R_{C\_ESR}"

    # Loop stability (Eq 8–14), using the output capacitors above
    D = 1 - V_IN_MIN * eta / V_OUT
    R_O = V_OUT / I_OUT
    f_P = 2 / (2 * math.pi * R_O * C_OUT)                                          # Eq 8
    f_ESRZ = 1 / (2 * math.pi * R_ESR * C_OUT)                                     # Eq 9
    f_RHPZ = R_O * (1 - D) ** 2 / (2 * math.pi * L2)                               # Eq 10
    f_C = min(f_SW_T / 10, f_RHPZ / 5)                                             # crossover rule
    R_C = 2 * math.pi * V_OUT * C_OUT * f_C / ((1 - D) * V_REF * G_EA * K_COMP)    # Eq 12
    C_C = R_O * C_OUT / (2 * R_C)                                                  # Eq 13
    C_P = R_ESR * C_OUT / R_C                                                      # Eq 14
    D_formula = r"D = 1 - \frac{V_{IN} \times η}{V_{OUT}}"
    R_O_formula = r"R_{O} = \frac{V_{OUT}}{I_{OUT}}"
    f_P_formula = r"f_{P} = \frac{2}{2\pi \times R_{O} \times C_{O}}"
    f_ESRZ_formula = r"f_{ESRZ} = \frac{1}{2\pi \times R_{ESR} \times C_{O}}"
    f_RHPZ_formula = r"f_{RHPZ} = \frac{R_{O} \times (1-D)^2}{2\pi \times L}"
    f_C_formula = r"f_{C} \leq \min\left(\frac{f_{SW}}{10}, \frac{f_{RHPZ}}{5}\right)"
    R_C_formula = r"R_{C} = \frac{2\pi \times V_{OUT} \times C_{O} \times f_{C}}{(1-D) \times V_{REF} \times G_{EA} \times K_{COMP}}"
    C_C_formula = r"C_{C} = \frac{R_{O} \times C_{O}}{2 R_{C}}"
    C_P_formula = r"C_{P} = \frac{R_{ESR} \times C_{O}}{R_{C}}"

    mo.md(
        fr'''
        # TPS61288 Components

        ## Output Voltage w/ R50(R<sub>1</sub>) R55(R<sub>2</sub>) Ratio
        Output voltage is the selected by the ratio of the R<sub>1</sub> & R<sub>2</sub>. The ratio your circuit needs for it's target output voltage can be found with the following:

        $$
        {v_out_ratio_formula}
        $$

        |  | target formula | target value | check formula | your value |
        |-------|---------|-------|---------|-------|
        | V<sub>OUT</sub> resistor ratio | ${{ {v_out_ratio_formula_p2} \mid V_{{OUT}} = {V_OUT} }}$ | {V_OUT_ratio:.2f} | ${{ {v_out_ratio_formula_p1} \mid R_{{1}} = {R1}, R_{{2}} = {R2} }}$ | {(R1/R2):.2f} |

        ## L2 Inductor Minimum Current Rating and Selection Criteria
        Inductor selection criteria:
        - with an inductance between 1.0 µH - 4.7 µH
        - all current ratings much greater than the peak inductance current
        - smallest DC resistance value available

        The minimum current rating is the peak inductor current(I<sub>Lpeak</sub>), it can be derived with the following formula:

        $$
        {I_Lpeak_formula}
        \\
        {I_DC_formula} \qquad {I_PP_formula}
        $$

        |       | formula | value |
        |-------|---------|-------|
        | Peak Inductor Current | ${{ {I_Lpeak_formula} }}$ | {I_Lpeak:.2f} A |
        | Inductor DC Current | ${{ {I_DC_formula} }}$ | {I_DC:.2f} A |
        | Inductor Current Peak-to-Peak Ripple | ${{ {I_PP_formula} }}$ | {I_PP:.2f} A |

        ## Input Capacitors C41(C<sub>power stage</sub>), C42(C<sub>VIN</sub>), C44(C<sub>VCC</sub>) [Varify AI Support]
        You size C41(C<sub>power stage</sub>) to limit input voltage ripple (𝜟V<sub>IN</sub>). The other values can be size but you aren't told to do so.

        > Here TI only recommends values, but doesn't provide supporting models for self selection. It is implied that a skill electrical engineer should be able to infer the correct models to use to select proper values.
        > **With the aide of AI and the verification of actual electrical engineers I'll be selecting values for C41.**

        Select a capacitor with an effective capacitance, and equivalent series resistance such that the ripple voltage (𝜟V<sub>IN</sub>) is under 100 mV.

        The model for 𝜟V<sub>IN</sub> is not given and must be derived. Based on Figure 9-2 it can be assumed that there is the inductor should have triangle current waveform, which causes a 𝜟V<sub>IN</sub> than can be modeled by the following.

        $${V_IN_ripple_formula}$$

        The capacitor you choose has an effective capcitance of {C_PS*1e6:.2f} µF and an ESR of {R_PS_ESR*1e3:.2f} mΩ, and the current ripple was found in prior steps.

        |  | target formula | target value | your value |
        |---|---|---|---|
        | Ripple Input Voltage |  ${{ {V_IN_ripple_formula} }}$ | < {dV_IN_MAX*1e3:.0f} mV | {dV_IN*1e3:.2f} mV |

        ## Output Capacitors C37, C38, C39 (C<sub>OUT</sub>)
        For this section you're not meant to size the capacitors you're determining if the output ripples are tolerable for your load. Ripple is caused by capcitor(s) esr and charge/discharge cycle of the capcitor(s).

        You choose to use {cap_count.value} of nomial capcitance of {cap_nom.value} µF, and an ESR of {cap_esr.value} mΩ. All together their effect capcitance is {C_OUT*1e6:.2f} µF and their ESR is {R_ESR*1e3:.2f} mΩ.

        |  | formula | value |
        |---|---|---|
        | Charge Discharge Voltage Ripple  |  ${{ {V_ripple_dis_formula} }}$ | {V_ripple_dis*1e3:.2f} mV |
        | ESR Voltage Ripple | ${{ {V_ripple_ESR_formula} }}$ | {V_ripple_ESR*1e3:.2f} mV |

        ## Loop Stability: Selecting R56(R<sub>C</sub>), C45(C<sub>C</sub>), N/A(C<sub>P</sub>).

        Use the formula to select values for the loop stability components. Based on the other formula given you can do developer analysis, but at the time of writing we're avoiding that. **If C<sub>P</sub> is less than 10 pF it should be left open.**

        C<sub>O</sub> and R<sub>ESR</sub> are the output capacitors' combined values from the section above.

        | | formula| value|
        |---|---|---|
        | R56 (R<sub>C</sub>) | ${{ {R_C_formula} }}$ | {R_C/1e3:.2f} kΩ |
        | C45 (C<sub>C</sub>) | ${{ {C_C_formula} }}$ | {C_C*1e9:.2f} nF |
        | C<sub>P</sub> | ${{ {C_P_formula} }}$ | {C_P*1e12:.1f} pF |

        ### Supporting Values
        | | formula| value|
        |---|---|---|
        | Duty cycle | ${{ {D_formula} }}$ | {D:.2f} |
        | Load resistance | ${{ {R_O_formula} }}$ | {R_O:.2f} Ω |
        | Output pole | ${{ {f_P_formula} }}$ | {f_P/1e3:.2f} kHz |
        | ESR zero | ${{ {f_ESRZ_formula} }}$ | {f_ESRZ/1e3:.0f} kHz |
        | Right-half-plane zero | ${{ {f_RHPZ_formula} }}$ | {f_RHPZ/1e3:.1f} kHz |
        | Crossover frequency | ${{ {f_C_formula} }}$ | {f_C/1e3:.1f} kHz |
        '''
    )
    return


if __name__ == "__main__":
    app.run()