# Tasks: Fix Static Navigation and Publish Verifiable Performance

**Input**: Design documents from `specs/031-static-nav-verifiable-perf/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md
**GitHub**: Issue #94
**Branch**: `feature/fix-static-navigation-and-publish-verifiable-per`

## Phase 1: Setup

- [x] T001 Confirm `SPECIFY_FEATURE` / `.specify/feature.json` → `031-static-nav-verifiable-perf`
- [x] T002 [P] Inventory pages using `Astro.url.searchParams` (index, archive, performance, methodology, daily)

**Checkpoint**: Feature pointer set; inventory noted in progress notes.

---

## Phase 2: Foundational

- [x] T003 [TDD] Add `src/lib/staticNav.test.ts` — parse `lang` / `year` / `month` / `market` from query string; defaults; invalid→default
- [x] T004 [TDD] Implement `src/lib/staticNav.ts` until tests pass
- [x] T005 [TDD] Extend performance view-model tests for `priceAdjustment`, `priceBasisValidation=incomplete`, labeling kind
- [x] T006 [TDD] Update `src/lib/performanceAggregate.ts` (+ load path if needed) to pass `runMeta` fields into view model

**Checkpoint**: Node tests for staticNav + aggregate green.

---

## Phase 3: User Story 1 — Language & archive controls (P1) MVP

**Goal**: Visible lang + archive month match query on static host; no 390px overflow
**Independent Test**: `astro build` + preview with `?lang=en` and prior month

- [x] T007 [US1] [SUBAGENT] Add client hydrate script/module that applies `lang` to `document.documentElement` + `[data-i18n]` / dual-language nodes on Layout + primary pages
- [x] T008 [US1] Embed bilingual strings (or dual DOM) so hydrate can switch without rebuild
- [x] T009 [US1] Archive: embed month datasets or client-filter calendar; month nav updates visible month from query
- [x] T010 [US1] Fix `.calendar` CSS (`table-layout: fixed`, min-width/padding) for 390px
- [x] T011 [US1] Smoke: build + preview SC-001–SC-003

**Checkpoint**: US1 independent test passes.

---

## Phase 4: User Story 2 — Performance market + Pages publish (P1)

**Goal**: KR/US switch works statically; ledger updates reach Pages
**Independent Test**: preview `?market=US`; ledger.yml contains deploy job

- [x] T012 [P] [US2] [SUBAGENT] Performance page embeds both market views; hydrate switches on `?market=`
- [x] T013 [US2] Ensure as-of, horizon sample counts, unavailable reasons remain visible after hydrate
- [x] T014 [P] [US2] [SUBAGENT] Extend `.github/workflows/ledger.yml` with Pages build/deploy after successful content push (mirror daily.yml; need `pages: write` + `id-token`)
- [x] T015 [US2] Document operator note in quickstart/progress if deploy needs environment

**Checkpoint**: US2 independent test passes (YAML + preview).

---

## Phase 5: User Story 3 — Price basis & aggregate labels (P1)

**Goal**: Honesty for unadjusted_fallback / 002780; distinct aggregate labels
**Independent Test**: Performance UI shows priceAdjustment + incomplete validation; copy review

- [x] T016 [P] [US3] Add `docs/architecture/price-basis-validation-002780.md` (status incomplete; facts for 783→7820)
- [x] T017 [US3] Surface `priceAdjustment` + incomplete validation banner on PerformanceSummary (i18n)
- [x] T018 [US3] Relabel cumulative / averages per Q5 (modeled pick chain vs per-pick stats)
- [x] T019 [US3] Link validation note from architecture README or Methodology if appropriate

**Checkpoint**: SC-006–SC-007 satisfied.

---

## Phase 6: User Story 4 — Scope guard (P2)

- [x] T020 [P] [US4] Confirm Top-N / RSS generators untouched (diff review); no RSS UI chrome added

**Checkpoint**: FR-010 held.

---

## Phase 7: Polish & Review gate

- [x] T021 [REVIEW] Run `npm run check` + relevant unit tests + `npm run build`
- [x] T022 [REVIEW] Fill `checklist-review.md` against FR/SC; constitution re-check
- [x] T023 Update `progress.yml` → execute done; ready `/speckit.superspec.review`

## Dependencies

- Phase 2 blocks Phase 3–5
- T012 depends on T006
- T017 depends on T006 / T012
- T014 parallel with T012–T013
- T020 anytime after code freeze before review

## Parallel opportunities

```text
T007-T011 (US1) ∥ T014 (ledger deploy)
T012-T013 (US2 UI) ∥ T016 (docs)
```

## Notes

- Auto-advance phase checkpoints per Speckit canonical (human pause only if blocked).
- No git commit/push unless user asks.
