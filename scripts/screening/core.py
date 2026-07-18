"""Screening orchestration: universe loading, filters, and per-symbol scoring dispatch."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from config import (
    COMPOSITE_THRESHOLD,
    MIN_MARKET_CAP_KR,
    MIN_MARKET_CAP_US,
    SCORE_VERSION,
    SCREEN_WORKERS,
    UNIVERSE_DIR,
    UniverseSymbol,
)
from scoring.common import _optional_float, _safe_float
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
from scoring.valuation import _score_valuation
from yf_cache import get_ticker_history, get_ticker_info

logger = logging.getLogger(__name__)


@dataclass
class ScreenStats:
    screened: int = 0
    passed_threshold: int = 0
    skipped_recent: int = 0
    skipped_market_cap: int = 0
    skipped_red_flags: int = 0
    no_data: int = 0
    errors: int = 0
    error_samples: list[str] = field(default_factory=list)


def load_universe(market: str) -> list[UniverseSymbol]:
    path = UNIVERSE_DIR / ("kr.json" if market == "KR" else "us.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        UniverseSymbol(
            symbol=item["symbol"],
            name_ko=item["name_ko"],
            name_en=item["name_en"],
            exchange=item["exchange"],
            currency=item["currency"],
            market_cap=item.get("market_cap"),
        )
        for item in raw
    ]


def passes_market_cap_filter(
    meta: UniverseSymbol,
    market: str,
    info: dict[str, Any] | None = None,
) -> bool:
    if market == "KR":
        if meta.market_cap is None:
            return True
        return meta.market_cap >= MIN_MARKET_CAP_KR
    if market == "US":
        if info is None:
            return True
        cap = _safe_float(info.get("marketCap"))
        if cap <= 0:
            return True
        return cap >= MIN_MARKET_CAP_US
    return True


def passes_red_flags(info: dict[str, Any]) -> bool:
    """Hard filters for distressed balance sheets (Epic #23).

    Missing book/P/B fields are not treated as negative equity — only explicit
    negative values fail. Dual-negative cash flow requires both fields present.
    """
    book_value = _optional_float(info.get("bookValue"))
    price_to_book = _optional_float(info.get("priceToBook"))
    if book_value is not None and book_value < 0:
        return False
    if price_to_book is not None and price_to_book < 0:
        return False

    free_cashflow = _optional_float(info.get("freeCashflow"))
    operating_cashflow = _optional_float(info.get("operatingCashflow"))
    if (
        free_cashflow is not None
        and operating_cashflow is not None
        and free_cashflow < 0
        and operating_cashflow < 0
    ):
        return False
    return True


def score_symbol(
    meta: UniverseSymbol,
    market: str,
    info: dict[str, Any] | None = None,
    *,
    score_version: int = SCORE_VERSION,
) -> ScoreResult | None:
    if info is None:
        info = get_ticker_info(meta.symbol)
    if not info.get("symbol") and not info.get("shortName"):
        return None
    if not passes_market_cap_filter(meta, market, info):
        return None
    if score_version >= 2 and not passes_red_flags(info):
        return None

    long_name = info.get("longName") or info.get("shortName")
    if long_name:
        meta = UniverseSymbol(
            symbol=meta.symbol,
            name_ko=meta.name_ko,
            name_en=str(long_name),
            exchange=meta.exchange,
            currency=meta.currency,
            market_cap=meta.market_cap,
        )

    hist = get_ticker_history(meta.symbol)

    if score_version < 2:
        growth, g_m = _score_growth_v1(info)
        valuation, v_m = _score_valuation_v1(info)
        momentum, m_m = _score_momentum_v1(hist)
        quality, q_m = _score_quality_v1(info)
        size, s_m, entry, e_m = 0.0, {}, 0.0, {}
        composite = _composite_v1(growth, valuation, momentum, quality)
        version = 1
    else:
        size, s_m = _score_size(meta, info, market)
        growth, g_m = _score_growth(info)
        valuation, v_m = _score_valuation(info, meta)
        entry, e_m = _score_entry(hist)
        momentum, m_m = _score_momentum(hist)
        quality, q_m = _score_quality(info)
        composite = _composite_v2(size, growth, valuation, quality, entry, momentum)
        version = 2

    return ScoreResult(
        symbol=meta.symbol,
        meta=meta,
        size=round(size, 1),
        growth=round(growth, 1),
        valuation=round(valuation, 1),
        entry=round(entry, 1),
        momentum=round(momentum, 1),
        quality=round(quality, 1),
        composite=round(composite, 1),
        metrics={**s_m, **g_m, **v_m, **e_m, **m_m, **q_m},
        score_version=version,
    )


def screen_market(
    market: str,
    exclude_symbols: set[str],
    *,
    score_version: int = SCORE_VERSION,
) -> tuple[list[ScoreResult], ScreenStats]:
    universe = load_universe(market)
    stats = ScreenStats(skipped_recent=len(exclude_symbols))

    to_screen: list[UniverseSymbol] = []
    for meta in universe:
        if meta.symbol in exclude_symbols:
            continue
        if not passes_market_cap_filter(meta, market):
            stats.skipped_market_cap += 1
            continue
        to_screen.append(meta)

    stats.screened = len(to_screen)
    results: list[ScoreResult] = []

    def _score_one(meta: UniverseSymbol) -> tuple[str, ScoreResult | None]:
        info = get_ticker_info(meta.symbol)
        if not info.get("symbol") and not info.get("shortName"):
            return ("no_data", None)
        if not passes_market_cap_filter(meta, market, info):
            return ("skip_mcap", None)
        if score_version >= 2 and not passes_red_flags(info):
            return ("skip_red", None)
        return ("ok", score_symbol(meta, market, info, score_version=score_version))

    workers = min(SCREEN_WORKERS, max(1, stats.screened))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_score_one, meta): meta for meta in to_screen}
        for future in as_completed(futures):
            meta = futures[future]
            try:
                status, scored = future.result()
            except Exception as exc:
                stats.errors += 1
                if len(stats.error_samples) < 5:
                    stats.error_samples.append(f"{meta.symbol}: {exc}")
                logger.warning("Screen error for %s: %s", meta.symbol, exc)
                continue

            if status == "skip_mcap":
                stats.skipped_market_cap += 1
                continue
            if status == "skip_red":
                stats.skipped_red_flags += 1
                continue
            if status == "no_data" or scored is None:
                stats.no_data += 1
                continue
            if scored.composite >= COMPOSITE_THRESHOLD:
                results.append(scored)
                stats.passed_threshold += 1

    results.sort(key=lambda r: r.composite, reverse=True)
    logger.info(
        "Screen %s v%d: screened=%d passed=%d no_data=%d errors=%d skipped_mcap=%d skipped_red=%d",
        market,
        score_version,
        stats.screened,
        stats.passed_threshold,
        stats.no_data,
        stats.errors,
        stats.skipped_market_cap,
        stats.skipped_red_flags,
    )
    if stats.error_samples:
        logger.warning("Sample errors: %s", "; ".join(stats.error_samples))

    return results, stats
