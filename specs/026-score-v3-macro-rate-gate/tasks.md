---
description: "Task list for Score v3 rate/macro gate (#70)"
---

# Tasks: Score v3 Rate/Macro Gate (Yartseva)

**Input**: Design documents from `specs/026-score-v3-macro-rate-gate/`  
**Prerequisites**: plan.md ✅, spec.md ✅  
**Constitution**: v1.3.0 Principle IV (Score Freeze — no live threshold/size merge)  
**Related**: Issue #70 · Epic #74 Phase 2 · ADR 0004

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` freeze self-check · `[SUBAGENT]` dispatchable

## Execution notes (checkpoints)

> **AUTO-APPROVE ALL PHASE CHECKPOINTS** — parent user directive. Do not wait
> for interactive phase approval. Print one-line summary + continue.
> `[REVIEW]` = freeze/self-check, not a human wait, unless Critical freeze
> violation (then stop).

> **Commits**: Do **not** auto-commit.

---

## Phase 1: Setup

**Purpose**: Scaffold module, fixtures, config constants — no gate logic yet.

- [x] T001 Create `scripts/scoring/macro_rate_gate.py` stub (docstring: Score v3 candidate / default-OFF / Issue #70)
- [x] T002 [P] Create `scripts/tests/fixtures/macro_rate_gate/` and `scripts/data/` if missing
- [x] T003 [P] [SUBAGENT] Author committed `scripts/data/fed_hike_regime.json` (interval or date→bool; documented Fed hiking cycles; enough dates for tests; no secrets)
- [x] T004 [P] Add to `scripts/config.py`: `ENABLE_MACRO_RATE_GATE_CANDIDATE = False`, `THRESHOLD_HIKE_DELTA = 5.0`, `SIZE_TIGHTEN_MIN_MCAP_MULT = 1.5` — do **not** change live `COMPOSITE_THRESHOLD`, `MIN_MARKET_CAP_*`, or `WEIGHT_*`

**Checkpoint (auto-approve)**: Module importable; constants present; regime JSON on disk.

---

## Phase 2: Foundational

**Purpose**: Freeze tests + dataclasses — blocks user stories.

- [x] T005 [TDD] `scripts/tests/test_macro_rate_gate_freeze.py` — `COMPOSITE_THRESHOLD == 70.0`; snapshot live `MIN_MARKET_CAP_KR/US` and `WEIGHT_*`; `ENABLE_MACRO_RATE_GATE_CANDIDATE is False`; deltas match +5.0 / 1.5
- [x] T006 Define dataclasses in `macro_rate_gate.py`: `HikeRegimeSignal`, `GateVariant` literals, `EffectiveSelectionKnobs`

**Checkpoint (auto-approve)**: Freeze tests green; types importable.

---

## Phase 3: User Story 1 — Regime signal (P1) 🎯 MVP

**Goal**: Deterministic Fed hike dummy for date `t` from committed JSON.

### Tests first

- [x] T007 [P] [TDD] [SUBAGENT] [US1] `scripts/tests/test_macro_rate_gate_regime.py` — date inside hike → `hike_regime=true`, `status=available`
- [x] T008 [P] [TDD] [SUBAGENT] [US1] Same file — outside hike → false/available; missing/gap → unavailable fail-open; malformed row hard-fails
- [x] T009 [TDD] [US1] Determinism + KR/US same signal for same `asOfDate`

### Implementation

- [x] T010 [US1] Implement `load_fed_hike_regime` / `resolve_hike_regime(as_of_date: str) -> HikeRegimeSignal`
- [x] T011 [US1] [REVIEW] No network in tests; no live config mutation

**Checkpoint (auto-approve)**: US1 pytest green offline.

---

## Phase 4: User Story 2 — Apply gate variants (P1)

**Goal**: Candidate path applies `threshold_raise` or `size_tighten` when enabled + hike; live defaults unchanged.

### Tests first

- [x] T012 [P] [TDD] [SUBAGENT] [US2] `scripts/tests/test_macro_rate_gate_apply.py` — enabled + hike + `threshold_raise` → effective threshold 75.0; live constant still 70.0
- [x] T013 [P] [TDD] [SUBAGENT] [US2] Same file — `size_tighten` → min caps ×1.5 KR/US; flag OFF / unavailable / non-hike → knobs match baseline
- [x] T014 [TDD] [US2] Both variants named and selectable; composable note (independent of #68/#69 flags)

### Implementation

- [x] T015 [US2] Implement `effective_selection_knobs(*, as_of_date, market, variant, enabled=None) -> EffectiveSelectionKnobs`
- [x] T016 [US2] [REVIEW] Diff audit: live `COMPOSITE_THRESHOLD` / `MIN_MARKET_CAP_*` / `WEIGHT_*` values unchanged in `config.py`

**Checkpoint (auto-approve)**: US2 + freeze tests green.

---

## Phase 5: User Story 3–4 / Polish — Methodology, OOS path, suite

**Goal**: Methodology gated copy; document OOS on/off reuse; full suite green.

- [x] T017 [P] [SUBAGENT] [US3] Update `src/pages/methodology.astro` KO+EN: rate/macro gate candidate, Fed dummy, KR=global Fed / BOK deferred, measurement-gated, Issue #70
- [x] T018 [P] [US3] Write `specs/026-score-v3-macro-rate-gate/quickstart.md` + `contracts/macro-rate-gate.md` (API + GO/NO-GO/wontfix via #66/#67)
- [x] T019 [US3] Run `npm run test:python` — all green
- [x] T020 [REVIEW] [US3] Final freeze + Methodology self-review; stop only on Critical freeze violation

**Checkpoint (auto-approve)**: Suite green; Methodology present; ready for review.

---

## Dependencies & Execution Order

- Phase 1 → 2 → 3 → 4 → 5 (sequential phases)
- Within phase: `[P]` tasks parallel; TDD tests before matching implementation
- US1 before US2 apply (needs regime resolver)

## Parallel opportunities

| Parallel group | Tasks |
|----------------|-------|
| Setup | T002, T003, T004 |
| US1 tests | T007, T008 |
| US2 tests | T012, T013 |
| Polish | T017, T018 |
