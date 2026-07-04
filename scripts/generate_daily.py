#!/usr/bin/env python3
"""Generate daily JSON report and update manifest."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from config import COMPOSITE_THRESHOLD, DAILY_DIR, DUPLICATE_BAN_DAYS, MANIFEST_PATH, market_for_date
from screen import build_reasoning, screen_market

KST = ZoneInfo("Asia/Seoul")


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def recent_pick_symbols(days: int, before: date) -> set[str]:
    symbols: set[str] = set()
    if not DAILY_DIR.exists():
        return symbols

    for path in sorted(DAILY_DIR.glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entry_date = _parse_date(entry["date"])
        if entry_date >= before:
            continue
        if before - entry_date > timedelta(days=days):
            continue
        if entry.get("status") == "pick" and entry.get("stock"):
            symbols.add(entry["stock"]["symbol"])
    return symbols


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"dates": [], "lastUpdated": ""}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_no_pick(target: str, market: str, screened: int, excluded: int) -> dict:
    now = datetime.now(KST).isoformat(timespec="seconds")
    return {
        "date": target,
        "market": market,
        "status": "no_pick",
        "scores": {
            "composite": 0,
            "growth": 0,
            "valuation": 0,
            "momentum": 0,
            "quality": 0,
            "threshold": COMPOSITE_THRESHOLD,
        },
        "meta": {
            "generatedAt": now,
            "candidatesScreened": screened,
            "excludedRecent": excluded,
        },
    }


def build_pick(target: str, market: str, result, screened: int, excluded: int) -> dict:
    now = datetime.now(KST).isoformat(timespec="seconds")
    return {
        "date": target,
        "market": market,
        "status": "pick",
        "stock": {
            "symbol": result.symbol,
            "name": {"ko": result.meta.name_ko, "en": result.meta.name_en},
            "exchange": result.meta.exchange,
            "currency": result.meta.currency,
        },
        "scores": {
            "composite": result.composite,
            "growth": result.growth,
            "valuation": result.valuation,
            "momentum": result.momentum,
            "quality": result.quality,
            "threshold": COMPOSITE_THRESHOLD,
        },
        "reasoning": build_reasoning(result),
        "meta": {
            "generatedAt": now,
            "candidatesScreened": screened,
            "excludedRecent": excluded,
        },
    }


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else datetime.now(KST).date().isoformat()
    market = market_for_date(target)
    before = _parse_date(target)

    excluded_symbols = recent_pick_symbols(DUPLICATE_BAN_DAYS, before)
    excluded_count = len(excluded_symbols)

    candidates, screened = screen_market(market, excluded_symbols)

    if candidates:
        entry = build_pick(target, market, candidates[0], screened, excluded_count)
    else:
        entry = build_no_pick(target, market, screened, excluded_count)

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DAILY_DIR / f"{target}.json"
    out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = load_manifest()
    dates = set(manifest.get("dates", []))
    dates.add(target)
    manifest["dates"] = sorted(dates, reverse=True)
    manifest["lastUpdated"] = datetime.now(timezone.utc).astimezone(KST).isoformat(timespec="seconds")
    save_manifest(manifest)

    print(f"Wrote {out_path} status={entry['status']} market={market}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
