# Reference Guide: Active Q-Control on Zurich Instruments UHF

**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Topology:** 4-Demodulator Setup (PLL, DAQ, Q-Control, AGC)  
**Date:** February 2026

---

## 1. System Topology & Demodulator Mapping

To ensure stability and measurement speed, we separate the control loops from the measurement line.

| Index | Function | Role | Critical Setting |
| :--- | :--- | :--- | :--- |
| **Demod 1** | **PLL Source** | Feeds PID 1 to track frequency. | **TC:** ~1 ms (Medium bandwidth). |
| **Demod 2** | **Measurement** | Reserved for high-speed DAQ/Scope recording (Ring-down). | **TC:** **Min** (e.g., 10 µs). Must be fast to see decay. |
| **Demod 3** | **Q-Control** | Feeds PID 2 to create damping force. | **TC:** Low (e.g., 30 µs). Fast feedback required. |
| **Demod 4** | **AGC Source** | Feeds PID 3 to stabilize amplitude. | **TC:** High (e.g., 100 ms). Slow integration. |

> **Note:** All 4 Demodulators must be set to the **same Oscillator** (e.g., Oscillator 1).

---

## 2. Hardware Wiring & Setup

| Signal Path | UHF Connection | Connection Detail |
| :--- | :--- | :--- |
| **Drive Output** | `Signal Output 1` | Main excitation. Controlled by AGC. |
| **Q-Feedback** | `Signal Output 2` | Feedback force. Controlled by Q-PID. |
| **Input Signal** | `Signal Input 1` | Resonator response. Feeds all Demods. |

> **Critical Hardware Step:** You must physically sum `Signal Output 1` and `Signal Output 2` (using a BNC T-piece or combiner) before connecting to the resonator drive pin.

---

## 3. Controller Configuration Reference

Use this table to configure the PID modules in LabVIEW.

| Parameter | **PID 1 (PLL)** | **PID 2 (Q-Control)** | **PID 3 (AGC)** |
| :--- | :--- | :--- | :--- |
| **Function** | **Frequency Tracking** | **Active Damping** | **Amplitude Stability** |
| **Input Source** | **Demod 1 Phase** ($\Theta$) | **Demod 3 R** (Amp) | **Demod 4 R** (Amp) |
| **Setpoint** | **0.0 deg** | **0.0 V** | **Target Amplitude** (e.g. 0.1 V) |
| **Output Channel** | `Oscillator 1 Freq` | `Signal Output 2 Amp` | `Signal Output 1 Amp` |
| **Output Phase** | N/A | **90.0°** (Crucial) | **0.0°** |
| **P-Gain (Kp)** | Tuned (Negative) | **Variable** (Scan this) | **Positive** |
| **I-Gain (Ki)** | Required | **Zero** | **Positive** (Slow) |
| **Output Range** | $\pm$ 10 kHz | $\pm$ 0.5 V (Safety Limit) | 0.0 V to 1.0 V |

---

## 4. LabVIEW Programming Algorithm

### Phase A: Initialization (Safe State)
1.  **Define Connections:** Open LabOne API Session.
2.  **Configure Oscillator:**
    * `oscs/0/freq` -> Target Freq (e.g., 10 MHz)
3.  **Configure Demods (The 4-Demod Setup):**
    * **Loop i = 0 to 3:** Set `demods/i/oscselect` -> `0`.
    * **Demod 1 (PLL):** `demods/0/timeconstant` -> `1e-3` (1ms), `order` -> 4.
    * **Demod 2 (DAQ):** `demods/1/timeconstant` -> `10e-6` (10µs), `order` -> 8 (Steep filter).
    * **Demod 3 (Q):** `demods/2/timeconstant` -> `30e-6` (30µs).
    * **Demod 4 (AGC):** `demods/3/timeconstant` -> `100e-3` (100ms).
    * **Enable All:** `demods/*/enable` -> `1`.
4.  **Configure Outputs:**
    * **Sig 1 (Drive):** `sigouts/0/on` -> `1`, `phaseshift` -> `0.0`, `amp` -> `0.05`.
    * **Sig 2 (Feedback):** `sigouts/1/on` -> `1`, `phaseshift` -> `90.0`, `amp` -> `0.0`.
5.  **Disable PIDs:** Set `pids/0..2/enable` -> `0`.

### Phase B: Lock Frequency (PID 1)
6.  **Setup PID 1 Node Paths:**
    * `pids/0/inputchannel` -> `0` (Demod 1)
    * `pids/0/input` -> `3` (Theta/Phase)
    * `pids/0/outputchannel` -> `0` (Oscillator 1)
    * `pids/0/output` -> `2` (Frequency)
    * `pids/0/setpoint` -> `0.0`
    * `pids/0/kp`, `ki` -> Tuned values.
7.  **Engage:** `pids/0/enable` -> `1`.
8.  **Wait Loop:** Read `pids/0/error` until absolute value is small.

### Phase C: Q-Calibration Loop (Scanning PID 2)
*Using Demod 2 for Measurement, Demod 3 for Control.*

9.  **Setup PID 2 (Q-Control):**
    * `pids/1/inputchannel` -> `2` (Demod 3)
    * `pids/1/input` -> `2` (R/Amplitude)
    * `pids/1/outputchannel` -> `1` (Sig Out 2)
    * `pids/1/output` -> `1` (Amplitude)
    * `pids/1/setpoint` -> `0.0`
    * `pids/1/kp` -> **0** (Start)
10. **Configure LabOne DAQ Module (in LabVIEW):**
    * *Trigger Source:* `SigOut 1 Enable` (Hardware Trigger).
    * *Signal Path:* `demods/1/sample.r` (Demod 2 R).
    * *Edge:* Falling (Trigger when drive turns off).
11. **Scan Loop (Iterate P-Gain):**
    * **Update P:** `pids/1/kp` -> `P_Value`. `pids/1/enable` -> `1`.
    * **Wait:** 500ms (Settle).
    * **Arm DAQ:** Execute `DAQ.Execute(Record)`.
    * **Cut Drive:** `sigouts/0/on` -> `0`.
    * **Wait for Record:** Poll DAQ module until finished.
    * **Restore Drive:** `sigouts/0/on` -> `1`.
    * **Fetch Data:** Get Waveform from DAQ module.
    * **Compute:** Fit exponential to Demod 2 data. Get $\tau$.

### Phase D: Engage Steady State
12. **Set Optimal Q:**
    * `pids/1/kp` -> Calculated Target P.
    * `pids/1/enable` -> `1`.
13. **Setup PID 3 (AGC):**
    * `pids/2/inputchannel` -> `3` (Demod 4)
    * `pids/2/input` -> `2` (R/Amplitude)
    * `pids/2/outputchannel` -> `0` (Sig Out 1)
    * `pids/2/output` -> `1` (Amplitude)
    * `pids/2/setpoint` -> Target Amp.
14. **Engage:** `pids/2/enable` -> `1`.

---

## 5. LabVIEW Node Reference

When using the `ziDotNET` assembly in LabVIEW, use these value types:

* **Demod Input Enum:** `pids/n/input`
    * `0`: Demod X
    * `1`: Demod Y
    * `2`: Demod R (Use this for PID 2 & 3)
    * `3`: Demod Theta (Use this for PID 1)
* **PID Output Enum:** `pids/n/output`
    * `0`: Signal Output 1 Amplitude
    * `1`: Signal Output 2 Amplitude (Use this for PID 2)
    * `2`: Oscillator Frequency (Use this for PID 1)
* **Triggering DAQ:**
    * Use the **Data Acquisition Module** class, not `poll()`.
    * `trigger/channel` node in the module settings corresponds to the specific hardware trigger line (e.g., Signal Output 1 Enable).

## 6. Safety Check (Lasing Prevention)
Ensure your LabVIEW code includes a "Panic Switch":
* Monitor `demods/1/sample.r` (Demod 2).
* If `R > Max_Limit` (e.g. 0.9V), immediately write `0` to `sigouts/*/on`.
* This prevents physical damage if P-gain is set too high (negative damping).