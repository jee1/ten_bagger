# Tasks: Product RSS Digest

**Input**: Design documents from `specs/029-product-rss-digest/`
**Prerequisites**: plan.md, spec.md, research.md, contracts/rss-feed.md
**GitHub**: Issue #73 | Epic #74 Phase 4

## Phase 1: Setup

- [x] T001 Install `@astrojs/rss` and add `test:rss` script to `package.json`
- [x] T002 [P] Confirm `SPECIFY_FEATURE` / feature.json point at `029-product-rss-digest`

**Checkpoint**: Dependency present; scripts listed.

---

## Phase 2: Foundational

- [x] T003 [TDD] Create failing tests in `src/lib/rss.test.ts` for window=30, pick/no_pick wording, bilingual fields, link join with base
- [x] T004 [TDD] Implement `src/lib/rss.ts` mapper until tests pass

**Checkpoint**: `npm run test:rss` green.

---

## Phase 3: User Story 1 — Subscribe via feed (P1) MVP

**Goal**: Public RSS 2.0 at `{base}rss.xml`
**Independent Test**: Build/dev serves feed; validator-friendly XML; pick items link to daily pages

- [x] T005 [US1] Add `src/pages/rss.xml.ts` GET using `@astrojs/rss` + mapper + daily loaders
- [x] T006 [P] [US1] Optional: `<link rel="alternate" type="application/rss+xml">` in `src/layouts/Layout.astro`
- [x] T007 [US1] Smoke: `npm run build` produces `rss.xml` under dist base

**Checkpoint**: US1 independent test passes.

---

## Phase 4: User Story 2 — README subscribe instructions (P1)

**Goal**: README documents feed URL + reader steps with base path
**Independent Test**: README section exists; URL matches deployed path pattern

- [x] T008 [P] [SUBAGENT] [US2] Add README subscription section (KR+EN brief) with `{base}rss.xml`

**Checkpoint**: SC-003 satisfied.

---

## Phase 5: User Story 3 — Honest thin days (P2)

**Goal**: no_pick included; cap enforced; no email/secrets
**Independent Test**: Covered by T003/T004 + review that no ESP added

- [x] T009 [US3] Confirm mapper tests cover no_pick + empty list; grep ensures no email/ESP code paths in change set

**Checkpoint**: US3 acceptance met by tests + review.

---

## Phase 6: Polish

- [x] T010 [P] Run `npm run check`
- [x] T011 Update `progress.yml`; prepare for superspec.review

---

## Dependencies

- Setup → Foundational → US1 → (US2 ∥ US3 polish) → Polish
- T004 blocks T005
- T008 parallel with T005–T007 after T004

## Parallel opportunities

- After T004: T005+T007 vs T008
- T006 with T005

## Task count: 11
