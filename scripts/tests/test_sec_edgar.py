"""SEC companyfacts point-in-time rows. No network."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_sources.opendart import visible
from data_sources.sec_edgar import parse_ticker_map, rows_from_companyfacts

PERIOD = "2024-12-31"


def _fact(**overrides):
    base = {
        "start": "2024-01-01",
        "end": PERIOD,
        "val": 100,
        "accn": "0001-24-000010",
        "fp": "FY",
        "form": "10-K",
        "filed": "2025-02-15",
    }
    base.update(overrides)
    return base


def _payload(*facts, concept="Revenues"):
    return {"facts": {"us-gaap": {concept: {"units": {"USD": list(facts)}}}}}


def test_future_filing_is_hidden_and_amendment_waits_for_its_date():
    rows = rows_from_companyfacts(
        "AAPL",
        _payload(
            _fact(val=100, accn="0001", filed="2025-02-15"),
            _fact(val=120, accn="0001-A", form="10-K/A", filed="2025-06-01"),
            _fact(val=999, accn="0001-F", filed="2026-02-01"),
        ),
    )
    before = visible(rows, symbol="AAPL", field="매출", period=PERIOD, as_of="2025-04-01")
    amended = visible(rows, symbol="AAPL", field="매출", period=PERIOD, as_of="2025-06-01")
    assert before is not None and before.value == 100
    assert amended is not None and amended.value == 120
    assert amended.source == "sec:0001-A"


def test_quarter_ytd_and_missing_filed_are_dropped():
    rows = rows_from_companyfacts(
        "AAPL",
        _payload(
            _fact(),
            _fact(start="2024-10-01", val=40, accn="q4", fp="FY"),
            _fact(form="10-Q", val=30, accn="q"),
            _fact(filed="", accn="nofile"),
        ),
    )
    assert len(rows) == 1
    assert rows[0].value == 100
    assert rows[0].known_at == "2025-02-15"


def test_balance_sheet_keeps_instant_facts_and_revenue_name_rank():
    payload = {
        "facts": {
            "us-gaap": {
                "SalesRevenueNet": {"units": {"USD": [_fact(val=50, accn="same")]}},
                "Revenues": {"units": {"USD": [_fact(val=80, accn="same")]}},
                "StockholdersEquity": {
                    "units": {
                        "USD": [
                            {
                                "end": PERIOD,
                                "val": 10,
                                "accn": "eq",
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-02-15",
                            }
                        ]
                    }
                },
            }
        }
    }
    rows = rows_from_companyfacts("AAPL.US", payload)
    by_field = {row.field: row.value for row in rows}
    assert by_field == {"매출": 80.0, "자본총계": 10.0}


def test_unframed_fact_wins_over_frame_on_the_same_accession():
    rows = rows_from_companyfacts(
        "AAPL",
        _payload(
            _fact(val=100, frame="CY2024"),
            _fact(val=90),
        ),
    )
    assert len(rows) == 1
    assert rows[0].value == 90


def test_ticker_map_pads_cik():
    mapped = parse_ticker_map({"0": {"cik_str": 320193, "ticker": "aapl", "title": "Apple"}})
    assert mapped == {"AAPL": "0000320193"}
