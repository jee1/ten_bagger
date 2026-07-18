"""Shared scoring dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import SCORE_VERSION, UniverseSymbol


@dataclass
class ScoreResult:
    symbol: str
    meta: UniverseSymbol
    size: float
    growth: float
    valuation: float
    entry: float
    momentum: float
    quality: float
    composite: float
    metrics: dict[str, Any]
    score_version: int = SCORE_VERSION
