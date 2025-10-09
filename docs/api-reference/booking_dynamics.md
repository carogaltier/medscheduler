# Booking dynamics

The parameters **`fill_rate`**, **`booking_horizon`**, and **`median_lead_time`** jointly control how appointment slots are booked over time.  
They determine the overall occupancy, how far in advance patients can schedule, and how early bookings tend to occur relative to the appointment date.

---

## `fill_rate`

Defines the proportion of available slots that are booked with appointments.  
It determines the overall utilization level of the generated calendar and represents system efficiency in using available capacity.

### Format
**Type:** float  
**Default:** `0.9` (90% utilization)  
**Accepted values:** between `0.3` and `1.0` inclusive  
**Typical range:** 0.9–0.95 in well-functioning outpatient systems [1]

### Validation rules
- Must be a float between 0.3 and 1.0.  
- Values below 0.3 raise a `ValueError`, as they represent implausibly low utilization.  
- Values above 1.0 are invalid since they exceed total capacity.

### How it works
- The fill rate is applied primarily to slots **before the reference date (`ref_date`)**, representing historical appointment activity.  
- For **future slots**, a *decaying probability model* is used, where near-term slots are more likely to be filled than those farther in the future.  
- This behavior mimics real-world scheduling, where future calendars are only partially filled.  
- When combined with `month_weights` and `weekday_weights`, it defines the **temporal density of booked appointments**, balancing capacity and realism.

### Examples

**High utilization (near-capacity system)**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(fill_rate=0.95)
sched.generate()
```

**Low utilization (underused system)**
```python
sched = AppointmentScheduler(fill_rate=0.5)
sched.generate()
```

---

## `booking_horizon`

Defines how far into the future patients are allowed to book appointments.  
It acts as a soft temporal limit and ensures the available date range extends beyond the reference date if necessary.

### Format
**Type:** int  
**Default:** `30` (days)  
**Units:** days ahead of the reference date  
**Typical range:** 7–90 days

### Validation rules
- Must be an integer between **7 and 90**.  
- Values below 7 or above 90 raise a `ValueError`.  
- Ensures that simulated calendars are realistic and prevent overly short or excessively long booking windows.  
- After validation, the scheduler automatically extends the latest date range to at least `ref_date + booking_horizon`.

### How it works
If `booking_horizon = 30`, the scheduler guarantees that the simulated calendar extends at least 30 days beyond the `ref_date`.  
This ensures sufficient forward capacity for future appointments and avoids truncating upcoming days.

Empirical evidence shows that longer booking horizons are associated with **higher no-show rates**, while shorter ones limit access.  
A 30-day horizon provides a realistic balance between accessibility and attendance reliability [2].

### Examples

**Extended booking window (long-term scheduling)**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(booking_horizon=60)
sched.generate()
```

**Restricted booking window (short-term scheduling)**
```python
sched = AppointmentScheduler(booking_horizon=14)
sched.generate()
```

---

## `median_lead_time`

Defines the median number of days between when a booking is made and when the appointment occurs.  
It governs how early patients tend to schedule relative to their visit date.

### Format
**Type:** int  
**Default:** `10` (days)  
**Units:** days between booking date and appointment date

### Validation rules
- Must be a positive integer.  
- Must not exceed the current `booking_horizon`.  
  If `median_lead_time > booking_horizon`, a `ValueError` is raised.  
- This ensures internal consistency: the median booking delay cannot exceed the maximum allowed booking window.

### How it works
This parameter shapes the **lead-time distribution** of bookings:  
- Smaller values → reactive systems (patients book close to the visit date).  
- Larger values → proactive systems (booked well in advance).  
The scheduler samples booking dates using a probabilistic decay model centered around this median, yielding realistic temporal dispersion of appointments.  

Empirical studies in primary care suggest a median lead time around 10 days [3].

### Examples

**Short-lead reactive system**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(median_lead_time=5)
sched.generate()
```

**Planned long-lead system**
```python
sched = AppointmentScheduler(median_lead_time=20)
sched.generate()
```

---

### References

[1] Buttz, L. (2004). *How to use scheduling data to improve efficiency.*  
*Family Practice Management, 11*(7), 27–29. [PMID: 15315285](https://pubmed.ncbi.nlm.nih.gov/15315285/)

[2] Woodcock, E., Nokes, D., Bolton, H., Bartholomew, D., Johnson, E., & Shakarchi, A. F. (2020).  
*The Influence of the Scheduling Horizon on New Patient Arrivals.*  
*Journal of Ambulatory Care Management, 43*(3), 221–229.  
[https://doi.org/10.1097/JAC.0000000000000334](https://doi.org/10.1097/JAC.0000000000000334)

[3] Grande, D., Zuo, J. X., Venkat, R., Chen, X., Ward, K. R., Seymour, J. W., & Mitra, N. (2018).  
*Differences in Primary Care Appointment Availability and Wait Times by Neighborhood Characteristics: a Mystery Shopper Study.*  
*Journal of General Internal Medicine, 33*(9), 1441–1443.  
[https://doi.org/10.1007/s11606-018-4407-9](https://doi.org/10.1007/s11606-018-4407-9)

---

### Next steps

- {doc}`date_ranges_ref_date` – explains reference dates and effective calendar windows.  
- {doc}`seasonality_weights` – details monthly and weekday weight adjustments.  
- {doc}`calendar_structure` – defines the working-day, hour, and slot configuration.
