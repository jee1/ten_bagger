"""Screening configuration for Ten Bagger Daily."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
DAILY_DIR = CONTENT_DIR / "daily"
MANIFEST_PATH = CONTENT_DIR / "manifest.json"
UNIVERSE_DIR = Path(__file__).resolve().parent / "universe"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "daily-entry.schema.json"
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_TTL_SECONDS = 43_200  # 12 hours

COMPOSITE_THRESHOLD = 70.0
DUPLICATE_BAN_DAYS = 30
SCREEN_WORKERS = 8

# Minimum market cap (KRW) for KR universe; US listings omit market_cap.
MIN_MARKET_CAP_KR = 50_000_000_000  # 500억 KRW

WEIGHT_GROWTH = 0.40
WEIGHT_VALUATION = 0.30
WEIGHT_MOMENTUM = 0.20
WEIGHT_QUALITY = 0.10

# Growth scoring
GROWTH_REV_WEIGHT = 0.55
GROWTH_EARN_WEIGHT = 0.45
GROWTH_BASE_SCORE = 20.0
GROWTH_SCORE_MULTIPLIER = 2.2
MAX_GROWTH_PCT = 100.0  # clip yfinance spikes

# Valuation (P/E tiers)
PE_TIER_EXCELLENT = 12
PE_TIER_GOOD = 20
PE_TIER_FAIR = 35
PE_SCORE_EXCELLENT = 85
PE_SCORE_GOOD = 70
PE_SCORE_FAIR = 50
PE_SCORE_POOR = 30
PE_BLEND_WEIGHT = 0.55

PEG_TIER_EXCELLENT = 0.8
PEG_TIER_GOOD = 1.2
PEG_TIER_FAIR = 2.0
PEG_SCORE_EXCELLENT = 90
PEG_SCORE_GOOD = 75
PEG_SCORE_FAIR = 55
PEG_SCORE_POOR = 35
PEG_BLEND_WEIGHT = 0.45

# Momentum
MOMENTUM_MIN_HISTORY_DAYS = 30
MOMENTUM_LOOKBACK_DAYS = 126  # ~6 months
MOMENTUM_DEFAULT_SCORE = 40.0
MOMENTUM_RET_BASE = 35.0
MOMENTUM_RET_MULTIPLIER = 1.5
MOMENTUM_RET_WEIGHT = 0.6
MOMENTUM_HIGH_WEIGHT = 0.4
MOMENTUM_RECOVERY_LOW = -25
MOMENTUM_RECOVERY_HIGH = -5
MOMENTUM_RECOVERY_SCORE = 75
MOMENTUM_NEAR_HIGH_SCORE = 65
MOMENTUM_DEEP_PULLBACK_SCORE = 45

# Quality
QUALITY_ROE_MULTIPLIER = 2.5
QUALITY_ROE_DEFAULT = 30
QUALITY_ROE_WEIGHT = 0.45
QUALITY_DEBT_WEIGHT = 0.25
QUALITY_MARGIN_WEIGHT = 0.30
QUALITY_DEBT_EXCELLENT = 50
QUALITY_DEBT_GOOD = 100
QUALITY_DEBT_FAIR = 200
QUALITY_DEBT_SCORE_EXCELLENT = 85
QUALITY_DEBT_SCORE_GOOD = 70
QUALITY_DEBT_SCORE_FAIR = 50
QUALITY_DEBT_SCORE_POOR = 30
QUALITY_MARGIN_BASE = 30.0
QUALITY_MARGIN_MULTIPLIER = 2.0


@dataclass(frozen=True)
class UniverseSymbol:
    symbol: str
    name_ko: str
    name_en: str
    exchange: str
    currency: str
    market_cap: int | None = None


def market_for_date(date_str: str) -> str:
    """Odd day -> KR, even day -> US (calendar day in KST context)."""
    day = int(date_str.split("-")[2])
    return "KR" if day % 2 == 1 else "US"
