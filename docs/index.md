# Medscheduler

**Medscheduler** is a Python library for generating fully synthetic outpatient scheduling datasets. It creates realistic yet privacy-preserving data for **education**, **research**, and **prototyping**, enabling healthcare operations analysis without privacy concerns.

## Introduction

Access to real-world healthcare data is often constrained by privacy regulations, ethical considerations, and administrative barriers. Most clinical records contain sensitive or identifiable information, requiring complex approval processes that can hinder innovation and reproducibility.

**Synthetic data** provides a practical alternative - artificially generated datasets that replicate the statistical properties of real-world data while containing no identifiable patient information. **Medscheduler** simulates outpatient appointment systems through a parameterized scheduler that generates plausible demographic distributions, booking behaviors, and attendance patterns. Default configurations are informed by **NHS England outpatient statistics** and peer-reviewed research on punctuality, rebooking, and visit frequency.


## Key features

- End-to-end synthetic scheduling pipeline (slots, patients, appointments)
- Configurable parameters for calendars, slot density, fill rates, rebooking, attendance, and punctuality
- Privacy-preserving by design - safe for sharing and collaboration
- Compatible with pandas and matplotlib for immediate analysis and visualization
- Modular and extensible architecture

## Use cases
- **Education & Training**: Health data science and operational analytics coursework
- **Prototyping & Development**: Testing scheduling algorithms, dashboards, and predictive models
- **Research & Reproducibility**: Open research without data access restrictions
  
## Simulation overview

The generator models a synthetic outpatient scheduling system with three core components:

- **Slots**: Configurable daily calendars with working days, operating hours, and slot density.  
- **Patients**: Synthetic registry with realistic age-sex distributions derived from NHS data.  
- **Appointments**: Booked appointments linking patients to slots with probabilistic attendance, cancellations, and rebooking outcomes.

Outputs are provided as **pandas DataFrames** with optional CSV export functionality. The modular codebase allows for customization of simulation parameters and behavioral assumptions through class arguments or extended methods, supporting adaptation to various healthcare systems and research requirements.

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
