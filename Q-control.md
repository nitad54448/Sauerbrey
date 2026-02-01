# Reference Guide: Active Q-Control on Zurich Instruments UHF

**Application:** QCM / Resonator Tracking with Active Damping  
**Instrument:** Zurich Instruments UHFLI (UHF-Lock-in)  
**Date:** February 2026

---

## 1. System Topology

To achieve stable Q-control while tracking resonance, the system requires three independent feedback loops operating simultaneously:

1.  **PID 1 (PLL): Frequency Tracker** Keeps the oscillator locked to the resonance peak ($f_0$).
2.  **PID 2 (Q-Control): Electronic Damping** Modifies the effective Q-factor by injecting a force proportional to velocity.
3.  **PID 3 (AGC): Amplitude Stabilizer** Adjusts the drive voltage to maintain constant oscillation amplitude.

---

## 2. Hardware Wiring & Setup

| Signal Path | UHF Connection | Connection Detail |
| :--- | :--- | :--- |
| **Drive Output** | `Signal Output 1` | Connect to Resonator Drive pin (via Adder/Splitter). |
| **Q-Feedback** | `Signal Output 2` | Connect to Resonator Drive pin (via Adder/Splitter). |
| **Input Signal** | `Signal Input 1` | Connect to Resonator Readout pin. |

> **Important:** You must sum `Signal Output 1` and `Signal Output 2` physically (using a signal combiner or T-piece) before they reach the resonator.

---

## 3. Controller Configuration Reference

Use this table to configure the PID modules in your software (LabVIEW/Python/Matlab).

| Parameter | **PID 1 (PLL)** | **PID 2 (Q-Control)** | **PID 3 (AGC)** |
| :--- | :--- | :--- | :--- |
| **Function** | **Frequency Tracking** | **Active Damping** | **Amplitude Stability** |
| **Input Signal** | `Demod 1 Phase` ($\Theta$) | `Demod 1 R` (Amplitude) | `Demod 1 R` (Amplitude) |
| **Setpoint** | **0.0 deg** (or offset) | **0.0 V** | **Target Amplitude** (e.g. 0.1 V) |
| **Output Channel** | `Oscillator 1 Freq` | `Signal Output 2 Amp` | `Signal Output 1 Amp` |
| **Output Physics** | Adjusts Frequency ($Hz$) | Adjusts Damping Force ($N$) | Adjusts Drive Force ($N$) |
| **Output Phase** | N/A | **90.0°** (Crucial) | **0.0°** |
| **P-Gain (Kp)** | Tuned for BW (Negative) | **Variable** (Scan this) | **Positive** |
| **I-Gain (Ki)** | Required | **Zero** | **Positive** (Slow) |
| **D-Gain (Kd)** | Zero | **Zero** | **Zero** |
| **Output Range** | $\pm$ 10 kHz (Example) | $\pm$ 0.5 V (Safety Limit) | 0.0 V to 1.0 V |

---

## 4. Programming Algorithm (Step-by-Step)

### Phase A: Initialization (Safe State)
1.  **Disable Control:** Set `enable` = `0` for PID 1, 2, and 3.
2.  **Config Drive (Sig 1):**
    * `sigouts/0/on` = `1`
    * `sigouts/0/phaseshift` = `0.0`
    * `sigouts/0/amplitudes/0` = `Safe_Start_Level`
3.  **Config Feedback (Sig 2):**
    * `sigouts/1/on` = `1`
    * `sigouts/1/phaseshift` = **90.0** (CRITICAL setting for Q-control)
    * `sigouts/1/amplitudes/0` = `0.0` (Start zeroed)

### Phase B: Characterization (Open Loop)
4.  **Sweep:** Run Frequency Sweeper on Signal 1.
5.  **Measure:** Extract $f_{native}$ (Resonance Freq) and $Q_{native}$.
6.  **Set Oscillator:** `oscs/0/freq` = $f_{native}$.

### Phase C: Lock Frequency (PID 1)
7.  **Setup PID 1:** Input=`Phase`, Output=`Freq`, Setpoint=`0`.
8.  **Engage:** `pids/0/enable` = `1`.
9.  **Wait:** Poll until Error is near zero (Locked).

### Phase D: Q-Calibration Loop (Scanning PID 2)
*Goal: Find the relationship between P-gain and Q.* *Ensure PID 3 (AGC) is OFF during this phase.*

10. **Define Array:** Create list of P-gains to test (e.g., `[-10, 0, 10, 50]`).
11. **Loop through Array:**
    * Set `pids/1/kp` = current value.
    * Enable PID 2.
    * Wait 500ms for settling.
    * **Ring-Down Measurement:**
        1.  Trigger Scope (Single Shot).
        2.  Set `sigouts/0/on` = `0` (Cut Drive).
        3.  Wait for Scope record.
        4.  Set `sigouts/0/on` = `1` (Restore Drive).
    * **Calculate:** Fit exponential decay $\tau$. Store pair `[P, 1/τ]`.

### Phase E: Set Target & Run
12. **Calculate:** Fit line to $\Gamma(P) = m \cdot P + c$. Solve for $P_{target}$ using desired Q.
    * $P_{target} = (\Gamma_{native} - \Gamma_{target}) / m$
13. **Apply Q:** Write $P_{target}$ to `pids/1/kp`.
14. **Engage AGC (PID 3):**
    * Set Setpoint = Target Amplitude.
    * Set `pids/2/enable` = `1`.
15. **Ready:** System is now tracking frequency with modified Q and stable amplitude.

---

## 5. Mathematical Reference

**Exponential Decay Fit:**
$$A(t) = A_0 \cdot e^{-t/\tau}$$

**Q-Factor from Decay:**
$$Q = \pi \cdot f_0 \cdot \tau$$

**Damping Rate ($\Gamma$):**
$$\Gamma = \frac{1}{\tau} = \frac{\pi \cdot f_0}{Q}$$

**Safety Check:**
Ensure $\Gamma > 0$. If $\Gamma \le 0$, the system will self-oscillate (Lase). Add a software limit to the P-gain to prevent this.