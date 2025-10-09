# Date ranges and reference date

The parameters **`date_ranges`** and **`ref_date`** jointly define the simulation calendar. They determine how far back and forward appointments are generated, set the effective window of operation, and anchor all time-dependent behaviors such as booking and attendance patterns. Together they establish the temporal logic that governs every component of the scheduler.

---

## `date_ranges`

`date_ranges` defines the calendar span(s) during which appointment slots exist. Each tuple represents a continuous block of valid dates. Multiple non-contiguous ranges can be used to simulate seasonal or intermittent activity periods, such as academic terms or clinics that close during holidays.

### Format and rules

**Type:** list of tuples `(start, end)`  
**Default:** `[('2024-01-01 00:00', '2024-12-31 23:59')]`  
If both `date_ranges` and `ref_date` are omitted, the scheduler applies this fixed deterministic 2024 window. If `ref_date` is supplied but `date_ranges` omitted, the same window is used while respecting the given `ref_date`.  
If `date_ranges` is provided but `ref_date` omitted, the reference date defaults to the last day of the latest range at `00:00`.

**Accepted values:** one or more non-overlapping intervals covering any valid chronological range. Each must satisfy `start < end`.

**Input formats:** each element of the tuple may be provided as:  
- `str` in ISO format `YYYY-MM-DD`  
- `datetime.date`  
- `datetime.datetime`  
- `pandas.Timestamp`  
- `numpy.datetime64`  

All inputs are internally converted to naive `datetime` (timezone information removed).

### Validation rules

- Each `(start, end)` must satisfy `start < end`.  
- If `end` occurs at midnight (`00:00`), it is expanded to `23:59` of the same day.  
- Same-day ranges like `(2024-01-15, 2024-01-15)` normalize to `[2024-01-15 00:00, 2024-01-15 23:59]`.  
- Non-contiguous ranges are allowed.  
- Invalid or reversed intervals raise a `ValueError`.  

### How it works

The `date_ranges` parameter defines the total temporal capacity for appointment generation. It determines how many slots can exist, which days are available for booking, and how far the simulation extends backward or forward in time.

During initialization, ranges are normalized and ordered. If the calculated window `ref_date + booking_horizon` extends beyond the latest defined range, the library automatically extends that range to ensure future appointments can still be scheduled. This guarantees continuity without ever shortening existing intervals.

This design enables realistic modeling of clinics with breaks or academic cycles, and provides deterministic behavior when using the default 2024 baseline. Longer or segmented ranges increase total slot capacity and allow simulations with more complex seasonal dynamics.

### Examples

**Default deterministic window (2024)**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler()
print(sched.date_ranges)
```

**Custom academic year**
```python
sched = AppointmentScheduler(
    date_ranges=[("2024-09-01", "2025-06-30")]
)
```

**Multiple operational blocks**
```python
sched = AppointmentScheduler(
    date_ranges=[
        ("2024-01-01", "2024-03-31"),
        ("2024-09-01", "2024-12-31"),
    ]
)
```

---

## `ref_date`

The `ref_date` parameter defines the simulation’s reference point—the “today” from which past and future appointments are interpreted. It divides the dataset into historical and future segments, serving as the anchor for booking horizons, appointment allocation, and attendance outcomes.

### Format and rules

**Type:** single date-like value  
**Default:** `2024-12-01 00:00` (used when both `date_ranges` and `ref_date` parameters are omitted).
If omitted and `date_ranges` provided, `ref_date` defaults to the last date of the final range (00:00). 
**Accepted values:** any valid date-like value that falls within at least one of the `date_ranges` intervals.  
**Input formats:** same as for `date_ranges` (string, date, datetime, Timestamp, or datetime64). All normalized to naive `datetime` at midnight.



### Validation rules

- The reference date must be inside at least one defined range.  
- A `ValueError` is raised if it falls before the first or after the last range.  
- Automatically normalized to `00:00` to avoid timezone drift.  

### How it works

`ref_date` acts as the simulation’s temporal pivot. Appointments before this date are considered historical, while those after it represent future bookings. It interacts with several other parameters to determine scheduling behavior:

- **`booking_horizon`** ensures a sufficient forward window for future appointments beyond the reference date.
- **`fill_rate`** and **`status_rates`** depend on this division to calculate the mix of attended, cancelled, and no-show visits.
- **`median_lead_time`** uses the reference point to compute scheduling intervals between booking and appointment dates.

Changing `ref_date` effectively shifts the simulated “present”. A later `ref_date` yields more past activity and fewer future bookings; an earlier one increases the ratio of pending appointments. The deterministic default (`2024-12-01`) ensures reproducibility in demonstrations and tests.

### Examples

**Default behavior (deterministic 2024 reference)**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler()
print(sched.ref_date)
```

**Custom reference date inside range**
```python
sched = AppointmentScheduler(
    date_ranges=[("2024-01-01", "2024-12-31")],
    ref_date="2024-06-01"
)
```

---

### Next steps

- {doc}`calendar_structure`: complete.  
- {doc}`booking_dynamics_`: complete.  


