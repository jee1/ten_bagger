# Feature Specification: Product Top-N Candidates + Score Breakdown Archive

**Feature Branch**: `feature/product-top-n`
**Created**: 2026-09-05
**Status**: Executed (review PASS)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/72 — 일 1픽은 유지하되, 투명성을 위해 당일 Top-N과 축별 점수를 아카이브/페이지에 노출. daily JSON 또는 부가 파일에 top N 저장; UI 펼쳐보기 (카드 남용 없이 기존 디자인 언어 유지). 수용: 스키마·타입 동기화, 페이지/아카이브 노출, Epic Phase 4."
**Related**: Epic #74 Phase 4 (제품 확장); Issue #72; informed by docs gate #75/PR #76 (not blocked); constitution Principles I–V; sibling #73 (RSS) out of scope

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See why this pick (or near-misses) ranked Top-N (Priority: P1)

A bilingual site visitor reading a published daily entry wants transparency beyond
the single published pick: they can open a compact Top-N list for that day and
see each candidate’s composite score plus the same score-axis breakdown the pick
already shows, so ranking is explainable without changing the “one pick per day”
product rule.

**Why this priority**: Issue #72’s core goal is transparency of the day’s ranking
and axis scores while keeping the daily one-pick contract.

**Independent Test**: With a published daily entry that includes Top-N
candidates, open the daily page (KR and EN) and confirm an expandable Top-N
section lists up to 5 ranked candidates with composite and axis scores; the day’s
published pick identity and status remain unchanged.

**Acceptance Scenarios**:

1. **Given** a published daily entry with status `pick` and Top-N data present,
   **When** a visitor opens that day’s page and expands Top-N, **Then** they see
   up to 5 ranked candidates including the published pick, each with composite
   and axis scores matching the live score-axis set for that entry’s score
   version.
2. **Given** the same entry, **When** Top-N remains collapsed, **Then** the first
   viewport still presents the existing one-pick narrative (pick identity,
   summary, primary scores) without an extra card cluster or competing hero
   blocks.
3. **Given** KR and EN locales, **When** the visitor switches language,
   **Then** labels and localized names for Top-N candidates follow the site’s
   bilingual pattern; numeric scores stay identical across locales.
4. **Given** a `no_pick` day with eligible scored candidates, **When** the
   visitor expands Top-N, **Then** they see up to 5 near-miss candidates with
   scores, and the page still states there is no published pick.

---

### User Story 2 - Archive history stays readable with optional Top-N (Priority: P1)

A visitor browsing the archive reaches day pages that may include Top-N
transparency, without archive-list chrome changes and without breaking days that
predate the feature.

**Why this priority**: Issue #72 requires archive exposure; older entries must
keep working (Principle I historical stability). v1 keeps archive list unchanged
and exposes Top-N on the day page only.

**Independent Test**: Open archive with a mix of entries that have and lack
Top-N fields; confirm list looks as today; open a day with Top-N and expand
breakdown; open a day without Top-N and confirm no broken control.

**Acceptance Scenarios**:

1. **Given** an archive listing that includes entries without Top-N data,
   **When** a visitor views the archive, **Then** those entries render with
   existing behavior and the list does not add Top-N badges or inline expands.
2. **Given** an entry with Top-N data, **When** a visitor opens it from the
   archive into the day page, **Then** they can expand the same Top-N breakdown
   as User Story 1.
3. **Given** Top-N is missing on a historical day, **When** content validation
   runs, **Then** the entry remains valid (Top-N is additive/optional for
   pre-feature history).

---

### User Story 3 - Schema and types stay honest for Top-N (Priority: P1)

A maintainer publishing daily content gets schema validation and generated/
hand-synced app types that accept Top-N candidate records so CI catches drift
between written content and the site contract.

**Why this priority**: Issue #72 acceptance criterion “스키마·타입 동기화”;
constitution Principle I requires committed content contracts.

**Independent Test**: Add a fixture daily JSON with Top-N candidates; run the
project’s content validation / type-check path and confirm pass; omit a required
candidate field and confirm fail.

**Acceptance Scenarios**:

1. **Given** a daily document with well-formed Top-N candidates, **When**
   content validation runs, **Then** it passes.
2. **Given** a Top-N candidate missing a required identity or score field,
   **When** validation runs, **Then** it fails with a clear contract error.
3. **Given** schema and app-facing types are updated together, **When** a
   maintainer compares them, **Then** Top-N field shapes are consistent (no
   silent optional drift).
4. **Given** Top-N with duplicate symbols or non-monotonic ranks, **When**
   validation runs, **Then** it fails.

---

### Edge Cases

- Day with fewer than 5 eligible scored survivors: publish shorter list, ordered
  by composite descending, no padding.
- Zero eligible scored candidates: omit Top-N field (or empty list disallowed —
  prefer omit); UI hides control.
- Tie on composite: secondary sort by symbol ascending (case-sensitive as stored);
  ranks remain stable across reruns.
- `no_pick` days: still publish Top-N near-misses when eligible candidates exist.
- Red-flag / hard-exclude symbols: MUST NOT appear in Top-N (same exclusion
  rules as pick eligibility for that score version).
- Historical days without Top-N: UI omits control; validation still passes.
- Score version / axis set: all Top-N rows for a day MUST share the same
  score-axis set as that day’s published scores / score version.
- Duplicate symbols in Top-N: invalid content.
- `pick` day where published pick is missing from Top-N or not rank 1: invalid.
- Readers mistaking Top-N for multi-pick advice: short transparency framing +
  existing investment disclaimer posture.

#### Brainstorm Prompts

- **Boundary conditions**: Exact N=5; short lists; ties; no_pick vs pick; zero eligible.
- **Error scenarios**: Malformed Top-N; missing axes; duplicate symbols; pick≠rank1.
- **Scale**: N=5 axis vectors — negligible daily JSON growth.
- **Security**: Public screened universe only; no secrets.
- **User confusion**: One-pick vs runners-up framing.
- **Data integrity**: Rank order = composite then symbol; pick = rank 1 on pick days.
- **Backwards compatibility**: Additive optional field; no historical rewrite.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Fixed Top-N size for v1? | Resolved | **N=5** |
| Q2 | Publish Top-N on `no_pick` days (near-miss transparency)? | Resolved | **Yes** — publish up to 5 near-misses when eligible candidates exist |
| Q3 | Archive exposure: day-page expand only, or also compact hint/expand on archive list? | Resolved | **Day page only** — archive list unchanged; Top-N via day page expand |
| Q4 | Empty eligible set: empty array vs omit field? | Resolved | **Omit field** when zero eligible; UI treats missing as no control |
| Q5 | Tie-break key when composites equal? | Resolved | **Symbol ascending** (as stored string) |
| Q6 | Validation: enforce pick≡rank1 and unique symbols? | Resolved | **Yes** — hard validation errors |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST continue publishing at most one daily pick per market
  day (`status: pick` with a single stock, or `no_pick`); Top-N MUST NOT change
  the one-pick product rule.
- **FR-002**: System MUST persist Top-N candidate records for new daily
  publications in the daily content document (additive field on the existing
  daily JSON — not a separate system of record). Sidecar files are out of scope
  for v1 unless a later ADR says otherwise.
- **FR-003**: System MUST store each Top-N candidate with: rank (1…5), symbol,
  localized name, exchange (if available for picks today), composite score, and
  the same score-axis fields used for that day’s score version (e.g. size,
  growth, valuation, entry, momentum, quality as applicable).
- **FR-004**: System MUST NOT require full reasoning prose for non-pick Top-N
  rows in v1 (scores + identity only); the published pick keeps existing
  reasoning.
- **FR-005**: When `status` is `pick`, the published pick MUST appear as rank 1
  in Top-N (same symbol), and remaining ranks MUST be the next-best eligible
  scored candidates by composite descending (ties: symbol ascending).
- **FR-006**: Top-N length MUST be fixed **N=5** for v1 (`min(5, eligible_count)`).
- **FR-007**: On days with fewer than 5 eligible scored candidates, System MUST
  publish the shorter list without padding.
- **FR-008**: System MUST apply the same eligibility / exclusion rules used for
  pick selection when building Top-N (red flags, universe filters for that run).
- **FR-009**: Content schema and app-facing types MUST be updated together so
  Top-N is validated and typed; historical entries MAY omit Top-N.
- **FR-010**: Daily page UI MUST offer an expand/collapse (or equivalent)
  Top-N + axis breakdown that reuses existing visual language (score grid /
  typography / spacing) and MUST NOT introduce a new card-heavy cluster in the
  hero/first viewport.
- **FR-011**: Archive list UI MUST remain unchanged for v1; Top-N exposure is
  via the day page reached from archive links.
- **FR-012**: UI MUST frame Top-N as transparency / runners-up, not as
  additional investment recommendations (preserve site disclaimer posture).
- **FR-013**: On `no_pick` days with eligible scored candidates, System MUST
  still populate Top-N (near-miss transparency); on `no_pick` with zero
  eligible, omit Top-N.
- **FR-014**: New daily pipeline runs after ship MUST populate Top-N when
  eligible candidates exist; mandatory historical backfill of all past days is
  OUT OF SCOPE for v1.
- **FR-015**: Completing this feature fulfills Epic #74 Phase 4 issue #72
  acceptance (schema/type sync + page/archive exposure); #73 RSS remains
  separate.
- **FR-016**: When eligible_count is 0, System MUST omit the Top-N field
  (must not write an empty array).
- **FR-017**: Content validation MUST reject Top-N lists with duplicate symbols,
  non-contiguous ranks starting at 1, length &gt; 5, or (when `status=pick`)
  rank-1 symbol ≠ published pick symbol.
- **FR-018**: Live Score weights / threshold / SCORE_VERSION MUST NOT change as
  part of this feature (Constitution Principle IV).

### Key Entities

- **DailyEntry**: Existing published day record; gains optional Top-N list.
- **TopNCandidate**: Ranked runner (or pick at rank 1) with identity + composite
  + axis scores for one day/market.
- **ScoreAxes**: The axis set consistent with that day’s `scores.version` /
  published pick score fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a day with Top-N present, a visitor can reveal all Top-N
  composite and axis scores in under 30 seconds without leaving the day page.
- **SC-002**: 100% of newly published daily entries after feature ship that have
  ≥1 eligible scored candidate include a Top-N list of length
  `min(5, eligible_count)` that validates against schema.
- **SC-003**: Historical entries without Top-N continue to pass content
  validation and render without layout errors (zero regressions on sample
  archive pages).
- **SC-004**: For `pick` days with Top-N, rank-1 symbol matches the published
  pick symbol in 100% of fixture/validation cases.
- **SC-005**: Bilingual (KR/EN) day pages both expose Top-N labels; numeric
  scores match across locales.
- **SC-006**: Issue #72 acceptance checklist items (schema/type sync,
  page/archive exposure, Epic Phase 4 #72) can be marked done without shipping
  #73.
- **SC-007**: Archive list pages show no new Top-N-only chrome; day pages with
  Top-N remain reachable from archive links.
- **SC-008**: Validation fixtures prove reject paths for duplicate symbol and
  pick≠rank1.

## Assumptions

- Epic Phase 4 here means product expansion issues #72/#73; this spec covers #72
  only.
- Performance Loop Phase 0–1 are already done on main; #72 remains informed /
  unblocked by docs gate.
- Top-N is for public transparency of the screening rank, not a change to
  portfolio construction or multi-pick publication.
- Axis set follows the live score version already written on the daily entry
  (v2 axes today); Score v3 live merge is independent and out of scope unless
  already live.
- No ADR required solely for v1 storage choice (additive daily field); dual
  source / RSS ADRs unchanged.
- Design: prefer native expand/collapse and existing score presentation over
  new card components (aligns with site UI rules and issue text).
- Speckit usage (project memory): recommend-auto for open Q; brainstorm to
  Brainstormed; plan only after explicit approve; no commit/push unless asked.

## Brainstorm Log

### Session 2026-09-05
**Focus**: Specify clarifications Q1–Q3 + boundary/error/UX saturation (memory: all-recommendations)
**Key insights**:
- N=5 (light payload, enough transparency)
- `no_pick` still gets Top-N near-misses when eligible exist
- Archive list unchanged; day-page expand only
- Omit Top-N field when zero eligible (no empty array)
- Tie-break: symbol ascending
- Hard validate: unique symbols, contiguous ranks from 1, pick≡rank1 on pick days
- Score freeze untouched (Principle IV)
**Spec updates**: Q1–Q6 Resolved; FR-006/011/013/016–018; US1.4; US2 day-page-only; US3.4; SC-007–008; Status=Brainstormed
