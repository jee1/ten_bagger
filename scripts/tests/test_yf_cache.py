"""Tests for yfinance retry behavior."""

from __future__ import annotations

import json
import os
import time

import pandas as pd
import pytest
import yf_cache
from config import YF_RATE_LIMIT_DELAY


def test_with_retry_succeeds_after_transient_failure(monkeypatch):
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("temporary")
        return "ok"

    monkeypatch.setattr(yf_cache.time, "sleep", lambda _seconds: None)
    assert yf_cache._with_retry("test", flaky) == "ok"
    assert calls["n"] == 2


def test_with_retry_raises_after_max_attempts(monkeypatch):
    def always_fail() -> str:
        raise RuntimeError("Too Many Requests. Rate limited.")

    sleeps: list[float] = []
    monkeypatch.setattr(yf_cache.time, "sleep", lambda seconds: sleeps.append(seconds))
    with pytest.raises(RuntimeError, match="Rate limited"):
        yf_cache._with_retry("test", always_fail)
    assert any(delay >= YF_RATE_LIMIT_DELAY for delay in sleeps)


def test_get_ticker_info_uses_stale_cache_after_rate_limit(monkeypatch, tmp_path):
    path = tmp_path / "TEST_info.json"
    path.write_text(json.dumps({"longName": "Cached Test Corp"}), encoding="utf-8")
    old_time = time.time() - 10_000
    os.utime(path, (old_time, old_time))

    class RateLimitedTicker:
        @property
        def info(self) -> dict[str, str]:
            raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 1)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: RateLimitedTicker())

    assert yf_cache.get_ticker_info("TEST") == {"longName": "Cached Test Corp"}


def test_get_ticker_history_uses_stale_cache_after_transient_failure(monkeypatch, tmp_path):
    path = tmp_path / "TEST_hist_1y.json"
    path.write_text(
        json.dumps({"index": ["2026-07-20T00:00:00"], "close": [12.5]}),
        encoding="utf-8",
    )
    old_time = time.time() - 10_000
    os.utime(path, (old_time, old_time))

    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise TimeoutError("temporary timeout")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 1)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())

    hist = yf_cache.get_ticker_history("TEST")

    assert hist["Close"].tolist() == [12.5]
    assert pd.Timestamp(hist.index[0]).strftime("%Y-%m-%d") == "2026-07-20"


def test_read_history_cache_mixed_tz_offsets(tmp_path):
    """US DST transitions produce mixed offsets in cached ISO index strings."""
    path = tmp_path / "US_hist_10y.json"
    path.write_text(
        json.dumps(
            {
                "index": [
                    "2026-03-07T00:00:00-05:00",
                    "2026-03-10T00:00:00-04:00",
                ],
                "open": [10.0, 11.0],
                "high": [10.5, 11.5],
                "low": [9.5, 10.5],
                "close": [10.2, 11.2],
            }
        ),
        encoding="utf-8",
    )
    hist = yf_cache._read_history_cache(path)
    assert hist is not None
    assert hist["Open"].tolist() == [10.0, 11.0]
    assert hist["Close"].tolist() == [10.2, 11.2]
    assert list(pd.Timestamp(t).strftime("%Y-%m-%d") for t in hist.index) == [
        "2026-03-07",
        "2026-03-10",
    ]


def test_get_ticker_info_raises_without_usable_stale_cache(monkeypatch, tmp_path):
    class RateLimitedTicker:
        @property
        def info(self) -> dict[str, str]:
            raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: RateLimitedTicker())

    with pytest.raises(RuntimeError, match="Too Many Requests"):
        yf_cache.get_ticker_info("TEST")


def test_get_ticker_history_uses_stooq_when_no_stale(monkeypatch, tmp_path):
    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise RuntimeError("429 Too Many Requests")

    stooq_calls = {"n": 0}

    def fake_stooq(symbol: str, period: str = "1y") -> pd.DataFrame:
        stooq_calls["n"] += 1
        idx = pd.to_datetime(["2026-07-21"], utc=True)
        return pd.DataFrame({"Close": [99.0], "Open": [98.0]}, index=idx)

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())
    monkeypatch.setattr("stooq_prices.fetch_history", fake_stooq)

    hist = yf_cache.get_ticker_history("TEST")
    assert stooq_calls["n"] == 1
    assert hist["Close"].tolist() == [99.0]
    assert (tmp_path / "TEST_hist_1y_stooq.json").exists()


def test_get_ticker_history_stale_before_stooq(monkeypatch, tmp_path):
    path = tmp_path / "TEST_hist_1y.json"
    path.write_text(
        json.dumps({"index": ["2026-07-20T00:00:00"], "close": [12.5]}),
        encoding="utf-8",
    )
    old_time = time.time() - 10_000
    os.utime(path, (old_time, old_time))

    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise TimeoutError("temporary timeout")

    def boom_stooq(*_a, **_k):
        raise AssertionError("Stooq must not run when stale cache exists")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 1)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())
    monkeypatch.setattr("stooq_prices.fetch_history", boom_stooq)

    hist = yf_cache.get_ticker_history("TEST")
    assert hist["Close"].tolist() == [12.5]


def test_get_ticker_history_empty_primary_tries_stooq(monkeypatch, tmp_path):
    class EmptyTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            return pd.DataFrame()

    def fake_stooq(symbol: str, period: str = "1y") -> pd.DataFrame:
        idx = pd.to_datetime(["2026-08-01"], utc=True)
        return pd.DataFrame({"Close": [7.0]}, index=idx)

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: EmptyTicker())
    monkeypatch.setattr("stooq_prices.fetch_history", fake_stooq)

    hist = yf_cache.get_ticker_history("TEST")
    assert hist["Close"].tolist() == [7.0]


def test_get_ticker_history_raises_when_primary_and_stooq_fail(monkeypatch, tmp_path):
    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise RuntimeError("429 Too Many Requests")

    def fail_stooq(*_a, **_k):
        raise RuntimeError("stooq down")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())
    monkeypatch.setattr("stooq_prices.fetch_history", fail_stooq)

    with pytest.raises(RuntimeError, match="Too Many Requests"):
        yf_cache.get_ticker_history("TEST")


def test_get_ticker_history_with_provider_fresh_yfinance_cache(monkeypatch, tmp_path):
    path = tmp_path / "TEST_hist_1y.json"
    path.write_text(
        json.dumps({"index": ["2026-07-20T00:00:00"], "close": [12.5]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 3600)

    hist, provider = yf_cache.get_ticker_history_with_provider("TEST")
    assert provider == "yfinance"
    assert hist["Close"].tolist() == [12.5]


def test_get_ticker_history_with_provider_live_yfinance(monkeypatch, tmp_path):
    history_kwargs: list[dict] = []

    class LiveTicker:
        def history(self, period: str = "1y", **kwargs) -> pd.DataFrame:
            history_kwargs.append(kwargs)
            idx = pd.to_datetime(["2026-07-22"], utc=True)
            return pd.DataFrame({"Close": [42.0]}, index=idx)

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: LiveTicker())

    hist, provider = yf_cache.get_ticker_history_with_provider("TEST")
    assert provider == "yfinance"
    assert hist["Close"].tolist() == [42.0]
    assert history_kwargs[0]["auto_adjust"] is True


def test_get_ticker_history_with_provider_stale_yfinance_cache(monkeypatch, tmp_path):
    path = tmp_path / "TEST_hist_1y.json"
    path.write_text(
        json.dumps({"index": ["2026-07-20T00:00:00"], "close": [12.5]}),
        encoding="utf-8",
    )
    old_time = time.time() - 10_000
    os.utime(path, (old_time, old_time))

    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise TimeoutError("temporary timeout")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 1)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())

    hist, provider = yf_cache.get_ticker_history_with_provider("TEST")
    assert provider == "yfinance"
    assert hist["Close"].tolist() == [12.5]


def test_get_ticker_history_with_provider_fresh_stooq_cache(monkeypatch, tmp_path):
    stooq_path = tmp_path / "TEST_hist_1y_stooq.json"
    stooq_path.write_text(
        json.dumps({"index": ["2026-07-21T00:00:00"], "close": [99.0]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 3600)

    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise RuntimeError("429 Too Many Requests")

    def boom_stooq(*_a, **_k):
        raise AssertionError("Stooq fetch must not run when fresh cache exists")

    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())
    monkeypatch.setattr("stooq_prices.fetch_history", boom_stooq)

    hist, provider = yf_cache.get_ticker_history_with_provider("TEST")
    assert provider == "stooq"
    assert hist["Close"].tolist() == [99.0]


def test_get_ticker_history_with_provider_fetched_stooq(monkeypatch, tmp_path):
    class FailingTicker:
        def history(self, period: str = "1y", **_) -> pd.DataFrame:
            raise RuntimeError("429 Too Many Requests")

    def fake_stooq(symbol: str, period: str = "1y") -> pd.DataFrame:
        idx = pd.to_datetime(["2026-07-21"], utc=True)
        return pd.DataFrame({"Close": [99.0], "Open": [98.0]}, index=idx)

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())
    monkeypatch.setattr("stooq_prices.fetch_history", fake_stooq)

    hist, provider = yf_cache.get_ticker_history_with_provider("TEST")
    assert provider == "stooq"
    assert hist["Close"].tolist() == [99.0]
