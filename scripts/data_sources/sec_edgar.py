"""SEC EDGAR companyfacts as point-in-time rows (issue #225).

Live selection and Score v2 do not import this module. ``filed`` is ``known_at``.
A 10-K/A is a later row, not an overwrite. The frames API is not called.
Annual ``fp == FY`` only. Q4 shares the FY end date, so a quarter needs its own
period key before it can sit in ``visible``.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import CACHE_DIR
from data_sources.opendart import FundamentalsPIT

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
ANNUAL_FORMS = frozenset({"10-K", "10-K/A"})
MIN_FY_DAYS = 300
# Earlier concept wins when one filing reports two names for the same field.
CONCEPTS = (
    ("Revenues", "매출"),
    ("RevenueFromContractWithCustomerExcludingAssessedTax", "매출"),
    ("SalesRevenueNet", "매출"),
    ("OperatingIncomeLoss", "영업이익"),
    ("NetIncomeLoss", "순이익"),
    ("StockholdersEquity", "자본총계"),
    ("Liabilities", "부채총계"),
    ("NetCashProvidedByUsedInOperatingActivities", "영업현금흐름"),
)
_FLOW = frozenset({"매출", "영업이익", "순이익", "영업현금흐름"})
_CONCEPT_RANK = {name: index for index, (name, _field) in enumerate(CONCEPTS)}


class SecEdgarError(RuntimeError):
    pass


def parse_ticker_map(payload: dict) -> dict[str, str]:
    """Ticker -> 10-digit CIK. Non-integers are skipped."""
    out: dict[str, str] = {}
    for item in payload.values():
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "").strip().upper()
        cik = item.get("cik_str")
        if ticker and isinstance(cik, int) and not isinstance(cik, bool):
            out[ticker] = f"{cik:010d}"
    return out


def rows_from_companyfacts(symbol: str, payload: dict) -> list[FundamentalsPIT]:
    """Annual USD facts. Missing ``filed`` and non-annual forms are dropped."""
    gaap = (payload.get("facts") or {}).get("us-gaap") or {}
    best: dict[tuple[str, str, str], tuple[tuple[int, int], FundamentalsPIT]] = {}
    for concept, field in CONCEPTS:
        node = gaap.get(concept) or {}
        series = (node.get("units") or {}).get("USD") or []
        for fact in series:
            row = _annual_row(symbol, field, fact)
            if row is None:
                continue
            rank = (_CONCEPT_RANK[concept], 1 if fact.get("frame") else 0)
            key = (row.field, row.period, row.source)
            current = best.get(key)
            if current is None or rank < current[0]:
                best[key] = (rank, row)
    return [item[1] for item in best.values()]


def fetch_fundamentals(symbols: Sequence[str]) -> list[FundamentalsPIT]:
    tickers = load_tickers()
    rows: list[FundamentalsPIT] = []
    for symbol in symbols:
        ticker = _ticker(symbol)
        cik = tickers.get(ticker)
        if cik is None:
            raise SecEdgarError(f"no CIK for {symbol}")
        rows.extend(rows_from_companyfacts(symbol, fetch_companyfacts(cik)))
    return rows


def load_tickers() -> dict[str, str]:
    cached = _read_cache("company_tickers")
    if _is_ticker_cache(cached):
        return cached
    payload = json.loads(_get(TICKERS_URL))
    if not isinstance(payload, dict):
        raise SecEdgarError("company_tickers was not an object")
    mapped = parse_ticker_map(payload)
    _write_cache("company_tickers", mapped)
    return mapped


def fetch_companyfacts(cik: str) -> dict:
    cached = _read_cache(f"companyfacts_{cik}")
    if isinstance(cached, dict):
        return cached
    payload = json.loads(_get(FACTS_URL.format(cik=cik)))
    if not isinstance(payload, dict):
        raise SecEdgarError(f"companyfacts {cik} was not an object")
    _write_cache(f"companyfacts_{cik}", payload)
    return payload


def _annual_row(symbol: str, field: str, fact: dict) -> FundamentalsPIT | None:
    form = str(fact.get("form") or "")
    if form not in ANNUAL_FORMS or fact.get("fp") != "FY":
        return None
    filed = str(fact.get("filed") or "")
    end = str(fact.get("end") or "")
    accn = str(fact.get("accn") or "").strip()
    value = fact.get("val")
    if not accn or not _iso(filed) or not _iso(end):
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    start = fact.get("start")
    if field in _FLOW:
        span = _span_days(str(start or ""), end)
        if span is None or span < MIN_FY_DAYS:
            return None
    elif start:
        return None
    return FundamentalsPIT(
        symbol=symbol,
        field=field,
        period=end,
        value=float(value),
        known_at=filed,
        source=f"sec:{accn}",
    )


def _ticker(symbol: str) -> str:
    text = symbol.strip().upper()
    if text.endswith(".US"):
        return text[:-3]
    return text


def _iso(text: str) -> bool:
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _span_days(start: str, end: str) -> int | None:
    if not _iso(start) or not _iso(end):
        return None
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def _is_ticker_cache(cached: dict | None) -> bool:
    if not isinstance(cached, dict) or not cached:
        return False
    return all(isinstance(value, str) for value in cached.values())


def _user_agent() -> str:
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if agent:
        return agent
    return "Ten Bagger tenbagger.finnaut.com (jee1@users.noreply.github.com)"


def _cache_path(name: str) -> Path:
    return CACHE_DIR / f"sec_{name}.json"


def _read_cache(name: str) -> dict | None:
    path = _cache_path(name)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_cache(name: str, payload: dict) -> None:
    path = _cache_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": _user_agent(), "Accept": "application/json"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except HTTPError as exc:
        raise SecEdgarError(f"sec HTTP {exc.code}") from None
    except (URLError, TimeoutError) as exc:
        raise SecEdgarError(f"sec {type(exc).__name__}") from None
