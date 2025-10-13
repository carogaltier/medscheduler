# Summarizing Slot Availability

Provides a concise statistical overview of the **slot calendar**, including total capacity, availability rates, and utilization split into past and future periods relative to the scheduler’s reference date. Useful for **report headers, summary dashboards**, or validating simulation realism before plotting.

---

## Function Overview
**Function:** `medscheduler.utils.plotting.summarize_slots(df, scheduler, date_col='appointment_date', available_col='is_available')`

**Inputs:**
- `df (pd.DataFrame)` — Slots table containing at least `appointment_date` and `is_available`.
- `scheduler (AppointmentScheduler)` — Provides configuration attributes (`ref_date`, `working_days`, `working_hours`, `appointments_per_hour`).
- `date_col (str)` — Name of the slot date column. Default: `"appointment_date"`.
- `available_col (str)` — Boolean column indicating slot availability. Default: `"is_available"`.

**Returns:**
- **`dict[str, Any]`** — Fields of a `SlotSummary` object.  
- Or **`matplotlib.axes.Axes`** if validation fails (missing columns or scheduler attributes).  

**Validation & fallback behavior:**
- Empty `df` → returns a zeroed summary dict.
- Missing required columns → returns `_empty_plot("`df` must include columns: …")`.
- Missing scheduler attributes → returns `_empty_plot("Scheduler must have attribute `…`.")`.

---

## Output Description
The function summarizes key operational metrics:
- **Total slots** and **operating days** across the simulation period.
- **Mean slots per working day** and **slots per week** derived from scheduler configuration.
- **Availability rate:** proportion of slots still open.
- **Past / Future segmentation:** counts and fill rates before and after `ref_date`.
- **Weekday distribution:** number of slots by weekday abbreviation (Mon–Sun).

The result can be converted to a `pd.Series` or displayed as a small summary table.

---

## Example
```python
from medscheduler import AppointmentScheduler
from medscheduler.utils.plotting import summarize_slots
import pandas as pd

# Simulate a semester-long outpatient calendar
sched = AppointmentScheduler()
slots_df, appts_df, patients_df = sched.generate()

# Compute capacity and utilization summary
summary = summarize_slots(slots_df, scheduler=sched)

# Display results as a Series for clarity
pd.Series(summary, name="Slots Summary")
```

---

## Next Steps
- Review slot generation and structure: {doc}`../api-reference/slots_table`
- Learn how reference dates define past/future segmentation: {doc}`../api-reference/date_ranges_ref_date`
- Explore utilization and fill rate dynamics: {doc}`../api-reference/booking_dynamics`
- Visualize past and future availability: {doc}`../visualization/plot_past_slot_availability`, {doc}`../visualization/plot_future_slot_availability`

