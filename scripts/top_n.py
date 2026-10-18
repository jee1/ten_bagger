"""Top-N helpers for daily transparency (Issue #72)."""

from __future__ import annotations

from typing import Any

import config as cfg
from scoring.models import ScoreResult


def select_pick(
    results: list[ScoreResult],
    threshold: float | None = None,
) -> ScoreResult | None:
    """First result with composite >= threshold (list must already be ranked)."""
    thr = cfg.COMPOSITE_THRESHOLD if threshold is None else threshold
    for result in results:
        if result.composite >= thr:
            return result
    return None


_SCORE_AXES = ("composite", "size", "growth", "valuation", "entry", "momentum", "quality")


def _scores_dict(result: ScoreResult | None, *, include_threshold: bool) -> dict[str, Any]:
    if result is None:
        scores: dict[str, Any] = {axis: 0 for axis in _SCORE_AXES}
        version = cfg.SCORE_VERSION
    else:
        scores = {axis: getattr(result, axis) for axis in _SCORE_AXES}
        version = result.score_version
    if include_threshold:
        scores["threshold"] = cfg.COMPOSITE_THRESHOLD
    scores["version"] = version
    return scores


def _meta_dict(stats: Any, generated_at: str) -> dict[str, Any]:
    return {
        "generatedAt": generated_at,
        "candidatesScreened": stats.screened,
        "excludedRecent": stats.skipped_recent,
        "skippedMarketCap": stats.skipped_market_cap,
        "skippedRedFlags": stats.skipped_red_flags,
        "noData": stats.no_data,
        "errors": stats.errors,
    }


def build_top_candidates(
    results: list[ScoreResult],
    n: int | None = None,
) -> list[dict[str, Any]] | None:
    """Serialize ranked Top-N rows, or None when there are no scored results."""
    limit = cfg.TOP_N if n is None else n
    if not results:
        return None
    out: list[dict[str, Any]] = []
    for i, result in enumerate(results[:limit], start=1):
        out.append(
            {
                "rank": i,
                "symbol": result.symbol,
                "name": {"ko": result.meta.name_ko, "en": result.meta.name_en},
                "exchange": result.meta.exchange,
                "currency": result.meta.currency,
                "scores": _scores_dict(result, include_threshold=False),
            }
        )
    return out


def rank_key(result: ScoreResult) -> tuple[float, str]:
    """Sort key: composite descending, symbol ascending."""
    return (-result.composite, result.symbol)
