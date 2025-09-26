# What is Medscheduler?

**Medscheduler** is a Python library designed to generate **synthetic outpatient scheduling datasets**.  
It allows researchers, educators, and developers to explore realistic healthcare scheduling data while avoiding privacy concerns.  
The package is lightweight, reproducible, and flexible enough for analytics, dashboards, and prototyping workflows.

## Overview

Medscheduler produces three interconnected tables that replicate a typical outpatient scheduling system:

- **Appointments (primary output):** the main table containing identifiers, scheduling fields, patient demographics,
  attendance outcomes, punctuality, and visit timing. It is sufficient for most use cases on its own.
- **Slots (auxiliary):** represents daily calendar capacity, with working days, hours, and slot density. Useful for analyzing utilization.
- **Patients (auxiliary):** a synthetic patient registry with demographics used to populate the appointments table.

Outputs are returned as pandas DataFrames, with optional CSV export for portability.

## Key capabilities

- **Configurable calendars:** define working days, hours, and slot density (`appointments_per_hour`).  
- **Realistic cohorts:** generate patients with age–sex distributions derived from NHS data, or override with your own.  
- **Behavioral simulation:** model attendance, cancellations, no‑shows, rebooking, lead‑time effects, and check‑in punctuality.  
- **Determinism:** seedable random state for reproducible results.  
- **Lightweight:** minimal dependencies, with visualization tools provided as optional utilities.  
- **Stand‑alone usability:** the `appointments` table contains all information needed for downstream analysis.

## Typical use cases

Medscheduler can be applied in diverse scenarios, including:

- Teaching data analytics with SQL or pandas, and building BI dashboards (e.g., punctuality, cancellations, waiting time).  
- Prototyping scheduling heuristics or overbooking strategies.  
- Demonstrating **ETL pipelines** or database integration using synthetic healthcare data.  
- Practicing machine learning workflows on structured, time‑series data without privacy risks.  
- Creating interactive apps or dashboards to showcase healthcare scheduling.  
- Supporting academic courses, workshops, or portfolio projects where real patient data cannot be shared.

## Outputs at a glance

- **Appointments:** `appointment_id`, `slot_id`, `patient_id`, `scheduling_date`, `appointment_date`, `appointment_time`,
  `status`, patient `sex`/`age`/`age_group`, plus when attended: `check_in_time`, `start_time`, `end_time`,
  `waiting_time`, `appointment_duration`.
- **Slots:** `slot_id`, `appointment_date`, `appointment_time`, `is_available`.
- **Patients:** `patient_id`, `name` (Faker), `sex`, `age`, or `dob` with age groupings.

> **Note:** In most workflows, the `appointments` table is sufficient. Use `slots` and `patients` for capacity analysis or when patient‑level detail is needed.

## Design goals

Medscheduler was built with the following principles:

- **Healthcare‑aware defaults:** parameters derived from open NHS datasets and published literature.  
- **Clarity and validation:** helpful error messages for invalid inputs.  
- **Reproducibility:** deterministic defaults with fixed seeds for demos, tests, and publications.  
- **PEP‑compliant design:** type hints, docstrings, and maintainable code style.  
- **Simple exports:** single CSV files for easy sharing across tools.

## Customization highlights

You can control behavior through constructor parameters, such as:

- **Calendar & density:** `date_ranges`, `working_days`, `working_hours`, `appointments_per_hour`.  
- **Booking dynamics:** `fill_rate`, `booking_horizon`, `median_lead_time`, `rebook_category`.  
- **Outcomes:** `status_rates` for attendance, cancellations, no‑shows, unknown.  
- **Cohort:** `age_gender_probs`, `bin_size`, `lower_cutoff`, `upper_cutoff`, `truncated`.  
- **Timing & punctuality:** `check_in_time_mean` and other arrival time parameters.  
- **Reproducibility:** `seed`, `noise`.

## When to use Medscheduler

Use **Medscheduler** whenever you need realistic but synthetic outpatient scheduling data.  
It is particularly useful for teaching, dashboards, demos, or prototyping algorithms without requiring access to protected health information.  
If you need inpatient pathways or multi‑department scheduling, Medscheduler can serve as a foundation to extend or adapt.

## Next steps

- Go to **Installation** to set up the package.  
- Follow the **Quickstart** to generate your first dataset.  
- Explore **Visualization** and **Examples** for advanced workflows and applied scenarios.  
