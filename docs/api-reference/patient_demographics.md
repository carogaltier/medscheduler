# Patient demographics

The parameters **`age_gender_probs`**, **`bin_size`**, **`lower_cutoff`**, **`upper_cutoff`**, and **`truncated`** define the demographic composition of the synthetic patient cohort.  
They determine how age and sex are distributed, how patients are grouped into age intervals, and how outliers are handled during population sampling.

---

## `age_gender_probs`

Specifies the **baseline distribution of patient age and sex**.  
By default, these probabilities are derived from *NHS England Hospital Outpatient Activity 2023–24 (Summary Report 3)* [1], which reports outpatient attendances by age and sex.

### Format
**Type:** list or tuple of dictionaries  
**Default:** `DEFAULT_AGE_GENDER_PROBS` stored in `constants.py`  
Each record contains the following keys:
```python
{
    "age_yrs": "15-19",
    "total_female": 0.01738,
    "total_male": 0.01348
}
```

### Validation rules
- Must contain both `"total_female"` and `"total_male"` proportions for each age range.  
- Probabilities must be finite and non-negative.  
- Values are normalized internally to ensure that total female + total male = 1.0 across all age groups.  
- If unspecified, the NHS-derived default is applied.

### How it works
During patient generation, ages are sampled proportionally to these probabilities, ensuring that the simulated cohort mirrors real-world demographic patterns observed in NHS outpatient services.

The distribution reflects adult outpatient activity (ages 15+) and is truncated according to the lower and upper cutoffs defined below.  
These values serve as statistical weights, not deterministic constraints, allowing for reproducible yet probabilistic cohort creation.

> **Note on gender representation:**  
> The NHS source data aggregates attendances by binary sex ("Male" and "Female").  
> The simulator inherits this binary structure for reproducibility.  
> Expanding to more inclusive gender representations would require access to disaggregated datasets not currently available in the NHS open data.

---

## `bin_size`

Defines the **size of age intervals** (in years) used for cohort grouping and reporting.

### Format
**Type:** int  
**Default:** `5`  
**Typical range:** 1–10  

### Validation rules
- Must be a positive integer.  
- Determines the resolution of derived age groups (e.g., `15–19`, `20–24`, etc.).  
- Does not affect raw sampling but controls how aggregated outputs (e.g., charts or summaries) are labeled.

### How it works
The `bin_size` parameter is applied during post-processing to group patient ages into standard reporting intervals.  
It supports downstream analytics and visualization without modifying the underlying patient-level data.

---

## `lower_cutoff` and `upper_cutoff`

Define the **minimum and maximum age limits** of the simulated cohort.  
These parameters constrain age sampling and ensure consistency with the outpatient focus of the dataset.

### Format
**Type:** int  
**Defaults:**  
- `lower_cutoff = 15`  
- `upper_cutoff = 90`  

### Validation rules
- Both values must be integers.  
- `lower_cutoff` must be strictly less than `upper_cutoff`.  
- Typical adult outpatient settings exclude children under 15.  
- Patients above 90 years are grouped into a “90+” category.

### How it works
- Ages below the lower cutoff are excluded entirely when `truncated=True`.  
- Ages above the upper cutoff are included but reported as part of a capped “90+” group for demographic aggregation.  
- This configuration ensures that the simulated dataset remains focused on adult populations, as per NHS reporting conventions.

---

## `truncated`

Controls whether ages outside the defined range are excluded or capped.

### Format
**Type:** bool  
**Default:** `True`  

### Validation rules
- Must be a boolean (`True` or `False`).  
- When `True`, age sampling strictly enforces the lower and upper cutoffs.  
- When `False`, rare outliers may be included but adjusted statistically.

### How it works
When truncation is enabled, the generator filters out ages below 15 before sampling and redistributes their probability mass among valid bins.  
This behavior ensures that pediatric cases are not simulated unless explicitly allowed by the user.

---

### Demographic attributes in generated tables

- The fields **`sex`** and **`dob`** (date of birth) are stored in the **`patients`** table.  
- The fields **`age`** and **`age_group`** are calculated dynamically in the **`appointments`** table based on appointment date and `dob`.  
- This design preserves normalization while supporting age-based analysis directly from appointment-level data.

> **Note on date of birth:**  
> Each patient’s `dob` is reverse-engineered from their sampled age at the first appointment, with a random offset (0–364 days) to avoid clustering.  
> This allows `age` to evolve consistently across appointments, maintaining temporal coherence.

---

### References

[1] NHS England (2024). *Hospital Outpatient Activity 2023–24: Summary Report 3.*  
[https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx](https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx)

---
### Next steps
- Explore {doc}`appointment_timing` to learn how punctuality and durations vary across demographics.  
- Review {doc}`patients_table` to examine how demographic attributes are embedded.  
- See {doc}`patient_flow` for how demographics interact with visit frequency and first attendances.



