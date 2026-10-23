"""OpenDART point-in-time visibility. No network."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_sources.opendart import FundamentalsPIT, rows_from_accounts, visible

PERIOD = "2024-12-31"
OLD = FundamentalsPIT("005930.KS", "매출", PERIOD, 100.0, "2025-03-01", "opendart:old")
NEW = FundamentalsPIT("005930.KS", "매출", PERIOD, 120.0, "2025-05-15", "opendart:new")


def test_future_filing_is_hidden():
    hidden = visible([OLD], symbol="005930.KS", field="매출", period=PERIOD, as_of="2025-02-28")
    assert hidden is None
    seen = visible([OLD], symbol="005930.KS", field="매출", period=PERIOD, as_of="2025-03-01")
    assert seen is OLD


def test_correction_replaces_only_after_its_filing_date():
    rows = [OLD, NEW]
    before = visible(rows, symbol="005930.KS", field="매출", period=PERIOD, as_of="2025-04-01")
    after = visible(rows, symbol="005930.KS", field="매출", period=PERIOD, as_of="2025-05-15")
    assert before is OLD
    assert after is NEW
    assert after.value == 120.0


def test_rows_without_a_filing_date_are_dropped_and_cfs_wins():
    accounts = [
        {
            "account_nm": "매출액",
            "thstrm_amount": "1,000",
            "bsns_year": "2024",
            "reprt_code": "11011",
            "rcept_no": "20250311000111",
            "fs_div": "OFS",
        },
        {
            "account_nm": "매출액",
            "thstrm_amount": "2,000",
            "bsns_year": "2024",
            "reprt_code": "11011",
            "rcept_no": "20250311000111",
            "fs_div": "CFS",
        },
        {
            "account_nm": "매출액",
            "thstrm_amount": "9",
            "bsns_year": "2024",
            "reprt_code": "11011",
            "rcept_no": "missing",
            "fs_div": "CFS",
        },
    ]
    rows = rows_from_accounts("005930.KS", accounts, {"20250311000111": "20250311"})
    assert len(rows) == 1
    assert rows[0].value == 2000.0
    assert rows[0].known_at == "2025-03-11"
    assert rows[0].period == PERIOD
    assert rows[0].field == "매출"
    assert rows[0].source == "opendart:20250311000111"


def test_parenthetical_net_income_maps_to_field():
    accounts = [
        {
            "account_nm": "당기순이익(손실)",
            "thstrm_amount": "10",
            "bsns_year": "2024",
            "reprt_code": "11011",
            "rcept_no": "20250311000111",
            "fs_div": "CFS",
        }
    ]
    rows = rows_from_accounts("005930.KS", accounts, {"20250311000111": "20250311"})
    assert len(rows) == 1
    assert rows[0].field == "순이익"
    assert rows[0].value == 10.0
