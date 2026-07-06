"""Unit tests for company profile helpers."""

from __future__ import annotations

from profile import build_stock_profile, short_overview, truncate_summary


def test_truncate_summary_limits_sentences_and_chars():
    text = (
        "First sentence here. Second sentence here. "
        "Third sentence here. Fourth sentence should be dropped."
    )
    result = truncate_summary(text, max_chars=80, max_sentences=2)
    assert result.count(".") <= 2
    assert len(result) <= 80


def test_build_stock_profile_uses_summary_and_template():
    info = {
        "longBusinessSummary": "Acme Corp makes widgets worldwide. It sells to retailers.",
        "sector": "Industrials",
        "industry": "Manufacturing",
    }
    profile = build_stock_profile(info, name_ko="아크미", name_en="Acme Corp")
    assert profile is not None
    assert "widgets" in profile["overview"]["en"]
    assert profile["overview"]["ko"] == "아크미는 Industrials 분야 Manufacturing 기업입니다."
    assert profile["sector"]["en"] == "Industrials"


def test_build_stock_profile_fallback_without_summary():
    info = {"sector": "Technology", "industry": "Software"}
    profile = build_stock_profile(info, name_ko="테크", name_en="Tech Inc")
    assert profile is not None
    assert "Technology" in profile["overview"]["en"]
    assert profile["overview"]["ko"] == "테크는 Technology 분야 Software 기업입니다."


def test_build_stock_profile_returns_none_without_data():
    assert build_stock_profile({}, name_ko="없음", name_en="None Co") is None


def test_short_overview_clips_long_text():
    text = "A" * 200
    assert short_overview(text, max_chars=50).endswith("…")
    assert len(short_overview(text, max_chars=50)) <= 51
