"""Point-in-time screening wrapper for walk-forward folds."""

from __future__ import annotations

from typing import Any

import screening.core as screening_core
from calibration.overrides import apply_candidate_overrides
from config import UniverseSymbol
from performance.pit_prices import filter_session_bars
from screening.core import screen_market
from top_n import select_pick
from walk_forward.fundamentals_pit import load_fundamentals_snapshot


def _pit_history(as_of_date: str):
    def filtered(symbol: str, period: str = "1y"):
        bars = screening_core.get_ticker_history(symbol, period=period)
        return filter_session_bars(bars, as_of_date)

    return filtered


def _snapshot_sources(market: str, as_of_date: str):
    """Screen the daily run's captured symbols with their captured info (#175 stage 2).

    Without a snapshot, live info stays in place; the report flags that session as
    ``fundamentals_not_pit``.

    ponytail: the universe is the set the daily run screened that day, so symbols it
    excluded as recent picks (~30) cannot be selected even when this run's own
    exclusions differ. Upgrade: capture info for excluded symbols too.
    """
    snapshot = load_fundamentals_snapshot(market, as_of_date)
    if snapshot is None:
        return None, None

    current = {meta.symbol: meta for meta in screening_core.load_universe(market)}
    currency = "KRW" if market == "KR" else "USD"
    # market_cap=None: the daily run already applied its listing-cap prefilter.
    universe = [
        UniverseSymbol(
            symbol=symbol,
            name_ko=current[symbol].name_ko if symbol in current else symbol,
            name_en=current[symbol].name_en if symbol in current else symbol,
            exchange=current[symbol].exchange if symbol in current else "",
            currency=current[symbol].currency if symbol in current else currency,
            market_cap=None,
        )
        for symbol in sorted(snapshot.infos)
    ]

    def snapshot_info(symbol: str) -> dict:
        info = snapshot.infos.get(symbol)
        return {"symbol": symbol, **info} if info else {}

    return universe, snapshot_info


def pit_screen_day(
    market: str,
    as_of_date: str,
    exclude_symbols: set[str],
    *,
    score_version: int = 2,
    threshold_override: float | None = None,
    weight_overrides: dict[str, Any] | None = None,
) -> tuple[str | None, bool]:
    """Run screen_market at *as_of_date* with PIT-filtered prices and fundamentals.

    Returns ``(symbol, no_pick)``. Top pick symbol, or ``(None, True)``.
    Optional analysis overrides are process-local and never write ``config.py``.
    """
    universe, info_fn = _snapshot_sources(market, as_of_date)
    with apply_candidate_overrides(threshold_override, weight_overrides):
        results, _stats = screen_market(
            market,
            exclude_symbols,
            score_version=score_version,
            info_fn=info_fn,
            history_fn=_pit_history(as_of_date),
            universe=universe,
        )
    # screen_market may include below-threshold scores (#72); pick is threshold-gated
    pick = select_pick(results)
    if pick is None:
        return None, True
    return pick.symbol, False


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
