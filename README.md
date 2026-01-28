# QCM Analyst

**QCM Analyst** is a lightweight, browser-based tool for visualizing and analyzing Quartz Crystal Microbalance (QCM) data. It allows researchers to load experimental datasets, simulate frequency responses, and calculate thin-film thickness using both Sauerbrey and Z-Match (Lu and Lewis) methods.

##  Features

* **Data Visualization:** Drag-and-drop support for `.dat`, `.txt`, and `.csv` files.
* **Interactive Controls:** Plot simulation curves (sigmoid) against experimental data to determine frequency shifts ($\Delta f$).
* **Automatic Calculation:**
    * Real-time calculation of Mass and Thickness.
    * Automatic switching between **Sauerbrey** and **Z-Match** equations based on loading thresholds.
* **Reporting:** Generates a PDF report including the chart and all calculated parameters.
* **Zero Dependencies:** Runs entirely in the browser using vanilla JS and CDNs (Chart.js, jsPDF).

---

##  Usage

1.  **Open:** Simply open `.html` in any modern web browser.
2.  **Load Data:** Click **"Load Data File"** to upload your QCM frequency data (Time vs. Frequency).
    * *Format:* Two columns separated by tabs, spaces, or commas; or a proprietary file format that is used in our labs (no interest for external users)
3.  **Set Parameters:**
    * **Crystal Freq:** The fundamental frequency of quartz (e.g., 5 MHz).
    * **Active Diameter:** The diameter of the electrode area (usually smaller than the total crystal diameter).
    * **Material:** Select a preset (Au, Ti, SiO2, etc.) or enter custom Density and Z-Factor values.
4.  **Analyze:**
    * Use the **Cursors** (vertical lines on the chart) to define the start and end of the deposition/adsorption event.
    * Alternatively, toggle **Plot Sim** to manually fit a sigmoid curve to your data if the signal is noisy.
5.  **Export:** Click **Download Report** to save a PDF summary.

---

##  Technical Reference

### 1. Physical Constants of Quartz ($AT$-cut)
The tool uses the standard physical constants for AT-cut quartz crystals:

* **Density of Quartz ($\rho_q$):** $2.648 \text{ g/cm}^3$
* **Shear Modulus of Quartz ($\mu_q$):** $2.947 \times 10^{11} \text{ g/cm}\cdot\text{s}^2$

#### The Frequency Constant ($N_q$)
While the code calculates mass using $\rho_q$ and $\mu_q$ directly, these values define the Frequency Constant ($N_q$), which represents the relationship between the crystal thickness and its resonant frequency.

$$N_q = \frac{1}{2} \sqrt{\frac{\mu_q}{\rho_q}} \approx 1668 \text{ kHz}\cdot\text{mm}$$

### 2. Acoustic Impedance ($Z$)
Acoustic impedance ($Z$) is a measure of the resistance a material offers to the propagation of an acoustic wave. It is defined as the product of density and acoustic velocity (or the square root of density times shear modulus).

$$Z = \sqrt{\rho \cdot \mu}$$

The **Z-Factor** used in this tool is the ratio of the acoustic impedance of the quartz to that of the film material:

$$Z_{ratio} = \frac{Z_q}{Z_f} = \sqrt{\frac{\rho_q \mu_q}{\rho_f \mu_f}}$$

* **Why is this important?** When an acoustic wave travels from the quartz into the film, a mismatch in $Z$ causes reflections at the interface.
* **Soft vs. Rigid:** "Soft" materials (like polymers) have high Z-Factors ($Z_{ratio} > 1$), while rigid metals often have Z-Factors closer to 1 or lower.

---

### 3. Calculation Methods

The tool automatically selects the appropriate equation based on the frequency shift magnitude.

#### A. The Sauerbrey Equation
**Condition:** Used when $\frac{\Delta f}{f_0} \leq 2\%$

The Sauerbrey equation assumes the deposited film is rigid and sufficiently thin that it can be treated purely as added mass, without considering its elastic properties.

$$\Delta m = - \frac{A \sqrt{\rho_q \mu_q}}{2 f_0^2} \Delta f$$

And thickness ($d_f$):

$$d_f = \frac{\Delta m}{A \cdot \rho_f}$$

** $Z$ is ignored here:**
In the Sauerbrey limit (thin rigid films), the acoustic wave acts as if it is still propagating through quartz. The impedance mismatch is negligible because the wave does not travel far enough into the film to experience significant phase shift or reflection errors. Therefore, the Z-Factor is assumed to be 1 ($Z_q = Z_f$).

#### B. The Z-Match Equation (Lu and Lewis)
**Condition:** Used when $\frac{\Delta f}{f_0} > 2\%$

As the film gets thicker or softer, the "missing mass" error in Sauerbrey calculations increases. The Z-Match method (derived from the one-dimensional acoustic composite resonator model) corrects for the acoustic impedance mismatch between the quartz and the film.

The tool implements the standard Lu and Lewis equation to solve for areal mass density ($\sigma$ in g/cm²):

$$\sigma = \left( \frac{\sqrt{\rho_q \mu_q}}{\pi f_{end} Z_{ratio}} \right) \cdot \arctan \left( Z_{ratio} \cdot \tan \left( \pi \frac{f_0 - f_{end}}{f_0} \right) \right)$$

Where:
* $f_0$ = Fundamental frequency (start)
* $f_{end}$ = Loaded frequency (end)
* $Z_{ratio}$ = Z-Factor input by the user

---

##  Tools

* **HTML5 / CSS3:** Responsive grid layout.
* **Chart.js:** Rendering the interactive canvas.
* **Hammer.js & chartjs-plugin-zoom:** Pan and zoom capabilities.
* **jsPDF:** Client-side PDF generation.

---

## License
MIT
