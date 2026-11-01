"""finnaut-ohlc snapshot reader: first price source for the ledger (#174).

Layout and contract: jee1/finnaut-ohlc docs/schema.md, docs/consumers.md.
Returns None (caller falls back to yfinance/stooq) instead of partial data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

OHLC_DIR_ENV = "FINNAUT_OHLC_DIR"
PROVIDER = "finnaut-ohlc"

_MARKET_DIRS = {"KR": "krx", "US": "us"}

# #174 scope update: ohlc US runs after ten_bagger, so bars ending one weekday before
# asOfDate are accepted; the missing session leaves horizons immature until the next run.
MAX_LAG_WEEKDAYS = 1


class OhlcMiss(Exception):
    """The snapshot cannot serve this symbol; the message is the reason."""


def ohlc_root() -> Path | None:
    raw = os.environ.get(OHLC_DIR_ENV)
    return Path(raw) if raw else None


def snapshot_dir(root: Path, market: str, as_of_date: str) -> Path:
    """Latest session folder on or before asOfDate (folders are session dates)."""
    market_dir = root / "bars" / _MARKET_DIRS.get(market.upper(), "us")
    if not market_dir.is_dir():
        raise OhlcMiss(f"no {market_dir}")
    dates = sorted(
        d.name
        for d in market_dir.iterdir()
        if d.is_dir() and d.name[:1].isdigit() and d.name <= as_of_date
    )
    if not dates:
        raise OhlcMiss(f"no snapshot <= {as_of_date}")
    return market_dir / dates[-1]


def load_ohlc_bars(
    symbol: str,
    market: str,
    as_of_date: str,
    *,
    since: str | None = None,
    root: Path,
) -> pd.DataFrame:
    """Bars from the snapshot, covering `since` when given. Raises OhlcMiss otherwise.

    attrs["lastSession"] is the symbol's own last bar: the folder is named after the newest
    bar across symbols, so a stock can end a session earlier than its folder.
    """
    folder = snapshot_dir(root, market, as_of_date)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if symbol in manifest.get("failedSymbols", []):
        raise OhlcMiss(f"{symbol} failed in {folder.name}")
    path = folder / f"{symbol.lstrip('^')}.json"
    if not path.exists():
        raise OhlcMiss(f"{symbol} not in {folder.name}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("bars") or []
    if not rows:
        raise OhlcMiss(f"{symbol} has no bars in {folder.name}")
    if since is not None and rows[0]["d"] > since:
        raise OhlcMiss(f"{symbol} bars start {rows[0]['d']} after {since}")
    last = rows[-1]["d"]
    if np.busday_count(last, as_of_date) > MAX_LAG_WEEKDAYS:
        raise OhlcMiss(f"{symbol} bars end {last}, stale for {as_of_date}")
    bars = pd.DataFrame(rows).rename(
        columns={"d": "date", "o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"}
    )
    bars.attrs["priceBasis"] = raw.get("priceBasis") or manifest.get("priceBasis", "unknown")
    bars.attrs["ohlcAsOf"] = manifest["asOf"]
    bars.attrs["lastSession"] = last
    return bars
