"""Horizon session and calendar helpers (ADR 0003)."""

from __future__ import annotations

import pandas as pd

HORIZON_IDS = ("H20", "H60", "1M", "3M", "6M", "1Y", "3Y", "5Y")

_CALENDAR_MONTHS = {"1M": 1, "3M": 3, "6M": 6}
_CALENDAR_YEARS = {"1Y": 1, "3Y": 3, "5Y": 5}


def trading_sessions(bars: pd.DataFrame) -> list[str]:
    """Return YYYY-MM-DD session dates ascending."""
    if bars.empty:
        return []
    if "date" in bars.columns:
        dates = pd.to_datetime(bars["date"]).dt.strftime("%Y-%m-%d")
    else:
        dates = pd.to_datetime(bars.index).strftime("%Y-%m-%d")
    return sorted(dates.unique().tolist())


def session_horizon_exit(
    sessions: list[str], entry_session: str, n: int
) -> str | None:
    """Nth trading session after entry session (n=20 → H20 exit session)."""
    if entry_session not in sessions:
        return None
    idx = sessions.index(entry_session)
    target_idx = idx + n
    if target_idx >= len(sessions):
        return None
    return sessions[target_idx]


def calendar_horizon_target(pick_date: str, horizon_id: str) -> str:
    """Calendar target date for pickDate + span."""
    ts = pd.Timestamp(pick_date)
    if horizon_id in _CALENDAR_MONTHS:
        target = ts + pd.DateOffset(months=_CALENDAR_MONTHS[horizon_id])
    elif horizon_id in _CALENDAR_YEARS:
        target = ts + pd.DateOffset(years=_CALENDAR_YEARS[horizon_id])
    else:
        raise ValueError(f"not a calendar horizon: {horizon_id}")
    return target.strftime("%Y-%m-%d")


def calendar_horizon_exit(
    sessions: list[str],
    pick_date: str,
    horizon_id: str,
    as_of_date: str,
) -> str | None:
    """Last usable session on/before calendar target and <= asOfDate."""
    target = calendar_horizon_target(pick_date, horizon_id)
    if target > as_of_date:
        return None
    eligible = [s for s in sessions if s <= target]
    if not eligible:
        return None
    return eligible[-1]
