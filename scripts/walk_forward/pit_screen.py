"""Point-in-time screening wrapper for walk-forward folds."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import patch

import screening.core as screening_core
from performance.pit_prices import filter_session_bars
from screening.core import screen_market


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
) -> tuple[str | None, bool]:
    """Run screen_market at *as_of_date* with PIT-filtered price history.

    Returns ``(symbol, no_pick)`` — top pick symbol or ``(None, True)``.
    """
    with _pit_history(as_of_date):
        results, _stats = screen_market(
            market,
            exclude_symbols,
            score_version=score_version,
        )
    if not results:
        return None, True
    return results[0].symbol, False
