# QCM Analyst - IFF & Z-Match Edition

**QCM Analyst** is a lightweight, browser-based tool for visualizing and analyzing Quartz Crystal Microbalance (QCM) data. It allows researchers to load experimental datasets, calculate thin-film thickness using both Sauerbrey and Z-Match (Lu and Lewis) methods, and determine the **Ion Flux Fraction (IFF)** for plasma/ion-assisted deposition processes.

## Features

* **Data Visualization:** Drag-and-drop support for `.dat`, `.txt`, and `.csv` files.
* **Interactive Analysis:**
    * Interactive cursors to define analysis windows (Start/End).
    * Zoom and Pan capabilities for inspecting noisy data.
* **Automatic Calculation:**
    * Real-time calculation of Mass, Thickness, and Deposition Rate.
    * Automatic switching between **Sauerbrey** and **Z-Match** equations based on loading thresholds (2% frequency shift).
* **Ion Flux Fraction (IFF):** Dedicated module for calculating the ionic contribution to deposition flux by comparing "Reference" (Total) vs. "Neutral" rates.
* **Reporting:** Generates a PDF report including the chart, calculated parameters, and IFF results.
* **Zero Dependencies:** Runs entirely in the browser using vanilla JS and CDNs (Chart.js, jsPDF).

---

## Usage

1.  **Open:** Simply open the `.html` file in any modern web browser.
2.  **Load Data:** Click **"Load Data File"** to upload your QCM frequency data (Time vs. Frequency).
    * *Format:* Two columns (Time, Frequency) separated by tabs, spaces, or commas.
3.  **Set Parameters:**
    * **Crystal Freq/Diameter:** Defaults are set for standard 6 MHz / 10mm crystals.
    * **Material:** Select a preset (Au, Ti, SiO2, etc.) or enter custom Density and Z-Factor values.
4.  **Analyze (Interactive Chart):**
    * **Move Cursors:** Click and drag anywhere on the chart to move the **Start** and **End** range cursors.
    * **Pan/Zoom:** Hold **Ctrl + Drag** to pan the view. Scroll to zoom in/out.
    * The tool calculates the frequency shift ($\Delta f$) and thickness change between these two cursors.
5.  **Calculate IFF (Optional):**
    * Measure the rate during a "Reference" phase (Ions + Neutrals). Click **Set Current as Ref**.
    * Measure the rate during a "Neutral only" phase. The tool will automatically calculate the IFF percentage.
6.  **Export:** Click **Download Report** to save a PDF summary.

---

## Technical Reference

### 1. Physical Constants ($AT$-cut Quartz)
The tool uses standard physical constants:
* **Density ($\rho_q$):** $2.648 \text{ g/cm}^3$
* **Shear Modulus ($\mu_q$):** $2.947 \times 10^{11} \text{ g/cm}\cdot\text{s}^2$

### 2. Calculation Methods

The tool automatically selects the appropriate equation based on the frequency shift magnitude.

#### A. The Sauerbrey Equation
**Condition:** Used when ratio $R(t) = \frac{|f_L - f_U|}{f_U} < 0.02$

Assumes the film is rigid and thin. The Z-Factor is ignored ($Z_{ratio} = 1$).

$$\Delta m = - \frac{A \sqrt{\rho_q \mu_q}}{2 f_0^2} \Delta f$$

#### B. The Z-Match Equation (Lu and Lewis)
**Condition:** Used when $R(t) \geq 0.02$

Corrects for the acoustic impedance mismatch between quartz and the film material.
*Note: The formula below includes the derived constants used in the code.*

$$\sigma = \left( \frac{\sqrt{\rho_q \mu_q}}{2 \pi f_{end} Z_{ratio}} \right) \cdot \arctan \left( Z_{ratio} \cdot \tan \left( \pi \frac{f_0 - f_{end}}{f_0} \right) \right)$$

Where:
* $\sigma$ = Areal mass density (g/cm²)
* $f_0$ = Fundamental frequency (unload/start)
* $f_{end}$ = Loaded frequency
* $Z_{ratio}$ = Z-Factor ($\sqrt{\rho_q \mu_q / \rho_f \mu_f}$)

### 3. Ion Flux Fraction (IFF)
The IFF determines the fraction of the deposition flux contributed by ions vs. neutrals. It assumes the film density and composition remain constant between configurations.

**Theory:**
Since deposition flux ($\Gamma$) is proportional to deposition rate ($v_e$), we can compare the rates directly:

1.  **Reference Config ($v_{tot}$):** Ions + Neutrals are deposited.
2.  **Neutral Config ($v_{neutre}$):** Ions are repelled; only neutrals deposited.

$$IFF = \frac{\Gamma_{ions}}{\Gamma_{total}} = 1 - \frac{v_{neutre}}{v_{tot}}$$

---

## Tools & Libraries

* **Chart.js:** Rendering the interactive canvas.
* **chartjs-plugin-zoom:** Pan (Ctrl+Drag) and Zoom interactions.
* **chartjs-plugin-annotation:** Drawing the vertical analysis cursors.
* **jsPDF:** Client-side PDF generation.

---

## License
MIT