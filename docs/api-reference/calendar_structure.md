# Calendar structure

The calendar structure parameters define **when slots are created during the week** and the **density of appointments per hour**.  
Together, they determine the daily pattern of the appointment calendar. These settings work in conjunction with `date_ranges` and `ref_date` to define the total scheduling capacity.

---

## `working_days`

`working_days` specifies which weekdays are valid for scheduling appointments. It follows Python’s weekday convention: `0 = Monday … 6 = Sunday`.

### Format

**Type:** list or tuple of integers  
**Default:** `(0, 1, 2, 3, 4)` → Monday to Friday  
**Accepted values:** integers between `0` and `6` inclusive  
**Input formats:** list or tuple, e.g. `[0, 1, 2, 3, 4]`

### Validation rules

- Must be a list or tuple of integers between 0 and 6.  
- Duplicates are automatically removed.  
- Values are sorted in ascending order.  
- An empty list is invalid.  

### How it works

`working_days` determines which weekdays are available for creating appointment slots. Only the specified days are included in the calendar generation process. When generating the slot table, the scheduler iterates through each date in `date_ranges`, filtering out any that do not match the selected weekdays.  

If no `working_days` argument is provided, the system defaults to Monday through Friday, representing a typical outpatient schedule. Including weekends can be useful for simulating urgent care or extended‑hours services.

### Examples

**Standard Monday–Friday calendar**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(working_days=[0, 1, 2, 3, 4])
```

**Include Saturdays**
```python
sched = AppointmentScheduler(working_days=[0, 1, 2, 3, 4, 5])
```

---

## `working_hours`

`working_hours` defines the daily time blocks during which appointment slots are generated. Multiple blocks can be used to represent morning and afternoon shifts.

### Format

**Type:** tuple `(start, end)` or list of tuples  
**Default:** `[(8, 18)]` → one continuous 10‑hour shift  
**Accepted values:** hour or time strings  
- Integer hours (0–23) → `(8, 16)`  
- Strings `'HH'` → `('8', '16')`  
- Strings `'HH:MM'` (minutes must be `00` or `30`) → `('08:30', '16:30')`

**Input formats:** accepts either integers or strings with 30‑minute granularity. Internally, all blocks are converted to minute offsets from midnight and sorted chronologically.

### Validation rules

- Each `(start, end)` must satisfy `start < end`.  
- Hours must fall within `[0..23]`, and minutes must be either `00` or `30`.  
- Blocks must not overlap.  
- All valid blocks are automatically sorted by start time.  
- Invalid or overlapping intervals raise a `ValueError`.  

### How it works

The scheduler uses `working_hours` to determine **when** during each working day slots can exist. Each day within the valid `working_days` is divided according to these shifts, and slots are generated for each hour range.  

If multiple blocks are defined (for example, `(8, 12)` and `(13, 17)`), the scheduler will produce a break between 12:00 and 13:00.  
All times are treated as half‑hour aligned to maintain compatibility with slot durations derived from `appointments_per_hour`.

### Examples

**Morning and afternoon shifts**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(working_hours=[(8, 12), (13, 17)])
```

**Continuous 8 am–8 pm day**
```python
sched = AppointmentScheduler(working_hours=[(8, 20)])
```

**Using strings with 30‑minute precision**
```python
sched = AppointmentScheduler(working_hours=[("08:30", "12:30"), ("13:00", "18:00")])
```

---

## `appointments_per_hour`

`appointments_per_hour` controls how many appointment slots are created within each working hour. It determines the **slot density** and therefore the granularity of the schedule.

### Format

**Type:** integer  
**Default:** `4` → four appointments per hour (15‑minute slots)  
**Accepted values:** integers that evenly divide 60, such as `1`, `2`, `3`, `4`, or `6`.  
**Derived attribute:** the slot duration (minutes) can be accessed via the property `slot_duration_min`, computed as `60 // appointments_per_hour`.

### Validation rules

- Must be an integer value dividing 60 evenly.  
- Valid values include: 1 (60 min), 2 (30 min), 3 (20 min), 4 (15 min), 6 (10 min).
- Invalid values raise a `ValueError`.  

### How it works

This parameter defines the **slot frequency** within each hour of the working schedule. For example, if `appointments_per_hour = 4`, each hour is divided into four 15‑minute slots.  
Higher densities (e.g., `6` → 10‑minute slots) increase the total number of slots in the generated calendar, while lower densities represent longer consultation times.  

The chosen density interacts directly with `working_hours` and `fill_rate`: more slots mean greater capacity, and `fill_rate` determines how many of them will be booked.  
The `slot_duration_min` property is a convenient way to retrieve the effective slot length.

### Examples

**10‑minute slots**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(appointments_per_hour=6)
print(sched.slot_duration_min)  # 10
```

**30‑minute slots**
```python
sched = AppointmentScheduler(appointments_per_hour=2)
```

---

### Next steps

- {doc}`booking_dynamics` – explore how fill rate and booking horizon determine slot utilization.  
- {doc}`seasonality_weights` – see how monthly and weekday weights affect slot distribution.

