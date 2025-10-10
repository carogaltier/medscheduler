# AppointmentScheduler

**`class medscheduler.AppointmentScheduler`**

Generates a fully synthetic yet statistically realistic dataset of outpatient appointments — including calendar slots, patient demographics, and visit outcomes. Designed for educational, analytical, and research use without privacy risks.

---

## Purpose

The `AppointmentScheduler` simulates the entire outpatient appointment process:
- Builds configurable daily calendars of bookable slots.  
- Generates patient cohorts with realistic age–sex distributions.  
- Allocates appointments with probabilistic attendance, cancellation, and rebooking.  
- Simulates punctuality and in-clinic timing dynamics.  
- Outputs three relational tables: `appointments`, `slots`, and `patients`.

All parameters are configurable for reproducibility or scenario testing.

---

## Parameters

| Parameter | Type | Default | Description |
|------------|------|----------|-------------|
| `date_ranges` | list of (date, date) | `[(2024-01-01, 2024-12-31)]` | Simulation window for available slots. See {doc}`date_ranges_ref_date`. |
| `ref_date` | date | `2024-12-01` | Reference date separating past and future appointments. |
| `working_days` | list[int] | `[0,1,2,3,4]` | Active weekdays (0=Mon, …, 6=Sun). See {doc}`calendar_structure`. |
| `appointments_per_hour` | int | `4` | Defines slot granularity (15 min). Must divide 60 evenly. |
| `working_hours` | list[tuple[int,int]] | `[(8,18)]` | Start–end working blocks (e.g. 8 → 18 h). |
| `fill_rate` | float | `0.9` | Target proportion of booked slots. See {doc}`booking_dynamics`. |
| `booking_horizon` | int | `30` | Maximum days ahead that can be booked. |
| `median_lead_time` | int | `10` | Median days between scheduling and appointment. |
| `status_rates` | dict | NHS-derived | Probabilities for outcomes (attended / cancelled / DNA / unknown). See {doc}`attendance_behavior`. |
| `rebook_category` | {`'min'`, `'med'`, `'max'`} | `'med'` | Intensity of rebooking behavior. |
| `check_in_time_mean` | float | `-10` | Average early arrival (minutes). See {doc}`appointment_timing`. |
| `visits_per_year` | float | `1.2` | Mean visit frequency per patient per year. See {doc}`patient_flow`. |
| `first_attendance` | float | `0.325` | Ratio of first attendances among visits. |
| `month_weights` | dict[int,float] or list[float] | NHS-derived | Monthly scaling factors (Apr 2023–Mar 2024). See {doc}`seasonality_weights`. |
| `weekday_weights` | dict[int,float] or list[float] | NHS-derived | Weekday scaling factors (Mon–Sun). |
| `bin_size` | int | `5` | Age group width for cohort generation. See {doc}`patient_demographics`. |
| `lower_cutoff` | int | `15` | Minimum patient age. |
| `upper_cutoff` | int | `90` | Maximum patient age. |
| `truncated` | bool | `True` | Truncate ages outside cutoffs. |
| `seed` | int or None | `42` | Random seed for reproducibility. See {doc}`randomness_and_noise`. |
| `noise` | float | `0.1` | Global stochastic variability factor. |
| `age_gender_probs` | DataFrame or list[dict] | NHS-derived | Age–sex distribution reference. |

---

## Attributes

| Attribute | Type | Description |
|------------|------|-------------|
| `slots_df` | `pd.DataFrame` | Appointment slot capacity table. See {doc}`slots_table`. |
| `appointments_df` | `pd.DataFrame` | Central table with all appointment outcomes. See {doc}`appointments_table`. |
| `patients_df` | `pd.DataFrame` | Registry of simulated patients. See {doc}`patients_table`. |
| `rng` | `numpy.random.Generator` | Internal random generator instance. |
| `fake` | `Faker` | Faker instance used to generate synthetic names. |
| `patient_id_counter` | int | Running counter for unique patient IDs. |

---

## Methods

| Method | Description |
|---------|--------------|
| `generate()` | Runs the full pipeline: slots → appointments → patients. |
| `generate_slots()` | Builds the appointment calendar. See {doc}`slots_table`. |
| `generate_appointments()` | Simulates bookings, cancellations, rebookings. See {doc}`appointments_table`. |
| `assign_actual_times()` | Assigns realistic check-in/start/end times. See {doc}`appointment_timing`. |
| `generate_patients()` | Creates synthetic patients by age and sex. See {doc}`patients_table`. |
| `assign_patients()` | Links patients to appointments and computes per-visit age. |
| `add_custom_column()` | Adds new categorical variables to `patients_df`. See {doc}`custom_columns`. |
| `to_csv()` | Exports all three tables to CSV files. |
| `rebook_appointments()` | Iterative rescheduling of cancelled visits. |
| `assign_status()` | Finalizes appointment outcomes. |
| `schedule_future_appointments()` | Simulates upcoming bookings within the horizon. |

---

## Usage example

```python
from medscheduler import AppointmentScheduler

# Initialize and run full simulation
sched = AppointmentScheduler(seed=42, fill_rate=0.9, booking_horizon=30)
slots, appointments, patients = sched.generate()

print(appointments.head())
```

---

## Notes
- All date-like inputs are parsed to naive `datetime` (timezone removed).  
- The default configuration reflects NHS 2023–24 outpatient statistics.  
- Outputs are fully deterministic when `seed` is fixed.  
- Recommended workflow: instantiate → `generate()` → access `.appointments_df`.  

---

### Next steps
- Learn how temporal boundaries are defined in {doc}`date_ranges_ref_date`.  
- Review {doc}`calendar_structure` to understand how working days, hours, and slot density are configured.  
- For dataset customization, see also {doc}`booking_dynamics` and {doc}`seasonality_weights`.


