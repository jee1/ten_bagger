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
        def history(self, period: str = "1y") -> pd.DataFrame:
            raise TimeoutError("temporary timeout")

    monkeypatch.setattr(yf_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(yf_cache, "CACHE_TTL_SECONDS", 1)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 1)
    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _symbol: FailingTicker())

    hist = yf_cache.get_ticker_history("TEST")

    assert hist["Close"].tolist() == [12.5]
    assert hist.index[0] == pd.Timestamp("2026-07-20T00:00:00")


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
