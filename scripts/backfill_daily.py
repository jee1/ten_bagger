#!/usr/bin/env python3
"""Backfill missing meta/reasoning fields in existing daily JSON files."""

from __future__ import annotations

import json
import re
import sys

from config import COMPOSITE_THRESHOLD, DAILY_DIR, MAX_GROWTH_PCT
from profile import build_stock_profile
from sync_manifest import sync_manifest
from yf_cache import get_ticker_info

_EARNINGS_KO = re.compile(r"이익 성장 \d+(?:\.\d+)?%")
_EARNINGS_EN = re.compile(r"earnings growth \d+(?:\.\d+)?%", re.IGNORECASE)


def _fix_clipped_growth_reasoning(entry: dict) -> None:
    scores = entry.get("scores") or {}
    if scores.get("growth") != MAX_GROWTH_PCT:
        return
    reasoning = entry.get("reasoning") or {}
    growth = reasoning.get("growth") or {}
    if "ko" in growth:
        growth["ko"] = _EARNINGS_KO.sub(f"이익 성장 {MAX_GROWTH_PCT}%", growth["ko"], count=1)
    if "en" in growth:
        growth["en"] = _EARNINGS_EN.sub(
            f"earnings growth {MAX_GROWTH_PCT:g}%",
            growth["en"],
            count=1,
        )


def backfill_entry(entry: dict) -> dict:
    meta = entry.setdefault("meta", {})
    meta.setdefault("skippedMarketCap", 0)
    meta.setdefault("noData", 0)
    meta.setdefault("errors", 0)

    if entry.get("status") == "pick" and "reasoning" in entry:
        reasoning = entry["reasoning"]
        scores = entry.get("scores", {})
        _fix_clipped_growth_reasoning(entry)
        if "quality" not in reasoning and scores:
            roe = reasoning.get("growth", {}).get("ko", "")
            reasoning["quality"] = {
                "ko": f"품질 점수 {scores.get('quality', 0)}입니다.",
                "en": f"Quality score is {scores.get('quality', 0)}.",
            }

        stock = entry.get("stock") or {}
        if stock.get("symbol") and not stock.get("profile"):
            info = get_ticker_info(stock["symbol"])
            name = stock.get("name") or {}
            profile = build_stock_profile(
                info,
                name_ko=name.get("ko", stock["symbol"]),
                name_en=name.get("en", stock["symbol"]),
            )
            if profile:
                stock["profile"] = profile
                entry["stock"] = stock

    if entry.get("status") == "no_pick":
        scores = entry.setdefault("scores", {})
        scores.setdefault("threshold", COMPOSITE_THRESHOLD)

    return entry


def main() -> int:
    if not DAILY_DIR.exists():
        print("No daily directory")
        return 0

    updated = 0
    for path in sorted(DAILY_DIR.glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        before = path.read_text(encoding="utf-8")
        entry = backfill_entry(entry)
        after = json.dumps(entry, ensure_ascii=False, indent=2) + "\n"
        if after != before:
            path.write_text(after, encoding="utf-8")
            updated += 1
            print(f"Updated {path.name}")

    sync_manifest()
    print(f"Backfilled {updated} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
