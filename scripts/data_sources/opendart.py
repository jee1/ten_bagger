"""OpenDART periodic-report fundamentals as point-in-time rows (issue #220).

Live selection and Score v2 do not import this module. Rows are visible at
``as_of`` only when ``known_at`` is on or before that date. A later correction
is a second row with a later ``known_at``.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from config import CACHE_DIR

API = "https://opendart.fss.or.kr/api/"
# reprt_code -> month-day of the statement period end
PERIOD_END = {
    "11013": "-03-31",
    "11012": "-06-30",
    "11014": "-09-30",
    "11011": "-12-31",
}
# 주요계정 account_nm -> issue field. Cash-flow names vary. Unlisted accounts are dropped.
# 주요계정 has no cash-flow line. 영업현금흐름 stays absent on this endpoint.
_EXACT_FIELD = {
    "자본총계": "자본총계",
    "부채총계": "부채총계",
    "영업활동현금흐름": "영업현금흐름",
    "영업활동으로인한현금흐름": "영업현금흐름",
}
_FS_RANK = {"CFS": 0, "OFS": 1}


class OpenDartError(RuntimeError):
    pass


@dataclass(frozen=True)
class FundamentalsPIT:
    symbol: str
    field: str
    period: str
    value: float
    known_at: str
    source: str


def visible(
    rows: Sequence[FundamentalsPIT],
    *,
    symbol: str,
    field: str,
    period: str,
    as_of: str,
) -> FundamentalsPIT | None:
    """Latest row whose filing date is known on ``as_of``. Same-day filings count."""
    matched = [
        row
        for row in rows
        if row.symbol == symbol
        and row.field == field
        and row.period == period
        and row.known_at <= as_of
    ]
    if not matched:
        return None
    return max(matched, key=lambda row: (row.known_at, row.source))


def parse_amount(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = raw.strip().replace(",", "")
    if not text or text == "-":
        return None
    return float(text)


def period_end(bsns_year: str, reprt_code: str) -> str | None:
    suffix = PERIOD_END.get(reprt_code)
    if suffix is None or not bsns_year.isdigit():
        return None
    return f"{bsns_year}{suffix}"


def field_for(account_nm: str) -> str | None:
    name = account_nm.replace(" ", "")
    if name.startswith("매출액"):
        return "매출"
    if name.startswith("영업이익"):
        return "영업이익"
    if name.startswith("당기순이익"):
        return "순이익"
    return _EXACT_FIELD.get(name)


def rows_from_accounts(
    symbol: str,
    accounts: Iterable[dict],
    filings: dict[str, str],
) -> list[FundamentalsPIT]:
    """Join 주요계정 rows to list.json ``rcept_dt``. Skip a row with no filing date."""
    best: dict[tuple[str, str, str], tuple[int, FundamentalsPIT]] = {}
    for account in accounts:
        field = field_for(account.get("account_nm") or "")
        rcept_no = (account.get("rcept_no") or "").strip()
        known_at = filings.get(rcept_no)
        end = period_end(str(account.get("bsns_year") or ""), str(account.get("reprt_code") or ""))
        value = parse_amount(account.get("thstrm_amount"))
        if field is None or known_at is None or end is None or value is None or not rcept_no:
            continue
        rank = _FS_RANK.get(account.get("fs_div") or "", 2)
        row = FundamentalsPIT(
            symbol=symbol,
            field=field,
            period=end,
            value=value,
            known_at=_iso_date(known_at),
            source=f"opendart:{rcept_no}",
        )
        key = (field, end, rcept_no)
        current = best.get(key)
        if current is None or rank < current[0]:
            best[key] = (rank, row)
    return [item[1] for item in best.values()]


def parse_corp_codes(xml_bytes: bytes) -> dict[str, str]:
    """stock_code (6 digits) -> corp_code. Blank stock codes are not listed."""
    out: dict[str, str] = {}
    for _event, elem in ElementTree.iterparse(io.BytesIO(xml_bytes), events=("end",)):
        if elem.tag != "list":
            continue
        stock = (elem.findtext("stock_code") or "").strip()
        corp = (elem.findtext("corp_code") or "").strip()
        if stock and corp:
            out[stock] = corp
        elem.clear()
    return out


def _iso_date(yyyymmdd: str) -> str:
    text = yyyymmdd.strip()
    if len(text) != 8 or not text.isdigit():
        raise OpenDartError(f"bad rcept_dt {yyyymmdd!r}")
    return f"{text[:4]}-{text[4:6]}-{text[6:]}"


def _redact(text: str) -> str:
    key = os.environ.get("OPENDART_API_KEY", "")
    if key:
        text = text.replace(key, "OPENDART_API_KEY")
    return text


def _api_key() -> str:
    key = os.environ.get("OPENDART_API_KEY", "").strip().strip('"').strip("'")
    if key:
        return key
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("OPENDART_API_KEY="):
                key = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    os.environ["OPENDART_API_KEY"] = key
                    return key
    raise OpenDartError("OPENDART_API_KEY is unset")


def _cache_path(name: str) -> Path:
    return CACHE_DIR / f"opendart_{name}.json"


def _read_cache(name: str) -> dict | list | None:
    path = _cache_path(name)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_cache(name: str, payload: dict | list) -> None:
    path = _cache_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _get(path: str, params: dict) -> bytes:
    query = dict(params)
    query["crtfc_key"] = _api_key()
    url = API + path + "?" + urlencode(query)
    request = Request(url, headers={"User-Agent": "ten-bagger"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise OpenDartError(_redact(str(exc))) from None


def _get_json(path: str, params: dict, *, empty_ok: bool = False) -> dict:
    data = json.loads(_get(path, params))
    status = str(data.get("status") or "")
    if status == "013" and empty_ok:
        return {"list": [], "total_page": 1, "status": "013"}
    if status and status != "000":
        raise OpenDartError(f"opendart {path} status {status} {data.get('message')}")
    return data


def load_corp_codes() -> dict[str, str]:
    cached = _read_cache("corp_codes")
    if isinstance(cached, dict) and cached:
        return {str(k): str(v) for k, v in cached.items()}
    blob = _get("corpCode.xml", {})
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        xml_name = archive.namelist()[0]
        codes = parse_corp_codes(archive.read(xml_name))
    _write_cache("corp_codes", codes)
    return codes


def _stock_code(symbol: str) -> str:
    code = symbol.upper().split(".", 1)[0]
    if len(code) != 6 or not code.isdigit():
        raise OpenDartError(f"not a KR ticker: {symbol}")
    return code


def fetch_filings(corp_code: str, bgn_de: str, end_de: str) -> dict[str, str]:
    """rcept_no -> rcept_dt for periodic reports in the window."""
    cache_name = f"list_{corp_code}_{bgn_de}_{end_de}"
    cached = _read_cache(cache_name)
    if isinstance(cached, dict):
        return {str(k): str(v) for k, v in cached.items()}
    filings: dict[str, str] = {}
    page = 1
    while True:
        data = _get_json(
            "list.json",
            {
                "corp_code": corp_code,
                "bgn_de": bgn_de,
                "end_de": end_de,
                "pblntf_ty": "A",
                "page_no": str(page),
                "page_count": "100",
            },
            empty_ok=True,
        )
        for item in data.get("list") or []:
            rcept_no = (item.get("rcept_no") or "").strip()
            rcept_dt = (item.get("rcept_dt") or "").strip()
            if rcept_no and rcept_dt:
                filings[rcept_no] = rcept_dt
        total = int(data.get("total_page") or 1)
        if page >= total:
            break
        page += 1
    _write_cache(cache_name, filings)
    return filings


def fetch_accounts(corp_codes: Sequence[str], bsns_year: str, reprt_code: str) -> list[dict]:
    cache_name = f"acnt_{bsns_year}_{reprt_code}_{'_'.join(corp_codes)}"
    cached = _read_cache(cache_name)
    if isinstance(cached, list):
        return cached
    data = _get_json(
        "fnlttMultiAcnt.json",
        {
            "corp_code": ",".join(corp_codes),
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
        },
        empty_ok=True,
    )
    rows = list(data.get("list") or [])
    _write_cache(cache_name, rows)
    return rows


def fetch_fundamentals(
    symbols: Sequence[str],
    *,
    bsns_year: str,
    reprt_code: str,
    bgn_de: str,
    end_de: str,
) -> list[FundamentalsPIT]:
    codes = load_corp_codes()
    by_corp: dict[str, str] = {}
    for symbol in symbols:
        corp = codes.get(_stock_code(symbol))
        if corp is None:
            raise OpenDartError(f"no corp_code for {symbol}")
        by_corp[corp] = symbol
    filings = {corp: fetch_filings(corp, bgn_de, end_de) for corp in by_corp}
    accounts = fetch_accounts(list(by_corp), bsns_year, reprt_code)
    grouped: dict[str, list[dict]] = {corp: [] for corp in by_corp}
    for account in accounts:
        corp = (account.get("corp_code") or "").strip()
        if corp in grouped:
            grouped[corp].append(account)
    rows: list[FundamentalsPIT] = []
    for corp, symbol in by_corp.items():
        rows.extend(rows_from_accounts(symbol, grouped[corp], filings[corp]))
    return rows
