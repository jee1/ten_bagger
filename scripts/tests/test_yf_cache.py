"""Tests for yfinance retry behavior."""

from __future__ import annotations

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
