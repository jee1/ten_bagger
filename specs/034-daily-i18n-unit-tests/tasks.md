# Tasks: Daily / i18n Unit Tests

**GitHub Issue**: #100

## Phase 1: Setup

- [x] T001 Confirm `import('./src/lib/daily.ts')` fails under node with `astro:`; `i18n.ts` imports OK
- [x] T002 [P] Add `test:daily-i18n` script in package.json

**Checkpoint**: auto-continue

## Phase 2: Foundational (extract)

- [x] T003 [TDD] Create `src/lib/dailyDates.ts`
- [x] T004 Update `daily.ts` to re-export helpers; keep async loaders

**Checkpoint**: auto-continue

## Phase 3: US1 + US2 tests

- [x] T005 [TDD] [P] Write `src/lib/dailyDates.test.ts`
- [x] T006 [TDD] [P] Write `src/lib/i18n.test.ts`
- [x] T007 Run `npm run test:daily-i18n` — green (8)

**Checkpoint**: auto-continue

## Phase 4: US3 CI

- [x] T008 Add `npm run test:daily-i18n` to ci.yml after `test:rss`
- [x] T009 Re-run check smoke (`npm run check` 0 errors)

**Checkpoint**: auto-continue

## Phase 5: Polish & Review

- [x] T010 [REVIEW] Spec compliance + simplify
- [x] T011 Update progress.yml; write checklist-review.md

**Checkpoint**: Summary; commit/PR only if asked (`Fixes #100`).
