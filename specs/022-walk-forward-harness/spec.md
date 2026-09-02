# Feature Specification: Point-in-Time Walk-Forward Harness

**Feature Branch**: `feature/performance-point-in-time-walk-forward-harness`
**Spec Directory**: `022-walk-forward-harness`
**Created**: 2026-08-31
**Status**: Brainstormed (ready for plan)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/66"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #66; ADRs 0001–0004;
ledger #63 (recommended dependency); constitution v1.0.1

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a point-in-time walk-forward evaluation (Priority: P1)

A maintainer runs a walk-forward evaluation so that, at each fold decision date
`t`, screening uses only information knowable at `t`, then measures subsequent
out-of-sample (OOS) outcomes — going beyond one-shot snapshot comparison.

**Why this priority**: Without PIT walk-forward, Score merge evidence and
screening-rule claims are not trustworthy. This is Epic #74 Phase 1 / Issue #66.

**Independent Test**: Given fixed pick/ledger fixtures and frozen prices, run
one walk-forward job and obtain fold-level OOS metrics that ignore any data
after each fold’s `t`.

**Acceptance Scenarios**:

1. **Given** a declared evaluation calendar with at least two folds, **When** a
   maintainer runs walk-forward for a candidate screening rule, **Then** each
   fold’s selection step uses only inputs available at that fold’s decision
   date `t`.
2. **Given** price or feature history that continues after `t`, **When** the
   fold’s selection and OOS measurement complete, **Then** no selected input
   and no OOS return uses observations after the relevant cut (decision `t` for
   selection; measurement policy per ADR 0002 for outcomes).
3. **Given** the same fixtures and configuration, **When** walk-forward is run
   twice, **Then** reported fold metrics and aggregates are identical
   (deterministic).

---

### User Story 2 - Produce a reproducible OOS metrics report (Priority: P1)

A reviewer receives a machine-readable report (and a human-readable CLI
summary) with pick forward return, hit-rate, excess return vs market benchmark,
and `no_pick` coverage — suitable as ADR 0004 evidence input.

**Why this priority**: Issue #66 acceptance requires reproducible OOS results;
ADR 0004 GO depends on walk-forward packages.

**Independent Test**: Run walk-forward on fixtures; open the report artifact and
verify required metrics and horizon/benchmark ids without network access.

**Acceptance Scenarios**:

1. **Given** a completed walk-forward run, **When** the reviewer inspects the
   report, **Then** it includes per-fold and aggregate pick forward return,
   hit-rate, excess return vs the market benchmark, and `no_pick` ratio (or
   equivalent coverage count).
2. **Given** KR and US folds in the evaluation window, **When** the report is
   produced, **Then** horizons name **H20** (required) and **H60** (reported)
   and benchmarks use **KR-KOSPI** / **US-SPX** per ADR 0003.
3. **Given** `no_pick` days in the sample, **When** averages are computed,
   **Then** `no_pick` days are excluded from pick-return averages but counted in
   coverage / `no_pick` ratio stats.
4. **Given** a run labeled `go_evidence`, **When** aggregate OOS scored `pick`
   days fall below the ADR 0004 floor (≥20), **Then** the report marks
   `insufficient_coverage` and MUST NOT imply GO readiness.

---

### User Story 3 - Support rolling train → OOS (and document anchored) (Priority: P1)

A maintainer configures rolling train windows that advance through time, each
followed by a held-out OOS segment, without reusing the same period for both
fitting narrative and GO claim without disclosure.

**Why this priority**: ADR 0003 requires rolling OOS segments for merge
evidence; Issue #66 calls for rolling/anchored train → OOS.

**Independent Test**: Fixture calendar with three successive folds yields three
distinct OOS segments and a report that labels train vs OOS ranges per fold.

**Acceptance Scenarios**:

1. **Given** a rolling configuration, **When** walk-forward runs, **Then** each
   fold declares an explicit train range and a later OOS range with no silent
   overlap between that fold’s train and OOS.
2. **Given** a maintainer requests anchored mode, **When** they review the PIT
   assumptions document, **Then** anchored behavior is fully defined and
   explicitly deferred to a follow-up (not runnable in v1).
3. **Given** a fold whose OOS window has insufficient completed H20 outcomes,
   **When** the report is written, **Then** that fold is marked
   `incomplete_horizon` rather than inventing returns.

---

### User Story 4 - Document PIT assumptions for readers and reviewers (Priority: P2)

A contributor can find a single written statement of point-in-time assumptions
(decision cut, calendar, holidays, what “knowable at `t`” means) in Methodology
and/or this feature’s spec package.

**Why this priority**: Issue #66 acceptance criterion; constitution Deployment
Gates require PIT docs for walk-forward claims.

**Independent Test**: Open the documented location and verify it answers cut
date, horizon length basis (trading sessions), and look-ahead prohibition
without reading implementation code.

**Acceptance Scenarios**:

1. **Given** the feature is delivered, **When** a reviewer searches Methodology
   or the active spec docs, **Then** they find an explicit PIT assumptions
   section covering decision `t`, H20/H60, and no look-ahead.
2. **Given** holiday / market-calendar choices affect fold boundaries, **When**
   those choices are made, **Then** they are named in the same documentation
   (exact calendar tables may ship with the implementation plan).
3. **Given** a reader compares walk-forward to snapshot screening checks,
   **When** they consult the PIT assumptions / feature docs, **Then** the
   distinction from legacy `backtest_screen` snapshot comparison is explicit.

---

### User Story 5 - Prove safety with CI smoke fixtures (Priority: P2)

A contributor changes walk-forward logic and relies on an offline CI smoke
(small fixture) to catch look-ahead regressions and missing report fields
before merge.

**Why this priority**: Issue #66 acceptance; constitution walk-forward smoke
gate.

**Independent Test**: Run the project’s walk-forward smoke suite with no
network; it fails if future-after-`t` data is used or required metrics are
absent.

**Acceptance Scenarios**:

1. **Given** checked-in small fixtures, **When** CI (or local equivalent) runs
   the smoke, **Then** it passes without live market calls.
2. **Given** a deliberately contaminated fixture (features only available after
   `t`), **When** smoke assertions run, **Then** the harness rejects or proves
   those features were unused.

---

### Edge Cases

- **Minimum folds**: A valid run requires at least **two** folds; fewer MUST fail
  with an actionable configuration error.
- **Empty train window**: If a fold’s train window has zero scored `pick` days,
  skip the fold with status `skipped_empty_train`; do not fabricate picks.
- **Insufficient GO coverage**: If a `go_evidence` run has fewer than **20**
  aggregate OOS scored `pick` days (ADR 0004 floor), mark `insufficient_coverage`
  in the report; do not imply GO readiness.
- **OOS beyond ledger asOfDate**: If OOS ends after the global `asOfDate` of
  available ledger facts, mark fold `incomplete_horizon`; do not invent exits.
- **Incomplete H20/H60**: If a horizon cannot complete within available facts,
  fold status MUST be `incomplete_horizon` (not silently averaged as complete).
- **Missing ledger (#63)**: For `go_evidence` runs (and default production
  paths), fail with an actionable error directing the maintainer to regenerate
  the ledger; do not quietly reimplement full ledger semantics inside the
  harness.
- **Fixture recompute (dev/smoke only)**: Offline smoke MAY use
  `measurementSource: fixture-recompute` with picks+prices fixtures; this path is
  FORBIDDEN for ADR 0004 GO packages.
- **Corrupt fixtures**: Fail with file path and schema-validation hint; do not
  proceed with partial silently-truncated inputs.
- **Partial market calendar**: If only one market (KR or US) appears in the
  window, report that market only; do not invent the other.
- **Unmatched symbols**: If a candidate rule selects symbols not present in
  ledger rows, record unmatched / incomplete outcomes explicitly.
- **Delisted mid-horizon**: Inherit survivorship labels from ledger/measurement
  policy (ADR 0002); never drop quietly.
- **Train/OOS date contamination (rolling)**: In rolling mode, the same decision
  date MUST NOT appear in both train and OOS for the same candidate; violation
  MUST fail validation or smoke.
- **Determinism**: Identical inputs and configuration MUST yield bitwise-identical
  report payloads under canonical JSON serialization.

#### Brainstorm Prompts

<!-- Explored 2026-09-01; retained as category checklist for future sessions. -->

- **Boundary conditions**: ✅ Resolved (min 2 folds, ADR 0004 ≥20 pick-day
  floor, empty train → `skipped_empty_train`).
- **Error scenarios**: ✅ Resolved (missing ledger, corrupt fixtures, partial
  market, incomplete H20/H60 → `incomplete_horizon`).
- **Scale**: ✅ Resolved (v1 single-threaded CLI; ≤5 candidates; ≤3yr smoke;
  multi-year supported but not perf-optimized).
- **Security**: ✅ Resolved (no secrets in report JSON; config hash only).
- **User confusion**: ✅ Resolved (`runIntent` labeling; explicit train/OOS
  ranges; `backtest_screen` distinction in docs).
- **Data integrity**: ✅ Resolved (canonical JSON; rolling train/OOS date
  separation; contaminated fixture fails smoke).
- **Backwards compatibility**: ✅ Reinforced (Score v2 unchanged; additive
  analysis only).

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | First delivery: rolling only vs rolling+anchored both runnable? | Resolved | **Rolling only runnable in v1.** Anchored behavior fully documented in PIT assumptions with explicit deferral to follow-up (not runnable v1). Rationale: YAGNI; ADR 0003 requires rolling OOS; anchored adds complexity without blocking Issue #66 acceptance. See FR-007, FR-008, FR-031. |
| Q2 | Candidate space for v1: Score v2 frozen rule only, or fixed manual grid of rule variants? | Resolved | **Frozen Score v2 baseline + small fixed manual grid (max 4 named variants)** supplied via config/fixtures; no Optuna. Rationale: Issue #66 non-goal; analysis-only per constitution IV. See FR-014, FR-032. |
| Q3 | Must harness consume #63 ledger exclusively, or may it recompute returns from picks+prices? | Resolved | **Ledger-first (#63) for all `go_evidence` runs** — fail with actionable error if missing. **Optional picks+prices recompute allowed ONLY for offline smoke/dev fixtures** with explicit `measurementSource: fixture-recompute` flag; never for ADR 0004 GO packages. Rationale: Principle III additive artifacts; don't duplicate ledger math. See FR-016, FR-021, FR-022. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST evaluate screening candidates with walk-forward folds
  that separate train (or fit) ranges from later OOS ranges.
- **FR-002**: At each fold decision date `t`, selection MUST use only
  information available at `t` (no look-ahead).
- **FR-003**: System MUST emit a reproducible machine-readable OOS report plus
  a CLI human summary for each completed run.
- **FR-004**: Report MUST include pick forward return, hit-rate, excess return
  vs market benchmark, and `no_pick` ratio / coverage stats.
- **FR-005**: Horizons MUST include **H20** (primary) and **H60** (reported);
  benchmarks MUST use **KR-KOSPI** and **US-SPX** when those markets appear.
- **FR-006**: `no_pick` days MUST be excluded from pick-return averages and
  included in coverage / `no_pick` statistics.
- **FR-007**: Rolling walk-forward MUST be supported in the first delivery.
- **FR-008**: Anchored walk-forward MUST be documented in PIT assumptions; it
  MUST NOT be runnable in v1 — deferral MUST be explicit with a tracked
  follow-up reference.
- **FR-009**: Point-in-time assumptions MUST be documented in Methodology
  and/or this feature’s committed docs (Issue #66 acceptance).
- **FR-010**: System MUST provide an offline CI smoke using small fixtures that
  asserts no look-ahead and presence of required report fields.
- **FR-011**: Identical inputs and configuration MUST yield identical reports
  via deterministic **canonical JSON serialization** (field order and formatting
  rules documented in the implementation plan).
- **FR-012**: System MUST NOT change live Score v2 weights or daily pick
  publication semantics.
- **FR-013**: System MUST NOT place live broker/order or account connectivity
  in scope.
- **FR-014**: System MUST NOT include automatic Optuna-style weight
  optimization in v1; candidates are a frozen Score v2 baseline plus a fixed
  manual grid (max **4** named variants) supplied via config/fixtures only.
- **FR-015**: Public site performance/walk-forward UI integration is OPTIONAL
  and OUT OF SCOPE for this feature’s required acceptance (CLI/JSON sufficient).
- **FR-016**: When ledger/performance facts from Issue #63 are required
  (`go_evidence` runs and default production paths) and missing, the harness
  MUST fail with an actionable error rather than silently omitting folds.
- **FR-017**: Incomplete folds or horizons MUST be labeled with explicit status
  (e.g., `incomplete_horizon`); inventing returns is FORBIDDEN.
- **FR-018**: Walk-forward analysis artifacts MUST be additive (dedicated paths /
  reports); they MUST NOT rewrite historical `content/daily` pick files.
- **FR-019**: Runs intended as ADR 0004 GO evidence MUST disclose train/OOS
  calendars and MUST NOT reuse the same period for fitting narrative and GO
  claim without disclosure (ADR 0003).
- **FR-020**: Survivorship and price-basis semantics for measured outcomes MUST
  align with ADR 0002 (via ledger facts or equivalent documented policy).
- **FR-021**: Every report MUST label `runIntent` as `exploratory` or
  `go_evidence`; GO packages and merge-gate reviewers MUST be able to filter on
  this field.
- **FR-022**: Report MUST record `measurementSource`: `ledger` (default for
  `go_evidence`) or `fixture-recompute` (offline smoke/dev only). Runs with
  `runIntent: go_evidence` MUST use `measurementSource: ledger`; recompute is
  FORBIDDEN for ADR 0004 GO packages.
- **FR-023**: A valid walk-forward run MUST include at least **two** folds;
  fewer MUST fail with an actionable configuration error.
- **FR-024**: For `go_evidence` runs, if aggregate OOS scored `pick` days are
  below the ADR 0004 floor (**≥ 20**), the report MUST mark
  `insufficient_coverage` and MUST NOT imply GO readiness.
- **FR-025**: Fold status MUST use explicit values including at minimum:
  `complete`, `incomplete_horizon`, and `skipped_empty_train`.
- **FR-026**: Rolling fold entries in the report MUST include explicit train and
  OOS date ranges (per market when applicable).
- **FR-027**: In rolling mode, the same decision date MUST NOT appear in both
  train and OOS for the same candidate; violations MUST fail validation or
  smoke.
- **FR-028**: Report artifacts MUST NOT embed secrets, API keys, or raw
  credentials; reproducibility stamps MUST use configuration hashes or equivalent
  non-secret identifiers only.
- **FR-029**: Corrupt or schema-invalid fixtures MUST fail with file path and
  schema-validation hints; partial silent truncation is FORBIDDEN.
- **FR-030**: When only one market appears in the evaluation window, the harness
  MUST evaluate and report that market only; it MUST NOT invent the missing
  market.
- **FR-031**: PIT assumptions documentation MUST distinguish this walk-forward
  harness from legacy `backtest_screen` snapshot comparison (purpose, PIT cut,
  and acceptable use).
- **FR-032**: v1 implementation MAY target single-threaded CLI execution with
  ≤5 candidates and ≤3-year calendars in smoke fixtures; larger calendars and
  candidate counts are supported but not performance-optimized (documented in
  Assumptions).

### Key Entities

- **Walk-Forward Fold**: Decision date `t`, train range, OOS range, status
  (`complete` / `incomplete_horizon` / `skipped_empty_train`).
- **Screening Candidate**: Named rule or parameter set under evaluation
  (frozen Score v2 baseline or manual grid entry, max 4 variants); not a live
  weight merge.
- **OOS Report**: Aggregate + per-fold metrics (returns, hit-rate, excess vs
  benchmark, coverage / `no_pick`), horizon and benchmark ids, `runIntent`,
  `measurementSource`, coverage flags (`insufficient_coverage` when applicable),
  configuration hash or equivalent reproducibility stamp.
- **PIT Assumptions Record**: Human-readable statement of cuts, calendars,
  rolling vs anchored (anchored deferred), and look-ahead rules used by the
  harness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can obtain a complete fixture-based walk-forward
  report in one offline run without live market access.
- **SC-002**: Contaminated fixtures that only expose features after `t` cause
  the smoke suite to fail (or prove unused) in 100% of those cases.
- **SC-003**: Required metrics (pick return, hit-rate, excess vs benchmark,
  `no_pick` coverage) appear in every successful report.
- **SC-004**: H20 is always present as the primary horizon label when any
  completed pick OOS row exists; H60 is present when that horizon is complete
  or explicitly marked incomplete.
- **SC-005**: Re-running the same fixture configuration twice produces
  bitwise-identical report payloads under canonical JSON serialization.
- **SC-006**: Live daily pick files remain unchanged after harness runs
  (zero unintended diffs to historical pick semantics).
- **SC-007**: PIT assumptions are discoverable from Methodology or the feature
  docs without reading source code.
- **SC-008**: Scope excludes broker integration and Optuna auto-optimization
  (verified by absence from acceptance scenarios and FR-013/FR-014).
- **SC-009**: Every report includes `runIntent` and `measurementSource`; a
  reviewer can identify GO-evidence runs without reading CLI logs.
- **SC-010**: `go_evidence` runs below the ADR 0004 pick-day floor surface
  `insufficient_coverage` in 100% of those cases (never silent GO implication).

## Assumptions

- Docs gate (#75) is merged; ADR 0001–0004 are the engineering authority.
- Issue #63 ledger/performance facts are the preferred measurement substrate;
  this harness does not redefine forward-return math.
- **First delivery is rolling-only runnable**; anchored is documented in PIT
  assumptions and explicitly deferred (not runnable v1).
- Candidate evaluation is analysis-only: frozen Score v2 baseline plus max **4**
  named manual variants via config/fixtures; Score v2 stays live until ADR 0004
  GO.
- **`go_evidence` runs require ledger (#63)**; `fixture-recompute` is dev/smoke
  only with explicit flag.
- v1 targets **single-threaded CLI**, **≤5 candidates**, **≤3-year** calendars
  in smoke fixtures; multi-year / multi-candidate runs are supported but not
  performance-optimized.
- Site UI for walk-forward charts is out of scope for required acceptance.
- KR/US dual calendars and holiday handling details will be fixed in plan /
  research; this spec requires they be documented, not a specific vendor.
- Snapshot comparator (`backtest_screen`) may remain for legacy checks but is
  not a substitute for this harness’s acceptance; docs MUST distinguish them
  (FR-031).
- Report JSON excludes secrets; reproducibility uses config hash only (FR-028).

## Out of Scope

- Live trading, broker, or order routing
- Automatic hyperparameter / Optuna optimization of Score weights
- Required public-site walk-forward pages (optional later)
- Merging Score v3 weights (belongs to #67 + ADR 0004 GO)
- Dual-source market-data redesign (#71)
- **Runnable anchored walk-forward in v1** (documented and deferred)
- **`fixture-recompute` for ADR 0004 GO packages** (ledger required)

## Brainstorm Log

<!--
  Maintained by /speckit.superspec.brainstorm — do not edit manually
-->

### 2026-09-01 — Round 1 (Q1: rolling vs anchored)

**Question**: First delivery — rolling only vs rolling+anchored both runnable?
**Decision**: **Rolling only runnable in v1.** Anchored fully documented in PIT
assumptions with explicit deferral to follow-up (not runnable v1).
**Rationale**: YAGNI; ADR 0003 requires rolling OOS; anchored adds complexity
without blocking Issue #66 acceptance.
**Spec impact**: Q1 Resolved; FR-008 tightened; US3 acceptance scenario 2 updated;
Assumptions amended.

### 2026-09-01 — Round 2 (Q2: candidate grid)

**Question**: Candidate space for v1 — Score v2 frozen only vs fixed manual grid?
**Decision**: **Frozen Score v2 baseline + small fixed manual grid (max 4 named
variants)** via config/fixtures; no Optuna.
**Rationale**: Issue #66 non-goal; analysis-only per constitution IV.
**Spec impact**: Q2 Resolved; FR-014 refined; Key Entities updated.

### 2026-09-01 — Round 3 (Q3: ledger vs recompute)

**Question**: Must harness consume #63 ledger exclusively, or recompute from
picks+prices?
**Decision**: **Ledger-first for all `go_evidence` runs** — fail actionable if
missing. **Optional `fixture-recompute` only for offline smoke/dev** with
explicit `measurementSource` flag; never for ADR 0004 GO packages.
**Rationale**: Principle III additive artifacts; don't duplicate ledger math.
**Spec impact**: Q3 Resolved; FR-021, FR-022 added; Edge Cases + Out of Scope.

### 2026-09-01 — Round 4 (Boundary conditions)

**Question**: Minimum folds, GO coverage floor, empty train handling?
**Decision**: Minimum **2 folds** for valid run; ADR 0004 floor **≥20** scored
pick days in aggregate OOS for `go_evidence` (mark `insufficient_coverage`
below floor); empty train → fold status `skipped_empty_train`.
**Spec impact**: FR-023, FR-024, FR-025; Edge Cases; SC-010; US2 scenario 4.

### 2026-09-01 — Round 5 (Error scenarios)

**Question**: Missing ledger, corrupt fixtures, partial markets, incomplete
horizons?
**Decision**: Missing ledger → fail actionable; corrupt fixture → fail with
path+schema hint; partial market calendar → evaluate present market only;
incomplete H20/H60 → fold status `incomplete_horizon`.
**Spec impact**: FR-017, FR-029, FR-030; Edge Cases expanded.

### 2026-09-01 — Round 6 (Scale & performance)

**Question**: v1 performance targets for calendars and candidate counts?
**Decision**: v1 targets **single-threaded CLI**, **≤5 candidates**, **≤3yr**
calendar in smoke; multi-year/multi-candidate supported but not
performance-optimized (document in Assumptions).
**Spec impact**: FR-032; Assumptions amended.

### 2026-09-01 — Round 7 (Security & privacy)

**Question**: What must report artifacts exclude?
**Decision**: Report JSON MUST exclude secrets; config hash only, no API keys in
artifacts.
**Spec impact**: FR-028; Assumptions.

### 2026-09-01 — Round 8 (UX / confusion)

**Question**: How to distinguish exploratory vs GO runs and rolling fold ranges?
**Decision**: Report MUST label `runIntent` (`exploratory` | `go_evidence`);
rolling folds MUST include explicit train/OOS date ranges; docs MUST distinguish
from `backtest_screen` snapshot comparator.
**Spec impact**: FR-021, FR-026, FR-031; US4 scenario 3; SC-009.

### 2026-09-01 — Round 9 (Data integrity)

**Question**: Determinism, train/OOS contamination, smoke for bad fixtures?
**Decision**: Deterministic **canonical JSON serialization**; rolling mode train/OOS
must not share decision dates for same candidate; contaminated fixture must fail
smoke.
**Spec impact**: FR-011 refined, FR-027; Edge Cases; SC-005 reaffirmed.

**Session summary**: Status → `Brainstormed (ready for plan)`; Open Questions
Q1–Q3 Resolved; FR-021–FR-032 added; SC-009–SC-010 added; Edge Cases and
Assumptions fully updated; Brainstorm Prompts marked explored.

**Constitution check (self-review)**: I Git-content SoT — additive reports only;
II PIT — fold cuts, no look-ahead, survivorship via ledger; III additive —
ledger-first, no pick rewrite; IV Score freeze — analysis-only, no Optuna;
V schema/contracts — deterministic artifacts, documented PIT. No TBD left for
planning-critical ambiguity.

**Further brainstorm needed**: No (saturated for Issue #66 scope).
