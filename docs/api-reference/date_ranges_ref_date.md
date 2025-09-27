# Date ranges and reference date

The parameters **`date_ranges`** and **`ref_date`** control the calendar window and the reference point
for generating synthetic outpatient schedules. Together, they determine how far back and forward
appointments are simulated, and how the booking horizon is applied.

---

## Overview

- **`date_ranges`** defines the calendar span(s) during which appointment slots exist.  
- **`ref_date`** sets the simulation "today", acting as the pivot between past and future appointments.  
- Both parameters are validated and normalized to ensure realistic and reproducible outputs.

---

## `date_ranges`

### Accepted input types

`date_ranges` must be a **list of tuples**, where each tuple contains a **start date** and an **end date**.

Valid input types for each element:  
- `str` in ISO format `"YYYY-MM-DD"`  
- `datetime.date`  
- `datetime.datetime`  
- `pandas.Timestamp`  
- `numpy.datetime64`  

Internally, all values are converted to naive `datetime` (timezone info removed).

```python
date_ranges = [
    ("2024-01-01", "2024-06-30"),
    ("2024-09-01", "2024-12-31"),
]
```

### Defaults and behavior

- If both `date_ranges` and `ref_date` are omitted:  
  - A **fixed reproducible window** is used → `[2024-01-01 00:00, 2024-12-31 23:59]`.  
  - `ref_date` defaults to **2024-12-01 00:00**.  

- If `date_ranges` is omitted but `ref_date` is supplied:  
  - The same deterministic 2024 window is used.  
  - `ref_date` is set as provided.  

- If `date_ranges` is provided but `ref_date` is omitted:  
  - `ref_date` defaults to the **last day of the latest range at 00:00**.  

- If `ref_date` is provided:  
  - It must fall within at least one range, otherwise a `ValueError` is raised.

### Validation rules

- Each `(start, end)` must satisfy `start < end`.  
- If `end` is at midnight (00:00), it is expanded to `23:59` of the same day.  
- Same-day ranges like `("2024-01-15", "2024-01-15")` normalize to `[2024-01-15 00:00, 2024-01-15 23:59]`.  
- Non-contiguous ranges are allowed.  

### Effective ranges

If `ref_date + booking_horizon` extends beyond the last range, the library **extends the final range** accordingly.  
Existing ranges are never shortened.

---

## `ref_date`

### Purpose

The **reference date** acts as the simulation "present". It divides historical appointments from future ones and anchors relative scheduling.

### Defaults

- If `date_ranges` and `ref_date` are both `None`:  
  - `ref_date = 2024-12-01 00:00`.  
  - `date_ranges = [2024-01-01 00:00, 2024-12-31 23:59]`.  

- If only `ref_date` is `None`:  
  - Derived as the last day of the last provided range, normalized to midnight.  

- If provided explicitly:  
  - Normalized to midnight.  
  - Must fall within one of the given ranges.  

### Impact

- Determines how appointments are distributed between past and future.  
- Interacts with `booking_horizon` to guarantee sufficient forward capacity.  
- Ensures reproducibility: the static default (`2024-12-01`) anchors datasets for demos and tests.

---

## Examples

### Default (no arguments)

```python
from medscheduler import AppointmentScheduler

# Uses fixed 2024 window and reference date
sched = AppointmentScheduler()
print(sched.date_ranges)
print(sched.ref_date)
```

### Custom academic year

```python
sched = AppointmentScheduler(
    date_ranges=[("2024-09-01", "2025-06-30")]
)
```

### Multiple disjoint ranges

```python
sched = AppointmentScheduler(
    date_ranges=[
        ("2024-01-01", "2024-03-31"),
        ("2024-09-01", "2024-12-31"),
    ]
)
```

### Custom reference date

```python
sched = AppointmentScheduler(
    date_ranges=[("2024-01-01", "2024-12-31")],
    ref_date="2024-06-01"
)
```

---

## See also

- {doc}`booking_horizon` – ensures sufficient forward scheduling capacity beyond `ref_date`.  
- {doc}`status_rates` – controls attendance, cancellation, and no‑show probabilities.  
