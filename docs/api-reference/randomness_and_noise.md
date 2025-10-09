# Randomness and variability

The parameters **`seed`** and **`noise`** control the stochastic behavior of the scheduler.  
They define how reproducible or variable the generated dataset will be across runs, balancing determinism with realism.

---

## `seed`

Determines the **reproducibility** of all random processes in the scheduler, including NumPy, Python’s built-in `random`, and the Faker library used for synthetic names.

### Format
**Type:** `int` or `None`  
**Default:** `42`  
**Accepted values:** any integer (positive or negative), or `None`

### Validation rules
- Must be an integer or `None`.  
- When set to an integer, all random sources are initialized with the same seed.  
- When `None`, outputs vary at each run.  
- Negative or excessively large integers are valid but discouraged for clarity.

### How it works
At initialization, the scheduler configures a consistent random state:
- NumPy’s `default_rng(seed)`  
- Python’s `random.seed(seed)`  
- Faker’s internal random generator (`self.fake.seed_instance(seed)`)

This ensures that all randomness—patient demographics, slot assignment, rebooking, and durations—is repeatable.  
When `seed=None`, every execution generates new random outcomes, suitable for stochastic experiments.

### Examples

**Reproducible simulation**
```python
from medscheduler import AppointmentScheduler

sched = AppointmentScheduler(seed=42)
sched.generate()
```

**Non-deterministic simulation**
```python
sched = AppointmentScheduler(seed=None)
sched.generate()
```

### Recommended usage
For reproducible results and testing, fix the seed (e.g., `seed=42`).  
To explore scenario variability, omit or randomize the seed between runs.

---

## `noise`

Adds **controlled randomness** to probabilistic processes throughout the simulation.  
It allows small deviations from deterministic baselines, producing more realistic yet statistically stable outcomes.

### Format
**Type:** float  
**Default:** `0.1`  
**Accepted range:** `≥ 0.0`

### Validation rules
- Must be a non-negative float.  
- Values above 0.5 introduce substantial variability and are not recommended for reproducibility.  
- If set to 0.0, all stochastic effects are disabled except those driven by `seed`.

### How it works
The noise parameter acts as a multiplicative perturbation:
\[
x' = x \times U(1 - \text{noise}, 1 + \text{noise})
\]
where \(U(a,b)\) is a uniform random factor applied to intermediate probabilities and scaling operations.

`noise` is applied in several contexts:
- **Patient generation:** adds slight randomness to demographic sampling and visit frequency.  
- **Appointment filling:** modulates local fill rates and lead-time distribution.  
- **Custom distributions:** smooths otherwise uniform probabilities to avoid artifacts.

### Examples

**Deterministic output**
```python
sched = AppointmentScheduler(seed=42, noise=0.0)
```

**Slightly variable simulation**
```python
sched = AppointmentScheduler(seed=42, noise=0.1)
```

**Highly stochastic output**
```python
sched = AppointmentScheduler(seed=None, noise=0.3)
```

### Interpretation
| Noise value | Behavior | Use case |
|--------------|-----------|----------|
| 0.0 | Fully deterministic | Unit testing, reproducible examples |
| 0.1 | Realistic variability | Default educational setting |
| 0.3 | Strong heterogeneity | Scenario simulation, Monte Carlo |

---

### Next steps

- {doc}`appointments_table` — shows how stochastic variability influences the generated appointment outcomes.  
- {doc}`custom_columns` — demonstrates how the same noise parameter applies when sampling user-defined categorical columns.


