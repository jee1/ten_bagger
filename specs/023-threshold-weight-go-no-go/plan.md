# Implementation Plan: Threshold·Weight GO/NO-GO Recalibration

**Branch**: `feature/performance-threshold-weight-go-no-go` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/023-threshold-weight-go-no-go/spec.md`

> **For agentic workers:** Prefer `/speckit.superspec.tasks` then
> `/speckit.superspec.execute` (TDD + subagents). Do not auto-edit live
> `scripts/config.py` selection constants.

## Summary

Add a Python **calibration** CLI that (1) evaluates a fixed grid of composite
threshold and top-level Score v2 weight candidates on **IS-only** walk-forward
windows, (2) runs **OOS `go_evidence`** via the existing #66 harness for
selected candidates, (3) emits a deterministic **calibration report** +
documented **merge criteria**, and (4) never mutates live selection constants —
config PRs are human-only after ADR 0004 GO.

## Technical Context

**Language/Version**: Python 3.11+ (existing `scripts/` stack)
**Primary Dependencies**: pytest, jsonschema, existing `walk_forward/`,
`screening/`, `scoring/`, `performance/`
**Storage**: Git JSON — `content/calibration/*.json` (additive); child reports
in `content/walk-forward/`; reads `content/ledger/`, `content/performance/`
**Testing**: pytest (`npm run test:python`); `npm run calibrate:smoke`
**Target Platform**: Linux/macOS CLI (maintainer/reviewer workflows)
**Project Type**: Python CLI + JSON schema contracts (Astro site unchanged for
required acceptance)
**Performance Goals**: v1 single-threaded; ≤10 candidates per run (FR-024)
**Constraints**: No Optuna; no live `config.py` writes; no `backtest_screen` as
GO evidence; IS/OOS date disjoint; weight sum `1.0±1e-6`; nested weights OOS;
`no_pick` informational only

## Constitution Check

*GATE: Must pass before proceeding. Re-checked after design — all PASS.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Reports under `content/calibration/`; no runtime DB; daily picks untouched |
| II. Point-in-Time Measurement | PASS | Reuses #66 PIT walk-forward; IS/OOS calendars disjoint; ledger outcomes for GO |
| III. Additive Performance Artifacts | PASS | New calibration schema/dir; WF child reports additive; no pick rewrite |
| IV. Score Freeze Until Merge Gate | PASS | Analysis-only overrides via patch; GO/NO-GO engine; human config PR only |
| V. Schema Contracts and Validation | PASS | `calibration-report.schema.json`; validate:content + gen:types registration |

## Project Structure

### Documentation (this feature)

```text
specs/023-threshold-weight-go-no-go/
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── calibration-report.schema.json
│   ├── cli-contract.md
│   └── merge-criteria.md
└── tasks.md             # /speckit.superspec.tasks
```

### Source Code (repository root)

```text
scripts/
├── calibrate.py                      # CLI entry
├── calibration/
│   ├── __init__.py
│   ├── config.py                     # CalibrationRunConfig, ≤10, IS/OOS disjoint
│   ├── candidates.py                 # Weight/threshold validation (1.0±1e-6)
│   ├── overrides.py                  # Context manager patching screen/score globals
│   ├── is_rank.py                    # IS walk-forward loop + ranking
│   ├── verdict.py                    # ADR 0004 GO/NO-GO pure function
│   ├── report.py                     # Calibration report + canonical JSON
│   └── runner.py                     # Orchestrate search / baseline-only
├── walk_forward/
│   ├── config.py                     # ALLOW analysis thresholdOverride + weightOverrides
│   └── pit_screen.py                 # Apply overrides during pit_screen_day
├── schema/
│   └── calibration-report.schema.json
├── tests/
│   ├── test_calibration_*.py
│   ├── test_walk_forward_config.py   # update: overrides allowed when valid
│   └── fixtures/calibration/
docs/architecture/
└── threshold-weight-merge-criteria.md
package.json                          # calibrate, calibrate:smoke scripts
```

**Structure Decision**: New `calibration/` package owns multi-candidate IS→OOS
orchestration and verdict/report. Extend `walk_forward` minimally so each
candidate evaluation reuses the same PIT + report contract (research R3–R5).
Do not raise walk-forward’s unused multi-id cap; calibration enforces ≤10.

## Execution Strategy

### TDD Requirements

- [x] **`calibration/candidates.py`**: Reject bad weight sums / unknown keys /
  >10 grid
- [x] **`calibration/verdict.py`**: Coverage floor, H20 excess > 0, soft
  `no_pick`, incomplete → no GO
- [x] **`calibration/config.py`**: IS/OOS overlap detection; baseline-only mode
- [x] **`calibration/report.py`**: Canonical JSON determinism
- [x] **`walk_forward` overrides**: Valid overrides accepted; applied in PIT
  screen; live config module unchanged after context exits
- [x] **Smoke suite**: Offline end-to-end search + fail-closed paths

### Parallel Execution Opportunities

- [x] Schema registration (`validate_content.py`, `gen_types.mjs`, `config.py`
  paths) parallel to package scaffold
- [x] Merge-criteria doc parallel to verdict tests
- [x] Fixture authoring parallel to unit tests

### Human Checkpoints

1. After foundational — schema validates sample calibration JSON; WF override
   tests green
2. After US1+US2 — IS ranking + OOS verdict on fixtures
3. After smoke — `calibrate:smoke` offline green; confirm `config.py` constants
   unchanged
4. Before merge — `npm run test:python` + `validate:content`; no live constant
   drift unless separate GO PR

### Review Gates

- [x] **Override injection** (`overrides.py` / `pit_screen.py`): look-ahead and
  freeze surface
- [x] **Verdict rules** vs ADR 0004 / merge-criteria.md
- [x] **CLI contract**: exit codes 2 vs 3; never writes `config.py`

## Complexity Tracking

> No constitution violations requiring justification.
>
> Note: Extending walk-forward to accept analysis overrides is an intentional
> #66 follow-on; live freeze remains intact because overrides are process-local
> patches only.

## Phase 0 Output

See [research.md](./research.md) — all technical unknowns resolved (no
NEEDS CLARIFICATION remaining).

## Phase 1 Output

- [data-model.md](./data-model.md)
- [contracts/](./contracts/)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Re-check

All principles remain PASS. Design adds additive calibration artifacts, reuses
PIT walk-forward for measurement, keeps Score/threshold freeze until human GO
PR, and registers schema contracts for CI validation.
