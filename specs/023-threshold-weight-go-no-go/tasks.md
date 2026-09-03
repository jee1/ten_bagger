---
description: "Task list for threshold·weight GO/NO-GO recalibration (#67)"
---

# Tasks: Threshold·Weight GO/NO-GO Recalibration

**Input**: Design documents from `specs/023-threshold-weight-go-no-go/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅  
**Constitution**: v1.1.0 Principle IV (IS-only search; OOS GO/NO-GO; no live config writes)

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` human gate · `[SUBAGENT]` dispatchable

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Schema, paths, npm scripts, package scaffold — no calibration logic yet.

- [x] T001 Copy `specs/023-threshold-weight-go-no-go/contracts/calibration-report.schema.json` → `scripts/schema/calibration-report.schema.json`
- [x] T002 [P] Add `CALIBRATION_DIR`, `CALIBRATION_SCHEMA_PATH` to `scripts/config.py` (alongside existing `WALK_FORWARD_*`)
- [x] T003 [P] Register calibration schema in `scripts/validate_content.py` (validate `content/calibration/` when dir exists)
- [x] T004 [P] Add `calibration-report.schema.json` to `scripts/gen_types.mjs` SCHEMAS; run `npm run gen:types`
- [x] T005 [P] Add npm scripts to `package.json`: `calibrate`, `calibrate:smoke`
- [x] T006 Create package scaffold: `scripts/calibration/__init__.py` and stub `scripts/calibrate.py` argparse (`run`, `--config`, `--json-only`, `--dry-run`, exit codes 0/1/2/3 per `contracts/cli-contract.md`)
- [x] T007 [P] [SUBAGENT] Create fixture dirs `scripts/tests/fixtures/calibration/` with placeholder JSON stubs listed in `quickstart.md` (smoke-search, baseline-only, invalid-weight-sum, overlapping-is-oos)

**Checkpoint**: `python calibrate.py --help` works; schema present; `gen:types` succeeds.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Candidate validation, calibration config, analysis-only WF overrides, report serialization — blocks all user stories.

**CRITICAL**: No user story work until this phase completes.

### Tests first

- [x] T008 [TDD] `scripts/tests/test_calibration_candidates.py` — accept valid top-level weight vector summing to `1.0±1e-6`; reject sum outside tolerance; reject unknown/nested keys; reject `>10` candidates (FR-012, FR-021, FR-024)
- [x] T009 [TDD] `scripts/tests/test_calibration_config.py` — `load_calibration_config()` rejects IS/OOS decision-date overlap for `go_evidence`; rejects `go_evidence` + non-ledger OOS; accepts `mode=baseline-only`; rejects `>10` candidates before evaluation
- [x] T010 [TDD] Update `scripts/tests/test_walk_forward_config.py` — **remove** blanket reject of `weightOverrides`; accept valid overrides + optional `thresholdOverride`; still reject `go_evidence`+`fixture-recompute`; include overrides in `config_hash`

### Implementation

- [x] T011 Implement `scripts/calibration/candidates.py` — `WeightVector` / `CandidateSpec` validation helpers used by config loader
- [x] T012 Implement `scripts/calibration/config.py` — `CalibrationRunConfig`, JSON loader, `config_hash()` (`sort_keys=True`, no secrets), IS/OOS disjoint check (FR-002, FR-024, FR-025, FR-032)
- [x] T013 [TDD] `scripts/tests/test_calibration_overrides.py` — context manager sets `screening.core.COMPOSITE_THRESHOLD` and `scoring.composite.WEIGHT_*`; after exit, live module values restored; `config.COMPOSITE_THRESHOLD` file constants unchanged
- [x] T014 Implement `scripts/calibration/overrides.py` — `apply_candidate_overrides(threshold, weights)` context manager
- [x] T015 [REVIEW] Extend `scripts/walk_forward/config.py` to allow analysis `thresholdOverride` / `weightOverrides` (validated sum/keys); update `config_hash` payload
- [x] T016 Extend `scripts/walk_forward/pit_screen.py` — accept optional overrides and apply via `calibration.overrides` (or shared helper) inside `pit_screen_day`
- [x] T017 [TDD] `scripts/tests/test_calibration_report.py` — `serialize_report` twice → identical bytes; required top-level fields per schema
- [x] T018 Implement `scripts/calibration/report.py` — `build_report(...)`, `serialize_report()` with `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
- [x] T019 Wire CLI `run --dry-run` to validate calibration config + print candidate count / fold specs (no evaluate, no write)

**Checkpoint**: Phase 2 pytest green; WF override tests updated; human approval before user stories.

---

## Phase 3: User Story 1 — IS candidate sweep (P1) 🎯 MVP

**Goal**: Rank ≤10 threshold/weight candidates on IS-only walk-forward metrics; live constants unchanged.  
**Independent Test**: Fixed grid + IS calendar → ranked list citing only IS metrics.

### Tests

- [x] T020 [TDD] [US1] `scripts/tests/test_calibration_is_rank.py` — rank by IS H20 excess desc, tie-break `isPickDays` then `candidateId`; OOS fold spec unused for ordering; invalid candidates status `rejected_invalid` and excluded from ranking
- [x] T021 [TDD] [US1] Integration: exploratory `mode=search` on fixtures produces `isRanking` length matching valid candidates; `config.py` threshold/weights unmodified after run

### Implementation

- [x] T022 [US1] Implement `scripts/calibration/is_rank.py` — for each candidate, invoke walk-forward programmatically with IS `foldSpec`, `runIntent=exploratory`, candidate overrides; collect metrics; sort deterministically (research R6)
- [x] T023 [US1] Implement promote selection (`promoteTopN`, default 1) recording `selectionRationale` string
- [x] T024 [US1] Ensure default fixture grid includes baseline + threshold **> 70** + ≥1 alternate weight vector (FR-019, FR-022)
- [x] T025 [US1] CLI `run` with `mode=search` + `packageIntent=exploratory` executes IS ranking and writes partial/full report path (OOS may be skipped or stubbed until Phase 4)

**Checkpoint**: US1 tests pass; IS ranking deterministic on fixtures.

---

## Phase 4: User Story 2 — OOS GO/NO-GO (P1)

**Goal**: Evaluate selected candidates on walk-forward OOS; emit per-candidate and overall GO/NO-GO.  
**Independent Test**: Feed IS winner into `go_evidence` path; read verdict offline.

### Tests

- [x] T026 [TDD] [US2] `scripts/tests/test_calibration_verdict.py` — GO when H20 excess > 0, oosPickDays ≥ 20, no contamination, complete; NO-GO on insufficient coverage; NO-GO on H20 excess ≤ 0; `no_pick` ratio alone does not force NO-GO; incomplete required set → no overall GO (FR-004–FR-005, FR-023, FR-030)
- [x] T027 [TDD] [US2] Integration: `packageIntent=go_evidence` + ledger/fixture policy — missing ledger fails closed with regenerate hint (FR-016, FR-026); exit code `3` when overall NO-GO

### Implementation

- [x] T028 [US2] Implement `scripts/calibration/verdict.py` — pure functions `verdict_from_oos_report(report, *, package_intent) -> OosEvaluationEntry` and `overall_verdict(entries, *, incomplete) -> (GO|NO-GO|N/A, failedBullets)`
- [x] T029 [US2] Implement OOS evaluation loop in `scripts/calibration/runner.py` — for promotees (or baseline), run walk-forward with `oosFoldSpec`, `runIntent=go_evidence`, `measurementSource=ledger` when required; attach paths/hashes
- [x] T030 [US2] [REVIEW] Map walk-forward aggregate fields → calibration OOS entry (`h20ExcessReturnMean`, `noPickRatio`, `insufficientCoverage`, contaminationFindings)
- [x] T031 [US2] Forbid treating `backtest_screen` as GO evidence (no import/call path in runner)

**Checkpoint**: US2 verdict tests + go_evidence fail-closed path green.

---

## Phase 5: User Story 3 — Calibration report & merge criteria (P1)

**Goal**: Reproducible calibration report + written merge criteria for reviewers.  
**Independent Test**: Open report + merge-criteria doc; required fields without reading code.

### Tests

- [x] T032 [TDD] [US3] Report validates against `scripts/schema/calibration-report.schema.json`; includes `packageIntent`, `isRanking`, `oosEvaluations`, `overallVerdict`, `mergeCriteriaRef`, `liveConstantsSnapshot` (FR-007, FR-032, SC-008)
- [x] T033 [TDD] [US3] Identical inputs → bit-identical serialized report (FR-013, SC-006)

### Implementation

- [x] T034 [US3] Finalize `runner.py` write path — atomic write to `content/calibration/{runId}.json` (reuse `performance.write_atomic` pattern if present); human summary when not `--json-only`
- [x] T035 [P] [SUBAGENT] [US3] Create `docs/architecture/threshold-weight-merge-criteria.md` from `contracts/merge-criteria.md` (FR-008, FR-031)
- [x] T036 [US3] Link merge-criteria from `docs/architecture/README.md`; set report `mergeCriteriaRef` to that path
- [x] T037 [US3] Soft-doc threshold ↔ `no_pick` tradeoff in merge-criteria (not a hard GO bullet)

**Checkpoint**: Schema validation passes on fixture GO package; docs discoverable.

---

## Phase 6: User Story 4 — Live config only after GO (P1)

**Goal**: Tooling never mutates live constants; NO-GO implies no config PR; GO prints human PR checklist only.  
**Independent Test**: NO-GO run leaves `config.py` unchanged; GO run still does not edit `config.py`.

### Tests

- [x] T038 [TDD] [US4] After full `calibrate.py run`, assert `scripts/config.py` bytes (or `COMPOSITE_THRESHOLD` / `WEIGHT_*` imports) unchanged (FR-009, FR-010, SC-005)
- [x] T039 [TDD] [US4] CLI stdout on GO includes explicit “do not auto-edit; open PR linking report” checklist; on NO-GO does not suggest editing weights/threshold

### Implementation

- [x] T040 [US4] Implement PR-hint printer in CLI (no file writes to `config.py`); ensure no code path calls write/open on `config.py` for mutation
- [x] T041 [US4] `baseline-only` mode emits GO/NO-GO for frozen constants but messaging states it does **not** authorize config change (FR-025)
- [x] T042 [US4] Exit code `3` for completed `go_evidence` with overall NO-GO; exit `0` for exploratory even if candidates are weak (cli-contract)

**Checkpoint**: Freeze guarantees covered by tests; human approval.

---

## Phase 7: User Story 5 — Depend on walk-forward harness (P2)

**Goal**: Reuse #66 harness/report contract; fail closed if missing/unusable.  
**Independent Test**: OOS path consumes WF reports; missing harness guidance error.

### Tests

- [x] T043 [TDD] [US5] If walk-forward import/run fails, calibration raises actionable error mentioning `npm run walk-forward` / harness — never falls back to `backtest_screen` (FR-026)

### Implementation

- [x] T044 [US5] Keep single integration surface: programmatic call into `walk_forward` runner/execute APIs (not subprocess-required for tests)
- [x] T045 [P] [US5] Document dependency on #66 in `quickstart.md` and architecture README pointer already added in T036

**Checkpoint**: US5 acceptance scenarios satisfied.

---

## Phase 8: Polish & Cross-Cutting

**Purpose**: Smoke suite, CI discoverability, freeze audit.

- [x] T046 [TDD] `scripts/tests/test_calibration_smoke.py` — offline: search smoke, invalid weight, overlapping IS/OOS, determinism; no network
- [x] T047 Wire `npm run calibrate:smoke` to that file; ensure included in or documented beside `npm run test:python`
- [x] T048 [P] [SUBAGENT] Author real fixture configs under `scripts/tests/fixtures/calibration/` (replace stubs) reusing walk_forward price/ledger snippets where possible
- [x] T049 [P] Run `npm run validate:content` against sample calibration JSON in fixtures or temp content dir
- [x] T050 [REVIEW] Full suite: `npm run test:python` + `calibrate:smoke` + confirm no live Score/threshold drift in diff
- [x] T051 [P] Update `specs/023-threshold-weight-go-no-go/progress.yml` notes when execute completes (leave for execute phase)

**Checkpoint**: Smoke green offline; ready for `/speckit.superspec.review` after execute.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: start immediately
- **Phase 2 Foundational**: depends on Setup — **BLOCKS** all user stories
- **Phase 3 US1**: depends on Foundational (MVP)
- **Phase 4 US2**: depends on US1 promote/selection outputs (can stub promote list in tests)
- **Phase 5 US3**: depends on US1+US2 report fields
- **Phase 6 US4**: depends on CLI runner from US3
- **Phase 7 US5**: can largely proceed in parallel with US4 after US2 runner exists
- **Phase 8 Polish**: after US1–US5 desired scope complete

### Within Stories

1. `[TDD]` tests MUST fail before implementation  
2. Validation helpers before loaders; overrides before PIT wiring  
3. Verdict pure functions before runner integration  
4. `[REVIEW]` pauses before consumers pile on  

### Parallel Opportunities

- T002–T005, T007 after T001  
- T035, T048 documentation/fixtures as `[SUBAGENT]`  
- US5 docs (T045) parallel with US4 implementation  

---

## Superpowers Execution

### Execution Discipline by Marker

- **[TDD]**: RED-GREEN-REFACTOR via `test-driven-development` skill when available  
- **[SUBAGENT]**: Dispatch via `subagent-driven-development` when available  
- **[REVIEW]**: Pause for explicit human approval  
- **[P]**: Parallelize with Task tool when no shared-file conflicts  

### Checkpoint Protocol

At every phase boundary:
1. Summarize completed tasks  
2. Run applicable pytest / smoke  
3. Ask: “Phase N complete. Proceed to Phase N+1?”  
4. Continue only after explicit approval  

### Freeze Rule (all phases)

Never commit changes that alter live `COMPOSITE_THRESHOLD` or top-level `WEIGHT_*` in `scripts/config.py` as part of this feature’s implementation PR. Those belong only in a post-GO config PR.

---

## Spec Coverage Map (self-review)

| Spec area | Tasks |
|-----------|-------|
| FR-001–002, FR-019–022, FR-024 IS search | T008–T012, T020–T025 |
| FR-003–006, FR-023, FR-030 OOS GO/NO-GO | T026–T031 |
| FR-007–008, FR-013, FR-031–032 report/docs | T017–T018, T032–T037 |
| FR-009–011, FR-025 freeze / baseline-only | T038–T042 |
| FR-012, FR-021 validation | T008, T011 |
| FR-014 no Optuna | implied by fixed grid fixtures T024 |
| FR-016, FR-026, FR-029 harness/ledger fail-closed | T027, T043–T044 |
| FR-017 no backtest_screen GO | T031, T043 |
| FR-018 / FR-032 packageIntent | T009, T032 |
| FR-027 no secrets | T012 config_hash |
| FR-028 single-thread | runner sequential (T022, T029) |
| US5 #66 dependency | T043–T045 |
| SC-001–SC-010 | covered by US1–US4 tests + smoke T046 |

**Placeholder scan**: none intentional.  
**Further task breakdown needed**: No — ready for `/speckit.superspec.execute`.
