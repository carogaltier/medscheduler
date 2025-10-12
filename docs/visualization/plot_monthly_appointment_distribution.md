# Visualizing Monthly Appointment Distribution

Displays the **percentage of appointments per month** across the entire dataset, allowing quick identification of seasonal peaks or gaps in activity. This visualization provides a high-level overview of the annual distribution of outpatient appointments.

---

## Function Overview
**Function:** `medscheduler.utils.plotting.plot_monthly_appointment_distribution(df)`

**Inputs:**
- `df (pd.DataFrame)` — Appointments table containing an `appointment_date` column (datetime-like or convertible).

**Returns:** `matplotlib.axes.Axes` — Bar chart showing the monthly percentage of total appointments.

**Validation & error handling:**
- Missing `appointment_date` column → raises `ValueError("DataFrame must contain an 'appointment_date' column.")`.
- Non-datetime values in `appointment_date` are automatically coerced using `pd.to_datetime(errors='coerce')`.

---

## Output Description
- **X-axis:** Calendar months (January–December).
- **Y-axis:** Percentage of total appointments in each month.
- **Bars:** Represent normalized frequencies of appointments (0–100%).
- **Color scheme:** Primary Medscheduler blue (`#67A7D4`).
- **Annotations:** Each bar displays its corresponding percentage value above the bar.
- **Style:** Minimalist PyData-style figure with dashed Y-grid and left-aligned title.

This plot helps verify whether the generated dataset reflects realistic or intentionally weighted seasonal patterns (e.g., reduced activity in summer months or end-of-year peaks).

---

## Example
```python
from medscheduler import AppointmentScheduler
from medscheduler.utils.plotting import plot_monthly_appointment_distribution

# Generate synthetic appointments
sched = AppointmentScheduler()
slots_df, appts_df, patients_df = sched.generate()

# Visualize monthly distribution of appointment activity
ax = plot_monthly_appointment_distribution(appts_df)
ax.figure.show()  # optional when running interactively
```

---

## Next Steps
- Explore seasonality weighting parameters: {doc}`../api-reference/seasonality_weights`
- Learn how appointment timing is determined: {doc}`../api-reference/appointment_timing`
- Review the main appointments table structure: {doc}`../api-reference/appointments_table`
- Adjust generation parameters for realistic temporal patterns: {doc}`../user-guide/customization_options`

