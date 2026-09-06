# Tasks: Score v3 Live Merge after Search `go_evidence`

**Input**: `specs/030-score-v3-live-merge-go-evidence/`
**Prerequisites**: plan.md, spec.md (brainstormed)
**GitHub**: #91

## Phase 1 — Setup

- [x] T001 Document contracts + quickstart stubs under `specs/030-score-v3-live-merge-go-evidence/`
- [x] T002 [P] Update `docs/architecture/074-phase2-measurement-note.md` Next section for #91 path
- [x] T003 [P] Addendum on `docs/architecture/threshold-weight-merge-criteria.md` (search GO vs baseline-only)

## Phase 2 — Foundational (US2 measure fill)

- [x] T004 [TDD] Failing test: ledger miss + weightOverrides → H20 completed via price recompute (not stuck on `missing_ledger_row`)
- [x] T005 [TDD] Failing test: ledger hit preferred over recompute when row exists
- [x] T006 [TDD] Failing test: no-override ledger miss still `missing_ledger_row`
- [x] T007 Implement hybrid fill in `scripts/walk_forward/measure.py` (+ `execute.py` provider wiring if needed)
- [x] T008 [REVIEW] Measure tests green; freeze tests still `SCORE_VERSION == 2`

## Phase 3 — US1 Readiness

- [x] T009 [TDD] [P] Failing tests for readiness `ready` / `not_ready` determinism (fixture ledger)
- [x] T010 Implement `scripts/walk_forward/readiness.py` (+ optional CLI flag or calibrate preflight helper)
- [x] T011 Wire search `go_evidence` preflight message/exit on `not_ready` (no merge claim)

## Phase 4 — US3/US4 Search package + hints

- [x] T012 [P] Add `scripts/calibration/configs/score-v3-search-go-evidence.json` (growth grid; ledger OOS; search go_evidence)
- [x] T013 [TDD] Smoke: search GO + compareToLiveBaseline prints SCORE_VERSION=3 PR hint; baseline-only does not
- [x] T014 [TDD] Dry-run / validation of new config loads (`calibrate.py run --dry-run`)
- [x] T015 Docs: `research.md` + `quickstart.md` how to re-run when history eligible

## Phase 5 — Polish

- [x] T016 Run `npm run test:python` (or targeted pytest) — all green
- [x] T017 Update `progress.yml` + `checklist-review.md` self-check against FR/SC
- [x] T018 [REVIEW] Speckit review pass; **no** live `SCORE_VERSION` bump on this branch without real GO

## Dependencies

```
T001 → T002/T003 (docs parallel)
T004–T006 → T007 → T008
T009 → T010 → T011
T007 ∥ T009 (after T008 preferred)
T012–T014 after T011 (or parallel with docs T015)
T016 after all impl
```

## Checkpoint policy

Auto-advance phases (Score v3 superspec precedent). Never auto-commit/push.
Never edit live `SCORE_VERSION` / `WEIGHT_*` / `COMPOSITE_THRESHOLD` unless search GO evidence exists on this branch (expected: not yet).
