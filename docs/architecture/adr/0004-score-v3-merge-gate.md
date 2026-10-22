# ADR 0004: Score v3 merge (GO / NO-GO) evidence

- **Status**: Accepted (2026-10-22, amended)
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
   - Robustness metric: the H20 **median** excess return vs benchmark is
     **strictly positive in every market** in the OOS package
     (`h20ExcessReturnMedianMin > 0`). A missing median fails closed.
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

## Amendment 2026-10-22: median bullet, pre-registered

Added before the #175 stage 3 OOS window opens (2026-11-09) and before any of
its results exist. Reason: package `d9a711990b5fe529` returned GO on an H20
mean that one 10x entry-price error (002780.KS) had inflated. A mean alone
lets one outlier decide the verdict. Requiring the median in each market also
stops one market from carrying the other.

Reported, not gating: Newey-West t of H20 excess, and the edge baseline
(pick vs random and size-matched random, `content/edge-baseline/`).

Every run counts as a trial and is listed in
`docs/architecture/trial-registry.md`. The thresholds above MUST NOT change
after stage 3 results are seen. A later change applies only to a new window.

## Consequences

- **Positive**: Clear stop-ship for premature v3; aligns with Principle IV/V.
- **Negative**: Slower iteration; may need more history before first GO.
- **Follow-up**: #67 plumbing; publish measurement summary linked from Epic #74
  before weight PR.
