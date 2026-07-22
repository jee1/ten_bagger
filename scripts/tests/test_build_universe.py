"""Unit tests for exchange universe builders."""

from __future__ import annotations

from types import SimpleNamespace

import build_universe


class _Listing:
    def __init__(self, *records: SimpleNamespace) -> None:
        self._records = records

    def itertuples(self, index: bool = False):
        assert index is False
        return iter(self._records)


def test_invalid_us_symbol_rejects_empty_long_and_delisted_formats():
    assert build_universe._invalid_us_symbol("")
    assert build_universe._invalid_us_symbol("TOOLONG")
    assert build_universe._invalid_us_symbol("BRK/B")
    assert build_universe._invalid_us_symbol("ABC^")
    assert build_universe._invalid_us_symbol("ABC=")
    assert build_universe._invalid_us_symbol("ABC D")

    assert not build_universe._invalid_us_symbol("AAPL")
    assert not build_universe._invalid_us_symbol("BRK.B")
    assert not build_universe._invalid_us_symbol("ABCDEF")


def test_build_kr_formats_symbols_and_row_schema(monkeypatch):
    listings = {
        "KOSPI": _Listing(
            SimpleNamespace(Code=5930, Name="삼성전자", Marcap=420_000_000_000_000),
        ),
        "KOSDAQ": _Listing(
            SimpleNamespace(Code="357780", Name="솔브레인", Marcap="nan"),
        ),
    }

    monkeypatch.setattr(build_universe.fdr, "StockListing", lambda market: listings[market])

    assert build_universe.build_kr() == [
        {
            "symbol": "005930.KS",
            "name_ko": "삼성전자",
            "name_en": "삼성전자",
            "exchange": "KOSPI",
            "currency": "KRW",
            "market_cap": 420_000_000_000_000,
        },
        {
            "symbol": "357780.KQ",
            "name_ko": "솔브레인",
            "name_en": "솔브레인",
            "exchange": "KOSDAQ",
            "currency": "KRW",
            "market_cap": None,
        },
    ]


def test_build_us_formats_filters_dedupes_and_sorts(monkeypatch):
    listings = {
        "NASDAQ": _Listing(
            SimpleNamespace(Symbol=" aapl ", Name="Apple Inc."),
            SimpleNamespace(Symbol="BRK.B", Name="Berkshire Hathaway"),
            SimpleNamespace(Symbol="BAD/WS", Name="Invalid Slash"),
            SimpleNamespace(Symbol="TOOLONG", Name="Too Long"),
        ),
        "NYSE": _Listing(
            SimpleNamespace(Symbol="AAPL", Name="Duplicate Apple"),
            SimpleNamespace(Symbol="ms", Name="Morgan Stanley"),
            SimpleNamespace(Symbol="ABC D", Name="Invalid Space"),
        ),
    }

    monkeypatch.setattr(build_universe.fdr, "StockListing", lambda market: listings[market])

    assert build_universe.build_us() == [
        {
            "symbol": "AAPL",
            "name_ko": "Apple Inc.",
            "name_en": "Apple Inc.",
            "exchange": "NASDAQ",
            "currency": "USD",
        },
        {
            "symbol": "BRK.B",
            "name_ko": "Berkshire Hathaway",
            "name_en": "Berkshire Hathaway",
            "exchange": "NASDAQ",
            "currency": "USD",
        },
        {
            "symbol": "MS",
            "name_ko": "Morgan Stanley",
            "name_en": "Morgan Stanley",
            "exchange": "NYSE",
            "currency": "USD",
        },
    ]
