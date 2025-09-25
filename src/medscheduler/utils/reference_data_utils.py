"""
Reference data utilities for the synthetic outpatient scheduler.

This module centralizes small, testable helpers that download and parse
reference statistics used to calibrate the simulation:

- Monthly relative weights (Apr 2023–Mar 2024) from NHS England provisional
  monthly open-data totals for outpatients (no month reindexing performed).
- Weekday relative weights derived from Ellis & Jenkins (2012) Mon–Fri
  appointment counts, with Sat/Sun extrapolated via a simple linear fit.
- Demographic proportions (age × sex), first‑attendance ratio, and appointment
  status rates read from the NHS outpatient workbook.

Guidance
--------
Run these computations once during development and persist results in
`constants.py` for deterministic simulations and to avoid repeated downloads.

Data sources
------------
1) NHS Hospital Outpatient Activity 2023–24 (Workbook; Hospital Episode Statistics).
   - Sheet names used:
       * "Summary Report 1" → status rates
       * "Summary Report 2" → first‑attendance ratio
       * "Summary Report 3" → age × sex proportions
   - URL: https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx

2) NHS Provisional Monthly Hospital Episode Statistics (Open Data – Totals) CSV.
   - Columns used: CALENDAR_MONTH_END_DATE, Outpatient_Total_Appointments
   - URL: https://files.digital.nhs.uk/57/C50E24/HES_M1_OPEN_DATA.csv

3) Ellis, D. A., & Jenkins, R. (2012). Weekday affects attendance rate for
   medical appointments: Large-scale data analysis and implications.
   PLOS ONE, 7(12), e51365. https://doi.org/10.1371/journal.pone.0051365
   - Table 1 (Mon–Fri counts) used to infer weekday weights.

Notes
-----
- Functions fail “softly”: they log and return empty values (e.g., `{}`, `None`,
  empty `DataFrame`) rather than raising, to keep the library resilient in
  offline or upstream‑change scenarios.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Final, Optional, Pattern, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

__all__ = [
    # Source URLs
    "NHS_OUTPATIENT_URL",
    "NHS_MONTHLY_OPEN_DATA_CSV",
    # NHS workbook extracts
    "get_age_gender_probs",
    "get_first_attendance_ratio",
    "get_status_rates",
    # Weights
    "compute_weekday_weights_from_ellis_jenkins",
    "compute_month_weights_from_nhs",
]

# ---------------------------------------------------------------------------
# Public source pointers
# ---------------------------------------------------------------------------

# NHS outpatient workbook (HES 2023–24)
NHS_OUTPATIENT_URL: Final[str] = (
    "https://files.digital.nhs.uk/34/18846B/hosp-epis-stat-outp-rep-tabs-2023-24-tab.xlsx"
)

# Provisional Monthly HES Open Data (Totals) CSV
NHS_MONTHLY_OPEN_DATA_CSV: Final[str] = (
    "https://files.digital.nhs.uk/57/C50E24/HES_M1_OPEN_DATA.csv"
)

# ---------------------------------------------------------------------------
# Constants & validation
# ---------------------------------------------------------------------------

EXPECTED_STATUS_KEYS: Final[frozenset[str]] = frozenset(
    {"attended", "cancelled", "did not attend", "unknown"}
)

# Ellis & Jenkins (2012), Table 1: Mon–Fri appointment counts (n)
# doi:10.1371/journal.pone.0051365.t001
_EJ12_MON_FRI_APPOINTMENTS: Final[Dict[str, int]] = {
    "Monday": 967_912,
    "Tuesday": 1_032_417,
    "Wednesday": 957_447,
    "Thursday": 887_960,
    "Friday": 617_633,
}

# Month-code parsing (strict MONYY, e.g., 'APR24')
_MONTH_ABBR_TO_NUM: Final[Dict[str, int]] = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}
_MONTH_CODE_RE: Final[Pattern[str]] = re.compile(r"^\s*([A-Z]{3})\s*(\d{2})\s*$")


def _parse_month_code(code: str) -> Optional[Tuple[int, int]]:
    """
    Parse a strict MONYY code (e.g., 'APR24') into (year, month).

    Two‑digit years are interpreted as 20YY (e.g., '23' → 2023). Returns None
    if there is no match or the month abbreviation is unknown.
    """
    if not isinstance(code, str):
        return None
    match = _MONTH_CODE_RE.match(code.upper())
    if not match:
        return None
    mon_abbr, yy = match.group(1), int(match.group(2))
    month = _MONTH_ABBR_TO_NUM.get(mon_abbr)
    if month is None:
        return None
    return 2000 + yy, month


# ---------------------------------------------------------------------------
# NHS workbook extracts (small, testable functions)
# ---------------------------------------------------------------------------

def get_age_gender_probs(url: str = NHS_OUTPATIENT_URL) -> pd.DataFrame:
    """
    Return age–sex proportions from the workbook sheet 'Summary Report 3'.

    Returns
    -------
    pd.DataFrame
        Columns: ['age_yrs', 'total_female', 'total_male'] with values in [0, 1].

    Notes
    -----
    The female total is computed as attended_female_maternity +
    attended_female_non_maternity; totals are then normalized over
    (attended_female, attended_male, dna_female, dna_male).
    """
    try:
        df = pd.read_excel(url, sheet_name="Summary Report 3", header=5, nrows=20)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read 'Summary Report 3': %s", exc)
        return pd.DataFrame(columns=["age_yrs", "total_female", "total_male"])

    df.columns = [
        "age_yrs",
        "attended_female_maternity",
        "attended_female_non_maternity",
        "attended_male",
        "dna_female",
        "dna_male",
    ]
    df["attended_female"] = (
        df["attended_female_maternity"] + df["attended_female_non_maternity"]
    )
    rel_cols = ["attended_female", "attended_male", "dna_female", "dna_male"]

    # Robust normalization (coerce to float, guard zero/NaN)
    total = float(pd.to_numeric(df[rel_cols].stack(), errors="coerce").sum())
    if not np.isfinite(total) or total <= 0:
        logger.warning("Total count for age–sex distribution is zero or non‑numeric.")
        return pd.DataFrame(columns=["age_yrs", "total_female", "total_male"])

    df[rel_cols] = df[rel_cols] / total
    df["total_female"] = df["attended_female"] + df["dna_female"]
    df["total_male"] = df["attended_male"] + df["dna_male"]
    return df[["age_yrs", "total_female", "total_male"]].round(5)


def get_first_attendance_ratio(url: str = NHS_OUTPATIENT_URL) -> Optional[float]:
    """
    Return First‑Attendances / Attendances from 'Summary Report 2' (row 'Total Activity').

    Returns
    -------
    float | None
        Ratio rounded to 5 decimals; None if unavailable or invalid.
    """
    try:
        s2 = pd.read_excel(url, sheet_name="Summary Report 2", header=5, nrows=9)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read 'Summary Report 2': %s", exc)
        return None

    try:
        label_col = s2.columns[0]
        row = s2.loc[s2[label_col].astype(str).str.strip().str.casefold() == "total activity"].squeeze()
        first = float(pd.to_numeric(row["First Attendances"], errors="coerce"))
        total = float(pd.to_numeric(row["Attendances"], errors="coerce"))
        if total > 0:
            return round(first / total, 5)
        logger.warning("Invalid denominator for first‑attendance ratio: total=%s", total)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("First‑attendance ratio not available: %s", exc)
        return None


def get_status_rates(url: str = NHS_OUTPATIENT_URL) -> Dict[str, float]:
    """
    Return appointment outcome rates from 'Summary Report 1' (row '2023-24').

    Returns
    -------
    dict
        Keys: {'attended','cancelled','did not attend','unknown'} with probabilities in [0, 1].
    """
    try:
        s1 = pd.read_excel(url, sheet_name="Summary Report 1", header=5, nrows=12)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read 'Summary Report 1': %s", exc)
        return {}

    try:
        row = s1.loc[s1["Year"].astype(str).str.strip() == "2023-24"].squeeze()
        rates = {
            "attended": float(pd.to_numeric(row.get("Attendances %"), errors="coerce")) / 100.0,
            "did not attend": float(pd.to_numeric(row.get("Did not attends (DNAs) %"), errors="coerce")) / 100.0,
            "cancelled": (
                float(pd.to_numeric(row.get("Patient cancellations %"), errors="coerce")) +
                float(pd.to_numeric(row.get("Hospital cancellations %"), errors="coerce"))
            ) / 100.0,
            "unknown": float(pd.to_numeric(row.get("Unknown %"), errors="coerce")) / 100.0,
        }

        if set(rates) != EXPECTED_STATUS_KEYS or any(not np.isfinite(v) for v in rates.values()):
            raise ValueError("Unexpected or non‑finite status keys/values in Summary Report 1.")

        return {k: round(v, 3) for k, v in rates.items()}
    except Exception as exc:  # noqa: BLE001
        logger.error("Status rates not available: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Weekday relative weights (Mon–Sun)
# ---------------------------------------------------------------------------

def compute_weekday_weights_from_ellis_jenkins() -> Dict[int, float]:
    """
    Compute weekday relative weights (Mon..Sun) using Mon–Fri appointment counts
    from Ellis & Jenkins (2012) Table 1 (PLoS ONE; doi:10.1371/journal.pone.0051365.t001).
    Saturday/Sunday are extrapolated via a linear fit over Mon–Fri shares.

    Returns
    -------
    dict
        Keys 0..6 (Mon..Sun). Values are relative weights with mean == 1.0,
        rounded to 3 decimals.
    """
    df = pd.DataFrame(_EJ12_MON_FRI_APPOINTMENTS.items(), columns=["Day", "Appointments"])
    shares = (df["Appointments"] / df["Appointments"].sum()).to_numpy(dtype="float64")

    x = np.arange(shares.size, dtype="float64")
    poly = np.poly1d(np.polyfit(x, shares, deg=1))

    # Predict weekend shares; clip at 0 to avoid negatives
    sat_share = max(float(poly(5)), 0.0)
    sun_share = max(float(poly(6)), 0.0)

    shares_full = np.concatenate([shares, [sat_share, sun_share]])
    shares_norm = shares_full / shares_full.sum()
    rel = shares_norm / shares_norm.mean()

    return {i: float(np.round(w, 3)) for i, w in enumerate(rel)}


# ---------------------------------------------------------------------------
# Monthly relative weights (Apr 2023 – Mar 2024) from NHS open data CSV
# ---------------------------------------------------------------------------

def compute_month_weights_from_nhs(
    url: str = NHS_MONTHLY_OPEN_DATA_CSV,
) -> Dict[int, float]:
    """
    Compute monthly relative weights from NHS provisional monthly Open Data totals
    for outpatients, using strict MONYY codes in CALENDAR_MONTH_END_DATE (e.g., 'APR24').

    Period filtered: Apr 2023 – Mar 2024 (inclusive).

    Returns
    -------
    dict
        Keys are calendar month numbers present in the filtered slice (e.g., {4..12,1..3}).
        Values are relative weights (mean == 1.0 across the returned months), rounded to 3 decimals.

    Notes
    -----
    This function does not reindex or impute missing months. If the CSV slice
    lacks any month in Apr 2023–Mar 2024, the output will contain fewer than
    twelve keys and will log a warning.
    """
    date_col = "CALENDAR_MONTH_END_DATE"
    total_col = "Outpatient_Total_Appointments"

    try:
        df = pd.read_csv(url, usecols=[date_col, total_col])
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load monthly CSV from %s: %s", url, exc)
        return {}

    # Parse strict MONYY codes via regex
    ym = df[date_col].apply(_parse_month_code)
    if not ym.notna().any():
        logger.error("No valid MONYY codes found in %s.", date_col)
        return {}

    work = df.loc[ym.notna()].copy()
    work[["year", "month"]] = pd.DataFrame(ym[ym.notna()].tolist(), index=work.index)

    # Filter Apr 2023 .. Mar 2024 (inclusive)
    mask = (
        ((work["year"] == 2023) & (work["month"].between(4, 12)))
        | ((work["year"] == 2024) & (work["month"].between(1, 3)))
    )
    work = work.loc[mask, ["year", "month", total_col]]

    if work.empty:
        logger.warning("No rows for Apr 2023 – Mar 2024 in monthly CSV (MONYY parsing).")
        return {}

    # Aggregate by (year, month) and sort chronologically
    monthly = (
        work.groupby(["year", "month"], as_index=False)[total_col]
        .sum()
        .sort_values(["year", "month"])
    )

    if len(monthly) != 12:
        logger.warning("Expected 12 rows (Apr 2023 – Mar 2024), got %d.", len(monthly))

    totals = monthly[total_col].to_numpy(dtype="float64")
    denom = totals.sum()
    if not np.isfinite(denom) or denom <= 0:
        logger.warning("Sum of Outpatient_Total_Appointments is zero or non‑numeric.")
        return {}

    shares = totals / denom
    rel = shares / shares.mean()

    # Keys are the actual calendar months present (no reindexing or fill)
    months = monthly["month"].tolist()  # e.g., [4..12, 1..3] if all present
    return {int(m): float(np.round(w, 3)) for m, w in zip(months, rel)}
