# Practical Guide: Active Q-Control on Zurich Instruments UHF
Based on notes from R. Stomp see https://www.zhinst.com/europe/en/blogs/resonance-engineering-quality-factor-q-control-method


**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Topology:** 4-Demodulator "Mnemonic" Setup (1=PLL, 2=Measurement, 3=Q, 4=AGC)  

---

## Part 1: The Experimental Workflow

This section outlines the logical sequence to initialize the system, calibrate the active damping, and lock the resonator for measurement.

### Step 1: Initial Sweep & Characterization
Before engaging any control loops, we must find the natural state of the QCM.
1. Run a frequency sweep across the expected resonance (e.g., around 6 MHz).
2. Calculate the native resonance frequency ($f_0$), bandwidth (BW), and native Q-factor from the amplitude peak .
3. Locate the frequency where the phase slope ($d\Theta/df$) is steepest. 
4. Record the exact phase angle at this steepest point. **This is the resonance phase setpoint.** (Lorentz fit and Pratt circle should give similar values; use unwrap in sweep ?)
5. Check the slope direction: If it goes down through resonance, the slope is Normal. If it goes up (due to parasitic capacitance), the slope is Inverted.

### Step 2: Engage Frequency Tracking (PID 1)
The Phase Locked Loop (PLL) must be engaged first and remain active continuously.
1. Use the PID Advisor to calculate baseline Proportional (P) and Integral (I) gains for a target bandwidth of 10 to 50 Hz.
2. Apply the polarity rule: If your phase slope is Normal, use Negative P and I gains. If Inverted, use Positive P and I gains. **D-Gain is always 0.**
3. Apply your measured phase setpoint from Step 1 to PID 1.
4. Enable PID 1 (in PLL). The lock-in will now continuously track the resonance frequency.

### Step 3: Q-Calibration & Scanning (PID 3)
With the frequency locked, we must calibrate the relationship between the Q-Control P-gain ($K_p$) and the physical damping ($\Gamma$).
1. Ensure PID 3 P-gain starts at 0.
2. Define a safe $K_p$ scan array (e.g., 0.0 to 10.0).
3. **For each $K_p$ value in the array:**
    * Apply $K_p$ to PID 3, **enable PID 3** (`pids/2/enable -> 1`), and wait 500 ms for the system to settle.
    * Subscribe to the Demod 2 data stream via software and begin polling (or use DAQ or scope ?).
    * Cut the drive signal (`sigouts/0/on -> 0`).
    * MEasure ~30 - 50 ms for the amplitude to ring down completely.
    * Restore the drive signal (`sigouts/0/on -> 1`) and stop polling.
    * **Disable PID 3** (`pids/2/enable -> 0`) before iterating to the next gain value.
    * **Safety Check:** If the amplitude grew instead of decaying, we have crossed the lasing threshold. Abort the scan and force PID 3 to 0.
    * Fit the valid decay curve to extract the time constant ($\tau$) and calculate the damping rate ($\Gamma$).
    * Verify that increasing Kp reduces ring-down time constant before proceeding.

### Step 4: Engage Steady State
1. Using the linear fit of the calibration data, we calculate the $K_p$ required for the target Q (e.g., 10k).
2. Apply this final $K_p$ to PID 3 and **enable PID 3 permanently** (`pids/2/enable -> 1`). The resonator should now actively be damped.
3. **Scale the PLL:** Because lowering the Q widens the bandwidth and alters the phase slope, scale the PID 1 gains to maintain stability: $P_{new} = P_{native} \times \frac{Q_{native}}{Q_{target}}$.
4. **Engage AGC:** **Enable PID 4** (`pids/3/enable -> 1`) to adjust the drive voltage and keep the amplitude stable at the target setpoint.
5. Begin the mass-loading experiment, logging the Oscillator 1 frequency continuously.

---


## Q-Control Signal Flow Diagram

![Q-Control Flow Diagram](q-control-flow.png)


## Part 2: Hardware & System Topology

### A. Hardware Wiring & Output Routing
* **Input Signal (`Signal Input 1`):** Resonator response. Feeds all four Demods.
* **Drive Output (`Signal Output 1`):** Main excitation, controlled by PID 4 (AGC). Set Phase to 0.0 deg. Routed to Oscillator 1.
* **Q-Feedback (`Signal Output 2`):** Feedback force, controlled by PID 3 (Q-Control). Set Phase to 90.0 deg. **Must be explicitly routed to Oscillator 1.**

> **Critical Hardware Step:** Physically sum `Signal Output 1` and `Signal Output 2` using a BNC T-piece before connecting to the resonator.

### B. Demodulator Settings (Example for 6 MHz, Q=50k)
All Demods must be referenced to `Oscillator 1`. To optimize USB bandwidth, enable data streaming ONLY for Demod 2 during the ring-down phase.

| Demodulator | Role | Time Constant (TC) | Filter Order |
| :--- | :--- | :--- | :--- |
| **Demod 1** | **PLL Source** | ~1 ms | 4 (Standard) |
| **Demod 2** | **Measurement** | **10 µs** | **1 (Crucial to prevent filter delay)** |
| **Demod 3** | **Q-Control** | ~30 µs | 4 (Fast) |
| **Demod 4** | **AGC Source** | ~100 ms | 4 (Slow) |


### C. Controller Configuration Reference
Configure the PID modules in your API. Note that PID 2 is skipped.

| Parameter | PID 1 | PID 3 (Q-Control) | PID 4 (AGC) |
| :--- | :--- | :--- | :--- |
| **Function** | Frequency Tracking | Active Damping | Amplitude Stability |
| **Module Mode** | **PLL** | **PID** | **PID** |
| **Input Source** | Demod 1 Phase | Demod 3 R (Amp) | Demod 4 R (Amp) |
| **Setpoint** | Measured Phase at Resonance | 0.0 V | Target Amp (the measured R value at demod 4 |
| **Output Channel**| Oscillator 1 Freq | Signal Output 2 Amp | Signal Output 1 Amp |
| **Output Phase** | N/A | 90.0 deg (Crucial) | 0.0 deg |
| **P-Gain (Kp)** | Adaptive & Sign-Dependent | Variable (Scan this) | Strictly Positive |
| **I-Gain (Ki)** | Sign-Dependent | Zero | Strictly Positive (Slow) |
| **D-Gain (Kd)** | Zero (Do not use) | Zero | Zero |

> **Critical Note on PID Polarity:** If parasitic capacitance inverts the phase slope, we must invert the P and I gains for **PID 1 only**. PID3 and PID4 normally use positive polarity, but verify the Q-control sign by checking that increasing Kp increases damping (shorter τ).

---

## Part 3: Mathematical & Software Reference

### A. The Ring-Down Fit & Data Slicing
To extract the Q-factor, fit the amplitude envelope data from Demod 2 to:
$$A(t) = A_0 \cdot e^{-t/\tau} + C$$

**LabVIEW Array Truncation Logic:**
Standard curve-fitting VIs fail if fed flatlines. We must isolate the decay curve:
1. **Find Trigger ($A_0$):** Average the first 100 samples to find the pre-trigger baseline. Search the array for the first index where amplitude drops below 95% of this baseline.
2. **Find Noise Floor ($C$):** Average the final 10% of the array. Search for the first index where amplitude drops to within 1% of this floor.
3. **Slice & Zero:** Truncate the time and amplitude arrays using these start/end indices. Subtract the first time value from the entire time array so the fit starts perfectly at $t=0$.


### Robust Array Truncation via Derivative (Finding $t_0$)

Instead of relying on a static 95% amplitude threshold to find the start of the decay, a more mathematically robust method is to locate the inflection point of the signal transition.

1. **Calculate the Derivative:** Compute the discrete first derivative ($dA/dt$) of the Demod 2 amplitude array (or of the smoothed data).
2. **Locate the Minimum:** Find the array index where this derivative reaches its absolute minimum (the most negative slope). 
3. **Define $t_0$:** This index represents the steepest part of the signal drop-off, marking the exact moment the lock-in filter responds to the drive cut ($t_0$).
4. **Slice the Array:** Truncate all data prior to this index. Subtract the time value at this new first index from the rest of the time array to force the pure decay curve to start perfectly at $t=0$.

This derivative method is better suited to baseline noise and slow amplitude drifts, getting a true exponential envelope for a stable fit.

$$\text{Calculate Q: } Q = \pi \cdot f_0 \cdot \tau$$
$$\text{Calculate Damping: } \Gamma = \frac{1}{\tau} = \frac{\pi \cdot f_0}{Q}$$

### B. Calibration and Safety Logic
The relationship between PID 3 P-gain ($K_p$) and system damping ($\Gamma$) is linear:
$$\Gamma(K_p) = \Gamma_{native} - \alpha \cdot K_p$$

$$\Gamma_{native} and \alpha are obtained from fit K_p$$

To hit a specific target Q, solve for $K_{p,target}$:
$$K_{p,target} = \frac{\Gamma_{native} - \frac{\pi \cdot f_0}{Q_{target}}}{\alpha}$$

**Lasing Threshold:** If $K_p$ is set too high, total damping becomes negative, causing amplitude to grow exponentially (Lasing). 
* Calculate maximum safe gain: $K_{p,max} = \frac{\Gamma_{native}}{\alpha}$.
* Apply hardware limits (`pids/2/limitlower` and `limitupper`) to $\pm 0.5$ V to prevent damage.


---
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

τ(Demod 2) ≪ τ(Demod 3) ≪ τ(Demod 1) ≪ τ(Demod 4)

Fast → Slow ordering prevents loop interaction and instability.

---

### Important Measurement Note

While Q-control is engaged, the measured damping is:

Γ_effective = Γ_native − α·Kp

Thus, during HIPIMS operation:
- Frequency shifts are physically meaningful.
- Measured Q reflects the actively controlled system.
- Native damping requires disabling PID 3 and performing a ring-down.

---
