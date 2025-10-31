# Medscheduler
Synthetic Outpatient Appointment Data Generator

![From Simulation to Insight](docs/_static/From%20Simulation%20to%20Insight.png)


`medscheduler` creates realistic, privacy-safe outpatient datasets — including appointment calendars, patient demographics, and visit outcomes — suitable for education, analytics, and research in healthcare operations.

---

## Features

- **End-to-end simulation**
  - Generates `slots`, `patients`, and `appointments` tables.
  - Reproduces booking, cancellation, and rebooking dynamics.
  - Simulates punctuality and in-clinic timing (arrival, start, end, waiting time, duration).
- **Realistic defaults**
  - Parameters reflect NHS England outpatient activity (2023–24) and peer-reviewed literature.
- **Configurable**
  - Calendar structure (days, hours, slot density), fill rate, booking horizon, lead time, attendance outcomes, rebooking intensity, demographics, and randomness.
- **Reproducible**
  - Controlled via `seed` and `noise`.
- **Lightweight**
  - Minimal scientific-Python dependencies; plotting utilities are optional.

---

## Installation

```bash
pip install medscheduler
```

Requires Python 3.9 or newer.

---

## Quickstart

```python
from medscheduler import AppointmentScheduler

# Initialize the scheduler
sched = AppointmentScheduler(
    seed=42,
    date_ranges=[("2024-01-01", "2024-12-31")],
    working_days=[0, 1, 2, 3, 4],  # Monday–Friday
    appointments_per_hour=4,       # 15-minute slots
    fill_rate=0.9
)

# Run the full pipeline
slots_df, appointments_df, patients_df = sched.generate()

# Export CSV files
sched.to_csv(
    slots_path="slots.csv",
    appointments_path="appointments.csv",
    patients_path="patients.csv",
)
```

Outputs:

| Table | Description |
|------|-------------|
| `slots.csv` | Calendar capacity (one row per slot). |
| `patients.csv` | Synthetic patient registry (demographics). |
| `appointments.csv` | Central table combining patient, slot, timing, and outcome data. |

---

## Core Concepts

### Calendar and Capacity
- `date_ranges` and `ref_date` delimit the simulation window and separate past from future.
- `working_days`, `working_hours`, and `appointments_per_hour` define slot structure and density.

### Booking Dynamics
- `fill_rate` controls overall utilization.
- `booking_horizon` and `median_lead_time` shape how far ahead and how early patients book.
- `rebook_category` (`min`, `med`, `max`) defines the probability of rebooking cancellations.

### Attendance and Flow
- `status_rates` determines attended / cancelled / did not attend / unknown proportions.
- `visits_per_year` and `first_attendance` regulate repeat visits and the share of new patients.

### Demographics
- `age_gender_probs`, `bin_size`, `lower_cutoff`, `upper_cutoff`, `truncated` control the cohort, derived from NHS distributions by default.

### Timing
- `check_in_time_mean` controls early/late arrivals.
- Durations follow a Beta(1.48, 3.6) model (mean ≈ 17 minutes).

### Randomness
- `seed` ensures reproducibility; `noise` introduces controlled variability.

---

## API Surface (selected)

- `AppointmentScheduler.generate()` — full pipeline: slots → appointments → patients  
- `AppointmentScheduler.generate_slots()`  
- `AppointmentScheduler.generate_appointments()`  
- `AppointmentScheduler.assign_actual_times()`  
- `AppointmentScheduler.generate_patients()`  
- `AppointmentScheduler.assign_patients()`  
- `AppointmentScheduler.add_custom_column()`  
- `AppointmentScheduler.to_csv()`  

See the full API in the documentation.

---

## Plotting Utilities

Module: `medscheduler.utils.plotting`

- `summarize_slots(df, scheduler, ...)` — summary metrics for calendar and availability.  
- `plot_population_pyramid(df, ...)` — age–sex pyramid.  
- `plot_past_slot_availability(slots_df, ...)` — availability before `ref_date` (Y/Q/M/W auto-aggregation).  
- `plot_future_slot_availability(slots_df, ...)` — availability on/after `ref_date` (D/W/M).  
- `plot_monthly_appointment_distribution(df)` — appointments by month (%).  
- `plot_weekday_appointment_distribution(df)` — appointments by weekday (%).  
- `plot_status_distribution_last_days(df, scheduler, days_back=30, ...)` — daily status counts last N days.  
- `plot_status_distribution_next_days(df, scheduler, days_ahead=30, ...)` — daily status counts next N days.  
- `plot_appointments_by_status(df, scheduler, ...)` — past appointments by status (%).  
- `plot_appointments_by_status_future(df, scheduler, ...)` — future appointments by status (%).  
- `plot_scheduling_interval_distribution(df, interval_col="scheduling_interval", ...)` — lead-time distribution.  
- `plot_appointment_duration_distribution(df, ...)` — consultation duration distribution (attended only).  
- `plot_waiting_time_distribution(df, ...)` — waiting time distribution (attended only).  
- `plot_arrival_time_distribution(df, ...)` — arrival offset distribution vs scheduled time.  
- `plot_first_attendance_distribution(df, scheduler, ...)` — first vs. returning attendance ratio.  
- `plot_custom_column_distribution(df, column_name, ...)` — categorical distribution for user-added columns.  
- `plot_patients_visits(df, scheduler, ...)` — distribution of patient visit frequency.  

All functions return a `matplotlib.axes.Axes` and follow a consistent, publication-grade styling.

---

## Visualization Gallery

Below are examples of the default visualization set produced by `medscheduler.utils.plotting`.

<p align="center">
  <img src="docs/_static/visuals/visualization/plot_appointments_by_status.png"><br>
</p>

<p align="center">
  <img src="docs/_static/visuals/visualization/plot_arrival_time_distribution.png"><br>
</p>

<p align="center">
  <img src="docs/_static/visuals/visualization/plot_past_slot_availability.png"><br>
</p>

<p align="center">
  <img src="docs/_static/visuals/visualization/plot_population_pyramid.png" width="600"><br>
</p>

See the complete gallery at [https://medscheduler.readthedocs.io/en/latest/visualization](https://medscheduler.readthedocs.io/en/latest/visualization).

---

## Repository Structure

```
medscheduler/
├─ src/medscheduler/
│  ├─ __init__.py
│  ├─ constants.py
│  ├─ scheduler.py
│  └─ utils/
│     ├─ plotting.py
│     └─ reference_data_utils.py
├─ tests/
│  └─ test_scheduler.py
├─ docs/
│  ├─ _static/logo.png
│  └─ _static/visuals/...
├─ README.md
├─ LICENSE
└─ pyproject.toml
```

---

## Testing

```bash
pytest -q
```

The test suite covers constructor validation and generation logic. Target coverage ≥ 80%.

---

## Documentation

Comprehensive documentation (User Guide, API Reference, Examples, and Visualization gallery) is available at:

- https://medscheduler.readthedocs.io

---

## References

- Buttz, L. (2004). How to use scheduling data to improve efficiency. Family Practice Management, 11(7), 27–29. PMID: 15315285.  
- Cerruti, B., Garavaldi, D., & Lerario, A. (2023). Patient's punctuality in an outpatient clinic: the role of age, medical branch and geographical factors. BMC Health Services Research, 23(1), 1385. https://doi.org/10.1186/s12913-023-10379-w  
- Ellis, D. A., & Jenkins, R. (2012). Weekday affects attendance rate for medical appointments: Large-scale data analysis and implications. PLoS ONE, 7(12), e51365. https://doi.org/10.1371/journal.pone.0051365  
- Grande, D., Zuo, J. X., Venkat, R., Chen, X., Ward, K. R., Seymour, J. W., & Mitra, N. (2018). Differences in Primary Care Appointment Availability and Wait Times by Neighborhood Characteristics: a Mystery Shopper Study. Journal of General Internal Medicine, 33(9), 1441–1443. https://doi.org/10.1007/s11606-018-4407-9  
- NHS Digital. Provisional Monthly Hospital Episode Statistics for Admitted Patient Care, Outpatient and Accident and Emergency Data. https://digital.nhs.uk/data-and-information/publications/statistical/provisional-monthly-hospital-episode-statistics-for-admitted-patient-care-outpatient-and-accident-and-emergency-data/april-2025---may-2025  
- NHS England (2024). Hospital Outpatient Activity 2023–24: Summary Reports 1–3. https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx  
- Rao, A., Shi, Z., Ray, K. N., Mehrotra, A., & Ganguli, I. (2019). National Trends in Primary Care Visit Use and Practice Capabilities, 2008–2015. Annals of Family Medicine, 17(6), 538–544. https://doi.org/10.1370/afm.2474  
- Tai-Seale, M., McGuire, T. G., & Zhang, W. (2007). Time allocation in primary care office visits. Health Services Research, 42(5), 1871–1894. https://doi.org/10.1111/j.1475-6773.2006.00689.x  
- Faker library documentation. https://faker.readthedocs.io/

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Citation

If this library is helpful in your work, please cite:

> Carolina González Galtier. *medscheduler: A synthetic outpatient appointment simulator*, 2025.  
> GitHub: https://github.com/carogaltier/medscheduler
