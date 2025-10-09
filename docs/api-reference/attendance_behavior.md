# Attendance behavior

The parameters **`status_rates`** and **`rebook_category`** define how appointments behave once scheduled.  
They determine the **outcome distribution** (attended, cancelled, no-show, unknown) and the **extent to which cancelled slots are rebooked**.

These mechanisms ensure the generated dataset reflects realistic outpatient activity, where missed or cancelled appointments may trigger follow-up bookings according to probabilistic rules.

---

## `status_rates`

### Purpose
Defines the proportion of appointment outcomes — whether patients attend, cancel, or miss their scheduled visit.

### Defaults (NHS 2023–24)
Derived from NHS England *Hospital Outpatient Activity, Summary Report 1 (2023–24)*.

| Status            | Probability |
|-------------------|-------------|
| **attended**      | 0.773 |
| **cancelled**     | 0.164 |
| **did not attend**| 0.059 |
| **unknown**       | 0.004 |

These values represent national averages across all specialties and appointment types.  
They are validated to ensure the probabilities sum to 1.0 (normalized internally if small deviations occur).

### Behavior
During simulation, each generated appointment receives one of these outcomes according to the given probabilities.  
The rates primarily affect **past appointments** (those dated before `ref_date`), but future appointments may also be assigned probabilistically if the user requests a complete calendar simulation.

### Customization
You may provide custom rates as a dictionary:

```python
custom_rates = {
    "attended": 0.80,
    "cancelled": 0.15,
    "did not attend": 0.04,
    "unknown": 0.01,
}

scheduler = AppointmentScheduler(status_rates=custom_rates)
```

If values do not sum exactly to 1, they are automatically normalized with a warning.

---

## `rebook_category`

### Purpose
Controls how frequently cancelled or missed appointments are **rebooked** (i.e., patients who attempt again later).

| Category | Rebook ratio | Description |
|-----------|--------------|-------------|
| `'min'`   | 0.0 | No rebooking — cancellations are lost. |
| `'med'`   | 0.5 | Half of cancellations are rebooked (default). |
| `'max'`   | 1.0 | All cancelled appointments are rebooked. |

### Defaults
- Default = `'med'` → 50% of cancelled appointments are rebooked.  
- Valid values: `'min'`, `'med'`, `'max'`.

### Behavior
When an appointment is cancelled or missed, a rebooking probability is applied based on the selected category.  
Rebooked slots are placed later in the simulation window, following realistic temporal and behavioral rules.

This ensures plausible continuity in care delivery — for example, some patients reschedule promptly after a cancellation, while others drop out of the schedule.

### Example

```python
from medscheduler import AppointmentScheduler

# High rebooking scenario (all cancellations rebooked)
scheduler = AppointmentScheduler(rebook_category="max")
scheduler.generate()
```

---

## Simulation impact

- Higher **`attended`** and **`rebook_category="max"`** increase total appointment volume and reduce wasted slots.  
- High **`cancelled`** or **`did not attend`** rates simulate less efficient systems.  
- Combined with **`fill_rate`**, these parameters determine **effective utilization** and **attendance KPIs** in the generated dataset.

---

## References

- NHS Digital. *Hospital Outpatient Activity, 2023–24 (Workbook; Hospital Episode Statistics).*  
  [https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx](https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx)

- Ellis, D. A., & Jenkins, R. (2012). *Weekday affects attendance rate for medical appointments: Large-scale data analysis and implications.*  
  *PLOS ONE, 7*(12), e51365. [https://doi.org/10.1371/journal.pone.0051365](https://doi.org/10.1371/journal.pone.0051365)

---

## See also

- {doc}`booking_dynamics` – controls how far ahead and how fully appointments are scheduled.  
- {doc}`visits_per_year` – defines the average number of visits per patient per year.
