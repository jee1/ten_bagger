---
description: "Task list for walk-forward harness (#66)"
---

# Tasks: Point-in-Time Walk-Forward Harness

**Input**: Design documents from `specs/022-walk-forward-harness/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

## Task Format

```
[ID] [markers] [Story] Description
```

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Schema, paths, npm scripts — no behavioral logic yet.

- [x] T001 Copy `specs/022-walk-forward-harness/contracts/walk-forward-report.schema.json` → `scripts/schema/walk-forward-report.schema.json`
- [x] T002 [P] Add `WALK_FORWARD_DIR`, `WALK_FORWARD_SCHEMA_PATH` to `scripts/config.py`
- [x] T003 [P] Register walk-forward schema in `scripts/validate_content.py` (validate `content/walk-forward/` when dir exists)
- [x] T004 [P] Add schema to `scripts/gen_types.mjs` SCHEMAS array; run `npm run gen:types`
- [x] T005 [P] Add npm scripts to `package.json`: `walk-forward`, `walk-forward:smoke`
- [x] T006 Create package scaffold: `scripts/walk_forward/__init__.py`, stub `scripts/walk_forward.py` with argparse skeleton (`run`, `--config`, exit codes per cli-contract.md)

**Checkpoint**: `python walk_forward.py --help` works; schema file present; gen:types succeeds.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config validation, fold calendar, report serialization — blocks all user stories.

**CRITICAL**: No user story work until this phase completes.

### Tests first

- [x] T007 [TDD] `scripts/tests/test_walk_forward_folds.py` — test `generate_rolling_folds()` returns ≥2 folds for valid spec; fails when <2; train/OOS ranges non-overlapping; `stepSessions` advances calendar
- [x] T008 [TDD] `scripts/tests/test_walk_forward_config.py` — test `load_run_config()` rejects `go_evidence` + `fixture-recompute`; rejects >4 candidates; computes stable `config_hash` (64-char hex, no secrets)

### Implementation

- [x] T009 Implement `scripts/walk_forward/config.py` — `RunConfig` dataclass, JSON loader, validation (FR-021–FR-023, FR-027), `config_hash()` using `sort_keys=True`
- [x] T010 Implement `scripts/walk_forward/folds.py` — `generate_rolling_folds(fold_spec, sessions) -> list[Fold]` using `performance.horizons.trading_sessions`
- [x] T011 [TDD] `scripts/tests/test_walk_forward_report.py` — canonical JSON twice → identical bytes; required top-level fields present
- [x] T012 Implement `scripts/walk_forward/report.py` — `build_report(...)`, `serialize_report()` with deterministic `json.dumps(sort_keys=True, separators=(",", ":"))`
- [x] T013 [REVIEW] Wire CLI `run --dry-run` to validate config + print fold count (no write)

**Checkpoint**: Phase 2 pytest green. Human approval before user stories.

---

## Phase 3: User Story 1 — PIT walk-forward evaluation (P1) 🎯 MVP

**Goal**: Rolling folds with PIT selection at each OOS decision date `t`.  
**Independent Test**: Fixture run yields fold metrics ignoring data after each `t`.

### Tests

- [x] T014 [TDD] [US1] `scripts/tests/test_walk_forward_pit.py` — mock price provider; bars after `t` must not affect pick selection; contaminated fixture fails or proves unused features
- [x] T015 [TDD] [US1] `scripts/tests/test_walk_forward_integration.py` — end-to-end with `fixture-recompute`, 2+ folds, deterministic output

### Implementation

- [x] T016 [US1] Implement `scripts/walk_forward/pit_screen.py` — `pit_screen_day(market, as_of_date, candidate, price_provider) -> pick|no_pick` wrapping `screen_market` with PIT-filtered history injection
- [x] T017 [US1] Implement fold runner in `scripts/walk_forward/runner.py` — iterate OOS sessions, call `pit_screen_day`, collect pick/no_pick counts per fold
- [x] T018 [US1] Handle `skipped_empty_train` when train window has zero scored pick days (FR-025)
- [x] T019 [US1] CLI `run` executes full fold loop (measurement stub returns empty horizons until Phase 4)

**Checkpoint**: US1 integration test passes on fixtures; fold statuses populated.

---

## Phase 4: User Story 2 — Reproducible OOS metrics report (P1)

**Goal**: Machine-readable report with H20/H60, benchmarks, coverage, `insufficient_coverage`.  
**Independent Test**: Open report JSON offline; required fields present.

### Tests

- [x] T020 [TDD] [US2] `scripts/tests/test_walk_forward_aggregate.py` — pick return mean excludes no_pick; hit-rate; excess vs benchmark; `insufficient_coverage` when oosPickDays < 20 and go_evidence
- [x] T021 [TDD] [US2] Extend integration test — report validates against `walk-forward-report.schema.json`; H20 present when picks exist

### Implementation

- [x] T022 [US2] Implement `scripts/walk_forward/ledger_loader.py` — load measurements from `content/performance/` keyed by pickDate+symbol+horizon; fail actionable if missing for go_evidence (FR-016)
- [x] T023 [US2] Implement `scripts/walk_forward/measure.py` — `fixture-recompute` path via `performance.returns.measure_pick_horizon` + fixture price loader; `ledger` path via ledger_loader
- [x] T024 [US2] Implement `scripts/walk_forward/aggregate.py` — per-fold and aggregate horizons (H20 primary, H60 reported), KR-KOSPI/US-SPX benchmark ids
- [x] T025 [US2] Integrate report builder — write to `content/walk-forward/{runId}.json` via `performance.write_atomic.atomic_replace`; CLI human summary
- [x] T026 [US2] Mark `incomplete_horizon` when OOS extends past ledger asOfDate or horizon incomplete (FR-017)

**Checkpoint**: Full fixture report with metrics; schema validation passes.

---

## Phase 5: User Story 3 — Rolling train → OOS (P1)

**Goal**: Explicit train/OOS ranges in report; anchored documented as deferred.  
**Independent Test**: Three-fold fixture shows three distinct OOS segments with labeled ranges.

### Tests

- [x] T027 [TDD] [US3] Test fold report entries include `trainRange` and `oosRange` matching generator output; no shared decision dates between train and OOS (FR-026, FR-027)

### Implementation

- [x] T028 [US3] Ensure `foldSpec.mode` locked to `"rolling"` in v1 config validation
- [x] T029 [US3] [P] Add anchored deferral note to report metadata comment field or document-only (no runnable anchored CLI flag)

**Checkpoint**: US3 acceptance scenarios satisfied on multi-fold fixture.

---

## Phase 6: User Story 4 — PIT assumptions documentation (P2)

**Goal**: Discoverable PIT assumptions without reading source.

- [x] T030 [P] [US4] Create `docs/architecture/pit-walk-forward-assumptions.md` — decision cut, H20/H60 sessions, rolling vs anchored deferral, backtest_screen distinction (FR-009, FR-031)
- [x] T031 [US4] Link from `docs/architecture/README.md` and `specs/022-walk-forward-harness/quickstart.md`

**Checkpoint**: SC-007 satisfied — doc answers cut, horizons, no look-ahead.

---

## Phase 7: User Story 5 — CI smoke fixtures (P2)

**Goal**: Offline smoke catches look-ahead regressions and missing report fields.

### Fixtures

- [x] T032 [P] [US5] Add `scripts/tests/fixtures/walk_forward/smoke-run-config.json` (≤3yr, 2+ folds, fixture-recompute)
- [x] T033 [P] [US5] Add `scripts/tests/fixtures/walk_forward/contaminated-post-t-config.json` + price fixture with post-`t`-only feature column

### Tests

- [x] T034 [TDD] [US5] `scripts/tests/test_walk_forward_smoke.py` — smoke config passes offline; contaminated config fails look-ahead assertion; required report fields asserted (FR-010)

**Checkpoint**: `npm run walk-forward:smoke` green in CI.

---

## Phase 8: Polish & Cross-Cutting

- [x] T035 [P] Support max 4 candidates in config (single run per candidateId for v1 CLI; batch loop documented in quickstart) (FR-014, FR-032)
- [x] T036 [P] Partial market window — only KR or US in config evaluates that market (FR-030)
- [x] T037 [P] Unmatched symbol / delisted — surface incomplete rows from ledger measurements, no silent drop (FR-020)
- [x] T038 [REVIEW] Verify zero diffs to `content/daily/` after harness runs (SC-006)
- [x] T039 Run full suite: `npm run test:python && npm run validate:content`
- [x] T040 Update `specs/022-walk-forward-harness/progress.yml` — plan + tasks done

---

## Dependencies & Execution Order

```text
Phase 1 → Phase 2 (blocks all) → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3)
                                                      ↓
                              Phase 6 (US4) ∥ Phase 7 (US5) → Phase 8
```

- US2 depends on US1 fold runner
- US5 depends on US2 report shape
- US4 can parallelize with US5 after US2

## Parallel Opportunities

| Tasks | Notes |
|-------|-------|
| T002–T005 | Different files, no deps |
| T032–T033 | Fixture files parallel |
| T030 ∥ T034 | Docs vs smoke after US2 |

## Superpowers Execution

### Discipline by Marker

- **[TDD]**: RED → GREEN → refactor; run pytest per task
- **[REVIEW]**: Pause at T013, T038 for human approval
- **[P]**: Safe parallel dispatch
- **[SUBAGENT]**: Phase 3+ implementation tasks may dispatch per file boundary

### Checkpoint Protocol

At each phase boundary: summarize, run pytest subset, ask user to proceed.

---

## Notes

- Do **not** extend `backtest_screen.py` for walk-forward (FR-031)
- `go_evidence` never uses `fixture-recompute` (FR-022)
- Schema source: keep `scripts/schema/` and `specs/.../contracts/` in sync when schema changes
