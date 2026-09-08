"""Unit tests for remaining tech-debt batch (#101–103, #106–107)."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest


def test_load_dailies_rejects_partial_pick(tmp_path: Path) -> None:
    from performance.load_dailies import load_eligible_dailies

    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    (daily_dir / "partial.json").write_text(
        json.dumps(
            {
                "date": "2026-01-02",
                "market": "KR",
                "status": "pick",
                "stock": {"symbol": "X"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid daily JSON"):
        load_eligible_dailies(daily_dir, "2026-02-01")


def test_survivorship_vendor_delisted_wins() -> None:
    from performance.returns import survivorship_flag

    bars = pd.DataFrame(
        {"date": ["2026-01-10"], "Close": [60.0]},
    )
    assert survivorship_flag(bars, "2026-01-11", vendor_status="DELISTED") == "delisted"


def test_survivorship_weekday_gap_not_weekend_inflated() -> None:
    """Fri→Mon is 3 calendar days but only 1 weekday after last session → unknown."""
    from performance.returns import survivorship_flag

    # 2026-01-09 is Friday
    bars = pd.DataFrame({"date": ["2026-01-09"], "Close": [10.0]})
    assert survivorship_flag(bars, "2026-01-12") == "unknown"  # Mon
    assert survivorship_flag(bars, "2026-01-16") == "delisted"  # next Fri (≥5 weekdays)


def test_screen_import_does_not_load_scoring_v1() -> None:
    for mod in list(sys.modules):
        if mod == "scoring.v1" or mod.startswith("scoring.v1."):
            del sys.modules[mod]
    if "screen" in sys.modules:
        del sys.modules["screen"]
    if "screening.core" in sys.modules:
        del sys.modules["screening.core"]

    importlib.import_module("screen")
    assert "scoring.v1" not in sys.modules


def test_fundamental_rate_limit_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    import yf_cache

    yf_cache.reset_fundamental_rate_limit_events()
    assert yf_cache.fundamental_rate_limit_events() == 0

    calls = {"n": 0}

    def boom() -> dict:
        calls["n"] += 1
        raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(yf_cache, "_is_fresh", lambda _p: False)
    monkeypatch.setattr(yf_cache, "_read_info_cache", lambda _p: None)
    monkeypatch.setattr(yf_cache, "_throttle_before_request", lambda: None)
    monkeypatch.setattr(yf_cache, "YF_MAX_RETRIES", 2)
    monkeypatch.setattr(yf_cache, "YF_RETRY_BASE_DELAY", 0)
    monkeypatch.setattr(yf_cache, "YF_RATE_LIMIT_DELAY", 0)

    class _T:
        @property
        def info(self) -> dict:
            return boom()

    monkeypatch.setattr(yf_cache.yf, "Ticker", lambda _s: _T())

    with pytest.raises(RuntimeError, match="429"):
        yf_cache.get_ticker_info("RATE.US")

    assert yf_cache.fundamental_rate_limit_events() >= 1
    assert calls["n"] >= 1


def test_root_requirements_delegates_to_scripts() -> None:
    root = Path(__file__).resolve().parents[2] / "requirements.txt"
    text = root.read_text(encoding="utf-8")
    assert "-r scripts/requirements.txt" in text
