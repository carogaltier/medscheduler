# Customization options

**Medscheduler** provides a wide range of parameters to control how slots, patients, and appointments are generated.  
By adjusting these options, you can simulate different healthcare settings, attendance behaviors, and patient cohorts.

All customization happens when you create an `AppointmentScheduler` instance.  
Below is a categorized overview of the most important parameters and their defaults.

---

## 1. Calendar & capacity

- **`date_ranges`**: list of tuples defining start and end dates (e.g., `[("2023-01-01", "2023-12-31")]`).  
  - **Default:** if neither `date_ranges` nor `ref_date` are provided, a deterministic static window is used:  
    `2024-01-01 00:00` → `2024-12-31 23:59`.  
- **`ref_date`**: reference point for relative date generation.  
  - **Default:** `2024-12-01 00:00` when no arguments are passed. Otherwise, normalized to midnight.  
- **`working_days`**: list of weekdays to include (`0=Mon ... 6=Sun`).  
- **`appointments_per_hour`**: slot density; valid divisors of 60 (e.g., 4 → 15‑minute slots, 6 → 10‑minute slots).  
- **`working_hours`**: list of tuples with daily shifts in `(hour, hour)` format, e.g., `[(8, 12), (13, 17)]`.  
- **`month_weights`**: relative weights for monthly activity (default: NHS seasonality).  
- **`weekday_weights`**: relative weights for weekdays (default: NHS patterns, Mon–Fri > Sat–Sun).  

---

## 2. Booking dynamics

- **`fill_rate`**: proportion of slots filled (0.0–1.0).  
- **`booking_horizon`**: how many days ahead patients can book.  
- **`median_lead_time`**: median days between booking and appointment (controls scheduling interval).  
- **`rebook_category`**: controls rebooking behavior for cancellations/no‑shows (`"low"`, `"med"`, `"high"`).  

---

## 3. Attendance behavior

- **`status_rates`**: dictionary with outcome probabilities (attended, did not attend, cancelled, unknown).  
- **`visits_per_year`**: expected number of appointments per patient per year (controls re‑use of patients).  
- **`first_attendance`**: proportion of appointments that are first visits vs. follow‑ups (default from NHS data).  
- **`check_in_time_mean`**: average minutes before appointment that patients check in (negative = early).  

---

## 4. Patient cohort

- **`age_gender_probs`**: age–sex distribution (default NHS‑derived proportions).  
- **`bin_size`**: age group bin width (e.g., 5 years).  
- **`lower_cutoff` / `upper_cutoff`**: minimum and maximum ages.  
- **`truncated`**: whether to enforce age bounds strictly.  

---

## 5. Reproducibility

- **`seed`**: random seed for deterministic output.  
- **`noise`**: adds controlled variability to prevent identical datasets across runs.  

---

## Example: adjusting multiple options

```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(
    seed=123,
    date_ranges=[("2024-01-01", "2024-03-31")],
    working_days=[0,1,2,3,4],  # Mon–Fri
    appointments_per_hour=6,
    fill_rate=0.9,
    status_rates={"attended": 0.75, "did not attend": 0.1, "cancelled": 0.12, "unknown": 0.03},
    check_in_time_mean=-10,  # patients arrive ~10 minutes early
)
slots, appointments, patients = sched.generate()
```

---

## Recommendations

- Start with defaults for quick experiments.  
- Override only the parameters relevant to your use case.  
- Use a fixed `seed` when teaching, testing, or publishing results.  
- Explore combinations of booking dynamics and attendance outcomes to prototype scheduling strategies.

---

## Next steps

- Continue to the **Visualization** section to learn how to plot the generated datasets.  
- Visit **Examples** for applied scenarios such as attendance analysis and overbooking simulations.  
