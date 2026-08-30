#!/usr/bin/env python3
"""Regenerate pick forward-return ledger / performance bundles (#63)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    DAILY_DIR,
    LEDGER_DIR,
    LEDGER_SCHEMA_PATH,
    PERFORMANCE_BUNDLE_SCHEMA_PATH,
    PERFORMANCE_DIR,
)
from performance.load_dailies import load_eligible_dailies
from performance.pit_prices import prefer_adjusted
from performance.prices_live import default_benchmark_provider, default_price_provider
from performance.returns import measure_all_horizons
from performance.write_atomic import atomic_replace
from validate_content import load_validator

SCHEMA_VERSION = "0.1.0"
MARKETS = ("KR", "US")


def _validate_as_of_date(value: str | None) -> str | None:
    if not value:
        return None
    parts = value.split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    y, m, d = (int(p) for p in parts)
    try:
        datetime(y, m, d)
    except ValueError:
        return None
    return value


PriceProvider = Callable[[str, str], pd.DataFrame]
BenchmarkProvider = Callable[[str], pd.DataFrame | None]


def _ledger_entry(daily: dict) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "pickDate": daily["date"],
        "symbol": "",
        "status": daily["status"],
    }
    if daily["status"] == "pick":
        entry["symbol"] = daily["stock"]["symbol"]
    scores = daily.get("scores") or {}
    if "version" in scores:
        entry["scoreVersion"] = str(scores["version"])
    elif "composite" in scores:
        entry["scoreVersion"] = "2"
    return entry


def build_market_snapshots(
    *,
    dailies: list[dict],
    market: str,
    as_of_date: str,
    price_provider: PriceProvider,
    benchmark_provider: BenchmarkProvider,
    provider_label: str,
    price_adjustment: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build ledger + performance dicts for one market."""
    market_dailies = [d for d in dailies if d.get("market") == market]
    entries = [_ledger_entry(d) for d in market_dailies]
    measurements: list[dict[str, Any]] = []
    bench_cache: dict[str, pd.DataFrame | None] = {}
    adj_labels: set[str] = set()

    for daily in market_dailies:
        if daily["status"] != "pick":
            continue
        symbol = daily["stock"]["symbol"]
        bars = price_provider(symbol, market)
        _, label = prefer_adjusted(bars)
        adj_labels.add(label)
        bench_id = "KR-KOSPI" if market == "KR" else "US-SPX"
        if bench_id not in bench_cache:
            bench_cache[bench_id] = benchmark_provider(bench_id)
        measurements.extend(
            measure_all_horizons(
                bars=bars,
                benchmark_bars=bench_cache[bench_id],
                pick_date=daily["date"],
                as_of_date=as_of_date,
                market=market,
                symbol=symbol,
            )
        )

    if price_adjustment is None:
        if not adj_labels:
            price_adjustment = "adjusted_preferred"
        elif adj_labels == {"adjusted_preferred"}:
            price_adjustment = "adjusted_preferred"
        elif adj_labels == {"unadjusted_fallback"}:
            price_adjustment = "unadjusted_fallback"
        else:
            price_adjustment = "mixed"

    ledger = {
        "schemaVersion": SCHEMA_VERSION,
        "market": market,
        "asOfDate": as_of_date,
        "entries": entries,
    }
    performance = {
        "schemaVersion": SCHEMA_VERSION,
        "market": market,
        "asOfDate": as_of_date,
        "runMeta": {
            "provider": provider_label,
            "priceAdjustment": price_adjustment,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "asOfDate": as_of_date,
        },
        "measurements": measurements,
    }
    return ledger, performance


def regenerate(
    *,
    as_of_date: str,
    markets: tuple[str, ...] = MARKETS,
    daily_dir: Path | None = None,
    ledger_dir: Path | None = None,
    performance_dir: Path | None = None,
    price_provider: PriceProvider | None = None,
    benchmark_provider: BenchmarkProvider | None = None,
    provider_label: str = "yfinance",
    price_adjustment: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Compute and atomically write ledger/performance snapshots."""
    daily_dir = daily_dir or DAILY_DIR
    ledger_dir = ledger_dir or LEDGER_DIR
    performance_dir = performance_dir or PERFORMANCE_DIR
    if price_provider is None:
        price_provider = default_price_provider(as_of_date)
    if benchmark_provider is None:
        benchmark_provider = default_benchmark_provider(as_of_date)

    dailies = load_eligible_dailies(daily_dir, as_of_date)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    performance_dir.mkdir(parents=True, exist_ok=True)

    writes: dict[Path, dict[str, Any]] = {}
    validators = []
    ledger_v = load_validator(LEDGER_SCHEMA_PATH)
    perf_v = load_validator(PERFORMANCE_BUNDLE_SCHEMA_PATH)

    summary: dict[str, Any] = {"markets": {}, "asOfDate": as_of_date}

    for market in markets:
        ledger, performance = build_market_snapshots(
            dailies=dailies,
            market=market,
            as_of_date=as_of_date,
            price_provider=price_provider,
            benchmark_provider=benchmark_provider,
            provider_label=provider_label,
            price_adjustment=price_adjustment,
        )
        ledger_path = ledger_dir / f"{market}.json"
        perf_path = performance_dir / f"{market}.json"
        writes[ledger_path] = ledger
        writes[perf_path] = performance
        validators.extend([ledger_v, perf_v])
        summary["markets"][market] = {
            "entries": len(ledger["entries"]),
            "measurements": len(performance["measurements"]),
        }

    atomic_replace(writes, validators, dry_run=dry_run)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="regenerate_ledger.py")
    parser.add_argument("--as-of-date", required=False, default=None)
    parser.add_argument("--market", choices=("KR", "US"), default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    as_of = _validate_as_of_date(args.as_of_date)
    if not as_of:
        print("error: --as-of-date YYYY-MM-DD is required", file=sys.stderr)
        return 2

    markets: tuple[str, ...] = (args.market,) if args.market else MARKETS

    try:
        summary = regenerate(as_of_date=as_of, markets=markets, dry_run=args.dry_run)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: regenerate failed: {exc}", file=sys.stderr)
        return 1

    parts = []
    for market, info in summary["markets"].items():
        parts.append(
            f"{market}: {info['entries']} entries, {info['measurements']} measurements"
        )
    print(
        f"regenerate ok asOfDate={as_of} "
        + "; ".join(parts)
        + (" (dry-run)" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
