# Outputs overview

After running the `.generate()` method, **medscheduler** produces three interconnected outputs that
together simulate an outpatient scheduling system. Each output is returned as a pandas DataFrame and
can optionally be exported to CSV files for portability.

---

## 1. Appointments (primary output)

The **appointments** table is the central dataset. It contains all information needed for most analytics workflows
and can often be used on its own without referencing the auxiliary tables.

### Key columns

| Column               | Description |
|-----------------------|-------------|
| `appointment_id`      | Unique identifier for each appointment. |
| `slot_id`             | Links the appointment to a calendar slot. |
| `patient_id`          | Identifier of the assigned patient. |
| `scheduling_date`     | Date when the appointment was booked. |
| `scheduling_interval` | Days between scheduling and appointment date (lead time). |
| `appointment_date`    | Scheduled date of the visit. |
| `appointment_time`    | Scheduled time of the visit. |
| `status`              | Outcome of the appointment: attended, did not attend, cancelled, rebooked, unknown. |
| `sex`, `age`, `age_group` | Patient demographics attached to the appointment. |
| `check_in_time`       | Actual time of arrival (attended only). |
| `start_time` / `end_time` | When the consultation began and ended. |
| `waiting_time`        | Minutes waited before start. |
| `appointment_duration`| Duration of the consultation in minutes. |

> **Tip:** For most analyses (attendance, waiting time, cancellations), this is the only table you need.

---

## 2. Slots (auxiliary)

The **slots** table represents the appointment calendar capacity.  
It is useful for analyzing utilization, availability, and overbooking strategies.

### Key columns

| Column            | Description |
|-------------------|-------------|
| `slot_id`         | Unique identifier for each slot. |
| `appointment_date`| Date of the slot. |
| `appointment_time`| Time of the slot. |
| `is_available`    | Boolean flag indicating if the slot is still open. |

---

## 3. Patients (auxiliary)

The **patients** table contains the synthetic registry of individuals who may receive appointments.
Demographics are generated using age–sex distributions derived from NHS data, but can be customized.

### Key columns

| Column     | Description |
|------------|-------------|
| `patient_id` | Unique identifier for each synthetic patient. |
| `name`       | Fake name (generated with `Faker`). |
| `sex`        | Biological sex of the patient. |
| `age`        | Age in years. |
| `dob`        | Date of birth (if configured). |
| `age_group`  | Age band for grouped analysis. |

---

## Summary

- **Appointments** is the primary dataset and usually sufficient for analysis.  
- **Slots** enables capacity and utilization studies.  
- **Patients** provides demographic context and can be linked to appointments for richer analysis.  

For advanced configuration of how these tables are generated, continue to the {doc}`customization_options` section.
