# Seasonality and weights

The parameters **`month_weights`** and **`weekday_weights`** control the **relative distribution of appointments across time**.  
They do not define the calendar itself (see {doc}`calendar_structure`), but apply **probabilistic scaling factors**  
that bias slot utilization to reflect real-world seasonality patterns.

---

## `weekday_weights`

### Purpose
Adjusts appointment load across weekdays, reflecting the fact that some days are systematically busier than others.

### Defaults
- By default, `weekday_weights` is based on **Ellis & Jenkins (2012)** [1],  
  which analyzed over 4.5 million outpatient appointments in Scotland (2008–2010).  
- Weekends were not observed in the study (<2% of total appointments), so the simulator extrapolates values for Saturday and Sunday.

---

#### 1. Data source (Mon–Fri)

| Weekday   | Appointments (n) | Share of total (Mon–Fri) |
|-----------|------------------|--------------------------|
| Monday    | 967,912           | 21.69%                   |
| Tuesday   | 1,032,417         | 23.13%                   |
| Wednesday | 957,447           | 21.45%                   |
| Thursday  | 887,960           | 19.89%                   |
| Friday    | 617,633           | 13.84%                   |

---

#### 2. Extrapolating to weekends
- A **linear regression** is fit to the Mon–Fri shares.  
- Predictions for indices 5 (Saturday) and 6 (Sunday) are obtained.  
- Any negative values are clipped to 0.  
- This creates a plausible decreasing pattern consistent with NHS practice (very few weekend appointments).

---

#### 3. Normalization
The Mon–Fri shares and extrapolated Sat–Sun values are combined and normalized:

\[
p_i^{\text{norm}} = \frac{p_i}{\sum_{j=0}^6 p_j}
\]

so that the weekly proportions sum to 1.0.

---

#### 4. Conversion to relative weights
Relative weights are computed as:

\[
w_i = \frac{p_i^{\text{norm}}}{\overline{p^{\text{norm}}}}
\]

This ensures that the **average across all 7 days = 1.0**.

---

#### 5. Resulting default weights

| Day       | Code | Relative weight |
|-----------|------|-----------------|
| Monday    | 0    | 1.198 |
| Tuesday   | 1    | 1.277 |
| Wednesday | 2    | 1.185 |
| Thursday  | 3    | 1.099 |
| Friday    | 4    | 0.764 |
| Saturday  | 5    | 0.791 |
| Sunday    | 6    | 0.686 |

---

#### 6. Adaptation in the simulator
- If `working_days` excludes some days, weights are recalculated over the active subset.  
- The mean is re-normalized to 1.0.  
- Final booking probabilities are scaled so that the **global fill rate matches `fill_rate`**.  
- Probabilities are clipped to ≤ 1.0.

---

## `month_weights`

### Purpose
Adjusts appointment load across calendar months, reflecting annual seasonality in NHS activity.

### Defaults
- By default, `month_weights` is set to **NHS-derived proportions** for April 2023 – March 2024.  
- Values are stored in `constants.py` and have a mean of 1.0.

---

#### 1. Timeframe and data selection
- Source: NHS Digital, *Provisional Monthly Hospital Episode Statistics* [2].  
- Period: **Apr 2023 – Mar 2024**.  
- Column used: `Outpatient_Total_Appointments`.

---

#### 2. Monthly totals

| Month  | Total appointments |
|--------|--------------------|
| APR23  | 9,759,065          |
| MAY23  | 11,263,834         |
| JUN23  | 11,677,419         |
| JUL23  | 11,105,355         |
| AUG23  | 11,216,105         |
| SEP23  | 11,207,017         |
| OCT23  | 11,905,182         |
| NOV23  | 12,217,216         |
| DEC23  | 10,011,736         |
| JAN24  | 12,324,617         |
| FEB24  | 11,581,356         |
| MAR24  | 11,176,694         |

---

#### 3. Share of annual activity
\[
\text{Share}_m = \frac{\text{Appointments}_m}{\sum_{\text{Apr–Mar}} \text{Appointments}}
\]

---

#### 4. Conversion to relative weights
\[
w_m = \frac{\text{Share}_m}{\overline{\text{Share}_{\text{Apr–Mar}}}}
\]

- Values above 1.0 = busier months.  
- Values below 1.0 = quieter months.  

---

#### 5. Resulting default weights

| Month  | Share of total | Relative weight |
|--------|----------------|-----------------|
| APR23  | 7.21%          | 0.865 |
| MAY23  | 8.32%          | 0.998 |
| JUN23  | 8.62%          | 1.035 |
| JUL23  | 8.20%          | 0.984 |
| AUG23  | 8.28%          | 0.994 |
| SEP23  | 8.27%          | 0.993 |
| OCT23  | 8.79%          | 1.055 |
| NOV23  | 9.02%          | 1.082 |
| DEC23  | 7.39%          | 0.887 |
| JAN24  | 9.10%          | 1.092 |
| FEB24  | 8.55%          | 1.026 |
| MAR24  | 8.25%          | 0.990 |

---

#### 6. Adaptation in the simulator
- If only a subset of months is simulated, weights are recalculated over that subset.  
- Weights are multiplied by weekday weights to form a **combined seasonality effect**.  
- Final probabilities are clipped at ≤ 1.0.  
- Global average always scales back to match `fill_rate`.

---

## References

[1] Ellis, D. A., & Jenkins, R. (2012). *Weekday affects attendance rate for medical appointments: Large-scale data analysis and implications.*  
PLoS ONE, 7(12), e51365. [doi:10.1371/journal.pone.0051365](https://doi.org/10.1371/journal.pone.0051365)  

[2] NHS Digital. *Provisional Monthly Hospital Episode Statistics for Admitted Patient Care, Outpatient and Accident and Emergency Data*.  
[Link](https://digital.nhs.uk/data-and-information/publications/statistical/provisional-monthly-hospital-episode-statistics-for-admitted-patient-care-outpatient-and-accident-and-emergency-data/april-2025---may-2025)  

---

## See also

- {doc}`calendar_structure` – defines the baseline calendar (days, hours, density).  
- {doc}`customization_options` – overview of how weights interact with other parameters.  
- {doc}`../examples/index` – applied scenarios showing the impact of seasonality.  
