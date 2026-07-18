"""Backward-compatible re-exports for the old monolithic screening module.

Real implementations live in scoring/, screening/, and reasoning.py
(Epic #27 / #33, #34). Import from those modules directly in new code;
this shim exists so pre-existing imports (`from screen import ...`) keep
working.
"""

from __future__ import annotations

from reasoning import build_reasoning
from screening.core import (
    ScreenStats,
    load_universe,
    passes_market_cap_filter,
    passes_red_flags,
    score_symbol,
    screen_market,
)
from scoring.common import (
    _blended_growth_pct,
    _clamp,
    _clip_growth_pct,
    _optional_float,
    _resolve_market_cap,
    _safe_float,
)
from scoring.composite import _composite_v2
from scoring.entry import _score_entry
from scoring.growth import _score_growth
from scoring.models import ScoreResult
from scoring.momentum import _score_momentum
from scoring.quality import _score_quality
from scoring.size import _score_size
from scoring.v1 import (
    _composite_v1,
    _score_growth_v1,
    _score_momentum_v1,
    _score_quality_v1,
    _score_valuation_v1,
)
from scoring.valuation import (
    _score_fcf_yield,
    _score_pe_peg,
    _score_price_to_book,
    _score_valuation,
)

__all__ = [
    "ScoreResult",
    "ScreenStats",
    "build_reasoning",
    "load_universe",
    "passes_market_cap_filter",
    "passes_red_flags",
    "score_symbol",
    "screen_market",
    "_blended_growth_pct",
    "_clamp",
    "_clip_growth_pct",
    "_optional_float",
    "_resolve_market_cap",
    "_safe_float",
    "_composite_v1",
    "_composite_v2",
    "_score_entry",
    "_score_fcf_yield",
    "_score_growth",
    "_score_growth_v1",
    "_score_momentum",
    "_score_momentum_v1",
    "_score_pe_peg",
    "_score_price_to_book",
    "_score_quality",
    "_score_quality_v1",
    "_score_size",
    "_score_valuation",
    "_score_valuation_v1",
]
