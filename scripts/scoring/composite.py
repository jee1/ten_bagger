"""v2 composite blend across all six score dimensions."""

from __future__ import annotations

from config import (
    WEIGHT_ENTRY,
    WEIGHT_GROWTH,
    WEIGHT_MOMENTUM,
    WEIGHT_QUALITY,
    WEIGHT_SIZE,
    WEIGHT_VALUATION,
)


def _composite_v2(
    size: float,
    growth: float,
    valuation: float,
    quality: float,
    entry: float,
    momentum: float,
) -> float:
    return (
        size * WEIGHT_SIZE
        + valuation * WEIGHT_VALUATION
        + growth * WEIGHT_GROWTH
        + quality * WEIGHT_QUALITY
        + entry * WEIGHT_ENTRY
        + momentum * WEIGHT_MOMENTUM
    )
