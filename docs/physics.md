# Physics and Calculations

QCM Analyst utilizes two primary models to convert frequency shift ($\Delta f$) into physical thickness ($d$).

## The 2% Threshold
The software monitors the ratio of the frequency shift to the fundamental frequency ($\Delta f / F_0$). 

### 1. Sauerbrey Model
For "thin" films (where $\Delta f / F_0 < 0.02$), the mass is assumed to be an extension of the crystal itself:
$$\Delta f = - \frac{2 f_0^2}{A \sqrt{\rho_q \mu_q}} \Delta m$$

### 2. Z-Match Model
For "thick" films (where $\Delta f / F_0 > 0.02$), the acoustic impedance mismatch is corrected using the material-specific **Z-Factor**:
$$d = \left( \frac{N_q \rho_q}{\pi \rho_f f_c Z} \right) \arctan \left( Z \tan \left[ \frac{\pi (f_q - f_c)}{f_q} \right] \right)$$

## Physical Constants
| Constant | Symbol | Value |
| :--- | :--- | :--- |
| Quartz Density | $\rho_q$ | $2.648\text{ g/cm}^3$ |
| Shear Modulus | $\mu_q$ | $2.947 \times 10^{11}\text{ g/cm}\cdot\text{s}^2$ |
| AT-cut Frequency Constant | $N_q$ | $1.668 \times 10^{13}\text{ Hz}\cdot\text{\AA}$ |