from __future__ import annotations

import pandas as pd
import numpy as np
import calendar
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Tuple, List, Sequence


# ==== Unified color palette for all plots ====
COLORS = {
    # base
    "primary":   "#67A7D4",
    "secondary": "#F9A369",
    "grid":      "#E5E7EB",
    "text":      "#222222",

    # availability
    "available":   "#43AD7E",
    "unavailable": "#FF6F61",

    # demographics
    "male":   "#4583B5",
    "female": "#EF7A84",

    # status
    "attended":  "#B69DE1",
    "cancelled": "#B3C1F2",
    "did not attend": "#BDE3F0", 
    "unknown":   "#E5E5E5",
    "scheduled": "#CD77B6",
}

@dataclass(frozen=True)
class SlotSummary:
    """
    Immutable container for summary metrics derived from an appointment slots table.

    Attributes
    ----------
    first_date : str
        Earliest appointment date in the dataset (YYYY-MM-DD).
    last_date : str
        Latest appointment date in the dataset (YYYY-MM-DD).
    reference_date : str
        Date used to split past vs. future metrics (YYYY-MM-DD).

    total_slots : int
        Total number of slots in the dataset.
    total_operating_days : int
        Number of calendar days between first and last slot date (inclusive).
    total_working_days : int
        Number of unique days with at least one slot.

    slots_per_working_day_mean : float
        Average number of slots per working day.
    slots_per_week : int
        Number of slots per week, computed from scheduler configuration.

    availability_rate : float
        Proportion of slots marked as available across the entire dataset (0–1).

    past_slots : int
        Count of slots before the reference date.
    past_filled_slots : int
        Count of past slots that are booked (unavailable).
    past_fill_rate : float
        Proportion of past slots that are booked (0–1).

    future_slots : int
        Count of slots on or after the reference date.
    future_filled_slots : int
        Count of future slots that are booked (unavailable).
    future_fill_rate : float
        Proportion of future slots that are booked (0–1).

    slots_by_weekday : Dict[str, int]
        Distribution of slots by weekday abbreviation (Mon, Tue, etc.).
    """

    first_date: str
    last_date: str
    reference_date: str

    total_slots: int
    total_operating_days: int
    total_working_days: int

    slots_per_working_day_mean: float
    slots_per_week: int

    availability_rate: float

    past_slots: int
    past_filled_slots: int
    past_fill_rate: float

    future_slots: int
    future_filled_slots: int
    future_fill_rate: float

    slots_by_weekday: Dict[str, int]


def summarize_slots(
    df: pd.DataFrame,
    scheduler: object,
    date_col: str = "appointment_date",
    available_col: str = "is_available",
) -> Dict[str, Any]:
    """
    Summarize calendar and availability metrics from a slots table.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least `date_col` and `available_col`.
    scheduler : object
        AppointmentScheduler instance providing configuration and `ref_date`.
    date_col : str, default="appointment_date"
        Column name for appointment date.
    available_col : str, default="is_available"
        Column name for availability flag (True/False).

    Returns
    -------
    Dict[str, Any]
        Dictionary representation of a SlotSummary instance.
    """
    if df.empty:
        return SlotSummary(
            first_date="", last_date="", reference_date="",
            total_slots=0, total_operating_days=0, total_working_days=0,
            slots_per_working_day_mean=0.0, slots_per_week=0,
            availability_rate=0.0,
            past_slots=0, past_filled_slots=0, past_fill_rate=0.0,
            future_slots=0, future_filled_slots=0, future_fill_rate=0.0,
            slots_by_weekday={}
        ).__dict__

    # Validate required columns
    missing = [c for c in (date_col, available_col) if c not in df.columns]
    if missing:
        return _empty_plot(f"`df` must include columns: {missing}")

    # Validate scheduler attributes
    required_attrs = ["ref_date", "working_days", "working_hours", "appointments_per_hour"]
    for attr in required_attrs:
        if not hasattr(scheduler, attr):
            return _empty_plot(f"Scheduler must have attribute `{attr}`.")

    # Reference date
    ref_ts = pd.to_datetime(scheduler.ref_date).normalize()

    # Parse and clean dates
    dates = pd.to_datetime(df[date_col], errors="coerce")
    df = df.loc[dates.notna()].copy()
    dates = dates.loc[dates.notna()]

    # Ensure availability is boolean
    if df[available_col].dtype != bool:
        df[available_col] = df[available_col].astype(bool)

    # Calendar range and totals
    min_date = dates.min()
    max_date = dates.max()
    total_operating_days = int((max_date - min_date).days) + 1
    total_working_days = int(dates.dt.date.nunique())
    total_slots = int(len(df))

    # Mean slots per working day
    slots_per_working_day_mean = (
        float(df.groupby(dates.dt.date).size().mean())
        if total_working_days else 0.0
    )

    # Slots per week from scheduler config
    working_days_count = len(scheduler.working_days)
    daily_slots = sum((end - start) * scheduler.appointments_per_hour
                      for start, end in scheduler.working_hours)
    slots_per_week = working_days_count * daily_slots

    # Availability rate
    available_slots_total = int(df[available_col].sum())
    availability_rate = available_slots_total / total_slots

    # Past/future segmentation
    past_mask = dates < ref_ts
    past_df = df.loc[past_mask]
    future_df = df.loc[~past_mask]

    past_slots = int(len(past_df))
    past_filled_slots = int((~past_df[available_col]).sum())
    past_fill_rate = past_filled_slots / past_slots if past_slots else 0.0

    future_slots = int(len(future_df))
    future_filled_slots = int((~future_df[available_col]).sum())
    future_fill_rate = future_filled_slots / future_slots if future_slots else 0.0

    # Weekday distribution
    weekday_counts = df.groupby(dates.dt.weekday).size()
    slots_by_weekday = {calendar.day_abbr[int(k)]: int(v) for k, v in weekday_counts.items()}

    return SlotSummary(
        first_date=min_date.strftime("%Y-%m-%d"),
        last_date=max_date.strftime("%Y-%m-%d"),
        reference_date=ref_ts.strftime("%Y-%m-%d"),
        total_slots=total_slots,
        total_operating_days=total_operating_days,
        total_working_days=total_working_days,
        slots_per_working_day_mean=float(round(slots_per_working_day_mean, 2)),
        slots_per_week=int(slots_per_week),
        availability_rate=float(round(availability_rate, 3)),
        past_slots=past_slots,
        past_filled_slots=past_filled_slots,
        past_fill_rate=float(round(past_fill_rate, 3)),
        future_slots=future_slots,
        future_filled_slots=future_filled_slots,
        future_fill_rate=float(round(future_fill_rate, 3)),
        slots_by_weekday=slots_by_weekday
    ).__dict__


# ============================================================
# Shared helpers
# ============================================================

def _empty_plot(message: str = "Nothing to show") -> plt.Axes:
    """
    Return an Axes with a clear message when there is nothing to plot.
    """
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.axis("off")
    ax.set_title(message)
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12)
    fig.tight_layout()
    return ax


def _get_reference_date(
    ref_date: Optional[Union[str, pd.Timestamp, datetime]],
    scheduler: Optional[object],
    df: pd.DataFrame,
    date_col: str
) -> pd.Timestamp:
    """Resolve reference date from explicit argument, scheduler, or dataset."""
    if ref_date is not None:
        return pd.to_datetime(ref_date, errors="coerce") or pd.Timestamp.today()
    if scheduler is not None and hasattr(scheduler, "ref_date"):
        return pd.to_datetime(scheduler.ref_date, errors="coerce") or pd.Timestamp.today()
    if date_col in df.columns:
        return pd.to_datetime(df[date_col], errors="coerce").max() or pd.Timestamp.today()
    ts = pd.to_datetime(ref_date, errors="coerce")
    return ts if pd.notna(ts) else pd.Timestamp.today()


def _to_period_timestamp(df: pd.DataFrame, date_col: str, freq: str) -> pd.Series:
    """Convert datetime column to period start timestamps for given frequency."""
    return pd.to_datetime(df[date_col], errors="coerce").dt.to_period(freq).dt.to_timestamp()


def _format_period_labels(periods: pd.Index, freq: str) -> List[str]:
    """Format period labels based on frequency."""
    if freq == "Y":
        return [p.strftime("%Y") for p in periods]
    if freq == "Q":
        return [f"{p.year}-Q{((p.month - 1) // 3) + 1}" for p in periods]
    if freq == "M":
        return [p.strftime("%Y-%m") for p in periods]
    if freq == "W":
        return [p.strftime("%G-W%V") for p in periods]
    if freq == "D":
        return [p.strftime("%Y-%m-%d") for p in periods]
    return [str(p) for p in periods]


def _aggregate_until_fits(
    df: pd.DataFrame,
    *,
    date_col: str,
    available_col: str,
    freq: str,
    allowed_freqs: Tuple[str, ...],
    min_bar_px: int,
    min_fig_w_in: float,
    max_fig_w_in: float,
    dpi: int
):
    """Aggregate slot availability until the chart fits in allowed figure width."""
    if freq not in allowed_freqs:
        return _empty_plot(f"freq must be one of {allowed_freqs}, got {freq}")

    start_idx = allowed_freqs.index(freq)
    sequence = [freq] + list(allowed_freqs[:start_idx][::-1])
    suggested = False

    for f in sequence:
        tmp = df.copy()
        tmp["period"] = _to_period_timestamp(tmp, date_col, f)
        grouped = tmp.groupby(["period", available_col]).size().unstack(fill_value=0).sort_index()

        for val in (True, False):
            if val not in grouped.columns:
                grouped[val] = 0

        n = len(grouped.index)
        if n == 0:
            continue

        required_width_in = max(min_fig_w_in, (n * min_bar_px) / dpi)
        if required_width_in <= max_fig_w_in:
            return grouped, grouped.index, f, (f != freq), (required_width_in, 5.5)

    grouped = df.groupby([date_col, available_col]).size().unstack(fill_value=0).sort_index()
    return grouped, grouped.index, freq, True, (max_fig_w_in, 5.5)


def _plot_stacked_bars(ax, x, top_vals, bottom_vals, annotate: bool):
    """Draw stacked bars for available vs non-available slots."""
    bars1 = ax.bar(x, bottom_vals, label="Unavailable Slots", color=COLORS["unavailable"], zorder=3)
    bars2 = ax.bar(x, top_vals, bottom=bottom_vals, label="Available Slots", color=COLORS["available"], zorder=3)

    if annotate:
        totals = (top_vals + bottom_vals)
        for i in range(len(x)):
            if totals[i] <= 0:
                continue
            na_pct = bottom_vals[i] / totals[i] * 100
            a_pct = top_vals[i] / totals[i] * 100
            ax.text(x[i], bottom_vals[i] / 2, f"{na_pct:.0f}%",
                    ha="center", va="center", color="white", fontsize=9, fontweight="bold")
            ax.text(x[i], bottom_vals[i] + (top_vals[i] / 2), f"{a_pct:.0f}%",
                    ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    return bars1, bars2


def _should_annotate_labels(
    fig_width_in: float,
    dpi: int,
    n_bars: int,
    label_px_threshold: int = 8,
) -> bool:
    """
    Decide whether per-bar text annotations are feasible given horizontal density.
    pixels_per_bar = (fig_width_in * dpi) / max(n_bars, 1)
    """
    if n_bars <= 0:
        return False
    pixels_per_bar = (fig_width_in * dpi) / float(n_bars)
    return pixels_per_bar >= float(label_px_threshold)


# ============================================================
# Slot Availability (Past)
# ============================================================

def plot_past_slot_availability(
    slots_df: pd.DataFrame,
    *,
    scheduler: Optional[object] = None,
    ref_date: Optional[Union[str, pd.Timestamp, datetime]] = None,
    date_col: str = "appointment_date",
    available_col: str = "is_available",
    freq: str = "Y",
    min_bar_px: int = 55,
    label_px_threshold: int = 55,
    min_fig_w_in: float = 7.0,
    max_fig_w_in: float = 16.0,
    dpi: int = 100,
    title: str = "Slot Availability (Past)"
) -> plt.Axes:
    """Plot past slot availability by period."""
    if slots_df.empty:
        return _empty_plot("No data")

    ref_date = _get_reference_date(ref_date, scheduler, slots_df, date_col)
    df = slots_df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df[df[date_col] < ref_date]

    if df.empty:
        return _empty_plot("No past data (before ref_date)")

    allowed = ("Y", "Q", "M", "W")
    grouped, periods, used_freq, suggested, figsize = _aggregate_until_fits(
        df, date_col=date_col, available_col=available_col, freq=freq,
        allowed_freqs=allowed, min_bar_px=min_bar_px,
        min_fig_w_in=min_fig_w_in, max_fig_w_in=max_fig_w_in, dpi=dpi
    )

    n = len(periods)
    if n == 0:
        return _empty_plot("No data after grouping")

    if figsize[0] >= max_fig_w_in and (n * min_bar_px) / dpi > max_fig_w_in and used_freq == "Y":
        return _empty_plot("Too many bars for a readable chart at any granularity.")

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    available = _extract_group_1d(grouped, True, periods)
    non_available = _extract_group_1d(grouped, False, periods)
    x = range(n)
    annotate = _should_annotate_labels(
        fig_width_in=figsize[0], dpi=dpi, n_bars=n, label_px_threshold=label_px_threshold
    )
    _plot_stacked_bars(ax, x, available, non_available, annotate=annotate)

    ax.set_xticks(list(x))
    ax.set_xticklabels(_format_period_labels(periods, used_freq),
                       rotation=45 if n > 8 else 0,
                       ha="right" if n > 8 else "center")
    ax.set_xlabel({"Y": "Year", "Q": "Quarter", "M": "Month", "W": "Week"}[used_freq], labelpad=10, fontsize=10.5)
    ax.set_ylabel("Number of Slots", labelpad=10, fontsize=10.5)
    ttl = title + (f"  — auto-aggregated to {used_freq}" if suggested and used_freq != freq else "")
    ax.set_title(ttl, loc="left", fontsize=12, y=1.1, x=-0.05)
    ax.legend(loc="upper right", bbox_to_anchor=(1, 1.15), frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    ax.spines[["right", "top"]].set_visible(False)
    fig.tight_layout()
    return ax


# ============================================================
# Slot Availability (Future)
# ============================================================

def plot_future_slot_availability(
    slots_df: pd.DataFrame,
    *,
    scheduler: Optional[object] = None,
    ref_date: Optional[Union[str, pd.Timestamp]] = None,
    date_col: str = "appointment_date",
    available_col: str = "is_available",
    freq: str = "W",
    limit_future_to_horizon: bool = True, 
    min_bar_px: int = 55,
    label_px_threshold: int = 55,
    min_fig_w_in: float = 7.0,
    max_fig_w_in: float = 16.0,
    dpi: int = 100,
    title: str = "Slot Availability (Future)"
) -> plt.Axes:
    """Plot future slot availability by period."""
    if slots_df.empty:
        return _empty_plot("No data")

    ref_date = _get_reference_date(ref_date, scheduler, slots_df, date_col)
    df = slots_df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if limit_future_to_horizon and scheduler is not None and hasattr(scheduler, "booking_horizon"):
        end = ref_date + timedelta(days=int(scheduler.booking_horizon))
        df = df[(df[date_col] >= ref_date) & (df[date_col] < end)]
    else:
        df = df[df[date_col] >= ref_date]

    if df.empty:
        return _empty_plot("No future data in the selected window")

    if freq not in ("D", "W", "M"):
        raise ValueError("freq must be one of: 'D', 'W', 'M'")
    if freq == "D":
        allowed = ("D",)
    elif freq == "W":
        allowed = ("W", "D")
    else:  # freq == "M"
        allowed = ("M", "W", "D")

    grouped, periods, used_freq, suggested, figsize = _aggregate_until_fits(
        df,
        date_col=date_col,
        available_col=available_col,
        freq=freq,
        allowed_freqs=allowed,
        min_bar_px=min_bar_px,
        min_fig_w_in=min_fig_w_in,
        max_fig_w_in=max_fig_w_in,
        dpi=dpi,
    )

    n = len(periods)
    if n == 0:
        return _empty_plot("No data after grouping")
    if figsize[0] >= max_fig_w_in and (n * min_bar_px) / dpi > max_fig_w_in and used_freq == "M":
        return _empty_plot("Too many bars for a readable chart at any granularity.")

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    def _to_1d(g, key, idx):
        try:
            obj = g.get(key)
        except Exception:
            obj = None
        if obj is None:
            s = pd.Series(0.0, index=idx)
        elif isinstance(obj, pd.DataFrame):
            s = obj.sum(axis=1).astype(float)
        else:
            s = pd.Series(obj, index=getattr(obj, "index", idx)).astype(float)
        if not s.index.equals(idx):
            s = s.reindex(idx, fill_value=0.0)
        return s.to_numpy(dtype=float)

    available = _to_1d(grouped, True, periods)
    non_available = _to_1d(grouped, False, periods)

    x = range(n)
    annotate = _should_annotate_labels(
        fig_width_in=figsize[0], dpi=dpi, n_bars=n, label_px_threshold=label_px_threshold
    )
    _plot_stacked_bars(ax, x, available, non_available, annotate=annotate)

    ax.set_xticks(list(x))
    ax.set_xticklabels(
        _format_period_labels(periods, used_freq),
        rotation=45 if n > 8 else 0,
        ha="right" if n > 8 else "center",
    )
    ax.set_xlabel({"D": "Day", "W": "Week", "M": "Month"}[used_freq], labelpad=10, fontsize=10.5)
    ax.set_ylabel("Number of Slots", labelpad=10, fontsize=10.5)
    add_suffix = (suggested and used_freq != freq)
    ttl = title + (f"  — auto-aggregated to {used_freq}" if add_suffix else "")
    ax.set_title(ttl, loc="left", fontsize=12, y=1.1, x=-0.05)

    ax.legend(loc="upper right", bbox_to_anchor=(1, 1.15), frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    ax.spines[["right", "top"]].set_visible(False)
    fig.tight_layout()
    return ax


# ---------------------------------------------------------------
# Monthly appointment distribution
# ---------------------------------------------------------------

def plot_monthly_appointment_distribution(df: pd.DataFrame) -> plt.Axes:
    """
    Plot the percentage distribution of appointments by month.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing an 'appointment_date' column.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.
    """
    if "appointment_date" not in df.columns:
        raise ValueError("DataFrame must contain an 'appointment_date' column.")

    if not pd.api.types.is_datetime64_any_dtype(df["appointment_date"]):
        df["appointment_date"] = pd.to_datetime(df["appointment_date"], errors="coerce")
    month_counts = (
        df["appointment_date"].dt.month
        .value_counts(normalize=True)
        .reindex(range(1, 13), fill_value=0)
        * 100
    )

    # Month names for x-axis labels
    month_names = [pd.Timestamp(month=m, day=1, year=2000).strftime("%B") for m in range(1, 13)]
    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(month_names, month_counts.values, color=COLORS["primary"], zorder=3, width=0.5)

    # Title and labels
    ax.set_title("Appointment Distribution by Month", loc="left", fontsize=12, y=1.1, x=-0.08)
    ax.set_ylabel("Percentage of Appointments", labelpad=10, fontsize=10.5)
    ax.set_xlabel("Month", labelpad=10, fontsize=10.5)

    # Y-axis limit for padding above bars
    #ax.set_ylim(0, month_counts.values.max() * 1.15)

    # Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    # plt.xticks(rotation=45)

    for bar, pct in zip(bars, month_counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.25,
            f"{pct:.1f}%",
            ha="center", fontsize=9, fontweight="bold", color=COLORS["text"]
        )

    fig.tight_layout()
    return ax


# ---------------------------------------------------------------
# Plot: Daily Appointment Status Distribution last days
# ---------------------------------------------------------------
def plot_status_distribution_last_days(
    df: pd.DataFrame,
    *,
    scheduler: object,
    days_back: int = 30,
    date_col: str = "appointment_date",
    status_col: str = "status"
) -> plt.Axes:
    """
    Plot the daily distribution of appointment statuses for the last N days.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least `date_col` and `status_col`.
    scheduler : object
        Scheduler instance providing a `ref_date` attribute.
    days_back : int, default=30
        Number of days before `ref_date` to include in the plot.
    date_col : str, default="appointment_date"
        Column name containing appointment dates.
    status_col : str, default="status"
        Column name containing appointment statuses.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.

    Raises
    ------
    ValueError
        If required columns are missing or scheduler does not have `ref_date`.
    """
    # --- Column validation
    required_cols = {date_col, status_col}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        return _empty_plot(f"DataFrame must contain columns: {', '.join(missing_cols)}")

    if not hasattr(scheduler, "ref_date"):
        return _empty_plot("Scheduler must have a `ref_date` attribute.")

    # --- Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # --- Filter last N days before ref_date
    ref_date = pd.to_datetime(scheduler.ref_date).normalize()
    start_date = ref_date - pd.Timedelta(days=days_back)
    mask = (df[date_col] < ref_date) & (df[date_col] >= start_date)
    filtered_df = df.loc[mask]

    if filtered_df.empty:
        return _empty_plot(f"No data available in the last {days_back} days before {ref_date.date()}.")

    # --- Group by date and status
    grouped = filtered_df.groupby([date_col, status_col], observed=True).size().unstack(fill_value=0)

    statuses = grouped.columns
    colors = [COLORS[s] for s in statuses]

    # --- Create plot
    dates = grouped.index
    fig, ax = plt.subplots(figsize=(15, 7))

    bottom_values = np.zeros(len(dates))
    for status, color in zip(statuses, colors):
        values = grouped[status]
        ax.bar(
            dates, values, bottom=bottom_values,
            label=status.capitalize(), color=color,
            edgecolor="#ffffff", zorder=3
        )
        bottom_values += values

    # --- Total labels per date
    total_per_date = grouped.sum(axis=1)
    for date, total in zip(dates, total_per_date):
        ax.text(
            date, total + 0.6, str(total),
            ha="center", va="bottom", fontsize=9,
            color=COLORS["text"], fontweight="bold"
        )

    # --- Titles and labels
    ax.set_title(
        f"Appointments Status Distribution (Last {days_back} Days)",
        loc="left", fontsize=12, y=1.27, x=-0.04
    )
    ax.set_xlabel("Date", labelpad=10, fontsize=10.5)
    ax.set_ylabel("Number of Appointments", labelpad=10, fontsize=10.5)
    ax.legend(loc="upper right", bbox_to_anchor=(1.01, 1.3), frameon=False)

    # --- X-axis formatting
    ax.set_xticks(dates)
    ax.set_xticklabels(dates.strftime("%Y-%m-%d"), rotation=45, ha="right")

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin + 0.75, xmax - 0.75)

    fig.tight_layout()
    return ax

# ---------------------------------------------------------------
# Plot: Daily Appointment Status Distribution (Next 30 Days)
# ---------------------------------------------------------------
def plot_status_distribution_next_days(
    df: pd.DataFrame,
    *,
    scheduler: object,
    days_ahead: int = 30,
    date_col: str = "appointment_date",
    status_col: str = "status"
) -> plt.Axes:
    """
    Plot the daily distribution of appointment statuses for the next N days.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least `date_col` and `status_col`.
    scheduler : object
        Scheduler instance providing a `ref_date` attribute.
    days_ahead : int, default=30
        Number of days after `ref_date` to include in the plot.
    date_col : str, default="appointment_date"
        Column name containing appointment dates.
    status_col : str, default="status"
        Column name containing appointment statuses.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.

    Raises
    ------
    ValueError
        If required columns are missing or scheduler does not have `ref_date`.
    """
    # --- Column validation
    required_cols = {date_col, status_col}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame must contain columns: {', '.join(missing_cols)}")

    if not hasattr(scheduler, "ref_date"):
        raise ValueError("Scheduler must have a `ref_date` attribute.")

    # --- Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # --- Filter next N days from ref_date
    ref_date = pd.to_datetime(scheduler.ref_date).normalize()
    end_date = ref_date + pd.Timedelta(days=days_ahead)
    mask = (df[date_col] >= ref_date) & (df[date_col] < end_date)
    filtered_df = df.loc[mask]

    if filtered_df.empty:
        return _empty_plot(f"No data available in the next {days_ahead} days after {ref_date.date()}.")

    # --- Group and ensure column order
    grouped = filtered_df.groupby([date_col, status_col], observed=True).size().unstack(fill_value=0)
    column_order = ["scheduled", "cancelled"]
    grouped = grouped.reindex(columns=column_order, fill_value=0)

    statuses = grouped.columns
    colors = [COLORS[s] for s in statuses]

    # --- Create plot
    dates = grouped.index
    fig, ax = plt.subplots(figsize=(14, 6))

    bottom_values = np.zeros(len(dates))
    for status, color in zip(statuses, colors):
        values = grouped[status]
        ax.bar(
            dates, values, bottom=bottom_values,
            label=status.capitalize(), color=color,
            edgecolor="#ffffff", zorder=3
        )
        bottom_values += values

    # --- Total labels per date
    total_per_date = grouped.sum(axis=1)
    for date, total in zip(dates, total_per_date):
        ax.text(
            date, total + 0.4, str(total),
            ha="center", va="bottom", fontsize=9,
            color=COLORS["text"], fontweight="bold"
        )

    # --- Titles and labels
    ax.set_title(
        f"Appointments Status Distribution (Next {days_ahead} Days)",
        loc="left", fontsize=12, y=1.09, x=-0.04
    )
    ax.set_xlabel("Date", labelpad=10, fontsize=10.5)
    ax.set_ylabel("Number of Appointments", labelpad=10, fontsize=10.5)
    ax.legend(loc="upper right", bbox_to_anchor=(1, 1.1), frameon=False)

    # --- X-axis formatting
    ax.set_xticks(dates)
    ax.set_xticklabels(dates.strftime("%Y-%m-%d"), rotation=45, ha="right")

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin + 0.5, xmax - 0.5)

    fig.tight_layout()
    return ax



def plot_weekday_appointment_distribution(df: pd.DataFrame) -> plt.Axes:
    """
    Plot the percentage distribution of appointments by weekday.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing an 'appointment_date' column.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.
    """
    if "appointment_date" not in df.columns:
        raise ValueError("DataFrame must contain an 'appointment_date' column.")

    # Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df["appointment_date"]):
        df["appointment_date"] = pd.to_datetime(df["appointment_date"], errors="coerce")

    # Calculate weekday distribution
    weekday_counts = (
        df["appointment_date"].dt.day_name()
        .value_counts(normalize=True)
        .reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            fill_value=0
        )
        * 100
    )

    # Create plot
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(weekday_counts.index, weekday_counts.values, color=COLORS["secondary"], width=0.5, zorder=3)

    # Title and labels
    ax.set_title("Appointment Distribution by Weekday", loc="left", fontsize=12, y=1.08, x=-0.1)
    ax.set_ylabel("Percentage of Appointments", labelpad=10, fontsize=10.5)
    ax.set_xlabel("Day", labelpad=10, fontsize=10.5)

    # Y-axis limit for padding above bars
    max_val = weekday_counts.values.max()
    ax.set_ylim(0, max_val * 1.15 if max_val > 0 else 1)

    # Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)

    # Add percentage labels above bars
    for bar, pct in zip(bars, weekday_counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.7,
            f"{pct:.1f}%",
            ha="center", fontsize=9, fontweight="bold", color=COLORS["text"]
        )
    fig.tight_layout()
    return ax

# ---------------------------------------------------------------
# Plot: Population Pyramid by Age and Sex
# ---------------------------------------------------------------
def plot_population_pyramid(
    df: pd.DataFrame,
    *,
    age_col: str = "age_group",
    sex_col: str = "sex",
    male_label: str = "Male",
    female_label: str = "Female"
) -> plt.Axes:
    """
    Plot a population pyramid showing the distribution by age group and sex.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing age group and sex columns.
    age_col : str, default="age_group"
        Column name representing age groups.
    sex_col : str, default="sex"
        Column name representing sex categories.
    male_label : str, default="Male"
        Label identifying male rows in the sex column.
    female_label : str, default="Female"
        Label identifying female rows in the sex column.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.

    Raises
    ------
    ValueError
        If required columns are missing.
    """
    # --- Column validation
    required_cols = {age_col, sex_col}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame must contain columns: {', '.join(missing_cols)}")

    # --- Group counts by age and sex
    gender_counts = (
        df.groupby([age_col, sex_col], observed=True)
        .size()
        .unstack(fill_value=0)
    )

    # --- Ensure both sexes exist
    if male_label not in gender_counts.columns or female_label not in gender_counts.columns:
        raise ValueError(f"Both '{male_label}' and '{female_label}' categories must be present.")

    males = -gender_counts[male_label].values
    females = gender_counts[female_label].values
    total_population = np.sum(gender_counts.values)

    # --- Style parameters
    shift = 0.0055 * len(df)
    label_offset = len(df) / 500
    fontsize = 9
    age_groups = gender_counts.index
    bar_color_male = COLORS["male"]
    bar_color_female = COLORS["female"]

    # --- Create figure
    fig, ax = plt.subplots(figsize=(9, 8))

    bars_male = ax.barh(
        age_groups, males, color=bar_color_male, align="center",
        height=0.75, left=-shift, label=male_label, zorder=3
    )
    bars_female = ax.barh(
        age_groups, females, color=bar_color_female, align="center",
        height=0.75, left=shift, label=female_label, zorder=3
    )

    # --- Axes styling
    ax.yaxis.set_ticks_position("none")
    max_population = max(abs(males).max(), females.max()) * 1.2
    ax.set_xlim(left=-max_population, right=max_population)
    ax.spines[["right", "top"]].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["left"].set_position(("data", shift))
    ax.set_title(
        "Population Distribution by Age and Sex",
        loc="left", fontsize=12, y=1.15, x=-0.05
    )

    # --- Add percentage labels on bars
    for bars, color, ha in [
        (bars_male, bar_color_male, "right"),
        (bars_female, bar_color_female, "left"),
    ]:
        for bar in bars:
            width = float(bar.get_width())
            center_y = float(bar.get_y() + bar.get_height() / 2.0)
            label_x = float(
                bar.get_x()
                + (width - label_offset if ha == "right" else width + label_offset)
            )
            ax.text(
                label_x,
                center_y,
                f"{abs(width) / float(total_population):.1%}",
                va="center",
                ha=ha,
                color=color,
                fontsize=fontsize,
                fontweight="bold",
            )

    # --- Age group labels at the center line (use numeric tick positions)
    yticks = ax.get_yticks()
    for yt, label in zip(yticks, age_groups):
        ax.text(
            0.0,
            float(yt),
            f" {label} ",
            va="center",
            ha="center",
            color="black",
            backgroundcolor="white",
            fontsize=10,
        )

    # --- X-axis formatting
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{int(abs(x))}")
    )
    ax.set_xlabel("Population", labelpad=10, fontsize=10.5)

    # --- Totals annotation
    for text, x, color in [
        (
            f"{female_label}: {np.sum(females)} ({np.sum(females) / total_population:.1%})",
            1, bar_color_female
        ),
        (
            f"{male_label}: {abs(np.sum(males))} ({abs(np.sum(males)) / total_population:.1%})",
            0.18 + (0.00000035 * len(df)), bar_color_male
        )
    ]:
        ax.text(
            x, 1.05, text, transform=ax.transAxes,
            fontsize=10, ha="right", va="bottom", color="white", weight="bold",
            bbox=dict(facecolor=color, edgecolor="none",
                      boxstyle="round, pad=1,rounding_size=0.5")
        )

    fig.tight_layout()
    return ax


def plot_appointments_by_status(
    df: pd.DataFrame,
    *,
    scheduler: object,
    date_col: str = "appointment_date",
    status_col: str = "status"
) -> plt.Axes:
    """
    Plot the percentage distribution of appointments by status.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least `date_col` and `status_col`.
    scheduler : object
        Scheduler instance providing a `ref_date` attribute.
    date_col : str, default="appointment_date"
        Column name containing appointment dates.
    status_col : str, default="status"
        Column name containing appointment statuses.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.

    Raises
    ------
    ValueError
        If required columns are missing or scheduler does not have `ref_date`.
    """
    # --- Column validation
    required_cols = {date_col, status_col}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame must contain columns: {', '.join(missing_cols)}")

    if not hasattr(scheduler, "ref_date"):
        raise ValueError("Scheduler must have a `ref_date` attribute.")

    # --- Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # --- Filter by reference date from scheduler
    ref_date = pd.to_datetime(scheduler.ref_date).normalize()
    df = df[df[date_col] <= ref_date]

    if df.empty:
        return _empty_plot("No data available after filtering by reference date.")

    # --- Calculate percentages by status
    grouped = (
        df[status_col]
        .value_counts(normalize=True)
        .sort_values(ascending=False)
        * 100
    )

    statuses = grouped.index
    percentages = grouped.values
    colors = [COLORS[s] for s in statuses]

    # --- Create plot
    fig, ax = plt.subplots(figsize=(5, 5))
    bars = ax.bar(statuses, percentages, color=colors, width=0.45, zorder=3)

    # --- Titles and labels
    ax.set_title("Appointments by Status", loc="left", fontsize=12, y=1.08, x=-0.15)
    ax.set_xlabel("Status", labelpad=10, fontsize=10.5)
    ax.set_ylabel("Percentage of Appointments", labelpad=10, fontsize=10.5)
    ax.set_ylim(0, percentages.max() * 1.15)

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin - 0.1, xmax)

    # --- Add percentage labels
    for bar, percent in zip(bars, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{percent:.1f}%",
            ha="center", fontsize=9, color=COLORS["text"], fontweight="bold"
        )

    fig.tight_layout()
    return ax



# ---------------------------------------------------------------
# Plot: Appointment Status Distribution (Future)
# ---------------------------------------------------------------
def plot_appointments_by_status_future(
    df: pd.DataFrame,
    *,
    scheduler: object,
    date_col: str = "appointment_date",
    status_col: str = "status"
) -> plt.Axes:
    """
    Plot the percentage distribution of FUTURE appointments by status.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least `date_col` and `status_col`.
    scheduler : object
        Scheduler instance providing a `ref_date` attribute.
    date_col : str, default="appointment_date"
        Column name containing appointment dates.
    status_col : str, default="status"
        Column name containing appointment statuses.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.

    Raises
    ------
    ValueError
        If required columns are missing or scheduler does not have `ref_date`.
    """
    # --- Column validation
    required_cols = {date_col, status_col}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame must contain columns: {', '.join(missing_cols)}")

    if not hasattr(scheduler, "ref_date"):
        raise ValueError("Scheduler must have a `ref_date` attribute.")

    # --- Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # --- Filter FUTURE appointments based on scheduler.ref_date
    ref_date = pd.to_datetime(scheduler.ref_date).normalize()
    df = df[df[date_col] > ref_date]

    if df.empty:
        return _empty_plot("No future appointments available after reference date.")

    # --- Calculate percentages by status
    grouped = (
        df[status_col]
        .value_counts(normalize=True)
        .sort_values(ascending=False)
        * 100
    )

    statuses = grouped.index
    percentages = grouped.values
    colors = [COLORS[s] for s in statuses]

    # --- Create plot
    fig, ax = plt.subplots(figsize=(3, 5))
    bars = ax.bar(statuses, percentages, color=colors, width=0.4, zorder=3)

    # --- Titles and labels
    ax.set_title("Upcoming Appointments by Status", loc="left", fontsize=12, y=1.08, x=-0.35)
    ax.set_xlabel("Status", labelpad=10, fontsize=10.5)
    ax.set_ylabel("Percentage of Appointments", labelpad=10, fontsize=10.5)
    ax.set_ylim(0, percentages.max() * 1.15)

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin - 0.15, xmax)

    # --- Add percentage labels
    for bar, percent in zip(bars, percentages):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{percent:.1f}%",
            ha="center", fontsize=9, color=COLORS["text"], fontweight="bold"
        )

    fig.tight_layout()
    return ax


# ---------------------------------------------------------------
# Plot: Scheduling Interval Distribution
# ---------------------------------------------------------------
def plot_scheduling_interval_distribution(
    df: pd.DataFrame,
    *,
    interval_col: str = "scheduling_interval",
    min_pct_threshold: float = 0.1
) -> plt.Axes:
    """
    Plot the distribution of scheduling intervals in days.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing at least the `interval_col` column.
    interval_col : str, default="scheduling_interval"
        Column name containing scheduling intervals in days.
    min_pct_threshold : float, default=0.1
        Minimum percentage threshold to include a bar in the plot.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.

    Raises
    ------
    ValueError
        If `interval_col` is missing or empty.
    """
    # --- Column validation
    if interval_col not in df.columns:
        raise ValueError(f"DataFrame must contain column '{interval_col}'.")
    if df[interval_col].dropna().empty:
        raise ValueError(f"No data available in column '{interval_col}'.")

    scheduling_intervals = df[interval_col].dropna()

    # --- Create bins and histogram
    bins = range(int(scheduling_intervals.min()), int(scheduling_intervals.max()) + 2)
    counts, edges = np.histogram(scheduling_intervals, bins=bins)
    percentages = (counts / scheduling_intervals.size) * 100

    # --- Filter bins by percentage threshold
    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= min_pct_threshold
    ]
    if not valid_bins:
        return _empty_plot(f"No intervals meet the {min_pct_threshold}% threshold.")

    valid_x = [x for x, _, _ in valid_bins]
    valid_counts = [count for _, count, _ in valid_bins]
    valid_percentages = [pct for _, _, pct in valid_bins]

    # --- Create plot
    fig, ax = plt.subplots(figsize=(16, 5))
    fig.suptitle(
        "How Far in Advance Do Patients Schedule?",
        fontsize=12, x=0.12, y=1.04, ha="center"
    )
    ax.bar(
        valid_x, valid_counts, width=0.9, align="center",
        edgecolor="#ffffff", color=COLORS["primary"], zorder=3
    )

    # --- Axis labels and formatting
    ax.set_xticks(bins[:-1])
    ax.set_xticklabels([int(b) for b in bins[:-1]], ha="center")
    ax.set_xlabel("Scheduling Interval (Days)", labelpad=10, fontsize=10.5)
    ax.set_ylabel("Number of Appointments", labelpad=10, fontsize=10.5)

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin + 1, xmax - 1)

    # --- Add percentage labels
    for x, count, pct in zip(valid_x, valid_counts, valid_percentages):
        ax.text(
            x, count + (max(valid_counts) * 0.025),
            f"{pct:.1f}%", fontsize=9, fontweight="bold",
            color=COLORS["text"], ha="center"
        )

    fig.tight_layout()
    return ax



# ---------------------------------------------------------------
# Plot: Appointment Duration Distribution
# ---------------------------------------------------------------
def plot_appointment_duration_distribution(df: pd.DataFrame) -> plt.Axes:
    """
    Plot the distribution of appointment durations in minutes.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing 'appointment_duration' column.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.
    """
    if "appointment_duration" not in df.columns:
        raise ValueError("DataFrame must contain an 'appointment_duration' column.")

    # --- Prepare data
    durations = df["appointment_duration"].dropna()
    if durations.empty:
        return _empty_plot("No valid data available for 'appointment_duration'.")

    # --- Create figure
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_title(
        "How Long Are Appointments? A Duration Breakdown",
        loc="left", fontsize=12, x=-0.15, y=1.1
    )

    # --- Initial binning (5-minute intervals)
    initial_bins = np.arange(0, durations.max() + 5, 5)
    counts, edges = np.histogram(durations, bins=initial_bins)
    percentages = (counts / durations.size) * 100

    # --- Filter valid bins (≥0.1%)
    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= 0.1
    ]

    # --- Determine final bins
    max_bin = valid_bins[-1][0] + 5 if valid_bins else 5
    bins = np.arange(0, max_bin, 5)
    counts, edges = np.histogram(durations, bins=bins)
    percentages = (counts / durations.size) * 100

    # --- Filter again after re-binning
    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= 0.1
    ]
    valid_x = [x for x, _, _ in valid_bins]
    valid_counts = [count for _, count, _ in valid_bins]
    valid_percentages = [pct for _, _, pct in valid_bins]

    # --- Plot bars
    ax.bar(
        valid_x, valid_counts,
        width=np.diff(edges)[:len(valid_x)], align="edge",
        edgecolor="#ffffff", color=COLORS["primary"], zorder=3
    )

    # --- Labels & ticks
    ax.set_xticks(bins)
    ax.set_xticklabels([int(b) for b in bins], ha="left")
    ax.set_ylabel("Number of Appointments", labelpad=10, fontsize=10.5)
    ax.set_xlabel("Appointment Duration (Minutes)", labelpad=10, fontsize=10.5)

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)

    # --- Add percentage labels
    for x, count, pct in zip(valid_x, valid_counts, valid_percentages):
        ax.text(
            x + (np.diff(edges)[0] / 2),  # centrado en la barra
            count + (max(valid_counts) * 0.02),
            f"{pct:.1f}%",
            fontsize=9, fontweight="bold",
            color=COLORS["text"], ha="center"
        )

    fig.tight_layout()
    return ax


# ---------------------------------------------------------------
# Plot: Waiting Time Distribution
# ---------------------------------------------------------------
def plot_waiting_time_distribution(df: pd.DataFrame) -> plt.Axes:
    """
    Plot the distribution of patient waiting times in minutes.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing 'waiting_time' column.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.
    """
    if "waiting_time" not in df.columns:
        raise ValueError("DataFrame must contain a 'waiting_time' column.")

    # --- Prepare data
    durations = df["waiting_time"].dropna()
    if durations.empty:
        return _empty_plot("No valid data available for 'waiting_time'.")

    # --- Create figure
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_title(
        "How Much Time Do Patients Spend Waiting?",
        loc="left", fontsize=12, y=1.04, x=-0.08
    )

    # --- Initial binning (10-minute intervals)
    initial_bins = np.arange(0, durations.max() + 10, 10)
    counts, edges = np.histogram(durations, bins=initial_bins)
    percentages = (counts / durations.size) * 100

    # --- Filter valid bins (≥0.1%)
    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= 0.1
    ]

    # --- Determine final bins
    max_bin = valid_bins[-1][0] + 10 if valid_bins else 10
    bins = np.arange(0, max_bin, 10)
    counts, edges = np.histogram(durations, bins=bins)
    percentages = (counts / durations.size) * 100

    # --- Filter again after re-binning
    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= 0.1
    ]
    valid_x = [x for x, _, _ in valid_bins]
    valid_counts = [count for _, count, _ in valid_bins]
    valid_percentages = [pct for _, _, pct in valid_bins]

    # --- Plot bars
    ax.bar(
        valid_x, valid_counts,
        width=np.diff(edges)[:len(valid_x)], align="edge",
        edgecolor="#ffffff", color=COLORS["primary"], zorder=3
    )

    # --- Labels & ticks
    ax.set_xticks(bins)
    ax.set_xticklabels([int(b) for b in bins], ha="center")
    ax.set_ylabel("Number of Appointments", labelpad=10, fontsize=10.5)
    ax.set_xlabel("Waiting Time (Minutes)", labelpad=10, fontsize=10.5)

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin + 5, xmax - 5)

    # --- Add percentage labels
    for x, count, pct in zip(valid_x, valid_counts, valid_percentages):
        ax.text(
            x + (np.diff(edges)[0] / 2),
            count + (max(valid_counts) * 0.025),
            f"{pct:.1f}%",
            fontsize=9, fontweight="bold",
            color=COLORS["text"], ha="center"
        )

    fig.tight_layout()
    return ax

# ---------------------------------------------------------------
# Plot: Patient Arrival Time Distribution
# ---------------------------------------------------------------
def plot_arrival_time_distribution(df: pd.DataFrame) -> plt.Axes:
    """
    Plot the distribution of patient arrival times relative to their appointment time.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing 'status', 'check_in_time', and 'appointment_time' columns.

    Returns
    -------
    plt.Axes
        Matplotlib Axes object for the generated plot.
    """
    required_cols = {"status", "check_in_time", "appointment_time"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"DataFrame must contain columns: {', '.join(missing_cols)}")

    # --- Filter only attended appointments with valid check-in time
    attended_appointments = df[
        (df["status"] == "attended") & df["check_in_time"].notna()
    ].copy()

    if attended_appointments.empty:
        return _empty_plot("No attended appointments with valid check-in times.")

    # --- Calculate arrival time difference in minutes
    attended_appointments["arrival_time_diff"] = (
        pd.to_datetime(attended_appointments["check_in_time"], format="%H:%M:%S", errors="coerce")
        - pd.to_datetime(attended_appointments["appointment_time"], format="%H:%M:%S", errors="coerce")
    ).dt.total_seconds() / 60.0

    arrival_time_diff = attended_appointments["arrival_time_diff"].dropna().round(0)
    if arrival_time_diff.empty:
        return _empty_plot("No valid arrival time differences available.")

    # --- Define bins (5-minute intervals)
    initial_bins = range(
        int(np.floor(arrival_time_diff.min() / 5.0) * 5),
        int(np.ceil(arrival_time_diff.max() / 5.0) * 5) + 5,
        5
    )
    counts, edges = np.histogram(arrival_time_diff, bins=initial_bins)
    percentages = (counts / arrival_time_diff.size) * 100

    # --- Filter valid bins (≥0.1%)
    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= 0.1
    ]

    if valid_bins:
        min_bin = valid_bins[0][0]
        max_bin = valid_bins[-1][0] + 5
    else:
        min_bin, max_bin = 0, 0

    # --- Final bins
    bins = range(min_bin, max_bin, 5)
    counts, edges = np.histogram(arrival_time_diff, bins=bins)
    percentages = (counts / arrival_time_diff.size) * 100

    valid_bins = [
        (x, count, pct)
        for x, count, pct in zip(edges[:-1], counts, percentages)
        if pct >= 0.1
    ]
    valid_x = [x for x, _, _ in valid_bins]
    valid_counts = [count for _, count, _ in valid_bins]
    valid_percentages = [pct for _, _, pct in valid_bins]

    # --- Bar colors (early = blue, late = orange)
    bar_colors = [COLORS["primary"] if x < 0 else COLORS["secondary"] for x in valid_x]

    # --- Create plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title(
        "How Early or Late Do Patients Arrive?",
        loc="left", fontsize=12, y=1.2, x=-0.13
    )

    ax.bar(
        valid_x, valid_counts,
        width=np.diff(edges)[:len(valid_x)], align="edge",
        edgecolor="#ffffff", color=bar_colors, zorder=3
    )

    # --- Vertical reference line at 0 (on-time)
    ax.axvline(0, color=COLORS["text"], linestyle="--", linewidth=1.5, zorder=4)

    # --- Labels & ticks
    ax.set_xticks(bins)
    ax.set_xticklabels([int(b) for b in bins], ha="center")
    ax.set_ylabel("Number of Patients", labelpad=10, fontsize=10.5)
    ax.set_xlabel("Arrival Time Difference (Minutes)", labelpad=10, fontsize=10.5)

    # --- Style adjustments
    ax.spines[["right", "top"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.7, zorder=-1)

    # --- Legend
    ax.legend(
        handles=[
            patches.Patch(color=COLORS["primary"], label="Early Arrival"),
            patches.Patch(color=COLORS["secondary"], label="Late Arrival")
        ],
        loc="upper right", frameon=False, fontsize=10,
        bbox_to_anchor=(1.02, 1.2),
        handlelength=1.5, handleheight=1.5,
        labelspacing=1.0, alignment="left"
    )

    # --- Add percentage labels
    for x, count, pct in zip(valid_x, valid_counts, valid_percentages):
        ax.text(
            x + (np.diff(edges)[0] / 2),
            count + (max(valid_counts) * 0.025),
            f"{pct:.1f}%",
            fontsize=9, fontweight="bold", color=COLORS["text"], ha="center"
        )

    fig.tight_layout()
    return ax

def _extract_group_1d(grouped: Any, key: Any, periods: Sequence) -> np.ndarray:
    """
    Return a 1D vector of length len(periods) for the requested key.

    Behavior
    --------
    - If the key is missing → return a zero vector.
    - If the value is a DataFrame with multiple columns → sum rows (axis=1).
    - Always align the result to 'periods' as the index before returning.
    """
    try:
        obj = grouped.get(key)
    except Exception:
        obj = None

    if obj is None:
        s = pd.Series(0.0, index=pd.Index(periods))
    elif isinstance(obj, pd.DataFrame):
        s = obj.sum(axis=1).astype(float)
    else:
        s = pd.Series(obj, index=getattr(obj, "index", pd.Index(periods))).astype(float)

    if not s.index.equals(pd.Index(periods)):
        s = s.reindex(periods, fill_value=0.0)
    return s.to_numpy(dtype=float)
