"""Tests for Stooq secondary price adapter (ADR 0005)."""

from __future__ import annotations

import pytest
import stooq_prices

SAMPLE_CSV = """Date,Open,High,Low,Close,Volume
2026-07-01,10.0,11.0,9.5,10.5,1000
2026-07-02,10.5,11.5,10.0,11.0,1100
"""


def test_to_stooq_symbol_us():
    assert stooq_prices.to_stooq_symbol("AAPL") == "aapl.us"
    assert stooq_prices.to_stooq_symbol("AAPL.US") == "aapl.us"


def test_to_stooq_symbol_kr():
    assert stooq_prices.to_stooq_symbol("005930.KS") == "005930.ks"
    assert stooq_prices.to_stooq_symbol("035420.KQ") == "035420.ks"


def test_to_stooq_symbol_empty():
    assert stooq_prices.to_stooq_symbol("") is None
    assert stooq_prices.to_stooq_symbol("   ") is None


def test_parse_stooq_csv_ohlcv():
    hist = stooq_prices.parse_stooq_csv(SAMPLE_CSV)
    assert hist is not None
    assert hist["Close"].tolist() == [10.5, 11.0]
    assert hist["Open"].tolist() == [10.0, 10.5]


def test_parse_stooq_csv_rejects_garbage():
    assert stooq_prices.parse_stooq_csv("") is None
    assert stooq_prices.parse_stooq_csv("<!DOCTYPE html>") is None
    assert stooq_prices.parse_stooq_csv("foo,bar\n1,2") is None


def test_fetch_history_injectable(monkeypatch):
    hist = stooq_prices.fetch_history(
        "TEST",
        period="max",
        fetch_text=lambda _url: SAMPLE_CSV,
    )
    assert hist["Close"].tolist() == [10.5, 11.0]


def test_fetch_history_raises_on_empty(monkeypatch):
    with pytest.raises(RuntimeError, match="no usable OHLCV"):
        stooq_prices.fetch_history(
            "TEST",
            period="max",
            fetch_text=lambda _url: "Date,Open,High,Low,Close,Volume\n",
        )
