"""Point-in-time price bar filtering and adjustment preference."""

from __future__ import annotations

from datetime import date

import pandas as pd


def _session_dates(bars: pd.DataFrame) -> pd.Series:
    if "date" in bars.columns:
        return pd.to_datetime(bars["date"]).dt.strftime("%Y-%m-%d")
    return pd.to_datetime(bars.index).strftime("%Y-%m-%d")


def filter_session_bars(bars: pd.DataFrame, as_of_date: str) -> pd.DataFrame:
    """Keep completed sessions with sessionDate <= asOfDate (no look-ahead)."""
    if bars.empty:
        return bars.copy()
    out = bars.copy()
    sessions = _session_dates(out)
    out = out.assign(_session=sessions)
    out = out[out["_session"] <= as_of_date]
    # ponytail: exclude asOfDate when it is today's calendar date (unclosed session)
    if as_of_date == date.today().isoformat():
        out = out[out["_session"] < as_of_date]
    return out.drop(columns=["_session"]).reset_index(drop=True)


def prefer_adjusted(bars: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Return bars with Open/Close columns and priceAdjustment label."""
    if bars.empty:
        return bars.copy(), "unadjusted_fallback"
    out = bars.copy()
    has_adj = "Adj Close" in out.columns or "Adj Open" in out.columns
    if has_adj:
        if "Adj Open" in out.columns:
            out["Open"] = out["Adj Open"]
        elif "Open" not in out.columns and "Adj Close" in out.columns:
            out["Open"] = out["Adj Close"]
        if "Adj Close" in out.columns:
            out["Close"] = out["Adj Close"]
        return out, "adjusted_preferred"
    return out, "unadjusted_fallback"
