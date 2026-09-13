"""Point-in-time price bar filtering and adjustment preference."""

from __future__ import annotations

import math
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

# Market regular cash closes for infer_as_of_session_closed only.
_MARKET_TZ_CLOSE: dict[str, tuple[str, time]] = {
    "KR": ("Asia/Seoul", time(15, 30)),
    "US": ("America/New_York", time(16, 0)),
}


def market_tz(market: str | None) -> str:
    """IANA timezone of the market's exchange (unknown markets fall back to US)."""
    key = (market or "US").upper()
    if key not in _MARKET_TZ_CLOSE:
        key = "US"
    return _MARKET_TZ_CLOSE[key][0]


def _session_dates(bars: pd.DataFrame) -> pd.Series:
    if "date" in bars.columns:
        return pd.to_datetime(bars["date"]).dt.strftime("%Y-%m-%d")
    return pd.to_datetime(bars.index).strftime("%Y-%m-%d")


def infer_as_of_session_closed(
    as_of_date: str,
    *,
    market: str,
    now: datetime | None = None,
) -> bool:
    """Whether the as-of regular cash session is closed in market local time.

    ponytail: ceiling = weekday regular close only (no holiday/half-day calendar).
    Upgrade: exchange session calendar / holiday API when false opens/closes matter.
    """
    key = (market or "US").upper()
    if key not in _MARKET_TZ_CLOSE:
        key = "US"
    tz_name = market_tz(market)
    close_t = _MARKET_TZ_CLOSE[key][1]
    tz = ZoneInfo(tz_name)
    current = now.astimezone(tz) if now is not None else datetime.now(tz)
    local_today = current.date().isoformat()
    if as_of_date < local_today:
        return True
    if as_of_date > local_today:
        return True
    return current.timetz().replace(tzinfo=None) >= close_t


def filter_session_bars(
    bars: pd.DataFrame,
    as_of_date: str,
    *,
    as_of_session_closed: bool = True,
) -> pd.DataFrame:
    """Keep completed sessions with sessionDate <= asOfDate (no look-ahead).

    When as_of_session_closed is False, exclude the as-of session itself
    (unclosed / not yet usable). Does not consult the host calendar date.
    """
    if bars.empty:
        return bars.copy()
    out = bars.copy()
    sessions = _session_dates(out)
    out = out.assign(_session=sessions)
    if as_of_session_closed:
        out = out[out["_session"] <= as_of_date]
    else:
        out = out[out["_session"] < as_of_date]
    return out.drop(columns=["_session"]).reset_index(drop=True)


def is_zero_volume_suspension_bar(row: pd.Series) -> bool:
    """True when vendor forward-filled a halt: Volume 0 and flat OHLC."""
    if "Volume" not in row.index or pd.isna(row["Volume"]):
        return False
    if float(row["Volume"]) != 0.0:
        return False
    cols = ("Open", "High", "Low", "Close")
    if not all(c in row.index and pd.notna(row[c]) for c in cols):
        return False
    o, h, low, c = (float(row[col]) for col in cols)
    if not all(math.isfinite(x) for x in (o, h, low, c)):
        return False
    return o == h == low == c


def prefer_adjusted(
    bars: pd.DataFrame, *, default_label: str = "unadjusted_fallback"
) -> tuple[pd.DataFrame, str]:
    """Return bars with Open/Close columns and priceAdjustment label."""
    if bars.empty:
        return bars.copy(), default_label
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
    return out, default_label
