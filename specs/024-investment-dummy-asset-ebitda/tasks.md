---
description: "Task list for Score v3 investment dummy (#68)"
---

# Tasks: Score v3 Investment Dummy (Asset Growth vs EBITDA)

**Input**: Design documents from `specs/024-investment-dummy-asset-ebitda/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅  
**Constitution**: v1.1.0 Principle IV (Score Freeze — no live weight/threshold merge)  
**Related**: Issue #68 · Epic #74 Phase 2 · ADR 0004

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` human gate · `[SUBAGENT]` dispatchable

## Execution notes (checkpoints)

> **AUTO-APPROVE ALL PHASE CHECKPOINTS** — parent user directive. Execute agents
> MUST NOT wait for interactive “Proceed to Phase N+1?” approval. At each phase
> boundary: print a one-line summary + test result, then continue immediately.
> Still honor `[REVIEW]` as a freeze/self-check (diff audit), not a human wait,
> unless a Critical freeze violation is found (then stop).

> **Commits**: Do **not** auto-commit. Optional polish only if a human later asks.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold module path, fixture dir, and config constant placeholders — no metric logic yet.

- [x] T001 Create `scripts/scoring/investment_dummy.py` stub exporting module docstring stating Score v3 candidate / default-OFF / not `passes_red_flags`
- [x] T002 [P] Create `scripts/tests/fixtures/investment_dummy/` directory
- [x] T003 [P] [SUBAGENT] Author fixture JSON stubs listed in `quickstart.md` (`hit_dummy`, `no_hit`, `equal_growth`, `both_negative_hit`, `unavailable_neg_ebitda`, `unavailable_zero_prior_assets`) with prior/current assets & EBITDA fields
- [x] T004 [P] Add `INVESTMENT_DUMMY_SOFT_PENALTY = 15.0` and `ENABLE_INVESTMENT_DUMMY_CANDIDATE = False` to `scripts/config.py` (do **not** change `COMPOSITE_THRESHOLD` or any `WEIGHT_*`)

**Checkpoint (auto-approve)**: Module importable; config constants present; fixtures on disk.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Metric/adjustment API shapes and freeze assertions scaffolding — blocks US work.

**CRITICAL**: No user-story implementation until this phase completes.

- [x] T005 [TDD] `scripts/tests/test_investment_dummy_freeze.py` — assert `COMPOSITE_THRESHOLD == 70.0`; import all live `WEIGHT_*` and snapshot values; assert `ENABLE_INVESTMENT_DUMMY_CANDIDATE is False`; assert `INVESTMENT_DUMMY_SOFT_PENALTY >= 15.0`
- [x] T006 [TDD] Same freeze file (or sibling) — existing `passes_red_flags` cases still pass/fail as today (negative equity, dual CF, clean); confirm function source has no `investment_dummy` branch (grep/ast or behavioral only)
- [x] T007 Define dataclasses / TypedDicts in `investment_dummy.py` matching [data-model.md](./data-model.md): `InvestmentDummyMetric`, `CandidateAdjustment` (fields only; compute may still raise `NotImplementedError` until US1/US2)

**Checkpoint (auto-approve)**: Freeze tests green; types importable.

---

## Phase 3: User Story 1 — Compute investment-dummy metric (P1) 🎯 MVP

**Goal**: Deterministic YoY assets vs EBITDA metric with unavailable neutrality.  
**Independent Test**: Fixture fundamentals → growths, spread, boolean, status offline.

### Tests first

- [x] T008 [P] [TDD] [SUBAGENT] [US1] `scripts/tests/test_investment_dummy_metric.py` — available hit: `asset_growth_pct > ebitda_growth_pct` → `investment_dummy=true`, `spread_pct` = asset − ebitda (FR-001, FR-002, FR-010)
- [x] T009 [P] [TDD] [SUBAGENT] [US1] Same file — non-hit and equal growth → `investment_dummy=false`; both-negative growth still can hit when asset > ebitda (edge 2–3)
- [x] T010 [P] [TDD] [SUBAGENT] [US1] Same file — unavailable: missing fields, zero prior assets, zero/negative EBITDA either period → `status=unavailable`, no silent zero growth (FR-005, SC-007)
- [x] T011 [TDD] [US1] Determinism: same inputs twice → identical metric dict/dataclass

### Implementation

- [x] T012 [US1] Implement `compute_investment_dummy_metric(...)` per [contracts/investment-dummy-metric.md](./contracts/investment-dummy-metric.md) and research R5 (`abs(prior)` growth formula)
- [x] T013 [US1] Optional thin helper `extract_period_fundamentals_from_statement_dicts(...)` mapping two annual columns → four floats or unavailable — **not** called from live daily path (research R1); unit-test with dict fixtures only if implemented
- [x] T014 [US1] [REVIEW] Self-check: no edits to `passes_red_flags`, `COMPOSITE_THRESHOLD`, or `WEIGHT_*` values in this phase

**Checkpoint (auto-approve)**: US1 pytest green offline.

---

## Phase 4: User Story 2 — Soft penalty + label, live default OFF (P1)

**Goal**: Candidate path applies soft penalty ≥ 15 + visible label when enabled & dummy fires; live defaults unchanged.  
**Independent Test**: Same ScoreResult fixture with flag on/off and dummy true/false.

### Tests first

- [x] T015 [P] [TDD] [SUBAGENT] [US2] `scripts/tests/test_investment_dummy_penalty.py` — enabled + dummy true → `applied=true`, penalty `== INVESTMENT_DUMMY_SOFT_PENALTY`, label `investment_dummy`, composite reduced (FR-003, SC-002)
- [x] T016 [P] [TDD] [SUBAGENT] [US2] Same file — enabled + dummy false / unavailable → no penalty, no label; flag OFF → no penalty even if dummy would hit (FR-004, FR-013, SC-008)
- [x] T017 [TDD] [US2] Additive smoke: existing hard red-flag info still fails `passes_red_flags` independently; investment-dummy apply does not call/patch `passes_red_flags` (FR-011)

### Implementation

- [x] T018 [US2] Implement `apply_investment_dummy_adjustment(result, metric, *, enabled=None)` defaulting `enabled` to `ENABLE_INVESTMENT_DUMMY_CANDIDATE`; write metrics keys + `red_flag_labels`
- [x] T019 [US2] Optional candidate-only hook helper (e.g. `maybe_apply_investment_dummy(result, period_inputs)`) — ensure `screening.core.score_symbol` / `generate_daily` do **not** enable by default
- [x] T020 [P] [US2] Optional: if reasoning is touched, append bilingual risk/label only when metrics show applied investment dummy — do not alter live pick copy otherwise
- [x] T021 [US2] [REVIEW] Diff audit: `passes_red_flags` body unchanged for this factor; live weight/threshold constants unchanged

**Checkpoint (auto-approve)**: US2 penalty tests + freeze tests green.

---

## Phase 5: User Story 3 / Polish — Tests suite, Methodology, traceability (P1)

**Goal**: Full python suite includes factor tests; Methodology bilingual gated-candidate section; #68/#74 measurement-gated wording.  
**Independent Test**: `npm run test:python`; open Methodology KR+EN.

- [x] T022 [P] [SUBAGENT] [US3] Update `src/pages/methodology.astro` — KO section: Score v3 후보 / 측정 게이트 / Yartseva asset vs EBITDA / soft penalty+label / ADR 0004 GO / no sector carve-out note; **not** inside live v2 weight `%` list (FR-007, FR-012, SC-005)
- [x] T023 [P] [SUBAGENT] [US3] Same file EN parallel copy with gated-candidate wording (FR-007)
- [x] T024 [P] [US3] Confirm `specs/024-investment-dummy-asset-ebitda/spec.md` / plan link Issue #68 and Epic #74; add one-line pointer in Methodology or spec notes if missing (FR-008, SC-006)
- [x] T025 [US3] Run `npm run test:python` — all new + existing tests green (SC-004)
- [x] T026 [P] [US3] Spot-check: `ENABLE_INVESTMENT_DUMMY_CANDIDATE is False` and no `content/daily` rewrites in the feature diff (FR-014)
- [x] T027 [REVIEW] [US3] Final freeze + Methodology wording self-review against SC-003/SC-005; stop only if Critical freeze violation

**Checkpoint (auto-approve)**: Suite green; Methodology gated section present; ready for `/speckit.superspec.review` after execute.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: start immediately
- **Phase 2 Foundational**: depends on Setup — **BLOCKS** US1–US3
- **Phase 3 US1**: depends on Foundational (MVP metric)
- **Phase 4 US2**: depends on US1 metric API
- **Phase 5 US3/Polish**: Methodology can start `[P][SUBAGENT]` once Foundational config names are stable; full suite gate after US1+US2

### Within Stories

1. `[TDD]` tests MUST fail before implementation  
2. Metric before penalty apply  
3. Flag default OFF before any optional hook  
4. `[REVIEW]` = freeze/self-check (no human wait per auto-approve note)

### Parallel Opportunities

- T002–T004 after T001  
- T008–T010 parallel `[SUBAGENT]` after Foundational  
- T015–T016 parallel after T012  
- T022–T023 Methodology parallel with US2 implementation (different files) after T004  

---

## Superpowers Execution

### Execution Discipline by Marker

- **[TDD]**: RED-GREEN-REFACTOR via `test-driven-development` skill when available  
- **[SUBAGENT]**: Dispatch via `subagent-driven-development` when available  
- **[REVIEW]**: Freeze/Methodology self-audit; do **not** block on human unless Critical freeze breach  
- **[P]**: Parallelize when no shared-file conflicts  

### Checkpoint Protocol (modified)

At every phase boundary:
1. Summarize completed tasks (one short paragraph)  
2. Run applicable pytest  
3. **Auto-approve** and continue to next phase (parent directive)  
4. Do not ask “Proceed to Phase N+1?”

### Freeze Rule (all phases)

Never change live `COMPOSITE_THRESHOLD` or top-level `WEIGHT_*` values. Never
add investment-dummy to `passes_red_flags`. Live weight merge requires separate
ADR 0004 GO PR outside this feature.

---

## Spec Coverage Map (self-review)

| Spec area | Tasks |
|-----------|-------|
| FR-001, FR-002, FR-010 metric | T008–T013 |
| FR-005, SC-007 unavailable | T010, T012 |
| FR-003, FR-011 soft penalty + label additive | T015–T018, T017 |
| FR-004, FR-013, SC-008 flag default OFF | T004, T016, T019, T005 |
| FR-006, SC-004 tests | T008–T011, T015–T017, T025 |
| FR-007, FR-012, SC-005 Methodology | T022–T023 |
| FR-008, SC-006 #68/#74 | T024 |
| FR-009 PIT | research + T013 docstring; fixture-only tests |
| FR-014 no daily rewrite | T026 |
| SC-001–SC-003 freeze / hit | T005–T006, T014, T021, T027 |
| Q1–Q5 locked | plan + research; tasks enforce |

**Placeholder scan**: none intentional.  
**NEEDS CLARIFICATION**: none.
