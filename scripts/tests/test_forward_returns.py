"""Forward-return measurement tests (offline, no network).

All tests monkeypatch/block live yfinance — fixture injection only.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from performance.horizons import HORIZON_IDS, calendar_horizon_target
from performance.pit_prices import filter_session_bars, prefer_adjusted
from performance.returns import measure_all_horizons, measure_pick_horizon
from tests.fixtures.price_loader import load_price_fixture

EPS = 1e-9


def _pick_daily(date: str, market: str, symbol: str) -> dict:
    return {
        "date": date,
        "market": market,
        "status": "pick",
        "stock": {"symbol": symbol},
        "scores": {"composite": 80, "version": 2},
    }


def _no_pick_daily(date: str, market: str) -> dict:
    return {
        "date": date,
        "market": market,
        "status": "no_pick",
        "scores": {"composite": 0, "version": 2},
    }


# --- T009: basic return arithmetic ---


def test_h20_simple_return_exit_minus_entry_over_entry():
    bars = load_price_fixture("simple_kr_h20")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="H20",
    )
    assert m["completionStatus"] == "complete"
    assert m["entryPrice"] == pytest.approx(100.0, abs=EPS)
    assert m["exitPrice"] == pytest.approx(121.0, abs=EPS)
    assert m["forwardReturn"] == pytest.approx(0.21, abs=EPS)


def test_no_pick_produces_zero_measurements_via_regenerate(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    (daily_dir / "2026-01-02.json").write_text(
        json.dumps(_no_pick_daily("2026-01-02", "KR")), encoding="utf-8"
    )
    ledger_dir = tmp_path / "ledger"
    perf_dir = tmp_path / "performance"

    import regenerate_ledger

    monkeypatch.setattr(
        regenerate_ledger,
        "default_price_provider",
        lambda _as_of: (lambda _s, _m: load_price_fixture("simple_kr_h20")),
    )
    monkeypatch.setattr(
        regenerate_ledger, "default_benchmark_provider", lambda _as_of: lambda _b: None
    )

    summary = regenerate_ledger.regenerate(
        as_of_date="2026-02-10",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        provider_label="fixture",
    )
    perf = json.loads((perf_dir / "KR.json").read_text())
    ledger = json.loads((ledger_dir / "KR.json").read_text())
    assert len(ledger["entries"]) == 1
    assert ledger["entries"][0]["status"] == "no_pick"
    assert ledger["entries"][0]["symbol"] == ""
    assert perf["measurements"] == []
    assert summary["markets"]["KR"]["measurements"] == 0


def test_empty_eligible_set_valid_empty_snapshots(tmp_path, monkeypatch):
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    ledger_dir = tmp_path / "ledger"
    perf_dir = tmp_path / "performance"

    import regenerate_ledger

    monkeypatch.setattr(
        regenerate_ledger,
        "default_price_provider",
        lambda _as_of: (lambda _s, _m: load_price_fixture("simple_kr_h20")),
    )
    monkeypatch.setattr(
        regenerate_ledger, "default_benchmark_provider", lambda _as_of: lambda _b: None
    )

    regenerate_ledger.regenerate(
        as_of_date="2026-01-01",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        provider_label="fixture",
    )
    ledger = json.loads((ledger_dir / "KR.json").read_text())
    perf = json.loads((perf_dir / "KR.json").read_text())
    assert ledger["entries"] == []
    assert perf["measurements"] == []


# --- T017: look-ahead refusal ---


def test_lookahead_bars_after_asof_not_used():
    bars = load_price_fixture("lookahead_kr")
    filtered = filter_session_bars(bars, "2026-01-08")
    sessions = filtered["date"].tolist()
    assert "2026-02-01" not in sessions
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-01-08",
        market="KR",
        symbol="LOOKAHEAD.KR",
        horizon_id="H20",
    )
    assert m["completionStatus"] == "incomplete"
    assert m["incompleteReason"] in ("missing_exit", "horizon_beyond_asof")


# --- T018: delist survivorship ---


def test_delist_uses_last_available_exit():
    bars = load_price_fixture("delist_kr")
    measurements = measure_all_horizons(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-01",
        market="KR",
        symbol="DELIST.KR",
    )
    h20 = next(m for m in measurements if m["horizonId"] == "H20")
    assert h20["survivorshipFlag"] == "delisted"
    assert h20["completionStatus"] == "complete"
    assert h20["exitPrice"] == pytest.approx(60.0, abs=EPS)
    assert h20["forwardReturn"] == pytest.approx((60.0 - 51.0) / 51.0, abs=EPS)


def test_missing_prices_incomplete_with_reason():
    bars = load_price_fixture("thin_ipo_kr")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-03-01",
        as_of_date="2026-03-10",
        market="KR",
        symbol="THIN.KR",
        horizon_id="H20",
    )
    assert m["completionStatus"] == "incomplete"
    assert m["incompleteReason"] in (
        "missing_exit",
        "horizon_beyond_asof",
        "insufficient_history",
    )


# --- T019: invalid entry ---


def test_non_positive_entry_invalid_no_forward_return():
    bars = load_price_fixture("invalid_entry_kr")
    measurements = measure_all_horizons(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-01-10",
        market="KR",
        symbol="INVALID.KR",
    )
    for m in measurements:
        assert m["completionStatus"] == "incomplete"
        assert m["incompleteReason"] == "invalid_entry"
        assert "forwardReturn" not in m


# --- T024: KR + US horizon ids and benchmark ids ---


def test_all_eight_horizon_ids_emitted():
    bars = load_price_fixture("simple_kr_h20")
    measurements = measure_all_horizons(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
    )
    assert {m["horizonId"] for m in measurements} == set(HORIZON_IDS)


def test_kr_benchmark_id():
    bars = load_price_fixture("simple_kr_h20")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="H20",
    )
    assert m["benchmarkId"] == "KR-KOSPI"


def test_us_benchmark_id():
    bars = load_price_fixture("simple_us_h20")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-02-02",
        as_of_date="2026-03-10",
        market="US",
        symbol="US.TEST",
        horizon_id="H20",
    )
    assert m["benchmarkId"] == "US-SPX"


# --- T025: calendar / H60 incomplete ---


def test_calendar_horizon_incomplete_when_exit_after_asof():
    bars = load_price_fixture("simple_kr_h20")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-01-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="1Y",
    )
    target = calendar_horizon_target("2026-01-02", "1Y")
    assert target > "2026-01-10"
    assert m["completionStatus"] == "incomplete"
    assert m["incompleteReason"] == "horizon_beyond_asof"


def test_h60_incomplete_when_fewer_than_60_sessions():
    bars = load_price_fixture("simple_kr_h20")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="H60",
    )
    assert m["completionStatus"] == "incomplete"
    assert m["incompleteReason"] in ("missing_exit", "horizon_beyond_asof")


# --- T026: missing benchmark ---


def test_missing_benchmark_pick_complete_benchmark_incomplete():
    bars = load_price_fixture("simple_kr_h20")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=None,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="H20",
    )
    assert m["completionStatus"] == "complete"
    assert m["benchmarkCompletionStatus"] == "incomplete"
    assert m["benchmarkIncompleteReason"] == "missing_benchmark_series"


def test_benchmark_complete_when_series_present():
    bars = load_price_fixture("simple_kr_h20")
    bench = load_price_fixture("benchmark_kr")
    m = measure_pick_horizon(
        bars=bars,
        benchmark_bars=bench,
        pick_date="2026-01-02",
        as_of_date="2026-02-10",
        market="KR",
        symbol="SIMPLE.KR",
        horizon_id="H20",
    )
    assert m["completionStatus"] == "complete"
    assert m["benchmarkCompletionStatus"] == "complete"
    assert "benchmarkReturn" in m
    assert math.isfinite(m["benchmarkReturn"])


# --- T031-T033: prefer_adjusted, epsilon ---


def test_prefer_adjusted_uses_adj_columns():
    import pandas as pd

    bars = pd.DataFrame(
        [
            {
                "date": "2026-01-02",
                "Open": 10.0,
                "Close": 11.0,
                "Adj Open": 100.0,
                "Adj Close": 110.0,
            }
        ]
    )
    adjusted, label = prefer_adjusted(bars)
    assert label == "adjusted_preferred"
    assert adjusted.iloc[0]["Open"] == pytest.approx(100.0)
    assert adjusted.iloc[0]["Close"] == pytest.approx(110.0)


def test_prefer_adjusted_unadjusted_fallback_without_adj():
    import pandas as pd

    bars = pd.DataFrame([{"date": "2026-01-02", "Open": 10.0, "Close": 11.0}])
    _, label = prefer_adjusted(bars)
    assert label == "unadjusted_fallback"


def test_second_regenerate_identical(tmp_path, monkeypatch):
    """SC-005 determinism with fixture provider."""
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    (daily_dir / "2026-01-02.json").write_text(
        json.dumps(_pick_daily("2026-01-02", "KR", "SIMPLE.KR")), encoding="utf-8"
    )
    ledger_dir = tmp_path / "ledger"
    perf_dir = tmp_path / "performance"

    import regenerate_ledger

    bars = load_price_fixture("simple_kr_h20")

    def price_provider(_as_of):
        return lambda _s, _m: bars.copy()

    monkeypatch.setattr(regenerate_ledger, "default_price_provider", price_provider)
    monkeypatch.setattr(
        regenerate_ledger, "default_benchmark_provider", lambda _as_of: lambda _b: None
    )
    fixed_meta = {
        "provider": "fixture",
        "priceAdjustment": "adjusted_preferred",
        "generatedAt": "2026-01-01T00:00:00+00:00",
        "asOfDate": "2026-02-10",
    }

    original_build = regenerate_ledger.build_market_snapshots

    def fake_build(*, dailies, market, as_of_date, price_provider, benchmark_provider, provider_label, price_adjustment):  # noqa: E501
        ledger, perf = original_build(
            dailies=dailies,
            market=market,
            as_of_date=as_of_date,
            price_provider=price_provider,
            benchmark_provider=benchmark_provider,
            provider_label=provider_label,
            price_adjustment=price_adjustment,
        )
        perf["runMeta"] = fixed_meta
        return ledger, perf

    monkeypatch.setattr(regenerate_ledger, "build_market_snapshots", fake_build)

    regenerate_ledger.regenerate(
        as_of_date="2026-02-10",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        provider_label="fixture",
    )
    first = (perf_dir / "KR.json").read_text()
    regenerate_ledger.regenerate(
        as_of_date="2026-02-10",
        markets=("KR",),
        daily_dir=daily_dir,
        ledger_dir=ledger_dir,
        performance_dir=perf_dir,
        provider_label="fixture",
    )
    second = (perf_dir / "KR.json").read_text()
    assert first == second
