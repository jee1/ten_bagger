"""Point-in-time fundamentals availability for walk-forward re-screening (#175)."""

from __future__ import annotations

from typing import Any

from config import market_for_date

from walk_forward.config import RunConfig


def fundamentals_pit_available(market: str, as_of_date: str) -> bool:
    """Whether scoring fundamentals for *as_of_date* are point-in-time safe.

    Stage 0: no snapshot store — always False. Stage 2 replaces this with
    snapshot lookup (single call site for walk-forward contamination).
    """
    _ = (market, as_of_date)
    return False


def _uses_override_rescreen(run_config: RunConfig) -> bool:
    return run_config.thresholdOverride is not None or bool(run_config.weightOverrides)


def contamination_findings_for_run(
    run_config: RunConfig,
    fold_results: list[dict[str, Any]],
) -> list[str]:
    """Contamination tags for live override re-screen (not ledger pick replay)."""
    if not _uses_override_rescreen(run_config):
        return []

    markets = set(run_config.markets)
    count = 0
    for fold in fold_results:
        sessions = list(fold.get("trainSessions") or []) + list(fold.get("oosSessions") or [])
        for session_str in sessions:
            market = market_for_date(session_str)
            if market not in markets:
                continue
            if not fundamentals_pit_available(market, session_str):
                count += 1
    if count == 0:
        return []
    return [f"fundamentals_not_pit:{count}"]
