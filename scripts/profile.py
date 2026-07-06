"""Build company profile snippets from yfinance ticker info."""

from __future__ import annotations

import re

_SUMMARY_MAX_CHARS = 300
_SUMMARY_MAX_SENTENCES = 3
_CARD_OVERVIEW_MAX_CHARS = 150


def truncate_summary(
    text: str,
    *,
    max_chars: int = _SUMMARY_MAX_CHARS,
    max_sentences: int = _SUMMARY_MAX_SENTENCES,
) -> str:
    text = text.strip()
    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    length = 0
    for sentence in sentences[:max_sentences]:
        if not sentence:
            continue
        next_len = length + len(sentence) + (1 if parts else 0)
        if next_len > max_chars and parts:
            break
        parts.append(sentence)
        length = next_len

    return " ".join(parts).strip()


def short_overview(overview: str, *, max_chars: int = _CARD_OVERVIEW_MAX_CHARS) -> str:
    overview = overview.strip()
    if len(overview) <= max_chars:
        return overview

    clipped = overview[:max_chars]
    last_space = clipped.rfind(" ")
    if last_space > max_chars // 2:
        clipped = clipped[:last_space]
    return clipped.rstrip(".,; ") + "…"


def build_stock_profile(
    info: dict,
    *,
    name_ko: str,
    name_en: str,
) -> dict | None:
    sector = str(info.get("sector") or "").strip()
    industry = str(info.get("industry") or "").strip()
    summary = str(info.get("longBusinessSummary") or "").strip()

    overview_en = truncate_summary(summary) if summary else ""
    if not overview_en and sector and industry:
        overview_en = f"{name_en} operates in the {sector} sector, focusing on {industry}."
    elif not overview_en and sector:
        overview_en = f"{name_en} operates in the {sector} sector."

    if sector and industry:
        overview_ko = f"{name_ko}는 {sector} 분야 {industry} 기업입니다."
    elif sector:
        overview_ko = f"{name_ko}는 {sector} 분야 기업입니다."
    elif overview_en:
        overview_ko = f"{name_ko}는 글로벌 상장 기업입니다."
    else:
        return None

    profile: dict = {
        "overview": {"ko": overview_ko, "en": overview_en or overview_ko},
    }
    if sector:
        profile["sector"] = {"ko": sector, "en": sector}
    if industry:
        profile["industry"] = {"ko": industry, "en": industry}
    return profile
