# Attendance behavior

The parameters **`status_rates`** and **`rebook_category`** control what happens to appointments once they are scheduled.  
Together, they define the **probabilities of attendance outcomes** and how often **cancelled or missed appointments are rebooked**.

---

## `status_rates`

Defines the probabilities of different appointment outcomes — whether patients attend, cancel, or miss their scheduled visit.

### Format
**Type:** `dict[str, float]`  
**Keys:** `{ "attended", "cancelled", "did not attend", "unknown" }`  
**Default:** Derived from *NHS England Hospital Outpatient Activity 2023–24 (Summary Report 1)*, stored in `constants.py` [1].  
These values represent national outpatient activity proportions for attended, cancelled, missed, and indeterminate outcomes:

```python
{
    "attended": 0.773,
    "cancelled": 0.164,
    "did not attend": 0.059,
    "unknown": 0.004,
}
```

**Accepted values:** user-provided dictionary with probabilities in `[0, 1]`.  
Values are automatically normalized if they do not sum to 1.0.

### Validation rules
- Must be a dictionary with exactly four keys: `"attended"`, `"cancelled"`, `"did not attend"`, `"unknown"`.  
- All values must be finite and non-negative.  
- If the sum of values deviates from 1.0 (tolerance ±1%), a warning is issued and the values are renormalized automatically.  
- If `status_rates=None`, the default NHS-derived probabilities are used.

### How it works
Each simulated appointment is assigned one of the four possible outcomes according to these probabilities.  
The rates reflect national outpatient trends reported by *NHS England Hospital Outpatient Activity (2023–24, Summary Report 1)*.  
They represent the proportion of attended, cancelled, missed (“did not attend”), and unspecified cases.

- **Attended:** appointment successfully completed.  
- **Cancelled:** appointment cancelled in advance (by patient or hospital).  
- **Did not attend (DNA):** missed without cancellation.  
- **Unknown:** indeterminate or unclassified cases.

If user-specified, these proportions influence the outcome assignment phase of the scheduler.  
The behavior of cancelled and missed appointments is further governed by `rebook_category`.

### Examples

**Use default NHS England proportions**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler()
print(sched.status_rates)
```

**Custom outcome probabilities**
```python
sched = AppointmentScheduler(
    status_rates={
        "attended": 0.80,
        "cancelled": 0.10,
        "did not attend": 0.09,
        "unknown": 0.01
    }
)
```

---

## `rebook_category`

Controls whether and how often cancelled appointments are rebooked.  
This parameter defines the **rebooking intensity**, modeling how outpatient services recycle missed slots.

### Format
**Type:** `str`  
**Default:** `"med"`  
**Accepted values:** `"min"`, `"med"`, `"max"`

| Category | Rebook Ratio | Description |
|-----------|---------------|-------------|
| `"min"` | 0.0 | No rebooking — cancelled appointments are lost. |
| `"med"` | 0.5 | 50% of cancelled appointments are rescheduled (balanced). |
| `"max"` | 1.0 | All cancelled appointments are rebooked. |

Internally, the `rebook_category` determines the numeric **`rebook_ratio`**, used to decide probabilistically whether a cancelled slot is replaced with a new booking attempt.

### Validation rules
- Must be one of `"min"`, `"med"`, or `"max"`.  
- Invalid strings raise a `ValueError`.  
- The corresponding numeric `rebook_ratio` is set automatically:
  ```python
  {"min": 0.0, "med": 0.5, "max": 1.0}
  ```

### How it works
When a cancellation occurs, the scheduler applies the `rebook_ratio` to determine if the appointment is rebooked.  
For example, with `"med"`, half of all cancelled appointments are recycled into new future bookings.  
This process preserves overall appointment volume and prevents an unrealistic decline in utilization.

The rebooking mechanism is applied only to **cancelled appointments** (not DNAs).  
Rescheduled cases are assigned a new date based on availability and the original patient’s booking behavior.

This approach helps maintain continuity in simulated appointment flow and reproduces the adaptive behavior seen in real outpatient systems.

### Examples

**Disable rebooking completely**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(rebook_category="min")
sched.generate()
```

**Allow all cancellations to be rebooked**
```python
sched = AppointmentScheduler(rebook_category="max")
sched.generate()
```

**Default (balanced rebooking at 50%)**
```python
sched = AppointmentScheduler()  # rebook_category="med"
```

---

### References

[1] NHS England (2024). *Hospital Outpatient Activity 2023–24: Summary Report 1.*  
[https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx](https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx)

---
### Next steps
- Continue to {doc}`patient_flow` to study how attendance influences visit frequency and new-patient ratios.  
- Examine {doc}`appointments_table` to see how these outcomes are stored in the final dataset.  
- For related parameters, see {doc}`booking_dynamics` and {doc}`appointment_timing`.


