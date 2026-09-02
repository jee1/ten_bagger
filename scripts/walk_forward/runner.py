"""Walk-forward fold runner: PIT screening + OOS pick collection."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from config import DUPLICATE_BAN_DAYS, market_for_date

from walk_forward.config import RunConfig
from walk_forward.pit_screen import pit_screen_day

PitFn = Callable[[str, str, set[str]], tuple[str | None, bool]]
MeasureFn = Callable[[list[dict[str, Any]], RunConfig, str], list[dict[str, Any]]]


def _parse_iso(day: str) -> date:
    return date.fromisoformat(day)


def _excluded_symbols(recent: list[tuple[str, date]], session: date) -> set[str]:
    excluded: set[str] = set()
    for symbol, pick_date in recent:
        if 0 <= (session - pick_date).days <= DUPLICATE_BAN_DAYS:
            excluded.add(symbol)
    return excluded


def _count_train_picks(
    fold: dict[str, Any],
    markets: set[str],
    pit_fn: PitFn,
    recent: list[tuple[str, date]],
) -> int:
    count = 0
    for session_str in fold["trainSessions"]:
        market = market_for_date(session_str)
        if market not in markets:
            continue
        session = _parse_iso(session_str)
        exclude = _excluded_symbols(recent, session)
        symbol, no_pick = pit_fn(market, session_str, exclude)
        if not no_pick and symbol:
            count += 1
            recent.append((symbol, session))
    return count


def run_folds(
    run_config: RunConfig,
    folds: list[dict[str, Any]],
    measure_fn: MeasureFn,
    *,
    pit_fn: PitFn | None = None,
    as_of_date: str | None = None,
) -> list[dict[str, Any]]:
    """Execute rolling folds; collect OOS picks and measurements per fold."""
    pit = pit_fn or pit_screen_day
    markets = set(run_config.markets)
    as_of = as_of_date or run_config.foldSpec["endDate"]
    recent: list[tuple[str, date]] = []
    results: list[dict[str, Any]] = []

    for fold in folds:
        train_picks = _count_train_picks(fold, markets, pit, recent)
        if train_picks == 0:
            results.append(
                {
                    **fold,
                    "status": "skipped_empty_train",
                    "pickDays": 0,
                    "noPickDays": 0,
                    "picks": [],
                    "measurements": [],
                    "horizons": [],
                }
            )
            continue

        picks: list[dict[str, Any]] = []
        pick_days = 0
        no_pick_days = 0

        for session_str in fold["oosSessions"]:
            market = market_for_date(session_str)
            if market not in markets:
                continue
            session = _parse_iso(session_str)
            exclude = _excluded_symbols(recent, session)
            symbol, no_pick = pit(market, session_str, exclude)
            if no_pick or not symbol:
                no_pick_days += 1
                continue
            pick_days += 1
            picks.append({"pickDate": session_str, "symbol": symbol, "market": market})
            recent.append((symbol, session))

        measurements = measure_fn(picks, run_config, as_of) if picks else []
        oos_end = _parse_iso(fold["oosRange"]["end"])
        incomplete_oos = oos_end > _parse_iso(as_of)
        incomplete_meas = any(
            m.get("completionStatus") != "complete"
            for m in measurements
            if m.get("horizonId") in ("H20", "H60")
        )
        if incomplete_oos or (picks and incomplete_meas):
            status = "incomplete_horizon"
        else:
            status = "complete"

        results.append(
            {
                **fold,
                "status": status,
                "pickDays": pick_days,
                "noPickDays": no_pick_days,
                "picks": picks,
                "measurements": measurements,
                "horizons": [],
            }
        )

    return results
