"""Semantic validation for optional daily topCandidates (Issue #72)."""

from __future__ import annotations

from typing import Any


def validate_top_candidates(entry: dict[str, Any]) -> list[str]:
    """Return human-readable errors for Top-N semantic rules. Empty = OK.

    JSON Schema covers shape; this covers unique symbols, contiguous ranks,
    index alignment, and pick≡rank1.
    """
    if "topCandidates" not in entry:
        return []

    rows = entry["topCandidates"]
    errors: list[str] = []
    if not isinstance(rows, list):
        return ["topCandidates must be an array"]

    n = len(rows)
    if n == 0:
        errors.append("topCandidates must be omitted when empty (do not write [])")
        return errors
    if n > 5:
        errors.append(f"topCandidates length {n} exceeds max 5")

    symbols: set[str] = set()
    ranks: list[int] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"topCandidates[{i}] must be an object")
            continue
        rank = row.get("rank")
        symbol = row.get("symbol")
        if rank != i + 1:
            errors.append(
                f"topCandidates[{i}].rank must be {i + 1}, got {rank!r}"
            )
        if isinstance(rank, int):
            ranks.append(rank)
        if not isinstance(symbol, str) or not symbol:
            errors.append(f"topCandidates[{i}].symbol missing or empty")
        elif symbol in symbols:
            errors.append(f"duplicate topCandidates symbol: {symbol}")
        else:
            symbols.add(symbol)

    expected_ranks = list(range(1, n + 1))
    if ranks and sorted(ranks) != expected_ranks:
        errors.append(
            f"topCandidates ranks must be contiguous 1..{n}, got {sorted(ranks)}"
        )

    if entry.get("status") == "pick":
        stock = entry.get("stock") or {}
        pick_symbol = stock.get("symbol")
        if rows and isinstance(rows[0], dict):
            rank1_symbol = rows[0].get("symbol")
            if pick_symbol and rank1_symbol != pick_symbol:
                errors.append(
                    f"pick symbol {pick_symbol!r} must equal topCandidates rank1 "
                    f"{rank1_symbol!r}"
                )

    return errors
