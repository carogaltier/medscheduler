# Medscheduler

**Medscheduler** is a Python library for generating fully synthetic outpatient scheduling datasets.  
It provides realistic yet non-identifiable data for **education**, **research**, and **prototyping**, enabling the exploration of healthcare operations without privacy risks.

## Introduction

Access to real-world healthcare data is often limited by privacy regulations, ethical restrictions, and administrative barriers.  
Because most clinical records contain identifiable or sensitive information, researchers and educators must navigate complex approval processes that can delay innovation and hinder reproducibility.

**Synthetic data** offer a practical solution. They are artificially generated datasets that reproduce the statistical structure of real-world data without including identifiable patient information.  
**Medscheduler** simulates outpatient appointment activity through a parameterized scheduler that reproduces plausible demographic distributions, booking behaviors, and attendance patterns.  
Default configurations are informed by **NHS England outpatient statistics** and peer-reviewed research on punctuality, rebooking, and visit frequency.

## Key features and use cases

- End-to-end synthetic scheduling pipeline (slots, patients, appointments).  
- Configurable parameters for calendars, slot density, fill rates, rebooking, attendance, and punctuality.  
- Safe for sharing — fully synthetic and privacy-preserving.  
- Ready for analytics and visualization with pandas and matplotlib.  
- Suitable for:  
  - **Education and training** in health data science and operational analytics.  
  - **Prototyping and experimentation** with scheduling algorithms, dashboards, and predictive models.  
  - **Open and reproducible research** without the constraints of restricted datasets. 

## Simulation overview

The generator models a synthetic outpatient scheduling system with three core components:

- **Slots** — Configurable daily calendars with working days, operating hours, and slot density.  
- **Patients** — Synthetic registry with realistic age-sex distributions derived from NHS data.  
- **Appointments** — Booked appointments linking patients to slots with probabilistic attendance, cancellations, and rebooking outcomes.

Outputs are returned as **pandas DataFrames**, with optional CSV export.



## User Guide

The User Guide introduces the main concepts of **medscheduler**. It provides step-by-step instructions
to install the library, run a quickstart example, and explore the generated outputs. This section also
explains key configuration parameters and how to adapt the scheduler to different teaching or research contexts.

```{toctree}
:maxdepth: 2

user-guide/index
```

## API Reference

The API Reference is the technical specification of the package. It contains detailed documentation of
the `AppointmentScheduler` class, its constructor arguments, and all public methods. Utility modules and
constants are also documented here, serving as a complete reference for developers who need fine-grained control.

```{toctree}
:maxdepth: 2

api-reference/index
```

## Visualization

The Visualization section focuses on functions that help analyze and display the generated data. It shows how
to produce plots of slot availability, patient demographics, and appointment outcomes. These visualizations are
useful for dashboards, teaching, and exploratory data analysis.

```{toctree}
:maxdepth: 2

visualization/index
```

## Examples

The Examples section demonstrates practical scenarios using **medscheduler**. Each example includes code snippets,
expected outputs, and guidance on interpreting results. Topics include attendance analysis, cancellations,
overbooking strategies, and integration with analytics tools.

```{toctree}
:maxdepth: 2

examples/index
```
