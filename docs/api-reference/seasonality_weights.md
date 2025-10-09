# Seasonality and weights

The parameters **`month_weights`** and **`weekday_weights`** control the **relative distribution of appointments across time**.  
They do not define the calendar itself (see {doc}`calendar_structure`), but apply **probabilistic scaling factors** that bias slot utilization to reflect real-world seasonality patterns.

---

## `weekday_weights`

`weekday_weights` adjusts the appointment load across weekdays, reflecting that some days are systematically busier than others.

### Format

**Type:** dict `{weekday:int → weight:float}` or list/tuple of 7 floats  
**Default:** `{0:1.198, 1:1.277, 2:1.185, 3:1.099, 4:0.764, 5:0.791, 6:0.686}`. Those values are based on **Ellis & Jenkins (2012)** [1] and stored in `constants.py`.  
**Accepted values:**  
Both forms are supported:  
- **Dict form:** `{weekday:int → weight:float}` where keys range from `0` (Monday) to `6` (Sunday), and all values are non-negative.  
- **List/Tuple form:** a sequence of **7 numeric values**, interpreted in order from Monday (`0`) to Sunday (`6`).  
**Input formats:** dict `{int: float}` or list `[float, …, float]`. Values are normalized internally to have a mean of 1.0.

### Validation rules

- Must provide 7 values corresponding to weekdays 0–6.  
- Values must be non-negative (`0.0` disables that day from booking activity).  
- If some weekdays are missing, they are automatically filled with `1.0` before normalization.  
- All weights are rescaled to have mean = 1.0.  
- If some weekdays are excluded by `working_days`, weights are re-normalized over the active subset.

### How it works

By default, the model uses weekday proportions derived from Ellis & Jenkins (2012) which analyzed over 4.5 million outpatient appointments in Scotland [1].  
The study observed that outpatient volumes peak early in the week and decline toward Friday, with minimal weekend activity.  
Because weekend appointments represented <2% of total activity, the simulator extrapolates plausible Saturday–Sunday values using a simple linear model fitted on Mon–Fri data.

#### Default reference data (Mon–Fri)

| Weekday   | Appointments (n) | Share of total (Mon–Fri) |
|------------|------------------|---------------------------|
| Monday     | 967,912          | 21.69%                   |
| Tuesday    | 1,032,417        | 23.13%                   |
| Wednesday  | 957,447          | 21.45%                   |
| Thursday   | 887,960          | 19.89%                   |
| Friday     | 617,633          | 13.84%                   |

The resulting normalized relative weights are:

| Day       | Code | Relative weight |
|------------|------|-----------------|
| Monday     | 0    | 1.198 |
| Tuesday    | 1    | 1.277 |
| Wednesday  | 2    | 1.185 |
| Thursday   | 3    | 1.099 |
| Friday     | 4    | 0.764 |
| Saturday   | 5    | 0.791 |
| Sunday     | 6    | 0.686 |

Internally, weekday weights are combined with `month_weights` to create a joint scaling factor applied to slot booking probabilities.  
If `working_days` excludes certain days, weights are recomputed to maintain mean = 1.0.  
All final probabilities are clipped to ≤ 1.0 to prevent overbooking effects.

### Examples

**Custom weekday bias**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(
    weekday_weights={0:1.1, 1:1.2, 2:1.0, 3:1.0, 4:0.7, 5:0.8, 6:0.6}
)
```

**Uniform weekdays (no variation)**
```python
sched = AppointmentScheduler(weekday_weights=[1.0]*7)
```

---

## `month_weights`

`month_weights` adjusts appointment load across months, capturing seasonal variation in healthcare activity.

### Format

**Type:** dict `{month:int → weight:float}` or list/tuple of 12 floats  
**Default:** NHS-derived proportions for April 2023 – March 2024, stored in `constants.py`.  
**Accepted values:**  
- **Dict form:** keys `1–12` (Jan–Dec), values ≥ 0  
- **List/Tuple form:** exactly 12 numeric values interpreted as January→December  
**Input formats:** dict `{int: float}` or list `[float, …, float]`. Values are automatically scaled so that mean = 1.0.

### Validation rules

- Must contain 12 non-negative values.  
- Values must be non-negative (`0.0` disables that month).  
- Missing months default to `1.0`, and all values are renormalized to maintain mean = 1.0.  
- If simulation covers a subset of months, weights are recalculated over that subset.

### How it works

Default weights are derived from NHS Digital *Provisional Monthly Hospital Episode Statistics* (Apr 2023 – Mar 2024).  
They reflect natural seasonality in outpatient activity, with peaks in late autumn–winter and lower activity around summer holidays.  
These month weights are stored in `constants.py` and have mean = 1.0.  

| Month  | Share of total | Relative weight |
|---------|----------------|-----------------|
| APR23  | 7.21% | 0.865 |
| MAY23  | 8.32% | 0.998 |
| JUN23  | 8.62% | 1.035 |
| JUL23  | 8.20% | 0.984 |
| AUG23  | 8.28% | 0.994 |
| SEP23  | 8.27% | 0.993 |
| OCT23  | 8.79% | 1.055 |
| NOV23  | 9.02% | 1.082 |
| DEC23  | 7.39% | 0.887 |
| JAN24  | 9.10% | 1.092 |
| FEB24  | 8.55% | 1.026 |
| MAR24  | 8.25% | 0.990 |

Within the simulator, month and weekday effects are multiplied to form a **combined seasonal bias**.  
This combined weight modifies the probability that a slot is filled during the booking process.  
When only a subset of months is simulated, weights are re-normalized to maintain mean = 1.0.

### Examples

**Custom winter peak adjustment**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(
    month_weights={1:1.2, 2:1.1, 12:1.3}  # emphasize winter demand
)
# Missing months not specified default to 1.0
```

**Flatten seasonality (uniform months)**
```python
sched = AppointmentScheduler(month_weights=[1.0]*12)
```

---

### References

[1] Ellis, D. A., & Jenkins, R. (2012). *Weekday affects attendance rate for medical appointments: Large-scale data analysis and implications.*  
PLoS ONE, 7(12), e51365. [https://doi.org/10.1371/journal.pone.0051365](https://doi.org/10.1371/journal.pone.0051365)  

[2] NHS Digital. *Provisional Monthly Hospital Episode Statistics for Admitted Patient Care, Outpatient and Accident and Emergency Data.*  
[https://digital.nhs.uk/data-and-information/publications/statistical/provisional-monthly-hospital-episode-statistics-for-admitted-patient-care-outpatient-and-accident-and-emergency-data/april-2025---may-2025](https://digital.nhs.uk/data-and-information/publications/statistical/provisional-monthly-hospital-episode-statistics-for-admitted-patient-care-outpatient-and-accident-and-emergency-data/april-2025---may-2025)

---

### Next steps

- {doc}`date_ranges_ref_date` – explains reference dates and effective calendar windows.
- {doc}`calendar_structure` – defines the baseline calendar (days, hours, density).  
- {doc}`booking_dynamics` – explore how fill rate and booking horizon determine slot utilization.

