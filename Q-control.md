
# Practical Guide: Active Q-Control on Zurich Instruments UHF
Based on notes from R. Stomp see https://www.zhinst.com/europe/en/blogs/resonance-engineering-quality-factor-q-control-method


**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Topology:** 4-Demodulator "Mnemonic" Setup (1=PLL, 2=Measurement, 3=Q, 4=AGC)  

---

## Part 1: The Experimental Workflow

This section outlines the logical sequence to initialize the system, calibrate the active damping, and lock the resonator for measurement. It is supposed to make a Q-control system for a QCM resonator. In this description, the PLL is activated first then the Q parameters are found, but Q control can be made without the PLL.


### Step 1: Initial Sweep & Characterization
Before engaging any control loops, we must find the natural state of the QCM. **Crucially, the electrical boundary conditions must match the final setup.**
1. **Turn ON `Signal Output 2` and set its amplitude to 0 V.** This engages the internal 50-ohm impedance, which creates a voltage divider with `Signal Output 1` at the physical T-piece.
2. **Turn ON `Signal Output 1` and set its amplitude to double** your physically desired drive voltage (to compensate for the 50% drop across the T-piece).
3. Run a frequency sweep across the expected resonance (e.g., around 6 MHz).
4. Calculate the native resonance frequency ($f_0$), bandwidth (BW), and native Q-factor from the amplitude peak. Amplitude will be used in pids4, see later.
5. Locate the frequency where the phase slope ($d\Theta/df$) is steepest. 
6. Record the exact phase angle at this steepest point. **This is the resonance phase setpoint.** (Lorentz fit and Pratt circle should give similar values -use unwrap in sweep. Note that in the v3 version of the program, the resonance point is calculated at the minimum point of the amplitude of the Lorentz fit. If the resonance is not symmetrical, use the Pratt parameters which take the resonance at the max slope of the phase.)
7. Check the slope direction: If it goes down through resonance, the slope is Normal. If it goes up (due to parasitic capacitance or others), the slope is Inverted.


### Step 2: Engage Frequency Tracking (PID 1)
1. Use the PID Advisor to calculate baseline Proportional (P) and Integral (I) gains for a target bandwidth of about 100 Hz (depending on the crystal BW).
2. Apply the polarity rule: If your phase slope is Normal, use Negative P and I gains (those given by Advisor). If it is Inverted, use Positive P and I gains. **D-Gain is always 0.**
3. Apply your measured phase setpoint from Step 1 to PID 1.
4. Enable PID 1 (in PLL). The lock-in will now continuously track the resonance frequency (for measuring during the deposition increase the lowlimit value). The Phase Locked Loop (PLL) must remain active. If PLL is lost, check the BW parameters, cables, noise ?
5. Set the osc 2 to the same frequency as osc 1: ('/oscs/1/freq', value).

### Step 3: Q-Calibration & Scanning (PID 3)
With the frequency locked, we must calibrate the relationship between the Q-Control P-gain ($K_p$) and the physical damping ($\Gamma$). By stepping the drive amplitude to half (or maybe 33%, need to test this), the resonator undergoes a transient decay to a new steady state. Because the signal never drops into the noise floor, the PLL should remain locked throughout the measurement.
1. Ensure PID 3 P-gain starts at 0.
2. Define a safe $K_p$ scan array (e.g., 0.0 to 1.0 or 2.0, we'll check the limit during the measurement) for the PID3. Put lower limit and upper limit to -0.25V and 0.25V.
3. **For each $K_p$ value in the array:**

    * Apply $K_p$ to PID 3, **enable PID 3** (`pids/2/enable -> 1`), and wait 500 ms for the system to settle.
    * Subscribe to the Demod 2 data stream via software and begin polling data (or use DAQ or scope; I think poll is fast enough).
    * Step the drive signal amplitude down to 50% of its initial value (do not disable the output).
    * Measure ~30 - 50 ms for the amplitude to decay to the new half-amplitude steady state.
    * Restore the drive signal amplitude to its full original value and stop polling.
    * **Disable PID 3** (`pids/2/enable -> 0`) before iterating to the next gain value.
    * Wait approximately 3 to 5 times the time constant ($\tau$) for the physical amplitude to stabilize; 10 msec is enough.
    * Verify that the PLL remained securely locked during the transient step.

    * **Safety Check:** If the amplitude increases instead of decaying, we have crossed the lasing threshold. Abort the scan and force PID 3 to 0. Note : in the v3 of the program, an estimate of the lasing limit is made before increasing too much the Kp.
    * Fit the valid decay curve to extract the time constant ($\tau$) and calculate the damping rate ($\Gamma$).
    * Verify that increasing $K_p$ reduces the transient time constant before proceeding.

### Step 4: Engage Steady State
Once the calibration scan is complete and we have the linear fit parameters ($\Gamma_{native}$ and $\alpha$), we can lock the system into its new Q-state.

**1. Calculate and Apply Final Q-Control Gain**
Calculate the $K_p$ required for the desired target Q. This formula handles both active damping (positive $K_p$) and Q-enhancement (negative $K_p$):
$$K_{p\_target} = \frac{\frac{\pi \cdot f_0}{Q_{target}} - \Gamma_{native}}{\alpha}$$
* Set the value to PID 3: `/{dev}/pids/2/p` -> $K_{p\_target}$
* Enable PID 3 permanently: `/{dev}/pids/2/enable` -> `1`

**2. Scale the PLL**
Changing the Q-factor directly alters the phase slope ($d\Theta/df$) near resonance. Lowering Q flattens the slope (requiring more PLL gain), while increasing Q steepens the slope (requiring less PLL gain). 
Scale the PID 1 Proportional and Integral gains based on the Q-ratio to maintain your original tracking bandwidth:
$$P_{new} = P_{native} \times \frac{Q_{native}}{Q_{target}}$$
$$I_{new} = I_{native} \times \frac{Q_{native}}{Q_{target}}$$
* Update PID 1 P-gain: `/{dev}/pids/0/p` -> $P_{new}$
* Update PID 1 I-gain: `/{dev}/pids/0/i` -> $I_{new}$
*(Note: the PLL and Q control will work if the Osc2 follows the frequency of Osc1. This is pssible with the MF option or by referencing the Osc2 to have the Osc1 frequency, via EstRef)*

**3. Engage the AGC**
Now that the active damping or enhancement has altered the natural amplitude, turn on the AGC to automatically adjust the drive voltage and hold the amplitude at your target setpoint.
* Enable PID 4: `/{dev}/pids/3/enable` -> `1`

**4. Begin Experiment**
The multi-loop system is now fully locked. You can begin mass-loading experiments, continuously logging the Oscillator 1 frequency.


---


## Q-Control Signal Flow Diagram

![Q-Control Flow Diagram](q-control-flow.png)


## Part 2: Hardware & System Topology

### A. Hardware Wiring & Output Routing
* **Input Signal (`Signal Input 1`):** Resonator response. Feeds all four Demods.
* **Drive Output (`Signal Output 1`):** Main excitation, controlled by PID 4 (AGC). Set Phase to an appopriate value. Routed to Oscillator 1.
* **Q-Feedback (`Signal Output 2`):** Feedback force, controlled by PID 3 (Q-Control) (set demod 3 phase to 90.0 deg). **Must be explicitly routed to Oscillator 1. If this is not possible, the Osc 2 frequency must be set manually** 

> **Hardware:** Physically sum `Signal Output 1` and `Signal Output 2` using a BNC T-piece before connecting to the resonator.


### B. Demodulator Settings (Example for 6 MHz, Q=50k)
All Demods must be referenced to `Oscillator 1`. Enable data streaming ONLY for Demod 2 during the measurement phase (about 100 kSa/sec).

| Demodulator | Role | `timeconstant` Value | `order` Value | Base Node Path |
| :--- | :--- | :--- | :--- | :--- |
| **Demod 1** | **PLL Source** | `0.2 to 1e-3` (~200 us to 1 ms) | `4` (Standard) | `/{dev}/demods/0/` |
| **Demod 2** | **Measurement** | `10e-6` (10 µs) | `1` (Fast, for ring down) | `/{dev}/demods/1/` |
| **Demod 3** | **Q-Control** | `30e-6` (~30 µs) | `4` (Fast) | `/{dev}/demods/2/` |
| **Demod 4** | **AGC Source** | `100e-3` (~100 ms) | `4` (Slow) | `/{dev}/demods/3/` |


### C. Controller Configuration Reference (PIDs)
Configure the PID modules below. PID 2 is skipped. 

| Parameter | PID 1 (`/{dev}/pids/0/`) | PID 3 (`/{dev}/pids/2/`) | PID 4 (`/{dev}/pids/3/`) |
| :--- | :--- | :--- | :--- |
| **Function** | Frequency Tracking | Active Damping | Amplitude Stability |
| **Target BW** | `50` to `100` Hz | Scan dependent | Slow  |
| **Module Mode** | **PLL** | **PID** | **PID** |
| **Input Node** | `.../input` (Demod 1 Phase) | `.../input` (Demod 3 R) | `.../input` (Demod 4 R) |
| **Setpoint**| `.../setpoint` (Resonance Phase) | `.../setpoint` -> `0.0` | `.../setpoint` (Target Amp, measured amplitude at resonance before applying Q) |
| **Output Node** | `.../output` (Osc 1 Freq) | `.../output` (SigOut 2 Amp) | `.../output` (SigOut 1 Amp) |
| **P-Gain (Kp)** | `.../p` (Sign-Dependent) | `.../p` (Variable Scan) | `.../p` (Strictly Positive) |
| **I-Gain (Ki)** | `.../i` (Sign-Dependent) | `.../i` -> `0.0` | `.../i` (Strictly Positive) |
| **D-Gain (Kd)** | `.../d` -> `0.0` | `.../d` -> `0.0` | `.../d` -> `0.0` |


### D. Signal Output Routing & Phase Configuration
Physically sum `Signal Output 1` and `Signal Output 2` using a BNC T-piece before connecting to the resonator.

| Parameter | Signal Output 1 (Main Drive) | Signal Output 2 (Q-Feedback) |
| :--- | :--- | :--- |
| **Enable Node** | `/{dev}/sigouts/0/on` -> `1` | `/{dev}/sigouts/1/on` -> `1` |
| **Routing** | `/{dev}/sigouts/0/enables/3` -> `1` | `/{dev}/sigouts/1/enables/7` -> `1` |
| **Phase Node** | `/{dev}/demods/3/phaseshift` -> `0.0` | `/{dev}/demods/2/phaseshift` -> **`90.0` (Crucial)** |

* The nodes for signal outputs: ('sigouts/0/amplitudes/3', 0.1) and ('sigouts/1/amplitudes/7', 0.0)

> **Note on PID Polarity:** If parasitic capacitance inverts the phase slope, we must invert the P and I gains for **PID 1 only**. PID3 and PID4 normally use positive polarity, but verify the Q-control sign by checking that increasing $K_p$ increases damping (shorter $\tau$).

---

## Part 3: Mathematical & Software Reference

### A. The Step-Response Fit 
To extract the Q-factor, fit the transient amplitude envelope data from Demod 2 to:
$$A(t) = A_0 \cdot e^{-t/\tau} + C$$

Here, $C$ represents the 50% (or whatever value) steady-state amplitude baseline rather than the noise floor, ensuring the PLL signal remains robust. If there are parasitic capacitance (like me) there will be a short peak just at the moment of changing the voltage. There are two cases.
No peak at the change of the voltage

**Data Slicing via Sliding-Window Knee Detection:**
 To isolate the pure decay curve robustly I tested several methods like derivative, fitting t0,... and it appears the Knee Detector works quite well.
1.  Choose a sliding window size (N) of roughly 20 to 30 points (or approximating a few time delays of Demod 2 filter).
2.  Slide two adjacent windows of size N across the amplitude array. Fit a simple linear regression to each window to extract their local slopes (m1 and m2).
3.  Calculate the difference between the adjacent slopes (delta_m = m2 - m1). Search the array for the index where this difference is maximized. This pinpoints the corner where the flatline drops into the steep exponential transient.
4. Truncate the time and amplitude arrays starting from this index (or shift 5 to 10 points to the right to completely clear the filter's rounded shoulder). Subtract the first time value from the entire sliced time array so the pure transient fit starts at t=0 (or use a stepwise function to fit all).

**Data Slicing via non-linear fit**
If there is peak, the above mentioned method will not work well. In this case, I detect the peak, remove all data before the peak and then fit two decaying exponentials.


$$\text{Calculate Damping: } \Gamma = \frac{1}{\tau} = \frac{\pi \cdot f_0}{Q}$$

### B. Calibration and Dynamic Safety Logic

The PID 3 P-gain ($K_p$) can be used to either decrease or increase the Q-factor. Based on your positive slope fit, the relationship between $K_p$ and the effective system damping ($\Gamma$) is:
$$\Gamma(K_p) = \Gamma_{native} + \alpha \cdot K_p$$

Where $\Gamma_{native}$ (the y-intercept) and $\alpha$ (the positive slope) are obtained by fitting the extracted damping rates against your scanned $K_p$ values.

* **Active Damping (Lowering Q):** Applying a positive $K_p$ adds artificial viscous damping to the system.
* **Q-Enhancement (Increasing Q):** Applying a negative $K_p$ counteracts natural damping, increasing the effective Q.

**Reaching the Target Q:**
Once the calibration scan is complete and your slope $\alpha$ is accurately fitted, calculate the exact $K_p$ required for your target Q. The formula natively handles both active damping and Q-enhancement:
$$K_{p\_target} = \frac{\frac{\pi \cdot f_0}{Q_{target}} - \Gamma_{native}}{\alpha}$$
*(Note: If $Q_{target} > Q_{native}$, the formula will correctly yield a negative $K_p$.)*

**Dynamic Lasing Threshold & Safety Limits:**
When enhancing the Q-factor ($K_p < 0$), you risk pushing the total damping to zero or below, causing the amplitude to grow exponentially (Lasing).
* **Lasing Threshold:** $K_{p\_lasing} = -\frac{\Gamma_{native}}{\alpha}$
* **Dynamic Limit:** When automating a scan for Q-enhancement, calculate a preliminary fit and cap your negative $K_p$ array at 80% to 90% of $K_{p\_lasing}$.
* **Hardware Limits (Fail-Safe):** Always apply the hardware limits (`pids/2/limitlower` and `limitupper` to `-0.25` and `0.25` V) to act as a hard physical fail-safe against lasing or saturation.

---

## Demodulator Settings for HIPIMS DAQ Operation

**Application:** HIPIMS (High Power Impulse Magnetron Sputtering) with  
- PLL active  
- Q-Control active  
- AGC active  
- DAQ streaming on Demod 2  
- Example resonator: ~6 MHz QCM, native Q ≈ 50k  
- Instrument: Zurich Instruments UHFLI  

The goal is to capture fast plasma transients while maintaining stable multi-loop control.

---

### Recommended Demodulator Configuration

| Demodulator | Role | Recommended Time Constant | Filter Order | Purpose |
|-------------|------|--------------------------|--------------|---------|
| **Demod 1** | **PLL Source** | **0.3 – 1 ms** | 4 | Stable phase tracking without reacting to plasma spikes |
| **Demod 2** | **DAQ Measurement** | **.1 – 1 µs** | **1 (Critical)** | High temporal resolution, minimal filter delay |
| **Demod 3** | **Q-Control Source** | **20 – 50 µs** | 4 | Fast damping control without noise amplification |
| **Demod 4** | **AGC Source** | **50 – 200 ms** | 4 | Slow amplitude stabilization; must not follow pulses |

---

### Design Rationale

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

### Loop Hierarchy Requirement

For stable multi-loop operation:

$\tau(\text{Demod } 2) \ll \tau(\text{Demod } 3) \ll \tau(\text{Demod } 1) \ll \tau(\text{Demod } 4)$

Fast → Slow ordering prevents loop interaction and instability.

---

### Important Measurement Note

While Q-control is engaged, the measured damping is:

$\Gamma_{effective} = \Gamma_{native} - \alpha \cdot K_p$

Thus, during HIPIMS operation:
- Frequency shifts are physically meaningful.
- Measured Q reflects the actively controlled system.
- Native damping requires disabling PID 3 and performing a partial ring-down transient.

---