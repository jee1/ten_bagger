"""Live price bar fetch via yfinance (not used in offline unit tests)."""

from __future__ import annotations

import pandas as pd
from yf_cache import get_ticker_history

from performance.pit_prices import filter_session_bars

BENCHMARK_SYMBOLS = {
    "KR-KOSPI": "^KS11",
    "US-SPX": "^GSPC",
}


def _history_to_bars(hist: pd.DataFrame) -> pd.DataFrame:
    if hist.empty:
        return pd.DataFrame(columns=["date", "Open", "High", "Low", "Close"])
    out = hist.reset_index()
    date_col = "Date" if "Date" in out.columns else out.columns[0]
    out = out.rename(columns={date_col: "date"})
    out["date"] = pd.to_datetime(out["date"], utc=True).dt.strftime("%Y-%m-%d")
    cols = ["date", "Open", "High", "Low", "Close"]
    for optional in ("Adj Open", "Adj Close"):
        if optional in out.columns:
            cols.append(optional)
    present = [c for c in cols if c in out.columns]
    return out[present].copy()


def fetch_live_bars(symbol: str, as_of_date: str, *, period: str = "10y") -> pd.DataFrame:
    """Fetch OHLCV via get_ticker_history (retry/backoff) and apply PIT filter."""
    hist = get_ticker_history(symbol, period=period)
    bars = _history_to_bars(hist)
    return filter_session_bars(bars, as_of_date)


def default_price_provider(as_of_date: str):
    """Return callable(symbol, market) -> bars for regenerate CLI."""

    def provider(symbol: str, market: str) -> pd.DataFrame:  # noqa: ARG001
        return fetch_live_bars(symbol, as_of_date)

    return provider


def default_benchmark_provider(as_of_date: str):
    """Return callable(benchmark_id) -> bars | None."""

    def provider(benchmark_id: str) -> pd.DataFrame | None:
        yf_symbol = BENCHMARK_SYMBOLS.get(benchmark_id)
        if not yf_symbol:
            return None
        try:
            return fetch_live_bars(yf_symbol, as_of_date)
        except Exception:
            return None

    return provider
