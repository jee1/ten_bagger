# Tasks: PIT asOfDate Session-Closed Flag

**Input**: Design documents from `specs/033-pit-asofdate-session-closed/`
**Prerequisites**: plan.md, spec.md
**GitHub Issue**: #99

## Phase 1: Setup

- [x] T001 Update `.specify/feature.json` + `progress.yml` for 033; confirm constitution unrevised

## Phase 2: Foundational (TDD core)

- [x] T002 [TDD] [US1] Add failing tests: `as_of_session_closed` True/False on as-of bar; assert no reliance on host today (inject as_of == real today with True still includes)
- [x] T003 [TDD] [US2] Add failing tests for `infer_as_of_session_closed` KR before/after 15:30 KST and historical as_of
- [x] T004 [TDD] [US1] Implement `filter_session_bars(..., *, as_of_session_closed=True)`; remove `date.today()`; ponytail upgrade comment
- [x] T005 [TDD] [US2] Implement `infer_as_of_session_closed` in `pit_prices.py`

## Phase 3: User Story 3 — call sites / docs

- [x] T006 [US3] Wire `prices_live.fetch_live_bars` to infer / explicit flag
- [x] T007 [P] [US3] One-line update in `docs/architecture/pit-walk-forward-assumptions.md` for closed-session cut
- [x] T008 [REVIEW] Run `pytest` for pit/session + look-ahead subset; mark tasks done

## Phase 4: Polish

- [x] T009 Write `checklist-review.md` after superspec.review

## Dependencies

- T002/T003 before T004/T005
- T004/T005 before T006
- T008 after T006–T007

## Parallel opportunities

- T007 parallel with T006 after core green
