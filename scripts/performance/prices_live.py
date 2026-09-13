"""Live price bar fetch via yfinance (not used in offline unit tests)."""

from __future__ import annotations

import pandas as pd
from yf_cache import get_ticker_history_with_provider

from performance.pit_prices import filter_session_bars, infer_as_of_session_closed, market_tz

# Matches yf_cache.get_ticker_history(..., auto_adjust=True) — vendor split/dividend adjusted.
YF_PRICE_BASIS = "adjusted_auto"
# ADR 0005 §5: Stooq daily CSV is typically unadjusted (no Adj columns).
PROVIDER_BASIS = {"yfinance": YF_PRICE_BASIS, "stooq": "unadjusted_fallback"}

# Yahoo daily bars are exchange-local midnights (KR: 00:00+09:00), so the session date is the
# local date, not the UTC one. Stooq CSV dates are already session dates (ADR 0005 §5).
PROVIDER_DATE_BASIS = {"yfinance": "exchange_local", "stooq": "session_date"}

BENCHMARK_SYMBOLS = {
    "KR-KOSPI": "^KS11",
    "US-SPX": "^GSPC",
}


def _session_dates(values, *, market: str | None, provider: str) -> pd.Series:
    ts = pd.to_datetime(values, utc=True)
    if PROVIDER_DATE_BASIS.get(provider) == "exchange_local":
        ts = ts.dt.tz_convert(market_tz(market))
    return ts.dt.strftime("%Y-%m-%d")


def _history_to_bars(hist: pd.DataFrame, *, market: str | None, provider: str) -> pd.DataFrame:
    if hist.empty:
        return pd.DataFrame(columns=["date", "Open", "High", "Low", "Close", "Volume"])
    out = hist.reset_index()
    date_col = "Date" if "Date" in out.columns else out.columns[0]
    out = out.rename(columns={date_col: "date"})
    out["date"] = _session_dates(out["date"], market=market, provider=provider)
    cols = ["date", "Open", "High", "Low", "Close", "Volume"]
    for optional in ("Adj Open", "Adj Close"):
        if optional in out.columns:
            cols.append(optional)
    present = [c for c in cols if c in out.columns]
    return out[present].copy()


def fetch_live_bars(
    symbol: str,
    as_of_date: str,
    *,
    period: str = "10y",
    market: str | None = None,
    as_of_session_closed: bool | None = None,
) -> pd.DataFrame:
    """Fetch OHLCV via get_ticker_history (retry/backoff) and apply PIT filter."""
    hist, provider = get_ticker_history_with_provider(symbol, period=period)
    bars = _history_to_bars(hist, market=market, provider=provider)
    closed = (
        as_of_session_closed
        if as_of_session_closed is not None
        else infer_as_of_session_closed(as_of_date, market=market or "US")
    )
    out = filter_session_bars(bars, as_of_date, as_of_session_closed=closed)
    out.attrs["provider"] = provider
    out.attrs["priceBasis"] = PROVIDER_BASIS.get(provider, "unknown")
    return out


def default_price_provider(as_of_date: str):
    """Return callable(symbol, market) -> bars for regenerate CLI."""

    def provider(symbol: str, market: str) -> pd.DataFrame:
        return fetch_live_bars(symbol, as_of_date, market=market)

    return provider


def default_benchmark_provider(as_of_date: str):
    """Return callable(benchmark_id) -> bars | None."""

    def provider(benchmark_id: str) -> pd.DataFrame | None:
        yf_symbol = BENCHMARK_SYMBOLS.get(benchmark_id)
        if not yf_symbol:
            return None
        market = "KR" if benchmark_id.startswith("KR") else "US"
        try:
            return fetch_live_bars(yf_symbol, as_of_date, market=market)
        except Exception:
            return None

    return provider
