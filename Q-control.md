# Practical Guide: Active Q-Control on Zurich Instruments UHF

**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Topology:** 4-Demodulator "Mnemonic" Setup (1=PLL, 3=Q, 4=AGC)  


---

## 1. System Topology & Demodulator Mapping

We map the PIDs directly to their corresponding Demodulators. 
**Crucial Concept:** The PLL (PID 1) must be engaged first and remain active continuously. If the system drifts off resonance, Q-control and AGC will fail. 

* **Demod 1 (PLL Source):** Feeds PID 1 to track frequency. Tracks phase to ensure you are always driving exactly at resonance.
* **Demod 2 (Measurement):** Reserved for high-speed DAQ/Scope (Ring-down). 
* **Demod 3 (Q-Control):** Feeds PID 3 to create damping force. Provides instantaneous feedback without phase lag.
* **Demod 4 (AGC Source):** Feeds PID 4 to stabilize amplitude. Slow integration to keep drive voltage stable.

> **Note:** All 4 Demodulators must be set to the same Oscillator (e.g., Oscillator 1).

---

## 2. Hardware Wiring & Setup


* **Drive Output:** UHF Connection is Signal Output 1. This is the main excitation, controlled by AGC (PID 4).
* **Q-Feedback:** UHF Connection is Signal Output 2. This is the feedback force, controlled by Q-PID (PID 3).
* **Input Signal:** UHF Connection is Signal Input 1. This is the resonator response, which feeds all Demods.

> **Critical Hardware Step:** Physically sum Signal Output 1 and Signal Output 2 (using a BNC T-piece or combiner) before connecting to the resonator drive pin.

---

## 3. Practical Example: 6 MHz Crystal (Q = 50k)

For an EE student setting this up, raw numbers help. Let's calculate the system parameters for a 6 MHz crystal with a Q of 50,000 and a native bandwidth (BW) of ~120-200 Hz.

**System Physics:**
* Resonance Frequency (f0) = 6,000,000 Hz
* Decay Time Constant (tau) = Q / (pi * f0) = 50,000 / (pi * 6e6) = ~2.65 ms

**Recommended Demodulator Time Constants (TC):**
* **Demod 1 (PLL): ~1 to 3 ms.** Must be fast enough to track drift, but slow enough to reject noise. 
* **Demod 2 (DAQ): ~100 us.** Must be at least 10x faster than the 2.65 ms decay time to accurately capture the ring-down envelope.
* **Demod 3 (Q-Control): ~10 to 30 us.** Needs to be as fast as safely possible to provide real-time force feedback.
* **Demod 4 (AGC): ~50 to 100 ms.** Needs to be much slower than the crystal decay to avoid fighting the Q-control dynamics.

**PID Advisor Recommendations:**
* **PID 1 (PLL): YES.** Use the Advisor. Target a loop BW of ~10 to 50 Hz (well below the crystal's 200 Hz BW) to get your baseline Proportional (P) and Integral (I) gains.
* **PID 3 (Q-Control): NO.** The Advisor cannot model your physical acoustic feedback loop. Gain must be found manually via sweep.
* **PID 4 (AGC): YES.** Use the Advisor to target a very slow loop BW (~1 to 5 Hz).

---

## 4. Controller Configuration Reference

Configure the PID modules in LabVIEW (or other APIs). Note that PID 2 is skipped.

| Parameter | PID 1 (PLL) | PID 3 (Q-Control) | PID 4 (AGC) |
| :--- | :--- | :--- | :--- |
| **Function** | Frequency Tracking | Active Damping | Amplitude Stability |
| **Input Source** | Demod 1 Phase | Demod 3 R (Amp) | Demod 4 R (Amp) |
| **Setpoint** | 0.0 deg | 0.0 V | Target Amplitude (e.g. 0.1 V) |
| **Output Channel**| Oscillator 1 Freq | Signal Output 2 Amp | Signal Output 1 Amp |
| **Output Phase** | N/A | 90.0 deg (Crucial) | 0.0 deg |
| **P-Gain (Kp)** | Adaptive (See Section 6.E) | Variable (Scan this) | Positive |
| **I-Gain (Ki)** | Required | Zero | Positive (Slow) |

---

## 5. LabVIEW Programming Algorithm

### Phase A: Initialization (Safe State)
* Define Connections: Open LabOne API Session.
* Configure Oscillator: oscs/0/freq -> Target Freq (e.g., 6 MHz).
* Configure Demods (The 4-Demod Setup): Set all demodulators' oscselect to 0. Enable all Demods.
* Configure Outputs:
    * Sig 1 (Drive): Turn on, set phase to 0.0, set an initial safe amplitude (e.g., 0.05 V).
    * Sig 2 (Feedback): Turn on, set phase to 90.0, set amp to 0.0.
* Disable PIDs: Ensure PID 1, PID 3, and PID 4 are disabled.

### Phase B: Lock Frequency (PID 1)
* Characterize Phase Slope: During sweep, calculate slope S = dPhase / df at resonance.
    * If S < 0 (Normal): Use Negative P/I gains.
    * If S > 0 (Inverted): Use Positive P/I gains (invert the Advisor suggested values).
* Engage PID 1 and poll the error until locked. Keep this running for all subsequent phases.

### Phase C: Q-Calibration Loop (Scanning PID 3)
*Using Demod 2 for Measurement, Demod 3 for Control.*

* Setup PID 3 (Q-Control): Input is Demod 3 R, Output is Sig Out 2 Amp, Setpoint is 0. P-Gain starts at 0.
* Configure LabOne DAQ Module: Hardware trigger on SigOut 1 Enable falling edge. Signal Path is demods/1/sample.r (Demod 2 R).
* Scan Loop:
    1.  Update P-Gain on PID 3 and wait 500ms to settle.
    2.  Arm DAQ, cut drive (sigouts/0/on -> 0), and wait for record.
    3.  Restore drive, fetch data, and compute the exponential fit.

### Phase D: Engage Steady State
* Set Optimal Q: Apply calculated Target P to PID 3. Update PID 1 Gain by scaling PLL gains.
* Engage AGC: Setup PID 4 (Input = Demod 4 R, Output = Sig Out 1 Amp) and enable.

---

## 6. Technical & Mathematical Reference


### A. The Ring-Down Fit
To extract the Q-factor from the DAQ time-series data, fit the amplitude envelope to:
A(t) = A_0 * exp(-t / tau) + C

* A_0: Initial Amplitude (Volts).
* tau: Decay time constant (Seconds).
* C: Noise floor / Offset (Volts).

Calculating Q: Q = pi * f0 * tau
Calculating Damping Rate (Gamma): Gamma = 1 / tau = (pi * f0) / Q

### B. The P-Gain to Q Relationship (Calibration)
The relationship between the PID 3 P-gain (Kp) and the system damping is linear; fit Gamma vs P.
Gamma(Kp) = Gamma_native - alpha * Kp

Solving for target Kp:
Kp_target = (Gamma_native - ((pi * f0) / Q_target)) / alpha

### C. AGC Logic (PID 4)
The AGC reduces the Drive Voltage to keep Amplitude constant when Q increases. Use a big Integral (I) term. The Proportional (P) term should be positive but small to avoiding ringing in the amplitude domain.

### D. Safety: The Lasing Threshold
If Kp is set too high, total damping becomes negative, resulting in exponential amplitude growth (Lasing). Calculate the "Lasing P-gain" (Kp_max = Gamma_native / alpha) and set a software limit at about 80-90% of this value.

### E. PID Polarity & Phase Slope Handling
Some resonators exhibit an inverted phase slope due to capacitive feedthrough. Q-control does not fix this; it simply changes the slope.

* Normal (S < 0): Use Negative P and I gains for PID 1.
* Inverted (S > 0): Use Positive P and I gains for PID 1. The sign of P and I must match each other.
* As Q increases, the phase slope becomes steeper, so you must reduce PID 1 gains proportionally to prevent oscillation.
    P_new = P_native * (Q_native / Q_target)
