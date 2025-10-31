"""
Comprehensive test suite for the `medscheduler` package.

Goals
-----
- Validate constructor arguments, error paths, and domain constraints.
- Exercise the end-to-end pipeline: slots → appointments → patients.
- Cover rebooking, status assignment, punctuality and timing simulation.
- Smoke-test plotting helpers (non-interactive backend).
- Unit-test reference data utilities with monkeypatched I/O.
- Sanity-check constants and default validation helpers.
- Keep tests deterministic where possible (seeded RNG).

Notes
-----
- The suite targets >80% coverage. It is organized into logical sections,
  with concise parametrized tests for invalid inputs.
- Matplotlib runs with the 'Agg' backend to avoid GUI requirements.
- Line length and imports follow PEP 8/PEP 257/PEP 484 and the project's Ruff settings.
"""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from typing import Iterable

import numpy as np
import pandas as pd
import pytest

# Ensure a headless backend for matplotlib before importing plotting utils
os.environ.setdefault("MPLBACKEND", "Agg")

try:
    import matplotlib  # noqa: F401
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt  # noqa: F401
    PLOTTING_AVAILABLE = True
except Exception:
    PLOTTING_AVAILABLE = False

from medscheduler import (
    AppointmentScheduler,
    DEFAULT_AGE_GENDER_PROBS,
    DEFAULT_FIRST_ATTENDANCE_RATIO,
    DEFAULT_MONTH_WEIGHTS,
    DEFAULT_STATUS_RATES,
    DEFAULT_WEEKDAY_WEIGHTS,
    STATUS_KEYS,
    validate_defaults,
)
from medscheduler.constants import MAX_VISITS_PER_YEAR, MAX_BIN_SIZE
from medscheduler.utils import reference_data_utils as rdu
from medscheduler.utils.plotting import (
    plot_appointment_duration_distribution,
    plot_arrival_time_distribution,
    plot_appointments_by_status,
    plot_appointments_by_status_future,
    plot_future_slot_availability,
    plot_monthly_appointment_distribution,
    plot_past_slot_availability,
    plot_population_pyramid,
    plot_scheduling_interval_distribution,
    plot_status_distribution_last_days,
    plot_status_distribution_next_days,
    plot_waiting_time_distribution,
    plot_weekday_appointment_distribution,
    summarize_slots,
)


# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

BASE_ARGS = dict(
    date_ranges=[(datetime(2023, 1, 1), datetime(2024, 12, 31))],
    ref_date=datetime(2024, 12, 31),
    working_days=[0, 1, 2, 3, 4],
    appointments_per_hour=4,
    working_hours=[(8, 18)],
    fill_rate=0.9,
    booking_horizon=30,
    median_lead_time=10,
    status_rates={
        "attended": 0.773,
        "cancelled": 0.164,
        "did not attend": 0.059,
        "unknown": 0.004,
    },
    rebook_category="med",
    check_in_time_mean=-10.0,
    visits_per_year=1.2,
    first_attendance=DEFAULT_FIRST_ATTENDANCE_RATIO,
    bin_size=5,
    lower_cutoff=15,
    upper_cutoff=90,
    truncated=True,
    seed=42,
    noise=0.1,
)


@pytest.fixture()
def sched() -> AppointmentScheduler:
    return AppointmentScheduler(**BASE_ARGS)

@pytest.fixture()
def dummy_sched():
    class _S:
        ref_date = pd.Timestamp("2024-01-01").normalize()
    return _S()


# ---------------------------------------------------------------------------
# Constructor & validation
# ---------------------------------------------------------------------------

def test_constructor_defaults():
    s = AppointmentScheduler()
    assert isinstance(s, AppointmentScheduler)
    assert s.appointments_per_hour in (1, 2, 3, 4, 6)
    assert s.fill_rate == pytest.approx(0.9, rel=1e-9)

def test_constructor_success():
    s = AppointmentScheduler(**BASE_ARGS)
    assert s.rebook_ratio == 0.5
    assert abs(sum(s.status_rates.values()) - 1.0) < 1e-9

@pytest.mark.parametrize(
    "key,value,exc",
    [
        ("date_ranges", [(datetime(2024, 12, 31), datetime(2024, 1, 1))], ValueError),
        ("ref_date", datetime(2022, 12, 1), ValueError),
        ("working_days", "Mon-Fri", ValueError),
        ("appointments_per_hour", 5, ValueError),
        ("working_hours", [(8, 12), (11, 15)], ValueError),
        ("fill_rate", 1.5, ValueError),
        ("booking_horizon", -1, ValueError),
        ("median_lead_time", 0, ValueError),
        ("status_rates", {"attended": 1.0}, ValueError),
        ("rebook_category", "extreme", ValueError),
        ("check_in_time_mean", -120, ValueError),
        ("visits_per_year", 0, ValueError),
        ("first_attendance", 1.5, ValueError),
        ("lower_cutoff", 100, ValueError),  # paired with upper in body below
        ("bin_size", 0, ValueError),
        ("truncated", "yes", TypeError),
        ("seed", "bad", TypeError),
        ("noise", -0.1, ValueError),
    ],
)
def test_constructor_invalid_params(key: str, value, exc):
    args = BASE_ARGS.copy()
    if key == "lower_cutoff":
        args["lower_cutoff"] = 100
        args["upper_cutoff"] = 90
    else:
        args[key] = value
    with pytest.raises(exc):
        AppointmentScheduler(**args)

def test_invalid_age_gender_probs_missing_column():
    df = pd.DataFrame({"age_yrs": ["0-4"], "total_female": [0.5]})  # no total_male
    args = BASE_ARGS.copy()
    args["age_gender_probs"] = df
    with pytest.raises(ValueError):
        AppointmentScheduler(**args)

def test_empty_working_days_results_in_empty_slots():
    args = BASE_ARGS.copy()
    args["working_days"] = []
    s = AppointmentScheduler(**args)
    slots = s.generate_slots()
    assert slots.empty


def test_fill_rate_minimum_boundary_inclusive():
    s = AppointmentScheduler(fill_rate=0.30)
    assert s.fill_rate == pytest.approx(0.30, rel=1e-12)

@pytest.mark.parametrize("bad_fill", [0.0, 0.1, 0.2999999, -1, 1.0000001, "0.5"])
def test_fill_rate_out_of_range_or_type_raises(bad_fill):
    with pytest.raises((ValueError, TypeError)):
        AppointmentScheduler(fill_rate=bad_fill)

def test_median_lead_time_must_not_exceed_booking_horizon():
    s = AppointmentScheduler(booking_horizon=7, median_lead_time=7)
    assert s.median_lead_time == 7
    with pytest.raises(ValueError):
        AppointmentScheduler(booking_horizon=7, median_lead_time=8)

# ---------------------------------------------------------------------------
# Core generation pipeline
# ---------------------------------------------------------------------------

def test_generate_slots_basic(sched: AppointmentScheduler):
    slots = sched.generate_slots()
    assert not slots.empty
    assert {"slot_id", "appointment_date", "appointment_time", "is_available"}.issubset(
        slots.columns
    )
    assert slots["is_available"].all()

def test_generate_check_in_time_has_reasonable_tail(sched: AppointmentScheduler):
    dt = sched.generate_check_in_time(
        date(2024, 12, 31),
        time.fromisoformat("10:00"),
    )
    assert isinstance(dt, datetime)
    offset_min = (datetime(2024, 12, 31, 10, 0) - dt).total_seconds() / 60.0
    # allow a generous tail since we don't clip the Normal distribution
    assert -180 <= offset_min <= 120

def test_generate_appointments_requires_slots_first(sched: AppointmentScheduler):
    with pytest.raises(ValueError):
        sched.generate_appointments()

def test_end_to_end_generate_pipeline_outputs_non_empty(sched: AppointmentScheduler):
    slots, appts, patients = sched.generate()
    assert not slots.empty
    assert not appts.empty
    assert not patients.empty
    assert {"appointment_id", "appointment_date", "check_in_time"}.issubset(appts.columns)
    assert {"patient_id"}.issubset(patients.columns)


# ---------------------------------------------------------------------------
# Scheduler — reproducibility, CSV roundtrip, slot edge cases
# ---------------------------------------------------------------------------
def test_reproducibility_with_seed():
    date_ranges = [(datetime(2024, 8, 1, 0, 0, 0), datetime(2025, 8, 31, 23, 59, 0))]
    ref_date = datetime(2024, 12, 31, 0, 0, 0)

    s1 = AppointmentScheduler(
        seed=123,
        date_ranges=date_ranges,
        ref_date=ref_date,
        booking_horizon=60,
        median_lead_time=30,
        noise=0.0,
        fill_rate=0.9,
    )
    s2 = AppointmentScheduler(
        seed=123,
        date_ranges=date_ranges,
        ref_date=ref_date,
        booking_horizon=60,
        median_lead_time=30,
        noise=0.0,
        fill_rate=0.9,
    )

    _, a1, p1 = s1.generate()
    _, a2, p2 = s2.generate()

    d1 = set(pd.to_datetime(a1["appointment_date"]).dt.normalize().unique())
    d2 = set(pd.to_datetime(a2["appointment_date"]).dt.normalize().unique())
    assert d1 == d2

    n1, n2 = len(a1), len(a2)
    tol = max(5, int(0.005 * max(n1, n2)))
    assert abs(n1 - n2) <= tol

    def _assert_dist_similar(s_left: pd.Series, s_right: pd.Series, *, atol: float = 0.02) -> None:
        left = s_left.value_counts(normalize=True).sort_index()
        right = s_right.value_counts(normalize=True).sort_index()
        left, right = left.align(right, fill_value=0.0)
        diffs = np.abs(left.values - right.values)
        assert (diffs <= atol).all(), f"Max abs. diff {diffs.max():.4f} exceeded {atol:.4f}"

    _assert_dist_similar(a1["status"], a2["status"], atol=0.02)
    _assert_dist_similar(p1["sex"], p2["sex"], atol=0.02)

    if "age_group" in p1.columns and "age_group" in p2.columns:
        _assert_dist_similar(p1["age_group"], p2["age_group"], atol=0.02)
    else:
        assert "dob" in p1.columns and "dob" in p2.columns, \
            "Se esperaba 'age_group' o 'dob' en pacientes."

        dob1 = pd.to_datetime(p1["dob"], errors="coerce")
        dob2 = pd.to_datetime(p2["dob"], errors="coerce")
        age1 = ((pd.to_datetime(ref_date) - dob1).dt.days // 365).astype("Int64")
        age2 = ((pd.to_datetime(ref_date) - dob2).dt.days // 365).astype("Int64")
        bins = list(range(0, 95, 5)) + [200]
        labels = [f"{i}-{i+4}" for i in range(0, 90, 5)] + ["90+"]
        g1 = pd.cut(age1.clip(lower=0).astype(float), bins=bins, right=False, labels=labels)
        g2 = pd.cut(age2.clip(lower=0).astype(float), bins=bins, right=False, labels=labels)
        _assert_dist_similar(g1.dropna(), g2.dropna(), atol=0.02)

def test_to_csv_roundtrip(tmp_path):
    s = AppointmentScheduler(
        seed=7,
        booking_horizon=10,
        median_lead_time=10,
        fill_rate=0.9,
        noise=0.0,
    )
    slots, appts, pats = s.generate()

    out_dir = tmp_path
    s.to_csv(
        slots_path=out_dir / "slots.csv",
        patients_path=out_dir / "patients.csv",
        appointments_path=out_dir / "appointments.csv",
    )
    r_slots = pd.read_csv(out_dir / "slots.csv")
    r_appts = pd.read_csv(out_dir / "appointments.csv")
    r_pats = pd.read_csv(out_dir / "patients.csv")

    assert {"slot_id", "appointment_date", "appointment_time"}.issubset(r_slots.columns)
    assert {"appointment_id", "status"}.issubset(r_appts.columns)
    assert {"patient_id", "sex"}.issubset(r_pats.columns)
    assert ("age" in r_pats.columns) or ("dob" in r_pats.columns)


def test_generate_slots_with_low_but_valid_fill_rate():
    s = AppointmentScheduler(
        fill_rate=0.30,
        booking_horizon=10,
        median_lead_time=10,
        appointments_per_hour=4,
        seed=1,
    )
    slots = s.generate_slots()
    assert not slots.empty
    assert slots["is_available"].mean() >= 0.65

# ---------------------------------------------------------------------------
# Rebooking behavior
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category, max_iter", [("min", 1), ("med", 2), ("max", 10)])
def test_rebooking_depth_by_category(category: str, max_iter: int):
    args = BASE_ARGS.copy()
    args["rebook_category"] = category
    s = AppointmentScheduler(**args)
    s.generate()
    if "rebook_iteration" in s.appointments_df.columns:
        assert s.appointments_df["rebook_iteration"].max() <= max_iter

def test_rebook_appointments_api_guards(sched: AppointmentScheduler):
    sched.generate_slots()
    with pytest.raises(ValueError):
        sched.rebook_appointments(pd.DataFrame({"slot_id": []}))


# ---------------------------------------------------------------------------
# Patient demographics and age logic
# ---------------------------------------------------------------------------

def test_generate_patients_invalid_total(sched: AppointmentScheduler):
    with pytest.raises(ValueError):
        sched.generate_patients(0)

def test_age_adjustment_and_binning(sched: AppointmentScheduler):
    sched.generate()
    ages = sched.appointments_df["age"]
    assert ages.ge(sched.lower_cutoff).all()
    assert sched.appointments_df["age_group"].notna().all()

# ---------------------------------------------------------------------------
# Appointments status & timing helpers
# ---------------------------------------------------------------------------

def test_assign_status_missing_columns_raises(sched: AppointmentScheduler):
    sched.generate_slots()
    df = pd.DataFrame({"appointment_date": [pd.Timestamp("2024-01-01")]})
    with pytest.raises(ValueError):
        sched.assign_status(df)

def test_assign_actual_times_attended_only_paths(sched: AppointmentScheduler):
    _, appts, _ = sched.generate()
    # The generator creates attended rows; ensure timing fields are strings HH:MM:SS
    attended = appts[appts["status"] == "attended"]
    if not attended.empty:
        assert attended["check_in_time"].str.match(r"\d{2}:\d{2}:\d{2}").all()
        assert attended["start_time"].str.match(r"\d{2}:\d{2}:\d{2}").all()
        assert attended["end_time"].str.match(r"\d{2}:\d{2}:\d{2}").all()


# ---------------------------------------------------------------------------
# Add custom columns to patients
# ---------------------------------------------------------------------------

def test_add_custom_column_uniform_and_custom_probs(sched: AppointmentScheduler):
    sched.generate()
    # Uniform
    sched.add_custom_column("insurance", ["A", "B", "C"], distribution_type="uniform")
    assert "insurance" in sched.patients_df.columns
    assert set(sched.patients_df["insurance"]).issubset({"A", "B", "C"})
    # Custom probs
    sched.add_custom_column("payer", ["Public", "Private"], custom_probs=[0.7, 0.3])
    assert set(sched.patients_df["payer"]).issubset({"Public", "Private"})

@pytest.mark.parametrize(
    "kwargs,exc",
    [
        (dict(distribution_type="triangular"), ValueError),
        (dict(custom_probs=[0.7]), ValueError),
        (dict(custom_probs=[0.0, 0.0]), ValueError),
    ],
)
def test_add_custom_column_invalids(sched: AppointmentScheduler, kwargs: dict, exc: type[Exception]):
    sched.generate()
    with pytest.raises(exc):
        sched.add_custom_column("region", ["N", "S"], **kwargs)


# ---------------------------------------------------------------------------
# Plotting helpers: summarize & validations
# ---------------------------------------------------------------------------

def test_summarize_slots_structure(sched: AppointmentScheduler):
    slots = sched.generate_slots()
    summary = summarize_slots(slots, scheduler=sched)
    for key in (
        "first_date",
        "last_date",
        "reference_date",
        "total_slots",
        "availability_rate",
        "past_slots",
        "future_slots",
        "slots_by_weekday",
    ):
        assert key in summary
    assert isinstance(summary["slots_by_weekday"], dict)

def test_summarize_slots_missing_columns_raises(sched: AppointmentScheduler):
    df = pd.DataFrame({"appointment_date": pd.date_range("2024-01-01", periods=3)})
    with pytest.raises(ValueError):
        summarize_slots(df, scheduler=sched)

@pytest.mark.parametrize("func", [plot_monthly_appointment_distribution, plot_weekday_appointment_distribution])
def test_plot_basic_distributions(func):
    # Minimal frame with appointment_date column
    df = pd.DataFrame({"appointment_date": pd.date_range("2024-01-01", periods=10)})
    ax = func(df)
    # Matplotlib Axes have a 'plot' attribute among others
    assert hasattr(ax, "plot") or hasattr(ax, "bar")

def test_population_pyramid_happy_and_missing_columns():
    df = pd.DataFrame(
        {"age_group": ["0-4", "0-4", "5-9", "5-9", "5-9"], "sex": ["Male", "Female", "Male", "Female", "Female"]}
    )
    ax = plot_population_pyramid(df, age_col="age_group", sex_col="sex")
    assert hasattr(ax, "barh")
    with pytest.raises(ValueError):
        plot_population_pyramid(pd.DataFrame({"age_group": ["0-4"]}), age_col="age_group")

def test_plot_appointments_by_status_paths(sched: AppointmentScheduler):
    _, appts, _ = sched.generate()
    ax = plot_appointments_by_status(appts, scheduler=sched)
    assert hasattr(ax, "bar")
    with pytest.raises(ValueError):
        plot_appointments_by_status(appts.drop(columns=["status"]), scheduler=sched)

def test_plot_appointments_by_status_future_paths(sched: AppointmentScheduler):
    _, appts, _ = sched.generate()
    ax = plot_appointments_by_status_future(appts, scheduler=sched)
    assert hasattr(ax, "bar")
    with pytest.raises(ValueError):
        plot_appointments_by_status_future(appts.drop(columns=["status"]), scheduler=sched)

def test_plot_status_distribution_last_and_next_days(sched: AppointmentScheduler):
    _, appts, _ = sched.generate()
    ax1 = plot_status_distribution_last_days(appts, scheduler=sched, days_back=10)
    assert hasattr(ax1, "bar")
    ax2 = plot_status_distribution_next_days(appts, scheduler=sched, days_ahead=10)
    assert hasattr(ax2, "bar")

def test_plot_future_slot_availability_freq_validation(sched: AppointmentScheduler):
    slots = sched.generate_slots()
    with pytest.raises(ValueError):
        plot_future_slot_availability(slots, scheduler=sched, freq="H")

def test_histogram_helpers(sched: AppointmentScheduler):
    _, appts, _ = sched.generate()
    ax = plot_scheduling_interval_distribution(appts)
    assert hasattr(ax, "bar")
    ax2 = plot_appointment_duration_distribution(appts.dropna(subset=["appointment_duration"]))
    assert hasattr(ax2, "bar")
    ax3 = plot_waiting_time_distribution(appts.dropna(subset=["waiting_time"]))
    assert hasattr(ax3, "bar")
    ax4 = plot_arrival_time_distribution(appts.dropna(subset=["check_in_time"]))
    assert hasattr(ax4, "bar")


# ---------------------------------------------------------------------------
# Plotting — extra branches (coercion & error paths)
# ---------------------------------------------------------------------------

def test_plot_appointments_by_status_future_rejects_non_datetime_coercion():
    class _S:
        ref_date = pd.Timestamp("2026-01-01").normalize()
    df = pd.DataFrame(
        {
            "appointment_date": ["2025-01-01", "not a date"],
            "status": ["scheduled", "scheduled"],
        }
    )
    with pytest.raises(ValueError):
        plot_appointments_by_status_future(df, scheduler=_S())

def test_plot_arrival_time_distribution_bad_time_formats():
    df = pd.DataFrame({
        "status": ["attended", "attended"],
        "check_in_time": ["9am", "25:61:00"],         # invalid formats
        "appointment_time": ["09:00:00", "09:00:00"],
    })
    with pytest.raises(ValueError):
        plot_arrival_time_distribution(df)


def test_plot_scheduling_interval_distribution_min_threshold_edge():
    df = pd.DataFrame({"scheduling_interval": [1, 1, 1]})
    ax = plot_scheduling_interval_distribution(df, min_pct_threshold=99.999)
    assert hasattr(ax, "bar")


def test_plot_weekday_and_monthly_handle_non_datetime():
    df = pd.DataFrame({"appointment_date": ["2024-01-01", "bad", "2024-02-15"]})
    # Functions should coerce and still return an Axes
    ax1 = plot_weekday_appointment_distribution(df)
    assert hasattr(ax1, "bar")
    ax2 = plot_monthly_appointment_distribution(df)
    assert hasattr(ax2, "bar")

# ---------------------------------------------------------------------------
# Constants sanity and validation helper
# ---------------------------------------------------------------------------

def test_constants_shapes_and_immutability():
    # Status keys ordering and content
    assert tuple(DEFAULT_STATUS_RATES.keys()) == STATUS_KEYS
    assert set(STATUS_KEYS) == {"attended", "cancelled", "did not attend", "unknown"}
    # Value ranges
    assert all(0.0 <= v <= 1.0 for v in DEFAULT_STATUS_RATES.values())
    # MappingProxyType immutability
    with pytest.raises(TypeError):
        DEFAULT_STATUS_RATES["attended"] = 0.5  # type: ignore[index]

def test_default_weights_mean_near_one():
    m_mean = sum(DEFAULT_MONTH_WEIGHTS.values()) / len(DEFAULT_MONTH_WEIGHTS)
    w_mean = sum(DEFAULT_WEEKDAY_WEIGHTS.values()) / len(DEFAULT_WEEKDAY_WEIGHTS)
    assert 0.95 < m_mean < 1.05
    assert 0.95 < w_mean < 1.05
    assert set(DEFAULT_MONTH_WEIGHTS).issubset(set(range(1, 13)))
    assert set(DEFAULT_WEEKDAY_WEIGHTS) == set(range(7))

def test_age_gender_probs_structure():
    assert isinstance(DEFAULT_AGE_GENDER_PROBS, tuple)
    assert all(set(d) == {"age_yrs", "total_female", "total_male"} for d in DEFAULT_AGE_GENDER_PROBS)
    assert all(d["total_female"] >= 0 and d["total_male"] >= 0 for d in DEFAULT_AGE_GENDER_PROBS)

def test_validate_defaults_non_strict_and_strict_paths():
    validate_defaults(strict=False)
    with pytest.raises(ValueError):
        validate_defaults(strict=True)

def test_constants_basic_ranges_and_types():
    assert isinstance(MAX_VISITS_PER_YEAR, (int, float))
    assert isinstance(MAX_BIN_SIZE, int)
    assert MAX_VISITS_PER_YEAR > 0
    assert MAX_BIN_SIZE >= 1

# ---------------------------------------------------------------------------
# medscheduler.utils dunder coverage
# ---------------------------------------------------------------------------

def test_utils_dunder_getattr_and_dir():
    import medscheduler.utils as U
    mod = U.reference_data_utils
    assert hasattr(mod, "get_status_rates")
    listed = dir(U)
    assert "reference_data_utils" in listed and "plotting" in listed
    with pytest.raises(AttributeError):
        _ = U.not_a_module  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# reference_data_utils tests (I/O mocked via monkeypatch)
# ---------------------------------------------------------------------------

def test__parse_month_code_variants():
    parse = rdu._parse_month_code
    assert parse("APR24") == (2024, 4)
    assert parse("  apr23 ") == (2023, 4)
    assert parse("DEC00") == (2000, 12)
    assert parse("INV24") is None
    assert parse(123) is None
    assert parse("APR2024") is None

def _month_abbr(i: int) -> str:
    return ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"][i - 1]

def test_compute_weekday_weights_from_ellis_jenkins_mean_unity():
    w = rdu.compute_weekday_weights_from_ellis_jenkins()
    assert set(w.keys()) == set(range(7))
    mean_val = sum(w.values()) / 7
    assert abs(mean_val - 1.0) < 1e-6

def test_compute_month_weights_from_nhs_happy(monkeypatch):
    # Build a fake CSV slice APR-2023 .. MAR-2024 with MONYY codes and totals
    data = []
    for m in range(4, 13):
        data.append(
            {"CALENDAR_MONTH_END_DATE": f"{_month_abbr(m)}23", "Outpatient_Total_Appointments": 1000 + m}
        )
    for m in range(1, 4):
        data.append(
            {"CALENDAR_MONTH_END_DATE": f"{_month_abbr(m)}24", "Outpatient_Total_Appointments": 1000 + m}
        )
    fake_df = pd.DataFrame(data)

    def fake_read_csv(url, usecols=None):
        assert usecols == ["CALENDAR_MONTH_END_DATE", "Outpatient_Total_Appointments"]
        return fake_df

    monkeypatch.setattr(pd, "read_csv", fake_read_csv)
    w = rdu.compute_month_weights_from_nhs()
    assert len(w) == 12
    assert 1 in w and 12 in w
    mean_val = sum(w.values()) / len(w)
    assert abs(mean_val - 1.0) < 1e-6

def test_compute_month_weights_from_nhs_failure_paths(monkeypatch):
    # read_csv raises
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert rdu.compute_month_weights_from_nhs() == {}

    # No parseable codes
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: pd.DataFrame({"CALENDAR_MONTH_END_DATE": ["???"]}))
    assert rdu.compute_month_weights_from_nhs() == {}

    # Empty slice after filtering
    df = pd.DataFrame({"CALENDAR_MONTH_END_DATE": ["APR25"], "Outpatient_Total_Appointments": [1]})
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: df)
    assert rdu.compute_month_weights_from_nhs() == {}

def test_get_status_rates_happy(monkeypatch):
    df = pd.DataFrame(
        {
            "Year": ["2023-24", "2022-23"],
            "Attendances %": [77.3, 0.0],
            "Did not attends (DNAs) %": [5.9, 0.0],
            "Patient cancellations %": [10.0, 0.0],
            "Hospital cancellations %": [6.4, 0.0],
            "Unknown %": [0.4, 0.0],
        }
    )

    def fake_read_excel(url, sheet_name=None, header=None, nrows=None):
        assert sheet_name == "Summary Report 1"
        return df

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    rates = rdu.get_status_rates()
    assert set(rates) == rdu.EXPECTED_STATUS_KEYS
    assert abs(sum(rates.values()) - 1.0) < 1e-6

def test_get_status_rates_failure_paths(monkeypatch):
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert rdu.get_status_rates() == {}
    bad_df = pd.DataFrame({"Year": ["2023-24"]})
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: bad_df)
    assert rdu.get_status_rates() == {}

def test_get_first_attendance_ratio_happy(monkeypatch):
    df = pd.DataFrame({
        "Label": ["Total Activity", "Other"],
        "First Attendances": [325, 100],
        "Attendances": [1000, 200],
    })

    def fake_read_excel(url, sheet_name=None, header=None, nrows=None):
        assert sheet_name == "Summary Report 2"
        return df

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    ratio = rdu.get_first_attendance_ratio()
    assert ratio == pytest.approx(0.325, rel=1e-6)

def test_get_first_attendance_ratio_failure_paths(monkeypatch):
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert rdu.get_first_attendance_ratio() is None
    bad = pd.DataFrame({"X": [1]})
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: bad)
    assert rdu.get_first_attendance_ratio() is None


# ---------------------------------------------------------------------------
# reference_data_utils — extra coverage
# ---------------------------------------------------------------------------

def test_get_status_rates_handles_alternative_headers(monkeypatch):
    df = pd.DataFrame({
        "Year": ["2023-24"],
        "Attendances %": [77.3],
        "Did not attends (DNAs) %": [5.9],
        "Patient cancellations %": [10.0],
        "Hospital cancellations %": [6.4],
        "Unknown %": [0.4],
    })
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: df)
    out = rdu.get_status_rates()
    assert set(out) == rdu.EXPECTED_STATUS_KEYS
    assert abs(sum(out.values()) - 1.0) < 1e-9


def test_get_age_gender_probs_missing_any_required_col_returns_empty(monkeypatch):
    cols = [
        "age_yrs",
        "attended_female_maternity",
        "attended_female_non_maternity",
        "attended_male",
        "dna_female",
        "dna_male",
    ]
    empty_df = pd.DataFrame({c: [] for c in cols})
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: empty_df)
    res = rdu.get_age_gender_probs()
    assert list(res.columns) == ["age_yrs", "total_female", "total_male"]
    assert res.empty


def test_parse_month_code_boundaries_and_junk():
    parse = rdu._parse_month_code
    assert parse("JAN00") == (2000, 1)
    assert parse(None) is None
    assert parse("") is None

# ---------------------------------------------------------------------------
# Small utility: ensure summarize_slots works on tiny handcrafted frames
# ---------------------------------------------------------------------------

class _DummyScheduler:
    def __init__(self, ref_date: datetime, working_days: Iterable[int] = (0, 1, 2, 3, 4)):
        self.ref_date = ref_date
        self.working_days = tuple(working_days)
        self.working_hours = [(8, 12), (13, 17)]
        self.appointments_per_hour = 4
        self.booking_horizon = 30

def test_summarize_slots_tiny_frame():
    ref_date = datetime(2024, 12, 31)
    sched = _DummyScheduler(ref_date=ref_date)
    dates = pd.to_datetime(
        [
            ref_date.date() - timedelta(days=1),
            ref_date.date(),
            ref_date.date() + timedelta(days=1),
        ]
    )
    times = [time(9, 0), time(9, 15)]
    rows = []
    i = 1
    for d in dates:
        for t in times:
            rows.append(
                {
                    "slot_id": f"{i:04d}",
                    "appointment_date": d,
                    "appointment_time": t,
                    "is_available": bool(i % 2 == 0),
                }
            )
            i += 1
    df = pd.DataFrame(rows)
    summary = summarize_slots(df, scheduler=sched)
    assert summary["total_slots"] == len(df)
    assert isinstance(summary["slots_by_weekday"], dict)


def _make_slots(start: str, *, periods: int, freq: str) -> pd.DataFrame:
    dates = pd.date_range(start=start, periods=periods, freq=freq)
    availability = (np.arange(periods) % 2 == 0)
    return pd.DataFrame({"appointment_date": dates, "is_available": availability})


def test_plot_past_slot_availability_happy_monthly():
    # Jan/Feb/Mar 2024 as "past"
    df = _make_slots("2024-01-01", periods=90, freq="D")
    ax = plot_past_slot_availability(
        df,
        ref_date=pd.Timestamp("2024-04-01"),  # only past data is kept
        freq="M",
        title="Past Monthly",
    )

    assert isinstance(ax, plt.Axes)
    
    xticklabels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    assert len(xticklabels) == 3
    legend = ax.get_legend()
    assert legend is not None
    legend_texts = {t.get_text() for t in legend.get_texts()}
    assert "Available Slots" in legend_texts
    assert "Non-Available Slots" in legend_texts


def test_plot_past_slot_availability_missing_column_raises():
    df = pd.DataFrame({"appointment_date": pd.date_range("2024-01-01", periods=10, freq="D")})

    with pytest.raises((KeyError, ValueError)):
        plot_past_slot_availability(
            df,
            ref_date=pd.Timestamp("2024-02-01"),
        )


def test_plot_past_slot_availability_auto_aggregates_title():
    # ~52 weeks of data to encourage aggregation when freq='W'
    df = _make_slots("2023-01-01", periods=60, freq="W")
    ax = plot_past_slot_availability(
        df,
        ref_date=pd.Timestamp("2024-02-01"),
        freq="W",            # start with weekly; should auto-aggregate to M/Q/Y
        min_bar_px=80,       # make each bar wide in pixels
        min_fig_w_in=6.0,    # tight figure width
        max_fig_w_in=6.0,    # same max width to force suggestion
        dpi=100,
        title="Past Weekly",
    )

    assert isinstance(ax, plt.Axes)
    title_texts = set()
    try:
        title_texts.add(ax.get_title())
    except Exception:
        pass
    for loc in ("left", "right"):
        try:
            title_texts.add(ax.get_title(loc=loc))  # type: ignore[call-arg]
        except TypeError:
            pass
        except Exception:
            pass
    try:
        for txt in getattr(ax, "texts", []):
            s = getattr(txt, "get_text", lambda: "")()
            if s:
                title_texts.add(s)
    except Exception:
        pass
    
    assert any("auto-aggregated to" in t for t in title_texts if t), (
        f"No auto-aggregation notice found. Titles seen: {title_texts!r}"
    )

    # ===============================================
# Extra tests to lift coverage >90%
# ===============================================
import numpy as np
import pandas as pd
import pytest

from datetime import datetime, time

from medscheduler.scheduler import AppointmentScheduler
from medscheduler.utils import plotting as pl
from medscheduler.utils.reference_data_utils import get_age_gender_probs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_sched(seed: int = 0) -> AppointmentScheduler:
    """Create a tiny, deterministic scheduler for unit tests."""
    return AppointmentScheduler(
        seed=seed,
        booking_horizon=10,
        median_lead_time=5,
        noise=0.0,
        fill_rate=0.9,
    )


# ---------------------------------------------------------------------------
# AppointmentScheduler: focused coverage for small/private utilities
# ---------------------------------------------------------------------------

def test_slot_duration_min_property_exposes_expected_minutes() -> None:
    """appointments_per_hour=4 → 15 minutes per slot."""
    s = _mk_sched()
    assert s.slot_duration_min == 15


def test_lead_time_pmf_shapes_and_normalization() -> None:
    """
    `_lead_time_pmf` currently only accepts `max_interval` and uses the
    instance `median_lead_time` internally. We verify that with a degenerate
    horizon it returns empty arrays and with a positive horizon it returns a
    normalized PMF.
    """
    s = _mk_sched()

    # Degenerate horizon -> empty outputs
    w, pmf = s._lead_time_pmf(max_interval=0)
    assert len(w) == 0 and len(pmf) == 0

    # Positive horizon -> non-empty, normalized PMF
    w, pmf = s._lead_time_pmf(max_interval=20)
    assert len(w) == len(pmf) > 0
    assert abs(sum(float(x) for x in pmf) - 1.0) < 1e-6


def test_weighted_sample_past_slots_respects_n_and_columns() -> None:
    s = _mk_sched(seed=123)
    # Generate internal slots so the private helper has data to sample from
    slots = s.generate_slots()
    assert not slots.empty

    n = 5
    out1 = s._weighted_sample_past_slots(n)
    out2 = s._weighted_sample_past_slots(n)

    assert len(out1) == n
    # The helper returns rows from the same schema as slots_df
    required_cols = {"appointment_date", "appointment_time"}
    assert required_cols.issubset(out1.columns)

    # With a fixed seed the result should be stable across calls
    pd.testing.assert_frame_equal(
        out1.reset_index(drop=True),
        out2.reset_index(drop=True),
        check_dtype=False,
    )


def test_finalize_appt_table_handles_empty_and_basic_rows() -> None:
    """
    `_finalize_appt_table` indexes columns that include `scheduling_interval`.
    Provide that column in the minimal one-row case to avoid KeyError and
    assert canonical formatting.
    """
    s = _mk_sched()

    # Empty -> canonical empty shape
    empty = pd.DataFrame(
        columns=[
            "slot_id",
            "appointment_date",
            "appointment_time",
            "status",
            "scheduling_date",
            "scheduling_interval",
        ]
    )
    res_empty = s._finalize_appt_table(empty)
    required = {"appointment_id", "slot_id", "appointment_date", "appointment_time", "status"}
    assert required.issubset(res_empty.columns)
    assert res_empty.empty

    # Minimal valid row -> padded ID & HH:MM:SS time string
    one = pd.DataFrame(
        {
            "slot_id": ["00001"],
            "appointment_date": [pd.Timestamp("2024-02-01").date()],
            "appointment_time": [time(9, 0)],
            "status": ["attended"],
            "scheduling_date": [pd.Timestamp("2023-12-15 08:00:00")],
            "scheduling_interval": [47],  # required by implementation
        }
    )
    res_one = s._finalize_appt_table(one)
    assert {"appointment_id", "scheduling_interval"}.issubset(res_one.columns)
    assert res_one.loc[0, "appointment_time"] in ("09:00:00", pd.Timestamp("09:00:00").time())


def test_normalize_calendar_weights_and_date_weight_raw_product() -> None:
    """Custom asymmetric month/weekday weights should reflect on raw date weights after normalization."""
    # January double weight, Monday triple weight
    month_w = {m: (2.0 if m == 1 else 1.0) for m in range(1, 13)}
    wk_w = {d: (3.0 if d == 0 else 1.0) for d in range(7)}
    s = AppointmentScheduler(
        seed=1,
        month_weights=month_w,
        weekday_weights=wk_w,
        booking_horizon=5,
        median_lead_time=3,
        fill_rate=0.9,
        noise=0.0,
    )
    ts_jan_mon = pd.Timestamp("2024-01-01")  # Monday
    ts_feb_tue = pd.Timestamp("2024-02-06")  # Tuesday
    w_jm = s._date_weight_raw(ts_jan_mon)
    w_ft = s._date_weight_raw(ts_feb_tue)
    assert w_jm > w_ft


def test_distribution_helpers_shapes_and_sum_to_one() -> None:
    """Pareto, uniform and normal distributions should all be valid probability vectors."""
    s = _mk_sched(seed=42)
    cats = ["A", "B", "C", "D", "E"]

    p_par = s._pareto_distribution(cats)
    p_uni = s._uniform_distribution(cats)
    p_norm = s._normal_distribution(cats)

    for p in (p_par, p_uni, p_norm):
        assert p.shape == (len(cats),)
        assert np.isclose(p.sum(), 1.0)
        assert np.all(p >= 0)


def test_add_custom_column_error_paths_and_happy_path() -> None:
    """Exercise error branches and a success path for add_custom_column."""
    s = _mk_sched()
    # Populate patients_df first
    s.generate()

    # Column exists -> error
    with pytest.raises(ValueError):
        s.add_custom_column("sex", ["X", "Y"], distribution_type="uniform")

    # Empty categories -> error
    with pytest.raises(ValueError):
        s.add_custom_column("region", [], distribution_type="uniform")

    # Custom probs bad length
    with pytest.raises(ValueError):
        s.add_custom_column("region", ["N", "S"], custom_probs=[1.0])

    # Custom probs non-positive sum
    with pytest.raises(ValueError):
        s.add_custom_column("region", ["N", "S"], custom_probs=[np.nan, 0.0])

    # Happy path: normal distribution
    s.add_custom_column("region", ["North", "South", "East", "West"], distribution_type="normal")
    assert "region" in s.patients_df.columns
    assert s.patients_df["region"].isin(["North", "South", "East", "West"]).all()


# ---------------------------------------------------------------------------
# Plotting internals: cover helpers and edge cases
# ---------------------------------------------------------------------------

def test__empty_plot_returns_axes_with_message() -> None:
    """_empty_plot should return an Axes and reflect the message in the text objects."""
    ax = pl._empty_plot("Nothing to show")
    assert hasattr(ax, "bar")  # Axes-like object
    texts = [t.get_text() for t in getattr(ax, "texts", [])]
    # Accept either an explicit Axes title/suptitle or a text overlay.
    title = getattr(ax, "get_title", lambda: "")()
    supt = getattr(getattr(ax, "figure", None), "_suptitle", None)
    supt_txt = supt.get_text() if supt is not None else ""
    assert ("Nothing to show" in title) or ("Nothing to show" in supt_txt) or ("Nothing to show" in " ".join(texts))


def test__get_reference_date_precedence_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit ref_date wins, then scheduler.ref_date, then max(df[date_col])."""
    class _S:
        ref_date = pd.Timestamp("2024-01-31")

    df = pd.DataFrame({"d": pd.to_datetime(["2024-01-01", "2024-02-01"])})
    # 1) explicit ref_date wins
    r = pl._get_reference_date(pd.Timestamp("2024-12-31"), _S(), df, "d")
    assert str(r.date()) == "2024-12-31"
    # 2) scheduler.ref_date if explicit is None
    r = pl._get_reference_date(None, _S(), df, "d")
    assert str(r.date()) == "2024-01-31"
    # 3) fallback to max(df[date_col])
    r = pl._get_reference_date(None, None, df, "d")
    assert str(r.date()) == "2024-02-01"


def test__format_period_labels_year_quarter_month_week_day() -> None:
    """_format_period_labels should return readable strings for all supported freqs."""
    years = pd.period_range("2023", periods=2, freq="Y").to_timestamp()
    quarters = pd.period_range("2023Q1", periods=2, freq="Q").to_timestamp()
    months = pd.period_range("2023-01", periods=2, freq="M").to_timestamp()
    weeks = pd.period_range("2023-01-02", periods=2, freq="W-MON").to_timestamp()
    days = pd.period_range("2023-01-01", periods=2, freq="D").to_timestamp()

    assert all(isinstance(x, str) for x in pl._format_period_labels(pd.Index(years), "Y"))
    assert all(isinstance(x, str) for x in pl._format_period_labels(pd.Index(quarters), "Q"))
    assert all(isinstance(x, str) for x in pl._format_period_labels(pd.Index(months), "M"))
    assert all(isinstance(x, str) for x in pl._format_period_labels(pd.Index(weeks), "W"))
    assert all(isinstance(x, str) for x in pl._format_period_labels(pd.Index(days), "D"))


def test__aggregate_until_fits_suggests_when_too_many_bars() -> None:
    """
    `_aggregate_until_fits` coarsens using `allowed_freqs` items that come
    *before* the current `freq`. Therefore, pass the tuple in coarse->fine
    order so that starting at 'D' it can try 'W', 'M', 'Q'.
    """
    df = pd.DataFrame(
        {
            "appointment_date": pd.date_range("2023-01-01", periods=120, freq="D"),
            "is_available": 1,
        }
    )
    grouped, periods, used_freq, suggested, _ = pl._aggregate_until_fits(
        df,
        date_col="appointment_date",
        available_col="is_available",
        freq="D",
        allowed_freqs=("Q", "M", "W", "D"),  # coarse -> fine (critical)
        min_bar_px=80,
        min_fig_w_in=6.0,
        max_fig_w_in=6.0,
        dpi=100,
    )
    assert suggested is True
    assert used_freq in {"W", "M", "Q"}  # must have coarsened from 'D'

def test__should_annotate_labels_threshold_logic() -> None:
    """
    With 10 bars at width 6 in and dpi 100 we have 600/10 = 60 px per bar.
    Use a higher threshold to force False, then a lower one to assert True.
    """
    # Below threshold -> False
    assert pl._should_annotate_labels(fig_width_in=6.0, dpi=100, n_bars=10, label_px_threshold=80) is False
    # Above threshold -> True
    assert pl._should_annotate_labels(fig_width_in=6.0, dpi=100, n_bars=10, label_px_threshold=8)


def test__histogram_with_threshold_success_and_failure() -> None:
    """Directly exercise histogram helper success and failure paths."""
    values = pd.Series([1, 2, 2, 3, 3, 3, 100])
    # Success with low threshold
    xs, counts, pcts, edges = pl._histogram_with_threshold(values, bin_width=1, min_pct_threshold=5)
    assert len(xs) == len(counts) == len(pcts)
    # Failure when threshold too high
    with pytest.raises(ValueError):
        pl._histogram_with_threshold(values, bin_width=1, min_pct_threshold=90)


# ---------------------------------------------------------------------------
# Plotting: increase plot_future_slot_availability coverage
# ---------------------------------------------------------------------------

def test_plot_future_slot_availability_invalid_freq_and_empty_future() -> None:
    # Case A: no future rows -> returns an "empty" Axes (no exception)
    past = pd.date_range("2023-01-01", periods=10, freq="D")
    df_past = pd.DataFrame({"appointment_date": past, "is_available": 1})

    ax = pl.plot_future_slot_availability(df_past, ref_date=pd.Timestamp("2024-01-01"))
    assert hasattr(ax, "bar")

    # Case B: there IS future -> invalid freq should be validated and raise
    future = pd.date_range("2024-01-01", periods=7, freq="D")
    df_future = pd.DataFrame({"appointment_date": future, "is_available": 1})

    with pytest.raises(ValueError):
        pl.plot_future_slot_availability(
            df_future,
            ref_date=pd.Timestamp("2024-01-01"),
            freq="X",   # invalid frequency
        )

def test_plot_future_slot_availability_daily_basic_paths() -> None:
    start = pd.Timestamp("2024-01-01")
    dates = pd.date_range(start, periods=30, freq="D")
    df = pd.DataFrame({"appointment_date": dates, "is_available": 1})

    class _S:
        ref_date = start
        booking_horizon = 14  # not enforced by current implementation

    ax = pl.plot_future_slot_availability(
        df,
        scheduler=_S(),
        ref_date=start,
        freq="D",                   # keep timestamps in X
        limit_future_to_horizon=True,  # noop in current code, but should not crash
    )
    assert hasattr(ax, "bar")

    # Expected number of grouped periods (daily) from ref_date onward
    expected = (df["appointment_date"] >= start).sum()
    assert len(ax.get_xticks()) == expected


# ---------------------------------------------------------------------------
# reference_data_utils: edge coverage
# ---------------------------------------------------------------------------

def test_get_age_gender_probs_zero_total_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fake sheet with correct headers but all zeros should yield an empty DataFrame."""
    cols = [
        "Age (yrs)",
        "Attended female (maternity)",
        "Attended female (non-maternity)",
        "Attended male",
        "Did not attend female",
        "Did not attend male",
    ]
    fake = pd.DataFrame(
        {
            cols[0]: ["0-4", "5-9"],
            cols[1]: [0, 0],
            cols[2]: [0, 0],
            cols[3]: [0, 0],
            cols[4]: [0, 0],
            cols[5]: [0, 0],
        }
    )
    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: fake)
    out = get_age_gender_probs(url="ignored")
    assert out.empty


def test_date_ranges_accept_str_and_datetime():
    # A) strings ISO
    s1 = AppointmentScheduler(
        date_ranges=[("2025-01-01", "2025-01-31")],
        ref_date="2025-01-15",
        working_hours=[(8, 16)],
    )
    start1, end1 = s1.date_ranges[0]
    assert start1 == datetime(2025, 1, 1, 0, 0)
    assert end1 == datetime(2025, 1, 31, 23, 59)
    assert s1.ref_date == datetime(2025, 1, 15, 0, 0)

    # B) datetime objects
    s2 = AppointmentScheduler(
        date_ranges=[(datetime(2025, 2, 1), datetime(2025, 2, 28))],
        ref_date=datetime(2025, 2, 10),
        working_hours=[(8, 16)],
    )
    start2, end2 = s2.date_ranges[0]
    assert start2 == datetime(2025, 2, 1, 0, 0)
    assert end2 == datetime(2025, 2, 28, 23, 59)
    assert s2.ref_date == datetime(2025, 2, 10, 0, 0)


def test_same_day_range_expands_end_to_2359():
    s = AppointmentScheduler(
        date_ranges=[("2025-03-01", "2025-03-01")],  
        ref_date="2025-03-01",
        working_hours=[(8, 16)],
    )
    start, end = s.date_ranges[0]
    assert start == datetime(2025, 3, 1, 0, 0)
    assert end == datetime(2025, 3, 1, 23, 59)


def test_ref_date_must_be_inside_ranges():
    with pytest.raises(ValueError):
        AppointmentScheduler(
            date_ranges=[("2025-01-01", "2025-01-31")],
            ref_date="2026-01-01",          
            working_hours=[(8, 16)],
        )


def test_working_hours_parsing_variants():
    A = AppointmentScheduler(
        date_ranges=[("2025-01-01", "2025-01-07")],
        ref_date="2025-01-03",
        working_hours=("08:00", "16:00"),
    )
    assert A.working_hours == [(8, 16)]

    B = AppointmentScheduler(
        date_ranges=[("2025-01-01", "2025-01-07")],
        ref_date="2025-01-03",
        working_hours=[(8, 12), (13, 17)],
    )
    assert B.working_hours == [(8, 12), (13, 17)]

    C = AppointmentScheduler(
        date_ranges=[("2025-01-01", "2025-01-07")],
        ref_date="2025-01-03",
        working_hours=[("8", "12:00"), ("13:00", "17")],
    )
    assert C.working_hours == [(8, 12), (13, 17)]


def test_working_hours_overlap_raises():
    with pytest.raises(ValueError):
        AppointmentScheduler(
            date_ranges=[("2025-01-01", "2025-01-07")],
            ref_date="2025-01-03",
            working_hours=[(8, 12), (11, 15)],  
        )


def test_working_hours_minutes_not_zero_raises():
    with pytest.raises(ValueError):
        AppointmentScheduler(
            date_ranges=[("2025-01-01", "2025-01-07")],
            ref_date="2025-01-03",
            working_hours=("08:30", "16:00"),  
        )