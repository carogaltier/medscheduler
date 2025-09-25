# medscheduler

**medscheduler** is a lightweight Python library for generating **fully synthetic**, **statistically plausible** outpatient appointment data. It simulates daily clinic calendars, patient cohorts, and appointment outcomes with healthcare‑aware defaults and strict validation.

Typical uses:

- Teaching and training in healthcare data science
- Prototyping dashboards, capacity planning, and scheduling models
- Reproducible experiments and benchmarks without PHI/PII risks

---

## Features

- Configurable clinic calendars (date ranges, working days/hours, capacity per hour)
- Patient cohort with realistic age–sex distributions
- Probabilistic scheduling: fill rate, first attendances, rebooking behavior
- Attendance outcomes with sensible defaults (attended, DNA, cancelled, unknown)
- Punctuality and check‑in time simulation
- Clear validation and informative error messages
- Minimal dependencies; optional plotting helpers

---

## Installation

From PyPI:

```bash
pip install medscheduler
```

Optional plots (Matplotlib):

```bash
pip install "medscheduler[viz]"
```

Requires Python 3.9 or newer.

---

## Quickstart

```python
from medscheduler import AppointmentScheduler

# Instantiate with defaults (seed for reproducibility)
sched = AppointmentScheduler(seed=42)

# Generate the three core tables
slots_df, appts_df, patients_df = sched.generate()

# Optionally export to CSV
sched.to_csv(
    slots_path="slots.csv",
    patients_path="patients.csv",
    appointments_path="appointments.csv",
)
```

---

## Core concepts (overview)

- **Calendar & capacity:** `date_ranges`, `working_days`, `working_hours`, `appointments_per_hour`
- **Demand & booking:** `fill_rate`, `booking_horizon`, `median_lead_time`, `rebook_category`
- **Outcomes:** `status_rates` (attended / did not attend / cancelled / unknown)
- **Demographics:** `age_gender_probs`, `bin_size`, `lower_cutoff`, `upper_cutoff`, `truncated`
- **First attendances:** `first_attendance` (ratio)
- **Punctuality:** `check_in_time_mean` and related timing fields
- **Reproducibility:** `seed` controls the RNG

All defaults are overrideable at instantiation time.

---

## Outputs

`generate()` returns three pandas DataFrames:

- **slots** — canonical calendar of available appointment slots  
  Columns include: `slot_id`, `appointment_date`, `appointment_time`, `is_available`, …
- **appointments** — scheduled visits with status and timing fields  
  Columns include: `appointment_id`, `slot_id`, `status`, `scheduling_date`, `check_in_time`, `start_time`, `end_time`, …
- **patients** — synthetic cohort linked to appointments  
  Columns include: `patient_id`, `sex`, `age` (or `dob` and `age_group`), plus any custom columns you add

---

## 📊 Plotting Examples (optional)

If you installed the visualization extra (`pip install "medscheduler[viz]"`), you can generate quick diagnostic plots.  
All functions return a Matplotlib `Axes` object. In Jupyter/Colab, plots are displayed automatically; in scripts, call `plt.show()`.

```python
import matplotlib.pyplot as plt
from medscheduler import AppointmentScheduler
from medscheduler.utils.plotting import (
    plot_past_slot_availability,
    plot_future_slot_availability,
    plot_monthly_appointment_distribution,
    plot_weekday_appointment_distribution,
    plot_population_pyramid,
    plot_appointments_by_status,
    plot_appointments_by_status_future,
    plot_status_distribution_last_days,
    plot_status_distribution_next_days,
    plot_scheduling_interval_distribution,
    plot_appointment_duration_distribution,
    plot_waiting_time_distribution,
    plot_arrival_time_distribution
)

# Generate synthetic data
sched = AppointmentScheduler(seed=42)
slots_df, appts_df, patients_df = sched.generate()

# Weekday distribution of appointments
ax = plot_weekday_appointment_distribution(appts_df)
plt.show()

# Monthly distribution of appointments
ax = plot_monthly_appointment_distribution(appts_df)
plt.show()

# Age–sex pyramid for patients
ax = plot_population_pyramid(appts_df)
plt.show()
```

## Documentation & examples

A tutorial series of Jupyter notebooks (Quickstart, Core Calendar, Fill Rate & Rebooking, Status Rates, Check‑in Time, Age/Gender, Seasonality, Scenarios, Validation) will be published as project documentation.  
For now, see the Quickstart above and the docstrings of `AppointmentScheduler` and utilities.

---

## Testing (for contributors)

```bash
pip install -e .[dev]
pytest -q
```

---

## License

MIT License. See `LICENSE` for details.

---

## Citation

If this library is helpful in your work, please cite:

> Carolina González Galtier. *medscheduler: A synthetic outpatient appointment simulator*, 2025.  
> GitHub: https://github.com/carogaltier/medscheduler
