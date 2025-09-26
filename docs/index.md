```{image} _static/logo.png
:alt: Medscheduler logo
:align: center
:width: 220px
```

# Medscheduler

**Medscheduler** is a Python library for generating synthetic outpatient scheduling datasets.  
It creates realistic but fully synthetic data for teaching, dashboards, prototyping, and research, without privacy concerns.

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

Conceptual and practical documentation for new users.  
Covers installation, quickstart, outputs, and customization options.

```{toctree}
:caption: User Guide
:maxdepth: 2

user-guide/index
```

## API Reference

Technical documentation of all classes, methods, and constants.  
Includes the `AppointmentScheduler` class and utility modules.

```{toctree}
:caption: API Reference
:maxdepth: 2

api-reference/index
```

## Visualization

Plotting and analysis helpers for exploring synthetic scheduling data.  
Shows how to generate charts for slots, patients, and appointments.

```{toctree}
:caption: Visualization
:maxdepth: 2

visualization/index
```

## Examples

Applied scenarios showing how to use medscheduler in practice.  
Includes code samples with inputs and expected outputs.

```{toctree}
:caption: Examples
:maxdepth: 2

examples/index
```
