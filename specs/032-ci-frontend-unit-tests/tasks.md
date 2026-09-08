# Tasks: CI Frontend Unit Tests

**Input**: Design documents from `specs/032-ci-frontend-unit-tests/`
**Prerequisites**: plan.md, spec.md
**GitHub Issue**: #98

## Phase 1: Setup

- [x] T001 Run `npm run test:performance-ui` and `npm run test:rss` locally — both green
- [x] T002 [P] Confirm `.github/workflows/ci.yml` currently has only `npm run check` after `npm ci`

**Checkpoint**: Suites green; gap confirmed. (auto-continue per Speckit procedure)

---

## Phase 2: Foundational

- [x] T003 Document N/A foundational — proceed to US1

**Checkpoint**: Ready for US1. (auto-continue)

---

## Phase 3: User Story 1 - PR CI blocks frontend unit-test regressions (P1) MVP

- [x] T004 [US1] Edit `.github/workflows/ci.yml` Install-and-check to run
  `npm run test:performance-ui` and `npm run test:rss` after `npm run check` via `&&`
- [x] T005 [US1] Re-read workflow: `check` still present; Python/content/audit steps untouched
- [x] T006 [US1] Re-run `npm run test:performance-ui` && `npm run test:rss` locally (parity smoke)

**Checkpoint**: YAML matches FR-001–005; local scripts green. (auto-continue)

---

## Phase 4: User Story 2 - Local/CI same scripts (P2)

- [x] T007 [US2] Verify CI invokes package.json script names only (no inline file lists)
- [x] T008 [P] [US2] Confirm quickstart.md lists the same commands

**Checkpoint**: US2 acceptance satisfied by inspection. (auto-continue)

---

## Phase 5: Polish & Review

- [x] T009 [REVIEW] Spec compliance + simplify check (no extra jobs/steps/scripts)
- [x] T010 Update `progress.yml` phases to done; note verification counts
- [x] T011 Write `checklist-review.md` with verdict

**Checkpoint**: Ready for summary; commit/PR only if user asks (`Fixes #98`).

## Notes

- Local verify 2026-09-08: performance-ui 12 pass; rss 6 pass
- Diff: `.github/workflows/ci.yml` only (+2 lines)
- No commit/push unless explicitly requested
