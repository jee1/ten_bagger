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
                "scores": {
                    "composite": result.composite,
                    "size": result.size,
                    "growth": result.growth,
                    "valuation": result.valuation,
                    "entry": result.entry,
                    "momentum": result.momentum,
                    "quality": result.quality,
                    "version": result.score_version,
                },
            }
        )
    return out


def rank_key(result: ScoreResult) -> tuple[float, str]:
    """Sort key: composite descending, symbol ascending."""
    return (-result.composite, result.symbol)
