#!/usr/bin/env python3
"""Generate daily JSON report and update manifest."""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, timedelta

from config import (
    DAILY_DIR,
    DUPLICATE_BAN_DAYS,
    market_for_date,
)
from moat_megatrend_classification import classify_top_candidate_moat_megatrend
from pit_snapshot import PitFundamentalsCollector, PitWriteResult, write_daily_pit_snapshots
from reasoning import build_reasoning
from risk_classification import apply_pick_risk_reasoning, classify_top_candidate_risks
from screening.core import screen_market
from stock_profile import build_stock_profile
from sync_manifest import sync_manifest
from time_utils import now_kst
from top_n import _meta_dict, _scores_dict, build_top_candidates, select_pick
from yf_cache import get_ticker_info

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def recent_pick_symbols(days: int, target: date) -> set[str]:
    symbols: set[str] = set()
    if not DAILY_DIR.exists():
        return symbols

    for path in sorted(DAILY_DIR.glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise json.JSONDecodeError(f"{path}: {exc.msg}", exc.doc, exc.pos) from exc
        entry_date = _parse_date(entry["date"])
        # Both directions: a backfilled date must not repeat a pick already published after it.
        if entry_date == target or abs(target - entry_date) > timedelta(days=days):
            continue
        if entry.get("status") == "pick" and entry.get("stock"):
            symbols.add(entry["stock"]["symbol"])
    return symbols


def build_no_pick(target: str, market: str, stats, top_candidates=None) -> dict:
    now = now_kst().isoformat(timespec="seconds")
    entry = {
        "date": target,
        "market": market,
        "status": "no_pick",
        "scores": _scores_dict(None, include_threshold=True),
        "meta": _meta_dict(stats, now),
    }
    if top_candidates:
        entry["topCandidates"] = top_candidates
    return entry


def build_pick(target: str, market: str, result, stats, top_candidates=None) -> dict:
    now = now_kst().isoformat(timespec="seconds")
    stock: dict = {
        "symbol": result.symbol,
        "name": {"ko": result.meta.name_ko, "en": result.meta.name_en},
        "exchange": result.meta.exchange,
        "currency": result.meta.currency,
    }
    info = result.info if result.info is not None else get_ticker_info(result.symbol)
    profile = build_stock_profile(
        info,
        name_ko=result.meta.name_ko,
        name_en=result.meta.name_en,
    )
    if profile:
        stock["profile"] = profile

    reasoning = build_reasoning(result)
    reasoning = apply_pick_risk_reasoning(
        reasoning,
        pick_symbol=result.symbol,
        top_candidates=top_candidates,
    )

    entry = {
        "date": target,
        "market": market,
        "status": "pick",
        "stock": stock,
        "scores": _scores_dict(result, include_threshold=True),
        "reasoning": reasoning,
        "meta": _meta_dict(stats, now),
    }
    if top_candidates:
        entry["topCandidates"] = top_candidates
    return entry


MAX_PROVIDER_ERROR_RATE = 0.20


def _provider_error_rate_exceeds(stats) -> bool:
    screened = stats.screened
    if screened <= 0:
        return False
    return (stats.errors + stats.no_data) / screened > MAX_PROVIDER_ERROR_RATE


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else now_kst().date().isoformat()
    target_date = _parse_date(target)
    if target_date.weekday() >= 5:
        raise SystemExit(f"{target} is a weekend; daily reports run Mon-Fri only")
    market = market_for_date(target)

    excluded_symbols = recent_pick_symbols(DUPLICATE_BAN_DAYS, target_date)

    pit_collector = PitFundamentalsCollector(market=market)
    candidates, stats = screen_market(market, excluded_symbols, pit_collector=pit_collector)
    if _provider_error_rate_exceeds(stats):
        failed = stats.errors + stats.no_data
        logger.error(
            "Refusing %s: provider failures %d/%d exceed %.0f%%",
            target,
            failed,
            stats.screened,
            MAX_PROVIDER_ERROR_RATE * 100,
        )
        return 1

    pick = select_pick(candidates)
    top_candidates = build_top_candidates(candidates)
    top_candidates = classify_top_candidate_risks(top_candidates)
    top_candidates = classify_top_candidate_moat_megatrend(top_candidates)
    logger.info(
        "Daily %s market=%s pick=%s screened=%d errors=%d",
        target,
        market,
        pick.symbol if pick else "none",
        stats.screened,
        stats.errors,
    )

    if pick:
        entry = build_pick(target, market, pick, stats, top_candidates)
    else:
        entry = build_no_pick(target, market, stats, top_candidates)

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DAILY_DIR / f"{target}.json"
    out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sync_manifest()

    if target == now_kst().date().isoformat():
        pit_result = write_daily_pit_snapshots(target, market, pit_collector)
    else:
        # A backfill fetches today's info; filing it under a past date is look-ahead.
        pit_result = PitWriteResult(skipped=True, reason="backfill_not_pit")
    if pit_result.skipped:
        logger.warning("PIT snapshot skipped: %s", pit_result.reason)
    elif pit_result.manifest_entry:
        logger.info(
            "PIT staging written for %s %s (manifest after pit-repo push)",
            market,
            target,
        )

    print(f"Wrote {out_path} status={entry['status']} market={market}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
