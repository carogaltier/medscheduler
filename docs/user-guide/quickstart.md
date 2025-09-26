# Quickstart

This guide walks you through generating a synthetic outpatient dataset with **medscheduler** and exploring its outputs.  
In just a few lines of code you can simulate appointment slots, patients, and scheduled visits.

---

## 1) Import and instantiate

```python
from medscheduler import AppointmentScheduler

# Reproducible baseline (NHS‑derived defaults are overrideable)
sched = AppointmentScheduler(seed=42)
```

### Optional: customize the scheduler

When creating an `AppointmentScheduler`, you can override many defaults.  
For example, you might change the **calendar parameters** (working days, hours, or slot density):

```python
sched = AppointmentScheduler(
    seed=42,
    working_days=[0, 1, 2, 3, 4],               # Mon–Fri
    appointments_per_hour=4,                    # valid divisors of 60
    working_hours=[("08:00", "12:00"), ("13:00", "17:00")],
)
```

---

## 2) Generate the dataset

```python
slots_df, appointments_df, patients_df = sched.generate()
len(slots_df), len(appointments_df), len(patients_df)
```

The `.generate()` method runs the end‑to‑end pipeline:

1. Build the **slot calendar**  
2. Allocate **appointments** (including cancellations and rebooking)  
3. Simulate **patients** and assign them to visits  

The result is three pandas DataFrames that replicate a real scheduling system.

---

## 3) Explore the outputs

### Appointments (main table)

```python
appointments_df.head()
```

Contains patient demographics, scheduling dates, visit timing, and attendance outcomes.  
Key columns include:  
- Identifiers: `appointment_id`, `slot_id`, `patient_id`  
- Scheduling: `scheduling_date`, `scheduling_interval`  
- Visit: `appointment_date`, `appointment_time`, `status`  
- Patient: `sex`, `age`, `age_group`  
- Timing (for attended visits): `check_in_time`, `start_time`, `end_time`, `waiting_time`, `appointment_duration`  

### Slots (capacity ledger)

```python
slots_df.head()
```

Represents daily appointment capacity.  
Columns: `slot_id`, `appointment_date`, `appointment_time`, `is_available`.

### Patients (registry)

```python
patients_df.head()
```

Synthetic patient registry.  
Columns: `patient_id`, `name` (Faker), `sex`, `dob`.

---

## 4) Export to CSV

You can save the generated tables for later use or sharing:

```python
sched.to_csv(
    slots_path="slots.csv",
    patients_path="patients.csv",
    appointments_path="appointments.csv",
)
```

This produces three standalone CSV files ready for BI tools, teaching, or demo purposes.

---

## 5) Reproducibility tips

- Always set a fixed `seed` for deterministic results across runs.  
- Store exported CSVs in your repo or data releases to ensure others can reproduce your analyses.  

---

## Next steps

- Explore {doc}`Outputs overview` for detailed descriptions of each table.  
- Check {doc}`Customization options` to adjust attendance rates, rebooking, and punctuality.  
- Visit {doc}`Visualization` to see how to plot distributions and capacity.  
- Browse {doc}`../examples/index` for applied scenarios such as attendance analysis and overbooking.  
