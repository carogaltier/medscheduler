# Appointment timing

The parameters **`check_in_time_mean`** and the internal duration model define how early patients arrive and how long attended visits last.  
Together, they simulate the **temporal dynamics** of an outpatient session — from patient arrival to consultation completion — enabling realistic waiting-time and throughput estimates.

---

## `check_in_time_mean`

Controls the **average arrival offset** (in minutes) relative to the scheduled appointment time.  
A negative value indicates early arrival, while positive values indicate delays.

### Format
**Type:** float  
**Default:** `-10.0` (10 minutes early)  
**Accepted range:** −60 to +30 minutes  
**Units:** minutes relative to the scheduled start

### Validation rules
- Must be a float within the range −60 ≤ `check_in_time_mean` ≤ +30.  
- Values outside this range raise a `ValueError`.  
- If omitted, defaults to −10 minutes (based on empirical punctuality studies).

### How it works
At simulation time, each patient’s arrival is drawn from a **Normal distribution** centered on the configured mean (`check_in_time_mean`), with a standard deviation of approximately **9.8 minutes**.  
This reflects real-world variability in patient punctuality.  
The resulting check-in time is computed as:

\[
t_{\text{arrival}} = t_{\text{scheduled}} + N(\text{mean}=\text{check\_in\_time\_mean},\, \sigma=9.8)
\]

A value of −10 means patients arrive, on average, 10 minutes before their appointment.  
The model allows a small fraction of patients to arrive significantly earlier or later (unclipped tails), which enhances realism.

Empirical evidence from *Cerruti et al. (2023)* [1] shows that **84.4% of patients check in before their appointment time**, with a **mode of −10 minutes**, closely matching this default configuration.

### Examples

**Default punctuality (mean = −10 min)**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(check_in_time_mean=-10)
sched.generate()
```

**Simulate a clinic with frequent late arrivals**
```python
sched = AppointmentScheduler(check_in_time_mean=5)
sched.generate()
```

---

## Appointment duration model

Appointment duration is not directly user-configurable but is internally simulated for each **attended** visit using a stochastic model derived from empirical data.

### Distribution
- Drawn from a **Beta(1.48, 3.6)** distribution, scaled to the range 0–60 minutes.  
- Yields an average duration of approximately **17.4 minutes** and a **median of 15.8 minutes**.  
- These values align with primary care observations by *Tai-Seale et al. (2007)* [2].

### How it works
For each attended appointment, the scheduler simulates:
1. **Check-in time** — drawn from the punctuality distribution.  
2. **Start time** — the later of the arrival time or previous consultation end.  
3. **Delay before start** — random waiting time due to backlog (~1 minute).  
4. **Duration** — randomly drawn from the Beta distribution.  
5. **End time** — start + duration.  

The result includes realistic variation in waiting time, overlap, and throughput across the clinic day.

### Example output fields
When `AppointmentScheduler.assign_actual_times()` is applied, the following columns are generated for attended visits:

| Column | Description |
|--------|--------------|
| `check_in_time` | Timestamp of patient arrival |
| `start_time` | Actual consultation start time |
| `end_time` | Actual consultation end time |
| `appointment_duration` | Duration of the consultation (minutes) |
| `waiting_time` | Delay between arrival and start (minutes) |

All times are formatted as `"HH:MM:SS"` for ease of analysis and visualization.

### Example usage

```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(check_in_time_mean=-10)
sched.generate()
appointments = sched.appointments_df.head()

print(appointments[["appointment_date", "check_in_time", "start_time", "end_time", "waiting_time"]])
```

---

### References

[1] Cerruti, B., Garavaldi, D., & Lerario, A. (2023).  
*Patient's punctuality in an outpatient clinic: the role of age, medical branch and geographical factors.*  
*BMC Health Services Research, 23*(1), 1385.  
[https://doi.org/10.1186/s12913-023-10379-w](https://doi.org/10.1186/s12913-023-10379-w)

[2] Tai-Seale, M., McGuire, T. G., & Zhang, W. (2007).  
*Time allocation in primary care office visits.*  
*Health Services Research, 42*(5), 1871–1894.  
[https://doi.org/10.1111/j.1475-6773.2006.00689.x](https://doi.org/10.1111/j.1475-6773.2006.00689.x)

---

### Next steps

- {doc}`attendance_behavior` – explains appointment outcomes and rebooking probabilities.  
- {doc}`booking_dynamics` – describes how future and past slots are filled.  
- {doc}`calendar_structure` – defines working hours and slot configuration.

