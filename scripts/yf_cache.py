"""Disk cache for yfinance info/history to reduce API calls."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from config import (
    CACHE_DIR,
    CACHE_TTL_SECONDS,
    YF_MAX_RETRIES,
    YF_MIN_REQUEST_INTERVAL,
    YF_RATE_LIMIT_DELAY,
    YF_RETRY_BASE_DELAY,
)

logger = logging.getLogger(__name__)

_SAFE_SYMBOL = re.compile(r"[^A-Za-z0-9._-]+")
_api_lock = threading.Lock()
_last_api_at = 0.0


def _safe_name(symbol: str) -> str:
    return _SAFE_SYMBOL.sub("_", symbol)


def _cache_path(symbol: str, kind: str) -> Path:
    return CACHE_DIR / f"{_safe_name(symbol)}_{kind}.json"


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < CACHE_TTL_SECONDS


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.debug("Corrupt yfinance cache ignored: %s", path)
        return None


def _read_info_cache(path: Path) -> dict[str, Any] | None:
    payload = _read_json(path)
    return payload if payload else None


def _read_history_cache(path: Path) -> pd.DataFrame | None:
    payload = _read_json(path)
    if not payload or not payload.get("close"):
        return None
    try:
        index = pd.to_datetime(payload["index"])
        return pd.DataFrame({"Close": payload["close"]}, index=index)
    except (KeyError, ValueError):
        logger.debug("Invalid yfinance history cache ignored: %s", path)
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _is_rate_limited(exc: Exception) -> bool:
    message = str(exc).lower()
    return "429" in message or "too many requests" in message or "rate limit" in message


def _is_transient_failure(exc: Exception) -> bool:
    if isinstance(exc, ConnectionError | TimeoutError):
        return True
    message = str(exc).lower()
    transient_markers = (
        "connection",
        "temporar",
        "timeout",
        "timed out",
        "remote end closed",
        "service unavailable",
    )
    return _is_rate_limited(exc) or any(marker in message for marker in transient_markers)


def _throttle_before_request() -> None:
    global _last_api_at
    with _api_lock:
        now = time.time()
        wait = YF_MIN_REQUEST_INTERVAL - (now - _last_api_at)
        if wait > 0:
            time.sleep(wait)
        _last_api_at = time.time()


def _with_retry[T](label: str, fn: Callable[[], T]) -> T:
    last_exc: Exception | None = None
    for attempt in range(YF_MAX_RETRIES):
        try:
            _throttle_before_request()
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt + 1 >= YF_MAX_RETRIES:
                break
            delay = YF_RETRY_BASE_DELAY * (2**attempt)
            if _is_rate_limited(exc):
                delay = max(delay, YF_RATE_LIMIT_DELAY)
            logger.warning(
                "%s failed (attempt %d/%d): %s; retry in %.1fs",
                label,
                attempt + 1,
                YF_MAX_RETRIES,
                exc,
                delay,
            )
            time.sleep(delay)
    assert last_exc is not None
    raise last_exc


def get_ticker_info(symbol: str) -> dict[str, Any]:
    path = _cache_path(symbol, "info")
    if _is_fresh(path):
        cached = _read_info_cache(path)
        if cached is not None:
            return cached

    def _fetch() -> dict[str, Any]:
        return yf.Ticker(symbol).info or {}

    try:
        info = _with_retry(f"yfinance info {symbol}", _fetch)
    except Exception as exc:
        stale = _read_info_cache(path)
        if stale is not None and _is_transient_failure(exc):
            logger.warning(
                "Using stale yfinance info cache for %s after fetch failure: %s",
                symbol,
                exc,
            )
            return stale
        raise
    if info:
        _write_json(path, info)
    return info


def get_ticker_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    kind = f"hist_{period.replace('/', '_')}"
    path = _cache_path(symbol, kind)
    if _is_fresh(path):
        cached = _read_history_cache(path)
        if cached is not None:
            return cached

    def _fetch() -> pd.DataFrame:
        return yf.Ticker(symbol).history(period=period)

    try:
        hist = _with_retry(f"yfinance history {symbol}", _fetch)
    except Exception as exc:
        stale = _read_history_cache(path)
        if stale is not None and _is_transient_failure(exc):
            logger.warning(
                "Using stale yfinance history cache for %s after fetch failure: %s",
                symbol,
                exc,
            )
            return stale
        raise
    if not hist.empty:
        _write_json(
            path,
            {
                "index": [d.isoformat() for d in hist.index.to_pydatetime()],
                "close": [float(v) for v in hist["Close"].tolist()],
            },
        )
    return hist
