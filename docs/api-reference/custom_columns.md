# Adding custom columns

The **`AppointmentScheduler`** class supports extending the synthetic dataset with **custom categorical variables**, allowing you to model additional patient attributes such as insurance type, region, provider group, or socioeconomic category.

This feature makes the dataset more flexible and adaptable to different simulation or research contexts without modifying the core generation pipeline.

---

## Overview

After running `generate()`, you can call  
```python
scheduler.add_custom_column()
```  
to append a new column to the **`patients_df`** table.

Each column is created by sampling from a **user-defined set of categories** according to one of three probability models — *normal*, *uniform*, or *Pareto* — or from custom probabilities supplied directly.

---

## Function signature

```python
add_custom_column(
    column_name: str,
    categories: List[str],
    *,
    distribution_type: str = "normal",
    custom_probs: Optional[List[float]] = None
) -> None
```

---

## Parameters

| Parameter | Type | Description |
|------------|------|-------------|
| **`column_name`** | `str` | Name of the new column to add to `patients_df`. Must not duplicate existing columns. |
| **`categories`** | `list[str]` | Category labels to sample from (e.g., `["Public", "Private"]`). |
| **`distribution_type`** | `{"normal", "uniform", "pareto"}` | Defines how probabilities are assigned when no explicit vector is given. Default = `"normal"`. |
| **`custom_probs`** | `list[float]`, optional | User-specified probability vector matching `categories`. Must sum approximately to 1. |

---

## Distribution models

The sampling probabilities can be generated automatically using one of the following internal methods:

| Distribution | Function | Behavior |
|---------------|-----------|-----------|
| **Normal** | `_normal_distribution()` | Creates a bell-shaped distribution centered on middle categories. Suitable for variables with a most common group (default). |
| **Uniform** | `_uniform_distribution()` | Assigns nearly equal probability to all categories, with light noise. Useful for balanced attributes. |
| **Pareto** | `_pareto_distribution()` | Generates a heavy-tailed distribution where the first category dominates. Models skewed real-world variables such as provider caseload or insurance concentration. |

All three functions include a small multiplicative **noise factor** (`±noise`, default 10%) to prevent deterministic sampling.

---

## Behavior and validation

- `patients_df` **must already be populated** — you must call `generate()` before adding custom columns.  
- The column name cannot already exist in the table.  
- If `custom_probs` is provided:
  - Its length must match the number of categories.
  - Values must be positive and sum to a finite, nonzero total.  
- If no custom probabilities are supplied, the probabilities are generated using the selected `distribution_type`.  
- The column is added directly to `patients_df`, making it available for analysis or joins.

---

## Examples

### Example 1 – Uniform distribution
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(seed=42)
sched.generate()

sched.add_custom_column(
    column_name="insurance_type",
    categories=["Public", "Private"],
    distribution_type="uniform"
)

print(sched.patients_df[["patient_id", "insurance_type"]].head())
```

### Example 2 – Normal distribution with more categories
```python
sched.add_custom_column(
    column_name="region",
    categories=["North", "Center", "South"],
    distribution_type="normal"
)
```

### Example 3 – Custom probabilities
```python
sched.add_custom_column(
    column_name="clinic_branch",
    categories=["A", "B", "C"],
    custom_probs=[0.6, 0.3, 0.1]
)
```

---

## Practical applications

Adding custom columns is particularly useful for:
- Simulating heterogeneous service providers or regional health centers.  
- Creating patient segmentation variables for dashboards.  
- Building realistic mock data for machine learning or visualization demos.  
- Introducing controlled bias or imbalance in training datasets.

Each column is generated deterministically under the same random `seed`, ensuring **reproducibility** across runs.

---

## Related parameters

| Parameter | Description | Reference |
|------------|-------------|------------|
| `noise` | Controls randomness intensity when generating probability vectors. | {doc}`randomness_and_noise` |
| `seed` | Ensures reproducibility of all random draws. | {doc}`randomness_and_noise` |
| `patients_df` | Target table where columns are added. | {doc}`patients_table` |

---

### Next steps
- Review {doc}`patients_table` to examine the base table where new columns are added.  
- Explore {doc}`slots_table` to see how patient-level extensions integrate with scheduling data.  
- Learn more in {doc}`randomness_and_noise` about how sampling variability affects these custom features.
