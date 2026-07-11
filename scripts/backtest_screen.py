#!/usr/bin/env python3
"""Compare Score v1 vs v2 screening snapshots for a market."""

from __future__ import annotations

import argparse
import json
import statistics

from screen import screen_market


def _median_cap(results) -> float | None:
    caps = [r.metrics.get("market_cap") for r in results if r.metrics.get("market_cap")]
    if not caps:
        return None
    return statistics.median(caps)


def _avg_fcf_yield(results) -> float | None:
    yields = [
        r.metrics.get("fcf_yield_pct")
        for r in results
        if r.metrics.get("fcf_yield_pct") is not None
    ]
    if not yields:
        return None
    return round(statistics.mean(yields), 2)


def snapshot(market: str, version: int, limit: int) -> dict:
    results, stats = screen_market(market, set(), score_version=version)
    top = results[:limit]
    return {
        "version": version,
        "market": market,
        "screened": stats.screened,
        "passed_threshold": stats.passed_threshold,
        "skipped_red_flags": stats.skipped_red_flags,
        "median_market_cap_top": _median_cap(top),
        "avg_fcf_yield_top": _avg_fcf_yield(top),
        "top_symbols": [
            {
                "symbol": r.symbol,
                "composite": r.composite,
                "size": r.size,
                "growth": r.growth,
                "valuation": r.valuation,
                "entry": r.entry,
                "market_cap": r.metrics.get("market_cap"),
                "fcf_yield_pct": r.metrics.get("fcf_yield_pct"),
            }
            for r in top
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare screening score versions")
    parser.add_argument("market", nargs="?", default="US", choices=["KR", "US"])
    parser.add_argument("--limit", type=int, default=5, help="Top N passed symbols to summarize")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    v1 = snapshot(args.market, 1, args.limit)
    v2 = snapshot(args.market, 2, args.limit)
    report = {"v1": v1, "v2": v2}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"Market: {args.market}")
    for label, data in [("v1", v1), ("v2", v2)]:
        print(f"\n=== Score {label} ===")
        print(f"  screened: {data['screened']}")
        print(f"  passed (>={70}): {data['passed_threshold']}")
        if label == "v2":
            print(f"  skipped red flags: {data['skipped_red_flags']}")
        print(f"  median cap (top {args.limit}): {data['median_market_cap_top']}")
        print(f"  avg FCF yield (top {args.limit}): {data['avg_fcf_yield_top']}")
        if data["top_symbols"]:
            top = data["top_symbols"][0]
            print(f"  #1: {top['symbol']} composite={top['composite']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
