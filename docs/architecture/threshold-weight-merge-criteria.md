# Merge Criteria: Threshold & Score v2 Weight Changes (Issue #67)

**Authority**: ADR 0004 + constitution Principle IV (v1.2.0)  
**Canonical eng doc target**: `docs/architecture/threshold-weight-merge-criteria.md`  
(implementers copy/sync this content there).

## Purpose

Decide whether a candidate composite threshold and/or top-level Score v2 weight  
vector may enter an **explicit config-change PR**. Analysis and calibration  
reports alone never change live selection.

## Hard GO bullets (all required)

1. **Walk-forward OOS package** from the #66 harness with  
   `runIntent: go_evidence` and `measurementSource: ledger`.
2. **H20 primary**: aggregate mean pick **excess return vs market benchmark**  
   on H20 is **strictly positive**. H60 is reported, not a substitute for H20.
3. **Coverage**: aggregate OOS scored `pick` days **≥ 20**. Below floor →  
   `insufficient_coverage` → **NO-GO**.
4. **No contamination**: no unresolved look-ahead / four-axis risk findings for  
   the candidate package.
5. **Reproducibility**: calibration report + child walk-forward artifacts  
   regenerable from committed inputs (or documented provider assumptions);  
   config hashes only — no secrets.
6. **IS/OOS separation**: the winning candidate was **not** selected using OOS  
   metrics; IS and OOS decision-date sets are disjoint.
7. **Completeness**: required OOS evaluations finished; mid-grid failure →  
   **no overall GO**.

## Soft / informational (not hard GO)

- **`no_pick` ratio**: higher threshold typically raises `no_pick` and may restore  
  filtering; low `no_pick` alone is **not** NO-GO; high `no_pick` alone is **not**  
  GO. Reviewers use it as tradeoff context beside excess return and coverage.
- Nested/sub-factor weights: out of scope; changing them is not authorized by  
  this gate.

## NO-GO

If any hard bullet fails, or `packageIntent` is only `exploratory`, or mode is  
`baseline-only` without a subsequent explicit GO package for a **changed**  
candidate: **do not** open a live config PR. Frozen `COMPOSITE_THRESHOLD` and  
`WEIGHT_*` remain.

## After GO

1. Human opens an explicit PR editing only approved live constants in  
   `scripts/config.py` (and necessary test expectation updates).  
2. PR description links calibration report path, walk-forward `go_evidence`  
   report(s), and this criteria doc.  
3. Reviewers re-check hard bullets; Methodology copy updates if reader-facing  
   threshold/weight text changes.

## Anti-patterns

- Using `backtest_screen` snapshot comparison as merge evidence  
- Treating baseline-only “GO on frozen constants” as permission to change them  
- Optuna / unbounded search  
- Silent renormalization of invalid weight vectors

## Addendum: Issue #69 / Score v3 growth-weight reallocation

Same **hard GO bullets** as Issue #67 above. Analysis and calibration reports  
alone never change live selection.

Until ADR 0004 GO: **analysis-only**; live `WEIGHT_*`, `COMPOSITE_THRESHOLD`,  
and `SCORE_VERSION=2` remain frozen.

On GO: an explicit config PR may set `SCORE_VERSION=3` together with the  
approved top-level `WEIGHT_*` vector (no separate feature flag; no auto-edit  
from calibration). Reviewers re-check the hard bullets before merge.
