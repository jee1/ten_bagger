"""Unit tests for exchange universe builders."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from urllib.error import HTTPError

import pandas as pd
import pytest

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


def test_kr_stock_listing_falls_back_on_cache_404(monkeypatch):
    def boom(_market: str):
        raise HTTPError("https://example.invalid/missing.csv", 404, "Not Found", None, None)

    fallback = pd.DataFrame(
        [{"Code": "005930", "Name": "삼성전자", "Marcap": 1, "MarketId": "STK"}]
    )
    monkeypatch.setattr(build_universe.fdr, "StockListing", boom)
    monkeypatch.setattr(build_universe, "_kr_listing_from_stale_cache", lambda market: fallback)

    listing = build_universe._kr_stock_listing("KOSPI")
    assert list(listing["Code"]) == ["005930"]


def test_kr_stock_listing_reraises_non_404(monkeypatch):
    def boom(_market: str):
        raise HTTPError("https://example.invalid/x", 500, "Server Error", None, None)

    monkeypatch.setattr(build_universe.fdr, "StockListing", boom)

    with pytest.raises(HTTPError) as excinfo:
        build_universe._kr_stock_listing("KOSPI")
    assert excinfo.value.code == 500


def test_kr_listing_from_stale_cache_walks_back_dates(monkeypatch):
    calls: list[str] = []

    def fake_read_csv(url, *args, **kwargs):
        calls.append(url)
        if url.endswith("2026-09-09.csv") or url.endswith("2026-09-08.csv"):
            raise HTTPError(url, 404, "Not Found", None, None)
        return pd.DataFrame(
            [
                {"Code": "005930", "Name": "삼성전자", "Marcap": 10, "MarketId": "STK"},
                {"Code": "000660", "Name": "SK하이닉스", "Marcap": 9, "MarketId": "STK"},
                {"Code": "357780", "Name": "솔브레인", "Marcap": 1, "MarketId": "KSQ"},
            ]
        )

    monkeypatch.setattr(build_universe.pd, "read_csv", fake_read_csv)

    listing = build_universe._kr_listing_from_stale_cache(
        "KOSPI", as_of=date(2026, 9, 9), lookback_days=5
    )
    assert list(listing["Code"]) == ["005930", "000660"]
    assert calls[0].endswith("2026-09-09.csv")
    assert calls[1].endswith("2026-09-08.csv")
    assert calls[2].endswith("2026-09-07.csv")
