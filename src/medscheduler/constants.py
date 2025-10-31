"""
Default constants for medscheduler.

These NHS-derived defaults parameterize the generation of synthetic
outpatient datasets (age–sex distribution, appointment outcome rates,
and seasonality by weekday/month). They are used by `AppointmentScheduler`
but can be overridden by users at instantiation.

Data sources
------------
1) NHS Hospital Outpatient Activity 2023–24 (Workbook; Hospital Episode Statistics).
   - Sheet names used in parsing (see `utils/reference_data_utils.py`):
       * "Summary Report 1" → status rates
       * "Summary Report 2" → first‑attendance ratio
       * "Summary Report 3" → age × sex proportions
   - URL: https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx

2) NHS Provisional Monthly HES Open Data (Totals) CSV.
   - Columns used: CALENDAR_MONTH_END_DATE, Outpatient_Total_Appointments
   - URL: https://files.digital.nhs.uk/57/C50E24/HES_M1_OPEN_DATA.csv

Notes
-----
- Values are stored here to avoid runtime I/O and keep the package self-contained.
- Weekday and month weights are normalized so that their mean is ~1.0.
- See `utils/reference_data_utils.py` for reproducible derivation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Literal, Mapping, TypedDict

# ---------------------------------------------------------------------------
# Typed structures
# ---------------------------------------------------------------------------

class AgeGenderProb(TypedDict):
    """Age–sex proportion for a specific age group."""
    age_yrs: str
    total_female: float
    total_male: float


StatusKey = Literal["attended", "cancelled", "did not attend", "unknown"]
StatusRates = Mapping[StatusKey, float]

# Exported canonical set of status keys (useful for validation/UI).
STATUS_KEYS: Final[tuple[StatusKey, ...]] = (
    "attended",
    "cancelled",
    "did not attend",
    "unknown",
)

# ---------------------------------------------------------------------------
# Age–sex distribution (normalized proportions).
# Derived from NHS outpatient datasets (2023–24).
# Stored as an immutable tuple of TypedDicts to retain order and prevent mutation.
# ---------------------------------------------------------------------------

DEFAULT_AGE_GENDER_PROBS: Final[tuple[AgeGenderProb, ...]] = (
    {"age_yrs": "0-4", "total_female": 0.01413, "total_male": 0.01794},
    {"age_yrs": "5-9", "total_female": 0.01140, "total_male": 0.01409},
    {"age_yrs": "10-14", "total_female": 0.01318, "total_male": 0.01459},
    {"age_yrs": "15-19", "total_female": 0.01738, "total_male": 0.01348},
    {"age_yrs": "20-24", "total_female": 0.02326, "total_male": 0.01010},
    {"age_yrs": "25-29", "total_female": 0.03988, "total_male": 0.01208},
    {"age_yrs": "30-34", "total_female": 0.05164, "total_male": 0.01449},
    {"age_yrs": "35-39", "total_female": 0.04369, "total_male": 0.01591},
    {"age_yrs": "40-44", "total_female": 0.03240, "total_male": 0.01754},
    {"age_yrs": "45-49", "total_female": 0.02902, "total_male": 0.01861},
    {"age_yrs": "50-54", "total_female": 0.03684, "total_male": 0.02513},
    {"age_yrs": "55-59", "total_female": 0.04172, "total_male": 0.03249},
    {"age_yrs": "60-64", "total_female": 0.04188, "total_male": 0.03723},
    {"age_yrs": "65-69", "total_female": 0.03939, "total_male": 0.03822},
    {"age_yrs": "70-74", "total_female": 0.04026, "total_male": 0.03995},
    {"age_yrs": "75-79", "total_female": 0.04395, "total_male": 0.04334},
    {"age_yrs": "80-84", "total_female": 0.03090, "total_male": 0.02876},
    {"age_yrs": "85-89", "total_female": 0.02015, "total_male": 0.01745},
    {"age_yrs": "90+", "total_female": 0.01040, "total_male": 0.00716},
)

# ---------------------------------------------------------------------------
# First‑attendance ratio (scalar).
# ---------------------------------------------------------------------------

DEFAULT_FIRST_ATTENDANCE_RATIO: Final[float] = 0.325

# ---------------------------------------------------------------------------
# Appointment outcome probabilities for past appointments.
# Exposed as an immutable Mapping to prevent accidental mutation.
# ---------------------------------------------------------------------------

_DEFAULT_STATUS_RATES_DICT = {
    "attended": 0.773,
    "cancelled": 0.164,
    "did not attend": 0.059,
    "unknown": 0.004,
}
DEFAULT_STATUS_RATES: Final[StatusRates] = MappingProxyType(_DEFAULT_STATUS_RATES_DICT)

# ---------------------------------------------------------------------------
# Relative appointment distribution by month (Jan=1..Dec=12), mean weight ≈ 1.0.
# Exposed as immutable Mapping[int, float].
# ---------------------------------------------------------------------------

_DEFAULT_MONTH_WEIGHTS_DICT: dict[int, float] = {
    1: 1.092,   # Jan
    2: 1.026,   # Feb
    3: 0.990,   # Mar
    4: 0.865,   # Apr
    5: 0.998,   # May
    6: 1.035,   # Jun
    7: 0.984,   # Jul
    8: 0.994,   # Aug
    9: 0.993,   # Sep
    10: 1.055,  # Oct
    11: 1.082,  # Nov
    12: 0.887,  # Dec
}
DEFAULT_MONTH_WEIGHTS: Final[Mapping[int, float]] = MappingProxyType(_DEFAULT_MONTH_WEIGHTS_DICT)

# ---------------------------------------------------------------------------
# Relative appointment distribution by weekday (Mon=0..Sun=6), mean weight ≈ 1.0.
# Exposed as immutable Mapping[int, float].
# ---------------------------------------------------------------------------

_DEFAULT_WEEKDAY_WEIGHTS_DICT: dict[int, float] = {
    0: 1.198,  # Monday
    1: 1.277,  # Tuesday
    2: 1.185,  # Wednesday
    3: 1.099,  # Thursday
    4: 0.764,  # Friday
    5: 0.791,  # Saturday
    6: 0.686,  # Sunday
}
DEFAULT_WEEKDAY_WEIGHTS: Final[Mapping[int, float]] = MappingProxyType(_DEFAULT_WEEKDAY_WEIGHTS_DICT)

# ---------------------------------------------------------------------------
# Package-wide operational constants
# ---------------------------------------------------------------------------

#: Allowed values for number of appointments per hour (must divide 60 evenly).
VALID_APPTS_PER_HOUR: Final[tuple[int, ...]] = (1, 2, 3, 4, 6)

#: Default working days: Monday (0) to Friday (4).
DEFAULT_WORKING_DAYS: Final[tuple[int, ...]] = (0, 1, 2, 3, 4)

#: Bounds for average check-in time (minutes relative to appointment).
#: Negative values mean early arrival, positive mean late arrival.
CHECK_IN_MIN_MAX: Final[tuple[int, int]] = (-60, 30)

#: Minimum reasonable standard deviation (minutes) for check-in distribution.
CHECK_IN_STD_MIN: Final[float] = 9.8

#: Reasonable maximum number of outpatient visits per patient per year.
MAX_VISITS_PER_YEAR: Final[float] = 12.0

#: Maximum allowed bin size for grouping ages (prevents overly coarse bins).
MAX_BIN_SIZE: Final[int] = 20

MIN_FILL_RATE: Final[float] = 0.30

# ---------------------------------------------------------------------------
# Optional validation helper (import-safe, no side effects by default)
# ---------------------------------------------------------------------------

def validate_defaults(*, strict: bool = False) -> None:
    """
    Validate structural and probabilistic invariants of default constants.

    Parameters
    ----------
    strict : bool, default False
        If True, raise ValueError on failures; otherwise do silent checks
        (no exceptions). Designed for unit tests / CI.

    Checks
    ------
    - Status keys match `STATUS_KEYS` and probabilities sum to ~1.
    - Month and weekday weights have mean ~1.0.
    - Age–sex proportions sum to ~1 across all groups.
    """
    def _fail(msg: str) -> None:
        if strict:
            raise ValueError(msg)

    # Status rates
    if tuple(DEFAULT_STATUS_RATES.keys()) != STATUS_KEYS:
        _fail("Status keys differ from canonical STATUS_KEYS.")
    total_status = sum(DEFAULT_STATUS_RATES.values())
    if not (0.995 <= total_status <= 1.005):
        _fail(f"Status rates must sum ~1. Got {total_status:.6f}")

    # Month weights: mean ~1.0
    mean_month = sum(DEFAULT_MONTH_WEIGHTS.values()) / len(DEFAULT_MONTH_WEIGHTS)
    if not (0.995 <= mean_month <= 1.005):
        _fail(f"Mean month weight must be ~1. Got {mean_month:.6f}")

    # Weekday weights: mean ~1.0
    mean_weekday = sum(DEFAULT_WEEKDAY_WEIGHTS.values()) / len(DEFAULT_WEEKDAY_WEIGHTS)
    if not (0.995 <= mean_weekday <= 1.005):
        _fail(f"Mean weekday weight must be ~1. Got {mean_weekday:.6f}")

    # Age–sex proportions: sum ~1 (female and male separately)
    female_sum = sum(row["total_female"] for row in DEFAULT_AGE_GENDER_PROBS)
    male_sum = sum(row["total_male"] for row in DEFAULT_AGE_GENDER_PROBS)
    if not (0.495 <= female_sum <= 0.505) or not (0.495 <= male_sum <= 0.505):
        _fail(
            "Age–sex totals must sum ~1 (separately for female/male). "
            f"Got female={female_sum:.6f}, male={male_sum:.6f}"
        )

# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__: Final[tuple[str, ...]] = (
    # types
    "AgeGenderProb",
    "StatusKey",
    "StatusRates",
    # keys and defaults
    "STATUS_KEYS",
    "DEFAULT_AGE_GENDER_PROBS",
    "DEFAULT_FIRST_ATTENDANCE_RATIO",
    "DEFAULT_STATUS_RATES",
    "DEFAULT_MONTH_WEIGHTS",
    "DEFAULT_WEEKDAY_WEIGHTS",
    # operational constants 
    "VALID_APPTS_PER_HOUR",
    "DEFAULT_WORKING_DAYS",
    "CHECK_IN_MIN_MAX",
    "CHECK_IN_STD_MIN",
    "MAX_VISITS_PER_YEAR",
    "MAX_BIN_SIZE",
    "MIN_FILL_RATE",
    # helpers
    "validate_defaults",
)
