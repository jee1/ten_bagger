"""Disk cache for yfinance info/history to reduce API calls."""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from config import CACHE_DIR, CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)

_SAFE_SYMBOL = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_name(symbol: str) -> str:
    return _SAFE_SYMBOL.sub("_", symbol)


def _cache_path(symbol: str, kind: str) -> Path:
    return CACHE_DIR / f"{_safe_name(symbol)}_{kind}.json"


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < CACHE_TTL_SECONDS


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def get_ticker_info(symbol: str) -> dict[str, Any]:
    path = _cache_path(symbol, "info")
    if _is_fresh(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.debug("Stale corrupt cache for %s info", symbol)

    info = yf.Ticker(symbol).info or {}
    if info:
        _write_json(path, info)
    return info


def get_ticker_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    kind = f"hist_{period.replace('/', '_')}"
    path = _cache_path(symbol, kind)
    if _is_fresh(path):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("close"):
                index = pd.to_datetime(payload["index"])
                return pd.DataFrame({"Close": payload["close"]}, index=index)
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.debug("Stale corrupt cache for %s history", symbol)

    hist = yf.Ticker(symbol).history(period=period)
    if not hist.empty:
        _write_json(
            path,
            {
                "index": [d.isoformat() for d in hist.index.to_pydatetime()],
                "close": [float(v) for v in hist["Close"].tolist()],
            },
        )
    return hist
