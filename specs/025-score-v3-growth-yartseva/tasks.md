# Tasks: Score v3 Growth Weight Reallocation (Yartseva)

**Input**: `specs/025-score-v3-growth-yartseva/` (spec.md + plan.md)
**Prerequisites**: constitution v1.2.0; brainstorm complete (3 sessions)

## Phase 1: Setup

**Purpose**: Shared fixtures and schema readiness

- [x] T001 Create `scripts/tests/fixtures/calibration/growth-yartseva-smoke-config.json` with the four named Issue #69 candidates + `compareToLiveBaseline: true` (exploratory / fixture-recompute OK for smoke)
- [x] T002 [P] Add committed `scripts/calibration/configs/growth-yartseva-issue69.json` documenting the default search grid (same four candidates; `compareToLiveBaseline: true`)
- [x] T003 Extend calibration config schema + `calibration/config.py` to accept optional `compareToLiveBaseline` (default `false`) without breaking existing fixtures

**Checkpoint**: Existing `npm run test:python` still passes; new config loads.

---

## Phase 2: Foundational

**Purpose**: Issue #69 validation module (blocks user stories)

- [x] T004 [TDD] [SUBAGENT] Write failing tests in `scripts/tests/test_growth_yartseva_grid.py` for: default four candidate IDs; each `WEIGHT_GROWTH` in `[0.05, 0.20)`; sum `1.0±1e-6`; Entry/Momentum unchanged vs live; reject growth≥0.20, growth&lt;0.05, Entry/Momentum redistribution
- [x] T005 [TDD] [SUBAGENT] Implement `scripts/calibration/growth_yartseva.py` (`DEFAULT_CANDIDATES`, `validate_growth_reallocation_candidate`, `assert_issue69_grid`) until T004 passes
- [x] T006 [P] [TDD] Write `scripts/tests/test_growth_yartseva_freeze.py` asserting live `WEIGHT_*` / `SCORE_VERSION==2` / `COMPOSITE_THRESHOLD` unchanged

**Checkpoint**: Grid + freeze tests green; live constants untouched.

---

## Phase 3: User Story 1 — Candidate grid (P1)

- [x] T007 [US1] Wire committed configs through `assert_issue69_grid` (load helper or test that configs match `DEFAULT_CANDIDATES`)
- [x] T008 [P] [US1] Document candidate notes (growth shrink + redistribution) in config `notes` fields / module docstrings

**Checkpoint**: US1 acceptance — grid validates offline.

---

## Phase 4: User Story 2 — IS/OOS + side-by-side baseline (P1)

- [x] T009 [TDD] [SUBAGENT] [US2] Failing test `test_growth_yartseva_baseline_compare.py`: when `compareToLiveBaseline` true, report `oosEvaluations` includes both promotee and `score-v2-baseline` (or equivalent live baseline id)
- [x] T010 [TDD] [SUBAGENT] [US2] Update `calibration/runner.py` to append live-baseline OOS evaluation when `compareToLiveBaseline` is true; keep fail-closed behavior
- [x] T011 [P] [US2] Extend GO PR hint for growth study / search+go_evidence to mention explicit PR with `SCORE_VERSION=3` + approved weights (no auto-edit)

**Checkpoint**: Fixture/mocked path proves side-by-side baseline row; no live merge.

---

## Phase 5: User Story 3 — Methodology + Epic docs (P1)

- [x] T012 [P] [SUBAGENT] [US3] Update `src/pages/methodology.astro` KR/EN Score v3 candidates section: growth-weight reallocation (Yartseva trailing-growth weak), gated, Issue #69, not live until GO
- [x] T013 [P] [SUBAGENT] [US3] Short addendum in `docs/architecture/threshold-weight-merge-criteria.md` for Issue #69 (`SCORE_VERSION=3` on GO + approved weights)
- [x] T014 [US3] Ensure growth-yartseva smoke config referenced from tests; `npm run test:python` passes for new suite

**Checkpoint**: Bilingual gated copy + merge-criteria addendum + tests green.

---

## Phase 6: User Story 4 — Reuse harness (P2)

- [x] T015 [US4] Confirm growth path uses existing calibrate/walk-forward contracts (no `backtest_screen` GO path); add regression assert in tests if missing
- [x] T016 [P] [US4] Reject nested weight keys via existing `validate_weights` (covered by grid tests)

**Checkpoint**: No parallel measurement stack introduced.

---

## Phase 7: Polish

- [x] T017 Run `npm run test:python` and fix failures — **195 passed**
- [x] T018 [REVIEW] Spec compliance pass: SC-001–SC-005 checklist in review notes
- [x] T019 Update `progress.yml` execute → done when all tasks checked

## Dependencies

```text
Phase 1 → Phase 2 → Phase 3 ∥ Phase 4 → Phase 5 ∥ Phase 6 → Phase 7
T004 → T005
T009 → T010
T012 ∥ T013 (after Phase 4 preferred for accurate copy)
```

## Parallel Opportunities

- T002 ∥ T003 after T001 skeleton
- T006 ∥ T005
- T012 ∥ T013 ∥ T015
- Phase 3 and Phase 4 after Phase 2 foundational

## Execution Notes (this pipeline)

User explicitly requested: run execute with subagents in parallel; **auto-advance all phase checkpoints** without waiting for human approval.
