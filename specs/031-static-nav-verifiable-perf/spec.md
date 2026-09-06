# Feature Specification: Fix Static Navigation and Publish Verifiable Performance

**Feature Branch**: `feature/fix-static-navigation-and-publish-verifiable-per`
**Spec directory**: `031-static-nav-verifiable-perf`
**Created**: 2026-09-06
**Status**: Executed (review PASS)
**Input**: GitHub Issue [#94](https://github.com/jee1/ten_bagger/issues/94) — Fix static navigation and publish verifiable performance data. Production static site ignores URL query params for lang / archive month / performance market; performance page empty on Pages despite local content; need deploy path after ledger updates; price-basis validation for outlier `002780.KS` (`unadjusted_fallback`); distinguish per-pick stats from modeled portfolio return. Scope note: Top-5 and RSS already exist — do not rebuild; surface RSS in UI only after reliability work.
**Related**: Constitution Principles I–V (esp. I Git-content → static publish, II PIT / price basis honesty, III additive performance artifacts, V schema/validation); specs/019 ledger, specs/020 performance dashboard, specs/028 Top-N, specs/029 RSS; ADRs 0002–0003

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Language and archive controls change what you see (Priority: P1)

A bilingual visitor opens the live site (including under a base path on GitHub
Pages). Changing language or archive month must change the visible document —
language chrome, titles, body copy, and the calendar month shown — not only the
address bar.

**Why this priority**: Issue #94 reproduces `#1–#2` and `#4` on production:
`?lang=en` leaves Korean content; archive month URL changes but calendar stays
current month; 390px archive overflows horizontally. Navigation trust is the
blocker before any discovery work.

**Independent Test**: On a static production-like build, exercise language
toggle and archive previous-month control; confirm rendered content and
`document` language match the control, and archive has no horizontal overflow
at 390px viewport width.

**Acceptance Scenarios**:

1. **Given** the site is served as a static build, **When** a visitor selects
   English (or opens the English entry for that page), **Then** document
   language, title, navigation labels, and primary body copy for that page are
   English (not Korean leftovers on required chrome).
2. **Given** the visitor is on Archive for the current month, **When** they
   select the previous month, **Then** the visible calendar/month heading
   matches the selected year-month (not merely the URL).
3. **Given** a 390px-wide viewport on Archive, **When** the page loads for any
   supported month, **Then** the document does not force horizontal overflow
   beyond the viewport (no ~403px forced width).

---

### User Story 2 - Performance market control and published facts are visible (Priority: P1)

A visitor opens Performance on the deployed site. Choosing Korea or US must
show that market’s view. When published performance facts exist, the page must
show data (not a permanent empty state), including as-of timestamp, horizon
sample counts, and an honest reason when a horizon is unavailable.

**Why this priority**: Issue #94 `#3` and `#5` — market control ignored; both
markets empty on production while local content exists. Accountability page is
useless until deploy + controls work.

**Independent Test**: After a ledger/performance content update that reaches the
hosted site, open Performance for KR and US; confirm each market’s control
updates content, empty state only when that market truly has no published facts,
and metadata (as-of, sample counts, unavailable reasons) is visible.

**Acceptance Scenarios**:

1. **Given** published performance facts exist for a market on the deployed
   site, **When** a visitor opens Performance for that market, **Then** they
   see non-empty performance content for that market (not the global empty
   state).
2. **Given** both markets have published facts, **When** the visitor switches
   KR ↔ US, **Then** the selected market’s series/summaries replace the other
   market’s (control and content stay in sync).
3. **Given** published facts are present, **When** the visitor reads the page
   chrome, **Then** they see the data-as-of timestamp, per-horizon sample
   counts where applicable, and a plain-language reason when a horizon is
   unavailable.
4. **Given** a ledger/performance regeneration commits updated content,
   **When** the publication path for static hosting runs, **Then** the hosted
   Performance page reflects those updated facts (not an older empty bundle).

---

### User Story 3 - Price basis and aggregate labels are trustworthy (Priority: P1)

A careful reader (or reviewer) inspecting large returns — especially
`002780.KS` H20 with `unadjusted_fallback` — needs visible validation status
and clear labeling that separates per-pick statistics from any modeled
portfolio / cumulative narrative. Incomplete validation must not look like a
verified claim.

**Why this priority**: Issue #94 acceptance requires outlier validation
documentation and UI visibility of incomplete validation; overlapping holding
periods must not be silently called a portfolio return.

**Independent Test**: With published KR facts including the `002780.KS`
outlier (or a fixture equivalent), open Performance and verify price-basis /
validation disclosure for that case; verify aggregate copy distinguishes
per-pick stats from modeled portfolio return.

**Acceptance Scenarios**:

1. **Given** a pick measurement uses `unadjusted_fallback` (including the
   documented `002780.KS` case), **When** a visitor views related performance
   presentation, **Then** the page surfaces that the price basis is fallback /
   validation status (complete vs incomplete) in reader language.
2. **Given** price-basis validation for the outlier is incomplete, **When** the
   page shows aggregate or pick-level outcomes that include that pick,
   **Then** incomplete validation is visibly flagged (not presented as fully
   verified).
3. **Given** cumulative or multi-pick summaries are shown, **When** the visitor
   reads labels and disclaimers, **Then** per-pick statistics are named as such
   and any overlapping-holdings compound figure is labeled as a modeled /
   hypothetical construction — not as a live multi-position portfolio return
   unless allocation/entry/exit rules are explicitly defined and disclosed.

---

### User Story 4 - Reliability before discovery chrome (Priority: P2)

Product discovery extras (notably surfacing the existing RSS feed in site UI)
remain deferred until the reliability stories above are satisfied. Top-N and
RSS generation already exist and MUST NOT be rebuilt in this feature.

**Why this priority**: Issue #94 scope note — avoid rebuilding Top-5/RSS;
surface RSS in UI only after reliability.

**Independent Test**: Confirm this package’s deliverables do not rewrite Top-N
or RSS generators; RSS UI surfacing is absent or explicitly deferred until US1–US3
acceptance is met.

**Acceptance Scenarios**:

1. **Given** Top-N and RSS already ship on the site/build, **When** this
   feature is implemented, **Then** those generators are left intact (no
   rebuild of Top-N/RSS pipelines as part of #94).
2. **Given** reliability acceptance for navigation + performance publish is
   not yet met, **When** reviewing UI scope for this feature, **Then** new
   “subscribe via RSS” chrome is out of scope / deferred.

### Edge Cases

- **Deep link vs control**: Opening a language/market/month entry directly must
  render that view; using on-page controls must yield the same visible result
  as the corresponding entry.
- **One market empty**: If only one market has published facts, that market
  shows data; the other shows market-local empty state — never blend markets.
- **Missing as-of**: If a bundle lacks a usable as-of, fail closed into empty /
  unavailable with reason — do not invent timestamps.
- **Mixed priceAdjustment in a market**: When a market’s run uses mixed or
  fallback adjustment, disclosures MUST cover market-level and outlier-level
  honesty (not only the happy path `adjusted_preferred`).
- **Overlap compounding**: If the site continues to multiply forward returns
  across overlapping holding windows, labeling MUST NOT claim non-overlapping
  portfolio PnL.
- **Base path hosting**: Controls and entries MUST work under the GitHub Pages
  base path (not root-only links).
- **390px archive**: Tables/calendars MUST wrap or scroll within the viewport
  without expanding the document width past the viewport.

#### Brainstorm Prompts

- **Boundary conditions**: Minimum content for non-empty performance; month
  edges (Jan/Dec); missing year/month params.
- **Error scenarios**: Deploy path fails after ledger commit; validation doc
  incomplete; schema-valid but empty measurement lists.
- **Scale**: Long archive history; large KR ledger with many incomplete
  horizons.
- **User confusion**: Query-looking URLs that do not drive static content;
  “portfolio return” wording vs per-pick averages.
- **Data integrity**: `unadjusted_fallback` corporate-action cases; unit
  mismatches; incomplete validation visibility.
- **Backwards compatibility**: Existing bookmarks to `?lang=` / `?market=` /
  `?year=&month=` URLs.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | How should language / archive month / performance market selection work on a fully static host so visible content always matches the visitor’s choice (path segments, client-side state, or hybrid with redirects)? | Resolved | **Client-driven views from URLSearchParams after load**, with all needed variants’ data embedded at build (bilingual strings; archive months/data; both KR/US performance bundles). Path-segment routes deferred — existing query URL contract stays primary. |
| Q2 | How should existing production bookmarks that use query strings (`?lang=`, `?year=&month=`, `?market=`) behave after the fix (preserve via client hydrate, redirect to new entries, or document breakage)? | Resolved | **Preserve**: same query shapes continue to drive the visible view via client hydrate (no intentional bookmark breakage). |
| Q3 | What deployment trigger must run after ledger/performance content commits so GitHub Pages receives the new bundles (extend ledger workflow, chain to daily deploy job, or other)? | Resolved | **Extend `ledger.yml`**: after successful ledger/performance commit+push, run the same Pages build/upload/deploy steps used by `daily.yml` (or reusable workflow_call). Do not wait for the next daily cron alone. |
| Q4 | What constitutes “complete” price-basis validation for `002780.KS` / `unadjusted_fallback` outliers, and what exact UI copy appears when validation is incomplete? | Resolved | **Complete** = written validation note under `docs/` (or Methodology/architecture) covering corporate-action/units/adjusted vs unadjusted for `002780.KS` H20 783→7820, plus UI showing market `runMeta.priceAdjustment` and per-outlier status. Until that note exists and asserts consistency, UI MUST show **incomplete validation** (not “verified”). v1 ships with incomplete status + disclosure. |
| Q5 | How should aggregate performance be labeled and computed when pick holding periods overlap — keep compounded per-pick chain with explicit “not a portfolio” label, or define a simple equal-weight / sequential model with disclosed rules? | Resolved | **Keep current compounded sequential-pick chain**; relabel as hypothetical **per-pick chain / modeled cumulative** (overlapping windows possible). Show **per-pick averages** as distinct stats. Do **not** invent a multi-position allocation model in this package. |
| Q6 | After reliability ships, is RSS UI surfacing in-scope for a fast follow in this branch or strictly a separate issue? | Resolved | **Separate follow-up** after #94 acceptance; out of this package. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST make language selection change visible page language
  (document language, titles, nav, body chrome) on the static hosted site.
- **FR-002**: System MUST make archive year-month selection change the visible
  calendar/month content on the static hosted site.
- **FR-003**: System MUST make performance market (KR/US) selection change the
  visible market content on the static hosted site.
- **FR-004**: Archive presentation MUST NOT cause horizontal document overflow
  at a 390px viewport width.
- **FR-005**: A ledger/performance content update MUST have a defined path that
  results in updated performance facts on GitHub Pages (not only in the git
  tree locally).
- **FR-006**: Performance page MUST show data-as-of timestamp when published
  facts exist for the selected market.
- **FR-007**: Performance page MUST show horizon sample counts and an explicit
  unavailable reason when a horizon cannot be shown.
- **FR-008**: Price-basis validation covering the `002780.KS` outlier (and
  equivalent `unadjusted_fallback` cases) MUST be documented; incomplete
  validation MUST be visible in the UI.
- **FR-009**: Aggregate presentation MUST distinguish per-pick statistics from
  any modeled / hypothetical portfolio-style cumulative figure.
- **FR-010**: Top-N and RSS generation pipelines MUST NOT be rebuilt as part of
  this feature; RSS UI surfacing remains deferred until FR-001–FR-009 are met
  (per Q6).
- **FR-011**: Live Score weights / threshold / `SCORE_VERSION` MUST NOT change
  as part of this feature (Constitution Principle IV).
- **FR-012**: Measurement and price-basis disclosures MUST remain consistent
  with PIT rules (Constitution Principle II) and additive performance artifacts
  (Principle III).
- **FR-013**: Public disclaimer (not investment advice) MUST remain on
  performance surfaces when copy changes.
- **FR-014**: Completing this feature fulfills Issue #94 acceptance criteria
  listed in the issue body.
- **FR-015**: Primary pages (home, archive, performance, methodology, daily) MUST embed sufficient build-time data for client-side selection of language and (where applicable) archive month / performance market so visible content matches URL query after load.
- **FR-016**: Performance UI MUST surface market `runMeta.priceAdjustment` (and incomplete price-basis validation status per Q4) whenever non-empty facts are shown.
- **FR-017**: Cumulative/aggregate copy MUST use the Q5 labeling (per-pick stats vs modeled cumulative chain; not a live multi-position portfolio).
- **FR-018**: `ledger.yml` MUST deploy GitHub Pages after a successful ledger/performance content push (Q3).

### Key Entities

- **StaticNavView**: The visitor-visible combination of language, archive
  month, and/or performance market that MUST match controls and entry links.
- **PerformanceBundle**: Published market performance facts (as-of, horizons,
  measurements, runMeta including priceAdjustment).
- **PriceBasisValidation**: Documented check of adjustment/fallback consistency
  for outlier picks; status complete or incomplete for UI.
- **AggregateLabeling**: Presentation contract separating per-pick stats vs
  modeled cumulative/portfolio narrative.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a static production-like build, changing language updates
  visible chrome/body language in 100% of primary pages exercised (home,
  archive, performance, methodology, sample daily).
- **SC-002**: On a static production-like build, selecting previous archive
  month updates visible month in 100% of trials (not URL-only).
- **SC-003**: At 390px viewport, Archive has 0 horizontal overflow (document
  scrollWidth ≤ clientWidth, or equivalent manual check).
- **SC-004**: After the defined ledger→Pages path runs with non-empty
  performance content, Performance for that market is non-empty on the hosted
  (or Pages-artifact) site.
- **SC-005**: Performance chrome exposes as-of + horizon availability/sample
  metadata whenever facts exist; unavailable horizons show a reason in 100% of
  fixture cases.
- **SC-006**: `002780.KS` / `unadjusted_fallback` validation result is
  documented and reflected in UI status (complete or incomplete) — no silent
  “fully verified” presentation when incomplete.
- **SC-007**: Aggregate labels pass a copy review: per-pick vs modeled
  portfolio wording are distinct; overlapping-holdings compound is never
  described as a live multi-position portfolio without disclosed rules.
- **SC-008**: Issue #94 acceptance checklist items can be marked done without
  rebuilding Top-N/RSS generators.
- **SC-009**: KR and US market switches each show the selected market’s content
  when both have published facts.

## Assumptions

- Site remains fully static (`output: 'static'`); request-time server rendering
  of query params is not available — navigation design must respect that.
- Issue #94 production URL `https://jee1.github.io/ten_bagger/` is the
  verification target shape (base path included).
- Local `content/performance/` may already contain facts; production emptiness
  is primarily a publish/deploy path and/or static nav issue.
- Top-N (#72) and RSS (#73) already delivered; out of rebuild scope.
- Constitution v1.3.0 remains in force; no Score live merge in this package.
- Q6 confirmed: RSS UI surfacing is a separate follow-up after #94 acceptance.


## Brainstorm Log

### Session 2026-09-06 (1) — all recommended
**Focus**: Q1–Q6 (static nav model, bookmarks, deploy path, price-basis validation, aggregate labeling, RSS UI scope)
**Key insights**:
- Static `Astro.url.searchParams` bake-in is root cause; client-driven views + embedded variant data preserves `?lang=` / `?year=&month=` / `?market=` bookmarks.
- `ledger.yml` commits performance JSON but never deploys Pages; must add deploy after push.
- KR `runMeta.priceAdjustment=unadjusted_fallback`; `002780.KS` H20 783→7820 ships with **incomplete** validation disclosure until docs note completes.
- Keep compounded pick chain; rename to modeled cumulative / per-pick stats — no new portfolio allocator.
- RSS UI deferred (separate issue).
**Spec updates**: Q1–Q6 Resolved; FR-015–FR-018; Status → Brainstormed
**Coverage**: Open Questions=0; further brainstorm not needed unless new focus requested.
