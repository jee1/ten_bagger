# Feature Specification: Score v3 Live Merge after Search `go_evidence`

**Feature Branch**: `feature/follow-up-score-v3-live-merge-after-search-go_ev`
**Spec Directory**: `030-score-v3-live-merge-go-evidence`
**Created**: 2026-09-06
**Status**: Executed (review PASS)
**Input**: GitHub Issue [#91](https://github.com/jee1/ten_bagger/issues/91) — Follow-up: Score v3 live merge after search `go_evidence`
**Related**: Epic [#74](https://github.com/jee1/ten_bagger/issues/74) CLOSED (explicit partial adoption via [PR #90](https://github.com/jee1/ten_bagger/pull/90)); Issues #67/#68/#69/#70; ADR 0004; `docs/architecture/074-phase2-measurement-note.md`; `docs/architecture/threshold-weight-merge-criteria.md`; constitution Principle IV (Score Freeze Until Merge Gate); specs `023`–`026`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Know when search `go_evidence` is eligible (Priority: P1)

A maintainer asks whether the committed ledger + H20-complete window is long
enough to carve **disjoint** IS and OOS calendars that each can reach the ADR
0004 OOS coverage floor (≥20 scored pick days) for a Score v3 **search**
`packageIntent=go_evidence` run — without guessing from Phase 2 baseline-only GO.

**Why this priority**: Issue #91 blockers open with “H20-complete window too
short”; running search anyway produces false merge pressure. Eligibility must be
explicit.

**Independent Test**: Point a readiness check at a fixed ledger/as-of fixture
(or committed content); read a deterministic ready / not-ready report citing
H20-complete span, proposed IS/OOS carve, and projected OOS pick-day coverage.

**Acceptance Scenarios**:

1. **Given** an as-of date and markets, **When** readiness runs, **Then** it
   reports whether a disjoint IS/OOS carve exists that can satisfy OOS pick-day
   ≥20 under ledger H20-complete rows (or explicitly why not).
2. **Given** history that cannot carve both sides ≥20, **When** readiness runs,
   **Then** status is **not_ready** / equivalent and MUST NOT imply merge
   readiness or authorize `SCORE_VERSION` edits.
3. **Given** identical inputs, **When** readiness runs twice, **Then** the
   report is deterministic.

---

### User Story 2 - Measure counterfactual Score v3 picks without ledger-symbol miss (Priority: P1)

A calibrator runs walk-forward / calibration with threshold or weight
**overrides** (Score v3 candidates). Re-screened symbols that are absent from
the published performance ledger MUST still be measurable for H20 (primary)
under documented ADR price rules, instead of collapsing the package via
`missing_ledger_row` incompletes.

**Why this priority**: Phase 2 note blocker #3 — “Override candidates re-screen →
symbols often missing from ledger → go_evidence fail.”

**Independent Test**: Fixture with override picks whose symbols lack ledger
rows; run measure path; confirm H20 rows complete via price recompute (or
documented fallback) without treating published-ledger-only baseline as
authority for the counterfactual symbols.

**Acceptance Scenarios**:

1. **Given** `go_evidence` with weight/threshold overrides and a pick symbol
   missing from the performance ledger, **When** measurement runs, **Then** the
   row is completed via ADR-aligned price recompute (not left as
   `missing_ledger_row` incomplete that silently starves coverage).
2. **Given** the same pick date/symbol **present** in the ledger, **When**
   measurement runs, **Then** the ledger row is preferred (no silent divergence
   from published returns for published picks).
3. **Given** price data insufficient for H20, **When** measurement runs,
   **Then** the row stays incomplete with an explicit reason other than a false
   “ledger miss is fatal for all counterfactuals” policy.
4. **Given** baseline-only / no-override ledger measurement, **When** a symbol
   is missing, **Then** existing published-pick incomplete behavior remains
   unchanged (no accidental rewrite of Phase 2 baseline semantics).

---

### User Story 3 - Run search `go_evidence` for Score v3 candidate packages (Priority: P1)

When history is eligible (US1), a maintainer runs **search**
`packageIntent=go_evidence` over Score v3 analysis packages (#68 investment
dummy, #69 growth reweight, #70 macro/rate gate — as available candidate grids),
with IS-only ranking and OOS GO/NO-GO per ADR 0004 / merge-criteria doc.

**Why this priority**: Issue #91 goal — search `go_evidence` for Score v3
candidates after Phase 2 baseline-only GO.

**Independent Test**: Dry-run or fixture calibration config with
`mode=search`, `packageIntent=go_evidence`, disjoint IS/OOS; assert IS ranking
ignores OOS; OOS verdict uses hard bullets; live `SCORE_VERSION` stays 2.

**Acceptance Scenarios**:

1. **Given** an eligible calendar and a declared Score v3 candidate grid,
   **When** search `go_evidence` runs, **Then** candidates are ranked on IS only
   and the winner is evaluated on held-out OOS with H20 excess primary and
   coverage floor ≥20.
2. **Given** OOS coverage below floor, **When** verdict computes, **Then**
   **NO-GO** with `insufficient_coverage` (or equivalent) and no merge hint for
   live Score v3.
3. **Given** IS/OOS date overlap or OOS used for selection, **When** validation
   runs, **Then** the package is rejected as contaminated.
4. **Given** any completed search run, **When** live config is inspected,
   **Then** `SCORE_VERSION` remains **2** and `ENABLE_*` Score v3 flags stay
   analysis-default until an explicit GO+merge PR (US4).

---

### User Story 4 - Open live Score v3 config PR only after search GO (Priority: P1)

On **GO** from search `go_evidence` (not baseline-only), a maintainer is guided
to open an explicit `scripts/config.py` PR setting `SCORE_VERSION=3` plus the
approved weights/threshold/gates. On **NO-GO** or **not_ready**, no live config
PR is opened.

**Why this priority**: Issue #91 — “On GO, open an explicit config PR”;
constitution IV; merge-criteria anti-pattern against treating baseline-only GO
as permission to change live Score.

**Independent Test**: Simulate GO search report → CLI/docs emit Score v3 PR
hint; simulate baseline-only GO → hint still forbids `SCORE_VERSION=3`; simulate
NO-GO → no live-edit authorization language.

**Acceptance Scenarios**:

1. **Given** search `go_evidence` **GO** with approved candidate constants,
   **When** the calibrator reads the PR hint, **Then** it instructs an explicit
   PR editing `SCORE_VERSION=3` and only the approved live knobs, linking the
   calibration report + merge-criteria doc.
2. **Given** baseline-only GO (Phase 2 style), **When** the hint is printed,
   **Then** it MUST NOT authorize `SCORE_VERSION=3` / weight/threshold edits.
3. **Given** NO-GO or not_ready, **When** outputs are read, **Then** frozen
   Score v2 remains and no config-PR authorization is claimed.

---

### Edge Cases

- H20-complete window grows mid-month — readiness must recompute from ledger, not
  cache a stale “not_ready forever.”
- One market eligible, the other not — report per-market and aggregate policy
  must be explicit (recommend: require the markets listed in the calibration
  config).
- Counterfactual recompute vs ledger disagreement on a symbol that later appears
  in ledger — prefer ledger when present; document precedence.
- H60 still incomplete for all picks — MUST NOT block H20-primary GO (ADR 0004);
  H60 remains reported/incomplete.
- Partial candidate grid failure mid-search — no overall GO (merge criteria
  completeness bullet).
- Operator tries `fixture-recompute` as sole `measurementSource` for
  `go_evidence` — still forbidden for published-baseline path; counterfactual
  fill is an additive measure policy under ledger go_evidence, not a replacement
  of the go_evidence ledger requirement for published picks.

#### Brainstorm Prompts

- **Boundary**: Minimum H20-complete days to claim eligibility; single-market
  configs.
- **Error**: Price provider failure during counterfactual fill; corrupt ledger
  index.
- **Scale**: Full KR+US search cost vs smoke fixtures.
- **Security**: No secrets in calibration configs; hash-only provenance.
- **Confusion**: Baseline-only GO vs search GO authorization.
- **Integrity**: IS/OOS disjoint; no look-ahead in recompute.
- **Compatibility**: Phase 2 baseline packages and freeze tests stay green.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Counterfactual missing ledger rows: price recompute fill, matching-picks-only, or both? | Resolved | **Hybrid**: prefer ledger row when present; else ADR-aligned **price recompute** for override picks. Matching-picks-only rejected — starves Score v3 search. |
| Q2 | When history ineligible: hard preflight stop vs run-and-NO-GO? | Resolved | **Hard readiness preflight** for search `go_evidence` configs (`not_ready` exit / no merge claim). Forced runs still may produce `insufficient_coverage` NO-GO; never imply merge readiness. |
| Q3 | Does incomplete H60 block search GO? | Resolved | **No**. ADR 0004: H20 primary; H60 reported. Incomplete H60 alone MUST NOT force NO-GO. |
| Q4 | Which Score v3 packages are in the default search grid for #91? | Resolved | **#68–#70** analysis packages as available candidate sources (investment-dummy / growth-yartseva / macro-rate). Start with growth grid if multi-package orchestration is deferred; document which grid(s) shipped. |
| Q5 | Auto-open GitHub PR on GO vs human-only explicit PR + CLI hint? | Resolved | **Human-only** explicit PR + calibrate CLI hint (constitution IV / merge-criteria). No auto-open / auto-edit of `scripts/config.py`. |
| Q6 | If still not_ready on 2026-09-06, is shipping readiness+measure path enough to close the implementation slice? | Resolved | **Yes** for this branch’s implementation slice: readiness + counterfactual measure + search wiring + docs/hints. Live `SCORE_VERSION=3` merge waits for real GO evidence. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a deterministic readiness / eligibility check
  for search `go_evidence` IS/OOS carve against H20-complete ledger coverage.
- **FR-002**: System MUST NOT treat Phase 2 baseline-only GO as authorization to
  change live `SCORE_VERSION` / weights / threshold / Score v3 gates.
- **FR-003**: For override (counterfactual) `go_evidence` runs, measurement MUST
  complete H20 via ADR-aligned price recompute when the performance ledger lacks
  that pick symbol, preferring ledger rows when present.
- **FR-004**: Baseline-only / no-override ledger measurement semantics MUST remain
  unchanged for published picks.
- **FR-005**: System MUST support `mode=search` + `packageIntent=go_evidence`
  calibration over Score v3 candidate packages with IS-only selection and OOS
  ADR 0004 hard bullets.
- **FR-006**: On search GO, system MUST emit guidance for an explicit
  `scripts/config.py` PR (`SCORE_VERSION=3` + approved constants). On NO-GO /
  not_ready / baseline-only GO, it MUST NOT authorize that PR.
- **FR-007**: Documentation (`074-phase2-measurement-note` follow-up and/or
  merge-criteria addendum) MUST describe #91 blockers, eligibility, and
  counterfactual measure policy.
- **FR-008**: Live daily selection MUST remain on Score v2 (`SCORE_VERSION=2`)
  until the explicit GO merge PR is approved.

### Key Entities

- **ReadinessReport**: asOfDate, markets, H20-complete span, proposed IS/OOS
  windows, projected OOS pick days, status (`ready` / `not_ready`), reasons.
- **CounterfactualMeasurement**: pickDate, symbol, horizon, source
  (`ledger` | `price_recompute`), completionStatus, incompleteReason.
- **ScoreV3SearchPackage**: calibration config with candidate grid referencing
  #68–#70 analysis knobs; `packageIntent=go_evidence`; `mode=search`.
- **LiveMergeAuthorization**: derived only from search GO (never baseline-only).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Readiness check returns deterministic ready/not_ready with cited
  coverage numbers on fixtures.
- **SC-002**: Override pick missing from ledger yields completed H20 via price
  recompute in unit/integration tests (no false all-incomplete from
  `missing_ledger_row` alone).
- **SC-003**: Freeze tests continue asserting live `SCORE_VERSION == 2` until a
  future GO merge (out of band for this branch unless GO evidence exists).
- **SC-004**: Search GO path prints Score v3 PR hint; baseline-only GO does not.
- **SC-005**: Docs name Issue #91 blockers and the unblock path (history and/or
  counterfactual measure).

## Assumptions

- Epic #74 is CLOSED with explicit partial adoption; #91 is the follow-up lane.
- ADR 0004 / merge-criteria hard bullets remain authoritative.
- H20 is primary; H60 reported.
- Existing calibrate CLI and walk-forward harness (#66/#67) are the extension
  points — prefer additive changes over a new subsystem.
- Actual live Score v3 merge may remain blocked by calendar length even after
  this feature ships; shipping the path is still in scope.

## Brainstorm Log

### Session 2026-09-06
**Focus**: Issue #91 blockers vs constitution IV / ADR 0004; unattended recommendations
**Key insights**:
- Phase 2 baseline-only GO must stay non-authorizing for Score v3 live merge
- Counterfactual search needs ledger-prefer + price-recompute fill (blocker #3)
- Eligibility preflight prevents false merge pressure while history is short
- H60 incompleteness is expected until ~60 sessions; do not gate on it
- Human PR only; ship path even if calendar still `not_ready`
**Spec updates**: Q1–Q6 Resolved; Status → Brainstormed (ready for plan)
