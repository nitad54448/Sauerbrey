# QCM_PLL Measurement Software Documentation

This software is designed to interface with a Zurich Instruments UHF-LI (or similar) to perform high-precision QCM measurements, frequency tracking, and dissipation (Q-factor) control.

---

## 1. Experiment Tab
The entry point of the application for hardware communication and configuration management.

* **Address:** Enter the device ID (e.g., `DEV2091`) of the instrument.
* **Connect:** Establishes communication with the hardware.
* **Load/Save cfg:** Allows importing or exporting instrument settings via `.xml` or `.cfg` files to ensure reproducibility.
* **Continue (Arrow):** Advances the workflow to the Sweep tab.

---

## 2. Sweep Tab
Used to characterize the resonator's resonance frequency ($f_0$) and Quality Factor ($Q$) before starting a track.

* **Sweep Parameters:** Set the **start/end** frequencies (typically around 5-6 MHz for standard crystals) and the number of **steps**.
* **R, theta:** Displays the amplitude ($R$) and phase response.
* **Nyquist:** Displays the real vs. imaginary part of the admittance/impedance, used for circular fitting.
* **Lorentz/Pratt Fit:** Automatically extracts:
    * **freq_0 ($f_0$):** Center resonance frequency.
    * **BW:** Bandwidth at half-maximum.
    * **Q:** The Quality factor ($f_0 / BW$).

---

## 3. Track f (Frequency Tracking)
The core real-time measurement tab using a PID loop to lock onto the resonance frequency.

* **Track f0 / ph:** Displays the current locked frequency and phase setpoint.
* **PID mode:** Usually set to **PI** for frequency tracking. 
* **BW factor:** Adjusts the tracking speed vs. stability.
* **Advisor:** Automatically calculates optimal PID gains based on the sweep data.
* **PLL Lock:** Indicators turn green when the system is successfully "locked" to the resonance.
* **Live Graph:** Monitors Frequency, Amplitude ($R$), and Phase over time.

---

## 4. Q-control Tab
Dedicated to active dissipation control or monitoring change in the damping of the crystal.

* **Actual Q:** Real-time display of the Quality factor.
* **Target Q:** Setpoint for active feedback to increase or decrease the effective Q.
* **Knee Detector:** Parameter for identifying the transition in the decay or response curve.
* **Gamma vs Kp:** Plots the relationship between the feedback gain and the damping coefficient.

---

## 5. DAQ (Data Acquisition)
Configures high-speed data capture for transient events.

* **Acquire / DAQ Points:** Defines the sampling rate and the number of points per trigger.
* **Trigger:** Set the source (e.g., Trigger 3) and the **Level (V)** at which data recording starts.
* **TC /usec:** The time constant for the digital filter.
* **Interval:** Time between automated successive measurements.

---

## 6. Status Tab
A high-level overview and system control panel.

* **Status Window:** Displays a log of system messages, errors, and connection confirmations.
* **Plotter:** Sends the current data view to a peripheral or file.
* **Quit:** Safely stops the instrument outputs and closes the LabVIEW application.