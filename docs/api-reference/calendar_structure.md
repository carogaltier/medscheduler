# Calendar structure

The calendar structure parameters define **when slots are created during the week** and the **density of appointments per hour**.  
They work together with `date_ranges` and `ref_date` to determine the effective slot calendar.

---

## `working_days`

### Purpose
Specifies which weekdays are considered valid for scheduling.  
Weekdays follow Python’s convention: `0=Monday ... 6=Sunday`.

### Defaults
- If not provided, defaults to **Monday–Friday**: `(0, 1, 2, 3, 4)`.

### Validation
- Must be a list or tuple of integers between 0 and 6.  
- Duplicates are removed internally.  
- Values are sorted.  
- An empty list is invalid.  

### Examples
```python
# Standard Mon–Fri calendar
sched = AppointmentScheduler(working_days=[0,1,2,3,4])

# Include Saturdays
sched = AppointmentScheduler(working_days=[0,1,2,3,4,5])
```

---

## `working_hours`

### Purpose
Defines the daily working shifts during which slots are generated.

### Format
- Accepts a single tuple `(start, end)` or a list of tuples.  
- Each start/end can be:  
  - Integer hours (0–23) → `(8, 16)`  
  - Strings `"HH"` → `("8", "16")`  
  - Strings `"HH:MM"` where minutes must be `00` or `30` → `("08:30", "16:30")`  

### Defaults
- If not provided, defaults to a **single shift 08:00–18:00**.  
- Each block is inclusive at the start and exclusive at the end.  

### Validation
- Each block must satisfy `start < end`.  
- Hours must be in [0..23]. Minutes must be 00 or 30.  
- Blocks must not overlap.  
- Blocks are automatically sorted by start time.  

### Examples
```python
# Morning + afternoon shifts
sched = AppointmentScheduler(working_hours=[(8,12), (13,17)])

# Continuous 8am–8pm day
sched = AppointmentScheduler(working_hours=[(8,20)])

# Using strings with 30-minute granularity
sched = AppointmentScheduler(working_hours=[("08:30","12:30"),("13:00","18:00")])
```

---

## `appointments_per_hour`

### Purpose
Defines the slot density per hour.  
Each hour is divided into equally sized slots, and this parameter sets the number of slots.

### Defaults
- Default = **4**, i.e. four appointments per hour (15-minute slots).  
  This setting reflects a scenario commonly used in primary care [1].

### Validation
- Must be an integer that divides 60 evenly.  
- Valid values include: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60.  
- Any invalid value raises a `ValueError`.  

### Derived attribute
- The slot duration in minutes can be retrieved via the property `slot_duration_min`.  
  Example: if `appointments_per_hour=6`, then `slot_duration_min=10`.  

### Examples
```python
# 10-minute slots
sched = AppointmentScheduler(appointments_per_hour=6)
print(sched.slot_duration_min)  # 10

# 30-minute slots
sched = AppointmentScheduler(appointments_per_hour=2)
```

---

## Summary

- **`working_days`** controls which weekdays contain slots.  
- **`working_hours`** sets the time ranges for each day.  
- **`appointments_per_hour`** sets the density of slots within those hours.  

Together, they define the structure of the appointment calendar before applying seasonality, booking dynamics, or attendance behavior.

---

**References**  
[1] Fiscella, K., & Epstein, R. M. (2008). *So much to do, so little time: care for the socially disadvantaged and the 15-minute visit*.  
Archives of Internal Medicine, 168(17), 1843–1852.  
[https://doi.org/10.1001/archinte.168.17.1843](https://doi.org/10.1001/archinte.168.17.1843)