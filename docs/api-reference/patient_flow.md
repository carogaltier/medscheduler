# Patient flow

The parameters **`first_attendance`** and **`visits_per_year`** describe how frequently patients interact with the system and how new versus returning attendances are distributed.  
Together, they control the **flow of patients through the appointment cycle**, determining whether visits correspond to new or follow-up encounters and how often each patient is expected to appear.

---

## `visits_per_year`

Defines the **average number of appointments per patient per year**.  
This parameter controls overall encounter frequency and scales the generated patient pool relative to total appointment volume.

### Format
**Type:** float  
**Default:** `1.2`  
**Typical range:** 0.5–4.0  
**Maximum allowed:** `12.0` (as defined in `constants.py`)

### Validation rules
- Must be a positive float ≤ `MAX_VISITS_PER_YEAR`.  
- Values greater than 12 trigger a `ValueError` since they imply unrealistic contact frequency for outpatient settings.  
- If omitted, the default value (1.2) is applied.

### How it works
This parameter determines how many total appointments are expected per patient per simulated year.  
Higher values increase patient revisit probability, while lower values simulate populations with fewer follow-ups.  
In combination with `first_attendance`, it shapes the balance between new and returning encounters.

The default value of **1.2 visits per year** reflects contemporary trends in primary care visit rates in the United States, as reported by Rao et al. (2019) [1].  
That study found a national decline in average visits per person—from 1.5 in 2008 to 1.2 in 2015—indicating reduced face-to-face utilization over time.

### Examples

**Use the default rate (1.2 visits per year)**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(visits_per_year=1.2)
sched.generate()
```

**Simulate a population with more frequent visits**
```python
sched = AppointmentScheduler(visits_per_year=3.0)
sched.generate()
```

---

## `first_attendance`

Defines the **proportion of appointments that correspond to first attendances** (i.e., new patients).  
This determines the fraction of visits that originate from new patients rather than follow-up encounters.

### Format
**Type:** float  
**Default:** `0.325` (32.5%)  
**Source:** Derived from *NHS England Hospital Outpatient Activity 2023–24, Summary Report 2* (stored in `constants.py`).

### Validation rules
- Must be a float in the range `[0, 1]`.  
- Values outside this range raise a `ValueError`.  
- If `None`, defaults to the NHS-derived proportion (`0.325`).

### How it works
During simulation, each generated appointment is tagged as either **first attendance** or **follow-up** according to this ratio.  
A higher value produces more new patient records and a broader simulated cohort; lower values favor repeat visits.  
The scheduler uses this proportion to control both patient generation and re-identification across cycles.

For example:
- With `first_attendance = 0.3`, approximately 30% of appointments represent new patients.  
- The remaining 70% are attributed to previously seen individuals, preserving continuity and realism.

### Examples

**Use the default NHS first attendance rate**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(first_attendance=0.325)
sched.generate()
```

**Simulate a specialist clinic with mostly follow-ups**
```python
sched = AppointmentScheduler(first_attendance=0.1)
sched.generate()
```

---

### References

[1] Rao, A., Shi, Z., Ray, K. N., Mehrotra, A., & Ganguli, I. (2019).  
*National Trends in Primary Care Visit Use and Practice Capabilities, 2008–2015.*  
*Annals of Family Medicine, 17*(6), 538–544.  
[https://doi.org/10.1370/afm.2474](https://doi.org/10.1370/afm.2474)

[2] NHS England (2024). *Hospital Outpatient Activity 2023–24: Summary Report 2.*  
[https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx](https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx)

---
### Next steps
- Explore {doc}`patient_demographics` to learn how age and sex distributions are derived.  
- Review {doc}`patients_table` to understand how those demographic traits are represented.  
- See also {doc}`attendance_behavior` to connect attendance outcomes with patient flow dynamics.


