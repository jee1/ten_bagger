#!/usr/bin/env python3
"""Build KR/US universe JSON from exchange listings (KOSPI, KOSDAQ, NASDAQ, NYSE)."""

from __future__ import annotations

import argparse
import json
from typing import Any

import FinanceDataReader as fdr
from config import UNIVERSE_DIR


def _invalid_us_symbol(symbol: str) -> bool:
    if not symbol or len(symbol) > 6:
        return True
    return any(ch in symbol for ch in ("^", "=", "/", " "))


def build_kr() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for market, suffix in (("KOSPI", "KS"), ("KOSDAQ", "KQ")):
        listing = fdr.StockListing(market)
        for record in listing.itertuples(index=False):
            code = str(record.Code).zfill(6)
            marcap = getattr(record, "Marcap", None)
            rows.append(
                {
                    "symbol": f"{code}.{suffix}",
                    "name_ko": str(record.Name),
                    "name_en": str(record.Name),
                    "exchange": market,
                    "currency": "KRW",
                    "market_cap": int(marcap) if marcap and str(marcap) != "nan" else None,
                }
            )
    rows.sort(key=lambda item: item["symbol"])
    return rows


def build_us() -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for market in ("NASDAQ", "NYSE"):
        listing = fdr.StockListing(market)
        for record in listing.itertuples(index=False):
            symbol = str(record.Symbol).strip().upper()
            if symbol in seen or _invalid_us_symbol(symbol):
                continue
            seen.add(symbol)
            rows.append(
                {
                    "symbol": symbol,
                    "name_ko": str(record.Name),
                    "name_en": str(record.Name),
                    "exchange": market,
                    "currency": "USD",
                }
            )
    rows.sort(key=lambda item: item["symbol"])
    return rows


def write_universe(market: str, rows: list[dict[str, Any]]) -> None:
    UNIVERSE_DIR.mkdir(parents=True, exist_ok=True)
    path = UNIVERSE_DIR / ("kr.json" if market == "KR" else "us.json")
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(rows)} symbols)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build exchange universe JSON files")
    parser.add_argument(
        "--market",
        choices=("KR", "US", "all"),
        default="all",
        help="Which market universe to rebuild (default: all)",
    )
    args = parser.parse_args()

    if args.market in ("KR", "all"):
        kr_rows = build_kr()
        write_universe("KR", kr_rows)

    if args.market in ("US", "all"):
        us_rows = build_us()
        write_universe("US", us_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
