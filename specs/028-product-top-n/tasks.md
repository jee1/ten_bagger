# Tasks: Product Top-N Candidates + Score Breakdown (Issue #72)

**Input**: `specs/028-product-top-n/` plan + spec + research + contracts
**Prerequisites**: plan.md, spec.md (Brainstormed)

## Phase 1: Setup

- [x] T001 Confirm constitution check PASS in plan; set `progress.yml` `current_phase=execute`
- [x] T002 [P] Add `TOP_N = 5` to `scripts/config.py` (or document constant colocated with helpers)

## Phase 2: Foundational — schema + types (blocking)

- [x] T003 [TDD] Extend `scripts/schema/daily-entry.schema.json` with optional `topCandidates` per `contracts/daily-top-n.md` / `data-model.md`
- [x] T004 Run `npm run gen:types`; update `src/lib/types.ts` so `DailyEntry` / `TopNCandidate` satisfy `_DailyEntrySchemaCheck`
- [x] T005 [TDD] `scripts/tests/test_validate_top_candidates.py` — reject duplicate symbol, bad ranks, pick≠rank1; accept valid list; omit-OK for historical
- [x] T006 Implement semantic checks in `scripts/validate_content.py` (GREEN)
- [x] T007 [REVIEW] Schema + semantic contract match FR-009/017 before pipeline/UI

**Checkpoint**: Foundation ready (schema validates; types compile).

---

## Phase 3: US3 + screening/pipeline (schema honesty + producer) — P1

- [x] T008 [TDD] Screening: all scored eligible retained; sort `(composite DESC, symbol ASC)`; `passed_threshold` counter still accurate
- [x] T009 [TDD] `select_pick(results, threshold)` returns first ≥ threshold or None
- [x] T010 [TDD] `build_top_candidates(results, n=TOP_N)` → list len `min(n,len)` or None if empty
- [x] T011 Implement `screen_market` + helpers (`generate_daily.py` and/or `scripts/top_n.py`)
- [x] T012 [TDD] `test_generate_daily.py`: pick day attaches Top-N with rank1=pick; include below-threshold runners
- [x] T013 [TDD] `test_generate_daily.py`: no_pick with scored below threshold still writes Top-N; zero scored omits field
- [x] T014 Wire `generate_daily.main` to attach `topCandidates` when builder returns list
- [x] T015 Update `walk_forward/pit_screen.py` to use `select_pick` (not raw `results[0]`)
- [x] T016 [P] Adjust `backtest_screen.py` top list to full ranked slice (document in comment)

**Checkpoint**: Producer + validation green; walk-forward pick semantics preserved.

---

## Phase 4: US1 — Day-page Top-N UI (P1)

- [x] T017 [P] [SUBAGENT] Add i18n labels (section title + transparency helper) in `src/lib/i18n.ts`
- [x] T018 [US1] `DailyCard.astro`: collapsed `<details>` Top-N; reuse score labels; no hero card cluster
- [x] T019 [US1] Verify index + `/daily/[date]` both show expand when field present; bilingual

**Checkpoint**: Day page matches US1 acceptance scenarios.

---

## Phase 5: US2 — Archive unchanged (P1)

- [x] T020 Confirm `archive.astro` / `Calendar.astro` unchanged (no Top-N chrome)
- [x] T021 Manual/quick check: archive → day link reaches Top-N disclosure

**Checkpoint**: FR-011 / SC-007 satisfied.

---

## Phase 6: Polish

- [x] T022 `npm run test:python` + `npm run validate:content` + `npm run check` green
- [x] T023 Write `checklist-review.md`; mark tasks; `progress.yml` → review

## Phase 7: Review loop

- [x] T024 [REVIEW] Spec compliance US1–US3 + FR-001–018 + SC-001–008; fix until PASS
- [x] T025 Summary to user (no commit/push unless asked)

## Dependencies

- Phase 2 before 3–5
- Phase 3 before relying on real fixture content in UI (UI can use typed optional field earlier)
- Phase 4 ∥ late Phase 3 after T004 types exist
- Phase 5 after Phase 4 (smoke path)

## Parallel notes

- T017 UI i18n ∥ T008–T014 pipeline once types exist
- T016 backtest comment ∥ T015 pit_screen
