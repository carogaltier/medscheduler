# Quickstart

This short guide shows how to generate a synthetic outpatient dataset with **medscheduler** and preview the three output tables.

## 1) Import and instantiate

```python
from medscheduler import AppointmentScheduler

# Reproducible baseline (NHS‑derived defaults are overrideable)
sched = AppointmentScheduler(seed=42)
```

### Optional: customize the calendar
You can override working days/hours and slot density at construction time:

```python
sched = AppointmentScheduler(
    seed=42,
    working_days=[0,1,2,3,4],             # Mon–Fri
    appointments_per_hour=4,              # 4, 5, 6, 10, 12… (must divide 60)
    working_hours=[("08:00","12:00"), ("13:00","17:00")],
)
```

## 2) Generate the data

```python
slots_df, appointments_df, patients_df = sched.generate()
len(slots_df), len(appointments_df), len(patients_df)
```

`generate()` runs the end‑to‑end pipeline:
1. Build the **slot calendar**
2. Allocate **appointments** (historical + future; cancellations & rebooking)
3. Simulate **patients** and assign them to visits

## 3) Explore the outputs

### Appointments (main table)

```python
appointments_df.head()
```

Includes:
- IDs: `appointment_id`, `slot_id`, `patient_id`
- Scheduling: `scheduling_date`, `scheduling_interval`
- Visit: `appointment_date`, `appointment_time`, `status`
- Patient: `sex`, `age`, `age_group`
- Timing (attended): `check_in_time`, `start_time`, `end_time`, `waiting_time`, `appointment_duration`

### Slots (capacity ledger)

```python
slots_df.head()
```

Columns: `slot_id`, `appointment_date`, `appointment_time`, `is_available`.

### Patients (registry)

```python
patients_df.head()
```

Columns: `patient_id`, `name` (Faker), `sex`, `age` (or `dob` + `age_group` if configured).

## 4) Export to CSV (optional)

```python
sched.to_csv(
    slots_path="slots.csv",
    patients_path="patients.csv",
    appointments_path="appointments.csv",
)
```
This produces three files you can import into BI tools or share for teaching/demo purposes.

## 5) Reproducibility tips

- Set a fixed `seed` to keep results deterministic across runs.
- Keep your library version pinned in `requirements.txt` for tutorials/papers.
- Save generated CSVs in your repo (or a release asset) to ensure readers can reproduce your figures.

## Next steps

- Explore **calendar configuration** (working days/hours, `appointments_per_hour`).
- Tune **status rates**, **rebooking**, and **punctuality** parameters.
- Use plotting helpers to visualize distributions and capacity (optional `matplotlib`).
