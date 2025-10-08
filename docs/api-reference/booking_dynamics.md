# Booking dynamics

The parameters **`fill_rate`**, **`booking_horizon`**, and **`median_lead_time`** define how appointment slots are booked over time.  
Together, they control the **overall occupancy**, **how far in advance patients can schedule**, and **how early they typically book** relative to the appointment date.

---

## `fill_rate`

### Purpose
Determines the proportion of available slots that are actually booked with appointments.  
It defines the overall utilization level of the generated calendar.

### Defaults
- Default = **0.9**, meaning 90% of all available slots are filled.  
- Valid range: **0.3–1.0**.  
  Values below 0.3 imply unrealistically low utilization and may lead to unstable scheduling behavior.  
  A fill rate of 0.9–0.95 is typical in well-functioning outpatient systems [1].

### Behavior
- The **fill rate is applied only to slots dated before the reference date (`ref_date`)**, representing past activity.  
- For slots after the reference date, a **decaying probability model** is applied:  
  near-future slots are more likely to be booked, while far-future slots remain mostly empty.

This reproduces real-world scheduling patterns where upcoming calendars are only partially filled in advance.

### Interaction with other parameters
- Works jointly with `booking_horizon` and `median_lead_time` to shape how quickly and how fully slots are filled.  
- Combined with `month_weights` and `weekday_weights`, it defines the **temporal density of booked appointments**.

---

## `booking_horizon`

### Purpose
Defines how far into the future patients can book appointments. The horizon acts as a soft limit, extending the available date range if needed.

### Defaults
- Default = **30 days**. This is a balanced value between accessibility and stability, based on observed outpatient booking behavior.

### Behavior
If `booking_horizon=30`, the scheduler ensures that the **latest date range extends at least 30 days beyond the reference date**.  
This allows future appointment generation and realistic calendar simulation.

### Evidence
Longer booking horizons are associated with **higher no-show rates**, while shorter ones may limit access.  
A 30-day window provides a realistic trade-off between operational flexibility and attendance reliability [2].

---

## `median_lead_time`

### Purpose
Defines the median number of days between the booking date and the appointment date.  
It shapes the lead-time distribution, influencing how early patients tend to schedule.

### Defaults
- Default = **10 days**, based on observed median waiting times in U.S. primary care [3].  

### Behavior
A lower `median_lead_time` implies a more reactive booking process (patients book close to the appointment date). Higher values simulate systems where appointments are planned further in advance.

---

## Example

```python
from medscheduler import AppointmentScheduler

# Simulate a lightly booked 2-month calendar with short booking lead time
scheduler = AppointmentScheduler(
    fill_rate=0.75,          # 75% utilization
    booking_horizon=45,      # appointments can be scheduled up to 45 days ahead
    median_lead_time=7       # patients book roughly a week before their visit
)

scheduler.generate()
appointments = scheduler.appointments_df.head()
print(appointments)
```

This configuration produces a moderately utilized calendar with realistic appointment timing and partial future occupancy.

---

## References

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

## See also

- {doc}`date_ranges_ref_date` – explains reference dates and effective calendar windows.  
- {doc}`seasonality_weights` – details monthly and weekday weight adjustments.
