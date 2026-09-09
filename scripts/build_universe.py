#!/usr/bin/env python3
"""Build KR/US universe JSON from exchange listings (KOSPI, KOSDAQ, NASDAQ, NYSE)."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from typing import Any
from urllib.error import HTTPError

import FinanceDataReader as fdr
import pandas as pd
from config import UNIVERSE_DIR

# FDR StockListing(KOSPI/KOSDAQ) reads GitHub cache keyed by KRX max_work_dt.
# Cache lag → HTTP 404; walk back to latest available CSV.
# ponytail: O(lookback) HEAD-less GETs; upgrade if FDR ships date fallback.
_FDR_KRX_CACHE = (
    "https://raw.githubusercontent.com/FinanceData/fdr_krx_data_cache"
    "/refs/heads/master/data/listing/krx"
)
_KR_MARKET_ID = {"KOSPI": "STK", "KOSDAQ": "KSQ"}


def _invalid_us_symbol(symbol: str) -> bool:
    if not symbol or len(symbol) > 6:
        return True
    return any(ch in symbol for ch in ("^", "=", "/", " "))


def _kr_listing_from_stale_cache(
    market: str,
    *,
    as_of: date | None = None,
    lookback_days: int = 14,
) -> pd.DataFrame:
    market_id = _KR_MARKET_ID[market]
    start = as_of or date.today()
    last_error: Exception | None = None
    for offset in range(lookback_days):
        day = start - timedelta(days=offset)
        url = f"{_FDR_KRX_CACHE}/{day.isoformat()}.csv"
        try:
            df = pd.read_csv(
                url,
                index_col=0,
                dtype={"Code": str, "Dept": str, "ChangeCode": str, "MarketId": str},
            )
        except HTTPError as exc:
            if getattr(exc, "code", None) == 404:
                last_error = exc
                continue
            raise
        df = df.reset_index(drop=True)
        df = df[df["MarketId"] == market_id].reset_index(drop=True)
        print(f"WARN: using stale FDR KRX cache {day.isoformat()} for {market} ({len(df)} rows)")
        return df
    raise RuntimeError(
        f"No FDR KRX cache CSV for {market} in last {lookback_days} days from {start}"
    ) from last_error


def _kr_stock_listing(market: str) -> pd.DataFrame:
    try:
        return fdr.StockListing(market)
    except HTTPError as exc:
        if getattr(exc, "code", None) != 404:
            raise
        print(f"WARN: StockListing({market}) HTTP 404; falling back to FDR cache walk-back")
        return _kr_listing_from_stale_cache(market)


def build_kr() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for market, suffix in (("KOSPI", "KS"), ("KOSDAQ", "KQ")):
        listing = _kr_stock_listing(market)
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
