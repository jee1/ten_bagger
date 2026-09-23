"""Contract: Daily deploy must chain exactly one Ledger Regenerate dispatch (#158)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DAILY = (REPO_ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")
LEDGER = (REPO_ROOT / ".github" / "workflows" / "ledger.yml").read_text(encoding="utf-8")


def test_daily_chains_ledger_after_pages_deploy() -> None:
    assert "dispatch-ledger:" in DAILY
    assert "needs: [generate-and-deploy, deploy]" in DAILY
    assert DAILY.count("gh workflow run ledger.yml") == 1
    assert "--ref main" in DAILY
    assert "asOfDate=${AS_OF}" in DAILY or "asOfDate=${AS_OF}" in DAILY
    assert "needs.generate-and-deploy.outputs.target_date" in DAILY
    assert "gh run list" not in DAILY
    assert "gh run watch" not in DAILY
    assert "MARKER=" not in DAILY
    assert "needs: [generate-and-deploy, deploy, dispatch-ledger]" in DAILY
    assert "dispatch-ledger'].result == 'failure'" in DAILY
    dispatch_idx = DAILY.index("dispatch-ledger:")
    assert "permissions:" in DAILY[dispatch_idx:]
    assert "actions: write" in DAILY[dispatch_idx : DAILY.index("notify-failure:")]
    top_perms_end = DAILY.index("concurrency:")
    assert "actions: write" not in DAILY[:top_perms_end]


def test_daily_never_writes_ledger_or_performance() -> None:
    assert "regenerate_ledger" not in DAILY
    assert "git add content/ledger/" not in DAILY
    assert "git add content/performance/" not in DAILY
    assert "Must not write content/ledger/** or content/performance/**" in DAILY


def test_ledger_stays_manual_dispatch_only() -> None:
    assert "schedule:" not in LEDGER
    assert "workflow_dispatch:" in LEDGER
    assert "asOfDate:" in LEDGER
