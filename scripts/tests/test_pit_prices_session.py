"""PIT session cut: as_of_session_closed flag + market-TZ infer (#99)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from performance.pit_prices import filter_session_bars, infer_as_of_session_closed


def _bars(*days: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": list(days),
            "Open": [1.0] * len(days),
            "Close": [1.0] * len(days),
        }
    )


def test_closed_true_keeps_asof_session_even_if_host_today():
    today = date.today().isoformat()
    bars = _bars("2020-01-02", today, "2099-01-01")
    out = filter_session_bars(bars, today, as_of_session_closed=True)
    sessions = out["date"].tolist()
    assert today in sessions
    assert "2099-01-01" not in sessions


def test_closed_false_drops_asof_session():
    bars = _bars("2026-01-07", "2026-01-08", "2026-01-09")
    out = filter_session_bars(bars, "2026-01-08", as_of_session_closed=False)
    assert out["date"].tolist() == ["2026-01-07"]


def test_default_closed_true_includes_asof():
    bars = _bars("2026-01-07", "2026-01-08")
    out = filter_session_bars(bars, "2026-01-08")
    assert out["date"].tolist() == ["2026-01-07", "2026-01-08"]


def test_infer_kr_before_close_not_closed():
    as_of = "2026-09-08"
    now = datetime(2026, 9, 8, 14, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert infer_as_of_session_closed(as_of, market="KR", now=now) is False


def test_infer_kr_after_close_closed():
    as_of = "2026-09-08"
    now = datetime(2026, 9, 8, 16, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert infer_as_of_session_closed(as_of, market="KR", now=now) is True


def test_infer_historical_asof_closed():
    now = datetime(2026, 9, 8, 10, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert infer_as_of_session_closed("2026-09-01", market="KR", now=now) is True


def test_pit_prices_module_has_no_date_today_heuristic():
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "performance" / "pit_prices.py"
    text = src.read_text(encoding="utf-8")
    assert "date.today()" not in text
