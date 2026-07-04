"""Screening configuration for Ten Bagger Daily."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
DAILY_DIR = CONTENT_DIR / "daily"
MANIFEST_PATH = CONTENT_DIR / "manifest.json"
UNIVERSE_DIR = Path(__file__).resolve().parent / "universe"

COMPOSITE_THRESHOLD = 70.0
DUPLICATE_BAN_DAYS = 30

WEIGHT_GROWTH = 0.40
WEIGHT_VALUATION = 0.30
WEIGHT_MOMENTUM = 0.20
WEIGHT_QUALITY = 0.10


@dataclass(frozen=True)
class UniverseSymbol:
    symbol: str
    name_ko: str
    name_en: str
    exchange: str
    currency: str


def market_for_date(date_str: str) -> str:
    """Odd day -> KR, even day -> US (calendar day in KST context)."""
    day = int(date_str.split("-")[2])
    return "KR" if day % 2 == 1 else "US"
