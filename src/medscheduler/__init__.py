"""medscheduler
Synthetic outpatient scheduling dataset generator.

Public API
----------
- AppointmentScheduler: core engine to generate realistic `slots`, `patients`,
  and `appointments` tables with attendance and punctuality outcomes.

Quickstart
----------
>>> from medscheduler import AppointmentScheduler
>>> sched = AppointmentScheduler(random_state=42)
>>> slots_df, appointments_df, patients_df = sched.generate()
>>> # sched.to_csv("slots.csv", "patients.csv", "appointments.csv")

Notes
-----
- Visualization utilities live under `medscheduler.utils.plotting` (optional extra: `pip install medscheduler[viz]`).
- Reference data helpers live under `medscheduler.utils.reference_data_utils`.
"""

from __future__ import annotations

from typing import Final, Tuple
from importlib.metadata import PackageNotFoundError, version as pkg_version

from .scheduler import AppointmentScheduler
from .constants import (
    DEFAULT_AGE_GENDER_PROBS,
    DEFAULT_FIRST_ATTENDANCE_RATIO,
    DEFAULT_MONTH_WEIGHTS,
    DEFAULT_STATUS_RATES,
    DEFAULT_WEEKDAY_WEIGHTS,
    STATUS_KEYS,
    validate_defaults,
)

__all__: Final[Tuple[str, ...]] = (
    "AppointmentScheduler",
    "DEFAULT_AGE_GENDER_PROBS",
    "DEFAULT_FIRST_ATTENDANCE_RATIO",
    "DEFAULT_MONTH_WEIGHTS",
    "DEFAULT_STATUS_RATES",
    "DEFAULT_WEEKDAY_WEIGHTS",
    "STATUS_KEYS",
    "validate_defaults",
    "__version__",
)

try:
    __version__ = pkg_version("medscheduler")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"