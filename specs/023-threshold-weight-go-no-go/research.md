# Research: Threshold·Weight GO/NO-GO Recalibration

**Date**: 2026-09-03  
**Spec**: [spec.md](./spec.md)

## R1 — Language & runtime

**Decision**: Python 3.11+ under existing `scripts/` stack.  
**Rationale**: Screening, Score v2, and walk-forward (#66) are already Python.  
**Alternatives considered**: TypeScript orchestration — rejected; no PIT/screen path in TS.

## R2 — CLI / package layout

**Decision**: Top-level `scripts/calibrate.py` + package `scripts/calibration/`  
(mirrors `walk_forward.py` / `walk_forward/`).  
**Rationale**: Calibration owns multi-candidate IS→OOS orchestration and the  
calibration report; keeps #66 harness single-candidate.  
**Alternatives considered**: Fold everything into `walk_forward.py` — rejected;  
would blur FR-024 (≤10) vs walk-forward’s historical ≤4 single-run concern and  
mix IS ranking with fold math.

## R3 — Reuse walk-forward for OOS (and IS metrics)

**Decision**: Calibration invokes the #66 harness programmatically (same report  
contract / schema) once per candidate. IS ranking uses `runIntent: exploratory`  
on an **IS-only** fold calendar; GO uses `runIntent: go_evidence` +  
`measurementSource: ledger` on a **disjoint OOS** calendar.  
**Rationale**: FR-003, FR-026; constitution IV IS/OOS separation.  
**Alternatives considered**: Snapshot `backtest_screen` for IS — rejected  
(FR-017); reinventing fold metrics — rejected (Principle III).

## R4 — Lift analysis-only overrides in walk-forward

**Decision**: Extend `walk_forward.config.RunConfig` to allow optional  
`thresholdOverride: number | null` and `weightOverrides: {WEIGHT_*} | null`  
for **analysis runs only**. Validate weight sum `1.0±1e-6` and known top-level  
keys only. Update tests that currently reject any `weightOverrides`.  
**Rationale**: Today `weightOverrides` are hard-rejected; #67 cannot evaluate  
candidates without injection. Live `scripts/config.py` constants stay frozen.  
**Alternatives considered**: Fork screening outside walk-forward — rejected  
(duplication); edit config.py during runs — rejected (Principle IV).

## R5 — Override injection surface

**Decision**: Context manager patches runtime module globals used by screening:
- `screening.core.COMPOSITE_THRESHOLD` ← thresholdOverride  
- `scoring.composite.WEIGHT_SIZE|VALUATION|GROWTH|QUALITY|ENTRY|MOMENTUM`  
  ← weightOverrides  

Wire through `pit_screen.pit_screen_day(..., threshold_override=, weight_overrides=)`.  
**Rationale**: Existing PIT test already monkeypatches `screening.core.COMPOSITE_THRESHOLD`;  
`scoring.composite` resolves WEIGHT_* at call time from module globals.  
**Alternatives considered**: Pass weights through every scoring function — larger  
diff; rejected for v1.

## R6 — IS ranking metric

**Decision**: Rank candidates by IS aggregate **H20 mean excess return vs  
benchmark** (descending); ties broken by higher IS `oosPickDays` then  
`candidateId` lexicographic for determinism. Record rationale in report.  
**Rationale**: Aligns with ADR 0004 primary metric; deterministic.  
**Alternatives considered**: Optimize `no_pick` ratio — rejected (FR-023 soft  
only); composite score mean — rejected (not OOS-aligned).

## R7 — GO / NO-GO engine

**Decision**: Pure function over walk-forward OOS report + merge-criteria rules:

| Check | GO requires |
|-------|-------------|
| Coverage | `oosPickDays ≥ 20` (else `insufficient_coverage` → NO-GO) |
| H20 excess | Aggregate mean excess return **strictly > 0** |
| Contamination | No unresolved look-ahead / contamination flags |
| Completeness | Required candidates finished; mid-grid failure → no overall GO |
| IS/OOS | Config proves IS window disjoint from OOS decision dates |

`no_pick` ratio recorded, **not** a hard bullet (FR-023).  
**Rationale**: ADR 0004 + brainstorm Q2.  
**Alternatives considered**: Soft score blending `no_pick` into GO — rejected.

## R8 — Artifact location & schema

**Decision**: Write `content/calibration/{runId}.json` validated by  
`scripts/schema/calibration-report.schema.json`; register in `validate_content.py`  
and `gen_types.mjs`. Walk-forward child reports remain under  
`content/walk-forward/` (referenced by path/hash).  
**Rationale**: Additive (Principle III); separate lifecycle from WF reports.  
**Alternatives considered**: Embed full WF JSON inside calibration — rejected  
(duplication / size); overwrite daily picks — forbidden.

## R9 — Modes

**Decision**: Config `mode`:
- `search` — IS rank all candidates (≤10), then OOS `go_evidence` for  
  top-N (default N=1) or explicitly listed promotees  
- `baseline-only` — skip IS search; OOS evaluate frozen live constants only;  
  still emits GO/NO-GO; MUST NOT imply config-change authorization  

`packageIntent`: `exploratory` | `go_evidence` on the calibration package.  
**Rationale**: FR-025, FR-032.  
**Alternatives considered**: Always search — rejected (baseline evidence needed).

## R10 — Candidate grid defaults (fixtures)

**Decision**: Ship a small documented default grid in fixtures/docs that  
includes: live baseline; ≥1 threshold **> 70**; ≥1 alternate top-level weight  
vector summing to 1.0; total ≤10. Nested weights never appear.  
**Rationale**: FR-019, FR-022.  
**Alternatives considered**: Empty default forcing user authoring — worse UX.

## R11 — Merge-criteria documentation

**Decision**: `docs/architecture/threshold-weight-merge-criteria.md` (engineering  
authority) + short pointer from Methodology or architecture README; mirror  
summary in `specs/023/.../contracts/merge-criteria.md`.  
**Rationale**: FR-008, FR-031; constitution authority split.  
**Alternatives considered**: Spec-only doc — weaker for PR reviewers.

## R12 — Live config change

**Decision**: Tooling **never** writes `scripts/config.py`. On GO, CLI prints a  
human checklist / suggested PR body citing report paths; human opens explicit  
PR. On NO-GO, exit non-zero for `go_evidence` packageIntent when verdict is  
NO-GO (configurable) but never mutates live constants.  
**Rationale**: FR-009, FR-010, SC-005.  
**Alternatives considered**: Auto-edit config on GO — rejected (freeze gate).

## R13 — Determinism & npm scripts

**Decision**: Canonical JSON same as walk-forward  
(`sort_keys=True, separators=(",", ":"), ensure_ascii=False`).  
npm: `"calibrate": "cd scripts && python calibrate.py"`,  
`"calibrate:smoke": "cd scripts && python -m pytest tests/test_calibration_smoke.py -q"`.  
**Rationale**: FR-013, SC-006; discoverability.  
**Alternatives considered**: Makefile — repo uses package.json.

## R14 — Walk-forward MAX_CANDIDATES

**Decision**: Leave walk-forward single-`candidateId` path as primary; do **not**  
raise walk-forward’s unused `candidateIds` limit to 10. Calibration enforces ≤10.  
**Rationale**: YAGNI; FR-024 owned by calibration.  
**Alternatives considered**: Unify limits — unnecessary coupling.
