# Practical Guide: Active Q-Control on Zurich Instruments UHF
Based on notes from R. Stomp see the [blog article](https://www.zhinst.com/europe/en/blogs/resonance-engineering-quality-factor-q-control-method).

**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Topology:** 4-Demodulator "Mnemonic" Setup (1=PLL, 2=Measurement, 3=Q, 4=AGC)  

---

## Part 1: The workflow

This section outlines the logical sequence to initialize the system, calibrate the active damping, and lock the resonator for measurements. 
It is intended to make a Q-control system for a QCM resonator. Q control can be made with or without the PLL activated. To achieve PLL with Q-control, we'll need the option MF-MD, so that the Sigout2 be assigned to the frequency of OSC1. This is required because the PID3 uses Sigout2.  
The program we use was initially made for a DAQ measurement on the demod 2 with a PLL on demod 1. So, building on that, we'll keep the demod 2 for fast measurements, 1 for PLL or sweep and demods 3 and 4 for Q-control. Obviously, other setups can me made, this is more of a ledger for our in-house work and the implemented program.
In a previous attempt we tried to use a ring-down method but the appearance of peak spikes at the change of the voltage prevented us to properly get the timeconstants of the decay. 


### Step 1: Initial sweep
Before engaging any control loops, we must find the resonance state of the QCM. **The electrical boundary conditions must match the final setup.**
1. **Turn ON `Signal Output 2`, set its amplitude to 0 V and 50 Ohm impedance.** This engages the internal 50-ohm impedance, which creates a voltage divider with `Signal Output 1` at the physical T-piece.
2. **Turn ON `Signal Output 1`** and set its amplitude to the desired voltage (mind the voltage divider).
3. Run a frequency sweep across the expected resonance (e.g., around 6 MHz), you may need to use Unwrap in the sweep procedure.
4. Calculate the native resonance frequency ($f_0$), bandwidth (BW), and native Q-factor from the amplitude peak (or Pratt circle), the amplitude will be used in pids4, see later.
5. Locate the resonance point; Lorentz fit and Pratt circle should give similar values. Note that in the v3 version of the QCM_PLL program, the resonance point is calculated at the minimum point of the amplitude of the Lorentz fit or by the largest phase slope ($d\Theta/df$) for the Pratt circle fit. If the resonance is not symmetrical, I think it is better to use the Pratt circle fit parameters.
6. Check the slope direction: If it goes down through resonance, the slope is Normal. If it goes up (due to parasitic capacitance or others), the slope is Inverted.

### Step 2: Q-Calibration & scanning (PID 3)
We need to calibrate the relationship between the Q-Control P-gain ($K_p$) and the physical damping ($\Gamma$). By performing a frequency sweep across the resonance at different $K_p$ values, we can extract the Q-factor directly from steady-state measurements, completely bypassing the peak charge/discharge transient.

1. Ensure PID 1 (PLL) is disabled, as the lock-in will conflict with the manual sweep sequencer. Because the PLL is temporarily off, we will use **Demod 1** to record the sweep data. This keeps **Demod 2** completely free for continuous DAQ measurements.
2. Set the **Demod 8** to have the same parameters as **Demod 1** 
3. Define a safe $K_p$ scan array (e.g., -10.0 to 10.0, increase it in subsecvent trials) for the PID3. Put lower limit and upper limit to about -0.25V and 0.25V.
   **Enable PID 3** (`pids/2/enable -> 1`).
4. **For each $K_p$ value in the array:**

    * Apply $K_p$ to PID 3, and wait 500-1000 ms for the system to settle.
    * Run a frequency sweep across the resonance, recording the amplitude and phase data from **Demod 1**. Both Osc 1 and Osc 2 (demod 8) must sweep at the same time to maintain identical frequencies on sigOut 1 and SigOut 2. Both Demods should have identical parameters.
    * Fit the Demod 1 sweep data to extract the Q-factor (e.g., using a Lorentz or Pratt circle fit). 
    * Calculate the effective damping rate for this $K_p$ step: $\Gamma = \frac{\pi \cdot f_0}{Q}$.

    At the end of the array scan, **Disable PID 3** (`pids/2/enable -> 0`).

    * **Safety check:** If the amplitude increases exponentially or the measured Q becomes extremely high, we have crossed the lasing threshold. Abort the scan and force PID 3 Kp to 0.
    * Fit the calculated damping rates ($\Gamma$) against the $K_p$ array to extract the natural damping ($\Gamma_{native}$) and the slope ($\alpha$).

### Step 3: Engage steady-state
Once the calibration scan is complete and we have the linear fit parameters ($\Gamma_{native}$ and $\alpha$), we can lock the system into its new Q-state.

**1. Calculate Kp and apply Q-Control**
Calculate the $K_p$ required for the desired target Q. This formula handles both active damping (positive $K_p$) and Q-enhancement (negative $K_p$):

$$K_{p\_target} = \frac{\frac{\pi \cdot f_0}{Q_{target}} - \Gamma_{native}}{\alpha}$$

* Set the value to PID 3: `/{dev}/pids/2/p` -> $K_{p\_target}$
* Enable PID 3 permanently: `/{dev}/pids/2/enable` -> `1`

**2. Scale the PLL (if used)**
Changing the Q-factor directly alters the phase slope ($d\Theta/df$) near resonance. Lowering Q flattens the slope (requiring more PLL gain), while increasing Q steepens the slope (requiring less PLL gain). 
Scale the PID 1 Proportional and Integral gains based on the Q-ratio to maintain your original tracking bandwidth:

$$P_{new} = P_{native} \times \frac{Q_{native}}{Q_{target}}$$

$$I_{new} = I_{native} \times \frac{Q_{native}}{Q_{target}}$$

* Update PID 1 P-gain: `/{dev}/pids/0/p` -> $P_{new}$
* Update PID 1 I-gain: `/{dev}/pids/0/i` -> $I_{new}$
* Re-enable PID 1 since the calibration sweeps are finished.

*(Note: the PLL and Q control will work together if the Osc2 follows the frequency of Osc1. This is pssible with the MF option or by referencing the Osc2 to have the Osc1 frequency, via ExtRef)*

**3. Engage the AGC**
Now that the active damping or enhancement has altered the natural amplitude, turn on the AGC to automatically adjust the drive voltage and hold the amplitude at your target setpoint. The setpoint for the PID4 should be the measured amplitude at the resonance point.
* Enable PID 4: `/{dev}/pids/3/enable` -> `1`

### Step 4 (optional): Frequency tracking (PLL on PID 1)
**Osc2 must follow Osc1 frequancy**
1. Use the PID Advisor to calculate baseline Proportional (P) and Integral (I) gains for a target bandwidth of about 100 Hz (depending on the crystal BW determined in Step 1 above). In the Advisor use the Resonator model.
2. Apply the polarity rule: If your phase slope is Normal, use Negative P and I gains (those given by Advisor). If it is Inverted, use Positive P and I gains (i.e. invert the values given by the Advisor). **D-Gain is usually 0.**
3. Apply the measured phase setpoint from Step 1 to PID 1.
4. Enable PID 1 (in PLL mode). The lock-in will now continuously track the resonance frequency (for measuring during the deposition increase the lowlimit value). The Phase Locked Loop (PLL) must remain active. If PLL is lost, check the BW parameters, cables, noise ?
5. Set the osc 2 to the same frequency as osc 1: ('/oscs/1/freq', value), or assign SigOut 2 to Osc 1.


---
## Q-Control flow diagram

![Q-Control Flow Diagram](q-control-flow.png)


## Part 2: Hardware & system topology

### A. Hardware wiring & routing
* **Input Signal (`Signal Input 1`):** Resonator response. Feeds all four Demods.
* **Drive Output (`Signal Output 1`):** Main excitation, controlled by PID 4 (AGC), use of Oscillator 1.
* **Q-Feedback (`Signal Output 2`):** Feedback force, controlled by PID 3 (Q-Control) (set Demod 3 phase to 90.0 deg). **Must be explicitly routed to Oscillator 1. If this is not possible, the Osc 2 frequency must be set manually** 

> **Hardware:** Physically sum `Signal Output 1` and `Signal Output 2` using a BNC T-piece before connecting to the resonator.


### B. Settings (example for 6 MHz, Q=50k)
All Demods must be referenced to `Oscillator 1`.

| Demodulator | Role | `timeconstant` | `order` | Base Node Path |
| :--- | :--- | :--- | :--- | :--- |
| **Demod 1** | **PLL Source & Sweep** | `0.2 to 1e-3` | `4` | `/{dev}/demods/0/` |
| **Demod 2** | **Measurement (DAQ)** | `0.1 to 1e-6` | `1` | `/{dev}/demods/1/` |
| **Demod 3** | **Q-Control** | `30e-6` | `4` | `/{dev}/demods/2/` |
| **Demod 4** | **AGC Source** | `100e-3` | `4` | `/{dev}/demods/3/` |


### C. Controller configuration (PIDs)
Configure the PID modules below. PID 2 is skipped. 

| Parameter | PID 1 (`/{dev}/pids/0/`) | PID 3 (`/{dev}/pids/2/`) | PID 4 (`/{dev}/pids/3/`) |
| :--- | :--- | :--- | :--- |
| **Function** | Frequency Tracking | Active Q-Control | Amplitude Stability (AGC) |
| **Target BW** | around `100` Hz | N/A (Pure P-controller) | `0.5` to `2.0` Hz |
| **Module Mode** | **PLL** | **PID** | **PID** |
| **Input Node** | `.../input` (Demod 1 Phase) | `.../input` (Demod 3 R) | `.../input` (Demod 4 R) |
| **Setpoint**| `.../setpoint` (Resonance Phase) | `.../setpoint` -> `0.0` | `.../setpoint` (Target Amp) |
| **Output Node** | `.../output` (Osc 1 Freq) | `.../output` (SigOut 2 Amp) | `.../output` (SigOut 1 Amp) |
| **P-Gain (Kp)** | `.../p` (Advisor, Sign-Dependent) | `.../p` (Calculated Kp_target) | `.../p` (Advisor) |
| **I-Gain (Ki)** | `.../i` (Advisor, Sign-Dependent) | `.../i` -> `0.0` | `.../i` (Advisor) |
| **D-Gain (Kd)** | `.../d` -> `0.0` | `.../d` -> `0.0` | `.../d` -> `0.0` |

>PID 1 is used in case of PLL lock.  

### D. Signal Output & phase configuration
Physically sum `Signal Output 1` and `Signal Output 2` using a BNC T-piece before connecting to the resonator.

| Parameter | Signal Output 1 (Main Drive) | Signal Output 2 (Q-Feedback) |
| :--- | :--- | :--- |
| **Enable Node** | `/{dev}/sigouts/0/on` -> `1` | `/{dev}/sigouts/1/on` -> `1` |
| **Routing** | `/{dev}/sigouts/0/enables/3` -> `1` | `/{dev}/sigouts/1/enables/7` -> `1` |
| **Phase Node** | `/{dev}/demods/3/phaseshift` -> `0.0` | `/{dev}/demods/2/phaseshift` -> `90.0` **(Crucial)** |

* The nodes for signal outputs: ('sigouts/0/amplitudes/3', '0.1') and ('sigouts/1/amplitudes/7', '0.0') ; '0.1'V or the desired voltage.

> **Note on PID polarity:** If parasitic capacitance inverts the phase slope, we must invert the P and I gains for **PID 1 only**. PID3 and PID4 normally use positive polarity.

---

## Part 3: Mathematical & software reference

### A. The Sweep steady-state fit 
To extract the Q-factor, fit the steady-state frequency sweep data (amplitude and phase) captured by Demod 1 to a Lorentz profile or a Pratt circle.

Once the $Q$ factor is extracted for a given $K_p$, convert it to the damping rate ($\Gamma$):

$$\text{Calculate Damping: } \Gamma = \frac{\pi \cdot f_0}{Q}$$

The Q-control module applies a feedback force that acts as artificial viscous damping, so the relationship between $K_p$ and $\Gamma$ is linear. Fit the resulting $\Gamma$ array against your $K_p$ array using a simple linear regression to find $\Gamma_{native}$ and $\alpha$.


### B. Calibration and safety limits

The PID 3 P-gain (Kp) can be used to either decrease or increase the Q-factor. Based on the negative slope fit shown in the calibration, the relationship between Kp and the effective system damping (Gamma) is:
Gamma(Kp) = Gamma_native - (alpha * Kp)

Where Gamma_native (the y-intercept) is your natural damping, and alpha is the magnitude of the slope obtained by fitting the extracted damping rates against your scanned Kp values.

* **Active damping (Lowering Q):** Kp < 0. Adds artificial viscous damping.
* **Q-Enhancement (Increasing Q):** Kp > 0. Counteracts natural damping.

**Reaching the target Q:**
Once the calibration scan is complete and the slope alpha is accurately fitted, calculate the exact Kp required for the target Q:
Kp_target = (Gamma_native - (pi * f0 / Q_target)) / alpha


**Lasing limit**
When enhancing the Q-factor we risk pushing the total damping to zero, causing the amplitude to grow exponentially (Lasing). For active damping (Kp > 0), this physical limit does not apply.
* **Lasing threshold:** Kp_lasing = -(Gamma_native / alpha)
* **Dynamic limit:** When automating a scan for Q-enhancement, calculate a preliminary fit and cap your negative Kp array at 80% to 90% of Kp_lasing.
* **Hardware limits:** Apply the hardware limits (`pids/2/limitlower` and `limitupper` to reasonable vlaues, e.g. -0.25 and 0.25 V) to act as physical fail-safe against lasing (in the negative direction) or output saturation (in the positive direction).

---

## Demodulator settings for HIPIMS DAQ operation

**Application:** HIPIMS (High Power Impulse Magnetron Sputtering) with  
- PLL active  
- Q-Control active  
- AGC active  
- DAQ streaming on Demod 2  
- Example resonator: ~6 MHz QCM, native Q ≈ 50k  
- Instrument: Zurich Instruments UHFLI  

The goal is to capture fast plasma transients while maintaining stable multi-loop control.

---

### Recommended demodulator configuration

| Demodulator | Role | Recommended Time Constant | Filter Order | Purpose |
|-------------|------|--------------------------|--------------|---------|
| **Demod 1** | **PLL Source** | **0.3 to 1 ms** | 4 | Stable phase tracking without reacting to plasma spikes. |
| **Demod 2** | **DAQ Measurement** | **0.1 to 1 us** | 1 | High temporal resolution, minimal filter delay for transient capture. |
| **Demod 3** | **Q-Control Source** | **20 to 50 us** | 4 | Fast damping/enhancement control without noise amplification. |
| **Demod 4** | **AGC Source** | **50 to 200 ms** | 4 | Slow amplitude stabilization; must not follow pulses. |

---

### Loop Hierarchy requirement

For stable multi-loop operation, the time constants (TC) must be decoupled:

TC(Demod 2) << TC(Demod 3) << TC(Demod 1) << TC(Demod 4)

Fast-to-Slow ordering prevents loop interaction and instability. 

### Important Measurement Note

While Q-control is engaged, the measured damping is:

Gamma_effective = Gamma_native + (alpha * Kp)

Thus, during HIPIMS operation:
* Frequency shifts are physically meaningful and reflect real mass/stress changes.
* Measured Q reflects the actively controlled system, not the native plasma damping.
* To measure native plasma-induced damping, you must disable PID 3 and observe the passive ring-down.

---

### Measurement notes

While Q-control is engaged, the measured damping is:

Gamma_effective = Gamma_native + (alpha * Kp)

Thus, during HIPIMS operation:
* Frequency shifts are physically meaningful and reflect real mass/stress changes.
* Measured Q reflects the actively controlled system, not the native plasma damping.
* To measure native plasma-induced damping, you must disable PID 3 and observe the passive ring-down.

---

### Design rationale

#### Demod 1 — PLL Source
The PLL must track real frequency shifts but ignore fast plasma-induced noise.

- Too fast (<100 µs) → PLL reacts to plasma transients → instability.
- Too slow (>5 ms) → PLL may temporarily lose lock during large frequency shifts.

A range of **0.3–1 ms** provides stable tracking for most HIPIMS regimes.

---

#### Demod 2 — Measurement (DAQ)
This demodulator captures transient behavior during the HIPIMS pulse.

- Time constant must be **much smaller than the plasma rise time**.
- Filter order must be **1** to minimize group delay distortion.
- If plasma rise ≈ 5 µs → use ~2 µs.
- If plasma rise ≈ 20 µs → use 5–10 µs.

This demodulator should always be the fastest in the system.

---

#### Demod 3 — Q-Control
Q-control implements active viscous damping.

- Too fast → amplifies noise.
- Too slow → damping becomes ineffective during fast transients.

A range of **20–50 µs** provides stable damping for a 6 MHz QCM.

---

#### Demod 4 — AGC
AGC maintains constant oscillation amplitude.

It must not respond to:
- Individual HIPIMS pulses
- Plasma ignition spikes

Time constant must be **much larger than pulse duration**.

Example:
- Pulse duration = 100 µs  
- Recommended AGC TC ≥ 50 ms  

---

### Loop hierarchy

For stable multi-loop operation:

$\tau(\text{Demod } 2) \ll \tau(\text{Demod } 3) \ll \tau(\text{Demod } 1) \ll \tau(\text{Demod } 4)$

Fast → Slow ordering prevents loop interaction and instability.

---

### Important measurement note

While Q-control is engaged, the measured damping is:

$\Gamma_{effective} = \Gamma_{native} - \alpha \cdot K_p$

Thus, during HIPIMS operation:
- Frequency shifts are physically meaningful.
- Measured Q reflects the actively controlled system.
- Native damping requires disabling PID 3 and performing a partial ring-down transient.

---