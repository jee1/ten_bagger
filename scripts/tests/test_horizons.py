"""Horizon helper unit tests."""

from __future__ import annotations

import pandas as pd
from performance.horizons import (
    calendar_horizon_exit,
    calendar_horizon_target,
    session_horizon_exit,
    trading_sessions,
)


def test_trading_sessions_ascending():
    bars = pd.DataFrame(
        [
            {"date": "2026-01-03", "Close": 1},
            {"date": "2026-01-02", "Close": 1},
        ]
    )
    assert trading_sessions(bars) == ["2026-01-02", "2026-01-03"]


def test_session_horizon_exit_20th_after_entry():
    sessions = [f"2026-01-{d:02d}" for d in range(2, 32)]
    entry = "2026-01-02"
    exit_session = session_horizon_exit(sessions, entry, 20)
    assert exit_session == sessions[sessions.index(entry) + 20]


def test_calendar_horizon_target_one_month():
    assert calendar_horizon_target("2026-01-15", "1M") == "2026-02-15"


def test_calendar_horizon_exit_last_on_or_before_target():
    sessions = ["2026-01-10", "2026-01-15", "2026-02-14", "2026-02-16"]
    assert calendar_horizon_exit(sessions, "2026-01-15", "1M", "2026-03-01") == "2026-02-14"
