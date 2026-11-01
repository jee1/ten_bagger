"""finnaut-ohlc first, yfinance/stooq fallback for ledger prices (#174)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from config import PERFORMANCE_BUNDLE_SCHEMA_PATH
from performance import prices_live
from performance.ohlc_bars import OHLC_DIR_ENV, OhlcMiss, load_ohlc_bars
from performance.prices_live import default_benchmark_provider, fetch_live_bars
from regenerate_ledger import build_market_snapshots
from validate_content import load_validator


def _bar(d: str, c: float) -> dict:
    return {"d": d, "o": c, "h": c, "l": c, "c": c, "v": 100}


def _snapshot(
    root: Path,
    market_dir: str,
    as_of: str,
    symbols: dict[str, list[dict]],
    failed: tuple[str, ...] = (),
) -> None:
    folder = root / "bars" / market_dir / as_of
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text(
        json.dumps({"asOf": as_of, "failedSymbols": list(failed), "priceBasis": "adjusted_auto"})
    )
    for symbol, bars in symbols.items():
        payload = {"symbol": symbol, "asOf": as_of, "priceBasis": "adjusted_auto", "bars": bars}
        (folder / f"{symbol.lstrip('^')}.json").write_text(json.dumps(payload))


KR_BARS = [_bar("2026-10-27", 100), _bar("2026-10-28", 101), _bar("2026-10-29", 102)]


def _no_yfinance(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("yfinance must not be called when finnaut-ohlc covers the symbol")

    monkeypatch.setattr(prices_live, "get_ticker_history_with_provider", boom)


def test_loads_latest_snapshot_on_or_before_as_of(tmp_path):
    _snapshot(tmp_path, "krx", "2026-10-28", {"005930.KS": KR_BARS[:2]})
    _snapshot(tmp_path, "krx", "2026-10-29", {"005930.KS": KR_BARS})
    _snapshot(tmp_path, "krx", "2026-10-30", {"005930.KS": KR_BARS + [_bar("2026-10-30", 999)]})

    bars = load_ohlc_bars("005930.KS", "KR", "2026-10-29", root=tmp_path)

    assert bars["date"].tolist() == ["2026-10-27", "2026-10-28", "2026-10-29"]
    assert bars["Close"].tolist() == [100, 101, 102]
    assert bars.attrs == {
        "priceBasis": "adjusted_auto",
        "ohlcAsOf": "2026-10-29",
        "lastSession": "2026-10-29",
    }


def test_index_symbol_file_drops_caret(tmp_path):
    _snapshot(tmp_path, "us", "2026-10-29", {"^GSPC": KR_BARS})
    assert len(load_ohlc_bars("^GSPC", "US", "2026-10-29", root=tmp_path)) == 3


def test_previous_weekday_snapshot_is_accepted(tmp_path):
    _snapshot(tmp_path, "us", "2026-10-30", {"AAPL": KR_BARS + [_bar("2026-10-30", 103)]})  # Fri
    bars = load_ohlc_bars("AAPL", "US", "2026-11-02", root=tmp_path)  # Monday
    assert bars.attrs["ohlcAsOf"] == "2026-10-30"


def test_symbol_behind_its_folder_reports_own_last_session(tmp_path):
    # Seen in bars/us/2026-10-30: ^GSPC had 10-30, every stock ended 10-29.
    _snapshot(
        tmp_path, "us", "2026-10-30", {"^GSPC": KR_BARS + [_bar("2026-10-30", 1)], "EBS": KR_BARS}
    )
    bars = load_ohlc_bars("EBS", "US", "2026-10-30", root=tmp_path)
    assert (bars.attrs["ohlcAsOf"], bars.attrs["lastSession"]) == ("2026-10-30", "2026-10-29")


@pytest.mark.parametrize(
    ("as_of", "symbol", "since", "failed", "reason"),
    [
        ("2026-11-03", "AAPL", None, (), "stale for 2026-11-03"),
        ("2026-10-29", "MSFT", None, (), "not in"),
        ("2026-10-29", "AAPL", None, ("AAPL",), "failed in"),
        ("2026-10-29", "AAPL", "2026-10-26", (), "after 2026-10-26"),
        ("2026-10-28", "AAPL", None, (), "no snapshot"),
    ],
)
def test_misses(tmp_path, as_of, symbol, since, failed, reason):
    _snapshot(tmp_path, "us", "2026-10-29", {"AAPL": KR_BARS}, failed=failed)
    with pytest.raises(OhlcMiss, match=reason):
        load_ohlc_bars(symbol, "US", as_of, since=since, root=tmp_path)


def test_fetch_live_bars_prefers_ohlc(tmp_path, monkeypatch):
    _snapshot(tmp_path, "krx", "2026-10-29", {"005930.KS": KR_BARS})
    monkeypatch.setenv(OHLC_DIR_ENV, str(tmp_path))
    _no_yfinance(monkeypatch)

    out = fetch_live_bars(
        "005930.KS", "2026-10-29", market="KR", as_of_session_closed=False, since="2026-10-27"
    )

    assert out["date"].tolist() == ["2026-10-27", "2026-10-28"]
    assert out.attrs == {
        "priceBasis": "adjusted_auto",
        "ohlcAsOf": "2026-10-29",
        "lastSession": "2026-10-29",
        "provider": "finnaut-ohlc",
    }


def test_fetch_live_bars_falls_back_to_yfinance(tmp_path, monkeypatch, capsys):
    _snapshot(tmp_path, "krx", "2026-10-29", {"005930.KS": KR_BARS})
    monkeypatch.setenv(OHLC_DIR_ENV, str(tmp_path))
    hist = pd.DataFrame({"Close": [50.0]}, index=pd.to_datetime(["2026-10-01T00:00:00Z"]))
    monkeypatch.setattr(
        prices_live,
        "get_ticker_history_with_provider",
        lambda symbol, period="10y": (hist, "stooq"),
    )

    out = fetch_live_bars("005930.KS", "2026-10-29", market="KR", since="2026-10-01")

    assert out.attrs == {"provider": "stooq", "priceBasis": "unadjusted_fallback"}
    assert "finnaut-ohlc fallback" in capsys.readouterr().err


def test_benchmark_reads_index_from_ohlc(tmp_path, monkeypatch):
    _snapshot(tmp_path, "krx", "2026-10-29", {"^KS11": KR_BARS})
    monkeypatch.setenv(OHLC_DIR_ENV, str(tmp_path))
    _no_yfinance(monkeypatch)

    bench = default_benchmark_provider("2026-10-29")("KR-KOSPI", since="2026-10-27")

    assert bench.attrs["provider"] == "finnaut-ohlc"


def test_run_meta_records_ohlc_snapshot(tmp_path, monkeypatch):
    sessions = pd.bdate_range("2026-09-01", "2026-10-29").strftime("%Y-%m-%d")
    bars = [_bar(d, 100 + i) for i, d in enumerate(sessions)]
    _snapshot(tmp_path, "krx", "2026-10-29", {"005930.KS": bars, "^KS11": bars})
    monkeypatch.setenv(OHLC_DIR_ENV, str(tmp_path))
    _no_yfinance(monkeypatch)
    daily = {
        "date": "2026-09-02",
        "market": "KR",
        "status": "pick",
        "stock": {"symbol": "005930.KS"},
    }

    _, performance = build_market_snapshots(
        dailies=[daily],
        market="KR",
        as_of_date="2026-10-29",
        price_provider=prices_live.default_price_provider("2026-10-29"),
        benchmark_provider=default_benchmark_provider("2026-10-29"),
        provider_label="yfinance",
    )

    assert performance["runMeta"]["provider"] == "finnaut-ohlc"
    assert performance["runMeta"]["ohlcAsOf"] == "2026-10-29"
    load_validator(PERFORMANCE_BUNDLE_SCHEMA_PATH).validate(performance)


def test_t_minus_1_bars_leave_calendar_horizon_immature(tmp_path, monkeypatch):
    # 1M target 2026-10-30 == asOfDate, but the stock's bars end 10-29: no early exit.
    sessions = pd.bdate_range("2026-09-01", "2026-10-29").strftime("%Y-%m-%d")
    bars = [_bar(d, 100 + i) for i, d in enumerate(sessions)]
    index = bars + [_bar("2026-10-30", 999)]
    _snapshot(tmp_path, "us", "2026-10-30", {"EBS": bars, "^GSPC": index})
    monkeypatch.setenv(OHLC_DIR_ENV, str(tmp_path))
    _no_yfinance(monkeypatch)
    daily = {"date": "2026-09-30", "market": "US", "status": "pick", "stock": {"symbol": "EBS"}}

    _, performance = build_market_snapshots(
        dailies=[daily],
        market="US",
        as_of_date="2026-10-30",
        price_provider=prices_live.default_price_provider("2026-10-30"),
        benchmark_provider=default_benchmark_provider("2026-10-30"),
        provider_label="yfinance",
    )

    one_month = next(m for m in performance["measurements"] if m["horizonId"] == "1M")
    assert one_month["completionStatus"] == "incomplete"
    assert one_month["asOfDate"] == "2026-10-29"
