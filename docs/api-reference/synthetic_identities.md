# Synthetic identities

The scheduler assigns each simulated patient a **unique identifier** and a **realistic name**, enabling reproducible yet human-readable synthetic records.  
These fields make the dataset suitable for interface mock-ups, educational dashboards, or identity token simulations while preserving complete anonymity.

---

## `patient_id`

Every patient receives a sequential, zero-padded identifier that guarantees uniqueness within the dataset.  

### Format
**Type:** string  
**Example:** `"00001"`, `"01234"`  
**Length:** dynamically adjusted based on population size  

### Validation rules
- Assigned sequentially during patient generation (`generate_patients`).  
- Always unique within a dataset.  
- The padding length increases automatically to maintain equal width (e.g., 5 digits for ≤99 999 patients).  

### How it works
`patient_id` is generated after all demographic records are created.  
The internal counter `self.patient_id_counter` tracks the last assigned ID, ensuring continuity across multiple simulation runs or chained population expansions.

```python
ids = [f"{i:0{id_length}d}" for i in range(start, start + total_patients)]
```

This allows reproducible record identifiers even when the scheduler is used iteratively.

---

## `name`

Simulated using the **[Faker](https://faker.readthedocs.io/)** library to produce **realistic, gender-consistent names**.  
The generator draws from localized name corpora (default: English) and aligns each record’s `name` with its assigned `sex`.

### Format
**Type:** string  
**Stored in:** `patients` table only  
**Examples:** `"Sophie Martin"`, `"James Thompson"`  

### Validation rules
- Names are generated using `self.fake.name_female()` or `self.fake.name_male()` according to the patient’s sex.  
- Guaranteed to be non-empty and syntactically valid (alphabetic).  
- No two patients are guaranteed to have unique names, reflecting real-world repetition.

### How it works
1. The scheduler first samples age and sex distributions according to `age_gender_probs`.  
2. For each generated record:
   - If `sex="Female"` → calls `fake.name_female()`.  
   - If `sex="Male"` → calls `fake.name_male()`.  
3. The resulting list of names is combined with demographic attributes (`age`, `sex`, and `patient_id`) into a `patients` DataFrame.

```python
patients.append({
    "name": self.fake.name_female(),
    "sex": "Female",
    "age": int(age)
})
```

This approach ensures realism without introducing any personally identifiable information (PII).

---

## Demographic consistency

The `generate_patients()` function integrates name assignment with the age–sex probabilities (`age_gender_probs`) derived from NHS England data (2023–24).  
For each sampled patient:
- Age is drawn from the range corresponding to their age bin (e.g., `"45–49"`).  
- Sex determines the naming function and demographic probability weighting.  
- Optional truncation removes out-of-range ages (`truncated=True`).  

Resulting table:

| Column | Description |
|---------|-------------|
| `patient_id` | Sequential synthetic ID |
| `name` | Gender-consistent name |
| `sex` | `"Male"` or `"Female"` |
| `age` | Random integer within sampled age range |

---

### Examples

**Default configuration**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(seed=42)
patients = sched.generate_patients(total_patients=5)
print(patients)
```

Output:

| patient_id | name              | sex     | age |
|-------------|------------------|---------|-----|
| 00001       | Emily Lewis       | Female  | 37  |
| 00002       | James Turner      | Male    | 62  |
| 00003       | Sarah Murray      | Female  | 49  |
| 00004       | Robert Hill       | Male    | 72  |
| 00005       | Olivia Clark      | Female  | 58  |

**Localized or custom naming**
```python
from faker import Faker
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler()
sched.fake = Faker('es_ES')  # Spanish names
patients = sched.generate_patients(5)
```

---

### References

- [Faker library documentation](https://faker.readthedocs.io/en/master/) – used for name generation.  
- NHS England (2024). *Hospital Outpatient Activity 2023–24: Summary Report 3.*  
  [https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx](https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx)

---

### Next steps

- {doc}`patient_demographics` – explains how age and sex are sampled.  
- {doc}`patient_flow` – models recurrence and first-attendance ratios.  
- {doc}`attendance_behavior` – describes appointment outcomes and rebooking behavior.

