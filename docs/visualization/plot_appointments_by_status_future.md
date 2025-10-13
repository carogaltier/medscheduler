# Visualizing Upcoming Appointment Outcomes

Displays the **percentage distribution of scheduled and cancelled appointments** for dates *after* the scheduler’s reference date (`ref_date`). This forward-looking chart helps evaluate upcoming workload and cancellation patterns in the near future.

---

## Function Overview
**Function:** `medscheduler.utils.plotting.plot_appointments_by_status_future(df, *, scheduler, date_col='appointment_date', status_col='status')`

**Inputs:**
- `df (pd.DataFrame)` — Appointment table containing at least the specified `date_col` and `status_col`.
- `scheduler (AppointmentScheduler)` — Must include a `ref_date` attribute indicating the start of the forecast window.
- `date_col (str)` — Column name with appointment dates. Default: `"appointment_date"`.
- `status_col (str)` — Column name with appointment statuses. Default: `"status"`.

**Returns:** `matplotlib.axes.Axes` — Vertical bar chart showing the proportion of *future* appointments by status.

**Validation & error handling:**
- Missing columns → raises `ValueError("DataFrame must contain columns: …")`.
- Scheduler without `ref_date` → raises `ValueError("Scheduler must have a `ref_date` attribute.")`.
- No future rows (`date > ref_date`) → `_empty_plot("No future appointments available after reference date.")`.

---

## Output Description
- **X-axis:** Appointment statuses (`scheduled`, `cancelled`, etc.)
- **Y-axis:** Percentage of future appointments.
- **Bars:** Color-coded by status using the Medscheduler palette:
  - `scheduled` = `#CD77B6`
  - `cancelled` = `#B3C1F2`
- **Annotations:** Displays percentage values above bars.
- **Style:** Compact design optimized for dashboards, with dashed Y-grid, no top/right spines, and left-aligned title.

This visualization provides a concise overview of upcoming clinic activity, enabling quick detection of overbooking, cancellations, or low utilization in the days following the reference date.

---

## Example
```python
from medscheduler import AppointmentScheduler
from medscheduler.utils.plotting import plot_appointments_by_status_future

# Generate future appointment dataset
sched = AppointmentScheduler()
slots_df, appts_df, patients_df = sched.generate()

# Visualize distribution of future appointments by status
ax = plot_appointments_by_status_future(appts_df, scheduler=sched)
ax.figure.show()  # optional when running interactively
```

---

## Next Steps
- Compare with historical appointment outcomes: {doc}`../visualization/plot_appointments_by_status`
- Review status categories and cancellation rates: {doc}`../api-reference/attendance_behavior`
- Understand reference date logic for upcoming data: {doc}`../api-reference/date_ranges_ref_date`
- Explore booking horizon and utilization parameters: {doc}`../api-reference/booking_dynamics`


