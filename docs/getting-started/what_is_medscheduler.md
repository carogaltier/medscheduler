# What is medscheduler?

**medscheduler** is a Python library that generates **synthetic outpatient scheduling data** suitable for
education, dashboards and experimentation **without** privacy risks.

It simulates three components and returns them as pandas DataFrames (and optional CSV export):

- **appointments**: the **main** table with everything most users need (identifiers, scheduling fields,
  outcomes, demographics, and attended‑visit timing).
- **slots**: the calendar capacity (working days/hours and slot density) with availability.
- **patients**: a synthetic registry used to populate the appointments table.

## Key capabilities

- **Configurable calendars (slots):** working days (Mon–Sun), working hour blocks, and slot density
  via `appointments_per_hour`.
- **Patient cohort:** realistic **age–sex** distributions (derived from public NHS statistics) that you can
  override at instantiation time.
- **Outcomes & behavior:** probabilistic **attendance**, **cancellations**, **no‑shows**, iterative **rebooking**,
  lead‑time effects, and **arrival punctuality** (check‑in offsets).
- **Stand‑alone usability:** the **appointments** table contains all fields typically required for downstream use.
- **Determinism:** seedable random state for fully reproducible runs.
- **Lightweight:** minimal hard dependencies; plotting utilities are optional.

## Typical use cases

- Teaching analytics (SQL, pandas), data-viz exercises, and BI dashboards  
  (utilization, punctuality, cancellations, waiting time, duration).
- Rapid prototyping of scheduling heuristics or overbooking strategies.
- Demonstrating **ETL pipelines** or database integration with synthetic but realistic healthcare data.
- Practicing **machine learning workflows** on time-series or tabular data without privacy concerns.
- Building **interactive apps or dashboards** to showcase scheduling insights.
- Supporting **academic courses, workshops, or portfolio projects** where real patient data cannot be shared.

## Outputs at a glance

- **appointments** (primary): `appointment_id`, `slot_id`, `patient_id`, `scheduling_date`,
  `scheduling_interval`, `appointment_date`, `appointment_time`, `status`, patient `sex`/`age`/`age_group`,
  and when attended `check_in_time`, `start_time`, `end_time`, `waiting_time`, `appointment_duration`.
- **slots** (auxiliary): `slot_id`, `appointment_date`, `appointment_time`, `is_available`.
- **patients** (auxiliary): `patient_id`, `name` (Faker), `sex`, `age` (or `dob` + `age_group` depending on settings).

> **Note:** Most workflows can rely **only** on the `appointments` table; `slots`/`patients` provide extra detail when
> analyzing capacity or extending patient‑level features.

## Design goals

- **Healthcare‑aware defaults** with clear validation and error messages.
- **PEP‑compliant** code (type hints, docstrings) for maintainability.
- **Reproducibility first**: deterministic reference window and seeds for tests, demos, and papers.
- **Single‑file exports** (`to_csv`) to share datasets across tools and classes.

## Customization highlights

You can override in the constructor:

- **Calendar & density:** `date_ranges`, `working_days`, `working_hours`, `appointments_per_hour`.
- **Booking dynamics:** `fill_rate`, `booking_horizon`, `median_lead_time`, `rebook_category`.
- **Outcomes:** `status_rates` (attended, cancelled, did not attend, unknown).
- **Cohort:** `age_gender_probs`, `bin_size`, `lower_cutoff`, `upper_cutoff`, `truncated`.
- **Punctuality & timing:** `check_in_time_mean` and time‑simulation parameters.
- **Reproducibility:** `seed`, `noise`.

## When to use medscheduler

Choose **medscheduler** when you need a realistic but **fully synthetic** outpatient dataset to teach, demo,
or prototype without accessing PHI/PII. If you need inpatient pathways or multi‑department scheduling,
treat this as a foundation—extend or adapt the generator to your care setting.

## Next steps

- Install the package in **Installation**.
- Generate your first dataset in **Quickstart**.
- Explore advanced parameters and plotting helpers in the Tutorials section.
