# Reference Guide: Active Q-Control on Zurich Instruments UHF

**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Topology:** 4-Demodulator "Mnemonic" Setup (1=PLL, 3=Q, 4=AGC)  
**Date:** February 2026

---

## 1. System Topology & Demodulator Mapping

We map the PIDs directly to their corresponding Demodulators.

| Index | Function | Role | Critical Setting |
| :--- | :--- | :--- | :--- |
| **Demod 1** | **PLL Source** | Feeds **PID 1** to track frequency. | **TC:** ~1 ms (Medium bandwidth). |
| **Demod 2** | **Measurement** | Reserved for high-speed DAQ/Scope (Ring-down). | **TC:** **Min** (e.g., 10 µs). Fast! |
| **Demod 3** | **Q-Control** | Feeds **PID 3** to create damping force. | **TC:** Low (e.g., 30 µs). Fast feedback. |
| **Demod 4** | **AGC Source** | Feeds **PID 4** to stabilize amplitude. | **TC:** High (e.g., 100 ms). Slow integration. |

> **Note:** All 4 Demodulators must be set to the **same Oscillator** (e.g., Oscillator 1).

---

## 2. Hardware Wiring & Setup

| Signal Path | UHF Connection | Connection Detail |
| :--- | :--- | :--- |
| **Drive Output** | `Signal Output 1` | Main excitation. Controlled by AGC (PID 4). |
| **Q-Feedback** | `Signal Output 2` | Feedback force. Controlled by Q-PID (PID 3). |
| **Input Signal** | `Signal Input 1` | Resonator response. Feeds all Demods. |

> **Critical Hardware Step:** Physically sum `Signal Output 1` and `Signal Output 2` (using a BNC T-piece or combiner) before connecting to the resonator drive pin.

---

## 3. Controller Configuration Reference

Configure the PID modules in LabVIEW (or other APIs). Note that **PID 2 is skipped**.

| Parameter | **PID 1 (PLL)** | **PID 3 (Q-Control)** | **PID 4 (AGC)** |
| :--- | :--- | :--- | :--- |
| **Function** | **Frequency Tracking** | **Active Damping** | **Amplitude Stability** |
| **Input Source** | **Demod 1 Phase** ($\Theta$) | **Demod 3 R** (Amp) | **Demod 4 R** (Amp) |
| **Setpoint** | **0.0 deg** | **0.0 V** | **Target Amplitude** (e.g. 0.1 V) |
| **Output Channel** | `Oscillator 1 Freq` | `Signal Output 2 Amp` | `Signal Output 1 Amp` |
| **Output Phase** | N/A | **90.0°** (Crucial) | **0.0°** |
| **P-Gain (Kp)** | **Adaptive** (See Section 5.E) | **Variable** (Scan this) | **Positive** |
| **I-Gain (Ki)** | Required | **Zero** | **Positive** (Slow) |
| **Output Range** | $\pm$ 10 kHz | $\pm$ 0.5 V (Safety Limit) | 0.0 V to 1.0 V |

---

## 4. LabVIEW Programming Algorithm

### Phase A: Initialization (Safe State)
1.  **Define Connections:** Open LabOne API Session.
2.  **Configure Oscillator:** `oscs/0/freq` -> Target Freq (e.g., 10 MHz).
3.  **Configure Demods (The 4-Demod Setup):**
    * **Loop i = 0 to 3:** Set `demods/i/oscselect` -> `0`.
    * **Demod 1 (PLL):** `demods/0/timeconstant` -> `1e-3`, `order` -> 4.
    * **Demod 2 (DAQ):** `demods/1/timeconstant` -> `10e-6`, `order` -> 8.
    * **Demod 3 (Q):** `demods/2/timeconstant` -> `30e-6`.
    * **Demod 4 (AGC):** `demods/3/timeconstant` -> `100e-3`.
    * **Enable All:** `demods/*/enable` -> `1`.
4.  **Configure Outputs:**
    * **Sig 1 (Drive):** `sigouts/0/on` -> `1`, `phaseshift` -> `0.0`, `amp` -> `0.05`.
    * **Sig 2 (Feedback):** `sigouts/1/on` -> `1`, `phaseshift` -> `90.0`, `amp` -> `0.0`.
5.  **Disable PIDs:** Set `pids/0/enable` (PID1), `pids/2/enable` (PID3), and `pids/3/enable` (PID4) -> `0`.

### Phase B: Lock Frequency (PID 1)
6.  **Characterize Phase Slope:**
    * During sweep, calculate slope $S = d\Theta / df$ at resonance.
    * If $S < 0$ (Normal): Use **Negative** P/I gains.
    * If $S > 0$ (Inverted): Use **Positive** P/I gains (invert the Advisor suggested values)
7.  **Setup PID 1 (PLL):**
    * Input=`Demod 1 Phase`, Output=`Osc 1 Freq`.
    * Set P/I based on slope direction.
8.  **Engage:** `pids/0/enable` -> `1`.
9.  **Wait Loop:** Read `pids/0/error` until locked.

### Phase C: Q-Calibration Loop (Scanning PID 3)
*Using Demod 2 for Measurement, Demod 3 for Control.*

10. **Setup PID 3 (Q-Control):**
    * Node Path: `pids/2/...` (Index 2 = PID 3).
    * Input=`Demod 3 R`, Output=`Sig Out 2 Amp`, Setpoint=`0`.
    * **Important:** P-Gain starts at 0.
11. **Configure LabOne DAQ Module:**
    * *Trigger Source:* `SigOut 1 Enable` (Hardware Trigger).
    * *Signal Path:* `demods/1/sample.r` (Demod 2 R).
    * *Edge:* Falling (Trigger when drive turns off).
12. **Scan Loop (Iterate P-Gain):**
    * **Update P:** `pids/2/kp` -> `P_Value`. `pids/2/enable` -> `1`.
    * **Wait:** 500ms (Settle).
    * **Arm DAQ:** Execute `DAQ.Execute(Record)`.
    * **Cut Drive:** `sigouts/0/on` -> `0`.
    * **Wait for Record:** Poll DAQ module until finished.
    * **Restore Drive:** `sigouts/0/on` -> `1`.
    * **Fetch Data:** Get Waveform from DAQ module.
    * **Compute:** Fit exponential to Demod 2 data (See Section 5).

### Phase D: Engage Steady State
13. **Set Optimal Q:**
    * `pids/2/kp` -> Calculated Target P (See Section 5).
    * `pids/2/enable` -> `1`.
    * **Update PID 1 Gain:** Scale PLL gains by $Q_{native}/Q_{target}$ (See Section 5.E).
14. **Setup PID 4 (AGC):**
    * Node Path: `pids/3/...` (Index 3 = PID 4).
    * Input=`Demod 4 R`, Output=`Sig Out 1 Amp`, Setpoint=`Target Amp`.
15. **Engage:** `pids/3/enable` -> `1`.

---

## 5. Technical & Mathematical Reference

### A. The Ring-Down Fit
To extract the Q-factor from the DAQ time-series data, fit the amplitude envelope to:

$$A(t) = A_0 \cdot e^{-t/\tau} + C$$

* **$A_0$**: Initial Amplitude (Volts).
* **$\tau$ (tau)**: Decay time constant (Seconds).
* **$C$**: Noise floor / Offset (Volts).

**Calculating Q:**
$$Q = \pi \cdot f_0 \cdot \tau$$

**Calculating Damping Rate ($\Gamma$):**
$$\Gamma = \frac{1}{\tau} = \frac{\pi \cdot f_0}{Q}$$

### B. The P-Gain to Q Relationship (Calibration)
The relationship between the PID 3 P-gain ($K_p$) and the system damping is linear. Do not fit Q vs P; fit $\Gamma$ vs P.

**Linear Model:**
$$\Gamma(K_p) = \Gamma_{native} - \alpha \cdot K_p$$

1.  **Plot** $\Gamma$ (Y-axis) vs $K_p$ (X-axis).
2.  **Fit** a straight line to find the slope $\alpha$ and intercept $\Gamma_{native}$.
3.  **Solve** for the required $K_p$ for any target Q:

$$K_{p,target} = \frac{\Gamma_{native} - \frac{\pi \cdot f_0}{Q_{target}}}{\alpha}$$

### C. AGC Logic (PID 4)
The AGC is critical because Q-control modifies the system gain.
* **Without AGC:** Increasing Q by 10x increases Amplitude by 10x (until saturation).
* **With AGC:** The AGC reduces the Drive Voltage ($V_{drive}$) to keep Amplitude ($A$) constant.
* **Tuning:** Use a robust **Integral (I)** term. The **Proportional (P)** term should be positive but small to avoiding ringing in the amplitude domain.

### D. Safety: The Lasing Threshold
If $K_p$ is set too high (positive feedback), the total damping $\Gamma$ becomes negative.
* **Condition:** $\Gamma \le 0$
* **Result:** Exponential amplitude growth (Lasing).
* **Prevention:** In your software, calculate the "Lasing P-gain" ($K_{p,max} = \Gamma_{native} / \alpha$) and set a software limit at 90% of this value.

### E. PID Polarity & Phase Slope Handling (For "Strange" Resonators)

Some resonators exhibit an **inverted phase slope** (positive slope through resonance) due to capacitive feedthrough. Q-control does **not** fix this physics; it simply steepens the slope.

**1. Polarity Rule:**
* You must detect the slope direction ($S = d\Theta/df$) during Phase B.
* **Normal ($S < 0$):** Use **Negative** P and I gains for PID 1.
* **Inverted ($S > 0$):** Use **Positive** P and I gains for PID 1.
* *Note:* The sign of P and I must always match each other.

**2. Magnitude Scaling:**
* As Q increases, the phase slope becomes steeper. A steeper slope increases the loop gain of the PLL.
* To prevent oscillation, you must **reduce** the PID 1 gains proportionally.
* **Formula:**
    $$P_{new} = P_{native} \times \frac{Q_{native}}{Q_{target}}$$