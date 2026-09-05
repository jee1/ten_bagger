"""Stooq daily OHLCV secondary for price history dual-source (ADR 0005)."""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd

logger = logging.getLogger(__name__)

_STOQ_DAILY = "https://stooq.com/q/d/l/?s={symbol}&i=d"
_PERIOD_DAYS = {
    "1d": 5,
    "5d": 10,
    "1mo": 40,
    "3mo": 100,
    "6mo": 200,
    "1y": 400,
    "2y": 800,
    "5y": 2000,
    "10y": 4000,
    "max": 50_000,
}


def to_stooq_symbol(symbol: str) -> str | None:
    """Map Yahoo-style ticker to Stooq symbol, or None if unusable."""
    raw = (symbol or "").strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper.endswith(".KS") or upper.endswith(".KQ"):
        code = upper.rsplit(".", 1)[0]
        if not code:
            return None
        return f"{code.lower()}.ks"
    if upper.endswith(".US"):
        return f"{upper[:-3].lower()}.us"
    if "." in upper:
        return upper.lower()
    return f"{upper.lower()}.us"


def _period_cutoff(period: str) -> datetime | None:
    days = _PERIOD_DAYS.get(period, _PERIOD_DAYS["1y"])
    if period == "max":
        return None
    return datetime.now(UTC) - timedelta(days=days)


def parse_stooq_csv(text: str) -> pd.DataFrame | None:
    """Parse Stooq daily CSV into OHLCV DataFrame; None if unusable."""
    stripped = text.strip()
    if not stripped or stripped.lower().startswith("<!"):
        return None
    reader = csv.DictReader(io.StringIO(stripped))
    if not reader.fieldnames or "Date" not in reader.fieldnames:
        return None
    rows: list[dict[str, Any]] = []
    for row in reader:
        date_s = (row.get("Date") or "").strip()
        close_s = (row.get("Close") or "").strip()
        if not date_s or not close_s:
            continue
        try:
            close = float(close_s)
        except ValueError:
            continue
        item: dict[str, Any] = {"Date": date_s, "Close": close}
        for src, col in (("Open", "Open"), ("High", "High"), ("Low", "Low")):
            raw_v = (row.get(src) or "").strip()
            if raw_v:
                try:
                    item[col] = float(raw_v)
                except ValueError:
                    pass
        rows.append(item)
    if not rows:
        return None
    frame = pd.DataFrame(rows)
    index = pd.to_datetime(frame["Date"], utc=True)
    data: dict[str, list[float]] = {"Close": frame["Close"].tolist()}
    for col in ("Open", "High", "Low"):
        if col in frame.columns:
            data[col] = frame[col].tolist()
    out = pd.DataFrame(data, index=index).sort_index()
    return out if not out.empty else None


def _default_fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "ten-bagger-dual-source/1.0"})
    with urlopen(req, timeout=30) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def fetch_history(
    symbol: str,
    period: str = "1y",
    *,
    fetch_text: Callable[[str], str] | None = None,
) -> pd.DataFrame:
    """Fetch Stooq daily history for Yahoo-style ``symbol``.

    Raises on mapping failure, network/parse failure, or empty series.
    """
    stooq_sym = to_stooq_symbol(symbol)
    if stooq_sym is None:
        raise ValueError(f"Cannot map symbol to Stooq: {symbol!r}")
    url = _STOQ_DAILY.format(symbol=stooq_sym)
    getter = fetch_text or _default_fetch
    try:
        text = getter(url)
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Stooq fetch failed for {stooq_sym}: {exc}") from exc
    hist = parse_stooq_csv(text)
    if hist is None or hist.empty:
        raise RuntimeError(f"Stooq returned no usable OHLCV for {stooq_sym}")
    cutoff = _period_cutoff(period)
    if cutoff is not None:
        hist = hist[hist.index >= pd.Timestamp(cutoff)]
    if hist.empty:
        raise RuntimeError(f"Stooq history empty after period filter {period} for {stooq_sym}")
    logger.info(
        "provider=stooq history for %s (stooq=%s, period=%s)",
        symbol,
        stooq_sym,
        period,
    )
    return hist
