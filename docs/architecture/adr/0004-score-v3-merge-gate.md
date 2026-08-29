# ADR 0004: Score v3 merge (GO / NO-GO) evidence

- **Status**: Proposed
- **Date**: 2026-08-29
- **Tags**: performance-loop, score-v3, governance

## Context

Changing Score weights without out-of-sample evidence risks overfitting and
silent degradation of the daily public picks. Constitution requires architecture
before behavioral change; Score v2 must stay frozen until GO.

## Decision

**Preferred merge gate**:

1. **Score v2 remains the live selector** until this ADR’s GO criteria are met
   and an explicit merge PR is approved.
2. **GO** requires all of:
   - Walk-forward OOS package per ADR 0003 (H20 required, H60 reported)
   - Primary metric: average pick **excess return vs benchmark** on H20 over the
     declared OOS window is **strictly positive**
   - No unresolved look-ahead or contamination findings in the four-axis risk
     review for that candidate
   - Ledger/performance artifacts reproducible from committed inputs (or
     documented provider assumptions)
3. **NO-GO** if any GO bullet fails, or if coverage is too thin (document minimum
   pick-count threshold in the candidate’s measurement note; default floor:
   **≥ 20** scored `pick` days in the OOS window unless a superseding note
   justifies otherwise).
4. Factor work (#68–#70) may proceed as **analysis** but **must not** merge
   weight changes until GO.

## Consequences

- **Positive**: Clear stop-ship for premature v3; aligns with Principle IV/V.
- **Negative**: Slower iteration; may need more history before first GO.
- **Follow-up**: #67 plumbing; publish measurement summary linked from Epic #74
  before weight PR.
