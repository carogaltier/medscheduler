# Visualizing Future Slot Availability

Displays **projected slot utilization** for upcoming periods, starting from the scheduler’s reference date (`ref_date`) and extending up to the booking horizon (if defined). The chart helps assess how far into the future appointment slots are already filled and how much open capacity remains.

---

## Function Overview
**Function:** `medscheduler.utils.plotting.plot_future_slot_availability(slots_df, *, scheduler=None, ref_date=None, date_col='appointment_date', available_col='is_available', freq='W', limit_future_to_horizon=True, min_bar_px=55, label_px_threshold=55, min_fig_w_in=7.0, max_fig_w_in=16.0, dpi=100, title='Slot Availability (Future)')`

**Inputs:**
- `slots_df (pd.DataFrame)` — Table of appointment slots with columns `appointment_date` and `is_available`.
- `scheduler (AppointmentScheduler, optional)` — Provides configuration including `ref_date` and `booking_horizon`.
- `ref_date (str | pd.Timestamp, optional)` — Override for the scheduler’s reference date.
- `date_col (str)` — Column for slot dates. Default: `"appointment_date"`.
- `available_col (str)` — Column for slot availability (True = open, False = filled). Default: `"is_available"`.
- `freq (str)` — Desired aggregation frequency: one of `D`, `W`, `M`. Default: `"W"`.
- `limit_future_to_horizon (bool)` — When `True`, limits display to the scheduler’s `booking_horizon` days beyond `ref_date`. Default: `True`.
- `min_bar_px (int)` — Minimum horizontal pixels per bar for readability.
- `label_px_threshold (int)` — Minimum pixels per bar to display value labels.
- `min_fig_w_in`, `max_fig_w_in` (`float`) — Minimum and maximum figure width in inches.
- `dpi (int)` — Dots per inch for scaling.
- `title (str)` — Chart title. Default: “Slot Availability (Future)”.

**Returns:** `matplotlib.axes.Axes` — Stacked bar chart showing booked vs. available slots in the future.

**Validation & error handling:**
- Empty DataFrame → `_empty_plot("No data")`.
- No rows in future window → `_empty_plot("No future data in the selected window")`.
- Invalid `freq` argument → raises `ValueError("freq must be one of: 'D', 'W', 'M'")`.
- Too many bars to render legibly → `_empty_plot("Too many bars for a readable chart at any granularity.")`.

---

## Output Description
- **X-axis:** Future time periods (Days, Weeks, or Months) relative to `ref_date`.
- **Y-axis:** Number of appointment slots.
- **Bars:** Stacked visualization where the lower bar section represents *filled* slots and the upper section *available* slots.
- **Color coding:** Available = `#43AD7E` (green); Filled = `#FF6F61` (salmon).
- **Auto-aggregation:** If too many bars are generated, the function automatically switches to a coarser frequency (e.g., from weeks to months) and appends “— auto-aggregated to {freq}” to the title.
- **Horizon control:** When `limit_future_to_horizon=True`, data is truncated to the scheduler’s `booking_horizon` (in days) beyond `ref_date`.
- **Grid & layout:** Dashed Y-grid, no top/right spines, legend positioned above the plot.

---

## Example
```python
from medscheduler import AppointmentScheduler
from medscheduler.utils.plotting import plot_future_slot_availability

# Simulate default outpatient calendar
sched = AppointmentScheduler()
slots_df, appts_df, patients_df = sched.generate()

# Visualize projected capacity beyond the reference date
ax = plot_future_slot_availability(slots_df, scheduler=sched)
ax.figure.show()  # optional when running interactively
```

---

## Next Steps
- Compare with past availability trends: {doc}`../visualization/plot_past_slot_availability`
- Understand booking horizon and forward visibility: {doc}`../api-reference/booking_dynamics`
- Review weekday and seasonal weights: {doc}`../api-reference/seasonality_weights`
- Learn about working hours and total slot capacity: {doc}`../api-reference/slots_table`


