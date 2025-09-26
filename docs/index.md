# Medscheduler

**Medscheduler** is a Python library for generating synthetic outpatient scheduling datasets.  
It creates realistic but fully synthetic data for teaching, dashboards and prototyping without privacy concerns.

The library simulates three main components:

- **Slots**: configurable appointment calendars (days, hours, and density).  
- **Patients**: synthetic registry with realistic age–sex distribution.  
- **Appointments**: the main table linking slots and patients with attendance outcomes.

Outputs are returned as pandas DataFrames, with optional CSV export.

## Key features

- Synthetic scheduling pipeline: slots, patients, and appointments.  
- Configurable: working days, hours, slot density, attendance rates, cancellations, rebooking.  
- Safe for sharing: fully synthetic, no real patient data.  
- Analytics ready: integration with pandas and visualization helpers.  

---

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
