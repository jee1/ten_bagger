# Tasks: Data dual-source (Issue #71)

**Input**: `specs/027-data-dual-source/` plan + spec
**Prerequisites**: plan.md, spec.md (Brainstormed)

## Phase 1: Setup

- [x] T001 Confirm constitution check PASS in plan; set progress.yml `current_phase=execute`
- [x] T002 [P] Add `scripts/stooq_prices.py` stub module docstring + public API names

## Phase 2: Foundational (TDD)

- [x] T003 [TDD] `test_stooq_prices.py`: symbol map US / KR / passthrough
- [x] T004 [TDD] Parse sample Stooq CSV → OHLCV DataFrame (Close required)
- [x] T005 Implement mapper + CSV parse in `stooq_prices.py` (GREEN)
- [x] T006 [TDD] `fetch_history` uses injectable urlopen; empty/malformed → None/raise policy

## Phase 3: US2 Cascade (P1)

- [x] T007 [TDD] Primary fail + no stale → Stooq success returns hist; log provider=stooq
- [x] T008 [TDD] Primary fail + no stale + Stooq fail → raises
- [x] T009 [TDD] Primary fail + stale present → stale returned **before** Stooq called
- [x] T010 [TDD] Primary returns empty DataFrame → treated as miss → Stooq path
- [x] T011 Wire cascade in `yf_cache.get_ticker_history`; provider-keyed Stooq cache write
- [x] T012 [REVIEW] Confirm `get_ticker_info` unchanged

## Phase 4: US1 ADR (P1) ∥ docs

- [x] T013 [P] [SUBAGENT] Write `docs/architecture/adr/0005-data-dual-source.md`
- [x] T014 [P] Link ADR 0005 from `docs/architecture/README.md`; note ADR 0003 follow-up done
- [x] T015 Touch `docs/architecture/arc42.md` single-provider line → dual-source ADR ref

## Phase 5: US3 polish

- [x] T016 ADR records DART evaluate-and-defer + triggers (FR-010)
- [x] T017 Run `npm run test:python` — all green including prior stale tests
- [x] T018 Write `checklist-review.md`; mark tasks complete; progress → review

## Phase 6: Review loop

- [x] T019 [REVIEW] Spec compliance US1–US3 + FR-001–014; fix until PASS
- [x] T020 Summary report to user (no commit unless asked)
