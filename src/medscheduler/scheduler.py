"""
scheduler.py

Synthetic outpatient appointment scheduler.

This module defines the `AppointmentScheduler` class, which simulates realistic
daily appointment slots, patient cohorts, and appointment outcomes. The goal is
to generate fully synthetic but statistically plausible datasets suitable for:

- Teaching and training in healthcare data science
- Building and testing dashboards or scheduling models
- Reproducible research and benchmarking without privacy risks

Key Features
------------
- Configurable daily calendars of bookable slots
- Patient cohort simulation with realistic age–sex distributions
- Appointment allocation with attendance/cancellation/no-show probabilities
- Rebooking behavior and punctuality simulation
- NHS-derived defaults, but all parameters overrideable

The main output is `appointments_df`, a unified table that contains
all key attributes (slot, patient, demographics, appointment outcome),
while `slots_df` and `patients_df` serve as auxiliary tables.
"""

from __future__ import annotations

import logging
import math
import random
import warnings
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Iterable
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from faker import Faker
from numpy.random import default_rng

from .constants import (
    DEFAULT_AGE_GENDER_PROBS,
    DEFAULT_FIRST_ATTENDANCE_RATIO,
    DEFAULT_MONTH_WEIGHTS,
    DEFAULT_STATUS_RATES,
    DEFAULT_WEEKDAY_WEIGHTS,
    STATUS_KEYS,
    VALID_APPTS_PER_HOUR,
    DEFAULT_WORKING_DAYS,
    CHECK_IN_MIN_MAX,
    CHECK_IN_STD_MIN,
    MAX_VISITS_PER_YEAR,
    MAX_BIN_SIZE,
    MIN_FILL_RATE
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AppointmentScheduler class
# ---------------------------------------------------------------------------

class AppointmentScheduler:
    """
    Synthetic outpatient appointment scheduler.

    This class generates a full synthetic dataset of appointment slots,
    patients, and appointment outcomes. The primary output `appointments_df`
    is sufficient for most analyses, with `slots_df` and `patients_df`
    provided as auxiliary detail tables.

    Parameters
    ----------
    date_ranges : list[tuple[date-like, date-like]], optional
        List of (start_date, end_date) ranges for available appointment slots.
        Each value may be ISO string "YYYY-MM-DD", datetime.date, datetime.datetime,
        pandas.Timestamp or numpy.datetime64. Internally normalized to naive datetimes.

        Defaults and behavior:
        - If BOTH `date_ranges` and `ref_date` are omitted, a deterministic, reproducible
          window is used: [2024-01-01 00:00, 2024-12-31 23:59].
        - If `date_ranges` is omitted but `ref_date` is supplied, the same deterministic
          window is used (as above), with `ref_date` respected.
        - If `date_ranges` is provided but `ref_date` is omitted, `ref_date` defaults to
          the last day (00:00) of the latest provided range.
        - Non-contiguous ranges are allowed. Each (start, end) must satisfy start < end.
          If `end` is provided at 00:00, it is expanded to 23:59 of that day.

    ref_date : date-like, optional
        Reference date dividing past and future appointments. Accepts ISO "YYYY-MM-DD",
        datetime.date, datetime.datetime, pandas.Timestamp or numpy.datetime64. Internally
        normalized to a naive datetime at 00:00.

        Defaults and validation:
        - If omitted AND `date_ranges` is omitted, defaults to 2024-12-01 00:00
          (for reproducible runs).
        - If omitted AND `date_ranges` is provided, defaults to the last day (00:00)
          of the latest range in `date_ranges`.
        - If provided explicitly, it must lie within at least one of the `date_ranges`;
          otherwise a ValueError is raised.

        Effective window:
        - The end of the latest range is extended, if needed, to ensure it reaches at least
          `ref_date + booking_horizon` (at 23:59). Existing ranges are never shortened.

    working_days : list of int, default (0..4)
        Weekdays when appointments occur (0=Mon, 6=Sun).

    appointments_per_hour : int, default 4
        Number of bookable slots per hour. Must divide 60 evenly.

    working_hours : list[tuple[int, int]] | tuple[int, int] | list[tuple[str, str]] | tuple[str, str], default [(8, 18)]
        Working periods during the day. Each block is (start, end).
        Accepts integer hours (e.g., (8, 16)) or strings "HH" / "HH:MM" with minutes in {00, 30}
        (e.g., ("08:00", "16:00")). Multiple blocks allowed; they must be non-overlapping
        and are automatically sorted.

    fill_rate : float, default 0.9
        Proportion of slots to be filled with appointments. The value must be between 0.3 and 1.0. 
        Values below 0.3 imply implausibly low utilization and are likely to yield unrealistic scheduling behavior.
        The default is `0.9`, meaning 90% of all generated slots are used.

    booking_horizon : int, default 30
        Maximum number of days into the future that can be booked. Used to extend
        the end of the latest range in `date_ranges` to at least `ref_date + booking_horizon`.

    median_lead_time : int, default 10
        Median lead time (days between scheduling and appointment).

    status_rates : dict, default NHS-derived
        Outcome probabilities for past appointments.

    rebook_category : {"min","med","max"}, default "med"
        Intensity of rebooking behavior.

    check_in_time_mean : float, default -10
        Average patient arrival offset (minutes relative to appointment time).

    visits_per_year : float, default 1.2
        Average visits per patient per year.

    first_attendance : float, default 0.325
        Proportion of first attendances among all visits.

    bin_size : int, default 5
        Size of age bins for cohort simulation.

    lower_cutoff : int, default 15
        Minimum age for included patients.

    upper_cutoff : int, default 90
        Maximum age for included patients.

    truncated : bool, default True
        Whether to truncate ages outside cutoffs.

    seed : int, optional
        Random seed for reproducibility.

    noise : float, default 0.1
        Random noise factor for patient age distribution.

    Attributes
    ----------
    slots_df : pd.DataFrame
        Auxiliary table of appointment slots.
    appointments_df : pd.DataFrame
        Main table of appointments, with demographics and outcomes.
    patients_df : pd.DataFrame
        Auxiliary table of patient registry.

    Notes
    -----
    - All date-like inputs are parsed to naive `datetime` (timezone information is dropped).
    - `working_hours` minutes are restricted to {00, 30} by design; extend the parser
      cautiously if you need finer granularity.
    - The effective calendar window is the union of `date_ranges` with an extension
      on the latest range’s end to satisfy `ref_date + booking_horizon` when necessary.
    """

    # -----------------------------------------------------------------------
    # Internal validation helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _to_datetime(value: Union[str, date, datetime, pd.Timestamp, np.datetime64]) -> datetime:
        """Parse many date-like inputs into a naive `datetime.datetime` (no tz)."""
        try:
            ts = pd.to_datetime(value)
        except Exception as exc:
            raise TypeError(f"Invalid date-like value {value!r} of type {type(value)}") from exc

        # Convert to Python datetime
        if isinstance(ts, pd.Timestamp):
            dt = ts.to_pydatetime()
        elif isinstance(ts, np.datetime64):
            dt = pd.Timestamp(ts).to_pydatetime()
        elif isinstance(ts, datetime):
            dt = ts
        elif isinstance(ts, date):
            dt = datetime.combine(ts, time(0, 0))
        else:
            raise TypeError(f"Could not convert {value!r} to datetime")

        # Enforce naive (drop tz if present)
        if dt.tzinfo is not None:
            dt = dt.astimezone(tz=None).replace(tzinfo=None)
        return dt

    @staticmethod
    def _normalize_range(
        start: "Union[str, date, datetime, pd.Timestamp, np.datetime64]",
        end:   "Union[str, date, datetime, pd.Timestamp, np.datetime64]"
    ) -> tuple[datetime, datetime]:
        """
        Normalize (start, end) into valid naive datetimes.

        Rules
        -----
        - If `end` has time 00:00 (e.g., '2025-01-31'), expand it to 23:59 of that day.
        - For same-day ranges where both start and end are at midnight, expand the end to 23:59.
        - Validate that start < end; otherwise raise ValueError.
        """
        s = AppointmentScheduler._to_datetime(start)
        e = AppointmentScheduler._to_datetime(end)

        if e.time() == time(0, 0):
            e = e.replace(hour=23, minute=59)
        if s.date() == e.date() and s.time() == time(0, 0) and e.time() == time(23, 59):
            pass  # same-day midnight-to-end expansion already applied

        if s >= e:
            raise ValueError(f"Invalid date range: start >= end ({s} >= {e}).")
        return s, e

    @staticmethod
    def _parse_time_like(x: Union[int, str]) -> tuple[int, int]:
        """
        Parse a time-like value into (hour, minute).
        Accepts:
        - int hour in [0..23]           -> (hour, 0)
        - str "HH"                      -> (hour, 0)
        - str "HH:MM" with MM in {00,30}
        """
        if isinstance(x, int):
            if 0 <= x <= 23:
                return x, 0
            raise ValueError(f"Hour out of range (0..23): {x}")

        if isinstance(x, str):
            s = x.strip()
            if ":" not in s:
                # "HH"
                try:
                    h = int(s)
                except Exception as exc:
                    raise ValueError(f"Invalid hour string {x!r}") from exc
                if 0 <= h <= 23:
                    return h, 0
                raise ValueError(f"Hour out of range (0..23): {x}")

            # "HH:MM"
            parts = s.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid time string {x!r}; expected 'HH' or 'HH:MM'")
            try:
                h = int(parts[0])
                m = int(parts[1])
            except Exception as exc:
                raise ValueError(f"Invalid time string {x!r}; expected 'HH:MM'") from exc

            if not (0 <= h <= 23):
                raise ValueError(f"Hour out of range (0..23): {x}")
            if m not in (0, 30):
                raise ValueError(
                    f"Minutes must be 00 or 30 (got {m:02d}) in {x!r}. "
                    "If you need other minute values, extend the parser safely."
                )
            return h, m

        raise TypeError(f"Unsupported time-like type: {type(x)} for value {x!r}")

    @staticmethod
    def _normalize_working_blocks_min(
        value: Union[None, tuple, list, Iterable[tuple]]
    ) -> list[tuple[int, int]]:
        """
        Normalize working_hours into a sorted, non-overlapping list of (start_min, end_min),
        where each item is the minute offset from midnight [0..1440], with minutes in {0,30}.

        Accepts:
        - None                    -> default [(8:00, 18:00)]
        - (start, end)
        - [(start, end), ...]
        Each start/end can be:
        - int hour (0..23)
        - str "HH" or "HH:MM" with MM in {00,30}.
        """
        if value is None:
            return [(8 * 60, 18 * 60)]

        if isinstance(value, tuple):
            value = [value]

        if not isinstance(value, Iterable):
            raise TypeError("`working_hours` must be a tuple or a list of (start, end) tuples.")

        blocks: list[tuple[int, int]] = []
        for i, block in enumerate(value):
            if not (isinstance(block, (tuple, list)) and len(block) == 2):
                raise TypeError(f"`working_hours[{i}]` must be a (start, end) tuple, got {block!r}")
            start_raw, end_raw = block
            sh, sm = AppointmentScheduler._parse_time_like(start_raw)
            eh, em = AppointmentScheduler._parse_time_like(end_raw)
            s_min = sh * 60 + sm
            e_min = eh * 60 + em
            if s_min >= e_min:
                raise ValueError(
                    f"`working_hours[{i}]` invalid interval: start >= end ({sh:02d}:{sm:02d} >= {eh:02d}:{em:02d})"
                )
            blocks.append((s_min, e_min))

        # sort and check overlaps
        blocks.sort(key=lambda x: x[0])
        for j in range(1, len(blocks)):
            prev = blocks[j - 1]
            cur = blocks[j]
            if cur[0] < prev[1]:
                raise ValueError(
                    f"`working_hours` blocks overlap: "
                    f"{prev[0]//60:02d}:{prev[0]%60:02d}-{prev[1]//60:02d}:{prev[1]%60:02d} and "
                    f"{cur[0]//60:02d}:{cur[0]%60:02d}-{cur[1]//60:02d}:{cur[1]%60:02d}. "
                    "Please provide non-overlapping intervals."
                )

        return blocks

    @staticmethod
    def _extend_last_range(
        ranges: "list[tuple[datetime, datetime]]",
        extra_days: int
    ) -> "list[tuple[datetime, datetime]]":
        """
        Return a copy of `ranges` extending ONLY the latest range end
        (the one with the maximum `end` value) by `extra_days` days.

        If `extra_days <= 0`, the ranges are returned unchanged.
        """
        if not ranges or extra_days <= 0:
            return list(ranges)

        out = list(ranges)
        last_idx = max(range(len(out)), key=lambda i: out[i][1])
        s, e = out[last_idx]
        out[last_idx] = (s, e + timedelta(days=extra_days))
        return out

    def _validate_appointments_per_hour(self, value: int) -> int:
        """Validate `appointments_per_hour` against allowed discrete densities."""
        if not isinstance(value, int) or value not in VALID_APPTS_PER_HOUR:
            raise ValueError(
                f"`appointments_per_hour` must be one of {VALID_APPTS_PER_HOUR}. "
                "These values divide 60 minutes evenly."
            )
        return value

    def _validate_check_in_time_mean(self, mean_minutes: float) -> float:
        """Validate average check-in offset within configured bounds."""
        min_mean, max_mean = CHECK_IN_MIN_MAX
        if not isinstance(mean_minutes, (int, float)) or not (min_mean <= mean_minutes <= max_mean):
            raise ValueError(
                f"`check_in_time_mean` must be between {min_mean} and {max_mean} minutes. "
                "Negative values mean patients typically arrive early."
            )
        return float(mean_minutes)

    @property
    def slot_duration_min(self) -> int:
        """Return slot duration in minutes derived from `appointments_per_hour`."""
        return 60 // self.appointments_per_hour

    @staticmethod
    def _end_of_day(dt: datetime) -> datetime:
        """Return `dt` with time set to 23:59 (seconds and micros zeroed)."""
        return dt.replace(hour=23, minute=59, second=0, microsecond=0)

    @staticmethod
    def _extend_latest_end_to(
        ranges: "list[tuple[datetime, datetime]]",
        min_end_dt: datetime
    ) -> "list[tuple[datetime, datetime]]":
        """
        Return a copy of `ranges` ensuring the latest range end is at least `min_end_dt`.
        - Only the range with the maximum `end` is considered/possibly extended.
        - Ranges are NEVER shortened.
        """
        if not ranges:
            return []

        out = list(ranges)
        last_idx = max(range(len(out)), key=lambda i: out[i][1])
        s, e = out[last_idx]
        if e < min_end_dt:
            out[last_idx] = (s, min_end_dt)
        return out



    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------

    def __init__(
        self,
        date_ranges: Optional[List[Tuple[datetime, datetime]]] = None,
        ref_date: Optional[datetime] = None,
        working_days: Optional[List[int]] = None,
        appointments_per_hour: int = 4,
        working_hours: Optional[List[Tuple[int, int]]] = None,
        fill_rate: float = 0.9,
        booking_horizon: int = 30,
        median_lead_time: int = 10,
        status_rates: Optional[Dict[str, float]] = None,
        rebook_category: str = "med",
        check_in_time_mean: float = -10.0,
        visits_per_year: float = 1.2,
        first_attendance: float = DEFAULT_FIRST_ATTENDANCE_RATIO,
        bin_size: int = 5,
        lower_cutoff: int = 15,
        upper_cutoff: int = 90,
        truncated: bool = True,
        seed: Optional[int] = 42,
        noise: float = 0.1,
        age_gender_probs: Any = DEFAULT_AGE_GENDER_PROBS,
        month_weights: Any = DEFAULT_MONTH_WEIGHTS,
        weekday_weights: Any = DEFAULT_WEEKDAY_WEIGHTS,
    ) -> None:
        
        # ============================
        # VALIDATION: appointments_per_hour
        # ============================
        self.appointments_per_hour = self._validate_appointments_per_hour(appointments_per_hour)

        # ============================
        # VALIDATION: check_in_time_mean
        # ============================
        self.check_in_time_mean = self._validate_check_in_time_mean(check_in_time_mean)

        # ============================
        # VALIDATION: date_ranges & ref_date (deterministic defaults)
        # ============================
        if (ref_date is None) and (date_ranges is None):
            # Case 1 — nothing provided: use fully reproducible static window (2024)
            ref_dt_default = datetime(2024, 12, 1, 0, 0)                       # 2024-12-01 00:00
            self.date_ranges: list[tuple[datetime, datetime]] = [
                (datetime(2024, 1, 1, 0, 0), datetime(2024, 12, 31, 23, 59))            # [2024-01-01 00:00, 2024-12-31 23:59]
            ]
        else:
            # Normalize explicit ref_date if provided (to 00:00)
            if ref_date is None:
                ref_dt_default = None  # will derive from latest range end below
            else:
                ref_dt_default = self._to_datetime(ref_date).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            # Normalize/validate date_ranges (or default to static if absent)
            if date_ranges is None:
                # Keep deterministic window even if ref_date was provided: reproducible baseline
                self.date_ranges = [(datetime(2024, 1, 1, 0, 0), datetime(2024, 12, 31, 23, 59))]
            else:
                if not isinstance(date_ranges, (list, tuple)):
                    raise TypeError("`date_ranges` must be a list of (start, end) tuples.")
                validated_ranges: list[tuple[datetime, datetime]] = []
                for i, rng in enumerate(date_ranges):
                    if not (isinstance(rng, (list, tuple)) and len(rng) == 2):
                        raise TypeError(f"`date_ranges[{i}]` must be a (start, end) tuple.")
                    s, e = self._normalize_range(rng[0], rng[1])
                    validated_ranges.append((s, e))
                self.date_ranges = validated_ranges

            # If ref_date missing but date_ranges provided → use last day (00:00) of the latest range
            if ref_dt_default is None:
                latest_end = max(e for (_, e) in self.date_ranges)
                ref_dt_default = latest_end.replace(hour=0, minute=0, second=0, microsecond=0)

        # ============================
        # VALIDATION: ref_date lies within ranges
        # ============================
        self.ref_date = ref_dt_default
        if not any(start <= self.ref_date <= end for start, end in self.date_ranges):
            raise ValueError(
                f"`ref_date` must lie within at least one of the `date_ranges`. Got {self.ref_date}."
            )

        self.earliest_scheduling_date: datetime = min(s for (s, _) in self.date_ranges)

        # ============================
        # VALIDATION: booking_horizon
        # ============================
        if not isinstance(booking_horizon, int) or booking_horizon <= 0:
            raise ValueError("`booking_horizon` must be a positive integer (days).")
        self.booking_horizon = booking_horizon

        # Effective ranges: ensure latest end reaches at least ref_date + horizon (23:59).
        # Never shorten existing ranges.
        target_end = self._end_of_day(self.ref_date + timedelta(days=self.booking_horizon))
        self._effective_date_ranges: list[tuple[datetime, datetime]] = self._extend_latest_end_to(
            self.date_ranges, target_end
        )

        # ============================
        # VALIDATION: working_days
        # ============================
        if working_days is None:
            self.working_days = DEFAULT_WORKING_DAYS
        else:
            if not all(isinstance(d, int) and 0 <= d <= 6 for d in working_days):
                raise ValueError("`working_days` must be integers between 0 and 6 (Mon=0 .. Sun=6).")
            self.working_days = tuple(sorted(set(working_days)))

        # ============================
        # VALIDATION: working_hours
        # ============================
        self._working_blocks_min: list[tuple[int, int]] = self._normalize_working_blocks_min(working_hours)
        self.working_hours: list[tuple[int, int]] = [
            (s // 60, (e + 59) // 60) for (s, e) in self._working_blocks_min
        ]


        # ============================
        # VALIDATION: fill_rate
        # ============================
        if not isinstance(fill_rate, (int, float)) or not (MIN_FILL_RATE <= float(fill_rate) <= 1.0):
            raise ValueError(f"`fill_rate` must be a float in [{MIN_FILL_RATE}, 1].")
        self.fill_rate = float(fill_rate)

        # ============================
        # VALIDATION: median_lead_time
        # ============================
        if not isinstance(median_lead_time, int) or median_lead_time <= 0:
            raise ValueError("`median_lead_time` must be a positive integer (days).")
        if median_lead_time > booking_horizon:
            raise ValueError("`median_lead_time` must be <= `booking_horizon`.")
        self.median_lead_time = median_lead_time

        # ============================
        # VALIDATION: status_rates
        # ============================
        if status_rates is None:
            self.status_rates = DEFAULT_STATUS_RATES
        else:
            if not isinstance(status_rates, dict):
                raise TypeError("`status_rates` must be a dictionary.")
            if set(status_rates.keys()) != set(STATUS_KEYS):
                raise ValueError(f"`status_rates` must have keys {STATUS_KEYS}.")
            total = sum(status_rates.values())
            if not math.isclose(total, 1.0, rel_tol=1e-2):
                warnings.warn("`status_rates` values do not sum exactly to 1. They will be normalized.")
                status_rates = {k: v / total for k, v in status_rates.items()}
            self.status_rates = status_rates

        # ============================
        # VALIDATION: rebook_category
        # ============================
        valid_rebook_options = {"min", "med", "max"}
        if rebook_category not in valid_rebook_options:
            raise ValueError("`rebook_category` must be one of: 'min', 'med', or 'max'.")
        self.rebook_category = rebook_category
        self.rebook_ratio: float = {"min": 0.0, "med": 0.5, "max": 1.0}[rebook_category]

        # ============================
        # VALIDATION: visits_per_year
        # ============================
        if not isinstance(visits_per_year, (int, float)) or visits_per_year <= 0:
            raise ValueError("`visits_per_year` must be a positive number.")
        if visits_per_year > MAX_VISITS_PER_YEAR:
            raise ValueError(
                f"`visits_per_year` is unrealistically high (> {MAX_VISITS_PER_YEAR}). "
                "Use a lower value for ambulatory settings."
            )
        self.visits_per_year = float(visits_per_year)

        # ============================
        # VALIDATION: first_attendance
        # ============================
        if not isinstance(first_attendance, (int, float)) or not (0 <= first_attendance <= 1):
            raise ValueError("`first_attendance` must be between 0 and 1.")
        self.first_attendance = float(first_attendance)

        # ============================
        # VALIDATION: bin_size
        # ============================
        if not isinstance(bin_size, int) or bin_size <= 0:
            raise ValueError("`bin_size` must be a positive integer.")
        if bin_size > MAX_BIN_SIZE:
            raise ValueError(f"`bin_size` must be <= {MAX_BIN_SIZE}.")
        self.bin_size = bin_size
        
        # ============================
        # VALIDATION: lower_cutoff / upper_cutoff
        # ============================
        if not (isinstance(lower_cutoff, int) and isinstance(upper_cutoff, int)):
            raise TypeError("`lower_cutoff` and `upper_cutoff` must be integers.")
        if lower_cutoff >= upper_cutoff:
            raise ValueError("`lower_cutoff` must be strictly less than `upper_cutoff`.")
        self.lower_cutoff = lower_cutoff
        self.upper_cutoff = upper_cutoff

        # ============================
        # VALIDATION: truncated
        # ============================
        if not isinstance(truncated, bool):
            raise TypeError("`truncated` must be a boolean.")
        self.truncated = truncated

        # ============================
        # VALIDATION: noise
        # ============================
        if not isinstance(noise, (int, float)) or noise < 0:
            raise ValueError("`noise` must be a non-negative number.")
        self.noise = float(noise)

        # ============================
        # VALIDATION: seed (numpy + Faker)
        # ============================
        if seed is not None and not isinstance(seed, int):
            raise TypeError("`seed` must be an integer or None.")
        self.seed = seed
        self.rng = default_rng(seed)
        self.fake = Faker()
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            self.fake.seed_instance(seed)

        # ============================
        # VALIDATION: age_gender_probs
        # ============================
        required_cols = {"age_yrs", "total_female", "total_male"}

        # Default to immutable tuple-of-dicts if None (from constants)
        agp_src = age_gender_probs if age_gender_probs is not None else DEFAULT_AGE_GENDER_PROBS

        # Normalize to a pandas DataFrame:
        # - If already a DataFrame → copy
        # - If a Mapping → wrap in list and build DataFrame
        # - If a Sequence of Mappings → build DataFrame directly
        if isinstance(agp_src, pd.DataFrame):
            agp_df = agp_src.copy()
        elif isinstance(agp_src, Mapping):
            agp_df = pd.DataFrame([agp_src])
        elif isinstance(agp_src, Sequence) and not isinstance(agp_src, (str, bytes)):
            agp_df = pd.DataFrame(list(agp_src))
        else:
            raise TypeError(
                "`age_gender_probs` must be a pandas DataFrame or a sequence of "
                "mappings with keys {'age_yrs','total_female','total_male'}."
            )

        # Validate required columns
        missing = required_cols - set(agp_df.columns)
        if missing:
            raise ValueError(
                "`age_gender_probs` missing columns: " + ", ".join(sorted(missing))
            )

        # Coerce types and run basic sanity checks
        agp_df = agp_df.loc[:, ["age_yrs", "total_female", "total_male"]].copy()
        agp_df["age_yrs"] = agp_df["age_yrs"].astype(str)
        for col in ("total_female", "total_male"):
            agp_df[col] = pd.to_numeric(agp_df[col], errors="raise")

        if (agp_df[["total_female", "total_male"]] < 0).to_numpy().any():
            raise ValueError("Values in `age_gender_probs` must be non-negative.")

        self.age_gender_probs = agp_df.reset_index(drop=True)

        # ============================
        # VALIDATION: month_weights
        # ============================
        if not isinstance(month_weights, Mapping):
            raise TypeError("`month_weights` must be a mapping of {month:int → weight:float}.")
        mw = dict(month_weights)  
        if not all(isinstance(m, int) and 1 <= m <= 12 for m in mw.keys()):
            raise ValueError("`month_weights` keys must be integers between 1 and 12.")
        self.month_weights = mw

        # ============================
        # VALIDATION: weekday_weights
        # ============================
        if not isinstance(weekday_weights, Mapping):
            raise TypeError("`weekday_weights` must be a mapping of {weekday:int → weight:float}.")
        ww = dict(weekday_weights)
        if not all(isinstance(d, int) and 0 <= d <= 6 for d in ww.keys()):
            raise ValueError("`weekday_weights` keys must be integers between 0 and 6 (Mon=0..Sun=6).")
        self.weekday_weights = ww

        self._normalize_calendar_weights()

        # ----------------------------
        # Final initialization / state
        # ----------------------------
        self.slots_df: Optional[pd.DataFrame] = None
        self.appointments_df: Optional[pd.DataFrame] = None
        self.patients_df: Optional[pd.DataFrame] = None

        # Monotonic patient ID counter (string IDs are zero-padded downstream)
        self.patient_id_counter: int = 1

        logger.debug("AppointmentScheduler initialized with parameters: %s", {
            "date_ranges": self.date_ranges,
            "ref_date": self.ref_date,
            "working_days": self.working_days,
            "appointments_per_hour": self.appointments_per_hour,
            "working_hours": self.working_hours,
            "fill_rate": self.fill_rate,
            "booking_horizon": self.booking_horizon,
            "median_lead_time": self.median_lead_time,
            "status_rates": self.status_rates,
            "rebook_category": self.rebook_category,
            "check_in_time_mean": self.check_in_time_mean,
            "visits_per_year": self.visits_per_year,
            "first_attendance": self.first_attendance,
            "bin_size": self.bin_size,
            "lower_cutoff": self.lower_cutoff,
            "upper_cutoff": self.upper_cutoff,
            "truncated": self.truncated,
            "noise": self.noise,
            "seed": self.seed,
        })


    # -----------------------------------------------------------------------
    # Internal helpers for slot calendar
    # -----------------------------------------------------------------------
    def _iter_working_dates(self) -> list[pd.Timestamp]:
        """Working dates over the *effective* ranges (capacity),
        filtered by `working_days`, in chronological order."""
        dates: list[pd.Timestamp] = []
        ranges = getattr(self, "_effective_date_ranges", self.date_ranges)
        for start_dt, end_dt in ranges:
            days = pd.date_range(start=start_dt, end=end_dt, freq="D")
            wk = days[days.weekday.isin(self.working_days)]
            if len(wk):
                dates.extend(wk.to_list())
        return dates

    def _daily_time_grid(self) -> list[time]:
        """Build the list of time-of-day slots for a single working day.

        Returns
        -------
        list[datetime.time]
            One entry per slot (e.g., every 10 minutes if appointments_per_hour=6).

        Notes
        -----
        - Uses `appointments_per_hour` to derive slot granularity.
        - Supports multiple working blocks (non-overlapping).
        - Respects start/end minutes (:00 or :30) from `self._working_blocks_min`.
        """
        grid: list[time] = []
        step = 60 // self.appointments_per_hour  # e.g., 10 min if 6 appts/hour
        for s_min, e_min in self._working_blocks_min:
            for m in range(s_min, e_min, step):
                h, mm = divmod(m, 60)
                grid.append(time(hour=h, minute=mm))
        return grid

    # -------------------------------------------------------------
    # Generate all appointment slots based on working calendar
    # -------------------------------------------------------------
    def generate_slots(self) -> pd.DataFrame:
        """Build the slot calendar over all `date_ranges`.

        The calendar is restricted to `working_days` and `working_hours`,
        and it uses a fixed slot duration derived from `appointments_per_hour`.

        Returns
        -------
        pandas.DataFrame
            Columns
            -------
            slot_id : str
                Zero‑padded sequential identifier.
            appointment_date : datetime64[ns]
                The calendar date of the slot.
            appointment_time : datetime.time
                The time of day for the slot.
            is_available : bool
                Initialized to True; changes downstream when booked/cancelled.

        Notes
        -----
        - This step **does not** perform any booking; it only enumerates capacity.
        - Slot duration (minutes) = ``60 // appointments_per_hour``.
        - The output preserves chronological order by (date, time).
        """
        working_dates = self._iter_working_dates()
        if not working_dates:
            # Defensive guard: empty capacity (e.g., no working days within ranges)
            return pd.DataFrame(
                columns=["slot_id", "appointment_date", "appointment_time", "is_available"]
            )

        times = self._daily_time_grid()
        # Cartesian product: dates × times
        # We avoid building a giant Python list when possible; construct with repeats.
        n_dates = len(working_dates)
        n_times = len(times)
        total_slots = n_dates * n_times

        # slot_id width (zero-padded)
        id_width = max(4, len(str(total_slots)))

        # Vectorized columns
        dates_col = np.repeat(np.array(working_dates, dtype="datetime64[ns]"), n_times)
        times_col = np.tile(np.array(times, dtype=object), n_dates)  # dtype=object to hold py `time`

        slots_df = pd.DataFrame(
            {
                "slot_id": pd.Series((f"{i:0{id_width}d}" for i in range(1, total_slots + 1))),
                "appointment_date": pd.to_datetime(dates_col),
                "appointment_time": times_col,
                "is_available": True,
            }
        )

        # Ensure stable chronological order
        slots_df.sort_values(["appointment_date", "appointment_time"], inplace=True, kind="mergesort")
        slots_df.reset_index(drop=True, inplace=True)
        self.total_slots = len(slots_df)
        return slots_df
    

    # -------------------------------------------------------------------
    # Internals (helpers used by generate_appointments)
    # -------------------------------------------------------------------
    def _lead_time_pmf(self, max_interval: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute a discrete exponential-like PMF over lead-time days [1..max_interval].

        Parameters
        ----------
        max_interval : int
            Maximum allowed scheduling interval in days.

        Returns
        -------
        (k, p) : (np.ndarray, np.ndarray)
            `k` is the support 1..max_interval and `p` the normalized probabilities.

        Notes
        -----
        - Uses the same parameterization as the original code:
          tau_eff = median_lead_time / ln(2)
          p(k) ∝ exp(-k / tau_eff)
        """
        if max_interval <= 0:
            # No valid interval → return empty support; caller must guard this.
            return np.array([], dtype=int), np.array([], dtype=float)

        tau_eff = self.median_lead_time / np.log(2)
        k = np.arange(1, max_interval + 1, dtype=int)
        p = np.exp(-k / tau_eff)
        p /= p.sum()
        return k, p

    def _weighted_sample_past_slots(self, n: int) -> pd.DataFrame:
        """
        Sample `n` available past slots with calendar weights (month × weekday).

        Returns at least:
        ['slot_id', 'appointment_date', 'appointment_time'].
        """
        cols = ["slot_id", "appointment_date", "appointment_time"]

        if n <= 0:
            return pd.DataFrame(columns=cols)
        slots_df = getattr(self, "slots_df", None)
        if slots_df is None or slots_df is pd.NA or (hasattr(slots_df, "empty") and slots_df.empty):
            if hasattr(self, "generate_slots"):
                try:
                    gen = self.generate_slots()
                    if gen is not None and hasattr(gen, "empty") and not gen.empty:
                        self.slots_df = gen.copy()
                        slots_df = self.slots_df
                    else:
                        return pd.DataFrame(columns=cols)
                except Exception:
                    return pd.DataFrame(columns=cols)
            else:
                return pd.DataFrame(columns=cols)

        df = slots_df.copy()
        df["appointment_date"] = pd.to_datetime(df.get("appointment_date"), errors="coerce")
        if "is_available" in df.columns:
            df["is_available"] = df["is_available"].astype(bool)
        else:
            df["is_available"] = True
        ref_date = getattr(self, "ref_date", None)
        if ref_date is None or pd.isna(ref_date):
            max_dt = df["appointment_date"].max()
            ref_date = (max_dt + pd.Timedelta(days=1)) if pd.notna(max_dt) else pd.Timestamp.today().normalize()

        past = df[(df["appointment_date"] < ref_date) & (df["is_available"])].copy()
        if past.empty:
            past = df[df["is_available"]].copy()
            if past.empty:
                return pd.DataFrame(columns=cols)
        try:
            from .constants import DEFAULT_MONTH_WEIGHTS, DEFAULT_WEEKDAY_WEIGHTS
            month_w = past["appointment_date"].dt.month.map(DEFAULT_MONTH_WEIGHTS).astype(float)
            wday_w  = past["appointment_date"].dt.weekday.map(DEFAULT_WEEKDAY_WEIGHTS).astype(float)
            weights = (month_w * wday_w).replace([np.inf, -np.inf], np.nan).fillna(0.0)
            if (weights <= 0).all():
                weights = None
        except Exception:
            weights = None 
        replace = len(past) < n
        rnd = getattr(self, "random_state", None)
        if rnd is None:
            rnd = getattr(self, "seed", None)

        sampled = past.sample(n=n, replace=replace, weights=weights, random_state=rnd)
        for c in cols:
            if c not in sampled.columns:
                sampled[c] = pd.NA

        return sampled[cols].reset_index(drop=True)
    

    def _finalize_appt_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column order, sort, assign contiguous string `appointment_id`,
        and drop staging columns used during generation.

        Parameters
        ----------
        df : pd.DataFrame
            Appointment table after rebooking + status assignment.

        Returns
        -------
        pd.DataFrame
            Canonical appointments table ready for downstream steps.
        """
        if df.empty:
            # Create an empty frame with the canonical schema
            cols = [
                "appointment_id", "slot_id", "scheduling_date", "appointment_date",
                "appointment_time", "scheduling_interval", "status"
            ]
            return pd.DataFrame(columns=cols)

        # Sort by scheduling_date for ID assignment stability, then by scheduled slot time
        df = df.sort_values(by="scheduling_date").reset_index(drop=True)

        id_width = len(str(max(len(df), 1))) + 1
        df["appointment_id"] = (df.index + 1).astype(str).str.zfill(id_width)

        # Remove staging columns
        df = df.drop(columns=["rebook_iteration", "primary_status"], errors="ignore")

        # Final column order (kept consistent with original pipeline expectations)
        cols = [
            "appointment_id", "slot_id", "scheduling_date", "appointment_date",
            "appointment_time", "scheduling_interval", "status"
        ]
        df = df[cols].sort_values(by=["appointment_date", "appointment_time"]).reset_index(drop=True)
        return df

    # -----------------------------------------------------------------------
    # Calendar weighting helpers (month × weekday)
    # -----------------------------------------------------------------------
    def _normalize_calendar_weights(self) -> None:
        """Precompute normalized (mean=1) month and weekday weights."""
        m_vals = np.array(list(self.month_weights.values()), dtype=float)
        w_vals = np.array(list(self.weekday_weights.values()), dtype=float)

        m_mean = float(m_vals.mean()) if m_vals.size else 1.0
        w_mean = float(w_vals.mean()) if w_vals.size else 1.0

        if not np.isfinite(m_mean) or m_mean == 0.0:
            m_mean = 1.0
        if not np.isfinite(w_mean) or w_mean == 0.0:
            w_mean = 1.0

        self._month_w_norm = {k: float(v) / m_mean for k, v in self.month_weights.items()}
        self._weekday_w_norm = {k: float(v) / w_mean for k, v in self.weekday_weights.items()}

    def _norm_month(self, month: int) -> float:
        """Normalized month weight (mean=1)."""
        return float(self._month_w_norm.get(int(month), 1.0))

    def _norm_weekday(self, weekday: int) -> float:
        """Normalized weekday weight (mean=1)."""
        return float(self._weekday_w_norm.get(int(weekday), 1.0))

    def _date_weight_raw(self, ts: "pd.Timestamp|datetime|date") -> float:
        """Return raw calendar weight for a given date (month × weekday)."""
        if not isinstance(ts, pd.Timestamp):
            ts = pd.Timestamp(ts)
        return self._norm_month(ts.month) * self._norm_weekday(ts.weekday())

    # -------------------------------------------------------------------
    # Generate appointment bookings with realistic temporal dynamics
    # -------------------------------------------------------------------
    def generate_appointments(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Simulate historical and future appointment scheduling with realistic
        attendance, cancellation, and rebooking patterns.

        Steps
        -----
        1) Compute the number of past slots to fill (`fill_rate`) and the initial
           booking volume A0 after accounting for cancellations and rebooking.
        2) Sample *past* available slots with seasonality weights (month × weekday).
        3) Assign scheduling dates via a discrete exponential lead-time model.
        4) Apply cancellation and iterative rebooking according to `rebook_category`.
        5) Assign final status to pre-ref_date appointments (attended/DNA/unknown/cancelled).
        6) Simulate *future* appointments within `booking_horizon`.
        7) Normalize columns, IDs, fill-rate metrics, and add attended timing fields.

        Returns
        -------
        (slots_df, appointments_df) : tuple[pd.DataFrame, pd.DataFrame]
            Updated slot availability and the finalized appointments table.

        Notes
        -----
        - Core logic and distributions intentionally preserved; this is a structural,
          PEP-compliant refactor for readability and maintainability.
        """
        # -------------------------------
        # Defensive preconditions
        # -------------------------------
        if getattr(self, "slots_df", None) is None or self.slots_df.empty:
            raise ValueError("`slots_df` is empty. Call `generate_slots()` before `generate_appointments()`.")
        if not hasattr(self, "total_slots_past"):
            # Compute if not present (kept consistent with original pipeline)
            self.total_slots_past = int((self.slots_df["appointment_date"] < self.ref_date).sum())

        # -------------------------------
        # Target volume for past bookings
        # -------------------------------
        total_slots_to_fill = int(self.fill_rate * self.total_slots_past)

        # ------------------------------------------
        # Estimate the initial number of bookings (A0)
        # ------------------------------------------
        c = self.status_rates['cancelled']
        rebook_ratio = getattr(
            self,
            "rebook_ratio",
            {"min": 0.0, "med": 0.5, "max": 1.0}.get(getattr(self, "rebook_category", "med"), 0.5),
        )

        A0 = total_slots_to_fill * (1 - c * rebook_ratio) / (1 - c)
        A0 = int(round(A0))

        # -------------------------------
        # Sample past available slots (weighted)
        # -------------------------------
        booked_slots = self._weighted_sample_past_slots(A0)
        if not booked_slots.empty:
            self.slots_df.loc[self.slots_df["slot_id"].isin(booked_slots["slot_id"]), "is_available"] = False

        # -------------------------------
        # Assign scheduling dates for past bookings
        # -------------------------------
        records: list[dict] = []
        for _, slot in booked_slots.iterrows():
            appt_date: pd.Timestamp = slot["appointment_date"]
            max_sched_interval = min(
                (appt_date - self.earliest_scheduling_date).days,
                self.booking_horizon
            )
            k, p = self._lead_time_pmf(max_sched_interval)
            if k.size == 0:
                sched_dt = max(appt_date - timedelta(days=1), self.earliest_scheduling_date)
            else:
                interval = int(np.random.choice(k, p=p))
                sched_dt = max(appt_date - timedelta(days=interval), self.earliest_scheduling_date)

            records.append(
                {
                    "slot_id": slot["slot_id"],
                    "scheduling_date": sched_dt,
                    "appointment_date": appt_date,
                    "appointment_time": slot["appointment_time"],
                    "scheduling_interval": (appt_date - sched_dt).days,
                    "rebook_iteration": 0,
                }
            )

        # -------------------------------
        # Staging frame for downstream cancellation/rebooking
        # -------------------------------
        self.appointments_df = pd.DataFrame.from_records(records)

        # -------------------------------
        # Primary cancellation draw (past)
        # -------------------------------
        if self.appointments_df.empty:
            self.appointments_df["primary_status"] = pd.Series(dtype=object)
            appointment_id_counter = 1
            self.fill_rate_calculated = 0.0
        else:
            self.appointments_df["primary_status"] = np.random.choice(
                ["cancelled", "scheduled"],
                size=len(self.appointments_df),
                p=[c, 1 - c],
            )

            # -------------------------------
            # Iterative rebooking
            # -------------------------------
            self.appointments_df, appointment_id_counter = self.rebook_appointments(self.appointments_df)

            # -------------------------------
            # Final status assignment pre-ref_date
            # -------------------------------
            self.appointments_df = self.assign_status(self.appointments_df)

            # -------------------------------
            # Update slots from past outcomes
            # -------------------------------
            cancelled_ids = self.appointments_df.loc[self.appointments_df["primary_status"] == "cancelled", "slot_id"]
            attended_like_ids = self.appointments_df.loc[
                self.appointments_df["status"].isin(["attended", "did not attend", "unknown"]),
                "slot_id",
            ]

            self.slots_df.loc[self.slots_df["slot_id"].isin(cancelled_ids), "is_available"] = True
            self.slots_df.loc[self.slots_df["slot_id"].isin(attended_like_ids), "is_available"] = False

            self.fill_rate_calculated = (
                len(attended_like_ids) / self.total_slots_past if self.total_slots_past > 0 else 0.0
        )

        # -------------------------------
        # Future appointments (within horizon)
        # -------------------------------
        self.appointments_df = self.schedule_future_appointments(self.appointments_df, appointment_id_counter)

        # -------------------------------
        # Finalize appointments table and add attended timings
        # -------------------------------
        self.appointments_df = self._finalize_appt_table(self.appointments_df)

        if not self.appointments_df.empty:
            self.appointments_df = self.assign_actual_times(self.appointments_df)
            self.scheduling_interval_mean_calculated = float(self.appointments_df["scheduling_interval"].mean())

        return self.slots_df, self.appointments_df


    # ---------------------------------------------------------------
    # Rebooking Logic for Cancelled Appointments (Iterative Simulation)
    # ---------------------------------------------------------------
    def rebook_appointments(self, appointments_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """
        Iteratively rebook a fraction of cancelled appointments.

        The process repeats up to:
        • 1 iteration for "min"
        • ≤2 iterations for "med"
        • Until exhausted for "max" (subject to data)

        Parameters
        ----------
        appointments_df : pandas.DataFrame
            Must include: ['slot_id','scheduling_date','appointment_date',
            'appointment_time','primary_status','rebook_iteration'].

        Returns
        -------
        tuple
            updated_df : pandas.DataFrame
                Original + rebooked rows. Rebooked rows inherit the same slot_id and date.
            appointment_id_counter : int
                Counter advanced for downstream ID assignment (note: the final, stable
                `appointment_id` is assigned once at the end of the pipeline).
        """
        required = {
            "slot_id", "scheduling_date", "appointment_date", "appointment_time",
            "primary_status", "rebook_iteration"
        }
        missing = required - set(appointments_df.columns)
        if missing:
            raise ValueError(f"appointments_df is missing required columns: {sorted(missing)}")

        appointment_id_counter = 1
        max_digits = len(str(getattr(self, "total_slots", len(self.slots_df)))) + 1
        rebook_iteration = 0

        while True:
            # -- Select cancelled in the current iteration
            cancelled = appointments_df[
                (appointments_df["primary_status"] == "cancelled")
                & (appointments_df["rebook_iteration"] == rebook_iteration)
            ]

            if cancelled.empty or len(cancelled) <= 1:
                break

            rebook_count = int(round(len(cancelled) * self.rebook_ratio))
            if rebook_count == 0:
                break

            rs = None if self.seed is None else (self.seed + rebook_iteration)
            rebooked = cancelled.sample(n=rebook_count, random_state=rs)
            new_appointments: list[dict] = []

            # -- Schedule rebooked appointments within (scheduling_date, appointment_date)
            for _, original in rebooked.iterrows():
                days_between = (original["appointment_date"] - original["scheduling_date"]).days
                if days_between <= 1:
                    # Not enough room to insert a new scheduling_date before the appointment_date
                    continue

                days_after = np.random.randint(1, days_between)
                new_sched_date = original["scheduling_date"] + timedelta(days=days_after)
                if new_sched_date >= original["appointment_date"]:
                    continue 

                new_appt = {
                    "appointment_id": str(appointment_id_counter).zfill(max_digits),
                    "slot_id": original["slot_id"],
                    "scheduling_date": new_sched_date,
                    "appointment_date": original["appointment_date"],
                    "appointment_time": original["appointment_time"],
                    "scheduling_interval": (original["appointment_date"] - new_sched_date).days,
                    "rebook_iteration": rebook_iteration + 1,
                    "primary_status": np.random.choice(
                        ["cancelled", "scheduled"],
                        p=[self.status_rates["cancelled"], 1 - self.status_rates["cancelled"]]
                    ),
                }
                new_appointments.append(new_appt)
                appointment_id_counter += 1

            if new_appointments:
                appointments_df = pd.concat(
                    [appointments_df, pd.DataFrame(new_appointments)],
                    ignore_index=True
                )
            else:
                break

            rebook_iteration += 1

            # -- Bound iteration depth by chosen category
            if self.rebook_category == "min":
                break
            if self.rebook_category == "med" and rebook_iteration >= 2:
                break
            if self.rebook_category == "max":
                remaining = appointments_df[
                    (appointments_df["primary_status"] == "cancelled")
                    & (appointments_df["rebook_iteration"] == rebook_iteration)
                ]
                if len(remaining) <= 1:
                    break

        return appointments_df, appointment_id_counter

    # ---------------------------------------------------------------
    # Assign Final Status to Appointments Before Reference Date
    # ---------------------------------------------------------------
    def assign_status(self, appointments_df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign a final 'status' to each appointment given its primary state and ref_date.

        Rules
        -----
        • For appointments before `ref_date` and not cancelled: draw from the normalized
          past-outcome mixture {'attended','did not attend','unknown'}.
        • For any appointment with primary_status == 'cancelled': status == 'cancelled'.
        • Future appointments retain their primary status ('scheduled' / 'cancelled').

        Parameters
        ----------
        appointments_df : pd.DataFrame
            Must contain 'appointment_date' and 'primary_status'.

        Returns
        -------
        pd.DataFrame
            Input with a 'status' column added/overwritten.
        """
        missing = {"appointment_date", "primary_status"} - set(appointments_df.columns)
        if missing:
            raise ValueError(f"appointments_df missing columns: {sorted(missing)}")

        # -- Pre-ref_date and not cancelled → assign attended/DNA/unknown
        mask = (
            (appointments_df["appointment_date"] < self.ref_date)
            & (appointments_df["primary_status"] != "cancelled")
        )
        pre_ref_active = appointments_df[mask]

        if len(pre_ref_active) > 0:
            s_att = self.status_rates["attended"]
            s_dna = self.status_rates["did not attend"]
            s_unk = self.status_rates["unknown"]
            denom = s_att + s_dna + s_unk
            if denom <= 0:
                raise ValueError("Invalid status rates; non-cancelled components sum to zero.")

            probs = [s_att / denom, s_dna / denom, s_unk / denom]
            labels = ["attended", "did not attend", "unknown"]

            drawn = np.random.choice(labels, size=len(pre_ref_active), p=probs)
            appointments_df.loc[pre_ref_active.index, "status"] = drawn

        # -- Cancelled appointments remain cancelled
        appointments_df.loc[
            appointments_df["primary_status"] == "cancelled",
            "status"
        ] = "cancelled"

        return appointments_df

    # ---------------------------------------------------------------
    # Simulate Realistic Arrival, Start, and End Times (Attended Only)
    # ---------------------------------------------------------------
    def assign_actual_times(self, appointments_df: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate in-clinic execution times for attended visits.

        For each 'attended' row this assigns:
        - check_in_time: arrival timestamp drawn from punctuality distribution
        - start_time: clinic start respecting arrival + backlog
        - end_time: start_time + stochastic duration
        - appointment_duration (minutes), waiting_time (minutes)

        Parameters
        ----------
        appointments_df : pd.DataFrame
            Needs ['appointment_date','appointment_time','status'].

        Returns
        -------
        pd.DataFrame
            Same frame with timing columns populated for attended rows:
            ['check_in_time','start_time','end_time','appointment_duration','waiting_time'].

        Notes
        -----
        • We keep the distributional logic intact; only structure/validation improved.
        • Times are finally formatted as '%H:%M:%S' strings (analytics-friendly).
        """
        need = {"appointment_date", "appointment_time", "status"}
        missing = need - set(appointments_df.columns)
        if missing:
            raise ValueError(f"appointments_df missing columns: {sorted(missing)}")

        # Initialize columns
        appointments_df = appointments_df.copy()
        appointments_df["check_in_time"] = pd.NaT
        appointments_df["appointment_duration"] = np.nan
        appointments_df["start_time"] = pd.NaT
        appointments_df["end_time"] = pd.NaT
        appointments_df["waiting_time"] = np.nan

        attended = appointments_df[appointments_df["status"] == "attended"]
        if attended.empty:
            # Nothing to simulate
            for col in ["start_time", "end_time", "check_in_time"]:
                appointments_df[col] = pd.to_datetime(appointments_df[col]).dt.strftime("%H:%M:%S")
            return appointments_df

        for appt_date in attended["appointment_date"].unique():
            daily = attended[attended["appointment_date"] == appt_date].copy()

            daily["check_in_time"] = daily.apply(
                lambda r: self.generate_check_in_time(r["appointment_date"], r["appointment_time"]),
                axis=1
            )

            daily.sort_values(by=["check_in_time", "appointment_time"], inplace=True)

            previous_end: Optional[datetime] = None
            for idx, appt in daily.iterrows():
                sched_dt = datetime.combine(appt["appointment_date"], appt["appointment_time"])
                w_start_min = self._working_blocks_min[0][0]
                work_start = sched_dt.replace(hour=w_start_min // 60, minute=w_start_min % 60, second=0)
                check_in = appt["check_in_time"]
                earliest_start = max(check_in, work_start)
                if previous_end is not None:
                    earliest_start = max(earliest_start, previous_end)
                delay_sec = max(0.0, float(np.random.normal(loc=60, scale=(75 - 60) / 1.96)))
                start = earliest_start + timedelta(seconds=delay_sec)

                # Duration from Beta(1.48, 3.6) scaled to 0–60 minutes
                duration_min = round(float(np.random.beta(1.48, 3.6) * 60), 1)
                end = start + timedelta(minutes=duration_min)

                # Waiting time in minutes (from arrival to start)
                waiting_min = round((start - check_in).total_seconds() / 60.0, 1)
                previous_end = end

                appointments_df.at[appt.name, "check_in_time"] = check_in
                appointments_df.at[appt.name, "start_time"] = start
                appointments_df.at[appt.name, "end_time"] = end
                appointments_df.at[appt.name, "appointment_duration"] = duration_min
                appointments_df.at[appt.name, "waiting_time"] = waiting_min

        # Format datetime columns to HH:MM:SS strings for downstream use
        for col in ["start_time", "end_time", "check_in_time"]:
            appointments_df[col] = pd.to_datetime(appointments_df[col]).dt.strftime("%H:%M:%S")

        return appointments_df

    # ---------------------------------------------------------------
    # Simulate Patient Check-In Time Based on Punctuality Behavior
    # ---------------------------------------------------------------
    def generate_check_in_time(self, appointment_date: date, appointment_time: time) -> datetime:
        """
        Draw a check-in timestamp relative to the scheduled time.

        Behavior
        --------
        • Mean offset is user-configured (`check_in_time_mean`, validated to [-60,+30] minutes).
        • Individual arrivals are sampled from a Normal(mean, 9.8min) *without clipping*,
          so a small tail may arrive earlier/later than that range (realistic behavior).

        Parameters
        ----------
        appointment_date : datetime.date
        appointment_time : datetime.time

        Returns
        -------
        datetime
            Concrete timestamp (same date) for check-in.
        """
        scheduled_dt = datetime.combine(appointment_date, appointment_time)
        mean_offset_min = float(self.check_in_time_mean)
        offset = float(np.random.normal(loc=mean_offset_min, scale=CHECK_IN_STD_MIN))
        return scheduled_dt + timedelta(minutes=offset)

    # ---------------------------------------------------------------
    # Simulate Future Appointments with Decaying Fill/Cancellation
    # ---------------------------------------------------------------
    def schedule_future_appointments(
        self,
        appointments_df: pd.DataFrame,
        appointment_id_counter: int
    ) -> pd.DataFrame:
        """
        Schedule appointments on/after `ref_date` using decaying fill and cancellation rates.

        Logic
        -----
        • For each future date within the booking horizon:
          - Decide how many slots to fill using: base fill_rate × exp(-k_fill * days_ahead),
            adjusted by month/weekday weights and small noise.
          - For each filled slot, draw scheduling_date from an exponential lead-time
            (median = `median_lead_time`), then mark status as 'scheduled' or 'cancelled'
            via a decaying cancellation probability exp(-k_cancel * days_ahead).
          - Cancelled future slots are freed back to availability.

        Parameters
        ----------
        appointments_df : pd.DataFrame
            Existing appointments (past side already simulated).
        appointment_id_counter : int
            Next running ID for future appointments (temp; final IDs re-assigned later).

        Returns
        -------
        pd.DataFrame
            Input with appended future appointments (status ∈ {'scheduled','cancelled'}).
        """
        if self.slots_df.empty:
            return appointments_df

        # -- Identify future dates within horizon
        slots_per_date = self.slots_df.groupby("appointment_date").size()
        future_dates = slots_per_date.index[
            (slots_per_date.index >= self.ref_date)
            & (slots_per_date.index < self.ref_date + timedelta(days=self.booking_horizon))
        ]

        # -- Precompute normalized calendar weights for those dates
        w_map = {d: self._date_weight_raw(pd.Timestamp(d)) for d in future_dates}
        if w_map:
            mean_w = float(np.mean(list(w_map.values())))
            if mean_w > 0:
                w_map = {d: w / mean_w for d, w in w_map.items()}

        # -- Decay constants from desired endpoints
        tau_eff = self.median_lead_time / np.log(2)  # exponential scale from median
        k_fill = -np.log(0.01 / self.fill_rate) / self.booking_horizon
        k_cancel = -np.log(0.01 / self.status_rates["cancelled"]) / self.booking_horizon

        for appt_date in future_dates:
            delta_days = (appt_date - self.ref_date).days

            # Decaying fill and cancellation
            fill_rate = float(self.fill_rate * np.exp(-k_fill * delta_days))
            cancel_rate = float(self.status_rates["cancelled"] * np.exp(-k_cancel * delta_days))

            # Expected count with small multiplicative noise and calendar weight
            variability = float(np.random.normal(loc=1.0, scale=self.noise))
            expected_n = int(slots_per_date[appt_date] * fill_rate * variability * w_map[appt_date])
            expected_n = max(0, min(int(expected_n), int(slots_per_date[appt_date])))

            # Available slots for that day
            available = self.slots_df[
                (self.slots_df["appointment_date"] == appt_date) & (self.slots_df["is_available"])
            ]
            expected_n = min(expected_n, len(available))
            if expected_n <= 0:
                continue

            rs = None if self.seed is None else (self.seed + delta_days)
            booked = available.sample(n=expected_n, random_state=rs)
            self.slots_df.loc[self.slots_df["slot_id"].isin(booked["slot_id"]), "is_available"] = False

            new_rows: list[dict] = []
            for _, slot in booked.iterrows():
                # Lead time (days) from exponential with median=median_lead_time, bounded to horizon
                max_interval = min(delta_days, self.booking_horizon)
                sched_interval = int(round(float(np.random.exponential(scale=tau_eff))))
                sched_interval = max(1, min(sched_interval, max_interval))

                sched_date = appt_date - timedelta(days=sched_interval)
                # Constrain schedule dates to [ref_date - horizon, ref_date]
                sched_date = min(sched_date, self.ref_date)
                sched_date = max(sched_date, self.ref_date - timedelta(days=self.booking_horizon))
                width = len(str(getattr(self, "total_slots", len(self.slots_df)))) + 1
                row = {
                    "appointment_id": str(appointment_id_counter).zfill(width),
                    "slot_id": slot["slot_id"],
                    "scheduling_date": sched_date,
                    "appointment_date": appt_date,
                    "appointment_time": slot["appointment_time"],
                    "scheduling_interval": (appt_date - sched_date).days,
                    "status": "scheduled",
                }

                # Future cancellation draw with decaying probability
                row["status"] = np.random.choice(["cancelled", "scheduled"], p=[cancel_rate, 1 - cancel_rate])

                if row["status"] == "cancelled":
                    self.slots_df.loc[self.slots_df["slot_id"] == slot["slot_id"], "is_available"] = True

                new_rows.append(row)
                appointment_id_counter += 1

            appointments_df = pd.concat([appointments_df, pd.DataFrame(new_rows)], ignore_index=True)

        return appointments_df

    # ---------------------------------------------------------------
    # Generate Synthetic Patient Demographics by Age and Sex
    # ---------------------------------------------------------------
    def generate_patients(self, total_patients: int) -> pd.DataFrame:
        """
        Generate a synthetic patient population with NHS-based age×sex structure.

        Parameters
        ----------
        total_patients : int
            Number of unique patients to create.

        Returns
        -------
        pd.DataFrame
            Columns: ['patient_id','name','sex','age'].
        """
        if total_patients <= 0:
            raise ValueError("total_patients must be a positive integer.")

        # Parse age range bins
        age_ranges: list[tuple[int, int]] = [
            (90, 100) if age == "90+" else tuple(map(int, age.split("-")))
            for age in self.age_gender_probs["age_yrs"]
        ]

        # Optional truncation of lower bins (keeps original bin logic intact)
        if self.truncated:
            full_ranges = age_ranges
            valid_idx = [i for i, (low, high) in enumerate(full_ranges) if high >= self.lower_cutoff]
            self.age_gender_probs = self.age_gender_probs.iloc[valid_idx].reset_index(drop=True)
            age_ranges = [full_ranges[i] for i in valid_idx]

        # Sex totals
        female_prop = float(self.age_gender_probs["total_female"].sum())
        male_prop = float(self.age_gender_probs["total_male"].sum())
        total_prop = female_prop + male_prop
        if total_prop <= 0:
            raise ValueError("Invalid age_gender_probs: total proportions sum to zero.")

        num_females = int(total_patients * (female_prop / total_prop))
        num_males = total_patients - num_females

        patients: list[dict] = []

        # Female sampling
        female_probs = (self.age_gender_probs["total_female"] / female_prop).to_numpy()
        for i in np.random.choice(len(age_ranges), size=num_females, p=female_probs):
            low, high = age_ranges[i]
            age = np.random.randint(max(low, self.lower_cutoff), min(high, self.upper_cutoff) + 1)
            patients.append({"name": self.fake.name_female(), "sex": "Female", "age": int(age)})

        # Male sampling
        male_probs = (self.age_gender_probs["total_male"] / male_prop).to_numpy()
        for i in np.random.choice(len(age_ranges), size=num_males, p=male_probs):
            low, high = age_ranges[i]
            age = np.random.randint(max(low, self.lower_cutoff), min(high, self.upper_cutoff) + 1)
            patients.append({"name": self.fake.name_male(), "sex": "Male", "age": int(age)})

        # Assemble DataFrame with sequential, zero-padded patient_id
        patients_df = pd.DataFrame(patients)
        id_length = max(5, len(str(self.patient_id_counter + total_patients - 1)))
        ids = [f"{i:0{id_length}d}" for i in range(self.patient_id_counter, self.patient_id_counter + total_patients)]
        self.patient_id_counter += total_patients
        patients_df.insert(0, "patient_id", ids)

        return patients_df

    # ------------------------------------------------------------------
    # Assign Patients to Appointments with Turnover and Age-on-Date
    # ------------------------------------------------------------------
    def assign_patients(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Assign patients to appointments by year with turnover, and compute age at visit.

        Steps
        -----
        1) Partition appointments by year, compute expected patient volume from visits_per_year.
        2) Year 1: all new patients. Subsequent years: mix of returning (+1 year of age) and new.
           (This keeps your original “+1 year on return” rule intact; no np.clip / unique resampling.)
        3) Compute patient DOB from age at first appointment; then compute per-appointment age.
        4) Add 'age_group' (binning with configured bin_size/cutoffs).
        5) Keep auxiliary tables: patients_df and appointments_df; the latter is the primary table.

        Returns
        -------
        tuple
            patients_df : pd.DataFrame
                Registry with ['patient_id','name','sex','dob'] (age removed, DOB derived).
            appointments_df : pd.DataFrame
                Main table including ['patient_id','sex','age','age_group'] plus scheduling/timing/status.
        """
        if self.appointments_df.empty:
            raise ValueError("No appointments to assign patients to. Did you run generate_appointments()?")

        # Order and tag by appointment year
        self.appointments_df = self.appointments_df.sort_values("appointment_date").reset_index(drop=True)
        self.appointments_df["appointment_year"] = self.appointments_df["appointment_date"].dt.year

        appointments_per_year = self.appointments_df.groupby("appointment_year").size().to_dict()

        patients_df = pd.DataFrame()
        assigned_appointments_df = pd.DataFrame()
        accumulated_patients = pd.DataFrame()

        # Process year by year
        for idx, (year, total_appointments) in enumerate(appointments_per_year.items()):
            yearly_random_factor = 1 + np.random.uniform(-self.noise, self.noise)

            if idx == 0:
                # First year: all new patients
                num_patients = max(1, int((total_appointments / self.visits_per_year) * yearly_random_factor))
                new_patients_df = self.generate_patients(num_patients)
                new_patients_df["year_joined"] = year

                accumulated_patients = new_patients_df.copy()
                patients_df = new_patients_df.copy()
                current_patients_df = new_patients_df.copy()
            else:
                # Later years: returning + new based on first_attendance
                expected_total_patients = max(1, int((total_appointments / self.visits_per_year) * yearly_random_factor))

                new_ratio = self.first_attendance * (1 + np.random.uniform(-self.noise, self.noise))
                num_new_patients = max(0, int(expected_total_patients * new_ratio))
                num_returning_patients = expected_total_patients - num_new_patients

                num_returning_patients = min(num_returning_patients, len(accumulated_patients))
                num_new_patients = expected_total_patients - num_returning_patients

                # Returning: increment age exactly +1 year (as requested)
                returning_df = accumulated_patients.sample(n=num_returning_patients, random_state=self.seed).copy()
                returning_df["age"] = returning_df["age"] + 1

                # New patients
                new_patients_df = self.generate_patients(num_new_patients)
                new_patients_df["year_joined"] = year

                # Optional small noise to “age levels” of new cohort to balance returning cohort
                if num_new_patients > 0:
                    age_shift = num_returning_patients / num_new_patients
                    adjusted: list[int] = []
                    for age in new_patients_df["age"]:
                        noise = np.random.uniform(-self.noise, self.noise)
                        candidate = age - int(age_shift + noise)
                        while candidate < self.lower_cutoff or candidate > self.upper_cutoff:
                            candidate = np.random.randint(self.lower_cutoff, self.upper_cutoff + 1)
                        adjusted.append(int(candidate))
                    new_patients_df["age"] = adjusted

                # Update pools
                accumulated_patients = pd.concat([accumulated_patients, new_patients_df], ignore_index=True)
                accumulated_patients.drop_duplicates(subset="patient_id", inplace=True)
                patients_df = pd.concat([patients_df, new_patients_df], ignore_index=True)
                current_patients_df = pd.concat([new_patients_df, returning_df], ignore_index=True)

            # Assign this year's appointments to current patient pool
            year_appointments = self.appointments_df[self.appointments_df["appointment_year"] == year].copy()
            n_appts = len(year_appointments)

            # Ensure at least one visit per patient, then distribute the remainder
            visit_counts = np.ones(len(current_patients_df), dtype=int)
            remainder = n_appts - len(current_patients_df)
            if remainder > 0:
                extra_ix = np.random.choice(len(current_patients_df), size=remainder, replace=True)
                np.add.at(visit_counts, extra_ix, 1)

            # Expand patient_id list accordingly and shuffle
            ids_expanded: list[str] = []
            for pid, cnt in zip(current_patients_df["patient_id"], visit_counts):
                ids_expanded.extend([pid] * int(cnt))
            np.random.shuffle(ids_expanded)

            year_appointments["patient_id"] = ids_expanded[:n_appts]
            assigned_appointments_df = pd.concat([assigned_appointments_df, year_appointments], ignore_index=True)

        # Final registry with unique patients
        self.patients_df = patients_df.drop_duplicates("patient_id").reset_index(drop=True)

        # Merge minimal demographics into appointments (keep 'sex' for analytics)
        self.appointments_df = assigned_appointments_df.merge(self.patients_df, on="patient_id", how="left")

        # Derive date of birth (DOB) from age at first appointment
        first_appt = self.appointments_df.groupby("patient_id")["appointment_date"].min().reset_index()
        first_appt.rename(columns={"appointment_date": "first_appointment_date"}, inplace=True)
        self.patients_df = self.patients_df.merge(first_appt, on="patient_id", how="left")

        # dob ≈ first_appointment_date - age(years) - random days (0..363)
        self.patients_df["dob"] = self.patients_df.apply(
            lambda r: r["first_appointment_date"]
            - pd.DateOffset(years=int(r["age"]))
            - pd.Timedelta(days=int(np.random.randint(0, 364))),
            axis=1,
        )
        self.patients_df["dob"] = pd.to_datetime(self.patients_df["dob"])
        self.patients_df.drop(columns=["first_appointment_date", "age", "year_joined"], inplace=True, errors="ignore")

        # Merge DOB to appointments and compute age at each appointment_date
        self.appointments_df = self.appointments_df.merge(
            self.patients_df[["patient_id", "dob"]],
            on="patient_id",
            how="left",
        )
        self.appointments_df["age"] = self.appointments_df.apply(
            lambda r: r["appointment_date"].year
            - r["dob"].year
            - ((r["appointment_date"].month, r["appointment_date"].day) < (r["dob"].month, r["dob"].day)),
            axis=1,
        ).astype(int)

        # Age-group binning (primary table keeps 'age' and 'age_group')
        lower = max(self.lower_cutoff, 15) if self.truncated else self.lower_cutoff
        bins = list(range(lower, self.upper_cutoff + 1, self.bin_size)) + [101]
        if self.upper_cutoff < 101:
            labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins) - 2)] + [f"{self.upper_cutoff}+"]
        else:
            labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins) - 1)]

        self.appointments_df["age_group"] = pd.cut(
            self.appointments_df["age"], bins=bins, labels=labels, right=False
        )

        # The main fact table shouldn't carry identifiers that are not needed downstream
        self.appointments_df.drop(
            columns=["name", "appointment_year", "year_joined", "dob"],
            inplace=True,
            errors="ignore",
        )
        return self.patients_df, self.appointments_df

    # ------------------------------------------------------------------
    # Internal methods for categorical distribution generation
    # ------------------------------------------------------------------

    def _pareto_distribution(self, categories: List[str]) -> np.ndarray:
        """
        Create a Pareto-like (power-law) probability vector over `categories`.

        The first category receives the highest probability, decaying as 1/(i+1).
        A small multiplicative noise is applied to avoid perfectly smooth curves.

        Parameters
        ----------
        categories : list[str]
            Category labels (e.g., provider names).

        Returns
        -------
        np.ndarray
            1D array of probabilities summing to 1.0 with length == len(categories).
        """
        if not categories:
            raise ValueError("`categories` must be a non-empty list.")

        # Base ∝ 1/(i+1) produces a heavy tail
        base = np.array([1.0 / (i + 1) for i in range(len(categories))], dtype=float)
        base /= base.sum()

        # Light noise to avoid deterministic splits
        noise = np.random.uniform(1 - self.noise, 1 + self.noise, size=len(categories))
        probs = base * noise
        return probs / probs.sum()

    def _uniform_distribution(self, categories: List[str]) -> np.ndarray:
        """
        Create an almost uniform probability vector over `categories`.

        A small multiplicative noise is applied so repeated calls don't yield
        perfectly identical splits.

        Parameters
        ----------
        categories : list[str]
            Category labels.

        Returns
        -------
        np.ndarray
            1D array of probabilities summing to 1.0.
        """
        if not categories:
            raise ValueError("`categories` must be a non-empty list.")

        base = np.ones(len(categories), dtype=float) / len(categories)
        noise = np.random.uniform(1 - self.noise, 1 + self.noise, size=len(categories))
        probs = base * noise
        return probs / probs.sum()

    def _normal_distribution(self, categories: List[str]) -> np.ndarray:
        """
        Create a bell-shaped (normal-like) probability vector over `categories`.

        The mass is centered near the middle index; tails receive less weight.
        A small noise is applied for realism.

        Parameters
        ----------
        categories : list[str]
            Category labels.

        Returns
        -------
        np.ndarray
            1D array of probabilities summing to 1.0.
        """
        if not categories:
            raise ValueError("`categories` must be a non-empty list.")

        n = len(categories)
        mean_idx = n / 2.0
        std_dev = max(n / 4.0, 1e-6) 

        idx = np.arange(n, dtype=float)
        base = np.exp(-0.5 * ((idx - mean_idx) / std_dev) ** 2)
        base /= base.sum()

        noise = np.random.uniform(1 - self.noise, 1 + self.noise, size=n)
        probs = base * noise
        return probs / probs.sum()

    # ------------------------------------------------------------------
    # Add custom categorical column to patients_df
    # ------------------------------------------------------------------

    def add_custom_column(
        self,
        column_name: str,
        categories: List[str],
        *,
        distribution_type: str = "normal",
        custom_probs: Optional[List[float]] = None
    ) -> None:
        """
        Add a synthetic categorical column to `patients_df` using a chosen distribution.

        Intended for adding auxiliary attributes (e.g., insurance, region) *after*
        `generate()` so `patients_df` is populated.

        Parameters
        ----------
        column_name : str
            Name of the new column to create in `patients_df`.
        categories : list[str]
            Available category labels to sample from.
        distribution_type : {"pareto","uniform","normal"}, default "normal"
            Family of probabilities used if `custom_probs` is not provided.
        custom_probs : list[float], optional
            Custom probability vector aligned to `categories`. Must sum to 1.

        Raises
        ------
        ValueError
            If `patients_df` is empty; if `categories` is empty; if
            `custom_probs` length mismatches categories or does not sum to ~1.
        """
        if self.patients_df.empty:
            raise ValueError(
                "patients_df is empty. Call `generate()` first to populate the patient registry."
            )
        if not categories:
            raise ValueError("`categories` must be a non-empty list.")
        if column_name in self.patients_df.columns:
            # Be explicit and avoid silent overwrite
            raise ValueError(f"Column '{column_name}' already exists in patients_df.")

        # Select probability vector
        if custom_probs is not None:
            if len(custom_probs) != len(categories):
                raise ValueError("`custom_probs` length must match `categories` length.")
            total = float(sum(custom_probs))
            if not np.isfinite(total) or total <= 0:
                raise ValueError("`custom_probs` must sum to a positive finite value.")
            probs = np.array(custom_probs, dtype=float) / total
        else:
            dist = distribution_type.lower()
            if dist == "pareto":
                probs = self._pareto_distribution(categories)
            elif dist == "uniform":
                probs = self._uniform_distribution(categories)
            elif dist == "normal":
                probs = self._normal_distribution(categories)
            else:
                raise ValueError("`distribution_type` must be 'pareto', 'uniform', or 'normal'.")

        # Sample and assign
        self.patients_df[column_name] = np.random.choice(
            categories,
            size=len(self.patients_df),
            p=probs
        )

    def to_csv(
        self,
        *,
        slots_path: "os.PathLike[str] | str",
        patients_path: "os.PathLike[str] | str",
        appointments_path: "os.PathLike[str] | str",
        index: bool = False,
    ) -> None:
        """
        Generate the three output tables and write them to CSV files.

        Parameters
        ----------
        slots_path : path-like
            Destination path for ``slots.csv``.
        patients_path : path-like
            Destination path for ``patients.csv``.
        appointments_path : path-like
            Destination path for ``appointments.csv``.
        index : bool, default False
            Whether to write the pandas index to files.

        Notes
        -----
        This is a convenience wrapper around :meth:`generate`.
        """
        slots, appts, pats = self.generate()
        slots.to_csv(slots_path, index=index)
        pats.to_csv(patients_path, index=index)
        appts.to_csv(appointments_path, index=index)

    # ------------------------------------------------------------------------
    # Main pipeline method to generate slots, appointments, and patients
    # ------------------------------------------------------------------------
    def generate(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Run the full synthetic data pipeline in a deterministic, testable order.

        Steps
        -----
        1) Build the slot calendar (`generate_slots`).
        2) Simulate bookings, cancellations, rebooking, and future scheduling
           (`generate_appointments`) and assign realistic execution times for
           attended visits (`assign_actual_times`).
        3) Generate/assign synthetic patients with turnover logic, and compute
           age at each appointment date (`assign_patients`).

        Returns
        -------
        (slots_df, appointments_df, patients_df) : tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
            - `slots_df`: all slots with availability.
            - `appointments_df`: master table with full analytic fields
              (IDs, dates, status, timing; and **age** & **age_group** per visit).
            - `patients_df`: unique patient registry (IDs, names, sex, dob).

        Notes
        -----
        • `appointments_df` is intentionally designed to be the primary analytics table, so
          downstream analyses can use a single source of truth and *optionally* ignore
          `slots_df` and `patients_df`.
        • Age is computed per appointment from each patient's inferred DOB to reflect
          that age depends on the visit date.
        """
        # 1) Slots
        self.slots_df = self.generate_slots()
        self.total_slots = len(self.slots_df)
        self.total_slots_past = int((self.slots_df["appointment_date"] < self.ref_date).sum())

        # Scheduling bounds for lead-time draws
        self.earliest_appointment_date = self.slots_df["appointment_date"].min().normalize()
        self.latest_appointment_date = self.slots_df["appointment_date"].max().normalize()
        self.earliest_scheduling_date = self.earliest_appointment_date - timedelta(days=self.booking_horizon)
        self.slots_per_date = self.slots_df.groupby("appointment_date").size()

        # 2) Appointments (past + future) + actual timing for attended
        self.generate_appointments()

        # Derived calendar extent (for expected patient counts)
        date_span_days = int(
            (self.appointments_df["appointment_date"].max() - self.appointments_df["appointment_date"].min()).days
        )
        self.total_years = max(int(np.ceil(date_span_days / 365.25)), 1)
        self.total_appointments = len(self.appointments_df)
        self.expected_visits_per_patient = self.visits_per_year * self.total_years

        # 3) Patients and age-at-visit enrichment
        self.assign_patients()

        # Return in canonical order
        return self.slots_df, self.appointments_df, self.patients_df
