"""Forward-return measurement (ADR 0002)."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import pandas as pd

from performance.horizons import (
    HORIZON_IDS,
    calendar_horizon_exit,
    calendar_horizon_target,
    session_horizon_exit,
    trading_sessions,
)
from performance.pit_prices import filter_session_bars, prefer_adjusted

BENCHMARK_IDS = {"KR": "KR-KOSPI", "US": "US-SPX"}

_SESSION_HORIZON_DAYS = {"H20": 20, "H60": 60}


def _bar_on_session(bars: pd.DataFrame, session: str) -> pd.Series | None:
    if "date" in bars.columns:
        mask = pd.to_datetime(bars["date"]).dt.strftime("%Y-%m-%d") == session
        rows = bars.loc[mask]
    else:
        rows = bars.loc[pd.to_datetime(bars.index).strftime("%Y-%m-%d") == session]
    if rows.empty:
        return None
    return rows.iloc[-1]


def _price(row: pd.Series, prefer: str) -> float | None:
    for col in (prefer, "Close", "Open"):
        if col in row.index and pd.notna(row[col]):
            val = float(row[col])
            if math.isfinite(val):
                return val
    return None


def resolve_entry(bars: pd.DataFrame, pick_date: str, as_of_date: str) -> dict[str, Any]:
    """Resolve entry session/price or incomplete reason."""
    filtered = filter_session_bars(bars, as_of_date)
    adjusted, _ = prefer_adjusted(filtered)
    sessions = trading_sessions(adjusted)
    after = [s for s in sessions if s > pick_date]
    if not after:
        return {"status": "incomplete", "incompleteReason": "missing_entry"}
    entry_session = after[0]
    row = _bar_on_session(adjusted, entry_session)
    if row is None:
        return {"status": "incomplete", "incompleteReason": "missing_entry"}
    entry_price = _price(row, "Open")
    if entry_price is None:
        entry_price = _price(row, "Close")
    if entry_price is None:
        return {"status": "incomplete", "incompleteReason": "missing_entry"}
    if entry_price <= 0 or not math.isfinite(entry_price):
        return {"status": "incomplete", "incompleteReason": "invalid_entry"}
    return {
        "status": "ok",
        "entrySession": entry_session,
        "entryPrice": entry_price,
        "bars": adjusted,
        "sessions": sessions,
    }


def survivorship_flag(bars: pd.DataFrame, as_of_date: str) -> str:
    """listed | delisted | unknown based on last session vs asOfDate."""
    filtered = filter_session_bars(bars, as_of_date)
    sessions = trading_sessions(filtered)
    if not sessions:
        return "unknown"
    last = sessions[-1]
    if last >= as_of_date:
        return "listed"
    gap_days = (datetime.fromisoformat(as_of_date) - datetime.fromisoformat(last)).days
    # ponytail: 7-day gap proxy for halted/delisted; upgrade path = vendor delist flag
    if gap_days >= 7:
        return "delisted"
    return "unknown"


def _base_measurement(
    *,
    market: str,
    pick_date: str,
    symbol: str,
    horizon_id: str,
    as_of_date: str,
    surv: str,
) -> dict[str, Any]:
    m: dict[str, Any] = {
        "market": market,
        "pickDate": pick_date,
        "symbol": symbol,
        "horizonId": horizon_id,
        "benchmarkId": BENCHMARK_IDS[market],
        "completionStatus": "incomplete",
        "benchmarkCompletionStatus": "incomplete",
        "survivorshipFlag": surv,
        "asOfDate": as_of_date,
    }
    if horizon_id in _SESSION_HORIZON_DAYS:
        m["horizonDays"] = _SESSION_HORIZON_DAYS[horizon_id]
    return m


def _measure_benchmark(
    *,
    benchmark_bars: pd.DataFrame | None,
    entry_session: str,
    exit_session: str | None,
    entry_price: float,
    as_of_date: str,
    pick_complete: bool,
) -> tuple[str, float | None, str | None]:
    if not pick_complete or exit_session is None:
        return "incomplete", None, "missing_benchmark_series"
    if benchmark_bars is None or benchmark_bars.empty:
        return "incomplete", None, "missing_benchmark_series"
    filtered = filter_session_bars(benchmark_bars, as_of_date)
    adjusted, _ = prefer_adjusted(filtered)
    sessions = trading_sessions(adjusted)
    if entry_session not in sessions:
        return "incomplete", None, "missing_benchmark_series"
    if exit_session not in sessions:
        return "incomplete", None, "missing_benchmark_exit"
    entry_row = _bar_on_session(adjusted, entry_session)
    exit_row = _bar_on_session(adjusted, exit_session)
    if entry_row is None or exit_row is None:
        return "incomplete", None, "missing_benchmark_exit"
    b_entry = _price(entry_row, "Open") or _price(entry_row, "Close")
    b_exit = _price(exit_row, "Close") or _price(exit_row, "Open")
    if b_entry is None or b_exit is None or b_entry <= 0:
        return "incomplete", None, "missing_benchmark_exit"
    return "complete", (b_exit - b_entry) / b_entry, None


def measure_pick_horizon(
    *,
    bars: pd.DataFrame,
    benchmark_bars: pd.DataFrame | None,
    pick_date: str,
    as_of_date: str,
    market: str,
    symbol: str,
    horizon_id: str,
) -> dict[str, Any]:
    """Return PerformanceMeasurement fields for one pick × horizon."""
    surv = survivorship_flag(bars, as_of_date)
    m = _base_measurement(
        market=market,
        pick_date=pick_date,
        symbol=symbol,
        horizon_id=horizon_id,
        as_of_date=as_of_date,
        surv=surv,
    )
    entry = resolve_entry(bars, pick_date, as_of_date)
    if entry["status"] != "ok":
        reason = entry["incompleteReason"]
        if reason == "missing_entry" and surv == "delisted":
            reason = "insufficient_history"
        m["incompleteReason"] = reason
        m["benchmarkIncompleteReason"] = "missing_benchmark_series"
        return m

    entry_session = entry["entrySession"]
    entry_price = entry["entryPrice"]
    sessions = entry["sessions"]
    adjusted = entry["bars"]

    exit_session: str | None
    incomplete_reason: str | None = None

    if horizon_id in _SESSION_HORIZON_DAYS:
        n = _SESSION_HORIZON_DAYS[horizon_id]
        exit_session = session_horizon_exit(sessions, entry_session, n)
        if exit_session is None:
            if len(sessions) - 1 - sessions.index(entry_session) < n:
                incomplete_reason = (
                    "horizon_beyond_asof"
                    if surv == "listed"
                    else "missing_exit"
                )
            else:
                incomplete_reason = "missing_exit"
        elif exit_session > as_of_date:
            incomplete_reason = "horizon_beyond_asof"
            exit_session = None
    elif horizon_id in ("1M", "3M", "6M", "1Y", "3Y", "5Y"):
        target = calendar_horizon_target(pick_date, horizon_id)
        exit_session = calendar_horizon_exit(
            sessions, pick_date, horizon_id, as_of_date
        )
        if exit_session is None:
            incomplete_reason = (
                "horizon_beyond_asof" if target > as_of_date else "missing_exit"
            )
        elif exit_session > as_of_date:
            incomplete_reason = "horizon_beyond_asof"
            exit_session = None
    else:
        raise ValueError(f"unknown horizon: {horizon_id}")

    pick_complete = False
    exit_price: float | None = None
    forward_return: float | None = None

    after_entry = len(sessions) - 1 - sessions.index(entry_session)

    if exit_session is None and horizon_id in _SESSION_HORIZON_DAYS:
        n = _SESSION_HORIZON_DAYS[horizon_id]
        if after_entry < n:
            if after_entry <= 1:
                incomplete_reason = "insufficient_history"
            elif surv == "delisted":
                exit_session = sessions[-1]
            else:
                incomplete_reason = incomplete_reason or "missing_exit"

    if exit_session is not None and exit_session not in sessions:
        incomplete_reason = incomplete_reason or "missing_exit"
        exit_session = None

    if exit_session is not None:
        exit_row = _bar_on_session(adjusted, exit_session)
        if exit_row is None:
            incomplete_reason = incomplete_reason or "missing_exit"
        else:
            exit_price = _price(exit_row, "Close") or _price(exit_row, "Open")
            if exit_price is None:
                incomplete_reason = incomplete_reason or "missing_exit"
            else:
                pick_complete = True
                forward_return = (exit_price - entry_price) / entry_price

    if not pick_complete:
        m["incompleteReason"] = incomplete_reason or "missing_exit"
        bench_status, _, bench_reason = _measure_benchmark(
            benchmark_bars=benchmark_bars,
            entry_session=entry_session,
            exit_session=exit_session,
            entry_price=entry_price,
            as_of_date=as_of_date,
            pick_complete=False,
        )
        m["benchmarkCompletionStatus"] = bench_status
        m["benchmarkIncompleteReason"] = bench_reason
        return m

    m["completionStatus"] = "complete"
    m["entryPrice"] = entry_price
    m["exitPrice"] = exit_price
    m["forwardReturn"] = forward_return

    bench_status, bench_ret, bench_reason = _measure_benchmark(
        benchmark_bars=benchmark_bars,
        entry_session=entry_session,
        exit_session=exit_session,
        entry_price=entry_price,
        as_of_date=as_of_date,
        pick_complete=True,
    )
    m["benchmarkCompletionStatus"] = bench_status
    if bench_status == "complete":
        m["benchmarkReturn"] = bench_ret
    else:
        m["benchmarkIncompleteReason"] = bench_reason
    return m


def measure_all_horizons(
    *,
    bars: pd.DataFrame,
    benchmark_bars: pd.DataFrame | None,
    pick_date: str,
    as_of_date: str,
    market: str,
    symbol: str,
) -> list[dict[str, Any]]:
    """Emit all eight horizon rows (never omit)."""
    return [
        measure_pick_horizon(
            bars=bars,
            benchmark_bars=benchmark_bars,
            pick_date=pick_date,
            as_of_date=as_of_date,
            market=market,
            symbol=symbol,
            horizon_id=hid,
        )
        for hid in HORIZON_IDS
    ]
