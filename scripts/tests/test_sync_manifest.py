"""Tests for manifest sync."""

from __future__ import annotations

from sync_manifest import build_manifest, collect_daily_dates


def test_collect_daily_dates_sorted_desc():
    dates = collect_daily_dates()
    assert dates == sorted(dates, reverse=True)


def test_build_manifest_matches_files():
    manifest = build_manifest()
    assert manifest["dates"] == collect_daily_dates()
    assert manifest["lastUpdated"]
