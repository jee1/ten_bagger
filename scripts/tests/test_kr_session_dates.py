"""KR session date normalization in prices_live (#125)."""

from __future__ import annotations

import pandas as pd
from performance import prices_live
from performance.prices_live import (
    PROVIDER_BASIS,
    PROVIDER_DATE_BASIS,
    _history_to_bars,
    fetch_live_bars,
)
from performance.returns import resolve_entry


def _kst_hist(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    """Build yfinance-shaped history with KST midnight index."""
    idx = pd.to_datetime([r[0] for r in rows])
    if idx.tz is None:
        idx = idx.tz_localize("Asia/Seoul")
    return pd.DataFrame(
        {"Open": [r[1] for r in rows], "Close": [r[2] for r in rows]},
        index=idx,
    )


def test_kst_midnight_bar_keeps_its_own_session_date():
    hist = _kst_hist([("2026-07-31 00:00:00", 7670.0, 7820.0)])
    bars = _history_to_bars(hist, market="KR", provider="yfinance")
    assert bars.iloc[0]["date"] == "2026-07-31"


def test_cached_utc_instant_recovers_kst_session_date():
    hist = pd.DataFrame(
        {"Open": [7670.0], "Close": [7820.0]},
        index=pd.to_datetime(["2026-07-30T15:00:00Z"]),
    )
    bars = _history_to_bars(hist, market="KR", provider="yfinance")
    assert bars.iloc[0]["date"] == "2026-07-31"


def test_kr_sessions_never_land_on_a_weekend():
    hist = _kst_hist(
        [
            ("2026-08-03 00:00:00", 7830.0, 7570.0),
            ("2026-08-04 00:00:00", 7600.0, 7700.0),
        ]
    )
    bars = _history_to_bars(hist, market="KR", provider="yfinance")
    for label in bars["date"]:
        assert pd.Timestamp(label).weekday() < 5


def test_resolve_entry_takes_next_kst_session_for_midweek_pick():
    hist = _kst_hist(
        [
            ("2026-07-29 00:00:00", 7400.0, 7150.0),
            ("2026-07-30 00:00:00", 7350.0, 7500.0),
            ("2026-07-31 00:00:00", 7670.0, 7820.0),
        ]
    )
    bars = _history_to_bars(hist, market="KR", provider="yfinance")
    entry = resolve_entry(bars, pick_date="2026-07-30", as_of_date="2026-08-31")
    assert entry["entrySession"] == "2026-07-31"
    assert entry["entryPrice"] == 7670.0


def test_unclosed_kst_asof_session_is_excluded(monkeypatch):
    hist = _kst_hist(
        [
            ("2026-07-29 00:00:00", 7400.0, 7150.0),
            ("2026-07-30 00:00:00", 7350.0, 7500.0),
            ("2026-07-31 00:00:00", 7670.0, 7820.0),
        ]
    )
    monkeypatch.setattr(
        prices_live,
        "get_ticker_history_with_provider",
        lambda symbol, period="10y": (hist, "yfinance"),
    )
    out = fetch_live_bars(
        "002780.KS",
        "2026-07-31",
        market="KR",
        as_of_session_closed=False,
    )
    assert out["date"].max() < "2026-07-31"
    assert not any((out["Open"] == 7670.0) & (out["Close"] == 7820.0))


def test_stooq_utc_midnight_dates_are_not_shifted():
    hist = pd.DataFrame(
        {"Open": [10.0], "Close": [11.0]},
        index=pd.to_datetime(["2026-07-30T00:00:00Z"]),
    )
    for market in ("US", "KR"):
        bars = _history_to_bars(hist, market=market, provider="stooq")
        assert bars.iloc[0]["date"] == "2026-07-30"


def test_us_yfinance_session_dates_unchanged():
    idx = pd.to_datetime(["2026-09-04 00:00:00"]).tz_localize("America/New_York")
    hist = pd.DataFrame({"Open": [5.0], "Close": [6.0]}, index=idx)
    bars = _history_to_bars(hist, market="US", provider="yfinance")
    assert bars.iloc[0]["date"] == "2026-09-04"


def test_every_provider_has_a_date_basis():
    assert set(PROVIDER_DATE_BASIS) == set(PROVIDER_BASIS)
