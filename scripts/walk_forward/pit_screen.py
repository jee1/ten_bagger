"""Point-in-time screening wrapper for walk-forward folds."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import screening.core as screening_core
from performance.pit_prices import filter_session_bars
from screening.core import screen_market

from calibration.overrides import apply_candidate_overrides


@contextmanager
def _pit_history(as_of_date: str) -> Iterator[None]:
    original = screening_core.get_ticker_history

    def filtered(symbol: str, period: str = "1y"):
        return filter_session_bars(original(symbol, period=period), as_of_date)

    with patch.object(screening_core, "get_ticker_history", filtered):
        yield


def pit_screen_day(
    market: str,
    as_of_date: str,
    exclude_symbols: set[str],
    *,
    score_version: int = 2,
    threshold_override: float | None = None,
    weight_overrides: dict[str, Any] | None = None,
) -> tuple[str | None, bool]:
    """Run screen_market at *as_of_date* with PIT-filtered price history.

    Returns ``(symbol, no_pick)`` — top pick symbol or ``(None, True)``.
    Optional analysis overrides are process-local and never write ``config.py``.
    """
    with (
        apply_candidate_overrides(threshold_override, weight_overrides),
        _pit_history(as_of_date),
    ):
        results, _stats = screen_market(
            market,
            exclude_symbols,
            score_version=score_version,
        )
    if not results:
        return None, True
    return results[0].symbol, False


def bind_pit_fn(
    *,
    threshold_override: float | None = None,
    weight_overrides: dict[str, Any] | None = None,
):
    """Return a pit_fn(market, as_of, exclude) closing over analysis overrides."""

    def _pit(market: str, as_of_date: str, exclude_symbols: set[str]) -> tuple[str | None, bool]:
        return pit_screen_day(
            market,
            as_of_date,
            exclude_symbols,
            threshold_override=threshold_override,
            weight_overrides=weight_overrides,
        )

    return _pit
